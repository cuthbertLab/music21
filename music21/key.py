#-------------------------------------------------------------------------------
# Name:         key.py
# Purpose:      Classes for keys
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
import doctest, unittest
import copy

import music21
from music21 import pitch
from music21 import note
from music21 import interval
from music21 import musicxml
from music21 import common


#-------------------------------------------------------------------------------
def sharpsToPitch(sharpCount):
    '''Given a number a positive/negative number of sharps, return a Pitch object set to the appropriate major key value.

    >>> sharpsToPitch(1)
    G
    >>> sharpsToPitch(1)
    G
    >>> sharpsToPitch(2)
    D
    >>> sharpsToPitch(-2)
    B-
    >>> sharpsToPitch(-6)
    G-
    >>> sharpsToPitch(6)
    F#
    '''
    pitchInit = pitch.Pitch('C')
    pitchInit.octave = None
    # keyPc = (self.sharps * 7) % 12
    if sharpCount > 0:
        intervalStr = 'P5'
    elif sharpCount < 0:
        intervalStr = 'P-5'
    else:
        return pitchInit # C

    intervalObj = interval.Interval(intervalStr)
    for x in range(abs(sharpCount)):
        pitchInit = intervalObj.transposePitch(pitchInit)    
    pitchInit.octave = None
    return pitchInit



def pitchToSharps(value, mode=None):
    '''Given a pitch or :class:`music21.pitch.Pitch` object, return the number of sharps found in the major key.

    The `mode` parameter can be None, 'major', or 'minor'.

    >>> pitchToSharps('c')
    0
    >>> pitchToSharps('c', 'minor')
    -3
    >>> pitchToSharps('a', 'minor')
    0
    >>> pitchToSharps('d')
    2
    >>> pitchToSharps('e-')
    -3
    >>> pitchToSharps('a')
    3
    >>> pitchToSharps('e', 'minor')
    1
    >>> pitchToSharps('f#', 'major')
    6
    >>> pitchToSharps('g-', 'major')
    -6
    >>> pitchToSharps('c#')
    7
    >>> pitchToSharps('g#')
    8
    '''
    if common.isStr(value):
        p = pitch.Pitch(value)
    else:
        p = value
    # start at C and continue in both directions
    sharpSource = [0]
    for i in range(1,13):
        sharpSource.append(i)
        sharpSource.append(-i)

    minorShift = interval.Interval('-m3')

    # NOTE: this may not be the fastest approach
    match = None
    for i in sharpSource:
        pCandidate = sharpsToPitch(i)
        if mode in [None, 'major']:
            if pCandidate.name == p.name:
                match = i
                break
        else: # match minor pitch
            pMinor = pCandidate.transpose(minorShift)
            if pMinor.name == p.name:
                match = i
                break
    return match


class KeySignatureException(Exception):
    pass

#-------------------------------------------------------------------------------

# some ideas
# c1 = chord.Chord(["D", "F", "A"])
# k1 = key.Key("C")
# c2 = k1.chordByRoman("ii")
# c1 == c2
# True

# 
# key1 = Key("E", "major")
# key1
# <music21.key.Key E major>
# key1.parallel
# <music21.key.Key E minor>
# key1.relative
# <music21.key.Key c# minor>
# 
# ks1 = key1.signature
# ks1
# <music21.key.KeySignature 4 sharps>
# ks1.sharpsOrFlats
# 4
# ks1.majorKey
# <music21.key.Key E major>
# ks1.minorKey
# <music21.key.Key c# minor>
# 
# # Set this E major piece to use a signature of 1 flat
# key1.signature = KeySignature(-1)
# 
# # Check that it's still E major
# key1
# <music21.key.Key E major>
# key1.signature
# <music21.key.KeySignature 1 flat>
# key1.sharpsOrFlats
# -1
# 
# # What major key would normally have this signature?
# key1.signature.majorKey
# <music21.key.Key F major>
# 
# # Modal piece in E
# key2 = Key("E", None)
# key2
# <music21.key.Key E >
# key2.signature
# <music21.key.KeySignature natural>

class Key(music21.Music21Object):
    '''
    Note that a key is a sort of hypothetical/conceptual object.
    It probably has a scale (or scales) associated with it and a KeySignature,
    but not necessarily.
    '''
    
    def __init__(self, stream1 = None):
        self.stream1 = stream1
        self.step = ''
        self.accidental = ''
        self.type = ''

        self.stepList = music21.pitch.STEPNAMES

        # this information might be better dervied from somewhere in 
        # note.py
        self.accidentalList = ['--', '-', None, '#', '##']
        self.typeList = ['major', 'minor']

    def generateKey(self):
        # want to use Krumhansl-Kessler algorithm; need to find explicit instructions
        pass

    def setKey(self, name = "C", accidental = None, type = "major"):
        self.step = name
        self.accidental = accidental
        self.type = type


def keyFromString(strKey):
    '''Given a string representing a key, return the appropriate Key object. 
    '''
    #TODO: Write keyFromString
    return None
    #raise KeyException("keyFromString not yet written")







#-------------------------------------------------------------------------------
class KeySignature(music21.Music21Object):

    # note that musicxml permits non-tradtional keys by specifying
    # one or more altered tones; these are given as pairs of 
    # step names and semiton alterations

    def __init__(self, sharps = None):
        '''
        >>> a = KeySignature(3)
        >>> a._strDescription()
        '3 sharps'
        '''
        music21.Music21Object.__init__(self)
        # position on the circle of fifths, where 1 is one sharp, -1 is one flat
        self.sharps = sharps
        # optionally store mode, if known
        self.mode = None
        # need to store a list of pitch objects, used for creating a 
        # non traditional key
        self._alteredPitches = None

    #---------------------------------------------------------------------------
    def _strDescription(self):
        ns = self.sharps
        if ns == None:
            return 'None'
        elif ns > 1:
            return "%s sharps" % str(ns)
        elif ns == 1:
            return "1 sharp"
        elif ns == 0:
            return "no sharps or flats"
        elif ns == -1:
            return "1 flat"
        else:
            return "%s flats" % str(abs(ns))
        
    def __repr__(self):
        return "<music21.key.KeySignature of %s>" % self._strDescription()
        

    def _getPitchAndMode(self):
        '''Returns a a two value list containg a :class:`music21.pitch.Pitch` object that names this key and the value of :attr:`~music21.key.KeySignature.mode`.
       
        >>> keyArray = [KeySignature(x) for x in range(-7,8)]
        >>> keyArray[0].pitchAndMode
        (C-, None)
        >>> keyArray[1].pitchAndMode
        (G-, None)
        >>> keyArray[2].pitchAndMode
        (D-, None)
        >>> keyArray[3].pitchAndMode
        (A-, None)
        >>> keyArray[4].pitchAndMode
        (E-, None)
        >>> keyArray[5].pitchAndMode
        (B-, None)
        >>> keyArray[6].pitchAndMode
        (F, None)
        >>> keyArray[7].pitchAndMode
        (C, None)
        >>> keyArray[8].pitchAndMode
        (G, None)
        '''
        # this works but returns sharps
        # keyPc = (self.sharps * 7) % 12
        pitchObj = sharpsToPitch(self.sharps)
        return pitchObj, self.mode

    pitchAndMode = property(_getPitchAndMode)


    def _getAlteredPitches(self):
        '''Return a list of pitches that are altered with this KeySignature. That is, all Pitch objects that will receive an accidental. 
        '''
        post = []
        if self.sharps > 0:
            pKeep = pitch.Pitch('B')
            for i in range(self.sharps):
                pKeep.transpose('P5', inPlace=True)
                p = copy.deepcopy(pKeep)
                p.octave = None
                post.append(p)

        elif self.sharps < 0:
            pKeep = pitch.Pitch('F')
            for i in range(abs(self.sharps)):
                pKeep.transpose('P4', inPlace=True)
                p = copy.deepcopy(pKeep)
                p.octave = None
                post.append(p)
        return post


    alteredPitches = property(_getAlteredPitches, 
        doc='''Return a list of pitches that are altered with this KeySignature. That is, all Pitch objects that will receive an accidental. 

        >>> a = KeySignature(3)
        >>> a.alteredPitches
        [F#, C#, G#]
        >>> a = KeySignature(1)
        >>> a.alteredPitches
        [F#]

        >>> a = KeySignature(9)
        >>> a.alteredPitches
        [F#, C#, G#, D#, A#, E#, B#, F##, C##]

        >>> a = KeySignature(-3)
        >>> a.alteredPitches
        [B-, E-, A-]

        >>> a = KeySignature(-1)
        >>> a.alteredPitches
        [B-]

        >>> a = KeySignature(-6)
        >>> a.alteredPitches
        [B-, E-, A-, D-, G-, C-]

        >>> a = KeySignature(-8)
        >>> a.alteredPitches
        [B-, E-, A-, D-, G-, C-, F-, B--]
        ''')

    #---------------------------------------------------------------------------
    # properties
    def transpose(self, value, inPlace=False):
        '''Tranpose the KeySignature by the user-provided value. If the value is an integer, the transposition is treated in half steps. If the value is a string, any Interval string specification can be provided. Alternatively, a :class:`music21.interval.Interval` object can be supplied.

        >>> a = KeySignature(2)
        >>> a.pitchAndMode
        (D, None)
        >>> b = a.transpose('p5')
        >>> b.pitchAndMode
        (A, None)
        >>> b.sharps
        3
        >>> c = b.transpose('-m2')
        >>> c.pitchAndMode
        (G#, None)
        >>> c.sharps
        8
        
        >>> d = c.transpose('-a3')
        >>> d.pitchAndMode
        (E-, None)
        >>> d.sharps
        -3
        '''
        if hasattr(value, 'diatonic'): # its an Interval class
            intervalObj = value
        else: # try to process
            intervalObj = interval.Interval(value)

        if not inPlace:
            post = copy.deepcopy(self)
        else:
            post = self

        p1, mode = post._getPitchAndMode()
        p2 = p1.transpose(intervalObj)
        
        post.sharps = pitchToSharps(p2, mode)
        # mode is already set
        if not inPlace:
            return post
        else:
            return None


    #---------------------------------------------------------------------------
    # properties

    def _getMX(self):
        '''Returns a musicxml.KeySignature object
       
        >>> a = KeySignature(3)
        >>> a.sharps = -3
        >>> mxKey = a.mx
        >>> mxKey.get('fifths')
        -3
        '''
        mxKey = musicxml.Key()
        mxKey.set('fifths', self.sharps)
        if self.mode != None:
            mxKey.set('mode', self.mode)
        return mxKey


    def _setMX(self, mxKeyList):
        '''Given a mxKey object or keyList, load internal attributes
        >>> a = musicxml.Key()
        >>> a.set('fifths', 5)
        >>> b = KeySignature()
        >>> b.mx = [a]
        >>> b.sharps
        5 
        '''
        if len(mxKeyList) == 1:
            mxKey = mxKeyList[0]
        else:
            raise KeySignatureException('found a key from MusicXML that has more than one key defined')

        self.sharps = int(mxKey.get('fifths'))
        mxMode = mxKey.get('mode')
        if mxMode != None:
            self.mode = mxMode

    mx = property(_getMX, _setMX)




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
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


    def testBasic(self):
        a = KeySignature()
        self.assertEqual(a.sharps, None)





#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [KeySignature, Key]


if __name__ == "__main__":
    music21.mainTest(Test)





