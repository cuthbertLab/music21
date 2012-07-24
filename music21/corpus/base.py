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
The music21 corpus includes a collection of freely distributable 
music in MusicXML, Humdrum, and other representations. The corpus 
package is an interface for easily working with this data.

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
    2231

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
    Access files in additional directories supplied by the user and defined in environment settings. If additional paths are added on a per-session basis witht the :func:`~music21.corpus.addPath` function, these paths are also retuned with this method. 
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
    
    Similar to the :meth:`~music21.converter.parse` method of converter (which takes in
    a filepath on the local hard drive), this 
    method searches the corpus (including the virtual corpus)
    for a work fitting the workName description and 
    returns a :class:`music21.stream.Stream`.

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
    
    After parsing, the file path within the corpus is stored as `.corpusFilePath`
    
    >>> bachChorale.corpusFilepath
    'bach/bwv66.6.mxl'
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

