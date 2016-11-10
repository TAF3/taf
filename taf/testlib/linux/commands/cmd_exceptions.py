#! /usr/bin/env python
"""
@copyright Copyright (c) 2011 - 2017, Intel Corporation.

This program is free software; you can redistribute it and/or modify it
under the terms and conditions of the GNU Lesser General Public License,
version 2.1, as published by the Free Software Foundation.

This program is distributed in the hope it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
more details.

@file  cmd_exceptions.py

@summary  Command helpers exception handling.
"""

import itertools

from contextlib import suppress, contextmanager
from collections import OrderedDict, Iterable, Iterator


def binary_op_dummy(lhs, rhs):
    pass


def binary_op_none(lhs, rhs):
    return None


def binary_op_identity_lhs(lhs, rhs):
    return lhs


def binary_op_identity_rhs(lhs, rhs):
    return rhs


def binary_op_gen(op):
    def binary_f(lhs, rhs):
        return op(lhs, rhs)
    return binary_f

def binary_op_update(lhs, rhs):
   lhs.update(rhs)
   return lhs


def reduce_with_exception(iterable, op_reduce_ex=binary_op_identity_lhs, exc_types=(),
                          noraise=False, rargs=None, rkwargs=None):
    """
    Execute a number of routines under a unified exception handling combining and reducing
    possibly multiple exceptions into a single one (of the specified type), to be re-raised
    once the routine has finished, as if it was a single routine, try/except block, exception.
    The implementation takes advantage of the fact that when an exception is thrown
    (the first of many), it can be reused (and even built upon) and re-raised
    at the end of the function, as opposed to not raising anything otherwise - which eliminates
    the need to check for emptiness, whether there is something to raise or not.
    """
    if isinstance(iterable, Iterable):
        iterable = iter(iterable)
    if not isinstance(iterable, Iterator):
        raise TypeError("Not an iterator")

    if not rargs:
        rargs = []
    if not rkwargs:
        rkwargs = {}

    def routine(r):
        return r(*rargs, **rkwargs)

    try:
        list(map(routine, iterable))
    except exc_types as ex1:
        def new_routine(r):
            try:
                routine(r)
            except exc_types as ex2:
                nonlocal ex1  # noqa ignore: SyntaxError
                ex1 = op_reduce_ex(ex1, ex2)

        list(map(new_routine, iterable))

        if noraise:
            return ex1
        raise ex1

    return None


class CmdArgsException(Exception):
    """
    @description  Base class to handle command arguments exceptions
    """
    BOILERPLATE = 'CmdArgsException({0}): [{1}]'
    JOIN_STR = ', '
    ARG_BOILERPLATE = "('{0}')"
    KWARG_BOILERPLATE = "({0[0]!r}={0[1]!r})"

    @classmethod
    def _to_alist(cls, args_rep):
        if not args_rep:
            return []

        if isinstance(args_rep, cls):
            return args_rep._args
        elif isinstance(args_rep, list):
            return args_rep
        elif isinstance(args_rep, dict):
            return []
        else:
            raise TypeError("{0}({1})".format(type(args_rep), args_rep))

    @classmethod
    def to_alist(cls, *args):
        if not args:
            args = []

        list_iter = (cls._to_alist(a) for a in args)
        return itertools.chain.from_iterable(list_iter)

    @classmethod
    def _to_kwdict(cls, args_rep):
        if not args_rep:
            return {}

        if isinstance(args_rep, cls):
            return args_rep._kwargs
        elif isinstance(args_rep, dict):
            return args_rep
        elif isinstance(args_rep, list):
            return {}
        else:
            raise TypeError("{0}({1})".format(type(args_rep), args_rep))

    @classmethod
    def to_kwdict(cls, *args, **kwargs):
        if not args:
            args = []
        if not kwargs:
            kwargs = {}

        dict_iter = (cls._to_kwdict(a).items() for a in itertools.chain(args, (kwargs, )))
        return itertools.chain.from_iterable(dict_iter)

    @classmethod
    def _cls_raise_on_true(cls, *args, **kwargs):
        raisers = (
            lambda: cls._cls_raise_on_true_args(*args),
            lambda: cls._cls_raise_on_true_kwargs(*args, **kwargs),
        )
        return reduce_with_exception(raisers,
                                     op_reduce_ex=lambda x, y: x.update(y),
                                     exc_types=(cls,))

    @classmethod
    def _cls_raise_on_true_args(cls, *args):
        _list = OrderedDict.fromkeys(cls.to_alist(*args))
        if _list:
            raise cls(*_list)

    @classmethod
    def _cls_raise_on_true_kwargs(cls, *args, **kwargs):
        _dict = dict(cls.to_kwdict(*args, **kwargs))
        if _dict:
            raise cls(**_dict)

    def _self_raise_on_true(self):
        self._cls_raise_on_true(list(self._args.keys()), **self._kwargs)

    def _self_raise_on_true_args(self):
        self._cls_raise_on_true_args(list(self._args.keys()))

    def _self_raise_on_true_kwargs(self):
        self._cls_raise_on_true_kwargs(*self._args, **self._kwargs)

    raise_on_true = _cls_raise_on_true
    raise_on_true_lists = _cls_raise_on_true_args
    raise_on_true_dicts = _cls_raise_on_true_kwargs

    def __init__(self, *args, **kwargs):
        super(CmdArgsException, self).__init__()
        self._args = OrderedDict.fromkeys(args)
        self._kwargs = kwargs

        self.raise_on_true = self._self_raise_on_true
        self.raise_on_true_lists = self._self_raise_on_true_args
        self.raise_on_true_dicts = self._self_raise_on_true_kwargs

    def extend_args(self, *args):
        a_extend_iter = (a for a in self.to_alist(*args) if a not in self._args)
        a_extend = OrderedDict.fromkeys(a_extend_iter)
        self._args.update(a_extend)
        return self

    def extend(self, *args, **kwargs):
        self.extend_args(*args)
        self.extend_kwargs(*args, **kwargs)
        return self

    def update(self, *args, **kwargs):
        self.update_args(*args)
        self.update_kwargs(*args, **kwargs)
        return self

    def update_args(self, *args):
        a_update = OrderedDict.fromkeys(self.to_alist(*args))
        self._args.update(a_update)
        return self

    def extend_kwargs(self, *args, **kwargs):
        _tmp = dict(self.to_kwdict(*args, **kwargs))
        _tmp.update(self._kwargs)
        self._kwargs = _tmp
        return self

    def update_kwargs(self, *args, **kwargs):
        self._kwargs.update(self.to_kwdict(*args, **kwargs))
        return self

    def _format_args(self, bp=None, a_bp=None, kw_bp=None, join_str=None):
        if not bp:
            bp = self.BOILERPLATE
        if not a_bp:
            a_bp = self.ARG_BOILERPLATE
        if not kw_bp:
            kw_bp = self.KWARG_BOILERPLATE
        if not join_str:
            join_str = self.JOIN_STR

        total = len(self._args) + len(self._kwargs)
        arg_iter = (a_bp.format(arg) for arg in self._args)
        kwarg_iter = (kw_bp.format(kv_pair) for kv_pair in self._kwargs.items())
        return bp.format(total, join_str.join(itertools.chain(arg_iter, kwarg_iter)))

    def is_nonempty(self):
        return bool(self._args or self._kwargs)

    __nonzero__ = __bool__ = is_nonempty

    def __str__(self):
        return self._format_args()

    __repr__ = __str__


class UnknownArguments(CmdArgsException):
    BOILERPLATE = "Unknown arguments({0}): [{1}]"


class ArgumentsNotSet(CmdArgsException):
    BOILERPLATE = "Arguments({0}): [{1}] have not been set"

    def __init__(self, *args):
        super(ArgumentsNotSet, self).__init__(*args)


class InvalidArguments(CmdArgsException):
    BOILERPLATE = "Arguments({0}): [{1}] have got invalid values"


class ArgumentsCollision(InvalidArguments):
    BOILERPLATE = "Arguments({0}): [{1}] collide"
