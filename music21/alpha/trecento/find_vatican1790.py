# -*- coding: utf-8 -*-
_DOC_IGNORE_MODULE_OR_PACKAGE = True


'''
Search for Vatican 1790 missing piece: find all ballatas in triple time

Mostly works, but needs some better snippet training...
'''

from music21 import stream
from music21.alpha.trecento import cadencebook

def find():
    ballatas = cadencebook.BallataSheet()
    opus = stream.Opus()
    i = 0
    for ballata in ballatas:
        if i > 10:
            break
        if (ballata.timeSigBegin == "6/8" or ballata.timeSigBegin == "9/8"):
            incipit = ballata.incipit
            if incipit != None:
                i += 1
                opus.insert(0, incipit)
    opus.show('lily.pdf')

if __name__ == "__main__":
    find()

#------------------------------------------------------------------------------
# eof

