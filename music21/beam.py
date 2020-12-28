# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         beam.py
# Purpose:      music21 classes for representing notes
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2012, 19 Michael Scott Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
The module defines Beam and Beams (note plural) objects.

The Beams object holds multiple Beam objects (e.g., a 32nd note might have
three Beam objects in its Beam object).

The Beams object is stored in :class:`~music21.note.Note` and
:class:`~music21.chord.Chord` objects as their :attr:`~music21.note.Note.beams`
attributes.   Beams objects can largely be treated as a list.

See `meter.TimeSignature`. :meth:`~music21.meter.TimeSignature.getBeams` for a
way of getting beam information for a measure given the meter.  The
`meter.TimeSignature`. :attr:`~music21.meter.TimeSignature.beamSequence`
attribute holds information about how to beam given the TimeSignature

Run `Stream`. :meth:`~music21.stream.Stream.makeBeams` to set beaming
information automatically given the current meter.

Suppose you had a measure of two eighths and a quarter and wanted to explicitly
beam the two eighth notes.  You could do this:

>>> m = stream.Measure()
>>> n1 = note.Note('C4', quarterLength=0.5)
>>> n2 = note.Note('D4', quarterLength=0.5)
>>> n3 = note.Note('E4', quarterLength=1.0)
>>> m.append(n1)
>>> m.append(n2)
>>> m.append(n3)
>>> n1.beams.fill('eighth', type='start')
>>> n2.beams.fill('eighth', type='stop')
>>> n1.beams
<music21.beam.Beams <music21.beam.Beam 1/start>>

>>> n2.beams
<music21.beam.Beams <music21.beam.Beam 1/stop>>

But suppose you wanted something harder: two 16ths, an 8th, a quarter, with the
first 3 notes beamed?  The first note and 3rd are easy to do, using the method
above:

>>> m = stream.Measure()
>>> n1 = note.Note('C4', quarterLength=0.25)
>>> n2 = note.Note('D4', quarterLength=0.25)
>>> n3 = note.Note('E4', quarterLength=0.5)
>>> n4 = note.Note('F4', quarterLength=1.0)
>>> for n in [n1, n2, n3, n4]:
...     m.append(n)
>>> n1.beams.fill('16th', type='start')
>>> n3.beams.fill('eighth', type='stop')

but the second note has an 8th beam that continues and a 16th beam that stops.
So you will need to set them separately:

>>> n2.beams.append('continue')
>>> n2.beams.append('stop')
>>> n2.beams
<music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>

To get rid of beams on a note do:

>>> n2.beams.beamsList = []
'''

import unittest

from music21 import common
from music21 import exceptions21
from music21 import duration
from music21 import environment
from music21 import prebase
from music21 import style
from music21.common.objects import EqualSlottedObjectMixin

_MOD = 'meter'
environLocal = environment.Environment(_MOD)


class BeamException(exceptions21.Music21Exception):
    pass


beamableDurationTypes = (
    duration.typeFromNumDict[8],
    duration.typeFromNumDict[16], duration.typeFromNumDict[32],
    duration.typeFromNumDict[64], duration.typeFromNumDict[128],
    duration.typeFromNumDict[256],
)


class Beam(prebase.ProtoM21Object, EqualSlottedObjectMixin, style.StyleMixin):
    '''
    A Beam is an object representation of one single beam, that is, one
    horizontal line connecting two notes together (or less commonly a note to a
    rest).  Thus it takes two separate Beam objects to represent the beaming of
    a 16th note.

    The Beams object (note the plural) is the object that handles groups of
    Beam objects; it is defined later on.

    Here are two ways to define the start of a beam

    >>> b1 = beam.Beam(type='start')
    >>> b2 = beam.Beam('start')

    Here is a partial beam (that is, one that does not connect to any other
    note, such as the second beam of a dotted eighth, sixteenth group)

    Two ways of doing the same thing

    >>> b3 = beam.Beam(number=1, type='partial', direction='left')
    >>> b3
    <music21.beam.Beam 1/partial/left>

    >>> b4 = beam.Beam('partial', 'left')
    >>> b4.number = 1
    >>> b4
    <music21.beam.Beam 1/partial/left>

    All attributes must be the same for equality:

    >>> b3 == b4
    True

    >>> b2
    <music21.beam.Beam None/start>
    >>> b2 == b3
    False
    '''

    # CLASS VARIABLES #

    __slots__ = (
        'direction',
        'id',
        'independentAngle',
        'number',
        'type',
    )

    # INITIALIZER #
    # pylint: disable=redefined-builtin
    def __init__(self, type=None, direction=None, number=None):  # type is okay @ReservedAssignment
        super().__init__()  # must call for style.
        self.type = type  # start, stop, continue, partial
        self.direction = direction  # left or right for partial
        self.independentAngle = None
        # represents which beam line referred to
        # 8th, 16th, etc represented as 1, 2, ...
        self.number = number
        self.id = id(self)

    # PRIVATE METHODS #

    def _reprInternal(self):
        out = f'{self.number}/{self.type}'
        if self.direction is not None:
            out += f'/{self.direction}'
        return out


# -----------------------------------------------------------------------------
class Beams(prebase.ProtoM21Object, EqualSlottedObjectMixin):
    '''
    The Beams object stores in it attribute beamsList (a list) all the Beam
    objects defined above.  Thus len(beam.Beams) tells you how many beams the
    note currently has on it, and iterating over a Beams object gives you each
    Beam.

    >>> n = note.Note(type='16th')
    >>> isinstance(n.beams, beam.Beams)
    True

    >>> n.beams.fill(2, 'start')
    >>> len(n.beams)
    2

    >>> for thisBeam in n.beams:
    ...     thisBeam.type
    'start'
    'start'

    >>> print(n.beams)
    <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>
    '''

    # CLASS VARIABLES #

    __slots__ = (
        'beamsList',
        'feathered',
        'id',
    )

    _DOC_ATTR = {
        'feathered': '''
            Boolean determining if this is a feathered beam or not
            (does nothing for now).''',
    }

    # INITIALIZER #

    def __init__(self):
        # no need for super() call w/ ProtoM21 and EqualSlottedObject
        self.beamsList = []
        self.feathered = False
        self.id = id(self)

    # SPECIAL METHODS #

    def __iter__(self):
        return common.Iterator(self.beamsList)

    def __len__(self):
        return len(self.beamsList)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__repr__() == other.__repr__()

    def _reprInternal(self):
        msg = []
        for beam in self.beamsList:
            msg.append(str(beam))
        return '/'.join(msg)

    # STATIC METHODS #

    @staticmethod
    def naiveBeams(srcList):
        '''
        Given a list or iterator of elements, return a list of None or Beams for
        each element: None if the element is a quarter or larger or
        if the element is a Rest, and the fullest possible set of beams
        for the duration if it is a beamable.  Each beam object has type of None

        staticmethod, does not need instance:

        >>> durList = [0, -1, -2, -3]
        >>> srcList = [note.Note(quarterLength=2 ** x) for x in durList]
        >>> srcList.append(note.Rest(type='32nd'))
        >>> beam.Beams.naiveBeams(srcList)
        [None,
         <music21.beam.Beams <music21.beam.Beam 1/None>>,
         <music21.beam.Beams <music21.beam.Beam 1/None>/<music21.beam.Beam 2/None>>,
         <music21.beam.Beams <music21.beam.Beam 1/None>/<music21.beam.Beam
                     2/None>/<music21.beam.Beam 3/None>>,
         None]
        '''
        beamsList = []
        for el in srcList:
            # if a dur cannot be beamable under any circumstance, replace
            # it with None; this includes Rests
            if el.duration.type not in beamableDurationTypes:
                beamsList.append(None)  # placeholder
            elif el.isRest is True:
                beamsList.append(None)  # placeholder
            else:
                # we have a beamable duration
                b = Beams()
                # set the necessary number of internal beamsList, that is,
                # one for each horizontal line in the beams group
                # this does not set type or direction
                b.fill(el.duration.type)
                beamsList.append(b)
        return beamsList

    @staticmethod
    def removeSandwichedUnbeamables(beamsList):
        '''
        Go through the naiveBeamsList and remove beams from objects surrounded
        by None objects -- you can't beam to nothing!

        Modifies beamsList in place

        >>> N = note.Note
        >>> R = note.Rest
        >>> e = 'eighth'
        >>> nList = [N(type=e), R(type=e), N(type=e), N(type=e),
        ...          R(type=e), N(type=e), R(type=e), N(type=e)]
        >>> beamsList = beam.Beams.naiveBeams(nList)
        >>> beamsList
        [<music21.beam.Beams <music21.beam.Beam 1/None>>,
         None,
         <music21.beam.Beams <music21.beam.Beam 1/None>>,
         <music21.beam.Beams <music21.beam.Beam 1/None>>,
         None,
         <music21.beam.Beams <music21.beam.Beam 1/None>>,
         None,
         <music21.beam.Beams <music21.beam.Beam 1/None>>]

        >>> beamsList2 = beam.Beams.removeSandwichedUnbeamables(beamsList)
        >>> beamsList2 is beamsList
        True
        >>> beamsList2
        [None,
         None,
         <music21.beam.Beams <music21.beam.Beam 1/None>>,
         <music21.beam.Beams <music21.beam.Beam 1/None>>,
         None,
         None,
         None,
         None]
        '''
        beamLast = None
        for i in range(len(beamsList)):
            if i != len(beamsList) - 1:
                beamNext = beamsList[i + 1]
            else:
                beamNext = None

            if beamLast is None and beamNext is None:
                beamsList[i] = None

            beamLast = beamsList[i]

        return beamsList

    @staticmethod
    def mergeConnectingPartialBeams(beamsList):
        '''
        Partial-right followed by partial-left must also be connected, even if otherwise
        over a archetypeSpan, such as 16th notes 2 and 3 in a quarter note span where
        16ths are not beamed by default.
        '''
        # sanitize two partials in a row:
        for i in range(len(beamsList) - 1):
            bThis = beamsList[i]
            bNext = beamsList[i + 1]
            if not bThis or not bNext:
                continue

            bThisNum = bThis.getNumbers()
            if not bThisNum:
                continue

            for thisNum in bThisNum:
                thisBeam = bThis.getByNumber(thisNum)
                if thisBeam.type != 'partial' or thisBeam.direction != 'right':
                    continue

                if thisNum not in bNext.getNumbers():
                    continue

                nextBeam = bNext.getByNumber(thisNum)
                if nextBeam.type == 'partial' and nextBeam.direction == 'right':
                    continue
                if nextBeam.type in ('continue', 'stop'):
                    environLocal.warn(
                        'Found a messed up beam pair {}, {}, at index {} of \n{}'.format(
                            bThis, bNext, i, beamsList))
                    continue

                thisBeam.type = 'start'
                thisBeam.direction = None
                if nextBeam.type == 'partial':
                    nextBeam.type = 'stop'
                elif nextBeam.type == 'start':
                    nextBeam.type = 'continue'

                nextBeam.direction = None

        # now fix partial-lefts that follow stops:
        for i in range(1, len(beamsList)):
            bThis = beamsList[i]
            bPrev = beamsList[i - 1]
            if not bThis or not bPrev:
                continue

            bThisNum = bThis.getNumbers()
            if not bThisNum:
                continue

            for thisNum in bThisNum:
                thisBeam = bThis.getByNumber(thisNum)
                if thisBeam.type != 'partial' or thisBeam.direction != 'left':
                    continue

                if thisNum not in bPrev.getNumbers():
                    continue

                prevBeam = bPrev.getByNumber(thisNum)
                if prevBeam.type != 'stop':
                    continue

                thisBeam.type = 'stop'
                thisBeam.direction = None
                prevBeam.type = 'continue'

        return beamsList

    @staticmethod
    def sanitizePartialBeams(beamsList):
        '''
        It is possible at a late stage to have beams that only consist of partials
        or beams with a 'start' followed by 'partial/left' or possibly 'stop' followed
        by 'partial/right'; beams entirely consisting of partials are removed
        and the direction of irrational partials is fixed.
        '''
        for i in range(len(beamsList)):
            if beamsList[i] is None:
                continue
            allTypes = beamsList[i].getTypes()
            # clear elements that have partial beams with no full beams:
            if 'start' not in allTypes and 'stop' not in allTypes and 'continue' not in allTypes:
                # nothing but partials
                beamsList[i] = None
                continue
            # make sure a partial-left does not follow a start or a partial-right does not
            # follow a stop
            hasStart = False
            hasStop = False
            for b in beamsList[i].beamsList:
                if b.type == 'start':
                    hasStart = True
                    continue
                if b.type == 'stop':
                    hasStop = True
                    continue
                if hasStart and b.type == 'partial' and b.direction == 'left':
                    b.direction = 'right'
                elif hasStop and b.type == 'partial' and b.direction == 'right':
                    b.direction = 'left'

        return beamsList

    # PUBLIC METHODS #
    # pylint: disable=redefined-builtin

    def append(self, type=None, direction=None):  # type is okay @ReservedAssignment
        '''
        Append a new Beam object to this Beams, automatically creating the Beam
        object and incrementing the number count.

        >>> beams = beam.Beams()
        >>> beams.append('start')
        >>> beams.beamsList
        [<music21.beam.Beam 1/start>]

        >>> beams.append('partial', 'right')
        >>> beams.beamsList
        [<music21.beam.Beam 1/start>, <music21.beam.Beam 2/partial/right>]


        A beam object can also be specified:

        >>> beams = beam.Beams()
        >>> beam1 = beam.Beam(type='start', number=1)
        >>> beams.append(beam1)
        >>> beams.beamsList
        [<music21.beam.Beam 1/start>]
        '''
        if isinstance(type, str):
            obj = Beam(type, direction)
            obj.number = len(self.beamsList) + 1
        else:
            obj = type

        self.beamsList.append(obj)

    def fill(self, level=None, type=None):  # type is okay @ReservedAssignment
        '''
        A quick way of setting the beams list for a particular duration, for
        instance, `fill('16th')` will clear the current list of beams in the
        Beams object and add two beams.  `fill(2)` will do the same (though note
        that that is an int, not a string).

        It does not do anything to the direction that the beams are going in,
        or by default.  Either set type here or call `setAll()` on the Beams
        object afterwards.

        Both "eighth" and "8th" work.  Adding more than six beams (i.e. things
        like 512th notes) raises an error.

        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> len(a)
        2

        >>> a.fill('32nd', type='start')
        >>> len(a)
        3

        >>> a.beamsList[2]
        <music21.beam.Beam 3/start>

        >>> a.beamsList[2].type
        'start'

        Filling a smaller number wipes larger numbers of beams:

        >>> a.fill('eighth', type='start')
        >>> len(a)
        1

        OMIT_FROM_DOCS

        >>> a.fill(4)
        >>> len(a)
        4

        >>> a.fill('128th')
        >>> len(a)
        5

        >>> a.fill('256th')
        >>> len(a)
        6

        >>> a.fill(7)
        Traceback (most recent call last):
        music21.beam.BeamException: cannot fill beams for level 7
        '''
        # TODO -- why not to 2048th?
        self.beamsList = []
        # 8th, 16th, etc represented as 1, 2, ...
        if level in [1, '8th', duration.typeFromNumDict[8]]:  # eighth
            count = 1
        elif level in [2, duration.typeFromNumDict[16]]:
            count = 2
        elif level in [3, duration.typeFromNumDict[32]]:
            count = 3
        elif level in [4, duration.typeFromNumDict[64]]:
            count = 4
        elif level in [5, duration.typeFromNumDict[128]]:
            count = 5
        elif level in [6, duration.typeFromNumDict[256]]:
            count = 6
        else:
            raise BeamException(f'cannot fill beams for level {level}')
        for i in range(1, count + 1):
            if i == 0:
                raise BeamException('level zero does not exist for this range')
            obj = Beam()
            obj.number = i
            self.beamsList.append(obj)
        if type is not None:
            self.setAll(type)

    def getByNumber(self, number):
        '''
        Gets an internal beam object by number.

        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> a.setAll('start')
        >>> a.getByNumber(2).type
        'start'

        >>> a.getByNumber(30)
        Traceback (most recent call last):
        IndexError: beam number 30 cannot be accessed
        '''
        if number not in self.getNumbers():
            raise IndexError(f'beam number {number} cannot be accessed')
        for i in range(len(self)):
            if self.beamsList[i].number == number:
                return self.beamsList[i]

    def getNumbers(self):
        '''
        Returns a list of all defined beam numbers; it should normally be a set
        of consecutive integers, but it might not be.

        >>> a = beam.Beams()
        >>> a.fill('32nd')
        >>> a.getNumbers()
        [1, 2, 3]
        '''
        return [x.number for x in self.beamsList]

    def getTypeByNumber(self, number):
        '''
        Get beam type, with direction, by number

        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> a.setAll('start')
        >>> a.setByNumber(2, 'partial-right')
        >>> a.getTypeByNumber(2)
        'partial-right'

        >>> a.getTypeByNumber(1)
        'start'
        '''
        beamObj = self.getByNumber(number)
        if beamObj.direction is None:
            return beamObj.type
        else:
            return f'{beamObj.type}-{beamObj.direction}'

    def getTypes(self):
        '''
        Returns a list of all beam types defined for the current beams

        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> a.setAll('start')
        >>> a.getTypes()
        ['start', 'start']
        '''
        return [x.type for x in self.beamsList]

    def setAll(self, type, direction=None):  # type is okay @ReservedAssignment
        '''
        `setAll` is a method of convenience that sets the type
        of each of the beam objects within the beamsList to the specified type.
        It also takes an optional "direction" attribute that sets the direction
        for each beam (otherwise the direction of each beam is set to None)
        Acceptable directions (start, stop, continue, etc.) are listed under
        Beam() above.

        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> a.setAll('start')
        >>> a.getTypes()
        ['start', 'start']

        >>> a.setAll('sexy')
        Traceback (most recent call last):
        music21.beam.BeamException: beam type cannot be sexy

        '''
        if type not in ('start', 'stop', 'continue', 'partial'):
            raise BeamException(f'beam type cannot be {type}')
        for beam in self.beamsList:
            beam.type = type
            beam.direction = direction

    def setByNumber(self, number, type, direction=None):  # type is okay @ReservedAssignment
        '''
        Set an internal beam object by number, or rhythmic symbol level.

        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> a.setAll('start')
        >>> a.setByNumber(1, 'continue')
        >>> a.beamsList[0].type
        'continue'

        >>> a.setByNumber(2, 'stop')
        >>> a.beamsList[1].type
        'stop'

        >>> a.setByNumber(2, 'partial-right')
        >>> a.beamsList[1].type
        'partial'

        >>> a.beamsList[1].direction
        'right'

        >>> a.setByNumber(30, 'stop')
        Traceback (most recent call last):
        IndexError: beam number 30 cannot be accessed

        >>> a.setByNumber(2, 'crazy')
        Traceback (most recent call last):
        music21.beam.BeamException: beam type cannot be crazy

        '''
        # permit providing one argument hyphenated
        if '-' in type:
            type, direction = type.split('-')  # type is okay @ReservedAssignment
        if type not in ['start', 'stop', 'continue', 'partial']:
            raise BeamException(f'beam type cannot be {type}')
        if number not in self.getNumbers():
            raise IndexError(f'beam number {number} cannot be accessed')
        for i in range(len(self)):
            if self.beamsList[i].number == number:
                self.beamsList[i].type = type
                self.beamsList[i].direction = direction


# -----------------------------------------------------------------------------


class Test(unittest.TestCase):
    pass


# -----------------------------------------------------------------------------
# define presented order in documentation


_DOC_ORDER = [Beams, Beam]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
