# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         humdrum.__init__.py
# Purpose:      base module for emulating Humdrum functionality in music21
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
# pylint: disable=line-too-long
# noinspection SpellCheckingInspection
'''
Files in this package deal specifically with making life easier for
people who have previously used humdrum or need to import
humdrum data (in spines, etc.) into music21.


Humdrum programs and their closest music21 equivalents:


============  =================================================  =========================================================================================================================================================================
Humdrum       music21                                            notes
============  =================================================  =========================================================================================================================================================================
assemble_     Not needed                                         Use python commands to unite objects and `s.insert(0, p)` to put a part at the beginning of a multipart score.
census_       Not needed                                         Use python to create census equivalents
cents_        `interval.ChromaticInterval.cents`
cleave_       Not needed                                         kern specific, not needed
context_      Not needed                                         Use object.next and object.prev to get some context for many objects and :meth:`~music21.base.Music21Object.getContextByClass` to find the most recent object of a given type
correl_       Not needed                                         Use numpy.corrcoef() or other, more sophisticated code
deg_          Several tools, see Notes                           Closest is :meth:`~music21.scale.Scale.getScaleDegreeAndAccidentalFromPitch`. See also `stream.Stream.analyze('key')`
degree_       see above for "`deg`"
diss_         Spectral analysis.  Out of scope for m21           Would be "analysis.kkdiss" for Kameoka and Kuriyagawa.
ditto_        see Notes                                          :meth:`~music21.stream.Stream.chordify` and the offsetTree objects accomplish similar things. Use `copy.copy(object)` or `copy.deepcopy(object)` to get another copy of an object
encode_       `midi.(severaltools)`                              Multifunction humdrum program.  See the midi directory for some replacements.  Or for simple conversion, `converter.parse` and `show('midi')` do this automatically
extract_      Not needed                                         Use python commands to extract objects with certain properties
fields_       Not needed
fin2hum_      `music21.converter.parse` (filename)               Enigma Transport Format did not take off and is rarely used. Software to convert Enigma to MusicXML is available from recordare
freq_         see :meth:`~music21.pitch.Pitch.frequency`
hint_         see Notes                                          :meth:`~music21.stream.Stream.attachIntervalsBetweenStreams` See alpha.trecento.capua demo to show how it can be done.
hum2fin_      `.write('musicxml')`                               Writes to musicXML.  A music21 to Enigma converter will not be written (obsolete format)
humdrum_      Not needed                                         The `spineParser` will report errors when parsing.
humsed_       Not needed
humver_       Not needed
infot_        Not needed                                         Use general purpose python information theory models
iv_           :meth:`~music21.chord.Chord.intervalVector`
kern_         None                                               Output to Humdrum is not currently supported
key_          :meth:`~music21.stream.Stream.analyze` ('key')
melac_        see Notes                                          :meth:`~music21.analysis.metrical.thomassenMelodicAccent`.  incorporates humdrum additions for giving accent of the first and last notes.
metpos_       `1 / obj.beatStrength()`                           the beatStrength of an object is essentially something similar but inverted.  beatStrength handles irregular meters.
midi_         `.show('midi')`
midireset_    None                                               Not needed for now because we do not write directly to MIDI.  A midi.allOff() will be needed for direct midi access...
mint_         `interval.Interval(note1, note2)`                  Or :meth:`~music21.stream.Stream.melodicIntervals`
nf_           :meth:`~music21.chord.Chord.normalOrder`           Also :meth:`~music21.chord.Chord.primeForm`, :meth:`~music21.chord.Chord.intervalVector`, :meth:`~music21.chord.Chord.forteClass`, :meth:`~music21.chord.Chord.getZRelation` etc.
num_          Not needed                                         try: `for i in range(len(s.recurse().getElementsByClass(X)))` etc.
patt_         `search.*`                                         see also, for instance, trecento.find_trecento_fragments for an example of a pattern searching module
pattern_      `search.*`                                         see patt above
pc_           :meth:`~music21.pitch.Pitch.pitchClass`
pcset_        see `Pitch.*` and `Chord.*`                        Pitch.pitchClass and pitchClassString, Chord.normalOrder, .primeForm, .intervalVector, etc.
perform_      `.show('midi')`
pf_           :meth:`~music21.chord.Chord.primeForm`             Also :meth:`~music21.chord.Chord.normalOrder` etc.
pitch_        :meth:`~music21.pitch.Pitch.nameWithOctave`
proof_        Not needed                                         See `humdrum` command above; However, something like this could be useful for each encoding format.
recode_       `"if"`
record_       via music21j                                       Not yet determined if it is a good idea to record directly to music21 within music21 -- our MIDI to music21 converter should suffice.  But note that audioSearch.recording gives recording transcription abilities
regexp_       Not needed                                         Use `re` module in Python core, not music21
reihe_        :class:`~music21.serial.TwelveToneRow`
rend_         Not needed                                         Object properties perform the same function.
rid_          Not needed                                         Use :meth:`~music21.stream.Stream.getElementsByClass` or :meth:`~music21.stream.Stream.getElementsNotOfClass` instead
scramble_     Not needed                                         Use random module in Python core, not music21.  However, see composition tools for some sophisticated scrambling methods
semits_       see Notes                                          :meth:`~music21.pitch.Pitch.ps`, :meth:`~music21.pitch.Pitch.p.midiNote` or :meth:`~music21.interval.Interval.chromatic`.  See also :class:`music21.pitch.Accidental`, esp. the `.alter` property.
simil_        Many implementations
smf_          `.write('midi')`                                   See midi above
solfa_        :meth:`~music21.scale.ConcreteScale.solfeg`        Use variant='humdrum' to get exact humdrum solfeg syllables
solfg_        :meth:`~music21.pitch.Pitch.french`                Also .dutch, .italian, .spanish
strophe_      :meth:`~music21.text.assembleLyrics`               You probably won't need this though
synco_        To-Do                                              Will be "analysis.leeLHiggins" but not yet written -- low priority
tacet_        Not needed                                         see `midireset` above; -i will not be supported
timebase_     Not needed                                         stream.getElementsByOffset() will cover most uses
tonh_         :meth:`~music21.pitch.Pitch.german`
trans_        `.transpose(Interval)`                             Note: :meth:`~music21.note.Note.transpose`, Stream: :meth:`~music21.stream.Stream.transpose`, etc
urrhythm_     To-Do                                              will be "`analysis.jl_urrhythm(Stream)`" but not yet written -- low priority
veritas_      Not needed                                         Use `import md5` or other checksum files
vox_          Not needed                                         `len(Chord.pitches())` works for a chord.  Stream has many methods for performing this function.
xdelta_       Not needed                                         Use `stream[i + 1].property - stream[i].property` for similar effects.
yank_         "if"
ydelta_       Not needed
============  =================================================  =========================================================================================================================================================================

.. _assemble: https://www.humdrum.org/Humdrum/commands/assemble.html
.. _census: https://www.humdrum.org/Humdrum/commands/census.html
.. _cents: https://www.humdrum.org/Humdrum/commands/cents.html
.. _cleave: https://www.humdrum.org/Humdrum/commands/cleave.html
.. _context: https://www.humdrum.org/Humdrum/commands/context.html
.. _correl: https://www.humdrum.org/Humdrum/commands/correl.html
.. _deg: https://www.humdrum.org/Humdrum/commands/deg.html
.. _degree: https://www.humdrum.org/Humdrum/commands/degree.html
.. _diss: https://www.humdrum.org/Humdrum/commands/diss.html
.. _ditto: https://www.humdrum.org/Humdrum/commands/ditto.html
.. _encode: https://www.humdrum.org/Humdrum/commands/encode.html
.. _extract: https://www.humdrum.org/Humdrum/commands/extract.html
.. _fields: https://www.humdrum.org/Humdrum/commands/fields.html
.. _fin2hum: https://www.humdrum.org/Humdrum/commands/fin2hum.html
.. _freq: https://www.humdrum.org/Humdrum/commands/freq.html
.. _hint: https://www.humdrum.org/Humdrum/commands/hint.html
.. _hum2fin: https://www.humdrum.org/Humdrum/commands/hum2fin.html
.. _humdrum: https://www.humdrum.org/Humdrum/commands/humdrum.html
.. _humsed: https://www.humdrum.org/Humdrum/commands/humsed.html
.. _humver: https://www.humdrum.org/Humdrum/commands/humver.html
.. _infot: https://www.humdrum.org/Humdrum/commands/infot.html
.. _iv: https://www.humdrum.org/Humdrum/commands/iv.html
.. _kern: https://www.humdrum.org/Humdrum/commands/kern.html
.. _key: https://www.humdrum.org/Humdrum/commands/key.html
.. _melac: https://www.humdrum.org/Humdrum/commands/melac.html
.. _metpos: https://www.humdrum.org/Humdrum/commands/metpos.html
.. _midi: https://www.humdrum.org/Humdrum/commands/midi.html
.. _midireset: https://www.humdrum.org/Humdrum/commands/midireset.html
.. _mint: https://www.humdrum.org/Humdrum/commands/mint.html
.. _nf: https://www.humdrum.org/Humdrum/commands/nf.html
.. _num: https://www.humdrum.org/Humdrum/commands/num.html
.. _patt: https://www.humdrum.org/Humdrum/commands/patt.html
.. _pattern: https://www.humdrum.org/Humdrum/commands/pattern.html
.. _pc: https://www.humdrum.org/Humdrum/commands/pc.html
.. _pcset: https://www.humdrum.org/Humdrum/commands/pcset.html
.. _perform: https://www.humdrum.org/Humdrum/commands/perform.html
.. _pf: https://www.humdrum.org/Humdrum/commands/pf.html
.. _pitch: https://www.humdrum.org/Humdrum/commands/pitch.html
.. _proof: https://www.humdrum.org/Humdrum/commands/proof.html
.. _recode: https://www.humdrum.org/Humdrum/commands/recode.html
.. _record: https://www.humdrum.org/Humdrum/commands/record.html
.. _regexp: https://www.humdrum.org/Humdrum/commands/regexp.html
.. _reihe: https://www.humdrum.org/Humdrum/commands/reihe.html
.. _rend: https://www.humdrum.org/Humdrum/commands/rend.html
.. _rid: https://www.humdrum.org/Humdrum/commands/rid.html
.. _scramble: https://www.humdrum.org/Humdrum/commands/scramble.html
.. _semits: https://www.humdrum.org/Humdrum/commands/semits.html
.. _simil: https://www.humdrum.org/Humdrum/commands/simil.html
.. _smf: https://www.humdrum.org/Humdrum/commands/smf.html
.. _solfa: https://www.humdrum.org/Humdrum/commands/solfa.html
.. _solfg: https://www.humdrum.org/Humdrum/commands/solfg.html
.. _strophe: https://www.humdrum.org/Humdrum/commands/strophe.html
.. _synco: https://www.humdrum.org/Humdrum/commands/synco.html
.. _tacet: https://www.humdrum.org/Humdrum/commands/tacet.html
.. _timebase: https://www.humdrum.org/Humdrum/commands/timebase.html
.. _tonh: https://www.humdrum.org/Humdrum/commands/tonh.html
.. _trans: https://www.humdrum.org/Humdrum/commands/trans.html
.. _urrhythm: https://www.humdrum.org/Humdrum/commands/urrhythm.html
.. _veritas: https://www.humdrum.org/Humdrum/commands/veritas.html
.. _vox: https://www.humdrum.org/Humdrum/commands/vox.html
.. _xdelta: https://www.humdrum.org/Humdrum/commands/xdelta.html
.. _yank: https://www.humdrum.org/Humdrum/commands/yank.html
.. _ydelta: https://www.humdrum.org/Humdrum/commands/ydelta.html
'''

__all__ = [
    'spineParser',
    'instruments',
    'testFiles',
]

from music21.humdrum import instruments
from music21.humdrum import spineParser
from music21.humdrum import testFiles

from music21.common.decorators import deprecated

@deprecated
def parseFile(filename):  # pragma: no cover
    '''
    shortcut to :class:`~music21.humdrum.spineParser.HumdrumFile`.
    Most users will call `converter.parse()` instead.

    Deprecated v6. -- call converter.parse() instead.  To be removed v.7
    '''
    hf = spineParser.HumdrumFile(filename)
    hf.parseFilename()
    return hf


@deprecated
def parseData(data):  # pragma: no cover
    '''
    shortcut to :class:`~music21.humdrum.spineParser.HumdrumDataCollection`.
    Most users will call `converter.parse()` instead.

    Deprecated v6. -- call converter.parse() instead.  To be removed v.7
    '''
    hdf = spineParser.HumdrumDataCollection(data)
    hdf.parse()
    return hdf

