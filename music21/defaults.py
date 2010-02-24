#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         defaults.py
# Purpose:      Storage for user environment settings and defaults
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-10 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest

# note: this module should not import any higher level modules

_MOD = 'defaults.py'



# TODO: defaults should check the environment object to see 
# if there are any preferences set for values used here


#-------------------------------------------------------------------------------
class DefaultsException(Exception):
    pass



title = 'Music21 Fragment'
author = 'Music21'
software = 'Music21' # used in xml encoding source software 


meterNumerator = 4
meterDenominator = 'quarter'
meterDenominatorBeatType = 4  # musicxml representation


pitchStep = 'C'
pitchOctave = 4

partGroup = 'Part Group'
partGroupAbbreviation = 'PG'

durationType = 'quarter'

instrumentName = ''
partName = ''
partId = 'P1'

keyFifths = 0
keyMode = 'major'


clefSign = 'G'
clefLine = 2

# define a default notehead for notes that know they are unpitched
noteheadUnpitched = 'square'

'''Divisions are a MusicXML concept that music21 does not share
It basically represents the lowest time unit that all other notes
are integer multiples of.  Useful for compatibility with MIDI, but
ultimately restricting since it must be less than 16384, so thus
cannot accurately reflect a piece which uses 64th notes, triplets,
quintuplets, septuplets, 11-tuplets, and 13-tuplets in the same piece
I have chosen a useful base that allows for perfect representation of
128th notes, triplets within triplets, quintuplets, and septuplets
within the piece.  Other tuplets (11, etc.) will be close enough for
most perceptual uses (11:1 will be off by 4 parts per thousand) but
will cause measures to be incompletely filled, etc.  If this gets to
be a problem, music21 could be modified to keep track of "rounding errors"
and make sure that for instance half the notes of an 11:1 are 916 divisions
long and the other half are 917.  But this has not been done yet.
'''
divisionsPerQuarter = 32*3*3*5*7 # 10080




#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    '''Unit tests
    '''

    def setUp(self):
        pass

    def testTest(self):
        self.assertEqual(1, 1)



#-----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    s1 = doctest.DocTestSuite(__name__)
    s2 = unittest.defaultTestLoader.loadTestsFromTestCase(Test)
    s1.addTests(s2)
    runner = unittest.TextTestRunner()
    runner.run(s1)  
