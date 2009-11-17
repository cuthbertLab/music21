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

import os

from music21 import common
from music21 import converter

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
    if extList == None:
        extList = common.findFormat('lily')[1] + common.findFormat('mx')[1]

    paths = []    
    for moduleName in MODULES:
        dir = moduleName.__path__[0] # returns a list with one or more paths
        for fn in os.listdir(dir):
            match = False
            for ext in extList:
                if fn.endswith(ext):
                    match = True
                    break 
            if match:
                fp = os.path.join(dir, fn)
                paths.append(fp)    
    return paths


def getComposer(composerName):
    paths = getPaths()
    post = []
    for path in paths:
        if composerName.lower() in path.lower():
            post.append(path)
    post.sort()
    return post


def getWork(workName, movementNumber = None):
    paths = getPaths()
    post = []
    for path in paths:
        if workName.lower() in path.lower():
            post.append(path)
    post.sort()
    if movementNumber is not None:
        try:
            return post[movementNumber - 1]
        except IndexError:
            raise CorpusException(
                "Cannot get movement number " + str(movementNumber) + 
                " either because " + workName + " does not have that many movements or because the corpus is not organized by movement")
    return post

    

def parseWork(workName, movementNumber = None):
    work = getWork(workName, movementNumber)
    return converter.parse(work)



#-------------------------------------------------------------------------------
# all paths
paths = getPaths()

#-------------------------------------------------------------------------------
# libraries

beethoven = getComposer('beethoven')
mozart = getComposer('mozart')
haydn = getComposer('haydn')