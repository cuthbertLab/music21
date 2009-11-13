#!/usr/bin/python

'''
counterpoint -- set of tools for dealing with Species Counterpoint and 
later other forms of counterpoint.

Mostly coded by Jackie Rogoff -- some routines have been moved to
by VoiceLeadingQuartet, and that module should be used for future work
'''

import random

import music21
from music21.note import Note
from music21 import interval
from music21.noteStream import Stream
from music21.twoStreams import TwoStreamComparer

import music21.key
from music21.voiceLeading import VoiceLeadingQuartet


class CounterpointException(Exception):
    pass

class Counterpoint(object):
    def __init__(self, stream1 = None, stream2 = None):
        self.stream1 = stream1
        self.stream2 = stream2
        self.legalHarmonicIntervals = ['P1', 'P5', 'P8', 'm3', 'M3', 'm6', 'M6']
        self.legalMelodicIntervals = ['P4', 'P5', 'P8', 'm2', 'M2', 'm3', 'M3', 'm6']

    def findParallelFifths(self, stream1, stream2):
        '''Given two streams, returns the number of parallel fifths and also
        assigns a flag under note.editorial.misc under "Parallel Fifth" for
        any note that has harmonic interval of a fifth and is preceded by a
        first harmonic interval of a fifth.'''
        twoStreams1 = TwoStreamComparer(stream1, stream2)
        twoStreams1.intervalToOtherStreamWhenAttacked()
        numParallelFifths = 0
        for note1 in stream1:
            note2 = stream1.noteFollowingNote(note1, False)
            if note2 is not None:
                if note1.editorial.harmonicInterval.name == "P5":
                    if note2.editorial.harmonicInterval.name == "P5":
                        numParallelFifths += 1
                        note2.editorial.misc["Parallel Fifth"] = True
        for note1 in stream2:
            note2 = stream2.noteFollowingNote(note1, False)
            if note2 is not None:
                if note1.editorial.harmonicInterval.name == "P5":
                    if note2.editorial.harmonicInterval.name == "P5":
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
        twoStreams1 = TwoStreamComparer(stream1, stream2)
        numHiddenFifths = 0
        for i in range(len(stream1.notes)-1):
            note1 = stream1.notes[i]
            note2 = stream1.noteFollowingNote(note1, False)
            note3 = twoStreams1.playingWhenSounded(note1, False)
            note4 = twoStreams1.playingWhenSounded(note2, False)
            if note2 is not None and note3 is not None and note4 is not None:
                hidden = self.isHiddenFifth(note1, note3, note2, note4)
                if hidden:
                    numHiddenFifths += 1
                    note2.editorial.misc["Hidden Fifth"] = True
        return numHiddenFifths

    def isParallelFifth(self, note11, note21, note12, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if the two
        harmonic intervals are P5 and False otherwise.'''
        interval1 = interval.generateInterval(note11, note21)
        interval2 = interval.generateInterval(note12, note22)
        if interval1.name == interval2.name == "P5": return True
        else: return False

    def isHiddenFifth(self, note11, note21, note12, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if there is a
        hidden fifth and false otherwise.'''
        interval1 = interval.generateInterval(note11, note21)
        interval2 = interval.generateInterval(note12, note22)
        interval3 = interval.generateInterval(note11, note12)
        interval4 = interval.generateInterval(note21, note22)
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
        twoStreams1 = TwoStreamComparer(stream1, stream2)
        numHiddenOctaves = 0
        for i in range(len(stream1.notes)-1):
            note1 = stream1.notes[i]
            note2 = stream1.noteFollowingNote(note1, False)
            note3 = twoStreams1.playingWhenSounded(note1, False)
            note4 = twoStreams1.playingWhenSounded(note2, False)
            if note2 is not None and note3 is not None and note4 is not None:
                hidden = self.isHiddenOctave(note1, note3, note2, note4)
                if hidden:
                    numHiddenOctaves += 1
                    note2.editorial.misc["Hidden Octave"] = True
        return numHiddenOctaves

    def isHiddenOctave(self, note11, note21, note12, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if there is a
        hidden octave and false otherwise.'''
        interval1 = interval.generateInterval(note11, note21)
        interval2 = interval.generateInterval(note12, note22)
        interval3 = interval.generateInterval(note11, note12)
        interval4 = interval.generateInterval(note21, note22)
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

    def isParallelUnison(self, note11, note21, note12, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if the two
        harmonic intervals are P8 and False otherwise.'''
        interval1 = interval.generateInterval(note11, note21)
        interval2 = interval.generateInterval(note12, note22)
        if interval1.name == interval2.name == "P1": return True
        else: return False


    def isValidHarmony(self, note11, note21):
        '''Determines if the harmonic interval between two given notes is
        "legal" according to 21M.301 rules of counterpoint.'''
        interval1 = interval.generateInterval(note11, note21)
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
            print stream1.notes[-1].editorial.harmonicInterval.specificName + " ending, yuk!"
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
        interval1 = interval.generateInterval(note11, note12)
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

    def isParallelOctave(self, note11, note21, note12, note22):
        '''Given four notes, assuming the first pair sounds at the same time and
        the second pair sounds at the same time, returns True if the two
        harmonic intervals are P8 and False otherwise.'''
        interval1 = interval.generateInterval(note11, note21)
        interval2 = interval.generateInterval(note12, note22)
        if interval1.name == interval2.name == "P8": return True
        else: return False


    def tooManyThirds(self, stream1, stream2, limit):
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
                
    def tooManySixths(self, stream1, stream2, limit):
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
                    newNote1 = interval.generateNote(note1, "A1")
                    newNote2 = interval.generateNote(note2, "A1")
                    stream2.notes[i] = newNote1
                    stream2.notes[i+1] = newNote2
        for i in range(len(stream1.notes)-1):
            note1 = stream1.notes[i]
            note2 = stream1.notes[i+1]
            if note1 is not None and note2 is not None:
                if note1.name == seventh and note2.name == tonic:
                    newNote = interval.generateNote(note1, "A1")
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
        choices = [interval.generateNote(firstNote, "P1"),\
                   interval.generateNote(firstNote, "P5"),\
                   interval.generateNote(firstNote, "P8")]
        note1 = random.choice(choices)
        note1.duration = firstNote.duration
        stream2.notes.append(note1)
        afterLeap = False
        for i in range(1, len(stream1.notes)):
            prevFirmus = stream1.notes[i-1]
            currFirmus = stream1.notes[i]
            prevNote = stream2.notes[i-1]
            choices = self.generateValidNotes(prevFirmus, currFirmus, prevNote, afterLeap, minorScale)
            if len(choices) == 0:
                raise CounterpointException("Sorry, please try again")
            newNote = random.choice(choices)
            newNote.duration = currFirmus.duration
            stream2.notes.append(newNote)
            int = interval.generateInterval(prevNote, newNote)
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
        bottomInt = interval.generateInterval(prevFirmus, currFirmus)
        if bottomInt.direction < 0: ascending = True
        else: ascending = False

        n1 = interval.generateNote(prevNote, "m2")
        n2 = interval.generateNote(prevNote, "M2")
        n3 = interval.generateNote(prevNote, "m3")
        n4 = interval.generateNote(prevNote, "M3")
        n5 = interval.generateNote(prevNote, "P4")
        n6 = interval.generateNote(prevNote, "P5")
        if afterLeap: possible = [n1, n2, n3, n4]
        else: possible = [n1, n2, n3, n4, n5, n6]
        possible.extend(possible)

        n7 = interval.generateNote(prevNote, "m-2")
        n8 = interval.generateNote(prevNote, "M-2")
        n9 = interval.generateNote(prevNote, "m-3")
        n10 = interval.generateNote(prevNote, "M-3")
        n11 = interval.generateNote(prevNote, "P-4")
        n12 = interval.generateNote(prevNote, "P-5")
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
            
            try: par5 = self.isParallelFifth(prevNote, prevFirmus, note1, currFirmus)
            except: par5 = True
            try: par8 = self.isParallelOctave(prevNote, prevFirmus, note1, currFirmus)
            except: par8 = True
            try: hid5 = self.isHiddenFifth(prevNote, prevFirmus, note1, currFirmus)
            except: hid5 = True
            try: hid8 = self.isHiddenOctave(prevNote, prevFirmus, note1, currFirmus)
            except: hid8 = True
            try: par1 = self.isParallelUnison(prevNote, prevFirmus, note1, currFirmus)
            except: par1 = True
            try:
                distance = interval.generateInterval(currFirmus, note1)
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
