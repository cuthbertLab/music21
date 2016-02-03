'''
Created on Jan 31, 2016

@author: Emily
'''
from music21 import interval
import copy
import unittest

class OMRMidiNoteFixer(object):
    '''
    Fixes OMR stream according to MIDI information
    '''
    def __init__(self, omrstream, midistream):
        self.omrstream = omrstream
        self.midistream = midistream
        self.correctedstream = copy.deepcopy(self.omrstream)
    
    def fixStreams(self):
        self.alignstreams()
        for omrnote, midinote in zip(self.omrstream, self.midistream):
            fixerRhythm = OMRMidiNoteRhythmFixer(omrnote, midinote)
            fixerRhythm.fix()
            fixerPitch = OMRMidiNotePitchFixer(omrnote, midinote)
            fixerPitch.fix()
    
    def alignStreams(self):
        if self.approxequal(self.omrstream.highestTime, self.midistream.highestTime):
            pass
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
                self.omrnote.accidental = None
            if len(self.measure_accidentals) == 0:
                self.omrnote.accidental = self.midinote.accidental
                
            else:
                self.measure_accidentals.append(self.omrnote.pitch)
        elif self.hasSharpFlatAcc() and self.stepEq():
            if self.hasAcc():
                self.omrnote.accidental = self.midinote.accidental
            else: 
                self.omrnote.accidental = None

    def isEnharmonic(self):
        return self.omrnote.pitch.isEnharmonic(self.midinote.pitch)

    def hasAcc(self):
        return self.omrnote.accidental is not None

    def hasNatAcc(self):
        return self.hasAcc() and self.omrnote.accidental.name == "natural"

    def hasSharpFlatAcc(self):
        return self.hasAcc() and self.omrnote.accidental.name != "natural"

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
       
        midinote.accidental = pitch.Accidental('sharp')
        
        self.assertEqual(omrnote.nameWithOctave, 'B-4')
        self.assertEqual(midinote.nameWithOctave, 'B#4')


    def failing_testNotSameStep(self):
        from music21 import note
        omrnote = note.Note('En4')
        midinote = note.Note('B-4')
    
        self.assertIsNotNone(omrnote.pitch.accidental)
    
        fixer = OMRMidiNotePitchFixer(omrnote, midinote)
        fixer.fix()
        self.assertEqual(omrnote.nameWithOctave, 'E4')
        self.assertEqual(midinote.nameWithOctave, 'B-4')
        self.assertTrue(fixer.isPossiblyMisaligned)



if __name__ == '__main__':
    import music21
    music21.mainTest(Test)