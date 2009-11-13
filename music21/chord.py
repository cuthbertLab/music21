#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         chord.py
# Purpose:      Chord representation and utilities
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


 
import copy
import unittest

import music21
from music21 import interval

from music21.duration import Duration
#from music21.note import Note
from music21 import musicxml
from music21 import note

from music21.lily import LilyString
#from music21.pitch import Pitch
from music21 import pitch



#-------------------------------------------------------------------------------
class ChordException(Exception):
    pass





class Chord(note.GeneralNote):
    '''Class for dealing with chords
    
    A Chord is an object composed of Notes.
    
    Create chords by creating notes:
    C = note.Note(), C.name = 'C'
    E = note.Note(), E.name = 'E'
    G = note.Note(), G.name = 'G'
    And then create a chord with notes:    
    cmaj = Chord([C, E, G])
    
    Chord has the ability to determine the root of a chord, as well as the bass note of a chord.
    In addition, Chord is capable of determining what type of chord a particular chord is, whether
    it is a triad or a seventh, major or minor, etc, as well as what inversion the chord is in. 
    
    NOTE: For now, the examples used in documentation give chords made from notes that are not
    defined. In the future, it may be possible to define a chord without first creating notes,
    but for now note that notes that appear in chords are simply shorthand instead of creating notes
    for use in examples
    
    '''

    ### TODO -- not near future -- allow Chords to have Rests in them

    ### note.Note to self: in documentation, add examples of usage
    
    _bass = None
    _root = None
    _duration = None
    isChord = True
    isNote = False
    isRest = False

    def __init__(self, notes = [], **keywords):
        note.GeneralNote.__init__(self, **keywords)

        # inherit Duration object from GeneralNote
        # keep it here in case we have no notes
        #self.duration = None  # inefficient, since note.Note.__init__ set it
        #del(self.pitch)

        self.pitches = []

        # here, pitch and duration data is extracted from notes
        # if provided

        for thisNote in notes:
            if isinstance(thisNote, music21.pitch.Pitch):
                self.pitches.append(thisNote)
            elif isinstance(thisNote, music21.note.Note):
                self.pitches.append(thisNote.pitch)
            elif isinstance(thisNote, Chord):
                for thisPitch in thisNote.pitches:
                    self.pitches.append(thisPitch)
            elif isinstance(thisNote, basestring) or \
                isinstance(thisNote, int):
                self.pitches.append(music21.pitch.Pitch(thisNote))
            else:
                raise ChordException("Could not process pitch %s" % thisNote)


        if "duration" in keywords or "type" in keywords or \
            "quarterLength" in keywords: #dots dont cut it
            self.duration = Duration(**keywords)

        elif len(notes) > 0:
            for thisNote in notes:
                # get duration from first note
                # but should other notes have the same duration?
                if hasattr(thisNote, "duration") and thisNote.duration != None:
                    self.duration = notes[0].duration
                    break
        
    def _preDurationLily(self):
        '''
        Method to return all the lilypond information that appears before the 
        duration number.  Note that _getLily is the same as with notes but 
        not yet subclassed...
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

    def _getLily(self):
        '''
        The name of the note as it would appear in Lilypond format.
        '''
        allNames = ""
        baseName = self._preDurationLily()
        if hasattr(self.duration, "components") and len(
            self.duration.components) > 0:
            for i in range(0, len(self.duration.components)):
                thisDuration = self.duration.components[i]            
                allNames += baseName
                allNames += thisDuration.lily
                allNames += self.editorial.lilyAttached()
                if (i != len(self.duration.components) - 1):
                    allNames += "~"
                    allNames += " "
        else:
            allNames += baseName
            allNames += self.duration.lily
            
        if (self.tie is not None):
            if (self.tie.type != "stop"):
                allNames += "~"
        if (self.notations):
            for thisNotation in self.notations:
                if dir(thisNotation).count('lily') > 0:
                    allNames += " " + thisNotation.lily

        return LilyString(allNames)

    lily = property(_getLily)


    #---------------------------------------------------------------------------
    def numNotes(self):
        '''
    	Returns the number of notes in the chord
    	'''
        return len(self.pitches)

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
# 
#     def _setDuration(self, value):
# 
#     property(_getDuration, _setDuration)

    def _getMX(self):
        '''
        Returns a List of mxNotes
        Attributes of notes are merged from different locations: first from the 
        duration objects, then from the pitch objects. Finally, GeneralNote 
        attributes are added

        >>> a = Chord()
        >>> a.quarterLength = 2
        >>> b = pitch.Pitch('A-')
        >>> c = pitch.Pitch('D-')
        >>> d = pitch.Pitch('E-')
        >>> e = a.pitches = [b, c, d]
        >>> len(e)
        3
        >>> mxNoteList = a.mx
        >>> len(mxNoteList) # get three mxNotes
        3
        >>> mxNoteList[0].get('chord')
        False
        >>> mxNoteList[1].get('chord')
        True
        >>> mxNoteList[2].get('chord')
        True
        '''
        mxNoteList = []
        for mxNoteBase in self.duration.mx: # returns a list of mxNote objs
            # merge method returns a new object
            chordPos = 0
            for pitchObj in self.pitches:
                mxNote = mxNoteBase.deepcopy()
                #mxNote.pitch = None # clear before each iteration
                mxNote = mxNote.merge(pitchObj.mx)
                if chordPos > 0:
                    mxNote.set('chord', True)
                # get color from within .editorial using attribute
                mxNote.set('color', self.color)
                mxNoteList.append(mxNote)
                chordPos += 1
        return mxNoteList

    def _setMX(self, mxNoteList):
        '''Given an a list of mxNotes, fill the necessary parameters

        >>> a = musicxml.Note()
        >>> a.setDefaults()
        >>> b = musicxml.Note()
        >>> b.setDefaults()
        >>> b.set('chord', True)
        >>> m = musicxml.Measure()
        >>> m.setDefaults()
        >>> a.external['measure'] = m # assign measure for divisions ref
        >>> a.external['divisions'] = m.external['divisions']
        >>> b.external['measure'] = m # assign measure for divisions ref
        >>> b.external['divisions'] = m.external['divisions']
        >>> c = Chord()
        >>> c.mx = [a, b]
        >>> len(c.pitches)
        2
        '''

        # assume that first chord is the same duration for all parts
        self.duration.mx = mxNoteList[0]
        pitches = []
        for mxNote in mxNoteList:
            # extract pitch pbjects     
            p = pitch.Pitch()
            p.mx = mxNote # will extact pitch info form mxNote
            pitches.append(p)
        self.pitches = pitches

    mx = property(_getMX, _setMX)    



    #---------------------------------------------------------------------------
    # analytical routines

    def bass(self, newbass = 0):
        '''returns the bass note or sets it to note.

        Usually defined to the lowest note in the chord,
        but we want to be able to override this.  You might want an implied
        bass for instance...  v o9.
        
        example:
        >>> cmaj = Chord(['C', 'E', 'G'])
        >>> cmaj.bass() # returns C
        C
        '''
        if (newbass):
            self._bass = newbass
        elif (self._bass is None):
            self._bass = self.findBass()

        return self._bass

    def findBass(self):
        ''' Returns the lowest note in the chord
        The only time findBass should be called is by bass() when it is figuring out what 
        the bass note of the chord is.
        Generally call bass() instead
        
        example:
        >>> cmaj = Chord (['C4', 'E3', 'G4'])
        >>> cmaj.findBass() # returns E3
        E3
        '''
        
        lowest = None
        
        for thisPitch in self.pitches:
            if (lowest is None):
                lowest = thisPitch
            else:
                lowest = interval.getWrittenLowerNote(lowest, thisPitch)
            
        return lowest
    

    def root(self, newroot = 0):
        '''Returns or sets the Root of the chord.  if not set, will run findRoot (q.v.)
        
        example:
        >>> cmaj = Chord (['C', 'E', 'G'])
        >>> cmaj.root() # returns C
        C
        '''

        if (newroot):
            self._root = newroot
        elif (self._root is None):
            self._root = self.findRoot()

        return self._root

    def findRoot(self):
        ''' Looks for the root by finding the note with the most 3rds above it
        Generally use root() instead, since if a chord doesn't know its root, root() will
        run findRoot() automatically.
        
        example:
        >>> cmaj = Chord (['C', 'E', 'G'])
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
                if self.hasScaleX(n, testRoot): ##n>7 = bug
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

    def duration(self, newDur = 0):
        '''Duration of the chord can be defined here OR it should return the duration
        of the first note of the chord
        '''
        if (newDur):
            self._duration = newDur
        elif (self._duration is None and len(self.pitches) > 0):
            self._duration = self.pitches[0].duration
            
        return self._duration
    
    def checkDurationSanity(self):
        '''
		TO WRITE

        Checks to make sure all notes have the same duration
        Does not run automatically
        '''
        pass

    def hasThird(self, testRoot = None):
        '''Shortcut for hasScaleX(3)'''
        return self.hasScaleX(3, testRoot)

    def hasFifth(self, testRoot = None):
        '''Shortcut for hasScaleX(5)'''
        return self.hasScaleX(5, testRoot)

    def hasSeventh(self, testRoot = None):
        '''Shortcut for hasScaleX(7)'''
        return self.hasScaleX(7, testRoot)

    def hasScaleX(self, scaleDegree, testRoot = None):
        '''
        Each of these returns the number of semitones above the root
        that the third, fifth, etc., of the chord lies, if there exists
        one.  Or False if it does not exist.
        
        You can optionally specify a note.Note object to try as the root.  It does
        not change the Chord.root object.  We use these methods to figure out
        what the root of the triad is.

        Currently there is a bug that in the case of a triply diminished
        third (e.g., "c" => "e----"), this function will incorrectly claim
        no third exists.  Perhaps this be construed as a feature.

        In the case of chords such as C, E-, E, hasThird
        will return 3, not 4, nor a list object (3,4).  You probably do not
        want to be using tonal chord manipulation functions on chords such
        as these anyway.
        
        note.Note that in Chord, we're using "Scale" to mean a diatonic scale step.
        It will not tell you if a chord has a specific scale degree in another
        scale system.  That functionality might be added to scale.py someday.
        
        example:
        >>> cchord = Chord (['C', 'E', 'E-', 'G'])
        >>> cchord.hasScaleX(3) #
        4
        >>> cchord.hasScaleX(5) # will return 7
        7
        >>> cchord.hasScaleX(6) # will return False
        False
        '''
        
        if (testRoot is None):
            testRoot = self.root()
            if (testRoot is None):
                raise ChordException("Cannot run hasScaleX without a root")

        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(testRoot, thisPitch)
            if (thisInterval.diatonic.generic.mod7 == scaleDegree):
                return thisInterval.chromatic.semitones

        return False
    
    def hasSpecificX(self, scaleDegree, testRoot = None):
        '''Exactly like hasScaleX, except it returns the interval itself instead of the number
        of semitones.
        
        example:
        >>> cmaj = Chord (['C', 'E', 'G'])
        >>> cmaj.hasScaleX(3) #will return the interval between C and E
        4
        >>> cmaj.hasScaleX(5) #will return the interval between C and G
        7
        >>> cmaj.hasScaleX(6) #will return False
        False
        '''
        if (testRoot is None):
            testRoot = self.root()
            if (testRoot is None):
                raise ChordException("Cannot run hasSpecificX without a root")

        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(testRoot, thisPitch)
            if (thisInterval.diatonic.generic.mod7 == scaleDegree):
                return thisInterval

        return False

    def hasRepeatedScaleX(self, scaleDeg, testRoot = None):
        '''Returns True if scaleDeg above testRoot (or self.root()) has two
        or more different notes (such as E and E-) in it.  Otherwise
        returns false.
       
        example:
        >>> cchord = Chord (['C', 'E', 'E-', 'G'])
        >>> cchord.hasRepeatedScaleX(3) # returns true
        True
        '''
        if (testRoot is None):
            testRoot = self.root()
            if (testRoot is None):
                raise ChordException("Cannot run hasRepeatedScaleX without a root")

        first = self.hasSpecificX(scaleDeg)
        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(testRoot, thisPitch)
            if (thisInterval.diatonic.generic.mod7 == scaleDeg):
                if (thisInterval.chromatic.mod12 - first.chromatic.mod12 != 0):
                    return True
                
        return False

    def hasAnyRepeatedScale(self, testRoot = None):
        '''Returns True if for any scale degree there are two or more different notes (such
        as E and E-) in the chord. If there are no repeated scale degrees, return false.
        
        example:
        >>> cchord = Chord (['C', 'E', 'E-', 'G'])
        >>> other = Chord (['C', 'E', 'F-', 'G'])
        >>> cchord.hasAnyRepeatedScale() 
        True
        >>> other.hasAnyRepeatedScale() # returns false (chromatically identical notes of different scale degrees do not count.
        False
        '''
        for i in range(1,8): ## == 1 - 7 inclusive
            if (self.hasRepeatedScaleX(i, testRoot) == True):
                return True
        return False

    def containsTriad(self):
        '''returns True or False if there is no triad above the root.
        "Contains vs. Is": A dominant-seventh chord contains a triad.
        
        example:
        >>> cchord = Chord (['C', 'E', 'G'])
        >>> other = Chord (['C', 'D', 'E', 'F', 'G'])
        >>> cchord.containsTriad() #returns True
        True
        >>> other.containsTriad() #returns True
        True
        '''

        third = self.hasThird()
        fifth = self.hasFifth()

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
        >>> cchord = Chord (['C', 'E', 'G'])
        >>> other = Chord (['C', 'D', 'E', 'F', 'G'])
        >>> cchord.isTriad() # returns True   
        True
        >>> other.isTriad() 
        False
        '''
        third = self.hasThird()
        fifth = self.hasFifth()

        if (third is False or fifth is False):
            return False
        
        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(self.root(), thisPitch)
            if (thisInterval.diatonic.generic.mod7 != 1) and (thisInterval.diatonic.generic.mod7 != 3) and (thisInterval.diatonic.generic.mod7 != 5):
                return False
            if (self.hasAnyRepeatedScale() == True):
                return False
                
        return True

    def containsSeventh(self):
        ''' returns True if the chord contains at least one of each of Third, Fifth, and Seventh.
        raises an exception if the Root can't be determined
        
        example:
        >>> cchord = Chord (['C', 'E', 'G', 'B'])
        >>> other = Chord (['C', 'D', 'E', 'F', 'G', 'B'])
        >>> cchord.containsSeventh() # returns True
        True
         >>> other.containsSeventh() # returns True
         True
        '''

        third = self.hasThird()
        fifth = self.hasFifth()
        seventh = self.hasSeventh()

        if (third is False or fifth is False or seventh is False):
            return False
        else:
            return True
        

    def isSeventh(self):
        '''Returns True if chord contains at least one of each of Third, Fifth, and Seventh,
        and every note in the chord is a Third, Fifth, or Seventh, such that there are no 
        repeated scale degrees (ex: E and E-). Else return false.
        
        example:
        >>> cchord = Chord (['C', 'E', 'G', 'B'])
        >>> other = Chord (['C', 'D', 'E', 'F', 'G', 'B'])
        >>> cchord.isSeventh() # returns True
        True
         >>> other.isSeventh() # returns False
         False
        '''
        
        third = self.hasThird()
        fifth = self.hasFifth()
        seventh = self.hasSeventh()

        if (third is False or fifth is False or seventh is False):
            return False

        #unused??
        firstThird = self.hasSpecificX(3)
        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(self.root(), thisPitch)
            if (thisInterval.diatonic.generic.mod7 != 1) and (thisInterval.diatonic.generic.mod7 != 3) and (thisInterval.diatonic.generic.mod7 != 5) and (thisInterval.diatonic.generic.mod7 != 7):
                return False
            if self.hasAnyRepeatedScale():
                return False
                
        return True

    def isMajorTriad(self):
        '''Returns True if chord is a Major Triad, that is, if it contains only notes that are
        either in unison with the root, a major third above the root, or a perfect fifth above the 
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.
        
        example:
        >>> cchord = Chord (['C', 'E', 'G'])
        >>> other = Chord (['C', 'G'])
        >>> cchord.isMajorTriad() # returns True
        True
        >>> other.isMajorTriad() # returns False
        False
        '''
        third = self.hasSpecificX(3)
        fifth = self.hasSpecificX(5)
        if (third is False or fifth is False):
            return False
 
        ### TODO: rewrite so that [C,E+++,G---] does not return True

        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 4) and (thisInterval.chromatic.mod12 != 7):
                return False
        
        return True

    def isMinorTriad(self):
        '''Returns True if chord is a Minor Triad, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, or a perfect fifth above the 
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.
        
        example:
        >>> cchord = Chord (['C', 'E-', 'G'])
        >>> other = Chord (['C', 'E', 'G'])
        >>> cchord.isMinorTriad() # returns True
        True
        >>> other.isMinorTriad() # returns False
        False
        '''
        third = self.hasSpecificX(3)
        fifth = self.hasSpecificX(5)
        if (third is False or fifth is False):
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3) and (thisInterval.chromatic.mod12 != 7):
                return False
        
        return True

    def isDiminishedTriad(self):
        '''Returns True if chord is a Diminished Triad, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, or a diminished fifth above the 
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.
        
        example:
        >>> cchord = Chord (['C', 'E-', 'G-'])
        >>> other = Chord (['C', 'E-', 'F#'])

        >>> cchord.isDiminishedTriad() #returns True
        True
        >>> other.isDiminishedTriad() #returns False
        False
        '''

        third = self.hasSpecificX(3)
        fifth = self.hasSpecificX(5)
        
        if (third is False or fifth is False):
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(self.root(), thisPitch)
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
        
        Examples
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
        third = self.hasSpecificX(3)
        fifth = self.hasSpecificX(5)

        if (third is False or fifth is False):
            return False
                
        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 4) and (thisInterval.chromatic.mod12 != 8):
                return False
        
        return True

    def isDominantSeventh(self):
        '''Returns True if chord is a Dominant Seventh, that is, if it contains only notes that are
        either in unison with the root, a major third above the root, a perfect fifth, or a major seventh
        above the root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.
        '''
        
        third = self.hasSpecificX(3)
        fifth = self.hasSpecificX(5)
        seventh = self.hasSpecificX(7)
        
        if (third is False or fifth is False or seventh is False):
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 4) and (thisInterval.chromatic.mod12 != 7) and (thisInterval.chromatic.mod12 != 10):
                return False
        
        return True

    def isDiminishedSeventh(self):
        '''Returns True if chord is a Diminished Seventh, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, a diminished fifth, or a minor seventh
        above the root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.
        '''
        third = self.hasSpecificX(3)
        fifth = self.hasSpecificX(5)
        seventh = self.hasSpecificX(7)
        
        if (third is False or fifth is False or seventh is False):
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(self.root(), thisPitch)
            if (thisInterval.chromatic.mod12 != 0) and (thisInterval.chromatic.mod12 != 3) and (thisInterval.chromatic.mod12 != 6) and (thisInterval.chromatic.mod12 != 9):
                return False
        
        return True
    
    
    def isHalfDiminishedSeventh(self):
        '''Returns True if chord is a Half Diminished Seventh, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, a diminished fifth, or a major seventh
        above the root. Additionally, must contain at least one of each third, fifth, and seventh above the root.
        Chord must be spelled correctly. Otherwise returns false.

        >>> c1 = Chord(['C4','E-4','G-4','B-4'])
        >>> c1.isHalfDiminishedSeventh()
        True
        
        Incorrectly spelled chords are not considered half-diminished sevenths
        >>> c2 = Chord(['C4','E-4','G-4','A#4'])
        >>> c2.isHalfDiminishedSeventh()
        False
        
        Nor are incomplete chords
        >>> c3 = Chord(['C4', 'G-4','B-4'])
        >>> c3.isHalfDiminishedSeventh()
        False
        '''
        third = self.hasSpecificX(3)
        fifth = self.hasSpecificX(5)
        seventh = self.hasSpecificX(7)
        
        if (third is False or fifth is False or seventh is False):
            return False
        for thisPitch in self.pitches:
            thisInterval = interval.generateInterval(self.root(), thisPitch)
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
            thisInterval = interval.generateInterval(self.root(), thisPitch)
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
    
    
    def determineType(self):
        '''returns an abbreviation for the type of chord it is.
        Add option to add inversion name to abbreviation?

        TODO: determine permanent designation abbreviation for every 
        type of chord and inversion
        '''
        if (self.isTriad()):
            if (self.isMajorTriad()):
                return "Major Triad"
            elif (self.isMinorTriad()):
                return "Minor Triad"
            elif (self.isDiminishedTriad()):
                return "Diminished Triad"
            elif (self.isAugmentedTriad()):
                return "Augmented Triad"
            else:
                return "other Triad"
        elif (self.isSeventh()):
            if (self.isDominantSeventh()):
                return "Dominant Seventh"
            elif (self.isDiminishedSeventh()):
                return "Dimininshed Seventh"
            elif (self.isHalfDiminishedSeventh()):
                return "Half Diminished Seventh"
            elif (self.isFalseDiminishedSeventh()):
                return "False Diminished Seventh"
            else:
                return "other Seventh"
    
    
    def canBeDominantV(self):
        if (self.isMajorTriad() or self.isDominantSeventh()):
            return 1
        else: 
            return 0
        

    def canBeTonic(self):
        if (self.isMajorTriad() or self.isMinorTriad()):
            return 1
        else: 
            return 0

    def inversion(self):
        ''' returns an integer representing which standard inversion the chord is in. Chord
        does not have to be complete, but determines the inversion by looking at the relationship
        of the bass note to the root.
        '''
        
        bassNote = self.bass()
        
        bassToRoot = interval.generateInterval(bassNote, self.root()).generic.simpleDirected
        
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
        ''' Returns an integer representing the common abbreviation for the inversion the chord is in.
        If chord is not in a common inversion, returns None.
        '''
        try:
            inv = self.inversion()
        except ChordException:
            return None
        
        if self.isSeventh() or self.hasScaleX(7):
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
    
    def sortAscending(self):
        # TODO Check context
        return self.sortDiatonicAscending()
        
    def sortDiatonicAscending(self):
        '''
        After talking with Daniel Jackson, let's try to make the chord object as immutable
        as possible, so we return a new Chord object with the notes arranged from lowest to highest
        
        The notes are sorted by Scale degree and then by Offset (so F## sorts below G-).  
        Notes that are the identical pitch retain their order
        
        >>> cMajUnsorted = Chord(['E4', 'C4', 'G4'])
        >>> cMajSorted = cMajUnsorted.sortDiatonicAscending()
        >>> cMajSorted.pitches[0].name
        'C'
        '''

        newChord = self.copy()
        tempChordNotes = copy.copy(self.pitches)
        tempChordNotes.sort(cmp=lambda x,y: cmp(x.diatonicNoteNum, y.diatonicNoteNum) or \
                            cmp(x.ps, y.ps))
        newChord.pitches = tempChordNotes
        return newChord
#        tchord = self.deepcopy()
#        tchord.pitches = tempChordNotes
#        return tchord

    
    def sortChromaticAscending(self):
        '''
        Same as sortAscending but notes are sorted by midi number, so F## sorts above G-.
        '''
        newChord = self.copy()
        tempChordNotes = copy.copy(self.pitches)
        tempChordNotes.sort(cmp=lambda x,y: cmp(x.ps, y.ps))
        newChord.pitches = tempChordNotes
        newChord.pitches = tempChordNotes
        return newChord
    
    def sortFrequencyAscending(self):
        '''
        Same as above, but uses a note's frequency to determine height; so that
        C# would be below D- in 1/4-comma meantone, equal in equal temperament,
        but below it in (most) just intonation types.
        '''
        newChord = self.copy()
        tempChordNotes = copy.copy(self.pitches)
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


class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
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
    
        chord1 = Chord ([HighEFlat, MiddleC, LowG])
        assert chord1.hasScaleX(3, MiddleC) is not False
        chord1.root(MiddleC)
    
        HighAFlat = note.Note()
        HighAFlat.name = "A-"
        HighAFlat.octave = 5
        
        chord2 = Chord ([MiddleC, HighEFlat, LowG, HighAFlat])
        assert chord1.hasThird() is not False
        assert chord1.hasFifth() is not False
        assert chord1.containsTriad()  == True
        assert chord1.isTriad() == True
        assert chord2.containsTriad() == True
        assert chord2.isTriad() == False
        
        MiddleE = note.Note()
        MiddleE.name = 'E'
        MiddleE.octave = 4
    
        chord3 = Chord ([MiddleC, HighEFlat, LowG, MiddleE])
        assert chord3.isTriad() == False
        
        MiddleB = note.Note()
        MiddleB.name = 'B'
        MiddleB.octave = 4
        
        chord4 = Chord ([MiddleC, HighEFlat, LowG, MiddleB])
        assert chord4.containsSeventh() == True
        assert chord3.containsSeventh() == False
        assert chord4.isSeventh() == True
        
        chord5 = Chord ([MiddleC, HighEFlat, LowG, MiddleE, MiddleB])
        assert chord5.isSeventh() == False
        
        chord6 = Chord ([MiddleC, MiddleE, LowG])
        assert chord6.isMajorTriad() == True
        assert chord3.isMajorTriad() == False
        
        chord7 = Chord ([MiddleC, HighEFlat, LowG])
        assert chord7.isMinorTriad() == True
        assert chord6.isMinorTriad() == False
        assert chord4.isMinorTriad() == False
        
        LowGFlat = note.Note()
        LowGFlat.name = 'G-'
        LowGFlat.octave = 3
        chord8 = Chord ([MiddleC, HighEFlat, LowGFlat])
        
        assert chord8.isDiminishedTriad() == True
        assert chord7.isDiminishedTriad() == False
        
        MiddleBFlat = note.Note()
        MiddleBFlat.name = 'B-'
        MiddleBFlat.octave = 4
        
        chord9 = Chord ([MiddleC, MiddleE, LowG, MiddleBFlat])
        
        assert chord9.isDominantSeventh() == True
        assert chord5.isDominantSeventh() == False
        
        MiddleBDoubleFlat = note.Note()
        MiddleBDoubleFlat.name = 'B--'
        MiddleBDoubleFlat.octave = 4
        
        chord10 = Chord ([MiddleC, HighEFlat, LowGFlat, MiddleBDoubleFlat])
    #    chord10.root(MiddleC)
        
        assert chord10.isDiminishedSeventh() == True
        assert chord9.isDiminishedSeventh() == False
        
        chord11 = Chord ([MiddleC])
        
        assert chord11.isTriad() == False
        assert chord11.isSeventh() == False
        
        MiddleCSharp = note.Note()
        MiddleCSharp.name = 'C#'
        MiddleCSharp.octave = 4
        
        chord12 = Chord ([MiddleC, MiddleCSharp, LowG, MiddleE])
        chord12.root(MiddleC)
        
        assert chord12.isTriad() == False
        assert chord12.isDiminishedTriad() == False
        
        chord13 = Chord ([MiddleC, MiddleE, LowG, LowGFlat])
        
        assert chord13.hasScaleX(5) is not False
        assert chord13.hasRepeatedScaleX(5) == True
        assert chord13.hasAnyRepeatedScale() == True
        assert chord13.hasScaleX(2) == False
        assert chord13.containsTriad() == True
        assert chord13.isTriad() == False
        
        LowGSharp = note.Note()
        LowGSharp.name = 'G#'
        LowGSharp.octave = 3
        
        chord14 = Chord ([MiddleC, MiddleE, LowGSharp])
        
        assert chord14.isAugmentedTriad() == True
        assert chord6.isAugmentedTriad() == False
        
        chord15 = Chord ([MiddleC, HighEFlat, LowGFlat, MiddleBFlat])
        
        assert chord15.isHalfDiminishedSeventh() == True
        assert chord12.isHalfDiminishedSeventh() == False
        
        assert chord15.bass().name == 'G-'
        
        assert chord15.inversion() == 2
        assert chord15.inversionName() == 43
        
        LowC = note.Note()
        LowC.name = 'C'
        LowC.octave = 3
        
        chord16 = Chord ([LowC, MiddleC, HighEFlat])
        
        assert chord16.inversion() == 0
        
        chord17 = Chord ([LowC, MiddleC, HighEFlat])
        chord17.root(MiddleC)
        
        assert chord17.inversion() == 0
        
        LowE = note.Note()
        LowE.name = 'E'
        LowE.octave = 3
        
        chord18 = Chord ([MiddleC, LowE, LowGFlat])
        
        assert chord18.inversion() == 1
        assert chord18.inversionName() == 6
        
        LowBFlat = note.Note()
        LowBFlat.name = 'B-'
        LowBFlat.octave = 3
        
        chord19 = Chord ([MiddleC, HighEFlat, LowBFlat])
        chord20 = Chord ([LowC, LowBFlat])
        chord20.root(LowBFlat)
        
        assert chord19.inversion() == 3
        assert chord19.inversionName() == 42
        '''assert chord20.inversion() == 4 intentionally raises error'''
        
        chord21 = Chord ([MiddleC, HighEFlat, LowGFlat])
        assert chord21.root().name == 'C'
        
        MiddleF = note.Note()
        MiddleF.name = 'F'
        MiddleF.octave = 4
        
        LowA = note.Note()
        LowA.name = 'A'
        LowA.octave = 3    
        
        chord22 = Chord ([MiddleC, MiddleF, LowA])
        assert chord22.root().name == 'F'
        assert chord22.inversionName() == 6
        
        chord23 = Chord ([MiddleC, MiddleF, LowA, HighEFlat])
        assert chord23.root().name == 'F'
        
        HighC = note.Note()
        HighC.name = 'C'
        HighC.octave = 4
        
        HighE = note.Note()
        HighE.name = 'E'
        HighE.octave = 5
        
        chord24 = Chord ([MiddleC])
        assert chord24.root().name == 'C'
        
        chord25 = Chord ([MiddleC, HighE])
        assert chord25.root().name == 'C'
        
        MiddleG = note.Note()
        MiddleG.name = 'G'
        MiddleG.octave = 4
        
        chord26 = Chord ([MiddleC, MiddleE, MiddleG])
        assert chord26.root().name == 'C'
        
        chord27 = Chord ([MiddleC, MiddleE, MiddleG, MiddleBFlat])
        assert chord27.root().name == 'C'
        
        chord28 = Chord ([LowE, LowBFlat, MiddleG, HighC])
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
        
        chord29 = Chord ([MiddleC, MiddleE, MiddleG, MiddleBFlat, HighD])
        assert chord29.root().name == 'C'
        
        chord30 = Chord ([MiddleC, MiddleE, MiddleG, MiddleBFlat, HighD, HighF])
        assert chord30.root().name == 'C'
         
        
        '''Should raise error'''
        chord31 = Chord ([MiddleC, MiddleE, MiddleG, MiddleBFlat, HighD, HighF, HighAFlat])
        
        self.assertRaises(ChordException, chord31.root)
        
        chord32 = Chord ([MiddleC, MiddleE, MiddleG, MiddleB])
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
        
        chord33 = Chord ([MiddleC, MiddleE, MiddleG, MiddleFDbleFlat, MiddleASharp, MiddleBDoubleFlat, MiddleFSharp])
        chord33.root(MiddleC)
        
        assert chord33.isHalfDiminishedSeventh() == False
        assert chord33.isDiminishedSeventh() == False
        assert chord33.isFalseDiminishedSeventh() == False
        
        chord34 = Chord ([MiddleC, MiddleFDbleFlat, MiddleFSharp, MiddleA])
        assert chord34.isFalseDiminishedSeventh() == True
                
        scrambledChord1 = Chord ([HighAFlat, HighF, MiddleC, MiddleASharp, MiddleBDoubleFlat])
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

if __name__ == '__main__':
    music21.mainTest(Test)