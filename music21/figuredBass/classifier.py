'''
From talking to Myke on 2/10, it seems that Chris has come up with a better
way of classifying chords by roman numeral, one which also does modulations.
That might mean that this class is "outdated," but I'll upload it anyways,
in case it contains some useful code.
-------------------------------------
Original ideas for class, NOT a tutorial:

Write some code that given a chord or a list of pitches, can provide a roman 
numeral string or object that corresponds to it in a given key. Would be great
if it could detect modulations as well, and point out a pivot chord.

[B3, D4, F4] vii

Translate a chord to Roman Numeral

Check if each pitch is in scale.

For example, if in C major,

[C3, E3, G3] is in scale.
[D3, F#3, A3] is not.

chord.Chord(['C3','E3','G3']) #Define chord
c.pitches.sort() #Sort pitches
removeRedundantPitchClasses() 
check if each "pitch class" is present
determine triad/seventh
call findRoot() (not root) to find root of chord.

sort by distance to key. On the circle of fifths maybe?
'''
import music21
import unittest
import copy

from music21 import chord
from music21 import scale
from music21 import common
from music21 import roman
from music21 import key
from music21 import pitch

def getRomanNumeral(samplePitches, inKey, recurse=True):
    '''
    >>> from music21 import *
    >>> dimChord = ['D3', 'F3', 'B3']
    >>> inKey = key.Key('C')
    >>> getRomanNumeral(dimChord, inKey)
    'viio6'
    >>> dom43 = ['D3','F3','G3','B3']
    >>> getRomanNumeral(dom43, inKey)
    'V43'
    >>> inKey = key.Key('c')
    >>> inKey.type
    'minor'
    >>> getRomanNumeral(dom43, inKey)
    'V43 | C major'
    '''
    sampleChord = chord.Chord(samplePitches) #Define chord
    sampleChord = copy.deepcopy(sampleChord)
    sampleChord.pitches.sort() #Sort pitches
    sampleChord.removeRedundantPitchClasses()

    pitchesInScale = inKey.getPitches(sampleChord.pitches[0], sampleChord.pitches[len(sampleChord.pitches) - 1])

    chordInScale = True
    for samplePitch in sampleChord.pitches:
        if not samplePitch in pitchesInScale:
            chordInScale = False
            break
    
    if chordInScale:
        #tonicCopy = copy.deepcopy(inKey.getTonic())
        #while tonicCopy > sampleChord.findRoot():
        #    tonicCopy.transpose('-P8', True)
        rn = common.toRoman(inKey.getScaleDegreeFromPitch(sampleChord.findRoot()))
        if sampleChord.isTriad():
            if sampleChord.isMajorTriad():
                rn = rn.upper()
            elif sampleChord.isMinorTriad():
                rn = rn.lower()
            elif sampleChord.isDiminishedTriad():
                rn = rn.lower() + 'o'
            elif sampleChord.isAugmentedTriad():
                rn = rn.upper() + '+'
        elif sampleChord.isSeventh():
            if sampleChord.isDominantSeventh():
                rn = rn.upper()
            elif sampleChord.isDiminishedSeventh():
                rn = rn.lower() + 'o'
            elif sampleChord.isHalfDiminishedSeventh():
                rn = rn.lower() + '/o'
        if not (sampleChord.inversionName() == None or sampleChord.inversionName() == 53):
            rn = rn + str(sampleChord.inversionName())
        #newKey = key.Key(tonicCopy, inKey.type)
        #v = roman.RomanNumeral(rn, newKey)
        return rn
    elif recurse:
        if inKey.type == 'major':
            rn = getRomanNumeral(samplePitches, inKey.getParallelMinor(), False)
            if not rn == None:
                return rn + ' | ' + inKey.getParallelMinor().name
        elif inKey.type == 'minor':
            rn = getRomanNumeral(samplePitches, inKey.getParallelMajor(), False)
            if not rn == None:
                return rn + ' | ' + inKey.getParallelMajor().name


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof