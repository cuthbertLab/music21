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
'''This module defines objects for representing key signatures as well as key 
areas. The :class:`~music21.key.KeySignature` is used in 
:class:`~music21.stream.Measure` objects for defining notated key signatures. 
'''

import doctest, unittest
import copy

import music21
from music21 import pitch
from music21 import note
from music21 import interval
from music21 import musicxml
from music21 import common
from music21 import scale

from music21 import environment
_MOD = "key.py"
environLocal = environment.Environment(_MOD)




#-------------------------------------------------------------------------------
def sharpsToPitch(sharpCount):
    '''Given a number a positive/negative number of sharps, return a Pitch 
    object set to the appropriate major key value.

    >>> from music21 import *
    >>> key.sharpsToPitch(1)
    G
    >>> key.sharpsToPitch(1)
    G
    >>> key.sharpsToPitch(2)
    D
    >>> key.sharpsToPitch(-2)
    B-
    >>> key.sharpsToPitch(-6)
    G-
    
    Note that these are :class:`music21.pitch.Pitch` objects not just names:
    
    >>> k1 = key.sharpsToPitch(6)
    >>> k1
    F#
    >>> k1.step
    'F'
    >>> k1.accidental
    <accidental sharp>
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


# store a cache of already-found values
_pitchToSharpsCache = {}

def pitchToSharps(value, mode=None):
    '''Given a pitch or :class:`music21.pitch.Pitch` object, 
    return the number of sharps found in that mode.

    The `mode` parameter can be 'major', 'minor', or most
    of the common church/jazz modes ('dorian', 'mixolydian', etc.)
    but not Locrian yet.
    
    If `mode` is omitted, the default mode is major.

    (extra points to anyone who can find the earliest reference to
    the Locrian mode in print.  David Cohen and I (MSC) have been
    looking for this for years).

    >>> from music21 import *

    >>> key.pitchToSharps('c')
    0
    >>> key.pitchToSharps('c', 'minor')
    -3
    >>> key.pitchToSharps('a', 'minor')
    0
    >>> key.pitchToSharps('d')
    2
    >>> key.pitchToSharps('e-')
    -3
    >>> key.pitchToSharps('a')
    3
    >>> key.pitchToSharps('e', 'minor')
    1
    >>> key.pitchToSharps('f#', 'major')
    6
    >>> key.pitchToSharps('g-', 'major')
    -6
    >>> key.pitchToSharps('c#')
    7
    >>> key.pitchToSharps('g#')
    8
    >>> key.pitchToSharps('e', 'dorian')
    2
    >>> key.pitchToSharps('d', 'dorian')
    0
    >>> key.pitchToSharps('g', 'mixolydian')
    0
    >>> key.pitchToSharps('e-', 'lydian')
    -2
    >>> key.pitchToSharps('e-', 'lydian')
    -2
    >>> key.pitchToSharps('a', 'phrygian')
    -1
    >>> key.pitchToSharps('e', 'phrygian')
    0

    '''

    if common.isStr(value):
        p = pitch.Pitch(value)
    else:
        p = value

    if (p.name, mode) in _pitchToSharpsCache.keys():            
        return _pitchToSharpsCache[(p.name, mode)]


    # start at C and continue in both directions
    sharpSource = [0]
    for i in range(1,13):
        sharpSource.append(i)
        sharpSource.append(-i)

    minorShift = interval.Interval('-m3')
    # these modal values were introduced to translate from ABC key values that
    # include mode specification
    # this value/mapping may need to be dynamically allocated based on other
    # contexts (historical meaning of dorian, for example) in the future
    dorianShift = interval.Interval('M2')
    phrygianShift = interval.Interval('M3')
    lydianShift = interval.Interval('P4')
    mixolydianShift = interval.Interval('P5')

    # note: this may not be the fastest approach
    match = None
    for i in sharpSource:
        pCandidate = sharpsToPitch(i)
        # create relative transpositions based on this pitch for major
        pMinor = pCandidate.transpose(minorShift)

        pDorian = pCandidate.transpose(dorianShift)
        pPhrygian = pCandidate.transpose(phrygianShift)
        pLydian = pCandidate.transpose(lydianShift)
        pMixolydian = pCandidate.transpose(mixolydianShift)

        if mode in [None, 'major']:
            if pCandidate.name == p.name:
                match = i
                break
        elif mode in ['dorian']:
            if pDorian.name == p.name:
                match = i
                break
        elif mode in ['phrygian']:
            if pPhrygian.name == p.name:
                match = i
                break
        elif mode in ['lydian']:
            if pLydian.name == p.name:
                match = i
                break
        elif mode in ['mixolydian']:
            if pMixolydian.name == p.name:
                match = i
                break
        elif mode in ['minor', 'aeolian']:
        #else: # match minor pitch
            if pMinor.name == p.name:
                match = i
                break

    _pitchToSharpsCache[(p.name, mode)] = match
    return match


class KeySignatureException(Exception):
    pass

#-------------------------------------------------------------------------------




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

    classSortOrder = 2
    
    def __init__(self, sharps=None, mode=None):
        '''
        >>> from music21 import *

        >>> a = key.KeySignature(3)
        >>> a
        <music21.key.KeySignature of 3 sharps>
        '''
        music21.Music21Object.__init__(self)
        # position on the circle of fifths, where 1 is one sharp, -1 is one flat
        self._sharps = sharps
        # optionally store mode, if known
        self._mode = mode
        # need to store a list of pitch objects, used for creating a 
        # non traditional key
        self._alteredPitches = None

        # cache altered pitches
        self._alteredPitchesCached = []

    #---------------------------------------------------------------------------
    def _attributesChanged(self):
        '''Clear the altered pitches cache
        '''
        self._alteredPitchesCached = []


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

    def __str__(self):
        # string representation needs to be complete, as is used
        # for metadata comparisons
        return "sharps %s, mode %s" % (self.sharps, self.mode)
        

    def _getPitchAndMode(self):
        '''Returns a a two value list containing 
        a :class:`music21.pitch.Pitch` object that 
        names this key and the value of :attr:`~music21.key.KeySignature.mode`.

        >>> from music21 import *
       
        >>> key.KeySignature(-7).pitchAndMode
        (C-, None)
        >>> key.KeySignature(-6).pitchAndMode
        (G-, None)
        >>> key.KeySignature(-3).pitchAndMode
        (E-, None)
        >>> key.KeySignature(0).pitchAndMode
        (C, None)
        >>> key.KeySignature(1).pitchAndMode
        (G, None)
        >>> csharp = key.KeySignature(4)
        >>> csharp.mode = "minor"
        >>> csharp.pitchAndMode
        (C#, 'minor')
        >>> csharpPitch = csharp.pitchAndMode[0]
        >>> csharpPitch.accidental
        <accidental sharp>
        '''
        # this works but returns sharps
        # keyPc = (self.sharps * 7) % 12
        if self.mode is not None and self.mode.lower() == 'minor':
            pitchObj = sharpsToPitch(self.sharps + 3)
        else:
            pitchObj = sharpsToPitch(self.sharps)
        return pitchObj, self.mode

    pitchAndMode = property(_getPitchAndMode)


    def _getAlteredPitches(self):
        if self._alteredPitchesCached: # if list not empty
            #environLocal.printDebug(['using cached altered pitches'])
            return self._alteredPitchesCached

        post = []
        if self.sharps > 0:
            pKeep = pitch.Pitch('B')
            if self.sharps > 8:
                pass
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

        # assign list to altered pitches; list will be empty if not set
        self._alteredPitchesCached = post
        return post


    alteredPitches = property(_getAlteredPitches, 
        doc='''
        Return a list of music21.pitch.Pitch objects that are altered by this 
        KeySignature. That is, all Pitch objects that will receive an accidental.  

        >>> from music21 import *

        >>> a = key.KeySignature(3)
        >>> a.alteredPitches
        [F#, C#, G#]
        >>> b = key.KeySignature(1)
        >>> b.alteredPitches
        [F#]

        >>> c = key.KeySignature(9)
        >>> c.alteredPitches
        [F#, C#, G#, D#, A#, E#, B#, F##, C##]

        >>> d = key.KeySignature(-3)
        >>> d.alteredPitches
        [B-, E-, A-]

        >>> e = key.KeySignature(-1)
        >>> e.alteredPitches
        [B-]

        >>> f = key.KeySignature(-6)
        >>> f.alteredPitches
        [B-, E-, A-, D-, G-, C-]

        >>> g = key.KeySignature(-8)
        >>> g.alteredPitches
        [B-, E-, A-, D-, G-, C-, F-, B--]
        ''')

    def accidentalByStep(self, step):
        '''
        given a step (C, D, E, F, etc.) return the accidental
        for that note in this key (using the natural minor for minor)
        or None if there is none.

        >>> from music21 import *
        
        >>> g = key.KeySignature(1)
        >>> g.accidentalByStep("F")
        <accidental sharp>
        >>> g.accidentalByStep("G")

        >>> f = KeySignature(-1)
        >>> bbNote = note.Note("B-5")
        >>> f.accidentalByStep(bbNote.step)
        <accidental flat>     


        Fix a wrong note in F-major:

        
        >>> wrongBNote = note.Note("B#4")
        >>> if f.accidentalByStep(wrongBNote.step) != wrongBNote.accidental:
        ...    wrongBNote.accidental = f.accidentalByStep(wrongBNote.step)
        >>> wrongBNote
        <music21.note.Note B->
       

        Set all notes to the correct notes for a key using the note's Context:        
        
        
        >>> from music21 import *
        >>> s1 = stream.Stream()
        >>> s1.append(key.KeySignature(4))  # E-major or C-sharp-minor
        >>> s1.append(note.HalfNote("C"))
        >>> s1.append(note.HalfNote("E-"))
        >>> s1.append(key.KeySignature(-4)) # A-flat-major or F-minor
        >>> s1.append(note.WholeNote("A"))
        >>> s1.append(note.WholeNote("F#"))
        >>> for n in s1.notes:
        ...    n.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.step)
        >>> #_DOCS_SHOW s1.show()

        .. image:: images/keyAccidentalByStep.*
            :width: 400

        OMIT_FROM_DOCS
        >>> s1.show('text')
        {0.0} <music21.key.KeySignature of 4 sharps>
        {0.0} <music21.note.Note C#>
        {2.0} <music21.note.Note E>
        {4.0} <music21.key.KeySignature of 4 flats>
        {4.0} <music21.note.Note A->
        {8.0} <music21.note.Note F>
        
        
        Test to make sure there are not linked accidentals (fixed bug 22 Nov. 2010)
        
        >>> nB1 = note.WholeNote("B")
        >>> nB2 = note.WholeNote("B")
        >>> s1.append(nB1)
        >>> s1.append(nB2)
        >>> for n in s1.notes:
        ...    n.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.step)
        >>> (nB1.accidental, nB2.accidental)
        (<accidental flat>, <accidental flat>)
        >>> nB1.accidental.name = 'sharp'
        >>> (nB1.accidental, nB2.accidental)
        (<accidental sharp>, <accidental flat>)
        
        '''
        for thisAlteration in reversed(self.alteredPitches):  # temp measure to fix dbl flats, etc.
            if thisAlteration.step.lower() == step.lower():
                return copy.deepcopy(thisAlteration.accidental) # get a new one each time otherwise we have linked accidentals, YUK!
        
        return None


    #---------------------------------------------------------------------------
    # properties
    def transpose(self, value, inPlace=False):
        '''
        Transpose the KeySignature by the user-provided value. 
        If the value is an integer, the transposition is treated 
        in half steps. If the value is a string, any Interval string 
        specification can be provided. Alternatively, a 
        :class:`music21.interval.Interval` object can be supplied.

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
        post._attributesChanged()

        # mode is already set
        if not inPlace:
            return post
        else:
            return None



    def getScale(self):
        '''Return a scale that is representative of this key.

        >>> from music21 import *
        >>> ks = key.KeySignature(3)
        >>> ks
        <music21.key.KeySignature of 3 sharps>
        >>> ks.getScale()
        <music21.scale.MajorScale A major>
        '''
        from music21 import scale
        pitchObj, mode = self._getPitchAndMode()
        if mode in [None, 'major']:
            return scale.MajorScale(pitchObj)
        elif mode in ['minor']:
            return scale.MinorScale(pitchObj)
        else:
            raise KeySignatureException('not mapping for this mode yet: %s' % mode)

    #---------------------------------------------------------------------------
    # properties


    def _getSharps(self):
        return self._sharps

    def _setSharps(self, value):
        if value != self._sharps:
            self._sharps = value
            self._attributesChanged()

    sharps = property(_getSharps, _setSharps, 
        doc = '''Get or set the number of sharps.
        ''')


    def _getMode(self):
        return self._mode

    def _setMode(self, value):
        if value != self._mode:
            self._mode = value
            self._attributesChanged()

    mode = property(_getMode, _setMode,
        doc = '''Get or set the mode.
        ''')




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
        if not common.isListLike(mxKeyList):
            mxKey = mxKeyList
        else: # there may be more than one if we have more staffs per part
            mxKey = mxKeyList[0]

        self.sharps = int(mxKey.get('fifths'))
        mxMode = mxKey.get('mode')
        if mxMode != None:
            self.mode = mxMode

    mx = property(_getMX, _setMX)

    def _getLily(self):
        (p, m) = self.pitchAndMode
        if m is None:
            m = "major"
        pn = p.lilyNoOctave()
        return r'\key ' + pn + ' \\' + m
    
    lily = property(_getLily, doc = r'''
        returns the Lilypond representation of a KeySignature object
        
        >>> from music21 import *
        >>> d = key.KeySignature(-1)
        >>> d.mode = 'minor'
        >>> print d.lily
        \key d \minor
        
        Major is assumed:
        
        >>> fsharp = key.KeySignature(6)
        >>> print fsharp.lily
        \key fis \major
    ''')


    #---------------------------------------------------------------------------
    # override these methods for json functionality
    # not presently in use

#     def jsonAttributes(self):
#         '''Define all attributes of this object that should be JSON serialized for storage and re-instantiation. Attributes that name basic Python objects or :class:`~music21.base.JSONSerializer` subclasses, or dictionaries or lists that contain Python objects or :class:`~music21.base.JSONSerializer` subclasses, can be provided.
#         '''
#         # only string notation is stored, meaning that any non-default
#         # internal representations will not be saved
#         # a new default will be created when restored
#         return ['sharps', 'mode', '_alteredPitches']
# 
# 
#     def jsonComponentFactory(self, idStr):
#         '''Given a stored string during JSON serialization, return an object'
# 
#         The subclass that overrides this method will have access to all modules necessary to create whatever objects necessary. 
#         '''
#         return None



# some ideas
# c1 = chord.Chord(["D", "F", "A"])
# k1 = key.Key("C")
# c2 = k1.chordFromRomanNumeral("ii")
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


class Key(KeySignature, scale.DiatonicScale):
    '''
    Note that a key is a sort of hypothetical/conceptual object.
    It probably has a scale (or scales) associated with it and a KeySignature,
    but not necessarily.

    EXPERIMENTAL


    >>> from music21 import *
    >>> cm = key.Key('c')  # cminor.
    >>> cm
    <music21.key.Key of c minor>
    >>> cm.sharps
    -3
    >>> cm.pitchFromDegree(3)
    E-4
    >>> cm.pitchFromDegree(7)
    B-4

    >>> Csharpmaj = key.Key('C#')
    >>> Csharpmaj
    <music21.key.Key of C# major>

    '''
    _sharps = 0
    _mode = None
    def __init__(self, tonic = None, mode = None):
        if tonic is not None:
            if mode is None:
                if 'm' in tonic:
                    mode = 'minor'
                    tonic = re.sub('m', '', tonic)
                elif 'M' in tonic:
                    mode = 'major'
                    tonic = re.sub('M', '', tonic)
                elif tonic.lower() == tonic:
                    mode = 'minor'
                else:
                    mode = 'major'
            sharps = pitchToSharps(tonic, mode)
            KeySignature.__init__(self, sharps, mode)

        scale.DiatonicScale.__init__(self, tonic=tonic)
        self.tonic = tonic
        self.type = mode
        self.mode = mode
        # build the network for the appropriate scale
        self._abstract._buildNetwork(self.type)

    def __repr__(self):
        return "<music21.key.Key of %s>" % self.__str__()

    def __str__(self):
        # string representation needs to be complete, as is used
        # for metadata comparisons
        return "%s %s" % (self.tonic, self.mode)




#-------------------------------------------------------------------------------
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


    def testBasic(self):
        a = KeySignature()
        self.assertEqual(a.sharps, None)




#     def testJSONStorage(self):
#         ks = KeySignature(3)
#         # cannot test to json str as __class__ is different based on context 
#         #self.assertEqual(ks.json, '{"__attr__": {"sharps": 3}, "__version__": [0, 3, 0], "__class__": "<class \'__main__.KeySignature\'>"}')
# 
#         jsonStr = ks.json
#     
#         ksNew = KeySignature()
#         ksNew.json = jsonStr
# 
#         self.assertEqual(ksNew._strDescription(), '3 sharps')
#         

#         jsString = ts.json
#         ts = TimeSignature()
#         ts.json = jsString
#         self.assertEqual(ts.stringNotation, '3/4')



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [KeySignature, Key]


if __name__ == "__main__":
    music21.mainTest(Test)





#------------------------------------------------------------------------------
# eof

