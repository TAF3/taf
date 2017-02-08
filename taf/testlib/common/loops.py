"""
@copyright Copyright (c) 2017, Intel Corporation.

This program is free software; you can redistribute it and/or modify it
under the terms and conditions of the GNU Lesser General Public License,
version 2.1, as published by the Free Software Foundation.

This program is distributed in the hope it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
more details.

@file  loops.py

@summary  flexible and extensible conditional loops helpers.
"""

import time
from contextlib import suppress
from collections import OrderedDict


class CondLoopException(Exception):
    pass


class CondLoopBase(object):
    """
    """
    END_FAIL = False
    END_SUCCESS = True
    KEEP_LOOPING = None

    def __init__(self, end_fail=False, end_success=True, keep_looping=None):
        super(CondLoopBase, self).__init__()

        self.END_FAIL = end_fail
        self.END_SUCCESS = end_success
        self.KEEP_LOOPING = keep_looping

        self.end_conds_fail = []
        self.end_conds_succ = []
        self.gen_iter = None
        self.loops_counter = 0

    def end_conditions_met(self):
        """
        Override this method. Expected behavior upon returns from this method:
            True/False - terminate with success/failure
            None - keep looping
        """
        raise NotImplementedError

    def loops_gen(self):
        res = self.end_conditions_met()
        while res is self.KEEP_LOOPING:
            yield res
            res = self.end_conditions_met()
        yield res

    def add_fail_condition(self, cond):
        self.end_conds_fail.append(cond)

    def add_success_condition(self, cond):
        self.end_conds_succ.append(cond)


class CondLoopImpl(CondLoopBase):
    """
    """
    OPTIONS = OrderedDict()

    @classmethod
    def register_option(cls, option=None):
        """
        Register a keyword option for the class in `cls`
        """
        if not option:
            option = cls.OPTION
        if option in cls.OPTIONS:
            raise CondLoopException("Conflict at '{}'".format(option))
        cls.OPTIONS[option] = cls

    def __init__(self):
        """
        @brief   Loop a routine over until it has passed or until an end condition has been met
        """
        super(CondLoopImpl, self).__init__()
        self.gen_iter = self.loops_gen()
        self.last_loop_res = None

    def _before_next(self):
        pass

    def _after_next(self):
        if self.last_loop_res is None:
            self.loops_counter += 1

    def __next__(self):
        self._before_next()
        self.last_loop_res = next(self.gen_iter)
        self._after_next()
        return self.last_loop_res

    def __iter__(self):
        return self

    def __call__(self, *args, **kwargs):
        return self.run(*args)

    def run(self, *conds):
        self.end_conds_succ.extend(conds)
        return self._run()

    def _run(self):
        status = self.KEEP_LOOPING
        while status is self.KEEP_LOOPING:
            try:
                status = self.__next__()
            except StopIteration:
                break

        return status


class CondLoopInterval(CondLoopImpl):
    """
    @brief:  Add an interval to wait before proceeding with the next loop
    """
    OPTION = 'interval'

    @classmethod
    def add_interval(cls, cloop, interval, *args, **kwargs):
        cloop._interval = interval

        def f():
            if cloop.loops_counter:
                do_sleep = True
                with suppress(AttributeError):
                    do_sleep = cloop.loops_counter < cloop._count_max
                if do_sleep:
                    time.sleep(cloop._interval)

        cloop._before_next = f

    add = add_interval

    def __init__(self, interval):
        super(CondLoopInterval, self).__init__()
        self.add_interval(self, interval)

    @property
    def interval(self):
        return self._interval


class CondLoopCounter(CondLoopImpl):
    """
    @brief:  Add a loop counter end condition that fails after the amount of loops is reached.
    """
    OPTION = 'counter'

    @classmethod
    def add_counter(cls, cloop, count, *args, **kwargs):
        cloop._count_max = count

        def end_cond():
            if not(cloop.loops_counter < cloop._count_max):
                return True
            return False

        cloop.end_conds_fail.append(end_cond)

    add = add_counter

    def __init__(self, count):
        super(CondLoopCounter, self).__init__()
        self.add_counter(self, count)

    @property
    def count_max(self):
        return self._count_max


class CondLoopTimeout(CondLoopImpl):
    """
    @brief:  Add a timeout end condition that fails after the deadline has been reached.
    """
    OPTION = 'timeout'

    @classmethod
    def add_timeout(cls, cloop, timeout, *args, **kwargs):
        cloop._start_time = int(time.time())
        cloop._deadline = cloop._start_time + timeout

        def end_cond():
            if not(int(time.time()) < cloop._deadline):
                return True
            return False

        cloop.end_conds_fail.append(end_cond)

    add = add_timeout

    def __init__(self, timeout):
        super(CondLoopTimeout, self).__init__()
        self.add_timeout(self, timeout)

    @property
    def start_time(self):
        return self._start_time

    @property
    def deadline(self):
        return self._deadline


class ConditionalLoop(CondLoopImpl):
    """
    public API
    """
    BP_UNREG_OPTIONS = "Unregistered options detected({0}): {1}"
    BP_UNREG_PAIR = "'{0}'='{1}'"

    def __init__(self, **kwargs):
        super(ConditionalLoop, self).__init__()

        for cl_option, cl_type in self.OPTIONS.items():
            with suppress(KeyError):
                cl_value = kwargs.pop(cl_option)
                cl_type.add(self, cl_value)

        if kwargs:
            raise CondLoopException(
                self.BP_UNREG_OPTIONS.format(
                    len(kwargs),
                    ', '.join(self.BP_UNREG_PAIR.format(k, v) for k, v in kwargs.items())))


# register default types automatically
DEFAULT_TYPES = [CondLoopInterval, CondLoopCounter, CondLoopTimeout]
for cl_type in DEFAULT_TYPES:
    cl_type.register_option()


# public helpers
class GenericLoop(ConditionalLoop):
    """
    Generic loop helper
    """
    @property
    def _fail_iter(self):
        return (True for cond in self.end_conds_fail if cond())

    @property
    def _succ_iter(self):
        return (True for cond in self.end_conds_succ if not cond())

    def _met_all(self):
        if list(self._fail_iter):
            return self.ON_FAIL_FALSE

        if list(self._succ_iter):
            return self.ON_SUCC_FALSE

        return self.ON_SUCC_TRUE

    def _met_one(self):
        if next(self._fail_iter, False):
            return self.ON_FAIL_FALSE

        if next(self._succ_iter, False):
            return self.ON_SUCC_FALSE

        return self.ON_SUCC_TRUE


class GenericWhile(GenericLoop):
    ON_FAIL_FALSE = GenericLoop.END_FAIL
    ON_SUCC_FALSE = GenericLoop.END_SUCCESS
    ON_SUCC_TRUE = GenericLoop.KEEP_LOOPING


class GenericUntil(GenericLoop):
    ON_FAIL_FALSE = GenericLoop.END_FAIL
    ON_SUCC_FALSE = GenericLoop.KEEP_LOOPING
    ON_SUCC_TRUE = GenericLoop.END_SUCCESS


class While(GenericWhile):
    end_conditions_met = GenericWhile._met_all


class Until(GenericUntil):
    end_conditions_met = GenericUntil._met_all


class LazyWhile(GenericWhile):
    end_conditions_met = GenericWhile._met_one


class LazyUntil(GenericUntil):
    end_conditions_met = GenericUntil._met_one
