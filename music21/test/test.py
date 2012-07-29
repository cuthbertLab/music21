# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         test.py
# Purpose:      Controller for all module tests in music21.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Controller to run all module tests in the music21 folders.

Runs great, but slowly on multiprocessor systems.
'''



import unittest, doctest
import os, imp, sys



from music21 import base
from music21 import common
from music21 import environment
_MOD = 'test.py'
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
            '__init__.py', 
            'timeGraphs.py',
            'exceldiff.py', 
            # not testing translate due to dependency
            'abj/translate.py', 
            'multiprocessTest.py',
            ]
        # skip any path that contains this string
        self.pathSkip = ['obsolete', 'xlrd', 'jsonpickle', 'ext', 'webapps/server']
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
            #environLocal.printDebug(['import:', fp]) 
            mod = imp.load_source(name, fp)
        except Exception as excp: # this takes all exceptions!
            environLocal.printDebug(['failed import:', fp, '\n', 
                '\tEXCEPTION:', str(excp).strip()])
            return None
        if restoreEnvironmentDefaults:
            if hasattr(mod, 'environLocal'):
                mod.environLocal.restoreDefaults()
        return mod






def main(testGroup=['test'], restoreEnvironmentDefaults=False):
    '''Run all tests. Group can be test and external

    >>> print(None)
    None
    '''    
    docTestOptions = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    # in case there are any tests here, get a suite to load up later
    s1 = doctest.DocTestSuite(__name__, optionflags=docTestOptions)

    modGather = ModuleGather()
    modules = modGather.load(restoreEnvironmentDefaults)

    verbosity = 2
    if 'verbose' in sys.argv:
        verbosity = 1 # this seems to hide most display

    environLocal.printDebug('looking for Test classes...\n')
    # look over each module and gather doc tests and unittests
    for module in common.sortModules(modules):
        unitTestCases = []
    
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
            s3 = doctest.DocTestSuite(module, optionflags=docTestOptions)
            s1.addTests(s3)
        except ValueError:
            environLocal.printDebug('%s cannot load Doctests' % module)
            continue
    
    environLocal.printDebug('running Tests...\n')
    runner = unittest.TextTestRunner(verbosity=verbosity)
    testResult = runner.run(s1)  

    # this should work but requires python 2.7 and the testRunner arg does not
    # seem to work properly
    #unittest.main(testRunner=runner, failfast=True)
                 

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    import sys
    reload(sys)
    sys.setdefaultencoding("UTF-8")

    # if optional command line args are given, assume they are  
    # test group arguments
    if len(sys.argv) >= 2:
        main(sys.argv[1:])
    else:
        main()


#------------------------------------------------------------------------------
# eof

