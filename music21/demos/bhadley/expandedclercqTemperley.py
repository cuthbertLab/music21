'''    Demonstration of how music21 can read in an expanded 
       Clercq and Temperley text file and output roman numeral 
       objects to score. **Note** input text file must be specially 
       expanded using C parser external to music21...I'm working on improving this!
       but this is the most accurate way to do things for now
'''
import os, sys, random, time, urllib
import music21
import shutil


if __name__ == '__main__':

    #CHANGE DIRECTORY BELOW!!!
    #good demo file to try: 23 (Bridge Over Troubled Water)
    #The following numbers of Temperley files won't work: 4,49,50,54,and 180 
    dst = 'C:\\expandedclercqtemperley\\23.txt' #location of EXPANDED clercq and tempereley file
    #format of text file:
    #[start] [end] [Roman numeral] [chromatic root] [diatonic root] [key] [absolute root] [timesig]
    chordlist = []
    
    try:
        f = open(dst, 'r')
        i = 0; 
        for line in f:
            if i == 0:
                if '%' in str(line):
                    piecetitle = str(line)
                    piecetitle = piecetitle.replace('%', '')
                else:
                    piecetitle = dst
                    print "NO PIECE TITLE!"
                print piecetitle, dst
                i = 2
                continue
            else:
                strline = str(line)
                chord = strline.split()
                #print chord
                try:
                    chord[1] = float(chord[1])- float(chord[0])
                except:
                    pass
                chordlist.append(chord)
    
        nicekey = {0:'C', 1:'D-', 2:'D', 3:'E-', 4:'E', 5:'F', 6:'F#', 7:'G', 8:'G', 9:'A-', 10:'A', 11:'B-', 12:'B'}
        
        scoreObj = music21.stream.Score()
        scoreObj.insert(music21.metadata.Metadata())
        scoreObj.metadata.title = piecetitle
        lasttimesig = 0
        lastkey = ''
        
        firsttime = True
        for x in chordlist[0:len(chordlist)]:
            startIndex = float(x[0])
            quarterLength= float(x[1])
            chord = x[2]
            root = x[4]
            thekey = str(nicekey[int(x[5])])
            currentKey = music21.key.Key(thekey)
            timesignature = str(x[7])
            timesig = timesignature.replace('0', '/')
            numerator = int(timesignature[0])
    
            if startIndex != float(0.0) and firsttime == True:
                first =  chordlist[0]
                top = float(first[7][0])
                scoreObj.insert(scoreObj.highestOffset, music21.meter.TimeSignature(timesig))
                scoreObj.append(music21.note.Rest(quarterLength=(float(first[0])*top)))
                scoreObj.insert(scoreObj.highestOffset, currentKey)
                lasttimesig = timesignature
                lastkey = thekey
            firsttime = False
    
            if 'x' in chord:
                chord = chord.replace('x', 'o')
            if 'h':
                chord = chord.replace('h', '/o')
            if chord[0].islower() and 'a' in chord:
                chord = chord.replace('a', '+')
    
            rn = music21.roman.RomanNumeral(chord, currentKey)
            try:
                rn.pitches
            except:
                print 'FAIL:', x
            #TODO: normalize quarterLength due to rounding errors
            rn.duration.quarterLength = (quarterLength * numerator)
            
            rn.lyric = chord
            scoreObj.append(rn)
        
            if timesignature != lasttimesig:
                scoreObj.insert(scoreObj.highestOffset, music21.meter.TimeSignature(timesig))
            if thekey != lastkey:
                scoreObj.insert(scoreObj.highestOffset, currentKey)
        
            lasttimesig = timesignature
            lastkey = thekey
        
        scoreObj.show()
    
    except:
        print "Error....file could not be read (either file does not exist of there's an error in script", dst