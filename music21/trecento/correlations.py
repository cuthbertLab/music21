'''
Created on Nov 5, 2009

@author: cuthbert
'''

import music21
import music21.analysis.correlate
from music21 import *
import cadencebook

def pitchToNoteLength():
    '''
    get a quick 3D image of the relationship between pitch and notelength in trecento ballata cadences
    '''
    allStream = stream.Stream()
    b = cadencebook.BallataSheet()
    for work in b:
        for snippet in work.snippetBlocks:
            if snippet is None:
                continue
            for thisStream in snippet.streams:
                allStream.append(thisStream)
    c = music21.analysis.correlate.NoteAnalysis(allStream.flat)
    c.noteAttributeCount()
        
pitchToNoteLength()
        