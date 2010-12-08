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
import re

import music21
from music21 import common
from music21 import pitch
from music21 import interval
from music21 import intervalNetwork

from music21.musicxml import translate as musicxmlTranslate

from music21 import environment
_MOD = "scale.py"
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class ScaleException(Exception):
    pass

class Scale(music21.Music21Object):
    '''
    Generic base class for all scales.
    '''
    def __init__(self):
        self.directionSensitive = False # can be true or false
        self.type = 'Scale' # could be mode, could be other indicator


    def _getName(self):
        '''Return or construct the name of this scale
        '''
        return self.type
        
    name = property(_getName, 
        doc = '''Return or construct the name of this scale.

        ''')

    def _isConcrete(self):
        '''To be concrete, a Scale must have a defined tonic. An abstract Scale is not Concrete
        '''
        return False

    isConcrete = property(_isConcrete, 
        doc = '''Return True if the scale is Concrete, that is, it has a defined Tonic. 
        ''')


    def _extractPitchList(self, other, comparisonAttribute='nameWithOctave'):
        '''Given a data format, extract all unique pitch space or pitch class values.
        '''
        pre = []
        # if a ConcreteScale, Chord or Stream
        if hasattr(other, 'pitches'):
            pre = other.pitches
        # if a list
        elif common.isListLike(other):
            # assume a list of pitches; possible permit conversions?
            pre = other
        elif hasatter(other, 'pitch'):
            pre = [other.pitch] # get pitch attribute
        return pre




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
#         return self.pitches
#     
#     def descending(self):
#         tempScale = copy(self.pitches)
#         return tempScale.reverse()
#         ## we perform the reverse on a copy of the pitchList so that
#         ## in case we are multithreaded later in life, we do not have
#         ## a race condition where someone might get self.pitches as
#         ## reversed
# 
# class DirectionSensitiveScale(Scale):
#     pass


#-------------------------------------------------------------------------------
class AbstractScale(Scale):
    '''An abstract scale is specific scale formation, but does not have a defined pitch collection or pitch reference. For example, all Major scales can be represented by an AbstractScale; a ConcreteScale, however, is a specific Major Scale, such as G Major. 

    These classes primarily create and manipulate the stored IntervalNetwork object. Thus, they are rarely created or manipulated directly by most users.
    '''
    def __init__(self):
        Scale.__init__(self)
        # store interval network within abstract scale
        self.net = None
        # in most cases tonic/final of scale is step one, but not always
        self.tonicStep = 1 # step of tonic


    def __eq__(self, other):
        '''
        >>> from music21 import *
        >>> as1 = scale.AbstractScale()
        >>> as2 = scale.AbstractScale()
        >>> as1 == as2
        True
        >>> as1 == None
        False
        >>> as1.isConcrete
        False
        '''
        # have to test each so as not to confuse with a subclass
        if (isinstance(other, self.__class__) and 
            isinstance(self, other.__class__) and 
            self.tonicStep == other.tonicStep and
            self.net == other.net
            ):
            return True     
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)




    def getStepMaxUnique(self):
        '''Return the maximum number of scale steps, or the number to use as a 
        modulus. 
        '''
        # access from property
        return self.net.stepMaxUnique

    def reverse(self):
        '''Reverse all intervals in this scale.
        '''
        pass

    def getRealization(self, pitchObj, stepOfPitch, 
                        minPitch=None, maxPitch=None):
        '''Realize the abstract scale as a list of pitch objects, given a pitch object, the step of that pitch object, and a min and max pitch.
        '''
        if self.net is None:
            raise ScaleException('no netowrk is defined.')

        return self.net.realizePitch(pitchObj, stepOfPitch, minPitch=minPitch, maxPitch=maxPitch)



class AbstractOctatonicScale(AbstractScale):

    def __init__(self, mode=None):
        AbstractScale.__init__(self)
        self.type = 'Abstract Octatonic'

        # here, accept None
        self.buildNetwork(mode=mode)

    def buildNetwork(self, mode=None):
        '''
        Given sub-class dependent parameters, build and assign the IntervalNetwork.

        >>> from music21 import *
        >>> sc = scale.AbstractDiatonicScale()
        >>> sc.buildNetwork('lydian')
        >>> sc.getRealization('f4', 1, 'f2', 'f6') 
        [F2, G2, A2, B2, C3, D3, E3, F3, G3, A3, B3, C4, D4, E4, F4, G4, A4, B4, C5, D5, E5, F5, G5, A5, B5, C6, D6, E6, F6]

        '''
        srcList = ['M2', 'm2', 'M2', 'm2', 'M2', 'm2', 'M2', 'm2']
        if mode in [None, 1, 'M2']:
            intervalList = srcList # start with M2
            self.tonicStep = 1
        elif mode in [2, 'm2']:
            intervalList = srcList[1:] + srcList[:1] # start with m2
            self.tonicStep = 1
        else:
            raise ScaleException('cannot create a scale of the following mode:' % mode)
        self.net = intervalNetwork.IntervalNetwork(intervalList)
        # might also set weights for tonic and dominant here






class AbstractDiatonicScale(AbstractScale):

    def __init__(self, mode=None):
        AbstractScale.__init__(self)
        self.type = 'Abstract Diatonic'
        self.tonicStep = None # step of tonic
        self.dominantStep = None # step of dominant

        if mode is not None:
            self.buildNetwork(mode=mode)

    def __eq__(self, other):
        '''
        >>> from music21 import *
        >>> as1 = scale.AbstractDiatonicScale('major')
        >>> as2 = scale.AbstractDiatonicScale('lydian')
        >>> as3 = scale.AbstractDiatonicScale('ionian')
        >>> as1 == as2
        False
        >>> as1 == as3
        True
        '''
        # have to test each so as not to confuse with a subclass
        if (isinstance(other, self.__class__) and 
            isinstance(self, other.__class__) and 
            self.type == other.type and
            self.tonicStep == other.tonicStep and
            self.dominantStep == other.dominantStep and
            self.net == other.net
            ):
            return True     
        else:
            return False

    def buildNetwork(self, mode=None):
        '''
        Given sub-class dependent parameters, build and assign the IntervalNetwork.

        >>> from music21 import *
        >>> sc = scale.AbstractDiatonicScale()
        >>> sc.buildNetwork('lydian')
        >>> sc.getRealization('f4', 1, 'f2', 'f6') 
        [F2, G2, A2, B2, C3, D3, E3, F3, G3, A3, B3, C4, D4, E4, F4, G4, A4, B4, C5, D5, E5, F5, G5, A5, B5, C6, D6, E6, F6]

        '''

        # nice reference here:
        # http://cnx.org/content/m11633/latest/
        # most diatonic scales will start with this collection
        srcList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']

        if mode in ['dorian']:
            intervalList = srcList[1:] + srcList[:1] # d to d
            self.tonicStep = 1
            self.dominantStep = 5

        elif mode in ['phrygian']:
            intervalList = srcList[2:] + srcList[:2] # e to e
            self.tonicStep = 1
            self.dominantStep = 5

        elif mode in ['lydian']:
            intervalList = srcList[3:] + srcList[:3] # f to f
            self.tonicStep = 1
            self.dominantStep = 5

        elif mode in ['mixolydian']:
            intervalList = srcList[4:] + srcList[:4] # g to g
            self.tonicStep = 1
            self.dominantStep = 5

        elif mode in ['hypodorian']:
            intervalList = srcList[5:] + srcList[:5] # a to a
            self.tonicStep = 4
            self.dominantStep = 6

        elif mode in ['hypophrygian']:
            intervalList = srcList[6:] + srcList[:6] # b to b
            self.tonicStep = 4
            self.dominantStep = 7

        elif mode in ['hypolydian']: # c to c
            intervalList = srcList
            self.tonicStep = 4
            self.dominantStep = 6

        elif mode in ['hypomixolydian']:
            intervalList = srcList[1:] + srcList[:1] # d to d
            self.tonicStep = 4
            self.dominantStep = 7

        elif mode in ['aeolian', 'minor']:
            intervalList = srcList[5:] + srcList[:5] # a to A
            self.tonicStep = 1
            self.dominantStep = 5

        elif mode in [None, 'major', 'ionian']: # c to C
            intervalList = srcList
            self.tonicStep = 1
            self.dominantStep = 5

        elif mode in ['locrian']:
            intervalList = srcList[6:] + srcList[:6] # b to B
            self.tonicStep = 1
            self.dominantStep = 5

        elif mode in ['hypoaeolian']:
            intervalList = srcList[2:] + srcList[:2] # e to e
            self.tonicStep = 4
            self.dominantStep = 6

        elif mode in ['hupomixolydian']:
            intervalList = srcList[3:] + srcList[:3] # f to f
            self.tonicStep = 4
            self.dominantStep = 7

        else:
            raise ScaleException('cannot create a scale of the following mode:' % mode)

        self.net = intervalNetwork.IntervalNetwork(intervalList)
        # might also set weights for tonic and dominant here










#-------------------------------------------------------------------------------
class ConcreteScale(Scale):
    '''A concrete scale is specific scale formation with a defined pitch collection (a `tonic` Pitch) that may or may not be bound by specific range. For example, a specific Major Scale, such as G Major, from G2 to G4.

    This class is not generally used directly but is used as a base class for all concrete scales.
    '''

    isConcrete = True

    def __init__(self, tonic=None):
        Scale.__init__(self)

        self.type = 'Concrete'

        # store an instance of an abstract scale
        # subclasses might use multiple abstract scales?
        self._abstract = None

        # determine wether this is a limited range
        self.boundRange = False

        # here, tonic is a pitch
        # the abstract scale defines what step the tonic is expected to be 
        # found on
        # no default tonic is defined; as such, it is mostly an abstract scale
        if tonic is None:
            self._tonic = None #pitch.Pitch()
        elif common.isStr(tonic):
            self._tonic = pitch.Pitch(tonic)
        elif hasattr(tonic, 'classes') and 'GeneralNote' in tonic.classes:
            self._tonic = tonic.pitch
        else: # assume this is a pitch object
            self._tonic = tonic

    def _isConcrete(self):
        '''To be concrete, a Scale must have a defined tonic. An abstract Scale is not Concrete
        '''
        if self._tonic is None:
            return True
        else:
            return False

    isConcrete = property(_isConcrete, 
        doc = '''Return True if the scale is Concrete, that is, it has a defined Tonic. 

        >>> from music21 import *
        >>> sc1 = scale.MajorScale('c')
        >>> sc1.isConcrete
        True
        >>> sc2 = scale.MajorScale()    
        >>> sc2.isConcrete
        False

        ''')


    def __eq__(self, other):
        '''For concrete equality, the stored abstract objects must evaluate as equal, as well as local attributes. 

        >>> from music21 import *
        >>> sc1 = scale.MajorScale('c')
        >>> sc2 = scale.MajorScale('c')
        >>> sc3 = scale.MinorScale('c')
        >>> sc4 = scale.MajorScale('g')
        >>> sc5 = scale.MajorScale() # an abstract scale, as no tonic defined

        >>> sc1 == sc2
        True
        >>> sc1 == sc3
        False
        >>> sc1 == sc4
        False
        >>> sc1.abstract == sc4.abstract # can compare abstract forms
        True
        >>> sc4 == sc5 # implicit abstract comparisoin
        True
        >>> sc5 == sc2 # implicit abstract comparisoin
        True
        >>> sc5 == sc3 # implicit abstract comparisoin
        False

        '''
        # have to test each so as not to confuse with a subclass
        # TODO: add pitch range comparison if defined

        if not self.isConcrete or not other.isConcrete:
            # if tonic is none, then we automatically do an abstract comparison
            return self._abstract == other._abstract
        
        else:
            if (isinstance(other, self.__class__) and 
                isinstance(self, other.__class__) and 
                self._abstract == other._abstract and
                self.boundRange == other.boundRange and
                self._tonic == other._tonic 
                ):
                return True     
            else:
                return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def _getName(self):
        '''Return or construct the name of this scale
        '''
        if self._tonic is None:
            return " ".join(['Abstract', self.type]) 
        else:
            return " ".join([self._tonic.name, self.type]) 

    name = property(_getName, 
        doc = '''Return or construct the name of this scale.

        >>> from music21 import *
        >>> sc = scale.DiatonicScale() # abstract, as no defined tonic
        >>> sc.name
        'Abstract Diatonic'
        ''')

    def __repr__(self):
        return '<music21.scale.%s %s %s>' % (self.__class__.__name__, self._tonic.name, self.type)

    def _getMusicXML(self):
        '''Return a complete musicxml representation as an xml string. This must call _getMX to get basic mxNote objects

        >>> from music21 import *
        '''
        from music21 import stream, note
        m = stream.Measure()
        for i in range(1, self._abstract.getStepMaxUnique()+1):
            p = self.pitchFromScaleDegree(i)
            n = note.Note()
            n.pitch = p
            if i == 1:
                n.addLyric(self.name)
            if p.name == self.getTonic().name:
                n.quarterLength = 4 # set longer
            else:
                n.quarterLength = 1
            m.append(n)
        m.timeSignature = m.bestTimeSignature()
        return musicxmlTranslate.measureToMusicXML(m)

    musicxml = property(_getMusicXML, 
        doc = '''Return a complete musicxml representation.
        ''')    


    #---------------------------------------------------------------------------
    def getTonic(self):
        '''Return the tonic. 

        This method may be overridden by subclasses that have alternative definitions of tonic. 

        >>> from music21 import *
        >>> sc = scale.ConcreteScale('e-')
        >>> sc.getTonic()
        E-
        '''
        return self._tonic


    def _getAbstract(self):
        '''Return the underlying abstract scale
        '''
        # copy before returning?
        return self._abstract

    abstract = property(_getAbstract, 
        doc='''Return the AbstractScale instance governing this ConcreteScale.

        >>> from music21 import *
        >>> sc1 = scale.MajorScale('d')
        >>> sc2 = scale.MajorScale('b-')
        >>> sc1 == sc2
        False
        >>> sc1.abstract == sc2.abstract
        True
        ''')

    def transpose(self, value, inPlace=False):
        '''Transpose this Scale by the given interval

        >>> from music21 import *
        >>> sc1 = scale.MajorScale('c')
        >>> sc2 = sc1.transpose('p5')
        >>> sc2
        <music21.scale.MajorScale G major>
        >>> sc3 = sc2.transpose('p5')
        >>> sc3
        <music21.scale.MajorScale D major>
        '''
        # note: it does not makes sense to transpose an abstract scale;
        # thus, only concrete scales can be transposed. 
        if inPlace:
            post = self
        else:
            post = copy.deepcopy(self)
        if self._tonic is None:
            # could raise an error; just assume a 'c'
            post._tonic = pitch.Pitch('C4')
            post._tonic.transpose(value, inPlace=True)        
        else:
            post._tonic.transpose(value, inPlace=True)        
        # may need to clear cache here
        return post


    def getPitches(self, minPitch=None, maxPitch=None, direction=None):
        '''Return a list of Pitch objects, using a deepcopy of a cached version if available. 

        '''
        # get from interval network of abstract scale

        if self._abstract is not None:
            # TODO: get and store in cache; return a copy
            # or generate from network stored in abstract
            if self._tonic is None:
                # note: could raise an error here, but instead will
                # use a pseudo-tonic
                pitchObj = pitch.Pitch('C4')
            else:
                pitchObj = self._tonic
            stepOfPitch = self._abstract.tonicStep

            # this creates new pitches on each call
            return self._abstract.getRealization(pitchObj, 
                        stepOfPitch, 
                        minPitch=minPitch, maxPitch=maxPitch)
            #return self._abstract.net.realizePitch(self._tonic, 1)
        else:
            return []
        #raise ScaleException("Cannot generate a scale from a DiatonicScale class")

    pitches = property(getPitches, 
        doc ='''Get a default pitch list from this scale.
        ''')

    def pitchFromScaleDegree(self, degree, minPitch=None, maxPitch=None, 
        direction=None):        

        '''Given a scale degree, return the appropriate pitch. 

        >>> from music21 import *
        >>> sc = scale.MajorScale('e-')
        >>> sc.pitchFromScaleDegree(2)
        F4
        >>> sc.pitchFromScaleDegree(7)
        D5
        '''
        # TODO: rely here on intervalNetwork for caching
        post = self._abstract.net.getPitchFromNodeStep(
            pitchReference=self._tonic, # pitch defined here
            nodeName=self._abstract.tonicStep, # defined in abstract class
            nodeStepTarget=degree, # target looking for
            direction=direction, 
            minPitch=minPitch, 
            maxPitch=maxPitch)
        return post

#         if 0 < degree <= self._abstract.getStepMaxUnique(): 
#             return self.getPitches()[degree - 1]
#         else: 
#             raise("Scale degree is out of bounds: must be between 1 and %s." % self._abstract.getStepMaxUnique())


    def pitchesFromScaleDegrees(self, degreeTargets, minPitch=None, 
        maxPitch=None, direction=None):        

        '''Given one or more scale degrees, return a list of all matches over the entire range. 

        >>> from music21 import *
        >>> sc = scale.MajorScale('e-')
        >>> sc.pitchesFromScaleDegrees([3,7])
        [G4, D5]
        >>> sc.pitchesFromScaleDegrees([3,7], 'c2', 'c6')
        [D2, G2, D3, G3, D4, G4, D5, G5]
        '''
        # TODO: rely here on intervalNetwork for caching
        post = self._abstract.net.realizePitchByStep(
            pitchObj=self._tonic, # pitch defined here
            nodeId=self._abstract.tonicStep, # defined in abstract class
            nodeStepTargets=degreeTargets, # target looking for
            direction=direction, 
            minPitch=minPitch, 
            maxPitch=maxPitch)
        return post


    def getScaleDegreeFromPitch(self, pitchTarget, direction=None, 
            comparisonAttribute='pitchClass'):
        '''For a given pitch, return the appropriate scale degree. If no scale degree is available, None is returned.

        >>> from music21 import *
        >>> sc = scale.MajorScale('e-')
        >>> sc.getScaleDegreeFromPitch('e-2')
        1
        >>> sc.getScaleDegreeFromPitch('d')
        7
        >>> sc.getScaleDegreeFromPitch('d#', comparisonAttribute='name') == None
        True
        >>> sc.getScaleDegreeFromPitch('d#', comparisonAttribute='pitchClass')
        1
        '''

        post = self._abstract.net.getRelativeNodeStep(
            pitchReference=self._tonic, 
            nodeName=self._abstract.tonicStep, 
            pitchTarget=pitchTarget,      
            comparisonAttribute=comparisonAttribute)
        return post


    def next(self, pitchOrigin, direction='ascending', stepSize=1):
        '''Get the next pitch.

        The `direction` attribute must be either ascending or descending.

        >>> from music21 import *
        >>> sc = scale.MajorScale('e-')
        >>> sc.next('e-5')
        F5
        >>> sc.next('e-5', stepSize=2)
        G5
        >>> sc.next('e-6', stepSize=3)
        A-6
        '''
        post = self._abstract.net.nextPitch(
            pitchReference=self._tonic, 
            nodeName=self._abstract.tonicStep, 
            pitchOrigin=pitchOrigin,      
            direction=direction,
            stepSize = stepSize
            )
        return post


#     def ascending(self):
#         '''Return ascending scale form.
#         '''
#         # get from pitch cache
#         return self.getPitches()
#     
#     def descending(self):
#         '''Return descending scale form.
#         '''
#         # get from pitch cache
#         tempScale = copy(self.getPitches())
#         tempScale.reverse()
#         return tempScale



    #---------------------------------------------------------------------------
    # comparison and evaluation

    def match(self, other, comparisonAttribute='pitchClass'):
        '''Given another object of various forms (e.g., a Stream, a ConcreteScale, a list of pitches), return a named dictionary of pitch lists with keys 'matched' and 'notMatched'.

        >>> from music21 import *
        >>> sc1 = scale.MajorScale('g')
        >>> sc2 = scale.MajorScale('d')
        >>> sc3 = scale.MajorScale('a')
        >>> sc4 = scale.MajorScale('e')
        >>> sc1.match(sc2)
        {'notMatched': [C#5], 'matched': [D, E4, F#4, G4, A4, B4, D5]}
        >>> sc2.match(sc3)
        {'notMatched': [G#5], 'matched': [A, B4, C#5, D5, E5, F#5, A5]}

        >>> sc1.match(sc4)
        {'notMatched': [G#4, C#5, D#5], 'matched': [E, F#4, A4, B4, E5]}

        '''

        # strip out unique pitches in a list
        # to do a pitch spa

        otherPitches = self._extractPitchList(other,
                        comparisonAttribute=comparisonAttribute)

        # need to deal with direction here? or get an aggregate scale
        matched, notMatched = self._abstract.net.match(
            pitchReference=self._tonic, 
            nodeId=self._abstract.tonicStep, 
            pitchTarget=otherPitches, # can supply a list here
            comparisonAttribute=comparisonAttribute)

        post = {}
        post['matched'] = matched
        post['notMatched'] = notMatched
        return post





    def deriveRanked(self, other, resultsReturned=4,
         comparisonAttribute='pitchClass'):
        '''Return a list of closest matching concrete scales given a collection of pitches, provided as a Stream, a ConcreteScale, a list of pitches)

        >>> from music21 import *
        >>> sc1 = scale.MajorScale('g')
        >>> sc1.deriveRanked(['c', 'e', 'b'])
        [(3, <music21.scale.MajorScale G major>), (3, <music21.scale.MajorScale C major>), (2, <music21.scale.MajorScale B major>), (2, <music21.scale.MajorScale A major>)]
        >>> sc1.deriveRanked(['c#', 'e', 'g#'])
        [(3, <music21.scale.MajorScale B major>), (3, <music21.scale.MajorScale A major>), (3, <music21.scale.MajorScale E major>), (3, <music21.scale.MajorScale C- major>)]

        '''
        # possibly return dictionary with named parameters
        # default return all scales that match all provided pitches
        # instead of results returned, define how many matched pitches necessary
        otherPitches = self._extractPitchList(other,
                        comparisonAttribute=comparisonAttribute)

        pairs = self._abstract.net.find(pitchTarget=otherPitches,
                             resultsReturned=resultsReturned,
                             comparisonAttribute=comparisonAttribute)

        post = []
        for weight, p in pairs:
            sc = self.__class__(tonic=p)
            post.append((weight, sc))
        return post

    def derive(self, other, comparisonAttribute='pitchClass'):
        '''
        >>> from music21 import *
        >>> sc1 = scale.MajorScale('g')
        >>> sc1.derive(['c#', 'e', 'g#'])
        <music21.scale.MajorScale B major>
        >>> sc1.derive(['e-', 'b-', 'd'], comparisonAttribute='name')
        <music21.scale.MajorScale B- major>
        '''
        otherPitches = self._extractPitchList(other,
                        comparisonAttribute=comparisonAttribute)

        # weight target membership
        pairs = self._abstract.net.find(pitchTarget=otherPitches,
                            comparisonAttribute=comparisonAttribute)

        return self.__class__(tonic=pairs[0][1])


    #---------------------------------------------------------------------------
    def _getMusicXML(self):
        '''Return a complete musicxml representation as an xml string.

        >>> from music21 import *
        '''
        from music21 import stream, note
        m = stream.Measure()
        for i in range(1, self._abstract.getStepMaxUnique()+1):
            p = self.pitchFromScaleDegree(i)
            n = note.Note()
            n.pitch = p
            if i == 1:
                n.addLyric(self.name)

            if p.name == self.getTonic().name:
                n.quarterLength = 4 # set longer
            else:
                n.quarterLength = 1
            m.append(n)
        m.timeSignature = m.bestTimeSignature()
        return musicxmlTranslate.measureToMusicXML(m)

    musicxml = property(_getMusicXML, 
        doc = '''Return a complete musicxml representation.
        ''')    





#-------------------------------------------------------------------------------
class DiatonicScale(ConcreteScale):
    '''A concrete diatonic scale. Assumes that all such scales have 
    '''

    def __init__(self, tonic=None):
        ConcreteScale.__init__(self, tonic=tonic)
        self._abstract = AbstractDiatonicScale()
        self.type = 'Diatonic'

    def getTonic(self):
        '''Return the dominant. 

        >>> from music21 import *
        >>> sc = scale.MajorScale('e-')
        >>> sc.getDominant()
        B-4
        >>> sc = scale.MajorScale('F#')
        >>> sc.getDominant()
        C#5
        '''
        # NOTE: override method on ConcreteScale that simply returns _tonic
        return self.pitchFromScaleDegree(self._abstract.tonicStep)

    def getDominant(self):
        '''Return the dominant. 

        >>> from music21 import *
        >>> sc = scale.MajorScale('e-')
        >>> sc.getDominant()
        B-4
        >>> sc = scale.MajorScale('F#')
        >>> sc.getDominant()
        C#5
        '''
        return self.pitchFromScaleDegree(self._abstract.dominantStep)
    

    def getLeadingTone(self):
        '''Return the leading tone. 

        >>> from music21 import *
        >>> sc = scale.MinorScale('c')
        >>> sc.pitchFromScaleDegree(7)
        B-4
        >>> sc.getLeadingTone()
        B4
        >>> sc.getDominant()
        G4

        '''
        # NOTE: must be adjust for modes that do not have a proper leading tone
        interval1to7 = interval.notesToInterval(self._tonic, 
                        self.pitchFromScaleDegree(7))
        if interval1to7.name != 'M7':
            # if not a major seventh from the tonic, get a pitch a M7 above
            return interval.transposePitch(self.pitchFromScaleDegree(1), "M7")
        else:
            return self.pitchFromScaleDegree(7)


    def _getMusicXML(self):
        '''Return a complete musicxml representation as an xml string. This must call _getMX to get basic mxNote objects

        >>> from music21 import *
        '''
        # note: overidding behavior on 
        from music21 import stream, note
        m = stream.Measure()
        for i in range(1, self._abstract.getStepMaxUnique()+1):
            p = self.pitchFromScaleDegree(i)
            n = note.Note()
            n.pitch = p
            if i == 1:
                n.addLyric(self.name)

            if p.name == self.getTonic().name:
                n.quarterLength = 4 # set longer
            elif p.name == self.getDominant().name:
                n.quarterLength = 2 # set longer
            else:
                n.quarterLength = 1
            m.append(n)
        m.timeSignature = m.bestTimeSignature()
        return musicxmlTranslate.measureToMusicXML(m)

    musicxml = property(_getMusicXML, 
        doc = '''Return a complete musicxml representation.
        ''')    


class OctatonicScale(ConcreteScale):
    '''A concrete diatonic scale. Assumes that all such scales have 
    '''

    def __init__(self, tonic=None, mode=None):
        ConcreteScale.__init__(self, tonic=tonic)
        self._abstract = AbstractOctatonicScale(mode=mode)
        self.type = 'Octatonic'











#-------------------------------------------------------------------------------
class MajorScale(DiatonicScale):
    '''A Major Scale

    >>> sc = MajorScale(pitch.Pitch('d'))
    >>> sc.pitchFromScaleDegree(7).name
    'C#'
    '''
    
    def __init__(self, tonic=None):

        DiatonicScale.__init__(self, tonic=tonic)
        self.type = "major"
        # build the network for the appropriate scale
        self._abstract.buildNetwork(self.type)


    def getRelativeMinor(self):
        '''Return a relative minor scale based on this concrete major scale.

        >>> sc1 = MajorScale(pitch.Pitch('a'))
        >>> sc1.pitches
        [A, B4, C#5, D5, E5, F#5, G#5, A5]
        >>> sc2 = sc1.getRelativeMinor()
        >>> sc2.pitches
        [F#5, G#5, A5, B5, C#6, D6, E6, F#6]
        '''
        return MinorScale(self.pitchFromScaleDegree(6))

    def getParallelMinor(self):
        '''Return a parallel minor scale based on this concrete major scale.

        >>> sc1 = MajorScale(pitch.Pitch('a'))
        >>> sc1.pitches
        [A, B4, C#5, D5, E5, F#5, G#5, A5]
        >>> sc2 = sc1.getParallelMinor()
        >>> sc2.pitches
        [A, B4, C5, D5, E5, F5, G5, A5]
        '''
        return MinorScale(self._tonic)




class MinorScale(DiatonicScale):
    '''A natural minor scale, or the Aeolian mode.

    >>> sc = MinorScale(pitch.Pitch('g'))
    >>> sc.pitches
    [G, A4, B-4, C5, D5, E-5, F5, G5]
    '''
    def __init__(self, tonic=None):
        DiatonicScale.__init__(self, tonic=tonic)
        self.type = "minor"
        self._abstract.buildNetwork(self.type)

    def getRelativeMajor(self):
        '''Return a concrete relative major scale

        >>> sc1 = MinorScale(pitch.Pitch('g'))
        >>> sc1.pitches
        [G, A4, B-4, C5, D5, E-5, F5, G5]
        >>> sc2 = sc1.getRelativeMajor()
        >>> sc2.pitches
        [B-4, C5, D5, E-5, F5, G5, A5, B-5]
        '''
        return MajorScale(self.pitchFromScaleDegree(3))

    def getParallelMajor(self):
        '''Return a concrete relative major scale

        >>> sc1 = MinorScale(pitch.Pitch('g'))
        >>> sc1.pitches
        [G, A4, B-4, C5, D5, E-5, F5, G5]
        >>> sc2 = sc1.getParallelMajor()
        >>> sc2.pitches
        [G, A4, B4, C5, D5, E5, F#5, G5]
        '''
        return MajorScale(self._tonic)



class DorianScale(DiatonicScale):
    '''A natural minor scale, or the Aeolian mode.

    >>> sc = DorianScale(pitch.Pitch('d'))
    >>> sc.pitches
    [D, E4, F4, G4, A4, B4, C5, D5]
    '''
    def __init__(self, tonic=None):
        DiatonicScale.__init__(self, tonic=tonic)
        self.type = "dorian"
        self._abstract.buildNetwork(self.type)


class PhrygianScale(DiatonicScale):
    '''A phrygian scale

    >>> sc = PhrygianScale(pitch.Pitch('e'))
    >>> sc.pitches
    [E, F4, G4, A4, B4, C5, D5, E5]
    '''
    def __init__(self, tonic=None):
        DiatonicScale.__init__(self, tonic=tonic)
        self.type = "phrygian"
        self._abstract.buildNetwork(self.type)



class HypophrygianScale(DiatonicScale):
    '''A hypophrygian scale

    >>> sc = HypophrygianScale(pitch.Pitch('e'))
    >>> sc.pitches
    [B3, C4, D4, E, F4, G4, A4, B4]
    >>> sc.getTonic()
    E
    >>> sc.getDominant()
    A4
    >>> sc.pitchFromScaleDegree(1) # scale degree 1 is treated as lowest
    B3
    '''
    def __init__(self, tonic=None):
        DiatonicScale.__init__(self, tonic=tonic)
        self.type = "hypophrygian"
        self._abstract.buildNetwork(self.type)



#     def getConcreteHarmonicMinorScale(self):
#         scale = self.pitches[:]
#         scale[6] = self.getLeadingTone()
#         scale.append(interval.transposePitch(self._tonic, "P8"))
#         return scale

#     def getAbstractHarmonicMinorScale(self):
#         concrete = self.getConcreteHarmonicMinorScale()
#         abstract = copy.deepcopy(concrete)
#         for pitch1 in abstract:
#             pitch1.octave = 0 #octave 0 means "octaveless"
#         return abstract
# 

# melodic minor will be implemented in a different way
#     def getConcreteMelodicMinorScale(self):
#         scale = self.getConcreteHarmonicMinorScale()
#         scale[5] = interval.transposePitch(self.pitchFromScaleDegree(6), "A1")
#         for n in range(0, 7):
#             scale.append(self.pitchFromScaleDegree(7-n))
#         return scale
# 
#     def getAbstractMelodicMinorScale(self):
#         concrete = self.getConcreteMelodicMinorScale()
#         abstract = copy.deepcopy(concrete)
#         for pitch1 in abstract:
#             pitch1.octave = 0 #octave 0 means "octaveless"
#         return abstract







#-------------------------------------------------------------------------------
class RomanNumeral(object):
    '''An abstract harmony built from scale degree selections.

    A RomanNumeral is type of concrete scale where the root is the tonic and the bass is defined by step. 
    '''
    # a harmony might be seen as a subclass of a concrete scale, but this 
    # is not always the case.
    # more often, a harmony is collection of scale steps
    def __init__(self, scale=None, rootScaleStep=1):

        # store a 'live' reference to the scale that this harmony is active one
        self.scale = scale
        self.rootScaleStep = rootScaleStep

        # store a mapping of scale steps from root
        self._members = [0]

        # store as index within members
        self._bassMemberIndex = 0

        # store mapping of alterations to members
        self._alterations = {}

        # default is to make a triad; could be otherwise
        self.makeTriad()


    def _getRoot(self):
        return self.scale.pitchFromScaleDegree(self.rootScaleStep)

    root = property(_getRoot, 
        doc = '''Return the root of this harmony. 

        >>> from music21 import *
        >>> sc1 = scale.MajorScale('g')
        >>> h1 = scale.RomanNumeral(sc1, 1)
        >>> h1.root
        G
        ''')

    def _getBass(self):
        return self.scale.pitchFromScaleDegree(self.rootScaleStep + self._members[self._bassMemberIndex])

    bass = property(_getBass, 
        doc = '''Return the root of this harmony. 

        >>> from music21 import *
        >>> sc1 = scale.MajorScale('g')
        >>> h1 = scale.RomanNumeral(sc1, 1)
        >>> h1.bass
        G
        ''')


    def nextInversion(self):
        '''Invert the harmony one position, or place the next member after the current bass as the bass

        >>> from music21 import *
        >>> sc1 = scale.MajorScale('g4')
        >>> h1 = scale.TriadicHarmony(sc1, 5)
        >>> h1.getPitches()
        [D5, F#5, A5]
        >>> h1.nextInversion()
        >>> h1._bassMemberIndex
        1
        >>> h1.getPitches()
        [F#5, A5, D6]

        '''
        self._bassMemberIndex = (self._bassMemberIndex + 1) % len(self._members)
        

    def _memberIndexToScaleDegree(self, memberIndex):
        '''Given a member index, return the scale degree
        '''
        return self.scale.pitchFromScaleDegree(self.rootScaleStep + 
                    self._members[memberIndex], 
                    minPitch=minPitch, maxPitch=maxPitch)


    def getPitches(self, minPitch=None, maxPitch=None, direction=None):
        '''Return the pitches the constitute this RomanNumeral with the present Scale.

        >>> from music21 import *
        >>> sc1 = scale.MajorScale('g4')
        >>> h1 = scale.TriadicHarmony(sc1, 1)
        >>> h1.makeTriad()
        >>> h1.getPitches()
        [G4, B4, D5]
        >>> h1.rootScaleStep = 7
        >>> h1.getPitches()
        [F#5, A5, C6]

        >>> h1.rootScaleStep = 5
        >>> h1.getPitches('c2','c8')
        [D2, F#2, A2, D3, F#3, A3, D4, F#4, A4, D5, F#5, A5, D6, F#6, A6, D7, F#7, A7]

        '''
        # first, get members, than orient bass/direction
        post = []
        bass = self.scale.pitchFromScaleDegree(self.rootScaleStep + 
                    self._members[self._bassMemberIndex], 
                    minPitch=minPitch, maxPitch=maxPitch)

        # for now, getting directly from network
        #self.scale.abstract.net.realizePitchByStep()

        degreeTargets = [self.rootScaleStep + n for n in self._members]

        if maxPitch is None:
            # assume that we need within an octave above the bass
            maxPitch = bass.transpose('M7')

        # transpose up bass by m2, and assign to min
        post = self.scale.pitchesFromScaleDegrees(
            degreeTargets=degreeTargets, 
            minPitch=bass.transpose('m2'), 
            maxPitch=maxPitch, 
            direction=direction)

        #environLocal.printDebug(['getPitches', 'post', post, 'degreeTargets', degreeTargets, 'bass', bass, 'minPitch', minPitch, 'maxPitch', maxPitch])

        # add bass in front
        post.insert(0, bass)
        return post

    pitches = property(getPitches, 
        doc = '''Get the minimum default pitches for this RomanNumeral
        ''')

    def getChord(self, minPitch=None, maxPitch=None, direction=None):
        '''Return a realized chord for this harmony
        '''
        from music21 import chord
        return chord.Chord(self.getPitches(minPitch=minPitch, maxPitch=maxPitch, direction=direction))

    chord = property(getChord, 
        doc = '''Return a Chord object form this harmony over a default range
        ''')


    def parseFigure(self, figure):
        '''
        Given a figure string, returns a list of parsed elements.
        Each element is a tuple, consisting of the interval and the
        corresponding accidental string (None if there isn't any)

        Based on code by Jose Cabal-Ugaz.
        
        >>> from music21 import *   
        >>> h1 = scale.TriadicHarmony()
        >>> h1.parseFigure('6#,5,3')
        [(6, '#'), (5, None), (3, None)]
        >>> h1.parseFigure('6-,3-')
        [(6, '-'), (3, '-')]
        >>> h1.parseFigure('7-,#3')
        [(7, '-'), (3, '#')]
        '''
        pattern = '[,]'
        notations = re.split(pattern, figure)
        translations = []
        patternA1 = '[#-nN/][1-7]' #example: -6
        patternA2 = '[1-7][#-nN+/]' #example: 6+
        patternB = '[1-7]' #example: 6
        patternC = '[#-N+]' #example: # (which implies #3)
        intervalAboveBass = None
        accidentalString = None

        for n in notations:
            n = n.strip()
            if re.match(patternA1, n) != None:
                intervalAboveBass = int(n[1])
                accidentalString = n[0]
            elif re.match(patternA2, n) != None:
                intervalAboveBass = int(n[0])
                accidentalString = n[1]
            elif re.match(patternB, n) != None:
                intervalAboveBass = int(n[0])
                accidentalString = None
            elif re.match(patternC, n) != None:
                intervalAboveBass = 3
                accidentalString = n[0]
            translations.append((intervalAboveBass, accidentalString))
            
        return translations
    


    def makeTriad(self):
        '''Configure this triad as a diatonic triad
        '''
        self._members = [0,2,4] 

    def makeSeventhChord(self):
        '''Configure this triad as a diatonic seventh chord
        '''
        self._members = [0,2,4,6] 

    def makeNinthChord(self):
        '''Configure this triad as a diatonic seventh chord
        '''
        self._members = [0,2,4,6,8] 


    def _getRomanNumeral(self):
        '''

        >>> from music21 import *
        >>> sc1 = scale.MajorScale('g4')
        >>> h1 = scale.TriadicHarmony(sc1, 2)
        >>> h1.romanNumeral
        'ii'
        >>> h1.romanNumeral = 'vii'
        >>> h1.chord
        <music21.chord.Chord F#5 A5 C6>
        '''
        notation = []
        rawNumeral = common.toRoman(self.rootScaleStep)

        # for now, can just look at chord to get is minor
        # TODO: get intervals; measure intervals over the bass
        # need to realize in tandem with returning intervals

        c = self.chord
        if c.isMinorTriad():
            rawNumeral = rawNumeral.lower()
        elif c.isMajorTriad():
            rawNumeral = rawNumeral.upper()
    
        # todo: add inversion symbol
        return rawNumeral

    def _setRomanNumeral(self, numeral):
        # TODO: strip off inversion figures and configure inversion
        self.rootScaleStep = common.fromRoman(numeral)

    romanNumeral = property(_getRomanNumeral, _setRomanNumeral,
        doc='''Return the roman numeral representation of this RomanNumeral, or set this RomanNumeral with a roman numeral representation.
        ''')


    def setFromPitches(self):
        '''Given a list of pitches or pitch-containing objects, find a root and inversion that provides the best fit.
        '''
        pass




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass


    def testBasicLegacy(self):
        from music21 import note

        n1 = note.Note()
        
        CMajor = MajorScale(n1)
        
        assert CMajor.name == "C major"
        assert CMajor.getPitches()[6].step == "B"
        
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
        
        notes = [note1.name for note1 in aMinor.getPitches()]
        self.assertEqual(notes, ["A", "B", "C", "D", "E", "F", "G", 'A'])
        
        n3 = note.Note()
        n3.name = "B-"
        n3.octave = 5
        
        bFlatMinor = MinorScale(n3)
        assert bFlatMinor.name == "B- minor", "Got a different name: " + bFlatMinor.name
        notes2 = [note1.name for note1 in bFlatMinor.getPitches()]
        self.assertEqual(notes2, ["B-", "C", "D-", "E-", "F", "G-", "A-", 'B-'])
        assert bFlatMinor.getPitches()[0] == n3
        assert bFlatMinor.getPitches()[6].octave == 6
        
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





    def testBasic(self):
        # deriving a scale from a Stream

        # just get default, c-major, as derive will check all tonics
        sc1 = MajorScale()
        sc2 = MinorScale()

        # we can get a range of pitches
        self.assertEqual(str(sc2.getPitches('c2', 'c5')), '[C2, D2, E-2, F2, G2, A-2, B-2, C3, D3, E-3, F3, G3, A-3, B-3, C4, D4, E-4, F4, G4, A-4, B-4, C5]')



        # we can transpose the Scale
        sc3 = sc2.transpose('-m3')
        self.assertEqual(str(sc3.getPitches('c2', 'c5')), '[C2, D2, E2, F2, G2, A2, B2, C3, D3, E3, F3, G3, A3, B3, C4, D4, E4, F4, G4, A4, B4, C5]')
        
        # getting pitches from scale degrees
        self.assertEqual(str(sc3.pitchFromScaleDegree(3)), 'C4')
        self.assertEqual(str(sc3.pitchFromScaleDegree(7)), 'G4')
        self.assertEqual(str(sc3.pitchesFromScaleDegrees([1,5,6])), '[A3, E4, F4]')
        self.assertEqual(str(sc3.pitchesFromScaleDegrees([2,3], minPitch='c6', maxPitch='c9')), '[C6, B6, C7, B7, C8, B8, C9]')


        # given a pitch, get the scale degree
        sc4 = MajorScale('A-')
        self.assertEqual(sc4.getScaleDegreeFromPitch('a-'), 1)
        # default is pitch class matching
        self.assertEqual(sc4.getScaleDegreeFromPitch('g#'), 1)
        # can set pitch comparison attribute
        self.assertEqual(sc4.getScaleDegreeFromPitch('g#', 
            comparisonAttribute='name'), None)
        self.assertEqual(sc4.getScaleDegreeFromPitch('e-', 
            comparisonAttribute='name'), 5)

        # showing scales
        # this assumes that the tonic is not the first scale degree
        sc1 = HypophrygianScale('c4')
        self.assertEqual(str(sc1.pitchFromScaleDegree(1)), "G3")
        self.assertEqual(str(sc1.pitchFromScaleDegree(4)), "C4")
        #sc1.show()

        sc1 = MajorScale()
        # deriving a new scale from the pitches found in a collection
        from music21 import corpus
        s = corpus.parseWork('bwv66.6')
        sc3 = sc1.derive(s.parts['soprano'])
        self.assertEqual(str(sc3), '<music21.scale.MajorScale A major>')

        sc3 = sc1.derive(s.parts['tenor'])
        self.assertEqual(str(sc3), '<music21.scale.MajorScale A major>')

        sc3 = sc2.derive(s.parts['bass'])
        self.assertEqual(str(sc3), '<music21.scale.MinorScale F# minor>')


        # composing with a scale
        from music21 import stream, note
        s = stream.Stream()
        p = 'd#4'
        #sc = PhrygianScale('e')
        sc = MajorScale('E4')
        for d, x in [('ascending', 1), ('descending', 2), ('ascending', 3), 
                    ('descending', 4), ('ascending', 3),  ('descending', 2), 
                    ('ascending', 1)]:
            # use duration type instead of quarter length
            for y in [1, .5, .5, .25, .25, .25, .25]:
                p = sc.next(p, direction=d, stepSize=x)
                n = note.Note(p)
                n.quarterLength = y
                s.append(n)
        self.assertEqual(str(s.pitches), '[E4, F#4, G#4, A4, B4, C#5, D#5, B4, G#4, E4, C#4, A3, F#3, D#3, G#3, C#4, F#4, B4, E5, A5, D#6, G#5, C#5, F#4, B3, E3, A2, D#2, G#2, C#3, F#3, B3, E4, A4, D#5, B4, G#4, E4, C#4, A3, F#3, D#3, E3, F#3, G#3, A3, B3, C#4, D#4]')
        #s.show()


        # composing with an octatonic scale.
        s1 = stream.Part()
        s2 = stream.Part()
        p1 = 'b4'
        p2 = 'b3'
        sc = OctatonicScale('C4')
        for d, x in [('ascending', 1), ('descending', 2), ('ascending', 3), 
                    ('descending', 2), 
                    ('ascending', 1)]:
            for y in [1, .5, .5, .25, .25, .25, .25]:
                p1 = sc.next(p1, direction=d, stepSize=x)
                n = note.Note(p1)
                n.quarterLength = y
                s1.append(n)

            if d == 'ascending':
                d = 'descending'
            elif d == 'descending':
                d = 'ascending'

            for y in [.25, .25, .25, .25, .5, .5, 1]:
                p2 = sc.next(p2, direction=d, stepSize=x)
                n = note.Note(p2)
                n.quarterLength = y
                s2.append(n)

        s = stream.Score()
        s.insert(0, s1)
        s.insert(0, s2)
        #s.show()


        # compare two different major scales
        sc1 = MajorScale('g')
        sc2 = MajorScale('a')
        sc3 = MinorScale('f#')
        # exact comparisons
        self.assertEqual(sc1 == sc2, False)
        self.assertEqual(sc1.abstract == sc2.abstract, True)
        self.assertEqual(sc1 == sc3, False)
        self.assertEqual(sc1.abstract == sc3.abstract, False)

        # getting details on comparison
        self.assertEqual(str(sc1.match(sc2)), "{'notMatched': [C#5, G#5], 'matched': [A, B4, D5, E5, F#5, A5]}")




        # associating a harmony with a scale
        sc1 = MajorScale('g4')

        # define undefined
        #rn3 = sc1.romanNumeral(3, figure="7")

        h1 = TriadicHarmony(sc1, 1)
        h2 = TriadicHarmony(sc1, 2)
        h3 = TriadicHarmony(sc1, 3)
        h4 = TriadicHarmony(sc1, 4)
        h5 = TriadicHarmony(sc1, 5)

        # can get pitches or roman numerals
        self.assertEqual(str(h1.pitches), '[G4, B4, D5]')
        self.assertEqual(str(h2.pitches), '[A4, C5, E5]')
        self.assertEqual(h2.romanNumeral, 'ii')
        self.assertEqual(h5.romanNumeral, 'V')
        
        # can get pitches from various ranges, invert, and get bass
        h5.nextInversion()
        self.assertEqual(str(h5.bass), 'F#5')
        self.assertEqual(str(h5.getPitches('c2', 'c6')), '[F#2, A2, D3, F#3, A3, D4, F#4, A4, D5, F#5, A5]')

        h5.nextInversion()
        self.assertEqual(str(h5.getPitches('c2', 'c6')), '[A2, D3, F#3, A3, D4, F#4, A4, D5, F#5, A5]')

        h5.nextInversion()
        self.assertEqual(str(h5.bass), 'D5')
        self.assertEqual(str(h5.getPitches('c2', 'c6')), '[D2, F#2, A2, D3, F#3, A3, D4, F#4, A4, D5, F#5, A5]')


        sc1 = MajorScale('g4')
        h2 = TriadicHarmony(sc1, 2)
        h2.makeSeventhChord()
        self.assertEqual(str(h2.getPitches('c4', 'c6')), '[A4, C5, E5, A5, C6]')

        h2.makeNinthChord()
        self.assertEqual(str(h2.getPitches('c4', 'c6')), '[A4, B4, C5, E5, A5, B5, C6]')
        #h2.chord.show()



        # questions:
        # what is the first scale step of a plagal scale?

        # is octatonic diatonic

        # should harmonies store a network, or are best getting pitches from 
        # scale network

        # should altered pitches be defined in scale/harmony, or in the
        # inteval network


        # scale storing parameters
        # how to get a spelling in different ways
        # ex: octatonic should always compare on pitchClass


        # add serial rows as scales

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()

        t.testBasic()


# store implicit tonic or Not
# if not set, then comparisons fall to abstract

#------------------------------------------------------------------------------
# eof




