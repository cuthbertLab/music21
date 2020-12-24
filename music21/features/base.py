# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         features/base.py
# Purpose:      Feature extractors base classes.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2017 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import os
import pathlib
import pickle
import unittest

from collections import Counter

from music21 import common
from music21 import converter
from music21 import corpus
from music21 import exceptions21
from music21 import stream
from music21 import text

from music21.metadata.bundles import MetadataEntry

from music21 import environment
_MOD = 'features.base'
environLocal = environment.Environment(_MOD)

# ------------------------------------------------------------------------------


class FeatureException(exceptions21.Music21Exception):
    pass


class Feature:
    '''
    An object representation of a feature, capable of presentation in a variety of formats,
    and returned from FeatureExtractor objects.

    Feature objects are simple. It is FeatureExtractors that store all metadata and processing
    routines for creating Feature objects.  Normally you wouldn't create one of these yourself.

    >>> myFeature = features.Feature()
    >>> myFeature.dimensions = 3
    >>> myFeature.name = 'Random arguments'
    >>> myFeature.isSequential = True

    This is a continuous Feature so we will set discrete to false.

    >>> myFeature.discrete = False

    The .vector is the most important part of the feature, and it starts out as None.

    >>> myFeature.vector is None
    True

    Calling .prepareVector() gives it a list of Zeros of the length of dimensions.

    >>> myFeature.prepareVectors()

    >>> myFeature.vector
    [0, 0, 0]

    Now we can set the vector parts:

    >>> myFeature.vector[0] = 4
    >>> myFeature.vector[1] = 2
    >>> myFeature.vector[2] = 1

    It's okay just to assign a new list to .vector itself.

    There is a normalize() method which normalizes the values
    of a histogram to sum to 1.

    >>> myFeature.normalize()
    >>> myFeature.vector
    [0.571..., 0.285..., 0.142...]

    And that's it! FeatureExtractors are much more interesting.
    '''

    def __init__(self):
        # these values will be filled by the extractor
        self.dimensions = None  # number of dimensions
        # data storage; possibly use numpy array
        self.vector = None

        # consider not storing this values, as may not be necessary
        self.name = None  # string name representation
        self.description = None  # string description
        self.isSequential = None  # True or False
        self.discrete = None  # is discrete or continuous

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
        Normalizes the vector so that the sum of its elements is 1.
        '''
        s = sum(self.vector)
        try:
            scalar = 1.0 / s  # get floating point scalar for speed
        except ZeroDivisionError:
            raise FeatureException('cannot normalize zero vector')
        temp = self._getVectors()
        for i, v in enumerate(self.vector):
            temp[i] = v * scalar
        self.vector = temp


# ------------------------------------------------------------------------------
class FeatureExtractorException(exceptions21.Music21Exception):
    pass


class FeatureExtractor:
    '''
    A model of process that extracts a feature from a Music21 Stream.
    The main public interface is the extract() method.

    The extractor can be passed a Stream or a reference to a DataInstance.
    All Streams are internally converted to a DataInstance if necessary.
    Usage of a DataInstance offers significant performance advantages, as common forms of
    the Stream are cached for easy processing.
    '''

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        self.stream = None  # the original Stream, or None
        self.data = None  # a DataInstance object: use to get data
        self.setData(dataOrStream)

        self.feature = None  # Feature object that results from processing

        if not hasattr(self, 'name'):
            self.name = None  # string name representation
        if not hasattr(self, 'description'):
            self.description = None  # string description
        if not hasattr(self, 'isSequential'):
            self.isSequential = None  # True or False
        if not hasattr(self, 'dimensions'):
            self.dimensions = None  # number of dimensions
        if not hasattr(self, 'discrete'):
            self.discrete = True  # default
        if not hasattr(self, 'normalize'):
            self.normalize = False  # default is no

    def setData(self, dataOrStream):
        '''
        Set the data that this FeatureExtractor will process.
        Either a Stream or a DataInstance object can be provided.
        '''
        if dataOrStream is not None:
            if (hasattr(dataOrStream, 'classes')
                    and 'Stream' in dataOrStream.classes):
                # environLocal.printDebug(['creating new DataInstance: this should be a Stream:',
                #     dataOrStream])
                # if we are passed a stream, create a DataInstance to
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
                post.append(f"{self.name.replace(' ', '_')}_{i}")
        return post

    def fillFeatureAttributes(self, feature=None):
        '''Fill the attributes of a Feature with the descriptors in the FeatureExtractor.
        '''
        # operate on passed-in feature or self.feature
        if feature is None:
            feature = self.feature
        feature.name = self.name
        feature.description = self.description
        feature.isSequential = self.isSequential
        feature.dimensions = self.dimensions
        feature.discrete = self.discrete
        return feature

    def prepareFeature(self):
        '''
        Prepare a new Feature object for data acquisition.

        >>> s = stream.Stream()
        >>> fe = features.jSymbolic.InitialTimeSignatureFeature(s)
        >>> fe.prepareFeature()
        >>> fe.feature.name
        'Initial Time Signature'
        >>> fe.feature.dimensions
        2
        >>> fe.feature.vector
        [0, 0]
        '''
        self.feature = Feature()
        self.fillFeatureAttributes()  # will fill self.feature
        self.feature.prepareVectors()  # will vector with necessary zeros

    def process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # do work in subclass, calling on self.data
        pass

    def extract(self, source=None):
        '''Extract the feature and return the result.
        '''
        if source is not None:
            self.stream = source
        # preparing the feature always sets self.feature to a new instance
        self.prepareFeature()
        self.process()  # will set Feature object to _feature
        if self.normalize:
            self.feature.normalize()
        return self.feature

    def getBlankFeature(self):
        '''
        Return a properly configured plain feature as a place holder

        >>> from music21 import features
        >>> fe = features.jSymbolic.InitialTimeSignatureFeature()
        >>> fe.name
        'Initial Time Signature'

        >>> blankF = fe.getBlankFeature()
        >>> blankF.vector
        [0, 0]
        >>> blankF.name
        'Initial Time Signature'
        '''
        f = Feature()
        self.fillFeatureAttributes(f)
        f.prepareVectors()  # will vector with necessary zeros
        return f


# ------------------------------------------------------------------------------
class StreamForms:
    '''
    A dictionary-like wrapper of a Stream, providing
    numerous representations, generated on-demand, and cached.

    A single StreamForms object can be created for an
    entire Score, as well as one for each Part and/or Voice.

    A DataSet object manages one or more StreamForms
    objects, and exposes them to FeatureExtractors for usage.

    The streamObj is stored as self.stream and if "prepared" then
    the prepared form is stored as .prepared

    A dictionary `.forms` stores various intermediary representations
    of the stream which is the main power of this routine, making
    it simple to add additional feature extractors at low additional
    time cost.

    '''

    def __init__(self, streamObj, prepareStream=True):
        self.stream = streamObj
        if self.stream is not None:
            if prepareStream:
                self.prepared = self._prepareStream(self.stream)
            else:
                self.prepared = self.stream
        else:
            self.prepared = None

        # basic data storage is a dictionary
        self.forms = {}

    def keys(self):
        # will only return forms that are established
        return self.forms.keys()

    def _prepareStream(self, streamObj):
        '''
        Common routines done on Streams prior to processing. Returns a new Stream

        Currently: runs stripTies.
        '''
        # this causes lots of deepcopies, but an inPlace operation loses
        # accuracy on feature extractors
        streamObj = streamObj.stripTies()
        return streamObj

    def __getitem__(self, key):
        '''
        Get a form of this Stream, using a cached version if available.
        '''
        # first, check for cached version
        if key in self.forms:
            return self.forms[key]

        splitKeys = key.split('.')

        prepared = self.prepared
        for i in range(len(splitKeys)):
            subKey = '.'.join(splitKeys[:i + 1])
            if subKey in self.forms:
                continue
            if i > 0:
                previousKey = '.'.join(splitKeys[:i])
                # should always be there.
                prepared = self.forms[previousKey]

            lastKey = splitKeys[i]

            if lastKey in self.keysToMethods:
                prepared = self.keysToMethods[lastKey](self, prepared)
            elif lastKey.startswith('getElementsByClass('):
                classToGet = lastKey[len('getElementsByClass('):-1]
                prepared = prepared.getElementsByClass(classToGet)
            else:
                raise AttributeError(f'no such attribute: {lastKey} in {key}')
            self.forms[subKey] = prepared

        return prepared

    def _getIntervalHistogram(self, algorithm='midi'):
        # note that this does not optimize and cache part presentations
        histo = [0] * 128
        # if we have parts, must add one at a time
        if self.prepared.hasPartLikeStreams():
            parts = self.prepared.parts
        else:
            parts = [self.prepared]  # emulate a list
        for p in parts:
            # will be flat

            # edit June 2012:
            # was causing millions of deepcopy calls
            # so I made it inPlace, but for some reason
            # code errored with 'p =' not present
            # also, this part has measures...so should retainContainers be True?
            # p = p.stripTies(retainContainers=False, inPlace=True)
            # noNone means that we will see all connections, even w/ a gap
            post = p.findConsecutiveNotes(skipRests=True,
                                          skipChords=True, skipGaps=True, noNone=True)
            for i, n in enumerate(post):
                if i < len(post) - 1:  # if not last
                    iNext = i + 1
                    nNext = post[iNext]
                    nValue = getattr(n.pitch, algorithm)
                    nextValue = getattr(nNext.pitch, algorithm)

                    try:
                        histo[abs(nValue - nextValue)] += 1
                    except AttributeError:
                        pass  # problem with not having midi
        return histo
# ----------------------------------------------------------------------------

    def formPartitionByInstrument(self, prepared):
        from music21 import instrument
        return instrument.partitionByInstrument(prepared)

    def formSetClassHistogram(self, prepared):
        return Counter([c.forteClassTnI for c in prepared])

    def formPitchClassSetHistogram(self, prepared):
        return Counter([c.orderedPitchClassesString for c in prepared])

    def formTypesHistogram(self, prepared):
        histo = {}

        # keys are methods on Chord
        keys = ['isTriad', 'isSeventh', 'isMajorTriad', 'isMinorTriad',
                'isIncompleteMajorTriad', 'isIncompleteMinorTriad', 'isDiminishedTriad',
                'isAugmentedTriad', 'isDominantSeventh', 'isDiminishedSeventh',
                'isHalfDiminishedSeventh']

        for c in prepared:
            for thisKey in keys:
                if thisKey not in histo:
                    histo[thisKey] = 0
                # get the function attr, call it, check bool
                if getattr(c, thisKey)():
                    histo[thisKey] += 1
        return histo

    def formGetElementsByClassMeasure(self, prepared):
        if 'Score' in prepared.classes:
            post = stream.Stream()
            for p in prepared.parts:
                # insert in overlapping offset positions
                for m in p.getElementsByClass('Measure'):
                    post.insert(m.getOffsetBySite(p), m)
        else:
            post = prepared.getElementsByClass('Measure')
        return post

    def formChordify(self, prepared):
        if 'Score' in prepared.classes:
            # options here permit getting part information out
            # of chordified representation
            return prepared.chordify(
                addPartIdAsGroup=True, removeRedundantPitches=False)
        else:  # for now, just return a normal Part or Stream
            # this seems wrong -- what if there are multiple voices
            # in the part?
            return prepared

    def formQuarterLengthHistogram(self, prepared):
        return Counter([float(n.quarterLength) for n in prepared])

    def formMidiPitchHistogram(self, pitches):
        return Counter([p.midi for p in pitches])

    def formPitchClassHistogram(self, pitches):
        cc = Counter([p.pitchClass for p in pitches])
        histo = [0] * 12
        for k in cc:
            histo[k] = cc[k]
        return histo

    def formMidiIntervalHistogram(self, unused):
        return self._getIntervalHistogram('midi')

    def formContourList(self, prepared):
        # list of all directed half steps
        cList = []
        # if we have parts, must add one at a time
        if prepared.hasPartLikeStreams():
            parts = prepared.parts
        else:
            parts = [prepared]  # emulate a list

        for p in parts:
            # this may be unnecessary but we cannot accessed cached part data

            # edit June 2012:
            # was causing lots of deepcopy calls, so I made
            # it inPlace=True, but errors when 'p =' no present
            # also, this part has measures...so should retainContainers be True?

            # REMOVE? Prepared is stripped!!!
            # p = p.stripTies(retainContainers=False, inPlace=True)  # will be flat
            # noNone means that we will see all connections, even w/ a gap
            post = p.findConsecutiveNotes(skipRests=True,
                                          skipChords=False,
                                          skipGaps=True,
                                          noNone=True)
            for i, n in enumerate(post):
                if i < (len(post) - 1):  # if not last
                    iNext = i + 1
                    nNext = post[iNext]

                    if n.isChord:
                        ps = n.sortDiatonicAscending().pitches[-1].midi
                    else:  # normal note
                        ps = n.pitch.midi
                    if nNext.isChord:
                        psNext = nNext.sortDiatonicAscending().pitches[-1].midi
                    else:  # normal note
                        psNext = nNext.pitch.midi

                    cList.append(psNext - ps)
        # environLocal.printDebug(['contourList', cList])
        return cList

    def formSecondsMap(self, prepared):
        post = []
        secondsMap = prepared.secondsMap
        # filter only notes; all elements would otherwise be gathered
        for bundle in secondsMap:
            if 'NotRest' in bundle['element'].classes:
                post.append(bundle)
        return post

    def formBeatHistogram(self, secondsMap):
        secondsList = [d['durationSeconds'] for d in secondsMap]
        bpmList = [round(60.0 / d) for d in secondsList]
        histogram = [0] * 200
        for thisBPM in bpmList:
            if thisBPM < 40 or thisBPM > 200:
                continue
            histogramIndex = int(thisBPM)
            histogram[histogramIndex] += 1
        return histogram

    keysToMethods = {
        'flat': lambda unused, p: p.flat,
        'pitches': lambda unused, p: p.pitches,
        'notes': lambda unused, p: p.notes,
        'getElementsByClass(Measure)': formGetElementsByClassMeasure,
        'metronomeMarkBoundaries': lambda unused, p: p.metronomeMarkBoundaries(),
        'chordify': formChordify,
        'partitionByInstrument': formPartitionByInstrument,
        'setClassHistogram': formSetClassHistogram,
        'pitchClassHistogram': formPitchClassHistogram,
        'typesHistogram': formTypesHistogram,
        'quarterLengthHistogram': formQuarterLengthHistogram,
        'pitchClassSetHistogram': formPitchClassSetHistogram,
        'midiPitchHistogram': formMidiPitchHistogram,
        'midiIntervalHistogram': formMidiIntervalHistogram,
        'contourList': formContourList,
        'analyzedKey': lambda unused, f: f.analyze(method='key'),
        'tonalCertainty': lambda unused, foundKey: foundKey.tonalCertainty(),
        'metadata': lambda unused, p: p.metadata,
        'secondsMap': formSecondsMap,
        'assembledLyrics': lambda unused, p: text.assembleLyrics(p),
        'beatHistogram': formBeatHistogram,
    }

# ------------------------------------------------------------------------------


class DataInstance:
    '''
    A data instance for analysis. This object prepares a Stream
    (by stripping ties, etc.) and stores
    multiple commonly-used stream representations once, providing rapid processing.
    '''
    # pylint: disable=redefined-builtin

    def __init__(self, streamOrPath=None, id=None):  # @ReservedAssignment
        if isinstance(streamOrPath, stream.Stream):
            self.stream = streamOrPath
            self.streamPath = None
        else:
            self.stream = None
            self.streamPath = streamOrPath

        # store an id for the source stream: file path url, corpus url
        # or metadata title
        if id is not None:
            self._id = id
        elif (self.stream is not None
              and hasattr(self.stream, 'metadata')
              and self.stream.metadata is not None
              and self.stream.metadata.title is not None
              ):
            self._id = self.stream.metadata.title
        elif self.stream is not None and hasattr(self.stream, 'sourcePath'):
            self._id = self.stream.sourcePath
        elif self.streamPath is not None:
            if hasattr(self.streamPath, 'sourcePath'):
                self._id = str(self.streamPath.sourcePath)
            else:
                self._id = str(self.streamPath)
        else:
            self._id = ''

        # the attribute name in the data set for this label
        self.classLabel = None
        # store the class value for this data instance
        self._classValue = None

        self.forms = None

        # store a list of voices, extracted from each part,
        self.formsByVoice = []
        # if parts exist, store a forms for each
        self.formsByPart = []

        self.featureExtractorClassesForParallelRunning = []

        if self.stream is not None:
            self.setupPostStreamParse()

    def setupPostStreamParse(self):
        '''
        Setup the StreamForms objects and other things that
        need to be done after a Stream is passed in but before
        feature extracting is run.

        Run automatically at instantiation if a Stream is passed in.
        '''
        # perform basic operations that are performed on all
        # streams

        # store a dictionary of StreamForms
        self.forms = StreamForms(self.stream)

        # if parts exist, store a forms for each
        self.formsByPart = []
        if hasattr(self.stream, 'parts'):
            self.partsCount = len(self.stream.parts)
            for p in self.stream.parts:
                # note that this will join ties and expand rests again
                self.formsByPart.append(StreamForms(p))
        else:
            self.partsCount = 0

        for v in self.stream.recurse().getElementsByClass('Voice'):
            self.formsByPart.append(StreamForms(v))

    def setClassLabel(self, classLabel, classValue=None):
        '''
        Set the class label, as well as the class value if known.
        The class label is the attribute name used to define the class of this data instance.

        >>> #_DOCS_SHOW s = corpus.parse('bwv66.6')
        >>> s = stream.Stream() #_DOCS_HIDE
        >>> di = features.DataInstance(s)
        >>> di.setClassLabel('Composer', 'Bach')
        '''
        self.classLabel = classLabel
        self._classValue = classValue

    def getClassValue(self):
        if self._classValue is None or callable(self._classValue) and self.stream is None:
            return ''

        if callable(self._classValue) and self.stream is not None:
            self._classValue = self._classValue(self.stream)

        return self._classValue

    def getId(self):
        if self._id is None or callable(self._id) and self.stream is None:
            return ''

        if callable(self._id) and self.stream is not None:
            self._id = self._id(self.stream)

        # make sure there are no spaces
        try:
            return self._id.replace(' ', '_')
        except AttributeError as e:
            raise AttributeError(str(self._id)) from e

    def parseStream(self):
        '''
        If a path to a Stream has been passed in at creation,
        then this will parse it (whether it's a corpus string,
        a converter string (url or filepath), a pathlib.Path,
        or a metadata.bundles.MetadataEntry.
        '''
        if self.stream is not None:
            return

        if isinstance(self.streamPath, str):
            # could be corpus or file path
            if os.path.exists(self.streamPath) or self.streamPath.startswith('http'):
                s = converter.parse(self.streamPath)
            else:  # assume corpus
                s = corpus.parse(self.streamPath)
        elif isinstance(self.streamPath, pathlib.Path):
            # could be corpus or file path
            if self.streamPath.exists():
                s = converter.parse(self.streamPath)
            else:  # assume corpus
                s = corpus.parse(self.streamPath)
        elif isinstance(self.streamPath, MetadataEntry):
            s = self.streamPath.parse()
        else:
            raise ValueError(f'Invalid streamPath type: {type(self.streamPath)}')

        self.stream = s
        self.setupPostStreamParse()

    def __getitem__(self, key):
        '''
        Get a form of this Stream, using a cached version if available.

        >>> di = features.DataInstance('bach/bwv66.6')
        >>> len(di['flat'])
        193
        >>> len(di['flat.pitches'])
        163
        >>> len(di['flat.notes'])
        163
        >>> len(di['getElementsByClass(Measure)'])
        40
        >>> len(di['flat.getElementsByClass(TimeSignature)'])
        4
        '''
        self.parseStream()
        if key in ['parts']:
            # return a list of Forms for each part
            return self.formsByPart
        elif key in ['voices']:
            # return a list of Forms for voices
            return self.formsByVoice
        # try to create by calling the attribute
        # will raise an attribute error if there is a problem
        return self.forms[key]


# ------------------------------------------------------------------------------
class DataSetException(exceptions21.Music21Exception):
    pass


class DataSet:
    '''
    A set of features, as well as a collection of data to operate on.

    Comprises multiple DataInstance objects, a FeatureSet, and an OutputFormat.


    >>> ds = features.DataSet(classLabel='Composer')
    >>> f = [features.jSymbolic.PitchClassDistributionFeature,
    ...      features.jSymbolic.ChangesOfMeterFeature,
    ...      features.jSymbolic.InitialTimeSignatureFeature]
    >>> ds.addFeatureExtractors(f)
    >>> ds.addData('bwv66.6', classValue='Bach')
    >>> ds.addData('bach/bwv324.xml', classValue='Bach')
    >>> ds.process()
    >>> ds.getFeaturesAsList()[0]
    ['bwv66.6', 0.196..., 0.0736..., 0.006..., 0.098..., 0.0368..., 0.177..., 0.0,
     0.085..., 0.134..., 0.018..., 0.171..., 0.0, 0, 4, 4, 'Bach']
    >>> ds.getFeaturesAsList()[1]
    ['bach/bwv324.xml', 0.25, 0.0288..., 0.125, 0.0, 0.144..., 0.125, 0.0, 0.163..., 0.0, 0.134...,
    0.0288..., 0.0, 0, 4, 4, 'Bach']

    >>> ds = ds.getString()


    By default, all exceptions are caught and printed if debug mode is on.

    Set ds.failFast = True to not catch them.

    Set ds.quiet = False to print them regardless of debug mode.
    '''

    def __init__(self, classLabel=None, featureExtractors=()):
        # assume a two dimensional array
        self.dataInstances = []

        # order of feature extractors is the order used in the presentations
        self._featureExtractors = []
        self._instantiatedFeatureExtractors = []
        # the label of the class
        self._classLabel = classLabel
        # store a multidimensional storage of all features
        self.features = []

        self.failFast = False
        self.quiet = True

        self.runParallel = True
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
            self._featureExtractors.append(sub)
            self._instantiatedFeatureExtractors.append(sub())

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
        for fe in self._instantiatedFeatureExtractors:
            post += fe.getAttributeLabels()
        if self._classLabel is not None and includeClassLabel:
            post.append(self._classLabel.replace(' ', '_'))
        return post

    def getDiscreteLabels(self, includeClassLabel=True, includeId=True):
        '''
        Return column labels for discrete status.

        >>> f = [features.jSymbolic.PitchClassDistributionFeature,
        ...      features.jSymbolic.ChangesOfMeterFeature]
        >>> ds = features.DataSet(classLabel='Composer', featureExtractors=f)
        >>> ds.getDiscreteLabels()
        [None, False, False, False, False, False, False, False, False, False,
         False, False, False, True, True]
        '''
        post = []
        if includeId:
            post.append(None)  # just a spacer
        for fe in self._instantiatedFeatureExtractors:
            # need as many statements of discrete as there are dimensions
            post += [fe.discrete] * fe.dimensions
        # class label is assumed always discrete
        if self._classLabel is not None and includeClassLabel:
            post.append(True)
        return post

    def getClassPositionLabels(self, includeId=True):
        '''
        Return column labels for the presence of a class definition

        >>> f = [features.jSymbolic.PitchClassDistributionFeature,
        ...      features.jSymbolic.ChangesOfMeterFeature]
        >>> ds = features.DataSet(classLabel='Composer', featureExtractors=f)
        >>> ds.getClassPositionLabels()
        [None, False, False, False, False, False, False, False, False,
         False, False, False, False, False, True]
        '''
        post = []
        if includeId:
            post.append(None)  # just a spacer
        for fe in self._instantiatedFeatureExtractors:
            # need as many statements of discrete as there are dimensions
            post += [False] * fe.dimensions
        # class label is assumed always discrete
        if self._classLabel is not None:
            post.append(True)
        return post

    def addMultipleData(self, dataList, classValues, ids=None):
        '''
        add multiple data points at the same time.

        Requires an iterable (including MetadataBundle) for dataList holding
        types that can be passed to addData, and an equally sized list of dataValues
        and an equally sized list of ids (or None)

        classValues can also be a pickleable function that will be called on
        each instance after parsing, as can ids.
        '''
        if (not callable(classValues)
                and len(dataList) != len(classValues)):
            raise DataSetException(
                'If classValues is not a function, it must have the same length as dataList')
        if (ids is not None
                and not callable(ids)
                and len(dataList) != len(ids)):
            raise DataSetException(
                'If ids is not a function or None, it must have the same length as dataList')

        if callable(classValues):
            try:
                pickle.dumps(classValues)
            except pickle.PicklingError:
                raise DataSetException('classValues if a function must be pickleable. '
                                       + 'Lambda and some other functions are not.')

            classValues = [classValues] * len(dataList)

        if callable(ids):
            try:
                pickle.dumps(ids)
            except pickle.PicklingError:
                raise DataSetException('ids if a function must be pickleable. '
                                       + 'Lambda and some other functions are not.')

            ids = [ids] * len(dataList)
        elif ids is None:
            ids = [None] * len(dataList)

        for i in range(len(dataList)):
            d = dataList[i]
            cv = classValues[i]
            thisId = ids[i]
            self.addData(d, cv, thisId)

    # pylint: disable=redefined-builtin

    def addData(self, dataOrStreamOrPath, classValue=None, id=None):  # @ReservedAssignment
        '''
        Add a Stream, DataInstance, MetadataEntry, or path (Posix or str)
        to a corpus or local file to this data set.

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
            if s is None:
                s = di.streamPath
        else:
            # all else are stored directly
            s = dataOrStreamOrPath
            di = DataInstance(dataOrStreamOrPath, id=id)

        di.setClassLabel(self._classLabel, classValue)
        self.dataInstances.append(di)

    def process(self):
        '''
        Process all Data with all FeatureExtractors.
        Processed data is stored internally as numerous Feature objects.
        '''
        if self.runParallel:
            return self._processParallel()
        else:
            return self._processNonParallel()

    def _processParallel(self):
        '''
        Run a set of processes in parallel.
        '''
        for di in self.dataInstances:
            di.featureExtractorClassesForParallelRunning = self._featureExtractors

        shouldUpdate = not self.quiet

        # print('about to run parallel')
        outputData = common.runParallel([(di, self.failFast) for di in self.dataInstances],
                                           _dataSetParallelSubprocess,
                                           updateFunction=shouldUpdate,
                                           updateMultiply=1,
                                           unpackIterable=True
                                        )
        featureData, errors, classValues, ids = zip(*outputData)
        errors = common.flattenList(errors)
        for e in errors:
            if self.quiet is True:
                environLocal.printDebug(e)
            else:
                environLocal.warn(e)
        self.features = featureData

        for i, di in enumerate(self.dataInstances):
            if callable(di._classValue):
                di._classValue = classValues[i]
            if callable(di._id):
                di._id = ids[i]

    def _processNonParallel(self):
        '''
        The traditional method: run non-parallel
        '''
        # clear features
        self.features = []
        for data in self.dataInstances:
            row = []
            for fe in self._instantiatedFeatureExtractors:
                fe.setData(data)
                # in some cases there might be problem; to not fail
                try:
                    fReturned = fe.extract()
                except Exception as e:  # pylint: disable=broad-except
                    # for now take any error
                    fList = ['failed feature extractor:', fe, str(e)]
                    if self.quiet is True:
                        environLocal.printDebug(fList)
                    else:
                        environLocal.warn(fList)
                    if self.failFast is True:
                        raise e
                    # provide a blank feature extractor
                    fReturned = fe.getBlankFeature()

                row.append(fReturned)  # get feature and store
            # rows will align with data the order of DataInstances
            self.features.append(row)

    def getFeaturesAsList(self, includeClassLabel=True, includeId=True, concatenateLists=True):
        '''
        Get processed data as a list of lists, merging any sub-lists
        in multi-dimensional features.
        '''
        post = []
        for i, row in enumerate(self.features):
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
        from music21.features import outputFormats
        if featureFormat.lower() in ['tab', 'orange', 'taborange', None]:
            outputFormat = outputFormats.OutputTabOrange(dataSet=self)
        elif featureFormat.lower() in ['csv', 'comma']:
            outputFormat = outputFormats.OutputCSV(dataSet=self)
        elif featureFormat.lower() in ['arff', 'attribute']:
            outputFormat = outputFormats.OutputARFF(dataSet=self)
        else:
            return None
        return outputFormat

    def _getOutputFormatFromFilePath(self, fp):
        '''
        Get an output format from a file path if possible, otherwise return None.

        >>> ds = features.DataSet()
        >>> ds._getOutputFormatFromFilePath('test.tab')
        <music21.features.outputFormats.OutputTabOrange object at ...>
        >>> ds._getOutputFormatFromFilePath('test.csv')
        <music21.features.outputFormats.OutputCSV object at ...>
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
        '''
        Get a string representation of the data set in a specific format.
        '''
        # pass reference to self to output
        outputFormat = self._getOutputFormat(outputFmt)
        return outputFormat.getString()

    # pylint: disable=redefined-builtin
    def write(self, fp=None, format=None, includeClassLabel=True):  # @ReservedAssignment
        '''
        Set the output format object.
        '''
        if format is None and fp is not None:
            outputFormat = self._getOutputFormatFromFilePath(fp)
        else:
            outputFormat = self._getOutputFormat(format)
        if outputFormat is None:
            raise DataSetException('no output format could be defined from file path '
                                   + f'{fp} or format {format}')

        outputFormat.write(fp=fp, includeClassLabel=includeClassLabel)


def _dataSetParallelSubprocess(dataInstance, failFast):
    row = []
    errors = []
    # howBigWeCopied = len(pickle.dumps(dataInstance))
    # print('Starting ', dataInstance, ' Size: ', howBigWeCopied)
    for feClass in dataInstance.featureExtractorClassesForParallelRunning:
        fe = feClass()
        fe.setData(dataInstance)
        # in some cases there might be problem; to not fail
        try:
            fReturned = fe.extract()
        except Exception as e:  # pylint: disable=broad-except
            # for now take any error
            errors.append('failed feature extractor:' + str(fe) + ': ' + str(e))
            if failFast:
                raise e
            # provide a blank feature extractor
            fReturned = fe.getBlankFeature()

        row.append(fReturned)  # get feature and store
    # rows will align with data the order of DataInstances
    return row, errors, dataInstance.getClassValue(), dataInstance.getId()


def allFeaturesAsList(streamInput):
    '''
    returns a list containing ALL currently implemented feature extractors

    streamInput can be a Stream, DataInstance, or path to a corpus or local
    file to this data set.

    >>> s = converter.parse('tinynotation: 4/4 c4 d e2')
    >>> f = features.allFeaturesAsList(s)
    >>> f[2:5]
    [[2], [2], [1.0]]
    >>> len(f) > 85
    True
    '''
    from music21.features import jSymbolic, native
    ds = DataSet(classLabel='')
    f = list(jSymbolic.featureExtractors) + list(native.featureExtractors)
    ds.addFeatureExtractors(f)
    ds.addData(streamInput)
    ds.process()
    allData = ds.getFeaturesAsList(includeClassLabel=False,
                                   includeId=False,
                                   concatenateLists=False)

    return allData


# ------------------------------------------------------------------------------
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
    for lib in library:
        if lib.lower() in ['jsymbolic', 'all']:
            featureExtractors += jSymbolic.featureExtractors
        elif lib.lower() in ['native', 'all']:
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
    if not flatIds:
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
    >>> fe = features.extractorById('p20')(s)  # call class
    >>> fe.extract().vector
    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    '''
    ebi = extractorsById(idOrList=idOrList, library=library)
    if ebi:
        return ebi[0]
    return None  # no match


def vectorById(streamObj, vectorId, library=('jSymbolic', 'native')):
    '''
    Utility function to get a vector from an extractor

    >>> s = stream.Stream()
    >>> s.append(note.Note('A4'))
    >>> features.vectorById(s, 'p20')
    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    '''
    fe = extractorById(vectorId, library)(streamObj)  # call class with stream
    if fe is None:
        return None  # could raise exception
    return fe.extract().vector


def getIndex(featureString, extractorType=None):
    '''
    Returns the list index of the given feature extractor and the feature extractor
    category (jsymbolic or native). If feature extractor string is not in either
    jsymbolic or native feature extractors, returns None

    optionally include the extractorType ('jsymbolic' or 'native') if known
    and searching will be made more efficient


    >>> features.getIndex('Range')
    (61, 'jsymbolic')
    >>> features.getIndex('Ends With Landini Melodic Contour')
    (19, 'native')
    >>> features.getIndex('aBrandNewFeature!') is None
    True
    >>> features.getIndex('Fifths Pitch Histogram', 'jsymbolic')
    (70, 'jsymbolic')
    >>> features.getIndex('Tonal Certainty', 'native')
    (1, 'native')
    '''
    from music21.features import jSymbolic, native

    if extractorType is None or extractorType == 'jsymbolic':
        indexCnt = 0
        for feature in jSymbolic.featureExtractors:

            if feature().name == featureString:
                return (indexCnt, 'jsymbolic')
            indexCnt += 1
    if extractorType is None or extractorType == 'native':
        indexCnt = 0
        for feature in native.featureExtractors:
            if feature().name == featureString:
                return (indexCnt, 'native')
            indexCnt += 1

        return None


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testStreamFormsA(self):

        from music21 import features
        self.maxDiff = None

        s = corpus.parse('corelli/opus3no1/1grave')
        # s.chordify().show()
        di = features.DataInstance(s)
        self.assertEqual(len(di['flat']), 291)
        self.assertEqual(len(di['flat.notes']), 238)

        # di['chordify'].show('t')
        self.assertEqual(len(di['chordify']), 27)
        chordifiedChords = di['chordify.flat.getElementsByClass(Chord)']
        self.assertEqual(len(chordifiedChords), 145)
        histo = di['chordify.flat.getElementsByClass(Chord).setClassHistogram']
        # print(histo)

        self.assertEqual(histo,
                         {'3-11': 30, '2-4': 26, '1-1': 25, '2-3': 16, '3-9': 12, '2-2': 6,
                          '3-7': 6, '2-5': 6, '3-4': 5, '3-6': 5, '3-10': 4,
                          '3-8': 2, '3-2': 2})

        self.assertEqual(di['chordify.flat.getElementsByClass(Chord).typesHistogram'],
                           {'isMinorTriad': 6, 'isAugmentedTriad': 0,
                            'isTriad': 34, 'isSeventh': 0, 'isDiminishedTriad': 4,
                            'isDiminishedSeventh': 0, 'isIncompleteMajorTriad': 26,
                            'isHalfDiminishedSeventh': 0, 'isMajorTriad': 24,
                            'isDominantSeventh': 0, 'isIncompleteMinorTriad': 16})

        self.assertEqual(di['flat.notes.quarterLengthHistogram'],
                         {0.5: 116, 1.0: 39, 1.5: 27, 2.0: 31, 3.0: 2, 4.0: 3,
                          0.75: 4, 0.25: 16})

        # can access parts by index
        self.assertEqual(len(di['parts']), 3)
        # stored in parts are StreamForms instances, caching their results
        self.assertEqual(len(di['parts'][0]['flat.notes']), 71)
        self.assertEqual(len(di['parts'][1]['flat.notes']), 66)

        # getting a measure by part
        self.assertEqual(len(di['parts'][0]['getElementsByClass(Measure)']), 19)
        self.assertEqual(len(di['parts'][1]['getElementsByClass(Measure)']), 19)

        self.assertEqual(di['parts'][0]['pitches.pitchClassHistogram'],
                         [9, 1, 11, 0, 9, 13, 0, 11, 0, 12, 5, 0])
        # the sum of the two arrays is the pitch class histogram of the complete
        # work
        self.assertEqual(di['pitches.pitchClassHistogram'],
                         [47, 2, 25, 0, 25, 42, 0, 33, 0, 38, 22, 4])

    def testStreamFormsB(self):

        from music21 import features, note

        s = stream.Stream()
        for p in ['c4', 'c4', 'd-4', 'd#4', 'f#4', 'a#4', 'd#5', 'a5', 'a5']:
            s.append(note.Note(p))
        di = features.DataInstance(s)
        self.assertEqual(di['pitches.midiIntervalHistogram'],
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

        self.assertEqual(pformat(di['flat.secondsMap']), '''[{'durationSeconds': 0.5,
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
  'voiceIndex': None}]''', pformat(di['secondsMap']))

    def testDataSetOutput(self):
        from music21 import features
        from music21.features import outputFormats
        # test just a few features
        featureExtractors = features.extractorsById(['ql1', 'ql2', 'ql4'], 'native')

        # need to define what the class label will be
        ds = features.DataSet(classLabel='Composer')
        ds.runParallel = False
        ds.addFeatureExtractors(featureExtractors)

        # add works, defining the class value
        ds.addData('bwv66.6', classValue='Bach')
        ds.addData('corelli/opus3no1/1grave', classValue='Corelli')

        ds.process()

        # manually create an output format and get output
        of = outputFormats.OutputCSV(ds)
        post = of.getString(lineBreak='//')
        self.assertEqual(
            post,
            'Identifier,Unique_Note_Quarter_Lengths,'
            'Most_Common_Note_Quarter_Length,Range_of_Note_Quarter_Lengths,'
            'Composer//bwv66.6,3,1.0,1.5,Bach//corelli/opus3no1/1grave,8,0.5,3.75,Corelli')

        # without id
        post = of.getString(lineBreak='//', includeId=False)
        self.assertEqual(
            post,
            'Unique_Note_Quarter_Lengths,Most_Common_Note_Quarter_Length,'
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
        # s.append(None)  # will create a wrapper -- NOT ANYMORE
        s.append(base.ElementWrapper(None))
        ds.addData(s, classValue='Monteverdi')
        ds.addData(s, classValue='Handel')

        # process with all feature extractors, store all features
        ds.failFast = True
        # Tests that some exception is raised, not necessarily that only one is
        with self.assertRaises(features.FeatureException):
            ds.process()

    def testEmptyStreamCustomErrors(self):
        from music21 import analysis, features
        from music21.features import jSymbolic, native

        ds = DataSet(classLabel='')
        f = list(jSymbolic.featureExtractors) + list(native.featureExtractors)

        bareStream = stream.Stream()
        bareScore = stream.Score()

        singlePart = stream.Part()
        singleMeasure = stream.Measure()
        singlePart.append(singleMeasure)
        bareScore.insert(singlePart)

        ds.addData(bareStream)
        ds.addData(bareScore)
        ds.addFeatureExtractors(f)

        for data in ds.dataInstances:
            for fe in ds._instantiatedFeatureExtractors:
                fe.setData(data)
                try:
                    fe.extract()
                # is every error wrapped?
                except (features.FeatureException,
                        analysis.discrete.DiscreteAnalysisException):
                    pass

    # --------------------------------------------------------------------------
    # silent tests

#    def testGetAllExtractorsMethods(self):
#        '''
#        ahh..this test takes a really long time....
#        '''
#        from music21 import stream, features, pitch
#        s = corpus.parse('bwv66.6').measures(1, 5)
#        self.assertEqual( len(features.alljSymbolicFeatures(s)), 70)
#        self.assertEqual(len (features.allNativeFeatures(s)),21)
#        self.assertEqual(str(features.alljSymbolicVectors(s)[1:5]),
# '[[2.6630434782608696], [2], [2], [0.391304347826087]]')
#        self.assertEqual(str(features.allNativeVectors(s)[0:4]),
# '[[1], [1.0328322202181006], [2], [1.0]]')

    def x_testComposerClassificationJSymbolic(self):  # pragma: no cover
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

        # worksBach = corpus.getBachChorales()[100:143]  # a middle range
        worksMonteverdi = corpus.search('monteverdi').search('.xml')[:43]

        worksBach = corpus.search('bach').search(numberOfParts=4)[:5]

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

    def x_testRegionClassificationJSymbolicA(self):  # pragma: no cover
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
                songId = f'essenFolksong/{name}-{w.metadata.number}'
                ds.addData(w, classValue='China', id=songId)

        for o, name in [(oMitteleuropa1, 'boehme10'),
                        (oMitteleuropa2, 'boehme20')]:
            for w in o.scores:
                songId = f'essenFolksong/{name}-{w.metadata.number}'
                ds.addData(w, classValue='Mitteleuropa', id=songId)

        # process with all feature extractors, store all features
        ds.process()
        ds.getString(outputFmt='tab')
        ds.getString(outputFmt='csv')
        ds.getString(outputFmt='arff')

    def x_testRegionClassificationJSymbolicB(self):  # pragma: no cover
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
                songId = f'essenFolksong/{name}-{w.metadata.number}'
                ds.addData(w, classValue='China', id=songId)

        for o, name in [(oMitteleuropa1, 'boehme10')]:
            for w in o.scores:
                songId = f'essenFolksong/{name}-{w.metadata.number}'
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
                songId = f'essenFolksong/{name}-{w.metadata.number}'
                ds.addData(w, classValue='China', id=songId)

        for o, name in [(oMitteleuropa2, 'boehme20')]:
            for w in o.scores:
                songId = f'essenFolksong/{name}-{w.metadata.number}'
                ds.addData(w, classValue='Mitteleuropa', id=songId)

        # process with all feature extractors, store all features
        ds.process()
        ds.write('/_scratch/chinaMitteleuropaSplit-b.tab')
        ds.write('/_scratch/chinaMitteleuropaSplit-b.csv')
        ds.write('/_scratch/chinaMitteleuropaSplit-b.arff')

# all these are written using orange-Py2 code; need better.
#     def xtestOrangeBayesA(self):  # pragma: no cover
#         '''Using an already created test file with a BayesLearner.
#         '''
#         import orange # @UnresolvedImport  # pylint: disable=import-error
#         data = orange.ExampleTable(
#             '~/music21Ext/mlDataSets/bachMonteverdi-a/bachMonteverdi-a.tab')
#         classifier = orange.BayesLearner(data)
#         for i in range(len(data)):
#             c = classifier(data[i])
#             print('original', data[i].getclass(), 'BayesLearner:', c)
#
#
#     def xtestClassifiersA(self):  # pragma: no cover
#         '''Using an already created test file with a BayesLearner.
#         '''
#         import orange, orngTree # @UnresolvedImport  # pylint: disable=import-error
#         data1 = orange.ExampleTable(
#                 '~/music21Ext/mlDataSets/chinaMitteleuropa-b/chinaMitteleuropa-b1.tab')
#
#         data2 = orange.ExampleTable(
#                 '~/music21Ext/mlDataSets/chinaMitteleuropa-b/chinaMitteleuropa-b2.tab')
#
#         majority = orange.MajorityLearner
#         bayes = orange.BayesLearner
#         tree = orngTree.TreeLearner
#         knn = orange.kNNLearner
#
#         for classifierType in [majority, bayes, tree, knn]:
#             print('')
#             for classifierData, classifierStr, matchData, matchStr in [
#                 (data1, 'data1', data1, 'data1'),
#                 (data1, 'data1', data2, 'data2'),
#                 (data2, 'data2', data2, 'data2'),
#                 (data2, 'data2', data1, 'data1'),
#                 ]:
#
#                 # train with data1
#                 classifier = classifierType(classifierData)
#                 mismatch = 0
#                 for i in range(len(matchData)):
#                     c = classifier(matchData[i])
#                     if c != matchData[i].getclass():
#                         mismatch += 1
#
#                 print('%s %s: misclassified %s/%s of %s' % (
#                         classifierStr, classifierType, mismatch, len(matchData), matchStr))
#
# #             if classifierType == orngTree.TreeLearner:
# #                 orngTree.printTxt(classifier)
#
#
#
#     def xtestClassifiersB(self):  # pragma: no cover
#         '''Using an already created test file with a BayesLearner.
#         '''
#         import orange, orngTree # @UnresolvedImport  # pylint: disable=import-error
#         data1 = orange.ExampleTable(
#                 '~/music21Ext/mlDataSets/chinaMitteleuropa-b/chinaMitteleuropa-b1.tab')
#
#         data2 = orange.ExampleTable(
#                 '~/music21Ext/mlDataSets/chinaMitteleuropa-b/chinaMitteleuropa-b2.tab',
#                 use=data1.domain)
#
#         data1.extend(data2)
#         data = data1
#
#         majority = orange.MajorityLearner
#         bayes = orange.BayesLearner
#         tree = orngTree.TreeLearner
#         knn = orange.kNNLearner
#
#         folds = 10
#         for classifierType in [majority, bayes, tree, knn]:
#             print('')
#
#             cvIndices = orange.MakeRandomIndicesCV(data, folds)
#             for fold in range(folds):
#                 train = data.select(cvIndices, fold, negate=1)
#                 test = data.select(cvIndices, fold)
#
#                 for classifierData, classifierStr, matchData, matchStr in [
#                     (train, 'train', test, 'test'),
#                     ]:
#
#                     # train with data1
#                     classifier = classifierType(classifierData)
#                     mismatch = 0
#                     for i in range(len(matchData)):
#                         c = classifier(matchData[i])
#                         if c != matchData[i].getclass():
#                             mismatch += 1
#
#                     print('%s %s: misclassified %s/%s of %s' % (
#                             classifierStr, classifierType, mismatch, len(matchData), matchStr))
#
#
#     def xtestOrangeClassifiers(self):  # pragma: no cover
#         '''
#         This test shows how to compare four classifiers; replace the file path
#         with a path to the .tab data file.
#         '''
#         import orange, orngTree # @UnresolvedImport  # pylint: disable=import-error
#         data = orange.ExampleTable(
#             '~/music21Ext/mlDataSets/bachMonteverdi-a/bachMonteverdi-a.tab')
#
#         # setting up the classifiers
#         majority = orange.MajorityLearner(data)
#         bayes = orange.BayesLearner(data)
#         tree = orngTree.TreeLearner(data, sameMajorityPruning=1, mForPruning=2)
#         knn = orange.kNNLearner(data, k=21)
#
#         majority.name='Majority'
#         bayes.name='Naive Bayes'
#         tree.name='Tree'
#         knn.name='kNN'
#         classifiers = [majority, bayes, tree, knn]
#
#         # print the head
#         print('Possible classes:', data.domain.classVar.values)
#         print('Original Class', end=' ')
#         for l in classifiers:
#             print('%-13s' % (l.name), end=' ')
#         print()
#
#         for example in data:
#             print('(%-10s)  ' % (example.getclass()), end=' ')
#             for c in classifiers:
#                 p = c([example, orange.GetProbabilities])
#                 print('%5.3f        ' % (p[0]), end=' ')
#             print('')
#
#
#     def xtestOrangeClassifierTreeLearner(self):  # pragma: no cover
#         import orange, orngTree # @UnresolvedImport  # pylint: disable=import-error
#         data = orange.ExampleTable(
#             '~/music21Ext/mlDataSets/bachMonteverdi-a/bachMonteverdi-a.tab')
#
#         tree = orngTree.TreeLearner(data, sameMajorityPruning=1, mForPruning=2)
#         # tree = orngTree.TreeLearner(data)
#         for i in range(len(data)):
#             p = tree(data[i], orange.GetProbabilities)
#             print('%s: %5.3f (originally %s)' % (i + 1, p[1], data[i].getclass()))
#
#         orngTree.printTxt(tree)

    def testParallelRun(self):
        from music21 import features
        # test just a few features
        featureExtractors = features.extractorsById(['ql1', 'ql2', 'ql4'], 'native')

        # need to define what the class label will be
        ds = features.DataSet(classLabel='Composer')
        ds.addFeatureExtractors(featureExtractors)

        # add works, defining the class value
        ds.addData('bwv66.6', classValue='Bach')
        ds.addData('corelli/opus3no1/1grave', classValue='Corelli')
        ds.runParallel = True
        ds.quiet = True
        ds.process()
        self.assertEqual(len(ds.features), 2)
        self.assertEqual(len(ds.features[0]), 3)
        fe00 = ds.features[0][0]
        self.assertEqual(fe00.vector, [3])

    # pylint: disable=redefined-outer-name
    def x_fix_parallel_first_testMultipleSearches(self):
        from music21.features import outputFormats
        from music21 import features

        # Need explicit import for pickling within the testSingleCoreAll context
        from music21.features.base import _pickleFunctionNumPitches  # @UnresolvedImport
        import textwrap

        self.maxDiff = None

        fewBach = corpus.search('bach/bwv6')

        self.assertEqual(len(fewBach), 13)
        ds = features.DataSet(classLabel='NumPitches')
        ds.addMultipleData(fewBach, classValues=_pickleFunctionNumPitches)
        featureExtractors = features.extractorsById(['ql1', 'ql4'], 'native')
        ds.addFeatureExtractors(featureExtractors)
        ds.runParallel = True
        ds.process()
        # manually create an output format and get output
        of = outputFormats.OutputCSV(ds)
        post = of.getString(lineBreak='\n')
        self.assertEqual(post.strip(), textwrap.dedent('''
            Identifier,Unique_Note_Quarter_Lengths,Range_of_Note_Quarter_Lengths,NumPitches
            bach/bwv6.6.mxl,4,1.75,164
            bach/bwv60.5.mxl,6,2.75,282
            bach/bwv62.6.mxl,5,1.75,182
            bach/bwv64.2.mxl,4,1.5,179
            bach/bwv64.4.mxl,5,2.5,249
            bach/bwv64.8.mxl,5,3.5,188
            bach/bwv65.2.mxl,4,3.0,148
            bach/bwv65.7.mxl,7,2.75,253
            bach/bwv66.6.mxl,3,1.5,165
            bach/bwv67.4.xml,3,1.5,173
            bach/bwv67.7.mxl,4,2.5,132
            bach/bwv69.6-a.mxl,4,1.5,170
            bach/bwv69.6.xml,8,4.25,623
            ''').strip())


def _pickleFunctionNumPitches(bachStream):
    '''
    A function for documentation testing of a pickleable function
    '''
    return len(bachStream.pitches)


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [DataSet, Feature, FeatureExtractor]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testStreamFormsA')

