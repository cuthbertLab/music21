if __name__ == '__main__':

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
    #while i < len(samps) - 500:
    #    if i < math.floor(window_length / 2):
    #        print "nothing"
    #        RMS.append(samps[i])
    #    elif i > len(samps) - math.ceil(window_length / 2) - 1:
    #        print "ho"
    #        RMS.append(samps[i])
    #    else:
    #        r = 0
    #        for j in range(window_length):
    #            if i + j - 25 >= len(samps):
    #                print i + j - 25
    #            r = r + (math.fabs(samps[i + j - 25]) * math.fabs(samps[i + j - 25]))
    #            if r < 0:
    #                neg = neg + 1
    #                print "R NEGATIVA"
    #                print samps[i + j - 25]
    #                print (samps[i + j - 25]) * (samps[i + j - 25])
    #        RMS.append(math.sqrt(r) / window_length)
    #    i = i + 1
    
    def freq_from_autocorr(sig, fs):
        # Calculate autocorrelation 
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
    
    def prepareThresholds(useScale=scale.MajorScale('C4')):
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
                returnPitch.inputFrequency = inputPitchFrequency
                name_note = pitch.Pitch(str(pitches[i]))
                #freq = dictionary_freq[str(pitches[i])]
                return name_note.frequency, returnPitch
        # above highest threshold
        returnPitch = copy.deepcopy(pitches[-1])
        returnPitch.octave = oct - 3
        returnPitch.inputFrequency = inputPitchFrequency
        name_note = pitch.Pitch(str(pitches[-1]))
        return name_note.frequency, returnPitch      
    
    
    def roundingToTypicalLength(length):
        length = length * 100
        typicalLengths = [25.00, 50.00, 100.00, 200.00, 400.00]
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
        print " HISTOGRAMA", pdf, bins   
        i = len(pdf) - 1
        while pdf[i] != max(pdf):
            i = i - 1
        qle = (bins[i] + bins[i + 1]) / 2
        return qle
    
    
            
            
        
        
    #    i=0
    #    # To avoid rests at the beginning of the song
    #    while i<len(notesList) and notesList[i]==10:
    #        i=i+1
    #    
    #    #matching
    #    while i<len(notesList):
    #        while 
            
        
     
    (t, p) = prepareThresholds(scale.ChromaticScale('C4'))
    
    
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
    
    print "* recording"
    # beginning - recording or not
    WAVE_FILENAME = "chrom.wav"
    
    recording = True
    if recording == True:
        for i in range(2000):
            data = st.read(chunk)
            all.append(data)
            samps = numpy.fromstring(data, dtype=numpy.int16)
            list.append(freq_from_autocorr(samps, fs))
    else:
        wv = wave.open(WAVE_FILENAME, 'r')
        print "NUMERO FRAMES", wv.getnframes()
        for i in range(2000):        
            data = wv.readframes(chunk)
            all.append(data)
            samps = numpy.fromstring(data, dtype=numpy.int16)
            list.append(freq_from_autocorr(samps, fs))    
    
    print "* done recording"
    
    ll = []
    list2 = []
    time_start = time()
    for i in range(len(list)):    # to find thresholds and frequencies
        inputPitchFrequency = list[i]
        freq, pitch_name = normalizeInputFrequency(inputPitchFrequency, dictionary_freq)     
        list2.append(pitch_name.frequency)  
        
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
        print "list2" , list2[i], list2[i].octave
    # smoothing finished
    
    # note counter    
    j = 0
    good = 0
    bad = 0
    total_notes = 0
    valid_note = 0
    total_rests = 0
    notesList = []
    durationList = []
    octavesList = []
    
    while j < len(list2):
        fr = list2[j].frequency
        while j < len(list2) and fr == list2[j].frequency:
            good = good + 1
            if good >= 6:
                valid_note = 1 
                if bad >= 15:
                    print "HE POSAT UN REST"
                    durationList.append(bad)   
                    total_rests = total_rests + 1  
                    n = note.Note(10, quarterLength=1)  
                    notesList.append(n)
                    octavesList.append(100)
                bad = 0       
            j = j + 1
        if valid_note == 1:
            durationList.append(good)        
            total_notes = total_notes + 1   
            print "poso nota", list2[j - 1]
            n = note.Note(list2[j - 1], quarterLength=1)
            print "oct", n.octave
            # n.frequency=list2[j-1] ###############################################
            notesList.append(n)
            octavesList.append(n.octave)
            print "prova1", notesList[0].octave
            print "prova2", notesList[0].name
        else:
            bad = bad + good
        good = 0
        valid_note = 0    
        j = j + 1        
     
    # quarterLengthEstimation
    qle = quarterLengthEstimation(durationList)
    
    # rounding lengths
    actualDurationList = []
    for i in range(len(durationList)):
        print "duracio rara", durationList[i], qle
        actualDurationList.append(roundingToTypicalLength(durationList[i] / qle))
        
    # total notes recording (not consecutive)
    notesRecording = []
    name = ""
    oct = 0
    total_not_consecutive_notes = 0
    part = stream.Part()
    sc = stream.Score()
    
    for i in range(len(notesList)): 
        print "notes_list", notesList[i], notesList[i].pitchNames[0]
        if name != notesList[i].pitchNames[0] or oct != notesList[i].octave: 
            name = notesList[i].pitchNames[0]
            oct = octavesList[i]
            tot_name = "%s%s" % (name, oct)
            print "****NOM", tot_name
            if octavesList[i] == 100: # new rest
                print "RES AQUI"
                notesRecording.append(note.Rest(quarterLength=actualDurationList[i]))
                part.append(note.Rest(quarterLength=actualDurationList[i]))
            else: # new note
                notesRecording.append(note.Note(tot_name, quarterLength=actualDurationList[i]))
                part.append(note.Note(tot_name, quarterLength=actualDurationList[i]))
            total_not_consecutive_notes = total_not_consecutive_notes + 1
        else: # the note or rest is the same as the last one - add durations
            last_length = notesRecording[len(notesRecording) - 1].quarterLength
            notesRecording.pop(len(notesRecording) - 1)
            part.pop(len(notesRecording) - 1)
            if notesList[i].frequency == 10:
                total = last_length + actualDurationList[i]
                notesRecording.append(note.Rest(quarterLength=total))
                part.append(note.Rest(quarterLength=total))                      
            else:
                total = last_length + actualDurationList[i]
                notesRecording.append(note.Note(tot_name, quarterLength=total))
                part.append(note.Note(tot_name, quarterLength=total))
                
         
    print "long notes list" , len(notesList)
    print "total notes no consecutives", total_not_consecutive_notes
    
    print 'Time elapsed: %.3f s\n' % (time() - time_start)
    
    st.close()
    p_audio.terminate()
    sc.insert(0, part) 
    sc.show()
     
    
    

