#-------------------------------------------------------------------------------
# Name:         articulations.py
# Purpose:      music21 classes for representing articulations
#
# Authors:      Michael Scott Cuthbert
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

_MOD = "articulations.py"



class Articulation(music21.Music21Object):
    pass

class LengthArticulation(Articulation):
    pass

class DynamicArticulation(Articulation):
    pass

class PitchArticulation(Articulation):
    pass

class TimbreArticulation(Articulation):
    pass

class Accent(DynamicArticulation):
    pass

class StrongAccent(Accent):
    pass

class Staccato(LengthArticulation):
    pass

class Staccatissimo(Staccato):
    pass

class Spiccato(Staccato):
    pass

class Tenuto(LengthArticulation):
    pass

class DetachedLegato(LengthArticulation):
    pass

class IndeterminantSlide(PitchArticulation):    
    pass

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



########
class TechnicalIndication(object):
    '''
    TechnicalIndications (MusicXML: technical) give performance indications specific to different instrument types.
    '''
    pass

class Harmonic(TechnicalIndication):
    pass

class Bowing(TechnicalIndication):  
    pass

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




