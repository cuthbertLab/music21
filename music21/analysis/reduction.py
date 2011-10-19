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
from music21 import stream, note


from music21 import environment
_MOD = "analysis/reduction.py"
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class ReductiveEventException(Exception):
    pass


# as lyric, or as parameter
# 
# ::/p:g#/o:5/nh:f/ns:n/l:1/g:ursatz/v:1
# 
# p as pitch, else take top of note 
# o as octave
# nh as noteHead
# ns as note stem
# g as group: each group becomes a part
# v as voice

 
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

    def __init__(self, specification, note):
        self._specification = specification

        self._note = None # store a reference to the note this is attached to
        self._parameters = {}  
        # do parsing if possible
        self._parseSpecification(self._specification)
        self._note = note # keep a reference

    def __repr__(self):
        msg = []
        for key in self._parameterKeys.keys():
            attr = self._parameterKeys[key]
            if attr in self._parameters.keys(): # only show those defined
                msg.append(key)
                msg.append(':')
                msg.append(self._parameters[attr])
        if self._note is not None:
            msg.append(' of ')
            msg.append(repr(self._note))
        return '<music21.analysis.reduction.ReductiveNote %s>' % ''.join(msg)

    def _parseSpecification(self, spec):
        self._parameters = {} # always clear at start
        spec = spec.strip()
        spec = spec.replace(' ', '')
        if not spec.startswith(self._delimitValue+self._delimitValue):
            return # nothing to parse
        args = spec.split(self._delimitArg)
        for a in args:
            if self._delimitValue not in a: # as in the first one
                continue
            # as in the first one
            elif a == self._delimitValue + self._delimitValue: 
                continue
            print a
            candidateKey, value = a.split(self._delimitValue)
            candidateKey = candidateKey.strip()
            if candidateKey.lower() in self._parameterKeys.keys():
                attr = self._parameterKeys[candidateKey]
                self._parameters[attr] = value

    def isParsed(self):
        if len(self._parameters.keys()) == 0:
            return False
        return True


    def getNote(self):
        '''Produce a new note, a deep copy of the supplied note and with the specified modifications.
        '''
        if self._note.isChord:
            # need to permit specification by pitch
            if 'pitch' in self._parameters.keys():
                for sub in self._note: # iterate over compoinents
                    if p.name == sub.pitch.name:
                        # copy the component
                        n = copy.deepcopy(sub)
            else: # get first
                n = copy.deepcopy(self._note.pitches[0])
        else:
            n = copy.deepcopy(self._note)
        # always clear certain parameters
        n.lyrics = []

        if 'octave' in self._parameters.keys():
            n.pitch.octave = self._parameters['octave']

        if 'stemDirection' in self._parameters.keys():
            # TODO: process values to provide more compact representations
            # possibly do not NotRest
            n.stemDirection = self._parameters['stemDirection']
        else:        
            n.stemDirection = self._defaultParameters['stemDirection']

        return n

#-------------------------------------------------------------------------------
class ScoreReductionException(Exception):
    pass


class ScoreReduction(object):

    def __init__(self, *args, **keywords):

        # store a list of one or more reductions
        self._reductiveNotes = {}

        self._score = None



    def _extractReductionEvents(self, score):
        '''Remove and store all reductive events 
        Store in a dictionary where obj id is obj key
        '''
        # iterate overall notes, check all lyrics
        for n in score.flat.notes:
            if n.hasLyrics():
                for l in n.lyrics: # a list of Lyric objects
                    rn = ReductiveNote(l.text, n)
                    if rn.isParsed():
                        environLocal.pd(['adding reductive note', rn])
                        # use id as hash key
                        self._reductiveNotes[id(n)] = rn

    def _setScore(self, value):
        # TODO: check for non Stream
        if value.hasPartLikeStreams:
            self._score = value
        else: # assume a single stream
            s = stream.Score()
            s.insert(0, value)
            self._score = s
        # after setting the score, process all reductive events if found
        self._extractReductionEvents(self.score)
        
    def  _getScore(self):
        return self._score

    score = property(_getScore, _setScore, doc='''
        Get or set the Score.

        >>> from music21 import *
        >>> s = corpus.parse('bwv66.6')
        >>> sr = analysis.reduction.ScoreReduction()
        >>> sr.score = s

        ''')



    def _createReduction(self):
        s = stream.Score() 
    
        # create reductive parts
        # need to break by necessary parts, voices; for now, assume one
        a1 = self._score.parts[0].measureTemplate()
        a1Measures = a1.getElementsByClass('Measure')

        # look in all parts for tags to this analysis part
        for p in self._score.parts:
            for i, m in enumerate(p.getElementsByClass('Measure')):
                for n in m.flat.notes:
                    if id(n) in self._reductiveNotes.keys():
                        rn = self._reductiveNotes[id(n)]
                        environLocal.pd(['_createReduction(): found reductive note, rn', rn])
                        a1Measures[i].insert(n.getOffsetBySite(m), rn.getNote())

        # after gathering all parts, fill with rests
        for i, m in enumerate(a1.getElementsByClass('Measure')):
            m.makeRests(fillGaps=True, inPlace=True) 
            # hide all rests       
            if len(m.notes) is 0:
                r = note.Rest()
                # TODO: this is not getting pickup
                r.duration.quarterLength = a1Measures[
                                            i].barDuration.quarterLength
                m.append(r)         
            for r in m.getElementsByClass('Rest'):
                r.hideObjectOnPrint = True

        # add to score
        s.insert(0, a1)

        srcParts = [] # for bracket
        for p in self._score.parts:
            s.insert(0, p)
            srcParts.append(p) # store to brace

        return s

    def reduce(self, score=None):
        '''Given a score, populate this Score reduction 
        '''
        if score is not None:
            self.score = score
        if self.score is None: # if not set here or before
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
        s.parts[0].flat.notes[4].addLyric('::/o:6')

        sr = analysis.reduction.ScoreReduction()
        sr.score = s

        post = sr.reduce()
        self.assertEqual(len(post.parts[0].flat.notes), 1)
        #post.show()



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []



if __name__ == "__main__":
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof



