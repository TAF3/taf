# Copyright (c) 2015 - 2017, Intel Corporation.
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

"""``dev_linux_host_vm.py``

`OpenStack VM host device related functionality`

"""
import copy
import functools

from . import clissh

from .dev_linux_host import NICHelper, GenericLinuxHost


class GenericLinuxVirtualHost(GenericLinuxHost):
    """
    """
    def _pred_mgmt_in_nic_ips(self, nic):
        return self.nated_mgmt in nic['ip_addr']

    @functools.wraps(_pred_mgmt_in_nic_ips)
    def NIC_IF_MGMT(self):
        return NICHelper.pwrap_bool_true(self._pred_mgmt_in_nic_ips)

    @functools.wraps(_pred_mgmt_in_nic_ips)
    def NIC_IF_NO_MGMT(self):
        return NICHelper.pwrap_bool_false(self._pred_mgmt_in_nic_ips)

    @classmethod
    def class_init(cls):
        super_class = super(GenericLinuxVirtualHost, cls)
        cls.__NIC_FILTERS_MAP__ = copy.deepcopy(super_class.__NIC_FILTERS_MAP__)
        cls.__NIC_FILTERS_MAP__['no_mgmt'] = cls.NIC_IF_NO_MGMT

    def __init__(self, config, opts):
        super(GenericLinuxVirtualHost, self).__init__(config, opts)
        self.nated_mgmt = config.get('nated_mgmt', None)
        self.tempest_ui = None
        self.os_networks = []

    def _set_mgmt_interface(self, mgmt_ip):
        # OpenStack instances management IP is NATed, we need to provide the
        # local IP (set in tempest_ui.create_server) to properly detect the management interface
        if self.nated_mgmt is None:
            raise Exception('nated_mgmt property not set, assign floating IP first.')
        super(GenericLinuxVirtualHost, self)._set_mgmt_interface(self.nated_mgmt)

    def _set_ssh(self, ipaddr):
        """Set ssh connection.

        Required in virtual environment. When we create VMs host object we do not know the IP yet.

        Args:
            ipaddr(list):  IPv4 address to be assigned to the specific interface

        """
        self.ipaddr = ipaddr
        ssh_eligible = self.ssh_pass or self.ssh_pkey or self.ssh_pkey_file
        if self.ipaddr and self.ssh_user and ssh_eligible:
            self.ssh = clissh.CLISSH(self.ipaddr, self.ssh_port, self.ssh_user, self.ssh_pass,
                                     pkey=self.ssh_pkey, key_filename=self.ssh_pkey_file)


GenericLinuxVirtualHost.class_init()


ENTRY_TYPE = "openstack"
INSTANCES = {
    "vm": GenericLinuxVirtualHost,
}
NAME = "ostack"
LINK_NAME = "ost"
