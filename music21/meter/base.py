# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         meter.py
# Purpose:      Classes for meters
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012, 2015, 2021 Michael Scott Cuthbert
#               and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
This module defines the :class:`~music21.meter.TimeSignature` object,
as well as component objects for defining nested metrical structures,
:class:`~music21.meter.MeterTerminal` and :class:`~music21.meter.MeterSequence` objects.
'''
import copy
import fractions
from typing import Optional

from music21 import base
from music21 import beam
from music21 import common
from music21 import defaults
from music21 import duration
from music21 import environment
from music21 import style
from music21.exceptions21 import MeterException, TimeSignatureException

from music21.common.enums import MeterDivision
from music21.common.numberTools import opFrac
from music21.meter.tools import slashToTuple, proportionToFraction
from music21.meter.core import MeterSequence

environLocal = environment.Environment('meter')


# -----------------------------------------------------------------------------

# also [pow(2,x) for x in range(8)]
MIN_DENOMINATOR_TYPE = '128th'

# store a module-level dictionary of partitioned meter sequences used
# for setting default accent weights; store as needed
_meterSequenceAccentArchetypes = {}


def bestTimeSignature(meas: 'music21.stream.Stream') -> 'music21.meter.TimeSignature':
    # noinspection PyShadowingNames
    '''
    Given a Measure (or any Stream) with elements in it, get a TimeSignature that contains all
    elements.

    Note: this does not yet accommodate triplets.

    >>> s = converter.parse('tinynotation: C4 D4 E8 F8').flatten().notes
    >>> m = stream.Measure()
    >>> for el in s:
    ...     m.insert(el.offset, el)
    >>> ts = meter.bestTimeSignature(m)
    >>> ts
    <music21.meter.TimeSignature 3/4>

    >>> s2 = converter.parse('tinynotation: C8. D16 E8 F8. G16 A8').flatten().notes
    >>> m2 = stream.Measure()
    >>> for el in s2:
    ...     m2.insert(el.offset, el)
    >>> ts2 = meter.bestTimeSignature(m2)
    >>> ts2
    <music21.meter.TimeSignature 6/8>

    >>> s3 = converter.parse('C2 D2 E2', format='tinyNotation').flatten().notes
    >>> m3 = stream.Measure()
    >>> for el in s3:
    ...     m3.insert(el.offset, el)
    >>> ts3 = meter.bestTimeSignature(m3)
    >>> ts3
    <music21.meter.TimeSignature 3/2>

    >>> s4 = converter.parse('C8. D16 E8 F8. G16 A8 C4. D4.', format='tinyNotation').flatten().notes
    >>> m4 = stream.Measure()
    >>> for el in s4:
    ...     m4.insert(el.offset, el)
    >>> ts4 = meter.bestTimeSignature(m4)
    >>> ts4
    <music21.meter.TimeSignature 12/8>

    >>> s5 = converter.parse('C4 D2 E4 F2', format='tinyNotation').flatten().notes
    >>> m5 = stream.Measure()
    >>> for el in s5:
    ...     m5.insert(el.offset, el)
    >>> ts5 = meter.bestTimeSignature(m5)
    >>> ts5
    <music21.meter.TimeSignature 6/4>

    >>> s6 = converter.parse('C4 D16.', format='tinyNotation').flatten().notes
    >>> m6 = stream.Measure()
    >>> for el in s6:
    ...     m6.insert(el.offset, el)
    >>> ts6 = meter.bestTimeSignature(m6)
    >>> ts6
    <music21.meter.TimeSignature 11/32>


    Complex durations (arose in han2.abc, number 445)

    >>> m7 = stream.Measure()
    >>> m7.append(note.Note('D', quarterLength=3.5))
    >>> m7.append(note.Note('E', quarterLength=5.5))
    >>> ts7 = meter.bestTimeSignature(m7)
    >>> ts7
    <music21.meter.TimeSignature 9/4>
    '''
    minDurQL = 4  # smallest denominator; start with a whole note
    # find sum of all durations in quarter length
    # find if there are any dotted durations
    minDurDots = 0
    sumDurQL = opFrac(meas.duration.quarterLength)
    # beatStrAvg = 0
    # beatStrAvg += e.beatStrength
    numerator = 0
    denominator = 1

    for e in meas.recurse().notesAndRests:
        if e.quarterLength == 0.0:
            continue  # case of grace durations
        if (e.quarterLength < minDurQL
                and not isinstance(opFrac(e.quarterLength), fractions.Fraction)):
            # no non-power2 signatures
            minDurQL = e.quarterLength
            minDurDots = e.duration.dots

    # first, we need to evenly divide min dur into total
    minDurTest = minDurQL
    if isinstance(sumDurQL, fractions.Fraction):
        # not a power of two -- some tuplets, etc.
        numerator = sumDurQL.numerator
        denominator = sumDurQL.denominator
    else:
        i = 10
        while i > 0:
            partsFloor = int(sumDurQL / minDurTest)
            partsReal = opFrac(sumDurQL / minDurTest)
            if (partsFloor == partsReal
                    or minDurTest <= duration.typeToDuration[MIN_DENOMINATOR_TYPE]):
                break
            # need to break down minDur until we can get a match
            else:
                minDurTest = minDurTest / (2 * common.dotMultiplier(minDurDots))
            i -= 1

        # see if we can get a type for the denominator
        # if we do not have a match; we need to break down this value
        match = False
        durationMinLimit = duration.typeToDuration[MIN_DENOMINATOR_TYPE]
        i = 10
        while i > 0:
            if minDurTest < durationMinLimit:
                minDurTest = durationMinLimit
                break
            try:
                dType, match = duration.quarterLengthToClosestType(minDurTest)
            except ZeroDivisionError:
                raise MeterException('Cannot find a good match for this measure')

            if match or dType == MIN_DENOMINATOR_TYPE:
                break
            minDurTest = minDurTest / (2 * common.dotMultiplier(minDurDots))
            i -= 1

        minDurQL = minDurTest
        dType, match = duration.quarterLengthToClosestType(minDurQL)
        if not match:  # cant find a type for a denominator
            raise MeterException(f'cannot find a type for denominator {minDurQL}')

        # denominator is the numerical representation of the min type
        # e.g., quarter is 4, whole is 1
        for num, typeName in duration.typeFromNumDict.items():
            if typeName == dType:
                if num >= 1:
                    num = int(num)
                denominator = num
                break
        # numerator is the count of min parts in the sum
        multiplier = 1
        while i > 0:
            numerator = multiplier * sumDurQL / minDurQL
            if numerator == int(numerator):
                break
            multiplier *= 2
            i -= 1

        numerator = int(numerator)
        denominator *= multiplier
        # simplifies to "simplest terms," with 4 in denominator, before testing beat strengths
        gcdValue = common.euclidGCD(numerator, denominator)
        numerator = numerator // gcdValue
        denominator = denominator // gcdValue

    # simplifies rare time signatures like 16/16 and 1/1 to 4/4
    if numerator == denominator and numerator not in [2, 4]:
        numerator = 4
        denominator = 4
    elif numerator != denominator and denominator == 1:
        numerator *= 4
        denominator *= 4
    elif numerator != denominator and denominator == 2:
        numerator *= 2
        denominator *= 2

    # a fairly accurate test of whether 3/4 or 6/8 is more appropriate (see doctests)
    if numerator == 3 and denominator == 4:
        ts1 = TimeSignature('3/4')
        ts2 = TimeSignature('6/8')
        str1 = ts1.averageBeatStrength(meas)
        str2 = ts2.averageBeatStrength(meas)

        if str1 <= str2:
            return ts2
        else:
            return ts1

    # tries three time signatures if "simplest" time signature is 6/4 or 3/2
    elif numerator == 6 and denominator == 4:
        ts1 = TimeSignature('6/4')
        ts2 = TimeSignature('12/8')
        ts3 = TimeSignature('3/2')
        str1 = ts1.averageBeatStrength(meas)
        str2 = ts2.averageBeatStrength(meas)
        str3 = ts3.averageBeatStrength(meas)
        m = max(str1, str2, str3)
        if m == str1:
            return ts1
        elif m == str3:
            return ts3
        else:
            return ts2

    else:
        ts = TimeSignature()
        ts.load(f'{numerator}/{denominator}')
        return ts


# -----------------------------------------------------------------------------


class TimeSignature(base.Music21Object):
    r'''
    The `TimeSignature` object represents time signatures in musical scores
    (4/4, 3/8, 2/4+5/16, Cut, etc.).

    `TimeSignatures` should be present in the first `Measure` of each `Part`
    that they apply to.  Alternatively you can put the time signature at the
    front of a `Part` or at the beginning of a `Score` and they will work
    within music21 but they won't necessarily display properly in musicxml,
    lilypond, etc.  So best is to create structures like this:

    >>> s = stream.Score()
    >>> p = stream.Part()
    >>> m1 = stream.Measure()
    >>> ts = meter.TimeSignature('3/4')
    >>> m1.insert(0, ts)
    >>> m1.insert(0, note.Note('C#3', type='half'))
    >>> n = note.Note('D3', type='quarter')  # we will need this later
    >>> m1.insert(1.0, n)
    >>> m1.number = 1
    >>> p.insert(0, m1)
    >>> s.insert(0, p)
    >>> s.show('t')
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.note.Note C#>
            {1.0} <music21.note.Note D>

    Basic operations on a TimeSignature object are designed to be very simple.

    >>> ts.ratioString
    '3/4'

    >>> ts.numerator
    3

    >>> ts.beatCount
    3

    >>> ts.beatCountName
    'Triple'

    >>> ts.beatDuration.quarterLength
    1.0

    As an alternative to putting a `TimeSignature` in a Stream at a specific
    position (offset), it can be assigned to a special property in Measure that
    positions the TimeSignature at the start of a Measure.  Notice that when we
    `show()` the Measure (or if we iterate through it), the TimeSignature
    appears as if it's in the measure itself:

    >>> m2 = stream.Measure()
    >>> m2.number = 2
    >>> ts2 = meter.TimeSignature('2/4')
    >>> m2.timeSignature = ts2
    >>> m2.append(note.Note('E3', type='half'))
    >>> p.append(m2)
    >>> s.show('text')
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.note.Note C#>
            {1.0} <music21.note.Note D>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note E>

    Once a Note has a local TimeSignature, a Note can get its beat position and
    other meter-specific parameters.  Remember `n`, our quarter note at offset
    2.0 of `m1`, a 3/4 measure? Let's get its beat:

    >>> n.beat
    2.0

    This feature is more useful if there are more beats:

    >>> m3 = stream.Measure()
    >>> m3.timeSignature = meter.TimeSignature('3/4')
    >>> eighth = note.Note(type='eighth')
    >>> m3.repeatAppend(eighth, 6)
    >>> [thisNote.beatStr for thisNote in m3.notes]
    ['1', '1 1/2', '2', '2 1/2', '3', '3 1/2']

    Now lets change its measure's TimeSignature and see what happens:

    >>> sixEight = meter.TimeSignature('6/8')
    >>> m3.timeSignature = sixEight
    >>> [thisNote.beatStr for thisNote in m3.notes]
    ['1', '1 1/3', '1 2/3', '2', '2 1/3', '2 2/3']

    TimeSignature('6/8') defaults to fast 6/8:

    >>> sixEight.beatCount
    2

    >>> sixEight.beatDuration.quarterLength
    1.5

    >>> sixEight.beatDivisionCountName
    'Compound'

    Let's make it slow 6/8 instead:

    >>> sixEight.beatCount = 6
    >>> sixEight.beatDuration.quarterLength
    0.5

    >>> sixEight.beatDivisionCountName
    'Simple'

    Now let's look at the `beatStr` for each of the notes in `m3`:

    >>> [thisNote.beatStr for thisNote in m3.notes]
    ['1', '2', '3', '4', '5', '6']

    As of v7., 3/8 also defaults to fast 3/8, that is, one beat:

    >>> meter.TimeSignature('3/8').beatCount
    1

    `TimeSignatures` can also use symbols instead of numbers

    >>> tsCommon = meter.TimeSignature('c')  # or common
    >>> tsCommon.beatCount
    4
    >>> tsCommon.denominator
    4

    >>> tsCommon.symbol
    'common'

    >>> tsCut = meter.TimeSignature('cut')
    >>> tsCut.beatCount
    2
    >>> tsCut.denominator
    2

    >>> tsCut.symbol
    'cut'

    For other time signatures, the symbol is '' (not set) or 'normal'

    >>> sixEight.symbol
    ''


    For complete details on using this object, see
    :ref:`User's Guide Chapter 14: Time Signatures <usersGuide_14_timeSignatures>` and
    :ref:`User's Guide Chapter 55: Advanced Meter <usersGuide_55_advancedMeter>` and


    That's it for the simple aspects of `TimeSignature` objects.  You know
    enough to get started now!

    Under the hood, they're extremely powerful.  For musicians, TimeSignatures
    do (at least) three different things:

    * They define where the beats in the measure are and how many there are.

    * They indicate how the notes should be beamed

    * They give a sense of how much accent or weight each note gets, which
      also defines which are important notes and which might be ornaments.

    These three aspects of `TimeSignatures` are controlled by the
    :attr:`~music21.meter.TimeSignature.beatSequence`,
    :attr:`~music21.meter.TimeSignature.beamSequence`, and
    :attr:`~music21.meter.TimeSignature.accentSequence` properties of the
    `TimeSignature`.  Each of them is an independent
    :class:`~music21.meter.MeterSequence` element which might have nested
    properties (e.g., a 11/16 meter might be beamed as {1/4+1/4+{1/8+1/16}}),
    so if you want to change how beats are calculated or beams are generated
    you'll want to learn more about `meter.MeterSequence` objects.

    There's a fourth `MeterSequence` object inside a TimeSignature, and that is
    the :attr:`~music21.meter.TimeSignature.displaySequence`. That determines
    how the `TimeSignature` should actually look on paper.  Normally this
    `MeterSequence` is pretty simple.  In '4/4' it's usually just '4/4'.  But
    if you have the '11/16' time above, you may want to have it displayed as
    '2/4+3/16' or '11/16 (2/4+3/16)'.  Or you might want the written
    TimeSignature to contradict what the notes imply.  All this can be done
    with .displaySequence.
    '''
    _styleClass = style.TextStyle
    classSortOrder = 4

    _DOC_ATTR = {
        'beatSequence': 'A :class:`~music21.meter.MeterSequence` governing beat partitioning.',
        'beamSequence': 'A :class:`~music21.meter.MeterSequence` governing automatic beaming.',
        'accentSequence': 'A :class:`~music21.meter.MeterSequence` governing accent partitioning.',
        'displaySequence': '''
            A :class:`~music21.meter.MeterSequence` governing the display of the TimeSignature.''',
        'symbol': '''
            A string representation of how to display the TimeSignature.
            can be "common", "cut", "single-number" (i.e.,
            no denominator), or "normal" or "".''',
        'symbolizeDenominator': '''
            If set to `True` (default is `False`) then the denominator
            will be displayed as a symbol rather than
            a number.  Hindemith uses this in his scores.
            Finale and other MusicXML readers do not support this
            so do not expect proper output yet.''',
    }

    def __init__(self, value: str = '4/4', divisions=None):
        super().__init__()

        if value is None:
            value = f'{defaults.meterNumerator}/{defaults.meterDenominatorBeatType}'

        self._overriddenBarDuration = None
        self.symbol = ''
        self.displaySequence: Optional[MeterSequence] = None
        self.beatSequence: Optional[MeterSequence] = None
        self.accentSequence: Optional[MeterSequence] = None
        self.beamSequence: Optional[MeterSequence] = None
        self.symbolizeDenominator = False

        self.resetValues(value, divisions)

    def _reprInternal(self):
        return self.ratioString

    def resetValues(self, value: str = '4/4', divisions=None):
        '''
        reset all values according to a new value and optionally, the number of
        divisions.
        '''
        self.symbol = ''  # common, cut, single-number, normal

        # a parameter to determine if the denominator is represented
        # as either a symbol (a note) or as a number
        self.symbolizeDenominator = False

        self._overriddenBarDuration = None

        # creates MeterSequence data representations
        # creates .displaySequence, .beamSequence, .beatSequence, .accentSequence
        self.load(value, divisions)

    def load(self, value: str, divisions=None):
        '''
        Load up a TimeSignature with a string value.

        >>> ts = meter.TimeSignature()
        >>> ts.load('4/4')
        >>> ts
        <music21.meter.TimeSignature 4/4>

        >>> ts.load('c')
        >>> ts.symbol
        'common'


        >>> ts.load('2/4+3/8')
        >>> ts
        <music21.meter.TimeSignature 2/4+3/8>


        >>> ts.load('fast 6/8')
        >>> ts.beatCount
        2
        >>> ts.load('slow 6/8')
        >>> ts.beatCount
        6

        Loading destroys all preexisting internal representations
        '''
        # create parallel MeterSequence objects to provide all data
        # these all refer to the same .numerator/.denominator
        # relationship

        # used for drawing the time signature symbol
        # this is the only one that can be  unlinked
        if value.lower() in ('common', 'c'):
            value = '4/4'
            self.symbol = 'common'
        elif value.lower() in ('cut', 'allabreve'):
            # allaBreve is the capella version
            value = '2/2'
            self.symbol = 'cut'

        self.displaySequence = MeterSequence(value)

        # get simple representation; presently, only slashToTuple
        # supports the fast/slow indication
        numerator, denominator, division = slashToTuple(value)
        if division == MeterDivision.NONE:
            if numerator % 3 == 0 and denominator >= 8:
                division = MeterDivision.FAST
            elif numerator == 3:
                division = MeterDivision.SLOW
        favorCompound = (division != MeterDivision.SLOW)

        # used for beaming
        self.beamSequence = MeterSequence(value, divisions)
        # used for getting beat divisions
        self.beatSequence = MeterSequence(value, divisions)

        # accentSequence is used for setting one level of accents
        self.accentSequence = MeterSequence(value, divisions)

        if divisions is None:  # set default beam partitions
            # beam is not adjust by tempo indication
            self._setDefaultBeamPartitions()
            self._setDefaultBeatPartitions(favorCompound=favorCompound)

            # for some summed meters default accent weights are difficult
            # to obtain
            try:
                self._setDefaultAccentWeights(3)  # set partitions based on beat
            except MeterException:
                environLocal.printDebug(['cannot set default accents for:', self])

    @common.deprecated('v7', 'v8', 'call .ratioString or .load()')
    def loadRatio(self, numerator, denominator, divisions=None):  # pragma: no cover
        '''
        Change the numerator and denominator, like ratioString, but with
        optional divisions and without resetting other parameters.

        DEPRECATED in v7. -- call .ratioString or .load with
        value = f'{numerator}/{denominator}'
        '''
        value = f'{numerator}/{denominator}'
        self.load(value, divisions)

    @property
    def ratioString(self):
        '''
        Returns or sets a simple string representing the time signature ratio.

        >>> threeFour = meter.TimeSignature('3/4')
        >>> threeFour.ratioString
        '3/4'

        It can also be set to load a new one, but '.load()' is better...

        >>> threeFour.ratioString = '5/8'  # now this variable name is dumb!
        >>> threeFour.numerator
        5
        >>> threeFour.denominator
        8

        >>> complexTime = meter.TimeSignature('2/4+3/8')
        >>> complexTime.ratioString
        '2/4+3/8'

        For advanced users, getting the ratioString is the equivalent of
        :attr:`~music21.meter.core.MeterSequence.partitionDisplay` on the displaySequence:

        >>> complexTime.displaySequence.partitionDisplay
        '2/4+3/8'
        '''
        return self.displaySequence.partitionDisplay

    @ratioString.setter
    def ratioString(self, newRatioString):
        self.resetValues(newRatioString)

    def ratioEqual(self, other):
        '''
        A basic form of comparison; does not determine if any internal structures are equal; o
        only outermost ratio.
        '''
        if other is None:
            return False
        if (other.numerator == self.numerator
                and other.denominator == self.denominator):
            return True
        else:
            return False

    # --------------------------------------------------------------------------
    # properties

    @property
    def numerator(self):
        '''
        Return the numerator of the TimeSignature as a number.

        Can set the numerator for a simple TimeSignature.
        To set the numerator of a complex TimeSignature, change beatCount.

        (for complex TimeSignatures, note that this comes from the .beamSequence
        of the TimeSignature)


        >>> ts = meter.TimeSignature('3/4')
        >>> ts.numerator
        3
        >>> ts.numerator = 5
        >>> ts
        <music21.meter.TimeSignature 5/4>


        In this case, the TimeSignature is silently being converted to 9/8
        to get a single digit numerator:

        >>> ts = meter.TimeSignature('2/4+5/8')
        >>> ts.numerator
        9

        Setting a summed time signature's numerator will change to a
        simple time signature

        >>> ts.numerator = 11
        >>> ts
        <music21.meter.TimeSignature 11/8>
        '''
        return self.beamSequence.numerator

    @numerator.setter
    def numerator(self, value):
        denominator = self.denominator
        newRatioString = str(value) + '/' + str(denominator)
        self.resetValues(newRatioString)


    @property
    def denominator(self):
        '''
        Return the denominator of the TimeSignature as a number or set it.

        (for complex TimeSignatures, note that this comes from the .beamSequence
        of the TimeSignature)

        >>> ts = meter.TimeSignature('3/4')
        >>> ts.denominator
        4
        >>> ts.denominator = 8
        >>> ts.ratioString
        '3/8'


        In this following case, the TimeSignature is silently being converted to 9/8
        to get a single digit denominator:

        >>> ts = meter.TimeSignature('2/4+5/8')
        >>> ts.denominator
        8
        '''
        return self.beamSequence.denominator

    @denominator.setter
    def denominator(self, value):
        numeratorValue = self.numerator
        newRatioString = str(numeratorValue) + '/' + str(value)
        self.resetValues(newRatioString)

    @property
    def barDuration(self) -> duration.Duration:
        '''
        Return a :class:`~music21.duration.Duration` object equal to the
        total length of this TimeSignature.

        >>> ts = meter.TimeSignature('5/16')
        >>> ts.barDuration
        <music21.duration.Duration 1.25>

        >>> ts2 = meter.TimeSignature('3/8')
        >>> d = ts2.barDuration
        >>> d.type
        'quarter'
        >>> d.dots
        1
        >>> d.quarterLength
        1.5

        This can be overridden to create different representations
        or to contradict the meter.

        >>> d2 = duration.Duration(1.75)
        >>> ts2.barDuration = d2
        >>> ts2.barDuration
        <music21.duration.Duration 1.75>
        '''

        if self._overriddenBarDuration:
            return self._overriddenBarDuration
        else:
            # could come from self.beamSequence, self.accentSequence,
            #   self.displaySequence, self.accentSequence
            return self.beamSequence.duration

    @barDuration.setter
    def barDuration(self, value: duration.Duration):
        self._overriddenBarDuration = value

    @property
    def beatLengthToQuarterLengthRatio(self):
        '''
        Returns 4.0 / denominator... seems a bit silly...

        >>> a = meter.TimeSignature('3/2')
        >>> a.beatLengthToQuarterLengthRatio
        2.0
        '''
        return 4 / self.denominator

    @property
    def quarterLengthToBeatLengthRatio(self):
        '''
        Returns denominator/4.0... seems a bit silly...
        '''
        return self.denominator / 4.0

    # --------------------------------------------------------------------------
    # meter classifications used for classifying meters such as
    # duple triple, etc.

    @property
    def beatCount(self):
        '''
        Return or set the count of beat units, or the number of beats in this TimeSignature.

        When setting beat units, one level of sub-partitions is automatically defined.
        Users can specify beat count values as integers or as lists of durations.
        For more precise configuration of the beat MeterSequence,
        manipulate the .beatSequence attribute directly.

        >>> ts = meter.TimeSignature('3/4')
        >>> ts.beatCount
        3
        >>> ts.beatDuration.quarterLength
        1.0
        >>> ts.beatCount = [1, 1, 1, 1, 1, 1]
        >>> ts.beatCount
        6
        >>> ts.beatDuration.quarterLength
        0.5

        Setting a beat-count directly is a simple, high-level way to configure the beatSequence.
        Note that his may not configure lower level partitions correctly,
        and will raise an error if the provided beat count is not supported by the
        overall duration of the .beatSequence MeterSequence.

        >>> ts = meter.TimeSignature('6/8')
        >>> ts.beatCount  # default is 2 beats
        2
        >>> ts.beatSequence
        <music21.meter.core.MeterSequence {{1/8+1/8+1/8}+{1/8+1/8+1/8}}>
        >>> ts.beatDivisionCountName
        'Compound'
        >>> ts.beatCount = 6
        >>> ts.beatSequence
        <music21.meter.core.MeterSequence
            {{1/16+1/16}+{1/16+1/16}+{1/16+1/16}+{1/16+1/16}+{1/16+1/16}+{1/16+1/16}}>
        >>> ts.beatDivisionCountName
        'Simple'
        >>> ts.beatCount = 123
        Traceback (most recent call last):
        music21.exceptions21.TimeSignatureException: cannot partition beat with provided value: 123

        >>> ts = meter.TimeSignature('3/4')
        >>> ts.beatCount = 6
        >>> ts.beatDuration.quarterLength
        0.5
        '''
        # the default is for the beat to be defined by the first, not zero,
        # level partition.
        return len(self.beatSequence)

    @beatCount.setter
    def beatCount(self, value):
        try:
            self.beatSequence.partition(value)
        except MeterException:
            raise TimeSignatureException(f'cannot partition beat with provided value: {value}')
        # create subdivisions using default parameters
        if len(self.beatSequence) > 1:  # if partitioned
            self.beatSequence.subdividePartitionsEqual()

    @property
    def beatCountName(self):
        '''
        Return the beat count name, or the name given for the number of beat units.
        For example, 2/4 is duple; 9/4 is triple.

        >>> ts = meter.TimeSignature('3/4')
        >>> ts.beatCountName
        'Triple'

        >>> ts = meter.TimeSignature('6/8')
        >>> ts.beatCountName
        'Duple'
        '''
        return self.beatSequence.partitionStr

    @property
    def beatDuration(self) -> duration.Duration:
        '''
        Return a :class:`~music21.duration.Duration` object equal to the beat unit
        of this Time Signature, if and only if this TimeSignature has a uniform beat unit.

        Otherwise raises an exception in v7.1 but will change to returning NaN
        soon fasterwards.

        >>> ts = meter.TimeSignature('3/4')
        >>> ts.beatDuration
        <music21.duration.Duration 1.0>
        >>> ts = meter.TimeSignature('6/8')
        >>> ts.beatDuration
        <music21.duration.Duration 1.5>

        >>> ts = meter.TimeSignature('7/8')
        >>> ts.beatDuration
        <music21.duration.Duration 0.5>

        >>> ts = meter.TimeSignature('3/8')
        >>> ts.beatDuration
        <music21.duration.Duration 1.5>
        >>> ts.beatCount = 3
        >>> ts.beatDuration
        <music21.duration.Duration 0.5>

        Cannot do this because of asymmetry

        >>> ts = meter.TimeSignature('2/4+3/16')
        >>> ts.beatDuration
        Traceback (most recent call last):
        music21.exceptions21.TimeSignatureException: non-uniform beat unit: [2.0, 0.75]

        Changed in v7. -- return NaN rather than raising Exception in property.
        '''
        post = []
        for ms in self.beatSequence:
            post.append(ms.duration.quarterLength)
        if len(set(post)) == 1:
            return self.beatSequence[0].duration  # all are the same
        else:
            raise TimeSignatureException(f'non-uniform beat unit: {post}')

    @property
    def beatDivisionCount(self):
        '''
        Return the count of background beat units found within one beat,
        or the number of subdivisions in the beat unit in this TimeSignature.

        >>> ts = meter.TimeSignature('3/4')
        >>> ts.beatDivisionCount
        2

        >>> ts = meter.TimeSignature('6/8')
        >>> ts.beatDivisionCount
        3

        >>> ts = meter.TimeSignature('15/8')
        >>> ts.beatDivisionCount
        3

        >>> ts = meter.TimeSignature('3/8')
        >>> ts.beatDivisionCount
        1

        >>> ts = meter.TimeSignature('13/8', 13)
        >>> ts.beatDivisionCount
        1

        Changed in v7. -- return 1 instead of a TimeSignatureException.
        '''
        # first, find if there is more than one beat and if all beats are uniformly partitioned
        post = []
        if len(self.beatSequence) == 1:
            return 1

        # need to see if first-level subdivisions are partitioned
        if not isinstance(self.beatSequence[0], MeterSequence):
            return 1

        # getting length here gives number of subdivisions
        for ms in self.beatSequence:
            post.append(len(ms))

        # convert this to a set; if length is 1, then all beats are uniform
        if len(set(post)) == 1:
            return len(self.beatSequence[0])  # all are the same
        else:
            return 1

    @property
    def beatDivisionCountName(self):
        '''
        Return the beat count name, or the name given for the number of beat units.
        For example, 2/4 is duple; 9/4 is triple.

        >>> ts = meter.TimeSignature('3/4')
        >>> ts.beatDivisionCountName
        'Simple'

        >>> ts = meter.TimeSignature('6/8')
        >>> ts.beatDivisionCountName
        'Compound'

        Rare cases of 5-beat divisions return 'Other', like this 10/8 divided into
        5/8 + 5/8 with no further subdivisions:

        >>> ts = meter.TimeSignature('10/8')
        >>> ts.beatSequence.partition(2)
        >>> ts.beatSequence
        <music21.meter.core.MeterSequence {5/8+5/8}>
        >>> for i, mt in enumerate(ts.beatSequence):
        ...     ts.beatSequence[i] = mt.subdivideByCount(5)
        >>> ts.beatSequence
        <music21.meter.core.MeterSequence {{1/8+1/8+1/8+1/8+1/8}+{1/8+1/8+1/8+1/8+1/8}}>
        >>> ts.beatDivisionCountName
        'Other'
        '''
        beatDivision = self.beatDivisionCount
        if beatDivision == 2:
            return 'Simple'
        elif beatDivision == 3:
            return 'Compound'
        else:
            return 'Other'

    @property
    def beatDivisionDurations(self):
        '''
        Return the beat division, or the durations that make up one beat,
        as a list of :class:`~music21.duration.Duration` objects, if and only if
        the TimeSignature has a uniform beat division for all beats.

        >>> ts = meter.TimeSignature('3/4')
        >>> ts.beatDivisionDurations
        [<music21.duration.Duration 0.5>,
         <music21.duration.Duration 0.5>]

        >>> ts = meter.TimeSignature('6/8')
        >>> ts.beatDivisionDurations
        [<music21.duration.Duration 0.5>,
         <music21.duration.Duration 0.5>,
         <music21.duration.Duration 0.5>]

        Value returned of non-uniform beat divisions will change at any time
        after v7.1 to avoid raising an exception.
        '''
        post = []
        if len(self.beatSequence) == 1:
            raise TimeSignatureException(
                'cannot determine beat division for a non-partitioned beat')
        for mt in self.beatSequence:
            for subMt in mt:
                post.append(subMt.duration.quarterLength)
        if len(set(post)) == 1:  # all the same
            out = []
            for subMt in self.beatSequence[0]:
                out.append(subMt.duration)
            return out
        else:
            raise TimeSignatureException(f'non uniform beat division: {post}')

    @property
    def beatSubDivisionDurations(self):
        '''
        Return a subdivision of the beat division, or a list
        of :class:`~music21.duration.Duration` objects representing each beat division
        divided by two.

        >>> ts = meter.TimeSignature('3/4')
        >>> ts.beatSubDivisionDurations
        [<music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>,
         <music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>]

        >>> ts = meter.TimeSignature('6/8')
        >>> ts.beatSubDivisionDurations
        [<music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>,
         <music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>,
         <music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>]
        '''
        post = []
        src = self.beatDivisionDurations
        for d in src:
            # this is too slow... TODO: fix, but make sure all durations are unique.
            post.append(d.augmentOrDiminish(0.5))
            post.append(d.augmentOrDiminish(0.5))
        return post

    @property
    def classification(self):
        '''
        Return the classification of this TimeSignature,
        such as Simple Triple or Compound Quadruple.

        >>> ts = meter.TimeSignature('3/4')
        >>> ts.classification
        'Simple Triple'
        >>> ts = meter.TimeSignature('6/8')
        >>> ts.classification
        'Compound Duple'
        >>> ts = meter.TimeSignature('4/32')
        >>> ts.classification
        'Simple Quadruple'
        '''
        return f'{self.beatDivisionCountName} {self.beatCountName}'

    @property
    def summedNumerator(self) -> bool:
        if self.displaySequence is None:
            return False
        return self.displaySequence.summedNumerator

    @summedNumerator.setter
    def summedNumerator(self, value: bool):
        if self.displaySequence is not None:
            self.displaySequence.summedNumerator = value

    # --------------------------------------------------------------------------
    # private methods -- most to be put into the various sequences.

    def _setDefaultBeatPartitions(self, *, favorCompound=True):
        '''Set default beat partitions based on numerator and denominator.

        >>> ts = meter.TimeSignature('3/4')
        >>> len(ts.beatSequence)  # first, not zeroth, level stores beat
        3
        >>> ts = meter.TimeSignature('6/8')
        >>> len(ts.beatSequence)
        2
        >>> ts = meter.TimeSignature('slow 6/8')
        >>> len(ts.beatSequence)
        6

        Changed in v7 -- favorCompound is keyword only
        '''
        # if a non-compound meter has been given, as in
        # not 3+1/4; just 5/4
        if len(self.displaySequence) == 1:
            # create toplevel partitions
            if self.numerator == 2:  # duple meters
                self.beatSequence.partition(2)
            elif self.numerator == 6 and favorCompound:  # duple meters
                self.beatSequence.partition(2)
            elif self.numerator == 3 and favorCompound:  # 3/8, 3/16, but not 3/4
                self.beatSequence.partition(1)
            elif self.numerator == 3:  # triple meters
                self.beatSequence.partition([1, 1, 1])
            elif self.numerator == 9 and favorCompound:  # triple meters
                self.beatSequence.partition([3, 3, 3])
            elif self.numerator == 4:  # quadruple meters
                self.beatSequence.partition(4)
            elif self.numerator == 12 and favorCompound:
                self.beatSequence.partition(4)
            elif self.numerator >= 15 and self.numerator % 3 == 0 and favorCompound:
                # quintuple meters and above.
                num_triples = self.numerator // 3
                self.beatSequence.partition([3] * num_triples)
            # skip 6 numerators; covered above
            else:  # case of odd meters: 11, 13
                self.beatSequence.partition(self.numerator)

        # if a complex meter has been given
        else:  # partition by display
            # TODO: remove partitionByMeterSequence usage.
            self.beatSequence.partition(self.displaySequence)

        # create subdivisions, and thus define compound/simple distinction
        if len(self.beatSequence) > 1:  # if partitioned
            try:
                self.beatSequence.subdividePartitionsEqual()
            except MeterException:
                if self.denominator >= 128:
                    pass  # do not raise an exception for unable to subdivide smaller than 128

    def _setDefaultBeamPartitions(self):
        '''
        This sets default beam partitions when partitionRequest is None.
        '''
        # beam short measures of 8ths, 16ths, or 32nds all together
        if self.beamSequence.summedNumerator:
            pass  # do not mess with a numerator such as (3+2)/8
        elif self.denominator == 8 and self.numerator in (1, 2, 3):
            pass  # doing nothing will beam all together
        elif self.denominator == 16 and self.numerator in range(1, 6):
            # 1 - 5 -- beam all together
            pass
        elif self.denominator == 32 and self.numerator in range(1, 12):
            # 1 - 11 -- beam all together.
            pass

        # more general, based only on numerator
        elif self.numerator in (2, 3, 4):
            self.beamSequence.partition(self.numerator)
            # if denominator is 4, subdivide each partition
            if self.denominator == 4:
                for i in range(len(self.beamSequence)):  # subdivide  each beat in 2
                    self.beamSequence[i] = self.beamSequence[i].subdivide(2)
        elif self.numerator == 5:
            default = [2, 3]
            self.beamSequence.partition(default)
            # if denominator is 4, subdivide each partition
            if self.denominator == 4:
                for i in range(len(self.beamSequence)):  # subdivide  each beat in 2
                    self.beamSequence[i] = self.beamSequence[i].subdivide(default[i])

        elif self.numerator == 7:
            self.beamSequence.partition(3)  # divide into three groups

        elif self.numerator in [6, 9, 12, 15, 18, 21]:
            self.beamSequence.partition([3] * int(self.numerator / 3))
        else:
            pass  # doing nothing will beam all together
        # environLocal.printDebug('default beam partitions set to: %s' % self.beamSequence)

    def _setDefaultAccentWeights(self, depth=3):
        '''
        This sets default accent weights based on common hierarchical notions for meters;
        each beat is given a weight, as defined by the top level count of self.beatSequence

        >>> ts1 = meter.TimeSignature('4/4')
        >>> ts1._setDefaultAccentWeights(4)
        >>> [mt.weight for mt in ts1.accentSequence]
        [1.0, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625,
         0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625]

        >>> ts2 = meter.TimeSignature('3/4')
        >>> ts2._setDefaultAccentWeights(4)
        >>> [mt.weight for mt in ts2.accentSequence]
        [1.0, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625,
         0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625,
         0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625]

        >>> ts2._setDefaultAccentWeights(3)  # lower depth
        >>> [mt.weight for mt in ts2.accentSequence]
        [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]

        '''
        # NOTE: this is a performance critical method

        # create a scratch MeterSequence for structure
        tsStr = f'{self.numerator}/{self.denominator}'
        if self.beatSequence.isUniformPartition():
            if len(self.beatSequence) > 1:
                firstPartitionForm = len(self.beatSequence)
            else:
                firstPartitionForm = None
            cacheKey = (tsStr, firstPartitionForm, depth)
        else:  # derive from meter sequence
            firstPartitionForm = self.beatSequence
            cacheKey = None  # cannot cache based on beat form

        # environLocal.printDebug(['_setDefaultAccentWeights(): firstPartitionForm set to',
        #    firstPartitionForm, 'self.beatSequence: ', self.beatSequence, tsStr])
        # using cacheKey speeds up TS creation from 2300 microseconds to 500microseconds
        try:
            self.accentSequence = copy.deepcopy(
                _meterSequenceAccentArchetypes[cacheKey]
            )
            # environLocal.printDebug(['using stored accent archetype:'])
        except KeyError:
            # environLocal.printDebug(['creating a new accent archetype'])
            ms = MeterSequence(tsStr)
            # key operation here
            # div count needs to be the number of top-level beat divisions
            ms.subdivideNestedHierarchy(depth,
                                        firstPartitionForm=firstPartitionForm)

            # provide a partition for each flat division
            accentCount = len(ms.flat)
            # environLocal.printDebug(['got accentCount', accentCount, 'ms: ', ms])
            divStep = self.barDuration.quarterLength / accentCount
            weightInts = [0] * accentCount  # weights as integer/depth counts
            for i in range(accentCount):
                ql = i * divStep
                weightInts[i] = ms.offsetToDepth(ql, align='quantize', index=i)

            maxInt = max(weightInts)
            weightValues = {}  # reference dictionary
            # minimum value, something like 1/16., to be multiplied by powers of 2
            weightValueMin = 1 / pow(2, maxInt - 1)
            for x in range(maxInt):
                # multiply base value (0.125) by 1, 2, 4
                # there is never a 0 integer weight, so add 1 to dictionary
                weightValues[x + 1] = weightValueMin * pow(2, x)

            # set weights on accent partitions
            self.accentSequence.partition([1] * accentCount)
            for i in range(accentCount):
                # get values from weightValues dictionary
                self.accentSequence[i].weight = weightValues[weightInts[i]]

            if cacheKey is not None:
                _meterSequenceAccentArchetypes[cacheKey] = copy.deepcopy(self.accentSequence)

    # --------------------------------------------------------------------------
    # access data for other processing
    def getBeams(self, srcList, measureStartOffset=0.0):
        '''
        Given a qLen position and an iterable of Music21Objects, return a list of Beams objects.

        The iterable can be a list (of elements) or a Stream (preferably flat)
        or a :class:`~music21.stream.iterator.StreamIterator` from which Durations
        and information about note vs. rest will be
        extracted.

        Objects are assumed to be adjoining; offsets are not used, except for
        measureStartOffset()

        Must process a list/Stream at time, because we cannot tell when a beam ends
        unless we see the context of adjoining durations.


        >>> a = meter.TimeSignature('2/4', 2)
        >>> a.beamSequence[0] = a.beamSequence[0].subdivide(2)
        >>> a.beamSequence[1] = a.beamSequence[1].subdivide(2)
        >>> a.beamSequence
        <music21.meter.core.MeterSequence {{1/8+1/8}+{1/8+1/8}}>
        >>> b = [note.Note(type='16th') for _ in range(8)]
        >>> c = a.getBeams(b)
        >>> len(c) == len(b)
        True
        >>> print(c)
        [<music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>,
         <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>,
         <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/start>>,
         <music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>,
         <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>,
         <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>,
         <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/start>>,
         <music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>]

        >>> a = meter.TimeSignature('6/8')
        >>> b = [note.Note(type='eighth') for _ in range(6)]
        >>> c = a.getBeams(b)
        >>> print(c)
        [<music21.beam.Beams <music21.beam.Beam 1/start>>,
         <music21.beam.Beams <music21.beam.Beam 1/continue>>,
         <music21.beam.Beams <music21.beam.Beam 1/stop>>,
         <music21.beam.Beams <music21.beam.Beam 1/start>>,
         <music21.beam.Beams <music21.beam.Beam 1/continue>>,
         <music21.beam.Beams <music21.beam.Beam 1/stop>>]

        >>> fourFour = meter.TimeSignature('4/4')
        >>> nList = [note.Note(type=d) for d in ('eighth', 'quarter', 'eighth',
        ...                                      'eighth', 'quarter', 'eighth')]
        >>> beamList = fourFour.getBeams(nList)
        >>> print(beamList)
        [None, None, None, None, None, None]

        Pickup measure support included by taking in an additional measureStartOffset argument.

        >>> twoTwo = meter.TimeSignature('2/2')
        >>> nList = [note.Note(type='eighth') for _ in range(5)]
        >>> beamList = twoTwo.getBeams(nList, measureStartOffset=1.5)
        >>> print(beamList)
        [None,
         <music21.beam.Beams <music21.beam.Beam 1/start>>,
         <music21.beam.Beams <music21.beam.Beam 1/continue>>,
         <music21.beam.Beams <music21.beam.Beam 1/continue>>,
         <music21.beam.Beams <music21.beam.Beam 1/stop>>]

        Fixed in v.7 -- incomplete final measures in 6/8:

        >>> sixEight = meter.TimeSignature('6/8')
        >>> nList = [note.Note(type='quarter'), note.Note(type='eighth'), note.Note(type='eighth')]
        >>> beamList = sixEight.getBeams(nList)
        >>> print(beamList)
        [None, None, None]

        And Measure objects with :attr:`~music21.stream.Measure.paddingRight` set:

        >>> twoFour = meter.TimeSignature('2/4')
        >>> m = stream.Measure([note.Note(type='eighth') for _ in range(3)])
        >>> m.paddingRight = 0.5
        >>> twoFour.getBeams(m)
        [<music21.beam.Beams <music21.beam.Beam 1/start>>,
         <music21.beam.Beams <music21.beam.Beam 1/stop>>,
         None]
        '''
        from music21 import stream
        if isinstance(srcList, stream.Stream):
            srcStream = srcList
            srcList = list(srcList)  # do not change to [srcList]
        elif srcList and isinstance(srcList[0], base.Music21Object):
            # make into a stream to get proper offsets:
            # for eventually removing measureStartOffset
            srcStream = stream.Measure()
            srcStream.append(srcList)
        else:
            return []

        if len(srcList) <= 1:
            return [None for _ in srcList]

        beamsList = beam.Beams.naiveBeams(srcList)  # hold maximum Beams objects, all with type None
        beamsList = beam.Beams.removeSandwichedUnbeamables(beamsList)

        def fixBeamsOneElementDepth(i, el, depth):
            beams = beamsList[i]
            if beams is None:
                return

            beamNumber = depth + 1
            # see if there is a component defined for this beam number
            # if not, continue
            if beamNumber not in beams.getNumbers():
                return

            dur = el.duration
            pos = el.offset + measureStartOffset

            start = opFrac(pos)
            end = opFrac(pos + dur.quarterLength)
            startNext = end

            isLast = (i == len(srcList) - 1)
            isFirst = (i == 0)

            beamNext = beamsList[i + 1] if not isLast else None
            beamPrevious = beamsList[i - 1] if not isFirst else None

            # get an archetype of the MeterSequence for this level
            # level is depth, starting at zero
            archetype = self.beamSequence.getLevel(depth)
            # span is the quarter note duration points for each partition
            # at this level
            archetypeSpanStart, archetypeSpanEnd = archetype.offsetToSpan(start)
            # environLocal.printDebug(['at level, got archetype span', depth,
            #                         archetypeSpan])

            if beamNext is None:  # last note or before a non-beamable note (half, whole, etc.)
                archetypeSpanNextStart = 0.0
            else:
                archetypeSpanNextStart = archetype.offsetToSpan(startNext)[0]

            # watch for a special case where a duration completely fills
            # the archetype; this generally should not be beamed
            # same if beamPrevious is None and beamNumber == 1 (quarter-eighth in 6/8)
            if end == archetypeSpanEnd and (
                start == archetypeSpanStart
                or (beamPrevious is None and beamNumber == 1)
            ):
                # increment position and continue loop
                beamsList[i] = None  # replace with None!
                return

            # determine beamType
            # if first w/o pickup, always start
            if isFirst and measureStartOffset == 0:
                beamType = 'start'
                # get a partial beam if we cannot continue this
                if (beamNext is None
                        or beamNumber not in beamNext.getNumbers()):
                    beamType = 'partial-right'

            # if last in complete measure or not in a measure, always stop
            elif isLast and (not srcStream.isMeasure or srcStream.paddingRight == 0.0):
                beamType = 'stop'
                # get a partial beam if we cannot form a beam
                if (beamPrevious is None
                        or beamNumber not in beamPrevious.getNumbers()):
                    # environLocal.warn(['triggering partial left where a stop normally falls'])
                    beamType = 'partial-left'

            # here on we know that it is neither the first nor last

            # if last beam was not defined, we need to either
            # start or have a partial left beam
            # or, if beam number was not active in last beams
            elif beamPrevious is None or beamNumber not in beamPrevious.getNumbers():
                if beamNumber == 1 and beamNext is None:
                    beamsList[i] = None
                    return
                elif beamNext is None and beamNumber > 1:
                    beamType = 'partial-left'

                elif startNext >= archetypeSpanEnd:
                    # case of where we need a partial left:
                    # if the next start value is outside of this span (or at the
                    # the greater boundary of this span), and we did not have a
                    # beam or beam number in the previous beam

                    # first note in pickup measures might also get 'partial-left'
                    # here, but this gets fixed in sanitize partial beams

                    # may need to check: beamNext is not None and
                    #   beamNumber in beamNext.getNumbers()
                    # note: it is critical that we check archetypeSpan here
                    # not archetypeSpanNext
                    # environLocal.printDebug(['matching partial left'])
                    beamType = 'partial-left'
                elif beamNext is None or beamNumber not in beamNext.getNumbers():
                    beamType = 'partial-right'
                else:
                    beamType = 'start'

            # last beams was active, last beamNumber was active,
            # and it was stopped or was a partial-left
            elif (beamPrevious is not None
                    and beamNumber in beamPrevious.getNumbers()
                    and beamPrevious.getTypeByNumber(beamNumber) in ['stop', 'partial-left']):
                if beamNext is not None:
                    beamType = 'start' if beamNumber in beamNext.getNumbers() else 'partial-right'

                # last note had beams but stopped, next note cannot be beamed to
                # was active, last beamNumber was active,
                # and it was stopped or was a partial-left
                else:
                    beamType = 'partial-left'  # will be deleted later in the script

            # if no beam is defined next (we know this already)
            # then must stop
            elif (beamNext is None
                  or beamNumber not in beamNext.getNumbers()):
                beamType = 'stop'

            # the last cases are when to stop, or when to continue
            # when we know we have a beam next

            # we continue if the next beam is in the same beaming archetype
            # as this one.
            # if endNext is outside of the archetype span,
            # not sure what to do
            elif startNext < archetypeSpanEnd:
                # environLocal.printDebug(['continue match: dur.type, startNext, archetypeSpan',
                #   dur.type, startNext, archetypeSpan])
                beamType = 'continue'

            # we stop if the next beam is not in the same beaming archetype
            # and (as shown above) a valid beam number is not previous
            elif startNext >= archetypeSpanNextStart:
                beamType = 'stop'

            else:
                raise TimeSignatureException('cannot match beamType')

            # debugging information displays:
            # if beamPrevious is not None:
            #     environLocal.printDebug(['beamPrevious', beamPrevious,
            #     'beamPrevious.getNumbers()', beamPrevious.getNumbers(),
            #        'beamPrevious.getByNumber(beamNumber).type'])
            #
            #     if beamNumber in beamPrevious.getNumbers():
            #         environLocal.printDebug(['beamPrevious type',
            #            beamPrevious.getByNumber(beamNumber).type])

            # environLocal.printDebug(['beamNumber, start, archetypeSpan, beamType',
            # beamNumber, start, dur.type, archetypeSpan, beamType])

            beams.setByNumber(beamNumber, beamType)

        # environLocal.printDebug(['beamsList', beamsList])
        # iter over each beams line, from top to bottom (1 through 5)
        for outer_depth in range(len(beam.beamableDurationTypes)):
            # increment to count from 1 not 0
            # assume we are always starting at offset w/n this meter (Jose)
            for outer_i, outer_el in enumerate(srcList):
                fixBeamsOneElementDepth(outer_i, outer_el, outer_depth)

        beamsList = beam.Beams.sanitizePartialBeams(beamsList)
        beamsList = beam.Beams.mergeConnectingPartialBeams(beamsList)

        return beamsList

    def setDisplay(self, value, partitionRequest=None):
        '''
        Set an independent display value for a meter.

        >>> a = meter.TimeSignature()
        >>> a.load('3/4')
        >>> a.setDisplay('2/8+2/8+2/8')
        >>> a.displaySequence
        <music21.meter.core.MeterSequence {2/8+2/8+2/8}>
        >>> a.beamSequence
        <music21.meter.core.MeterSequence {{1/8+1/8}+{1/8+1/8}+{1/8+1/8}}>
        >>> a.beatSequence  # a single top-level partition is default for beat
        <music21.meter.core.MeterSequence {{1/8+1/8}+{1/8+1/8}+{1/8+1/8}}>
        >>> a.setDisplay('3/4')
        >>> a.displaySequence
        <music21.meter.core.MeterSequence {3/4}>
        '''
        if isinstance(value, MeterSequence):  # can set to an existing MeterSequence
            # must make a copy
            self.displaySequence = copy.deepcopy(value)
        else:
            # create a new object; it will not be linked
            self.displaySequence = MeterSequence(value, partitionRequest)

    def getAccent(self, qLenPos: float) -> bool:
        '''
        Return True or False if the qLenPos is at the start of an accent
        division.

        >>> a = meter.TimeSignature('3/4', 3)
        >>> a.accentSequence.partition([2, 1])
        >>> a.accentSequence
        <music21.meter.core.MeterSequence {2/4+1/4}>
        >>> a.getAccent(0.0)
        True
        >>> a.getAccent(1.0)
        False
        >>> a.getAccent(2.0)
        True
        '''
        pos = 0
        qLenPos = opFrac(qLenPos)
        for i in range(len(self.accentSequence)):
            if pos == qLenPos:
                return True
            pos += self.accentSequence[i].duration.quarterLength
        return False

    def setAccentWeight(self, weightList, level=0):
        '''Set accent weight, or floating point scalars, for the accent MeterSequence.
        Provide a list of values; if this list is shorter than the length of the MeterSequence,
        it will be looped; if this list is longer, only the first relevant value will be used.

        If the accent MeterSequence is subdivided, the level of depth to set is given by the
        optional level argument.


        >>> a = meter.TimeSignature('4/4', 4)
        >>> len(a.accentSequence)
        4
        >>> a.setAccentWeight([0.8, 0.2])
        >>> a.getAccentWeight(0)
        0.8...
        >>> a.getAccentWeight(0.5)
        0.8...
        >>> a.getAccentWeight(1)
        0.2...
        >>> a.getAccentWeight(2.5)
        0.8...
        >>> a.getAccentWeight(3.5)
        0.2...
        '''
        if not common.isListLike(weightList):
            weightList = [weightList]

        msLevel = self.accentSequence.getLevel(level)
        for i in range(len(msLevel)):
            msLevel[i].weight = weightList[i % len(weightList)]

    def averageBeatStrength(self, streamIn, notesOnly=True):
        '''
        returns a float of the average beat strength of all objects (or if notesOnly is True
        [default] only the notes) in the `Stream` specified as streamIn.


        >>> s = converter.parse('C4 D4 E8 F8', format='tinyNotation').flatten().notes.stream()
        >>> sixEight = meter.TimeSignature('6/8')
        >>> sixEight.averageBeatStrength(s)
        0.4375
        >>> threeFour = meter.TimeSignature('3/4')
        >>> threeFour.averageBeatStrength(s)
        0.5625

        If `notesOnly` is `False` then test objects will give added
        weight to the beginning of the measure:

        >>> sixEight.averageBeatStrength(s, notesOnly=False)
        0.4375
        >>> s.insert(0.0, clef.TrebleClef())
        >>> s.insert(0.0, clef.BassClef())
        >>> sixEight.averageBeatStrength(s, notesOnly=False)
        0.625
        '''
        if notesOnly is True:
            streamIn = streamIn.notes

        totalWeight = 0.0
        totalObjects = len(streamIn)
        if totalObjects == 0:
            return 0.0  # or raise exception?  add doc test
        for el in streamIn:
            elWeight = self.getAccentWeight(
                self.getMeasureOffsetOrMeterModulusOffset(el),
                forcePositionMatch=True, permitMeterModulus=False)
            totalWeight += elWeight
        return totalWeight / totalObjects

    def getMeasureOffsetOrMeterModulusOffset(self, el):
        '''
        Return the measure offset based on a Measure, if it exists,
        otherwise based on meter modulus of the TimeSignature.

        >>> m = stream.Measure()
        >>> ts1 = meter.TimeSignature('3/4')
        >>> m.insert(0, ts1)
        >>> n1 = note.Note()
        >>> m.insert(2, n1)
        >>> ts1.getMeasureOffsetOrMeterModulusOffset(n1)
        2.0

        Exceeding the range of the Measure gets a modulus

        >>> n2 = note.Note()
        >>> m.insert(4.0, n2)
        >>> ts1.getMeasureOffsetOrMeterModulusOffset(n2)
        1.0

        Can be applied to Notes in a Stream with a TimeSignature.

        >>> ts2 = meter.TimeSignature('5/4')
        >>> s2 = stream.Stream()
        >>> s2.insert(0, ts2)
        >>> n3 = note.Note()
        >>> s2.insert(3, n3)
        >>> ts2.getMeasureOffsetOrMeterModulusOffset(n3)
        3.0

        >>> n4 = note.Note()
        >>> s2.insert(5, n4)
        >>> ts2.getMeasureOffsetOrMeterModulusOffset(n4)
        0.0
        '''
        mOffset = el._getMeasureOffset()  # TODO(msc): expose this method and remove private
        tsMeasureOffset = self._getMeasureOffset(includeMeasurePadding=False)
        if (mOffset + tsMeasureOffset) < self.barDuration.quarterLength:
            return mOffset
        else:
            # must get offset relative to not just start of Stream, but the last
            # time signature
            post = ((mOffset - tsMeasureOffset) % self.barDuration.quarterLength)
            # environLocal.printDebug(['result', post])
            return post

    def getAccentWeight(self, qLenPos, level=0, forcePositionMatch=False,
                        permitMeterModulus=False):
        '''Given a qLenPos,  return an accent level. In general, accents are assumed to
        define only a first-level weight.

        If `forcePositionMatch` is True, an accent will only be returned if the
        provided qLenPos is a near exact match to the provided quarter length. Otherwise,
        half of the minimum quarter length will be provided.

        If `permitMeterModulus` is True, quarter length positions greater than
        the duration of the Meter will be accepted as the modulus of the total meter duration.


        >>> ts1 = meter.TimeSignature('3/4')
        >>> [ts1.getAccentWeight(x) for x in range(3)]
        [1.0, 0.5, 0.5]


        Returns an error...

        >>> [ts1.getAccentWeight(x) for x in range(6)]
        Traceback (most recent call last):
        music21.exceptions21.MeterException: cannot access from qLenPos 3.0
            where total duration is 3.0

        ...unless permitMeterModulus is employed

        >>> [ts1.getAccentWeight(x, permitMeterModulus=True) for x in range(6)]
        [1.0, 0.5, 0.5, 1.0, 0.5, 0.5]

        '''
        qLenPos = opFrac(qLenPos)
        # might store this weight every time it is set, rather than
        # getting it here
        minWeight = min(
            [mt.weight for mt in self.accentSequence]) * 0.5
        msLevel = self.accentSequence.getLevel(level)

        if permitMeterModulus:
            environLocal.printDebug(
                [' self.duration.quarterLength', self.duration.quarterLength,
                 'self.barDuration.quarterLength', self.barDuration.quarterLength])
            qLenPos = qLenPos % self.barDuration.quarterLength

        if forcePositionMatch:
            # only return values for qLen positions that are at the start
            # of a span; for those that are not, we need to return a minWeight
            localSpan = msLevel.offsetToSpan(qLenPos,
                                             permitMeterModulus=permitMeterModulus)

            if qLenPos != localSpan[0]:
                return minWeight
        return msLevel[msLevel.offsetToIndex(qLenPos)].weight

    def getBeat(self, offset):
        '''
        Given an offset (quarterLength position), get the beat, where beats count from 1

        If you want a fractional number for the beat, see `getBeatProportion`.

        TODO: In v7 -- getBeat will probably do what getBeatProportion does now...
        but just with 1 added to it.

        >>> a = meter.TimeSignature('3/4', 3)
        >>> a.getBeat(0)
        1
        >>> a.getBeat(2.5)
        3
        >>> a.beatSequence.partition(['3/8', '3/8'])
        >>> a.getBeat(2.5)
        2
        '''
        return self.beatSequence.offsetToIndex(offset) + 1

    def getBeatOffsets(self):
        '''Return offset positions in a list for the start of each beat,
        assuming this object is found at offset zero.

        >>> a = meter.TimeSignature('3/4')
        >>> a.getBeatOffsets()
        [0.0, 1.0, 2.0]
        >>> a = meter.TimeSignature('6/8')
        >>> a.getBeatOffsets()
        [0.0, 1.5]
        '''
        post = []
        post.append(0.0)
        if len(self.beatSequence) == 1:
            return post
        else:
            endOffset = self.barDuration.quarterLength
            o = 0.0
            for ms in self.beatSequence:
                o = opFrac(o + ms.duration.quarterLength)
                if o >= endOffset:
                    return post  # do not add offset for end of bar
                post.append(o)

    def getBeatDuration(self, qLenPos):
        '''
        Returns a :class:`~music21.duration.Duration`
        object representing the length of the beat
        found at qLenPos.  For most standard
        meters, you can give qLenPos = 0
        and get the length of any beat in
        the TimeSignature; but the simpler
        :attr:`music21.meter.TimeSignature.beatDuration` parameter,
        will do that for you just as well.

        The advantage of this method is that
        it will work for asymmetrical meters, as the second
        example shows.


        Ex. 1: beat duration for 3/4 is always 1.0
        no matter where in the meter you query.


        >>> ts1 = meter.TimeSignature('3/4')
        >>> ts1.getBeatDuration(0.5)
        <music21.duration.Duration 1.0>
        >>> ts1.getBeatDuration(2.5)
        <music21.duration.Duration 1.0>


        Ex. 2: same for 6/8:


        >>> ts2 = meter.TimeSignature('6/8')
        >>> ts2.getBeatDuration(2.5)
        <music21.duration.Duration 1.5>


        Ex. 3: but for a compound meter of 3/8 + 2/8,
        where you ask for the beat duration
        will determine the length of the beat:


        >>> ts3 = meter.TimeSignature('3/8+2/8')  # will partition as 2 beat
        >>> ts3.getBeatDuration(0.5)
        <music21.duration.Duration 1.5>
        >>> ts3.getBeatDuration(1.5)
        <music21.duration.Duration 1.0>
        '''
        return self.beatSequence[self.beatSequence.offsetToIndex(qLenPos)].duration

    def getOffsetFromBeat(self, beat):
        '''
        Given a beat value, convert into an offset position.


        >>> ts1 = meter.TimeSignature('3/4')
        >>> ts1.getOffsetFromBeat(1)
        0.0
        >>> ts1.getOffsetFromBeat(2)
        1.0
        >>> ts1.getOffsetFromBeat(3)
        2.0
        >>> ts1.getOffsetFromBeat(3.5)
        2.5
        >>> ts1.getOffsetFromBeat(3.25)
        2.25

        >>> from fractions import Fraction
        >>> ts1.getOffsetFromBeat(Fraction(8, 3))  # 2.66666
        Fraction(5, 3)


        >>> ts1 = meter.TimeSignature('6/8')
        >>> ts1.getOffsetFromBeat(1)
        0.0
        >>> ts1.getOffsetFromBeat(2)
        1.5
        >>> ts1.getOffsetFromBeat(2.33)
        2.0
        >>> ts1.getOffsetFromBeat(2.5)  # will be + 0.5 * 1.5
        2.25
        >>> ts1.getOffsetFromBeat(2.66)
        2.5


        Works for asymmetrical meters as well:


        >>> ts3 = meter.TimeSignature('3/8+2/8')  # will partition as 2 beat
        >>> ts3.getOffsetFromBeat(1)
        0.0
        >>> ts3.getOffsetFromBeat(2)
        1.5
        >>> ts3.getOffsetFromBeat(1.66)
        1.0
        >>> ts3.getOffsetFromBeat(2.5)
        2.0


        Let's try this on a real piece, a 4/4 chorale with a one beat pickup.  Here we get the
        normal offset from the active TimeSignature but we subtract out the pickup length which
        is in a `Measure`'s :attr:`~music21.stream.Measure.paddingLeft` property.

        >>> c = corpus.parse('bwv1.6')
        >>> for m in c.parts.first().getElementsByClass('Measure'):
        ...     ts = m.timeSignature or m.getContextByClass('TimeSignature')
        ...     print('%s %s' % (m.number, ts.getOffsetFromBeat(4.5) - m.paddingLeft))
        0 0.5
        1 3.5
        2 3.5
        ...
        '''
        # divide into integer and floating point components
        beatInt, beatFraction = divmod(beat, 1)
        beatInt = int(beatInt)  # convert to integer

        # resolve 0.33 to 0.3333333 (actually Fraction(1, 3). )
        beatFraction = common.addFloatPrecision(beatFraction)

        if beatInt - 1 > len(self.beatSequence) - 1:
            raise TimeSignatureException(
                'requested beat value (%s) not found in beat partitions (%s) of ts %s' % (
                    beatInt, self.beatSequence, self))
        # get a duration object for the beat; will translate into quarterLength
        # beat int counts from 1; subtract 1 to get index
        beatDur = self.beatSequence[beatInt - 1].duration
        oStart, unused_oEnd = self.beatSequence.getLevelSpan()[beatInt - 1]
        post = opFrac(oStart + (beatDur.quarterLength * beatFraction))
        return post

    def getBeatProgress(self, qLenPos):
        '''
        Given a quarterLength position, get the beat,
        where beats count from 1, and return the the
        amount of qLen into this beat the supplied qLenPos
        is.

        >>> a = meter.TimeSignature('3/4', 3)
        >>> a.getBeatProgress(0)
        (1, 0)
        >>> a.getBeatProgress(0.75)
        (1, 0.75)
        >>> a.getBeatProgress(1.0)
        (2, 0.0)
        >>> a.getBeatProgress(2.5)
        (3, 0.5)


        Works for specifically partitioned meters too:

        >>> a.beatSequence.partition(['3/8', '3/8'])
        >>> a.getBeatProgress(2.5)
        (2, 1.0)
        '''
        beatIndex = self.beatSequence.offsetToIndex(qLenPos)
        start, unused_end = self.beatSequence.offsetToSpan(qLenPos)
        return beatIndex + 1, qLenPos - start

    def getBeatProportion(self, qLenPos):
        '''
        Given a quarter length position into the meter, return a numerical progress
        through the beat (where beats count from one) with a floating-point or fractional value
        between 0 and 1 appended to this value that gives the proportional progress into the beat.

        For faster, integer values, use simply `.getBeat()`

        >>> ts1 = meter.TimeSignature('3/4')
        >>> ts1.getBeatProportion(0.0)
        1.0
        >>> ts1.getBeatProportion(0.5)
        1.5
        >>> ts1.getBeatProportion(1.0)
        2.0

        >>> ts3 = meter.TimeSignature('3/8+2/8')  # will partition as 2 beat
        >>> ts3.getBeatProportion(0.75)
        1.5
        >>> ts3.getBeatProportion(2.0)
        2.5
        '''
        beatIndex = self.beatSequence.offsetToIndex(qLenPos)
        start, end = self.beatSequence.offsetToSpan(qLenPos)
        totalRange = end - start
        progress = qLenPos - start  # how far in QL
        return opFrac(beatIndex + 1 + (progress / totalRange))

    def getBeatProportionStr(self, qLenPos):
        '''Return a string presentation of the beat.

        >>> ts1 = meter.TimeSignature('3/4')
        >>> ts1.getBeatProportionStr(0.0)
        '1'
        >>> ts1.getBeatProportionStr(0.5)
        '1 1/2'
        >>> ts1.getBeatProportionStr(1.0)
        '2'
        >>> ts3 = meter.TimeSignature('3/8+2/8')  # will partition as 2 beat
        >>> ts3.getBeatProportionStr(0.75)
        '1 1/2'
        >>> ts3.getBeatProportionStr(2)
        '2 1/2'

        >>> ts4 = meter.TimeSignature('6/8')  # will partition as 2 beat
        '''
        beatIndex = int(self.beatSequence.offsetToIndex(qLenPos))
        start, end = self.beatSequence.offsetToSpan(qLenPos)
        totalRange = end - start
        progress = qLenPos - start  # how far in QL

        if (progress / totalRange) == 0.0:
            post = f'{beatIndex + 1}'  # just show beat
        else:
            a, b = proportionToFraction(progress / totalRange)
            post = f'{beatIndex + 1} {a}/{b}'  # just show beat
        return post

    def getBeatDepth(self, qLenPos, align='quantize'):
        '''Return the number of levels of beat partitioning given a QL into the TimeSignature.
        Note that by default beat partitioning always has a single, top-level partition.

        The `align` parameter is passed to the :meth:`~music21.meter.MeterSequence.offsetToDepth`
        method, and can be used to find depths based on start position overlaps.

        >>> a = meter.TimeSignature('3/4', 3)
        >>> a.getBeatDepth(0)
        1
        >>> a.getBeatDepth(1)
        1
        >>> a.getBeatDepth(2)
        1

        >>> b = meter.TimeSignature('3/4', 1)
        >>> b.beatSequence[0] = b.beatSequence[0].subdivide(3)
        >>> b.beatSequence[0][0] = b.beatSequence[0][0].subdivide(2)
        >>> b.beatSequence[0][1] = b.beatSequence[0][1].subdivide(2)
        >>> b.beatSequence[0][2] = b.beatSequence[0][2].subdivide(2)
        >>> b.getBeatDepth(0)
        3
        >>> b.getBeatDepth(0.5)
        1
        >>> b.getBeatDepth(1)
        2
        '''
        return self.beatSequence.offsetToDepth(qLenPos, align)


# -----------------------------------------------------------------------------
class SenzaMisuraTimeSignature(base.Music21Object):
    '''
    A SenzaMisuraTimeSignature represents the absence of a TimeSignature

    It is NOT a TimeSignature subclass, only because it has none of the attributes
    of a TimeSignature.

    >>> smts = meter.SenzaMisuraTimeSignature('0')
    >>> smts.text
    '0'
    >>> smts
    <music21.meter.SenzaMisuraTimeSignature 0>
    '''

    def __init__(self, text=None):
        super().__init__()
        self.text = text

    def _reprInternal(self):
        if self.text is None:
            return ''
        else:
            return str(self.text)


# TODO: Implement or delete...

# class NonPowerOfTwoTimeSignature(TimeSignature):
#     pass
# class AutoAdjustTimeSignature(TimeSignature):
#     automatically adjusts to fit its measure context.


# -----------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [TimeSignature]


if __name__ == '__main__':
    import music21
    music21.mainTest()
