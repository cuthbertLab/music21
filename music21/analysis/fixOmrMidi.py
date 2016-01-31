'''
Created on Jan 31, 2016

@author: Emily
'''

import unittest

class OMRMidiNotePitchFixer(object):
    '''
    Fixes an OMRNote according to information from MIDI Note
    '''

    def __init__(self, omrnote, midinote):
        self.omrnote = omrnote
        self.midinote = midinote
        self.measure_accidentals = []
        self.isPossiblyMisaligned = False 

    def fix(self):
        # keySignature = self.omrnote.getContextByClass('KeySignature')
        # curr_measure = self.midinote.measureNumber

        self.setOMRacc()

    def setOMRacc(self):
        if self._isEnharmonic():
            pass

        if self._hasNatAcc():
            if self._isEnharmonic():
                self.omrnote.accidental = None
            if len(self.measure_accidentals) == 0:
                self.omrnote.accidental = self.midinote.accidental
            # fix this, reference to outside of class 
            # measure_accidentals.append(self.omrnote.pitch)
            else:
                # append to measure_accidentals
                pass
        elif self._hasSharpFlatAcc() and self._stepEq():
            if self._hasAcc():
                self.omrnote.accidental = self.midinote.accidental
            else: 
                self.omrnote.accidental = None

    def _isEnharmonic(self):
        return self.omrnote.pitch.isEnharmonic(self.midinote.pitch)

    def _hasAcc(self):
        return self.omrnote.accidental is not None

    def _hasNatAcc(self):
        return self._hasAcc() and self.omrnote.accidental.name == "natural"

    def _hasSharpFlatAcc(self):
        return self._hasAcc() and self.omrnote.accidental.name != "natural"

    def _stepEq(self):
        return self.omrnote.step == self.midinote.step
        #score = omrnote.ActiveSite

# 
# for midinote, omrnote in zip(gtMIDI.recurse(classFilter='Note'), gtOMR.recurse(classFilter='Note')):
#     if omrnote != midinote:
#         newFix = OMRMidiNotePitchFixer(omrnote, midinote)
#         newFix.fix()

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