# ------------------------------------------------------------------------------
# Name:         common/fileTools.py
# Purpose:      Utilities for files
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Tools for working with files
'''
from __future__ import annotations

import codecs
import contextlib  # for with statements
import gzip
import io
import pathlib
import pickle
import os
import subprocess
import typing as t

from music21.exceptions21 import Music21Exception

__all__ = [
    'readFileEncodingSafe',
    'readPickleGzip',
    'cd',
    'preparePathClassesForUnpickling',
    'restorePathClassesAfterUnpickling',
    'runSubprocessCapturingStderr',
]


@contextlib.contextmanager
def cd(targetDir):
    '''
    Useful for a temporary cd for use in a `with` statement:

         with cd('/Library/'):
              os.system(make)

    will switch temporarily, and then switch back when leaving.
    '''
    cwd = os.getcwd()

    try:
        os.chdir(targetDir)
        yield
    finally:
        os.chdir(cwd)


def readPickleGzip(filePath: str|pathlib.Path) -> t.Any:
    '''
    Read a gzip-compressed pickle file, uncompress it, unpickle it, and
    return the contents.
    '''
    preparePathClassesForUnpickling()
    with gzip.open(filePath, 'rb') as pickledFile:
        try:
            uncompressed = pickledFile.read()
            newMdb = pickle.loads(uncompressed)
        except Exception as e:
            # pickle exceptions cannot be caught directly
            # because they might come from pickle or _pickle and the latter cannot
            # be caught.
            restorePathClassesAfterUnpickling()
            raise Music21Exception('Cannot load file ' + str(filePath)) from e

    restorePathClassesAfterUnpickling()
    return newMdb

def readFileEncodingSafe(filePath, firstGuess='utf-8') -> str:
    # noinspection PyShadowingNames
    r'''
    Slow, but will read a file of unknown encoding as safely as possible using
    the chardet package.  Mostly obsolete in the utf-8 world of today, but
    useful for older code

    Let's try to load the `music21.common.__init__.py` file as ascii --
    it has a copyright symbol near the top, so it won't load in Python3:

    >>> import os
    >>> c = str(common.getSourceFilePath() / 'common' / '__init__.py')
    >>> f = open(c, encoding='ascii')
    >>> data = f.read()
    Traceback (most recent call last):
    UnicodeDecodeError: 'ascii' codec can't decode byte 0xc2 in position ...:
        ordinal not in range(128)

    That won't do! Now I know that it is in utf-8, but maybe you don't. Or it could
    be an old Humdrum or Noteworthy file with Windows or unknown encoding.
    This will load it as safely as possible.

    >>> data = common.readFileEncodingSafe(c)
    >>> data[83:106]
    'Name:         common.py'

    Well, that's nothing, since the first guess here is utf-8, and it's right. So let's
    give a worse first guess:

    >>> data = common.readFileEncodingSafe(c, firstGuess='SHIFT_JIS')  # old Japanese standard
    >>> data[83:106]
    'Name:         common.py'

    It worked!

    Note that trying lots of encodings is slow enough when the first guess is wrong
    that the firstGuess should be set to something reasonable like 'utf-8' or 'ascii'.
    '''
    try:
        with io.open(filePath, 'r', encoding=firstGuess) as thisFile:
            data = thisFile.read()
            return data
    except UnicodeDecodeError:
        import chardet  # type: ignore
        with io.open(filePath, 'rb') as thisFileBinary:
            dataBinary = thisFileBinary.read()
            encoding = chardet.detect(dataBinary)['encoding'] or 'ascii'
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


def runSubprocessCapturingStderr(subprocessCommand):
    '''
    Run a subprocess command, capturing stderr and
    only show the error if an exception is raised.
    '''
    completed_process = subprocess.run(subprocessCommand, capture_output=True, check=False)
    if completed_process.returncode != 0:
        # Raise same exception class as findNumberedPNGPath()
        # for backward compatibility
        stderr_bytes = completed_process.stderr
        try:
            import locale
            stderr_str = stderr_bytes.decode(locale.getpreferredencoding(do_setlocale=False))
        except UnicodeDecodeError:
            # not really a str, but best we can do.
            stderr_str = stderr_bytes.decode('ascii', errors='ignore')
        raise IOError(stderr_str)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest()
