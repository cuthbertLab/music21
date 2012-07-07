# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common.py
# Purpose:      Basic Utilties
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza 
#
# Copyright:    (c) 2009-2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''Utility constants, dictionaries, functions, and objects used throughout music21.
'''

# should NOT import music21 or anything like that, except in doctests.
import re
import copy
import math, types, sys, os
import unittest, doctest
import fractions
import decimal
import time
import hashlib
import imp
import random
import inspect
import unicodedata


# define file extensions for various formats
# keys are assumed to be formats
fileExtensions = {
    'abc' : {'input': ['abc'], 'output': 'abc'},
    'text' : {'input': ['txt', 'text', 't'], 'output': 'txt'},
    'textline' : {'input': ['tl', 'textline'], 'output': 'txt'},
    'musicxml' : {'input': ['xml', 'mxl', 'mx'], 'output': 'xml'},
    'midi' : {'input': ['mid', 'midi'], 'output': 'mid'},
    'tinynotation' : {'input': ['tntxt', 'tinynotation'], 'output': 'tntxt'},
     # note: this is setting .zip as default mapping to musedata
    'musedata' : {'input': ['md', 'musedata', 'zip'], 'output': 'md'},
    'noteworthytext': {'input': ['nwctxt', 'nwc'], 'output': 'nwctxt'},
    'lilypond' : {'input': ['ly', 'lily'], 'output': 'ly'},
    'finale' : {'input': ['mus'], 'output': 'mus'},
    'humdrum' : {'input': ['krn'], 'output': 'krn'},
    'jpeg' : {'input': ['jpg', 'jpeg'], 'output': 'jpg'},
    'png'  : {'input': ['png', 'lily.png', 'lilypond.png'], 'output': 'png'},
    'pdf'  : {'input': ['pdf', 'lily.pdf', 'lilypond.pdf'], 'output': 'pdf'},
    'svg'  : {'input': ['svg', 'lily.svg', 'lilypond.svg'], 'output': 'svg'},
    'pickle' : {'input': ['p', 'pickle'], 'output': 'p'},
    'romantext' : {'input': ['rntxt', 'rntext', 'romantext', 'rtxt'], 'output': 'rntxt'},
    'scala' : {'input': ['scl'], 'output': 'scl'},
    'braille' : {'input' : ['brailleTextDoesNotWork'], 'output' : 'txt'},
    'vexflow' : {'input' : ['vexflowDoesNotWork'], 'output': 'html'},
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

# used for checking preferences, and for setting environment variables
VALID_SHOW_FORMATS = ['musicxml', 'lilypond', 'text', 'textline', 'midi', 'png', 'pdf', 'svg', 'lily.pdf', 'lily.png', 'lily.svg', 'braille', 'vexflow', 'vexflow.html', 'vexflow.js']
VALID_WRITE_FORMATS = ['musicxml', 'lilypond', 'text', 'textline', 'midi', 'png', 'pdf', 'svg', 'lily.pdf', 'lily.png', 'lily.svg', 'braille', 'vexflow', 'vexflow.html', 'vexflow.js']
VALID_AUTO_DOWNLOAD = ['ask', 'deny', 'allow']


#-------------------------------------------------------------------------------
# provide warning strings to users for use in conditional imports

def getMissingImportStr(modNameList):
    '''
    Given a list of missing module names, returns a nicely-formatted message to the user
    that gives instructions on how to expand music21 with optional packages.
    
    >>> from music21 import *
    >>> common.getMissingImportStr(['matplotlib'])
    'Certain music21 functions might need the optional package matplotlib; if you run into errors, install it by following the instructions at http://mit.edu/music21/doc/html/installAdditional.html'
    >>> common.getMissingImportStr(['matplotlib', 'numpy'])
    'Certain music21 functions might need these optional packages: matplotlib, numpy; if you run into errors, install it by following the instructions at http://mit.edu/music21/doc/html/installAdditional.html'

    '''
    if len(modNameList) == 0:
        return None
    elif len(modNameList) == 1:
        return 'Certain music21 functions might need the optional package %s; if you run into errors, install it by following the instructions at http://mit.edu/music21/doc/html/installAdditional.html' % modNameList[0]
    else:
        return 'Certain music21 functions might need these optional packages: %s; if you run into errors, install it by following the instructions at http://mit.edu/music21/doc/html/installAdditional.html' % ', '.join(modNameList)

#-------------------------------------------------------------------------------
def findFormat(fmt):
    '''Given a format defined either by a format name or 
    an extension, return the format name as well as the output exensions.

    Note that .mxl and .mx are only considered MusicXML input formats. 

    >>> from music21 import *
    >>> common.findFormat('mx')
    ('musicxml', '.xml')
    >>> common.findFormat('.mxl')
    ('musicxml', '.xml')
    >>> common.findFormat('musicxml')
    ('musicxml', '.xml')
    >>> common.findFormat('jpeg')
    ('jpeg', '.jpg')
    >>> common.findFormat('lily')
    ('lilypond', '.ly')
    >>> common.findFormat('jpeg')
    ('jpeg', '.jpg')
    >>> common.findFormat('humdrum')
    ('humdrum', '.krn')
    >>> common.findFormat('txt')
    ('text', '.txt')
    >>> common.findFormat('textline')
    ('textline', '.txt')
    >>> common.findFormat('midi')
    ('midi', '.mid')
    >>> common.findFormat('abc')
    ('abc', '.abc')
    >>> common.findFormat('scl')
    ('scala', '.scl')
    >>> common.findFormat('braille')
    ('braille', '.txt')
    >>> common.findFormat('vexflow')
    ('vexflow', '.html')
    

    Works the same whether you have a leading dot or not:
    

    >>> common.findFormat('md')
    ('musedata', '.md')
    >>> common.findFormat('.md')
    ('musedata', '.md')
    
    
    If you give something we can't deal with, returns a Tuple of None, None:
    
    >>> common.findFormat('wpd')
    (None, None)
    
    '''
    # make lower case, as some lilypond processing used upper case
    fmt = fmt.lower().strip()
    for key in fileExtensions.keys():
        if fmt.startswith('.'):
            fmt = fmt[1:] # strip .
        if fmt == key or fmt in fileExtensions[key]['input']:
            # add leading dot to extension on output
            return key, '.' + fileExtensions[key]['output']
    return None, None # if no match found


def findInputExtension(fmt):
    '''Given an input format, find and return all possible input extensions.

    >>> from music21 import *
    >>> a = common.findInputExtension('musicxml')
    >>> a
    ['.xml', '.mxl', '.mx']
    >>> a = common.findInputExtension('mx')
    >>> a
    ['.xml', '.mxl', '.mx']
    >>> a = common.findInputExtension('humdrum')
    >>> a
    ['.krn']
    >>> common.findInputExtension('musedata')
    ['.md', '.musedata', '.zip']
    '''
    fmt = findFormat(fmt)[0]
    if fmt == None:
        raise Exception('no match to format: %s' % fmt)
    post = []
    for ext in fileExtensions[fmt]['input']:
        if not ext.startswith('.'):
            ext = '.'+ext # must have a leading dot
        post.append(ext)
    return post

def findFormatFile(fp):
    '''Given a file path (relative or absolute) return the format

    >>> from music21 import *
    >>> common.findFormatFile('test.xml')
    'musicxml'
    >>> common.findFormatFile('long/file/path/test-2009.03.02.xml')
    'musicxml'
    >>> common.findFormatFile('long/file/path.intermediate.png/test-2009.03.xml')
    'musicxml'
    
    Windows drive + pickle
    >>> common.findFormatFile('d:/long/file/path/test.p')
    'pickle'
    
    On a windows networked filesystem
    >>> common.findFormatFile('\\\\long\\file\\path\\test.krn')
    'humdrum'
    '''
    fmt, ext = findFormat(fp.split('.')[-1])
    return fmt # may be None if no match


def findFormatExtFile(fp):
    '''Given a file path (relative or absolute) find format and extension used (not the output extension)

    >>> from music21 import *
    >>> common.findFormatExtFile('test.mx')
    ('musicxml', '.mx')
    >>> common.findFormatExtFile('long/file/path/test-2009.03.02.xml')
    ('musicxml', '.xml')
    >>> common.findFormatExtFile('long/file/path.intermediate.png/test-2009.03.xml')
    ('musicxml', '.xml')

    >>> common.findFormatExtFile('test.mus')
    ('finale', '.mus')

    >>> common.findFormatExtFile('test')
    (None, None)
    
    Windows drive + pickle
    >>> common.findFormatExtFile('d:/long/file/path/test.p')
    ('pickle', '.p')
    
    On a windows networked filesystem
    >>> common.findFormatExtFile('\\\\long\\file\\path\\test.krn')
    ('humdrum', '.krn')
    '''
    format, extOut = findFormat(fp.split('.')[-1])
    if format == None:
        return None, None
    else:
        return format, '.'+fp.split('.')[-1] # may be None if no match


def findFormatExtURL(url):
    '''Given a URL, attempt to find the extension. This may scrub arguments in a URL, or simply look at the last characters.

    >>> from music21 import *
    >>> urlA = 'http://kern.ccarh.org/cgi-bin/ksdata?l=cc/schubert/piano/d0576&file=d0576-06.krn&f=xml'
    >>> urlB = 'http://kern.ccarh.org/cgi-bin/ksdata?l=cc/schubert/piano/d0576&file=d0576-06.krn&f=kern'
    >>> urlC = 'http://kern.ccarh.org/cgi-bin/ksdata?l=cc/bach/cello&file=bwv1007-01.krn&f=xml'
    >>> urlD = 'http://static.wikifonia.org/4918/musicxml.mxl'
    >>> urlE = 'http://static.wikifonia.org/4306/musicxml.mxl'
    >>> urlF = 'http://junk'

    >>> common.findFormatExtURL(urlA)
    ('musicxml', '.xml')
    >>> common.findFormatExtURL(urlB)
    ('humdrum', '.krn')
    >>> common.findFormatExtURL(urlC)
    ('musicxml', '.xml')
    >>> common.findFormatExtURL(urlD)
    ('musicxml', '.mxl')
    >>> common.findFormatExtURL(urlE)
    ('musicxml', '.mxl')
    >>> common.findFormatExtURL(urlF)
    (None, None)
    '''
    ext = None
    # first, look for cgi arguments
    if '=xml' in url:
        ext = '.xml'
    elif '=kern' in url:
        ext = '.krn'
    # specific tag used on musedata.org
    elif 'format=stage2' in url or 'format=stage1' in url:
        ext = '.md'
    else: # check for file that ends in all known input extensions
        for key in fileExtensions.keys():
            for extSample in fileExtensions[key]['input']:
                if url.endswith('.' + extSample):
                    ext = '.' + extSample
                    break
    # presently, not keeping the extension returned from this function
    # reason: mxl is converted to xml; need to handle mxl files first
    if ext != None:
        format, junk = findFormat(ext)
        return format, ext
    else:
        return None, None    

def basicallyEqual(a, b):
    '''
    returns true if a and b are equal except for whitespace differences

    >>> from music21 import *
    >>> a = " hello there "
    >>> b = "hello there"
    >>> c = " bye there "
    >>> common.basicallyEqual(a,b)
    True
    >>> common.basicallyEqual(a,c)
    False
    '''
    a = WHITESPACE.sub('', a)
    b = WHITESPACE.sub('', b)
    a = LINEFEED.sub('', a)
    b = LINEFEED.sub('', b)
    if (a == b): 
        return True
    else: return False

basicallyEquals = basicallyEqual

def cleanupFloat(floatNum, maxDenominator=1000):
    '''
    Cleans up a floating point number by converting
    it to a fractions.Fraction object limited to
    a denominator of maxDenominator
    
    >>> from music21 import *
    >>> common.cleanupFloat(0.33333327824)
    0.333333333333...
    
    >>> common.cleanupFloat(0.142857)
    0.1428571428571...

    >>> common.cleanupFloat(1.5)
    1.5
    
    '''
    # this form only works w/ python2.7
    #f = fractions.Fraction(floatNum).limit_denominator(maxDenominator)

    # this works w/ python2.6, 2.7
    f = fractions.Fraction.from_float(
        floatNum).limit_denominator(maxDenominator)
    return float(f)


def roundToHalfInteger(num):
    '''Given a floating-point number, round to the nearest half-integer.  

    >>> from music21 import *
    >>> common.roundToHalfInteger(1.2)
    1
    >>> common.roundToHalfInteger(1.35)
    1.5
    >>> common.roundToHalfInteger(1.8)
    2
    >>> common.roundToHalfInteger(1.6234)
    1.5
    '''
    intVal, floatVal = divmod(num, 1.0)
    intVal = int(intVal)
    if floatVal < .25:
        floatVal = 0
    elif floatVal >= .25 and floatVal < .75 :
        floatVal = .5
    else:
        floatVal = 1
    return intVal + floatVal


def almostEquals(x, y = 0.0, grain=1e-7):
    '''
    The following four routines work for comparisons between floats that are normally inconsistent.
    
    almostEquals(x, y) -- returns True if x and y are within 0.0000001 of each other


    >>> from music21 import common
    >>> common.almostEquals(1.000000001, 1)
    True 
    >>> common.almostEquals(1.001, 1)
    False
    >>> common.almostEquals(1.001, 1, grain=0.1)
    True
    
    '''
    if abs(x - y) < grain: 
        return True
    return False

almostEqual = almostEquals


def nearestCommonFraction(x, grain=1e-2):
    '''Given a value that suggests a floating point fraction, like .33, 
    return a float that provides greater specification, such as .333333333
        
    >>> from music21 import *
    >>> common.nearestCommonFraction(.333) == 1/3.
    True
    >>> common.nearestCommonFraction(.33) == 1/3.
    True
    >>> common.nearestCommonFraction(.35) == 1/3.
    False
    >>> common.nearestCommonFraction(.2) == .2
    True
    >>> common.nearestCommonFraction(.125)
    0.125
    '''
    if isStr(x):
        x = float(x)

    values = [1/3., 2/3., 
              1/6., 2/6., 3/6., 4/6., 5/6.]
    for v in values:
        if almostEquals(x, v, grain=grain):
            return v
    return x


def greaterThan(x, y = 0.0, grain=1e-7):
    '''
    greaterThan returns True if x is greater than and not almostEquals y

    >>> from music21 import *
    >>> common.greaterThan(5, 4)
    True
    >>> common.greaterThan(5.05, 5.02)
    True
    >>> common.greaterThan(5.000000000005, 5.000000000006)
    False
    >>> common.greaterThan(5.000000000006, 5.000000000005)
    False
    '''
    if x < y or almostEquals(x, y, grain): 
        return False
    return True

def greaterThanOrEqual(x, y=0.0, grain=1e-7):
    '''
    greaterThan returns True if x is greater than or almostEquals y
    '''
    if x > y or almostEquals(x, y, grain): 
        return True
    return False


def lessThan(x, y = 0.0, grain=1e-7):
    '''
    lessThan -- returns True if x is less than and not almostEquals y

    >>> from music21 import *
    >>> common.lessThan(5, 4)
    False
    >>> common.lessThan(5.2, 5.5)
    True
    >>> common.lessThan(5.2, 5.5, grain=1)
    False
    >>> common.lessThan(5.000000000005, 5.000000000006)
    False
    >>> common.lessThan(5.000000000006, 5.000000000005)
    False

    '''
    if x > y or almostEquals(x, y, grain): 
        return False
    return True    


def lessThanOrEqual(x, y = 0.0, grain=1e-7):
    '''
    lessThan -- returns True if x is less than and not almostEquals y

    >>> from music21 import *
    >>> common.lessThanOrEqual(4, 4)
    True
    >>> common.lessThanOrEqual(5.2, 5.5)
    True
    >>> common.lessThanOrEqual(5.2, 5.5)
    True
    >>> common.lessThanOrEqual(5.000000000005, 5.000000000006)
    True

    '''
    if x < y or almostEquals(x, y, grain): 
        return True
    return False    

    
def isPowerOfTwo(n):
    ''' 
    returns True if argument is either a power of 2 or a reciprocal
    of a power of 2. Uses almostEquals so that a float whose reminder after
    taking a log is nearly zero is still True

    >>> from music21 import *
    >>> common.isPowerOfTwo(3)
    False
    >>> common.isPowerOfTwo(18)
    False
    >>> common.isPowerOfTwo(1024)
    True
    >>> common.isPowerOfTwo(1024.01)
    False
    >>> common.isPowerOfTwo(1024.00001)
    True

    OMIT_FROM_DOCS
    >>> common.isPowerOfTwo(10)
    False
    '''

    if n <= 0:
        return False
    
    (remainder, throwAway) = math.modf(math.log(n, 2))
    if (almostEquals(remainder, 0.0)): 
        return True
    else: 
        return False


def nearestMultiple(n, unit):
    '''Given a positive value `n`, return the nearest multiple of the supplied `unit` as well as the difference (error) to 
    seven significant digits.

    >>> from music21 import *
    >>> print common.nearestMultiple(.25, .25)
    (0.25, 0.0)
    >>> print common.nearestMultiple(.35, .25)
    (0.25, 0.1...)
    
    Note that this one also has an error of .1 but it's a positive error off of 0.5
    >>> print common.nearestMultiple(.4, .25)
    (0.5, 0.1...)



    >>> common.nearestMultiple(.4, .25)[0]
    0.5
    >>> common.nearestMultiple(23404.001, .125)[0]
    23404.0
    >>> common.nearestMultiple(23404.134, .125)[0]
    23404.125
    >>> common.nearestMultiple(.001, .125)[0]
    0.0

    >>> common.almostEquals(common.nearestMultiple(.25, (1/3.))[0], .33333333)
    True
    >>> common.almostEquals(common.nearestMultiple(.55, (1/3.))[0], .66666666)
    True
    >>> common.almostEquals(common.nearestMultiple(234.69, (1/3.))[0], 234.6666666)
    True
    >>> common.almostEquals(common.nearestMultiple(18.123, (1/6.))[0], 18.16666666)
    True


    '''
    if n < 0:
        raise Exception('cannot find nearest multiple for a value less than the unit: %s, %s' % (n, unit))

    mult = math.floor(n / float(unit)) # can start with the floor 
    halfUnit = unit / 2.0

    matchLow = unit * mult
    matchHigh = unit * (mult + 1)

    #print(['mult, halfUnit, matchLow, matchHigh', mult, halfUnit, matchLow, matchHigh])

    if matchLow >= n >= matchHigh:
        raise Exception('cannot place n between multiples: %s, %s', matchLow, matchHigh)

    if n >= matchLow and n < (matchLow + halfUnit):
        return matchLow, round(n - matchLow, 7)
    elif n >= (matchHigh - halfUnit) and n <= matchHigh:
        return matchHigh, round(matchHigh - n, 7)
       

def standardDeviation(coll, bassel=False):
    '''Given a collection of values, return the standard deviation.

    >>> from music21 import *
    >>> common.standardDeviation([2,4,4,4,5,5,7,9])
    2.0
    >>> common.standardDeviation([600, 470, 170, 430, 300])
    147.3227...
    >>> common.standardDeviation([4, 2, 5, 8, 6], bassel=True)
    2.23606...
    '''
    avg = sum(coll) / float(len(coll))
    diffColl = [math.pow(val-avg, 2) for val in coll]
    # with a sample standard deviation (not a whole population)
    # subtract 1 from the length
    # this is bassel's correction
    if bassel:
        return math.sqrt(sum(diffColl) / float(len(diffColl)-1))
    else:
        return math.sqrt(sum(diffColl) / float(len(diffColl)))


def isNum(usrData):
    '''check if usrData is a number (float, int, long, Decimal), return boolean
    IMPROVE: when 2.6 is everywhere: add numbers class.

    >>> from music21 import *
    >>> common.isNum(3.0)
    True
    >>> common.isNum(3)
    True
    >>> common.isNum('three')
    False
    '''
    try:
        # TODO: this may have unexpected consequences: find
        x = usrData + 0
        return True
    except:
        return False

#     if (isinstance(usrData, int) or 
#         isinstance(usrData, float) or 
#         isinstance(usrData, long) or
#         isinstance(usrData, decimal.Decimal)):
#         return True
#     else:
#         return False        


def isStr(usrData):
    """Check of usrData is some form of string, including unicode.

    >>> from music21 import *
    >>> common.isStr(3)
    False
    >>> common.isStr('sharp')
    True
    >>> common.isStr(u'flat')
    True
    """
    if isinstance(usrData, basestring):
#     if (isinstance(usrData, str) or 
#         isinstance(usrData, unicode)):
        return True
    else:
        return False                


def isListLike(usrData):
    """
    Returns True if is a List or a Set or a Tuple

    >>> from music21 import *
    >>> common.isListLike([])
    True
    >>> common.isListLike('sharp')
    False
    >>> common.isListLike((None, None))
    True
    >>> common.isListLike(stream.Stream())
    False
    """
    #TODO: add immutable sets and pre 2.6 set support
    if (isinstance(usrData, list) or 
        isinstance(usrData, tuple) or
        isinstance(usrData, set)):
        return True
    else:
        return False            

def isIterable(usrData):
    """
    Returns True if is the object can be iter'd over

    >>> from music21 import *
    >>> common.isIterable([5, 10])
    True
    >>> common.isIterable('sharp')
    False
    >>> common.isIterable((None, None))
    True
    >>> common.isIterable(stream.Stream())
    True
    """
    if hasattr(usrData, "__iter__"):
        return True
    else:
        return False


def toUnicode(usrStr):
    '''Convert this tring to a uncode string; if already a unicode string, do nothing.
        
    >>> from music21 import *
    >>> common.toUnicode('test')
    u'test'
    >>> common.toUnicode(u'test')
    u'test'
    '''
    try:
        usrStr = unicode(usrStr, 'utf-8')
    # some documentation may already be in unicode; if so, a TypeException will be raised
    except TypeError: #TypeError: decoding Unicode is not supported
        pass
    return usrStr


def classToClassStr(classObj):
    '''Convert a class object to a class string.

    >>> from music21 import *
    >>> common.classToClassStr(note.Note)
    'Note'
    >>> common.classToClassStr(chord.Chord)
    'Chord'
    '''
    # remove closing quotes
    return str(classObj).split('.')[-1][:-2]

def getNumFromStr(usrStr, numbers='0123456789'):
    '''Given a string, extract any numbers. Return two strings, the numbers (as strings) and the remaining characters.

    >>> from music21 import *
    >>> common.getNumFromStr('23a')
    ('23', 'a')
    >>> common.getNumFromStr('23a954sdfwer')
    ('23954', 'asdfwer')
    >>> common.getNumFromStr('')
    ('', '')
    '''
    found = []
    remain = []
    for char in usrStr:
        if char in numbers:
            found.append(char)
        else:
            remain.append(char)
    # returns numbers, and then characters
    return ''.join(found), ''.join(remain)


def numToIntOrFloat(value):
    '''Given a number, return an integer if it is very close to an integer, otherwise, return a float.

    >>> from music21 import *
    >>> common.numToIntOrFloat(1.0)
    1
    >>> common.numToIntOrFloat(1.00003)
    1.00003
    >>> common.numToIntOrFloat(1.5)
    1.5
    >>> common.numToIntOrFloat(1.0000000005)
    1
    '''
    intVal = int(round(value))
    if almostEquals(intVal, value, 1e-6):
        return intVal
    else: # source
        return value


def spaceCamelCase(usrStr, replaceUnderscore=True):
    '''Given a camel-cased string, or a mixture of numbers and characters, create a space separated string.

    If replaceUnderscore is True (default) then underscores also become spaces (but without the _)

    >>> from music21 import *
    >>> common.spaceCamelCase('thisIsATest')
    'this Is A Test'
    >>> common.spaceCamelCase('ThisIsATest')
    'This Is A Test'
    >>> common.spaceCamelCase('movement3')
    'movement 3'
    >>> common.spaceCamelCase('opus41no1')
    'opus 41 no 1'
    >>> common.spaceCamelCase('opus23402no219235')
    'opus 23402 no 219235'
    >>> common.spaceCamelCase('opus23402no219235').title()
    'Opus 23402 No 219235'

    >>> common.spaceCamelCase('hello_myke')
    'hello myke'
    >>> common.spaceCamelCase('hello_myke', replaceUnderscore = False)
    'hello_myke'

    '''
    numbers = '0123456789.'
    firstNum = False
    firstChar = False
    isNum = False
    lastIsNum = False
    post = []

    for char in usrStr:
        if char in numbers:
            isNum = True
        else:
            isNum = False

        if isNum and not firstNum and not lastIsNum: 
            firstNum = True
        else:
            firstNum = False

        # for chars
        if not isNum and not firstChar and lastIsNum: 
            firstChar = True
        else:
            firstChar = False

        if len(post) > 0:
            if char.isupper() or firstNum or firstChar:
                post.append(' ')
            post.append(char)
        else: # first character
            post.append(char)

        if isNum:
            lastIsNum = True
        else:
            lastIsNum = False
    postStr = ''.join(post)
    if replaceUnderscore:
        postStr = postStr.replace('_', ' ')
    return postStr


def getPlatform():
    '''
    Return the name of the platform, where platforms are divided 
    between 'win' (for Windows), 'darwin' (for MacOS X), and 'nix' for (GNU/Linux and other variants).
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
    
    >>> from music21 import *
    >>> common.dotMultiplier(1)
    1.5
    >>> common.dotMultiplier(2)
    1.75
    >>> common.dotMultiplier(3)
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

    >>> from music21 import *
    >>> common.decimalToTuplet(1.5)
    (3, 2)
    >>> common.decimalToTuplet(1.25)
    (5, 4)
    '''

    def findSimpleFraction(working):
        'Utility function.'
        for i in range(1,1000):
            for j in range(i,2*i):
                if almostEquals(working, (j+0.0)/i):
                    return (int(j), int(i))
        return (0,0)

    remainder, multiplier = math.modf(decNum)
    working = decNum/multiplier

    (jy, iy) = findSimpleFraction(working)

    if iy == 0:
        raise Exception("No such luck")

    jy *= multiplier
    gcd = euclidGCD(int(jy), int(iy))
    jy = jy/gcd
    iy = iy/gcd
    return (int(jy), int(iy))




def unitNormalizeProportion(values):
    """Normalize values within the unit interval, where max is determined by the sum of the series.

    >>> from music21 import *
    >>> common.unitNormalizeProportion([0,3,4])
    [0.0, 0.42857142857142855, 0.5714285714285714]
    >>> common.unitNormalizeProportion([1,1,1])
    [0.3333333..., 0.333333..., 0.333333...]
    
    
    On 32-bit computers this number is inexact.  On 64-bit it works fine.
    
    
    #>>> common.unitNormalizeProportion([.2, .6, .2])
    #[0.20000000000000001, 0.59999999999999998, 0.20000000000000001]
    """
    # note: negative values should be shifted to positive region first
    sum = 0
    for x in values:
        if x < 0: 
            raise ValueError('value members must be positive')
        sum += x
    unit = [] # weights on the unit interval; sum == 1
    for x in values:
        unit.append((x / float(sum)))
    return unit

def unitBoundaryProportion(series):
    """Take a series of parts with an implied sum, and create unit-interval boundaries proportional to the series components.

    >>> from music21 import *
    >>> common.unitBoundaryProportion([1,1,2])
    [(0, 0.25), (0.25, 0.5), (0.5, 1.0)]
    >>> common.unitBoundaryProportion([8,1,1])
    [(0, 0.8...), (0.8..., 0.9...), (0.9..., 1.0)]
    """
    unit = unitNormalizeProportion(series)
    bounds = []
    sum = 0
    for i in range(len(unit)):
        if i != len(unit) - 1: # not last
            bounds.append((sum, sum + unit[i])) 
            sum += unit[i]
        else: # last, avoid rounding errors
            bounds.append((sum, 1.0))            
    return bounds


def weightedSelection(values, weights, randomGenerator=None):
    '''Given a list of values and an equal-sized list of weights, return a randomly selected value using the weight.

    Example: sum -1 and 1 for 100 values; should be around 0 or at least between -30 and 30

    >>> from music21 import *
    >>> -30 < sum([common.weightedSelection([-1, 1], [1,1]) for x in range(100)]) < 30
    True
    '''
    if randomGenerator is not None:
        q = randomGenerator() # must be in unit interval
    else: # use random uniform
        q = random.random()
    # normalize weights w/n unit interval
    boundaries = unitBoundaryProportion(weights)
    for i, (low, high) in enumerate(boundaries):
        if q >= low and q < high: # accepts both boundaries
            return values[i]
    # just in case we get the high boundary
    return values[i]


def euclidGCD(a, b):
    '''use Euclid\'s algorithm to find the GCD of a and b

    >>> from music21 import *
    >>> common.euclidGCD(2,4)
    2
    >>> common.euclidGCD(20,8)
    4
    '''
    if b == 0:
        return a
    else:
        return euclidGCD(b, a % b)
    

def approximateGCD(values, grain=1e-4):
    '''Given a list of values, find the lowest common divisor of floating point values. 

    >>> from music21 import *
    >>> common.approximateGCD([2.5,10, .25])
    0.25
    >>> common.approximateGCD([2.5,10])
    2.5
    >>> common.approximateGCD([2,10])
    2.0
    >>> common.approximateGCD([1.5, 5, 2, 7])
    0.5
    >>> common.approximateGCD([2,5,10])
    1.0
    >>> common.approximateGCD([2,5,10,.25])
    0.25
    >>> str(common.approximateGCD([1/3.,2/3.]))
    '0.333333333333'
    >>> str(common.approximateGCD([5/3.,2/3.,4]))
    '0.333333333333'
    >>> str(common.approximateGCD([5/3.,2/3.,5]))
    '0.333333333333'
    >>> str(common.approximateGCD([5/3.,2/3.,5/6.,3/6.]))
    '0.166666666667'

    '''
    lowest = float(min(values))

    # quick method: see if the smallest value is a common divisor of the rest
    count = 0
    for x in values:
        # lowest is already a float
        junk, floatingValue = divmod(x / lowest, 1.0)
        # if almost an even division
        if almostEqual(floatingValue, 0.0, grain=grain):
            count += 1
    if count == len(values):
        return lowest

    # assume that one of these divisions will match
    divisors = [1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12., 13., 14., 15., 16.]
    divisions = [] # a list of lists, one for each entry
    uniqueDivisions = []
    for i in values:
        coll = []
        for d in divisors:
            v = i / d
            coll.append(v) # store all divisions
            if v not in uniqueDivisions:
                uniqueDivisions.append(v)
        divisions.append(coll)
    # find a unique divisor that is found in collected divisors
    commonUniqueDivisions = []
    for v in uniqueDivisions:
        count = 0
        for coll in divisions:
            for x in coll:
                # grain here is set low, mostly to catch triplets
                if almostEquals(x, v, grain=grain):
                    count += 1
                    break # exit the iteration of coll; only 1 match possible
        # store any division that is found in all values
        if count == len(divisions):
            commonUniqueDivisions.append(v)
    if len(commonUniqueDivisions) == 0:
        raise Exception('cannot find a common divisor')
    return max(commonUniqueDivisions)


def _lcm(a, b):
    """find lowest common multiple of a,b"""
    # // forcers integer style division (no remainder)
    return abs(a*b) / euclidGCD(a,b) 

def lcm(filter):
    '''
    Find the least common multiple of a list of values
    
    >>> from music21 import *
    >>> common.lcm([3,4,5])
    60
    >>> common.lcm([3,4])
    12
    >>> common.lcm([1,2])
    2
    >>> common.lcm([3,6])
    6
    '''
    # derived from 
    # http://www.oreillynet.com/cs/user/view/cs_msg/41022
    lcmVal = 1
    for i in range(len(filter)):
        lcmVal = _lcm(lcmVal, filter[i])
    return lcmVal


def groupContiguousIntegers(src):
    '''Given a list of integers, group contiguous values into sub lists

    >>> from music21 import *
    >>> common.groupContiguousIntegers([3, 5, 6])
    [[3], [5, 6]]
    >>> common.groupContiguousIntegers([3, 4, 6])
    [[3, 4], [6]]
    >>> common.groupContiguousIntegers([3, 4, 6, 7])
    [[3, 4], [6, 7]]
    >>> common.groupContiguousIntegers([3, 4, 6, 7, 20])
    [[3, 4], [6, 7], [20]]
    >>> common.groupContiguousIntegers([3, 4, 5, 6, 7])
    [[3, 4, 5, 6, 7]]
    >>> common.groupContiguousIntegers([3])
    [[3]]
    >>> common.groupContiguousIntegers([3, 200])
    [[3], [200]]
    '''
    if len(src) <= 1:
        return [src]
    post = []
    group = []
    src.sort()
    i = 0
    while i < (len(src)-1):
        e = src[i]
        group.append(e)
        eNext = src[i+1]
        # if next is contiguous, add to grou
        if eNext != e + 1:
        # if not contiguous
            post.append(group)
            group = []
        # second to last elements; handle separately 
        if i == len(src)-2:
            # need to handle next elements
            group.append(eNext)
            post.append(group)

        i += 1

    return post


def fromRoman(num):
    '''
    
    Convert a Roman numeral (upper or lower) to an int

    http://code.activestate.com/recipes/81611-roman-numerals/
    
    >>> from music21 import *
    >>> common.fromRoman('ii')
    2
    >>> common.fromRoman('vii')
    7
    
    Works with both IIII and IV forms:
    >>> common.fromRoman('MCCCCLXXXIX')
    1489
    >>> common.fromRoman('MCDLXXXIX')
    1489


    some people consider this an error, but you see it in medieval documents:
    >>> common.fromRoman('ic')
    99

    but things like this are never seen and cause an error:
    >>> common.fromRoman('vx')
    Traceback (most recent call last):
    Music21CommonException: input contains an invalid subtraction element: vx

    '''
    input = num.upper()
    nums = ['M', 'D', 'C', 'L', 'X', 'V', 'I']
    ints = [1000, 500, 100, 50,  10,  5,   1]
    places = []
    for c in input:
       if not c in nums:
          raise Music21CommonException("input is not a valid roman numeral: %s" % input)
    for i in range(len(input)):
       c = input[i]
       value = ints[nums.index(c)]
       # If the next place holds a larger number, this value is negative.
       try:
           nextvalue = ints[nums.index(input[i +1])]
           if nextvalue > value and value in [1, 10, 100]:
               value *= -1
           elif nextvalue > value:
               raise Music21CommonException("input contains an invalid subtraction element: %s" % num)
       except IndexError:
          # there is no next place.
          pass
       places.append(value)
    sum = 0
    for n in places: sum += n
    return sum
    # Easiest test for validity...
    #if int_to_roman(sum) == input:
    #   return sum
    #else:
    #   raise ValueError, 'input is not a valid roman numeral: %s' % input
    
def toRoman(num):
    '''
    
    Convert a number from 1 to 3999 to a roman numeral
    
    >>> from music21 import *
    >>> common.toRoman(2)
    'II'
    >>> common.toRoman(7)
    'VII'
    >>> common.toRoman(1999)
    'MCMXCIX'

    >>> common.toRoman("hi")
    Traceback (most recent call last):
    TypeError: expected integer, got <type 'str'>
    '''
    if type(num) != type(1):
       raise TypeError("expected integer, got %s" % type(num))
    if not 0 < num < 4000:
       raise ValueError, "Argument must be between 1 and 3999"   
    ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
    nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
    result = ""
    for i in range(len(ints)):
        count = int(num/ ints[i])
        result += nums[i] * count
        num -= ints[i] * count
    return result


def ordinalAbbreviation(value, plural=False):
    '''Return the ordinal abbreviations for integers

    >>> from music21 import common
    >>> common.ordinalAbbreviation(3)
    'rd'
    >>> common.ordinalAbbreviation(255)
    'th'
    >>> common.ordinalAbbreviation(255, plural=True)
    'ths'

    '''
    valueStr = str(value)
    if value in [1]:
        post = 'st'
    elif value in [0, 4, 5, 6, 7, 8, 9, 11, 12, 13]:
        post = 'th'
    elif value in [2]:
        post = 'nd'
    elif value in [3]:
        post = 'rd'
    # test strings if not matched here
    elif valueStr[-1] in ['1']:
        post = 'st'
    elif valueStr[-1] in ['2']:
        post = 'nd'
    elif valueStr[-1] in ['3']:
        post = 'rd'
    elif valueStr[-1] in ['0', '4', '5', '6', '7', '8', '9']:
        post = 'th'

    if post != 'st' and plural:
        post += 's'
    return post

                


def stripAddresses(textString, replacement = "ADDRESS"):
    '''
    Function that changes all memory addresses in the given 
    textString with (replacement).  This is useful for testing
    that a function gives an expected result even if the result
    contains references to memory locations.  So for instance:

    >>> from music21 import *
    >>> common.stripAddresses("{0.0} <music21.clef.TrebleClef object at 0x02A87AD0>")
    '{0.0} <music21.clef.TrebleClef object at ADDRESS>'
    
    while this is left alone:

    >>> common.stripAddresses("{0.0} <music21.humdrum.MiscTandam *>I humdrum control>")
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

    >>> from music21 import *
    >>> import os
    >>> a = os.listdir(os.curdir)
    >>> b = common.sortFilesRecent(a)
    '''
    sort = []
    for fp in fileList:
        lastmod = time.localtime(os.stat(fp)[8])
        sort.append([lastmod, fp])
    sort.sort()
    sort.reverse()
    # just return 
    return [y for x, y in sort] 


def getMd5(value=None):
    '''Return a string from an md5 haslib
    
    >>> from music21 import *
    >>> common.getMd5('test')
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

    >>> from music21 import *
    >>> a = common.formatStr('test', '1', 2, 3)
    >>> print a
    test 1 2 3
    <BLANKLINE>
    '''
    if 'format' in keywords.keys():
        format = keywords['format']
    else:
        format = None

    msg = [msg] + list(arguments)
    msg = [str(x) for x in msg]
    if format == 'block':
        return '\n*** '.join(msg)+'\n'
    else: # catch all others
        return ' '.join(msg)+'\n'



def dirPartitioned(obj, skipLeading=['__']):
    '''Given an object, return three lists of names: methods, attributes, and properties.

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
# tools for setup.py
def getSourceFilePath():
    '''Get the music21 directory that contains source files. This is not the same as the outermost package development directory. 
    '''
    import music21
    fpMusic21 = music21.__path__[0] # list, get first item
    # use corpus as a test case
    if 'corpus' not in os.listdir(fpMusic21):
        raise Exception('cannot find expected music21 directory: %s' % fpMusic21)
    return fpMusic21


def getBuildDocRstFilePath():
    '''Return the directory that contains the documentation RST files.
    '''
    outer = os.path.dirname(getSourceFilePath())
    post = os.path.join(outer, 'buildDoc', 'rst')
    if os.path.exists(post):
        return post
    raise Exception('no such path exists: %s' % post)

def getBuildDocFilePath():
    '''Return the directory that contains the documentation RST files.
    '''
    outer = os.path.dirname(getSourceFilePath())
    post = os.path.join(outer, 'buildDoc')
    if os.path.exists(post):
        return post
    raise Exception('no such path exists: %s' % post)


def getTestDocsFilePath():
    '''Return the directory that contains the documentation RST files.
    '''
    post = os.path.join(getSourceFilePath(), 'test', 'testDocs')
    if os.path.exists(post):
        return post
    raise Exception('no such path exists: %s' % post)

def getMetadataCacheFilePath():
    '''Get the stored music21 directory that contains the corpus metadata cache. 

    >>> from music21 import *
    >>> fp = common.getMetadataCacheFilePath()
    >>> fp.endswith('corpus/metadataCache') or fp.endswith(r'corpus\metadataCache')
    True
    '''
    return os.path.join(getSourceFilePath(), 'corpus', 'metadataCache')

def getCorpusFilePath():
    '''Get the stored music21 directory that contains the corpus metadata cache. 

    >>> from music21 import *
    >>> fp = common.getCorpusFilePath()
    >>> fp.endswith('music21/corpus') or fp.endswith(r'music21\corpus')
    True
    '''
    return os.path.join(getSourceFilePath(), 'corpus')

def getCorpusContentDirs():
    '''Get all dirs that are found in the corpus that contain content; that is, exclude dirst that have code or other resoures.

    >>> from music21 import *
    >>> fp = common.getCorpusContentDirs()
    >>> fp # this test will be fragile, depending on composition of dirs
    ['airdsAirs', 'bach', 'beethoven', 'ciconia', 'corelli', 'cpebach', 'demos', 'essenFolksong', 'handel', 'haydn', 
    'josquin', 'leadSheet', 'license.txt', 'luca', 'miscFolk', 'monteverdi', 'mozart', 'oneills1850', 'ryansMammoth', 
    'schoenberg', 'schumann', 'theoryExercises', 'trecento', 'verdi']
    '''
    dir = getCorpusFilePath()
    post = []
    # dirs to exclude; all files will be retained
    exclude = ['__init__.py', 'base.py', 'metadataCache', 'virtual.py', 'chorales.py'] 
    for fn in os.listdir(dir):
        if fn not in exclude:
            if not fn.endswith('.pyc') and not fn.startswith('.'):
                post.append(fn)
    return post


def getPackageDir(fpMusic21=None, relative=True, remapSep='.',
     packageOnly=True):
    '''Manually get all directories in the music21 package, including the top level directory. This is used in setup.py.
    
    If `relative` is True, relative paths will be returned. 

    If `remapSep` is set to anything other than None, the path separator will be replaced. 

    If `packageOnly` is true, only directories with __init__.py files are colllected. 
    '''
    if fpMusic21 == None:
        import music21
        fpMusic21 = music21.__path__[0] # list, get first item

    # a test if this is the correct directory
    if 'corpus' not in os.listdir(fpMusic21):
        raise Exception('cannot find corpus within %s' % fpMusic21)
    #fpCorpus = os.path.join(fpMusic21, 'corpus')
    fpParent = os.path.dirname(fpMusic21)
    match = []
    for dirpath, dirnames, filenames in os.walk(fpMusic21):
        # remove hidden directories
        if ('%s.' % os.sep) in dirpath:
            continue
        elif '.svn' in dirpath:
            continue
        if packageOnly:
            if '__init__.py' not in filenames: # must be to be a package
                continue
        # make relative
        if relative:
            fp = dirpath.replace(fpParent, '')
            if fp.startswith(os.sep):
                fp = fp[fp.find(os.sep)+len(os.sep):]
        else:
            fp = dirpath
        # replace os.sep
        if remapSep != None:
            fp = fp.replace(os.sep, remapSep)
        match.append(fp)
    return match


def getPackageData():
    '''Return a list of package data in the format specified by setup.py. This creates a very inclusive list of all data types. 
    '''
    # include these extensions for all directories, even if they are not normally there.
    # also need to update writeManifestTemplate() in setup.py when adding
    # new file extensions
    ext = ['txt', 'xml', 'krn', 'mxl', 'pdf', 'html', 
           'css', 'js', 'png', 'tiff', 'jpg', 'xls', 'mid', 'abc', 'json', 'md', 
           'zip', 'rntxt', 'command', 'scl', 'nwctxt', 'wav']

    # need all dirs, not just packages, and relative to music21
    fpList = getPackageDir(fpMusic21=None, relative=True, remapSep=None,
                            packageOnly=False)
    stub = 'music21%s' % os.sep
    match = []
    for fp in fpList:
        # these are relative to music21 package, so remove music21
        if fp == 'music21':
            continue
        elif fp.startswith(stub):
            fp = fp[fp.find(stub)+len(stub):]
        for e in ext:
            target = fp + os.sep + '*.%s' % e
            match.append(target)

    return match


#-------------------------------------------------------------------------------

    
'''The following are a set of objects with more relaxed behaviors for quicker writing.

Most of these objects behave more like perl; for Python converts.

A set of quick and dirty objects to make coding a bit easier for people who have
been coding in perl for years.  Prevents things like KeyErrors, etc.  Tradeoff
is that typos of keys etc. are harder to detect (and some run speed tradeoff I'm sure).
Advantage is coding time and fewer type errors while coding.
'''

class DefaultHash(dict):
    '''A replacement for dictionaries that behave a bit more like perl hashes.  
    No more KeyErrors. The difference between DefaultHash and defaultdict is that the 
    Dict values come first in the definition and that default can be set to 
    None (which it is) or to any object.
    
    If you want a factory that makes hashes with a particular different default, use:
    
        falsehash = lambda h = None: common.DefaultHash(h, default = False)
        a = falsehash({"A": falsehash(), "B": falsehash()})
        print(a["A"]["hi"]) # returns False
    
    there's probably a way to use this to create a data structure
    of arbitrary dimensionality, though it escapes this author.

    if callDefault is True then the default is called:
    
        common.DefaultHash(default = list, callDefault = True)
        
    will create a new List for each element
    '''
    def __init__(self, hash = None, default=None, callDefault=False):
        if hash:
            dict.__init__(self, hash)
        else:
            dict.__init__(self)
        self.default = default
        self.callDefault = callDefault
    
    def __getitem__(self, key):
        # NOTE: this is perforamnce critical method and should be as fast as 
        # possible
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if not self.callDefault:
                return self.default
            else:
                dict.__setitem__(self, key, self.default())
                return dict.__getitem__(self, key)

    def __len__(self):
        return dict.__len__(self)

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




# this presently is not used anywhere in music21

class Scalar(object):
    '''for those of us who miss perl scalars....'''

    def __init__(self, value = None):
        self.value = value
        self.valType = type(value)
    
    def toInt(self):
        '''Return an integer.
        '''
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
        '''Return a float.
        '''
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
        '''Return unicode.
        '''
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
        #newType = type(newNum)

        if valType == int or valType == float or valType == complex or valType == long:
            return Scalar(value - newNum)
        elif valType == str:
            raise Exception("Wouldnt it be cool to s/x// this?")
            #return Scalar(value + str(newNum))
        elif valType == unicode:
            raise Exception("Wouldnt it be cool to s/x// this?")
            #return Scalar(value + unicode(newNum))
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
                print("Trying value method instead...")
                return self.value.__getattribute__(attribute)
            except AttributeError:
                print("Well, that didnt do it, hey, lets try lots of things!")
                try:
                    return int.__getattribute__(self.toInt(), attribute)
                except AttributeError:
                    try:
                        return unicode.__getattribute__(self.toUnicode(), attribute)
                    except AttributeError:
                        print("no more...")
                         





#-------------------------------------------------------------------------------
def wrapWeakref(referent):
    '''
    utility function that wraps objects as weakrefs but does not wrap
    already wrapped objects
    '''
    import weakref
    #if type(referent) is weakref.ref:
#     if isinstance(referent, weakref.ref):
#         return referent

    try:
        return weakref.ref(referent)
    # if referent is None, will raise a TypeError
    # if referent is a weakref, will also raise a TypeError
    # will also raise a type error for string, ints, etc.
    # slight performance bost rather than checking if None
    except TypeError:
        return referent
        #return None

def unwrapWeakref(referent):
    '''
    Utility function that gets an object that might be an object itself
    or a weak reference to an object.  It returns obj() if it's a weakref 
    and obj if it's not.
    
    >>> from music21 import *
    >>> class Mock(object): 
    ...     pass
    >>> a1 = Mock()
    >>> a2 = Mock()
    >>> a2.strong = a1
    >>> a2.weak = common.wrapWeakref(a1)
    >>> common.unwrapWeakref(a2.strong) is a1
    True
    >>> common.unwrapWeakref(a2.weak) is a1
    True
    >>> common.unwrapWeakref(a2.strong) is common.unwrapWeakref(a2.weak)
    True
    '''
    import weakref
    if type(referent) is weakref.ref:
        return referent()
    else:
        return referent
    

def isWeakref(referent):
    '''Test if an object is a weakref

    >>> from music21 import *
    >>> class Mock(object): 
    ...     pass
    >>> a1 = Mock()
    >>> a2 = Mock()
    >>> common.isWeakref(a1)
    False
    >>> common.isWeakref(3)
    False
    >>> common.isWeakref(common.wrapWeakref(a1))
    True
    '''
    import weakref
    if type(referent) is weakref.ref:
        return True
    return False


def findWeakRef(target):
    '''Given an object or composition of objects, find an attribute that is a weakref. This is a diagnostic tool.
    '''
    for attrName in dir(target):
        try:
            attr = getattr(target, attrName)
        except:
            print 'exception on attribute access: %s' % attrName
        if isWeakref(attr):
            print 'found weakref', attr, attrName, 'of target:', target
        if isinstance(attr, (list, tuple)):
            for x in attr:
                findWeakRef(x)
#         elif isinstance(attr, dict):
#             for x in attr.keys():
#                 findWeakRef(attr[x])

xlateAccents={0xc0:'A', 0xc1:'A', 0xc2:'A', 0xc3:'A', 0xc4:'A', 0xc5:'A',
    0xc6:'Ae', 0xc7:'C',
    0xc8:'E', 0xc9:'E', 0xca:'E', 0xcb:'E',
    0xcc:'I', 0xcd:'I', 0xce:'I', 0xcf:'I',
    0xd0:'Th', 0xd1:'N',
    0xd2:'O', 0xd3:'O', 0xd4:'O', 0xd5:'O', 0xd6:'O', 0xd8:'O',
    0xd9:'U', 0xda:'U', 0xdb:'U', 0xdc:'U',
    0xdd:'Y', 0xde:'th', 0xdf:'ss',
    0xe0:'a', 0xe1:'a', 0xe2:'a', 0xe3:'a', 0xe4:'a', 0xe5:'a',
    0xe6:'ae', 0xe7:'c',
    0xe8:'e', 0xe9:'e', 0xea:'e', 0xeb:'e',
    0xec:'i', 0xed:'i', 0xee:'i', 0xef:'i',
    0xf0:'th', 0xf1:'n',
    0xf2:'o', 0xf3:'o', 0xf4:'o', 0xf5:'o', 0xf6:'o', 0xf8:'o',
    0xf9:'u', 0xfa:'u', 0xfb:'u', 0xfc:'u',
    0xfd:'y', 0xfe:'th', 0xff:'y',
    0xa1:'!', 0xa2:'{cent}', 0xa3:'{pound}', 0xa4:'{currency}',
    0xa5:'{yen}', 0xa6:'|', 0xa7:'{section}', 0xa8:'{umlaut}',
    0xa9:'{C}', 0xaa:'{^a}', 0xab:'<<', 0xac:'{not}',
    0xad:'-', 0xae:'{R}', 0xaf:'_', 0xb0:'{degrees}',
    0xb1:'{+/-}', 0xb2:'{^2}', 0xb3:'{^3}', 0xb4:"'",
    0xb5:'{micro}', 0xb6:'{paragraph}', 0xb7:'*', 0xb8:'{cedilla}',
    0xb9:'{^1}', 0xba:'{^o}', 0xbb:'>>',
    0xbc:'{1/4}', 0xbd:'{1/2}', 0xbe:'{3/4}', 0xbf:'?',
    0xd7:'*', 0xf7:'/'
    }

def stripAccents(inputString):
    '''
    removes accents from unicode strings.
    
    >>> from music21 import *
    >>> s = u'tr\u00e8s vite'
    >>> u'\u00e8' in s
    True
    >>> common.stripAccents(s)
    u'tres vite'
    '''
    #if isinstance(inputString, unicode):        
    r = ''
    for i in inputString:
        if ord(i) in xlateAccents:
            r += xlateAccents[ord(i)]
        elif ord(i) >= 0x80:
            pass
        else:
            r += i
    return r
    #else:
    #    return inputString



#-------------------------------------------------------------------------------
_singletonCounter = {}
_singletonCounter['value'] = 0

class SingletonCounter(object):
    '''A simple counter that can produce unique numbers regardless of how many instances exist. 
    '''
    def __init__(self):
        pass

    def __call__(self):
        post = _singletonCounter['value']
        _singletonCounter['value'] += 1
        return post



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


class Music21CommonException(Exception):
    pass

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

    def __copy__(self, memo=None):
        self.environLocal.printDebug(['copy called'])
        return copy.copy(self, memo)

    property1 = property(_get1, _set1)

    property2 = property(_get1, _set1)




class Test(unittest.TestCase):
    '''Tests not requiring file output. 
    '''

    def runTest(self):
        pass

    def setUp(self):
        pass

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
        '''A simple test of deepcopying.
        '''
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
        

    def testWeightedSelection(self):

        from music21 import environment
        _MOD = "common.py"
        environLocal = environment.Environment(_MOD)
        

        # test equal selection
        for j in range(10):
            x = 0
            for i in range(1000):
                # equal chance of -1, 1
                x += weightedSelection([-1, 1], [1,1])
            #environLocal.printDebug(['weightedSelection([-1, 1], [1,1])', x])
            self.assertEqual(-100 < x < 100, True)


        # test a strongly weighed boudnary
        for j in range(10):
            x = 0
            for i in range(1000):
                # equal chance of -1, 1
                x += weightedSelection([0, 1], [10000,1])
            #environLocal.printDebug(['weightedSelection([0, 1], [10000,1])', x])
            self.assertEqual(0 <= x < 5, True)

        for j in range(10):
            x = 0
            for i in range(1000):
                # equal chance of -1, 1
                x += weightedSelection([0, 1], [1, 10000])
            #environLocal.printDebug(['weightedSelection([0, 1], [1, 10000])', x])
            self.assertEqual(980 <= x < 1020, True)


        for j in range(10):
            x = 0
            for i in range(1000):
                x += weightedSelection([0, 1], [1, 0])
            #environLocal.printDebug(['weightedSelection([0, 1], [1, 0])', x])
            self.assertEqual(x == 0, True)



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [fromRoman, toRoman, Scalar]


if __name__ == "__main__":
    if len(sys.argv) == 1: # normal conditions

        ## do this the old way to avoid music21 import
        s1 = doctest.DocTestSuite(__name__, optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE))
        s2 = unittest.defaultTestLoader.loadTestsFromTestCase(Test)
        s1.addTests(s2)
        runner = unittest.TextTestRunner()
        runner.run(s1)  

    elif len(sys.argv) > 1:
        t = Test()

        t.testWeightedSelection()


#------------------------------------------------------------------------------
# eof

