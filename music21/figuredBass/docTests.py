import unittest
import music21

'''
Contains all the sample tests in "fbRealizer: A 21st Century, Computational Engineering Approach
to the Centuries-Old Musical Problem of Figured Bass Resolution" by Jose Cabal-Ugaz (2011, MIT)
'''

#--------------------------------------------------
# I. notation.py

def notationExample1():
    '''
    >>> from music21.figuredBass import notation
    >>> notation1a = notation.Notation("6, 4+, 2")
    '''
    pass
    
def notationExample2():
    '''
    >>> from music21 import note
    >>> from music21.figuredBass import realizer
    >>> fbExample = realizer.FiguredBass()
    >>> noteA = note.Note("C3")
    >>> notationStringA  = "6"
    >>> fbExample.addElement(noteA, notationStringA)
    '''
    pass
    
def notationExample3():
    '''
    >>> from music21.figuredBass import notation
    >>> notation1a = notation.Notation("6, 4+, 2")
    >>> notation1a.origNumbers
    (6, 4, 2)
    >>> notation1a.origModStrings
    (None, '+', None)
    '''
    pass
    
def notationExample4():
    '''
    >>> from music21.figuredBass import notation
    >>> notation1b = notation.Notation("4+, 2")
    >>> notation1b.origNumbers
    (4, 2)
    >>> notation1b.numbers
    (6, 4, 2)
    >>> notation1b.origModStrings
    ('+', None)
    >>> notation1b.modifierStrings
    (None, '+', None)
    '''
    pass
    
def notationExample5():
    '''
    >>> from music21.figuredBass import notation
    >>> notation2 = notation.Notation("#")
    >>> notation2.numbers
    (5, 3)
    >>> notation2.modifierStrings
    (None, '#')
    >>> notation3 = notation.Notation("7, 5, #")
    >>> notation3.numbers
    (7, 5, 3)
    >>> notation3.modifierStrings
    (None, None, '#')
    >>> notation4 = notation.Notation("7, #")
    >>> notation4.numbers
    (7, 3)
    >>> notation4.modifierStrings
    (None, '#')
    '''
    pass
    
def notationExample6():
    '''
    >>> from music21.figuredBass import notation
    >>> from music21 import pitch
    >>> sharp = notation.Modifier("+")
    >>> sharp.modifyPitch(pitch.Pitch("A3"))
    A#3
    >>> sharp.modifyPitchName("A")
    'A#'
    '''
    pass
    
def notationExample7():
    '''
    >>> from music21.figuredBass import notation
    >>> notation1a = notation.Notation("6, 4+, 2")
    >>> notation1a.figures[1]
    <music21.figuredBass.notation Figure 4 <modifier + <accidental sharp>>>
    '''
    pass

#--------------------------------------------------
# II. realizerScale.py

def realizerScaleExample1():
    '''
    >>> from music21.figuredBass import realizerScale
    >>> fbScale1 = realizerScale.FiguredBassScale("D", "major")
    >>> fbScale1.realizerScale
    <music21.scale.MajorScale D major>
    >>> fbScale1.keySig
    <music21.key.KeySignature of 2 sharps>
    >>> fbScale2 = realizerScale.FiguredBassScale("E", "phrygian")
    >>> fbScale2.realizerScale
    <music21.scale.PhrygianScale E phrygian>
    '''
    pass
    
def realizerScaleExample2():
    '''
    >>> from music21.figuredBass import realizerScale
    >>> from music21 import pitch
    >>> pitchString = "C5"
    >>> realizerScale.convertToPitch(pitchString)
    C5
    >>> realizerScale.convertToPitch(pitch.Pitch('E4'))
    E4
    '''
    pass
    
def realizerScaleExample3():
    '''
    >>> from music21.figuredBass import realizerScale
    >>> fbScale1 = realizerScale.FiguredBassScale("D", "major")
    >>> fbScale1.getPitchNames("E3", "6")
    ['E', 'G', 'C#']
    '''
    pass
    
def realizerScaleExample4():
    '''
    >>> from music21.figuredBass import realizerScale
    >>> fbScale1 = realizerScale.FiguredBassScale("D", "major")
    >>> fbScale1.getPitchNames("C#3", "6, #5")
    ['C#', 'E', 'G#', 'A']
    '''
    pass

def realizerScaleExample5():
    '''
    >>> from music21.figuredBass import realizerScale
    >>> fbScale1 = realizerScale.FiguredBassScale("D", "major")
    >>> fbScale1.getPitchNames("D#3", "-7")
    ['D#', 'F#', 'A', 'C']
    '''
    pass

def realizerScaleExample6():
    '''
    >>> from music21.figuredBass import realizerScale
    >>> fbScale1 = realizerScale.FiguredBassScale("D", "major")
    >>> fbScale1.getPitches("D3", "6")
    [D3, F#3, B3, D4, F#4, B4, D5, F#5, B5]
    '''
    pass

def realizerScaleExample7():
    '''
    >>> from music21.figuredBass import realizerScale
    >>> fbScale1 = realizerScale.FiguredBassScale("D", "major")
    >>> fbScale1.getSamplePitches("D3", "6")
    [D3, F#3, B3]
    '''
    pass

#--------------------------------------------------
# III. rules.py

def rulesExample1():
    '''
    >>> from music21.figuredBass import rules
    >>> fbRules = rules.Rules()
    >>> fbRules.allowParallelFifths
    False
    >>> fbRules.allowParallelFifths = True
    >>> fbRules.allowParallelFifths
    True
    '''
    pass

def rulesExample2():
    '''
    >>> from music21.figuredBass import rules
    >>> fbRules = rules.Rules()
    >>> fbRules.upperPartsMaxSemitoneSeparation
    12
    >>> fbRules.upperPartsMaxSemitoneSeparation = 6
    >>> fbRules.upperPartsMaxSemitoneSeparation
    6
    >>> fbRules.upperPartsMaxSemitoneSeparation = None
    >>> print(fbRules.upperPartsMaxSemitoneSeparation)
    None
    '''
    pass

def rulesExample3():
    '''
    >>> from music21.figuredBass import rules
    >>> fbRules = rules.Rules()
    >>> fbRules.allowVoiceOverlap
    False
    >>> fbRules.allowVoiceOverlap = True
    >>> fbRules.allowVoiceOverlap
    True
    '''
    pass
    
def rulesExample4():
    '''
    >>> from music21.figuredBass import rules
    >>> fbRules = rules.Rules()
    >>> fbRules.doubledRootInDim7
    False
    >>> fbRules.doubledRootInDim7 = True
    >>> fbRules.doubledRootInDim7
    True
    '''
    pass

#--------------------------------------------------
# IV. resolution.py

def resolutionExample1():
    '''
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> Fdom43 = possibility.Possibility({p1: "E5", p2: "B-4", p3: "C4", p4: "G3"})
    >>> print(Fdom43)
    {1: E5, 2: B-4, 3: C4, 4: G3}
    >>> print(resolution.dominantSeventhToMajorTonic(Fdom43))
    {1: F5, 2: A4, 3: C4, 4: F3}
    >>> print(resolution.dominantSeventhToMajorTonic(Fdom43, True))
    {1: F5, 2: C5, 3: C4, 4: A3}
    >>> Fdom7 = possibility.Possibility({p1: "B-3", p2: "G3", p3: "E3", p4: "C3"})
    >>> print(Fdom7)
    {1: B-3, 2: G3, 3: E3, 4: C3}
    >>> print(resolution.dominantSeventhToMinorSubmediant(Fdom7))
    {1: A3, 2: F3, 3: F3, 4: D3}
    >>> print(resolution.dominantSeventhToMajorSubdominant(Fdom7))
    {1: B-3, 2: F3, 3: F3, 4: D3}
    '''
    pass

def resolutionExample2():
    '''
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> Ddim7 = possibility.Possibility({p1: "B-4", p2: "E4", p3: "G3", p4: "C#3"})
    >>> print(Ddim7)
    {1: B-4, 2: E4, 3: G3, 4: C#3}
    >>> print(resolution.diminishedSeventhToMajorTonic(Ddim7))
    {1: A4, 2: F#4, 3: F#3, 4: D3}
    >>> print(resolution.diminishedSeventhToMajorTonic(Ddim7, True))
    {1: A4, 2: D4, 3: F#3, 4: D3}
    >>> print(resolution.diminishedSeventhToMinorSubdominant(Ddim7))
    {1: B-4, 2: D4, 3: G3, 4: D3}
    '''
    pass

#--------------------------------------------------
# V. part.py

def partExample1():
    '''
    >>> from music21.figuredBass import part
    >>> range0 = part.Range("E2", "E4")
    >>> range0.lowestPitch
    E2
    >>> range0.highestPitch
    E4
    >>> range1 = part.Range("C5", "C2")
    >>> range1.lowestPitch
    C2
    >>> range1.highestPitch
    C5
    '''
    pass

def partExample2():
    '''
    >>> from music21.figuredBass import part
    >>> from music21.figuredBass import realizerScale
    >>> fbScale2 = realizerScale.FiguredBassScale("C")
    >>> pitchesAboveBass = fbScale2.getPitches("C2")
    >>> pitchesAboveBass
    [C2, E2, G2, C3, E3, G3, C4, E4, G4, C5, E5, G5]
    >>> range0 = part.Range("E2", "E4")
    >>> range0.pitchesInRange(pitchesAboveBass)
    [E2, G2, C3, E3, G3, C4, E4]
    '''
    pass
    
def partExample3():
    '''
    >>> from music21.figuredBass import part
    >>> rangeA = part.Range("B3", "G6")
    >>> rangeB = part.Range("B3", "G7")
    >>> rangeB > rangeA
    True
    '''
    pass
    
def partExample4():
    '''
    >>> from music21.figuredBass import part
    >>> bassVoice = part.Part("Bass", 16, "E2", "E4")
    >>> bassVoice
    <music21.figuredBass.part Part Bass: E2->E4>
    >>> bassVoice.label
    'Bass'
    >>> bassVoice.maxSeparation
    16
    >>> bassVoice.range.lowestPitch
    E2
    >>> bassVoice.range.highestPitch
    E4
    '''
    pass

def partExample5():
    '''
    >>> from music21.figuredBass import part
    >>> partA = part.Part("Bass1", 16, "E2", "E4")
    >>> partB = part.Part("Bass2", 16, "E2", "E4")
    >>> partA > partB 
    True
    '''
    pass

#--------------------------------------------------
# VI. possibility.py

def possibilityExample1():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> Ddim7 = possibility.Possibility({p1: "B-4", p2: "E4", p3: "G3", p4: "C#3"})
    >>> print(Ddim7)
    {1: B-4, 2: E4, 3: G3, 4: C#3}
    '''
    pass

def possibilityExample2():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> Ddim7 = possibility.Possibility()
    >>> Ddim7[p1] = "B-4"
    >>> Ddim7[p2] = "E4"
    >>> Ddim7[p3] = "G3"
    >>> Ddim7[p4] = "C#3"
    >>> print(Ddim7)
    {1: B-4, 2: E4, 3: G3, 4: C#3}
    '''
    pass

def possibilityExample3():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> Ddim7 = possibility.Possibility({p1: "B-4", p2: "E4", p3: "G3", p4: "C#3"})
    >>> print(Ddim7)
    {1: B-4, 2: E4, 3: G3, 4: C#3}
    >>> Ddim7.numParts()
    4
    >>> Ddim7.lowestPart()
    <music21.figuredBass.part Part 4: A0->C8>
    >>> Ddim7.highestPitch()
    B-4
    '''
    pass

def possibilityExample4():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> possibA1 = possibility.Possibility({p1: "C5", p2: "G4", p3: "C4", p4: "C3"})
    >>> possibA2 = possibility.Possibility({p1: "C5", p2: "G4", p3: "E3", p4: "C3"})
    >>> possibA1.isIncomplete(["C", "E", "G"])
    True
    >>> possibA2.isIncomplete(["C", "E", "G"])
    False
    '''
    pass

def possibilityExample5():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> possibA1 = possibility.Possibility({p1: "C5", p2: "G4", p3: "C4", p4: "C3"})
    >>> possibA2 = possibility.Possibility({p1: "C5", p2: "G4", p3: "E3", p4: "C3"})
    >>> possibA1.upperPartsWithinLimit()
    True
    >>> possibA2.upperPartsWithinLimit()
    False
    '''
    pass

def possibilityExample6():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> S = part.Part("Soprano", 2, "C4", "A5")
    >>> T = part.Part("Tenor", 12, "C3", "A4")
    >>> B = part.Part("Bass", 12, "E2", "E4")
    >>> possibA1 = possibility.Possibility({S: "C5", T: "G4", B: "C3"})
    >>> possibA1.pitchesWithinRange()
    True
    
    >>> possibA2 = possibility.Possibility({S: "B3", T: "E3", B: "C3"})
    >>> possibA2.pitchesWithinRange()
    False
    '''
    pass
    
def possibilityExample7():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> possibA1 = possibility.Possibility({p1: "C5", p2: "G4", p3: "C4", p4: "C3"})
    >>> possibA1.voiceCrossing()
    False
    >>> possibA2 = possibility.Possibility({p1: "C5", p2: "E4", p3: "G4", p4: "C3"})
    >>> possibA2.voiceCrossing()
    True
    '''
    pass

def possibilityExample8():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> possibA = possibility.Possibility({p3: "G3", p4: "C3"})
    >>> possibB = possibility.Possibility({p3: "A3", p4: "D3"})
    >>> possibA.parallelFifths(possibB)
    True
    '''
    pass

def possibilityExample9():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> possibA = possibility.Possibility({p3: "C4", p4: "C3"})
    >>> possibB = possibility.Possibility({p3: "D4", p4: "D3"})
    >>> possibA.parallelOctaves(possibB)
    True
    '''
    pass

def possibilityExample10():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p4 = part.Part(4)
    >>> possibA = possibility.Possibility({p1: "E5", p4: "C3"})
    >>> possibB = possibility.Possibility({p1: "A5", p4: "D3"})
    >>> possibA.hiddenFifth(possibB)
    True
    '''
    pass

def possibilityExample11():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p4 = part.Part(4)
    >>> possibA = possibility.Possibility({p1: "A5", p4: "C3"})
    >>> possibB = possibility.Possibility({p1: "D6", p4: "D3"})
    >>> possibA.hiddenOctave(possibB)
    True
    '''
    pass

def possibilityExample12():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> possibA1 = possibility.Possibility({p1: "C5", p2: "G4", p3: "E4", p4: "C4"})
    >>> possibB1 = possibility.Possibility({p1: "B4", p2: "F4", p3: "D4"})
    
    >>> possibA1.voiceOverlap(possibB1)
    False
    >>> possibB2 = possibility.Possibility({p1: "F4", p2: "F4"})
    >>> possibA1.voiceOverlap(possibB2)
    True
    >>> possibA1.voiceCrossing(possibB2)
    False
    '''
    pass

def possibilityExample13():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1, 2) #Limited to stepwise motion
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> possibA1 = possibility.Possibility({p1: "C5", p2: "G4", p3: "E4", p4: "C3"})
    >>> possibB1 = possibility.Possibility({p1: "B4", p2: "F4", p3: "D4", p4: "D3"})
    >>> possibA1.partMovementsWithinLimits(possibB1)
    True
    >>> possibB2 = possibility.Possibility({p1: "G4", p3: "D4", p4: "D3"})
    >>> possibA1.partMovementsWithinLimits(possibB2)
    False
    '''
    pass

def possibilityExample14():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> possibA = possibility.Possibility({p3: "G3", p4: "C3"})
    >>> possibB = possibility.Possibility({p3: "A3", p4: "D3"})
    >>> possibA.parallelFifths(possibB, True)
    True 
    
    ...........possibility.py: WARNING: Parallel fifths between 4 and 3 in {3: G3, 4: C3} and {3: A3, 4: D3}
    '''
    pass

def possibilityExample15():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> Ddim7 = possibility.Possibility({p1: "B-4", p2: "E4", p3: "G3", p4: "C#3"})
    >>> Ddim7.chordify()
    <music21.chord.Chord C#3 G3 E4 B-4>
    >>> dim7Chord = Ddim7.chordify(2.0)
    >>> dim7Chord.quarterLength
    2.0
    >>> Ddim7.isDominantSeventh()
    False
    >>> Ddim7.isDiminishedSeventh()
    True
    '''
    pass

def possibilityExample16():
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> possibA = possibility.Possibility({p1: "C5", p4: "C4"})
    >>> possibB = possibility.Possibility({p1: "B4", p3: "D4", p4: "D4"})
    >>> pairsList = possibA.partPairs(possibB)
    >>> len(pairsList)
    2
    >>> pairsList[0]
    (<music21.figuredBass.part Part 4: A0->C8>, C4, D4)
    >>> pairsList[1]
    (<music21.figuredBass.part Part 1: A0->C8>, C5, B4)
    '''
    pass

#--------------------------------------------------
# VII. segment.py

def segmentExample1():
    '''
    >>> from music21.figuredBass import segment
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> from music21.figuredBass import rules
    >>> from music21.figuredBass import realizerScale
    >>> from music21 import note
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> partList = [p1, p2, p3, p4]
    >>> fbScale = realizerScale.FiguredBassScale("D")
    >>> fbRules = rules.Rules()
    >>> bassNote = note.Note("D3")
    >>> startSeg = segment.StartSegment(fbScale, partList, fbRules, bassNote, "5, 3")
    >>> len(startSeg.possibilities) # Number of correctly formed possibilities
    21
    >>> startSeg.possibilities[0]
    <music21.figuredBass.possibility Possibility: {1: A3, 2: F#3, 3: D3, 4: D3}>
    '''
    pass
    
def segmentExample2():
    '''
    >>> from music21.figuredBass import segment
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> from music21.figuredBass import rules
    >>> from music21.figuredBass import realizerScale
    >>> from music21 import note
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> partList = [p1, p2, p3, p4]
    >>> fbScale = realizerScale.FiguredBassScale("D")
    >>> fbRules = rules.Rules()
    >>> bassA = note.Note("D3")
    >>> startSeg = segment.StartSegment(fbScale, partList, fbRules, bassA, "5, 3")
    >>> bassB = note.Note("E3")
    >>> midSeg  = segment.MiddleSegment(fbScale, partList, fbRules,  startSeg, bassB, "6, 3")
    >>> len(midSeg.possibilities) # Number of correctly formed self-contained possibilities
    17
    >>> midSeg.possibilities[0]
    <music21.figuredBass.possibility Possibility: {1: C#4, 2: G3, 3: E3, 4: E3}>
    >>> startSeg.nextMovements[3]
    [0, 1, 2, 4]
    >>> startSeg.possibilities[3]
    <music21.figuredBass.possibility Possibility: {1: D4, 2: A3, 3: F#3, 4: D3}>
    >>> midSeg.possibilities[0]
    <music21.figuredBass.possibility Possibility: {1: C#4, 2: G3, 3: E3, 4: E3}>
    >>> midSeg.possibilities[1]
    <music21.figuredBass.possibility Possibility: {1: C#4, 2: G3, 3: G3, 4: E3}>
    >>> midSeg.possibilities[2]
    <music21.figuredBass.possibility Possibility: {1: C#4, 2: C#4, 3: G3, 4: E3}>
    >>> midSeg.possibilities[4]
    <music21.figuredBass.possibility Possibility: {1: G4, 2: C#4, 3: G3, 4: E3}>
    '''
    pass

def segmentExample3():
    '''
    >>> from music21.figuredBass import segment
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> from music21.figuredBass import rules
    >>> from music21.figuredBass import realizerScale
    >>> from music21 import note
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> partList = [p1, p2, p3, p4]
    >>> fbScale = realizerScale.FiguredBassScale("D")
    >>> fbRules = rules.Rules()
    >>> bassA = note.Note("D3")
    >>> startSeg = segment.StartSegment(fbScale, partList, fbRules, bassA, "5, 3")
    >>> bassB = note.Note("E3")
    >>> midSeg1  = segment.MiddleSegment(fbScale, partList, fbRules,  startSeg, bassB, "6, 3")
    >>> bassC  = note.Note("F#3")
    >>> midSeg2 = segment.MiddleSegment(fbScale, partList, fbRules,  startSeg, bassC, "6, 3")
    >>> midSeg2.trimAllMovements()
    >>> midSeg2.getNumSolutions()
    92
    '''
    pass

#--------------------------------------------------
# VIII. realizer.py

def realizerExample1():
    '''
    >>> from music21.figuredBass import realizer
    >>> from music21 import tinyNotation
    >>> s = tinyNotation.TinyNotationStream('C4 D8_6 E8_6 F4 G4_7 c1', '4/4')
    >>> fbLine1 = realizer.figuredBassFromStream(s)
    >>> fbLine1.realize()
    >>> #_DOCS_SHOW fbLine1.showAllRealizations()
    '''
    pass

def realizerExample2():
    '''
    >>> from music21.figuredBass import realizer
    >>> from music21.figuredBass import part
    >>> from music21 import note
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> partList = [p1, p2, p3, p4]
    >>> fbLine2 = realizer.FiguredBass(partList, "3/4", "D", "major")
    >>> bassNote1 = note.Note("D3")
    >>> bassNote2 = note.Note("E3")
    >>> bassNote3 = note.Note("F#3")
    >>> fbLine2.addElement(bassNote1)         # I
    >>> fbLine2.addElement(bassNote2, "6")     # viio6
    >>> fbLine2.addElement(bassNote3,  "6")     # I6
    >>> fbLine2.realize()
    '''
    pass

def realizerExample3():
    '''
    >>> from music21.figuredBass import realizer
    >>> from music21.figuredBass import part
    >>> from music21 import note
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> partList = [p1, p2, p3, p4]
    >>> fbLine2 = realizer.FiguredBass(partList, "3/4", "D", "major")
    >>> bassNote1 = note.Note("D3")
    >>> bassNote2 = note.Note("E3")
    >>> bassNote3 = note.Note("F#3")
    >>> fbLine2.addElement(bassNote1)        # I
    >>> fbLine2.addElement(bassNote2, "6")    # viio6
    >>> fbLine2.addElement(bassNote3,  "6")    # I6
    >>> fbLine2.realize()
    >>> fbLine2.showRandomRealizations(20)
    >>> allSolsScore = fbLine2.generateAllRealizations()
    >>> #_DOCS_SHOW fbLine2.showRandomRealization()
    '''
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof