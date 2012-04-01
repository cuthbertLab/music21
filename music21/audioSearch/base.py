# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.base.py
# Purpose:      base subroutines for all audioSearching and score following routines
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import copy
import math
import os
import wave
import unittest, doctest

import music21.scale
import music21.pitch
from music21 import common
from music21 import search
from music21 import features
from music21 import environment, converter
from music21 import metadata, note, stream
from music21.audioSearch import recording
_MOD = 'audioSearch/base.py'
environLocal = environment.Environment(_MOD)

audioChunkLength = 1024
recordSampleRate = 44100

_missingImport = []
try:
    import matplotlib.mlab # for find
    import matplotlib.pyplot
except ImportError:
    _missingImport.append('matplotlib')

try:    
    import numpy
except ImportError:
    _missingImport.append('numpy')

try:
    import scipy.signal 
except ImportError:
    _missingImport.append('scipy')

if len(_missingImport) > 0:
    if environLocal['warnings'] in [1, '1', True]:
        pass
        #environLocal.warn(common.getMissingImportStr(_missingImport), header='music21:')


def histogram(data,bins):
    '''
    Histogram
    
    
    >>> from music21 import *
    >>> data = [1, 1, 4, 5, 6, 0, 8, 8, 8, 8, 8]
    >>> pdf, bins = audioSearch.histogram(data,8)
    >>> print pdf
    [3, 0, 0, 1, 1, 1, 0, 5]
    >>> print bins
    [0, 1, 2, 3, 4, 5, 6, 7, 8]
    
    '''
    maxValue = max(data)
    minValue = min(data)
    lengthEachBin = (maxValue-minValue)/bins
    
    container = []
    for i in range(int(bins)):
        container.append(0)
    for i in data:
        count = 1
        while i > minValue + count*lengthEachBin:
            count += 1
        container[count - 1] += 1
        
    binsLimits = []
    binsLimits.append(minValue)
    count = 1
    for i in range(int(bins)):
        binsLimits.append(minValue+count*lengthEachBin)
        count +=1
    return container,binsLimits


def autocorrelationFunction(recordedSignal, recordSampleRate):
    '''  
    It converts the temporal domain into a frequency domain. In order to do that, it
    uses the autocorrelation function, which finds periodicities in the signal
    in the temporal domain and, consequently, obtains the frequency in each instant 
    of time.
    
    
    >>> from music21 import *
    >>> import wave
    >>> import os #_DOCS_HIDE
    >>> readPath = os.path.dirname(__file__) + os.path.sep #_DOCS_HIDE
    >>> wv = wave.open(readPath + 'test_audio.wav', 'r') #_DOCS_HIDE
    >>> #_DOCS_SHOW wv = wave.open("test_audio.wav",'r')
    >>> data = wv.readframes(1024)
    >>> samps = numpy.fromstring(data, dtype=numpy.int16)
    >>> finalResult = autocorrelationFunction(samps, 44100)
    >>> wv.close()
    >>> print finalResult
    143.6276...

    '''

    recordedSignal = numpy.array(recordedSignal)
    correlation = scipy.signal.fftconvolve(recordedSignal, recordedSignal[::-1], mode='full')
    lengthCorrelation = len(correlation) / 2
    correlation = correlation[lengthCorrelation:]
    difference = numpy.diff(correlation) #  Calculates the difference between slots
    positiveDifferences = matplotlib.mlab.find(difference > 0)
    if len(positiveDifferences) == 0:
        finalResult = 10 # Rest
    else:
        beginning = positiveDifferences[0]
        peak = numpy.argmax(correlation[beginning:]) + beginning
        vertex = interpolation(correlation, peak)
        finalResult = recordSampleRate / vertex
    return finalResult

def prepareThresholds(useScale=None):
    '''
    returns two elements.  The first is a list of threshold values
    for one octave of a given scale, `useScale`, 
    (including the octave repetition) (Default is a ChromaticScale).
    The second is the pitches of the scale.
    
    
    A threshold value is the fractional part of the log-base-2 value of the
    frequency.
    
    
    For instance if A = 440 and B-flat = 460, then the threshold between
    A and B-flat will be 450.  Notes below 450 should be considered As and those
    above 450 should be considered B-flats.
    
    
    Thus the list returned has one less element than the number of notes in the
    scale + octave repetition.  If useScale is a ChromaticScale, `prepareThresholds`
    will return a 12 element list.  If it's a diatonic scale, it'll have 7 elements.
    
    
    >>> from music21 import *
    >>> l, p = music21.audioSearch.prepareThresholds(scale.MajorScale('A3'))
    >>> for i in range(len(l)):
    ...    print "%s < %.2f < %s" % (p[i], l[i], p[i+1])
    A3 < 0.86 < B3
    B3 < 0.53 < C#4
    C#4 < 0.16 < D4
    D4 < 0.28 < E4
    E4 < 0.45 < F#4
    F#4 < 0.61 < G#4
    G#4 < 1.24 < A4
    '''
    if useScale is None:
        useScale = music21.scale.ChromaticScale('C4')
    
    scPitches = useScale.pitches
    scPitchesRemainder = []
   
    for p in scPitches:
        pLog2 = math.log(p.frequency, 2)
        scPitchesRemainder.append(math.modf(pLog2)[0])
   
    scPitchesRemainder[-1] += 1
   
    scPitchesThreshold = []
    for i in range(len(scPitchesRemainder) - 1):
        scPitchesThreshold.append((scPitchesRemainder[i] + scPitchesRemainder[i + 1]) / 2)
 
    return scPitchesThreshold, scPitches


def interpolation(correlation, peak):
    '''
    Interpolation for estimating the true position of an
    inter-sample maximum when nearby samples are known.
   
    Correlation is a vector and peak is an index for that vector.
   
    Returns the x coordinate of the vertex of that parabola.

    >>> from music21 import *
    >>> import numpy
    >>> f = [2, 3, 1, 6, 4, 2, 3, 1]
    >>> audioSearch.interpolation(f, numpy.argmax(f))
    3.21428571...   
    '''
    vertex = (correlation[peak - 1] - correlation[peak + 1]) / (correlation[peak - 1] - 2.0 * correlation[peak] + correlation[peak + 1])
    vertex = vertex * 0.5 + peak
    return vertex



def normalizeInputFrequency(inputPitchFrequency, thresholds=None, pitches=None):
    '''
    Takes in an inputFrequency, a set of threshold values, and a set of allowable pitches
    (given by prepareThresholds) and returns a tuple of the normalized frequency and the 
    pitch detected (as a :class:`~music21.pitch.Pitch` object)
    
    
    It will convert the frequency to be within the range of the default frequencies
    (usually C4 to C5) but the pitch object will have the correct octave.
    
    
    >>> from music21 import *
    >>> audioSearch.normalizeInputFrequency(441.72)
    (440.0, A4)
    
    
    If you will be doing this often, it's best to cache your thresholds and
    pitches by running `prepareThresholds` once first:
    
    
    >>> thresholds, pitches = audioSearch.prepareThresholds(scale.ChromaticScale('C4'))
    >>> for fq in [450, 510, 550, 600]:
    ...      print normalizeInputFrequency(fq, thresholds, pitches)
    (440.0, A4)
    (523.25113..., C5)
    (277.18263..., C#5)
    (293.66476..., D5)
    '''
    if ((thresholds is None and pitches is not None)
         or (thresholds is not None and pitches is None)):
        raise AudioSearchException("Cannot normalize input frequency if thresholds are given and pitches are not, or vice-versa")   
    elif thresholds == None:
        (thresholds, pitches) = prepareThresholds()
   
    inputPitchLog2 = math.log(inputPitchFrequency, 2)
    (remainder, oct) = math.modf(inputPitchLog2)
    oct = int(oct)
    for i in range(len(thresholds)):
        threshold = thresholds[i]
        if remainder < threshold:
            returnPitch = copy.deepcopy(pitches[i])            
            returnPitch.octave = oct - 4 ## PROBLEM
            #returnPitch.inputFrequency = inputPitchFrequency
            name_note = music21.pitch.Pitch(str(pitches[i]))
            return name_note.frequency, returnPitch
    # else:
    # above highest threshold
    returnPitch = copy.deepcopy(pitches[-1])
    returnPitch.octave = oct - 3
    returnPitch.inputFrequency = inputPitchFrequency
    name_note = music21.pitch.Pitch(str(pitches[-1]))
    return name_note.frequency, returnPitch      

def pitchFrequenciesToObjects(detectedPitchesFreq, useScale=None):
    '''
    Takes in a list of detected pitch frequencies and returns a tuple where the first element
    is a list of :class:~`music21.pitch.Pitch` objects that best match these frequencies 
    and the second element is a list of the frequencies of those objects that can
    be plotted for matplotlib
    
    
    To-do: only return the former.  The latter can be generated in other ways.
    
    >>> from music21 import *
    >>> scNotes = corpus.parse('luca/gloria').parts[0].flat.notes        
    >>> import os #_DOCS_HIDE
    >>> readPath = os.path.dirname(__file__) + os.path.sep #_DOCS_HIDE
    >>> freqFromAQList = getFrequenciesFromAudioFile(waveFilename=readPath + 'test_audio.wav') #_DOCS_HIDE
    >>> #_DOCS_SHOW freqFromAQList = getFrequenciesFromAudioFile(waveFilename='test_audio.wav')
    >>> detectedPitchesFreq = detectPitchFrequencies(freqFromAQList, useScale=scale.ChromaticScale('C4'))
    >>> detectedPitchesFreq = smoothFrequencies(detectedPitchesFreq)
    >>> (detectedPitchObjects, listplot) = pitchFrequenciesToObjects(detectedPitchesFreq, useScale=scale.ChromaticScale('C4'))
    >>> print detectedPitchObjects
    [A5, A5, A5, D5, D4, B4, A4, F4, E-4, C#3, B3, B3, B3, A3, G3, F3, F3, E3, F#3, F#3,...]   
    '''
    if useScale is None:
        useScale = music21.scale.MajorScale('C4')

    detectedPitchObjects = []
    (thresholds, pitches) = prepareThresholds(useScale)

    for i in range(len(detectedPitchesFreq)):    
        inputPitchFrequency = detectedPitchesFreq[i]
        freq, pitch_name = normalizeInputFrequency(inputPitchFrequency, thresholds, pitches)       
        detectedPitchObjects.append(pitch_name)
    
    listplot = []
    i = 0
    while i < len(detectedPitchObjects) - 1:
        name = detectedPitchObjects[i].name
        hold = i
        tot_octave = 0
        while i < len(detectedPitchObjects) - 1 and detectedPitchObjects[i].name == name:
            tot_octave = tot_octave + detectedPitchObjects[i].octave
            i = i + 1
        tot_octave = round(tot_octave / (i - hold))
        for j in range(i - hold):
            detectedPitchObjects[hold + j - 1].octave = tot_octave
            listplot.append(detectedPitchObjects[hold + j - 1].frequency)
    return detectedPitchObjects, listplot


        
def getFrequenciesFromMicrophone(length=10.0, storeWaveFilename=None):
    '''
    records for length (=seconds) a set of frequencies from the microphone.
    
    If storeWaveFilename is not None, then it will store the recording on disk
    in a wave file.
    
    Returns a list of frequencies detected.
    
    
    TODO -- find a way to test... or at least demo
    '''
    
    storedWaveSampleList = []
    environLocal.printDebug("* start recording")
    storedWaveSampleList = recording.samplesFromRecording(seconds=length,
                                                          storeFile=storeWaveFilename,
                                                          recordChunkLength=audioChunkLength)
    environLocal.printDebug("* stop recording")
    
    freqFromAQList = []
    
    for data in storedWaveSampleList:
        samps = numpy.fromstring(data, dtype=numpy.int16)
        freqFromAQList.append(autocorrelationFunction(samps, recordSampleRate))  
    return freqFromAQList


def getFrequenciesFromAudioFile(waveFilename='xmas.wav'):
    '''
    gets a list of frequencies from a complete audio file.
    
    
    >>> from music21 import *
    >>> import os #_DOCS_HIDE
    >>> readPath = os.path.dirname(__file__) + os.path.sep #_DOCS_HIDE
    >>> freq = getFrequenciesFromAudioFile(waveFilename=readPath + 'test_audio.wav') #_DOCS_HIDE
    >>> #_DOCS_SHOW freq = getFrequenciesFromAudioFile(waveFilename='test_audio.wav')
    >>> print freq
    [143.627689055..., 99.083545201..., 211.004784688..., 4700.313479623..., ...]
    '''
    storedWaveSampleList = []
    environLocal.printDebug("* reading entire file from disk")
    try:
        wv = wave.open(waveFilename, 'r')
    except IOError:
        raise AudioSearchException("Cannot open %s for reading, does not exist" % waveFilename)
    
    #modify it to read the entire file
    for i in range(wv.getnframes() / audioChunkLength):        
        data = wv.readframes(audioChunkLength)
        storedWaveSampleList.append(data)
    
    freqFromAQList = []        
    for data in storedWaveSampleList:
        samps = numpy.fromstring(data, dtype=numpy.int16)
        freqFromAQList.append(autocorrelationFunction(samps, recordSampleRate))  
    wv.close()
    
    return freqFromAQList
    
    
def getFrequenciesFromPartialAudioFile(waveFilenameOrHandle='temp', length=10.0, startSample=0):
    '''
    It calculates the fundamental frequency at every instant of time of an audio signal 
    extracted either from the microphone or from an already recorded song. 
    It uses a period of time defined by the variable "length" in seconds.
    
    It returns a list with the frequencies, a variable with the file descriptor, and the end sample position.
    
    >>> from music21 import *
    >>> #_DOCS_SHOW readFile = 'pachelbel.wav' 
    >>> import os #_DOCS_HIDE
    >>> readPath = os.path.dirname(__file__) #_DOCS_HIDE
    >>> readFile = readPath + os.path.sep + 'test_audio.wav' #_DOCS_HIDE
    >>> frequencyList, pachelbelFileHandle, currentSample  = getFrequenciesFromPartialAudioFile(readFile, length=1.0)
    >>> for i in range(5):
    ...     print frequencyList[i]
    143.627689055
    99.0835452019
    211.004784689
    4700.31347962
    767.827403482
    >>> print currentSample  # should be near 44100, but probably not exact
    44032

    Now read the next 1 second...
    
    >>> frequencyList, pachelbelFileHandle, currentSample  = getFrequenciesFromPartialAudioFile(pachelbelFileHandle, length=1.0, startSample = currentSample)
    >>> for i in range(5):
    ...     print frequencyList[i]
    187.798213268
    238.263483185
    409.700397349
    149.958733396
    101.989786226
    >>> print currentSample  # should be exactly double the previous
    88064


    '''
    if waveFilenameOrHandle == 'temp':
        waveFilenameOrHandle = environLocal.getRootTempDir() + os.path.sep + 'temp.wav'
        
    if common.isStr(waveFilenameOrHandle):
        # waveFilenameOrHandle is a filename
        waveFilename = waveFilenameOrHandle
        try:
            waveHandle = wave.open(waveFilename, 'r')
        except IOError:
            raise AudioSearchException("Cannot open %s for reading, does not exist" % waveFilename)
    else:
        # waveFilenameOrHandle is a filehandle
        waveHandle = waveFilenameOrHandle

    storedWaveSampleList = []
       
    environLocal.printDebug("* reading file from disk a part of the song")
    for i in range(int(math.floor(length * recordSampleRate / audioChunkLength))):        
        startSample = startSample + audioChunkLength
        if startSample < waveHandle.getnframes():
            data = waveHandle.readframes(audioChunkLength)
            storedWaveSampleList.append(data)
    freqFromAQList = []
    
    for data in storedWaveSampleList:
        samps = numpy.fromstring(data, dtype=numpy.int16)
        freqFromAQList.append(autocorrelationFunction(samps, recordSampleRate))  

    endSample = startSample    
    return (freqFromAQList, waveHandle, endSample)
        

def detectPitchFrequencies(freqFromAQList, useScale=music21.scale.MajorScale('C4')):
    '''
    It detects the pitches of the notes from a list of frequencies, using thresholds which
    depend on the used scale. The default value is the major scale C4.
    
    >>> from music21 import *
    >>> freqFromAQList=[143.627689055,99.0835452019,211.004784689,4700.31347962,2197.9431119]
    >>> pitchesList = detectPitchFrequencies(freqFromAQList, useScale=music21.scale.MajorScale('C4'))
    >>> for i in range(5):
    ...     print pitchesList[i]
    146.832383959
    97.9988589954
    220.0
    4698.63628668
    2093.0045224
    '''
    (thresholds, pitches) = prepareThresholds(useScale)
    
    detectedPitchesFreq = []
    
    for i in range(len(freqFromAQList)):    # to find thresholds and frequencies
        inputPitchFrequency = freqFromAQList[i]
        freq, pitch_name = normalizeInputFrequency(inputPitchFrequency, thresholds, pitches)     
        detectedPitchesFreq.append(pitch_name.frequency)    
    return detectedPitchesFreq

def smoothFrequencies(detectedPitchesFreq, smoothLevels=7, inPlace=True):
    '''
    It smooths the shape of the signal in order to avoid false detections in the fundamental
    frequency.
    
    
    >>> from music21 import *
    >>> inputPitches=[440, 440, 440, 440, 442, 443, 441, 470, 440, 441, 440, 442, 440, 440, 440, 397, 440, 440, 440, 442, 443, 441, 440, 440, 440, 440, 440, 442, 443, 441, 440, 440]
    >>> result=smoothFrequencies(inputPitches)
    >>> print result
    [440, 440, 440, 440, 445, 445, 446, 446, 442, 442, 441, 441, 434, 433, 432, 430, 436, 437, 438, 439, 439, 439, 439, 439, 439, 440, 440, 440, 440, 440, 440, 440]
    '''
    dpf = detectedPitchesFreq
    if inPlace == True:
        detectedPitchesFreq = dpf
    else:
        detectedPitchesFreq = copy.copy(dpf)

    #smoothing
    beginning = 0
    ends = 0
    
    for i in range(smoothLevels):
        beginning = beginning + detectedPitchesFreq[i]
    beginning = beginning / smoothLevels
    
    for i in range(smoothLevels):
        ends = ends + detectedPitchesFreq[len(detectedPitchesFreq) - 1 - i] 
    ends = ends / smoothLevels
    
    for i in range(len(detectedPitchesFreq)):
        if i < int(math.floor(smoothLevels / 2.0)):
            detectedPitchesFreq[i] = beginning
        elif i > len(detectedPitchesFreq) - int(math.ceil(smoothLevels / 2.0)) - 1:
            detectedPitchesFreq[i] = ends
        else:
            t = 0
            for j in range(smoothLevels):
                t = t + detectedPitchesFreq[i + j - int(math.floor(smoothLevels / 2.0))]
            detectedPitchesFreq[i] = t / smoothLevels
    return detectedPitchesFreq



#-------------------------------------------------------
# Duration related routines


def joinConsecutiveIdenticalPitches(detectedPitchObjects):
    '''
    takes a list of equally-spaced :class:`~music21.pitch.Pitch` objects
    and returns a tuple of two lists, the first a list of 
    :class:`~music21.note.Note` 
    or :class:`~music21.note.Rest` objects (each of quarterLength 1.0) 
    and a list of how many were joined together to make that object.
    
    
    N.B. the returned list is NOT a :class:`~music21.stream.Stream`.    



    >>> from music21 import *
    >>> import os #_DOCS_HIDE
    >>> scNotes = corpus.parse('luca/gloria').parts[0].flat.notes        
    >>> readPath = os.path.dirname(__file__) + os.path.sep #_DOCS_HIDE
    >>> freqFromAQList = getFrequenciesFromAudioFile(waveFilename=readPath + 'test_audio.wav') #_DOCS_HIDE
    >>> detectedPitchesFreq = detectPitchFrequencies(freqFromAQList, useScale=scale.ChromaticScale('C4'))
    >>> detectedPitchesFreq = smoothFrequencies(detectedPitchesFreq)
    >>> (detectedPitchObjects, listplot) = pitchFrequenciesToObjects(detectedPitchesFreq, useScale=scale.ChromaticScale('C4'))
    >>> (notesList, durationList) = joinConsecutiveIdenticalPitches(detectedPitchObjects)
    >>> print notesList
    [<music21.note.Rest rest>, <music21.note.Note C>, <music21.note.Note C>, <music21.note.Note D>, <music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>, ...]
    >>> print durationList
    [72, 6, 14, 23, 34, 40, 27, 36, 35, 15, 17, 15, 6, 33, 22, 13, 16, 39, 35, 38, 27, 27, 27, 8]
    '''
    
    #initialization
    REST_FREQUENCY = 10
    detectedPitchObjects[0].frequency = REST_FREQUENCY

    #detecting the length of each note 
    j = 0
    good = 0
    bad = 0
    valid_note = False
    
    total_notes = 0
    total_rests = 0
    notesList = []
    durationList = []
    
    while j < len(detectedPitchObjects):
        fr = detectedPitchObjects[j].frequency

        # detect consecutive instances of the same frequency
        while j < len(detectedPitchObjects) and fr == detectedPitchObjects[j].frequency:
            good = good + 1
            
            # if more than 6 consecutive identical samples, it might be a note
            if good >= 6:
                valid_note = True
                
                # if we've gone 15 or more samples without getting something constant, assume it's a rest
                if bad >= 15:
                    durationList.append(bad)   
                    total_rests = total_rests + 1    
                    notesList.append(note.Rest())
                bad = 0       
            j = j + 1
        if valid_note == True:
            durationList.append(good)        
            total_notes = total_notes + 1    
            ### doesn't this unnecessarily create a note that it doesn't need?
            ### notesList.append(detectedPitchObjects[j-1].frequency) should work
            n = note.Note()
            n.pitch = detectedPitchObjects[j - 1]
            notesList.append(n)
        else:
            bad = bad + good
        good = 0
        valid_note = False
        j = j + 1
    return notesList, durationList


def quantizeDuration(length):
    '''
    round an approximately transcribed quarterLength to a better one in
    music21.
    
    
    Should be replaced by a full-featured routine in midi or stream.
    
    
    See :meth:`~music21.stream.Stream.quantize` for more information
    on the standard music21 methodology.
    
    
    >>> from music21 import *
    >>> audioSearch.quantizeDuration(1.01)
    1.0
    >>> audioSearch.quantizeDuration(1.70)
    1.5
    '''
    length = length * 100
    typicalLengths = [25.00, 50.00, 100.00, 150.00, 200.00, 400.00]
    thresholds = []
    for i in range(len(typicalLengths) - 1):
        thresholds.append((typicalLengths[i] + typicalLengths[i + 1]) / 2)
    
    finalLength = typicalLengths[0]   
    for i in range(len(thresholds)):        
        threshold = thresholds[i]
        if length > threshold:
            finalLength = typicalLengths[i + 1]
    return finalLength / 100



def quarterLengthEstimation(durationList, mostRepeatedQuarterLength=1.0):
    '''
    takes a list of lengths of notes (measured in
    audio samples) and tries to estimate using
    matplotlib.pyplot.hist what the length of a
    quarter note should be in this list.
    
    If mostRepeatedQuarterLength is another number, it still returns the
    estimated length of a quarter note, but chooses it so that the most
    common note in durationList will be the other note.  See example 2:
    :
    
    
    Returns a float -- and not an int.
    
    
    >>> from music21 import *
    >>> durationList = [20, 19, 10, 30, 6, 21]
    >>> audioSearch.quarterLengthEstimation(durationList)
    20.625    
    
    
    Example 2: suppose these are the inputted durations for a
    score where most of the notes are half notes.  Show how long
    a quarter note should be:
    
    >>> audioSearch.quarterLengthEstimation(durationList, mostRepeatedQuarterLength = 2.0)
    10.3125    


    ''' 
    dl = copy.copy(durationList)
    dl.append(0)

    pdf, bins = histogram(dl,8.0)        

    #environLocal.printDebug("HISTOGRAMA %s %s" % (pdf, bins))
    
    i = len(pdf) - 1 # backwards! it has more sense
    while pdf[i] != max(pdf):
        i = i - 1
    qle = (bins[i] + bins[i + 1]) / 2.0


    if mostRepeatedQuarterLength == 0:
        mostRepeatedQuarterLength = 1.0

    binPosition = 0 - math.log(mostRepeatedQuarterLength, 2)
    qle = qle * math.pow(2, binPosition) # it normalizes the length to a quarter note

    #environLocal.printDebug("QUARTER ESTIMATION")
    #environLocal.printDebug("bins %s " % bins)
    #environLocal.printDebug("pdf %s" % pdf)
    #environLocal.printDebug("quarterLengthEstimate %f" % qle)
    return qle



        
    
def notesAndDurationsToStream(notesList, durationList, scNotes=None,
                              removeRestsAtBeginning=True, qle=None):
    '''
    take a list of :class:`~music21.note.Note` objects or rests
    and an equally long list of how long
    each ones lasts in terms of samples and returns a
    Stream using the information from quarterLengthEstimation
    and quantizeDurations.
    
    
    returns a :class:`~music21.stream.Score` object, containing
    a metadata object and a single :class:`~music21.stream.Part` object, which in turn
    contains the notes, etc.  Does not run :meth:`~music21.stream.Stream.makeNotation`
    on the Score.
    
    
    >>> from music21 import *
    >>> durationList = [20, 19, 10, 30, 6, 21]
    >>> n = note.Note
    >>> noteList = [n('C#4'), n('D5'), n('B4'), n('F#5'), n('C5'), note.Rest()]
    >>> s,lengthPart = audioSearch.notesAndDurationsToStream(noteList, durationList)
    >>> s.show('text')
    {0.0} <music21.metadata.Metadata object at ...>
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.note.Note C#>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note B>
        {2.5} <music21.note.Note F#>
        {4.0} <music21.note.Note C>
        {4.25} <music21.note.Rest rest>    
    '''
    
    # rounding lengths    
    p2 = stream.Part() 
    
    # If the score is available, the quarter estimation is better:
    # It could take into account the changes of tempo during the song, but it
    # would take more processing time
    if scNotes != None:
        fe = features.native.MostCommonNoteQuarterLength(scNotes)
        mostCommon = fe.extract().vector[0]        
        qle = quarterLengthEstimation(durationList, mostCommon)
    elif scNotes == None: # this is for the transcriber 
        qle = quarterLengthEstimation(durationList)    

    for i in range(len(durationList)): 
        actualDuration = quantizeDuration(durationList[i] / qle)
        notesList[i].quarterLength = actualDuration
        if (removeRestsAtBeginning == True) and (notesList[i].name == "rest"):
            pass
        else: 
            p2.append(notesList[i])
            removeRestsAtBeginning = False        

    sc = stream.Score()
    sc.metadata = metadata.Metadata()
    sc.metadata.title = 'Automatic Music21 Transcription'
    sc.insert(0, p2)  
    
    if scNotes == None:   # Case transcriber
        return sc, len(p2)
    else: #case follower
        return sc,qle

def decisionProcess(list, notePrediction, beginningData, lastNotePosition, countdown, firstNotePage=None, lastNotePage=None):
    '''
    It decides which of the given parts of the score has a better matching with 
    the recorded part of the song.
    If there is not a part of the score with a high probability to be the correct part,
    it starts a "countdown" in order stop the score following if the bad matching persists.   
    In this case, it does not match the recorded part of the song with any part of the score.
    
    Inputs: List, contains all the possible parts of the score, sorted from the 
    higher probability to be the best matching at the beginning to the lowest probability.
    notePrediction is the position of the score in which the next note should start.
    beginningData is a list with all the beginnings of the used fragments of the score to find
    the best matching.
    lastNotePosition is the position of the score in which the last matched fragment of the 
    score finishes.
    Countdown is a counter of consecutive errors in the matching process.
    
    Outputs: It returns the beginning of the best matching fragment of 
    score and the countdown.
    
    
    
    >>> from music21 import *
    >>> scNotes = corpus.parse('luca/gloria').parts[0].flat.notes    
    >>> scoreStream = scNotes    
    >>> import os #_DOCS_HIDE
    >>> readPath = os.path.dirname(__file__) + os.path.sep #_DOCS_HIDE
    >>> freqFromAQList = getFrequenciesFromAudioFile(waveFilename=readPath + 'test_audio.wav') #_DOCS_HIDE
    >>> #_DOCS_SHOW freqFromAQList = getFrequenciesFromAudioFile(waveFilename='test_audio.wav')
    >>> detectedPitchesFreq = detectPitchFrequencies(freqFromAQList, useScale=scale.ChromaticScale('C4'))
    >>> detectedPitchesFreq = smoothFrequencies(detectedPitchesFreq)
    >>> (detectedPitchObjects, listplot) = pitchFrequenciesToObjects(detectedPitchesFreq, useScale=scale.ChromaticScale('C4'))
    >>> (notesList, durationList) = joinConsecutiveIdenticalPitches(detectedPitchObjects)
    >>> transcribedScore, qle = notesAndDurationsToStream(notesList, durationList, scNotes=scNotes, qle=None)
    >>> hop = 6
    >>> tn_recording = 24
    >>> totScores = []
    >>> beginningData = []
    >>> lengthData = []
    >>> for i in range(4):
    ...     scNotes = scoreStream[i * hop + 1 :i * hop + tn_recording + 1 ] 
    ...     name = "%d" % i
    ...     beginningData.append(i * hop + 1)
    ...     lengthData.append(tn_recording)
    ...     scNotes.id = name
    ...     totScores.append(scNotes)  
    >>> listOfParts = search.approximateNoteSearch(transcribedScore.flat.notes, totScores)
    >>> notePrediction = 0
    >>> lastNotePosition = 0
    >>> countdown = 0
    >>> positionInList, countdown = decisionProcess(listOfParts, notePrediction, beginningData, lastNotePosition, countdown)
    >>> print positionInList
    0
    >>> print countdown # the result is 1 because the song used is completely different from the score!!
    1
    '''
    i = 0
    position = 0
    while i < len(list) and beginningData[int(list[i].id)] < notePrediction:
        i = i + 1
        position = i
    if len(list) == 1: # it happens when you don't play anything during a recording period
        position = 0
        
    dist = math.fabs(beginningData[0] - notePrediction)
    for i in range(len(list)):
        if (list[i].matchProbability >= 0.9 * list[0].matchProbability) and (beginningData[int(list[i].id)] > lastNotePosition): #let's take a 90%
            if math.fabs(beginningData[int(list[i].id)] - notePrediction) < dist:
                dist = math.fabs(beginningData[int(list[i].id)] - notePrediction)
                position = i 
                environLocal.printDebug("NICE") 
                
    #print "ERRORS", position, len(list), lastNotePosition, list[position].matchProbability , beginningData[int(list[position].id)]
    if position < len(list) and beginningData[int(list[position].id)] <= lastNotePosition:
        environLocal.printDebug(" error ? %d, %d" % (beginningData[int(list[position].id)], lastNotePosition))
    if list[position].matchProbability < 0.6 or len(list) == 1: #the latter for the all-rest case
        environLocal.printDebug("ARE YOU SURE YOU ARE PLAYING THE RIGHT SONG??")
        countdown = countdown + 1
        environLocal.printDebug('are you playing the right song?')
    elif dist > 20 and countdown == 0:
        countdown += 1
        environLocal.printDebug("Excessive distance....? dist=%d" % dist)
        
    elif dist > 30 and countdown == 1:
        countdown += 1
        environLocal.printDebug("Excessive distance....? dist=%d" % dist)
        
    elif (firstNotePage != None and lastNotePage != None) and ((beginningData[int(list[position].id)] < firstNotePage or beginningData[int(list[position].id)] > lastNotePage) and countdown < 2):
        countdown += 1
        environLocal.printDebug('playing in a not shown part')
    else:
        countdown = 0
    environLocal.printDebug('****????**** DECISION PROCESS: dist from expected: %d, beginning data: %d , lastNotePos: %d' %(dist, beginningData[int(list[i].id)],lastNotePosition))
    return position, countdown

    
class AudioSearchException(music21.Music21Exception):
    pass

#------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof
