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

from music21 import duration, note, pitch, clef, meter, stream, tie, key, repeat
from music21 import bar, chord, dynamics, spanner
import unittest, doctest


class classNote:    
    def caseNote(self, dictionaries, line, meas, actualclef, totlength, al, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st, lyrics, lyr, coun):
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
                            lengthnote = dictionaries["dictionary"][parts[0]]                                                                                                         
                    
                else:
                    lengthnote = dictionaries["dictionary"][dur]
                #print lengthnote
                
            if i == 4:
                res2 = word.split(':')
                pos = res2[1]
                alteration = ""
                #print "POSITIONNN"
                flag = 0                
                for kk in range(len(pos)):
                    if pos[kk - 1] == "^":
                        #print "cas TIED"
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
                if actualclef == "TREBLE8dw":
                    oct = 4       
                    while positionnote < 1 or positionnote > 7:
                        if positionnote < 1:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 7:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryTreble"][positionnote]
                elif actualclef == "TREBLE8up":
                    oct = 6       
                    while positionnote < 1 or positionnote > 7:
                        if positionnote < 1:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 7:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryTreble"][positionnote]                                   
                elif actualclef == "BASS":
                    oct = 3
                    while positionnote < -1 or positionnote > 5:
                        if positionnote < -1:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 5:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryBass"][positionnote]
                elif actualclef == "BASS8dw":
                    oct = 2
                    while positionnote < -1 or positionnote > 5:
                        if positionnote < -1:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 5:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryBass"][positionnote]
                elif actualclef == "BASS8up":
                    oct = 4
                    while positionnote < -1 or positionnote > 5:
                        if positionnote < -1:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 5:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryBass"][positionnote]                
                elif actualclef == "ALTO":
                    oct = 4
                    while positionnote < 0 or positionnote > 6:
                        if positionnote < 0:
                            positionnote = positionnote + 7
                            oct = oct - 1
                        if positionnote > 6:
                            positionnote = positionnote - 7
                            oct = oct + 1  
                    notename = dictionaries["dictionaryAlto"][positionnote]                
                elif actualclef == "TENOR":
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
        #print "CLAU ACTUAL ............................... %s" % actualclef
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
        return meas, totlength, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st
    
class classRest:
    def caseRest(self, dictionaries, line, part, totlength):
        #print "REST"
        i = 1
        for word in line.split('|'):
            if i == 3:
                res = word.split(':')
                r = note.Rest(quarterLength=dictionaries["dictionaryrest"][res[1]])
                part.append(r)
            i = i + 1
        totlength = totlength + dictionaries["dictionaryrest"][res[1]]
        return part, totlength    

class classClef:    
    def caseClef(self, line, meas, start, totlength):
        #print "Clef!"
        i = 1
        octave = 0
        for word in line.split('|'):
            if i == 3:
                res = word.split(':')
                cl = res[1]
                if cl == "Treble\n":
                    #print "TREBLE"
                    meas.append(clef.TrebleClef())
                    actualclef = "TREBLE"                                            
                elif cl == "Bass\n":
                    #print "BASS"
                    meas.append(clef.BassClef())
                    actualclef = "BASS"
                elif cl == "Alto\n":
                    #print Alto
                    meas.append(clef.AltoClef())
                    actualclef = "ALTO" 
                elif cl == "Tenor\n":
                    #print Alto
                    meas.append(clef.TenorClef())
                    actualclef = "TENOR" 
                elif cl == "Treble":
                    octave = 1
                    actualclef = "TREBLE" 
                elif cl == "Bass":
                    actualclef = "BASS" 
                    octave = 1
                elif cl == "Alto":
                    octave = 1
                    actualclef = "ALTO" 
                elif cl == "Tenor":
                    octave = 1                
                    actualclef = "TENOR" 
            if i == 4:
                if octave != 0:
                    r = word.split(' ') # Different octaves
                    if r[1] == "Down\n" and actualclef == "TREBLE" :
                        meas.append(clef.Treble8vbClef())
                        actualclef = "TREBLE8dw"
                    elif r[1] == "Up\n" and actualclef == "TREBLE":
                        meas.append(clef.Treble8vaClef())
                        actualclef = "TREBLE8up"                   
                        #octave = 1      
                    if r[1] == "Down\n" and actualclef == "BASS" :
                        meas.append(clef.Bass8vbClef())
                        actualclef = "BASS8dw"
                    elif r[1] == "Up\n" and actualclef == "BASS":
                        meas.append(clef.Bass8vaClef())
                        actualclef = "BASS8up"                   
                        #octave = 1                           
            i = i + 1
        return meas, actualclef
    
class classKey:
    def caseKey(self, line, meas, totlength, actualclef):
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
    
class classSign:
    def caseSign(self, line, meas, totlength):
        i = 1
        # Time signature
        for word in line.split('|'):
            if i == 3:                
                res = word.split(':')
                tim = res[1]
                t = tim.split('\n')
                tim = t[0]
                if tim == "AllaBreve": # These are strange cases
                    times = "2/2"
                elif tim == "Common":
                    times = "4/4"
                else:
                    times = tim
                meas.insert(totlength, meter.TimeSignature(times))  
            i = i + 1
        return meas        

class classChord:
    def caseChord(self, dictionaries, line, meas, totlength, al, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st, lyrics, lyr, coun, actualclef):
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
                            lengthnote = dictionaries["dictionary"][parts[0]]        
                    
                else:
                    lengthnote = dictionaries["dictionary"][dur]
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
                    if actualclef == "TREBLE8dw":
                        oct = 4       
                        while positionnote < 1 or positionnote > 7:
                            if positionnote < 1:
                                positionnote = positionnote + 7
                                oct = oct - 1
                            if positionnote > 7:
                                positionnote = positionnote - 7
                                oct = oct + 1  
                        notename = dictionaries["dictionaryTreble"][positionnote]
                    elif actualclef == "TREBLE8up":
                        oct = 6       
                        while positionnote < 1 or positionnote > 7:
                            if positionnote < 1:
                                positionnote = positionnote + 7
                                oct = oct - 1
                            if positionnote > 7:
                                positionnote = positionnote - 7
                                oct = oct + 1  
                        notename = dictionaries["dictionaryTreble"][positionnote]                                   
                    elif actualclef == "BASS":
                        oct = 3
                        while positionnote < -1 or positionnote > 5:
                            if positionnote < -1:
                                positionnote = positionnote + 7
                                oct = oct - 1
                            if positionnote > 5:
                                positionnote = positionnote - 7
                                oct = oct + 1  
                        notename = dictionaries["dictionaryBass"][positionnote]
                    elif actualclef == "BASS8dw":
                        oct = 2
                        while positionnote < -1 or positionnote > 5:
                            if positionnote < -1:
                                positionnote = positionnote + 7
                                oct = oct - 1
                            if positionnote > 5:
                                positionnote = positionnote - 7
                                oct = oct + 1  
                        notename = dictionaries["dictionaryBass"][positionnote]
                    elif actualclef == "BASS8up":
                        oct = 4
                        while positionnote < -1 or positionnote > 5:
                            if positionnote < -1:
                                positionnote = positionnote + 7
                                oct = oct - 1
                            if positionnote > 5:
                                positionnote = positionnote - 7
                                oct = oct + 1  
                        notename = dictionaries["dictionaryBass"][positionnote]                
                    elif actualclef == "ALTO":
                        oct = 4
                        while positionnote < 0 or positionnote > 6:
                            if positionnote < 0:
                                positionnote = positionnote + 7
                                oct = oct - 1
                            if positionnote > 6:
                                positionnote = positionnote - 7
                                oct = oct + 1  
                        notename = dictionaries["dictionaryAlto"][positionnote]                
                    elif actualclef == "TENOR":
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
            if len(nt) == 2:
                n1 = chord.Chord([acord[0], acord[1]], quarterLength=lengthnote)
            if len(nt) == 3:
                n1 = chord.Chord([acord[0], acord[1], acord[2]], quarterLength=lengthnote)
            if len(nt) == 4:
                n1 = chord.Chord([acord[0], acord[1], acord[2], acord[3]], quarterLength=lengthnote)
            if len(nt) == 5:
                n1 = chord.Chord([acord[0], acord[1], acord[2], acord[3], acord[4]], quarterLength=lengthnote)
            if len(nt) == 6:
                n1 = chord.Chord([acord[0], acord[1], acord[2], acord[3], acord[4], acord[5]], quarterLength=lengthnote)
            if len(nt) == 7:
                n1 = chord.Chord([acord[0], acord[1], acord[2], acord[3], acord[4], acord[5], acord[6]], quarterLength=lengthnote)
            
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
                
        return meas, totlength, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st

class classPart:
    def caseParts(self, fl, part, meas, totalscore, totlength):
        totlength = 0
        if fl == 0:
            part = stream.Part()
            meas = stream.Measure()
        else:
            part.append(meas)
            totalscore.insert(0, part)
            part = stream.Part()
            meas = stream.Measure()         
            
        return part, meas, totalscore, totlength
    
class classRep:
    def caseRep(self, line, part, meas, totlength):
        # Repetition bars
        i = 1
        for word in line.split('|'):
            if i == 3:
                res = word.split(':')
                cl = res[1]                

                if cl == "MasterRepeatOpen\n":
                    part.append(meas)
                    meas = stream.Measure()
                    meas.leftBarline = bar.Repeat(direction='start')

                elif cl == "MasterRepeatClose\n":
                    meas.rightBarline = bar.Repeat(direction='end')
                    part.append(meas)
                    meas = stream.Measure()
                    
                elif cl == "LocalRepeatOpen\n":
                    part.append(meas)
                    meas = stream.Measure()
                    meas.leftBarline = bar.Repeat(direction='start')
                    
                elif cl == "LocalRepeatClose":
                    meas.rightBarline = bar.Repeat(direction='end')
                    part.append(meas)
                    meas = stream.Measure()
                    
                elif cl == "Double\n":
                    meas.rightBarline = bar.Barline()
                    part.append(meas)
                    meas = stream.Measure()    
                                
            i = i + 1
        return part, meas
            
class classDCalFine:
    def caseDCalFine(self, line, meas):
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

class classDyn:
    def caseDyn(self, line, meas):
        # Dynamics
        i = 1
        for word in line.split('|'):
            if i == 3:
                res = word.split(':')
                if res[1] == "Crescendo":
                    # Crescendo case
                    print ""
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
    
class classDynamics:
    def caseDynamics(self, line, meas):
        # Dynamic case
        i = 1
        for word in line.split('|'):
            if i == 3:
                res = word.split(':')
                g = dynamics.Dynamic(res[1])
                meas.append(g)                                                                        
            i = i + 1
        return meas
    
class classLyrics:
    def caseLyrics(self, line):
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
    totalscore = stream.Score()
    part = stream.Part()
    meas = stream.Measure()
    actualclef = "G"
    counter = 0
    fl = 0
    start = 0
    alte = 0
    numparts = 0
    totlength = 0
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
    
    dictionary = {"Whole":4, "Half": 2, "4th":1, "8th":0.5, "16th":0.25, "32nd":0.125, "64th":0.0625, 0:0}
    dictionaryrest = {"Whole\n":4, "Half\n": 2, "4th\n":1, "8th\n":0.5, "16th\n":0.25, "32nd\n":0.125, "64th\n":0.0625}
    dictionarytrip = {4:"Whole", 2:"Half", 1:"4th", 0.5:"eighth", 0.25: "16th", 0.125: "32nd", 0.0625:"64th", 0:0}
    dictionaryTreble = {1:"C", 2:"D", 3:"E", 4:"F", 5:"G", 6:"A", 7:"B", "octave":5}
    dictionaryBass = {-1:"C", 0:"D", 1:"E", 2:"F", 3:"G", 4:"A", 5:"B", "octave":3}
    dictionaryAlto = {0:"C", 1:"D", 2:"E", 3:"F", 4:"G", 5:"A", 6:"B", "octave":4}
    dictionaryTenor = {-5:"C", -4:"D", -3:"E", -2:"F", -1:"G", 0:"A", 1:"B", "octave":3}
    dictionarysharp = {1:"F", 2:"C", 3:"G", 4:"D", 5:"A", 6:"E", 7:"B"}
    dictionarybemol = {1:"B", 2:"E", 3:"A", 4:"D", 5:"G", 6:"C", 7:"F"}
    dictionaries = {"dictionary":dictionary, "dictionaryrest":dictionaryrest, "dictionarytrip": dictionarytrip, "dictionaryTreble":dictionaryTreble, "dictionaryAlto":dictionaryAlto, "dictionaryTenor":dictionaryTenor, "dictionaryBass":dictionaryBass, "dictionarysharp":dictionarysharp, "dictionarybemol":dictionarybemol}
    
    notes = classNote()
    clefs = classClef()
    rests = classRest()
    keys = classKey()
    sign = classSign()
    ch = classChord()
    np = classPart()
    rep = classRep()
    dc = classDCalFine()
    dyn = classDyn()
    dynam = classDynamics()
    lyri = classLyrics()      
    
    # Main
    for pi in data:
        for word in pi.split('|'):
            counter += 1
            text.append(word)
            if word == "Note":  
                meas, totlength, SLUR, SLURbeginning , SLUR1st, TIED, TIED1st = notes.caseNote(dictionaries, pi, meas, actualclef, totlength, alte, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st, lyrics, lyr, coun)
                coun = coun + 1
                measWasAppended = False
            elif word == "Clef":
                meas, actualclef = clefs.caseClef(pi, meas, start, totlength)
                start = 1
                measWasAppended = False
            elif word == "Rest":
                meas, totlength = rests.caseRest(dictionaries, pi, meas, totlength)
                measWasAppended = False
            elif word == "Key":
                meas, alte = keys.caseKey(pi, meas, totlength, actualclef)
                measWasAppended = False
            elif word == "TimeSig":
                meas = sign.caseSign(pi, meas, totlength)
                measWasAppended = False
            elif word == "Chord":
                meas, totlength, SLUR, SLURbeginning , SLUR1st, TIED, TIED1st = ch.caseChord(dictionaries, pi, meas, totlength, alte, SLUR, SLURbeginning, SLUR1st, TIED, TIED1st, lyrics, lyr, coun, actualclef)
                coun = coun + 1
                measWasAppended = False
            elif word == "AddStaff":
                numparts = numparts + 1
                part, meas, totalscore, totlength = np.caseParts(fl, part, meas, totalscore, totlength)
                fl = 1  
                alte = 0  
                lyr = 0
                coun = 0            
                measWasAppended = False
            elif word == "Lyric1":
                lyr = 1
                lyrics = lyri.caseLyrics(pi)
                measWasAppended = False
            elif word == "Bar":
                part, meas = rep.caseRep(pi, part, meas, totlength)
                measWasAppended = False
            elif word == "Flow":
                meas = dc.caseDCalFine(pi, meas)
                measWasAppended = False
            elif word == "DynamicVariance":
                meas = dyn.caseDyn(pi, meas)
                measWasAppended = False

            elif word == "Dynamic":
                meas = dynam.caseDynamics(pi, meas)
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
    return totalscore
    
    
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    def testBasic(self):
        print "here"

if __name__ == '__main__':
#    import os
#    nwcTranslatePath = os.path.dirname(__file__)
#    paertPath = nwcTranslatePath + os.path.sep + 'verySimple.nwctxt' #'Part_OWeisheit.nwctxt'
#    myScore = parseFile(paertPath)
#    myScore.show('text')
    import music21
    music21.mainTest(Test)

