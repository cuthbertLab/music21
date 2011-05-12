#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         corpus/base.py
# Purpose:      Access to the corpus collection
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
The music21 corpus provides a collection of freely distributable music in MusicXML, Humdrum, and other representations. The corpus package provides an interface to this data.

To see complete listing of works in the music21 corpus, visit  :ref:`referenceCorpus`.
'''


import re
import os
import doctest, unittest

import music21
from music21 import common
from music21 import converter
from music21 import metadata
from music21 import musicxml
from music21.corpus import virtual

from music21 import environment
_MOD = "corpus.base.py"
environLocal = environment.Environment(_MOD)


# import corpus packages as python modules
from music21.corpus import airdsAirs

from music21.corpus import beethoven
from music21.corpus.beethoven import opus18no1
from music21.corpus.beethoven import opus59no1
from music21.corpus.beethoven import opus59no2
from music21.corpus.beethoven import opus59no3

from music21.corpus import essenFolksong
from music21.corpus import ciconia
from music21.corpus import josquin

from music21.corpus import handel
from music21.corpus.handel import hwv56  

from music21.corpus import haydn
from music21.corpus.haydn import opus1no0
from music21.corpus.haydn import opus1no1
from music21.corpus.haydn import opus1no2
from music21.corpus.haydn import opus1no3
from music21.corpus.haydn import opus1no4
from music21.corpus.haydn import opus1no6
from music21.corpus.haydn import opus9no2
from music21.corpus.haydn import opus9no3
from music21.corpus.haydn import opus17no1
from music21.corpus.haydn import opus17no2
from music21.corpus.haydn import opus17no3
from music21.corpus.haydn import opus17no5
from music21.corpus.haydn import opus17no6
from music21.corpus.haydn import opus20no1
from music21.corpus.haydn import opus20no2
from music21.corpus.haydn import opus20no3
from music21.corpus.haydn import opus20no4
from music21.corpus.haydn import opus20no5
from music21.corpus.haydn import opus20no6
from music21.corpus.haydn import opus33no1
from music21.corpus.haydn import opus33no2
from music21.corpus.haydn import opus33no3
from music21.corpus.haydn import opus33no4
from music21.corpus.haydn import opus33no5
from music21.corpus.haydn import opus33no6
from music21.corpus.haydn import opus42
from music21.corpus.haydn import opus50no1
from music21.corpus.haydn import opus50no2
from music21.corpus.haydn import opus50no3
from music21.corpus.haydn import opus50no4
from music21.corpus.haydn import opus50no5
from music21.corpus.haydn import opus50no6
from music21.corpus.haydn import opus54no1
from music21.corpus.haydn import opus54no2
from music21.corpus.haydn import opus54no3
from music21.corpus.haydn import opus55no1
from music21.corpus.haydn import opus55no2
from music21.corpus.haydn import opus55no3
from music21.corpus.haydn import opus64no1
from music21.corpus.haydn import opus64no2
from music21.corpus.haydn import opus64no3
from music21.corpus.haydn import opus64no4
from music21.corpus.haydn import opus64no5
from music21.corpus.haydn import opus64no6
from music21.corpus.haydn import opus71no1
from music21.corpus.haydn import opus71no2
from music21.corpus.haydn import opus71no3
from music21.corpus.haydn import opus74no1  
from music21.corpus.haydn import opus74no2 
from music21.corpus.haydn import opus74no3
from music21.corpus.haydn import opus76no1
from music21.corpus.haydn import opus76no2
from music21.corpus.haydn import opus76no3
from music21.corpus.haydn import opus76no4
from music21.corpus.haydn import opus76no5
from music21.corpus.haydn import opus76no6
from music21.corpus.haydn import opus77no1
from music21.corpus.haydn import opus77no2 

from music21.corpus import monteverdi

from music21.corpus import mozart
from music21.corpus.mozart import k80
from music21.corpus.mozart import k155
from music21.corpus.mozart import k156
from music21.corpus.mozart import k157
from music21.corpus.mozart import k158
from music21.corpus.mozart import k159
from music21.corpus.mozart import k160
from music21.corpus.mozart import k168
from music21.corpus.mozart import k169
from music21.corpus.mozart import k170
from music21.corpus.mozart import k171
from music21.corpus.mozart import k172
from music21.corpus.mozart import k173
from music21.corpus.mozart import k285
from music21.corpus.mozart import k298
from music21.corpus.mozart import k370
from music21.corpus.mozart import k387
from music21.corpus.mozart import k421
from music21.corpus.mozart import k428
from music21.corpus.mozart import k458
from music21.corpus.mozart import k464
from music21.corpus.mozart import k465
from music21.corpus.mozart import k499
from music21.corpus.mozart import k546
from music21.corpus.mozart import k575
from music21.corpus.mozart import k589
from music21.corpus.mozart import k590

from music21.corpus import schoenberg
from music21.corpus.schoenberg import opus19

from music21.corpus import schumann
from music21.corpus.schumann import opus41no1

from music21.corpus import luca

from music21.corpus import bach
from music21.corpus.bach import bwv1080
from music21.corpus.bach import bwv846

from music21.corpus.bach import bwv847
from music21.corpus.bach import bwv848
from music21.corpus.bach import bwv849
from music21.corpus.bach import bwv850
from music21.corpus.bach import bwv851
from music21.corpus.bach import bwv852
from music21.corpus.bach import bwv853
from music21.corpus.bach import bwv854
from music21.corpus.bach import bwv855
from music21.corpus.bach import bwv856
from music21.corpus.bach import bwv857
from music21.corpus.bach import bwv858
from music21.corpus.bach import bwv859
from music21.corpus.bach import bwv860
from music21.corpus.bach import bwv861
from music21.corpus.bach import bwv862
from music21.corpus.bach import bwv863
from music21.corpus.bach import bwv864
from music21.corpus.bach import bwv865
from music21.corpus.bach import bwv866
from music21.corpus.bach import bwv867
from music21.corpus.bach import bwv868
from music21.corpus.bach import bwv869
from music21.corpus.bach import bwv870
from music21.corpus.bach import bwv871
from music21.corpus.bach import bwv872
from music21.corpus.bach import bwv873
from music21.corpus.bach import bwv874
from music21.corpus.bach import bwv875
from music21.corpus.bach import bwv876
from music21.corpus.bach import bwv877
from music21.corpus.bach import bwv878
from music21.corpus.bach import bwv879
from music21.corpus.bach import bwv880
from music21.corpus.bach import bwv881
from music21.corpus.bach import bwv882
from music21.corpus.bach import bwv883
from music21.corpus.bach import bwv884
from music21.corpus.bach import bwv885
from music21.corpus.bach import bwv886
from music21.corpus.bach import bwv887
from music21.corpus.bach import bwv888
from music21.corpus.bach import bwv889
from music21.corpus.bach import bwv890
from music21.corpus.bach import bwv891
from music21.corpus.bach import bwv892
from music21.corpus.bach import bwv893


MODULES = [
            airdsAirs,
            
            beethoven, 
            opus18no1,
            opus59no1,
            opus59no2,
            opus59no3,

            ciconia,
            josquin,
            essenFolksong,

            handel,
            hwv56,

            haydn,
            opus1no0,
            opus1no1,
            opus1no2,
            opus1no3,
            opus1no4,
            opus1no6,
            opus9no2,
            opus9no3,
            opus17no1,
            opus17no2,
            opus17no3,
            opus17no5,
            opus17no6,
            opus20no1,
            opus20no2,
            opus20no3,
            opus20no4,
            opus20no5,
            opus20no6,
            opus33no1,
            opus33no2,
            opus33no3,
            opus33no4,
            opus33no5,
            opus33no6,
            opus42,
            opus50no1,
            opus50no2,
            opus50no3,
            opus50no4,
            opus50no5,
            opus50no6,
            opus54no1,
            opus54no2,
            opus54no2,
            opus55no1,
            opus55no2,
            opus55no3,
            opus64no1,
            opus64no2,
            opus64no3,
            opus64no4,
            opus64no5,
            opus64no6,
            opus71no1,
            opus71no2,
            opus71no3,
            opus74no1,
            opus74no2,
            opus74no3,
            opus76no1,
            opus76no2,
            opus76no3,
            opus76no4,
            opus76no5,
            opus76no6,
            opus77no1,
            opus77no2,

            monteverdi,

            mozart,
            k80,
            k155,
            k156,
            k157,
            k158,
            k159,
            k160,
            k168,
            k169,
            k170,
            k171,
            k172,
            k173,
            k285,
            k298,
            k370,
            k387,
            k421,
            k428,
            k458,
            k464,
            k465,
            k499,
            k546,
            k575,
            k589,
            k590,
            
            schoenberg,
            opus19,

            schumann,
            opus41no1,

            luca,

            bach,
            bwv1080,
            bwv846,
            bwv847,
            bwv848,
            bwv849,
            bwv850,
            bwv851,
            bwv852,
            bwv853,
            bwv854,
            bwv855,
            bwv856,
            bwv857,
            bwv858,
            bwv859,
            bwv860,
            bwv861,
            bwv862,
            bwv863,
            bwv864,
            bwv865,
            bwv866,
            bwv867,
            bwv868,
            bwv869,
            bwv870,
            bwv871,
            bwv872,
            bwv873,
            bwv874,
            bwv875,
            bwv876,
            bwv877,
            bwv878,
            bwv879,
            bwv880,
            bwv881,
            bwv882,
            bwv883,
            bwv884,
            bwv885,
            bwv886,
            bwv887,
            bwv888,
            bwv889,
            bwv890,
            bwv891,
            bwv892,
            bwv893,


    ]


# a list of metadataCache's can reside in this module-level storage; this 
# data is loaded on demand. 
_METADATA_BUNDLES = {'core':None, 'virtual':None, 'local':None}

_ALL_EXTENSIONS = (common.findInputExtension('abc') +
                   common.findInputExtension('lily') +
                   common.findInputExtension('musicxml') +
                   common.findInputExtension('musedata') +
                   common.findInputExtension('humdrum') +
                   common.findInputExtension('romantext'))

# store all composers in the corpus (not virtual) 
# as two element tuples of path name, full name
COMPOSERS = [
    ('bach', 'Johann Sebastian Bach'),
    ('beethoven', 'Ludwig van Beethoven'),
    ('ciconia', 'Johannes Ciconia'),
    ('haydn', 'Joseph Haydn'),
    ('handel', 'George Frideric Handel'),
    ('josquin', 'Josquin des Prez'),
    ('luca', 'D. Luca'),
    ('monteverdi', "Claudio Monteverdi"),
    ('mozart', 'Wolfgang Amadeus Mozart'),
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
def getPaths(extList=None, expandExtensions=True):    
    '''Get all paths in the corpus that match a known extension, or an extenion
    provided by an argument.

    If `expandExtensions` is True, a format for an extension, and related extensions, will replaced by all known input extensions. This is convenient when an input format might match for multiple extensions.

    >>> a = getPaths()
    >>> len(a) > 30
    True

    >>> a = getPaths('krn')
    >>> len(a) >= 4
    True

    >>> a = getPaths('abc')
    >>> len(a) >= 10
    True

    '''
    if not common.isListLike(extList):
        extList = [extList]
    if extList == [None]:
        extList = _ALL_EXTENSIONS
    elif expandExtensions:
        extMod = []
        for e in extList:
            extMod += common.findInputExtension(e)
        extList = extMod
        
    #environLocal.printDebug(['getting paths with extensions:', extList])
    paths = []    
    for moduleName in MODULES:
        if not hasattr(moduleName, '__path__'):
            # when importing a package name (a directory) the moduleName        
            # may be a list of all paths contained within the package
            # this seems to be dependent on the context of the call:
            # from the command line is different than from the interpreter
            dirListing = moduleName
        else:
            # returns a list with one or more paths
            # the first is the path to the directory that contains xml files
            dir = moduleName.__path__[0] 
            dirListing = [os.path.join(dir, x) for x in os.listdir(dir)]

        for fp in dirListing:
            if fp in paths:
                continue
            match = False
            for ext in extList:
                if fp.endswith(ext):
                    match = True
                    break 
            if match:
                if fp not in paths:
                    paths.append(fp)    
    return paths

def getVirtualPaths(extList=None):
    '''Get all paths in the virtual corpus that match a known extension. An extension of None will return all known extensions.
   
    >>> len(getVirtualPaths()) > 6
    True
    '''
    if not common.isListLike(extList):
        extList = [extList]

    if extList == [None]:
        extList = _ALL_EXTENSIONS
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


def getLocalPaths(extList=None):
    '''
    Access files in additional directories supplied by the user and defined in environement settings. 
    '''
    return []



#-------------------------------------------------------------------------------
def _updateMetadataBundle():

    for d, f in (('core', getPaths), ('virtual', getVirtualPaths)):
        if _METADATA_BUNDLES[d] == None:
            _METADATA_BUNDLES[d] = metadata.MetadataBundle(d)
            _METADATA_BUNDLES[d].read()
            # must update access paths for the files found on this system
            _METADATA_BUNDLES[d].updateAccessPaths(f())

#     if 'local' in domain:
#         pass


def search(query, field=None, domain=['core', 'virtual'], extList=None):
    '''Search all stored metadata and return a list of file paths; to return a list of parsed Streams, use searchParse(). 

    The `domain` parameter can be used to specify one of three corpora: core (included with music21), virtual (defined in music21 but hosted online), and local (hosted on the user's system). 

    This method uses stored metadata and thus, on first usage, will incur a performance penalty during metadata loading.
    '''
    post = []
    _updateMetadataBundle()
    if 'core' in domain:
        post += _METADATA_BUNDLES['core'].search(query, field, extList)
    if 'virtual' in domain:
        post += _METADATA_BUNDLES['virtual'].search(query, field, extList)
    return post



#-------------------------------------------------------------------------------
def getComposer(composerName, extList=None):
    '''Return all components of the corpus that match a composer's or a collection's name. An `extList`, if provided, defines which extensions are returned. An `extList` of None returns all extensions. 

    >>> a = getComposer('beethoven')
    >>> len(a) > 10
    True
    >>> a = getComposer('mozart')
    >>> len(a) > 10
    True
    >>> a = getComposer('bach', 'krn')
    >>> len(a) < 10
    True
    >>> a = getComposer('bach', 'xml')
    >>> len(a) > 10
    True
    '''
    paths = getPaths(extList)
    post = []
    for path in paths:
        if composerName.lower() in path.lower():
            post.append(path)
    post.sort()
    return post

def getComposerDir(composerName):
    '''Given the name of a composer, get the path to the top-level directory
    of that composer 

    >>> import os
    >>> a = getComposerDir('beethoven')
    >>> a.endswith(os.path.join('corpus', os.sep, 'beethoven'))
    True
    >>> a = getComposerDir('bach')
    >>> a.endswith(os.path.join('corpus', os.sep, 'bach'))
    True
    >>> a = getComposerDir('mozart')
    >>> a.endswith(os.path.join('corpus', os.sep, 'mozart'))
    True
    >>> a = getComposerDir('luca')
    >>> a.endswith(os.path.join('corpus', os.sep, 'luca'))
    True
    '''
    match = None
    for moduleName in MODULES:          
        if common.isListLike(moduleName):
            candidate = moduleName[0]         
        else:
            candidate = str(moduleName)
        if composerName.lower() not in candidate.lower():
            continue
        # might also slook at .__file__
        if not hasattr(moduleName, '__path__'): # its a list of files
            dirCandidate = moduleName[0]
            while True:
                dir = os.path.dirname(dirCandidate)
                if dir.lower().endswith(composerName.lower()):
                    break
                else:
                    dirCandidate = dir
                if dirCandidate.count(os.sep) < 2: # done enough checks
                    break
        else:
            dir = moduleName.__path__[0] 

        # last check
        if dir.lower().endswith(composerName.lower()):
            match = dir     
            break
    return match


#-------------------------------------------------------------------------------
def getWorkList(workName, movementNumber=None, extList=None):
    '''Search the corpus and return a list of works, always in a list. If no matches are found, an empty list is returned.

    >>> len(getWorkList('beethoven/opus18no1'))
    8
    >>> len(getWorkList('beethoven/opus18no1', 1))
    2 
    >>> len(getWorkList('beethoven/opus18no1', 1, '.krn'))
    1
    >>> len(getWorkList('beethoven/opus18no1', 1, '.xml'))
    1
    >>> len(getWorkList('beethoven/opus18no1', 0, '.xml'))
    0
    >>> len(getWorkList('handel/hwv56', '1-01', '.md'))
    1
    >>> len(getWorkList('handel/hwv56', (1,1), '.md'))
    1

    >>> len(getWorkList('bach/bwv1080', 1, '.md'))
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

    # find all matches for the work name
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

    >>> getVirtualWorkList('bach/bwv1007/prelude')
    ['http://kern.ccarh.org/cgi-bin/ksdata?l=cc/bach/cello&file=bwv1007-01.krn&f=xml']

    >>> getVirtualWorkList('junk')
    []
    '''
    if not common.isListLike(extList):
        extList = [extList]

    for obj in VIRTUAL:
        if obj.corpusPath != None and workName.lower() in obj.corpusPath.lower():
            return obj.getUrlByExt(extList)
    return []


#-------------------------------------------------------------------------------
# high level utilities that mix corpus and virtual corpus
# this will need to be re-worked after metadata caching is stored

def getWorkReferences(sort=True):
    '''Return a data dictionary for all works in the corpus and (optionally) the virtual corpus. Returns a list of reference dictionaries, each each dictionary for a each composer. A 'works' dictionary for each composer provides references to dictionaries for all associated works. 

    >>> post = getWorkReferences()
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
            junk, fileStub = path.split(dirComposer)
            if fileStub.startswith(os.sep):
                fileStub = fileStub[len(os.sep):]
            # break into file components
            fileComponents = fileStub.split(os.sep)
            # the first is either a directory for containing components
            # or a top-level name
            format, ext = common.findFormatExtFile(fileComponents[0])
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
            if title == None:
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

    >>> import os
    >>> a = getWork('opus74no2', 4)
    >>> a.endswith(os.path.sep.join(['haydn', 'opus74no2', 'movement4.xml']))
    True

    >>> a = getWork(['haydn', 'opus74no2', 'movement4.xml'])
    >>> a.endswith(os.path.sep.join(['haydn', 'opus74no2', 'movement4.xml']))
    True

    '''
    if not common.isListLike(extList):
        extList = [extList]

    post = getWorkList(workName, movementNumber, extList)
    if len(post) == 0:
        post = getVirtualWorkList(workName, movementNumber, extList)

    if len(post) == 1:
        return post[0]
    elif len(post) == 0:
        raise CorpusException("Could not find a file/url that met this criteria")
    else: # return a list
        return post



def parse(workName, movementNumber=None, number=None, 
    extList=None, forceSource=False):
    '''Search the corpus, then the virtual corpus, for a work, and return a parsed :class:`music21.stream.Stream`.

    If `movementNumber` is defined, and a movement is included in the corpus, that movement will be returned. 

    If `number` is defined, and the work is a collection with multiple components, that work number will be returned. 

    If `forceSource` is True, the original file will always be loaded and pickled files, if available, will be ignored.

    >>> aStream = parse('opus74no1/movement3')
    '''
    if not common.isListLike(extList):
        extList = [extList]

    post = getWorkList(workName, movementNumber, extList)
    #environLocal.printDebug(['result of getWorkList()', post])
    if len(post) == 0:
        post = getVirtualWorkList(workName, movementNumber, extList)    

    if len(post) == 1:
        fp = post[0]
    elif len(post) == 0:
        raise CorpusException("Could not find a work that met this criteria")
    else: # greater than zero:
        fp = post[0] # get first
      
    return converter.parse(fp, forceSource=forceSource, number=number)


def parseWork(*arguments, **keywords):
    '''This function exists for backwards compatibility. All calls should use :func:`~music21.corpus.parse` instead.
    '''
    import warnings
    #raise DeprecationWarning('the corpus.parseWork() function is depcreciated: use corpus.parse()')
    warnings.warn('the corpus.parseWork() function is depcreciated: use corpus.parse()', DeprecationWarning)
    return parse(*arguments, **keywords)


#-------------------------------------------------------------------------------
# all paths

paths = getPaths()

#-------------------------------------------------------------------------------
# libraries


beethoven = getComposer('beethoven')
josquin = getComposer('josquin')
mozart = getComposer('mozart')
monteverdi = getComposer('monteverdi')
haydn = getComposer('haydn')
handel = getComposer('handel')
bach = getComposer('bach')

# additional libraries to define

def getBachChorales(extList='xml'):
    '''Return the file name of all Bach chorales.
    
    By default, only Bach Chorales in xml format are returned, because the quality of 
    the encoding and our parsing of those is superior.

    >>> a = getBachChorales()
    >>> len(a) > 400
    True
    >>> a = getBachChorales('krn')
    >>> len(a) > 10
    False
    >>> a = getBachChorales('xml')
    >>> len(a) > 400
    True
    '''
    names = ['bwv1.6.xml', 'bwv10.7.xml', 'bwv101.7.xml', 'bwv102.7.xml', 'bwv103.6.xml', 'bwv104.6.xml', 'bwv108.6.xml', 'bwv11.6.xml', 'bwv110.7.xml', 'bwv111.6.xml', 'bwv112.5-sc.xml', 'bwv112.5.xml', 'bwv113.8.xml', 'bwv114.7.xml', 'bwv115.6.xml', 'bwv116.6.xml', 'bwv117.4.xml', 'bwv119.9.xml', 'bwv12.7.xml', 'bwv120.6.xml', 'bwv120.8-a.xml', 'bwv121.6.xml', 'bwv122.6.xml', 'bwv123.6.xml', 'bwv124.6.xml', 'bwv125.6.xml', 'bwv126.6.xml', 'bwv127.5.xml', 'bwv128.5.xml', 'bwv13.6.xml', 'bwv130.6.xml', 'bwv133.6.xml', 'bwv135.6.xml', 'bwv136.6.xml', 'bwv137.5.xml', 'bwv139.6.xml', 'bwv14.5.xml', 'bwv140.7.xml', 'bwv144.3.xml', 'bwv144.6.xml', 'bwv145-a.xml', 'bwv145.5.xml', 'bwv146.8.xml', 'bwv148.6.xml', 'bwv149.7.xml', 'bwv151.5.xml', 'bwv153.1.xml', 'bwv153.5.xml', 'bwv153.9.xml', 'bwv154.3.xml', 'bwv154.8.xml', 'bwv155.5.xml', 'bwv156.6.xml', 'bwv157.5.xml', 'bwv158.4.xml', 'bwv159.5.xml', 'bwv16.6.xml', 'bwv161.6.xml', 'bwv162.6-lpz.xml', 'bwv164.6.xml', 'bwv165.6.xml', 'bwv166.6.xml', 'bwv168.6.xml', 'bwv169.7.xml', 'bwv17.7.xml', 'bwv171.6.xml', 'bwv172.6.xml', 'bwv174.5.xml', 'bwv175.7.xml', 'bwv176.6.xml', 'bwv177.5.xml', 'bwv178.7.xml', 'bwv179.6.xml', 'bwv18.5-lz.xml', 'bwv18.5-w.xml', 'bwv180.7.xml', 'bwv183.5.xml', 'bwv184.5.xml', 'bwv185.6.xml', 'bwv187.7.xml', 'bwv188.6.xml', 'bwv19.7.xml', 'bwv190.7-inst.xml', 'bwv190.7.xml', 'bwv194.12.xml', 'bwv194.6.xml', 'bwv195.6.xml', 'bwv197.10.xml', 'bwv197.5.xml', 'bwv197.7-a.xml', 'bwv2.6.xml', 'bwv20.11.xml', 'bwv20.7.xml', 'bwv226.2.xml', 'bwv227.1.xml', 'bwv227.11.xml', 'bwv227.3.xml', 'bwv227.7.xml', 'bwv229.2.xml', 'bwv244.10.xml', 'bwv244.15.xml', 'bwv244.17.xml', 'bwv244.25.xml', 'bwv244.29-a.xml', 'bwv244.3.xml', 'bwv244.32.xml', 'bwv244.37.xml', 'bwv244.40.xml', 'bwv244.44.xml', 'bwv244.46.xml', 'bwv244.54.xml', 'bwv244.62.xml', 'bwv245.11.xml', 'bwv245.14.xml', 'bwv245.15.xml', 'bwv245.17.xml', 'bwv245.22.xml', 'bwv245.26.xml', 'bwv245.28.xml', 'bwv245.3.xml', 'bwv245.37.xml', 'bwv245.40.xml', 'bwv245.5.xml', 'bwv248.12-2.xml', 'bwv248.17.xml', 'bwv248.23-2.xml', 'bwv248.23-s.xml', 'bwv248.28.xml', 'bwv248.33-3.xml', 'bwv248.35-3.xml', 'bwv248.35-3c.xml', 'bwv248.42-4.xml', 'bwv248.42-s.xml', 'bwv248.46-5.xml', 'bwv248.5.xml', 'bwv248.53-5.xml', 'bwv248.59-6.xml', 'bwv248.64-6.xml', 'bwv248.64-s.xml', 'bwv248.9-1.xml', 'bwv248.9-s.xml', 'bwv25.6.xml', 'bwv250.xml', 'bwv251.xml', 'bwv252.xml', 'bwv253.xml', 'bwv254.xml', 'bwv255.xml', 'bwv256.xml', 'bwv257.xml', 'bwv258.xml', 'bwv259.xml', 'bwv26.6.xml', 'bwv260.xml', 'bwv261.xml', 'bwv262.xml', 'bwv263.xml', 'bwv264.xml', 'bwv265.xml', 'bwv266.xml', 'bwv267.xml', 'bwv268.xml', 'bwv269.xml', 'bwv27.6.xml', 'bwv270.xml', 'bwv271.xml', 'bwv272.xml', 'bwv273.xml', 'bwv276.xml', 'bwv277.krn', 'bwv277.xml', 'bwv278.xml', 'bwv279.xml', 'bwv28.6.xml', 'bwv280.xml', 'bwv281.krn', 'bwv281.xml', 'bwv282.xml', 'bwv283.xml', 'bwv284.xml', 'bwv285.xml', 'bwv286.xml', 'bwv287.xml', 'bwv288.xml', 'bwv289.xml', 'bwv29.8.xml', 'bwv290.xml', 'bwv291.xml', 'bwv292.xml', 'bwv293.xml', 'bwv294.xml', 'bwv295.xml', 'bwv296.xml', 'bwv297.xml', 'bwv298.xml', 'bwv299.xml', 'bwv3.6.xml', 'bwv30.6.xml', 'bwv300.xml', 'bwv301.xml', 'bwv302.xml', 'bwv303.xml', 'bwv304.xml', 'bwv305.xml', 'bwv306.xml', 'bwv307.xml', 'bwv308.xml', 'bwv309.xml', 'bwv31.9.xml', 'bwv310.xml', 'bwv311.xml', 'bwv312.xml', 'bwv313.xml', 'bwv314.xml', 'bwv315.xml', 'bwv316.xml', 'bwv317.xml', 'bwv318.xml', 'bwv319.xml', 'bwv32.6.xml', 'bwv320.xml', 'bwv321.xml', 'bwv322.xml', 'bwv323.xml', 'bwv324.xml', 'bwv325.xml', 'bwv326.xml', 'bwv327.xml', 'bwv328.xml', 'bwv329.xml', 'bwv33.6.xml', 'bwv330.xml', 'bwv331.xml', 'bwv332.xml', 'bwv333.xml', 'bwv334.xml', 'bwv335.xml', 'bwv336.xml', 'bwv337.xml', 'bwv338.xml', 'bwv339.xml', 'bwv340.xml', 'bwv341.xml', 'bwv342.xml', 'bwv343.xml', 'bwv344.xml', 'bwv345.xml', 'bwv346.xml', 'bwv347.xml', 'bwv348.xml', 'bwv349.xml', 'bwv350.xml', 'bwv351.xml', 'bwv352.xml', 'bwv353.xml', 'bwv354.xml', 'bwv355.xml', 'bwv356.xml', 'bwv357.xml', 'bwv358.xml', 'bwv359.xml', 'bwv36.4-2.xml', 'bwv36.8-2.xml', 'bwv360.xml', 'bwv361.xml', 'bwv362.xml', 'bwv363.xml', 'bwv364.xml', 'bwv365.xml', 'bwv366.krn', 'bwv366.xml', 'bwv367.xml', 'bwv368.xml', 'bwv369.xml', 'bwv37.6.xml', 'bwv370.xml', 'bwv371.xml', 'bwv372.xml', 'bwv373.xml', 'bwv374.xml', 'bwv375.xml', 'bwv376.xml', 'bwv377.xml', 'bwv378.xml', 'bwv379.xml', 'bwv38.6.xml', 'bwv380.xml', 'bwv381.xml', 'bwv382.xml', 'bwv383.xml', 'bwv384.xml', 'bwv385.xml', 'bwv386.xml', 'bwv387.xml', 'bwv388.xml', 'bwv389.xml', 'bwv39.7.xml', 'bwv390.xml', 'bwv391.xml', 'bwv392.xml', 'bwv393.xml', 'bwv394.xml', 'bwv395.xml', 'bwv396.xml', 'bwv397.xml', 'bwv398.xml', 'bwv399.xml', 'bwv4.8.xml', 'bwv40.3.xml', 'bwv40.6.xml', 'bwv40.8.xml', 'bwv400.xml', 'bwv401.xml', 'bwv402.xml', 'bwv403.xml', 'bwv404.xml', 'bwv405.xml', 'bwv406.xml', 'bwv407.xml', 'bwv408.xml', 'bwv41.6.xml', 'bwv410.xml', 'bwv411.xml', 'bwv412.xml', 'bwv413.xml', 'bwv414.xml', 'bwv415.xml', 'bwv416.xml', 'bwv417.xml', 'bwv418.xml', 'bwv419.xml', 'bwv42.7.xml', 'bwv420.xml', 'bwv421.xml', 'bwv422.xml', 'bwv423.xml', 'bwv424.xml', 'bwv425.xml', 'bwv426.xml', 'bwv427.xml', 'bwv428.xml', 'bwv429.xml', 'bwv43.11.xml', 'bwv430.xml', 'bwv431.xml', 'bwv432.xml', 'bwv433.xml', 'bwv434.xml', 'bwv435.xml', 'bwv436.xml', 'bwv437.xml', 'bwv438.xml', 'bwv44.7.xml', 'bwv45.7.xml', 'bwv47.5.xml', 'bwv48.3.xml', 'bwv48.7.xml', 'bwv5.7.xml', 'bwv52.6.xml', 'bwv55.5.xml', 'bwv56.5.xml', 'bwv57.8.xml', 'bwv59.3.xml', 'bwv6.6.xml', 'bwv60.5.xml', 'bwv64.2.xml', 'bwv64.4.xml', 'bwv64.8.xml', 'bwv65.2.xml', 'bwv65.7.xml', 'bwv66.6.xml', 'bwv67.4.xml', 'bwv67.7.xml', 'bwv69.6-a.xml', 'bwv69.6.xml', 'bwv7.7.xml', 'bwv70.11.xml', 'bwv70.7.xml', 'bwv72.6.xml', 'bwv73.5.xml', 'bwv74.8.xml', 'bwv77.6.xml', 'bwv78.7.xml', 'bwv79.3.xml', 'bwv79.6.xml', 'bwv8.6.xml', 'bwv80.8.xml', 'bwv81.7.xml', 'bwv83.5.xml', 'bwv84.5.xml', 'bwv85.6.xml', 'bwv86.6.xml', 'bwv87.7.xml', 'bwv88.7.xml', 'bwv89.6.xml', 'bwv9.7.xml', 'bwv90.5.xml', 'bwv91.6.xml', 'bwv92.9.xml', 'bwv93.7.xml', 'bwv94.8.xml', 'bwv95.7.xml', 'bwv96.6.xml', 'bwv97.9.xml', 'bwv99.6.xml']

    baseDir = getComposerDir('bach')
    post = []
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

bachChorales = getBachChorales('xml')


def getHandelMessiah(extList='md'):
    '''Return the file name of all of handel's messiah.

    >>> from music21 import *
    >>> a = getHandelMessiah()
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

handelMessiah = getHandelMessiah()



def getMonteverdiMadrigals(extList='xml'):
    '''Return the file name of all Monteverdi madrigals.

    >>> from music21 import *
    >>> a = getMonteverdiMadrigals()
    >>> len(a) > 40
    True
    '''
    names = ['madrigal.3.1.xml', 'madrigal.3.2.xml', 'madrigal.3.3.xml', 'madrigal.3.4.xml', 'madrigal.3.5.xml', 'madrigal.3.6.xml', 'madrigal.3.7.xml', 'madrigal.3.8.xml', 'madrigal.3.9.xml', 'madrigal.3.10.xml', 'madrigal.3.11.xml', 'madrigal.3.12.xml', 'madrigal.3.13.xml', 'madrigal.3.14.xml', 'madrigal.3.15.xml', 'madrigal.3.16.xml', 'madrigal.3.17.xml', 'madrigal.3.18.xml', 'madrigal.3.19.xml', 'madrigal.3.20.xml', 

    'madrigal.4.1.xml', 'madrigal.4.2.xml', 'madrigal.4.3.xml', 'madrigal.4.4.xml', 'madrigal.4.5.xml', 'madrigal.4.6.xml', 'madrigal.4.7.xml', 'madrigal.4.8.xml', 'madrigal.4.9.xml', 'madrigal.4.10.xml', 'madrigal.4.11.xml', 'madrigal.4.12.xml', 'madrigal.4.13.xml', 'madrigal.4.14.xml', 'madrigal.4.15.xml', 'madrigal.4.16.xml', 'madrigal.4.17.xml', 'madrigal.4.18.xml', 'madrigal.4.19.xml', 'madrigal.4.20.xml',

    'madrigal.5.1.xml', 'madrigal.5.2.xml', 'madrigal.5.3.xml', 'madrigal.5.5.xml', 'madrigal.5.5.xml', 'madrigal.5.6.xml', 'madrigal.5.7.xml', 'madrigal.5.8.xml', 
    ]

    baseDir = getComposerDir('monteverdi')
    post = []
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

monteverdiMadrigals = getMonteverdiMadrigals('xml')

def getBeethovenStringQuartets(extList=None):
    '''Return all Beethoven String Quartets.

    >>> a = getBeethovenStringQuartets()
    >>> len(a) > 10
    True
    >>> a = getBeethovenStringQuartets('krn')
    >>> len(a) < 10 and len(a) > 0
    True
    >>> a = getBeethovenStringQuartets('xml')
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

beethovenStringQuartets = getBeethovenStringQuartets('xml')









#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testGetPaths(self):
        for known in ['haydn/opus74no2/movement4.xml',         
            'beethoven/opus18no3.xml',
            'beethoven/opus59no1/movement2.xml',
            'mozart/k80/movement4.xml',
            'schumann/opus41no1/movement5.xml',
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
            environLocal.printDebug([keyObj])


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
        self.assertEqual(post[0][1], '209') # work number
        
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

        self.assertEqual(len(getWorkList('bach/bwv1080', 1, '.zip')), 1)

        self.assertEqual(len(getWorkList('handel/hwv56', (1,1), '.md')), 1)

        self.assertEqual(len(getWorkList('handel/hwv56', '1-01', '.md')), 1)

        self.assertEqual(len(getWorkList('bach/bwv1080')), 21)

        self.assertEqual(len(getWorkList('bach/bwv1080', 1)), 1)


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



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [parse, parseWork, getWork]


if __name__ == "__main__":
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

