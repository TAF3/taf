"""
@copyright Copyright (c) 2017, Intel Corporation.

This program is free software; you can redistribute it and/or modify it
under the terms and conditions of the GNU Lesser General Public License,
version 2.1, as published by the Free Software Foundation.

This program is distributed in the hope it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
more details.

@file  ping_cmd.py

@summary  ping command parsing and building support
"""

import itertools

from collections import OrderedDict
from argparse import ArgumentParser

from testlib.linux.commands.cmd_helper import Command, CommandHelper, ArgumentBuilder
from testlib.linux.commands import cmd_exceptions as cmd_ex


PING_OPTS = {
    '__a': {
        'names': {'short': '-a'},
        'help': 'audible ping'
    },
    '__A': {
        'names': {'short': '-A'},
        'help': 'adaptive ping'
    },
    '__b': {
        'names': {'short': '-b'},
        'help': 'allow pinging a broadcast address'
    },
    '__B': {
        'names': {'short': '-B'},
        'help': '-B'
    },
    '__d': {
        'names': {'short': '-d'},
        'help': 'set the SO_DEBUG option on the socket being used.'
    },
    '__f': {
        'names': {'short': '-f'},
        'help': 'flood ping'
    },
    '__L': {
        'names': {'short': '-L'},
        'help': 'suppress loopback of multicast packets'
    },
    '__n': {
        'names': {'short': '-n'},
        'help': 'numeric output only'
    },
    '__q': {
        'names': {'short': '-q'},
        'help': 'quiet output'
    },
    '__R': {
        'names': {'short': '-R'},
        'help': 'Record route'
    },
    '__r': {
        'names': {'short': '-r'},
    },
    '__U': {
        'names': {'short': '-U'},
        'help': 'print full uset-to-user latency'
    },
    '__v': {
        'names': {'short': '-v'},
        'help': 'verbose output'
    },
    '__V': {
        'names': {'short': '-V'},
        'help': 'show version and exit'
    }
}


PING_OPT_VAL_PAIRS = {
    '__c': {
        'names': {'short': '-c'},
        'help': '(count) stop after sending count ECHO_REQUEST packets',
        'type': int
    },
    '__F': {
        'names': {'short': '-F'},
        'help': '(flow label) alocate and set 20 bit flow label on echo request packets'
    },
    '__i': {
        'names': {'short': '-i'},
        'help': '(interval) wait <interval> seconds between sending each packet'
    },
    '__I': {
        'names': {'short': '-I'},
        'help': '(interface address) set source address to specified <interface address>'
    },
    '__l': {
        'names': {'short': '-l'},
        'help': '(preload) ping sends <preload> many packets not waiting for reply',
        'type': int
    },
    '__p': {
        'names': {'short': '-p'},
        'help':  '(pattern) 16 "pad" bytes to fill out the packet'
    },
    '__Q': {
        'names': {'short': '-Q'},
        'help': '(tos) set Quality of Service -related bits in ICMP datagrams'
    },
    '__s': {
        'names': {'short': '-s'},
        'help': '(packetsize) specifies the number of data bytes to be sent'
    },
    '__S': {
        'names': {'short': '-S'},
        'help': '(sndbuf) set socket sndbuf',
        'type': int
    },
    '__t': {
        'names': {'short': '-t'},
        'help': '(ttl) set the IP Time to Live'
    },
    '__T': {
        'names': {'short': '-T'},
        'help': '(timestamp option) set special IP timestamp options'
    },
    '__M': {
        'names': {'short': '-M'},
        'help': '(hint) select Path MTU Discovery strategy',
        'choices': ['do', 'want', 'dont']
    },
    '__w': {
        'names': {'short': '-w'},
        'help': '(deadline) specify a timeout, in seconds, before ping exits regardless of how \
                 many packets have been sent or received. In this case ping does not stop after \
                 <count> packets are sent, it waits either for <deadline> to expire or until \
                 <count> probes are answered or for some error notification from network',
        'type': int
    },
    '__W': {
        'names': {'short': '-W'},
        'help': '(timeout) time to wait for a response, in seconds. The option affects only \
                 in absence of any responses, otherwise ping waits for two RTTS',
        'type': int
    }
}

PING_POS_ARGS = {
    '__host': {
    }
}


# fine-tune options by class accordingly
for v in PING_OPTS.values():
    v.update(action='store_true')


__OPT_KV_PAIR_NO_VAL__ = object()
__OPT_KV_PAIR_NO_VAL_KWARGS = {
    'nargs': '?',
    'const': __OPT_KV_PAIR_NO_VAL__,
    'default': __OPT_KV_PAIR_NO_VAL__
}
for v in PING_OPT_VAL_PAIRS.values():
    v.update(__OPT_KV_PAIR_NO_VAL_KWARGS)


# specify the order of the output arguments when buildinig up a command
_PING_ARGS_ORDERED = OrderedDict(
    itertools.chain(sorted(PING_OPTS.items()),
                    sorted(PING_OPT_VAL_PAIRS.items()),
                    sorted(PING_POS_ARGS.items())))


class PingArgumentBuilder(ArgumentBuilder):
    """
    """
    ARGS_ORDERED = _PING_ARGS_ORDERED
    ARGS_FORMATTER = {}  # init after class definition

    @classmethod
    def get_args_formatter(cls, redo=False):
        if redo or not cls.ARGS_FORMATTER:
            cls.ARGS_FORMATTER = {
                'optional': cls.FORMATTER_BY_VALUE_MAP(
                    {
                        None: cls.FORMAT_NONE,
                        cls.__FALSE__: cls.FORMAT_NONE,
                        __OPT_KV_PAIR_NO_VAL__: cls.FORMAT_KEY_BY_TAG('short'),
                        cls.__TRUE__: cls.FORMAT_KEY_BY_TAG('short'),
                    },
                    default=cls.FORMATTER_JOIN_KEY_VAL(
                        key=cls.FORMAT_KEY_BY_TAG('short'),
                        joiner=cls.FORMAT_ARG_APPEND_LIST,
                        val=cls.FORMAT_VAL_TRANSFORM(str),
                    )
                ),
                'positional': cls.FORMAT_VAL_TRANSFORM(str)
            }
        return cls.ARGS_FORMATTER

    def __init__(self):
        super(PingArgumentBuilder, self).__init__(args_order=self.ARGS_ORDERED,
                                                  args_formatter=self.get_args_formatter())


PingArgumentBuilder.get_args_formatter()


class CmdPingHelper(CommandHelper):
    """
    """
    ARG_PREFIX = ''

    @classmethod
    def check_args(cls, *args, **__kwargs):
        return cls._check_args(**cls._encode_args(**__kwargs))

    @classmethod
    def check_opts(
            cls,
            __a=None, __A=None, __b=None, __B=None, __d=None, __f=None, __L=None, __n=None,
            __q=None, __R=None, __r=None, __U=None, __v=None,
            **__kwargs):

        return __kwargs

    @classmethod
    def check_opt_val_pairs(
            cls,
            __c=None, __F=None, __i=None, __I=None, __l=None, __p=None, __Q=None, __s=None,
            __S=None, __t=None, __T=None, __M=None, __w=None, __W=None,
            **__kwargs):

        return __kwargs

    @classmethod
    def check_pos_args(
            cls,
            __host=None,
            **__kwargs):

        if not __host:
            raise cmd_ex.ArgumentsNotSet('host')

        return __kwargs

    @classmethod
    def _check_args(cls, **__kwargs):
        __kwargs = cls.check_opts(**__kwargs)
        __kwargs = cls.check_opt_val_pairs(**__kwargs)
        __kwargs = cls.check_pos_args(**__kwargs)

        if __kwargs:
            raise cmd_ex.UnknownArguments(**cls._decode_args(**__kwargs))

        return True


PING_PARSER = ArgumentParser(prog='ping', conflict_handler='resolve')
PING_BUILDER = PingArgumentBuilder()

ping_cmd_kwargs = {
    'arg_parser': PING_PARSER,
    'params': _PING_ARGS_ORDERED,
    'arg_builder': PING_BUILDER,
    'default_list': [None]
}
PING_CMD_HELPER = CmdPingHelper(**ping_cmd_kwargs)


class CmdPing(Command):
    CMD_HELPER = PING_CMD_HELPER
