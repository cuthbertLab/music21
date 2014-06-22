# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         timespanAnalysis.py
# Purpose:      Tools for grouping notes and chords into a searchable tree
#               organized by start and stop offsets
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013-14 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL, see license.txt
#------------------------------------------------------------------------------
'''
Tools for performing voice-leading analysis with timespans.
'''

import collections
import unittest

from music21 import base
from music21 import common
from music21 import chord
from music21 import environment
from music21 import key
from music21 import pitch

environLocal = environment.Environment("stream.timespanAnalysis")


#------------------------------------------------------------------------------


class Horizontality(collections.Sequence):
    r'''
    A horizontality of consecutive elementTimespan objects.
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_timespans',
        )

    ### INITIALIZER ###

    def __init__(self,
        timespans=None,
        ):
        assert isinstance(timespans, collections.Sequence)
        assert len(timespans)
        assert all(hasattr(x, 'startOffset') and hasattr(x, 'stopOffset')
            for x in timespans)
        self._timespans = tuple(timespans)

    ### SPECIAL METHODS ###

    def __getitem__(self, item):
        return self._timespans[item]

    def __len__(self):
        return len(self._timespans)

    def __repr__(self):
        pitch_strings = []
        for x in self:
            string = '({},)'.format(', '.join(
                y.nameWithOctave for y in x.pitches))
            pitch_strings.append(string)
        return '<{}: {}>'.format(
            type(self).__name__,
            ' '.join(pitch_strings),
            )

    ### PROPERTIES ###

    @property
    def hasPassingTone(self):
        r'''
        Is true if the horizontality contains a passing tone.
        '''
        if len(self) < 3:
            return False
        elif not all(len(x.pitches) for x in self):
            return False
        pitches = (
            self[0].pitches[0],
            self[1].pitches[0],
            self[2].pitches[0],
            )
        if pitches[0] < pitches[1] < pitches[2]:
            return True
        elif pitches[0] > pitches[1] > pitches[2]:
            return True
        return False

    @property
    def hasNeighborTone(self):
        r'''
        Is true if the horizontality contains a neighbor tone.
        '''
        if len(self) < 3:
            return False
        elif not all(len(x.pitches) for x in self):
            return False
        pitches = (
            self[0].pitches[0],
            self[1].pitches[0],
            self[2].pitches[0],
            )
        if pitches[0] == pitches[2]:
            if abs(pitches[1].ps - pitches[0].ps) < 3:
                return True
        return False

    @property
    def hasNoMotion(self):
        pitchSets = set()
        for x in self:
            pitchSets.add(tuple(x.pitches))
        if len(pitchSets) == 1:
            return True
        return False



#------------------------------------------------------------------------------


class Verticality(object):
    r'''
    A collection of information about elements that are sounding at a given
    offset or just finished at that offset or are continuing from before, etc..


    Create a timespan-stream from a score:

    ::

        >>> score = corpus.parse('bwv66.6')
        >>> tree = stream.timespans.streamToTimespanCollection(score)


    Find the verticality at offset 6.5, or beat 2.5 of measure 2 (there's a one
    beat pickup)

    ::

        >>> verticality = tree.getVerticalityAt(6.5)
        >>> verticality
        <Verticality 6.5 {E3 D4 G#4 B4}>

    The representation of a verticality gives the pitches from lowest to
    highest (in sounding notes).


    A verticality knows its startOffset, but because elements might end at
    different times, it doesn't know its stopOffset

    ::

        >>> verticality.startOffset
        6.5
        >>> verticality.stopOffset
        Traceback (most recent call last):
        AttributeError: 'Verticality' object has no attribute 'stopOffset'

    However, we can find when the next verticality starts by looking at the
    nextVerticality

    ::

        >>> verticality.nextVerticality
        <Verticality 7.0 {A2 C#4 E4 A4}>
        >>> verticality.nextVerticality.startOffset
        7.0

    Or more simply:

    ::

        >>> verticality.nextStartOffset
        7.0

    (There is also a previousVerticality, but not a previousStartOffset)

    What we just demonstrated is actually very powerful: a Verticality keeps a
    record of exactly where it is in the timespanCollection -- scores can be
    recreated with this information.

    Getting back to the task at hand, we can find all the elementTimespans (and
    from there the elements) that start at exactly 6.5.  There's one, it's a
    passing tone D in the tenor and it lastes from offset 6.5 to offset 7.0,
    with respect to the beginning of the score, not to the beginning of the
    measure.  That is to say, it's an eighth note

    ::

        >>> verticality.startTimespans
        (<ElementTimespan (6.5 to 7.0) <music21.note.Note D>>,)


    And we can get all the elementTimespans that were already sounding at the
    moment (that is to say, the non-passing tones):

    ::

        >>> verticality.overlapTimespans
        (<ElementTimespan (6.0 to 7.0) <music21.note.Note B>>,
         <ElementTimespan (6.0 to 7.0) <music21.note.Note G#>>,
         <ElementTimespan (6.0 to 7.0) <music21.note.Note E>>)

    And we can get all the things that stop right at this moment.  It's the E
    in the tenor preceding the passing tone D:

    ::

        >>> verticality.stopTimespans
        (<ElementTimespan (6.0 to 6.5) <music21.note.Note E>>,)

    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_timespanCollection',
        '_overlapTimespans',
        '_startTimespans',
        '_startOffset',
        '_stopTimespans',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        timespanCollection=None,
        overlapTimespans=None,
        startTimespans=None,
        startOffset=None,
        stopTimespans=None,
        ):
        from music21.stream import timespans
        prototype = (timespans.TimespanCollection, type(None))
        assert isinstance(timespanCollection, prototype)
        self._timespanCollection = timespanCollection
        self._startOffset = startOffset
        assert isinstance(startTimespans, tuple)
        assert isinstance(stopTimespans, (tuple, type(None)))
        assert isinstance(overlapTimespans, (tuple, type(None)))
        self._startTimespans = startTimespans
        self._stopTimespans = stopTimespans
        self._overlapTimespans = overlapTimespans

    ### SPECIAL METHODS ###

    def __repr__(self):
        sortedPitches = sorted(self.pitchSet)
        return '<{} {} {{{}}}>'.format(
            type(self).__name__,
            self.startOffset,
            ' '.join(x.nameWithOctave for x in sortedPitches)
            )

    ### PUBLIC PROPERTIES ###

    @property
    def bassTimespan(self):
        r'''
        Gets the bass timespan in this verticality.

        This is CURRENTLY the lowest PART not the lowest note necessarily.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> verticality
            <Verticality 1.0 {F#3 C#4 F#4 A4}>

        ::

            >>> verticality.bassTimespan
            <ElementTimespan (1.0 to 2.0) <music21.note.Note F#>>

        '''
        pitches = sorted(self.pitchSet)
        lowestPitch = pitches[0]
        timespans = self.startTimespans + self.overlapTimespans
        bassTimespans = []
        for timespan in timespans:
            pitches = timespan.pitches
            if lowestPitch in pitches:
                bassTimespans.append(timespan)
        if bassTimespans:
            bassTimespans.sort(
                key=lambda x: x.part.getInstrument().partId,
                reverse=True,
                )
            return bassTimespans[0]
        return None

    @property
    def beatStrength(self):
        r'''
        Gets the beat strength of a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> verticality.beatStrength
            1.0

        '''
        thisElementTimespan = self.startTimespans[0]
        if self.startOffset == 1.0:
            pass  # debugging; delete
        return thisElementTimespan.beatStrength

    @property
    def degreeOfOverlap(self):
        '''
        Counts the number of things sounding at this moment
        '''

        return len(self.startTimespans) + len(self.overlapTimespans)

    def toChord(self):
        '''
        creates a chord object from the verticality
        '''
        pitchSet = sorted(self.pitchSet)
        testChord = chord.Chord(pitchSet)
        return testChord

    @property
    def isConsonant(self):
        r'''
        Is true when the pitch set of a verticality is consonant.

        ::

                >>> score = corpus.parse('bwv66.6')
                >>> tree = stream.timespans.streamToTimespanCollection(score)
                >>> verticalities = list(tree.iterateVerticalities())
                >>> for verticality in verticalities[:10]:
                ...     print("%r %r" % (verticality, verticality.isConsonant))
                ...
                <Verticality 0.0 {A3 E4 C#5}> True
                <Verticality 0.5 {G#3 B3 E4 B4}> True
                <Verticality 1.0 {F#3 C#4 F#4 A4}> True
                <Verticality 2.0 {G#3 B3 E4 B4}> True
                <Verticality 3.0 {A3 E4 C#5}> True
                <Verticality 4.0 {G#3 B3 E4 E5}> True
                <Verticality 5.0 {A3 E4 C#5}> True
                <Verticality 5.5 {C#3 E4 A4 C#5}> True
                <Verticality 6.0 {E3 E4 G#4 B4}> True
                <Verticality 6.5 {E3 D4 G#4 B4}> False

        '''
        return self.toChord().isConsonant()

    @property
    def measureNumber(self):
        r'''
        Gets the measure number of the verticality's starting elements.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(7.0)
            >>> verticality.measureNumber
            2

        '''
        return self.startTimespans[0].measureNumber

    @property
    def nextStartOffset(self):
        r'''
        Gets the next start-offset in the verticality's offset-tree.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> verticality.nextStartOffset
            2.0

        '''
        tree = self._timespanCollection
        if tree is None:
            return None
        startOffset = tree.getStartOffsetAfter(self.startOffset)
        return startOffset

    @property
    def nextVerticality(self):
        r'''
        Gets the next verticality after a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> print(verticality)
            <Verticality 1.0 {F#3 C#4 F#4 A4}>

        ::

            >>> nextVerticality = verticality.nextVerticality
            >>> print(nextVerticality)
            <Verticality 2.0 {G#3 B3 E4 B4}>

        Verticality objects created by an offset-tree hold a reference back to
        that offset-tree. This means that they determine their next or previous
        verticality dynamically based on the state of the offset-tree only when
        asked. Because of this, it is safe to mutate the offset-tree by
        inserting or removing timespans while iterating over it.

        ::

            >>> tree.remove(nextVerticality.startTimespans)
            >>> verticality.nextVerticality
            <Verticality 3.0 {A3 E4 C#5}>

        '''
        tree = self._timespanCollection
        if tree is None:
            return None
        startOffset = tree.getStartOffsetAfter(self.startOffset)
        if startOffset is None:
            return None
        return tree.getVerticalityAt(startOffset)

    @property
    def overlapTimespans(self):
        r'''
        Gets timespans overlapping the start offset of a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(0.5)
            >>> verticality.overlapTimespans
            (<ElementTimespan (0.0 to 1.0) <music21.note.Note E>>,)

        '''
        return self._overlapTimespans

    @property
    def pitchSet(self):
        r'''
        Gets the pitch set of all elements in a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> for pitch in sorted(verticality.pitchSet):
            ...     pitch
            ...
            <music21.pitch.Pitch F#3>
            <music21.pitch.Pitch C#4>
            <music21.pitch.Pitch F#4>
            <music21.pitch.Pitch A4>

        '''
        pitchSet = set()
        for elementTimespan in self.startTimespans:
            element = elementTimespan.element
            if hasattr(element, 'pitches'):
                pitches = [x.nameWithOctave for x in element.pitches]
                pitchSet.update(pitches)
        for elementTimespan in self.overlapTimespans:
            element = elementTimespan.element
            if hasattr(element, 'pitches'):
                pitches = [x.nameWithOctave for x in element.pitches]
                pitchSet.update(pitches)
        pitchSet = set([pitch.Pitch(x) for x in pitchSet])
        return pitchSet

    @property
    def pitchClassSet(self):
        r'''
        Gets the pitch-class set of all elements in a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> for pitchClass in sorted(verticality.pitchClassSet):
            ...     pitchClass
            ...
            <music21.pitch.Pitch C#>
            <music21.pitch.Pitch F#>
            <music21.pitch.Pitch A>

        '''
        pitchClassSet = set()
        for currentPitch in self.pitchSet:
            pitchClass = pitch.Pitch(currentPitch.name)
            pitchClassSet.add(pitchClass)
        return pitchClassSet

    @property
    def previousVerticality(self):
        r'''
        Gets the previous verticality before a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> print(verticality)
            <Verticality 1.0 {F#3 C#4 F#4 A4}>

        ::

            >>> previousVerticality = verticality.previousVerticality
            >>> print(previousVerticality)
            <Verticality 0.5 {G#3 B3 E4 B4}>
            
        Continue it:
        
        ::
            >>> v = tree.getVerticalityAt(1.0)
            >>> while v is not None:
            ...     print(v)
            ...     v = v.previousVerticality
            <Verticality 1.0 {F#3 C#4 F#4 A4}>
            <Verticality 0.5 {G#3 B3 E4 B4}>
            <Verticality 0.0 {A3 E4 C#5}>

        Verticality objects created by an offset-tree hold a reference back to
        that offset-tree. This means that they determine their next or previous
        verticality dynamically based on the state of the offset-tree only when
        asked. Because of this, it is safe to mutate the offset-tree by
        inserting or removing timespans while iterating over it.

        ::

            >>> tree.remove(previousVerticality.startTimespans)
            >>> verticality.previousVerticality
            <Verticality 0.0 {A3 E4 C#5}>

        '''
        tree = self._timespanCollection
        if tree is None:
            return None
        startOffset = tree.getStartOffsetBefore(self.startOffset)
        if startOffset is None:
            return None
        return tree.getVerticalityAt(startOffset)

    @property
    def startOffset(self):
        r'''
        Gets the start offset of a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> verticality.startOffset
            1.0

        '''
        return self._startOffset

    @property
    def startTimespans(self):
        r'''
        Gets the timespans starting at a verticality's start offset.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> for timespan in verticality.startTimespans:
            ...     timespan
            ...
            <ElementTimespan (1.0 to 2.0) <music21.note.Note A>>
            <ElementTimespan (1.0 to 2.0) <music21.note.Note F#>>
            <ElementTimespan (1.0 to 2.0) <music21.note.Note C#>>
            <ElementTimespan (1.0 to 2.0) <music21.note.Note F#>>

        '''
        return self._startTimespans

    @property
    def stopTimespans(self):
        r'''
        Gets the timespans stopping at a verticality's start offset.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> for timespan in verticality.stopTimespans:
            ...     timespan
            ...
            <ElementTimespan (0.0 to 1.0) <music21.note.Note E>>
            <ElementTimespan (0.5 to 1.0) <music21.note.Note B>>
            <ElementTimespan (0.5 to 1.0) <music21.note.Note B>>
            <ElementTimespan (0.5 to 1.0) <music21.note.Note G#>>

        '''
        return self._stopTimespans

    @property
    def timespanCollection(self):
        return self._timespanCollection

    def getAllVoiceLeadingQuartets(self, includeRests = True, includeOblique = True, 
                                   includeNoMotion=False, returnObjects=True, partPairNumbers=None):
        '''
        >>> c = corpus.parse('luca/gloria').measures(1,8)
        >>> tsCol = stream.timespans.streamToTimespanCollection(c)
        >>> verticality22 = tsCol.getVerticalityAt(22.0)
        
        >>> from pprint import pprint as pp
        >>> for vlq in verticality22.getAllVoiceLeadingQuartets():
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note E> , v1n2=<music21.note.Note F>, v2n1=<music21.note.Note G>, v2n2=<music21.note.Note C>  
        <music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note E> , v1n2=<music21.note.Note F>, v2n1=<music21.note.Note A>, v2n2=<music21.note.Note A>  
        <music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note G> , v1n2=<music21.note.Note C>, v2n1=<music21.note.Note A>, v2n2=<music21.note.Note A>  

        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(includeRests = False):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note E> , v1n2=<music21.note.Note F>, v2n1=<music21.note.Note A>, v2n2=<music21.note.Note A>  

        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(includeOblique=False):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note E> , v1n2=<music21.note.Note F>, v2n1=<music21.note.Note G>, v2n2=<music21.note.Note C>  

        >>> verticality22.getAllVoiceLeadingQuartets(includeOblique=False, includeRests=False)
        []


        Raw output
        
        >>> for vlqRaw in verticality22.getAllVoiceLeadingQuartets(returnObjects=False):
        ...     pp(vlqRaw)
        ((<ElementTimespan (21.0 to 22.0) <music21.note.Note E>>,
          <ElementTimespan (22.0 to 23.0) <music21.note.Note F>>),
         (<ElementTimespan (19.5 to 21.0) <music21.note.Note G>>,
          <ElementTimespan (22.0 to 22.5) <music21.note.Note C>>))
        ((<ElementTimespan (21.0 to 22.0) <music21.note.Note E>>,
          <ElementTimespan (22.0 to 23.0) <music21.note.Note F>>),
         (<ElementTimespan (21.5 to 22.5) <music21.note.Note A>>,
          <ElementTimespan (21.5 to 22.5) <music21.note.Note A>>))
        ((<ElementTimespan (19.5 to 21.0) <music21.note.Note G>>,
          <ElementTimespan (22.0 to 22.5) <music21.note.Note C>>),
         (<ElementTimespan (21.5 to 22.5) <music21.note.Note A>>,
          <ElementTimespan (21.5 to 22.5) <music21.note.Note A>>))
          
        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(partPairNumbers=[(0,1)]):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note E> , v1n2=<music21.note.Note F>, v2n1=<music21.note.Note G>, v2n2=<music21.note.Note C>          
        
        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(partPairNumbers=[(0,2),(1,2)]):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note E> , v1n2=<music21.note.Note F>, v2n1=<music21.note.Note A>, v2n2=<music21.note.Note A>  
        <music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note G> , v1n2=<music21.note.Note C>, v2n1=<music21.note.Note A>, v2n2=<music21.note.Note A>          
        
        '''
        import itertools
        from music21.voiceLeading import VoiceLeadingQuartet
        pairedMotionList = self.getPairedMotion(includeRests=includeRests, includeOblique=includeOblique)
        allQuartets = itertools.combinations(pairedMotionList, 2)
        filteredList = []
        
        verticalityStreamParts = self.timespanCollection.source.parts
        
        
        for thisQuartet in allQuartets:
            if includeNoMotion is False:
                if (thisQuartet[0][0].pitches == thisQuartet[0][1].pitches and
                    thisQuartet[1][0].pitches == thisQuartet[1][1].pitches):
                    continue
                if partPairNumbers is not None:
                    isAppropriate = False
                    for pp in partPairNumbers:
                        thisQuartetTopPart = thisQuartet[0][0].part
                        thisQuartetBottomPart = thisQuartet[1][0].part
                        if (((verticalityStreamParts[pp[0]] == thisQuartetTopPart) or
                            (verticalityStreamParts[pp[0]] == thisQuartetBottomPart)) and 
                            ((verticalityStreamParts[pp[1]] == thisQuartetTopPart) or
                            (verticalityStreamParts[pp[1]] == thisQuartetBottomPart))  
                            ):
                            isAppropriate = True
                            break
                    if (isAppropriate is False):
                        continue
                
                
                if returnObjects is False:
                    filteredList.append(thisQuartet)
                else:
                    n11 = thisQuartet[0][0].element
                    n12 = thisQuartet[0][1].element
                    n21 = thisQuartet[1][0].element
                    n22 = thisQuartet[1][1].element
                    vlq = VoiceLeadingQuartet(n11, n12, n21, n22)
                    filteredList.append(vlq)
        
        return filteredList
        
        
        
    def getPairedMotion(self, includeRests=True, includeOblique=True):
        '''
        Get a list of two-element tuples that are in the same part [TODO: or containing stream??]
        and which move here.
        
        >>> c = corpus.parse('luca/gloria').measures(1,8)
        >>> tsCol = stream.timespans.streamToTimespanCollection(c)
        >>> verticality22 = tsCol.getVerticalityAt(22.0)
        >>> for pm in verticality22.getPairedMotion():
        ...     print(pm)
        (<ElementTimespan (21.0 to 22.0) <music21.note.Note E>>, <ElementTimespan (22.0 to 23.0) <music21.note.Note F>>)
        (<ElementTimespan (19.5 to 21.0) <music21.note.Note G>>, <ElementTimespan (22.0 to 22.5) <music21.note.Note C>>)
        (<ElementTimespan (21.5 to 22.5) <music21.note.Note A>>, <ElementTimespan (21.5 to 22.5) <music21.note.Note A>>)
        
        Note that the second one contains a one-beat rest at 21.0-22.0; so includeRests = False will
        get rid of that:
        
        >>> for pm in verticality22.getPairedMotion(includeRests=False):
        ...     print(pm)
        (<ElementTimespan (21.0 to 22.0) <music21.note.Note E>>, <ElementTimespan (22.0 to 23.0) <music21.note.Note F>>)
        (<ElementTimespan (21.5 to 22.5) <music21.note.Note A>>, <ElementTimespan (21.5 to 22.5) <music21.note.Note A>>)
        
        
        Oblique here means a pair that does not move (it could be called noMotion, because there's no motion
        here in a two-note pair, but we still call it includeOblique so it's consistent with
        getAllVoiceLeadingQuartets).
        
        >>> for pm in verticality22.getPairedMotion(includeOblique=False):
        ...     print(pm)
        (<ElementTimespan (21.0 to 22.0) <music21.note.Note E>>, <ElementTimespan (22.0 to 23.0) <music21.note.Note F>>)
        (<ElementTimespan (19.5 to 21.0) <music21.note.Note G>>, <ElementTimespan (22.0 to 22.5) <music21.note.Note C>>)

        >>> for pm in verticality22.getPairedMotion(includeOblique=False, includeRests=False):
        ...     print(pm)
        (<ElementTimespan (21.0 to 22.0) <music21.note.Note E>>, <ElementTimespan (22.0 to 23.0) <music21.note.Note F>>)
        '''
        stopTss = self.stopTimespans
        startTss = self.startTimespans
        overlapTss = self.overlapTimespans
        allPairedMotions = []
                
        for startingTs in startTss:
            previousTs = self._timespanCollection.findPreviousElementTimespanInSameStreamByClass(startingTs)
            if previousTs is None:
                continue  # first not in piece in this part...
            
            if includeRests is False:
                if previousTs not in stopTss:
                    continue
            if includeOblique is False and startingTs.pitches == previousTs.pitches:
                continue            
            tsTuple = (previousTs, startingTs)
            allPairedMotions.append(tsTuple)
        
        if includeOblique is True:
            for overlapTs in overlapTss:
                tsTuple = (overlapTs, overlapTs)
                allPairedMotions.append(tsTuple)
        
        return allPairedMotions
        
                
        


#------------------------------------------------------------------------------


class VerticalitySequence(collections.Sequence):
    r'''
    A segment of verticalities.
    '''

    ### INITIALIZER ###

    def __init__(self, verticalities):
        self._verticalities = tuple(verticalities)

    ### SPECIAL METHODS ###

    def __getitem__(self, item):
        return self._verticalities[item]

    def __len__(self):
        return len(self._verticalities)

    def __repr__(self):
        string = '<VerticalitySequence: [\n\t{}\n\t]>'.format(
            ',\n\t'.join(repr(x) for x in self))
        return string

    ### PUBLIC METHODS ###

    def unwrap(self):
        unwrapped = {}
        for timespan in self[0].overlapTimespans:
            if timespan.part not in unwrapped:
                unwrapped[timespan.part] = []
            unwrapped[timespan.part].append(timespan)
        for timespan in self[0].startTimespans:
            if timespan.part not in unwrapped:
                unwrapped[timespan.part] = []
            unwrapped[timespan.part].append(timespan)
        for verticality in self[1:]:
            for timespan in verticality.startTimespans:
                if timespan.part not in unwrapped:
                    unwrapped[timespan.part] = []
                unwrapped[timespan.part].append(timespan)
        for part, unused_timespans in unwrapped.items():
            horizontality = Horizontality(
                timespans=unwrapped[part],
                )
            unwrapped[part] = horizontality
        return unwrapped


#------------------------------------------------------------------------------


class VoiceLeadingQuartet(common.SlottedObject):

    ### CLASS VARIABLES ###

    __slots__ = (
        '_key_signature',
        '_voiceOneNoteOne',
        '_voiceOneNoteTwo',
        '_voiceTwoNoteOne',
        '_voiceTwoNoteTwo',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        voiceOneNoteOne=None,
        voiceOneNoteTwo=None,
        voiceTwoNoteOne=None,
        voiceTwoNoteTwo=None,
        key_signature=None,
        ):
        base.Music21Object.__init__(self)
        if key_signature is None:
            key_signature = key.Key('C')
        self._key_signature = key.Key(key_signature)
        self._voiceOneNoteOne = voiceOneNoteOne
        self._voiceOneNoteTwo = voiceOneNoteTwo
        self._voiceTwoNoteOne = voiceTwoNoteOne
        self._voiceTwoNoteTwo = voiceTwoNoteTwo

    ### PUBLIC METHODS ###

    def hasAntiParallelMotion(self):
        pass

    def hasContraryMotion(self):
        pass

    def hasHiddenFifth(self):
        pass

    def hasHiddenInterval(self, expr):
        pass

    def hasHiddenOctave(self):
        pass

    def hasImproperResolution(self):
        pass

    def hasInwardContraryMotion(self):
        pass

    def hasNoMotion(self):
        pass

    def hasObliqueMotion(self):
        pass

    def hasOutwardContraryMotion(self):
        pass

    def hasParallelFifth(self):
        pass

    def hasParallelInterval(self, expr):
        pass

    def hasParallelMotion(self):
        pass

    def hasParallelOctave(self):
        pass

    def hasParallelUnison(self):
        pass

    def hasParallelUnisonOrOctave(self):
        pass

    def hasSimilarMotion(self):
        pass

    ### PUBLIC PROPERTIES ###

    @property
    def key_signature(self):
        return self._key_signature

    @property
    def voiceOneNoteOne(self):
        return self._voiceOneNoteOne

    @property
    def voiceOneNoteTwo(self):
        return self._voiceOneNoteTwo

    @property
    def voiceTwoNoteOne(self):
        return self._voiceTwoNoteOne

    @property
    def voiceTwoNoteTwo(self):
        return self._voiceTwoNoteTwo


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------


_DOC_ORDER = (
    )


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
