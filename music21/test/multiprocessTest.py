# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         multiprocesssTest.py
# Purpose:      Controller for all tests in music21 run concurrently.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
multiprocess testing...
'''
import multiprocessing
import time

import unittest, doctest
import os, imp, sys

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
        Given full file path, find a name for the the module
        
        >>> from music21.test import test as testModule
        >>> mg = testModule.ModuleGather()
        >>> #_DOCS_SHOW mg._getName(r'D:\Web\eclipse\music21base\music21\xmlnode.py')
        'xmlnode'
        '''
        fn = fp.replace(self.dirParent, '') # remove parent
        if fn.startswith(os.sep):
            fn = fn[1:]
        fn = fn.replace(os.sep, ':') # replace w/ dots
        fn = fn.replace('.py', '')
        return fn
     
    def load(self, restoreEnvironmentDefaults=False):
        '''
        Return a list of module objects that are not in the skip list.
        
        N.B. the list is a list of actual module objects not names,
        therefore cannot be pickled.
        '''
        modules = []
        for fp in self.modulePaths:
            moduleObject = self.getModule(fp, restoreEnvironmentDefaults)
            if moduleObject is not None:
                modules.append(moduleObject)
        return modules

    def getModule(self, fp, restoreEnvironmentDefaults = False):
        '''
        gets one module object from the file path
        '''
        skip = False
        for fnSkip in self.moduleSkip:
            if fp.endswith(fnSkip):
                skip = True
                break
        if skip:
            return None
        for dirSkip in self.pathSkip:
            if dirSkip in fp:
                skip = True  
                break
        if skip:
            return None
        name = self._getName(fp)
        try:
            mod = imp.load_source(name, fp) 
        except Exception as excp: # this takes all exceptions!
            environLocal.printDebug(['failed import:', fp, '\n', 
                '\tEXCEPTION:', str(excp).strip()])
            return None
        if restoreEnvironmentDefaults:
            if hasattr(mod, 'environLocal'):
                mod.environLocal.restoreDefaults()
        return mod


                 


class Consumer(multiprocessing.Process):
    
    def __init__(self, task_queue, result_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue   = task_queue
        self.result_queue = result_queue

    def run(self):
        proc_name = self.name
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means we should exit
                #print '%s: Exiting' % proc_name
                break
            #print '%s: %s' % (proc_name, next_task)
            environLocal.printDebug("Next task: %s" % next_task.fp)
            answer = next_task()
            self.result_queue.put(answer)
        self.terminate()
        return



class Task(object):
    def __init__(self, modGath, fp):
        self.modGath = modGath
        self.fp = fp

    def __call__(self):
        verbosity = False
        moduleObject = self.modGath.getModule(self.fp)
        environLocal.printDebug('running %s \n' % self.fp)
        if moduleObject is None:
            environLocal.printDebug('%s is skipped \n' % self.fp)
            return (None, None)
        moduleName = self.modGath._getName(self.fp)
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
        testResult = runner.run(s1)  
        return (moduleName, testResult)
    
    def __str__(self):
        return '%s * %s' % (self.a, self.b)

class DummyTask(object):
    fp = "Dummy"
    
    def __call__(self):
        time.sleep(.1)
        return (None, "dummy")

class StdErrHolder(object):
    def __init__(self):
        self.log = []
    
    def write(self, s):
        self.log.append(s)

def mainQueueRunner(testGroup=['test'], restoreEnvironmentDefaults=False):
    '''Run all tests. Group can be test and external

    >>> print(None)
    None
    '''    

#    oldStderr = sys.stderr
#    sys.stderr = StdErrHolder()

    # Establish communication queues
    tasks   = multiprocessing.Queue()
    results = multiprocessing.Queue()
    
    timeStart = time.time()
    # Start consumers
    num_consumers = multiprocessing.cpu_count()
    print 'Creating %d processes for multiprocessing' % num_consumers
    consumers = [ Consumer(tasks, results)
                  for i in xrange(num_consumers) ]
    for w in consumers:
        w.start()
    
    modGather = ModuleGather()

    environLocal.printDebug('looking for Test classes...\n')
    # look over each module and gather doc tests and unittests


    ## add tasks
    num_jobs = 0
    for fp in modGather.modulePaths:
        num_jobs += 1
        tasks.put(Task(modGather, fp))
    for i in range(10):
        num_jobs += 1
        tasks.put(DummyTask())
    
    #NO # Add a poison pill for each consumer
    #for i in xrange(num_consumers):
    #    tasks.put(None)
    
    # Start printing results
    summaryOutput = []
    totalTests = 0
    totalDummy = 0
    while (results.empty() is False and tasks.empty() is False):
        num_jobs -= 1    
        try:
            #print "trying to get... %d" % num_jobs
            (moduleName, textTestResult) = results.get()
        except Exception as exc:
            errorMsg = 'failed on get! %s' % exc
            environLocal.printDebug(errorMsg)
            summaryOutput.append(errorMsg)
            (moduleName, textTestResult) = (None, None)
        if moduleName is not None:
            eCount = 0
            fCount = 0
            print '%d: %s: %s' % (num_jobs, moduleName, textTestResult)
            summaryOutput.append('%s: %s' % (moduleName, textTestResult))
            for e in textTestResult.errors:
                print e[0], e[1]
                summaryOutput.append('%s: %s' % (e[0], e[1]))
            for f in textTestResult.failures:
                print f[0], f[1]
                summaryOutput.append('%s: %s' % (f[0], f[1]))
            totalTests += textTestResult.testsRun
            #print "got! %d" % num_jobs
            sys.stdout.flush()
        sys.stderr.flush()


    #for errMsg in sys.stderr.log:
    #    print errMsg
        
    timeEnd = time.time()
    elapsedTime = timeEnd - timeStart

    print "\n\n---------------SUMMARY---------------------------------------------------"
    for l in summaryOutput:
        print l
    print "-------------------------------------------------------------------------"
    print "Ran %d tests in %.4f seconds" % (totalTests, elapsedTime)
    print "\n\n(waiting for subprocesses to terminate...can take a few seconds)"
    sys.stdout.flush()


    for w in consumers:
        w.terminate()


#    sys.stderr = oldStderr

if __name__ == '__main__':
    mainQueueRunner()
