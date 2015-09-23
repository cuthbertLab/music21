# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         articulations.py
# Purpose:      music21 classes for representing articulations
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

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



>>> n1 = note.Note("D#4")
>>> n1.articulations.append(articulations.Tenuto())
>>> #_DOCS_SHOW n1.show()

>>> c1 = chord.Chord(["C3","G4","E-5"])
>>> c1.articulations = [articulations.OrganHeel(), articulations.Accent() ]
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
>>> n5.quarterLength = 1.3333333333333
>>> s.append(n5)


>>> n6 = note.Note('b-4')
>>> n6.articulations = [articulations.Staccatissimo(), articulations.Tenuto()] 
>>> n6.quarterLength = 0.6666666666667
>>> s.append(n6)


>>> s.metadata = metadata.Metadata()
>>> s.metadata.title = 'Prova articolazioni' # ital: "Articulation Test"
>>> s.metadata.composer = 'Giuliano Lancioni'


>>> #_DOCS_SHOW s.show()

.. image:: images/prova_articolazioni.*
    :width: 628


'''

import unittest

from music21 import base
from music21 import exceptions21
from music21 import environment
_MOD = "articulations.py"
environLocal = environment.Environment(_MOD)



class ArticulationException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Articulation(base.Music21Object):
    '''
    Base class for all Articulation sub-classes. 
    
    
    >>> x = articulations.Articulation()
    >>> x.placement = 'below'
    
    '''
    def __init__(self):
        base.Music21Object.__init__(self)
        self.name = None # specified in subclasses
        self.placement = 'above'
        # declare a unit interval shift for the performance of this articulation
        self._volumeShift = 0.0 

    def __repr__(self):
        return '<music21.articulations.%s>' % (self.__class__.__name__)
    
#     def __eq__(self, other):
#         '''
#         Equality. Based only on the class name, 
#         as other other attributes are independent of context and deployment.
# 
#         
#         >>> at1 = articulations.StrongAccent()
#         >>> at2 = articulations.StrongAccent()
#         >>> at1.placement = 'above'
#         >>> at2.placement = 'below'
#         >>> at1 == at2
#         True
# 
# 
#         Comparison between classes and with the object itself behaves as expected
# 
# 
#         >>> at3 = articulations.Accent()
#         >>> at4 = articulations.Staccatissimo()
#         >>> at1 == at3
#         False
#         >>> at4 == at4
#         True
# 
# 
#         OMIT_FROM_DOCS
#         
#         >>> at5 = articulations.Staccato()
#         >>> at6 = articulations.Spiccato()
#         >>> [at1, at4, at3] == [at1, at4, at3]
#         True
#         >>> [at1, at2, at3] == [at2, at3, at1]
#         False
#         >>> set([at1, at2, at3]) == set([at2, at3, at1])
#         True 
#         >>> at6 == None
#         False
#         '''
#         # checks pitch.octave, pitch.accidental, uses Pitch.__eq__
#         if other == None or not isinstance(other, Articulation):
#             return False
#         elif self.__class__ == other.__class__:
#             return True
#         return False
# 
#     def __ne__(self, other):
#         '''Inequality. Needed for pitch comparisons.
# 
#         
#         >>> at1 = articulations.StrongAccent()
#         >>> at2 = articulations.StrongAccent()
#         >>> at3 = articulations.Accent()
#         >>> at4 = articulations.Staccatissimo()
#         >>> at5 = articulations.Staccato()
#         >>> at6 = articulations.Spiccato()
#         >>> at1 != at2
#         False
#         >>> at1 != at3
#         True
#         '''
#         return not self.__eq__(other)

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
        >>> at1.volumeShift > .1
        True
        ''')

#-------------------------------------------------------------------------------
class LengthArticulation(Articulation):
    '''
    Superclass for all articulations that change the length of a note.
    '''
    def __init__(self):
        Articulation.__init__(self)

class DynamicArticulation(Articulation):
    '''
    Superclass for all articulations that change the dynamic of a note.
    '''
    def __init__(self):
        Articulation.__init__(self)

class PitchArticulation(Articulation):
    '''
    Superclass for all articulations that change the pitch of a note.
    '''
    def __init__(self):
        Articulation.__init__(self)

class TimbreArticulation(Articulation):
    '''
    Superclass for all articulations that change the timbre of a note.
    '''
    def __init__(self):
        Articulation.__init__(self)


#-------------------------------------------------------------------------------
class Accent(DynamicArticulation):
    def __init__(self):
        '''
        
        >>> a = articulations.Accent()
        '''
        DynamicArticulation.__init__(self)
        self.name = 'accent'
        self._volumeShift = 0.1


class StrongAccent(Accent):
    def __init__(self):
        '''
        
        >>> a = articulations.StrongAccent()
        '''
        Accent.__init__(self)
        self.name = 'strong accent'
        self._volumeShift = 0.15

class Staccato(LengthArticulation):
    def __init__(self):
        '''
        
        >>> a = articulations.Staccato()
        '''
        LengthArticulation.__init__(self)
        self.name = 'staccato'
        self._volumeShift = 0.05

class Staccatissimo(Staccato):
    def __init__(self):
        '''
        A very short note (derived from staccato), usually
        represented as a wedge.
        
        
        >>> a = articulations.Staccatissimo()
        '''
        Staccato.__init__(self)
        self.name = 'staccatissimo'
        self._volumeShift = 0.05

class Spiccato(Staccato):
    def __init__(self):
        '''
        A staccato note + accent in one
        
        
        >>> a = articulations.Spiccato()
        '''
        Staccato.__init__(self)
        self.name = 'spiccato'
        self._volumeShift = 0.05

class Tenuto(LengthArticulation):
    def __init__(self):
        '''
        
        >>> a = articulations.Tenuto()
        '''
        LengthArticulation.__init__(self)
        self.name = 'tenuto'
        self._volumeShift = -0.05

class DetachedLegato(LengthArticulation):
    def __init__(self):
        '''
        
        >>> a = articulations.DetachedLegato()
        '''
        LengthArticulation.__init__(self)
        self.name = 'detached legato'
        self._volumeShift = 0


class IndeterminantSlide(PitchArticulation):    
    def __init__(self):
        PitchArticulation.__init__(self)

class Scoop(IndeterminantSlide):
    def __init__(self):
        '''
        
        >>> a = articulations.Scoop()
        '''
        IndeterminantSlide.__init__(self)


class Plop(IndeterminantSlide):
    def __init__(self):
        '''
        
        >>> a = articulations.Plop()
        '''
        IndeterminantSlide.__init__(self)

class Doit(IndeterminantSlide):
    def __init__(self):
        '''
        
        >>> a = articulations.Doit()
        '''
        IndeterminantSlide.__init__(self)

class Falloff(IndeterminantSlide):
    def __init__(self):
        '''
        
        >>> a = articulations.Falloff()
        '''
        IndeterminantSlide.__init__(self)

class BreathMark(LengthArticulation):
    def __init__(self):
        '''
        
        >>> a = articulations.BreathMark()
        '''
        LengthArticulation.__init__(self)

class Caesura(Articulation):
    def __init__(self):
        '''
        
        >>> a = articulations.Caesura()
        '''
        Articulation.__init__(self)

class Stress(DynamicArticulation):
    def __init__(self):
        '''
        
        >>> a = articulations.Stress()
        '''
        DynamicArticulation.__init__(self)

class Unstress(DynamicArticulation):
    def __init__(self):
        '''
        
        >>> a = articulations.Unstress()
        '''
        DynamicArticulation.__init__(self)



#-------------------------------------------------------------------------------
class TechnicalIndication(Articulation):
    '''
    TechnicalIndications (MusicXML: technical) give performance 
    indications specific to different instrument types, such
    as harmonics or bowing.
    '''
    pass

class Harmonic(TechnicalIndication):
    def __init__(self):
        '''
        
        >>> a = articulations.Harmonic()
        '''
        TechnicalIndication.__init__(self)

class Bowing(TechnicalIndication):  
    def __init__(self):
        '''
        
        >>> a = articulations.Bowing()
        '''
        TechnicalIndication.__init__(self)


#-------------------------------------------------------------------------------
class UpBow(Bowing):
    def __init__(self):
        '''
        
        >>> a = articulations.UpBow()
        '''
        Bowing.__init__(self)

class DownBow(Bowing):
    def __init__(self):
        '''
        
        >>> a = articulations.DownBow()
        '''
        Bowing.__init__(self)

class StringHarmonic(Bowing, Harmonic):
    pass

class OpenString(Bowing):
    pass

class StringIndication(Bowing):
    pass


class StringThumbPosition(Bowing):
    '''
    MusicXML -- thumb-position
    '''
    pass

class StringFingering(Bowing):
    '''
    MusicXML -- fingering
    '''
    pass

class Pizzicato(Bowing):
    '''
    in MusicXML, Pizzicato is an element of every note.  
    Here we represent pizzes along with all bowing marks.
    '''
    pass
    
    ### for pluck see FrettedPluck

class SnapPizzicato(Pizzicato):
    pass

class NailPizzicato(Pizzicato):
    '''not in MusicXML'''
    pass

class FretIndication(TechnicalIndication):
    pass

class FrettedPluck(FretIndication):
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

class OrganIndication(TechnicalIndication):
    pass

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








#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

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
#         #self.assertEqual(list(set([a1, a3])), list(set([a2, a4])))


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Articulation]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof


