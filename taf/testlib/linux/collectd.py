"""
@copyright Copyright (c) 2016-2017, Intel Corporation.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@file  collectd.py

@summary  Class to abstract collectd operations
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

If required, stop running collectd service:
env.lhost[1].ui.collectd.stop()

Start collectd service:
env.lhost[1].ui.collectd.start()

Consistent and valid collectd.conf content is built from OrderedDict object, e.g.:
python_plugin_config = collections.OrderedDict(
    (('ModulePath', '"/tmp/"'),
     ('Interactive', 'false'),
     ('Import', '"python_module_name"'),
     ('Module "python_module_name"', {'Test': 'arg1'})))

env.lhost[1].ui.collectd.plugins_config = collections.OrderedDict(
    (('Interval', 3),
     ('AutoLoadPlugins', 'false'),
     ('LoadPlugin cpu', {}),
     ('LoadPlugin "csv"', {}),
     ('LoadPlugin "python"', {'Interval': 5, 'Globals': 'true'}),
     ('Plugin "csv"', {'DataDir': '"/tmp/csv_data/"'}),
     ('Plugin "python"', python_plugin_config)))

As shown above, config parts that depend on parameters order should be presented as OrderedDict objects.
Otherwise, dict() object can be used.

Transform data structure into multiline text block:
env.lhost[1].ui.collectd.update_config_file()

If required, in other test the default plugins configuration may be changed, e.g.:
env.lhost[1].ui.collectd.plugins_config['LoadPlugin "csv"'].update({'Interval': 9})
env.lhost[1].ui.collectd.update_config_file()

Some plugins support multiple entries of parameter with same name.
Such case should be presented as
{param_name: [param1_value, ...]}

Example of resulting collectd.conf file:

Interval 3
AutoLoadPlugins false
<LoadPlugin cpu>
</LoadPlugin>
<LoadPlugin "csv">
    Interval 9
</LoadPlugin>
<LoadPlugin "python">
    Interval 5
    Globals true
</LoadPlugin>
<Plugin "csv">
    DataDir "/tmp/csv_data/"
</Plugin>
<Plugin "python">
    ModulePath "/tmp/"
    Interactive false
    Import "python_module_name"
    <Module "python_module_name">
        Test arg1
    </Module>
</Plugin>

Restart collectd service
env.lhost[1].ui.collectd.restart()
"""
import collections

from testlib.linux import service_lib
from testlib.custom_exceptions import CustomException

INDENT = ' ' * 4
PARAM_BOILERPLATE = '{indent}{name} {value}\n'
TAGGED_BOILERPLATE = ('{indent}<{tag}{space}{name}>\n'
                      '{params}'
                      '{indent}</{tag}>\n')


def build_tagged_section(config_data, indent_level=-1, res=''):
    """
    @brief  Fill in data into text block
    @param  config_data:  plugins configuration data structure
    @type  config_data:  collections.Mapping
    @param  indent_level:  indentation level
    @type  indent_level:  int
    @param  res:  Init resulting text block
    @type  res:  str
    @return:  resulting text block
    @rtype:  str
    """
    for k, v in config_data.items():
        if isinstance(v, collections.Mapping):
            tag, space, name = k.partition(' ')
            indent_level += 1
            res += TAGGED_BOILERPLATE.format(indent=INDENT * indent_level,
                                             tag=tag, space=space, name=name,
                                             params=build_tagged_section(v, indent_level))
            indent_level -= 1
        elif not isinstance(v, str) and isinstance(v, collections.Iterable):
            res += ''.join(PARAM_BOILERPLATE.format(indent=INDENT * (indent_level + 1), name=k, value=x) for x in v)
        else:
            res += PARAM_BOILERPLATE.format(indent=INDENT * (indent_level + 1), name=k, value=v)
    return res


class Collectd(object):

    SERVICE = 'collectd'
    DEFAULT_COLLECTD_CONF = '/etc/collectd.conf'

    def __init__(self, cli_send_command, collectd_conf=None):
        """
        @brief  Initialize Collectd class.
        """
        super(Collectd, self).__init__()
        self.send_command = cli_send_command
        self.collectd_conf = collectd_conf if collectd_conf else self.DEFAULT_COLLECTD_CONF
        self.service_manager = service_lib.specific_service_manager_factory(self.SERVICE, self.send_command)

        # Data structure presenting content of collectd.conf
        self.plugins_config = None

    def start(self):
        """
        @brief  Start collectd service
        """
        return self.service_manager.start()

    def stop(self):
        """
        @brief  Stop collectd service
        """
        return self.service_manager.stop()

    def restart(self):
        """
        @brief  Restart collectd service
        """
        return self.service_manager.restart()

    def update_config_file(self):
        """
        @brief  Create collectd configuration text and write it to collectd.conf file
        """
        # Make provided collectd plugins configuration object accessible
        if not self.plugins_config:
            raise CustomException("No plugins config defined.")
        # Build up text block and make it accessible
        config_text = build_tagged_section(self.plugins_config)
        self.send_command('cat > {} <<EOF\n{}\nEOF'.format(self.collectd_conf, config_text))
