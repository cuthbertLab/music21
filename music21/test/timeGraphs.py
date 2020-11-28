# # -*- coding: utf-8 -*-
# # ------------------------------------------------------------------------------
# # Name:          timeGraphs.py
# # Purpose:       install
# #
# # Authors:       Michael Scott Cuthbert
# #                Christopher Ariza
# #
# # Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# # License:      BSD, see license.txt
# # ------------------------------------------------------------------------------
# import time
#
#
# # script to create a graph to time how fast some things are happening...
# # generates pretty graphs showing what the bottlenecks in the system are, for helping to
# # improve them.  Requires pycallgraph (not included with music21).
#
# import pycallgraph  # @UnusedImport @UnresolvedImport
# import pycallgraph.output  # @UnresolvedImport
#
#
# # from music21 import *
# # import music21.stream
# # import music21.humdrum
# # import music21.converter
# # import music21.corpus
# # import music21.trecento.capua
# #
# #
# # from music21.humdrum import testFiles as humdrumTestFiles
# #
# # from music21 import common
#
#
#
# # this class is duplicated from common.py in order to avoid
# # import the module for clean testing
# class Timer:
#     """An object for timing."""
#
#     def __init__(self):
#         # start on init
#         self._tStart = time.time()
#         self._tDif = 0
#         self._tStop = None
#
#     def start(self):
#         '''Explicit start method; will clear previous values.
#         Start always happens on initialization.'''
#         self._tStart = time.time()
#         self._tStop = None  # show that a new run has started so __call__ works
#         self._tDif = 0
#
#     def stop(self):
#         self._tStop = time.time()
#         self._tDif = self._tStop - self._tStart
#
#     def clear(self):
#         self._tStop = None
#         self._tDif = 0
#         self._tStart = None
#
#     def __call__(self):
#         '''Reports current time or, if stopped, stopped time.
#         '''
#         # if stopped, gets _tDif; if not stopped, gets current time
#         if self._tStop is None:  # if not stopped yet
#             t = time.time() - self._tStart
#         else:
#             t = self._tDif
#         return t
#
#     def __str__(self):
#         if self._tStop is None:  # if not stopped yet
#             t = time.time() - self._tStart
#         else:
#             t = self._tDif
#         return str(round(t, 3))
#
#
#
# # ------------------------------------------------------------------------------
# class CallTest:
#     '''Base class for timed tests
#     '''
#     def __init__(self):
#         '''Perform setup routines for tests
#         '''
#         pass
#
#     def testFocus(self):
#         '''Calls to be timed
#         '''
#         pass  # run tests
#
#
# class M21CallTest:
#     '''Base class for timed tests that need music21 imported
#     '''
#     def __init__(self):
#         '''Perform setup routines for tests
#         '''
#         import music21
#         self.m21 = music21
#
#
# # ------------------------------------------------------------------------------
# class TestTimeHumdrum(M21CallTest):
#     def testFocus(self):
#         music21 = self.m21
#         unused = music21.humdrum.parseData(music21.humdrum.humdrumTestFiles.mazurka6).stream
#
# class TestTimeMozart(M21CallTest):
#     def testFocus(self):
#         music21 = self.m21
#         unused = music21.converter.parse(music21.corpus.getWork('k155')[0])
#
# class TestTimeCapua1(M21CallTest):
#     def testFocus(self):
#         music21 = self.m21
#         c1 = music21.trecento.capua.Test()
#         c1.testRunPiece()
#
# class TestTimeCapua2(M21CallTest):
#     def testFocus(self):
#         music21 = self.m21
#         music21.trecento.capua.ruleFrequency()
#
# class TestTimeIsmir(M21CallTest):
#     def testFocus(self):
#         music21 = self.m21
#         s1 = music21.corpus.parse('bach/bwv248')
#         unused = s1.musicxml
#
#
# class TestMakeMeasures(CallTest):
#     def __init__(self):
#         super().__init__()
#         import music21.stream
#         import music21.note
#         self.s = music21.stream.Stream()
#         for i in range(10):
#             n = music21.note.Note()
#             self.s.append(n)
#
#     def testFocus(self):
#         unused = self.s.makeMeasures()
#
#
# class TestMakeTies(CallTest):
#     def __init__(self):
#         import music21.stream
#         import music21.note
#
#         super().__init__()
#
#         self.s = music21.stream.Stream()
#         for i in range(100):
#             n = music21.note.Note()
#             n.quarterLength = 8
#             self.s.append(n)
#         self.s = self.s.makeMeasures()
#
#     def testFocus(self):
#         self.s.makeTies(inPlace=True)
#
#
# class TestMakeBeams(CallTest):
#     def __init__(self):
#         import music21.stream
#         import music21.note
#         super().__init__()
#
#         self.s = music21.stream.Stream()
#         for i in range(100):
#             n = music21.note.Note()
#             n.quarterLength = 0.25
#             self.s.append(n)
#         self.s = self.s.makeMeasures()
#
#     def testFocus(self):
#         self.s.makeBeams(inPlace=True)
#
#
# class TestMakeAccidentals(CallTest):
#     def __init__(self):
#         import music21.stream
#         import music21.note
#
#         super().__init__()
#
#         self.s = music21.stream.Stream()
#         for i in range(100):
#             n = music21.note.Note()
#             n.quarterLength = 0.25
#             self.s.append(n)
#         self.s = self.s.makeMeasures()
#
#     def testFocus(self):
#         self.s.makeAccidentals(inPlace=True)
#
#
# class TestMusicXMLOutput(CallTest):
#     def __init__(self):
#         import music21.stream
#         import music21.note
#
#         super().__init__()
#
#         self.s = music21.stream.Stream()
#         for i in range(100):
#             n = music21.note.Note()
#             n.quarterLength = 1.5
#             self.s.append(n)
#
#     def testFocus(self):
#         unused = self.s.musicxml
#
#
# class TestMusicXMLOutputParts(CallTest):
#     '''This tries to isolate a problem whereby part
#     creation is much faster than score creation.
#     '''
#     def __init__(self):
#         from music21 import corpus
#         super().__init__()
#
#         self.s = corpus.parse('bach/bwv66.6', forceSource=True)
#         # self.s = corpus.parse('beethoven/opus59no2/movement3', forceSource=True)
#
#     def testFocus(self):
#         for p in self.s.parts:
#             unused = p.musicxml
#
#
# class TestMusicXMLOutputScore(CallTest):
#     '''This tries to isolate a problem whereby part creation is much faster than score creation.
#     '''
#     def __init__(self):
#         from music21 import corpus
#
#         super().__init__()
#
#         self.s = corpus.parse('bach/bwv66.6', forceSource=True)
#         # self.s = corpus.parse('beethoven/opus59no2/movement3', forceSource=True)
#
#     def testFocus(self):
#         unused = self.s.musicxml
#
#
# class TestABCImport(M21CallTest):
#
#     def testFocus(self):
#         music21 = self.m21
#         self.s = music21.corpus.parse('essenFolksong/erk20.abc', forceSource=True)
#
#
#
#
#
# class TestCreateTimeSignature(CallTest):
#
#     def __init__(self):
#         from music21.test import testPerformance
#         super().__init__()
#
#         self.t = testPerformance.Test()
#
#     def testFocus(self):
#         # create 500 time signatures
#         self.t.runCreateTimeSignatures()
#
#
#
# class TestCreateDurations(CallTest):
#
#     def __init__(self):
#         from music21.test import testPerformance
#         super().__init__()
#
#         self.t = testPerformance.Test()
#
#     def testFocus(self):
#         # create 500 time signatures
#         self.t.runCreateDurations()
#
#
#
#
# class TestParseABC(CallTest):
#
#     def __init__(self):
#         super().__init__()
#         from music21.test import testPerformance
#         self.t = testPerformance.Test()
#
#     def testFocus(self):
#         # create 500 time signatures
#         self.t.runParseABC()
#
#
#
#
#
#
# class TestGetContextByClassA(CallTest):
#
#     def __init__(self):
#         super().__init__()
#         from music21 import corpus
#         self.s = corpus.parse('bwv66.6')
#
#
#     def testFocus(self):
#         from music21 import clef, meter, key
#         for p in self.s.parts:
#             for m in p.getElementsByClass('Measure'):
#                 unused = m.getContextByClass(clef.Clef)
#                 unused = m.getContextByClass(meter.TimeSignature)
#                 unused = m.getContextByClass(key.KeySignature)
#                 for n in m.notesAndRests:
#                     unused = n.getContextByClass(clef.Clef)
#                     unused = n.getContextByClass(meter.TimeSignature)
#                     unused = n.getContextByClass(key.KeySignature)
#
#
# class TestParseRNText(CallTest):
#
#     def __init__(self):
#         super().__init__()
#         from music21.test import testPerformance
#         self.t = testPerformance.Test()
#
#     def testFocus(self):
#         self.t.runParseMonteverdiRNText()
#
#
# # ------------------------------------------------------------------------------
# class TestMusicXMLMultiPartOutput(CallTest):
#
#     def __init__(self):
#         super().__init__()
#         from music21 import note, stream
#         self.s = stream.Score()
#         for i in range(10):  # parts
#             p = stream.Part()
#             for j in range(10):  # measures
#                 m = stream.Measure()
#                 m.append(note.Note(type='quarter'))
#                 p.append(m)
#             p._mutable = False
#             self.s.insert(0, p)
#
#         for obj in self.s.recurse(streamsOnly=True):
#             obj._mutable = False
#
#         # self.s.show()
#
#     def testFocus(self):
#         # get musicxml string
#         unused = self.s.musicxml
#
#
# class TestCommonContextSearches(CallTest):
#
#     def __init__(self):
#         from music21 import corpus
#         self.s = corpus.parse('bwv66.6')
#
#     def testFocus(self):
#         unused = self.s.parts[0].getElementsByClass(
#             'Measure')[3].getContextByClass('TimeSignature')
#
#
# class TestBigMusicXML(CallTest):
#
#     def __init__(self):
#         from music21 import corpus
#         self.s = corpus.parse('opus41no1')
#
#     def testFocus(self):
#         unused = self.s.musicxml
#
#
# class TestGetElementsByClassA(CallTest):
#
#     def __init__(self):
#         from music21 import corpus
#         self.s = corpus.parse('bwv66.6')
#
#     def testFocus(self):
#         unused = self.s.flat.notes
#
#
#
# class TestGetElementsByClassB(CallTest):
#
#     def __init__(self):
#         from music21 import stream, note, clef, meter, chord
#         self.s = stream.Stream()
#         self.s.repeatAppend(note.Note(), 300)
#         self.s.repeatAppend(note.Rest(), 300)
#         self.s.repeatAppend(chord.Chord(), 300)
#         self.s.repeatInsert(meter.TimeSignature(), [0, 50, 100, 150])
#         self.s.repeatInsert(clef.BassClef(), [0, 50, 100, 150])
#
#     def testFocus(self):
#         for i in range(20):
#             self.s.getElementsByClass(['Rest'])
#             self.s.getElementsByClass(['Note'])
#             self.s.getElementsByClass(['GeneralNote'])
#             self.s.getElementsByClass(['NotRest'])
#             self.s.getElementsByClass(['BassClef'])
#             self.s.getElementsByClass(['Clef'])
#             self.s.getElementsByClass(['TimeSignature'])
#
#
# class TestGetContextByClassB(CallTest):
#     def __init__(self):
#         from music21 import stream, note, meter
#
#         self.s = stream.Score()
#
#         p1 = stream.Part()
#         m1 = stream.Measure()
#         m1.repeatAppend(note.Note(), 3)
#         m1.timeSignature = meter.TimeSignature('3/4')
#         m2 = stream.Measure()
#         m2.repeatAppend(note.Note(), 3)
#         p1.append(m1)
#         p1.append(m2)
#
#         p2 = stream.Part()
#         m3 = stream.Measure()
#         m3.timeSignature = meter.TimeSignature('3/4')
#         m3.repeatAppend(note.Note(), 3)
#         m4 = stream.Measure()
#         m4.repeatAppend(note.Note(), 3)
#         p2.append(m3)
#         p2.append(m4)
#
#         self.s.insert(0, p1)
#         self.s.insert(0, p2)
#
#         p3 = stream.Part()
#         m5 = stream.Measure()
#         m5.timeSignature = meter.TimeSignature('3/4')
#         m5.repeatAppend(note.Note(), 3)
#         m6 = stream.Measure()
#         m6.repeatAppend(note.Note(), 3)
#         p3.append(m5)
#         p3.append(m6)
#
#         p4 = stream.Part()
#         m7 = stream.Measure()
#         m7.timeSignature = meter.TimeSignature('3/4')
#         m7.repeatAppend(note.Note(), 3)
#         m8 = stream.Measure()
#         m8.repeatAppend(note.Note(), 3)
#         p4.append(m7)
#         p4.append(m8)
#
#         self.s.insert(0, p3)
#         self.s.insert(0, p4)
#
#         # self.targetMeasures = m4
#         self.targetNoteA = m4[-1]  # last element is a note
#         self.targetNoteB = m1[-1]  # last element is a note
#
#     def testFocus(self):
#         # post = self.targetNoteA.getContextByClass('TimeSignature')
#         unused = self.targetNoteA.previous('TimeSignature')
#
#
#
# class TestMeasuresA(CallTest):
#
#     def __init__(self):
#         from music21 import corpus
#         self.s = corpus.parse('symphony94/02')
#
#     def testFocus(self):
#         unused = self.s.measures(3, 10)
#
#
# class TestMeasuresB(CallTest):
#     def __init__(self):
#         from music21 import stream, note, meter
#
#         self.s = stream.Score()
#         for j in [1]:
#             p = stream.Part()
#             for mn in range(10):
#                 m = stream.Measure()
#                 if mn == 0:
#                     m.timeSignature = meter.TimeSignature('3/4')
#                 for i in range(3):
#                     m.append(note.Note())
#                 p.append(m)
#             self.s.insert(0, p)
#         # self.s.show()
#
#     def testFocus(self):
#         unused = self.s.measures(3, 6)
#
#
# class TestImportCorpus2(M21CallTest):
#
#     def testFocus(self):
#         music21 = self.m21
#         unused = music21.corpus.getWork('bach/bwv66.6')
#
#
# class TestImportCorpus3(CallTest):
#     includeList = ['music21.corpus.*']
#
#     def testFocus(self):
#         import music21
#         bc = music21.corpus.parse('bach/bwv1.6')  # @UndefinedVariable @UnusedVariable
#
# class TestRomantextParse(CallTest):
#     def __init__(self):
#         from music21 import converter
#         from music21.romanText import testFiles as tf
#         self.converter = converter
#         self.tf = tf
#
#     def testFocus(self):
#         self.converter.parse(self.tf.monteverdi_3_13)
#
#
# # ------------------------------------------------------------------------------
# # handler
# class CallGraph:
#
#     def __init__(self):
#         self.includeList = ['*xmlToM21*', '*meter*']
#         # self.excludeList = ['pycallgraph.*', 're.*', 'sre_*', 'copy*',]
#         self.excludeList = ['pycallgraph.*']
#         self.excludeList += ['re.*', 'sre_*']
#         # these have been shown to be very fast
#         self.excludeList += ['xml.dom.*', 'codecs.*', 'io.*']
#         # self.excludeList += ['*meter*', 'encodings*', '*isClass*', '*duration.Duration*']
#
#         # set class  to test here
#         # self.callTest = TestMakeTies
#         # self.callTest = TestMakeAccidentals
#         # self.callTest = TestMusicXMLOutputParts
#         # self.callTest = TestMusicXMLOutputScore
#
#         # self.callTest = TestABCImport
#         # self.callTest = TestMetadataBundle
#         # self.callTest = TestCreateTimeSignature
#
#         # self.callTest = TestParseABC
#         # self.callTest = TestMusicXMLObjectTypeChecking
#         # self.callTest = TestGetContextByClass
#         # self.callTest = TestMakeMeasures
#         # self.callTest = TestGetElementsByClass
#
#         # self.callTest = TestMusicXMLMultiPartOutput
#         # self.callTest = TestCommonContextSearches
#         # self.callTest = TestBigMusicXML
#
#         # self.callTest = TestMeasuresA
#         # self.callTest = TestTimeMozart
#         # self.callTest = TestTimeIsmir
#         # self.callTest = TestGetContextByClassB
#         self.callTest = TestMeasuresB
#         # self.callTest = TestImportCorpus
#         # self.callTest = TestImportCorpus3
#         # self.callTest = TestRomantextParse
#         # self.callTest = TestImportStar
#
#         # common to all call tests.
#         if hasattr(self.callTest, 'includeList'):
#             self.includeList = self.callTest.includeList
#
#     def run(self, runWithEnviron=True):
#         '''
#         Main code runner for testing. To set a new test,
#         update the self.callTest attribute in __init__().
#
#         Note that the default of runWithEnviron imports music21.environment.  That might
#         skew results
#         '''
#         from music21 import environment
#
#         suffix = '.png'  # '.svg'
#         outputFormat = suffix[1:]
#         _MOD = "test.timeGraphs"
#
#         if runWithEnviron:
#             environLocal = environment.Environment(_MOD)
#             fp = environLocal.getTempFile(suffix)
#         # manually get a temporary file
#         else:
#             import tempfile
#             import os
#             import sys
#             if os.name in ['nt'] or sys.platform.startswith('win'):
#                 platform = 'win'
#             else:
#                 platform = 'other'
#
#             tempdir = os.path.join(tempfile.gettempdir(), 'music21')
#             if platform != 'win':
#                 fd, fp = tempfile.mkstemp(dir=tempdir, suffix=suffix)
#                 if isinstance(fd, int):
#                 # on MacOS, fd returns an int, like 3, when this is called
#                 # in some context (specifically, programmatically in a
#                 # TestExternal class. the fp is still valid and works
#                     pass
#                 else:
#                     fd.close()
#             else:
#                 tf = tempfile.NamedTemporaryFile(dir=tempdir, suffix=suffix)
#                 fp = tf.name
#                 tf.close()
#
#
#         if self.includeList is not None:
#             gf = pycallgraph.GlobbingFilter(include=self.includeList, exclude=self.excludeList)
#         else:
#             gf = pycallgraph.GlobbingFilter(exclude=self.excludeList)
#         # create instance; will call setup routines
#         ct = self.callTest()
#
#         # start timer
#         print('%s starting test' % _MOD)
#         t = Timer()
#         t.start()
#
#         graphviz = pycallgraph.output.GraphvizOutput(output_file=fp)
#         graphviz.tool = '/usr/local/bin/dot'
#
#         config = pycallgraph.Config()
#         config.trace_filter = gf
#
#         from music21 import meter
#         from music21 import note
#
#         with pycallgraph.PyCallGraph(output=graphviz, config=config):
#             note.Note()
#             meter.TimeSignature('4/4')
#             ct.testFocus()  # run routine
#             pass
#         print('elapsed time: %s' % t)
#         # open the completed file
#         print('file path: ' + fp)
#         try:
#             environLocal = environment.Environment(_MOD)
#             environLocal.launch(outputFormat, fp)
#         except NameError:
#             pass
#
#
# if __name__ == '__main__':
#
#     cg = CallGraph()
#     cg.run()
#
#
