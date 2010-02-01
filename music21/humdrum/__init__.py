#-------------------------------------------------------------------------------
# Name:         humdrum.__init__.py
# Purpose:      base module for emulating Humdrum functionality in music21
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''
Files in this package deal specifically with making life easier for
people who have previously used humdrum or need to import
humdrum data (in spines, etc.) into music21.

typical usage:

import music21.humdrum
score1 = music21.humdrum.parseFile("chopin.krn")

#-----------------------------------------------------------------------
Humdrum programs and their closest music21 equivalents:

HUMDRUM         music21             NOTES
---------------------------------------------------------------------------
assemble        None                Use python commands to unite objects
census          None                Use python to create census equivalents
cents           interval.ChromaticInterval.cents    (tuning will eventually affect this; produces cents w.r.t. interval not middle C)
cleave          None                kern specific, not needed
context         None                Not needed.  Use object.next and object.prev to get some context for many objects
correl          None                Use numpy.corrcoef() or other, more sophisticated code
deg             Key.degree(Note)    NOT YET WRITTEN -- for music21 v0.6b.  You will want to run key.keyFromStream() or key.keyFromStreams() first if key is unknown
degree          Key.degree(Note)    Returns a scale.ScaleDegree object which will have various representations
diss            analysis.kkdiss     NOT YET WRITTEN -- for music21 v2.0.
ditto           None                Not needed.  Use copy.copy(object) or copy.deepcopy(object) to get another copy of an object
encode          midi.(severaltools) Multifunction humdrum program.  Replaced by midi tools.  (NOT YET WRITTEN: simple midi in v0.3a; more complex in v2.0)
extract         None                Use python commands to extract objects with certain properties
fields          None                Not needed.
fin2hum         music21.musicxml.parseFile(filename) (Outputting to Kern is not a priority of the music21 team for now; We do not read Finale files in Enigma, only those in musicXML.  An Enigma to music21 converter is a low priority.  Software to do this is available from recordare
freq            note.Note.freq440
hint            twoStreams.TwoStreamComparer.intervalToOtherStreamWhenAttacked()   or other similar functions
hum2fin         m21xml.write()      Writes to musicXML.  A music21 to enigma converter is an extremely low priority since musicXML has made writing new Enigma files essentially obsolete.
humdrum         None                Not needed.
humsed          None                Not needed.
humver          None                Not needed.
infot           None                Use general purpose python information theory models
iv              Chord.intervalVector  NOT YET WRITTEN (2008-10-18) (v0.6b)
kern            kern.write()        Outputting to kern not planned at this time.
key             Key.keyFromStream() NOT YET WRITTEN (2008-10-18) (v0.6b)
melac           analysis.thomassen.MelodicAccent    NOT YET WRITTEN -- lower priority (v2.0 or later)
metpos          meter.addAccentToStream()   NOT YET WRITTEN -- high priority (v0.3a)
midi            midi.write()        NOT YET WRITTEN -- however, lily.ShowPNGandPlayMIDI() already works using the Lilypond midi functions
midireset       midi.allOff()       NOT YET WRITTEN -- v2.0 -- good to have though...
mint            Interval(note1, stream.noteFollowingNote(note1))
nf              Chord.normalForm    NOT YET WRITTEN -- (v0.6b)
num             None                not needed
patt            None                Not needed, However, see, for instance, trecento.find_trecento_fragments for an example of a pattern searching module
pattern         None                see patt above
pc              Note.pitchClass
pcset           Chord.pcset         NOT YET WRITTEN (v0.6); Returns PitchClassSet object.  PitchClassSet.forte, .normalForm, .primeForm, etc. will exist 
perform         midi.play           For now use lily.ShowPNGandPlayMIDI()
pf              PitchClassSet.primeForm   NOT YET WRITTEN -- see pcset
pitch           Note.name + str(Note.octave)
proof           None                Not needed; but something like this could be useful for each encoding format, however.
recode          "if"
record          none yet...         Not yet determined if it is a good idea to record directly to music21 within music21 -- a MIDI to music21 converter should suffice.
regexp          None                Use re module in Python core, not music21
reihe           twelveTone.Row      NOT YET WRITTEN -- v0.6
rend            None                Not needed.
rid             None                Not needed.
scramble        None                Use random module in Python core, not music21.  However, see composition tools for some sophisticated scrambling methods
semits          Note.pitchClass, Note.midiNote or Interval.chromatic.  Also Accidental.alter
simil           None                Download http://www.mindrot.org/projects/py-editdist/ ; Possibly to be embedded later esp. for different costs...
smf             midi.write          See midi above
solfa           Key.chromaticSolfege(Note)  NOT YET WRITTEN
solfg           Note.frenchSolfege  NOT YET WRITTEN -- see also to be written chromaticFixedDoSolfege()
strophe         Note.lyric.strophe[i] NOT YET WRITTEN
synco           analysis.leeLHiggins    NOT YET WRITTEN -- low priority
tacet           midi.allOff()       see midireset above; -i will not be supported
timebase        None                Not needed.  stream.getElementsByOffset() will cover most uses
tonh            Note.germanName     NOT YET WRITTEN -- simple, but low priority
trans           Note.transpose(Interval), Stream.transpose(Interval), etc -- not yet written, but interval.getNoteAboveNote(Note, Interval) works fine.  Modal transpositions still are needed
urrhythm        analysis.JohnsonLaird.urrhythm(Stream)  NOT YET WRITTEN -- low priority
veritas         None                Not needed.  use md5 or other checksum files
vox             None                Chord.numNotes() works for a chord.  TwoStreamComparer has many methods for performing this function.
xdelta          None                Not needed.
yank            "if"
ydelta          None                Not needed.
'''

__ALL__ = ['spineParser','testFiles','questions','utils']

import spineParser

def parseFile(filename):
    return spineParser.HumdrumFile(filename)

def parseData(data):
    return spineParser.HumdrumDataCollection(data)

