# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/misc.py
# Purpose:      Everything that doesn't fit into anything else.
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
If it doesn't fit anywhere else in the common directory, you'll find it here...
'''
from typing import Tuple, List
import platform
import re

__all__ = [
    'flattenList',
    'getMissingImportStr',
    'getPlatform',
    'macOSVersion',
    'sortModules',
    'pitchList',
    'runningUnderIPython',
    'defaultDeepcopy',
    'cleanedFlatNotation',
]

import copy
import os
import sys
import textwrap
import time

# -----------------------------------------------------------------------------


def flattenList(originalList: List) -> List:
    '''
    Flatten a list of lists into a flat list

    but not a list of lists of lists...

    >>> l = [[1, 2, 3], [4, 5], [6]]
    >>> common.flattenList(l)
    [1, 2, 3, 4, 5, 6]
    '''
    return [item for sublist in originalList for item in sublist]

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

def macOSVersion() -> Tuple[int, int, int]:  # pragma: no cover
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


def sortModules(moduleList) -> List[str]:
    '''
    Sort a lost of imported module names such that most recently modified is
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
    lists of pitches
    '''
    return '[' + ', '.join([x.nameWithOctave for x in pitchL]) + ']'


def runningUnderIPython() -> bool:
    '''
    return bool if we are running under iPython Notebook (not iPython)

    (no tests, since will be different)

    This post:

    http://stackoverflow.com/questions/15411967/
    how-can-i-check-if-code-is-executed-in-the-ipython-notebook

    says not to do this, but really, I can't think of another way
    to have different output as default.

    Returns True also for Google Colab
    '''
    if sys.stderr.__class__.__name__ == 'OutStream':
        return True
    else:
        return False


# ----------------------------
# match collections, defaultdict()


# NB -- temp files (tempFile) etc. are in environment.py

# ------------------------------------------------------------------------------
def defaultDeepcopy(obj, memo, callInit=True):
    '''
    Unfortunately, it is not possible to do something like:

        def __deepcopy__(self, memo):
            if self._noDeepcopy:
                return self.__class__()
            else:
                copy.deepcopy(self, memo, ignore__deepcopy__=True)

    Or, else: return NotImplemented

    so that's what this is for:

        def __deepcopy__(self, memo):
            if self._noDeepcopy:
                return self.__class__()
            else:
                return common.defaultDeepcopy(self, memo)

    looks through both __slots__ and __dict__ and does a deepcopy
    of anything in each of them and returns the new object.

    If callInit is False, then only __new__() is called.  This is
    much faster if you're just going to overload every instance variable.
    '''
    if callInit is False:
        new = obj.__class__.__new__(obj.__class__)
    else:
        new = obj.__class__()

    dictState = getattr(obj, '__dict__', None)
    if dictState is not None:
        for k in dictState:
            # noinspection PyArgumentList
            setattr(new, k, copy.deepcopy(dictState[k], memo=memo))
    slots = set()
    for cls in obj.__class__.mro():  # it is okay that it's in reverse order, since it's just names
        slots.update(getattr(cls, '__slots__', ()))
    for slot in slots:
        slotValue = getattr(obj, slot, None)
        # might be none if slot was deleted; it will be recreated here
        setattr(new, slot, copy.deepcopy(slotValue))

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
