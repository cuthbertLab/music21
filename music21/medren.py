#-------------------------------------------------------------------------------
# Name:         medren.py
# Purpose:      classes for dealing with medieval and Renaissance Music
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Tools for working with medieval and Renaissance music -- see also the 
trecento directory which works particularly on 14th-century Italian
music.
'''
import copy
import music21
from music21 import common
from music21 import duration
from music21 import interval
from music21 import meter
from music21 import note
from music21 import tempo
import unittest, doctest

allowableStrettoIntervals = { 
        -8: [(interval.GenericInterval(3), True), 
             (interval.GenericInterval(-3), True),
             (interval.GenericInterval(5), False),
             (interval.GenericInterval(-4), False),
             (interval.GenericInterval(1), True)],
        8:  [(interval.GenericInterval(3), True), 
             (interval.GenericInterval(-3), True),
             (interval.GenericInterval(5), False),
             (interval.GenericInterval(4), False),
             (interval.GenericInterval(1), True)],
        -5: [(interval.GenericInterval(-3), True), 
             (interval.GenericInterval(-5), False),
             (interval.GenericInterval(2), True),
             (interval.GenericInterval(4), False),
             (interval.GenericInterval(1), True)],
        5:  [(interval.GenericInterval(3), True), 
             (interval.GenericInterval(5), False),
             (interval.GenericInterval(-2), True),
             (interval.GenericInterval(-4), False),
             (interval.GenericInterval(1), True)],
        -4: [(interval.GenericInterval(3), True), 
             (interval.GenericInterval(5), False),
             (interval.GenericInterval(2), False),
             (interval.GenericInterval(-2), True),
             (interval.GenericInterval(-4), False)],
        4:  [(interval.GenericInterval(-3), True), 
             (interval.GenericInterval(-5), False),
             (interval.GenericInterval(2), True),
             (interval.GenericInterval(-2), False),
             (interval.GenericInterval(4), False)],
    }


class Mensuration(meter.TimeSignature):
    '''
    An object representing a mensuration sign in early music:
    
    
    >>> from music21 import *
    >>> ODot = medren.Mensuration(tempus = 'perfect', prolation = 'major', scalingFactor = 2)
    >>> ODot.barDuration.quarterLength
    9.0
    '''
    
    
    def __init__(self, tempus = 'perfect', prolation = 'minor', mode = 'perfect', maximode = None, scalingFactor = 4):

        self.tempus = tempus
        self.prolation = prolation
        self.mode = mode
        self.maximode = maximode
        self._scalingFactor = scalingFactor
        if tempus == 'perfect' and prolation == 'major':
            underlying = [9, 2]
            self.standardSymbol = 'O-dot'
        elif tempus == 'perfect' and prolation == 'minor':
            underlying = [6, 2]
            self.standardSymbol = 'C-dot'
        elif tempus == 'imperfect' and prolation == 'major':
            underlying = [3, 1]
            self.standardSymbol = 'O'
        elif tempus == 'imperfect' and prolation == 'minor':
            underlying = [2, 1]
            self.standardSymbol = 'C'
        else:
            raise MedRenException('cannot make out the mensuration from tempus %s and prolation %s' % (tempus, prolation)) 
        underlying[1] = underlying[1] * scalingFactor

        
        timeString = str(underlying[0]) + '/' + str(underlying[1])
        meter.TimeSignature.__init__(self, timeString)

    def _getScalingFactor(self):
        return self._scalingFactor
    
    def _setScalingFactor(self, newScalingFactor):
        pass
    
class MensuralNote(music21.note.Note):
    scaling = 4
    
    def __init__(self, *arguments, **keywords):
        music21.note.Note.__init__(self, *arguments, **keywords)
        if len(arguments) >= 2:
            self.mensuralType = arguments[1]
            self.setModernDuration()

    def setModernDuration(self):    
        '''
        set the modern duration from 
        '''

def setBarlineStyle(score, newStyle, oldStyle = 'regular', inPlace = True):
    '''
    Converts any right barlines in the previous style (oldStyle; default = 'regular')
    to have the newStyle (such as 'tick', 'none', etc., see bar.py).  
    Leaves alone any other barline types (such as
    double bars, final bars, etc.).  Also changes any measures with no specified
    barlines (which come out as 'regular') to have the new style.

    returns the Score object.
    '''
    if inPlace is False:
        score = copy.deepcopy(score)
    
    oldStyle = oldStyle.lower()
    for m in score.semiFlat:
        if isinstance(m, music21.stream.Measure):
            barline = m.rightBarline
            if barline is None:
                m.rightBarline = music21.bar.Barline(style = newStyle)
            else:
                if barline.style == oldStyle:
                    barline.style = newStyle

    return score

def scaleDurations(score, scalingNum = 1, inPlace = True, scaleUnlinked = True):
    '''
    scale all notes and TimeSignatures by the scaling amount.
    
    returns the Score object
    '''
    if inPlace is False:
        score = copy.deepcopy(score)

    for el in score.recurse():
        el.offset = el.offset * scalingNum
        if el.duration is not None:
            el.duration.quarterLength = el.duration.quarterLength * scalingNum
            if hasattr(el.duration, 'linkStatus') and el.duration.linkStatus is False and scaleUnlinked is True:
                raise MedRenException('scale unlinked is not yet supported')
        if isinstance(el, tempo.MetronomeMark):
            el.value = el.value * scalingNum
        elif isinstance(el, meter.TimeSignature):
            newNum = el.numerator
            newDem = el.denominator / (1.0 * scalingNum) # float division
            iterationNum = 0
            while (newDem != int(newDem)):
                newNum = newNum * 2
                newDem = newDem * 2
                iterationNum += 1
                if iterationNum > 4:
                    raise MedRenException('cannot create a scaling of the TimeSignature for this ratio')
            newDem = int(newDem)
            el.loadRatio(newNum, newDem)
    
    for p in score.parts:
        p.makeBeams()
    return score

def transferTies(score, inPlace = True):
    '''
    transfer the duration of tied notes (if possible) to the first note and fill the remaining places
    with invisible rests:
    
    returns the new Score object
    '''
    if inPlace is False:
        score = copy.deepcopy(score)
    tiedNotes = []
    tieBeneficiary = None 
    for el in score.recurse():
        if not isinstance(el, note.Note):
            continue
        if el.tie is not None:
            if el.tie.type == 'start':
                tieBeneficiary = el
            elif el.tie.type == 'continue':
                tiedNotes.append(el)
            elif el.tie.type == 'stop':
                tiedNotes.append(el)
                tiedQL = tieBeneficiary.duration.quarterLength
                for tiedEl in tiedNotes:
                     tiedQL += tiedEl.duration.quarterLength
                tempDuration = duration.Duration(tiedQL)
                if (tempDuration.type != 'complex' and 
                    len(tempDuration.tuplets) == 0):
                    # successfully can combine these notes into one unit
                    ratioDecimal = tiedQL/float(tieBeneficiary.duration.quarterLength)
                    (tupAct, tupNorm) = common.decimalToTuplet(ratioDecimal)
                    if (tupAct != 0): # error...
                        tempTuplet = duration.Tuplet(tupAct, tupNorm, copy.deepcopy(tempDuration.components[0]))
                        tempTuplet.tupletActualShow = "none"
                        tempTuplet.bracket = False
                        tieBeneficiary.duration = tempDuration
                        tieBeneficiary.duration.tuplets = (tempTuplet,)
                        tieBeneficiary.tie = None #.style = 'hidden'
                        for tiedEl in tiedNotes:
                            tiedEl.tie = None #.style = 'hidden'
                            tiedEl.hideObjectOnPrint = True
                tiedNotes = []

    return score

def convertHouseStyle(score, durationScale = 2, barlineStyle = 'tick', tieTransfer = True, inPlace = False):
    if inPlace is False:
        score = copy.deepcopy(score)
    if durationScale != False:
        scaleDurations(score, durationScale, inPlace = True)
    if barlineStyle != False:
        setBarlineStyle(score, barlineStyle, inPlace = True)
    if tieTransfer != False:
        transferTies(score, inPlace = True)
    
    return score




def cummingSchubertStrettoFuga(score):
    pass


class MedRenException(music21.Music21Exception):
    pass

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
   
class TestExternal(unittest.TestCase):
        
    def runTest(self):
        pass    
    
    def xtestBarlineConvert(self):
        from music21 import corpus
        self.testPiece = corpus.parse('luca/gloria')
        setBarlineStyle(self.testPiece, 'tick')
        self.testPiece.show()

    def xtestScaling(self):
        from music21 import corpus
        self.testPiece = corpus.parse('luca/gloria')
        scaleDurations(self.testPiece, .5)
        self.testPiece.show()

    def xtestTransferTies(self):
        from music21 import corpus
        self.testPiece = corpus.parse('luca/gloria')
        transferTies(self.testPiece)
        self.testPiece.show()

    def xtestUnlinked(self):
        from music21 import stream, note, meter
        s = stream.Stream()
        m = meter.TimeSignature('4/4')
        s.append(m)
        n1 = note.WholeNote('C4')
        n2 = note.HalfNote('D4')
        n1.duration.unlink()
        n1.duration.quarterLength = 2.0
        s.append([n1, n2])

    def testAll(self):
        from music21 import corpus
        gloria = corpus.parse('luca/gloria')
        gloriaNew = convertHouseStyle(gloria)
        print gloriaNew.write()
        #gloriaNew.show()


if __name__ == '__main__':
    music21.mainTest(TestExternal)
