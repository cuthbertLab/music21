#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common.py
# Purpose:      Basic Utilties
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Utility constants, dictionaries, functions, and objects used throughout music21.
'''

# should NOT import music21 or anything like that, except in doctests.
import re
import copy
import math, sys, os
import doctest
import unittest
import time
import hashlib
import random
import inspect
import weakref

from fractions import Fraction # speedup 50% below...

from music21 import defaults
from music21 import exceptions21
from music21.ext import six

#python3
try:
    basestring # @UndefinedVariable 
except NameError:
    basestring = str # @ReservedAssignment


# define file extensions for various formats
# keys are assumed to be formats
# fileExtensions = {
#     'abc' : {'input': ['abc'], 'output': 'abc'},
#     'text' : {'input': ['txt', 'text', 't'], 'output': 'txt'},
#     'textline' : {'input': ['tl', 'textline'], 'output': 'txt'},
#     'musicxml' : {'input': ['xml', 'mxl', 'mx'], 'output': 'xml'},
#     'musicxml.png' : {'input': ['png'], 'output': 'png'},
#     'midi' : {'input': ['mid', 'midi'], 'output': 'mid'},
#     'tinynotation' : {'input': ['tntxt', 'tinynotation'], 'output': 'tntxt'},
#      # note: this is setting .zip as default mapping to musedata
#     'musedata' : {'input': ['md', 'musedata', 'zip'], 'output': 'md'},
#     'noteworthy': {'input': ['nwc'], 'output': 'nwc'},
#     'noteworthytext': {'input': ['nwctxt'], 'output': 'nwctxt'},
#     'lilypond' : {'input': ['ly', 'lily'], 'output': 'ly'},
#     'finale' : {'input': ['mus'], 'output': 'mus'},
#     'humdrum' : {'input': ['krn'], 'output': 'krn'},
#     'jpeg' : {'input': ['jpg', 'jpeg'], 'output': 'jpg'},
#     'png'  : {'input': ['png', 'lily.png', 'lilypond.png'], 'output': 'png'},
#     'pdf'  : {'input': ['pdf', 'lily.pdf', 'lilypond.pdf'], 'output': 'pdf'},
#     'svg'  : {'input': ['svg', 'lily.svg', 'lilypond.svg'], 'output': 'svg'},
#     'pickle' : {'input': ['p', 'pickle'], 'output': 'p'},
#     'romantext' : {'input': ['rntxt', 'rntext', 'romantext', 'rtxt'], 'output': 'rntxt'},
#     'scala' : {'input': ['scl'], 'output': 'scl'},
#     'braille' : {'input' : ['brailleTextDoesNotWork'], 'output' : 'txt'},
#     'vexflow' : {'input' : ['vexflowDoesNotWork'], 'output': 'html'},
#     'capella' : {'input': ['capx'], 'output': 'capx'},
#     'ipython' : {'input': ['ipython.png'], 'output': 'png'},
# }



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

WHITESPACE = re.compile(r'\s+')
LINEFEED = re.compile('\n+')

DEBUG_OFF = 0
DEBUG_USER = 1
DEBUG_DEVEL = 63
DEBUG_ALL = 255

# used for checking preferences, and for setting environment variables
VALID_SHOW_FORMATS = ['musicxml', 'lilypond', 'text', 'textline', 'midi', 'png', 'pdf', 'svg', 'lily.pdf', 'lily.png', 'lily.svg', 'braille', 'vexflow', 'vexflow.html', 'vexflow.js', 'ipython', 'ipython.png', 'musicxml.png']
VALID_WRITE_FORMATS = ['musicxml', 'lilypond', 'text', 'textline', 'midi', 'png', 'pdf', 'svg', 'lily.pdf', 'lily.png', 'lily.svg', 'braille', 'vexflow', 'vexflow.html', 'vexflow.js', 'ipython', 'ipython.png', 'musicxml.png']
VALID_AUTO_DOWNLOAD = ['ask', 'deny', 'allow']


#-------------------------------------------------------------------------------
# provide warning strings to users for use in conditional imports

def getMissingImportStr(modNameList):
    '''
    Given a list of missing module names, returns a nicely-formatted message to the user
    that gives instructions on how to expand music21 with optional packages.


    >>> common.getMissingImportStr(['matplotlib'])
    'Certain music21 functions might need the optional package matplotlib; if you run into errors, install it by following the instructions at http://mit.edu/music21/doc/installing/installAdditional.html'
    >>> common.getMissingImportStr(['matplotlib', 'numpy'])
    'Certain music21 functions might need these optional packages: matplotlib, numpy; if you run into errors, install it by following the instructions at http://mit.edu/music21/doc/installing/installAdditional.html'

    '''
    if len(modNameList) == 0:
        return None
    elif len(modNameList) == 1:
        return 'Certain music21 functions might need the optional package %s; if you run into errors, install it by following the instructions at http://mit.edu/music21/doc/installing/installAdditional.html' % modNameList[0]
    else:
        return 'Certain music21 functions might need these optional packages: %s; if you run into errors, install it by following the instructions at http://mit.edu/music21/doc/installing/installAdditional.html' % ', '.join(modNameList)

#-------------------------------------------------------------------------------
def subConverterList():
    '''
    returns a list of subconverter classes available to music21
    in converter/subConverters, including the stub SubConverter class
    
    DEPRECATED May 2015: moved to converter. #TODO: Remove
    '''
    from music21 import converter
    return converter.Converter().subconvertersList()

def findSubConverterForFormat(fmt):
    '''
    return a converter.subConverter.SubConverter subclass
    for a given format -- this is a music21 format name,
    not a file extension. Or returns None
    
    >>> common.findSubConverterForFormat('musicxml')
    <class 'music21.converter.subConverters.ConverterMusicXML'>
    
    >>> common.findSubConverterForFormat('text')
    <class 'music21.converter.subConverters.ConverterText'>

    Some subconverters have format aliases

    >>> common.findSubConverterForFormat('t')
    <class 'music21.converter.subConverters.ConverterText'>
    
    '''
    fmt = fmt.lower().strip()
    scl = subConverterList()
    for sc in scl:
        formats = sc.registerFormats
        if fmt in formats:
            return sc

def findFormat(fmt):
    '''
    Given a format defined either by a format name, abbreviation, or
    an extension, return the regularized format name as well as 
    the output exensions.
    
    DEPRECATED May 2014 -- moving to converter

    
    All but the first element of the tuple are deprecated for use, since
    the extension can vary by subconverter (e.g., lily.png)

    Note that .mxl and .mx are only considered MusicXML input formats.

    >>> common.findFormat('mx')
    ('musicxml', '.xml')
    >>> common.findFormat('.mxl')
    ('musicxml', '.xml')
    >>> common.findFormat('musicxml')
    ('musicxml', '.xml')
    >>> common.findFormat('lily')
    ('lilypond', '.ly')
    >>> common.findFormat('lily.png')
    ('lilypond', '.ly')
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
    >>> common.findFormat('capx')
    ('capella', '.capx')

    >>> common.findFormat('mx')
    ('musicxml', '.xml')

    
    #>>> common.findFormat('png')
    #('musicxml.png', '.png')
    
    #>>> common.findFormat('ipython')
    #('ipython', '.png')
    #     >>> common.findFormat('ipython.png')
    #     ('ipython', '.png')
    #     >>> common.findFormat('musicxml.png')
    #     ('musicxml.png', '.png')


    Works the same whether you have a leading dot or not:


    >>> common.findFormat('md')
    ('musedata', '.md')
    >>> common.findFormat('.md')
    ('musedata', '.md')


    If you give something we can't deal with, returns a Tuple of None, None:

    >>> common.findFormat('wpd')
    (None, None)

    '''
    from music21 import converter
    c = converter.Converter()
    fileformat = c.regularizeFormat(fmt)
    if fileformat is None:
        return (None, None)
    scf = c.getSubConverterFormats()
    sc = scf[fileformat]

        
    if len(sc.registerOutputExtensions) > 0:
        firstOutput = '.' + sc.registerOutputExtensions[0]
    elif len(sc.registerInputExtensions) > 0:
        firstOutput = '.' + sc.registerInputExtensions[0]
    else:
        firstOutput = None
            
    return fileformat, firstOutput
    
#     for key in sorted(list(fileExtensions)):
#         if fmt.startswith('.'):
#             fmt = fmt[1:] # strip .
#         if fmt == key or fmt in fileExtensions[key]['input']:
#             # add leading dot to extension on output
#             return key, '.' + fileExtensions[key]['output']
#     return None, None # if no match found


def findInputExtension(fmt):
    '''
    DEPRECATED May 2014 -- moving to converter
    
    Given an input format or music21 format, find and return all possible 
    input extensions.

    >>> a = common.findInputExtension('musicxml')
    >>> a
    ('.xml', '.mxl', '.mx', '.musicxml')
    >>> a = common.findInputExtension('humdrum')
    >>> a
    ('.krn',)
    >>> common.findInputExtension('musedata')
    ('.md', '.musedata', '.zip')
    
    mx is not a music21 format but it is a file format
    
    >>> common.findInputExtension('mx')
    ('.xml', '.mxl', '.mx', '.musicxml')
    
    Leading dots don't matter...
    
    >>> common.findInputExtension('.mx')
    ('.xml', '.mxl', '.mx', '.musicxml')


    blah is neither
    
    >>> common.findInputExtension('blah') is None
    True
    
    
    '''
    fmt = fmt.lower().strip()    
    if fmt.startswith('.'):
        fmt = fmt[1:] # strip .

    sc = findSubConverterForFormat(fmt)
    if sc is None:
        # file extension
        post = []
        for sc in subConverterList():
            if fmt not in sc.registerInputExtensions:
                continue
            for ext in sc.registerInputExtensions:
                if not ext.startswith('.'):
                    ext = '.' + ext
                post.append(ext)
            if len(post) > 0:
                return tuple(post)
        return None
    else:
        # music21 format
        post = []
        for ext in sc.registerInputExtensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            post.append(ext)
        return tuple(post)

def findFormatFile(fp):
    '''
    Given a file path (relative or absolute) return the format
    
    DEPRECATED May 2014 -- moving to converter


    >>> common.findFormatFile('test.xml')
    'musicxml'
    >>> common.findFormatFile('long/file/path/test-2009.03.02.xml')
    'musicxml'
    >>> common.findFormatFile('long/file/path.intermediate.png/test-2009.03.xml')
    'musicxml'

    On a windows networked filesystem
    >>> common.findFormatFile('\\\\long\\file\\path\\test.krn')
    'humdrum'
    '''
    fmt, unused_ext = findFormat(fp.split('.')[-1])
    return fmt # may be None if no match


def findFormatExtFile(fp):
    '''Given a file path (relative or absolute) find format and extension used (not the output extension)

    DEPRECATED May 2014 -- moving to converter

    >>> common.findFormatExtFile('test.mx')
    ('musicxml', '.mx')
    >>> common.findFormatExtFile('long/file/path/test-2009.03.02.xml')
    ('musicxml', '.xml')
    >>> common.findFormatExtFile('long/file/path.intermediate.png/test-2009.03.xml')
    ('musicxml', '.xml')

    >>> common.findFormatExtFile('test')
    (None, None)

    Windows drive
    >>> common.findFormatExtFile('d:/long/file/path/test.xml')
    ('musicxml', '.xml')

    On a windows networked filesystem
    >>> common.findFormatExtFile('\\\\long\\file\\path\\test.krn')
    ('humdrum', '.krn')
    '''
    fileFormat, unused_extOut = findFormat(fp.split('.')[-1])
    if fileFormat == None:
        return None, None
    else:
        return fileFormat, '.'+fp.split('.')[-1] # may be None if no match


def findFormatExtURL(url):
    '''Given a URL, attempt to find the extension. This may scrub arguments in a URL, or simply look at the last characters.

    DEPRECATED May 2014 -- moving to converter


    >>> urlA = 'http://somesite.com/?l=cc/schubert/piano/d0576&file=d0576-06.krn&f=xml'
    >>> urlB = 'http://somesite.com/cgi-bin/ksdata?l=cc/schubert/piano/d0576&file=d0576-06.krn&f=kern'
    >>> urlC = 'http://somesite.com/cgi-bin/ksdata?l=cc/bach/cello&file=bwv1007-01.krn&f=xml'
    >>> urlF = 'http://junk'

    >>> common.findFormatExtURL(urlA)
    ('musicxml', '.xml')
    >>> common.findFormatExtURL(urlB)
    ('humdrum', '.krn')
    >>> common.findFormatExtURL(urlC)
    ('musicxml', '.xml')
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
        for sc in subConverterList():
            inputTypes = sc.registerInputExtensions            
            for extSample in inputTypes:
                if url.endswith('.' + extSample):
                    ext = '.' + extSample
                    break
    # presently, not keeping the extension returned from this function
    # reason: mxl is converted to xml; need to handle mxl files first
    if ext != None:
        fileFormat, unused_junk = findFormat(ext)
        return fileFormat, ext
    else:
        return None, None

def basicallyEqual(a, b):
    '''
    returns true if a and b are equal except for whitespace differences


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

def cleanupFloat(floatNum, maxDenominator=defaults.limitOffsetDenominator):
    '''
    Cleans up a floating point number by converting
    it to a fractions.Fraction object limited to
    a denominator of maxDenominator


    >>> common.cleanupFloat(0.33333327824)
    0.333333333333...

    >>> common.cleanupFloat(0.142857)
    0.1428571428571...

    >>> common.cleanupFloat(1.5)
    1.5

    Fractions are passed through silently...
    
    >>> import fractions
    >>> common.cleanupFloat(fractions.Fraction(4, 3))
    Fraction(4, 3)

    '''
    if isinstance(floatNum, Fraction):
        return floatNum # do nothing to fractions
    else:
        f = Fraction(floatNum).limit_denominator(maxDenominator)
        return float(f)

#------------------------------------------------------------------------------
# Number methods...

DENOM_LIMIT = defaults.limitOffsetDenominator

def _preFracLimitDenominator(n, d):
    '''
    copied from fractions.limit_denominator.  Their method
    requires creating three new Fraction instances to get one back. this doesn't create any
    call before Fraction...
    
    DENOM_LIMIT is hardcoded to defaults.limitOffsetDenominator for speed...
    
    returns a new n, d...
    
    >>> common._preFracLimitDenominator(100001, 300001)
    (1, 3)
    >>> from fractions import Fraction
    >>> Fraction(100000000001, 300000000001).limit_denominator(65535)
    Fraction(1, 3)
    >>> Fraction(100001, 300001).limit_denominator(65535)
    Fraction(1, 3)
    
    Timing differences are huge!

    t is timeit.timeit
    
    t('Fraction(*common._preFracLimitDenominator(*x.as_integer_ratio()))', 
       setup='x = 1000001/3000001.; from music21 import common;from fractions import Fraction', 
       number=100000)
    1.0814228057861328
    
    t('Fraction(x).limit_denominator(65535)', 
       setup='x = 1000001/3000001.; from fractions import Fraction', 
       number=100000)
    7.941488981246948
    
    Proof of working...
    
    >>> import random
    >>> myWay = lambda x: Fraction(*common._preFracLimitDenominator(*x.as_integer_ratio()))
    >>> theirWay = lambda x: Fraction(x).limit_denominator(65535)

    >>> for i in range(50):
    ...     x = random.random()
    ...     if myWay(x) != theirWay(x):
    ...         print("boo: %s, %s, %s" % (x, myWay(x), theirWay(x)))
    
    (n.b. -- nothing printed)
    
    '''
    nOrg = n
    dOrg = d
    if (d <= DENOM_LIMIT):
        return (n, d)
    p0, q0, p1, q1 = 0, 1, 1, 0
    while True:
        a = n//d
        q2 = q0+a*q1
        if q2 > DENOM_LIMIT:
            break
        p0, q0, p1, q1 = p1, q1, p0+a*p1, q2
        n, d = d, n-a*d

    k = (DENOM_LIMIT-q0)//q1
    bound1n = p0+k*p1
    bound1d = q0+k*q1
    bound2n = p1
    bound2d = q1
    #s = (0.0 + n)/d
    bound1minusS = (abs((bound1n * dOrg) - (nOrg * bound1d)), (dOrg * bound1d))
    bound2minusS = (abs((bound2n * dOrg) - (nOrg * bound2d)), (dOrg * bound2d))
    difference = (bound1minusS[0] * bound2minusS[1]) - (bound2minusS[0] * bound1minusS[1])
    if difference > 0:
        # bound1 is farther from zero than bound2; return bound2
        return (p1, q1)
    else:
        return (p0 + k*p1, q0 + k * q1)
    
    

def opFrac(num):
    '''
    opFrac -> optionally convert a number to a fraction or back.
    
    Important music21 2.x function for working with offsets and quarterLengths
    
    Takes in a number (or None) and converts it to a Fraction with denominator
    less than limitDenominator if it is not binary expressible; otherwise return a float.  
    Or if the Fraction can be converted back to a binary expressable
    float then do so.
    
    This function should be called often to ensure that values being passed around are floats
    and ints wherever possible and fractions where needed.
    
    The naming of this method violates music21's general rule of no abbreviations, but it
    is important to make it short enough so that no one will be afraid of calling it often.
    It also doesn't have a setting for maxDenominator so that it will expand in
    Code Completion easily. That is to say, this function has been set up to be used, so please
    use it.
    
    
    >>> from fractions import Fraction
    >>> defaults.limitOffsetDenominator
    65535
    >>> common.opFrac(3)
    3.0
    >>> common.opFrac(1.0/3)
    Fraction(1, 3)
    >>> common.opFrac(1.0/4)
    0.25
    >>> f = Fraction(1,3)
    >>> common.opFrac(f + f + f)
    1.0
    >>> common.opFrac(0.123456789)
    Fraction(10, 81)
    >>> common.opFrac(None) is None
    True
    '''
    # This is a performance critical operation, tuned to go as fast as possible.
    # hence redundancy -- first we check for type (no inheritance) and then we
    # repeat exact same test with inheritence. Note that the later examples are more verbose
    t = type(num)
    if t is float:
        # quick test of power of whether denominator is a power
        # of two, and thus representable exactly as a float: can it be
        # represented w/ a denominator less than DENOM_LIMIT?
        # this doesn't work:
        #    (denominator & (denominator-1)) != 0
        # which is a nice test, but denominator here is always a power of two...
        #unused_numerator, denominator = num.as_integer_ratio() # too slow
        ir = num.as_integer_ratio()
        if ir[1] > DENOM_LIMIT: # slightly faster than hardcoding 65535!
            return Fraction(*_preFracLimitDenominator(*ir)) # way faster!
            #return Fraction(*ir).limit_denominator(DENOM_LIMIT) # *ir instead of float -- this happens
                # internally in Fraction constructor, but is twice as fast...
        else:
            return num
    elif t is int:
        return num + 0.0 # 8x faster than float(num)
    elif t is Fraction:
        d = num._denominator # private access instead of property: 6x faster; may break later...
        if (d & (d-1)) == 0: # power of two...
            return num._numerator/(d + 0.0) # 50% faster than float(num)
        else:
            return num # leave fraction alone
    elif num is None:
        return None
    
    # class inheritance only check AFTER ifs...
    elif isinstance(num, int):
        return num + 0.0
    elif isinstance(num, float):
        ir = num.as_integer_ratio()
        if ir[1] > DENOM_LIMIT: # slightly faster than hardcoding 65535!
            return Fraction(*_preFracLimitDenominator(*ir)) # way faster!
        else:
            return num
        
    elif isinstance(num, Fraction):
        d = num._denominator # private access instead of property: 6x faster; may break later...
        if (d & (d-1)) == 0: # power of two...
            return num._numerator/(d + 0.0) # 50% faster than float(num)
        else:
            return num # leave fraction alone
    else:
        raise TypeError("Cannot convert num: %r" % num)
        


def mixedNumeral(expr, limitDenominator=defaults.limitOffsetDenominator):
    '''
    Returns a string representing a mixedNumeral form of a number
    
    >>> common.mixedNumeral(1.333333)
    '1 1/3'
    >>> common.mixedNumeral(0.333333)
    '1/3'
    >>> common.mixedNumeral(-1.333333)
    '-1 1/3'
    >>> common.mixedNumeral(-0.333333)
    '-1/3'

    >>> common.mixedNumeral(0)
    '0'
    >>> common.mixedNumeral(-0)
    '0'

    
    Works with Fraction objects too
    
    >>> from fractions import Fraction
    >>> common.mixedNumeral( Fraction(31,7) )
    '4 3/7'
    >>> common.mixedNumeral( Fraction(1,5) )
    '1/5'
    >>> common.mixedNumeral( Fraction(-1,5) )
    '-1/5'
    >>> common.mixedNumeral( Fraction(-31,7) )
    '-4 3/7'
    
    Denominator is limited by default but can be changed.
    
    >>> common.mixedNumeral(2.0000001)
    '2'
    >>> common.mixedNumeral(2.0000001, limitDenominator=10000000)
    '2 1/10000000'
    '''
    if not isinstance(expr, Fraction):        
        quotient, remainder = divmod(float(expr), 1.)
        remainderFrac = Fraction(remainder).limit_denominator(limitDenominator)
        if quotient < -1:
            quotient += 1
            remainderFrac = 1 - remainderFrac
        elif quotient == -1:
            quotient = 0.0
            remainderFrac = remainderFrac - 1
    else:
        quotient = int(expr)
        remainderFrac = expr - quotient
        if (quotient < 0):
            remainderFrac *= -1
    
    if quotient:
        if remainderFrac:
            return '{} {}'.format(int(quotient), remainderFrac)
        else:
            return str(int(quotient))
    else:
        if remainderFrac != 0:
            return str(remainderFrac)
    return str(0)

def roundToHalfInteger(num):
    '''
    Given a floating-point number, round to the nearest half-integer.

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
    # for very small grains, just compare Fractions without converting...
    if (isinstance(x, Fraction) and isinstance(y, Fraction) and grain <= 5e-6):
        if x == y:
            return True
    
    if abs(x - y) < grain:
        return True
    return False


def nearestCommonFraction(x, grain=1e-2):
    '''Given a value that suggests a floating point fraction, like .33,
    return a float that provides greater specification, such as .333333333


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
              1/6., 5/6.]
    for v in values:
        if almostEquals(x, v, grain=grain):
            return v
    return x


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


def nearestMultiple(n, unit):
    '''
    Given a positive value `n`, return the nearest multiple of the supplied `unit` as well as 
    the absolute difference (error) to seven significant digits and the signed difference.

    >>> print(common.nearestMultiple(.25, .25))
    (0.25, 0.0, 0.0)
    >>> print(common.nearestMultiple(.35, .25))
    (0.25, 0.1..., 0.1...)
    >>> print(common.nearestMultiple(.20, .25))
    (0.25, 0.05..., -0.05...)

    Note that this one also has an error of .1 but it's a positive error off of 0.5
    >>> print(common.nearestMultiple(.4, .25))
    (0.5, 0.1..., -0.1...)

    >>> common.nearestMultiple(.4, .25)[0]
    0.5
    >>> common.nearestMultiple(23404.001, .125)[0]
    23404.0
    >>> common.nearestMultiple(23404.134, .125)[0]
    23404.125
    
    Error is always positive, but signed difference can be negative.
    
    >>> common.nearestMultiple(23404 - 0.0625, .125)
    (23404.0, 0.0625, -0.0625)

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


    >>> common.nearestMultiple(-0.5, 0.125)
    Traceback (most recent call last):
    ValueError: n (-0.5) is less than zero. Thus cannot find nearest multiple for a value less than the unit, 0.125

    '''
    if n < 0:
        raise ValueError('n (%s) is less than zero. Thus cannot find nearest multiple for a value less than the unit, %s' % (n, unit))

    mult = math.floor(n / float(unit)) # can start with the floor
    halfUnit = unit / 2.0

    matchLow = unit * mult
    matchHigh = unit * (mult + 1)

    #print(['mult, halfUnit, matchLow, matchHigh', mult, halfUnit, matchLow, matchHigh])

    if matchLow >= n >= matchHigh:
        raise Exception('cannot place n between multiples: %s, %s', matchLow, matchHigh)

    if n >= matchLow and n < (matchLow + halfUnit):
        return matchLow, round(n - matchLow, 7), round(n - matchLow, 7)
    elif n >= (matchHigh - halfUnit) and n <= matchHigh:
        return matchHigh, round(matchHigh - n, 7), round(n - matchHigh, 7)


def standardDeviation(coll, bassel=False):
    '''Given a collection of values, return the standard deviation.


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
    TODO: consider using numbers class (wasn't available until 2.6)

    >>> common.isNum(3.0)
    True
    >>> common.isNum(3)
    True
    >>> common.isNum('three')
    False
    
    True and False are NOT numbers:
    
    >>> common.isNum(True)
    False
    >>> common.isNum(False)
    False
    >>> common.isNum(None)
    False
    '''
    try:
        # TODO: this may have unexpected consequences: find
        dummy = usrData + 0
        if usrData is not True and usrData is not False:
            return True
        else:
            return False
    except Exception: # pylint: disable=broad-except
        return False

#     if (isinstance(usrData, int) or
#         isinstance(usrData, float) or
#         isinstance(usrData, long) or
#         isinstance(usrData, decimal.Decimal)):
#         return True
#     else:
#         return False

def contiguousList(inputListOrTuple):
    '''
    returns bool True or False if a list containing ints contains only contiguous (increasing) values

    requires the list to be sorted first


    >>> l = [3, 4, 5, 6]
    >>> common.contiguousList(l)
    True
    >>> l.append(8)
    >>> common.contiguousList(l)
    False

    Sorting matters

    >>> l.append(7)
    >>> common.contiguousList(l)
    False
    >>> common.contiguousList(sorted(l))
    True
    '''
    currentMaxVal = inputListOrTuple[0]
    for i in range(1, len(inputListOrTuple)):
        newVal = inputListOrTuple[i]
        if newVal != currentMaxVal + 1:
            return False
        currentMaxVal += 1
    return True

def isStr(usrData):
    """Check of usrData is some form of string, including unicode.

    >>> common.isStr(3)
    False
    >>> common.isStr('sharp')
    True
    >>> common.isStr(u'flat')
    True
    """
    #python3 compatibility
    try:
        if isinstance(usrData, basestring):
    #     if (isinstance(usrData, str) or
    #         isinstance(usrData, unicode)):
            return True
        else:
            return False
    except NameError:
        if isinstance(usrData, str):
            return True
        else:
            return False


def isListLike(usrData):
    """
    Returns True if is a List or a Set or a Tuple


    >>> common.isListLike([])
    True
    >>> common.isListLike('sharp')
    False
    >>> common.isListLike((None, None))
    True
    >>> common.isListLike( set(['a','b','c','c']) )
    True
    >>> common.isListLike(stream.Stream())
    False
    """
    #TODO: add immutable sets
    if (isinstance(usrData, list) or
        isinstance(usrData, tuple) or
        isinstance(usrData, set)):
        return True
    else:
        return False

def isIterable(usrData):
    """
    Returns True if is the object can be iter'd over and is NOT a string


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
        if six.PY3:
            if isinstance(usrData, str) or isinstance(usrData, bytes):
                return False
        return True
    else:
        return False


def toUnicode(usrStr):
    '''Convert this tring to a uncode string; if already a unicode string, do nothing.

    >>> common.toUnicode('test')
    u'test'
    >>> common.toUnicode(u'test')
    u'test'
    '''
    if six.PY3:
        if not isinstance(usrStr, str):
            try:
                return usrStr.decode('utf-8')
            except TypeError:
                return usrStr
        else:
            return usrStr
    else:
        try:
            usrStr = unicode(usrStr, 'utf-8') # @UndefinedVariable  pylint: disable=undefined-variable
        # some documentation may already be in unicode; if so, a TypeException will be raised
        except TypeError: #TypeError: decoding Unicode is not supported
            pass
        return usrStr

def readFileEncodingSafe(filePath, firstGuess='utf-8'):
    r'''
    Slow, but will read a file of unknown encoding as safely as possible using
    the LGPL chardet package in music21.ext.  
    
    Let's try to load this file as ascii -- it has a copyright symbol at the top
    so it won't load in Python3:
    
    >>> import os 
    >>> c = common.getSourceFilePath() + os.sep + 'common.py'
    >>> f = open(c)
    >>> #_DOCS_SHOW data = f.read()
    Traceback (most recent call last):
    UnicodeDecodeError: 'ascii' codec can't decode byte 0xc2 in position ...: ordinal not in range(128)

    That won't do! now I know that it is in utf-8, but maybe you don't. Or it could
    be an old humdrum or Noteworthy file with unknown encoding.  This will load it safely.
    
    >>> data = common.readFileEncodingSafe(c)
    >>> data[0:30]
    u'#-*- coding: utf-8 -*-\n#------'
    
    Well, that's nothing, since the first guess here is utf-8 and it's right. So let's
    give a worse first guess:
    
    >>> data = common.readFileEncodingSafe(c, firstGuess='SHIFT_JIS') # old Japanese standard
    >>> data[0:30]
    u'#-*- coding: utf-8 -*-\n#------'
    
    It worked!
    
    Note that this is slow enough if it gets it wrong that the firstGuess should be set
    to something reasonable like 'ascii' or 'utf-8'.
    '''
    import codecs
    from music21.ext import chardet # encoding detector... @UnresolvedImport
    try:
        with codecs.open(filePath, 'r', encoding=firstGuess) as thisFile:
            data = thisFile.read()
            return data
    except OSError: # Python3 FileNotFoundError...
        raise
    except UnicodeDecodeError:
        with codecs.open(filePath, 'rb') as thisFileBinary:
            dataBinary = thisFileBinary.read()
            encoding = chardet.detect(dataBinary)['encoding']
            return codecs.decode(dataBinary, encoding)
    


def classToClassStr(classObj):
    '''Convert a class object to a class string.

    >>> common.classToClassStr(note.Note)
    'Note'
    >>> common.classToClassStr(chord.Chord)
    'Chord'
    '''
    # remove closing quotes
    return str(classObj).split('.')[-1][:-2]

def getNumFromStr(usrStr, numbers='0123456789'):
    '''Given a string, extract any numbers. Return two strings, the numbers (as strings) and the remaining characters.

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

    >>> common.dotMultiplier(1)
    Fraction(3, 2)
    >>> common.dotMultiplier(2)
    Fraction(7, 4)
    >>> common.dotMultiplier(3)
    Fraction(15, 8)
    '''
    x = (((2**(dots+1.0))-1.0)/(2**dots))
    return Fraction(x)



def decimalToTuplet(decNum):
    '''
    For simple decimals (usually > 1), a quick way to figure out the
    fraction in lowest terms that gives a valid tuplet.

    No it does not work really fast.  No it does not return tuplets with
    denominators over 100.  Too bad, math geeks.  This is real life.  :-)

    returns (numerator, denominator)


    >>> common.decimalToTuplet(1.5)
    (3, 2)
    >>> common.decimalToTuplet(1.25)
    (5, 4)

    If decNum is < 1, the denominator will be greater than the numerator:

    >>> common.decimalToTuplet(.8)
    (4, 5)

    If decNum is <= 0, returns a ZeroDivisionError:

    >>> common.decimalToTuplet(-.02)
    Traceback (most recent call last):
    ZeroDivisionError: number must be greater than zero

    TODO: replace with fractions...
    '''

    def findSimpleFraction(working):
        'Utility function.'
        for i in range(1,1000):
            for j in range(i,2*i):
                if almostEquals(working, (j+0.0)/i):
                    return (int(j), int(i))
        return (0,0)

    flipNumerator = False
    if decNum <= 0:
        raise ZeroDivisionError("number must be greater than zero")
    if decNum < 1:
        flipNumerator = True
        decNum = 1.0/decNum

    unused_remainder, multiplier = math.modf(decNum)
    working = decNum/multiplier

    (jy, iy) = findSimpleFraction(working)

    if iy == 0:
        raise Exception("No such luck")

    jy *= multiplier
    gcd = euclidGCD(int(jy), int(iy))
    jy = jy/gcd
    iy = iy/gcd

    if flipNumerator is False:
        return (int(jy), int(iy))
    else:
        return (int(iy), int(jy))




def unitNormalizeProportion(values):
    """Normalize values within the unit interval, where max is determined by the sum of the series.


    >>> common.unitNormalizeProportion([0,3,4])
    [0.0, 0.42857142857142855, 0.5714285714285714]
    >>> common.unitNormalizeProportion([1,1,1])
    [0.3333333..., 0.333333..., 0.333333...]


    On 32-bit computers this number is inexact.  On 64-bit it works fine.


    #>>> common.unitNormalizeProportion([.2, .6, .2])
    #[0.20000000000000001, 0.59999999999999998, 0.20000000000000001]
    """
    # note: negative values should be shifted to positive region first
    summation = 0
    for x in values:
        if x < 0:
            raise ValueError('value members must be positive')
        summation += x
    unit = [] # weights on the unit interval; sum == 1
    for x in values:
        unit.append((x / float(summation)))
    return unit

def unitBoundaryProportion(series):
    """Take a series of parts with an implied sum, and create unit-interval boundaries proportional to the series components.


    >>> common.unitBoundaryProportion([1,1,2])
    [(0, 0.25), (0.25, 0.5), (0.5, 1.0)]
    >>> common.unitBoundaryProportion([8,1,1])
    [(0, 0.8...), (0.8..., 0.9...), (0.9..., 1.0)]
    """
    unit = unitNormalizeProportion(series)
    bounds = []
    summation = 0
    for i in range(len(unit)):
        if i != len(unit) - 1: # not last
            bounds.append((summation, summation + unit[i]))
            summation += unit[i]
        else: # last, avoid rounding errors
            bounds.append((summation, 1.0))
    return bounds


def weightedSelection(values, weights, randomGenerator=None):
    '''
    Given a list of values and an equal-sized list of weights,
    return a randomly selected value using the weight.

    Example: sum -1 and 1 for 100 values; should be
    around 0 or at least between -30 and 30


    >>> -30 < sum([common.weightedSelection([-1, 1], [1,1]) for x in range(100)]) < 30
    True
    '''
    if randomGenerator is not None:
        q = randomGenerator() # must be in unit interval
    else: # use random uniform
        q = random.random()
    # normalize weights w/n unit interval
    boundaries = unitBoundaryProportion(weights)
    i = 0
    for i, (low, high) in enumerate(boundaries):
        if q >= low and q < high: # accepts both boundaries
            return values[i]
    # just in case we get the high boundary
    return values[i]


def euclidGCD(a, b):
    '''use Euclid\'s algorithm to find the GCD of a and b


    >>> common.euclidGCD(2,4)
    2
    >>> common.euclidGCD(20,8)
    4
    >>> common.euclidGCD(20,16)
    4
    '''
    if b == 0:
        return a
    else:
        return euclidGCD(b, a % b)


def approximateGCD(values, grain=1e-4):
    '''Given a list of values, find the lowest common divisor of floating point values.

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
    >>> common.strTrimFloat(common.approximateGCD([1/3.,2/3.]))
    '0.3333'
    >>> common.strTrimFloat(common.approximateGCD([5/3.,2/3.,4]))
    '0.3333'
    >>> common.strTrimFloat(common.approximateGCD([5/3.,2/3.,5]))
    '0.3333'
    >>> common.strTrimFloat(common.approximateGCD([5/3.,2/3.,5/6.,3/6.]))
    '0.1667'

    '''
    lowest = float(min(values))

    # quick method: see if the smallest value is a common divisor of the rest
    count = 0
    for x in values:
        # lowest is already a float
        unused_int, floatingValue = divmod(x / lowest, 1.0)
        # if almost an even division
        if almostEquals(floatingValue, 0.0, grain=grain):
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
    return abs(a*b) // euclidGCD(a,b)

def lcm(filterList):
    '''
    Find the least common multiple of a list of values


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
    for i in range(len(filterList)):
        lcmVal = _lcm(lcmVal, filterList[i])
    return lcmVal


def groupContiguousIntegers(src):
    '''Given a list of integers, group contiguous values into sub lists


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


    >>> common.fromRoman('ii')
    2
    >>> common.fromRoman('vii')
    7

    Works with both IIII and IV forms:
    >>> common.fromRoman('MCCCCLXXXIX')
    1489
    >>> common.fromRoman('MCDLXXXIX')
    1489


    Some people consider this an error, but you see it in medieval documents:

    >>> common.fromRoman('ic')
    99

    But things like this are never seen, and thus cause an error:

    >>> common.fromRoman('vx')
    Traceback (most recent call last):
    Music21CommonException: input contains an invalid subtraction element: vx

    '''
    inputRoman = num.upper()
    nums = ['M', 'D', 'C', 'L', 'X', 'V', 'I']
    ints = [1000, 500, 100, 50,  10,  5,   1]
    places = []
    for c in inputRoman:
        if not c in nums:
            raise Music21CommonException("value is not a valid roman numeral: %s" % inputRoman)
    for i in range(len(inputRoman)):
        c = inputRoman[i]
        value = ints[nums.index(c)]
        # If the next place holds a larger number, this value is negative.
        try:
            nextvalue = ints[nums.index(inputRoman[i +1])]
            if nextvalue > value and value in [1, 10, 100]:
                value *= -1
            elif nextvalue > value:
                raise Music21CommonException("input contains an invalid subtraction element: %s" % num)
        except IndexError:
            # there is no next place.
            pass
        places.append(value)
    summation = 0
    for n in places:
        summation += n
    return summation
    # Easiest test for validity...
    #if int_to_roman(sum) == input:
    #   return sum
    #else:
    #   raise ValueError, 'input is not a valid roman numeral: %s' % input

def toRoman(num):
    '''

    Convert a number from 1 to 3999 to a roman numeral


    >>> common.toRoman(2)
    'II'
    >>> common.toRoman(7)
    'VII'
    >>> common.toRoman(1999)
    'MCMXCIX'

    >>> common.toRoman("hi")
    Traceback (most recent call last):
    TypeError: expected integer, got <... 'str'>
    '''
    if type(num) != type(1):
        raise TypeError("expected integer, got %s" % type(num))
    if not 0 < num < 4000:
        raise ValueError("Argument must be between 1 and 3999")
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
    valueHundreths = value % 100
    if valueHundreths in [11, 12, 13]:
        post = 'th'
    else:
        valueMod = value % 10
        if valueMod == 1:
            post = 'st'
        elif valueMod in [0, 4, 5, 6, 7, 8, 9]:
            post = 'th'
        elif valueMod == 2:
            post = 'nd'
        elif valueMod == 3:
            post = 'rd'

    if post != 'st' and plural:
        post += 's'
    return post

def stripAddresses(textString, replacement = "ADDRESS"):
    '''
    Function that changes all memory addresses (pointers) in the given
    textString with (replacement).  This is useful for testing
    that a function gives an expected result even if the result
    contains references to memory locations.  So for instance:


    >>> common.stripAddresses("{0.0} <music21.clef.TrebleClef object at 0x02A87AD0>")
    '{0.0} <music21.clef.TrebleClef object at ADDRESS>'

    while this is left alone:

    >>> common.stripAddresses("{0.0} <music21.humdrum.MiscTandem *>I humdrum control>")
    '{0.0} <music21.humdrum.MiscTandem *>I humdrum control>'


    For doctests, can strip to '...' to make it work fine with doctest.ELLIPSIS
    
    >>> common.stripAddresses("{0.0} <music21.base.Music21Object object at 0x102a0ff10>", '0x...')
    '{0.0} <music21.base.Music21Object object at 0x...>'


    '''
    ADDRESS = re.compile('0x[0-9A-Fa-f]+')
    return ADDRESS.sub(replacement, textString)


def sortModules(moduleList):
    '''
    Sort a lost of imported module names such that most recently modified is
    first.  In ties, last accesstime is used then module name
    
    Will return a different order each time depending on the last mod time
    '''
    sort = []
    modNameToMod = {}    
    for mod in moduleList:
        modNameToMod[mod.__name__] = mod
        fp = mod.__file__ # returns the pyc file
        stat = os.stat(fp)
        lastmod = time.localtime(stat[8])
        asctime = time.asctime(lastmod)
        sort.append((lastmod, asctime, mod.__name__))
    sort.sort()
    sort.reverse()
    # just return module list
    return [modNameToMod[modName] for lastmod, asctime, modName in sort]


def sortFilesRecent(fileList):
    '''Given two files, sort by most recent. Return only the file
    paths.


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
    return [y for dummy, y in sort]


def getMd5(value=None):
    '''
    Return an md5 hash from a string.  If no value is given then
    the current time plus a random number is encoded.

    >>> common.getMd5('test')
    '098f6bcd4621d373cade4e832627b4f6'

    '''
    if value == None:
        value = str(time.time()) + str(random.random())
    m = hashlib.md5()
    try:
        m.update(value)
    except TypeError: # unicode...
        m.update(value.encode('UTF-8'))
    
    return m.hexdigest()


def formatStr(msg, *arguments, **keywords):
    '''Format one or more data elements into string suitable for printing
    straight to stderr or other outputs

    >>> a = common.formatStr('test', '1', 2, 3)
    >>> print(a)
    test 1 2 3
    <BLANKLINE>
    '''
    if 'format' in keywords:
        formatType = keywords['format']
    else:
        formatType = None

    msg = [msg] + list(arguments)
    if six.PY3:
        for i in range(len(msg)):
            x = msg[i]
            if isinstance(x, bytes): 
                msg[i] = x.decode('utf-8')
            if not isinstance(x, str):
                try:
                    msg[i] = repr(x)
                except TypeError:
                    try:
                        msg[i] = x.decode('utf-8')
                    except AttributeError:
                        msg[i] = ""
    else:
        msg = [str(x) for x in msg]
    if formatType == 'block':
        return '\n*** '.join(msg)+'\n'
    else: # catch all others
        return ' '.join(msg)+'\n'

def strTrimFloat(floatNum, maxNum = 4):
    '''
    returns a string from a float that is at most maxNum of
    decimial digits long, but never less than 1.
    
    >>> common.strTrimFloat(42.3333333333)
    '42.3333'
    >>> common.strTrimFloat(42.3333333333, 2)
    '42.33'
    >>> common.strTrimFloat(6.66666666666666, 2)
    '6.67'
    >>> common.strTrimFloat(2.0)
    '2.0'
    >>> common.strTrimFloat(-5)
    '-5.0'
    '''
    # variables called "off" because originally designed for offsets
    offBuildString = r'%.' + str(maxNum) + 'f'
    off = offBuildString % floatNum
    offDecimal = off.index('.')
    offLen = len(off)
    for i in range(offLen - 1, offDecimal + 1, -1):
        if off[i] != '0':
            break
        else:
            offLen = offLen - 1
    off = off[0:offLen]
    return off

def dirPartitioned(obj, skipLeading=('__',)):
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
    '''
    Get the music21 directory that contains source files. This is not the same as the
    outermost package development directory.
    '''
    import music21 # pylint: disable=redefined-outer-name
    fpMusic21 = music21.__path__[0] # list, get first item 
    # use corpus as a test case
    if 'stream' not in os.listdir(fpMusic21):
        raise Exception('cannot find expected music21 directory: %s' % fpMusic21)
    return fpMusic21



def getMetadataCacheFilePath():
    r'''Get the stored music21 directory that contains the corpus metadata cache.

    >>> fp = common.getMetadataCacheFilePath()
    >>> fp.endswith('corpus/metadataCache') or fp.endswith(r'corpus\metadataCache')
    True
    '''
    return os.path.join(getSourceFilePath(), 'corpus', 'metadataCache')


def getCorpusFilePath():
    r'''Get the stored music21 directory that contains the corpus metadata cache.

    >>> fp = common.getCorpusFilePath()
    >>> fp.endswith('music21/corpus') or fp.endswith(r'music21\corpus')
    True
    '''
    from music21 import corpus
    coreCorpus = corpus.CoreCorpus()
    if coreCorpus.manualCoreCorpusPath is None:
        return os.path.join(getSourceFilePath(), 'corpus')
    return coreCorpus.manualCoreCorpusPath


def getCorpusContentDirs():
    '''Get all dirs that are found in the corpus that contain content; that is, exclude dirst that have code or other resoures.

    >>> fp = common.getCorpusContentDirs()
    >>> fp # this test will be fragile, depending on composition of dirs
    ['airdsAirs', 'bach', 'beethoven', 'ciconia', 'corelli', 'cpebach',
    'demos', 'essenFolksong', 'handel', 'haydn', 'josquin', 'leadSheet',
    'luca', 'miscFolk', 'monteverdi', 'mozart', 'oneills1850', 'palestrina',
    'ryansMammoth', 'schoenberg', 'schumann', 'schumann_clara',
    'theoryExercises', 'trecento', 'verdi', 'weber']
    '''
    directoryName = getCorpusFilePath()
    result = []
    # dirs to exclude; all files will be retained
    excludedNames = (
        'license.txt',
        'metadataCache',
        '__pycache__',
        )
    for filename in os.listdir(directoryName):
        if filename.endswith(('.py', '.pyc')):
            continue
        elif filename.startswith('.'):
            continue
        elif filename in excludedNames:
            continue
        result.append(filename)
    return sorted(result)


def getPackageDir(fpMusic21=None, relative=True, remapSep='.',
     packageOnly=True):
    '''Manually get all directories in the music21 package, including the top level directory. This is used in setup.py.

    If `relative` is True, relative paths will be returned.

    If `remapSep` is set to anything other than None, the path separator will be replaced.

    If `packageOnly` is true, only directories with __init__.py files are colllected.
    '''
    if fpMusic21 == None:
        import music21 # pylint: disable=redefined-outer-name
        fpMusic21 = music21.__path__[0] # list, get first item

    # a test if this is the correct directory
    if 'corpus' not in os.listdir(fpMusic21):
        raise Exception('cannot find corpus within %s' % fpMusic21)
    #fpCorpus = os.path.join(fpMusic21, 'corpus')
    fpParent = os.path.dirname(fpMusic21)
    match = []
    for dirpath, unused_dirnames, filenames in os.walk(fpMusic21):
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
           'zip', 'rntxt', 'command', 'scl', 'nwc', 'nwctxt', 'wav']

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

#-----------------------------
# match collections, defaultdict()

class defaultlist(list):
    '''
    Call a function for every time something is missing:
    
    >>> a = common.defaultlist(lambda:True)
    >>> a[5]
    True    
    '''
    def __init__(self, fx):
        list.__init__(self)
        self._fx = fx
    def _fill(self, index):
        while len(self) <= index:
            self.append(self._fx())
    def __setitem__(self, index, value):
        self._fill(index)
        list.__setitem__(self, index, value)
    def __getitem__(self, index):
        self._fill(index)
        return list.__getitem__(self, index)


#-----------------------------
def pitchList(pitchL):
    '''
    utility method that replicates the previous behavior of lists of pitches



    '''
    return '[' + ', '.join([x.nameWithOctave for x in pitchL]) + ']'

#-------------------------------------------------------------------------------
def wrapWeakref(referent):
    '''
    utility function that wraps objects as weakrefs but does not wrap
    already wrapped objects; also prevents wrapping the unwrapable "None" type, etc.
    '''
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
    if type(referent) is weakref.ref:
        return referent()
    else:
        return referent


def isWeakref(referent):
    '''Test if an object is a weakref


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
    if type(referent) is weakref.ref:
        return True
    return False


def findWeakRef(target):
    '''Given an object or composition of objects, find an attribute that is a weakref. This is a diagnostic tool.
    '''
    for attrName in dir(target):
        try:
            attr = getattr(target, attrName)
        except AttributeError:
            print('exception on attribute access: %s' % attrName)
        if isWeakref(attr):
            print('found weakref', attr, attrName, 'of target:', target)
        if isinstance(attr, (list, tuple)):
            for x in attr:
                findWeakRef(x)
#         elif isinstance(attr, dict):
#             for x in attr:
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
    r'''
    removes accents from unicode strings.


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

def normalizeFilename(name):
    u'''
    take a name that might contain unicode characters, punctuation,
    or spaces and
    normalize it so that it is POSIX compliant (except for the limit
    on length).

    Takes in a string or unicode string and returns a string (unicode in Py3)
    without any accented characters.

    >>> common.normalizeFilename(u'03-Niccolò all’lessandra.not really.xml')
    '03-Niccolo_alllessandra_not_really.xml'
    '''
    import unicodedata
    extension = None
    lenName = len(name)

    if lenName > 5 and name[-4] == '.':
        extension = str(name[lenName - 4:])
        name = name[:lenName -4]

    if isinstance(name, str) and six.PY2:
        name = unicode(name) # @UndefinedVariable pylint: disable=undefined-variable

    name = unicodedata.normalize('NFKD', name)
    if six.PY2:
        name = name.encode('ascii', 'ignore')
    else:
        name = name.encode('ascii', 'ignore').decode('UTF-8')
    name = re.sub(r'[^\w-]', '_', name).strip()
    if extension is not None:
        name += extension
    return name


def runningUnderIPython():
    '''
    return bool if we are running under iPython Notebook (not iPython)

    (no tests, since will be different)

    This post:
    http://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook
    says not to do this, but really, I can't think of another way to have different output as default.
    '''
    if sys.stderr.__class__.__name__ == 'OutStream':
        return True
    else:
        return False


def relativepath(path, start='.'):
    '''
    A cross-platform wrapper for `os.path.relpath()`, which returns `path` if
    under Windows, otherwise returns the relative path of `path`.

    This avoids problems under Windows when the current working directory is
    on a different drive letter from `path`.
    '''
    import platform
    if platform == 'Windows':
        return path
    return os.path.relpath(path, start)


###### test related functions

def addDocAttrTestsToSuite(suite, moduleVariableLists, outerFilename=None, globs=False, optionflags=(
            doctest.ELLIPSIS |
            doctest.NORMALIZE_WHITESPACE
            )):
    '''
    takes a suite, such as a doctest.DocTestSuite and the list of variables
    in a module and adds from those classes that have a _DOC_ATTR dictionary
    (which documents the properties in the class) any doctests to the suite.
    
    >>> import doctest
    >>> s1 = doctest.DocTestSuite(chord)
    >>> s1TestsBefore = len(s1._tests)
    >>> allLocals = [getattr(chord, x) for x in dir(chord)]
    >>> common.addDocAttrTestsToSuite(s1, allLocals)
    >>> s1TestsAfter = len(s1._tests)
    >>> s1TestsAfter - s1TestsBefore
    1
    >>> t = s1._tests[-1]
    >>> t
    isRest ()
    '''
    dtp = doctest.DocTestParser()
    if globs is False:
        globs = __import__('music21').__dict__.copy()
    for lvk in moduleVariableLists:
        if not (inspect.isclass(lvk)):
            continue
        docattr = getattr(lvk, '_DOC_ATTR', None)
        if docattr is None:
            continue
        for dockey in docattr:
            documentation = docattr[dockey]
            #print(documentation)
            dt = dtp.get_doctest(documentation, globs, dockey, outerFilename, 0)
            if len(dt.examples) == 0:
                continue
            dtc = doctest.DocTestCase(dt, optionflags=optionflags)
            #print(dtc)
            suite.addTest(dtc)


def fixTestsForPy2and3(doctestSuite):
    '''
    Fix doctests so that they work in both python2 and python3, namely
    unicode/byte characters and added module names to exceptions.
    
    >>> import doctest
    >>> s1 = doctest.DocTestSuite(chord)
    >>> common.fixTestsForPy2and3(s1)
    '''
    for dtc in doctestSuite: # Suite to DocTestCase
        if not hasattr(dtc, '_dt_test'):
            continue
        dt = dtc._dt_test # DocTest
        for example in dt.examples: # fix Traceback exception differences Py2 to Py3
            if six.PY3:
                if example.exc_msg is not None and len(example.exc_msg) > 0:
                    example.exc_msg = "..." + example.exc_msg[1:]
                elif (example.want is not None and
                        example.want.startswith('u\'')):
                    # probably a unicode example:
                    # simplistic, since (u'hi', u'bye')
                    # won't be caught, but saves a lot of anguish
                    example.want = example.want[1:]
            elif six.PY2:
                if (example.want is not None and
                        example.want.startswith('b\'')):
                    # probably a unicode example:
                    # simplistic, since (b'hi', b'bye')
                    # won't be caught, but saves a lot of anguish
                    example.want = example.want[1:]

#-------------------------------------------------------------------------------
_singletonCounter = {}
_singletonCounter['value'] = 0

class SingletonCounter(object):
    '''
    A simple counter that can produce unique numbers regardless of how many instances exist.
    
    Instantiate and then call it.
    '''
    def __init__(self):
        pass

    def __call__(self):
        post = _singletonCounter['value']
        _singletonCounter['value'] += 1
        return post

#-------------------------------------------------------------------------------
class SlottedObject(object):
    r'''
    Provides template for classes implementing slots allowing it to be pickled
    properly.
    
    Only use SlottedObjects for objects that we expect to make so many of
    that memory storage and speed become an issue.
    
    >>> import pickle
    >>> class Glissdata(common.SlottedObject):
    ...     __slots__ = ('time', 'frequency')
    >>> s = Glissdata
    >>> s.time = 0.125
    >>> s.frequency = 440.0
    >>> #_DOCS_SHOW out = pickle.dumps(s)
    >>> #_DOCS_SHOW t = pickle.loads(out)
    >>> t = s #_DOCS_HIDE -- cannot define classes for pickling in doctests
    >>> t.time, t.frequency
    (0.125, 440.0)
    '''
    
    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __getstate__(self):
        state = {}
        slots = set()
        for cls in self.__class__.mro():
            slots.update(getattr(cls, '__slots__', ()))
        for slot in slots:
            sValue = getattr(self, slot, None)
            if sValue is not None and type(sValue) is weakref.ref:
                sValue = sValue()
                print("Warning: uncaught weakref found in %r - %s, will not be rewrapped" % (self, slot))
            state[slot] = sValue
        return state

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)

#===============================================================================
# Image functions 
#===============================================================================
### Removed because only used by MuseScore and newest versions have -T option...
# try:
#     imp.find_module('PIL')
#     hasPIL = True
# except ImportError:
#     hasPIL = False
# 
# def cropImageFromPath(fp, newPath=None):
#     '''
#     Autocrop an image in place (or at new path) from Path, if PIL is installed and return True,
#     otherwise return False.  leave a border of size (
#     
#     Code from
#     https://gist.github.com/mattjmorrison/932345
#     '''
#     if newPath is None:
#         newPath = fp
#     if hasPIL:
#         from PIL import Image, ImageChops # overhead of reimporting is low compared to imageops
#         imageObj = Image.open(fp)
#         imageBox = imageObj.getbbox()
#         if imageBox:
#             croppedImg = imageObj.crop(imageBox)
#         options = {}
#         if 'transparency' in imageObj.info:
#             options['transparency'] = imageObj.info["transparency"]
# #         border = 255 # white border...
# #         tempBgImage = Image.new(imageObj.mode, imageObj.size, border)
# #         differenceObj = ImageChops.difference(imageObj, tempBgImage)
# #         boundingBox = differenceObj.getbbox()
# #         if boundingBox: # empty images return None...
# #             croppedImg = imageObj.crop(boundingBox)
#         croppedImg.save(newPath, **options)
#         return True
#         
# 
#     else:
#         from music21 import environment
#         if six.PY3:
#             pip = 'pip3'
#         else:
#             pip = 'pip'
#         environLocal = environment.Environment('common.py')        
#         environLocal.warn('PIL/Pillow is not installed -- "sudo ' + pip + ' install Pillow"')
#         return False
#         


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

    def __next__(self):
        if self.index >= len(self.data):
            raise StopIteration
        post = self.data[self.index]
        self.index += 1
        return post

    def next(self):
        return self.__next__()


#-------------------------------------------------------------------------------
class Timer(object):
    """
    An object for timing.
    
    >>> t = common.Timer()
    >>> now = t()
    >>> nownow = t()
    >>> nownow > now
    True
    >>> t.stop()
    >>> stopTime = t()
    >>> stopNow = t()
    >>> stopTime == stopNow
    True
    
    All this had better take less than one second!
    
    >>> stopTime < 1
    True
    """

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


class Music21CommonException(exceptions21.Music21Exception):
    pass

# NB -- temp files (tempFile) etc. are in environment.py


#-------------------------------------------------------------------------------
class TestMock(object):
    '''
    A test object with attributes, methods, and properties
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
        for name in self.__dict__:
            if name.startswith('_'): # avoid environemnt
                continue
            part = getattr(self, name)
            newValue = copy.deepcopy(part, memo)
            setattr(new, name, newValue)
        return new

    def __copy__(self):
        self.environLocal.printDebug(['copy called'])
        return copy.copy(self)

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


        unused_methods, attributes, unused_properties = dirPartitioned(a)
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

        #from music21 import environment
        #_MOD = "common.py"
        #environLocal = environment.Environment(_MOD)


        # test equal selection
        for j in range(10):
            x = 0
            for i in range(1000):
                # equal chance of -1, 1
                x += weightedSelection([-1, 1], [1,1])
            #environLocal.printDebug(['weightedSelection([-1, 1], [1,1])', x])
            self.assertEqual(-200 < x < 200, True)


        # test a strongly weighed boudnary
        for j in range(10):
            x = 0
            for i in range(1000):
                # 10,000 more chance of 0 than 1.
                x += weightedSelection([0, 1], [10000,1])
            #environLocal.printDebug(['weightedSelection([0, 1], [10000,1])', x])
            self.assertEqual(0 <= x < 5, True)

        for j in range(10):
            x = 0
            for i in range(1000):
                # 10,000 times more likely 1 than 0.
                x += weightedSelection([0, 1], [1, 10000])
            #environLocal.printDebug(['weightedSelection([0, 1], [1, 10000])', x])
            self.assertEqual(980 <= x <= 1000, True)


        for unused_j in range(10):
            x = 0
            for i in range(1000):
                # no chance of anything but 0.
                x += weightedSelection([0, 1], [1, 0])
            #environLocal.printDebug(['weightedSelection([0, 1], [1, 0])', x])
            self.assertEqual(x == 0, True)



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [fromRoman, toRoman]


if __name__ == "__main__":
    if len(sys.argv) == 1: # normal conditions
        import music21
        music21.mainTest(Test)


        ## do this the old way to avoid music21 import
#        s1 = doctest.DocTestSuite(__name__, optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE))
#        s2 = unittest.defaultTestLoader.loadTestsFromTestCase(Test)
#        s1.addTests(s2)
#        runner = unittest.TextTestRunner()
#        runner.run(s1)

    elif len(sys.argv) > 1:
        testModule = Test()
        testModule.testWeightedSelection()


#------------------------------------------------------------------------------
# eof

