# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         humdrum.__init__.py
# Purpose:      base module for emulating Humdrum functionality in music21
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2009-12 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Files in this package deal specifically with making life easier for
people who have previously used humdrum or need to import
humdrum data (in spines, etc.) into music21.


Humdrum programs and their closest music21 equivalents:


============  ===============================================  =========================================================================================================================================================================
Humdrum       music21                                          notes
============  ===============================================  =========================================================================================================================================================================
assemble      None                                             Use python commands to unite objects
census        None                                             Use python to create census equivalents
cents         interval.ChromaticInterval.cents                 (tuning will eventually affect this; produces cents w.r.t. interval not middle C)
cleave        None                                             kern specific, not needed
context       None                                             Not needed.  Use object.next and object.prev to get some context for many objects
correl        None                                             Use numpy.corrcoef() or other, more sophisticated code
deg           Several Tools, see Notes                         Closest is :meth:`~music21.scale.Scale.getScaleDegreeAndAccidentalFromPitch`. See also stream.analyze('key')
degree        see above for "deg"
diss          To-Do                                            Will be "analysis.kkdiss".
ditto         None                                             Use copy.copy(object) or copy.deepcopy(object) to get another copy of an object
encode        midi.(severaltools)                              Multifunction humdrum program.  See the midi directory for some replacements.
extract       None                                             Use python commands to extract objects with certain properties
fields        None                                             Not needed.
fin2hum       music21.converter.parse(filename)                Currently we only parse MusicXML files; as far as I know, Enigma Transport Format did not take off and is rarely used. (Outputting to Kern is not a priority of the music21 team for now; We do not read Finale files in Enigma, only those in musicXML.  An Enigma to music21 converter is a low priority.  Software to do this is available from recordare
freq          see :meth:`~music21.note.Note.freq440` 
hint          see Notes                                        :meth:`~music21.stream.Stream.attachIntervalsBetweenStreams` See trecento.capua demo to show how it can be done.
hum2fin       .write('musicxml')                               Writes to musicXML.  A music21 to enigma converter will not be written (obsolete format)
humdrum       None                                             Not needed.
humsed        None                                             Not needed.
humver        None                                             Not needed.
infot         None                                             Use general purpose python information theory models
iv            :meth:`~music21.chord.Chord.intervalVector` 
kern          To-Do                                            myScore.write('kern') -- Outputting to kern is a priority.
key           :meth:`~music21.stream.Stream.analyze`('key')
melac         To-Do                                            analysis.thomassen.MelodicAccent; lower priority but easily done (v2.0 or later)
metpos        1.0/obj.beatStrength()                           the beatStrength of an object is essentially something similar but inverted.  beatStrength handles irregular meters.
midi          .show('midi')
midireset     None                                             Not needed for now because we do not write directly to MIDI.  A midi.allOff() will be needed for direct midi access...
mint          Interval(note1, note2)                           Or :meth:`~music21.stream.Stream.melodicIntervals`
nf            :meth:`~music21.chord.Chord.normalForm`
num           None                                             not needed
patt          search.*                                         see also, for instance, trecento.find_trecento_fragments for an example of a pattern searching module
pattern       search.*                                         see patt above
pc            :meth:`~music21.pitch.Pitch.pitchClass`
pcset         see Pitch.* and Chord.*                          Pitch.pitchClass and pitchClassString, Chord.normalForm, .primeForm, .intervalVector, etc.
perform       .show('midi')
pf            :meth:`~music21.chord.Chord.normalForm`
pitch         :meth:`~music21.pitch.Pitch.noteNameWithOctave`
proof         None                                             Not needed; However, something like this could be useful for each encoding format.
recode        "if"
record        None yet...                                      Not yet determined if it is a good idea to record directly to music21 within music21 -- a MIDI to music21 converter should suffice.  But note that audioSearch.recording gives recording transcription abilities
regexp        None                                             Use `re` module in Python core, not music21
reihe         :class:`~music21.serial.TwelveToneRow`
rend          None                                             Not needed.
rid           None                                             Not needed.
scramble      None                                             Use random module in Python core, not music21.  However, see composition tools for some sophisticated scrambling methods
semits        see Notes                                        :meth:`~music21.pitch.Pitch.ps`, :meth:`~music21.pitch.Pitch.p.midiNote` or :meth:`~music21.interval.Interval.chromatic`.  See also :class:`music21.pitch.Accidental`, esp. the `.alter` property.
simil         None                                             Download http://www.mindrot.org/projects/py-editdist/ ; Possibly to be embedded later esp. for different costs...
smf           .write('midi')                                   See midi above
solfa         key.Key.solfeg()                                 Use variant='humdrum' to get exact humdrum solfeg syllables
solfg         None                                             Very easily written by users
strophe       text.assembleLyrics(i)                           You probably won't need this though
synco         To-Do                                            Will be "analysis.leeLHiggins" but not yet written -- low priority
tacet         None                                             see midireset above; -i will not be supported
timebase      None                                             Not needed.  stream.getElementsByOffset() will cover most uses
tonh          :meth:`~music21.pitch.Pitch.germanName` 
trans         .transpose(Interval)                             Note.transpose(), Stream.transpose(), etc
urrhythm      To-Do                                            will be "analysis.JohnsonLaird.urrhythm(Stream)" but not yet written -- low priority
veritas       None                                             Not needed.  use md5 or other checksum files
vox           None                                             len(Chord.pitches()) works for a chord.  Stream has many methods for performing this function.
xdelta        None                                             Not needed.
yank          "if"
ydelta        None                                             Not needed.
============  ===============================================  =========================================================================================================================================================================

'''

__ALL__ = ['spineParser','testFiles','questions']

import spineParser
import testFiles
import questions

def parseFile(filename):
    '''
    shortcut to :class:`~music21.humdrum.spineParser.HumdrumFile`.  Most users will call `converter.parse()` instead.
    '''
    return spineParser.HumdrumFile(filename)

def parseData(data):
    '''
    shortcut to :class:`~music21.humdrum.spineParser.HumdrumDataCollection`. Most users will call `converter.parse()` instead.
    '''
    return spineParser.HumdrumDataCollection(data)


#------------------------------------------------------------------------------
# eof

