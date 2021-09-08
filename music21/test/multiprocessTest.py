# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         multiprocesssTest.py
# Purpose:      Controller for all tests in music21 run concurrently.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012-15 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
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
import dataclasses
import multiprocessing
import os
import sys
import time
import unittest
from typing import Optional, Any

from music21 import environment
from music21 import common
from music21.test import testRunner
from music21.test import commonTest

_MOD = 'test.multiprocessTest'
environLocal = environment.Environment(_MOD)

@dataclasses.dataclass
class ModuleResponse:
    returnCode: Optional[str] = None
    fp: Any = None
    moduleName: Optional[str] = None
    success: Any = None
    testRunner: Any = None
    errors: Any = None
    failures: Any = None
    testsRun: Any = None
    runTime: Any = None


# ------------------------------------------------------------------------------

def runOneModuleWithoutImp(args):
    modGath = args[0]  # modGather object
    fp = args[1]
    verbosity = False
    timeStart = time.time()

    moduleObject = modGath.getModuleWithoutImp(fp)

    environLocal.printDebug(f'running {fp} \n')
    namePeriod = modGath._getNamePeriod(fp)
    if moduleObject == 'skip':
        success = f'{fp} is skipped \n'
        environLocal.printDebug(success)
        return ModuleResponse(returnCode='Skipped', fp=fp, success=success)
    elif moduleObject == 'notInTree':
        success = (
            f'{namePeriod} is in the music21 directory but not imported in music21. Skipped -- fix!'
        )
        environLocal.printDebug(success)
        return ModuleResponse(returnCode='NotInTree', fp=fp, success=success)

    try:
        moduleName = modGath._getName(fp)

        s1 = commonTest.defaultDoctestSuite()

        # get Test classes in moduleObject
        if not hasattr(moduleObject, 'Test'):
            environLocal.printDebug(f'{moduleObject} has no Test class')
        else:
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(moduleObject.Test)
            s1.addTests(s2)

        try:
            s3 = commonTest.defaultDoctestSuite(moduleObject)
            s1.addTests(s3)
        except ValueError:
            environLocal.printDebug(f'{moduleObject} cannot load Doctests')
            pass

        testRunner.fixDoctests(s1)

        environLocal.printDebug('running Tests...\n')
        runner = commonTest.Music21TestRunner(verbosity=verbosity)
        try:
            testResult = runner.run(s1)

            # need to make testResult pickleable by removing the instancemethod parts...
            errors = []
            for e in testResult.errors:
                errors.append(e[1])
            failures = []
            for f in testResult.failures:
                failures.append(f[1])
            runTime = round(10 * (time.time() - timeStart)) / 10.0
            return ModuleResponse(returnCode='TestsRun',
                                  fp=fp,
                                  moduleName=moduleName,
                                  success=testResult.wasSuccessful(),
                                  testRunner=str(testResult),
                                  errors=errors,
                                  failures=failures,
                                  testsRun=testResult.testsRun,
                                  runTime=runTime)
        except Exception as excp:  # pylint: disable=broad-except
            environLocal.printDebug(f'*** Exception in running {moduleName}: {excp}...\n')
            return ModuleResponse(returnCode='TrappedException',
                                  fp=fp,
                                  moduleName=moduleName,
                                  success=None,
                                  testRunner=str(excp)
                                  )
    except Exception as excp:  # pylint: disable=broad-except
        environLocal.printDebug(f'*** Large Exception in running {fp}: {excp}...\n')
        return ModuleResponse(returnCode='LargeException',
                              fp=fp,
                              testRunner=str(excp))


def mainPoolRunner(testGroup=('test',), restoreEnvironmentDefaults=False, leaveOut=1):
    '''
    Run all tests. Group can be test and/or external
    '''
    commonTest.testImports()

    normalStdError = sys.stderr

    timeStart = time.time()
    poolSize = common.cpus()

    print(f'Creating {poolSize} processes for multiprocessing (omitting {leaveOut} processors)')

    modGather = commonTest.ModuleGather(useExtended=True)

    maxTimeout = 200
    pathsToRun = modGather.modulePaths  # [30:60]

    # pylint: disable=not-callable
    with multiprocessing.Pool(processes=poolSize) as pool:

        # imap returns the results as they are completed.
        # Since the number of files is small, the overhead of returning is
        # outweighed by the positive aspect of getting results immediately
        # unordered says that results can RETURN in any order; not that
        # they'd be pooled out in any order.
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
                    print('')
                if newResult is not None:
                    if newResult.moduleName is not None:
                        mn = newResult.moduleName
                        mn = mn.replace('___init__', '')
                        mn = mn.replace('_', '.')
                    else:
                        mn = ''
                    rt = newResult.runTime
                    if rt is not None:
                        rt = round(newResult.runTime * 10) / 10.0
                        if not newResult.errors and not newResult.failures:
                            print(f'\t\t\t\t{mn}: {newResult.testsRun} tests in {rt} secs')
                        else:
                            numErr = len(newResult.errors)
                            numFail = len(newResult.failures)
                            print(f'\t\t\t\t{mn}: {newResult.testsRun} tests, '
                                  f'{numErr} errors {numFail} failures in {rt} secs')
                timeouts = 0
                eventsProcessed += 1
                summaryOutput.append(newResult)
            except multiprocessing.TimeoutError:
                timeouts += 1
                if timeouts == 5 and eventsProcessed > 0:
                    print('Delay in processing, seconds: ', end='')
                elif timeouts == 5:
                    print('Starting first modules, should take 5-10 seconds: ', end='')

                if timeouts % 5 == 0:
                    print(str(timeouts) + ' ', end='', flush=True)
                if timeouts > maxTimeout and eventsProcessed > 0:
                    print('\nToo many delays, giving up...', flush=True)
                    continueIt = False
                    printSummary(summaryOutput, timeStart, pathsToRun)
                    pool.close()
                    sys.exit()
            except StopIteration:
                continueIt = False
                pool.close()
                pool.join()
            except Exception as excp:  # pylint: disable=broad-except
                eventsProcessed += 1
                exceptionLog = ModuleResponse(
                    returnCode='UntrappedException',
                    moduleName=str(excp)
                )
                summaryOutput.append(exceptionLog)

    sys.stderr = normalStdError
    printSummary(summaryOutput, timeStart, pathsToRun)


def printSummary(summaryOutput, timeStart, pathsToRun):
    outStr = ''
    summaryOutputTwo = [i.fp for i in summaryOutput]
    for fp in pathsToRun:
        if fp not in summaryOutputTwo:
            failLog = ModuleResponse(returnCode='NoResult', fp=fp)
            summaryOutput.append(failLog)

    totalTests = 0

    skippedSummary = []
    successSummary = []
    errorsFoundSummary = []
    otherSummary = []
    for moduleResponse in summaryOutput:
        print(moduleResponse)
        if moduleResponse.returnCode == 'Skipped':
            skippedSummary.append(f'Skipped: {moduleResponse.fp}')
        elif moduleResponse.returnCode == 'NoResult':
            otherSummary.append(f'Silent test fail for {moduleResponse.fp}: Run separately!')
        elif moduleResponse.returnCode == 'UntrappedException':
            otherSummary.append(f'Untrapped Exception for unknown module: {moduleResponse.fp}')
        elif moduleResponse.returnCode == 'TrappedException':
            otherSummary.append('Trapped Exception for module %s, at %s: %s' %
                                (moduleResponse.moduleName,
                                  moduleResponse.fp,
                                  moduleResponse.testRunner))
        elif moduleResponse.returnCode == 'LargeException':
            otherSummary.append('Large Exception for file %s: %s' %
                                (moduleResponse.fp, moduleResponse.testResult))
        elif moduleResponse.returnCode == 'ImportError':
            otherSummary.append(f'Import Error for {moduleResponse.fp}')
        elif moduleResponse.returnCode == 'NotInTree':
            if moduleResponse.moduleName == '':
                otherSummary.append(f'Not in Tree Error: {moduleResponse.moduleName} ')
        elif moduleResponse.returnCode == 'TestsRun':
            totalTests += moduleResponse.testsRun
            if moduleResponse.success:
                successSummary.append('%s successfully ran %s tests in %s seconds'
                                      % (moduleResponse.moduleName,
                                         moduleResponse.testsRun,
                                         moduleResponse.runTime))
            else:
                errorsList = moduleResponse.errors
                # not the original errors list! see pickle note above
                failuresList = moduleResponse.failures
                errorsFoundSummary.append(
                    '\n-----------------------------\n'
                    + '%s had %s ERRORS and %s FAILURES in %s tests after %s seconds:\n' %
                    (moduleResponse.moduleName, len(errorsList),
                       len(failuresList), moduleResponse.testsRun, moduleResponse.runTime)
                    + '-----------------------------\n')

                for e in errorsList:
                    outStr += e + '\n'
                    errorsFoundSummary.append(str(e))
                for f in failuresList:
                    outStr += f + '\n'
                    errorsFoundSummary.append(str(f))
                # for e in errorsList:
                #     print(e[0], e[1])
                #     errorsFoundSummary.append('%s: %s' % (e[0], e[1]))
                # for f in failuresList:
                #     print(f[0], f[1])
                #     errorsFoundSummary.append('%s: %s' % (f[0], f[1]))
        else:
            otherSummary.append(f'Unknown return code {moduleResponse}')

    outStr += '\n\n---------------SUMMARY---------------------------------------------------\n'
    for line in skippedSummary:
        outStr += line + '\n'
    for line in successSummary:
        outStr += line + '\n'
    for line in otherSummary:
        outStr += line + '\n'
    for line in errorsFoundSummary:
        outStr += line + '\n'
    outStr += '-------------------------------------------------------------------------\n'
    elapsedTime = time.time() - timeStart
    outStr += f'Ran {totalTests} tests in {elapsedTime:.4f} seconds\n'
    sys.stdout.flush()
    print(outStr)
    sys.stdout.flush()

    import datetime
    import locale
    lastResults = os.path.join(environLocal.getRootTempDir(), 'lastResults.txt')
    with open(lastResults, 'w', encoding=locale.getdefaultencoding()) as f:
        f.write(outStr)
        f.write('Run at ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    print('Results at ' + lastResults)


if __name__ == '__main__':
    # mg = ModuleGather(useExtended=True)
    # mm = mg.getModuleWithoutImp('trecento.capua')
    # print(mm)
    mainPoolRunner()
