# Copyright (c) 2011 - 2017, Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""``pytest_syslog.py``

`Plugin writes messages to SysLogHandler`

Note:
    For correct functioning syslog should be properly configured, e.g.

      1. On device should be configured hostname seacliff9.
      2. The following lines should be added to syslog config::

          # This is criteria for seacliff messages
          if $hostname contains 'seacliff9' then /var/log/switches/seacliff09.log
          # This s criteria for our log messages
          if $msg contains 'seacliff9' and $programname == 'pytest_syslog' then /var/log/switches/seacliff9.log

Also it is good to configure logrotate (e.g. /etc/logrotate.d/switches) file of :

Examples::

    /var/log/switches/*.log
    {
        rotate 730
        weekly
        missingok
        notifempty
        delaycompress
        compress
        postrotate
            reload rsyslog >/dev/null 2>&1 || true
        endscript
    }

Known issues:
    - rsyslog could miss log messages from remote host if it cannot resolve host FQDN 10 times.
      To disable dns resolving add -x option to /etc/default/rsyslog (for debian based distros).

"""

import logging
from logging.handlers import SysLogHandler
from os import getpid
from os import path
import socket
import sys

import pytest

from .pytest_helpers import get_tcname


def pytest_addoption(parser):
    """Describe plugin specified options.

    """
    group = parser.getgroup("syslog", "plugin syslog notifier")
    group.addoption("--syslog", action="store_true", dest="syslog",
                    default=False,
                    help="Enable syslog plugin. %default by default.")


def pytest_configure(config):
    """Registering plugin.

    """
    if config.option.syslog:
        config.pluginmanager.register(SyslogNotifier(), "_syslog_notifier")


def pytest_unconfigure(config):
    """Unregistering plugin.

    """
    syslog_notifier = getattr(config, "_syslog_notifier", None)
    if syslog_notifier:
        del config._syslog_notifier
        config.pluginmanager.unregister(syslog_notifier)


class SyslogNotifier(object):
    """Send syslog messages.

    """

    def setup_logger(self, session):
        """Setup logger for each device.

        Args:
            session(pytest.Session): pytest session

        """
        servers = []
        self.loggers = []  # pylint: disable=attribute-defined-outside-init
        self.logs_path = []  # pylint: disable=attribute-defined-outside-init

        switches_ids = session.config.env.switch
        for switch_id in switches_ids:
            switch = session.config.env.switch[switch_id]
            if "related_conf" in switch.config:
                for item in switch.config["related_conf"]:
                    if "instance_type" in switch.config["related_conf"][item]:
                        if switch.config["related_conf"][item]["instance_type"] == "syslog_settings":
                            path_to_log = switch.config["related_conf"][item]["path_to_log"]
                            switch_name = switch.config['name']
                            self.logs_path += [{switch_id: path_to_log}]
                            syslogserver_port = 514
                            syslogserver = switch.config["related_conf"][item]["ip"]
                            if "port" in switch.config["related_conf"][item]:
                                syslogserver_port = switch.config["related_conf"][item]["port"]
                            switch_item = {}
                            switch_item["ip"] = syslogserver
                            switch_item["name"] = switch_name
                            switch_item["port"] = syslogserver_port
                            servers.append(switch_item)

        for server in servers:
            syslogserver = server["ip"]
            syslogserver_port = server["port"]
            switch_name = server["name"]
            logger = logging.getLogger()
            formatter = logging.Formatter('%(module)s: %(levelname)s %(message)s')
            if sys.version_info >= (2, 7):
                syslog = SysLogHandler(address=(syslogserver, syslogserver_port),
                                       facility=SysLogHandler.LOG_USER,
                                       socktype=socket.SOCK_DGRAM)
            else:
                syslog = SysLogHandler(address=(syslogserver, syslogserver_port),
                                       facility=SysLogHandler.LOG_USER, )
            syslog.setFormatter(formatter)
            logger.addHandler(syslog)
            logger.setLevel(logging.INFO)
            logger_item = {}
            logger_item["name"] = switch_name
            logger_item["logger"] = logger
            self.loggers += [logger_item]

        self.setup_fail = False  # pylint: disable=attribute-defined-outside-init
        self.call_fail = False  # pylint: disable=attribute-defined-outside-init
        self.teardown_fail = False  # pylint: disable=attribute-defined-outside-init

    def _create_header(self, env_prop, stage):
        """Send syslog header/footer message for each device in config.

        Args:
            env_prop(dict): Environment properties for test run identification
            stage(str): "SessionStart" or "SessionFinish"

        Returns:
            None

        Examples::

            self._create_header(env_object.config, {"py.test PID": "5216", "chipName": "8086", "cpuArchitecture": "8bit"}, "SessionStart")

        """
        env_dict = env_prop.copy() if env_prop is not None else {}
        env_dict["py.test PID"] = str(getpid())

        for logger in self.loggers:
            logger["logger"].info("{0}: {1} on environment: {2}.".format(logger["name"], stage, env_dict))

    def _update_tc_status(self, tcname, status):
        """Send syslog TC status message for each device in config.

        Args:
            tcname(str):  Name of TC
            status(str):  TC status - started or finished

        Returns:
            None

        Examples::

            self._update_tc_status(env_object.config, "test_some_feature_1", "started")

        """
        for logger in self.loggers:
            logger["logger"].info("{0}: TC {1} {2}.".format(logger["name"], tcname, status))

    @pytest.mark.trylast
    def pytest_sessionstart(self, session):
        """Send syslog message with session header.

        """
        self.setup_logger(session)
        self._create_header(session.config.env.env_prop, "SessionStart")

    @pytest.mark.tryfirst
    def pytest_runtest_call(self, item):
        """Send syslog message on TC start.

        """
        if self.loggers:
            tcname = get_tcname(item)
            self._update_tc_status(tcname, "started")

    @pytest.mark.trylast
    def pytest_runtest_teardown(self, item, nextitem):
        """Send syslog message on TC end.

        """
        if self.loggers:
            tcname = get_tcname(item)
            self._update_tc_status(tcname, "finished")

    def is_test_completed(self, report):
        """Return True if make_report hook called after TC and TC failed.

        Args:
            report(pytest.Report): pytest report

        Returns:
            bool: True if test is complited without errors

        """
        if report.when == "setup" and report.outcome == "failed":
            self.setup_fail = True  # pylint: disable=attribute-defined-outside-init
        elif report.when == "call" and report.outcome == "failed":
            self.call_fail = True  # pylint: disable=attribute-defined-outside-init
        elif report.when == "teardown" and report.outcome == "failed":
            self.teardown_fail = True  # pylint: disable=attribute-defined-outside-init
        return report.when == "teardown" and (self.setup_fail or self.call_fail or self.teardown_fail)

    def get_log_path(self, switch_name):
        """Return log path from environment.json for switch.

        Args:
            switch_name(str): switch name

        Returns:
            str: path to log for specified device

        """
        for item in self.logs_path:
            if switch_name in list(item.keys()):
                return item[switch_name]

    def get_last_record_from_log(self, log, item):
        """Return last log records for TC.

        Args:
            log(str): log file
            item(pytest.Item): test case item

        Returns:
            str: Log related to specified test item

        """
        started = False

        tc_name = get_tcname(item)
        fin = open(log)

        lines = []
        while True:
            line = fin.readline()
            # EOF
            if line == "":
                break
            # Select last block "TC started ... TC finished" in log
            if not started:
                if tc_name in line and "started" in line:
                    started = True
                    lines = []
                    lines.append(line)
            else:
                lines.append(line)
                if tc_name in line and "finished" in line:
                    started = False
        fin.close()
        return " ".join(lines)

    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        """If TC failed add system log (rsyslog) for TC to report object.

        """
        outcome = yield
        rep = outcome.get_result()
        rep.device_log = {}
        if self.is_test_completed(rep):
            for switch_id in list(item.config.env.switch.keys()):
                switch_name = item.config.env.switch[switch_id].config['name']
                path_to_log = self.get_log_path(switch_id)
                if not path_to_log:
                    rep.device_log[switch_id] = "Using option syslog without set log path in environment.json"
                    return rep
                else:
                    log = path.join(path_to_log, switch_name + ".log")
                    if not path.exists(log):
                        rep.device_log[switch_id] = "Log file %s does not exists" % log
                        return rep
                    rep.device_log[switch_id] = self.get_last_record_from_log(log, item)

    @pytest.mark.trylast
    def pytest_sessionfinish(self, session):
        """Send syslog message with session footer.

        """
        self._create_header(session.config.env.env_prop, "SessionFinish")
