# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         alpha/analysis/fixer.py
# Purpose:      Fixes two streams given a list of changes between them
#
# Authors:      Emily Zhang
#
# Copyright:    Copyright © 2016 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
import unittest

from music21.alpha.analysis import aligner
from music21 import interval
from music21 import note
from music21 import pitch
from music21 import stream

class OMRMidiFixer:
    '''
    Base class for future fixers
    changes is a list of changes associated with the midiStream and omrStream, 
    not a list of lists
    '''
    def __init__(self, changes, midiStream, omrStream):
        self.changes = changes
        self.midiStream = midiStream
        self.omrStream = omrStream
    
    def checkIfNoteInstance(self, midiRef, omrRef):
        if isinstance(midiRef, note.Note) and isinstance(omrRef, note.Note):
            return True
        return False
    
class DeleteFixer(OMRMidiFixer):
    '''
    CAUTION: this does really weird things still.
    Deletes measure that have wrong things in them a la OpenScore specs
    
    '''
    def fix(self):
        for (midiRef, omrRef, op) in self.changes:
            if self.checkIfNoteInstance(midiRef, omrRef) is False:
                continue
            # if the are the same, don't bother to try changing it
            # 3 is the number of noChange Ops
            if isinstance(op, aligner.ChangeOps) and op == aligner.ChangeOps.NoChange:
                continue
             
            m = omrRef.getContextByClass(stream.Measure)
            self.omrStream.remove(m)
    
class EnharmonicFixer(OMRMidiFixer):
    '''
    Fixes incorrectly spelled enharmonics
    initialized with self.changes -- a list of tuples in this form:
    (MIDIReference, OMRReference, op)
    MIDIReference and OMRReference are actual note/rest/chord object in some stream
    op is a ChangeOp that relates the two references
    
    TEST 1, no changes in omr stream

    >>> omrStream1 = stream.Stream()
    >>> midiStream1 = stream.Stream()
          
    >>> omrNote1 = note.Note('A#4')
    >>> omrNote2 = note.Note('A#4')
    >>> midiNote1 = note.Note('B-4')
    >>> midiNote2 = note.Note('B-4')
          
    >>> omrStream1.append([omrNote1, omrNote2])
    >>> midiStream1.append([midiNote1, midiNote2])
    >>> subOp = alpha.analysis.aligner.ChangeOps.Substitution
     
    >>> ct1 = (midiNote1, omrNote1, subOp)
    >>> ct2 = (midiNote2, omrNote2, subOp)
    >>> changes1 = [ct1, ct2]
     
    >>> fixer1 = alpha.analysis.fixer.EnharmonicFixer(changes1, None, None)
    >>> fixer1.fix()
    >>> omrStream1[0]
    <music21.note.Note A#>
    >>> omrStream1[1]
    <music21.note.Note A#>
     
     
    TEST 2, no changes in omr stream

    >>> omrStream2 = stream.Stream()
    >>> midiStream2 = stream.Stream()
          
    >>> omr2Note1 = note.Note('A#4')
    >>> omr2Note2 = note.Note('A#4')
    >>> midi2Note1 = note.Note('A#4')
    >>> midi2Note2 = note.Note('A#4')
          
    >>> omrStream2.append([omr2Note1, omr2Note2])
    >>> midiStream2.append([midi2Note1, midi2Note2])
    >>> ncOp = alpha.analysis.aligner.ChangeOps.NoChange
     
    >>> ct2_1 = (midi2Note1, omr2Note1, ncOp)
    >>> ct2_2 = (midi2Note2, omr2Note2, ncOp)
    >>> changes2 = [ct2_1, ct2_2]
     
    >>> fixer2 = alpha.analysis.fixer.EnharmonicFixer(changes2, None, None)
    >>> fixer2.fix()
    >>> omrStream2[0]
    <music21.note.Note A#>
    >>> omrStream1[1]
    <music21.note.Note A#>
     
    
    TEST 3 (case 1)
    
    >>> midiNote3 = note.Note('A4')
    >>> omrNote3 = note.Note('An4')
         
    >>> subOp = alpha.analysis.aligner.ChangeOps.Substitution
     
    >>> ct3 = (midiNote3, omrNote3, subOp)
    >>> changes3 = [ct3]
    >>> omrNote3.pitch.accidental
    <accidental natural>
    >>> fixer3 = alpha.analysis.fixer.EnharmonicFixer(changes3, None, None)
    >>> fixer3.fix()
    >>> omrNote3.pitch.accidental
     
    
    TEST 4 (case 2-1) e.g midi = g#, gt = a-, omr = an
    
    >>> midiNote4 = note.Note('G#4')
    >>> omrNote4 = note.Note('An4')
         
    >>> subOp = alpha.analysis.aligner.ChangeOps.Substitution
     
    >>> ct4 = (midiNote4, omrNote4, subOp)
    >>> changes4 = [ct4]
    >>> omrNote4.pitch.accidental
    <accidental natural>
    >>> fixer4 = alpha.analysis.fixer.EnharmonicFixer(changes4, None, None)
    >>> fixer4.fix()
    >>> omrNote4.pitch.accidental
    <accidental flat>
    
    
    TEST 5 (case 2-2) e.g midi = g-, gt = f#, omr = fn
    
    >>> midiNote5 = note.Note('G-4')
    >>> omrNote5 = note.Note('Fn4')
        
    >>> subOp = alpha.analysis.aligner.ChangeOps.Substitution
    
    >>> ct5 = (midiNote5, omrNote5, subOp)
    >>> changes5 = [ct5]
    >>> omrNote5.pitch.accidental
    <accidental natural>
    >>> fixer5 = alpha.analysis.fixer.EnharmonicFixer(changes5, None, None)
    >>> fixer5.fix()
    >>> omrNote5.pitch.accidental
    <accidental sharp>
    
    
    TEST 6.1 (case 3) e.g. midi = g#, gt = g#, omr = gn or omr = g-
    
    >>> midiNote6_1 = note.Note('G#4')
    >>> midiNote6_2 = note.Note('G#4')
    >>> omrNote6_1 = note.Note('Gn4')
    >>> omrNote6_2 = note.Note('G-4')
        
    >>> subOp6_1 = alpha.analysis.aligner.ChangeOps.Substitution
    >>> subOp6_2 = alpha.analysis.aligner.ChangeOps.Substitution
    >>> ct6_1 = (midiNote6_1, omrNote6_1, subOp6_1)
    >>> ct6_2 = (midiNote6_2, omrNote6_2, subOp6_2)
    >>> changes6 = [ct6_1, ct6_2]
    
    >>> omrNote6_1.pitch.accidental
    <accidental natural>
    >>> omrNote6_2.pitch.accidental
    <accidental flat>
    >>> fixer6 = alpha.analysis.fixer.EnharmonicFixer(changes6, None, None)
    >>> fixer6.fix()
    >>> omrNote6_1.pitch.accidental
    <accidental sharp>
    >>> omrNote6_2.pitch.accidental
    <accidental sharp>
    
    
    TEST 7 (case 4-1, 4-2) notes are on different step, off by an interval of 2,
    * 4-1: e.g. midi = g#, gt = a-, omr = a#
    * 4-2: e.g. midi = a-, gt = g#, omr = g-
    
    >>> midiNote7_1 = note.Note('G#4')
    >>> omrNote7_1 = note.Note('A#4')
    
    >>> midiNote7_2 = note.Note('A-4')
    >>> omrNote7_2 = note.Note('G-4')
        
    >>> subOp7_1 = alpha.analysis.aligner.ChangeOps.Substitution
    >>> subOp7_2 = alpha.analysis.aligner.ChangeOps.Substitution
    >>> ct7_1 = (midiNote7_1, omrNote7_1, subOp7_1)
    >>> ct7_2 = (midiNote7_2, omrNote7_2, subOp7_2)
    >>> changes7 = [ct7_1, ct7_2]
    
    >>> omrNote7_1.pitch.accidental
    <accidental sharp>
    >>> omrNote7_2.pitch.accidental
    <accidental flat>
    >>> fixer7 = alpha.analysis.fixer.EnharmonicFixer(changes7, None, None)
    >>> fixer7.fix()
    
    >>> omrNote7_1.pitch.step
    'A'
    >>> omrNote7_1.pitch.accidental
    <accidental flat>
    
    >>> omrNote7_2.pitch.step
    'G'
    >>> omrNote7_2.pitch.accidental
    <accidental sharp>
    '''
    def fix(self):
        for (midiRef, omrRef, op) in self.changes:
            omrRef.color = "black"
            #if they're not notes, don't bother with rest
            if self.checkIfNoteInstance(midiRef, omrRef) is False:
                continue
            # if the are the same, don't bother to try changing it
            # 3 is the number of noChange Ops
            if isinstance(op, aligner.ChangeOps) and op == aligner.ChangeOps.NoChange:
                continue
            
            # don't bother with notes with too big of an interval between them
            if self.intervalTooBig(midiRef, omrRef, setint=5):
                continue
            # case 1: omr has extraneous natural sign in front of it, get rid of it
            if self.hasNatAcc(omrRef):
                if self.isEnharmonic(midiRef, omrRef):
                    omrRef.pitch.accidental = None
                else: 
                    # case 2-1: midi note is sharp, omr note is one step higher and natural,
                    # should be a flat instead. e.g midi = g#, gt = a-, omr = an
                    # omr note has higher ps than midi-- on a higher 
                    # line or space than midi note
                    if omrRef.pitch > midiRef.pitch:
                        if omrRef.pitch.transpose(interval.Interval(-1)
                                                  ).isEnharmonic(midiRef.pitch):
                            omrRef.pitch.accidental = pitch.Accidental('flat')
                    # case 2-2: midi note is flat, omr note is one step lower and natural,
                    # should be a flat instead. e.g midi = g-, gt = f#, omr = fn
                    # omr note has lower ps than midi-- on a higher line 
                    # or space than midi note
                    elif omrRef.pitch < midiRef.pitch:
                        if omrRef.pitch.transpose(interval.Interval(1)
                                                  ).isEnharmonic(midiRef.pitch):
                            omrRef.pitch.accidental = pitch.Accidental('sharp')
            # case 3: notes are on same step, but omr got read wrong. 
            # e.g. midi = g#, gt = g#, omr = gn or omr = g-
            elif self.hasSharpFlatAcc(omrRef) and self.stepEq(midiRef, omrRef):
                if self.hasAcc(omrRef):
                    omrRef.pitch.accidental = midiRef.pitch.accidental
                else: 
                    omrRef.pitch.accidental = None
                    
            elif self.hasSharpFlatAcc(omrRef) and self.stepNotEq(midiRef, omrRef):
                # case 4-1: notes are on different step, off by an interval of 2,
                # omr note is higher and sharp
                # e.g. midi = g#, gt = a-, omr = a#
                if omrRef.pitch > midiRef.pitch:
                    if omrRef.pitch.accidental == pitch.Accidental('sharp'):
                        if omrRef.pitch.transpose(interval.Interval(-2)
                                                  ).isEnharmonic(midiRef.pitch):
                            omrRef.pitch.accidental = pitch.Accidental('flat')
                # case 4-2: notes are on different step, off by an interval of 2,
                # omr note is lower and flat
                # e.g. midi = a-, gt = g#, omr = g-
                elif omrRef.pitch < midiRef.pitch:
                    if omrRef.pitch.accidental == pitch.Accidental('flat'):
                        if omrRef.pitch.transpose(interval.Interval(2)
                                                  ).isEnharmonic(midiRef.pitch):
                            omrRef.pitch.accidental = pitch.Accidental('sharp')
            # case 5: same step, MIDI has accidental, 
            # omr was read wrong (e.g. key signture not parsed)
            # e.g. midi = b-, gt = b-, omr=
            elif (omrRef.pitch != midiRef.pitch 
                    and self.hasSharpFlatAcc(midiRef) 
                    and self.stepEq(midiRef, omrRef)):
                omrRef.pitch = midiRef.pitch
            
              
    def isEnharmonic(self, midiRef, omrRef):
        return midiRef.pitch.isEnharmonic(omrRef.pitch)
    
    def hasAcc(self, omrRef):
        return omrRef.pitch.accidental is not None
    
    def hasNatAcc(self, omrRef):
        return self.hasAcc(omrRef) and omrRef.pitch.accidental.name == "natural"
    
    def hasSharpFlatAcc(self, omrRef):
        return self.hasAcc(omrRef) and omrRef.pitch.accidental.name != "natural"
    
    def stepEq(self, midiRef, omrRef):
        return midiRef.step == omrRef.step
    
    def stepNotEq(self, midiRef, omrRef):
        return midiRef.step != omrRef.step
    
    def intervalTooBig(self, midiRef, omrRef, setint=5):
        if interval.notesToChromatic(midiRef, omrRef).intervalClass > setint:
            return True
        return False

class Test(unittest.TestCase):
    pass
        

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
    