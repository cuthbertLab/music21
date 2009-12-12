#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         corpus/base.py
# Purpose:      Access to the corpus collection
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import re
import os
import doctest, unittest

import music21
from music21 import common
from music21 import converter
from music21 import environment
_MOD = "corpus/base.py"
environLocal = environment.Environment(_MOD)



from music21.corpus import beethoven
from music21.corpus.beethoven import opus18no1
from music21.corpus.beethoven import opus59no1
from music21.corpus.beethoven import opus59no2
from music21.corpus.beethoven import opus59no3

from music21.corpus.haydn import opus74no1  
from music21.corpus.haydn import opus74no2  

from music21.corpus.mozart import k80
from music21.corpus.mozart import k155
from music21.corpus.mozart import k156
from music21.corpus.mozart import k458

from music21.corpus.schumann import opus41no1

from music21.corpus import luca


MODULES = [
            beethoven, 
            opus18no1,
            opus59no1,
            opus59no2,
            opus59no3,

            opus74no1,
            opus74no2,

            k80,
            k155,
            k156,
            k458,

            opus41no1,
            luca,
    ]



#-------------------------------------------------------------------------------
class CorpusException(Exception):
    pass


#-------------------------------------------------------------------------------
def getPaths(extList=None):    
    '''Get all paths in the corpus that match a known extension, or an extenions
    provided by an argument.

    >>> a = getPaths()
    >>> len(a) > 30
    True

    >>> a = getPaths('krn')
    >>> len(a) >= 4
    True
    '''
    if extList == None:
        extList = common.findInputExtension('lily') + common.findInputExtension('mx')
    else:
        if not common.isListLike(extList):
            extList = [extList]

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
                paths.append(fp)    
    return paths


def getComposer(composerName):
    '''
    >>> a = getComposer('beethoven')
    >>> len(a) > 10
    True
    >>> a = getComposer('mozart')
    >>> len(a) > 10
    True
    '''
    paths = getPaths()
    post = []
    for path in paths:
        if composerName.lower() in path.lower():
            post.append(path)
    post.sort()
    return post


def getWork(workName, movementNumber = None):
    '''Search the corpus and return either a list of file paths or a single
    file path

    >>> import os
    >>> a = getWork('opus74no2', 4)
    >>> a.endswith(os.path.sep.join(['haydn', 'opus74no2', 'movement4.xml']))
    True

    >>> a = getWork(['haydn', 'opus74no2', 'movement4.xml'])
    >>> a.endswith(os.path.sep.join(['haydn', 'opus74no2', 'movement4.xml']))
    True

    '''
    paths = getPaths()
    post = []


    # permit workName to be a list of paths/branches
    if common.isListLike(workName):
        workName = os.path.sep.join(workName)

    # below, should '\\' be replaced by os.path.sep?
    # or removed, and not encouraged?
    workSlashes = re.sub('/', r'\\', workName)

    for path in paths:
        if workName.lower() in path.lower():
            post.append(path)
        elif workSlashes.lower() in path.lower():
            post.append(path)
    post.sort()
    if movementNumber is not None:
        try:
            return post[movementNumber - 1]
        except IndexError:
            raise CorpusException(
                "Cannot get movement number " + str(movementNumber) + 
                " either because " + workName + " does not have that many movements or because the corpus is not organized by movement")
    if len(post) == 1:
        return post[0]
    elif len(post) == 0:
        raise CorpusException("Could not find a single file that met this criteria")
    else:
        return post

    

def parseWork(workName, movementNumber=None, forceSource=False):
    '''Return a parsed stream from a converter by providing only a work name.

    If forceSource is True, the original file will always be loaded and pickled
    files, if available, will be ignored.

    >>> aStream = parseWork('opus74no1/movement3')
    '''
    work = getWork(workName, movementNumber)
    return converter.parse(work, forceSource)



#-------------------------------------------------------------------------------
# all paths

paths = getPaths()

#-------------------------------------------------------------------------------
# libraries

beethoven = getComposer('beethoven')
mozart = getComposer('mozart')
haydn = getComposer('haydn')



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


    def testTimingTolerance(self):
        '''Test the performance of loading various files
        This may not produce errors as such, but is used to provide reference
        if overall perforamance has changed.
        '''
        # provide work and expected min/max in seconds
        for known, max in [
            ('beethoven/opus59no2/movement3', 9),
            ('haydn/opus74no1/movement3', 6),
            ('schumann/opus41no1/movement2', 7),

            ]:
            pass

            t = common.Timer()
            t.start()
            x = parseWork(known, forceSource=True)
            t.stop()
            dur = t()
            environLocal.printDebug(['timing tolarance for', known, t])
            self.assertEqual(True, dur <= max) # performance test


if __name__ == "__main__":
    music21.mainTest(Test)




