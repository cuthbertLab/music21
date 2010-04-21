#!/usr/bin/python

'''
counterpoint -- set of tools for dealing with Species Counterpoint and 
later other forms of counterpoint.

Mostly coded by Jackie Rogoff -- some routines have been moved to
by VoiceLeadingQuartet, and that module should be used for future work
'''

import random
import unittest, doctest

import music21
from music21.note import Note
from music21 import duration
from music21 import interval
from music21 import lily
from music21 import scale
#from music21 import twoStreams

from music21.stream import Stream
from music21.voiceLeading import VoiceLeadingQuartet

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
        first harmonic interval of a fifth.'''
        
        srcStream.attachIntervalsBetweenStreams(cmpStream)
        numParallelFifths = 0
        srcNotes = srcStream.notes
        
        for note1 in srcStream:
            note2 = srcStream.getElementAfterElement(note1, [Note])
            if note2 is not None:
                if note1.editorial.harmonicInterval.name == "P5" and \
                   note2.editorial.harmonicInterval.name == "P5":
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

        NOTE: Order matters! (stream1, stream2) might
        have no hidden fifths, while (stream2, stream1) does have them.'''
        numHiddenFifths = 0
        for i in range(len(stream1.notes)-1):
            note1 = stream1.notes[i]
            note2 = stream1.noteFollowingNote(note1, False)
            note3 = stream2.playingWhenAttacked(note1)
            note4 = stream2.playingWhenAttacked(note2)
            if note2 is not None and note3 is not None and note4 is not None:
                hidden = self.isHiddenFifth(note1, note2, note3, note4)
                if hidden:
                    numHiddenFifths += 1
                    note2.editorial.misc["Hidden Fifth"] = True
        return numHiddenFifths

    def isParallelFifth(self, note11, note12, note21, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if the two
        harmonic intervals are P5 and False otherwise.'''
        vlq = VoiceLeadingQuartet(note11, note12, note21, note22)
        return vlq.parallelFifth()
#        interval1 = interval.notesToInterval(note11, note21)
#        interval2 = interval.notesToInterval(note12, note22)
#        if interval1.name == interval2.name == "P5": return True
#        else: return False

    def isHiddenFifth(self, note11, note12, note21, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if there is a
        hidden fifth and false otherwise.'''
        interval1 = interval.notesToInterval(note11, note21)
        interval2 = interval.notesToInterval(note12, note22)
        interval3 = interval.notesToInterval(note11, note12)
        interval4 = interval.notesToInterval(note21, note22)
        if interval3.direction > 0 and interval4.direction > 0:
            if interval2.name == "P5" and not interval1.name == "P5": return True
            else: return False
        elif interval3.direction < 0 and interval4.direction < 0:
            if interval2.name == "P5" and not interval1.name == "P5": return True
            else: return False
        elif interval3.direction == interval4.direction == 0: return False
        return False

    def findParallelOctaves(self, stream1, stream2):
        '''Given two streams, returns the number of parallel octaves and also
        assigns a flag under note.editorial.misc under "Parallel Octave" for
        any note that has harmonic interval of an octave and is preceded by a
        harmonic interval of an octave.'''
        twoStreams1 = TwoStreamComparer(stream1, stream2)
        twoStreams1.intervalToOtherStreamWhenAttacked()
        numParallelOctaves = 0
        for note1 in stream1:
            note2 = stream1.noteFollowingNote(note1, False)
            if note2 is not None:
                if note1.editorial.harmonicInterval.name == "P8":
                    if note2.editorial.harmonicInterval.name == "P8":
                        numParallelOctaves += 1
                        note2.editorial.misc["Parallel Octave"] = True
        for note1 in stream2:
            note2 = stream2.noteFollowingNote(note1, False)
            if note2 is not None:
                if note1.editorial.harmonicInterval.name == "P8":
                    if note2.editorial.harmonicInterval.name == "P8":
                        note2.editorial.misc["Parallel Octave"] = True
        return numParallelOctaves

    def findHiddenOctaves(self, stream1, stream2):
        '''Given two streams, returns the number of hidden octaves and also
        assigns a flag under note.editorial.misc under "Hidden Octave" for
        any note that has harmonic interval of an octave where it creates a
        hidden parallel octave. Note: a hidden octave here is defined as
        anything where the two streams reach an octave through parallel motion,
        but is not a parallel octave.

        NOTE: Order matters! (stream1, stream2) might
        have no hidden octaves, while (stream2, stream1) does have them.'''
        numHiddenOctaves = 0
        for i in range(len(stream1.notes)-1):
            note1 = stream1.notes[i]
            note2 = stream1.noteFollowingNote(note1, False)
            note3 = stream2.playingWhenAttacked(note1)
            note4 = stream2.playingWhenAttacked(note2)
            if note2 is not None and note3 is not None and note4 is not None:
                hidden = self.isHiddenOctave(note1, note2, note3, note4)
                if hidden:
                    numHiddenOctaves += 1
                    note2.editorial.misc["Hidden Octave"] = True
        return numHiddenOctaves

    def isHiddenOctave(self, note11, note12, note21, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if there is a
        hidden octave and false otherwise.'''
        interval1 = interval.notesToInterval(note11, note21)
        interval2 = interval.notesToInterval(note12, note22)
        interval3 = interval.notesToInterval(note11, note12)
        interval4 = interval.notesToInterval(note21, note22)
        if interval3.direction > 0 and interval4.direction > 0:
            if interval2.name == "P8" and not interval1.name == "P8": return True
            else: return False
        if interval3.direction < 0 and interval4.direction < 0:
            if interval2.name == "P8" and not interval1.name == "P8": return True
            else: return False
        if interval3.direction == 0 and interval4.direction == 0: return False
        return False

    def findParallelUnisons(self, stream1, stream2):
        '''Given two streams, returns the number of parallel unisons and also
        assigns a flag under note.editorial.misc under "Parallel Unison" for
        any note that has harmonic interval of P1 and is preceded by a P1.'''
        twoStreams1 = TwoStreamComparer(stream1, stream2)
        twoStreams1.intervalToOtherStreamWhenAttacked()
        numParallelUnisons = 0
        for note1 in stream1:
            note2 = stream1.noteFollowingNote(note1, False)
            if note2 is not None:
                if note1.editorial.harmonicInterval.name == "P1":
                    if note2.editorial.harmonicInterval.name == "P1":
                        numParallelUnisons += 1
                        note2.editorial.misc["Parallel Unison"] = True
        for note1 in stream2:
            note2 = stream2.noteFollowingNote(note1, False)
            if note2 is not None:
                if note1.editorial.harmonicInterval.name == "P1":
                    if note2.editorial.harmonicInterval.name == "P1":
                        note2.editorial.misc["Parallel Unison"] = True
        return numParallelUnisons

    def isParallelOctave(self, note11, note12, note21, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if the two
        harmonic intervals are P8 and False otherwise.'''
        interval1 = interval.notesToInterval(note11, note21)
        interval2 = interval.notesToInterval(note12, note22)
        if interval1.name == interval2.name == "P8": return True
        else: return False

    def isParallelUnison(self, note11, note12, note21, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if the two
        harmonic intervals are P8 and False otherwise.'''
        interval1 = interval.notesToInterval(note11, note21)
        interval2 = interval.notesToInterval(note12, note22)
        if interval1.name == interval2.name == "P1": return True
        else: return False


    def isValidHarmony(self, note11, note21):
        '''Determines if the harmonic interval between two given notes is
        "legal" according to 21M.301 rules of counterpoint.'''
        interval1 = interval.notesToInterval(note11, note21)
        if interval1.diatonic.name in self.legalHarmonicIntervals: return True
        else: return False

    def allValidHarmony(self, stream1, stream2):
        '''Given two simultaneous streams, returns True if all of the harmonies
        are legal and False if one or more is not.'''
        twoStreams1 = TwoStreamComparer(stream1, stream2)
        twoStreams1.intervalToOtherStreamWhenAttacked()
        for note1 in stream1:
            if note1.editorial.harmonicInterval.name not in self.legalHarmonicIntervals:
                return False
        for note2 in stream2:
            if note2.editorial.harmonicInterval.name not in self.legalHarmonicIntervals:
                return False
        if stream1.notes[-1].editorial.harmonicInterval.specificName != "Perfect":
            print(stream1.notes[-1].editorial.harmonicInterval.specificName + " ending, yuk!")
            return False
        return True

    def countBadHarmonies(self, stream1, stream2):
        '''Given two simultaneous streams, counts the number of notes (in the
        first stream given) that create illegal harmonies when attacked.'''
        twoStreams1 = TwoStreamComparer(stream1, stream2)
        twoStreams1.intervalToOtherStreamWhenAttacked()
        numBadHarmonies = 0
        for note1 in stream1:
            if note1.editorial.harmonicInterval.name not in self.legalHarmonicIntervals:
                numBadHarmonies += 1
        return numBadHarmonies

    def isValidStep(self, note11, note12):
        '''Determines if the melodic interval between two given notes is "legal"
        according to 21M.301 rules of counterpoint.'''
        interval1 = interval.notesToInterval(note11, note12)
        if interval1.diatonic.name in self.legalMelodicIntervals: return True
        else: return False

    def isValidMelody(self, stream1):
        '''Given a single stream, returns True if all melodic intervals are
        legal and False otherwise.'''
        numBadSteps = self.countBadSteps(stream1)
        if numBadSteps == 0: return True
        else: return False
        
    def countBadSteps(self, stream1):
        '''Given a single stream, returns the number of illegal melodic intervals.'''
        numBadSteps = 0
        for i in range(len(stream1.notes)-1):
            note1 = stream1.notes[i]
            note2 = stream1.noteFollowingNote(note1, False)
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
        otherwise.'''
        twoStreams1 = TwoStreamComparer(stream1, stream2)
        twoStreams1.intervalToOtherStreamWhenAttacked()
        intervalList = []
        for note1 in stream1.notes:
            intName = note1.editorial.harmonicInterval.name
            intervalList.append(intName)
        for i in range(len(intervalList)-limit):
            newList = intervalList[i:]
            consecutiveThirds = self.thirdCounter(newList, 0)
            if consecutiveThirds > limit:
                return True
        return False

    def thirdCounter(self, intervalList, numThirds):
        '''Recursive helper function for tooManyThirds that returns the number
        of consecutive thirds in a stream, given a corresponding list of
        interval names.'''
        if intervalList[0] != "M3" and intervalList[0] != "m3":
            return numThirds
        else:
            numThirds += 1
            newList = intervalList[1:]
            return self.thirdCounter(newList, numThirds)
                
    def tooManySixths(self, stream1, stream2, limit = 3):
        '''Given two consecutive streams and a limit, returns True if the
        number of consecutive harmonic sixths exceeds the limit and False
        otherwise.'''
        twoStreams1 = TwoStreamComparer(stream1, stream2)
        twoStreams1.intervalToOtherStreamWhenAttacked()
        intervalList = []
        for note1 in stream1.notes:
            intName = note1.editorial.harmonicInterval.name
            intervalList.append(intName)
        for i in range(len(intervalList)-limit):
            newList = intervalList[i:]
            consecutiveSixths = self.sixthCounter(newList, 0)
            if consecutiveSixths > limit:
                return True
        return False

    def sixthCounter(self, intervalList, numSixths):
        '''Recursive helper function for tooManyThirds that returns the number
        of consecutive thirds in a stream, given a corresponding list of
        interval names.'''
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
        notes2 = stream1.notes[:]
        stream2 = Stream(notes2)
        sixth = minorScale.pitchFromScaleDegree(6).name
        seventh = minorScale.pitchFromScaleDegree(7).name
        tonic = minorScale.getTonic().name
        for i in range(len(stream1.notes)-2):
            note1 = stream1.notes[i]
            note2 = stream1.notes[i+1]
            note3 = stream1.notes[i+2]
            if note1 is not None and note2 is not None and note3 is not None:
                if note1.name == sixth and note2.name == seventh and note3.name == tonic:
                    newNote1 = interval.transposeNote(note1, "A1")
                    newNote2 = interval.transposeNote(note2, "A1")
                    stream2.notes[i] = newNote1
                    stream2.notes[i+1] = newNote2
        for i in range(len(stream1.notes)-1):
            note1 = stream1.notes[i]
            note2 = stream1.notes[i+1]
            if note1 is not None and note2 is not None:
                if note1.name == seventh and note2.name == tonic:
                    newNote = interval.transposeNote(note1, "A1")
                    stream2.notes[i] = newNote
        return stream2

    def generateFirstSpecies(self, stream1, minorScale):
        '''Given a stream (the cantus firmus) and the stream's key in the
        form of a MinorScale object, generates a stream of first species
        counterpoint that follows the rules of 21M.301.'''
        # DOES NOT YET CHECK FOR TOO MANY THIRDS/SIXTHS IN A ROW,
        # DOES NOT YET RAISE LEADING TONES, AND DOES NOT CHECK FOR NOODLING.
        stream2 = Stream([])
        firstNote = stream1.notes[0]
        choices = [interval.transposeNote(firstNote, "P1"),\
                   interval.transposeNote(firstNote, "P5"),\
                   interval.transposeNote(firstNote, "P8")]
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
            newNote = random.choice(choices)
            newNote.duration = currFirmus.duration
            stream2.append(newNote)
            int = interval.notesToInterval(prevNote, newNote)
            if int.generic.undirected > 3: afterLeap = True
            else: afterLeap = False
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
        if bottomInt.direction < 0: ascending = True
        else: ascending = False

        n1 = interval.transposeNote(prevNote, "m2")
        n2 = interval.transposeNote(prevNote, "M2")
        n3 = interval.transposeNote(prevNote, "m3")
        n4 = interval.transposeNote(prevNote, "M3")
        n5 = interval.transposeNote(prevNote, "P4")
        n6 = interval.transposeNote(prevNote, "P5")
        if afterLeap: possible = [n1, n2, n3, n4]
        else: possible = [n1, n2, n3, n4, n5, n6]
        possible.extend(possible)

        n7 = interval.transposeNote(prevNote, "m-2")
        n8 = interval.transposeNote(prevNote, "M-2")
        n9 = interval.transposeNote(prevNote, "m-3")
        n10 = interval.transposeNote(prevNote, "M-3")
        n11 = interval.transposeNote(prevNote, "P-4")
        n12 = interval.transposeNote(prevNote, "P-5")
        if afterLeap: possible.extend([n7, n8, n9, n10])
        else: possible.extend([n7, n8, n9, n10, n11, n12])
        print "possible: ", [note1.name for note1 in possible]
        
        for note1 in possible:
            try: validHarmony = self.isValidHarmony(note1, currFirmus)
            except: validHarmony = False

#            vlq = VoiceLeadingQuartet(prevNote, prevFirmus, note1, currFirmus)
#            par5 = vlq.parallelFifth()
#            par8 = vlq.parallelOctave()
#            hid5 = vlq.hiddenFifth()
#            hid8 = vlq.hiddenOctave()
#            par1 = vlq.parallelUnison()
            
            try: par5 = self.isParallelFifth(prevNote, note1, prevFirmus, currFirmus)
            except: par5 = True
            try: par8 = self.isParallelOctave(prevNote, note1, prevFirmus, currFirmus)
            except: par8 = True
            try: hid5 = self.isHiddenFifth(prevNote, note1, prevFirmus, currFirmus)
            except: hid5 = True
            try: hid8 = self.isHiddenOctave(prevNote, note1, prevFirmus, currFirmus)
            except: hid8 = True
            try: par1 = self.isParallelUnison(prevNote, note1, prevFirmus, currFirmus)
            except: par1 = True
            try:
                distance = interval.notesToInterval(currFirmus, note1)
                if distance.direction < 0: crossing = True
                else: crossing = False
            except: crossing = True
            goodNotes = minorScale.getConcreteMelodicMinorScale()
            goodNames = [note2.name for note2 in goodNotes]
            if validHarmony and (not par5) and (not par8) and (not hid5) and\
               (not hid8) and (not par1) and (not crossing):
                if note1.name in goodNames:
                    print "adding: ", note1.name, note1.octave
                    valid.append(note1)
        print
        return valid

class Test(unittest.TestCase):
    pass

    def xtestCounterpoint(self):
        (n11,n12,n13,n14) = (Note(), Note(), Note(), Note())
        (n21,n22,n23,n24) = (Note(), Note(), Note(), Note())
        n11.duration.type = "quarter"
        n12.duration.type = "quarter"
        n13.duration.type = "quarter"
        n14.duration.type = "quarter"
        n21.duration.type = "quarter"
        n22.duration.type = "quarter"
        n23.duration.type = "quarter"
        n24.duration.type = "quarter"
        
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
        n31.duration.type = "quarter"
        n32.duration.type = "quarter"
        n33.duration.type = "quarter"
        n34.duration.type = "quarter"
    
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
        n41.duration.type = "quarter"
        n42.duration.type = "quarter"
        n43.duration.type = "quarter"
        n44.duration.type = "quarter"
        n45.duration.type = "quarter"
        n46.duration.type = "quarter"
        n47.duration.type = "quarter"
    
        (n51, n52, n53, n54, n55, n56, n57) = (Note(), Note(), Note(), Note(), Note(), Note(), Note())
        n51.duration.type = "quarter"
        n52.duration.type = "quarter"
        n53.duration.type = "quarter"
        n54.duration.type = "quarter"
        n55.duration.type = "quarter"
        n56.duration.type = "quarter"
        n57.duration.type = "quarter"
    
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
        n61.duration.type = "quarter"
        n62.duration.type = "quarter"
        n63.duration.type = "quarter"
        n64.duration.type = "quarter"
        n65.duration.type = "quarter"
        n66.duration.type = "quarter"
        n67.duration.type = "quarter"
    
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
        n71.duration.type = "quarter"
        n72.duration.type = "quarter"
        n81.duration.type = "quarter"
        n82.duration.type = "quarter"
        
        n71.octave = 5
        n72.step = "D"
        n72.octave = 5
        n82.step = "G"
        hiding = counterpoint1.isHiddenFifth(n71, n72, n81, n82)
        hiding2 = counterpoint1.isHiddenFifth(n71, n72, n82, n81)
    
        assert hiding == True
        assert hiding2 == False
    
        (n73, n74, n75, n76) = (Note(), Note(), Note(), Note())
        n73.duration.type = "quarter"
        n74.duration.type = "quarter"
        n75.duration.type = "quarter"
        n76.duration.type = "quarter"
        
        n73.step = "D"
        n73.octave = 5
        n74.step = "A"
        n75.step = "D"
        n75.octave = 5
        n76.step = "E"
        n76.octave = 5
    
        (n83, n84, n85, n86) = (Note(), Note(), Note(), Note())
        n83.duration.type = "quarter"
        n84.duration.type = "quarter"
        n85.duration.type = "quarter"
        n86.duration.type = "quarter"
        
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
    
        n91.duration.type = n92.duration.type = n93.duration.type = "quarter"
        n94.duration.type = n95.duration.type = n96.duration.type = "quarter"
        n01.duration.type = n02.duration.type = n03.duration.type = "quarter"
        n04.duration.type = n05.duration.type = n06.duration.type = "quarter"
    
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
        n100.duration.type = "quarter"
        n101.duration.type = "quarter"
        n102.duration.type = "quarter"
        n103.duration.type = "quarter"
        n104.duration.type = "quarter"
        n105.duration.type = "quarter"
        n106.duration.type = "quarter"
        n107.duration.type = "quarter"
    
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
        an UROP (Undergraduate Research Opportunities Program) project at M.I.T. 2007.
        '''
        
        n101 = Note()
        n101.duration.type = "quarter"
        n101.name = "A"
        aMinor = scale.ConcreteMinorScale(n101)
        n101b = Note()
        n101b.duration.type = "quarter"
        n101b.name = "D"
        dMinor = scale.ConcreteMinorScale(n101b)
        
        counterpoint1 = ModalCounterpoint()
        (n110, n111, n112, n113) = (Note(), Note(), Note(), Note())
        (n114, n115, n116, n117, n118) = (Note(), Note(), Note(), Note(), Note())
        (n119, n120, n121, n122, n123) = (Note(), Note(), Note(), Note(), Note())
        (n124, n125, n126, n127, n128) = (Note(), Note(), Note(), Note(), Note())
    
        n110.duration.type = "quarter"
        n111.duration.type = "quarter"
        n112.duration.type = "quarter"
        n113.duration.type = "quarter"
        n114.duration.type = "quarter"
        n115.duration.type = "quarter"
        n116.duration.type = "quarter"
        n117.duration.type = "quarter"
        n118.duration.type = "quarter"
    
        n110.name = "A"
        n110.octave = 3
        n111.name = "C"
        n111.octave = 4
        n112.name = "B"
        n112.octave = 3
        n113.name = "C"
        n113.octave = 4
        n114.name = "D"
        n115.name = "E"
        n116.name = "C"
        n116.octave = 4
        n117.name = "B"
        n117.octave = 3
        n118.name = "A"
        n118.octave = 3
        n119.name = "F"
        n120.name = "E"
        n121.name = "D"
        n122.name = "G"
        n123.name = "F"
        n124.name = "A"
        n125.name = "G"
        n126.name = "F"
        n127.name = "E"
        n128.name = "D"
    
        cantusFirmus1 = Stream([n110, n111, n112, n113, n114, n115, n116, n117, n118])
        cantusFirmus2 = Stream([n110, n115, n114, n119, n120, n113, n121, n116, n117, n118])
        cantusFirmus3 = Stream([n114, n119, n115, n121, n122, n123, n124, n125, n126, n127, n128])
        
        choices = [cantusFirmus1, cantusFirmus2, cantusFirmus3, cantusFirmus3, cantusFirmus3, cantusFirmus3]
        cantusFirmus = random.choice(choices)
    
        thisScale = aMinor
        if cantusFirmus is cantusFirmus3:
            thisScale = dMinor
            
        goodHarmony = False
        goodMelody = False
    
        while (goodHarmony == False or goodMelody == False):
            try:
                hopeThisWorks = counterpoint1.generateFirstSpecies(cantusFirmus, thisScale)
                print [note1.name + str(note1.octave) for note1 in hopeThisWorks.notes]
    
                hopeThisWorks2 = counterpoint1.raiseLeadingTone(hopeThisWorks, thisScale)
                print [note1.name + str(note1.octave) for note1 in hopeThisWorks2.notes]
        
                goodHarmony = counterpoint1.allValidHarmony(hopeThisWorks2, cantusFirmus)
                goodMelody = counterpoint1.isValidMelody(hopeThisWorks2)        
    
                lastInterval = interval.notesToInterval(hopeThisWorks2.notes[-2], hopeThisWorks2.notes[-1])
                if lastInterval.generic.undirected != 2:
                    goodMelody = False
                    print "rejected because lastInterval was not a second"
             
                print [note1.name + str(note1.octave) for note1 in cantusFirmus.notes]
                if not goodHarmony: print "bad harmony"
                else: print "harmony good"
                if not goodMelody: print "bad melody"
                else: print "melody good"
            except ModalCounterpointException:
                pass
        
        d1 = duration.Duration()
        d1.type = "whole"
        for tN in hopeThisWorks2.notes:
            tN.duration = d1
        for tN in cantusFirmus.notes:
            tN.duration = d1
    
        lilyOut = twoStreamLily(hopeThisWorks2, cantusFirmus)
        lilyOut.showPNGandPlayMIDI()
    
def twoStreamLily(st1, st2):
    lilyOut = lily.LilyString()
    lilyOut += "<< \\time 4/4\n"
    lilyOut += "  \\new Staff { " 
    lilyOut += st1.lily + " } \n"    
    lilyOut += "  \\new Staff { " 
    lilyOut += st2.lily + " } \n"    
    lilyOut += ">> \n"
    return lilyOut
    
if (__name__ == "__main__"):
    music21.mainTest(TestExternal) #TestExternal
