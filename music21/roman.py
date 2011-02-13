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


from music21 import environment
_MOD = 'roman.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------

SHORTHAND_RE = re.compile('#*-*b*o*[1-9xyz]')
ENDWITHFLAT_RE = re.compile('[b\-]$')

def expandShortHand(shorthand):
    '''
    expands shorthand notation into comma notation
    
    >>> from music21.roman import expandShortHand
    >>> expandShortHand("64")
    '6,4'
    >>> expandShortHand("973")
    '9,7,3'
    >>> expandShortHand("11b3")
    '11,b3'
    >>> expandShortHand("b13#9-6")
    'b13,#9,-6'
    >>> expandShortHand("-")
    '5,-3'
    >>> expandShortHand("6/4")
    '6,4'
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
    return ','.join(shGroupOut)
        

class RomanNumeral(chord.Chord):
    '''
    
    >>> from music21 import *
    >>> V = roman.RomanNumeral('V') # could also use 5
    >>> V.quality
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

    PROBLEM! >>> minoriiiB = roman.RomanNumeral('IIIb', em, caseMatters = False)
    ####>>> minoriiiB.pitches
    #####[G4, B-4, D5]
    
   
    Can also take a scale object, here we build a first-inversion chord
    on the raised-three degree of D-flat major, that is, F#-major (late
    Schubert would be proud...)
    
    
    >>> sharp3 = roman.RomanNumeral('#III6', scale.MajorScale('D-'))
    >>> sharp3.scaleDegreeWithAlteration
    (3, <accidental sharp>)
    >>> sharp3.pitches
    [A#4, C#5, F#5]
   
   
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
    >>> r.figure
    'v64/V'
    >>> r.pitches
    [C#5, F#5, A5]

    >>> r2 = roman.RomanNumeral('V42/V7/vi', key.Key('C'))
    >>> r2.pitches
    [A4, B4, D#5, F#5]

    
    OMIT_FROM_DOCS
    Things that were giving us trouble
    >>> dminor = key.Key('d')
    >>> rn = roman.RomanNumeral('ii/o65', dminor)
    >>> rn.pitches
    [G4, B-4, D5, E5]
    
    >>> rn3 = roman.RomanNumeral('III', dminor)
    >>> rn3.pitches
    [F4, A4, C5]
    
    '''

    frontFlat = re.compile('^(b+)')
    frontFlatAlt = re.compile('^(\-+)')
    frontSharp = re.compile('^(\#+)')
    romanNumerals = re.compile('(i?v?i*)', re.IGNORECASE)
    secondarySlash = re.compile('(.*?)\/([\#a-np-zA-NP-Z].*)')
    omitNote = re.compile('\[no([1-9])\].*')
    
    def __init__(self, figure=None, keyOrScale=None, caseMatters = True):
        chord.Chord.__init__(self)

        self.caseMatters = caseMatters
        self.scaleCardinality = 7
        
        if isinstance(figure, int):
            self.caseMatters = False
            figure = common.toRoman(figure)
         # store raw figure
        self.figure = figure
        
        if common.isStr(keyOrScale):
            keyOrScale = key.Key(keyOrScale)
            
        self.scale = keyOrScale
        self.impliedScale = None
        self.setKeyOrScale(keyOrScale)


    def setKeyOrScale(self, keyOrScale):
        '''Provide a new key or scale, and re-configure the RN with the existing figure. 
        
        >>> from music21 import *
        >>> r1 = RomanNumeral('V')
        >>> r1.pitches
        [G4, B4, D5]
        >>> r1.setKeyOrScale(key.Key('A'))
        >>> r1.pitches
        [E5, G#5, B5]
        '''
        self.scale = keyOrScale
        if keyOrScale == None or (hasattr(keyOrScale, "isConcrete") and 
            keyOrScale.isConcrete == False):
            self.impliedScale = True
        else:
            self.impliedScale = False        
        # need to permit object creation with no arguments
        if self.figure is not None:
            self._parseFigure(self.figure)

        #environLocal.printDebug(['Roman.setKeyOrScale:', 'called w/ scale', self.scale, 'figure', self.figure, 'pitches', self.pitches])


    def _parseFigure(self, prelimFigure):
        '''
        '''
        
        if not common.isStr(prelimFigure):
            raise RomanException('got a non-string figure: %r', prelimFigure)

        if self.impliedScale == False:
            useScale = self.scale
        else:
            if self.scale != None:
                useScale = self.scale.derive(1, 'C')
            else:
                useScale = scale.MajorScale('C')

        secondary = self.secondarySlash.match(prelimFigure)
        
        ## TODO: secondaries of secondaries
        if secondary:
            primaryFigure = secondary.group(1)
            secondaryFigure = secondary.group(2)
            secRoman = RomanNumeral(secondaryFigure, useScale, self.caseMatters)
            if secRoman.semitonesFromChordStep(3) == 3:
                secondaryMode = 'minor'
            else:
                secondaryMode = 'major'
            useScale = key.Key(secRoman.root().name, secondaryMode)
            figure = primaryFigure
        else:
            figure = prelimFigure

        omit = self.omitNote.search(figure)
        if omit:
            omit = int(omit.group(1))
            figure = self.omitNote.sub('', figure)

        flatAlteration = 0
        sharpAlteration = 0
        figure = re.sub('^N', 'bII', figure)
        frontAlteration = "" # the b in bVI, or the # in #vii
        if self.frontFlat.match(figure):
            fm = self.frontFlat.match(figure)
            flatAlteration = len(fm.group(1))
            transposeInterval = interval.intervalFromGenericAndChromatic(interval.GenericInterval(1), interval.ChromaticInterval(-1 * flatAlteration))
            scaleAlter = pitch.Accidental(-1 * flatAlteration)
            figure = self.frontFlat.sub('', figure)
            frontAlteration = fm
        elif self.frontFlatAlt.match(figure):
            fm = self.frontFlatAlt.match(figure)
            flatAlteration = len(fm.group(1))
            transposeInterval = interval.intervalFromGenericAndChromatic(interval.GenericInterval(1), interval.ChromaticInterval(-1 * flatAlteration))
            scaleAlter = pitch.Accidental(-1 * flatAlteration)
            figure = self.frontFlatAlt.sub('', figure)
            frontAlteration = fm
        elif self.frontSharp.match(figure):
            sm = self.frontSharp.match(figure)
            sharpAlteration = len(sm.group(1))
            transposeInterval = interval.intervalFromGenericAndChromatic(interval.GenericInterval(1), interval.ChromaticInterval(1 * sharpAlteration))
            scaleAlter = pitch.Accidental(sharpAlteration)
            figure = self.frontSharp.sub('', figure)
            frontAlteration = sm
        else: 
            transposeInterval = None
            scaleAlter = None

        romanNumeralAlone = ""
        if not self.romanNumerals.match(figure):
            raise RomanException("No roman numeral found in %s " % (figure))
        else:
            rm = self.romanNumerals.match(figure)
            romanNumeralAlone = rm.group(1)
            self.scaleDegree = common.fromRoman(romanNumeralAlone)
            figure = self.romanNumerals.sub('', figure)

        
        shouldBe = '' # major, minor, augmented, or diminished (and half-diminished for 7ths)
        if figure.startswith('o'):
            figure = figure[1:]
            shouldBe = 'diminished'
        elif figure.startswith('/o'):
            figure = figure[2:]
            shouldBe = 'half-diminished'
        elif figure.startswith('+'):
            figure = figure[1:]
            shouldBe = 'augmented'
        elif self.caseMatters and romanNumeralAlone.upper() == romanNumeralAlone:
            shouldBe = 'major'
        elif self.caseMatters and romanNumeralAlone.lower() == romanNumeralAlone:
            shouldBe = 'minor'
#        elif self.caseMatters == False and hasattr(useScale, 'mode'):
#            if useScale.mode == 'major':
#                if self.scaleDegree in [1,4,5]:
#                    shouldBe = 'major'
#                elif self.scaleDegree in [2,3,6]:
#                    shouldBe = 'minor'
#                elif self.scaleDegree == 7:
#                    shouldBe = 'diminished'
#            elif useScale.mode == 'minor':
#                if self.scaleDegree in [1,4,5]:
#                    shouldBe = 'minor'
#                elif self.scaleDegree in [3,6,7]:
#                    shouldBe = 'major'
#                elif self.scaleDegree == 2:
#                    shouldBe = 'diminished'            
            
        # make vii always #vii and vi always #vi
        if frontAlteration == "" and hasattr(useScale, 'mode') and \
             useScale.mode == 'minor' and self.caseMatters == True:
            if self.scaleDegree == 6 and shouldBe == 'minor':
                transposeInterval = interval.Interval('A1')
                scaleAlter = pitch.Accidental(1)
            elif self.scaleDegree == 7 and (shouldBe == 'minor' or shouldBe =='diminished' or shouldBe == 'half-diminished'):
                transposeInterval = interval.Interval('A1')
                scaleAlter = pitch.Accidental(1)
                if shouldBe == 'minor':
                    shouldBe = 'diminished'

        sd = self.scaleDegree
        self.scaleDegreeWithAlteration = (sd, scaleAlter)
        
        shfig = expandShortHand(figure)
        
        notationObj = fbNotation.Notation(shfig)
        
        self.scaleCardinality = len(useScale.pitches) - 1 # should be 7 but hey, octatonic scales, etc.

        bassScaleDegree = self.bassScaleDegreeFromNotation(notationObj)
        bassPitch = useScale.pitchFromDegree(bassScaleDegree, direction = scale.DIRECTION_ASCENDING)
        pitches = [bassPitch]
        lastPitch = bassPitch
        numberNotes = len(notationObj.numbers)
        
        for j in range(numberNotes):
            i = numberNotes - j - 1
            thisSD = bassScaleDegree + notationObj.numbers[i] - 1
            newPitch = useScale.pitchFromDegree(thisSD, direction = scale.DIRECTION_ASCENDING)
            pitchName = notationObj.modifiers[i].modifyPitchName(newPitch.name)
            newnewPitch = pitch.Pitch(pitchName + str(newPitch.octave))
            if newnewPitch.midi < lastPitch.midi:
                newnewPitch.octave += 1
            pitches.append(newnewPitch)
            lastPitch = newnewPitch

        if transposeInterval:
            newPitches = []
            for thisPitch in pitches:
                newPitch = thisPitch.transpose(transposeInterval)
                newPitches.append(newPitch)
            self.pitches = newPitches
        else:
            self.pitches = pitches
        
        self._fixAccidentals(shouldBe)
                
        self.remainingFigure = figure
        self.scaleOffset = transposeInterval
        
        if omit:
            omittedPitch = self.getChordStep(omit)
            newPitches = []
            for thisPitch in pitches:
                if omittedPitch != thisPitch:
                    newPitches.append(thisPitch)
            self.pitches = newPitches
            

    def _fixAccidentals(self, shouldBe):
        '''
        fixes notes that should be out of the scale
        based on what the chord "shouldBe" (major, minor, augmented, diminished)
        
        an intermediary step in parsing figures
        
        '''        
        chordStepsToExamine = (3,5,7)
        if shouldBe == 'major':
            correctSemitones = (4, 7)
        elif shouldBe == 'minor':
            correctSemitones = (3, 7)
        elif shouldBe == 'diminished':
            if len(self.pitches) == 2:
                correctSemitones = (3, 6)
            elif len(self.pitches) > 2:
                correctSemitones = (3, 6, 9)
        elif shouldBe == 'half-diminished':
            correctSemitones = (3, 6, 10)
        elif shouldBe == 'augmented':
            correctSemitones = (4, 8)
        else:
            return

        newPitches = []
        for i in range(len(correctSemitones)): # 3,5,7
            thisChordStep = chordStepsToExamine[i]
            thisCorrect = correctSemitones[i]
            thisSemis = self.semitonesFromChordStep(thisChordStep)
            if thisSemis == 0:
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

def fromChordAndKey(inChord, inKey):
    '''
    return a RomanNumeral object from the given chord in the given key.
    
    >>> from music21 import *
    >>> dim7chord = chord.Chord(["E2", "C#3", "B-3", "G4"])
    >>> viio65 = roman.fromChordAndKey(dim7chord, key.Key('D'))
    >>> viio65
    'VII'
    >>> roman.fromChordAndKey(["E-3","G4","B-5"], key.Key('D'))
    'bII'
    >>> roman.fromChordAndKey(["G#3","B#4","D#5"], key.Key('D'))
    '#IV'

    
    #>>> viio65.pitches   # retains octave
    #['E2', 'C#3', 'B-3', 'G4']
    #>>> viio65.figure
    #'viio65'
    '''
    if isinstance(inChord, list):
        inChord = chord.Chord(inChord)
    chordRoot = inChord.root()
    chordBass = inChord.bass()
    frontPrefix = ""
    scaleDeg = inKey.getScaleDegreeFromPitch(chordRoot)
    if scaleDeg is None:
        tempChordRoot = copy.deepcopy(chordRoot)
        tempChordRoot.accidental = pitch.Accidental(tempChordRoot.accidental.alter + 1)
        scaleDeg = inKey.getScaleDegreeFromPitch(tempChordRoot, comparisonAttribute='name')
        if scaleDeg is not None:
            frontPrefix = 'b'
        else:        
            tempChordRoot = copy.deepcopy(chordRoot)
            tempChordRoot.accidental = pitch.Accidental(tempChordRoot.accidental.alter - 1)
            scaleDeg = inKey.getScaleDegreeFromPitch(tempChordRoot, comparisonAttribute='name')
            if scaleDeg is not None:
                frontPrefix = '#'
            else:
                raise RomanException('could not find this note as a scale degree in the given key (double-sharps and flats, such as bbVII are not currently searched)')
    rootScaleDeg = frontPrefix + common.toRoman(int(scaleDeg))
    return rootScaleDeg






class RomanException(music21.Music21Exception):
    pass

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
        self.assertEqual(r1.remainingFigure, "6")
        self.assertEqual(r1.scaleOffset.chromatic.semitones, -2)
        self.assertEqual(r1.scaleOffset.diatonic.niceName, "Doubly-Augmented Unison")

        cM = scale.MajorScale('C')
        r2 = RomanNumeral('ii', cM)

        dminor = key.Key('d')
        rn = RomanNumeral('ii/o65', dminor)
        self.assertEqual(rn.pitches, chord.Chord(['G4','B-4','D5','E5']).pitches)
        
        
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
 


_DOC_ORDER = [RomanNumeral, fromChordAndKey]


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
