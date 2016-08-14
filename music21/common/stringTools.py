#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common/stringTools.py
# Purpose:      Utilities for strings
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Tools for working with strings
'''
__all__ = [
           'whitespaceEqual',
           'toUnicode',
           'getNumFromStr',
           'hyphenToCamelCase',
           'camelCaseToHyphen',
           'spaceCamelCase',
           'getMd5',
           'formatStr',
           'stripAccents',
           'normalizeFilename',
           'removePunctuation',
           ]

import hashlib
import random
import re
import time
import string
import unicodedata # @UnresolvedImport

from music21.ext import six

#-------------------------------------------------------------------------------
WHITESPACE = re.compile(r'\s+')
LINEFEED = re.compile('\n+')


def whitespaceEqual(a, b):
    r'''
    returns True if a and b are equal except for whitespace differences


    >>> a = "    hello \nthere "
    >>> b = "hello there"
    >>> c = " bye there "
    >>> common.whitespaceEqual(a,b)
    True
    >>> common.whitespaceEqual(a,c)
    False
    '''
    a = WHITESPACE.sub('', a)
    b = WHITESPACE.sub('', b)
    a = LINEFEED.sub('', a)
    b = LINEFEED.sub('', b)
    if (a == b):
        return True
    else: return False


def toUnicode(usrStr):
    '''Convert this tring to a unicode string; if already a unicode string, do nothing.

    >>> common.toUnicode('test')
    'test'
    >>> common.toUnicode(u'test')
    'test'
    
    Note: this method is NOT USED and could disappear
    without notice.
    
    # TODO: Remove
    
    :rtype: str
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
            # pylint: disable=undefined-variable
            usrStr = unicode(usrStr, 'utf-8') # @UndefinedVariable  
        # some documentation may already be in unicode; if so, a TypeException will be raised
        except TypeError: #TypeError: decoding Unicode is not supported
            pass
        return usrStr


def getNumFromStr(usrStr, numbers='0123456789'):
    '''
    Given a string, extract any numbers. 
    Return two strings, the numbers (as strings) and the remaining characters.

    >>> common.getNumFromStr('23a')
    ('23', 'a')
    >>> common.getNumFromStr('23a954sdfwer')
    ('23954', 'asdfwer')
    >>> common.getNumFromStr('')
    ('', '')
    
    :rtype: tuple(str)
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





def hyphenToCamelCase(usrStr, replacement='-'):
    '''
    given a hyphen-connected-string, change it to
    a camelCaseConnectedString.  

    The replacement can be specified to be something besides a hyphen.

    This code is from: 
    
    http://stackoverflow.com/questions/4303492/
    how-can-i-simplify-this-conversion-from-underscore-to-camelcase-in-python

    >>> common.hyphenToCamelCase('movement-name')
    'movementName'

    >>> common.hyphenToCamelCase('movement_name', replacement='_')
    'movementName'

    '''
    PATTERN = re.compile(r'''
    (?<!\A) # not at the start of the string
    ''' + replacement + r'''
    (?=[a-zA-Z]) # followed by a letter
    ''', re.X)
    
    tokens = PATTERN.split(usrStr)
    response = tokens.pop(0).lower()
    for remain in tokens:
        response += remain.capitalize()
    return response
    
def camelCaseToHyphen(usrStr, replacement='-'):
    '''
    Given a camel-cased string, or a mixture of numbers and characters, 
    create a space separated string.

    The replacement can be specified to be something besides a hyphen, but only
    a single character and not (for internal reasons) an uppercase character.

    code from http://stackoverflow.com/questions/1175208/
        elegant-python-function-to-convert-camelcase-to-camel-case

    >>> common.camelCaseToHyphen('movementName')
    'movement-name'

    First letter can be uppercase as well:
    
    >>> common.camelCaseToHyphen('MovementName')
    'movement-name'

    >>> common.camelCaseToHyphen('movementNameName')
    'movement-name-name'
    
    >>> common.camelCaseToHyphen('fileName', replacement='_')
    'file_name'

    Some things you cannot do:

    >>> common.camelCaseToHyphen('fileName', replacement='NotFound')
    Traceback (most recent call last):
    ValueError: Replacement must be a single character.
    
    >>> common.camelCaseToHyphen('fileName', replacement='A')
    Traceback (most recent call last):
    ValueError: Replacement cannot be an uppercase character.
    '''
    if len(replacement) != 1:
        raise ValueError('Replacement must be a single character.')
    elif replacement.lower() != replacement:
        raise ValueError('Replacement cannot be an uppercase character.')
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1' + replacement + r'\2', usrStr)
    return re.sub('([a-z0-9])([A-Z])', r'\1' + replacement + r'\2', s1).lower()

def spaceCamelCase(usrStr, replaceUnderscore=True, fixMeList=None):
    '''
    Given a camel-cased string, or a mixture of numbers and characters, 
    create a space separated string.

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
    
    There is a small list called fixMeList that can fix mistakes.
    
    >>> common.spaceCamelCase('PMFC22')
    'PMFC 22'

    >>> common.spaceCamelCase('hello_myke')
    'hello myke'
    >>> common.spaceCamelCase('hello_myke', replaceUnderscore = False)
    'hello_myke'

    :rtype: str
    '''
    numbers = '0123456789.'
    firstNum = False
    firstChar = False
    isNumber = False  
    lastIsNum = False
    post = []
    
    # do not split these...
    if fixMeList is None:
        fixupList = ('PMFC',)
    else:
        fixupList = fixMeList

    for char in usrStr:
        if char in numbers:
            isNumber = True
        else:
            isNumber = False

        if isNumber and not firstNum and not lastIsNum:
            firstNum = True
        else:
            firstNum = False

        # for chars
        if not isNumber and not firstChar and lastIsNum:
            firstChar = True
        else:
            firstChar = False

        if len(post) > 0:
            if char.isupper() or firstNum or firstChar:
                post.append(' ')
            post.append(char)
        else: # first character
            post.append(char)

        if isNumber:
            lastIsNum = True
        else:
            lastIsNum = False
    postStr = ''.join(post)
    for fixMe in fixupList:
        fixMeSpaced = ' '.join(fixMe)
        postStr = postStr.replace(fixMeSpaced, fixMe)
    
    if replaceUnderscore:
        postStr = postStr.replace('_', ' ')
    return postStr



def getMd5(value=None):
    '''
    Return an md5 hash from a string.  If no value is given then
    the current time plus a random number is encoded.

    >>> common.getMd5('test')
    '098f6bcd4621d373cade4e832627b4f6'

    :rtype: str
    '''
    if value is None:
        value = str(time.time()) + str(random.random())
    m = hashlib.md5()
    try:
        m.update(value)
    except TypeError: # unicode...
        m.update(value.encode('UTF-8'))
    
    return m.hexdigest()


def formatStr(msg, *arguments, **keywords):
    '''
    Format one or more data elements into string suitable for printing
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


def stripAccents(inputString):
    r'''
    removes accents from unicode strings.

    >>> s = u'trés vite'
    
    >>> u'é' in s
    True
    
    This works on Python2, but the doctest does not.
    
    >>> if ext.six.PY3:
    ...     common.stripAccents(s)
    ... else: 'tres vite'
    'tres vite'
    '''
    nfkd_form = unicodedata.normalize('NFKD', inputString)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

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


    :type name: str
    :rtype: str

    '''
    extension = None
    lenName = len(name)

    if lenName > 5 and name[-4] == '.':
        extension = str(name[lenName - 4:])
        name = name[:lenName -4]

    if isinstance(name, str) and six.PY2:
        name = unicode(name) # @UndefinedVariable pylint: disable=undefined-variable

    name = stripAccents(name)
    if six.PY2:
        name = name.encode('ascii', 'ignore')
    else:
        name = name.encode('ascii', 'ignore').decode('UTF-8')
    name = re.sub(r'[^\w-]', '_', name).strip()
    if extension is not None:
        name += extension
    return name

def removePunctuation(s):
    '''
    Remove all punctuation from a string -- very different in Py2 vs Py3
    so moved out...

    >>> common.removePunctuation("This, is! my (face).")
    'This is my face'

    >>> common.removePunctuation(u"This, is! my (face).")
    u'This is my face'
    '''
    if six.PY2:
        # pylint: disable=undefined-variable
        wasUnicode = False
        if isinstance(s, unicode): # @UndefinedVariable
            s = s.encode('utf-8')
            wasUnicode = True
        out = s.translate(string.maketrans("", ""), string.punctuation) # @UndefinedVariable
        if wasUnicode:
            out = unicode(out, encoding='utf-8') # @UndefinedVariable
    
    else:
        maketrans = str.maketrans("", "", string.punctuation)
        out = s.translate(maketrans)
    return out


#------------------------------------------------------------------------------

if __name__ == "__main__":
    import music21 # @Reimport
    music21.mainTest()
#------------------------------------------------------------------------------
# eof
