# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         serial.py
# Purpose:      music21 classes for serial transformations
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               Carl Lian
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
This module defines objects for defining and manipulating structures 
common to serial and/or twelve-tone music, 
including :class:`~music21.serial.ToneRow` subclasses.
'''

import unittest
import copy

from music21 import exceptions21

from music21 import base
from music21 import note
from music21 import chord
from music21 import stream
from music21 import pitch
from music21 import spanner

from music21 import environment

_MOD = 'serial.py'
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class SerialException(exceptions21.Music21Exception):
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

    OMIT_FROM_DOCS

    
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
            for n in rowForm:
                msg.append(str(n.pitch.pitchClassString).rjust(3))
            ret += ''.join(msg) + "\n"
        return ret

    def __repr__(self):
        if self:
            if isinstance(self[0], ToneRow):
                return '<music21.serial.TwelveToneMatrix for [%s]>' % self[0]
            else:
                return stream.Stream.__repr__(self)
        else:
            return stream.Stream.__repr__(self)
#-------------------------------------------------------------------------------

historicalDict = {
      'RowWebernOp29': ('Webern', 'Op. 29', 'Cantata I', [3, 11, 2, 1, 5, 4, 7, 6, 10, 9, 0, 8]), 
      'RowWebernOp28': ('Webern', 'Op. 28', 'String Quartet', [1, 0, 3, 2, 6, 7, 4, 5, 9, 8, 11, 10]), 
      'RowSchoenbergOp24Mvmt5': ('Schoenberg', 'Op. 24', 'Serenade, Mvt. 5, "Tanzscene"', [9, 10, 0, 3, 4, 6, 5, 7, 8, 11, 1, 2]), 
      'RowSchoenbergOp24Mvmt4': ('Schoenberg', 'Op. 24', 'Serenade, Mvt. 4, "Sonett"', [4, 2, 3, 11, 0, 1, 8, 6, 9, 5, 7, 10]), 
      'RowSchoenbergJakobsleiter': ('Schoenberg', None, 'Die Jakobsleiter', [1, 2, 5, 4, 8, 7, 0, 3, 11, 10, 6, 9]), 
      'RowSchoenbergOp27No4': ('Schoenberg', 'Op. 27 No. 4', 'Four Pieces for Mixed Chorus, No. 4', [1, 3, 10, 6, 8, 4, 11, 0, 2, 9, 5, 7]), 
      'RowWebernOp23': ('Webern', 'Op. 23', 'Three Songs', [8, 3, 7, 4, 10, 6, 2, 5, 1, 0, 9, 11]), 
      'RowBergLuluActIIScene1': ('Berg', 'Lulu, Act II, Scene 1', 'Perm. (Every 5th Note Of Transposed Primary Row)', [10, 7, 1, 0, 9, 2, 4, 11, 5, 8, 3, 6]), 
      'RowSchoenbergOp27No1': ('Schoenberg', 'Op. 27 No. 1', 'Four Pieces for Mixed Chorus, No. 1', [6, 5, 2, 8, 7, 1, 3, 4, 10, 9, 11, 0]), 
      'RowBergLuluActIScene20': ('Berg', 'Lulu, Act I , Scene XX', 'Perm. (Every 7th Note Of Transposed Primary Row)', [10, 6, 3, 8, 5, 11, 4, 2, 9, 0, 1, 7]), 
      'RowSchoenbergOp27No3': ('Schoenberg', 'Op. 27 No. 3', 'Four Pieces for Mixed Chorus, No. 3', [7, 6, 2, 4, 5, 3, 11, 0, 8, 10, 9, 1]), 
      'RowSchoenbergOp27No2': ('Schoenberg', 'Op. 27 No. 2', 'Four Pieces for Mixed Chorus, No. 2', [0, 11, 4, 10, 2, 8, 3, 7, 6, 5, 9, 1]), 
      'RowSchoenbergFragPiano': ('Schoenberg', None, 'Fragment For Piano', [6, 9, 0, 7, 1, 2, 8, 11, 5, 10, 4, 3]), 
      'RowSchoenbergOp50B': ('Schoenberg', 'Op. 50B', 'De Profundis', [3, 9, 8, 4, 2, 10, 7, 11, 0, 6, 5, 1]), 
      'RowSchoenbergOp50C': ('Schoenberg', 'Op. 50C', 'Modern Psalms, The First Psalm', [4, 3, 0, 8, 11, 7, 5, 9, 6, 10, 1, 2]), 
      'RowSchoenbergOp50A': ('Schoenberg', 'Op. 50A', 'Three Times A Thousand Years', [7, 9, 6, 4, 5, 11, 10, 2, 0, 1, 3, 8]), 
      'RowSchoenbergMosesAron': ('Schoenberg', None, 'Moses And Aron', [9, 10, 4, 2, 3, 1, 7, 5, 6, 8, 11, 0]), 
      'RowWebernOp25': ('Webern', 'Op. 25', 'Three Songs', [7, 4, 3, 6, 1, 5, 2, 11, 10, 0, 9, 8]), 
      'RowSchoenbergOp23No5': ('Schoenberg', 'Op. 23, No. 5', 'Five Piano Pieces', [1, 9, 11, 7, 8, 6, 10, 2, 4, 3, 0, 5]), 
      'RowSchoenbergOp28No1': ('Schoenberg', 'Op. 28 No. 1', 'Three Satires for Mixed Chorus, No. 1', [0, 4, 7, 1, 9, 11, 5, 3, 2, 6, 8, 10]), 
      'RowSchoenbergOp28No3': ('Schoenberg', 'Op. 28 No. 3', 'Three Satires for Mixed Chorus, No. 3', [5, 6, 4, 8, 2, 10, 7, 9, 3, 11, 1, 0]), 
      'RowWebernOp21': ('Webern', 'Op. 21', 'Chamber Symphony', [5, 8, 7, 6, 10, 9, 3, 4, 0, 1, 2, 11]), 
      'RowSchoenbergIsraelExists': ('Schoenberg', None, 'Israel Exists Again', [0, 3, 4, 9, 11, 5, 2, 1, 10, 8, 6, 7]), 
      'RowSchoenbergOp35No2': ('Schoenberg', 'Op. 35', 'Six Pieces for Male Chorus, No. 2', [6, 9, 7, 1, 0, 2, 5, 11, 10, 3, 4, 8]), 
      'RowSchoenbergOp35No3': ('Schoenberg', 'Op. 35', 'Six Pieces for Male Chorus, No. 3', [3, 6, 7, 8, 5, 0, 9, 10, 4, 11, 2, 1]), 
      'RowSchoenbergOp35No1': ('Schoenberg', 'Op. 35', 'Six Pieces for Male Chorus, No. 1', [2, 11, 3, 5, 4, 1, 8, 10, 9, 6, 0, 7]), 
      'RowSchoenbergOp48No1': ('Schoenberg', 'Op. 48', 'Three Songs, No. 1, "Sommermud"', [1, 2, 0, 6, 3, 5, 4, 10, 11, 7, 9, 8]), 
      'RowSchoenbergOp35No5': ('Schoenberg', 'Op. 35', 'Six Pieces for Male Chorus, No. 5', [1, 7, 10, 2, 3, 11, 8, 4, 0, 6, 5, 9]), 
      'RowSchoenbergOp29': ('Schoenberg', 'Op. 29', 'Suite', [3, 7, 6, 10, 2, 11, 0, 9, 8, 4, 5, 1]), 
      'RowBergLyricSuitePerm': ('Berg', None, 'Lyric Suite, Last Mvt. Permutation', [5, 6, 10, 4, 1, 9, 2, 8, 7, 3, 0, 11]), 
      'RowWebernOp20': ('Webern', 'Op. 20', 'String Trio', [8, 7, 2, 1, 6, 5, 9, 10, 3, 4, 0, 11]), 
      'RowSchoenbergOp46': ('Schoenberg', 'Op. 46', 'A Survivor From Warsaw', [6, 7, 0, 8, 4, 3, 11, 10, 5, 9, 1, 2]), 
      'RowSchoenbergFragOrganSonata': ('Schoenberg', None, 'Fragment of Sonata For Organ', [1, 7, 11, 3, 9, 2, 8, 6, 10, 5, 0, 4]), 
      'RowSchoenbergOp44': ('Schoenberg', 'Op. 44', 'Prelude To A Suite From "Genesis"', [10, 6, 2, 5, 4, 0, 11, 8, 1, 3, 9, 7]), 
      'RowSchoenbergOp45': ('Schoenberg', 'Op. 45', 'String Trio', [2, 10, 3, 9, 4, 1, 11, 8, 6, 7, 5, 0]), 
      'RowSchoenbergOp33A': ('Schoenberg', 'Op. 33A', 'Two Piano Pieces, No. 1', [10, 5, 0, 11, 9, 6, 1, 3, 7, 8, 2, 4]), 
      'RowSchoenbergOp25': ('Schoenberg', 'Op.25', 'Suite for Piano', [4, 5, 7, 1, 6, 3, 8, 2, 11, 0, 9, 10]), 
      'RowSchoenbergOp26': ('Schoenberg', 'Op. 26', 'Wind Quintet', [3, 7, 9, 11, 1, 0, 10, 2, 4, 6, 8, 5]), 
      'RowSchoenbergOp33B': ('Schoenberg', 'Op. 33B', 'Two Piano Pieces, No. 2', [11, 1, 5, 3, 9, 8, 6, 10, 7, 4, 0, 2]), 
      'RowBergViolinConcerto': ('Berg', None, 'Concerto For Violin And Orchestra', [7, 10, 2, 6, 9, 0, 4, 8, 11, 1, 3, 5]), 
      'RowWebernOp22': ('Webern', 'Op. 22', 'Quartet For Violin, Clarinet, Tenor Sax, And Piano', [6, 3, 2, 5, 4, 8, 9, 10, 11, 1, 7, 0]), 
      'RowBergLulu': ('Berg', None, 'Lulu: Primary Row', [0, 4, 5, 2, 7, 9, 6, 8, 11, 10, 3, 1]), 
      'RowWebernOp30': ('Webern', 'Op. 30', 'Variations For Orchestra', [9, 10, 1, 0, 11, 2, 3, 6, 5, 4, 7, 8]), 
      'RowWebernOp31': ('Webern', 'Op. 31', 'Cantata II', [6, 9, 5, 4, 8, 3, 7, 11, 10, 2, 1, 0]), 
      'RowWebernOpNo17No1': ('Webern', 'Op. 17, No. 1', '"Armer Sunder, Du"', [11, 10, 5, 6, 3, 4, 7, 8, 9, 0, 1, 2]), 
      'RowWebernOp24': ('Webern', 'Op. 24', 'Concerto For Nine Instruments', [11, 10, 2, 3, 7, 6, 8, 4, 5, 0, 1, 9]), 
      'RowSchoenbergOp48No2': ('Schoenberg', 'Op. 48', 'Three Songs, No. 2, "Tot"', [2, 3, 9, 1, 10, 4, 8, 7, 0, 11, 5, 6]), 
      'RowWebernOp27': ('Webern', 'Op. 27', 'Variations For Piano', [3, 11, 10, 2, 1, 0, 6, 4, 7, 5, 9, 8]), 
      'RowSchoenbergOp47': ('Schoenberg', 'Op. 47', 'Fantasy For Violin And Piano', [10, 9, 1, 11, 5, 7, 3, 4, 0, 2, 8, 6]), 
      'RowWebernOp19No2': ('Webern', 'Op. 19, No. 2', '"Ziehn Die Schafe"', [8, 4, 9, 6, 7, 0, 11, 5, 3, 2, 10, 1]), 
      'RowWebernOp19No1': ('Webern', 'Op. 19, No. 1', '"Weiss Wie Lilien"', [7, 10, 6, 5, 3, 9, 8, 1, 2, 11, 4, 0]), 
      'RowWebernOp26': ('Webern', 'Op. 26', 'Das Augenlicht', [8, 10, 9, 0, 11, 3, 4, 1, 5, 2, 6, 7]), 
      'RowSchoenbergFragPianoPhantasia': ('Schoenberg', None, 'Fragment of Phantasia For Piano', [1, 5, 3, 6, 4, 8, 0, 11, 2, 9, 10, 7]), 
      'RowBergDerWein': ('Berg', None, 'Der Wein', [2, 4, 5, 7, 9, 10, 1, 6, 8, 0, 11, 3]), 
      'RowBergWozzeckPassacaglia': ('Berg', None, 'Wozzeck, Act I, Scene 4 "Passacaglia"', [3, 11, 7, 1, 0, 6, 4, 10, 9, 5, 8, 2]), 
      'RowWebernOp18No1': ('Webern', 'Op. 18, No. 1', '"Schatzerl Klein"', [0, 11, 5, 8, 10, 9, 3, 4, 1, 7, 2, 6]), 
      'RowWebernOp18No2': ('Webern', 'Op. 18, No. 2', '"Erlosung"', [6, 9, 5, 8, 4, 7, 3, 11, 2, 10, 1, 0]), 
      'RowWebernOp18No3': ('Webern', 'Op. 18, No. 3', '"Ave, Regina Coelorum"', [4, 3, 7, 6, 5, 11, 10, 2, 1, 0, 9, 8]), 
      'RowSchoenbergOp42': ('Schoenberg', 'Op. 42', 'Concerto For Piano And Orchestra', [3, 10, 2, 5, 4, 0, 6, 8, 1, 9, 11, 7]), 
      'RowSchoenbergOp48No3': ('Schoenberg', 'Op. 48', 'Three Songs, No, 3, "Madchenlied"', [1, 7, 9, 11, 3, 5, 10, 6, 4, 0, 8, 2]), 
      'RowSchoenbergOp37': ('Schoenberg', 'Op. 37', 'Fourth String Quartet', [2, 1, 9, 10, 5, 3, 4, 0, 8, 7, 6, 11]), 
      'RowSchoenbergOp36': ('Schoenberg', 'Op. 36', 'Concerto for Violin and Orchestra', [9, 10, 3, 11, 4, 6, 0, 1, 7, 8, 2, 5]), 
      'RowSchoenbergOp34': ('Schoenberg', 'Op. 34', 'Accompaniment to a Film Scene', [3, 6, 2, 4, 1, 0, 9, 11, 10, 8, 5, 7]), 
      'RowBergChamberConcerto': ('Berg', None, 'Chamber Concerto', [11, 7, 5, 9, 2, 3, 6, 8, 0, 1, 4, 10]), 
      'RowSchoenbergOp32': ('Schoenberg', 'Op. 32', 'Von Heute Auf Morgen', [2, 3, 9, 1, 11, 5, 8, 7, 4, 0, 10, 6]), 
      'RowSchoenbergOp31': ('Schoenberg', 'Op. 31', 'Variations for Orchestra', [10, 4, 6, 3, 5, 9, 2, 1, 7, 8, 11, 0]), 
      'RowSchoenbergOp30': ('Schoenberg', 'Op. 30', 'Third String Quartet', [7, 4, 3, 9, 0, 5, 6, 11, 10, 1, 8, 2]), 
      'RowBergLyricSuite': ('Berg', None, 'Lyric Suite Primary Row', [5, 4, 0, 9, 7, 2, 8, 1, 3, 6, 10, 11]), 
      'RowSchoenbergOp41': ('Schoenberg', 'Op. 41', 'Ode To Napoleon', [1, 0, 4, 5, 9, 8, 3, 2, 6, 7, 11, 10]), 
      'RowWebernOp17No3': ('Webern', 'Op. 17, No. 3', '"Heiland, Unsere Missetaten..."', [8, 5, 4, 3, 7, 6, 0, 1, 2, 11, 10, 9]), 
      'RowWebernOp17No2': ('Webern', 'Op. 17, No. 2', '"Liebste Jungfrau"', [1, 0, 11, 7, 8, 2, 3, 6, 5, 4, 9, 10])
      }

#-------------------------------------------------------------------------------
class ToneRow(stream.Stream):
    '''
    A Stream representation of a tone row, or an ordered sequence of pitches; 
    can most importantly be used to deal with
    serial transformations. 
    '''
    
    row = None

    _DOC_ATTR = {
    'row': 'A list representing the pitch class values of the row.',
    }
    
    _DOC_ORDER = ['pitchClasses', 'noteNames', 'isTwelveToneRow', 'isSameRow', 
                  'getIntervalsAsString', 
                  'zeroCenteredTransformation', 'originalCenteredTransformation',
                  'findZeroCenteredTransformations', 'findOriginalCenteredTransformations']
    
    def __init__(self):
        stream.Stream.__init__(self)
        
        if self.row != None:
            for pc in self.row:
                n = note.Note()
                n.pitch = pitch.Pitch(pc)
                n.pitch.octave = None
                self.append(n)
    
        
    def pitchClasses(self):
        '''
        Convenience function showing the pitch classes of a 
        :class:`~music21.serial.ToneRow` as a list.  
        
        >>> L = [5*i for i in range(0,12)]
        >>> quintupleRow = serial.pcToToneRow(L)
        >>> quintupleRow.pitchClasses()
        [0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7]
        >>> halfStep = serial.pcToToneRow([0, 1])
        >>> halfStep.pitchClasses()
        [0, 1] 
        '''
        
        pitchlist = [n.pitch.pitchClass for n in self]
        return pitchlist
    
    def noteNames(self):
        '''
        Convenience function showing the note names of a 
        :class:`~music21.serial.ToneRow` as a list.
        
        
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
        Describes whether or not a :class:`~music21.serial.ToneRow` constitutes a twelve-tone row. Note that a
        :class:`~music21.serial.TwelveToneRow` object might not be a twelve-tone row.
        
        
        >>> serial.pcToToneRow(range(0,12)).isTwelveToneRow()
        True
        >>> serial.pcToToneRow(range(0,10)).isTwelveToneRow()
        False
        >>> serial.pcToToneRow([3,3,3,3,3,3,3,3,3,3,3,3]).isTwelveToneRow()
        False
        
        '''
        
        pitchList = self.pitchClasses()
        if len(pitchList) != 12:
            return False
        else:
            temp = True
            for i in range(0,12):
                if i not in pitchList:
                    temp = False
            return temp
    
    def makeTwelveToneRow(self):
        '''
        Convenience function returning a :class:`~music21.serial.TwelveToneRow` with the same pitches.
        Note that a :class:`~music21.serial.ToneRow` may be created without being a true twelve tone row.
        
        
        >>> a = serial.pcToToneRow(range(0,11))
        >>> type(a)
        <class 'music21.serial.ToneRow'>
        >>> n = note.Note()
        >>> n.pitch.pitchClass = 11
        >>> a.append(n)
        >>> a = a.makeTwelveToneRow()
        ...
        >>> type(a)
        <class 'music21.serial.TwelveToneRow'>
        '''
        pcSet = self.pitchClasses()
        a = TwelveToneRow()
        for thisPc in pcSet:
            n = note.Note()
            n.duration.quarterLength = 0.0
            n.pitch.pitchClass = thisPc
            n.pitch.octave = None
            a.append(n)
        return a

    def isSameRow(self, row):
        '''
        Convenience function describing if two rows are the same.
        
        
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
                    if self[i].pitch.pitchClass != row[i].pitch.pitchClass:
                        tempsame = False
        
        return tempsame
    
    def getIntervalsAsString(self):
        '''
        
        Returns the string of intervals between consecutive pitch classes of a :class:`~music21.serial.ToneRow`.
        'T' = 10, 'E' = 11.
        
        >>> cRow = serial.pcToToneRow([0])
        >>> cRow.getIntervalsAsString()
        ''
        >>> reversechromatic = serial.pcToToneRow([11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0])
        >>> reversechromatic.getIntervalsAsString()
        'EEEEEEEEEEE'
        '''
        
        numPitches = len(self)
        pitchList = self.pitchClasses()
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
        Returns a :class:`~music21.serial.ToneRow` giving a transformation of a tone row.
        Admissible transformationTypes are 'P' (prime), 'I' (inversion),
        'R' (retrograde), and 'RI' (retrograde inversion).
        
        In the "zero-centered" convention, 
        the transformations Pn and In start on the pitch class n, and the transformations
        Rn and RIn end on the pitch class n.
       
        
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.pitchClasses()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        >>> chromaticP3 = chromatic.zeroCenteredTransformation('P',3)
        >>> chromaticP3.pitchClasses()
        [3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2]
        >>> chromaticI6 = chromatic.zeroCenteredTransformation('I',6)
        >>> chromaticI6.pitchClasses()
        [6, 5, 4, 3, 2, 1, 0, 11, 10, 9, 8, 7]
        >>> schoenberg = serial.getHistoricalRowByName('RowSchoenbergOp26')
        >>> schoenberg.pitchClasses()
        [3, 7, 9, 11, 1, 0, 10, 2, 4, 6, 8, 5]
        >>> schoenbergR8 = schoenberg.zeroCenteredTransformation('R',8)
        >>> schoenbergR8.pitchClasses()
        [10, 1, 11, 9, 7, 3, 5, 6, 4, 2, 0, 8]
        >>> schoenbergRI9 = schoenberg.zeroCenteredTransformation('RI',9)
        >>> schoenbergRI9.noteNames()
        ['G', 'E', 'F#', 'G#', 'B-', 'D', 'C', 'B', 'C#', 'E-', 'F', 'A']
        
        '''
            
        numPitches = len(self)
        pitchList = self.pitchClasses()
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
        Returns a :class:`~music21.serial.ToneRow` giving a transformation of a tone row.
        Admissible transformations are 'T' (transposition), 'I' (inversion),
        'R' (retrograde), and 'RI' (retrograde inversion).
        
        In the "original-centered" convention,
        which is less common than the "zero-centered" convention, the original row is not initially
        transposed to start on the pitch class 0. Thus, the transformation Tn transposes
        the original row up by n semitones, and the transformations In, Rn, and RIn first
        transform the row appropriately (without transposition), then transpose the resulting
        row by n semitones.
       
        
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.pitchClasses()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        >>> chromaticP3 = chromatic.originalCenteredTransformation('T',3)
        >>> chromaticP3.pitchClasses()
        [3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2]
        >>> chromaticI6 = chromatic.originalCenteredTransformation('I',6)
        >>> chromaticI6.pitchClasses()
        [6, 5, 4, 3, 2, 1, 0, 11, 10, 9, 8, 7]
        >>> schoenberg = serial.getHistoricalRowByName('RowSchoenbergOp26')
        >>> schoenberg.pitchClasses()
        [3, 7, 9, 11, 1, 0, 10, 2, 4, 6, 8, 5]
        >>> schoenbergR8 = schoenberg.originalCenteredTransformation('R',8)
        >>> schoenbergR8.pitchClasses()
        [1, 4, 2, 0, 10, 6, 8, 9, 7, 5, 3, 11]
        >>> schoenbergRI9 = schoenberg.originalCenteredTransformation('RI',9)
        >>> schoenbergRI9.noteNames()
        ['B-', 'G', 'A', 'B', 'C#', 'F', 'E-', 'D', 'E', 'F#', 'G#', 'C']
        
        '''
        
        pitchList = self.pitchClasses()
        firstPitch = pitchList[0]
        newIndex = (firstPitch + index) % 12
        if transformationType == 'T':
            return self.zeroCenteredTransformation('P', newIndex)
        if transformationType == 'P':
            raise SerialException("Invalid Transformation Type.")
        else:
            return self.zeroCenteredTransformation(transformationType, newIndex)
        
    
    def findZeroCenteredTransformations(self, otherRow):
        ''' 
        Gives the list of zero-centered serial transformations taking one :class:`~music21.serial.ToneRow`
        to another, the second specified in the argument. Each transformation is given as a
        tuple of the transformation type and index.
        
        See :meth:`~music21.serial.zeroCenteredTransformation` for an explanation of this convention.
        
        
        >>> chromatic = serial.pcToToneRow([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1])
        >>> reversechromatic = serial.pcToToneRow([8, 7, 6, 5, 4, 3, 2, 1, 0, 11, 10, 9])
        >>> chromatic.findZeroCenteredTransformations(reversechromatic)
        [('I', 8), ('R', 9)]
        >>> schoenberg25 = serial.getHistoricalRowByName('RowSchoenbergOp25')
        >>> schoenberg26 = serial.pcToToneRow(serial.getHistoricalRowByName('RowSchoenbergOp26').row)
        >>> schoenberg25.findZeroCenteredTransformations(schoenberg26)
        []
        >>> schoenberg26.findZeroCenteredTransformations(schoenberg26.zeroCenteredTransformation('RI',8))
        [('RI', 8)]
        
        '''
        if len(self) != len(otherRow):
            return False
        else:
            otherRowPitches = otherRow.pitchClasses()
            transformationList = []
            firstPitch = otherRowPitches[0]
            lastPitch = otherRowPitches[-1]
            
            if otherRowPitches == self.zeroCenteredTransformation('P',firstPitch).pitchClasses():
                transformation = 'P', firstPitch
                transformationList.append(transformation)
            if otherRowPitches == self.zeroCenteredTransformation('I',firstPitch).pitchClasses():
                transformation = 'I', firstPitch
                transformationList.append(transformation)
            if otherRowPitches == self.zeroCenteredTransformation('R',lastPitch).pitchClasses():
                transformation  = 'R', lastPitch
                transformationList.append(transformation)
            if otherRowPitches == self.zeroCenteredTransformation('RI',lastPitch).pitchClasses():
                transformation = 'RI', lastPitch
                transformationList.append(transformation)
                
            return transformationList
        
    def findOriginalCenteredTransformations(self, otherRow):
        ''' 
        Gives the list of original-centered serial transformations taking one :class:`~music21.serial.ToneRow`
        to another, the second specified in the argument. Each transformation is given as a tuple
        of the transformation type and index.
        
        See :meth:`~music21.serial.originalCenteredTransformation` for an explanation of this convention.
        
        
        >>> chromatic = serial.pcToToneRow([2, 3, 4, 5, 6, 7, 8, 9, 'A', 'B', 0, 1])
        >>> reversechromatic = serial.pcToToneRow([8, 7, 6, 5, 4, 3, 2, 1, 0, 'B', 'A', 9])
        >>> chromatic.findOriginalCenteredTransformations(reversechromatic)
        [('I', 6), ('R', 7)]
        >>> schoenberg25 = serial.getHistoricalRowByName('RowSchoenbergOp25')
        >>> schoenberg26 = serial.getHistoricalRowByName('RowSchoenbergOp26')
        >>> schoenberg25.findOriginalCenteredTransformations(schoenberg26)
        []
        >>> schoenberg26.findOriginalCenteredTransformations(schoenberg26.originalCenteredTransformation('RI',8))
        [('RI', 8)]
        
        '''
        
        originalRowPitches = self.pitchClasses()
        otherRowPitches = otherRow.pitchClasses()
        transformationList = []
        oldFirstPitch = originalRowPitches[0]
        oldLastPitch = originalRowPitches [-1]
        newFirstPitch = otherRowPitches[0]
        
        if otherRowPitches == self.originalCenteredTransformation('T',(newFirstPitch - oldFirstPitch) % 12).pitchClasses():
            transformation = 'T', (newFirstPitch - oldFirstPitch) % 12
            transformationList.append(transformation)
        if otherRowPitches == self.originalCenteredTransformation('I',(newFirstPitch - oldFirstPitch) % 12).pitchClasses():
            transformation = 'I', (newFirstPitch - oldFirstPitch) % 12
            transformationList.append(transformation)
        if otherRowPitches == self.originalCenteredTransformation('R',(newFirstPitch - oldLastPitch) % 12).pitchClasses():
            transformation  = 'R', (newFirstPitch - oldLastPitch) % 12
            transformationList.append(transformation)
        if otherRowPitches == self.originalCenteredTransformation('RI',(newFirstPitch - 2*oldFirstPitch + oldLastPitch) % 12).pitchClasses():
            transformation = 'RI', (newFirstPitch - 2*oldFirstPitch + oldLastPitch) % 12
            transformationList.append(transformation)
            
        return transformationList
    

# ----------------------------------------------------------------------------------------

class TwelveToneRow(ToneRow):
    '''
    A Stream representation of a twelve-tone row, capable of producing a 12-tone matrix.
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
        Returns a :class:`~music21.serial.TwelveToneMatrix` object for the row.  
        That object can just be printed (or displayed via .show())
        
        >>> src = serial.getHistoricalRowByName('RowSchoenbergOp37')
        >>> [p.name for p in src]
        ['D', 'C#', 'A', 'B-', 'F', 'E-', 'E', 'C', 'G#', 'G', 'F#', 'B']
        >>> len(src)
        12
        >>> s37 = serial.getHistoricalRowByName('RowSchoenbergOp37').matrix()
        >>> print(s37)
          0  B  7  8  3  1  2  A  6  5  4  9
          1  0  8  9  4  2  3  B  7  6  5  A
          5  4  0  1  8  6  7  3  B  A  9  2
          4  3  B  0  7  5  6  2  A  9  8  1
        ...
        >>> [str(e.pitch) for e in s37[0]]
        ['C', 'B', 'G', 'G#', 'E-', 'C#', 'D', 'B-', 'F#', 'F', 'E', 'A']

        
        '''        
        # note: do not want to return a TwelveToneRow() type, as this will
        # add again the same pitches to the elements list twice. 
        noteList = self.getElementsByClass('Note', returnStreamSubClass='list')

        i = [(12-x.pitch.pitchClass) % 12 for x in noteList]
        matrix = [[(x.pitch.pitchClass+t) % 12 for x in noteList] for t in i]

        matrixObj = TwelveToneMatrix()
        i = 0
        for row in matrix:
            i += 1
            rowObject = copy.copy(self)
            rowObject.elements = []
            rowObject.id = 'row-' + str(i)
            for p in row: # iterate over pitch class values
                n = note.Note()
                n.duration.quarterLength = 0.0
                n.pitch.pitchClass = p
                n.pitch.octave = None
                rowObject.append(n)
            matrixObj.insert(0, rowObject)
        

        #environLocal.printDebug(['calling matrix start: len row:', self.row, 'len self', len(self)])

        return matrixObj
    
    def findHistorical(self):
        '''
        Checks if a given :class:`music21.serial.TwelveToneRow` is the same as 
        any of the historical
        twelve-tone rows stored by music21: see :func:`music21.serial.getHistoricalRowByName`.
        Returns a list of names of historical rows to which the input row is identical.
        
        >>> row = serial.pcToToneRow([2, 3, 9, 1, 11, 5, 8, 7, 4, 0, 10, 6])
        >>> row.findHistorical()
        ['RowSchoenbergOp32']
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.findHistorical()
        []
        '''
        samerows = []
        for historicalrow in historicalDict:
            if self.isSameRow(getHistoricalRowByName(historicalrow)):
                samerows.append(historicalrow)
        return samerows
    
    def findTransformedHistorical(self, convention):
        '''
        Checks if a given :class:`music21.serial.TwelveToneRow` is a transformation of any of the historical
        twelve-tone rows stored by music21: see :func:`music21.serial.getHistoricalRowByName`. Returns a list
        of tuples, the tuple consisting of the name of a historical row, and a list of transformations relating
        the input row to the historical row.
        
        The convention for serial transformations must also be specified as 'zero' or 'original', as explained
        in :meth:`~music21.serial.findZeroCenteredTransformations` and 
        :meth:`~music21.serial.findOriginalCenteredTransformations`.
        
        >>> row = serial.pcToToneRow([5, 9, 11, 3, 6, 7, 4, 10, 0, 8, 2, 1])
        >>> row.findTransformedHistorical('original')
        [('RowSchoenbergOp32', [('R', 11)])]
        '''
        samerows = []
        if convention == 'zero':
            for historicalrow in historicalDict:
                trans = getHistoricalRowByName(historicalrow).findZeroCenteredTransformations(self)
                if trans != []:
                    samerows.append((historicalrow, trans))
            return samerows
        if convention == 'original':
            for historicalrow in historicalDict:
                trans = getHistoricalRowByName(historicalrow).findOriginalCenteredTransformations(self)
                if trans != []:
                    samerows.append((historicalrow, trans))
            return samerows
        else:
            raise SerialException("Invalid convention - choose 'zero' or 'original'.")
                    
    def isAllInterval(self):
        '''
        Describes whether or not a :class:`~music21.serial.TwelveToneRow` is an all-interval row.
        
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.pitchClasses()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        >>> chromatic.isAllInterval()
        False
        >>> bergLyric = serial.getHistoricalRowByName('RowBergLyricSuite')
        >>> bergLyric.pitchClasses()
        [5, 4, 0, 9, 7, 2, 8, 1, 3, 6, 10, 11]
        >>> bergLyric.isAllInterval()
        True
        '''
        
        if self.isTwelveToneRow() == False:
            raise SerialException("An all-interval row must be a twelve-tone row.")
        else:
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
        Gives the classification number of a Link Chord 
        (as given in http://www.johnlinkmusic.com/LinkChords.pdf), 
        that is, is an all-interval twelve-tone row containing a voicing of the 
        all-trichord hexachord: [0, 1, 2, 4, 7, 8].
        In addition, gives a list of sets of five contiguous intervals 
        within the row representing a voicing
        of the all-trichord hexachord. Note that the interval sets may be transformed.
        
        Named for John Link who discovered them.
        
        
        >>> bergLyric = serial.getHistoricalRowByName('RowBergLyricSuite')
        >>> bergLyric.pitchClasses()
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
        # the link interval strings given below are untransformed: by inversion around 0, 
        # original-centered retrograde, and
        # retrograde inversion around zero, we get three more link interval strings for 
        # each one in fullLinkIntervals.
        # in the original rows, this corresponds simply to checking the interval string of any
        # inversion, retrograde inversion, and retrograde, respectively.
        
        fullLinkIntervals = ['125634T97E8', '134E78526T9', '134E79T6258', '134E79T6258', 
                             '1367T89E254', '137E542896T', '137E982456T', '142965837ET', 
                             '142973856ET', '1429738E65T', '14297TE6853', '145638E729T', 
                             '1456T729E83', '1456T982E73', '145927E836T', '14598E63T72', 
                             '14689T7E253', '1469E27T853', '149278356ET', '1492783E65T', 
                             '1496258T73E', '1496E358T72', '14972836E5T', '14972E6385T', 
                             '1497T853E62', '14E379T6528', '14E6T783529', '172E6853T94', 
                             '17356ET8294', '1738T542E69', '173E65T8294', '1763T4952E8', 
                             '176852E34T9', '179236E8T54', '179236E8T54', '17923E685T4', 
                             '179245T8E63', '17924T586E3', '179T65234E8', '179T8E63254', 
                             '179T8E63254', '1825E43796T', '1825E43796T', '1825E79T364', 
                             '1825E79T364', '1852E43769T', '1852E79463T', '185629TE743', 
                             '18563479TE2', '18563E7T492', '18734E5296T', '18734E5296T', 
                             '187E259436T', '187E259436T', '18T352E7964', '18T497E3562', 
                             '18T97E52364', '18T97E52364', '18E63T79452', '18E63T79452', 
                             '19476538TE2', '1947T8536E2', '1954763T8E2', '19742538E6T', 
                             '197425T6E83', '1974T8E6352', '197T8532E64', '1T5E7928364', 
                             '1T63E874259', '1T6E3852479', '1T8352E4679', '1T974253E68', 
                             '214367TE985', '214376598ET', '214376598ET', '2143E86597T', 
                             '2149586E37T', '214976538ET', '214976538ET', '216734ET985', 
                             '216743E9T85', '217634TE985', '21T8E956347', '21T96583E47', 
                             '234T1596E87', '235189E647T', '235189E647T', '23689E7T145', 
                             '236E981547T', '236E981547T', '23T514697E8', '2513647ET98', 
                             '25189TE7463', '25189TE7463', '2546E981T73', '25691T8E473', 
                             '2569E8T1437', '258T73E6149', '258T9614E37', '25T31496E87', 
                             '25T89E61437', '2618T497E35', '26347ET9185', '263891T7E45', 
                             '263891T7E45', '2653E718T49', '2654T1783E9', '2654T1783E9', 
                             '2654E3871T9', '2654E3871T9', '2654E7T1983', '2654E7T1983', 
                             '265819TE743', '2659E8T1347', '267431T8E95', '2694T817E35', 
                             '269T1783E45', '269T1783E45', '269E3871T45', '269E3871T45', 
                             '26E451T7389', '26E451T7389', '26E459817T3', '26E459817T3', 
                             '26E4T718953', '26E4T718953', '26E873T5149', '26E95134T87', 
                             '26E95178T43', '274316E985T', '274316E985T', '2743E86591T', 
                             '274916E385T', '274916E385T', '2749586E31T', '276134ET985', 
                             '276143E9T85', '27E34169T85', '2965387E41T', '2965387E41T', 
                             '296E387T145', '29TE7436185', '29TE7463158', '29E7835641T', 
                             '29E7835641T', '2E431T96587', '2E431T96587', '2E465387T19', 
                             '2E637T85419', '2E783T51469', '2E783T51469', '2E796415T38', 
                             '2E8T1956743', '2E9658T4137', '3142E8956T7', '3142ET79685', 
                             '31456T972E8', '314672E9T85', '3152689TE74', '3152689TE74', 
                             '3152E9T8764', '3158629TE74', '3158629TE74', '316452E98T7', 
                             '317ET562894', '317ET926854', '317ET986254', '319765T42E8', 
                             '3198265TE74', '31T524796E8', '31T567942E8', '31T7E294685', 
                             '325E79T8164', '325E79T8164', '3265981TE74', '329E71T4568', 
                             '329E71T4568', '32E981T6547', '347621T8E95', '3479TE26185', 
                             '34T9E712568', '35146T927E8', '35146T927E8', '351T64927E8', 
                             '351T64927E8', '351T7924E68', '35216E98T74', '3521T8E9674', 
                             '3581629ET74', '3594T6127E8', '359E6128T74', '35E7216T498', 
                             '35E72946T18', '35E729T6418', '3625189TE74', '3625189TE74', 
                             '36524ET8917', '3674218T9E5', '36T154927E8', '36T154927E8', 
                             '3764128T9E5', '38297E5T164', '38E729T6145', '3T17E924568', 
                             '3T17E924568', '3T4952E8617', '3T6194527E8', '3T62E815497', 
                             '3T97E528164', '3T97E528164', '3E2418596T7', '3E7T4926185', 
                             '416352E7T98', '41T629E7835', '41T629E7835', '4328T56E917', 
                             '4328TE65917', '43T9E865217', '463152E9T87', '46529E8T137', 
                             '46731T8E925', '4692E513T87', '4692E513T87', '46982315ET7', 
                             '469T315E287', '469T315E287', '4769E251T38', '4783T1629E5', 
                             '47T198236E5', '47E928361T5', '4T1629E3785', '4TE86592317', 
                             '4E2538T1697', '4E29658T317', '4E29658T317', '4ET85692317', 
                             '4ET85692317', '5896T142E37']
        specialLinkIntervals = [
                             '25634', '134E7', '134E7', 'E79T6', '89E25', '7E542', '7E982', 
                             '29658', '856ET', '8E65T', 'E6853', '8E729', '729E8', '982E7', 
                             '927E8', '8E63T', '7E253', '7T853', '78356', '783E6', '58T73', 
                             '358T7', '2836E', '2E638', '7T853', '79T65', '78352', 'E6853', 
                             '56ET8', '42E69', 'E65T8', '4952E', '52E34', '236E8', '36E8T', 
                             '3E685', 'T8E63', '586E3', '79T65', 'T8E63', '8E632', '25E43', 
                             '5E437', '25E79', '5E79T', 'E4376', 'E7946', '9TE74', '479TE', 
                             'E7T49', '734E5', '34E52', '87E25', 'E2594', '352E7', 'T497E', 
                             'T97E5', '97E52', '8E63T', 'T7945', '76538', '7T853', '4763T', 
                             '97425', '97425', 'T8E63', '7T853', '5E792', '74259', '52479', 
                             '8352E', '97425', '4367T', '43765', '76598', 'E8659', '586E3', 
                             '49765', '76538', '6734E', '21674', '7634T', '1T8E9', 'T9658', 
                             '34T15', '5189E', '189E6', '689E7', '6E981', 'E9815', '3T514', 
                             '47ET9', '25189', '9TE74', '6E981', '91T8E', '9E8T1', '58T73', 
                             'T9614', '5T314', '89E61', 'T497E', '47ET9', '891T7', '1T7E4', 
                             'E718T', 'T1783', '1783E', 'E3871', '3871T', '4E7T1', '7T198', 
                             '9TE74', '9E8T1', '1T8E9', 'T817E', 'T1783', '1783E', 'E3871', 
                             '3871T', '451T7', '1T738', '59817', '9817T', 'T7189', '71895', 
                             '3T514', '5134T', '5178T', '4316E', '16E98', 'E8659', '4916E', 
                             '16E38', '586E3', '6134E', '27614', '4169T', '65387', '5387E', 
                             '6E387', '9TE74', '9TE74', 'E7835', '78356', 'E431T', 'T9658', 
                             '65387', '37T85', '2E783', '3T514', '415T3', 'E8T19', '9658T', 
                             '3142E', '3142E', '56T97', '31467', '52689', '9TE74', '152E9', 
                             '58629', '9TE74', '52E98', '56289', '92685', '98625', '765T4', 
                             '98265', '52479', '56794', '31T7E', '25E79', '5E79T', '65981', 
                             '29E71', '9E71T', '2E981', '1T8E9', '479TE', 'T9E71', '146T9', 
                             '927E8', '1T649', '927E8', '51T79', '16E98', '1T8E9', '1629E', 
                             '94T61', 'E6128', '16T49', '946T1', '9T641', '25189', '9TE74', 
                             '36524', '36742', 'T1549', '927E8', '37641', '297E5', '8E729', 
                             'T17E9', '17E92', '4952E', '61945', '15497', 'T97E5', '97E52', 
                             '3E241', 'E7T49', '352E7', '629E7', 'E7835', '8T56E', '8TE65', 
                             '9E865', '152E9', '9E8T1', '1T8E9', '2E513', 'E513T', '2315E', 
                             'T315E', '315E2', '9E251', '1629E', '7T198', '8361T', '1629E', 
                             'E8659', 'E2538', '29658', '9658T', 'T8569', '85692', '142E3']
        linkClassification = [# line breaks emphasize repetitions
                               1,  2,  3,  3, 
                               4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 
                              18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 
                              30, 31, 32, 33, 33, 
                              34, 35, 36, 37, 38, 38, 
                              39, 39, 
                              40, 40, 41, 42, 43, 44, 45, 46, 46, 47, 47, 48, 49, 
                              50, 50, 
                              51, 51, 
                              52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 
                              64, 65, 65, 66, 67, 68, 68, 69, 70, 71, 72, 73, 74, 75, 75, 
                              76, 77, 77, 
                              78, 79, 80, 80, 
                              81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 90, 
                              91, 92, 92, 
                              93, 93, 
                              94, 94, 
                              95, 96, 97, 98, 99, 99, 
                              100, 100, 
                              101, 101, 
                              102, 102, 
                              103, 103, 
                              104, 105, 106, 107, 107, 108, 109, 109, 
                              110, 111, 112, 113, 114, 114, 
                              115, 116, 117, 118, 118, 
                              119, 119, 
                              120, 121, 122, 122, 
                              123, 124, 125, 126, 127, 128, 129, 130, 130, 
                              131, 132, 132, 
                              133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 142, 
                              143, 144, 144, 
                              145, 146, 147, 148, 149, 149, 
                              150, 150, 
                              151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 160, 
                              161, 162, 163, 163, 
                              164, 165, 166, 167, 167, 168, 169, 170, 171, 171, 
                              172, 173, 174, 175, 175, 
                              176, 177, 178, 179, 180, 181, 182, 182, 
                              183, 184, 184, 
                              185, 186, 187, 188, 189, 190, 191, 192, 192, 
                              193, 193, 
                              194]
        numchords = len(fullLinkIntervals)
        
        if self.isTwelveToneRow() == False:
            raise SerialException("A Link Chord must be a twelve-tone row.")
        else: 
            rowchecklist = [self, 
                            self.zeroCenteredTransformation('I',0), 
                            self.zeroCenteredTransformation('R',0), 
                            self.zeroCenteredTransformation('RI',0)]
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
        Describes whether or not a :class:`~music21.serial.TwelveToneRow` is a Link Chord.
        
        >>> bergLyric = serial.getHistoricalRowByName('RowBergLyricSuite')
        >>> bergLyric.pitchClasses()
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
        linkTuple = self.getLinkClassification()
        if linkTuple[0] == None:
            return False
        else:
            return True
    
    def areCombinatorial(self, transType1, index1, transType2, index2, convention):
        '''
        Describes whether or not two transformations of a twelve-tone row are combinatorial.
        
        The first and second arguments describe one transformation, while the third and fourth
        describe another. One of the zero-centered or original-centered conventions for tone row
        transformations must be specified in the last argument; see 
        :meth:`~music21.serial.zeroCenteredTransformation` and 
        :meth:`~music21.serial.originalCenteredTransformation` explanations of these conventions.
        
        >>> moses = serial.getHistoricalRowByName('RowSchoenbergMosesAron')
        >>> moses.pitchClasses()
        [9, 10, 4, 2, 3, 1, 7, 5, 6, 8, 11, 0]
        >>> moses.areCombinatorial('P', 1, 'I', 4, 'zero')
        True
        >>> moses.areCombinatorial('R', 5, 'RI', 6, 'original')
        False
        '''
        if self.isTwelveToneRow() == False:
            raise SerialException("Combinatoriality applies only to twelve-tone rows.")
        else:
            if convention == 'zero':
                testRow = []
                trans1 = self.zeroCenteredTransformation(transType1, index1)
                pitches1 = trans1.pitchClasses()
                trans2 = self.zeroCenteredTransformation(transType2, index2)
                pitches2 = trans2.pitchClasses()
                for i in range(0,6):
                    testRow.append(pitches1[i])
                for i in range(0,6):
                    testRow.append(pitches2[i])
                return pcToToneRow(testRow).isTwelveToneRow()
            elif convention == 'original':
                testRow = []
                trans1 = self.originalCenteredTransformation(transType1, index1)
                pitches1 = trans1.pitchClasses()
                trans2 = self.originalCenteredTransformation(transType2, index2)
                pitches2 = trans2.pitchClasses()
                for i in range(0,6):
                    testRow.append(pitches1[i])
                for i in range(0,6):
                    testRow.append(pitches2[6+i])
                return pcToToneRow(testRow).isTwelveToneRow()
            else:
                raise SerialException("Invalid convention - choose 'zero' or 'original'.")

# ------- parsing functions for atonal music -------

class ContiguousSegmentOfNotes(base.Music21Object):
    '''
    Class whose instantiations represent contiguous segments of notes and chords appearing
    within a :class:`~music21.stream.Stream`. Generally speaking, these objects are instantiated 
    internally, though it is possible
    for the user to create them as well. 
    '''

    activeSegment = None
    matchedSegment = None
    
    _DOC_ATTR = {
    'segment': 'The list of notes and chords in the contiguous segment.',
    'containerStream': '''The stream containing the contiguous segment - 
        all contiguous segments must have a container stream.''',
    'partNumber': '''The part number in which the segment appears, or None 
        (if the container stream has no parts). Note that this attribute is zero-indexed, 
        so the top (e.g. soprano) part is labeled 0.''',
    'activeSegment': '''A list of pitch classes representing the way the contiguous 
        segment of notes is being read as a sequence of single pitches. Set to None 
        unless the container stream is being searched for segments or multisets 
        (for example, using :func:`~music21.serial.findSegments`), in which case 
        the representation depends on the segments or multisets being searched for. 
        If there are no chords in the segment, this attribute will simply give the 
        pitch classes of the notes in the segment.''',
    'matchedSegment': '''A list of pitch classes representing the segment to which 
        the contiguous segment of notes is matched when segments or multisets are 
        searched for (for example, using :func:`~music21.serial.findSegments`); 
        otherwise set to None. Note that the contiguous segment will only be 
        matched to one of the segments or multisets being searched for.'''
    }
    
    _DOC_ORDER = ['startMeasureNumber', 'startOffset', 'zeroCenteredTransformationsFromMatched', 
                  'originalCenteredTransformationsFromMatched']

    def __init__(self, segment=None, containerStream=None, partNumber=0):
        '''
        >>> s = stream.Stream()
        >>> p = stream.Part()
        >>> n1 = note.Note('c4')
        >>> n2 = note.Note('d4')
        >>> p.append(n1)
        >>> p.append(n2)
        >>> p = p.makeMeasures()
        >>> s.insert(0, p)
        >>> CD_ContiguousSegment = serial.ContiguousSegmentOfNotes([n1, n2], s, 0)
        '''
        base.Music21Object.__init__(self)        
        self.segment = segment
        self.containerStream = containerStream
        self.partNumber = partNumber
        
    def _getStartMeasureNumber(self):
        if (len(self.segment)):
            return self.segment[0].measureNumber
        else:
            return None
    
    startMeasureNumber = property(_getStartMeasureNumber,
        doc = '''The measure number on which the contiguous segment begins.''')
    
    def _getStartOffset(self):
        if (len(self.segment)):
            return self.segment[0].offset
        else:
            return None
    startOffset = property(_getStartOffset,
        doc = '''The offset of the beginning of the contiguous segment, 
            with respect to the measure containing the first note.''')
    
    def _getZeroCenteredTransformationsFromMatchedToActive(self):
        activeRow = pcToToneRow(self.activeSegment)
        matchedRow = pcToToneRow(self.matchedSegment)
        return matchedRow.findZeroCenteredTransformations(activeRow)
    
    zeroCenteredTransformationsFromMatched = property(
        _getZeroCenteredTransformationsFromMatchedToActive, 
        doc = '''The list of zero-centered transformations taking a segment being searched 
                    for to a found segment, for example, in 
                    :func:`~music21.serial.findTransformedSegments`. 
                    For an explanation of the zero-centered convention for serial transformations, 
                    see :meth:`music21.serial.ToneRow.zeroCenteredTransformation`.''')
        
    def _getOriginalCenteredTransformationsFromMatchedToActive(self):
        activeRow = pcToToneRow(self.activeSegment)
        matchedRow = pcToToneRow(self.matchedSegment)
        return matchedRow.findOriginalCenteredTransformations(activeRow)
    
    originalCenteredTransformationsFromMatched = property(
        _getOriginalCenteredTransformationsFromMatchedToActive, 
        doc = '''The list of original-centered transformations taking a segment being 
                searched for to a found segment, for example, in 
                :func:`~music21.serial.findTransformedSegments`. For an explanation of the 
                zero-centered convention for serial transformations, see 
                :meth:`music21.serial.ToneRow.originalCenteredTransformation`.''')

    def readPitchClassesFromBottom(self):        
        '''
        Returns the list of pitch classes in the segment, reading pitches within 
        chords from bottom to top.
        
        >>> sc = stream.Score()
        >>> n1 = note.Note('d4')
        >>> n1.quarterLength = 1
        >>> Cmaj = chord.Chord(['c4', 'e4', 'g4'])
        >>> Cmaj.quarterLength = 1
        >>> sc.append(n1)
        >>> sc.append(Cmaj)
        >>> sc = sc.makeMeasures()
        >>> allNotes = serial.getContiguousSegmentsOfLength(sc, 4)
        >>> allNotes[0].readPitchClassesFromBottom()
        [2, 0, 4, 7]
        '''
        seg = self.segment
        pitchClasses = []
        for noteOrChord in seg:
            for p in noteOrChord.pitches:
                pitchClasses.append(p.pitchClass)
        return pitchClasses
    
    def getDistinctPitchClasses(self):        
        '''
        Returns a list of distinct pitch classes in the segment, in order of appearance,
        where pitches in a chord are read from bottom to top.
        
        
        >>> sc = stream.Score()
        >>> n1 = note.Note('d4')
        >>> n1.quarterLength = 1
        >>> c = chord.Chord(['d4', 'e4', 'g4', 'd5'])
        >>> c.quarterLength = 1
        >>> sc.append(n1)
        >>> sc.append(c)
        >>> sc = sc.makeMeasures()
        >>> allNotes = serial.getContiguousSegmentsOfLength(sc, 5)
        >>> allNotes[0].getDistinctPitchClasses()
        [2, 4, 7]
        
        '''
        
        seg = self.segment
        pitchClasses = []
        for noteOrChord in seg:
            for p in noteOrChord.pitches:
                if p.pitchClass not in pitchClasses:
                    pitchClasses.append(p.pitchClass)
        return pitchClasses


def getContiguousSegmentsOfLength(inputStream, 
                                  length, 
                                  reps='skipConsecutive', 
                                  includeChords=True):
    #TODO: The ignoreAll setting currently gets everything that could possibly work, which is a lot. For example, currently
    #if you have 123412341234, any subsequence of this with length at least 4 will be found. There are four commented
    #lines that say "uncomment this line to find shortest." Uncommenting all four of these lines should
    #find the shortest segment of the given length starting on each note. The reason why this will better is that
    #there will be far less clutter when calling a labelling function; too much clutter on one of these functions
    #results in overlapping IdLocals and spanners not showing properly.
    
    #For the above, there are other reasonable subsettings for ignoreAll, like to find the longest segment of the given
    #length containing the first note. Of course, this works very badly with doing something like finding all 12-tone rows,
    #because all this will do is make the entire piece one big twelve-tone row.
    
    #Also, one should keep in mind 121212121212123456 - when 123456 is searched for, what should be found?
    '''
    Returns a list of :class:`~music21.serial.ContiguousSegmentOfNotes` objects given a :class:`~music21.stream.Stream`
    where the desired number of notes in the segment is specified.
    
    The inputStream is a :class:`~music21.serial.ContiguousSegmentOfNotes` containing at most one score.
    Furthermore, all notes must be contained within measures.
    
    The reps argument specifies how repeated pitch classes are dealt with. 
    It may be set to 'skipConsecutive' (default), 'rowsOnly', 'includeAll', or 'ignoreAll'. These are explained in detail below.
    
    The includeChords argument specifies how chords are dealt with. When set to True (default), the pitches of all chords
    are read in order from bottom to top, and when set to False, all segments containing chords are ignored.
    
    The main subtleties of this function lie in how each reps setting works in conjunction with chords when
    includeChords is set to True, and how the lengths of the segments are measured.
    However, let us first examine what happens when includeChords
    is set to False, to get an idea of how the function works.
    
    To begin, we create a stream on which we will apply the function.
    
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
        
    We can now try to apply this function:
    
    >>> contiglist = serial.getContiguousSegmentsOfLength(s, 3, 'skipConsecutive', False)
    >>> print(contiglist)
    []
        
    On our first attempt, no contiguous segments of notes were found above 
    because the inputStream has no measures -
    hence we replace s with s.makeMeasures().
    
    >>> s = s.makeMeasures()
    >>> s.makeTies()
    >>> #_DOCS_SHOW s.show()
        
    .. image:: images/serial-findTransposedSegments.png
       :width: 500
        
    We now can apply the function, and in doing so we examine in detail each of the reps settings.
    
    'skipConsecutive' means that whenever immediate repetitions of notes or chords occur, only the first
    instance of the note or chord is included in the segment. The durations of the repeated notes,
    do not have to be the same.
    
    >>> skipConsecutiveList = serial.getContiguousSegmentsOfLength(s, 3, 'skipConsecutive', False)
    >>> print(skipConsecutiveList)
    [<music21.serial.ContiguousSegmentOfNotes object ...]
    >>> [instance.segment for instance in skipConsecutiveList]
    [[<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>], 
    [<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>]]
        
    In order to be considered repetition, the spellings of the notes 
    in question must be exactly the same:
    enharmonic equivalents are not checked and notes with the 
    same pitch in different octaves are considered different.
    To illustrate this, see the example below, in which all three notes, 
    with pitch class 0, are considered
    separately.
    
    >>> new = stream.Stream()
    >>> N1 = note.Note('c4')
    >>> N2 = note.Note('c5')
    >>> N3 = note.Note('b#5')
    >>> new.append(N1)
    >>> new.append(N2)
    >>> new.append(N3)
    >>> new = new.makeMeasures()
    >>> [seg.segment for seg in serial.getContiguousSegmentsOfLength(new, 3, 'skipConsecutive', includeChords = False)]
    [[<music21.note.Note C>, <music21.note.Note C>, <music21.note.Note B#>]]
    
    'rowsOnly' searches only for tone rows, in which all pitch classes 
    in the segment must be distinct. Below,
    we are looking for sequences three consecutive notes within the 
    stream s, all of which have different pitch classes.
    There is only one such set of notes, and by calling the 
    :attr:`~music21.serial.ContiguousSegmentOfNotes` we can
    determine its location (the measure number of its first note).  
    
    >>> rowsOnlyList = serial.getContiguousSegmentsOfLength(s, 3, 'rowsOnly', includeChords = False)
    >>> [(instance.segment, instance.startMeasureNumber) for instance in rowsOnlyList]
    [([<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>], 4)]
    
    'includeAll' disregards all repetitions, and simply gets all 
    contiguous segments of the specified length (still subject
    to the includeChords setting).
    
    >>> includeAllList = serial.getContiguousSegmentsOfLength(s, 3, 'includeAll', includeChords = False)
    >>> [(instance.segment, instance.startMeasureNumber, instance.startOffset) for instance in includeAllList]
    [([<music21.note.Note G>, <music21.note.Note G>, <music21.note.Note A>], 3, 0.0),
    ([<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note A>], 3, 1.0),
    ([<music21.note.Note A>, <music21.note.Note A>, <music21.note.Note B>], 3, 2.0),
    ([<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>], 4, 1.0)]
    
    Note that there only two total As appear in these segments, despite there being three
    :class:`~music21.note.Note` objects with the A4 as the pitch 
    in the stream s; this is because only the first note of each set
    of tied notes is considered. This convention applies to this 
    function and all parsing functions below.
    Also note that so far, neither of the first two notes n1, n2 
    nor the major third n3 in s have been included in any of the
    returned contiguous segments. This is because for each of these, 
    any instance of three consecutive notes or chords
    contains the chord n3. This phenomenon also applies to the next example below.
    
    Finally, when includeChords is set to False, 'ignoreAll' finds all 
    contiguous segments containing exactly three distinct pitch
    classes within it. It is unique in that unlike the previous three 
    reps settings, the segments returned in fact
    have more than the number of notes specified (3). Rather, they 
    each have 3 distinct pitch classes, and some pitch classes
    may be repeated.
    
    >>> ignoreAllList = serial.getContiguousSegmentsOfLength(s, 3, 'ignoreAll', includeChords = False)
    >>> [instance.segment for instance in ignoreAllList]
    [[<music21.note.Note G>, <music21.note.Note G>, <music21.note.Note A>, <music21.note.Note A>, 
      <music21.note.Note B>], 
     [<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note A>, <music21.note.Note B>], 
     [<music21.note.Note A>, <music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>], 
     [<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>]]
        
    Let us now examine what happens in the default chord setting, in which includeChords is set to True.

    There are two points to remember when considering chords: the first is that all 
    chords are read as sequences of single notes,
    from bottom to top. The second is that 'length' always applies to the total 
    number of single pitches or pitch classes found 
    in the segment, including within chords, and not to the number of notes or chords. 
    However, as we will see, when we search
    for contiguous segments of length 4, the returned segments may not have exactly 
    4 total notes (possibly existing 
    as single notes or within chords), a natural point of confusion.
    
    Below is a new stream s0.
    
    >>> s0 = stream.Stream()
    >>> n1 = note.Note('d4')
    >>> maj2nd = chord.Chord(['f4', 'g4'])
    >>> bmaj1 = chord.Chord(['b4', 'd#5', 'f#5'])
    >>> bmaj2 = chord.Chord(['b4', 'd#5', 'f#5'])
    >>> n2 = note.Note('f#4')
    >>> n3 = note.Note('e4')
    >>> n4 = note.Note('a4')
    >>> s0.append(n1)
    >>> s0.append(maj2nd)
    >>> s0.append(bmaj1)
    >>> s0.append(bmaj2)
    >>> s0.append(n2)
    >>> s0.append(n3)
    >>> s0.append(n4)
    >>> s0 = s0.makeMeasures()
    >>> #_DOCS_SHOW s.show()
    
    .. image:: images/serial-getContiguousSegmentsOfLength2.png
       :width: 500
    
    >>> skipConsecutiveWithChords = serial.getContiguousSegmentsOfLength(s0, 4, 'skipConsecutive')
    >>> [seg.segment for seg in skipConsecutiveWithChords]
    [[<music21.note.Note D>, <music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>], 
     [<music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>], 
     [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>], 
     [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>, <music21.note.Note E>], 
     [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>, <music21.note.Note E>, 
      <music21.note.Note A>]]
        
    Let us look closely at the found segments. First, because reps 
    was set to 'skipConsecutive', the second
    B major chord (bmaj2) is never considered, as the chord right 
    before it is the same. As was mentioned before,
    not all of the segments found have exactly 4 notes total. 
    This is because, for each segment, only a subset
    of the notes contained in the first and last elements are read. Given one of the 
    found segments, it will always 
    be possible to extract exactly four consecutive pitches from the notes and chords, 
    reading in order, so that
    at least one pitch is taken from each of the first and last chords.
    
    In the first segment, there is one way to extract 4 consecutive pitches: 
    we take the D in the first note, read
    the F and G (in that order) from the next chord, and finally, 
    reading the last chord from bottom to top, the B
    from the B major chord. Note that no other reading of the segment 
    is possible because the D from the first note
    must be used. The second segment in the returned list, on the other 
    hand, can be read as a sequence of 4
    consecutive pitches in two ways, both equally valid. We can either take 
    the top note of the first chord, and all three
    notes, in order, of the second chord, or both notes of the first chord 
    and the bottom two notes of the second chord.
    
    >>> rowsOnlyChords = serial.getContiguousSegmentsOfLength(s0, 4, 'rowsOnly')
    >>> [seg.segment for seg in rowsOnlyChords]
    [[<music21.note.Note D>, <music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>], 
    [<music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>]]
        
    When reps is set to 'rowsOnly', the segments returned are those such that each may be read as a sequence
    of 4 pitches, in the same manner as explained above with the 'skipConsecutive' setting, such that the sequence
    of 4 pitches constitutes a four-note tone row. Above, the first segment corresponds to the row [2, 5, 7, 11], and the
    second may be read as either [5, 7, 11, 3] or [7, 11, 3, 6]. Note that, for example, we could not include both
    the B-major chord and the F# that comes right after it in the same segment, because there would have to be two 
    consecutive instances of the pitch class 6 (corresponding to F#). Similarly, we could not include both instances
    of the B-major chord, as, again, we would have a pitch class repeated in any resulting four-note row.
    
    >>> includeAll = serial.getContiguousSegmentsOfLength(s0, 4, 'includeAll')
    >>> [seg.segment for seg in includeAll]
    [[<music21.note.Note D>, <music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>], 
    [<music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>], 
    [<music21.chord.Chord B4 D#5 F#5>, <music21.chord.Chord B4 D#5 F#5>], 
    [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>], 
    [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>, <music21.note.Note E>], 
    [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>, <music21.note.Note E>, <music21.note.Note A>]]
        
    Here, all segments from which sequences of four consecutive pitches can be extracted, again with at least
    one pitch coming from each of the first and last elements of the segments, are found.
    
    >>> ignoreAll = serial.getContiguousSegmentsOfLength(s0, 4, 'ignoreAll')
    >>> [seg.segment for seg in ignoreAll]
    [[<music21.note.Note D>, <music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>], 
    [<music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>], 
    [<music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>, <music21.chord.Chord B4 D#5 F#5>], 
    [<music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>, <music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>], 
    [<music21.chord.Chord B4 D#5 F#5>, <music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>, <music21.note.Note E>], 
    [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>, <music21.note.Note E>], 
    [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>, <music21.note.Note E>, <music21.note.Note A>]]
        
    When reps is set to 'ignoreAll', the pitch classes from each segment are read by taking, in order, the pitch classes
    in the order in which they first appear, where chords are again read from bottom to top. For example, in the last segment,
    the first three pitch classes are those in the first chord, from bottom to top: 11, 3, and 6. Then, the next pitch class
    appearing is 6, which is disregarded because it has already appeared. Finally, the pitch classes 4 and 9 appear in that order.
    There are thus five pitch classes in this segment, in the order [11, 3, 6, 4, 9]. 
    
    The segment can be read has having length 4 because four consecutive 
    pitch classes, [3, 6, 4, 9], can be read from this sequence 
    in such a way that the first pitch class of this subsequence is part of the 
    first chord in the segment, and the last pitch class
    is that of the last note of the segment. More generally, in this setting the 
    found segments are those which contain at least 4
    distinct pitch classes, but the top note of the first chord (or note), the 
    bottom note of the last chord (or note), 
    and all pitches of all notes and chords other than the first and last 
    contain at most 4 distinct pitch classes.
    
    OMIT_FROM_DOCS
    
    >>> import copy
    >>> sc = stream.Score()
    >>> p = stream.Part()
    >>> c1 = chord.Chord(['c4', 'd4'])
    >>> c2 = chord.Chord(['c5', 'd5'])
    >>> n1 = note.Note('e4')
    >>> n2 = note.Note('f4')
    >>> p.append(n2)
    >>> p.append(n1)
    >>> p.append(c2)
    >>> p.append(c1)
    >>> p = p.makeMeasures()
    >>> p1 = copy.deepcopy(p)
    >>> sc.insert(0.0, p1)
    >>> p2 = copy.deepcopy(p)
    >>> sc.insert(0.0, p2)
    >>> [seg.segment for seg in serial.getContiguousSegmentsOfLength(sc, 3, 'ignoreAll')]
    [[<music21.note.Note F>, <music21.note.Note E>, <music21.chord.Chord C5 D5>], 
    [<music21.note.Note E>, <music21.chord.Chord C5 D5>], 
    [<music21.note.Note E>, <music21.chord.Chord C5 D5>, <music21.chord.Chord C4 D4>], 
    [<music21.note.Note F>, <music21.note.Note E>, <music21.chord.Chord C5 D5>], 
    [<music21.note.Note E>, <music21.chord.Chord C5 D5>], 
    [<music21.note.Note E>, <music21.chord.Chord C5 D5>, <music21.chord.Chord C4 D4>]]
    '''
    
    listOfContiguousSegments = []
    
    scores = inputStream.getElementsByClass(stream.Score)
    if len(scores) == 0:
        parts = inputStream.getElementsByClass(stream.Part)
    elif len(scores) == 1:
        parts = scores[0].parts
    else:
        raise SerialException("The inputStream can contain at most one score.")
    
    if len(parts) == 0:
        if len(scores) == 0:
            measures = inputStream.getElementsByClass(stream.Measure)
        elif len(scores) == 1:
            measures = scores[0].getElementsByClass(stream.Measure)
        if reps == 'skipConsecutive':
            pitchList = []
            totallength = 0 #counts each pitch within a chord once
            for m in measures:
                for n in m.getElementsByClass([note.Note, chord.Chord], returnStreamSubClass=False):
                    if n.tie == None or n.tie.type == 'start':
                        add = False
                        if includeChords == False:
                            if len(n.pitches) == 1:
                                if pitchList == []:
                                    add = True
                                else:
                                    if pitchList[-1].pitch != n.pitch:
                                        add = True
                                if add == True:
                                    pitchList.append(n)
                                    if len(pitchList) == length + 1:
                                        pitchList.remove(pitchList[0])
                                    if len(pitchList) == length:
                                        listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(pitchList), inputStream, None))
                            elif len(n.pitches) > 1:
                                pitchList = []
                        else:
                            if pitchList == []:
                                add = True
                            else:
                                if pitchList[-1].pitches != n.pitches:
                                    add = True
                            if add == True:
                                pitchList.append(n)
                                totallength = totallength + len(n.pitches)
                                lengthofactive = totallength
                                donechecking = False
                                numnotestodelete = 0
                                for i in range(0, len(pitchList)):
                                    if donechecking == False:
                                        activePitchList = pitchList[i:len(pitchList)]
                                        if i != 0:
                                            lengthofactive = lengthofactive - len(pitchList[i-1].pitches)
                                        if lengthofactive >= length:
                                            if lengthofactive - len(activePitchList[0].pitches) - len(activePitchList[-1].pitches) <= length - 2:
                                                listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(activePitchList), inputStream, None))
                                            else:
                                                numnotestodelete = numnotestodelete + 1
                                        else:
                                            donechecking = True
                                for i in range(0, numnotestodelete):
                                    totallength = totallength - len(pitchList[0].pitches)
                                    pitchList.remove(pitchList[0])
        elif reps == 'rowsOnly':
            pitchList = []
            totallength = 0     
            for m in measures:
                for n in m.getElementsByClass([note.Note, chord.Chord], returnStreamSubClass=False):
                    if n.tie == None or n.tie.type == 'start':
                        if includeChords == False:
                            if len(n.pitches) == 1:
                                if len(pitchList) == length:
                                    if n.pitch.pitchClass not in [m.pitch.pitchClass for m in pitchList[1:]]:
                                        pitchList.append(n)
                                        pitchList.remove(pitchList[0])
                                    else:
                                        pitchList = [n]
                                else:
                                    if n.pitch.pitchClass not in [m.pitch.pitchClass for m in pitchList]:
                                        pitchList.append(n)
                                    else:
                                        pitchList = [n]
                                if len(pitchList) == length:
                                    listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(pitchList), inputStream, None))
                            else:
                                pitchList = []
                        else:
                            pitchList.append(n)
                            totallength = totallength + len(n.pitches)
                            lengthofactive = totallength
                            donechecking = False
                            numnotestodelete = 0
                            for i in range(0, len(pitchList)):
                                if donechecking == False:
                                    activePitchList = pitchList[i:len(pitchList)]
                                    if i != 0:
                                        lengthofactive = lengthofactive - len(pitchList[i-1].pitches)
                                    if lengthofactive >= length:
                                        if lengthofactive - len(activePitchList[0].pitches) - len(activePitchList[-1].pitches) <= length - 2:
                                            contigObj = ContiguousSegmentOfNotes(list(activePitchList), inputStream, None)
                                            rowSuperset = contigObj.readPitchClassesFromBottom()
                                            lowerBound = max([0, len(rowSuperset) - length - len(activePitchList[-1].pitches) + 1])
                                            upperBound = min([len(activePitchList[0].pitches) - 1, len(rowSuperset) - length])
                                            added = False
                                            for j in range(lowerBound, upperBound + 1):
                                                if added == False:   
                                                    if len(set(rowSuperset[j:j+length])) == length:
                                                        listOfContiguousSegments.append(contigObj)
                                                        added = True
                                        else:
                                            numnotestodelete = numnotestodelete + 1
                                    else:
                                        donechecking = True
                            for i in range(0, numnotestodelete):
                                totallength = totallength - len(pitchList[0].pitches)
                                pitchList.remove(pitchList[0])
        elif reps == 'includeAll':
            pitchList = []
            totallength = 0
            for m in measures:
                for n in m.getElementsByClass([note.Note, chord.Chord], returnStreamSubClass=False):
                    #environLocal.warn(str(n.measureNumber))
                    if n.tie == None or n.tie.type == 'start':
                        if includeChords == False:
                            if len(n.pitches) == 1:
                                pitchList.append(n)
                                if len(pitchList) == length + 1:
                                    pitchList.remove(pitchList[0])
                                if len(pitchList) == length:
                                    listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(pitchList), inputStream, None))
                            else:
                                pitchList = []                            
                        else:
                            pitchList.append(n)
                            totallength = totallength + len(n.pitches)
                            lengthofactive = totallength
                            donechecking = False
                            numnotestodelete = 0
                            for i in range(0, len(pitchList)):
                                if donechecking == False:
                                    activePitchList = pitchList[i:len(pitchList)]
                                    if i != 0:
                                        lengthofactive = lengthofactive - len(pitchList[i-1].pitches)
                                    if lengthofactive >= length:
                                        if lengthofactive - len(activePitchList[0].pitches) - len(activePitchList[-1].pitches) <= length - 2:
                                            listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(activePitchList), inputStream, None))
                                        else:
                                            numnotestodelete = numnotestodelete + 1
                                    else:
                                        donechecking = True
                            for i in range(0, numnotestodelete):
                                totallength = totallength - len(pitchList[0].pitches)
                                pitchList.remove(pitchList[0])
        elif reps == 'ignoreAll':
            pitchList = []
            totallength = 0
            for m in measures:
                for n in m.getElementsByClass([note.Note, chord.Chord], returnStreamSubClass=False):
                    if n.tie == None or n.tie.type == 'start':
                        if includeChords == False:
                            if len(n.pitches) == 1:
                                pitchList.append(n)
                                donechecking = False
                                numnotestodelete = 0
                                for i in range(0, len(pitchList)):
                                    if donechecking == False:
                                        activePitchList = pitchList[i:len(pitchList)]
                                        if len(set([n.pitch.pitchClass for n in activePitchList])) == length:
                                            listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(activePitchList), inputStream, None))
#uncomment this line to get shortest        #numnotestodelete = numnotestodelete + 1
                                        elif len(set([n.pitch.pitchClass for n in activePitchList])) > length:
                                            numnotestodelete = numnotestodelete + 1
                                        else:
                                            donechecking = True
                                for i in range(0, numnotestodelete):
                                    totallength = totallength - len(pitchList[0].pitches)
                                    pitchList.remove(pitchList[0])
                                                                                
                            else:
                                pitchList = []                            
                        else:
                            pitchList.append(n)
                            donechecking = False
                            numnotestodelete = 0
                            for i in range(0, len(pitchList)):
                                if donechecking == False:
                                    activePitchList = pitchList[i:len(pitchList)]
                                    activeseg = ContiguousSegmentOfNotes(list(activePitchList), inputStream, None)
                                    if len(set(activeseg.readPitchClassesFromBottom())) >= length:
                                        middleseg = ContiguousSegmentOfNotes(list(activePitchList[1:len(activePitchList)-1]), None, None)
                                        middlePitchClassSet = set(middleseg.readPitchClassesFromBottom())
                                        setToCheck = middlePitchClassSet.union([activePitchList[0].pitches[-1].pitchClass]).union([activePitchList[-1].pitches[0].pitchClass])
                                        if len(setToCheck) <= length:
                                            listOfContiguousSegments.append(activeseg)
#uncomment this line to get shortest        #numnotestodelete = numnotestodelete + 1                                            
                                        else:
                                            numnotestodelete = numnotestodelete + 1
                                    else:
                                        donechecking = True
                            for i in range(0, numnotestodelete):
                                totallength = totallength - len(pitchList[0].pitches)
                                pitchList.remove(pitchList[0])
        else:
            raise SerialException("Invalid repeated pitch setting.")
    else:
        for p in range(0, len(parts)):
            measures = parts[p].getElementsByClass(stream.Measure)
            if reps == 'skipConsecutive':
                pitchList = []
                totallength = 0 #counts each pitch within a chord once
                for m in measures:
                    for n in m.flat.notes:
                        if n.tie == None or n.tie.type == 'start':
                            add = False
                            if includeChords == False:
                                if len(n.pitches) == 1:
                                    if pitchList == []:
                                        add = True
                                    else:
                                        if pitchList[-1].pitch != n.pitch:
                                            add = True
                                    if add == True:
                                        pitchList.append(n)
                                        if len(pitchList) == length + 1:
                                            pitchList.remove(pitchList[0])
                                        if len(pitchList) == length:
                                            listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(pitchList), inputStream, p))
                                elif len(n.pitches) > 1:
                                    pitchList = []
                            else:
                                if pitchList == []:
                                    add = True
                                else:
                                    if pitchList[-1].pitches != n.pitches:
                                        add = True
                                if add == True:
                                    pitchList.append(n)
                                    totallength = totallength + len(n.pitches)
                                    lengthofactive = totallength
                                    donechecking = False
                                    numnotestodelete = 0
                                    for i in range(0, len(pitchList)):
                                        if donechecking == False:
                                            activePitchList = pitchList[i:len(pitchList)]
                                            if i != 0:
                                                lengthofactive = lengthofactive - len(pitchList[i-1].pitches)
                                            if lengthofactive >= length:
                                                if lengthofactive - len(activePitchList[0].pitches) - len(activePitchList[-1].pitches) <= length - 2:
                                                    listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(activePitchList), inputStream, p))
                                                else:
                                                    numnotestodelete = numnotestodelete + 1
                                            else:
                                                donechecking = True
                                    for i in range(0, numnotestodelete):
                                        totallength = totallength - len(pitchList[0].pitches)
                                        pitchList.remove(pitchList[0])
            elif reps == 'rowsOnly':
                pitchList = []
                totallength = 0
                for m in measures:
                    for n in m.flat.notes:
                        if n.tie == None or n.tie.type == 'start':
                            if includeChords == False:
                                if len(n.pitches) == 1:
                                    if len(pitchList) == length:
                                        if n.pitchClass not in [m.pitchClass for m in pitchList[1:]]:
                                            pitchList.append(n)
                                            pitchList.remove(pitchList[0])
                                        else:
                                            pitchList = [n]
                                    else:
                                        if n.pitchClass not in [m.pitchClass for m in pitchList]:
                                            pitchList.append(n)
                                        else:
                                            pitchList = [n]
                                    if len(pitchList) == length:
                                        listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(pitchList), inputStream, p))
                                else:
                                    pitchList = []
                            else:
                                pitchList.append(n)
                                totallength = totallength + len(n.pitches)
                                lengthofactive = totallength
                                donechecking = False
                                numnotestodelete = 0
                                for i in range(0, len(pitchList)):
                                    if donechecking == False:
                                        activePitchList = pitchList[i:len(pitchList)]
                                        if i != 0:
                                            lengthofactive = lengthofactive - len(pitchList[i-1].pitches)
                                        if lengthofactive >= length:
                                            if lengthofactive - len(activePitchList[0].pitches) - len(activePitchList[-1].pitches) <= length - 2:
                                                contigObj = ContiguousSegmentOfNotes(list(activePitchList), inputStream, p)
                                                rowSuperset = contigObj.readPitchClassesFromBottom()
                                                lowerBound = max([0, len(rowSuperset) - length - len(activePitchList[-1].pitches) + 1])
                                                upperBound = min([len(activePitchList[0].pitches) - 1, len(rowSuperset) - length])
                                                added = False
                                                for j in range(lowerBound, upperBound + 1):
                                                    if added == False:   
                                                        if len(set(rowSuperset[j:j+length])) == length:
                                                            listOfContiguousSegments.append(contigObj)
                                                            added = True
                                            else:
                                                numnotestodelete = numnotestodelete + 1
                                        else:
                                            donechecking = True
                                for i in range(0, numnotestodelete):
                                    totallength = totallength - len(pitchList[0].pitches)
                                    pitchList.remove(pitchList[0])
            elif reps == 'includeAll':
                pitchList = []
                totallength = 0
                for m in measures:
                    for n in m.flat.notes:
                        if n.tie == None or n.tie.type == 'start':
                            if includeChords == False:
                                if len(n.pitches) == 1:
                                    pitchList.append(n)
                                    if len(pitchList) == length + 1:
                                        pitchList.remove(pitchList[0])
                                    if len(pitchList) == length:
                                        listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(pitchList), inputStream, p))
                                else:
                                    pitchList = []
                            else:
                                pitchList.append(n)
                                totallength = totallength + len(n.pitches)
                                lengthofactive = totallength
                                donechecking = False
                                numnotestodelete = 0
                                for i in range(0, len(pitchList)):
                                    if donechecking == False:
                                        activePitchList = pitchList[i:len(pitchList)]
                                        if i != 0:
                                            lengthofactive = lengthofactive - len(pitchList[i-1].pitches)
                                        if lengthofactive >= length:
                                            if lengthofactive - len(activePitchList[0].pitches) - len(activePitchList[-1].pitches) <= length - 2:
                                                listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(activePitchList), inputStream, p))
                                            else:
                                                numnotestodelete = numnotestodelete + 1
                                        else:
                                            donechecking = True
                                for i in range(0, numnotestodelete):
                                    totallength = totallength - len(pitchList[0].pitches)
                                    pitchList.remove(pitchList[0])
            elif reps == 'ignoreAll':
                pitchList = []
                totallength = 0
                for m in measures:
                    for n in m.getElementsByClass([note.Note, chord.Chord], returnStreamSubClass=False):
                        if n.tie == None or n.tie.type == 'start':
                            if includeChords == False:
                                if len(n.pitches) == 1:
                                    pitchList.append(n)
                                    donechecking = False
                                    numnotestodelete = 0
                                    for i in range(0, len(pitchList)):
                                        if donechecking == False:
                                            activePitchList = pitchList[i:len(pitchList)]
                                            if len(set([p.pitchClass for p in activePitchList])) == length:
                                                listOfContiguousSegments.append(ContiguousSegmentOfNotes(list(activePitchList), inputStream, p))
#uncomment this line to get shortest            #numnotestodelete = numnotestodelete + 1                                                
                                            elif len(set([p.pitchClass for p in activePitchList])) > length:
                                                numnotestodelete = numnotestodelete + 1
                                            else:
                                                donechecking = True
                                    for i in range(0, numnotestodelete):
                                        totallength = totallength - len(pitchList[0].pitches)
                                        pitchList.remove(pitchList[0])                                                 
                                else:
                                    pitchList = []                            
                            else:
                                pitchList.append(n)
                                donechecking = False
                                numnotestodelete = 0
                                for i in range(0, len(pitchList)):
                                    if donechecking == False:
                                        activePitchList = pitchList[i:len(pitchList)]
                                        activeseg = ContiguousSegmentOfNotes(list(activePitchList), inputStream, p)
                                        if len(set(activeseg.readPitchClassesFromBottom())) >= length:
                                            middleseg = ContiguousSegmentOfNotes(list(activePitchList[1:len(activePitchList)-1]), None, None)
                                            middlePitchClassSet = set(middleseg.readPitchClassesFromBottom())
                                            setToCheck = middlePitchClassSet.union([activePitchList[0].pitches[-1].pitchClass]).union([activePitchList[-1].pitches[0].pitchClass])
                                            if len(setToCheck) <= length:
                                                listOfContiguousSegments.append(activeseg)
#uncomment this line to get shortest            #numnotestodelete = numnotestodelete + 1                                                
                                            else:
                                                numnotestodelete = numnotestodelete + 1                                                
                                        else:
                                            donechecking = True
                                for i in range(0, numnotestodelete):
                                    totallength = totallength - len(pitchList[0].pitches)
                                    pitchList.remove(pitchList[0])
                

            else:
                raise SerialException("Invalid repeated pitch setting.")
            
        
    return listOfContiguousSegments

def _labelGeneral(segmentsToLabel, inputStream, segmentDict, reps, includeChords):
    '''
    Helper function for all but one of the labelling functions below. 
    Private because this should only be called
    in conjunction with one of the find(type of set of pitch classes) functions.
    '''
    
    from operator import attrgetter
    
    if len(inputStream.getElementsByClass(stream.Score)) == 0:
        bigContainer = inputStream
    else:
        bigContainer = inputStream.getElementsByClass(stream.Score)
    if len(bigContainer.getElementsByClass(stream.Part)) == 0:
        hasParts = False
    else:
        parts = bigContainer.getElementsByClass(stream.Part)
        hasParts = True
        
    segmentList = [segmentDict[label] for label in segmentDict]
    labelList = [label for label in segmentDict]
    numSearchSegments = len(segmentList)
    numSegmentsToLabel = len(segmentsToLabel)
    reorderedSegmentsToLabel = sorted(segmentsToLabel, key=attrgetter(
                                                'partNumber', 'startMeasureNumber', 'startOffset'))
    
    for k in range (0, numSegmentsToLabel):
        foundSegment = reorderedSegmentsToLabel[k]          
        linelabel = spanner.Line(foundSegment.segment[0], foundSegment.segment[-1])
        if hasParts == True:
            parts[foundSegment.partNumber].insert(0, linelabel)
        else:
            bigContainer.insert(0, linelabel)
        
        foundLabel = False
        rowToMatch = foundSegment.matchedSegment
        for l in range(0, numSearchSegments):
            if foundLabel == False:
                if segmentList[l] == rowToMatch:
                    foundLabel = True
                    label = labelList[l]
                    firstnote = foundSegment.segment[0]
                    if label not in [lyr.text for lyr in firstnote.lyrics]:
                        firstnote.addLyric(label)
                    
    return inputStream
    

def findSegments(inputStream, searchList, reps='skipConsecutive', includeChords=True):
    '''
    Finds all instances of given contiguous segments of pitch classes within a :class:`~music21.stream.Stream`.
    
    The inputStream is a :class:`~music21.stream.Stream`; as in :func:`~music21.serial.getContiguousSegmentsOfLength`, 
    the inputStream can contain at most one :class:`~music21.stream.Score` and
    its notes must be contained in measures. The searchList is a list of contiguous segments to
    be searched for, each segment being given as a list of pitch classes. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings are the same as those in
    :func:`~music21.serial.getContiguousSegmentsOfLength`.
    
    Returns a list of :class:`~music21.serial.ContiguousSegmentOfNotes` objects for which the
    :attr:`~music21.serial.ContiguousSegmentOfNotes.activeSegment` matches at least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.
    
    
    >>> sc = stream.Score()
    >>> part = stream.Part()
    >>> sig = meter.TimeSignature('2/4')
    >>> part.append(sig)
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
    >>> #_DOCS_SHOW newpart.show()
    
    .. image:: images/serial-findSegments.png
        :width: 500
    
    >>> sc.insert(0, newpart)
    >>> GABandABC = serial.findSegments(sc, [[7, 9, 11], [9, 11, 0]], includeChords = False)
    >>> print(GABandABC)
    [<music21.serial.ContiguousSegmentOfNotes object...]
    >>> len(GABandABC)
    2
    >>> GABandABC[0].segment, GABandABC[1].segment
    ([<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>], 
    [<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>])
    >>> GABandABC[0].startMeasureNumber, GABandABC[1].startMeasureNumber
    (5, 6)
    
    In case it is not clear, we can use the :attr:`~music21.serial.ContiguousSegmentsOfNotes.matchedSegment` property
    to determine, to which element of the original searchList the found contiguous segments were matched.
    
    >>> GABandABC[0].matchedSegment
    [7, 9, 11]
    >>> GABandABC[1].matchedSegment
    [9, 11, 0]
    
    One can also search for segments of different lengths, simultaneously. Below, 'B' refers to the
    pitch class 11, which only coincidentally is the same as that of the note B.
    
    >>> len(serial.findSegments(sc, [[7, 9, 11], ['B', 0]], includeChords = False))
    2
    
    Below, we can see what happens when we include the chords.
    
    >>> [seg.segment for seg in serial.findSegments(newpart, [[5, 7, 'B']], 'ignoreAll')]
    [[<music21.note.Note F>, <music21.chord.Chord G4 B4>]]
    
    As expected, the pitch classes found segment are read in the order 5, 7, 11 ('B'), as the pitches
    in the chord are read from bottom to top.
    
    Consider the following other example with chords, which is somewhat more complex:
    
    >>> sc0 = stream.Score()
    >>> p0 = stream.Part()
    >>> c1 = chord.Chord(['c4', 'd4'])
    >>> c2 = chord.Chord(['e4', 'f4'])
    >>> p0.append(c1)
    >>> p0.append(c2)
    >>> p0 = p0.makeMeasures()
    >>> sc0.insert(0, p0)
    >>> [(seg.segment, seg.activeSegment) for seg in serial.findSegments(sc0, [[0, 2, 4]])]
    [([<music21.chord.Chord C4 D4>, <music21.chord.Chord E4 F4>], [0, 2, 4])]
    >>> [(seg.segment, seg.activeSegment) for seg in serial.findSegments(sc0, [[2, 4, 5]])]
    [([<music21.chord.Chord C4 D4>, <music21.chord.Chord E4 F4>], [2, 4, 5])]
    
    In the two function calls, despite the fact that two different segments of pitch classes were searched for, the same
    :class:`~music21.serial.ContiguousSegmentOfNotes` object was found for each. This is because the found object can be read
    in two ways as a sequence of three pitch classes: either as [0, 2, 4], by taking the two notes of the first chord in order
    and the bottom note of the second, or as [2, 4, 5], by taking the top note of the first chord and the two notes of the second
    chord in order. Both times, the chords are read from bottom to top.
    
    OMIT_FROM_DOCS
    
    >>> for a in serial.findSegments(sc, [[7, -3, 11], [9, 11, 0]], includeChords = False):
    ...    print(a.matchedSegment)
    [7, -3, 11]
    [9, 11, 0]
    >>> len(serial.findSegments(sc, [[7, -3, 11], [9, 11, 0]], includeChords = False))
    2
    
    >>> s = stream.Stream()
    >>> n1 = note.Note('e4')
    >>> n2 = note.Note('f4')
    >>> n3 = note.Note('g4')
    >>> c = chord.Chord(['b4', 'g5', 'a5'])
    >>> s.append(n1)
    >>> s.append(n2)
    >>> s.append(n3)
    >>> s.append(c)
    >>> s = s.makeMeasures()
    >>> [seg.segment for seg in serial.findSegments(s, [[4, -7, 7]], 'ignoreAll')]
    [[<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>]]
    >>> [seg.segment for seg in serial.findSegments(s, [[7, 'B', 9]], 'ignoreAll')]
    [[<music21.note.Note G>, <music21.chord.Chord B4 G5 A5>]]
    
    '''
    
    numsegs = len(searchList)
    segs = []
    donealready = []
    contigdict = {}
    
    for k in range(0,numsegs):
        currentSearchSegment = searchList[k]
        currentSearchSegmentCopy = list(currentSearchSegment)
        used = False
        searchRow = pcToToneRow(currentSearchSegment)
        currentSearchSegment = searchRow.pitchClasses()
        for usedsegment in donealready:
            if used == False:
                used = searchRow.isSameRow(pcToToneRow(usedsegment))
        if used == False:
            donealready.append(currentSearchSegment)
            length = len(currentSearchSegment)
            if length in contigdict:
                contig = contigdict[length]
            else:
                contig = getContiguousSegmentsOfLength(inputStream, length, reps, includeChords)
                contigdict[length] = contig        
            for contiguousseg in contig:
                if reps == 'ignoreAll':
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.getDistinctPitchClasses()
                    matched = False
                    for i in range(0, len(pitchList) - len(currentSearchSegment) + 1):
                        if matched == False:
                            subsetToCheck = pitchList[i:i+length]
                            if currentSearchSegment == subsetToCheck:
                                if subsetToCheck[0] in [p.pitchClass for p in segment[0].pitches]:
                                    startseg = segment[0:len(segment)-1]
                                    if subsetToCheck[-1] not in ContiguousSegmentOfNotes(startseg, None, None).readPitchClassesFromBottom():
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = currentSearchSegmentCopy
                                        segs.append(contiguousseg)
                                            
                else:
                    pitchList = contiguousseg.readPitchClassesFromBottom()
                    segment = contiguousseg.segment
                    matched = False
                    lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                    upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                    for j in range(lowerBound, upperBound + 1):
                        if matched == False:
                            subsetToCheck = pitchList[j:j+length]
                            if subsetToCheck == currentSearchSegment:
                                matched = True
                                contiguousseg.activeSegment = subsetToCheck
                                contiguousseg.matchedSegment = currentSearchSegmentCopy
                                segs.append(contiguousseg)
        
    return segs

        

def labelSegments(inputStream, segmentDict, reps='skipConsecutive', includeChords=True):
    '''
    Labels all instances of a given collection of segments of pitch classes in a
    :class:`~music21.stream.Stream`.
    
    The segmentDict is a dictionary whose keys are names of 
    the segments to be searched for, and whose values are the segments of pitch classes. The values will be
    turned in to a segmentList, as in :func:`~music21.serial.findSegments`.
    All other settings are as in :func:`~music21.serial.findSegments` as well.
    
    Returns a deepcopy of the inputStream with a :class:`~music21.spanner.Line` connecting the first and last notes
    of each found segment, and the first note of each found segment labeled with a :class:`~music21.note.Lyric`,
    the label being the key corresponding to the segment of pitch classes. One should make sure not
    to call this function with too large of a segmentDict, as a note being contained
    in too many segments will result in some spanners not showing.
    
    >>> part = stream.Part()
    >>> sig = meter.TimeSignature('2/4')
    >>> part.append(sig)
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
    
    We can then label the segment of pitch classes [7, 9, 11], which corresponds to a G, followed by an A,
    followed by a B. Let us call this segment "GAB".
    
    >>> labelGAB = serial.labelSegments(newpart, {'GAB':[7, 9, 11]}, includeChords=False)
    >>> #_DOCS_SHOW labelGAB.show()
    
    .. image:: images/serial-labelSegments.png
       :width: 500
    
    OMIT_FROM_DOCS
    
    >>> len(labelGAB.getElementsByClass(spanner.Line))
    1
    
    '''
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [segmentDict[label] for label in segmentDict]
    segmentsToLabel = findSegments(streamCopy, segmentList, reps, includeChords)
    return _labelGeneral(segmentsToLabel, streamCopy, segmentDict, reps, includeChords)
        
def findTransposedSegments(inputStream, searchList, reps='skipConsecutive', includeChords=True):
    
        
    '''
    Finds all instances of given contiguous segments of pitch classes, with transpositions, within a :class:`~music21.stream.Stream`.
    
    The inputStream is a :class:`~music21.stream.Stream`; as in :func:`~music21.serial.getContiguousSegmentsOfLength`, 
    the inputStream can contain at most one :class:`~music21.stream.Score` and
    its notes must be contained in measures. The searchList is a list of contiguous segments to
    be searched for, each segment being given as a list of pitch classes. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings are the same as those in
    :func:`~music21.serial.getContiguousSegmentsOfLength`.
    
    Returns a list of :class:`~music21.serial.ContiguousSegmentOfNotes` objects for which some transposition of the
    :attr:`~music21.serial.ContiguousSegmentOfNotes.activeSegment` matches at least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.
    
    
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
    >>> #_DOCS_SHOW newpart.show()
    
    .. image:: images/serial-findTransposedSegments.png
        :width: 500
        
    First, note that it is impossible, using the 'ignoreAll' setting, to find segments, transposed or not,
    with repeated pitch classes.
    
    >>> serial.findTransposedSegments(newpart, [[0, 0]], 'ignoreAll')
    []
    
    A somewhat more interesting example is below.
    
    >>> halfStepList = serial.findTransposedSegments(newpart, [[0, 1]], 'rowsOnly', includeChords=False)
    >>> L = [step.segment for step in halfStepList]
    >>> print(L)
    [[<music21.note.Note E>, <music21.note.Note F>], [<music21.note.Note B>, <music21.note.Note C>]]
    >>> [step.startMeasureNumber for step in halfStepList]
    [1, 5]
    
    In addition to calling the :attr:`~music21.serial.ContiguousSegmentOfNotes.startMeasureNumber` property
    to return the measure numbers on which the half steps start, one may also call the
    :attr:`~music21.base.Music21Object.measureNumber` property of the first :class:`~music21.note.Note` of each segment.
    
    >>> s = stream.Stream()
    >>> s.repeatAppend(newpart, 2) #s has two parts, each of which is a copy of newpart.
    >>> wholeStepList = serial.findTransposedSegments(s, [[12, 2]], includeChords=False)
    >>> [(step.segment, step.startMeasureNumber, step.partNumber) for step in wholeStepList]
    [([<music21.note.Note G>, <music21.note.Note A>], 3, 0), 
    ([<music21.note.Note A>, <music21.note.Note B>], 3, 0), 
    ([<music21.note.Note G>, <music21.note.Note A>], 3, 1), 
    ([<music21.note.Note A>, <music21.note.Note B>], 3, 1)]
    
    Including chords works similarly as in :class:`~music21.serial.findSegments`.
    
    >>> [seg.segment for seg in serial.findTransposedSegments(newpart, [[4, 6, 'A']])]
    [[<music21.note.Note F>, <music21.chord.Chord G4 B4>]]
    
    OMIT_FROM_DOCS
    
    >>> testSameSeg = serial.findTransposedSegments(newpart, [[12, 13], [0, 1]], 'skipConsecutive', includeChords=False)
    >>> len(testSameSeg)
    2
    >>> testSameSeg[0].matchedSegment
    [12, 13]
    >>> serial.findTransposedSegments(newpart, [[9, 'A', 'B']], 'rowsOnly', includeChords=False)
    []
    
    >>> s = stream.Stream()
    >>> n1 = note.Note('e4')
    >>> n2 = note.Note('f4')
    >>> n3 = note.Note('g4')
    >>> c = chord.Chord(['b4', 'g5', 'a5'])
    >>> s.append(n1)
    >>> s.append(n2)
    >>> s.append(n3)
    >>> s.append(c)
    >>> s = s.makeMeasures()
    >>> [seg.segment for seg in serial.findTransposedSegments(s, [[3, 4, 6]], 'ignoreAll')]
    [[<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>]]
    >>> [seg.segment for seg in serial.findTransposedSegments(s, [[4, 8, 6]], 'ignoreAll')]
    [[<music21.note.Note G>, <music21.chord.Chord B4 G5 A5>]]
    
    '''
    
    numsegs = len(searchList)
    segs = []
    donealready = []
    contigdict = {}

    for k in range(0, numsegs):
        currentSearchSegment = searchList[k]
        row = pcToToneRow([n for n in currentSearchSegment])
        intervals = row.getIntervalsAsString()
        if intervals not in donealready:
            donealready.append(intervals)
            length = len(currentSearchSegment)
            if length in contigdict:
                contig = contigdict[length]
            else:
                contig = getContiguousSegmentsOfLength(inputStream, length, reps, includeChords)
                contigdict[length] = contig
            for contiguousseg in contig:
                if reps == 'ignoreAll':
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.getDistinctPitchClasses()
                    matched = False
                    for i in range(0, len(pitchList) - len(currentSearchSegment) + 1):
                        if matched == False:
                            subsetToCheck = pitchList[i:i+length]
                            subsetToCheckAsRow = pcToToneRow(subsetToCheck)
                            if row.getIntervalsAsString() == subsetToCheckAsRow.getIntervalsAsString():
                                if subsetToCheck[0] in [p.pitchClass for p in segment[0].pitches]:
                                    startseg = segment[0:len(segment)-1]
                                    if subsetToCheck[-1] not in ContiguousSegmentOfNotes(startseg, None, None).readPitchClassesFromBottom():
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = currentSearchSegment
                                        segs.append(contiguousseg)
                else:
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.readPitchClassesFromBottom()
                    matched = False
                    lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                    upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                    for j in range(lowerBound, upperBound + 1):
                        if matched == False:
                            subsetToCheck = pitchList[j:j+length]
                            if intervals == pcToToneRow(pitchList).getIntervalsAsString():
                                matched = True
                                contiguousseg.activeSegment = subsetToCheck
                                contiguousseg.matchedSegment = currentSearchSegment
                                segs.append(contiguousseg)
    return segs

def labelTransposedSegments(inputStream, segmentDict, reps='skipConsecutive', includeChords=True):
    '''
    Labels all instances of a given collection of segments of pitch classes,
    with transpositions, in a :class:`~music21.stream.Stream`.
    
    The segmentDict is a dictionary whose keys are names of the segments to be
    searched for, and whose values are the segments of pitch classes. The
    values will be turned in to a segmentList, as in
    :func:`~music21.serial.findTransposedSegments`.  All other settings are as
    in :func:`~music21.serial.findTransposedSegments` as well.
    
    Returns a deep copy of the inputStream with a
    :class:`~music21.spanner.Line` connecting the first and last notes of each
    found segment, and the first note of each found segment labeled with a
    :class:`~music21.note.Lyric`, the label being the key corresponding to the
    segment of pitch classes. One should make sure not to call this function 
    with too large of a segmentDict, as a note being contained in too many 
    segments will result in some spanners not showing.
    
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

    We have a soprano line; let us now form a bass line.
    
    >>> bass = stream.Part()
    >>> n8 = note.Note('c3')
    >>> n8.quarterLength = 4
    >>> bass.append(n8)
    >>> r1 = note.Rest()
    >>> r1.quarterLength = 4
    >>> bass.append(r1)
    >>> n9 = note.Note('b2')
    >>> n9.quarterLength = 4
    >>> bass.append(n9)
    >>> r2 = note.Rest()
    >>> r2.quarterLength = 4
    >>> bass.append(r2)
    >>> n10 = note.Note('c3')
    >>> n10.quarterLength = 4
    >>> bass.append(n10)
    >>> newbass = bass.makeMeasures()
    >>> sc = stream.Score()
    >>> import copy
    >>> sc.insert(0, copy.deepcopy(newpart))
    >>> sc.insert(0, copy.deepcopy(newbass))
    >>> labeledsc = serial.labelTransposedSegments(sc, {'half':[0, 1]}, 'rowsOnly')
    >>> #_DOCS_SHOW labeledsc.show()

    .. image:: images/serial-labelTransposedSegments.png
       :width: 500
        
    OMIT_FROM_DOCS
    
    >>> len(labeledsc.parts[0].getElementsByClass(spanner.Line))
    2    
    '''
    
    
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [segmentDict[label] for label in segmentDict]
    segmentsToLabel = findTransposedSegments(streamCopy, segmentList, reps, includeChords)
    return _labelGeneral(segmentsToLabel, streamCopy, segmentDict, reps, includeChords)

def findTransformedSegments(inputStream, searchList, reps='skipConsecutive', includeChords='skipChords'):
    
    '''
    Finds all instances of given contiguous segments of pitch classes, with serial transformations,
    within a :class:`~music21.stream.Stream`.
    
    The inputStream is :class:`~music21.stream.Stream`; as in :func:`~music21.serial.getContiguousSegmentsOfLength`,
    the inputStream can 
    contain at most one :class:`~music21.stream.Score` 
    and its notes must be contained in measures. The searchList is a list of contiguous segments to
    be searched for, each segment being given as a list of pitch classes. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings are the same as those in
    :func:`~music21.serial.getContiguousSegmentsOfLength`. The convention for serial transformations must be specified to either
    'zero' or 'original', as described in :meth:`~music21.serial.zeroCenteredTransformation` and
    :func:`~music21.serial.originalCenteredTransformation` - the default setting is 'original', as to relate found segments
    directly to the given segments, without first transposing the given segment to begin on the pitch class 0.
    
    Returns a list of :class:`~music21.serial.ContiguousSegmentOfNotes` objects for which some transformation of the
    :attr:`~music21.serial.ContiguousSegmentOfNotes.activeSegment` matches at least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.
    
    
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
    >>> #_DOCS_SHOW part.show()
    
    .. image:: images/serial-findTransformedSegments.png
        :width: 150
    
    >>> row = [2, 5, 4]    
    >>> rowInstances = serial.findTransformedSegments(part, [row], 'rowsOnly', includeChords=False)
    >>> len(rowInstances)
    2
    >>> firstInstance = rowInstances[0]
    >>> firstInstance.activeSegment, firstInstance.startMeasureNumber
    ([1, 4, 3], 1)
    >>> firstInstance.originalCenteredTransformationsFromMatched
    [('T', 11)]
    
    We have thus found that the first instance of the row [2, 5, 4] within our stream appears as a transposition
    down a semitone, beginning in measure 1. We can do a similar analysis on the other instance of the row.
    
    >>> secondInstance = rowInstances[1]
    >>> secondInstance.activeSegment, secondInstance.startMeasureNumber
    ([5, 4, 7], 1)
    >>> secondInstance.zeroCenteredTransformationsFromMatched
    [('RI', 7)]
    
    Let us give an example of this function used with chords included and reps set to 'ignoreAll'.
    
    >>> s = stream.Stream()
    >>> n1 = note.Note('e4')
    >>> n2 = note.Note('f4')
    >>> n3 = note.Note('g4')
    >>> c = chord.Chord(['b4', 'g5', 'a5'])
    >>> s.append(n1)
    >>> s.append(n2)
    >>> s.append(n3)
    >>> s.append(c)
    >>> s = s.makeMeasures()
    >>> [seg.segment for seg in serial.findTransformedSegments(s, [[6, 4, 3]], 'ignoreAll')]
    [[<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>]]
    >>> [seg.segment for seg in serial.findTransformedSegments(s, [[6, 8, 4]], 'ignoreAll')]
    [[<music21.note.Note G>, <music21.chord.Chord B4 G5 A5>], [<music21.chord.Chord B4 G5 A5>]]
    >>> [seg.activeSegment for seg in serial.findTransformedSegments(s, [[6, 8, 4]], 'ignoreAll')]
    [[7, 11, 9], [11, 7, 9]]
    >>> [seg.originalCenteredTransformationsFromMatched for seg in serial.findTransformedSegments(s, [[6, 8, 4]], 'ignoreAll')]
    [[('R', 3)], [('RI', 3)]]
    
    Pitch classes are extracted from segments in order of appearance, with pitches in chords being read from bottom to top.
    However, only the first instance of each pitch class is considered, as seen in the
    :attr:`~music21.serial.ContiguousSegmentOfNotes.activeSegment` calls. As long as the first and last pitch classes in the
    active segment first appear in the first and last elements of the found segment, respectively, the segment will be matched to the
    segment being searched for. To make this more clear, consider the following example in the same stream s:
    
    >>> [(seg.segment, seg.activeSegment) for seg in serial.findTransformedSegments(s, [[4, 0, 4]], 'includeAll')]
    [([<music21.note.Note G>, <music21.chord.Chord B4 G5 A5>], [7, 11, 7])]
    
    Above, the pitch classes of the found segment are read in the order 7, 11, 7, 9. Because a subsequence of this, [7, 11, 7],
    is an inversion of the search segment, [4, 0, 4], and furthermore, the first 7 is part of the first note of the segment (G), and
    the last 7 is part of the last chord of the segment, the found segment is matched to the segment being searched for.
    
    OMIT_FROM_DOCS
    
    >>> s = stream.Stream()
    >>> s.repeatAppend(part, 2)
    >>> testNegativePitchClass = serial.findTransformedSegments(s, [[2, -7, 4]], includeChords=False)
    >>> len(testNegativePitchClass)
    4
    >>> testNegativePitchClass[0].matchedSegment
    [2, -7, 4]

    '''
    
    numsegs = len(searchList)
    segs = []
    donealready = []
    contigdict = {}
    
    for k in range(0, numsegs):
        currentSearchSegment = searchList[k]
        row = pcToToneRow(currentSearchSegment)
        used = False
        for usedrow in donealready:
            if used == False:
                if row.findZeroCenteredTransformations(pcToToneRow(usedrow)) != []:
                    used = True
        if used == False:
            donealready.append(currentSearchSegment)
            length = len(currentSearchSegment)
            if length in contigdict:
                contig = contigdict[length]
            else:
                contig = getContiguousSegmentsOfLength(inputStream, length, reps, includeChords)
                contigdict[length] = contig    
            for contiguousseg in contig:
                if reps == 'ignoreAll':
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.getDistinctPitchClasses()
                    matched = False
                    for i in range(0, len(pitchList) - len(currentSearchSegment) + 1):
                        if matched == False:
                            subsetToCheck = pitchList[i:i+length]
                            subsetToCheckAsRow = pcToToneRow(subsetToCheck)
                            transformations = row.findZeroCenteredTransformations(subsetToCheckAsRow)
                            if transformations != []:
                                if subsetToCheck[0] in [p.pitchClass for p in segment[0].pitches]:
                                    startseg = segment[0:len(segment)-1]
                                    if subsetToCheck[-1] not in ContiguousSegmentOfNotes(startseg, None, None).readPitchClassesFromBottom():
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = currentSearchSegment
                                        segs.append(contiguousseg)
                else:
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.readPitchClassesFromBottom()
                    matched = False
                    lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                    upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                    for j in range(lowerBound, upperBound + 1):
                        if matched == False:
                            subsetToCheck = pitchList[j:j+length]
                            contiguoussegrow = pcToToneRow(subsetToCheck)
                            transformations = row.findZeroCenteredTransformations(contiguoussegrow)
                            if transformations != []:
                                matched = True
                                contiguousseg.activeSegment = subsetToCheck
                                contiguousseg.matchedSegment = currentSearchSegment
                                segs.append(contiguousseg)
    return segs

def labelTransformedSegments(inputStream, segmentDict, reps='skipConsecutive', chords = 'skipChords', convention = 'original'):
    
    '''
    Labels all instances of a given collection of segments of pitch classes,
    with transformations, in a :class:`~music21.stream.Stream`.
    
    The segmentDict is a dictionary whose keys are names of the segments to be 
    searched for, and whose values are the segments of pitch classes. The 
    values will be turned in to a segmentList, as in 
    :func:`~music21.serial.findTransposedSegments`. The last argument specifies
    the convention ('zero' or 'original') used for naming serial 
    transformations, as explained in 
    :meth:`~music21.serial.ToneRow.zeroCenteredTransformation` and
    :meth:`~music21.serial.ToneRow.originalCenteredTransformation`.

    All other settings are as in :func:`~music21.serial.findTransposedSegments`
    as well.
    
    Returns a deep copy of the inputStream with a 
    :class:`~music21.spanner.Line` connecting the first and last notes of each
    found segment, and the first note of each found segment labeled with a 
    :class:`~music21.note.Lyric`, the label being the key corresponding to the 
    segment of pitch classes. One should make sure not to call this function 
    with too large of a segmentDict, as a note being contained in too many
    segments will result in some spanners not showing.
    
    >>> c1 = chord.Chord(['c#4', 'e4'])
    >>> c2 = chord.Chord(['d#4', 'f4'])
    >>> c3 = chord.Chord(['e4', 'g4'])
    >>> chordList = [c1, c2, c3]
    >>> part = stream.Part()
    >>> for c in chordList:
    ...    c.quarterLength = 4
    ...    part.append(c)
    >>> part = part.makeMeasures()
    >>> labeledPart = serial.labelTransformedSegments(part, {'row':[2, 5, 4]})
    >>> #_DOCS_SHOW labeledPart.show()
    
    .. image:: images/serial-labelTransformedSegments.png
       :width: 500
    
    Note: the spanners above were moved manually so that they can be more easily distinguished from one another.
    
    OMIT_FROM_DOCS
    
    >>> [len(n.lyrics) for n in labeledPart.flat.notes]
    [1, 1, 0]
    
    '''
    
    from operator import attrgetter
    
    streamCopy = copy.deepcopy(inputStream)
    
    #this doesn't call _labelGeneral because each segment is also labeled with the transformations.
    if len(streamCopy.getElementsByClass(stream.Score)) == 0:
        bigContainer = streamCopy
    else:
        bigContainer = streamCopy.getElementsByClass(stream.Score)
    if len(bigContainer.getElementsByClass(stream.Part)) == 0:
        hasParts = False
    else:
        parts = bigContainer.getElementsByClass(stream.Part)
        hasParts = True
        
    segmentList = [segmentDict[label] for label in segmentDict]
    labelList = [label for label in segmentDict]
    numSearchSegments = len(segmentList)
    segmentsToLabel = findTransformedSegments(streamCopy, segmentList, reps, chords)
    numSegmentsToLabel = len(segmentsToLabel)
    reorderedSegmentsToLabel = sorted(segmentsToLabel, key = attrgetter('partNumber', 'startMeasureNumber', 'startOffset'))
    
    for k in range (0, numSegmentsToLabel):
        foundSegment = reorderedSegmentsToLabel[k]          
        linelabel = spanner.Line(foundSegment.segment[0], foundSegment.segment[-1])
        if hasParts == True:
            parts[foundSegment.partNumber].insert(0, linelabel)
        else:
            bigContainer.insert(0, linelabel)
        
        foundLabel = False
        rowToMatch = foundSegment.matchedSegment
        for l in range(0, numSearchSegments):
            if foundLabel == False:
                if segmentList[l] == rowToMatch:
                    foundLabel = True
                    label = labelList[l]
                    firstnote = foundSegment.segment[0]
                    if convention == 'original':
                        transformations = foundSegment.originalCenteredTransformationsFromMatched
                    elif convention == 'zero':
                        transformations = foundSegment.zeroCenteredTransformationsFromMatched
                    else:
                        raise SerialException("Invalid convention - choose 'zero' or 'original'.")
                    for trans in transformations:
                        label = label + ' ,' + str(trans[0]) + str(trans[1])
                    if label not in [lyr.text for lyr in firstnote.lyrics]:
                        firstnote.addLyric(label)
                    
    return streamCopy

def _checkMultisetEquivalence(multiset1, multiset2):
    
    '''
    Boolean describing if two multisets of pitch classes are the same.
    
    
    >>> serial._checkMultisetEquivalence([3, 4, 5], [3, 3, 4, 5])
    False
    >>> serial._checkMultisetEquivalence([10, 'A', -7], [-2, 5, -2])
    True
    '''
    
    if len(multiset1) != len(multiset2):
        return False
    else:
        
        row1 = pcToToneRow(multiset1)
        multiset1 = row1.pitchClasses()
        
        row2 = pcToToneRow(multiset2)
        multiset2 = row2.pitchClasses()
        
        uniqueelements = set(multiset1)
        tempsame = True
        for i in uniqueelements:
            if tempsame == True:
                if multiset1.count(i) != multiset2.count(i):
                    tempsame = False
        return tempsame
            
def findMultisets(inputStream, searchList, reps='skipConsecutive', includeChords=True):
    
    '''
    Finds all instances of given multisets of pitch classes within a :class:`~music21.stream.Stream`. A multiset
    is a generalization of a set, in which the order of the elements in the multiset does not matter, but multiple instances
    of the same thing (in this case, same pitch class) are treated as distinct elements. Thus, two multisets of pitch classes
    are considered to be equal if and only if the number of times any given pitch class appears in one multiset is the same as
    the number of times the pitch class appears in the other multiset.

    The inputStream is :class:`~music21.stream.Stream`; as in :func:`~music21.serial.getContiguousSegmentsOfLength`,
    the inputStream can contain at most one :class:`~music21.stream.Score`
    its notes must be contained in measures. However, the inputStream may have
    multiple parts. The searchList is a list of multisets to
    be searched for, each multiset being given as a list of pitch classes. Note that the order of pitch classes given in a multiset
    does not matter. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings are the same as those in
    :func:`~music21.serial.getContiguousSegmentsOfLength`.
    
    Returns a list of :class:`~music21.serial.ContiguousSegmentOfNotes` objects for the
    :attr:`~music21.serial.ContiguousSegmentOfNotes.activeSegment`, interpreted as a multiset,
    matches at least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.
    
    
    >>> part = stream.Part()
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 4
    >>> n2 = note.Note('e4')
    >>> n2.quarterLength = 4
    >>> n3 = note.Note('f4')
    >>> n3.quarterLength = 4
    >>> n4 = note.Note('e4')
    >>> n4.quarterLength = 4
    >>> part.append(n1)
    >>> part.append(n2)
    >>> part.append(n3)
    >>> part.append(n4)
    >>> part.makeMeasures(inPlace = True)
    >>> part.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note E>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.note.Note E>
    {8.0} <music21.stream.Measure 3 offset=8.0>
        {0.0} <music21.note.Note F>
    {12.0} <music21.stream.Measure 4 offset=12.0>
        {0.0} <music21.note.Note E>
        {4.0} <music21.bar.Barline style=final>
            
    >>> #_DOCS_SHOW part.show()
    
    .. image:: images/serial-findMultisets.png
        :width: 150
    
    
    Find all instances of the multiset [5,4,4] in the part
    
    >>> EEF = serial.findMultisets(part, [[5, 4, 4]], 'includeAll', includeChords=False)
    >>> [(seg.activeSegment, seg.startMeasureNumber) for seg in EEF]
    [([4, 4, 5], 1), ([4, 5, 4], 2)]
    >>> EF = serial.findMultisets(part, [[4, 5]], 'ignoreAll')
    >>> [seg.segment for seg in EF]
    [[<music21.note.Note E>, <music21.note.Note E>, <music21.note.Note F>], 
    [<music21.note.Note E>, <music21.note.Note F>], 
    [<music21.note.Note E>, <music21.note.Note E>, <music21.note.Note F>, <music21.note.Note E>], 
    [<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note E>], 
    [<music21.note.Note F>, <music21.note.Note E>]]    
    
    Consider the following examples, with chords.
    
    >>> sc0 = stream.Score()
    >>> part0 = stream.Part()
    >>> part0.append(note.Note('c4'))
    >>> part0.append(note.Note('d4'))
    >>> part0.append(note.Note('e4'))
    >>> part0.append(chord.Chord(['f4', 'e5']))
    >>> part0 = part0.makeMeasures()
    >>> sc0.insert(0, part0)
    >>> [seg.segment for seg in serial.findMultisets(sc0, [[0, 2, 4]], 'ignoreAll')]
    [[<music21.note.Note C>, <music21.note.Note D>, <music21.note.Note E>]]
    
    Also:
    
    >>> sc1 = stream.Score()
    >>> part1 = stream.Part()
    >>> part1.append(note.Note('c4'))
    >>> part1.append(note.Note('d4'))
    >>> part1.append(chord.Chord(['e4', 'f4']))
    >>> part1 = part1.makeMeasures()
    >>> sc1.insert(0, part1)
    >>> [seg.getDistinctPitchClasses() for seg in serial.getContiguousSegmentsOfLength(sc1, 3)]
    [[0, 2, 4, 5], [2, 4, 5]]
    >>> serial.findMultisets(sc1, [[0, 2, 5]])
    []
    
    OMIT_FROM_DOCS
    
    >>> s = stream.Stream()
    >>> s.repeatAppend(part, 2)
    >>> serial.findMultisets(part, [[5, 4, 4]], 'rowsOnly')
    []
    >>> testMultiple = serial.findMultisets(s, [[-7, 16, 4], [5, 4, 4]], 'includeAll', includeChords=False)
    >>> len(testMultiple)
    4
    >>> testMultiple[0].matchedSegment
    [-7, 16, 4]
    
    >>> sc = stream.Score()
    >>> part = stream.Part()
    >>> part.append(note.Note('c4'))
    >>> part.append(note.Note('d4'))
    >>> part.append(note.Note('e4'))
    >>> part.append(chord.Chord(['f4', 'e5']))
    >>> part = part.makeMeasures()
    >>> sc.insert(0, part)
    >>> [seg.segment for seg in serial.findMultisets(sc, [[0, 2, 4]], 'ignoreAll')]
    [[<music21.note.Note C>, <music21.note.Note D>, <music21.note.Note E>]]

    
    '''
    
    nummultisets = len(searchList)
    multisets = []
    donealready = []
    contigdict = {}
    
    for k in range(0, nummultisets):
        multiset = searchList[k]
        length = len(multiset)
        used = False
        for usedset in donealready:
            if used == False:
                if _checkMultisetEquivalence(usedset, multiset) == True:
                    used = True
        if used == False:
            donealready.append(multiset)
            length = len(multiset)
            if length in contigdict:
                contig = contigdict[length]
            else:
                contig = getContiguousSegmentsOfLength(inputStream, length, reps, includeChords)
                contigdict[length] = contig
            for contiguousseg in contig:
                if reps == 'ignoreAll':
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.getDistinctPitchClasses()
#                    if len(set([p.pitchClass for p in segment[0].pitches]) and set(multiset)) != 0:
#                        if len(set([p.pitchClass for p in segment[-1].pitches]) and set(multiset)) != 0:
                    matched = False
                    for i in range(0, len(pitchList) - len(multiset) + 1):
                        if matched == False:
                            subsetToCheck = pitchList[i:i+len(multiset)]
                            if _checkMultisetEquivalence(multiset, subsetToCheck) == True:
                                if len(segment) == 1:
                                    matched = True
                                    contiguousseg.activeSegment = subsetToCheck
                                    contiguousseg.matchedSegment = multiset
                                    multisets.append(contiguousseg)
                                else:
                                    multiset = pcToToneRow(multiset).pitchClasses()
                                    if segment[0].pitches[-1].pitchClass in multiset:
                                        if segment[-1].pitches[0].pitchClass in multiset:
                                            middleseg = ContiguousSegmentOfNotes(list(segment[1:len(segment)-1]), None, None)
                                            # environLocal.warn("" + str(middleseg.startMeasureNumber))
                                            listOfPitchClasses = middleseg.readPitchClassesFromBottom()
                                            doneAddingFirst = False
                                            firstChordPitches = segment[0].pitches
                                            for j in range(1, len(firstChordPitches) + 1):
                                                if doneAddingFirst == False:
                                                    if firstChordPitches[-j].pitchClass in multiset:
                                                        listOfPitchClasses.append(firstChordPitches[-j].pitchClass)
                                                    else:
                                                        doneAddingFirst = True
                                            doneAddingLast = False
                                            lastChordPitches = segment[-1].pitches
                                            for k in range(0, len(lastChordPitches)):
                                                if doneAddingLast == False:
                                                    if lastChordPitches[k].pitchClass in multiset:
                                                        listOfPitchClasses.append(lastChordPitches[k].pitchClass)
                                                    else:
                                                        doneAddingLast = True
                                            if set(listOfPitchClasses) == set(multiset):
                                                matched = True
                                                contiguousseg.activeSegment = subsetToCheck
                                                contiguousseg.matchedSegment = multiset
                                                multisets.append(contiguousseg)
                else:
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.readPitchClassesFromBottom()
                    matched = False
                    lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                    upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                    for j in range(lowerBound, upperBound + 1):
                        if matched == False:
                            subsetToCheck = pitchList[j:j+length]
                            if _checkMultisetEquivalence(subsetToCheck, multiset) == True:
                                matched = True
                                contiguousseg.activeSegment = subsetToCheck
                                contiguousseg.matchedSegment = multiset
                                multisets.append(contiguousseg)
    return multisets

def labelMultisets(inputStream, multisetDict, reps='skipConsecutive', includeChords=True):
    
    '''
    
    Labels all instances of a given collection of multisets of pitch classes in a
    :class:`~music21.stream.Stream`. A multiset
    is a generalization of a set, as described in :meth:`~music21.serial.findMultisets`.
    
    The multisetDict is a dictionary whose keys are names of 
    the multisets to be searched for, and whose values are the segments of pitch classes. The values will be
    turned in to a segmentList, as in :func:`~music21.serial.findMultisets`.
    All other settings are as in :func:`~music21.serial.findMultisets` as well.
    
    Returns a deep copy of the inputStream with a :class:`~music21.spanner.Line` connecting the first and last notes
    of each found multiset, and the first note of each found multiset labeled with a :class:`~music21.note.Lyric`,
    the label being the key corresponding to the segment of pitch classes. One should make sure not
    to call this function with too large of a segmentDict, as a note being contained
    in too many segments will result in some spanners not showing.
    
    At the present time a relatively large number of multisets are found using the 'ignoreAll' setting,
    particularly when there are many repetitions of pitch classes (immediate or otherwise).
    As a result, it is possible that at points in the stream there will be more than six spanners active 
    simultaneously, which may result in some spanners not showing correctly in XML format, or not at all.
    
    
    >>> part = stream.Part()
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 4
    >>> n2 = note.Note('e4')
    >>> n2.quarterLength = 4
    >>> n3 = note.Note('f4')
    >>> n3.quarterLength = 4
    >>> n4 = note.Note('e4')
    >>> n4.quarterLength = 4
    >>> part.append(n1)
    >>> part.append(n2)
    >>> part.append(n3)
    >>> part.append(n4)
    >>> part = part.makeMeasures()
    >>> labeledPart = serial.labelMultisets(part, {'EEF':[4, 5, 4]}, reps='includeAll', includeChords=False)
    >>> #_DOCS_SHOW labeledPart.show()
    
    .. image:: images/serial-labelMultisets.png
        :width: 500
        
    Note: the spanners above were moved manually so that they can be more easily distinguished from one another.
    
    OMIT_FROM_DOCS
    
    >>> [len(n.lyrics) for n in labeledPart.flat.notes]
    [1, 1, 0, 0]
    
    '''

    
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [multisetDict[label] for label in multisetDict]
    segmentsToLabel = findMultisets(streamCopy, segmentList, reps, includeChords)
    return _labelGeneral(segmentsToLabel, streamCopy, multisetDict, reps, includeChords)    
    
def findTransposedMultisets(inputStream, searchList, reps='skipConsecutive', includeChords=True):
    
    '''
    
    Finds all instances of given multisets of pitch classes, with transpositions, within a :class:`~music21.stream.Stream`. A multiset
    is a generalization of a set, as described in :meth:`~music21.serial.findMultisets`.

    The inputStream is :class:`~music21.stream.Stream`; as in :func:`~music21.serial.getContiguousSegmentsOfLength`,
    the inputStream can contain at most one :class:`~music21.stream.Score` and its notes must be contained in measures. 
    The searchList is a list of multisets to
    be searched for, each multiset being given as a list of pitch classes. Note that the order of pitch classes given in a multiset
    does not matter. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings are the same as those in
    :func:`~music21.serial.getContiguousSegmentsOfLength`.
    
    Returns a list of :class:`~music21.serial.ContiguousSegmentOfNotes` objects for some transposition of the 
    :attr:`~music21.serial.ContiguousSegmentOfNotes.activeSegment`, interpreted as a multiset,
    matches at least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.
    
    
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
    >>> #_DOCS_SHOW part.show()
    
    .. image:: images/serial-findTransposedMultisets.png
        :width: 500
    
    >>> instanceList = serial.findTransposedMultisets(part, [[-9, -10, -11]], includeChords=False)
    >>> for instance in instanceList:
    ...    (instance.activeSegment, instance.startMeasureNumber, instance.matchedSegment)
    ([2, 4, 3], 3, [-9, -10, -11])
    ([3, 4, 2], 5, [-9, -10, -11])
    ([0, 1, 2], 1, [-9, -10, -11])
    
    OMIT_FROM_DOCS
    
    
    >>> part2 = stream.Part()
    >>> n1 = chord.Chord(['c4', 'c5'])
    >>> n2 = chord.Chord(['c#4', 'c#5'])
    >>> n3 = chord.Chord(['d4', 'd5'])
    >>> n4 = chord.Chord(['e4', 'e5'])
    >>> n5 = chord.Chord(['e-4', 'e-5'])
    >>> n6 = chord.Chord(['e4', 'e5'])
    >>> n7 = chord.Chord(['d4', 'd5'])
    >>> for n in [n1, n2, n3, n4, n5, n6, n7]:
    ...    n.quarterLength = 1
    ...    part2.append(n)
    >>> part2 = part2.makeMeasures()
    >>> instanceList2 = serial.findTransposedMultisets(part2, [[-9, -10, -11]], 'ignoreAll')
    >>> [seg.segment for seg in instanceList2]
    [[<music21.chord.Chord D4 D5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord E-4 E-5>], 
    [<music21.chord.Chord D4 D5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord E-4 E-5>, <music21.chord.Chord E4 E5>], 
    [<music21.chord.Chord D4 D5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord E-4 E-5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord D4 D5>], 
    [<music21.chord.Chord E4 E5>, <music21.chord.Chord E-4 E-5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord D4 D5>], 
    [<music21.chord.Chord E-4 E-5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord D4 D5>], 
    [<music21.chord.Chord C4 C5>, <music21.chord.Chord C#4 C#5>, <music21.chord.Chord D4 D5>]]
    >>> [seg.matchedSegment for seg in instanceList2]
    [[-9, -10, -11], [-9, -10, -11], [-9, -10, -11], [-9, -10, -11], [-9, -10, -11], [-9, -10, -11]]
    
    
        
    '''
    
    nummultisets = len(searchList)
    multisets = []
    donealready = []
    contigdict = {}
    
    for k in range(0, nummultisets):
        baseMultiset = searchList[k]
        baseMultisetPitchClasses = pcToToneRow(baseMultiset).pitchClasses()
        for l in range(0, 12):
            multiset = [(l + x) % 12 for x in baseMultisetPitchClasses]
            length = len(multiset)
            used = False
            for usedset in donealready:
                if used == False:
                    if _checkMultisetEquivalence(usedset, multiset) == True:
                        used = True
            if used == False:
                donealready.append(multiset)
                length = len(multiset)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    contig = getContiguousSegmentsOfLength(inputStream, length, reps, includeChords)
                    contigdict[length] = contig
                for contiguousseg in contig:
                    if reps == 'ignoreAll':
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.getDistinctPitchClasses()
    #                    if len(set([p.pitchClass for p in segment[0].pitches]) and set(multiset)) != 0:
    #                        if len(set([p.pitchClass for p in segment[-1].pitches]) and set(multiset)) != 0:
                        matched = False
                        for i in range(0, len(pitchList) - len(multiset) + 1):
                            if matched == False:
                                subsetToCheck = pitchList[i:i+len(multiset)]
                                if _checkMultisetEquivalence(multiset, subsetToCheck) == True:
                                    if len(segment) == 1:
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = baseMultiset
                                        multisets.append(contiguousseg)
                                    else:
                                        multiset = pcToToneRow(multiset).pitchClasses()
                                        if segment[0].pitches[-1].pitchClass in multiset:
                                            if segment[-1].pitches[0].pitchClass in multiset:
                                                middleseg = ContiguousSegmentOfNotes(list(segment[1:len(segment)-1]), None, None)
                                                listOfPitchClasses = middleseg.readPitchClassesFromBottom()
                                                doneAddingFirst = False
                                                firstChordPitches = segment[0].pitches
                                                for j in range(1, len(firstChordPitches) + 1):
                                                    if doneAddingFirst == False:
                                                        if firstChordPitches[-j].pitchClass in multiset:
                                                            listOfPitchClasses.append(firstChordPitches[-j].pitchClass)
                                                        else:
                                                            doneAddingFirst = True
                                                doneAddingLast = False
                                                lastChordPitches = segment[-1].pitches
                                                for k in range(0, len(lastChordPitches)):
                                                    if doneAddingLast == False:
                                                        if lastChordPitches[k].pitchClass in multiset:
                                                            listOfPitchClasses.append(lastChordPitches[k].pitchClass)
                                                        else:
                                                            doneAddingLast = True
                                                if set(listOfPitchClasses) == set(multiset):
                                                    matched = True
                                                    contiguousseg.activeSegment = subsetToCheck
                                                    contiguousseg.matchedSegment = baseMultiset
                                                    multisets.append(contiguousseg)
                    else:
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.readPitchClassesFromBottom()
                        matched = False
                        lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                        upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                        for j in range(lowerBound, upperBound + 1):
                            if matched == False:
                                subsetToCheck = pitchList[j:j+length]
                                if _checkMultisetEquivalence(subsetToCheck, multiset) == True:
                                    matched = True
                                    contiguousseg.activeSegment = subsetToCheck
                                    contiguousseg.matchedSegment = baseMultiset
                                    multisets.append(contiguousseg)
                                    
    return multisets

def labelTransposedMultisets(inputStream, multisetDict, reps='skipConsecutive', includeChords=True):
    '''
    Labels all instances of a given collection of multisets, with 
    transpositions, of pitch classes in a :class:`~music21.stream.Stream`.

    A multiset is a generalization of a set, as described in 
    :meth:`~music21.serial.findMultisets`.
    
    The multisetDict is a dictionary whose keys are names of the multisets to 
    be searched for, and whose values are the segments of pitch classes. The 
    values will be turned in to a segmentList, as in 
    :func:`~music21.serial.findMultisets`.

    All other settings are as in 
    :func:`~music21.serial.findTransposedMultisets` as well.
    
    Returns a deep copy of the inputStream with a 
    :class:`~music21.spanner.Line` connecting the first and last notes of each 
    found multiset, and the first note of each found multiset labeled with a 
    :class:`~music21.note.Lyric`, the label being the key corresponding to the 
    segment of pitch classes. One should make sure not to call this function 
    with too large of a segmentDict, as a note being contained in too many 
    segments will result in some spanners not showing.
    
    At the present time a relatively large number of multisets are found using 
    the 'ignoreAll' setting, particularly when there are many repetitions of 
    pitch classes (immediate or otherwise). As a result, it is possible that at 
    points in the stream there will be more than six spanners active 
    simultaneously, which may result in some spanners not showing correctly in 
    XML format, or not at all.
    
    As a diversion, instead of using this tool on atonal music, let us do so on 
    Bach.
    
    We can label all instances of three of the same pitch classes occurring in 
    a row in one of the chorales.
    
    We learn the obvious - it appears that the alto section would be the most 
    bored while performing this chorale.
    
    >>> bach = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW serial.labelTransposedMultisets(bach, {'x3':[0, 0, 0]}, reps='includeAll', includeChords=False).show()
    
    .. image:: images/serial-labelTransposedMultisets.png
        :width: 500
    
    Note: the spanners above were moved manually so that they can be more 
    easily distinguished from one another.
    '''
    
    
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [multisetDict[label] for label in multisetDict]
    segmentsToLabel = findTransposedMultisets(streamCopy, segmentList, reps, includeChords)
    return _labelGeneral(segmentsToLabel, streamCopy, multisetDict, reps, includeChords)    
    

def findTransposedAndInvertedMultisets(inputStream, searchList, reps='skipConsecutive', includeChords=True):
    
    '''
    
    Finds all instances of given multisets of pitch classes, with transpositions and inversions, within a :class:`~music21.stream.Stream`. 
    A multiset is a generalization of a set, as described in :meth:`~music21.serial.findMultisets`.

    The inputStream is :class:`~music21.stream.Stream`; as in :func:`~music21.serial.getContiguousSegmentsOfLength`,
    it can contain at most one :class:`~music21.stream.Score`, and
    its notes must be contained in measures. The multisetList is a list of multisets to
    be searched for, each multiset being given as a list of pitch classes. Note that the order of pitch classes given in a multiset
    does not matter. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings are the same as those in
    :func:`~music21.serial.getContiguousSegmentsOfLength`.
    
    Returns a list of :class:`~music21.serial.ContiguousSegmentOfNotes` objects for some transposition or inversion of the 
    :attr:`~music21.serial.ContiguousSegmentOfNotes.activeSegment`, interpreted as a multiset,
    matches at least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.
    
    
    >>> s = stream.Stream()
    >>> n1 = note.Note('c4')
    >>> n2 = note.Note('e-4')
    >>> n3 = note.Note('g4')
    >>> n4 = note.Note('e4')
    >>> n5 = note.Note('c4')
    >>> for n in [n1, n2, n3, n4]:
    ...     n.quarterLength = 1
    ...     s.append(n)
    >>> n5.quarterLength = 4
    >>> s.append(n5)
    >>> s = s.makeMeasures()
    >>> #_DOCS_SHOW s.show()
    
    .. image:: images/serial-findTransposedAndInvertedMultisets.png
        :width: 150
        
    >>> majTriads = serial.findTransposedAndInvertedMultisets(s, [[0, 4, 7], [0, 3, 7]], 'ignoreAll', includeChords=False)
    >>> [(maj.segment, maj.startOffset) for maj in majTriads]
    [([<music21.note.Note G>, <music21.note.Note E>, <music21.note.Note C>], 2.0), 
    ([<music21.note.Note C>, <music21.note.Note E->, <music21.note.Note G>], 0.0)]
    >>> [maj.matchedSegment for maj in majTriads]
    [[0, 4, 7], [0, 4, 7]]
        
    Note that when we search for both [0, 4, 7] and [0, 3, 7], which are related to each other
    by the composition of an inversion and a transposition, each found segment is only matched to one
    of the multisets in the searchList; thus each found segment appears still appears at most once in the returned list
    of contiguous segments. Accordingly, calling :attr:`~music21.serial.ContiguousSegmentOfNotes.matchedSegment`
    returns only one element of the searchList for each found segment.
    
    OMIT_FROM_DOCS
    
    >>> majAndMinTriads = serial.findTransposedAndInvertedMultisets(s, [[0, 4, 7]], 'rowsOnly', includeChords=True)
    >>> [maj.segment for maj in majAndMinTriads]
    [[<music21.note.Note G>, <music21.note.Note E>, <music21.note.Note C>], 
    [<music21.note.Note C>, <music21.note.Note E->, <music21.note.Note G>]]
    
    '''
    
    nummultisets = len(searchList)
    multisets = []
    donealready = []
    contigdict = {}
    
    for k in range(0, nummultisets):
        baseMultiset = searchList[k]
        baseMultisetPitchClasses = pcToToneRow(baseMultiset).pitchClasses()
        baseMultisetInversion = pcToToneRow(baseMultiset).zeroCenteredTransformation('I', 0).pitchClasses()
        for l in range(0, 12):
            multiset = [(l + x) % 12 for x in baseMultisetPitchClasses]
            length = len(multiset)
            used = False
            for usedset in donealready:
                if used == False:
                    if _checkMultisetEquivalence(usedset, multiset) == True:
                        used = True
            if used == False:
                donealready.append(multiset)
                length = len(multiset)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    contig = getContiguousSegmentsOfLength(inputStream, length, reps, includeChords)
                    contigdict[length] = contig
                for contiguousseg in contig:
                    if reps == 'ignoreAll':
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.getDistinctPitchClasses()
    #                    if len(set([p.pitchClass for p in segment[0].pitches]) and set(multiset)) != 0:
    #                        if len(set([p.pitchClass for p in segment[-1].pitches]) and set(multiset)) != 0:
                        matched = False
                        for i in range(0, len(pitchList) - len(multiset) + 1):
                            if matched == False:
                                subsetToCheck = pitchList[i:i+len(multiset)]
                                if _checkMultisetEquivalence(multiset, subsetToCheck) == True:
                                    if len(segment) == 1:
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = baseMultiset
                                        multisets.append(contiguousseg)
                                    else:
                                        multiset = pcToToneRow(multiset).pitchClasses()
                                        if segment[0].pitches[-1].pitchClass in multiset:
                                            if segment[-1].pitches[0].pitchClass in multiset:
                                                middleseg = ContiguousSegmentOfNotes(list(segment[1:len(segment)-1]), None, None)
                                                listOfPitchClasses = middleseg.readPitchClassesFromBottom()
                                                doneAddingFirst = False
                                                firstChordPitches = segment[0].pitches
                                                for j in range(1, len(firstChordPitches) + 1):
                                                    if doneAddingFirst == False:
                                                        if firstChordPitches[-j].pitchClass in multiset:
                                                            listOfPitchClasses.append(firstChordPitches[-j].pitchClass)
                                                        else:
                                                            doneAddingFirst = True
                                                doneAddingLast = False
                                                lastChordPitches = segment[-1].pitches
                                                for k in range(0, len(lastChordPitches)):
                                                    if doneAddingLast == False:
                                                        if lastChordPitches[k].pitchClass in multiset:
                                                            listOfPitchClasses.append(lastChordPitches[k].pitchClass)
                                                        else:
                                                            doneAddingLast = True
                                                if set(listOfPitchClasses) == set(multiset):
                                                    matched = True
                                                    contiguousseg.activeSegment = subsetToCheck
                                                    contiguousseg.matchedSegment = baseMultiset
                                                    multisets.append(contiguousseg)
                    else:
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.readPitchClassesFromBottom()
                        matched = False
                        lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                        upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                        for j in range(lowerBound, upperBound + 1):
                            if matched == False:
                                subsetToCheck = pitchList[j:j+length]
                                if _checkMultisetEquivalence(subsetToCheck, multiset) == True:
                                    matched = True
                                    contiguousseg.activeSegment = subsetToCheck
                                    contiguousseg.matchedSegment = baseMultiset
                                    multisets.append(contiguousseg)
        for l in range(0, 12):
            multiset = [(l + x) % 12 for x in baseMultisetInversion]
            length = len(multiset)
            used = False
            for usedset in donealready:
                if used == False:
                    if _checkMultisetEquivalence(usedset, multiset) == True:
                        used = True
            if used == False:
                donealready.append(multiset)
                length = len(multiset)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    contig = getContiguousSegmentsOfLength(inputStream, length, reps, includeChords)
                    contigdict[length] = contig
                for contiguousseg in contig:
                    if reps == 'ignoreAll':
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.getDistinctPitchClasses()
    #                    if len(set([p.pitchClass for p in segment[0].pitches]) and set(multiset)) != 0:
    #                        if len(set([p.pitchClass for p in segment[-1].pitches]) and set(multiset)) != 0:
                        matched = False
                        for i in range(0, len(pitchList) - len(multiset) + 1):
                            if matched == False:
                                subsetToCheck = pitchList[i:i+len(multiset)]
                                if _checkMultisetEquivalence(multiset, subsetToCheck) == True:
                                    if len(segment) == 1:
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = baseMultiset
                                        multisets.append(contiguousseg)
                                    else:
                                        multiset = pcToToneRow(multiset).pitchClasses()
                                        if segment[0].pitches[-1].pitchClass in multiset:
                                            if segment[-1].pitches[0].pitchClass in multiset:
                                                middleseg = ContiguousSegmentOfNotes(list(segment[1:len(segment)-1]), None, None)
                                                listOfPitchClasses = middleseg.readPitchClassesFromBottom()
                                                doneAddingFirst = False
                                                firstChordPitches = segment[0].pitches
                                                for j in range(1, len(firstChordPitches) + 1):
                                                    if doneAddingFirst == False:
                                                        if firstChordPitches[-j].pitchClass in multiset:
                                                            listOfPitchClasses.append(firstChordPitches[-j].pitchClass)
                                                        else:
                                                            doneAddingFirst = True
                                                doneAddingLast = False
                                                lastChordPitches = segment[-1].pitches
                                                for k in range(0, len(lastChordPitches)):
                                                    if doneAddingLast == False:
                                                        if lastChordPitches[k].pitchClass in multiset:
                                                            listOfPitchClasses.append(lastChordPitches[k].pitchClass)
                                                        else:
                                                            doneAddingLast = True
                                                if set(listOfPitchClasses) == set(multiset):
                                                    matched = True
                                                    contiguousseg.activeSegment = subsetToCheck
                                                    contiguousseg.matchedSegment = baseMultiset
                                                    multisets.append(contiguousseg)
                    else:
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.readPitchClassesFromBottom()
                        matched = False
                        lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                        upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                        for j in range(lowerBound, upperBound + 1):
                            if matched == False:
                                subsetToCheck = pitchList[j:j+length]
                                if _checkMultisetEquivalence(subsetToCheck, multiset) == True:
                                    matched = True
                                    contiguousseg.activeSegment = subsetToCheck
                                    contiguousseg.matchedSegment = baseMultiset
                                    multisets.append(contiguousseg)
    return multisets

def labelTransposedAndInvertedMultisets(inputStream, 
                                        multisetDict, 
                                        reps='skipConsecutive', 
                                        includeChords=True):    
    '''
    Labels all instances of a given collection of multisets, with 
    transpositions and inversions, of pitch classes in a
    :class:`~music21.stream.Stream`.

    A multiset is a generalization of a set, as described in 
    :meth:`~music21.serial.findMultisets`.
    
    The multisetDict is a dictionary whose keys are names of the multisets to
    be searched for, and whose values are the segments of pitch classes. The 
    values will be turned in to a segmentList, as in 
    :func:`~music21.serial.findMultisets`.

    All other settings are as in 
    :func:`~music21.serial.findTransposedMultisets` as well.
    
    Returns a deep copy of the inputStream with a 
    :class:`~music21.spanner.Line` connecting the first and last notes of each
    found multiset, and the first note of each found multiset labeled with a 
    :class:`~music21.note.Lyric`, the label being the key corresponding to the 
    segment of pitch classes. One should make sure not to call this function 
    with too large of a segmentDict, as a note being contained in too many 
    segments will result in some spanners not showing.
    
    At the present time a relatively large number of multisets are found using 
    the 'ignoreAll' setting, particularly when there are many repetitions of 
    pitch classes (immediate or otherwise).

    As a result, it is possible that at points in the stream there will be more 
    than six spanners active simultaneously, which may result in some spanners 
    not showing correctly in XML format, or not at all.
    
    >>> s = stream.Stream()
    >>> n1 = note.Note('c4')
    >>> n2 = note.Note('e-4')
    >>> n3 = note.Note('g4')
    >>> n4 = note.Note('e4')
    >>> n5 = note.Note('c4')
    >>> for n in [n1, n2, n3, n4]:
    ...     n.quarterLength = 1
    ...     s.append(n)
    >>> n5.quarterLength = 4
    >>> s.append(n5)
    >>> s = s.makeMeasures()
    >>> #_DOCS_SHOW serial.labelTransposedAndInvertedMultisets(s, {'triad':[0, 4, 7]}, includeChords=False).show()
        
    .. image:: images/serial-labelTransposedAndInvertedMultisets.png
       :width: 500
    
    Note: the spanners above were moved manually so that they can be more 
    easily distinguished from one another.
    '''
    
    
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [multisetDict[label] for label in multisetDict]
    segmentsToLabel = findTransposedAndInvertedMultisets(streamCopy, segmentList, reps, includeChords)
    return _labelGeneral(segmentsToLabel, streamCopy, multisetDict, reps, includeChords)   
      
#---------------------------------------------------------------------            


class HistoricalTwelveToneRow(TwelveToneRow):
    
    '''
    Subclass of :class:`~music21.serial.TwelveToneRow` storing additional attributes of a twelve-tone row used in the historical literature.
    
    '''
    
    _DOC_ATTR = {
    'composer': 'The name of the composer.',
    'opus': 'The opus of the work, or None.',
    'title': 'The title of the work.',
    }
    
    composer = None
    opus = None
    title = None
    
    def __init__(self, composer = None, opus = None, title = None, row = None):
        self.composer = composer
        self.opus = opus
        self.title = title
        self.row = row
        TwelveToneRow.__init__(self)



def getHistoricalRowByName(rowName):
    
    '''
    Given the name referring to a twelve-tone row used in the historical literature,
    returns a :class:`~music21.serial.HistoricalTwelveToneRow` object with attributes describing the row.
    
    The names of the rows with stored attributes are below (each must be passed as a string, in single quotes).
    
    >>> for r in sorted(list(serial.historicalDict)):
    ...     print(r)   
    RowBergChamberConcerto
    RowBergDerWein
    RowBergLulu
    RowBergLuluActIIScene1
    RowBergLuluActIScene20
    RowBergLyricSuite
    RowBergLyricSuitePerm
    RowBergViolinConcerto
    RowBergWozzeckPassacaglia
    RowSchoenbergFragOrganSonata
    RowSchoenbergFragPiano
    RowSchoenbergFragPianoPhantasia
    RowSchoenbergIsraelExists
    RowSchoenbergJakobsleiter
    RowSchoenbergMosesAron
    RowSchoenbergOp23No5
    RowSchoenbergOp24Mvmt4
    RowSchoenbergOp24Mvmt5
    RowSchoenbergOp25
    RowSchoenbergOp26
    RowSchoenbergOp27No1
    RowSchoenbergOp27No2
    RowSchoenbergOp27No3
    RowSchoenbergOp27No4
    RowSchoenbergOp28No1
    RowSchoenbergOp28No3
    RowSchoenbergOp29
    RowSchoenbergOp30
    RowSchoenbergOp31
    RowSchoenbergOp32
    RowSchoenbergOp33A
    RowSchoenbergOp33B
    RowSchoenbergOp34
    RowSchoenbergOp35No1
    RowSchoenbergOp35No2
    RowSchoenbergOp35No3
    RowSchoenbergOp35No5
    RowSchoenbergOp36
    RowSchoenbergOp37
    RowSchoenbergOp41
    RowSchoenbergOp42
    RowSchoenbergOp44
    RowSchoenbergOp45
    RowSchoenbergOp46
    RowSchoenbergOp47
    RowSchoenbergOp48No1
    RowSchoenbergOp48No2
    RowSchoenbergOp48No3
    RowSchoenbergOp50A
    RowSchoenbergOp50B
    RowSchoenbergOp50C
    RowWebernOp17No2
    RowWebernOp17No3
    RowWebernOp18No1
    RowWebernOp18No2
    RowWebernOp18No3
    RowWebernOp19No1
    RowWebernOp19No2
    RowWebernOp20
    RowWebernOp21
    RowWebernOp22
    RowWebernOp23
    RowWebernOp24
    RowWebernOp25
    RowWebernOp26
    RowWebernOp27
    RowWebernOp28
    RowWebernOp29
    RowWebernOp30
    RowWebernOp31
    RowWebernOpNo17No1
    
    
    >>> a = serial.getHistoricalRowByName('RowWebernOp29')
    >>> a.row
    [3, 11, 2, 1, 5, 4, 7, 6, 10, 9, 0, 8]
    >>> a.composer
    'Webern'
    >>> a.opus
    'Op. 29'
    >>> a.title
    'Cantata I'
    >>> a.isLinkChord()
    False
    
    '''
    
    if rowName in historicalDict:
        attr = historicalDict[rowName]
        rowObj = HistoricalTwelveToneRow(attr[0], attr[1], attr[2], attr[3])
        return rowObj
    else:
        raise SerialException("No historical row with given name found")

#-------------------------------------------------------------------------------
def pcToToneRow(pcSet):
    '''A convenience function that, given a list of pitch classes represented as integers
    and turns it in to a :class:`~music21.serial.ToneRow` object.

    
    >>> a = serial.pcToToneRow(range(12))
    >>> a.show('text')
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note C#>
    {2.0} <music21.note.Note D>
    {3.0} <music21.note.Note E->
    {4.0} <music21.note.Note E>
    {5.0} <music21.note.Note F>
    {6.0} <music21.note.Note F#>
    {7.0} <music21.note.Note G>
    {8.0} <music21.note.Note G#>
    {9.0} <music21.note.Note A>
    {10.0} <music21.note.Note B->
    {11.0} <music21.note.Note B>
    >>> matrixObj = a.matrix()
    >>> print(matrixObj)
      0  1  2  3  4  5  6  7  8  9  A  B
      B  0  1  2  3  4  5  6  7  8  9  A
    ...

    >>> a = serial.pcToToneRow([4,5,0,6,7,2,'a',8,9,1,'b',3])
    >>> matrixObj = a.matrix()
    >>> print(matrixObj)
      0  1  8  2  3  A  6  4  5  9  7  B
      B  0  7  1  2  9  5  3  4  8  6  A
    ...
    
    OMIT_FROM_DOCS
    
    >>> a = serial.pcToToneRow([1,1,1,1,1,1,1,1,1,1,1,1])
    >>> a.pitchClasses()
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    >>> serial.pcToToneRow([3, 4]).pitchClasses()
    [3, 4]
    '''
    
    if len(pcSet) == 12:
        a = TwelveToneRow()
    else:
        a = ToneRow()
    for thisPc in pcSet:
        n = note.Note()
        n.pitch.pitchClass = thisPc
        n.pitch.octave = None
        a.append(n)
    return a
    
def rowToMatrix(p):
    '''
    takes a row of numbers of converts it to a 12-tone matrix.
    '''
    
    i = [(12-x) % 12 for x in p]
    matrix = [[(x+t) % 12 for x in p] for t in i]

    ret = ""
    for row in matrix:
        msg = []
        for p in row:
            msg.append(str(p).rjust(3))
        ret += ''.join(msg) + "\n"

    return ret


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCarlCode(self):
        part = stream.Part()
        n1 = note.Note('e4')
        n1.quarterLength = 4
        n2 = note.Note('e4')
        n2.quarterLength = 4
        n3 = note.Note('f4')
        n3.quarterLength = 4
        n4 = note.Note('e4')
        n4.quarterLength = 4
        part.append(n1)
        part.append(n2)
        part.append(n3)
        part.append(n4)
        part.makeMeasures(inPlace = True)
        EEF = findMultisets(part, [[5, 4, 4]], 'includeAll', includeChords=False)
        unused = [(seg.activeSegment, seg.startMeasureNumber) for seg in EEF]
        # TODO: Test this?

#    def testRows(self):
#        from music21 import interval
#
#        self.assertEqual(len(vienneseRows), 71)
#
#        totalRows = 0
#        cRows = 0
#        for thisRow in vienneseRows:
#            thisRow = thisRow() 
#            self.assertEqual(isinstance(thisRow, TwelveToneRow), True)
#            
#            if thisRow.composer == "Berg":
#                continue
#            post = thisRow.title
#            
#            totalRows += 1
#            if thisRow[0].pitchClass == 0:
#                cRows += 1
            
#             if interval.notesToInterval(thisRow[0], 
#                                    thisRow[6]).intervalClass == 6:
#              # between element 1 and element 7 is there a TriTone?
#              rowsWithTTRelations += 1


    def testMatrix(self):

        src = getHistoricalRowByName('RowSchoenbergOp37')
        self.assertEqual([p.name for p in src], 
            ['D', 'C#', 'A', 'B-', 'F', 'E-', 'E', 'C', 'G#', 'G', 'F#', 'B'])
        s37 = getHistoricalRowByName('RowSchoenbergOp37').matrix()
        self.assertEqual([e.name for e in s37[0]], ['C', 'B', 'G', 'G#', 'E-', 'C#', 'D', 'B-', 'F#', 'F', 'E', 'A'])


    def testLabelingA(self):
        from music21 import corpus
        series = {'a':1, 'g-':2, 'g':3, 'a-':4, 
                  'f':5, 'e-':6, 'e':7, 'd':8, 
                  'c':9, 'c#':10, 'b-':11, 'b':12}
        s = corpus.parse('bwv66.6')
        for n in s.flat.notes:
            for key in series:
                if n.pitch.pitchClass == pitch.Pitch(key).pitchClass:
                    n.addLyric(series[key])
        match = []
        for n in s.parts[0].flat.notes:
            match.append(n.lyric)
        self.assertEqual(match, ['10', '12', '1', '12', '10', '7', '10', '12', '1', '10', '1', '12', '4', '2', '1', '12', '12', '2', '7', '1', '12', '10', '10', '1', '12', '10', '1', '4', '2', '4', '2', '2', '2', '2', '2', '5', '2'])
        #s.show()
    
    def testHistorical(self):
        
        nonRows = []
        for historicalRow in historicalDict:
            if getHistoricalRowByName(historicalRow).isTwelveToneRow() == False:
                nonRows.append(historicalRow)
        self.assertEqual(nonRows, [])

    def testExtractRowParts(self):
        '''Was a problem in slices'''
        aRow = getHistoricalRowByName('RowBergViolinConcerto')
        unused_aRow2 = aRow[0:3]
        
    def testPostTonalDocs(self):
        aRow = getHistoricalRowByName('RowBergViolinConcerto')
        #aMatrix = aRow.matrix()
        bStream = stream.Stream()
        for i in range(0,12,3):
            aRow2 = aRow[i:i+3]
            c = chord.Chord(aRow2)
            c.addLyric(c.primeFormString)
            c.addLyric(c.forteClass)
            bStream.append(c)

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                i = copy.copy(obj)
                j = copy.deepcopy(obj)

                
        
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = ['ToneRow', 'TwelveToneRow', 'HistoricalTwelveToneRow', 'ContiguousSegmentOfNotes',
              'pcToToneRow', 'TwelveToneMatrix', 'rowToMatrix', 'getHistoricalRowByName', 
              'getContiguousSegmentsOfLength',
              'findSegments', 'labelSegments',
              'findTransposedSegments', 'labelTransposedSegments',
              'findTransformedSegments', 'labelTransformedSegments',
              'findMultisets', 'labelMultisets',
              'findTransposedMultisets', 'labelTransposedMultisets',
              'findTransposedAndInvertedMultisets', 'labelTransposedAndInvertedMultisets'
              ]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
