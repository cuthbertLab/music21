# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         corpus/__init__.py
# Purpose:      Shortcuts to the corpus collection
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009, 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
The music21 corpus includes a collection of freely distributable
music in MusicXML, Humdrum, and other representations. The corpus
package is an interface for easily working with this data.

To see a complete listing of the works in the music21 corpus,
visit  :ref:`referenceCorpus`.  Note that music21 does not own
most of the music in the corpus -- it has been licensed to us (or
in a free license).  It may not be free in all parts of the world,
but to the best of our knowledge is true for the US.

Use `corpus.parse` if you know the name of a file in the corpus:

>>> b = corpus.parse('bwv66.6')
>>> b
<music21.stream.Score 0x1050ce920>

And use `corpus.search` if you do not:

>>> cb = corpus.search('shandy')
>>> cb
<music21.metadata.bundles.MetadataBundle {1 entry}>
>>> cb[0]
<music21.metadata.bundles.MetadataEntry 'airdsAirs_book1_abc_191'>
>>> cb[0].parse()
<music21.stream.Score 0x1050ce940>
'''
__all__ = [
    'chorales', 'corpora', 'manager',
    # virtual
    'work',
    'parse',
    'getCorePaths',
    # 'getVirtualPaths',
    'getLocalPaths',
    'addPath',
    'getPaths',
    'cacheMetadata',
    'getComposer',
    'noCorpus',
    'getWork',

]

import re
import os
import unittest

from music21 import common
from music21 import converter
from music21 import exceptions21
from music21 import metadata

from music21.corpus import chorales
from music21.corpus import corpora
from music21.corpus import manager
from music21.corpus import virtual
from music21.corpus import work

from music21.corpus.manager import search
from music21.exceptions21 import CorpusException

from music21 import environment
_MOD = 'corpus'
environLocal = environment.Environment(_MOD)


# -----------------------------------------------------------------------------


def getCorePaths(fileExtensions=None, expandExtensions=True):
    '''
    Get all paths in the corpus that match a known extension, or an extenion
    provided by an argument.

    If `expandExtensions` is True, a format for an extension, and related
    extensions, will replaced by all known input extensions.

    This is convenient when an input format might match for multiple
    extensions.

    >>> corpusFilePaths = corpus.getCorePaths()
    >>> cpl = len(corpusFilePaths)
    >>> 3000 < cpl < 4000
    True

    >>> kernFilePaths = corpus.getCorePaths('krn')
    >>> len(kernFilePaths) >= 500
    True

    >>> abcFilePaths = corpus.getCorePaths('abc')
    >>> len(abcFilePaths) >= 100
    True

    '''
    return corpora.CoreCorpus().getPaths(
        fileExtensions=fileExtensions,
        expandExtensions=expandExtensions,
    )

# def getVirtualPaths(fileExtensions=None, expandExtensions=True):
#     '''
#     Get all paths in the virtual corpus that match a known extension.
#
#     An extension of None will return all known extensions.
#
#     >>> len(corpus.getVirtualPaths()) > 6
#     True
#
#     '''
#     return corpora.VirtualCorpus().getPaths(
#         fileExtensions=fileExtensions,
#         expandExtensions=expandExtensions,
#         )


def getLocalPaths(fileExtensions=None, expandExtensions=True):
    '''
    Access files in additional directories supplied by the user and defined in
    environment settings in the 'localCorpusSettings' list.

    If additional paths are added on a per-session basis with the
    :func:`~music21.corpus.addPath` function, these paths are also returned
    with this method.
    '''
    return corpora.LocalCorpus().getPaths(
        fileExtensions=fileExtensions,
        expandExtensions=expandExtensions,
    )


def addPath(filePath, corpusName=None):
    '''
    Add a directory path to the Local Corpus on a *temporary* basis, i.e., just
    for the current Python session.

    All directories contained within the provided directory will be searched
    for files with file extensions matching the currently readable file types.
    Any number of file paths can be added one at a time.

    An error will be raised if the file path does not exist, is already defined
    as a temporary, or is already being searched by being defined with the
    :class:`~music21.environment.Environment` 'localCorpusSettings' setting.

    To permanently add a path to the list of stored local corpus paths,
    set the 'localCorpusPath' or 'localCorpusSettings' setting of
    the :class:`~music21.environment.UserSettings` object.

    >>> #_DOCS_SHOW corpus.addPath('~/Documents')

    Alternatively, add a directory permanently (see link above
    for more details):

    >>> #_DOCS_SHOW us = environment.UserSettings()
    >>> #_DOCS_SHOW us['localCorpusPath'] = 'd:/desktop/'

    Restart music21 after adding paths.
    '''
    corpora.LocalCorpus(corpusName).addPath(filePath)


def getPaths(
    fileExtensions=None,
    expandExtensions=True,
    name=('local', 'core'),  # , 'virtual'
):
    '''
    Get paths from core and/or local corpora.
    This is the public interface for getting all corpus
    paths with one function.
    '''
    paths = []
    if 'core' in name:
        paths += corpora.CoreCorpus().getPaths(
            fileExtensions=fileExtensions,
            expandExtensions=expandExtensions,
        )
    if 'local' in name:
        paths += corpora.LocalCorpus().getPaths(
            fileExtensions=fileExtensions,
            expandExtensions=expandExtensions,
        )
    # if 'virtual' in name:
    #     paths += corpora.VirtualCorpus().getPaths(
    #         fileExtensions=fileExtensions,
    #         expandExtensions=expandExtensions,
    #         )
    return paths


# -----------------------------------------------------------------------------
# metadata routines


def cacheMetadata(corpusNames=('local',), verbose=True):
    '''
    Rebuild the metadata cache.
    '''
    if not common.isIterable(corpusNames):
        corpusNames = [corpusNames]
    for name in corpusNames:
        # todo -- create cache names for local corpora
        manager._metadataBundles[name] = None
    metadata.caching.cacheMetadata(corpusNames, verbose=verbose)


# -----------------------------------------------------------------------------


def getComposer(composerName, fileExtensions=None):
    '''
    Return all filenames in the corpus that match a composer's or a
    collection's name. An `fileExtensions`, if provided, defines which
    extensions are returned. An `fileExtensions` of None (default) returns all
    extensions.

    Note that xml and mxl are treated equivalently.

    >>> a = corpus.getComposer('schoenberg')
    >>> len(a) > 1
    True

    >>> a = corpus.getComposer('bach', 'krn')
    >>> len(a) < 10
    True

    >>> a = corpus.getComposer('bach', 'xml')
    >>> len(a) > 10
    True

    '''
    return corpora.CoreCorpus().getComposer(
        composerName,
        fileExtensions=fileExtensions,
    )


def noCorpus():
    '''
    Return True or False if this is a `corpus` or `noCorpus` distribution.

    >>> corpus.noCorpus()
    False

    '''
    return corpora.CoreCorpus().noCorpus


# -----------------------------------------------------------------------------


def getWork(workName, movementNumber=None, fileExtensions=None):
    '''
    Search all Corpora for a work, and return a file
    path or URL.  N.B. does not parse the work: but it's suitable for passing
    to converter.parse.

    This method will return either a list of file paths or, if there is a
    single match, a single file path. If no matches are found an Exception is
    raised.

    returns a pathlib.Path object

    >>> import os
    >>> a = corpus.getWork('luca/gloria')
    >>> a.name
    'gloria.xml'

    >>> a.parent.name
    'luca'

    >>> trecentoFiles = corpus.getWork('trecento')
    >>> 100 < len(trecentoFiles) < 200
    True
    '''
    return manager.getWork(workName, movementNumber, fileExtensions)


# pylint: disable=redefined-builtin
# noinspection PyShadowingBuiltins
def parse(workName,
            movementNumber=None,
            number=None,
            fileExtensions=None,
            forceSource=False,
            format=None  # @ReservedAssignment
          ):
    '''
    The most important method call for corpus.

    Similar to the :meth:`~music21.converter.parse` method of converter (which
    takes in a filepath on the local hard drive), this method searches the
    corpus (including local corpora) for a work fitting the workName
    description and returns a :class:`music21.stream.Stream`.

    If `movementNumber` is defined, and a movement is included in the corpus,
    that movement will be returned.

    If `number` is defined, and the work is a collection with multiple
    components, that work number will be returned.  For instance, some of our
    ABC documents contain dozens of folk songs within a single file.

    Advanced: if `forceSource` is True, the original file will always be loaded
    freshly and pickled (e.g., pre-parsed) files will be ignored.  This should
    not be needed if the file has been changed, since the filetime of the file
    and the filetime of the pickled version are compared.  But it might be
    needed if the music21 parsing routine has changed.

    Example, get a chorale by Bach.  Note that the source type does not need to
    be specified, nor does the name Bach even (since it's the only piece with
    the title BWV 66.6)

    >>> bachChorale = corpus.parse('bwv66.6')
    >>> len(bachChorale.parts)
    4

    After parsing, the file path within the corpus is stored as
    `.corpusFilePath`

    >>> bachChorale.corpusFilepath
    'bach/bwv66.6.mxl'
    '''
    return manager.parse(
        workName=workName,
        movementNumber=movementNumber,
        number=number,
        fileExtensions=fileExtensions,
        forceSource=forceSource,
        format=format  # @ReservedAssignment
    )


if __name__ == '__main__':
    import music21
    music21.mainTest()
