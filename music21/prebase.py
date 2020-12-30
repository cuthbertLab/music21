# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         prebase.py
# Purpose:      classes for anything in music21 to inherit from.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2019 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Classes for pseudo-m21 objects to inherit from.  The most import attributes that nearly
everything in music21 -- not just things that live in streams --
should inherit from are given below.

Concept borrowed from m21j.
'''
import unittest

from typing import (
    Dict,
    FrozenSet,
    List,
    Sequence,
    Union,
    Tuple,
)


class ProtoM21Object:
    '''
    A class for pseudo-m21 objects to inherit from.  Any object can inherit from
    ProtoM21Object and it makes sense for anything a user is likely to encounter
    to inherit from it.  Certain translators, etc. can choose to skip it.

    >>> class PitchCounter(prebase.ProtoM21Object):
    ...     def _reprInternal(self):
    ...         return 'no pitches'

    >>> pc = PitchCounter()
    >>> pc.classes
    ('PitchCounter', 'ProtoM21Object', 'object')
    >>> PitchCounter in pc.classSet
    True
    >>> pc.isClassOrSubclass(('music21.note.Note',))
    False
    >>> repr(pc)
    '<music21.PitchCounter no pitches>'


    ProtoM21Objects, like other Python primitives, cannot be put into streams --
    this is what base.Music21Object does.

    A ProtoM21Object defines several methods relating to unified representation
    and keeping track of the classes of the object.  It has no instance attributes
    or properties, and thus adds a very small creation time impact: recent
    tests show that an empty object with an empty `__init__()` method can
    be created in about 175ns while an empty object that subclasses ProtoM21Object
    with the same empty `__init__()` takes only 180ns, or a 5ns impact.  On
    real objects, the creation time percentage hit is usually much smaller.

    ProtoM21Objects have no __init__() defined, so do not call super().__init__() on
    objects that only inherit from ProtoM21Object unless you like wasting 200ns.
    '''

    # define order to present names in documentation; use strings
    _DOC_ORDER = [
        'classes',
        'classSet',
    ]

    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {}

    # this dictionary stores as a tuple of strings for each Class so that
    # it only needs to be made once (11 microseconds per call, can be
    # a big part of iteration; from cache just 1 microsecond)
    _classTupleCacheDict = {}
    _classSetCacheDict: Dict[type, FrozenSet[Union[str, type]]] = {}
    # same with fully qualified names
    _classListFullyQualifiedCacheDict = {}

    __slots__ = ()

    def isClassOrSubclass(self, classFilterList: Sequence) -> bool:
        '''
        Given a class filter list (a list or tuple must be submitted),
        which may have strings or class objects, determine
        if this class is of the provided classes or a subclasses.

        NOTE: this is a performance critical operation
        for performance, only accept lists or tuples

        >>> n = note.Note()
        >>> n.isClassOrSubclass(('Note',))
        True
        >>> n.isClassOrSubclass(('GeneralNote',))
        True
        >>> n.isClassOrSubclass((note.Note,))
        True
        >>> n.isClassOrSubclass((note.Rest,))
        False
        >>> n.isClassOrSubclass((note.Note, note.Rest))
        True
        >>> n.isClassOrSubclass(('Rest', 'Note'))
        True
        '''
        return not self.classSet.isdisjoint(classFilterList)

    @property
    def classes(self) -> Tuple[str]:
        '''
        Returns a tuple containing the names (strings, not objects) of classes that this
        object belongs to -- starting with the object's class name and going up the mro()
        for the object.

        Notes are Music21Objects:

        >>> n = note.Note('C#')
        >>> n.classes
        ('Note', 'NotRest', 'GeneralNote', 'Music21Object', 'ProtoM21Object', 'object')

        Durations are not, but they inherit from ProtoM21Object

        >>> d = duration.Duration('half')
        >>> d.classes
        ('Duration', 'ProtoM21Object', 'SlottedObjectMixin', 'object')


        Having quick access to these things as strings makes it easier to do comparisons:

        Example: find GClefs that are not Treble clefs (or treble 8vb, etc.):

        >>> s = stream.Stream()
        >>> s.insert(10, clef.GClef())
        >>> s.insert(20, clef.TrebleClef())
        >>> s.insert(30, clef.FrenchViolinClef())
        >>> s.insert(40, clef.Treble8vbClef())
        >>> s.insert(50, clef.BassClef())
        >>> s2 = stream.Stream()
        >>> for t in s:
        ...    if 'GClef' in t.classes and 'TrebleClef' not in t.classes:
        ...        s2.insert(t)
        >>> s2.show('text')
        {10.0} <music21.clef.GClef>
        {30.0} <music21.clef.FrenchViolinClef>

        `Changed 2015 Sep`: returns a tuple, not a list.
        '''
        try:
            return self._classTupleCacheDict[self.__class__]
        except KeyError:
            classTuple = tuple([x.__name__ for x in self.__class__.mro()])
            self._classTupleCacheDict[self.__class__] = classTuple
            return classTuple

    @property
    def classSet(self) -> FrozenSet[Union[str, type]]:
        '''
        Returns a set (that is, unordered, but indexed) of all of the classes that
        this class belongs to, including
        string names, fullyQualified string names, and objects themselves.

        It's cached on a per class basis, so makes for a really fast way of checking to
        see if something belongs
        to a particular class when you don't know if the user has given a string,
        a fully qualified string name, or an object.

        Did I mention it's fast?  It's a drop in substitute for the deprecated
        `.isClassOrSubclass`.  It's not as fast as x in n.classes or isinstance(n, x)
        if you know whether it's a string or class, but this is good and safe.

        >>> n = note.Note()
        >>> 'Note' in n.classSet
        True
        >>> 'music21.note.Note' in n.classSet
        True
        >>> note.Note in n.classSet
        True

        >>> 'Rest' in n.classSet
        False
        >>> note.Rest in n.classSet
        False

        >>> object in n.classSet
        True

        >>> sorted([s for s in n.classSet if isinstance(s, str)])
        ['GeneralNote', 'Music21Object', 'NotRest', 'Note', 'ProtoM21Object',
         'builtins.object',
         'music21.base.Music21Object',
         'music21.note.GeneralNote', 'music21.note.NotRest', 'music21.note.Note',
         'music21.prebase.ProtoM21Object',
         'object']

        >>> sorted([s for s in n.classSet if not isinstance(s, str)], key=lambda x: x.__name__)
        [<class 'music21.note.GeneralNote'>,
         <class 'music21.base.Music21Object'>,
         <class 'music21.note.NotRest'>,
         <class 'music21.note.Note'>,
         <class 'music21.prebase.ProtoM21Object'>,
         <class 'object'>]
        '''
        try:
            return self._classSetCacheDict[self.__class__]
        except KeyError:
            classList: List[Union[str, type]] = list(self.classes)
            classList.extend(self.__class__.mro())
            classList.extend(x.__module__ + '.' + x.__name__ for x in self.__class__.mro())

            classSet = frozenset(classList)
            self._classSetCacheDict[self.__class__] = classSet
            return classSet

    def __repr__(self) -> str:
        '''
        Defines the default representation for a ProtoM21Object
        which includes the module name, the class name, and additional
        information, such as the memory location:

        >>> p = prebase.ProtoM21Object()
        >>> repr(p)
        '<music21.prebase.ProtoM21Object object at 0x112590380>'

        The additional information is defined in the `_reprInternal` method,
        so objects inheriting from ProtoM21Object (such as Music21Object)
        should change `_reprInternal` and not `__repr__`.
        '''
        reprHead = '<'
        if self.__module__ != '__main__':
            reprHead += self.__module__ + '.'
        reprHead += self.__class__.__qualname__
        strRepr = self._reprInternal()
        if strRepr and not strRepr.startswith(':'):
            reprHead += ' '

        if strRepr:
            reprHead += strRepr.strip()
        return reprHead + '>'

    def _reprInternal(self) -> str:
        '''
        Defines the insides of the representation.

        Overload this method for most objects.

        A default representation:

        >>> p = prebase.ProtoM21Object()
        >>> p._reprInternal()
        'object at 0x112590380'

        If an object has `.id` defined and `x.id` is not the same as `id(x)`
        then that id is used instead:

        >>> b = base.Music21Object()
        >>> b._reprInternal()
        'object at 0x129a903b1'
        >>> b.id = 'hi'
        >>> b._reprInternal()
        'id=hi'
        '''
        if not hasattr(self, 'id') or self.id == id(self):
            return f'object at {hex(id(self))}'
        else:
            reprId = self.id
            try:
                reprId = hex(reprId)
            except (ValueError, TypeError):
                pass
            return f'id={reprId}'


del (
    Dict,
    FrozenSet,
    Sequence,
    Union,
    Tuple,
)


class Test(unittest.TestCase):
    def test_reprInternal(self):
        from music21.base import Music21Object
        b = Music21Object()
        b.id = 'hello'
        r = repr(b)
        self.assertEqual(r, '<music21.base.Music21Object id=hello>')


# ---------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
