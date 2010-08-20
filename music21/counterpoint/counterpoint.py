#!/usr/bin/python

'''
counterpoint -- set of tools for dealing with Species Counterpoint and 
later other forms of counterpoint.

Mostly coded by Jackie Rogoff -- some routines have been moved to
by VoiceLeadingQuartet, and that module should be used for future work
'''

import copy
import random
import unittest, doctest

import music21
from music21.note import Note
from music21 import converter
from music21 import duration
from music21 import interval
from music21 import meter
from music21 import lily
from music21 import scale

from music21 import stream
from music21.stream import Stream
from music21 import voiceLeading

class ModalCounterpointException(Exception):
    pass

class ModalCounterpoint(object):
    def __init__(self, stream1 = None, stream2 = None):
        self.stream1 = stream1
        self.stream2 = stream2
        self.legalHarmonicIntervals = ['P1', 'P5', 'P8', 'm3', 'M3', 'm6', 'M6']
        self.legalMelodicIntervals = ['P4', 'P5', 'P8', 'm2', 'M2', 'm3', 'M3', 'm6']

    def findParallelFifths(self, srcStream, cmpStream):
        '''Given two streams, returns the number of parallel fifths and also
        assigns a flag under note.editorial.misc under "Parallel Fifth" for
        any note that has harmonic interval of a fifth and is preceded by a
        first harmonic interval of a fifth.


        >>> from music21 import *
        >>> n1 = note.Note('G3')
        >>> n2 = note.Note('A3')
        >>> n3 = note.Note('B3')
        >>> n4 = note.Note('C4')
        >>> m1 = note.Note('D4')
        >>> m2 = note.Note('E4')
        >>> m3 = note.Note('F#4')
        >>> m4 = note.Note('G4')
        >>> bass = stream.Stream()
        >>> bass.append([n1, n2, n3, n4])
        >>> sop = stream.Stream()
        >>> sop.append([m1, m2, m3, m4])
        >>> cp = ModalCounterpoint(stream1 = bass, stream2 = sop)
        >>> cp.findParallelFifths(cp.stream1, cp.stream2)
        3
        >>> n1.editorial.harmonicInterval.name
        'P5'
        >>> m4.octave = 5 #checking for 12ths as well
        >>> cp.findParallelFifths(cp.stream1, cp.stream2)
        3
        
        '''
        
        srcStream.attachIntervalsBetweenStreams(cmpStream)
        numParallelFifths = 0
        srcNotes = srcStream.notes
        
        for note1 in srcStream:
            note2 = srcStream.getElementAfterElement(note1, [Note])
            if note2 is not None:
                if note1.editorial.harmonicInterval.semiSimpleName == "P5" and \
                   note2.editorial.harmonicInterval.semiSimpleName == "P5":
                        numParallelFifths += 1
                        note2.editorial.misc["Parallel Fifth"] = True
        return numParallelFifths

    def findHiddenFifths(self, stream1, stream2):
        '''Given two streams, returns the number of hidden fifths and also
        assigns a flag under note.editorial.misc under "Hidden Fifth" for
        any note that has harmonic interval of a fifth where it creates a
        hidden parallel fifth. Note: a hidden fifth here is defined as anything
        where the two streams reach a fifth through parallel motion, but is
        not a parallel fifth.


        >>> from music21 import *
        >>> n1 = note.Note('G3')
        >>> n2 = note.Note('A3')
        >>> n3 = note.Note('B3')
        >>> n4 = note.Note('C4')
        >>> m1 = note.Note('C4')
        >>> m2 = note.Note('E4')
        >>> m3 = note.Note('D4')
        >>> m4 = note.Note('G4')
        >>> bass = stream.Stream()
        >>> bass.append([n1, n2, n3, n4])
        >>> sop = stream.Stream()
        >>> sop.append([m1, m2, m3, m4])
        >>> cp = ModalCounterpoint(stream1 = bass, stream2 = sop)
        >>> cp.findHiddenFifths(cp.stream1, cp.stream2)
        2
        >>> n2.editorial.misc['Hidden Fifth']
        True
        >>> cp.findHiddenFifths(cp.stream2, cp.stream1)
        2

        '''
        numHiddenFifths = 0
        for i in range(len(stream1.notes)-1):
            note1 = stream1.notes[i]
            note2 = stream1.getElementAfterElement(note1, [Note])
            note3 = stream2.playingWhenAttacked(note1)
            note4 = stream2.playingWhenAttacked(note2)
            if note2 is not None and note3 is not None and note4 is not None:
                hidden = self.isHiddenFifth(note1, note2, note3, note4)
                if hidden:
                    numHiddenFifths += 1
                    note2.editorial.misc["Hidden Fifth"] = True
        return numHiddenFifths

    def isParallelFifth(self, note11, note12, note21, note22):
        '''Given four notes, assuming the first pair is one voice and
        the second pair is another voice sounding at the same time,
        returns True if the two harmonic intervals are P5 and False otherwise.
        

        >>> from music21 import *
        >>> n1 = note.Note('G3')
        >>> n2 = note.Note('B-3')
        >>> m1 = note.Note('D4')
        >>> m2 = note.Note('F4')
        >>> cp = ModalCounterpoint()
        >>> cp.isParallelFifth(n1, m1, n2, m2) #(n1, n2) and (m1, m2) are chords
        False
        >>> cp.isParallelFifth(n1, n2, m1, m2) #(n1, m1) and (n2, m2) are chords
        True
        >>> m1.octave = 5
        >>> m2.octave = 5 #test parallel 12ths
        >>> cp.isParallelFifth(n1, n2, m1, m2)
        True

        '''
        vlq = voiceLeading.VoiceLeadingQuartet(note11, note12, note21, note22)
        return vlq.parallelFifth()
#        interval1 = interval.notesToInterval(note11, note21)
#        interval2 = interval.notesToInterval(note12, note22)
#        if interval1.semiSimpleName == interval2.semiSimpleName == "P5": return True
#        else: return False

    def isHiddenFifth(self, note11, note12, note21, note22):
        '''Given four notes, assuming the first pair is one part and the
        second is another part sounding at the same time, returns True if
        there is a hidden fifth and false otherwise.
        

        >>> from music21 import *
        >>> n1 = note.Note('G3')
        >>> n2 = note.Note('B-3')
        >>> m1 = note.Note('E4')
        >>> m2 = note.Note('F4')
        >>> cp = ModalCounterpoint()
        >>> cp.isHiddenFifth(n1, m1, n2, m2) #(n1, n2) and (m1, m2) are chords
        False
        >>> cp.isHiddenFifth(n1, n2, m1, m2) #(n1, m1) and (n2, m2) are chords
        True
        >>> m1.octave = 5
        >>> m2.octave = 5 # check for hidden 12ths
        >>> cp.isHiddenFifth(n1, n2, m1, m2)
        True

        '''

        vlq = voiceLeading.VoiceLeadingQuartet(note11, note12, note21, note22)
        return vlq.hiddenFifth()
##        interval1 = interval.notesToInterval(note11, note21)
##        interval2 = interval.notesToInterval(note12, note22)
##        interval3 = interval.notesToInterval(note11, note12)
##        interval4 = interval.notesToInterval(note21, note22)
##        if interval3.direction > 0 and interval4.direction > 0:
##            if interval2.semiSimpleName == "P5" and not interval1.semiSimpleName == "P5":
##                return True
##            else:
##                return False
##        elif interval3.direction < 0 and interval4.direction < 0:
##            if interval2.semiSimpleName == "P5" and not interval1.semiSimpleName == "P5":
##                return True
##            else:
##                return False
##        elif interval3.direction == interval4.direction == 0: return False
##        return False

    def findParallelOctaves(self, stream1, stream2):
        '''Given two streams, returns the number of parallel octaves and also
        assigns a flag under note.editorial.misc under "Parallel Octave" for
        any note that has harmonic interval of an octave and is preceded by a
        harmonic interval of an octave.

        >>> from music21 import *
        >>> n1 = note.Note('G3')
        >>> n2 = note.Note('A3')
        >>> n3 = note.Note('B3')
        >>> n4 = note.Note('C4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('A4')
        >>> m3 = note.Note('B4')
        >>> m4 = note.Note('C5')
        >>> bass = stream.Stream()
        >>> bass.append([n1, n2, n3, n4])
        >>> sop = stream.Stream()
        >>> sop.append([m1, m2, m3, m4])
        >>> cp = ModalCounterpoint(stream1 = bass, stream2 = sop)
        >>> cp.findParallelOctaves(cp.stream1, cp.stream2)
        3
        >>> n2.editorial.misc['Parallel Octave']
        True
        >>> cp.findParallelOctaves(cp.stream2, cp.stream1)
        3
        >>> m3.octave = 5
        >>> m4.octave = 6 #check for parallel 17ths
        >>> cp.findParallelOctaves(cp.stream2, cp.stream1)
        3

        '''
        stream1.attachIntervalsBetweenStreams(stream2)
        stream2.attachIntervalsBetweenStreams(stream1)

        numParallelOctaves = 0
        for note1 in stream1:
            note2 = stream1.getElementAfterElement(note1, [Note])
            if note2 is not None:
                if note1.editorial.harmonicInterval.semiSimpleName == "P8":
                    if note2.editorial.harmonicInterval.semiSimpleName == "P8":
                        numParallelOctaves += 1
                        note2.editorial.misc["Parallel Octave"] = True
        for note1 in stream2:
            note2 = stream2.getElementAfterElement(note1, [Note])
            if note2 is not None:
                if note1.editorial.harmonicInterval.semiSimpleName == "P8":
                    if note2.editorial.harmonicInterval.semiSimpleName == "P8":
                        note2.editorial.misc["Parallel Octave"] = True
        return numParallelOctaves

    def findHiddenOctaves(self, stream1, stream2):
        '''Given two streams, returns the number of hidden octaves and also
        assigns a flag under note.editorial.misc under "Hidden Octave" for
        any note that has harmonic interval of an octave where it creates a
        hidden parallel octave. Note: a hidden octave here is defined as
        anything where the two streams reach an octave through parallel motion,
        but is not a parallel octave.
        

        >>> from music21 import *
        >>> n1 = note.Note('F3')
        >>> n2 = note.Note('A3')
        >>> n3 = note.Note('A3')
        >>> n4 = note.Note('C4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('A4')
        >>> m3 = note.Note('B4')
        >>> m4 = note.Note('C5')
        >>> bass = stream.Stream()
        >>> bass.append([n1, n2, n3, n4])
        >>> sop = stream.Stream()
        >>> sop.append([m1, m2, m3, m4])
        >>> cp = ModalCounterpoint(stream1 = bass, stream2 = sop)
        >>> cp.findHiddenOctaves(cp.stream1, cp.stream2)
        2
        >>> n2.editorial.misc['Hidden Octave']
        True
        >>> cp.findHiddenOctaves(cp.stream2, cp.stream1)
        2
        >>> m4.octave = 6
        >>> cp.findHiddenOctaves(cp.stream2, cp.stream1)
        2

        '''
        numHiddenOctaves = 0
        for i in range(len(stream1.notes)-1):
            note1 = stream1.notes[i]
            note2 = stream1.getElementAfterElement(note1, [Note])
            note3 = stream2.playingWhenAttacked(note1)
            note4 = stream2.playingWhenAttacked(note2)
            if note2 is not None and note3 is not None and note4 is not None:
                hidden = self.isHiddenOctave(note1, note2, note3, note4)
                if hidden:
                    numHiddenOctaves += 1
                    note2.editorial.misc["Hidden Octave"] = True
        return numHiddenOctaves

    def isParallelOctave(self, note11, note12, note21, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if the two
        harmonic intervals are P8 and False otherwise.


        >>> from music21 import *
        >>> n1 = note.Note('A3')
        >>> n2 = note.Note('B-3')
        >>> m1 = note.Note('A4')
        >>> m2 = note.Note('B-4')
        >>> cp = ModalCounterpoint()
        >>> cp.isParallelOctave(n1, m1, n2, m2) #(n1, n2) and (m1, m2) are chords
        False
        >>> cp.isParallelOctave(n1, n2, m1, m2) #(n1, m1) and (n2, m2) are chords
        True
        >>> m1.octave = 5
        >>> m2.octave = 5
        >>> cp.isParallelOctave(n1, n2, m1, m2)
        True

        '''
        vlq = voiceLeading.VoiceLeadingQuartet(note11, note12, note21, note22)
        return vlq.parallelOctave()
##        interval1 = interval.notesToInterval(note11, note21)
##        interval2 = interval.notesToInterval(note12, note22)
##        if interval1.semiSimpleName == interval2.semiSimpleName == "P8":
##            return True
##        else:
##            return False

    def isHiddenOctave(self, note11, note12, note21, note22):
        '''Given four notes, assuming the first pair is from one part and
        the second pair is from another part sounding at the same time,
        returns True if there is a hidden octave and false otherwise.


        >>> from music21 import *
        >>> n1 = note.Note('A3')
        >>> n2 = note.Note('B-3')
        >>> m1 = note.Note('F4')
        >>> m2 = note.Note('B-4')
        >>> cp = ModalCounterpoint()
        >>> cp.isHiddenOctave(n1, m1, n2, m2) #(n1, n2) and (m1, m2) are chords
        False
        >>> cp.isHiddenOctave(n1, n2, m1, m2) #(n1, m1) and (n2, m2) are chords
        True
        >>> m1.octave = 5
        >>> m2.octave = 5
        >>> cp.isHiddenOctave(n1, n2, m1, m2)
        True

        '''
        vlq = voiceLeading.VoiceLeadingQuartet(note11, note12, note21, note22)
        return vlq.hiddenOctave()
##        interval1 = interval.notesToInterval(note11, note21)
##        interval2 = interval.notesToInterval(note12, note22)
##        interval3 = interval.notesToInterval(note11, note12)
##        interval4 = interval.notesToInterval(note21, note22)
##        if interval3.direction > 0 and interval4.direction > 0:
##            if interval2.semiSimpleName == "P8" and not interval1.semiSimpleName == "P8":
##                return True
##            else:
##                return False
##        if interval3.direction < 0 and interval4.direction < 0:
##            if interval2.semiSimpleName == "P8" and not interval1.semiSimpleName == "P8":
##                return True
##            else:
##                return False
##        if interval3.direction == 0 and interval4.direction == 0: return False
##        return False

    def findParallelUnisons(self, stream1, stream2):
        '''Given two streams, returns the number of parallel unisons and also
        assigns a flag under note.editorial.misc under "Parallel Unison" for
        any note that has harmonic interval of P1 and is preceded by a P1.


        >>> from music21 import *
        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('A4')
        >>> n3 = note.Note('B4')
        >>> n4 = note.Note('C5')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('A4')
        >>> m3 = note.Note('B4')
        >>> m4 = note.Note('C5')
        >>> bass = stream.Stream()
        >>> bass.append([n1, n2, n3, n4])
        >>> sop = stream.Stream()
        >>> sop.append([m1, m2, m3, m4])
        >>> cp = ModalCounterpoint(stream1 = bass, stream2 = sop)
        >>> cp.findParallelUnisons(cp.stream1, cp.stream2)
        3
        >>> n2.editorial.misc['Parallel Unison']
        True
        >>> cp.findParallelUnisons(cp.stream2, cp.stream1)
        3

        '''
        stream1.attachIntervalsBetweenStreams(stream2)
        stream2.attachIntervalsBetweenStreams(stream1)
        
        numParallelUnisons = 0
        for note1 in stream1:
            note2 = stream1.getElementAfterElement(note1, [Note])
            if note2 is not None:
                if note1.editorial.harmonicInterval.name == "P1":
                    if note2.editorial.harmonicInterval.name == "P1":
                        numParallelUnisons += 1
                        note2.editorial.misc["Parallel Unison"] = True
        for note1 in stream2:
            note2 = stream2.getElementAfterElement(note1, [Note])
            if note2 is not None:
                if note1.editorial.harmonicInterval.name == "P1":
                    if note2.editorial.harmonicInterval.name == "P1":
                        note2.editorial.misc["Parallel Unison"] = True
        return numParallelUnisons

    def isParallelUnison(self, note11, note12, note21, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if the two
        harmonic intervals are P8 and False otherwise.


        >>> from music21 import *
        >>> n1 = note.Note('A3')
        >>> n2 = note.Note('B-3')
        >>> m1 = note.Note('A3')
        >>> m2 = note.Note('B-3')
        >>> cp = ModalCounterpoint()
        >>> cp.isParallelUnison(n1, m1, n2, m2) #(n1, n2) and (m1, m2) are chords
        False
        >>> cp.isParallelUnison(n1, n2, m1, m2) #(n1, m1) and (n2, m2) are chords
        True
        >>> m1.octave = 4
        >>> m2.octave = 4
        >>> cp.isParallelUnison(n1, n2, m1, m2) #parallel octaves, not unison
        False

        '''
        vlq = voiceLeading.VoiceLeadingQuartet(note11, note12, note21, note22)
        return vlq.parallelUnison()
##        interval1 = interval.notesToInterval(note11, note21)
##        interval2 = interval.notesToInterval(note12, note22)
##        if interval1.name == interval2.name == "P1":
##            return True
##        else:
##            return False


    def isValidHarmony(self, note11, note21):
        '''Determines if the harmonic interval between two given notes is
        "legal" according to 21M.301 rules of counterpoint. Legal harmonic
        intervals include 'P1', 'P5', 'P8', 'm3', 'M3', 'm6', and 'M6'.


        >>> from music21 import *
        >>> c = note.Note('C4')
        >>> d = note.Note('D4')
        >>> e = note.Note('E4')
        >>> cp = ModalCounterpoint()
        >>> cp.isValidHarmony(c, d)
        False
        >>> cp.isValidHarmony(c, c)
        True
        >>> cp.isValidHarmony(c, e)
        True

        '''
        interval1 = interval.notesToInterval(note11, note21)
        if interval1.diatonic.name in self.legalHarmonicIntervals:
            return True
        else:
            return False

    def allValidHarmony(self, stream1, stream2):
        '''Given two simultaneous streams, returns True if all of the harmonies
        are legal and False if one or more is not. Legal harmonic intervals
        include 'P1', 'P5', 'P8', 'm3', 'M3', 'm6', and 'M6'.


        >>> from music21 import *
        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('A4')
        >>> n3 = note.Note('B4')
        >>> n4 = note.Note('C5')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('A4')
        >>> m3 = note.Note('B4')
        >>> m4 = note.Note('C5')
        >>> bass = stream.Stream()
        >>> bass.append([n1, n2, n3, n4])
        >>> sop = stream.Stream()
        >>> sop.append([m1, m2, m3, m4])
        >>> cp = ModalCounterpoint(stream1 = bass, stream2 = sop)
        >>> cp.allValidHarmony(cp.stream1, cp.stream2)
        True
        >>> n1.name = 'F#4'
        >>> cp.allValidHarmony(cp.stream1, cp.stream2)
        False

        '''
        stream1.attachIntervalsBetweenStreams(stream2)
        stream2.attachIntervalsBetweenStreams(stream1)
        for note1 in stream1.notes:
            if note1.editorial.harmonicInterval.name not in self.legalHarmonicIntervals:
                return False
        for note2 in stream2.notes:
            if note2.editorial.harmonicInterval.name not in self.legalHarmonicIntervals:
                return False
        if stream1.notes[-1].editorial.harmonicInterval.specificName != "Perfect":
            print(stream1.notes[-1].editorial.harmonicInterval.specificName + " ending, yuk!")
            return False
        return True

    def countBadHarmonies(self, stream1, stream2):
        '''Given two simultaneous streams, counts the number of notes (in the
        first stream given) that create illegal harmonies when attacked.


        >>> from music21 import *
        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('A4')
        >>> n3 = note.Note('B4')
        >>> n4 = note.Note('C5')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('A4')
        >>> m3 = note.Note('B4')
        >>> m4 = note.Note('C5')
        >>> bass = stream.Stream()
        >>> bass.append([n1, n2, n3, n4])
        >>> sop = stream.Stream()
        >>> sop.append([m1, m2, m3, m4])
        >>> cp = ModalCounterpoint(stream1 = bass, stream2 = sop)
        >>> cp.countBadHarmonies(cp.stream1, cp.stream2)
        0
        >>> n1.name = 'F#4'
        >>> cp.countBadHarmonies(cp.stream1, cp.stream2)
        1

        '''
        stream1.attachIntervalsBetweenStreams(stream2)
        numBadHarmonies = 0
        for note1 in stream1.notes:
            if note1.editorial.harmonicInterval.name not in self.legalHarmonicIntervals:
                numBadHarmonies += 1
        return numBadHarmonies

    def isValidStep(self, note11, note12):
        '''Determines if the melodic interval between two given notes is "legal"
        according to 21M.301 rules of counterpoint. Legal melodic intervals
        include 'P4', 'P5', 'P8', 'm2', 'M2', 'm3', 'M3', and 'm6'.

        SHOULD BE RENAMED isValidMelody?


        >>> from music21 import *
        >>> c = note.Note('C4')
        >>> d = note.Note('D4')
        >>> e = note.Note('E#4')
        >>> cp = ModalCounterpoint()
        >>> cp.isValidStep(c, d)
        True
        >>> cp.isValidStep(c, c)
        False
        >>> cp.isValidStep(c, e)
        False

        '''
        interval1 = interval.notesToInterval(note11, note12)
        if interval1.diatonic.name in self.legalMelodicIntervals:
            return True
        else:
            return False

    def isValidMelody(self, stream1):
        '''Given a single stream, returns True if all melodic intervals are
        legal and False otherwise. Legal melodic intervals include 'P4',
        'P5', 'P8', 'm2', 'M2', 'm3', 'M3', and 'm6'.

        SHOULD BE RENAMED allValidMelody?


        >>> from music21 import *
        >>> n1 = note.Note('G-4')
        >>> n2 = note.Note('A4')
        >>> n3 = note.Note('B4')
        >>> n4 = note.Note('B5')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('A4')
        >>> m3 = note.Note('B4')
        >>> m4 = note.Note('C5')
        >>> bass = stream.Stream()
        >>> bass.append([n1, n2, n3, n4])
        >>> sop = stream.Stream()
        >>> sop.append([m1, m2, m3, m4])
        >>> cp = ModalCounterpoint(stream1 = bass, stream2 = sop)
        >>> cp.isValidMelody(cp.stream1)
        False
        >>> n1.name = 'F#4'
        >>> cp.isValidMelody(cp.stream2)
        True

        '''
        numBadSteps = self.countBadSteps(stream1)
        if numBadSteps == 0:
            return True
        else:
            return False
        
    def countBadSteps(self, stream1):
        '''Given a single stream, returns the number of illegal melodic
        intervals.

        SHOULD BE RENAMED countBadMelodies?


        >>> from music21 import *
        >>> n1 = note.Note('G-4')
        >>> n2 = note.Note('A4')
        >>> n3 = note.Note('B4')
        >>> n4 = note.Note('A5')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('A4')
        >>> m3 = note.Note('B4')
        >>> m4 = note.Note('C5')
        >>> bass = stream.Stream()
        >>> bass.append([n1, n2, n3, n4])
        >>> sop = stream.Stream()
        >>> sop.append([m1, m2, m3, m4])
        >>> cp = ModalCounterpoint(stream1 = bass, stream2 = sop)
        >>> cp.countBadSteps(cp.stream1)
        2
        >>> n1.name = 'F#4'
        >>> cp.countBadSteps(cp.stream2)
        0
    
        '''
        numBadSteps = 0
        sn = stream1.notes
        for i in range(len(sn)-1):
            note1 = sn[i]
            note2 = sn[i+1]
            if note2 is not None:
                if not self.isValidStep(note1, note2):
                    numBadSteps += 1
        return numBadSteps


    def findAllBadFifths(self, stream1, stream2):
        '''Given two streams, returns the total parallel and hidden fifths,
        and also puts the appropriate tags in note.editorial.misc under
        "Parallel Fifth" and "Hidden Fifth".'''
        parallel = self.findParallelFifths(stream1, stream2)
        hidden = self.findHiddenFifths(stream1, stream2)
        return parallel + hidden

    def findAllBadOctaves(self, stream1, stream2):
        '''Given two streams, returns the total parallel and hidden octaves,
        and also puts the appropriate tags in note.editorial.misc under
        "Parallel Octave" and "Hidden Octave".'''
        parallel = self.findParallelOctaves(stream1, stream2)
        hidden = self.findHiddenOctaves(stream1, stream2)
        return parallel + hidden

    def tooManyThirds(self, stream1, stream2, limit = 3):
        '''Given two consecutive streams and a limit, returns True if the
        number of consecutive harmonic thirds exceeds the limit and False
        otherwise.


        >>> from music21 import *
        >>> n1 = note.Note('E4')
        >>> n2 = note.Note('F4')
        >>> n3 = note.Note('G4')
        >>> n4 = note.Note('A4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('A4')
        >>> m3 = note.Note('B4')
        >>> m4 = note.Note('C5')
        >>> bass = stream.Stream()
        >>> bass.append([n1, n2, n3, n4])
        >>> sop = stream.Stream()
        >>> sop.append([m1, m2, m3, m4])
        >>> cp = ModalCounterpoint(stream1 = bass, stream2 = sop)
        >>> cp.tooManyThirds(cp.stream1, cp.stream2)
        True
        >>> cp.tooManyThirds(cp.stream1, cp.stream2, 4)
        False

        '''
        stream1.attachIntervalsBetweenStreams(stream2)
        iList = []
        for note1 in stream1.notes:
            iList.append(note1.editorial.harmonicInterval.name)
        for i in range(len(iList)-limit): #no point checking if not enough notes left to SURPASS limit
            if iList[i] == 'm3' or iList[i] == 'M3':
                newList = iList[i:]
                consecutiveThirds = self.thirdCounter(newList, 0)
                if consecutiveThirds > limit:
                    return True
        return False

    def thirdCounter(self, intervalList, numThirds):
        '''Recursive helper function for tooManyThirds that returns the number
        of consecutive thirds in a stream, given a corresponding list of
        interval names.


        >>> from music21 import *
        >>> cp = ModalCounterpoint()
        >>> iList1 = ['m3', 'M3', 'm6']
        >>> cp.thirdCounter(iList1, 0)
        2
        >>> cp.thirdCounter(iList1, 2)
        4
        >>> iList2 = ['m2', 'M3', 'P1']
        >>> cp.thirdCounter(iList2, 0)
        0
        >>> iList3 = []
        >>> cp.thirdCounter(iList3, 52)
        52

        '''
        if len(intervalList) == 0:
            return numThirds
        if intervalList[0] != "M3" and intervalList[0] != "m3":
            return numThirds
        else:
            numThirds += 1
            newList = intervalList[1:]
            return self.thirdCounter(newList, numThirds)
                
    def tooManySixths(self, stream1, stream2, limit = 3):
        '''Given two consecutive streams and a limit, returns True if the
        number of consecutive harmonic sixths exceeds the limit and False
        otherwise.


        >>> from music21 import *
        >>> n1 = note.Note('E4')
        >>> n2 = note.Note('F4')
        >>> n3 = note.Note('G4')
        >>> n4 = note.Note('A4')
        >>> m1 = note.Note('C5')
        >>> m2 = note.Note('D5')
        >>> m3 = note.Note('E5')
        >>> m4 = note.Note('F5')
        >>> bass = stream.Stream()
        >>> bass.append([n1, n2, n3, n4])
        >>> sop = stream.Stream()
        >>> sop.append([m1, m2, m3, m4])
        >>> cp = ModalCounterpoint(stream1 = bass, stream2 = sop)
        >>> cp.tooManySixths(cp.stream1, cp.stream2)
        True
        >>> cp.tooManySixths(cp.stream1, cp.stream2, 4)
        False

        '''
        stream1.attachIntervalsBetweenStreams(stream2)
        iList = []
        for note1 in stream1.notes:
            intName = note1.editorial.harmonicInterval.name
            iList.append(intName)
        for i in range(len(iList)-limit): #no point checking if not enough notes left to SURPASS limit
            newList = iList[i:]
            consecutiveSixths = self.sixthCounter(newList, 0)
            if consecutiveSixths > limit:
                return True
        return False

    def sixthCounter(self, intervalList, numSixths):
        '''Recursive helper function for tooManyThirds that returns the number
        of consecutive thirds in a stream, given a corresponding list of
        interval names.


        >>> from music21 import *
        >>> cp = ModalCounterpoint()
        >>> iList1 = ['m6', 'M6', 'm3']
        >>> cp.sixthCounter(iList1, 0)
        2
        >>> cp.sixthCounter(iList1, 2)
        4
        >>> iList2 = ['m2', 'M6', 'P1']
        >>> cp.sixthCounter(iList2, 0)
        0
        >>> iList3 = []
        >>> cp.sixthCounter(iList3, 52)
        52

        '''
        if len(intervalList) == 0:
            return numSixths
        if intervalList[0] != "M6" and intervalList[0] != "m6":
            return numSixths
        else:
            numSixths += 1
            newList = intervalList[1:]
            return self.sixthCounter(newList, numSixths)

    def raiseLeadingTone(self, stream1, minorScale):
        '''Given a stream of notes and a minor scale object, returns a new
        stream that raises all the leading tones of the original stream. Also
        raises the sixth if applicable to avoid augmented intervals.'''
        s1notes = stream1.notes
        stream2 = stream.Part()
        sixth = minorScale.pitchFromScaleDegree(6).name
        seventh = minorScale.pitchFromScaleDegree(7).name
        tonic = minorScale.getTonic().name

        maxNote = len(s1notes)
        for i in range(maxNote):
            note1 = s1notes[i]
            if (note1.name == sixth and i < maxNote - 2):
                    note2 = s1notes[i+1]
                    note3 = s1notes[i+2]
                    if (note2.name == seventh and note3.name == tonic):
                        note1 = note1.transpose("A1")
            elif (note1.name == seventh and i < maxNote - 1):
                note2 = s1notes[i+1]
                if note2.name == tonic:
                    note1 = note1.transpose("A1")
            
            stream2.append(copy.deepcopy(note1))
        return stream2

    def generateFirstSpecies(self, stream1, minorScale):
        '''Given a stream (the cantus firmus) and the stream's key in the
        form of a MinorScale object, generates a stream of first species
        counterpoint that follows the rules of 21M.301.'''
        # DOES NOT YET CHECK FOR TOO MANY THIRDS/SIXTHS IN A ROW,
        # DOES NOT YET RAISE LEADING TONES, AND DOES NOT CHECK FOR NOODLING.
        stream2 = stream.Part([])
        firstNote = stream1.notes[0]
#        choices = [interval.transposeNote(firstNote, "P1"),\
#                   interval.transposeNote(firstNote, "P5"),\
#                   interval.transposeNote(firstNote, "P8")]
        choices = [copy.deepcopy(firstNote),
                   firstNote.transpose("P5"),
                   firstNote.transpose("P8")]
        note1 = random.choice(choices)
        note1.duration = firstNote.duration
        stream2.append(note1)
        afterLeap = False
        for i in range(1, len(stream1.notes)):
            prevFirmus = stream1.notes[i-1]
            currFirmus = stream1.notes[i]
            prevNote = stream2.notes[i-1]
            choices = self.generateValidNotes(prevFirmus, currFirmus, prevNote, afterLeap, minorScale)
            if len(choices) == 0:
                raise ModalCounterpointException("Sorry, please try again")
            #TODO: make deterministic with a flag
            newNote = random.choice(choices)
            newNote.duration = currFirmus.duration
            stream2.append(newNote)
            int1 = interval.notesToInterval(prevNote, newNote)
            if int1.generic.undirected > 3:
                afterLeap = True
            else:
                afterLeap = False
        return stream2

    def generateValidNotes(self, prevFirmus, currFirmus, prevNote, afterLeap, minorScale):
        '''Helper function for generateFirstSpecies; gets a list of possible
        next notes based on valid melodic intervals, then checks each one so
        that parallel/hidden fifths/octaves, voice crossing, and invalid
        harmonies are prevented. Adds extra weight to notes that would create
        contrary motion.'''
        print currFirmus.name
        valid = []
        bottomInt = interval.notesToInterval(prevFirmus, currFirmus)

        possibleNotes = []

        n1 = interval.transposeNote(prevNote, "m2")
        n2 = interval.transposeNote(prevNote, "M2")
        n3 = interval.transposeNote(prevNote, "m3")
        n4 = interval.transposeNote(prevNote, "M3")
        
        if afterLeap:
            goingUp = [n1, n2, n3, n4]
        else:
            n5 = interval.transposeNote(prevNote, "P4")
            n6 = interval.transposeNote(prevNote, "P5")
            goingUp = [n1, n2, n3, n4, n5, n6]

        n7 = interval.transposeNote(prevNote, "m-2")
        n8 = interval.transposeNote(prevNote, "M-2")
        n9 = interval.transposeNote(prevNote, "m-3")
        n10 = interval.transposeNote(prevNote, "M-3")
        if afterLeap:
            goingDown = [n7, n8, n9, n10]
        else:
            n11 = interval.transposeNote(prevNote, "P-4")
            n12 = interval.transposeNote(prevNote, "P-5")
            goingDown = [n7, n8, n9, n10, n11, n12]

        possibleNotes.extend(goingUp)
        possibleNotes.extend(goingDown)
        #favor contrary motion
        if bottomInt.direction < 0:
            possibleNotes.extend(goingUp)
        else:
            possibleNotes.extend(goingDown)
        print "possible: ", [note1.name for note1 in possibleNotes]

        goodNotes = minorScale.getConcreteMelodicMinorScale()
        goodNames = [note2.name for note2 in goodNotes]
        
        for note1 in possibleNotes:
            if note1.name in goodNames:
                if self.isValidHarmony(note1, currFirmus):
                    if not self.isParallelUnison(prevNote, note1, prevFirmus, currFirmus):
                        if not self.isParallelFifth(prevNote, note1, prevFirmus, currFirmus):
                            if not self.isParallelOctave(prevNote, note1, prevFirmus, currFirmus):
                                if not self.isHiddenFifth(prevNote, note1, prevFirmus, currFirmus):
                                    if not self.isHiddenOctave(prevNote, note1, prevFirmus, currFirmus):
                                        if interval.Interval(currFirmus, note1).direction >= 0:
                                            print "adding: ", note1.name, note1.octave
                                            valid.append(note1)
                
##            try: validHarmony = self.isValidHarmony(note1, currFirmus)
##            except: validHarmony = False
##
###            vlq = VoiceLeadingQuartet(prevNote, prevFirmus, note1, currFirmus)
###            par5 = vlq.parallelFifth()
###            par8 = vlq.parallelOctave()
###            hid5 = vlq.hiddenFifth()
###            hid8 = vlq.hiddenOctave()
###            par1 = vlq.parallelUnison()
##            
##            try: par5 = self.isParallelFifth(prevNote, note1, prevFirmus, currFirmus)
##            except: par5 = True
##            try: par8 = self.isParallelOctave(prevNote, note1, prevFirmus, currFirmus)
##            except: par8 = True
##            try: hid5 = self.isHiddenFifth(prevNote, note1, prevFirmus, currFirmus)
##            except: hid5 = True
##            try: hid8 = self.isHiddenOctave(prevNote, note1, prevFirmus, currFirmus)
##            except: hid8 = True
##            try: par1 = self.isParallelUnison(prevNote, note1, prevFirmus, currFirmus)
##            except: par1 = True
##            try:
##                distance = interval.notesToInterval(currFirmus, note1)
##                if distance.direction < 0: crossing = True
##                else: crossing = False
##            except: crossing = True
##            goodNotes = minorScale.getConcreteMelodicMinorScale()
##            goodNames = [note2.name for note2 in goodNotes]
##            if (note1.name in goodNames) and validHarmony and (not par5) and (not par8) and (not hid5) and\
##               (not hid8) and (not par1) and (not crossing):
##                    print "adding: ", note1.name, note1.octave
##                    valid.append(note1)
        print
        return valid

##############################################################
###
###     TONS OF TESTING
###
##############################################################

class Test(unittest.TestCase):
    pass

    def xtestCounterpoint(self):
        (n11,n12,n13,n14) = (Note(), Note(), Note(), Note())
        (n21,n22,n23,n24) = (Note(), Note(), Note(), Note())
        n11.duration.type = "whole"
        n12.duration.type = "whole"
        n13.duration.type = "whole"
        n14.duration.type = "whole"
        n21.duration.type = "whole"
        n22.duration.type = "whole"
        n23.duration.type = "whole"
        n24.duration.type = "whole"
        
        n11.step = "C"
        n12.step = "D"
        n13.step = "E"
        n14.step = "F"
    
        n21.step = "G"
        n22.step = "G"
        n23.step = "B"
        n24.step = "C"
        n24.octave = 5
    
    
        stream1 = Stream([n11, n12, n13, n14])
        stream2 = Stream([n21, n22, n23, n24])
        stream3 = Stream([n11, n13, n14])
        stream4 = Stream([n21, n23, n24])
        stream5 = Stream([n11, n23, n24, n21])
    
        counterpoint1 = ModalCounterpoint(stream1, stream2)
    
        #  CDEF
        #  GGBC
        findPar5 = counterpoint1.findParallelFifths(stream1, stream2)
        
        assert findPar5 == 1
        assert n24.editorial.misc["Parallel Fifth"] == True
        assert "Parallel Fifth" not in n21.editorial.misc
        assert "Parallel Fifth" not in n22.editorial.misc
        assert "Parallel Fifth" not in n23.editorial.misc

        assert n14.editorial.misc["Parallel Fifth"] == True
        assert "Parallel Fifth" not in n11.editorial.misc
        assert "Parallel Fifth" not in n12.editorial.misc
        assert "Parallel Fifth" not in n13.editorial.misc
    
        par5 = counterpoint1.isParallelFifth(n11, n12, n21, n22)
        assert par5 == False
    
        par52 = counterpoint1.isParallelFifth(n13, n14, n23, n24)
        assert par52 == True
    
        validHarmony1 = counterpoint1.isValidHarmony(n11, n21)
        validHarmony2 = counterpoint1.isValidHarmony(n12, n22)
    
        assert validHarmony1 == True
        assert validHarmony2 == False
    
        validStep1 = counterpoint1.isValidStep(n11, n23)
        validStep2 = counterpoint1.isValidStep(n23, n11)
        validStep3 = counterpoint1.isValidStep(n23, n24)
    
        assert validStep1 == False
        assert validStep2 == False
        assert validStep3 == True
    
        allHarmony = counterpoint1.allValidHarmony(stream1, stream2)
        assert allHarmony == False
    
        allHarmony2 = counterpoint1.allValidHarmony(stream3, stream4)
        assert allHarmony2 == True
    
        melody1 = counterpoint1.isValidMelody(stream1)
        melody2 = counterpoint1.isValidMelody(stream5)
    
        assert melody1 == True
        assert melody2 == False
    
        numBadHarmony = counterpoint1.countBadHarmonies(stream1, stream2)
        numBadHarmony2 = counterpoint1.countBadHarmonies(stream3, stream4)
    
        assert numBadHarmony == 1
        assert numBadHarmony2 == 0
    
        numBadMelody = counterpoint1.countBadSteps(stream1)
        numBadMelody2 = counterpoint1.countBadSteps(stream5)
    
        assert numBadMelody == 0
        assert numBadMelody2 == 1
    
        (n31, n32, n33, n34) = (Note(), Note(), Note(), Note())
        n31.duration.type = "whole"
        n32.duration.type = "whole"
        n33.duration.type = "whole"
        n34.duration.type = "whole"
    
        n31.octave = 5
        n32.octave = 5
        n33.octave = 5
        n34.octave = 5
    
        n32.step = "D"
        n33.step = "E"
        n34.step = "F"
    
        stream6 = Stream([n31, n32, n33, n34])
    
        par8 = counterpoint1.findParallelOctaves(stream1, stream6)
    
        assert par8 == 3
        assert "Parallel Octave" not in n31.editorial.misc
        assert n32.editorial.misc["Parallel Octave"] == True
        assert n33.editorial.misc["Parallel Octave"] == True
        assert n34.editorial.misc["Parallel Octave"] == True
    
        par82 = counterpoint1.findParallelOctaves(stream1, stream2)
        assert par82 == 0
    
        par83 = counterpoint1.isParallelOctave(n11, n12, n31, n32)
        par84 = counterpoint1.isParallelOctave(n11, n12, n21, n22)
    
        assert par83 == True
        assert par84 == False
    
        intervalList = ["m3", "M3", "P4", "P5", "m3"]
        consecutive = counterpoint1.thirdCounter(intervalList, 0)
        assert consecutive == 2
    
        list2 = ["m3", "M3", "m3", "m7"]
        consecutive2 = counterpoint1.thirdCounter(list2, 3)
        assert consecutive2 == 6
    
        list3 = ["m2", "m3"]
        consecutive3 = counterpoint1.thirdCounter(list3, 0)
        assert consecutive3 == 0
    
        (n41, n42, n43, n44, n45, n46, n47) = (Note(), Note(), Note(), Note(), Note(), Note(), Note())
        n41.duration.type = "whole"
        n42.duration.type = "whole"
        n43.duration.type = "whole"
        n44.duration.type = "whole"
        n45.duration.type = "whole"
        n46.duration.type = "whole"
        n47.duration.type = "whole"
    
        (n51, n52, n53, n54, n55, n56, n57) = (Note(), Note(), Note(), Note(), Note(), Note(), Note())
        n51.duration.type = "whole"
        n52.duration.type = "whole"
        n53.duration.type = "whole"
        n54.duration.type = "whole"
        n55.duration.type = "whole"
        n56.duration.type = "whole"
        n57.duration.type = "whole"
    
        n51.step = "E"
        n52.step = "E"
        n53.step = "E"
        n54.step = "E"
        n56.step = "E"
        n57.step = "E"
    
        stream7 = Stream([n41, n42, n43, n44, n45, n46, n47])
        stream8 = Stream([n51, n52, n53, n54, n55, n56, n57])
    
        too3 = counterpoint1.tooManyThirds(stream7, stream8, 4)
        too32 = counterpoint1.tooManyThirds(stream7, stream8, 3)
    
        assert too3 == False
        assert too32 == True
    
        (n61, n62, n63, n64, n65, n66, n67) = (Note(), Note(), Note(), Note(), Note(), Note(), Note())
        n61.duration.type = "whole"
        n62.duration.type = "whole"
        n63.duration.type = "whole"
        n64.duration.type = "whole"
        n65.duration.type = "whole"
        n66.duration.type = "whole"
        n67.duration.type = "whole"
    
        n61.step = "E"
        n62.step = "E"
        n63.step = "E"
        n64.step = "E"
        n66.step = "E"
        n67.step = "E"
    
        n61.octave = 3
        n62.octave = 3
        n63.octave = 3
        n64.octave = 3
        n66.octave = 3
        n67.octave = 3
    
        stream9 = Stream([n61, n62, n63, n64, n65, n66, n67])
    
        too6 = counterpoint1.tooManySixths(stream7, stream9, 4)
        too62 = counterpoint1.tooManySixths(stream7, stream9, 3)
    
        assert too6 == False
        assert too62 == True
    
        (n71, n72, n81, n82) = (Note(), Note(), Note(), Note())
        n71.duration.type = "whole"
        n72.duration.type = "whole"
        n81.duration.type = "whole"
        n82.duration.type = "whole"
        
        n71.octave = 5
        n72.step = "D"
        n72.octave = 5
        n82.step = "G"
        hiding = counterpoint1.isHiddenFifth(n71, n72, n81, n82)
        hiding2 = counterpoint1.isHiddenFifth(n71, n72, n82, n81)
    
        assert hiding == True
        assert hiding2 == False
    
        (n73, n74, n75, n76) = (Note(), Note(), Note(), Note())
        n73.duration.type = "whole"
        n74.duration.type = "whole"
        n75.duration.type = "whole"
        n76.duration.type = "whole"
        
        n73.step = "D"
        n73.octave = 5
        n74.step = "A"
        n75.step = "D"
        n75.octave = 5
        n76.step = "E"
        n76.octave = 5
    
        (n83, n84, n85, n86) = (Note(), Note(), Note(), Note())
        n83.duration.type = "whole"
        n84.duration.type = "whole"
        n85.duration.type = "whole"
        n86.duration.type = "whole"
        
        n83.step = "G"
        n84.step = "F"
        n85.step = "G"
        n86.step = "A"
    
        stream10 = Stream([n71, n72, n73, n74, n75, n76])
        stream11 = Stream([n81, n82, n83, n84, n85, n86])
    
        parallel5 = counterpoint1.findParallelFifths(stream10, stream11)
        hidden5 = counterpoint1.findHiddenFifths(stream10, stream11)
        assert "Hidden Fifth" not in n71.editorial.misc
        assert n72.editorial.misc["Hidden Fifth"] == True
        assert n75.editorial.misc["Hidden Fifth"] == True
        total5 = counterpoint1.findAllBadFifths(stream10, stream11)
    
        assert parallel5 == 2
        assert hidden5 == 2
        assert total5 == 4
    
        (n91, n92, n93, n94, n95, n96) = (Note(), Note(), Note(), Note(), Note(), Note())
        (n01, n02, n03, n04, n05, n06) = (Note(), Note(), Note(), Note(), Note(), Note())
    
        n91.duration.type = n92.duration.type = n93.duration.type = "whole"
        n94.duration.type = n95.duration.type = n96.duration.type = "whole"
        n01.duration.type = n02.duration.type = n03.duration.type = "whole"
        n04.duration.type = n05.duration.type = n06.duration.type = "whole"
    
        n91.step = "A"
        n92.step = "D"
        n92.octave = 5
        n93.step = "E"
        n93.octave = 5
        n94.octave = 5
        n95.step = "A"
        n96.step = "E"
        n96.octave = 5
    
        n02.step = "D"
        n03.step = "E"
        n06.step = "E"
    
        stream12 = Stream([n91, n92, n93, n94, n95, n96])
        stream13 = Stream([n01, n02, n03, n04, n05, n06])
    
        parallel8 = counterpoint1.findParallelOctaves(stream12, stream13)
        hidden8 = counterpoint1.findHiddenOctaves(stream12, stream13)
        total8 = counterpoint1.findAllBadOctaves(stream12, stream13)
    
        assert "Parallel Octave" not in n91.editorial.misc
        assert "Hidden Octave" not in n91.editorial.misc
        assert n92.editorial.misc["Hidden Octave"] == True
        assert "Parallel Octave" not in n92.editorial.misc
        assert n93.editorial.misc["Parallel Octave"] == True
        assert "Hidden Octave" not in n93.editorial.misc
        assert n94.editorial.misc["Parallel Octave"] == True
        assert n96.editorial.misc["Hidden Octave"] == True
    
        assert parallel8 == 2
        assert hidden8 == 2
        assert total8 == 4
    
        hidden8 = counterpoint1.isHiddenOctave(n91, n92, n01, n02)
        hidden82 = counterpoint1.isHiddenOctave(n92, n93, n02, n03)
    
        assert hidden8 == True
        assert hidden82 == False
    
        (n100, n101, n102, n103, n104, n105, n106, n107) = (Note(), Note(), Note(), Note(), Note(), Note(), Note(), Note())
        n100.duration.type = "whole"
        n101.duration.type = "whole"
        n102.duration.type = "whole"
        n103.duration.type = "whole"
        n104.duration.type = "whole"
        n105.duration.type = "whole"
        n106.duration.type = "whole"
        n107.duration.type = "whole"
    
        n100.name = "G"
        n101.name = "A"
        n102.name = "D"
        n103.name = "F"
        n104.name = "G"
        n105.name = "A"
        n106.name = "G"
        n107.name = "F"
    
        stream14 = Stream([n100, n101, n102, n103, n104, n105, n106, n107])
        aMinor = scale.ConcreteMinorScale(n101)
        stream15 = counterpoint1.raiseLeadingTone(stream14, aMinor)
        names15 = [note1.name for note1 in stream15.notes]
        assert names15 == ["G#", "A", "D", "F#", "G#", "A", "G", "F"]

class TestExternal(unittest.TestCase):
    pass
   
    def testGenerateFirstSpecies(self):
        '''
        A First Species Counterpoint Generator by Jackie Rogoff (MIT 2010) written as part of 
        an UROP (Undergraduate Research Opportunities Program) project at M.I.T. 2008.
        '''
        
        n101 = Note()
        n101.duration.type = "whole"
        n101.name = "A"
        aMinor = scale.ConcreteMinorScale(n101)
        n101b = Note()
        n101b.duration.type = "whole"
        n101b.name = "D"
        dMinor = scale.ConcreteMinorScale(n101b)
        
        counterpoint1 = ModalCounterpoint()

        cantusFirmus1 = "A1 c B c d e c B A"
        cantusFirmus2 = "A1 e d f e c d c B A"
        cantusFirmus3 = "d1 f e d g f a g f e d"
        #cantusFirmus4 = 
        
        choices = [cantusFirmus1, cantusFirmus2, cantusFirmus3]
        chosenCantusFirmus = random.choice(choices)
        cantusFirmus = stream.Part(converter.parse(chosenCantusFirmus, "4/4").notes)
    
        thisScale = aMinor
        if cantusFirmus is cantusFirmus3:
            thisScale = dMinor
            
        goodHarmony = False
        goodMelody = False
        thirdsGood = False
        sixthsGood = False
    
        while (goodHarmony == False or goodMelody == False or thirdsGood == False or sixthsGood == False):
            try:
                hopeThisWorks = counterpoint1.generateFirstSpecies(cantusFirmus, thisScale)
                hopeThisWorks2 = counterpoint1.raiseLeadingTone(hopeThisWorks, thisScale)
                print [note1.name + str(note1.octave) for note1 in hopeThisWorks2.notes]
        
                goodHarmony = counterpoint1.allValidHarmony(hopeThisWorks2, cantusFirmus)
                goodMelody = counterpoint1.isValidMelody(hopeThisWorks2)
                thirdsGood = not counterpoint1.tooManyThirds(hopeThisWorks2, cantusFirmus)
                sixthsGood = not counterpoint1.tooManySixths(hopeThisWorks2, cantusFirmus)
    
                lastInterval = interval.notesToInterval(hopeThisWorks2.notes[-2], hopeThisWorks2.notes[-1])
                if lastInterval.generic.undirected != 2:
                    goodMelody = False
                    print "rejected because lastInterval was not a second"
             
                print [note1.name + str(note1.octave) for note1 in cantusFirmus.notes]
                if not goodHarmony: print "bad harmony"
                else: print "harmony good"
                if not goodMelody: print "bad melody"
                else: print "melody good"
                if not thirdsGood: print "too many thirds"
                if not sixthsGood: print "too many sixths"
            except ModalCounterpointException:
                pass        
    
        score = stream.Score()
        score.insert(0, meter.TimeSignature('4/4'))
        score.insert(0, hopeThisWorks2)
        score.insert(0, cantusFirmus)
#        score.show('text')
#        score.show('musicxml')
        score.show('midi')
        score.show('lily.png')
        
if (__name__ == "__main__"):
    music21.mainTest(TestExternal) #TestExternal
