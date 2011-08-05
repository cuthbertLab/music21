import pyaudio
import wave
import sys
import numpy
import pylab
import matplotlib.pyplot as plt
import math
#from __future__ import division
#from scikits.audiolab import flacread
from numpy.fft import rfft, irfft
from numpy import argmax, sqrt, mean, diff, log
from matplotlib.mlab import find
from scipy.signal import blackmanharris, fftconvolve
from time import time
import sys
from numpy import array
from music21 import *
import copy
import random
from parabolic import parabolic


chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 0.01

p_audio = pyaudio.PyAudio()

st = p_audio.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=chunk)

# RMS of the signal

window_length = 50
RMS = []
i = 0
neg = 0

def freq_from_autocorr(sig, fs):
    # Calculate autocorrelation (same thing as convolution, but with one input 
    # reversed in time), and throw away the negative lags
    sig = array(sig)
    #print str(sig)
    corr = fftconvolve(sig, sig[::-1], mode='full')
    corr = corr[len(corr) / 2:]
    
    # Find the first low point
    d = diff(corr)
    start = find(d > 0)[0]
    
    # Find the next peak after the low point (other than 0 lag).  This bit is 
    # not reliable for long signals, due to the desired peak occurring between 
    # samples, and other peaks appearing higher.
    peak = argmax(corr[start:]) + start
    px, py = parabolic(corr, peak)
    return fs / px


fs = 44100
#canviar l'escala
def prepareThresholds(useScale=scale.ChromaticScale('C4')):
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
 
def normalizeInputFrequency(inputFrequency, dictionary_freq, thresholds=None, pitches=None):
    if thresholds == None:
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
            name_note = pitch.Pitch(str(pitches[i]))
            #freq = dictionary_freq[str(pitches[i])]
            return name_note.frequency, returnPitch
    # above highest threshold
    returnPitch = copy.deepcopy(pitches[-1])
    returnPitch.octave = oct - 3
    returnPitch.inputFrequency = inputPitchFrequency
    name_note = pitch.Pitch(str(pitches[-1]))
    return name_note.frequency, returnPitch      
 
(t, p) = prepareThresholds(scale.MajorScale('C4'))


all = []
list = []
list3 = []
cops = 0
RECORD_SECONDS = 0.5
chunk = 1024
dictionary_freq = {"C4":261.626, "D4":293.665, "E4":329.628, "F4":349.228, "G4":391.995, "A4":440, "B4":493.883, "C5":523.251}

# waiting
#print "* waiting"
#for i in range(550):
#    data = st.read(chunk)
#    samps = numpy.fromstring(data, dtype=numpy.int16)
#    list3.append(samps)
#    
#plt.plot(list3)
#plt.show()
list = []
all = []

print "* recording"
#beginning - recording or not
WAVE_FILENAME = "chrom2.wav"

recording = True
if recording == True:
    for i in range(2000):
        data = st.read(chunk)
        all.append(data)
        samps = numpy.fromstring(data, dtype=numpy.int16)
        list.append(freq_from_autocorr(samps, fs))
else:
    wv = wave.open(WAVE_FILENAME, 'r')
    for i in range(wv.getnframes() / chunk):        
        data = wv.readframes(chunk)
        all.append(data)
        samps = numpy.fromstring(data, dtype=numpy.int16)
        list.append(freq_from_autocorr(samps, fs))    

ll = []
list2 = []
time_start = time()
for i in range(len(list)):    # to find thresholds and frequencies
    inputPitchFrequency = list[i]
    freq, pitch_name = normalizeInputFrequency(inputPitchFrequency, dictionary_freq)     
    list2.append(pitch_name.frequency)    

#smoothing
smooth = 7
for i in range(smooth):
    beginning = list2[i]
beginning = beginning / smooth

for i in range(smooth):
    ends = list2[len(list2) - 1 - i] 
ends = ends / smooth

for i in range(len(list2)):
    if i < int(math.floor(smooth / 2)):
        list2[i] = beginning
    elif i > len(list2) - int(math.ceil(smooth / 2)) - 1:
        list2[i] = ends
    else:
        t = 0
        for j in range(smooth):
            t = t + list2[i + j - int(math.floor(smooth / 2))]
        list2[i] = t / smooth       
for i in range(len(list2)):    
    inputPitchFrequency = list2[i]
    freq, pitch_name = normalizeInputFrequency(inputPitchFrequency, dictionary_freq)       
    list2[i] = pitch_name

listplot = []
i = 0
while i < len(list2) - 1:
    name = list2[i].name
    hold = i
    tot_octave = 0
    while i < len(list2) - 1 and list2[i].name == name:
        tot_octave = tot_octave + list2[i].octave
        i = i + 1
    tot_octave = round(tot_octave / (i - hold))
    for j in range(i - hold):
        list2[hold + j - 1].octave = tot_octave
        listplot.append(list2[hold + j - 1].frequency)


# detecting notes
print "notes detection"  

#initialization
list2[0].frequency = 10
sc = stream.Score()
BPM = 120 # for the rhythm of the notes
JUST_PITCHES = False # If you only want the pitches define it True

#detecting the length of each note 
       
p2 = stream.Part() 
j = 0
good = 0
bad = 0
total_notes = 0
valid_note = 0
total_rests = 0
notesList = []
durationList = []

def roundingToTypicalLength(length):
    length = length * 100
    typicalLengths = [25.00, 50.00, 100.00, 150.00, 200.00, 400.00]
    thresholds = []
    for i in range(len(typicalLengths) - 1):
        thresholds.append((typicalLengths[i] + typicalLengths[i + 1]) / 2)
        finalLength = typicalLengths[0]   
    for i in range(len(thresholds)):        
        threshold = thresholds[i]
        if length > threshold:
            finalLength = typicalLengths[i]
    return finalLength / 100

def quarterLengthEstimation(durationList):    
    mod = durationList
    mod.append(0)
    pdf, bins, patches = plt.hist(mod, bins=16)        
    i = len(pdf) - 1
    while pdf[i] != max(pdf):
        i = i - 1
    qle = (bins[i] + bins[i + 1]) / 2
    print "QUARTER ESTIMATION"
    print "bins", bins
    print "pdf", pdf
    print "qle", qle
    return qle


while j < len(list2):
    fr = list2[j].frequency
    while j < len(list2) and fr == list2[j].frequency:
        good = good + 1
        if good >= 6:
            valid_note = 1 
            if bad >= 15:
                durationList.append(bad)   
                total_rests = total_rests + 1    
                notesList.append(10)
            bad = 0       
        j = j + 1
    if valid_note == 1:
        durationList.append(good)        
        total_notes = total_notes + 1    
        n = note.Note(list2[j - 1], quarterLength=1)
        notesList.append(n.frequency)
    else:
        bad = bad + good
    good = 0
    valid_note = 0    
    j = j + 1    
    
       
# quarterLengthEstimation
qle = quarterLengthEstimation(durationList)

# rounding lengths
actualDurationList = []
print "durationList", len(durationList)
print "notesList", len(notesList)
for i in range(len(durationList) - 1): #because I added a 0
    actualDurationList.append(roundingToTypicalLength(durationList[i] / qle))
    if notesList[i] != 10:
        n = note.Note(quarterLength=actualDurationList[i])
        n.frequency = notesList[i]
        p2.append(n)
    else:
        p2.append(note.Rest(quarterLength=actualDurationList[i]))
    
print "TOTAL_NOTES", total_notes
sc.insert(0, p2)       
#sc.show('text')
sc.show()        
print "* done recording"
print 'Time elapsed: %.3f s\n' % (time() - time_start)

st.close()
p_audio.terminate()

plt.plot(listplot)
plt.show()
#plt.plot(ll)
#plt.show()


#print 'Calculating frequency from FFT:',
#start_time = time()
#print '%f Hz' % freq_from_fft(signal, fs)
#print 'Time elapsed: %.3f s\n' % (time() - start_time)
#
#print 'Calculating frequency from zero crossings:',
#start_time = time()
#print '%f Hz' % freq_from_crossings(signal, fs)
#print 'Time elapsed: %.3f s\n' % (time() - start_time)
#
#print 'Calculating frequency from autocorrelation:',
#start_time = time()
#print '%f Hz' % freq_from_autocorr(signal, fs)
#print 'Time elapsed: %.3f s\n' % (time() - start_time)
#plt.plot(samps)
#plt.show()
#plt.plot(RMS)
#plt.show()

if recording == True:
    data = ''.join(all)
    wf = wave.open(WAVE_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p_audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

print "* END"
