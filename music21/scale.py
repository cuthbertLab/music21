#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         scale.py
# Purpose:      music21 classes for representing scales
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Objects for defining scales. 
'''

import copy
import unittest, doctest

import music21
from music21 import pitch
from music21 import interval
from music21 import intervalNetwork



#-------------------------------------------------------------------------------
class ScaleException(Exception):
    pass

class Scale(music21.Music21Object):
    '''
    Generic base class for all scales.
    '''
    def __init__(self):
        self.directionSensitive = False # can be true or false
        self.type = None # could be mode, could be other indicator

    def _getName(self):
        '''Return or construct the name of this scale
        '''
        return 'Scale'
        
    name = property(_getName, 
        doc = '''Return or construct the name of this scale.

        ''')

# instead of classes, these can be attributes on the scale object
# class DirectionlessScale(Scale):
#     '''A DirectionlessScale is the same ascending and descending.
#     For instance, the major scale.  
# 
#     A DirectionSensitiveScale has
#     two different forms.  For instance, the natural-minor scale.
#     
#     One could imagine more complex scales that have different forms
#     depending on what scale degree you've just landed on.  Some
#     Ragas might be expressible in that way.'''
#     
#     def ascending(self):
#         return self.pitchList
#     
#     def descending(self):
#         tempScale = copy(self.pitchList)
#         return tempScale.reverse()
#         ## we perform the reverse on a copy of the pitchList so that
#         ## in case we are multithreaded later in life, we do not have
#         ## a race condition where someone might get self.pitchList as
#         ## reversed
# 
# class DirectionSensitiveScale(Scale):
#     pass


#-------------------------------------------------------------------------------
class DiatonicScale(Scale):
    def __init__(self, tonic = pitch.Pitch()):

        Scale.__init__(self)

        # if this class is an abstract scale type, it may not make sense
        # to store the tonic, as the tonic is part of the process of 
        # concretization

        self.type = 'Diatonic'

        # as this is still an abstract scale, storing a pitch list
        # and a tonic does not seem necessary
        # instead, a tonic and dominant scale step might be stored (and 
        # customized in modal subclasses)
        self.tonic = tonic
        self.pitchList = self._generatePitchList()


    def _getName(self):
        '''Return or construct the name of this scale
        '''
        return " ".join([self.tonic.name, self.type]) 

    name = property(_getName, 
        doc = '''Return or construct the name of this scale.

        >>> from music21 import *
        >>> sc = scale.DiatonicScale()
        >>> sc.name
        'C Diatonic'
        ''')

    def _generatePitchList(self):
        '''Return a list of Pitch objects. 
        '''
        return []
        #raise ScaleException("Cannot generate a scale from a DiatonicScale class")


    def ascending(self):
        '''Return ascending scale form.
        '''
        return self.pitchList
    
    def descending(self):
        '''Return descending scale form.
        '''
        tempScale = copy(self.pitchList)
        return tempScale.reverse()


    def pitchFromScaleDegree(self, degree):        
        if 0 < degree <= 7: 
            return self.pitchList[degree - 1]
        else: 
            raise("Scale degree is out of bounds: must be between 1 and 7.")



    #---------------------------------------------------------------------------
    # getting scale degrees by common names

    def getTonic(self):
        return self.tonic

    def getDominant(self):
        interval1to5 = interval.notesToInterval(self.tonic, 
                        self.pitchFromScaleDegree(5))
        if interval1to5.specificName != "Perfect":
            raise ScaleException("This scale has no Dominant (Locrian perhaps?): %s" % interval1to5.diatonicType)
        else:
            return self.pitchFromScaleDegree(5)
    

    def getLeadingTone(self):
        '''Return the leading tone. 

        >>> from music21 import *
        >>> sc = scale.ConcreteMinorScale()
        >>> sc.pitchFromScaleDegree(7)
        B-4
        >>> sc.getLeadingTone()
        B4
        '''
        # NOTE: must be adjust for modes that do not have a proper leading tone
        interval1to7 = interval.notesToInterval(self.tonic, 
                        self.pitchFromScaleDegree(7))
        if interval1to7.name != 'M7':
            # if not a major seventh from the tonic, get a pitch a M7 above
            return interval.transposePitch(self.pitchFromScaleDegree(1), "M7")
        else:
            return self.pitchFromScaleDegree(7)


# class ScaleDegree(object):
#     pass
# 



#-------------------------------------------------------------------------------
# a concrete scale might best a different object from a abstact scales
# a concerte scale might contain an instance of its abstract archetype
# then define a tonic and optionally an ambitus
# thus, we would have a MajorScale class as Scale subclass,
# and a ConcreteMajorScale as a Scale subclass
# the concrete version would contain an instance of the abstract scale
# and use this to build, extend, or transform its pitch list
 



class ConcreteMajorScale(DiatonicScale):
    '''
    >>> d = pitch.Pitch(); d.name = "D"
    >>> dScale = ConcreteMajorScale(d)
    >>> cis = dScale.pitchFromScaleDegree(7)
    >>> cis.name
    'C#'
    '''
    
    def __init__(self, tonic = pitch.Pitch()):

        DiatonicScale.__init__(self, tonic=tonic)
        self.type = "major"


    
    def _generatePitchList(self):
        # note: these are not notes, but Pitch objects
        n1 = self.tonic
        n2 = interval.transposePitch(n1, "M2")
        n3 = interval.transposePitch(n1, "M3")
        n4 = interval.transposePitch(n1, "P4")
        n5 = interval.transposePitch(n1, "P5")
        n6 = interval.transposePitch(n1, "M6")
        n7 = interval.transposePitch(n1, "M7")
        pitchList = [n1, n2, n3, n4, n5, n6, n7]
        return pitchList

#     def getConcreteMajorScale(self):
#         scale = self.pitchList[:]
#         scale.append(interval.transposePitch(self.tonic, "P8"))        
#         return scale
# 
#     def getAbstractMajorScale(self):
#         concrete = self.getConcreteMajorScale()
#         abstract = copy.deepcopy(concrete)
#         for pitch1 in abstract:
#             pitch1.octave = 0 #octave 0 means "octaveless"
#         return abstract


    def getRelativeMinor(self):
        return ConcreteMinorScale(self.pitchFromScaleDegree(6))

    def getParallelMinor(self):
        return ConcreteMinorScale(self.tonic)




class ConcreteMinorScale(DiatonicScale):


    def __init__(self, tonic = pitch.Pitch()):
        DiatonicScale.__init__(self, tonic=tonic)
        self.type = "minor"


    def _generatePitchList(self):
        # note: these are not notes, but Pitch objects

        n1 = self.tonic
        n2 = interval.transposePitch(n1, "M2")
        n3 = interval.transposePitch(n1, "m3")
        n4 = interval.transposePitch(n1, "P4")
        n5 = interval.transposePitch(n1, "P5")
        n6 = interval.transposePitch(n1, "m6")
        n7 = interval.transposePitch(n1, "m7")
        return [n1, n2, n3, n4, n5, n6, n7]


# not presently needed
#     def getConcreteHarmonicMinorScale(self):
#         scale = self.pitchList[:]
#         scale[6] = self.getLeadingTone()
#         scale.append(interval.transposePitch(self.tonic, "P8"))
#         return scale
# 
#     def getConcreteMelodicMinorScale(self):
#         scale = self.getConcreteHarmonicMinorScale()
#         scale[5] = interval.transposePitch(self.pitchFromScaleDegree(6), "A1")
#         for n in range(0, 7):
#             scale.append(self.pitchFromScaleDegree(7-n))
#         return scale
# 
#     def getAbstractHarmonicMinorScale(self):
#         concrete = self.getConcreteHarmonicMinorScale()
#         abstract = copy.deepcopy(concrete)
#         for pitch1 in abstract:
#             pitch1.octave = 0 #octave 0 means "octaveless"
#         return abstract
# 
#     def getAbstractMelodicMinorScale(self):
#         concrete = self.getConcreteMelodicMinorScale()
#         abstract = copy.deepcopy(concrete)
#         for pitch1 in abstract:
#             pitch1.octave = 0 #octave 0 means "octaveless"
#         return abstract




    def getRelativeMajor(self):
        return ConcreteMajorScale(self.pitchFromScaleDegree(3))

    def getParallelMajor(self):
        return ConcreteMajorScale(self.tonic)




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass


    def testBasicLegacy(self):
        from music21 import note

        n1 = note.Note()
        
        CMajor = ConcreteMajorScale(n1)
        
        assert CMajor.name == "C major"
        assert CMajor.pitchList[6].step == "B"
        
#         CScale = CMajor.getConcreteMajorScale()
#         assert CScale[7].step == "C"
#         assert CScale[7].octave == 5
#         
#         CScale2 = CMajor.getAbstractMajorScale()
#         
#         for note1 in CScale2:
#             assert note1.octave == 0
#             #assert note1.duration.type == ""
#         assert [note1.name for note1 in CScale] == ["C", "D", "E", "F", "G", "A", "B", "C"]
        
        seventh = CMajor.pitchFromScaleDegree(7)
        assert seventh.step == "B"
        
        dom = CMajor.getDominant()
        assert dom.step == "G"
        
        n2 = note.Note()
        n2.step = "A"
        
        aMinor = CMajor.getRelativeMinor()
        assert aMinor.name == "A minor", "Got a different name: " + aMinor.name
        
        notes = [note1.name for note1 in aMinor.pitchList]
        assert notes == ["A", "B", "C", "D", "E", "F", "G"]
        
        n3 = note.Note()
        n3.name = "B-"
        n3.octave = 5
        
        bFlatMinor = ConcreteMinorScale(n3)
        assert bFlatMinor.name == "B- minor", "Got a different name: " + bFlatMinor.name
        notes2 = [note1.name for note1 in bFlatMinor.pitchList]
        assert notes2 == ["B-", "C", "D-", "E-", "F", "G-", "A-"]
        assert bFlatMinor.pitchList[0] == n3
        assert bFlatMinor.pitchList[6].octave == 6
        
#         harmonic = bFlatMinor.getConcreteHarmonicMinorScale()
#         niceHarmonic = [note1.name for note1 in harmonic]
#         assert niceHarmonic == ["B-", "C", "D-", "E-", "F", "G-", "A", "B-"]
#         
#         harmonic2 = bFlatMinor.getAbstractHarmonicMinorScale()
#         assert [note1.name for note1 in harmonic2] == niceHarmonic
#         for note1 in harmonic2:
#             assert note1.octave == 0
#             #assert note1.duration.type == ""
        
#         melodic = bFlatMinor.getConcreteMelodicMinorScale()
#         niceMelodic = [note1.name for note1 in melodic]
#         assert niceMelodic == ["B-", "C", "D-", "E-", "F", "G", "A", "B-", "A-", "G-", \
#                                "F", "E-", "D-", "C", "B-"]
        
#         melodic2 = bFlatMinor.getAbstractMelodicMinorScale()
#         assert [note1.name for note1 in melodic2] == niceMelodic
#         for note1 in melodic2:
#             assert note1.octave == 0
            #assert note1.duration.type == ""
        
        cNote = bFlatMinor.pitchFromScaleDegree(2)
        assert cNote.name == "C"
        fNote = bFlatMinor.getDominant()
        assert fNote.name == "F"
        
        bFlatMajor = bFlatMinor.getParallelMajor()
        assert bFlatMajor.name == "B- major"
#         scale = [note1.name for note1 in bFlatMajor.getConcreteMajorScale()]
#         assert scale == ["B-", "C", "D", "E-", "F", "G", "A", "B-"]
        
        dFlatMajor = bFlatMinor.getRelativeMajor()
        assert dFlatMajor.name == "D- major"
        assert dFlatMajor.getTonic().name == "D-"
        assert dFlatMajor.getDominant().name == "A-"



#-------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()



#------------------------------------------------------------------------------
# eof

