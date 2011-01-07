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
    '''
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
   
   
    >>> em = key.Key('e')
    >>> dominantV = roman.RomanNumeral('V7', em)
    >>> dominantV.pitches
    [B4, D#5, F#5, A5]
    
    >>> minorV = roman.RomanNumeral('V43', em, caseMatters = False) 
    >>> minorV.pitches
    [F#4, A4, B4, D5]



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
    
    
    Just for kicks (no worries if this is goobley-gook):
    
    
    
    >>> ots = scale.OctatonicScale("C2")
    >>> rn = roman.RomanNumeral('I9', ots, caseMatters=False)
    >>> rn.pitches
    [C2, E-2, G-2, A2, C3]
    >>> rn2 = roman.RomanNumeral('V7#5b3', ots, caseMatters = False)
    >>> rn2.pitches
    [G-2, A-2, C#3, E-3] 
    
    
    '''

    frontFlat = re.compile('^(b+)')
    frontFlatAlt = re.compile('^(\-+)')
    frontSharp = re.compile('^(\#+)')
    romanNumerals = re.compile('(i?v?i*)', re.IGNORECASE)
    
    def __init__(self, figure=None, keyOrScale=None, caseMatters = True):
        chord.Chord.__init__(self)

        self.caseMatters = caseMatters
        self.scaleCardinality = 7
        
        
        if isinstance(figure, int):
            self.caseMatters = False
            figure = common.toRoman(figure)
 
        if common.isStr(keyOrScale):
            keyOrScale = key.Key(keyOrScale)
        self.scale = keyOrScale
        if keyOrScale == None or (hasattr(keyOrScale, "isConcrete") and keyOrScale.isConcrete == False):
            self.impliedScale = True
        else:
            self.impliedScale = False
        
        self._parseFigure(figure)


    def _parseFigure(self, figure):
        self.figure = figure

        flatAlteration = 0
        sharpAlteration = 0
        figure = re.sub('^N', 'bII', figure)
        
        if self.frontFlat.match(figure):
            fm = self.frontFlat.match(figure)
            flatAlteration = len(fm.group(1))
            transposeInterval = interval.intervalFromGenericAndChromatic(interval.GenericInterval(1), interval.ChromaticInterval(-1 * flatAlteration))
            scaleAlter = pitch.Accidental(-1 * flatAlteration)
            figure = self.frontFlat.sub('', figure)
        elif self.frontFlatAlt.match(figure):
            fm = self.frontFlatAlt.match(figure)
            flatAlteration = len(fm.group(1))
            transposeInterval = interval.intervalFromGenericAndChromatic(interval.GenericInterval(1), interval.ChromaticInterval(-1 * flatAlteration))
            scaleAlter = pitch.Accidental(-1 * flatAlteration)
            figure = self.frontFlatAlt.sub('', figure)
        elif self.frontSharp.match(figure):
            sm = self.frontSharp.match(figure)
            sharpAlteration = len(sm.group(1))
            transposeInterval = interval.intervalFromGenericAndChromatic(interval.GenericInterval(1), interval.ChromaticInterval(1 * sharpAlteration))
            scaleAlter = pitch.Accidental(sharpAlteration)
            figure = self.frontSharp.sub('', figure)
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

        
        sd = self.scaleDegree
        self.scaleDegreeWithAlteration = (sd, scaleAlter)
        
        shfig = expandShortHand(figure)
        
        notationObj = fbNotation.Notation(shfig)
        bassSD = self.bassScaleDegreeFromNotation(notationObj)
        
        if self.impliedScale == False:
            useScale = self.scale
        else:
            if self.scale != None:
                useScale = self.scale.derive(1, 'C')
            else:
                useScale = scale.MajorScale('C')

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
            for thisPitch in pitches:
                thisPitch.transpose(transposeInterval, inPlace = True)
        
        self.pitches = pitches
        
        self._fixAccidentals(shouldBe)
                
        self.remainingFigure = figure
        self.scaleOffset = transposeInterval

    def _fixAccidentals(self, shouldBe):
        '''
        fixes notes that should be out of the scale
        based on what the chord "shouldBe" (major, minor, augmented, diminished)
                
        '''        
        defaultScaleDegrees = (3,5,7)
        if shouldBe == 'major':
            defaults = (4, 7)
        elif shouldBe == 'minor':
            defaults = (3, 7)
        elif shouldBe == 'diminished':
            if len(self.pitches) == 2:
                defaults = (3, 6)
            elif len(self.pitches) > 2:
                defaults = (3, 6, 9)
        elif shouldBe == 'half-diminished':
            defaults = (3, 6, 10)
        elif shouldBe == 'augmented':
            defaults = (4, 8)
        else:
            return

        for i in range(len(defaults)):
            thisScaleDegree = defaultScaleDegrees[i]
            thisDefault = defaults[i]
            thisSemis = self.hasScaleX(thisScaleDegree)
            if thisSemis == 0:
                continue
            if thisSemis != thisDefault:
                faultyPitch = self.scaleX(thisScaleDegree)
                if faultyPitch == None:
                    raise RomanException("this is very odd...")
                if faultyPitch.accidental == None:
                    faultyPitch.accidental = pitch.Accidental(thisDefault - thisSemis)
                else:
                    acc = faultyPitch.accidental
                    acc.set(thisDefault - thisSemis + acc.alter)
        

#    def _getRoot(self):
#        return self.scale.pitchFromDegree(self.rootScaleStep)
#
#    root = property(_getRoot, 
#        doc = '''Return the root of this harmony. 
#
#        >>> from music21 import *
#        >>> sc1 = scale.MajorScale('g')
#        >>> h1 = sc1.getRomanNumeral(1)
#        >>> h1.root
#        G4
#        ''')
#
#    def _getBass(self):
#        return self.scale.pitchFromDegree(self.rootScaleStep + self._members[self._bassMemberIndex])
#
#    bass = property(_getBass, 
#        doc = '''Return the root of this harmony. 
#
#        >>> from music21 import *
#        >>> sc1 = scale.MajorScale('g')
#        >>> h1 = scale.RomanNumeral(sc1, 1)
#        >>> h1.bass
#        G4
#        ''')
#
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
#
#    def _memberIndexToPitch(self, memberIndex, minPitch=None,
#         maxPitch=None, direction=DIRECTION_ASCENDING):
#        '''Given a member index, return the scale degree
#
#
#        >>> from music21 import *
#        >>> sc1 = scale.MajorScale('g4')
#        >>> h1 = scale.RomanNumeral(sc1, 5)
#        >>> h1._memberIndexToPitch(0)
#        D5
#        >>> h1._memberIndexToPitch(1)
#        F#5
#        '''
#        return self.scale.pitchFromDegree(
#                    self._memberIndexToScaleDegree(memberIndex), 
#                    minPitch=minPitch, maxPitch=maxPitch)
#
#
#    def _memberIndexToScaleDegree(self, memberIndex):
#        '''Return the degree in the underlying scale given a member index.
#
#        >>> from music21 import *
#        >>> sc1 = scale.MajorScale('g4')
#        >>> h1 = scale.RomanNumeral(sc1, 5)
#        >>> h1._memberIndexToScaleDegree(0)
#        5
#        >>> h1._memberIndexToScaleDegree(1)
#        7
#        >>> h1._memberIndexToScaleDegree(2)
#        9
#        '''
#        # note that results are not taken to the modulus of the scale
#        # make an option
#        return self.rootScaleStep + self._members[memberIndex]
#
#
#    def _degreeToMemberIndex(self, degree):
#        '''Return the member index of a provided degree, assuming that degree is a member.
#
#        >>> from music21 import *
#        >>> sc1 = scale.MajorScale('g4')
#        >>> h1 = scale.RomanNumeral(sc1, 5)
#        >>> h1._degreeToMemberIndex(1)
#        0
#        >>> h1._degreeToMemberIndex(3)
#        1
#        >>> h1._degreeToMemberIndex(5)
#        2
#        '''
#        return self._members.index(degree-1)
#
#
#
#    def _prepareAlterations(self):
#        '''Prepare the alterations dictionary to conform to the presentation necessary for use in IntervalNetwork. All stored member indexes need to be converted to scale degrees.
#        '''
#        post = {}
#        for key, value in self._alterations:
#            
#            post
#
#    def pitchFromDegree(self, degree, minPitch=None,
#         maxPitch=None, direction=DIRECTION_ASCENDING):
#        '''Given a chord degree, such as 1 (for root), 3 (for third chord degree), return the pitch.
#
#        >>> from music21 import *
#        >>> sc1 = scale.MajorScale('g4')
#        >>> h1 = scale.RomanNumeral(sc1, 5)
#        >>> h1.pitchFromDegree(1)
#        D5
#        >>> h1.pitchFromDegree(2) # not a member, but we can get pitch
#        E5
#        >>> h1.pitchFromDegree(3) # third
#        F#5
#
#        '''
#        return self.scale.pitchFromDegree(
#                    self.rootScaleStep + degree-1, 
#                    minPitch=minPitch, maxPitch=maxPitch)
#
#
#
#    def scaleDegreeFromDegree(self, degree, minPitch=None,
#         maxPitch=None, direction=DIRECTION_ASCENDING):
#        '''Given a degree in this Harmony, such as 3, or 5, return the scale degree in the underlying scale
#
#        >>> from music21 import *
#        >>> sc1 = scale.MajorScale('g4')
#        >>> h1 = scale.RomanNumeral(sc1, 5)
#        >>> h1.scaleDegreeFromDegree(1)
#        5
#        >>> h1.scaleDegreeFromDegree(3)
#        7
#        '''
#        # note: there may be a better way to do this that 
#        return self.scale.getScaleDegreeFromPitch(
#            self.pitchFromDegree(degree, minPitch=minPitch, maxPitch=maxPitch, direction=direction))
#
#
#    def getPitches(self, minPitch=None, maxPitch=None,
#         direction=DIRECTION_ASCENDING):
#        '''Return the pitches the constitute this RomanNumeral with the present Scale.
#
#        >>> from music21 import *
#        >>> sc1 = scale.MajorScale('g4')
#        >>> h1 = scale.RomanNumeral(sc1, 1)
#        >>> h1.makeTriad()
#        >>> h1.getPitches()
#        [G4, B4, D5]
#        >>> h1.rootScaleStep = 7
#        >>> h1.getPitches()
#        [F#5, A5, C6]
#
#        >>> h1.rootScaleStep = 5
#        >>> h1.getPitches('c2','c8')
#        [D2, F#2, A2, D3, F#3, A3, D4, F#4, A4, D5, F#5, A5, D6, F#6, A6, D7, F#7, A7]
#
#        '''
#        # first, get members, than orient bass/direction
#        post = []
#        bass = self._memberIndexToPitch(self._bassMemberIndex, 
#                minPitch=minPitch, maxPitch=maxPitch, direction=direction)
#
#        #bass = self.scale.pitchFromDegree(self.rootScaleStep + 
#        #            self._members[self._bassMemberIndex], 
#        #            minPitch=minPitch, maxPitch=maxPitch)
#
#        # for now, getting directly from network
#        #self.scale.abstract._net.realizePitchByStep()
#
#        degreeTargets = [self.rootScaleStep + n for n in self._members]
#
#        if maxPitch is None:
#            # assume that we need within an octave above the bass
#            maxPitch = bass.transpose('M7')
#
#        # transpose up bass by m2, and assign to min
#        post = self.scale.pitchesFromScaleDegrees(
#            degreeTargets=degreeTargets, 
#            minPitch=bass.transpose('m2'), 
#            maxPitch=maxPitch, 
#            direction=direction)
#
#        #environLocal.printDebug(['getPitches', 'post', post, 'degreeTargets', degreeTargets, 'bass', bass, 'minPitch', minPitch, 'maxPitch', maxPitch])
#
#        # add bass in front
#        post.insert(0, bass)
#        return post
#
#    pitches = property(getPitches, 
#        doc = '''Get the minimum default pitches for this RomanNumeral
#        ''')
#
#
#    def _alterDegree(self, degree, alteration):
#        '''Given a scale degree as well as an alteration, configure the 
#        alteredDegrees dictionary.
#        '''
#        # TODO
#        pass
#
#
#
#
#
#    def _getRomanNumeral(self):
#        '''
#
#        >>> from music21 import *
#        >>> sc1 = scale.MajorScale('g4')
#        >>> h1 = scale.RomanNumeral(sc1, 2)
#        >>> h1.romanNumeral
#        'ii'
#        >>> h1.romanNumeral = 'vii'
#        >>> h1.chord
#        <music21.chord.Chord F#5 A5 C6>
#        '''
#        notation = []
#        rawNumeral = common.toRoman(self.rootScaleStep)
#
#        # for now, can just look at chord to get is minor
#        # TODO: get intervals; measure intervals over the bass
#        # need to realize in tandem with returning intervals
#
#        c = self.chord
#        if c.isMinorTriad():
#            rawNumeral = rawNumeral.lower()
#        elif c.isMajorTriad():
#            rawNumeral = rawNumeral.upper()
#    
#        # todo: add inversion symbol
#        return rawNumeral
#
#    def _setRomanNumeral(self, numeral):
#        # TODO: strip off inversion figures and configure inversion
#        self.rootScaleStep = common.fromRoman(numeral)
#
#    romanNumeral = property(_getRomanNumeral, _setRomanNumeral,
#        doc='''Return the roman numeral representation of this RomanNumeral, or set this RomanNumeral with a roman numeral representation.
#        ''')
#
#
#    def setFromPitches(self):
#        '''Given a list of pitches or pitch-containing objects, find a root and inversion that provides the best fit.
#        '''
#        pass
    
    
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
#    '''
#    return a RomanNumeral object from the given chord in the given key.
#    
#    >>> dim7chord = chord.Chord(["E2", "C#3", "B-3", "G4"])
#    >>> viio65 = roman.fromChordAndKey(dim7chord, key.Key('D'))
#    >>> viio65.pitches   # retains octave
#    ['E2', 'C#3', 'B-3', 'G4']
#
#    '''
    pass






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
