# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         serial.py
# Purpose:      music21 classes for serial transformations
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
This module defines objects for defining and manipulating structures 
common to serial and/or twelve-tone music, 
including :class:`~music21.serial.ToneRow` subclasses.

Serial searching methods that were previously here have been moved to `alpha.search.serial`
'''

import unittest
import copy

from music21 import exceptions21

from music21 import note
from music21 import chord
from music21 import stream
from music21 import pitch

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

    >>> ttr = serial.TwelveToneRow([0, 2, 11, 7, 8, 3, 9, 1, 4, 10, 6, 5])
    >>> aMatrix = ttr.matrix()
    >>> print(aMatrix)
      0  2  B  7  8  3  9  1  4  A  6  5
      A  0  9  5  6  1  7  B  2  8  4  3
      1  3  0  8  9  4  A  2  5  B  7  6
      5  7  4  0  1  8  2  6  9  3  B  A
      4  6  3  B  0  7  1  5  8  2  A  9
      9  B  8  4  5  0  6  A  1  7  3  2
      3  5  2  A  B  6  0  4  7  1  9  8
      B  1  A  6  7  2  8  0  3  9  5  4
      8  A  7  3  4  B  5  9  0  6  2  1
      2  4  1  9  A  5  B  3  6  0  8  7
      6  8  5  1  2  9  3  7  A  4  0  B
      7  9  6  2  3  A  4  8  B  5  1  0
    
    >>> repr(aMatrix)
    '<music21.serial.TwelveToneMatrix for [<music21.serial.TwelveToneRow row-1>]>'
    
    >>> fourthQuartetMatrix = serial.getHistoricalRowByName('RowSchoenbergOp37').matrix()
    >>> repr(fourthQuartetMatrix)
    '<music21.serial.TwelveToneMatrix for 
         [<music21.serial.HistoricalTwelveToneRow Schoenberg Op. 37 Fourth String Quartet>]>'
    '''
    
    def __init__(self, *arguments, **keywords):
        stream.Stream.__init__(self, *arguments, **keywords)
    
    def __str__(self):
        '''
        Return a string representation of the matrix.
        '''
        ret = []
        for rowForm in self:
            msg = []
            for n in rowForm:
                msg.append(str(n.pitch.pitchClassString).rjust(3))
            ret.append(''.join(msg))
        return '\n'.join(ret)

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
      'RowWebernOp29': ('Webern', 'Op. 29', 'Cantata I', 
                        [3, 11, 2, 1, 5, 4, 7, 6, 10, 9, 0, 8]), 
      'RowWebernOp28': ('Webern', 'Op. 28', 'String Quartet', 
                        [1, 0, 3, 2, 6, 7, 4, 5, 9, 8, 11, 10]), 
      'RowSchoenbergOp24Mvmt5': ('Schoenberg', 'Op. 24', 'Serenade, Mvt. 5, "Tanzscene"',
                        [9, 10, 0, 3, 4, 6, 5, 7, 8, 11, 1, 2]), 
      'RowSchoenbergOp24Mvmt4': ('Schoenberg', 'Op. 24', 'Serenade, Mvt. 4, "Sonett"',
                        [4, 2, 3, 11, 0, 1, 8, 6, 9, 5, 7, 10]), 
      'RowSchoenbergJakobsleiter': ('Schoenberg', None, 'Die Jakobsleiter',
                        [1, 2, 5, 4, 8, 7, 0, 3, 11, 10, 6, 9]), 
      'RowSchoenbergOp27No4': ('Schoenberg', 'Op. 27 No. 4', 'Four Pieces for Mixed Chorus, No. 4',
                        [1, 3, 10, 6, 8, 4, 11, 0, 2, 9, 5, 7]), 
      'RowWebernOp23': ('Webern', 'Op. 23', 'Three Songs',
                        [8, 3, 7, 4, 10, 6, 2, 5, 1, 0, 9, 11]), 
      'RowBergLuluActIIScene1': ('Berg', 'Lulu, Act II, Scene 1', 
                                 'Perm. (Every 5th Note Of Transposed Primary Row)',
                                 [10, 7, 1, 0, 9, 2, 4, 11, 5, 8, 3, 6]), 
      'RowSchoenbergOp27No1': ('Schoenberg', 'Op. 27 No. 1', 'Four Pieces for Mixed Chorus, No. 1',
                               [6, 5, 2, 8, 7, 1, 3, 4, 10, 9, 11, 0]), 
      'RowBergLuluActIScene20': ('Berg', 'Lulu, Act I , Scene XX', 
                                 'Perm. (Every 7th Note Of Transposed Primary Row)',
                                 [10, 6, 3, 8, 5, 11, 4, 2, 9, 0, 1, 7]), 
      'RowSchoenbergOp27No3': ('Schoenberg', 'Op. 27 No. 3', 'Four Pieces for Mixed Chorus, No. 3',
                        [7, 6, 2, 4, 5, 3, 11, 0, 8, 10, 9, 1]), 
      'RowSchoenbergOp27No2': ('Schoenberg', 'Op. 27 No. 2', 'Four Pieces for Mixed Chorus, No. 2',
                        [0, 11, 4, 10, 2, 8, 3, 7, 6, 5, 9, 1]), 
      'RowSchoenbergFragPiano': ('Schoenberg', None, 'Fragment For Piano',
                        [6, 9, 0, 7, 1, 2, 8, 11, 5, 10, 4, 3]), 
      'RowSchoenbergOp50B': ('Schoenberg', 'Op. 50B', 'De Profundis',
                        [3, 9, 8, 4, 2, 10, 7, 11, 0, 6, 5, 1]), 
      'RowSchoenbergOp50C': ('Schoenberg', 'Op. 50C', 'Modern Psalms, The First Psalm',
                        [4, 3, 0, 8, 11, 7, 5, 9, 6, 10, 1, 2]), 
      'RowSchoenbergOp50A': ('Schoenberg', 'Op. 50A', 'Three Times A Thousand Years',
                        [7, 9, 6, 4, 5, 11, 10, 2, 0, 1, 3, 8]), 
      'RowSchoenbergMosesAron': ('Schoenberg', None, 'Moses And Aron',
                        [9, 10, 4, 2, 3, 1, 7, 5, 6, 8, 11, 0]), 
      'RowWebernOp25': ('Webern', 'Op. 25', 'Three Songs',
                        [7, 4, 3, 6, 1, 5, 2, 11, 10, 0, 9, 8]), 
      'RowSchoenbergOp23No5': ('Schoenberg', 'Op. 23, No. 5', 'Five Piano Pieces',
                        [1, 9, 11, 7, 8, 6, 10, 2, 4, 3, 0, 5]), 
      'RowSchoenbergOp28No1': ('Schoenberg', 'Op. 28 No. 1', 
                               'Three Satires for Mixed Chorus, No. 1',
                               [0, 4, 7, 1, 9, 11, 5, 3, 2, 6, 8, 10]), 
      'RowSchoenbergOp28No3': ('Schoenberg', 'Op. 28 No. 3', 
                               'Three Satires for Mixed Chorus, No. 3',
                               [5, 6, 4, 8, 2, 10, 7, 9, 3, 11, 1, 0]), 
      'RowWebernOp21': ('Webern', 'Op. 21', 'Chamber Symphony',
                        [5, 8, 7, 6, 10, 9, 3, 4, 0, 1, 2, 11]), 
      'RowSchoenbergIsraelExists': ('Schoenberg', None, 'Israel Exists Again',
                        [0, 3, 4, 9, 11, 5, 2, 1, 10, 8, 6, 7]), 
      'RowSchoenbergOp35No2': ('Schoenberg', 'Op. 35', 'Six Pieces for Male Chorus, No. 2',
                        [6, 9, 7, 1, 0, 2, 5, 11, 10, 3, 4, 8]), 
      'RowSchoenbergOp35No3': ('Schoenberg', 'Op. 35', 'Six Pieces for Male Chorus, No. 3',
                        [3, 6, 7, 8, 5, 0, 9, 10, 4, 11, 2, 1]), 
      'RowSchoenbergOp35No1': ('Schoenberg', 'Op. 35', 'Six Pieces for Male Chorus, No. 1',
                        [2, 11, 3, 5, 4, 1, 8, 10, 9, 6, 0, 7]), 
      'RowSchoenbergOp48No1': ('Schoenberg', 'Op. 48', 'Three Songs, No. 1, "Sommermud"',
                        [1, 2, 0, 6, 3, 5, 4, 10, 11, 7, 9, 8]), 
      'RowSchoenbergOp35No5': ('Schoenberg', 'Op. 35', 'Six Pieces for Male Chorus, No. 5',
                        [1, 7, 10, 2, 3, 11, 8, 4, 0, 6, 5, 9]), 
      'RowSchoenbergOp29': ('Schoenberg', 'Op. 29', 'Suite',
                        [3, 7, 6, 10, 2, 11, 0, 9, 8, 4, 5, 1]), 
      'RowBergLyricSuitePerm': ('Berg', None, 'Lyric Suite, Last Mvt. Permutation',
                        [5, 6, 10, 4, 1, 9, 2, 8, 7, 3, 0, 11]), 
      'RowWebernOp20': ('Webern', 'Op. 20', 'String Trio',
                        [8, 7, 2, 1, 6, 5, 9, 10, 3, 4, 0, 11]), 
      'RowSchoenbergOp46': ('Schoenberg', 'Op. 46', 'A Survivor From Warsaw',
                        [6, 7, 0, 8, 4, 3, 11, 10, 5, 9, 1, 2]), 
      'RowSchoenbergFragOrganSonata': ('Schoenberg', None, 'Fragment of Sonata For Organ',
                        [1, 7, 11, 3, 9, 2, 8, 6, 10, 5, 0, 4]), 
      'RowSchoenbergOp44': ('Schoenberg', 'Op. 44', 'Prelude To A Suite From "Genesis"',
                        [10, 6, 2, 5, 4, 0, 11, 8, 1, 3, 9, 7]), 
      'RowSchoenbergOp45': ('Schoenberg', 'Op. 45', 'String Trio',
                        [2, 10, 3, 9, 4, 1, 11, 8, 6, 7, 5, 0]), 
      'RowSchoenbergOp33A': ('Schoenberg', 'Op. 33A', 'Two Piano Pieces, No. 1',
                        [10, 5, 0, 11, 9, 6, 1, 3, 7, 8, 2, 4]), 
      'RowSchoenbergOp25': ('Schoenberg', 'Op.25', 'Suite for Piano',
                        [4, 5, 7, 1, 6, 3, 8, 2, 11, 0, 9, 10]), 
      'RowSchoenbergOp26': ('Schoenberg', 'Op. 26', 'Wind Quintet',
                        [3, 7, 9, 11, 1, 0, 10, 2, 4, 6, 8, 5]), 
      'RowSchoenbergOp33B': ('Schoenberg', 'Op. 33B', 'Two Piano Pieces, No. 2',
                        [11, 1, 5, 3, 9, 8, 6, 10, 7, 4, 0, 2]), 
      'RowBergViolinConcerto': ('Berg', None, 'Concerto For Violin And Orchestra',
                        [7, 10, 2, 6, 9, 0, 4, 8, 11, 1, 3, 5]), 
      'RowWebernOp22': ('Webern', 'Op. 22', 'Quartet For Violin, Clarinet, Tenor Sax, And Piano',
                        [6, 3, 2, 5, 4, 8, 9, 10, 11, 1, 7, 0]), 
      'RowBergLulu': ('Berg', None, 'Lulu: Primary Row',
                        [0, 4, 5, 2, 7, 9, 6, 8, 11, 10, 3, 1]), 
      'RowWebernOp30': ('Webern', 'Op. 30', 'Variations For Orchestra',
                        [9, 10, 1, 0, 11, 2, 3, 6, 5, 4, 7, 8]), 
      'RowWebernOp31': ('Webern', 'Op. 31', 'Cantata II',
                        [6, 9, 5, 4, 8, 3, 7, 11, 10, 2, 1, 0]), 
      'RowWebernOpNo17No1': ('Webern', 'Op. 17, No. 1', '"Armer Sunder, Du"',
                        [11, 10, 5, 6, 3, 4, 7, 8, 9, 0, 1, 2]), 
      'RowWebernOp24': ('Webern', 'Op. 24', 'Concerto For Nine Instruments',
                        [11, 10, 2, 3, 7, 6, 8, 4, 5, 0, 1, 9]), 
      'RowSchoenbergOp48No2': ('Schoenberg', 'Op. 48', 'Three Songs, No. 2, "Tot"',
                        [2, 3, 9, 1, 10, 4, 8, 7, 0, 11, 5, 6]), 
      'RowWebernOp27': ('Webern', 'Op. 27', 'Variations For Piano',
                        [3, 11, 10, 2, 1, 0, 6, 4, 7, 5, 9, 8]), 
      'RowSchoenbergOp47': ('Schoenberg', 'Op. 47', 'Fantasy For Violin And Piano',
                        [10, 9, 1, 11, 5, 7, 3, 4, 0, 2, 8, 6]), 
      'RowWebernOp19No2': ('Webern', 'Op. 19, No. 2', '"Ziehn Die Schafe"',
                        [8, 4, 9, 6, 7, 0, 11, 5, 3, 2, 10, 1]), 
      'RowWebernOp19No1': ('Webern', 'Op. 19, No. 1', '"Weiss Wie Lilien"',
                        [7, 10, 6, 5, 3, 9, 8, 1, 2, 11, 4, 0]), 
      'RowWebernOp26': ('Webern', 'Op. 26', 'Das Augenlicht',
                        [8, 10, 9, 0, 11, 3, 4, 1, 5, 2, 6, 7]), 
      'RowSchoenbergFragPianoPhantasia': ('Schoenberg', None, 'Fragment of Phantasia For Piano',
                        [1, 5, 3, 6, 4, 8, 0, 11, 2, 9, 10, 7]), 
      'RowBergDerWein': ('Berg', None, 'Der Wein',
                        [2, 4, 5, 7, 9, 10, 1, 6, 8, 0, 11, 3]), 
      'RowBergWozzeckPassacaglia': ('Berg', None, 'Wozzeck, Act I, Scene 4 "Passacaglia"',
                        [3, 11, 7, 1, 0, 6, 4, 10, 9, 5, 8, 2]), 
      'RowWebernOp18No1': ('Webern', 'Op. 18, No. 1', '"Schatzerl Klein"',
                        [0, 11, 5, 8, 10, 9, 3, 4, 1, 7, 2, 6]), 
      'RowWebernOp18No2': ('Webern', 'Op. 18, No. 2', '"Erlosung"',
                        [6, 9, 5, 8, 4, 7, 3, 11, 2, 10, 1, 0]), 
      'RowWebernOp18No3': ('Webern', 'Op. 18, No. 3', '"Ave, Regina Coelorum"',
                        [4, 3, 7, 6, 5, 11, 10, 2, 1, 0, 9, 8]), 
      'RowSchoenbergOp42': ('Schoenberg', 'Op. 42', 'Concerto For Piano And Orchestra',
                        [3, 10, 2, 5, 4, 0, 6, 8, 1, 9, 11, 7]), 
      'RowSchoenbergOp48No3': ('Schoenberg', 'Op. 48', 'Three Songs, No, 3, "Madchenlied"',
                        [1, 7, 9, 11, 3, 5, 10, 6, 4, 0, 8, 2]), 
      'RowSchoenbergOp37': ('Schoenberg', 'Op. 37', 'Fourth String Quartet',
                        [2, 1, 9, 10, 5, 3, 4, 0, 8, 7, 6, 11]), 
      'RowSchoenbergOp36': ('Schoenberg', 'Op. 36', 'Concerto for Violin and Orchestra',
                        [9, 10, 3, 11, 4, 6, 0, 1, 7, 8, 2, 5]), 
      'RowSchoenbergOp34': ('Schoenberg', 'Op. 34', 'Accompaniment to a Film Scene',
                        [3, 6, 2, 4, 1, 0, 9, 11, 10, 8, 5, 7]), 
      'RowBergChamberConcerto': ('Berg', None, 'Chamber Concerto',
                        [11, 7, 5, 9, 2, 3, 6, 8, 0, 1, 4, 10]), 
      'RowSchoenbergOp32': ('Schoenberg', 'Op. 32', 'Von Heute Auf Morgen',
                        [2, 3, 9, 1, 11, 5, 8, 7, 4, 0, 10, 6]), 
      'RowSchoenbergOp31': ('Schoenberg', 'Op. 31', 'Variations for Orchestra',
                        [10, 4, 6, 3, 5, 9, 2, 1, 7, 8, 11, 0]), 
      'RowSchoenbergOp30': ('Schoenberg', 'Op. 30', 'Third String Quartet',
                        [7, 4, 3, 9, 0, 5, 6, 11, 10, 1, 8, 2]), 
      'RowBergLyricSuite': ('Berg', None, 'Lyric Suite Primary Row', 
                            [5, 4, 0, 9, 7, 2, 8, 1, 3, 6, 10, 11]), 
      'RowSchoenbergOp41': ('Schoenberg', 'Op. 41', 'Ode To Napoleon', 
                            [1, 0, 4, 5, 9, 8, 3, 2, 6, 7, 11, 10]), 
      'RowWebernOp17No3': ('Webern', 'Op. 17, No. 3', '"Heiland, Unsere Missetaten..."', 
                           [8, 5, 4, 3, 7, 6, 0, 1, 2, 11, 10, 9]), 
      'RowWebernOp17No2': ('Webern', 'Op. 17, No. 2', '"Liebste Jungfrau"', 
                           [1, 0, 11, 7, 8, 2, 3, 6, 5, 4, 9, 10])
      }

#-------------------------------------------------------------------------------
class ToneRow(stream.Stream):
    '''
    A Stream representation of a tone row, or an ordered sequence of pitches; 
    can most importantly be used to deal with
    serial transformations. 
    '''
    _DOC_ATTR = {
        'row': 'A list representing the pitch class values of the row.',
    }
    
    _DOC_ORDER = ['pitchClasses', 'noteNames', 'isTwelveToneRow', 'isSameRow', 
                  'getIntervalsAsString', 
                  'zeroCenteredTransformation', 'originalCenteredTransformation',
                  'findZeroCenteredTransformations', 'findOriginalCenteredTransformations']
    
    def __init__(self, row=None, *arguments, **keywords):
        stream.Stream.__init__(self, *arguments, **keywords)
        if row is not None:
            self.row = row
        else:
            self.row = []

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
        >>> quintupleRow
        <music21.serial.TwelveToneRow 0x104760780>
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
        Describes whether or not a :class:`~music21.serial.ToneRow` constitutes 
        a twelve-tone row. Note that a
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
        Convenience function returning a :class:`~music21.serial.TwelveToneRow` with the 
        same pitches.
        Note that a :class:`~music21.serial.ToneRow` may be created without being a 
        true twelve tone row.
        
        
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
                if tempsame is True:
                    if self[i].pitch.pitchClass != row[i].pitch.pitchClass:
                        tempsame = False
        
        return tempsame
    
    def getIntervalsAsString(self):
        '''
        
        Returns the string of intervals between consecutive pitch classes of 
        a :class:`~music21.serial.ToneRow`.
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
                for i in range(0, numPitches):
                    newPitch = (pitchList[i] - firstPitch + index) % 12
                    transformedPitchList.append(newPitch)
            elif transformationType == 'I':
                for i in range(0, numPitches):
                    newPitch = (index + firstPitch - pitchList[i]) % 12
                    transformedPitchList.append(newPitch)
            elif transformationType == 'R':
                for i in range(0, numPitches):
                    newPitch = (index + pitchList[numPitches-1-i] - firstPitch) % 12
                    transformedPitchList.append(newPitch)
            elif transformationType == 'RI':
                for i in range(0, numPitches):
                    newPitch = (index - pitchList[numPitches-1-i] + firstPitch) % 12
                    transformedPitchList.append(newPitch)
            else:
                raise SerialException("Invalid transformation type.")

            return pcToToneRow(transformedPitchList)
            
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
        Gives the list of zero-centered serial transformations 
        taking one :class:`~music21.serial.ToneRow`
        to another, the second specified in the argument. Each transformation is given as a
        tuple of the transformation type and index.
        
        See :meth:`~music21.serial.zeroCenteredTransformation` for 
        an explanation of this convention.
        
        
        >>> chromatic = serial.pcToToneRow([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1])
        >>> reversechromatic = serial.pcToToneRow([8, 7, 6, 5, 4, 3, 2, 1, 0, 11, 10, 9])
        >>> chromatic.findZeroCenteredTransformations(reversechromatic)
        [('I', 8), ('R', 9)]
        >>> schoenberg25 = serial.getHistoricalRowByName('RowSchoenbergOp25')
        >>> schoenberg26 = serial.pcToToneRow(serial.getHistoricalRowByName(
        ...                                        'RowSchoenbergOp26').row)
        >>> schoenberg25.findZeroCenteredTransformations(schoenberg26)
        []
        >>> schoenberg26.findZeroCenteredTransformations(
        ...     schoenberg26.zeroCenteredTransformation('RI',8))
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
        Gives the list of original-centered serial transformations taking one 
        :class:`~music21.serial.ToneRow`
        to another, the second specified in the argument. Each transformation is given as a tuple
        of the transformation type and index.
        
        See :meth:`~music21.serial.originalCenteredTransformation` for an 
        explanation of this convention.
        
        >>> chromatic = serial.pcToToneRow(       [2, 3, 4, 5, 6, 7, 8, 9, 'A', 'B',   0, 1])
        >>> reverseChromatic = serial.pcToToneRow([8, 7, 6, 5, 4, 3, 2, 1, 0,   'B', 'A', 9])
        >>> chromatic.findOriginalCenteredTransformations(reverseChromatic)
        [('I', 6), ('R', 7)]
        >>> schoenberg25 = serial.getHistoricalRowByName('RowSchoenbergOp25')
        >>> schoenberg26 = serial.getHistoricalRowByName('RowSchoenbergOp26')
        >>> schoenberg25.findOriginalCenteredTransformations(schoenberg26)
        []
        >>> schoenberg26.findOriginalCenteredTransformations(
        ...     schoenberg26.originalCenteredTransformation('RI',8))
        [('RI', 8)]
        '''
        # This is rather confused in execution.
        originalRowPitches = self.pitchClasses()
        otherRowPitches = otherRow.pitchClasses()
        transformationList = []
        oldFirstPitch = originalRowPitches[0]
        oldLastPitch = originalRowPitches [-1]
        newFirstPitch = otherRowPitches[0]
        
        # for T, I:
        tiPitch = (newFirstPitch - oldFirstPitch) % 12

        # for R
        rPitch = (newFirstPitch - oldLastPitch) % 12
        
        # for RI
        riPitch = (newFirstPitch - (2 * oldFirstPitch) + oldLastPitch) % 12
        
        # bound method
        ocTrans = self.originalCenteredTransformation
        
        if otherRowPitches == ocTrans('T', tiPitch).pitchClasses():
            transformation = ('T', tiPitch)
            transformationList.append(transformation)
        if otherRowPitches == ocTrans('I', tiPitch).pitchClasses():
            transformation = ('I', tiPitch)
            transformationList.append(transformation)
        if otherRowPitches == ocTrans('R', rPitch).pitchClasses():
            transformation = ('R', rPitch)
            transformationList.append(transformation)
        if otherRowPitches == ocTrans('RI', riPitch).pitchClasses():
            transformation = ('RI', riPitch)
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
    
    _DOC_ORDER = ['matrix', 'isAllInterval', 
                  'getLinkClassification', 'isLinkChord', 'areCombinatorial']

    def __init__(self, *arguments, **keywords):
        ToneRow.__init__(self, *arguments, **keywords)
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
        noteList = self.getElementsByClass('Note')

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
        

        #environLocal.printDebug([
        #  'calling matrix start: len row:', self.row, 'len self', len(self)])

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
        for historicalRow in historicalDict:
            if self.isSameRow(getHistoricalRowByName(historicalRow)):
                samerows.append(historicalRow)
        return samerows
    
    def findTransformedHistorical(self, convention):
        '''
        Checks if a given :class:`music21.serial.TwelveToneRow` is a transformation of 
        any of the historical
        twelve-tone rows stored by music21: see :func:`music21.serial.getHistoricalRowByName`. 
        Returns a list
        of tuples, the tuple consisting of the name of a historical row, and a 
        list of transformations relating
        the input row to the historical row.
        
        The convention for serial transformations must also be specified as 'zero' or 
        'original', as explained
        in :meth:`~music21.serial.findZeroCenteredTransformations` and 
        :meth:`~music21.serial.findOriginalCenteredTransformations`.
        
        >>> row = serial.pcToToneRow([5, 9, 11, 3, 6, 7, 4, 10, 0, 8, 2, 1])
        >>> row.findTransformedHistorical('original')
        [('RowSchoenbergOp32', [('R', 11)])]
        '''
        samerows = []
        if convention == 'zero':
            for historicalRow in historicalDict:
                trans = getHistoricalRowByName(historicalRow).findZeroCenteredTransformations(self)
                if trans != []:
                    samerows.append((historicalRow, trans))
            return samerows
        if convention == 'original':
            for historicalRow in historicalDict:
                historicalRowObject = getHistoricalRowByName(historicalRow)
                trans = historicalRowObject.findOriginalCenteredTransformations(self)
                if trans != []:
                    samerows.append((historicalRow, trans))
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
        
        if self.isTwelveToneRow() is False:
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
        
        if self.isTwelveToneRow() is False:
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
        if linkTuple[0] is None:
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
        if self.isTwelveToneRow() is False:
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


class HistoricalTwelveToneRow(TwelveToneRow):
    '''
    Subclass of :class:`~music21.serial.TwelveToneRow` storing additional attributes of a 
    twelve-tone row used in the historical literature.
    '''
    _DOC_ATTR = {
        'composer': 'The name of the composer.',
        'opus': 'The opus of the work, or None.',
        'title': 'The title of the work.',
    }
    
    composer = None
    opus = None
    title = None
    
    def __init__(self, composer=None, opus=None, title=None, row=None):
        TwelveToneRow.__init__(self, row)
        self.composer = composer
        self.opus = opus
        self.title = title

    def __repr__(self):
        return '<music21.serial.HistoricalTwelveToneRow {} {} {}>'.format(self.composer,
                                                                          self.opus,
                                                                          self.title)



def getHistoricalRowByName(rowName):
    '''
    Given the name referring to a twelve-tone row used in the historical literature,
    returns a :class:`~music21.serial.HistoricalTwelveToneRow` object with attributes 
    describing the row.
    
    The names of the rows with stored attributes are below (each must be passed as a string, 
    in single quotes).
    
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

    >>> aMatrix = serial.rowToMatrix([0, 2, 11, 7, 8, 3, 9, 1, 4, 10, 6, 5])
    >>> print(aMatrix)
      0  2 11  7  8  3  9  1  4 10  6  5
     10  0  9  5  6  1  7 11  2  8  4  3
      1  3  0  8  9  4 10  2  5 11  7  6
      5  7  4  0  1  8  2  6  9  3 11 10
      4  6  3 11  0  7  1  5  8  2 10  9
      9 11  8  4  5  0  6 10  1  7  3  2
      3  5  2 10 11  6  0  4  7  1  9  8
     11  1 10  6  7  2  8  0  3  9  5  4
      8 10  7  3  4 11  5  9  0  6  2  1
      2  4  1  9 10  5 11  3  6  0  8  7
      6  8  5  1  2  9  3  7 10  4  0 11
      7  9  6  2  3 10  4  8 11  5  1  0
    '''
    
    i = [(12 - x) % 12 for x in p]
    matrix = [[(x + t) % 12 for x in p] for t in i]

    ret = []
    for row in matrix:
        msg = []
        for p in row:
            msg.append(str(p).rjust(3))
        ret.append(''.join(msg))

    return '\n'.join(ret)


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass


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
        self.assertEqual([e.name for e in s37[0]], ['C', 'B', 'G', 'G#', 'E-', 'C#', 'D', 'B-', 
                                                    'F#', 'F', 'E', 'A'])


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
        self.assertEqual(match, ['10', '12', '1', '12', '10', '7', '10', '12', '1', '10', '1', 
                                 '12', '4', '2', '1', '12', '12', '2', '7', '1', '12', '10', 
                                 '10', '1', '12', '10', '1', '4', '2', '4', '2', '2', '2', 
                                 '2', '2', '5', '2'])
        #s.show()
    
    def testHistorical(self):
        nonRows = []
        for historicalRow in historicalDict:
            if getHistoricalRowByName(historicalRow).isTwelveToneRow() is False:
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
        for i in range(0, 12, 3):
            aRow2 = aRow[i:i + 3]
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
              ]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
