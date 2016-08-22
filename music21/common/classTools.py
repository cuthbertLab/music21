#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common/classTools.py
# Purpose:      Utilities for classes
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

#from music21 import exceptions21
from music21.ext import six

__all__ = ['isNum', 'isListLike', 'isIterable', 'classToClassStr']

def isNum(usrData):
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
    
    :rtype: bool
    '''
    try:
        # TODO: this may have unexpected consequences: find
        dummy = usrData + 0
        if usrData is not True and usrData is not False:
            return True
        else:
            return False
    except Exception: # pylint: disable=broad-except
        return False


def isListLike(usrData):
    """
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
    >>> common.isListLike(set(['a','b','c','c']))
    False
    >>> common.isListLike(stream.Stream())
    False
    
    :rtype: bool
    """
    return isinstance(usrData, (list, tuple))

def isIterable(usrData):
    """
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
    
    :rtype: bool
    """
    if hasattr(usrData, "__iter__"): 
        if six.PY3: # no __iter__ on strings in py2
            if isinstance(usrData, str) or isinstance(usrData, bytes):
                return False
        return True
    else:
        return False

def classToClassStr(classObj):
    '''Convert a class object to a class string.

    >>> common.classToClassStr(note.Note)
    'Note'
    >>> common.classToClassStr(chord.Chord)
    'Chord'
    
    :rtype: str
    '''
    # remove closing quotes
    return str(classObj).split('.')[-1][:-2]

#-------------------------------------------------------------------------------
# define presented order in documentation
# _DOC_ORDER = [fromRoman, toRoman]


if __name__ == "__main__":
    import music21
    music21.mainTest()

#------------------------------------------------------------------------------
# eof


