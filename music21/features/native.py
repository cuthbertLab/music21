#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         features.native.py
# Purpose:      music21 feature extractors
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Original music21 feature extractors.
'''



import unittest
import music21

from music21.features import base as featuresModule

from music21 import environment
_MOD = 'features/native.py'
environLocal = environment.Environment(_MOD)






# ideas for other music21 features extactors
# and not available in midi

# clef usage
# enhmaronic usage
# chord analysis

# key signature histogram
# array of circle of fiths


#-------------------------------------------------------------------------------
class NoteStartOnFirstBeatFeature(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.NoteStartOnFirstBeatFeature(s)
    >>> fe = features.jSymbolic.MostCommonPitchPrevalenceFeature(s)
    >>> fe.extract().vector
    [0.29999...]
    '''
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Note Start on First Beat'
        self.description = 'Fraction of first beats of a measure that have notes that start on this beat.'
        self.isSequential = True
        self.dimensions = 1
        self.discrete = False 







#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass




if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof




