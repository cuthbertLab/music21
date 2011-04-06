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

import music21


class Mensuration(music21.meter.TimeSignature):
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
        music21.meter.TimeSignature.__init__(self, timeString)

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


class MedRenException(music21.Music21Exception):
    pass

if __name__ == '__main__':
    music21.mainTest()
