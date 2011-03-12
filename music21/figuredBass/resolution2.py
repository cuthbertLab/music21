import music21
import copy 
import unittest

from music21 import chord
from music21 import pitch
from music21 import interval

from music21.figuredBass import possibility

def dominantSeventhToMajorTonic(dominantPossib, inPlace = False):
    '''
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': pitch.Pitch('G2'), 'T': pitch.Pitch('B3'), 'A': pitch.Pitch('F4'), 'S': pitch.Pitch('D5')})
    >>> resolution2.dominantSeventhToMajorTonic(possibA)
    {'A': E4, 'S': C5, 'B': C3, 'T': C4}
    >>> possibB = possibility.Possibility({'B': pitch.Pitch('C3'), 'T': pitch.Pitch('E3'), 'A': pitch.Pitch('G3'), 'S': pitch.Pitch('B-3')})
    >>> resolution2.dominantSeventhToMajorTonic(possibB)
    {'A': F3, 'S': A3, 'B': F3, 'T': F3}
    '''
    if inPlace:
        dpCopy = dominantPossib
    else:
        dpCopy = copy.copy(dominantPossib)
    
    V7chord = dpCopy.chordify()
    if not V7chord.isDominantSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled dominant seventh chord.")
    
    root = V7chord.root()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('M3')).name
    fifthName = root.transpose(interval.Interval('P5')).name
    seventhName = root.transpose(interval.Interval('m7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isRoot = (samplePitch == root)
        if samplePitch.name == rootName:
            if isRoot:
                samplePitch.transpose('P4', True)
        elif samplePitch.name == thirdName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == fifthName:
            samplePitch.transpose('-M2', True)
        elif samplePitch.name == seventhName:
            samplePitch.transpose('-m2', True)
        
    return dpCopy

def dominantSeventhToMinorTonic(dominantPossib, inPlace = False):
    '''
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': pitch.Pitch('G2'), 'T': pitch.Pitch('B3'), 'A': pitch.Pitch('F4'), 'S': pitch.Pitch('D5')})
    >>> resolution2.dominantSeventhToMinorTonic(possibA)
    {'A': E-4, 'S': C5, 'B': C3, 'T': C4}
    >>> possibB = possibility.Possibility({'B': pitch.Pitch('C3'), 'T': pitch.Pitch('E3'), 'A': pitch.Pitch('G3'), 'S': pitch.Pitch('B-3')})
    >>> resolution2.dominantSeventhToMinorTonic(possibB)
    {'A': F3, 'S': A-3, 'B': F3, 'T': F3}
    '''
    dpCopy = copy.copy(dominantPossib)
    V7chord = dpCopy.chordify()
    
    if not V7chord.isDominantSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled dominant seventh chord.")
    
    root = V7chord.root()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('M3')).name
    fifthName = root.transpose(interval.Interval('P5')).name
    seventhName = root.transpose(interval.Interval('m7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isRoot = (samplePitch == root)
        if samplePitch.name == rootName:
            if isRoot:
                samplePitch.transpose('P4', True)
        elif samplePitch.name == thirdName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == fifthName:
            samplePitch.transpose('-M2', True)
        elif samplePitch.name == seventhName:
            samplePitch.transpose('-M2', True)
        
    return dpCopy


class ResolutionException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

