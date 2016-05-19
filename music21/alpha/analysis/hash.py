# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         alpha/analysis/hash.py
# Purpose:      Hash musical notation
#
# Authors:      Emily Zhang
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import unittest

import collections
import difflib


from music21 import note, chord, key
from music21 import interval
from music21 import stream

class Hasher(object):
    def __init__(self):
        # --- begin general types of things to hash ---
        self.validTypes = [note.Note, note.Rest, chord.Chord]
        # --- end general types of things to hash ---

        # --- begin general hashing settings --- 
        self.stripTies = True
        # --- end general hashing settings ---

        # --- begin note properties to hash ---
        self.hashPitch = True
        self.hashMIDI = True # otherwise, hash string "C-- instead of 58"
        self.hashNoteNameOctave = False # good for catching octaves, only deals octaves in note name
        self.hashOctave = False
        self.hashDuration = True
        self.roundDurationAndOffset = True
        self.hashOffset = True
        # self.roundOffset = True
        self.granularity = 32
        self.hashIntervalFromLastNote = False
        self.hashIsAccidental = False
        self.hashIsTied = False

        self.hashChordsAsNotes = True
        self.hashChordsAsChords = False # hashes information about chords instead of its note components
        self.hashNormalFormString = False
        self.hashPrimeFormString = False
        # --- end note properties to hash ---

        self.tupleList = []
        self.stateVars = {} # keeps track of last note, key sig
        self.hashingFunctions = {}

    def setupValidTypesAndStateVars(self):
        if self.hashIntervalFromLastNote:
            self.stateVars["IntervalFromLastNote"] = None

        if self.hashIsAccidental:
            self.validTypes.append(key.KeySignature)
            self.stateVars["KeySignature"] = None

        # -- Begin Individual Hashing Functions ---
    def _hashDuration(self, e, c=None):
        if c:
            return c.duration.quarterLengthFloat
        return e.duration.quarterLengthFloat

    def _hashRoundedDuration(self, e, c=None):
        if c:
            return self._getApproxDurOrOffset(float(c.duration.quarterLength))
        e.duration.quarterLength = self._getApproxDurOrOffset(float(e.duration.quarterLength))
        return e.duration.quarterLength
    

    def _hashMIDIPitchName(self, e, c=None):
        """
        returns midi pitch value (21-108) of a note
        returns 0 if rest
        returns 1 if not hashing individual notes of a chord
        """
        if c and self.hashChordsAsChords:
            return 1
        elif type(e) == note.Rest:
            return 0
        return e.pitch.midi

    
    def _hashPitchName(self, e, c=None):
        """
        returns string representation of a note e.g. "F##4"
        returns "r" if rest
        reuturns "z" if not hashing individual notes of a chord
        """
        if c and self.hashChordsAsChords:
            return "z" 
        elif type(e) == note.Rest:
            return "r"
        return str(e.pitch)
    
    def _hashPitchNameNoOctave(self, e, c=None):
        """
        returns string representation of a note e.g. "F##4"
        returns "r" if rest
        reuturns "z" if not hashing individual notes of a chord
        """
        if c and self.hashChordsAsChords:
            return "z" 
        elif type(e) == note.Rest:
            return "r"
        return str(e.pitch)[:-1]


    
    def _hashOctave(self, e, c=None):
        """
        returns octave number of a note
        retuns -1 if rest or not hashing individual notes of a chord
        """
        if type(e) == chord.Chord and self.hashChordsAsChords:
            return -1
        elif type(e) == note.Rest:
            return -1
        return e.octave

    def _hashIsAccidental(self, e, c=None):
        pass

    
    def _hashRoundedOffset(self, e, c=None):
        """
        returns offset rounded to the nearest subdivided beat
        subdivided beat is indicated with self.granularity
        by default, the granularity is set to 32, or 32nd notes
        """
        if c:

            return self._getApproxDurOrOffset(c.offset)
        e.offset = self._getApproxDurOrOffset(e.offset)
        return e.offset

    
    def _hashOffset(self, e, c=None):
        """
        returns unrounded floating point representation of a note's offset
        """
        if c:
            return c.offsetFloat
        return e.offsetFloat

    
    def _hashIntervalFromLastNote(self, e, c=None):
        """
        returns the interval between last note and current note, if extant
        known issues with first note of every measure in transposed pieces
        returns 0 if things don't work
        """
        try: 
            if type(e) == note.Note and e.previous('Note', flattenLocalSites=True) is not None:

                return interval.convertGeneric(interval.Interval(noteStart=e.previous('Note', flattenLocalSites=True), noteEnd=e).intervalClass)
        except:
            pass
        return 0

    
    def _hashPrimeFormString(self, e ,c=None):
        """
        returns prime form of a chord as a string e.g. '<037>'
        returns "<>" otherwise
        """
        if c:
            return c.primeFormString
        return "<>"

    def _hashChordNormalFormString(self, e ,c=None):
        """
        returns normal form of a chord as a string e.g. '<047>'
        returns "<>" otherwise
        """
        if c:
            return c.normalFormString
        return "<>"

    # --- End Indivdual Hashing Functions

    def setupTupleList(self):
        tupleList = []

        if self.hashPitch:
            tupleList.append("Pitch")
            if self.hashMIDI:
                self.hashingFunctions["Pitch"] = self._hashMIDIPitchName
            elif not self.hashMIDI and self.hashNoteNameOctave:
                self.hashingFuctions["Pitch"] = self._hashPitchName
#                 self.hashingFunctions["Pitch"] = ''.join([i for i in self._hashPitchName if not i.isdigit()])
            elif not self.hashMIDI and not self.hashNoteNameOctave:
                self.hashingFunctions["Pitch"] = self._hashPitchNameNoOctave
                
            if self.hashIsAccidental:
                tupleList.append("IsAccidental")
                self.hashingFunctions["IsAccidental"] = self._hashIsAccidental

        if self.hashOctave:
            tupleList.append("Octave")
            self.hashingFunctions["Octave"] = self._hashOctave

        if self.hashChordsAsNotes:
            pass
        elif self.hashChordsAsChords:
            if self.hashNormalFormString:
                tupleList.append("NormalFormString")
                self.hashingFunctions["NormalFormString"] = self._hashChordNormalFormString
            if self.hashPrimeFormString:
                tupleList.append("PrimeFormString")
                self.hashingFunctions["PrimeFormString"] = self._hashPrimeFormString


        if self.hashDuration:
            tupleList.append("Duration")
            if self.roundDurationAndOffset:
                self.hashingFunctions["Duration"] = self._hashRoundedDuration
            else:
                self.hashingFunctions["Duration"] = self._hashDuration

        if self.hashOffset:
            tupleList.append("Offset")
            if self.roundDurationAndOffset:
                self.hashingFunctions["Offset"] = self._hashRoundedOffset
            else:
                self.hashingFunctions["Offset"] = self._hashOffset

        if self.hashIntervalFromLastNote:
            tupleList.append("IntervalFromLastNote")
            self.hashingFunctions["IntervalFromLastNote"] = self._hashIntervalFromLastNote
        

        self.tupleList = tupleList
        self.tupleClass = collections.namedtuple('NoteHash', tupleList)


    def preprocessStream(self, s):
        if self.stripTies:
            try:
                st = s.stripTies()
            except:
                pass
        try:
            return st.recurse()
        except:
            return s.recurse()



    def hash(self, s):
        finalHash = []
        self.setupValidTypesAndStateVars()
        ss = self.preprocessStream(s)
        finalEltsToBeHashed = [elt for elt in ss if type(elt) in self.validTypes]
        self.setupTupleList()
        
        for elt in finalEltsToBeHashed:
            if self.hashIsAccidental and type(elt) == key.KeySignature:
                self.stateVars["currKeySig"] = elt
            elif type(elt) == chord.Chord:
                if self.hashChordsAsNotes:
                    for n in elt:
                        single_note_hash = [self.hashingFunctions[prop](n, c=elt) for prop in self.tupleList]        
                        finalHash.append(self.tupleClass._make(single_note_hash))
                elif self.hashChordsAsChords:
                    single_note_hash = [self.hashingFunctions[prop](None, c=elt) for prop in self.tupleList]
                    finalHash.append(self.tupleClass._make(single_note_hash))
            else: #type(elt) == note.Note or type(elt) == note.Rest
                single_note_hash = [self.hashingFunctions[prop](elt) for prop in self.tupleList]
                finalHash.append(self.tupleClass._make(single_note_hash))
        return finalHash

    # --- Begin Rounding Helper Functions ---

    def _getApproxDurOrOffset(self, durOrOffset):
        return round(durOrOffset*self.granularity)/self.granularity
    

    def _approximatelyEqual(self, a, b, sig_fig = 4):
        """
        use to look at whether beat lengths are close, within a certain range
        probably can use for other things that are approx. equal
        """
        return (a==b or int(a*10**sig_fig) == int(b*10**sig_fig))

    # --- End Rounding Helper Functions ---

class Test(unittest.TestCase):

    def runTest(self):
        pass

    def _approximatelyEqual(self, a, b, sig_fig = 2):
        """
        use to look at whether beat lengths are close, within a certain range
        probably can use for other things that are approx. equal
        """
        return (a==b or int(a*10**sig_fig) == int(b*10**sig_fig))

    
    def testBasicHash(self):
        """
        test for hasher with basic settings: pitch, rounded duration, offset
        with notes, chord, and rest
        """
        s1 = stream.Stream()
        note1 = note.Note("C4")
        note1.duration.type = 'half'
        note2 = note.Note("F#4")
        note3 = note.Note("B-2")
        cMinor = chord.Chord(["C4","G4","E-5"])
        cMinor.duration.type = 'half'
        r = note.Rest(quarterLength=1.5)
        s1.append(note1)
        s1.append(note2)
        s1.append(note3)
        s1.append(cMinor)
        s1.append(r)
        h = Hasher()
        hashes_plain_numbers = [(60, 2.0, 0.0), (66, 1.0, 2.0), (46, 1.0, 3.0), (60, 2.0, 4.0), (67, 2.0, 4.0), (75, 2.0, 4.0), (0, 1.5, 6.0)]
        NoteHash = collections.namedtuple('NoteHash', ["Pitch", "Duration", "Offset"])
        hashes_in_format = [NoteHash(Pitch=x, Duration=y, Offset=z) for (x, y, z) in hashes_plain_numbers]

        self.assertEqual(h.hash(s1), hashes_in_format)

    def testHashChordsAsChordsPrimeFormString(self):
        """
        test to make sure that hashing works when trying to hash chord as chord
        """
        s1 = stream.Stream()
        note1 = note.Note("C4")
        note1.duration.type = 'half'
        cMinor = chord.Chord(["C4","G4","E-5"])
        cMinor.duration.type = 'half'
        cMajor = chord.Chord(["C4","G4","E4"])
        cMajor.duration.type = "whole"
        s1.append(note1)
        s1.append(cMinor)
        s1.append(cMajor)
        h = Hasher()
        h.hashChordsAsChords = True
        h.hashChordsAsNotes = False
        h.hashPrimeFormString = True
        NoteHash = collections.namedtuple('NoteHash', ["Pitch", "PrimeFormString", "Duration", "Offset"])
        hashes_plain_numbers = [(60, "<>", 2.0, 0.0), (1, '<037>', 2.0, 2.0), (1, '<037>', 4.0, 4.0)]
        hashes_in_format = [NoteHash(Pitch=x, PrimeFormString=y, Duration = z, Offset=a) for (x, y, z, a) in hashes_plain_numbers]
        self.assertEqual(h.hash(s1), hashes_in_format)

    def testHashChordsAsChordsNormalForm(self):
        s2 = stream.Stream()
        note1 = note.Note("C4")
        note1.duration.type = 'half'
        cMinor = chord.Chord(["C4","G4","E-5"])
        cMinor.duration.type = 'half'
        cMajor = chord.Chord(["C4","G4","E3"])
        cMajor.duration.type = "whole"
        s2.append(note1)
        s2.append(cMinor)
        s2.append(cMajor)
        h = Hasher()
        h.hashChordsAsChords = True
        h.hashChordsAsNotes = False
        h.hashPrimeFormString = False
        h.hashNormalFormString = True
        NoteHash = collections.namedtuple('NoteHash', ["Pitch", "NormalFormString", "Duration", "Offset"])
        hashes_plain_numbers = [(60, "<>", 2.0, 0.0), (1, '<037>', 2.0, 2.0), (1, '<047>', 4.0, 4.0)]
        hashes_in_format = [NoteHash(Pitch=x, NormalFormString=y, Duration = z, Offset=a) for (x, y, z, a) in hashes_plain_numbers]
        self.assertEqual(h.hash(s2), hashes_in_format)

    def testHashUnroundedDuration(self):
        from pprint import pprint as pp
        s3 = stream.Stream()
        note1 = note.Note("C4")
        note2 = note.Note("G4")
        cMinor = chord.Chord(["C4","G4"])
        note1.duration.quarterLength = 1.783
        note2.duration.quarterLength = 2.0/3
        cMinor.duration.type = "half"
        s3.append(note1)
        s3.append(note2)
        s3.append(cMinor)
        h = Hasher()
        h.roundDurationAndOffset = False
        NoteHash = collections.namedtuple('NoteHash', ["Pitch", "Duration", "Offset"])
        hashes_plain_numbers = [(60, 1.783, 0.0), (67, 2.0/3, 1.783), (60, 2., 1.783+2.0/3), (67, 2., 1.783+2.0/3)]
        hashes_in_format = [NoteHash(Pitch=x, Duration = z, Offset=a) for (x, z, a) in hashes_plain_numbers]
        h3 = h.hash(s3)
        h3_floats = [h3[0][2], h3[1][2], h3[2][2], h3[3][2]]
        answers_floats = [hashes_in_format[0][2], hashes_in_format[1][2], hashes_in_format[2][2], hashes_in_format[3][2]]
        assert all(self._approximatelyEqual(*values) for values in zip(h3_floats, answers_floats))

    def testHashRoundedDuration(self):
        from pprint import pprint as pp
        s3 = stream.Stream()
        note1 = note.Note("C4")
        note2 = note.Note("G4")
        cMinor = chord.Chord(["C4","G4"])
        note1.duration.quarterLength = 1.783
        note2.duration.quarterLength = 2.0/3
        cMinor.duration.type = "half"
        s3.append(note1)
        s3.append(note2)
        s3.append(cMinor)
        h = Hasher()
        h.roundDurationAndOffset = True
        NoteHash = collections.namedtuple('NoteHash', ["Pitch", "Duration", "Offset"])
        hashes_plain_numbers = [(60, 1.78125, 0.0), (67, .65625, 1.78125), (60, 2., 2.4375), (67, 2., 2.4375)]
        hashes_in_format = [NoteHash(Pitch=x, Duration = z, Offset=a) for (x, z, a) in hashes_plain_numbers]
        h3 = h.hash(s3)
        self.assertEqual(h3, hashes_in_format)
        h.granularity = 8 # smallest length note is now 8th note
        new_hashes_in_format = [(60, 1.75, 0.0), (67, .625, 1.75), (60, 2., 2.5), (67, 2., 2.5)]
        h4 = h.hash(s3)
        self.assertEqual(h4, new_hashes_in_format)

    def testHashRoundedOffset(self):
        from pprint import pprint as pp
        s3 = stream.Stream()
        for i in range(6):
            s3.append(note.Note('A-', quarterLength=1.5))
            s3.append(note.Note('C4', quarterLength=2))
            s3.append(note.Note('A-', quarterLength=1.4))
            s3.append(note.Note('B4', quarterLength=.7))
        h = Hasher()
        h.roundDurationAndOffset = True
        NoteHash = collections.namedtuple('NoteHash', ["Pitch", "Duration", "Offset"])
        h3 = h.hash(s3)
        final_offset = 6*1.5 + 6*2. + 6*1.4 + 5*.7
        assert self._approximatelyEqual(h3[-1][2], final_offset)
        h.granularity = 4 # smallest length note is now 16th note
        h4 = h.hash(s3)
        new_final_offset = 6*1.5 + 6*2. + 6*1.5 + 5 *.75
        # assert self._approximatelyEqual(h4[-1][2], new_final_offset)


class TestExternal(unittest.TestCase):

    def runTest(self):
        pass

    # def testBasicHash(self):
    #     # from pprint import pprint as pp
    #     from music21 import corpus
    #     s1 = corpus.parse('schoenberg', 6).parts[0]
    #     h = Hasher()
    #     # h.hashPitch = True
    #     # h.hashDuration = True
    #     # h.hashOffset = True
    #     # h.hashMIDI = False
    #     # h.hashChords = False
    #     # h.hashChordsAsNotes = False
    #     # h.validTypes = [note.Note, note.Rest]
    #     # h.hashMIDI = False # otherwise, hash string "C-- instead of 58"
    #     # h.hashOctave = False
    #     # h.hashDuration = True
    #     # h.roundDurationAndOffset = False
    #     # h.roundOffset = False
    #     # h.hashChordsAsNotes = False
    #     # h.hashChordsAsChords = True
    #     # h.hashOctave = True
    #     # h.hashPrimeiFormString = True
    #     h.hashIntervalFromLastNote = True
    #     # pp(h.hash(s1.recurse()))
    #     # hashes1 = h.hash(s1.recurse())
    #     s2 = corpus.parse('schoenberg', 2).parts[0]
    #     # hashes2 = h.hash(s2.recurse())
    #     s3 = corpus.parse('bwv66.6').parts[0]
    #     # print type(s3.recurse())
    #     hashes3 = h.hash(s3)
    #     # s4 = corpus.parse('bwv66.6').parts[0].transpose('M2')
    #     # s4 = s5.parts[0].transpose('M2')
    #     s4.show()
    #     # pp(s4.recurse())

    #     hashes4 = h.hash(s4)
    #     print hashes3
    #     print "    "
    #     print hashes4

    #     pp(difflib.SequenceMatcher(a=hashes1, b=hashes2).ratio())
    #     pp(difflib.SequenceMatcher(a=hashes1, b=hashes3).ratio())
    #     pp(difflib.SequenceMatcher(a=hashes2, b=hashes3).ratio())
    #     # pp(difflib.SequenceMatcher(a=hashes3, b=hashes4).ratio())
    # def testfolk(self):
    #     from music21 import corpus
    #     h = Hasher()

    #     s1 = corpus.parse('ryansMammoth/MyLoveIsInAmericaReel.abc').parts[0]
    #     s2 = corpus.parse('ryansMammoth/MyLoveIsFarAwayReel.abc').parts[0]

    #     s2.show()

    #     hashes1 = h.hash(s1)
    #     hashes2 = h.hash(s2)

    #     print difflib.SequenceMatcher(a=hashes1, b=hashes2).ratio()

    #     h.hashPitch = False

    #     hashes1 = h.hash(s1)
    #     hashes2 = h.hash(s2)

    #     print difflib.SequenceMatcher(a=hashes1, b=hashes2).ratio()


    def testBvSvS(self):
        from music21 import corpus
        h = Hasher()
        h.hashDuration = False
        h.hashOffset = False
        s1 = corpus.parse('schoenberg', 6).parts[0]
        s2 = corpus.parse('schoenberg', 2).parts[0]
        s3 = corpus.parse('bwv66.6').parts[0]
        hashes1 = h.hash(s1)
        hashes2 = h.hash(s2)
        hashes3 = h.hash(s3)

        print difflib.SequenceMatcher(a=hashes1, b=hashes2).ratio()
        print difflib.SequenceMatcher(a=hashes1, b=hashes3).ratio()
        print difflib.SequenceMatcher(a=hashes2, b=hashes3).ratio()
        s2.show()

        h.hashPitch = False
        h.hashDuration = True
        h.hashOffset = True

        hashes1 = h.hash(s1)
        hashes2 = h.hash(s2)
        hashes3 = h.hash(s3)

        print difflib.SequenceMatcher(a=hashes1, b=hashes2).ratio()
        print difflib.SequenceMatcher(a=hashes1, b=hashes3).ratio()
        print difflib.SequenceMatcher(a=hashes2, b=hashes3).ratio()

    def testInterval(self):
        from music21 import corpus
        h = Hasher()
        s3 = corpus.parse('bwv66.6').parts[0]
        s4 = corpus.parse('bwv66.6').parts[0].transpose('M2')

        hashes3 = h.hash(s3)
        hashes4 = h.hash(s4)

        print difflib.SequenceMatcher(a=hashes3, b=hashes4).ratio()

        h.hashIntervalFromLastNote = True
        h.hashPitch = False

        hashes3 = h.hash(s3)
        hashes4 = h.hash(s4)

        print difflib.SequenceMatcher(a=hashes3, b=hashes4).ratio()
if __name__ == "__main__":
    import music21
    music21.mainTest(TestExternal) 
