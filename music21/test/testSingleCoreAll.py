# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         test.py
# Purpose:      Controller for all module tests in music21.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Controller to run all module tests in the music21 folders.

Runs great, but slowly on multiprocessor systems.
'''

import doctest
import sys
import unittest
import warnings

from music21 import common
from music21 import environment

from music21.test import testRunner
from music21.test import commonTest

_MOD = 'test.testSingleCoreAll'
environLocal = environment.Environment(_MOD)

from music21.test import coverageM21

# this is designed to be None for all but one system and a Coverage() object
# for one system.
cov = coverageM21.getCoverage()



def main(testGroup=('test',), restoreEnvironmentDefaults=False, limit=None, verbosity=2):
    '''
    Run all tests. Group can be test and external

    >>> print(None)
    None
    '''
    s1 = commonTest.defaultDoctestSuite(__name__)

    modGather = commonTest.ModuleGather()
    modules = modGather.load(restoreEnvironmentDefaults)

    environLocal.printDebug('looking for Test classes...\n')
    # look over each module and gather doc tests and unittests
    totalModules = 0
    sortMods = common.misc.sortModules(modules)
    # print(dir(sortMods[0]))
    
    for moduleObject in sortMods:
        unitTestCases = []
        if limit is not None:
            if totalModules > limit:
                break
        totalModules += 1
        # get Test classes in module
        if not hasattr(moduleObject, 'Test'):
            environLocal.printDebug('%s has no Test class' % moduleObject)
        else:
            if 'test' in testGroup:
                unitTestCases.append(moduleObject.Test)
        if not hasattr(moduleObject, 'TestExternal'):
            pass
            #environLocal.printDebug('%s has no TestExternal class\n' % module)
        else:
            if 'external' in testGroup or 'testExternal' in testGroup:
                unitTestCases.append(moduleObject.TestExternal)

        # for each Test class, load this into a suite
        for testCase in unitTestCases:
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(testCase)
            s1.addTests(s2)
        try:
            s3 = commonTest.defaultDoctestSuite(moduleObject)
            s1.addTests(s3)
        except ValueError:
            environLocal.printDebug('%s cannot load Doctests' % moduleObject)
            continue

        allLocals = [getattr(moduleObject, x) for x in dir(moduleObject)]

        globs = __import__('music21').__dict__.copy()
        docTestOptions = (doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
        testRunner.addDocAttrTestsToSuite(s1,
                                          allLocals,
                                          outerFilename=moduleObject.__file__,
                                          globs=globs,
                                          optionflags=docTestOptions,
                                          # no checker here
                                          )

    testRunner.fixDoctests(s1)

    environLocal.printDebug('running Tests...\n')

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)  # import modules...
        runner = unittest.TextTestRunner(verbosity=verbosity)
        finalTestResults = runner.run(s1)

    coverageM21.stopCoverage(cov)

    if (finalTestResults.errors or
            finalTestResults.failures or
            finalTestResults.unexpectedSuccesses):
        returnCode = 1
    else:
        returnCode = 0

    return returnCode



def travisMain():
    # the main call for travis-ci tests.
    # exits with the returnCode
    returnCode = main(verbosity=1)
    exit(returnCode)


#-------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        reload(sys) # @UndefinedVariable
        sys.setdefaultencoding("UTF-8") # @UndefinedVariable
    except (NameError, AttributeError):
        pass # no need in Python3

    # if optional command line arguments are given, assume they are
    # test group arguments
    if len(sys.argv) >= 2:
        unused_returnCode = main(sys.argv[1:])
    else:
        unused_returnCode = main()

#------------------------------------------------------------------------------
# eof

