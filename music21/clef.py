# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         clef.py
# Purpose:      Objects for representing clefs
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
#
# Changes:      04 March 2014 by Michael Bodenbach
#               - TabClef added
# ------------------------------------------------------------------------------
'''
This module defines numerous subclasses of
:class:`~music21.clef.Clef`, providing object representations for all
commonly used clefs. Clef objects are often found
within :class:`~music21.stream.Measure` objects.
'''
import unittest
from typing import Mapping, Optional

from music21 import base
from music21 import exceptions21
from music21 import environment
from music21 import style

_MOD = 'clef'
environLocal = environment.Environment(_MOD)


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
    '''
    _DOC_ATTR = {
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
    }  # type: Mapping[str, str]

    _styleClass = style.TextStyle
    classSortOrder = 0

    def __init__(self):
        super().__init__()
        self.sign: Optional[str] = None
        # line counts start from the bottom up, the reverse of musedata
        self.line: Optional[int] = None
        self._octaveChange: int = 0  # set to zero as default
        # musicxml has an attribute for clefOctaveChange,
        # an integer to show transposing clef

    def __eq__(self, other):
        '''
        two Clefs are equal if their class is the same, their sign is the same,
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
        '''
        try:
            if (self.__class__ == other.__class__
                    and self.sign == other.sign
                    and self.line == other.line
                    and self.octaveChange == other.octaveChange):
                return True
            else:
                return False
        except AttributeError:
            return False

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
        return self._octaveChange

    @octaveChange.setter
    def octaveChange(self, newValue: int):
        oldOctaveChange = self._octaveChange
        self._octaveChange = newValue
        if hasattr(self, 'lowestLine') and self.lowestLine is not None:
            self.lowestLine += (newValue - oldOctaveChange) * 7

    @property
    def name(self) -> str:
        '''
        Returns the "name" of the clef, from the class name

        >>> tc = clef.TrebleClef()
        >>> tc.name
        'treble'
        '''
        className = self.__class__.__name__.replace('Clef', '')
        return className[0].lower() + className[1:]

# ------------------------------------------------------------------------------


class PitchClef(Clef):
    '''
    superclass for all other clef subclasses that use pitches...
    '''
    _DOC_ATTR: Mapping[str, str] = {
        'lowestLine': '''
            The diatonicNoteNumber of the lowest line of the clef.
            (Can be none...)

            >>> clef.TrebleClef().lowestLine
            31
            ''',
    }

    def __init__(self):
        super().__init__()
        self.lowestLine: Optional[int] = None


class PercussionClef(Clef):
    '''
    represents a Percussion clef.

    >>> pc = clef.PercussionClef()
    >>> pc.sign
    'percussion'
    >>> pc.line is None
    True

    Percussion clefs should not, technically. have a
    lowest line, but it is a common usage to assume that
    in pitch-centric contexts to use the pitch numbers
    from treble clef for percussion clefs.  Thus:

    >>> pc.lowestLine == clef.TrebleClef().lowestLine
    True
    '''
    _DOC_ATTR = {}

    def __init__(self):
        super().__init__()
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
    _DOC_ATTR = {}

    def __init__(self):
        super().__init__()
        self.sign = 'none'


class JianpuClef(NoClef):
    '''
    Jianpu notation does not use a clef, but musicxml marks it
    with a specialized "jianpu" sign.

    >>> jc = clef.JianpuClef()
    >>> jc.sign
    'jianpu'
    '''

    def __init__(self):
        super().__init__()
        self.sign = 'jianpu'


class TabClef(PitchClef):
    '''
    represents a Tablature clef.

    >>> a = clef.TabClef()
    >>> a.sign
    'TAB'
    '''

    def __init__(self):
        super().__init__()
        self.sign = 'TAB'
        self.line = 5

# ------------------------------------------------------------------------------


class GClef(PitchClef):
    '''
    A generic G Clef

    >>> a = clef.GClef()
    >>> a.sign
    'G'
    >>> a.lowestLine is None
    True
    '''

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
        self.line = 3
        self.lowestLine = (7 * 2) + 7


class BassClef(FClef):
    '''
    A standard Bass Clef

    >>> a = clef.BassClef()
    >>> a.sign
    'F'
    '''

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
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

    def __init__(self):
        super().__init__()
        self.line = 5
        self.lowestLine = (7 * 2) + 3


# ------------------------------------------------------------------------------
CLASS_FROM_TYPE = {
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
        from music21 import clef as myself  # @UnresolvedImport
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
        raise ClefException('cannot read %s as clef str, should be G2, F4, etc.' % xnStr)

    if lineNum < 1 or lineNum > 5:
        raise ClefException('line number (second character) must be 1-5; do not use this '
                            + "function for clefs on special staves such as '%s'" % xnStr)

    clefObj = None
    if thisType in CLASS_FROM_TYPE:
        if CLASS_FROM_TYPE[thisType][lineNum] is None:
            if thisType == 'G':
                clefObj = GClef()
            elif thisType == 'F':
                clefObj = FClef()
            elif thisType == 'C':
                clefObj = CClef()
            elif thisType == 'TAB':
                clefObj = TabClef()
            clefObj.line = lineNum
        else:
            clefObj = CLASS_FROM_TYPE[thisType][lineNum]()
    else:
        clefObj = PitchClef()
        clefObj.sign = thisType
        clefObj.line = lineNum

    if octaveShift != 0:
        clefObj.octaveChange = octaveShift

    return clefObj


def bestClef(streamObj: 'music21.stream.Stream',
             allowTreble8vb=False,
             recurse=False) -> PitchClef:
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

    Streams of very very high notes or very very low notes can get
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

    sIter = streamObj.recurse() if recurse else streamObj.iter

    notes = sIter.getElementsByClass('GeneralNote')

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
        averageHeight = 29
    else:
        averageHeight = (totalHeight + 0.0) / totalNotes

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
class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        '''
        Test copying all objects defined in this module
        '''
        import copy
        import sys
        import types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            # noinspection PyTypeChecker
            if callable(name) and not isinstance(name, types.FunctionType):
                try:  # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                unused_a = copy.copy(obj)
                unused_b = copy.deepcopy(obj)

    def testConversionClassMatch(self):
        from xml.etree.ElementTree import fromstring as El
        from music21.musicxml.xmlToM21 import MeasureParser
        from music21 import clef
        # need to get music21.clef.X, not X, because
        # we are comparing the result to a translation outside
        # clef.py
        src = [
            [('G', 1, 0), clef.FrenchViolinClef],
            [('G', 2, 0), clef.TrebleClef],
            [('G', 2, -1), clef.Treble8vbClef],
            [('G', 2, 1), clef.Treble8vaClef],
            [('G', 3, 0), clef.GSopranoClef],
            [('C', 1, 0), clef.SopranoClef],
            [('C', 2, 0), clef.MezzoSopranoClef],
            [('C', 3, 0), clef.AltoClef],
            [('C', 4, 0), clef.TenorClef],
            [('C', 5, 0), clef.CBaritoneClef],
            [('F', 3, 0), clef.FBaritoneClef],
            [('F', 4, 0), clef.BassClef],
            [('F', 4, 1), clef.Bass8vaClef],
            [('F', 4, -1), clef.Bass8vbClef],
            [('F', 5, 0), clef.SubBassClef],
            [('TAB', 5, 0), clef.TabClef]
        ]

        MP = MeasureParser()

        for params, className in src:
            sign, line, octaveChange = params
            mxClef = El(r'<clef><sign>'
                        + sign + '</sign><line>'
                        + str(line) + '</line>'
                        + '<clef-octave-change>'
                        + str(octaveChange)
                        + '</clef-octave-change></clef>')
            c = MP.xmlToClef(mxClef)

            # environLocal.printDebug([type(c).__name__])

            self.assertEqual(c.sign, params[0])
            self.assertEqual(c.line, params[1])
            self.assertEqual(c.octaveChange, params[2])
            self.assertIsInstance(c, className,
                                  'Failed Conversion of classes: %s is not a %s' % (c, className))

    def testContexts(self):
        from music21 import stream
        from music21 import note
        from music21 import meter

        n1 = note.Note('C')
        n1.offset = 10
        c1 = AltoClef()
        c1.offset = 0
        s1 = stream.Stream([c1, n1])

        self.assertIs(s1.recurse().notes[0].getContextByClass(Clef), c1)
        # equally good: getContextsByClass(Clef)[0]

        del s1

        n2 = note.Note('D')
        n2.duration.type = 'whole'
        n3 = note.Note('E')
        n3.duration.type = 'whole'
        ts1 = meter.TimeSignature('4/4')
        s2 = stream.Stream()
        s2.append(c1)
        s2.append(ts1)
        s2.append(n2)
        s2.append(n3)
        s2.makeMeasures()
        self.assertIs(n2.getContextByClass(Clef), c1)

        del s2

        n4 = note.Note('F')
        n4.duration.type = 'half'
        n5 = note.Note('G')
        n5.duration.type = 'half'
        n6 = note.Note('A')
        n6.duration.type = 'whole'

        ts2 = meter.TimeSignature('4/4')
        bc1 = BassClef()
        tc1 = TrebleClef()

        s3 = stream.Stream()
        s3.append(bc1)
        s3.append(ts2)
        s3.append(n4)
        s3.append(tc1)
        s3.append(n5)
        s3.append(n6)
        s3.makeMeasures()

        self.assertIs(n4.getContextByClass(stream.Measure), n5.getContextByClass(stream.Measure))
        self.assertIs(n4.getContextByClass(Clef), bc1)
        self.assertIs(n5.getContextByClass(Clef), tc1)
        self.assertIs(n6.getContextByClass(Clef), tc1)


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Clef, TrebleClef, BassClef]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

