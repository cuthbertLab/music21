# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         chord.py
# Purpose:      Chord representation and utilities
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
This module defines the Chord object, a sub-class of :class:`~music21.note.GeneralNote`
as well as other methods, functions, and objects related to chords.
'''
__all__ = ['tables']
from music21.chord import tables as chordTables


import copy
import unittest



from music21 import beam
from music21 import common
from music21 import derivation
from music21 import duration
from music21 import exceptions21
from music21 import interval
from music21 import note
from music21 import pitch
from music21 import tie
from music21 import volume

from music21 import environment
from music21.ext import six

_MOD = "chord.py"
environLocal = environment.Environment(_MOD)

#-------------------------------------------------------------------------------


class ChordException(exceptions21.Music21Exception):
    pass


#-------------------------------------------------------------------------------


class Chord(note.NotRest):
    '''Class for dealing with chords

    A Chord functions like a Note object but has multiple pitches.

    Create chords by passing a string of pitch names

    >>> dmaj = chord.Chord(["D","F#","A"])
    >>> dmaj
    <music21.chord.Chord D F# A>

    Pitch names can also include octaves:

    >>> dmaj = chord.Chord(["D3","F#4","A5"])
    >>> dmaj
    <music21.chord.Chord D3 F#4 A5>

    String attribute is also okay...

    >>> myChord = chord.Chord('A4 C#5 E5')
    >>> myChord
    <music21.chord.Chord A4 C#5 E5>


    Or you can combine already created Notes or Pitches:

    >>> Cnote = note.Note('C')
    >>> Enote = note.Note('E')
    >>> Gnote = note.Note('G')

    And then create a chord with note objects:

    >>> cmaj = chord.Chord([Cnote, Enote, Gnote])
    >>> cmaj # default octave of 4 is used for these notes, since octave was not specified
    <music21.chord.Chord C E G>

    Chord has the ability to determine the root of a chord, as well as the bass note of a chord.
    In addition, Chord is capable of determining what type of chord a particular chord is, whether
    it is a triad or a seventh, major or minor, etc, as well as what inversion the chord is in.


    A chord can also be created from pitch class numbers:

    >>> c = chord.Chord([0, 2, 3, 5])
    >>> c.pitches
    (<music21.pitch.Pitch C>, <music21.pitch.Pitch D>, <music21.pitch.Pitch E->, <music21.pitch.Pitch F>)

    Or from MIDI numbers:

    >>> c = chord.Chord([72, 76, 79])
    >>> c.pitches
    (<music21.pitch.Pitch C5>, <music21.pitch.Pitch E5>, <music21.pitch.Pitch G5>)


    Duration as keyword works

    >>> d = duration.Duration(2.0)
    >>> myChord = chord.Chord('A4 C#5 E5', duration=d)
    >>> myChord
    <music21.chord.Chord A4 C#5 E5>
    >>> myChord.duration
    <music21.duration.Duration 2.0>
    >>> myChord.duration is d
    True


    OMIT_FROM_DOCS

    Test that durations are being created efficiently:

    >>> dmaj.duration
    <music21.duration.Duration 1.0>

    >>> cmaj.pitches[0] is Cnote.pitch
    True

    >>> Cnote.duration
    <music21.duration.Duration 1.0>

    >>> cmaj.duration
    <music21.duration.Duration 1.0>

    >>> cmaj.duration is Cnote.duration
    True

    Create a chord from two chords (or a chord + notes):
    
    >>> eflatSixFive = chord.Chord('G3 B-3 D-4 E-4')
    >>> fflat = chord.Chord('F-2 A-2 C-3 F-3')
    >>> riteOfSpring = chord.Chord([fflat, eflatSixFive])
    >>> riteOfSpring
    <music21.chord.Chord F-2 A-2 C-3 F-3 G3 B-3 D-4 E-4>
    
    Incorrect entries raise a ChordException:
    
    >>> chord.Chord([base])
    Traceback (most recent call last):
    ChordException: Could not process input argument <module 'music21.base' from '...base...'>

    '''
    ### CLASS VARIABLES ###

    _bass = None
    _root = None
    _inversion = None
    isChord = True
    isNote = False
    isRest = False

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['pitches']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'isChord': 'Boolean read-only value describing if this GeneralNote object is a Chord. Is True',
    'isNote': 'Boolean read-only value describing if this GeneralNote object is a Note. Is False',
    'isRest': r'''Boolean read-only value describing if this GeneralNote object is a Rest. Is False
        >>> c = chord.Chord()
        >>> c.isRest
        False    
    ''',
    'beams': 'A :class:`music21.beam.Beams` object.',
    }
    # update inherited _DOC_ATTR dictionary
    _TEMPDOC = note.NotRest._DOC_ATTR
    _TEMPDOC.update(_DOC_ATTR)
    _DOC_ATTR = _TEMPDOC

    ### INITIALIZER ###

    def __init__(self, notes=None, **keywords):
        if notes is None:
            notes = []
        if common.isStr(notes) and " " in notes:
            notes = notes.split()
        # the list of pitch objects is managed by a property; this permits
        # only updating the _chordTablesAddress when pitches has changed

        # duration looks at _notes to get first duration of a pitch
        # if no other pitches are defined

        # a list of dictionaries; each storing pitch, tie, and volume objects
        # one for each component of the chord
        self._notes = []
        self._chordTablesAddress = None
        self._chordTablesAddressNeedsUpdating = True # only update when needed
        # here, pitch and duration data is extracted from notes
        # if provided

        note.NotRest.__init__(self, **keywords)

        # inherit Duration object from GeneralNote
        # keep it here in case we have no notes
        #self.duration = None  # inefficient, since note.Note.__init__ set it
        #del self.pitch
        quickDuration = False
        if 'duration' not in keywords:
            keywords['duration'] = self.duration
            quickDuration = True

        for n in notes:
            if isinstance(n, pitch.Pitch):
                # assign pitch to a new Note
                if 'duration' in keywords:
                    newNote = note.Note(n, duration=keywords['duration'])
                else:
                    newNote = note.Note(n)
                self._notes.append(newNote)
                #self._notes.append({'pitch':n})
            elif isinstance(n, note.Note):
                self._notes.append(n)
                if quickDuration is True:
                    self.duration = n.duration
                    #print "got it! %s" % n
                    del keywords['duration']
                    quickDuration = False
                # no need for deepcopy...
                #self._notes.append(copy.deepcopy(n))

                # TODO: need to provide self as argument, but currently
                # cause problem on copy
#                 vNew = volume.Volume()
#                 vNew.mergeAttributes(n.volume)
#                 self._notes.append({'pitch':n.pitch,
#                                       'notehead':n.notehead,
#                                       'stem': n.stemDirection,
#                                      'volume': vNew, # volume
#                                     })
            elif isinstance(n, Chord):
                for newNote in n._notes:
                    self._notes.append(copy.deepcopy(newNote))
                if quickDuration is True:
                    self.duration = n.duration
                    del keywords['duration']
                    quickDuration = False
                # TODO: transfer all attributes from _notes of other
#                 for p in n.pitches:
#                     # this might better make a deepcopy of the pitch
#                     self._notes.append({'pitch':p})
            elif isinstance(n, six.string_types) or isinstance(n, int):
                if 'duration' in keywords:
                    self._notes.append(note.Note(n, duration=keywords['duration']))
                else:
                    self._notes.append(note.Note(n))
                #self._notes.append({'pitch':music21.pitch.Pitch(n)})
            else:
                raise ChordException("Could not process input argument %s" % n)

        if quickDuration is True:
            del keywords['duration']
            quickDuration = False

        if "duration" in keywords:
            self.duration = keywords['duration']
        elif "type" in keywords or \
            "quarterLength" in keywords: #dots dont cut it
            self.duration = duration.Duration(**keywords)

#        elif len(notes) > 0:
#            for thisNote in notes:
#                # get duration from first note
#                # but should other notes have the same duration?
#                if hasattr(thisNote, "duration") and thisNote.duration != None:
#                    self.duration = notes[0].duration
#                    break

        if "beams" in keywords:
            self.beams = keywords["beams"]
        else:
            self.beams = beam.Beams()


    ### SPECIAL METHODS ###
    def __deepcopy__(self, memo=None):
        '''As Chord objects have one or more Volume, objects, and Volume
        objects store weak refs to the to client object, need to specialize
        deepcopy handling depending on if the chord has its own volume object.
        '''
        #environLocal.printDebug(['calling NotRest.__deepcopy__', self])
        # as this inherits from NotRest, can use that __deepcopy__ as basis
        # that looks only to _volume to see if it is not None; with a
        # Chord, _volume will always be None
        new = note.NotRest.__deepcopy__(self, memo=memo)
        # after copying, if a Volume exists, it is linked to the old object
        # look at _volume so as not to create object if not already there
        for d in new._notes:
            # if .volume is called, a new Volume obj will be created
            if d._volume is not None:
                d.volume.client = new # update with new instance
        return new


    def __getitem__(self, key):
        '''
        Get item makes access pitch components for the Chord easier
        
        >>> c = chord.Chord('C#4 D-4')
        >>> c['0.step'] 
        'C'
        >>> c['3.accidental']
        Traceback (most recent call last):
        KeyError: 'cannot access component with string: 3.accidental'
        
        >>> c[5]
        Traceback (most recent call last):
        KeyError: 'cannot access component with: 5'
        '''

        if common.isStr(key) and key.count('.') == 1:
            first, last = key.split('.')
            try:
                component = self._notes[int(first)]
            except:
                raise KeyError('cannot access component with string: %s' % key)

            # get by name of attribute on Note
            if last == 'volume': # special handling to avoid setting client
                return component._getVolume(forceClient=self)
            else:
                return getattr(component, last)
        else:
            try:
                return self._notes[key] # must be a number
            except (KeyError, IndexError):
                raise KeyError('cannot access component with: %s' % key)

    def __iter__(self):
        return common.Iterator(self._notes)

    def __len__(self):
        '''
        Return the length of components in the chord.

        >>> c = chord.Chord(['c', 'e', 'g'])
        >>> len(c)
        3
        '''
        return len(self._notes)

    def __repr__(self):
        allPitches = []
        for thisPitch in self.pitches:
            allPitches.append(thisPitch.nameWithOctave)
        return "<music21.chord.Chord %s>" % ' '.join(allPitches)

    ### PUBLIC METHODS ###

    def seekChordTablesAddress(self):
        '''
        Utility method to return the address to the chord table.

        Table addresses are TN based three character codes:
        cardinaltiy, Forte index number, inversion

        Inversion is either 0 (for symmetrical) or -1/1

        NOTE: time consuming, and only should be run when necessary.

        >>> c1 = chord.Chord(['c3'])
        >>> c1.orderedPitchClasses
        [0]

        >>> c1.seekChordTablesAddress()
        (1, 1, 0)

        >>> c1 = chord.Chord(
        ...     ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'b']
        ...     )
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
        
        
        Zero-length chords raise a pitch exception:
        
        >>> c2 = chord.Chord()
        >>> c2.seekChordTablesAddress()
        Traceback (most recent call last):
        ChordException: cannot access chord tables address for Chord with 0 pitches
        '''
        pcSet = self.orderedPitchClasses
        if len(pcSet) == 0:
            raise ChordException(
                'cannot access chord tables address for Chord with %s pitches' % len(pcSet))

        #environLocal.printDebug(['calling seekChordTablesAddress:', pcSet])

        card = len(pcSet)
        if card == 1: # its a singleton: return
            return (1, 1, 0)
        elif card == 11: # its the only 11 note pcset
            return (11, 1, 0)
        elif card == 12: # its the aggregate
            return (12, 1, 0)
        # go through each rotation of pcSet
        candidates = []
        for rot in range(0, card):
            testSet = pcSet[rot:] + pcSet[0:rot]
            # transpose to lead with zero
            testSet = [(x - testSet[0]) % 12 for x in testSet]
            # create inversion; first take difference from 12 mod 12
            testSetInvert = [(12 - x) % 12 for x in testSet]
            testSetInvert.reverse() # reverse order (first steps now last)
            # transpose all steps (were last) to zero, mod 12
            testSetInvert = [(x + (12 - testSetInvert[0])) % 12
                            for x in testSetInvert]
            candidates.append([testSet, testSetInvert])

        # compare sets to those in table
        match = False
        for indexCandidate in range(len(chordTables.FORTE[card])):
            dataLine = chordTables.FORTE[card][indexCandidate]
            if dataLine == None: 
                continue # spacer lines
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

    ### PRIVATE METHODS ###

    def _formatVectorString(self, vectorList):
        '''
        Return a string representation of a vector or set

        >>> c1 = chord.Chord(["D4", "A4", "F#5", "D6"])
        >>> c1._formatVectorString([3,4,5])
        '<345>'

        >>> c1._formatVectorString([10,11,3,5])
        '<AB35>'

        '''
        msg = ['<']
        for e in vectorList: # should be numbers
            eStr = pitch._convertPitchClassToStr(e)
            msg.append(eStr)
        msg.append('>')
        return ''.join(msg)

    def _findBass(self):
        '''
        Returns the lowest note in the chord.

        The only time findBass should be called is by bass() when it is
        figuring out what the bass note of the chord is.

        Generally call bass() instead:

        >>> cmaj = chord.Chord(['C4', 'E3', 'G4'])
        >>> cmaj._findBass() # returns E3
        <music21.pitch.Pitch E3>

        '''
        lowest = None
        for thisPitch in self.pitches:
            if lowest is None:
                lowest = thisPitch
            else:
                lowest = interval.getWrittenLowerNote(lowest, thisPitch)
        return lowest

    def _removePitchByRedundantAttribute(self, attribute, inPlace):
        '''
        Common method for stripping pitches based on redundancy of one pitch
        attribute. The `attribute` is provided by a string.
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        uniquePitches = []
        deleteComponents = []
        for comp in returnObj._notes:
            if getattr(comp.pitch, attribute) not in uniquePitches:
                uniquePitches.append(getattr(comp.pitch, attribute))
            else:
                deleteComponents.append(comp)

        #environLocal.printDebug(['unique, delete', self, unique, delete])
        altered = returnObj._notes
        for p in deleteComponents:
            altered.remove(p)

        returnObj._notes = altered
        if len(deleteComponents) > 0:
            returnObj._chordTablesAddressNeedsUpdating = True
            returnObj._bass = None
            returnObj._root = None
        if not inPlace:
            return returnObj

    def _updateChordTablesAddress(self):
        if self._chordTablesAddressNeedsUpdating:
            self._chordTablesAddress = self.seekChordTablesAddress()
        self._chordTablesAddressNeedsUpdating = False

    ### PUBLIC METHODS ###

    def annotateIntervals(self, inPlace=True, stripSpecifiers=True, sortPitches=True, returnList=False):
        '''
        Add lyrics to the chord that show the distance of each note from
        the bass.  If returnList is True, a list of the intervals is returned instead.  
        
        By default we show only the generic interval:

        >>> c1 = chord.Chord(['C2','E2','G2','C3'])
        >>> c2 = c1.annotateIntervals(inPlace = False)
        >>> c2.lyrics
        [<music21.note.Lyric number=1 syllabic=single text="8">, <music21.note.Lyric number=2 syllabic=single text="5">, <music21.note.Lyric number=3 syllabic=single text="3">]

        >>> [l.text for l in c2.lyrics]
        ['8', '5', '3']

        The `stripSpecifiers` parameter can be used to show only the intervals size (3, 5, etc)
        or the complete interval specification (m3, P5, etc.)

        >>> c3 = c1.annotateIntervals(inPlace = False, stripSpecifiers = False)
        >>> c3.lyrics
        [<music21.note.Lyric number=1 syllabic=single text="P8">, <music21.note.Lyric number=2 syllabic=single text="P5">, <music21.note.Lyric number=3 syllabic=single text="M3">]

        >>> [l.text for l in c3.lyrics]
        ['P8', 'P5', 'M3']

        This chord was giving us problems:

        >>> c4 = chord.Chord(['G4', 'E4', 'B3', 'E3'])
        >>> c4.annotateIntervals(stripSpecifiers = False)
        >>> [l.text for l in c4.lyrics]
        ['m3', 'P8', 'P5']
        >>> c4.annotateIntervals(stripSpecifiers = False, returnList = True)
        ['m3', 'P8', 'P5']

        If sortPitches is false it still gives problems...

        >>> c4 = chord.Chord(['G4', 'E4', 'B3', 'E3'])
        >>> c4.annotateIntervals(stripSpecifiers = False, sortPitches = False)
        >>> [l.text for l in c4.lyrics]
        ['m3', 'm6', 'm3']

        >>> c = chord.Chord(['c4', 'd-4', 'g4'])
        >>> c.annotateIntervals()
        >>> [l.text for l in c.lyrics]
        ['5', '2']

        >>> c = chord.Chord(['c4', 'd-4', 'g4'])
        >>> c.annotateIntervals(stripSpecifiers=False)
        >>> [l.text for l in c.lyrics]
        ['P5', 'm2']

        >>> c = chord.Chord(['c4', 'd---4', 'g4'])
        >>> c.annotateIntervals(stripSpecifiers=False)
        >>> [l.text for l in c.lyrics]
        ['P5', 'dd2']

        >>> c = chord.Chord(['c4', 'g5', 'e6'])
        >>> c.annotateIntervals()
        >>> [l.text for l in c.lyrics]
        ['5', '3']


        ## TODO: -- decide, should inPlace be False like others?
        '''
        # make a copy of self for reducing pitches, but attach to self
        c = copy.deepcopy(self)
        # this could be an option
        c.removeRedundantPitches(inPlace=True)
        
        if sortPitches:
            c = c.sortAscending()
        #environLocal.printDebug(['annotateIntervals()', c.pitches])
        lyricsList = []
        
        for j in range(len(c.pitches) - 1, 0, -1): # only go to one; zero never used
            p = c.pitches[j]
            i = interval.Interval(c.pitches[0], p)
            if stripSpecifiers is False:
                notation = i.semiSimpleName
            else:
                notation = str(i.diatonic.generic.semiSimpleUndirected)
            lyricsList.append(notation)

        if stripSpecifiers is True and sortPitches is True:
            lyricsList.sort(reverse=True)

        if returnList is True:
            return lyricsList

        for notation in lyricsList:
            if inPlace is True:
                self.addLyric(notation)
            else:
                c.addLyric(notation)
        
        if inPlace is False:
            return c

    def areZRelations(self, other):
        '''Check of chord other is also a z relations

        >>> c1 = chord.Chord(["C", "c#", "e", "f#"])
        >>> c2 = chord.Chord(["C", "c#", "e-", "g"])
        >>> c3 = chord.Chord(["C", "c#", "f#", "g"])
        >>> c1.areZRelations(c2)
        True

        >>> c1.areZRelations(c3)
        False

        If there is no Z-Relation for the first chord, obviously return false:
        
        >>> c4 = chord.Chord('C E G')
        >>> c4.areZRelations(c3)
        False
        '''
        self._updateChordTablesAddress()
        post = chordTables.addressToZAddress(self._chordTablesAddress)
        if post is None:
            return False
        zRelationAddress = chordTables.addressToZAddress(
            self._chordTablesAddress)
        if other.chordTablesAddress == zRelationAddress:
            return True
        return False

    def bass(self, newbass=None, find=True):
        '''
        Return the bass Pitch or set it to the given Pitch:

        >>> cmaj1stInv = chord.Chord(['C4', 'E3', 'G5'])
        >>> cmaj1stInv.bass()
        <music21.pitch.Pitch E3>

        The bass is usually defined to the lowest note in the chord,
        but we want to be able to override this.  You might want an implied
        bass for instance some people (following the music theorist
        Rameau) call a diminished seventh chord (vii7)
        a dominant chord with an omitted bass -- here we will specify the bass
        to be a note not in the chord:

        >>> vo9 = chord.Chord(['B3', 'D4', 'F4', 'A-4'])
        >>> vo9.bass()
        <music21.pitch.Pitch B3>

        >>> vo9.bass(pitch.Pitch('G3'))
        >>> vo9.bass()
        <music21.pitch.Pitch G3>

        By default this method uses an algorithm to find the bass among the
        chord's pitches, if no bass has been previously specified. If this is
        not intended, set find to False when calling this method, and 'None'
        will be returned if no bass is specified

        >>> c = chord.Chord(['E3','G3','B4'])
        >>> c.bass(find=False) == None
        True

        >>> d = harmony.ChordSymbol('CM')
        >>> d.bass()
        <music21.pitch.Pitch C3>

        >>> d = harmony.ChordSymbol('Cm/E-')
        >>> d.bass()
        <music21.pitch.Pitch E-3>

        OMIT_FROM_DOCS

        Test to make sure that cached basses still work by calling twice:

        >>> a = chord.Chord(['C4'])
        >>> a.bass()
        <music21.pitch.Pitch C4>

        '''
        if newbass:
            if common.isStr(newbass):
                newbass = newbass.replace('b', '-')
                self._bass = pitch.Pitch(newbass)
            else:
                self._bass = newbass
            self._inversion = None # reset inversion if root changes
        elif (self._bass is None) and (find):
            # TODO: stop caching basses
            self._bass = self._findBass()
            return self._bass
        else:
            return self._bass

    def canBeDominantV(self):
        '''
        Returns True if the chord is a Major Triad or a Dominant Seventh:

        >>> gSeven = chord.Chord(['g', 'b', 'd', 'f'])
        >>> gSeven.canBeDominantV()
        True

        >>> gDim = chord.Chord(['g', 'b-', 'd-'])
        >>> gDim.canBeDominantV()
        False
        '''
        if self.isMajorTriad() or self.isDominantSeventh():
            return True
        else:
            return False

    def canBeTonic(self):
        '''
        Returns True if the chord is a major or minor triad:

        >>> a = chord.Chord(['g', 'b', 'd', 'f'])
        >>> a.canBeTonic()
        False

        >>> a = chord.Chord(['g', 'b', 'd'])
        >>> a.canBeTonic()
        True

        '''
        if self.isMajorTriad() or self.isMinorTriad():
            return True
        else:
            return False

    def closedPosition(self, forceOctave=None, inPlace=False, leaveRedundantPitches=False):
        '''Returns a new Chord object with the same pitch classes,
        but now in closed position.

        If `forcedOctave` is provided, the bass of the chord will
        be shifted to that provided octave.

        If inPlace is True then the original chord is returned with new pitches.

        >>> chord1 = chord.Chord(["C#4", "G5", "E6"])
        >>> chord2 = chord1.closedPosition()
        >>> chord2
        <music21.chord.Chord C#4 E4 G4>

        Force octave changes the octave of the bass note (and all notes above it...)

        >>> c2 = chord.Chord(["C#4", "G5", "E6"])
        >>> c2.closedPosition(forceOctave = 2)
        <music21.chord.Chord C#2 E2 G2>

        >>> c3 = chord.Chord(["C#4", "G5", "E6"])
        >>> c3.closedPosition(forceOctave = 6)
        <music21.chord.Chord C#6 E6 G6>

        Redundant pitches are removed by default, but can be retained...

        >>> c4 = chord.Chord(["C#4", "C5", "F7", "F8"])
        >>> c5 = c4.closedPosition(4, inPlace = False)
        >>> c5
        <music21.chord.Chord C#4 F4 C5>

        >>> c6 = c4.closedPosition(4, inPlace = False, leaveRedundantPitches=True)
        >>> c6
        <music21.chord.Chord C#4 F4 F4 C5>

        Implicit octaves work fine...

        >>> c7 = chord.Chord(["A4", "B4", "A"])
        >>> c7.closedPosition(4, inPlace = True)
        >>> c7
        <music21.chord.Chord A4 B4>

        OMIT_FROM_DOCS
        Very specialized fears...

        Duplicate octaves were not working

        >>> c7b = chord.Chord(["A4", "B4", "A5"])
        >>> c7b.closedPosition(inPlace = True)
        >>> c7b
        <music21.chord.Chord A4 B4>

        but the bass must remain A4:

        >>> c7c = chord.Chord(["A4", "B4", "A5", "G##6"])
        >>> c7c.closedPosition(inPlace = True)
        >>> c7c
        <music21.chord.Chord A4 B4 G##5>

        >>> str(c7c.bass())
        'A4'

        complex chord for semiclosed-position testing...

        >>> c8 = chord.Chord(['C3','E5','C#6','E-7', 'G8','C9','E#9'])
        >>> c8.closedPosition(inPlace=True)
        >>> c8
        <music21.chord.Chord C3 C#3 E-3 E3 E#3 G3>

        Implicit octave + forceOctave
        
        >>> c9 = chord.Chord('C G E')
        >>> c9.closedPosition(forceOctave=6)
        <music21.chord.Chord C6 E6 G6>

        '''
        #environLocal.printDebug(['calling closedPosition()', inPlace])
        if inPlace:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)
            returnObj.derivation = derivation.Derivation(returnObj)
            returnObj.derivation.origin = self
            returnObj.derivation.method = 'closedPosition'
        #tempChordNotes = returnObj.pitches

        pBass = returnObj.bass() # returns a reference, not a copy
        if forceOctave is not None:
            pBassOctave = pBass.octave
            if pBassOctave is None:
                pBassOctave = pBass.implicitOctave
                
            if pBassOctave > forceOctave:
                dif = -1
            elif pBassOctave < forceOctave:
                dif = 1
            else: # equal
                dif = None
            if dif != None:
                while pBass.octave != forceOctave:
                    # shift octave of all pitches
                    for p in returnObj.pitches:
                        if p.octave is None:
                            p.octave = p.implicitOctave
                        p.octave += dif

        # can change these pitches in place
        for p in returnObj.pitches:
            # bring each pitch down octaves until pitch space is
            # within an octave
            if p.octave is None:
                p.octave = p.implicitOctave
            while p.ps >= pBass.ps + 12:
                p.octave -= 1
            # check for a bass of C4 and the note B#7 added to it, should be B#4 not B#3...
            if p.diatonicNoteNum < pBass.diatonicNoteNum:
                p.octave += 1

        if leaveRedundantPitches is not True:
            returnObj.removeRedundantPitches(inPlace=True) #here we can always be in place...

        # if not inPlace, creates a second new chord object!
        returnObj.sortAscending(inPlace=True)

        if inPlace == False:
            return returnObj

    def containsSeventh(self):
        '''
        Returns True if the chord contains at least one of each of Third, Fifth, and Seventh.
        raises an exception if the Root can't be determined



        >>> cchord = chord.Chord(['C', 'E', 'G', 'B'])
        >>> other = chord.Chord(['C', 'D', 'E', 'F', 'G', 'B'])
        >>> cchord.containsSeventh() # returns True
        True
        >>> other.containsSeventh() # returns True
        True
        
        Empty chord returns False
        
        >>> chord.Chord().containsSeventh()
        False
        '''
        try:
            third = self.third
            fifth = self.fifth
            seventh = self.seventh
        except ChordException:
            return False

        if third is None or fifth is None or seventh is None:
            return False
        else:
            return True

    def containsTriad(self):
        '''
        Returns True or False if there is no triad above the root.
        "Contains vs. Is": A dominant-seventh chord contains a triad.

        >>> cchord = chord.Chord(['C', 'E', 'G'])
        >>> other = chord.Chord(['C', 'D', 'E', 'F', 'G'])
        >>> cchord.containsTriad()
        True

        >>> other.containsTriad() 
        True

        >>> scale = chord.Chord(['C', 'D-', 'E', 'F#', 'G', 'A#', 'B'])
        >>> scale.containsTriad() 
        True

        >>> c = chord.Chord('C4 D4')
        >>> c.containsTriad()
        False

        >>> chord.Chord().containsTriad()
        False
        '''
        try:
            third = self.third
            fifth = self.fifth
            # the only reason it cannot find a third or a fifth is that there is a complete 7-note diatonic scale present. or no notes
        except ChordException:
            return False

        if third is None or fifth is None:
            return False
        else:
            return True

    def findRoot(self):
        '''
        Looks for the root usually by finding the note with the most 3rds above
        it.

        Generally use root() instead, since if a chord doesn't know its root,
        root() will run findRoot() automatically.

        Example:

        >>> cmaj = chord.Chord(['E', 'G', 'C'])
        >>> cmaj.findRoot()
        <music21.pitch.Pitch C>

        For some chords we make an exception.  For instance, this chord in
        B-flat minor:

        >>> aDim7no3rd = chord.Chord(['A3', 'E-4', 'G4'])

        Could be considered an type of E-flat 11 chord with a 3rd, but no 5th,
        7th, or 9th, in 5th inversion.  That doesn't make sense, so we should
        call it an A dim 7th chord
        with no 3rd.

        >>> aDim7no3rd.findRoot()
        <music21.pitch.Pitch A3>

        >>> aDim7no3rdInv = chord.Chord(['E-3', 'A4', 'G4'])
        >>> aDim7no3rdInv.findRoot()
        <music21.pitch.Pitch A4>

        The root of a 13th chord (which could be any chord in any inversion) is
        designed to be the bass:

        >>> chord.Chord("F3 A3 C4 E-4 G-4 B4 D5").findRoot()
        <music21.pitch.Pitch F3>

        >>> lotsOfNotes = chord.Chord(['E3','C4','G4','B-4','E5','G5'])
        >>> r = lotsOfNotes.findRoot()
        >>> r
        <music21.pitch.Pitch C4>

        >>> r is lotsOfNotes.pitches[1]
        True


        >>> chord.Chord().findRoot()
        Traceback (most recent call last):
        ChordException: no notes in chord <music21.chord.Chord >
        '''
        def rootnessFunction(rootThirdList):
            '''
            Returns a value for how likely this pitch is to be a root given the
            number of thirds and fifths above it.

            Takes a list of True's and Falses's where each value represents
            whether a note has a 3rd, 5th, 7th, 9th, 11th, and 13th above it
            and calculates a value based on that.  The highest score on
            rootnessFunction is the root.

            This formula might be tweaked if wrong notes are found.

            Rootness function might be divided by the inversion number
            in case that's a problem.
            '''
            score = 0
            for i, val in enumerate(rootThirdList):
                if val is True:
                    score += 1.0/(i+6)
            return score

        stepsFound = []
        nonDuplicatingPitches = []
        for p in self.pitches:
            if p.step in stepsFound:
                continue
            else:
                stepsFound.append(p.step)
                nonDuplicatingPitches.append(p)
        closedChord = Chord(nonDuplicatingPitches)
        chordBass = closedChord.bass()
        lenPitches = len(closedChord.pitches)
        rootThirdsList = []
        rootnessFunctionScores = []
        if len(closedChord.pitches) == 0:
            raise ChordException("no notes in chord %r" % self)
        elif len(closedChord.pitches) == 1:
            return self.pitches[0]
        indexOfPitchesWithPerfectlyStackedThirds = []
        for i,p in enumerate(closedChord.pitches):
            currentListOfThirds = []
            for chordStepTest in (3, 5, 7, 2, 4, 6):
                if closedChord.getChordStep(chordStepTest, p):
                    currentListOfThirds.append(True)
                else:
                    currentListOfThirds.append(False)
            hasFalse = False
            for j in range(lenPitches - 1):
                if currentListOfThirds[j] is False:
                    hasFalse = True
            if hasFalse is False:
                indexOfPitchesWithPerfectlyStackedThirds.append(i)
            rootThirdsList.append(currentListOfThirds)
            rootnessScore = rootnessFunction(currentListOfThirds)
            #if p is not chordBass: # doesn't work
            #    rootnessScore *= 0.8  # penalize non-bass notes for stacked chords...
            rootnessFunctionScores.append(rootnessScore)
        # if one pitch has perfectlyStackedThirds, return it always:
        if len(indexOfPitchesWithPerfectlyStackedThirds) == 1:
            return closedChord.pitches[indexOfPitchesWithPerfectlyStackedThirds[0]]
        elif len(indexOfPitchesWithPerfectlyStackedThirds) == len(closedChord.pitches):
            # they're all equally good. return the bass note.  Is true for 13th chords...
            return chordBass
        # no notes (or more than one...) have perfectlyStackedThirds above them.  Return
        # the highest scoring note...
        mostRootyIndex = rootnessFunctionScores.index(max(rootnessFunctionScores))
        return closedChord.pitches[mostRootyIndex]
        

    def geometricNormalForm(self):
        '''
        Geometric Normal Form, as first defined by Dmitri Tymoczko, orders pitch classes
        such that the spacing is prioritized with the smallest spacing between the first and
        second pitch class first, then the smallest spacing between second and third pitch class,
        and so on. This form has unique properties that make it useful.

        `geometricNormalForm` returns a list of pitch class integers in
        geometric normal form.

        Example 1: A major triad has geometricNormalForm of 038 not 047.

        >>> c1 = chord.Chord("E4 C5 G6 C7")
        >>> pcList = c1.geometricNormalForm()
        >>> pcList
        [0, 3, 8]

        >>> c2 = chord.Chord(pcList)
        >>> c2.orderedPitchClassesString
        '<038>'

        Compare this to the usual normalForm:

        >>> c1.normalForm
        [0, 4, 7]

        '''
        # Order pitches
        pitchClassList = []
        for i in range (len(self.pitches)):
            pitchClassList.append(self.pitches[i].pitchClass)
        sortedPitchClassList = sorted(pitchClassList)
        # Remove duplicates
        uniquePitchClassList = [sortedPitchClassList[0]]
        for i in range (1, len(sortedPitchClassList)):
            if sortedPitchClassList[i] != sortedPitchClassList[i-1]:
                uniquePitchClassList.append(sortedPitchClassList[i])
        intervalList = []
        for i in range (1, len(uniquePitchClassList)):
            l = (uniquePitchClassList[i] - uniquePitchClassList[i-1])%12
            intervalList.append(l)
        intervalList.append((uniquePitchClassList[0] - uniquePitchClassList[-1])%12)
        # make list of rotations
        rotationList = []
        for i in range (0, len(intervalList)):
            b = intervalList.pop(0)
            intervalList.append(b)
            intervalTuple = tuple(intervalList)
            rotationList.append(intervalTuple)
        # Sort list of rotations.
        # First entry will be the geometric normal form arranged intervals
        newRotationList = sorted(rotationList)
        # Take that first entry and assign it as the PCIs that we will want for our chord
        geomNormChord = newRotationList[0]
        # Create final form of Geometric Normal Chord by starting at pc 0 and
        # assigning the notes based on the intervals we just discovered.
        geomNormChordPitches = []
        intervalSum = 0
        for i in range (0, len(geomNormChord)):
            geomNormChordPitches.append(intervalSum)
            intervalSum += geomNormChord[i]
        return geomNormChordPitches

    def getChordStep(self, chordStep, testRoot=None):
        '''
        Returns the (first) pitch at the provided scaleDegree (Thus, it's
        exactly like semitonesFromChordStep, except it instead of the number of
        semitones.)

        Returns None if none can be found.

        >>> cmaj = chord.Chord(['C', 'E', 'G'])
        >>> cmaj.getChordStep(3) # will return the third of the chord
        <music21.pitch.Pitch E>

        >>> g = cmaj.getChordStep(5) # will return the fifth of the chord
        >>> g.name
        'G'

        >>> cmaj.getChordStep(6) is None
        True

        '''
        if testRoot is None:
            testRoot = self.root()
            if testRoot is None:
                raise ChordException("Cannot run getChordStep without a root") # can this be tested?
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(testRoot, thisPitch)
            if thisInterval.diatonic.generic.mod7 == chordStep:
                return thisPitch
        return None

    def getColor(self, pitchTarget):
        '''
        For a pitch in this Chord, return the color stored in self.editorial,
        or, if set for each component, return the color assigned to this
        component.
        
        First checks for "is" then "equals"
        
        >>> p = pitch.Pitch('C4')
        >>> n = note.Note(p)
        >>> n.color = 'red'
        >>> c = chord.Chord([n, 'E4'])
        >>> c.getColor(p)
        'red'
        >>> c.getColor('C4')
        'red'
        >>> c.getColor('E4') is None
        True
        
        The color of any pitch (even a non-existing one) is the color of the chord if
        the color of that pitch is not defined.
        
        >>> c.color = 'pink'
        >>> c.getColor('E4')
        'pink'
        >>> c.getColor('D#7')
        'pink'        
        '''
        if common.isStr(pitchTarget):
            pitchTarget = pitch.Pitch(pitchTarget)
        for n in self._notes:
            if n.pitch is pitchTarget:
                if n.color is not None:
                    return n.color
        for n in self._notes:
            if n.pitch == pitchTarget:
                if n.color is not None:
                    return n.color
        return self.color # may be None

    def getNotehead(self, p):
        '''Given a pitch in this Chord, return an associated notehead
        attribute, or return 'normal' if not defined for that Pitch.

        If the pitch is not found, None will be returned.

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> n2.notehead = 'diamond'
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.getNotehead(c1.pitches[1])
        'diamond'

        >>> c1.getNotehead(c1.pitches[0])
        'normal'

        >>> c1.getNotehead(pitch.Pitch('A#6')) is None
        True

        Will work if the two notes are equal in pitch

        >>> c1.getNotehead(note.Note('G4'))
        'diamond'
        '''
        if hasattr(p, 'pitch'):
            p = p.pitch
        
        for d in self._notes:
            if d.pitch is p:
                return d.notehead
        for d in self._notes:
            if d.pitch == p:
                return d.notehead
        return None

    def getNoteheadFill(self, p):
        '''Given a pitch in this Chord, return an associated noteheadFill
        attribute, or return None if not defined for that Pitch.

        If the pitch is not found, None will also be returned.

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> n2.noteheadFill = True
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.getNoteheadFill(c1.pitches[1])
        True

        >>> print(c1.getNoteheadFill(c1.pitches[0]))
        None

        >>> c1.getNotehead(pitch.Pitch('A#6')) is None
        True

        Will work if the two notes are equal in pitch

        >>> c1.getNoteheadFill(note.Note('G4'))
        True
        '''
        if hasattr(p, 'pitch'):
            p = p.pitch

        for d in self._notes:
            if d.pitch is p:
                return d.noteheadFill
        for d in self._notes:
            if d.pitch == p:
                return d.noteheadFill
        return None


    def getStemDirection(self, p):
        '''Given a pitch in this Chord, return an associated stem attribute, or
        return 'unspecified' if not defined for that Pitch.

        If the pitch is not found, None will be returned.

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> n2.stemDirection = 'double'
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.getStemDirection(c1.pitches[1])
        'double'

        >>> c1.getStemDirection(c1.pitches[0])
        'unspecified'

        Will work if the two pitches are equal in pitch

        >>> c1.getStemDirection(pitch.Pitch('G4'))
        'double'
        '''
        if hasattr(p, 'pitch'):
            p = p.pitch

        for d in self._notes:
            if d.pitch is p: # compare by obj id first
                return d.stemDirection
            
        for d in self._notes:
            if d.pitch == p:
                return d.stemDirection
        return None

    def getTie(self, p):
        '''
        Given a pitch in this Chord, return an associated Tie object, or return
        None if not defined for that Pitch.

        >>> c1 = chord.Chord(['d', 'e-', 'b-'])
        >>> t1 = tie.Tie('start')
        >>> c1.setTie(t1, c1.pitches[2]) # just to b-
        >>> c1.getTie(c1.pitches[2]) == t1
        True

        >>> c1.getTie(c1.pitches[0]) is None
        True

        All notes not in chord return None

        >>> c1.getTie(pitch.Pitch('F#2')) is None
        True

        '''
        for d in self._notes:
            if d.pitch is p:
                return d.tie
        for d in self._notes:
            if d.pitch == p:
                return d.tie
        return None

    def getVolume(self, p):
        '''
        For a given Pitch in this Chord, return the
        :class:`~music21.volume.Volume` object.
        
        Raises an exception if the pitch isn't in the chord (TODO: consider changing to be like notehead, etc.)
        
        >>> c = chord.Chord('C4 F4')
        >>> c[0].volume = 2
        >>> c.getVolume('C4')
        <music21.volume.Volume realized=0.02>
        
        >>> c.getVolume('F4') # default
        <music21.volume.Volume realized=0.71>

        >>> c.getVolume('G4')
        Traceback (most recent call last):
        ChordException: the given pitch is not in the Chord: G4
        '''
        # NOTE: pitch matching is potentially problematic if we have more than
        # one of the same pitch
        if common.isStr(p):
            p = pitch.Pitch(p)

        for d in self._notes:
            if d.pitch is p or d.pitch == p:
                # will create if not set; otherwise will set client to Note
                return d._getVolume(forceClient=self)
        raise ChordException('the given pitch is not in the Chord: %s' % p)

    def getZRelation(self):
        '''Return a Z relation if it exists, otherwise return None.

        >>> chord.fromIntervalVector((1,1,1,1,1,1))
        <music21.chord.Chord C C# E F#>

        >>> chord.fromIntervalVector((1,1,1,1,1,1)).getZRelation()
        <music21.chord.Chord C C# E- G>


        >>> chord.Chord('C E G').getZRelation() is None
        True
        '''
        if self.hasZRelation:
            self._updateChordTablesAddress()
            chordTablesAddress = tuple(self._chordTablesAddress)
            v = chordTables.addressToIntervalVector(chordTablesAddress)
            addresses = chordTables.intervalVectorToAddress(v)
            #environLocal.printDebug(['addresses', addresses, 'chordTablesAddress', chordTablesAddress])
            # addresses returned here are 2 elements lists
            addresses.remove(chordTablesAddress[:2])
            prime = chordTables.addressToNormalForm(addresses[0])
            return Chord(prime)
        return None
        # c2.getZRelation()  # returns a list in non-ET12 space...
        # <music21.chord.ForteSet at 0x234892>

    def hasAnyRepeatedDiatonicNote(self, testRoot=None):
        '''
        Returns True if for any diatonic note (e.g., C or C# = C) there are two or more
        different notes (such as E and E-) in the chord. If there are no repeated
        scale degrees, return false.

        >>> cchord = chord.Chord (['C', 'E', 'E-', 'G'])
        >>> other = chord.Chord (['C', 'E', 'F-', 'G'])
        >>> cchord.hasAnyRepeatedDiatonicNote()
        True

        >>> other.hasAnyRepeatedDiatonicNote() # returns false (chromatically identical notes of different scale degrees do not count).
        False

        '''
        for i in range(1, 8): ## == 1 - 7 inclusive
            if self.hasRepeatedChordStep(i, testRoot) == True:
                return True
        return False

    def hasComponentVolumes(self):
        '''Utility method to determine if this object has component
        :class:`~music21.volume.Volume` objects assigned to each
        note-component.

        >>> c1 = chord.Chord(['c4', 'd-1', 'g6'])
        >>> c1.volume = [60, 20, 120]
        >>> [n.volume.velocity for n in c1]
        [60, 20, 120]

        >>> c1.hasComponentVolumes()
        True

        >>> c2 = chord.Chord(['c4', 'd-1', 'g6'])
        >>> c2.volume.velocity = 23
        >>> c2.hasComponentVolumes()
        False

        >>> c3 = chord.Chord(['c4', 'd-1', 'g6'])
        >>> c3.volume = [.2, .5, .8]
        >>> [n.volume.velocity for n in c3]
        [25, 64, 102]

        >>> c4 = chord.Chord(['c4', 'd-1', 'g6'])
        >>> c4.volume = 89
        >>> c4.volume.velocity
        89

        >>> c4.hasComponentVolumes()
        False

        '''
        count = 0
        for c in self._notes:
            # access private attribute, as property will create otherwise
            if c._volume is not None:
                count += 1
        if count == len(self._notes):
            #environLocal.printDebug(['hasComponentVolumes:', True])
            return True
        else:
            #environLocal.printDebug(['hasComponentVolumes:', False])
            return False

    def hasRepeatedChordStep(self, chordStep, testRoot=None):
        '''
        Returns True if chordStep above testRoot (or self.root()) has two
        or more different notes (such as E and E-) in it.  Otherwise
        returns False.

        >>> cchord = chord.Chord (['G2', 'E4', 'E-5', 'C6'])
        >>> cchord.hasRepeatedChordStep(3)
        True

        >>> cchord.hasRepeatedChordStep(5)
        False

        '''
        if testRoot is None:
            testRoot = self.root()
            if testRoot is None:
                raise ChordException("Cannot run hasRepeatedChordStep without a root") # possible to raise?

        first = self.intervalFromChordStep(chordStep)
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(testRoot, thisPitch)
            if thisInterval.diatonic.generic.mod7 == chordStep:
                if thisInterval.chromatic.mod12 - first.chromatic.mod12 != 0:
                    return True

        return False

    def intervalFromChordStep(self, chordStep, testRoot=None):
        '''
        Exactly like semitonesFromChordStep, except it returns the interval
        itself instead of the number of semitones:

        >>> cmaj = chord.Chord(['C', 'E', 'G'])
        >>> cmaj.intervalFromChordStep(3) #will return the interval between C and E
        <music21.interval.Interval M3>

        >>> cmaj.intervalFromChordStep(5) #will return the interval between C and G
        <music21.interval.Interval P5>

        >>> print(cmaj.intervalFromChordStep(6))
        None

        '''
        if testRoot is None:
            try:
                testRoot = self.root()
            except ChordException:
                raise ChordException("Cannot run intervalFromChordStep without a root") # possible to raise?

            if testRoot is None:
                raise ChordException("Cannot run intervalFromChordStep without a root") # possible to raise?
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(testRoot, thisPitch)
            if thisInterval.diatonic.generic.mod7 == chordStep:
                return thisInterval
        return None

    def inversion(self, newInversion=None, find=True, testRoot=None, transposeOnSet=True):
        '''
        Returns an integer representing which inversion (if any) the chord is in. Chord
        does not have to be complete, but determines the inversion by looking at the relationship
        of the bass note to the root. Returns max value of 5 for inversion of a thirteenth chord.
        Returns 0 if bass to root interval is 1 or if interval is not a common inversion (1st-5th).
        Octave of bass and root are irrelevant to this calculation of inversion.

        Method doesn't check to see if inversion is reasonable according to the chord provided
        (if only two pitches given, an inversion is still returned)
        see :meth:`~music21.harmony.ChordSymbol.inversionIsValid` for checker method on ChordSymbolObjects.

        >>> a = chord.Chord(['g4', 'b4', 'd5', 'f5'])
        >>> a.inversion()
        0
        >>> a.inversion(1)
        >>> a
        <music21.chord.Chord B4 D5 F5 G5>


        With implicit octaves, D becomes the bass (since octaves start on C):

        >>> a = chord.Chord(['g', 'b', 'd', 'f'])
        >>> a.inversion()
        2

        Note that in inverting a chord with implicit octaves, some
        pitches will gain octave designations, but not necessarily all of them:

        >>> a.inversion(1)
        >>> a
        <music21.chord.Chord B D5 F5 G5>


        >>> CTriad1stInversion = chord.Chord(['E1', 'G1', 'C2'])
        >>> CTriad1stInversion.inversion()
        1

        >>> CTriad2ndInversion = chord.Chord(['G1', 'E2', 'C2'])
        >>> CTriad2ndInversion.inversion()
        2

        >>> DSeventh3rdInversion = chord.Chord(['C4', 'B4'])
        >>> DSeventh3rdInversion.bass(pitch.Pitch('B4'))
        >>> DSeventh3rdInversion.inversion()
        3

        >>> GNinth4thInversion = chord.Chord(['G4', 'B4', 'D5', 'F5', 'A4'])
        >>> GNinth4thInversion.bass(pitch.Pitch('A4'))
        >>> GNinth4thInversion.inversion()
        4

        >>> BbEleventh5thInversion = chord.Chord(['B-','D','F','A','C','E-'])
        >>> BbEleventh5thInversion.bass(pitch.Pitch('E-4'))
        >>> BbEleventh5thInversion.inversion()
        5


        >>> GMajRepeats = chord.Chord(['G4','B5','G6','B6','D7'])
        >>> GMajRepeats.inversion(2)
        >>> GMajRepeats
        <music21.chord.Chord D7 G7 B7 G8 B8>

        >>> GMajRepeats.inversion(3)
        Traceback (most recent call last):
        ChordException: Could not invert chord...inversion may not exist


        If testRoot is True then that temporary root is used instead of self.root(). 
        
        Get the inversion for a seventh chord siving different roots
        
        >>> dim7 = chord.Chord('B4 D5 F5 A-5 C6 E6 G6')
        >>> dim7.inversion()
        0
        >>> dim7.inversion(testRoot=pitch.Pitch('D5'))
        6
        >>> dim7.inversion("six-four")
        Traceback (most recent call last):
        ChordException: Inversion must be an integer      

        if you are trying to crash the system...
        
        >>> chord.Chord().inversion(testRoot=pitch.Pitch('C5')) is None
        True
        '''
        #self._inversion = None
        if testRoot is not None:
            rootPitch = testRoot
        else:
            rootPitch = self.root()

        if newInversion is not None:
            if not common.isNum(newInversion):
                try:
                    newInversion = int(newInversion)
                except:
                    raise ChordException("Inversion must be an integer")
            if transposeOnSet is False:
                self._inversion = newInversion
            else:
                numberOfRunsBeforeCrashing = len(self.pitches) + 2 # could have set bass or root externally
                soughtInversion = newInversion

                self._inversion = None
                currentInversion = self.inversion(find=True)
                while currentInversion != soughtInversion and numberOfRunsBeforeCrashing > 0:
                    currentMaxMidi = max(self.pitches).ps
                    tempBassPitch = self.bass()
                    while tempBassPitch.ps < currentMaxMidi:
                        try:
                            tempBassPitch.octave += 1  # will this work with implicit octave chords???
                        except TypeError:
                            tempBassPitch.octave = tempBassPitch.implicitOctave + 1

                    # housekeeping for next loop tests
                    self._inversion = None
                    self._bass = None
                    self._root = None
                    currentInversion = self.inversion(find=True)
                    numberOfRunsBeforeCrashing -= 1
                if numberOfRunsBeforeCrashing == 0:
                    raise ChordException("Could not invert chord...inversion may not exist")
                else:
                    self.sortAscending(inPlace=True)
                return

        elif (self._inversion is None and find is True) or testRoot is not None:
            try:
                if rootPitch == None or self.bass() == None:
                    return None
            except ChordException:
                raise ChordException("Not a normal inversion") # can this be run?

            #bassNote = self.bass()
            #do all interval calculations with bassNote being one octave below root note
            tempBassPitch = copy.deepcopy(self.bass())
            tempBassPitch.octave = 1
            tempRootPitch = copy.deepcopy(rootPitch)
            tempRootPitch.octave = 2

            bassToRoot = interval.notesToInterval(tempBassPitch, tempRootPitch).generic.simpleDirected
            #print 'bassToRoot', bassToRoot
            if bassToRoot == 1:
                inv = 0
            elif bassToRoot == 6: #triads
                inv = 1
            elif bassToRoot == 4: #triads
                inv = 2
            elif bassToRoot == 2: #sevenths
                inv = 3
            elif bassToRoot == 7: #ninths
                inv = 4
            elif bassToRoot == 5: #eleventh
                inv = 5
            elif bassToRoot == 3: # thirteenth
                inv = 6
            else:
                inv = None #no longer raise an exception if not normal inversion
            # is this cache worth it? or more trouble than it's worth...
            self._inversion = inv
            return inv
        else:
            return self._inversion

    def inversionName(self):
        '''
        Returns an integer representing the common abbreviation for the
        inversion the chord is in. If chord is not in a common inversion,
        returns None.

        Third inversion sevenths return 42 not 2.

        >>> a = chord.Chord(['G3', 'B3', 'F3', 'D3'])
        >>> a.inversionName()
        43
        '''
        try:
            inv = self.inversion()
        except ChordException:
            return None
        seventhMapping = [7, 65, 43, 42]
        triadMapping = [53, 6, 64]

        if self.isSeventh() or self.seventh is not None:
            if 0 <= inv <= 3:
                return seventhMapping[inv]
            else:
                raise ChordException("Not a normal inversion for a seventh: %r" % inv)
        elif self.isTriad():
            if 0 <= inv <= 2:
                return triadMapping[inv]
            else:
                raise ChordException("Not a normal inversion for a triad: %r" % inv)
        else:
            raise ChordException("Not a triad or Seventh, cannot determine inversion.")

    def isAugmentedSixth(self):
        '''
        returns True if the chord is an Augmented 6th chord in first inversion.
        (N.B. a French/Swiss sixth technically needs to be in second inversion)


        >>> c = chord.Chord(['A-3','C4','E-4','F#4'])
        >>> c.isAugmentedSixth()
        True

        Spelling matters

        >>> c.pitches[3].getEnharmonic(inPlace = True)
        >>> c
        <music21.chord.Chord A-3 C4 E-4 G-4>
        >>> c.isAugmentedSixth()
        False


        Italian...

        >>> c = chord.Chord(['A-3','C4', 'F#4'])
        >>> c.isAugmentedSixth()
        True
        '''

        if self.isItalianAugmentedSixth():
            return True
        elif self.isFrenchAugmentedSixth():
            return True
        elif self.isGermanAugmentedSixth():
            return True
        elif self.isSwissAugmentedSixth():
            return True

        return False

    def isAugmentedTriad(self):
        '''Returns True if chord is an Augmented Triad, that is, if it contains only notes that are
        either in unison with the root, a major third above the root, or an augmented fifth above the
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord might NOT seem to have to be spelled correctly because incorrectly spelled Augmented Triads are
        usually augmented triads in some other inversion (e.g. C-E-Ab is a 2nd inversion aug triad; C-Fb-Ab
        is 1st inversion).  However, B#-Fb-Ab does return False as expeccted).

        Returns false if is not an augmented triad.


        >>> c = chord.Chord(["C4", "E4", "G#4"])
        >>> c.isAugmentedTriad()
        True
        >>> c = chord.Chord(["C4", "E4", "G4"])
        >>> c.isAugmentedTriad()
        False

        Other spellings will give other roots!
        >>> c = chord.Chord(["C4", "E4", "A-4"])
        >>> c.isAugmentedTriad()
        True
        >>> c.root()
        <music21.pitch.Pitch A-4>

        >>> c = chord.Chord(["C4", "F-4", "A-4"])
        >>> c.isAugmentedTriad()
        True
        >>> c = chord.Chord(["B#4", "F-4", "A-4"])
        >>> c.isAugmentedTriad()
        False
        
        >>> chord.Chord().isAugmentedTriad()
        False
        '''
        try:
            third = self.third
            fifth = self.fifth
        except ChordException:
            return False

        if third is None or fifth is None:
            return False

        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 4) and (thisInterval.chromatic.mod12 != 8):
                return False
        return True

    def isConsonant(self):
        '''
        returns True if the chord is
             one pitch
             two pitches: uses :meth:`~music21.interval.Interval.isConsonant()` , which
             checks if interval is a major or minor third or sixth or perfect fifth.
             three pitches: if chord is a major or minor triad not in second inversion.

        These rules define all common-practice consonances (and earlier back to about 1300 all imperfect consonances)

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

        Spelling does matter:

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

        OMIT_FROM_DOCS

        Weird things used to happen when some notes have octaves and some don't:

        >>> c13 = chord.Chord(['A4','B4','A'])
        >>> c14 = c13.removeRedundantPitchNames(inPlace = False)
        >>> c14
        <music21.chord.Chord A4 B4>

        >>> i14 = interval.notesToInterval(c14.pitches[0], c14.pitches[1])
        >>> i14
        <music21.interval.Interval M2>

        >>> i14.isConsonant()
        False

        >>> c13.isConsonant()
        False

        '''
        c2 = self.removeRedundantPitchNames(inPlace=False)
        if len(c2.pitches) == 1:
            return True
        elif len(c2.pitches) == 2:
            c3 = self.closedPosition()
            c4 = c3.removeRedundantPitches(inPlace=False) # to get from lowest to highest for P4 protection
            i = interval.notesToInterval(c4.pitches[0], c4.pitches[1])
            return i.isConsonant()
        elif len(c2.pitches) == 3:
            if (self.isMajorTriad() is True
                or self.isMinorTriad() is True) \
                and (self.inversion() != 2):
                return True
            else:
                return False
        else:
            return False

    def isDiminishedSeventh(self):
        '''Returns True if chord is a Diminished Seventh, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, a diminished fifth, or a minor seventh
        above the root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.


        >>> a = chord.Chord(['c', 'e-', 'g-', 'b--'])
        >>> a.isDiminishedSeventh()
        True
        
        >>> chord.Chord().isDiminishedSeventh()
        False
        '''
        try:
            third = self.third
            fifth = self.fifth
            seventh = self.seventh
        except ChordException:
            return False

        if third is None or fifth is None or seventh is None:
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3) and (thisInterval.chromatic.mod12 != 6) and (thisInterval.chromatic.mod12 != 9):
                return False
        return True

    def isDiminishedTriad(self):
        '''Returns True if chord is a Diminished Triad, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, or a diminished fifth above the
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.


        >>> cchord = chord.Chord(['C', 'E-', 'G-'])
        >>> other = chord.Chord(['C', 'E-', 'F#'])

        >>> cchord.isDiminishedTriad() #returns True
        True
        >>> other.isDiminishedTriad() #returns False
        False
        
        >>> chord.Chord().isDiminishedTriad()
        False
        '''
        try:
            third = self.third
            fifth = self.fifth
        except ChordException:
            return False

        if third is None or fifth is None:
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3) and (thisInterval.chromatic.mod12 != 6):
                return False

        return True

    def isDominantSeventh(self):
        '''Returns True if chord is a Dominant Seventh, that is, if it contains only notes that are
        either in unison with the root, a major third above the root, a perfect fifth, or a major seventh
        above the root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.


        >>> a = chord.Chord(['b', 'g', 'd', 'f'])
        >>> a.isDominantSeventh()
        True

        >>> chord.Chord().isDominantSeventh()
        False
        '''
        try:
            third = self.third
            fifth = self.fifth
            seventh = self.seventh
        except ChordException:
            return False

        if third is None or fifth is None or seventh is None:
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 4) and (thisInterval.chromatic.mod12 != 7) and (thisInterval.chromatic.mod12 != 10):
                return False

        return True

    def isFalseDiminishedSeventh(self):
        '''Returns True if chord is a Diminished Seventh, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, a diminished fifth, or a minor seventh
        above the root. Additionally, must contain at least one of each third and fifth above the root.
        Chord MAY BE SPELLED INCORRECTLY. Otherwise returns false.
        
        
        >>> c = chord.Chord('C D# G- A')
        >>> c.isFalseDiminishedSeventh()
        True
        
        >>> chord.Chord().isFalseDiminishedSeventh()
        False        
        '''
        third = False
        fifth = False
        seventh = False

        try: # check for no root
            self.root()
        except ChordException:
            return False


        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3) and (thisInterval.chromatic.mod12 != 6) and (thisInterval.chromatic.mod12 != 9):
                return False
            elif thisInterval.chromatic.mod12 == 3:
                third = True
            elif thisInterval.chromatic.mod12 == 6:
                fifth = True
            elif thisInterval.chromatic.mod12 == 9:
                seventh = True
        if third is None or fifth is None or seventh is None:
            return False

        return True

    def isFrenchAugmentedSixth(self):
        '''
        Returns True if the chord is a French augmented sixth chord
        (flat 6th scale degree in bass, tonic, second scale degree, and raised 4th).

        N.B. The findRoot() method of music21.chord Chord determines
        the root based on the note with
        the most thirds above it. However, under this definition, a
        1st-inversion french augmented sixth chord
        resembles a second inversion chord, not the first inversion
        subdominant chord it is based
        upon. We fix this by adjusting the root. First, however, we
        check to see if the chord is
        in second inversion to begin with, otherwise its not
        a Fr+6 chord. This is to avoid ChordException errors.

        >>> fr6a = chord.Chord(['A-3','C4','D4','F#4'])
        >>> fr6a.isFrenchAugmentedSixth()
        True

        >>> fr6b = chord.Chord(['A-3','C4','E--4','F#4'])
        >>> fr6b.isFrenchAugmentedSixth()
        False

        Inversion matters...
    
        >>> fr6c = chord.Chord(['C4','D4','F#4', 'A-4'])
        >>> fr6c.isFrenchAugmentedSixth()
        False

        OMIT_FROM_DOCS
    
        >>> chord.Chord().isFrenchAugmentedSixth()
        False        

        >>> fr6d = chord.Chord(['A-3','C-4','D4','F#4'])
        >>> fr6d.isFrenchAugmentedSixth()
        False
        '''
        augSixthChord = self.removeRedundantPitchNames(inPlace=False)
        ### Fr+6 => Minor sixth scale step in bass, tonic, raised 4th + second scale degree.
        try:
            if not augSixthChord.inversion() == 2:
                return False
        except ChordException:
            return False
        augSixthChord.root(augSixthChord.getChordStep(3))
        ### Chord must be in first inversion.
        if not augSixthChord.inversion() == 1:
            return False
        ### Augmented sixth interval (simple or compound) must be present between bass and raised 4th (root of chord)
        bass = augSixthChord.bass() # might be caught by the try: except: above
        root = augSixthChord.root()
        if bass is None or root is None:
            return False
        augSixthInterval = interval.Interval(bass, root)
        if not (augSixthInterval.diatonic.specificName == 'Augmented' and augSixthInterval.generic.simpleDirected == 6):
            return False
        ### The fifth of the chord must be the tonic. The fifth of the chord is the tonic if and only if
        ### there is a M3 (simple or compound) between the bass (m6 scale step) and the fifth of the chord.
        tonic = augSixthChord.getChordStep(5)
        if tonic is None:
            return False
        majThirdInterval = interval.Interval(bass, tonic)
        if not (majThirdInterval.diatonic.specificName == 'Major' and majThirdInterval.generic.simpleDirected == 3):
            return False
        ### The sixth of the chord must be the supertonic. The sixth of the chord is the supertonic if and only if
        ### there is a A4 (simple or compound) between the bass (m6 scale step) and the sixth of the chord.
        supertonic = augSixthChord.getChordStep(6)
        augFourthInterval = interval.Interval(bass, supertonic)
        if supertonic is None:
            return False
        if not (augFourthInterval.diatonic.specificName == 'Augmented' and augFourthInterval.generic.simpleDirected == 4):
            return False
        ### No other pitches may be present that aren't the m6 scale step, raised 4th, tonic, or supertonic.
        for samplePitch in augSixthChord.pitches:
            if not (samplePitch == bass or samplePitch == root or samplePitch == tonic or samplePitch == supertonic):
                return False
        return True

    def isGermanAugmentedSixth(self):
        augSixthChord = self.removeRedundantPitchNames(inPlace=False)
        ### Chord must be in first inversion.
        if not augSixthChord.inversion() == 1:
            return False

        ### Augmented sixth interval (simple or compound) must be present between bass and raised 4th (root of chord)
        bass = augSixthChord.bass()
        root = augSixthChord.root()
        if bass is None or root is None:
            return False
        augSixthInterval = interval.Interval(bass, root)
        if not (augSixthInterval.diatonic.specificName == 'Augmented' and augSixthInterval.generic.simpleDirected == 6):
            return False

        ### The fifth of the chord must be the tonic. The fifth of the chord is the tonic if and only if
        ### there is a M3 (simple or compound) between the bass (m6 scale step) and the fifth of the chord.
        tonic = augSixthChord.getChordStep(5)
        if tonic is None:
            return False
        majThirdInterval = interval.Interval(bass, tonic)
        if not (majThirdInterval.diatonic.specificName == 'Major' and majThirdInterval.generic.simpleDirected == 3):
            return False

        ### The seventh of the chord must be the mediant. The seventh of the chord is the mediant if and only if
        ### there is a P5 (simple or compound) between the bass (m6 scale step) and the fifth of the chord.
        mediant = augSixthChord.getChordStep(7)
        if mediant is None:
            return False
        perfectFifthInterval = interval.Interval(bass, mediant)
        if not (perfectFifthInterval.diatonic.specificName == 'Perfect' and perfectFifthInterval.generic.simpleDirected == 5):
            return False

        return True

    def isHalfDiminishedSeventh(self):
        '''Returns True if chord is a Half Diminished Seventh, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, a diminished fifth, or a major seventh
        above the root. Additionally, must contain at least one of each third, fifth, and seventh above the root.
        Chord must be spelled correctly. Otherwise returns false.


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
        
        >>> chord.Chord().isHalfDiminishedSeventh()
        False
        '''
        try:
            third = self.third
            fifth = self.fifth
            seventh = self.seventh
        except ChordException:
            return False

        if third is None or fifth is None or seventh is None:
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3) and (thisInterval.chromatic.mod12 != 6) and (thisInterval.chromatic.mod12 != 10):
                return False

        return True

    def isIncompleteMajorTriad(self):
        '''
        Returns True if the chord is an incomplete Major triad, or, essentially,
        a dyad of root and major third


        >>> c1 = chord.Chord(['C4','E3'])
        >>> c1.isMajorTriad()
        False
        >>> c1.isIncompleteMajorTriad()
        True


        Note that complete major triads return False:


        >>> c2 = chord.Chord(['C4','E3', 'G5'])
        >>> c2.isIncompleteMajorTriad()
        False

        Remember, MAJOR Triad...
        
        >>> c3 = chord.Chord(['C4','E-3'])
        >>> c3.isIncompleteMajorTriad()
        False
        
        >>> chord.Chord().isIncompleteMajorTriad()
        False        
        '''
        try:
            third = self.third
        except ChordException:
            return False

        if third is None:
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

        >>> chord.Chord().isIncompleteMinorTriad()
        False

        '''
        try:
            third = self.third
        except ChordException:
            return False
        if third is None:
            return False

        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3):
                return False

        return True

    def isItalianAugmentedSixth(self, restrictDoublings=False):
        '''
        Returns true if the chord is a properly spelled Italian augmented sixth chord in
        first inversion.

        If restrictDoublings is set to True then only the tonic may be doubled.

        >>> c1 = chord.Chord(['A-4','C5','F#6'])
        >>> c1.isItalianAugmentedSixth()
        True


        Spelling matters:

        >>> c2 = chord.Chord(['A-4','C5','G-6'])
        >>> c2.isItalianAugmentedSixth()
        False
        
        So does inversion:
        
        >>> c3 = chord.Chord(['F#4','C5','A-6'])
        >>> c3.isItalianAugmentedSixth()
        False
        >>> c4 = chord.Chord(['C5','A-5','F#6'])
        >>> c4.isItalianAugmentedSixth()
        False

        If inversions don't matter to you, put the chord in another inversion:
        
        >>> import copy
        >>> c5 = copy.deepcopy(c4)
        >>> c5.inversion(1)
        >>> c5.isItalianAugmentedSixth()
        True
        



        If doubling rules are turned on then only the tonic can be doubled:


        >>> c4 = chord.Chord(['A-4','C5','F#6', 'C6', 'C7'])
        >>> c4.isItalianAugmentedSixth(restrictDoublings = True)
        True
        >>> c5 = chord.Chord(['A-4','C5','F#6', 'C5', 'F#7'])
        >>> c5.isItalianAugmentedSixth(restrictDoublings = True)
        False
        >>> c5.isItalianAugmentedSixth(restrictDoublings = False)
        True
        '''
        ### It+6 => Minor sixth scale step in bass, tonic, raised 4th + doubling of tonic note.
        augSixthChord = self.removeRedundantPitchNames(inPlace=False)

        ### Chord must be in first inversion.
        if not augSixthChord.inversion() == 1:
            return False

        ### Augmented sixth interval (simple or compound) must be present between bass and raised 4th (root of chord)
        bass = augSixthChord.bass()
        root = augSixthChord.root()
        if bass is None or root is None:
            return False
        augSixthInterval = interval.Interval(bass, root)
        if not (augSixthInterval.diatonic.specificName == 'Augmented' and augSixthInterval.generic.simpleDirected == 6):
            return False

        ### The fifth of the chord must be the tonic. The fifth of the chord is the tonic if and only if
        ### there is a M3 (simple or compound) between the bass (m6 scale step) and the fifth of the chord.
        tonic = augSixthChord.getChordStep(5)
        if tonic is None:
            return False
        majThirdInterval = interval.Interval(bass, tonic)
        if not (majThirdInterval.diatonic.specificName == 'Major' and majThirdInterval.generic.simpleDirected == 3):
            return False

        ### No other pitches may be present that aren't the m6 scale step, raised 4th, or tonic.
        for samplePitch in augSixthChord.pitches:
            if not (samplePitch == bass or samplePitch == root or samplePitch == tonic):
                return False

        if restrictDoublings:
            # only the tonic can be doubled...
            for samplePitch in self.pitches:
                if not (samplePitch.nameWithOctave == bass.nameWithOctave
                    or samplePitch.nameWithOctave == root.nameWithOctave
                    or samplePitch.nameWithOctave == tonic.nameWithOctave):
                    if samplePitch.name != tonic.name:
                        return False

        return True

    def isMajorTriad(self):
        '''
        Returns True if chord is a Major Triad, that is, if it contains only notes that are
        either in unison with the root, a major third above the root, or a perfect fifth above the
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.

        Example:

        >>> cchord = chord.Chord(['C', 'E', 'G'])
        >>> other = chord.Chord(['C', 'G'])
        >>> cchord.isMajorTriad()
        True
        >>> other.isMajorTriad()
        False

        Notice that the proper spelling of notes is crucial
        
        >>> chord.Chord(['B-','D','F']).isMajorTriad()
        True
        >>> chord.Chord(['A#','D','F']).isMajorTriad()
        False
        
        (See: :meth:`~music21.chord.Chord.forteClassTn` to catch this case; major triads 
        in the forte system are 3-11B no matter how they are spelled.)
        
        >>> chord.Chord(['A#','D','F']).forteClassTn == '3-11B'
        True
        
        
        OMIT_FROM_DOCS
        
        Strange chords like [C,E###,G---] used to return True.  E### = G
        and G--- = E, so the chord is found to be a major triad, even though it should
        not be.  This bug is now fixed.
        
        >>> chord.Chord(['C','E###','G---']).isMajorTriad()
        False
        >>> chord.Chord(['C','E','G','E###','G---']).isMajorTriad()
        False
        

        >>> chord.Chord().isMajorTriad()
        False
        '''
        try:
            third = self.third
            fifth = self.fifth
        except ChordException:
            return False
        if third is None or fifth is None:
            return False

        root = self.root()        
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(root, thisPitch)
            if (thisPitch is third) and (thisInterval.chromatic.mod12 != 4):
                return False
            if (thisPitch is fifth) and (thisInterval.chromatic.mod12 != 7):
                return False
            if thisPitch.name not in (root.name, third.name, fifth.name):
                return False

        return True

    def isMinorTriad(self):
        '''
        Returns True if chord is a Minor Triad, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, or a perfect fifth above the
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.

        Example:

        >>> cchord = chord.Chord(['C', 'E-', 'G'])
        >>> other = chord.Chord(['C', 'E', 'G'])
        >>> cchord.isMinorTriad() # returns True
        True
        >>> other.isMinorTriad() # returns False
        False

        OMIT_FROM_DOCS

        >>> chord.Chord().isMinorTriad()
        False

        '''
        try:
            third = self.third
            fifth = self.fifth
        except ChordException:
            return False
        if third is None or fifth is None:
            return False

        root = self.root()        
        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(root, thisPitch)
            if (thisPitch is third) and (thisInterval.chromatic.mod12 != 3):
                return False
            if (thisPitch is fifth) and (thisInterval.chromatic.mod12 != 7):
                return False
            if thisPitch.name not in (root.name, third.name, fifth.name):
                return False

        return True

    def isSeventh(self):
        '''
        Returns True if chord contains at least one of each of Third, Fifth, and Seventh,
        and every note in the chord is a Third, Fifth, or Seventh, such that there are no
        repeated scale degrees (ex: E and E-). Else return false.

        Example:


        >>> cchord = chord.Chord(['C', 'E', 'G', 'B'])
        >>> other = chord.Chord(['C', 'D', 'E', 'F', 'G', 'B'])
        >>> cchord.isSeventh() # returns True
        True
        >>> other.isSeventh() # returns False
        False

        OMIT_FROM_DOCS

        >>> chord.Chord().isSeventh()
        False

        '''
        try:
            third = self.third
            fifth = self.fifth
            seventh = self.seventh
        except ChordException:
            return False

        if third is None or fifth is None or seventh is None:
            return False

        if self.hasAnyRepeatedDiatonicNote():
            return False

        for thisPitch in self.pitches:
            thisInterval = interval.notesToInterval(self.root(), thisPitch)
            if (thisInterval.diatonic.generic.mod7 != 1) and (thisInterval.diatonic.generic.mod7 != 3) and (thisInterval.diatonic.generic.mod7 != 5) and (thisInterval.diatonic.generic.mod7 != 7):
                return False

        return True

    def isSwissAugmentedSixth(self):
        '''
        Returns true is it is a respelled German augmented 6th chord with
        sharp 2 instead of flat 3.  This chord has many names,
        Swiss Augmented Sixth, Alsatian Chord, English A6, Norwegian, etc.
        as well as doubly-augmented sixth, which is a bit of a misnomer since
        it is the 4th that is doubly augmented, not the sixth.
        '''

        ### Sw+6 => Minor sixth scale step in bass, tonic, raised 4th + raised 2nd scale degree.
        augSixthChord = self.removeRedundantPitchNames(inPlace=False)

        ### The findRoot() method of music21.chord Chord determines the root based on the note with
        ### the most thirds above it. However, under this definition, a Swiss augmented sixth chord
        ### resembles a second inversion chord, not the first inversion subdominant chord it is based
        ### upon. We fix this by adjusting the root. First, however, we check to see if the chord is
        ### in second inversion to begin with, otherwise its not a Sw+6 chord. This is to avoid
        ### ChordException errors.
        if not augSixthChord.inversion() == 2:
            return False
        augSixthChord.root(augSixthChord.getChordStep(3))

        ### Chord must be in first inversion.
        if not augSixthChord.inversion() == 1:
            return False

        ### Augmented sixth interval (simple or compound) must be present between bass and raised 4th (root of chord)
        bass = augSixthChord.bass()
        root = augSixthChord.root()
        if bass is None or root is None:
            return False
        augSixthInterval = interval.Interval(bass, root)
        if not (augSixthInterval.diatonic.specificName == 'Augmented' and augSixthInterval.generic.simpleDirected == 6):
            return False

        ### The fifth of the chord must be the tonic. The fifth of the chord is the tonic if and only if
        ### there is a M3 (simple or compound) between the bass (m6 scale step) and the fifth of the chord.
        tonic = augSixthChord.getChordStep(5)
        if tonic is None:
            return False
        majThirdInterval = interval.Interval(bass, tonic)
        if not (majThirdInterval.diatonic.specificName == 'Major' and majThirdInterval.generic.simpleDirected == 3):
            return False

        ### The sixth of the chord must be the supertonic. The sixth of the chord is the supertonic if and only if
        ### there is a A4 (simple or compound) between the bass (m6 scale step) and the sixth of the chord.
        supertonic = augSixthChord.getChordStep(6)
        augFourthInterval = interval.Interval(bass, supertonic)
        if supertonic is None:
            return False
        if not (augFourthInterval.diatonic.specificName == 'Doubly-Augmented' and augFourthInterval.generic.simpleDirected == 4):
            return False

        ### No other pitches may be present that aren't the m6 scale step, raised 4th, tonic, or supertonic.
        for samplePitch in augSixthChord.pitches:
            if not (samplePitch == bass or samplePitch == root or samplePitch == tonic or samplePitch == supertonic):
                return False

        return True

    def isTriad(self):
        '''
        Returns boolean.

        "Contains vs. Is:" A dominant-seventh chord is NOT a triad.
        returns True if the chord contains at least one Third and one Fifth and all notes are
        equivalent to either of those notes. Only returns True if triad is spelled correctly.

        >>> cchord = chord.Chord(['C4', 'E4', 'A4'])
        >>> cchord.isTriad()
        True

        >>> other = chord.Chord(['C', 'D', 'E', 'F', 'G'])
        >>> other.isTriad()
        False

        >>> incorrectlySpelled = chord.Chord(['C','D#','G'])
        >>> incorrectlySpelled.isTriad()
        False

        >>> incorrectlySpelled.pitches[1].getEnharmonic(inPlace = True)
        >>> incorrectlySpelled.isTriad()
        True

        OMIT_FROM_DOCS

        >>> chord.Chord().isTriad()
        False

        '''
        try:
            third = self.third
            fifth = self.fifth
        except ChordException:
            return False
        if third is None or fifth is None:
            return False
        for thisPitch in self.pitches:
            try:
                thisInterval = interval.notesToInterval(self.root(), thisPitch)
            except ChordException:
                return False
            if (thisInterval.diatonic.generic.mod7 != 1) and (thisInterval.diatonic.generic.mod7 != 3) and (thisInterval.diatonic.generic.mod7 != 5):
                return False
            if self.hasAnyRepeatedDiatonicNote():
                return False
        return True

    def removeRedundantPitches(self, inPlace=True):
        '''
        Remove all but one instance of a pitch that appears twice.

        It removes based on the name of the note and the octave, so the same
        note name in two different octaves is retained.

        If `inPlace` is True, a copy is not made and None is returned;
        otherwise a copy is made and that copy is returned.

        >>> c1 = chord.Chord(['c2', 'e3', 'g4', 'e3'])
        >>> c1
        <music21.chord.Chord C2 E3 G4 E3>

        >>> c1.removeRedundantPitches(inPlace=True)
        >>> c1
        <music21.chord.Chord C2 G4 E3>

        >>> c1.forteClass
        '3-11B'

        >>> c2 = chord.Chord(['c2', 'e3', 'g4', 'c5'])
        >>> c2c = c2.removeRedundantPitches(inPlace=False)
        >>> c2c
        <music21.chord.Chord C2 E3 G4 C5>

        It is a known bug that because pitch.nameWithOctave gives
        the same value for B-flat in octave 1 as B-natural in octave
        negative 1, negative octaves can screw up this method.
        With all the things left to do for music21, it doesn't seem
        a bug worth squashing at this moment, but FYI:

        >>> p1 = pitch.Pitch('B-')
        >>> p1.octave = 1
        >>> p2 = pitch.Pitch('B')
        >>> p2.octave = -1
        >>> c3 = chord.Chord([p1, p2])
        >>> c3.removeRedundantPitches(inPlace=True)
        >>> c3.pitches
        (<music21.pitch.Pitch B-1>,)

        The first pitch survives:

        >>> c3.pitches[0] is p1
        True

        >>> c3.pitches[0] is p2
        False

        '''
        return self._removePitchByRedundantAttribute('nameWithOctave',
              inPlace=inPlace)

    def removeRedundantPitchClasses(self, inPlace=True):
        '''
        Remove all but the FIRST instance of a pitch class with more than one
        instance of that pitch class.

        If `inPlace` is True, a copy is not made and None is returned;
        otherwise a copy is made and that copy is returned.

        >>> c1 = chord.Chord(['c2', 'e3', 'g4', 'e3'])
        >>> c1.removeRedundantPitchClasses(inPlace=True)
        >>> c1.pitches
        (<music21.pitch.Pitch C2>, <music21.pitch.Pitch G4>, <music21.pitch.Pitch E3>)

        >>> c2 = chord.Chord(['c5', 'e3', 'g4', 'c2', 'e3', 'f-4'])
        >>> c2.removeRedundantPitchClasses(inPlace=True)
        >>> c2.pitches
        (<music21.pitch.Pitch C5>, <music21.pitch.Pitch G4>, <music21.pitch.Pitch E3>)

        '''
        return self._removePitchByRedundantAttribute('pitchClass',
              inPlace=inPlace)

    def removeRedundantPitchNames(self, inPlace=True):
        '''
        Remove all but the FIRST instance of a pitch class with more than one
        instance of that pitch name regardless of octave (but note that
        spelling matters, so that in the example, the F-flat stays even
        though there is already an E.)

        If `inPlace` is True, a copy is not made and None is returned;
        otherwise a copy is made and that copy is returned.

        >>> c2 = chord.Chord(['c5', 'e3', 'g4', 'c2', 'e3', 'f-4'])
        >>> c2
        <music21.chord.Chord C5 E3 G4 C2 E3 F-4>

        >>> c2.removeRedundantPitchNames(inPlace = True)
        >>> c2
        <music21.chord.Chord C5 G4 E3 F-4>

        '''
        return self._removePitchByRedundantAttribute('name',
              inPlace=inPlace)

    def root(self, newroot=False, find=True):
        '''
        Returns or sets the Root of the chord. If not set, will run findRoot (q.v.)

        >>> cmaj = chord.Chord(['E3', 'C4', 'G5'])
        >>> cmaj.root()
        <music21.pitch.Pitch C4>

        By default this method uses an algorithm to find the root among the
        chord's pitches, if no root has been previously specified. If this is
        not intended, set find to False when calling this method, and 'None'
        will be returned if no root is specified

        >>> c = chord.Chord(['E3','G3','B4'])
        >>> c.root(find=False) == None
        True

        >>> d = harmony.ChordSymbol('CM/E')
        >>> d.root(find=False) == None
        True

        >>> d.root()
        <music21.pitch.Pitch C4>

        '''
        if newroot:
            if common.isStr(newroot):
                newroot = newroot.replace('b', '-')
                self._root = pitch.Pitch(newroot)
            else:
                self._root = newroot
            self._inversion = None # reset inversion if root changes
        elif (self._root is None) and find:
            self._root = self.findRoot()
            return self._root
        else:
            return self._root

    def semiClosedPosition(self, forceOctave=None, inPlace=False, leaveRedundantPitches=False):
        '''
        Similar to :meth:`~music21.chord.Chord.ClosedPosition` in that it
        moves everything within an octave EXCEPT if there's already
        a pitch at that step, then it puts it up an octave.  It's a
        very useful display standard for dense post-tonal chords.

        >>> c1 = chord.Chord(['C3','E5','C#6','E-7', 'G8','C9','E#9'])
        >>> c2 = c1.semiClosedPosition(inPlace=False)
        >>> c2
        <music21.chord.Chord C3 E-3 G3 C#4 E4 E#5>

        `leaveRedundantPitches` still works, and gives them a new octave!

        >>> c3 = c1.semiClosedPosition(
        ...     inPlace=False,
        ...     leaveRedundantPitches=True,
        ...     )
        >>> c3
        <music21.chord.Chord C3 E-3 G3 C4 E4 C#5 E#5>

        of course `forceOctave` still works, as does `inPlace=True`.

        >>> c1.semiClosedPosition(
        ...     forceOctave=2,
        ...     inPlace=True,
        ...     leaveRedundantPitches=True,
        ...     )
        >>> c1
        <music21.chord.Chord C2 E-2 G2 C3 E3 C#4 E#4>

        '''
        if inPlace is False:
            c2 = self.closedPosition(forceOctave, inPlace, leaveRedundantPitches)
        else:
            self.closedPosition(forceOctave, inPlace, leaveRedundantPitches)
            c2 = self
        #startOctave = c2.bass().octave
        remainingPitches = copy.copy(c2.pitches) # no deepcopy needed

        while len(remainingPitches) > 0:
            usedSteps = []
            newRemainingPitches = []
            for i, p in enumerate(remainingPitches):
                if p.step not in usedSteps:
                    usedSteps.append(p.step)
                else:
                    p.octave += 1
                    newRemainingPitches.append(p)
            remainingPitches = newRemainingPitches

        c2.sortAscending(inPlace=True)

        if inPlace is False:
            return c2

    def semitonesFromChordStep(self, chordStep, testRoot=None):
        '''
        Returns the number of semitones (mod12) above the root that the
        chordStep lies (i.e., 3 = third of the chord; 5 = fifth, etc.) if one
        exists.  Or None if it does not exist.

        You can optionally specify a note.Note object to try as the root.  It
        does not change the Chord.root object.  We use these methods to figure
        out what the root of the triad is.

        Currently there is a bug that in the case of a triply diminished third
        (e.g., "c" => "e----"), this function will incorrectly claim no third
        exists.  Perhaps this should be construed as a feature.

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

        >>> cchord = chord.Chord(['E3', 'C4', 'G5'])
        >>> cchord.semitonesFromChordStep(3) # distance from C to E
        4

        >>> cchord.semitonesFromChordStep(5) # C to G
        7

        >>> print(cchord.semitonesFromChordStep(6)) # will return None
        None

        >>> achord = chord.Chord(['a2', 'c4', 'c#5', 'e#7'])
        >>> achord.semitonesFromChordStep(3) # returns the semitones to the FIRST third.
        3

        >>> achord.semitonesFromChordStep(5)
        8

        >>> print(achord.semitonesFromChordStep(2)) # will return None
        None


        Test whether this strange chord gets the B# as 0 semitones:
        
        >>> c = chord.Chord(['C4','E4','G4','B#4'])
        >>> c.semitonesFromChordStep(7)
        0

        If testRoot is set to a Pitch object then that note is used as the root of the chord
        regardless of anything else that might be considered.
        
        A-minor: 1st inversion.
        
        >>> aMin = chord.Chord(['C4','E4','A4'])
        >>> aMin.semitonesFromChordStep(3)
        3
        >>> aMin.semitonesFromChordStep(5)
        7

        C6 chord, jazz like, root position:
        
        >>> cPitch = pitch.Pitch('C4')
        >>> c6 = aMin  # renaming for clarity
        >>> c6.semitonesFromChordStep(3, testRoot = cPitch)
        4
        >>> c6.semitonesFromChordStep(5, testRoot = cPitch) is None
        True
        >>> c6.semitonesFromChordStep(6, testRoot = cPitch)
        9
            

        '''
        tempInt = self.intervalFromChordStep(chordStep, testRoot)
        if tempInt is None:
            return None
        else:
            return tempInt.chromatic.mod12

    def setColor(self, value, pitchTarget=None):
        '''
        Set color for specific pitch.
        
        >>> c = chord.Chord('C4 E4 G4')
        >>> c.setColor('red', 'C4')
        >>> c['0.color']
        'red'
        >>> c.setColor('blue') # set for whole chord...
        >>> c.color
        'blue'
        >>> c.setColor('red', 'C9')
        Traceback (most recent call last):
        ChordException: the given pitch is not in the Chord: C9
        '''
        # assign to base
        if pitchTarget is None and len(self._notes) > 0:
            self.color = value
            return
        elif common.isStr(pitchTarget):
            pitchTarget = pitch.Pitch(pitchTarget)

        match = False
        for d in self._notes:
            if d.pitch is pitchTarget:
                d.color = value
                match = True
                break
        if not match: # look at equality of value
            for d in self._notes:
                if d.pitch == pitchTarget:
                    d.color = value
                    match = True
                    break
        if not match:
            raise ChordException(
                'the given pitch is not in the Chord: {0}'.format(pitchTarget))

    def setNotehead(self, nh, pitchTarget):
        '''Given a notehead attribute as a string and a pitch object in this
        Chord, set the notehead attribute of that pitch to the value of that
        notehead. Valid notehead type names are found in note.noteheadTypeNames
        (see below):

        >>> for noteheadType in note.noteheadTypeNames:
        ...    noteheadType
        ...
        'arrow down'
        'arrow up'
        'back slashed'
        'circle dot'
        'circle-x'
        'cluster'
        'cross'
        'diamond'
        'do'
        'fa'
        'inverted triangle'
        'la'
        'left triangle'
        'mi'
        'none'
        'normal'
        're'
        'rectangle'
        'slash'
        'slashed'
        'so'
        'square'
        'ti'
        'triangle'
        'x'

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.setNotehead('diamond', c1.pitches[1]) # just to g
        >>> c1.getNotehead(c1.pitches[1])
        'diamond'

        >>> c1.getNotehead(c1.pitches[0])
        'normal'

        If a chord has two of the same pitch, but each associated with a different notehead, then
        object equality must be used to distinguish between the two.

        >>> c2 = chord.Chord(['D4','D4'])
        >>> secondD4 = c2.pitches[1]
        >>> c2.setNotehead('diamond', secondD4)
        >>> for i in [0,1]:
        ...     c2.getNotehead(c2.pitches[i])
        ...
        'normal'
        'diamond'

        By default assigns to first pitch:
        
        >>> c3 = chord.Chord('C3 F4')
        >>> c3.setNotehead('slash', None)
        >>> c3['0.notehead']
        'slash'

        Less safe to match by string, but possible:
        
        >>> c3.setNotehead('so', 'F4')
        >>> c3['1.notehead']
        'so'

        Error:

        >>> c3.setNotehead('so', 'G4')
        Traceback (most recent call last):
        ChordException: the given pitch is not in the Chord: G4

        '''
        # assign to first pitch by default
        if pitchTarget is None and len(self._notes) > 0:
            pitchTarget = self._notes[0].pitch
        elif common.isStr(pitchTarget):
            pitchTarget = pitch.Pitch(pitchTarget)
        match = False
        for d in self._notes:
            if d.pitch is pitchTarget:
                d.notehead = nh
                match = True
                break
        if not match:
            for d in self._notes:
                if d.pitch == pitchTarget:
                    d.notehead = nh
                    match = True
                    break
        if not match:
            raise ChordException('the given pitch is not in the Chord: %s' % pitchTarget)

    def setNoteheadFill(self, nh, pitchTarget):
        '''Given a noteheadFill attribute as a string and a pitch object in this
        Chord, set the noteheadFill attribute of that pitch to the value of that
        notehead. Valid noteheadFill names are True, False, None (default)
        
        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.setNoteheadFill(False, c1.pitches[1]) # just to g
        >>> c1.getNoteheadFill(c1.pitches[1])
        False

        >>> c1.getNoteheadFill(c1.pitches[0]) is None
        True

        If a chord has two of the same pitch, but each associated with a different notehead, then
        object equality must be used to distinguish between the two.

        >>> c2 = chord.Chord(['D4','D4'])
        >>> secondD4 = c2.pitches[1]
        >>> c2.setNoteheadFill(False, secondD4)
        >>> for i in [0,1]:
        ...     print(c2.getNoteheadFill(c2.pitches[i]))
        ...
        None
        False

        By default assigns to first pitch:
        
        >>> c3 = chord.Chord('C3 F4')
        >>> c3.setNoteheadFill(False, None)
        >>> c3['0.noteheadFill']
        False

        Less safe to match by string, but possible:
        
        >>> c3.setNoteheadFill(True, 'F4')
        >>> c3['1.noteheadFill']
        True

        Error:
        >>> c3.setNoteheadFill(True, 'G4')
        Traceback (most recent call last):
        ChordException: the given pitch is not in the Chord: G4

        '''
        # assign to first pitch by default
        if pitchTarget is None and len(self._notes) > 0:
            pitchTarget = self._notes[0].pitch
        elif common.isStr(pitchTarget):
            pitchTarget = pitch.Pitch(pitchTarget)
        match = False
        for d in self._notes:
            if d.pitch is pitchTarget:
                d.noteheadFill = nh
                match = True
                break
        if not match:
            for d in self._notes:
                if d.pitch == pitchTarget:
                    d.noteheadFill = nh
                    match = True
                    break
        if not match:
            raise ChordException('the given pitch is not in the Chord: %s' % pitchTarget)


    def setStemDirection(self, stem, pitchTarget):
        '''Given a stem attribute as a string and a pitch object in this Chord,
        set the stem attribute of that pitch to the value of that stem. Valid
        stem directions are found note.stemDirectionNames (see below).

        >>> for name in note.stemDirectionNames:
        ...     name
        ...
        'double'
        'down'
        'noStem'
        'none'
        'unspecified'
        'up'

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.setStemDirection('double', c1.pitches[1]) # just to g
        >>> c1.getStemDirection(c1.pitches[1])
        'double'

        >>> c1.getStemDirection(c1.pitches[0])
        'unspecified'

        If a chord has two of the same pitch, but each associated with a
        different stem, then object equality must be used to distinguish
        between the two.

        >>> c2 = chord.Chord(['D4','D4'])
        >>> secondD4 = c2.pitches[1]
        >>> c2.setStemDirection('double', secondD4)
        >>> for i in [0,1]:
        ...    print(c2.getStemDirection(c2.pitches[i]))
        ...
        unspecified
        double

        By default assigns to first pitch:
        
        >>> c3 = chord.Chord('C3 F4')
        >>> c3.setStemDirection('down', None)
        >>> c3['0.stemDirection']
        'down'

        Less safe to match by string, but possible:
        
        >>> c3.setStemDirection('down', 'F4')
        >>> c3['1.stemDirection']
        'down'

        Error:
        >>> c3.setStemDirection('up', 'G4')
        Traceback (most recent call last):
        ChordException: the given pitch is not in the Chord: G4

        '''
        if pitchTarget is None and len(self._notes) > 0:
            pitchTarget = self._notes[0].pitch # first is default
        elif common.isStr(pitchTarget):
            pitchTarget = pitch.Pitch(pitchTarget)
        match = False
        for d in self._notes:
            if d.pitch is pitchTarget:
                d.stemDirection = stem
                match = True
                break
        if not match:
            for d in self._notes:
                if d.pitch == pitchTarget:
                    d.stemDirection = stem
                    match = True
                    break
        if not match:
            raise ChordException(
                'the given pitch is not in the Chord: {}'.format(pitchTarget))

    def setTie(self, t, pitchTarget):
        '''Given a tie object (or a tie type string) and a pitch in this Chord,
        set the pitch's tie attribute in this chord to that tie type.

        >>> c1 = chord.Chord(['d3', 'e-4', 'b-4'])
        >>> t1 = tie.Tie('start')
        >>> c1.setTie(t1, 'b-4') # or it can be done with a pitch.Pitch object
        >>> c1.getTie(c1.pitches[2]) == t1
        True

        Setting a tie with a chord with the same pitch twice requires
        getting the exact pitch object out to be sure which one...

        >>> c2 = chord.Chord(['D4','D4'])
        >>> secondD4 = c2.pitches[1]
        >>> c2.setTie('start', secondD4)
        >>> for i in [0,1]:
        ...    print(c2.getTie(c2.pitches[i]))
        ...
        None
        <music21.tie.Tie start>


        >>> c3 = chord.Chord('C3 F4')
        >>> c3.setTie('start', None)
        >>> c3.getTie(c3.pitches[0])
        <music21.tie.Tie start>
        
        Less safe to match by string, but possible:
        

        Error:
        
        >>> c3.setTie('stop', 'G4')
        Traceback (most recent call last):
        ChordException: the given pitch is not in the Chord: G4

        '''
        if pitchTarget is None and len(self._notes) > 0: # if no pitch
            pitchTarget = self._notes[0].pitch
        elif common.isStr(pitchTarget):
            pitchTarget = pitch.Pitch(pitchTarget)
        if common.isStr(t):
            t = tie.Tie(t)
        else:
            pass # assume a tie object
        match = False
        for d in self._notes:
            if d.pitch is pitchTarget: # compare by obj id first
                d.tie = t
                match = True
                break
        if not match: # more loose comparison: by ==
            for d in self._notes:
                if d.pitch == pitchTarget:
                    d.tie = t
                    match = True
                    break
        if not match:
            raise ChordException(
                'the given pitch is not in the Chord: {0}'.format(pitchTarget))

    def setVolume(self, vol, pitchTarget=None):
        '''
        Set the :class:`~music21.volume.Volume` object of a specific pitch
        target. If no pitch target is given, the first pitch is used.
        '''
        # assign to first pitch by default
        if pitchTarget is None and len(self._notes) > 0: # if no pitches
            pitchTarget = self._notes[0].pitch
        elif common.isStr(pitchTarget):
            pitchTarget = pitch.Pitch(pitchTarget)
        match = False
        for d in self._notes:
            if d.pitch is pitchTarget or d.pitch == pitchTarget:
                vol.client = self
                d._setVolume(vol, setClient=False)
                match = True
                break
        if not match:
            raise ChordException('the given pitch is not in the Chord: %s' % pitchTarget)

    def sortAscending(self, inPlace=False):
        # TODO: Check context
        return self.sortDiatonicAscending(inPlace=inPlace)

    def sortChromaticAscending(self):
        '''
        Same as sortAscending but notes are sorted by midi number, so F## sorts above G-.
        '''
        newChord = copy.deepcopy(self)
        #tempChordNotes = newChord.pitches
        pitches = sorted(newChord.pitches, key=lambda x: x.ps)
        newChord.pitches = pitches
        return newChord

    def sortDiatonicAscending(self, inPlace=False):
        '''
        The notes are sorted by Scale degree and then by Offset (so F## sorts below G-).
        Notes that are the identical pitch retain their order

        After talking with Daniel Jackson, let's try to make the chord object as immutable
        as possible, so we return a new Chord object with the notes arranged from lowest to highest

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
        pitches = sorted(returnObj.pitches, key=lambda x: (x.diatonicNoteNum, x.ps))
        # must re-assign altered list, as a new list is created
        returnObj.pitches = pitches
        return returnObj

    def sortFrequencyAscending(self):
        '''
        Same as above, but uses a note's frequency to determine height; so that
        C# would be below D- in 1/4-comma meantone, equal in equal temperament,
        but below it in (most) just intonation types.
        '''
        newChord = copy.deepcopy(self)
        pitches = sorted(newChord.pitches, key=lambda x: x.frequency)
        newChord.pitches = pitches
        return newChord

    def transpose(self, value, inPlace=False):
        '''Transpose the Note by the user-provided value. If the value
        is an integer, the transposition is treated in half steps and
        enharmonics might be simplified (not done yet). If the value is a
        string, any Interval string specification can be provided.

        If inPlace is set to True (default = False) then the original
        chord is changed.  Otherwise a new Chord is returned.

        We take a three-note chord (G, A, C#) and transpose it up a minor
        third, getting the chord B-flat, C, E.

        >>> a = chord.Chord(['g4', 'a3', 'c#6'])
        >>> b = a.transpose('m3')
        >>> b
        <music21.chord.Chord B-4 C4 E6>

        Here we create the interval object first (rather than giving
        a string) and specify transposing down six semitones, instead
        of saying A-4.

        >>> aInterval = interval.Interval(-6)
        >>> b = a.transpose(aInterval)
        >>> b
        <music21.chord.Chord C#4 D#3 F##5>

        If `inPlace` is True then rather than returning a new chord, the
        chord itself is changed.

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
        # call transpose on component Notes
        for n in post._notes:
            n.transpose(intervalObj, inPlace=True)
#         for p in post.pitches:
#             # we are either operating on self or a copy; always use inPlace
#             p.transpose(intervalObj, inPlace=True)
#             #pitches.append(intervalObj.transposePitch(p))
        if not inPlace:
            return post
        else:
            return None

    ### PUBLIC PROPERTIES ###

    @property
    def chordTablesAddress(self):
        '''
        Return a three-element tuple that represents that raw data location for
        information on the set class interpretation of this Chord.

        The data format is a Forte set class cardinality, index number, and
        inversion status (where 0 is invariant, and -1 and 1 represent
        inverted or not, respectively).

        >>> c = chord.Chord(["C4", "E4", "G#4"])
        >>> c.chordTablesAddress
        (3, 12, 0)

        '''
        self._updateChordTablesAddress()
        return self._chordTablesAddress

    @property
    def color(self):
        '''
        Get or set the Chord color.

        >>> a = chord.Chord(['c4', 'e4', 'g4'])
        >>> a.duration.type = 'whole'
        >>> a.color = '#235409'
        >>> a.color
        '#235409'

        >>> a.editorial.color
        '#235409'

        >>> a.setColor('#ff0000', 'e4')
        >>> a.getColor('c4')
        '#235409'

        >>> for p in a.pitches: 
        ...    print(a.getColor(p))
        #235409
        #ff0000
        #235409

        '''
        if self._editorial is not None:
            return self.editorial.color
        else:
            return None

    @color.setter
    def color(self, expr):
        self.editorial.color = expr

    @property
    def commonName(self):
        '''
        Return the most common name associated with this Chord as a string.
        does not currently check enharmonic equivalents.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.commonName
        'minor triad'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.commonName
        'major triad'

        >>> c3 = chord.Chord(['c', 'd-', 'e', 'f#'])
        >>> c3.commonName
        'all-interval tetrachord'

        >>> c3 = chord.Chord([0, 1, 2, 3, 4, 9])
        >>> c3.commonName
        ''
        '''
        self._updateChordTablesAddress()
        ctn = chordTables.addressToCommonNames(self._chordTablesAddress)
        if ctn is None or len(ctn) == 0:
            return ''
        else:
            return ctn[0]

    @property
    def duration(self):
        '''Get and set the duration of this Chord as a Duration object.

        >>> c = chord.Chord(['a', 'c', 'e'])
        >>> c.duration
        <music21.duration.Duration 1.0>

        Durations can be overridden after the fact:

        >>> d = duration.Duration()
        >>> d.quarterLength = 2
        >>> c.duration = d
        >>> c.duration
        <music21.duration.Duration 2.0>

        >>> c.duration == d
        True

        >>> c.duration is d
        True

        '''
        if self._duration is None and len(self._notes) > 0:
            #pitchZeroDuration = self._notes[0]['pitch'].duration
            pitchZeroDuration = self._notes[0].duration
            self._duration = pitchZeroDuration
        return self._duration

    @duration.setter
    def duration(self, durationObj):
        '''Set a Duration object.        
        '''
        if hasattr(durationObj, "quarterLength"):
            self._duration = durationObj
        else:
            # need to permit Duration object assignment here
            raise ChordException('this must be a Duration object, not %s' % durationObj)

    @property
    def fifth(self):
        '''Shortcut for getChordStep(5):

        >>> cMaj1stInv = chord.Chord(['E3','C4','G5'])
        >>> cMaj1stInv.fifth
        <music21.pitch.Pitch G5>

        >>> cMaj1stInv.fifth.midi
        79

        '''
        return self.getChordStep(5)

    @property
    def forteClass(self):
        '''Return the Forte set class name as a string. This assumes a Tn
        formation, where inversion distinctions are represented.

        (synonym: forteClassTn)

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.forteClass
        '3-11A'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClass
        '3-11B'

        '''
        self._updateChordTablesAddress()
        return chordTables.addressToForteName(self._chordTablesAddress, 'tn')

    @property
    def forteClassNumber(self):
        '''
        Return the number of the Forte set class within the defined set group.
        That is, if the set is 3-11, this method returns 11.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.forteClassNumber
        11

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClassNumber
        11

        '''
        self._updateChordTablesAddress()
        return self._chordTablesAddress[1] # the second value

    @property
    def forteClassTn(self):
        '''
        A synonym for "forteClass"

        Return the Forte Tn set class name, where inversion distinctions are
        represented:

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.forteClass
        '3-11A'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClassTn
        '3-11B'

        '''
        return self.forteClass

    @property
    def forteClassTnI(self):
        '''
        Return the Forte TnI class name, where inversion distinctions are not
        represented.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.forteClassTnI
        '3-11'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClassTnI
        '3-11'

        '''
        self._updateChordTablesAddress()
        return chordTables.addressToForteName(self._chordTablesAddress, 'tni')

    @property
    def fullName(self):
        '''
        Return the most complete representation of this Note, providing
        duration and pitch information.

        >>> c = chord.Chord(["D","F#","A"])
        >>> c.fullName
        'Chord {D | F-sharp | A} Quarter'

        >>> chord.Chord(['d1', 'e4-', 'b3-'], quarterLength=2/3.).fullName
        'Chord {D in octave 1 | E-flat in octave 4 | B-flat in octave 3} Quarter Triplet (2/3 QL)'

        '''
        msg = []
        sub = []
        for p in self.pitches:
            sub.append('%s' % p.fullName)
        msg.append('Chord')
        msg.append(' {%s} ' % ' | '.join(sub))
        msg.append(self.duration.fullName)
        return ''.join(msg)

    @property
    def hasZRelation(self):
        '''
        Return True or False if the Chord has a Z-relation.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.hasZRelation
        False

        >>> c2 = chord.Chord(['c', 'c#', 'e', 'f#'])
        >>> c2.hasZRelation  # it is c, c#, e-, g
        True

        '''
        self._updateChordTablesAddress()
        post = chordTables.addressToZAddress(self._chordTablesAddress)
        #environLocal.printDebug(['got post', post])
        if post is not None:
            return True
        return False

    @property
    def intervalVector(self):
        '''
        Return the interval vector for this Chord as a list of integers.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.intervalVector
        [0, 0, 1, 1, 1, 0]

        >>> c2 = chord.Chord(['c', 'c#', 'e', 'f#'])
        >>> c2.intervalVector
        [1, 1, 1, 1, 1, 1]

        >>> c3 = chord.Chord(['c', 'c#', 'e-', 'g'])
        >>> c3.intervalVector
        [1, 1, 1, 1, 1, 1]

        '''
        self._updateChordTablesAddress()
        return list(chordTables.addressToIntervalVector(
               self._chordTablesAddress))

    @property
    def intervalVectorString(self):
        '''
        Return the interval vector as a string representation.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.intervalVectorString
        '<001110>'

        '''
        return self._formatVectorString(self.intervalVector)

    @property
    def isPrimeFormInversion(self):
        '''
        Return True or False if the Chord represents a set class inversion.

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

    @property
    def multisetCardinality(self):
        '''
        Return an integer representing the cardinality of the mutliset, or the
        number of pitch values.

        >>> c1 = chord.Chord(["D4", "A4", "F#5", "D6"])
        >>> c1.multisetCardinality
        4

        '''
        return len(self.pitchClasses)

    @property
    def normalForm(self):
        '''
        Return the normal form of the Chord represented as a list of integers:

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.normalForm
        [0, 3, 7]

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.normalForm
        [0, 4, 7]

        '''
        self._updateChordTablesAddress()
        return list(chordTables.addressToNormalForm(self._chordTablesAddress))

    @property
    def normalFormString(self):
        '''
        Return a string representation of the normal form of the Chord.

        >>> c1 = chord.Chord(['f#', 'e-', 'g'])
        >>> c1.normalFormString
        '<034>'

        '''
        return self._formatVectorString(self.normalForm)

    @property
    def orderedPitchClasses(self):
        '''
        Return an list of pitch class integers, ordered form lowest to highest.

        >>> c1 = chord.Chord(["D4", "A4", "F#5", "D6"])
        >>> c1.orderedPitchClasses
        [2, 6, 9]

        '''
        pcGroup = []
        for p in self.pitches:
            if p.pitchClass in pcGroup:
                continue
            pcGroup.append(p.pitchClass)
        pcGroup.sort()
        return pcGroup

    @property
    def orderedPitchClassesString(self):
        '''
        Return a string representation of the pitch class values.

        >>> c1 = chord.Chord(['f#', 'e-', 'g'])
        >>> c1.orderedPitchClassesString
        '<367>'

        >>> # redundancies are removed
        >>> c1 = chord.Chord(['f#', 'e-', 'e-', 'g'])
        >>> c1.orderedPitchClassesString
        '<367>'

        '''
        return self._formatVectorString(self.orderedPitchClasses)

    @property
    def pitchClassCardinality(self):
        '''
        Return a the cardinality of pitch classes, or the number of unique
        pitch classes, in the Chord:

        >>> c1 = chord.Chord(["D4", "A4", "F#5", "D6"])
        >>> c1.pitchClassCardinality
        3

        '''
        return len(self.orderedPitchClasses)

    @property
    def pitchClasses(self):
        '''
        Return a list of all pitch classes in the chord as integers. Not sorted

        >>> c1 = chord.Chord(["D4", "A4", "F#5", "D6"])
        >>> c1.pitchClasses
        [2, 9, 6, 2]

        '''
        pcGroup = []
        for p in self.pitches:
            pcGroup.append(p.pitchClass)
        return pcGroup

    @property
    def pitchNames(self):
        '''
        Return a list of Pitch names from each
        :class:`~music21.pitch.Pitch` object's
        :attr:`~music21.pitch.Pitch.name` attribute.

        >>> c = chord.Chord(['g#', 'd-'])
        >>> c.pitchNames
        ['G#', 'D-']

        >>> c.pitchNames = ['c2', 'g2']
        >>> c.pitchNames
        ['C', 'G']

        '''
        return [d.pitch.name for d in self._notes]

    @pitchNames.setter
    def pitchNames(self, value):
        if common.isListLike(value):
            if common.isStr(value[0]): # only checking first
                self._notes = [] # clear
                for name in value:
                    self._notes.append(note.Note(name))
            else:
                raise ChordException(
                    'must provide a list containing a Pitch, not: {0}'.format(value))
        else:
            raise ChordException('cannot set pitch name with provided object: {0}'.format(value))
        self._chordTablesAddressNeedsUpdating = True

    @property
    def pitchedCommonName(self):
        '''
        Return the common name of this Chord preceded by its root, if a root is
        available:

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
        return '%s-%s' % (root, nameStr)

    @property
    def pitches(self):
        '''
        Get or set a list of all Pitch objects in this Chord.

        >>> c = chord.Chord(["C4", "E4", "G#4"])
        >>> c.pitches
        (<music21.pitch.Pitch C4>, <music21.pitch.Pitch E4>, <music21.pitch.Pitch G#4>)

        >>> [p.midi for p in c.pitches]
        [60, 64, 68]

        >>> d = chord.Chord()
        >>> d.pitches = c.pitches
        >>> d.pitches
        (<music21.pitch.Pitch C4>, <music21.pitch.Pitch E4>, <music21.pitch.Pitch G#4>)

        >>> c = chord.Chord(['C4', 'A4', 'E5'])
        >>> c.bass()
        <music21.pitch.Pitch C4>

        >>> c.root()
        <music21.pitch.Pitch A4>

        >>> c.pitches = ['C#4', 'A#4', 'E#5']
        >>> c.bass()
        <music21.pitch.Pitch C#4>

        >>> c.root()
        <music21.pitch.Pitch A#4>

        TODO: presently, whenever pitches are accessed, it sets
        the _chordTablesAddressNeedsUpdating value to True
        this is b/c the pitches list can be accessed and appended to.
        A better way to do this needs to be found.
        '''
        self._chordTablesAddressNeedsUpdating = True
        pitches = tuple(component.pitch for component in self._notes)
        return pitches

    @pitches.setter
    def pitches(self, value):
        #if value != [d['pitch'] for d in self._notes]:
        if value != [d.pitch for d in self._notes]:
            self._chordTablesAddressNeedsUpdating = True
        self._notes = []
        self._root = None
        self._bass = None
        self._inversion = None
        # assume we have pitch objects here
        # TODO: individual ties are not being retained here
        for p in value:
            self._notes.append(note.Note(p))

    @property
    def primeForm(self):
        '''
        Return a representation of the Chord as a prime-form list of pitch
        class integers:

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.primeForm
        [0, 3, 7]

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.primeForm
        [0, 3, 7]

        '''
        self._updateChordTablesAddress()
        return list(chordTables.addressToPrimeForm(self._chordTablesAddress))

    @property
    def primeFormString(self):
        '''
        Return a representation of the Chord as a prime-form set class string.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.primeFormString
        '<037>'

        >>> c1 = chord.Chord(['c', 'e', 'g'])
        >>> c1.primeFormString
        '<037>'

        '''
        return self._formatVectorString(self.primeForm)

    @property
    def quality(self):
        '''
        Returns the quality of the underlying triad of a triad or
        seventh, either major, minor, diminished, augmented, or other:

        >>> a = chord.Chord(['a', 'c', 'e'])
        >>> a.quality
        'minor'

        Inversions don't matter, nor do added tones so long as a root can be
        found:

        >>> a = chord.Chord(['f', 'b', 'd', 'g'])
        >>> a.quality
        'major'

        >>> a = chord.Chord(['c', 'a-', 'e'])
        >>> a.quality
        'augmented'

        >>> a = chord.Chord(['c','c#','d'])
        >>> a.quality
        'other'

        Incomplete triads are returned as major or minor:

        >>> a = chord.Chord(['c','e-'])
        >>> a.quality
        'minor'

        >>> a = chord.Chord(['e-','g'])
        >>> a.quality
        'major'

        Major + Minor = ?? other

        >>> chord.Chord('C E- E G').quality
        'other'
        >>> chord.Chord('C E G- G').quality
        'other'
        >>> chord.Chord('C D E').quality # NB! Major 9th....
        'major'
        >>> chord.Chord('C E--').quality
        'other'
        '''
        third = self.semitonesFromChordStep(3)
        fifth = self.semitonesFromChordStep(5)
        #environLocal.printDebug(['third, fifth', third, fifth])
        if third is None:
            return "other"
        elif self.hasRepeatedChordStep(3):
            #environLocal.printDebug('self.hasRepeatedChordStep(3)', self.hasRepeatedChordStep(3))
            return "other"
        elif fifth is None:
            if third == 4:
                return "major"
            elif third == 3:
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

    @property
    def scaleDegrees(self):
        '''
        Returns a list of two-element tuples for each pitch in the chord where
        the first element of the tuple is the scale degree as an int and the
        second is an Accidental object that specifies the alteration from the
        scale degree (could be None if the note is not part of the scale).

        It is easiest to see the utility of this method using a chord subclass,
        :class:`music21.roman.RomanNumeral`, but it is also callable from this
        Chord object if the Chord has a Key or Scale context set for it.

        >>> k = key.Key('f#')  # 3-sharps minor
        >>> rn = roman.RomanNumeral('V', k)
        >>> rn.key
        <music21.key.Key of f# minor>

        >>> rn.pitches
        (<music21.pitch.Pitch C#5>, <music21.pitch.Pitch E#5>, <music21.pitch.Pitch G#5>)

        >>> rn.scaleDegrees
        [(5, None), (7, <accidental sharp>), (2, None)]

        >>> rn2 = roman.RomanNumeral('N6', k)
        >>> rn2.pitches
        (<music21.pitch.Pitch B4>, <music21.pitch.Pitch D5>, <music21.pitch.Pitch G5>)

        >>> rn2.scaleDegrees # N.B. -- natural form used for minor!
        [(4, None), (6, None), (2, <accidental flat>)]

        As mentioned above, the property can also get its scale from context if
        the chord is embedded in a Stream.  Let's create the same V in f#-minor
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
        # roman numerals have this built in as the key attribute
        if hasattr(self, 'key') and self.key is not None:
            # Key is a subclass of scale.DiatonicScale
            sc = self.key
        else:
            sc = self.getContextByClass(scale.Scale, sortByCreationTime=True)
            if sc is None:
                raise ChordException("Cannot find a Key or Scale context for this chord, so cannot find what scale degrees the pitches correspond to!")
#        if hasattr(sc, 'mode'):
#            mode = sc.mode       ### POSSIBLY USE to describe #7 etc. properly in minor -- not sure...
#        else:
#            mode = ""
        degrees = []
        for thisPitch in self.pitches:
            degree = sc.getScaleDegreeFromPitch(
                thisPitch,
                comparisonAttribute='step',
                direction=scale.DIRECTION_DESCENDING,
                )
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

    @property
    def seventh(self):
        '''shortcut for getChordStep(7)

        >>> bDim7_2ndInv = chord.Chord(['F2','A-3','B4','D5'])
        >>> bDim7_2ndInv.seventh
        <music21.pitch.Pitch A-3>

        Test whether this strange chord gets the B# not the C or something else:
        
        >>> c = chord.Chord(['C4','E4','G4','B#4'])
        >>> c.seventh
        <music21.pitch.Pitch B#4>

        '''
        return self.getChordStep(7)

    @property
    def third(self):
        '''Shortcut for getChordStep(3):

        >>> cMaj1stInv = chord.Chord(['E3','C4','G5'])
        >>> cMaj1stInv.third
        <music21.pitch.Pitch E3>

        >>> cMaj1stInv.third.octave
        3

        '''
        return self.getChordStep(3)

    @property
    def tie(self):
        '''
        Get or set a single tie based on all the ties in this Chord.

        This overloads the behavior of the tie attribute found in all
        NotRest classes.

        If setting a tie, tie is applied to all pitches.

        >>> c1 = chord.Chord(['c4','g4'])
        >>> tie1 = tie.Tie('start')
        >>> c1.tie = tie1
        >>> c1.tie
        <music21.tie.Tie start>

        >>> c1.getTie(c1.pitches[1])
        <music21.tie.Tie start>

        '''
        for d in self._notes:
            if d.tie is not None:
                return d.tie
        return None

    @tie.setter
    def tie(self, value):
        for d in self._notes:
            d.tie = value
            # set the same instance for each pitch
            #d['tie'] = value

    @property
    def volume(self):
        '''
        Get or set the :class:`~music21.volume.Volume` object for this
        Chord.

        When setting the .volume property, all pitches are treated as
        having the same Volume object.

        >>> c = chord.Chord(['g#', 'd-'])
        >>> c.volume
        <music21.volume.Volume realized=0.71>

        >>> c.volume = volume.Volume(velocity=64)
        >>> c.volume.velocityIsRelative = False
        >>> c.volume
        <music21.volume.Volume realized=0.5>

        >>> c.volume = [volume.Volume(velocity=96), volume.Volume(velocity=96)]
        >>> c.hasComponentVolumes()
        True

        >>> c._volume == None
        True

        >>> c.volume.velocity
        96

        >>> c.volume.velocityIsRelative = False
        >>> c.volume  # return a new volume that is an average
        <music21.volume.Volume realized=0.76>

        '''
        if not self.hasComponentVolumes() and self._volume is None:
            # create a single new Volume object for the chord
            return note.NotRest._getVolume(self, forceClient=self)
        elif self._volume is not None:
            # if we already have a Volume, use that
            return self._volume
        # if we have components and _volume is None, create a volume from
        # components
        elif self.hasComponentVolumes():
            vels = []
            for d in self._notes:
                vels.append(d._volume.velocity)
            # create new local object
            self._volume = volume.Volume(client=self)
            self._volume.velocity = int(round(sum(vels) / float(len(vels))))
            return self._volume
        else:
            raise ChordException('unmatched condition')

    @volume.setter
    def volume(self, expr):
        if isinstance(expr, volume.Volume):
            expr.client = self
            # remove any component volmes
            for c in self._notes:
                c._volume = None
            return note.NotRest._setVolume(self, expr, setClient=False)
        elif common.isNum(expr):
            vol = self._getVolume()
            if expr < 1: # assume a scalar
                vol.velocityScalar = expr
            else: # assume velocity
                vol.velocity = expr
        elif common.isListLike(expr): # assume an array of vol objects
            # if setting components, remove single velocity
            self._volume = None
            for i, c in enumerate(self._notes):
                v = expr[i % len(expr)]
                if common.isNum(v): # create a new Volume
                    if v < 1: # assume a scalar
                        v = volume.Volume(velocityScalar=v)
                    else: # assume velocity
                        v = volume.Volume(velocity=v)
                v.client = self
                c._setVolume(v, setClient=False)
        else:
            raise ChordException('unhandled setting expr: %s' % expr)

    #---------------------------------------------------------------------------
    # volume per pitch


    #---------------------------------------------------------------------------



def fromForteClass(notation):
    '''
    Return a Chord given a Forte-class notation. The Forte class can be
    specified as string (e.g., 3-11) or as a list of cardinality and number
    (e.g., [8,1]).

    If no match is available, None is returned.

    >>> chord.fromForteClass('3-11')
    <music21.chord.Chord C E- G>

    >>> chord.fromForteClass('3-11b')
    <music21.chord.Chord C E G>

    >>> chord.fromForteClass('3-11a')
    <music21.chord.Chord C E- G>

    >>> chord.fromForteClass((11,1))
    <music21.chord.Chord C C# D E- E F F# G G# A B->

    '''
    card = None
    num = 1
    inv = None
    if common.isStr(notation):
        if '-' in notation:
            parts = notation.split('-')
            card = int(parts[0])
            num, chars = common.getNumFromStr(parts[1])
            num = int(num)
            if 'a' in chars.lower():
                inv = 1
            elif 'b' in chars.lower():
                inv = -1
        else:
            raise ChordException('cannot extract set-class representation from string: %s' % notation)
    elif common.isListLike(notation):
        if len(notation) <= 3: # assume its a set-class representation
            if len(notation) > 0:
                card = notation[0]
            if len(notation) > 1:
                num = notation[1]
            if len(notation) > 2:
                inv = notation[2]
        else:
            raise ChordException('cannot handle specified notation: %s' % notation)
    else:
        raise ChordException('cannot handle specified notation: %s' % notation)

    prime = chordTables.addressToNormalForm([card, num, inv])
    return Chord(prime)


def fromIntervalVector(notation, getZRelation=False):
    '''
    Return one or more Chords given an interval vector.

    >>> chord.fromIntervalVector([0,0,0,0,0,1])
    <music21.chord.Chord C F#>

    >>> chord.fromIntervalVector((5,5,5,5,5,5)) == None
    True

    >>> chord.fromIntervalVector((1,1,1,1,1,1))
    <music21.chord.Chord C C# E F#>

    >>> chord.fromIntervalVector((1,1,1,1,1,1), getZRelation=True)
    <music21.chord.Chord C C# E- G>

    >>> chord.fromIntervalVector((1,1,1,1,1,1)).getZRelation()
    <music21.chord.Chord C C# E- G>

    '''
    addressList = None
    if common.isListLike(notation):
        if len(notation) == 6: #assume its an interval vector
            addressList = chordTables.intervalVectorToAddress(notation)
    if addressList is None:
        raise ChordException('cannot handle specified notation: %s' % notation)

    post = []
    for card, num in addressList:
        post.append(Chord(chordTables.addressToNormalForm([card, num])))
    # for now, return the first chord
    # z-related chords will have more than one
    if len(post) == 1:
        return post[0]
    elif len(post) == 2 and not getZRelation:
        return post[0]
    elif len(post) == 2 and getZRelation:
        return post[1]
    else:
        return None


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
        from music21 import stream
        s = stream.Stream()
        for i in range(30):
            chordRaw = []
            for i in range(random.choice([3, 4, 5, 6, 7, 8])):
                pc = random.choice(list(range(0, 12))) # py3
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

    def pitchOut(self, listIn):
        '''
        make tests for old-style pitch representation still work.
        '''
        out = "["
        for p in listIn:
            out += str(p) + ', '
        out = out[0:len(out)-2]
        out += "]"
        return out

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types
        for part in sys.modules[self.__module__].__dict__:
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
                i = copy.copy(obj)
                j = copy.deepcopy(obj)

        c1 = Chord(['C4', 'E-4', 'G4'])
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
        HighEFlat = note.Note()
        HighEFlat.name = 'E-'
        HighEFlat.octave = 5

        a = note.Note()
        b = note.Note()
        assert isinstance(a, note.Note)
        assert isinstance(a, note.Note)
        assert isinstance(b, note.Note)
        assert isinstance(b, note.Note)

        MiddleC = note.Note()
        MiddleC.name = 'C'
        MiddleC.octave = 4

        LowG = pitch.Pitch()
        LowG.name = 'G'
        LowG.octave = 3

        chord1 = Chord([HighEFlat, MiddleC, LowG])
        self.assertIsNot(chord1.getChordStep(3, testRoot=MiddleC), False)
        chord1.root(MiddleC)

        HighAFlat = note.Note()
        HighAFlat.name = "A-"
        HighAFlat.octave = 5

        chord2 = Chord([MiddleC, HighEFlat, LowG, HighAFlat])
        self.assertIsNot(chord1.third, None)
        self.assertIsNot(chord1.fifth, None)
        self.assertEqual(chord1.containsTriad(),  True)
        self.assertEqual(chord1.isTriad(),  True)
        self.assertEqual(chord2.containsTriad(),  True)
        self.assertEqual(chord2.isTriad(),  False)

        MiddleE = note.Note()
        MiddleE.name = 'E'
        MiddleE.octave = 4

        chord3 = Chord([MiddleC, HighEFlat, LowG, MiddleE])
        self.assertEqual(chord3.isTriad(),  False)

        MiddleB = note.Note()
        MiddleB.name = 'B'
        MiddleB.octave = 4

        chord4 = Chord([MiddleC, HighEFlat, LowG, MiddleB])
        self.assertEqual(chord4.containsSeventh(),  True)
        self.assertEqual(chord3.containsSeventh(),  False)
        self.assertEqual(chord4.isSeventh(),  True)

        chord5 = Chord([MiddleC, HighEFlat, LowG, MiddleE, MiddleB])
        self.assertEqual(chord5.isSeventh(),  False)

        chord6 = Chord([MiddleC, MiddleE, LowG])
        self.assertEqual(chord6.isMajorTriad(),  True)
        self.assertEqual(chord3.isMajorTriad(),  False)

        chord7 = Chord([MiddleC, HighEFlat, LowG])
        self.assertEqual(chord7.isMinorTriad(),  True)
        self.assertEqual(chord6.isMinorTriad(),  False)
        self.assertEqual(chord4.isMinorTriad(),  False)

        LowGFlat = note.Note()
        LowGFlat.name = 'G-'
        LowGFlat.octave = 3
        chord8 = Chord([MiddleC, HighEFlat, LowGFlat])

        self.assertEqual(chord8.isDiminishedTriad(),  True)
        self.assertEqual(chord7.isDiminishedTriad(),  False)

        MiddleBFlat = note.Note()
        MiddleBFlat.name = 'B-'
        MiddleBFlat.octave = 4

        chord9 = Chord([MiddleC, MiddleE, LowG, MiddleBFlat])

        self.assertEqual(chord9.isDominantSeventh(),  True)
        self.assertEqual(chord5.isDominantSeventh(),  False)

        MiddleBDoubleFlat = note.Note()
        MiddleBDoubleFlat.name = 'B--'
        MiddleBDoubleFlat.octave = 4

        chord10 = Chord([MiddleC, HighEFlat, LowGFlat, MiddleBDoubleFlat])
    #    chord10.root(MiddleC)

        self.assertEqual(chord10.isDiminishedSeventh(),  True)
        self.assertEqual(chord9.isDiminishedSeventh(),  False)

        chord11 = Chord([MiddleC])

        self.assertEqual(chord11.isTriad(),  False)
        self.assertEqual(chord11.isSeventh(),  False)

        MiddleCSharp = note.Note()
        MiddleCSharp.name = 'C#'
        MiddleCSharp.octave = 4

        chord12 = Chord([MiddleC, MiddleCSharp, LowG, MiddleE])
        chord12.root(MiddleC)

        self.assertEqual(chord12.isTriad(),  False)
        self.assertEqual(chord12.isDiminishedTriad(),  False)

        chord13 = Chord([MiddleC, MiddleE, LowG, LowGFlat])

        self.assertIsNot(chord13.getChordStep(5), None)
        self.assertEqual(chord13.hasRepeatedChordStep(5),  True)
        self.assertEqual(chord13.hasAnyRepeatedDiatonicNote(),  True)
        self.assertIs(chord13.getChordStep(2),  None)
        self.assertEqual(chord13.containsTriad(),  True)
        self.assertEqual(chord13.isTriad(),  False)

        LowGSharp = note.Note()
        LowGSharp.name = 'G#'
        LowGSharp.octave = 3

        chord14 = Chord([MiddleC, MiddleE, LowGSharp])

        self.assertEqual(chord14.isAugmentedTriad(),  True)
        self.assertEqual(chord6.isAugmentedTriad(),  False)

        chord15 = Chord([MiddleC, HighEFlat, LowGFlat, MiddleBFlat])

        self.assertEqual(chord15.isHalfDiminishedSeventh(),  True)
        self.assertEqual(chord12.isHalfDiminishedSeventh(),  False)
        self.assertEqual(chord15.bass().name,  'G-')
        self.assertEqual(chord15.inversion(),  2)
        self.assertEqual(chord15.inversionName(),  43)

        LowC = note.Note()
        LowC.name = 'C'
        LowC.octave = 3

        chord16 = Chord([LowC, MiddleC, HighEFlat])

        self.assertEqual(chord16.inversion(),  0)

        chord17 = Chord([LowC, MiddleC, HighEFlat])
        chord17.root(MiddleC)

        self.assertEqual(chord17.inversion(),  0)

        LowE = note.Note()
        LowE.name = 'E'
        LowE.octave = 3

        chord18 = Chord([MiddleC, LowE, LowGFlat])

        self.assertEqual(chord18.inversion(),  1)
        self.assertEqual(chord18.inversionName(), 6)

        LowBFlat = note.Note()
        LowBFlat.name = 'B-'
        LowBFlat.octave = 3


        chord19 = Chord([MiddleC, HighEFlat, LowBFlat])
        self.assertEqual(chord19.root().name, MiddleC.name)
        self.assertEqual(chord19.inversion(), 3)
        self.assertEqual(chord19.inversionName(), 42)
        #self.assertEqual(chord20.inversion(),  4 #intentionally raises error)

        chord20 = Chord([LowC, LowBFlat])
        chord20.root(LowBFlat)


        chord21 = Chord([MiddleC, HighEFlat, LowGFlat])
        self.assertEqual(chord21.root().name, 'C')

        MiddleF = note.Note()
        MiddleF.name = 'F'
        MiddleF.octave = 4

        LowA = note.Note()
        LowA.name = 'A'
        LowA.octave = 3

        chord22 = Chord([MiddleC, MiddleF, LowA])
        self.assertEqual(chord22.root().name, 'F')
        self.assertEqual(chord22.inversionName(), 6)

        chord23 = Chord([MiddleC, MiddleF, LowA, HighEFlat])
        self.assertEqual(chord23.root().name,  'F')

        HighC = note.Note()
        HighC.name = 'C'
        HighC.octave = 4

        HighE = note.Note()
        HighE.name = 'E'
        HighE.octave = 5

        chord24 = Chord([MiddleC])
        self.assertEqual(chord24.root().name, 'C')

        chord25 = Chord([MiddleC, HighE])
        self.assertEqual(chord25.root().name, 'C')

        MiddleG = note.Note()
        MiddleG.name = 'G'
        MiddleG.octave = 4

        chord26 = Chord([MiddleC, MiddleE, MiddleG])
        self.assertEqual(chord26.root().name, 'C')

        chord27 = Chord([MiddleC, MiddleE, MiddleG, MiddleBFlat])
        self.assertEqual(chord27.root().name, 'C')

        chord28 = Chord([LowE, LowBFlat, MiddleG, HighC])
        self.assertEqual(chord28.root().name, 'C')

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
        self.assertEqual(chord29.root().name, 'C')

        chord30 = Chord([MiddleC, MiddleE, MiddleG, MiddleBFlat, HighD, HighF])
        self.assertEqual(chord30.root().name, 'C')


        chord31 = Chord([MiddleC, MiddleE, MiddleG, MiddleBFlat, HighD, HighF, HighAFlat])
        # Used to raise an error; now should return middleC
        #self.assertRaises(ChordException, chord31.root)
        self.assertEqual(chord31.root().name, MiddleC.name)

        chord32 = Chord([MiddleC, MiddleE, MiddleG, MiddleB])
        self.assertEqual(chord32.bass().name, 'C')
        self.assertEqual(chord32.root().name, 'C')
        self.assertEqual(chord32.inversionName(), 7)

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

        self.assertEqual( chord33.isHalfDiminishedSeventh(), False )
        self.assertEqual(chord33.isDiminishedSeventh() ,  False)
        self.assertEqual(chord33.isFalseDiminishedSeventh(),  False)

        chord34 = Chord([MiddleC, MiddleFDbleFlat, MiddleFSharp, MiddleA])
        self.assertEqual(chord34.isFalseDiminishedSeventh(),  True)

        scrambledChord1 = Chord([HighAFlat, HighF, MiddleC, MiddleASharp, MiddleBDoubleFlat])
        unscrambledChord1 = scrambledChord1.sortAscending()
        self.assertEqual(unscrambledChord1.pitches[0].name,  "C")
        self.assertEqual(unscrambledChord1.pitches[1].name,  "A#")
        self.assertEqual(unscrambledChord1.pitches[2].name,  "B--")
        self.assertEqual(unscrambledChord1.pitches[3].name,  "F")
        self.assertEqual(unscrambledChord1.pitches[4].name,  "A-")

        unscrambledChord2 = scrambledChord1.sortChromaticAscending()
        self.assertEqual(unscrambledChord2.pitches[0].name,  "C")
        self.assertEqual(unscrambledChord2.pitches[1].name,  "B--")
        self.assertEqual(unscrambledChord2.pitches[2].name,  "A#")
        self.assertEqual(unscrambledChord2.pitches[3].name,  "F")
        self.assertEqual(unscrambledChord2.pitches[4].name,  "A-")

        unscrambledChord3 = scrambledChord1.sortFrequencyAscending()
        self.assertEqual(unscrambledChord3.pitches[0].name,  "C")
        self.assertEqual(unscrambledChord3.pitches[1].name,  "B--")
        self.assertEqual(unscrambledChord3.pitches[2].name,  "A#")
        self.assertEqual(unscrambledChord3.pitches[3].name,  "F")
        self.assertEqual(unscrambledChord3.pitches[4].name,  "A-")


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
        chord1 = Chord(["C#4", "E4", "G4"])
        self.assertTrue(chord1.isDiminishedTriad())
        self.assertFalse(chord1.isMajorTriad())
        # duration shold store a Duration object
        #self.assertIs(chord1.duration,  None)

    def testClosedPosition(self):
        chord1 = Chord(["C#4", "G5", "E6"])
        chord2 = chord1.closedPosition()
        self.assertEqual(repr(chord2), "<music21.chord.Chord C#4 E4 G4>")

    def testPostTonalChordsA(self):
        c1 = Chord([0, 1, 3, 6, 8, 9, 12])
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
        self.assertEqual(c1.areZRelations(Chord([0, 1, 4, 6, 7, 9])), True)
        self.assertEqual(c1.commonName, 'combinatorial RI (RI9)')

    def testPostTonalChordsB(self):
        c1 = Chord([1, 4, 7, 10])
        self.assertEqual(c1.commonName, 'diminished seventh chord')
        self.assertEqual(c1.pitchedCommonName, 'C#-diminished seventh chord')

    def testScaleDegreesA(self):
        from music21 import key
        from music21 import stream

        chord1 = Chord(["C#5", "E#5", "G#5"])
        st1 = stream.Stream()
        st1.append(key.Key('c#'))   # c-sharp minor
        st1.append(chord1)
        self.assertEqual(repr(chord1.scaleDegrees), "[(1, None), (3, <accidental sharp>), (5, None)]")

        st2 = stream.Stream()
        st2.append(key.Key('c'))    # c minor
        st2.append(chord1)          # same pitches as before gives different scaleDegrees
        sd2 = chord1.scaleDegrees
        self.assertEqual(repr(sd2), "[(1, <accidental sharp>), (3, <accidental double-sharp>), (5, <accidental sharp>)]")


        st3 = stream.Stream()
        st3.append(key.Key('C'))    # C major
        chord2 = Chord(["C4", "C#4", "D4", "E-4", "E4", "F4"])  # 1st 1/2 of chromatic
        st3.append(chord2)
        sd3 = chord2.scaleDegrees
        self.assertEqual(repr(sd3), '[(1, None), (1, <accidental sharp>), (2, None), (3, <accidental flat>), (3, None), (4, None)]')


    def testScaleDegreesB(self):
        from music21 import stream, key
        # trying to isolate problematic context searches
        chord1 = Chord(["C#5", "E#5", "G#5"])
        st1 = stream.Stream()
        st1.append(key.Key('c#'))   # c-sharp minor
        st1.append(chord1)
        self.assertEqual(chord1.activeSite, st1)
        self.assertEqual(str(chord1.scaleDegrees),
        "[(1, None), (3, <accidental sharp>), (5, None)]")

        st2 = stream.Stream()
        st2.append(key.Key('c'))    # c minor
        st2.append(chord1)# same pitches as before gives different scaleDegrees

        self.assertNotEqual(chord1.activeSite, st1)

        # test id
        self.assertEqual(chord1.activeSite, st2)
        # for some reason this test fails when test cases are run at the
        # module level, but not at the level of running the specific method
        # from the class
        #self.assertEqual(chord1.activeSite, st2)

        self.assertEqual(str(chord1.scaleDegrees),
        "[(1, <accidental sharp>), (3, <accidental double-sharp>), (5, <accidental sharp>)]")

    def testTiesA(self):
        # test creating independent ties for each Pitch
        from music21.musicxml import m21ToString

        c1 = Chord(['c', 'd', 'b'])
        # as this is a subclass of Note, we have a .tie attribute already
        # here, it is managed by a property
        self.assertEqual(c1.tie, None)
        # directly manipulate pitches
        t1 = tie.Tie()
        t2 = tie.Tie()
        c1._notes[0].tie = t1
        # now, the tie attribute returns the tie found on the first pitch
        self.assertEqual(c1.tie, t1)
        # try to set all ties for all pitches using the .tie attribute
        c1.tie = t2
        # must do id comparisons, as == comparisons are based on attributes
        self.assertEqual(id(c1.tie), id(t2))
        self.assertEqual(id(c1._notes[0].tie), id(t2))
        self.assertEqual(id(c1._notes[1].tie), id(t2))
        self.assertEqual(id(c1._notes[2].tie), id(t2))

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
        out = m21ToString.fromMusic21Object(s)
        out = out.replace(' ', '')
        out = out.replace('\n', '')
        #print out
        self.assertTrue(out.find('''<pitch><step>A</step><octave>4</octave></pitch><duration>15120</duration><tietype="start"/><type>quarter</type><dot/><stem>up</stem><notehead>normal</notehead><notations><tiedtype="start"/></notations>''') != -1, out)

    def testTiesB(self):
        from music21 import stream, scale
        sc = scale.WholeToneScale()
        s = stream.Stream()
        for i in range(7):
            tiePos = list(range(i + 1)) # py3 = list
            c = sc.getChord('c4', 'c5', quarterLength=1)
            for pos in tiePos:
                c.setTie(tie.Tie('start'), c.pitches[pos])
            s.append(c)
        #s.show()

    def testTiesC(self):
        c2 = Chord(['D4', 'D4'])
        secondD4 = c2.pitches[1]
        c2.setTie('start', secondD4)
        self.assertEqual(c2._notes[0].tie is None, True)
        self.assertEqual(c2._notes[1].tie.type, 'start')

    def testChordQuality(self):
        c1 = Chord(['c', 'e-'])
        self.assertEqual(c1.quality, 'minor')

    def testVolumePerPitchA(self):
        c = Chord(['c4', 'd-4', 'g4'])
        v1 = volume.Volume(velocity=111)
        v2 = volume.Volume(velocity=98)
        v3 = volume.Volume(velocity=73)
        c.setVolume(v1, 'c4')
        c.setVolume(v2, 'd-4')
        c.setVolume(v3, 'g4')
        self.assertEqual(c.getVolume('c4').velocity, 111)
        self.assertEqual(c.getVolume('d-4').velocity, 98)
        self.assertEqual(c.getVolume('g4').velocity, 73)
        self.assertEqual(c.getVolume('c4').client, c)
        self.assertEqual(c.getVolume('d-4').client, c)
        self.assertEqual(c.getVolume('g4').client, c)
        cCopy = copy.deepcopy(c)
        self.assertEqual(cCopy.getVolume('c4').velocity, 111)
        self.assertEqual(cCopy.getVolume('d-4').velocity, 98)
        self.assertEqual(cCopy.getVolume('g4').velocity, 73)
#         environLocal.printDebug(['in test', 'id(c)', id(c)])
#         environLocal.printDebug(['in test', "c.getVolume('g4').client", id(c.getVolume('g4').client)])
#         environLocal.printDebug(['in test', 'id(cCopy)', id(cCopy)])
#         environLocal.printDebug(['in test', "cCopy.getVolume('g4').client", id(cCopy.getVolume('g4').client)])
        self.assertEqual(cCopy.getVolume('c4').client, cCopy)
        self.assertEqual(cCopy.getVolume('d-4').client, cCopy)
        self.assertEqual(cCopy.getVolume('g4').client, cCopy)

    def testVolumePerPitchB(self):
        from music21 import stream
        s = stream.Stream()
        amps = [.1, .5, 1]
        for j in range(12):
            c = Chord(['c3', 'd-4', 'g5'])
            for i, sub in enumerate(c):
                sub.volume.velocityScalar = amps[i]
            s.append(c)
        match = []
        for c in s:
            for sub in c:
                match.append(sub.volume.velocity)
        self.assertEqual(match, [13, 64, 127, 13, 64, 127, 13, 64, 127, 13, 64,
            127, 13, 64, 127, 13, 64, 127, 13, 64, 127, 13, 64, 127, 13, 64,
            127, 13, 64, 127, 13, 64, 127, 13, 64, 127])

    def testVolumePerPitchC(self):
        import random
        from music21 import stream, tempo
        c = Chord(['f-2', 'a-2', 'c-3', 'f-3', 'g3', 'b-3', 'd-4', 'e-4'])
        c.duration.quarterLength = .5
        s = stream.Stream()
        s.insert(tempo.MetronomeMark(referent=2, number=50))
        amps = [.1, .2, .3, .4, .5, .6, .7, .8]
        for accent in [.5, .5, .5, .5, .5, .5, .5, .5, .5, 1, .5, 1,
                       .5, .5, .5, .5, .5, 1, .5, .5, 1, .5, .5, .5,
                        1, .5, .5, .5, .5, 1, .5, .5,
                        None, None, None, None,
                        None, None, None, None,
                        None, None, None, None,
                        None, None, None, None,
                        .5, .5, .5, .5, .5, 1, .5, 1, .5, .5, .5, .5,
                         .5, 1, .5, .5, .5, .5, .5, .5, .5, .5, .5, .5,
                        .5, .5, .5, .5, .5, .5, .5, .5,
                        .5, .5, .5, .5, .5, .5, .5, .5,
                        ]:
            cNew = copy.deepcopy(c)
            if accent is not None:
                cNew.volume.velocityScalar = accent
                self.assertEqual(cNew.hasComponentVolumes(), False)
            else:
                random.shuffle(amps)
                cNew.volume = [volume.Volume(velocityScalar=x) for x in amps]
                self.assertEqual(cNew.hasComponentVolumes(), True)
            s.append(cNew)

    def testVolumePerPitchD(self):
        c = Chord(['f-3', 'g3', 'b-3'])
        #set a single velocity
        c.volume.velocity = 121
        self.assertEqual(c.volume.velocity, 121)
        self.assertEqual(c.hasComponentVolumes(), False)
        # set individual velocities
        c.volume = [volume.Volume(velocity=x) for x in (30, 60, 90)]
        # components are set
        self.assertEqual([x.volume.velocity for x in c], [30, 60, 90])
        # hasComponentVolumes is True
        self.assertEqual(c.hasComponentVolumes(), True)
        # if we get a volume, the average is taken, and we get this velocity
        self.assertEqual(c.volume.velocity, 60)
        # still have components
        self.assertEqual(c.hasComponentVolumes(), True)
        self.assertEqual([x.volume.velocity for x in c], [30, 60, 90])
        # if we set the outer velocity of the volume, components are not
        # changed; now we have an out-of sync situation
        c.volume.velocity = 127
        self.assertEqual(c.volume.velocity, 127)
        self.assertEqual(c.hasComponentVolumes(), True)
        self.assertEqual([x.volume.velocity for x in c], [30, 60, 90])
        # if we set the volume property, then we drop the components
        c.volume = volume.Volume(velocity=20)
        self.assertEqual(c.volume.velocity, 20)
        self.assertEqual(c.hasComponentVolumes(), False)
        # if we can still set components
        c.volume = [volume.Volume(velocity=x) for x in (10, 20, 30)]
        self.assertEqual([x.volume.velocity for x in c], [10, 20, 30])
        self.assertEqual(c.hasComponentVolumes(), True)
        self.assertEqual(c._volume, None)

    def testGetItemA(self):
        c = Chord(['c4', 'd-4', 'g4'])
        self.assertEqual(str(c[0].pitch), 'C4')
        self.assertEqual(str(c[1].pitch), 'D-4')
        self.assertEqual(str(c[2].pitch), 'G4')
        self.assertEqual(str(c['0.pitch']), 'C4')
        self.assertEqual(str(c['1.pitch']), 'D-4')
        self.assertEqual(str(c['2.pitch']), 'G4')
        # cannot do this, as this provides raw access
        #self.assertEqual(str(c[0]['volume']), 'C4')
        self.assertEqual(str(c['0.volume']), '<music21.volume.Volume realized=0.71>')
        self.assertEqual(str(c['1.volume']), '<music21.volume.Volume realized=0.71>')
        self.assertEqual(str(c['1.volume']), '<music21.volume.Volume realized=0.71>')
        c['0.volume'].velocity = 20
        c['1.volume'].velocity = 80
        c['2.volume'].velocity = 120
        self.assertEqual(c['0.volume'].velocity, 20)
        self.assertEqual(c['1.volume'].velocity, 80)
        self.assertEqual(c['2.volume'].velocity, 120)
        self.assertEqual([x.volume.velocity for x in c], [20, 80, 120])
        cCopy = copy.deepcopy(c)
        self.assertEqual([x.volume.velocity for x in cCopy], [20, 80, 120])
        vals = [11, 22, 33]
        for i, x in enumerate(cCopy):
            x.volume.velocity = vals[i]
        self.assertEqual([x.volume.velocity for x in cCopy], [11, 22, 33])
        self.assertEqual([x.volume.velocity for x in c], [20, 80, 120])
        self.assertEqual([x.volume.client for x in cCopy], [cCopy, cCopy, cCopy])
        # TODO: not yet working
        #self.assertEqual([x.volume.client for x in c], [c, c, c])

    def testChordComponentsA(self):
        from music21 import stream
        c = Chord(['d2', 'e-1', 'b-6'])
        s = stream.Stream()
        for n in c:
            s.append(n)
        self.assertEqual(len(s.notes), 3)
        self.assertEqual(s.highestOffset, 2.0)
        self.assertEqual(str(s.pitches), '[<music21.pitch.Pitch D2>, <music21.pitch.Pitch E-1>, <music21.pitch.Pitch B-6>]')


#-------------------------------------------------------------------------------


_DOC_ORDER = [Chord]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

