# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:          timeGraphs.py
# Purpose:       time how long it takes to run music21 commands
#
# Authors:       Michael Scott Cuthbert
#                Christopher Ariza
#
# Copyright:    Copyright © 2009-2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
# pragma: no cover
import cProfile
import pstats
# import time

import music21
# from music21.common.objects import Timer



class Test:
    '''Base class for timed tests that need music21 imported
    '''


# ------------------------------------------------------------------------------
class TestTimeHumdrum(Test):
    def testFocus(self):
        # pylint: disable=expression-not-assigned
        # noinspection PyStatementEffect
        music21.humdrum.parseData(music21.humdrum.humdrumTestFiles.mazurka6
                                  ).stream

class TestTimeMozart(Test):
    def testFocus(self):
        music21.converter.parse(music21.corpus.getWork('k155')[0])

class TestTimeCapua1(Test):
    def testFocus(self):
        c1 = music21.trecento.capua.Test()
        c1.testRunPiece()

class TestTimeCapua2(Test):
    def testFocus(self):
        music21.trecento.capua.ruleFrequency()

class TestTimeIsmir(Test):
    def testFocus(self):
        music21.corpus.parse('bach/bwv248')


class TestMakeMeasures(Test):
    def __init__(self):
        super().__init__()
        self.s = music21.stream.Stream()
        for i in range(10):
            n = music21.note.Note()
            self.s.append(n)

    def testFocus(self):
        self.s.makeMeasures()


class TestMakeTies(Test):
    def __init__(self):
        super().__init__()

        self.s = music21.stream.Stream()
        for i in range(100):
            n = music21.note.Note()
            n.quarterLength = 8
            self.s.append(n)
        self.s = self.s.makeMeasures()

    def testFocus(self):
        self.s.makeTies(inPlace=True)


class TestMakeBeams(Test):
    def __init__(self):
        super().__init__()

        self.s = music21.stream.Stream()
        for i in range(100):
            n = music21.note.Note()
            n.quarterLength = 0.25
            self.s.append(n)
        self.s = self.s.makeMeasures()

    def testFocus(self):
        self.s.makeBeams(inPlace=True)


class TestMakeAccidentals(Test):
    def __init__(self):

        super().__init__()

        self.s = music21.stream.Stream()
        for i in range(100):
            n = music21.note.Note()
            n.quarterLength = 0.25
            self.s.append(n)
        self.s = self.s.makeMeasures()

    def testFocus(self):
        self.s.makeAccidentals(inPlace=True)


class TestMusicXMLOutput(Test):
    def __init__(self):
        self.s = music21.stream.Stream()
        for i in range(100):
            n = music21.note.Note()
            n.quarterLength = 1.5
            self.s.append(n)

    def testFocus(self):
        self.s.write('musicxml')


class TestMusicXMLOutputParts(Test):
    '''
    This tries to isolate a problem whereby part
    creation is much faster than score creation.
    '''
    def __init__(self):
        from music21 import corpus

        self.s = corpus.parse('bach/bwv66.6', forceSource=True)
        # self.s = corpus.parse('beethoven/opus59no2/movement3', forceSource=True)

    def testFocus(self):
        for p in self.s.parts:
            p.write('musicxml')




class TestCreateTimeSignature(Test):

    def __init__(self):
        from music21.test import testPerformance
        self.t = testPerformance.Test()

    def testFocus(self):
        # create 500 time signatures
        self.t.runCreateTimeSignatures()



class TestCreateDurations(Test):

    def __init__(self):
        from music21.test import testPerformance
        self.t = testPerformance.Test()

    def testFocus(self):
        # create 500 time signatures
        self.t.runCreateDurations()




class TestParseABC(Test):

    def __init__(self):
        from music21.test import testPerformance
        self.t = testPerformance.Test()

    def testFocus(self):
        # create 500 time signatures
        self.t.runParseABC()






class TestGetContextByClassA(Test):

    def __init__(self):
        from music21 import corpus
        self.s = corpus.parse('bwv66.6')


    def testFocus(self):
        from music21 import clef, meter, key
        for p in self.s.parts:
            for m in p.getElementsByClass('Measure'):
                m.getContextByClass(clef.Clef)
                m.getContextByClass(meter.TimeSignature)
                m.getContextByClass(key.KeySignature)
                for n in m.notesAndRests:
                    n.getContextByClass(clef.Clef)
                    n.getContextByClass(meter.TimeSignature)
                    n.getContextByClass(key.KeySignature)


class TestParseRNText(Test):

    def __init__(self):
        from music21.test import testPerformance
        self.t = testPerformance.Test()

    def testFocus(self):
        self.t.runParseMonteverdiRNText()


# ------------------------------------------------------------------------------
class TestMusicXMLMultiPartOutput(Test):

    def __init__(self):
        from music21 import note, stream
        self.s = stream.Score()
        for i in range(10):  # parts
            p = stream.Part()
            for j in range(10):  # measures
                m = stream.Measure()
                m.append(note.Note(type='quarter'))
                p.append(m)
            p._mutable = False
            self.s.insert(0, p)

        for obj in self.s.recurse(streamsOnly=True):
            obj._mutable = False

        # self.s.show()

    def testFocus(self):
        self.s.write('musicxml')


class TestCommonContextSearches(Test):

    def __init__(self):
        from music21 import corpus
        self.s = corpus.parse('bwv66.6')

    def testFocus(self):
        self.s.parts[0].getElementsByClass(
            'Measure')[3].getContextByClass('TimeSignature')


class TestBigMusicXML(Test):

    def __init__(self):
        from music21 import corpus
        self.s = corpus.parse('opus41no1')

    def testFocus(self):
        self.s.write('musicxml')


class TestGetElementsByClassA(Test):

    def __init__(self):
        from music21 import corpus
        self.s = corpus.parse('bwv66.6')

    def testFocus(self):
        len(self.s.flat.notes)



class TestGetElementsByClassB(Test):

    def __init__(self):
        from music21 import stream, note, clef, meter, chord
        self.s = stream.Stream()
        self.s.repeatAppend(note.Note(), 300)
        self.s.repeatAppend(note.Rest(), 300)
        self.s.repeatAppend(chord.Chord(), 300)
        self.s.repeatInsert(meter.TimeSignature(), [0, 50, 100, 150])
        self.s.repeatInsert(clef.BassClef(), [0, 50, 100, 150])

    def testFocus(self):
        for i in range(20):
            self.s.getElementsByClass(['Rest'])
            self.s.getElementsByClass(['Note'])
            self.s.getElementsByClass(['GeneralNote'])
            self.s.getElementsByClass(['NotRest'])
            self.s.getElementsByClass(['BassClef'])
            self.s.getElementsByClass(['Clef'])
            self.s.getElementsByClass(['TimeSignature'])


class TestGetContextByClassB(Test):
    def __init__(self):
        from music21 import stream, note, meter

        self.s = stream.Score()

        p1 = stream.Part()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note(), 3)
        m1.timeSignature = meter.TimeSignature('3/4')
        m2 = stream.Measure()
        m2.repeatAppend(note.Note(), 3)
        p1.append(m1)
        p1.append(m2)

        p2 = stream.Part()
        m3 = stream.Measure()
        m3.timeSignature = meter.TimeSignature('3/4')
        m3.repeatAppend(note.Note(), 3)
        m4 = stream.Measure()
        m4.repeatAppend(note.Note(), 3)
        p2.append(m3)
        p2.append(m4)

        self.s.insert(0, p1)
        self.s.insert(0, p2)

        p3 = stream.Part()
        m5 = stream.Measure()
        m5.timeSignature = meter.TimeSignature('3/4')
        m5.repeatAppend(note.Note(), 3)
        m6 = stream.Measure()
        m6.repeatAppend(note.Note(), 3)
        p3.append(m5)
        p3.append(m6)

        p4 = stream.Part()
        m7 = stream.Measure()
        m7.timeSignature = meter.TimeSignature('3/4')
        m7.repeatAppend(note.Note(), 3)
        m8 = stream.Measure()
        m8.repeatAppend(note.Note(), 3)
        p4.append(m7)
        p4.append(m8)

        self.s.insert(0, p3)
        self.s.insert(0, p4)

        # self.targetMeasures = m4
        self.targetNoteA = m4._elements[-1]  # last element is a note
        self.targetNoteB = m1._elements[-1]  # last element is a note

    def testFocus(self):
        # post = self.targetNoteA.getContextByClass('TimeSignature')
        self.targetNoteA.previous('TimeSignature')



class TestMeasuresA(Test):

    def __init__(self):
        from music21 import corpus
        self.s = corpus.parse('symphony94/02')

    def testFocus(self):
        self.s.measures(3, 10)


class TestMeasuresB(Test):
    def __init__(self):
        from music21 import stream, note, meter

        self.s = stream.Score()
        for j in [1]:
            p = stream.Part()
            for mn in range(10):
                m = stream.Measure()
                if mn == 0:
                    m.timeSignature = meter.TimeSignature('3/4')
                for i in range(3):
                    m.append(note.Note())
                p.append(m)
            self.s.insert(0, p)
        # self.s.show()

    def testFocus(self):
        self.s.measures(3, 6)


class TestGetWork(Test):

    def testFocus(self):
        music21.corpus.getWork('bach/bwv66.6')


class TestImportCorpus3(Test):
    def __init__(self):
        # to put the path cache in.
        music21.corpus.getWork('bach/bwv66.6')

    def testFocus(self):
        music21.corpus.parse('bach/bwv1.6', forceSource=True)


class TestImportPiano(Test):
    def __init__(self):
        # to put the path cache in.
        music21.corpus.getWork('cpebach')

    def testFocus(self):
        music21.corpus.parse('cpebach', forceSource=True)


class TestRomantextParse(Test):
    def __init__(self):
        from music21.romanText import testFiles as tf
        self.converter = music21.converter
        self.tf = tf

    def testFocus(self):
        self.converter.parse(self.tf.monteverdi_3_13)


def main(TestClass):
    t = TestClass()
    with cProfile.Profile() as pr:
        t.testFocus()

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats(0.3)


if __name__ == '__main__':
    main(TestImportPiano)


