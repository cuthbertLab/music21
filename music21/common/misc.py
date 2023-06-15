# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/misc.py
# Purpose:      Everything that doesn't fit into anything else.
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2020 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
If it doesn't fit anywhere else in the common directory, you'll find it here...
'''
from __future__ import annotations

from collections.abc import Callable, Iterable
import copy
import os
import platform
import re
import sys
import textwrap
import time
import types
import typing as t
import weakref

from music21.common.decorators import deprecated

__all__ = [
    'flattenList',
    'getMissingImportStr',
    'getPlatform',
    'macOSVersion',
    'sortModules',
    'pitchList',
    'unique',
    'runningInNotebook',
    'defaultDeepcopy',
    'cleanedFlatNotation',
]

if t.TYPE_CHECKING:
    _T = t.TypeVar('_T')

# -----------------------------------------------------------------------------


def flattenList(originalList: Iterable[Iterable[_T]]) -> list[_T]:
    '''
    Flatten a list of lists into a flat list

    but not a list of lists of lists...

    >>> l = [[1, 2, 3], [4, 5], [6]]
    >>> common.flattenList(l)
    [1, 2, 3, 4, 5, 6]
    '''
    return [item for sublist in originalList for item in sublist]


def unique(originalList: Iterable, *, key: Callable | None = None) -> list:
    '''
    Return a List of unique items from an iterable, preserving order.
    (unlike casting to a set and back)

    (And why is this not already in Python?)

    >>> common.misc.unique([3, 2, 4, 3, 2, 5])
    [3, 2, 4, 5]

    Works on any iterable, but order might not be preserved for sets, etc.

    >>> common.misc.unique(range(5))
    [0, 1, 2, 3, 4]

    If key is a function then use that to get the value:

    >>> s = converter.parse('tinyNotation: c4 E d C f# e a')
    >>> common.misc.unique(s.recurse().notes, key=lambda n: n.name)
     [<music21.note.Note C>,
      <music21.note.Note E>,
      <music21.note.Note D>,
      <music21.note.Note F#>,
      <music21.note.Note A>]
    '''
    seen = set()
    out = []
    for el in originalList:
        if key:
            elKey = key(el)
        else:
            elKey = el
        if elKey in seen:
            continue
        seen.add(elKey)
        out.append(el)
    return out

# ------------------------------------------------------------------------------
# provide warning strings to users for use in conditional imports


def getMissingImportStr(modNameList):
    '''
    Given a list of missing module names, returns a nicely-formatted message to the user
    that gives instructions on how to expand music21 with optional packages.


    >>> print(common.getMissingImportStr(['matplotlib']))
    Certain music21 functions might need the optional package matplotlib;
    if you run into errors, install it by following the instructions at
    http://mit.edu/music21/doc/installing/installAdditional.html

    >>> print(common.getMissingImportStr(['matplotlib', 'numpy']))
    Certain music21 functions might need these optional packages: matplotlib, numpy;
    if you run into errors, install them by following the instructions at
    http://mit.edu/music21/doc/installing/installAdditional.html
    '''
    if not modNameList:
        return None
    elif len(modNameList) == 1:
        m = modNameList[0]
        return textwrap.dedent(f'''Certain music21 functions might need the optional package {m};
                  if you run into errors, install it by following the instructions at
                  http://mit.edu/music21/doc/installing/installAdditional.html''')
    else:
        m = ', '.join(modNameList)
        return textwrap.dedent(
            f'''Certain music21 functions might need these optional packages: {m};
                   if you run into errors, install them by following the instructions at
                   http://mit.edu/music21/doc/installing/installAdditional.html''')


def getPlatform() -> str:
    '''
    Return the name of the platform, where platforms are divided
    between 'win' (for Windows), 'darwin' (for MacOS X), and 'nix' for
    (GNU/Linux and other variants).

    Does not discern between Linux/FreeBSD, etc.

    Lowercase names are for backwards compatibility -- this existed before
    the platform module.
    '''
    # possible os.name values: 'posix', 'nt', 'os2', 'ce', 'java'.
    if platform.system() == 'Windows':
        return 'win'
    elif platform.system() == 'Darwin':
        return 'darwin'
    elif os.name == 'posix':  # catch all other nix platforms
        return 'nix'  # this must be after the Mac Darwin check, b/c Darwin is also posix
    else:
        return os.name

def macOSVersion() -> tuple[int, int, int]:  # pragma: no cover
    '''
    On a Mac returns the current version as a tuple of (currently 3) ints,
    such as: (10, 5, 6) for 10.5.6.

    On other systems, returns (0, 0, 0)
    '''
    if getPlatform() != 'darwin':
        return (0, 0, 0)

    # Catch minor and maintenance as they could be missing,
    # e.g., macOS Big Sur 11.0.1 (20B28) corresponds to "10.16".
    major, *minor_and_maintenance = tuple(int(v) for v in platform.mac_ver()[0].split('.'))

    minor = minor_and_maintenance[0] if minor_and_maintenance else 0
    maintenance = minor_and_maintenance[1] if len(minor_and_maintenance) > 1 else 0

    return (major, minor, maintenance)


def sortModules(moduleList: Iterable[t.Any]) -> list[object]:
    '''
    Sort a list of imported module names such that most recently modified is
    first.  In ties, last access time is used then module name

    Will return a different order each time depending on the last mod time
    '''
    sort = []
    modNameToMod = {}
    for mod in moduleList:
        modNameToMod[mod.__name__] = mod
        fp = mod.__file__  # returns the py or pyc file
        stat = os.stat(fp)
        lastmod = time.localtime(stat[8])
        asctime = time.asctime(lastmod)
        sort.append((lastmod, asctime, mod.__name__))
    sort.sort()
    sort.reverse()
    # just return module list
    outMods = [modNameToMod[modName] for lastmod, asctime, modName in sort]
    return outMods


# ----------------------------
def pitchList(pitchL):
    '''
    utility method that replicates the previous behavior of
    lists of pitches.

    May be moved in v8 or later to a common.testing or test.X module.
    '''
    return '[' + ', '.join([x.nameWithOctave for x in pitchL]) + ']'


def runningInNotebook() -> bool:
    '''
    return bool if we are running under Jupyter Notebook (not IPython terminal)
    or Google Colabatory (colab).

    Methods based on:

    https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook

    (No tests provided here, since results will differ depending on environment)
    '''
    if sys.stderr.__class__.__name__ == 'OutStream':
        return True
    else:
        return False


@deprecated('v9', 'v10', 'use runningInNotebook() instead')
def runningUnderIPython() -> bool:  # pragma: no cover
    '''
    DEPRECATED in v9: use runningInNotebook() instead
    '''
    return runningInNotebook()


# ----------------------------
# match collections, defaultdict()


# NB -- temp files (tempFile) etc. are in environment.py

# ------------------------------------------------------------------------------
# From copy.py
_IMMUTABLE_DEEPCOPY_TYPES = {
    type(None), type(Ellipsis), type(NotImplemented),
    int, float, bool, complex, bytes, str,
    types.CodeType, type, range,
    types.BuiltinFunctionType, types.FunctionType,
    weakref.ref, property,
}

def defaultDeepcopy(obj: t.Any, memo=None, *, ignoreAttributes: Iterable[str] = ()):
    '''
    Unfortunately, it is not possible to do something like::

        def __deepcopy__(self, memo):
            if self._noDeepcopy:
                return self.__class__()
            else:
                copy.deepcopy(self, memo, ignore__deepcopy__=True)

    Or, else: return NotImplemented

    so that's what this is for::

        def __deepcopy__(self, memo):
            if self._noDeepcopy:
                return self.__class__()
            else:
                return common.defaultDeepcopy(self, memo)

    Does a deepcopy of the state returned by `__reduce_ex__` for protocol 4.

    * Changed in v9: callInit is removed, replaced with ignoreAttributes.
      uses `__reduce_ex__` internally.
    '''
    if memo is None:
        memo = {}

    rv = obj.__reduce_ex__(4)  # get a protocol 4 reduction
    func, args, state = rv[:3]
    new = func(*args)
    memo[id(obj)] = new

    # set up reducer to not copy the ignoreAttributes set.
    for attr, value in state.items():
        if attr in ignoreAttributes:
            setattr(new, attr, None)
        elif type(value) in _IMMUTABLE_DEEPCOPY_TYPES:
            setattr(new, attr, value)
        else:
            setattr(new, attr, copy.deepcopy(value, memo))
    return new


def cleanedFlatNotation(music_str: str) -> str:
    '''
    Returns a copy of the given string where each occurrence of a flat note
    specified with a 'b' is replaced by a '-'.

    music_str is a string containing a note specified (for example in a chord)

    Returns a new string with flats only specified with '-'.

    >>> common.cleanedFlatNotation('Cb')
    'C-'
    '''
    return re.sub('([A-Ga-g])b', r'\1-', music_str)


if __name__ == '__main__':
    import music21
    music21.mainTest()
