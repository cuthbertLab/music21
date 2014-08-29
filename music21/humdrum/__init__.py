# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         humdrum.__init__.py
# Purpose:      base module for emulating Humdrum functionality in music21
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
Files in this package deal specifically with making life easier for
people who have previously used humdrum or need to import
humdrum data (in spines, etc.) into music21.


Humdrum programs and their closest music21 equivalents:


============  =================================================  =========================================================================================================================================================================
Humdrum       music21                                            notes
============  =================================================  =========================================================================================================================================================================
assemble_     None                                               Use python commands to unite objects and `s.insert(0, p)` to put a part at the beginning of a multipart score.
census_       None                                               Use python to create census equivalents
cents_        `interval.ChromaticInterval.cents`                 (tuning will eventually affect this; produces cents w.r.t. interval not middle C)
cleave_       None                                               kern specific, not needed
context_      None                                               Not needed.  Use object.next and object.prev to get some context for many objects and :meth:`~music21.stream.Stream.getContextByClass` to find the most recent object of a given type
correl_       None                                               Use numpy.corrcoef() or other, more sophisticated code
deg_          Several tools, see Notes                           Closest is :meth:`~music21.scale.Scale.getScaleDegreeAndAccidentalFromPitch`. See also `stream.Stream.analyze('key')`
degree_       see above for "`deg`"
diss_         To-Do                                              Will be "analysis.kkdiss".
ditto_        see Notes                                          :meth:`~music21.stream.Stream.choridfy` and the offsetTree objects accomplish similar things. Use `copy.copy(object)` or `copy.deepcopy(object)` to get another copy of an object
encode_       `midi.(severaltools)`                              Multifunction humdrum program.  See the midi directory for some replacements.  Or for simple conversion, `converter.parse` and `show('midi')` do this automatically
extract_      None                                               Use python commands to extract objects with certain properties
fields_       None                                               Not needed.
fin2hum_      `music21.converter.parse` (filename)               Currently we only parse MusicXML files; as far as I know, Enigma Transport Format did not take off and is rarely used. An Enigma to music21 converter is very low priority.  Software to convert Enigma to MusicXML is available from recordare
freq_         see :meth:`~music21.pitch.Pitch.frequency` 
hint_         see Notes                                          :meth:`~music21.stream.Stream.attachIntervalsBetweenStreams` See trecento.capua demo to show how it can be done.
hum2fin_      `.write('musicxml')`                               Writes to musicXML.  A music21 to Enigma converter will not be written (obsolete format)
humdrum_      None                                               Not needed.  The `spineParser` will report errors when parsing.
humsed_       None                                               Not needed.
humver_       None                                               Not needed.
infot_        None                                               Use general purpose python information theory models
iv_           :meth:`~music21.chord.Chord.intervalVector` 
kern_         To-Do                                              Not needed for general work, but a `myScore.write('kern')` call for outputting to kern is a priority.
key_          :meth:`~music21.stream.Stream.analyze` ('key')
melac_        see Notes                                          :meth:`~music21.analysis.metrical.thomassenMelodicAccent`.  incorporates humdrum additions for giving accent of the first and last notes.
metpos_       `1.0/obj.beatStrength()`                           the beatStrength of an object is essentially something similar but inverted.  beatStrength handles irregular meters.
midi_         `.show('midi')`
midireset_    None                                               Not needed for now because we do not write directly to MIDI.  A midi.allOff() will be needed for direct midi access...
mint_         `interval.Interval(note1, note2)`                  Or :meth:`~music21.stream.Stream.melodicIntervals`
nf_           :meth:`~music21.chord.Chord.normalForm`            Also :meth:`~music21.chord.Chord.primeForm`, :meth:`~music21.chord.Chord.intervalVector`, :meth:`~music21.chord.Chord.forteClass`, :meth:`~music21.chord.Chord.getZRelation` etc.
num_          None                                               not needed; try: `for i in range(s.flat.getElementsByClass(X))` etc.
patt_         `search.*`                                         see also, for instance, trecento.find_trecento_fragments for an example of a pattern searching module
pattern_      `search.*`                                         see patt above
pc_           :meth:`~music21.pitch.Pitch.pitchClass`
pcset_        see `Pitch.*` and `Chord.*`                        Pitch.pitchClass and pitchClassString, Chord.normalForm, .primeForm, .intervalVector, etc.
perform_      `.show('midi')`
pf_           :meth:`~music21.chord.Chord.primeForm`             Also :meth:`~music21.chord.Chord.normalForm` etc.
pitch_        :meth:`~music21.pitch.Pitch.nameWithOctave`
proof_        None                                               Not needed, see `humdrum` command above; However, something like this could be useful for each encoding format.
recode_       `"if"`
record_       None yet...                                        Not yet determined if it is a good idea to record directly to music21 within music21 -- our MIDI to music21 converter should suffice.  But note that audioSearch.recording gives recording transcription abilities
regexp_       None                                               Use `re` module in Python core, not music21
reihe_        :class:`~music21.serial.TwelveToneRow`
rend_         None                                               Not needed. Object properties perform the same function.
rid_          None                                               Not needed. Use :meth:`~music21.stream.Stream.getElementsByClass` or :meth:`~music21.stream.Stream.getElementsNotOfClass` instead
scramble_     None                                               Use random module in Python core, not music21.  However, see composition tools for some sophisticated scrambling methods
semits_       see Notes                                          :meth:`~music21.pitch.Pitch.ps`, :meth:`~music21.pitch.Pitch.p.midiNote` or :meth:`~music21.interval.Interval.chromatic`.  See also :class:`music21.pitch.Accidental`, esp. the `.alter` property.
simil_        None                                               Download http://www.mindrot.org/projects/py-editdist/ ; Possibly to be embedded later esp. for different costs...
smf_          `.write('midi')`                                   See midi above
solfa_        :meth:`~music21.scale.ConcreteScale.solfeg`        Use variant='humdrum' to get exact humdrum solfeg syllables
solfg_        :meth:`~music21.pitch.Pitch.french`                Also .dutch, .italian, .spanish
strophe_      :meth:`~music21.text.assembleLyrics`               You probably won't need this though
synco_        To-Do                                              Will be "analysis.leeLHiggins" but not yet written -- low priority
tacet_        None                                               see `midireset` above; -i will not be supported
timebase_     None                                               Not needed.  stream.getElementsByOffset() will cover most uses
tonh_         :meth:`~music21.pitch.Pitch.german` 
trans_        `.transpose(Interval)`                             Note: :meth:`~music21.note.Note.transpose`, Stream: :meth:`~music21.stream.Stream.transpose`, etc
urrhythm_     To-Do                                              will be "`analysis.JohnsonLaird.urrhythm(Stream)`" but not yet written -- low priority
veritas_      None                                               Not needed.  use `import md5` or other checksum files
vox_          None                                               `len(Chord.pitches())` works for a chord.  Stream has many methods for performing this function.
xdelta_       None                                               Not needed.  Use `stream[i+1].property - stream[i].property` for similar effects.
yank_         "if"
ydelta_       None                                               Not needed.
============  =================================================  =========================================================================================================================================================================

.. _assemble: http://www.music-cog.ohio-state.edu/Humdrum/commands/assemble.html
.. _census: http://www.music-cog.ohio-state.edu/Humdrum/commands/census.html
.. _cents: http://www.music-cog.ohio-state.edu/Humdrum/commands/cents.html
.. _cleave: http://www.music-cog.ohio-state.edu/Humdrum/commands/cleave.html
.. _context: http://www.music-cog.ohio-state.edu/Humdrum/commands/context.html
.. _correl: http://www.music-cog.ohio-state.edu/Humdrum/commands/correl.html
.. _deg: http://www.music-cog.ohio-state.edu/Humdrum/commands/deg.html
.. _degree: http://www.music-cog.ohio-state.edu/Humdrum/commands/degree.html
.. _diss: http://www.music-cog.ohio-state.edu/Humdrum/commands/diss.html
.. _ditto: http://www.music-cog.ohio-state.edu/Humdrum/commands/ditto.html
.. _encode: http://www.music-cog.ohio-state.edu/Humdrum/commands/encode.html
.. _extract: http://www.music-cog.ohio-state.edu/Humdrum/commands/extract.html
.. _fields: http://www.music-cog.ohio-state.edu/Humdrum/commands/fields.html
.. _fin2hum: http://www.music-cog.ohio-state.edu/Humdrum/commands/fin2hum.html
.. _freq: http://www.music-cog.ohio-state.edu/Humdrum/commands/freq.html
.. _hint: http://www.music-cog.ohio-state.edu/Humdrum/commands/hint.html
.. _hum2fin: http://www.music-cog.ohio-state.edu/Humdrum/commands/hum2fin.html
.. _humdrum: http://www.music-cog.ohio-state.edu/Humdrum/commands/humdrum.html
.. _humsed: http://www.music-cog.ohio-state.edu/Humdrum/commands/humsed.html
.. _humver: http://www.music-cog.ohio-state.edu/Humdrum/commands/humver.html
.. _infot: http://www.music-cog.ohio-state.edu/Humdrum/commands/infot.html
.. _iv: http://www.music-cog.ohio-state.edu/Humdrum/commands/iv.html
.. _kern: http://www.music-cog.ohio-state.edu/Humdrum/commands/kern.html
.. _key: http://www.music-cog.ohio-state.edu/Humdrum/commands/key.html
.. _melac: http://www.music-cog.ohio-state.edu/Humdrum/commands/melac.html
.. _metpos: http://www.music-cog.ohio-state.edu/Humdrum/commands/metpos.html
.. _midi: http://www.music-cog.ohio-state.edu/Humdrum/commands/midi.html
.. _midireset: http://www.music-cog.ohio-state.edu/Humdrum/commands/midireset.html
.. _mint: http://www.music-cog.ohio-state.edu/Humdrum/commands/mint.html
.. _nf: http://www.music-cog.ohio-state.edu/Humdrum/commands/nf.html
.. _num: http://www.music-cog.ohio-state.edu/Humdrum/commands/num.html
.. _patt: http://www.music-cog.ohio-state.edu/Humdrum/commands/patt.html
.. _pattern: http://www.music-cog.ohio-state.edu/Humdrum/commands/pattern.html
.. _pc: http://www.music-cog.ohio-state.edu/Humdrum/commands/pc.html
.. _pcset: http://www.music-cog.ohio-state.edu/Humdrum/commands/pcset.html
.. _perform: http://www.music-cog.ohio-state.edu/Humdrum/commands/perform.html
.. _pf: http://www.music-cog.ohio-state.edu/Humdrum/commands/pf.html
.. _pitch: http://www.music-cog.ohio-state.edu/Humdrum/commands/pitch.html
.. _proof: http://www.music-cog.ohio-state.edu/Humdrum/commands/proof.html
.. _recode: http://www.music-cog.ohio-state.edu/Humdrum/commands/recode.html
.. _record: http://www.music-cog.ohio-state.edu/Humdrum/commands/record.html
.. _regexp: http://www.music-cog.ohio-state.edu/Humdrum/commands/regexp.html
.. _reihe: http://www.music-cog.ohio-state.edu/Humdrum/commands/reihe.html
.. _rend: http://www.music-cog.ohio-state.edu/Humdrum/commands/rend.html
.. _rid: http://www.music-cog.ohio-state.edu/Humdrum/commands/rid.html
.. _scramble: http://www.music-cog.ohio-state.edu/Humdrum/commands/scramble.html
.. _semits: http://www.music-cog.ohio-state.edu/Humdrum/commands/semits.html
.. _simil: http://www.music-cog.ohio-state.edu/Humdrum/commands/simil.html
.. _smf: http://www.music-cog.ohio-state.edu/Humdrum/commands/smf.html
.. _solfa: http://www.music-cog.ohio-state.edu/Humdrum/commands/solfa.html
.. _solfg: http://www.music-cog.ohio-state.edu/Humdrum/commands/solfg.html
.. _strophe: http://www.music-cog.ohio-state.edu/Humdrum/commands/strophe.html
.. _synco: http://www.music-cog.ohio-state.edu/Humdrum/commands/synco.html
.. _tacet: http://www.music-cog.ohio-state.edu/Humdrum/commands/tacet.html
.. _timebase: http://www.music-cog.ohio-state.edu/Humdrum/commands/timebase.html
.. _tonh: http://www.music-cog.ohio-state.edu/Humdrum/commands/tonh.html
.. _trans: http://www.music-cog.ohio-state.edu/Humdrum/commands/trans.html
.. _urrhythm: http://www.music-cog.ohio-state.edu/Humdrum/commands/urrhythm.html
.. _veritas: http://www.music-cog.ohio-state.edu/Humdrum/commands/veritas.html
.. _vox: http://www.music-cog.ohio-state.edu/Humdrum/commands/vox.html
.. _xdelta: http://www.music-cog.ohio-state.edu/Humdrum/commands/xdelta.html
.. _yank: http://www.music-cog.ohio-state.edu/Humdrum/commands/yank.html
.. _ydelta: http://www.music-cog.ohio-state.edu/Humdrum/commands/ydelta.html
'''

__ALL__ = ['spineParser', 'instruments', 'testFiles']

import sys

from music21.humdrum import instruments
from music21.humdrum import spineParser
from music21.humdrum import testFiles


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

