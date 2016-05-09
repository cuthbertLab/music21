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

import copy
import unittest
import os
import inspect
import itertools

pathName = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

K525xmlShortPath = pathName + os.sep + 'k525short3.xml'
K525midiShortPath = pathName + os.sep + 'k525short.mid'
K525omrShortPath = pathName + os.sep + 'k525omrshort.xml'


class OMRMidiNoteFixer(object):
    '''
    Fixes OMR stream according to MIDI information
    '''
    def __init__(self, omrstream, midistream):
        self.omrstream = omrstream
        self.midistream = midistream
        self.correctedstream = copy.deepcopy(self.omrstream)
    
    def fixStreams(self):
        if self.check_parts():
            self.alignStreams()

        for omrnote, midinote in zip(self.omrstream, self.midistream):
            fixerRhythm = OMRMidiNoteRhythmFixer(omrnote, midinote)
            fixerRhythm.fix()
            fixerPitch = OMRMidiNotePitchFixer(omrnote, midinote)
            fixerPitch.fix()
    
    def check_parts(self):
        num_midi_parts = len(self.midistream.parts)
        num_omr_parts = len(self.omrstream.parts)
        
        if num_midi_parts == num_omr_parts:
            if num_midi_parts == num_omr_parts + 1:
                if self.check_bass_doubles_cello():
                    return True
                
        else:
            return False
    
    def checkBassDoublesCello(self):
        # assume bass part is last part
        bassPart = self.midistream [-1]
        # assume cello part is penultimate part
        celloPart = self.midistream[-2]
        
        h = hash.Hasher()
        h.validTypes = [note.Note, note.Rest]
        h.validTypes = [note.Note, note.Rest]
        h.hashMIDI = False
        h.hashNoteName = True
        hashBass = h.hash(bassPart)
        hashCello = h.hash(celloPart)
        return hashBass == hashCello
        
    
    def alignStreams(self):

        '''
        try a variety of mechanisms to get midistream to align with omrstream
        '''
        #if self.approxequal(self.omrstream.highestTime, self.midistream.highestTime):
        #    pass

        # TODO: more ways of checking if stream is aligned 
        pass
    
    def cursoryCheck(self):
        '''
        check if both rhythm and pitch are close enough together
        '''
        pass
    
class OMRMidiNoteRhythmFixer(object):
    '''
    Fixes an OMR Note pitch according to information from MIDI Note
    '''
    
    def __init__(self, omrnote, midinote):
        self.omrnote = omrnote
        self.midinote = midinote
        self.isPossiblyMisaligned = False
        
    def fix(self):
        pass
    
    
class OMRMidiNotePitchFixer(object):
    '''
    Fixes an OMR Note pitch according to information from MIDI Note
    '''

    def __init__(self, omrnote, midinote):
        self.omrnote = omrnote
        self.midinote = midinote
        self.measure_accidentals = []
        self.isPossiblyMisaligned = False 

    def fix(self):
        # keySignature = self.omrnote.getContextByClass('KeySignature')
        # curr_measure = self.midinote.measureNumber
        if self.intervalTooBig(self.omrnote, self.midinote):
            self.isPossiblyMisaligned = True
        else:    
            self.setOMRacc()

    def setOMRacc(self):
        if self.isEnharmonic():
            pass

        if self.hasNatAcc():
            if self.isEnharmonic():
                self.omrnote.pitch.accidental= None
            if len(self.measure_accidentals) == 0:
                self.omrnote.pitch.accidental= self.midinote.pitch.accidental         
            else:
                self.measure_accidentals.append(self.omrnote.pitch)
        elif self.hasSharpFlatAcc() and self.stepEq():
            if self.hasAcc():
                self.omrnote.pitch.accidental= self.midinote.pitch.accidental
            else: 
                self.omrnote.pitch.accidental= None

    def isEnharmonic(self):
        return self.omrnote.pitch.isEnharmonic(self.midinote.pitch)

    def hasAcc(self):
        return self.omrnote.pitch.accidental is not None

    def hasNatAcc(self):
        return self.hasAcc() and self.omrnote.pitch.accidental.name == "natural"

    def hasSharpFlatAcc(self):
        return self.hasAcc() and self.omrnote.pitch.accidental.name != "natural"

    def stepEq(self):
        return self.omrnote.step == self.midinote.step
    
    def intervalTooBig(self, aNote, bNote, setint = 5):
        if interval.notesToChromatic(aNote, bNote).intervalClass > setint:
            return True
        return False

class Test(unittest.TestCase):
    def testEnharmonic(self):
        from music21 import note
        omrnote = note.Note('A#4')
        midinote = note.Note('B-4')
    
        fixer = OMRMidiNotePitchFixer(omrnote, midinote)
        fixer.fix()
        self.assertEqual(omrnote.nameWithOctave, 'A#4')
        self.assertEqual(midinote.nameWithOctave, 'B-4')

    def testSameStep(self):
        from music21 import note, pitch
        omrnote = note.Note('Bn4')
        midinote = note.Note('B-4')
        self.assertEqual(omrnote.nameWithOctave, 'B4')
        self.assertIsNotNone(omrnote.pitch.accidental)
    
        fixer = OMRMidiNotePitchFixer(omrnote, midinote)
        fixer.fix()
        
        self.assertEqual(omrnote.nameWithOctave, 'B-4')
        self.assertEqual(midinote.nameWithOctave, 'B-4')
       
        midinote.pitch.accidental= pitch.Accidental('sharp')

        
        self.assertEqual(omrnote.nameWithOctave, 'B-4')
        self.assertEqual(midinote.nameWithOctave, 'B#4')


    def testIntervalNotTooBig(self):
        from music21 import note
        omrnote = note.Note('G-4')
        midinote = note.Note('A#4')
    
        self.assertIsNotNone(omrnote.pitch.accidental)
    
        fixer = OMRMidiNotePitchFixer(omrnote, midinote)
        fixer.fix()
        self.assertEqual(omrnote.nameWithOctave, 'G-4')
        self.assertEqual(midinote.nameWithOctave, 'A#4')
        self.assertFalse(fixer.isPossiblyMisaligned)
        
    def testNotSameStep(self):
        from music21 import note
        omrnote = note.Note('En4')
        midinote = note.Note('B-4')
    
        self.assertIsNotNone(omrnote.pitch.accidental)
        fixer = OMRMidiNotePitchFixer(omrnote, midinote)
        fixer.fix()
        self.assertEqual(omrnote.nameWithOctave, 'E4')
        self.assertEqual(midinote.nameWithOctave, 'B-4')
        self.assertTrue(fixer.isPossiblyMisaligned)
        
    def testK525BassCelloDouble(self):
        from music21 import converter
        from music21.alpha.analysis import hash
        
        midiFP = K525midiShortPath
        omrFP = K525omrShortPath
        midistream = converter.parse(midiFP)
        omrstream = converter.parse(omrFP)
        
        fixer = OMRMidiNoteFixer(omrstream, midistream)
        celloBassAnalysis = fixer.checkBassDoublesCello()
        self.assertEqual(celloBassAnalysis, True)
#         h = hash.Hasher()
#         h.validTypes = [note.Note, note.Rest]
#         h.hashMIDI = False
#         h.hashNoteName = True
#         hashBass = h.hash(bassPart)
#         hashCello = h.hash(celloPart)
#         self.assertEqual(hashBass, hashCello)

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)