# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.transcriber.py
# Purpose:      Automatically transcribe melodies from a microphone or
#               wave file and output them as a score
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import copy
import math
import random
import sys
from time import time

_missingImport = []
try:
    import matplotlib.pyplot
except ImportError:
    _missingImport.append('matplotlib')

if len(_missingImport) > 0:
    if environLocal['warnings'] in [1, '1', True]:
        pass
        #environLocal.warn(common.getMissingImportStr(_missingImport), header='music21:')

from music21 import environment
from music21 import scale, stream, note, pitch
from music21.audioSearch.base import *
from music21.audioSearch import recording
_MOD = 'audioSearch/transcriber.py'
environLocal = environment.Environment(_MOD)
                                       
                                       
def runTranscribe(show=True, plot=True, useMic=True,
                  seconds=10.0, useScale=scale.ChromaticScale('C4'), saveFile=True):
    '''
    runs all the methods to record from audio for `seconds` length (default 10.0)
    and transcribe the resulting melody.
    
    
    if `useMic` is false it will load a file from disk.
    
    
    if `show` is True then the score will be displayed.


    if `plot` is True then a Tk graph of the frequencies will be displayed.
    
    
    a different scale besides the chromatic scale can be specified by setting `useScale`.
    See :ref:`moduleScale` for a list of allowable scales. (or a custom one can be given).
    Microtonal scales are totally accepted, as are retuned scales where A != 440hz.
    '''
    #beginning - recording or not
    if saveFile != False:
        WAVE_FILENAME = "ex.wav"
    else:
        WAVE_FILENAME = False
    
    # the rest of the score
    time_start = time()
    freqFromAQList, wv, totsamp, samp = getFrequenciesFromAudio(record=useMic, length=seconds, waveFilename=WAVE_FILENAME, wholeFile=False, wv=None)
    detectedPitchesFreq = detectPitchFrequencies(freqFromAQList, useScale)
    detectedPitchesFreq = smoothFrequencies(detectedPitchesFreq)
    (detectedPitchObjects, listplot) = pitchFrequenciesToObjects(detectedPitchesFreq, useScale)
    (notesList, durationList) = joinConsecutiveIdenticalPitches(detectedPitchObjects)
    myScore, length_part = notesAndDurationsToStream(notesList, durationList, removeRestsAtBeginning=True)    
    environLocal.printDebug('Time elapsed: %.3f s' % (time() - time_start))


    if show == True:
        myScore.show()        
    
    if plot == True:
        matplotlib.pyplot.plot(listplot)
        matplotlib.pyplot.show()
    environLocal.printDebug("* END")
    return myScore

if __name__ == '__main__':
    runTranscribe(show=True, plot=True, seconds=20.0)

#------------------------------------------------------------------------------
# eof


