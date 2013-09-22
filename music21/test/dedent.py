# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         dedent.py
# Purpose:      Dedent an indented multi-line string
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21 
#               Project
# License:      LGPL, see license.txt
#------------------------------------------------------------------------------


def dedent(string):
    splitLines = string.split('\n')
    if not splitLines[0] or splitLines[0].isspace():
        splitLines.pop(0)
    if not splitLines[-1] or splitLines[-1].isspace():
        splitLines.pop(-1)

    for indentWidth, character in enumerate(splitLines[0]):
        if character != ' ':
            break
    massagedLines = []
    for splitLine in splitLines:
        massagedLine = splitLine[indentWidth:]
        massagedLines.append(massagedLine)
    massagedString = '\n'.join(massagedLines)
    return massagedString
