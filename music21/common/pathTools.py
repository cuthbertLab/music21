#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common/pathTools.py
# Purpose:      Utilities for paths
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
__all__ = [
           'getSourceFilePath',
           'getMetadataCacheFilePath',
           'getCorpusFilePath',
           'getCorpusContentDirs',
           'getPackageDir',
           'getPackageData',
           'relativepath', 
           'cleanpath',
           ]

import inspect
import os

#-------------------------------------------------------------------------------
def getSourceFilePath():
    '''
    Get the music21 directory that contains source files such as note.py, etc.. 
    This is not the same as the
    outermost package development directory.
    
    :rtype: str
    '''
    fpThis = inspect.getfile(getSourceFilePath)
    fpMusic21 = os.path.dirname(os.path.dirname(fpThis)) # common is two levels deep
    # use stream as a test case
    if 'stream' not in os.listdir(fpMusic21):
        raise Exception('cannot find expected music21 directory: %s' % fpMusic21)
    return fpMusic21



def getMetadataCacheFilePath():
    r'''Get the stored music21 directory that contains the corpus metadata cache.

    >>> fp = common.getMetadataCacheFilePath()
    >>> fp.endswith('corpus/_metadataCache') or fp.endswith(r'corpus\_metadataCache')
    True
    
    :rtype: str
    '''
    return os.path.join(getSourceFilePath(), 'corpus', '_metadataCache')


def getCorpusFilePath():
    r'''Get the stored music21 directory that contains the corpus metadata cache.

    >>> fp = common.getCorpusFilePath()
    >>> fp.endswith('music21/corpus') or fp.endswith(r'music21\corpus')
    True
    '''
    from music21 import corpus
    coreCorpus = corpus.corpora.CoreCorpus()
    if coreCorpus.manualCoreCorpusPath is None:
        return os.path.join(getSourceFilePath(), 'corpus')
    return coreCorpus.manualCoreCorpusPath


def getCorpusContentDirs():
    '''
    Get all dirs that are found in the corpus that contain content; 
    that is, exclude dirs that have code or other resources.

    >>> fp = common.getCorpusContentDirs()
    >>> fp # this test will be fragile, depending on composition of dirs
    ['airdsAirs', 'bach', 'beethoven', 'ciconia', 'corelli', 'cpebach',
    'demos', 'essenFolksong', 'handel', 'haydn', 'josquin', 'leadSheet',
    'luca', 'miscFolk', 'monteverdi', 'mozart', 'oneills1850', 'palestrina',
    'ryansMammoth', 'schoenberg', 'schumann', 'schumann_clara',
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
    
    '''
    directoryName = getCorpusFilePath()
    result = []
    # dirs to exclude; all files will be retained
    excludedNames = (
        'license.txt',
        '_metadataCache',
        '__pycache__',
        )
    for filename in os.listdir(directoryName):
        if filename.endswith(('.py', '.pyc')):
            continue
        elif filename.startswith('.'):
            continue
        elif filename in excludedNames:
            continue
        result.append(filename)
    return sorted(result)


def getPackageDir(fpMusic21=None, relative=True, remapSep='.',
                  packageOnly=True):
    '''
    Manually get all directories in the music21 package, 
    including the top level directory. This is used in setup.py.

    If `relative` is True, relative paths will be returned.

    If `remapSep` is set to anything other than None, the path separator will be replaced.

    If `packageOnly` is true, only directories with __init__.py files are collected.
    '''
    if fpMusic21 is None:
        fpMusic21 = getSourceFilePath()

    #fpCorpus = os.path.join(fpMusic21, 'corpus')
    fpParent = os.path.dirname(fpMusic21)
    match = []
    for dirpath, unused_dirnames, filenames in os.walk(fpMusic21):
        # remove hidden directories
        if ('%s.' % os.sep) in dirpath:
            continue
        elif '.git' in dirpath:
            continue
        if packageOnly:
            if '__init__.py' not in filenames: # must be to be a package
                continue
        # make relative
        if relative:
            fp = dirpath.replace(fpParent, '')
            if fp.startswith(os.sep):
                fp = fp[fp.find(os.sep)+len(os.sep):]
        else:
            fp = dirpath
        # replace os.sep
        if remapSep != None:
            fp = fp.replace(os.sep, remapSep)
        match.append(fp)
    return match


def getPackageData():
    '''
    Return a list of package data in 
    the format specified by setup.py. This creates a very inclusive list of all data types.
    '''
    # include these extensions for all directories, even if they are not normally there.
    # also need to update writeManifestTemplate() in setup.py when adding
    # new file extensions
    ext = ['txt', 'xml', 'krn', 'mxl', 'pdf', 'html',
           'css', 'js', 'png', 'tiff', 'jpg', 'xls', 'mid', 'abc', 'json', 'md',
           'zip', 'rntxt', 'command', 'scl', 'nwc', 'nwctxt', 'wav']

    # need all dirs, not just packages, and relative to music21
    fpList = getPackageDir(fpMusic21=None, relative=True, remapSep=None,
                            packageOnly=False)
    stub = 'music21%s' % os.sep
    match = []
    for fp in fpList:
        # these are relative to music21 package, so remove music21
        if fp == 'music21':
            continue
        elif fp.startswith(stub):
            fp = fp[fp.find(stub)+len(stub):]
        for e in ext:
            target = fp + os.sep + '*.%s' % e
            match.append(target)

    return match



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

def cleanpath(path):
    '''
    Normalizes the path by expanding ~user on Unix, ${var} environmental vars
    (is this a good idea?), expanding %name% on Windows, normalizing path names (Windows
    turns backslashes to forward slashes, and finally if that file is not an absolute path,
    turns it from a relative path to an absolute path.
    '''
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    path = os.path.normpath(path)
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    return path


if __name__ == '__main__':
    import music21
    music21.mainTest()
