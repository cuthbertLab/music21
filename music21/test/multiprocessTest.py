# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         multiprocesssTest.py
# Purpose:      Controller for all tests in music21 run concurrently.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012-15 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
Multiprocess testing.  Tests all doctests and Test unittest objects in all
modules that are imported when running "import music21".  Runs threads on
each core of a multicore system unless there are more than 2 cores, in which
case it runs on n-1 cores.

N.B. this gets a slightly different set of modules than test/test.py does
because the `imp` module is not available for threaded processing.  Running
both modules gives great coverage of just about everything -- do that before
building a new release.

Run test/testDocumentation after this.
'''
from __future__ import print_function

import collections
import doctest
import multiprocessing
import os
import sys
import time
import unittest

from music21 import environment
from music21.test import testRunner
from music21.test import commonTest

_MOD = 'multiprocessTest.py'
environLocal = environment.Environment(_MOD)

ModuleResponse = collections.namedtuple('ModuleResponse', 
                    'returnCode fp moduleName success testRunner errors failures testsRun runTime')
ModuleResponse.__new__.__defaults__ = (None,) * len(ModuleResponse._fields)
 
#-------------------------------------------------------------------------------

def runOneModuleWithoutImp(args):
    modGath = args[0] # modGather object
    fp = args[1]
    verbosity = False
    timeStart = time.time()
    
    moduleObject = modGath.getModuleWithoutImp(fp)
    environLocal.printDebug('running %s \n' % fp)
    if moduleObject == 'skip':
        success = '%s is skipped \n' % fp
        environLocal.printDebug(success)
        return ModuleResponse('Skipped', fp, success)
    elif moduleObject == 'notInTree':
        success = '%s is in the music21 directory but not imported in music21. Skipped -- fix!' % modGath._getNamePeriod(fp)
        environLocal.printDebug(success)
        return ModuleResponse("NotInTree", fp, success)

    
    try:
        moduleName = modGath._getName(fp)
        
        s1 = commonTest.defaultDoctestSuite()
        
        # get Test classes in moduleObject
        if not hasattr(moduleObject, 'Test'):
            environLocal.printDebug('%s has no Test class' % moduleObject)
        else:
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(moduleObject.Test)
            s1.addTests(s2)
            
        try:
            s3 = commonTest.defaultDoctestSuite(moduleObject)
            s1.addTests(s3)
        except ValueError:
            environLocal.printDebug('%s cannot load Doctests' % moduleObject)
            pass        

        testRunner.fixTestsForPy2and3(s1)
        
        
        environLocal.printDebug('running Tests...\n')
        runner = unittest.TextTestRunner(verbosity=verbosity)
        try:
            testResult = runner.run(s1)  
            
            # need to make testResult pickleable by removing the instancemethod parts...
            errors = []
            for e in testResult.errors:
                errors.append(e[1])
            failures = []
            for f in testResult.failures:
                failures.append(f[1])
            runTime = int(time.time() - timeStart)
            return ModuleResponse("TestsRun", fp, moduleName, testResult.wasSuccessful(), 
                                  str(testResult), errors, failures, testResult.testsRun, runTime)
        except Exception as excp: # pylint: disable=broad-except
            environLocal.printDebug('*** Exception in running %s: %s...\n' % (moduleName, excp))
            return ModuleResponse("TrappedException", fp, moduleName, None, str(excp))
    except Exception as excp: # pylint: disable=broad-except
        environLocal.printDebug('*** Large Exception in running %s: %s...\n' % (fp, excp))
        return ModuleResponse("LargeException", fp, None, None, str(excp))

    
def mainPoolRunner(testGroup=('test',), restoreEnvironmentDefaults=False, leaveOut = 1):
    '''
    Run all tests. Group can be test and/or external
    '''    
    
    timeStart = time.time()
    poolSize = multiprocessing.cpu_count() # @UndefinedVariable
    if poolSize > 2:
        poolSize = poolSize - leaveOut
    else:
        leaveOut = 0

    print('Creating %d processes for multiprocessing (omitting %d processors)' % (poolSize, leaveOut))
    

    modGather = commonTest.ModuleGather(useExtended=True)

    maxTimeout = 200
    pathsToRun = modGather.modulePaths # [30:60]


    pool = multiprocessing.Pool(processes=poolSize) # @UndefinedVariable # pylint: disable=not-callable
    
    # imap returns the results as they are completed.  Since the number of files is small,
    # the overhead of returning is outweighed by the positive aspect of getting results immediately
    # unordered says that results can RETURN in any order; not that they'd be pooled out in any
    # order.
    res = pool.imap_unordered(runOneModuleWithoutImp, 
                              ((modGather, fp) for fp in pathsToRun))

    continueIt = True
    timeouts = 0
    eventsProcessed = 0
    summaryOutput = []
    
    while continueIt is True:
        try:
            newResult = res.next(timeout=1)
            if timeouts >= 5:
                print("")
            if newResult.testRunner is not None:
                print("%s: %s" % (newResult.moduleName, newResult.testRunner))
            timeouts = 0
            eventsProcessed += 1
            summaryOutput.append(newResult)
        except multiprocessing.TimeoutError: # @UndefinedVariable
            timeouts += 1
            if timeouts == 5 and eventsProcessed > 0:
                print("Delay in processing, seconds: ", end="")
            elif timeouts == 5:
                print("Starting first modules, should take 5-10 seconds: ", end="")
            if timeouts % 5 == 0:
                print(str(timeouts) + " ", end="")
            if timeouts > maxTimeout and eventsProcessed > 0:
                print("\nToo many delays, giving up...")
                continueIt = False
                printSummary(summaryOutput, timeStart, pathsToRun)
                pool.close()
                exit()
        except StopIteration:
            continueIt = False
            pool.close()    
            pool.join()
        except Exception as excp: # pylint: disable=broad-except
            eventsProcessed += 1
            exceptionLog = ModuleResponse("UntrappedException", None, "%s" % excp)
            summaryOutput.append(exceptionLog)

    printSummary(summaryOutput, timeStart, pathsToRun)

def printSummary(summaryOutput, timeStart, pathsToRun):
    outStr = ""
    summaryOutputTwo = [i[1] for i in summaryOutput]
    for fp in pathsToRun:
        if fp not in summaryOutputTwo:
            failLog = ModuleResponse("NoResult", fp)
            summaryOutput.append(failLog)

    totalTests = 0

    skippedSummary = []
    successSummary = []
    errorsFoundSummary = []
    otherSummary = []
    for moduleResponse in summaryOutput:
        print(moduleResponse)
        if moduleResponse.returnCode == 'Skipped':
            skippedSummary.append("Skipped: %s" % moduleResponse.fp)
        elif moduleResponse.returnCode == 'NoResult':
            otherSummary.append("Silent test fail for %s: Run separately!" % moduleResponse.fp)
        elif moduleResponse.returnCode == 'UntrappedException':
            otherSummary.append("Untrapped Exception for unknown module: %s" % moduleResponse.fp)
        elif moduleResponse.returnCode == 'TrappedException':
            otherSummary.append("Trapped Exception for module %s, at %s: %s" % 
                                (moduleResponse.moduleName, moduleResponse.fp, moduleResponse.testRunner))
        elif moduleResponse.returnCode == 'LargeException':
            otherSummary.append("Large Exception for file %s: %s" % 
                                (moduleResponse.fp, moduleResponse.testResult))
        elif moduleResponse.returnCode == 'ImportError':
            otherSummary.append("Import Error for %s" % moduleResponse.fp)
        elif moduleResponse.returnCode == 'NotInTree':
            if moduleResponse.moduleName == "":
                otherSummary.append("Not in Tree Error: %s " % moduleResponse.moduleName) 
        elif moduleResponse.returnCode == 'TestsRun':
            totalTests += moduleResponse.testsRun
            if moduleResponse.success:
                successSummary.append("%s successfully ran %d tests in %d seconds" 
                                      % (moduleResponse.moduleName, 
                                         moduleResponse.testsRun,
                                         moduleResponse.runTime))
            else:
                errorsList = moduleResponse.errors # not the original errors list! see pickle note above
                failuresList = moduleResponse.failures
                errorsFoundSummary.append("\n-----------------------------\n" + 
                                          "%s had %d ERRORS and %d FAILURES in %d tests after %d seconds:\n-----------------------------\n" 
                                          % (moduleResponse.moduleName, len(errorsList), 
                                             len(failuresList), moduleResponse.testsRun, moduleResponse.runTime))

                for e in errorsList:
                    outStr += e + "\n"
                    errorsFoundSummary.append('%s' % (e))
                for f in failuresList:
                    outStr += f + "\n"
                    errorsFoundSummary.append('%s' % (f))
#                for e in errorsList:
#                    print e[0], e[1]
#                    errorsFoundSummary.append('%s: %s' % (e[0], e[1]))
#                for f in failuresList:
#                    print f[0], f[1]
#                    errorsFoundSummary.append('%s: %s' % (f[0], f[1]))    
        else:
            otherSummary.append("Unknown return code %s" % moduleResponse)


    outStr += "\n\n---------------SUMMARY---------------------------------------------------\n"
    for l in skippedSummary:
        outStr += l + "\n"
    for l in successSummary:
        outStr += l + "\n"
    for l in otherSummary:
        outStr += l + "\n"
    for l in errorsFoundSummary:
        outStr += l + "\n"
    outStr += "-------------------------------------------------------------------------\n"
    elapsedTime = time.time() - timeStart
    outStr += "Ran %d tests in %.4f seconds\n" % (totalTests, elapsedTime)
    sys.stdout.flush()
    print(outStr)
    sys.stdout.flush()
    
    import datetime
    lastResults = os.path.join(environLocal.getRootTempDir(), 'lastResults.txt')
    with open(lastResults, 'w') as f:
        f.write(outStr)
        f.write("Run at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    print("Results at " + lastResults)

if __name__ == '__main__':
    #mg = ModuleGather(useExtended=True)
    #mm = mg.getModuleWithoutImp('trecento.capua')
    #print mm
    mainPoolRunner()
