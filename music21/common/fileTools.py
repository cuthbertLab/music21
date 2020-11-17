# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/fileTools.py
# Purpose:      Utilities for files
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Tools for working with files
'''

import codecs
import contextlib  # for with statements
import gzip
import io
import pathlib
import pickle
import os
from typing import Union, Any

import chardet

from music21.exceptions21 import Music21Exception

__all__ = [
    'readFileEncodingSafe',
    'readPickleGzip',
    'cd',
    'preparePathClassesForUnpickling',
    'restorePathClassesAfterUnpickling',
]


@contextlib.contextmanager
def cd(targetDir):
    '''
    Useful for a temporary cd for use in a `with` statement:

         with cd('/Library/'):
              os.system(make)

    will switch temporarily, and then switch back when leaving.
    '''
    try:
        cwd = os.getcwdu()  # unicode # @UndefinedVariable
    except AttributeError:
        cwd = os.getcwd()  # non unicode

    try:
        os.chdir(targetDir)
        yield
    finally:
        os.chdir(cwd)


def readPickleGzip(filePath: Union[str, pathlib.Path]) -> Any:
    '''
    Read a gzip-compressed pickle file, uncompress it, unpickle it, and
    return the contents.
    '''
    preparePathClassesForUnpickling()
    with gzip.open(filePath, 'rb') as pickledFile:
        try:
            uncompressed = pickledFile.read()
            newMdb = pickle.loads(uncompressed)
        except Exception as e:  # pylint: disable=broad-except
            # pickle exceptions cannot be caught directly
            # because they might come from pickle or _pickle and the latter cannot
            # be caught.
            restorePathClassesAfterUnpickling()
            raise Music21Exception('Cannot load file ' + str(filePath)) from e

    restorePathClassesAfterUnpickling()
    return newMdb

def readFileEncodingSafe(filePath, firstGuess='utf-8'):
    # noinspection PyShadowingNames
    r'''
    Slow, but will read a file of unknown encoding as safely as possible using
    the chardet package.

    Let's try to load this file as ascii -- it has a copyright symbol at the top
    so it won't load in Python3:

    >>> import os
    >>> c = str(common.getSourceFilePath() / 'common' / '__init__.py')
    >>> #_DOCS_SHOW f = open(c)
    >>> #_DOCS_SHOW data = f.read()
    Traceback (most recent call last):
    UnicodeDecodeError: 'ascii' codec can't decode byte 0xc2 in position ...:
        ordinal not in range(128)

    That won't do! now I know that it is in utf-8, but maybe you don't. Or it could
    be an old humdrum or Noteworthy file with unknown encoding.  This will load it safely.

    >>> data = common.readFileEncodingSafe(c)
    >>> data[0:30]
    '# -*- coding: utf-8 -*-\n# ----'

    Well, that's nothing, since the first guess here is utf-8 and it's right. So let's
    give a worse first guess:

    >>> data = common.readFileEncodingSafe(c, firstGuess='SHIFT_JIS')  # old Japanese standard
    >>> data[0:30]
    '# -*- coding: utf-8 -*-\n# ----'

    It worked!

    Note that this is slow enough if it gets it wrong that the firstGuess should be set
    to something reasonable like 'ascii' or 'utf-8'.

    :rtype: str
    '''
    try:
        with io.open(filePath, 'r', encoding=firstGuess) as thisFile:
            data = thisFile.read()
            return data
    except UnicodeDecodeError:
        with io.open(filePath, 'rb') as thisFileBinary:
            dataBinary = thisFileBinary.read()
            encoding = chardet.detect(dataBinary)['encoding']
            return codecs.decode(dataBinary, encoding)
    # might also raise FileNotFoundError, but let that bubble


_storedPathlibClasses = {'posixPath': pathlib.PosixPath, 'windowsPath': pathlib.WindowsPath}

def preparePathClassesForUnpickling():
    '''
    When we need to unpickle a function that might have relative paths
    (like some music21 stream options), Windows chokes if the PosixPath
    is not defined, but usually can still unpickle easily.
    '''
    from music21.common.misc import getPlatform
    platform = getPlatform()
    if platform == 'win':
        pathlib.PosixPath = pathlib.WindowsPath
    else:
        pathlib.WindowsPath = pathlib.PosixPath


def restorePathClassesAfterUnpickling():
    '''
    After unpickling, leave pathlib alone.
    '''
    from music21.common.misc import getPlatform
    platform = getPlatform()
    if platform == 'win':
        pathlib.PosixPath = _storedPathlibClasses['posixPath']
    else:
        pathlib.WindowsPath = _storedPathlibClasses['windowsPath']


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest()
