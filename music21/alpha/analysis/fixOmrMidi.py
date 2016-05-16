# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         alpha/analysis/fixOmrMidi.py
# Purpose:      use MIDI score data to fix OMR scores
#
# Authors:      Emily Zhang
#
# Copyright:    Copyright © 2013-16 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

from music21 import note
from music21 import interval
from music21.alpha.analysis import hash
from music21.common import numberTools

import copy
import numpy as np
import unittest
import os
import inspect

pathName = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

K525xmlShortPath = pathName + os.sep + 'k525short3.xml'
K525midiShortPath = pathName + os.sep + 'k525short.mid'
K525omrShortPath = pathName + os.sep + 'k525omrshort.xml'

class StreamAligner(object):
    
    def __init__(self, stream1, stream2):
        self.stream1 = stream1
        self.stream2 = stream2
        
        h = hash.Hasher()
        self.hashedStream1 = h.hash(self.stream1)
        self.hashedStream2 = h.hash(self.stream2)
    
    
    def align(self):
        len1 = len(self.hashedStream1)-1
        len2 = len(self.hashedStream2)-1
        
        # create edit distance matrix
        dist_table = np.zeros(len1, len2)
        dist_table[0][0] = 0
        for i in range(len1+1):
            dist_table[0][i] = -1 * i
        for j in range(len2+1):
            dist_table[0][j] = -1 * j
            
        for idx1, tup1 in enumerate(self.hashedStream1, start=1):
            for idx2, tup2 in enumerate(self.hashedStream2, start=1):
                dist_table[idx1][idx2] = max([dist_table[idx1-1][idx2]-1, 
                                              dist_table[idx1][idx2-1]-1, 
                                              dist_table[idx1-1][idx2-2]+self.costFunction(tup1, tup2)])
                
               
    
    def costFunction(self, hashedItem1, hashedItem2):
        total = 0.
        for idx, item in enumerate(hashedItem1):
            if hashedItem2[idx] == hashedItem1:
                total += 2
            elif type(item) is float or type(item) is int:
                if numberTools.almostEquals(item, hashedItem2[idx], grain=.01):
                    total +=1
            else:
                total -= 1

class OMRmidiNoteFixer(object):
    '''
    Fixes OMR stream according to MIDI information
    '''
    def __init__(self, omrStream, midiStream):
        self.omrStream = omrStream
        self.midiStream = midiStream
        self.correctedStream = copy.deepcopy(self.omrStream)
        
        self.bassDoublesCello = False
    
    def fixStreams(self):
        if self.check_parts():
            pass

        for omrNote, midiNote in zip(self.omrStream, self.midiStream):
            fixerRhythm = OMRmidiNoteRhythmFixer(omrNote, midiNote)
            fixerRhythm.fix()
            fixerPitch = OMRmidiNotePitchFixer(omrNote, midiNote)
            fixerPitch.fix()
    
    def check_parts(self):
        num_midi_parts = len(self.midiStream.parts)
        num_omr_parts = len(self.omrStream.parts)
        
        
        if num_midi_parts == num_omr_parts:
            if num_midi_parts == num_omr_parts + 1:
                if self.check_bass_doubles_cello():
                    return True
                
        else:
            return False
    
    def checkBassDoublesCello(self):
        '''
        check if Bass part doubles Cello 
        '''
        # assume bass part is last part
        bassPart = self.midiStream [-1]
        # assume cello part is penultimate part
        celloPart = self.midiStream[-2]
        
        h = hash.Hasher()
        h.validTypes = [note.Note, note.Rest]
        h.validTypes = [note.Note, note.Rest]
        h.hashMIDI = False
        h.hashNoteName = True
        hashBass = h.hash(bassPart)
        hashCello = h.hash(celloPart)
        self.bassDoublesCello = hashBass == hashCello
        return self.bassDoublesCello
        
    
    def alignStreams(self):

        '''
        try a variety of mechanisms to get midiStream to align with omrStream
        '''
        #if self.approxequal(self.omrStream.highestTime, self.midiStream.highestTime):
        #    pass

        # TODO: more ways of checking if stream is aligned
        
        # find the part that aligns the best? or assume already aligned?
        part_pairs = {}
        for omr_part_index, omr_part in enumerate(self.omrStream):
            midi_part = omr_part_index, self.midiStream(omr_part_index)
            part_pairs[omr_part_index] = (omr_part, midi_part)
            
            
        pass
    
    def cursoryCheck(self):
        '''
        check if both rhythm and pitch are close enough together
        '''
        pass
    
class OMRmidiNoteRhythmFixer(object):
    '''
    Fixes an OMR Note pitch according to information from MIDI Note
    '''
    
    def __init__(self, omrNote, midiNote):
        self.omrNote = omrNote
        self.midiNote = midiNote
        self.isPossiblyMisaligned = False
        
    def fix(self):
        pass
    
    
class OMRmidiNotePitchFixer(object):
    '''
    Fixes an OMR Note pitch according to information from MIDI Note
    '''

    def __init__(self, omrNote, midiNote):
        self.omrNote = omrNote
        self.midiNote = midiNote
        self.measure_accidentals = []
        self.isPossiblyMisaligned = False 

    def fix(self):
        # keySignature = self.omrNote.getContextByClass('KeySignature')
        # curr_measure = self.midiNote.measureNumber
        if self.intervalTooBig(self.omrNote, self.midiNote):
            self.isPossiblyMisaligned = True
        else:    
            self.setOMRacc()

    def setOMRacc(self):
        if self.isEnharmonic():
            pass

        if self.hasNatAcc():
            if self.isEnharmonic():
                self.omrNote.pitch.accidental= None
            if len(self.measure_accidentals) == 0:
                self.omrNote.pitch.accidental= self.midiNote.pitch.accidental         
            else:
                self.measure_accidentals.append(self.omrNote.pitch)
        elif self.hasSharpFlatAcc() and self.stepEq():
            if self.hasAcc():
                self.omrNote.pitch.accidental= self.midiNote.pitch.accidental
            else: 
                self.omrNote.pitch.accidental= None

    def isEnharmonic(self):
        return self.omrNote.pitch.isEnharmonic(self.midiNote.pitch)

    def hasAcc(self):
        return self.omrNote.pitch.accidental is not None

    def hasNatAcc(self):
        return self.hasAcc() and self.omrNote.pitch.accidental.name == "natural"

    def hasSharpFlatAcc(self):
        return self.hasAcc() and self.omrNote.pitch.accidental.name != "natural"

    def stepEq(self):
        return self.omrNote.step == self.midiNote.step
    
    def intervalTooBig(self, aNote, bNote, setint = 5):
        if interval.notesToChromatic(aNote, bNote).intervalClass > setint:
            return True
        return False

class Test(unittest.TestCase):
    def testEnharmonic(self):
        from music21 import note
        omrNote = note.Note('A#4')
        midiNote = note.Note('B-4')
    
        fixer = OMRmidiNotePitchFixer(omrNote, midiNote)
        fixer.fix()
        self.assertEqual(omrNote.nameWithOctave, 'A#4')
        self.assertEqual(midiNote.nameWithOctave, 'B-4')

    def testSameStep(self):
        from music21 import note, pitch
        omrNote = note.Note('Bn4')
        midiNote = note.Note('B-4')
        self.assertEqual(omrNote.nameWithOctave, 'B4')
        self.assertIsNotNone(omrNote.pitch.accidental)
    
        fixer = OMRmidiNotePitchFixer(omrNote, midiNote)
        fixer.fix()
        
        self.assertEqual(omrNote.nameWithOctave, 'B-4')
        self.assertEqual(midiNote.nameWithOctave, 'B-4')
       
        midiNote.pitch.accidental= pitch.Accidental('sharp')

        
        self.assertEqual(omrNote.nameWithOctave, 'B-4')
        self.assertEqual(midiNote.nameWithOctave, 'B#4')


    def testIntervalNotTooBig(self):
        from music21 import note
        omrNote = note.Note('G-4')
        midiNote = note.Note('A#4')
    
        self.assertIsNotNone(omrNote.pitch.accidental)
    
        fixer = OMRmidiNotePitchFixer(omrNote, midiNote)
        fixer.fix()
        self.assertEqual(omrNote.nameWithOctave, 'G-4')
        self.assertEqual(midiNote.nameWithOctave, 'A#4')
        self.assertFalse(fixer.isPossiblyMisaligned)
        
    def testNotSameStep(self):
        from music21 import note
        omrNote = note.Note('En4')
        midiNote = note.Note('B-4')
    
        self.assertIsNotNone(omrNote.pitch.accidental)
        fixer = OMRmidiNotePitchFixer(omrNote, midiNote)
        fixer.fix()
        self.assertEqual(omrNote.nameWithOctave, 'E4')
        self.assertEqual(midiNote.nameWithOctave, 'B-4')
        self.assertTrue(fixer.isPossiblyMisaligned)
        
    def testK525BassCelloDouble(self):
        from music21 import converter
        from music21.alpha.analysis import hash
        
        midiFP = K525midiShortPath
        omrFP = K525omrShortPath
        midiStream = converter.parse(midiFP)
        omrStream = converter.parse(omrFP)
        
        fixer = OMRmidiNoteFixer(omrStream, midiStream)
        celloBassAnalysis = fixer.checkBassDoublesCello()
        self.assertEqual(celloBassAnalysis, True)
#         h = hash.Hasher()
#         h.validTypes = [note.Note, note.Rest]
#         h.hashMIDI = False
#         h.hashNoteName = True
#         hashBass = h.hash(bassPart)
#         hashCello = h.hash(celloPart)
#         self.assertEqual(hashBass, hashCello)


## this test is included in the quarterLengthDivisor PR in the converter.py tests
# class ParseTestExternal(unittest.TestCase):
#     def testParseMidi(self):
#         from music21 import converter
#         midiStream = converter.parse(K525midiShortPath, forceSource=True, quarterLengthDivisors=[4])
#         midiStream.show()

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)