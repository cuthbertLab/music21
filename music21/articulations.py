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
music21.articulations -- Classes for dealing with articulations

As much as possible, MusicXML names are used, with xxx-yyy changed to XxxYyy 
'''

import doctest, unittest

import music21

from music21 import musicxml
from music21 import environment
_MOD = "articulations.py"
environLocal = environment.Environment(_MOD)



class ClefException(Exception):
    pass

#-------------------------------------------------------------------------------
class Articulation(music21.Music21Object):
    def __init__(self):
        music21.Music21Object.__init__(self)
        self._mxName = None # specified in subclasses
        self.placement = 'above'

    def _getMX(self):
        '''
        >>> a = Accent()
        >>> mxArticulations = a.mx
        >>> mxArticulations.componentList[0].tag
        'accent'
        '''

        mxArticulations = musicxml.Articulations()
        mxArticulationMark = musicxml.ArticulationMark(self._mxName)
        mxArticulationMark.set('placement', self.placement)

        mxArticulations.append(mxArticulationMark)
        return mxArticulations


    def _setMX(self, mxArticulationMark):
        '''Provided an mxArticulation object (not an mxArticulations object)
        to configure the object.

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
        >>> a = Accent()
        '''
        DynamicArticulation.__init__(self)
        self._mxName = 'accent'

class StrongAccent(Accent):
    def __init__(self):
        '''
        >>> a = StrongAccent()
        '''
        Accent.__init__(self)
        self._mxName = 'strong-accent'

class Staccato(LengthArticulation):
    def __init__(self):
        '''
        >>> a = Staccato()
        '''
        LengthArticulation.__init__(self)
        self._mxName = 'staccato'

class Staccatissimo(Staccato):
    def __init__(self):
        '''
        >>> a = Staccatissimo()
        '''
        Staccato.__init__(self)
        self._mxName = 'staccatissimo'

class Spiccato(Staccato):
    def __init__(self):
        '''
        >>> a = Spiccato()
        '''
        Staccato.__init__(self)
        self._mxName = 'spiccato'

class Tenuto(LengthArticulation):
    def __init__(self):
        '''
        >>> a = Tenuto()
        '''
        LengthArticulation.__init__(self)
        self._mxName = 'tenuto'

class DetachedLegato(LengthArticulation):
    def __init__(self):
        '''
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


if __name__ == "__main__":
    music21.mainTest(Test)




