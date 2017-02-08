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
import itertools

from contextlib import suppress
from abc import abstractmethod, abstractproperty
from collections import Iterable, Iterator


class CondLoopException(Exception):
    pass


class StopIterationCounter(StopIteration):
    pass


class StopIterationTimeout(StopIteration):
    pass


class IBase(Iterator):
    """
    """
    EX_STOP_ITERATION = StopIteration

    def __init__(self, iterable=None, stop_iteration=None):
        super().__init__()
        if iterable:
            self._iterable = iterable

        if not stop_iteration:
            stop_iteration = self.EX_STOP_ITERATION
        self.stop_iteration = stop_iteration

    def __iter__(self):
        return self

    def __next__(self):
        return self._iterable.__next__()


class IGeneric(IBase):
    """
    """
    def __init__(self, stop_iteration=None):
        super().__init__(stop_iteration=stop_iteration)

    @abstractmethod
    def next_iter(self):
        raise self.stop_iteration()

    def __next__(self):
        with suppress(AttributeError):
            return super().__next__()
        self._iterable = self.next_iter()
        return super().__next__()


class IInterval(IGeneric):
    """
    """
    KEYWORD = 'interval'

    def __init__(self, interval):
        super().__init__()
        self._interval = interval

    @property
    def interval(self):
        return self._interval

    def next_iter(self):
        while True:
            yield self
            time.sleep(self.interval)


class ITimeout(IGeneric):
    """
    """
    KEYWORD = 'timeout'
    EX_STOP_ITERATION = StopIterationTimeout

    def __init__(self, timeout):
        super().__init__()
        self._timeout = timeout

    @property
    def start_time(self):
        with suppress(AttributeError):
            return self._start_time
        self.reset_start_time()
        return self._start_time

    def reset_start_time(self):
        self._start_time = int(time.time())

    @property
    def timeout(self):
        return self._timeout

    @property
    def end_time(self):
        return self.start_time + self.timeout

    def next_iter(self):
        while int(time.time()) < self.end_time:
            yield self
        raise self.stop_iteration(self.timeout)


class ICounter(IGeneric):
    """
    """
    KEYWORD = 'counter'
    EX_STOP_ITERATION = StopIterationCounter

    def __init__(self, count):
        super().__init__()
        self._count = count

    @property
    def start_count(self):
        with suppress(AttributeError):
            return self._start_count
        self._reset_start_count()
        return self._start_count

    def _reset_start_count(self, start_from=0):
        self._start_count = start_from

    @property
    def end_count(self):
        return self.start_count + self.count

    @property
    def count(self):
        return self._count

    def next_iter(self):
        for i in range(self.start_count, self.end_count):
            yield self
        raise self.stop_iteration(i)


# example
"""
GenericLoop(
    takewhile(
        predicate,
        enumerate(
            zip(
                IInterval(5),
                ITimeout(60),
                ICounter(10),
                IBase(...),
                iter(.., ...),
            )
        )
    )
)
"""


class GenericLoopBase(IGeneric):
    """
    A generic `loop` is of the form:
        GenericLoop(acceptor(predicate, enumerator))
    Itself an IBase
    """
    def __init__(self, acceptor=None, predicate=None):
        super().__init__()

        self._acceptor = acceptor
        self._predicate = predicate

    def next_iter(self):
        return self.acceptor(self.predicate, self.enumerator)

    @property
    def acceptor(self):
        return self._acceptor

    @acceptor.setter
    def acceptor(self, value):
        self._acceptor = value

    @property
    def predicate(self):
        return self._predicate

    @predicate.setter
    def predicate(self, value):
        self._predicate = value

    @abstractproperty
    def enumerator(self):
        return self._enumerator


# predicates
def P1st_Any_False(terms):
    with suppress(StopIteration):
        next(itertools.filterfalse(bool, terms[1]))
        return True
    return False


def PAll_Any_False(terms):
    return bool(list(itertools.filterfalse(bool, terms[1])))


def P1st_Any_True(terms):
    return bool(next(filter(bool, terms[1]), False))


def PAll_Any_True(terms):
    return bool(list(filter(bool, terms[1])))


class GenericLoop(GenericLoopBase):
    """
    """
    ENUMERATE = enumerate
    ZIP = zip

    @classmethod
    def PREDICATE(cls, results_tuple):
        i, results = results_tuple
        return bool(next(itertools.filterfalse(bool, results), True))

    @classmethod
    def from_iterables(cls, *iterables, **kwargs):
        return cls(iterables, **kwargs)

    def __init__(self, iterables,
                 acceptor=None, predicate=None,
                 enumerator=None, zipper=None):
        """
        """
        self._iterables = iterables

        if not acceptor:
            acceptor = self.ACCEPTOR
        if not predicate:
            predicate = self.PREDICATE

        super().__init__(acceptor=acceptor, predicate=predicate)

        if not enumerator:
            enumerator = self.ENUMERATE
        self._enumerator = enumerator

        if not zipper:
            zipper = self.ZIP
        self._zipper = zipper

    @property
    def iterables(self):
        return self._iterables

    @property
    def enumerator(self):
        return self._enumerator(self._zipper(*self.iterables))

    def append(self, *iterables):
        self._iterables = itertools.chain(self._iterables, iterables)

    def prepend(self, *iterables):
        self._iterables = itertools.chain(iterables, self._iterables)


class GenericWhile(GenericLoop):
    ACCEPTOR = itertools.takewhile


class GenericUntil(GenericLoop):
    ACCEPTOR = itertools.dropwhile
