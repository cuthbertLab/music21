# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         tree/verticality.py
# Purpose:      Object for dealing with vertical simultaneities in a 
#               fast way w/o Chord's overhead
#
# Authors:      Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-16 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Object for dealing with vertical simultaneities in a fast way w/o Chord's overhead.
'''
import collections
import unittest

from music21 import note
from music21 import tie
from music21 import chord
from music21 import environment
from music21 import exceptions21
#from music21 import key
from music21 import pitch

environLocal = environment.Environment("tree.verticality")

class VerticalityException(exceptions21.TreeException):
    pass

class Verticality(object):
    r'''
    A collection of information about elements that are sounding at a given
    offset or just finished at that offset or are continuing from before, etc..


    Create a timespan-stream from a score:

    >>> score = corpus.parse('bwv66.6')
    >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
    ...        classList=(note.Note, chord.Chord))


    Find the verticality at offset 6.5, or beat 2.5 of measure 2 (there's a one
    beat pickup)

    >>> verticality = scoreTree.getVerticalityAt(6.5)
    >>> verticality
    <Verticality 6.5 {E3 D4 G#4 B4}>


    The representation of a verticality gives the pitches from lowest to
    highest (in sounding notes).


    A verticality knows its offset, but because elements might end at
    different times, it doesn't know its endTime

    >>> verticality.offset
    6.5
    >>> verticality.endTime
    Traceback (most recent call last):
    AttributeError: 'Verticality' object has no attribute 'endTime'


    However, we can find when the next verticality starts by looking at the
    nextVerticality

    >>> nv = verticality.nextVerticality
    >>> nv
    <Verticality 7.0 {A2 C#4 E4 A4}>
    >>> nv.offset
    7.0

    Or more simply:

    >>> verticality.nextStartOffset
    7.0

    (There is also a previousVerticality, but not a previousStartOffset)

    What we just demonstrated is actually very powerful: a Verticality keeps a
    record of exactly where it is in the timespanTree -- scores can be
    recreated with this information.

    Getting back to the task at hand, we can find all the PitchedTimespans (and
    from there the elements) that start at exactly 6.5.  There's one, it's a
    passing tone D in the tenor and it lastes from offset 6.5 to offset 7.0,
    with respect to the beginning of the score, not to the beginning of the
    measure.  That is to say, it's an eighth note

    >>> verticality.startTimespans
    (<PitchedTimespan (6.5 to 7.0) <music21.note.Note D>>,)

    And we can get all the PitchedTimespans that were already sounding at the
    moment (that is to say, the non-passing tones):

    >>> verticality.overlapTimespans
    (<PitchedTimespan (6.0 to 7.0) <music21.note.Note B>>,
     <PitchedTimespan (6.0 to 7.0) <music21.note.Note G#>>,
     <PitchedTimespan (6.0 to 7.0) <music21.note.Note E>>)

    And we can get all the things that stop right at this moment.  It's the E
    in the tenor preceding the passing tone D:

    >>> verticality.stopTimespans
    (<PitchedTimespan (6.0 to 6.5) <music21.note.Note E>>,)
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        'timespanTree',
        'overlapTimespans',
        'startTimespans',
        'offset',
        'stopTimespans',
        )

    _DOC_ATTR = {
        'timespanTree': r''' 
            Returns the timespanTree initially set.
            ''',
        'overlapTimespans': r'''
            Gets timespans overlapping the start offset of a verticality.

            >>> score = corpus.parse('bwv66.6')
            >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
            ...            classList=(note.Note, chord.Chord))
            >>> verticality = scoreTree.getVerticalityAt(0.5)
            >>> verticality
            <Verticality 0.5 {G#3 B3 E4 B4}>
            >>> verticality.overlapTimespans
            (<PitchedTimespan (0.0 to 1.0) <music21.note.Note E>>,)        
            ''',
        'startTimespans': r'''
            Gets the timespans starting at a verticality's start offset.

            >>> score = corpus.parse('bwv66.6')
            >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
            ...            classList=(note.Note, chord.Chord))
            >>> verticality = scoreTree.getVerticalityAt(1.0)
            >>> verticality
            <Verticality 1.0 {F#3 C#4 F#4 A4}>
            >>> for timespan in verticality.startTimespans:
            ...     timespan
            ...
            <PitchedTimespan (1.0 to 2.0) <music21.note.Note A>>
            <PitchedTimespan (1.0 to 2.0) <music21.note.Note F#>>
            <PitchedTimespan (1.0 to 2.0) <music21.note.Note C#>>
            <PitchedTimespan (1.0 to 2.0) <music21.note.Note F#>>        
            ''',
        'offset': r'''
            Gets the start offset of a verticality.

            >>> score = corpus.parse('bwv66.6')
            >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
            ...            classList=(note.Note, chord.Chord))
            >>> verticality = scoreTree.getVerticalityAt(1.0)
            >>> verticality
            <Verticality 1.0 {F#3 C#4 F#4 A4}>
            >>> verticality.offset
            1.0    
            ''',
        'stopTimespans': r'''
            Gets the timespans stopping at a verticality's start offset.

            >>> score = corpus.parse('bwv66.6')
            >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
            ...                classList=(note.Note, chord.Chord))
            >>> verticality = scoreTree.getVerticalityAt(1.0)
            >>> verticality
            <Verticality 1.0 {F#3 C#4 F#4 A4}>

            Note that none of the elements in the stopTimespans are listed in 
            the repr for the Verticality

            >>> for timespan in verticality.stopTimespans:
            ...     timespan
            ...
            <PitchedTimespan (0.0 to 1.0) <music21.note.Note E>>
            <PitchedTimespan (0.5 to 1.0) <music21.note.Note B>>
            <PitchedTimespan (0.5 to 1.0) <music21.note.Note B>>
            <PitchedTimespan (0.5 to 1.0) <music21.note.Note G#>>
            ''', 
    }

    ### INITIALIZER ###

    def __init__(
        self,
        offset=None,
        overlapTimespans=None,
        startTimespans=None,
        stopTimespans=None,
        timespanTree=None,
        ):
        from music21.tree import trees
        prototype = (trees.OffsetTree, type(None))
        if not isinstance(timespanTree, prototype):
            raise VerticalityException(
                "timespanTree %r is not a OffsetTree or None" % (timespanTree,))
        
        self.timespanTree = timespanTree
        self.offset = offset
        
        if not isinstance(startTimespans, tuple):
            raise VerticalityException("startTimespans must be a tuple, not %r" % startTimespans)
        if not isinstance(stopTimespans, (tuple, type(None))):
            raise VerticalityException(
                    "stopTimespans must be a tuple or None, not %r" % stopTimespans)
        if not isinstance(overlapTimespans, (tuple, type(None))):
            raise VerticalityException(
                    "overlapTimespans must be a tuple or None, not %r" % overlapTimespans)
        
        self.startTimespans = startTimespans
        self.stopTimespans = stopTimespans
        self.overlapTimespans = overlapTimespans

    ### SPECIAL METHODS ###

    def __repr__(self):
        sortedPitches = sorted(self.pitchSet)
        return '<{} {} {{{}}}>'.format(
            type(self).__name__,
            self.offset,
            ' '.join(x.nameWithOctave for x in sortedPitches)
            )

    ### PUBLIC PROPERTIES ###

    @property
    def bassTimespan(self):
        r'''
        Gets the bass timespan in this verticality.

        This is CURRENTLY the lowest PART not the lowest note necessarily.
        TODO: Fix this!

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> verticality
        <Verticality 1.0 {F#3 C#4 F#4 A4}>

        >>> verticality.bassTimespan
        <PitchedTimespan (1.0 to 2.0) <music21.note.Note F#>>
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

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> verticality.beatStrength
        1.0
        
        
        Note that it will return None if there are no startTimespans at this point:
        
        >>> verticality = scoreTree.getVerticalityAt(1.25)
        >>> verticality
        <Verticality 1.25 {F#3 C#4 F#4 A4}>
        >>> verticality.startTimespans
        ()
        >>> verticality.beatStrength is None
        True
        '''
        try:
            thisPitchedTimespan = self.startTimespans[0]
        except IndexError:
            return None        
        return thisPitchedTimespan.element.beatStrength


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

        TODO: remove, and use toChord.isConsonant() instead.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticalities = list(scoreTree.iterateVerticalities())
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

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(7.0)
        >>> verticality.measureNumber
        2
        '''
        return self.startTimespans[0].measureNumber

    @property
    def nextStartOffset(self):
        r'''
        Gets the next start-offset in the verticality's offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> verticality.nextStartOffset
        2.0
        
        If a verticality has no tree attached, then it cannot be 
        
        '''
        tree = self.timespanTree
        if tree is None:
            return None
        offset = tree.getPositionAfter(self.offset)
        return offset

    @property
    def nextVerticality(self):
        r'''
        Gets the next verticality after a verticality.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> print(verticality)
        <Verticality 1.0 {F#3 C#4 F#4 A4}>

        >>> nextVerticality = verticality.nextVerticality
        >>> print(nextVerticality)
        <Verticality 2.0 {G#3 B3 E4 B4}>

        Verticality objects created by an offset-tree hold a reference back to
        that offset-tree. This means that they determine their next or previous
        verticality dynamically based on the state of the offset-tree only when
        asked. Because of this, it is safe to mutate the offset-tree by
        inserting or removing timespans while iterating over it.

        >>> scoreTree.removeTimespanList(nextVerticality.startTimespans)
        >>> verticality.nextVerticality
        <Verticality 3.0 {A3 E4 C#5}>
        '''
        tree = self.timespanTree
        if tree is None:
            return None
        offset = tree.getPositionAfter(self.offset)
        if offset is None:
            return None
        return tree.getVerticalityAt(offset)

    @property
    def pitchSet(self):
        r'''
        Gets the pitch set of all elements in a verticality.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> for pitch in sorted(verticality.pitchSet):
        ...     pitch
        ...
        <music21.pitch.Pitch F#3>
        <music21.pitch.Pitch C#4>
        <music21.pitch.Pitch F#4>
        <music21.pitch.Pitch A4>
        '''
        pitchSet = set()
        for timespan in self.startTimespans:
            if hasattr(timespan, 'element'):
                element = timespan.element
            else:
                element = timespan

            if 'music21.key.Key' not in element.classSet and hasattr(element, 'pitches'):
                pitches = [x.nameWithOctave for x in element.pitches]
                pitchSet.update(pitches)
        for timespan in self.overlapTimespans:
            if hasattr(timespan, 'element'):
                element = timespan.element
            else:
                element = timespan

            if 'music21.key.Key' not in element.classSet and hasattr(element, 'pitches'):
                pitches = [x.nameWithOctave for x in element.pitches]
                pitchSet.update(pitches)
        pitchSet = set([pitch.Pitch(x) for x in pitchSet])
        return pitchSet

    @property
    def pitchClassSet(self):
        r'''
        Gets the pitch-class set of all elements in a verticality.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(1.0)
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

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> print(verticality)
        <Verticality 1.0 {F#3 C#4 F#4 A4}>

        >>> previousVerticality = verticality.previousVerticality
        >>> print(previousVerticality)
        <Verticality 0.5 {G#3 B3 E4 B4}>
            
        Continue it:
        
        >>> v = scoreTree.getVerticalityAt(1.0)
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

        >>> scoreTree.removeTimespanList(previousVerticality.startTimespans)
        >>> verticality.previousVerticality
        <Verticality 0.0 {A3 E4 C#5}>
        '''
        tree = self.timespanTree
        if tree is None:
            return None
        offset = tree.getPositionBefore(self.offset)
        if offset is None:
            return None
        return tree.getVerticalityAt(offset)



    ######### makeElement
    
    def makeElement(self, quarterLength=1.0):
        r'''
        Makes a Chord or Rest from this verticality and quarterLength.
        
        >>> score = tree.makeExampleScore()
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(4.0)
        >>> verticality
        <Verticality 4.0 {E#3 G3}>
        >>> el = verticality.makeElement(2.0)
        >>> el
        <music21.chord.Chord E#3 G3>
        >>> el.duration.quarterLength
        2.0
        >>> el.duration.type
        'half'
        
        If there is nothing there, then a Rest is created
        
        >>> verticality = scoreTree.getVerticalityAt(400.0)
        >>> verticality
        <Verticality 400.0 {}>
        >>> el = verticality.makeElement(1./3)
        >>> el
        <music21.note.Rest rest>
        >>> el.duration.fullName
        'Eighth Triplet (1/3 QL)'
        
        
        TODO: Consider if this is better to return a Note if only one pitch?
        '''
        if self.pitchSet:
            element = chord.Chord(sorted(self.pitchSet))
            startElements = [x.element for x in self.startTimespans]
            try:
                ties = [x.tie for x in startElements if x.tie is not None]
                if any(x.type == 'start' for x in ties):
                    element.tie = tie.Tie('start')
                elif any(x.type == 'continue' for x in ties):
                    element.tie = tie.Tie('continue')
            except AttributeError:
                pass
        else:
            element = note.Rest()
        element.duration.quarterLength = quarterLength
        return element

    #########  Analysis type things...

    def getAllVoiceLeadingQuartets(self, includeRests=True, includeOblique=True, 
                                   includeNoMotion=False, returnObjects=True, partPairNumbers=None):
        '''
        >>> c = corpus.parse('luca/gloria').measures(1,8)
        >>> tsCol = tree.fromStream.asTimespans(c, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticality22 = tsCol.getVerticalityAt(22.0)
        
        >>> from pprint import pprint as pp
        >>> for vlq in verticality22.getAllVoiceLeadingQuartets():
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet 
             v1n1=<music21.note.Note G>, v1n2=<music21.note.Note C>, 
             v2n1=<music21.note.Note E>, v2n2=<music21.note.Note F> >
        <music21.voiceLeading.VoiceLeadingQuartet 
            v1n1=<music21.note.Note G>, v1n2=<music21.note.Note C>, 
            v2n1=<music21.note.Note A>, v2n2=<music21.note.Note A> >
        <music21.voiceLeading.VoiceLeadingQuartet 
            v1n1=<music21.note.Note E>, v1n2=<music21.note.Note F>, 
            v2n1=<music21.note.Note A>, v2n2=<music21.note.Note A> > 

        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(includeRests=False):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet 
            v1n1=<music21.note.Note E>, v1n2=<music21.note.Note F>, 
            v2n1=<music21.note.Note A>, v2n2=<music21.note.Note A> > 

        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(includeOblique=False):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet 
            v1n1=<music21.note.Note G>, v1n2=<music21.note.Note C>, 
            v2n1=<music21.note.Note E>, v2n2=<music21.note.Note F> > 

        >>> verticality22.getAllVoiceLeadingQuartets(includeOblique=False, includeRests=False)
        []


        Raw output
        
        >>> for vlqRaw in verticality22.getAllVoiceLeadingQuartets(returnObjects=False):
        ...     pp(vlqRaw)
        ((<PitchedTimespan (19.5 to 21.0) <music21.note.Note G>>,
          <PitchedTimespan (22.0 to 22.5) <music21.note.Note C>>),
         (<PitchedTimespan (21.0 to 22.0) <music21.note.Note E>>,
          <PitchedTimespan (22.0 to 23.0) <music21.note.Note F>>))
        ((<PitchedTimespan (19.5 to 21.0) <music21.note.Note G>>,
          <PitchedTimespan (22.0 to 22.5) <music21.note.Note C>>),
         (<PitchedTimespan (21.5 to 22.5) <music21.note.Note A>>,
          <PitchedTimespan (21.5 to 22.5) <music21.note.Note A>>))
        ((<PitchedTimespan (21.0 to 22.0) <music21.note.Note E>>,
          <PitchedTimespan (22.0 to 23.0) <music21.note.Note F>>),
         (<PitchedTimespan (21.5 to 22.5) <music21.note.Note A>>,
          <PitchedTimespan (21.5 to 22.5) <music21.note.Note A>>))
          
        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(partPairNumbers=[(0,1)]):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet 
            v1n1=<music21.note.Note G>, v1n2=<music21.note.Note C>, 
            v2n1=<music21.note.Note E>, v2n2=<music21.note.Note F> >  
        
        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(partPairNumbers=[(0,2),(1,2)]):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet 
            v1n1=<music21.note.Note G>, v1n2=<music21.note.Note C>, 
            v2n1=<music21.note.Note A>, v2n2=<music21.note.Note A> >                 
        <music21.voiceLeading.VoiceLeadingQuartet 
            v1n1=<music21.note.Note E>, v1n2=<music21.note.Note F>, 
            v2n1=<music21.note.Note A>, v2n2=<music21.note.Note A> >
        '''
        import itertools
        from music21.voiceLeading import VoiceLeadingQuartet
        pairedMotionList = self.getPairedMotion(includeRests=includeRests, 
                                                includeOblique=includeOblique)
        allQuartets = itertools.combinations(pairedMotionList, 2)
        filteredList = []
        
        verticalityStreamParts = self.timespanTree.source.parts
        
        for thisQuartet in allQuartets:
            if includeNoMotion is False:
                if (thisQuartet[0][0].pitches == thisQuartet[0][1].pitches
                    and thisQuartet[1][0].pitches == thisQuartet[1][1].pitches):
                    continue
                if partPairNumbers is not None:
                    isAppropriate = False
                    for pp in partPairNumbers:
                        thisQuartetTopPart = thisQuartet[0][0].part
                        thisQuartetBottomPart = thisQuartet[1][0].part
                        if ((verticalityStreamParts[pp[0]] == thisQuartetTopPart
                                or verticalityStreamParts[pp[0]] == thisQuartetBottomPart) 
                            and (verticalityStreamParts[pp[1]] == thisQuartetTopPart
                                 or verticalityStreamParts[pp[1]] == thisQuartetBottomPart)  
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
                    
                    if (n11 is not None
                            and n12 is not None
                            and n21 is not None
                            and n22 is not None): 
                        vlq = VoiceLeadingQuartet(n11, n12, n21, n22)
                        filteredList.append(vlq)
        
        return filteredList
        
    def getPairedMotion(self, includeRests=True, includeOblique=True):
        '''
        Get a list of two-element tuples that are in the same part [TODO: or containing stream??]
        and which move here.
        
        >>> c = corpus.parse('luca/gloria').measures(1,8)
        >>> tsCol = tree.fromStream.asTimespans(c, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> verticality22 = tsCol.getVerticalityAt(22.0)
        >>> for pm in verticality22.getPairedMotion():
        ...     print(pm)
        (<PitchedTimespan (19.5 to 21.0) <music21.note.Note G>>, 
         <PitchedTimespan (22.0 to 22.5) <music21.note.Note C>>)
        (<PitchedTimespan (21.0 to 22.0) <music21.note.Note E>>, 
         <PitchedTimespan (22.0 to 23.0) <music21.note.Note F>>)
        (<PitchedTimespan (21.5 to 22.5) <music21.note.Note A>>, 
         <PitchedTimespan (21.5 to 22.5) <music21.note.Note A>>)
        
        Note that the second one contains a one-beat rest at 21.0-22.0; so includeRests = False will
        get rid of that:
        
        >>> for pm in verticality22.getPairedMotion(includeRests=False):
        ...     print(pm)
        (<PitchedTimespan (21.0 to 22.0) <music21.note.Note E>>, 
         <PitchedTimespan (22.0 to 23.0) <music21.note.Note F>>)
        (<PitchedTimespan (21.5 to 22.5) <music21.note.Note A>>, 
         <PitchedTimespan (21.5 to 22.5) <music21.note.Note A>>)
        
        
        Oblique here means a pair that does not move (it could be called noMotion, 
        because there's no motion
        here in a two-note pair, but we still call it includeOblique so it's consistent with
        getAllVoiceLeadingQuartets).
        
        >>> for pm in verticality22.getPairedMotion(includeOblique=False):
        ...     print(pm)
        (<PitchedTimespan (19.5 to 21.0) <music21.note.Note G>>, 
         <PitchedTimespan (22.0 to 22.5) <music21.note.Note C>>)
        (<PitchedTimespan (21.0 to 22.0) <music21.note.Note E>>, 
         <PitchedTimespan (22.0 to 23.0) <music21.note.Note F>>)

        >>> for pm in verticality22.getPairedMotion(includeOblique=False, includeRests=False):
        ...     print(pm)
        (<PitchedTimespan (21.0 to 22.0) <music21.note.Note E>>, 
         <PitchedTimespan (22.0 to 23.0) <music21.note.Note F>>)
        '''
        stopTss = self.stopTimespans
        startTss = self.startTimespans
        overlapTss = self.overlapTimespans
        allPairedMotions = []
                
        for startingTs in startTss:
            previousTs = self.timespanTree.findPreviousPitchedTimespanInSameStreamByClass(
                                                                                        startingTs)
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
        from music21.tree.analysis import Horizontality
        
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
            horizontality = Horizontality(timespans=unwrapped[part],)
            unwrapped[part] = horizontality
        return unwrapped


#------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def runTest(self):
        pass

#------------------------------------------------------------------------------


_DOC_ORDER = (Verticality, VerticalitySequence)


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
