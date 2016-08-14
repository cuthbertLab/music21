# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         features/base.py
# Purpose:      Feature extractors base classes.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
from __future__ import print_function

import unittest
import os

from music21 import common
from music21 import converter
from music21 import corpus
from music21 import exceptions21
from music21 import stream
from music21 import text

from music21.ext import six

from music21 import environment
_MOD = 'features/base.py'
environLocal = environment.Environment(_MOD)




#-------------------------------------------------------------------------------
class FeatureException(exceptions21.Music21Exception):
    pass


class Feature(object):
    '''
    An object representation of a feature, capable of presentation in a variety of formats, 
    and returned from FeatureExtractor objects.

    Feature objects are simple. It is FeatureExtractors that store all metadata and processing 
    routines for creating Feature objects. 
    '''
    def __init__(self):
        # these values will be filled by the extractor
        self.dimensions = None # number of dimensions
        # data storage; possibly use numpy array
        self.vector = None

        # consider not storing this values, as may not be necessary
        self.name = None # string name representation
        self.description = None # string description
        self.isSequential = None # True or False
        self.discrete = None # is discrete or continuous

    def _getVectors(self):
        '''
        Prepare a vector of appropriate size and return
        '''
        return [0] * self.dimensions

    def prepareVectors(self):
        '''
        Prepare the vector stored in this feature.
        '''
        self.vector = self._getVectors()

    def normalize(self):
        '''
        Normalize the vector between 0 and 1, assuming there is more than one value.
        '''
        if self.dimensions == 1:
            return # do nothing
        m = max(self.vector)
        if m == 0:
            return # do nothing
        scalar = 1. / m # get floating point scalar for speed
        temp = self._getVectors()
        for i, v in enumerate(self.vector):
            temp[i] = v * scalar
        self.vector = temp


#-------------------------------------------------------------------------------
class FeatureExtractorException(exceptions21.Music21Exception):
    pass

class FeatureExtractor(object):
    '''
    A model of process that extracts a feature from a Music21 Stream. 
    The main public interface is the extract() method. 

    The extractor can be passed a Stream or a reference to a DataInstance. 
    All Streams are internally converted to a DataInstance if necessary. 
    Usage of a DataInstance offers significant performance advantages, as common forms of 
    the Stream are cached for easy processing. 
    '''
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        self.stream = None # the original Stream, or None
        self.data = None # a DataInstance object: use to get data
        self.setData(dataOrStream)

        self._feature = None # Feature object that results from processing

        if not hasattr(self, "name"):
            self.name = None # string name representation
        if not hasattr(self, "description"):
            self.description = None # string description
        if not hasattr(self, "isSequential"):
            self.isSequential = None # True or False
        if not hasattr(self, "dimensions"):
            self.dimensions = None # number of dimensions
        if not hasattr(self, "discrete"):
            self.discrete = True # default
        if not hasattr(self, "normalize"):
            self.normalize = False # default is no

    def setData(self, dataOrStream):
        '''
        Set the data that this FeatureExtractor will process. 
        Either a Stream or a DataInstance object can be provided. 
        '''
        if dataOrStream is not None:
            if (hasattr(dataOrStream, 'classes') and 'Stream' in         
                dataOrStream.classes):
                #environLocal.printDebug(['creating new DataInstance: this should be a Stream:', 
                #     dataOrStream])
                # if we are passed a stream, create a DataInstrance to 
                # manage the
                # its data; this is less efficient but is good for testing
                self.stream = dataOrStream
                self.data = DataInstance(self.stream)
            # if a DataInstance, do nothing
            else:
                self.stream = None
                self.data = dataOrStream

    def getAttributeLabels(self): 
        '''Return a list of string in a form that is appropriate for data storage.
    
        
        >>> fe = features.jSymbolic.AmountOfArpeggiationFeature()
        >>> fe.getAttributeLabels()
        ['Amount_of_Arpeggiation']

        >>> fe = features.jSymbolic.FifthsPitchHistogramFeature()
        >>> fe.getAttributeLabels()
        ['Fifths_Pitch_Histogram_0', 'Fifths_Pitch_Histogram_1', 'Fifths_Pitch_Histogram_2', 
         'Fifths_Pitch_Histogram_3', 'Fifths_Pitch_Histogram_4', 'Fifths_Pitch_Histogram_5', 
         'Fifths_Pitch_Histogram_6', 'Fifths_Pitch_Histogram_7', 'Fifths_Pitch_Histogram_8', 
         'Fifths_Pitch_Histogram_9', 'Fifths_Pitch_Histogram_10', 'Fifths_Pitch_Histogram_11']

        '''
        post = []
        if self.dimensions == 1:
            post.append(self.name.replace(' ', '_'))
        else:
            for i in range(self.dimensions):
                post.append('%s_%s' % (self.name.replace(' ', '_'), i))
        return post

    def _fillFeatureAttributes(self, feature=None):
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
        self._fillFeatureAttributes() # will fill self._feature
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
            self.stream = source
        # preparing the feature always sets self._feature to a new instance
        self._prepareFeature()
        self._process() # will set Feature object to _feature
        # assume we always want to normalize?
        if self.normalize:
            self._feature.normalize()
        return self._feature    

    def getBlankFeature(self):
        '''Return a properly configured plain feature as a place holder

        >>> from music21 import features
        >>> fe = features.jSymbolic.InitialTimeSignatureFeature()
        >>> fe.getBlankFeature().vector
        [0, 0]
        '''
        f = Feature()
        self._fillFeatureAttributes(f) 
        f.prepareVectors() # will vector with necessary zeros
        return f


#-------------------------------------------------------------------------------
class StreamForms(object):
    '''A dictionary-like wrapper of a Stream, providing 
    numerous representations, generated on-demand, and cached.

    A single StreamForms object can be created for an 
    entire Score, as well as one for each Part and/or Voice. 

    A DataSet object manages one or more StreamForms 
    objects, and exposes them to FeatureExtractors for usage.
    '''
    def __init__(self, streamObj, prepareStream=True):   
        self.stream = streamObj
        if self.stream is not None:
            if prepareStream:
                self._base = self._prepareStream(self.stream)
            else: # possibly make a copy?
                self._base = self.stream
        else:       
            self._base = None

        # basic data storage is a dictionary
        self._forms = {}    

    def keys(self):
        # will only return forms that are established
        return self._forms.keys()

    def _prepareStream(self, streamObj):
        '''
        Common routines done on Streams prior to processing. Return a new Stream
        '''   
        # this causes lots of deepcopys, but an inPlace operation loses 
        # accuracy on feature extractors         
        streamObj = streamObj.stripTies(retainContainers=True)
        return streamObj

    def __getitem__(self, key):
        '''Get a form of this Stream, using a cached version if available.
        '''
        # first, check for cached version
        if key in self._forms:
            return self._forms[key]

        # else, process, store, and return
        elif key in ['flat']:
            self._forms['flat'] = self._base.flat
            return self._forms['flat']

        elif key in ['flat.pitches']:
            self._forms['flat.pitches'] = self._base.flat.pitches
            return self._forms['flat.pitches']

        elif key in ['flat.notes']:
            self._forms['flat.notes'] = self._base.flat.notes
            return self._forms['flat.notes']

        elif key in ['getElementsByClass.Measure']:
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

        elif key in ['flat.getElementsByClass.TimeSignature']:
            self._forms['flat.getElementsByClass.TimeSignature'
                        ] = self._base.flat.getElementsByClass('TimeSignature')
            return self._forms['flat.getElementsByClass.TimeSignature']

        elif key in ['flat.getElementsByClass.KeySignature']:
            self._forms['flat.getElementsByClass.KeySignature'
                        ] = self._base.flat.getElementsByClass('KeySignature')
            return self._forms['flat.getElementsByClass.KeySignature']

        elif key in ['flat.getElementsByClass.Harmony']:
            self._forms['flat.getElementsByClass.Harmony'
                        ] = self._base.flat.getElementsByClass('Harmony')
            return self._forms['flat.getElementsByClass.Harmony']


        elif key in ['metronomeMarkBoundaries']: # already flat
            self._forms['metronomeMarkBoundaries'] = self._base.metronomeMarkBoundaries()
            return self._forms['metronomeMarkBoundaries']

        # some methods that return new streams
        elif key in ['chordify']:
            if 'Score' in self._base.classes:
                # options here permit getting part information out
                # of chordified representation
                self._forms['chordify'] = self._base.chordify(
                    addPartIdAsGroup=True, removeRedundantPitches=False)
            else: # for now, just return a normal Part or Stream
                self._forms['chordify'] = self._base
            return self._forms['chordify']

        elif key in ['chordify.getElementsByClass.Chord']:
            # need flat here, as chordify might return Measures
            x = self.__getitem__('chordify').flat.getElementsByClass('Chord')
            self._forms['chordify.getElementsByClass.Chord'] = x
            return self._forms['chordify.getElementsByClass.Chord']

        # create a Part in a Score for each Instrument
        elif key in ['partitionByInstrument']:
            from music21 import instrument
            x = instrument.partitionByInstrument(self._base)
            self._forms['partitionByInstrument'] = x
            return self._forms['partitionByInstrument']
            
        # create a dictionary of encountered set classes and a count
        elif key in ['chordifySetClassHistogram']:  
            histo = {}
            for c in self.__getitem__('chordify.getElementsByClass.Chord'):
                key = c.forteClassTnI
                if key not in histo:
                    histo[key] = 0
                histo[key] += 1
            self._forms['chordifySetClassHistogram'] = histo
            return self._forms['chordifySetClassHistogram']

        # a dictionary of pitch class sets
        elif key in ['chordifyPitchClassSetHistogram']:  
            histo = {}
            for c in self.__getitem__('chordify.getElementsByClass.Chord'):
                key = c.orderedPitchClassesString
                if key not in histo:
                    histo[key] = 0
                histo[key] += 1
            self._forms['chordifyPitchClassSetHistogram'] = histo
            return self._forms['chordifyPitchClassSetHistogram']

        # dictionary of common chord types
        elif key in ['chordifyTypesHistogram']:  
            histo = {}
            # keys are methods on Chord 
            keys = ['isTriad', 'isSeventh', 'isMajorTriad', 'isMinorTriad', 
                    'isIncompleteMajorTriad', 'isIncompleteMinorTriad', 'isDiminishedTriad', 
                    'isAugmentedTriad', 'isDominantSeventh', 'isDiminishedSeventh', 
                    'isHalfDiminishedSeventh']

            for c in self.__getitem__('chordify.getElementsByClass.Chord'):
                for key in keys:
                    if key not in histo:
                        histo[key] = 0
                    # get the function attr, call it, check bool
                    if getattr(c, key)():
                        histo[key] += 1
                        # not breaking here means that we may get multiple 
                        # hits for the same chord
            self._forms['chordifyTypesHistogram'] = histo
            return self._forms['chordifyTypesHistogram']

        # a dictionary of intervals
        #self.flat.melodicIntervals(skipRests=True, skipChords=False, skipGaps=True)

        # a dictionary of quarter length values
        elif key in ['noteQuarterLengthHistogram']:  
            histo = {}
            for n in self.__getitem__('flat.notes'):
                key = n.quarterLength
                if key not in histo:
                    histo[key] = 0
                histo[key] += 1
            self._forms['noteQuarterLengthHistogram'] = histo
            return self._forms['noteQuarterLengthHistogram']

        # data lists / histograms
        elif key in ['pitchClassHistogram']:
            histo = [0] * 12
            for p in self.__getitem__('flat.pitches'): # recursive call
                histo[p.pitchClass] += 1
            self._forms['pitchClassHistogram'] = histo
            return self._forms['pitchClassHistogram']

        elif key in ['midiPitchHistogram']:
            histo = [0] * 128
            for p in self.__getitem__('flat.pitches'): # recursive call
                histo[p.midi] += 1
            self._forms['midiPitchHistogram'] = histo
            return self._forms['midiPitchHistogram']

        # bins for all abs spans between adjacent melodic notes
        elif key in ['midiIntervalHistogram']:
            # note that this does not optimize and cache part presentations            
            histo = [0] * 128
            # if we have parts, must add one at a time
            if self._base.hasPartLikeStreams():
                parts = self._base.parts
            else:
                parts = [self._base] # emulate a list
            for p in parts:
                # will be flat
                
                # edit June 2012:
                # was causing millions of deepcopy calls
                # so I made it inPlace, but for some reason
                # code errored with 'p =' not present
                # also, this part has measures...so should retainContains be True?
                p = p.stripTies(retainContainers=False, inPlace=True)
                # noNone means that we will see all connections, even w/ a gap
                post = p.findConsecutiveNotes(skipRests=True, 
                    skipChords=True, skipGaps=True, noNone=True)
                for i, n in enumerate(post):
                    if i < len(post) - 1: # if not last
                        iNext = i + 1
                        nNext = post[iNext]
                        try:
                            histo[abs(n.pitch.midi - nNext.pitch.midi)] += 1
                        except AttributeError:
                            pass # problem with not having midi
            self._forms['midiIntervalHistogram'] = histo
            return self._forms['midiIntervalHistogram']


        elif key in ['contourList']:
            # list of all directed half steps
            cList = []
            # if we have parts, must add one at a time
            if self._base.hasPartLikeStreams():
                parts = self._base.parts
            else:
                parts = [self._base] # emulate a list
            for p in parts:
                # this may be unnecessary but we cannot accessed cached part data
                
                # edit June 2012:
                # was causing lots of deepcopy calls, so I made
                # it inPlace=True, but errors when 'p =' no present
                # also, this part has measures...so should retainContains be True?
                p = p.stripTies(retainContainers=False, inPlace=True) # will be flat
                # noNone means that we will see all connections, even w/ a gap
                post = p.findConsecutiveNotes(skipRests=True, 
                    skipChords=False, skipGaps=True, noNone=True)
                for i, n in enumerate(post):
                    if i < (len(post) - 1): # if not last
                        iNext = i + 1
                        nNext = post[iNext]

                        if n.isChord:
                            ps = n.sortDiatonicAscending().pitches[-1].midi
                        else: # normal note
                            ps = n.pitch.midi
                        if nNext.isChord:
                            psNext = nNext.sortDiatonicAscending().pitches[-1].midi
                        else: # normal note
                            psNext = nNext.pitch.midi

                        cList.append(psNext - ps)
            #environLocal.printDebug(['contourList', cList])
            self._forms['contourList'] = cList
            return self._forms['contourList']


        elif key in ['flat.analyzedKey']:
            # this will use default weightings
            self._forms['analyzedKey'] = self.__getitem__('flat').analyze(
                                         method='key')
            return self._forms['analyzedKey']

        elif key in ['flat.tonalCertainty']:
            # this will use default weightings
            foundKey = self.__getitem__('flat.analyzedKey')
            self._forms['flat.tonalCertainty'] = foundKey.tonalCertainty()         
            return self._forms['flat.tonalCertainty']
        
        elif key in ['metadata']:
            self._forms['metadata'] = self._base.metadata
            return self._forms['metadata']

        elif key in ['secondsMap']:
            secondsMap = self.__getitem__('flat').secondsMap
            post = []
            # filter only notes; all elements would otherwise be gathered
            for bundle in secondsMap:
                if 'GeneralNote' in bundle['element'].classes:
                    post.append(bundle)
            self._forms['secondsMap'] = post
            return self._forms['secondsMap']

        elif key in ['assembledLyrics']:
            self._forms['assembledLyrics'] = text.assembleLyrics(self._base)
            return self._forms['assembledLyrics']
        
        else:
            raise AttributeError('no such attribute: %s' % key)

        



#-------------------------------------------------------------------------------
class DataInstance(object):
    '''
    A data instance for analysis. This object prepares a Stream 
    (by stripping ties, etc.) and stores 
    multiple commonly-used stream representations once, providing rapid processing. 
    '''
    # pylint: disable=redefined-builtin
    def __init__(self, streamObj=None, id=None): #@ReservedAssignment
        self.stream = streamObj

        # perform basic operations that are performed on all
        # streams

        # store an id for the source stream: file path url, corpus url
        # or metadata title
        if id is not None:
            self._id = id
        else:
            if hasattr(self.stream, 'metadata'): 
                self._id = self.stream.metadata # may be None

        # the attribute name in the data set for this label
        self._classLabel = None
        # store the class value for this data instance
        self._classValue = None

        # store a dictionary of StreamForms
        self._forms = StreamForms(self.stream)
        
        # if parts exist, store a forms for each
        self._formsByPart = []
        if hasattr(self.stream, 'parts'):
            self.partsCount = len(self.stream.parts)
            for p in self.stream.parts:
                # note that this will join ties and expand rests again
                self._formsByPart.append(StreamForms(p))
        else:
            self.partsCount = 0

        # TODO: store a list of voices, extracted from each part, 
        # presently this will only work on a measure stream
        self._formsByVoice = []
        if hasattr(self.stream, 'voices'):
            for v in self.stream.voices:
                self._formsByPart.append(StreamForms(v))
  
    def setClassLabel(self, classLabel, classValue=None):
        '''
        Set the class label, as well as the class value if known. 
        The class label is the attribute name used to define the class of this data instance.

        
        >>> #_DOCS_SHOW s = corpus.parse('bwv66.6')
        >>> s = stream.Stream() #_DOCS_HIDE
        >>> di = features.DataInstance(s)
        >>> di.setClassLabel('Composer', 'Bach')
        '''
        self._classLabel = classLabel
        self._classValue = classValue

    def getClassValue(self):    
        if self._classValue is None:
            return ''
        else:
            return self._classValue

    def getId(self):    
        if self._id is None:
            return ''
        else:
            # make sure there are no spaces
            return self._id.replace(' ', '_')

    def __getitem__(self, key):
        '''Get a form of this Stream, using a cached version if available.

        
        >>> s = corpus.parse('bwv66.6')
        >>> di = features.DataInstance(s)
        >>> len(di['flat'])
        193
        >>> len(di['flat.pitches'])
        163
        >>> len(di['flat.notes'])
        163
        >>> len(di['getElementsByClass.Measure'])
        40
        >>> len(di['getElementsByClass.Measure'])
        40
        >>> len(di['flat.getElementsByClass.TimeSignature'])
        4
        '''
        if key in ['parts']:
            # return a list of Forms for each part
            return self._formsByPart
        elif key in ['voices']:
            # return a list of Forms for voices
            return self._formsByVoices
        # try to create by calling the attribute
        # will raise an attribute error if there is a problem
        return self._forms[key]



#-------------------------------------------------------------------------------
class OutputFormatException(exceptions21.Music21Exception):
    pass

class OutputFormat(object):
    '''Provide output for a DataSet, passed as an initial argument.
    '''
    def __init__(self, dataSet=None):
        # assume a two dimensional array
        self._ext = None # store a file extension if necessary
        # pass a data set object
        self._dataSet = dataSet

    def getHeaderLines(self):
        '''Get the header as a list of lines.
        '''
        pass # define in subclass

    def write(self, fp=None, includeClassLabel=True, includeId=True):
        '''Write the file. If not file path is given, a temporary file will be written.
        '''
        if fp is None:
            fp = environLocal.getTempFile(suffix=self._ext)
        if not fp.endswith(self._ext):
            raise OutputFormatException("Could not get a temp file with the right extension")
        with open(fp, 'w') as f:
            f.write(self.getString(includeClassLabel=includeClassLabel, 
                                   includeId=includeId))
        return fp


class OutputTabOrange(OutputFormat):
    '''Tab delimited file format used with Orange.

    http://orange.biolab.si/doc/reference/Orange.data.formats/
    '''
    def __init__(self, dataSet=None):
        OutputFormat.__init__(self, dataSet=dataSet)
        self._ext = '.tab'

    def getHeaderLines(self, includeClassLabel=True, includeId=True):
        '''Get the header as a list of lines.

        
        >>> f = [features.jSymbolic.ChangesOfMeterFeature]
        >>> ds = features.DataSet()
        >>> ds.addFeatureExtractors(f)
        >>> of = features.OutputTabOrange(ds)
        >>> for x in of.getHeaderLines(): print(x)
        ['Identifier', 'Changes_of_Meter']
        ['string', 'discrete']
        ['meta', '']

        >>> ds = features.DataSet(classLabel='Composer')
        >>> ds.addFeatureExtractors(f)
        >>> of = features.OutputTabOrange(ds)
        >>> for x in of.getHeaderLines(): print(x)
        ['Identifier', 'Changes_of_Meter', 'Composer']
        ['string', 'discrete', 'discrete']
        ['meta', '', 'class']

        '''
        post = []
        post.append(self._dataSet.getAttributeLabels(
            includeClassLabel=includeClassLabel, includeId=includeId))

        # second row meta data
        row = []
        for x in self._dataSet.getDiscreteLabels(
            includeClassLabel=includeClassLabel, includeId=includeId):
            if x is None: # this is a string entry
                row.append('string')
            elif x is True: # if True, it is discrete
                row.append('discrete')
            else:
                row.append('continuous')
        post.append(row)

        # third row metadata
        row = []
        for x in self._dataSet.getClassPositionLabels(includeId=includeId):
            if x is None: # the id value
                row.append('meta')
            elif x is True: # if True, it is the class column
                row.append('class')
            else:
                row.append('')
        post.append(row)
        return post

    def getString(self, includeClassLabel=True, includeId=True, lineBreak=None):
        '''Get the complete DataSet as a string with the appropriate headers.
        '''
        if lineBreak is None:
            lineBreak = '\n'
        msg = []
        header = self.getHeaderLines(includeClassLabel=includeClassLabel,
                                     includeId=includeId)
        data = header + self._dataSet.getFeaturesAsList(
            includeClassLabel=includeClassLabel)
        for row in data:
            sub = []
            for e in row:
                sub.append(str(e))
            msg.append('\t'.join(sub))
        return lineBreak.join(msg)



class OutputCSV(OutputFormat):
    '''Comma-separated value list. 

    '''
    def __init__(self, dataSet=None):
        OutputFormat.__init__(self, dataSet=dataSet)
        self._ext = '.csv'

    def getHeaderLines(self, includeClassLabel=True, includeId=True):
        '''Get the header as a list of lines.

        
        >>> f = [features.jSymbolic.ChangesOfMeterFeature]
        >>> ds = features.DataSet(classLabel='Composer')
        >>> ds.addFeatureExtractors(f)
        >>> of = features.OutputCSV(ds)
        >>> of.getHeaderLines()[0]
        ['Identifier', 'Changes_of_Meter', 'Composer']
        '''
        post = []
        post.append(self._dataSet.getAttributeLabels(
            includeClassLabel=includeClassLabel, includeId=includeId))
        return post

    def getString(self, includeClassLabel=True, includeId=True, lineBreak=None):
        if lineBreak is None:
            lineBreak = '\n'
        msg = []
        header = self.getHeaderLines(includeClassLabel=includeClassLabel, 
                                    includeId=includeId)
        data = header + self._dataSet.getFeaturesAsList(
            includeClassLabel=includeClassLabel, includeId=includeId)
        for row in data:
            sub = []
            for e in row:
                sub.append(str(e))
            msg.append(','.join(sub))
        return lineBreak.join(msg)



class OutputARFF(OutputFormat):
    '''An ARFF (Attribute-Relation File Format) file.

    See http://weka.wikispaces.com/ARFF+%28stable+version%29 for more details

    
    >>> oa = features.OutputARFF()
    >>> oa._ext
    '.arff'
    '''
    def __init__(self, dataSet=None):
        OutputFormat.__init__(self, dataSet=dataSet)
        self._ext = '.arff'

    def getHeaderLines(self, includeClassLabel=True, includeId=True):
        '''Get the header as a list of lines.

        
        >>> f = [features.jSymbolic.ChangesOfMeterFeature]
        >>> ds = features.DataSet(classLabel='Composer')
        >>> ds.addFeatureExtractors(f)
        >>> of = features.OutputARFF(ds)
        >>> for x in of.getHeaderLines(): print(x)
        @RELATION Composer
        @ATTRIBUTE Identifier STRING
        @ATTRIBUTE Changes_of_Meter NUMERIC
        @ATTRIBUTE class {}
        @DATA
        
        '''
        post = []

        # get three parallel lists
        attrs = self._dataSet.getAttributeLabels(
                includeClassLabel=includeClassLabel, includeId=includeId)
        discreteLabels = self._dataSet.getDiscreteLabels(
                includeClassLabel=includeClassLabel, includeId=includeId)
        classLabels = self._dataSet.getClassPositionLabels(includeId=includeId)

        post.append('@RELATION %s' % self._dataSet.getClassLabel())

        for i, attrLabel in enumerate(attrs):
            discrete = discreteLabels[i] 
            classLabel = classLabels[i]
            if not classLabel: # a normal attribute
                if discrete is None: # this is an identifier
                    post.append('@ATTRIBUTE %s STRING' % attrLabel)
                elif discrete is True:
                    post.append('@ATTRIBUTE %s NUMERIC' % attrLabel)
                else: # this needs to be a NOMINAL type
                    post.append('@ATTRIBUTE %s NUMERIC' % attrLabel)
            else:
                values = self._dataSet.getUniqueClassValues()
                post.append('@ATTRIBUTE class {%s}' % ','.join(values))
        # include start of data declaration
        post.append('@DATA')
        return post

    def getString(self, includeClassLabel=True, includeId=True, lineBreak=None):
        if lineBreak is None:
            lineBreak = '\n'

        msg = []

        header = self.getHeaderLines(includeClassLabel=includeClassLabel, 
                                    includeId=includeId)
        for row in header:
            msg.append(row)

        data = self._dataSet.getFeaturesAsList(
                includeClassLabel=includeClassLabel)
        # data is separated by commas
        for row in data:
            sub = []
            for e in row:
                sub.append(str(e))
            msg.append(','.join(sub))
        return lineBreak.join(msg)



#-------------------------------------------------------------------------------
class DataSetException(exceptions21.Music21Exception):
    pass

class DataSet(object):
    '''
    A set of features, as well as a collection of data to operate on

    Multiple DataInstance objects, a FeatureSet, and an OutputFormat. 

    
    >>> ds = features.DataSet(classLabel='Composer')
    >>> f = [features.jSymbolic.PitchClassDistributionFeature, 
    ...      features.jSymbolic.ChangesOfMeterFeature, 
    ...      features.jSymbolic.InitialTimeSignatureFeature]
    >>> ds.addFeatureExtractors(f)
    >>> ds.addData('bwv66.6', classValue='Bach')
    >>> ds.addData('bach/bwv324.xml', classValue='Bach')
    >>> ds.process()
    >>> ds.getFeaturesAsList()[0]
    ['bwv66.6', 0.0, 1.0, 0.375, 0.03125, 0.5, 0.1875, 0.90625, 0.0, 0.4375,
     0.6875, 0.09375, 0.875, 0, 4, 4, 'Bach']
    >>> ds.getFeaturesAsList()[1]
    ['bach/bwv324.xml', 0.12, 0.0, 1.0, 0.12, 0.56..., 0.0, ..., 0.52..., 
     0.0, 0.68..., 0.0, 0.56..., 0, 4, 4, 'Bach']
    >>> ds = ds.getString()
    
    
    By default, all exceptions are caught and printed if debug mode is on.
    
    Set ds.failFast = True to not catch them.    
    
    Set ds.quiet = False to print them regardless of debug mode.
    '''

    def __init__(self, classLabel=None, featureExtractors=()):
        # assume a two dimensional array
        self.dataInstances = []
        self.streams = []
        # order of feature extractors is the order used in the presentations
        self._featureExtractors = []
        # the label of the class
        self._classLabel = classLabel
        # store a multidimensional storage of all features
        self._features = [] 
        
        self.failFast = False
        self.quiet = True
        # set extractors
        self.addFeatureExtractors(featureExtractors)
        

    def getClassLabel(self):
        return self._classLabel

    def addFeatureExtractors(self, values):
        '''
        Add one or more FeatureExtractor objects, either as a list or as an individual object. 
        '''
        # features are instantiated here
        # however, they do not have a data assignment
        if not common.isIterable(values):
            values = [values]
        # need to create instances
        for sub in values:
            self._featureExtractors.append(sub())

    def getAttributeLabels(self, includeClassLabel=True, 
        includeId=True):
        '''
        Return a list of all attribute labels. Optionally add a class 
        label field and/or an id field.

        
        >>> f = [features.jSymbolic.PitchClassDistributionFeature, 
        ...      features.jSymbolic.ChangesOfMeterFeature]
        >>> ds = features.DataSet(classLabel='Composer', featureExtractors=f)
        >>> ds.getAttributeLabels(includeId=False)
        ['Pitch_Class_Distribution_0', 
         'Pitch_Class_Distribution_1', 
         ...
         ...
         'Pitch_Class_Distribution_11', 
         'Changes_of_Meter', 
         'Composer']
        '''
        post = []
        # place ids first
        if includeId:
            post.append('Identifier')
        for fe in self._featureExtractors:
            post += fe.getAttributeLabels()
        if self._classLabel is not None and includeClassLabel:
            post.append(self._classLabel.replace(' ', '_'))
        return post

    def getDiscreteLabels(self, includeClassLabel=True, includeId=True):
        '''Return column labels for discrete status.

        
        >>> f = [features.jSymbolic.PitchClassDistributionFeature, 
        ...      features.jSymbolic.ChangesOfMeterFeature]
        >>> ds = features.DataSet(classLabel='Composer', featureExtractors=f)
        >>> ds.getDiscreteLabels()
        [None, False, False, False, False, False, False, False, False, False, 
         False, False, False, True, True]
        '''
        post = []
        if includeId:
            post.append(None) # just a spacer
        for fe in self._featureExtractors:
            # need as many statements of discrete as there are dimensions
            post += [fe.discrete] * fe.dimensions 
        # class label is assumed always discrete
        if self._classLabel is not None and includeClassLabel:
            post.append(True)
        return post

    def getClassPositionLabels(self, includeId=True):
        '''Return column labels for the presence of a class definition

        >>> f = [features.jSymbolic.PitchClassDistributionFeature, 
        ...      features.jSymbolic.ChangesOfMeterFeature]
        >>> ds = features.DataSet(classLabel='Composer', featureExtractors=f)
        >>> ds.getClassPositionLabels()
        [None, False, False, False, False, False, False, False, False, 
         False, False, False, False, False, True]
        '''
        post = []
        if includeId:
            post.append(None) # just a spacer
        for fe in self._featureExtractors:
            # need as many statements of discrete as there are dimensions
            post += [False] * fe.dimensions 
        # class label is assumed always discrete
        if self._classLabel is not None:
            post.append(True)
        return post

    # pylint: disable=redefined-builtin    
    def addData(self, dataOrStreamOrPath, classValue=None, id=None): #@ReservedAssignment
        '''Add a Stream, DataInstance, or path to a corpus or local file to this data set.

        The class value passed here is assumed to be the same as 
        the classLabel assigned at startup. 
        '''
        if self._classLabel is None:
            raise DataSetException(
                    'cannot add data unless a class label for this DataSet has been set.')

        s = None
        if isinstance(dataOrStreamOrPath, DataInstance):
            di = dataOrStreamOrPath
            s = di.stream
        elif isinstance(dataOrStreamOrPath, six.string_types):
            # could be corpus or file path
            if os.path.exists(dataOrStreamOrPath) or dataOrStreamOrPath.startswith('http'):
                s = converter.parse(dataOrStreamOrPath)
            else: # assume corpus
                s = corpus.parse(dataOrStreamOrPath)
            # assume we can use this string as an id
            di = DataInstance(s, id=dataOrStreamOrPath)
        else:        
            # for now, assume all else are streams
            s = dataOrStreamOrPath
            di = DataInstance(dataOrStreamOrPath, id=id)

        di.setClassLabel(self._classLabel, classValue)
        self.dataInstances.append(di)
        self.streams.append(s)

    def process(self):
        '''
        Process all Data with all FeatureExtractors. 
        Processed data is stored internally as numerous Feature objects. 
        '''
        # clear features
        self._features = []
        for data in self.dataInstances:
            row = []
            for fe in self._featureExtractors:
                fe.setData(data)
                # in some cases there might be problem; to not fail 
                try:
                    fReturned = fe.extract()
                except Exception as e: # for now take any error  # pylint: disable=broad-except
                    fList = ['failed feature extractor:', fe, str(e)]
                    if self.quiet is True:                   
                        environLocal.printDebug(fList)
                    else:
                        environLocal.warn(fList)
                    if self.failFast is True:
                        raise e
                    # provide a blank feature extractor
                    fReturned = fe.getBlankFeature()

                row.append(fReturned) # get feature and store
            # rows will align with data the order of DataInstances
            self._features.append(row)

    def getFeaturesAsList(self, includeClassLabel=True, includeId=True, concatenateLists=True):
        '''
        Get processed data as a list of lists, merging any sub-lists 
        in multi-dimensional features. 
        '''
        post = []
        for i, row in enumerate(self._features):
            v = []
            di = self.dataInstances[i]

            if includeId:
                v.append(di.getId())
            for f in row:
                if concatenateLists:
                    v += f.vector
                else:
                    v.append(f.vector)
            if includeClassLabel:
                v.append(di.getClassValue())
            post.append(v)
        if not includeClassLabel and not includeId:
            return post[0]
        else:
            return post

    def getUniqueClassValues(self):
        '''
        Return a list of unique class values.
        '''
        post = []
        for di in self.dataInstances:
            v = di.getClassValue()
            if v not in post:
                post.append(v)
        return post

    def _getOutputFormat(self, featureFormat):
        if featureFormat.lower() in ['tab', 'orange', 'taborange', None]:
            outputFormat = OutputTabOrange(dataSet=self)
        elif featureFormat.lower() in ['csv', 'comma']:
            outputFormat = OutputCSV(dataSet=self)
        elif featureFormat.lower() in ['arff', 'attribute']:
            outputFormat = OutputARFF(dataSet=self)
        else:
            return None
        return outputFormat

    def _getOutputFormatFromFilePath(self, fp):
        '''
        Get an output format from a file path if possible, otherwise return None.
        
        >>> ds = features.DataSet()
        >>> ds._getOutputFormatFromFilePath('test.tab')
        <music21.features.base.OutputTabOrange object at ...>
        >>> ds._getOutputFormatFromFilePath('test.csv')
        <music21.features.base.OutputCSV object at ...>
        >>> ds._getOutputFormatFromFilePath('junk') is None
        True

        '''
        # get format from fp if possible
        of = None
        if '.' in fp:
            if self._getOutputFormat(fp.split('.')[-1]) is not None:
                of = self._getOutputFormat(fp.split('.')[-1])
        return of


    def getString(self, outputFmt='tab'):
        '''Get a string representation of the data set in a specific format.
        '''
        # pass reference to self to output
        outputFormat = self._getOutputFormat(outputFmt)
        return outputFormat.getString()

    # pylint: disable=redefined-builtin
    def write(self, fp=None, format=None, includeClassLabel=True): #@ReservedAssignment
        '''
        Set the output format object. 
        '''
        if format is None and fp is not None:
            outputFormat = self._getOutputFormatFromFilePath(fp)
        else:
            outputFormat = self._getOutputFormat(format)
        if OutputFormat is None:
            raise DataSetException('no output format could be defined from file path ' + 
                                   '%s or format %s' % (fp, format))

        outputFormat.write(fp=fp, includeClassLabel=includeClassLabel)
        
def allFeaturesAsList(streamInput):
    '''
    returns a tuple containing ALL currentingly implemented feature extractors. The first
    in the tuple are jsymbolic vectors, and the second native vectors. Vectors are NOT nested
    
    streamInput can be Add a Stream, DataInstance, or path to a corpus or local 
    file to this data set.
    
    
    >>> s = converter.parse('tinynotation: 4/4 c4 d e2')
    >>> f = features.allFeaturesAsList(s)
    >>> f[1][0:3]
    [[1], [0.689999...], [2]]
    >>> len(f[0]) > 65
    True
    >>> len(f[1]) > 20
    True
    '''
    from music21.features import jSymbolic, native
    ds = DataSet(classLabel='')
    f = [f for f in jSymbolic.featureExtractors]
    ds.addFeatureExtractors(f)
    ds.addData(streamInput)
    ds.process()
    jsymb = ds.getFeaturesAsList(includeClassLabel=False, includeId=False, concatenateLists=False)
    ds._featureExtractors = []
    ds._features = []
    n = [f for f in native.featureExtractors]
    ds.addFeatureExtractors(n)
    ds.process()
    nat = ds.getFeaturesAsList(includeClassLabel=False, includeId=False, concatenateLists=False)
            
    return (jsymb, nat)


#-------------------------------------------------------------------------------
def extractorsById(idOrList, library=('jSymbolic', 'native')):
    '''
    Given one or more :class:`~music21.features.FeatureExtractor` ids, return the 
    appropriate  subclass. An optional `library` argument can be added to define which 
    module is used. Current options are jSymbolic and native.
    
    >>> features.extractorsById('p20')
    [<class 'music21.features.jSymbolic.PitchClassDistributionFeature'>]
    
    >>> [x.id for x in features.extractorsById('p20')]
    ['P20']
    >>> [x.id for x in features.extractorsById(['p19', 'p20'])]
    ['P19', 'P20']


    Normalizes case...

    >>> [x.id for x in features.extractorsById(['r31', 'r32', 'r33', 'r34', 'r35', 'p1', 'p2'])]
    ['R31', 'R32', 'R33', 'R34', 'R35', 'P1', 'P2']
    
    Get all feature extractors from all libraries   
    
    >>> y = [x.id for x in features.extractorsById('all')]
    >>> y[0:3], y[-3:-1]
    (['M1', 'M2', 'M3'], ['MD1', 'MC1'])

    '''
    from music21.features import jSymbolic
    from music21.features import native

    if not common.isIterable(library):
        library = [library]

    featureExtractors = []
    for l in library:
        if l.lower() in ['jsymbolic', 'all']:
            featureExtractors += jSymbolic.featureExtractors
        elif l.lower() in ['native', 'all']:
            featureExtractors += native.featureExtractors

    if not common.isIterable(idOrList):
        idOrList = [idOrList]

    flatIds = []
    for featureId in idOrList:
        featureId = featureId.strip().lower()
        featureId.replace('-', '')
        featureId.replace(' ', '')
        flatIds.append(featureId)

    post = []
    if len(flatIds) == 0:
        return post
    
    for fe in featureExtractors:
        if fe.id.lower() in flatIds or flatIds[0].lower() == 'all':
            post.append(fe)
    return post


def extractorById(idOrList, library=('jSymbolic', 'native')):
    '''
    Get the first feature matched by extractorsById().

    >>> s = stream.Stream()
    >>> s.append(note.Note('A4'))
    >>> fe = features.extractorById('p20')(s) # call class
    >>> fe.extract().vector
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]

    '''
    ebi = extractorsById(idOrList=idOrList, library=library)
    if ebi:
        return ebi[0]
    return None # no match


def vectorById(streamObj, vectorId, library=('jSymbolic', 'native')):
    '''
    Utility function to get a vector from an extractor

    >>> s = stream.Stream()
    >>> s.append(note.Note('A4'))
    >>> features.vectorById(s, 'p20')
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    '''
    fe = extractorById(vectorId)(streamObj) # call class with stream
    if fe is None:
        return None # could raise exception
    return fe.extract().vector

def getIndex(featureString, extractorType=None):
    '''
    Returns the list index of the given feature extractor and the feature extractor
    category (jsymbolic or native). If feature extractor string is not in either 
    jsymbolic or native feature extractors, returns None
    
    optionally include the extractorType ('jsymbolic' or 'native') if known
    and searching will be made more efficient
    
    
    >>> features.getIndex('Range')
    (59, 'jsymbolic')
    >>> features.getIndex('Ends With Landini Melodic Contour')
    (19, 'native')
    >>> features.getIndex('abrandnewfeature!')
    >>> features.getIndex('Fifths Pitch Histogram','jsymbolic')
    (68, 'jsymbolic')
    >>> features.getIndex('Tonal Certainty','native')
    (1, 'native')
    '''
    from music21.features import jSymbolic, native

    if extractorType is None or extractorType == 'jsymbolic':
        indexcnt = 0
        for feature in jSymbolic.featureExtractors:
    
            if feature().name  == featureString:
                return (indexcnt, 'jsymbolic')
            indexcnt += 1
    if extractorType is None or extractorType == 'native':
        indexcnt = 0  
        for feature in native.featureExtractors:
            if feature().name == featureString:
                return (indexcnt, 'native')
            indexcnt += 1
        
        return None
    
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

#    def testGetAllExtractorsMethods(self):
#        '''
#        ahh..this test taks a realy long time....
#        '''
#        from music21 import stream, features, pitch
#        s = corpus.parse('bwv66.6').measures(1,5)
#        self.assertEqual( len(features.alljSymbolicFeatures(s)), 70)
#        self.assertEqual(len (features.allNativeFeatures(s)),21)
#        self.assertEqual(str(features.alljSymbolicVectors(s)[1:5]), 
#'[[2.6630434782608696], [2], [2], [0.391304347826087]]')
#        self.assertEqual(str(features.allNativeVectors(s)[0:4]),
#'[[1], [1.0328322202181006], [2], [1.0]]')

    def testStreamFormsA(self):

        from music21 import features

        s = corpus.parse('corelli/opus3no1/1grave')
        di = features.DataInstance(s)
        self.assertEqual(len(di['flat']), 291)
        self.assertEqual(len(di['flat.notes']), 238)

        #di['chordify'].show('t')
        self.assertEqual(len(di['chordify']), 20)
        self.assertEqual(len(di['chordify.getElementsByClass.Chord']), 144)


        self.assertEqual(di['chordifySetClassHistogram'], 
                         {'2-2': 6, '2-3': 12, '2-4': 21, '2-5': 5, 
                          '3-10': 4, '3-11': 33, '3-2': 3, '3-4': 7,
                          '3-6': 7, '3-7': 9, '3-8': 6, '3-9': 16,
                          '1-1': 15})

        self.maxDiff = None
        self.assertEqual(di['chordifyTypesHistogram'], 
                           {'isMinorTriad': 8, 'isAugmentedTriad': 0, 
                            'isTriad': 37, 'isSeventh': 0, 'isDiminishedTriad': 4, 
                            'isDiminishedSeventh': 0, 'isIncompleteMajorTriad': 21, 
                            'isHalfDiminishedSeventh': 0, 'isMajorTriad': 25, 
                            'isDominantSeventh': 0, 'isIncompleteMinorTriad': 12})

        self.assertEqual(di['noteQuarterLengthHistogram'], 
                         {0.5: 116, 1.0: 39, 1.5: 27, 2.0: 31, 3.0: 2, 4.0: 3, 
                          0.75: 4, 0.25: 16})


        # can access parts by index
        self.assertEqual(len(di['parts']), 3)
        # stored in parts are StreamForms instances, caching their results
        self.assertEqual(len(di['parts'][0]['flat.notes']), 71)
        self.assertEqual(len(di['parts'][1]['flat.notes']), 66)

        # getting a measure by part
        self.assertEqual(len(di['parts'][0]['getElementsByClass.Measure']), 19)
        self.assertEqual(len(di['parts'][1]['getElementsByClass.Measure']), 19)

        self.assertEqual(di['parts'][0]['pitchClassHistogram'], 
                         [9, 1, 11, 0, 9, 13, 0, 11, 0, 12, 5, 0])
        # the sum of the two arrays is the pitch class histogram of the complete
        # work
        self.assertEqual(di['pitchClassHistogram'], 
                         [47, 2, 25, 0, 25, 42, 0, 33, 0, 38, 22, 4])


    def testStreamFormsB(self):

        from music21 import features, note

        s = stream.Stream()
        for p in ['c4', 'c4', 'd-4', 'd#4', 'f#4', 'a#4', 'd#5', 'a5', 'a5']:
            s.append(note.Note(p))
        di = features.DataInstance(s)
        self.assertEqual(di['midiIntervalHistogram'], 
                         [2, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])



    def testStreamFormsC(self):
        from pprint import pformat
        from music21 import features, note

        s = stream.Stream()
        for p in ['c4', 'c4', 'd-4', 'd#4', 'f#4', 'a#4', 'd#5', 'a5']:
            s.append(note.Note(p))
        di = features.DataInstance(s)

        self.assertEqual(pformat(di['secondsMap']), """[{'durationSeconds': 0.5,
  'element': <music21.note.Note C>,
  'endTimeSeconds': 0.5,
  'offsetSeconds': 0.0,
  'voiceIndex': None},
 {'durationSeconds': 0.5,
  'element': <music21.note.Note C>,
  'endTimeSeconds': 1.0,
  'offsetSeconds': 0.5,
  'voiceIndex': None},
 {'durationSeconds': 0.5,
  'element': <music21.note.Note D->,
  'endTimeSeconds': 1.5,
  'offsetSeconds': 1.0,
  'voiceIndex': None},
 {'durationSeconds': 0.5,
  'element': <music21.note.Note D#>,
  'endTimeSeconds': 2.0,
  'offsetSeconds': 1.5,
  'voiceIndex': None},
 {'durationSeconds': 0.5,
  'element': <music21.note.Note F#>,
  'endTimeSeconds': 2.5,
  'offsetSeconds': 2.0,
  'voiceIndex': None},
 {'durationSeconds': 0.5,
  'element': <music21.note.Note A#>,
  'endTimeSeconds': 3.0,
  'offsetSeconds': 2.5,
  'voiceIndex': None},
 {'durationSeconds': 0.5,
  'element': <music21.note.Note D#>,
  'endTimeSeconds': 3.5,
  'offsetSeconds': 3.0,
  'voiceIndex': None},
 {'durationSeconds': 0.5,
  'element': <music21.note.Note A>,
  'endTimeSeconds': 4.0,
  'offsetSeconds': 3.5,
  'voiceIndex': None}]""", pformat(di['secondsMap']))


    def testDataSetOutput(self):
        from music21 import features
        # test just a few features
        featureExtractors = features.extractorsById(['ql1', 'ql2', 'ql4'], 'native')
        
        # need to define what the class label will be
        ds = features.DataSet(classLabel='Composer')
        ds.addFeatureExtractors(featureExtractors)
        
        # add works, defining the class value 
        ds.addData('bwv66.6', classValue='Bach')
        ds.addData('corelli/opus3no1/1grave', classValue='Corelli')
        
        ds.process()

        # manually create an output format and get output
        of = OutputCSV(ds)
        post = of.getString(lineBreak='//')
        self.assertEqual(post, 'Identifier,Unique_Note_Quarter_Lengths,' + 
                'Most_Common_Note_Quarter_Length,Range_of_Note_Quarter_Lengths,' + 
                'Composer//bwv66.6,3,1.0,1.5,Bach//corelli/opus3no1/1grave,8,0.5,3.75,Corelli')

        # without id
        post = of.getString(lineBreak='//', includeId=False)
        self.assertEqual(post, 'Unique_Note_Quarter_Lengths,Most_Common_Note_Quarter_Length,' + 
                'Range_of_Note_Quarter_Lengths,Composer//3,1.0,1.5,Bach//8,0.5,3.75,Corelli')

        ds.write(format='tab')
        ds.write(format='csv')
        ds.write(format='arff')



    def testFeatureFail(self):
        from music21 import features
        from music21 import base

        featureExtractors = ['p10', 'p11', 'p12', 'p13']

    
        featureExtractors = features.extractorsById(featureExtractors, 
                            'jSymbolic')

        ds = features.DataSet(classLabel='Composer')
        ds.addFeatureExtractors(featureExtractors)
        
        # create problematic streams
        s = stream.Stream()
        #s.append(None) # will create a wrapper -- NOT ANYMORE
        s.append(base.ElementWrapper(None))
        ds.addData(s, classValue='Monteverdi')
        ds.addData(s, classValue='Handel')
        
        # process with all feature extractors, store all features
        ds.process()



    #---------------------------------------------------------------------------
    # silent tests


    def xtestComposerClassificationJSymbolic(self):
        '''
        Demonstrating writing out data files for feature extraction. Here, 
        features are used from the jSymbolic library.
        '''
        from music21 import features
                
        featureExtractors = ['r31', 'r32', 'r33', 'r34', 'r35', 'p1', 'p2', 'p3', 
                             'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p12', 
                             'p13', 'p14', 'p15', 'p16', 'p19', 'p20', 'p21']
        
        # will return a list
        featureExtractors = features.extractorsById(featureExtractors, 
                            'jSymbolic')
        
        #worksBach = corpus.getBachChorales()[100:143] # a middle range
        worksMonteverdi = corpus.getMonteverdiMadrigals()[:43]
        
        worksBach = corpus.getBachChorales()[:5] 
#         worksMonteverdi = corpus.getMonteverdiMadrigals()[:5]
        
        # need to define what the class label will be
        ds = features.DataSet(classLabel='Composer')
        ds.addFeatureExtractors(featureExtractors)
        
        # add works, defining the class value 
#         for w in worksBach:
#             ds.addData(w, classValue='Bach')
        for w in worksMonteverdi:
            ds.addData(w, classValue='Monteverdi')
        for w in worksBach:
            ds.addData(w, classValue='Bach')
        
        # process with all feature extractors, store all features
        ds.process()
        ds.write(format='tab')
        ds.write(format='csv')
        ds.write(format='arff')




    def xtestRegionClassificationJSymbolicA(self):
        '''
        Demonstrating writing out data files for feature extraction. Here, 
        features are used from the jSymbolic library.
        '''
        from music21 import features

        featureExtractors = features.extractorsById(['r31', 'r32', 'r33', 'r34', 'r35', 
                                                     'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 
                                                     'p7', 'p8', 'p9', 'p10', 'p11', 'p12', 
                                                     'p13', 'p14', 'p15', 'p16', 'p19', 
                                                     'p20', 'p21'], 'jSymbolic')

        oChina1 = corpus.parse('essenFolksong/han1')
        oChina2 = corpus.parse('essenFolksong/han2')

        oMitteleuropa1 = corpus.parse('essenFolksong/boehme10')
        oMitteleuropa2 = corpus.parse('essenFolksong/boehme20')

        ds = features.DataSet(classLabel='Region')
        ds.addFeatureExtractors(featureExtractors)
        
        # add works, defining the class value 
        for o, name in [(oChina1, 'han1'), 
                        (oChina2, 'han2')]:
            for w in o.scores:
                songId = 'essenFolksong/%s-%s' % (name, w.metadata.number)
                ds.addData(w, classValue='China', id=songId)

        for o, name in [(oMitteleuropa1, 'boehme10'), 
                        (oMitteleuropa2, 'boehme20')]:
            for w in o.scores:
                songId = 'essenFolksong/%s-%s' % (name, w.metadata.number)
                ds.addData(w, classValue='Mitteleuropa', id=songId)

        # process with all feature extractors, store all features
        ds.process()
        ds.getString(format='tab') # pylint: disable=unexpected-keyword-arg
        ds.getString(format='csv') # pylint: disable=unexpected-keyword-arg
        ds.getString(format='arff') # pylint: disable=unexpected-keyword-arg



    def xtestRegionClassificationJSymbolicB(self):
        '''
        Demonstrating writing out data files for feature extraction. 
        Here, features are used from the jSymbolic library.
        '''
        from music21 import features

        # features common to both collections
        featureExtractors = features.extractorsById(
                            ['r31', 'r32', 'r33', 'r34', 'r35', 'p1', 'p2', 'p3', 'p4', 
                             'p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p12', 'p13', 
                             'p14', 'p15', 'p16', 'p19', 'p20', 'p21'], 'jSymbolic')

        # first bundle
        ds = features.DataSet(classLabel='Region')
        ds.addFeatureExtractors(featureExtractors)

        oChina1 = corpus.parse('essenFolksong/han1')
        oMitteleuropa1 = corpus.parse('essenFolksong/boehme10')
        
        # add works, defining the class value 
        for o, name in [(oChina1, 'han1')]:
            for w in o.scores:
                songId = 'essenFolksong/%s-%s' % (name, w.metadata.number)
                ds.addData(w, classValue='China', id=songId)

        for o, name in [(oMitteleuropa1, 'boehme10')]:
            for w in o.scores:
                songId = 'essenFolksong/%s-%s' % (name, w.metadata.number)
                ds.addData(w, classValue='Mitteleuropa', id=songId)

        # process with all feature extractors, store all features
        ds.process()
        ds.write('/_scratch/chinaMitteleuropaSplit-a.tab')
        ds.write('/_scratch/chinaMitteleuropaSplit-a.csv')
        ds.write('/_scratch/chinaMitteleuropaSplit-a.arff')

        # create second data set from alternate collections
        ds = features.DataSet(classLabel='Region')
        ds.addFeatureExtractors(featureExtractors)

        oChina2 = corpus.parse('essenFolksong/han2')
        oMitteleuropa2 = corpus.parse('essenFolksong/boehme20')
        # add works, defining the class value 
        for o, name in [(oChina2, 'han2')]:
            for w in o.scores:
                songId = 'essenFolksong/%s-%s' % (name, w.metadata.number)
                ds.addData(w, classValue='China', id=songId)

        for o, name in [(oMitteleuropa2, 'boehme20')]:
            for w in o.scores:
                songId = 'essenFolksong/%s-%s' % (name, w.metadata.number)
                ds.addData(w, classValue='Mitteleuropa', id=songId)

        # process with all feature extractors, store all features
        ds.process()
        ds.write('/_scratch/chinaMitteleuropaSplit-b.tab')
        ds.write('/_scratch/chinaMitteleuropaSplit-b.csv')
        ds.write('/_scratch/chinaMitteleuropaSplit-b.arff')


    def xtestOrangeBayesA(self):
        '''Using an already created test file with a BayesLearner.
        '''
        import orange # @UnresolvedImport # pylint: disable=import-error
        data = orange.ExampleTable(
            '~/music21Ext/mlDataSets/bachMonteverdi-a/bachMonteverdi-a.tab')
        classifier = orange.BayesLearner(data)
        for i in range(len(data)):
            c = classifier(data[i])
            print("original", data[i].getclass(), "BayesLearner:", c)


    def xtestClassifiersA(self):
        '''Using an already created test file with a BayesLearner.
        '''
        import orange, orngTree # @UnresolvedImport  # pylint: disable=import-error
        data1 = orange.ExampleTable(
                '~/music21Ext/mlDataSets/chinaMitteleuropa-b/chinaMitteleuropa-b1.tab')
        
        data2 = orange.ExampleTable(
                '~/music21Ext/mlDataSets/chinaMitteleuropa-b/chinaMitteleuropa-b2.tab')
        
        majority = orange.MajorityLearner
        bayes = orange.BayesLearner
        tree = orngTree.TreeLearner
        knn = orange.kNNLearner
        
        for classifierType in [majority, bayes, tree, knn]:
            print('')
            for classifierData, classifierStr, matchData, matchStr in [
                (data1, 'data1', data1, 'data1'), 
                (data1, 'data1', data2, 'data2'),
                (data2, 'data2', data2, 'data2'), 
                (data2, 'data2', data1, 'data1'),
                ]:
        
                # train with data1
                classifier = classifierType(classifierData)
                mismatch = 0
                for i in range(len(matchData)):
                    c = classifier(matchData[i])
                    if c != matchData[i].getclass():
                        mismatch += 1
        
                print('%s %s: misclassified %s/%s of %s' % (
                        classifierStr, classifierType, mismatch, len(matchData), matchStr))

#             if classifierType == orngTree.TreeLearner:
#                 orngTree.printTxt(classifier)



    def xtestClassifiersB(self):
        '''Using an already created test file with a BayesLearner.
        '''
        import orange, orngTree # @UnresolvedImport # pylint: disable=import-error
        data1 = orange.ExampleTable(
                '~/music21Ext/mlDataSets/chinaMitteleuropa-b/chinaMitteleuropa-b1.tab')
        
        data2 = orange.ExampleTable(
                '~/music21Ext/mlDataSets/chinaMitteleuropa-b/chinaMitteleuropa-b2.tab', 
                use=data1.domain)
        
        data1.extend(data2)
        data = data1
        
        majority = orange.MajorityLearner
        bayes = orange.BayesLearner
        tree = orngTree.TreeLearner
        knn = orange.kNNLearner
        
        folds = 10
        for classifierType in [majority, bayes, tree, knn]:
            print('')
        
            cvIndices = orange.MakeRandomIndicesCV(data, folds)    
            for fold in range(folds):
                train = data.select(cvIndices, fold, negate=1)
                test = data.select(cvIndices, fold)
        
                for classifierData, classifierStr, matchData, matchStr in [
                    (train, 'train', test, 'test'),
                    ]:
        
                    # train with data1
                    classifier = classifierType(classifierData)
                    mismatch = 0
                    for i in range(len(matchData)):
                        c = classifier(matchData[i])
                        if c != matchData[i].getclass():
                            mismatch += 1
            
                    print('%s %s: misclassified %s/%s of %s' % (
                            classifierStr, classifierType, mismatch, len(matchData), matchStr))


    def xtestOrangeClassifiers(self):
        '''
        This test shows how to compare four classifiers; replace the file path 
        with a path to the .tab data file. 
        '''
        import orange, orngTree # @UnresolvedImport # pylint: disable=import-error
        data = orange.ExampleTable('~/music21Ext/mlDataSets/bachMonteverdi-a/bachMonteverdi-a.tab')

        # setting up the classifiers
        majority = orange.MajorityLearner(data)
        bayes = orange.BayesLearner(data)
        tree = orngTree.TreeLearner(data, sameMajorityPruning=1, mForPruning=2)
        knn = orange.kNNLearner(data, k=21)
        
        majority.name="Majority"
        bayes.name="Naive Bayes"
        tree.name="Tree"
        knn.name="kNN"        
        classifiers = [majority, bayes, tree, knn]
        
        # print the head
        print("Possible classes:", data.domain.classVar.values)
        print("Original Class", end=' ')
        for l in classifiers:
            print("%-13s" % (l.name), end=' ')
        print()
        
        for example in data:
            print("(%-10s)  " % (example.getclass()), end=' ')
            for c in classifiers:
                p = c([example, orange.GetProbabilities])
                print("%5.3f        " % (p[0]), end=' ')
            print("")


    def xtestOrangeClassifierTreeLearner(self):
        import orange, orngTree # @UnresolvedImport # pylint: disable=import-error
        data = orange.ExampleTable('~/music21Ext/mlDataSets/bachMonteverdi-a/bachMonteverdi-a.tab')

        tree = orngTree.TreeLearner(data, sameMajorityPruning=1, mForPruning=2)
        #tree = orngTree.TreeLearner(data)
        for i in range(len(data)):
            p = tree(data[i], orange.GetProbabilities)
            print("%d: %5.3f (originally %s)" % (i+1, p[1], data[i].getclass()))

        orngTree.printTxt(tree)


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [FeatureExtractor]


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
    

#------------------------------------------------------------------------------
# eof





