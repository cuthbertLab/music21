#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common/misc.py
# Purpose:      Everything that doesn't fit into anything else.
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
If it doesn't fit anywhere else in the common directory, you'll find it here...
'''

__all__ = ['getMissingImportStr',
           'getPlatform', 
           'sortModules',
           'pitchList',
           'runningUnderIPython',
           'defaultDeepcopy',
           'runParallel',
           'runNonParallel',
           'cpus',]

import copy
import os
import sys
import textwrap
import time
import multiprocessing

from music21.ext.joblib import Parallel, delayed  # @UnresolvedImport

#-------------------------------------------------------------------------------
# provide warning strings to users for use in conditional imports

def getMissingImportStr(modNameList):
    '''
    Given a list of missing module names, returns a nicely-formatted message to the user
    that gives instructions on how to expand music21 with optional packages.


    >>> print(common.getMissingImportStr(['matplotlib']))
    Certain music21 functions might need the optional package matplotlib;
    if you run into errors, install it by following the instructions at
    http://mit.edu/music21/doc/installing/installAdditional.html
    
    >>> print(common.getMissingImportStr(['matplotlib', 'numpy']))
    Certain music21 functions might need these optional packages: matplotlib, numpy;
    if you run into errors, install them by following the instructions at
    http://mit.edu/music21/doc/installing/installAdditional.html    
    '''
    if len(modNameList) == 0:
        return None
    elif len(modNameList) == 1:
        return textwrap.dedent('''\
                  Certain music21 functions might need the optional package %s;
                  if you run into errors, install it by following the instructions at
                  http://mit.edu/music21/doc/installing/installAdditional.html''' % 
                  modNameList[0])
    else:
        return textwrap.dedent('''\
                   Certain music21 functions might need these optional packages: %s;
                   if you run into errors, install them by following the instructions at
                   http://mit.edu/music21/doc/installing/installAdditional.html''' % 
                   ', '.join(modNameList))


def getPlatform():
    '''
    Return the name of the platform, where platforms are divided
    between 'win' (for Windows), 'darwin' (for MacOS X), and 'nix' for 
    (GNU/Linux and other variants).

    :rtype: str
    '''
    # possible os.name values: 'posix', 'nt', 'mac' (=Mac OS 9), 'os2', 'ce',
    # 'java', 'riscos'.
    if os.name == 'nt' or sys.platform.startswith('win'):
        return 'win'
    elif sys.platform == 'darwin':
        return 'darwin' #
    elif os.name == 'posix': # catch all other nix platforms
        return 'nix' # this must be after the Mac Darwin check, b/c Darwin is also posix

def sortModules(moduleList):
    '''
    Sort a lost of imported module names such that most recently modified is
    first.  In ties, last accesstime is used then module name
    
    Will return a different order each time depending on the last mod time
    
    :rtype: list(str)
    '''
    sort = []
    modNameToMod = {}    
    for mod in moduleList:
        modNameToMod[mod.__name__] = mod
        fp = mod.__file__ # returns the pyc file
        stat = os.stat(fp)
        lastmod = time.localtime(stat[8])
        asctime = time.asctime(lastmod)
        sort.append((lastmod, asctime, mod.__name__))
    sort.sort()
    sort.reverse()
    # just return module list
    return [modNameToMod[modName] for lastmod, asctime, modName in sort]



#-----------------------------
def pitchList(pitchL):
    '''
    utility method that replicates the previous behavior of 
    lists of pitches
    '''
    return '[' + ', '.join([x.nameWithOctave for x in pitchL]) + ']'


def runningUnderIPython():
    '''
    return bool if we are running under iPython Notebook (not iPython)

    (no tests, since will be different)

    This post:
    http://stackoverflow.com/questions/15411967/
        how-can-i-check-if-code-is-executed-in-the-ipython-notebook
    
    says not to do this, but really, I can't think of another way 
    to have different output as default.
    
    :rtype: bool
    '''
    if sys.stderr.__class__.__name__ == 'OutStream':
        return True
    else:
        return False


    
#-----------------------------
# match collections, defaultdict()


# NB -- temp files (tempFile) etc. are in environment.py

#-------------------------------------------------------------------------------
def defaultDeepcopy(obj, memo, callInit=True):
    '''
    Unfortunately, it is not possible to do something like:
    
        def __deepcopy__(self, memo):
            if self._noDeepcopy:
                return self.__class__()
            else:
                copy.deepcopy(self, memo, ignore__deepcopy__=True)
    
    Or, else: return NotImplemented
    
    so that's what this is for:
    
        def __deepcopy__(self, memo):
            if self._noDeepcopy:
                return self.__class__()
            else:
                common.defaultDeepcopy(obj, memo)
                
    looks through both __slots__ and __dict__ and does a deepcopy
    of anything in each of them and returns the new object.
    
    If callInit is False, then only __new__() is called.  This is
    much faster if you're just going to overload every instance variable.    
    '''
    if callInit is False:
        new = obj.__class__.__new__(obj.__class__)
    else:
        new = obj.__class__()

    dictState = getattr(obj, '__dict__', None)
    if dictState is not None:
        for k in dictState:
            setattr(new, k, copy.deepcopy(dictState[k], memo))
    slots = set()
    for cls in obj.__class__.mro(): # it is okay that it's in reverse order, since it's just names
        slots.update(getattr(cls, '__slots__', ()))
    for slot in slots:
        slotValue = getattr(obj, slot, None) 
            # might be none if slot was deleted; it will be recreated here
        setattr(new, slot, copy.deepcopy(slotValue))

    return new

def runParallel(iterable, parallelFunction, 
                updateFunction=None, updateMultiply=3,
                unpackIterable=False):
    '''
    runs parallelFunction over iterable in parallel, optionally calling updateFunction after
    each common.cpus * updateMultiply calls.
    
    Setting updateMultiply too small can make it so that cores wait around when they
    could be working if one CPU has a particularly hard task.  Setting it too high
    can make it seem like the job has hung.

    updateFunction should take three arguments: the current position, the total to run,
    and the most recent results.  It does not need to be pickleable, and in fact,
    a bound method might be very useful here.  Or updateFunction can be "True"
    which just prints a generic message.

    If unpackIterable is True then each element in iterable is considered a list or
    tuple of different arguments to delayFunction.

    As of Python 2.7, partial functions are pickleable, so if you need to pass the same
    arguments to parallelFunction each time, make it a partial function before passing
    it to runParallel.

    Note that parallelFunction, iterable's contents, and the results of calling parallelFunction
    must all be pickleable, and that if pickling the contents or
    unpickling the results takes a lot of time, you won't get nearly the speedup
    from this function as you might expect.  The big culprit here is definitely
    music21 streams.
    '''
    iterLength = len(iterable)
    totalRun = 0
    numCpus = cpus()
    
    resultsList = []
    
    if os.environ.get('alreadyRunningInParallel', 'no') == 'yes':
        return runNonParallel(iterable, parallelFunction, updateFunction,
                              updateMultiply, unpackIterable)
    else:
        os.environ['alreadyRunningInParallel'] = 'yes'
    
    with Parallel(n_jobs=numCpus) as para:
        delayFunction = delayed(parallelFunction)
        while totalRun < iterLength:
            endPosition = min(totalRun + numCpus * updateMultiply, iterLength)
            rangeGen = range(totalRun, endPosition)
            
            if unpackIterable:
                _r = para(delayFunction(*iterable[i]) for i in rangeGen)
            else:
                _r = para(delayFunction(iterable[i]) for i in rangeGen)

            totalRun = endPosition
            resultsList.extend(_r)
            if updateFunction is True:
                print("Done {} tasks of {}".format(totalRun, iterLength))
            elif updateFunction is not None:
                updateFunction(totalRun, iterLength, _r)

    os.environ['alreadyRunningInParallel'] = 'no'

    return resultsList


def runNonParallel(iterable, parallelFunction, 
                updateFunction=None, updateMultiply=3,
                unpackIterable=False):
    '''
    This is intended to be a perfect drop in replacement for runParallel, except that
    it runs on one core only, and not in parallel.
    
    Used, for instance, if we're already in a parallel function.
    '''
    iterLength = len(iterable)
    resultsList = []

    for i in range(iterLength):
        if unpackIterable:
            _r = parallelFunction(*iterable[i])
        else:
            _r = parallelFunction(iterable[i])
        
        resultsList.append(_r)
            
        if updateFunction is True and i % updateMultiply == 0:
            print("Done {} tasks of {} not in parallel".format(i, iterLength))
        elif updateFunction is not None and i % updateMultiply == 0:
            updateFunction(i, iterLength, [_r])
        
    return resultsList
    

def cpus():
    '''
    Returns the number of CPUs or if >= 3, one less (to leave something out for multiprocessing)
    '''
    cpuCount = multiprocessing.cpu_count() # @UndefinedVariable
    if cpuCount >= 3:
        return cpuCount - 1
    else:
        return cpuCount

# Not shown to work.
# def pickleCopy(obj):
#     '''
#     use pickle to serialize/deserialize a copy of an object -- much faster than deepcopy,
#     but only works for things that are completely pickleable.
#     '''
#     return pickleMod.loads(pickleMod.dumps(obj, protocol=-1))


if __name__ == '__main__':
    import music21
    music21.mainTest()
