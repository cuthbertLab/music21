.. _examples:


Examples
==========================

Some simple ideas to get started
--------------------------------

1. Load a musicxml file and count the number of G#'s in it::

    from music21 import *
    chopinScore = converter.parse("mazurka6.xml")
    
    ## a flat representation puts all notes, dynamics, etc.
    ## from all parts into one giant data stream
    chopinFlat = chopinScore.flat
    pitches = chopinFlat.getPitches()
    
    totalGSharps = 0
    for thisPitch in pitches:
        if thisPitch.name == 'G#':
            totalGSharps += 1
    
    print totalGSharps


Style Analysis
--------------

These are examples only to test syntax coloring. 

Create a note and process it::


    from music21 import note
    a = note.Note()


.. note::
    There are many varieties of Note objects::

        b = note.SimpleNote()




Statistical Processing
----------------------------
