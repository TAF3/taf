"""
@copyright Copyright (c) 2017, Intel Corporation.

This program is free software; you can redistribute it and/or modify it
under the terms and conditions of the GNU Lesser General Public License,
version 2.1, as published by the Free Software Foundation.

This program is distributed in the hope it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
more details.

@file  logic.py

@summary  combinational, resolution, functional, predicate and other logics helpers.
"""

import itertools
import functools


__0__ = object()


class Functional(object):
    """
    """
    @classmethod
    def fixed(cls, value):
        def wrapper(arg):
            return value
        return wrapper

    @classmethod
    def mapped(cls, mapper):
        def wrapper(arg):
            return mapper(arg)
        return wrapper

    @classmethod
    def f2i(sentinel=object()):
        """
        function to iter decorator
        """
        def decorator(f):
            return iter(f, sentinel)
        return decorator

    @classmethod
    def fwrap(cls, wraps=__0__, returns=__0__, args=__0__, kwargs=__0__):
        """
        function wrapper
        """
        def decorator(f):
            """
            TODO Propagate the signature as originally declared for `f`?
            inspect.signature(f) ...  ???
            """
            @functools.wraps(f if wraps is __0__ else wraps)
            def wrapper(*f_args, **f_kwargs):
                if args is not __0__:
                    f_args = args(*f_args)
                if kwargs is not __0__:
                    f_kwargs = kwargs(**f_kwargs)

                ret = f(*f_args, **f_kwargs)

                if returns is __0__:
                    return ret
                return returns(ret)

            return wrapper
        return decorator

    @classmethod
    def ifwrap(cls, sentinel=__0__):
        """
        iterator [function] wrapper
        Just like the builtin `iter`, only with a customizable sentinel predicate
        """
        if sentinel is __0__:
            def wrapper(obj):
                return iter(obj)
            return wrapper

        predicate = Predicate.pwrap_bool_false(sentinel)

        def wrapper(obj):
            return itertools.takewhile(predicate, Functional.f2i()(obj))
        return wrapper


class Predicate(object):
    """
    """
    DEFAULT_PREDICATE = bool

    @classmethod
    def pwrap(cls, wraps=__0__, predicate=__0__, on_true=__0__, on_false=__0__):
        """
        predicate wrapper
        """
        if predicate is __0__:
            predicate = cls.DEFAULT_PREDICATE

        def mapper(mappee):
            ret = on_false
            if predicate(mappee):
                ret = on_true
            if ret is __0__:
                return mappee
            return ret

        return Functional.fwrap(wraps=wraps, returns=Functional.mapped(mapper))

    __PWRAP_IMPL_MAP__ = {}

    @classmethod
    def class_init(cls):
        cls.pwrap_bool_true = cls.pwrap(on_true=True, on_false=False)
        cls.pwrap_bool_false = cls.pwrap(on_true=False, on_false=True)
        cls.pwrap_object_true = cls.pwrap(on_false=None)
        cls.pwrap_object_false = cls.pwrap(on_true=None)

        cls.__PWRAP_IMPL_MAP__.update(
            {
                bool: [cls.pwrap_bool_false, cls.pwrap_bool_true],
                object: [cls.pwrap_object_false, cls.pwrap_object_true],
            }
        )


Predicate.class_init()
