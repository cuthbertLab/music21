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
import matplotlib.mlab # for find
import matplotlib.pyplot
import wave
import numpy

import scipy.signal 
import unittest, doctest

import music21.scale
import music21.pitch
from music21 import environment
from music21 import metadata, note, stream
from music21.audioSearch import recording
_MOD = 'audioSearch/base.py'
environLocal = environment.Environment(_MOD)

audioChunkLength = 1024
recordSampleRate = 44100


def freq_from_autocorr(sig, fs):
    '''  
    JORDI: what does this do.  Did you write the code yourself? if not, what
    is the license on it if any?
    '''
    
    # Calculate autocorrelation (same thing as convolution, but with one input 
    # reversed in time), and throw away the negative lags
    sig = numpy.array(sig)
    #print str(sig)
    corr = scipy.signal.fftconvolve(sig, sig[::-1], mode='full')
    corr = corr[len(corr) / 2:]
    
    # Find the first low point
    d = numpy.diff(corr)
    start = matplotlib.mlab.find(d > 0)[0]
    
    # Find the next peak after the low point (other than 0 lag).  This bit is 
    # not reliable for long signals, due to the desired peak occurring between 
    # samples, and other peaks appearing higher.
    peak = numpy.argmax(corr[start:]) + start
    px, py = parabolic(corr, peak)
    return fs / px

def prepareThresholds(useScale=music21.scale.ChromaticScale('C4')):
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


def parabolic(f, x):
    '''
    Quadratic interpolation for estimating the true position of an
    inter-sample maximum when nearby samples are known.

   
    f is a vector and x is an index for that vector.

   
    Returns (vx, vy), the coordinates of the vertex of a parabola that goes
    through point x and its two neighbors.
   

    Example:
    Defining a vector f with a local maximum at index 3 (= 6), find local
    maximum if points 2, 3, and 4 actually defined a parabola.


    >>> from music21 import *
    >>> import numpy
    >>> f = [2, 3, 1, 6, 4, 2, 3, 1]
    >>> audioSearch.parabolic(f, numpy.argmax(f))
    (3.214285714285..., 6.160714285714...)
   
    '''
    xv = 1.0 / 2.0 * (f[x - 1] - f[x + 1]) / (f[x - 1] - 2.0 * f[x] + f[x + 1]) + x
    yv = f[x] - 1.0 / 4.0 * (f[x - 1] - f[x + 1]) * (xv - x)
    return (xv, yv)



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
    (277.18263..., D-5)
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

def pitchFrequenciesToObjects(detectedPitchesFreq, useScale = music21.scale.MajorScale('C4')):
    '''
    takes in a list of detected pitch frequencies and returns a tuple where the first element
    is a list of :class:~`music21.pitch.Pitch` objects that best match these frequencies 
    and the second element is a list of the frequencies of those objects that can
    be plotted for matplotlib
    
    
    To-do: only return the former.  The latter can be generated in other ways.
    
    '''
    
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


def getFrequenciesFromAudio(record = True, length = 10.0, waveFilename = 'chrom2.wav'):
    storedWaveSampleList = []
    if record == True:
        environLocal.printDebug("* start recording")
        storedWaveSampleList = recording.samplesFromRecording(seconds = length, 
                                                              storeFile = waveFilename, 
                                                              recordChunkLength = audioChunkLength)
        environLocal.printDebug("* stop recording")
        
    else:
        environLocal.printDebug("* reading file from disk")
        try:
            wv = wave.open(waveFilename, 'r')
        except IOError:
            raise AudioSearchException("Cannot open %s for reading, does not exist" % waveFilename)
        
        for i in range(wv.getnframes() / audioChunkLength):        
            data = wv.readframes(audioChunkLength)
            storedWaveSampleList.append(data)
            
    freqFromAQList = []
    for data in storedWaveSampleList:
        samps = numpy.fromstring(data, dtype=numpy.int16)
        freqFromAQList.append(freq_from_autocorr(samps, recordSampleRate))

    return freqFromAQList

def detectPitchFrequencies(freqFromAQList, useScale = music21.scale.MajorScale('C4')):
    (thresholds, pitches) = prepareThresholds(useScale)
    
    detectedPitchesFreq = []
    
    for i in range(len(freqFromAQList)):    # to find thresholds and frequencies
        inputPitchFrequency = freqFromAQList[i]
        freq, pitch_name = normalizeInputFrequency(inputPitchFrequency, thresholds, pitches)     
        detectedPitchesFreq.append(pitch_name.frequency)    
    return detectedPitchesFreq

def smoothFrequencies(detectedPitchesFreq, smoothLevels = 7, inPlace = True):
    dpf = detectedPitchesFreq
    if inPlace == True:
        detectedPitchesFreq = dpf
    else:
        detectedPitchesFreq = copy.copy(dpf)

    ### Jordi -- are you sure that this does what you want it to?
    #smoothing
    for i in range(smoothLevels):
        beginning = detectedPitchesFreq[i]
    beginning = beginning / smoothLevels
    
    for i in range(smoothLevels):
        ends = detectedPitchesFreq[len(detectedPitchesFreq) - 1 - i] 
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
    
    
    Jordi: I've changed this to return the note or rest objects directly
    and not store their frequency.  This will speed things up.
    
    '''
    # detecting notes
    environLocal.printDebug("* joining identical consecutive pitches")
    
    #initialization
    REST_FREQUENCY = 10
    detectedPitchObjects[0].frequency = REST_FREQUENCY
    #BPM = 120 # for the rhythm of the notes
    #JUST_PITCHES = False # If you only want the pitches define it True
    
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

    environLocal.printDebug("Total notes recorded %d " % total_notes)
    environLocal.printDebug("Total rests recorded %d " % total_rests)
    
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
            finalLength = typicalLengths[i+1]
    return finalLength / 100


def quarterLengthEstimation(durationList):
    '''
    takes a list of lengths of notes (measured in
    audio samples) and tries to estimate using
    matplotlib.pyplot.hist what the length of a
    quarter note should be in this list.
    
    
    Returns a float -- and not an int.
    
    
    >>> from music21 import *
    >>> durationList = [20, 19, 10, 30, 6, 21]
    >>> audioSearch.quarterLengthEstimation(durationList)
    19.6875
    
    ''' 
    dl = copy.copy(durationList)
    dl.append(0)
    pdf, bins, patches = matplotlib.pyplot.hist(dl, bins=16)        
    environLocal.printDebug("HISTOGRAMA %s %s" % (pdf, bins))

    i = len(pdf) - 1
    while pdf[i] != max(pdf):
        i = i - 1
    qle = (bins[i] + bins[i + 1]) / 2.0
    environLocal.printDebug("QUARTER ESTIMATION")
    environLocal.printDebug("bins %s " % bins)
    environLocal.printDebug("pdf %s" % pdf)
    environLocal.printDebug("quarterLengthEstimate %f" % qle)
    return qle



    
def notesAndDurationsToStream(notesList, durationList):
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
    >>> s = audioSearch.notesAndDurationsToStream(noteList, durationList)
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

    # quarterLengthEstimation
    qle = quarterLengthEstimation(durationList)
    
    for i in range(len(durationList)): 
        actualDuration = quantizeDuration(durationList[i] / qle)
        notesList[i].quarterLength = actualDuration
        p2.append(notesList[i])        
    sc = stream.Score()
    sc.metadata = metadata.Metadata()
    sc.metadata.title = 'Automatic Music21 Transcription'
    sc.insert(0, p2)       
    return sc


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
