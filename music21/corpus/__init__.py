# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         corpus/__init__.py
# Purpose:      Shortcuts to the corpus collection
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009, 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
The music21 corpus includes a collection of freely distributable
music in MusicXML, Humdrum, and other representations. The corpus
package is an interface for easily working with this data.

To see a complete listing of the works in the music21 corpus,
visit  :ref:`referenceCorpus`.  Note that music21 does not own
most of the music in the corpus -- it has been licensed to us (or
in a free license).  It may not be free in all parts of the world,
but to the best of our knowledge is true for the US.
'''
from __future__ import unicode_literals

import re
import os
import unittest
import zipfile

from music21 import common
from music21 import converter
from music21 import exceptions21
from music21 import metadata
from music21.corpus import chorales
from music21.corpus import virtual
from music21.corpus import corpora
from music21.corpus.corpora import *

from music21 import environment
_MOD = "corpus.base.py"
environLocal = environment.Environment(_MOD)


#------------------------------------------------------------------------------


class CorpusException(exceptions21.Music21Exception):
    pass


#------------------------------------------------------------------------------


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
    >>> 2550 < cpl < 2600
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

def getVirtualPaths(fileExtensions=None, expandExtensions=True):
    '''
    Get all paths in the virtual corpus that match a known extension.

    An extension of None will return all known extensions.

    >>> len(corpus.getVirtualPaths()) > 6
    True

    '''
    return corpora.VirtualCorpus().getPaths(
        fileExtensions=fileExtensions,
        expandExtensions=expandExtensions,
        )

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


def addPath(filePath):
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
    corpora.LocalCorpus().addPath(filePath)


def getPaths(
    fileExtensions=None,
    expandExtensions=True,
    name=('local', 'core', 'virtual'),
    ):
    '''
    Get paths from core, virtual, and/or local corpora.
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
    if 'virtual' in name:
        paths += corpora.VirtualCorpus().getPaths(
            fileExtensions=fileExtensions,
            expandExtensions=expandExtensions,
            )
    return paths


#------------------------------------------------------------------------------
# metadata routines


def _updateMetadataBundle():
    '''
    Load the metadata bundle from JSON and store it in the module global
    variable _METADATA_BUNDLES, unless the _METADATA_BUNDLES have already been
    built, in which case, don't do it.

    This relies on the functions `getCorePaths()`, `getVirtualPaths()`, and
    `getLocalPaths()`.

    Note that this updates the in-memory cached metdata bundles not the disk
    caches (that's MUCH slower!) to do that run corpus.metadata.metadata.py
    '''
    corpora.Corpus._updateAllMetadataBundles()


def cacheMetadata(corpusNames=('local',), verbose=True):
    '''
    Rebuild the metadata cache.
    '''
    if not common.isIterable(corpusNames):
        corpusNames = [corpusNames]
    for name in corpusNames:
        corpora.Corpus._metadataBundles[name] = None
    metadata.cacheMetadata(corpusNames, verbose=verbose)


def search(
    query,
    field=None,
    corpusNames=('core', 'virtual', 'local'),
    fileExtensions=None,
    ):
    r'''
    Search all stored metadata and return a list of file paths; to return a
    list of parsed Streams, use `searchParse()`.

    The `name` parameter can be used to specify one of three corpora: core
    (included with music21), virtual (defined in music21 but hosted online),
    and local (hosted on the user's system (not yet implemented)).

    This method uses stored metadata and thus, on first usage, will incur a
    performance penalty during metadata loading.
    
    >>> corpus.search('china')
    <music21.metadata.bundles.MetadataBundle {1235 entries}>

    >>> corpus.search('bach', field='composer')
    <music21.metadata.bundles.MetadataBundle {21 entries}>
   
    >>> corpus.search('coltrane', corpusNames=('virtual',))
    <music21.metadata.bundles.MetadataBundle {1 entry}>

    '''
    return corpora.Corpus.search(
        query,
        field=field,
        corpusNames=corpusNames,
        fileExtensions=fileExtensions,
        )


#------------------------------------------------------------------------------


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


def getComposerDir(composerName):
    '''
    Given the name of a composer, get the path to the top-level directory of
    that composer:

    >>> import os
    >>> a = corpus.getComposerDir('bach')
    >>> a.endswith(os.path.join('corpus', os.sep, 'bach'))
    True
    '''
    return corpora.CoreCorpus().getComposerDirectoryPath(composerName)


@property
def noCorpus():
    '''
    Return True or False if this is a `corpus` or `noCoprus` distribution.

    >>> corpus.noCorpus
    False

    '''
    return corpora.CoreCorpus.noCorpus

#------------------------------------------------------------------------------


def getWorkList(workName, movementNumber=None, fileExtensions=None):
    '''
    Search the corpus and return a list of filenames of works, always in a
    list.

    If no matches are found, an empty list is returned.

    >>> len(corpus.getWorkList('schumann_clara', 3, '.xml'))
    1

    Make sure that 'verdi' just gets the single Verdi piece and not the
    Monteverdi pieces:

    >>> len(corpus.getWorkList('verdi'))
    1

    '''
    return corpora.CoreCorpus().getWorkList(
        workName,
        movementNumber=movementNumber,
        fileExtensions=fileExtensions,
        )


def getVirtualWorkList(workName, movementNumber=None, fileExtensions=None):
    '''
    Given a work name, search all virtual works and return a list of URLs for
    any matches.


    >>> corpus.getVirtualWorkList('bach/bwv1007/prelude')
    ['http://kern.ccarh.org/cgi-bin/ksdata?l=cc/bach/cello&file=bwv1007-01.krn&f=xml']

    >>> corpus.getVirtualWorkList('junk')
    []

    '''
    return corpora.VirtualCorpus().getWorkList(
        workName,
        movementNumber=movementNumber,
        fileExtensions=fileExtensions,
        )


#------------------------------------------------------------------------------


def getWorkReferences():
    '''
    Return a data dictionary for all works in the corpus 
    Returns a list of corpus.corpora.DirectoryInformation object, one
    for each directory. A 'works' dictionary for each composer
    provides references to dictionaries for all associated works.

    This is used in the generation of corpus documentation

    >>> workRefs = corpus.getWorkReferences()
    >>> workRefs[1:3]
    [<music21.corpus.corpora.DirectoryInformation bach>, 
     <music21.corpus.corpora.DirectoryInformation beethoven>]
     
    No longer finds the VirtualCorpus. TODO: Reinstate when
    that corpus becomes useful again...
    '''
    results = [di for di in corpora.CoreCorpus().directoryInformation]

#     for vw in corpora.VirtualCorpus._virtual_works:
#         composerDir = vw.corpusPath.split('/')[0]
#         match = False
#         for ref in results:
#             # check composer reference or first part of corpusPath
#             if (ref['composer'] == vw.composer or
#                 composerDir == ref['composerDir']):
#                 match = True
#                 break  # use this ref
#         if not match:  # new composers, create a new ref
#             ref = {}
#             ref['composer'] = vw.composer
#             ref['composerDir'] = composerDir
#             ref['works'] = {}  # store by keys of name/dirname
#         # work stub should be everything other than top-level
#         workStub = vw.corpusPath.replace(composerDir + '/', '')
#         ref['works'][workStub] = {}
#         ref['works'][workStub]['virtual'] = True
#         ref['works'][workStub]['files'] = []
#         ref['works'][workStub]['title'] = vw.title
#         for url in vw.urlList:
#             m21Format, ext = common.findFormatExtURL(url)
#             fileDict = {}
#             fileDict['format'] = m21Format
#             fileDict['ext'] = ext
#             # all path parts after corpus
#             fileDict['corpusPath'] = vw.corpusPath
#             fileDict['title'] = vw.title
#             fileDict['url'] = url
#             ref['works'][workStub]['files'].append(fileDict)
#         if not match:  # not found already, need to add
#             results.append(ref)
    return results


#------------------------------------------------------------------------------


def getWork(workName, movementNumber=None, fileExtensions=None):
    '''
    Search the corpus, then the virtual corpus, for a work, and return a file
    path or URL.  N.B. does not parse the work: but it's suitable for passing
    to converter.parse.

    This method will return either a list of file paths or, if there is a
    single match, a single file path. If no matches are found an Exception is
    raised.

    >>> import os
    >>> a = corpus.getWork('luca/gloria')
    >>> a.endswith(os.path.sep.join([
    ...     'luca', 'gloria.xml']))
    True

    >>> trecentoFiles = corpus.getWork('trecento')
    >>> len(trecentoFiles) > 100 and len(trecentoFiles) < 200
    True

    '''
    if not common.isListLike(fileExtensions):
        fileExtensions = [fileExtensions]
    results = getWorkList(workName, movementNumber, fileExtensions)
    if len(results) == 0:
        if common.isListLike(workName):
            workName = os.path.sep.join(workName)
        if workName.endswith(".xml"):  # might be compressed MXL file
            newWorkName = workName[0:len(workName) - 4] + ".mxl"
            return getWork(newWorkName, movementNumber, fileExtensions)
        results = getVirtualWorkList(workName, movementNumber, fileExtensions)
    if len(results) == 1:
        return results[0]
    elif len(results) == 0:
        raise CorpusException(
            'Could not find a file/url that met these criteria')
    return results


def parse(
    workName,
    movementNumber=None,
    number=None,
    fileExtensions=None,
    forceSource=False,
    format=None # @ReservedAssignment
    ):
    '''
    The most important method call for corpus.

    Similar to the :meth:`~music21.converter.parse` method of converter (which
    takes in a filepath on the local hard drive), this method searches the
    corpus (including the virtual corpus) for a work fitting the workName
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
    return corpora.Corpus.parse(
        workName,
        movementNumber=movementNumber,
        number=number,
        fileExtensions=fileExtensions,
        forceSource=forceSource,
        format=format
        )


def _addCorpusFilepath(streamObj, filePath):
    # metadata attribute added to store the file path,
    # for use later in identifying the score
    #if streamObj.metadata == None:
    #    streamObj.insert(metadata.Metadata())
    corpusFilePath = common.getCorpusFilePath()
    lenCFP = len(corpusFilePath) + len(os.sep)
    if filePath.startswith(corpusFilePath):
        fp2 = filePath[lenCFP:]
        ### corpus fix for windows
        dirsEtc = fp2.split(os.sep)
        fp3 = '/'.join(dirsEtc)
        streamObj.corpusFilepath = fp3
    else:
        streamObj.corpusFilepath = filePath


@common.deprecated("1999?","by early 2016", "Use corpus.parse() instead.")
def parseWork(*arguments, **keywords):
    '''
    This function exists for backwards compatibility.

    All calls should use :func:`~music21.corpus.parse` instead.
    '''
    return parse(*arguments, **keywords)


#------------------------------------------------------------------------------
# compression


def compressAllXMLFiles(deleteOriginal=False):
    '''
    Takes all filenames in corpus.paths and runs
    :meth:`music21.corpus.compressXML` on each.  If the musicXML files are
    compressed, the originals are deleted from the system.
    '''
    environLocal.warn("Compressing musicXML files...")
    for filename in getPaths(fileExtensions=('.xml',)):
        compressXML(filename, deleteOriginal=deleteOriginal)
    environLocal.warn(
        'Compression complete. '
        'Run the main test suite, fix bugs if necessary,'
        'and then commit modified directories in corpus.'
        )


def compressXML(filename, deleteOriginal=False):
    '''
    Takes a filename, and if the filename corresponds to a musicXML file with
    an .xml extension, creates a corresponding compressed .mxl file in the same
    directory.

    If deleteOriginal is set to True, the original musicXML file is deleted
    from the system.
    '''
    if not filename.endswith('.xml'):
        return  # not a musicXML file
    environLocal.warn("Updating file: {0}".format(filename))
    filenameList = filename.split(os.path.sep)
    # find the archive name (name w/out filepath)
    archivedName = filenameList.pop()
    # new archive name
    filenameList.append(archivedName[0:len(archivedName) - 4] + ".mxl")
    newFilename = os.path.sep.join(filenameList)  # new filename
    # contents of container.xml file in META-INF folder
    container = '<?xml version="1.0" encoding="UTF-8"?>\n\
<container>\n\
  <rootfiles>\n\
    <rootfile full-path="{0}"/>\n\
  </rootfiles>\n\
</container>\n\
    '.format(archivedName)
    # Export container and original xml file to system as a compressed XML.
    with zipfile.ZipFile(
        newFilename,
        'w',
        compression=zipfile.ZIP_DEFLATED,
        ) as myZip:
        myZip.write(filename=filename, archivedName=archivedName)
        myZip.writestr(
            zinfo_or_archivedName='META-INF{0}container.xml'.format(
                os.path.sep),
            bytes=container,
            )
    # Delete uncompressed xml file from system
    if deleteOriginal:
        os.remove(filename)


def uncompressMXL(filename, deleteOriginal=False):
    '''
    Takes a filename, and if the filename corresponds to a compressed musicXML
    file with an .mxl extension, creates a corresponding uncompressed .xml file
    in the same directory.

    If deleteOriginal is set to True, the original compressed musicXML file is
    deleted from the system.
    '''
    if not filename.endswith(".mxl"):
        return  # not a musicXML file
    environLocal.warn("Updating file: {0}".format(filename))
    filenames = filename.split(os.path.sep)
    # find the archive name (name w/out filepath)
    archivedName = filenames.pop()

    unarchivedName = os.path.splitext(archivedName)[0] + '.xml'
    extractPath = os.path.sep.join(filenames)
    # Export container and original xml file to system as a compressed XML.
    with zipfile.ZipFile(
        filename,
        'r',
        compression=zipfile.ZIP_DEFLATED,
        ) as myZip:
        myZip.extract(member=unarchivedName, path=extractPath)
    # Delete uncompressed xml file from system
    if deleteOriginal:
        os.remove(filename)


#------------------------------------------------------------------------------
# libraries


# additional libraries to define


def getBachChorales(fileExtensions='xml'):
    r'''
    Return the file name of all Bach chorales.

    By default, only Bach Chorales in xml format are returned, because the
    quality of the encoding and our parsing of those is superior.

    N.B. Look at the module corpus.chorales for many better ways to work with
    the chorales.

    >>> a = corpus.getBachChorales()
    >>> len(a) > 400
    True

    >>> a = corpus.getBachChorales('krn')
    >>> len(a) > 10
    False

    >>> a = corpus.getBachChorales('xml')
    >>> len(a) > 400
    True

    >>> #_DOCS_SHOW a[0]
    >>> '/Users/cuthbert/Documents/music21/corpus/bach/bwv1.6.mxl' #_DOCS_HIDE
    '/Users/cuthbert/Documents/music21/corpus/bach/bwv1.6.mxl'

    '''
    cc = corpora.CoreCorpus()
    return cc.getBachChorales(fileExtensions=fileExtensions,)


def getMonteverdiMadrigals(fileExtensions='xml'):
    '''
    Return a list of the filenames of all Monteverdi madrigals.

    >>> a = corpus.getMonteverdiMadrigals()
    >>> len(a) > 40
    True

    '''
    return corpora.CoreCorpus().getMonteverdiMadrigals(
        fileExtensions=fileExtensions,
        )

#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest()
