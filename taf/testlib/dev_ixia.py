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

"""``dev_ixia.py``

`Ixia traffic generators specific functionality`

"""

from . import loggers
from . import entry_template

from .Ixia.IxiaHAL import IxiaHALMixin
from .Ixia.IxiaHLT import IxiaHLTMixin
from .Ixia.IxLoadHL import IxLoadHL
from .packet_processor import PacketProcessor
from .tg_helpers import TGHelperMixin


class Ixia(IxiaHLTMixin, IxiaHALMixin, TGHelperMixin, PacketProcessor, entry_template.GenericEntry):
    """IXIA interaction base class.

    """

    class_logger = loggers.ClassLogger()

    def __init__(self, config, opts):
        """Initializes connection to IXIA.

        Args:
            config(dict):  Configuration information.
            opts(OptionParser):  py.test config.option object which contains all py.test cli options.

        """
        self.__opts = opts
        self.__config = config

        # Indicates if TG object supports high level protocol emulation (can emulate dialogs).
        self.is_protocol_emulation_present = "tcl_server" in config

        if self.is_protocol_emulation_present:
            IxiaHLTMixin.__init__(self, config, opts)
        IxiaHALMixin.__init__(self, config, opts)

        self.ports, self.port_list = self._get_speed_ports()

        self.ifaces = "{"
        for iface in self.ports:
            self.ifaces = self.ifaces + self._convert_iface(iface) + " "
        self.ifaces = self.ifaces + "}"

        # Configure port rate dictionary:
        self.rate = {k: 1 for k in self.ports}
        if "port_rate" in config:
            for _key in config["port_rate"]:
                self.rate[self.ports[int(_key) - 1]] = config["port_rate"][_key]

    def _get_speed_ports(self):
        """Get ports with speed from config.

        Returns:
            tuple(list[tuple], list[tuple, int]):  Tuple with list of ports used in real config and list of port/speed values

        Notes:
            This function check if port has speed in config file.

        """
        ports = []
        ports_list = []
        if 'ports' in self.__config:
            ports = [tuple(x) for x in self.__config["ports"]]
        if "port_list" in self.__config:
            ports = [tuple(x[0]) for x in self.__config["port_list"]]
            ports_list = [[tuple(x[0]), x[1]] for x in self.__config["port_list"]]

        return ports, ports_list

    def connect(self):
        """Logs in to IXIA and takes ports ownership.

        Returns:
            None

        """
        if self.is_protocol_emulation_present:
            IxiaHLTMixin.connect(self)
        IxiaHALMixin.connect(self)

    def disconnect(self, mode='fast'):
        """Logs out from IXIA and clears ports ownership.

        Returns:
            None

        """
        IxiaHALMixin.disconnect(self, mode)
        if self.is_protocol_emulation_present:
            IxiaHLTMixin.disconnect(self, mode)

    def check(self):
        """Checking connection to IXIA.

        Returns:
            None

        """
        if self.is_protocol_emulation_present:
            IxiaHLTMixin.check(self)
        IxiaHALMixin.check(self)

    def create(self):
        """Obligatory class for entry_type = tg.

        """
        if self.is_protocol_emulation_present:
            IxiaHLTMixin.create(self)
        IxiaHALMixin.create(self)

    def destroy(self):
        """Obligatory class for entry_type = tg.

        """
        self.class_logger.info("Destroying Ixia object...")
        IxiaHALMixin.cleanup(self, mode="fast")
        self.class_logger.info("IxHAL Cleanup finished.")
        if not self.__opts.leave_on and not self.__opts.get_only:
            self.class_logger.info("Disconnecting IxHAL...")
            IxiaHALMixin.disconnect(self)
            if self.is_protocol_emulation_present:
                self.class_logger.info("Disconnecting IxNetwork...")
                IxiaHLTMixin.disconnect(self, mode="fast")

    def cleanup(self, mode="complete"):
        """This method should do Ixia ports cleanup (remove streams etc.).

        Args:
            mode(str): "fast" or "complete". If mode == "fast", method does not clear streams on the port (string)

        """
        # TODO: Add stop_sniff etc
        # TODO: Handle errors more gracefully
        if self.is_protocol_emulation_present:
            IxiaHLTMixin.cleanup(self, mode)
        IxiaHALMixin.cleanup(self, mode)

    def sanitize(self):
        """Clear ownership before exit.

        """
        if self.is_protocol_emulation_present:
            IxiaHLTMixin.sanitize(self)
        IxiaHALMixin.sanitize(self)

    def get_os_mtu(self, iface=None):
        """Get MTU value in host OS.

        Args:
            iface(str):  Interface for getting MTU in host OS

        Returns:
            int: Original MTU value

        Example::

            env.tg[1].get_os_mtu(iface=ports[('tg1', 'sw1')][1])

        """
        return 14000

    def set_os_mtu(self, iface=None, mtu=None):
        """Set MTU value in host OS.

        Args:
            iface(str):  Interface for changing MTU in host OS
            mtu(int):  New MTU value

        Returns:
            int:  Original MTU value

        Examples ::

            env.tg[1].set_os_mtu(iface=ports[('tg1', 'sw1')][1], mtu=1650)

        """
        return self.get_os_mtu(iface)


class IxiaLOAD(IxLoadHL, PacketProcessor, entry_template.GenericEntry):
    """IXIA interaction class based on IxLoadCsv.

    """

    class_logger = loggers.ClassLogger()


ENTRY_TYPE = "tg"
INSTANCES = {"ixiahl": Ixia,
             "ixload": IxiaLOAD,
             }
NAME = "tg"
