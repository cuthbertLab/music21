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
import imp
import os 
import sys
import unittest
import warnings

from music21 import base
from music21 import common
from music21 import environment
from music21.ext import six

_MOD = 'test.py'
environLocal = environment.Environment(_MOD)

if six.PY2:
    try:
        import coverage
        cov = coverage.coverage(omit=[
            '*/ext/*',
            'dist/dist.py',
            'installer.py',
            '*/documentation/upload.py',
            '*/documentation/make.py',
#            '*/test/*',
#            '*/demos/*',  # maybe remove someday...
            'music21/configure.py',
            '*/figuredBass/examples.py',
            '*/trecento/tonality.py'
            ])
        exclude_lines=[
            '\s*import music21\s*',
            '\s*music21.mainTest\(\)\s*',
            ]
        for e in exclude_lines:
            cov.exclude(e, which='exclude')
        cov.start()
    except ImportError:
        cov = None
else:
    cov = None # coverage is extremely slow on Python 3.4 for some reason
        # in any case we only need to run it once.

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
            'testPerformance.py',
            'timeGraphs.py',
            'exceldiff.py', 
            'multiprocessTest.py',
            'figuredBass' + os.sep + 'examples.py', # 40 seconds and runs fine
            'trecento' + os.sep + 'tonality.py'
            ]
        # skip any path that contains this string
        self.pathSkip = ['obsolete', 'xlrd', 'jsonpickle', 'ext', 'webapps' + os.sep + 'server', 
                         'webapps' + os.sep + 'archive']
        # search on init
        self._walk()

    def _visitFunc(self, args, dirname, names):
        '''
        append all module paths from _walk() to self.modulePaths.
        Utility function called from os.walk()
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
        # the results of this are stored in self.curFiles, self.dirList
        for dirpath, unused_dirnames, filenames in os.walk(self.dirParent):
            self._visitFunc(None, dirpath, filenames)
        self.modulePaths.sort()
        #for p in self.modulePaths:
        #    print p# self.modulePaths
        self.modulePaths.reverse()

    def _getName(self, fp):
        r'''
        Given full file path, find a name for the module
        
        >>> from music21.test import testSingleCoreAll as testModule
        >>> mg = testModule.ModuleGather()
        >>> #_DOCS_SHOW mg._getName(r'D:\Web\eclipse\music21base\music21\xmlnode.py')
        'xmlnode'
        '''
        fn = fp.replace(self.dirParent, '') # remove parent
        parts = [x for x in fn.split(os.sep) if x]
        if parts[-1] == '__init__.py':
            parts.pop()
        fn = '.'.join(parts)
        #fn = fn.replace(os.sep, ':') # replace w/ dots
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
        #print(name, os.path.dirname(fp))
        #fmFile, fmPathname, fmDescription = imp.find_module(name, os.path.dirname(fp) + os.sep)
        try:
            #environLocal.printDebug(['import:', fp]) 
            #mod = imp.load_module(name, fmFile, fmPathname, fmDescription)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                mod = imp.load_source(name, fp)
        except Exception as excp: # this takes all exceptions!
            environLocal.printDebug(['failed import:', fp, '\n', 
                '\tEXCEPTION:', str(excp).strip()])
            return None
        if restoreEnvironmentDefaults:
            if hasattr(mod, 'environLocal'):
                mod.environLocal.restoreDefaults()
        return mod






def main(testGroup=['test'], restoreEnvironmentDefaults=False, limit=None):
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

    modGather = ModuleGather()
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
        common.addDocAttrTestsToSuite(s1, allLocals, outerFilename=module.__file__, globs=globs, optionflags=docTestOptions)
    
    common.fixTestsForPy2and3(s1)
    
    environLocal.printDebug('running Tests...\n')
            
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)  # import modules...
        runner = unittest.TextTestRunner(verbosity=verbosity)
        finalTestResults = runner.run(s1)  
    
    if cov is not None:
        cov.stop()
        cov.save()
    
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
    except:
        pass # no need in Python3

    # if optional command line arguments are given, assume they are  
    # test group arguments
    if len(sys.argv) >= 2:
        main(sys.argv[1:])
    else:
        main()


#------------------------------------------------------------------------------
# eof

