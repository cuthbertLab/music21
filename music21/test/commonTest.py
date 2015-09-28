# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         commonTest.py
# Purpose:      Things common to testing
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-15 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Things that are common to testing...
'''
import doctest
import imp
import multiprocessing
import os
import types
import warnings

import music21
from music21 import common
from music21 import environment
from music21.test import testRunner

_MOD = 'commonTest.py'
environLocal = environment.Environment(_MOD)

def defaultDoctestSuite(name=None):
    globs = __import__('music21').__dict__.copy()
    docTestOptions = (doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    kwArgs = {
              'globs': globs,
              'optionflags': docTestOptions,
              'checker': testRunner.Py3In2OutputChecker()              
              }
    # in case there are any tests here, get a suite to load up later
    if name is not None:
        s1 = doctest.DocTestSuite(name, **kwArgs)
    else:
        s1 = doctest.DocTestSuite(**kwArgs)
    return s1

#-------------------------------------------------------------------------------
class ModuleGather(object):
    r'''
    Utility class for gathering and importing all modules in the music21
    package. Puts them in self.modulePaths.
    
    >>> from music21.test import commonTest
    >>> mg = commonTest.ModuleGather(useExtended=True)
    >>> #_DOCS_SHOW print mg.modulePaths[0]
    D:\Web\eclipse\music21base\music21\xmlnode.py
    '''
    def __init__(self, useExtended=False):
        self.dirParent = common.getSourceFilePath()
        self.useExtended = useExtended
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
            'figuredBass/examples.py', # 40 seconds and runs fine
            ]
        
        self.moduleSkipExtended = self.moduleSkip + [
            'exceldiff.py', 
            'mrjobaws.py', # takes too long.
            'configure.py', # runs oddly...
                                                     
            'timeGraphImportStar.py',
            'testSerialization.py',
            'mptCurses.py',
            'memoryUsage.py',
            'dedent.py',
            
            'testPerformance.py',
            'multiprocessTest.py',
            'timeGraphs.py',
            
            'alpha/trecento/quodJactatur.py',
            'alpha/trecento/find_vatican1790.py',
            'alpha/trecento/findSevs.py',
            'alpha/trecento/correlations.py',
            'alpha/trecento/contenanceAngloise.py',
            'alpha/trecento/capuaProbabilities.py',
            'alpha/theoryAnalysis/wwnortonMGTA.py',
            'test/treeYield.py',
            'test/toggleDebug.py',
            
            'musicxml/testPrimitive.py',
            'musicxml/testFiles.py',
            'musedata/testPrimitive/test01/__init__.py',
            'musedata/testPrimitive/__init__.py',
            'mei/test_base.py',
            'humdrum/questions.py',
            
            'documentation/upload.py',
            'documentation/source/conf.py',
            'documentation/extensions.py',

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
        # run these first...
        self.slowModules = ['graph', 
                            'figuredBass/realizer', 
                            'features/jSymbolic', 
                            'features/native', 
                            'figuredBass/examples', 
                            'braille/test', 
                            'test/testStream', 
                            'analysis/windowed', 
                            'converter/__init__', 
                            'metadata/bundles', 
                            
                            'musicxml/m21ToXml',
                            'musicxml/xmlToM21', 

                            'musicxml/fromMxObjects',
                            'musicxml/m21ToString', 

                            'romanText/translate', 
                            'alpha/theoryAnalysis/theoryAnalyzer',
                            ]

        
        # skip any path that contains this string
        self.pathSkip = ['obsolete', 
                         'ext', 
                         'alpha/webapps/server', 
                         'alpha/webapps/archive',
                         ]
        self.pathSkipExtended = self.pathSkip + [
                         'demos',                                                 
                        ]
        
        self.moduleSkip = [x.replace('/', os.sep) for x in self.moduleSkip]
        self.moduleSkipExtended = [x.replace('/', os.sep) for x in self.moduleSkipExtended]
        self.pathSkip = [x.replace('/', os.sep) for x in self.pathSkip]
        self.pathSkipExtended = [x.replace('/', os.sep) for x in self.pathSkipExtended]
        self.slowModules = [x.replace('/', os.sep) for x in self.slowModules]

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

        #for p in self.modulePaths:
        #    print p# self.modulePaths
        self.modulePaths.reverse()

    def _getName(self, fp):
        r'''
        Given full file path, find a name for the module with _ as the separator.
        
        >>> from music21.test import commonTest
        >>> mg = commonTest.ModuleGather()
        >>> #_DOCS_SHOW mg._getName(r'D:\Web\eclipse\music21base\music21\chord.py')
        'chord'
        '''
        fn = fp.replace(self.dirParent, '') # remove parent
        if fn.startswith(os.sep):
            fn = fn[1:]
        fn = fn.replace(os.sep, '_') # replace w/ _
        fn = fn.replace('.py', '')
        return fn

    def _getNamePeriod(self, fp):
        r'''
        Given full file path, find a name for the module with . as the separator.
        
        >>> from music21.test import commonTest
        >>> mg = commonTest.ModuleGather()
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
        ms = self.moduleSkip
        if self.useExtended:
            ms = self.moduleSkipExtended
        
        for fnSkip in ms:
            if fp.endswith(fnSkip):
                skip = True
                break
        if skip:
            return None

        ps = self.pathSkip
        if self.useExtended:
            ps = self.pathSkipExtended

        
        for dirSkip in ps:
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



if __name__ == '__main__':
    music21.mainTest()
