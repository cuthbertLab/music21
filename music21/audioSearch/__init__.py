# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         audioSearch.py
# Purpose:      base subroutines for all audioSearching and score following
#               routines
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Base routines used throughout audioSearching and score-following.

Requires numpy and matplotlib.  Installing scipy makes the process faster
and more accurate using FFT convolve.
'''
__all__ = [
    'transcriber', 'recording', 'scoreFollower',
    'histogram', 'autocorrelationFunction',
    'prepareThresholds', 'interpolation',
    'normalizeInputFrequency', 'pitchFrequenciesToObjects',
    'getFrequenciesFromMicrophone',
    'getFrequenciesFromAudioFile',
    'getFrequenciesFromPartialAudioFile',
    'detectPitchFrequencies',
    'smoothFrequencies',
    'joinConsecutiveIdenticalPitches',
    'quantizeDuration',
    'quarterLengthEstimation',
    'notesAndDurationsToStream',
    'decisionProcess',
    'AudioSearchException',
]

import copy
import math
import os
import pathlib
import wave
import warnings
import unittest

from typing import List, Union

# cannot call this base, because when audioSearch.__init__.py
# imports * from base, it overwrites audioSearch!
from music21 import base
from music21 import common
from music21 import exceptions21
from music21 import features
from music21 import metadata
from music21 import note
from music21 import pitch
from music21 import scale
from music21 import stream

from music21.audioSearch import recording
from music21.audioSearch import transcriber

from music21 import environment
_MOD = 'audioSearch'
environLocal = environment.Environment(_MOD)

audioChunkLength = 1024
recordSampleRate = 44100


def histogram(data, bins):
    # noinspection PyShadowingNames
    '''
    Partition the list in `data` into a number of bins defined by `bins`
    and return the number of elements in each bins and a set of `bins` + 1
    elements where the first element (0) is the start of the first bin,
    the last element (-1) is the end of the last bin, and every remaining element (i)
    is the dividing point between one bin and another.

    >>> data = [1, 1, 4, 5, 6, 0, 8, 8, 8, 8, 8]
    >>> outputData, bins = audioSearch.histogram(data, 8)
    >>> print(outputData)
    [3, 0, 0, 1, 1, 1, 0, 5]
    >>> bins
    [0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    >>> print([int(b) for b in bins])
    [0, 1, 2, 3, 4, 5, 6, 7, 8]

    >>> outputData, bins = audioSearch.histogram(data, 4)
    >>> print(outputData)
    [3, 1, 2, 5]
    >>> print([int(b) for b in bins])
    [0, 2, 4, 6, 8]
    '''
    maxValue = max(data)
    minValue = min(data)
    lengthEachBin = (maxValue - minValue) / bins

    container = []
    for i in range(int(bins)):
        container.append(0)
    for i in data:
        count = 1
        while i > minValue + count * lengthEachBin:
            count += 1
        container[count - 1] += 1

    binsLimits = []
    binsLimits.append(minValue)
    count = 1
    for i in range(int(bins)):
        binsLimits.append(minValue + count * lengthEachBin)
        count += 1
    return container, binsLimits


def autocorrelationFunction(recordedSignal, recordSampleRateIn):
    # noinspection PyShadowingNames
    '''
    Converts the temporal domain into a frequency domain. In order to do that, it
    uses the autocorrelation function, which finds periodicities in the signal
    in the temporal domain and, consequently, obtains the frequency in each instant
    of time.

    >>> import wave
    >>> import numpy  # you need to have numpy, scipy, and matplotlib installed to use this

    >>> wv = wave.open(str(common.getSourceFilePath() /
    ...                     'audioSearch' / 'test_audio.wav'), 'r')
    >>> data = wv.readframes(1024)
    >>> samples = numpy.frombuffer(data, dtype=numpy.int16)
    >>> finalResult = audioSearch.autocorrelationFunction(samples, 44100)
    >>> wv.close()
    >>> print(finalResult)
    143.6276...
    '''
    if 'numpy' in base._missingImport:
        # len(_missingImport) > 0:
        raise AudioSearchException(
            'Cannot run autocorrelationFunction without '
            + f'numpy installed (scipy recommended).  Missing {base._missingImport}')
    import numpy
    try:
        with warnings.catch_warnings():  # scipy.signal gives ImportWarning...
            warnings.simplefilter('ignore', ImportWarning)
            # numpy warns scipy that oldnumeric will be dropped soon.
            warnings.simplefilter('ignore', DeprecationWarning)
            # noinspection PyPackageRequirements
            from scipy.signal import fftconvolve as convolve
    except ImportError:  # pragma: no cover
        warnings.warn('Running convolve without scipy -- will be slower')
        convolve = numpy.convolve

    recordedSignal = numpy.array(recordedSignal)
    correlation = convolve(recordedSignal, recordedSignal[::-1], mode='full')
    lengthCorrelation = len(correlation) // 2
    correlation = correlation[lengthCorrelation:]
    difference = numpy.diff(correlation)  # Calculates the difference between slots
    positiveDifferences = numpy.where(difference > 0)[0]
    if len(positiveDifferences) == 0:  # pylint: disable=len-as-condition
        finalResult = 10  # Rest
    else:
        beginning = positiveDifferences[0]
        peak = numpy.argmax(correlation[beginning:]) + beginning
        vertex = interpolation(correlation, peak)
        finalResult = recordSampleRateIn / vertex
    return finalResult


def prepareThresholds(useScale=None):
    # noinspection PyShadowingNames
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


    >>> pitchThresholds, pitches = audioSearch.prepareThresholds(scale.MajorScale('A3'))
    >>> for i in range(len(pitchThresholds)):
    ...    print(f'{pitches[i]} < {pitchThresholds[i]:.2f} < {pitches[i + 1]}')
    A3 < 0.86 < B3
    B3 < 0.53 < C#4
    C#4 < 0.16 < D4
    D4 < 0.28 < E4
    E4 < 0.45 < F#4
    F#4 < 0.61 < G#4
    G#4 < 1.24 < A4
    '''
    if useScale is None:
        useScale = scale.ChromaticScale('C4')

    scPitches = useScale.pitches
    scPitchesRemainder = []

    for p in scPitches:
        pLog2 = math.log2(p.frequency)
        scPitchesRemainder.append(math.modf(pLog2)[0])
    scPitchesRemainder[-1] += 1

    scPitchesThreshold = []
    for i in range(len(scPitchesRemainder) - 1):
        scPitchesThreshold.append((scPitchesRemainder[i] + scPitchesRemainder[i + 1]) / 2)

    return scPitchesThreshold, scPitches


def interpolation(correlation, peak):
    # noinspection PyShadowingNames
    '''
    Interpolation for estimating the true position of an
    inter-sample maximum when nearby samples are known.

    Correlation is a vector and peak is an index for that vector.

    Returns the x coordinate of the vertex of that parabola.

    >>> import numpy
    >>> f = [2, 3, 1, 6, 4, 2, 3, 1]
    >>> peak = numpy.argmax(f)
    >>> peak  # f[3] is 6, which is the max.
    3
    >>> audioSearch.interpolation(f, peak)
    3.21428571...
    '''
    if peak in (0, len(correlation) - 1):
        return peak

    vertex = (correlation[peak - 1] - correlation[peak + 1]) / (
        correlation[peak - 1] - 2.0 * correlation[peak] + correlation[peak + 1])
    vertex = vertex * 0.5 + peak
    return vertex


def normalizeInputFrequency(inputPitchFrequency, thresholds=None, pitches=None):
    # noinspection PyShadowingNames
    '''
    Takes in an inputFrequency, a set of threshold values, and a set of allowable pitches
    (given by prepareThresholds) and returns a tuple of the normalized frequency and the
    pitch detected (as a :class:`~music21.pitch.Pitch` object)

    It will convert the frequency to be within the range of the default frequencies
    (usually C4 to C5) but the pitch object will have the correct octave.

    >>> audioSearch.normalizeInputFrequency(441.72)
    (440.0, <music21.pitch.Pitch A4>)

    If you will be doing this often, it's best to cache your thresholds and
    pitches by running `prepareThresholds` once first:

    >>> thresholds, pitches = audioSearch.prepareThresholds(scale.ChromaticScale('C4'))
    >>> for fq in [450, 510, 550, 600]:
    ...      print(audioSearch.normalizeInputFrequency(fq, thresholds, pitches))
    (440.0, <music21.pitch.Pitch A4>)
    (523.25113..., <music21.pitch.Pitch C5>)
    (277.18263..., <music21.pitch.Pitch C#5>)
    (293.66476..., <music21.pitch.Pitch D5>)
    '''
    if ((thresholds is None and pitches is not None)
         or (thresholds is not None and pitches is None)):
        raise AudioSearchException(
            'Cannot normalize input frequency if thresholds are given and '
            + 'pitches are not, or vice-versa')

    if thresholds is None:
        (thresholds, pitches) = prepareThresholds()

    inputPitchLog2 = math.log2(inputPitchFrequency)
    (remainder, octave) = math.modf(inputPitchLog2)
    octave = int(octave)

    for i in range(len(thresholds)):
        threshold = thresholds[i]
        if remainder < threshold:
            returnPitch = copy.deepcopy(pitches[i])
            returnPitch.octave = octave - 4  # PROBLEM
            # returnPitch.inputFrequency = inputPitchFrequency
            name_note = pitch.Pitch(str(pitches[i]))
            return name_note.frequency, returnPitch
    # else:
    # above highest threshold
    returnPitch = copy.deepcopy(pitches[-1])
    returnPitch.octave = octave - 3
    returnPitch.inputFrequency = inputPitchFrequency
    name_note = pitch.Pitch(str(pitches[-1]))
    return name_note.frequency, returnPitch


def pitchFrequenciesToObjects(detectedPitchesFreq, useScale=None):
    # noinspection PyShadowingNames
    '''
    Takes in a list of detected pitch frequencies and returns a tuple where the first element
    is a list of :class:~`music21.pitch.Pitch` objects that best match these frequencies
    and the second element is a list of the frequencies of those objects that can
    be plotted for matplotlib

    TODO: only return the former.  The latter can be generated in other ways.

    >>> readPath = common.getSourceFilePath() / 'audioSearch' / 'test_audio.wav'
    >>> freqFromAQList = audioSearch.getFrequenciesFromAudioFile(waveFilename=readPath)

    >>> detectedPitchesFreq = audioSearch.detectPitchFrequencies(
    ...   freqFromAQList, useScale=scale.ChromaticScale('C4'))
    >>> detectedPitchesFreq = audioSearch.smoothFrequencies(detectedPitchesFreq)
    >>> (detectedPitchObjects, listPlot) = audioSearch.pitchFrequenciesToObjects(
    ...   detectedPitchesFreq, useScale=scale.ChromaticScale('C4'))
    >>> [str(p) for p in detectedPitchObjects]
    ['A5', 'A5', 'A6', 'D6', 'D4', 'B4', 'A4', 'F4', 'E-4', 'C#3', 'B3', 'B3', 'B3', 'A3', 'G3',...]
    '''
    if useScale is None:
        useScale = scale.MajorScale('C4')

    detectedPitchObjects = []
    (thresholds, pitches) = prepareThresholds(useScale)

    for i in range(len(detectedPitchesFreq)):
        inputPitchFrequency = detectedPitchesFreq[i]
        unused_freq, pitch_name = normalizeInputFrequency(inputPitchFrequency, thresholds, pitches)
        detectedPitchObjects.append(pitch_name)

    listPlot = []
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
            listPlot.append(detectedPitchObjects[hold + j - 1].frequency)
    return detectedPitchObjects, listPlot


def getFrequenciesFromMicrophone(length=10.0, storeWaveFilename=None):
    '''
    records for length (=seconds) a set of frequencies from the microphone.

    If storeWaveFilename is not None, then it will store the recording on disk
    in a wave file.

    Returns a list of frequencies detected.

    TODO -- find a way to test... or at least demo
    '''
    if 'numpy' in base._missingImport:
        raise AudioSearchException(
            'Cannot run getFrequenciesFromMicrophone without numpy installed')

    import numpy
    environLocal.printDebug('* start recording')
    storedWaveSampleList = recording.samplesFromRecording(seconds=length,
                                                          storeFile=storeWaveFilename,
                                                          recordChunkLength=audioChunkLength)
    environLocal.printDebug('* stop recording')

    freqFromAQList = []

    for data in storedWaveSampleList:
        samples = numpy.frombuffer(data, dtype=numpy.int16)
        freqFromAQList.append(autocorrelationFunction(samples, recordSampleRate))
    return freqFromAQList


def getFrequenciesFromAudioFile(waveFilename='xmas.wav'):
    '''
    gets a list of frequencies from a complete audio file.

    Each sample is a window of audioSearch.audioChunkLength long.

    >>> audioSearch.audioChunkLength
    1024

    >>> readPath = common.getSourceFilePath() / 'audioSearch' / 'test_audio.wav'
    >>> freq = audioSearch.getFrequenciesFromAudioFile(waveFilename=readPath)
    >>> print(freq)
    [143.627..., 99.083..., 211.004..., 4700.313..., ...]
    '''
    if 'numpy' in base._missingImport:
        raise AudioSearchException(
            'Cannot run getFrequenciesFromAudioFile without numpy installed')
    import numpy

    storedWaveSampleList = []
    environLocal.printDebug('* reading entire file from disk')
    try:
        wv = wave.open(str(waveFilename), 'r')
    except IOError:
        raise AudioSearchException(f'Cannot open {waveFilename} for reading, does not exist')

    # modify it to read the entire file
    for i in range(int(wv.getnframes() / audioChunkLength)):
        data = wv.readframes(audioChunkLength)
        storedWaveSampleList.append(data)

    freqFromAQList = []
    for data in storedWaveSampleList:
        samples = numpy.frombuffer(data, dtype=numpy.int16)
        freqFromAQList.append(autocorrelationFunction(samples, recordSampleRate))
    wv.close()

    return freqFromAQList


def getFrequenciesFromPartialAudioFile(waveFilenameOrHandle='temp', length=10.0, startSample=0):
    '''
    It calculates the fundamental frequency at every instant of time of an audio signal
    extracted either from the microphone or from an already recorded song.
    It uses a period of time defined by the variable "length" in seconds.

    It returns a list with the frequencies, a variable with the file descriptor,
    and the end sample position.

    >>> #_DOCS_SHOW readFile = 'pachelbel.wav'
    >>> sp = common.getSourceFilePath() #_DOCS_HIDE
    >>> readFile = sp / 'audioSearch' / 'test_audio.wav' #_DOCS_HIDE
    >>> fTup  = audioSearch.getFrequenciesFromPartialAudioFile(readFile, length=1.0)
    >>> frequencyList, pachelbelFileHandle, currentSample = fTup
    >>> for frequencyIndex in range(5):
    ...     print(frequencyList[frequencyIndex])
    143.627...
    99.083...
    211.004...
    4700.313...
    767.827...
    >>> print(currentSample)  # should be near 44100, but probably not exact
    44032

    Now read the next 1 second...

    >>> fTup = audioSearch.getFrequenciesFromPartialAudioFile(pachelbelFileHandle, length=1.0,
    ...                                                       startSample=currentSample)
    >>> frequencyList, pachelbelFileHandle, currentSample = fTup
    >>> for frequencyIndex in range(5):
    ...     print(frequencyList[frequencyIndex])
    187.798...
    238.263...
    409.700...
    149.958...
    101.989...
    >>> print(currentSample)  # should be exactly double the previous
    88064
    '''
    if 'numpy' in base._missingImport:
        raise AudioSearchException(
            'Cannot run getFrequenciesFromPartialAudioFile without numpy installed')
    import numpy

    if waveFilenameOrHandle == 'temp':
        waveFilenameOrHandle = environLocal.getRootTempDir() / 'temp.wav'

    if isinstance(waveFilenameOrHandle, pathlib.Path):
        waveFilenameOrHandle = str(waveFilenameOrHandle)

    if isinstance(waveFilenameOrHandle, str):
        # waveFilenameOrHandle is a filename
        waveFilename = waveFilenameOrHandle
        try:
            waveHandle = wave.open(waveFilename, 'r')
        except IOError:
            raise AudioSearchException(f'Cannot open {waveFilename} for reading, does not exist')
    else:
        # waveFilenameOrHandle is a file handle
        waveHandle = waveFilenameOrHandle

    storedWaveSampleList = []

    environLocal.printDebug('* reading file from disk a part of the song')
    for i in range(int(math.floor(length * recordSampleRate / audioChunkLength))):
        startSample = startSample + audioChunkLength
        if startSample < waveHandle.getnframes():
            data = waveHandle.readframes(audioChunkLength)
            storedWaveSampleList.append(data)
    freqFromAQList = []

    for data in storedWaveSampleList:
        samples = numpy.frombuffer(data, dtype=numpy.int16)
        freqFromAQList.append(autocorrelationFunction(samples, recordSampleRate))

    endSample = startSample
    return (freqFromAQList, waveHandle, endSample)


def detectPitchFrequencies(freqFromAQList, useScale=None):
    # noinspection PyShadowingNames
    '''
    Detects the pitches of the notes from a list of frequencies, using thresholds which
    depend on the useScale option. If useScale is None,
    the default value is the Major Scale beginning C4.

    Returns the frequency of each pitch after normalizing them.

    >>> freqFromAQList=[143.627689055, 99.0835452019, 211.004784689, 4700.31347962, 2197.9431119]
    >>> cMaj = scale.MajorScale('C4')
    >>> pitchesList = audioSearch.detectPitchFrequencies(freqFromAQList, useScale=cMaj)
    >>> for i in range(5):
    ...     print(int(round(pitchesList[i])))
    147
    98
    220
    4699
    2093
    '''
    if useScale is None:
        useScale = scale.MajorScale('C4')
    (thresholds, pitches) = prepareThresholds(useScale)

    detectedPitchesFreq = []

    for i in range(len(freqFromAQList)):    # to find thresholds and frequencies
        inputPitchFrequency = freqFromAQList[i]
        unused_freq, pitch_name = normalizeInputFrequency(inputPitchFrequency, thresholds, pitches)
        detectedPitchesFreq.append(pitch_name.frequency)
    return detectedPitchesFreq


def smoothFrequencies(
    frequencyList: List[Union[int, float]],
    *,
    smoothLevels=7,
    inPlace=False
) -> List[int]:
    '''
    Smooths the shape of the signal in order to avoid false detections in the fundamental
    frequency.  Takes in a list of ints or floats.

    The second pitch below is obviously too low.  It will be smoothed out...

    >>> inputPitches = [440, 220, 440, 440, 442, 443, 441, 470, 440, 441, 440,
    ...                 442, 440, 440, 440, 397, 440, 440, 440, 442, 443, 441,
    ...                 440, 440, 440, 440, 440, 442, 443, 441, 440, 440]
    >>> result = audioSearch.smoothFrequencies(inputPitches)
    >>> result
    [409, 409, 409, 428, 435, 438, 442, 444, 441, 441, 441,
     441, 434, 433, 432, 431, 437, 438, 439, 440, 440, 440,
     440, 440, 440, 441, 441, 441, 441, 441, 441, 441]

    Original list is unchanged:

    >>> inputPitches[1]
    220

    Different levels of smoothing have different effects.  At smoothLevel=2,
    the isolated 220hz sample is pulling down the samples around it:

    >>> audioSearch.smoothFrequencies(inputPitches, smoothLevels=2)[:5]
    [330, 275, 358, 399, 420]

    Doing this enough times will smooth out a lot of inconsistencies.

    >>> audioSearch.smoothFrequencies(inputPitches, smoothLevels=28)[:5]
    [432, 432, 432, 432, 432]


    If inPlace is True then the list is modified in place and nothing is returned:

    >>> audioSearch.smoothFrequencies(inputPitches, inPlace=True)
    >>> inputPitches[:5]
    [409, 409, 409, 428, 435]

    Note that `smoothLevels=1` is the baseline that does nothing:

    >>> audioSearch.smoothFrequencies(inputPitches, smoothLevels=1) == inputPitches
    True

    And less than 1 raises a ValueError:

    >>> audioSearch.smoothFrequencies(inputPitches, smoothLevels=0)
    Traceback (most recent call last):
    ValueError: smoothLevels must be >= 1

    There cannot be more smoothLevels than input frequencies:

    >>> audioSearch.smoothFrequencies(inputPitches, smoothLevels=40)
    Traceback (most recent call last):
    ValueError: There cannot be more smoothLevels (40) than inputPitches (32)

    Note that the system runs on O(smoothLevels * len(frequenciesList)),
    so additional smoothLevels can be costly on a large set.

    This function always returns a list of ints -- rounding to the nearest
    hertz (you did want it smoothed right?)

    Changed in v.6 -- inPlace defaults to False (like other music21
    functions) and if done in Place, returns nothing.  smoothLevels and inPlace
    became keyword only.
    '''
    if smoothLevels < 1:
        raise ValueError('smoothLevels must be >= 1')

    numFreqs = len(frequencyList)
    if smoothLevels > numFreqs:
        raise ValueError(
            f'There cannot be more smoothLevels ({smoothLevels}) than inputPitches ({numFreqs})'
        )

    dpf = frequencyList
    if inPlace:
        detectedPitchesFreq = dpf
    else:
        detectedPitchesFreq = copy.copy(dpf)

    # smoothing
    beginning = 0.0
    ends = 0.0

    for i in range(smoothLevels):
        beginning = beginning + detectedPitchesFreq[i]
        ends = ends + detectedPitchesFreq[numFreqs - 1 - i]
    beginning = beginning / smoothLevels
    ends = ends / smoothLevels

    for i in range(numFreqs):
        if i < int(math.floor(smoothLevels / 2.0)):
            detectedPitchesFreq[i] = beginning
        elif i > numFreqs - int(math.ceil(smoothLevels / 2.0)) - 1:
            detectedPitchesFreq[i] = ends
        else:
            t = 0
            for j in range(smoothLevels):
                t = t + detectedPitchesFreq[i + j - int(math.floor(smoothLevels / 2.0))]
            detectedPitchesFreq[i] = t / smoothLevels

    for i in range(numFreqs):
        detectedPitchesFreq[i] = int(round(detectedPitchesFreq[i]))

    if not inPlace:
        return detectedPitchesFreq


# ------------------------------------------------------
# Duration related routines


def joinConsecutiveIdenticalPitches(detectedPitchObjects):
    # noinspection PyShadowingNames
    '''
    takes a list of equally-spaced :class:`~music21.pitch.Pitch` objects
    and returns a tuple of two lists, the first a list of
    :class:`~music21.note.Note`
    or :class:`~music21.note.Rest` objects (each of quarterLength 1.0)
    and a list of how many were joined together to make that object.

    N.B. the returned list is NOT a :class:`~music21.stream.Stream`.

    >>> readPath = common.getSourceFilePath() / 'audioSearch' / 'test_audio.wav'
    >>> freqFromAQList = audioSearch.getFrequenciesFromAudioFile(waveFilename=readPath)
    >>> chrome = scale.ChromaticScale('C4')
    >>> detectedPitchesFreq = audioSearch.detectPitchFrequencies(freqFromAQList, useScale=chrome)
    >>> detectedPitchesFreq = audioSearch.smoothFrequencies(detectedPitchesFreq)
    >>> (detectedPitches, listPlot) = audioSearch.pitchFrequenciesToObjects(
    ...        detectedPitchesFreq, useScale=chrome)
    >>> len(detectedPitches)
    861
    >>> notesList, durationList = audioSearch.joinConsecutiveIdenticalPitches(detectedPitches)
    >>> len(notesList)
    24
    >>> print(notesList)
    [<music21.note.Rest rest>, <music21.note.Note C>, <music21.note.Note C>,
     <music21.note.Note D>, <music21.note.Note E>, <music21.note.Note F>,
     <music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>,
     <music21.note.Note C>, ...]
    >>> print(durationList)
    [71, 6, 14, 23, 34, 40, 27, 36, 35, 15, 17, 15, 6, 33, 22, 13, 16, 39, 35, 38, 27, 27, 26, 8]
    '''
    # initialization
    REST_FREQUENCY = 10
    detectedPitchObjects[0].frequency = REST_FREQUENCY

    # detecting the length of each note
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

                # if we've gone 15 or more samples without getting something constant,
                # assume it's a rest
                if bad >= 15:
                    durationList.append(bad)
                    total_rests = total_rests + 1
                    notesList.append(note.Rest())
                bad = 0
            j = j + 1
        if valid_note:
            durationList.append(good)
            total_notes = total_notes + 1
            # doesn't this unnecessarily create a note that it doesn't need?
            # notesList.append(detectedPitchObjects[j - 1].frequency) should work
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
    # noinspection PyShadowingNames
    '''
    takes a list of lengths of notes (measured in
    audio samples) and tries to estimate what the length of a
    quarter note should be in this list.

    If mostRepeatedQuarterLength is another number, it still returns the
    estimated length of a quarter note, but chooses it so that the most
    common note in durationList will be the other note.  See example 2:

    Returns a float -- and not an int.

    >>> durationList = [20, 19, 10, 30, 6, 21]
    >>> audioSearch.quarterLengthEstimation(durationList)
    20.625

    Example 2: suppose these are the inputted durations for a
    score where most of the notes are half notes.  Show how long
    a quarter note should be:

    >>> audioSearch.quarterLengthEstimation(durationList, mostRepeatedQuarterLength=2.0)
    10.3125
    '''
    dl = copy.copy(durationList)
    dl.append(0)

    pdf, bins = histogram(dl, 8.0)

    # environLocal.printDebug(f' HISTOGRAM {pdf} {bins}')

    i = len(pdf) - 1  # backwards! it has more sense
    while pdf[i] != max(pdf):
        i = i - 1
    qle = (bins[i] + bins[i + 1]) / 2.0

    if mostRepeatedQuarterLength == 0:
        mostRepeatedQuarterLength = 1.0

    binPosition = 0 - math.log2(mostRepeatedQuarterLength)
    qle = qle * math.pow(2, binPosition)  # it normalizes the length to a quarter note

    # environLocal.printDebug('QUARTER ESTIMATION')
    # environLocal.printDebug(f' bins {bins} ')
    # environLocal.printDebug(f' pdf {pdf}')
    # environLocal.printDebug(f' quarterLengthEstimate {qle}')
    return qle


def notesAndDurationsToStream(
    notesList,
    durationList,
    scNotes=None,
    removeRestsAtBeginning=True,
    qle=None
):
    # noinspection PyShadowingNames
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
    if scNotes is not None:
        fe = features.native.MostCommonNoteQuarterLength(scNotes)
        mostCommon = fe.extract().vector[0]
        qle = quarterLengthEstimation(durationList, mostCommon)
    elif scNotes is None:  # this is for the transcriber
        qle = quarterLengthEstimation(durationList)

    for i in range(len(durationList)):
        actualDuration = quantizeDuration(durationList[i] / qle)
        notesList[i].quarterLength = actualDuration
        if not (removeRestsAtBeginning and (notesList[i].name == 'rest')):
            p2.append(notesList[i])
            removeRestsAtBeginning = False

    sc = stream.Score()
    sc.metadata = metadata.Metadata()
    sc.metadata.title = 'Automatic Music21 Transcription'
    sc.insert(0, p2)

    if scNotes is None:   # Case transcriber
        return sc, len(p2)
    else:  # case follower
        return sc, qle


def decisionProcess(
    partsList,
    notePrediction,
    beginningData,
    lastNotePosition,
    countdown,
    firstNotePage=None,
    lastNotePage=None
):
    # noinspection PyShadowingNames
    '''
    Decides which of the given parts of the score has the best match with
    the recorded part of the song.
    If there is not a part of the score with a high probability to be the correct part,
    it starts a "countdown" in order stop the score following if the bad matching persists.
    In this case, it does not match the recorded part of the song with any part of the score.

    Inputs: partsList, contains all the possible parts of the score, sorted from the
    higher probability to be the best matching at the beginning to the lowest probability.
    notePrediction is the position of the score in which the next note should start.
    beginningData is a list with all the beginnings of the used fragments of the score to find
    the best matching.
    lastNotePosition is the position of the score in which the last matched fragment of the
    score finishes.
    Countdown is a counter of consecutive errors in the matching process.

    Outputs: Returns the beginning of the best matching fragment of
    score and the countdown.

    >>> scNotes = corpus.parse('luca/gloria').parts[0].flat.notes.stream()
    >>> scoreStream = scNotes
    >>> sfp = common.getSourceFilePath() #_DOCS_HIDE
    >>> readPath = sfp / 'audioSearch' / 'test_audio.wav' #_DOCS_HIDE
    >>> freqFromAQList = audioSearch.getFrequenciesFromAudioFile(waveFilename=readPath) #_DOCS_HIDE

    >>> tf = 'test_audio.wav'
    >>> #_DOCS_SHOW freqFromAQList = audioSearch.getFrequenciesFromAudioFile(waveFilename=tf)
    >>> chrome = scale.ChromaticScale('C4')
    >>> detectedPitchesFreq = audioSearch.detectPitchFrequencies(freqFromAQList, useScale=chrome)
    >>> detectedPitchesFreq = audioSearch.smoothFrequencies(detectedPitchesFreq)
    >>> (detectedPitches, listPlot) = audioSearch.pitchFrequenciesToObjects(
    ...                                             detectedPitchesFreq, useScale=chrome)
    >>> (notesList, durationList) = audioSearch.joinConsecutiveIdenticalPitches(detectedPitches)
    >>> transcribedScore, qle = audioSearch.notesAndDurationsToStream(notesList, durationList,
    ...                                             scNotes=scNotes, qle=None)
    >>> hop = 6
    >>> tn_recording = 24
    >>> totScores = []
    >>> beginningData = []
    >>> lengthData = []
    >>> for i in range(4):
    ...     scNotes = scoreStream[i * hop + 1:i * hop + tn_recording + 1]
    ...     name = str(i)
    ...     beginningData.append(i * hop + 1)
    ...     lengthData.append(tn_recording)
    ...     scNotes.id = name
    ...     totScores.append(scNotes)
    >>> listOfParts = search.approximateNoteSearch(transcribedScore.flat.notes.stream(), totScores)
    >>> notePrediction = 0
    >>> lastNotePosition = 0
    >>> countdown = 0
    >>> positionInList, countdown = audioSearch.decisionProcess(
    ...          listOfParts, notePrediction, beginningData, lastNotePosition, countdown)
    >>> print(positionInList)
    0

    The countdown result is 1 because the song used is completely different from the score!!

    >>> print(countdown)
    1
    '''
    i = 0
    position = 0
    while i < len(partsList) and beginningData[int(partsList[i].id)] < notePrediction:
        i = i + 1
        position = i
    if len(partsList) == 1:  # it happens when you don't play anything during a recording period
        position = 0

    dist = math.fabs(beginningData[0] - notePrediction)
    for i in range(len(partsList)):
        positionBeginningData = beginningData[int(partsList[i].id)]
        if ((partsList[i].matchProbability >= 0.9 * partsList[0].matchProbability)
                and (positionBeginningData > lastNotePosition)):  # let's take a 90%
            if math.fabs(positionBeginningData - notePrediction) < dist:
                dist = math.fabs(positionBeginningData - notePrediction)
                position = i

    positionBeginningData = beginningData[int(partsList[position].id)]
    # print('ERRORS', position, len(partsList), lastNotePosition,
    #      partsList[position].matchProbability , positionBeginningData)
    if position < len(partsList) and positionBeginningData <= lastNotePosition:
        environLocal.printDebug(f' error ? {positionBeginningData}, {lastNotePosition}')
    if partsList[position].matchProbability < 0.6 or len(partsList) == 1:
        # the latter for the all-rest case
        environLocal.printDebug('Are you sure you are playing the right song?')
        countdown = countdown + 1
    elif dist > 20 and countdown == 0:
        countdown += 1
        environLocal.printDebug(f'Excessive distance....? dist={dist}')  # 3.8 replace {dist=}

    elif dist > 30 and countdown == 1:
        countdown += 1
        environLocal.printDebug(f'Excessive distance....? dist={dist}')  # 3.8 replace {dist=}

    elif ((firstNotePage is not None and lastNotePage is not None)
          and ((positionBeginningData < firstNotePage
                or positionBeginningData > lastNotePage)
               and countdown < 2)):
        countdown += 1
        environLocal.printDebug('playing in a not shown part')
    else:
        countdown = 0
    environLocal.printDebug(['****????**** DECISION PROCESS: dist from expected:', dist,
                             'beginning data:', positionBeginningData,
                             'lastNotePos', lastNotePosition])
    return position, countdown


class AudioSearchException(exceptions21.Music21Exception):
    pass

# -----------------------------------------


class Test(unittest.TestCase):
    pass


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []  # type: List[Class]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

