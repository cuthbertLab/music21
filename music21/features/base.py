#-------------------------------------------------------------------------------
# Name:         features/base.py
# Purpose:      Feature extractors base classes.
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest
import music21

from music21 import environment
_MOD = 'features/base.py'
environLocal = environment.Environment(_MOD)




#-------------------------------------------------------------------------------
class Feature(object):
    '''An object representation of a feature, capable of presentation in a variety of formats, and returned from FeatureExtractor objects.
    '''
    def __init__(self):
        # these values will be filled by the extractor
        self.name = None # string name representation
        self.description = None # string description
        self.isSequential = None # True or False
        self.dimensions = None # number of dimensions
        self.discrete = None # is discrete or continuous
        # data storage; possibly use numpy array
        self.vector = None

    def _getVectors(self):
        '''Prepare a vector of appropriate size and return
        '''
        return [0] * self.dimensions

    def prepareVectors(self):
        '''Prepare the vector stored in this feature.
        '''
        self.vector = self._getVectors()

    def normalize(self):
        '''Normalize the vector between 0 and 1, assuming there is more than one value.
        '''
        if self.dimensions == 1:
            return # do nothing
        m = max(self.vector)
        if max == 0:
            return # do nothing
        scalar = 1. / m # get floating point scalar for speed
        temp = self._getVectors()
        for i, v in enumerate(self.vector):
            temp[i] = v * scalar
        self.vector = temp


#-------------------------------------------------------------------------------
class FeatureExtractor(object):
    def __init__(self, featureSetOrStream, *arguments, **keywords):
        self._src = featureSetOrStream
        self._feature = None # Feature object

        self.name = None # string name representation
        self.description = None # string description
        self.isSequential = None # True or False
        self.dimensions = None # number of dimensions
        self.discrete = True # default

    def _fillFeautureAttributes(self, feature=None):
        '''Fill the attributes of a Feature with the descriptors in the FeatureExtractor.
        '''
        # operate on passed-in feature or self._feature
        if feature is None:
            feature = self._feature
        feature.name = self.name
        feature.description = self.description
        feature.isSequential = self.isSequential
        feature.dimensions = self.dimensions
        feature.discrete = self.discrete
        return feature

    def _prepareFeature(self):
        '''Prepare a new feature for data acquisition.

        >>> from music21 import *
        >>> s = stream.Stream()
        >>> fe = features.jSymbolic.InitialTimeSignatureFeature(s)
        >>> fe._prepareFeature()
        >>> fe._feature.name
        'Initial Time Signature'
        >>> fe._feature.dimensions
        2
        >>> fe._feature.vector
        [0, 0]
        '''
        self._feature = Feature()
        self._fillFeautureAttributes() # will fill self._feature
        self._feature.prepareVectors() # will vector with necessary zeros


    def _prepareStream(self, streamObj):
        '''Common routines done on Streams prior to processing. Return a new Stream
        '''
        #TODO: add expand repeats
        src = streamObj.stripTies(retainContainers=True, inPlace=False)
        return src


    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # do work in subclass
        pass

    def extract(self, source=None):
        '''Extract the feature and return the result. 
        '''
        if source is not None:
            self._src = source
        self._prepareFeature()
        self._process() # will set feature object

        # assume we always want to normalize?
        self._feature.normalize()

        return self._feature    






#-------------------------------------------------------------------------------

class DataFile(object):
    '''Provide output of data in an number of formats
    '''
    def __init__(self):
        # assume a two dimensional array
        self._rows = []
    
    def append(self, row):
        self._rows.append(row)

    def preperaTabDelimted(self):
        msg = []
        for row in self._rows:
            sub = []
            for e in row:
                sub.append(str(e))
            msg.append('\t'.join(sub))
        return '\n'.join(msg)

    def write(self, fp):
        msg = self.preperaTabDelimted()
        f = open(fp, 'w')
        f.write(msg)
        f.close()



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testComposerClassification(self):
        from music21 import stream, note, features, corpus

        features = [
            features.jSymbolic.PitchClassDistributionFeature, features.jSymbolic.FifthsPitchHistogramFeature, 
            features.jSymbolic.BasicPitchHistogramFeature, 
            features.jSymbolic.ChangesOfMeterFeature
            ]
        worksBach = [
            'bwv3.6.xml', 'bwv5.7.xml', 'bwv32.6.xml',
            ]
        # monteverdi
        worksPalestrina = [
            'madrigal.3.1.xml', 'madrigal.3.2.xml', 'madrigal.3.9.xml',
            ]

        df = DataFile()

        # create header:
#         v1 = [] # lable
#         v2 = [] # data type
#         v3 = [] # optional flags
#         s = stream.Stream()
#         for feClass in features:
#             fe = feClass(s)
#             for i in range(fe.dimensions):
#                 v1.append('%s %s' % (fe.name, i))
#                 if fe.discrete:
#                     v2.append('d')
#                 else:
#                     v2.append('c')
#                 v3.append('')
#         # last vector is class, here the composer
#         v1.append('Composer')
#         v2.append('d')
#         v3.append('class') # place in last position
#         df.append(v1)
#         df.append(v2)
#         df.append(v3)
# 
#         # add data
#         for works, composer in [(worksBach, 'Bach'), 
#                                  (worksPalestrina, 'Palestrina')]:
#             for w in works:
#                 s = corpus.parse(w)
#                 environLocal.printDebug([s, s.metadata.title, s.metadata.composer])
#                 v = [] # final vector
#                 for feClass in features:
#                     fe = feClass(s)
#                     v += fe.extract().vector
#                 # last vector is class, here the composer
#                 v.append(composer)
#                 df.append(v)
# 
#         df.write('/_scratch/test.tab')


if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof





