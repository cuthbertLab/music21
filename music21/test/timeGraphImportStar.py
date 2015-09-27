# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:          timeGraphImportStar.py
# Purpose:       test the time to run "from music21 import *"
#
# Authors:       Michael Scott Cuthbert
#                Christopher Ariza
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------


# script to create a graph to time how fast some things are happening...
# generates pretty graphs showing what the bottlenecks in the system are, for helping to
# improve them.  Requires pycallgraph (not included with music21).  

import pycallgraph
import time

# this class is duplicated from common.py in order to avoid 
# import the module for clean testing
class Timer(object):
    """An object for timing."""
        
    def __init__(self):
        # start on init
        self._tStart = time.time()
        self._tDif = 0
        self._tStop = None

    def start(self):
        '''Explicit start method; will clear previous values. Start always happens on initialization.'''
        self._tStart = time.time()
        self._tStop = None # show that a new run has started so __call__ works
        self._tDif = 0
    
    def stop(self):
        self._tStop = time.time()
        self._tDif = self._tStop - self._tStart

    def clear(self):
        self._tStop = None
        self._tDif = 0
        self._tStart = None

    def __call__(self):
        '''Reports current time or, if stopped, stopped time.
        '''
        # if stopped, gets _tDif; if not stopped, gets current time
        if self._tStop == None: # if not stoped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return t 

    def __str__(self):
        if self._tStop == None: # if not stoped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return str(round(t,3))



#-------------------------------------------------------------------------------
class CallTest(object):
    '''Base class for timed tests
    '''
    def __init__(self):
        '''Perform setup routines for tests
        '''
        pass 

    def testFocus(self):
        '''Calls to be timed
        '''
        pass # run tests



class TestImportStar(CallTest):
    def testFocus(self):
        import music21 # @UnusedImport # the point is timing the import!




#-------------------------------------------------------------------------------
# handler
class CallGraph:

    def __init__(self):
        self.includeList = None
        self.excludeList = ['pycallgraph.*']
        self.excludeList += ['re.*','sre_*']
        
        # only test our own code for now
        self.excludeList += ['*xlrd*', 'matplotlib*', 'scipy*', 'numpy*']

        self.excludeList += ['pdb*', 'repr*', 'cmd*', 'bdb*', 'threading.*', '_weakrefset*']
        self.excludeList += ['unittest*','doctest*']
        self.excludeList += ['encodings*', 'pkg_resources*', 'ntpath*', 'shutil.*', 'pkgutil.*']
        self.excludeList += ['difflib*','urlparse*', 'dateutil.*', 'calendar.*',]
        self.excludeList += ['zipfile*','io.*', 'collections.*', 'tempfile.*', 'urllib.*', 'StringIO*']
        self.excludeList += ['csv.*', 'json.*', 'os.*', 'distutils.*','ctypes*']
        self.excludeList += ['FileDialog.*', 'Tk*', 'PIL*', 'tk*', 'pillow*']
        
        # these have been shown to be very fast
        self.excludeList += ['*xmlnode*', 'xml.dom.*', 'xml.sax.*', 'codecs.*', 'io.*']
        #self.excludeList += ['*meter*', 'encodings*', '*isClass*', '*duration.Duration*']

        # these cloud up the graph... should be tested, but removed when you want to see
        # what is up
        self.excludeList += ['music21.articulations.*',
                             'music21.instrument.*', 
                             'music21.musicxml.*',
                             'music21.romanText.base.*',
                             'music21.clef.*',
                             'music21.features.jSymbolic.*',
                             'music21.features.native.*',
                             'music21.lily.lilyObjects.*']

        self.callTest = TestImportStar

        # common to all call tests. 
        if hasattr(self.callTest, 'includeList'):
            self.includeList = self.callTest.includeList

    def run(self, runWithEnviron=False):
        '''Main code runner for testing. To set a new test, update the self.callTest attribute in __init__(). 
        '''
        suffix = '.svg'
        fmt = suffix[1:]
        _MOD = "test.timeGraphs.py"

        if runWithEnviron:
            from music21 import environment
            environLocal = environment.Environment(_MOD)
            fp = environLocal.getTempFile(suffix)
        # manually get a temporary file
        else:
            import tempfile
            import os
            import sys
            if os.name in ['nt'] or sys.platform.startswith('win'):
                platform = 'win'
            else:
                platform = 'other'
            
            tempdir = os.path.join(tempfile.gettempdir(), 'music21')
            if platform != 'win':
                fd, fp = tempfile.mkstemp(dir=tempdir, suffix=suffix)
                if isinstance(fd, int):
                # on MacOS, fd returns an int, like 3, when this is called
                # in some context (specifically, programmatically in a 
                # TestExternal class. the fp is still valid and works
                # TODO: this did not work on MacOS 10.6.8 w/ py 2.7
                    pass
                else:
                    fd.close() 
            else:
                tf = tempfile.NamedTemporaryFile(dir=tempdir, suffix=suffix)
                fp = tf.name
                tf.close()

 
        if self.includeList is not None:
            gf = pycallgraph.GlobbingFilter(include=self.includeList, exclude=self.excludeList)
        else:
            gf = pycallgraph.GlobbingFilter(exclude=self.excludeList)
        # create instance; will call setup routines
        ct = self.callTest()

        # start timer
        print('%s starting test' % _MOD)
        t = Timer()
        t.start()

        pycallgraph.start_trace(filter_func = gf)
        ct.testFocus() # run routine

        pycallgraph.stop_trace()
        pycallgraph.make_dot_graph(fp, format=fmt, tool='/usr/local/bin/dot')
        print('elapsed time: %s' % t)
        # open the completed file
        print('file path: ' + fp)
        try:
            environLocal = environment.Environment(_MOD)
            environLocal.launch(format, fp)
        except NameError:
            pass


if __name__ == '__main__':

    cg = CallGraph()
    cg.run()



#------------------------------------------------------------------------------
# eof

