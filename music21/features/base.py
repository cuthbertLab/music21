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

from music21 import stream

from music21 import environment
_MOD = 'features/base.py'
environLocal = environment.Environment(_MOD)




#-------------------------------------------------------------------------------
class FeatureException(music21.Music21Exception):
    pass


class Feature(object):
    '''An object representation of a feature, capable of presentation in a variety of formats, and returned from FeatureExtractor objects.

    Feature objects are simple. It is FeatureExtractors that store all metadata and processing routines for creating Feature objects. 
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
class FeatureExtractorException(music21.Music21Exception):
    pass

class FeatureExtractor(object):
    '''A model of process that extracts a feature from a Music21 Stream. The main public interface is the extract() method. 

    The extractor can be passed a Stream or a reference to a DataInstance. All Stream's are internally converted to a DataInstance if necessary. Usage of a DataInstance offers significant performance advantages, as common forms of the Stream are cached for easy processing. 

    '''
    def __init__(self, dataOrStream, *arguments, **keywords):
        self._src = None # the original Stream, or None
        self.data = None # a DataInstance object: use to get data
        self._setupDataOrStream(dataOrStream)

        self._feature = None # Feature object that results from processing

        self.name = None # string name representation
        self.description = None # string description
        self.isSequential = None # True or False
        self.dimensions = None # number of dimensions
        self.discrete = True # default

    def _setupDataOrStream(self, dataOrStream):
        if isinstance(dataOrStream, DataInstance):
            self._src = None
            self.data = dataOrStream
        else:
            # if we are passed a stream, create a DataInstrance to manage the
            # its data; this is less efficient but is good for testing
            self._src = dataOrStream
            self.data = DataInstance(self._src)


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
        '''Prepare a new Feature object for data acquisition.

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


    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # do work in subclass, calling on self.data
        pass

    def extract(self, source=None):
        '''Extract the feature and return the result. 
        '''
        if source is not None:
            self._src = source
        self._prepareFeature()
        self._process() # will set Feature object to _feature
        # assume we always want to normalize?
        self._feature.normalize()
        return self._feature    




#-------------------------------------------------------------------------------
class DataInstance(object):
    '''A data instance for analysis. This object prepares a Stream and stores multiple common-used stream representations once, providing rapid processing. 
    '''
    def __init__(self, streamObj):
        self._src = streamObj

        # perform basic operations that are performed on all
        # streams
        self._base = self._prepareStream(self._src)

        # store the class value for this data instance
        self._classValue = None
        # the attribute name in the data set for this label
        self._classLabel = None

        # store a dictionary of stream forms that are made and stored
        # on demand
        self._forms = {}

    def _prepareStream(self, streamObj):
        '''Common routines done on Streams prior to processing. Return a new Stream
        '''
        #TODO: add expand repeats
        src = streamObj.stripTies(retainContainers=True, inPlace=False)
        return src

    def _getForm(self, form='flat'):
        '''Get a form of this stream, using a cached version if available.

        >>> from music21 import *
        >>> s = corpus.parse('bwv66.6')
        >>> di = features.DataInstance(s)
        >>> len(di._getForm('flat'))
        192
        >>> len(di['flat'])
        192
        >>> len(di._getForm('flat.pitches'))
        163
        >>> len(di._getForm('flat.notes'))
        163
        >>> len(di._getForm('getElementsByClass.Measure'))
        40
        >>> len(di['getElementsByClass.Measure'])
        40
        >>> len(di._getForm('flat.getElementsByClass.TimeSignature'))
        4
        '''
        # get cached copy
        if form in self._forms.keys():
            return self._forms[form]

        elif form in ['flat']:
            self._forms['flat'] = self._base.flat
            return self._forms['flat']

        elif form in ['flat.pitches']:
            self._forms['flat.pitches'] = self._base.flat.pitches
            return self._forms['flat.pitches']

        elif form in ['flat.notes']:
            self._forms['flat.notes'] = self._base.flat.notes
            return self._forms['flat.notes']

        elif form in ['getElementsByClass.Measure']:
            # need to determine if should concatenate
            # measure for all parts if a score?
            if 'Score' in self._base.classes:
                post = stream.Stream()
                for p in self._base.parts:
                    # insert in overlapping offset positions
                    for m in p.getElementsByClass('Measure'):
                        post.insert(m.getOffsetBySite(p), m)
            else:
                post = self._base.getElementsByClass('Measure')

            self._forms['getElementsByClass.Measure'] = post
            return self._forms['getElementsByClass.Measure']

        elif form in ['flat.getElementsByClass.TimeSignature']:
            self._forms['flat.getElementsByClass.TimeSignature'] = self._base.flat.getElementsByClass('TimeSignature')
            return self._forms['flat.getElementsByClass.TimeSignature']
        else:
            raise AttributeError('no such attribute: %s' % form)


    def __getitem__(self, key):
        return self._getForm(key)


#-------------------------------------------------------------------------------
class OutputFormatException(music21.Music21Exception):
    pass

class OutputFormat(object):
    '''Provide storage classes for data input and output
    '''
    def __init__(self):
        # assume a two dimensional array
        self._rows = []
        self._ext = None # store a fiel extension if necessare
    
    def append(self, row):
        self._rows.append(row)

    def getString(self):
        # define in subclass
        return ''

    def getArray(self):
        '''Get data in a numeric array. 
        '''
        pass
    
    def write(self, fp=None):
        '''Write the file. If not file path is given, a temporary file will be written.
        '''
        if fp is None:
            fp = environment.getTempFile(suffix=self._ext)
        if not fp.endswith(self._ext):
            raise
        f = open(fp, 'w')
        f.write(self.getString())
        f.close()
        return fp

class OutputTabOrange(OutputFormat):
    '''Tab delimited file format used with Orange.

    http://orange.biolab.si/doc/reference/tabdelimited.htm
    '''
    def __init__(self):
        OutputFormat.__init__(self)
        self._ext = '.tab'

    def getString(self):
        msg = []
        for row in self._rows:
            sub = []
            for e in row:
                sub.append(str(e))
            msg.append('\t'.join(sub))
        return '\n'.join(msg)

class OutputCSV(OutputFormat):
    '''Comma-separated value list. 
    '''
    def __init__(self):
        OutputFormat.__init__(self)
        self._ext = '.csv'

    def getString(self):
        msg = []
        for row in self._rows:
            sub = []
            for e in row:
                sub.append(str(e))
            msg.append(','.join(sub))
        return '\n'.join(msg)

class OutputARFF(OutputFormat):
    '''An ARFF (Attribute-Relation File Format) file.

    http://weka.wikispaces.com/ARFF+(stable+version)

    >>> from music21 import *
    >>> oa = features.OutputARFF()
    >>> oa._ext
    '.arff'
    '''
    def __init__(self):
        OutputFormat.__init__(self)
        self._ext = '.arff'

    def getString(self):
        msg = []
        for row in self._rows:
            sub = []
            for e in row:
                sub.append(str(e))
            msg.append(','.join(sub))
        return '\n'.join(msg)



#-------------------------------------------------------------------------------
class DataSet(object):
    '''A set of features, as well as a collection of data to opperate on

    Multiple DataInstance objects, a FeatureSet, and an OutputFormat. 

    >>> from music21 import *
    >>> fds = features.DataSet()
    '''

    def __init__(self, format='tab'):
        # assume a two dimensional array
        self._dataInstances = []
        # order of feature extractors is the order used in the presentaitons
        self._featureExtractors = []
        # the label of the class
        self._classLabel = None
        self._outputFormat = None

        # set the _outputFormat
        self.setOutputFormat(format)



        
    def setOutputFormat(self, format):
        '''Set the output format object. 
        '''
        if format.lower() in ['tab', 'orange', 'taborange', None]:
            self._outputFormat = OutputTabOrange()
        elif format.lower() in ['csv', 'comma']:
            self._outputFormat = OutputCSV()
        elif format.lower() in ['arff', 'attribute']:
            self._outputFormat = OutputARFF()






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

#        df = DataFile()

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





