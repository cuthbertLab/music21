#-------------------------------------------------------------------------------
# Name:         articulations.py
# Purpose:      music21 classes for representing articulations
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
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


>>> from music21 import *
>>> n1 = note.Note("D#4")
>>> n1.articulations.append(articulations.Tenuto())
>>> #_DOCS_SHOW n1.show()

>>> c1 = chord.Chord(["C3","G4","E-5"])
>>> c1.articulations = [articulations.OrganHeel(), articulations.Accent() ]
>>> #_DOCS_SHOW c1.show()




A longer test showing the utility of the module:




>>> from music21 import *


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

import doctest, unittest

import music21

from music21 import musicxml
from music21 import environment
_MOD = "articulations.py"
environLocal = environment.Environment(_MOD)



class ArticulationException(Exception):
    pass

#-------------------------------------------------------------------------------
class Articulation(music21.Music21Object):
    '''
    Base class for all Articulation sub-classes. 
    
    >>> from music21 import *
    >>> x = articulations.Articulation()
    >>> x.placement = 'below'
    
    '''
    def __init__(self):
        music21.Music21Object.__init__(self)
        self._mxName = None # specified in subclasses
        self.placement = 'above'

    def __repr__(self):
        return '<music21.articulations.%s>' % (self.__class__.__name__)
    
    def __eq__(self, other):
        '''
        Equality. Based only on the class name, 
        as other other attributes are independent of context and deployment.

        >>> from music21 import *
        >>> at1 = articulations.StrongAccent()
        >>> at2 = articulations.StrongAccent()
        >>> at1.placement = 'above'
        >>> at2.placement = 'below'
        >>> at1 == at2
        True




        Comparison between classes and with the object itself behaves as expected
        



        >>> at3 = articulations.Accent()
        >>> at4 = articulations.Staccatissimo()
        >>> at1 == at3
        False
        >>> at4 == at4
        True



        #OMIT_FROM_DOCS
        >>> at5 = articulations.Staccato()
        >>> at6 = articulations.Spiccato()
        >>> [at1, at4, at3] == [at1, at4, at3]
        True
        >>> [at1, at2, at3] == [at2, at3, at1]
        False
        >>> set([at1, at2, at3]) == set([at2, at3, at1])
        True 
        >>> at6 == None
        False
        '''
        # checks pitch.octave, pitch.accidental, uses Pitch.__eq__
        if other == None or not isinstance(other, Articulation):
            return False
        elif self.__class__ == other.__class__:
            return True
        return False

    def __ne__(self, other):
        '''Inequality. Needed for pitch comparisons.

        >>> from music21 import *
        >>> at1 = articulations.StrongAccent()
        >>> at2 = articulations.StrongAccent()
        >>> at3 = articulations.Accent()
        >>> at4 = articulations.Staccatissimo()
        >>> at5 = articulations.Staccato()
        >>> at6 = articulations.Spiccato()
        >>> at1 != at2
        False
        >>> at1 != at3
        True
        '''
        return not self.__eq__(other)



    def _getMX(self):
        '''
        Advanced method for musicxml output.  Not needed by most users.

        As a getter: Returns a class (mxArticulationMark) that represents the
        MusicXML structure of an articulation mark.

        >>> from music21 import *
        >>> a = articulations.Accent()
        >>> mxArticulationMark = a.mx
        >>> mxArticulationMark
        <accent placement=above>



        As a setter: Provided an musicxml.ArticulationMark object (not an mxArticulations object)
        configure the music21 object.


        Create both a musicxml.ArticulationMark object and a conflicting music21 object:
        
        
        
        >>> from music21 import *
        >>> mxArticulationMark = musicxml.ArticulationMark('accent')
        >>> mxArticulationMark.set('placement', 'below')
        >>> a = articulations.Tenuto()
        >>> a.placement = 'above'



        Now override the music21 object with the mxArticulationMark object's characteristics




        >>> a.mx = mxArticulationMark
        >>> a._mxName
        'accent'
        >>> 'Tenuto' in a.classes
        False
        >>> 'Accent' in a.classes
        True
        >>> a.placement
        'below'
        '''

        #mxArticulations = musicxml.Articulations()
        mxArticulationMark = musicxml.ArticulationMark(self._mxName)
        mxArticulationMark.set('placement', self.placement)
        #mxArticulations.append(mxArticulationMark)
        return mxArticulationMark


    def _setMX(self, mxArticulationMark):
        self.placement = mxArticulationMark.get('placement')
        self._mxName = mxArticulationMark.tag
        if self._mxName == 'accent':
            self.__class__ = Accent
        elif self._mxName == 'strong-accent':
            self.__class__ = StrongAccent
        elif self._mxName == 'staccato':
            self.__class__ = Staccato
        elif self._mxName == 'staccatissimo':
            self.__class__ = Staccatissimo
        elif self._mxName == 'spiccato':
            self.__class__ = Spiccato
        elif self._mxName == 'tenuto':
            self.__class__ = Tenuto
        elif self._mxName == 'detached-legato':
            self.__class__ = DetachedLegato
        # add more, below

    mx = property(_getMX, _setMX)


#-------------------------------------------------------------------------------
class LengthArticulation(Articulation):
    def __init__(self):
        Articulation.__init__(self)

class DynamicArticulation(Articulation):
    def __init__(self):
        Articulation.__init__(self)

class PitchArticulation(Articulation):
    def __init__(self):
        Articulation.__init__(self)

class TimbreArticulation(Articulation):
    def __init__(self):
        Articulation.__init__(self)


#-------------------------------------------------------------------------------
class Accent(DynamicArticulation):
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = articulations.Accent()
        '''
        DynamicArticulation.__init__(self)
        self._mxName = 'accent'

class StrongAccent(Accent):
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = articulations.StrongAccent()
        '''
        Accent.__init__(self)
        self._mxName = 'strong-accent'

class Staccato(LengthArticulation):
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = articulations.Staccato()
        '''
        LengthArticulation.__init__(self)
        self._mxName = 'staccato'

class Staccatissimo(Staccato):
    def __init__(self):
        '''
        A very short note (derived from staccato), usually
        represented as a wedge.
        
        >>> from music21 import *
        >>> a = articulations.Staccatissimo()
        '''
        Staccato.__init__(self)
        self._mxName = 'staccatissimo'

class Spiccato(Staccato):
    def __init__(self):
        '''
        A staccato note + accent in one
        
        >>> from music21 import *
        >>> a = articulations.Spiccato()
        '''
        Staccato.__init__(self)
        self._mxName = 'spiccato'

class Tenuto(LengthArticulation):
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = articulations.Tenuto()
        '''
        LengthArticulation.__init__(self)
        self._mxName = 'tenuto'

class DetachedLegato(LengthArticulation):
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = articulations.DetachedLegato()
        '''
        LengthArticulation.__init__(self)
        self._mxName = 'detached-legato'


class IndeterminantSlide(PitchArticulation):    
    def __init__(self):
        PitchArticulation.__init__(self)

class Scoop(IndeterminantSlide):
    pass

class Plop(IndeterminantSlide):
    pass

class Doit(IndeterminantSlide):
    pass

class Falloff(IndeterminantSlide):
    pass

class BreathMark(LengthArticulation):
    pass

class Caesura(Articulation):
    pass

class Stress(DynamicArticulation):
    pass

class Unstress(DynamicArticulation):
    pass



#-------------------------------------------------------------------------------
class TechnicalIndication(Articulation):
    '''
    TechnicalIndications (MusicXML: technical) give performance 
    indications specific to different instrument types, such
    as harmonics or bowing.
    '''
    pass

class Harmonic(TechnicalIndication):
    pass

class Bowing(TechnicalIndication):  
    pass


#-------------------------------------------------------------------------------
class UpBow(Bowing):
    pass

class DownBow(Bowing):
    pass

class StringHarmonic(Bowing, Harmonic):
    pass

class OpenString(Bowing):
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


    def testArticulationEquality(self):
        a1 = Accent()
        a2 = Accent()
        a3 = StrongAccent()
        a4 = StrongAccent()

        self.assertEqual(a1, a2)
        self.assertEqual(a3, a4)

        # in order lists
        self.assertEqual([a1, a3], [a2, a4])

        self.assertEqual(set([a1, a3]), set([a1, a3]))
        self.assertEqual(set([a1, a3]), set([a3, a1]))

        # comparison of sets of different objects to not pass
        self.assertEqual(list(set([a1, a3])), list(set([a2, a4])))


if __name__ == "__main__":
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof


