# Copyright (c) 2016 - 2017, Intel Corporation.
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

"""``iperf.py``

`Run iperf on the remote host and parse output`

"""

import os
import sys
import operator

from collections import namedtuple, OrderedDict
from contextlib import suppress

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from utils.iperflexer import sumparser  # noqa ignore: E402  # pylint: disable=no-name-in-module
from utils.iperflexer import iperfexpressions  # noqa ignore: E402  # pylint: disable=no-name-in-module
from utils.iperflexer.main import UNITS  # noqa ingore: E402  pylint: disable=no-name-in-module
from testlib.linux import tool_general  # noqa ingore: E402  pylint: disable=no-name-in-module
from testlib.linux.iperf import iperf_cmd  # noqa ingore: E402  pylint: disable=no-name-in-module

Line = namedtuple('Line', 'interval, transfer, t_units, bandwidth, b_units')

IPERF_UNITS = {
    'm': 'mbits',
    'k': 'kbits',
    'M': 'mbytes',
    'K': 'kbytes',
    'a': 'mbytes',
    'g': 'gbits',
    'G': 'gbytes',
}


class IPerfParser(sumparser.SumParser):
    """Class for parsing Iperf output.

    """

    def __init__(self, *args, **kwargs):
        """Initialize IPerfParser class.

        """
        if kwargs.get('units', None):
            kwargs['units'] = UNITS[kwargs['units']]
        super(IPerfParser, self).__init__(*args, **kwargs)
        self.format = iperfexpressions.ParserKeys.human

    def parse(self, output):
        """Parse output from iperf execution.

        Args:
            output(str): iperf output

        Returns:
            list:  list of parsed iperf results

        """
        results = []
        for line in output.splitlines():
            match = self.search(line)
            if match:
                start = float(match[iperfexpressions.ParserKeys.start])
                end = float(match[iperfexpressions.ParserKeys.end])
                bandwidth = self.bandwidth(match)
                transfer = self.transfer(match)
                results.append(Line((start, end),
                                    transfer,
                                    self._transfer_units,
                                    bandwidth,
                                    self.units))
        return results


class IperfStats(object):
    """
    Iperf output statistics from a single run (process)
    """
    DEFAULT_UNITS = 'mbytes'
    DEFAULT_THREADS = 1

    LAST_LINE_GETTER = operator.itemgetter(-1)

    def __init__(self, command=None, iface=None, data_raw=None, data_parsed=None, parser=None):
        super(IperfStats, self).__init__()

        self.command = command
        self.iface = iface

        if not parser:
            parser = self.parser_from_command(command)
        self.parser = parser

        if not data_parsed and data_raw:
            data_parsed = self.parsed_from_raw(data_raw)
        self.output_raw = data_raw
        self.output_parsed = data_parsed

    @property
    def last_line(self):
        with suppress(AttributeError):
            return self._last_line

        with suppress(IndexError):
            self._last_line = self.LAST_LINE_GETTER(self.output_parsed)
            return self._last_line

        self._last_line = None
        return self._last_line

    @classmethod
    def parser_from_command(cls, command):
        return IPerfParser(units=command.get('format', cls.DEFAULT_UNITS),
                           threads=command.get('parallel', cls.DEFAULT_THREADS))

    def parsed_from_raw(self, data_raw, parser=None):
        if not parser:
            parser = self.parser
        return self.parser.parse(data_raw)

    def parse(self, output, raw=None):
        if raw:
            self.output_raw = raw
            self.output_parsed = output
        else:
            self.output_raw = output
            self.output_parsed = self.parser.parse(output)

    def __str__(self):
        return self.retval()

    @classmethod
    def dict_to_str(cls, a_dict,
                    dict_items_formatter="\"{0[0]}\"=\"{0[1]}\"".format,
                    dict_items_joint=", ".join,
                    dict_items_iterator=dict.items):
        return str(dict_items_joint(map(dict_items_formatter,
                                        dict_items_iterator(a_dict))))

    @property
    def retval(self):
        last_line = self.last_line

        retval = {
            "comment": self.dict_to_str(
                dict(
                    command=str(" ".join(map(str, self.command.to_args_list()))),
                    interface=str(self.iface),
                    interval=str("-".join(map(str, last_line.interval[0:1]))),
                    time=str(last_line.interval[1]),
                )
            ),
            "metrics": OrderedDict((
                (
                    "bandwidth",
                    {
                        # "name": "bandwidth",
                        "value": last_line.bandwidth,
                        "units": last_line.b_units,
                    }
                ),
                (
                    "transfer",
                    {
                        # "name": "transfer",
                        "value": last_line.transfer,
                        "units": last_line.t_units,
                    }
                )
            ))
        }
        return retval


class Iperf(tool_general.GenericTool):
    """Class for Iperf functionality.

    """

    def __init__(self, run_command):
        """Initialize Iperf class.

        Args:
            run_command(function): function that runs the actual commands

        """
        super(Iperf, self).__init__(run_command, 'iperf')

    def start(self, prefix=None, options=None, command=None, **kwargs):
        """Generate Iperf command, launch iperf and store results in the file.

        Args:
            prefix(str): command prefix
            options(list of str): intermediate iperf options list
            command(Command): intermediate iperf command object

        Returns:
            dict:  iperf instance process info

        """
        # intermediate operands in 'command' and 'options', if any,  prevail in this
        # respective order and overrule the (both default and set) method arguments
        cmd = iperf_cmd.CmdIperf(kwargs, options, command)
        cmd.check_args()
        args_list = cmd.to_args_list()

        # TODO: do we need timeout with systemd?
        cmd_time = cmd.get('time', 10)
        timeout = int(cmd_time) + 30 if cmd_time else 60

        cmd_list = [self.tool]
        if prefix:
            cmd_list = [prefix, self.tool]

        if args_list:
            cmd_list.extend(args_list)

        cmd_str = ' '.join(map(str, cmd_list))
        instance_id = super(Iperf, self).start(cmd_str, timeout=timeout)
        self.instances[instance_id]['iperf_cmd'] = cmd
        return instance_id

    def parse(self, output, parser=None, threads=1, units='m'):
        """Parse the Iperf output.

        Args:
            output(str):  Iperf origin output
            parser(IPerfParser): parser object
            threads(int): num iperf threads
            units(str): iperf units

        Returns:
            list:  list of parsed iperf results

        """
        if not parser:
            parser = IPerfParser(threads=threads, units=IPERF_UNITS[units])

        return parser.parse(output)
