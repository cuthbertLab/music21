#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         chord.py
# Purpose:      Chord representation and utilities
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
This module defines the Chord object, a sub-class of :class:`~music21.note.GeneralNote`
as well as other methods, functions, and objects related to chords.
'''
 
import copy
import unittest

import music21
from music21 import interval

#from music21.note import Note
from music21 import musicxml
from music21 import midi as midiModule
from music21.midi import translate as midiTranslate
from music21.musicxml import translate as musicxmlTranslate
from music21 import note
from music21 import defaults

#from music21.pitch import Pitch
from music21 import pitch
from music21 import beam
from music21 import common
from music21 import chordTables

from music21 import environment
_MOD = "chord.py"
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class ChordException(Exception):
    pass


class Chord(note.NotRest):
    '''Class for dealing with chords
    
    A Chord functions like a Note object but has multiple pitches.
    
    Create chords by passing a string of pitch names

    >>> from music21 import *
    >>> dmaj = chord.Chord(["D","F#","A"])


    Or you can combine already created Notes or Pitches:

    
    >>> C = note.Note()
    >>> C.name = 'C'
    >>> E = note.Note()
    >>> E.name = 'E'
    >>> G = note.Note()
    >>> G.name = 'G'
    

    And then create a chord with note objects:    


    >>> cmaj = chord.Chord([C, E, G])

    
    Chord has the ability to determine the root of a chord, as well as the bass note of a chord.
    In addition, Chord is capable of determining what type of chord a particular chord is, whether
    it is a triad or a seventh, major or minor, etc, as well as what inversion the chord is in. 
    
    NOTE: For now, the examples used in documentation give chords made from notes that are not
    defined. In the future, it may be possible to define a chord without first creating notes,
    but for now note that notes that appear in chords are simply shorthand instead of creating notes
    for use in examples
    
    '''
    
    _bass = None
    _root = None
    isChord = True
    isNote = False
    isRest = False

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['pitches']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'isChord': 'Boolean read-only value describing if this GeneralNote object is a Chord. Is True',
    'isNote': 'Boolean read-only value describing if this GeneralNote object is a Note. Is False',
    'isRest': 'Boolean read-only value describing if this GeneralNote object is a Rest. Is False',
    'beams': 'A :class:`music21.beam.Beams` object.',
    }
    # update inherited _DOC_ATTR dictionary
    _TEMPDOC = note.NotRest._DOC_ATTR
    _TEMPDOC.update(_DOC_ATTR)
    _DOC_ATTR = _TEMPDOC

    def __init__(self, notes = [], **keywords):
        # the list of pitch objects is managed by a property; this permits
        # only updating the _chordTablesAddress when pitches has changed
        
        # duration looks at _pitches to get first duration of a pitch 
        # if no other pitches are defined 
        self._pitches = [] # a list of dictionaries; each storing pitch, tie key
        self._chordTablesAddress = None
        self._chordTablesAddressNeedsUpdating = True # only update when needed
        # here, pitch and duration data is extracted from notes
        # if provided
        
        note.NotRest.__init__(self, **keywords)

        # inherit Duration object from GeneralNote
        # keep it here in case we have no notes
        #self.duration = None  # inefficient, since note.Note.__init__ set it
        #del(self.pitch)

        for n in notes:
            if isinstance(n, music21.pitch.Pitch):
                self._pitches.append({'pitch':n})
            elif isinstance(n, music21.note.Note):
                self._pitches.append({'pitch':n.pitch})
            elif isinstance(n, Chord):
                for p in n.pitches:
                    # this might better make a deepcopy of the pitch
                    self._pitches.append({'pitch':p})
            elif isinstance(n, basestring) or \
                isinstance(n, int):
                self._pitches.append({'pitch':music21.pitch.Pitch(n)})
            else:
                raise ChordException("Could not process pitch %s" % n)


        if "duration" in keywords or "type" in keywords or \
            "quarterLength" in keywords: #dots dont cut it
            self.duration = music21.duration.Duration(**keywords)

        elif len(notes) > 0:
            for thisNote in notes:
                # get duration from first note
                # but should other notes have the same duration?
                if hasattr(thisNote, "duration") and thisNote.duration != None:
                    self.duration = notes[0].duration
                    break

        if "beams" in keywords:
            self.beams = keywords["beams"]
        else:
            self.beams = beam.Beams()

        
    def _preDurationLily(self):
        '''
        Method to return all the lilypond information that appears before the 
        duration number.  This is called from GeneralNote .lily, but we are
        overriding the previously defined call. 
        
        '''
        baseName = "<"
        baseName += self.editorial.lilyStart()
        for thisPitch in self.pitches:
            baseName += thisPitch.step.lower()
            if (thisPitch.accidental):
                baseName += thisPitch.accidental.lily
            elif (self.editorial.ficta is not None):
                baseName += self.editorial.ficta.lily
            octaveModChars = ""
            if (thisPitch.octave < 3):
                correctedOctave = 3 - thisPitch.octave
                octaveModChars = ',' * correctedOctave #  C3 = c ; C2 = c, ; C1 = c,,
            else:
                correctedOctave = thisPitch.octave - 3
                octaveModChars  = '\'' * correctedOctave # C4 = c' ; C5 = c''  etc.
            baseName += octaveModChars
            if (self.editorial.ficta is not None):
                baseName += "!"  # always display ficta
            baseName += " "
        baseName = baseName.rstrip()
        baseName += ">"
        return baseName

    #---------------------------------------------------------------------------
    def __repr__(self):
        allPitches = []
        for thisPitch in self.pitches:
            allPitches.append(thisPitch.nameWithOctave)
        return "<music21.chord.Chord %s>" % ' '.join(allPitches)


    #---------------------------------------------------------------------------
    # properties

#     def _getDuration(self):
#         '''It is assumed that all notes ahve the same duration
#         '''
#     def _setDuration(self, value):
# 
#     property(_getDuration, _setDuration)

    def _getMidiEvents(self):
        return midiTranslate.chordToMidiEvents(self)

    def _setMidiEvents(self, eventList, ticksPerQuarter):

        midiTranslate.midiEventsToChord(eventList, 
            ticksPerQuarter, self)

    midiEvents = property(_getMidiEvents, _setMidiEvents, 
        doc='''Get or set this Chord as a list of :class:`music21.midi.base.MidiEvent` objects.

        >>> from music21 import *
        >>> c = chord.Chord(['c3','g#4', 'b5'])
        >>> c.midiEvents
        [<MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=48, velocity=90>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=68, velocity=90>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=83, velocity=90>, <MidiEvent DeltaTime, t=1024, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=48, velocity=0>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=68, velocity=0>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=83, velocity=0>]
        ''')

    def _getMidiFile(self):
        '''Provide a complete MIDI file representation. 
        '''
        return midiTranslate.chordToMidiFile(self)

    midiFile = property(_getMidiFile,
        doc = '''Return a complete :class:`music21.midi.base.MidiFile` object based on the Chord.

        The :class:`music21.midi.base.MidiFile` object can be used to write a MIDI file 
        of this Chord with default parameters using the :meth:`music21.midi.base.MidiFile.write` 
        method, given a file path. The file must be opened in 'wb' mode.  

        >>> from music21 import *
        >>> c = chord.Chord(['c3','g#4', 'b5'])
        >>> mf = c.midiFile
        >>> #_DOCS_SHOW mf.open('/Volumes/xdisc/_scratch/midi.mid', 'wb')
        >>> #_DOCS_SHOW mf.write()
        >>> #_DOCS_SHOW mf.close()
        ''')

    # moved to musicxml.translate
    def _getMX(self):
        return musicxmlTranslate.chordToMx(self)

    def _setMX(self, mxNoteList):
        # build parameters into self
        musicxmlTranslate.mxToChord(mxNoteList, self)

    mx = property(_getMX, _setMX)    

    #---------------------------------------------------------------------------
    # manage pitches property and chordTablesAddress

    def seekChordTablesAddress(self):
        '''Utility method to return the address to the chord table.

        Table addresses are TN based three character codes:
        cardinaltiy, Forte index number, inversion 

        Inversion is either 0 (for symmetrical) or -1/1

        NOTE: time consuming, and only should be run when necessary.

        >>> from music21 import *
        >>> c1 = chord.Chord(['c3'])
        >>> c1.orderedPitchClasses
        [0]
        >>> c1.seekChordTablesAddress()
        (1, 1, 0)

        >>> c1 = chord.Chord(['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'b'])
        >>> c1.seekChordTablesAddress()
        (11, 1, 0)

        >>> c1 = chord.Chord(['c', 'e', 'g'])
        >>> c1.seekChordTablesAddress()
        (3, 11, -1)

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.seekChordTablesAddress()
        (3, 11, 1)

        >>> c1 = chord.Chord(['c', 'c#', 'd#', 'e', 'f#', 'g#', 'a#'])
        >>> c1.seekChordTablesAddress()
        (7, 34, 0)

        >>> c1 = chord.Chord(['c', 'c#', 'd'])
        >>> c1.seekChordTablesAddress()
        (3, 1, 0)
        '''
        pcSet = self._getOrderedPitchClasses()   
        if len(pcSet) == 0:
            raise ChordException('cannot access chord tables address for Chord with %s pitches' % len(pcSet))

        #environLocal.printDebug(['calling seekChordTablesAddress:', pcSet])

        card = len(pcSet)
        if card == 1: # its a singleton: return
            return (1,1,0)
        elif card == 11: # its the only 11 note pcset
            return (11,1,0)
        elif card == 12: # its the aggregate
            return (12,1,0)
        # go through each rotation of pcSet
        candidates = []
        for rot in range(0, card):
            testSet = pcSet[rot:] + pcSet[0:rot]
            # transpose to lead with zero
            testSet = [(x-testSet[0]) % 12 for x in testSet]
            # create inversion; first take difference from 12 mod 12
            testSetInvert = [(12-x) % 12 for x in testSet]
            testSetInvert.reverse() # reverse order (first steps now last)
            # transpose all steps (were last) to zero, mod 12
            testSetInvert = [(x + (12 - testSetInvert[0])) % 12 
                            for x in testSetInvert]
            candidates.append([testSet, testSetInvert]) 

        # compare sets to those in table
        match = False
        for indexCandidate in range(len(chordTables.FORTE[card])):
            dataLine = chordTables.FORTE[card][indexCandidate]
            if dataLine == None: continue # spacer lines
            inversionsAvailable = chordTables.forteIndexToInversionsAvailable(
                                  card, indexCandidate)

            for candidate, candidateInversion in candidates:
                #environLocal.printDebug([candidate])
                # need to only match form
                if dataLine[0] == tuple(candidate): # must compare to tuple
                    if 0 in inversionsAvailable:
                        index, inversion = indexCandidate, 0
                    else:
                        index, inversion = indexCandidate, 1
                    match = True
                    break
                elif dataLine[0] == tuple(candidateInversion):
                    if 0 in inversionsAvailable:
                        index, inversion = indexCandidate, 0
                    else:
                        index, inversion = indexCandidate, -1
                    match = True
                    break
        if not match:
            raise ChordException('cannot find a chord table address for %s' % pcSet)
        return (card, index, inversion)                


    def _updateChordTablesAddress(self):
        if self._chordTablesAddressNeedsUpdating:
            self._chordTablesAddress = self.seekChordTablesAddress()
        self._chordTablesAddressNeedsUpdating = False

    def _getPitches(self):
        '''
        OMIT_FROM_DOCS

        TODO: presently, whenever pitches are accessed, it sets
        the _chordTablesAddressNeedsUpdating value to True
        this is b/c the pitches list can be accessed and appended to
        a better way to do this needs to be found
        '''
        self._chordTablesAddressNeedsUpdating = True
        post = [d['pitch'] for d in self._pitches]
        #return self._pitches
        return post

    def _setPitches(self, value):
        if value != [d['pitch'] for d in self._pitches]:
            self._chordTablesAddressNeedsUpdating = True
        self._pitches = []
        # assume we have pitch objects here
        for p in value:
            self._pitches.append({'pitch':p})

    pitches = property(_getPitches, _setPitches, 
        doc = '''Get or set a list of all Pitch objects in this Chord.

        >>> from music21 import *
        >>> c = chord.Chord(["C4", "E4", "G#4"])
        >>> c.pitches
        [C4, E4, G#4]
        >>> [p.midi for p in c.pitches]
        [60, 64, 68]
        
        >>> d = chord.Chord()
        >>> d.pitches = c.pitches
        >>> d.pitches
        [C4, E4, G#4]
        ''')


    def _setTie(self, value):
        '''If setting a tie, tie is applied to all pitches. 
        '''
        for d in self._pitches:
            # set the same instance for each pitch
            d['tie'] = value

    def _getTie(self):
        # this finds the tie on the first pitch; it might alternatively
        # return the first tie available 
        if len(self._pitches) > 0:
            if 'tie' in self._pitches[0].keys():
                return self._pitches[0]['tie']
        # otherwise, return None
        return None

    tie = property(_getTie, _setTie, 
        doc = '''Get or set a single tie based on all the ties in this Chord.

        This overloads the behavior of the tie attribute found in all NotRest classes.
        
        >>> from music21 import *
        >>> c1 = chord.Chord(['c4','g4'])
        >>> tie1 = tie.Tie('start')
        >>> c1.tie = tie1
        >>> c1.tie
        <music21.tie.Tie start>
        >>> c1.getTie(c1.pitches[1])
        <music21.tie.Tie start>
        ''')

    def getTie(self, p):
        '''Given a pitch in this Chord, return an associated Tie object, or return None if not defined for that Pitch.

        >>> from music21 import *
        >>> c1 = chord.Chord(['d', 'e-', 'b-'])
        >>> t1 = tie.Tie('start')
        >>> c1.setTie(t1, c1.pitches[2]) # just to b-
        >>> c1.getTie(c1.pitches[2]) == t1
        True
        >>> c1.getTie(c1.pitches[0]) == None
        True
        '''
        for d in self._pitches:
            # this is an equality comparison, not object
            if d['pitch'] == p:
                if 'tie' in d.keys():
                    return d['tie']
                else:
                    return None
        return None

    def setTie(self, t, pitchTarget):
        '''Given a pitch in this Chord, return an associated Tie object, or return None if not defined for that Pitch.

        >>> from music21 import *
        >>> c1 = chord.Chord(['d', 'e-', 'b-'])
        >>> t1 = tie.Tie('start')
        >>> c1.setTie(t1, c1.pitches[2]) # just to b-
        >>> c1.getTie(c1.pitches[2]) == t1
        True
        '''
        # assign to first pitch by default
        if pitchTarget is None and len(self._pitches) > 0: # if no pitch target
            pitchTarget = self._pitches[0]['pitch']
        match = False
        for d in self._pitches:
            if d['pitch'] == pitchTarget:
                d['tie'] = t
                match = True
                break
        if not match:
            raise ChordException('the given pitch is not in the Chord: %s' % pitchTarget)


    def _getPitchNames(self):
        return [d['pitch'].name for d in self._pitches]

    def _setPitchNames(self, value):
        if common.isListLike(value):
            if common.isStr(value[0]): # only checking first
                self._pitches = [] # clear
                for name in value:
                    self._pitches.append({'pitch':pitch.Pitch(name)})
            else:
                raise NoteException('must provide a list containing a Pitch, not: %s' % value)
        else:
            raise NoteException('cannot set pitch name with provided object: %s' % value)

        self._chordTablesAddressNeedsUpdating = True


    pitchNames = property(_getPitchNames, _setPitchNames, 
        doc = '''Return a list of Pitch names from each  :class:`~music21.pitch.Pitch` object's :attr:`~music21.pitch.Pitch.name` attribute.

        >>> from music21 import *
        >>> c = chord.Chord(['g#', 'd-'])
        >>> c.pitchNames
        ['G#', 'D-']
        >>> c.pitchNames = ['c2', 'g2']
        >>> c.pitchNames
        ['C', 'G']
        ''')



    def _getChordTablesAddress(self):
        '''
        >>> from music21 import *
        >>> c = chord.Chord(["C4", "E4", "G#4"])
        >>> c.chordTablesAddress
        (3, 12, 0)
        '''
        self._updateChordTablesAddress()
        return self._chordTablesAddress

    chordTablesAddress = property(_getChordTablesAddress, 
        doc = '''Return a triple tuple that represents that raw data location for information on the set class interpretation of this Chord. The data format is Forte set class cardinality, index number, and inversion status (where 0 is invariant, and -1 and 1 represent inverted or not, respectively).

        >>> from music21 import *
        >>> c = chord.Chord(["C4", "E4", "G#4"])
        >>> c.chordTablesAddress
        (3, 12, 0)
        ''')



# possibly add methods to create chords form pitch classes:
# c2 = chord.fromPitchClasses([0, 1, 3, 7])
    #---------------------------------------------------------------------------

    def transpose(self, value, inPlace=False):
        '''Transpose the Note by the user-provided value. If the value 
        is an integer, the transposition is treated in half steps and 
        enharmonics might be simplified (not done yet). If the value is a 
        string, any Interval string specification can be provided.

        if inPlace is set to True (default = False) then the original
        chord is changed.  Otherwise a new Chord is returned.

        >>> from music21 import *
        >>> a = chord.Chord(['g4', 'a3', 'c#6'])
        >>> b = a.transpose('m3')
        >>> b
        <music21.chord.Chord B-4 C4 E6>

        >>> aInterval = interval.Interval(-6)
        >>> b = a.transpose(aInterval)
        >>> b
        <music21.chord.Chord C#4 D#3 F##5>
        
        >>> a.transpose(aInterval, inPlace=True)
        >>> a
        <music21.chord.Chord C#4 D#3 F##5>
        '''
        if hasattr(value, 'diatonic'): # its an Interval class
            intervalObj = value
        else: # try to process
            intervalObj = interval.Interval(value)

        if not inPlace:
            post = copy.deepcopy(self)
        else:
            post = self
        
        for p in post.pitches:
            # we are either operating on self or a copy; always use inPlace
            p.transpose(intervalObj, inPlace=True)
            #pitches.append(intervalObj.transposePitch(p))

        if not inPlace:
            return post
        else:
            return None




    #---------------------------------------------------------------------------
    # analytical routines

    def bass(self, newbass = 0):
        '''returns the bass note or sets it to note.

        Usually defined to the lowest note in the chord,
        but we want to be able to override this.  You might want an implied
        bass for instance...  v o9.
        
        example:
        
        
        >>> from music21 import *
        >>> cmaj1stInv = chord.Chord(['C4', 'E3', 'G5'])
        >>> cmaj1stInv.bass() 
        E3
        '''
        if (newbass):
            self._bass = newbass
        elif (self._bass is None):
            self._bass = self._findBass()

        return self._bass

    def _findBass(self):
        ''' Returns the lowest note in the chord
        The only time findBass should be called is by bass() when it is figuring out what 
        the bass note of the chord is.
        Generally call bass() instead
        
        example:
        
        >>> from music21 import *
        >>> cmaj = chord.Chord(['C4', 'E3', 'G4'])
        >>> cmaj._findBass() # returns E3
        E3
        '''
        
        lowest = None
        
        for thisPitch in self.pitches:
            if (lowest is None):
                lowest = thisPitch
            else:
                lowest = interval.getWrittenLowerNote(lowest, thisPitch)
            
        return lowest
    

    def root(self, newroot=False):
        '''Returns or sets the Root of the chord.  if not set, will run findRoot (q.v.)
        
        example:
        
        
        >>> from music21 import *
        >>> cmaj = chord.Chord(['E3', 'C4', 'G5'])
        >>> cmaj.root()
        C4
        '''
        if newroot:
            self._root = newroot
        elif self._root is None:
            self._root = self.findRoot()
        return self._root

    def findRoot(self):
        ''' Looks for the root by finding the note with the most 3rds above it
        Generally use root() instead, since if a chord doesn't know its root, root() will
        run findRoot() automatically.
        
        example:
        >>> from music21 import *
        >>> cmaj = chord.Chord(['E', 'G', 'C'])
        >>> cmaj.findRoot() # returns C
        C
        '''
        oldRoots = copy.copy(self.pitches)
        newRoots = []
        roots = 0
        n = 3
        
        while True:
            if (len(oldRoots) == 1):
                return oldRoots[0]
            elif (len(oldRoots) == 0):
                raise ChordException("no notes in chord")
            for testRoot in oldRoots:
                if self.getChordStep(n, testRoot): ##n>7 = bug
                    newRoots.append(testRoot)
                    roots = roots + 1
            if (roots == 1):
                return newRoots.pop()
            elif (roots == 0):
                return oldRoots[0]
            oldRoots = newRoots
            newRoots = []
            n = n + 2
            if (n > 7):
                n = n - 7
            if (n == 6):
                raise ChordException("looping chord with no root: comprises all notes in the scale")
            roots = 0


# this was an old method of assigning duration to a Chord. better now is to use
# an overridden Duration property, as done below.

#     def duration(self, newDur = 0):
#         '''Duration of the chord can be defined here OR it should return the duration
#         of the first note of the chord
#         '''
#         if (newDur):
#             self._duration = newDur
#         elif (self._duration is None and len(self.pitches) > 0):
#             self._duration = self.pitches[0].duration
#         return self._duration


    def _getDuration(self):
        '''
        Gets the DurationObject of the object or None
        '''
        if self._duration is None and len(self._pitches) > 0:
            pitchZeroDuration = self._pitches[0]['pitch'].duration
            self._duration = pitchZeroDuration
        return self._duration

    def _setDuration(self, durationObj):
        '''Set a Duration object.
        '''
        if hasattr(durationObj, "quarterLength"):
            self._duration = durationObj
        else:
            # need to permit Duration object assignment here
            raise Exception('this must be a Duration object, not %s' % durationObj)

    duration = property(_getDuration, _setDuration, 
        doc = '''Get and set the duration of this Chord as a Duration object.

        >>> from music21 import *
        >>> c = chord.Chord(['a', 'c', 'e'])
        >>> c.duration
        <music21.duration.Duration 1.0>
        >>> d = duration.Duration()
        >>> d.quarterLength = 2
        >>> c.duration = d
        ''')

    def _getScaleDegrees(self):
        '''
        returns a list of two-element tuples for each
        pitch in the chord where the first element of the tuple
        is the scale degree as an int and the second is an Accidental
        object that specifies the alteration from the scale degree (could
        be None if the note is a part of the scale)
        
        
        It is easiest to see the utility of this method using a
        chord subclass, :class:`music21.roman.RomanNumeral`,
        but it is also callable from this Chord object if the
        Chord has a Key or Scale context set for it.
        
        
        >>> from music21 import *
        >>> k = key.Key('f#')  # 3-sharps minor

        >>> rn = roman.RomanNumeral('V', k)
        >>> rn.pitches
        [C#5, E#5, G#5]
        >>> rn.scaleDegrees
        [(5, None), (7, <accidental sharp>), (2, None)] 
        >>> rn2 = roman.RomanNumeral('N6', k)
        >>> rn2.pitches
        [B4, D5, G5]
        >>> rn2.scaleDegrees # N.B. -- natural form used for minor!
        [(4, None), (6, None), (2, <accidental flat>)]
        
        
        As mentioned above, the property can also get its scale from context if
        the chord is embedded in a Stream.  Let's great the same V in f#-minor
        again, but give it a context of c-sharp minor, and then c-minor instead:
        
        
        >>> chord1 = chord.Chord(["C#5", "E#5", "G#5"])
        >>> st1 = stream.Stream()
        >>> st1.append(key.Key('c#'))   # c-sharp minor
        >>> st1.append(chord1)
        >>> chord1.scaleDegrees
        [(1, None), (3, <accidental sharp>), (5, None)]
        
        
        >>> st2 = stream.Stream()
        >>> chord2 = chord.Chord(["C#5", "E#5", "G#5"])
        >>> st2.append(key.Key('c'))    # c minor
        >>> st2.append(chord2)          # same pitches as before gives different scaleDegrees
        >>> chord2.scaleDegrees
        [(1, <accidental sharp>), (3, <accidental double-sharp>), (5, <accidental sharp>)]
        
        
        >>> st3 = stream.Stream()
        >>> st3.append(key.Key('C'))    # C major
        >>> chord2 = chord.Chord(["C4","C#4","D4","E-4","E4","F4"])  # 1st 1/2 of chromatic
        >>> st3.append(chord2)
        >>> chord2.scaleDegrees
        [(1, None), (1, <accidental sharp>), (2, None), (3, <accidental flat>), (3, None), (4, None)]
                
        '''
        from music21 import scale
        if hasattr(self, 'scale') and self.scale != None: # roman numerals have this built in
            sc = self.scale
        else:

            sc = self.getContextByClass(scale.Scale, 
                prioritizeActiveSite=True, sortByCreationTime=True)
            if sc is None:
                raise ChordException("Cannot find a Key or Scale context for this chord, so cannot find what scale degrees the pitches correspond to!")            
        if hasattr(sc, 'mode'):
            mode = sc.mode       ### POSSIBLY USE to describe #7 etc. properly in minor -- not sure...
        else:
            mode = ""      
        degrees = []
        for thisPitch in self.pitches:
            degree = sc.getScaleDegreeFromPitch(thisPitch, comparisonAttribute='step', direction=scale.DIRECTION_DESCENDING)
            if degree is None:
                degrees.append((None, None))
            else:
                actualPitch = sc.pitchFromDegree(degree, direction=scale.DIRECTION_DESCENDING)
                if actualPitch.name == thisPitch.name:
                    degrees.append((degree, None))
                else:
                    actualPitch.octave = thisPitch.octave
                    degrees.append((degree, pitch.Accidental(int(thisPitch.ps - actualPitch.ps))))
        return degrees
    
    scaleDegrees = property(_getScaleDegrees)




    def semitonesFromChordStep(self, chordStep, testRoot = None):
        '''
        Returns the number of semitones (mod12) above the root
        that the chordStep lies (i.e., 3 = third of the chord; 5 = fifth, etc.)
        if one exists.  Or False if it does not exist.
        
        You can optionally specify a note.Note object to try as the root.  It does
        not change the Chord.root object.  We use these methods to figure out
        what the root of the triad is.

        Currently there is a bug that in the case of a triply diminished
        third (e.g., "c" => "e----"), this function will incorrectly claim
        no third exists.  Perhaps this be construed as a feature.

        In the case of chords such as C, E-, E, semitonesFromChordStep(3)
        will return the number for the first third, in this case 3.  It
        will not return 4, nor a list object (3,4).  You probably do not
        want to be using tonal chord manipulation functions on chords such
        as these anyway.  Check for such cases with 
        chord.hasAnyRepeatedDiatonicNote first.
        
        Tools with the expression "chordStep" in them refer to the diatonic 
        third, fifth, etc., of the chord.  They have little to do with
        the scale degree of the scale or key that the chord is embedded
        within.  See "chord.scaleDegrees" for this functionality.
        
        
        example:
        
        
        >>> from music21 import *
        >>> cchord = chord.Chord(['E3', 'C4', 'G5'])
        >>> cchord.semitonesFromChordStep(3) # distance from C to E
        4
        >>> cchord.semitonesFromChordStep(5) # C to G
        7
        >>> cchord.semitonesFromChordStep(6) # will return False
        False

        >>> achord = chord.Chord(['a2', 'c4', 'c#5', 'e#7'])
        >>> achord.semitonesFromChordStep(3) # returns the semitones to the FIRST third.
        3
        >>> achord.semitonesFromChordStep(5) 
        8
        >>> achord.semitonesFromChordStep(2) # will return False
        False

        '''
        tempInt = self.intervalFromChordStep(chordStep, testRoot)
        if tempInt is False:
            return False
        else:
            return tempInt.chromatic.mod12
    
    def _getThird(self):
        '''shortcut for getChordStep(3)'''
        return self.getChordStep(3)

    third = property(_getThird)

    def _getFifth(self):
        '''shortcut for getChordStep(5)'''
        return self.getChordStep(5)
    
    fifth = property(_getFifth)
    
    def _getSeventh(self):
        '''shortcut for getChordStep(7)'''
        return self.getChordStep(7)
    
    seventh = property(_getSeventh)
    
    def getChordStep(self, chordStep, testRoot = None):
        '''
        Exactly like semitonesFromChordStep, except it returns the (first) pitch at the 
        provided scaleDegree instead of the number of semitones.
        
        example:
        >>> from music21 import *
        >>> cmaj = chord.Chord(['C','E','G#'])
        >>> cmaj.getChordStep(3) # will return the third of the chord
        E
        >>> gis = cmaj.getChordStep(5) # will return the fifth of the chord
        >>> gis.name
        'G#'
        >>> cmaj.getChordStep(6)
        False
        '''
        if (testRoot is None):
            testRoot = self.root()
            if (testRoot is None):
                raise ChordException("Cannot run getChordStep without a root")

        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(testRoot, thisPitch)
            if (thisInterval.diatonic.generic.mod7 == chordStep):
                return thisPitch

        return False
    
    def intervalFromChordStep(self, chordStep, testRoot = None):
        '''Exactly like semitonesFromChordStep, except it returns the interval itself instead of the number
        of semitones.
        
        example:
        
        
        >>> from music21 import *
        >>> cmaj = chord.Chord(['C', 'E', 'G'])
        >>> cmaj.intervalFromChordStep(3) #will return the interval between C and E
        <music21.interval.Interval M3>
        >>> cmaj.intervalFromChordStep(5) #will return the interval between C and G
        <music21.interval.Interval P5>
        >>> cmaj.intervalFromChordStep(6) #will return False
        False
        '''
        if (testRoot is None):
            testRoot = self.root()
            if (testRoot is None):
                raise ChordException("Cannot run intervalFromChordStep without a root")

        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(testRoot, thisPitch)
            if (thisInterval.diatonic.generic.mod7 == chordStep):
                return thisInterval

        return False

    def hasRepeatedChordStep(self, chordStep, testRoot = None):
        '''Returns True if chordStep above testRoot (or self.root()) has two
        or more different notes (such as E and E-) in it.  Otherwise
        returns false.
       
        example:
       
       
        >>> from music21 import *
        >>> cchord = chord.Chord (['G2', 'E4', 'E-5', 'C6'])
        >>> cchord.hasRepeatedChordStep(3)
        True
        >>> cchord.hasRepeatedChordStep(5)
        False
        '''
        if (testRoot is None):
            testRoot = self.root()
            if (testRoot is None):
                raise ChordException("Cannot run hasRepeatedChordStep without a root")

        first = self.intervalFromChordStep(chordStep)
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(testRoot, thisPitch)
            if (thisInterval.diatonic.generic.mod7 == chordStep):
                if (thisInterval.chromatic.mod12 - first.chromatic.mod12 != 0):
                    return True
                
        return False

    def hasAnyRepeatedDiatonicNote(self, testRoot = None):
        '''Returns True if for any diatonic note (e.g., C or C# = C) there are two or more 
        different notes (such as E and E-) in the chord. If there are no repeated 
        scale degrees, return false.
        
        example:
        >>> from music21 import *
        >>> cchord = chord.Chord (['C', 'E', 'E-', 'G'])
        >>> other = chord.Chord (['C', 'E', 'F-', 'G'])
        >>> cchord.hasAnyRepeatedDiatonicNote() 
        True
        >>> other.hasAnyRepeatedDiatonicNote() # returns false (chromatically identical notes of different scale degrees do not count).
        False
        '''
        for i in range(1,8): ## == 1 - 7 inclusive
            if (self.hasRepeatedChordStep(i, testRoot) == True):
                return True
        return False

    def containsTriad(self):
        '''returns True or False if there is no triad above the root.
        "Contains vs. Is": A dominant-seventh chord contains a triad.
        
        example:
        >>> from music21 import *
        >>> cchord = chord.Chord(['C', 'E', 'G'])
        >>> other = chord.Chord(['C', 'D', 'E', 'F', 'G'])
        >>> cchord.containsTriad() #returns True
        True
        >>> other.containsTriad() #returns True
        True
        '''

        third = self.third
        fifth = self.fifth

        if (third is False or fifth is False):
            return False
        else:
            return True
        

    def isTriad(self):
        '''returns True or False
        "Contains vs. Is:" A dominant-seventh chord is NOT a triad.
        returns True if the chord contains at least one Third and one Fifth and all notes are
        equivalent to either of those notes. Only returns True if triad is spelled correctly.
        
        example:
        >>> from music21 import *
        >>> cchord = chord.Chord(['C', 'E', 'G'])
        >>> other = chord.Chord(['C', 'D', 'E', 'F', 'G'])
        >>> cchord.isTriad() # returns True   
        True
        >>> other.isTriad() 
        False
        '''
        third = self.third
        fifth = self.fifth

        if (third is False or fifth is False):
            return False
        
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.diatonic.generic.mod7 != 1) and (thisInterval.diatonic.generic.mod7 != 3) and (thisInterval.diatonic.generic.mod7 != 5):
                return False
            if (self.hasAnyRepeatedDiatonicNote() == True):
                return False
                
        return True

    def containsSeventh(self):
        ''' returns True if the chord contains at least one of each of Third, Fifth, and Seventh.
        raises an exception if the Root can't be determined
        
        >>> from music21 import *
        >>> cchord = chord.Chord(['C', 'E', 'G', 'B'])
        >>> other = chord.Chord(['C', 'D', 'E', 'F', 'G', 'B'])
        >>> cchord.containsSeventh() # returns True
        True
        >>> other.containsSeventh() # returns True
        True
        '''

        third = self.third
        fifth = self.fifth
        seventh = self.seventh

        if (third is False or fifth is False or seventh is False):
            return False
        else:
            return True
        

    def isSeventh(self):
        '''Returns True if chord contains at least one of each of Third, Fifth, and Seventh,
        and every note in the chord is a Third, Fifth, or Seventh, such that there are no 
        repeated scale degrees (ex: E and E-). Else return false.
        
        example:
        >>> from music21 import *
        >>> cchord = chord.Chord(['C', 'E', 'G', 'B'])
        >>> other = chord.Chord(['C', 'D', 'E', 'F', 'G', 'B'])
        >>> cchord.isSeventh() # returns True
        True
        >>> other.isSeventh() # returns False
        False
        '''
        
        third = self.third
        fifth = self.fifth
        seventh = self.seventh

        if (third is False or fifth is False or seventh is False):
            return False

        if self.hasAnyRepeatedDiatonicNote():
            return False

        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.diatonic.generic.mod7 != 1) and (thisInterval.diatonic.generic.mod7 != 3) and (thisInterval.diatonic.generic.mod7 != 5) and (thisInterval.diatonic.generic.mod7 != 7):
                return False
                
        return True

    def isMajorTriad(self):
        '''Returns True if chord is a Major Triad, that is, if it contains only notes that are
        either in unison with the root, a major third above the root, or a perfect fifth above the 
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.
        
        example:
        >>> from music21 import *
        >>> cchord = chord.Chord(['C', 'E', 'G'])
        >>> other = chord.Chord(['C', 'G'])
        >>> cchord.isMajorTriad() # returns True
        True
        >>> other.isMajorTriad() # returns False
        False
        '''
        third = self.third
        fifth = self.fifth
        if (third == False or fifth == False):
            return False
 
        ### TODO: rewrite so that [C,E+++,G---] does not return True

        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 4) and (thisInterval.chromatic.mod12 != 7):
                return False
        
        return True

    def isMinorTriad(self):
        '''Returns True if chord is a Minor Triad, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, or a perfect fifth above the 
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.
        
        example:
        >>> from music21 import *
        >>> cchord = chord.Chord(['C', 'E-', 'G'])
        >>> other = chord.Chord(['C', 'E', 'G'])
        >>> cchord.isMinorTriad() # returns True
        True
        >>> other.isMinorTriad() # returns False
        False
        '''
        third = self.third
        fifth = self.fifth
        if (third == False or fifth == False):
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3) and (thisInterval.chromatic.mod12 != 7):
                return False
        
        return True

    def isIncompleteMajorTriad(self):
        '''
        returns True if the chord is an incomplete Major triad, or, essentially,
        a dyad of root and major third
        
        >>> from music21 import *
        >>> c1 = chord.Chord(['C4','E3'])
        >>> c1.isMajorTriad()
        False
        >>> c1.isIncompleteMajorTriad()
        True
        
        
        Note that complete major triads return False:
        
        
        >>> c2 = chord.Chord(['C4','E3', 'G5'])
        >>> c2.isIncompleteMajorTriad()
        False

        OMIT_FROM_DOCS
        >>> c3 = chord.Chord(['C4','E-3'])
        >>> c3.isIncompleteMajorTriad()
        False        
        '''
        third = self.third
        if (third == False):
            return False
 
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 4):
                return False
        
        return True

    def isIncompleteMinorTriad(self):
        '''
        returns True if the chord is an incomplete Minor triad, or, essentially,
        a dyad of root and minor third
        
        >>> from music21 import *
        >>> c1 = chord.Chord(['C4','E-3'])
        >>> c1.isMinorTriad()
        False
        >>> c1.isIncompleteMinorTriad()
        True
        >>> c2 = chord.Chord(['C4','E-3', 'G5'])
        >>> c2.isIncompleteMinorTriad()
        False

        OMIT_FROM_DOCS
        >>> c3 = chord.Chord(['C4','E3'])
        >>> c3.isIncompleteMinorTriad()
        False        
        '''
        third = self.third
        if (third == False):
            return False
 
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3):
                return False
        
        return True



    def isDiminishedTriad(self):
        '''Returns True if chord is a Diminished Triad, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, or a diminished fifth above the 
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.
        
        >>> from music21 import *
        >>> cchord = chord.Chord(['C', 'E-', 'G-'])
        >>> other = chord.Chord(['C', 'E-', 'F#'])

        >>> cchord.isDiminishedTriad() #returns True
        True
        >>> other.isDiminishedTriad() #returns False
        False
        '''

        third = self.third
        fifth = self.fifth
        
        if (third is False or fifth is False):
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3) and (thisInterval.chromatic.mod12 != 6):
                return False
        
        return True

    def isAugmentedTriad(self):
        '''Returns True if chord is an Augmented Triad, that is, if it contains only notes that are
        either in unison with the root, a major third above the root, or an augmented fifth above the 
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord might NOT seem to have to be spelled correctly because incorrectly spelled Augmented Triads are
        usually augmented triads in some other inversion (e.g. C-E-Ab is a 2nd inversion aug triad; C-Fb-Ab
        is 1st inversion).  However, B#-Fb-Ab does return false as expeccted). 
        
        Returns false if is not an augmented triad.
        
        >>> import music21.chord
        >>> c = music21.chord.Chord(["C4", "E4", "G#4"])
        >>> c.isAugmentedTriad()
        True
        >>> c = music21.chord.Chord(["C4", "E4", "G4"])
        >>> c.isAugmentedTriad()
        False
        
        Other spellings will give other roots!
        >>> c = music21.chord.Chord(["C4", "E4", "A-4"])
        >>> c.isAugmentedTriad()
        True
        >>> c.root()
        A-4
        
        >>> c = music21.chord.Chord(["C4", "F-4", "A-4"])
        >>> c.isAugmentedTriad()
        True
        >>> c = music21.chord.Chord(["B#4", "F-4", "A-4"])
        >>> c.isAugmentedTriad()
        False
        '''
        third = self.third
        fifth = self.fifth

        if (third == False or fifth == False):
            return False
                
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 4) and (thisInterval.chromatic.mod12 != 8):
                return False
        return True

    def isDominantSeventh(self):
        '''Returns True if chord is a Dominant Seventh, that is, if it contains only notes that are
        either in unison with the root, a major third above the root, a perfect fifth, or a major seventh
        above the root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.

        >>> from music21 import *
        >>> a = chord.Chord(['b', 'g', 'd', 'f'])
        >>> a.isDominantSeventh()
        True
        '''
        
        third = self.third
        fifth = self.fifth
        seventh = self.seventh
        
        if (third == False or fifth == False or seventh == False):
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 4) and (thisInterval.chromatic.mod12 != 7) and (thisInterval.chromatic.mod12 != 10):
                return False
        
        return True

    def isDiminishedSeventh(self):
        '''Returns True if chord is a Diminished Seventh, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, a diminished fifth, or a minor seventh
        above the root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.

        >>> from music21 import *
        >>> a = chord.Chord(['c', 'e-', 'g-', 'b--'])
        >>> a.isDiminishedSeventh()
        True
        '''
        third = self.third
        fifth = self.fifth
        seventh = self.seventh
        
        if (third is False or fifth is False or seventh is False):
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3) and (thisInterval.chromatic.mod12 != 6) and (thisInterval.chromatic.mod12 != 9):
                return False
        return True
    
    
    def isHalfDiminishedSeventh(self):
        '''Returns True if chord is a Half Diminished Seventh, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, a diminished fifth, or a major seventh
        above the root. Additionally, must contain at least one of each third, fifth, and seventh above the root.
        Chord must be spelled correctly. Otherwise returns false.

        >>> from music21 import *
        >>> c1 = chord.Chord(['C4','E-4','G-4','B-4'])
        >>> c1.isHalfDiminishedSeventh()
        True
        
        Incorrectly spelled chords are not considered half-diminished sevenths
        >>> c2 = chord.Chord(['C4','E-4','G-4','A#4'])
        >>> c2.isHalfDiminishedSeventh()
        False
        
        Nor are incomplete chords
        >>> c3 = chord.Chord(['C4', 'G-4','B-4'])
        >>> c3.isHalfDiminishedSeventh()
        False
        '''
        third = self.third
        fifth = self.fifth
        seventh = self.seventh
        
        if (third is False or fifth is False or seventh is False):
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3) and (thisInterval.chromatic.mod12 != 6) and (thisInterval.chromatic.mod12 != 10):
                return False
        
        return True
    
    
    def isFalseDiminishedSeventh(self):
        '''Returns True if chord is a Diminished Seventh, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, a diminished fifth, or a minor seventh
        above the root. Additionally, must contain at least one of each third and fifth above the root.
        Chord MAY BE SPELLED INCORRECTLY. Otherwise returns false.
        '''
        third = False
        fifth = False
        seventh = False
        
        
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3) and (thisInterval.chromatic.mod12 != 6) and (thisInterval.chromatic.mod12 != 9):
                return False
            elif (thisInterval.chromatic.mod12 == 3):
                third = True
            elif (thisInterval.chromatic.mod12 == 6):
                fifth = True
            elif (thisInterval.chromatic.mod12 == 9):
                seventh = True
        if (third is False or fifth is False or seventh is False):
            return False
        
        return True
    
    def isConsonant(self):
        '''
        returns True if the chord is
             one PC
             two PCs is a major or minor third or sixth or perfect fifth.
             three PCs and is a major or minor triad not in second inversion.

        These rules define all common-practice consonances (and earlier back to about 1300 all imperfect consonances)

        >>> from music21 import *
        >>> c1 = chord.Chord(['C3', 'E4', 'G5'])
        >>> c1.isConsonant()
        True
        >>> c2 = chord.Chord(['G3', 'E-4', 'C5'])
        >>> c2.isConsonant()
        False
        >>> c3 = chord.Chord(['F2','A2','C3','E-3'])
        >>> c3.isConsonant()
        False
        >>> c4 = chord.Chord(['C1','G1','C2','G2','C3','G3'])
        >>> c4.isConsonant()
        True
        >>> c5 = chord.Chord(['G1','C2','G2','C3','G3'])
        >>> c5.isConsonant()
        False
        >>> c6 = chord.Chord(['F#'])
        >>> c6.isConsonant()
        True
        >>> c7 = chord.Chord(['C1','C#1','D-1'])
        >>> c7.isConsonant()
        False
        
        
        Spelling does matter
        
        
        >>> c8 = chord.Chord(['D-4','G#4'])
        >>> c8.isConsonant()
        False
        >>> c9 = chord.Chord(['D3','A2','D2','D2','A4'])
        >>> c9.isConsonant()
        True
        >>> c10 = chord.Chord(['D3','A2','D2','D2','A1'])
        >>> c10.isConsonant()
        False
        
        >>> c11 = chord.Chord(['F3','D4','A4'])
        >>> c11.isConsonant()
        True
        >>> c12 = chord.Chord(['F3','D4','A4','E#4'])
        >>> c12.isConsonant()
        False
        
        '''
        c2 = self.removeRedundantPitchNames(inPlace = False)
        if len(c2.pitches) == 1:  
            return True
        elif len(c2.pitches) == 2:
            c3 = self.closedPosition()
            c4 = c3.removeRedundantPitches(inPlace = False) # to get from lowest to highest for P4 protection
            
            i = interval.notesToInterval(c4.pitches[0], c4.pitches[1])
            if i.simpleName == 'P5' or i.simpleName == 'm3' or i.simpleName == 'M3' or i.simpleName == 'm6' or i.simpleName == 'M6':
                return True
            else:
                return False
        elif len(c2.pitches) == 3:
            if (self.isMajorTriad() is True or self.isMinorTriad() is True) and (self.inversion() != 2):
                return True
            else:
                return False
        else:
            return False
    
    def _getQuality(self):
        '''
        returns the quality of the underlying triad of a triad or 
        seventh, either major, minor, diminished, augmented, or other.

        >>> from music21 import *
        >>> a = chord.Chord(['a', 'c', 'e'])
        >>> a.quality
        'minor'

        Inversions don't matter.

        >>> a = chord.Chord(['f', 'b', 'd', 'g'])
        >>> a.quality
        'major'

        >>> a = chord.Chord(['c', 'a-', 'e'])
        >>> a.quality
        'augmented'

        >>> a = chord.Chord(['c','c#','d'])
        >>> a.quality
        'other'

        '''
        third = self.semitonesFromChordStep(3)
        fifth = self.semitonesFromChordStep(5)
        if third == None:
            return "other"        
        elif self.hasRepeatedChordStep(3):
            return "other"
        elif fifth == None:
            if third.semitones == 4:
                return "major"
            elif third.semitones == 3:
                return "minor"
            else:
                return "other"
        elif self.hasRepeatedChordStep(5):
            return "other"
        elif fifth == 7 and third == 4:
            return "major"
        elif fifth == 7 and third == 3:
            return "minor"
        elif fifth == 8 and third == 4:
            return "augmented"
        elif fifth == 6 and third == 3:
            return "diminished"
        else:
            return "other"
   
    quality = property(_getQuality)
     
    def canBeDominantV(self):
        '''
        Returns True if the chord is a Major Triad or a Dominant Seventh

        >>> from music21 import *
        >>> a = chord.Chord(['g', 'b', 'd', 'f'])
        >>> a.canBeDominantV()
        True
        '''
        if (self.isMajorTriad() or self.isDominantSeventh()):
            return True
        else: 
            return False
        

    def canBeTonic(self):
        '''
        returns True if the chord is a major or minor triad

        >>> from music21 import *
        >>> a = chord.Chord(['g', 'b', 'd', 'f'])
        >>> a.canBeTonic()
        False
        >>> a = chord.Chord(['g', 'b', 'd'])
        >>> a.canBeTonic()
        True
        '''
        if (self.isMajorTriad() or self.isMinorTriad()):
            return True
        else: 
            return False

    def inversion(self):
        ''' returns an integer representing which standard inversion the chord is in. Chord
        does not have to be complete, but determines the inversion by looking at the relationship
        of the bass note to the root.

        >>> from music21 import *
        >>> a = chord.Chord(['g', 'b', 'd', 'f'])
        >>> a.inversion()
        2
        '''
        
        bassNote = self.bass()
        
        bassToRoot = interval.notesToInterval(bassNote, self.root()).generic.simpleDirected
        
        if (bassToRoot == 1):
            return 0
        elif (bassToRoot == 6):
            return 1
        elif (bassToRoot == 4):
            return 2
        elif (bassToRoot == 2):
            return 3
        else:
            raise ChordException("Not a normal inversion")

    def inversionName(self):
        ''' 
        Returns an integer representing the common abbreviation 
        for the inversion the chord is in.
        If chord is not in a common inversion, returns None.

        Third inversion sevenths return 42 not 2

        >>> from music21 import *
        >>> a = chord.Chord(['G3', 'B3', 'F3', 'D3'])
        >>> a.inversionName()
        43
        '''
        try:
            inv = self.inversion()
        except ChordException:
            return None
        
        if self.isSeventh() or self.seventh is not False:
            if inv == 0:
                return 7
            elif inv == 1:
                return 65
            elif inv == 2:
                return 43
            elif inv == 3:
                return 42
            else:
                raise ChordException("Not a normal inversion")
        elif self.isTriad():
            if inv == 0:
                return 53
            elif inv == 1:
                return 6
            elif inv == 2:
                return 64
            else:
                raise ChordException("Not a normal inversion")
        else:
            raise ChordException("Not a triad")
 
    def closedPosition(self, forceOctave=None, inPlace=False):
        '''Returns a new Chord object with the same pitch classes, but now in closed position.

        If `forcedOctave` is provided, the bass of the chord will be shifted to that provided octave.

        >>> from music21 import *
        >>> chord1 = chord.Chord(["C#4", "G5", "E6"])
        >>> chord2 = chord1.closedPosition()
        >>> print(chord2.lily.value)
        <cis' e' g'>4

        >>> c2 = chord.Chord(["C#4", "G5", "E6"])
        >>> str(c2.closedPosition(2).pitches)
        '[C#2, E2, G2]'

        >>> c2 = chord.Chord(["C#4", "G5", "E6"])
        >>> str(c2.closedPosition(6).pitches)
        '[C#6, E6, G6]'
        '''
        #environLocal.printDebug(['calling closedPosition()', inPlace])
        if inPlace:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)
        #tempChordNotes = returnObj.pitches

        pBass = returnObj.bass() # returns a reference, not a copy
        if forceOctave is not None:
            if pBass.octave > forceOctave:      
                dif = -1
            elif pBass.octave < forceOctave:      
                dif = 1
            else: # equal
                dif = None
            if dif != None:
                while pBass.octave != forceOctave:
                    # shift octave of all pitches
                    for p in returnObj.pitches:
                        p.octave += dif

        # can change these pitches in place
        for p in returnObj.pitches:
            # bring each pitch down octaves until pitch space is 
            # within an octave
            while p.ps > pBass.ps + 12:
                p.octave -= 1      

        # if not inPlace, creates a second new chord object!
        return returnObj.sortAscending(inPlace=True) 

    def semiClosedPosition(self):
        '''
        TODO: Write
        
        moves everything within an octave EXCEPT if there's already 
        a pitch at that step, then it puts it up an octave.  It's a 
        very useful display standard for dense post-tonal chords.
        '''
        raise ChordException('not yet implemented')

    #---------------------------------------------------------------------------
    # annotations

    def annotateIntervals(self, stripSpecifiers=True, sortPitches=False):
        # make a copy of self for reducing pitches, but attach to self
        c = copy.deepcopy(self)

        # this could be an option
        c.removeRedundantPitches(inPlace=True)
        if sortPitches:
            c.sortAscending()
        #environLocal.printDebug(['annotateIntervals()', c.pitches])
        for j in range(len(c.pitches)-1, 0, -1): # only go to zero 
            if j == 0: 
                continue # first is lowest
            p = c.pitches[j]
            i = interval.Interval(c.pitches[0], p)
            notation = i.semiSimpleName
            # remove perfect
            if stripSpecifiers:
                notation = notation.lower().replace('p', '')
                notation = notation.replace('m', '')
                notation = notation.replace('d', '')
                notation = notation.replace('a', '')
            self.addLyric(notation)


    #---------------------------------------------------------------------------
    # new methods for forte/pitch class data

    def _formatVectorString(self, vectorList):
        '''
        Return a string representation of a vector or set

        >>> from music21 import *
        >>> c1 = chord.Chord(["D4", "A4", "F#5", "D6"])
        >>> c1._formatVectorString([3,4,5])
        '<345>'
        >>> c1._formatVectorString([10,11,3,5])
        '<AB35>'
        '''
        msg = ['<']
        for e in vectorList: # should be numbers
            eStr = pitch.convertPitchClassToStr(e)
            msg.append(eStr)
        msg.append('>')
        return ''.join(msg)


    def _getPitchClasses(self):
        '''Return a pitch class representation ordered as the original chord.
        '''
        pcGroup = []
        for p in self.pitches:
            pcGroup.append(p.pitchClass)
        return pcGroup            
        
    pitchClasses = property(_getPitchClasses, 
        doc = '''Return a list of all pitch classes in the chord as integers.

        >>> from music21 import *
        >>> c1 = chord.Chord(["D4", "A4", "F#5", "D6"])
        >>> c1.pitchClasses
        [2, 9, 6, 2]
        ''')    


    def _getMultisetCardinality(self):
        '''Return the number of pitches, regardless of redundancy.
        '''            
        return len(self._getPitchClasses())

    multisetCardinality = property(_getMultisetCardinality, 
        doc = '''Return an integer representing the cardinality of the mutliset, or the number of pitch values. 

        >>> from music21 import *
        >>> c1 = chord.Chord(["D4", "A4", "F#5", "D6"])
        >>> c1.multisetCardinality
        4
        ''')   


    def _getOrderedPitchClasses(self):
        '''Return a pitch class representation ordered by pitch class and removing redundancies.

        This is a traditional pitch class set.
        '''
        pcGroup = []
        for p in self.pitches:
            if p.pitchClass in pcGroup: continue
            pcGroup.append(p.pitchClass)
        pcGroup.sort()
        return pcGroup            
        
    orderedPitchClasses = property(_getOrderedPitchClasses, 
        doc = '''Return an list of pitch class integers, ordered form lowest to highest. 

        >>> from music21 import *
        >>> c1 = chord.Chord(["D4", "A4", "F#5", "D6"])
        >>> c1.orderedPitchClasses
        [2, 6, 9]
        ''')    


    def _getOrderedPitchClassesString(self):        
        return self._formatVectorString(self._getOrderedPitchClasses())

    orderedPitchClassesString = property(_getOrderedPitchClassesString, 
        doc = '''Return a string representation of the pitch class values. 

        >>> from music21 import *
        >>> c1 = chord.Chord(['f#', 'e-', 'g'])
        >>> c1.orderedPitchClassesString
        '<367>'
        ''')    



    def _getPitchClassCardinality(self):
        '''Return the number of unique pitch classes
        '''            
        return len(self._getOrderedPitchClasses())

    pitchClassCardinality = property(_getPitchClassCardinality, 
        doc = '''Return a the cardinality of pitch classes, or the number of unique pitch classes, in the Chord.

        >>> from music21 import *
        >>> c1 = chord.Chord(["D4", "A4", "F#5", "D6"])
        >>> c1.pitchClassCardinality
        3
        ''')    


    def _getForteClass(self):
        '''Return a forte class name

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.forteClass
        '3-11A'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClass
        '3-11B'
        '''
        self._updateChordTablesAddress()
        return chordTables.addressToForteName(self._chordTablesAddress, 'tn')

    forteClass = property(_getForteClass, 
        doc = '''Return the Forte set class name as a string. This assumes a Tn formation, where inversion distinctions are represented. 

        >>> from music21 import *
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClass
        '3-11B'
        ''')    

    forteClassTn = property(_getForteClass, 
        doc = '''Return the Forte Tn set class name, where inversion distinctions are represented.

        >>> from music21 import *
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClassTn
        '3-11B'
        ''')    

    def _getForteClassTnI(self):
        '''Return a forte class name under TnI classification

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.forteClassTnI
        '3-11'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClassTnI
        '3-11'
        '''
        self._updateChordTablesAddress()
        return chordTables.addressToForteName(self._chordTablesAddress, 'tni')

    forteClassTnI = property(_getForteClassTnI, 
        doc = '''Return the Forte TnI class name, where inversion distinctions are not represented.

        >>> from music21 import *
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClassTnI
        '3-11'
        ''')    


    def _getNormalForm(self):
        '''
        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.normalForm
        [0, 3, 7]

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.normalForm
        [0, 4, 7]
        '''
        self._updateChordTablesAddress()
        return list(chordTables.addressToNormalForm(self._chordTablesAddress))
        
    normalForm = property(_getNormalForm, 
        doc = '''Return the normal form of the Chord represented as a list of integers. 

        >>> from music21 import *
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.normalForm
        [0, 4, 7]
        ''')    

    def _getNormalFormString(self):        
        '''
        >>> from music21 import *
        >>> c1 = chord.Chord(['f#', 'e-', 'g'])
        >>> c1.normalFormString
        '<034>'
        '''
        return self._formatVectorString(self._getNormalForm())

    normalFormString = property(_getNormalFormString, 
        doc = '''Return a string representation of the normal form of the Chord.

        >>> from music21 import *
        >>> c1 = chord.Chord(['f#', 'e-', 'g'])
        >>> c1.normalFormString
        '<034>'
        ''')    

    def _getForteClassNumber(self):
        '''Get the Forte class index number.

        Possible rename forteIndex

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.forteClassNumber
        11
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClassNumber
        11
        '''
        self._updateChordTablesAddress()
        return self._chordTablesAddress[1] # the second value
        
    forteClassNumber = property(_getForteClassNumber, 
        doc = '''Return the number of the Forte set class within the defined set group. That is, if the set is 3-11, this method returns 11.

        >>> from music21 import *
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClassNumber
        11
        ''')    

    def _getPrimeForm(self):
        '''Get the Forte class index number.

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.primeForm
        [0, 3, 7]
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.primeForm
        [0, 3, 7]
        '''
        self._updateChordTablesAddress()
        return list(chordTables.addressToPrimeForm(self._chordTablesAddress))
        
    primeForm = property(_getPrimeForm, 
        doc='''Return a representation of the Chord as a prime-form list of pitch class integers.

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.primeForm
        [0, 3, 7]
       ''')    

    def _getPrimeFormString(self):        
        '''
        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.primeFormString
        '<037>'
        '''
        return self._formatVectorString(self._getPrimeForm())

    primeFormString = property(_getPrimeFormString, 
        doc='''Return a representation of the Chord as a prime-form set class string.

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.primeFormString
        '<037>'
        ''')    


    def _getIntervalVector(self):
        '''Get the Forte class index number.

        Possible rename forteIndex

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.intervalVector
        [0, 0, 1, 1, 1, 0]
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.intervalVector
        [0, 0, 1, 1, 1, 0]
        '''
        self._updateChordTablesAddress()
        return list(chordTables.addressToIntervalVector(
               self._chordTablesAddress))
        
    intervalVector = property(_getIntervalVector, 
        doc = '''Return the interval vector for this Chord as a list of integers.

        >>> from music21 import *
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.intervalVector
        [0, 0, 1, 1, 1, 0]
        ''')    

    def _getIntervalVectorString(self):        
        '''
        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.intervalVectorString
        '<001110>'
        '''
        return self._formatVectorString(self._getIntervalVector())

    intervalVectorString = property(_getIntervalVectorString, 
        doc = '''Return the interval vector as a string representation.

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.intervalVectorString
        '<001110>'
        ''')    


    def _isPrimeFormInversion(self):
        '''
        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.isPrimeFormInversion
        False
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.isPrimeFormInversion
        True
        '''
        self._updateChordTablesAddress()
        if self._chordTablesAddress[2] == -1:
            return True
        else:
            return False
        
    isPrimeFormInversion = property(_isPrimeFormInversion, 
        doc = '''Return True or False if the Chord represents a set class inversion. 

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.isPrimeFormInversion
        False
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.isPrimeFormInversion
        True
        ''')    


    def _hasZRelation(self):
        '''Get the Z-relation status

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.hasZRelation
        False
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.hasZRelation
        False
        '''
        self._updateChordTablesAddress()
        post = chordTables.addressToZAddress(self._chordTablesAddress)
        #environLocal.printDebug(['got post', post])
        if post == None:
            return False
        else:
            return True
        
    hasZRelation = property(_hasZRelation, 
        doc = '''Return True or False if the Chord has a Z-relation.

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.hasZRelation
        False
        ''')    

# c2.getZRelation()  # returns a list in non-ET12 space...
# <music21.chord.ForteSet at 0x234892>

    def areZRelations(self, other):
        '''Check of chord other is also a z relations

        >>> from music21 import *
        >>> c1 = chord.Chord(["C", "c#", "e", "f#"])
        >>> c2 = chord.Chord(["C", "c#", "e-", "g"])
        >>> c3 = chord.Chord(["C", "c#", "f#", "g"])
        >>> c1.areZRelations(c2)
        True
        >>> c1.areZRelations(c3)
        False
        '''
        self._updateChordTablesAddress()
        post = chordTables.addressToZAddress(self._chordTablesAddress)
        if post == None:
            return False
        else: # check of other is a z relation
            zRelationAddress = chordTables.addressToZAddress(
                self._chordTablesAddress)
            if other.chordTablesAddress == zRelationAddress:
                return True
            else:
                return False

    def _getCommonName(self):
        self._updateChordTablesAddress()
        ctn = chordTables.addressToCommonNames(self._chordTablesAddress)
        if len(ctn) == 0:
            return ''
        else:
            return ctn[0]
        
    commonName = property(_getCommonName, 
        doc = '''
        return the most common name associated with this Chord as a string.
        does not currently check enharmonic equivalents.

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.commonName
        'minor triad'

        >>> from music21 import *
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.commonName
        'major triad'

        >>> from music21 import *
        >>> c3 = chord.Chord(['c', 'd-', 'e', 'f#'])
        >>> c3.commonName
        'all-interval tetrachord'

        ''')    


    def _getPitchedCommonName(self):
        '''Get the common name of the TN set class.

        >>> from music21 import *
        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.pitchedCommonName
        'C-minor triad'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.pitchedCommonName
        'C-major triad'
        '''
        self._updateChordTablesAddress()
        post = chordTables.addressToCommonNames(self._chordTablesAddress)
        if post != None:
            nameStr = post[0] # get first
        else:
            nameStr = ''

        try:
            root = self.root()
        except ChordException: # if a root cannot be found
            root = self.pitches[0]

        return '%s-%s' % (self.root(), nameStr)

    pitchedCommonName = property(_getPitchedCommonName, 
        doc = '''Return the common name of this Chord preceded by its root, if a root is available.

        >>> from music21 import *
        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.pitchedCommonName
        'C-major triad'
        ''')    


    #---------------------------------------------------------------------------
    # remove routines

    def _removePitchByRedundantAttribute(self, attribute, inPlace):
        '''Common method for stripping pitches based on redundancy of one pitch attribute. The `attribute` is provided by a string. 
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        unique = []
        delete = []
        for p in returnObj.pitches:
            if getattr(p, attribute) not in unique:
                unique.append(getattr(p, attribute)) 
            else:
                delete.append(p)

        #environLocal.printDebug(['unique, delete', self, unique, delete])
        altered = returnObj.pitches
        for p in delete:
            altered.remove(p)

        returnObj.pitches = altered
        if len(delete) > 0:
            returnObj._chordTablesAddressNeedsUpdating = True

        if not inPlace:
            return returnObj



    def removeRedundantPitches(self, inPlace=True):
        '''Remove all but one instance of a pitch with more than one instance. 
        
        If `inPlace` is True, a copy is not made and None is returned; otherwise a copy is made and that copy is returned.

        >>> from music21 import *
        >>> c1 = chord.Chord(['c2', 'e3', 'g4', 'e3'])
        >>> c1.removeRedundantPitches()
        >>> c1.pitches
        [C2, G4, E3]
        >>> c1.forteClass
        '3-11B'

        >>> c2 = chord.Chord(['c2', 'e3', 'g4', 'c5'])
        >>> c2.removeRedundantPitches()
        >>> c2.pitches
        [C2, E3, G4, C5]
        >>> c1.forteClass
        '3-11B'

        '''
        return self._removePitchByRedundantAttribute('nameWithOctave',
              inPlace=inPlace)


    def removeRedundantPitchClasses(self, inPlace=True):
        '''Remove all but the FIRST instance of a pitch class with more than one instance of that pitch class.

        If `inPlace` is True, a copy is not made and None is returned; otherwise a copy is made and that 
        copy is returned.

        >>> from music21 import *
        >>> c1 = chord.Chord(['c2', 'e3', 'g4', 'e3'])
        >>> c1.removeRedundantPitchClasses()
        >>> c1.pitches
        [C2, G4, E3]

        >>> c2 = chord.Chord(['c5', 'e3', 'g4', 'c2', 'e3', 'f-4'])
        >>> c2.removeRedundantPitchClasses()
        >>> c2.pitches
        [C5, G4, E3]

        '''
        return self._removePitchByRedundantAttribute('pitchClass',
              inPlace=inPlace)

    def removeRedundantPitchNames(self, inPlace=True):
        '''Remove all but the FIRST instance of a pitch class with more than one instance of that pitch name
        regardless of octave (but note that spelling matters, so that in the example, the F-flat stays even
        though there is already an E.

        If `inPlace` is True, a copy is not made and None is returned; otherwise a copy is made and that 
        copy is returned.

        >>> from music21 import *
        >>> c2 = chord.Chord(['c5', 'e3', 'g4', 'c2', 'e3', 'f-4'])
        >>> c2.removeRedundantPitchNames()
        >>> c2.pitches
        [C5, G4, E3, F-4]

        '''
        return self._removePitchByRedundantAttribute('name',
              inPlace=inPlace)



    #---------------------------------------------------------------------------
    # sort routines

        
    def sortDiatonicAscending(self, inPlace=False):
        '''        
        The notes are sorted by Scale degree and then by Offset (so F## sorts below G-).  
        Notes that are the identical pitch retain their order
        
        After talking with Daniel Jackson, let's try to make the chord object as immutable
        as possible, so we return a new Chord object with the notes arranged from lowest to highest


        >>> from music21 import *
        >>> cMajUnsorted = chord.Chord(['E4', 'C4', 'G4'])
        >>> cMajSorted = cMajUnsorted.sortDiatonicAscending()
        >>> cMajSorted.pitches[0].name
        'C'

        >>> c2 = chord.Chord(['E4', 'C4', 'G4'])
        >>> junk = c2.sortDiatonicAscending(inPlace=True)
        >>> c2
        <music21.chord.Chord C4 E4 G4>
        '''

        if inPlace:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)

        altered = returnObj.pitches
        altered.sort(cmp=lambda x,y: cmp(x.diatonicNoteNum, y.diatonicNoteNum)
                     or cmp(x.ps, y.ps))
        # must re-assign altered list, as a new list is created
        returnObj.pitches = altered

        return returnObj

    def sortAscending(self, inPlace=False):
        # TODO: Check context
        return self.sortDiatonicAscending(inPlace=inPlace)

    
    def sortChromaticAscending(self):
        '''
        Same as sortAscending but notes are sorted by midi number, so F## sorts above G-.
        '''
        newChord = copy.deepcopy(self)
        tempChordNotes = newChord.pitches
        tempChordNotes.sort(cmp=lambda x,y: cmp(x.ps, y.ps))
        newChord.pitches = tempChordNotes
        return newChord
    
    def sortFrequencyAscending(self):
        '''
        Same as above, but uses a note's frequency to determine height; so that
        C# would be below D- in 1/4-comma meantone, equal in equal temperament,
        but below it in (most) just intonation types.
        '''
        newChord = copy.deepcopy(self)
        tempChordNotes = newChord.pitches
        tempChordNotes.sort(cmp=lambda x,y: cmp(x.frequency, y.frequency))
        newChord.pitches = tempChordNotes
        return newChord
    







#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        for pitchList in [['g2', 'c4', 'c#6'], ['c', 'd-', 'f#', 'g']]:
            a = Chord(pitchList)
            a.show()

    def testPostTonalChords(self): 
        import random
        from music21 import note, stream
        s = stream.Stream()
        for x in range(30):
            chordRaw = []
            for p in range(random.choice([3,4,5,6,7,8])):
                pc = random.choice(range(0,12))
                if pc not in chordRaw:
                    chordRaw.append(pc)
            c = Chord(chordRaw)
            c.quarterLength = 4
            c.addLyric(c.forteClass)
            c.addLyric(str(c.primeForm).replace(' ', ''))
            s.append(c)
        s.show()


class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    

    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)

        c1 = Chord(['C4','E-4','G4'])
        c2 = copy.deepcopy(c1)
        c1.pitches[0].accidental = pitch.Accidental('sharp')
        c1.pitches[1].accidental.set(1)
        self.assertEqual(c1.__repr__(), "<music21.chord.Chord C#4 E#4 G4>")
        self.assertEqual(c2.__repr__(), "<music21.chord.Chord C4 E-4 G4>")
        
        c1 = Chord(["C#3", "E4"])
        c2 = copy.deepcopy(c1)
        self.assertTrue(c1 is not c2)
        self.assertTrue(c1.pitches[0] is not c2.pitches[0])
        self.assertTrue(c1.pitches[0].accidental is not c2.pitches[0].accidental)

        from music21 import stream
        stream1 = stream.Stream()
        stream1.append(c1)
        stream2 = copy.deepcopy(stream1)
        self.assertTrue(stream1 is not stream2)
        self.assertTrue(stream1.notes[0].pitches[0] is not stream2.notes[0].pitches[0])
        self.assertTrue(stream1.notes[0].pitches[0].accidental is not stream2.notes[0].pitches[0].accidental)
        


    def testConstruction(self):
        HighEFlat = note.Note ()
        HighEFlat.name = 'E-'
        HighEFlat.octave = 5
    
        a = note.Note()
        b = note.Note()
        assert isinstance(a, music21.note.Note)
        assert isinstance(a, music21.note.Note)
        assert isinstance(b, music21.note.Note)
        assert isinstance(b, music21.note.Note)
    
        MiddleC = note.Note ()
        MiddleC.name = 'C'
        MiddleC.octave = 4
    
        LowG = pitch.Pitch ()
        LowG.name = 'G'
        LowG.octave = 3
    
        chord1 = Chord([HighEFlat, MiddleC, LowG])
        assert chord1.getChordStep(3, testRoot = MiddleC) is not False
        chord1.root(MiddleC)
    
        HighAFlat = note.Note()
        HighAFlat.name = "A-"
        HighAFlat.octave = 5
        
        chord2 = Chord([MiddleC, HighEFlat, LowG, HighAFlat])
        assert chord1.third is not False
        assert chord1.fifth is not False
        assert chord1.containsTriad()  == True
        assert chord1.isTriad() == True
        assert chord2.containsTriad() == True
        assert chord2.isTriad() == False
        
        MiddleE = note.Note()
        MiddleE.name = 'E'
        MiddleE.octave = 4
    
        chord3 = Chord([MiddleC, HighEFlat, LowG, MiddleE])
        assert chord3.isTriad() == False
        
        MiddleB = note.Note()
        MiddleB.name = 'B'
        MiddleB.octave = 4
        
        chord4 = Chord([MiddleC, HighEFlat, LowG, MiddleB])
        assert chord4.containsSeventh() == True
        assert chord3.containsSeventh() == False
        assert chord4.isSeventh() == True
        
        chord5 = Chord([MiddleC, HighEFlat, LowG, MiddleE, MiddleB])
        assert chord5.isSeventh() == False
        
        chord6 = Chord([MiddleC, MiddleE, LowG])
        assert chord6.isMajorTriad() == True
        assert chord3.isMajorTriad() == False
        
        chord7 = Chord([MiddleC, HighEFlat, LowG])
        assert chord7.isMinorTriad() == True
        assert chord6.isMinorTriad() == False
        assert chord4.isMinorTriad() == False
        
        LowGFlat = note.Note()
        LowGFlat.name = 'G-'
        LowGFlat.octave = 3
        chord8 = Chord([MiddleC, HighEFlat, LowGFlat])
        
        assert chord8.isDiminishedTriad() == True
        assert chord7.isDiminishedTriad() == False
        
        MiddleBFlat = note.Note()
        MiddleBFlat.name = 'B-'
        MiddleBFlat.octave = 4
        
        chord9 = Chord([MiddleC, MiddleE, LowG, MiddleBFlat])
        
        assert chord9.isDominantSeventh() == True
        assert chord5.isDominantSeventh() == False
        
        MiddleBDoubleFlat = note.Note()
        MiddleBDoubleFlat.name = 'B--'
        MiddleBDoubleFlat.octave = 4
        
        chord10 = Chord([MiddleC, HighEFlat, LowGFlat, MiddleBDoubleFlat])
    #    chord10.root(MiddleC)
        
        assert chord10.isDiminishedSeventh() == True
        assert chord9.isDiminishedSeventh() == False
        
        chord11 = Chord([MiddleC])
        
        assert chord11.isTriad() == False
        assert chord11.isSeventh() == False
        
        MiddleCSharp = note.Note()
        MiddleCSharp.name = 'C#'
        MiddleCSharp.octave = 4
        
        chord12 = Chord([MiddleC, MiddleCSharp, LowG, MiddleE])
        chord12.root(MiddleC)
        
        assert chord12.isTriad() == False
        assert chord12.isDiminishedTriad() == False
        
        chord13 = Chord([MiddleC, MiddleE, LowG, LowGFlat])
        
        assert chord13.getChordStep(5) is not False
        assert chord13.hasRepeatedChordStep(5) == True
        assert chord13.hasAnyRepeatedDiatonicNote() == True
        assert chord13.getChordStep(2) == False
        assert chord13.containsTriad() == True
        assert chord13.isTriad() == False
        
        LowGSharp = note.Note()
        LowGSharp.name = 'G#'
        LowGSharp.octave = 3
        
        chord14 = Chord([MiddleC, MiddleE, LowGSharp])
        
        assert chord14.isAugmentedTriad() == True
        assert chord6.isAugmentedTriad() == False
        
        chord15 = Chord([MiddleC, HighEFlat, LowGFlat, MiddleBFlat])
        
        assert chord15.isHalfDiminishedSeventh() == True
        assert chord12.isHalfDiminishedSeventh() == False        
        assert chord15.bass().name == 'G-'
        assert chord15.inversion() == 2
        assert chord15.inversionName() == 43
        
        LowC = note.Note()
        LowC.name = 'C'
        LowC.octave = 3
        
        chord16 = Chord([LowC, MiddleC, HighEFlat])
        
        assert chord16.inversion() == 0
        
        chord17 = Chord([LowC, MiddleC, HighEFlat])
        chord17.root(MiddleC)
        
        assert chord17.inversion() == 0
        
        LowE = note.Note()
        LowE.name = 'E'
        LowE.octave = 3
        
        chord18 = Chord([MiddleC, LowE, LowGFlat])
        
        assert chord18.inversion() == 1
        self.assertEqual(chord18.inversionName(), 6)
        
        LowBFlat = note.Note()
        LowBFlat.name = 'B-'
        LowBFlat.octave = 3
        
        chord19 = Chord([MiddleC, HighEFlat, LowBFlat])
        chord20 = Chord([LowC, LowBFlat])
        chord20.root(LowBFlat)
        
        assert chord19.inversion() == 3
        assert chord19.inversionName() == 42
        '''assert chord20.inversion() == 4 intentionally raises error'''
        
        chord21 = Chord([MiddleC, HighEFlat, LowGFlat])
        assert chord21.root().name == 'C'
        
        MiddleF = note.Note()
        MiddleF.name = 'F'
        MiddleF.octave = 4
        
        LowA = note.Note()
        LowA.name = 'A'
        LowA.octave = 3    
        
        chord22 = Chord([MiddleC, MiddleF, LowA])
        assert chord22.root().name == 'F'
        self.assertEqual(chord22.inversionName(), 6)
        
        chord23 = Chord([MiddleC, MiddleF, LowA, HighEFlat])
        assert chord23.root().name == 'F'
        
        HighC = note.Note()
        HighC.name = 'C'
        HighC.octave = 4
        
        HighE = note.Note()
        HighE.name = 'E'
        HighE.octave = 5
        
        chord24 = Chord([MiddleC])
        assert chord24.root().name == 'C'
        
        chord25 = Chord([MiddleC, HighE])
        assert chord25.root().name == 'C'
        
        MiddleG = note.Note()
        MiddleG.name = 'G'
        MiddleG.octave = 4
        
        chord26 = Chord([MiddleC, MiddleE, MiddleG])
        assert chord26.root().name == 'C'
        
        chord27 = Chord([MiddleC, MiddleE, MiddleG, MiddleBFlat])
        assert chord27.root().name == 'C'
        
        chord28 = Chord([LowE, LowBFlat, MiddleG, HighC])
        assert chord28.root().name == 'C'
        
        HighD = note.Note()
        HighD.name = 'D'
        HighD.octave = 5
        
        HighF = note.Note()
        HighF.name = 'F'
        HighF.octave = 5
        
        HighAFlat = note.Note()
        HighAFlat.name = 'A-'
        HighAFlat.octave = 5
        
        chord29 = Chord([MiddleC, MiddleE, MiddleG, MiddleBFlat, HighD])
        assert chord29.root().name == 'C'
        
        chord30 = Chord([MiddleC, MiddleE, MiddleG, MiddleBFlat, HighD, HighF])
        assert chord30.root().name == 'C'
         
        
        '''Should raise error'''
        chord31 = Chord([MiddleC, MiddleE, MiddleG, MiddleBFlat, HighD, HighF, HighAFlat])
        
        self.assertRaises(ChordException, chord31.root)
        
        chord32 = Chord([MiddleC, MiddleE, MiddleG, MiddleB])
        assert chord32.bass().name == 'C'
        assert chord32.root().name == 'C'
        assert chord32.inversionName() == 7
        
        MiddleFDbleFlat = note.Note()
        MiddleFDbleFlat.name = 'F--'
        
        MiddleA = note.Note()
        MiddleA.name = 'A'
        
        MiddleASharp = note.Note()
        MiddleASharp.name = 'A#'
        
        MiddleFSharp = note.Note()
        MiddleFSharp.name = 'F#'
        
        chord33 = Chord([MiddleC, MiddleE, MiddleG, MiddleFDbleFlat, MiddleASharp, MiddleBDoubleFlat, MiddleFSharp])
        chord33.root(MiddleC)
        
        assert chord33.isHalfDiminishedSeventh() == False
        assert chord33.isDiminishedSeventh() == False
        assert chord33.isFalseDiminishedSeventh() == False
        
        chord34 = Chord([MiddleC, MiddleFDbleFlat, MiddleFSharp, MiddleA])
        assert chord34.isFalseDiminishedSeventh() == True
                
        scrambledChord1 = Chord([HighAFlat, HighF, MiddleC, MiddleASharp, MiddleBDoubleFlat])
        unscrambledChord1 = scrambledChord1.sortAscending()
        assert unscrambledChord1.pitches[0].name == "C"
        assert unscrambledChord1.pitches[1].name == "A#"
        assert unscrambledChord1.pitches[2].name == "B--"
        assert unscrambledChord1.pitches[3].name == "F"
        assert unscrambledChord1.pitches[4].name == "A-"
    
        unscrambledChord2 = scrambledChord1.sortChromaticAscending()
        assert unscrambledChord2.pitches[0].name == "C"
        assert unscrambledChord2.pitches[1].name == "B--"
        assert unscrambledChord2.pitches[2].name == "A#"
        assert unscrambledChord2.pitches[3].name == "F"
        assert unscrambledChord2.pitches[4].name == "A-"
    
        unscrambledChord3 = scrambledChord1.sortFrequencyAscending()
        assert unscrambledChord3.pitches[0].name == "C"
        assert unscrambledChord3.pitches[1].name == "B--"
        assert unscrambledChord3.pitches[2].name == "A#"
        assert unscrambledChord3.pitches[3].name == "F"
        assert unscrambledChord3.pitches[4].name == "A-"
    
        
    #    for thisPitch in unscrambledChord2.pitches:
    #        print thisPitch.name + str(thisPitch.octave) + '  ' + str(thisPitch.diatonicNoteNum()) + "  " + str(thisPitch.midiNote())
    
    def testDurations(self):
        
        Cq = note.Note('C4')
        Cq.duration.type = "quarter"
        
        chord35 = Chord([Cq])
        self.assertEquals(chord35.duration.type, "quarter")

        Dh = note.Note('D4')
        Dh.duration.type = "half"
        
        chord36 = Chord([Cq, Dh])
        self.assertEquals(chord36.duration.type, "quarter")
        
        chord37 = Chord([Dh, Cq])
        self.assertEquals(chord37.duration.type, "half")
        
        chord38 = Chord([Cq, Dh], type="whole")
        self.assertEquals(chord38.duration.type, "whole")
        
    def testShortCuts(self):
        chord1 = Chord(["C#4","E4","G4"])
        self.assertTrue(chord1.isDiminishedTriad())
        self.assertFalse(chord1.isMajorTriad())
        # duration shold store a Duration object
        #assert chord1.duration is None

    def testLily(self):
        chord1 = Chord(["C#4","E4","G5"])
        self.assertEqual("<cis' e' g''>4", chord1.lily.value)

    def testClosedPosition(self):
        chord1 = Chord(["C#4", "G5", "E6"])
        chord2 = chord1.closedPosition()
        self.assertEqual("<cis' e' g'>4", chord2.lily.value)

    def testPostTonalChordsA(self):
        c1 = Chord([0,1,3,6,8,9,12])
        self.assertEqual(c1.pitchClasses, [0, 1, 3, 6, 8, 9, 0])
        self.assertEqual(c1.multisetCardinality, 7)
        self.assertEqual(c1.orderedPitchClasses, [0, 1, 3, 6, 8, 9])
        self.assertEqual(c1.pitchClassCardinality, 6)
        self.assertEqual(c1.forteClass, '6-29')
        self.assertEqual(c1.normalForm, [0, 1, 3, 6, 8, 9])
        self.assertEqual(c1.forteClassNumber, 29)
        self.assertEqual(c1.primeForm, [0, 1, 3, 6, 8, 9])
        self.assertEqual(c1.intervalVector, [2, 2, 4, 2, 3, 2])
        self.assertEqual(c1.isPrimeFormInversion, False)
        self.assertEqual(c1.hasZRelation, True)
        self.assertEqual(c1.areZRelations(Chord([0,1,4,6,7,9])), True)
        self.assertEqual(c1.commonName, 'combinatorial RI (RI9)')

    def testPostTonalChordsB(self):
        c1 = Chord([1, 4, 7, 10])
        self.assertEqual(c1.commonName, 'diminished seventh chord')
        self.assertEqual(c1.pitchedCommonName, 'C#-diminished seventh chord')

    def testScaleDegreesA(self):
        chord1 = Chord(["C#5", "E#5", "G#5"])
        st1 = music21.stream.Stream()
        st1.append(music21.key.Key('c#'))   # c-sharp minor
        st1.append(chord1)
        self.assertEqual(repr(chord1.scaleDegrees), "[(1, None), (3, <accidental sharp>), (5, None)]")
          
        st2 = music21.stream.Stream()
        st2.append(music21.key.Key('c'))    # c minor
        st2.append(chord1)          # same pitches as before gives different scaleDegrees
        sd2 = chord1.scaleDegrees
        self.assertEqual(repr(sd2), "[(1, <accidental sharp>), (3, <accidental double-sharp>), (5, <accidental sharp>)]")
        
        
        st3 = music21.stream.Stream()
        st3.append(music21.key.Key('C'))    # C major
        chord2 = Chord(["C4","C#4","D4","E-4","E4","F4"])  # 1st 1/2 of chromatic
        st3.append(chord2)
        sd3 = chord2.scaleDegrees
        self.assertEqual(repr(sd3), '[(1, None), (1, <accidental sharp>), (2, None), (3, <accidental flat>), (3, None), (4, None)]')
        

    def testScaleDegreesB(self):
        from music21 import chord, stream, key
        # trying to isolate problematic context searches
        chord1 = chord.Chord(["C#5", "E#5", "G#5"])
        st1 = stream.Stream()
        st1.append(key.Key('c#'))   # c-sharp minor
        st1.append(chord1)
        self.assertEqual(chord1.activeSite, st1)
        self.assertEqual(str(chord1.scaleDegrees), 
        "[(1, None), (3, <accidental sharp>), (5, None)]")
        
        st2 = stream.Stream()
        st2.append(key.Key('c'))    # c minor
        st2.append(chord1)          # same pitches as before gives different scaleDegrees

        self.assertEqual(chord1.activeSite, st2)
        self.assertEqual(str(chord1.scaleDegrees), 
        "[(1, <accidental sharp>), (3, <accidental double-sharp>), (5, <accidental sharp>)]")


    def testTiesA(self):
        # test creating independent ties for each Pitch
        from music21 import chord, stream, pitch, tie

        c1 = chord.Chord(['c', 'd', 'b'])
        # as this is a subclass of Note, we have a .tie attribute already
        # here, it is managed by a property
        self.assertEqual(c1.tie, None)
        # directly manipulate pitches
        t1 = tie.Tie()
        t2 = tie.Tie()
        c1._pitches[0]['tie'] = t1
        # now, the tie attribute returns the tie found on the first pitch
        self.assertEqual(c1.tie, t1)
        # try to set all ties for all pitches using the .tie attribute
        c1.tie = t2
        # must do id comparisons, as == comparisons are based on attributes
        self.assertEqual(id(c1.tie), id(t2))
        self.assertEqual(id(c1._pitches[0]['tie']), id(t2))
        self.assertEqual(id(c1._pitches[1]['tie']), id(t2))
        self.assertEqual(id(c1._pitches[2]['tie']), id(t2))

        # set ties for specific pitches
        t3 = tie.Tie()
        t4 = tie.Tie()
        t5 = tie.Tie()
        
        c1.setTie(t3, c1.pitches[0])
        c1.setTie(t4, c1.pitches[1])
        c1.setTie(t5, c1.pitches[2])

        self.assertEqual(id(c1.getTie(c1.pitches[0])), id(t3))
        self.assertEqual(id(c1.getTie(c1.pitches[1])), id(t4))
        self.assertEqual(id(c1.getTie(c1.pitches[2])), id(t5))

        from music21.musicxml import testPrimitive
        from music21 import converter
        s = converter.parse(testPrimitive.chordIndependentTies)
        chords = s.flat.getElementsByClass('Chord')
        # the middle pitch should have a tie
        self.assertEqual(chords[0].getTie(pitch.Pitch('a4')).type, 'start')
        self.assertEqual(chords[0].getTie(pitch.Pitch('c5')), None)
        self.assertEqual(chords[0].getTie(pitch.Pitch('f4')), None)

        self.assertEqual(chords[1].getTie(pitch.Pitch('a4')).type, 'continue')
        self.assertEqual(chords[1].getTie(pitch.Pitch('g5')), None)

        self.assertEqual(chords[2].getTie(pitch.Pitch('a4')).type, 'continue')
        self.assertEqual(chords[2].getTie(pitch.Pitch('f4')).type, 'start')
        self.assertEqual(chords[2].getTie(pitch.Pitch('c5')), None)

        #s.show()
        out = s.musicxml
        out = out.replace(' ', '')
        out = out.replace('\n', '')
        #print out
        self.assertEqual(out.find("""<pitch><step>A</step><octave>4</octave></pitch><duration>15120</duration><tietype="start"/><type>quarter</type><dot/><notations><tiedtype="start"/></notations>"""), 1149)

        
    def testTiesB(self):
        from music21 import chord, stream, tie, scale
        sc = scale.WholeToneScale()
        s = stream.Stream()
        for i in range(7):
            tiePos = range(i+1)
            c = sc.getChord('c4', 'c5', quarterLength=1)
            for pos in tiePos:
                c.setTie(tie.Tie('start'), c.pitches[pos])
            s.append(c)
        #s.show()



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Chord]

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        te = TestExternal()
        # arg[1] is test to launch
        if hasattr(t, sys.argv[1]): getattr(t, sys.argv[1])()

#------------------------------------------------------------------------------
# eof

