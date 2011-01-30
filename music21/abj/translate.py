#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         translate.py
# Purpose:      Translation from music21 into Abjad
#
# Authors:      Michael Scott Cuthbert
#               Trevor Baca
#
# Copyright:    (c) 2011 The music21 Project / Victor Adan and Trevor Baca
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Translation methods for going from music21 to Victor Adan and
Trevor Baca's Abjad framework -- a high-quality, Lilypond-based python
framework for algorithmic music composition and post-tonal music.

See http://packages.python.org/Abjad/ for more details.  Requires
abjad 2.0 (not 1.1.1) to work.  Fetchable via SVN as of January 2011.

automatically imported in music21.abj:

'''

import unittest,doctest
import music21
import music21.note
import music21.common

import re

try:
    import abjad
except ImportError:
    abjad = None
    
if abjad is not None:
    try:
        x = int(abjad.cfgtools.get_abjad_revision_string())
        if x < 4000:
            raise ImportError('This version of abjad is not compatible with music21, please upgrade')
            abjad = None
    except:
        abjad = None



class AbjadTranslateException(music21.Music21Exception):
    pass

def translateLilyStringPitch(lilyStringPitch):
    '''
    Translates cis to cs
    
    And ces to cf
    
    
    >>> translateLilyStringPitch("cis''2")
    "cs''2"
    
    '''
    lilyStringPitch = lilyStringPitch.replace('is', 's')
    lilyStringPitch = lilyStringPitch.replace('es', 'f')
    return lilyStringPitch   
    

def music21ObjectToAbjad(m21Object):
    '''
    translates an arbitrary object into abjad objects.
    
    might return a tuple because some single m21 objects will
    require multiple abjad objects (and vice versa).
    
    '''
    if "Note" in m21Object.classes:
        return noteToAbjad(m21Object)
    elif "Stream" in m21Object.classes:
        return streamToAbjad(m21Object)
    else:
        pass
        #raise AbjadTranslateException('cannot translate object of class %s', m21Object.__class__.__name__ )
    
    

def noteToAbjad(m21Note):
    '''
    Translates a simple music21 Note (no ties or tuplets) to an abjad note.
    
    >>> import abjad
    >>> import music21
    >>> m21Note1 = music21.note.Note("C#5")
    >>> m21Note1.quarterLength = 2
    >>> abjadNote1 = music21.abj.noteToAbjad(m21Note1)
    >>> abjadNote1
    Note("cs''2")
    >>> #_DOCS_SHOW abjad.iotools.show(abjadNote1)
    
    .. image:: images/abjad_output_cs.*
            :width: 217



    >>> m21Note2 = music21.note.Note("D--2")
    >>> m21Note2.quarterLength = 0.125
    >>> abjadNote2 = music21.abj.noteToAbjad(m21Note2)
    >>> abjadNote2
    Note('dff,32')
    
    >>> m21Note3 = music21.note.Note("E-6")
    >>> m21Note3.quarterLength = 2.333333333333333
    >>> abjadNote3 = music21.abj.noteToAbjad(m21Note3)
    Traceback (most recent call last):
    AbjadTranslateException: cannot translate complex notes directly
    '''
    if m21Note.duration.type == 'complex':
        raise AbjadTranslateException("cannot translate complex notes directly")
    elif len(m21Note.duration.tuplets) > 0:
        raise AbjadTranslateException("cannot translate tuplet notes directly")
    
    x = translateLilyStringPitch(str(m21Note.lily))
    abjadNote = abjad.Note(x)
    return abjadNote

def pitchToAbjad(m21Pitch):
    '''
    translates a music21 :class:`music21.pitch.Pitch` object 
    to abjad.Pitch object
    
    >>> import music21
    >>> m21p = music21.pitch.Pitch("D--2")
    >>> music21.abj.pitchToAbjad(m21p)
    NamedChromaticPitch('dff,')
    '''    
    music21name = m21Pitch.name
    abjadPitchName = music21name.replace('-','f').replace('#','s')
    abjadPitch = abjad.pitchtools.NamedChromaticPitch(abjadPitchName, m21Pitch.octave)
    return abjadPitch


def streamToAbjad(m21Stream, makeNotation = True):
    '''
    translates a Stream into an Abjad container
    
    >>> import abjad
    >>> import music21
    >>> stream1 = music21.parse("c4 d8. e-16 FF2", "4/4")
    >>> abjadContainer = music21.abj.streamToAbjad(stream1)
    >>> abjadContainer
    Staff{4}
    >>> abjadContainer.leaves[:]
    (Note("c'4"), Note("d'8."), Note("ef'16"), Note('f,2'))
    >>> #_DOCS_SHOW abjad.iotools.show(abjadContainer)


    .. image:: images/abjad_translateStream1.*
            :width: 371
    
    
    '''
    #if makeNotation == True:
    #    m21FinishedStream = m21Stream.makeNotation() 
    #else:
    m21FinishedStream = m21Stream
    abjadNotes = []
    
    for thisObject in m21FinishedStream:
        x = music21ObjectToAbjad(thisObject)
        if x is not None:
            abjadNotes.append(x) 
    
    abjadContainer = abjad.Staff(abjadNotes)
    return abjadContainer


class Test(unittest.TestCase):
    pass

    def runTest(self):
        pass

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [noteToAbjad]


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()
#        a.testMusicXMLExport()

#------------------------------------------------------------------------------
# eof
