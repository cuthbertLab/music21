#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         corpus/base.py
# Purpose:      Access to the corpus collection
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
The music21 corpus provides a collection of freely distributable music in MusicXML, Humdrum, and other representations. The corpus package provides an interface to this data.
'''


import re
import os
import doctest, unittest

import music21
from music21 import common
from music21 import converter
from music21.corpus import virtual

from music21 import environment
_MOD = "corpus.base.py"
environLocal = environment.Environment(_MOD)



from music21.corpus import beethoven
from music21.corpus.beethoven import opus18no1
from music21.corpus.beethoven import opus59no1
from music21.corpus.beethoven import opus59no2
from music21.corpus.beethoven import opus59no3

from music21.corpus import ciconia

from music21.corpus import haydn
from music21.corpus.haydn import opus74no1  
from music21.corpus.haydn import opus74no2  

from music21.corpus import mozart
from music21.corpus.mozart import k80
from music21.corpus.mozart import k155
from music21.corpus.mozart import k156
from music21.corpus.mozart import k458

from music21.corpus import schoenberg
from music21.corpus.schoenberg import opus19

from music21.corpus import schumann
from music21.corpus.schumann import opus41no1

from music21.corpus import luca
from music21.corpus import bach


MODULES = [
            beethoven, 
            opus18no1,
            opus59no1,
            opus59no2,
            opus59no3,

            ciconia,

            haydn,
            opus74no1,
            opus74no2,

            mozart,
            k80,
            k155,
            k156,
            k458,
            
            schoenberg,
            opus19,

            schumann,
            opus41no1,

            luca,
            bach,
    ]


# instantiate an instance of each virtual work object in a module
# level constant
VIRTUAL = []
for name in dir(virtual): # look over virtual module
    className = getattr(virtual, name)
    if callable(className):
        obj = className()
        if isinstance(obj, virtual.VirtualWork):
            VIRTUAL.append(obj)



#-------------------------------------------------------------------------------
class CorpusException(Exception):
    pass


#-------------------------------------------------------------------------------
def getPaths(extList=None):    
    '''Get all paths in the corpus that match a known extension, or an extenion
    provided by an argument.

    >>> a = getPaths()
    >>> len(a) > 30
    True

    >>> a = getPaths('krn')
    >>> len(a) >= 4
    True
    '''
    if not common.isListLike(extList):
        extList = [extList]

    if extList == [None]:
        extList = (common.findInputExtension('lily') +
                   common.findInputExtension('musicxml') +
                   common.findInputExtension('humdrum'))

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
        extList = (common.findInputExtension('lily') +
                   common.findInputExtension('musicxml') +
                   common.findInputExtension('humdrum'))
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

def getComposer(composerName, extList=None):
    '''Return all components of the corpus that match a composer's name. An extList, if provided, defines which extensions are returned. An extList of None returns all extensions. 

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
    '''
    if not common.isListLike(extList):
        extList = [extList]

    paths = getPaths(extList)
    post = []

    # permit workName to be a list of paths/branches
    if common.isListLike(workName):
        workName = os.path.sep.join(workName)

    workSlashes = workName.replace('/', os.path.sep)

    for path in paths:
        if workName.lower() in path.lower():
            post.append(path)
        elif workSlashes.lower() in path.lower():
            post.append(path)

    post.sort()
    postMvt = []
    if movementNumber is not None and len(post) > 0:
        movementStrList = ['movement%s' % movementNumber]
        for fp in post:
            for movementStr in movementStrList:
                if movementStr.lower() in fp.lower():
                    postMvt.append(fp)
        if len(postMvt) == 0:
            pass # return an empty list
#             raise CorpusException(
#                 "Cannot get movement number " + str(movementNumber) + 
#                 " either because " + workName + " does not have that many movements or because the corpus is not organized by movement")
    else:
        postMvt = post

    if len(postMvt) == 0:
        return []
    else:
        return postMvt

def getVirtualWorkList(workName, movementNumber=None, extList=None):
    '''Given as work name, search all virtual works and see if there is a match. Return a list of one or more work URLs.

    >>> getVirtualWorkList('bach/bwv1007/prelude')
    ['http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/bach/cello&file=bwv1007-01.krn&f=xml']

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
def getWork(workName, movementNumber=None, extList=None):
    '''Search the corpus and return either a list of file paths or, if there is a single match, a single file path. If no matches are found an Exception is raised. 

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


def parseWork(workName, movementNumber=None, extList=None, forceSource=False):
    '''Return a parsed stream from a converter by providing only a work name.

    If forceSource is True, the original file will always be loaded and pickled
    files, if available, will be ignored.

    >>> aStream = parseWork('opus74no1/movement3')
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
      
    return converter.parse(fp, forceSource=forceSource)



#-------------------------------------------------------------------------------
# all paths

paths = getPaths()

#-------------------------------------------------------------------------------
# libraries

beethoven = getComposer('beethoven')
mozart = getComposer('mozart')
haydn = getComposer('haydn')
bach = getComposer('bach')

# additional libraries to define

def getBachChorales(extList=None):
    '''
    >>> a = getBachChorales()
    >>> len(a) > 10
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


def getBeethovenStringQuartets(extList=None):
    '''
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

    # TODO: this is a problem: getWork sometimes returns a list, 
    # sometimes a single value. this should always return a list

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
            s = parseWork(fp)
            # get keys from first part
            keyStream = s[0].flat.getElementsByClass(key.KeySignature)
            keyObj = keyStream[0]
            environLocal.printDebug([keyObj])





#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [parseWork, getWork]


if __name__ == "__main__":
    #qj = parseWork('ciconia/quod_jactatur')
    music21.mainTest(Test)




