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

"""``afs.py``

`AFS-specific functionality`

"""

import re

from . import loggers
from .clitelnet import TelnetCMD
from .connpool import ConnectionPool

from .custom_exceptions import AFSException


# Decorators to set CLI privilege mode and return TelnetCMD object

def afs_normal_mode(function):
    """Decorator: get afs_instance for class methods.

    """
    def wrapper(*args, **kwargs):
        """Get afs_instance for class methods.

        """
        afs_instance = args[0].connection_pool.get_connection()
        set_vty_timeout(afs_instance, args[0].config_prompt)
        err = True
        try:
            result = function(afs_instance=afs_instance, *args, **kwargs)
            err = False
        finally:
            if err:
                args[0].connection_pool.del_connection_in_use(afs_instance)
            else:
                args[0].connection_pool.release(afs_instance)
        return result
    return wrapper


def afs_conf_mode(function):
    """Decorator: get afs_instance with enabled config mode for class methods.

    """
    def wrapper(*args, **kwargs):
        """Get afs_instance with enabled config mode for class methods.

        """
        afs_instance = args[0].connection_pool.get_connection()
        set_vty_timeout(afs_instance, args[0].config_prompt)
        afs_instance.enter_mode("config", args[0].config_prompt)
        err = True
        try:
            result = function(afs_instance=afs_instance, *args, **kwargs)
            err = False
        finally:
            if err:
                args[0].connection_pool.del_connection_in_use(afs_instance)
            else:
                afs_instance.exit_mode("exit")
                args[0].connection_pool.release(afs_instance)
        return result
    return wrapper


def set_vty_timeout(afs_instance, config_prompt):
    """Set AFS vty timeout.

    Args:
        afs_instance(CLIGenericMixin):  Instance of AFS device
        config_prompt(str):  Prompt message

    Notes:
        By default AFS has timeout = 1800 seconds.
        Such long timeout could cause excided number of allowed connection in case any error.

    """
    # Switch# config
    # Configuring from memory or network is not supported
    # Switch(config)# line vty
    # Switch(config-line)# exec-timeout 60
    # Switch(config-line)# exit
    # Switch(config)# exit
    afs_instance.enter_mode("config", config_prompt)
    afs_instance.enter_mode("line vty", "Switch(config-line)#")
    afs_instance.shell_command("exec-timeout 60", ret_code=False)
    afs_instance.exit_mode("exit")
    afs_instance.exit_mode("exit")


def get_unused_values(used_values, min_value, max_value):
    """Return two first unused values from range min_value - max_value.

    Args:
        used_values(list[int]):  List of used integers
        min_value(int):  Min value
        max_value(int):  Max value

    Raises:
        AFSException:  not enough free values

    Returns:
        list[int]:  Two first unused values from range min_value - max_value

    """
    used_set = set(used_values)
    free_set = set(range(min_value, max_value + 1))
    free_values = list(free_set - used_set)
    if len(free_values) >= 2:
        return free_values[:2]
    else:
        raise AFSException("All allowed map ids are used.")


# TODO: Add ability to restore AFS config after tests
# TODO: Add xconnect_array method to do fast connection of many ports
# TODO: Add port_shutdown for emulating operState Down
class AFS(object):
    """Basic interact with AFS.

    """

    class_logger = loggers.ClassLogger()

    def __init__(self, config):
        """Initialize AFS class.

        Args:
            config(dict):  Configuration

        """

        # self.class_logger = loggers.ClassLogger()
        self.class_logger.info("Create AFS object.")

        self.id = config['id']
        self.type = config['instance_type']
        self.config = config
        self.portmap = config['portmap']

        host = config['ip_host']
        user = config['user']
        password = config['password']

        self.prompt = "Switch# "
        # self.config_prompt = "Switch\(config\)# "
        self.config_prompt = "Switch(config)# "

        pass_prompt = "Password: "
        login_prompt = "Switch login: "
        page_break = "--More--"
        timeout = 10
        exit_cmd = "exit"

        self.connection_pool = ConnectionPool(connection_class=TelnetCMD,
                                              host=host, user=user, password=password,
                                              prompt=self.prompt, pass_prompt=pass_prompt,
                                              login_prompt=login_prompt, page_break=page_break,
                                              timeout=timeout, exit_cmd=exit_cmd)

        self.running_config = None

        # AFS constants
        # It's not verified value. We don't have new AFS firmware manual.
        self.min_map_number = 1
        self.max_map_number = 4094

    def clear_connection_pool(self):
        """Close all connections from connection pool.

        """
        self.class_logger.debug("Destroy all AFS telnet connections.")
        self.connection_pool.disconnect_all()

    @afs_normal_mode
    def get_run_config(self, afs_instance=None):
        """Return running config and write it to self.running_config.

        Args:
            afs_instance(CLIGenericMixin):  Instance of AFS device

        Raises:
            AFSException:  error in getting AFS running config

        Returns:
            str:  Running config

        """
        running_config, err = afs_instance.shell_command("show running-config", ret_code=False)
        if err:
            raise AFSException("Cannot get ASF running config! ERROR: %s, OUTPUT: %s" % (err, running_config, ))
        self.running_config = running_config
        return running_config

    @afs_normal_mode
    def get_sys_info(self, afs_instance=None):
        """Return AFS system information.

        Args:
            afs_instance(CLIGenericMixin):  Instance of AFS device

        Raises:
            AFSException:  error in getting AFS system information

        Returns:
            str:  AFS system information

        """
        sysinfo, err = afs_instance.shell_command("show system information", ret_code=False)
        if err:
            raise AFSException("Cannot get ASF system information! ERROR: %s, OUTPUT: %s" % (err, sysinfo, ))
        return sysinfo

    def _get_maps_id(self):
        """Return list of map's ids founded in running config.

        Raises:
            AFSException:  AFS running config is not available

        Returns:
            list:  list of map's ids founded in running config

        """
        if self.running_config is None:
            raise AFSException("No running config!")
        run_conf = self.running_config.splitlines()
        map_list = []
        for line in run_conf:
            val = re.search('^configuration map ([0-9]{1,4})$', line)
            if val:
                map_list.append(val.groups()[0])
        return map_list

    @afs_normal_mode
    def _get_port_map(self, afs_instance=None):
        """Return list of VLAN ids and port to VLAN map.

        Args:
            afs_instance(CLIGenericMixin):  Instance of AFS device

        Raises:
            AFSException:  error on getting AFS MAP information

        Returns:
            tuple:  tuple set(['1', '3', '2', '4']), {'1': set(['2', '4']), '17': set(['3'])}

        """
        output, err = afs_instance.shell_command("show configuration map all", ret_code=False)
        if err:
            raise AFSException("Cannot get ASF MAP information! ERROR: %s, OUTPUT: %s" % (err, output, ))
        map_conf = output.splitlines()
        port_map = {}
        map_list = set()
        mid = None
        for rawid, value in enumerate(map_conf):
            # Search begin of Config Map section and store map id in mid variable
            val = re.search('^.*?Config Map.*: ([0-9]{1,4})$', map_conf[rawid])
            if val:
                mid = int(val.groups()[0])
                map_list.add(mid)
                continue
            # Search input ports if map id is found
            val = re.search('^.*?Input Ports.*: Ex0/([0-9]{1,2})$', map_conf[rawid])
            if val and mid:
                pid = int(val.groups()[0])
                if pid not in list(port_map.keys()):
                    port_map[pid] = set()
                port_map[pid].add(mid)
                continue
            # Search output ports if map id is found.
            # And clear map id because this field is last in section that we need.
            val = re.search('^.*?Output Ports.*: Ex0/([0-9]{1,2})$', map_conf[rawid])
            if val and mid:
                pid = int(val.groups()[0])
                if pid not in list(port_map.keys()):
                    port_map[pid] = set()
                port_map[pid].add(mid)
                mid = None
        return map_list, port_map

    @afs_conf_mode
    def _add_map(self, afs_instance=None, mid=None, pid1=None, pid2=None):
        """Add port configuration map.

        Args:
            afs_instance(CLIGenericMixin):  Instance of AFS device
            mid(str):  Configuration map
            pid1(str):  Port 1 ID
            pid2(str):  Port 2 ID

        Notes:
            Map is monodirectional pid1 -> pid2

        """
        # Switch(config)# configuration map 1
        # Switch(config-map-1)# input-ports extreme-ethernet 0/6 output-ports extreme-ethernet 0/25
        # Switch(config-map-1)# set description "Enter description here."
        # Switch(config-map-1)# set name "New Configuration Map"
        afs_instance.enter_mode("configuration map {0}".format(mid),
                                "Switch(config-map-{0})# ".format(mid))
        afs_instance.shell_command("input-ports extreme-ethernet 0/{0} output-ports extreme-ethernet 0/{1}".format(pid1, pid2), ret_code=False)
        afs_instance.shell_command("set name \"Map {0}. Ports 0/{1} -> 0/{2}\"".format(mid, pid1, pid2), ret_code=False)
        afs_instance.exit_mode("exit")

    @afs_conf_mode
    def _del_map(self, afs_instance=None, mid=None):
        """Delete configuration map.

        Args:
            afs_instance(CLIGenericMixin):  Instance of AFS device
            mid(str):  Configuration map

        """
        # Switch(config)# no configuration map 1
        afs_instance.shell_command('no configuration map %s' % mid, ret_code=False)

    def _del_port_config(self, port, port_map=None):
        """Delete maps mapped to port.

        Args:
            port(int):  Port ID
            port_map(dict):  Port map

        """
        # Delete all maps mapped to port.
        if port in port_map:
            for mid in port_map[port]:
                self._del_map(mid=mid)

    def _get_port(self, connection_element):
        """Get AFS port number from portmap.

        Args:
            connection_element(list):  Link information

        Raises:
            AFSException:  invalid port number in connection element

        Returns:
            int:  Port number

        """
        port = None
        for element in self.portmap:
            if element[0] == connection_element[0] and element[1] == connection_element[1]:
                port = element[2]
                break
        if not port:
            raise AFSException("Invalid ports number. Given device port number is not in configuration portmap.")
        return port

    def _get_ports_from_config(self, connection=None):
        """Return AFS port number from given connection.

        Args:
            connection(list):  Link information

        Returns:
            tuple: Port numbers

        """
        port1 = self._get_port(connection[2:])
        port2 = self._get_port(connection[:2])
        return port1, port2

    @afs_conf_mode
    def _set_port_disabled(self, afs_instance=None, pid=None):
        """Shutdown port.

        Args:
            afs_instance(CLIGenericMixin):  Instance of AFS device
            pid(int):  Port ID

        """
        # Switch(config)# interface extreme-ethernet 0/18
        # Switch(config-if)# shutdown
        # Switch(config-if)# exit
        afs_instance.enter_mode("interface extreme-ethernet 0/{0}".format(pid), "Switch(config-if)# ")
        afs_instance.shell_command("shutdown", ret_code=False)
        afs_instance.exit_mode("exit")

    @afs_conf_mode
    def _set_port_enabled(self, afs_instance=None, pid=None):
        """Turn On port.

        Args:
            afs_instance(CLIGenericMixin):  Instance of AFS device
            pid(int):  Port ID

        """
        # Switch(config)# interface extreme-ethernet 0/18
        # Switch(config-if)# no shutdown
        # Switch(config-if)# exit
        afs_instance.enter_mode("interface extreme-ethernet 0/{0}".format(pid), "Switch(config-if)# ")
        afs_instance.shell_command("no shutdown", ret_code=False)
        afs_instance.exit_mode("exit")

    @afs_conf_mode
    def _set_port_loopback(self, afs_instance=None, pid=None):
        """Set loopback on port.

        Args:
            afs_instance(CLIGenericMixin):  Instance of AFS device
            pid(int):  Port ID

        """
        # Switch(config)# interface extreme-ethernet 0/18
        # Switch(config-if)# loopback local
        # Switch(config-if)# exit
        afs_instance.enter_mode("interface extreme-ethernet 0/{0}".format(pid), "Switch(config-if)# ")
        afs_instance.shell_command("loopback local", ret_code=False)
        afs_instance.exit_mode("exit")

    def xconnect(self, connection=None):
        """Make cross connection device <-> device.

        Args:
            connection(list[int]):  Link info - list [dev1Id, dev1portId, dev2Id, dev2portId] ([0, 1, 1, 24])

        """
        self.class_logger.debug("Make connection: %s" % (connection, ))
        map_list, port_map = self._get_port_map()
        # Get AFS ports numbers
        ports = self._get_ports_from_config(connection)
        self.class_logger.debug("Connect AFS ports: %s<->%s" % (ports[0], ports[1]))
        # Clear config for port
        self._del_port_config(ports[0], port_map)
        self._del_port_config(ports[1], port_map)
        # Get free map IDs
        mids = get_unused_values(map_list, self.min_map_number, self.max_map_number)
        # Make connection
        self._add_map(mid=mids[0], pid1=ports[0], pid2=ports[1])
        self._add_map(mid=mids[1], pid1=ports[1], pid2=ports[0])

    # WORKAROUND BEGIN: To avoid situations when AFS port in down state, but actually the link is good.
    def reenable_port(self, port, dev_id):
        """Set Down and than Up status for AFS port connected to given port and device.

        Args:
            port(int):  Port ID
            dev_id(int):  Device ID

        Returns:
            bool:  True if workaround performed and False if skipped.

        """
        try:
            afs_port = self._get_port([dev_id, port])
        except AFSException:
            self.class_logger.info(("Skip down/up workaround for port_id {0} dev_id {1}. " +
                                    "Port is not in AFS portmap.").format(port, dev_id))
            self.class_logger.debug("AFS portmap: {0}".format(self.portmap))
            return False
        self.class_logger.info("Performing down/up workaround for port_id {0} dev_id {1}".format(port, dev_id))
        self._set_port_disabled(pid=afs_port)
        self._set_port_loopback(pid=afs_port)
        self._set_port_enabled(pid=afs_port)
        return True
        # WORKAROUND END

    def xdisconnect(self, connection=None):
        """Destroy cross connection device <-> device.

        Args:
            connection(list[int]):  Link info - list [dev1Id, dev1portId, dev2Id, dev2portId] ([0, 1, 1, 24])

        """
        _, port_map = self._get_port_map()
        # Get AFS ports numbers
        ports = self._get_ports_from_config(connection)
        # Clear config for port
        self._del_port_config(ports[0], port_map)
        self._del_port_config(ports[1], port_map)

    def __del__(self):
        """Disconnect all telnet connections to AFS on destroy.

        """
        self.class_logger.debug("Destroy AFS object.")
        self.clear_connection_pool()
