# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         corpus/manager.py
# Purpose:      Manage multiple corpora
#
# Authors:      Christopher Ariza
#               Josiah Wolf Oberholtzer
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2009, 2013, 2015-17 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
The manager module handles requests across multiple corpora.  It should be the default
interface to searching corpora.

New in v3 -- previously most were static methods on corpus.corpora.Corpus, but that
seemed inappropriate since these work across corpora.
'''
from __future__ import annotations

from collections.abc import Iterable
import pathlib
import os
import typing as t

from music21 import common
from music21 import converter
from music21.exceptions21 import CorpusException
from music21 import environment
from music21 import metadata

from music21.corpus import corpora


if t.TYPE_CHECKING:
    from music21.metadata import bundles
    from music21 import stream


_metadataBundles: dict[str, bundles.MetadataBundle | None] = {
    'core': None,
    'local': None,
    # 'virtual': None,
}

# -----------------------------------------------------------------------------


def fromName(name):
    '''
    Instantiate a specific corpus based on `name`:

    >>> corpus.manager.fromName('core')
    <music21.corpus.corpora.CoreCorpus>

    >>> corpus.manager.fromName('local')
    <music21.corpus.corpora.LocalCorpus: 'local'>

    >>> corpus.manager.fromName(None)
    <music21.corpus.corpora.LocalCorpus: 'local'>


    Note that this corpus probably does not exist on disk, but it's ready to have
    paths added to it and to be stored on disk.

    >>> corpus.manager.fromName('testDummy')
    <music21.corpus.corpora.LocalCorpus: 'testDummy'>
    '''
    # >>> corpus.manager.fromName('virtual')
    # <music21.corpus.corpora.VirtualCorpus>

    if name == 'core':
        return corpora.CoreCorpus()
    # elif name == 'virtual':
    #     return corpora.VirtualCorpus()
    elif name == 'local':
        return corpora.LocalCorpus()
    else:
        return corpora.LocalCorpus(name=name)


def iterateCorpora(returnObjects=True):
    '''
    a generator that iterates over the corpora (either as objects or as names)
    for use in pan corpus searching.

    This test will only show the first two, because it needs to run the same
    on every system:

    >>> for i, corpusObject in enumerate(corpus.manager.iterateCorpora()):
    ...     print(corpusObject)
    ...     if i == 1:
    ...        break
    <music21.corpus.corpora.CoreCorpus>
    <music21.corpus.corpora.LocalCorpus: 'local'>

    We can also get names instead... Note that the name of the main local corpus is 'local' not
    None

    >>> for i, corpusName in enumerate(corpus.manager.iterateCorpora(returnObjects=False)):
    ...     print(corpusName)
    ...     if i == 1:
    ...        break
    core
    local

    * New in v3.
    '''
    if returnObjects is True:
        yield corpora.CoreCorpus()
        # yield corpora.VirtualCorpus()
        for cn in listLocalCorporaNames():
            yield corpora.LocalCorpus(cn)
    else:
        yield corpora.CoreCorpus().name
        # yield corpora.VirtualCorpus().name
        for cn in listLocalCorporaNames():
            if cn is None:
                yield 'local'
            else:
                yield cn


def getWork(
    workName: str | pathlib.Path,
    movementNumber: int | None = None,
    *,
    fileExtensions: Iterable[str] = (),
) -> pathlib.Path | list[pathlib.Path]:
    '''
    this parse function is called from `corpus.parse()` and does nothing differently from it.

    Searches all corpora for a file that matches the name and returns it parsed.
    '''
    addXMLWarning = False
    workNameJoined = str(workName)
    mxlWorkName = workNameJoined

    if not workName:
        raise CorpusException('a work name must be provided as an argument')

    if workNameJoined.endswith('.xml') or workNameJoined.endswith('.musicxml'):
        # might be compressed MXL file
        mxlWorkName = os.path.splitext(workNameJoined)[0] + '.mxl'
        addXMLWarning = True

    filePaths = None
    for corpusObject in iterateCorpora():
        workList = corpusObject.getWorkList(workName,
                                            movementNumber,
                                            fileExtensions=fileExtensions)
        if not workList and addXMLWarning:
            workList = corpusObject.getWorkList(mxlWorkName,
                                                movementNumber,
                                                fileExtensions=fileExtensions)
            if not workList:
                continue
        if workList:
            filePaths = workList
            break

    if filePaths is None:
        warningMessage = 'Could not find a'
        if addXMLWarning:
            warningMessage += 'n xml, musicxml, or mxl'
        warningMessage += f' work that met this criterion: {workName};'
        warningMessage += ' if you are searching for a file on disk, '
        warningMessage += 'use "converter" instead of "corpus".'
        raise CorpusException(warningMessage)

    if len(filePaths) == 1:
        return pathlib.Path(filePaths[0])
    else:
        return [pathlib.Path(p) for p in filePaths]


# pylint: disable=redefined-builtin
# noinspection PyShadowingBuiltins
def parse(
    workName: str | pathlib.Path,
    *,
    movementNumber: int | None = None,
    number: int | None = None,
    fileExtensions: Iterable[str] = (),
    forceSource: bool = False,
    format: str | None = None,
) -> stream.Score | stream.Part | stream.Opus:
    filePaths = getWork(
        workName=workName,
        movementNumber=movementNumber,
        fileExtensions=fileExtensions,
    )
    if isinstance(filePaths, list):
        filePath = filePaths[0]
    else:
        filePath = filePaths

    streamObject = converter.parse(
        filePath,
        forceSource=forceSource,
        number=number,
        format=format
    )
    _addCorpusFilePathToStreamObject(streamObject, filePath)
    return streamObject


def _addCorpusFilePathToStreamObject(streamObj, filePath):
    '''
    Adds an entry 'corpusFilePpath' to the Stream object.

    TODO: this should work for non-core-corpora
    TODO: this should be in the metadata object
    TODO: this should set a pathlib.Path object
    '''
    # metadata attribute added to store the file path,
    # for use later in identifying the score
    # if streamObj.metadata == None:
    #    streamObj.insert(metadata.Metadata())
    corpusFilePath = str(common.getCorpusFilePath())
    lenCFP = len(corpusFilePath) + len(os.sep)
    filePath = str(filePath)

    if filePath.startswith(corpusFilePath):
        fp2 = filePath[lenCFP:]
        # corpus fix for windows
        dirsEtc = fp2.split(os.sep)
        fp3 = '/'.join(dirsEtc)
        streamObj.metadata.corpusFilePath = fp3
    else:
        streamObj.metadata.corpusFilePath = filePath

    if isinstance(streamObj.id, int):
        streamObj.id = streamObj.metadata.corpusFilePath


def search(
    query: str | None = None,
    field: str | None = None,
    *,
    corpusNames=None,
    fileExtensions: Iterable[str] | str = (),
    **keywords
):
    '''
    Search all stored metadata bundles and return a list of file paths.

    This function uses stored metadata and thus, on first usage, will incur a
    performance penalty during metadata loading.

    >>> #_DOCS_SHOW corpus.search('china')
    >>> corpus.search('china', corpusNames=('core',))  #_DOCS_HIDE
    <music21.metadata.bundles.MetadataBundle {1235 entries}>

    >>> #_DOCS_SHOW corpus.search('china', fileExtensions=('.mid',))
    >>> corpus.search('china', fileExtensions=('.mid',), corpusNames=('core',))  #_DOCS_HIDE
    <music21.metadata.bundles.MetadataBundle {0 entries}>

    >>> #_DOCS_SHOW corpus.search('bach', field='composer')
    >>> corpus.search('bach', field='composer', corpusNames=('core',))  #_DOCS_HIDE
    <music21.metadata.bundles.MetadataBundle {363 entries}>

    Note the importance of good metadata -- there's almost 400 pieces by
    Bach in the corpus, but many do not have correct metadata entries.

    This can also be specified as:

    >>> #_DOCS_SHOW corpus.search(composer='bach')
    >>> corpus.search(composer='bach', corpusNames=('core',))  #_DOCS_HIDE
    <music21.metadata.bundles.MetadataBundle {363 entries}>

    Or, to get all the chorales (without using `corpus.chorales.Iterator`):

    >>> #_DOCS_SHOW corpus.search(sourcePath='bach', numberOfParts=4)
    >>> corpus.search(sourcePath='bach', numberOfParts=4, corpusNames=('core',))  #_DOCS_HIDE
    <music21.metadata.bundles.MetadataBundle {368 entries}>


    This function is implemented in `corpus.manager` as a method there but also directly
    available in the corpus module for ease of use.

    The ``corpusNames`` parameter can be used to specify which corpora to search,
    for example:

    >>> corpus.manager.search(
    ...     'bach',
    ...     corpusNames=('core',),
    ...     )
    <music21.metadata.bundles.MetadataBundle {564 entries}>

    >>> corpus.manager.search(
    ...     'bach',
    ...     corpusNames=('core',),
    ...     fileExtensions=('xml',),
    ...     )
    <music21.metadata.bundles.MetadataBundle {412 entries}>

    If ``corpusNames`` is None, all corpora known to music21 will be searched.

    See usersGuide (chapter 11) for more information on searching

    '''
    # >>> corpus.search('coltrane', corpusNames=('virtual',))
    # <music21.metadata.bundles.MetadataBundle {1 entry}>
    if isinstance(fileExtensions, str):
        fileExtensions = (fileExtensions,)

    readAllMetadataBundlesFromDisk()
    allSearchResults = metadata.bundles.MetadataBundle()

    if corpusNames is None:
        corpusNames = list(iterateCorpora(returnObjects=False))

    for corpusName in corpusNames:
        c = fromName(corpusName)
        searchResults = c.metadataBundle.search(
            query,
            field,
            fileExtensions=fileExtensions,
            **keywords,
        )
        allSearchResults = allSearchResults.union(searchResults)

    return allSearchResults


def getMetadataBundleByCorpus(corpusObject: corpora.Corpus) -> bundles.MetadataBundle:
    '''
    Return the metadata bundle for a single Corpus object

    >>> cc = corpus.corpora.CoreCorpus()
    >>> mdb1 = corpus.manager.getMetadataBundleByCorpus(cc)
    >>> mdb1
    <music21.metadata.bundles.MetadataBundle 'core': {... entries}>

    This is the same as calling `metadataBundle` on the corpus itself,
    but this is the routine that actually does the work. In other words,
    it's the call on the object that is redundant, not this routine.

    >>> mdb1 is cc.metadataBundle
    True

    Non-existent corpus...

    >>> lc = corpus.corpora.LocalCorpus('junk')
    >>> mdb1 = corpus.manager.getMetadataBundleByCorpus(lc)
    >>> mdb1
    <music21.metadata.bundles.MetadataBundle 'junk': {0 entries}>
    '''
    cacheMetadataBundleFromDisk(corpusObject)
    corpusName = corpusObject.name
    if corpusName in _metadataBundles:
        mdb = _metadataBundles[corpusName]
        if t.TYPE_CHECKING:
            assert mdb is not None  # cacheMetadataBundleFromDisk makes None impossible
        return mdb
    else:  # pragma: no cover
        raise CorpusException('No metadata bundle found for corpus {0} with name {1}'.format(
            corpusObject, corpusName))


def cacheMetadataBundleFromDisk(corpusObject: corpora.Corpus) -> None:
    r'''
    Update a corpus' metadata bundle from its stored JSON file on disk.
    '''
    corpusName = corpusObject.name
    if (corpusName not in _metadataBundles
            or _metadataBundles[corpusName] is None):
        metadataBundle = metadata.bundles.MetadataBundle(corpusName)
        metadataBundle.read()
        metadataBundle.validate()
        _metadataBundles[corpusName] = metadataBundle

def readAllMetadataBundlesFromDisk():
    '''
    Read each corpus's metadata bundle and store it in memory.
    '''
    for corpusObject in iterateCorpora():
        cacheMetadataBundleFromDisk(corpusObject)


def listLocalCorporaNames(skipNone=False):
    '''
    List the names of all user-defined local corpora.

    The entry for None refers to the default local corpus.
    '''
    userSettings = environment.UserSettings()
    if not skipNone:
        result = [None]
    else:
        result = []
    result.extend(userSettings['localCorporaSettings'].keys())
    return result


def listSearchFields():
    r'''
    List all available search field names:

    >>> for field in corpus.manager.listSearchFields():
    ...     field
    ...
    'abstract'
    'accessRights'
    'accompanyingMaterialWriter'
    ...
    'composer'
    'composerAlias'
    'composerCorporate'
    'conceptor'
    'conductor'
    ...
    'dateCreated'
    'dateFirstPublished'
    'dateIssued'
    'dateModified'
    'dateSubmitted'
    'dateValid'
    ...
    'tempoFirst'
    'tempos'
    'textLanguage'
    'textOriginalLanguage'
    'timeSignatureFirst'
    'timeSignatures'
    'title'
    ...
    '''
    return metadata.bundles.MetadataBundle.listSearchFields()

# -----------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest()
