# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         tree/spans.py
# Purpose:      Tools for marking off spans of time that optionally contain 
#               elements and which can be manipulated quickly in a tree
#
# Authors:      Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-15 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Tools for grouping notes and chords into a searchable tree
organized by start and stop offsets.
''' 
import unittest

from music21 import exceptions21
from music21 import environment
environLocal = environment.Environment("tree.spans")
#------------------------------------------------------------------------------
class TimespanException(exceptions21.TreeException):
    pass

#------------------------------------------------------------------------------
class Timespan(object):
    r'''
    A span of time, with a start offset and stop offset.

    Useful for demonstrating various properties of the timespan-collection class
    family.

    >>> timespan = tree.spans.Timespan(-1.5, 3.25)
    >>> print(timespan)
    <Timespan -1.5 3.25>
    
    A timespan has two attributes, its offset and its endTime.  They are immutable...
    
    >>> timespan.offset
    -1.5
    >>> timespan.endTime
    3.25
    
    To create a changed timespan, call the .new() method on the timespan.
    
    >>> ts2 = timespan.new(offset=0.0)
    >>> ts2
    <Timespan 0.0 3.25>

    >>> ts3 = timespan.new(endTime=5.0)
    >>> ts3
    <Timespan -1.5 5.0>
    
    Two timespans are equal if they have the same offset and endTime
    
    >>> ts4 = tree.spans.Timespan(-1.5, 5.0)
    >>> ts3 == ts4
    True
    >>> ts4 == ts2
    False
    '''
    def __init__(self, offset=float('-inf'), endTime=float('inf')):
        if offset is not None:
            offset = float(offset)
        self._offset = offset
        if endTime is not None:
            endTime = float(endTime)
        self._endTime = endTime
        if offset is not None and endTime is not None:
            if offset > endTime:
                raise TimespanException('offset %r must be after endTime %r' % (offset, endTime))

    def __eq__(self, expr):
        if type(self) is type(expr):
            if self.offset == expr.offset:
                if self.endTime == expr.endTime:
                    return True
        return False

    def __repr__(self):
        return '<{} {} {}>'.format(
            type(self).__name__,
            self.offset,
            self.endTime,
            )


    @property
    def offset(self):
        r'''
        The start offset of the Timespan, relative to its
        containing score.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTimespans()
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> timespan = verticality.startTimespans[0]
        >>> timespan.offset
        1.0
        '''
        # this is a property to make it immutable.
        return self._offset
        
    @property
    def endTime(self):
        r'''
        The stop offset of the Timespan, relative to its
        containing score.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTimespans()
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> timespan = verticality.startTimespans[0]
        >>> timespan.endTime
        2.0
        '''
        # this is a property to make it immutable.
        return self._endTime

    def new(self, offset=None, endTime=None):
        '''
        return a new object with the given offset and endTime
        '''
        if offset is None:
            offset = self.offset
        if endTime is None:
            endTime = self.endTime

        return type(self)(offset=offset, endTime=endTime)
        

    def canMerge(self, other):
        '''
        returns a tuple of (True or False) if these timespans can be merged
        with the second element being a message or None.
        
        >>> ts1 = tree.spans.Timespan(0, 5)
        >>> ts2 = tree.spans.Timespan(5, 7)
        >>> ts1.canMerge(ts2)
        (True, '')
        >>> ts3 = tree.spans.Timespan(6, 10)
        >>> ts1.canMerge(ts3)
        (False, 'Cannot merge <Timespan 0.0 5.0> with <Timespan 6.0 10.0>: not contiguous')

        Overlapping Timespans cannot be merged, just contiguous ones.

        >>> ts4 = tree.spans.Timespan(3, 4)
        >>> ts1.canMerge(ts4)
        (False, 'Cannot merge <Timespan 0.0 5.0> with <Timespan 3.0 4.0>: not contiguous')
        '''
        if not isinstance(other, type(self)):
            message = 'Cannot merge {} with {}: wrong types'.format(self, other)
            return (False, message)
        if not ((self.endTime == other.offset)
                or (other.endTime == self.offset)):
            message = 'Cannot merge {} with {}: not contiguous'.format(self, other)
            return (False, message)
        return (True, "")

    def mergeWith(self, other):
        r'''
        Merges two consecutive/contiguous timespans, keeping the
        information from the former of the two.
        
        >>> ts1 = tree.spans.Timespan(0, 5)
        >>> ts2 = tree.spans.Timespan(5, 7)
        >>> ts3 = ts1.mergeWith(ts2)
        >>> ts3
        <Timespan 0.0 7.0>

        Note that (for now), overlapping timespans cannot be merged:
        
        >>> ts4 = tree.spans.Timespan(6, 10)
        >>> ts3.mergeWith(ts4)
        Traceback (most recent call last):
        music21.tree.spans.TimespanException: Cannot merge <Timespan 0.0 7.0> with 
            <Timespan 6.0 10.0>: not contiguous        
        '''
        can, message = self.canMerge(other)
        if can is False:
            raise TimespanException(message)
        
        if self.offset < other.offset:
            mergedTimespan = self.new(endTime=other.endTime)
        else:
            mergedTimespan = other.new(endTime=self.endTime)
        return mergedTimespan
    
    def splitAt(self, offset):
        r'''
        Split Timespan at `offset`.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTimespans(classList=(note.Note,))
        >>> verticality = scoreTree.getVerticalityAt(0)
        >>> verticality
        <Verticality 0 {A3 E4 C#5}>
        
        >>> timespan = verticality.startTimespans[0]
        >>> timespan
        <PitchedTimespan (0.0 to 0.5) <music21.note.Note C#>>

        >>> for shard in timespan.splitAt(0.25):
        ...     shard
        ...
        <PitchedTimespan (0.0 to 0.25) <music21.note.Note C#>>
        <PitchedTimespan (0.25 to 0.5) <music21.note.Note C#>>

        >>> timespan.splitAt(1000)
        (<PitchedTimespan (0.0 to 0.5) <music21.note.Note C#>>,)
        '''

        if offset < self.offset or self.endTime < offset:
            return (self,)
        left = self.new(endTime=offset)
        right = self.new(offset=offset)
        return left, right
    
    
#------------------------------------------------------------------------------

class ElementTimespan(Timespan):
    r'''
    A span of time anchored to an element in a score.  The span of time may
    be the same length as the element in the score.  It may be shorter (a
    "slice" of an element) or it may be longer (in the case of a timespan
    that is anchored to a single element but extends over rests or other
    notes following a note)

    PitchedTimespans give information about an element (such as a Note).  It knows
    its absolute position with respect to the element passed into TimespanTree.  
    It contains information about what measure it's in, what part it's in, etc.

    Example, getting a passing tone from a known location from a Bach chorale.

    First we create an Offset tree:

    >>> score = corpus.parse('bwv66.6')
    >>> scoreTree = score.asTimespans()
    >>> scoreTree
    <TimespanTree {195} (0.0 to 36.0) <music21.stream.Score ...>>

    Then get the verticality from offset 6.5, which is beat two-and-a-half of
    measure 2 (the piece is in 4/4 with a quarter-note pickup)

    >>> verticality = scoreTree.getVerticalityAt(6.5)
    >>> verticality
    <Verticality 6.5 {E3 D4 G#4 B4}>

    There are four PitchedTimespans in the verticality -- each representing
    a note.  The notes are arranged from lowest to highest.


    We can find all the PitchedTimespans that start exactly at 6.5. There's
    one.

    >>> verticality.startTimespans
    (<PitchedTimespan (6.5 to 7.0) <music21.note.Note D>>,)

    >>> pitchedTimespan = verticality.startTimespans[0]
    >>> pitchedTimespan
    <PitchedTimespan (6.5 to 7.0) <music21.note.Note D>>

    What can we do with a PitchedTimespan? We can get its Part object and from there the
    Part object name

    >>> pitchedTimespan.part
    <music21.stream.Part Tenor>
    >>> pitchedTimespan.part.partName
    'Tenor'

    Find out what measure it's in:

    >>> pitchedTimespan.measureNumber
    2
    >>> pitchedTimespan.parentOffset
    5.0

    The position in the measure is given by subtracting that from the
    .offset:

    >>> pitchedTimespan.offset - pitchedTimespan.parentOffset
    1.5

    >>> pitchedTimespan.element
    <music21.note.Note D>

    These are not dynamic, so changing the Score object does not change the
    measureNumber, etc.    
    '''

    ### CLASS VARIABLES ###
    _DOC_ATTR = {'parentage':  r'''
                    The Stream hierarchy above the ElementTimespan's element.
            
                    >>> score = corpus.parse('bwv66.6')
                    >>> scoreTree = score.asTimespans()
                    >>> verticality = scoreTree.getVerticalityAt(1.0)
                    >>> pitchedTimespan = verticality.startTimespans[0]
                    >>> pitchedTimespan
                    <PitchedTimespan (1.0 to 2.0) <music21.note.Note A>>
                    >>> for streamSite in pitchedTimespan.parentage:
                    ...     streamSite
                    <music21.stream.Measure 1 offset=1.0>
                    <music21.stream.Part Soprano>
                    <music21.stream.Score ...>
                    '''
                 }

    ### INITIALIZER ###

    def __init__(self,
                 element=None,
                 parentOffset=None,
                 parentEndTime=None,
                 parentage=None,
                 offset=None,
                 endTime=None,
                 ):
        super(ElementTimespan, self).__init__(offset=offset, endTime=endTime)
        
        self.element = element
        if parentage is not None:
            parentage = tuple(parentage)
        self.parentage = parentage
        if parentOffset is not None:
            parentOffset = float(parentOffset)
        self.parentOffset = parentOffset
        if parentEndTime is not None:
            parentEndTime = float(parentEndTime)
        self.parentEndTime = parentEndTime
        if parentOffset is not None and parentEndTime is not None:
            if parentOffset > parentEndTime:
                raise TimespanException(
                    'offset %r must be after parentEndTime %r' % (parentOffset, parentEndTime))

    ### SPECIAL METHODS ###
    def __eq__(self, other):
        if self is other:
            return True
        else:
            return False

    def __repr__(self):
        return '<{} ({} to {}) {!r}>'.format(
            type(self).__name__,
            self.offset,
            self.endTime,
            self.element,
            )

    ### PUBLIC METHODS ###


    def new(self,
            element=None,
            parentOffset=None,
            parentEndTime=None,
            offset=None,
            endTime=None,
        ):
        '''
        Create a new object that is identical to the calling object
        but with some of the parameters overridden.
        
        >>> n = note.Note("C#")
        >>> pts = tree.spans.PitchedTimespan(n, offset=11.0, endTime=12.0)
        >>> pts
        <PitchedTimespan (11.0 to 12.0) <music21.note.Note C#>>
        >>> pts2 = pts.new(endTime=13.0)
        >>> pts2
        <PitchedTimespan (11.0 to 13.0) <music21.note.Note C#>>
        >>> pts.element is pts2.element
        True
        '''
        element = element or self.element
        if parentOffset is None:
            parentOffset = self.parentOffset
        if parentEndTime is None:
            parentEndTime = self.parentEndTime
        if offset is None:
            offset = self.offset
        if endTime is None:
            endTime = self.endTime
        
        return type(self)(
            element=element,
            parentOffset=parentOffset,
            parentEndTime=parentEndTime,
            parentage=self.parentage,
            offset=offset,
            endTime=endTime,
            )


    ### PUBLIC PROPERTIES ###


    @property
    def quarterLength(self):
        '''
        The quarterLength of the Timespan, which, due to manipulation, may be different
        from that of the element.
        
        >>> n = note.Note('D-')
        >>> n.offset = 1.0
        >>> n.duration.quarterLength = 2.0

        >>> pts = tree.spans.PitchedTimespan(n, offset=n.offset, endTime=3.0)
        >>> pts
        <PitchedTimespan (1.0 to 3.0) <music21.note.Note D->>
        >>> pts.quarterLength
        2.0
        >>> n.duration.quarterLength
        2.0
        
        >>> pts2 = pts.new(offset=0.0)
        >>> pts2
        <PitchedTimespan (0.0 to 3.0) <music21.note.Note D->>
        >>> pts2.quarterLength
        3.0
        >>> pts2.element.duration.quarterLength
        2.0
        '''
        return self.endTime - self.offset


    @property
    def measureNumber(self):
        r'''
        The measure number of the measure containing the element.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTimespans()
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> pitchedTimespan = verticality.startTimespans[0]
        >>> pitchedTimespan.measureNumber
        1
        '''
        return self.element.measureNumber
        #from music21 import stream
        #for x in self.parentage:
        #    if not isinstance(x, stream.Measure):
        #        continue
        #    return x.measureNumber
        #return None

    def getParentageByClass(self, classList):
        '''
        returns that is the first parentage that has this classList.
        default stream.Part

        >>> score = corpus.parse('bwv66.6')
        >>> score.id = 'bach'
        >>> scoreTree = score.asTimespans()
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> pitchedTimespan = verticality.startTimespans[2]
        >>> pitchedTimespan
        <PitchedTimespan (1.0 to 2.0) <music21.note.Note C#>>
        >>> pitchedTimespan.getParentageByClass(classList=(stream.Part,))
        <music21.stream.Part Tenor>
        >>> pitchedTimespan.getParentageByClass(classList=(stream.Measure,))
        <music21.stream.Measure 1 offset=1.0>
        >>> pitchedTimespan.getParentageByClass(classList=(stream.Score,))
        <music21.stream.Score bach>

        The closest parent is returned in case of a multiple list...

        >>> searchTuple = (stream.Voice, stream.Measure, stream.Part)
        >>> pitchedTimespan.getParentageByClass(classList=searchTuple)
        <music21.stream.Measure 1 offset=1.0>

        TODO: this should take a normal class list.
        '''
        for parent in self.parentage:
            if isinstance(parent, classList):
                return parent
        return None

    @property
    def part(self):
        '''
        find the object in the parentage that is a Part object:
        
        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTimespans()
        >>> verticality = scoreTree.getVerticalityAt(1.0)
        >>> pitchedTimespan = verticality.startTimespans[2]
        >>> pitchedTimespan
        <PitchedTimespan (1.0 to 2.0) <music21.note.Note C#>>
        >>> pitchedTimespan.part
        <music21.stream.Part Tenor>
        '''
        from music21 import stream
        return self.getParentageByClass(classList=(stream.Part,))



#------------------------------------------------------------------------------
class PitchedTimespan(ElementTimespan):
    def __init__(self,
                 element=None,
                 parentOffset=None,
                 parentEndTime=None,
                 parentage=None,
                 offset=None,
                 endTime=None,
                 ):
        super(PitchedTimespan, self).__init__(element=element,
                                              parentOffset=parentOffset,
                                              parentEndTime=parentEndTime,
                                              parentage=parentage,
                                              offset=offset, 
                                              endTime=endTime)


    @property
    def pitches(self):
        r'''
        Gets the pitches of the element wrapped by this PitchedTimespan.

        This treats notes as chords.
        
        >>> c = chord.Chord('C4 E4 G4')
        >>> pts = tree.spans.PitchedTimespan(c, offset=0.0, endTime=1.0)
        >>> pts.pitches
        (<music21.pitch.Pitch C4>, <music21.pitch.Pitch E4>, <music21.pitch.Pitch G4>)
        
        Perhaps remove? except for this case:
        
        >>> d = dynamics.Dynamic('f')
        >>> pts2 = tree.spans.PitchedTimespan(d, offset=0.0, endTime=10.0)
        >>> pts2.pitches
        ()
        '''
        result = []
        if hasattr(self.element, 'pitches') and 'music21.key.Key' not in self.element.classSet:
            result.extend(self.element.pitches)
        result.sort()
        return tuple(result)


    def canMerge(self, other):
        '''
        submethod of base canMerge that checks to see if the pitches are the same.

        For quick score reductions, we can merge two consecutive 
        like-pitched element timespans, keeping
        score-relevant information from the first of the two, such as its
        Music21 Element.
    
        This is useful when using timespans to perform score reduction.
    
        Let's demonstrate merging some contiguous E's in the alto part of a Bach
        chorale:
    
        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTimespans(classList=(note.Note,))
        >>> timespan_one = scoreTree[12]
        >>> print(timespan_one)
        <PitchedTimespan (2.0 to 3.0) <music21.note.Note E>>
    
        >>> print(timespan_one.part)
        <music21.stream.Part Alto>
    
        >>> timespan_two = scoreTree.findNextPitchedTimespanInSameStreamByClass(timespan_one)
        >>> print(timespan_two)
        <PitchedTimespan (3.0 to 4.0) <music21.note.Note E>>
        
        >>> timespan_one.canMerge(timespan_two)
        (True, '')
        
        >>> merged = timespan_one.mergeWith(timespan_two)
        >>> print(merged)
        <PitchedTimespan (2.0 to 4.0) <music21.note.Note E>>
    
        >>> merged.part is timespan_one.part
        True
    
    
        Attempting to merge timespans which are not contiguous, or which do not
        have identical pitches will result in error:
    
        >>> scoreTree[0].canMerge(scoreTree[50])
        (False, 'Cannot merge <PitchedTimespan (0.0 to 0.5) <music21.note.Note C#>> 
             with <PitchedTimespan (9.5 to 10.0) <music21.note.Note B>>: not contiguous')

        
        >>> scoreTree[0].mergeWith(scoreTree[50])
        Traceback (most recent call last):
        music21.tree.spans.TimespanException: Cannot merge 
                <PitchedTimespan (0.0 to 0.5) <music21.note.Note C#>> 
                with <PitchedTimespan (9.5 to 10.0) <music21.note.Note B>>: not contiguous
    
        
        This is probably not what you want to do: get the next element timespan in
        the same score:
    
        >>> timespan_twoWrong = scoreTree.findNextPitchedTimespanInSameStreamByClass(
        ...     timespan_one, classList=(stream.Score,))
        >>> print(timespan_twoWrong)
        <PitchedTimespan (3.0 to 4.0) <music21.note.Note C#>>
        >>> print(timespan_twoWrong.part)
        <music21.stream.Part Soprano>

        '''
        can, message = super(PitchedTimespan, self).canMerge(other)
        if can is True:
            if self.pitches != other.pitches:
                message = 'Cannot merge {} with {}: different pitches'.format(
                    self, other)
                can = False                
        return (can, message)


#------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def runTest(self):
        pass


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
