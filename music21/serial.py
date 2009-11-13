#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         serial.py
# Purpose:      music21 classes for serial transformations
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest


import music21
import music21.note
from music21 import stream
from music21.stream import Stream




class SerialException(Exception):
    pass

class ToneRow(Stream):
    pass

class TwelveToneRow(ToneRow):
    
    def matrix(self):
        p = self.getNotes()
        i = [(12-x.pitchClass) % 12 for x in p]
        matrix = [[(x.pitchClass+t) % 12 for x in p] for t in i]

        matrixObj = TwelveToneMatrix()
        
        i = 0
        
        for row in matrix:
            i += 1
            rowObject = self.copy()
            rowObject.elements = []
            rowObject.id = 'row-' + str(i)
            for pitch in row:
                note1 = music21.note.Note()
                note1.pitchClass = pitch
                rowObject.addNext(note1)
            matrixObj.append(rowObject)
        
        return matrixObj
        
            
class TwelveToneMatrix(Stream):
    
    def __init__(self, *arguments, **keywords):
        Stream.__init__(self, *arguments, **keywords)



def pcToToneRow(pcSet):
    '''

    >>> a = pcToToneRow(range(12))
    '''
    if len(pcSet) == 12:
        ## TODO: check for uniqueness
        a = TwelveToneRow()
        for thisPc in pcSet:
            newNote = music21.note.Note()
            newNote.pitchClass = thisPc
            a.addNext(newNote)
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

    def testEmpty(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)
