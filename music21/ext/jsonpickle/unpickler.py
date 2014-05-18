# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 John Paulett (john -at- paulett.org)
# Copyright (C) 2009, 2011, 2013 David Aguilar (davvid -at- gmail.com)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import sys

import jsonpickle.util as util
import jsonpickle.tags as tags
import jsonpickle.handlers as handlers

from jsonpickle.compat import set
from jsonpickle.backend import JSONBackend


def decode(string, backend=None, context=None, keys=False, reset=True,
           safe=False):
    backend = _make_backend(backend)
    if context is None:
        context = Unpickler(keys=keys, backend=backend, safe=safe)
    return context.restore(backend.decode(string), reset=reset)


def _make_backend(backend):
    if backend is None:
        return JSONBackend()
    else:
        return backend

def _supports_getstate(obj, instance):
    return hasattr(instance, '__setstate__') and has_tag(obj, tags.STATE)


class Unpickler(object):

    def __init__(self, backend=None, keys=False, safe=False):
        ## The current recursion depth
        ## Maps reference names to object instances
        self.backend = _make_backend(backend)
        self.keys = keys
        self.safe = safe

        self._namedict = {}
        ## The namestack grows whenever we recurse into a child object
        self._namestack = []

        ## Maps objects to their index in the _objs list
        self._obj_to_idx = {}
        self._objs = []

    def reset(self):
        """Resets the object's internal state.
        """
        self._namedict = {}
        self._namestack = []
        self._obj_to_idx = {}
        self._objs = []

    def restore(self, obj, reset=True):
        """Restores a flattened object to its original python state.

        Simply returns any of the basic builtin types

        >>> u = Unpickler()
        >>> u.restore('hello world')
        'hello world'
        >>> u.restore({'key': 'value'})
        {'key': 'value'}
        """
        if reset:
            self.reset()
        return self._restore(obj)

    def _restore(self, obj):
        if has_tag(obj, tags.ID):
            restore = self._restore_id
        elif has_tag(obj, tags.REF): # Backwards compatibility
            restore = self._restore_ref
        elif has_tag(obj, tags.TYPE):
            restore = self._restore_type
        elif has_tag(obj, tags.REPR): # Backwards compatibility
            restore = self._restore_repr
        elif has_tag(obj, tags.OBJECT):
            restore = self._restore_object
        elif util.is_list(obj):
            restore = self._restore_list
        elif has_tag(obj, tags.TUPLE):
            restore = self._restore_tuple
        elif has_tag(obj, tags.SET):
            restore = self._restore_set
        elif util.is_dictionary(obj):
            restore = self._restore_dict
        else:
            restore = lambda x: x
        return restore(obj)

    def _restore_id(self, obj):
        return self._objs[obj[tags.ID]]

    def _restore_ref(self, obj):
        return self._namedict.get(obj[tags.REF])

    def _restore_type(self, obj):
        typeref = loadclass(obj[tags.TYPE])
        if typeref is None:
            return obj
        return typeref

    def _restore_repr(self, obj):
        if self.safe:
            # eval() is not allowed in safe mode
            return None
        obj = loadrepr(obj[tags.REPR])
        return self._mkref(obj)

    def _restore_object(self, obj):
        cls = loadclass(obj[tags.OBJECT])
        if cls is None:
            return self._mkref(obj)
        handler = handlers.get(cls)
        if handler is not None: # custom handler
            instance = handler(self).restore(obj)
            return self._mkref(instance)
        else:
            return self._restore_object_instance(obj, cls)

    def _restore_object_instance(self, obj, cls):
        factory = loadfactory(obj)
        args = getargs(obj)
        if args:
            args = self._restore(args)
        try:
            if hasattr(cls, '__new__'): # new style classes
                if factory:
                    instance = cls.__new__(cls, factory, *args)
                    instance.default_factory = factory
                else:
                    instance = cls.__new__(cls, *args)
            else:
                instance = object.__new__(cls)
        except TypeError: # old-style classes
            try:
                instance = cls()
            except TypeError: # fail gracefully
                return self._mkref(obj)

        self._mkref(instance) # allow references in downstream objects
        if isinstance(instance, tuple):
            return instance

        return self._restore_object_instance_variables(obj, instance)

    def _restore_object_instance_variables(self, obj, instance):
        for k, v in sorted(obj.items(), key=util.itemgetter):
            # ignore the reserved attribute
            if k in tags.RESERVED:
                continue
            self._namestack.append(k)
            # step into the namespace
            value = self._restore(v)
            if (util.is_noncomplex(instance) or
                    util.is_dictionary_subclass(instance)):
                instance[k] = value
            else:
                setattr(instance, k, value)
            # step out
            self._namestack.pop()

        # Handle list and set subclasses
        if has_tag(obj, tags.SEQ):
            if hasattr(instance, 'append'):
                for v in obj[tags.SEQ]:
                    instance.append(self._restore(v))
            if hasattr(instance, 'add'):
                for v in obj[tags.SEQ]:
                    instance.add(self._restore(v))

        if _supports_getstate(obj, instance):
            self._restore_state(obj, instance)

        return instance

    def _restore_state(self, obj, instance):
        state = self._restore(obj[tags.STATE])
        instance.__setstate__(state)
        return instance

    def _restore_list(self, obj):
        parent = []
        self._mkref(parent)
        children = [self._restore(v) for v in obj]
        parent.extend(children)
        return parent

    def _restore_tuple(self, obj):
        return tuple([self._restore(v) for v in obj[tags.TUPLE]])

    def _restore_set(self, obj):
        return set([self._restore(v) for v in obj[tags.SET]])

    def _restore_dict(self, obj):
        data = {}
        for k, v in sorted(obj.items(), key=util.itemgetter):
            self._namestack.append(k)
            if self.keys and k.startswith(tags.JSON_KEY):
                k = decode(k[len(tags.JSON_KEY):],
                           backend=self.backend, context=self,
                           keys=True, reset=False)
            data[k] = self._restore(v)
            self._namestack.pop()
        return data

    def _refname(self):
        """Calculates the name of the current location in the JSON stack.

        This is called as jsonpickle traverses the object structure to
        create references to previously-traversed objects.  This allows
        cyclical data structures such as doubly-linked lists.
        jsonpickle ensures that duplicate python references to the same
        object results in only a single JSON object definition and
        special reference tags to represent each reference.

        >>> u = Unpickler()
        >>> u._namestack = []
        >>> u._refname()
        '/'

        >>> u._namestack = ['a']
        >>> u._refname()
        '/a'

        >>> u._namestack = ['a', 'b']
        >>> u._refname()
        '/a/b'

        """
        return '/' + '/'.join(self._namestack)

    def _mkref(self, obj):
        """
        >>> from jsonpickle._samples import Thing
        >>> thing = Thing('referenced-thing')
        >>> u = Unpickler()
        >>> u._mkref(thing)
        Thing("referenced-thing")

        >>> u._objs[0]
        Thing("referenced-thing")

        """
        obj_id = id(obj)
        try:
            self._obj_to_idx[obj_id]
        except KeyError:
            self._obj_to_idx[obj_id] = len(self._objs)
            self._objs.append(obj)
            # Backwards compatibility: old versions of jsonpickle
            # produced "py/ref" references.
            self._namedict[self._refname()] = obj
        return obj


def loadclass(module_and_name):
    """Loads the module and returns the class.

    >>> loadclass('jsonpickle._samples.Thing')
    <class 'jsonpickle._samples.Thing'>

    >>> loadclass('does.not.exist')


    >>> loadclass('__builtin__.int')()
    0

    """
    try:
        module, name = module_and_name.rsplit('.', 1)
        module = util.untranslate_module_name(module)
        __import__(module)
        return getattr(sys.modules[module], name)
    except:
        return None


def loadfactory(obj):
    try:
        default_factory = obj['default_factory']
    except KeyError:
        return None
    try:
        type_tag = default_factory[tags.TYPE]
    except:
        return None

    typeref = loadclass(type_tag)
    if typeref:
        del obj['default_factory']
        return typeref

    return None


def getargs(obj):
    try:
        seq_list = obj[tags.SEQ]
        obj_dict = obj[tags.OBJECT]
    except KeyError:
        return []
    typeref = loadclass(obj_dict)
    if not typeref:
        return []
    if hasattr(typeref, '_fields'):
        if len(typeref._fields) == len(seq_list):
            return seq_list
    return []


def loadrepr(reprstr):
    """Returns an instance of the object from the object's repr() string.
    It involves the dynamic specification of code.

    >>> loadrepr('jsonpickle._samples/jsonpickle._samples.Thing("json")')
    Thing("json")

    """
    module, evalstr = reprstr.split('/')
    mylocals = locals()
    localname = module
    if '.' in localname:
        localname = module.split('.', 1)[0]
    mylocals[localname] = __import__(module)
    return eval(evalstr)


def has_tag(obj, tag):
    """Helper class that tests to see if the obj is a dictionary
    and contains a particular key/tag.

    >>> obj = {'test': 1}
    >>> has_tag(obj, 'test')
    True
    >>> has_tag(obj, 'fail')
    False

    >>> has_tag(42, 'fail')
    False

    """
    return type(obj) is dict and tag in obj
