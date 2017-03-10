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

"""``ui_wrapper.py``

`XMLRPC UI wrappers`

"""

from abc import abstractmethod
# from abc import ABCMeta


class UiInterface(object):
    # disable this for now so we can instantiate subclasses without
    # all the abstract methods defined.  Re-enable once implemented
    # __metaclass__ = ABCMeta
    """Abstract class to store UI wrapper interface methods.

    """

    @abstractmethod
    def connect(self):
        """Mandatory method for UI wrapper connection.

        """
        pass

    @abstractmethod
    def disconnect(self):
        """Mandatory method for UI wrapper disconnection.

        """
        pass

    @abstractmethod
    def restart(self):
        """Perform device reboot via User Interface.

        """
        pass

# Clear Config
    @abstractmethod
    def clear_config(self):
        """Clear device configuration.

        """
        pass

    @abstractmethod
    def save_config(self):
        """Save device configuration.

        """
        pass

    @abstractmethod
    def restore_config(self):
        """Restore device configuration.

        """
        pass

# Application Check
    @abstractmethod
    def check_device_state(self):
        """Attempts to connect to the shell retries number of times.

        """

# Platform
    @abstractmethod
    def get_table_platform(self):
        """Get 'Platform' table.

        """
        pass

# Syslog configuration
    @abstractmethod
    def create_syslog(self, syslog_proto, syslog_ip, syslog_port, syslog_localport, syslog_transport, syslog_facility, syslog_severity):
        """Configure Syslog settings.

        Args:
            syslog_proto(str):  syslog host protocol Udp | Tcp
            syslog_ip(str):  syslog host IP address
            syslog_port(int):  syslog host port
            syslog_localport(int):  syslog host local port
            syslog_transport(str):  syslog host transport
            syslog_facility(int):  syslog host facility
            syslog_severity(str):  syslog host severity

        """
        pass

    @abstractmethod
    def logs_add_message(self, level, message):
        """Add message into device logs.

        Args:
            level(str):  log severity
            message(str):  log message

        """
        pass

# Temperature information
    @abstractmethod
    def get_temperature(self):
        """Get temperature from Sensors table.

        Returns:
            dict:  CPU temperature information (Sensors table)

        """
        pass

# System information
    @abstractmethod
    def get_memory(self, mem_type='usedMemory'):
        """Returns free cached/buffered memory from switch.

        Args:
            mem_type(str):  memory type

        Returns:
            float::  memory size

        """
        pass

    @abstractmethod
    def get_cpu(self):
        """Returns cpu utilization from switch.

        Returns:
            float:  cpu utilization from switch

        """
        pass

# Applications configuration
    @abstractmethod
    def get_table_applications(self):
        """Get 'Applications' table.

        Returns:
            list[dict]: 'Applications' table

        """
        pass

    @abstractmethod
    def configure_application(self, application, loglevel):
        """Set application loglevel.

        Args:
            application(str):  Application Name.
            loglevel(str):  Application loglevel.

        Returns:
            None

        Example::

            env.switch[1].ui.configure_application('L1PortControlApp', 'Debug')

        """
        pass

# STP configuration
    @abstractmethod
    def configure_spanning_tree(self, **kwargs):
        """Configure 'SpanningTree' table.

        Args:
            kwargs(dict):  Possible parameters from 'SpanningTree' table to configure:
                           "enable" - globally enable STP;
                           "mode" - set STP mode. RSTP|MSTP|STP;
                           "maxAge" - set maxAge value;
                           "forwardDelay" - set forwardDelay value;
                           "bridgePriority" - set bridgePriority value;
                           "bpduGuard" - set bpduGuard value;
                           "forceVersion" - set forceVersion value;
                           "mstpciName" - set mstpciName value.

        Returns:
            None

        Example::

            env.switch[1].ui.configure_spanning_tree(mode='MSTP')

        """
        pass

    @abstractmethod
    def create_stp_instance(self, instance, priority):
        """Create new STP instance in 'STPInstances' table.

        Args:
            instance(int):  Instance number.
            priority(int):  Instance priority.

        Returns:
            None

        Examples::

            env.switch[1].ui.create_stp_instance(instance=3, priority=2)

        """
        pass

    @abstractmethod
    def configure_stp_instance(self, instance, **kwargs):
        """Configure existing STP instance.

        Args:
            instance(int):  Instance number.
            **kwargs(dict):  Possible parameters to configure.
                             "priority" - change instance priority;
                             "vlan" - assign instance to the existed vlan.

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_stp_instance(instance=3, priority=2)  # change instance priority
            env.switch[1].ui.configure_stp_instance(instance=3, vlan=10)  # assign instance to the existed vlan

        """
        pass

    @abstractmethod
    def get_table_spanning_tree(self):
        """Get 'SpanningTree' table.

        Returns:
            list(dict): table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_spanning_tree()

        """
        pass

    @abstractmethod
    def get_table_spanning_tree_mst(self):
        """Get 'STPInstances' table

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_spanning_tree_mst()

        """
        pass

    @abstractmethod
    def get_table_mstp_ports(self, ports=None, instance=None):
        """Get 'MSTPPorts' table.

        Notes:
            Return all table or information about particular ports and STP instance.

        Args:
            ports(list):  list of ports.
            instance(int):  Instance number(int).

        Returns:
            list(dict): table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_mstp_ports()
            env.switch[1].ui.get_table_mstp_ports([1, 2])
            env.switch[1].ui.get_table_mstp_ports([1, 2], instance=3)

        """
        pass

    @abstractmethod
    def modify_mstp_ports(self, ports, instance=0, **kwargs):
        """Modify records in 'MSTPPorts' table.

        Args:
            ports(list):  list of ports.
            instance(int):  Instance number.
            **kwargs(dict): Parameters to be modified. Parameters names should be the same as in XMLRPC nb.MSTPPorts.set.* calls
                            "adminState" - change adminState;
                            "portFast" - set portFast value;
                            "rootGuard" - set rootGuard value;
                            "bpduGuard" - set bpduGuard value;
                            "autoEdgePort" - set autoEdgePort value;
                            "adminPointToPointMAC" - set adminPointToPointMAC value;
                            "externalCost" - set externalCost value;
                            "internalCost" - set internalCost value.

        Returns:
            None

        Examples::

            env.switch[1].ui.modify_mstp_ports([1, 2], instance=3, adminState='Enabled')

        """
        pass

    @abstractmethod
    def modify_rstp_ports(self, ports, **kwargs):
        """Modify records in 'RSTPPorts' table.

        Args:
            ports(list):  list of ports.
            **kwargs(dict):  Parameters to be modified. Parameters names should be the same as in XMLRPC nb.RSTPPorts.set.* calls
                             "adminState" - change adminState;
                             "portFast" - set portFast value;
                             "rootGuard" - set rootGuard value;
                             "bpduGuard" - set bpduGuard value;
                             "autoEdgePort" - set autoEdgePort value;
                             "adminPointToPointMAC" - set adminPointToPointMAC value;
                             "cost" - set cost value.

        Returns:
            None

        Examples::

            env.switch[1].ui.modify_rstp_ports([1, 2], adminState='Enabled')

        """
        pass

    @abstractmethod
    def get_table_rstp_ports(self, ports=None):
        """Get 'MSTPPorts' table.

        Notes:
            Return all table or information about particular ports.

        Args:
            ports(list):  list of ports.

        Returns:
            list(dict): table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_rstp_ports()
            env.switch[1].ui.get_table_rstp_ports([1, 2])

        """
        pass

# Ports configuration
    @abstractmethod
    def set_all_ports_admin_disabled(self):
        """Set all ports into admin Down state.

        Notes:
            This method is used in helpers.set_all_ports_admin_disabled() for all functional test case.

        Returns:
            None

        """
        pass

    @abstractmethod
    def wait_all_ports_admin_disabled(self):
        """Wait for all ports into admin Down state.

        Notes:
            This method is used in helpers.set_all_ports_admin_disabled() for all functional test case.

        Returns:
            None

        """
        pass

    @abstractmethod
    def modify_ports(self, ports, **kwargs):
        """Modify records in 'Ports' table.

        Args:
            ports(list(int)):  list of ports.
            **kwargs(dict): Parameters to be modified. Parameters names should be the same as in XMLRPC nb.Ports.set.* calls:
                            "pvid" - set pvid value;
                            "pvpt" - set pvpt value;
                            "adminMode" - set adminMode value;
                            "ingressFiltering" - set ingressFiltering value;
                            "maxFrameSize" - set maxFrameSize value;
                            "discardMode" - set discardMode value;
                            "cutThrough" - set cutThrough value;
                            "flowControl" - set flowControl value;
                            "speed" - set speed value;
                            "learnMode" - set learnMode value.

        Returns:
            None

        Examples::

            env.switch[1].ui.modify_ports([1, 2], adminMode='Down')

        """
        pass

    @abstractmethod
    def get_table_ports(self, ports=None, all_params=False):
        """Get 'Ports' table.

        Args:
            ports(list):  list of port IDs.
            all_params(bool):  get additional port properties

        Returns:
            list(dict): table (list of dictionaries)

        Notes:
            Return all table or information about particular ports.

        Examples::

            env.switch[1].ui.get_table_ports()
            env.switch[1].ui.get_table_ports([1, 2])

        """
        pass

# Flow Confrol configuration
    @abstractmethod
    def set_flow_control_type(self, ports=None, control_type=None):
        """Enable/disable sending/accepting pause frames

        Args:
            ports(list): list of port IDs
            control_type(str): 'Rx', 'Tx', 'RxTx' and 'None'

        Returns:
            None

        Examples::

            env.switch[1].ui.set_flow_control([1, 2], 'RxTx')

        """
        pass

# Ustack configuration
    @abstractmethod
    def start_ustack_with_given_mesh_ports(self, mesh_ports=tuple(), dbglevel=0):
        """Start ustack with given mesh ports on command line.

        Args:
            mesh_ports(list):  List of mesh ports given by command line user
            dbglevel(int):  dbglevel value

        Returns:
            Success or failure report.

        Examples::

            env.switch[1].ui.start_ustack_with_given_mesh_ports('sw0p1,sw0p2')

        """
        pass

# Vlan configuration
    @abstractmethod
    def create_vlans(self, vlans=None):
        """Create new Vlans

        Args:
            vlans(list[int]):  list of vlans to be created.

        Returns:
            None

        Examples::

            env.switch[1].ui.create_vlans([2, 3])

        """
        pass

    @abstractmethod
    def delete_vlans(self, vlans=None):
        """Delete existing Vlans.

        Args:
            vlans(list[int]):  list of vlans to be deleted.

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_vlans([2, 3])

        """
        pass

    @abstractmethod
    def get_table_vlans(self):
        """Get 'Vlans' table.

        Returns:
            list(dict): table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_vlans()

        """
        pass

    @abstractmethod
    def create_vlan_ports(self, ports=None, vlans=None, tagged='Tagged'):
        """Create new Ports2Vlans records.

        Args:
            ports(list[int]):  list of ports to be added to Vlans.
            vlans(list[int] | set(int)):  list of vlans.
            tagged(str):  information about ports tagging state.

        Returns:
            None

        Examples::

            Port 1 will be added into the vlans 3 and 4 as Untagged and port 2 will be added into the vlans 3 and 4 as Untagged
            env.switch[1].ui.create_vlan_ports([1, 2], [3, 4], 'Untagged')

        """
        pass

    @abstractmethod
    def delete_vlan_ports(self, ports=None, vlans=None):
        """Delete Ports2Vlans records.

        Args:
            ports(list[int]):  list of ports to be added to Vlans.
            vlans(list[int]):  list of vlans.

        Returns:
            None

        Examples::

            Ports 1 and 2 will be removed from the vlan 3:
            env.switch[1].ui.delete_vlan_ports([1, 2], [3, ])

        """
        pass

    @abstractmethod
    def modify_vlan_ports(self, ports=None, vlans=None, tagged='Tagged'):
        """Modify Ports2Vlans records.

        Args:
            ports(list):  list of ports to be added to Vlans.
            vlans(list[int] | set(int)):  list of vlans.
            tagged(str):  information about ports tagging state.

         Returns:
            None

        Examples::

            Port 1 will be modified in the vlans 3 and 4 as Tagged
            env.switch[1].ui.create_vlan_ports([1, ], [3, 4], 'Tagged')

        """
        pass

    @abstractmethod
    def get_table_ports2vlans(self):
        """Get 'Ports2Vlans' table.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_ports2vlans()

        """
        pass

# ACL configuration
    @abstractmethod
    def create_acl_name(self, acl_name=None):
        """Create ACL name.

        Args:
            acl_name(str):  ACL name to be created

        Returns:
            None

        Examples::

            env.switch[1].ui.create_acl_name('Test-1')

        """
        pass

    @abstractmethod
    def add_acl_rule_to_acl(self, acl_name=None, rule_id='', action=None, conditions=None):
        """Add rule to ACL.

        Args:
            acl_name(str):  ACL name where rule is added to.
            rule_id(str|int):  Rule Id used for adding.
            action(list[str]):  ACL Action
            conditions(list[list[str]]):  List of ACL conditions

        Returns:
            None

        Examples::

            env.switch[1].ui.add_acl_rule_to_acl(acl_name='Test-1',
                                                 rule_id=1,
                                                 action=['forward', '1'],
                                                 conditions=[['ip-source',
                                                             '192.168.10.10',
                                                             '255.255.255.255']])

        """
        pass

    @abstractmethod
    def bind_acl_to_ports(self, acl_name=None, ports=None):
        """Bind ACL to ports.

        Args:
            acl_name(str):  ACL name
            ports(list[int]):  list of ports where ACL will be bound.

        Returns:
            None

        Examples::

            env.switch[1].ui.bind_acl_to_ports(acl_name='Test-1', ports=[1, 2, 3])

        """
        pass

    @abstractmethod
    def unbind_acl(self, acl_name=None):
        """Unbind ACL.

        Args:
            acl_name(str):  ACL name

        Returns:
            None

        Examples::

            env.switch[1].ui.unbind_acl('Test-1')

        """
        pass

    @abstractmethod
    def create_acl(self, ports=None, expressions=None, actions=None, rules=None, acl_name='Test-ACL'):
        """Create ACLs.

        Args:
            ports(list[int]):  list of ports where ACLs will be created.
            expressions(list[list]):  list of ACL expressions.
            actions(list[list]):  list of ACL actions.
            rules(list[list]):  list of ACL rules.
            acl_name(str):  ACL name to which add rules

        Returns:
            None

        Examples::

            env.switch[1].ui.create_acl(ports=[1, 2], expressions=[[1, 'SrcMac', 'FF:FF:FF:FF:FF:FF', '00:00:00:11:11:11'], ],
                                        actions=[[1, 'Drop', ''], ], [[1, 1, 1, 'Ingress', 'Enabled', 0], ])

        """
        pass

    @abstractmethod
    def delete_acl(self, ports=None, expression_ids=None, action_ids=None, rule_ids=None, acl_name=None):
        """Delete ACLs.

        Args:
            ports(list[int]):  list of ports where ACLs will be deleted (mandatory).
            expression_ids(list[int]):  list of ACL expression IDs to be deleted (optional).
            action_ids( list[int]):  list of ACL action IDs to be deleted (optional).
            rule_ids(list[int]):  list of ACL rule IDs to be deleted (optional).
            acl_name(str):  ACL name

        Returns:
            None

        Example::

            env.switch[1].ui.delete_acl(ports=[1, 2], rule_ids=[1, 2])

        """
        pass

    @abstractmethod
    def get_table_acl(self, table=None, acl_name=None):
        """Get ACL table.

        Args:
            table(str):  ACL table name to be returned. ACLStatistics|ACLExpressions|ACLActions
            acl_name(str):  ACL name

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_acl('ACLStatistics')

        """
        pass

    @abstractmethod
    def get_acl_names(self):
        """Get ACL names.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_acl_names()

        """
        pass

# FDB configuration
    @abstractmethod
    def create_static_macs(self, port=None, vlans=None, macs=None):
        """Create static FDB records.

        Args:
            port(int):  port where static Fbds will be created (mandatory).
            vlans( list[int]):  list of vlans where static Fbds will be created (mandatory).
            macs(list[str]):  list of MACs to be added (mandatory).

        Returns:
            None

        Examples::

            env.switch[1].ui.create_static_macs(10, [1, 2], ['00:00:00:11:11:11', ])

        """
        pass

    @abstractmethod
    def delete_static_mac(self, port=None, vlan=None, mac=None):
        """Delete static FDB records.

        Args:
            port(int):  port where static Fbds will be deleted.
            vlan(list[int]):  list of vlans where static Fbds will be deleted (mandatory).
            mac(list[str]):  list of MACs to be deleted (mandatory).

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_static_mac([1, 2], ['00:00:00:11:11:11', ])

        """
        pass

    @abstractmethod
    def get_table_fdb(self, table='Fdb'):
        """Get Fbd table.

        Args:
            table(str):  Fbd record type to be returned ('Fbd' or 'Static')

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_fdb()
            env.switch[1].ui.get_table_fdb('Static')

        """
        pass

    @abstractmethod
    def clear_table_fdb(self):
        """Clear Fdb table.

        Returns:
            None

        Examples::

            env.switch[1].ui.clear_table_fdb()

        """
        pass

# QoS configuration

    @abstractmethod
    def get_table_ports_qos_scheduling(self, port=None, param=None):
        """Get PortsQoS scheduling information.

        Args:
            port(int):  port Id to get info about
            param(str):  param name to get info about

        Returns:
            list[dict] | str | int: table (list of dictionaries) or dictionary or param value

        Examples::

            env.switch[1].ui.get_table_ports_qos_scheduling(port=1, param='schedMode')
            env.switch[1].ui.get_table_ports_qos_scheduling('Static')

        """
        pass

    @abstractmethod
    def get_table_ports_dot1p2cos(self, port=None, rx_attr_flag=True):
        """Get PortsDot1p2CoS table.

        Args:
            port(str|int):  port Id to get info about ('All' or port id)
            rx_attr_flag(bool):  whether get rx or tx attribute information

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_ports_dot1p2cos(1)
            env.switch[1].ui.get_table_ports_dot1p2cos('All')

        """
        pass

    @abstractmethod
    def configure_cos_global(self, **kwargs):
        """Configure global mapping of ingress VLAN priority to CoS per port or per switch (PortsDot1p2CoS records).

        Args:
            **kwargs(dict):  parameters to be modified

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_cos_global(dotp2CoS=6)

        """
        pass

    @abstractmethod
    def configure_dscp_to_cos_mapping_global(self, **kwargs):
        """Configure PortsDscp2CoS records.

        Args:
            *kwargs(dict):  parameters to be modified

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_dscp_to_cos_mapping_global(dscp0CoS=6)

        """
        pass

    @abstractmethod
    def get_table_ports_dscp2cos(self):
        """Get PortsDscp2CoS records.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_ports_dscp2cos()

        """
        pass

    @abstractmethod
    def configure_schedweight_to_cos_mapping(self, ports, **kwargs):
        """Configure schedweight to cos mapping.

        Args:
            ports(list[int]):  list of port Ids
            **kwargs(dict):  parameters to be modified

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_schedweight_to_cos_mapping(ports=[1,2], schedWeight0=35)

        """
        pass

    @abstractmethod
    def configure_port_cos(self, ports=None, **kwargs):
        """Configure PortsQoS records.

        Args:
            ports(list[int]):  list of ports to be modified
            **kwargs(dict):  parameters to be modified

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_port_cos([1, ], trustMode='Dot1p')

        """
        pass

    @abstractmethod
    def create_dot1p_to_cos_mapping(self, ports, rx_attr_flag=False, **kwargs):
        """Configure mapping of ingress VLAN priority to CoS per port or per switch (PortsDot1p2CoS mapping).

        Args:
            ports(list[int]):  list of ports to be modified
            rx_attr_flag(bool):  whether rx or tx attribute to be modified
            **kwargs(dict):  parameters to be modified

        Returns:
            None

        Examples::

            env.switch[1].ui.create_dot1p_to_cos_mapping([1, ], dotp7CoS=6)

        """
        pass

    @abstractmethod
    def modify_dot1p_to_cos_mapping(self, ports, rx_attr_flag=False, **kwargs):
        """Modify mapping of ingress VLAN priority to CoS per port or per switch (PortsDot1p2CoS mapping).

        Args:
            ports(list[int]):  list of ports to be modified
            rx_attr_flag(bool):  whether rx or tx attribute to be modified
            **kwargs(dict):  parameters to be modified

        Returns:
            None

        Examples::

            env.switch[1].ui.modify_dot1p_to_cos_mapping([1, ], dotp7CoS=6)

        """
        pass

    @abstractmethod
    def clear_per_port_dot1p_cos_mapping(self, ports, rx_attr_flag=False, dot1p=None):
        """Clear PortsDot1p2CoS mapping.

        Args:
            ports(list[int]):  list of ports to be modified
            rx_attr_flag(bool):  whether to use rx attribute or tx attribute
            dot1p(list[int]):  list of Dot1p priority required to clear.

        Examples::

            env.switch[1].ui.clear_per_port_dot1p_cos_mapping(ports=[port1, ], dot1p=[6, ])

        """
        pass

# Statistics configuration
    @abstractmethod
    def map_stat_name(self, generic_name):
        """Get the UI specific stat name for given generic name.

        Args:
            generic_name(str): generic statistic name

        Returns:
            str: UI specific stat name

        """
        pass

    @abstractmethod
    def get_table_statistics(self, port=None, stat_name=None):
        """Get Statistics table.

        Args:
            port(str|int|None):  port Id to get info about ('cpu' or port id) (optional)
            stat_name(str):  name of statistics parameter (optional)

        Returns:
            list[dict]|int:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_statistics()
            env.switch[1].ui.get_table_statistics(port=1)
            env.switch[1].ui.get_table_statistics(port='cpu')

        """
        pass

    @abstractmethod
    def clear_statistics(self):
        """Clear Statistics.

        Returns:
            None

        Examples:

            env.switch[1].ui.clear_statistics()

        """
        pass

# Bridge Info configuration
    @abstractmethod
    def get_table_bridge_info(self, param=None, port=None):
        """Get Bridge Info table or specific parameter value in Bridge Info table

        Args:
            param(str):  parameter name (optional)
            port(int):  port ID (optional)

        Returns:
            list[dict]|str|int: table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_bridge_info()
            env.switch[1].ui.get_table_bridge_info('agingTime')

        """
        pass

    @abstractmethod
    def modify_bridge_info(self, **kwargs):
        """Modify BridgeInfo table.

        Args:
            **kwargs(dict):  Parameters to be modified:
                             "agingTime" - set agingTime value;
                             "defaultVlanId" - set defaultVlanId value.

        Returns:
            None

        Examples::

            env.switch[1].ui.modify_bridge_info(agingTime=5)

        """
        pass

# LAG configuration
    @abstractmethod
    def create_lag(self, lag=None, key=None, lag_type='Static', hash_mode='None'):
        """Create LAG instance.

        Args:
            lag(int):  LAG id
            key(int):  LAG key
            lag_type(str):  LAG type. 'Static'|'Dynamic'
            hash_mode(str):  LAG hash type:
                             'None'|'SrcMac'|'DstMac'|'SrcDstMac'|'SrcIp'|'DstIp'|
                             'SrcDstIp'|'L4SrcPort'|'L4DstPort'|'L4SrcPort,L4DstPort'|
                             'OuterVlanId'|'InnerVlanId'|'EtherType'|'OuterVlanPri'|
                             'InnerVlanPri'|'Dscp'|'IpProtocol'|'DstIp,L4DstPort'|
                             'SrcIp,L4SrcPort'|'SrcMac,OuterVlanId'|'DstMac,OuterVlanId'|
                             'SrcIp,DstIp,L4SrcPort'|'DstIp,IpProtocol'|'SrcIp,IpProtocol'|'Ip6Flow'

        Returns:
            None

        Examples::

            env.switch[1].ui.create_lag(3800, 1, 'Static', 'None')

        """
        pass

    @abstractmethod
    def delete_lags(self, lags=None):
        """Delete LAG instance.

        Args:
            lags(list[int]):  list of LAG Ids

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_lags([3800, ])

        """
        pass

    @abstractmethod
    def get_table_lags(self):
        """Get LagsAdmin table.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_lags()

        """
        pass

    @abstractmethod
    def modify_lags(self, lag, key=None, lag_type=None, hash_mode=None):
        """Modify LagsAdmin table.

        Args:
            lag(int):  LAG id
            key(int):  LAG key
            lag_type(str):  LAG type (Static or Dynamic)
            hash_mode():  LAG hash mode

        Returns:
            None

        Examples:

            env.switch[1].ui.modify_lags(lag=3800, lag_type="Static")

        """
        pass

    @abstractmethod
    def get_table_link_aggregation(self):
        """Get LinkAggregation table.

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_link_aggregation()

        """
        pass

    @abstractmethod
    def modify_link_aggregation(self, globalenable=None, collectormaxdelay=None, globalhashmode=None, priority=None, lacpenable=None):
        """Modify LinkAggregation table.

        Args:
            globalenable(str):  globalEnable parameter value
            collectormaxdelay(int):  collectorMaxDelay parameter value
            globalhashmode(str):  globalHashMode parameter value
            priority(int):  priority parameter value
            lacpenable(str):  lacpEnable parameter value

        Returns:
            None

        Examples::

            env.switch[1].ui.modify_link_aggregation(globalhashmode='SrcMac')

        """
        pass

    @abstractmethod
    def create_lag_ports(self, ports, lag, priority=1, key=None, aggregation='Multiple', lag_mode='Passive', timeout='Long', synchronization=False,
                         collecting=False, distributing=False, defaulting=False, expired=False, partner_system='00:00:00:00:00:00', partner_syspri=32768,
                         partner_number=1, partner_key=0, partner_pri=32768):
        """Add ports into created LAG.

        Args:
            ports( list[int]):  list of ports to be added into LAG
            lag(int):  LAG Id
            priority(int):  LAG priority
            key(int):  LAG key
            aggregation(str):  LAG aggregation
            lag_mode(str):  LAG mode
            timeout(str):  LAG timeout
            synchronization(bool):  LAG synchronization
            collecting(bool):  LAG collecting
            distributing(bool):  LAG distributing
            defaulting(bool):  LAG defaulting
            expired(bool):  LAG expired
            partner_system(str):  LAG partner system MAC address
            partner_syspri(int):  LAG partner system priority
            partner_number(int):  LAG partner number
            partner_key(int):  LAG partner key
            partner_pri(int):  LAG partner priority

        Returns:
            None

        Examples::

            env.switch[1].ui.create_lag_ports([1, ], 3800, priority=1, key=5)

        """
        pass

    @abstractmethod
    def delete_lag_ports(self, ports, lag):
        """Delete ports from created LAG.

        Args:
            ports(list[int]):  list of ports to be added into LAG
            lag(int):  LAG Id

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_lag_ports([1, ], 3800)

        """
        pass

    @abstractmethod
    def get_table_ports2lag(self):
        """Get Ports2LagAdmin table.

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_ports2lag()

        """
        pass

    @abstractmethod
    def modify_ports2lag(self, port, lag, priority=None, key=None, aggregation=None, lag_mode=None, timeout=None, synchronization=None,
                         collecting=None, distributing=None, defaulting=None, expired=None, partner_system=None, partner_syspri=None,
                         partner_number=None, partner_key=None, partner_pri=None):
        """Modify Ports2LagAdmin table.

        Args:
            port(int):  LAG port
            lag(int):  LAG Id
            priority(int):  port priority
            key(int):  port key
            aggregation(str):  port aggregation (multiple or individual)
            lag_mode(str):  LAG mode (Passive or Active)
            timeout(str):  port timeout (Short or Long)
            synchronization(str):  port synchronization (True or False)
            collecting(str):  port collecting (True or False)
            distributing(str):  port distributing (True or False)
            defaulting(str):  port defaulting state (True or False)
            expired(str):  port expired state (True or False)
            partner_system(str):  partner LAG MAC address
            partner_syspri(int):  partner LAG  priority
            partner_number(int):  partner port number
            partner_key(int):  partner port key
            partner_pri(int):  partner port priority

        Returns:
            None

        Examples::

            env.switch[1].ui.modify_ports2lag(1, 3800, priority=100)

        """
        pass

    @abstractmethod
    def get_table_lags_local(self, lag=None):
        """Get LagsLocal table.

        Args:
            lag(int):  LAG Id

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_lags_local()
            env.switch[1].ui.get_table_lags_local(3800)

        """
        pass

    @abstractmethod
    def get_table_lags_local_ports(self, lag=None):
        """Get Ports2LagLocal table.

        Args:
            lag(int):  LAG Id

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_lags_local_ports()
            env.switch[1].ui.get_table_lags_local_ports(3800)

        """
        pass

    @abstractmethod
    def get_table_lags_remote(self, lag=None):
        """Get LagsRemote table.

        Args:
            lag(int):  LAG Id

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_lags_remote()
            env.switch[1].ui.get_table_lags_remote(3800)

        """
        pass

    @abstractmethod
    def get_table_lags_remote_ports(self, lag=None):
        """Get Ports2LagRemote table.

        Args:
            lag(int):  LAG Id

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_lags_remote_ports()
            env.switch[1].ui.get_table_lags_remote_ports(lag=3800)

        """
        pass

# IGMP configuration
    @abstractmethod
    def configure_igmp_global(self, mode='Enabled', router_alert=None, unknown_igmp_behavior=None, query_interval=None, querier_robustness=None):
        """Modify IGMPSnoopingGlobalAdmin table.

        Args:
            mode(str):  mode parameter value. 'Enabled'|'Disabled'
            router_alert(str):  routerAlertEnforced parameter value. 'Enabled'|'Disabled'
            unknown_igmp_behavior(str):  unknownIgmpBehavior parameter value. 'Broadcast'|'Drop'
            query_interval(int):  queryInterval parameter value
            querier_robustness(int):  querierRobustness parameter value

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_igmp_global(mode='Enabled')

        """
        pass

    @abstractmethod
    def configure_igmp_per_ports(self, ports, mode='Enabled', router_port_mode=None):
        """Modify IGMPSnoopingPortsAdmin table.

        Args:
            ports(list[int]):  list of ports
            mode(str):  igmpEnabled parameter value. 'Enabled'|'Disabled'
            router_port_mode(str):  routerPortMode parameter value. 'Auto'|'Always'

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_igmp_per_ports([1, 2], mode='Enabled')

        """
        pass

    @abstractmethod
    def create_multicast(self, port, vlans, macs):
        """Create StaticL2Multicast record.

        Args:
            port(int):  port Id
            vlans(list[int]):  list of vlans
            macs(list[str]):  list of multicast MACs

        Returns:
            None

        Examples::

            env.switch[1].ui.create_multicast(10, [5, ], ['01:00:05:11:11:11', ])

        """
        pass

    @abstractmethod
    def delete_multicast(self, port=None, vlan=None, mac=None):
        """Delete StaticL2Multicast record.

        Args:
            port(int):  port Id
            vlan(int):  vlan Id
            mac(str):  multicast MAC

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_multicast(10, 5, '01:00:05:11:11:11')

        """
        pass

    @abstractmethod
    def get_table_l2_multicast(self):
        """Get L2Multicast table.

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_l2_multicast()

        """
        pass

    @abstractmethod
    def get_table_igmp_snooping_global_admin(self, param=None):
        """Get IGMPSnoopingGlobalAdmin table.

        Args:
            param(str):  parameter name

        Returns:
            list[dict]|int|str:  table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_igmp_snooping_global_admin()
            env.switch[1].ui.get_table_igmp_snooping_global_admin('queryInterval')

        """
        pass

    @abstractmethod
    def get_table_igmp_snooping_port_oper(self, port, param=None):
        """Get IGMPSnoopingPortsOper table.

        Args:
            port(int):  port Id
            param(str):  parameter name

        Returns:
            list[dict]|int|str: table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_igmp_snooping_port_oper()
            env.switch[1].ui.get_table_igmp_snooping_port_oper('queryInterval')

        """
        pass

    @abstractmethod
    def clear_l2_multicast(self):
        """Clear L2Multicast table.

        Returns:
            None

        Examples::

            env.switch[1].ui.clear_l2_multicast()

        """
        pass

# L3 configuration
    @abstractmethod
    def configure_routing(self, routing='Enabled', ospf=None):
        """Configure L3 routing.

        Args:
            routing(str):  enable L3 routing
            ospf(str|None):  enable OSPF. None|'Enabled'

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_routing(routing='Enabled', ospf='Enabled')

        """
        pass

    @abstractmethod
    def create_route_interface(self, vlan, ip, ip_type='InterVlan', bandwidth=1000, mtu=1500, status='Enabled', vrf=0, mode='ip'):
        """Create Route Interface.

        Args:
            vlan(int):  vlan Id
            ip(str):  Route Interface network
            ip_type(str):  Route interface type
            bandwidth(int):  Route interface bandwidth
            mtu(int):  Route interface mtu
            status(str):  Route interface status
            vrf(int):  Route interface vrf
            mode(str):  'ip' or 'ipv6'

        Returns:
            None

        Examples::

            env.switch[1].ui.create_route_interface(10, '10.0.5.101/24', 'InterVlan', 1000, 1500, 'Enabled, 0, 'ip')
            env.switch[1].ui.create_route_interface(10, '2000::01/96', 'InterVlan', 1000, 1500, 'Enabled, 0, 'ipv6')

        """
        pass

    @abstractmethod
    def delete_route_interface(self, vlan, ip, bandwith=1000, mtu=1500, vrf=0, mode='ip'):
        """Delete Route Interface.

        Args:
            vlan(int):  vlan Id
            ip(str):  Route Interface network
            bandwith(int):  Route interface bandwidth
            mtu(int):  Route interface mtu
            vrf(int):  Route interface vrf
            mode(str):  'ip' or 'ipv6'

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_route_interface(10, '10.0.5.101/24', 1000, 1500, 0, 'ip')
            env.switch[1].ui.create_route_interface(10, '2000::01/96', 1000, 1500, 0, 'ipv6')

        """
        pass

    @abstractmethod
    def modify_route_interface(self, vlan, ip, **kwargs):
        """Modify Route Interface.

        Args:
            vlan(int):  vlan Id
            ip(str):  Route Interface network
            **kwargs(dict):   parameters to be modified:
                             "adminMode" - set adminMode value.

        Returns:
            None

        Examples::

            env.switch[1].ui.modify_route_interface(10, '10.0.5.101/24', adminMode='Disabled')

        """
        pass

    @abstractmethod
    def get_table_route_interface(self):
        """Get RouteInterface table.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_route_interface()

        """
        pass

    @abstractmethod
    def get_table_route(self, mode='ip'):
        """Get Route table.

        Args:
            mode(str):  'ip' or 'ipv6'

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_route()

        """
        pass

    @abstractmethod
    def configure_arp(self, garp=None, refresh_period=None, delay=None, secure_mode=None, age_time=None, attemptes=None, arp_len=None):
        """Configure ARPConfig table.

        Args:
            garp(str):  AcceptGARP value. 'True'|'False'
            refresh_period(int):  RefreshPeriod value
            delay(int):  RequestDelay value
            secure_mode(str):  SecureMode value. 'True'|'False'
            age_time(int):  AgeTime value
            attemptes(int):  NumAttempts value
            arp_len(int):  length value for ARP

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_arp(garp='Enabled')

        """
        pass

    @abstractmethod
    def get_table_arp_config(self):
        """Get ARPConfig table.

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_arp_config()

        """
        pass

    @abstractmethod
    def create_arp(self, ip, mac, network, mode='arp'):
        """Create StaticARP record.

        Args:
            ip(str):  ARP ip address
            mac(str):  ARP mac address
            network(str):  RouteInterface network
            mode(str):  'arp' or 'ipv6 neigbor'

        Returns:
            None

        Examples::

            env.switch[1].ui.create_arp('10.0.5.102', '00:00:22:22:22', '10.0.5.101/24')

        """
        pass

    @abstractmethod
    def delete_arp(self, ip, network, mode='arp'):
        """Delete ARP record.

        Args:
            ip(str):  ARP ip address
            network(str):  RouteInterface network
            mode(str):  'arp' or 'ipv6 neigbor'

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_arp('10.0.5.102', '10.0.5.101/24')

        """
        pass

    @abstractmethod
    def get_table_arp(self, mode='arp'):
        """Get ARP table.

        Args:
            mode(str):  'arp' or 'ipv6 neigbor'

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_arp()

        """
        pass

    @abstractmethod
    def create_static_route(self, ip, nexthop, network, distance=-1, mode='ip'):
        """Create StaticRoute record.

        Args:
            ip(str):  Route IP network
            nexthop(str):  Nexthop IP address
            network(str):  RouteInterface network
            distance(int):  Route distance
            mode(str):  'ip' or 'ipv6'

        Returns:
            None

        Examples::

            env.switch[1].ui.create_static_route('20.20.20.0/24', '10.0.5.102', '10.0.5.101/24')

        """
        pass

    @abstractmethod
    def delete_static_route(self, network):
        """Delete StaticRoute record.

        Args:
            network(str):  RouteInterface network

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_static_route('10.0.5.101/24')

        """
        pass

    @abstractmethod
    def get_table_static_route(self, mode='ip'):
        """Get StaticRoute table.

        Args:
            mode(str):  'ip' or 'ipv6'

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_static_route()

        """
        pass

    @abstractmethod
    def configure_ospf_router(self, **kwargs):
        """Configure OSPFRouter table.

        Args:
            **kwargs(dict):  parameters to be modified:
                             "logAdjacencyChanges" - set logAdjacencyChanges value;
                             "routerId" - set routerId value.

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_ospf_router(routerId='1.1.1.1')

        """
        pass

    @abstractmethod
    def get_table_ospf_router(self):
        """Get OSPFRouter table.

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_ospf_router()

        """
        pass

    @abstractmethod
    def create_ospf_area(self, area, **kwargs):
        """Create OSPFAreas record.

        Args:
            area(int):  Area Id to be created
            **kwargs(dict):  parameters to be added

        Returns:
            None

        Examples::

            env.switch[1].ui.create_ospf_area("0.0.0.0")

        """
        pass

    @abstractmethod
    def get_table_ospf_area(self):
        """Get OSPFAreas table.

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_ospf_area()

        """
        pass

    @abstractmethod
    def create_network_2_area(self, network, area, mode):
        """Create OSPFNetworks2Area record.

        Args:
            network(str):  RouteInterface network
            area(int):  Area Id
            mode(str):  Area mode

        Returns:
            None

        Examples::

            env.switch[1].ui.create_network_2_area('10.0.5.101/24', "0.0.0.0", 'Disabled')

        """
        pass

    @abstractmethod
    def get_table_network_2_area(self):
        """Get OSPFNetworks2Area table.

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_network_2_area()

        """
        pass

    @abstractmethod
    def create_area_ranges(self, area, range_ip, range_mask, substitute_ip, substitute_mask):
        """Create OSPFAreas2Ranges record.

        Args:
            area(int):  Area Id
            range_ip(str):  IP address
            range_mask(str):  mask
            substitute_ip(str):  IP address
            substitute_mask(str):  mask

        Returns:
            None

        Examples::

            env.switch[1].ui.create_area_ranges("0.0.0.0", "10.0.2.0", "255.255.255.0", "11.0.2.0", "255.255.255.0")

        """
        pass

    @abstractmethod
    def get_table_area_ranges(self):
        """Get OSPFAreas2Ranges table.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_area_ranges()

        """
        pass

    @abstractmethod
    def create_route_redistribute(self, mode):
        """Create OSPFRouteRedistribute record.

        Args:
            mode(str):  redistribute mode

        Returns:
            None

        Examples::

            env.switch[1].ui.create_route_redistribute("Static")

        """
        pass

    @abstractmethod
    def get_table_route_redistribute(self):
        """Get OSPFRouteRedistribute table.

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_route_redistribute()

        """
        pass

    @abstractmethod
    def create_interface_md5_key(self, vlan, network, key_id, key):
        """Create OSPFInterfaceMD5Keys record.

        Args:
            vlan(int):  Vlan Id
            network(str):  Route Interface network
            key_id(int):  key Id
            key(str):  key

        Returns:
            None

        Example:

            env.switch[1].ui.create_interface_md5_key(10, "10.0.5.101/24", 1, "Key1")

        """
        pass

    @abstractmethod
    def get_table_interface_authentication(self):
        """Get OSPFInterfaceMD5Keys table.

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_interface_authentication()

        """
        pass

    @abstractmethod
    def create_ospf_interface(self, vlan, network, dead_interval=40, hello_interval=5, network_type="Broadcast", hello_multiplier=3, minimal='Enabled',
                              priority=-1, retransmit_interval=-1):
        """Create OSPFInterface record.

        Args:
            vlan(int):  Vlan Id
            network(str):  Route Interface network
            dead_interval(int):  dead interval
            hello_interval(int):  hello interval
            network_type(str):  network type
            hello_multiplier(int):  hello multiplier
            minimal(str):  minimal
            priority(int):  priority
            retransmit_interval(int):  retransmit interval

        Returns:
            None

        Examples::

            env.switch[1].ui.create_ospf_interface(vlan_id, "10.0.5.101/24", 40, 5, network_type='Broadcast', minimal='Enabled', priority=1, retransmit_interval=3)

        """
        pass

    @abstractmethod
    def get_table_ospf_interface(self):
        """Get OSPFInterface table.

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_interface_authentication()

        """
        pass

    @abstractmethod
    def create_area_virtual_link(self, area, link):
        """Create OSPFInterface record.

        Args:
            area(str):  OSPF Area
            link(str):  Virtual link IP

        Returns:
            None

        Examples::

            env.switch[1].ui.create_area_virtual_link("0.0.0.0", "1.1.1.2")

        """
        pass

# BGP configuration
    @abstractmethod
    def configure_bgp_router(self, asn=65501, enabled='Enabled'):
        """Modify BGPRouter record.

        Args:
            asn(int):  AS number
            enabled(str):  enabled status

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_bgp_router(asn=65501, enabled='Enabled')

        """
        pass

    @abstractmethod
    def create_bgp_neighbor_2_as(self, asn, ip, remote_as):
        """Create BGPNeighbor2As record.

        Args:
            asn(int):  AS number
            ip(str):  IP address
            remote_as(int):  Remote AS number

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_neighbor_2_as(65501, '10.0.5.102', 65502)

        """
        pass

    @abstractmethod
    def create_bgp_neighbor(self, asn=65501, ip='192.168.0.1'):
        """Create BGPNeighbor record.

        Args:
            asn(int):  AS number
            ip(str):  IP address

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_neighbor(asn=65501, ip='192.168.0.1')

        """
        pass

    @abstractmethod
    def create_bgp_neighbor_connection(self, asn=65501, ip='192.168.0.1', port=179):
        """Create BGPNeighborConnection record.

        Args:
            asn(int):  AS number
            ip(str):  IP address
            port(int):  connection port

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_neighbor_connection(asn=65501, ip='192.168.0.1', port=179)

        """
        pass

    @abstractmethod
    def create_bgp_bgp(self, asn=65501, router_id="1.1.1.1"):
        """Create BGPBgp record.

        Args:
            asn(int):  AS number
            router_id(int):  OSPF router Id

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_bgp(asn=65501, router_id="1.1.1.1")

        """
        pass

    @abstractmethod
    def create_bgp_peer_group(self, asn=65501, name="mypeergroup"):
        """Create BGPPeerGroups record.

        Args:
            asn(int):  AS number
            name(str):  peer group name

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_peer_group(65501, "test_name")

        """
        pass

    @abstractmethod
    def create_bgp_peer_group_member(self, asn=65501, name="mypeergroup", ip="12.1.0.2"):
        """Create BGPPeerGroupMembers record.

        Args:
            asn(int):  AS number
            name(str):  peer group name
            ip(str):  IP address

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_peer_group_member(65501, "test_name", "12.1.0.2")

        """
        pass

    @abstractmethod
    def create_bgp_redistribute(self, asn=65501, rtype="OSPF"):
        """Create BGPRedistribute record.

        Args:
            asn(int):  AS number
            rtype(str):  redistribute type

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_redistribute(65501, "OSPF")

        """
        pass

    @abstractmethod
    def create_bgp_network(self, asn=65501, ip='10.0.0.0', mask='255.255.255.0', route_map='routeMap'):
        """Create BGPNetwork record.

        Args:
            asn(int):  AS number
            ip(str):  IP address
            mask(str):  IP address mask
            route_map(str):  route map name

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_network(asn=65501, ip='10.0.0.0', mask='255.255.255.0', route_map='routeMap')

        """
        pass

    @abstractmethod
    def create_bgp_aggregate_address(self, asn=65501, ip='22.10.10.0', mask='255.255.255.0'):
        """Create BGPAggregateAddress record

        Args:
            asn(int):  AS number
            ip(str):  IP address
            mask(str):  IP address mask

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_aggregate_address(asn=65501, ip='10.0.0.0', mask='255.255.255.0')

        """
        pass

    @abstractmethod
    def create_bgp_confederation_peers(self, asn=65501, peers=70000):
        """Create BGPBgpConfederationPeers record.

        Args:
            asn(int):  AS number
            peers(int):  peers number

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_confederation_peers(asn=65501, peers=70000)

        """
        pass

    @abstractmethod
    def create_bgp_distance_network(self, asn=65501, ip="40.0.0.0/24", mask='255.255.255.0', distance=100, route_map='routeMap'):
        """Create BGPDistanceNetwork record.

        Args:
            asn(int):  AS number
            ip(str):  IP address
            mask(str):  IP address mask
            distance(int):  IP address distance
            route_map(str):  route map name

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_distance_network(asn=65501, ip="40.0.0.0", mask='255.255.255.0', distance=100, route_map='routeMap')

        """
        pass

    @abstractmethod
    def create_bgp_distance_admin(self, asn=65501, ext_distance=100, int_distance=200, local_distance=50):
        """Create BGPDistanceAdmin record.

        Args:
            asn(int):  AS number
            ext_distance(int):  external distance
            int_distance(int):  internal distance
            local_distance(int):  local distance

        Returns:
            None

        Examples::

            env.switch[1].ui.create_bgp_distance_admin(asn=65501, ext_distance=100, int_distance=200, local_distance=50)

        """
        pass

    @abstractmethod
    def get_table_bgp_neighbor(self):
        """Get BGPNeighbour table.

        Returns:
            list[dict]: table

        Examples::

            env.switch[1].ui.get_table_bgp_neighbor()

        """
        pass

    @abstractmethod
    def get_table_bgp_neighbor_connections(self):
        """Get BGPNeighborConnection table.

        Returns:
            list[dict]:  table

        Examples::

            env.switch[1].ui.get_table_bgp_neighbor_connections()

        """
        pass

    @abstractmethod
    def get_table_bgp_aggregate_address(self):
        """Get BGPAggregateAddress table.

        Returns:
            list[dict]:  table

        Examples::

            env.switch[1].ui.get_table_bgp_aggregate_address()

        """
        pass

    @abstractmethod
    def get_table_bgp_confederation_peers(self):
        """Get BGPBgpConfederationPeers table.

        Returns:
            list[dict] table

        Examples::

            env.switch[1].ui.get_table_bgp_confederation_peers()

        """
        pass

    @abstractmethod
    def get_table_bgp_distance_admin(self):
        """Get BGPDistanceAdmin table.

        Returns:
            list[dict]: table

        Examples::

            env.switch[1].ui.get_table_bgp_distance_admin()

        """
        pass

    @abstractmethod
    def get_table_bgp_distance_network(self):
        """Get BGPDistanceNetwork table.

        Returns:
            list[dict]: table

        Examples::

            env.switch[1].ui.get_table_bgp_distance_network()

        """
        pass

    @abstractmethod
    def get_table_bgp_network(self):
        """Get BGPNetwork table.

        Returns:
            list[dict]:  table

        Examples::

            env.switch[1].ui.get_table_bgp_network()

        """
        pass

    @abstractmethod
    def get_table_bgp_peer_group_members(self):
        """Get BGPPeerGroupMembers table.

        Returns:
            list[dict]: table

        Examples::

            env.switch[1].ui.get_table_bgp_peer_group_members()

        """
        pass

    @abstractmethod
    def get_table_bgp_peer_groups(self):
        """Get BGPPeerGroups table

        Returns:
            list[dict]:  table

        Example:

            env.switch[1].ui.get_table_bgp_peer_groups()

        """
        pass

    @abstractmethod
    def get_table_bgp_redistribute(self):
        """Get BGPRedistribute table.

        Returns:
            list[dict]: table

        Examples::

            env.switch[1].ui.get_table_bgp_redistribute()

        """
        pass

# HWOA Flow configuration
    @abstractmethod
    def create_match_api_tcam_subtable(self, source_id, table_id, table_name,
                                       max_table_entries, match_field_type_pairs,
                                       actions):
        """Create a sub-table of tcam.

        Args:
            source_id(int):  the source id in the tcam table.
            table_id(int):  a given table id.
                            If switchd running, table id starts from 5
                            If matchd is running, table id starts from 4
            table_name(str):  a given table name.
            max_table_entries(int):  maximum number of flows can be set.
            match_field_type_pairs(list[tuple(str, str)]):  list of given match field with match type
            actions(list[str]):  list of actions for configurable matches

        """
        pass

    @abstractmethod
    def create_match_api_rule(self, prio_id, handle_id, table_id,
                              match_field_value_mask_list, action, action_value=None):
        """Set a rule into the table.

        Args:
            prio_id(int):  Higher id has a higher priority.
            handle_id(int):  handle for match.
            table_id(int):  the source table id where match to be set.
            match_field_value_mask_list(list[tuple(str, str, str)]):  field with match field, value and mask.
            action(str):  given action for source table

        Raises:
            UIException:  for TypeError - Not enough arguments for format string
            UIException:  In case of Command execution Error reported in MatchAPI

        """
        pass

    @abstractmethod
    def get_table_match_api(self, table_id=None):
        """Lists the match api tables.

        Args:
            table_id(int):  table ID

        Returns:
            list[dict]

        """
        pass

    @abstractmethod
    def get_rules_match_api(self, table_id=None, handle_id=None):
        """Lists the match api rules of the table.

        Args:
            table_id(int):  table ID (mandatory parameter)
            handle_id(int):  optional parameter

        Returns:
            list[dict]

        """

        pass

    @abstractmethod
    def delete_match_api_rule(self, handle_id, table_id):
        """Delete a rule from the table.

        Args:
            handle_id(int):  handle for match.[MANDATORY]
            table_id(int):  the source table id where match to be set.[MANDATORY]

        """
        pass

    @abstractmethod
    def delete_match_api_tcam_subtable(self, source_id, table_id=0, table_name=None):
        """Destroy a sub-table of tcam.

        Args:
            source_id(int):  the source id in the tcam table.[MANDATORY]
            table_id(int):  a given table id.[MANDATORY if table_name not specified]
            table_name(str):  a given table name.[MANDATORY if table_id not specified]

        """
        pass

# OVS configuration
    @abstractmethod
    def create_ovs_bridge(self, bridge_name):
        """Create OvsBridges record.

        Args:
            bridge_name(str):  OVS bridge name

        Returns:
            None

        Examples::

            env.switch[1].ui.create_ovs_bridge('spp0')

        """
        pass

    @abstractmethod
    def get_table_ovs_bridges(self):
        """Get OvsBridges table.

        Returns:
            list[dict]:  table (list of dictionaries))

        Examples::

            env.switch[1].ui.get_table_ovs_bridges()

        """
        pass

    @abstractmethod
    def delete_ovs_bridge(self):
        """Delete OVS Bridge.

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_ovs_bridge()

        """
        pass

    @abstractmethod
    def create_ovs_port(self, port, bridge_name):
        """Create OvsPorts record.

        Args:
            port(int):  port Id
            bridge_name(str):  OVS bridge name

        Returns:
            None

        Examples::

            env.switch[1].ui.create_ovs_port(1, 'spp0')

        """
        pass

    @abstractmethod
    def get_table_ovs_ports(self):
        """Get OvsPorts table.

        Returns:
            list[dict]:  table (list of dictionaries))

        Examples::

            env.switch[1].ui.get_table_ovs_ports()

        """
        pass

    @abstractmethod
    def get_table_ovs_rules(self):
        """Get OvsFlowRules table.

        Returns:
            list[dict]: table (list of dictionaries))

        Examples::

            env.switch[1].ui.get_table_ovs_rules()

        """
        pass

    @abstractmethod
    def create_ovs_bridge_controller(self, bridge_name, controller):
        """Create OvsControllers record.

        Args:
            bridge_name(str):  OVS bridge name
            controller(str):  controller address

        Returns:
            None

        Examples::

            env.switch[1].ui.create_ovs_bridge_controller("spp0", "tcp:127.0.0.1:6633")

        """
        pass

    @abstractmethod
    def get_table_ovs_controllers(self):
        """Get OvsControllers table.

        Returns:
            list[dict]:  table (list of dictionaries))

        Examples::

            env.switch[1].ui.get_table_ovs_controllers()

        """
        pass

    @abstractmethod
    def create_ovs_flow_rules(self, bridge_id, table_id, flow_id, priority, enabled):
        """Create OvsFlowRules table.

        Args:
            bridge_id(int):  OVS bridge ID
            table_id(int):  Table ID
            flow_id(int):  Flow ID
            priority(int):  Rule priority
            enabled(str):  Rule status

        Returns:
            None

        Examples::

            env.switch[1].ui.create_ovs_flow_rules(0, 0, 1, 2000, "Enabled")

        """
        pass

    @abstractmethod
    def delete_ovs_flow_rules(self, bridge_id, table_id, flow_id, priority):
        """Delete row from OvsFlowRules table.

        Args:
            bridge_id(int):  OVS bridge ID
            table_id(int):  Table ID
            flow_id(int):  Flow ID
            priority(int):  Rule priority

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_ovs_flow_rules(bridgeId, tableId, flowId, priority)

        """
        pass

    @abstractmethod
    def configure_ovs_resources(self, **kwargs):
        """Configure OvsResources table.

        Args:
            **kwargs(dict): parameters to be configured:
                            "controllerRateLimit";
                            "vlansLimit";
                            "untaggedVlan";
                            "rulesLimit".

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_ovs_resources(rulesLimit=2000)

        """
        pass

    @abstractmethod
    def get_table_ovs_flow_actions(self):
        """Get OvsFlowActions table.

        Returns:
            list[dict]:  table (list of dictionaries))

        Examples::

            env.switch[1].ui.get_table_ovs_flow_actions()

        """
        pass

    @abstractmethod
    def create_ovs_flow_actions(self, bridge_id, table_id, flow_id, action, param, priority=2000):
        """Add row to OvsFlowActions table.

        Args:
            bridge_id(int):  OVS bridge ID
            table_id(int):  Table ID
            flow_id(int):  Flow ID
            priority(int):  Rule priority
            action(str):  Action name
            param(str):  Action parameter

        Returns:
            None

        Examples::

            env.switch[1].ui.create_ovs_flow_actions(0, 0, 1, 'Output', '25')

        """
        pass

    @abstractmethod
    def delete_ovs_flow_actions(self, bridge_id, table_id, flow_id, action, priority=2000):
        """Delete row from OvsFlowActions table.

        Args:
            bridge_id(int):  OVS bridge ID
            table_id(int):  Table ID
            flow_id(int):  Flow ID
            priority(int):  Rule priority
            action(str):  Action name

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_ovs_flow_actions(0, 0, 1, 'Output')

        """
        pass

    @abstractmethod
    def get_table_ovs_flow_qualifiers(self):
        """Get OvsFlowQualifiers table.

        Returns:
            list[dict]:  table (list of dictionaries))

        Examples::

            env.switch[1].ui.get_table_ovs_flow_qualifiers()

        """
        pass

    @abstractmethod
    def create_ovs_flow_qualifiers(self, bridge_id, table_id, flow_id, field, data, priority=2000):
        """Add row to OvsFlowQualifiers table.

        Args:
            bridge_id(int):  OVS bridge ID
            table_id(int):  Table ID
            flow_id(int):  Flow ID
            priority(int):  Rule priority
            field(str):  Expression name
            data(str):  Expression data

        Returns:
            None

        Examples::

            env.switch[1].ui.create_ovs_flow_qualifiers(0, 0, i, 'EthSrc', '00:00:00:00:00:01')

        """
        pass

    @abstractmethod
    def delete_ovs_flow_qualifiers(self, bridge_id, table_id, flow_id, field, priority=2000):
        """Delete row from OvsFlowQualifiers table.

        Args:
            bridge_id(int):  OVS bridge ID
            table_id(int):  Table ID
            flow_id(int):  Flow ID
            priority(int):  Rule priority
            field(str):  Expression name

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_ovs_flow_qualifiers(bridgeId, tableId, flowId, field)

        """
        pass

# LLDP configuration

    @abstractmethod
    def configure_global_lldp_parameters(self, **kwargs):
        """Configure global LLDP parameters.

        Args:
            **kwargs(dict):  parameters to be modified:
                             'messageFastTx';
                             'messageTxHoldMultiplier';
                             'messageTxInterval';
                             'reinitDelay';
                             'txCreditMax';
                             'txFastInit';
                             'locChassisIdSubtype'.

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_global_lldp_parameters(messageTxInterval=5)

        """
        pass

    @abstractmethod
    def configure_lldp_ports(self, ports, **kwargs):
        """Configure LldpPorts records.

        Args:
            ports(list[int]):  list of ports
            **kwargs(dict):  parameters to be modified:
                             'adminStatus';
                             'tlvManAddrTxEnable';
                             'tlvPortDescTxEnable';
                             'tlvSysCapTxEnable';
                             'tlvSysDescTxEnable';
                             'tlvSysNameTxEnable'.

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_lldp_ports([1, 2], adminStatus='Disabled')

        """
        pass

    @abstractmethod
    def get_table_lldp(self, param=None):
        """Get Lldp table.

        Args:
            param(str):  parameter name (optional)

        Returns:
            list[dict]|int|str: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_lldp()

        """
        pass

    @abstractmethod
    def get_table_lldp_ports(self, port=None, param=None):
        """Get LldpPorts table.

        Args:
            port(int):  port Id (optional)
            param(str):  parameter name (optional)

        Returns:
            list[dict]|int|str:  table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_lldp_ports(1)

        """
        pass

    @abstractmethod
    def get_table_lldp_ports_stats(self, port=None, param=None):
        """Get LldpPorts table statistics.

        Args:
            port(int):  port Id (optional)
            param(str):  parameter name (optional)

        Returns:
            list[dict]|int|str: table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_lldp_ports_stats(1)

        """
        pass

    @abstractmethod
    def get_table_lldp_remotes(self, port=None):
        """Get LldpRemotes table.

        Args:
            port(int):  port Id (optional)

        Returns:
            list[dict]: table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_lldp_remotes(1)

        """
        pass

    @abstractmethod
    def get_table_remotes_mgmt_addresses(self, port=None):
        """Get LldpRemotesMgmtAddresses table.

        Args:
            port(int):  port Id (optional)

        Returns:
            list[dict]: table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_remotes_mgmt_addresses(1)

        """
        pass

    @abstractmethod
    def disable_lldp_on_device_ports(self, ports=None):
        """Disable Lldp on device ports (if port=None Lldp should be disabled on all ports).

        Args:
            ports(list[int]):  list of ports

        Returns:
            None

        Examples::

            env.switch[1].ui.disable_lldp_on_device_ports()

        """
        pass

# DCBX configuration

    @abstractmethod
    def set_dcb_admin_mode(self, ports, mode='Enabled'):
        """Enable/Disable DCB on ports.

        Args:
            ports(list[int]):  list of ports
            mode(str):  "Enabled" or 'Disabled'

        Returns:
            None

        Examples::

            env.switch[1].ui.set_dcb_admin_mode([1, 2], "Enabled")

        """
        pass

    @abstractmethod
    def enable_dcbx_tlv_transmission(self, ports, dcbx_tlvs="all", mode="Enabled"):
        """Enable/Disable the transmission of all Type-Length-Value messages.

        Args:
            ports(list[int]):  list of ports
            dcbx_tlvs(str):  TLV message types
            mode(str):  "Enabled" or 'Disabled'

        Returns:
            None

        Examples::

            env.switch[1].ui.enable_dcbx_tlv_transmission([1, 2], dcbx_tlvs="all", mode="Enabled")

        """
        pass

    @abstractmethod
    def get_table_dcbx_ports(self, port=None, param=None):
        """Get DcbxPorts table.

        Args:
            port(int):  port Id (optional)
            param(str):  parameter name (optional)

        Returns:
            list[dict]:  table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_dcbx_ports()

        """
        pass

    @abstractmethod
    def get_table_dcbx_app_remote(self, port=None):
        """Get DcbxAppRemotes table.

        Args:
            port(int):  port Id (optional)

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_dcbx_app_remote()

        """
        pass

    @abstractmethod
    def get_table_dcbx_app_ports(self, table_type="Admin", port=None):
        """Get DcbxAppPorts* table.

        Args:
            table_type(str):  "Admin", "Local"
            port(int):  port Id (optional)

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_dcbx_app_ports("Admin", 1)

        """
        pass

    @abstractmethod
    def get_table_dcbx_app_maps(self, table_type="Admin", port=None):
        """Get DcbxAppMaps* table

        Args:
            table_type(str):  "Admin", "Local" or "Remote"
            port(int):  port Id (optional)

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_dcbx_app_maps("Admin", 1)

        """
        pass

    @abstractmethod
    def configure_application_priority_rules(self, ports, app_prio_rules, delete_params=False, update_params=False):
        """Configure Application Priority rules.

        Args:
            ports(list[int]):  list of ports
            app_prio_rules(list[dict]):  list of rules dictionaries
            delete_params(bool): if delete specified params or not
            update_params(bool): if update specified params or not

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_application_priority_rules([1, 2], [{"selector": 1, "protocol": 2, "priority":1}, ])

        """
        pass

    @abstractmethod
    def configure_dcbx_ets(self, ports, **kwargs):
        """Configure DCBx ETS Conf/Reco parameter for ports list.

        Args:
            ports(list[int]):  list of ports
            **kwargs(dict):  parameters to be modified:
                             "willing";
                             "cbs";
                             "maxTCs";
                             "confBandwidth";
                             "confPriorityAssignment";
                             "confAlgorithm";
                             "recoBandwidth";
                             "recoPriorityAssignment";
                             "recoAlgorithm".

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_dcbx_ets([1, 2], confBandwidth=100)

        """
        pass

    @abstractmethod
    def configure_dcbx_cn(self, ports, **kwargs):
        """Configure DCBx CN parameter for the ports list.

        Args:
            ports(list[int]):  list of ports
            **kwargs(dict):  parameters to be modified:
                             "cnpvSupported";
                             "cnpvReady".

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_dcbx_cn([1, 2], cnpvSupported='Enabled')

        """
        pass

    @abstractmethod
    def configure_dcbx_pfc(self, ports, **kwargs):
        """Configure DCBx PFC parameter for the ports list.

        Args:
            ports(list[int]):  list of ports
            **kwargs(dict):  parameters to be modified:
                             "mbc";
                             "enabled";
                             "willing".

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_dcbx_pfc([1, 2])

        """
        pass

    @abstractmethod
    def configure_dcbx_app(self, ports, **kwargs):
        """Configure DCBx APP parameter for the ports list.

        Args:
            ports(list[int]):  list of ports
            **kwargs(dict):  parameters to be modified:
                             "willing".

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_dcbx_app([1, 2])

        """
        pass

    @abstractmethod
    def get_table_dcbx_remotes(self, port=None, param=None):
        """Get DcbxRemotes* table.

        Args:
            port(int):  port Id (optional)
            param(str):  parameter name (optional)

        Returns:
            list[dict]|int|str: table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_dcbx_remotes(1)

        """
        pass

    @abstractmethod
    def get_table_dcbx_pfc(self, table_type="Local", port=None):
        """Get DcbxRemotes* table.

        Args:
            port(int):  port Id (optional)
            table_type(str):  Table types "Admin"| "Local"| "Remote"

        Returns:
            list[dict]|int|str:  table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_dcbx_pfc()

        """
        pass

    @abstractmethod
    def get_table_dcbx_ets_ports(self, table_type='Admin', port=None):
        """Get DcbxEtsPorts* table.

        Args:
            port(int):  port Id (optional)
            table_type(str):  Table types "Admin"| "Local"

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_dcbx_ets_ports()

        """
        pass

# UFD configuration

    @abstractmethod
    def get_table_ufd_config(self):
        """Get UFDConfig table.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_ufd_config()

        """
        pass

    @abstractmethod
    def configure_ufd(self, enable='Enabled', hold_on_time=None):
        """Modify UFDConfig table.

        Args:
            enable(str):  Enable or disable UFD
            hold_on_time(int):  hold on time

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_ufd(enable='Enabled')

        """
        pass

    @abstractmethod
    def create_ufd_group(self, group_id, threshold=None, enable='Enabled'):
        """Create UFDGroups record.

        Args:
            group_id(int):  UFD group ID
            threshold(int):  group threshold
            enable(str):  Enable or disable UFD group

        Returns:
            None

        Examples::

            env.switch[1].ui.create_ufd_group(1)

        """
        pass

    @abstractmethod
    def modify_ufd_group(self, group_id, threshold=None, enable=None):
        """Modify UFDGroups record.

        Args:
            group_id(int):  UFD group ID
            threshold(int):  group threshold
            enable(str):  Enable or disable UFD group

        Returns:
            None

        Examples::

            env.switch[1].ui.modify_ufd_group(1, enable='Disabled')

        """
        pass

    @abstractmethod
    def delete_ufd_group(self, group_id):
        """Delete UFDGroups record.

        Args:
            group_id(int):  UFD group ID

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_ufd_group(2)

        """
        pass

    @abstractmethod
    def get_table_ufd_groups(self):
        """Get UFDGroups table.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_ufd_groups()

        """
        pass

    @abstractmethod
    def create_ufd_ports(self, ports, port_type, group_id):
        """Create UFDPorts2Groups record.

        Args:
            ports(list[int]):  list of ports
            port_type(str):  type of port
            group_id(int):  UFD group Id

        Returns:
            None

        Examples::

            env.switch[1].ui.create_ufd_ports([1, ], 'LtM' 2)

        """
        pass

    @abstractmethod
    def delete_ufd_ports(self, ports, port_type, group_id):
        """Delete UFDPorts2Groups record.

        Args:
            ports(list[int]):  list of ports
            port_type(str):  type of port
            group_id(int):  UFD group Id

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_ufd_ports([1, ], 'LtM' 2)

        """
        pass

    @abstractmethod
    def get_table_ufd_ports(self):
        """Get UFDPorts2Groups table.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_ufd_ports()

        """
        pass

# QinQ configuration

    @abstractmethod
    def configure_qinq_ports(self, ports, **kwargs):
        """Configure QinQ Ports.

        Args:
            ports(list[int]):  list of ports
            **kwargs(dict):  parameters to be modified:
                             "mode";
                             "tpid".

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_qinq_ports([1, ], tpid=2)

        """
        pass

    @abstractmethod
    def configure_qinq_vlan_stacking(self, ports, provider_vlan_id, provider_vlan_priority):
        """Configure QinQVlanStacking.

        Args:
            ports(list[int]):  list of ports
            provider_vlan_id(int):  provider vlan Id
            provider_vlan_priority(int):  provider vlan priority

        Returns:
            None

        Examples:

            env.switch[1].ui.configure_qinq_vlan_stacking([1, ], 2, 7)

        """
        pass

    @abstractmethod
    def get_table_qinq_vlan_stacking(self):
        """Get QinQVlanStacking table.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_qinq_vlan_stacking()

        """
        pass

    @abstractmethod
    def configure_qinq_vlan_mapping(self, ports, customer_vlan_id, customer_vlan_priority, provider_vlan_id, provider_vlan_priority):
        """Configure QinQCustomerVlanMapping and QinQProviderVlanMapping.

        Args:
            ports(list[int]):  list of ports
            customer_vlan_id(int):  customer vlan Id
            customer_vlan_priority(int):  customer vlan priority
            provider_vlan_id(int):  provider vlan Id
            provider_vlan_priority(int):  provider vlan priority

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_qinq_vlan_mapping([1, ], 2, 7, 5, 6)

        """
        pass

    @abstractmethod
    def get_table_qinq_customer_vlan_mapping(self):
        """Get QinQCustomerVlanMapping table.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_qinq_customer_vlan_mapping()

        """
        pass

    @abstractmethod
    def get_table_qinq_provider_vlan_mapping(self):
        """Get QinQProviderVlanMapping table.

        Returns:
            list[dict]: table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_qinq_provider_vlan_mapping()

        """
        pass

    @abstractmethod
    def get_table_qinq_ports(self, port=None, param=None):
        """Get QinQPorts table.

        Args:
            port(int):  port Id (optional)
            param(str):  parameter name (optional)

        Returns:
            list[dict]|int|str:  table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_qinq_ports()

        """
        pass

# Errdisable configuration

    @abstractmethod
    def get_table_errdisable_errors_config(self, app_name=None, app_error=None):
        """Get ErrdisableErrorsConfig table.

        Args:
            app_name(str):  application name
            app_error(str):  application error

        Returns:
            list[dict]|str:  table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_table_errdisable_errors_config()

        """
        pass

    @abstractmethod
    def get_table_errdisable_config(self):
        """Get ErrdisableConfig table.

        Returns:
            list[dict]:  table (list of dictionaries)

        Examples::

            env.switch[1].ui.get_table_errdisable_config()

        """
        pass

    @abstractmethod
    def modify_errdisable_errors_config(self, detect=None, recovery=None, app_name=None, app_error=None):
        """Configure ErrdisableErrorsConfig table.

        Args:
            detect(str):  detect status
            recovery(str):  recovery status
            app_name(str):  application name
            app_error(str):  application error

        Returns:
            None

        Examples::

            env.switch[1].ui.modify_errdisable_errors_config(detect="Enabled", app_name='L2UfdControlApp', app_error='ufd')

        """
        pass

    @abstractmethod
    def modify_errdisable_config(self, interval=None):
        """Configure ErrdisableConfig table.

        Args:
            interval(int):  recovery interval

        Returns:
            None

        Examples::

            env.switch[1].ui.modify_errdisable_config(10)

        """
        pass

    @abstractmethod
    def get_errdisable_ports(self, port=None, app_name=None, app_error=None, param=None):
        """Get ErrdisablePorts table.

        Args:
            port(int):  port Id (optional)
            app_name(str):  application name (optional)
            app_error(str):  application error (optional)
            param(str):  parameter name (optional)

        Returns:
            list[dict]|int|str: table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_errdisable_ports()

        """
        pass

# Mirroring configuration

    @abstractmethod
    def create_mirror_session(self, port, target, mode):
        """Configure PortsMirroring table.

        Args:
            port(int):  source port Id
            target(int):  target port Id
            mode(str):  mirroring mode

        Returns:
            None

        Examples::

            env.switch[1].ui.create_mirror_session(1, 2, 'Redirect')

        """
        pass

    @abstractmethod
    def get_mirroring_sessions(self):
        """Get PortsMirroring table.

        Returns:
            list[dict]|int|str:  table (list of dictionaries) or value

        Examples::

            env.switch[1].ui.get_mirroring_sessions()

        """
        pass

    @abstractmethod
    def delete_mirroring_session(self, port, target, mode):
        """Delete mirroring session from the PortsMirroring table.

        Args:
            port(int):  source port Id
            target(int):  target port Id
            mode(str):  mirroring mode

        Returns:
            None

        Examples::

            env.switch[1].ui.delete_mirroring_session(1, 2, 'Redirect')

        """
        pass

# DHCP Relay configuration

    @abstractmethod
    def create_dhcp_relay(self, iface_name='global', server_ip=None, fwd_iface_name=None):
        """Configure DhcpRelayAdmin or DhcpRelayV6Admin table.

        Args:
            iface_name(str):  VLAN inteface name
            server_ip(str):  DHCP Server IP address
            fwd_iface_name(str):  VLAN forward interface name (for IPv6 config only)

        Returns:
            None

        Examples::

            env.switch[1].ui.create_dhcp_relay(iface_name='global', server_ip='10.10.0.2')

        """
        pass

    @abstractmethod
    def get_table_dhcp_relay(self, dhcp_relay_ipv6=False):
        """Return DhcpRelayAdmin or DhcpRelayV6Admin table

        Args:
            dhcp_relay_ipv6(bool):  is IPv6 config defined

        Returns:
            None

        Examples::

            env.switch[1].ui.get_table_dhcp_relay(dhcp_relay_ipv6=False)

        """
        pass

# VxLAN configuration

    @abstractmethod
    def configure_tunneling_global(self, **kwargs):
        """Configure TunnelingGlobalAdmin table.

        Args:
            **kwargs(dict):  parameters to be modified:
                             "vnTag";
                             "vxlanInnerVlanProcessing";
                             "mode",
                             "vxlanDestUDPPort".

        Returns:
            None

        Examples::

            env.switch[1].ui.configure_tunneling_global()

        """
        pass

    @abstractmethod
    def create_tunnels(self, tunnel_id=None, destination_ip=None, vrf=0, encap_type=None):
        """Configure TunnelsAdmin table.

        Args:
            tunnel_id(int):  Tunnel ID
            destination_ip(str):  Destination IP address
            vrf(int):  Tunnel VRF
            encap_type(str):  Tunnel encapsulation type

        Returns:
            None

        Examples::

            env.switch[1].ui.create_tunnels(tunnel_id=records_count, destination_ip=ip_list, encap_type='VXLAN')

        """
        pass

    @abstractmethod
    def get_table_tunnels_admin(self):
        """Return TunnelsAdmin table.

        Returns:
            list[dict]:  table

        Examples::

            env.switch[1].ui.get_table_tunnels_admin()

        """
        pass
