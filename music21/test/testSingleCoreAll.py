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

_MOD = 'testSingleCoreAll.py'
environLocal = environment.Environment(_MOD)

from music21.test import coverageM21
cov = coverageM21.getCoverage()






def main(testGroup=('test',), restoreEnvironmentDefaults=False, limit=None):
    '''Run all tests. Group can be test and external

    >>> print(None)
    None
    '''
    globs = __import__('music21').__dict__.copy()
    docTestOptions = (doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    # in case there are any tests here, get a suite to load up later
    s1 = doctest.DocTestSuite(
        __name__,
        globs=globs,
        optionflags=docTestOptions
        )

    modGather = commonTest.ModuleGather()
    modules = modGather.load(restoreEnvironmentDefaults)

    verbosity = 2
    if 'verbose' in sys.argv:
        verbosity = 1 # this seems to hide most display

    environLocal.printDebug('looking for Test classes...\n')
    # look over each module and gather doc tests and unittests
    totalModules = 0
    
    for module in common.sortModules(modules):
        unitTestCases = []
        if limit is not None:
            if totalModules > limit:
                break
        totalModules += 1
        # get Test classes in module
        if not hasattr(module, 'Test'):
            environLocal.printDebug('%s has no Test class' % module)
        else:
            if 'test' in testGroup:
                unitTestCases.append(module.Test)
        if not hasattr(module, 'TestExternal'):
            pass
            #environLocal.printDebug('%s has no TestExternal class\n' % module)
        else:
            if 'external' in testGroup or 'testExternal' in testGroup:
                unitTestCases.append(module.TestExternal)

        # for each Test class, load this into a suite
        for testCase in unitTestCases:
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(testCase)
            s1.addTests(s2)
        try:
            globs = __import__('music21').__dict__.copy()
            s3 = doctest.DocTestSuite(
                module,
                globs=globs,
                optionflags=docTestOptions,
                )
            s1.addTests(s3)
        except ValueError:
            environLocal.printDebug('%s cannot load Doctests' % module)
            continue
        
        allLocals = [getattr(module, x) for x in dir(module)]
        testRunner.addDocAttrTestsToSuite(s1, allLocals, outerFilename=module.__file__, globs=globs, optionflags=docTestOptions)
    
    testRunner.fixTestsForPy2and3(s1)
    
    environLocal.printDebug('running Tests...\n')
            
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)  # import modules...
        runner = unittest.TextTestRunner(verbosity=verbosity)
        finalTestResults = runner.run(s1)  
    
    coverageM21.stopCoverage(cov)
        
    if (len(finalTestResults.errors) > 0 or
        len(finalTestResults.failures) > 0 or
        len(finalTestResults.unexpectedSuccesses) > 0):
            exit(1)
    else:
        exit(0)

    # this should work but requires python 2.7 and the testRunner arg does not
    # seem to work properly
    #unittest.main(testRunner=runner, failfast=True)
                 

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
        main(sys.argv[1:])
    else:
        main()


#------------------------------------------------------------------------------
# eof

