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
# features that use metrical distinctions

class FirstBeatAttackPrevelance(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.FirstBeatAttackPrevelance(s)
    '''
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'First Beat Attack Prevelance'
        self.description = 'Fraction of first beats of a measure that have notes that start on this beat.'
        self.dimensions = 1
        self.discrete = False 




#-------------------------------------------------------------------------------
# employing symbolic durations

class MostCommonQuarterLength(featuresModule.FeatureExtractor):
    id = 'D1'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Most Common Quarter Length.'
        self.description = 'The value of the most common quarter length.'
        self.dimensions = 1
        self.discrete = False 


class MostCommonQuarterLengthPrevelance(featuresModule.FeatureExtractor):
    id = 'D2'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Most Common Quarter Length Prevalance'
        self.description = 'Fraction of notes that have the most common quarter length.'
        self.dimensions = 1
        self.discrete = False 


class RangeOfQuarterLengths(featuresModule.FeatureExtractor):
    id = 'D3'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Range Of Quarter Lengths'
        self.description = 'Difference between the longest and shortest quarter lengths.'
        self.dimensions = 1
        self.discrete = False




#-------------------------------------------------------------------------------
# various ways of looking at chordify representation

class UniquePitchClassSetSimultaneities(featuresModule.FeatureExtractor):
    id = 'S1'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Unique Pitch Class Set Simultaneities'
        self.description = 'Number of unique pitch class simultaneities.'
        self.dimensions = 1
        self.discrete = True 


class UniqueSetClassSimultaneities(featuresModule.FeatureExtractor):
    id = 'S2'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Unique Pitch Class Set Simultaneities'
        self.description = 'Number of unique pitch class simultaneities.'
        self.dimensions = 1
        self.discrete = True 



class MostCommonPitchClassSimultaneityPrevelance(
    featuresModule.FeatureExtractor):
    id = 'S3'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Most Common Pitch Class Simultaneity Prevelance'
        self.description = 'Fraction of all pitch class simultaneities that are the most common simultaneity.'
        self.dimensions = 1
        self.discrete = False 


class MostCommonSetClassSimultaneityPrevelance(featuresModule.FeatureExtractor):
    id = 'S4'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Most Common Set Class Simultaneity Prevelance'
        self.description = 'Fraction of all set class simultaneities that are the most common simultaneity.'
        self.dimensions = 1
        self.discrete = False 


class MajorTriadSimultaneityPrevelance(featuresModule.FeatureExtractor):
    id = 'S5'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'MajorTriadSimultaneityPrevelance'
        self.description = 'Percentage of all simultaneityies that are major triads.'
        self.dimensions = 1
        self.discrete = False 


class MinorTriadSimultaneityPrevelance(featuresModule.FeatureExtractor):
    id = 'S6'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'MinorTriadSimultaneityPrevelance'
        self.description = 'Percentage of all simultaneityies that are major triads.'
        self.dimensions = 1
        self.discrete = False 


class DominantSeventhSimultaneityPrevelance(featuresModule.FeatureExtractor):
    id = 'S7'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'DominantSeventhSimultaneityPrevelance'
        self.description = 'Percentage of all simultaneityies that are major triads.'
        self.dimensions = 1
        self.discrete = False 


class DiminishedTriadSimultaneityPrevelance(featuresModule.FeatureExtractor):
    id = 'S8'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'DiminishedTriadSimultaneityPrevelance'
        self.description = 'Percentage of all simultaneityies that are major triads.'
        self.dimensions = 1
        self.discrete = False 




featureExtractors = [

UniquePitchClassSetSimultaneities, # r31
UniqueSetClassSimultaneities,

]





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass




if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof




