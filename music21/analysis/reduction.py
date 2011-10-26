# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         reduction.py
# Purpose:      Tools for creating a score reduction.
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import doctest, unittest
import copy



import music21 
from music21 import stream, note, expressions
from music21 import instrument
from music21 import pitch

from music21 import environment
_MOD = "analysis/reduction.py"
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class ReductiveEventException(Exception):
    pass


# as lyric, or as parameter
# 
# ::/p:g#/o:5/nh:f/ns:n/l:1/g:ursatz/v:1

 
class ReductiveNote(object):
    '''The extraction of an event from a score and specification of where and how it should be presented in a reductive score.

    A specification string, as well as Note, must be provided for parsing.
    '''
    _delimitValue = ':' # store the delimit string, must start with 2
    _delimitArg = '/'
    # map the abbreviation to the data key
    _parameterKeys = {
        'p':'pitch',
        'o':'octave',
        'nf':'noteheadFill',
        'sd':'stemDirection',
        'g':'group',
        'v':'voice',
        'ta':'textAbove', # text annotation
        'tb':'textBelow', # text annotation
        }
    _defaultParameters = {
        'pitch':None, # use notes, or if a chord take highest
        'octave':None, # use notes
        'noteheadFill':None, # use notes
        'stemDirection':'noStem',
        'group':None,
        'voice':None,
    }

    def __init__(self, specification, note, measureIndex, measureOffset):
        '''
        A specification must be created when access the Measure that the source note is found in. Storing the measure and index position provides significant performance optimization, as we do no have to search every note when generated the reduction. 

        The `measureIndex` is the index of measure where this is found, not
        the measure number. The `measureOffset` is the position in the measure
        specified by the index.
        '''
        self._specification = specification

        self._note = None # store a reference to the note this is attached to
        self._parameters = {}  
        # do parsing if possible
        self._isParsed = False 
        self._parseSpecification(self._specification)
        self._note = note # keep a reference
        self.measureIndex = measureIndex
        self.measureOffset = measureOffset

    def __repr__(self):
        msg = []
        for key in self._parameterKeys.keys():
            attr = self._parameterKeys[key]
            if attr in self._parameters.keys(): # only show those defined
                if self._parameters[attr] is not None:
                    msg.append(key)
                    msg.append(':')
                    msg.append(self._parameters[attr])
        if self._note is not None:
            msg.append(' of ')
            msg.append(repr(self._note))
        return '<music21.analysis.reduction.ReductiveNote %s>' % ''.join(msg)

    def __getitem__(self, key):
        return self._parameters[key]

    def _parseSpecification(self, spec):
        # start with the defaults
        self._parameters = copy.deepcopy(self._defaultParameters)
        spec = spec.strip()
        #spec = spec.replace(' ', '')
        if not spec.startswith(self._delimitValue+self._delimitValue):
            return # nothing to parse
        args = spec.split(self._delimitArg)
        for a in args[1:]: # skip the first arg, as it is just delmiiter
            # if no delimit arg, it cannot be parsed
            if self._delimitValue not in a: 
                continue
            candidateKey, value = a.split(self._delimitValue)
            candidateKey = candidateKey.strip()
            value = value.strip()
            if candidateKey.lower() in self._parameterKeys.keys():
                attr = self._parameterKeys[candidateKey]
                self._parameters[attr] = value
        self._isParsed = True

    def isParsed(self):
        return self._isParsed

    def getNoteAndTextExpression(self):
        '''Produce a new note, a deep copy of the supplied note and with the specified modifications.
        '''
        if self._note.isChord:
            # need to permit specification by pitch
            if 'pitch' in self._parameters.keys():
                p = pitch.Pitch(self._parameters['pitch'])
                for sub in self._note: # iterate over compoinents
                    if p.name == sub.pitch.name:
                        # copy the component
                        n = copy.deepcopy(sub)
            else: # get first, or get entire chord?
                #n = copy.deepcopy(self._note.pitches[0])
                n = copy.deepcopy(self._note.pitches[0])
        else:
            n = copy.deepcopy(self._note)
        # always clear certain parameters
        n.lyrics = []
        te = None

        if 'octave' in self._parameters.keys():
            if self._parameters['octave'] is not None:
                n.pitch.octave = self._parameters['octave']
        if 'stemDirection' in self._parameters.keys():
            n.stemDirection = self._parameters['stemDirection']
        if 'noteheadFill' in self._parameters.keys():
            if self._parameters['noteheadFill'] is not None:
                n.noteheadFill = self._parameters['noteheadFill']
        if 'textBelow' in self._parameters.keys():
            n.addLyric(self._parameters['textBelow'])
        if 'textAbove' in self._parameters.keys():
            te = expressions.TextExpression(self._parameters['textAbove'])
        return n, te


#-------------------------------------------------------------------------------
class ScoreReductionException(Exception):
    pass


class ScoreReduction(object):
    def __init__(self, *args, **keywords):
        # store a list of one or more reductions
        self._reductiveNotes = {}
        self._reductiveVoices = []
        self._reductiveGroups = []

        # store the source score
        self._score = None
        self._chordReduction = None  # store a chordal reduction of available


    def _setScore(self, value):
        if 'Stream' not in value.classes:
            raise ScoreReductionException('cannot set a non Stream')
        if value.hasPartLikeStreams:
            # make a local copy
            self._score = copy.deepcopy(value)
        else: # assume a single stream, place in a Score
            s = stream.Score()
            s.insert(0, copy.deepcopy(value))
            self._score = s
        
    def  _getScore(self):
        return self._score

    score = property(_getScore, _setScore, doc='''
        Get or set the Score. Setting the score set a deepcopy of the score; the score set here will not be altered.

        >>> from music21 import *
        >>> s = corpus.parse('bwv66.6')
        >>> sr = analysis.reduction.ScoreReduction()
        >>> sr.score = s
        ''')


    def _setChordReduction(self, value):
        if 'Stream' not in value.classes:
            raise ScoreReductionException('cannot set a non Stream')
        if value.hasPartLikeStreams():
            # make a local copy
            self._chordReduction = copy.deepcopy(value)
        else: # assume a single stream, place in a Score
            s = stream.Score()
            s.insert(0, copy.deepcopy(value))
            self._chordReduction = s
        
    def  _getChordReduction(self):
        return self._chordReduction

    chordReduction = property(_getChordReduction, _setChordReduction, doc='''
        Get or set a Chord reduction as a Stream or Score. Setting the this values set a deepcopy of the reduction; the reduction set here will not be altered.
        ''')



    def _extractReductionEvents(self, score, removeAfterParsing=True):
        '''Remove and store all reductive events 
        Store in a dictionary where obj id is obj key
        '''
        if score is None:
            return
        # iterate overall notes, check all lyrics
        for p in score.parts:
            for i, m in enumerate(p.getElementsByClass('Measure')):
                for n in m.flat.notes:
                    if n.hasLyrics():
                        removalIndices = []
                        # a list of Lyric objects
                        for k, l in enumerate(n.lyrics): 
                            # store measure index
                            rn = ReductiveNote(l.text, n, i, 
                                                n.getOffsetBySite(m))
                            if rn.isParsed():
                                environLocal.pd(['parsing reductive note', rn])
                                # use id, lyric text as hash
                                key = str(id(n)) + l.text
                                self._reductiveNotes[key] = rn
                                removalIndices.append(k)
                        if removeAfterParsing:
                            for q in removalIndices:
                                # replace position in list with empty lyric
                                n.lyrics[q] = note.Lyric('') 

    def _parseReductiveNotes(self):
        self._reductiveNotes = {}
        self._extractReductionEvents(self._chordReduction)
        self._extractReductionEvents(self._score)
        for key, rn in self._reductiveNotes.items():
            if rn['group'] not in self._reductiveGroups: 
                self._reductiveGroups.append(rn['group'])
            if rn['voice'] not in self._reductiveVoices: 
                self._reductiveVoices.append(rn['voice'])
            # if we have None and a group, then we should just use that one
            # group; same with voices
            if (len(self._reductiveGroups) == 2 and None in 
                self._reductiveGroups):
                self._reductiveGroups.remove(None)
            # for now, sort all 
            environLocal.pd(['self._reductiveGroups', self._reductiveGroups])

            if (len(self._reductiveVoices) == 2 and None in 
                self._reductiveVoices):
                self._reductiveVoices.remove(None)


    def _createReduction(self):
        self._parseReductiveNotes()

        s = stream.Score() 
        # need to scan all tags 

        oneGroup = False
        if len(self._reductiveGroups) == 1:
            # if 1, can be None or a group name:
            oneGroup = True
        oneVoice = False
        if len(self._reductiveVoices) == 1:
            # if 1, can be None or a group name:
            oneVoice = True

        if self._score is not None:
            mTemplate = self._score.parts[0].measureTemplate()
        else:
            mTemplate = self._chordReduction.parts[0].measureTemplate()

        # for each defined reductive group
        for gName in self._reductiveGroups:
            # create reductive parts
            # need to break by necessary parts, voices; for now, assume one
            g = copy.deepcopy(mTemplate)
            g.id = gName
            inst = instrument.Instrument()
            inst.partName = gName
            g.insert(0, inst)
            gMeasures = g.getElementsByClass('Measure')
    
            # TODO: insert into note or chord
            for key, rn in self._reductiveNotes.items():
                if oneGroup or rn['group'] == gName:
                    environLocal.pd(['_createReduction(): found reductive note, rn', rn, 'group', gName])
                    gMeasure = gMeasures[rn.measureIndex]
                    if len(gMeasure.voices) == 0: # common setup routines
                        # if no voices, start by removing rests
                        gMeasure.removeByClass('Rest')
                        for vId in self._reductiveVoices:
                            v = stream.Voice()
                            v.id = vId
                            gMeasure.insert(0, v)
                    if oneVoice:
                        n, te = rn.getNoteAndTextExpression()
                        gMeasure.voices[0].insertIntoNoteOrChord(
                            rn.measureOffset, n)
                        # place the text expression in the Measure, not Voice
                        if te is not None:
                            gMeasure.voices[0].insert(rn.measureOffset, te)
                    else:
                        v = gMeasure.getElementById(rn['voice'])
                        if v is None: # just take the first
                            v = gMeasure.voices[0]
                        n, te = rn.getNoteAndTextExpression()
                        v.insertIntoNoteOrChord(rn.measureOffset, n)
                        if te is not None:
                            v.insert(rn.measureOffset, te)

            # after gathering all parts, fill with rests
            for i, m in enumerate(g.getElementsByClass('Measure')):

                # only make rests if there are notes in the measure
                for v in m.voices:
                    if len(v.flat.notes) > 0:
                        v.makeRests(fillGaps=True, inPlace=True) 
                m.flattenUnnecessaryVoices(inPlace=True)
                # hide all rests in all containers
                for r in m.flat.getElementsByClass('Rest'):
                    r.hideObjectOnPrint = True
                #m.show('t')

            # add to score
            s.insert(0, g)
            #g.show('t')

        if self._chordReduction is not None:
            for p in self._chordReduction.parts:
                s.insert(0, p)

        srcParts = [] # for bracket
        if self._score is not None:
            for p in self._score.parts:
                s.insert(0, p)
                srcParts.append(p) # store to brace
        return s

    def reduce(self):
        '''Given a score, populate this Score reduction 
        '''
        # if not set here or before
        if self.score is None and self.chordReduction is None: 
            raise ScoreReductionException('no score defined to reduce')

        return self._createReduction()





#-------------------------------------------------------------------------------    
class Test(unittest.TestCase):

    def runTest(self):
        pass


    def testExtractionA(self):
        from music21 import stream, analysis, note, corpus
        s = corpus.parse('bwv66.6')
        #s.show()
        s.parts[0].flat.notes[3].addLyric('test')
        s.parts[0].flat.notes[4].addLyric('::/o:6/tb:here')
        s.parts[3].flat.notes[2].addLyric('::/o:5/tb:fromBass')

        s.parts[1].flat.notes[7].addLyric('::/o:4/nf:no/g:Ursatz/ta:3 3 200')

        sr = analysis.reduction.ScoreReduction()
        sr.score = s

        post = sr.reduce()
        #post.show()
        #post.parts[0].show('t')
        self.assertEqual(len(post.parts[0].flat.notes), 3)
        #post.parts[0].show('t')

        match = [(e, e.offset, e.duration.quarterLength) for e in post.parts[0].getElementsByClass('Measure')[0:3].flat.notesAndRests]
        self.assertEqual(str(match), '[(<music21.note.Rest rest>, 0.0, 1.0), (<music21.note.Note F#>, 1.0, 1.0), (<music21.note.Rest rest>, 2.0, 1.0), (<music21.note.Note C#>, 3.0, 1.0), (<music21.note.Rest rest>, 5.0, 1.0), (<music21.note.Note G#>, 6.0, 1.0)]')

        # test that lyric is found
        self.assertEqual(post.parts[0].flat.notes[0].lyric, 'fromBass')


    def testExtractionB(self):
        from music21 import stream, analysis, note, corpus
        s = corpus.parse('bwv66.6')

        s.parts[0].flat.notes[4].addLyric('::/o:6/v:1/tb:s/g:Ursatz')
        s.parts[3].flat.notes[2].addLyric('::/o:5/v:2/tb:b')
        s.parts[2].flat.notes[3].addLyric('::/o:4/v:2/tb:t')
        s.parts[1].flat.notes[2].addLyric('::/o:4/v:2/tb:a')

        sr = analysis.reduction.ScoreReduction()
        sr.score = s.measures(0, 10)
        post = sr.reduce()
        match = [n for n in post.parts[0].flat.notes]
        self.assertEqual(str(match), '[<music21.note.Note F#>, <music21.chord.Chord B4 E4>, <music21.note.Note C#>]')

        
        #post.show()

    def testExtractionC(self):
        from music21 import stream, analysis, note, corpus
        # http://solomonsmusic.net/schenker.htm

        src = corpus.parse('bwv846')
        chords = src.flattenParts().makeChords(minimumWindowSize=2)

        chords.measure(1).notes[0].addLyric('::/p:e/o:5/ta:3/g:Ursatz')
        chords.measure(1).notes[0].addLyric('::/p:c/o:4/tb:I/g:Ursatz')

        chords.measure(1).notes[0].addLyric('::/p:e/o:5/ta:3/nf:no/g:Other')


        chords.measure(24).notes[0].addLyric('::/p:d/o:5/ta:2/g:Ursatz')

        chords.measure(35).notes[0].addLyric('::/p:c/o:5/ta:1/g:Ursatz')


        sr = analysis.reduction.ScoreReduction()
        sr.chordReduction = chords
        post = sr.reduce()
        #post.show()        


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []



if __name__ == "__main__":
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof



