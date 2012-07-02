# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         corpus/base.py
# Purpose:      Access to the corpus collection
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
The music21 corpus provides a collection of freely distributable 
music in MusicXML, Humdrum, and other representations. The corpus 
package provides an interface to this data.

To see a complete listing of the works in the music21 corpus, 
visit  :ref:`referenceCorpus`.  Note that music21 does not own
most of the music in the corpus -- it has been licensed to us (or
in a free license).  It may not be free in all parts of the world,
but to the best of our knowledge is true for the US.
'''


import re
import os
import doctest, unittest
import zipfile

import music21
from music21 import common
from music21 import converter
from music21 import metadata
from music21 import musicxml
from music21.corpus import virtual
from music21.corpus.metadataCache import metadataCache

from music21 import environment
_MOD = "corpus.base.py"
environLocal = environment.Environment(_MOD)


# a list of metadataCache's can reside in this module-level storage; this 
# data is loaded on demand. 
_METADATA_BUNDLES = {'core':None, 'virtual':None, 'local':None}

# update and access through property to make clear
# that this is a corpus distribution or a no-corpus distribution
_NO_CORPUS = False 

# store all composers in the corpus (not virtual) 
# as two element tuples of path name, full name
COMPOSERS = [
    ('airdsAirs', 'Aird\'s Airs'),
    ('bach', 'Johann Sebastian Bach'),
    ('beethoven', 'Ludwig van Beethoven'),
    ('cpebach', 'C.P.E. Bach'),
    ('ciconia', 'Johannes Ciconia'),
    ('essenFolksong', 'Essen Folksong Collection'),
    ('handel', 'George Frideric Handel'),
    ('haydn', 'Joseph Haydn'),
    ('josquin', 'Josquin des Prez'),
    ('luca', 'D. Luca'),
    ('miscFolk', "Miscellaneous Folk"),
    ('monteverdi', "Claudio Monteverdi"),
    ('mozart', 'Wolfgang Amadeus Mozart'),
    ('oneills1850', 'Oneill\'s 1850'),
    ('ryansMammoth', 'Ryan\'s Mammoth Collection'),
    ('schoenberg', 'Arnold Schoenberg'),
    ('schumann', 'Robert Schumann'),
    ]

# instantiate an instance of each virtual work object in a module
# level constant; this object contains meta data about the work
VIRTUAL = []
for name in dir(virtual): # look over virtual module
    className = getattr(virtual, name)
    if callable(className):
        obj = className()
        if isinstance(obj, virtual.VirtualWork) and obj.corpusPath != None:
            VIRTUAL.append(obj)


#-------------------------------------------------------------------------------
class CorpusException(Exception):
    pass


#-------------------------------------------------------------------------------
def _findPaths(fpRoot, extList):
    '''Given a root fp file path, recursively search all contained paths for files
    in fpRoot matching any of the extensions in extList
    
    The `extList` is a list of file extensions. 
    
    NB: we've tried optimizing with fnmatch but it does not save any time.
    '''
    # can replace extension matching with a regex    
    #escape extension dots (if there) for regex
    #extList = ["\\%s" % ex for ex in extList if ex.startswith('.')]
    #extRe = re.compile('.*(%s)' % '|'.join(extList))

    matched = []
    # walk each top-level dir
    for dirpath, dirnames, filenames in os.walk(fpRoot):
        if '.svn' in dirnames:
            # removing in place will stop recursion into these dirs
            dirnames.remove('.svn')
        for fn in filenames:
            if fn.startswith('.'): 
                continue
            for ext in extList:
                if fn.endswith(ext):
                    matched.append(os.path.join(dirpath, fn))
                    break # just break out of outer loop
    return matched


# cached once; default extensions for all corpus entires;
# returned by _translateExtensions() function below
_ALL_EXTENSIONS = (common.findInputExtension('abc') +
                   common.findInputExtension('lily') +
                   common.findInputExtension('midi') +
                   common.findInputExtension('musicxml') +
                   common.findInputExtension('musedata') +
                   common.findInputExtension('humdrum') +
                   common.findInputExtension('romantext') +
                   common.findInputExtension('noteworthytext') 
                )

def _translateExtensions(extList=None, expandExtensions=True):
    '''Utility to get default extensions, or, optionally, expand extensions to all known formats. 

    >>> from music21 import *
    >>> corpus.base._translateExtensions()
    ['.abc', '.ly', '.lily', '.mid', '.midi', '.xml', '.mxl', '.mx', '.md', '.musedata', '.zip', '.krn', '.rntxt', '.rntext', '.romantext', '.rtxt', '.nwctxt', '.nwc']

    >>> corpus.base._translateExtensions('.mid', False)
    ['.mid']
    >>> corpus.base._translateExtensions('.mid', True)
    ['.mid', '.midi']
    '''
    if not common.isListLike(extList):
        extList = [extList]

    if extList == [None]:
        extList = _ALL_EXTENSIONS # already expended
    elif expandExtensions:
        extMod = []
        for e in extList:
            extMod += common.findInputExtension(e)
        extList = extMod
    return extList


#-------------------------------------------------------------------------------
# core routines for getting file paths

# module-level cache; only higher-level functions cache results
_pathsCache = {}
# store temporary local paths added by a user in a session and not stored in 
# Environment
_pathsLocalTemp = [] 

def getCorePaths(extList=None, expandExtensions=True):    
    '''Get all paths in the corpus that match a known extension, or an extenion
    provided by an argument.

    If `expandExtensions` is True, a format for an extension, and related extensions, will replaced by all known input extensions. This is convenient when an input format might match for multiple extensions.

    >>> from music21 import *
    
    >>> a = corpus.getCorePaths()
    >>> len(a) # the current number of paths; update when adding to corpus
    2210

    >>> a = corpus.getCorePaths('krn')
    >>> len(a) >= 4
    True

    >>> a = corpus.getCorePaths('abc')
    >>> len(a) >= 10
    True

    '''
    extList = _translateExtensions(extList=extList,
                expandExtensions=expandExtensions)
    cacheKey = ('core', tuple(extList))
    # not cached, fetch and reset 
    if cacheKey not in _pathsCache.keys():
        _pathsCache[cacheKey] = _findPaths(common.getCorpusFilePath(), extList)
    return _pathsCache[cacheKey]


def getVirtualPaths(extList=None, expandExtensions=True):
    '''Get all paths in the virtual corpus that match a known extension. An extension of None will return all known extensions.
   
    >>> from music21 import *
    >>> len(corpus.getVirtualPaths()) > 6
    True
    '''
    extList = _translateExtensions(extList=extList,
                expandExtensions=expandExtensions)
    paths = []
    for obj in VIRTUAL:
        if obj.corpusPath != None:
            for ext in extList:
                #environLocal.printDebug([obj.corpusPath, ext])
                post = obj.getUrlByExt(ext)
                for part in post:
                    if part not in paths:
                        paths.append(part)
    return paths


def getLocalPaths(extList=None, expandExtensions=True):
    '''
    Access files in additional directories supplied by the user and defined in environement settings. If addtional paths are added on a per-session basis witht the :func:`~music21.corpus.addPath` function, these paths are also retuned with this method. 
    '''
    extList = _translateExtensions(extList=extList,
                expandExtensions=expandExtensions)
    cacheKey = ('local', tuple(extList))
    # not cached, fetch and reset 
    if cacheKey not in _pathsCache.keys():
        # check paths before trying to search
        candidatePaths = environLocal['localCorpusSettings']
        validPaths = []
        for fp in candidatePaths + _pathsLocalTemp:
            if not os.path.isdir(fp):
                environLocal.warn(
                'invalid path set as localCorpusSetting: %s' % fp)
            else:
                validPaths.append(fp)
        # append successive matches into one list
        matched = []
        for fp in validPaths:
            #environLocal.pd(['finding paths in:', fp])
            matched += _findPaths(fp, extList)
        _pathsCache[cacheKey] = matched
    return _pathsCache[cacheKey]


def addPath(fp):
    '''
    Add a directory path to the Local Corpus on a 
    *temporary* basis, i.e., just for the current Python 
    session. All directories contained within the provided 
    directory will be searched for files with file extensions 
    matching the currently readable file types. Any number of 
    file paths can be added one at a time. 

    An error will be raised if the file path does not exist, 
    is already defined as a temporary, or is already being 
    searched by being defined with the 
    :class:`~music21.environment.Environment` 'localCorpusSettings' setting.

    To permanently add a path to the list of stored local corpus paths, 
    set the 'localCorpusPath' or 'localCorpusSettings' setting of 
    the :class:`~music21.environment.UserSettings` object. 

    >>> from music21 import *
    >>> #_DOCS_SHOW coprus.addPath('~/Documents')

    alternatively, add a directory permanently (see link above 
    for more details):
    
    >>> from music21 import *
    >>> #_DOCS_SHOW us = environment.UserSettings()
    >>> #_DOCS_SHOW us['localCorpusPath'] = 'd:/desktop/'
    
    (then best is to restart music21)

    '''
    if fp is None or not os.path.exists(fp):
        raise CorpusException("an invalid file path has been provided: %s" % fp)
    if fp in _pathsLocalTemp:
        raise CorpusException("the provided path has already been added: %s" % fp)
    if fp in environLocal['localCorpusSettings']:
        raise CorpusException("the provided path is already incldued in the Environment localCorpusSettings: %s" % fp)

    _pathsLocalTemp.append(fp)
    # delete all local keys in the cache
    for key in _pathsCache.keys():
        if key[0] == 'local':
            del _pathsCache[key]


def getPaths(extList=None, expandExtensions=True, 
    domain=['core', 'virtual', 'local']):
    '''
    Get paths from core, virtual, and/or local domains. 
    This is the public interface for getting all corpus 
    paths with one function. 
    '''
    post = []
    if 'core' in domain:
        post += getCorePaths(extList=extList,
                expandExtensions=expandExtensions)
    if 'virtual' in domain:
        post += getVirtualPaths(extList=extList,
                expandExtensions=expandExtensions)
    if 'local' in domain:
        post += getLocalPaths(extList=extList,
                expandExtensions=expandExtensions)
    return post



#-------------------------------------------------------------------------------
# metadata routines

def _updateMetadataBundle():
    '''
    Update cached metdata bundles.
    '''
    for d, f in (('core', getCorePaths), ('virtual', getVirtualPaths),
                 ('local', getLocalPaths)):
        if _METADATA_BUNDLES[d] is None:
            fpList = f()
            _METADATA_BUNDLES[d] = metadata.MetadataBundle(d)
            _METADATA_BUNDLES[d].read()
            # must update access paths for the files found on this system
            _METADATA_BUNDLES[d].updateAccessPaths(fpList)

def cacheMetadata(domainList=['local']):
    if not common.isListLike(domainList):
        domainList = [domainList]
    for domain in domainList:
        # remove any cached values
        _METADATA_BUNDLES[domain] = None
    metadataCache.cacheMetadata(domainList)        

def search(query, field=None, domain=['core', 'virtual', 'local'],     
    extList=None):
    '''Search all stored metadata and return a list of file paths; to 
    return a list of parsed Streams, use searchParse(). 

    The `domain` parameter can be used to specify one of three corpora: 
    core (included with music21), virtual (defined in music21 but hosted 
    online), and local (hosted on the user's system (not yet implemented)). 

    This method uses stored metadata and thus, on first usage, will 
    incur a performance penalty during metadata loading.
    '''
    post = []
    _updateMetadataBundle()
    if 'core' in domain:
        post += _METADATA_BUNDLES['core'].search(query, field, extList)
    if 'virtual' in domain:
        post += _METADATA_BUNDLES['virtual'].search(query, field, extList)
    if 'local' in domain:
        post += _METADATA_BUNDLES['local'].search(query, field, extList)

    return post



#-------------------------------------------------------------------------------
def getComposer(composerName, extList=None):
    '''
    Return all filenames in the corpus that match a composer's 
    or a collection's name. An `extList`, if provided, defines 
    which extensions are returned. An `extList` of None (default) returns 
    all extensions. 
    
    Note that xml and mxl are treated equivalently.

    >>> from music21 import *
    >>> a = corpus.getComposer('beethoven')
    >>> len(a) > 10
    True
    >>> a = corpus.getComposer('mozart')
    >>> len(a) > 10
    True
    >>> a = corpus.getComposer('bach', 'krn')
    >>> len(a) < 10
    True
    >>> a = corpus.getComposer('bach', 'xml')
    >>> len(a) > 10
    True
    '''
    paths = getPaths(extList)
    post = []
    for path in paths:
        # iterate through path components; cannot match entire string
        # composer name may be at any level
        stubs = path.split(os.sep)
        for s in stubs:
            # need to remove extension if found
            if composerName.lower() == s.lower():
                post.append(path)
                break
            # get all but the last dot group
            # this is done for file names that function like composer names
            elif '.' in s and '.'.join(s.split('.')[:-1]).lower() == composerName.lower():
                post.append(path)
                break
    post.sort()
    return post

def getComposerDir(composerName):
    '''
    Given the name of a composer, get the path 
    to the top-level directory of that composer 

    >>> from music21 import *
    >>> import os
    >>> a = corpus.getComposerDir('beethoven')
    >>> a.endswith(os.path.join('corpus', os.sep, 'beethoven'))
    True
    >>> a = corpus.getComposerDir('bach')
    >>> a.endswith(os.path.join('corpus', os.sep, 'bach'))
    True
    >>> a = corpus.getComposerDir('mozart')
    >>> a.endswith(os.path.join('corpus', os.sep, 'mozart'))
    True
    '''
    match = None
    #for moduleName in MODULES:          
    for moduleName in sorted(os.listdir(common.getCorpusFilePath())):

#         if common.isListLike(moduleName):
#             candidate = moduleName[0]         
#         else:
#             candidate = str(moduleName)

        candidate = moduleName

        if composerName.lower() not in candidate.lower():
            continue
        # might also look at .__file__
#         if not hasattr(moduleName, '__path__'): # its a list of files
#             dirCandidate = moduleName[0]
#             while True:
#                 dir = os.path.dirname(dirCandidate)
#                 if dir.lower().endswith(composerName.lower()):
#                     break
#                 else:
#                     dirCandidate = dir
#                 if dirCandidate.count(os.sep) < 2: # done enough checks
#                     break
#         else:
#             dir = moduleName.__path__[0] 

        # last check
        dir = os.path.join(common.getCorpusFilePath(), moduleName)
        if dir.lower().endswith(composerName.lower()):
            match = dir     
            break
    return match


def _noCorpus():
    '''Return True or False if this is a corpus or noCoprus distrubution. 
    '''
    if _NO_CORPUS is None:
        if corpus.getComposerDir('bach') is None:
            _NO_CORPUS = True
        else:
            _NO_CORPUS = False
    return _NO_CORPUS

noCorpus = property(_noCorpus, doc='''
    Get True or False if this is a noCorpus music21 distribution.

    >>> from music21 import *
    >>> corpus.noCorpus
    False
    ''')



#-------------------------------------------------------------------------------
def getWorkList(workName, movementNumber=None, extList=None):
    '''
    Search the corpus and return a list of filenames of works, 
    always in a list. 
    
    If no matches are found, an empty list is returned.

    >>> from music21 import *
    >>> len(corpus.getWorkList('beethoven/opus18no1'))
    8
    >>> len(corpus.getWorkList('beethoven/opus18no1', 1))
    2 
    >>> len(corpus.getWorkList('beethoven/opus18no1', 1, '.krn'))
    1
    >>> len(corpus.getWorkList('beethoven/opus18no1', 1, '.xml'))
    1
    >>> len(corpus.getWorkList('beethoven/opus18no1', 0, '.xml'))
    0
    >>> len(corpus.getWorkList('handel/hwv56', '1-02', '.md'))
    1
    >>> len(corpus.getWorkList('handel/hwv56', (2,1), '.md'))
    1

    >>> len(corpus.getWorkList('bach/artOfFugue_bwv1080', 2, '.md'))
    1

    '''
    if not common.isListLike(extList):
        extList = [extList]

    paths = getPaths(extList)
    post = []

    # permit workName to be a list of paths/branches
    if common.isListLike(workName):
        workName = os.path.sep.join(workName)
    # replace with os-dependent separators 
    workSlashes = workName.replace('/', os.path.sep)

    #environLocal.printDebug(['getWorkList(): searching for workName or workSlashses', workName, workSlashes])

    # find all matches for the work name
    # TODO: this should match by path component, not just
    # substring
    for path in paths:
        if workName.lower() in path.lower():
            post.append(path)
        elif workSlashes.lower() in path.lower():
            post.append(path)
    #environLocal.printDebug(['getWorkList(): post', post])

    postMvt = []
    if movementNumber is not None and len(post) > 0:
        # store one ore more possible mappings of movement number
        movementStrList = []

        # see if this is a pair
        if common.isListLike(movementNumber):
            movementStrList.append(''.join([str(x) for x in movementNumber]))
            movementStrList.append('-'.join([str(x) for x in movementNumber]))
            movementStrList.append('movement' + '-'.join([str(x) for x in movementNumber]))
            movementStrList.append('movement' + '-0'.join([str(x) for x in movementNumber]))
        else:
            movementStrList += ['0%s' % str(movementNumber), 
                           '%s' % str(movementNumber), 
                           'movement%s' % str(movementNumber)]

        #environLocal.printDebug(['movementStrList', movementStrList])

        for fp in post:
            dir, fn = os.path.split(fp)
            if '.' in fn:
                fnNoExt = fn.split('.')[0]
            else:
                fnNoExt = None
            
            searchPartialMatch = True
            if fnNoExt != None:
                # look for direct matches first
                for movementStr in movementStrList:
                    #if movementStr.lower() in fp.lower():
                    #environLocal.printDebug(['fnNoExt comparing', movementStr, fnNoExt])
                    if fnNoExt.lower() == movementStr.lower():
                        #environLocal.printDebug(['matched fnNoExt', fp])
                        postMvt.append(fp)     
                        searchPartialMatch = False           

            # if we have one direct match, all other matches must 
            # be direct. this will match multiple files with different 
            # file extensions
            if len(postMvt) > 0:
                continue

            if searchPartialMatch:
                #environLocal.printDebug(['searching partial match'])
                for movementStr in movementStrList:
                    #if movementStr.lower() in fp.lower():
                    if fn.startswith(movementStr.lower()):
                        postMvt.append(fp)
        if len(postMvt) == 0:
            pass # return an empty list
    else:
        postMvt = post

    #environLocal.printDebug(['postMvt', postMvt])

    postMvt.sort() # sort here, a shorter list
    if len(postMvt) == 0:
        return []
    else:
        return postMvt

def getVirtualWorkList(workName, movementNumber=None, extList=None):
    '''Given a work name, search all virtual works and return a list of URLs for any matches.

    >>> from music21 import *
    >>> corpus.getVirtualWorkList('bach/bwv1007/prelude')
    ['http://kern.ccarh.org/cgi-bin/ksdata?l=cc/bach/cello&file=bwv1007-01.krn&f=xml']

    >>> corpus.getVirtualWorkList('junk')
    []
    '''
    if not common.isListLike(extList):
        extList = [extList]

    for obj in VIRTUAL:
        if obj.corpusPath != None and workName.lower() in obj.corpusPath.lower():
            return obj.getUrlByExt(extList)
    return []



#-------------------------------------------------------------------------------
def getWorkReferences(sort=True):
    '''Return a data dictionary for all works in the corpus and (optionally) the virtual corpus. Returns a list of reference dictionaries, each each dictionary for a each composer. A 'works' dictionary for each composer provides references to dictionaries for all associated works. 

    This is used in the generation of corpus documentation

    >>> from music21 import *
    >>> post = corpus.getWorkReferences()
    '''
    # from music21 import corpus; corpus.getWorkReferences()
    # TODO: update this to use metadata

    post = []
    for dirComposer, composer in COMPOSERS:
        ref = {}
        ref['composer'] = composer
        ref['composerDir'] = dirComposer
        ref['works'] = {} # store by keys of name/dirname

        works = getComposer(dirComposer)
        for path in works:
            # split by the composer dir to get relative path
            #environLocal.printDebug(['dir composer', dirComposer, path])
            junk, fileStub = path.split(dirComposer)
            if fileStub.startswith(os.sep):
                fileStub = fileStub[len(os.sep):]
            # break into file components
            fileComponents = fileStub.split(os.sep)
            # the first is either a directory for containing components
            # or a top-level name
            format, ext = common.findFormatExtFile(fileComponents[-1])
            if ext is None:
                #environLocal.printDebug(['file that does not seem to have an extension', ext, path])
                continue
            # if not a file w/ ext, we will get None for format
            if format == None:
                workStub = fileComponents[0]
            else: # remove the extension
                workStub = fileComponents[0].replace(ext, '')
            # create list location if not already added
            if workStub not in ref['works'].keys():
                ref['works'][workStub] = {}
                ref['works'][workStub]['files'] = []
                title = common.spaceCamelCase(workStub).title()
                ref['works'][workStub]['title'] = title
                ref['works'][workStub]['virtual'] = False

            # last component is name
            format, ext = common.findFormatExtFile(fileComponents[-1])
            fileDict = {}
            fileDict['format'] = format
            fileDict['ext'] = ext
            # all path parts after corpus
            fileDict['corpusPath'] = os.path.join(dirComposer, fileStub)
            fileDict['fileName'] = fileComponents[-1] # all after 

            title = None
            # this works but takes a long time!
#             if format == 'musicxml':
#                 mxDocument = musicxml.Document()
#                 mxDocument.open(path)
#                 title = mxDocument.getBestTitle()
            if title is None:
                title = common.spaceCamelCase(
                    fileComponents[-1].replace(ext, ''))
                title = title.title()
            fileDict['title'] = title

            ref['works'][workStub]['files'].append(fileDict)

            # add this path
        post.append(ref)

    # get each VirtualWork object
    for vw in VIRTUAL:
        composerDir = vw.corpusPath.split('/')[0]
        match = False
        for ref in post:
            # check composer reference or first part of corpusPath
            if (ref['composer'] == vw.composer or 
                composerDir == ref['composerDir']):
                match = True
                break # use this ref

        if not match: # new composers, create a new ref
            ref = {}
            ref['composer'] = vw.composer
            ref['composerDir'] = composerDir
            ref['works'] = {} # store by keys of name/dirname

        # work stub should be everything other than top-level
        workStub = vw.corpusPath.replace(composerDir+'/', '')
        ref['works'][workStub] = {}
        ref['works'][workStub]['virtual'] = True
        ref['works'][workStub]['files'] = []
        ref['works'][workStub]['title'] = vw.title

        for url in vw.urlList:
            format, ext = common.findFormatExtURL(url)
            fileDict = {}
            fileDict['format'] = format
            fileDict['ext'] = ext
            # all path parts after corpus
            fileDict['corpusPath'] = vw.corpusPath
            fileDict['title'] = vw.title
            fileDict['url'] = url
            ref['works'][workStub]['files'].append(fileDict)

        if not match: # not found already, need to add
            post.append(ref)

    if sort:
        sortGroup = []
        for ref in post:
            sortGroupSub = []
            for workStub in ref['works'].keys():
                # add title first for sorting
                sortGroupSub.append([ref['works'][workStub]['title'], workStub])
            sortGroupSub.sort()
            ref['sortedWorkKeys'] = [y for x, y in sortGroupSub]
            # prepare this sort group
            sortGroup.append([ref['composerDir'], ref])
        sortGroup.sort()
        post = [ref for junk, ref in sortGroup]
    return post


#-------------------------------------------------------------------------------
def getWork(workName, movementNumber=None, extList=None):
    '''Search the corpus, then the virtual corpus, for a work, and return a file path or URL. This method will return either a list of file paths or, if there is a single match, a single file path. If no matches are found an Exception is raised. 

    >>> from music21 import *
    >>> import os
    >>> a = corpus.getWork('opus74no2', 4)
    >>> a.endswith(os.path.sep.join(['haydn', 'opus74no2', 'movement4.mxl']))
    True

    >>> a = corpus.getWork(['haydn', 'opus74no2', 'movement4.xml'])
    >>> a.endswith(os.path.sep.join(['haydn', 'opus74no2', 'movement4.mxl']))
    True

    '''
    if not common.isListLike(extList):
        extList = [extList]
    post = getWorkList(workName, movementNumber, extList)
    if len(post) == 0:
        wn = workName
        if common.isListLike(workName):
            wn = os.path.sep.join(workName)
        if wn.endswith(".xml"): # might be compressed MXL file
            newWorkName = wn[0:len(wn)-4] + ".mxl"
            return getWork(newWorkName,movementNumber,extList)
        post = getVirtualWorkList(workName, movementNumber, extList)
    if len(post) == 1:
        return post[0]
    elif len(post) == 0:
        raise CorpusException("Could not find a file/url that met this criteria")
    else: # return a list
        return post



def parse(workName, movementNumber=None, number=None, 
    extList=None, forceSource=False):
    '''
    The most important method call for corpus.
    
    Similar to converer.parse(), the method searches the corpus (including the virtual corpus)
    for a work fitting the workName description and returns a :class:`music21.stream.Stream`.

    If `movementNumber` is defined, and a movement is included in the corpus, that movement will be returned. 

    If `number` is defined, and the work is a collection with multiple components, that work number will be returned.
    For instance, some of our ABC documents contain dozens of folk songs within a single file.

    Advanced: if `forceSource` is True, the original file will always be loaded freshly and pickled (e.g., pre-parsed) files
    will be ignored.  This should not be needed if the file has been changed, since the filetime of the file and
    the filetime of the pickled version are compared.  But it might be needed if the music21 parsing routine has changed.
    
    Example, get a chorale by Bach.  Note that the source type does not need to be
    specified, nor does the name Bach even (since it's the only piece with the title BWV 66.6)

    >>> from music21 import *
    >>> bachChorale = corpus.parse('bwv66.6')
    >>> len(bachChorale.parts)
    4
    
    OMIT_FROM_DOCS
    
    >>> bachChorale.corpusFilepath
    'bach/bwv66.6.mxl'
    
    >>> s = corpus.parse('trecento/PMFC_13_05-Gloria Rosetta.mxl')
    >>> s.corpusFilepath
    'trecento/PMFC_13_05-Gloria Rosetta.mxl'
    '''
    if workName in [None, '']:
        raise CorpusException('a work name must be provided as an argument')

    if not common.isListLike(extList):
        extList = [extList]

    post = getWorkList(workName, movementNumber, extList)
    #environLocal.printDebug(['result of getWorkList()', post])
    if len(post) == 0:
        wn = workName
        if common.isListLike(workName):
            wn = os.path.sep.join(workName)
        if wn.endswith(".xml"):
            newWorkName = wn[0:len(wn)-4] + ".mxl" # might be compressed MXL file
            return parse(newWorkName,movementNumber,number,extList,forceSource)
        post = getVirtualWorkList(workName, movementNumber, extList)    

    if len(post) == 1:
        fp = post[0]
    elif len(post) == 0:
        raise CorpusException("Could not find a work that met this criteria %s" % workName)
    else: # greater than zero:
        fp = post[0] # get first
        
    #return converter.parse(fp, forceSource=forceSource, number=number)

    streamObj = converter.parse(fp, forceSource=forceSource, number=number)
    _addCorpusFilepath(streamObj, fp)
    return streamObj

def _addCorpusFilepath(streamObj, filepath):   
    # metadata attribute added to store the file path, for use later in identifying the score
    #if streamObj.metadata == None:
    #    streamObj.insert(metadata.Metadata())
    cfp = common.getCorpusFilePath()
    lenCFP = len(cfp) + len(os.sep)
    if filepath.startswith(cfp):
        fp2 = filepath[lenCFP:]
        ### corpus fix for windows
        dirsEtc = fp2.split(os.sep)
        fp3 = '/'.join(dirsEtc)
        streamObj.corpusFilepath = fp3
    else:
        streamObj.corpusFilepath = filepath

def parseWork(*arguments, **keywords):
    '''This function exists for backwards compatibility. All calls should use :func:`~music21.corpus.parse` instead.
    '''
    import warnings
    #raise DeprecationWarning('the corpus.parseWork() function is depcreciated: use corpus.parse()')
    warnings.warn('the corpus.parseWork() function is depcreciated: use corpus.parse()', DeprecationWarning)
    return parse(*arguments, **keywords)

#-------------------------------------------------------------------------------
# compression

def compressAllXMLFiles(deleteOriginal = False):
    '''
    Takes all filenames in corpus.paths and runs :meth:`music21.corpus.base.compressXML` on each.
    If the musicXML files are compressed, the originals are deleted from the system.
    '''
    environLocal.warn("Compressing musicXML files...")
    for filename in music21.corpus.paths:
        compressXML(filename, deleteOriginal=deleteOriginal)
    environLocal.warn("Compression complete. Run the main test suite, fix bugs if necessary,\n\
and then commit modified directories in corpus.")

def compressXML(filename, deleteOriginal=False):
    '''
    Takes a filename, and if the filename corresponds to a musicXML file with an .xml extension,
    creates a corresponding compressed .mxl file in the same directory. If deleteOriginal is set
    to True, the original musicXML file is deleted from the system.
    '''
    if not filename.endswith(".xml"):
        return # not a musicXML file
    environLocal.warn("Updating file: {0}".format(filename))
    fnList = filename.split(os.path.sep)
    arcname = fnList.pop() # find the archive name (name w/out filepath)
    fnList.append(arcname[0:len(arcname)-4] + ".mxl") # new archive name
    newFilename = os.path.sep.join(fnList) # new filename
    
    # contents of container.xml file in META-INF folder
    container = '<?xml version="1.0" encoding="UTF-8"?>\n\
<container>\n\
  <rootfiles>\n\
    <rootfile full-path="{0}"/>\n\
  </rootfiles>\n\
</container>\n\
    '.format(arcname)

    # Export container and original xml file to system as a compressed XML.
    with zipfile.ZipFile(newFilename, 'w', compression=zipfile.ZIP_DEFLATED) as myZip:
        #os.remove(newFilename)
        myZip.write(filename = filename, arcname = arcname)
        myZip.writestr(zinfo_or_arcname = 'META-INF{0}container.xml'.format(os.path.sep), bytes = container)

    # Delete uncompressed xml file from system
    if deleteOriginal:
        os.remove(filename)

#-------------------------------------------------------------------------------
# all paths

paths = getPaths()

#-------------------------------------------------------------------------------
# libraries


#beethoven = getComposer('beethoven')
#josquin = getComposer('josquin')
#mozart = getComposer('mozart')
#monteverdi = getComposer('monteverdi')
#haydn = getComposer('haydn')
#handel = getComposer('handel')
#bach = getComposer('bach')

# additional libraries to define

def getBachChorales(extList='xml'):
    '''Return the file name of all Bach chorales.
    
    By default, only Bach Chorales in xml format are returned, because the quality of 
    the encoding and our parsing of those is superior.

    >>> from music21 import *
    >>> a = corpus.getBachChorales()
    >>> len(a) > 400
    True
    >>> a = corpus.getBachChorales('krn')
    >>> len(a) > 10
    False
    >>> a = corpus.getBachChorales('xml')
    >>> len(a) > 400
    True
    '''
    names = ['bwv1.6.mxl', 'bwv10.7.mxl', 'bwv101.7.mxl', 'bwv102.7.mxl', 'bwv103.6.mxl', 'bwv104.6.mxl', 'bwv108.6.mxl', 'bwv11.6.mxl', 'bwv110.7.mxl', 'bwv111.6.mxl', 'bwv112.5-sc.mxl', 'bwv112.5.mxl', 'bwv113.8.mxl', 'bwv114.7.mxl', 'bwv115.6.mxl', 'bwv116.6.mxl', 'bwv117.4.mxl', 'bwv119.9.mxl', 'bwv12.7.mxl', 'bwv120.6.mxl', 'bwv120.8-a.mxl', 'bwv121.6.mxl', 'bwv122.6.mxl', 'bwv123.6.mxl', 'bwv124.6.mxl', 'bwv125.6.mxl', 'bwv126.6.mxl', 'bwv127.5.mxl', 'bwv128.5.mxl', 'bwv13.6.mxl', 'bwv130.6.mxl', 'bwv133.6.mxl', 'bwv135.6.mxl', 'bwv136.6.mxl', 'bwv137.5.mxl', 'bwv139.6.mxl', 'bwv14.5.mxl', 'bwv140.7.mxl', 'bwv144.3.mxl', 'bwv144.6.mxl', 'bwv145-a.mxl', 'bwv145.5.mxl', 'bwv146.8.mxl', 'bwv148.6.mxl', 'bwv149.7.mxl', 'bwv151.5.mxl', 'bwv153.1.mxl', 'bwv153.5.mxl', 'bwv153.9.mxl', 'bwv154.3.mxl', 'bwv154.8.mxl', 'bwv155.5.mxl', 'bwv156.6.mxl', 'bwv157.5.mxl', 'bwv158.4.mxl', 'bwv159.5.mxl', 'bwv16.6.mxl', 'bwv161.6.mxl', 'bwv162.6-lpz.mxl', 'bwv164.6.mxl', 'bwv165.6.mxl', 'bwv166.6.mxl', 'bwv168.6.mxl', 'bwv169.7.mxl', 'bwv17.7.mxl', 'bwv171.6.mxl', 'bwv172.6.mxl', 'bwv174.5.mxl', 'bwv175.7.mxl', 'bwv176.6.mxl', 'bwv177.5.mxl', 'bwv178.7.mxl', 'bwv179.6.mxl', 'bwv18.5-lz.mxl', 'bwv18.5-w.mxl', 'bwv180.7.mxl', 'bwv183.5.mxl', 'bwv184.5.mxl', 'bwv185.6.mxl', 'bwv187.7.mxl', 'bwv188.6.mxl', 'bwv19.7.mxl', 'bwv190.7-inst.mxl', 'bwv190.7.mxl', 'bwv194.12.mxl', 'bwv194.6.mxl', 'bwv195.6.mxl', 'bwv197.10.mxl', 'bwv197.5.mxl', 'bwv197.7-a.mxl', 'bwv2.6.mxl', 'bwv20.11.mxl', 'bwv20.7.mxl', 'bwv226.2.mxl', 'bwv227.1.mxl', 'bwv227.11.mxl', 'bwv227.3.mxl', 'bwv227.7.mxl', 'bwv229.2.mxl', 'bwv244.10.mxl', 'bwv244.15.mxl', 'bwv244.17.mxl', 'bwv244.25.mxl', 'bwv244.29-a.mxl', 'bwv244.3.mxl', 'bwv244.32.mxl', 'bwv244.37.mxl', 'bwv244.40.mxl', 'bwv244.44.mxl', 'bwv244.46.mxl', 'bwv244.54.mxl', 'bwv244.62.mxl', 'bwv245.11.mxl', 'bwv245.14.mxl', 'bwv245.15.mxl', 'bwv245.17.mxl', 'bwv245.22.mxl', 'bwv245.26.mxl', 'bwv245.28.mxl', 'bwv245.3.mxl', 'bwv245.37.mxl', 'bwv245.40.mxl', 'bwv245.5.mxl', 'bwv248.12-2.mxl', 'bwv248.17.mxl', 'bwv248.23-2.mxl', 'bwv248.23-s.mxl', 'bwv248.28.mxl', 'bwv248.33-3.mxl', 'bwv248.35-3.mxl', 'bwv248.35-3c.mxl', 'bwv248.42-4.mxl', 'bwv248.42-s.mxl', 'bwv248.46-5.mxl', 'bwv248.5.mxl', 'bwv248.53-5.mxl', 'bwv248.59-6.mxl', 'bwv248.64-6.mxl', 'bwv248.64-s.mxl', 'bwv248.9-1.mxl', 'bwv248.9-s.mxl', 'bwv25.6.mxl', 'bwv250.mxl', 'bwv251.mxl', 'bwv252.mxl', 'bwv253.mxl', 'bwv254.mxl', 'bwv255.mxl', 'bwv256.mxl', 'bwv257.mxl', 'bwv258.mxl', 'bwv259.mxl', 'bwv26.6.mxl', 'bwv260.mxl', 'bwv261.mxl', 'bwv262.mxl', 'bwv263.mxl', 'bwv264.mxl', 'bwv265.mxl', 'bwv266.mxl', 'bwv267.mxl', 'bwv268.mxl', 'bwv269.mxl', 'bwv27.6.mxl', 'bwv270.mxl', 'bwv271.mxl', 'bwv272.mxl', 'bwv273.mxl', 'bwv276.mxl', 'bwv277.krn', 'bwv277.mxl', 'bwv278.mxl', 'bwv279.mxl', 'bwv28.6.mxl', 'bwv280.mxl', 'bwv281.krn', 'bwv281.mxl', 'bwv282.mxl', 'bwv283.mxl', 'bwv284.mxl', 'bwv285.mxl', 'bwv286.mxl', 'bwv287.mxl', 'bwv288.mxl', 'bwv289.mxl', 'bwv29.8.mxl', 'bwv290.mxl', 'bwv291.mxl', 'bwv292.mxl', 'bwv293.mxl', 'bwv294.mxl', 'bwv295.mxl', 'bwv296.mxl', 'bwv297.mxl', 'bwv298.mxl', 'bwv299.mxl', 'bwv3.6.mxl', 'bwv30.6.mxl', 'bwv300.mxl', 'bwv301.mxl', 'bwv302.mxl', 'bwv303.mxl', 'bwv304.mxl', 'bwv305.mxl', 'bwv306.mxl', 'bwv307.mxl', 'bwv308.mxl', 'bwv309.mxl', 'bwv31.9.mxl', 'bwv310.mxl', 'bwv311.mxl', 'bwv312.mxl', 'bwv313.mxl', 'bwv314.mxl', 'bwv315.mxl', 'bwv316.mxl', 'bwv317.mxl', 'bwv318.mxl', 'bwv319.mxl', 'bwv32.6.mxl', 'bwv320.mxl', 'bwv321.mxl', 'bwv322.mxl', 'bwv323.mxl', 'bwv324.mxl', 'bwv325.mxl', 'bwv326.mxl', 'bwv327.mxl', 'bwv328.mxl', 'bwv329.mxl', 'bwv33.6.mxl', 'bwv330.mxl', 'bwv331.mxl', 'bwv332.mxl', 'bwv333.mxl', 'bwv334.mxl', 'bwv335.mxl', 'bwv336.mxl', 'bwv337.mxl', 'bwv338.mxl', 'bwv339.mxl', 'bwv340.mxl', 'bwv341.mxl', 'bwv342.mxl', 'bwv343.mxl', 'bwv344.mxl', 'bwv345.mxl', 'bwv346.mxl', 'bwv347.mxl', 'bwv348.mxl', 'bwv349.mxl', 'bwv350.mxl', 'bwv351.mxl', 'bwv352.mxl', 'bwv353.mxl', 'bwv354.mxl', 'bwv355.mxl', 'bwv356.mxl', 'bwv357.mxl', 'bwv358.mxl', 'bwv359.mxl', 'bwv36.4-2.mxl', 'bwv36.8-2.mxl', 'bwv360.mxl', 'bwv361.mxl', 'bwv362.mxl', 'bwv363.mxl', 'bwv364.mxl', 'bwv365.mxl', 'bwv366.krn', 'bwv366.mxl', 'bwv367.mxl', 'bwv368.mxl', 'bwv369.mxl', 'bwv37.6.mxl', 'bwv370.mxl', 'bwv371.mxl', 'bwv372.mxl', 'bwv373.mxl', 'bwv374.mxl', 'bwv375.mxl', 'bwv376.mxl', 'bwv377.mxl', 'bwv378.mxl', 'bwv379.mxl', 'bwv38.6.mxl', 'bwv380.mxl', 'bwv381.mxl', 'bwv382.mxl', 'bwv383.mxl', 'bwv384.mxl', 'bwv385.mxl', 'bwv386.mxl', 'bwv387.mxl', 'bwv388.mxl', 'bwv389.mxl', 'bwv39.7.mxl', 'bwv390.mxl', 'bwv391.mxl', 'bwv392.mxl', 'bwv393.mxl', 'bwv394.mxl', 'bwv395.mxl', 'bwv396.mxl', 'bwv397.mxl', 'bwv398.mxl', 'bwv399.mxl', 'bwv4.8.mxl', 'bwv40.3.mxl', 'bwv40.6.mxl', 'bwv40.8.mxl', 'bwv400.mxl', 'bwv401.mxl', 'bwv402.mxl', 'bwv403.mxl', 'bwv404.mxl', 'bwv405.mxl', 'bwv406.mxl', 'bwv407.mxl', 'bwv408.mxl', 'bwv41.6.mxl', 'bwv410.mxl', 'bwv411.mxl', 'bwv412.mxl', 'bwv413.mxl', 'bwv414.mxl', 'bwv415.mxl', 'bwv416.mxl', 'bwv417.mxl', 'bwv418.mxl', 'bwv419.mxl', 'bwv42.7.mxl', 'bwv420.mxl', 'bwv421.mxl', 'bwv422.mxl', 'bwv423.mxl', 'bwv424.mxl', 'bwv425.mxl', 'bwv426.mxl', 'bwv427.mxl', 'bwv428.mxl', 'bwv429.mxl', 'bwv43.11.mxl', 'bwv430.mxl', 'bwv431.mxl', 'bwv432.mxl', 'bwv433.mxl', 'bwv434.mxl', 'bwv435.mxl', 'bwv436.mxl', 'bwv437.mxl', 'bwv438.mxl', 'bwv44.7.mxl', 'bwv45.7.mxl', 'bwv47.5.mxl', 'bwv48.3.mxl', 'bwv48.7.mxl', 'bwv5.7.mxl', 'bwv52.6.mxl', 'bwv55.5.mxl', 'bwv56.5.mxl', 'bwv57.8.mxl', 'bwv59.3.mxl', 'bwv6.6.mxl', 'bwv60.5.mxl', 'bwv64.2.mxl', 'bwv64.4.mxl', 'bwv64.8.mxl', 'bwv65.2.mxl', 'bwv65.7.mxl', 'bwv66.6.mxl', 'bwv67.4.mxl', 'bwv67.7.mxl', 'bwv69.6-a.mxl', 'bwv69.6.mxl', 'bwv7.7.mxl', 'bwv70.11.mxl', 'bwv70.7.mxl', 'bwv72.6.mxl', 'bwv73.5.mxl', 'bwv74.8.mxl', 'bwv77.6.mxl', 'bwv78.7.mxl', 'bwv79.3.mxl', 'bwv79.6.mxl', 'bwv8.6.mxl', 'bwv80.8.mxl', 'bwv81.7.mxl', 'bwv83.5.mxl', 'bwv84.5.mxl', 'bwv85.6.mxl', 'bwv86.6.mxl', 'bwv87.7.mxl', 'bwv88.7.mxl', 'bwv89.6.mxl', 'bwv9.7.mxl', 'bwv90.5.mxl', 'bwv91.6.mxl', 'bwv92.9.mxl', 'bwv93.7.mxl', 'bwv94.8.mxl', 'bwv95.7.mxl', 'bwv96.6.mxl', 'bwv97.9.mxl', 'bwv99.6.mxl']

    baseDir = getComposerDir('bach')
    post = []
    if baseDir is None: # case where we have no corpus
        return post

    paths = getPaths(extList)
    for fn in names:
        candidate = os.path.join(baseDir, fn)
        if candidate not in paths: # it may not match extensions
            if not os.path.exists(candidate): # it does not exist at all 
                environLocal.printDebug(['corpus missing expected file path', 
                                    candidate])
        else:
            post.append(candidate)
    return post

bachChorales = property(getBachChorales)




class BachChoraleList(object):
    '''
    A searchable list of BachChorales by various numbering systems:
    
    Note that multiple chorales share the same title, so it's best to
    iterate over one of the other lists to get them all.
    
    The list of chorales comes from http://en.wikipedia.org/wiki/List_of_chorale_harmonisations_by_Johann_Sebastian_Bach
    which does not have all chorales in the Bärenreitter-Kirnbergger or Riemenschneider
    numberings since it only includes BWV 250-438.


    >>> from music21 import *
    >>> bcl = corpus.BachChoraleList()
    >>> info358 = bcl.byBudapest[358]
    >>> for key in info358.keys():
    ...   print key, info358[key]
    budapest 358
    bwv 431
    title Wenn wir in höchsten Nöten sein
    notes None
    baerenreiter 68
    riemenschneider 68
    kalmus 358
    >>> #_DOCS_SHOW c = corpus.parse('bach/bwv' + str(info358['bwv']))
    >>> #_DOCS_SHOW c.show() # shows Bach BWV431    

    More fully:
    
    >>> b = corpus.parse('bwv' + str(corpus.BachChoraleList().byRiemenschneider[2]['bwv']))
    >>> b
    <music21.stream.Score ...>
    
    '''
    def __init__(self):
        self.prepareList()
        
    def prepareList(self):
        '''
        puts a list of Bach Chorales into dicts of dicts called
        
        self.byBudapest
        self.byBWV
        self.byRiemenschneider
        
        etc.
        '''
        # From http://en.wikipedia.org/wiki/List_of_chorale_harmonisations_by_Johann_Sebastian_Bach
        # CC license. http://en.wikipedia.org/wiki/WP:CC-BY-SA
        # Some of these are problematic--I have removed them for now: --Evan Lynch
        # |Seelen-Bräutigam||409||0||5||306||141||Actally 5a in Bärenreiter, not in Kalmus
        # |-
        # |Christe, du Beistand deiner Kreuzgemeinde||275||35||210||45||210||&nbsp;
        # |-
        # |Christe, der du bist Tag und Licht||274||34||245||44||245||&nbsp;

        
        allCat = r'''|Was Gott tut, das ist wohlgetan||250||339||346||342||347||1st Wedding Chorale in this group
        |-
        |Sei Lob und Ehr' dem höchsten Gut||251||89||328||91||329||2nd Wedding Chorale in this group; melody known as "Es ist das Heil uns kommen her"
        |-
        |Nun danket alle Gott||252||258||329||258||330||3rd Wedding Chorale in this group
        |-
        |Ach bleib bei uns, Herr Jesu Christ||253||1||177||1||177||&nbsp;
        |-
        |Ach Gott, erhör' mein Seufzen||254||2||186||2||186||&nbsp;
        |-
        |Ach Gott und Herr||255||3||40||4||40||&nbsp;
        |-
        |Ach lieben Christen, seid getrost||256||385||31||385||31||&nbsp;
        |-
        |Wär Gott nicht mit uns diese Zeit||257||388||284||386||285||melody known as "Wo Gott der Herr nicht bei uns hält"
        |-
        |Wo Gott der Herr nicht bei uns hält||258||383||335||387||336||No. 63 in Schemelli
        |-
        |Ach, was soll ich Sünder machen||259||10||39||10||39||&nbsp;
        |-
        |Allein Gott in der Höh' sei Ehr'||260||12||249||16||249||&nbsp;
        |-
        |Allein zu dir, Herr Jesu Christ||261||15||358||18||359||&nbsp;
        |-
        |Alle Menschen müssen sterben||262||17||153||13||153||&nbsp;
        |-
        |Alles ist an Gottes Segen||263||19||128||19||128||&nbsp;
        |-
        |Als der gütige Gott||264||20||159||20||159||&nbsp;
        |-
        |Als Jesus Christus in der Nacht||265||21||180||21||180||&nbsp;
        |-
        |Als vierzig Tag nach Ostern||266||22||208||22||208||&nbsp;
        |-
        |An Wasserflüssen Babylon||267||23||5||23||5||&nbsp;
        |-
        |Auf, auf, mein Herz, und du mein ganzer Sinn||268||24||124||24||124||&nbsp;
        |-
        |Aus meines Herzens Grunde||269||30||1||30||1||&nbsp;
        |-
        |Befiehl du deine Wege||270||157||285||162||286||melody known as "Herzlich tut mich verlangen"
        |-
        |Befiehl du deine Wege||271||158||366||163||367||melody known as "Herzlich tut mich verlangen"
        |-
        |Befiehl du deine Wege||272||32||339||32||340||&nbsp;
        |-
        |Christ, der du bist der helle Tag||273||33||230||33||230||&nbsp;
        |-
        |Christ ist erstanden||276||36||197||35||197||&nbsp;
        |-
        |Christ lag in Todes Banden||277||38||15||39||15||&nbsp;
        |-
        |Christ lag in Todesbanden||278||39||370||40||371||&nbsp;
        |-
        |Christ lag in Todesbanden||279||40||261||37||261||&nbsp;
        |-
        |Christ, unser Herr, zum Jordan kam||280||43||65||43||66||&nbsp;
        |-
        |Christus, der ist mein Leben||281||46||7||47||6||&nbsp;
        |-
        |Christus, der ist mein Leben||282||47||315||48||316||BWV 95 Christus, der ist mein Leben (opening chorus)
        |-
        |Christus, der uns selig macht||283||48||198||51||198||&nbsp;
        |Christus, der uns selig macht||283||48||306||51||307||&nbsp;
        |-
        |Christus ist erstanden, hat überwunden||284||51||200||52||200||&nbsp;
        |-
        |Da der Herr Christ zu Tische saß||285||52||196||53||196||&nbsp;
        |-
        |Danket dem Herren||286||53||228||55||228||&nbsp;
        |-
        |Dank sei Gott in der Höhe||287||54||310||54||311||&nbsp;
        |-
        |Das alte Jahr vergangen ist||288||55||162||56||162||&nbsp;
        |-
        |Das alte Jahr vergangen ist||289||56||313||57||314||&nbsp;
        |-
        |Das walt' Gott Vater und Gott Sohn||290||58||224||59||224||&nbsp;
        |-
        |Das walt' mein Gott, Vater, Sohn und heiliger Geist||291||59||75||60||75||&nbsp;
        |-
        |Den Vater dort oben||292||60||239||61||239||&nbsp;
        |-
        |Der du bist drei in Einigkeit||293||61||154||62||154||&nbsp;
        |-
        |Der Tag, der ist so freudenreich||294||62||158||63||158||&nbsp;
        |-
        |Des heil'gen Geistes reiche Gnad'||295||63||207||64||207||&nbsp;
        |-
        |Die Nacht ist kommen||296||64||231||65||231||&nbsp;
        |-
        |Die Sonn' hat sich mit ihrem Glanz||297||65||232||66||232||&nbsp;
        |-
        |Dies sind die heil'gen zehn Gebot'||298||66||127||67||127||&nbsp;
        |-
        |Dir, dir, Jehova, will ich singen||299||67||209||68||209||Notebook for Anna Magdalena Bach
        |-
        |Du grosser Schmerzensmann||300||70||164||71||167||&nbsp;
        |-
        |Du, o schönes Weltgebäude||301||71||137||73||134||&nbsp;
        |-
        |Ein feste Burg ist unser Gott||302||74||20||76||20||&nbsp;
        |-
        |Ein feste Burg ist unser Gott||303||75||250||77||250||&nbsp;
        |-
        |Eins ist Not! ach Herr, dies Eine||304||77||280||78||280||&nbsp;
        |-
        |Erbarm' dich mein, o Herre Gott||305||78||33||79||34||&nbsp;
        |-
        |Erstanden ist der heil'ge Christ||306||85||176||86||176||&nbsp;
        |-
        |Es ist gewisslich an der Zeit||307||262||260||262||260||&nbsp;
        |-
        |Es spricht der Unweisen Mund wohl||308||92||27||93||27||&nbsp;
        |-
        |Es stehn vor Gottes Throne||309||93||166||94||166||&nbsp;
        |-
        |Es wird schier der letzte Tag herkommen||310||94||238||95||238||&nbsp;
        |-
        |Es woll' uns Gott genädig sein||311||95||16||97||16||&nbsp;
        |-
        |Es woll' uns Gott genädig sein||312||96||351||98||352||&nbsp;
        |-
        |Für Freuden lasst uns springen||313||106||163||107||163||&nbsp;
        |-
        |Gelobet seist du, Jesu Christ||314||107||287||112||288||&nbsp;
        |-
        |Gib dich zufrieden und sei stille||315||111||271||113||271||&nbsp;
        |-
        |Gott, der du selber bist das Licht||316||112||225||114||225||&nbsp;
        |-
        |Gott, der Vater, wohn' uns bei||317||113||134||115||135||&nbsp;
        |-
        |Gottes Sohn ist kommen||318||115||18||120||18||&nbsp;
        |-
        |Gott hat das Evangelium||319||116||181||117||181||&nbsp;
        |-
        |Gott lebet noch||320||117||234||118||234||No. 37 in Schemelli
        |-
        |Gottlob, es geht nunmehr zu Ende||321||118||192||121||192||&nbsp;
        |-
        |Gott sei gelobet und gebenedeiet / Meine Seele erhebet den Herrn||322||119||70||119||70||&nbsp;
        |-
        |Gott sei uns gnädig||323||120||319||239||320||melody better known as "Meine Seele erhebt den Herren" – the "German Magnificat" or "Tonus peregrinus"
        |-
        |Meine Seele erhebet den Herrn||324||121||130||240||130||&nbsp;
        |-
        |Heilig, heilig||325||123||235||122||235||or Sanctus, Sanctus, Dominus Deus Sabaoth
        |Heilig, heilig||325||123||318||122||319||or Sanctus, Sanctus, Dominus Deus Sabaoth
        |-
        |Herr Gott, dich loben alle wir||326||129||167||129||164||&nbsp;
        |-
        |Vor deinen Thron tret' ich hiermit||327||132||333||130||334||or "Herr Gott, dich loben alle wir"
        |-
        |Herr, Gott, dich loben wir||328||133||205||133||205||&nbsp;
        |-
        |Herr, ich denk' an jene Zeit||329||136||212||134||212||&nbsp;
        |-
        |Herr, ich habe missgehandelt||330||137||35||135||33||&nbsp;
        |-
        |Herr, ich habe missgehandelt||331||138||286||136||287||&nbsp;
        |-
        |Herr Jesu Christ, dich zu uns wend||332||139||136||137||136||&nbsp;
        |-
        |Herr Jesu Christ, du hast bereit't||333||140||226||138||226||&nbsp;
        |-
        |Herr Jesu Christ, du höchstes Gut||334||141||73||142||73||&nbsp;
        |-
        |Herr Jesu Christ (or O Jesu Christ), mein's Lebens Licht (or O Jesu, du mein Bräutigam)||335||145||236||143||295||BWV 118 O Jesu Christ, mein's Lebens Licht
        |-
        |Herr Jesu Christ, wahr'r Mensch und Gott||336||146||189||145||189||&nbsp;
        |-
        |Herr, nun lass in Frieden||337||148||190||146||190||&nbsp;
        |-
        |Herr, straf mich nicht in deinem Zorn||338||149||221||147||221||&nbsp;
        |-
        |Herr, wie du willst, so schick's mit mir or Wer in dem Schutz des Höchsten||339||151||144||149||144||&nbsp;
        |Herr, wie du willst, so schick's mit mir or Wer in dem Schutz des Höchsten||339||151||144||149||318||&nbsp;
        |-
        |Herzlich lieb hab ich dich, o Herr||340||152||277||153||277||&nbsp;
        |-
        |Heut' ist, o Mensch, ein grosser Trauertag||341||170||168||168||168||&nbsp;
        |-
        |Heut' triumphieret Gottes Sohn||342||171||79||169||79||&nbsp;
        |-
        |Hilf, Gott, dass mir's gelinge||343||172||199||170||199||&nbsp;
        |Hilf, Gott, dass mir's gelinge||343||172||301||170||302||&nbsp;
        |-
        |Hilf, Herr Jesu, lass gelingen||344||173||155||171||155||&nbsp;
        |-
        |Ich bin ja, Herr, in deiner Macht||345||174||251||172||251||&nbsp;
        |-
        |Ich dank' dir Gott für all' Wohltat||346||175||223||173||223||&nbsp;
        |-
        |Ich dank' dir, lieber Herre||347||176||2||175||2||&nbsp;
        |-
        |Ich dank' dir, lieber Herre||348||177||272||176||272||&nbsp;
        |-
        |Ich dank' dir schon durch deinen Sohn||349||179||188||177||188||&nbsp;
        |-
        |Ich danke dir, o Gott, in deinem Throne||350||180||229||178||229||&nbsp;
        |-
        |Ich hab' mein' Sach' Gott heimgestellt||351||182||19||180||19||&nbsp;
        |-
        |Jesu, der du meine Seele||352||185||37||192||37||&nbsp;
        |-
        |Jesu, der du meine Seele||353||186||269||193||269||&nbsp;
        |-
        |Jesu, der du meine Seele||354||187||368||194||369||&nbsp;
        |-
        |Jesu, der du selbsten wohl||355||189||169||195||169||&nbsp;
        |-
        |Jesu, du mein liebstes Leben||356||190||243||196||243||&nbsp;
        |-
        |Jesu, Jesu, du bist mein||357||191||244||197||244||No. 53 in Schemelli
        |-
        |Jesu, meine Freude||358||195||355||207||356||&nbsp;
        |-
        |Jesu, meiner Seelen Wonne||359||363||364||372||365||melody known as "Werde munter, mein Gemüte"
        |-
        |Jesu, meiner Freuden Freude||360||364||349||373||350||melody known as "Werde munter, mein Gemüte"
        |-
        |Jesu, meines Herzens Freud'||361||202||264||208||264||&nbsp;
        |-
        |Jesu, nun sei gepreiset||362||203||252||211||252||&nbsp;
        |-
        |Jesus Christus, unser Heiland||363||206||30||212||30||&nbsp;
        |-
        |Jesus Christus, unser Heiland||364||207||174||213||174||&nbsp;
        |-
        |Jesus, meine Zuversicht||365||208||175||215||175||&nbsp;
        |-
        |Ihr Gestirn', ihr hohlen Lüfte||366||210||161||183||161||&nbsp;
        |-
        |In allen meinen Taten||367||211||140||184||140||&nbsp;
        |-
        |In dulci jubilo||368||215||143||188||143||&nbsp;
        |-
        |Keinen hat Gott verlassen||369||217||129||216||129||&nbsp;
        |-
        |Komm, Gott Schöpfer, heiliger Geist||370||218||187||217||187||&nbsp;
        |-
        |Kyrie, Gott Vater in Ewigkeit||371||225||132||222||132||&nbsp;
        |-
        |Lass, o Herr, dein Ohr sich neigen||372||226||218||223||218||&nbsp;
        |-
        |Liebster Jesu, wir sind hier||373||228||131||226||131||&nbsp;
        |-
        |Lobet den Herren, denn er ist freundlich||374||232||227||229||227||&nbsp;
        |-
        |Lobt Gott, ihr Christen, allzugleich||375||233||276||232||276||&nbsp;
        |-
        |Lobt Gott, ihr Christen, allzugleich||376||234||341||233||342||&nbsp;
        |-
        |Mach's mit mir, Gott, nach deiner Güt'||377||237||44||236||44||&nbsp;
        |-
        |Meine Augen schliess' ich jetzt||378||240||258||237||258||&nbsp;
        |-
        |Meinen Jesum lass' ich nicht, Jesus||379||241||151||247||151||&nbsp;
        |-
        |Meinen Jesum lass' ich nicht, weil||380||242||298||246||299||&nbsp;
        |-
        |Meines Lebens letzte Zeit||381||248||345||248||346||&nbsp;
        |-
        |Mit Fried' und Freud' ich fahr' dahin||382||249||49||251||49||&nbsp;
        |-
        |Mitten wir im Leben sind||383||252||214||252||214||&nbsp;
        |-
        |Nicht so traurig, nicht so sehr||384||253||149||253||149||&nbsp;
        |-
        |Nun bitten wir den heiligen Geist||385||254||36||256||36||&nbsp;
        |-
        |Nun danket alle Gott||386||257||32||259||32||Leuthen Chorale
        |-
        |Nun freut euch, Gottes Kinder all'||387||260||185||260||185||&nbsp;
        |-
        |Nun freut euch, lieben Christen g'mein||388||261||183||263||183||&nbsp;
        |-
        |Nun lob', mein' Seel', den Herren||389||269||268||271||268||&nbsp;
        |-
        |Nun lob', mein Seel', den Herren||390||270||295||272||296||&nbsp;
        |-
        |Nun preiset alle Gottes Barmherzigkeit||391||273||222||273||222||&nbsp;
        |-
        |Nun ruhen alle Wälder||392||298||288||295||289||melody known as "Innsbruck, ich muss dich lassen"/"O Welt ich muss dich lassen"
        |-
        |O Welt, sieh hier dein Leben||393||289||275||296||275||melody known as "Innsbruck, ich muss dich lassen"/"O Welt ich muss dich lassen"
        |-
        |O Welt, sieh hier dein Leben||394||290||365||297||366||melody known as "Innsbruck, ich muss dich lassen"/"O Welt ich muss dich lassen"
        |-
        |O Welt, sieh hier dein Leben||395||291||362||298||363||&nbsp;
        |-
        |Nun sich der Tag geendet hat||396||274||240||274||240||&nbsp;
        |-
        |O Ewigkeit, du Donnerwort||397||275||274||276||274||BWV 513 & Notebook for Anna Magdalena Bach
        |-
        |O Gott, du frommer Gott||398||277||311||282||312||BWV 197a "Ehre sei Gott in der Höhe" ("Ich freue mich in dir")
        |-
        |O Gott, du frommer Gott||399||282||314||277||315||&nbsp;
        |-
        |O Herzensangst, o Bangigkeit||400||284||173||284||173||&nbsp;
        |-
        |O Lamm Gottes, unschuldig||401||285||165||285||165||&nbsp;
        |-
        |O Mensch, bewein' dein' Sünde gross||402||286||201||286||201||&nbsp;
        |O Mensch, bewein' dein' Sünde gross||402||286||305||286||306||&nbsp;
        |-
        |O Mensch, schaue Jesum Christum an||403||287||203||287||203||&nbsp;
        |-
        |O Traurigkeit, o Herzeleid||404||288||60||288||57||&nbsp;
        |-
        |O wie selig seid ihr doch, ihr Frommen||405||299||213||299||213||No. 65 in Schemelli
        |-
        |O wie selig seid ihr doch, ihr Frommen||406||300||219||300||219||&nbsp;
        |-
        |O wir armen Sünder||407||301||202||301||202||&nbsp;
        |-
        |Schaut, ihr Sünder||408||303||171||303||171||&nbsp;
        |-
        |Sei gegrüsset, Jesu gütig||410||307||172||308||172||No. 22 in Schemelli
        |-
        |Singet dem Herrn ein neues Lied||411||309||246||310||246||&nbsp;
        |-
        |So gibst du nun, mein Jesu, gute Nacht||412||310||206||311||206||No. 26 in Schemelli
        |-
        |Sollt' ich meinem Gott nicht singen||413||311||220||312||220||No. 18 in Schemelli
        |-
        |Uns ist ein Kindlein heut' gebor'n||414||313||148||0||148||Not in Musica Budapest
        |-
        |Valet will ich dir geben||415||314||24||315||24||&nbsp;
        |-
        |Vater unser im Himmelreich||416||316||47||319||47||BWV 245
        |-
        |Von Gott will ich nicht lassen||417||324||363||326||364||&nbsp;
        |-
        |Von Gott will ich nicht lassen||418||325||331||327||332||&nbsp;
        |-
        |Von Gott will ich nicht lassen||419||326||114||328||114||&nbsp;
        |-
        |Warum betrübst du dich, mein Herz||420||331||145||332||145||&nbsp;
        |-
        |Warum betrübst du dich, mein Herz||421||332||299||333||300||&nbsp;
        |-
        |Warum sollt' ich mich denn grämen||422||334||356||335||357||&nbsp;
        |-
        |Was betrübst du dich, mein Herze||423||336||237||336||237||&nbsp;
        |-
        |Was bist du doch, o Seele, so betrübet||424||337||193||337||193||No. 55 in Schemelli
        |-
        |Was willst du dich, o meine Seele||425||349||241||350||241||&nbsp;
        |-
        |Weltlich Ehr' und zeitlich Gut||426||351||211||351||211||&nbsp;
        |-
        |Wenn ich in Angst und Not||427||352||147||352||147||&nbsp;
        |-
        |Wenn mein Stündlein vorhanden ist||428||353||321||355||322||&nbsp;
        |-
        |Wenn mein Stündlein vorhanden ist||429||354||51||356||52||&nbsp;
        |-
        |Wenn mein Stündlein vorhanden ist||430||355||350||357||351||&nbsp;
        |-
        |Wenn wir in höchsten Nöten sein||431||358||68||358||68||&nbsp;
        |-
        |Wenn wir in höchsten Nöten sein||432||359||247||359||247||&nbsp;
        |-
        |Wer Gott vertraut, hat wohl gebaut||433||366||135||360||137||&nbsp;
        |-
        |Wer nur den lieben Gott läßt walten||434||367||146||367||146||&nbsp;
        |-
        |Wie bist du, Seele, in mir so gar betrübt||435||374||242||374||242||&nbsp;
        |-
        |Wie schön leuchtet der Morgenstern||436||375||278||378||278||&nbsp;
        |-
        |Wir glauben all' an einen Gott||437||382||133||382||133||&nbsp;
        |-
        |Wo Gott zum Haus nicht gibt sein' Gunst||438||389||157||388||157||&nbsp;'''
    
        self.byTitle = {}
        self.byBWV = {}
        self.byKalmus = {}
        self.byBaerenreiter = {}
        self.byBudapest = {}
        self.byRiemenschneider = {}
        
        for line in allCat.splitlines():
            line = line.strip()
            if line.startswith('|-'):
                continue
            else:
                line = line[1:]
                (title,bwv,kalmus,baerenreiter,budapest,riemenschneider,notes) = line.split('||')
                if notes == u'&nbsp;':
                    notes = None
                lineDict = {'title': title, 'bwv': int(bwv),'kalmus': int(kalmus),
                            'baerenreiter': int(baerenreiter), 'budapest': int(budapest),
                            'riemenschneider': int(riemenschneider), 'notes': notes} 
                self.byTitle[title] = lineDict
                self.byBWV[int(bwv)] = lineDict
                self.byKalmus[int(kalmus)] = lineDict
                self.byBaerenreiter[int(baerenreiter)] = lineDict
                self.byBudapest[int(budapest)] = lineDict
                self.byRiemenschneider[int(riemenschneider)] = lineDict
                
class BachChoraleListRKBWV(object):
    '''
    A searchable list of BachChorales by various numbering systems:
    
    Note that multiple chorales share the same title, so it's best to
    iterate over one of the other lists to get them all.
    
    The list of chorales comes from http://www.jsbchorales.net/ which contains
    all chorales in the corpus, but which only has numbers for the kalmus,
    riemenschneider, and bwv numbering systems.


    >>> from music21 import *
    >>> bcl = corpus.BachChoraleListRKBWV()
    >>> info155 = bcl.byRiemenschneider[155]
    >>> for key in info155.keys():
    ...   print key, info155[key]
    kalmus 173
    riemenschneider 155
    bwv 344
    title Hilf, Herr Jesu, laß gelingen 1
    >>> #_DOCS_SHOW c = corpus.parse('bach/bwv' + str(info155['bwv']))
    >>> #_DOCS_SHOW c.show() # shows Bach BWV344

    More fully:
    
    >>> b = corpus.parse('bwv' + str(corpus.BachChoraleList().byRiemenschneider[2]['bwv']))
    >>> b
    <music21.stream.Score ...>
    
    '''
    def __init__(self):
        self.prepareList()
        
    def prepareList(self):
        '''
        puts a list of Bach Chorales into dicts of dicts called
        
        self.byKalmus
        self.byBWV
        self.byRiemenschneider
        self.byTitle
        
        '''
        # ----Existence problems with R82,141,210,245,309,337----------------------- #
        # 82---||---46.6s---||---O großer Gott von Macht---||---0                    #
        # 141---||---409---||---Seelenbräutigam, Jesu, Gottes Lamm---||---306        #
        # 210---||---275---||---Christe, du Beistand deiner Kreuz-gemeine---||---35  #
        # 245---||---274---||---Christe, der du bist Tag und Licht---||---34         #
        # 309---||---267-a---||---An Wasserflüssen Babylon---||---23                 #
        # 337---||---24.6s---||---O Gott, du frommer Gott---||---0                   #
        # -------------------------------------------------------------------------- #
        
        
        allCat = r'''1---||---269---||---Aus meines Herzens Grunde---||---30
            2---||---347---||---Ich dank dir, lieber Herre---||---176
            3---||---153.1---||---Ach Gott, vom Himmel sieh' darein---||---5
            4---||---86.6---||---Es ist das Heil uns kommen her---||---86
            5---||---267---||---An Wasserflüssen Babylon---||---23
            6---||---281---||---Christus, der ist mein Leben---||---46
            7---||---17.7---||---Nun lob, mein Seel, den Herren---||---271
            8---||---40.8---||---Freuet euch, ihr Christen alle---||---105
            9---||---248.12-2---||---Ermuntre dich, mein schwacher Geist---||---80
            10---||---38.6---||---Aus tiefer Not schrei ich zu dir 1---||---31
            11---||---41.6---||---Jesu, nun sei gepreiset---||---0
            12---||---65.2---||---Puer natus in Bethlehem---||---302
            13---||---33.6---||---Allein zu dir, Herr Jesu Christ---||---16
            15---||---277---||---Christ lag in Todesbanden---||---38
            16---||---311---||---Es woll uns Gott genädig sein 2---||---95
            18---||---318---||---Menschenkind, merk eben---||---115
            19---||---351---||---Ich hab mein Sach Gott heimgestellt---||---182
            20---||---302---||---Ein feste Burg ist unser Gott---||---74
            21---||---153.5---||---Herzlich tut mich verlangen---||---160
            23---||---28.6---||---Helft mir Gotts Güte preisen---||---124
            24---||---415---||---Valet will ich dir geben---||---314
            26---||---20.7---||---O Ewigkeit, du Donnerwort---||---276
            26---||---20.11---||---O Ewigkeit, du Donnerwort---||---276
            27---||---308---||---Es spricht der Unweisen Mund---||---92
            28---||---36.8-2---||---Nun komm, der Heiden Heiland---||---264
            29---||---32.6---||---Wie nach einer Wasserquelle---||---102
            30---||---363---||---Jesus Christus, unser Heiland, der von uns den Gottes Zorn wandt---||---206
            31---||---256---||---Wo Gott der Herr nicht bei uns hält---||---385
            32---||---386---||---Nun danket alle Gott---||---257
            33---||---330---||---Herr, ich habe mißgehandelt---||---137
            34---||---305---||---Erbarm dich mein, o Herre Gott---||---78
            35---||---248.53-5---||---Gott des Himmels und der Erden---||---114
            36---||---385---||---Nun bitten wir den heiligen Geist---||---254
            37---||---352---||---Wachet doch, erwacht, ihr Schläfer---||---185
            39---||---259---||---Ach, was soll ich Sünder machen---||---10
            40---||---255---||---Ach Gott und Herr, wie groß und schwer---||---3
            41---||---65.7---||---Was mein Gott will, das g'scheh allzeit---||---346
            42---||---67.7---||---Du Friedefürst, Herr Jesu Christ---||---68
            43---||---8.6---||---Liebster Gott, wann werd ich sterben---||---227
            44---||---377---||---Mach's mit mir, Gott, nach deiner Güt---||---237
            45---||---108.6---||---Kommt her zu mir, spricht Gottes Söhn---||---224
            46---||---248.9-1---||---Vom Himmel hoch, da komm ich her---||---0
            47---||---416---||---Vater unser im Himmelreich---||---316
            48---||---26.6---||---Ach wie nichtig, ach wie flüchtig---||---11
            49---||---382---||---Mit Fried und Freud ich fahr dahin---||---249
            50---||---244.37---||---O Welt, ich muß dich lassen---||---292
            51---||---91.6---||---Gelobet seist du, Jesu Christ---||---109
            52---||---429---||---Wenn mein Stündlein vorhanden ist 1---||---354
            53---||---122.6---||---Das neugeborne Kindelein---||---57
            54---||---151.5---||---Kommt her, ihr lieben Schwesterlein---||---235
            55---||---110.7---||---Wir Christenleut---||---380
            56---||---121.6---||---Christum wir sollen loben schon---||---42
            57---||---404---||---O Traurigkeit, o Herzeleid---||---288
            58---||---174.5---||---Herzlich lieb hab ich dich, o Herr---||---153
            59---||---245.3---||---Herzliebster Jesu, was hast du verbrochen---||---168
            60---||---133.6---||---O stilles Gotteslamm---||---181
            61---||---159.5---||---Jesu Kreuz, Leiden und Pein---||---194
            62---||---197.10---||---Wer nur den lieben Gott läßt walten---||---370
            63---||---245.11---||---O Welt, ich muß dich lassen---||---293
            65---||---144.3---||---Was Gott tut, das ist wohlgetan---||---338
            66---||---280---||---Es woll uns Gott genädig sein 1---||---43
            67---||---39.7---||---Wie nach einer Wasserquelle---||---104
            68---||---431---||---Wenn wir in höchsten Nöten sein---||---358
            69---||---226.2---||---Komm, heiliger Geist, Herre Gott---||---221
            70---||---322---||---Gott sei gelobet und gebenedeiet---||---119
            72---||---6.6---||---Erhalt uns, Herr, bei deinem Wort---||---79
            73---||---334---||---Wenn mein Stündlein vorhanden ist 2---||---141
            74---||---244.54---||---Herzlich tut mich verlangen---||---162
            75---||---291---||---Das walt' mein Gott, Vater, Sohn und heiliger Geist---||---59
            76---||---30.6---||---Wie nach einer Wasserquelle---||---103
            77---||---248.46-5---||---In dich hab ich gehoffet, Herr 1---||---214
            78---||---244.3---||---Herzliebster Jesu, was hast du verbrochen---||---166
            79---||---342---||---Heut' triumphieret Gottes Sohn---||---171
            80---||---244.44---||---Herzlich tut mich verlangen---||---159
            81---||---245.15---||---Christus, der uns selig macht---||---49
            83---||---245.14---||---Jesu Kreuz, Leiden und Pein---||---192
            84---||---197.5---||---Nun bitten wir den heiligen Geist---||---255
            85---||---45.7---||---Die Wollust dieser Welt---||---278
            86---||---36.4-2---||---Wie schön leuchtet der Morgenstern---||---377
            87---||---56.5---||---Du geballtes Weltgebäude---||---72
            88---||---28.6---||---Helft mir Gotts Güte preisen---||---124
            90---||---57.8---||---Hast du denn, Liebster, dein Angesicht gänzlich verborgen---||---231
            91---||---42.7---||---Gib unsern Fürsten und aller Obrigkeit (ending)---||---322
            91---||---42.7---||---Verleih uns Frieden gnädiglich (beginning)---||---322
            92---||---168.6---||---Wenn mein Stündlein vorhanden ist 2---||---143
            93---||---194.12---||---Nun laßt uns Gott dem Herren---||---268
            94---||---47.5---||---Warum betrübst du dich, mein Herz---||---333
            95---||---55.5---||---Werde munter, mein Gemüte---||---362
            96---||---87.7---||---Jesu, meine Freude---||---201
            97---||---169.7---||---Nun bitten wir den heiligen Geist---||---256
            99---||---16.6---||---Helft mir Gotts Güte preisen---||---125
            100---||---18.5-w---||---Durch Adams Fall ist ganz verderbt---||---73
            101---||---164.6---||---Herr Christ, der einge Gottes-Söhn---||---127
            102---||---43.11---||---Ermuntre dich, mein schwacher Geist---||---81
            103---||---13.6---||---O Welt, ich muß dich lassen---||---295
            104---||---88.7---||---Wer nur den lieben Gott läßt walten---||---368
            105---||---244.46---||---Herzliebster Jesu, was hast du verbrochen---||---167
            106---||---245.28---||---Jesu Kreuz, Leiden und Pein---||---193
            107---||---245.40---||---Herzlich lieb hab ich dich, o Herr---||---154
            108---||---245.26---||---Valet will ich dir geben---||---315
            109---||---187.7---||---Da Christus geboren war---||---308
            110---||---102.7---||---Vater unser im Himmelreich---||---320
            111---||---245.17---||---Herzliebster Jesu, was hast du verbrochen---||---169
            112---||---84.5---||---Wer nur den lieben Gott läßt walten---||---373
            113---||---245.37---||---Christus, der uns selig macht---||---50
            114---||---419---||---Von Gott will ich nicht lassen---||---326
            115---||---244.25---||---Was mein Gott will, das g'scheh allzeit---||---342
            116---||---29.8---||---Nun lob, mein Seel, den Herren---||---272
            117---||---244.10---||---O Welt, ich muß dich lassen---||---294
            118---||---244.32---||---In dich hab ich gehoffet, Herr 1---||---213
            119---||---176.6---||---Es woll uns Gott genädig sein 1---||---45
            120---||---103.6---||---Was mein Gott will, das g'scheh allzeit---||---348
            121---||---244.40---||---Werde munter, mein Gemüte---||---361
            122---||---85.6---||---Ist Gott mein Schild und Helfersmann---||---216
            123---||---183.5---||---Helft mir Gotts Güte preisen---||---126
            124---||---268---||---Auf, auf, mein Herz, und du, mein ganzer Sinn---||---24
            125---||---104.6---||---Allein Gott in der Höh sei Ehr---||---0
            126---||---18.5-l---||---Durch Adams Fall ist ganz verderbt---||---0
            127---||---298---||---Dies sind die heiligen zehn Gebot---||---66
            128---||---263---||---Alles ist an Gottes Segen---||---19
            129---||---369---||---Keinen hat Gott verlassen---||---217
            130---||---324---||---Meine Seel erhebt den Herren---||---121
            131---||---373---||---Liebster Jesu, wir sind hier---||---228
            132---||---371---||---Kyrie, Gott Vater in Ewigkeit---||---225
            133---||---437---||---Wir glauben all an einen Gott, Schöpfer Himmels und der Erden---||---382
            134---||---301---||---Du geballtes Weltgebäude---||---71
            135---||---317---||---Gott der Vater wohn uns bei---||---113
            136---||---332---||---Herr Jesu Christ, dich zu uns wend---||---139
            137---||---433---||---Wer Gott vertraut, hat wohl gebaut---||---366
            138---||---64.8---||---Jesu, meine Freude---||---200
            139---||---248.33-3---||---Warum sollt ich mich denn grämen---||---335
            140---||---367---||---In allen meinen Taten---||---211
            142---||---40.6---||---Schwing dich auf zu deinem Gott---||---305
            143---||---368---||---In dulci jubilo---||---215
            144---||---339---||---Aus tiefer Not schrei ich zu dir 2---||---151
            145---||---420---||---Warum betrübst du dich, mein Herz---||---331
            146---||---434---||---Wer nur den lieben Gott läßt walten---||---367
            147---||---427---||---Wenn ich in Angst und Not mein' Augen heb empor---||---352
            148---||---414---||---Danket dem Herrn, heuf und allzeit---||---313
            149---||---384---||---Nicht so traurig, nicht so sehr---||---253
            150---||---27.6---||---Welt, ade! ich bin dein müde---||---350
            151---||---379---||---Jesus ist mein Aufenthalt---||---241
            152---||---154.8---||---Meinen Jesum laß ich nicht, weil er sich für mich gegeben---||---244
            153---||---262---||---Alle Menschen müssen sterben 1---||---17
            154---||---293---||---Der du bist drei in Einigkeit---||---61
            155---||---344---||---Hilf, Herr Jesu, laß gelingen 1---||---173
            156---||---3.6---||---Herr Jesu Christ, meins Lebens Licht---||---8
            157---||---438---||---Wo Gott zum Haus nicht gibt sein Gunst---||---389
            158---||---294---||---Der Tag der ist so freudenreich---||---62
            159---||---264---||---Als der gütige Gott vollenden wollt sein Wort---||---20
            160---||---64.2---||---Gelobet seist du, Jesu Christ---||---108
            161---||---366---||---Ihr Gestirn, ihr hohen Lüfte---||---210
            162---||---288---||---Das alte Jahr vergangen ist---||---55
            163---||---313---||---Für Freuden laßt uns springen---||---106
            164---||---326---||---Ihr Knecht des Herren allzugleich---||---129
            165---||---401---||---O Lamm Gottes, unschuldig---||---285
            166---||---309---||---Es stehn vor Gottes Throne---||---93
            167---||---300---||---Du großer Schmerzensmann, vom Vater so geschlagen---||---70
            168---||---341---||---Heut ist, o Mensch, ein großer Trauertag---||---170
            169---||---355---||---Jesu, der du selbsten wohl---||---189
            171---||---408---||---Schaut, ihr Sünder! Ihr macht mir große Pein---||---303
            172---||---410---||---Sei gegrüßet, Jesu gütig---||---307
            173---||---400---||---O Herzensangst, o Bangigkeit und Zagen---||---284
            174---||---364---||---Jesus Christus, unser Heiland, der den Tod überwandt---||---207
            175---||---365---||---Jesus, meine Zuversicht---||---208
            176---||---306---||---Erstanden ist der heilig Christ---||---85
            177---||---253---||---Danket dem Herrn heut und allzeit---||---1
            178---||---122.6---||---Das neugeborne Kindelein---||---57
            179---||---140.7---||---Wachet auf, ruft uns die Stimme---||---329
            180---||---265---||---Als Jesus Christus in der Nacht---||---21
            181---||---319---||---Gott hat das Evangelium---||---116
            183---||---388---||---Nun freut euch, lieben Christen, g'mein 1---||---261
            184---||---4.8---||---Christ lag in Todesbanden---||---41
            185---||---387---||---Ihr lieben Christen, freut euch nun---||---260
            186---||---254---||---Ach Gott, erhör mein Seufzen und Wehklagen---||---2
            187---||---370---||---Komm, Gott Schöpfer, heiliger Geist---||---218
            188---||---349---||---Ach Herre Gott, mich treibt die Not---||---179
            189---||---336---||---Herr Jesu Christ, wahr' Mensch und Gott---||---146
            190---||---337---||---Herr, nun laß in Frieden---||---148
            192---||---321---||---Gottlob, es geht nunmehr zu Ende---||---118
            193---||---424---||---Was bist du doch, o Seele, so betrübet---||---337
            194---||---123.6---||---Liebster Immanuel, Herzog der Frommen---||---229
            195---||---36.4-2---||---Wie schön leuchtet der Morgenstern---||---377
            196---||---285---||---Da der Herr Christ zu Tische saß---||---52
            197---||---276---||---Christ ist erstanden---||---36
            198---||---283---||---Christus, der uns selig macht---||---48
            199---||---343---||---Hilf, Gott laß mirs gelingen---||---172
            200---||---284---||---Christus ist erstanden, hat überwunden---||---51
            201---||---402---||---Es sind doch selig alle, die im rechten Glauben wandeln---||---286
            202---||---407---||---O wir armen Sünder---||---301
            203---||---403---||---O Mensch, schau Jesum Christum an---||---287
            204---||---166.6---||---Wer nur den lieben Gott läßt walten---||---372
            205---||---328---||---Herr Gott, dich loben wir, Herr Gott, wir danken dir---||---133
            206---||---412---||---So gibst du nun, mein Jesu, gute Nacht---||---310
            207---||---295---||---Spiritus sancti gratia---||---63
            208---||---266---||---Am Sabbat früh Marien drei 1---||---22
            209---||---299---||---Dir, dir, Jehova, will ich singen---||---67
            211---||---426---||---Weltlich Ehr und zeitlich Gut---||---351
            212---||---329---||---Lob sei dir, gütiger Gott---||---136
            213---||---405---||---O wie selig seid ihr doch, ihr Frommen---||---299
            214---||---383---||---Mitten wir im Leben sind---||---252
            216---||---60.5---||---Es ist genug---||---91
            217---||---153.9---||---Herr Jesu Christ, meins Lebens Licht---||---9
            218---||---372---||---Herr, dein Ohren zu mir neige---||---226
            219---||---406---||---Ach, wie groß ist Gottes Güt und Wohltat---||---300
            220---||---413---||---Lasset uns den Herren preisen---||---311
            221---||---338---||---Herr, straf mich nicht in deinem Zorn---||---149
            222---||---391---||---Nun preiset alle Gottes Barmherzigkeit---||---273
            223---||---346---||---Ich dank dir Gott für alle Wohltat---||---175
            224---||---290---||---Das walt Gott Vater und Gott Sohn---||---58
            225---||---316---||---Gott, der du selber bist das Licht---||---112
            226---||---333---||---Herr Jesu Christ, du hast bereit---||---140
            227---||---374---||---Lobet den Herren, denn er ist sehr freundlich---||---232
            228---||---286---||---Vitam quae faciunt---||---53
            229---||---350---||---Mein Hüter und mein Hirt ist Gott der Herre---||---180
            230---||---273---||---Christ, der du bist der helle Tag---||---33
            231---||---296---||---Die Nacht ist kommen, drin wir ruhen sollen---||---64
            232---||---297---||---O höchster Gott, o unser lieber Herre---||---65
            233---||---154.3---||---Werde munter, mein Gemüte---||---365
            234---||---320---||---Gott lebet noch, Seele, was verzagst du doch?---||---117
            235---||---325---||---Heilig, heilig, heilig---||---123
            237---||---423---||---Was betrübst du dich, mein Herze---||---336
            238---||---310---||---Es wird schier der letzte Tag herkommen---||---94
            239---||---292---||---Den Vater dort oben---||---60
            240---||---396---||---Nun sich der Tag geendet hat---||---274
            241---||---425---||---Was willst du dich, o meine Seele, kränken---||---349
            242---||---435---||---Wie bist du, Seele, in mir so gar betrübt---||---374
            243---||---356---||---Jesu, du mein liebstes Leben---||---190
            244---||---357---||---Jesu, Jesu, du bist mein---||---191
            246---||---411---||---Singt dem Herrn ein neues Lied---||---309
            247---||---432---||---Wenn wir in höchsten Nöten sein---||---359
            249---||---260---||---Allein Gott in der Höh sei Ehr---||---12
            250---||---303---||---Ein feste Burg ist unser Gott---||---75
            251---||---345---||---Ich bin ja, Herr, in deiner Macht---||---174
            252---||---362---||---Jesu, nun sei gepreiset---||---203
            253---||---77.6---||---Ach Gott, vom Himmel sieh' darein---||---6
            254---||---25.6---||---Wie nach einer Wasserquelle---||---101
            255---||---64.4---||---Die Wollust dieser Welt---||---280
            256---||---194.6---||---Wie nach einer Wasserquelle---||---100
            257---||---194.12---||---Nun laßt uns Gott dem Herren---||---268
            258---||---378---||---Meine Augen schließ ich jetzt in Gottes Namen zu---||---240
            259---||---42.7---||---Verleih uns Frieden gnädiglich (beginning)---||---322
            259---||---42.7---||---Gib unsern Fürsten und aller Obrigkeit (ending)---||---322
            260---||---307---||---Nun freut euch, lieben Christen, g'mein 2---||---262
            261---||---158.4---||---Christ lag in Todesbanden---||---40
            261---||---279---||---Christ lag in Todesbanden---||---40
            262---||---2.6---||---Ach Gott, vom Himmel sieh' darein---||---7
            263---||---227.1---||---Jesu, meine Freude---||---196
            263---||---227.11---||---Jesu, meine Freude---||---196
            264---||---361---||---Jesu, meines Herzens Freud'---||---202
            265---||---144.6---||---Was mein Gott will, das g'scheh allzeit---||---343
            266---||---48.7---||---Wenn mein Stündlein vorhanden ist 2---||---144
            267---||---90.5---||---Vater unser im Himmelreich---||---319
            268---||---389---||---Nun lob, mein Seel, den Herren---||---269
            269---||---353---||---Wachet doch, erwacht, ihr Schläfer---||---186
            270---||---161.6---||---Herzlich tut mich verlangen---||---161
            271---||---315---||---Gib dich zufrieden und sei stille---||---111
            272---||---348---||---Ich dank dir, lieber Herre---||---177
            273---||---80.8---||---Ein feste Burg ist unser Gott---||---76
            274---||---397---||---O Ewigkeit, du Donnerwort---||---275
            275---||---393---||---O Welt, ich muß dich lassen---||---289
            276---||---375---||---Kommt her, ihr lieben Schwesterlein---||---233
            277---||---340---||---Herzlich lieb hab ich dich, o Herr---||---152
            278---||---436---||---Wie schön leuchtet der Morgenstern---||---375
            279---||---48.3---||---Ach Gott und Herr, wie groß und schwer---||---4
            280---||---304---||---Eins ist not, ach Herr, dies eine---||---77
            281---||---89.6---||---Auf meinen lieben Gott---||---26
            282---||---25.6---||---Wie nach einer Wasserquelle---||---101
            283---||---227.7---||---Jesu, meine Freude---||---199
            284---||---127.5---||---Wenn einer schon ein Haus aufbaut---||---147
            285---||---257---||---Wo Gott der Herr nicht bei uns hält---||---388
            286---||---270---||---Herzlich tut mich verlangen---||---157
            287---||---331---||---Herr, ich habe mißgehandelt---||---138
            288---||---314---||---Gelobet seist du, Jesu Christ---||---107
            289---||---392---||---Nun ruhen alle Wälder---||---298
            290---||---9.7---||---Es ist das Heil uns kommen her---||---87
            291---||---94.8---||---Die Wollust dieser Welt---||---281
            292---||---101.7---||---Vater unser im Himmelreich---||---318
            293---||---69.6-a---||---Was Gott tut, das ist wohlgetan---||---0
            294---||---113.8---||---Wenn mein Stündlein vorhanden ist 2---||---142
            295---||---335---||---Rex Christe factor omnium---||---145
            296---||---390---||---Nun lob, mein Seel, den Herren---||---270
            297---||---78.7---||---Wachet doch, erwacht, ihr Schläfer---||---188
            298---||---19.7---||---Wie nach einer Wasserquelle---||---99
            299---||---380---||---Meinen Jesum laß ich nicht---||---242
            300---||---421---||---Warum betrübst du dich, mein Herz---||---332
            301---||---114.7---||---Wo Gott, der Herr, nicht bei uns hält---||---386
            302---||---343---||---Hilf, Gott, laß mirs gelingen---||---172
            303---||---96.6---||---Herr Christ, der einge Gottes-Söhn---||---128
            304---||---5.7---||---Auf meinen lieben Gott---||---28
            305---||---36.4-2---||---Wie schön leuchtet der Morgenstern---||---377
            306---||---402---||---Es sind doch selig alle, die im rechten Glauben wandeln---||---286
            307---||---283---||---Christus, der uns selig macht---||---48
            310---||---245.22---||---Mach's mit mir, Gott, nach deiner Güt---||---239
            311---||---287---||---Jesus Christ, unser Herre---||---54
            312---||---398---||---Die Wollust dieser Welt---||---277
            313---||---112.5---||---Allein Gott in der Höh sei Ehr---||---14
            314---||---289---||---Das alte Jahr vergangen ist---||---56
            315---||---399---||---O Gott, du frommer Gott---||---282
            316---||---282---||---Christus, der ist mein Leben---||---47
            317---||---156.6---||---Aus tiefer Not schrei ich zu dir 2---||---150
            318---||---339---||---Aus tiefer Not schrei ich zu dir 2---||---151
            319---||---325---||---Heilig, heilig, heilig---||---123
            320---||---323---||---Meine Seel erhebt den Herren---||---120
            321---||---40.3---||---Wir Christenleut---||---379
            322---||---428---||---Wenn mein Stündlein vorhanden ist 1---||---353
            323---||---172.6---||---Wie schön leuchtet der Morgenstern---||---376
            324---||---81.7---||---Jesu, meine Freude---||---197
            325---||---83.5---||---Mit Fried und Freud ich fahr dahin---||---250
            326---||---104.6---||---Allein Gott in der Höh sei Ehr---||---13
            327---||---190.7---||---Jesu, nun sei gepreiset---||---205
            329---||---251---||---Es ist das Heil uns kommen Her---||---89
            330---||---252---||---Nun danket alle Gott---||---258
            331---||---136.6---||---Auf meinen lieben Gott---||---27
            332---||---418---||---Von Gott will ich nicht lassen---||---325
            333---||---69.6---||---Es woll uns Gott genädig sein 2---||---97
            334---||---327---||---Ihr Knecht des Herren allzugleich---||---132
            335---||---155.5---||---Es ist das Heil uns kommen her---||---88
            336---||---258---||---Wo Gott, der Herr, nicht bei uns hält---||---383
            338---||---145-a---||---Jesus, meine Zuversicht---||---209
            339---||---179.6---||---Wer nur den lieben Gott läßt walten---||---371
            340---||---272---||---Lobet Gott, unsern Herren---||---32
            341---||---37.6---||---Ich dank dir, lieber Herre---||---178
            342---||---376---||---Kommt her, ihr lieben Schwesterlein---||---234
            343---||---11.6---||---Ermuntre dich, mein schwacher Geist---||---82
            344---||---248.23-2---||---Vom Himmel hoch, da komm ich her---||---0
            345---||---248.5---||---Herzlich tut mich verlangen---||---165
            346---||---381---||---Meines Lebens letzte Zeit---||---248
            347---||---250---||---Was Gott tut das ist wohlgetan---||---339
            348---||---70.11---||---Meinen Jesum laß ich nicht, weil er sich für mich gegeben---||---243
            349---||---103.6---||---Was mein Gott will, das g'scheh allzeit---||---348
            350---||---360---||---Werde munter, mein Gemüte---||---364
            351---||---430---||---Wenn mein Stündlein vorhanden ist 1---||---355
            352---||---312---||---Es woll uns Gott genädig sein 2---||---96
            353---||---112.5---||---Allein Gott in der Höh sei Ehr---||---14
            355---||---44.7---||---O Welt, ich muß dich lassen---||---296
            356---||---358---||---Jesu, meine Freude---||---195
            357---||---422---||---Warum sollt ich mich denn grämen---||---334
            358---||---10.7---||---Meine Seel erhebt den Herren---||---122
            359---||---261---||---Allein zu dir, Herr Jesu Christ---||---15
            360---||---248.35-3---||---Wir Christenleut---||---381
            361---||---248.12-2---||---Ermuntre dich, mein schwacher Geist---||---80
            362---||---248.59-6---||---Nun freut euch, lieben Christen, g'mein 2---||---263
            363---||---395---||---O Welt, ich muß dich lassen---||---291
            364---||---417---||---Von Gott will ich nicht lassen---||---324
            365---||---359---||---Werde munter, mein Gemüte---||---363
            366---||---394---||---O Welt, ich muß dich lassen---||---290
            367---||---271---||---Herzlich tut mich verlangen---||---158
            368---||---248.42-4---||---Hilf, Herr Jesu, laß gelingen 2---||---0
            369---||---354---||---Wachet doch, erwacht, ihr Schläfer---||---187
            370---||---74.8---||---Kommt her zu mir, spricht Gottes Söhn---||---223
            371---||---278---||---Christ lag in Todesbanden---||---39'''
    
        self.byTitle = {}
        self.byBWV = {}
        self.byKalmus = {}
        self.byRiemenschneider = {}
        
        for line in allCat.splitlines():
            line = line.strip()
            (riemenschneider,bwv,title,kalmus) = line.split('---||---')
            lineDict = {'title': title, 'bwv': bwv,'kalmus': int(kalmus),
                        'riemenschneider': int(riemenschneider)} 
            self.byTitle[title] = lineDict
            self.byBWV[bwv] = lineDict
            self.byKalmus[int(kalmus)] = lineDict
            self.byRiemenschneider[int(riemenschneider)] = lineDict
 


class BachChoraleIterator(object):
    '''
    This is a class for iterating over many Bach Chorales. It is designed to make it easier to use
    one of music21's most accessible datasets. It will parse each chorale in the selected
    range in a lazy fashion so that a list of chorales need not be parsed up front. To select a
    range of chorales, first select a .numberingSystem ('riemenschneider', 'bwv', 'kalmus', 'budapest', 
    'baerenreiter', or 'title'). Then, set .currentNumber to the lowest number in the range and
    .highestNumber to the highest in the range. This can either be done by catalogue number
    (iterationType = 'number') or by index (iterationType = 'index').
    
    Changing the numberingSystem will reset the iterator and change the range values to span the entire numberList.
    The iterator can be initialized with three parameters (currentNumber, highestNumber, numberingSystem). For example
    BachChoraleIterator(1,26,'riemenschneider') iterates through the riemenschneider numbered chorales from 1 to 26.
    Additionally, the following kwargs can be set:
    
    returnType = either 'stream' or 'filename'
    
    iterationType = either 'number' or 'index'
    
    titleList = [list, of, titles]
    
    numberList = [list, of, numbers]
    
    >>> from music21 import *
    >>> for chorale in corpus.BachChoraleIterator(1,4, returnType = 'filename'):
    ...    print chorale
    bach/bwv269
    bach/bwv347
    bach/bwv153.1
    bach/bwv86.6
    
    
    >>> BCI = corpus.BachChoraleIterator()
    >>> BCI.numberingSystem
    'riemenschneider'
    
    >>> BCI.currentNumber
    1
    
    >>> BCI.highestNumber
    371
    
    An exception will be raised if the number set is not in the numbering system selected, or if the
    numbering system selected is not valid.
    
    >>> BCI.currentNumber = 25
    Traceback (most recent call last):
    ...
    CorpusException: 25 does not correspond to a chorale in the riemenschneider numbering system
    
    >>> BCI.numberingSystem = 'not a numbering system'
    Traceback (most recent call last):
    ...
    CorpusException: not a numbering system is not a valid numbering system for Bach Chorales.
    
    If the numberingSystem 'title' is selected, the iterator must be initialized with a list of titles.
    It will iterate through the titles in the order of the list.

    >>> BCI.numberingSystem = 'title'
    >>> BCI.returnType = 'filename'
    >>> BCI.titleList = ['Jesu, meine Freude', 'Mit Fried und Freud ich fahr dahin', 'Not a Chorale']
    Not a Chorale will be skipped because it is not a recognized title
    
    >>> for chorale in BCI:
    ...    print chorale
    bach/bwv358
    bach/bwv83.5
    
    Finally, the numberList, which by default includes all chorales in the chosen numberingSystem,
    can be set like the titleList. In the following example, note that the first chorale in the given
    numberList will not be part of the iteration because the first currentNumber is set to 2 at the 
    start by the first argument. (If iterationType = 'index' setting the currentNumber to 1 and the
    highestNumber to 7 would have the same effect as the given example.
    
    >>> BCI = corpus.BachChoraleIterator(2, 371, numberingSystem = 'riemenschneider', numberList = [1,2,3,4,6,25,190,371], returnType = 'filename')
    25 will be skipped because it is not in the numberingSystem riemenschneider
    
    >>> for chorale in BCI:
    ...    print chorale
    bach/bwv347
    bach/bwv153.1
    bach/bwv86.6
    bach/bwv281
    bach/bwv337
    bach/bwv278
    
    '''
    _DOC_ORDER = ['numberingSystem', 'currentNumber', 'highestNumber', 'titleList', 'numberList', 'returnType', 'iterationType']
    
    def __init__(self, currentNumber = None, highestNumber = None, numberingSystem = 'riemenschneider', **kwargs):
        '''
        By default: numberingSystem = 'riemenschneider', currentNumber = 1, highestNumber = 371, iterationType = 'number',
        and returnType = 'stream'
        '''
        
        '''
        Notes:
        Two BachChoraleList objects are created. These should probably be consolidated, but they contain
        different information at this time. Also, there are problems with entries in BachChoraleListRKBWV
        that need to be addressed. Namely, chorales that share the same key (and thus overwrite eachother)
        and chorales that do not appear to be in the corpus at all.
        '''
        self._currentIndex = None
        self._highestIndex = None
        self._titleList = None
        self._numberList = None
        self._numberingSystem = None
        self._returnType = 'stream'
        self._iterationType = 'number'
        
        self._choraleList1 = BachChoraleList() #For budapest, baerenreiter
        self._choraleList2 = BachChoraleListRKBWV() #for kalmus, riemenschneider, title, and bwv
        
        self.numberingSystem = numberingSystem #This assignment must come before the kwargs
        
        for key in kwargs.keys():
            if key is 'returnType':
                self.returnType = kwargs[key]
            elif key is 'numberList':
                self.numberList = kwargs[key]
            elif key is 'titleList':
                self.titleList = kwargs[key]
            elif key is 'iterationType':
                self.iterationType = kwargs[key]
        
        #These assignements must come after .iterationType

        self.currentNumber = currentNumber
        self.highestNumber = highestNumber

    def __iter__(self):
        return self

    def __len__(self):
        if self.numberingSystem is None:
            raise CorpusException("NumberingSystem not set. Cannot find a length.")
        if self.numberingSystem is 'title':
            return len(self.titleList)
        else:
            return len(self.numberList)
    
    def next(self):
        '''
        At each iteration, the _currentIndex is incremented, and the next chorale is parsed based upon its bwv number which is queried via
        whatever the current numberingSystem is set to. If the _currentIndex becomes higher than the _highestIndex, the iteration stops.
        '''
        if self._currentIndex > self._highestIndex:
            raise StopIteration
        else:
            nextChorale = self._returnCurrent()
            self._currentIndex += 1
            return nextChorale
    
    #---Functions
    def _returnCurrent(self):
        '''
        This returns a chorale based upon the _currentIndex and the numberingSystem. The numberList is the list
        of valid numbers in the selected numbering system. The _currentIndex is the location in the numberList
        of the current iteration. If the numberingSystem is 'title', the chorale is instead queried by Title
        from the titleList and the numberList is ignored.
        
        >>> from music21 import *
        >>> BCI = corpus.BachChoraleIterator()
        >>> riemenschneider1 = BCI._returnCurrent()
        >>> riemenschneider1.show('text')
        {0.0} <music21.text.TextBox "BWV 269">
        {0.0} <music21.text.TextBox "PDF © 2004...">
        {0.0} <music21.metadata.Metadata object at ...>
        {0.0} <music21.stream.Part Soprano>
            {0.0} <music21.instrument.Instrument P1: Soprano: Instrument 1>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.key.KeySignature of 1 sharp>
                {0.0} <music21.meter.TimeSignature 3/4>
                {0.0} <music21.note.Note G>
        ...
        
        
        >>> BCI.currentNumber = BCI.highestNumber
        >>> riemenschneider371 = BCI._returnCurrent()
        >>> riemenschneider371.show('text')
        {0.0} <music21.text.TextBox "BWV 278">
        {0.0} <music21.text.TextBox "PDF © 2004...">
        {0.0} <music21.metadata.Metadata object at ...>
        {0.0} <music21.stream.Part Soprano>
            {0.0} <music21.instrument.Instrument P1: Soprano: Instrument 1>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.key.KeySignature of 1 sharp>
                {0.0} <music21.meter.TimeSignature 4/4>
                {0.0} <music21.note.Note B>
        ...
        
        
        >>> BCI.numberingSystem = 'title'
        >>> BCI._returnCurrent()
        Traceback (most recent call last):
        ...
        CorpusException: Cannot parse Chorales because no titles to parse.
        
        >>> BCI.titleList = ['Christ lag in Todesbanden', 'Aus meines Herzens Grunde']
        >>> christlag = BCI._returnCurrent()
        >>> christlag.show('text')
        {0.0} <music21.text.TextBox "BWV 278">
        {0.0} <music21.text.TextBox "PDF © 2004...">
        {0.0} <music21.metadata.Metadata object at ...>
        {0.0} <music21.stream.Part Soprano>
            {0.0} <music21.instrument.Instrument P1: Soprano: Instrument 1>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.key.KeySignature of 1 sharp>
                {0.0} <music21.meter.TimeSignature 4/4>
                {0.0} <music21.note.Note B>
        ...
        
        >>> BCI.currentNumber += 1
        >>> ausmeines = BCI._returnCurrent()
        >>> ausmeines.show('text')
        {0.0} <music21.text.TextBox "BWV 269">
        {0.0} <music21.text.TextBox "PDF © 2004...">
        {0.0} <music21.metadata.Metadata object at ...>
        {0.0} <music21.stream.Part Soprano>
            {0.0} <music21.instrument.Instrument P1: Soprano: Instrument 1>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.key.KeySignature of 1 sharp>
                {0.0} <music21.meter.TimeSignature 3/4>
                {0.0} <music21.note.Note G>
        ...
        
        
        >>> BCI.numberingSystem = 'kalmus'
        >>> BCI.returnType = 'filename'
        >>> BCI._returnCurrent()
        'bach/bwv253'       
        
        
        '''
        if self.numberingSystem is None:
            raise CorpusException("Cannot parse Chorales because no .numberingSystem set.")
        elif self.numberingSystem is 'title':
            if self._titleList is None:
                raise CorpusException("Cannot parse Chorales because no titles to parse.")
            else:
                filename = 'bach/bwv'+ str(self._choraleList2.byTitle[self.titleList[self._currentIndex]]['bwv'])
        elif self.numberingSystem is 'riemenschneider':
            filename = 'bach/bwv' + str(self._choraleList2.byRiemenschneider[self._numberList[self._currentIndex]]['bwv'])
        elif self.numberingSystem is 'baerenreiter':
            filename = 'bach/bwv' + str(self._choraleList1.byBaerenreiter[self._numberList[self._currentIndex]]['bwv'])
        elif self.numberingSystem is 'budapest':
            filename = 'bach/bwv' + str(self._choraleList1.byBudapest[self._numberList[self._currentIndex]]['bwv'])
        elif self.numberingSystem is 'kalmus':
            filename = 'bach/bwv' + str(self._choraleList2.byKalmus[self._numberList[self._currentIndex]]['bwv'])
        else:
            filename = 'bach/bwv' + str(self._numberList[self._currentIndex])
        
        if self._returnType is 'stream':
            chorale = parse(filename)
            return chorale
        elif self._returnType is 'filename':
            return filename
        else:
            raise Exception("An unexpected returnType %s was introduced. This should not happen." % self._returnType)
        
    def _initializeNumberList(self):
        '''
        This creates the _numberList which the iterator iterates through. It is called each time the numberingSystem
        changes and also whenever the titleList is set. The numbers are drawn from the chorale search objects,
        so any mistakes should be corrected there. Additionally, the initial values of currentNumber and highestNumber
        are set to the lowest and highest numbers in the selected list. If the numberingSystem is 'title', the _numberList
        is set to None, and the currentNumber and highestNumber are set to the lowest and highest indices in the titleList.
        
        >>> from music21 import *
        >>> BCI = corpus.BachChoraleIterator()
        >>> BCI.numberingSystem = 'riemenschneider'
        >>> (BCI._numberList[0], BCI._numberList[40], BCI._numberList[-1])
        (1, 46, 371)
        
        >>> BCI.numberingSystem = 'kalmus'
        >>> (BCI._numberList[0], BCI._numberList[40], BCI._numberList[-1])
        (1, 48, 389)
        
        >>> BCI.numberingSystem = 'bwv'
        >>> (BCI._numberList[0], BCI._numberList[40], BCI._numberList[-1])
        ('10.7', '174.5', '96.6')
        
        >>> BCI.numberingSystem = 'budapest'
        >>> (BCI._numberList[0], BCI._numberList[40], BCI._numberList[-1])
        (0, 66, 388)
        
        >>> BCI.numberingSystem = 'baerenreiter'
        >>> (BCI._numberList[0], BCI._numberList[40], BCI._numberList[-1])
        (1, 134, 370)
        
        >>> BCI.numberingSystem = 'title'
        >>> BCI._numberList
        '''
        
        if self._numberingSystem is 'title':
            self._numberList = None
            self.currentNumber = 0
            if self._titleList is None:
                self.highestNumber = 0
            else:    
                self.highestNumber = len(self.titleList)-1
        else:
            if self._numberingSystem is 'riemenschneider':
                self._numberList = []
                for n in sorted(self._choraleList2.byRiemenschneider.keys()):
                    self._numberList.append(n) #addList = [26, 91, 259, 261, 263] These are the numbers that appear twice and thus stored only once.
            elif self._numberingSystem is 'kalmus':
                self._numberList = []
                for n in sorted(self._choraleList2.byKalmus.keys()):
                    if n is 0: # Need to skip K0 because it is not actually in the number system. Denotes chorales that do not have a Kalmus number.
                        continue
                    self._numberList.append(n)
            elif self._numberingSystem is 'bwv':
                self._numberList = []
                for n in sorted(self._choraleList2.byBWV.keys()): #This does not sort correctly at this time TODO: Make this sort correctly
                    self._numberList.append(n)
            elif self._numberingSystem is 'budapest':
                self._numberList = []
                for n in sorted(self._choraleList1.byBudapest.keys()):
                    self._numberList.append(n)
            elif self._numberingSystem is 'baerenreiter':
                self._numberList = []
                for n in sorted(self._choraleList1.byBaerenreiter.keys()):
                    self._numberList.append(n)
            
            if self.iterationType is 'number':
                self.currentNumber = self._numberList[0]
                self.highestNumber = self._numberList[-1]
            else:
                self.currentNumber = 0
                self.highestNumber = len(self._numberList) - 1
        
    #---Properties
    #- Numbering System    
    def _getNumberingSystem(self):
        if self._numberingSystem is None:
            raise CorpusException("Numbering System not set.")
        else:
            return self._numberingSystem
    
    def _setNumberingSystem(self, value):
        if value in ['bwv', 'kalmus', 'baerenreiter', 'budapest', 'riemenschneider']:
            self._numberingSystem = value
            self._initializeNumberList() #initializes the numberlist and sets current and highest numbers / indices
        elif value is 'title':
            self._numberingSystem = 'title'
            self._setTitleList()
        else:
            raise CorpusException("%s is not a valid numbering system for Bach Chorales." % value)
        
    numberingSystem = property(_getNumberingSystem, _setNumberingSystem, doc='''This property determines which numbering system to iterate through chorales with.
                                                                                It can be set to 'bwv', 'kalmus', 'baerenreiter', 'budapest', or 'riemenschneider'.
                                                                                It can also be set to 'title' in which case the iterator needs to be given a list
                                                                                of chorale titles in .titleList. At this time, the titles need to be exactly as they
                                                                                appear in the dictionary it queries.''')
    
    
    
    #- Title List
    def _getTitleList(self):
        if self._titleList is None:
            return []
        else:
            return self._titleList
    
    def _setTitleList(self, value = []):
        if value == []:
            self._titleList = None
        elif (type(value) is list) is False:
            raise CorpusException("%s is not and must be a list." % value)
        else:
            self._titleList = []
            for v in value:
                if v in self._choraleList2.byTitle.keys():
                    self._titleList.append(v)
                else:
                    print '%s will be skipped because it is not a recognized title' % v    
        if self._titleList == []:
            self._titleList = None
        
        self._initializeNumberList()
    
    titleList = property(_getTitleList, _setTitleList, doc='''This is to store the list of titles to iterate over if .numberingSystem is set to 'title'.''')
    
    
    #- Number List
    def _getNumberList(self):
        if self._numberList is None:
            return []
        else:
            return self._numberList
    
    def _setNumberList(self, value):
        if (type(value) is list) is False:
            raise CorpusException("%s is not and must be a list." % value)
        if self._numberingSystem is 'title':
            self._numberList = None
            raise CorpusException("Cannot set numberList when .numberingSystem is 'title'")
        else:
            if self._numberingSystem is 'riemenschneider':
                self._numberList = []
                for v in sorted(value):
                    if v in self._choraleList2.byRiemenschneider.keys():
                        self._numberList.append(v)
                    else:
                        print "%s will be skipped because it is not in the numberingSystem %s" % (v, self._numberingSystem)
            elif self._numberingSystem is 'kalmus':
                self._numberList = []
                for v in sorted(value):
                    if v in self._choraleList2.byKalmus.keys() and v != 0:
                        self._numberList.append(v)
                    else:
                        print "%s will be skipped because it is not in the numberingSystem %s" % (v, self._numberingSystem)
            elif self._numberingSystem is 'bwv':
                self._numberList = []
                for v in sorted(value):
                    if v in self._choraleList2.byBWV.keys():
                        self._numberList.append(v)
                    else:
                        print "%s will be skipped because it is not in the numberingSystem %s" % (v, self._numberingSystem)
            elif self._numberingSystem is 'budapest':
                self._numberList = []
                for v in sorted(value):
                    if v in self._choraleList1.byBudapest.keys():
                        self._numberList.append(v)
                    else:
                        print "%s will be skipped because it is not in the numberingSystem %s" % (v, self._numberingSystem) 
            elif self._numberingSystem is 'baerenreiter':
                self._numberList = []
                for v in sorted(value):
                    if v in self._choraleList1.byBaerenreiter.keys():
                        self._numberList.append(v)
                    else:
                        print "%s will be skipped because it is not in the numberingSystem %s" % (v, self._numberingSystem)
            
            if self._numberList is None:
                self.currentNumber = 0
                self.highestNumber = 0
            else:
                if self.iterationType is 'number':
                    self.currentNumber = self._numberList[0]
                    self.highestNumber = self._numberList[-1]
                else:
                    self.currentNumber = 0
                    self.highestNumber = len(self._numberList) - 1

    numberList = property(_getNumberList, _setNumberList, doc='''Allows access to the catalogue numbers (or indices if iterationType is 'index')
                                                                    that will be iterated over. This can be set to a specific list of numbers.
                                                                    They will be sorted.''')
    
        
    
    
    #- Current Number
    def _getCurrentNumber(self):
        if self._iterationType is 'index' or self._numberingSystem is 'title':
            return self._currentIndex
        else:
            return self._numberList[self._currentIndex]
        
    def _setCurrentNumber(self, value):
        if self._numberingSystem is None:
            raise Exception("Numbering System is not set.")
        if self._iterationType is 'number':
            if self._numberingSystem is 'title':
                if self._titleList is None:
                    self._currentIndex = 0
                    return
                else:
                    if value in range(len(self.titleList)):
                        if self._highestIndex is None or value <= self._highestIndex:
                            self._currentIndex = value
                        else:
                            raise CorpusException("%s is greater than the highestNumber %s" % (value, self.highestNumber))
                    else:
                        raise CorpusException("%s is not an index in the range of the titleList" % value)
            else:
                if value is None:
                    self._currentIndex = 0
                elif value in self._numberList:
                    newIndex = self._numberList.index(value)
                    if self._highestIndex is None or newIndex <= self._highestIndex:
                        self._currentIndex = newIndex
                    else:
                        raise CorpusException("%s is greater than the HighestNumber %s" % (value, self.highestNumber))
                else:
                    raise CorpusException("%s does not correspond to a chorale in the %s numbering system" % (value, self.numberingSystem))
       
        elif self._iterationType is 'index':
            if self._numberingSystem is 'title':
                if self._titleList is None:
                    self._currentIndex = 0
                    return
                else:
                    if value in range(len(self.titleList)):
                        if self._highestIndex is None or value <= self._highestIndex:
                            self._currentIndex = value
                        else:
                            raise CorpusException("%s is greater than the highestNumber %s" % (value, self.highestNumber))
                    else:
                        raise CorpusException("%s is not an index in the range of the titleList" % value)
            else:
                if value is None:
                    self._currentIndex = 0
                elif value in range(len(self._numberList)):
                    newIndex = value
                    if self._highestIndex is None or newIndex <= self._highestIndex:
                        self._currentIndex = newIndex
                    else:
                        raise CorpusException("%s is greater than the HighestNumber %s" % (value, self.highestNumber))
                else:
                    raise CorpusException("%s does not correspond to a chorale in the %s numbering system" % (value, self.numberingSystem))
        
    currentNumber = property(_getCurrentNumber, _setCurrentNumber, doc='''The currentNumber is the number of the chorale (in the set numberingSystem) for the
                                                                            next chorale to be parsed by the iterator. It is initially the first chorale in whatever
                                                                            numberingSystem is set, but it can be changed to any other number in the numberingSystem
                                                                            as desired as long as it does not go above the highestNumber which is the boundary
                                                                            of the iteration.''')
    
    
    #- Highest Number
    def _getHighestNumber(self):
        if self.iterationType is 'index' or self._numberingSystem is 'title':
            return self._highestIndex
        else:
            return self._numberList[self._highestIndex]
    
    def _setHighestNumber(self, value):
        if self._numberingSystem is None:
            raise Exception("Numbering System is not set.")
        if self.iterationType is 'number':
            if self._numberingSystem is 'title':
                if self._titleList is None:
                    self._highestIndex = 0
                    return
                else:
                    if value in range(len(self.titleList)):
                        if self._currentIndex is None or value >= self._currentIndex:
                            self._highestIndex = value
                        else:
                            raise CorpusException("%s is less than the currentNumber %s" % (value, self.currentNumber))
                    else:
                        raise CorpusException("%s is not an index in the range of the titleList" % value)
            else:
                if value is None:
                    self._highestIndex = len(self._numberList)-1
                elif value in self._numberList:
                    newIndex = self._numberList.index(value)
                    if self._currentIndex is None or newIndex >= self._currentIndex:
                        self._highestIndex = newIndex
                    else:
                        raise CorpusException("%s is less than the CurrentNumber %s" % (value, self.currentNumber))
                else:
                    raise CorpusException("%s does not correspond to a chorale in the %s numbering system" % (value, self.numberingSystem))
                
        elif self.iterationType is 'index':
            if self._numberingSystem is 'title':
                if self._titleList is None:
                    self._highestIndex = 0
                    return
                else:
                    if value in range(len(self.titleList)):
                        if self._currentIndex is None or value >= self._currentIndex:
                            self._highestIndex = value
                        else:
                            raise CorpusException("%s is less than the currentNumber %s" % (value, self.currentNumber))
                    else:
                        raise CorpusException("%s is not an index in the range of the titleList" % value)
            else:
                if value is None:
                    self._highestIndex = len(self._numberList)-1
                elif value in range(len(self._numberList)):
                    newIndex = value
                    if self._currentIndex is None or newIndex >= self._currentIndex:
                        self._highestIndex = newIndex
                    else:
                        raise CorpusException("%s is less than the CurrentNumber %s" % (value, self.currentNumber))
                else:
                    raise CorpusException("%s does not correspond to a chorale in the %s numbering system" % (value, self.numberingSystem))
        
    highestNumber = property(_getHighestNumber, _setHighestNumber, doc='''The highestNumber is the number of the chorale (in the set numberingSystem) for the
                                                                            last chorale to be parsed by the iterator. It is initially the highest numbered chorale in whatever
                                                                            numberingSystem is set, but it can be changed to any other number in the numberingSystem
                                                                            as desired as long as it does not go below the currentNumber of the iteration.''')

    #- Return Type
    def _getReturnType(self):
        return self._returnType
    
    def _setReturnType(self, value):
        if value in ['stream', 'filename']:
            self._returnType = value
        else:
            raise CorpusException("%s is not a proper returnType for this iterator. Only 'stream' and 'filename' are acceptable." % value)
    
    returnType = property(_getReturnType, _setReturnType, doc='''This property determins what the iterator returns; 'stream' is the default and causes the iterator to parse
                                                                    each chorale. If this is set to 'filename', the iterator will return the filename of each chorale but not
                                                                    parse it.''')
    
    
    #- Iteration Type
    def _getIterationType(self):
        return self._iterationType
    
    def _setIterationType(self, value):
        if value in ['number', 'index']:
            self._iterationType = value
            self._initializeNumberList()
        else:
            raise CorpusException("%s is not a proper iterationType for this iterator. Only 'number' and 'index' are acceptable." % value)
    iterationType = property(_getIterationType, _setIterationType, doc='''This property determines how boundary numbers are interpreted, as indices or as catalogue numbers.''')
        

def getHandelMessiah(extList='md'):
    '''
    Return a list of the filenames of all parts of Handel's Messiah.

    >>> from music21 import *
    >>> a = corpus.getHandelMessiah()
    >>> len(a)
    43
    '''
    names = ['movement1-01.md', 'movement1-02.md', 'movement1-03.md', 
             'movement1-04.md', 'movement1-05.md', 
             'movement1-07.md', 'movement1-08.md', 'movement1-09.md', 
             'movement1-10.md', 'movement1-11.md', 'movement1-12.md', 
             'movement1-13.md', 'movement1-15.md', 
             'movement1-17.md', 'movement1-18.md', 'movement1-19.md', 
             'movement1-23.md', 

            'movement2-01.md', 'movement2-03.md', 
            'movement2-03.md', 'movement2-04.md', 'movement2-05.md', 
            'movement2-06.md', 'movement2-07.md', 'movement2-08.md', 
            'movement2-09.md', 'movement2-10.md', 'movement2-11.md', 
            'movement2-12.md', 'movement2-13.md', 
            'movement2-15.md', 'movement2-18.md', 'movement2-19.md', 
            'movement2-21.md', 

            'movement3-01.md', 'movement3-02.md', 'movement3-03.md', 
            'movement3-04.md', 'movement3-05.md', 'movement3-07.md', 
            'movement3-08.md', 'movement3-09.md', 'movement3-10.md', 
    ]

    baseDir = getComposerDir('handel')
    post = []
    if baseDir is None:
        return post
    paths = getPaths(extList)
    for fn in names:
        candidate = os.path.join(baseDir, 'hwv56', fn)
        if candidate not in paths: # it may not match extensions
            if not os.path.exists(candidate): # it does not exist at all 
                environLocal.printDebug(['corpus missing expected file path', 
                                    candidate])
        else:
            post.append(candidate)
    return post

#handelMessiah = getHandelMessiah()



def getMonteverdiMadrigals(extList='xml'):
    '''
    Return a list of the filenames of all Monteverdi madrigals.

    >>> from music21 import *
    >>> a = corpus.getMonteverdiMadrigals()
    >>> len(a) > 40
    True
    '''
    names = ['madrigal.3.1.mxl', 'madrigal.3.2.mxl', 'madrigal.3.3.mxl', 'madrigal.3.4.mxl', 'madrigal.3.5.mxl', 'madrigal.3.6.mxl', 'madrigal.3.7.mxl', 'madrigal.3.8.mxl', 'madrigal.3.9.mxl', 'madrigal.3.10.mxl', 'madrigal.3.11.mxl', 'madrigal.3.12.mxl', 'madrigal.3.13.mxl', 'madrigal.3.14.mxl', 'madrigal.3.15.mxl', 'madrigal.3.16.mxl', 'madrigal.3.17.mxl', 'madrigal.3.18.mxl', 'madrigal.3.19.mxl', 'madrigal.3.20.mxl', 

    'madrigal.4.1.mxl', 'madrigal.4.2.mxl', 'madrigal.4.3.mxl', 'madrigal.4.4.mxl', 'madrigal.4.5.mxl', 'madrigal.4.6.mxl', 'madrigal.4.7.mxl', 'madrigal.4.8.mxl', 'madrigal.4.9.mxl', 'madrigal.4.10.mxl', 'madrigal.4.11.mxl', 'madrigal.4.12.mxl', 'madrigal.4.13.mxl', 'madrigal.4.14.mxl', 'madrigal.4.15.mxl', 'madrigal.4.16.mxl', 'madrigal.4.17.mxl', 'madrigal.4.18.mxl', 'madrigal.4.19.mxl', 'madrigal.4.20.mxl',

    'madrigal.5.1.mxl', 'madrigal.5.2.mxl', 'madrigal.5.3.mxl', 'madrigal.5.5.mxl', 'madrigal.5.5.mxl', 'madrigal.5.6.mxl', 'madrigal.5.7.mxl', 'madrigal.5.8.mxl', 
    ]

    baseDir = getComposerDir('monteverdi')
    post = []
    if baseDir is None:
        return post
    paths = getPaths(extList)
    for fn in names:
        candidate = os.path.join(baseDir, fn)
        if candidate not in paths: # it may not match extensions
            if not os.path.exists(candidate): # it does not exist at all 
                environLocal.printDebug(['corpus missing expected file path', 
                                    candidate])
        else:
            post.append(candidate)
    return post

#monteverdiMadrigals = getMonteverdiMadrigals('xml')

def getBeethovenStringQuartets(extList=None):
    '''
    Return a list of all Beethoven String Quartet filenames.

    >>> from music21 import *
    >>> a = corpus.getBeethovenStringQuartets()
    >>> len(a) > 10
    True
    >>> a = corpus.getBeethovenStringQuartets('krn')
    >>> len(a) < 10 and len(a) > 0
    True
    >>> a = corpus.getBeethovenStringQuartets('xml')
    >>> len(a) > 400
    False
    '''

    candidates = []
    candidates += getWorkList(['beethoven', 'opus18no1'], extList=extList)
    candidates += getWorkList(['beethoven', 'opus18no3'], extList=extList)
    candidates += getWorkList(['beethoven', 'opus18no4'], extList=extList)
    candidates += getWorkList(['beethoven', 'opus18no5'], extList=extList)
    candidates += getWorkList(['beethoven', 'opus59no1'], extList=extList)
    candidates += getWorkList(['beethoven', 'opus59no2'], extList=extList)
    candidates += getWorkList(['beethoven', 'opus59no3'], extList=extList)
    candidates += getWorkList(['beethoven', 'opus74'], extList=extList)
    candidates += getWorkList(['beethoven', 'opus132'], extList=extList)
    candidates += getWorkList(['beethoven', 'opus133'], extList=extList)

    post = []
    for candidate in candidates:
        if not os.path.exists(candidate):
            environLocal.printDebug(['corpus missing expected file path', 
                                    candidate])
        else:
            post.append(candidate)
    return candidates

#beethovenStringQuartets = getBeethovenStringQuartets('xml')









#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testGetPaths(self):
        for known in ['haydn/opus74no2/movement4.mxl',         
            'beethoven/opus18no3.mxl',
            'beethoven/opus59no1/movement2.mxl',
            'mozart/k80/movement4.mxl',
            'schumann/opus41no1/movement5.mxl',
            ]:
            a = getWork(known)
            # make sure it is not an empty list
            self.assertNotEqual(len(a), 0)
            workSlashes = re.sub(r'\\', '/', a)
            self.assertEqual(workSlashes.endswith(known), True)


    def testBachKeys(self):
        from music21 import key
        for fp in getComposer('bach')[-5:]: # get the last 10
            s = parse(fp)
            # get keys from first part
            keyStream = s.parts[0].flat.getElementsByClass(key.KeySignature)
            keyObj = keyStream[0]
            #environLocal.printDebug([keyObj])


    def testEssenImport(self):

        # can get a single file just by file name        
        fp = getWork('altdeu10')
        self.assertTrue(fp.endswith('essenFolksong/altdeu10.abc') or fp.endswith(r'essenFolksong\altdeu10.abc'))
                        
        fpCollection = getComposer('essenFolksong')
        self.assertEqual(len(fpCollection), 31)

        fpCollection = getComposer('essenFolksong', ['abc'])
        self.assertEqual(len(fpCollection), 31)


    def testDesPrezImport(self):

        # can get a single file just by file name        
        fp = getWork('fortunaDunGranTempo')
        fp = re.sub(r'\\', '/', fp)
        self.assertEqual(fp.endswith('josquin/fortunaDunGranTempo.abc'), True)

        fpCollection = getComposer('josquin')
        self.assertEqual(len(fpCollection) >= 8, True)

        fpCollection = getComposer('josquin', ['abc'])
        self.assertEqual(len(fpCollection) >= 8, True)


    def testHandelImport(self):

        # can get a single file just by file name        
        fp = getWork('hwv56/movement1-01')# 
        fpCollection = getComposer('handel')
        self.assertEqual(len(fpCollection) >= 1, True)
        fpCollection = getComposer('handel', ['md'])
        self.assertEqual(len(fpCollection) >= 1, True)


    def testSearch(self):

        from music21 import corpus, key

        post = corpus.search('china', 'locale')
        self.assertEqual(len(post) > 1200, True)
        
        post = corpus.search('Sichuan', 'locale')
        self.assertEqual(len(post), 47)
        
        post = corpus.search('Taiwan', 'locale')
        self.assertEqual(len(post), 27)
        self.assertEqual(post[0][0][-8:], 'han2.abc') # file
        self.assertEqual(post[0][1], 209) # work number
        
        post = corpus.search('Sichuan|Taiwan', 'locale')
        self.assertEqual(len(post), 74)


        post = corpus.search('bach')
        self.assertEqual(len(post) > 120, True)

        post = corpus.search('haydn', 'composer')
        self.assertEqual(len(post), 0)
        post = corpus.search('haydn|beethoven', 'composer')
        self.assertEqual(len(post) >= 16, True)


        post = corpus.search('canon')
        self.assertEqual(len(post) >= 1, True)

        post = corpus.search('3/8', 'timeSignature')
        self.assertEqual(len(post) > 360, True)

        post = corpus.search('3/.', 'timeSignature')
        self.assertEqual(len(post) >= 2200 , True)


        ks = key.KeySignature(3, 'major')
        post = corpus.search(str(ks), 'keySignature')
        self.assertEqual(len(post) >= 32, True)

        post = corpus.search('sharps (.*), mode phry(.*)', 'keySignature')
        self.assertEqual(len(post) >= 9, True)

        # searching virtual entries
        post = corpus.search('coltrane', 'composer')
        self.assertEqual(len(post) > 0, True)
        # returns items in pairs: url and work number
        self.assertEqual(post[0][0], 'http://static.wikifonia.org/1164/musicxml.mxl')



    def testGetWorkList(self):
        self.assertEqual(len(getPaths('.md')) >= 38, True)

        self.assertEqual(len(getWorkList('bach/artOfFugue_bwv1080', 1, '.zip')), 1)

        self.assertEqual(len(getWorkList('handel/hwv56', (1,1), '.md')), 1)

        self.assertEqual(len(getWorkList('handel/hwv56', '1-01', '.md')), 1)

        self.assertEqual(len(getWorkList('bach/artOfFugue_bwv1080')), 21)

        self.assertEqual(len(getWorkList('bach/artOfFugue_bwv1080', 1)), 1)


        # there are two versions of this file        
        self.assertEqual(len(getWorkList('beethoven/opus18no1', 1)), 2)

        # if specify movement
        for bwv in ['bwv846', 'bwv847', 'bwv848', 'bwv849', 'bwv850', 'bwv851', 'bwv852', 'bwv853', 'bwv854', 'bwv855', 'bwv856', 'bwv857', 'bwv858', 'bwv859', 'bwv860', 'bwv861', 'bwv862', 'bwv863', 'bwv864', 'bwv865', 'bwv866', 'bwv867', 'bwv868', 'bwv869', 'bwv870', 'bwv871', 'bwv872', 'bwv873', 'bwv874', 'bwv875', 'bwv876', 'bwv877', 'bwv878', 'bwv879', 'bwv880', 'bwv881', 'bwv882', 'bwv883', 'bwv884', 'bwv885', 'bwv886', 'bwv887', 'bwv888', 'bwv889', 'bwv890', 'bwv891', 'bwv892', 'bwv893']:
            #print bwv
            self.assertEqual(len(getWorkList(bwv)), 2)
            self.assertEqual(len(getWorkList(bwv, 1)), 1)
            self.assertEqual(len(getWorkList(bwv, 2)), 1)


    def testWTCImport(self):
        from music21 import corpus
        s = corpus.parse('bach/bwv846', 1)
        self.assertEqual(s.metadata.title, 'WTC I: Prelude and Fugue in C major')
        self.assertEqual(s.metadata.movementNumber, '1')
        s = corpus.parse('bach/bwv846', 2)
        self.assertEqual(s.metadata.movementName, 'Fugue  I. ')
        self.assertEqual(s.metadata.movementNumber, '2')


        s = corpus.parse('bach/bwv862', 1)
        self.assertEqual(s.metadata.title, 'WTC I: Prelude and Fugue in A flat major')


        s = corpus.parse('bach/bwv888', 1)
        self.assertEqual(s.metadata.title, 'WTC II: Prelude and Fugue in A major')
        #s.show()


#     def testWorkReferences(self):
#         from music21 import corpus
#         s = corpus.getWorkReferences()
#         
#         # presenly 19 top level lists
#         self.assertEqual(len(s)>=19, True)
#         self.assertEqual(len(s[0].keys()), 4)


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [parse, getWork]


if __name__ == "__main__":
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

