#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         serial.py
# Purpose:      music21 classes for serial transformations
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest
import copy

import music21
import music21.note
from music21 import stream
from music21 import pitch

#-------------------------------------------------------------------------------
class SerialException(Exception):
    pass






#-------------------------------------------------------------------------------
class TwelveToneMatrix(stream.Stream):
    '''An object representation of a 2-dimensional array of 12 pitches. Internal representation is as a :class:`~music21.stream.Stream`, which stores 12 Streams, each Stream a horizontal row of pitches in the matrix. 

    This object is commonly used by calling the :meth:`~music21.stream.TwelveToneRow.matrix` method of :meth:`~music21.stream.TwelveToneRow` (or a subclass).

    '''
    
    def __init__(self, *arguments, **keywords):
        '''
        >>> aMatrix = TwelveToneMatrix()
        '''
        stream.Stream.__init__(self, *arguments, **keywords)
    
    def __str__(self):
        '''Return a string representation of the matrix.
        '''
        ret = ""
        for rowForm in self.elements:
            msg = []
            for pitch in rowForm:
                msg.append(str(pitch.pitchClassString).rjust(3))
            ret += ''.join(msg) + "\n"
        return ret


#-------------------------------------------------------------------------------
class ToneRow(stream.Stream):
    '''A Stream representation of a tone row, or an ordered sequence of pitches. 

    '''
    def __init__(self):
        stream.Stream.__init__(self)    


class TwelveToneRow(ToneRow):
    '''A Stream representation of a twelve-tone row, capable of producing a 12-tone matrix.
    '''
    row = None

    _DOC_ATTR = {
    'row': 'A list representing the pitch class values of the row.',
    }

    def __init__(self):
        ToneRow.__init__(self)
        if self.row != None:
            for pc in self.row:
                self.append(pitch.Pitch(pc))
    
    def matrix(self):
        '''
        Returns a :class:`~music21.serial.TwelveToneMatrix` object for the row.  That object can just be printed (or displayed via .show())
        
        >>> s37 = RowSchoenbergOp37().matrix()
        >>> print s37
          0  B  7  8  3  1  2  A  6  5  4  9
          1  0  8  9  4  2  3  B  7  6  5  A
          5  4  0  1  8  6  7  3  B  A  9  2
          4  3  B  0  7  5  6  2  A  9  8  1
        ...
        '''        
        
        # TODO: FIX!
        p = self.getElementsByClass(pitch.Pitch)
        i = [(12-x.pitchClass) % 12 for x in p]
        matrix = [[(x.pitchClass+t) % 12 for x in p] for t in i]

        matrixObj = TwelveToneMatrix()
        i = 0
        for row in matrix:
            i += 1
            rowObject = copy.copy(self)
            rowObject.elements = []
            rowObject.id = 'row-' + str(i)
            for thisPitch in row:
                pObj = pitch.Pitch()
                pObj.pitchClass = thisPitch
                rowObject.append(pObj)
            matrixObj.insert(0, rowObject)
        
        return matrixObj
        


class HistoricalTwelveToneRow(TwelveToneRow):
    '''A 12-tone row used in the historical literature. Added attributes to document the the historical context of the row. 
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
    row = [1, 0, 10, 2, 3, 11, 8, 4, 0, 6, 5, 9]
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
    row = [2, 3, 9, 1, 10, 11, 8, 7, 0, 11, 5, 6]
class RowSchoenbergOp48No3(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 48'
    title = 'Three Songs, No, 3, "Madchenlied"'
    row = [1, 7, 9, 11, 3, 5, 10, 6, 11, 0, 8, 2]
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
    row = [10, 7, 1, 0, 9, 2, 11, 5, 8, 3, 6]
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
    row = [8, 4, 9, 6, 7, 0, 11, 5, 3, 2, 9, 1]
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

    >>> a = pcToToneRow(range(12))
    >>> matrixObj = a.matrix()
    >>> print matrixObj
      0  1  2  3  4  5  6  7  8  9  A  B
      B  0  1  2  3  4  5  6  7  8  9  A
    ...

    >>> import random
    >>> a = pcToToneRow([4,5,0,6,7,2,'a',8,9,1,'b',3])
    >>> matrixObj = a.matrix()
    >>> print matrixObj
      0  1  8  2  3  A  6  4  5  9  7  B
      B  0  7  1  2  9  5  3  4  8  6  A
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
        raise SerialException("pcToToneRow requires a 12-tone-row")
    
def rowToMatrix(p):
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
        
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [ToneRow, TwelveToneRow, TwelveToneMatrix]

if __name__ == "__main__":
    music21.mainTest(Test)
