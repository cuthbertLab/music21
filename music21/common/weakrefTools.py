#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common/weakrefTools.py
# Purpose:      Utilities for weak references
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

__all__ = ['wrapWeakref', 'unwrapWeakref', 'isWeakref', 'findWeakref']

import weakref
from music21.common.decorators import deprecated

#-------------------------------------------------------------------------------
def wrapWeakref(referent):
    '''
    utility function that wraps objects as weakrefs but does not wrap
    already wrapped objects; also prevents wrapping the unwrapable "None" type, etc.

    >>> import weakref
    >>> class Mock(object):
    ...     pass
    >>> a1 = Mock()
    >>> ref1 = common.wrapWeakref(a1)
    >>> ref1
    <weakref at 0x101f29ae8; to 'Mock' at 0x101e45358>
    >>> ref2 = common.wrapWeakref(ref1)
    >>> ref2
    <weakref at 0x101f299af; to 'Mock' at 0x101e45358>
    >>> ref3 = common.wrapWeakref(5)
    >>> ref3
    5
    '''
    #if type(referent) is weakref.ref:
#     if isinstance(referent, weakref.ref):
#         return referent
    try:
        return weakref.ref(referent)
    # if referent is None, will raise a TypeError
    # if referent is a weakref, will also raise a TypeError
    # will also raise a type error for string, ints, etc.
    # slight performance boost rather than checking if None
    except TypeError:
        return referent

def unwrapWeakref(referent):
    '''
    Utility function that gets an object that might be an object itself
    or a weak reference to an object.  It returns obj() if it's a weakref.
    and obj if it's not.


    >>> class Mock(object):
    ...     pass
    >>> a1 = Mock()
    >>> a2 = Mock()
    >>> a2.strong = a1
    >>> a2.weak = common.wrapWeakref(a1)
    >>> common.unwrapWeakref(a2.strong) is a1
    True
    >>> common.unwrapWeakref(a2.weak) is a1
    True
    >>> common.unwrapWeakref(a2.strong) is common.unwrapWeakref(a2.weak)
    True
    '''
    # faster than type checking if referent will usually be a weakref.ref.
    if isinstance(referent, weakref.ref):
        return referent()
    else:
        return referent


@deprecated("September 2015", "December 2015", "Use isinstance(obj, weakref.ref) instead")
def isWeakref(referent):
    '''Test if an object is a weakref

    just does isinstance, so DEPRECATED Sep 2015; to disappear soon as Dec 2015.

    >>> class Mock(object):
    ...     pass
    >>> a1 = Mock()
    >>> a2 = Mock()
    >>> common.isWeakref(a1)
    False
    >>> common.isWeakref(3)
    False
    >>> common.isWeakref(common.wrapWeakref(a1))
    True
    '''
    if isinstance(referent, weakref.ref):        
        return True
    return False


def findWeakref(target):
    '''
    Given an object or composition of objects, find an attribute that is a weakref. 
    This is a diagnostic tool.  It does not work on all cases (slots, etc.), but it works okay.

    Prints rather than returns

    >>> n = note.Note()
    >>> s = stream.Stream()
    >>> s2 = stream.Stream()
    >>> s.insert(0, n)
    >>> s2.insert(0, n)
    >>> common.findWeakref(s)
    ('found weakref', <weakref at 0x...; to 'Stream' at 0x...>, 
        '_activeSite', 'of target:', <music21.note.Note C>)
    '''
    for attrName in target.__dict__:
        try:
            attr = getattr(target, attrName)
        except AttributeError:
            print('exception on attribute access: %s' % attrName)
        if isWeakref(attr):
            print('found weakref', attr, attrName, 'of target:', target)
        if isinstance(attr, (list, tuple)):
            for x in attr:
                findWeakref(x)



if __name__ == "__main__":
    import music21
    music21.mainTest()

#------------------------------------------------------------------------------
# eof
