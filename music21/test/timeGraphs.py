#!/usr/local/bin/python
#-------------------------------------------------------------------------------
# Name:          timeGraphs.py
# Purpose:       install
#
# Authors:       Michael Scott Cuthbert
#                Christopher Ariza
#
# Copyright:     (c) 2009-2010 The music21 Project
# License:       GPL
#-------------------------------------------------------------------------------


# script to create a graph to time how fast some things are happening...
# generates pretty graphs showing what the bottlenecks in the system are, for helping to
# improve them.  Requires pycallgraph (not included with music21).  


import pycallgraph
import time


from music21 import *
import music21.stream
import music21.humdrum
import music21.converter
import music21.corpus
import music21.lily
import music21.trecento.capua


from music21.humdrum import testFiles as humdrumTestFiles

from music21 import common

from music21 import environment
_MOD = "test.timeGraphs.py"
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class CallTest:
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


#-------------------------------------------------------------------------------
class TestTimeHumdrum(CallTest):
    def testFocus(self):
        masterStream = music21.humdrum.parseData(humdrumTestFiles.mazurka6).stream

class TestTimeMozart(CallTest):
    def testFocus(self):
        a = music21.converter.parse(music21.corpus.getWork('k155')[0])
    #    ls = music21.lily.LilyString("{" + a[0].lily + "}")
    #    ls.showPNG()
    #    a = music21.converter.parse(mxtf.ALL[1])

class TestTimeCapua1(CallTest):
    def testFocus(self):
        c1 = music21.trecento.capua.Test()
        c1.testRunPiece()

class TestTimeCapua2(CallTest):
    def testFocus(self):
        music21.trecento.capua.ruleFrequency()

class TestTimeIsmir(CallTest):
    def testFocus(self):
        s1 = corpus.parseWork('bach/bwv248')
        post = s1.musicxml


class TestMakeMeasures(CallTest):
    def __init__(self):
        self.s = music21.stream.Stream()
        for i in range(10):
            n = note.Note()
            self.s.append(n)

    def testFocus(self):
        post = self.s.makeMeasures()


class TestMakeTies(CallTest):
    def __init__(self):
        self.s = music21.stream.Stream()
        for i in range(100):
            n = note.Note()
            n.quarterLength = 8
            self.s.append(n)
        self.s = self.s.makeMeasures()

    def testFocus(self):
        self.s.makeTies(inPlace=True)


class TestMakeBeams(CallTest):
    def __init__(self):
        self.s = music21.stream.Stream()
        for i in range(100):
            n = note.Note()
            n.quarterLength = .25
            self.s.append(n)
        self.s = self.s.makeMeasures()

    def testFocus(self):
        self.s.makeBeams(inPlace=True)


class TestMakeAccidentals(CallTest):
    def __init__(self):
        self.s = music21.stream.Stream()
        for i in range(100):
            n = note.Note()
            n.quarterLength = .25
            self.s.append(n)
        self.s = self.s.makeMeasures()

    def testFocus(self):
        self.s.makeAccidentals(inPlace=True)


class TestMusicXMLOutput(CallTest):
    def __init__(self):
        self.s = music21.stream.Stream()
        for i in range(100):
            n = note.Note()
            n.quarterLength = 1.5
            self.s.append(n)

    def testFocus(self):
        post = self.s.musicxml


class TestMusicXMLOutputParts(CallTest):
    '''This tries to isolate a problem whereby part creation is much faster than score creation. 
    '''
    def __init__(self):
        self.s = corpus.parseWork('bach/bwv66.6', forceSource=True)
        #self.s = corpus.parseWork('beethoven/opus59no2/movement3', forceSource=True)

    def testFocus(self):
        for p in self.s.parts:
            post = p.musicxml


class TestMusicXMLOutputScore(CallTest):
    '''This tries to isolate a problem whereby part creation is much faster than score creation. 
    '''
    def __init__(self):
        self.s = corpus.parseWork('bach/bwv66.6', forceSource=True)
        #self.s = corpus.parseWork('beethoven/opus59no2/movement3', forceSource=True)

    def testFocus(self):
        post = self.s.musicxml


class TestABCImport(CallTest):


    def __init__(self):
        pass

    def testFocus(self):
        self.s = corpus.parseWork('essenFolksong/erk20.abc', forceSource=True)


class TestMetadataBundle(CallTest):

    def __init__(self):
        pass

    def testFocus(self):
        # this opens and instantiates the metad
        from music21.corpus import base
        base._updateMetadataBundle()




class TestCreateTimeSignature(CallTest):

    def __init__(self):
        from music21.test import testPerformance
        self.t = test.testPerformance.Test()

    def testFocus(self):
        # create 500 time signatures
        self.t.runCreateTimeSignatures()



class TestCreateDurations(CallTest):

    def __init__(self):
        from music21.test import testPerformance
        self.t = test.testPerformance.Test()

    def testFocus(self):
        # create 500 time signatures
        self.t.runCreateDurations()




class TestParseABC(CallTest):

    def __init__(self):
        from music21.test import testPerformance
        self.t = test.testPerformance.Test()

    def testFocus(self):
        # create 500 time signatures
        self.t.runParseABC()




class TestMusicXMLObjectTypeChecking(CallTest):

    def __init__(self):
        from music21 import musicxml
        self.objs = []
        self.count = 100000
        # all objects that would be found in a Measure
        for x in range(self.count):
            self.objs.append(musicxml.Note())
        for x in range(self.count):
            self.objs.append(musicxml.Backup())
        for x in range(self.count):
            self.objs.append(musicxml.Forward())

    def testFocus(self):
        # note: this shows that using isinstance() is much faster than 
        # checking the tag attribute

        from music21 import musicxml
        # create 500 time signatures
        n = []
        b = []
        f = []
#         for obj in self.objs:
#             if isinstance(obj, musicxml.Note):
#                 n.append(obj)
#             elif isinstance(obj, musicxml.Backup):
#                 b.append(obj)
#             elif isinstance(obj, musicxml.Forward):
#                 f.append(obj)

        for obj in self.objs:
            if obj.tag == 'note':
                n.append(obj)
            elif obj.tag == 'backup':
                b.append(obj)
            elif obj.tag == 'forward':
                f.append(obj)


        assert(len(n) == self.count)
        assert(len(b) == self.count)
        assert(len(f) == self.count)


class TestGetContextByClass(CallTest):

    def __init__(self):

        from music21 import corpus, clef, meter, key
        self.s = corpus.parseWork('bwv66.6')


    def testFocus(self):
        from music21 import corpus, clef, meter, key
        for p in self.s.parts:
            for m in p.getElementsByClass('Measure'):
                post = m.getContextByClass(clef.Clef)
                post = m.getContextByClass(meter.TimeSignature)
                post = m.getContextByClass(key.KeySignature)
                for n in m.notes:
                    post = n.getContextByClass(clef.Clef)
                    post = n.getContextByClass(meter.TimeSignature)
                    post = n.getContextByClass(key.KeySignature)
            







#-------------------------------------------------------------------------------
# handler
class CallGraph:

    def __init__(self):
        self.excludeList = ['pycallgraph.*','re.*','sre_*', 'copy*', '*xlrd*']
        #excludeList += ['*meter*', 'encodings*', '*isClass*', '*duration.Duration*']

        # set class  to test here
        #self.callTest = TestMakeTies
        #self.callTest = TestMakeAccidentals
        #self.callTest = TestMusicXMLOutputParts
        #self.callTest = TestMusicXMLOutputScore

        #self.callTest = TestABCImport
        #self.callTest = TestMetadataBundle
        #self.callTest = TestCreateTimeSignature

        #self.callTest = TestParseABC
        #self.callTest = TestMusicXMLObjectTypeChecking
        self.callTest = TestGetContextByClass

    def run(self):
        '''Main code runner for testing. To set a new test, update the self.callTest attribute in __init__(). 
        '''
        fp = environLocal.getTempFile('.png')
        gf = pycallgraph.GlobbingFilter(exclude=self.excludeList)
        # create instnace; will call setup routines
        ct = self.callTest()

        # start timer
        print('starting test')
        t = common.Timer()
        t.start()

        pycallgraph.start_trace(filter_func = gf)
        ct.testFocus() # run routine

        pycallgraph.stop_trace()
        pycallgraph.make_dot_graph(fp)

        print('elpased time: %s' % t)
        # open the completed file
        environLocal.launch('png', fp)


if __name__ == '__main__':

    cg = CallGraph()
    cg.run()



#------------------------------------------------------------------------------
# eof

