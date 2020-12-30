# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         articulations.py
# Purpose:      music21 classes for representing articulations
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2013 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

'''
Classes for representing and processing articulations.
Specific articulations are modeled as :class:`~music21.articulation.Articulation` subclasses.

A :class:`~music21.note.Note` object has a :attr:`~music21.note.Note.articulations` attribute.
This list can be used to store one or more :class:`music21.articulation.Articulation` subclasses.

As much as possible, MusicXML names are used for Articulation classes,
with xxx-yyy changed to XxxYyy.  For instance, "strong-accent" in
MusicXML is "StrongAccent" here.

Fingering and other playing marks are found here.  Fermatas, trills, etc.
are found in music21.expressions.



>>> n1 = note.Note('D#4')
>>> n1.articulations.append(articulations.Tenuto())
>>> #_DOCS_SHOW n1.show()

>>> c1 = chord.Chord(['C3', 'G4', 'E-5'])
>>> c1.articulations = [articulations.OrganHeel(), articulations.Accent()]
>>> #_DOCS_SHOW c1.show()

A longer test showing the utility of the module:

>>> s = stream.Stream()
>>> n1 = note.Note('c#5')
>>> n1.articulations = [articulations.Accent()]
>>> n1.quarterLength = 1.25
>>> s.append(n1)

>>> n2 = note.Note('d5')
>>> n2.articulations = [articulations.StrongAccent()]
>>> n2.quarterLength = 0.75
>>> s.append(n2)

>>> n3 = note.Note('b4')
>>> n3.articulations = [articulations.Staccato()]
>>> n3.quarterLength = 1.25
>>> n3.tie = tie.Tie('start')
>>> s.append(n3)

>>> n4 = note.Note('b4')
>>> n4.articulations = [articulations.Staccatissimo()]
>>> n4.quarterLength = 0.75
>>> s.append(n4)

>>> n5 = note.Note('a4')
>>> n5.articulations = [articulations.Tenuto()]
>>> n5.quarterLength = 4/3
>>> s.append(n5)

>>> n6 = note.Note('b-4')
>>> n6.articulations = [articulations.Staccatissimo(), articulations.Tenuto()]
>>> n6.quarterLength = 2/3
>>> s.append(n6)

>>> s.metadata = metadata.Metadata()
>>> s.metadata.title = 'Prova articolazioni'  # ital: 'Articulation Test'
>>> s.metadata.composer = 'Giuliano Lancioni'

>>> #_DOCS_SHOW s.show()

.. image:: images/prova_articolazioni.*
    :width: 628

'''
from typing import Optional
import unittest

from music21 import base
from music21 import common
from music21 import exceptions21
from music21 import environment
from music21 import style

_MOD = 'articulations'
environLocal = environment.Environment(_MOD)



class ArticulationException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------
class Articulation(base.Music21Object):
    '''
    Base class for all Articulation sub-classes.

    >>> x = articulations.Articulation()
    >>> x.placement = 'below'
    >>> x.style.absoluteY = 20
    >>> x.displayText = '>'

    '''
    _styleClass = style.TextStyle

    def __init__(self):
        super().__init__()
        self.placement = None
        # declare a unit interval shift for the performance of this articulation
        self._volumeShift: float = 0.0
        self.lengthShift: float = 1.0
        self.tieAttach: str = 'first'  # attach to first or last or all notes after split
        self.displayText: Optional[str] = None

    def _reprInternal(self):
        return ''

    @property
    def name(self) -> str:
        '''
        returns the name of the articulation, which is generally the
        class name without the leading letter lowercase.

        Subclasses can override this as necessary.

        >>> st = articulations.Staccato()
        >>> st.name
        'staccato'

        >>> sp = articulations.SnapPizzicato()
        >>> sp.name
        'snap pizzicato'
        '''
        className = self.__class__.__name__
        return common.camelCaseToHyphen(className, replacement=' ')

    # def __eq__(self, other):
    #     '''
    #     Equality. Based only on the class name,
    #     as other other attributes are independent of context and deployment.
    #
    #
    #     >>> at1 = articulations.StrongAccent()
    #     >>> at2 = articulations.StrongAccent()
    #     >>> at1.placement = 'above'
    #     >>> at2.placement = 'below'
    #     >>> at1 == at2
    #     True
    #
    #
    #     Comparison between classes and with the object itself behaves as expected
    #
    #
    #     >>> at3 = articulations.Accent()
    #     >>> at4 = articulations.Staccatissimo()
    #     >>> at1 == at3
    #     False
    #     >>> at4 == at4
    #     True
    #
    #
    #     OMIT_FROM_DOCS
    #
    #     >>> at5 = articulations.Staccato()
    #     >>> at6 = articulations.Spiccato()
    #     >>> [at1, at4, at3] == [at1, at4, at3]
    #     True
    #     >>> [at1, at2, at3] == [at2, at3, at1]
    #     False
    #     >>> set([at1, at2, at3]) == set([at2, at3, at1])
    #     True
    #     >>> at6 == None
    #     False
    #     '''
    #     # checks pitch.octave, pitch.accidental, uses Pitch.__eq__
    #     if other == None or not isinstance(other, Articulation):
    #         return False
    #     elif self.__class__ == other.__class__:
    #         return True
    #     return False
    #

    def _getVolumeShift(self):
        return self._volumeShift

    def _setVolumeShift(self, value):
        # value should be between 0 and 1
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        self._volumeShift = value

    volumeShift = property(_getVolumeShift, _setVolumeShift, doc='''
        Get or set the volumeShift of this Articulation. This value, between -1 and 1,
        that is used to shift the final Volume of the object it is attached to.


        >>> at1 = articulations.StrongAccent()
        >>> at1.volumeShift > 0.1
        True
        ''')

# ------------------------------------------------------------------------------
class LengthArticulation(Articulation):
    '''
    Superclass for all articulations that change the length of a note.
    '''
    def __init__(self):
        super().__init__()
        self.tieAttach = 'last'

class DynamicArticulation(Articulation):
    '''
    Superclass for all articulations that change the dynamic of a note.
    '''

class PitchArticulation(Articulation):
    '''
    Superclass for all articulations that change the pitch of a note.
    '''

class TimbreArticulation(Articulation):
    '''
    Superclass for all articulations that change the timbre of a note.
    '''


# ------------------------------------------------------------------------------
class Accent(DynamicArticulation):
    '''

    >>> a = articulations.Accent()
    '''
    def __init__(self):
        super().__init__()
        self._volumeShift = 0.1


class StrongAccent(Accent):
    '''
    Like an accent but even stronger.  Has an extra
    attribute of pointDirection

    >>> a = articulations.StrongAccent()
    >>> a.pointDirection
    'up'
    >>> a.pointDirection = 'down'
    >>> a.pointDirection
    'down'
    '''
    def __init__(self):
        super().__init__()
        self._volumeShift = 0.15
        self.pointDirection = 'up'

class Staccato(LengthArticulation):
    '''

    >>> a = articulations.Staccato()
    '''
    def __init__(self):
        super().__init__()
        self._volumeShift = 0.05
        self.lengthShift = 0.7

class Staccatissimo(Staccato):
    '''
    A very short note (derived from staccato), usually
    represented as a wedge.

    >>> a = articulations.Staccatissimo()
    '''
    def __init__(self):
        super().__init__()
        self._volumeShift = 0.05
        self.lengthShift = 0.5

class Spiccato(Staccato, Accent):
    '''
    A staccato note + accent in one

    >>> spiccato = articulations.Spiccato()
    >>> staccato = articulations.Staccato()
    >>> accent = articulations.Accent()
    >>> spiccato.lengthShift == staccato.lengthShift
    True
    >>> spiccato.volumeShift == accent.volumeShift
    True
    '''
    def __init__(self):
        Staccato.__init__(self)
        storedLengthShift = self.lengthShift
        Accent.__init__(self)  # order matters...
        self.lengthShift = storedLengthShift


class Tenuto(LengthArticulation):
    '''
    >>> a = articulations.Tenuto()
    '''
    def __init__(self):
        super().__init__()
        self._volumeShift = -0.05  # is this the right thing to do?
        self.lengthShift = 1.1

class DetachedLegato(LengthArticulation):
    '''
    >>> a = articulations.DetachedLegato()
    '''
    def __init__(self):
        super().__init__()
        self.lengthShift = 0.9

# --------- indeterminate slides

class IndeterminateSlide(PitchArticulation):
    '''
    Represents a whole class of slides that are
    of an indeterminate pitch amount (scoops, plops, etc.)

    All these have style information of .style.lineShape
    .style.lineType, .style.dashLength, and .style.spaceLength
    '''
    _styleClass = style.LineStyle


class Scoop(IndeterminateSlide):
    '''
    An indeterminateSlide coming before the main note and going up

    >>> a = articulations.Scoop()
    '''


class Plop(IndeterminateSlide):
    '''
    An indeterminateSlide coming before the main note and going down.

    >>> a = articulations.Plop()
    '''

class Doit(IndeterminateSlide):
    '''
    An indeterminateSlide coming after the main note and going up.

    >>> a = articulations.Doit()
    '''
    def __init__(self):
        super().__init__()
        self.tieAttach = 'last'

class Falloff(IndeterminateSlide):
    '''
    An indeterminateSlide coming after the main note and going down.

    >>> a = articulations.Falloff()
    '''
    def __init__(self):
        super().__init__()
        self.tieAttach = 'last'

# --------- end indeterminate slide


class BreathMark(LengthArticulation):
    '''
    Can have as a symbol 'comma' or 'tick' or None

    >>> a = articulations.BreathMark()
    >>> a.symbol = 'comma'
    '''
    def __init__(self):
        super().__init__()
        self.lengthShift = 0.7
        self.symbol = None

class Caesura(Articulation):
    '''
    >>> a = articulations.Caesura()
    '''

class Stress(DynamicArticulation, LengthArticulation):
    '''
    An articulation indicating stress.  Played a little longer and louder.

    >>> a = articulations.Stress()
    '''
    def __init__(self):
        super().__init__()
        self._volumeShift = 0.05
        self.lengthShift = 1.1

class Unstress(DynamicArticulation):
    '''
    An articulation indicating lack of stress.  Played a little quieter.

    >>> a = articulations.Unstress()
    '''
    def __init__(self):
        super().__init__()
        self._volumeShift = -0.05


# ------------------------------------------------------------------------------
class TechnicalIndication(Articulation):
    '''
    TechnicalIndications (MusicXML: technical) give performance
    indications specific to different instrument types, such
    as harmonics or bowing.

    TechnicalIndications can include an optional content.
    '''

class Harmonic(TechnicalIndication):
    '''
    A general harmonic indicator -- StringHarmonic is probably what you want...
    '''

class Bowing(TechnicalIndication):
    '''
    Indication that bowing is being affected.

    >>> a = articulations.Bowing()
    '''

class Fingering(TechnicalIndication):
    '''
    Fingering is a technical indication that covers the fingering of
    a note (in a guitar/fret context, this covers the fret finger,
    see FrettedPluck for that).

    Converts the MusicXML -- <fingering> object

    >>> f = articulations.Fingering(5)
    >>> f
    <music21.articulations.Fingering 5>
    >>> f.fingerNumber
    5

    `.substitution` indicates that this fingering indicates a substitute fingering:

    >>> f.substitution = True

    MusicXML distinguishes between a substitution and an alternate
    fingering:

    >>> f.alternate = True

    Fingerings are the only articulations that apply per note in a chord.
    Other articulations, e.g., accents, apply to the whole chord and will,
    therefore, only be associated with the first note of a chord when serializing.
    Since chords store all articulations in an ordered list, Fingerings
    are mapped implicitly to the notes of a chord in order. Superfluous
    Fingerings will be ignored and may be discarded when serializing.
    '''
    def __init__(self, fingerNumber=None):
        super().__init__()
        self.fingerNumber = fingerNumber
        self.substitution = False
        self.alternate = False

    def _reprInternal(self):
        return str(self.fingerNumber)


# ------------------------------------------------------------------------------
class UpBow(Bowing):
    '''
    >>> a = articulations.UpBow()
    '''

class DownBow(Bowing):
    '''
    >>> a = articulations.DownBow()
    '''

class StringHarmonic(Bowing, Harmonic):
    '''
    Indicates that a note is a harmonic, and can also specify
    whether it is the base pitch, the sounding pitch, or the touching pitch.

    >>> h = articulations.StringHarmonic()
    >>> h.harmonicType
    'natural'
    >>> h.harmonicType = 'artificial'

    pitchType can be 'base', 'sounding', or 'touching' or None

    >>> h.pitchType = 'base'
    '''
    def __init__(self):
        super().__init__()
        self.harmonicType = 'natural'
        self.pitchType = None

class OpenString(Bowing):
    pass

class StringIndication(Bowing):
    '''
    StringIndication indicates which string a note is played on.

    A StringIndication can be constructed as

    >>> si = articulations.StringIndication(2)
    >>> si
    <music21.articulations.StringIndication 2>
    >>> si.number
    2

    If no argument to the constructor is specified, number defaults to 0.
    '''
    def __init__(self, number=0):
        super().__init__()
        self.number = number

    def __repr__(self):
        return f'<music21.articulations.{self.__class__.__name__} {self.number}>'


class StringThumbPosition(Bowing):
    '''
    MusicXML -- thumb-position
    '''
    pass

class StringFingering(StringIndication, Fingering):
    '''
    Indicates a fingering on a specific string.  Nothing special for now.
    '''
    pass

class Pizzicato(Bowing):
    '''
    in MusicXML, Pizzicato is an element of every note.
    Here we represent pizzicatos along with all bowing marks.

    For pluck, see FrettedPluck.
    '''
    pass

class SnapPizzicato(Pizzicato):
    pass

class NailPizzicato(Pizzicato):
    '''
    Does not exist in MusicXML
    '''
    pass

class FretIndication(TechnicalIndication):
    '''
    FretIndication indicates which fret of a string a note is played on.

    A FretIndication can be constructed as

    >>> fi = articulations.FretIndication(3)
    >>> fi
    <music21.articulations.FretIndication 3>
    >>> fi.number
    3

    If no argument to the constructor is specified, number defaults to 0.
    '''
    def __init__(self, number=0):
        super().__init__()
        self.number = number

    def __repr__(self):
        return f'<music21.articulations.{self.__class__.__name__} {self.number}>'

class FrettedPluck(FretIndication, Fingering):
    '''
    specifies plucking fingering for fretted instruments

    pluck in musicxml
    '''
    pass

class HammerOn(FretIndication):
    pass

class PullOff(FretIndication):
    pass

class FretBend(FretIndication):
    bendAlter = None  # music21.interval.Interval object
    preBend = None
    release = None
    withBar = None

class FretTap(FretIndication):
    pass

class WindIndication(TechnicalIndication):
    pass

class WoodwindIndication(WindIndication):
    pass

class BrassIndication(WindIndication):
    pass

class TonguingIndication(WindIndication):
    pass

class DoubleTongue(TonguingIndication):
    pass

class TripleTongue(TonguingIndication):
    pass

class Stopped(WindIndication):
    pass

# -------------------------------
class OrganIndication(TechnicalIndication):
    '''
    Indicates whether a pitch should be played with heel or toe.

    Has one attribute, "substitution" default to False, which
    indicates whether the mark is a substitution mark
    '''
    def __init__(self):
        super().__init__()
        self.substitution = False


class OrganHeel(OrganIndication):
    pass

class OrganToe(OrganIndication):
    pass

class HarpIndication(TechnicalIndication):
    pass

class HarpFingerNails(HarpIndication):
    '''
    musicXML -- fingernails
    '''
    pass

class HandbellIndication(TechnicalIndication):
    '''
    displayText is used to store any of the techniques in handbell music.

    Values are damp, echo, gyro, hand martellato, mallet lift,
    mallet table, martellato, martellato lift,
    muted martellato, pluck lift, and swing
    '''
    pass


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testBasic(self):
        a = FretBend()
        self.assertEqual(a.bendAlter, None)


#     def testArticulationEquality(self):
#         a1 = Accent()
#         a2 = Accent()
#         a3 = StrongAccent()
#         a4 = StrongAccent()
#
#         self.assertEqual(a1, a2)
#         self.assertEqual(a3, a4)
#
#         # in order lists
#         self.assertEqual([a1, a3], [a2, a4])
#
#         self.assertEqual(set([a1, a3]), set([a1, a3]))
#         self.assertEqual(set([a1, a3]), set([a3, a1]))
#
#         # comparison of sets of different objects do not pass
#         # self.assertEqual(list(set([a1, a3])), list(set([a2, a4])))


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Articulation]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

