# -*- coding: utf-8 -*-
'''
The Lilypond MusicXML Test Suite comes from 
http://lilypond.org/doc/v2.18/input/regression/musicxml/collated-files

The test suite is licensed under the MIT license 
(https://opensource.org/licenses/mit-license.php)
and copyrighted by the Lilypond project.

Currently this tests only if everything parses without error.  
It does not check to make sure that it actually works.

One change has been made, to 33g-Slur-ChordedNotes.xml
which is contains a common incorrect notation but also a very difficult one 
that music21 can parse if the slur number is changed 
to "2" for the second incorrect slur
since music21 parses all notes of a chord before moving to the next.
'''
import os
import unittest

from music21 import converter
from music21 import common

def allFiles():
    thisDir = os.sep.join([common.getSourceFilePath(),
                           'musicxml',
                           'lilypondTestSuite'])
    allOut = []
    for f in os.listdir(thisDir):
        if f.startswith('__'):
            continue
        allOut.append(thisDir + os.sep + f)
    return allOut

class Test(unittest.TestCase):
    '''
    Test Suite for the Test Suite (meta!)
    '''
    
    def testAll(self):
        for f in allFiles():
            converter.parse(f)
            
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
