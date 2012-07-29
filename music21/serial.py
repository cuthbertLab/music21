# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         serial.py
# Purpose:      music21 classes for serial transformations
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               Carl Lian
#
# Copyright:    (c) 2009-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''This module defines objects for defining and manipulating structures 
common to serial and/or twelve-tone music, 
including :class:`~music21.serial.ToneRow` subclasses.
'''


import unittest, doctest
import copy

import music21
import music21.note
from music21 import stream
from music21 import pitch

from music21 import environment
_MOD = 'serial.py'
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class SerialException(Exception):
    pass


#-------------------------------------------------------------------------------
class TwelveToneMatrix(stream.Stream):
    '''
    An object representation of a 2-dimensional array of 12 pitches. 
    Internal representation is as a :class:`~music21.stream.Stream`, 
    which stores 12 Streams, each Stream a horizontal row of pitches 
    in the matrix. 

    This object is commonly used by calling the 
    :meth:`~music21.stream.TwelveToneRow.matrix` method of 
    :meth:`~music21.stream.TwelveToneRow` (or a subclass).

    __OMIT_FROM_DOCS__

    >>> from music21 import *
    >>> aMatrix = serial.rowToMatrix([0,2,11,7,8,3,9,1,4,10,6,5])
    '''
    
    def __init__(self, *arguments, **keywords):
        stream.Stream.__init__(self, *arguments, **keywords)
    
    def __str__(self):
        '''
        Return a string representation of the matrix.
        '''
        ret = ""
        for rowForm in self.elements:
            msg = []
            for pitch in rowForm:
                msg.append(str(pitch.pitchClassString).rjust(3))
            ret += ''.join(msg) + "\n"
        return ret

    def __repr__(self):
        if len(self.elements) > 0:
            if isinstance(ToneRow, self.elements[0]):
                return '<music21.serial.TwelveToneMatrix for [%s]>' % self.elements[0]
            else:
                return Music21Object.__repr__(self)
        else:
            return Music21Object.__repr__(self)

#-------------------------------------------------------------------------------
class ToneRow(stream.Stream):
    '''A Stream representation of a tone row, or an ordered sequence of pitches. 

    '''
    
    row = None

    _DOC_ATTR = {
    'row': 'A list representing the pitch class values of the row.',
    }
    
    _DOC_ORDER = ['pitches', 'noteNames', 'isTwelveToneRow', 'isSameRow', 'getIntervalsAsString', 
                  'zeroCenteredTransformation', 'originalCenteredTransformation',
                  'findZeroCenteredTransformations', 'findOriginalCenteredTransformations']
    
    def __init__(self):
        stream.Stream.__init__(self)
        
        if self.row != None:
            for pc in self.row:
                self.append(pitch.Pitch(pc))
        
    def pitches(self):
        
        '''
        Convenience method showing the pitch classes of a serial.ToneRow object as a list.
        
        >>> from music21 import *
        >>> L = [5*i for i in range(0,12)]
        >>> quintupleRow = serial.pcToToneRow(L)
        >>> quintupleRow.pitches()
        [0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7]
        >>> halfStep = serial.pcToToneRow([0, 1])
        >>> halfStep.pitches()
        [0, 1]
        
        '''
        
        pitchlist = [p.pitchClass for p in self]
        return pitchlist
    
    def noteNames(self):
        
        '''
        Convenience method showing the note names of a serial.ToneRow object as a list.
        
        >>> from music21 import *
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.noteNames()
        ['C', 'C#', 'D', 'E-', 'E', 'F', 'F#', 'G', 'G#', 'A', 'B-', 'B']
        >>> halfStep = serial.pcToToneRow([0,1])
        >>> halfStep.noteNames()
        ['C', 'C#']
        
        '''
        
        notelist = [p.name for p in self]
        return notelist
    
    def isTwelveToneRow(self):
        
        '''
        Describes whether or not a serial.ToneRow object constitutes a twelve-tone row. Note that a
        serial.TwelveToneRow object might not be a twelve-tone row.
        
        >>> from music21 import *
        >>> serial.pcToToneRow(range(0,12)).isTwelveToneRow()
        True
        >>> serial.pcToToneRow(range(0,10)).isTwelveToneRow()
        False
        >>> serial.pcToToneRow([3,3,3,3,3,3,3,3,3,3,3,3]).isTwelveToneRow()
        False
        
        '''
        
        pitchList = self.pitches()
        if len(pitchList) != 12:
            return False
        else:
            temp = True
            for i in range(0,11):
                if i not in pitchList:
                    temp = False
            return temp
    
    def makeTwelveToneRow(self):
        
        '''
        Convenience function returning a music21.TwelveToneRow object with the same pitches.
        Note that the TwelveToneRow object may not be a twelve tone row.
        
        >>> from music21 import *
        >>> a = serial.pcToToneRow(range(0,11))
        >>> type(a)
        <class 'music21.serial.ToneRow'>
        >>> p = pitch.Pitch()
        >>> p.pitchClass = 11
        >>> a.append(p)
        >>> a = a.makeTwelveToneRow()
        ...
        >>> type(a)
        <class 'music21.serial.TwelveToneRow'>
        '''
        
        pcSet = self.pitches()
        a = TwelveToneRow()
        for thisPc in pcSet:
            p = music21.pitch.Pitch()
            p.pitchClass = thisPc
            a.append(p)
        return a

    def isSameRow(self, row):
        
        '''
        Convenience function describing if two rows are the same.
        
        >>> from music21 import *
        >>> row1 = serial.pcToToneRow([6, 7, 8])
        >>> row2 = serial.pcToToneRow([-6, 19, 128])
        >>> row3 = serial.pcToToneRow([6, 7, -8])
        >>> row1.isSameRow(row2)
        True
        >>> row2.isSameRow(row1)
        True
        >>> row1.isSameRow(row3)
        False
        
        '''
        
        if len(row) != len(self):
            return False
        else:
            tempsame = True
            for i in range(0,len(row)):
                if tempsame == True:
                    if self[i].pitchClass != row[i].pitchClass:
                        tempsame = False
        
        return tempsame
    
    def getIntervalsAsString(self):
        
        '''
        
        Returns the string of intervals between consecutive pitch classes of a serial.ToneRow object.
        'T' = 10, 'E' = 11.
        
        >>> from music21 import *
        >>> cRow = serial.pcToToneRow([0])
        >>> cRow.getIntervalsAsString()
        ''
        >>> reversechromatic = serial.pcToToneRow([11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0])
        >>> reversechromatic.getIntervalsAsString()
        'EEEEEEEEEEE'
        
        '''
        
        numPitches = len(self)
        pitchList = self.pitches()
        intervalString = ''
        for i in range(0,numPitches - 1):
            interval = (pitchList[i+1] - pitchList[i]) % 12
            if interval in range(0,10):
                intervalString = intervalString + str(interval)
            if interval == 10:
                intervalString = intervalString + 'T'
            if interval == 11:
                intervalString = intervalString + 'E'
        return intervalString

    def zeroCenteredTransformation(self, transformationType, index):
        
        '''
        
        Returns a serial.ToneRow object giving a transformation of a tone row.
        Admissible transformations are 'P' (prime), 'I' (inversion),
        'R' (retrograde), and 'RI' (retrograde inversion). Note that in this convention, 
        the transformations P3 and I3 start on the pitch class 3, and the transformations
        R3 and RI3 end on the pitch class 3.
       
        >>> from music21 import *
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.pitches()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        >>> chromaticP3 = chromatic.zeroCenteredTransformation('P',3)
        >>> chromaticP3.pitches()
        [3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2]
        >>> chromaticI6 = chromatic.zeroCenteredTransformation('I',6)
        >>> chromaticI6.pitches()
        [6, 5, 4, 3, 2, 1, 0, 11, 10, 9, 8, 7]
        >>> schoenberg = serial.pcToToneRow(serial.RowSchoenbergOp26().row)
        >>> schoenberg.pitches()
        [3, 7, 9, 11, 1, 0, 10, 2, 4, 6, 8, 5]
        >>> schoenbergR8 = schoenberg.zeroCenteredTransformation('R',8)
        >>> schoenbergR8.pitches()
        [10, 1, 11, 9, 7, 3, 5, 6, 4, 2, 0, 8]
        >>> schoenbergRI9 = schoenberg.zeroCenteredTransformation('RI',9)
        >>> schoenbergRI9.noteNames()
        ['G', 'E', 'F#', 'G#', 'B-', 'D', 'C', 'B', 'C#', 'E-', 'F', 'A']
        
        '''
            
        numPitches = len(self)
        pitchList = self.pitches()
        if int(index) != index:
            raise SerialException("Transformation must be by an integer.")
        else:
            firstPitch = pitchList[0]
            transformedPitchList = []
            if transformationType == 'P':
                for i in range(0,numPitches):
                    newPitch = (pitchList[i] - firstPitch + index) % 12
                    transformedPitchList.append(newPitch)
                return pcToToneRow(transformedPitchList)
            elif transformationType == 'I':
                for i in range(0,numPitches):
                    newPitch = (index + firstPitch - pitchList[i]) % 12
                    transformedPitchList.append(newPitch)
                return pcToToneRow(transformedPitchList)
            elif transformationType == 'R':
                for i in range(0,numPitches):
                    newPitch = (index + pitchList[numPitches-1-i] - firstPitch) % 12
                    transformedPitchList.append(newPitch)
                return pcToToneRow(transformedPitchList)
            elif transformationType == 'RI':
                for i in range(0,numPitches):
                    newPitch = (index - pitchList[numPitches-1-i] + firstPitch) % 12
                    transformedPitchList.append(newPitch)
                return pcToToneRow(transformedPitchList) 
            else:
                raise SerialException("Invalid transformation type.")
            
    def originalCenteredTransformation(self, transformationType, index):
        
        '''
        
        Returns a serial.ToneRow object giving a transformation of a tone row.
        Admissible transformations are 'T' (transposition), 'I' (inversion),
        'R' (retrograde), and 'RI' (retrograde inversion). Note that in this convention,
        which is less common than the 'zero-centered' convention, the original row is not
        transposed to start on the pitch class 0. Thus, the transformation T3 transposes
        the original row by 3 semitones, and the transformations I3, R3, and RI3 first
        transform the row appropriately (without transposition), then transpose the resulting
        row by 3 semitones.
       
        >>> from music21 import *
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.pitches()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        >>> chromaticP3 = chromatic.originalCenteredTransformation('P',3)
        >>> chromaticP3.pitches()
        [3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2]
        >>> chromaticI6 = chromatic.originalCenteredTransformation('I',6)
        >>> chromaticI6.pitches()
        [6, 5, 4, 3, 2, 1, 0, 11, 10, 9, 8, 7]
        >>> schoenberg = serial.pcToToneRow(serial.RowSchoenbergOp26().row)
        >>> schoenberg.pitches()
        [3, 7, 9, 11, 1, 0, 10, 2, 4, 6, 8, 5]
        >>> schoenbergR8 = schoenberg.originalCenteredTransformation('R',8)
        >>> schoenbergR8.pitches()
        [1, 4, 2, 0, 10, 6, 8, 9, 7, 5, 3, 11]
        >>> schoenbergRI9 = schoenberg.originalCenteredTransformation('RI',9)
        >>> schoenbergRI9.noteNames()
        ['B-', 'G', 'A', 'B', 'C#', 'F', 'E-', 'D', 'E', 'F#', 'G#', 'C']
        
        '''
        
        pitchList = self.pitches()
        firstPitch = pitchList[0]
        newIndex = (firstPitch + index) % 12
        if transformationType == 'T':
            return self.zeroCenteredTransformation('P', newIndex)
        else:
            return self.zeroCenteredTransformation(transformationType, newIndex)
        
    
    def findZeroCenteredTransformations(self, otherRow):
        ''' 
        
        Gives the list of zero-centered serial transformations taking one tone row
        to another, the second specified in the argument. Each transformation is given as a
        tuple of the transformation type and index.
        
        >>> from music21 import *
        >>> chromatic = serial.pcToToneRow([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1])
        >>> reversechromatic = serial.pcToToneRow([8, 7, 6, 5, 4, 3, 2, 1, 0, 11, 10, 9])
        >>> chromatic.findZeroCenteredTransformations(reversechromatic)
        [('I', 8), ('R', 9)]
        >>> schoenberg25 = serial.pcToToneRow(serial.RowSchoenbergOp25.row)
        >>> schoenberg26 = serial.pcToToneRow(serial.RowSchoenbergOp26.row)
        >>> schoenberg25.findZeroCenteredTransformations(schoenberg26)
        []
        >>> schoenberg26.findZeroCenteredTransformations(schoenberg26.zeroCenteredTransformation('RI',8))
        [('RI', 8)]
        
        '''
        if len(self) != len(otherRow):
            return False
        else:
            otherRowPitches = otherRow.pitches()
            transformationList = []
            firstPitch = otherRowPitches[0]
            lastPitch = otherRowPitches[-1]
            
            if otherRowPitches == self.zeroCenteredTransformation('P',firstPitch).pitches():
                transformation = 'P', firstPitch
                transformationList.append(transformation)
            if otherRowPitches == self.zeroCenteredTransformation('I',firstPitch).pitches():
                transformation = 'I', firstPitch
                transformationList.append(transformation)
            if otherRowPitches == self.zeroCenteredTransformation('R',lastPitch).pitches():
                transformation  = 'R', lastPitch
                transformationList.append(transformation)
            if otherRowPitches == self.zeroCenteredTransformation('RI',lastPitch).pitches():
                transformation = 'RI', lastPitch
                transformationList.append(transformation)
                
            return transformationList
        
    def findOriginalCenteredTransformations(self, otherRow):
        ''' 
        
        Gives the list of original-centered serial transformations taking one tone row
        to another, the second specified in the argument. Each transformation is given as a tuple
        of the transformation type and index.
        
        >>> from music21 import *
        >>> chromatic = serial.pcToToneRow([2, 3, 4, 5, 6, 7, 8, 9, 'A', 'B', 0, 1])
        >>> reversechromatic = serial.pcToToneRow([8, 7, 6, 5, 4, 3, 2, 1, 0, 'B', 'A', 9])
        >>> chromatic.findOriginalCenteredTransformations(reversechromatic)
        [('I', 6), ('R', 7)]
        >>> schoenberg25 = serial.pcToToneRow(serial.RowSchoenbergOp25.row)
        >>> schoenberg26 = serial.pcToToneRow(serial.RowSchoenbergOp26.row)
        >>> schoenberg25.findOriginalCenteredTransformations(schoenberg26)
        []
        >>> schoenberg26.findOriginalCenteredTransformations(schoenberg26.originalCenteredTransformation('RI',8))
        [('RI', 8)]
        
        '''
        
        originalRowPitches = self.pitches()
        otherRowPitches = otherRow.pitches()
        transformationList = []
        oldFirstPitch = originalRowPitches[0]
        oldLastPitch = originalRowPitches [-1]
        newFirstPitch = otherRowPitches[0]
        newLastPitch = otherRowPitches[-1]
        
        if otherRowPitches == self.originalCenteredTransformation('P',(newFirstPitch - oldFirstPitch) % 12).pitches():
            transformation = 'P', (newFirstPitch - oldFirstPitch) % 12
            transformationList.append(transformation)
        if otherRowPitches == self.originalCenteredTransformation('I',(newFirstPitch - oldFirstPitch) % 12).pitches():
            transformation = 'I', (newFirstPitch - oldFirstPitch) % 12
            transformationList.append(transformation)
        if otherRowPitches == self.originalCenteredTransformation('R',(newFirstPitch - oldLastPitch) % 12).pitches():
            transformation  = 'R', (newFirstPitch - oldLastPitch) % 12
            transformationList.append(transformation)
        if otherRowPitches == self.originalCenteredTransformation('RI',(newFirstPitch - 2*oldFirstPitch + oldLastPitch) % 12).pitches():
            transformation = 'RI', (newFirstPitch - 2*oldFirstPitch + oldLastPitch) % 12
            transformationList.append(transformation)
            
        return transformationList
    

# ----------------------------------------------------------------------------------------

class TwelveToneRow(ToneRow):
    
    '''A Stream representation of a twelve-tone row, capable of producing a 12-tone matrix.
    '''
    #row = None

    #_DOC_ATTR = {
    #'row': 'A list representing the pitch class values of the row.',
    #}
    
    _DOC_ORDER = ['matrix', 'isAllInterval', 'getLinkClassification', 'isLinkChord', 'areCombinatorial']
    

    def __init__(self):
        ToneRow.__init__(self)
        #environLocal.printDebug(['TwelveToneRow.__init__: length of elements', len(self)])

        #if self.row != None:
        #    for pc in self.row:
        #        self.append(pitch.Pitch(pc))
    
    def matrix(self):
        '''
        Returns a :class:`~music21.serial.TwelveToneMatrix` object for the row.  That object can just be printed (or displayed via .show())
        
        >>> from music21 import *
        >>> src = serial.RowSchoenbergOp37()
        >>> [p.name for p in src]
        ['D', 'C#', 'A', 'B-', 'F', 'E-', 'E', 'C', 'G#', 'G', 'F#', 'B']
        >>> len(src)
        12
        >>> s37 = serial.RowSchoenbergOp37().matrix()
        >>> print s37
          0  B  7  8  3  1  2  A  6  5  4  9
          1  0  8  9  4  2  3  B  7  6  5  A
          5  4  0  1  8  6  7  3  B  A  9  2
          4  3  B  0  7  5  6  2  A  9  8  1
        ...
        >>> [e for e in s37[0]]
        [C, B, G, G#, E-, C#, D, B-, F#, F, E, A]

        
        '''        
        # note: do not want to return a TwelveToneRow() type, as this will
        # add again the same pitches to the elements list twice. 
        p = self.getElementsByClass(pitch.Pitch, returnStreamSubClass=False)

        i = [(12-x.pitchClass) % 12 for x in p]
        matrix = [[(x.pitchClass+t) % 12 for x in p] for t in i]

        matrixObj = TwelveToneMatrix()
        i = 0
        for row in matrix:
            i += 1
            rowObject = copy.copy(self)
            rowObject.elements = []
            rowObject.id = 'row-' + str(i)
            for p in row: # iterate over pitch class values
                pObj = pitch.Pitch()
                pObj.pitchClass = p
                rowObject.append(pObj)
            matrixObj.insert(0, rowObject)
        

        #environLocal.printDebug(['calling matrix start: len row:', self.row, 'len self', len(self)])

        return matrixObj
    
                    
    def isAllInterval(self):
        
        '''
        Describes whether or not a twelve-tone row is an all-interval row.
        
        >>> from music21 import *
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.pitches()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        >>> chromatic.isAllInterval()
        False
        >>> bergLyric = serial.pcToToneRow(serial.RowBergLyricSuite().row)
        >>> bergLyric.pitches()
        [5, 4, 0, 9, 7, 2, 8, 1, 3, 6, 10, 11]
        >>> bergLyric.isAllInterval()
        True
        '''
        tempAllInterval = True
        intervalString = self.getIntervalsAsString()
        for i in range(1,10):
            if str(i) not in intervalString:
                tempAllInterval = False
        if 'T' not in intervalString:
            tempAllInterval = False
        if 'E' not in intervalString:
            tempAllInterval = False
        return tempAllInterval
    
    def getLinkClassification(self):
        
        '''
        Gives the classification number of a Link Chord (as given in http://www.johnlinkmusic.com/LinkChords.pdf), 
        that is, is an all-interval twelve-tone row containing a voicing of the all-trichord hexachord: [0, 1, 2, 4, 7, 8].
        In addition, gives a list of sets of five contiguous intervals within the row representing a voicing
        of the all-trichord hexachord. Note that the interval sets may be transformed.
        
        Named for John Link who discovered them.
        
        >>> from music21 import *
        >>> bergLyric = serial.pcToToneRow(serial.RowBergLyricSuite().row)
        >>> bergLyric.pitches()
        [5, 4, 0, 9, 7, 2, 8, 1, 3, 6, 10, 11]
        >>> bergLyric.isAllInterval()
        True
        >>> bergLyric.getLinkClassification()
        (None, [])
        >>> link = serial.pcToToneRow([0, 3, 8, 2, 10, 11, 9, 4, 1, 5, 7, 6])
        >>> link.getLinkClassification()
        (62, ['8352E'])
        >>> doubleLink = serial.pcToToneRow([0, 1, 8, 5, 7, 10, 4, 3, 11, 9, 2, 6])
        >>> doubleLink.getLinkClassification()
        (33, ['236E8', '36E8T'])
        
        '''
        
        #the link interval strings given below are untransformed: by inversion around 0, original-centered retrograde, and
        #retrograde inversion around zero, we get three more link interval strings for each one in fullLinkIntervals.
        #in the original rows, this corresponds simply to checking the interval string of any
        # inversion, retrograde inversion, and retrograde, respectively.
        
        fullLinkIntervals = ['125634T97E8', '134E78526T9', '134E79T6258', '134E79T6258', '1367T89E254', '137E542896T', '137E982456T', '142965837ET', '142973856ET', '1429738E65T', '14297TE6853', '145638E729T', '1456T729E83', '1456T982E73', '145927E836T', '14598E63T72', '14689T7E253', '1469E27T853', '149278356ET', '1492783E65T', '1496258T73E', '1496E358T72', '14972836E5T', '14972E6385T', '1497T853E62', '14E379T6528', '14E6T783529', '172E6853T94', '17356ET8294', '1738T542E69', '173E65T8294', '1763T4952E8', '176852E34T9', '179236E8T54', '179236E8T54', '17923E685T4', '179245T8E63', '17924T586E3', '179T65234E8', '179T8E63254', '179T8E63254', '1825E43796T', '1825E43796T', '1825E79T364', '1825E79T364', '1852E43769T', '1852E79463T', '185629TE743', '18563479TE2', '18563E7T492', '18734E5296T', '18734E5296T', '187E259436T', '187E259436T', '18T352E7964', '18T497E3562', '18T97E52364', '18T97E52364', '18E63T79452', '18E63T79452', '19476538TE2', '1947T8536E2', '1954763T8E2', '19742538E6T', '197425T6E83', '1974T8E6352', '197T8532E64', '1T5E7928364', '1T63E874259', '1T6E3852479', '1T8352E4679', '1T974253E68', '214367TE985', '214376598ET', '214376598ET', '2143E86597T', '2149586E37T', '214976538ET', '214976538ET', '216734ET985', '216743E9T85', '217634TE985', '21T8E956347', '21T96583E47', '234T1596E87', '235189E647T', '235189E647T', '23689E7T145', '236E981547T', '236E981547T', '23T514697E8', '2513647ET98', '25189TE7463', '25189TE7463', '2546E981T73', '25691T8E473', '2569E8T1437', '258T73E6149', '258T9614E37', '25T31496E87', '25T89E61437', '2618T497E35', '26347ET9185', '263891T7E45', '263891T7E45', '2653E718T49', '2654T1783E9', '2654T1783E9', '2654E3871T9', '2654E3871T9', '2654E7T1983', '2654E7T1983', '265819TE743', '2659E8T1347', '267431T8E95', '2694T817E35', '269T1783E45', '269T1783E45', '269E3871T45', '269E3871T45', '26E451T7389', '26E451T7389', '26E459817T3', '26E459817T3', '26E4T718953', '26E4T718953', '26E873T5149', '26E95134T87', '26E95178T43', '274316E985T', '274316E985T', '2743E86591T', '274916E385T', '274916E385T', '2749586E31T', '276134ET985', '276143E9T85', '27E34169T85', '2965387E41T', '2965387E41T', '296E387T145', '29TE7436185', '29TE7463158', '29E7835641T', '29E7835641T', '2E431T96587', '2E431T96587', '2E465387T19', '2E637T85419', '2E783T51469', '2E783T51469', '2E796415T38', '2E8T1956743', '2E9658T4137', '3142E8956T7', '3142ET79685', '31456T972E8', '314672E9T85', '3152689TE74', '3152689TE74', '3152E9T8764', '3158629TE74', '3158629TE74', '316452E98T7', '317ET562894', '317ET926854', '317ET986254', '319765T42E8', '3198265TE74', '31T524796E8', '31T567942E8', '31T7E294685', '325E79T8164', '325E79T8164', '3265981TE74', '329E71T4568', '329E71T4568', '32E981T6547', '347621T8E95', '3479TE26185', '34T9E712568', '35146T927E8', '35146T927E8', '351T64927E8', '351T64927E8', '351T7924E68', '35216E98T74', '3521T8E9674', '3581629ET74', '3594T6127E8', '359E6128T74', '35E7216T498', '35E72946T18', '35E729T6418', '3625189TE74', '3625189TE74', '36524ET8917', '3674218T9E5', '36T154927E8', '36T154927E8', '3764128T9E5', '38297E5T164', '38E729T6145', '3T17E924568', '3T17E924568', '3T4952E8617', '3T6194527E8', '3T62E815497', '3T97E528164', '3T97E528164', '3E2418596T7', '3E7T4926185', '416352E7T98', '41T629E7835', '41T629E7835', '4328T56E917', '4328TE65917', '43T9E865217', '463152E9T87', '46529E8T137', '46731T8E925', '4692E513T87', '4692E513T87', '46982315ET7', '469T315E287', '469T315E287', '4769E251T38', '4783T1629E5', '47T198236E5', '47E928361T5', '4T1629E3785', '4TE86592317', '4E2538T1697', '4E29658T317', '4E29658T317', '4ET85692317', '4ET85692317', '5896T142E37']
        specialLinkIntervals = ['25634', '134E7', '134E7', 'E79T6', '89E25', '7E542', '7E982', '29658', '856ET', '8E65T', 'E6853', '8E729', '729E8', '982E7', '927E8', '8E63T', '7E253', '7T853', '78356', '783E6', '58T73', '358T7', '2836E', '2E638', '7T853', '79T65', '78352', 'E6853', '56ET8', '42E69', 'E65T8', '4952E', '52E34', '236E8', '36E8T', '3E685', 'T8E63', '586E3', '79T65', 'T8E63', '8E632', '25E43', '5E437', '25E79', '5E79T', 'E4376', 'E7946', '9TE74', '479TE', 'E7T49', '734E5', '34E52', '87E25', 'E2594', '352E7', 'T497E', 'T97E5', '97E52', '8E63T', 'T7945', '76538', '7T853', '4763T', '97425', '97425', 'T8E63', '7T853', '5E792', '74259', '52479', '8352E', '97425', '4367T', '43765', '76598', 'E8659', '586E3', '49765', '76538', '6734E', '21674', '7634T', '1T8E9', 'T9658', '34T15', '5189E', '189E6', '689E7', '6E981', 'E9815', '3T514', '47ET9', '25189', '9TE74', '6E981', '91T8E', '9E8T1', '58T73', 'T9614', '5T314', '89E61', 'T497E', '47ET9', '891T7', '1T7E4', 'E718T', 'T1783', '1783E', 'E3871', '3871T', '4E7T1', '7T198', '9TE74', '9E8T1', '1T8E9', 'T817E', 'T1783', '1783E', 'E3871', '3871T', '451T7', '1T738', '59817', '9817T', 'T7189', '71895', '3T514', '5134T', '5178T', '4316E', '16E98', 'E8659', '4916E', '16E38', '586E3', '6134E', '27614', '4169T', '65387', '5387E', '6E387', '9TE74', '9TE74', 'E7835', '78356', 'E431T', 'T9658', '65387', '37T85', '2E783', '3T514', '415T3', 'E8T19', '9658T', '3142E', '3142E', '56T97', '31467', '52689', '9TE74', '152E9', '58629', '9TE74', '52E98', '56289', '92685', '98625', '765T4', '98265', '52479', '56794', '31T7E', '25E79', '5E79T', '65981', '29E71', '9E71T', '2E981', '1T8E9', '479TE', 'T9E71', '146T9', '927E8', '1T649', '927E8', '51T79', '16E98', '1T8E9', '1629E', '94T61', 'E6128', '16T49', '946T1', '9T641', '25189', '9TE74', '36524', '36742', 'T1549', '927E8', '37641', '297E5', '8E729', 'T17E9', '17E92', '4952E', '61945', '15497', 'T97E5', '97E52', '3E241', 'E7T49', '352E7', '629E7', 'E7835', '8T56E', '8TE65', '9E865', '152E9', '9E8T1', '1T8E9', '2E513', 'E513T', '2315E', 'T315E', '315E2', '9E251', '1629E', '7T198', '8361T', '1629E', 'E8659', 'E2538', '29658', '9658T', 'T8569', '85692', '142E3']
        linkClassification = [1, 2, 3, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 33, 34, 35, 36, 37, 38, 38, 39, 39, 40, 40, 41, 42, 43, 44, 45, 46, 46, 47, 47, 48, 49, 50, 50, 51, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 65, 66, 67, 68, 68, 69, 70, 71, 72, 73, 74, 75, 75, 76, 77, 77, 78, 79, 80, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 90, 91, 92, 92, 93, 93, 94, 94, 95, 96, 97, 98, 99, 99, 100, 100, 101, 101, 102, 102, 103, 103, 104, 105, 106, 107, 107, 108, 109, 109, 110, 111, 112, 113, 114, 114, 115, 116, 117, 118, 118, 119, 119, 120, 121, 122, 122, 123, 124, 125, 126, 127, 128, 129, 130, 130, 131, 132, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 142, 143, 144, 144, 145, 146, 147, 148, 149, 149, 150, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 160, 161, 162, 163, 163, 164, 165, 166, 167, 167, 168, 169, 170, 171, 171, 172, 173, 174, 175, 175, 176, 177, 178, 179, 180, 181, 182, 182, 183, 184, 184, 185, 186, 187, 188, 189, 190, 191, 192, 192, 193, 193, 194]

        numchords = len(fullLinkIntervals)
        
        rowchecklist = [self, self.zeroCenteredTransformation('I',0), self.zeroCenteredTransformation('R',0), self.zeroCenteredTransformation('RI',0)]
        
        specialintervals = []
        classification = None
        for row in rowchecklist:
            intervals = row.getIntervalsAsString()
            for i in range(0,numchords):
                if fullLinkIntervals[i] == intervals:
                    classification = linkClassification[i]
                    specialintervals.append(specialLinkIntervals[i])
        if specialintervals == []:
            return None, []
        else:
            return classification, specialintervals

    def isLinkChord(self):
        
        '''
        Describes whether or not a twelve-tone row is a Link Chord.
        
        >>> from music21 import *
        >>> bergLyric = serial.pcToToneRow(serial.RowBergLyricSuite().row)
        >>> bergLyric.pitches()
        [5, 4, 0, 9, 7, 2, 8, 1, 3, 6, 10, 11]
        >>> bergLyric.isAllInterval()
        True
        >>> bergLyric.isLinkChord()
        False
        >>> link = serial.pcToToneRow([0, 3, 8, 2, 10, 11, 9, 4, 1, 5, 7, 6])
        >>> link.isLinkChord()
        True
        >>> doubleLink = serial.pcToToneRow([0, 1, 8, 5, 7, 10, 4, 3, 11, 9, 2, 6])
        >>> doubleLink.isLinkChord()
        True

        '''
        
        tuple = self.getLinkClassification()
        if tuple[0] == None:
            return False
        else:
            return True
    
    def areCombinatorial(self, transType1, index1, transType2, index2, convention):
        
        '''
        Describes whether or not two transformations, with one of the zero-centered
        and original-centered conventions specified (as in the zeroCenteredRowTransformation
        and originalCenteredRowTransformation methods), of a twelve-tone row are combinatorial.
        The first and second arguments describe one transformation, while the third and fourth
        describe another.
        
        >>> from music21 import *
        >>> moses = serial.pcToToneRow(serial.RowSchoenbergMosesAron.row)
        >>> moses.pitches()
        [9, 10, 4, 2, 3, 1, 7, 5, 6, 8, 11, 0]
        >>> moses.areCombinatorial('P', 1, 'I', 4, 'zero')
        True
        >>> moses.areCombinatorial('R', 5, 'RI', 6, 'original')
        False
        '''
        
        if convention == 'zero':
            testRow = []
            trans1 = self.zeroCenteredTransformation(transType1, index1)
            pitches1 = trans1.pitches()
            trans2 = self.zeroCenteredTransformation(transType2, index2)
            pitches2 = trans2.pitches()
            for i in range(0,6):
                testRow.append(pitches1[i])
            for i in range(0,6):
                testRow.append(pitches2[i])
            return pcToToneRow(testRow).isTwelveToneRow()
        if convention == 'original':
            testRow = []
            trans1 = self.originalCenteredTransformation(transType1, index1)
            pitches1 = trans1.pitches()
            trans2 = self.originalCenteredTransformation(transType2, index2)
            pitches2 = trans2.pitches()
            for i in range(0,6):
                testRow.append(pitches1[i])
            for i in range(0,6):
                testRow.append(pitches2[6+i])
            return pcToToneRow(testRow).isTwelveToneRow()
        else:
            raise SerialException("Invalid convention - choose 'zero' or 'original'.")

# ------- parsing functions for atonal music -------

# add defaults
# add hyperlinks
# first describe what function , then explain arguments, then explain what is returned.
# caps on things
# doc order

def getContiguousSegmentsOfLength(inputPart, length, reps, chords = 'skipChords'):
    
    '''
    
    Finds contiguous segments of notes in a stream,
    where the number of notes in the segment is specified. 
    
    The inputPart must be a stream.Part object or otherwise a stream object with at most one part.
    The length is an integer specifying the desired number of notes in each contiguous segment.
    
    The reps argument specifies how repeated pitch classes are dealt with. 
    It may be set to 'skipConsecutive', 'rowsOnly', or 'includeAll'.
    The first setting treats immediate repetitions of pitch classes as one instance of the
    same pitch class. The second only finds segments of consecutive pitch classes
    which are distinct, i.e. tone rows. The third includes all repeated pitches.
    
    The 'chord' argument specifies how chords are dealt with. At the present time, it must be 
    set to 'skipChords', which ignores any segment containing a chord.
    
    The returned list gives all contiguous segments with the desired number of notes subject
    to the specified constraints on repetitions and chords. Each entry of the list is a tuple of a
    contiguous segment of notes and the measure number of its first note.
    
    
    >>> from music21 import *
    >>> s = stream.Stream()
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 6
    >>> s.append(n1)
    >>> n2 = note.Note('f4')
    >>> n2.quarterLength = 1
    >>> s.append(n2)
    >>> n3 = chord.Chord(['g4', 'b4'])
    >>> n3.quarterLength = 1
    >>> s.append(n3)
    >>> n4 = note.Note('g4')
    >>> n4.quarterLength = 1
    >>> s.repeatAppend(n4, 2)
    >>> n5 = note.Note('a4')
    >>> n5.quarterLength = 3
    >>> s.repeatAppend(n5, 2)
    >>> n6 = note.Note('b4')
    >>> n6.quarterLength = 1
    >>> s.append(n6)
    >>> n7 = note.Note('c5')
    >>> n7.quarterLength = 1
    >>> s.append(n7)
    >>> s = s.makeMeasures()
    >>> s.makeTies()
    >>> serial.getContiguousSegmentsOfLength(s, 3, 'skipConsecutive', 'skipChords')
    [([<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>], 3), 
    ([<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>], 3)]
    >>> serial.getContiguousSegmentsOfLength(s, 3, 'rowsOnly', 'skipChords')
    [([<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>], 4)]
    >>> serial.getContiguousSegmentsOfLength(s, 3, 'includeAll', 'skipChords')
    [([<music21.note.Note G>, <music21.note.Note G>, <music21.note.Note A>], 3), 
    ([<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note A>], 3), 
    ([<music21.note.Note A>, <music21.note.Note A>, <music21.note.Note B>], 3), 
    ([<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>], 4)]
    
    __OMIT_FROM_DOCS__
    
    >>> from music21 import *
    >>> n1 = note.Note('c#4')
    >>> n2 = note.Note('e4')
    >>> n3 = note.Note('d#4')
    >>> n4 = note.Note('f4')
    >>> n5 = note.Note('e4')
    >>> n6 = note.Note('g4')
    >>> notelist = [n1, n2, n3, n4, n5, n6]
    >>> part = stream.Part()
    >>> for n in notelist:
    ...    n.quarterLength = 1
    ...    part.append(n)
    >>> part = part.makeMeasures()
    >>> serial.getContiguousSegmentsOfLength(part, 3, 'rowsOnly', 'skipChords')
    [([<music21.note.Note C#>, <music21.note.Note E>, <music21.note.Note D#>], 1), 
    ([<music21.note.Note E>, <music21.note.Note D#>, <music21.note.Note F>], 1), 
    ([<music21.note.Note D#>, <music21.note.Note F>, <music21.note.Note E>], 1), 
    ([<music21.note.Note F>, <music21.note.Note E>, <music21.note.Note G>], 1)]

    '''
    
    #reps settings: skipconsecutive, rowsonly, includeall
    #chords settings: skipchords, readfrombottom, readfromtop
    
    listOfPitchLists = []
    currentPitchLists = []
    inputPart = inputPart.stripTies(False, False, True)
    
    if len(inputPart.getElementsByClass(stream.Part)) == 0:
        measures = inputPart.getElementsByClass(stream.Measure)
    elif len(inputPart.getElementsByClass(stream.Part)) == 1:
        measures = inputPart.parts[0].getElementsByClass(stream.Measure)
    else:
        raise SerialException("serial.getContiguousSegmentsOfLength can only applied to streams with one part.")
    
    
    
    if chords == 'skipChords':
        pitchList = []
        if reps == 'skipConsecutive':
            for m in measures:
                for n in m.flat.notes:
                    add = False
                    if len(n.pitches) == 1:
                        if pitchList == []:
                            add = True
                        else:
                            if pitchList[-1].pitchClass != n.pitchClass:
                                add = True
                        if add == True:
                            pitchList.append(n)
                            if len(pitchList) == length + 1:
                                pitchList.remove(pitchList[0])
                            if len(pitchList) == length:
                                listOfPitchLists.append((list(pitchList), 
                                                         pitchList[0].measureNumber))
                    elif len(n.pitches) > 1:
                            pitchList = []
# --- below code doesn't work properly, but also seems to me like it would be the least useful
# --- thing to do with repeated pitches
#        elif reps == 'skipall':
#            for m in measures:
#                for n in m.flat.notes:
#                    if len(n.pitches) == 1 and n not in pitchList:
#                        pitchList.append(n)
#                        if len(pitchList) == length + 1:
#                            pitchList.remove(pitchList[0])
#                        if len(pitchList) == length:
#                            listOfPitchLists.append((list(pitchList), pitchList[0].measureNumber))
#                    elif len(n.pitches) > 1:
#                        pitchList = []
        elif reps == 'rowsOnly':
            for m in measures:
                for n in m.flat.notes:
                    if len(n.pitches) == 1:
                        if len(pitchList) == length:
                            if n not in pitchList[1:]:
                                pitchList.append(n)
                                pitchList.remove(pitchList[0])
                            else:
                                pitchList = [n]
                        else:
                            if n not in pitchList:
                                pitchList.append(n)
                            else:
                                pitchList = [n]
                        if len(pitchList) == length:
                            listOfPitchLists.append((list(pitchList), 
                                                 pitchList[0].measureNumber))
                    else:
                        pitchList = []
                        
            return listOfPitchLists
        
        elif reps == 'includeAll':
            for m in measures:
                for n in m.flat.notes:
                    if len(n.pitches) == 1:
                        pitchList.append(n)
                        if len(pitchList) == length + 1:
                            pitchList.remove(pitchList[0])
                        if len(pitchList) == length:
                            listOfPitchLists.append((list(pitchList), 
                                                     pitchList[0].measureNumber))
                    else:
                        pitchList = []
        else:
            raise SerialException("Invalid repeated pitch setting.")
    else:
        raise SerialException("Invalid chord setting.")
    return listOfPitchLists
    

#chordify - search multiple parts simultaneously


def findSegments(inputStream, segmentlist, reps, chords):
    
    '''
    Given a stream object and list of contiguous segments of pitch classes (each given as a list), returns a list of all
    instances of the segment in the stream subject to the constraints on repetitions of pitches
    and how chords are dealt with as described in getContinuousSegmentsOfLength. Each
    instance is given as a tuple of the segment of notes, the number of the measure in which it appears, and,
    if the stream object contains parts, the part in which it appears (where a lower number
    denotes a higher part).
    
    >>> from music21 import *
    >>> part = stream.Part()
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 6
    >>> part.append(n1)
    >>> n2 = note.Note('f4')
    >>> n2.quarterLength = 1
    >>> part.append(n2)
    >>> n3 = chord.Chord(['g4', 'b4'])
    >>> n3.quarterLength = 1
    >>> part.append(n3)
    >>> n4 = note.Note('g4')
    >>> n4.quarterLength = 1
    >>> part.repeatAppend(n4, 2)
    >>> n5 = note.Note('a4')
    >>> n5.quarterLength = 3
    >>> part.repeatAppend(n5, 2)
    >>> n6 = note.Note('b4')
    >>> n6.quarterLength = 1
    >>> part.append(n6)
    >>> n7 = note.Note('c5')
    >>> n7.quarterLength = 1
    >>> part.append(n7)
    >>> newpart = part.makeMeasures()
    >>> newpart.makeTies()
    >>> findSegments(newpart, [[7, 9, 11]], 'skipConsecutive', 'skipChords')
    [([<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>], 3)]
    >>> findSegments(newpart, [[7, 9, 11], [9, 11, 0]], 'skipConsecutive', 'skipChords')
    [([<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>], 3), 
    ([<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>], 3)]
    >>> s = stream.Stream()
    >>> s.repeatAppend(newpart, 2)
    >>> findSegments(s, [[7, -3, 11]], 'skipConsecutive', 'skipChords')
    [([<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>], 3, 1), 
    ([<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>], 3, 2)]
    
    __OMIT_FROM_DOCS__
    
    >>> findSegments(newpart, [[7, 9, 11], [9, 11, 0], [7, -3, 11]], 'skipConsecutive', 'skipChords')
    [([<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>], 3), 
    ([<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>], 3)]
    
    '''
    
    segs = []
    donealready = []
    contigdict = {}
    parts = inputStream.getElementsByClass(stream.Part)
    numparts = len(parts)
         
    if numparts == 0:
        for segment in segmentlist:
            used = False
            for usedsegment in donealready:
                segmentrow = pcToToneRow(segment)
                if used == False:
                    if segmentrow.isSameRow(pcToToneRow(usedsegment)) == True:
                        used = True
            if used == False:
                donealready.append(segment)
                length = len(segment)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    contig = getContiguousSegmentsOfLength(inputStream, len(segment), reps, chords)
                    contigdict[length] = contig           
                for contiguousseg in contig:
                    pitchlist = [n.pitchClass for n in contiguousseg[0]]
                    samemod12 = True
                    for j in range(0,length):
                        if samemod12 == True:
                            if pitchlist[j] != segment[j] % 12:
                                samemod12 = False
                    if samemod12 == True:
                        segs.append((contiguousseg[0], contiguousseg[1]))
    else:
        for segment in segmentlist:
            used = False
            for usedsegment in donealready:
                segmentrow = pcToToneRow(segment)
                if used == False:
                    if segmentrow.isSameRow(pcToToneRow(usedsegment)) == True:
                        used = True
            if used == False:
                donealready.append(segment)
                length = len(segment)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    contiglist = []
                    for i in range(0,numparts):
                        part = parts[i]
                        contigforpart = getContiguousSegmentsOfLength(part, length, reps, chords)
                        contiglist.append((contigforpart, i+1))
                    contig = contiglist
                    contigdict[length] = contig
                for partcontiguousseg in contig:
                    for contiguousseg in partcontiguousseg[0]:
                        pitchlist = [n.pitchClass for n in contiguousseg[0]]
                        samemod12 = True
                        for j in range(0,length):
                            if samemod12 == True:
                                if pitchlist[j] != segment[j] % 12:
                                    samemod12 = False
                        if samemod12 == True:
                            segs.append((contiguousseg[0], contiguousseg[1], partcontiguousseg[1]))
                        
    return segs

def findTransposedSegments(inputStream, segmentlist, reps, chords):
    
    '''
    Given a stream object and list of segments of pitch classes (each given as a list), returns a list of all
    instances of the segment and its transpositions in the stream subject to the constraints on repetitions of pitches
    and how chords are dealt with as described in getContinuousSegmentsOfLength. Each
    instance is given as a tuple of the segment of notes, the number of the measure in which it appears, and,
    if the stream object contains parts, the part in which it appears (where a lower number
    denotes a higher part).
    
    >>> from music21 import *
    >>> part = stream.Part()
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 6
    >>> part.append(n1)
    >>> n2 = note.Note('f4')
    >>> n2.quarterLength = 1
    >>> part.append(n2)
    >>> n3 = chord.Chord(['g4', 'b4'])
    >>> n3.quarterLength = 1
    >>> part.append(n3)
    >>> n4 = note.Note('g4')
    >>> n4.quarterLength = 1
    >>> part.repeatAppend(n4, 2)
    >>> n5 = note.Note('a4')
    >>> n5.quarterLength = 3
    >>> part.repeatAppend(n5, 2)
    >>> n6 = note.Note('b4')
    >>> n6.quarterLength = 1
    >>> part.append(n6)
    >>> n7 = note.Note('c5')
    >>> n7.quarterLength = 1
    >>> part.append(n7)
    >>> newpart = part.makeMeasures()
    >>> newpart.makeTies()
    >>> findTransposedSegments(newpart, [[0, 1]], 'skipConsecutive', 'skipChords')
    [([<music21.note.Note E>, <music21.note.Note F>], 1), ([<music21.note.Note B>, <music21.note.Note C>], 5)]
    >>> s = stream.Stream()
    >>> s.repeatAppend(newpart, 2)
    >>> findTransposedSegments(s, [[12, 2]], 'skipConsecutive', 'skipChords')
    [([<music21.note.Note G>, <music21.note.Note A>], 3, 1), ([<music21.note.Note A>, <music21.note.Note B>], 3, 1), 
    ([<music21.note.Note G>, <music21.note.Note A>], 3, 2), ([<music21.note.Note A>, <music21.note.Note B>], 3, 2)]
    
    __OMIT_FROM_DOCS__
    
    >>> findTransposedSegments(newpart, [[0, 1], [12, 13]], 'skipConsecutive', 'skipChords')
    [([<music21.note.Note E>, <music21.note.Note F>], 1), ([<music21.note.Note B>, <music21.note.Note C>], 5)]
    
    '''
    
    
    segs = []
    donealready = []
    contigdict = {}
    parts = inputStream.getElementsByClass(stream.Part)
    numparts = len(parts)
    
    if numparts == 0:
        for segment in segmentlist:
            row = pcToToneRow([n for n in segment])
            intervals = row.getIntervalsAsString()
            if intervals not in donealready:
                donealready.append(intervals)
                length = len(segment)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    contig = getContiguousSegmentsOfLength(inputStream, length, reps, chords)
                    contigdict[length] = contig
                for contiguousseg in contig:
                    if intervals == pcToToneRow([n.pitchClass for n in contiguousseg[0]]).getIntervalsAsString():
                        segs.append((contiguousseg[0], contiguousseg[1]))
    else:
        for segment in segmentlist:
            row = pcToToneRow([n for n in segment])
            intervals = row.getIntervalsAsString()
            if intervals not in donealready:
                donealready.append(intervals)
                length = len(segment)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    contiglist = []
                    for i in range(0,numparts):
                        part = parts[i]
                        contigforpart = getContiguousSegmentsOfLength(part, length, reps, chords)
                        contiglist.append((contigforpart, i+1))
                    contig = contiglist
                    contigdict[length] = contig
                for partcontiguousseg in contig:
                    for contiguousseg in partcontiguousseg[0]:
                        if intervals == pcToToneRow([n.pitchClass for n in contiguousseg[0]]).getIntervalsAsString():
                            segs.append((contiguousseg[0], contiguousseg[1], partcontiguousseg[1]))
            
    return segs


def findTransformedSegments(inputStream, segmentlist, reps, chords, convention):
    '''
    Given a stream object and list of segments of pitch classes (each given as a list), returns a list of all
    instances of the segment and its transformations in the stream subject to the constraints on repetitions of pitches,
    how chords are dealt with as described in getContinuousSegmentsOfLength, and a transformation index convention. 
    Each instance is given as a tuple of the segment of notes, the transformation of the original row,
    the number of the measure in which it appears, and,
    if the stream object contains parts, the part in which it appears (where a lower number
    denotes a higher part).
    
    >>> from music21 import *
    >>> n1 = note.Note('c#4')
    >>> n2 = note.Note('e4')
    >>> n3 = note.Note('d#4')
    >>> n4 = note.Note('f4')
    >>> n5 = note.Note('e4')
    >>> n6 = note.Note('g4')
    >>> notelist = [n1, n2, n3, n4, n5, n6]
    >>> part = stream.Part()
    >>> for n in notelist:
    ...    n.quarterLength = 1
    ...    part.append(n)
    >>> part = part.makeMeasures()
    >>> serial.findTransformedSegments(part, [[2, 5, 4]], 'rowsOnly', 'skipChords', 'zero')
    [([<music21.note.Note C#>, <music21.note.Note E>, <music21.note.Note D#>], [('P', 1)], 1), 
    ([<music21.note.Note F>, <music21.note.Note E>, <music21.note.Note G>], [('RI', 7)], 1)]
    
    
    __OMIT_FROM_DOCS__
    
    >>> s = stream.Stream()
    >>> s.repeatAppend(part, 2)
    >>> serial.findTransformedSegments(s, [[2, -7, 4]], 'skipConsecutive', 'skipChords', 'original')
    [([<music21.note.Note C#>, <music21.note.Note E>, <music21.note.Note D#>], [('P', 11)], 1, 1), 
    ([<music21.note.Note F>, <music21.note.Note E>, <music21.note.Note G>], [('RI', 5)], 1, 1), 
    ([<music21.note.Note C#>, <music21.note.Note E>, <music21.note.Note D#>], [('P', 11)], 1, 2), 
    ([<music21.note.Note F>, <music21.note.Note E>, <music21.note.Note G>], [('RI', 5)], 1, 2)]
    '''
    
    segs = []
    donealready = []
    contigdict = {}
    parts = inputStream.getElementsByClass(stream.Part)
    numparts = len(parts)
    
    if numparts == 0:
        for segment in segmentlist:
            row = pcToToneRow([n for n in segment])
            used = False
            for usedrow in donealready:
                if used == False:
                    if row.findZeroCenteredTransformations != []:
                        used = True
            if used == False:
                donealready.append(segment)
                length = len(segment)
                row = pcToToneRow(segment)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    contig = getContiguousSegmentsOfLength(inputStream, length, reps, chords)
                    contigdict[length] = contig
                if convention == 'zero':
                    for contiguousseg in contig:
                            transformations = row.findZeroCenteredTransformations(pcToToneRow(
                                                    [n.pitchClass for n in contiguousseg[0]]))
                            if transformations != []:
                                segs.append((contiguousseg[0], transformations, contiguousseg[1]))
                elif convention == 'original':
                    for contiguousseg in contig:
                            transformations = row.findOriginalCenteredTransformations(pcToToneRow(
                                                    [n.pitchClass for n in contiguousseg[0]]))
                            if transformations != []:
                                segs.append((contiguousseg[0], transformations, contiguousseg[1]))
                else:
                    raise SerialException("Invalid convention - choose 'zero' or 'original'.")
    
    else:
        for segment in segmentlist:
            row = pcToToneRow([n for n in segment])
            used = False
            for usedrow in donealready:
                if used == False:
                    if row.findZeroCenteredTransformations != []:
                        used = True
            if used == False:
                donealready.append(segment)
                length = len(segment)
                row = pcToToneRow(segment)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    contiglist = []
                    for i in range(0,numparts):
                        part = parts[i]
                        contigforpart = getContiguousSegmentsOfLength(part, length, reps, chords)
                        contiglist.append((contigforpart, i+1))
                    contig = contiglist
                    contigdict[length] = contig
                    if convention == 'zero':
                        for partcontiguousseg in contig:
                            for contiguousseg in partcontiguousseg[0]:
                                transformations = row.findZeroCenteredTransformations(pcToToneRow(
                                                            [n.pitchClass for n in contiguousseg[0]]))
                                if transformations != []:
                                    segs.append((contiguousseg[0], transformations, contiguousseg[1], partcontiguousseg[1]))
                    elif convention == 'original':
                        for partcontiguousseg in contig:
                            for contiguousseg in partcontiguousseg[0]:
                                transformations = row.findOriginalCenteredTransformations(pcToToneRow(
                                                        [n.pitchClass for n in contiguousseg[0]]))
                                if transformations != []:
                                    segs.append((contiguousseg[0], transformations, contiguousseg[1], partcontiguousseg[1]))
                    else:
                        raise SerialException("Invalid convention - choose 'zero' or 'original'.")

    return segs


def _checkMultisetEquivalence(multiset1, multiset2):
    
    from sets import Set
    
    if len(multiset1) != len(multiset2):
        return False
    else:
        
        row1 = pcToToneRow(multiset1)
        multiset1 = row1.pitches()
        
        row2 = pcToToneRow(multiset2)
        multiset2 = row2.pitches()
        
        uniqueelements = Set(multiset1)
        tempsame = True
        for i in uniqueelements:
            if tempsame == True:
                if multiset1.count(i) != multiset2.count(i):
                    tempsame = False
        return tempsame
            


def findMultisets(inputStream, multisetlist, reps, chords):
    
    '''
    
    Given a stream object and list of (unordered) multisets of pitch classes (each given as a list), 
    returns a list of all
    instances of the set in the stream subject to the constraints on repetitions of pitches
    and how chords are dealt with as described in getContinuousSegmentsOfLength. Note that a multiset
    is a generalization of a set in which multiple apperances of the same element (in this case, pitch class) 
    in the multi-set are allowed, hence the use of the list, rather than the set, type. Each
    instance of the multiset is given as a tuple of the segment of notes, the number of the measure in which it appears, and,
    if the stream object contains parts, the part in which it appears (where a lower number
    denotes a higher part).
    
    >>> from music21 import *
    >>> part = stream.Part()
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 4
    >>> n2 = note.Note('f4')
    >>> n2.quarterLength = 4
    >>> part.repeatAppend(n1, 2)
    >>> part.append(n2)
    >>> part.append(n1)
    >>> part = part.makeMeasures()
    >>> findMultisets(part, [[5, 4, 4]], 'includeAll', 'skipChords')
    [([<music21.note.Note E>, <music21.note.Note E>, <music21.note.Note F>], 1), 
    ([<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note E>], 2)]
    
    __OMIT_FROM_DOCS__
    
    >>> s = stream.Stream()
    >>> s.repeatAppend(part, 2)
    >>> findMultisets(part, [[5, 4, 4]], 'rowsOnly', 'skipChords')
    []
    >>> findMultisets(part, [[5, 4, 4]], 'skipConsecutive', 'skipChords')
    [([<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note E>], 1)]
    >>> findMultisets(s, [[-7, 16, 4], [5, 4, 4]], 'includeAll', 'skipChords')
    [([<music21.note.Note E>, <music21.note.Note E>, <music21.note.Note F>], 1, 1), 
    ([<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note E>], 2, 1), 
    ([<music21.note.Note E>, <music21.note.Note E>, <music21.note.Note F>], 1, 2), 
    ([<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note E>], 2, 2)]

    
    '''
    
    multisets = []
    donealready = []
    contigdict = {}
    parts = inputStream.getElementsByClass(stream.Part)
    numparts = len(parts)
    
    if numparts == 0:
        for multiset in multisetlist:
            length = len(multiset)
            used = False
            for usedset in donealready:
                if used == False:
                    if _checkMultisetEquivalence(usedset, multiset) == True:
                        used = True
            if used == False:
                donealready.append(multiset)
                length = len(multiset)
                row = pcToToneRow(multiset)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    contig = getContiguousSegmentsOfLength(inputStream, length, reps, chords)
                    contigdict[length] = contig
                for contiguousseg in contig:
                    pitchmultiset = [n.pitchClass for n in contiguousseg[0]]
                    if _checkMultisetEquivalence(pitchmultiset,multiset) == True:
                        multisets.append((contiguousseg[0], contiguousseg[1]))
    else:
        for multiset in multisetlist:
            length = len(multiset)
            used = False
            for usedset in donealready:
                if used == False:
                    if _checkMultisetEquivalence(usedset, multiset) == True:
                        used = True
            if used == False:
                donealready.append(multiset)
                length = len(multiset)
                row = pcToToneRow(multiset)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    contiglist = []
                    for i in range(0,numparts):
                        part = parts[i]
                        contigforpart = getContiguousSegmentsOfLength(part, length, reps, chords)
                        contiglist.append((contigforpart, i+1))
                    contig = contiglist
                    contigdict[length] = contig
                for partcontiguousseg in contig:
                    for contiguousseg in partcontiguousseg[0]:
                        pitchmultiset = [n.pitchClass for n in contiguousseg[0]]
                        if _checkMultisetEquivalence(pitchmultiset,multiset) == True:
                            multisets.append((contiguousseg[0], contiguousseg[1], partcontiguousseg[1]))

    return multisets

def findTransposedMultisets(inputStream, multisetlist, reps, chords):
    
    '''
    
    Given a stream object and list of (unordered) multisets of pitch classes (each given as a list), 
    returns a list of all
    instances of the set, with its transpositions in the stream subject to the constraints on repetitions of pitches
    and how chords are dealt with as described in getContinuousSegmentsOfLength. Note that a multiset
    is a generalization of a set in which multiple apperances of the same element (in this case, pitch class) 
    in the multi-set are allowed, hence the use of the list, rather than the set, type. Each
    instance of the multiset is given as a tuple of the segment of notes, the number of the measure in which it appears, and,
    if the stream object contains parts, the part in which it appears (where a lower number
    denotes a higher part).
    
    >>> from music21 import *
    >>> part = stream.Part()
    >>> n1 = note.Note('c4')
    >>> n2 = note.Note('c#4')
    >>> n3 = note.Note('d4')
    >>> n4 = note.Note('e4')
    >>> n5 = note.Note('e-4')
    >>> n6 = note.Note('e4')
    >>> n7 = note.Note('d4')
    >>> for n in [n1, n2, n3, n4, n5, n6, n7]:
    ...    n.quarterLength = 2
    ...    part.repeatAppend(n, 2)
    >>> part = part.makeMeasures()
    >>> instancelist = serial.findTransposedMultisets(part, [[1, 2, 3]], 'skipConsecutive', 'skipChords')
    >>> print instancelist
    [([<music21.note.Note D>, <music21.note.Note E>, <music21.note.Note E->], 3),
    ([<music21.note.Note E->, <music21.note.Note E>, <music21.note.Note D>], 5), 
    ([<music21.note.Note C>, <music21.note.Note C#>, <music21.note.Note D>], 1)]
    
    The instances are ordered by transposition, then by measure number: to reorder the list
    one may use Python's built-in list-sorting functions.
    
    >>> sorted(instancelist, key = lambda instance:instance[1])
    [([<music21.note.Note C>, <music21.note.Note C#>, <music21.note.Note D>], 1), 
    ([<music21.note.Note D>, <music21.note.Note E>, <music21.note.Note E->], 3), 
    ([<music21.note.Note E->, <music21.note.Note E>, <music21.note.Note D>], 5)]

        
    '''
    
    transposedmultisets = []
    for multiset in multisetlist:
        for i in range(0,12):
            transposition = []
            for j in multiset:
                transposition.append((j+i) % 12)
            transposedmultisets.append(transposition)
    return findMultisets(inputStream, transposedmultisets, reps, chords)

def findTransposedAndInvertedMultisets(inputStream, multisetlist, reps, chords):
    
    '''
    
    Given a stream object and list of (unordered) multisets of pitch classes (each given as a list), 
    returns a list of all
    instances of the set, with its transpositions and inversions in the stream subject to the constraints on repetitions of pitches
    and how chords are dealt with as described in getContinuousSegmentsOfLength. Note that a multiset
    is a generalization of a set in which multiple apperances of the same element (in this case, pitch class) 
    in the multi-set are allowed, hence the use of the list, rather than the set, type. Each
    instance of the multiset is given as a tuple of the segment of notes, the number of the measure in which it appears, and,
    if the stream object contains parts, the part in which it appears (where a lower number
    denotes a higher part).
    
    >>> from music21 import *
    >>> s = stream.Stream()
    >>> n1 = note.Note('c4')
    >>> n2 = note.Note('e-4')
    >>> n3 = note.Note('g4')
    >>> n4 = note.Note('e4')
    >>> n5 = note.Note('c4')
    >>> for n in [n1, n2, n3, n4, n5]:
    ...     n.quarterLength = 1
    ...     s.append(n)
    >>> s = s.makeMeasures()
    >>> serial.findTransposedAndInvertedMultisets(s, [[0, 4, 7]], 'rowsOnly', 'skipChords')
    [([<music21.note.Note G>, <music21.note.Note E>, <music21.note.Note C>], 1), 
    ([<music21.note.Note C>, <music21.note.Note E->, <music21.note.Note G>], 1)]
    
    __OMIT_FROM_DOCS__
    
    >>> serial.findTransposedAndInvertedMultisets(s, [[0, 4, 7], [0, 3, 7]], 'rowsOnly', 'skipChords')
    [([<music21.note.Note G>, <music21.note.Note E>, <music21.note.Note C>], 1), 
    ([<music21.note.Note C>, <music21.note.Note E->, <music21.note.Note G>], 1)]
    
    '''
    
    
    multisetlistcopy = list(multisetlist)
    for multiset in multisetlistcopy:
        row = pcToToneRow(multiset)
        inversion = row.originalCenteredTransformation('I', 0).pitches()
        multisetlist.append(inversion)
    return findTransposedMultisets(inputStream, multisetlist, reps, chords)
        
            
    
        
    
                
            
        


class HistoricalTwelveToneRow(TwelveToneRow):
    '''
    A 12-tone row used in the historical literature. 
    Added attributes to document the the historical context of the row. 
    '''
    composer = None
    opus = None
    title = None

    _DOC_ATTR = {
    'composer': 'The composers name.',
    'opus': 'The opus of the work, or None.',
    'title': 'The title of the work.',
    }



class RowSchoenbergOp23No5(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 23, No. 5'
    title = 'Five Piano Pieces'
    row = [1, 9, 11, 7, 8, 6, 10, 2, 4, 3, 0, 5]
class RowSchoenbergOp24Mvmt4(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 24'
    title = 'Serenade, Mvt. 4, "Sonett"'
    row = [4, 2, 3, 11, 0, 1, 8, 6, 9, 5, 7, 10]
class RowSchoenbergOp24Mvmt5(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 24'
    title = 'Serenade, Mvt. 5, "Tanzscene"'
    row = [9, 10, 0, 3, 4, 6, 5, 7, 8, 11, 1, 2]
class RowSchoenbergOp25(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op.25'
    title = 'Suite for Piano'
    row = [4, 5, 7, 1, 6, 3, 8, 2, 11, 0, 9, 10]
class RowSchoenbergOp26(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 26'
    title = 'Wind Quintet'
    row = [3, 7, 9, 11, 1, 0, 10, 2, 4, 6, 8, 5]
class RowSchoenbergOp27No1(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 27 No. 1'
    title = 'Four Pieces for Mixed Chorus, No. 1'
    row = [6, 5, 2, 8, 7, 1, 3, 4, 10, 9, 11, 0]
class RowSchoenbergOp27No2(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 27 No. 2'
    title = 'Four Pieces for Mixed Chorus, No. 2'
    row = [0, 11, 4, 10, 2, 8, 3, 7, 6, 5, 9, 1]
class RowSchoenbergOp27No3(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 27 No. 3'
    title = 'Four Pieces for Mixed Chorus, No. 3'
    row = [7, 6, 2, 4, 5, 3, 11, 0, 8, 10, 9, 1]
class RowSchoenbergOp27No4(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 27 No. 4'
    title = 'Four Pieces for Mixed Chorus, No. 4'
    row = [1, 3, 10, 6, 8, 4, 11, 0, 2, 9, 5, 7]
class RowSchoenbergOp28No1(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 28 No. 1'
    title = 'Three Satires for Mixed Chorus, No. 1'
    row = [0, 4, 7, 1, 9, 11, 5, 3, 2, 6, 8, 10]
class RowSchoenbergOp28No3(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 28 No. 3'
    title = 'Three Satires for Mixed Chorus, No. 3'
    row = [5, 6, 4, 8, 2, 10, 7, 9, 3, 11, 1, 0]
class RowSchoenbergOp29(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 29'
    title = 'Suite'
    row = [3, 7, 6, 10, 2, 11, 0, 9, 8, 4, 5, 1]
class RowSchoenbergOp30(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 30'
    title = 'Third String Quartet'
    row = [7, 4, 3, 9, 0, 5, 6, 11, 10, 1, 8, 2]
class RowSchoenbergOp31(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 31'
    title = 'Variations for Orchestra'
    row = [10, 4, 6, 3, 5, 9, 2, 1, 7, 8, 11, 0]
class RowSchoenbergOp32(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 32'
    title = 'Von Heute Auf Morgen'
    row = [2, 3, 9, 1, 11, 5, 8, 7, 4, 0, 10, 6]
class RowSchoenbergOp33A(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 33A'
    title = 'Two Piano Pieces, No. 1'
    row = [10, 5, 0, 11, 9, 6, 1, 3, 7, 8, 2, 4]
class RowSchoenbergOp33B(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 33B'
    title = 'Two Piano Pieces, No. 2'
    row = [11, 1, 5, 3, 9, 8, 6, 10, 7, 4, 0, 2]
class RowSchoenbergOp34(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 34'
    title = 'Accompaniment to a Film Scene'
    row = [3, 6, 2, 4, 1, 0, 9, 11, 10, 8, 5, 7]
class RowSchoenbergOp35No1(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 35'
    title = 'Six Pieces for Male Chorus, No. 1'
    row = [2, 11, 3, 5, 4, 1, 8, 10, 9, 6, 0, 7]
class RowSchoenbergOp35No2(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 35'
    title = 'Six Pieces for Male Chorus, No. 2'
    row = [6, 9, 7, 1, 0, 2, 5, 11, 10, 3, 4, 8]
class RowSchoenbergOp35No3(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 35'
    title = 'Six Pieces for Male Chorus, No. 3'
    row = [3, 6, 7, 8, 5, 0, 9, 10, 4, 11, 2, 1]
class RowSchoenbergOp35No5(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 35'
    title = 'Six Pieces for Male Chorus, No. 5'
    row = [1, 7, 10, 2, 3, 11, 8, 4, 0, 6, 5, 9]
class RowSchoenbergOp36(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 36'
    title = 'Concerto for Violin and Orchestra'
    row = [9, 10, 3, 11, 4, 6, 0, 1, 7, 8, 2, 5]
class RowSchoenbergOp37(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 37'
    title = 'Fourth String Quartet'
    row = [2, 1, 9, 10, 5, 3, 4, 0, 8, 7, 6, 11]
class RowSchoenbergFragPianoPhantasia(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Fragment of Phantasia For Piano'
    row = [1, 5, 3, 6, 4, 8, 0, 11, 2, 9, 10, 7]
class RowSchoenbergFragOrganSonata(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Fragment of Sonata For Organ'
    row = [1, 7, 11, 3, 9, 2, 8, 6, 10, 5, 0, 4]
class RowSchoenbergFragPiano(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Fragment For Piano'
    row = [6, 9, 0, 7, 1, 2, 8, 11, 5, 10, 4, 3]
class RowSchoenbergOp41(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 41'
    title = 'Ode To Napoleon'
    row = [1, 0, 4, 5, 9, 8, 3, 2, 6, 7, 11, 10]
class RowSchoenbergOp42(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 42'
    title = 'Concerto For Piano And Orchestra'
    row = [3, 10, 2, 5, 4, 0, 6, 8, 1, 9, 11, 7]
class RowSchoenbergJakobsleiter(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Die Jakobsleiter'
    row = [1, 2, 5, 4, 8, 7, 0, 3, 11, 10, 6, 9]
class RowSchoenbergOp44(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 44'
    title = 'Prelude To A Suite From "Genesis"'
    row = [10, 6, 2, 5, 4, 0, 11, 8, 1, 3, 9, 7]
class RowSchoenbergOp45(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 45'
    title = 'String Trio'
    row = [2, 10, 3, 9, 4, 1, 11, 8, 6, 7, 5, 0]
class RowSchoenbergOp46(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 46'
    title = 'A Survivor From Warsaw'
    row = [6, 7, 0, 8, 4, 3, 11, 10, 5, 9, 1, 2]
class RowSchoenbergOp47(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 47'
    title = 'Fantasy For Violin And Piano'
    row = [10, 9, 1, 11, 5, 7, 3, 4, 0, 2, 8, 6]
class RowSchoenbergOp48No1(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 48'
    title = 'Three Songs, No. 1, "Sommermud"'
    row = [1, 2, 0, 6, 3, 5, 4, 10, 11, 7, 9, 8]
class RowSchoenbergOp48No2(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 48'
    title = 'Three Songs, No. 2, "Tot"'
    row = [2, 3, 9, 1, 10, 4, 8, 7, 0, 11, 5, 6]
class RowSchoenbergOp48No3(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 48'
    title = 'Three Songs, No, 3, "Madchenlied"'
    row = [1, 7, 9, 11, 3, 5, 10, 6, 4, 0, 8, 2]
class RowSchoenbergIsraelExists(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Israel Exists Again'
    row = [0, 3, 4, 9, 11, 5, 2, 1, 10, 8, 6, 7]
class RowSchoenbergOp50A(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 50A'
    title = 'Three Times A Thousand Years'
    row = [7, 9, 6, 4, 5, 11, 10, 2, 0, 1, 3, 8]
class RowSchoenbergOp50B(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 50B'
    title = 'De Profundis'
    row = [3, 9, 8, 4, 2, 10, 7, 2, 0, 6, 5, 1]
class RowSchoenbergOp50C(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 50C'
    title = 'Modern Psalms, The First Psalm'
    row = [4, 3, 0, 8, 9, 7, 5, 9, 6, 10, 1, 2]
class RowSchoenbergMosesAron(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Moses And Aron'
    row = [9, 10, 4, 2, 3, 1, 7, 5, 6, 8, 11, 0]

# Berg
class RowBergChamberConcerto(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Chamber Concerto'
    row = [11, 7, 5, 9, 2, 3, 6, 8, 0, 1, 4, 10]
class RowBergWozzeckPassacaglia(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Wozzeck, Act I, Scene 4 "Passacaglia"'
    row = [3, 11, 7, 1, 0, 6, 4, 10, 9, 5, 8, 2]
class RowBergLyricSuite(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Lyric Suite Primary Row'
    row = [5, 4, 0, 9, 7, 2, 8, 1, 3, 6, 10, 11]
class RowBergLyricSuitePerm(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Lyric Suite, Last Mvt. Permutation'
    row = [5, 6, 10, 4, 1, 9, 2, 8, 7, 3, 0, 11]
class RowBergDerWein(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Der Wein'
    row = [2, 4, 5, 7, 9, 10, 1, 6, 8, 0, 11, 3]
class RowBergLulu(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Lulu: Primary Row'
    row = [0, 4, 5, 2, 7, 9, 6, 8, 11, 10, 3, 1]
class RowBergLuluActIScene20(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = 'Lulu, Act I , Scene XX'
    title = 'Perm. (Every 7th Note Of Primary Row)'
    row = [10, 6, 3, 8, 5, 11, 4, 2, 9, 0, 1, 7]
class RowBergLuluActIIScene1(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = 'Lulu, Act II, Scene 1'
    title = 'Perm. (Every 5th Note Of Primary Row)'
    row = [4, 10, 7, 1, 0, 9, 2, 11, 5, 8, 3, 6]
    #NOTE: this is wrong! 4 was inserted so that the row could pass the testViennese
class RowBergViolinConcerto(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Concerto For Violin And Orchestra'
    row = [7, 10, 2, 6, 9, 0, 4, 8, 11, 1, 3, 5]

# Webern
class RowWebernOpNo17No1(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. No. 17, No. 1'
    title = '"Armer Sunder, Du"'
    row = [11, 10, 5, 6, 3, 4, 7, 8, 9, 0, 1, 2]
class RowWebernOp17No2(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 17, No. 2'
    title = '"Liebste Jungfrau"'
    row = [1, 0, 11, 7, 8, 2, 3, 6, 5, 4, 9, 10]
class RowWebernOp17No3(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 17, No. 3'
    title = '"Heiland, Unsere Missetaten..."'
    row = [8, 5, 4, 3, 7, 6, 0, 1, 2, 11, 10, 9]
class RowWebernOp18No1(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 18, No. 1'
    title = '"Schatzerl Klein"'
    row = [0, 11, 5, 8, 10, 9, 3, 4, 1, 7, 2, 6]
class RowWebernOp18No2(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 18, No. 2'
    title = '"Erlosung"'
    row = [6, 9, 5, 8, 4, 7, 3, 11, 2, 10, 1, 0]
class RowWebernOp18No3(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 18, No. 3'
    title = '"Ave, Regina Coelorum"'
    row = [4, 3, 7, 6, 5, 11, 10, 2, 1, 0, 9, 8]
class RowWebernOp19No1(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 19, No. 1'
    title = '"Weiss Wie Lilien"'
    row = [7, 10, 6, 5, 3, 9, 8, 1, 2, 11, 4, 0]
class RowWebernOp19No2(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 19, No. 2'
    title = '"Ziehn Die Schafe"'
    row = [8, 4, 9, 6, 7, 0, 11, 5, 3, 2, 10, 1]
class RowWebernOp20(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 20'
    title = 'String Trio'
    row = [8, 7, 2, 1, 6, 5, 9, 10, 3, 4, 0, 11]
class RowWebernOp21(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 21'
    title = 'Chamber Symphony'
    row = [5, 8, 7, 6, 10, 9, 3, 4, 0, 1, 2, 11]
class RowWebernOp22(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 22'
    title = 'Quartet For Violin, Clarinet, Tenor Sax, And Piano'
    row = [6, 3, 2, 5, 4, 8, 9, 10, 11, 1, 7, 0]
class RowWebernOp23(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 23'
    title = 'Three Songs'
    row = [8, 3, 7, 4, 10, 6, 2, 5, 1, 0, 9, 11]
class RowWebernOp24(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 24'
    title = 'Concerto For Nine Instruments'
    row = [11, 10, 2, 3, 7, 6, 8, 4, 5, 0, 1, 9]
class RowWebernOp25(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 25'
    title = 'Three Songs'
    row = [7, 4, 3, 6, 1, 5, 2, 11, 10, 0, 9, 8]
class RowWebernOp26(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 26'
    title = 'Das Augenlicht'
    row = [8, 10, 9, 0, 11, 3, 4, 1, 5, 2, 6, 7]
class RowWebernOp27(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 27'
    title = 'Variations For Piano'
    row = [3, 11, 10, 2, 1, 0, 6, 4, 7, 5, 9, 8]
class RowWebernOp28(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 28'
    title = 'String Quartet'
    row = [1, 0, 3, 2, 6, 7, 4, 5, 9, 8, 11, 10]
class RowWebernOp29(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 29'
    title = 'Cantata I'
    row = [3, 11, 2, 1, 5, 4, 7, 6, 10, 9, 0, 8]
class RowWebernOp30(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 30'
    title = 'Variations For Orchestra'
    row = [9, 10, 1, 0, 11, 2, 3, 6, 5, 4, 7, 8]
class RowWebernOp31(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 31'
    title = 'Cantata II'
    row = [6, 9, 5, 4, 8, 3, 7, 11, 10, 2, 1, 0]



vienneseRows = [RowSchoenbergOp23No5, RowSchoenbergOp24Mvmt4, RowSchoenbergOp24Mvmt5, RowSchoenbergOp25, RowSchoenbergOp26, RowSchoenbergOp27No1, RowSchoenbergOp27No2, RowSchoenbergOp27No3, RowSchoenbergOp27No4, RowSchoenbergOp28No1, RowSchoenbergOp28No3, RowSchoenbergOp29, RowSchoenbergOp30, RowSchoenbergOp31, RowSchoenbergOp32, RowSchoenbergOp33A, RowSchoenbergOp33B, RowSchoenbergOp34, RowSchoenbergOp35No1, RowSchoenbergOp35No2, RowSchoenbergOp35No3, RowSchoenbergOp35No5, RowSchoenbergOp36, RowSchoenbergOp37, RowSchoenbergFragPianoPhantasia, RowSchoenbergFragOrganSonata, RowSchoenbergFragPiano, RowSchoenbergOp41, RowSchoenbergOp42, RowSchoenbergJakobsleiter, RowSchoenbergOp44, RowSchoenbergOp45, RowSchoenbergOp46, RowSchoenbergOp47, RowSchoenbergOp48No1, RowSchoenbergOp48No2, RowSchoenbergOp48No3, RowSchoenbergIsraelExists, RowSchoenbergOp50A, RowSchoenbergOp50B, RowSchoenbergOp50C, RowSchoenbergMosesAron, RowBergChamberConcerto, RowBergWozzeckPassacaglia, RowBergLyricSuite, RowBergLyricSuitePerm, RowBergDerWein, RowBergLulu, RowBergLuluActIScene20, RowBergLuluActIIScene1, RowBergViolinConcerto, RowWebernOpNo17No1, RowWebernOp17No2, RowWebernOp17No3, RowWebernOp18No1, RowWebernOp18No2, RowWebernOp18No3, RowWebernOp19No1, RowWebernOp19No2, RowWebernOp20, RowWebernOp21, RowWebernOp22, RowWebernOp23, RowWebernOp24, RowWebernOp25, RowWebernOp26, RowWebernOp27, RowWebernOp28, RowWebernOp29, RowWebernOp30, RowWebernOp31]



#-------------------------------------------------------------------------------
def pcToToneRow(pcSet):
    '''A convenience function that, given a list of pitch classes represented as integers
    and turns it in to a serial.ToneRow object.

    >>> from music21 import *
    >>> a = serial.pcToToneRow(range(12))
    >>> matrixObj = a.matrix()
    >>> print matrixObj
      0  1  2  3  4  5  6  7  8  9  A  B
      B  0  1  2  3  4  5  6  7  8  9  A
    ...

    >>> a = serial.pcToToneRow([4,5,0,6,7,2,'a',8,9,1,'b',3])
    >>> matrixObj = a.matrix()
    >>> print matrixObj
      0  1  8  2  3  A  6  4  5  9  7  B
      B  0  7  1  2  9  5  3  4  8  6  A
    ...
    
    __OMIT_FROM_DOCS__
    >>> a = serial.pcToToneRow([1,1,1,1,1,1,1,1,1,1,1,1])
    ...
    >>> a = serial.pcToToneRow([3, 4])
    ...
    '''
    
    if len(pcSet) == 12:
        # TODO: check for uniqueness
        a = TwelveToneRow()
        for thisPc in pcSet:
            p = music21.pitch.Pitch()
            p.pitchClass = thisPc
            a.append(p)
        return a
    else:
        a = ToneRow()
        for thisPc in pcSet:
            p = music21.pitch.Pitch()
            p.pitchClass = thisPc
            a.append(p)
        return a
           #raise SerialException("pcToToneRow requires a 12-tone-row")
    
def rowToMatrix(p):
    '''
    takes a row of numbers of converts it to a 12-tone matrix.
    '''
    
    i = [(12-x) % 12 for x in p]
    matrix = [[(x+t) % 12 for x in p] for t in i]

    ret = ""
    for row in matrix:
        msg = []
        for pitch in row:
            msg.append(str(pitch).rjust(3))
        ret += ''.join(msg) + "\n"

    return ret









#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testRows(self):
        from music21 import interval

        self.assertEqual(len(vienneseRows), 71)

        totalRows = 0
        cRows = 0
        for thisRow in vienneseRows:
            thisRow = thisRow() 
            self.assertEqual(isinstance(thisRow, TwelveToneRow), True)
            
            if thisRow.composer == "Berg":
                continue
            post = thisRow.title
            
            totalRows += 1
            if thisRow[0].pitchClass == 0:
                cRows += 1
            
#             if interval.notesToInterval(thisRow[0], 
#                                    thisRow[6]).intervalClass == 6:
#              # between element 1 and element 7 is there a TriTone?
#              rowsWithTTRelations += 1


    def testMatrix(self):

        src = RowSchoenbergOp37()
        self.assertEqual([p.name for p in src], 
            ['D', 'C#', 'A', 'B-', 'F', 'E-', 'E', 'C', 'G#', 'G', 'F#', 'B'])
        s37 = RowSchoenbergOp37().matrix()
        self.assertEqual([e.name for e in s37[0]], ['C', 'B', 'G', 'G#', 'E-', 'C#', 'D', 'B-', 'F#', 'F', 'E', 'A'])


    def testLabelingA(self):

        from music21 import corpus, stream, pitch
        series = {'a':1, 'g-':2, 'g':3, 'a-':4, 
                  'f':5, 'e-':6, 'e':7, 'd':8, 
                  'c':9, 'c#':10, 'b-':11, 'b':12}
        s = corpus.parse('bwv66.6')
        for n in s.flat.notes:
            for key in series.keys():
                if n.pitch.pitchClass == pitch.Pitch(key).pitchClass:
                    n.addLyric(series[key])
        match = []
        for n in s.parts[0].flat.notes:
            match.append(n.lyric)
        self.assertEqual(match, ['10', '12', '1', '12', '10', '7', '10', '12', '1', '10', '1', '12', '4', '2', '1', '12', '12', '2', '7', '1', '12', '10', '10', '1', '12', '10', '1', '4', '2', '4', '2', '2', '2', '2', '2', '5', '2'])
        #s.show()
    
    def testViennese(self):
        
        nonRows = []
        for historicalRow in vienneseRows:
            if pcToToneRow(historicalRow.row).isTwelveToneRow() == False:
                nonRows.append(historicalRow)
                self.assertEqual(nonRows, [])

                
        
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = ['ToneRow', 'TwelveToneRow', 'pcToToneRow', 'TwelveToneMatrix', 'rowToMatrix', 'getContiguousSegmentsOfLength', 'findSegments',
              'findTransposedSegments', 'findTransformedSegments', 'findMultisets', 'findTransposedMultisets', 
              'findTransposedAndInvertedMultisets']

if __name__ == "__main__":
    music21.mainTest(Test)

#     import sys
#     if len(sys.argv) == 1: # normal conditions
#         music21.mainTest(Test)
# 
#     elif len(sys.argv) > 1:
#         t = Test()
# 
#         t.testMatrix()

#------------------------------------------------------------------------------
# eof

