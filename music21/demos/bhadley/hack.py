

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
        notationString =  '-'
    elif kind == 'dominant':
        notationString = '-7'
    elif kind == 'major-seventh':
        notationString = '7'
    elif kind == 'minor-seventh':
        notationString = '-7'
    elif kind == 'diminished-seventh':
        notationString = ''
    elif kind == 'augmented-seventh':
        notationString = ''
    elif kind == 'half-diminished':
        notationString = ''
    elif kind == 'major-minor':
        notationString = ''

    return notationString

    
def correctChordSymbols(music21piece1, music21piece2):  
    chords1 = music21piece1.flat.getElementsByClass(music21.chord.Chord)
    chords2 = music21piece2.flat.getElementsByClass(music21.chord.Chord)
    #1 is correct
    #2 is incorrect
    
    for chord1, chord2 in zip(chords1, chords2):
        newPitches = []
        for x in chord2.pitches:
            newPitches.append(str(x.name))
        for pitch in chord1:
            if not (pitch.name in newPitches):
                chord2.lyric = "WRONG"

    s = music21piece2.getElementsByClass(music21.stream.PartStaff)[1]
    s.insert(0, music21.clef.BassClef())
    newScore = music21.stream.Score()
    newScore.append(music21piece2.getElementsByClass(music21.stream.PartStaff)[0])
    newScore.append(s)
   
    return newScore #student's corrected score
    

def realizePitches(harmonyChordSymbolObject):
    x = harmonyChordSymbolObject
    print x.duration
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
       # print pitches
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

    nicePiece = music21.converter.parse('C:\Users\sample.xml')
    incorrectPiece = music21.converter.parse('C:\\Users\\bhadley\\Documents\\hack\incorrect.xml')
    
    sopranoLine = nicePiece.getElementsByClass(music21.stream.PartStaff)[0]
    s = music21.harmony.getDuration(sopranoLine)
    onlyChordSymbols = s.flat.getElementsByClass(music21.harmony.ChordSymbol)
    newStream = music21.stream.PartStaff()
    newStream.append(music21.clef.BassClef())
    answerKey = music21.stream.Score()
    answerKey.append(sopranoLine)
    for chordSymbol in onlyChordSymbols:
        newStream.append(realizePitches(chordSymbol))
    
    answerKey.insert(0,newStream)

    correctedAssignment = correctChordSymbols(answerKey, incorrectPiece)

    correctedAssignment.show('text')
    answerKey.show('text')
    answerKey.show()
    correctedAssignment.show()
    
    
'''Triads:
    major (major third, perfect fifth)
    minor (minor third, perfect fifth)
    augmented (major third, augmented fifth)
    diminished (minor third, diminished fifth)
Sevenths:
    dominant (major triad, minor seventh)
    major-seventh (major triad, major seventh)
    minor-seventh (minor triad, minor seventh)
    diminished-seventh (diminished triad, diminished seventh)
    augmented-seventh (augmented triad, minor seventh)
    half-diminished (diminished triad, minor seventh)
    major-minor (minor triad, major seventh)
Sixths:
    major-sixth (major triad, added sixth)
    minor-sixth (minor triad, added sixth)
Ninths:
    dominant-ninth (dominant-seventh, major ninth)
    major-ninth (major-seventh, major ninth)
    minor-ninth (minor-seventh, major ninth)
11ths (usually as the basis for alteration):
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
#maj chords = I; minor = ii; dom7 = V7; dim = vii; dim7 = viio7, etc
