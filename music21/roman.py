# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         roman.py
# Purpose:      music21 classes for doing Roman Numeral / Tonal analysis
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Music21 class for dealing with Roman Numeral analysis
'''

import doctest,unittest
import copy
import re
import music21
from music21 import chord
from music21 import common
from music21 import interval
from music21 import key
from music21 import pitch
from music21 import scale
from music21.figuredBass import notation as fbNotation
from music21 import harmony

from music21 import environment
_MOD = 'roman.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------

SHORTHAND_RE = re.compile('#*-*b*o*[1-9xyz]')
ENDWITHFLAT_RE = re.compile('[b\-]$')

# cache all Key/Scale objects created or passed in; re-use
# permits using internally scored pitch segments
_scaleCache = {}
_keyCache = {}


functionalityScores =  { 
    'I'  : 100,
    'i'  : 90,
    'V7' : 80,
    'V'  : 70,
    'V65' : 68,
    'I6' : 65,
    'V6' : 63,
    'V43' : 61,
    'I64' : 60,
    'IV' : 59,
    'i6' : 58,
    'viio7' : 57,
    'V42' : 55,
    'viio65' : 53,
    'viio6' : 52,
    '#viio65' : 51,
    'ii' : 50,
    '#viio6' : 49,
    'ii65' : 48,
    'ii43' : 47,
    'ii42' : 46,
    'IV6' : 45,
    'ii6' : 43,
    'VI' : 42,
    '#VI' : 41,
    'vi' : 40,
    '#viio' : 39,
    'iio' : 37, ## common in Minor
    'iio42' : 36,
    'bII6' : 35, ## Neapolitan
    'iio43' : 32,
    'iio65' : 31,
    '#vio' : 28,
    '#vio6' : 28,
    'III' : 22,
    'v'  : 20,
    'VII' : 19,
    'VII7' : 18,
    'IV65' : 17,
    'IV7' : 16,
    'iii' : 15,
    'iii6' : 12,
    'vi6' : 10,
  }




def romanNumeralFromChord(chordObj, keyObj = None, preferSecondaryDominants = False):
    '''
    takes a chord object and returns an appropriate chord name.  If keyObj is omitted,
    the root of the chord is considered the key (if the chord has a major third, it's major;
    otherwise it's minor).
    
    >>> from music21 import *
    >>> rn = roman.romanNumeralFromChord(chord.Chord(['E-3','C4','G-6']), key.Key('g#'))
    >>> rn
    <music21.roman.RomanNumeral bivo6 in g# minor>
    
    
    The pitches remain the same with the same octaves:
    
    >>> rn.pitches
    [E-3, C4, G-6]
    
    
    >>> rn2 = roman.romanNumeralFromChord(chord.Chord(['E3','C4','G4','B-4','E5','G5']), key.Key('F'))
    >>> rn2
    <music21.roman.RomanNumeral V65 in F major>


    Note that vi and vii in minor signifies what you might think of alternatively as #vi and #vii:
    
    >>> rn3 = roman.romanNumeralFromChord(chord.Chord(['A4','C5','E-5']), key.Key('c'))
    >>> rn3
    <music21.roman.RomanNumeral vio in c minor>
    >>> rn4 = roman.romanNumeralFromChord(chord.Chord(['A-4','C5','E-5']), key.Key('c'))
    >>> rn4
    <music21.roman.RomanNumeral bVI in c minor>
    >>> rn5 = roman.romanNumeralFromChord(chord.Chord(['B4','D5','F5']), key.Key('c'))
    >>> rn5
    <music21.roman.RomanNumeral viio in c minor>
    >>> rn6 = roman.romanNumeralFromChord(chord.Chord(['B-4','D5','F5']), key.Key('c'))
    >>> rn6
    <music21.roman.RomanNumeral bVII in c minor>

    For reference, odder notes:

    >>> rn7 = roman.romanNumeralFromChord(chord.Chord(['A--4','C-5','E--5']), key.Key('c'))
    >>> rn7
    <music21.roman.RomanNumeral bbVI in c minor>
    >>> rn8 = roman.romanNumeralFromChord(chord.Chord(['A#4','C#5','E#5']), key.Key('c'))
    >>> rn8
    <music21.roman.RomanNumeral #vi in c minor>

#    >>> rn9 = roman.romanNumeralFromChord(chord.Chord(['C4','E5','G5', 'C#6', 'C7', 'C#8']), key.Key('C'))
#    >>> rn9
#    <music21.roman.RomanNumeral I#853 in C major>
#
#    >>> rn10 = roman.romanNumeralFromChord(chord.Chord(['F#3', 'A3', 'E4', 'C5']), key.Key('d'))
#    >>> rn10
#    <music21.roman.RomanNumeral #iiio/7 in d minor>

    '''
    stepAdjustments = {'minor' : {3: -1, 6: -1, 7: -1},
                       'diminished' : {3: -1, 5: -1, 6: -1, 7: -2},
                       'half-diminished': {3: -1, 5: -1, 6: -1, 7: -1},
                       'augmented': {5: 1},
                       }
    chordObjSemiclosed = chordObj.semiClosedPosition(inPlace=False)
    root = chordObj.root()
    thirdType = chordObjSemiclosed.semitonesFromChordStep(3)
    if thirdType == 4:
        isMajorThird = True
    else:
        isMajorThird = False
    
    if isMajorThird is True:
        rootkeyObj = key.Key(root.name, mode='major')
    else:
        rootkeyObj = key.Key(root.name.lower(), mode='minor')

    if keyObj is None:
        keyObj = rootKeyObj

    fifthType = chordObjSemiclosed.semitonesFromChordStep(5)
    if fifthType == 6:
        fifthName = 'o'
    elif fifthType == 8:
        fifthName = '+'
    else:
        fifthName = ""

    (stepNumber, alter, rootAlterationString, discard) = figureTupletSolo(root, keyObj, keyObj.tonic)

    if keyObj.mode == 'minor' and stepNumber in [6, 7]:
        if alter == 1.0:
            alter = 0
            rootAlterationString = ''
        elif alter == 0.0:
            alter = 0 # NB! does not change!
            rootAlterationString = 'b'
        ## more exotic:
        elif alter > 1.0:
            alter = alter - 1
            rootAlterationString = rootAlterationString[1:]
        elif alter < 0.0:
            rootAlterationString = 'b' + rootAlterationString

    if alter == 0:
        alteredKeyObj = key.Key(keyObj.tonic, rootkeyObj.mode)
    else:
        ## altered scale degrees, such as #V require a different hypothetical tonic
        transposeInterval = interval.intervalFromGenericAndChromatic(
                interval.GenericInterval(1), 
                interval.ChromaticInterval(alter))
        alteredKeyObj = key.Key(transposeInterval.transposePitch(keyObj.tonic), rootkeyObj.mode)
    
    stepRoman = common.toRoman(stepNumber)
    if isMajorThird is True:
        pass
    elif isMajorThird is False:
        stepRoman = stepRoman.lower()
    inversionString = figureFromChordAndKey(chordObj, alteredKeyObj)
    if len(inversionString) > 0 and inversionString[0] == 'o':
        if fifthName == 'o':
            fifthName == ""
    #print (inversionString, fifthName)
    rnString = rootAlterationString + stepRoman + fifthName + inversionString
    try:
        rn = RomanNumeral(rnString, keyObj)
    except fbNotation.ModifierException as strerror:
        raise RomanNumeralException("Could not parse %s from chord %s as an RN in key %s: %s" % (rnString, chordObj, keyObj, strerror))
        
    rn.pitches = chordObj.pitches
    return rn

def figureTuplets(chordObj, keyObj):
    '''
    return a set of tuplets for each pitch
    showing the presence of a note, its interval above the bass
    its alteration (float) from a step in the given key, an alterationString,
    and the pitch object.

    Note though that for roman numerals, the applicable key is almost always
    the root.
    
    For instance, in C major, F# D A- C# would be:

    >>> from music21 import *
    >>> figureTuplets(chord.Chord(['F#2','D3','A-3','C#4']), key.Key('C'))
    [(1, 1.0, '#', F#2), (6, 0.0, '', D3), (3, -1.0, 'b', A-3), (5, 1.0, '#', C#4)]

    >>> figureTuplets(chord.Chord(['E3','C4','G4','B-5']), key.Key('C'))
    [(1, 0.0, '', E3), (6, 0.0, '', C4), (3, 0.0, '', G4), (5, -1.0, 'b', B-5)]
    '''
    retList = []
    bass = chordObj.bass()
    for thisPitch in chordObj.pitches:
        appendTuple = figureTupletSolo(thisPitch, keyObj, bass)
        retList.append(appendTuple)
    return retList

def figureTupletSolo(pitchObj, keyObj, bass):
    '''
    return a single tuplet for a pitch and key
    showing the interval above the bass,
    its alteration from a step in the given key, an
    alteration string, and the pitch object.
    
    For instance, in C major, an A-3 above an F# bass would be:

    >>> from music21 import *
    >>> figureTupletSolo(pitch.Pitch('A-3'), key.Key('C'), pitch.Pitch('F#2'))
    (3, -1.0, 'b', A-3)
    '''
    (scaleStep, scaleAccidental) = keyObj.getScaleDegreeAndAccidentalFromPitch(pitchObj)
    
    thisInterval = interval.notesToInterval(bass, pitchObj)
    aboveBass = thisInterval.diatonic.generic.mod7
    if scaleAccidental is None:
        rootAlterationString = ""
        alterDiff = 0.0
    else:
        alterDiff = scaleAccidental.alter
        alter = int(alterDiff)
        if alter < 0:
            rootAlterationString = "b" * (-1*alter)
        elif alter > 0:
            rootAlterationString = "#" * alter
        else:
            rootAlterationString = ""

    appendTuple = (aboveBass, alterDiff, rootAlterationString, pitchObj)
    return appendTuple

figureShorthands = {'53': '',
                    '3': '',
                    '63': '6',
                    '753': '7',
                    '653': '65',
                    '6b53': '6b5',
                    '643': '43',
                    '642': '42',
                    'bb7b5b3': 'o7',
                    'bb7b53': 'o7',
#                    '6b5bb3': 'o65',
                    'b7b5b3': 'o/7',
                    }

def figureFromChordAndKey(chordObj, keyObj=None):
    '''
    returns the post RN figure for a given chord in a given key.
    if keyObj is none, it uses the root as a major key
    
    >>> from music21 import *
    >>> figureFromChordAndKey(chord.Chord(['F#2','D3','A-3','C#4']), key.Key('C'))
    '6#5b3'

    The method substitutes shorthand (e.g., '6' not '63')

    >>> figureFromChordAndKey(chord.Chord(['E3','C4','G4']), key.Key('C'))
    '6'

    >>> figureFromChordAndKey(chord.Chord(['E3','C4','G4','B-5']), key.Key('F'))
    '65'
    >>> figureFromChordAndKey(chord.Chord(['E3','C4','G4','B-5']), key.Key('C'))
    '6b5'

    '''
    if keyObj is None:
        keyObj = key.Key(chordObj.root())
    chordFigureTuplets = figureTuplets(chordObj, keyObj)
    rootFigureAlter = chordFigureTuplets[0][1]

    allFigureStringList = []

    third = chordObj.third
    fifth = chordObj.fifth
    seventh = chordObj.seventh
    for figureTuplet in sorted(chordFigureTuplets, key=lambda tuple: tuple[0], reverse=True):
        (diatonicIntervalNum, alter, alterStr, pitchObj) = figureTuplet
        if diatonicIntervalNum != 1 and pitchObj is third:
            if chordObj.isMajorTriad() or chordObj.isMinorTriad():
                alterStr = '' #alterStr[1:]
            elif chordObj.isMinorTriad() is True and alter > 0:
                alterStr = '' #alterStr[1:]
        elif diatonicIntervalNum != 1 and pitchObj is fifth:
            if chordObj.isDiminishedTriad() or chordObj.isAugmentedTriad() or \
                chordObj.isMajorTriad() or chordObj.isMinorTriad():
                alterStr = ''#alterStr[1:]
        
        
        if diatonicIntervalNum == 1:
            if alter != rootFigureAlter and alterStr != '':
                pass
#                diatonicIntervalNum = 8 # mark altered octaves as 8 not 1
#                figureString = alterStr + str(diatonicIntervalNum)
#                if figureString not in allFigureStringList:
                    # filter duplicates and put at beginning
#                    allFigureStringList.insert(0, figureString)
        else:
            figureString = alterStr + str(diatonicIntervalNum)
            # filter out duplicates...
            if figureString not in allFigureStringList:
                allFigureStringList.append(figureString)

    allFigureString = ''.join(allFigureStringList)
    if allFigureString in figureShorthands:
        allFigureString = figureShorthands[allFigureString]
    return allFigureString

    
    
def expandShortHand(shorthand):
    '''
    expands shorthand notation into a list with all figures expanded
    
    >>> from music21.roman import expandShortHand
    >>> expandShortHand("64")
    ['6', '4']
    >>> expandShortHand("973")
    ['9', '7', '3']
    >>> expandShortHand("11b3")
    ['11', 'b3']
    >>> expandShortHand("b13#9-6")
    ['b13', '#9', '-6']
    >>> expandShortHand("-")
    ['5', '-3']
    >>> expandShortHand("6/4")
    ['6', '4']
    '''
    shorthand = shorthand.replace('/', '')
    if ENDWITHFLAT_RE.match(shorthand):
        shorthand += "3"
    shorthand = re.sub('11', 'x', shorthand)
    shorthand = re.sub('13', 'y', shorthand)
    shorthand = re.sub('15', 'z', shorthand)
    shorthandGroups = SHORTHAND_RE.findall(shorthand)
    if len(shorthandGroups) == 1 and shorthandGroups[0].endswith('3'):
        shorthandGroups = ['5', shorthandGroups[0]]
    
    shGroupOut = []
    for sh in shorthandGroups:
        sh = re.sub('x', '11', sh)
        sh = re.sub('y', '13', sh)
        sh = re.sub('z', '15', sh)
        shGroupOut.append(sh)
    return shGroupOut
        

#-------------------------------------------------------------------------------
class RomanException(music21.Music21Exception):
    pass

class RomanNumeralException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class RomanNumeral(harmony.Harmony):
    '''
    A RomanNumeral object is a specialized type of :class:`~music21.harmony.Harmony` object
    that stores the function and scale degree of a chord within a 
    :class:`~music21.key.Key` (if no Key is given then it exists as a theoretical, keyless
    RomanNumeral; e.g., V in any key. but when realized, keyless RomanNumerals are
    treated as if they are in C major).
    
    
    >>> from music21 import *
    >>> V = roman.RomanNumeral('V') # could also use 5
    >>> V.quality   # TODO: document better! what is inherited from Chord and what is new here...
    'major'
    >>> V.inversion()
    0
    >>> V.forteClass
    '3-11B'
    >>> V.scaleDegree
    5
    >>> V.pitches  # default key-- C Major
    [G4, B4, D5]
    
    
    >>> neapolitan = roman.RomanNumeral('N6', 'c#') # could also use "bII6"
    >>> neapolitan.key
    <music21.key.Key of c# minor>

    >>> neapolitan.isMajorTriad()
    True
    >>> neapolitan.scaleDegreeWithAlteration
    (2, <accidental flat>)
    >>> neapolitan.pitches  # default octaves
    [F#4, A4, D5]

    >>> neapolitan2 = roman.RomanNumeral('bII6', 'g#') 
    >>> neapolitan2.pitches
    [C#5, E5, A5]
    >>> neapolitan2.scaleDegree
    2
   
    >>> em = key.Key('e')
    >>> dominantV = roman.RomanNumeral('V7', em)
    >>> dominantV.pitches
    [B4, D#5, F#5, A5]
    
    >>> minorV = roman.RomanNumeral('V43', em, caseMatters = False) 
    >>> minorV.pitches
    [F#4, A4, B4, D5]


    >>> majorFlatSeven = roman.RomanNumeral('VII', em)
    >>> majorFlatSeven.pitches
    [D5, F#5, A5]
    >>> diminishedSharpSeven = roman.RomanNumeral('vii', em)
    >>> diminishedSharpSeven.pitches
    [D#5, F#5, A5]
    >>> majorFlatSix = roman.RomanNumeral('VI', em)
    >>> majorFlatSix.pitches
    [C5, E5, G5]
    >>> minorSharpSix = roman.RomanNumeral('vi', em)
    >>> minorSharpSix.pitches
    [C#5, E5, G#5]


    Either of these is the same way of getting a minor iii in a minor key:



    >>> minoriii = roman.RomanNumeral('iii', em, caseMatters = True)
    >>> minoriii.pitches
    [G4, B-4, D5]

    >>> minoriiiB = roman.RomanNumeral('IIIb', em, caseMatters = False)
    >>> minoriiiB.pitches
    [G4, B-4, D5]
    
   
    Can also take a scale object, here we build a first-inversion chord
    on the raised-three degree of D-flat major, that is, F#-major (late
    Schubert would be proud...)
    
    
    >>> sharp3 = roman.RomanNumeral('#III6', scale.MajorScale('D-'))
    >>> sharp3.scaleDegreeWithAlteration
    (3, <accidental sharp>)
    >>> sharp3.pitches
    [A#4, C#5, F#5]
    >>> sharp3.figure
    '#III6'
    
    Figures can be changed
    
    >>> sharp3.figure = "V"
    >>> sharp3.pitches
    [A-4, C5, E-5]
    

   
   
    >>> leadingToneSeventh = roman.RomanNumeral('viio', scale.MajorScale('F'))
    >>> leadingToneSeventh.pitches
    [E5, G5, B-5]
    
    A little modal mixture:
    
    >>> lessObviousDiminished = roman.RomanNumeral('vio', scale.MajorScale('c'))
    >>> lessObviousDiminished.pitches
    [A4, C5, E-5]

    >>> diminished7th = roman.RomanNumeral('vio7', scale.MajorScale('c'))
    >>> diminished7th.pitches
    [A4, C5, E-5, G-5]
    
    >>> diminished7th1stInv = roman.RomanNumeral('vio65', scale.MajorScale('c'))
    >>> diminished7th1stInv.pitches
    [C4, E-4, G-4, A4]
    
    >>> halfDim7th2ndInv = roman.RomanNumeral('iv/o43', scale.MajorScale('F'))
    >>> halfDim7th2ndInv.pitches
    [F-4, A-4, B-4, D-5]

    >>> alteredChordHalfDim3rdInv = roman.RomanNumeral('bii/o42', scale.MajorScale('F'))
    >>> alteredChordHalfDim3rdInv.pitches
    [F-4, G-4, B--4, D--5]
    >>> alteredChordHalfDim3rdInv.intervalVector
    [0, 1, 2, 1, 1, 1]
    >>> alteredChordHalfDim3rdInv.commonName
    'half-diminished seventh chord'
    >>> alteredChordHalfDim3rdInv.romanNumeral
    '-ii'
    >>> alteredChordHalfDim3rdInv.romanNumeralAlone
    'ii'

    >>> openFifth = roman.RomanNumeral('V[no3]', key.Key('F'))
    >>> openFifth.pitches
    [C5, G5]

    
    Some theoretical traditions express a viio7 as a V9 chord with omitted root.  Music21 allows that:


    >>> fiveOhNine = roman.RomanNumeral('V9[no1]', key.Key('g'))
    >>> fiveOhNine.pitches
    [F#5, A5, C6, E-6]


    
    Just for kicks (no worries if this is goobley-gook):
    
    
    
    >>> ots = scale.OctatonicScale("C2")
    >>> rn = roman.RomanNumeral('I9', ots, caseMatters=False)
    >>> rn.pitches
    [C2, E-2, G-2, A2, C3]
    >>> rn2 = roman.RomanNumeral('V7#5b3', ots, caseMatters = False)
    >>> rn2.pitches
    [G-2, A-2, C#3, E-3] 
    
    >>> r = roman.RomanNumeral('v64/V', key.Key('e'))
    >>> r
    <music21.roman.RomanNumeral v64/V in e minor>

    >>> r.figure
    'v64/V'
    >>> r.pitches
    [C#5, F#5, A5]
    >>> r.secondaryRomanNumeral
    <music21.roman.RomanNumeral V in e minor>


    Dominant 7ths can be specified by putting d7 at end:

    >>> r = roman.RomanNumeral('bVIId7', key.Key('B-'))
    >>> r.figure
    'bVIId7'
    >>> r.pitches
    [A-5, C6, E-6, G-6]
    >>> r = roman.RomanNumeral('VId7')
    >>> r.figure
    'VId7'
    >>> r.key = key.Key('B-')
    >>> r.pitches
    [G5, B5, D6, F6]



    >>> r2 = roman.RomanNumeral('V42/V7/vi', key.Key('C'))
    >>> r2.pitches
    [A4, B4, D#5, F#5]

    
    OMIT_FROM_DOCS
    Things that were giving us trouble
    >>> dminor = key.Key('d')
    >>> rn = roman.RomanNumeral('ii/o65', dminor)
    >>> rn.pitches
    [G4, B-4, D5, E5]
    >>> rn.romanNumeral
    'ii'
    
    >>> rn3 = roman.RomanNumeral('III', dminor)
    >>> rn3.pitches
    [F4, A4, C5]


    Should be the same as above no matter when the key is set:
    
    >>> r = roman.RomanNumeral('VId7', key.Key('B-'))
    >>> r.pitches
    [G5, B5, D6, F6]
    >>> r.key = key.Key('B-')
    >>> r.pitches
    [G5, B5, D6, F6]
    

    This was getting B-flat.

    >>> r = roman.RomanNumeral('VId7')
    >>> r.key = key.Key('B-')
    >>> r.pitches
    [G5, B5, D6, F6]
    '''

    frontFlat = re.compile('^(b+)')
    frontFlatAlt = re.compile('^(\-+)')
    frontSharp = re.compile('^(\#+)')
    romanNumerals = re.compile('(i?v?i*)', re.IGNORECASE)
    secondarySlash = re.compile('(.*?)\/([\#a-np-zA-NP-Z].*)')
    omitNotes = re.compile('\[no([1-9])no([1-9])\]')
    omitNote = re.compile('\[no([1-9])\]')
    
    def __init__(self, figure=None, keyOrScale=None, caseMatters = True):
        

        self.primaryFigure = None
        self.secondaryRomanNumeral = None
        self.secondaryRomanNumeralKey = None

        self.caseMatters = caseMatters
        self.scaleCardinality = 7
        
        if isinstance(figure, int):
            self.caseMatters = False
            figure = common.toRoman(figure)

         # store raw figure before calling setKeyOrScale
        self._figure = figure            
        self._scale = None # this is set when _setKeyOrScale() is called
        self.impliedScale = None
        self.useImpliedScale = False
        
        self._parsingComplete = False
        
        self._setKeyOrScale(keyOrScale)
        harmony.Harmony.__init__(self, figure)
        
        self._parsingComplete = True
        self._functionalityScore = None
        
    def __repr__(self):
        if hasattr(self.key, 'tonic'):
            return '<music21.roman.RomanNumeral %s>' % (self.figureAndKey)
        else:
            return '<music21.roman.RomanNumeral %s>' % (self.figure)

    def _updatePitches(self):
        '''
        utility function to update the pitches to the new figure etc.
        '''
        if self.secondaryRomanNumeralKey  is not None:
            useScale = self.secondaryRomanNumeralKey 
        elif self.useImpliedScale is False:
            useScale = self._scale
        else:
            useScale = self.impliedScale
        
        #self.scaleCardinality = len(useScale.pitches) - 1 # should be 7 but hey, octatonic scales, etc.
        self.scaleCardinality = useScale.getDegreeMaxUnique()

        bassScaleDegree = self.bassScaleDegreeFromNotation( 
                            self.figuresNotationObj)
        bassPitch = useScale.pitchFromDegree(bassScaleDegree, 
                    direction = scale.DIRECTION_ASCENDING)
        pitches = [bassPitch]
        lastPitch = bassPitch
        numberNotes = len(self.figuresNotationObj.numbers)
        
        for j in range(numberNotes):
            i = numberNotes - j - 1
            thisSD = bassScaleDegree + self.figuresNotationObj.numbers[i] - 1
            newPitch = useScale.pitchFromDegree(thisSD, 
                        direction = scale.DIRECTION_ASCENDING)
            pitchName = self.figuresNotationObj.modifiers[i].modifyPitchName(newPitch.name)
            newnewPitch = pitch.Pitch(pitchName + str(newPitch.octave))
            #if newnewPitch.midi < lastPitch.midi:
            # better to compare pitch space, as midi has limits and rounding
            if newnewPitch.ps < lastPitch.ps:
                newnewPitch.octave += 1
            pitches.append(newnewPitch)
            lastPitch = newnewPitch

        if self.frontAlterationTransposeInterval:
            newPitches = []
            for thisPitch in pitches:
                newPitch = thisPitch.transpose(self.frontAlterationTransposeInterval)
                newPitches.append(newPitch)
            self.pitches = newPitches
        else:
            self.pitches = pitches
        
        self._matchAccidentalsToQuality(self.impliedQuality)
                
        self.scaleOffset = self.frontAlterationTransposeInterval
        
        if self.omittedSteps:
            omittedPitches = []
            for thisCS in self.omittedSteps:
                # getChordStep may return False
                p = self.getChordStep(thisCS)
                if p not in [False, None]:
                    omittedPitches.append(p.name)
            newPitches = []
            for thisPitch in pitches:
                if thisPitch.name not in omittedPitches:
                    newPitches.append(thisPitch)
            self.pitches = newPitches

        if len(self.pitches) == 0:
            raise RomanNumeralException('_updatePitches() was unable to derive pitches from the figure: %s' % self.figure)

    def _parseFigure(self):
        '''
        parse the .figure object in its component parts
        '''
        if not common.isStr(self._figure):
            raise RomanException('got a non-string figure: %r', self._figure)

        if self.useImpliedScale is False:
            useScale = self._scale
        else:
            useScale = self.impliedScale

        hasSecondary = self.secondarySlash.match(self._figure)
        
        if hasSecondary:
            primaryFigure = hasSecondary.group(1)
            secondaryFigure = hasSecondary.group(2)
            secRoman = RomanNumeral(secondaryFigure, useScale, self.caseMatters)
            self.secondaryRomanNumeral = secRoman
            if secRoman.quality == 'minor':
                secondaryMode = 'minor'
            elif secRoman.quality == 'major':
                secondaryMode = 'major'
            elif secRoman.semitonesFromChordStep(3) == 3:
                secondaryMode = 'minor'
            else:
                secondaryMode = 'major'
            self.secondaryRomanNumeralKey  = key.Key(secRoman.root().name, secondaryMode)
            useScale = self.secondaryRomanNumeralKey 
            workingFigure = primaryFigure
            self.primaryFigure = primaryFigure
        else:
            workingFigure = self._figure
            self.primaryFigure = workingFigure 

        ## TODO -- make a while...
        omit = self.omitNotes.search(workingFigure)
        if omit:
            omit = [int(omit.group(1)), int(omit.group(2))]
            workingFigure = self.omitNotes.sub('', workingFigure)
        else:
            omit = self.omitNote.search(workingFigure)
            if omit:
                omit = [int(omit.group(1))]
                workingFigure = self.omitNote.sub('', workingFigure)
            else:
                omit = []
        
        self.omittedSteps = omit
        
        flatAlteration = 0
        sharpAlteration = 0
        workingFigure = re.sub('^N', 'bII', workingFigure)
        
        frontAlterationString = "" # the b in bVI, or the # in #vii
        if self.frontFlat.match(workingFigure):
            fm = self.frontFlat.match(workingFigure)
            flatAlteration = len(fm.group(1))
            transposeInterval = interval.intervalFromGenericAndChromatic(
                interval.GenericInterval(1), 
                interval.ChromaticInterval(-1 * flatAlteration))
            scaleAlter = pitch.Accidental(-1 * flatAlteration)
            workingFigure = self.frontFlat.sub('', workingFigure)
            frontAlterationString = fm.group(0)
        elif self.frontFlatAlt.match(workingFigure):
            fm = self.frontFlatAlt.match(workingFigure)
            flatAlteration = len(fm.group(1))
            transposeInterval = interval.intervalFromGenericAndChromatic(
                interval.GenericInterval(1), interval.ChromaticInterval(-1 * flatAlteration))
            scaleAlter = pitch.Accidental(-1 * flatAlteration)
            workingFigure = self.frontFlatAlt.sub('', workingFigure)
            frontAlterationString = fm.group(0)
        elif self.frontSharp.match(workingFigure):
            sm = self.frontSharp.match(workingFigure)
            sharpAlteration = len(sm.group(1))
            transposeInterval = interval.intervalFromGenericAndChromatic(
                interval.GenericInterval(1), interval.ChromaticInterval(1 * sharpAlteration))
            scaleAlter = pitch.Accidental(sharpAlteration)
            workingFigure = self.frontSharp.sub('', workingFigure)
            frontAlterationString = sm.group(0)
        else: 
            transposeInterval = None
            scaleAlter = None
       
        self.frontAlterationString = frontAlterationString
        self.frontAlterationTransposeInterval = transposeInterval
        self.frontAlterationAccidental = scaleAlter
        romanNumeralAlone = ""
        if not self.romanNumerals.match(workingFigure):
            raise RomanException("No roman numeral found in %s " % (workingFigure))
        else:
            rm = self.romanNumerals.match(workingFigure)
            romanNumeralAlone = rm.group(1)
            self.scaleDegree = common.fromRoman(romanNumeralAlone)
            workingFigure = self.romanNumerals.sub('', workingFigure)
            self.romanNumeralAlone = romanNumeralAlone
 
        workingFigure = self._setImpliedQualityFromString(workingFigure)
    
        # make vii always #vii and vi always #vi
        if self.frontAlterationString == "" and hasattr(useScale, 'mode') and \
             useScale.mode == 'minor' and self.caseMatters == True:
            if self.scaleDegree == 6 and self.impliedQuality == 'minor':
                self.frontAlterationTransposeInterval = interval.Interval('A1')
                self.frontAlterationAccidental = pitch.Accidental(1)
            elif self.scaleDegree == 7 and \
                  (self.impliedQuality == 'minor' or self.impliedQuality =='diminished' or self.impliedQuality == 'half-diminished'):
                self.frontAlterationTransposeInterval = interval.Interval('A1')
                self.frontAlterationAccidental = pitch.Accidental(1)
                if self.impliedQuality == 'minor':
                    self.impliedQuality = 'diminished'

        self.figuresWritten = workingFigure        
        shfig = ','.join(expandShortHand(workingFigure))
        self.figuresNotationObj = fbNotation.Notation(shfig)


    def _setImpliedQualityFromString(self, workingFigure):
        impliedQuality = '' # major, minor, augmented, or diminished (and half-diminished for 7ths)
        impliedQualitySymbol = ''
        if workingFigure.startswith('o'):
            workingFigure = workingFigure[1:]
            impliedQuality = 'diminished'
            impliedQualitySymbol = 'o'
        elif workingFigure.startswith('/o'):
            workingFigure = workingFigure[2:]
            impliedQuality = 'half-diminished'
            impliedQualitySymbol = '/o'
        elif workingFigure.startswith('+'):
            workingFigure = workingFigure[1:]
            impliedQuality = 'augmented'
            impliedQualitySymbol = '+'
        elif workingFigure.endswith('d7'):
            ## this one is different
            workingFigure = workingFigure[:-2] + '7'
            impliedQuality = 'dominant-seventh'
            impliedQualitySymbol = '(dom7)'        
        elif self.caseMatters and \
               self.romanNumeralAlone.upper() == self.romanNumeralAlone:
            impliedQuality = 'major'
        elif self.caseMatters and \
               self.romanNumeralAlone.lower() == self.romanNumeralAlone:
            impliedQuality = 'minor'
        self.impliedQuality = impliedQuality
        return workingFigure


    def _matchAccidentalsToQuality(self, impliedQuality):
        '''
        fixes notes that should be out of the scale
        based on what the chord "impliedQuality" (major, minor, augmented, diminished)
        
        an intermediary step in parsing figures
        
        '''        
        chordStepsToExamine = (3,5,7)
        if impliedQuality == 'major':
            correctSemitones = (4, 7)
        elif impliedQuality == 'minor':
            correctSemitones = (3, 7)
        elif impliedQuality == 'diminished':
            if len(self.pitches) == 2:
                correctSemitones = (3, 6)
            elif len(self.pitches) > 2:
                correctSemitones = (3, 6, 9)
        elif impliedQuality == 'half-diminished':
            correctSemitones = (3, 6, 10)
        elif impliedQuality == 'augmented':
            correctSemitones = (4, 8)
        elif impliedQuality == 'dominant-seventh':
            correctSemitones = (4, 7, 10)
        else:
            return

        newPitches = []
        for i in range(len(correctSemitones)): # 3,5,7
            thisChordStep = chordStepsToExamine[i]
            thisCorrect = correctSemitones[i]
            thisSemis = self.semitonesFromChordStep(thisChordStep)
            if thisSemis is None:
                continue
            if thisSemis != thisCorrect:
                faultyPitch = self.getChordStep(thisChordStep)
                if faultyPitch == None:
                    raise RomanException("this is very odd...")
                if faultyPitch.accidental == None:
                    faultyPitch.accidental = pitch.Accidental(thisCorrect - thisSemis)
                else:
                    acc = faultyPitch.accidental
                    acc.set(thisCorrect - thisSemis + acc.alter)

    ### changeable stuff...
    def _getRomanNumeral(self):
        '''
        read-only property that returns either the romanNumeralAlone (e.g. just II)
        or the frontAlterationAccidental.modifier + romanNumeralAlone (e.g. #II)
        
        >>> from music21 import *
        >>> rn = roman.RomanNumeral("#II7")
        >>> rn.romanNumeral
        '#II'
        '''
        if self.frontAlterationAccidental is None:
            return self.romanNumeralAlone
        else:
            return self.frontAlterationAccidental.modifier + self.romanNumeralAlone

    romanNumeral = property(_getRomanNumeral)


    def _getFigure(self):
        return self._figure
    
    def _setFigure(self, newFigure):
        self._figure = newFigure
        if self._parsingComplete is True:
            self._parseFigure()
            self._updatePitches()

    figure = property(_getFigure, _setFigure, doc='''
        gets or sets the entire figure (the whole enchilada)
        ''')

    def _getFigureAndKey(self):
        '''
        returns the figure and the key and mode as a string
        
        >>> from music21 import *
        >>> rn = roman.RomanNumeral('V65/V', 'e')
        >>> rn.figureAndKey
        'V65/V in e minor'
        
        '''
        tonic = self.key.tonic
        if hasattr(tonic, 'name'):
            tonic = tonic.name
        mode = ""
        if hasattr(self.key, 'mode'):
            mode = " " + self.key.mode
        elif self.key.__class__.__name__ == 'MajorScale':
            mode = ' major'
        elif self.key.__class__.__name__ == 'MinorScale':
            mode = ' minor'
        else:
            pass
        if mode == ' minor':
            tonic = tonic.lower()
        elif mode == ' major':
            tonic = tonic.upper()
        return '%s in %s%s' % (self.figure, tonic, mode)

    figureAndKey = property(_getFigureAndKey)

    def _getKeyOrScale(self):
        return self._scale

    def _setKeyOrScale(self, keyOrScale):
        '''Provide a new key or scale, and re-configure the RN with the existing figure.         
        '''
        # try to get Scale or Key object from cache: this will offer
        # performance boost as Scale stores cached pitch segments
        if common.isStr(keyOrScale):
            if keyOrScale in _keyCache.keys():
                keyOrScale = _keyCache[keyOrScale]
            else:
                keyOrScale = key.Key(keyOrScale)
                _keyCache[keyOrScale] = keyOrScale
        elif keyOrScale is not None:
            #environLocal.printDebug(['got keyOrScale', keyOrScale])
            try:
                keyClasses = keyOrScale.classes
            except:
                raise RomanNumeralException("Cannot call classes on object %s, send only Key or Scale Music21Objects" % keyOrScale)

            if 'Key' in keyClasses:
                if keyOrScale.name in _keyCache.keys():
                    # use stored scale as already has cache
                    keyOrScale = _keyCache[keyOrScale.name]
                else:
                    _keyCache[keyOrScale.name] = keyOrScale
            elif 'Scale' in keyClasses:      
                if keyOrScale.name in _scaleCache.keys():
                    # use stored scale as already has cache
                    keyOrScale = _scaleCache[keyOrScale.name]
                else:
                    _scaleCache[keyOrScale.name] = keyOrScale
            else:
                raise RomanNumeralException("Cannot get a key from this object %s, send only Key or Scale objects" % keyOrScale)
        else:
            pass
            # cache object if passed directly

        self._scale = keyOrScale
        if keyOrScale is None or (hasattr(keyOrScale, "isConcrete") and 
            keyOrScale.isConcrete == False):
            self.useImpliedScale = True
            if self._scale != None:
                self.impliedScale = self._scale.derive(1, 'C')
            else:
                self.impliedScale = scale.MajorScale('C')
        else:
            self.useImpliedScale = False        
        # need to permit object creation with no arguments, thus
        # self._figure can be None
        if self._parsingComplete == True:
            self._updatePitches()
        #environLocal.printDebug(['Roman.setKeyOrScale:', 'called w/ scale', self.key, 'figure', self.figure, 'pitches', self.pitches])

    key = property(_getKeyOrScale, _setKeyOrScale, doc='''
    
        Gets or Sets the current Key (or Scale object) for a given RomanNumeral object.
        If a new key is set, then the pitches will probably change
        
        >>> from music21 import *
        >>> r1 = RomanNumeral('V')
        >>> r1.pitches
        [G4, B4, D5]
        >>> r1.key = key.Key('A')
        >>> r1.pitches
        [E5, G#5, B5]
        >>> r1
        <music21.roman.RomanNumeral V in A major>
        >>> r1.key
        <music21.key.Key of A major>
        
        
        >>> r1.key = key.Key('e')
        >>> r1.pitches
        [B4, D#5, F#5]
        >>> r1
        <music21.roman.RomanNumeral V in e minor>
        ''')
        
#
#    def nextInversion(self):
#        '''Invert the harmony one position, or place the next member after the current bass as the bass
#
#        >>> from music21 import *
#        >>> sc1 = scale.MajorScale('g4')
#        >>> h1 = scale.RomanNumeral(sc1, 5)
#        >>> h1.getPitches()
#        [D5, F#5, A5]
#        >>> h1.nextInversion()
#        >>> h1._bassMemberIndex
#        1
#        >>> h1.getPitches()
#        [F#5, A5, D6]
#
#        '''
#        self._bassMemberIndex = (self._bassMemberIndex + 1) % len(self._members)
#        

    def _getScaleDegreeWithAlteration(self):
        return (self.scaleDegree, self.frontAlterationAccidental)
    def _setScaleDegreeWithAlteration(self, scaleDegree, alteration):
        self.scaleDegree = scaleDegree
        self.frontAlterationAccidental = alteration
        if self._parsingComplete is True:
            self._updatePitches()
    
    scaleDegreeWithAlteration = property(_getScaleDegreeWithAlteration, _setScaleDegreeWithAlteration, doc='''
        returns or sets a two element tuple of the scale degree and the accidental that
        alters the scale degree for things such as #ii or bV.
        
        Note that vi and vii in minor have a frontAlterationAccidental of <sharp> even if it
        is not preceded by a # sign.
        
        Has the same effect as setting .scaleDegree and .frontAlterationAccidental separately
        ''')
    
    def bassScaleDegreeFromNotation(self, notationObject):
        '''
        given a notationObject from :class:`music21.figuredBass.notation.Notation`
        return the scaleDegree of the bass.
        
        >>> from music21 import *
        >>> fbn = figuredBass.notation.Notation('6,3')
        >>> V = roman.RomanNumeral('V')
        >>> V.bassScaleDegreeFromNotation(fbn)
        7
        >>> fbn2 = figuredBass.notation.Notation('#6,4')
        >>> vi = roman.RomanNumeral('vi')
        >>> vi.bassScaleDegreeFromNotation(fbn2)
        3
        '''
        c = pitch.Pitch("C3")
        cDNN = c.diatonicNoteNum
        pitches = [c]
        for i in notationObject.numbers:
            distanceToMove = i-1
            newDiatonicNumber = (cDNN + distanceToMove)

            newStep, newOctave = interval.convertDiatonicNumberToStep(newDiatonicNumber)
            newPitch = pitch.Pitch("C3")
            newPitch.step = newStep
            newPitch.octave = newOctave
            pitches.append(newPitch)
            
        tempChord = chord.Chord(pitches)
        rootDNN = tempChord.root().diatonicNoteNum
        staffDistanceFromBassToRoot = rootDNN - cDNN
        bassSD = (self.scaleDegree - staffDistanceFromBassToRoot) % self.scaleCardinality
        if bassSD == 0:
            bassSD = 7
        return bassSD

    def _getFunctionalityScore(self):
        if self._functionalityScore is not None:
            return self._functionalityScore
        try:
            score = functionalityScores[self.figure]
        except KeyError:
            score = 0
        return score
    
    def _setFunctionalityScore(self, value):
        self._functionalityScore = value
    
    functionalityScore = property(_getFunctionalityScore, _setFunctionalityScore, doc='''
        Return or set a number from 1 to 100 representing the relative functionality of this RN.figure
        (possibly given the mode, etc.)
        
        Numbers are ordinal not cardinal.

        >>> from music21 import *
        >>> rn1 = roman.RomanNumeral('V7')
        >>> rn1.functionalityScore
        80
        
        >>> rn2 = roman.RomanNumeral('vi6')
        >>> rn2.functionalityScore
        10
        
        >>> rn2.functionalityScore = 99
        >>> rn2.functionalityScore
        99
        ''')

def identifyAsTonicOrDominant(inChord, inKey):
    '''
    returns the roman numeral string expression (either tonic or dominant) that best matches the inChord.
    Useful when you know inChord is either tonic or dominant, but only two pitches are provided in the chord.
    If neither tonic nor dominant is possibly correct, False is returned
    
    >>> from music21 import *
    >>> roman.identifyAsTonicOrDominant(['B2','F5'], key.Key('C'))
    'V65'
    >>> roman.identifyAsTonicOrDominant(['B3','G4'], key.Key('g'))
    'i6'
    >>> roman.identifyAsTonicOrDominant(['C3', 'B4'], key.Key('f'))
    'V7'
    >>> roman.identifyAsTonicOrDominant(['D3'], key.Key('f'))
    False
    '''
    if isinstance(inChord, list):
        inChord = chord.Chord(inChord)
    pitchNameList = []
    for x in inChord.pitches:
        pitchNameList.append(x.name)
    oneRoot =  inKey.pitchFromDegree(1)
    fiveRoot = inKey.pitchFromDegree(5)
    oneChordIdentified = False
    fiveChordIdentified = False
    if oneRoot.name in pitchNameList:
        oneChordIdentified = True
    elif fiveRoot.name in pitchNameList:
        fiveChordIdentified = True
    else:
        oneRomanChord = RomanNumeral('I7', inKey).pitches
        fiveRomanChord = RomanNumeral('V7', inKey).pitches
        
        onePitchNameList = []
        for x in oneRomanChord:
            onePitchNameList.append(x.name)
        
        fivePitchNameList = []
        for x in fiveRomanChord:
            fivePitchNameList.append(x.name)                    
        
        oneMatches = len(set(onePitchNameList) & set(pitchNameList))
        fiveMatches = len(set(fivePitchNameList) & set(pitchNameList))
        if  oneMatches > fiveMatches and oneMatches > 0:
            oneChordIdentified = True
        elif oneMatches < fiveMatches and fiveMatches > 0:
            fiveChordIdentified = True
        else:
            return False
        
    if oneChordIdentified:
        rootScaleDeg = common.toRoman(1)
        if inKey.mode == 'minor':
            rootScaleDeg = rootScaleDeg.lower()
        else:
            rootScaleDeg = rootScaleDeg.upper()
        inChord.root(oneRoot)
    elif fiveChordIdentified:
        rootScaleDeg = common.toRoman(5)
        inChord.root(fiveRoot)
    else:
        return False

    return rootScaleDeg + _romanInversionName(inChord)
    
def _romanInversionName(inChord):
    '''
    method is extremely similar to Chord's inversionName() method, but returns string values
    and allows incomplete triads
    '''
    inv = inChord.inversion()
    if inChord.isSeventh() or inChord.seventh is not None:
        if inv == 0:
            return '7'
        elif inv == 1:
            return '65'
        elif inv == 2:
            return '43'
        elif inv == 3:
            return '42'
        else:
            return ''
    elif inChord.isTriad() or inChord.isIncompleteMajorTriad() or inChord.isIncompleteMinorTriad():
        if inv == 0:
            return '' #not 53
        elif inv == 1:
            return '6'
        elif inv == 2:
            return '64'
        else:
            return ''
    else:
        return ''



class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)

    def testFBN(self):
        fbn = fbNotation.Notation('6,3')
        V = RomanNumeral('V')
        sdb = V.bassScaleDegreeFromNotation(fbn)
        self.assertEqual(sdb, 7)

    def testFigure(self):
        from music21 import scale
        
        r1 = RomanNumeral('V')
        self.assertEqual(r1.scaleOffset, None)
        self.assertEqual(r1.pitches, chord.Chord(["G4","B4","D5"]).pitches)
        
        r1 = RomanNumeral('bbVI6')
        self.assertEqual(r1.figuresWritten, "6")
        self.assertEqual(r1.scaleOffset.chromatic.semitones, -2)
        self.assertEqual(r1.scaleOffset.diatonic.niceName, "Doubly-Augmented Unison")

        cM = scale.MajorScale('C')
        r2 = RomanNumeral('ii', cM)

        dminor = key.Key('d')
        rn = RomanNumeral('ii/o65', dminor)
        self.assertEqual(rn.pitches, chord.Chord(['G4','B-4','D5','E5']).pitches)
        
        rnOmit = RomanNumeral('V[no3]', dminor)
        self.assertEqual(rnOmit.pitches, chord.Chord(['A4', 'E5']).pitches)
        
        rnOmit = RomanNumeral('V[no5]', dminor)
        self.assertEqual(rnOmit.pitches, chord.Chord(['A4', 'C#5']).pitches)
        
        rnOmit = RomanNumeral('V[no3no5]', dminor)
        self.assertEqual(rnOmit.pitches, chord.Chord(['A4']).pitches)
        
        
#    def xtestFirst(self):                  
#         # associating a harmony with a scale
#        sc1 = MajorScale('g4')
#
#        # define undefined
#        #rn3 = sc1.romanNumeral(3, figure="7")
#
#        h1 = RomanNumeral(sc1, 1)
#        h2 = RomanNumeral(sc1, 2)
#        h3 = RomanNumeral(sc1, 3)
#        h4 = RomanNumeral(sc1, 4)
#        h5 = RomanNumeral(sc1, 5)
#
#        # can get pitches or roman numerals
#        self.assertEqual(str(h1.pitches), '[G4, B4, D5]')
#        self.assertEqual(str(h2.pitches), '[A4, C5, E5]')
#        self.assertEqual(h2.romanNumeral, 'ii')
#        self.assertEqual(h5.romanNumeral, 'V')
#        
#        # can get pitches from various ranges, invert, and get bass
#        h5.nextInversion()
#        self.assertEqual(str(h5.bass), 'F#5')
#        self.assertEqual(str(h5.getPitches('c2', 'c6')), '[F#2, A2, D3, F#3, A3, D4, F#4, A4, D5, F#5, A5]')
#
#        h5.nextInversion()
#        self.assertEqual(str(h5.getPitches('c2', 'c6')), '[A2, D3, F#3, A3, D4, F#4, A4, D5, F#5, A5]')
#
#        h5.nextInversion()
#        self.assertEqual(str(h5.bass), 'D5')
#        self.assertEqual(str(h5.getPitches('c2', 'c6')), '[D2, F#2, A2, D3, F#3, A3, D4, F#4, A4, D5, F#5, A5]')
#
#
#        sc1 = MajorScale('g4')
#        h2 = RomanNumeral(sc1, 2)
#        h2.makeSeventhChord()
#        self.assertEqual(str(h2.getPitches('c4', 'c6')), '[A4, C5, E5, G5, A5, C6]')
#
#        h2.makeNinthChord()
#        self.assertEqual(str(h2.getPitches('c4', 'c6')), '[A4, B4, C5, E5, G5, A5, B5, C6]')
#        #h2.chord.show()
 


    def testYieldRemoveA(self):
        from music21 import corpus, stream, key, note
#        s = corpus.parse('madrigal.3.1.rntxt')
        m = stream.Measure()
        m.append(key.KeySignature(4))
        m.append(note.Note())
        p = stream.Part()
        p.append(m)
        s = stream.Score()
        s.append(p)
        targetCount = 1
        self.assertEqual(len(s.flat.getElementsByClass('KeySignature')), targetCount)

        # through sequential iteration
        s1 = copy.deepcopy(s)
        for p in s1.parts:
            for m in p.getElementsByClass('Measure'):
                for e in m.getElementsByClass('KeySignature'):
                    m.remove(e)

        self.assertEqual(len(s1.flat.getElementsByClass('KeySignature')), 0)


        s2 = copy.deepcopy(s)
        self.assertEqual(len(s2.flat.getElementsByClass('KeySignature')), targetCount)
        for e in s2.flat.getElementsByClass('KeySignature'):
            for site in e.getSites():
                if site is not None:
                    site.remove(e)
        #s2.show()

        # yield elements and containers
        s3 = copy.deepcopy(s)
        self.assertEqual(len(s3.flat.getElementsByClass('KeySignature')), targetCount)

        for e in s3._yieldElementsDownward(streamsOnly=True):
            if 'KeySignature' in e.classes:
                # all active sites are None because of deep-copying
                if e.activeSite is not None:                
                    e.activeSite.remove(e)
        #s3.show()

        # yield containers
        s4 = copy.deepcopy(s)
        self.assertEqual(len(s4.flat.getElementsByClass('KeySignature')), targetCount)
        for c in s4._yieldElementsDownward(streamsOnly=False):
            if 'Stream' in c.classes:
                for e in c.getElementsByClass('KeySignature'):
                    c.remove(e)


    def testYieldRemoveB(self):
        from music21 import stream, note, corpus

        m = stream.Measure()
        m.append(key.KeySignature(4))
        m.append(note.Note())
        p = stream.Part()
        p.append(m)
        s = stream.Score()
        s.append(p)

        #s = corpus.parse('madrigal.3.1.rntxt')

        for e in s._yieldElementsDownward(streamsOnly=False):
            #environLocal.printDebug(['activeSite:', e, e.activeSite])
            if 'KeySignature' in e.classes:
                e.activeSite.remove(e)

        self.assertEqual(len(s.flat.getElementsByClass('KeySignature')), 0)


    def testYieldRemoveC(self):
        from music21 import stream, note, corpus

        s = corpus.parse('madrigal.5.8.rntxt')
        # first measure's active site is the Part
        self.assertEqual(id(s[1][0].activeSite), id(s[1]))
        # first rn's active site is the Measure
        self.assertEqual(id(s[1][0][2].activeSite), id(s[1][0]))
        self.assertEqual(id(s[1][0][3].activeSite), id(s[1][0]))

        self.assertEqual(s[1][0] in s[1][0][3].getSites(), True)


        for e in s._yieldElementsDownward(streamsOnly=False):
            if 'KeySignature' in e.classes:
                e.activeSite.remove(e)

        self.assertEqual(len(s.flat.getElementsByClass('KeySignature')), 0)


    def testScaleDegreesA(self):
        from music21 import key, roman
        k = key.Key('f#')  # 3-sharps minor
        rn = roman.RomanNumeral('V', k)
        self.assertEqual(str(rn.key), 'f# minor')
        self.assertEqual(str(rn.pitches), '[C#5, E#5, G#5]')
        self.assertEqual(str(rn.scaleDegrees), '[(5, None), (7, <accidental sharp>), (2, None)]')
                


class TestExternal(unittest.TestCase):

    def runTest(self):
        pass


    def testFromChordify(self):
        from music21 import corpus
        b = corpus.parse('bwv103.6')
        c = b.chordify()
        ckey = b.analyze('key')
        figuresCache = {}
        for x in c.recurse():
            if 'Chord' in x.classes:
                rnc = romanNumeralFromChord(x, ckey)
                figure = rnc.figure
                if figure not in figuresCache:
                    figuresCache[figure] = 1
                else:
                    figuresCache[figure] += 1 
                x.lyric = figure
                
        sortedList = sorted(figuresCache, key=figuresCache.get, reverse=True)
        for thisFigure in sortedList:
            print thisFigure, figuresCache[thisFigure]
            
        b.insert(0, c)
        b.show()


_DOC_ORDER = [RomanNumeral]


if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof