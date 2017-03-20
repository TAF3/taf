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

"""``pytest_onsenv.py``

`Multiple traffic generator specific functionality`

"""
from collections import namedtuple

from . import loggers
from .tg_template import GenericTG
from .packet_processor import PacketProcessor


DEFAULT_SPEED = 10000


Port = namedtuple('Port', 'tg, port')


class MultipleTG(PacketProcessor, GenericTG):
    """Class for general TG instance combined with multiple different TGs.

    """

    class_logger = loggers.ClassLogger()

    def __init__(self, traffic_generators, config, opts):
        """Initialize RemoteMultiHostTG class.

        Args:
            traffic_generators(dict):  Dictionary with TG instances in format {id:tg_instance}
            config(dict):  Configuration information.
            opts(OptionParser):  py.test config.option object which contains all py.test cli options.

        """
        super(MultipleTG, self).__init__(config, opts)

        # TG instances
        self.tgs = {x.id: x for x in traffic_generators.values()}

        # Get ports and port lists
        # For ports use namedtuple(tg.id, port.id)
        self.ports, self.port_list = self._get_speed_ports()

        self.streams = []

        # Indicates if TG object supports high level protocol emulation (can emulate dialogs).
        self.is_protocol_emulation_present = all(x.is_protocol_emulation_present
                                                 for x in self.tgs.values())

    def _get_speed_ports(self):
        """Get ports with speed from TG instances.

        Returns:
            tuple(list[tuple], list[tuple, int]):  Tuple with list of ports used in real config and list of port/speed values

        """

        ports = []
        ports_list = []
        if any(x.port_list for x in self.tgs.values()):
            for tg in self.tgs.values():
                if tg.port_list:
                    ports_list.extend([[Port(tg.id, _port[0]), _port[1]] for _port in tg.port_list])
                else:
                    ports_list.extend([[Port(tg.id, _port), DEFAULT_SPEED] for _port in tg.ports])
            ports = [_port[0] for _port in ports_list]
        else:
            ports = [Port(x.id, port) for x in self.tgs.values() for port in x.ports]

        return ports, ports_list

    def get_tg_port_map(self, ifaces):
        """Return ports related to specific TG.

        Args:
            ifaces(list(tuple)): list of interfaces in format (tg_id, port_id)

        Returns:
            dict:  dictionary in format {'host id': [port ids]}

        """
        iface_map = {}
        for iface in ifaces:
            iface_map.setdefault(iface.tg, []).append(iface.port)
        return iface_map

    def get_port_id(self, tg_id, port_id):
        """Return port's sequence number in list of ports.

        Args:
            tg_id(int):  TG instance ID
            port_id(int):  TG instance port's sequence number

        Raises:
            ValueError:  in case expected port is not in list of ports

        Returns:
            int:  Port sequence number in list of ports starting from 1

        """
        port_name = self.tgs[tg_id].ports[port_id - 1]
        return self.ports.index(Port(tg_id, port_name)) + 1

    def start(self, wait_on=True):
        """Start TG instances.

        """
        for tg in self.tgs.values():
            tg.start()

        self.status = all(x.status for x in self.tgs.values())  # pylint: disable=attribute-defined-outside-init

    def stop(self):
        """Shutdown TG instances.

        """
        for tg in self.tgs.values():
            tg.stop()

    def create(self):
        """Start TG instances or get running ones.

        """
        for tg in self.tgs.values():
            tg.create()

    def destroy(self):
        """Stop or release TG instances.

        """
        for tg in self.tgs.values():
            tg.destroy()

    def cleanup(self, *args, **kwargs):
        """Cleanup TG instances.

        """
        self.streams = []
        for tg in self.tgs.values():
            tg.cleanup()

    def check(self):
        """Check TG instances.

        """
        for tg in self.tgs.values():
            tg.check()

    def sanitize(self):
        """Perform any necessary operations to leave environment in normal state.

        """
        self.streams = []
        for tg in self.tgs.values():
            tg.sanitize()

    def stop_sniff(self, *args, **kwargs):
        """Collect sniffed data from all TG instances.

        """
        iface_map = self.get_tg_port_map(*args)
        data_hosts = {}
        for tg, ifaces in iface_map.items():
            data_hosts[tg] = self.tgs[tg].stop_sniff(ifaces, **kwargs)

        data = {}
        for tg, ifaces in data_hosts.items():
            for iface in ifaces:
                data['{} {}'.format(tg, iface)] = data_hosts[tg][iface]
        return data

    def connect_port(self, iface):
        """Simulate port link connecting (set it to admin up etc).

        Args:
            iface(str):  Interface to connect.

        Raises:
            NotImplementedError:  not implemented

        Returns:
            None or raise and exception.

        """
        self.tgs[iface.tg].connect_port(iface.port)

    def disconnect_port(self, iface):
        """Simulate port link disconnecting (set it to admin down etc).

        Args:
            iface(str):  Interface to disconnect.

        Raises:
            NotImplementedError:  not implemented

        Returns:
            None or raise and exception.

        """
        self.tgs[iface.tg].disconnect_port(iface.port)

    def clear_streams(self):
        """Stop and remove all streams.

        """
        self.streams = []
        for tg in self.tgs.values():
            tg.clear_streams()

    def set_stream(self, *args, **kwargs):
        """Set traffic stream with specified parameters on specified TG port.

        Returns:
            int: stream id

        Notes:
            It's not expected to configure a lot of incrementation options. Different traffic generator could have different limitations for these options.

        Examples::

            stream_id_1 = tg.set_stream(pack_ip, count=100, iface=iface)
            stream_id_2 = tg.set_stream(pack_ip, continuous=True, inter=0.1, iface=iface)
            stream_id_3 = tg.set_stream(pack_ip_udp, count=5, protocol_increment=(3, 5), iface=iface)
            stream_id_4 = tg.set_stream(pack_ip_udp, count=18, sip_increment=(3, 3), dip_increment=(3, 3), iface=iface,
                                        udf_dependancies={'sip_increment': 'dip_increment'})

        """
        tg, kwargs['iface'] = kwargs['iface']
        stream_id = self.tgs[tg].set_stream(*args, **kwargs)
        tg_stream_id = Port(tg, stream_id)
        self.streams.append(tg_stream_id)
        return tg_stream_id

    def send_stream(self, stream_id, **kwargs):
        """Sends the stream created by 'set_stream' method.

        Args:
            stream_id(int):  ID of the stream to be send.

        Returns:
            float: timestamp.

        """
        tg, stream = stream_id
        self.tgs[tg].send_stream(stream, **kwargs)

    def start_streams(self, stream_list):
        """Enable and start streams from the list simultaneously.

        Args:
            stream_list(list[int]):  List of stream IDs.

        Returns:
            None

        """
        stream_map = self.get_tg_port_map(stream_list)

        for tg, streams in stream_map.items():
            self.tgs[tg].start_streams(streams)

    def stop_streams(self, stream_list=None):
        """ Disable streams from the list.

        Args:
            stream_list(list[int]):  Stream IDs to stop. In case stream_list is not set all running streams will be stopped.

        Returns:
            None

        """
        stream_map = self.get_tg_port_map(stream_list)

        for tg, streams in stream_map.items():
            self.tgs[tg].stop_streams(streams)

    def start_sniff(self, ifaces, **kwargs):
        """Starts sniffing on specified interfaces.

        Args:
            ifaces(list):  List of TG interfaces for capturing.
            kwargs(dict):  Possible parameters to configure.

        Returns:
            None

        Notes:
            This method introduces additional 1.5 seconds timeout after capture enabling.
            It's required by Ixia sniffer to wait until capturing is started.

        Examples::

            env.tg[1].start_sniff(['eth0', ], filter_layer='IP', src_filter='00:00:00:01:01:01', dst_filter='00:00:00:22:22:22')

        """
        iface_map = self.get_tg_port_map(ifaces)

        for tg, ports in iface_map.items():
            self.tgs[tg].start_sniff(ports, **kwargs)

    def clear_statistics(self, sniff_port_list):
        """Clearing statistics on TG ports.

        """
        iface_map = self.get_tg_port_map(sniff_port_list)

        for tg, ports in iface_map.items():
            self.tgs[tg].clear_statistics(ports)

    def get_received_frames_count(self, iface):
        """Read statistics - framesReceived.

        """
        return self.tgs[iface.tg].get_received_frames_count(iface.port)

    def get_filtered_frames_count(self, iface):
        """Read statistics - filtered frames received.

        """
        return self.tgs[iface.tg].get_filtered_frames_count(iface.port)

    def get_uds_3_frames_count(self, iface):
        """Read statistics - UDS3 - Capture Trigger (UDS3) - count of non-filtered received packets (valid and invalid).

        """
        return self.tgs[iface.tg].get_uds_3_frames_count(iface.port)

    def clear_received_statistics(self, iface):
        """Clear statistics.

        """
        return self.tgs[iface.tg].clear_received_statistics(iface.port)

    def get_sent_frames_count(self, iface):
        """Read statistics - framesSent.

        """
        return self.tgs[iface.tg].get_sent_frames_count(iface.port)

    def get_port_txrate(self, iface):
        """Get port Tx rate.

        """
        return self.tgs[iface.tg].get_port_txrate(iface.port)

    def get_port_rxrate(self, iface):
        """Get port Rx rate.

        """
        return self.tgs[iface.tg].get_port_rxrate(iface.port)

    def get_port_qos_rxrate(self, iface, qos):
        """Get ports Rx rate for specific qos.

        """
        return self.tgs[iface.tg].get_port_qos_rxrate(iface.port, qos)

    def get_qos_frames_count(self, iface, prio):
        """Get QoS packets count.

        """
        return self.tgs[iface.tg].get_qos_frames_count(iface.port, prio)

    def set_qos_stat_type(self, iface, ptype):
        """Set QoS stats type.

        """
        return self.tgs[iface.tg].set_qos_stat_type(iface.port, ptype)

    def set_flow_control(self, iface, mode):
        """Set Flow Control.

        """
        return self.tgs[iface.tg].set_flow_control(iface.port, mode)

    def get_os_mtu(self, iface=None):
        """Get MTU value in host OS.

        Args:
            iface(str):  Interface for getting MTU in host OS

        Returns:
            int: Original MTU value

        Examples::

            env.tg[1].get_os_mtu(iface=ports[('tg1', 'sw1')][1])

        """
        return self.tgs[iface.tg].get_os_mtu(iface.port)

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
        return self.tgs[iface.tg].set_os_mtu(iface.port, mtu)
