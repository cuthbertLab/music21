# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 John Paulett (john -at- paulett.org)
# Copyright (C) 2009, 2011, 2013 David Aguilar (davvid -at- gmail.com)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

"""Python library for serializing any arbitrary object graph into JSON.

jsonpickle can take almost any Python object and turn the object into JSON.
Additionally, it can reconstitute the object back into Python.

The object must be accessible globally via a module and must
inherit from object (AKA new-style classes).

Create an object.

    >>> from jsonpickle._samples import Thing
    >>> obj = Thing('A String')
    >>> obj.name
    'A String'

Use jsonpickle to transform the object into a JSON string.

    >>> import jsonpickle
    >>> pickled = jsonpickle.encode(obj)

Use jsonpickle to recreate a Python object from a JSON string

    >>> unpickled = jsonpickle.decode(pickled)
    >>> print(unpickled.name)
    A String

.. warning::

    Loading a JSON string from an untrusted source represents a potential
    security vulnerability.  jsonpickle makes no attempt to sanitize the input.

The new object has the same type and data, but essentially is now a copy of
the original.

    >>> obj is unpickled
    False
    >>> obj.name == unpickled.name
    True
    >>> type(obj) == type(unpickled)
    True

If you will never need to load (regenerate the Python class from JSON), you can
pass in the keyword unpicklable=False to prevent extra information from being
added to JSON.

    >>> oneway = jsonpickle.encode(obj, unpicklable=False)
    >>> result = jsonpickle.decode(oneway)
    >>> print(result['name'])
    A String

    >>> print(result['child'])
    None


"""
import sys, os
from music21 import common
sys.path.append(common.getSourceFilePath() + os.path.sep + 'ext')

from jsonpickle import pickler # @UnresolvedImport
from jsonpickle import unpickler # @UnresolvedImport
from jsonpickle.backend import JSONBackend # @UnresolvedImport
from jsonpickle.version import VERSION  # @UnresolvedImport

# ensure built-in handlers are loaded
__import__('jsonpickle.handlers')

__all__ = ('encode', 'decode')
__version__ = VERSION

json = JSONBackend()

# Export specific JSONPluginMgr methods into the jsonpickle namespace
set_preferred_backend = json.set_preferred_backend
set_encoder_options = json.set_encoder_options
load_backend = json.load_backend
remove_backend = json.remove_backend
enable_fallthrough = json.enable_fallthrough


def encode(value,
           unpicklable=True, make_refs=True, keys=False,
           max_depth=None, backend=None):
    """
    Return a JSON formatted representation of value, a Python object.

    The keyword argument 'unpicklable' defaults to True.
    If set to False, the output will not contain the information
    necessary to turn the JSON data back into Python objects.

    The keyword argument 'max_depth' defaults to None.
    If set to a non-negative integer then jsonpickle will not recurse
    deeper than 'max_depth' steps into the object.  Anything deeper
    than 'max_depth' is represented using a Python repr() of the object.

    The keyword argument 'make_refs' defaults to True.
    If set to False jsonpickle's referencing support is disabled.
    Objects that are id()-identical won't be preserved across
    encode()/decode(), but the resulting JSON stream will be conceptually
    simpler.  jsonpickle detects cyclical objects and will break the
    cycle by calling repr() instead of recursing when make_refs is set False.
    
    MSC: if make_refs is None then continues until max_depth is reached.

    The keyword argument 'keys' defaults to False.
    If set to True then jsonpickle will encode non-string dictionary keys
    instead of coercing them into strings via `repr()`.

    >>> encode('my string')
    '"my string"'
    >>> encode(36)
    '36'

    >>> encode({'foo': True})
    '{"foo": true}'

    >>> encode({'foo': True}, max_depth=0)
    '"{\\'foo\\': True}"'

    >>> encode({'foo': True}, max_depth=1)
    '{"foo": "True"}'


    """
    if backend is None:
        backend = json
    return pickler.encode(value,
                          backend=backend,
                          unpicklable=unpicklable,
                          make_refs=make_refs,
                          keys=keys,
                          max_depth=max_depth)


def decode(string, backend=None, keys=False):
    """
    Convert a JSON string into a Python object.

    The keyword argument 'keys' defaults to False.
    If set to True then jsonpickle will decode non-string dictionary keys
    into python objects via the jsonpickle protocol.

    >>> str(decode('"my string"'))
    'my string'
    >>> decode('36')
    36
    """
    if backend is None:
        backend = json
    return unpickler.decode(string, backend=backend, keys=keys)
