# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         corpus/manager.py
# Purpose:      Manage multiple corpora
#
# Authors:      Christopher Ariza
#               Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009, 2013, 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------

from music21 import environment
from music21 import metadata

from music21.corpus import corpora

_metadataBundles = {
    'core': None,
    'local': None,
    'virtual': None,
    }

#------------------------------------------------------------------------------
def iterateCorpora(returnObjects=True):
    '''
    a generator that iterates over the corpora (either as objects or as names)
    for use in pan corpus searching.
    
    This test will only show the first three, because it needs to run the same
    on every system:
    
    >>> for i, corpusObject in enumerate(corpus.manager.iterateCorpora()):
    ...     print(corpusObject)
    ...     if i == 2:
    ...        break
    <music21.corpus.corpora.CoreCorpus>
    <music21.corpus.corpora.VirtualCorpus>
    <music21.corpus.corpora.LocalCorpus: 'local'>    

    We can also get names instead... Note that the name of the main localcorpus is 'local' not
    None

    >>> for i, corpusName in enumerate(corpus.manager.iterateCorpora(returnObjects=False)):
    ...     print(corpusName)
    ...     if i == 2:
    ...        break
    core
    virtual
    local
    
    New in v.3 
    '''
    if returnObjects is True:
        yield corpora.CoreCorpus()
        yield corpora.VirtualCorpus()
        for cn in listLocalCorporaNames():
            yield corpora.LocalCorpus(cn)
    else:
        yield corpora.CoreCorpus().name
        yield corpora.VirtualCorpus().name
        for cn in listLocalCorporaNames():
            if cn is None:
                yield 'local'
            else:
                yield cn

def search(
    query,
    field=None,
    corpusNames=None,
    fileExtensions=None,
    ):
    '''
    Search all stored metadata bundles and return a list of file paths.

    The ``names`` parameter can be used to specify which corpora to search,
    for example:

    >>> corpus.manager.search(
    ...     'bach',
    ...     corpusNames=('core', 'virtual'),
    ...     )
    <music21.metadata.bundles.MetadataBundle {150 entries}>

    If ``names`` is None, all corpora known to music21 will be searched.

    This method uses stored metadata and thus, on first usage, will incur a
    performance penalty during metadata loading.
    '''
    updateAllMetadataBundles()
    allSearchResults = metadata.bundles.MetadataBundle()
    
    if corpusNames is None:
        corpusNames = list(iterateCorpora(returnObjects=False))
    
    for corpusName in corpusNames:
        if corpusName in _metadataBundles:
            searchResults = _metadataBundles[corpusName].search(
                query, field, fileExtensions=fileExtensions)
            allSearchResults = allSearchResults.union(searchResults)
    
    return allSearchResults


def getMetadataBundleByCorpus(corpusObject):
    '''
    Return the metadata bundle for a single Corpus object
    
    >>> vc = corpus.corpora.VirtualCorpus()
    >>> mdb1 = corpus.manager.getMetadataBundleByCorpus(vc)
    >>> mdb1
    <music21.metadata.bundles.MetadataBundle 'virtual': {11 entries}>
    
    This is the same as calling `metadataBundle` on the corpus itself,
    but this is the routine that actually does the work:
    
    >>> mdb1 is vc.metadataBundle
    True
    '''
    updateMetadataBundle(corpusObject)
    cacheName = corpusObject.cacheName
    return _metadataBundles[cacheName]

def updateMetadataBundle(corpusObject):
    r'''
    Update a corpus' metadata bundle from its stored JSON file on disk.


    '''
    corpusCacheName = corpusObject.cacheName
    if (corpusCacheName not in _metadataBundles or
            _metadataBundles[corpusCacheName] is None):
        metadataBundle = metadata.bundles.MetadataBundle(corpusCacheName)
        metadataBundle.read()
        metadataBundle.validate()
        _metadataBundles[corpusCacheName] = metadataBundle


def updateAllMetadataBundles():
    '''
    Update each corpus's metadata bundle.
    '''
    for corpusObject in iterateCorpora():
        updateMetadataBundle(corpusObject)

def listLocalCorporaNames():
    '''
    List the names of all user-defined local corpora.

    The entry for None refers to the default local corpus.
    '''
    userSettings = environment.UserSettings()
    result = [None]
    result.extend(userSettings['localCorporaSettings'].keys())
    return result


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest()
