# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         multiprocesssTest.py
# Purpose:      Controller for all tests in music21 run concurrently.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012-13 Michael Scott Cuthbert and the music21 Project
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
import types
import unittest

import music21
from music21 import base
from music21 import common
from music21 import environment
_MOD = 'multiprocessTest.py'
environLocal = environment.Environment(_MOD)

ModuleResponse = collections.namedtuple('ModuleResponse', 'returnCode fp moduleName success testRunner errors failures testsRun runTime')
ModuleResponse.__new__.__defaults__ = (None,) * len(ModuleResponse._fields)
 
#-------------------------------------------------------------------------------
class ModuleGather(object):
    r'''
    Utility class for gathering and importing all modules in the music21
    package. Puts them in self.modulePaths.
    
    
    >>> from music21.test import testSingleCoreAll as testModule
    >>> mg = testModule.ModuleGather()
    >>> #_DOCS_SHOW print mg.modulePaths[0]
    D:\Web\eclipse\music21base\music21\xmlnode.py
    '''
    def __init__(self):
        self.dirParent = os.path.dirname(base.__file__)

        self.modulePaths = []
    
        self.moduleSkip = [
            'testSingleCoreAll.py', 
            'testExternal.py', 
            'testDefault.py', 
            'testInstallation.py', 
            'testLint.py', 
            'timeGraphImportStar.py',
            'testSerialization.py',
            'mptCurses.py',
            'memoryUsage.py',
            'dedent.py',
            
            'testPerformance.py',
            'multiprocessTest.py',
            'timeGraphs.py',
            'exceldiff.py', 
            'mrjobaws.py', # takes too long.
            'configure.py', # runs oddly...
            
            'vexflow/testShow.py',
            'vexflow/exporter.py',
            'trecento/quodJactatur.py',
            'trecento/find_vatican1790.py',
            'trecento/findSevs.py',
            'trecento/correlations.py',
            'trecento/contenanceAngloise.py',
            'trecento/capuaProbabilities.py',
            'theoryAnalysis/wwnortonMGTA.py',
            'test/treeYield.py',
            'test/toggleDebug.py',
            
            'musicxml/testPrimitive.py',
            'musicxml/testFiles.py',
            'musedata/testPrimitive/test01/__init__.py',
            'musedata/testPrimitive/__init__.py',
            'mei/test_base.py',
            'humdrum/questions.py',
            'humdrum/canonicalOutput.py',
            'documentation/upload.py',
            'documentation/source/conf.py',
            'documentation/library/extensions.py',
            'documentation/make.py',
            'corpus/testCorpus.py',
            'composition/seeger.py',
            'composition/aug30.py',
            'audioSearch/scores/__init__.py',
            'audioSearch/scoreFollower.py',
            'audioSearch/repetitionGame.py',
            'audioSearch/omrfollow.py',
            'audioSearch/humanVScomputer.py',
            'audioSearch/graphicalInterfaceTranscriber.py',
            'audioSearch/graphicalInterfaceSF.py',
            'audioSearch/graphicalInterfaceGame.py',
            'analysis/phrasing.py',
            'abcFormat/testFiles.py',
            ]
        # skip any path that starts with this string
        self.pathSkip = ['obsolete', 'ext', 'server', 'demos']
        self.slowModules = ['graph', 'figuredBass/realizer', 
                            'features/jSymbolic', 'features/native', 'figuredBass/examples', 
                            'braille/test', 'test/testStream', 'analysis/windowed', 
                            'converter/__init__', 'metadata/bundles', 'musicxml/fromMxObjects',
                            'romanText/translate', 'musicxml/m21ToString', 'theoryAnalysis/theoryAnalyzer']
        # search on init
        self._walk()

    def _visitFunc(self, args, dirname, names):
        '''
        append all module paths from _walk() to self.modulePaths.
        Utility function was called from os.path.walk() now called from os.walk
        '''
        for fileName in names:
            if fileName.endswith('py'):
                fp = os.path.join(dirname, fileName)
                if not os.path.isdir(fp):
                    self.modulePaths.append(fp)

    def _walk(self):
        '''
        Get all the modules in reverse order, storing them in self.modulePaths
        '''
        def manyCoreSortFunc(name):
            '''
            for many core systems, like the MacPro, running slowest modules first
            helps there be fewer idle cores later 
            '''
            name = name[len(self.dirParent) + 1:]
            name = name.replace('.py', '')
            return (name in self.slowModules, name)
        
        # the results of this are stored in self.curFiles, self.dirList        
        for dirpath, unused_dirnames, filenames in os.walk(self.dirParent):
            self._visitFunc(None, dirpath, filenames)
        if multiprocessing.cpu_count() > 4:# @UndefinedVariable
            self.modulePaths.sort(key=manyCoreSortFunc)
        else:
            self.modulePaths.sort()
        self.modulePaths.reverse()
        

    def _getName(self, fp):
        r'''
        Given full file path, find a name for the module with : as the separator.
        
        >>> from music21.test import testSingleCoreAll as testModule
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
        Given full file path, find a name for the module with . as the separator.
        
        >>> from music21.test import testSingleCoreAll as testModule
        >>> mg = testModule.ModuleGather()
        >>> #_DOCS_SHOW mg._getName(r'D:\Web\eclipse\music21base\music21\trecento\findSevs.py')
        'trecento.findSevs'
        '''
        fn = fp.replace(self.dirParent, '') # remove parent
        parts = [x for x in fn.split(os.sep) if x]
        if parts[-1] == '__init__.py':
            parts.pop()
        fn = '.'.join(parts) # replace w/ period
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
            dirSkipSlash = os.sep + dirSkip + os.sep
            if dirSkipSlash in fp:
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
                    return "notInTree"
            else:
                return "notInTree"
        mod = currentModule
        
        if restoreEnvironmentDefaults:
            if hasattr(mod, 'environLocal'):
                mod.environLocal.restoreDefaults()
        print('starting ' + moduleName)
        return mod

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
        globs = __import__('music21').__dict__.copy()
        docTestOptions = (doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
        s1 = doctest.DocTestSuite(
            globs=globs,
            optionflags=docTestOptions,
            )
        
        # get Test classes in moduleObject
        if not hasattr(moduleObject, 'Test'):
            environLocal.printDebug('%s has no Test class' % moduleObject)
        else:
            s1.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(moduleObject.Test))
        try:
            globs = __import__('music21').__dict__.copy()
            s3 = doctest.DocTestSuite(moduleObject,
                globs=globs,
                optionflags=docTestOptions,
                )
            s1.addTests(s3)
        except ValueError:
            environLocal.printDebug('%s cannot load Doctests' % moduleObject)
            pass        

        common.fixTestsForPy2and3(s1)
        
        
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
        except Exception as excp:
            environLocal.printDebug('*** Exception in running %s: %s...\n' % (moduleName, excp))
            return ModuleResponse("TrappedException", fp, moduleName, None, str(excp))
    except Exception as excp:
        environLocal.printDebug('*** Large Exception in running %s: %s...\n' % (fp, excp))
        return ModuleResponse("LargeException", fp, None, None, str(excp))

    
def mainPoolRunner(testGroup=['test'], restoreEnvironmentDefaults=False, leaveOut = 1):
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
    

    modGather = ModuleGather()

    maxTimeout = 200
    pathsToRun = modGather.modulePaths # [0:30]

    pool = multiprocessing.Pool(processes=poolSize) # @UndefinedVariable
    
    # imap returns the results as they are completed.  Since the number of files is small,
    # the overhead of returning is outweighed by the positive aspect of getting results immediately
    # unordered says that results can RETURN in any order; not that they'd be pooled out in any
    # order.
    res = pool.imap_unordered(runOneModuleWithoutImp, ((modGather, fp) for fp in pathsToRun))

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
        except Exception as excp:
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
    #mg = ModuleGather()
    #mm = mg.getModuleWithoutImp('trecento.capua')
    #print mm
    mainPoolRunner()
