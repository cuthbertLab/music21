# -*- coding: utf-8 -*-
_DOC_IGNORE_MODULE_OR_PACKAGE = True


'''
Created on Nov 5, 2009

@author: cuthbert
'''
from music21 import stream
from music21.trecento import cadencebook
from music21 import graph

def pitchToNoteLength():
    '''
    get a quick 3D image of the relationship between pitch and notelength in trecento ballata cadences
    '''
    allStream = stream.Stream()
    b = cadencebook.BallataSheet()
    for work in b:
        for snippet in work.snippets:
            if snippet is None:
                continue
            for thisStream in snippet.streams:
                allStream.append(thisStream)

    #c = music21.analysis.correlate.NoteAnalysis(allStream.flat)
    #c.noteAttributeCount()

    g = graph.Plot3DBarsPitchSpaceQuarterLength(allStream.flat)
    g.process()

if __name__ == "__main__":   
    pitchToNoteLength()
    

#------------------------------------------------------------------------------
# eof

