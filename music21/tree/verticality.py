# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:         tree/verticality.py
# Purpose:      Object for dealing with vertical simultaneities in a
#               fast way w/o Chord's overhead
#
# Authors:      Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-16 Michael Scott Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# ----------------------------------------------------------------------------
'''
Object for dealing with vertical simultaneities in a fast way w/o Chord's overhead.
'''
import collections.abc
import copy
import itertools
import unittest

from music21 import chord
from music21 import common
from music21 import environment
from music21 import exceptions21
from music21 import note
from music21 import prebase
from music21 import tie
# from music21 import key
# from music21 import pitch

from music21.tree import spans

environLocal = environment.Environment('tree.verticality')


class VerticalityException(exceptions21.TreeException):
    pass


class Verticality(prebase.ProtoM21Object):
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
    <music21.tree.verticality.Verticality 6.5 {E3 D4 G#4 B4}>


    The representation of a verticality gives the pitches from lowest to
    highest (in sounding notes).


    A verticality knows its offset, but because elements might end at
    different times, it doesn't know its endTime

    >>> verticality.offset
    6.5
    >>> verticality.endTime
    Traceback (most recent call last):
    AttributeError: 'Verticality' object has no attribute 'endTime'


    However, we can find when the next verticality starts by looking at the nextVerticality

    >>> nv = verticality.nextVerticality
    >>> nv
    <music21.tree.verticality.Verticality 7.0 {A2 C#4 E4 A4}>
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
    passing tone D in the tenor and it lasts from offset 6.5 to offset 7.0,
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

    # CLASS VARIABLES #

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
            <music21.tree.verticality.Verticality 0.5 {G#3 B3 E4 B4}>
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
            <music21.tree.verticality.Verticality 1.0 {F#3 C#4 F#4 A4}>
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
            <music21.tree.verticality.Verticality 1.0 {F#3 C#4 F#4 A4}>
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
            <music21.tree.verticality.Verticality 1.0 {F#3 C#4 F#4 A4}>

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

    # INITIALIZER #

    def __init__(self,
                 offset=None,
                 overlapTimespans=None,
                 startTimespans=None,
                 stopTimespans=None,
                 timespanTree=None,
                 ):

        from music21.tree import trees
        if timespanTree is not None and not isinstance(timespanTree, trees.OffsetTree):
            raise VerticalityException(
                f'timespanTree {timespanTree!r} is not a OffsetTree or None')

        self.timespanTree = timespanTree
        self.offset = offset

        if not isinstance(startTimespans, tuple):
            raise VerticalityException(f'startTimespans must be a tuple, not {startTimespans!r}')
        if not isinstance(stopTimespans, (tuple, type(None))):
            raise VerticalityException(
                f'stopTimespans must be a tuple or None, not {stopTimespans!r}')
        if not isinstance(overlapTimespans, (tuple, type(None))):
            raise VerticalityException(
                f'overlapTimespans must be a tuple or None, not {overlapTimespans!r}')

        self.startTimespans = startTimespans
        self.stopTimespans = stopTimespans
        self.overlapTimespans = overlapTimespans

    # SPECIAL METHODS #

    def _reprInternal(self):
        sortedPitches = sorted(self.pitchSet)
        enclosedNames = '{' + ' '.join(x.nameWithOctave for x in sortedPitches) + '}'
        return f'{self.offset} {enclosedNames}'

    # PUBLIC PROPERTIES #

    @property
    def bassTimespan(self):
        r'''
        Gets the bass timespan in this verticality.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> verticality
        <music21.tree.verticality.Verticality 1.0 {F#3 C#4 F#4 A4}>

        >>> verticality.bassTimespan
        <PitchedTimespan (1.0 to 2.0) <music21.note.Note F#>>
        '''
        overallLowestPitch = None
        lowestTimespan = None

        for ts in self.startAndOverlapTimespans:
            if not hasattr(ts, 'pitches'):
                continue

            tsPitches = ts.pitches
            if not tsPitches:
                continue

            lowestPitch = sorted(tsPitches)[0]
            if overallLowestPitch is None:
                overallLowestPitch = lowestPitch
                lowestTimespan = ts
            if lowestPitch <= overallLowestPitch:
                overallLowestPitch = lowestPitch
                lowestTimespan = ts

        return lowestTimespan

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
        <music21.tree.verticality.Verticality 1.25 {F#3 C#4 F#4 A4}>
        >>> verticality.startTimespans
        ()
        >>> verticality.beatStrength is None
        True
        '''
        try:
            thisTimespan = self.startTimespans[0]
        except IndexError:
            return None
        return thisTimespan.element.beatStrength

    def toChord(self):
        '''
        creates a chord.Chord object of default length (1.0 or
        the duration of some note object) from the verticality.

        Does nothing about ties, etc. -- a very dumb chord, but useful
        for querying consonance, etc.  See makeElement() for the smart version.

        It may be a zero- or one-pitch chord.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTimespans()
        >>> verticality = scoreTree.getVerticalityAt(4.0)
        >>> verticality.toChord()
        <music21.chord.Chord G#3 B3 E4 E5>
        '''
        c = chord.Chord(sorted(self.pitchSet))
        return c

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

        If a verticality has no tree attached, then it will return None
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
        <music21.tree.verticality.Verticality 1.0 {F#3 C#4 F#4 A4}>

        >>> nextVerticality = verticality.nextVerticality
        >>> print(nextVerticality)
        <music21.tree.verticality.Verticality 2.0 {G#3 B3 E4 B4}>

        Verticality objects created by an offset-tree hold a reference back to
        that offset-tree. This means that they determine their next or previous
        verticality dynamically based on the state of the offset-tree only when
        asked. Because of this, it is safe to mutate the offset-tree by
        inserting or removing timespans while iterating over it.

        >>> scoreTree.removeTimespanList(nextVerticality.startTimespans)
        >>> verticality.nextVerticality
        <music21.tree.verticality.Verticality 3.0 {A3 E4 C#5}>
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
        pitchNameSet = set()
        pitchSet = set()

        for timespan in self.startAndOverlapTimespans:
            if not hasattr(timespan, 'pitches'):
                continue
            for p in timespan.pitches:
                pName = p.nameWithOctave
                if pName in pitchNameSet:
                    continue

                pitchNameSet.add(pName)
                pitchSet.add(p)

        return pitchSet

    @property
    def pitchClassSet(self):
        r'''
        Gets a set of all pitches in a verticality with distinct pitchClasses

        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('B#5')
        >>> s = stream.Stream()
        >>> s.insert(4.0, n1)
        >>> s.insert(4.0, n2)
        >>> scoreTree = s.asTimespans()
        >>> verticality = scoreTree.getVerticalityAt(4.0)
        >>> pitchSet = verticality.pitchSet
        >>> list(sorted(pitchSet))
        [<music21.pitch.Pitch C4>, <music21.pitch.Pitch B#5>]

        PitchClassSet will return only one pitch.  Which of these
        is returned is arbitrary.

        >>> pitchClassSet = verticality.pitchClassSet
        >>> #_DOCS_SHOW list(sorted(pitchClassSet))
        >>> print('[<music21.pitch.Pitch B#5>]')  #_DOCS_HIDE
        [<music21.pitch.Pitch B#5>]
        '''
        outPitchSet = set()
        pitchClassSet = set()

        for currentPitch in self.pitchSet:
            pitchClass = currentPitch.pitchClass
            if pitchClass in pitchClassSet:
                continue

            pitchClassSet.add(pitchClass)
            outPitchSet.add(currentPitch)
        return outPitchSet

    @property
    def previousVerticality(self):
        r'''
        Gets the previous verticality before a verticality.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> print(verticality)
        <music21.tree.verticality.Verticality 1.0 {F#3 C#4 F#4 A4}>

        >>> previousVerticality = verticality.previousVerticality
        >>> print(previousVerticality)
        <music21.tree.verticality.Verticality 0.5 {G#3 B3 E4 B4}>

        Continue it:

        >>> v = scoreTree.getVerticalityAt(1.0)
        >>> while v is not None:
        ...     print(v)
        ...     v = v.previousVerticality
        <music21.tree.verticality.Verticality 1.0 {F#3 C#4 F#4 A4}>
        <music21.tree.verticality.Verticality 0.5 {G#3 B3 E4 B4}>
        <music21.tree.verticality.Verticality 0.0 {A3 E4 C#5}>

        Verticality objects created by an offset-tree hold a reference back to
        that offset-tree. This means that they determine their next or previous
        verticality dynamically based on the state of the offset-tree only when
        asked. Because of this, it is safe to mutate the offset-tree by
        inserting or removing timespans while iterating over it.

        >>> scoreTree.removeTimespanList(previousVerticality.startTimespans)
        >>> verticality.previousVerticality
        <music21.tree.verticality.Verticality 0.0 {A3 E4 C#5}>
        '''
        tree = self.timespanTree
        if tree is None:
            return None
        offset = tree.getPositionBefore(self.offset)
        if offset is None:
            return None
        return tree.getVerticalityAt(offset)

    @property
    def startAndOverlapTimespans(self):
        '''
        Return a tuple adding the start and overlap timespans into one.

        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('D4')
        >>> s = stream.Stream()
        >>> s.insert(4.0, n1)
        >>> s.insert(4.5, n2)
        >>> scoreTree = s.asTimespans()
        >>> verticality = scoreTree.getVerticalityAt(4.5)
        >>> verticality.startTimespans
        (<PitchedTimespan (4.5 to 5.5) <music21.note.Note D>>,)

        >>> verticality.overlapTimespans
        (<PitchedTimespan (4.0 to 5.0) <music21.note.Note C>>,)

        >>> verticality.startAndOverlapTimespans
        (<PitchedTimespan (4.5 to 5.5) <music21.note.Note D>>,
         <PitchedTimespan (4.0 to 5.0) <music21.note.Note C>>)

        >>> verticality = scoreTree.getVerticalityAt(4.0)
        >>> verticality.startAndOverlapTimespans
        (<PitchedTimespan (4.0 to 5.0) <music21.note.Note C>>,)
        '''
        if self.overlapTimespans is None:
            return tuple(self.startTimespans)

        return tuple(self.startTimespans[:] + self.overlapTimespans[:])

    # makeElement

    def makeElement(self,
                    quarterLength=1.0,
                    *,
                    addTies=True,
                    addPartIdAsGroup=False,
                    removeRedundantPitches=True,
                    gatherArticulations='single',
                    gatherExpressions='single',
                    copyPitches=True,
                    ):
        r'''
        Makes a Chord or Rest from this verticality and quarterLength.

        >>> score = tree.makeExampleScore()
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
        ...            classList=(note.Note, chord.Chord))
        >>> verticality = scoreTree.getVerticalityAt(4.0)
        >>> verticality
        <music21.tree.verticality.Verticality 4.0 {E#3 G3}>
        >>> verticality.startTimespans
        (<PitchedTimespan (4.0 to 5.0) <music21.note.Note G>>,
         <PitchedTimespan (4.0 to 6.0) <music21.note.Note E#>>)

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
        <music21.tree.verticality.Verticality 400.0 {}>
        >>> el = verticality.makeElement(1/3)
        >>> el
        <music21.note.Rest rest>
        >>> el.duration.fullName
        'Eighth Triplet (1/3 QL)'


        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('C4')
        >>> s = stream.Score()
        >>> s.insert(0, n1)
        >>> s.insert(0.5, n2)
        >>> scoreTree = s.asTimespans()
        >>> verticality = scoreTree.getVerticalityAt(0.5)
        >>> c = verticality.makeElement(0.5)
        >>> c
        <music21.chord.Chord C4>

        >>> c = verticality.makeElement(0.5, removeRedundantPitches=False)
        >>> c
        <music21.chord.Chord C4 C4>

        Generally the pitches of the new element are not connected to the original pitch:

        >>> c[0].pitch.name = 'E'
        >>> c[1].pitch.name = 'F'
        >>> (n1.name, n2.name)
        ('C', 'C')

        But if `copyPitches` is False then the original pitch will be used:

        >>> n1.name = 'D'
        >>> n2.name = 'E'
        >>> c = verticality.makeElement(0.5, removeRedundantPitches=False, copyPitches=False)
        >>> c
        <music21.chord.Chord D4 E4>

        >>> c[0].pitch.name = 'F'
        >>> c[1].pitch.name = 'G'
        >>> (n1.name, n2.name)
        ('F', 'G')



        gatherArticulations and gatherExpressions can be True, False, or (default) 'single'.

        * If False, no articulations (or expressions) are transferred to the chord.
        * If True, all articulations are transferred to the chord.
        * If 'single', then no more than one articulation of each class (chosen from the lowest
          note) will be added.  This way, the chord does not get 4 fermatas, etc.

        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('D4')
        >>> s = stream.Stream()
        >>> s.insert(0, n1)
        >>> s.insert(0.5, n2)

        >>> class AllAttachArticulation(articulations.Articulation):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.tieAttach = 'all'

        >>> class OtherAllAttachArticulation(articulations.Articulation):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.tieAttach = 'all'


        >>> n1.articulations.append(articulations.Accent())
        >>> n1.articulations.append(AllAttachArticulation())
        >>> n1.expressions.append(expressions.Fermata())

        >>> n2.articulations.append(articulations.Staccato())
        >>> n2.articulations.append(AllAttachArticulation())
        >>> n2.articulations.append(OtherAllAttachArticulation())
        >>> n2.expressions.append(expressions.Fermata())

        >>> scoreTree = s.asTimespans()

        >>> verticality = scoreTree.getVerticalityAt(0.0)
        >>> c = verticality.makeElement(1.0)
        >>> c.expressions
        [<music21.expressions.Fermata>]
        >>> c.articulations
        [<music21.articulations.Accent>, <...AllAttachArticulation>]

        >>> verticality = scoreTree.getVerticalityAt(0.5)


        Here there will be no expressions, because there is no note ending
        at 0.75 and Fermatas attach to the last note:

        >>> c = verticality.makeElement(0.25)
        >>> c.expressions
        []

        >>> c = verticality.makeElement(0.5)
        >>> c.expressions
        [<music21.expressions.Fermata>]

        Only two articulations, since accent attaches to beginning and staccato attaches to last
        and we are beginning after the start of the first note (with an accent)
        and cutting right through the second note (with a staccato)

        >>> c.articulations
        [<...AllAttachArticulation>,
         <...OtherAllAttachArticulation>]

        >>> c = verticality.makeElement(0.5, gatherArticulations=True)
        >>> c.articulations
        [<...AllAttachArticulation>,
         <...AllAttachArticulation>,
         <...OtherAllAttachArticulation>]

        >>> c = verticality.makeElement(0.5, gatherArticulations=False)
        >>> c.articulations
        []

        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> c = verticality.makeElement(0.5)
        >>> c.expressions
        [<music21.expressions.Fermata>]
        >>> c.articulations
        [<music21.articulations.Staccato>,
         <...AllAttachArticulation>,
         <...OtherAllAttachArticulation>]

        Added in v6.3:  copyPitches option

        OMIT_FROM_DOCS

        Test that copyPitches works with expressions:

        >>> c = verticality.makeElement(0.5, copyPitches=False)
        >>> c
        <music21.chord.Chord D4>
        >>> c.pitches[0].accidental = pitch.Accidental('sharp')
        >>> n2
        <music21.note.Note D#>

        '''
        if not self.pitchSet:
            r = note.Rest()
            r.duration.quarterLength = common.opFrac(quarterLength)
            return r

        # easy stuff done, time to get to the hard stuff...

        c = chord.Chord()
        c.duration.quarterLength = common.opFrac(quarterLength)
        dur = c.duration

        seenPitches = set()
        notesToAdd = {}

        startStopSet = {'start', 'stop'}
        pitchBust = 0  # used if removeRedundantPitches is False.

        def newNote(ts, n):
            '''
            Make a copy of the note and clear some settings
            '''
            nNew = copy.deepcopy(n)
            nNew.duration = dur
            if not copyPitches:
                nNew.pitch = n.pitch

            if nNew.stemDirection != 'noStem':
                nNew.stemDirection = None
            if not addTies:
                return nNew

            offsetDifference = common.opFrac(self.offset - ts.offset)
            endTimeDifference = common.opFrac(ts.endTime - (self.offset + quarterLength))
            if offsetDifference == 0 and endTimeDifference <= 0:
                addTie = None
            elif offsetDifference > 0:
                if endTimeDifference > 0:
                    addTie = 'continue'
                else:
                    addTie = 'stop'
            elif endTimeDifference > 0:
                addTie = 'start'
            else:
                raise VerticalityException('What possibility was missed?',
                                           offsetDifference, endTimeDifference, ts, self)

            if nNew.tie is not None and {nNew.tie.type, addTie} == startStopSet:
                nNew.tie.type = 'continue'
            elif nNew.tie is not None and nNew.tie.type == 'continue':
                nNew.tie.placement = None
            elif addTie is None and nNew.tie is not None:
                nNew.tie.placement = None

            elif addTie:
                nNew.tie = tie.Tie(addTie)

            return nNew

        def conditionalAdd(ts, n):
            '''
            Add an element only if it is not already in the chord.

            If it has more tie information than the previously
            added note, then remove the previously added note and add it
            '''
            nonlocal pitchBust  # love Py3!!!
            p = n.pitch
            pitchKey = p.nameWithOctave

            pitchGroup = None
            if addPartIdAsGroup:
                partContext = n.getContextByClass('Part')
                if partContext is not None:
                    pidStr = str(partContext.id)
                    pitchGroup = pidStr.replace(' ', '_')  # spaces are not allowed as group names
                    n.pitch.groups.append(pitchGroup)
                    n.groups.append(pitchGroup)

            if pitchKey not in seenPitches:
                seenPitches.add(pitchKey)
                notesToAdd[pitchKey] = newNote(ts, n)
                return
            elif not removeRedundantPitches:
                notesToAdd[pitchKey + str(pitchBust)] = newNote(ts, n)
                pitchBust += 1
                return
            elif addPartIdAsGroup:
                notesToAdd[pitchKey].groups.append(pitchGroup)
                notesToAdd[pitchKey].pitch.groups.append(pitchGroup)

            if not addTies:
                return

            # else add derivation once multiple derivations are allowed.
            oldNoteTie = notesToAdd[pitchKey].tie
            if oldNoteTie is not None and oldNoteTie.type == 'continue':
                return  # previous note was as good or better

            possibleNewNote = newNote(ts, n)
            possibleNewNote.groups = notesToAdd[pitchKey].groups

            if possibleNewNote.tie is None:
                return  # do nothing
            elif oldNoteTie is None:
                notesToAdd[pitchKey] = possibleNewNote  # a better note to add
            elif {oldNoteTie.type, possibleNewNote.tie.type} == startStopSet:
                notesToAdd[pitchKey].tie.type = 'continue'
            elif possibleNewNote.tie.type == 'continue':
                notesToAdd[pitchKey] = possibleNewNote  # a better note to add
            elif possibleNewNote.tie.type == oldNoteTie.type:
                return
            else:
                raise VerticalityException('Did I miss one? ', possibleNewNote.tie, oldNoteTie)

        for ts in self.startAndOverlapTimespans:
            if not isinstance(ts, spans.PitchedTimespan):
                continue
            el = ts.element
            if 'Chord' in el.classes:
                if len(el) == 0:  # pylint: disable=len-as-condition
                    continue

                if el.articulations or el.expressions:
                    firstSubEl = copy.deepcopy(el[0])  # this makes an additional deepcopy
                    firstSubEl.articulations += el.articulations
                    firstSubEl.expressions += el.expressions
                    if not copyPitches:
                        firstSubEl.pitch = el[0].pitch
                else:
                    firstSubEl = el[0]
                conditionalAdd(ts, firstSubEl)

                if len(el) > 1:
                    for subEl in list(el)[1:]:
                        conditionalAdd(ts, subEl)
            else:
                conditionalAdd(ts, el)

        seenArticulations = set()
        seenExpressions = set()

        # pylint: disable=unidiomatic-typecheck
        for n in sorted(notesToAdd.values(), key=lambda x: x.pitch.ps):
            c.add(n)
            if gatherArticulations:
                for art in n.articulations:
                    if art.tieAttach == 'first' and n.tie is not None and n.tie.type != 'start':
                        continue
                    if art.tieAttach == 'last' and n.tie is not None and n.tie.type != 'stop':
                        continue

                    if gatherArticulations == 'single' and type(art) in seenArticulations:
                        continue
                    c.articulations.append(art)
                    seenArticulations.add(type(art))
            if gatherExpressions:
                for exp in n.expressions:
                    if exp.tieAttach == 'first' and n.tie is not None and n.tie.type != 'start':
                        continue
                    if exp.tieAttach == 'last' and n.tie is not None and n.tie.type != 'stop':
                        continue

                    if gatherExpressions == 'single' and type(exp) in seenExpressions:
                        continue
                    c.expressions.append(exp)
                    seenExpressions.add(type(exp))

        return c

    # Analysis type things...

    def getAllVoiceLeadingQuartets(self, includeRests=True, includeOblique=True,
                                   includeNoMotion=False, returnObjects=True,
                                   partPairNumbers=None):
        '''
        >>> c = corpus.parse('luca/gloria').measures(1, 8)
        >>> tsCol = tree.fromStream.asTimespans(c, flatten=True,
        ...            classList=(note.Note, chord.Chord))
        >>> verticality22 = tsCol.getVerticalityAt(22.0)

        >>> from pprint import pprint as pp
        >>> for vlq in verticality22.getAllVoiceLeadingQuartets():
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet
            v1n1=G4, v1n2=C4, v2n1=E4, v2n2=F4>
        <music21.voiceLeading.VoiceLeadingQuartet
            v1n1=G4, v1n2=C4, v2n1=A3, v2n2=A3>
        <music21.voiceLeading.VoiceLeadingQuartet
            v1n1=E4, v1n2=F4, v2n1=A3, v2n2=A3>

        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(includeRests=False):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet
            v1n1=E4, v1n2=F4, v2n1=A3, v2n2=A3>
        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(includeOblique=False):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet
            v1n1=G4, v1n2=C4, v2n1=E4, v2n2=F4>
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

        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(partPairNumbers=[(0, 1)]):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet
            v1n1=G4, v1n2=C4, v2n1=E4, v2n2=F4>
        >>> for vlq in verticality22.getAllVoiceLeadingQuartets(partPairNumbers=[(0, 2), (1, 2)]):
        ...     pp(vlq)
        <music21.voiceLeading.VoiceLeadingQuartet
            v1n1=G4, v1n2=C4, v2n1=A3, v2n2=A3>
        <music21.voiceLeading.VoiceLeadingQuartet
            v1n1=E4, v1n2=F4, v2n1=A3, v2n2=A3>
        '''
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
                                or verticalityStreamParts[pp[1]] == thisQuartetBottomPart)):
                            isAppropriate = True
                            break
                    if not isAppropriate:
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

        >>> c = corpus.parse('luca/gloria').measures(1, 8)
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


# -----------------------------------------------------------------------------


class VerticalitySequence(prebase.ProtoM21Object, collections.abc.Sequence):
    r'''
    A segment of verticalities.
    '''

    # INITIALIZER #

    def __init__(self, verticalities):
        self._verticalities = tuple(verticalities)

    # SPECIAL METHODS #

    def __getitem__(self, item):
        return self._verticalities[item]

    def __len__(self):
        return len(self._verticalities)

    # noinspection PyProtectedMember
    def _reprInternal(self):
        internalRepr = ',\n\t'.join('(' + x._reprInternal() + ')' for x in self)
        out = f'[\n\t{internalRepr}\n\t]'
        return out

    # PUBLIC METHODS #

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


# -----------------------------------------------------------------------------

class Test(unittest.TestCase):
    pass

# -----------------------------------------------------------------------------


_DOC_ORDER = (Verticality, VerticalitySequence)


# -----------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
