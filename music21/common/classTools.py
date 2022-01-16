# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/classTools.py
# Purpose:      Utilities for classes
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import contextlib
from typing import Any, Type, Dict

# from music21 import exceptions21
__all__ = [
    'isNum', 'isListLike', 'isIterable', 'classToClassStr', 'getClassSet',
    'tempAttribute', 'saveAttributes',
]


def isNum(usrData: Any) -> bool:
    '''
    check if usrData is a number (float, int, long, Decimal),
    return boolean

    unlike `isinstance(usrData, Number)` does not return True for `True, False`.

    Does not use `isinstance(usrData, Number)` which is 6 times slower
    than calling this function (except in the case of Fraction, when
    it's 6 times faster, but that's rarer)

    Runs by adding 0 to the "number" -- so anything that implements
    add to a scalar works

    >>> common.isNum(3.0)
    True
    >>> common.isNum(3)
    True
    >>> common.isNum('three')
    False
    >>> common.isNum([2, 3, 4])
    False

    True and False are NOT numbers:

    >>> common.isNum(True)
    False
    >>> common.isNum(False)
    False
    >>> common.isNum(None)
    False
    '''
    # noinspection PyBroadException
    try:
        # TODO: this may have unexpected consequences: find
        dummy = usrData + 0
        if usrData is not True and usrData is not False:
            return True
        else:
            return False
    except Exception:  # pylint: disable=broad-except
        return False


def isListLike(usrData: Any) -> bool:
    '''
    Returns True if is a List or Tuple

    Formerly allowed for set here, but that does not allow for
    subscripting (`set([1, 2, 3])[0]` is undefined).

    Differs from isinstance(collections.abc.Sequence()) in that
    we do not want Streams included even if __contains__, __reversed__,
    and count are added.

    >>> common.isListLike([])
    True
    >>> common.isListLike('sharp')
    False
    >>> common.isListLike((None, None))
    True
    >>> common.isListLike({'a', 'b', 'c', 'c'})
    False
    >>> common.isListLike(stream.Stream())
    False
    '''
    return isinstance(usrData, (list, tuple))


def isIterable(usrData: Any) -> bool:
    '''
    Returns True if is the object can be iter'd over
    and is NOT a string

    >>> common.isIterable([5, 10])
    True
    >>> common.isIterable('sharp')
    False
    >>> common.isIterable((None, None))
    True
    >>> common.isIterable(stream.Stream())
    True

    Ranges are not iterators by python 3, but return True

    >>> common.isIterable(range(20))
    True

    Classes are not iterable even if their instances are:

    >>> common.isIterable(stream.Stream)
    False

    Changed in v7.3 -- Classes (not instances) are not iterable
    '''
    if isinstance(usrData, (str, bytes)):
        return False
    if hasattr(usrData, '__iter__'):
        if usrData.__class__ is type:
            return False
        return True
    return False


def classToClassStr(classObj: Type) -> str:
    '''Convert a class object to a class string.

    >>> common.classToClassStr(note.Note)
    'Note'
    >>> common.classToClassStr(chord.Chord)
    'Chord'
    '''
    # remove closing quotes
    return str(classObj).rsplit('.', maxsplit=1)[-1][:-2]


def getClassSet(instance, classNameTuple=None):
    '''
    Return the classSet for an instance (whether a Music21Object or something else.
    See base.Music21Object.classSet for more details.

    >>> p = pitch.Pitch()
    >>> cs = common.classTools.getClassSet(p)
    >>> cs
     frozenset(...)
    >>> pitch.Pitch in cs
    True
    >>> 'music21.pitch.Pitch' in cs
    True
    >>> 'Pitch' in cs
    True
    >>> object in cs
    True
    >>> 'object' in cs
    True

    To save time (this IS a performance-critical operation), classNameTuple
    can be passed a tuple of names such as ('Pitch', 'object') that
    will save the creation time of this set.

    >>> cs2 = common.classTools.getClassSet(p, classNameTuple=('Pitch', 'ProtoM21Object'))
    >>> 'Pitch' in cs2
    True

    Use base.Music21Object.classSet in general for music21Objects since it
    not only caches the result for each object, it caches the result for the
    whole class the first time it is run.
    '''
    if classNameTuple is None:
        classNameList = [x.__name__ for x in instance.__class__.mro()]
    else:
        classNameList = list(classNameTuple)

    classObjList = instance.__class__.mro()
    classListFQ = [x.__module__ + '.' + x.__name__ for x in instance.__class__.mro()]
    classList = classNameList + classObjList + classListFQ
    classSet = frozenset(classList)
    return classSet


TEMP_ATTRIBUTE_SENTINEL = object()


@contextlib.contextmanager
def tempAttribute(obj, attribute: str, new_val=TEMP_ATTRIBUTE_SENTINEL):
    '''
    Temporarily set an attribute in an object to another value
    and then restore it afterwards.

    >>> p = pitch.Pitch('C4')
    >>> p.midi
    60
    >>> with common.classTools.tempAttribute(p, 'nameWithOctave', 'D#5'):
    ...     p.midi
    75
    >>> p.nameWithOctave
    'C4'

    Setting to a new value is optional.

    For working with multiple attributes see :func:`~music21.classTools.saveAttributes`.

    New in v7.
    '''
    tempStorage = getattr(obj, attribute)
    if new_val is not TEMP_ATTRIBUTE_SENTINEL:
        setattr(obj, attribute, new_val)
    try:
        yield
    finally:
        setattr(obj, attribute, tempStorage)

@contextlib.contextmanager
def saveAttributes(obj, *attributeList):
    '''
    Save a number of attributes in an object and then restore them afterwards.

    >>> p = pitch.Pitch('C#2')
    >>> with common.classTools.saveAttributes(p, 'name', 'accidental'):
    ...     p.step = 'E'
    ...     p.accidental = pitch.Accidental('flat')
    ...     p.nameWithOctave
    'E-2'
    >>> p.nameWithOctave
    'C#2'

    For storing and setting a value on a single attribute see
    :func:`~music21.classTools.tempAttribute`.

    New in v7.
    '''
    tempStorage: Dict[str, Any] = {}
    for attribute in attributeList:
        tempStorage[attribute] = getattr(obj, attribute)
    try:
        yield
    finally:
        for k, v in tempStorage.items():  # dicts are ordered in 3.7
            setattr(obj, k, v)


# ------------------------------------------------------------------------------
# define presented order in documentation
# _DOC_ORDER = [fromRoman, toRoman]

if __name__ == '__main__':
    import music21
    music21.mainTest()

