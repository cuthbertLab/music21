#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common/parallel.py
# Purpose:      Utilities for parallel computing
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015-16 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
__all__ = ['runParallel',
           'runNonParallel',
           'cpus',
           ]

import multiprocessing

from music21.ext.joblib import Parallel, delayed  # @UnresolvedImport

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
    
    # multiprocessing has trouble with introspection
    # pylint: disable=not-callable
    if multiprocessing.current_process().daemon: # @UndefinedVariable
        return runNonParallel(iterable, parallelFunction, updateFunction,
                              updateMultiply, unpackIterable)
    
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


if __name__ == "__main__":
    import music21
    music21.mainTest()

#------------------------------------------------------------------------------
# eof
