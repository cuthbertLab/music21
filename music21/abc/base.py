#-------------------------------------------------------------------------------
# Name:         abc.base.py
# Purpose:      music21 classes for dealing with abc data
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Objects and tools for processing ABC data. 

'''

import music21
import unittest
import re

try:
    import StringIO # python 2 
except:
    from io import StringIO # python3 (also in python 2.6+)


from music21 import common
from music21 import environment
_MOD = 'abc.base.py'
environLocal = environment.Environment(_MOD)

# for implementation
# see http://abcnotation.com/abc2mtex/abc.txt

# store symbol and m21 naming/class eq
ABC_BARS = [
           ('|]', 'thin-thick double bar line'),
           ('||', 'thin-thin double bar line'),
           ('[|', 'thick-thin double bar line'),
           ('[1', 'first repeat'),
           ('[2', 'second repeat'),
           (':|', 'left repeat'),
           ('|:', 'right repeat'),
           ('::', 'left-right repeat'),
            # for comparison, single chars must go last
           ('|', 'bar line'),
           ]

#-------------------------------------------------------------------------------
reMetadataTag = re.compile('[A-Z]:')

rePitchName = re.compile('[a-gA-Gz]')

reChordSymbol = re.compile('"[^"]*"') # non greedy

reChord = re.compile('[.*?]') # non greedy

#-------------------------------------------------------------------------------
class ABCTokenException(Exception):
    pass

class ABCHandlerException(Exception):
    pass


#-------------------------------------------------------------------------------
class ABCToken(object):
    def __init__(self, src=''):
        self.src = src # store source character sequence

    def __repr__(self):
        return '<ABCToken %r>' % self.src

    def stripComment(self, strSrc):
        '''
        removes ABC-style comments from a string:
        
        >>> ao = ABCToken()
        >>> ao.stripComment('asdf')
        'asdf'
        >>> ao.stripComment('asdf%234')
        'asdf'
        >>> ao.stripComment('asdf  %     234')
        'asdf  '
        
        >>> ao.stripComment('[ceg]% this chord appears 50% more often than other chords do')
        '[ceg]'
        '''
        if '%' in strSrc:
            return strSrc.split('%')[0] #
        return strSrc
    
    def preParse(self):
        '''Called before context adjustments. 
        '''
        pass

    def parse(self): 
        '''Read self.src and load attributes. Customize in subclasses.
        Called after context adjustments
        '''
        pass


class ABCMetadata(ABCToken):

    # given a logical unit, create an object
    # may be a chord, notes, metadata, bars
    def __init__(self, src):
        ABCToken.__init__(self, src)
        self.tag = None
        self.data = None

    def __repr__(self):
        return '<ABCMetadata %r>' % self.src

    def preParse(self):
        '''Called before context adjustments: need to have access to data
        '''
        div = reMetadataTag.match(self.src).end()
        strSrc = self.stripComment(self.src) # remove any comments
        self.tag = strSrc[:div-1] # do not get colon, :
        self.data = strSrc[div:].strip() # remove leading/trailing

    def parse(self):
        pass

    def isDefaultNoteLength(self):
        if self.tag == 'L': 
            return True
        return False

    def isMeter(self):
        if self.tag == 'M': 
            return True
        return False

    def isTitle(self):
        if self.tag == 'T': 
            return True
        return False

    def isComposer(self):
        if self.tag == 'C': 
            return True
        return False

    def isVoice(self):
        if self.tag == 'V': 
            return True
        return False

    def isKey(self):
        if self.tag == 'K': 
            return True
        return False


    def getTimeSignature(self):
        '''If there is a time signature representation available, get a numerator and denominator

        >>> am = ABCMetadata('M:2/2')
        >>> am.preParse()
        >>> am.getTimeSignature()
        (2, 2, 'normal')

        >>> am = ABCMetadata('M:C|')
        >>> am.preParse()
        >>> am.getTimeSignature()
        (2, 2, 'cut')
        '''
        if self.isMeter():
            if self.data == 'C':
                n, d = 4, 4
                symbol = 'ccommon' # m21 compat
            elif self.data == 'C|':
                n, d = 2, 2
                symbol = 'cut' # m21 compat
            else:
                n, d = self.data.split('/')
                n = int(n.strip())
                d = int(d.strip())
                symbol = 'normal' # m21 compat
        else:       
            raise ABCTokenException('no time signature associated with this meta-data')

        return n, d, symbol


    def getKeySignature(self):
        '''Extract key signature parameters, include indications for mode, and translate sharps count compatible with m21
        '''
        pass



    def getDefaultQuarterLength(self):
        '''If there is a quarter length representation available, return it as a floating point value

        >>> am = ABCMetadata('L:1/2')
        >>> am.preParse()
        >>> am.getDefaultQuarterLength()
        2.0

        >>> am = ABCMetadata('L:1/8')
        >>> am.preParse()
        >>> am.getDefaultQuarterLength()
        0.5

        >>> am = ABCMetadata('M:C|')
        >>> am.preParse()
        >>> am.getDefaultQuarterLength()
        0.5

        >>> am = ABCMetadata('M:2/4')
        >>> am.preParse()
        >>> am.getDefaultQuarterLength()
        0.25

        >>> am = ABCMetadata('M:6/8')
        >>> am.preParse()
        >>> am.getDefaultQuarterLength()
        0.5

        '''
        if self.isDefaultNoteLength():
            # should be in L:1/4 form
            n, d = self.data.split('/')
            n = int(n.strip())
            d = int(d.strip())
            # 1/4 is 1, 1/8 is .5
            return (float(n) / d) * 4
            
        elif self.isMeter():
            # meter auto-set a default not length
            n, d, symbol = self.getTimeSignature()
            if float(n) / d < .75:
                return .25 # less than 0.75 the default is a sixteenth note
            else:
                return .5 # otherwiseit is an eighth note

        else:       
            raise ABCTokenException('no quarter length associated with this meta-data')



class ABCBar(ABCToken):

    # given a logical unit, create an object
    # may be a chord, notes, metadata, bars
    def __init__(self, src):
        ABCToken.__init__(self, src)
        self.barType = None

    def __repr__(self):
        return '<ABCBar %r>' % self.src


class ABCTuplet(ABCToken):
    def __init__(self, src):
        ABCToken.__init__(self, src)

    def __repr__(self):
        return '<ABCTuplet %r>' % self.src


class ABCBrokenRhythmMarker(ABCToken):

    # given a logical unit, create an object
    # may be a chord, notes, metadata, bars
    def __init__(self, src):
        ABCToken.__init__(self, src)
        self.data = None

    def __repr__(self):
        return '<ABCBrokenRhythmMarker %r>' % self.src

    def preParse(self):
        '''Called before context adjustments: need to have access to data

        >>> abrm = ABCBrokenRhythmMarker('>>>')
        >>> abrm.preParse()
        >>> abrm.data
        '>>>'
        '''
        self.data = self.src.strip()



class ABCNote(ABCToken):

    # given a logical unit, create an object
    # may be a chord, notes, bars

    def __init__(self, src=''):
        ABCToken.__init__(self, src)

        # context attributes
        self.inBar = None
        self.inBeam = None
        self.inSlur = None
        self.inGrace = None

        # determined during parse() based on if pitch chars are present
        self.isRest = None

        # store chord string if connected to this note
        self.chordSymbols = [] 
        
        # provide default duration from handler; may change during piece
        self.activeDefaultQuarterLength = None
        # store if a broken symbol applies; pair of symbol, position (left, right)
        self.brokenRhythmMarker = None

        # pitch/ duration attributes for m21 conversion
        self.pitchName = None # if None, a rest or chord
        self.quarterLength = None


    def __repr__(self):
        return '<ABCNote %r>' % self.src

    
    def _splitChordSymbols(self, strSrc):
        '''Split chord symbols from other string characteristics. Return list of chord symbols and clean, remain chars

        >>> an = ABCNote()
        >>> an._splitChordSymbols('"C"e2')
        (['"C"'], 'e2')
        >>> an._splitChordSymbols('b2')
        ([], 'b2')
        >>> an._splitChordSymbols('"D7""D"d2')
        (['"D7"', '"D"'], 'd2')
        '''
        if '"' in strSrc:
            chordSymbols = reChordSymbol.findall(strSrc)
            # might remove quotes from chord symbols here

            # index of end of last match
            i = [m for m in reChordSymbol.finditer(strSrc)][-1].end()
            return chordSymbols, strSrc[i:]
        else:
            return [], strSrc        


    def _getPitchName(self, strSrc):
        '''Given a note or rest string without a chord symbol, return pitch or None of a rest. 

        >>> an = ABCNote()
        >>> an._getPitchName('e2')
        'E5'
        >>> an._getPitchName('C')
        'C4'
        >>> an._getPitchName('B,,')
        'B2'
        >>> an._getPitchName('C,')
        'C3'
        >>> an._getPitchName('c')
        'C5'
        >>> an._getPitchName("c'")
        'C6'
        >>> an._getPitchName("c''")
        'C7'
        >>> an._getPitchName("^g")
        'G#5'
        >>> an._getPitchName("_g''")
        'G-7'
        >>> an._getPitchName("=c")
        'Cn5'
        >>> an._getPitchName("z4") == None
        True

        '''
        # TODO: pitches are key dependent: accidentals are not given
        # if specified in key: must store key and adjust here

        try:
            name = rePitchName.findall(strSrc)[0]
        except IndexError: # no matches
            raise ABCHandlerException('cannot find any pitch information in: %s' % repr(strSrc))
    
        if name == 'z':
            return None # designates a rest
        else:
            if name.islower():
                octave = 5
            else:
                octave = 4
        # look in source string for register modification
        octModUp = strSrc.count("'")
        octModDown = strSrc.count(",")
        octave -= octModDown
        octave += octModUp

        sharpCount = strSrc.count("^")
        flatCount = strSrc.count("_")
        naturalCount = strSrc.count("=")
        accString = ''
        for x in range(flatCount):
            accString += '-' # m21 symbols
        for x in range(sharpCount):
            accString += '#' # m21 symbols
        for x in range(naturalCount):
            accString += 'n' # m21 symbols

        return '%s%s%s' % (name.upper(), accString, octave)


    def _getQuarterLength(self, strSrc, forceDefaultQuarterLength=None):
        '''Called with parse(), after context processing, to calculate duration

        >>> an = ABCNote()
        >>> an.activeDefaultQuarterLength = .5
        >>> an._getQuarterLength('e2')
        1.0
        >>> an._getQuarterLength('G')
        0.5
        >>> an._getQuarterLength('=c/2')
        0.25
        >>> an._getQuarterLength('A3/2')
        0.75
        >>> an._getQuarterLength('A/')
        0.25

        >>> an = ABCNote()
        >>> an.activeDefaultQuarterLength = .5
        >>> an.brokenRhythmMarker = ('>', 'left')
        >>> an._getQuarterLength('A')
        0.75
        >>> an.brokenRhythmMarker = ('>', 'right')
        >>> an._getQuarterLength('A')
        0.25

        >>> an.brokenRhythmMarker = ('<<<', 'left')
        >>> an._getQuarterLength('A')
        0.0625
        >>> an.brokenRhythmMarker = ('<<<', 'right')
        >>> an._getQuarterLength('A')
        0.9375

        >>> an._getQuarterLength('A', forceDefaultQuarterLength=1)
        1.875

        '''
        if forceDefaultQuarterLength != None:
            activeDefaultQuarterLength = forceDefaultQuarterLength
        else: # may be None
            activeDefaultQuarterLength = self.activeDefaultQuarterLength

        if activeDefaultQuarterLength == None:
            raise ABCTokenException('cannot calculate quarter length without a default quarter length')

        numStr = []
        for c in strSrc:
            if c.isdigit() or c in '/':
                numStr.append(c)
        numStr = ''.join(numStr)

        # get default
        if numStr == '':
            ql = activeDefaultQuarterLength
        # if only, shorthand for /2
        elif numStr == '/':
            ql = activeDefaultQuarterLength * .5
        # if a half fraction
        elif numStr.startswith('/'):
            ql = activeDefaultQuarterLength / int(numStr.split('/')[1])
        # assume we have a complete fraction
        elif '/' in numStr:
            n, d = numStr.split('/')
            n = int(n.strip())
            d = int(d.strip())
            ql = activeDefaultQuarterLength * (float(n) / d)
        # not a fraction; a multiplier
        else: 
            ql = activeDefaultQuarterLength * int(numStr)

        if self.brokenRhythmMarker != None:
            symbol, direction = self.brokenRhythmMarker
            if symbol == '>':
                modPair = (1.5, .5)
            elif symbol == '<':
                modPair = (.5, 1.5)
            elif symbol == '>>':
                modPair = (1.75, .25)
            elif symbol == '<<':
                modPair = (.25, 1.75)
            elif symbol == '>>>':
                modPair = (1.875, .125)
            elif symbol == '<<<':
                modPair = (.125, 1.875)
            # apply based on direction
            if direction == 'left':
                ql *= modPair[0]
            elif direction == 'right':
                ql *= modPair[1]

        # need to look at tuplets lastly
        return ql


    def parse(self, forceKey=None, forceDefaultQuarterLength=None):
        self.chordSymbols, nonChordSymStr = self._splitChordSymbols(self.src)        
        # get pitch name form remaining string
        # rests will have a pitch name of None
        self.pitchName = self._getPitchName(nonChordSymStr)
        if self.pitchName == None:
            self.isRest = True
        else:
            self.isRest = False

        self.quarterLength = self._getQuarterLength(nonChordSymStr, 
                            forceDefaultQuarterLength=forceDefaultQuarterLength)

        # environLocal.printDebug(['ABCNote:', 'pitch name:', self.pitchName, 'ql:', self.quarterLength])


class ABCChord(ABCNote):

    # given a logical unit, create an object
    # may be a chord, notes, bars

    def __init__(self, src):
        ABCNote.__init__(self, src)
        # store a list of component objects
        self.subTokens = []

    def __repr__(self):
        return '<ABCChord %r>' % self.src


    def parse(self, forceKey=None, forceDefaultQuarterLength=None):
        self.chordSymbols, nonChordSymStr = self._splitChordSymbols(self.src) 

        tokenStr = nonChordSymStr[1:-1] # remove outer brackets
        #environLocal.printDebug(['ABCChord:', nonChordSymStr, 'tokenStr', tokenStr])

        self.quarterLength = self._getQuarterLength(nonChordSymStr, 
                            forceDefaultQuarterLength=forceDefaultQuarterLength)

        # create a handler for processing internal chord notes
        ah = ABCHandler()
        # only tokenizing; not calling process() as these objects
        # have no metadata
        # may need to supply key?
        ah.tokenize(tokenStr)

        for t in ah.tokens:
            #environLocal.printDebug(['ABCChord: subTokens', t])
            # parse any tokens individually, supply local data as necesssary
            if isinstance(t, ABCNote):
                t.parse(forceDefaultQuarterLength=self.quarterLength)

            self.subTokens.append(t)


#-------------------------------------------------------------------------------
class ABCHandler(object):

    # divide elements of a character stream into objects and handle
    # store in a list, and pass global information to compontns
    def __init__(self):
        # tokens are ABC objects in a linear stream
        self._tokens = []

    def _getLinearContext(self, strSrc, i):
        '''Find the local context of a string or list of ojbects. Returns charPrevNotSpace, charPrev, charThis, charNext, charNextNotSpace.


        >>> ah = ABCHandler()
        >>> ah._getLinearContext('12345', 0)
        (None, None, '1', '2', '2', '3')
        >>> ah._getLinearContext('12345', 1)
        ('1', '1', '2', '3', '3', '4')
        >>> ah._getLinearContext('12345', 3)
        ('3', '3', '4', '5', '5', None)
        >>> ah._getLinearContext('12345', 4)
        ('4', '4', '5', None, None, None)

        >>> ah._getLinearContext([32, None, 8, 11, 53], 4)
        (11, 11, 53, None, None, None)
        >>> ah._getLinearContext([32, None, 8, 11, 53], 2)
        (32, None, 8, 11, 11, 53)
        >>> ah._getLinearContext([32, None, 8, 11, 53], 0)
        (None, None, 32, None, 8, 8)


        '''            
        lastIndex = len(strSrc) - 1
        if i > lastIndex:
            raise ABCHandlerException
        # find local area of string
        if i > 0:
            cPrev = strSrc[i-1]
        else:      
            cPrev = None
        # get last char previous non-white; do not start with current
        # -1 goes to index 0
        cPrevNotSpace = None
        for j in range(i-1, -1, -1):
            # condition to break: find a something that is not None, or 
            # a string that is not a space
            if isinstance(strSrc[j], str):
                if not strSrc[j].isspace():
                    cPrevNotSpace = strSrc[j]
                    break
            else:
                if strSrc[j] != None:
                    cPrevNotSpace = strSrc[j]
                    break
        # set this characters
        c = strSrc[i]

        cNext = None
        if i < len(strSrc)-1:
            cNext = strSrc[i+1]            

        # get 2 chars forward
        cNextNext = None
        if i < len(strSrc)-2:
            cNextNext = strSrc[i+2]

        cNextNotSpace = None
        # start at next index and look forward
        for j in range(i+1, len(strSrc)):
            if isinstance(strSrc[j], str):
                if not strSrc[j].isspace():
                    cNextNotSpace = strSrc[j]
                    break
            else:
                if strSrc[j] != None:
                    cNextNotSpace = strSrc[j]
                    break
        return cPrevNotSpace, cPrev, c, cNext, cNextNotSpace, cNextNext


    def _getNextLineBreak(self, strSrc, i):
        '''Return index of next line break.

        >>> ah = ABCHandler()
        >>> strSrc = 'de  we\\n wer bfg\\n'
        >>> ah._getNextLineBreak(strSrc, 0)
        6
        >>> strSrc[0:6]
        'de  we'
        >>> # from last line break
        >>> ah._getNextLineBreak(strSrc, 6)
        15
        >>> strSrc[ah._getNextLineBreak(strSrc, 0):]
        '\\n wer bfg\\n'
        '''
        lastIndex = len(strSrc) - 1
        j = i + 1 # start with next
        while True:
            if strSrc[j] == '\n' or j > lastIndex:
                return j # will increment to next char on loop
            j += 1


    #---------------------------------------------------------------------------
    # token processing

    def tokenize(self, strSrc):
        '''Walk the abc string, creating ABC objects along the way.

        This may be called separately from process(), in the case that pre/post parse processing is not needed. 
        '''
        i = 0
        collect = []
        lastIndex = len(strSrc) - 1

        activeChordSymbol = '' # accumulate, then prepend
        while True:    
            if i > lastIndex:
                break

            q = self._getLinearContext(strSrc, i)
            cPrevNotSpace, cPrev, c, cNext, cNextNotSpace, cNextNext = q
            
            # comment lines, also encoding defs
            if c == '%':
                j = self._getNextLineBreak(strSrc, i)
                #environLocal.printDebug(['got comment:', repr(strSrc[i:j+1])])
                i = j+1 # skip \n char
                continue

            # metadata: capatal alpha, with next char as ':'
            # get metadata before others
            # some meta data might have bar symbols, for example
            # need to not misinterpret repeat ends bars as meta
            # e.g. dAG FED:|2 dAG FGA| this is incorrect, but can avoid by
            # looking for a leading pipe
            if (c.isalpha() and c.isupper() 
                and cNext != None and cNext == ':' and 
                cNextNext != None and cNextNext not in '|'):
                # collect until end of line; add one to get line break
                j = self._getNextLineBreak(strSrc, i) + 1
                collect = strSrc[i:j].strip()
                #environLocal.printDebug(['got metadata:', repr(''.join(collect))])
                self._tokens.append(ABCMetadata(collect))
                i = j
                continue
            
            # get bars: if not a space and not alphanemeric
            if (not c.isspace() and not c.isalnum()
                and c not in ['~', '(']):
                matchBars = False
                for barIndex in range(len(ABC_BARS)):
                    # first of bars tuple is symbol to match
                    if c + cNext == ABC_BARS[barIndex][0]:
                        j = i + 2
                        matchBars = True 
                        break
                    # check for single char bars
                    elif c == ABC_BARS[barIndex][0]:
                        j = i + 1
                        matchBars = True 
                        break
                if matchBars:
                    collect = strSrc[i:j]
                    #environLocal.printDebug(['got bars:', repr(collect)])  
                    self._tokens.append(ABCBar(collect))
                    i = j
                    continue
                    
            # get tuplet indicators: (2, (3
            # TODO: extended tuplets look like this: (p:q:r or (3::
            if (c == '(' and cNext != None and cNext.isdigit()):
                j = i + 2 # always two characters
                collect = strSrc[i:j]
                #environLocal.printDebug(['got tuplet start:', repr(collect)])
                self._tokens.append(ABCTuplet(collect))
                i = j
                continue

            # get broken rhythm modifiers: < or >, >>, up to <<<
            if c in '<>':
                j = i + 1
                while (j < lastIndex and strSrc[j] in '<>'):
                    j += 1
                collect = strSrc[i:j]
                #environLocal.printDebug(['got bidrectional rhythm mod:', repr(collect)])
                self._tokens.append(ABCBrokenRhythmMarker(collect))
                i = j
                continue

            # get chord symbols / guitar chords; collected and joined with
            # chord or notes
            if (c == '"'):
                j = i + 1
                while (j < lastIndex and strSrc[j] not in '"'):
                    j += 1
                j += 1 # need character that caused break
                # there may be more than one chord symbol: need to accumulate
                activeChordSymbol += strSrc[i:j]
                #environLocal.printDebug(['got chord symbol:', repr(activeChordSymbol)])
                i = j
                continue

            # get chords
            if (c == '['):
                j = i + 1
                while (j < lastIndex and strSrc[j] not in ']'):
                    j += 1
                j += 1 # need character that caused break
                # prepend chord symbol
                if activeChordSymbol != '':
                    collect = activeChordSymbol+strSrc[i:j]
                    activeChordSymbol = '' # reset
                else:
                    collect = strSrc[i:j]

                #environLocal.printDebug(['got chord:', repr(collect)])
                self._tokens.append(ABCChord(collect))

                i = j
                continue

            # get the start of a note event: alpha, or 
            # ~ tunr/ornament, accidentals ^, =, - as well as ^^
            if (c.isalpha() or c in '~^=_.'):
                # condition where we start with an alpha that is not an alpha
                # that comes before a pitch indication
                # H is fermata, L is accent, T is trill
                foundPitchAlpha = c.isalpha() and c not in 'uvHLT'
                j = i + 1

                while True:
                    if j > lastIndex:
                        break    
                    # if we have not found pitch alpha
                    # ornaments may precede note names
                    # accidentals (^=_) staccato (.), up/down bow (u, v)
                    elif foundPitchAlpha == False and strSrc[j] in '~=^_.uvHLT':
                        j += 1
                        continue                    
                    # only allow one pitch alpha to be a continue condition
                    elif (foundPitchAlpha == False and strSrc[j].isalpha() 
                        and strSrc[j] not in 'uvHL'):
                        foundPitchAlpha = True
                        j += 1
                        continue                    
                    # continue conditions after alpha: 
                    # , register modifiaciton (, ') or number, rhythm indication
                    # number, /, 
                    elif strSrc[j].isdigit() or strSrc[j] in ',/\'':
                        j += 1
                        continue    
                    else: # space, all else: break
                        break
                # prepend chord symbol
                if activeChordSymbol != '':
                    collect = activeChordSymbol+strSrc[i:j]
                    activeChordSymbol = '' # reset
                else:
                    collect = strSrc[i:j]
                #environLocal.printDebug(['got note event:', repr(collect)])
                self._tokens.append(ABCNote(collect))
                i = j
                continue

            # look for white space: can be used to determine beam groups

            # no action: normal continuation of 1 char
            i += 1

    
    def tokenProcess(self):
        '''Process all token objects. First, call preParse(), then do cointext assignments, then call parse(). 
        '''
        # pre-parse : call on objects that need preliminary processing
        # metadata, for example, is parsed
        for t in self._tokens:
            #environLocal.printDebug(['token:', t.src])
            t.preParse()

        # context: iterate through tokens, supplying contextual data as necessary to appropriate objects
        lastDefaultQL = None
        for i in range(len(self._tokens)):
            # get context of tokens
            q = self._getLinearContext(self._tokens, i)
            tPrevNotSpace, tPrev, t, tNext, tNextNotSpace, tNextNext = q
            
            if isinstance(t, ABCMetadata):
                if t.isMeter() or t.isDefaultNoteLength():
                    lastDefaultQL = t.getDefaultQuarterLength()
                continue

            # broken rhythms need to be applied to previous and next notes
            if isinstance(t, ABCBrokenRhythmMarker):
                if (isinstance(tPrev, ABCNote) and 
                isinstance(tNext, ABCNote)):
                    #environLocal.printDebug(['tokenProcess: got broken rhythm marker', t.src])       
                    tPrev.brokenRhythmMarker = (t.data, 'left')
                    tNext.brokenRhythmMarker = (t.data, 'right')
                else:
                    raise ABCHandlerException('broken rhythm marker (%s) not positioned between two notes or chords' % t.src)

            # ABCChord inherits ABCNote, thus getting note is enough for both
            if isinstance(t, (ABCNote, ABCChord)):
                if lastDefaultQL == None:
                    raise ABCHandlerException('no active default note length provided for note processing. tPrev: %s, t: %s, tNext: %s' % (tPrev, t, tNext))
                t.activeDefaultQuarterLength = lastDefaultQL
                continue

        # parse : call methods to set attributes and parse string
        for t in self._tokens:
            t.parse()
            #print o.src

    def process(self, strSrc):
        self._tokens = []
        self.tokenize(strSrc)
        self.tokenProcess()
        # return list of tokens; stored internally

    def _getTokens(self):
        if self._tokens == []:
            raise ABCHandlerException('must process tokens before calling split')
        return self._tokens

    tokens = property(_getTokens, 
        doc = '''Get a the tokens from this Handler
        ''')
    

    #---------------------------------------------------------------------------
    # utility methods for post processing

    def splitByVoice(self):
        '''Given a processed token list, look for voices. If voices exist, split into parts: common metadata, then next voice, next voice, etc.

        >>> abcStr = 'M:6/8\\nL:1/8\\nK:G\\nV:1 name="Whistle" snm="wh"\\nB3 A3 | G6 | B3 A3 | G6 ||\\nV:2 name="violin" snm="v"\\nBdB AcA | GAG D3 | BdB AcA | GAG D6 ||\\nV:3 name="Bass" snm="b" clef=bass\\nD3 D3 | D6 | D3 D3 | D6 ||'
        >>> ah = ABCHandler()
        >>> junk = ah.process(abcStr)
        >>> tokenColls = ah.splitByVoice()
        >>> [t.src for t in tokenColls[0]] # common headers are first
        ['M:6/8', 'L:1/8', 'K:G']
        >>> # then each voice
        >>> [t.src for t in tokenColls[1]] 
        ['V:1 name="Whistle" snm="wh"', 'B3', 'A3', '|', 'G6', '|', 'B3', 'A3', '|', 'G6', '||']
        >>> [t.src for t in tokenColls[2]] 
        ['V:2 name="violin" snm="v"', 'B', 'd', 'B', 'A', 'c', 'A', '|', 'G', 'A', 'G', 'D3', '|', 'B', 'd', 'B', 'A', 'c', 'A', '|', 'G', 'A', 'G', 'D6', '||']
        >>> [t.src for t in tokenColls[3]] 
        ['V:3 name="Bass" snm="b" clef=bass', 'D3', 'D3', '|', 'D6', '|', 'D3', 'D3', '|', 'D6', '||']

        '''

        if self._tokens == []:
            raise ABCHandlerException('must process tokens before calling split')

        voiceCount = 0
        pos = []
        for i in range(len(self._tokens)):
            t = self._tokens[i]
            if isinstance(t, ABCMetadata):
                if t.isVoice():
                    # if first char is a number
                    # can be V:3 name="Bass" snm="b" clef=bass
                    if t.data[0].isdigit():
                        pos.append(i) # store position 
                        voiceCount += 1

        post = []
        # no voices, or definition of one voice, or use of V: field for 
        # something else
        if voiceCount <= 1:
            post.append(self._tokens)
        # two or more voices
        else: 
            # metadata is everything before first v1. 
            # first v1 found at pos[0]
            post.append(self._tokens[:pos[0]])
            i = pos[0]
            # start range at second value in pos
            for x in range(1, len(pos)):
                j = pos[x]
                post.append(self._tokens[i:j])
                i = j
            # get last span
            post.append(self._tokens[i:])

        return post



    def getTitle(self):
        '''If tokens are processed, get the first title tag. Used for testing.
        '''
        if self._tokens == []:
            raise ABCHandlerException('must process tokens before calling split')
        for t in self._tokens:
            if isinstance(t, ABCMetadata):
                if t.isTitle():
                    return t.data
        return None




#-------------------------------------------------------------------------------
class ABCFile(object):
    '''
    ABC File access

    '''
    
    def __init__(self): 
        pass

    def open(self, filename): 
        '''Open a file for reading
        '''
        self.file = open(filename, 'r') 

    def openFileLike(self, fileLike):
        '''Assign a file-like object, such as those provided by StringIO, as an open file object.

        >>> fileLikeOpen = StringIO.StringIO()
        '''
        self.file = fileLike
    
    def __repr__(self): 
        r = "<ABCFile>" 
        return r 
    
    def close(self): 
        self.file.close() 
    
    def read(self): 
        return self.readstr(self.file.read()) 
    
    def readstr(self, str): 
        handler = ABCHandler()
        # return the handler instanc
        handler.process(str)
        return handler
    
#     def write(self): 
#         ws = self.writestr()
#         self.file.write(ws) 
#     
#     def writestr(self): 
#         pass










#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testTokenization(self):
        from music21.abc import testFiles

        for (tf, countTokens, noteTokens, chrodTokens) in [
            (testFiles.fyrareprisarn, 236, 152, 0), 
            (testFiles.mysteryReel, 188, 153, 0), 
            (testFiles.aleIsDear, 291, 206, 32),
            (testFiles.testPrimitive, 94, 75, 2),
            (testFiles.kitchGirl, 125, 101, 2),
            (testFiles.williamAndNancy, 127, 93, 0),
            (testFiles.morrisonsJig, 176, 137, 0),

                ]:

            handler = ABCHandler()
            handler.tokenize(tf)
            tokens = handler._tokens # get private for testing
            self.assertEqual(len(tokens), countTokens)
            countNotes = 0
            countChords = 0
            for o in tokens:
                if isinstance(o, ABCChord):
                    countChords += 1
                elif isinstance(o, ABCNote):
                    countNotes += 1

            self.assertEqual(countNotes, noteTokens)
            self.assertEqual(countChords, chrodTokens)
        

    def testRe(self):

        src = 'A: this is a test'
        post = reMetadataTag.match(src).end()
        self.assertEqual(src[:post], 'A:')
        self.assertEqual(src[post:], ' this is a test' )


        src = 'Q: this is a test % and a following comment'
        post = reMetadataTag.match(src).end()
        self.assertEqual(src[:post], 'Q:')


        # chord symbol matches
        src = 'd|"G"e2d B2d|"C"gfe "D7"d2d|"G"e2d B2d|"A7""C"gfe "D7""D"d2c|'
        post = reChordSymbol.findall(src)
        self.assertEqual(post, ['"G"', '"C"', '"D7"', '"G"', '"A7"', 
                                '"C"', '"D7"', '"D"'] )

        # get index of last match of many
        i = [m for m in reChordSymbol.finditer(src)][-1].end()

        src = '=d2'
        self.assertEqual(rePitchName.findall(src)[0], 'd')

        src = 'A3/2'
        self.assertEqual(rePitchName.findall(src)[0], 'A')


        

    def testTokenProcessMetadata(self):
        from music21.abc import testFiles

#'Full Rigged Ship', '6/8', 'G'
        for (tf, titleEncoded, meterEncoded, keyEncoded) in [
            (testFiles.fyrareprisarn, 'Fyrareprisarn', '3/4', 'F'), 
            (testFiles.mysteryReel, 'Mystery Reel', 'C|', 'G'), 
            (testFiles.aleIsDear, 'Ale is Dear, the', '4/4', 'D', ),
            (testFiles.kitchGirl, 'Kitchen Girl', '4/4', 'D'),
            (testFiles.williamAndNancy, 'William and Nancy', '6/8', 'G'),
            ]:

            handler = ABCHandler()
            handler.tokenize(tf)
            handler.tokenProcess()

            tokens = handler._tokens # get private for testing
            for t in tokens:
                if isinstance(t, ABCMetadata):
                    if t.tag == 'T':
                        self.assertEqual(t.data, titleEncoded)
                    elif t.tag == 'M':
                        self.assertEqual(t.data, meterEncoded)
                    elif t.tag == 'K':
                        self.assertEqual(t.data, keyEncoded)



    def testTokenProcess(self):
        from music21.abc import testFiles

        for tf in [
            testFiles.fyrareprisarn,
            testFiles.mysteryReel,
            testFiles.aleIsDear, 
            testFiles.testPrimitive,
            testFiles.kitchGirl,
            testFiles.williamAndNancy,
            ]:

            handler = ABCHandler()
            handler.tokenize(tf)
            handler.tokenProcess()


if __name__ == "__main__":
    music21.mainTest(Test)








