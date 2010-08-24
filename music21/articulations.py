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

'''Classes for representing and processing articulations. Specific articulations are modeled as :class:`~music21.articulation.Articulation` subclasses. 

 A :class:`~music21.note.Note` object has a :attr:`~music21.note.Note.articulations` attribute. This list can be used to store one or more :class:`music21.articulation.Articulation` subclasses.

As much as possible, MusicXML names are used for Articulation classes, with xxx-yyy changed to XxxYyy 
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
    '''Base class for all Articulation sub-classes. 
    '''
    def __init__(self):
        music21.Music21Object.__init__(self)
        self._mxName = None # specified in subclasses
        self.placement = 'above'

    def __eq__(self, other):
        '''Equality. Based only on the class name, as not other attributes are independent of context and deployment.

        >>> from music21 import *
        >>> at1 = StrongAccent()
        >>> at2 = StrongAccent()
        >>> at3 = Accent()
        >>> at4 = Staccatissimo()
        >>> at5 = Staccato()
        >>> at6 = Spiccato()
        >>> at1 == at2
        True
        >>> at1 == at3
        False
        >>> at6 == at6
        True
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
        >>> at1 = StrongAccent()
        >>> at2 = StrongAccent()
        >>> at3 = Accent()
        >>> at4 = Staccatissimo()
        >>> at5 = Staccato()
        >>> at6 = Spiccato()
        >>> at1 != at2
        False
        >>> at1 != at3
        True
        '''
        return not self.__eq__(other)



    def _getMX(self):
        '''Return an mxArticulationMark

        >>> from music21 import *
        >>> a = Accent()
        >>> mxArticulationMark = a.mx
        >>> mxArticulationMark
        <accent placement=above>
        '''

        #mxArticulations = musicxml.Articulations()
        mxArticulationMark = musicxml.ArticulationMark(self._mxName)
        mxArticulationMark.set('placement', self.placement)
        #mxArticulations.append(mxArticulationMark)
        return mxArticulationMark


    def _setMX(self, mxArticulationMark):
        '''Provided an mxArticulation object (not an mxArticulations object)
        to configure the object.

        >>> from music21 import *
        >>> mxArticulationMark = musicxml.ArticulationMark('accent')
        >>> a = Articulation()
        >>> a.mx = mxArticulationMark
        >>> a._mxName
        'accent'
        '''
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
        >>> a = Accent()
        '''
        DynamicArticulation.__init__(self)
        self._mxName = 'accent'

class StrongAccent(Accent):
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = StrongAccent()
        '''
        Accent.__init__(self)
        self._mxName = 'strong-accent'

class Staccato(LengthArticulation):
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = Staccato()
        '''
        LengthArticulation.__init__(self)
        self._mxName = 'staccato'

class Staccatissimo(Staccato):
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = Staccatissimo()
        '''
        Staccato.__init__(self)
        self._mxName = 'staccatissimo'

class Spiccato(Staccato):
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = Spiccato()
        '''
        Staccato.__init__(self)
        self._mxName = 'spiccato'

class Tenuto(LengthArticulation):
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = Tenuto()
        '''
        LengthArticulation.__init__(self)
        self._mxName = 'tenuto'

class DetachedLegato(LengthArticulation):
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = DetachedLegato()
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
class TechnicalIndication(object):
    '''
    TechnicalIndications (MusicXML: technical) give performance indications specific to different instrument types.
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
    in MusicXML, Pizzicato is an element of every note.  Here we represent pizzes along with all bowing marks.
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




