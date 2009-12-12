#-------------------------------------------------------------------------------
# Name:         common.py
# Purpose:      Basic Utilties
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''Utility constants, dictionaries, functions, and objects used throughout music21.
'''

# should NOT import music21 or anything like that except in doctests.
import re
import copy
import math, types, sys, os
import unittest, doctest
import decimal
import time
import weakref
import hashlib
import imp
import random
import inspect

# define file extensions for various foramts
fileExtensions = {
    'musicxml' : {'input': ['xml', 'mxl', 'mx'], 'output': 'mxl'},
    'lilypond' : {'input': ['ly', 'lily'], 'output': 'ly'},
    'humdrum' : {'input': ['krn'], 'output': 'krn'},
    'jpeg' : {'input': ['jpg', 'jpeg'], 'output': 'jpg'},
    'png'  : {'input': ['png'], 'output': 'png'},
    'pdf'  : {'input': ['pdf'], 'output': 'pdf'},
    'pickle' : {'input': ['p', 'pickle'], 'output': 'p'},
}



ordinals = ["Zeroth","First","Second","Third","Fourth","Fifth",
            "Sixth","Seventh","Eighth","Ninth","Tenth","Eleventh",
            "Twelfth","Thirteenth","Fourteenth","Fifteenth",
            "Sixteenth","Seventeenth","Eighteenth","Nineteenth",
            "Twentieth","Twenty-first","Twenty-second"]

musicOrdinals = ordinals
musicOrdinals[1] = "Unison"
musicOrdinals[8] = "Octave"
musicOrdinals[15] = "Double-octave"
musicOrdinals[22] = "Triple-octave"

WHITESPACE = re.compile('\s+')
LINEFEED = re.compile('\n+')


DEBUG_OFF = 0
DEBUG_USER = 1
DEBUG_DEVEL = 63
DEBUG_ALL = 255





def findFormat(fmt):
    '''Given a format defined either by a format name or 
    an extension, return the format name as well as the output exensions

    >>> findFormat('mx')
    ('musicxml', '.mxl')
    >>> findFormat('.mxl')
    ('musicxml', '.mxl')
    >>> findFormat('musicxml')
    ('musicxml', '.mxl')
    >>> findFormat('jpeg')
    ('jpeg', '.jpg')
    >>> findFormat('lily')
    ('lilypond', '.ly')
    >>> findFormat('jpeg')
    ('jpeg', '.jpg')
    >>> findFormat('humdrum')
    ('humdrum', '.krn')
    '''
    for key in fileExtensions.keys():
        if fmt.startswith('.'):
            fmt = fmt[1:] # strip .
        if fmt == key or fmt in fileExtensions[key]['input']:
            # add leading dot to extension on output
            return key, '.' + fileExtensions[key]['output']
    return None, None # if no match found


def findInputExtension(fmt):
    '''Given an input format, find and return all possible input extensions.

    >>> a = findInputExtension('musicxml')
    >>> a
    ['xml', 'mxl', 'mx']
    >>> a = findInputExtension('mx')
    >>> a
    ['xml', 'mxl', 'mx']
    >>> a = findInputExtension('humdrum')
    >>> a
    ['krn']
    '''
    fmt = findFormat(fmt)[0]
    if fmt == None:
        raise Exception('no match to format: %s' % fmt)
    return fileExtensions[fmt]['input']

def findFormatFile(fp):
    '''Given a file path (relative or absolute) return the format

    >>> findFormatFile('test.xml')
    'musicxml'
    >>> findFormatFile('long/file/path/test-2009.03.02.xml')
    'musicxml'
    >>> findFormatFile('long/file/path.intermediate.png/test-2009.03.xml')
    'musicxml'
    
    Windows drive + pickle
    >>> findFormatFile('d:/long/file/path/test.p')
    'pickle'
    
    On a windows networked filesystem
    >>> findFormatFile('\\\\long\\file\\path\\test.krn')
    'humdrum'

    '''
    format, ext = findFormat(fp.split('.')[-1])
    return format # may be None if no match


def basicallyEqual(a, b):
    '''
    returns true if a and b are equal except for whitespace differences

    >>> a = " hello there "
    >>> b = "hello there"
    >>> c = " bye there "
    >>> basicallyEqual(a,b)
    True
    >>> basicallyEqual(a,c)
    False
    '''
    a = WHITESPACE.sub('', a)
    b = WHITESPACE.sub('', b)
    a = LINEFEED.sub('', a)
    b = LINEFEED.sub('', b)
#    print a
#    print b
    if (a == b): return True
    else: return False

basicallyEquals = basicallyEqual

def almostEquals(x, y = 0.0, grain=1e-7):
    '''
    The following four routines work for comparisons between floats that are normally inconsistent.
    
    almostEquals(x, y) -- returns True if x and y are within 0.0000001 of each other
    '''
    
    if abs(x - y) < grain: return True
    else: return False

almostEqual = almostEquals

def greaterThan(x, y = 0.0):
    '''
    greaterThan returns True if x is greater than and not almostEquals y
    '''
    if x < y or almostEquals(x, y): return False
    else: return True

def lessThan(x, y = 0.0):
    '''
    lessThan -- returns True if x is less than and not almostEquals y
    '''
    if x > y or almostEquals(x, y): return False
    else: return True    
    
def isPowerOfTwo(n):
    ''' 
    returns True if argument is either a power of 2 or a reciprocal
    of a power of 2. Uses almostEquals so that a float whose reminder after
    taking a log is nearly zero is still True

    >>> isPowerOfTwo(3)
    False
    >>> isPowerOfTwo(18)
    False
    >>> isPowerOfTwo(1024)
    True
    >>> isPowerOfTwo(1024.01)
    False
    >>> isPowerOfTwo(1024.00001)
    True

    OMIT_FROM_DOCS
    >>> isPowerOfTwo(10)
    False
    '''

    if n <= 0:
        return False
    
    (remainder, throwAway) = math.modf(math.log(n, 2))
    if (almostEquals(remainder, 0.0)): return True
    else: return False

def isNum(usrData):
    '''check if usrData is a number (float, int, long, Decimal), return boolean
    IMPROVE: when 2.6 is everwhere: add numbers class.

    >>> isNum(3.0)
    True
    >>> isNum(3)
    True
    >>> isNum('three')
    False
    '''
    if (isinstance(usrData, float) or 
        isinstance(usrData, int) or 
        isinstance(usrData, long) or
        isinstance(usrData, decimal.Decimal)):
        return True
    else:
        return False        


def isStr(usrData):
    """Check of usrData is some form of string, including unicode.

    >>> isStr(3)
    False
    >>> isStr('sharp')
    True
    >>> isStr(u'flat')
    True
    """
    if (isinstance(usrData, str) or 
        isinstance(usrData, unicode)):
        return True
    else:
        return False                


def isListLike(usrData):
    """
    Returns True if is a List or a Set or a Tuple
    #TODO: add immutable sets and pre 2.6 set support

    >>> isListLike([])
    True
    >>> isListLike('sharp')
    False
    >>> isListLike((None, None))
    True
    >>> import music21.stream
    >>> isListLike(music21.stream.Stream())
    False
    """
    if (isinstance(usrData, list) or 
        isinstance(usrData, tuple) or
        isinstance(usrData, set)):
        return True
    else:
        return False            

def isIterable(usrData):
    """
    Returns True if is the object can be iter'd over

    >>> isIterable([])
    True
    >>> isIterable('sharp')
    False
    >>> isIterable((None, None))
    True
    >>> import music21.stream
    >>> isIterable(music21.stream.Stream())
    True
    """
    if hasattr(usrData, "__iter__"):
        return True
    else:
        return False


def getPlatform():
    '''
    Shared function to get platform names.
    '''
    # possible os.name values: 'posix', 'nt', 'mac', 'os2', 'ce', 
    # 'java', 'riscos'.
    if os.name in ['nt'] or sys.platform.startswith('win'):
        return 'win'
    elif sys.platform in ['darwin']:
        return 'darwin' # 
    elif os.name == 'posix': # catch all other nix platforms
        return 'nix'  


def dotMultiplier(dots):
    '''
    dotMultiplier(dots) returns how long to multiply the note length of a note in order to get the note length with n dots
    
    >>> dotMultiplier(1)
    1.5
    >>> dotMultiplier(2)
    1.75
    >>> dotMultiplier(3)
    1.875
    '''
    x = (((2**(dots+1.0))-1.0)/(2**dots))
    return x



def decimalToTuplet(decNum):
    '''
    For simple decimals (mostly > 1), a quick way to figure out the
    fraction in lowest terms that gives a valid tuplet.

    No it does not work really fast.  No it does not return tuplets with
    denominators over 100.  Too bad, math geeks.  This is real life.

    returns (numerator, denominator)
    '''

    (remainder, multiplier) = math.modf(decNum)
    working = decNum/multiplier

    (jy, iy) = findSimpleFraction(working)

    if iy == 0:
        raise Exception("No such luck")

    jy *= multiplier
    gcd = EuclidGCD(int(jy), int(iy))
    jy = jy/gcd
    iy = iy/gcd
    return (int(jy), int(iy))

def findSimpleFraction(working):
    for i in range(1,1000):
        for j in range(i,2*i):
            if almostEquals(working, (j+0.0)/i):
                return (int(j), int(i))
    return (0,0)

def EuclidGCD(a, b):
    '''use Euclid\'s algorithm to find the GCD of a and b'''
    if b == 0:
        return a
    else:
        return EuclidGCD(b, a % b)
    

def _lcm(a, b):
    """find lowest common multiple of a,b"""
    # // forcers integer style division (no remainder)
    return abs(a*b) / EuclidGCD(a,b) 

def lcm(filter):
    '''
    >>> lcm([3,4,5])
    60
    >>> lcm([3,4])
    12
    >>> lcm([1,2])
    2
    >>> lcm([3,6])
    6
    '''
    # derived from 
    # http://www.oreillynet.com/cs/user/view/cs_msg/41022
    lcmVal = 1
    for i in range(len(filter)):
        lcmVal = _lcm(lcmVal, filter[i])
    return lcmVal





def fromRoman(num):
    if (num == 'I' or num == 'i'):
        return 1
    elif (num == 'II' or num == 'ii'):
        return 2
    elif (num == 'III' or num == 'iii'):
        return 3
    elif (num == 'IV' or num == 'iv'):
        return 4
    elif (num == 'V' or num == 'v'):
        return 5
    elif (num == 'VI' or num == 'vi'):
        return 6
    elif (num == 'VII' or num == 'vii'):
        return 7
    elif (num == 'VIII' or num == 'viii'):
        return 8
    else:
        raise Exception("invalid roman numeral")

def toRoman(num):
    if (num == 1):
        return 'I'
    elif (num == 2):
        return 'II'
    elif (num == 3):
        return 'III'
    elif (num == 4):
        return 'IV'
    elif (num == 5):
        return 'V'
    elif (num == 6):
        return 'VI'
    elif (num == 7):
        return 'VII'
    elif (num == 8):
        return 'VII'
    else:
        raise Exception("invalid input: must be integer 1-8")

def stripAddresses(textString, replacement = "ADDRESS"):
    '''
    Function that changes all memory addresses in the given 
    textString with (replacement).  This is useful for testing
    that a function gives an expected result even if the result
    contains references to memory locations.  So for instance:

    >>> stripAddresses("{0.0} <music21.clef.TrebleClef object at 0x02A87AD0>")
    '{0.0} <music21.clef.TrebleClef object at ADDRESS>'
    
    while this is left alone:

    >>> stripAddresses("{0.0} <music21.humdrum.MiscTandam *>I humdrum control>")
    '{0.0} <music21.humdrum.MiscTandam *>I humdrum control>'
    '''
    ADDRESS = re.compile('0x[0-9A-F]+')
    return ADDRESS.sub(replacement, textString)

    
def sortModules(moduleList):
    '''Sort a lost of imported module names such that most recently modified is 
    first'''
    sort = []
    for mod in moduleList:
        fp = mod.__file__ # returns the pyc file
        stat = os.stat(fp)
        lastmod = time.localtime(stat[8])
        asctime = time.asctime(lastmod)
        sort.append((lastmod, asctime, mod))
    sort.sort()
    sort.reverse()
    # just return module list
    return [mod for lastmod, asctime, mod in sort]


def sortFilesRecent(fileList):
    '''Given two files, sort by most recent. Return only the file
    paths.

    >>> a = os.listdir(os.curdir)
    >>> b = sortFilesRecent(a)
    '''
    sort = []
    for fp in fileList:
        lastmod = time.localtime(os.stat(fp)[8])
        sort.append([lastmod, fp])
    sort.sort()
    sort.reverse()
    # just return 
    return [y for x,y in sort] 


def getMd5(value=None):
    '''Return a string from an md5 haslib
    >>> getMd5('test')
    '098f6bcd4621d373cade4e832627b4f6'
    '''
    if value == None:
        value = str(time.time()) + str(random.random())
    m = hashlib.md5()
    m.update(value)    
    return m.hexdigest()


def formatStr(msg, *arguments, **keywords):
    '''Format one or more data elements into string suitable for printing
    straight to stderr or other outputs

    >>> a = formatStr('test', '1', 2, 3)
    >>> print a
    test 1 2 3
    <BLANKLINE>
    '''
    msg = [msg] + list(arguments)
    msg = [str(x) for x in msg]
    return ' '.join(msg)+'\n'


def dirPartitioned(obj, skipLeading=['__']):
    '''Given an objet, return three lists of names: methods, attributes, and properties.

    Note that if a name/attribute is dynamically created by a property it 
    cannot be found until that attribute is created.

    TODO: this cannot properly partiton properties from methods
    '''
    names = dir(obj)
    methods = []
    attributes = []
    properties = []
    for name in names:
        skip = False
        for lead in skipLeading:
            if name.startswith(lead):
                skip = True
                break
        if skip:
            continue
        # get attr returns methods, attributes, and properties
        # when getting an attribute from a property, however, this may call
        # the getter of a name that is only defined in a setter
        part = getattr(obj, name)
        if isinstance(part, property):
            properties.append(name)
#         if inspect.isdatadescriptor(part):
#             properties.append(name)
        elif inspect.ismethod(part):
            methods.append(name)
#         elif isinstance(part, types.MethodType):
#             methods.append(name)
        else:
            attributes.append(name)
    return methods, attributes, properties

#-------------------------------------------------------------------------------

    
'''
the following are a set of objects with more relaxed behaviors for quicker writing.

Most of these objects behave more like perl; for Python converts.

A set of quick and dirty objects to make coding a bit easier for people who have
been coding in perl for years.  Prevents things like KeyErrors, etc.  Tradeoff
is that typos of keys etc. are harder to detect (and some run speed tradeoff I'm sure).
Advantage is coding time and fewer type errors while coding.
'''

class defHash(dict):
    '''A replacement for dictionaries that behave a bit more like perl hashes.  No more KeyErrors. The difference between defHash and defaultdict is that the Dict values come first and that default can be set to None (which it is...) or any object.
    
    If you want a factory that makes hashes with a particular different default, use:
    
        falsehash = lambda h = None: defHash(h, default = False)
        a = falsehash({"A": falsehash(), "B": falsehash()})
        print a["A"]["hi"] # returns False
    
    there's probably a way to use this to create a data structure
    of arbitrary dimensionality, though it escapes this author.

    if callDefault is True then the default is called:
    
        defHash(default = list, callDefault = True)
        
    will create a new List for each element
    '''
    def __init__(self, hash = None, default = None, callDefault = False):
        if hash:
            dict.__init__(self, hash)
        else:
            dict.__init__(self)
        self.default = default
        self.callDefault = callDefault
    
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if self.callDefault is False:
                return self.default
            else:
                dict.__setitem__(self, key, self.default())
                return dict.__getitem__(self, key)

    def get(self, key, *args):
            if not args:
                if self.callDefault is False:
                    args = (self.default,)
                else:
                    args = (self.default(),)
            return dict.get(self, key, *args)


class defList(list):
    '''A replacement for lists that behave a bit more like perl arrays. No more ListErrors.
        '''    
    
    def __init__(self, value = None, default = None, callDefault = False):
        if value:
            list.__init__(self, value)
        else:
            list.__init__(self)
        self.default = default
        self.callDefault = callDefault

    def __getitem__(self, item):
        try:
            return list.__getitem__(self, item)
        except IndexError:
            if self.callDefault is False:
                return self.default
            else:
                list.__setitem__(self, item, self.default())
                return list.__getitem__(self, item)
    
    def __setitem__(self, item, value):
        try:
            return list.__setitem__(self, item, value)
        except IndexError:
            lnow = len(self)
            for i in range(lnow, item):
                if self.callDefault is False:
                    self.append(self.default)
                else:
                    self.append(self.default())
            self.append(value)

class Scalar(object):
    '''for those of us who miss perl scalars....'''

    def __init__(self, value = None):
        self.value = value
        self.valType = type(value)
    
    def toInt(self):
        valType = object.__getattribute__(self, "valType")
        value = object.__getattribute__(self, "value")
        if valType == int:
            return value
        elif valType == float or valType == long or valType == complex:
            return int(value)
        elif valType == str or valType == unicode:
            return len(value)
        elif value is None:
            return 0
        else:
            raise Exception("Could not force to Int " + valType)

    def toFloat(self):
        valType = object.__getattribute__(self, "valType")
        value = object.__getattribute__(self, "value")
        if valType == float or valType == long:
            return value
        elif valType == int or valType == complex:
            return float(value)
        elif valType == str or valType == unicode:
            return len(value) + 0.0
        elif value is None:
            return 0.0
        else:
            raise Exception("Could not force to Int " + valType)
      
    def toUnicode(self):
        valType = object.__getattribute__(self, "valType")
        value = object.__getattribute__(self, "value")
        if valType == unicode:
            return value
        elif valType == str:
            return unicode(value)
        elif valType == int or valType == float or valType == complex:
            return unicode(value)
        elif valType == None:
            return ""
        else:
            raise Exception("Could not force to Unicode " + valType)
           
    def __add__(self, newNum):
        valType = object.__getattribute__(self, "valType")
        value = object.__getattribute__(self, "value")
        newType = type(newNum)
        if valType in [int, float, complex, long]:
            if newType in [int, float, complex, long]:
                return Scalar(value + newNum)
            else:
                return Scalar(self.toUnicode() + newNum)
        elif valType == str:
            return Scalar(value + str(newNum))
        elif valType == unicode:
            return Scalar(value + unicode(newNum))
        elif value is None:
            return Scalar(newNum)
        else:
            raise Exception("Cannot add type " + valType)

    def __radd__(self, newNum):
        valType = object.__getattribute__(self, "valType")
        value = object.__getattribute__(self, "value")
        newType = type(newNum)
        if valType in [int, float, complex, long]:
            if newType in [int, float, complex, long]:
                return Scalar(newNum + value)
            else:
                return Scalar(newNum + self.toUnicode())
        elif valType == str:
            return Scalar(str(newNum) + value)
        elif valType == unicode:
            if newType != unicode and newType != str:
                newNum = str(newNum)
            return Scalar(unicode(newNum) + value)
        elif value is None:
            return Scalar(newNum)
        else:
            raise Exception("Cannot add type " + valType)

    def __sub__(self, newNum):
        valType = object.__getattribute__(self, "valType")
        value = object.__getattribute__(self, "value")
        newType = type(newNum)
        if valType == int or valType == float or valType == complex or valType == long:
            return Scalar(value - newNum)
        elif valType == str:
            raise Exception("Wouldnt it be cool to s/x// this?")
            return Scalar(value + str(newNum))
        elif valType == unicode:
            raise Exception("Wouldnt it be cool to s/x// this?")
            return Scalar(value + unicode(newNum))
        elif value is None:
            return Scalar(0 - newNum)
        else:
            raise Exception("Cannot subtract type %s " % valType)

    def __repr__(self):
        value = object.__getattribute__(self, "value")
        return value.__repr__()

    def __mod__(self, value):
        return int.__mod__(self.toInt(), value)        

    def __rmod__(self, value):
        return int.__mod__(value, self.toInt())        

    def __getattribute__(self, attribute):
        try:
            return object.__getattribute__(self, attribute)
        except AttributeError:
            try:
                print "Trying value method instead..."
                return self.value.__getattribute__(attribute)
            except AttributeError:
                print "Well, that didnt do it, hey, lets try lots of things!"
                try:
                    return int.__getattribute__(self.toInt(), attribute)
                except AttributeError:
                    try:
                        return unicode.__getattribute__(self.toUnicode(), attribute)
                    except AttributeError:
                        print "no more..."        
                         
#-------------------------------------------------------------------------------
def wrapWeakref(referent):
    '''
    utility function that wraps objects as weakrefs but does not wrap
    already wrapped objects
    '''
    if type(referent) is weakref.ref:
        return referent
    elif referent is None:
        return None
    else:
        return weakref.ref(referent)

def unwrapWeakref(referent):
    '''
    utility function that gets an object that might be an object itself
    or a weak reference to an object.
    
    >>> class Mock(object): pass
    >>> a1 = Mock()
    >>> a2 = Mock()
    >>> a2.strong = a1
    >>> a2.weak = wrapWeakref(a1)
    >>> unwrapWeakref(a2.strong) is a1
    True
    >>> unwrapWeakref(a2.weak) is a1
    True
    >>> unwrapWeakref(a2.strong) is unwrapWeakref(a2.weak)
    True
    '''
    if type(referent) is weakref.ref:
        unwrapped = referent()
        return unwrapped # could be None if referent has gone away!
    else:
        return referent
    

def isWeakref(referent):
    '''Test if an object is a weakref

    >>> class Mock(object): pass
    >>> a1 = Mock()
    >>> a2 = Mock()
    >>> isWeakref(a1)
    False
    >>> isWeakref(3)
    False
    >>> isWeakref(wrapWeakref(a1))
    True
    '''
    if type(referent) is weakref.ref:
        return True
    else:
        return False




#-------------------------------------------------------------------------------
class Iterator(object):
    '''A simple Iterator object used to handle iteration of Streams and other 
    list-like objects. 
    '''
    def __init__(self, data):
        self.data = data
        self.index = 0

    def __iter__(self):
        return self

    def next(self):
        if self.index >= len(self.data):
            raise StopIteration
        post = self.data[self.index]
        self.index += 1
        return post



#-------------------------------------------------------------------------------
class Timer(object):
    """An object for timing."""
        
    def __init__(self):
        # start on init
        self._tStart = time.time()
        self._tDif = 0
        self._tStop = None

    def start(self):
        '''Explicit start method; will clear previous values. Start always happens on initialization.'''
        self._tStart = time.time()
        self._tStop = None # show that a new run has started so __call__ works
        self._tDif = 0
    
    def stop(self):
        self._tStop = time.time()
        self._tDif = self._tStop - self._tStart

    def clear(self):
        self._tStop = None
        self._tDif = 0
        self._tStart = None

    def __call__(self):
        '''Reports current time or, if stopped, stopped time.
        '''
       # if stopped, gets _tDif; if not stopped, gets current time
        if self._tStop == None: # if not stoped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return t 

    def __str__(self):
        if self._tStop == None: # if not stoped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return str(round(t,3))




#-------------------------------------------------------------------------------
class TestMock(object):
    '''A test object with attributes, methods, and properties
    '''
    def __init__(self):
        self.attr1 = 1
        self.attr2 = 2
        self.attr3 = 3

        from music21 import environment
        _MOD = 'music21.common.TestMock'
        self._environLocal = environment.Environment(_MOD)
       

    def method1(self):
        return 3

    def method2(self):
        return 4

    def _get1(self):
        return self.attr3

    def _set1(self, value):
        self.attr3 = value
 
    def __deepcopy__(self, memo=None):
        # None is the empty memp default
        #self._environLocal.printDebug(['__deepcopy__ called, got memo', 
        #                              self, memo])
        new = self.__class__()
        for name in self.__dict__.keys():
            if name.startswith('_'): # avoid environemnt
                continue
            part = getattr(self, name)
            newValue = copy.deepcopy(part, memo)
            setattr(new, name, newValue)
        return new

    def __copy__(self, memo):
        self.environLocal.printDebug(['copy called'])
        return copy.copy(self, memo)


    property1 = property(_get1, _set1)

    property2 = property(_get1, _set1)




class Test(unittest.TestCase):

    def runTest(self):
        pass

    def setUp(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
        '''
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                a = copy.copy(obj)
                b = copy.deepcopy(obj)


    def testToRoman(self):
        for src, dst in [(1, 'I'), (3, 'III'), (5, 'V')]:
            self.assertEqual(dst, toRoman(src))


    def testGettingAttributes(self):
        a = TestMock()
        # dir() returns all names, including properties, attributes, methods
        aDir = dir(a)
        self.assertEqual(('_get1' in aDir), True)
        self.assertEqual(('attr1' in aDir), True)
        self.assertEqual(('method1' in aDir), True)
        self.assertEqual(('property1' in aDir), True)
        # __dict__ stores only attributes
        aDictKeys = a.__dict__.keys()
        self.assertEqual(('attr1' in aDictKeys), True)
        # properties are not found htere
        self.assertNotEqual(('property1' in aDictKeys), True)
        # after setting an attribute not defined in __init__ with a property
        # the new data value is store in __dict__
        a.property1 = 3
        aDictKeys = a.__dict__.keys()
        self.assertEqual(('attr3' in aDictKeys), True)

        # we cannot use insepct.isdatadescriptor to find properties
        self.assertEqual(inspect.isdatadescriptor(a.property1), False)
        

        methods, attributes, properties = dirPartitioned(a)
        self.assertEqual(('attr1' in attributes), True)



    def testDeepcopy(self):
        a = TestMock()
        b = TestMock()
        a.attr1 = b
        a.attr2 = b
        # test first by using copy.deepcopy
        c = copy.deepcopy(a)
        self.assertNotEqual(a, c)
        self.assertNotEqual(a.attr1, c.attr1)
        self.assertNotEqual(a.attr2, c.attr2)
        # but, the concept of the same object w/ two references is still there
        self.assertEqual(a.attr1, a.attr2)
        self.assertEqual(c.attr1, c.attr2)

        # test second by using the .deepcopy() method
        c = copy.deepcopy(a)
        self.assertNotEqual(a, c)
        self.assertNotEqual(a.attr1, c.attr1)
        self.assertNotEqual(a.attr2, c.attr2)
        self.assertEqual(a.attr1, a.attr2)
        self.assertEqual(c.attr1, c.attr2)
        


#-------------------------------------------------------------------------------
if __name__ == "__main__":
    ## do this the old way to avoid music21 import
    s1 = doctest.DocTestSuite(__name__)
    s2 = unittest.defaultTestLoader.loadTestsFromTestCase(Test)
    s1.addTests(s2)
    runner = unittest.TextTestRunner()
    runner.run(s1)  
