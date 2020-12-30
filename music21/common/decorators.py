# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/decorators.py
# Purpose:      Decorators for functions
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import warnings

from functools import wraps

from music21 import exceptions21

__all__ = ['optional_arg_decorator', 'deprecated', 'cacheMethod']

# from Ryne Everett
# http://stackoverflow.com/questions/3888158/python-making-decorators-with-optional-arguments


def optional_arg_decorator(fn):
    '''
    a decorator for decorators.  Allows them to either have or not have arguments.
    '''
    @wraps(fn)
    def wrapped_decorator(*args, **kwargs):
        is_bound_method = hasattr(args[0], fn.__name__) if args else False
        klass = None

        if is_bound_method:
            klass = args[0]
            args = args[1:]

        # If no arguments were passed...
        if len(args) == 1 and not kwargs and callable(args[0]):
            if is_bound_method:
                return fn(klass, args[0])
            else:
                return fn(args[0])

        else:
            def real_decorator(toBeDecorated):
                if is_bound_method:
                    return fn(klass, toBeDecorated, *args, **kwargs)
                else:
                    return fn(toBeDecorated, *args, **kwargs)
            return real_decorator
    return wrapped_decorator


@optional_arg_decorator
def deprecated(method, startDate=None, removeDate=None, message=None):
    '''
    Decorator that marks a function as deprecated and should not be called.

    Because we're all developers, it does not use DeprecationWarning, which no
    one would ever see, but UserWarning.

    Warns once per session and never again.

    Use without arguments for a simple case:


    For demonstrating I need to screw with stderr...

    >>> import sys
    >>> saveStdErr = sys.stderr
    >>> sys.stderr = sys.stdout

    >>> @common.deprecated
    ... def hi(msg):
    ...     print(msg)

    (I'm printing "/" at the beginning because message begins with the filename and that is
    different on each system, but you can't use ellipses at the beginning of a doctest)

    >>> print('/'); hi('myke')
    /...Music21DeprecationWarning: hi was deprecated
            and will disappear soon. Find alternative methods.
    ...
     myke

    A second call raises no warning:

    >>> hi('myke')
    myke


    Now a new function demonstrating the argument form.

    >>> @common.deprecated('February 1972', 'September 2099', 'You should be okay...')
    ... def bye(msg):
    ...     print(msg)

    >>> print('/'); bye('world')
    /...Music21DeprecationWarning: bye was deprecated on February 1972
            and will disappear at or after September 2099. You should be okay...
    ...
    world

    Restore stderr at the end.

    >>> sys.stderr = saveStdErr

    '''
    if hasattr(method, '__qualname__'):
        funcName = method.__qualname__
    else:
        funcName = method.__name__

    if startDate is not None:
        startDate = ' on ' + startDate
    else:
        startDate = ''

    if removeDate is not None:
        removeDate = 'at or after ' + removeDate
    else:
        removeDate = 'soon'

    if message is None:
        message = 'Find alternative methods.'

    m = f'{funcName} was deprecated{startDate} and will disappear {removeDate}. {message}'
    callInfo = {'calledAlready': False,
                'message': m}

    @wraps(method)
    def func_wrapper(*args, **kwargs):
        # TODO: look at sys.warnstatus.
        if callInfo['calledAlready'] is False:
            warnings.warn(callInfo['message'],
                          exceptions21.Music21DeprecationWarning,
                          stacklevel=2)
            callInfo['calledAlready'] = True
        return method(*args, **kwargs)

    return func_wrapper


def cacheMethod(method):
    '''
    A decorator for music21Objects or other objects that
    assumes that there is a ._cache Dictionary in the instance
    and returns or sets that value if it exists, otherwise calls the method
    and stores the value.

    To be used ONLY with zero-arg calls.  Like properties.  Well, can be
    used by others but will not store per-value caches.

    Not a generic memorize, because by storing in one ._cache place,
    a .clearCache() method can eliminate them.

    Uses the name of the function as the cache key.

    New in v.6 -- helps to make all the caches easier to work with.
    '''
    if hasattr(method, '__qualname__'):
        funcName = method.__qualname__
    else:
        funcName = method.__name__

    @wraps(method)
    def inner(instance, *args, **kwargs):
        if funcName in instance._cache:
            return instance._cache[funcName]

        instance._cache[funcName] = method(instance, *args, **kwargs)
        return instance._cache[funcName]

    return inner


if __name__ == '__main__':
    import music21  # @Reimport
    music21.mainTest()
