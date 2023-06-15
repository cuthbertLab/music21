# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         clef.py
# Purpose:      Objects for representing clefs
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#               Michael Bodenbach
#
# Copyright:    Copyright © 2009-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module defines numerous subclasses of
:class:`~music21.clef.Clef`, providing object representations for all
commonly used clefs. Clef objects are often found
within :class:`~music21.stream.Measure` objects.
'''
from __future__ import annotations

from collections.abc import Iterable, Sequence
import typing as t
import unittest

from music21 import base
from music21 import exceptions21
from music21 import environment
from music21 import pitch
from music21 import style


if t.TYPE_CHECKING:
    from music21 import stream


environLocal = environment.Environment('clef')


class ClefException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------
class Clef(base.Music21Object):
    '''
    A Clef is a basic `music21` object for representing musical clefs
    (Treble, Bass, etc.)

    Some clefs only represent the graphical element of the clef,
    such as G clef, which is subclassed by TrebleClef() and FrenchViolinClef().

    >>> tc = clef.TrebleClef()
    >>> tc
    <music21.clef.TrebleClef>
    >>> tc.sign
    'G'
    >>> tc.line
    2

    Most clefs also have a "lowestLine" function which represents the
    :attr:`~music21.pitch.Pitch.diatonicNoteNum` of the note that would fall on the
    lowest line if the Clef were put on a five-line staff. (Where C4,C#4,C##4,C-4
    etc. = 29, all types of D4 = 30, etc.)

    >>> tc.lowestLine
    31

    **Equality**

    Two Clefs are equal if their class is the same, their sign is the same,
    their line is the same and their octaveChange is the same.

    >>> c1 = clef.PercussionClef()
    >>> c2 = clef.NoClef()
    >>> c1 == c2
    False
    >>> c3 = clef.TrebleClef()
    >>> c4 = clef.TrebleClef()
    >>> c3 == c4
    True
    >>> c4.octaveChange = -1
    >>> c3 == c4
    False

    Note that these are not equal:

    >>> clef.TrebleClef() == clef.GClef(line=2)
    False
    '''
    equalityAttributes = ('sign', 'line', 'octaveChange')

    _DOC_ATTR: dict[str, str] = {
        'sign': '''
            The sign of the clef, generally, 'C', 'G', 'F', 'percussion', 'none' or None.

            >>> alto = clef.AltoClef()
            >>> alto.sign
            'C'
            >>> percussion = clef.PercussionClef()
            >>> percussion.sign
            'percussion'

            Note the difference here:

            >>> clef.Clef().sign is None
            True
            >>> clef.NoClef().sign
            'none'

            ''',
        'line': '''
            The line, counting from the bottom up, that the clef resides on.

            >>> clef.AltoClef().line
            3
            >>> clef.TenorClef().line
            4

            May be None:

            >>> print(clef.NoClef().line)
            None
            ''',
    }

    _styleClass = style.TextStyle
    classSortOrder = 0

    def __init__(self, **keywords) -> None:
        super().__init__(**keywords)
        self.sign: str | None = None
        # line counts start from the bottom up, the reverse of musedata
        self.line: int | None = None
        self._octaveChange: int = 0  # set to zero as default
        # musicxml has an attribute for clefOctaveChange,
        # an integer to show transposing clef

    def _reprInternal(self):
        return ''

    @property
    def octaveChange(self) -> int:
        '''
        The number of octaves that the clef "transposes", generally 0.

        >>> tc = clef.TrebleClef()
        >>> tc.octaveChange
        0
        >>> clef.Treble8vbClef().octaveChange
        -1
        '''
        return self._octaveChange

    @octaveChange.setter
    def octaveChange(self, newValue: int):
        self._octaveChange = newValue

    @property
    def name(self) -> str:
        '''
        Returns the "name" of the clef, from the class name

        >>> tc = clef.TrebleClef()
        >>> tc.name
        'treble'

        >>> tc = clef.Treble8vbClef()
        >>> tc.name
        'treble8vb'

        >>> tc = clef.MezzoSopranoClef()
        >>> tc.name
        'mezzoSoprano'

        OMIT_FROM_DOCS

        >>> clef.Clef().name
        ''
        '''
        className = self.__class__.__name__.replace('Clef', '')
        if className:
            return className[0].lower() + className[1:]
        else:
            return ''

    def getStemDirectionForPitches(
        self,
        pitches: pitch.Pitch | Sequence[pitch.Pitch],
        *,
        firstLastOnly: bool = True,
        extremePitchOnly: bool = False,
    ) -> str:
        # noinspection PyShadowingNames
        '''
        Return a string representing the stem direction for a single
        :class:`~music21.pitch.Pitch` object or a list/tuple/Stream of pitches.

        >>> P = pitch.Pitch
        >>> bc = clef.BassClef()
        >>> bc.getStemDirectionForPitches(P('C3'))
        'up'

        For two pitches, the most extreme pitch determines the direction:

        >>> pitchList = [P('C3'), P('B3')]
        >>> bc.getStemDirectionForPitches(pitchList)
        'down'

        If `firstLastOnly` is True (as by default) then only the first and last pitches are
        examined, as in a beam group.  Here we have C3, B3, C3, so despite the B in bass
        clef being much farther from the center line than either of the Cs, it is stem up:

        >>> pitchList.append(P('C3'))
        >>> bc.getStemDirectionForPitches(pitchList)
        'up'

        If `firstLastOnly` is False, then each of the pitches has a weight on the process

        >>> bc.getStemDirectionForPitches(pitchList, firstLastOnly=False)
        'down'

        If extremePitchOnly is True, then whatever pitch is farthest from the center line
        determines the direction, regardless of order.  (default False).

        >>> bc.getStemDirectionForPitches(pitchList, extremePitchOnly=True)
        'down'
        >>> pitchList.insert(1, P('C2'))
        >>> bc.getStemDirectionForPitches(pitchList, extremePitchOnly=True)
        'up'
        '''
        pitchList: Sequence[pitch.Pitch]
        if isinstance(pitches, pitch.Pitch):
            pitchList = [pitches]
        else:
            pitchList = pitches
        relevantPitches: Sequence[pitch.Pitch]

        if not pitchList:
            raise ValueError('getStemDirectionForPitches cannot operate on an empty list')

        if extremePitchOnly:
            pitchMin = min(pitchList, key=lambda pp: pp.diatonicNoteNum)
            pitchMax = max(pitchList, key=lambda pp: pp.diatonicNoteNum)
            relevantPitches = [pitchMin, pitchMax]
        elif firstLastOnly and len(pitchList) > 1:
            relevantPitches = [pitchList[0], pitchList[-1]]
        else:
            relevantPitches = pitchList

        differenceSum = 0
        # pylint: disable-next=no-member
        if isinstance(self, (PercussionClef, PitchClef)) and self.lowestLine is not None:
            midLine = self.lowestLine + 4  # pylint: disable=no-member
        else:
            midLine = 35  # assume TrebleClef-like.

        for p in relevantPitches:
            distanceFromMidLine = p.diatonicNoteNum - midLine
            differenceSum += distanceFromMidLine

        if differenceSum >= 0:
            return 'down'
        else:
            return 'up'




# ------------------------------------------------------------------------------


class PitchClef(Clef):
    '''
    superclass for all other clef subclasses that use pitches...
    '''
    _DOC_ATTR: dict[str, str] = {
        'lowestLine': '''
            The diatonicNoteNumber of the lowest line of the clef.
            (Can be none...)

            >>> clef.TrebleClef().lowestLine
            31
            ''',
    }

    def __init__(self, **keywords) -> None:
        super().__init__(**keywords)
        self.lowestLine: int = 31

    @property
    def octaveChange(self) -> int:
        '''
        The number of octaves that the clef "transposes", generally 0.

        >>> tc = clef.TrebleClef()
        >>> tc.octaveChange
        0
        >>> clef.Treble8vbClef().octaveChange
        -1

        Changing octaveChange changes lowestLine (but not vice-versa)

        >>> tc.lowestLine
        31
        >>> tc.octaveChange = 1
        >>> tc.lowestLine
        38
        >>> tc.octaveChange = -1
        >>> tc.lowestLine
        24
        '''
        return super().octaveChange

    @octaveChange.setter
    def octaveChange(self, newValue: int):
        oldOctaveChange = self._octaveChange
        self._octaveChange = newValue
        if self.lowestLine is not None:
            self.lowestLine += (newValue - oldOctaveChange) * 7


class PercussionClef(Clef):
    '''
    represents a Percussion clef.

    >>> pc = clef.PercussionClef()
    >>> pc.sign
    'percussion'
    >>> pc.line is None
    True

    Percussion clefs should not, technically have a
    "lowestLine," but it is a common usage to assume that
    in pitch-centric contexts to use the pitch numbers
    from treble clef for percussion clefs.  Thus:

    >>> pc.lowestLine == clef.TrebleClef().lowestLine
    True

    * Changed in v7.3: setting `octaveChange` no longer affects
      `lowestLine`
    '''
    _DOC_ATTR: dict[str, str] = {}

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.sign = 'percussion'
        self.lowestLine = (7 * 4) + 3  # 4 octaves + 3 notes = e4


class NoClef(Clef):
    '''
    represents the absence of a Clef.

    >>> nc = clef.NoClef()
    >>> nc.sign
    'none'

    Note that the sign is the string 'none' not the None object

    >>> nc.sign is None
    False
    '''
    _DOC_ATTR: dict[str, str] = {}

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.sign = 'none'


class JianpuClef(NoClef):
    '''
    Jianpu notation does not use a clef, but musicxml marks it
    with a specialized "jianpu" sign.

    >>> jc = clef.JianpuClef()
    >>> jc.sign
    'jianpu'
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.sign = 'jianpu'


class TabClef(PitchClef):
    '''
    represents a Tablature clef.

    >>> a = clef.TabClef()
    >>> a.sign
    'TAB'
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.sign = 'TAB'
        self.line = 5

    def getStemDirectionForPitches(
        self,
        pitchList: pitch.Pitch | Iterable[pitch.Pitch],
        *,
        firstLastOnly: bool = True,
        extremePitchOnly: bool = False,
    ) -> str:
        '''
        Overridden to simply return 'down' for guitar tabs.
        '''
        return 'down'

# ------------------------------------------------------------------------------


class GClef(PitchClef):
    '''
    A generic G Clef

    >>> a = clef.GClef()
    >>> a.sign
    'G'

    If not defined, the lowestLine is set as a Treble Clef (E4 = 31)

    >>> a.lowestLine
    31
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.sign = 'G'


class FrenchViolinClef(GClef):
    '''
    A G Clef that appears in many old French Violin scores,
    appearing on the lowest line, and thus higher than
    a treble clef.

    >>> a = clef.FrenchViolinClef()
    >>> a.sign
    'G'
    >>> a.line
    1
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 1
        self.lowestLine = (7 * 4) + 5


class TrebleClef(GClef):
    '''
    The most common clef of all, a treble clef.

    >>> a = clef.TrebleClef()
    >>> a.sign
    'G'
    >>> a.line
    2
    >>> a.lowestLine
    31
    >>> note.Note('E4').pitch.diatonicNoteNum
    31
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 2
        self.lowestLine = (7 * 4) + 3  # 4 octaves + 3 notes = e4


class Treble8vbClef(TrebleClef):
    '''
    A vocal tenor treble clef. Also for guitars.

    >>> a = clef.Treble8vbClef()
    >>> a.sign
    'G'
    >>> a.octaveChange
    -1
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.octaveChange = -1
        self.lowestLine = (7 * 3) + 3


class Treble8vaClef(TrebleClef):
    '''
    A treble clef an octave up (such as for piccolos)

    >>> a = clef.Treble8vaClef()
    >>> a.sign
    'G'
    >>> a.octaveChange
    1
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.octaveChange = 1
        self.lowestLine = (7 * 3) + 3


class GSopranoClef(GClef):
    '''
    A G clef on the middle line, formerly occasionally used
    for soprano parts.

    >>> a = clef.GSopranoClef()
    >>> a.sign
    'G'
    >>> a.line
    3
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 3
        self.lowestLine = (7 * 4) + 1

# ------------------------------------------------------------------------------


class CClef(PitchClef):
    '''
    A generic C Clef, with no line set

    >>> a = clef.CClef()
    >>> a.sign
    'C'
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.sign = 'C'


class SopranoClef(CClef):
    '''
    A soprano clef, with C on the lowest line
    (found in Bach often)

    >>> a = clef.SopranoClef()
    >>> a.sign
    'C'
    >>> a.line
    1
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 1
        self.lowestLine = (7 * 4) + 1


class MezzoSopranoClef(CClef):
    '''
    A C clef with C on the second line.  Perhaps
    the rarest of the C clefs

    >>> a = clef.MezzoSopranoClef()
    >>> a.sign
    'C'
    >>> a.line
    2
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 2
        self.lowestLine = (7 * 3) + 6


class AltoClef(CClef):
    '''
    A C AltoClef, common for violas.

    >>> a = clef.AltoClef()
    >>> a.sign
    'C'
    >>> a.line
    3
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 3
        self.lowestLine = (7 * 3) + 4


class TenorClef(CClef):
    '''
    A C Tenor Clef, often used in bassoon and cello parts
    and orchestral trombone parts.

    >>> a = clef.TenorClef()
    >>> a.sign
    'C'
    >>> a.line
    4

    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 4
        self.lowestLine = (7 * 3) + 2


class CBaritoneClef(CClef):
    '''
    A Baritone C clef (as opposed to an F Baritone Clef)

    >>> a = clef.CBaritoneClef()
    >>> a.sign
    'C'
    >>> a.line
    5
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 5
        self.lowestLine = (7 * 2) + 7


# ------------------------------------------------------------------------------
class FClef(PitchClef):
    '''
    A generic F-Clef, like a Bass clef

    >>> a = clef.FClef()
    >>> a.sign
    'F'
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.sign = 'F'


class FBaritoneClef(FClef):
    '''
    an F Baritone Clef

    >>> a = clef.FBaritoneClef()
    >>> a.sign
    'F'
    >>> a.line
    3
    >>> b = clef.CBaritoneClef()
    >>> a.lowestLine == b.lowestLine
    True
    >>> a.sign == b.sign
    False
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 3
        self.lowestLine = (7 * 2) + 7


class BassClef(FClef):
    '''
    A standard Bass Clef

    >>> a = clef.BassClef()
    >>> a.sign
    'F'
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 4
        self.lowestLine = (7 * 2) + 5


class Bass8vbClef(FClef):
    '''
    A bass clef configured to be an octave lower.

    >>> a = clef.Bass8vbClef()
    >>> a.sign
    'F'
    >>> a.octaveChange
    -1
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 4
        self.octaveChange = -1
        self.lowestLine = (7 * 2) + 5


class Bass8vaClef(FClef):
    '''
    A rarely used Bass Clef an octave higher.

    >>> a = clef.Bass8vaClef()
    >>> a.sign
    'F'
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 4
        self.octaveChange = 1
        self.lowestLine = (7 * 2) + 5


class SubBassClef(FClef):
    '''
    An F clef on the top line.

    >>> a = clef.SubBassClef()
    >>> a.sign
    'F'
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.line = 5
        self.lowestLine = (7 * 2) + 3


# ------------------------------------------------------------------------------
CLASS_FROM_TYPE: dict[str, list[type[Clef] | None]] = {
    'G': [None, FrenchViolinClef, TrebleClef, GSopranoClef, None, None],
    'C': [None, SopranoClef, MezzoSopranoClef, AltoClef, TenorClef, CBaritoneClef],
    'F': [None, None, None, FBaritoneClef, BassClef, SubBassClef],
    'TAB': [None, None, None, None, None, TabClef]
}


def clefFromString(clefString, octaveShift=0) -> Clef:
    '''
    Returns a Clef object given a string like "G2" or "F4" etc.

    Does not refer to a violin/guitar string.


    >>> tc = clef.clefFromString('G2')
    >>> tc
    <music21.clef.TrebleClef>
    >>> nonStandard1 = clef.clefFromString('F1')
    >>> nonStandard1
    <music21.clef.FClef>
    >>> nonStandard1.line
    1
    >>> nonStandard2 = clef.clefFromString('D4')
    >>> nonStandard2
    <music21.clef.PitchClef>
    >>> nonStandard2.sign
    'D'
    >>> nonStandard2.line
    4


    >>> tc8vb = clef.clefFromString('G2', -1)
    >>> tc8vb
    <music21.clef.Treble8vbClef>

    Three special clefs, Tab, Percussion, and None are also supported.

    >>> tabClef = clef.clefFromString('TAB')
    >>> tabClef
    <music21.clef.TabClef>

    Case does not matter.

    >>> tc8vb = clef.clefFromString('g2', -1)
    >>> tc8vb
    <music21.clef.Treble8vbClef>

    >>> percussionClef = clef.clefFromString('Percussion')
    >>> percussionClef
    <music21.clef.PercussionClef>

    >>> noClef = clef.clefFromString('None')
    >>> noClef
    <music21.clef.NoClef>

    Invalid line numbers raise an exception:

    >>> invalidClef = clef.clefFromString('F6')
    Traceback (most recent call last):
    music21.clef.ClefException: line number (second character) must be 1-5;
                do not use this function for clefs on special staves such as 'F6'


    Can find any clef in the module

    >>> clef.clefFromString('Treble')
    <music21.clef.TrebleClef>
    >>> clef.clefFromString('trebleclef')
    <music21.clef.TrebleClef>
    >>> clef.clefFromString('treble8vb')
    <music21.clef.Treble8vbClef>
    '''
    xnStr = clefString.strip()
    if xnStr.lower() in ('tab', 'percussion', 'none', 'jianpu'):
        if xnStr.lower() == 'tab':
            return TabClef()
        elif xnStr.lower() == 'percussion':
            return PercussionClef()
        elif xnStr.lower() == 'none':
            return NoClef()
        elif xnStr.lower() == 'jianpu':
            return JianpuClef()

    if len(xnStr) == 2:
        (thisType, lineNum) = (xnStr[0].upper(), int(xnStr[1]))
    elif len(xnStr) == 1:  # some Humdrum files have just ClefG, eg. Haydn op. 9 no 3, mvmt 1
        thisType = xnStr[0].upper()
        if thisType == 'G':
            lineNum = 2
        elif thisType == 'F':
            lineNum = 4
        elif thisType == 'C':
            lineNum = 3
        else:
            lineNum = False
    elif len(xnStr) > 2:
        from music21 import clef as myself
        xnLower = xnStr.lower()
        for x in dir(myself):
            if 'Clef' not in x:
                continue
            if xnLower != x.lower() and xnLower + 'clef' != x.lower():
                continue
            objType = getattr(myself, x)
            if isinstance(objType, type):
                return objType()

        raise ClefException('Could not find clef ' + xnStr)
    else:
        raise ClefException('Entry has clef info but no clef specified')

    if octaveShift != 0:
        params = (thisType, lineNum, octaveShift)
        if params == ('G', 2, -1):
            return Treble8vbClef()
        elif params == ('G', 2, 1):
            return Treble8vaClef()
        elif params == ('F', 4, -1):
            return Bass8vbClef()
        elif params == ('F', 4, 1):
            return Bass8vaClef()
        # other octaveShifts will pass through

    if thisType is False or lineNum is False:
        raise ClefException(f'cannot read {xnStr} as clef str, should be G2, F4, etc.')

    if lineNum < 1 or lineNum > 5:
        raise ClefException('line number (second character) must be 1-5; do not use this '
                            + f'function for clefs on special staves such as {xnStr!r}')

    clefObj: Clef
    if thisType in CLASS_FROM_TYPE:
        line_list = CLASS_FROM_TYPE[thisType]
        assert isinstance(line_list, list)
        if line_list[lineNum] is None:
            if thisType == 'G':
                clefObj = GClef()
            elif thisType == 'F':
                clefObj = FClef()
            elif thisType == 'C':
                clefObj = CClef()
            elif thisType == 'TAB':
                clefObj = TabClef()
            else:  # pragma: no cover
                clefObj = PitchClef()
            clefObj.line = lineNum
        else:
            ClefType = line_list[lineNum]
            if t.TYPE_CHECKING:
                assert ClefType is not None
                assert issubclass(ClefType, PitchClef)
            clefObj = ClefType()
    else:
        clefObj = PitchClef()
        clefObj.sign = thisType
        clefObj.line = lineNum

    if octaveShift != 0:
        clefObj.octaveChange = octaveShift

    return clefObj


def bestClef(streamObj: stream.Stream,
             allowTreble8vb=False,
             recurse=False) -> PitchClef:
    # noinspection PyShadowingNames
    '''
    Returns the clef that is the best fit for notes and chords found in this Stream.

    >>> import random
    >>> a = stream.Stream()
    >>> for x in range(30):
    ...    n = note.Note()
    ...    n.pitch.midi = random.randint(70, 81)
    ...    a.insert(n)
    >>> b = clef.bestClef(a)
    >>> b
    <music21.clef.TrebleClef>
    >>> b.line
    2
    >>> b.sign
    'G'

    >>> c = stream.Stream()
    >>> for x in range(10):
    ...    n = note.Note()
    ...    n.pitch.midi = random.randint(45, 54)
    ...    c.insert(n)
    >>> d = clef.bestClef(c)
    >>> d
    <music21.clef.BassClef>
    >>> d.line
    4
    >>> d.sign
    'F'

    This does not automatically get a flat representation of the Stream.

    There are a lot more high notes in `a` (30) than low notes in `c` (10),
    but it will not matter here, because the pitches in `a` will not be found:

    >>> c.insert(0, a)
    >>> clef.bestClef(c)
    <music21.clef.BassClef>

    But with recursion, it will matter:

    >>> clef.bestClef(c, recurse=True)
    <music21.clef.TrebleClef>


    Notes around middle C can get Treble8vb if the setting is allowed:

    >>> clef.bestClef(stream.Stream([note.Note('D4')]))
    <music21.clef.TrebleClef>
    >>> clef.bestClef(stream.Stream([note.Note('D4')]), allowTreble8vb=True)
    <music21.clef.Treble8vbClef>

    Streams of extremely high notes or extremely low notes can get
    Treble8va or Bass8vb clefs:

    >>> clef.bestClef(stream.Stream([note.Note('D7')]))
    <music21.clef.Treble8vaClef>
    >>> clef.bestClef(stream.Stream([note.Note('C0')]))
    <music21.clef.Bass8vbClef>
    '''
    def findHeight(pInner):
        height = pInner.diatonicNoteNum
        if pInner.diatonicNoteNum > 33:  # a4
            height += 3  # bonus
        elif pInner.diatonicNoteNum < 24:  # Bass F or lower
            height += -3  # bonus
        return height
    # environLocal.printDebug(['calling bestClef()'])

    totalNotes = 0
    totalHeight = 0

    sIter = streamObj.recurse() if recurse else streamObj.iter()

    notes = sIter.notesAndRests

    for n in notes:
        if n.isRest:
            pass
        elif n.isNote:
            totalNotes += 1
            totalHeight += findHeight(n.pitch)
        elif n.isChord:
            for p in n.pitches:
                totalNotes += 1
                totalHeight += findHeight(p)
    if totalNotes == 0:
        averageHeight = 29.0
    else:
        averageHeight = totalHeight / totalNotes

    # environLocal.printDebug(['average height', averageHeight])
    if averageHeight > 49:  # value found with experimentation; revise
        return Treble8vaClef()
    elif allowTreble8vb and averageHeight > 32:
        return TrebleClef()
    elif not allowTreble8vb and averageHeight > 28:  # c4
        return TrebleClef()
    elif allowTreble8vb and averageHeight > 26:
        return Treble8vbClef()
    elif averageHeight > 10:  # value found with experimentation; revise
        return BassClef()
    else:
        return Bass8vbClef()


# ------------------------------------------------------------------------------
# all other tests in test/test_clef
class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Clef, TrebleClef, BassClef]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
