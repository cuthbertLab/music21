# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         dedent.py
# Purpose:      Dedent an indented multi-line string
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21 
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
# TODO: is this the same as textwrap.dedent()?  If so, delete and replace.

def dedent(string):
    r'''
    >>> from music21.test.dedent import dedent
    >>> msg = '    Hello\n    There\n        My friend\n    Hi!'
    >>> print(msg)
        Hello
        There
            My friend
        Hi!
    >>> out = dedent(msg)
    >>> print(out)
    Hello
    There
        My friend
    Hi!
    '''
    splitLines = string.split('\n')
    if not splitLines[0] or splitLines[0].isspace():
        splitLines.pop(0)
    if not splitLines[-1] or splitLines[-1].isspace():
        splitLines.pop(-1)

    indentWidth = 0
    for indentWidth, character in enumerate(splitLines[0]):
        if character != ' ':
            break
    massagedLines = []
    for splitLine in splitLines:
        massagedLine = splitLine[indentWidth:]
        massagedLines.append(massagedLine)
    massagedString = '\n'.join(massagedLines)
    return massagedString

if __name__ == '__main__':
    import music21
    music21.mainTest()
