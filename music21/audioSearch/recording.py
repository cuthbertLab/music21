# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.recording.py
# Purpose:      routines for making recordings from microphone input
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
modules for audio searching that directly record from the microphone.


Requires PyAudio and portaudio to be installed (http://www.portaudio.com/download.html)


To download pyaudio for windows 64-bit go to http://www.lfd.uci.edu/~gohlke/pythonlibs/


users of 64-bit windows but 32-bit python should download the win32 port


users of 64-bit windows and 64-bit python should download the amd64 port
 

'''
import os
import unittest
import wave


from music21 import exceptions21
from music21.ext import six

from music21 import environment
_MOD = "audiosearch.recording.py"
environLocal = environment.Environment(_MOD)


###
# to download pyaudio for windows 64-bit go to http://www.lfd.uci.edu/~gohlke/pythonlibs/
# users of 64-bit windows but 32-bit python should download the win32 port
# users of 64-bit windows and 64-bit python should download the amd64 port
# requires portaudio to be installed http://www.portaudio.com/download.html

default_recordChannels = 1
default_recordSampleRate = 44100
default_recordChunkLength = 1024

def samplesFromRecording(seconds=10.0, storeFile=True,
                recordFormat=None,
                recordChannels=default_recordChannels,     
                recordSampleRate=default_recordSampleRate, 
                recordChunkLength=default_recordChunkLength):
    '''
    records `seconds` length of sound in the given format (default Wave)
    and optionally stores it to disk using the filename of `storeFile`
    
    
    Returns a list of samples.
    '''
    
    try:
        import pyaudio #@UnresolvedImport
        recordFormatDefault = pyaudio.paInt16
    except (ImportError, SystemExit):
        pyaudio = None
        environLocal.warn("No Pyaudio found. Recording will probably not work.")
        recordFormatDefault = 8 # pyaudio.paInt16    

    if recordFormat is None:
        recordFormat = recordFormatDefault

    if recordFormat == pyaudio.paInt8:
        raise RecordingException("cannot perform freq_from_autocorr on 8-bit samples")
    
    p_audio = pyaudio.PyAudio()
    st = p_audio.open(format=recordFormat,
                    channels=recordChannels,
                    rate=recordSampleRate,
                    input=True,
                    frames_per_buffer=recordChunkLength)

    recordingLength = int(recordSampleRate * float(seconds) / recordChunkLength)
    
    storedWaveSampleList = []

    #time_start = time.time()
    for i in range(recordingLength):
        data = st.read(recordChunkLength)
        storedWaveSampleList.append(data)
    #print 'Time elapsed: %.3f s\n' % (time.time() - time_start)
    st.close()
    p_audio.terminate()    

    if storeFile != False: 
        if isinstance(storeFile, six.string_types):
            waveFilename = storeFile
        else:
            waveFilename = environLocal.getRootTempDir() + os.path.sep + 'recordingTemp.wav'
        ### write recording to disk
        data = b''.join(storedWaveSampleList)
        try:
            wf = wave.open(waveFilename, 'wb')
            wf.setnchannels(recordChannels)
            wf.setsampwidth(p_audio.get_sample_size(recordFormat))
            wf.setframerate(recordSampleRate)
            wf.writeframes(data)
            wf.close()
        except IOError:
            raise RecordingException("Cannot open %s for writing." % waveFilename)
    return storedWaveSampleList


class RecordingException(exceptions21.Music21Exception):
    pass


#------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testRecording(self):
        '''
        record one second of data and print 10 records
        '''
        sampleList = samplesFromRecording(seconds=1, storeFile=False)
        print(sampleList[30:40])


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
#------------------------------------------------------------------------------
# eof
