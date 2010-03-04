#!/usr/bin/python

'''
contenance_angloise.py -- module to run tests on the percentage of sixths etc. to test theories about
the contenance angloise in 14th and 15th century music

'''

from music21.trecento import cadencebook

debug = True

def sortMelodicFifths():
    '''
    Finds instances of melodic Perfect fifths or Fourths (a harmonic version should also be made)
    to see if the B-F# fifth/fourth is actually less used than other common fifths when adjusting
    for the % of notes that are B or F#.
    '''
    ballataObj = cadencebook.BallataSheet()
    for pieceObj in ballataObj:
        if pieceObj.incipitClass() is None:
            continue
        print(pieceObj.title)
        for polyphonicSnippet in pieceObj.snippets:
            if polyphonicSnippet is None:
                continue
            for thisStream in polyphonicSnippet.streams:
                thisStream.generateIntervalLists()
                for thisNote in thisStream:
                    if thisNote.editorial is None:
                        continue
                    elif thisNote.editorial.melodicIntervalOverRests is None:
                        continue
                    elif thisNote.editorial.melodicIntervalOverRests.simpleName == "P4" or \
                        thisNote.editorial.melodicIntervalOverRests.simpleName == "P5":
                        print(thisNote.name)

if (__name__ == "__main__"):
    sortMelodicFifths()