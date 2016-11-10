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

"""``dev_iperftg.py``

`Remote Iperf traffic generators specific functionality`

"""
import time
import pytest

from contextlib import suppress, contextmanager

from . import loggers, tg_template

from .dev_linux_host import GenericLinuxHost
from .dev_linux_host_vm import GenericLinuxVirtualHost
from .custom_exceptions import TGException

from .linux.iperf import iperf, iperf_cmd


HOST_MAP = {
    "riperf": GenericLinuxHost,
    "riperf_vm": GenericLinuxVirtualHost,
}


__0__ = object()


class RemoteIperfTG(tg_template.GenericTG):
    """Class for launching Iperf on remote server.

    Configuration examples:

    Remote Iperf Example::


        {
         "name": "RemoteIperf"
         "entry_type": "tg",
         "instance_type": "riperf",
         "id": "TG1",
         "ports": ["eth1", "eth2"],
         "ipaddr": "1.1.1.1",
         "ssh_user": "user",
         "ssh_pass": "PassworD",
         "host_type": "lhost",
         "results_folder": "/tmp/iperf_tg"
        }

    Where:
        - \b entry_type and \b instance_type are mandatory values and cannot be changed
        - \n\b id - int or str uniq device ID (mandatory)
        - \n\b name - User defined device name (optional)
        - \n\b ports or \b port_list - short or long ports configuration (pick one exclusively)
        - \n\b ipaddr - remote host IP address (mandatory)
        - \n\b ssh_user - remote host login user (mandatory)
        - \n\b ssh_pass - remote host login password (mandatory)
        - \n\b results_folder - folder to store Iperf results

    Notes:
        You can safely add additional custom attributes.

    """

    class_logger = loggers.ClassLogger()
    _lhost = None
    default_duration = 1000000
    namespace_prefix = 'ip netns exec {} '

    def __init__(self, config, opts, reuse_host=None):
        """Initialize RemoteIperfTG class.

        Args:
            config(dict):  Configuration information.
            opts(OptionParser):  py.test config.option object containing all py.test cli options.

        """
        super(RemoteIperfTG, self).__init__(config, opts)
        self.config = config
        self.opts = opts
        self.type = config['instance_type']
        self.id = config['id']
        self.name = config.get('name', "UndefinedName_{0}".format(self.id))
        self.ports = []
        self.port_list = []
        if "ports" in config:
            self.ports = config['ports']
        if "port_list" in config:
            self.port_list = config['port_list']
        if not self.ports and self.port_list:
            self.ports = [p[0] for p in self.port_list]

        self.init_lhost = reuse_host is None
        self._lhost = reuse_host

        # Indicates if TG object supports high level protocol emulation (can emulate dialogs).
        self.is_protocol_emulation_present = False

        # Store information about used ports
        self.used_ifaces = set()

        # Stream IDs
        self.streams = {}
        self.stream_results = []

        # Iperf server interfaces
        self.sniff_ports = {}
        self.sniff_results = []
        # Store information about configured network namespaces
        self.namespaces = {}
        # Store information about configured iface IP addresses
        self.iface_ip = []

    def start(self, wait_on=True):
        """Start iperf TG.

        Args:
            wait_on(bool):  Wait for device is loaded

        """
        # Get host instance from related devices
        if self.init_lhost and self.related_obj:
            self._lhost = next(iter(dev for dev in self.related_obj.values()
                                    if hasattr(dev, 'ui')),
                               None)

        # Set remote host platform
        if self.init_lhost:
            self._lhost = HOST_MAP[self.type](self.config, self.opts)
            self._lhost.start()

        self.status = True  # pylint: disable=attribute-defined-outside-init

    def stop(self):
        """Shutdown Iperf TG device.

        """
        # Cleanup platform first.
        self.cleanup()

        if self.init_lhost:
            self._lhost.stop()

        self.status = False  # pylint: disable=attribute-defined-outside-init

    def create(self):
        """Start Iperf TG device or get running one.

        """
        return self.start()

    def destroy(self):
        """Stop or release Iperf TG device.

        """
        if not self.status:
            self.class_logger.info("Skip iperf tg id:{0}({1}) destroying because "
                                   "it's has already Off status.".format(self.id, self.name))
            return
        self.stop()

        self.sanitize()

    def cleanup(self, *args, **kwargs):
        """Cleanup host.

        """
        self.clear_streams()
        self.stop_sniff()
        self.used_ifaces.clear()
        self.streams.clear()
        self.sniff_ports.clear()
        self.delete_ipaddr()
        self.delete_namespaces()

        if self.init_lhost:
            self._lhost.cleanup()
            self._lhost.ui.iperf.cleanup()

    def check(self):
        """Check host.

        """
        self._lhost.check()

    def sanitize(self):
        """Perform any necessary operations to leave environment in normal state.

        """
        self.clear_streams()
        self.stop_sniff()
        if self.init_lhost:
            self._lhost.ui.disconnect()

    def clear_streams(self):
        """Stop and clear all traffic streams.

        """
        self.stop_streams()
        self.streams.clear()

    def set_stream(self, iface=None, dst_ip=__0__, src_ip=__0__, l4_proto=__0__, l4_port=__0__,
                   l4_bandwidth=__0__, duration=__0__, interval=__0__, units=__0__,
                   options=None, command=None):
        """
        @brief  Set traffic stream with specified parameters on specified TG port.
        @note  Method generates option for Iperf launching in client mode

        @param iface:  Interface to use for packet sending.
        @type  iface:  str
        @param dst_ip:  Iperf server IP address('client' iperf client option).
        @type  dst_ip:  str
        @param src_ip:  Local TG interface IP address('bind' iperf general option).
        @type  src_ip:  str
        @param l4_proto:  Iperf L4 proto. tcp|udp('udp' iperf general option).
        @type  l4_proto:  str
        @param l4_port:  Iperf L4 port('port' iperf general option).
        @type  l4_port:  int
        @param l4_bandwidth:  Iperf UDP bandwidth('bandwidth' iperf client option).
        @type  l4_bandwidth:  str
        @param duration:  Traffic transmit duration('time' iperf client option).
        @type  duration:  int
        @param interval:  Iperf statistics interval('interval' iperf general option).
        @type  interval:  int
        @param units:  Iperf statistics reports foramat('format' iperf general option).
        @type  units:  str

        @param options: intermediate iperf options list
        @type  options: list of str
        @param command: intermediate iperf command object
        @type  command: iperf_cmd.CmdIperf

        @rtype:  int
        @return:  stream id
        @par Example:
        @code{.py}
        stream_id_1 = tg.set_stream(dst_ip='1.1.1.1', iface=iface)
        stream_id_2 = tg.set_stream(dst_ip='1.1.1.1', iface=iface, l4_proto='udp')
        @endcode
        """
        kwargs = {
            'client': dst_ip,
            'time': duration,
            'bandwidth': l4_bandwidth,

            'interval': iperf_cmd._DEFAULT_INTERVAL if interval is __0__ else interval,
            'format': iperf_cmd._DEFAULT_FORMAT if units is __0__ else units,
            'port': l4_port,
            'bind': src_ip,
            'udp': True if l4_proto == 'udp' else __0__,
        }
        # filter out default arguments first:
        # 1) function defaults:
        kwargs = {k: v for k, v in kwargs.items() if v is not __0__}
        # 2) command defaults: handled by Command by design
        # kwargs = iperf_cmd.CmdIperf.CMD_HELPER.get_set_args(kwargs)

        cmd = iperf_cmd.CmdIperf(kwargs, options, command)
        cmd.check_args()

        stream_id = (max(self.streams.keys()) + 1) if self.streams else 1
        self.streams[stream_id] = {
            'iface': iface,
            'iperf_cmd': cmd,
        }

        # Add src_ip address to specific TG port
        bind = cmd.get('bind')
        if iface and bind:
            self.iface_config(iface, intf_ip_addr=bind)

        self.class_logger.info("Stream ID:%s was set.", stream_id)
        return stream_id

    def send_stream(self, stream_id, get_result=False):
        """Start Iperf client with options from set_stream.

        Args:
            stream_id(int):  ID of the stream to be send
            get_result(bool):  flag that indicates whether to get iperf results or not

        Returns:
            list:  iperf client output

        """
        stream = self.streams.get(stream_id)
        if not stream:
            raise TGException("Stream with ID {} was not configured".format(stream_id))

        prefix = None
        iface = stream['iface']
        # Verify that there is no ports already used by another iperf instances
        if iface:
            if iface in self.used_ifaces:
                raise TGException("There is an another iperf on port {}.".format(iface))
            if iface in self.namespaces:
                stream['prefix'] = prefix = self.namespace_prefix.format(self.namespaces[iface])
            self.used_ifaces.add(iface)

        cmd = stream['iperf_cmd']
        iid = self._lhost.ui.iperf.start(prefix=prefix, command=cmd)
        stream['instance_id'] = iid

        if get_result:
            cmd_time = cmd.get('time', 10)
            time.sleep(int(cmd_time))

            # make sure we stopped correctly
            return self.stop_stream(stream_id, ignore_inactive=True)

    def start_streams(self, stream_list, get_result=False):
        """Start streams from the list.

        Args:
            stream_list(list[int]):  List of stream IDs.
            get_result(bool): get results

        Returns:
            None

        """
        for stream_id in stream_list:
            self.send_stream(stream_id, get_result=get_result)

    def _stop_and_parse_instance(self, iid, stop_kwargs=None, parse_kwargs=None):
        """
        Stops an iperf instance and returns the parsed output.
        """
        inst = self._lhost.ui.iperf.instances.get(iid)
        if not inst:
            return None

        if not stop_kwargs:
            stop_kwargs = {}

        self._lhost.ui.iperf.stop(iid, **stop_kwargs)
        inst_res = self._lhost.ui.iperf.get_results(iid)
        if not inst_res:
            return None

        if not parse_kwargs:
            parse_kwargs = {}
        cmd = inst.get('iperf_cmd', {})
        # output = self._lhost.ui.iperf.parse(inst_res, units=units, threads=threads)
        stats = iperf.IperfStats(command=cmd, data_raw=inst_res, **parse_kwargs)
        return stats.retval

    def stop_stream(self, stream_id, **kwargs):
        """
        @brief  Stop an iperf stream.
        @param stream_id:  Stream ID to stop.
        @type  stream_id:  int
        @rtype:  dict
        @return:  iperf output per stream
        @raises: UICmdException: when check is True and service is already stopped or other error
        """
        stream = self.streams.get(stream_id)
        if not stream:
            return

        # instance could have already been stopped in send_stream
        iid = stream.get('instance_id')
        if not iid:
            return None

        iface = stream.get('iface')
        res = self._stop_and_parse_instance(iid, stop_kwargs=kwargs, parse_kwargs={'iface': iface})
        self.stream_results.append(res)

        if iface:
            self.used_ifaces.remove(iface)

        del self.streams[stream_id]
        return res

    def stop_streams(self, stream_list=None, **kwargs):
        """Stop all streams from the list.

        Args:
            stream_list(list[int]):  Stream IDs to stop.

        Returns:
            dict:  iperf output per stream

        """
        if not stream_list:
            stream_list = list(self.streams.keys())

        results = {}
        for stream_id in stream_list:
            results[stream_id] = self.stop_stream(stream_id, **kwargs)

        return results

    def start_sniff(self, ifaces, src_ip=__0__, l4_proto=__0__, l4_port=__0__, interval=__0__,
                    units=__0__, options=None, command=None):
        """
        @brief  Starts Iperf server on specified interfaces.
        @param ifaces:  List of TG interfaces for capturing.
        @type  ifaces:  list
        @param src_ip:  Local TG interface IP address('bind' iperf general option).
        @type  src_ip:  str
        @param l4_proto:  Iperf L4 proto. tcp|udp('udp' iperf general option).
        @type  l4_proto:  str
        @param l4_port:  Iperf L4 port('port' iperf general option).
        @type  l4_port:  int
        @param interval:  Iperf statistics interval('interval' iperf general option).
        @type  interval:  int
        @param units:  Iperf statistics reports foramat('format' iperf general option).
        @type  units:  str

        @param options: intermediate iperf options list
        @type  options: list of str
        @param command: intermediate iperf command object
        @type  command: iperf_cmd.CmdIperf

        @return:  None

        @par Example:
        @code
        env.tg[1].start_sniff(['eth0', ], src_ip='1.1.1.1')
        @endcode
        """
        if not ifaces:
            return

        kwargs = {
            'server': True,

            'interval': iperf_cmd._DEFAULT_INTERVAL if interval is __0__ else interval,
            'format': iperf_cmd._DEFAULT_FORMAT if units is __0__ else units,
            'port': l4_port,
            'bind': src_ip,
            'udp': True if l4_proto == 'udp' else __0__,
        }
        # filter out default arguments first:
        # 1) function defaults:
        kwargs = {k: v for k, v in kwargs.items() if v is not __0__}
        # 2) command defaults: handled by Command by design
        # kwargs = iperf_cmd.CmdIperf.CMD_HELPER.get_set_args(kwargs)

        cmd = iperf_cmd.CmdIperf(kwargs, options, command)
        cmd.check_args()

        bind = cmd.get('bind')

        for iface in ifaces:
            # Verify that there is no ports already used by another iperf instances
            if iface in self.used_ifaces:
                raise TGException("There is an another iperf on port {}.".format(iface))

            prefix = None
            if iface in self.namespaces:
                prefix = self.namespace_prefix.format(self.namespaces[iface])

            # Add src_ip address to specific TG port
            if bind:
                self.iface_config(iface, intf_ip_addr=bind)

            iid = self._lhost.ui.iperf.start(prefix=prefix, command=cmd)
            self.sniff_ports[iface] = iid
            self.used_ifaces.add(iface)

            self.class_logger.info("Iperf server was started on iface {}.".format(iface))

    def stop_sniff(self, ifaces=None, **kwargs):
        """
        @param check:
        @type check:
        brief  Stops sniffing on specified interfaces and returns captured data.
        @param ifaces:  List of interfaces where capturing has to be stopped.
        @type  ifaces:  list
        @rtype:  dict
        @return:  Dictionary where key = interface name, value = iperf statistics.
        """
        if not ifaces:
            # we destructively iterate over self.sniff_ports, so we have to copy keys
            ifaces = list(self.sniff_ports.keys())

        results = {}
        for iface in ifaces:
            results[iface] = self._stop_sniff(iface, **kwargs)
        return results

    def _stop_sniff(self, iface, **kwargs):
        iid = self.sniff_ports.get(iface)
        if not iid:
            return None

        res = self._stop_and_parse_instance(iid, stop_kwargs=kwargs, parse_kwargs={'iface': iface})
        self.sniff_results.append(res)

        self.used_ifaces.remove(iface)
        del self.sniff_ports[iface]
        return res

    def iface_config(self, iface, *args, **kwargs):
        """
        @param iface: interface name
        @type iface: str
        @brief  High-level interface config utility.
        raise  NotImplementedError:  not implemented
        @note  This method has to support parameters supported by ::ixia::interface_config
               function for compatibility.
               You have to check already implemented parameters for other TG types.
        @par  Example:
        @code
        env.tg[1].iface_config(tgport1, intf_ip_addr="10.1.0.101", netns=True)
        @endcode
        """
        if not set(kwargs).issubset({'intf_ip_addr', 'netns', 'adminMode'}):
            raise NotImplementedError("Method is not implemented for current kwargs.")

        # Create network namespaces for current iface
        with suppress(KeyError):
            del kwargs['netns']
            self.create_namespaces(iface)

        intf_ip_addr = kwargs.get('intf_ip_addr')
        if intf_ip_addr:
            kwargs['ipAddr'] = "{}/24".format(intf_ip_addr)

        iface_ns = self.namespaces.get(iface)
        if iface_ns:
            with self.ns_context(iface_ns):
                self._lhost.ui.modify_ports([iface], **kwargs)

    def create_namespaces(self, iface):
        """Create network namespace for specified interface.

        Args:
            iface(str):  interface name

        """
        if iface not in self.namespaces:
            name = "netns_{}".format(iface)
            self._lhost.ui.create_namespace(name)

            self._lhost.ui.modify_ports([iface], netns=name)
            self.namespaces[iface] = name

            self.iface_config(iface, adminMode='Up')

    def delete_namespaces(self, ifaces=None):
        """Delete network namespaces for specified interfaces.

        Args:
            ifaces(list[str]):  interface names

        """
        if not ifaces:
            ifaces = list(self.namespaces.keys())
        for iface in ifaces:
            self._lhost.ui.delete_namespace(self.namespaces[iface])
            del self.namespaces[iface]

    def delete_ipaddr(self, ifaces=None):
        """Delete configured IP addresses for specified interface.

        Args:
            ifaces(list[str]):  interface names

        """
        if not ifaces:
            ifaces = self.iface_ip
        for iface in ifaces:
            self._lhost.ui.modify_ports([iface], ipAddr=None)
        self.iface_ip = []

    def clear_statistics(self, sniff_port_list):
        """Clear statistics - number of frames.

        Args:
            sniff_port_list(list):  List of interface names.

        Returns:
            None

        """
        pass

    def get_received_frames_count(self, iface):
        """Read statistics - number of received valid frames.

        Args:
            iface(str):  Interface name.

        Returns:
            int:  Number of received frames.

        """
        pytest.skip("Method is not supported by Iperf TG")

    def get_filtered_frames_count(self, iface):
        """Read statistics - number of received frames which fit filter criteria.

        Args:
            iface(str):  Interface name.

        Returns:
            int: Number of filtered frames.

        """
        pytest.skip("Method is not supported by Iperf TG")

    def get_uds_3_frames_count(self, iface):
        """Read statistics - number of non-filtered received frames (valid and invalid).

        Args:
            iface(str):  Interface name.

        Returns:
            int:  Number of received frames.

        """
        pytest.skip("Method is not supported by Iperf TG")

    def get_sent_frames_count(self, iface):
        """Read statistics - number of sent frames.

        Args:
            iface(str):  Interface name.

        Returns:
            int:  Number of sent frames.

        """
        pytest.skip("Method is not supported by Iperf TG")

    def set_flow_control(self, iface, mode):
        """Enable/Disable flow control on the port.

        Args:
            iface(str):  Interface name.
            mode(bool):  True/False.

        Returns:
            None

        """
        pytest.skip("Method is not supported by Iperf TG")

    def set_qos_stat_type(self, iface, ptype):
        """Set the QoS counters to look for priority bits for given packets type.

        Args:
            iface(str):  Interface name.
            ptype(str):  Priority type: VLAN/IP.

        Returns:
            None

        """
        pytest.skip("Method is not supported by Iperf TG")

    def get_qos_frames_count(self, iface, prio):
        """Get captured QoS frames count.

        Args:
            iface(str):  Interface name.
            prio(int):  Priority.

        Returns:
            int:  captured QoS frames count

        """
        pytest.skip("Method is not supported by Iperf TG")

    def get_port_txrate(self, iface):
        """Return port transmission rate.

        Args:
            iface(str):  Interface name.

        Returns:
            int:  Frames per second

        """
        pytest.skip("Method is not supported by Iperf TG")

    def get_port_rxrate(self, iface):
        """Return port receiving rate.

        Args:
            iface(str):  Interface name.

        Returns:
            int:  Frames per second.

        """
        pytest.skip("Method is not supported by Iperf TG")

    def get_port_qos_rxrate(self, iface, qos):
        """Return port receiving rate for specific qos.

        Args:
            iface(str):  Interface name.
            qos(int):  Qos value.

        Returns:
            int:  Frames per second

        """
        pytest.skip("Method is not supported by Iperf TG")

    def get_os_mtu(self, iface=None):
        """
        @brief  Get MTU value in host OS
        @param iface:  Interface name for getting MTU in host OS
        @type  iface:  str
        @rtype:  int
        @return:  Original MTU value
        @par  Example:
        @code
        env.tg[1].get_os_mtu(iface=ports[('tg1', 'sw1')][1])
        @endcode
        """
        if not iface:
            return None

        # TODO: get_port_by(name=iface)/get(port=by(name=iface))?
        port_it = (port for port in self._lhost.ui.get_table_ports() if port['name'] == iface)
        return next(port_it, None)

    def set_os_mtu(self, iface=None, mtu=None):
        """Set MTU value in host OS.

        Args:
            iface(str):  Interface for changing MTU in host OS
            mtu(int):  New MTU value

        Returns:
            int:  Original MTU value

        Examples::

            env.tg[1].set_os_mtu(iface=ports[('tg1', 'sw1')][1], mtu=1650)

        """
        if not(iface and mtu):
            return

        self._lhost.ui.modify_ports([iface], mtu=mtu)

    def connect_port(self, iface):
        """Simulate port link connecting (set it to admin up etc).

        Args:
            iface(str):  Interface to connect.

        Raises:
            NotImplementedError:  not implemented

        Returns:
            None or raise and exception.

        """
        self.iface_config(iface, adminMode='Up')

    def disconnect_port(self, iface):
        """Simulate port link disconnecting (set it to admin down etc).

        Args:
            iface(str):  Interface to disconnect.

        Raises:
            NotImplementedError:  not implemented

        Returns:
            None or raise and exception.

        """
        self.iface_config(iface, adminMode='Down')

    @property
    def last_stream_result(self):
        return self.stream_results[-1]

    @property
    def last_sniff_result(self):
        return self.sniff_results[-1]

    @contextmanager
    def ns_context(self, ns):
        try:
            self._lhost.ui.enter_namespace(ns)
            yield self
        finally:
            self._lhost.ui.exit_namespace()

    @contextmanager
    def tg_context(self, do_create=True, do_start=True, do_stop=True):
        try:
            if do_create:
                self.create()
            if do_start:
                self.start()
            yield self
        finally:
            if do_stop:
                self.stop()

    @contextmanager
    def stream_context(self, **kwargs):
        try:
            stream_id = self.set_stream(**kwargs)
            yield stream_id
        finally:
            self.stop_stream(stream_id)

    @contextmanager
    def sniff_context(self, iface, **kwargs):
        try:
            self.start_sniff([iface], **kwargs)
            yield self
        finally:
            self.stop_sniff([iface])


ENTRY_TYPE = "tg"
# used in HOST_MAP
INSTANCES = {
    "riperf": RemoteIperfTG,
    "riperf_vm": RemoteIperfTG,
}
NAME = "tg"
