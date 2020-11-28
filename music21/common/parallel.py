# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/parallel.py
# Purpose:      Utilities for parallel computing
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015-16 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
__all__ = [
    'runParallel',
    'runNonParallel',
    'cpus',
]

import multiprocessing
import unittest

from joblib import Parallel, delayed


def runParallel(iterable, parallelFunction, *,
                updateFunction=None, updateMultiply=3,
                unpackIterable=False, updateSendsIterable=False):
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
    tuple of different arguments to parallelFunction.

    If updateSendsIterable is True then the update function will get the iterable
    content, after the output.

    As of Python 3, partial functions are pickleable, so if you need to pass the same
    arguments to parallelFunction each time, make it a partial function before passing
    it to runParallel.

    Note that parallelFunction, iterable's contents, and the results of calling parallelFunction
    must all be pickleable, and that if pickling the contents or
    unpickling the results takes a lot of time, you won't get nearly the speedup
    from this function as you might expect.  The big culprit here is definitely
    music21 streams.

    >>> files = ['bach/bwv66.6', 'schoenberg/opus19', 'AcaciaReel']
    >>> def countNotes(fn):
    ...     c = corpus.parse(fn)  # this is the slow call that is good to parallelize
    ...     return len(c.recurse().notes)
    >>> #_DOCS_SHOW outputs = common.runParallel(files, countNotes)
    >>> outputs = common.runNonParallel(files, countNotes) #_DOCS_HIDE cant pickle doctest funcs.
    >>> outputs
    [165, 50, 131]

    Set updateFunction=True to get an update every 3 * numCpus (-1 if > 2)

    >>> #_DOCS_SHOW outputs = common.runParallel(files, countNotes, updateFunction=True)
    >>> outputs = common.runNonParallel(files, countNotes, updateFunction=True) #_DOCS_HIDE
    Done 0 tasks of 3
    Done 3 tasks of 3

    With a custom updateFunction that gets each output:

    >>> def yak(position, length, output):
    ...     print("%d:%d %d is a lot of notes!" % (position, length, output))
    >>> #_DOCS_SHOW outputs = common.runParallel(files, countNotes, updateFunction=yak)
    >>> outputs = common.runNonParallel(files, countNotes, updateFunction=yak) #_DOCS_HIDE
    0:3 165 is a lot of notes!
    1:3 50 is a lot of notes!
    2:3 131 is a lot of notes!

    Or with updateSendsIterable, we can get the original files data as well:

    >>> def yik(position, length, output, fn):
    ...     print("%d:%d (%s) %d is a lot of notes!" % (position, length, fn, output))
    >>> #_DOCS_SHOW outputs = common.runParallel(files, countNotes, updateFunction=yik,
    >>> outputs = common.runNonParallel(files, countNotes, updateFunction=yik, #_DOCS_HIDE
    ...             updateSendsIterable=True)
    0:3 (bach/bwv66.6) 165 is a lot of notes!
    1:3 (schoenberg/opus19) 50 is a lot of notes!
    2:3 (AcaciaReel) 131 is a lot of notes!

    unpackIterable is useful for when you need to send multiple values to your function
    call as separate arguments.  For instance, something like:

    >>> def pitchesAbove(fn, minPitch):  # a two-argument function
    ...     c = corpus.parse(fn)  # again, the slow call goes in the function
    ...     return len([p for p in c.pitches if p.ps > minPitch])

    >>> inputs = [('bach/bwv66.6', 60),
    ...           ('schoenberg/opus19', 72),
    ...           ('AcaciaReel', 66)]
    >>> #_DOCS_SHOW outputs = common.runParallel(inputs, pitchesAbove, unpackIterable=True)
    >>> outputs = common.runNonParallel(inputs, pitchesAbove, unpackIterable=True) #_DOCS_HIDE
    >>> outputs
    [99, 11, 123]
    '''
    # multiprocessing has trouble with introspection
    # pylint: disable=not-callable
    numCpus = cpus()

    if numCpus == 1 or multiprocessing.current_process().daemon:  # @UndefinedVariable
        return runNonParallel(iterable, parallelFunction,
                              updateFunction=updateFunction,
                              updateMultiply=updateMultiply,
                              unpackIterable=unpackIterable,
                              updateSendsIterable=updateSendsIterable)

    iterLength = len(iterable)
    totalRun = 0
    if updateFunction is None:
        updateMultiply = iterLength
        # if there is no need for updates, run at max speed
        #    -- do the whole list at once.

    resultsList = []

    def callUpdate(ii):
        if updateFunction is True:
            print("Done {} tasks of {}".format(min([ii, iterLength]),
                                               iterLength))
        elif updateFunction not in (False, None):
            for thisPosition in range(ii - (updateMultiply * numCpus), ii):
                if thisPosition < 0:
                    continue

                if thisPosition >= len(resultsList):
                    thisResult = None
                else:
                    thisResult = resultsList[thisPosition]

                if updateSendsIterable is False:
                    updateFunction(thisPosition, iterLength, thisResult)
                else:
                    updateFunction(thisPosition, iterLength, thisResult, iterable[thisPosition])

    callUpdate(0)

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
            callUpdate(totalRun)

    return resultsList


def runNonParallel(iterable, parallelFunction, *,
                   updateFunction=None, updateMultiply=3,
                   unpackIterable=False, updateSendsIterable=False):
    '''
    This is intended to be a perfect drop in replacement for runParallel, except that
    it runs on one core only, and not in parallel.

    Used automatically if we're already in a parallelized function.
    '''
    iterLength = len(iterable)
    resultsList = []

    def callUpdate(ii):
        if ii % updateMultiply != 0:
            return

        if updateFunction is True:
            print("Done {} tasks of {}".format(min([ii, iterLength]),
                                               iterLength))
        elif updateFunction not in (False, None):
            for thisPosition in range(ii - updateMultiply, ii):
                if thisPosition < 0:
                    continue

                if thisPosition >= len(resultsList):
                    thisResult = None
                else:
                    thisResult = resultsList[thisPosition]

                if updateSendsIterable is False:
                    updateFunction(thisPosition, iterLength, thisResult)
                else:
                    updateFunction(thisPosition, iterLength, thisResult, iterable[thisPosition])

    callUpdate(0)
    for i in range(iterLength):
        if unpackIterable:
            _r = parallelFunction(*iterable[i])
        else:
            _r = parallelFunction(iterable[i])

        resultsList.append(_r)

        callUpdate(i + 1)

    return resultsList


def cpus():
    '''
    Returns the number of CPUs or if >= 3, one less (to leave something out for multiprocessing)
    '''
    cpuCount = multiprocessing.cpu_count()  # @UndefinedVariable
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
#     return pickle.loads(pickle.dumps(obj, protocol=-1))


# pickleable testing functions.

def _countN(fn):
    from music21 import corpus
    c = corpus.parse(fn)
    return len(c.recurse().notes)


def _countUnpacked(i, fn):
    if i >= 3:
        return False
    if fn not in ['bach/bwv66.6', 'schoenberg/opus19', 'AcaciaReel']:
        return False
    return True


class Test(unittest.TestCase):
    # pylint: disable=redefined-outer-name
    def x_figure_out_segfault_testMultiprocess(self):
        files = ['bach/bwv66.6', 'schoenberg/opus19', 'AcaciaReel']
        # for importing into testSingleCoreAll we need the full path to the modules
        from music21.common.parallel import _countN, _countUnpacked  # @UnresolvedImport
        output = runParallel(files, _countN)
        self.assertEqual(output, [165, 50, 131])
        runParallel(files, _countN,
                    updateFunction=self._customUpdate1)
        runParallel(files, _countN,
                    updateFunction=self._customUpdate2,
                    updateSendsIterable=True)
        passed = runParallel(list(enumerate(files)), _countUnpacked,
                             unpackIterable=True)
        self.assertEqual(len(passed), 3)
        self.assertNotIn(False, passed)

    # testing functions
    def _customUpdate1(self, i, total, output):
        self.assertEqual(total, 3)
        self.assertLess(i, 3)
        self.assertIn(output, [165, 50, 131])

    def _customUpdate2(self, i, unused_total, unused_output, fn):
        self.assertIn(fn, ['bach/bwv66.6', 'schoenberg/opus19', 'AcaciaReel'])


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

