

import music21
from music21.figuredBass import realizerScale


def chordSymbolObjectToRoman(chordSymbolObject):
    romanString = ""
    pitches = []
    kind = chordSymbolObject.kind
    root = chordSymbolObject.root
    bass = chordSymbolObject.bass
    if kind == 'major':
        romanString =  'I'
    elif kind == 'minor':
        romanString =  'i'
    elif kind == 'augmented':
        romanString =  'I+'
    elif kind == 'diminished':
        romanString =  'io'
    elif kind == 'dominant':
        romanString = 'I-7'
    elif kind == 'major-seventh':
        romanString = 'I7'
    elif kind == 'minor-seventh':
        romanString = 'i-7'
    elif kind == 'diminished-seventh':
        romanString = 'io7'
    elif kind == 'augmented-seventh':
        romanString = 'I+-7'
    elif kind == 'half-diminished':
        romanString = 'i/o-7'
    elif kind == 'major-minor':
        romanString = 'i7'
        
    pitches = music21.roman.RomanNumeral(romanString, str(root)).pitches    
    return music21.chord.Chord(pitches)

def getPitches(chordSymbolObject):
    kind = chordSymbolObject.kind
    root = chordSymbolObject.root
    bass = chordSymbolObject.bass
    inversion = chordSymbolObject.inversion

    romanString = ""
    kind = chordSymbolObject.kind
    root = chordSymbolObject.root
    bass = chordSymbolObject.bass
    if kind == 'major':
        romanString =  'I'
    elif kind == 'minor':
        romanString =  'i'
    elif kind == 'augmented':
        romanString =  'I+'
    elif kind == 'diminished':
        romanString = 'io'
    elif kind == 'dominant':
        romanString = 'I-7'
    elif kind == 'major-seventh':
        romanString = 'I7'
    elif kind == 'minor-seventh':
        romanString = 'i-7'
    elif kind == 'diminished-seventh':
        romanString = 'io7'
    elif kind == 'augmented-seventh':
        romanString = 'I+-7'
    elif kind == 'half-diminished':
        romanString = 'i/o-7'
    elif kind == 'major-minor':
        romanString = 'i7'
    
    romanString = romanString + fbInversion(chordSymbolObject)
        
    return music21.roman.RomanNumeral(romanString, str(root)).pitches    
  
  
def fbInversion(ChordSymbolObject):  
    kind = ChordSymbolObject.kind
    root = ChordSymbolObject.root
    bass = ChordSymbolObject.bass  
    inversion = ChordSymbolObject.inversion   
    triads = ['major', 'minor', 'augmented', 'diminished']
    sevenths = ['dominant', 'major-seventh', 'minor-seventh', 'diminished-seventh', 'augmented-seventh', 'half-diminished', 'major-minor']

    if bass != None and root !=bass and inversion == None:
        interval = music21.interval.notesToInterval(bass, root).name[-1]
        if interval == '3':
            if kind in triads:
                return '63'
            elif kind in sevenths:
                return '65'
        elif interval == '5':
            if kind in triads:
                return '64'
            elif kind in sevenths:
                return '43'
        elif interval == '7' or interval == '2':
            if kind in sevenths:
                return '42'
        else:
            return ''
    elif inversion != None:
        if inversion == 1:
            if kind in triads:
                return '63'
            elif kind in sevenths:
                return '65'
        elif inversion == 2:
            if kind in triads:
                return '64'
            elif kind in sevenths:
                return '43'
        elif inversion == 3:
            if kind in sevenths:
                return '42'
        else:
            return ''
    else:
        return ''


def numInversion(ChordSymbolObject):  
    kind = ChordSymbolObject.kind
    root = ChordSymbolObject.root
    bass = ChordSymbolObject.bass  
    inversion = ChordSymbolObject.inversion   
    if root != bass and bass != None and inversion == None:
        interval = music21.interval.notesToInterval(bass, root).name[-1]
        if interval == '3':
            return 1
        elif interval == '5':
            return 2
        elif interval == '7' or interval == '2':
            return 3
        else:
            return 0
    elif inversion != None:
        return inversion
    else:
        return 0



def getInversion(ChordSymbolObject):
    '''return inversion (1st, 2nd, 3rd) given a ChordSymbol Object)
    >>> h1 = music21.harmony.ChordSymbol()
    >>> h1.root = 'C'
    >>> h1.bass = 'E'
    >>> h1.kind = 'major'
    >>> getInversion(h1)
    1
    
    >>> h2 = music21.harmony.ChordSymbol()
    >>> h2.root = 'C'
    >>> h2.bass = 'G'
    >>> h2.kind = 'major'
    >>> getInversion(h2)
    2
    
    >>> h3 = music21.harmony.ChordSymbol()
    >>> h3.root = 'C'
    >>> h3.bass = 'B-'
    >>> h3.kind = 'dominant'
    >>> getInversion(h3)
    3
    '''
    inversion = 0
    kind = ChordSymbolObject.kind
    root = ChordSymbolObject.root
    bass = ChordSymbolObject.bass
    pitcheswithOctaves = chordSymbolObjectToRoman(ChordSymbolObject)
    pitchesNoOctaves = []
    for x in pitcheswithOctaves:
        stringNote = str(x.pitch)
        pitchesNoOctaves.append(stringNote[0:-1])
    if bass != None:
        #print pitchesNoOctaves
        try:
            inversion = pitchesNoOctaves.index(str(bass))
        except:
            inversion = 0 #should this be an exception like pitch is not in list?
    return inversion   


def majorOrMinor(xmltypeString):
    kind = xmltypeString
    tonality = ''
    if kind == 'major':
        tonality =  'major'
    elif kind == 'minor':
        tonality =  'minor'
    elif kind == 'augmented':
        tonality =  'major'
    elif kind == 'diminished':
        tonality =  'minor'
    elif kind == 'dominant':
        tonality = 'major'
    elif kind == 'major-seventh':
        tonality = 'major'
    elif kind == 'minor-seventh':
        tonality = 'minor'
    elif kind == 'diminished-seventh':
        tonality = 'minor'
    elif kind == 'augmented-seventh':
        tonality = 'major'
    elif kind == 'half-diminished':
        tonality = 'minor'
    elif kind == 'major-minor':
        tonality = 'minor'
    elif kind == 'major-sixth':
        tonality = 'major'
    elif kind == 'minor-sixth':
        tonality = 'minor'
    elif kind == 'dominant-ninth':
        tonality = 'major'
    elif kind == 'major-ninth':
        tonality = 'major'
    elif kind == 'minor-ninth':
        tonality = 'minor'
    elif kind == 'dominant-13th':
        tonality = 'major'
    elif kind == 'major-13th':
        tonality = 'major'
    elif kind == 'minor-13th':
        tonality = 'minor'
    elif kind == 'suspended-second':
        tonality = 'major'
    elif kind == 'suspended-fourth':
        tonality = 'major'
    else:
        tonality = 'major'
    return tonality

def getNotationString(chordSymbolObject):
    notationString = ""
    pitches = []
    kind = chordSymbolObject.kind
    root = chordSymbolObject.root
    bass = chordSymbolObject.bass
    
    if kind == 'major':
        notationString =  ''
    elif kind == 'minor':
        notationString =  ''
    elif kind == 'augmented':
        notationString =  '3,#5'
    elif kind == 'diminished':
        notationString =  '3,-5'
    elif kind == 'dominant':
        notationString = '-7'
    elif kind == 'major-seventh':
        notationString = '7'
    elif kind == 'minor-seventh':
        notationString = '7'
    elif kind == 'diminished-seventh':
        notationString = '3,-5,-7'
    elif kind == 'augmented-seventh':
        notationString = '3,#5,-7'
    elif kind == 'half-diminished':
        notationString = '3,-5,7'
    elif kind == 'major-minor':
        notationString = '#7'
    elif kind == 'major-sixth':
        notationString = '3,5,6'
    elif kind == 'minor-sixth':
        notationString = '3,5,6'
    elif kind == 'dominant-ninth':
        notationString = '3,5,-7,9'
    elif kind == 'major-ninth':
        notationString = '3,5,7,9'
    elif kind == 'minor-ninth':
        notationString = '3,5,7,9'
    elif kind == 'dominant-11':
        notationString = '3,5,-7,9,11'
    else:
        notationString = ''

    return notationString

'''
    dominant-11th (dominant-ninth, perfect 11th)
    major-11th (major-ninth, perfect 11th)
    minor-11th (minor-ninth, perfect 11th)
13ths (usually as the basis for alteration):
    dominant-13th (dominant-11th, major 13th)
    major-13th (major-11th, major 13th)
    minor-13th (minor-11th, major 13th)
Suspended:
    suspended-second (major second, perfect fifth)
    suspended-fourth (perfect fourth, perfect fifth)
Functional sixths:
    Neapolitan
    Italian
    French
    German
Other:
    pedal (pedal-point bass)
    power (perfect fifth)
    Tristan'''
    
def correctChordSymbols(music21piece1, music21piece2): 
    numCorrect = 0 
    chords1 = music21piece1.flat.getElementsByClass(music21.chord.Chord)
    totalNumChords = len(chords1)
    chordLine = music21piece2.getElementsByClass(music21.stream.Part)[1]
    chords2 = chordLine.flat.getElementsByClass([music21.chord.Chord, music21.note.Note])
    print 'here'
    chords2.show('text')
    #1 is correct
    #2 is incorrect
    isCorrect = False
    for chord1, chord2 in zip(chords1, chords2):
        print chord2.classes
        if not('Chord' in chord2.classes):      
            chord2.lyric = "NOT A CHORD"
            continue
        newPitches = []
        for x in chord2.pitches:
            newPitches.append(str(x.name))
        for pitch in chord1:
            print 'from', pitch.name
            print 'to', newPitches
            if pitch.name in newPitches:
                isCorrect = True
            else:
                isCorrect = False
                break
        if isCorrect == True:
            newPitches1 = []
            for y in chord1.pitches:
                newPitches1.append(str(y.name))
            p = chord1.sortDiatonicAscending()
            o =  chord2.sortDiatonicAscending()
            print 'this', p.pitches
            print 'that', o.pitches
            foolist = []
            boolist = []
            for d in p.pitches:
                foolist.append(str(d.name))
            for k in o.pitches:
                boolist.append(str(k.name))
            print foolist
            print boolist
            if foolist != boolist:
                chord2.lyric = "INVERSION"
            else:
                numCorrect = numCorrect + 1
                chord2.lyric = ":)"
        if isCorrect == False:
            chord2.lyric = "PITCHES"

    percentCorrect =  float(numCorrect)/float(totalNumChords) * 100
    s = music21piece2.getElementsByClass(music21.stream.PartStaff)[1]
    s.insert(0, music21.clef.BassClef())
    newScore = music21.stream.Score()
    newScore.append(music21piece2.getElementsByClass(music21.stream.PartStaff)[0])
    newScore.append(s)
   
    return (newScore, percentCorrect) #student's corrected score
    

def realizePitches(harmonyChordSymbolObject):
    x = harmonyChordSymbolObject
    #print x.kind, x.root, x.bass, x.inversion
    #print majorOrMinor(x.kind)
    #pitches = getPitches(x) my old way
    fbScale = realizerScale.FiguredBassScale(x.root, majorOrMinor(x.kind) ) #create figured bass scale with root as scale
    #print getNotationString(x)
    rootNote = str(x.root) + '3' #render in the 3rd octave
    
    pitches = fbScale.getSamplePitches(rootNote, getNotationString(x))
    #print pitches

    inversionNum = numInversion(x)
    if inversionNum != 0:
        #bassNote = music21.note.Note(str(x.bass) + '3')
        #print pitches
        index = -1

        for p in pitches[0:inversionNum]:
            index = index + 1
            octave = str(p)[-1]
            newOctave = int(octave) + 1
            temp = str(p.name) + str(newOctave)
            pitches[index] = music21.pitch.Pitch(temp)
    octaveList = []
    for pitch in pitches:
        #octave = str(p)[-1]
        octaveList.append([str(pitch.name), int(str(pitch)[-1])])
    #octaveList.sort()
    #print octaveList
    takeOctaveDown = False
    for pitch, octave in octaveList:
        if octave >= 4 and (pitch == 'D' or pitch == 'E' or pitch == 'F' or pitch == 'G'):
            takeOctaveDown = True
    i = -1
    if takeOctaveDown:
        for h in pitches:
            i = i + 1
            octave = str(h)[-1]
            newOctave = int(octave) - 1
            temp = str(h.name) + str(newOctave)
            pitches[i] = music21.pitch.Pitch(temp)
    #print pitches
    c = music21.chord.Chord(pitches) 
    c.duration.quarterLength = x.duration.quarterLength 
    return c

    
if __name__ == '__main__':     
    #import doctest
    #doctest.testmod()
    '''WIKIFONIA SPECIFIC
    nicePiece = music21.converter.parse('C:\\Users\\bhadley\\Dropbox\\UROP\\data\\Databases\\wikifoniawithchords\\wikifonia-1028.mxl')

    #nicePiece.show('text')
    j = music21.harmony.getDuration(nicePiece)
    onlyChordSymbols = j.flat.getElementsByClass(music21.harmony.ChordSymbol)
    newStream = music21.stream.Part()
    newStream.append(music21.clef.BassClef())
    for chordSymbol in onlyChordSymbols:
        newStream.append(realizePitches(chordSymbol))

    newStream = newStream.makeMeasures()
    nicePiece.insert(0,newStream)
    nicePiece.show()
    #NOTEFLIGHT SPECIFIC
    nicePiece = music21.converter.parse('C:\\Users\\bhadley\\Documents\\hack\\try11.xml')
    incorrectPiece = music21.converter.parse('C:\\Users\\bhadley\\Documents\\hack\\try11.xml')

    #incorrectPiece = music21.converter.parse('C:\Users\sample.xml')
    
    sopranoLine = nicePiece.getElementsByClass(music21.stream.PartStaff)[0]
    chordLine = nicePiece.getElementsByClass(music21.stream.Part)[1]
    #chordLine.show('text')
    #bassLine = nicePiece.part(2)
    s = music21.harmony.getDuration(sopranoLine)
    onlyChordSymbols = s.flat.getElementsByClass(music21.harmony.ChordSymbol)
    newStream = music21.stream.PartStaff()
    newStream.append(music21.clef.BassClef())
    answerKey = music21.stream.Score()
    answerKey.append(sopranoLine)
    for chordSymbol in onlyChordSymbols:
        newStream.append(realizePitches(chordSymbol))
    
    answerKey.insert(0,newStream)

    correctedAssignment, numCorrect = correctChordSymbols(answerKey, incorrectPiece)
    correctedAssignment.show('text')
    answerKey.show('text')

    correctedAssignment.show()
    answerKey.show()    
    print numCorrect
    
    
'''