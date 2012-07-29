# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         multiprocesssTest.py
# Purpose:      Controller for all tests in music21 run concurrently.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Multiprocess testing.  Tests all doctests and Test unittest objects in all
modules that are imported when running "import music21".  Runs threads on
each core of a multicore system.

N.B. this gets a slightly different set of modules than test/test.py does
because the `imp` module is not available for threaded processing.  Running
both modules gives a great coverage.

Run test/testDocumentation after this.
'''
from Queue import Empty as EmptyQueueException
import multiprocessing
import time

import unittest, doctest
import os, sys
import types

import music21
from music21 import base
from music21 import common
from music21 import environment
_MOD = 'multip.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class ModuleGather(object):
    r'''
    Utility class for gathering and importing all modules in the music21
    package. Puts them in self.modulePaths.
    
    
    >>> from music21.test import test as testModule
    >>> mg = testModule.ModuleGather()
    >>> #_DOCS_SHOW print mg.modulePaths[0]
    D:\Web\eclipse\music21base\music21\xmlnode.py
    '''
    def __init__(self):
        self.dirParent = os.path.dirname(base.__file__)

        self.modulePaths = []
    
        self.moduleSkip = [
            'test.py', 
            'testExternal.py', 
            'testDefault.py', 
            'testInstallation.py', 
            'testLint.py', 
            'testPerformance.py',
            'multiprocessTest.py',
            '__init__.py', 
            'timeGraphs.py',
            'exceldiff.py', 
            'mrjobaws.py', # takes too long.
            'configure.py', # runs oddly...
            ]
        # skip any path that contains this string
        self.pathSkip = ['abj', 'obsolete', 'xlrd', 'jsonpickle', 'ext', 'server', 'mrjobaws']
        # search on init
        self._walk()

    def _visitFunc(self, args, dirname, names):
        '''
        append all module paths from _walk() to self.modulePaths.
        Utility function called from os.path.walk()
        '''
        for file in names:
            if file.endswith('py'):
                fp = os.path.join(dirname, file)
                if not os.path.isdir(fp):
                    self.modulePaths.append(fp)

    def _walk(self):
        '''
        Get all the modules in reverse order, storing them in self.modulePaths
        '''
        # the results of this are stored in self.curFiles, self.dirList
        os.path.walk(self.dirParent, self._visitFunc, '')
        self.modulePaths.sort()
        self.modulePaths.reverse()

    def _getName(self, fp):
        r'''
        Given full file path, find a name for the the module with : as the separator.
        
        >>> from music21.test import test as testModule
        >>> mg = testModule.ModuleGather()
        >>> #_DOCS_SHOW mg._getName(r'D:\Web\eclipse\music21base\music21\xmlnode.py')
        'xmlnode'
        '''
        fn = fp.replace(self.dirParent, '') # remove parent
        if fn.startswith(os.sep):
            fn = fn[1:]
        fn = fn.replace(os.sep, '_') # replace w/ colon
        fn = fn.replace('.py', '')
        return fn

    def _getNamePeriod(self, fp):
        r'''
        Given full file path, find a name for the the module with . as the separator.
        
        >>> from music21.test import test as testModule
        >>> mg = testModule.ModuleGather()
        >>> #_DOCS_SHOW mg._getName(r'D:\Web\eclipse\music21base\music21\trecento\findSevs.py')
        'trecento.findSevs'
        '''
        fn = fp.replace(self.dirParent, '') # remove parent
        if fn.startswith(os.sep):
            fn = fn[1:]
        fn = fn.replace(os.sep, '.') # replace w/ period
        fn = fn.replace('.py', '')
        return fn
     

    def getModuleWithoutImp(self, fp, restoreEnvironmentDefaults = False):
        '''
        gets one module object from the file path without using Imp
        '''
        skip = False
        for fnSkip in self.moduleSkip:
            if fp.endswith(fnSkip):
                skip = True
                break
        if skip:
            return "skip"
        for dirSkip in self.pathSkip:
            if dirSkip in fp:
                skip = True  
                break
        if skip:
            return "skip"
        moduleName = self._getNamePeriod(fp)
        moduleNames = moduleName.split('.')
        currentModule = music21
        for thisName in moduleNames:
            if hasattr(currentModule, thisName):
                currentModule = object.__getattribute__(currentModule, thisName)
                if not isinstance(currentModule, types.ModuleType):
                    return "fail"
            else:
                return "fail"
        mod = currentModule
        
        if restoreEnvironmentDefaults:
            if hasattr(mod, 'environLocal'):
                mod.environLocal.restoreDefaults()
        return mod



def multime(multinum):
    sleeptime = multinum[0]/100.0
    if multinum[0] == 90:
        raise Exception("Ha! 90!") 
    print multinum, sleeptime
    sys.stdout.flush()
    time.sleep(sleeptime)
    x = multinum[0] * multinum[1]
    return (x, multinum[0])

def examplePoolRunner(testGroup=['test'], restoreEnvironmentDefaults=False):
    '''
    demo of a pool runner with failures and successes...
    '''
    poolSize = 2 #multiprocessing.cpu_count()
    print 'Creating %d processes for multiprocessing' % poolSize
    pool = multiprocessing.Pool(processes=poolSize)

    storage = []
    
    numbers = [50, 20, 10, 5, 700, 90]
    res = pool.imap_unordered(multime, ((i,10) for i in numbers))
    continueIt = True
    timeouts = 0
    eventsProcessed = 0
    while continueIt is True:
        try:
            newResult = res.next(timeout=1)
            print newResult
            timeouts = 0
            eventsProcessed += 1
            storage.append(newResult)
        except multiprocessing.TimeoutError:
            timeouts += 1
            print "TIMEOUT!"
            if timeouts > 3 and eventsProcessed > 0:
                print "Giving up..."
                continueIt = False
                pool.close()
                pool.join()
        except StopIteration:
            continueIt = False
            pool.close()    
            pool.join()
        except Exception as excp:
            exceptionLog = ("UntrappedException", "%s" % excp)
            storage.append(exceptionLog)

    storageTwo = [i[1] for i in storage]
    for x in numbers:
        if x not in storageTwo:
            failLog = ("Fail", x)
            storage.append(failLog)
    print storage

def runOneModuleWithoutImp(args):
    modGath = args[0] # modGather object
    fp = args[1]
    verbosity = False
    moduleObject = modGath.getModuleWithoutImp(fp)
    environLocal.printDebug('running %s \n' % fp)
    if moduleObject == 'skip':
        environLocal.printDebug('%s is skipped \n' % fp)
        return ("Skipped", fp)
    elif moduleObject == 'fail':
        environLocal.printDebug('%s is in the music21 directory but not imported in music21. Skipped -- fix! \n' % fp)
        return ("NotInTree", fp, '%s is in the music21 directory but not imported in music21. Skipped -- fix!' % modGath._getNamePeriod(fp))

    
    try:
        moduleName = modGath._getName(fp)
        docTestOptions = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    
        
        s1 = doctest.DocTestSuite(optionflags=docTestOptions)
    
        
        # get Test classes in moduleObject
        if not hasattr(moduleObject, 'Test'):
            environLocal.printDebug('%s has no Test class' % moduleObject)
        else:
            s1.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(moduleObject.Test))
        try:
            s3 = doctest.DocTestSuite(moduleObject, optionflags=docTestOptions)
            s1.addTests(s3)
        except ValueError:
            environLocal.printDebug('%s cannot load Doctests' % moduleObject)
            pass        
        environLocal.printDebug('running Tests...\n')
        runner = unittest.TextTestRunner(verbosity=verbosity)
        try:
            testResult = runner.run(s1)  
            
            # need to make testResult pickleable by removing the instancemethod parts...
            trE = []
            for e in testResult.errors:
                trE.append(e[1])
            trF = []
            for f in testResult.failures:
                trF.append(f[1])
            testResult.errors = trE
            testResult.failures = trF
            return ("TestsRun", fp, moduleName, testResult)
        except Exception as excp:
            environLocal.printDebug('*** Exception in running %s: %s...\n' % (moduleName, excp))
            return ("TrappedException", fp, moduleName, str(excp))
    except Exception as excp:
        environLocal.printDebug('*** Large Exception in running %s: %s...\n' % (fp, excp))
        return ("LargeException", fp, str(excp))

    
def mainPoolRunner(testGroup=['test'], restoreEnvironmentDefaults=False):
    '''Run all tests. Group can be test and external
    '''    
    
    timeStart = time.time()
    poolSize = multiprocessing.cpu_count()
    print 'Creating %d processes for multiprocessing' % poolSize
    

    modGather = ModuleGather()

    maxTimeout = 120
    pathsToRun = modGather.modulePaths

    pool = multiprocessing.Pool(processes=poolSize)
    res = pool.imap_unordered(runOneModuleWithoutImp, ((modGather,fp) for fp in pathsToRun))

    continueIt = True
    timeouts = 0
    eventsProcessed = 0
    summaryOutput = []
    
    while continueIt is True:
        try:
            newResult = res.next(timeout=1)
            if timeouts >= 5:
                print ""
            print newResult
            timeouts = 0
            eventsProcessed += 1
            summaryOutput.append(newResult)
        except multiprocessing.TimeoutError:
            timeouts += 1
            if timeouts == 5 and eventsProcessed > 0:
                print "Delay in processing, seconds: ",
            elif timeouts == 5:
                print "Starting first modules, should take 5-10 seconds: ",
            if timeouts % 5 == 0:
                print str(timeouts) + " ",
            if timeouts > maxTimeout and eventsProcessed > 0:
                print "\nToo many delays, giving up..."
                continueIt = False
                printSummary(summaryOutput, timeStart, pathsToRun)
                pool.close()
                exit()
        except StopIteration:
            continueIt = False
            pool.close()    
            pool.join()
        except Exception as excp:
            eventsProcessed += 1
            exceptionLog = ("UntrappedException", "%s" % excp)
            summaryOutput.append(exceptionLog)

    #print summaryOutput

    printSummary(summaryOutput, timeStart, pathsToRun)

def printSummary(summaryOutput, timeStart, pathsToRun):

    summaryOutputTwo = [i[1] for i in summaryOutput]
    for fp in pathsToRun:
        if fp not in summaryOutputTwo:
            failLog = ("NoResult", fp)
            summaryOutput.append(failLog)

    totalTests = 0

    skippedSummary = []
    successSummary = []
    errorsFoundSummary = []
    otherSummary = []
    for l in summaryOutput:
        (returnCode, fp) = (l[0], l[1])
        if returnCode == 'Skipped':
            skippedSummary.append("Skipped: %s" % fp)
        elif returnCode == 'NoResult':
            otherSummary.append("Silent test fail for %s: Run separately!" % fp)
        elif returnCode == 'UntrappedException':
            otherSummary.append("Untrapped Exception for unknown module: %s" % fp)
        elif returnCode == 'TrappedException':
            (moduleName, excp) = (l[2], l[3])
            otherSummary.append("Trapped Exception for module %s, at %s: %s" % (moduleName, fp, excp))
        elif returnCode == 'LargeException':
            excp = l[2]
            otherSummary.append("Large Exception for file %s: %s" % (fp, excp))
        elif returnCode == 'ImportError':
            otherSummary.append("Import Error for %s" % fp)
        elif returnCode == 'NotInTree':
            otherSummary.append("Not in Tree Error: %s " % l[2]) 
        elif returnCode == 'TestsRun':
            (moduleName, textTestResultObj) = (l[2], l[3])
            testsRun = textTestResultObj.testsRun
            totalTests += testsRun
            if textTestResultObj.wasSuccessful():
                successSummary.append("%s successfully ran %d tests" % (moduleName, testsRun))
            else:
                errorsList = textTestResultObj.errors # not the original errors list! see pickle note above
                failuresList = textTestResultObj.failures
                errorsFoundSummary.append("\n-----------\n%s had %d ERRORS and %d FAILURES in %d tests:" %(moduleName, len(errorsList), len(failuresList), testsRun))

                for e in errorsList:
                    print e
                    errorsFoundSummary.append('%s' % (e))
                for f in failuresList:
                    print f
                    errorsFoundSummary.append('%s' % (f))
#                for e in errorsList:
#                    print e[0], e[1]
#                    errorsFoundSummary.append('%s: %s' % (e[0], e[1]))
#                for f in failuresList:
#                    print f[0], f[1]
#                    errorsFoundSummary.append('%s: %s' % (f[0], f[1]))    
        else:
            otherSummary.append("Unknown return code %s" % l)


    print "\n\n---------------SUMMARY---------------------------------------------------"
    for l in skippedSummary:
        print l
    for l in successSummary:
        print l
    for l in otherSummary:
        print l
    for l in errorsFoundSummary:
        print l
    print "-------------------------------------------------------------------------"
    elapsedTime = time.time() - timeStart
    print "Ran %d tests in %.4f seconds" % (totalTests, elapsedTime)
    sys.stdout.flush()


if __name__ == '__main__':
    #mg = ModuleGather()
    #mm = mg.getModuleWithoutImp('trecento.capua')
    #print mm
    mainPoolRunner()
