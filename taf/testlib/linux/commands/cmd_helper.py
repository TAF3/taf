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

"""``cmd_helper.py``

`Flexible command representation with parsing and building support`

"""

import copy
import operator
import itertools
import argparse

from contextlib import suppress
from collections import Mapping, OrderedDict

from testlib.linux.commands import cmd_exceptions as cmd_ex


class ArgumentBuilder(object):
    """
    """
    ARGS_ORDER = []

    def __init__(self, args_order=None, args_formatter=None):
        self.args_order = args_order
        self.args_formatter = args_formatter

    GET_FIRST = operator.itemgetter(0)
    GET_LAST = operator.itemgetter(-1)

    # SECTION optional args' key formatter
    @classmethod
    def FORMAT_KEY_FIRST(cls, params, arg_name=None, **kwargs):
        keys = list(params[arg_name]['names'].values())
        return cls.GET_FIRST(keys)

    @classmethod
    def FORMAT_KEY_LAST(cls, params, arg_name=None, **kwargs):
        keys = list(params[arg_name]['names'].values())
        return cls.GET_LAST(keys)

    @classmethod
    def FORMAT_KEY_LONGEST(cls, params, arg_name=None, **kwargs):
        keys = list(params[arg_name]['names'].values())
        return max(keys, key=len)

    @classmethod
    def FORMAT_KEY_SHORTEST(cls, params, arg_name=None, **kwargs):
        keys = list(params[arg_name]['names'].values())
        return min(keys, key=len)

    @classmethod
    def FORMAT_NONE(cls, *args, **kwargs):
        pass

    @classmethod
    def FORMAT_KEY_BY_TAG(cls, tag):
        _tag_getter = operator.itemgetter(tag)

        def wrapper(params, arg_name=None, **kwargs):
            return _tag_getter(params[arg_name]['names'])
        return wrapper

    @classmethod
    def FORMAT_VAL_TRANSFORM(cls, trans_f):
        def wrapper(params, arg_val=None, **kwargs):
            return trans_f(arg_val)
        return wrapper

    @classmethod
    def FORMAT_ARG_APPEND_LIST(cls, params, key_fmtd=None, val_fmtd=None, **kwargs):
        return [key_fmtd, val_fmtd]

    @classmethod
    def FORMAT_ARG_JOIN_STR(cls, join_char=None):
        def wrapper(params, key_fmtd=None, val_fmtd=None, **kwargs):
            return '{}{}{}'.format(key_fmtd, join_char, val_fmtd)
        return wrapper

    @classmethod
    def FORMATTER_JOIN_KEY_VAL(cls, key=None, val=None, joiner=None):
        def wrapper(params, arg_name=None, arg_val=None, **kwargs):
            arg_kwargs = {
                'arg_name': arg_name,
                'arg_val': arg_val,
            }
            out = None
            if key:
                arg_kwargs['key_fmtd'] = key(params, **arg_kwargs)
            if val:
                arg_kwargs['val_fmtd'] = val(params, **arg_kwargs)
            if joiner:
                out = joiner(params, **arg_kwargs)
            return out
        return wrapper

    # a little hack to allow for booleans to simulate unique objects behavior.
    # As opposed to ints 0/1 for keywords False/True respectively.
    __FALSE__ = object()
    __TRUE__ = object()
    __BOOL_MAP__ = {}

    @classmethod
    def FORMATTER_BY_VALUE_MAP(cls, val_map, default=None):
        def wrapper(params, arg_name=None, arg_val=None, **kwargs):
            if isinstance(arg_val, bool):
                __arg_val = cls.__BOOL_MAP__[arg_val]
                arg_formatter = val_map.get(__arg_val, default)
            else:
                arg_formatter = val_map.get(arg_val, default)

            if arg_formatter:
                return arg_formatter(params, arg_name=arg_name, arg_val=arg_val)
        return wrapper

    # SECTION builder
    def build_args(self, opts_map, pos_map, args, order=None, formatter=None):
        """
        """
        if not order:
            if self.args_order:
                order = self.args_order
            else:
                order = sorted(args)

        if not formatter:
            if self.args_formatter:
                formatter = self.args_formatter
            else:
                formatter = self.__DEFAULT_FORMATTER

        args_list = []
        unknown_kwargs = {}
        for arg_name in order:
            try:
                arg_val = args[arg_name]
            except KeyError:
                continue

            opts_arg = opts_map.get(arg_name)
            pos_arg = pos_map.get(arg_name)
            both = opts_arg and pos_arg
            neither = not opts_arg and not pos_arg
            if both:
                # ???
                raise ValueError(arg_name)
            if neither:
                unknown_kwargs[arg_name] = arg_val

            if unknown_kwargs:
                continue

            if opts_arg:
                assert 'names' in opts_arg
                fmt = formatter['optional']
                args_map = opts_map

            else:  # if pos_arg
                assert 'pos' in pos_arg
                fmt = formatter['positional']
                args_map = pos_map

            out = fmt(args_map, arg_name=arg_name, arg_val=arg_val)
            if out:
                if isinstance(out, list):
                    args_list.extend(out)
                elif isinstance(out, str):
                    args_list.append(out)
                else:
                    raise TypeError(out)

            # cmd_ex.UnknownArguments(unknown_kwargs).raise_on_true()
            cmd_ex.UnknownArguments.raise_on_true(unknown_kwargs)
        return args_list

    @classmethod
    def get_formatter(cls):
        _formatter = {
            'optional': cls.FORMATTER_BY_VALUE_MAP(
                {
                    cls.__TRUE__: cls.FORMAT_KEY_FIRST,
                    cls.__FALSE__: cls.FORMAT_NONE,
                    None: cls.FORMAT_NONE,
                },
                default=cls.FORMATTER_JOIN_KEY_VAL(
                    key=cls.FORMAT_KEY_FIRST,
                    joiner=cls.FORMAT_ARG_APPEND_LIST,
                    val=cls.FORMAT_VAL_TRANSFORM(str),
                ),
            ),
            'positional': cls.FORMAT_VAL_TRANSFORM(str),
        }
        return _formatter

    __DEFAULT_FORMATTER = {}


ArgumentBuilder.__BOOL_MAP__ = {
    False: ArgumentBuilder.__FALSE__,
    True: ArgumentBuilder.__TRUE__,
}

ArgumentBuilder.__DEFAULT_FORMATTER = ArgumentBuilder.get_formatter()  # pylint: disable=protected-access


class CommandHelper(object):
    """
    """
    MANGLED_CLS_PREFIX = ''
    ARG_PREFIX = '__'
    ARG_SUFFIX = ''
    FORMATTER = ''

    ST_ALWAYS = 'always'
    ST_NEVER = 'never'
    ST_VALUE_NONDEFAULT = 'value_nondefault'
    SET_TRAITS = {
        ST_ALWAYS,
        ST_NEVER,
        ST_VALUE_NONDEFAULT,
    }
    DEFAULT_SET_TRAITS = ST_VALUE_NONDEFAULT

    @classmethod
    def _get_cls_prefix(cls):
        if not cls.MANGLED_CLS_PREFIX:
            cls.MANGLED_CLS_PREFIX = '_{}'.format(cls.__name__)
        return cls.MANGLED_CLS_PREFIX

    @classmethod
    def _get_formatter(cls):
        if not cls.FORMATTER:
            cls.FORMATTER = '{0}{1}{{}}{2}'.format(cls._get_cls_prefix(),
                                                   cls.ARG_PREFIX,
                                                   cls.ARG_SUFFIX)
        return cls.FORMATTER

    @classmethod
    def _encode_args(cls, **kwargs):
        return {cls._get_formatter().format(k): v for k, v in kwargs.items()}

    @classmethod
    def _decode_args(cls, **__kwargs):
        return {k[len(cls._get_cls_prefix()) + 2:]: v for k, v in __kwargs.items()}

    @classmethod
    def check_args(cls, **kwargs):
        """Input command arguments checking API.

        Todo:
            abstract

        """
        pass

    def __init__(self, prog=None, arg_parser=None, conflict_handler=None, params=None,
                 arg_builder=None, default_list=None):
        """
        """
        self.posarg_list = []
        self.posarg_map = {}
        self.optarg_list = []
        self.optarg_map = {}
        self.default_image = None
        self.args_blacklist = set()
        self.args_whitelist = set()

        if not conflict_handler:
            conflict_handler = 'resolve'
        if not arg_parser:
            arg_parser = argparse.ArgumentParser(prog=prog, conflict_handler=conflict_handler)
        self.arg_parser = arg_parser

        if not arg_builder:
            arg_builder = ArgumentBuilder()
        self.arg_builder = arg_builder

        if params:
            self._init_params(params, default_list=default_list)

    def _init_params(self, params, default_list=None):
        self.params = params
        for param_name, param_desc in params.items():
            _par = copy.copy(param_desc)

            set_traits = _par.pop('set_traits', self.DEFAULT_SET_TRAITS)
            assert set_traits in self.SET_TRAITS
            if set_traits is self.ST_NEVER:
                self.args_blacklist.add(param_name)
            elif set_traits is self.ST_ALWAYS:
                self.args_whitelist.add(param_name)

            if 'names' in param_desc:  # optional arg
                self.optarg_map[param_name] = _par
                names = _par.pop('names')
                self.arg_parser.add_argument(*list(names.values()), dest=param_name, **_par)
                _par['names'] = names
                _par['pos'] = len(self.optarg_list)
                self.optarg_list.append(param_name)
            else:  # positional arg
                self.posarg_map[param_name] = _par
                self.arg_parser.add_argument(param_name)
                _par['pos'] = len(self.posarg_list)
                self.posarg_list.append(param_name)

        if default_list is None:
            default_list = [None] * len(self.posarg_map)
        self.default_image = self.arg_parser.parse_args(default_list)
        assert self.default_image

    def parse_args(self, args_list):
        return self.arg_parser.parse_args(args_list)

    def _get_reverse_dest_action_map(self):
        with suppress(AttributeError):
            return self.dest2action_map

        self.dest2action_map = {action.dest: action for action in self.arg_parser._actions}
        return self.dest2action_map

    def _check_arg_value(self, arg_name, arg_val, noraise=False):
        actions_map = self._get_reverse_dest_action_map()
        try:
            arg_action = actions_map[arg_name]
        except KeyError:
            raise cmd_ex.UnknownArguments(arg_name=arg_val)

        try:
            # the following 2 methods may violate `argparse` "encapsulation"
            value = self.arg_parser._get_value(arg_action, arg_val)
            self.arg_parser._check_value(arg_action, value)
        except argparse.ArgumentError:
            if noraise:
                return False
            else:
                raise cmd_ex.InvalidArguments(arg_name=arg_val)
        return True

    def check_values(self, **kwargs):
        unknown = {}
        invalid = {}
        for arg_name, arg_val in kwargs.items():
            try:
                if not self._check_arg_value(arg_name, arg_val, noraise=True):
                    invalid[arg_name] = arg_val
            except cmd_ex.UnknownArguments:
                unknown[arg_name] = arg_val

        cmd_ex.UnknownArguments.raise_on_true(unknown)
        cmd_ex.InvalidArguments.raise_on_true(invalid)

    def get_set_args(self, args_in, args_out=None, args_order=None, args_bl=set(), args_wl=set()):
        """
        @brief A command builder helper function.
            Strips the dict off the unset (default) arguments.
            Learns which fields in 'args_in' (dict or argparse.Namespace instance), possibly
            parsed earlier, had been set before the parsing took place.
            If an intermediate dict is provided in 'args_out', mutate in place and overwrite
            it on collision.
        """
        if args_out is None:
            args_out = OrderedDict()

        assert args_in is not None
        if isinstance(args_in, Command):
            args_in = args_in._ns  # pylint: disable=protected-access
        if isinstance(args_in, argparse.Namespace):
            args_in = vars(args_in)

        if not isinstance(args_in, Mapping):
            raise TypeError("Mapping expected. Got {}".format(type(args_in)))

        if not args_order:
            if self.arg_builder.args_order:
                args_order = self.arg_builder.args_order
            else:
                args_order = sorted(args_in)

        for k in args_order:
            if k in args_bl:  # blacklisted, skip
                continue
            if k in args_wl:  # whitelisted, accept
                with suppress(KeyError):
                    args_out[k] = args_in[k]
                continue

            with suppress(AttributeError, KeyError):
                v = getattr(self.default_image, k)
                if v != args_in[k]:
                    args_out[k] = args_in[k]

        return args_out

    def build_cmd_list(self, **kwargs):
        """A command builder helper function.

        Reverse parse_args() functionality.
        Converts the input sequence of command arguments(key[:value] pairs) to a
            command options list.

        """
        return self.arg_builder.build_args(self.optarg_map, self.posarg_map, kwargs)


_DEFAULT_CMD_HELPER = CommandHelper()
_LOCAL_DEFAULT = object()


class Command(Mapping):
    """Command holder object flexible representation.

    """
    CMD_HELPER = _DEFAULT_CMD_HELPER

    @classmethod
    def copy(cls, cmd):
        return cls(cmd)

    @classmethod
    def _validate_args(cls, *args):
        unknown_iter = (a for a in args if not hasattr(cls.CMD_HELPER.default_image, a))
        cmd_ex.UnknownArguments.raise_on_true_lists(list(unknown_iter))

    @classmethod
    def _validate_kwargs(cls, **kwargs):
        cls.CMD_HELPER.check_values(**kwargs)

    @classmethod
    def validate(cls, *args, **kwargs):
        unknown = cmd_ex.UnknownArguments()
        invalid = cmd_ex.InvalidArguments()
        try:
            cls._validate_args(*args)
        except cmd_ex.UnknownArguments as ex_unknown:
            unknown.extend_args(ex_unknown)

        try:
            cls._validate_kwargs(**kwargs)
        except cmd_ex.UnknownArguments as ex_unknown:
            unknown.update(ex_unknown)
        except cmd_ex.InvalidArguments as ex_invalid:
            invalid.update(ex_invalid)

        unknown.raise_on_true()
        invalid.raise_on_true()

    def _update_kwargs(self, **kwargs):
        self._ns.__init__(**kwargs)

    def _extend_kwargs(self, **kwargs):
        set_self = self.get_set_args()
        to_update = {k: v for k, v in kwargs.items() if k not in set_self}
        self._ns.__init__(**to_update)

    def _unset_kwargs(self, **kwargs):
        to_update = {k: getattr(self.CMD_HELPER.default_image, k) for k in kwargs}
        self._ns.__init__(**to_update)

    def __init__(self, *args, **kwargs):
        # technically Mapping has no __init__, but we keep this to be proper for MI
        super(Command, self).__init__()  # pylint: disable=no-member

        self._ns = copy.copy(self.CMD_HELPER.default_image)

        for cmd in args:
            self._init_cmd(cmd)

        if kwargs:
            self._update_kwargs(**self._to_dict(kwargs))

        assert self._ns

    def _init_cmd(self, cmd_rep):
        if not cmd_rep:
            return

        if isinstance(cmd_rep, Command):
            if not isinstance(cmd_rep, self.__class__):
                raise TypeError(type(cmd_rep))
        elif isinstance(cmd_rep, argparse.Namespace):
            if vars(self._ns).keys() != vars(cmd_rep).keys():
                raise TypeError(type(cmd_rep))

        self._update_kwargs(**self._to_dict(cmd_rep))

    # various constructoion methods
    @classmethod
    def from_kwargs(cls, **kwargs):
        """
        Enforce argument specification by keyword arguments (**) only for all arguments.
        Arguments are identified and indexed with their associated key from keyword arguments (**).
        """
        return cls(kwargs)

    @classmethod
    def from_posargs_optkwargs(cls, *args, **kwargs):
        """
        Enforce argument specification by:
            1) positional arguments (*) for positional arguments
            2) keyword arguments (**) for optional arguments
        only.

        Positional arguments are indexed with their associated index in positionoal args (*)
        and optional arguments are indexed with their associated key from keyword arguments (**).
        """
        extras = cmd_ex.UnknownArguments(*list(args[len(cls.CMD_HELPER.posarg_list):]))
        kwargs.update({k: v for k, v in zip(cls.CMD_HELPER.posarg_list, args)})

        try:
            cls.validate(**kwargs)
        except cmd_ex.UnknownArguments as ex_unknown:
            extras.update(ex_unknown).raise_on_true()
        except cmd_ex.InvalidArguments:
            extras.raise_on_true()
            raise
        else:
            extras.raise_on_true()

        return cls(*args, **kwargs)

    # Conversion/parsing methods
    @classmethod
    def _list_2_ns(cls, cmd_list):
        cmd_ns = cls.CMD_HELPER.parse_args(cmd_list)
        return cmd_ns

    @classmethod
    def list_2_cmd(cls, cmd_list):
        return cls(cls._list_2_ns(cmd_list))

    @classmethod
    def _str_2_ns(cls, cmd_str):
        _cmd_list = cmd_str.split()
        cmd_ns = cls.CMD_HELPER.parse_args(_cmd_list)
        return cmd_ns

    @classmethod
    def str_2_cmd(cls, cmd_str):
        return cls(cls._str_2_ns(cmd_str))

    # Conversion/building methods
    @classmethod
    def _ns_2_list(cls, cmd_ns, **kwargs):
        cmd_list = None
        with suppress(cmd_ex.CmdArgsException):
            cmd_args = cls.CMD_HELPER.get_set_args(cmd_ns, **kwargs)
            cmd_list = cls.CMD_HELPER.build_cmd_list(**cmd_args)
        return cmd_list

    @classmethod
    def cmd_2_list(cls, cmd):
        return cls._ns_2_list(cmd._ns)

    @classmethod
    def _ns_2_str(cls, cmd_ns):
        cmd_list = cls._ns_2_list(cmd_ns)
        return ' '.join(cmd_list)

    @classmethod
    def cmd_2_str(cls, cmd):
        return cls._ns_2_str(cmd._ns)  # pylint: disable=protected-access

    def to_args_list(self):
        return self._ns_2_list(self._ns,
                               args_bl=self.CMD_HELPER.args_blacklist,
                               args_wl=self.CMD_HELPER.args_whitelist)

    @classmethod
    def _to_dict(cls, cmd_rep):
        if isinstance(cmd_rep, (Command, argparse.Namespace, dict)):
            if isinstance(cmd_rep, dict):
                cls._validate_kwargs(**cmd_rep)
            return cls.CMD_HELPER.get_set_args(cmd_rep)

        if isinstance(cmd_rep, list):
            return cls.CMD_HELPER.get_set_args(cls._list_2_ns(cmd_rep))
        if isinstance(cmd_rep, str):
            return cls.CMD_HELPER.get_set_args(cls._str_2_ns(cmd_rep))

        raise TypeError(cmd_rep)

    def to_dict(self):
        return self._to_dict(self)

    # Auxilliary
    def __str__(self):
        return self._ns_2_str(self._ns)

    def __repr__(self):
        return "%s:%r" % (type(self), self._ns)

    def __bool__(self):
        return self._ns != self.CMD_HELPER.default_image

    # def __bool__(self):
    #     return self.__nonzero__()

    # Container methods
    def __iter__(self):
        return self.get_set_args().__iter__()

    def __len__(self):
        return self.get_set_args().__len__()

    def __contains__(self, item):
        with suppress(cmd_ex.ArgumentsNotSet):
            self.__getitem__(item)
            return True
        return False

    def __getitem__(self, item):
        # self._validate_kwargs(**{item: None})
        try:
            val = getattr(self._ns, item)
        except AttributeError:
            raise cmd_ex.UnknownArguments(item)
        else:
            default = getattr(self.CMD_HELPER.default_image, item)
            if val == default:
                raise cmd_ex.ArgumentsNotSet(item)
        return val

    def __setitem__(self, item, value):
        # self._update_kwargs(**{item: value})
        try:
            getattr(self._ns, item)
        except AttributeError:
            raise cmd_ex.UnknownArguments(item)
        else:
            self.__init__(**{item: value})

    def __delitem__(self, item):
        self.__getitem__(item)
        default = getattr(self.CMD_HELPER.default_image, item)
        self._ns.__init__(**{item: default})

    def get(self, item, default=None):
        try:
            return self.__getitem__(item)
        except cmd_ex.ArgumentsNotSet:
            return default

    def pop(self, item, default=_LOCAL_DEFAULT):
        try:
            val = self.__getitem__(item)
        except cmd_ex.ArgumentsNotSet:
            if default is _LOCAL_DEFAULT:
                raise
            return default
        else:
            self.__delitem__(item)
            return val

    def clear(self):
        if bool(self):
            self._ns = copy.copy(self.CMD_HELPER.default_image)

    def keys(self):
        return self.get_set_args().keys()

    def values(self):
        return self.get_set_args().values()

    def items(self):
        return self.get_set_args().items()

    # Command arithmetics
    @classmethod
    def merge(cls, cmd_lhs, cmd_rhs):
        # we have to merge dicts before we check defaults with get_set_args()
        return cls(cmd_lhs, cmd_rhs)

    def update(self, *args, **kwargs):
        """Add new stuff and update existing

        cmd{a: 1, b: 2, c:3} + (cmd{b: 'b', c: 'c', d: 'd'}) => cmd{a: 1, b: 'b', c: 'c', d: 'd'}

        """
        for cmd in itertools.chain(args, [kwargs]):
            self._update_kwargs(**self._to_dict(cmd))

        return self

    def extend(self, *args, **kwargs):
        """Add new stuff only

        cmd{a: 1, b: 2, c:3} + (cmd{b: 'b', c: 'c', d: 'd'}) => cmd{a: 1, b: 2, c: 3, d: 'd'}

        """
        for cmd in itertools.chain(args, [kwargs]):
            self._extend_kwargs(**self._to_dict(cmd))

        return self

    def unset(self, *args, **kwargs):
        """Remove stuff

        cmd{a: 1, b: 2, c: 3} - {cmd{b: 'b', c: 'c', d: 'd'} => cmd{a: 1}

        """
        for cmd in itertools.chain(args, [kwargs]):
            self._unset_cmd(cmd)

        return self

    def _unset_cmd(self, cmd_rep):
        # unsetting neednt comply the "set" arguments only idiom for dicts, will unset all keys
        if isinstance(cmd_rep, dict):
            self._validate_kwargs(**cmd_rep)
            self._unset_kwargs(**cmd_rep)
        else:
            _cmd_dict = self._to_dict(cmd_rep)
            self._unset_kwargs(**_cmd_dict)

    def __eq__(self, other):
        if isinstance(other, Command):
            return (isinstance(other, self.__class__) or isinstance(self, other.__class__))\
                and self._ns == other._ns
        elif isinstance(other, argparse.Namespace):
            return self._ns == other
        elif isinstance(other, dict):
            return self.get_set_args() == other
        elif isinstance(other, list):
            return self._ns == self._list_2_ns(other)
        elif isinstance(other, str):
            return self._ns == self._str_2_ns(other)

        return False

    # Command utilities
    def get_set_args(self, **kwargs):
        if kwargs:
            return self.CMD_HELPER.get_set_args(kwargs)

        return self.CMD_HELPER.get_set_args(self._ns)

    def check_args(self, **kwargs):
        if not kwargs:
            kwargs = self.CMD_HELPER.get_set_args(self)

        return self.CMD_HELPER.check_args(**kwargs)
