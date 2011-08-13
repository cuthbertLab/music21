# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         noteworthy/translate.py
# Purpose:      translates Noteworthy Composer's NWCTXT format
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

from music21.base import Music21Exception
from music21 import duration
from music21 import note
from music21 import pitch
from music21 import clef
from music21 import meter
from music21 import stream
from music21 import tie
from music21 import key
from music21 import repeat
from music21 import bar
from music21 import chord
from music21 import dynamics
from music21 import spanner


from music21.noteworthy import base as noteworthyModule

import unittest, doctest




def translateNote(line, meas, currentclef, al, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st, lyrics, lyr, coun):
    r'''
    Translation of a music21 note from a NWC note.       
    >>> from music21 import *
    >>> measure,  slur_flag, slur_beginning, slur_1st, tied_flag, tied_1st = noteworthy.translate.translateNote("|Note|Dur:Half|Pos:-3\n",stream.Measure(),"G", 0, 0, 0, 0, 0, 0, "Hi", 1, 0)
    >>> measure[0]
    <music21.note.Note F>        
    '''   
    dictionaries = noteworthyModule.dictionaries

    sl = 0
    ti = 0
    ERR = 0
    TRIPLET = 0
    if al < 0:
        bemol = 1
        al = -al
    else:
        bemol = 0
    
    i = 1
    for word in line.split('|'):
        if i == 3:
            res = word.split(':')
            dur = res[1]
            compt = 0
            for k in range(len(dur)):
                if dur[k] == ",":
                    compt = compt + 1
            if compt != 0:
                parts = dur.split(',')
                lengthnote = parts[0]
                kk = 0
                for kk in parts:
                    if kk == "Grace":
                        #print "GRACE NOTE"
                        # Now it doesn't work, the function for grace notes have to be added here 
                        ERR = 1   
                    elif kk == "Slur":
                        #print "SLUR"
                        if SLUR == 1:
                            SLUR1st = 0
                        else:
                            SLUR1st = 1
                        sl = 1
                        SLUR = 1

                    elif kk == "Triplet" or kk == "Triplet=First" or kk == "Triplet=End":
                        TRIPLET = 1  
                        durat = duration.Duration(float(lengthnote))   
                        tup = duration.Tuplet(3, 2, dictionaries["dictionarytrip"][lengthnote])
                        durat.tuplets = (tup,)  
                        lengthnote = durat.quarterLength 
                    else:
                        lengthnote = dictionaries["dictionaryNoteLength"][parts[0]]                                                                                                         
                
            else:
                lengthnote = dictionaries["dictionaryNoteLength"][dur]
            #print lengthnote
            
        if i == 4:
            res2 = word.split(':')
            pos = res2[1]
            alteration = ""
            flag = 0                
            for kk in range(len(pos)):
                if pos[kk - 1] == "^":
                    r = pos.split('^')                        
                    pos = r[0]
                    flag = 1
                    if TIED == 1:
                        TIED1st = 0
                    else:
                        TIED1st = 1
                    ti = 1
                    TIED = 1
                    
            if pos[0] == "n":
                alteration = "n"
                r = pos.split('n')
                pos = r[1]
                
            if pos[0] == "b":
                alteration = "-"
                r = pos.split('b')
                pos = r[1]  
                
            if pos[0] == "#":
                alteration = "#"
                r = pos.split('#')
                pos = r[1]
                
            if pos[0] == "x":
                alteration = "##"
                r = pos.split('x')
                pos = r[1]
                    
            if pos[0] == "v":
                alteration = "--"
                r = pos.split('v')
                pos = r[1]

            if pos[len(pos) - 2] == "x":
                altfinal = "x"
                r = pos.split('x')
                pos = r[0]
                
            if pos[len(pos) - 2] == "X":
                altfinal = "x"
                r = pos.split('X')
                pos = r[0]
                
            if pos[len(pos) - 2] == "z":
                altfinal = "z"
                r = pos.split('z')
                pos = r[0]
                                                                            
            positionnote = int(pos)
            # Different clefs                
            if currentclef == "TREBLE8dw":
                oct = 4       
                while positionnote < 1 or positionnote > 7:
                    if positionnote < 1:
                        positionnote = positionnote + 7
                        oct = oct - 1
                    if positionnote > 7:
                        positionnote = positionnote - 7
                        oct = oct + 1  
                notename = dictionaries["dictionaryTreble"][positionnote]
            elif currentclef == "TREBLE8up":
                oct = 6       
                while positionnote < 1 or positionnote > 7:
                    if positionnote < 1:
                        positionnote = positionnote + 7
                        oct = oct - 1
                    if positionnote > 7:
                        positionnote = positionnote - 7
                        oct = oct + 1  
                notename = dictionaries["dictionaryTreble"][positionnote]                                   
            elif currentclef == "BASS":
                oct = 3
                while positionnote < -1 or positionnote > 5:
                    if positionnote < -1:
                        positionnote = positionnote + 7
                        oct = oct - 1
                    if positionnote > 5:
                        positionnote = positionnote - 7
                        oct = oct + 1  
                notename = dictionaries["dictionaryBass"][positionnote]
            elif currentclef == "BASS8dw":
                oct = 2
                while positionnote < -1 or positionnote > 5:
                    if positionnote < -1:
                        positionnote = positionnote + 7
                        oct = oct - 1
                    if positionnote > 5:
                        positionnote = positionnote - 7
                        oct = oct + 1  
                notename = dictionaries["dictionaryBass"][positionnote]
            elif currentclef == "BASS8up":
                oct = 4
                while positionnote < -1 or positionnote > 5:
                    if positionnote < -1:
                        positionnote = positionnote + 7
                        oct = oct - 1
                    if positionnote > 5:
                        positionnote = positionnote - 7
                        oct = oct + 1  
                notename = dictionaries["dictionaryBass"][positionnote]                
            elif currentclef == "ALTO":
                oct = 4
                while positionnote < 0 or positionnote > 6:
                    if positionnote < 0:
                        positionnote = positionnote + 7
                        oct = oct - 1
                    if positionnote > 6:
                        positionnote = positionnote - 7
                        oct = oct + 1  
                notename = dictionaries["dictionaryAlto"][positionnote]                
            elif currentclef == "TENOR":
                oct = 3
                while positionnote < -5 or positionnote > 1:
                    if positionnote < -5:
                        positionnote = positionnote + 7
                        oct = oct - 1
                    if positionnote > 1:
                        positionnote = positionnote - 7
                        oct = oct + 1  
                notename = dictionaries["dictionaryTenor"][positionnote]                
            else: # "TREBLE":
                oct = 5
                while positionnote < 1 or positionnote > 7:
                    if positionnote < 1:
                        positionnote = positionnote + 7
                        oct = oct - 1
                    if positionnote > 7:
                        positionnote = positionnote - 7
                        oct = oct + 1  
                notename = dictionaries["dictionaryTreble"][positionnote]
            if al > 0:
                if bemol == 0:
                    #print "Sharp case"                 
                    for f in range(al):
                        if f > 0:
                            if notename == dictionaries["dictionarysharp"][f]:
                                alteration = "#"
                else:
                    for f in range(al):
                        if f > 0:
                            if notename == dictionaries["dictionarybemol"][f]:
                                alteration = "b"

            finalnote = "%s%s%d" % (notename, alteration, oct)           
        i = i + 1
    #print "CLAU ACTUAL ............................... %s" % currentclef
    n1 = note.Note(finalnote, quarterLength=lengthnote)   # note!
    
    # if Tied          
    if TIED1st == 1:
        n1.tie = tie.Tie("start")  
        TIED1st = 0         
    if TIED == 1 and ti == 0:
        n1.tie = tie.Tie("stop") 
        TIED = 0       
    if ti == 0:
        TIED = 0   
    else:
        TIED = 1   
        
    # if Lyrics
    if lyr == 1 and coun < len(lyrics):
        n1.addLyric(lyrics[coun])  
                
    if ERR == 0: # only if it is a grace note
        meas.append(n1)
        
    # if Slur
    if SLUR1st == 1:
        SLURbeginning = n1   
        SLUR1st = 0         
    if SLUR == 1 and sl == 0:
        SLURend = n1           
        finalslur = spanner.Slur(SLURbeginning, SLURend)
        meas.append(finalslur)
        SLUR = 0        
    if sl == 0:
        SLUR = 0   
    else:
        SLUR = 1            
    return meas, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st
    
def translateRest(line, meas):
    r'''
    Translation of a music21 rest.  Adds the rest to the given measure.
    
    
    >>> from music21 import *
    >>> measureIn = stream.Measure()
    >>> measureIn.append(note.HalfNote("C#4"))
    
    >>> measureOut = noteworthy.translate.translateRest("|Rest|Dur:8th\n", measureIn)
    >>> measureOut = noteworthy.translate.translateRest("|Rest|Dur:4th\n", measureOut)
    >>> measureOut.show('text')
    {0.0} <music21.note.Note C#>
    {2.0} <music21.note.Rest rest>     
    {2.5} <music21.note.Rest rest>     
    
    
    Note that measureOut is really the same as measureIn now.
    
    
    >>> measureOut is measureIn
    True
    >>> measureIn.show('text')
    {0.0} <music21.note.Note C#>
    {2.0} <music21.note.Rest rest>     
    {2.5} <music21.note.Rest rest>     
    '''   
    #print "REST"
    dictionaries = noteworthyModule.dictionaries
    try:
        res = line.split('|')[2].split(':')[1].rstrip()
    except:
        raise NoteworthyTranslateException('cannot find a rest in this line: %s ' % line)
    r = note.Rest(quarterLength=dictionaries["dictionaryNoteLength"][res])
    meas.append(r)
    return meas   
  
def createClef(line, meas):
    r'''
    Add a new clef to the current measure and return the measure.
    
    
    Clef lines should look like: \|Clef\|Type:ClefType  or
    \|Clef\|Type:ClefType\|OctaveShift:Octave Down (or Up)
           
     
    >>> from music21 import *
    >>> measureIn = stream.Measure()
    >>> measureOut, currentclef = noteworthy.translate.createClef("|Clef|Type:Treble\n", measureIn)
    >>> measureOut.show('text')
    {0.0} <music21.clef.TrebleClef>      
    >>> currentclef
    'TREBLE'
    >>> measureOut2, currentclef = noteworthy.translate.createClef("|Clef|Type:Bass|OctaveShift:Octave Down", measureOut)
    >>> measureOut2.show('text')
    {0.0} <music21.clef.TrebleClef>      
    {0.0} <music21.clef.Bass8vbClef>      
    
    
    

    If no clef can be found then it raises a NoteworthyTranslate exception


    >>> measureOut, currentclef = noteworthy.translate.createClef("|Clef|Type:OBonobo\n", measureIn)
    Traceback (most recent call last):
    NoteworthyTranslateException: Did not find a clef in line, |Clef|Type:OBonobo

    '''  
    currentclef = None
    i = 1
    octave = 0
    parseElements = line.split('|')
    if len(parseElements) < 3:
        raise NoteworthyTranslateException('Need at least two | characters in "%s" to parse clef' % line)
    parseElements[-1] = parseElements[-1].rstrip()
    if len(parseElements) == 4:
        if parseElements[3] == 'OctaveShift:Octave Down':
            octaveShift = -1
        elif parseElements[3] == 'OctaveShift:Octave Up':
            octaveShift = 1
        elif parseElements[3] == '':
            pass
        else:
            raise NoteworthyTranslateException('Did not get a proper octave shift from %s' % parseElements[3])
    else:
        octaveShift = 0

    try:
        cl = parseElements[2].split(':')[1]
    except:
        raise NoteworthyTranslateException('Did you remember to put "Type:" in this element %s' % parseElements[2])
        
    if cl == "Treble":
        if octaveShift == 0: 
            meas.append(clef.TrebleClef())
            currentclef = "TREBLE"
        elif octaveShift == -1:
            meas.append(clef.Treble8vbClef())
            currentclef = "TREBLE8dw"
        elif octaveShift == 1:
            meas.append(clef.Treble8vaClef())
            currentclef = "TREBLE8up"                   
                
    elif cl == "Bass":
        if octaveShift == 0: 
            meas.append(clef.BassClef())
            currentclef = "BASS"
        elif octaveShift == -1:
            meas.append(clef.Bass8vbClef())
            currentclef = "BASS8dw"
        elif octaveShift == 1:
            meas.append(clef.Bass8vaClef())
            currentclef = "BASS8up"                   

    elif cl == "Alto":
        if octaveShift != 0: 
            raise NoteWorthyTranslateException('cannot shift octaves on an alto clef')
        meas.append(clef.AltoClef())
        currentclef = "ALTO" 
    elif cl == "Tenor":
        if octaveShift != 0: 
            raise NoteWorthyTranslateException('cannot shift octaves on a tenor clef')
        meas.append(clef.TenorClef())
        currentclef = "TENOR" 
    if currentclef is None:
        raise NoteworthyTranslateException('Did not find a clef in line, %s' % line)
    return meas, currentclef

def createKey(line, meas):
    r'''
    Adds a new key signature to the given measure.  Returns the measure and the number of sharps (negative for flats)
    
    
    >>> from music21 import *
    >>> measureIn = stream.Measure()
    >>> measureIn.append(note.Rest(quarterLength = 3.0))
    >>> measureOut, fourSharps = noteworthy.translate.createKey("|Key|Signature:F#,C#,G#,D#\n", measureIn)
    >>> fourSharps
    4
    >>> measureOut.show('text')
    {0.0} <music21.note.Rest rest>
    {3.0} <music21.key.KeySignature of 4 sharps>
    '''  
    i = 1
    for word in line.split('|'):
        if i == 3:
            res = word.split(':')
            ke = res[1]
            alte = 0
            for a in range(len(ke)):
                if ke[a] == "#":
                    alte = alte + 1          
                if ke[a] == "b":
                    alte = alte - 1
            meas.append(key.KeySignature(alte))
        i = i + 1
    return meas, alte    
    
def createTimeSignature(line, meas):
    r'''
    Adding a time signature in the score.      
    >>> from music21 import *
    >>> measure = noteworthy.translate.createTimeSignature("|TimeSig|Signature:4/4\n",stream.Measure())
    >>> measure[0]
    <music21.meter.TimeSignature 4/4>       
    '''   
    i = 1
    # Time signature
    for word in line.split('|'):
        if i == 3:                
            res = word.split(':')
            tim = res[1]
            tim = tim.rstrip()
            if tim == "AllaBreve": # These are strange cases
                times = "2/2"
            elif tim == "Common":
                times = "4/4"
            else:
                times = tim
            meas.append(meter.TimeSignature(times))  
        i = i + 1
    return meas        

def translateChord(line, meas, al, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st, lyrics, lyr, coun, currentclef):
    r'''
    Translation of a music21 chord from a NWC one.      
    >>> from music21 import *
    >>> measure,  slur_flag, slur_beginning, slur_1st, tied, tied_1st = noteworthy.translate.translateChord("|Chord|Dur:4th|Pos:1,3,5\n",stream.Measure(),0, 0, 0, 0, 0, 0, "Hi", 1, 0,"G")
    >>> measure[0]
    <music21.chord.Chord C5 E5 G5>        
    ''' 
    dictionaries = noteworthyModule.dictionaries
    
    sl = 0
    ti = 0
    ERR = 0
    TRIPLET = 0
    if al < 0:
        bemol = 1
        al = -al
    else:
        bemol = 0
    acord = []
    i = 1
    for word in line.split('|'):
        if i == 3:
            res = word.split(':')
            dur = res[1]
            compt = 0
            for k in range(len(dur)):
                if dur[k] == ",":
                    compt = compt + 1
            if compt != 0:
                parts = dur.split(',')
                lengthnote = parts[0]
                for kk in parts:
                    if kk == "Grace":
                        # Now it doesn't work, the function for grace notes have to be added here 
                        ERR = 1
                    elif kk == "Slur":
                        if SLUR == 1:
                            SLUR1st = 0
                        else:
                            SLUR1st = 1
                        sl = 1
                        SLUR = 1      
                    elif kk == "Triplet" or kk == "Triplet=First" or kk == "Triplet=End":
                        TRIPLET = 1  
                        durat = duration.Duration(float(lengthnote))   
                        tup = duration.Tuplet(3, 2, dictionaries["dictionarytrip"][lengthnote])
                        durat.tuplets = (tup,)  
                        lengthnote = durat.quarterLength 
                    else:
                        lengthnote = dictionaries["dictionaryNoteLength"][parts[0]]        
                
            else:
                lengthnote = dictionaries["dictionaryNoteLength"][dur]
        if i == 4:                
            res2 = word.split(':')
            pos = res2[1]
            nt = pos.split(',')
            for n in nt:
                alteration = ""
                pos = n
                flag = 0                  
                for kk in range(len(pos)):
                    if pos[kk - 1] == "^":
                        # TIED case
                        r = pos.split('^')                        
                        pos = r[0]
                        flag = 1
                        if TIED == 1:
                            TIED1st = 0
                        else:
                            TIED1st = 1
                        ti = 1
                        TIED = 1
                    
                if pos[0] == "n": # Alerations
                    alteration = "n"
                    r = pos.split('n')
                    pos = r[1]
                    
                if pos[0] == "b":
                    alteration = "-"
                    r = pos.split('b')
                    pos = r[1]  
                    
                if pos[0] == "#":
                    alteration = "#"
                    r = pos.split('#')
                    pos = r[1]
                    
                if pos[0] == "x":
                    alteration = "##"
                    r = pos.split('x')
                    pos = r[1]
                        
                if pos[0] == "v":
                    alteration = "--"
                    r = pos.split('v')
                    pos = r[1]
                    
                if pos[len(pos) - 1] == "x":
                    altfinal = "x"
                    r = pos.split('x')
                    pos = r[0]
                    
                if pos[len(pos) - 1] == "X":
                    altfinal = "x"
                    r = pos.split('X')
                    pos = r[0]
                    
                if pos[len(pos) - 1] == "z":
                    altfinal = "z"
                    r = pos.split('z')
                    pos = r[0]
                                                                                
                positionnote = int(pos)

                #division
                if currentclef == "TREBLE8dw":
                    oct = 4       
                    while positionnote < 1 or positionnote > 7:
                        if positionnote < 1:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 7:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryTreble"][positionnote]
                elif currentclef == "TREBLE8up":
                    oct = 6       
                    while positionnote < 1 or positionnote > 7:
                        if positionnote < 1:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 7:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryTreble"][positionnote]                                   
                elif currentclef == "BASS":
                    oct = 3
                    while positionnote < -1 or positionnote > 5:
                        if positionnote < -1:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 5:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryBass"][positionnote]
                elif currentclef == "BASS8dw":
                    oct = 2
                    while positionnote < -1 or positionnote > 5:
                        if positionnote < -1:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 5:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryBass"][positionnote]
                elif currentclef == "BASS8up":
                    oct = 4
                    while positionnote < -1 or positionnote > 5:
                        if positionnote < -1:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 5:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryBass"][positionnote]                
                elif currentclef == "ALTO":
                    oct = 4
                    while positionnote < 0 or positionnote > 6:
                        if positionnote < 0:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 6:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryAlto"][positionnote]                
                elif currentclef == "TENOR":
                    oct = 3
                    while positionnote < -5 or positionnote > 1:
                        if positionnote < -5:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 1:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryTenor"][positionnote]                
                else: # "TREBLE":
                    oct = 5
                    while positionnote < 1 or positionnote > 7:
                        if positionnote < 1:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 7:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryTreble"][positionnote]

                  
                if al > 0:
                    if bemol == 0:
                        # Sharp case                   
                        for f in range(al):
                            if f > 0:
                                if notename == dictionaries["dictionarysharp"][f]:
                                    alteration = "#"
                    else: # flat case
                        for f in range(al):
                            if f > 0:
                                if notename == dictionaries["dictionarybemol"][f]:
                                    alteration = "b"
                finalnote = "%s%s%d" % (notename, alteration, oct)
                acord.append(finalnote)                             
        i = i + 1

    if ERR == 0:
        if len(nt) >= 2:
            pitches = acord[0:len(nt)]
            n1 = chord.Chord(pitches, quarterLength=lengthnote)
        
        # Add lyrics
        if lyr == 1 and coun < len(lyrics):
            n1.addLyric(lyrics[coun])  
        
        # if Tied
        if TIED1st == 1:
            n1.tie = tie.Tie("start")  
            TIED1st = 0         
        if TIED == 1 and ti == 0:
            n1.tie = tie.Tie("stop") 
            TIED = 0   
        if ti == 0:
            TIED = 0   
        else:
            TIED = 1   
            
        meas.append(n1) 
        
        #if Slur
        if SLUR1st == 1:
            SLURbeginning = n1   
            SLUR1st = 0         
        if SLUR == 1 and sl == 0:
            SLURend = n1           
            finalslur = spanner.Slur(SLURbeginning, SLURend)
            meas.append(finalslur)
            SLUR = 0        
        if sl == 0:
            SLUR = 0   
        else:
            SLUR = 1            
            
    return meas, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st

def createPart(fl, part, meas, totalscore):
    '''
    Adding a new part in the score.
    '''
    if fl == 0:
        part = stream.Part()
        meas = stream.Measure()
    else:
        part.append(meas)
        totalscore.insert(0, part)
        part = stream.Part()
        meas = stream.Measure()         
        
    return part, meas, totalscore

def createRepetitionBars(line, part, meas):
    r'''
    It translates the repetition bars into music21.
    
    
    >>> from music21 import *
    >>> part,measure =  noteworthy.translate.createRepetitionBars("|Bar|Style:MasterRepeatOpen\n",stream.Part(),stream.Measure())
    >>> measure
    <music21.stream.Measure 0 offset=0.0>        
    >>> measure.leftBarline
    <music21.bar.Repeat direction=start> 
    
    '''
    # Repetition bars
    i = 1
    try:
        style = line.split('|')[2].split(':')[1].rstrip()
    except:
        raise NoteworthyTranslateException('cannot parse %s for repeat signs' % line)
    
    if style == "MasterRepeatOpen":
        part.append(meas)
        meas = stream.Measure()
        meas.leftBarline = bar.Repeat(direction='start')

    elif style == "MasterRepeatClose":
        meas.rightBarline = bar.Repeat(direction='end')
        part.append(meas)
        meas = stream.Measure()
        
    elif style == "LocalRepeatOpen":
        part.append(meas)
        meas = stream.Measure()
        meas.leftBarline = bar.Repeat(direction='start')
        
    elif style == "LocalRepeatClose":
        meas.rightBarline = bar.Repeat(direction='end')
        part.append(meas)
        meas = stream.Measure()
        
    elif style == "Double":
        meas.rightBarline = bar.Barline('double')
        part.append(meas)
        meas = stream.Measure()    
    else:
        raise NoteworthyTranslateException('cannot find a style %s in our list' % style)
    
                            
    return part, meas
            
def createOtherRepetitions(line, meas):
    r'''
    Repetitions like "Coda", "Segno" and some others.
    >>> from music21 import *
    >>> m =  noteworthy.translate.createOtherRepetitions("|Flow|Style:ToCoda|Pos:8|Wide:Y|Placement:BestFitForward\n",stream.Measure())
    >>> "Coda" in m[0].classes
    True
    '''
    # DaCapoAlFine - Coda - Segno - ToCoda
    i = 1
    for word in line.split('|'):
        if i == 3:
            res = word.split(':')
            if res[1] == "DCalFine":
                g = repeat.DaCapoAlFine()
                meas.append(g)
            if res[1] == "Coda":
                g = repeat.Coda()
                meas.append(g)  
            if res[1] == "ToCoda":
                g = repeat.Coda()
                meas.append(g)    
            if res[1] == "Segno":
                g = repeat.Segno()
                meas.append(g)                                                                         
        i = i + 1
    return meas

def createDynamicVariance(line, meas):
    r'''
    Adding dynamics like "crescendo" to the measure.       
    
    
    >>> from music21 import *
    >>> measure = noteworthy.translate.createDynamicVariance("|Flow|Style:ToCoda|Pos:8|Wide:Y|Placement:BestFitForward\n",stream.Measure())
    >>> measure
    <music21.stream.Measure 0 offset=0.0>       
    '''  
    i = 1
    for word in line.split('|'):
        if i == 3:
            res = word.split(':')
            if res[1] == "Crescendo":
                #print "need to add crescendo"
                tt = 1
            if res[1] == "Decrescendo":
                #print "need to add crescendo"
                tt = 1
            if res[1] == "..":
                #print "need to add crescendo"
                tt = 1    
            if res[1] == "...":
                #print "need to add crescendo"
                tt = 1                                                                        
        i = i + 1
    return meas    
    
def createDynamics(line, meas):
    r'''
    Adding dynamics like "fff", "pp", ... to the measure.    
    >>> from music21 import *
    >>> measure = noteworthy.translate.createDynamics("|Dynamic|Style:fff|Pos:-8\n",stream.Measure())
    >>> measure[0]
    <music21.dynamics.Dynamic fff >      
    '''  
    # Dynamic case
    i = 1
    for word in line.split('|'):
        if i == 3:
            res = word.split(':')
            g = dynamics.Dynamic(res[1])
            meas.append(g)                                                                        
        i = i + 1
    return meas

def createLyrics(line):
    r'''
    Adding lyrics       
    >>> from music21 import *
    >>> Lyricslist = noteworthy.translate.createLyrics('|Lyric1|Text:"Hello world"')
    >>> Lyricslist[0]
    'Hello'      
    ''' 
    lyrics = []
    space = 0
    p = line.split('"')
    for word in p[1].split(' '):
        nou = 1
        for wo in word.split('-'):
            if space == 1:
                nou = 0
                space = 0
            for w in wo.split('\n'):                   
                if nou != 1:
                    ll = " -%s" % w
                else:
                    ll = w
                    nou = 0        
                if w == "":
                    space = 0 # if "space=1", it will appear a "-" before the next syllable   
                    ll = " - " 
                lyrics.append(ll)
    return lyrics


# initializations

#file = open("Part_OWeisheit.nwctxt")


def parseFile(filePath):
    file = open(filePath)
    dataList = file.readlines()
    file.close()
    return parseList(dataList)
    
def parseString(data):
    dataList = data.splitlines()
    return parseList(dataList)

def parseList(data):
    r'''
    Parses a list where each element is a line from a nwctxt file.
    
    Returns a :class:`~music21.stream.Score` object
    
    
    >>> from music21 import *
    >>> data = []
    >>> data.append("!NoteWorthyComposer(2.0)\n")
    >>> data.append("|AddStaff|\n")
    >>> data.append("|Clef|Type:Bass\n")
    >>> data.append("|TimeSig|Signature:4/4\n")
    >>> data.append("|Note|Dur:Whole|Pos:1\n")
    >>> s = noteworthy.translate.parseList(data)
    >>> s.show('text')
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note E>

    '''
    totalscore = stream.Score()
    part = stream.Part()
    meas = stream.Measure()
    currentclef = "TREBLE"
    counter = 0
    fl = 0
    start = 0
    alte = 0
    numparts = 0
    newclef = 1
    SLUR = 0
    SLUR1st = 0
    SLURbeginning = 0
    TIED = 0
    TIED1st = 0
    lyr = 0
    coun = 0
    lyrics = []
    text = []
    measWasAppended = False  
   
    
    # Main
    for pi in data:
        for word in pi.split('|'):
            counter += 1
            text.append(word)
            if word == "Note":  
                meas, SLUR, SLURbeginning , SLUR1st, TIED, TIED1st = translateNote(pi, meas, currentclef, alte, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st, lyrics, lyr, coun)
                coun = coun + 1
                measWasAppended = False
            elif word == "Clef":
                meas, currentclef = createClef(pi, meas)
                start = 1
                measWasAppended = False
            elif word == "Rest":
                meas = translateRest(pi, meas)
                measWasAppended = False
            elif word == "Key":
                meas, alte = createKey(pi, meas)
                measWasAppended = False
            elif word == "TimeSig":
                meas = createTimeSignature(pi, meas)
                measWasAppended = False
            elif word == "Chord":
                meas, SLUR, SLURbeginning , SLUR1st, TIED, TIED1st = translateChord(pi, meas, alte, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st, lyrics, lyr, coun, currentclef)
                coun = coun + 1
                measWasAppended = False
            elif word == "AddStaff":
                numparts = numparts + 1
                part, meas, totalscore = createPart(fl, part, meas, totalscore)
                fl = 1  
                alte = 0  
                lyr = 0
                coun = 0            
                measWasAppended = False
            elif word == "Lyric1":
                lyr = 1
                lyrics = createLyrics(pi)
                measWasAppended = False
            elif word == "Bar":
                part, meas = createRepetitionBars(pi, part, meas)
                measWasAppended = False
            elif word == "Flow":
                meas = createOtherRepetitions(pi, meas)
                measWasAppended = False
            elif word == "DynamicVariance":
                meas = createDynamicVariance(pi, meas)
                measWasAppended = False

            elif word == "Dynamic":
                meas = createDynamics(pi, meas)
                measWasAppended = False

            elif word == "Bar\n":
                part.append(meas)
                meas = stream.Measure()
                measWasAppended = True
                
    # Add the last Stuff 
    if measWasAppended == False:
        part.append(meas)
    
    totalscore.insert(0, part)
    
    #print "SHOW"  
    #totalscore.show('text')
    #totalscore.show()
    return totalscore   

class NoteworthyTranslateException(Music21Exception):
    pass


class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    def testBasic(self):
        import os
        nwcTranslatePath = os.path.dirname(__file__)
        simplePath = nwcTranslatePath + os.path.sep + 'verySimple.nwctxt'#'NWCTEXT_Really_complete_example_file.nwctxt' # ## #'Part_OWeisheit.nwctxt' #
        myScore = parseFile(simplePath)
        self.assertEqual(len(myScore.flat.notes), 1)
        self.assertEqual(str(myScore.flat.notes[0].name), "E")
        self.assertEqual(str(myScore.flat.getElementsByClass('Clef')[0]), "<music21.clef.BassClef>")

class TestExternal(unittest.TestCase):
    def runTest(self):
        pass
    def testPaert(self):
        import os
        nwcTranslatePath = os.path.dirname(__file__)
        paertPath = nwcTranslatePath + os.path.sep + 'Part_OWeisheit.nwctxt' #
        myScore = parseFile(paertPath)
        myScore.show()

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

