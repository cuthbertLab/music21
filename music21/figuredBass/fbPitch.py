import music21
import unittest

from music21 import pitch

class HashablePitch(pitch.Pitch):
    def __init__(self, name=None, **keywords):
        '''
        A HashablePitch takes on identical properties as a :class:`~music21.pitch.Pitch`.
        It only defines a hash function, such that two identical HashablePitch instances 
        hash to the same thing. This is not the case for two identical Pitch instances.
        
        
        Internally, fbRealizer uses HashablePitch instances in place of Pitch instances,
        to allow possibilities (see :mod:`~music21.figuredBass.possibility`) to be used 
        as dictionary keys for movements between :class:`~music21.figuredBass.segment.Segment`
        instances.
        
        >>> from music21.figuredBass import fbPitch
        >>> from music21 import pitch
        >>> h1 = fbPitch.HashablePitch('G4')
        >>> p1 = pitch.Pitch('G4')
        >>> h1 == p1
        True
        >>> h2 = fbPitch.HashablePitch('G4')
        >>> p2 = pitch.Pitch('G4')
        >>> hash(h1) == hash(h2)
        True
        >>> hash(p1) == hash(p2)
        False
        '''
        pitch.Pitch.__init__(self, name, **keywords)
        
    def __hash__(self):
        return hash(self.fullName)
    

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof