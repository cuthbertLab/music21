# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/weakrefTools.py
# Purpose:      Utilities for weak references
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

__all__ = ['wrapWeakref', 'unwrapWeakref']

import weakref

# ------------------------------------------------------------------------------


def wrapWeakref(referent):
    '''
    utility function that wraps objects as weakrefs but does not wrap
    already wrapped objects; also prevents wrapping the unwrappable "None" type, etc.

    >>> import weakref
    >>> class Mock:
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
    # if type(referent) is weakref.ref:
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


    >>> class Mock:
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


if __name__ == '__main__':
    import music21
    music21.mainTest()

