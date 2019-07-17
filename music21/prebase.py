# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         prebase.py
# Purpose:      classes for anything in music21 to inherit from.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2019 Michael Scott Cuthbert and the music21 Project
# License:      BSD or LGPL, see license.txt
# ------------------------------------------------------------------------------
'''
Classes for pseudo-m21 objects to inherit from.  The most import attributes that nearly
everything in music21 -- not just things that live in streams --
should inherit from are given below.

Concept borrowed from m21j.
'''
from typing import (
    Dict,
    FrozenSet,
    Sequence,
    Union,
    Tuple,
)

# ## Notes:
# adding ProtoM21Object added 0.03 microseconds to creation time (2.51 to 2.54)
# well worth it.

class ProtoM21Object:
    '''
    A class for pseudo-m21 objects to inherit from.

    Cannot be put into streams.
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
    _classSetCacheDict = {}  # type: Dict[type, Frozenset[Union[str, type]]]
    # same with fully qualified names
    _classListFullyQualifiedCacheDict = {}


    __slots__ = ()

    def isClassOrSubclass(self, classFilterList : Sequence) -> bool:
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
            classNameList = list(self.classes)  # type: List[Union[str, type]]

            classObjList = self.__class__.mro()
            classListFQ = [x.__module__ + '.' + x.__name__ for x in self.__class__.mro()]
            classList = classNameList + classObjList + classListFQ  # type: List[Union[str, type]]
            classSet = frozenset(classList)
            self._classSetCacheDict[self.__class__] = classSet
            return classSet

    def __repr__(self) -> str:
        '''
        Defines the representation for a ProtoM21Object
        '''
        reprHead = '<'
        if self.__module__ != '__main__':
            reprHead += self.__module__ + '.'
        reprHead += self.__class__.__qualname__
        strRepr = self._reprInternal()
        if strRepr:
            reprHead += ' ' + strRepr.strip()
        return reprHead + '>'

    def _reprInternal(self) -> str:
        '''
        Overload this method for most objects -- defines the insides of the representation.
        '''
        if not hasattr(self, 'id'):
            return f'object at {hex(id(self))}'
        elif self.id == id(self):
            return f'object at {hex(self.id)}'
        else:
            reprId = self.id
            try:
                reprId = hex(reprId)
            except ValueError:
                pass
            return f'id={reprId}'


del (
    Dict,
    FrozenSet,
    Sequence,
    Union,
    Tuple,
)


# ---------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest()

