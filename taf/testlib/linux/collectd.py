"""
@copyright Copyright (c) 2016 - 2017, Intel Corporation.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@file collectd.py

@summary Class to abstract collectd operations
@note
collectd.conf path is retrieved from testcases/config/setup/setup.json in format:
{
    "env": [
      {
        "id": "213207",
        "collectd_conf_path": "/opt/collectd/etc/collectd.conf"
      }
    ],
    "cross": {}
}
If "collectd_conf_path" is not specified in setup.json then default value is set: /etc/collectd.conf

Examples of collectd usage in tests:

env.lhost[1].ui.collectd.start()
env.lhost[1].ui.collectd.stop()
env.lhost[1].ui.collectd.restart()

Example of collectd.conf modifications:
format: instance.ui.collectd.<action>.<plugin_name>()
env.lhost[1].ui.collectd.enable.csv(DataDir='"/path/to/logs"')
env.lhost[1].ui.collectd.disable.csv()
env.lhost[1].ui.collectd.enable_defaults.csv()
env.lhost[1].ui.collectd.change_param.csv(DataDir='"/path/to/logs"')
env.lhost[1].ui.collectd.insert_param.csv(DataDir='"/path/to/logs"')
"""

import re

from testlib.custom_exceptions import CustomException
from testlib.linux import service_lib


PLUGINS = ("python", "csv", "dpdkstat", "dpdkevents", "hugepages", "intel_rdt", "mcelog", "ovs_stats", "ovs_events",
           "snmp_agent", "syslog", "exec", "ipmi")

GLOBAL_PLUGIN_LOAD_BOILERPLATE = """
<LoadPlugin {plugin}>
    {params_to_insert}
</LoadPlugin>
"""

LOAD_PLUGIN_WITH_PARAM_BOILERPLATE = """
LoadPlugin {plugin}

<Plugin {plugin}>
    {params_to_insert}
</Plugin>
"""

ACTIONS = {'enable': {'cmd': [r"printf  '{0}' >> {{collectd_conf}}".format(LOAD_PLUGIN_WITH_PARAM_BOILERPLATE)],
                      'kwargs_required': True},
           'enable_default': {'cmd': [r"sed -i '/[^<]LoadPlugin {plugin}/s/^\(#\)\+//gw /dev/stdout' {collectd_conf}",
                                      r"sed -i '/<Plugin \({plugin}\|\"{plugin}\"\)>/,/<\/Plugin>/s/^\(#\)\+//w /dev/stdout' {collectd_conf}"],
                              'kwargs_required': False},
           'enable_global': {'cmd': [r"printf  '{0}' >> {{collectd_conf}}".format(GLOBAL_PLUGIN_LOAD_BOILERPLATE)],
                             'kwargs_required': True},
           'enable_global_default': {'cmd': [r"sed -i '/<LoadPlugin \({plugin}\|\"{plugin}\"\)>/,/<\/LoadPlugin>/s/^\(#\)\+//gw /dev/stdout' {collectd_conf}"],
                                     'kwargs_required': False},
           'change_param': {'cmd': [r"sed -i '/^<Plugin \({plugin}\|\"{plugin}\"\)>/,/^<\/Plugin>/s/\(^\s*\)\({par}.*\)/\1{par} {val}/w /dev/stdout' {collectd_conf}"],
                            'kwargs_required': True},
           'change_global': {'cmd': [r"sed -i '/^<LoadPlugin \({plugin}\|\"{plugin}\"\)>/,/^<\/LoadPlugin>/s/\(^\s*\)\({par}.*\)/\1{par} {val}/w /dev/stdout' {collectd_conf}"],
                             'kwargs_required': True},
           'insert_param': {'cmd': [r"sed -i '/^<Plugin \({plugin}\|\"{plugin}\"\)>/a\\t{par} {val}' {collectd_conf}"],
                            'kwargs_required': True},
           'disable': {'cmd': [r"sed  -i '/^LoadPlugin {plugin}/s/^[^#]/#&/w /dev/stdout' {collectd_conf}",
                               r"sed  -i '/^<Plugin \({plugin}\|\"{plugin}\"\)>/,/^<\/Plugin>/s/^[^#]/#&/w /dev/stdout' {collectd_conf}"],
                       'kwargs_required': False},
           'disable_global': {'cmd': [r"sed  -i '/^<LoadPlugin \({plugin}\|\"{plugin}\"\)>/,/^<\/LoadPlugin>/s/^[^#]/#&/w /dev/stdout' {collectd_conf}"],
                              'kwargs_required': False},
           'disable_inline': {'cmd': [r"sed  -i '/^LoadPlugin {plugin}\|\"{plugin}\"/s/^[^#]/#&/w /dev/stdout' {collectd_conf}"],
                             'kwargs_required': False},
           'enable_inline': {'cmd': [r"sed  -i '/^\s*#\s*LoadPlugin {plugin}\|\"{plugin}\"/s/^\s*#\s*//w /dev/stdout' {collectd_conf}"],
                              'kwargs_required': False},
           'enable_param': {'cmd': [ r"sed -i '/^<Plugin \({plugin}\|\"{plugin}\"\)>/,/^<\/Plugin>/s/\(^\s*\)\(#{par}.*\)/\1{par} {val}/w /dev/stdout' {collectd_conf}"],
                            'kwargs_required': True},
           'disable_param': {'cmd': [ r"sed -i '/^<Plugin \({plugin}\|\"{plugin}\"\)>/,/^<\/Plugin>/s/\(^\s*\)\({par}.*\)/\1#{par} {val}/w /dev/stdout' {collectd_conf}"],
                            'kwargs_required': True},
           }


class CollectdConfCommandGenerator(object):
    def __init__(self, action, command_generator, collectd_conf, plugin_list=PLUGINS):
        """
        @brief  Initialize collectd conf command generator class
        """
        super(CollectdConfCommandGenerator, self).__init__()
        self.plugin_list = plugin_list
        for plugin in self.plugin_list:
            setattr(self, plugin, command_generator(action, plugin, collectd_conf))


class CollectdPluginsManager(object):
    def __init__(self, action, collectd_conf_commands, run):
        """
        @brief  Initialize collectd conf manager class
        """
        super(CollectdPluginsManager, self).__init__()
        for cmd in collectd_conf_commands.plugin_list:
            setattr(self, cmd,
                    self.generate_run_function(run, getattr(collectd_conf_commands, cmd), action))

    @staticmethod
    def generate_run_function(run_func, command, action):
        def run(**kwargs):
            return run_func(command(**kwargs))
        return run


def collectd_conf_action(action, run_func, collectd_conf):
    collectd_conf_commands = CollectdConfCommandGenerator(action, command_generator, collectd_conf, PLUGINS)
    return CollectdPluginsManager(action, collectd_conf_commands, run_func)


def command_generator(action, plugin, collectd_conf):
    """
    @brief Wrapper to map collectd operations with related commands
    """
    def method(**params):
        command_list = []
        this_action = ACTIONS[action]
        this_cmd = this_action['cmd']
        kwargs_needed = this_action['kwargs_required']
        if kwargs_needed and not params:
            raise CustomException("Arguments are required for current method")
        if not kwargs_needed and params:
            raise CustomException("Arguments are not required for current method")
        if not params:
            for cmd in this_cmd:
                command_list.append([cmd.format(plugin=plugin, collectd_conf=collectd_conf)])
        elif action in {'insert_param', 'change_param', 'change_global', 'enable_param', 'disable_param'}:
            for par, val in params.items():
                command_list.append(
                    [this_cmd[0].format(plugin=plugin, par=par, val=re.escape(str(val)), collectd_conf=collectd_conf)])
        else:
            params_to_insert = '\n'.join('\t{0} {1}'.format(par, val) for par, val in params.items())
            for cmd in this_cmd:
                command_list.append(
                    [cmd.format(plugin=plugin, params_to_insert=params_to_insert, collectd_conf=collectd_conf)])
        return command_list
    return method


class Collectd(object):

    SERVICE = 'collectd'
    DEFAULT_COLLECTD_CONF = '/etc/collectd.conf'

    def __init__(self, cli_send_command, cli_set_command, collectd_conf=None):
        """
        @brief Initialize Collectd class.
        """
        super(Collectd, self).__init__()
        self.send_command = cli_send_command
        self.cli_set_command = cli_set_command
        self.collectd_conf = collectd_conf if collectd_conf else self.DEFAULT_COLLECTD_CONF
        self.service_manager = service_lib.specific_service_manager_factory(self.SERVICE, self.send_command)

        for action in ACTIONS:
            setattr(self, action, collectd_conf_action(action, self.cli_set_command, self.collectd_conf))

    def start(self):
        """
        @brief Start collectd service
        """
        return self.service_manager.start()

    def stop(self):
        """
        @brief Stop collectd service
        """
        return self.service_manager.stop()

    def restart(self):
        """
        @brief Restart collectd service
        """
        return self.service_manager.restart()

    def add_globals(self, **kwargs):
        """
        @brief Add global collectd variables in collectd.conf
        """
        inserts = r'\n'.join("{} {}".format(param, re.escape(str(val))) for param, val in kwargs.items())
        command = r"sed -i '1s/^/{}\n/' {}"
        self.send_command(command.format(inserts, self.collectd_conf))

    def status(self, exp_rc=frozenset({0, 3})):
        """
        @brief Status collectd service
        """
        return self.service_manager.status(expected_rcs=exp_rc)
