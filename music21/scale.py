import copy
import unittest, doctest


import music21
from music21 import pitch
from music21.pitch import Pitch
from music21 import stream
from music21.stream import Stream
from music21 import interval


class Scale(music21.Music21Object):
    '''
    Generic class for all scales
    
    Not for general use because a scale can been so many things to
    so many different people
    '''
    
    pass

class DirectionlessScale(Scale):
    '''A DirectionlessScale is the same ascending and descending.
    For instance, the major scale.  A DirectionSensitiveScale has
    two different forms.  For instance, the natural-minor scale.
    One could imagine more complex scales that have different forms
    depending on what scale degree you've just landed on.  Some
    Ragas might be expressible in that way.'''
    
    def ascending(self):
        return self.scaleList
    
    def descending(self):
        tempScale = copy(self.scaleList)
        return tempScale.reverse()
        ## we perform the reverse on a copy of the scaleList so that
        ## in case we are multithreaded later in life, we do not have
        ## a race condition where someone might get self.scaleList as
        ## reversed

class DirectionSensitiveScale(Scale):
    pass

class DiatonicScale(Scale):
    def __init__(self, tonic = Pitch()):
        spacer = " "
        self.tonic = tonic
        self.step = self.tonic.step
        self.accidental = self.tonic.accidental
        self.name = spacer.join([self.tonic.name, self.type]) 
        self.scaleList = self.generateScaleList()

    def generateScaleList(self):
        raise ScaleException("Cannot generate a scale from a DiatonicScale class")

    def pitchFromScaleDegree(self, int):
        if 0 < int <= 7: return self.scaleList[int - 1]
        else: raise("Scale degree is out of bounds: must be between 1 and 7.")

    def getTonic(self):
        return self.tonic

    def getDominant(self):
        interval1to5 = interval.notesToInterval(self.tonic, self.pitchFromScaleDegree(5))
        if interval1to5.specificName != "Perfect":
            print(interval1to5.diatonicType)
            raise ScaleException("This scale has no Dominant (Locrian perhaps?)")
        else:
            return self.pitchFromScaleDegree(5)
    
    def concrete(self):
        pass
    
class ConcreteMajorScale(DiatonicScale, DirectionlessScale):
    '''
    >>> d = Pitch(); d.name = "D"
    >>> dScale = ConcreteMajorScale(d)
    >>> cis = dScale.pitchFromScaleDegree(7)
    >>> cis.name
    'C#'
    '''
    
    type = "major"
    
    def generateScaleList(self):
        n1 = self.tonic
        n2 = interval.transposePitch(n1, "M2")
        n3 = interval.transposePitch(n1, "M3")
        n4 = interval.transposePitch(n1, "P4")
        n5 = interval.transposePitch(n1, "P5")
        n6 = interval.transposePitch(n1, "M6")
        n7 = interval.transposePitch(n1, "M7")
        scaleList = [n1, n2, n3, n4, n5, n6, n7]
        return scaleList

    def getConcreteMajorScale(self):
        scale = self.scaleList[:]
        scale.append(interval.transposePitch(self.tonic, "P8"))        
        return scale

    def getAbstractMajorScale(self):
        concrete = self.getConcreteMajorScale()
        abstract = copy.deepcopy(concrete)
        for pitch1 in abstract:
            pitch1.octave = 0 #octave 0 means "octaveless"
        return abstract

    def getRelativeMinor(self):
        return ConcreteMinorScale(self.pitchFromScaleDegree(6))

    def getParallelMinor(self):
        return ConcreteMinorScale(self.tonic)

class ConcreteMinorScale(DiatonicScale, DirectionlessScale):
    type = "minor"

    def generateScaleList(self):
        n1 = self.tonic
        n2 = interval.transposePitch(n1, "M2")
        n3 = interval.transposePitch(n1, "m3")
        n4 = interval.transposePitch(n1, "P4")
        n5 = interval.transposePitch(n1, "P5")
        n6 = interval.transposePitch(n1, "m6")
        n7 = interval.transposePitch(n1, "m7")
        return [n1, n2, n3, n4, n5, n6, n7]

    def getConcreteHarmonicMinorScale(self):
        scale = self.scaleList[:]
        scale[6] = self.getLeadingTone()
        scale.append(interval.transposePitch(self.tonic, "P8"))
        return scale

    def getConcreteMelodicMinorScale(self):
        scale = self.getConcreteHarmonicMinorScale()
        scale[5] = interval.transposePitch(self.pitchFromScaleDegree(6), "A1")
        for n in range(0, 7):
            scale.append(self.pitchFromScaleDegree(7-n))
        return scale

    def getAbstractHarmonicMinorScale(self):
        concrete = self.getConcreteHarmonicMinorScale()
        abstract = copy.deepcopy(concrete)
        for pitch1 in abstract:
            pitch1.octave = 0 #octave 0 means "octaveless"
        return abstract

    def getAbstractMelodicMinorScale(self):
        concrete = self.getConcreteMelodicMinorScale()
        abstract = copy.deepcopy(concrete)
        for pitch1 in abstract:
            pitch1.octave = 0 #octave 0 means "octaveless"
        return abstract

    def pitchFromScaleDegree(self, degree):        
        if 0 < degree <= 7: return self.scaleList[degree - 1]
        else: raise("Scale degree is out of bounds: must be between 1 and 7.")

    def getTonic(self):
        return self.tonic

    def getDominant(self):
        return self.pitchFromScaleDegree(5)

    def getLeadingTone(self):
        return interval.transposePitch(self.pitchFromScaleDegree(7), "A1")

    def getRelativeMajor(self):
        return ConcreteMajorScale(self.pitchFromScaleDegree(3))

    def getParallelMajor(self):
        return ConcreteMajorScale(self.tonic)

class ScaleException(Exception):
    pass

class ScaleDegree(object):
    pass

class Test(unittest.TestCase):
    
    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)