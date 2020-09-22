# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/pathTools.py
# Purpose:      Utilities for paths
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
__all__ = [
    'getRootFilePath',
    'getSourceFilePath',
    'getMetadataCacheFilePath',
    'getCorpusFilePath',
    'getCorpusContentDirs',
    'relativepath',
    'cleanpath',
]

import inspect
import os
import pathlib

# ------------------------------------------------------------------------------


def getSourceFilePath():
    '''
    Get the music21 directory that contains source files such as note.py, etc..
    This is not the same as the
    outermost package development directory.

    :rtype: pathlib.Path
    '''
    fpThis = pathlib.Path(inspect.getfile(getSourceFilePath)).resolve()
    fpMusic21 = fpThis.parent.parent  # common is two levels deep
    # use stream as a test case
    if 'stream' not in [x.name for x in fpMusic21.iterdir()]:
        raise Exception('cannot find expected music21 directory: %s' % fpMusic21)
    return fpMusic21


def getMetadataCacheFilePath():
    r'''
    Get the stored music21 directory that contains the corpus metadata cache.

    >>> fp = common.getMetadataCacheFilePath()
    >>> fp.name == '_metadataCache' and fp.parent.name == 'corpus'
    True

    :rtype: pathlib.Path
    '''
    return getSourceFilePath() / 'corpus' / '_metadataCache'


def getCorpusFilePath():
    r'''Get the stored music21 directory that contains the corpus metadata cache.

    >>> fp = common.getCorpusFilePath()
    >>> fp.name == 'corpus' and fp.parent.name == 'music21'
    True

    :rtype: pathlib.Path
    '''
    from music21 import corpus
    coreCorpus = corpus.corpora.CoreCorpus()
    if coreCorpus.manualCoreCorpusPath is None:
        return getSourceFilePath() / 'corpus'
    return pathlib.Path(coreCorpus.manualCoreCorpusPath)


def getCorpusContentDirs():
    '''
    Get all dirs that are found in the CoreCorpus that contain content;
    that is, exclude dirs that have code or other resources.

    >>> fp = common.getCorpusContentDirs()
    >>> fp  # this list will be fragile, depending on composition of dirs
    ['airdsAirs', 'bach', 'beach', 'beethoven', 'chopin',
     'ciconia', 'corelli', 'cpebach',
     'demos', 'essenFolksong', 'handel', 'haydn', 'joplin', 'josquin',
     'leadSheet', 'luca', 'miscFolk', 'monteverdi', 'mozart', 'nottingham-dataset',
     'oneills1850', 'palestrina',
     'ryansMammoth', 'schoenberg', 'schubert', 'schumann', 'schumann_clara',
     'theoryExercises', 'trecento', 'verdi', 'weber']

    Make sure that all corpus data has a directoryInformation tag in
    CoreCorpus.

    >>> cc = corpus.corpora.CoreCorpus()
    >>> failed = []
    >>> di = [d.directoryName for d in cc.directoryInformation]
    >>> for f in fp:
    ...     if f not in di:
    ...         failed.append(f)
    >>> failed
    []

    :rtype: List[str]
    '''
    directoryName = getCorpusFilePath()
    result = []
    # dirs to exclude; all files will be retained
    excludedNames = (
        'license.txt',
        '_metadataCache',
        '__pycache__',
    )
    for filename in sorted(os.listdir(directoryName)):
        if filename.endswith(('.py', '.pyc')):
            continue
        elif filename.startswith('.'):
            continue
        elif filename in excludedNames:
            continue
        result.append(filename)
    return sorted(result)


def getRootFilePath():
    '''
    Return the root directory for music21 -- outside of the music21 namespace
    which has directories such as "dist", "documentation", "music21"

    :rtype: pathlib.Path
    '''
    fpMusic21 = getSourceFilePath()
    fpParent = fpMusic21.parent
    return fpParent


def relativepath(path, start=None):
    '''
    A cross-platform wrapper for `os.path.relpath()`, which returns `path` if
    under Windows, otherwise returns the relative path of `path`.

    This avoids problems under Windows when the current working directory is
    on a different drive letter from `path`.

    :type path: str
    :type start: str
    :rtype: str
    '''
    import platform
    if platform == 'Windows':
        return path
    return os.path.relpath(path, start)


def cleanpath(path, *, returnPathlib=None):
    '''
    Normalizes the path by expanding ~user on Unix, ${var} environmental vars
    (is this a good idea?), expanding %name% on Windows, normalizing path names (Windows
    turns backslashes to forward slashes, and finally if that file is not an absolute path,
    turns it from a relative path to an absolute path.

    v5 -- returnPathlib -- None (default) does not convert. False, returns a string,
    True, returns a pathlib.Path.
    '''
    if isinstance(path, pathlib.Path):
        path = str(path)
        if returnPathlib is None:
            returnPathlib = True
    elif returnPathlib is None:
        returnPathlib = False
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    if not os.path.isabs(path):
        path = os.path.abspath(path)

    path = os.path.expandvars(path)
    if not returnPathlib:
        return path
    else:
        return pathlib.Path(path)


if __name__ == '__main__':
    import music21
    music21.mainTest()
