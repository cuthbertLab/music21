# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/stringTools.py
# Purpose:      Utilities for strings
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Tools for working with strings
'''
from __future__ import annotations

__all__ = [
    'whitespaceEqual',
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
import unicodedata

# ------------------------------------------------------------------------------
WHITESPACE = re.compile(r'\s+')
LINEFEED = re.compile('\n+')


def whitespaceEqual(a: str, b: str) -> bool:
    # noinspection PyShadowingNames
    r'''
    returns True if a and b are equal except for whitespace differences

    >>> a = '    hello \n there '
    >>> b = 'hello there'
    >>> c = ' bye there '
    >>> common.whitespaceEqual(a, b)
    True
    >>> common.whitespaceEqual(a, c)
    False
    '''
    a = WHITESPACE.sub('', a)
    b = WHITESPACE.sub('', b)
    a = LINEFEED.sub('', a)
    b = LINEFEED.sub('', b)
    if a == b:
        return True
    else:
        return False


def getNumFromStr(usrStr: str, numbers: str = '0123456789') -> tuple[str, str]:
    '''
    Given a string, extract any numbers.
    Return two strings, the numbers (as strings) and the remaining characters.

    >>> common.getNumFromStr('23a')
    ('23', 'a')
    >>> common.getNumFromStr('23a954Hello')
    ('23954', 'aHello')
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
    # returns numbers and then characters
    return ''.join(found), ''.join(remain)


def hyphenToCamelCase(usrStr: str, replacement: str = '-') -> str:
    '''
    Given a hyphen-connected-string, change it to
    a camelCaseConnectedString.

    The replacement can be specified to be something besides a hyphen.

    >>> common.hyphenToCamelCase('movement-name')
    'movementName'

    >>> common.hyphenToCamelCase('movement_name', replacement='_')
    'movementName'

    Safe to call on a string lacking the replacement character:

    >>> common.hyphenToCamelCase('voice')
    'voice'

    And on "words" beginning with numbers:

    >>> common.hyphenToCamelCase('music-21')
    'music21'
    '''
    post = ''
    for i, word in enumerate(usrStr.split(replacement)):
        if i == 0:
            post = word
        else:
            post += word.capitalize()
    return post


def camelCaseToHyphen(usrStr: str, replacement: str = '-') -> str:
    # pylint: disable=line-too-long
    '''
    Given a camel-cased string, or a mixture of numbers and characters,
    create a space separated string.

    The replacement can be specified to be something besides a hyphen, but only
    a single character and not (for internal reasons) an uppercase character.

    code from https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case

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
    if replacement.lower() != replacement:
        raise ValueError('Replacement cannot be an uppercase character.')
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1' + replacement + r'\2', usrStr)
    return re.sub('([a-z0-9])([A-Z])', r'\1' + replacement + r'\2', s1).lower()


def spaceCamelCase(usrStr: str, replaceUnderscore=True, fixMeList=None) -> str:
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
    >>> common.spaceCamelCase('hello_myke', replaceUnderscore=False)
    'hello_myke'
    '''
    numbers = '0123456789.'
    firstNum = False
    firstChar = False
    isNumber = False
    lastIsNum = False
    post: list[str] = []

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

        if post:
            if char.isupper() or firstNum or firstChar:
                post.append(' ')
            post.append(char)
        else:  # first character
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


def getMd5(value=None) -> str:
    # noinspection SpellCheckingInspection
    '''
    Return an md5 hash from a string.  If no value is given then
    the current time plus a random number is encoded.

    >>> common.getMd5('test')
    '098f6bcd4621d373cade4e832627b4f6'
    '''
    if value is None:
        value = str(time.time()) + str(random.random())
    m = hashlib.md5()
    try:
        m.update(value)
    except TypeError:  # unicode...
        m.update(value.encode('UTF-8'))

    return m.hexdigest()


def formatStr(msg,
              *rest_of_message,
              **keywords) -> str:
    '''
    DEPRECATED: do not use.  May be removed at any time.

    Format one or more data elements into string suitable for printing
    straight to stderr or other outputs

    >>> a = common.formatStr('test', '1', 2, 3)
    >>> print(a)
    test 1 2 3
    <BLANKLINE>
    '''
    msg = [msg, *rest_of_message]
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
                    msg[i] = ''
    return ' '.join(msg) + '\n'


def stripAccents(inputString: str) -> str:
    r'''
    removes accents from unicode strings.

    >>> s = 'trés vite'
    >>> 'é' in s
    True
    >>> common.stripAccents(s)
    'tres vite'

    Also handles the German Eszett

    >>> common.stripAccents('Muß')
    'Muss'
    '''
    nfkd_form = unicodedata.normalize('NFKD', inputString).replace('ß', 'ss')
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])


def normalizeFilename(name: str) -> str:
    '''
    take a name that might contain unicode characters, punctuation,
    or spaces and
    normalize it so that it is POSIX compliant (except for the limit
    on length).

    Takes in a string or unicode string and returns a string (unicode in Py3)
    without any accented characters.

    >>> common.normalizeFilename('03-Niccolò all’lessandra.not really.xml')
    '03-Niccolo_alllessandra_not_really.xml'
    '''
    extension = None
    lenName = len(name)

    if lenName > 5 and name[-4] == '.':
        extension = str(name[lenName - 4:])
        name = name[:lenName - 4]

    name = stripAccents(name)
    name = name.encode('ascii', 'ignore').decode('UTF-8')
    name = re.sub(r'[^\w-]', '_', name).strip()
    if extension is not None:
        name += extension
    return name


def removePunctuation(s: str) -> str:
    '''
    Remove all punctuation from a string.

    >>> common.removePunctuation('This, is! my (face).')
    'This is my face'
    '''
    maketrans = str.maketrans('', '', string.punctuation)
    out = s.translate(maketrans)
    return out


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest()
