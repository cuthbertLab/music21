# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         reduction.py
# Purpose:      Tools for creating a score reduction.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
Tools for generation reduction displays, showing a score and or a chord reduction, 
and one or more reductive representation lines.

Used by graph.PlotHorizontalBarWeighted()
'''


import unittest
import copy

from music21 import exceptions21

from music21 import stream, note, expressions
from music21 import instrument
from music21 import pitch
from music21 import common

from music21 import environment
_MOD = "analysis.reduction"
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class ReductiveEventException(exceptions21.Music21Exception):
    pass


# as lyric, or as parameter
# 
# ::/p:g#/o:5/nh:f/ns:n/l:1/g:ursatz/v:1

 
class ReductiveNote(object):
    '''
    The extraction of an event from a score and specification of where 
    and how it should be presented in a reductive score.

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

    def __init__(self, specification, inputNote, measureIndex, measureOffset):
        '''
        A specification must be created when access the Measure that the source note 
        is found in. Storing the measure and index position provides significant 
        performance optimization, as we do no have to search every note when generated the reduction. 

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
        self._note = inputNote # keep a reference
        self.measureIndex = measureIndex
        self.measureOffset = measureOffset

    def __repr__(self):
        msg = []
        for key in self._parameterKeys:
            attr = self._parameterKeys[key]
            if attr in self._parameters: # only show those defined
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
            if candidateKey.lower() in self._parameterKeys:
                attr = self._parameterKeys[candidateKey]
                self._parameters[attr] = value
        self._isParsed = True

    def isParsed(self):
        return self._isParsed

    def getNoteAndTextExpression(self):
        '''Produce a new note, a deep copy of the supplied note and with the specified modifications.
        '''
        n = None
        if self._note.isChord:
            # need to permit specification by pitch
            if 'pitch' in self._parameters:
                p = pitch.Pitch(self._parameters['pitch'])
                for sub in self._note: # iterate over components
                    if p.name.lower() == sub.pitch.name.lower():
                        # copy the component
                        n = copy.deepcopy(sub)
            else: # get first, or get entire chord?
                #n = copy.deepcopy(self._note.pitches[0])
                n = copy.deepcopy(self._note.pitches[0])
        else:
            n = copy.deepcopy(self._note)
        # always clear certain parameters
        if (n is None):
            raise ReductiveEventException('Could not find pitch, %r in self._note: %r' % (self._parameters['pitch'], self._note))
        n.lyrics = []
        n.tie = None
        n.expressions = []
        n.articulations = []
        n.duration.dots = 0 # set to zero
        if n.pitch.accidental is not None:
            n.pitch.accidental.displayStatus = True
        te = None

        if 'octave' in self._parameters:
            if self._parameters['octave'] is not None:
                n.pitch.octave = self._parameters['octave']
        if 'stemDirection' in self._parameters:
            n.stemDirection = self._parameters['stemDirection']
        if 'noteheadFill' in self._parameters:
            nhf = self._parameters['noteheadFill']
            if nhf is not None:
                if nhf == 'yes':
                    nhf = True
                elif nhf == 'no':
                    nhf = False
                n.noteheadFill = nhf
                #environLocal.printDebug(['set nothead fill:', n.noteheadFill])
        if 'textBelow' in self._parameters:
            n.addLyric(self._parameters['textBelow'])
        if 'textAbove' in self._parameters:
            te = expressions.TextExpression(self._parameters['textAbove'])
        return n, te


#-------------------------------------------------------------------------------
class ScoreReductionException(exceptions21.Music21Exception):
    pass


class ScoreReduction(object):
    '''
    An object to reduce a score.
    '''
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
        Get or set the Score. Setting the score set a deepcopy of the score; the score 
        set here will not be altered.
        
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
        Get or set a Chord reduction as a Stream or Score. Setting the this values 
        set a deepcopy of the reduction; the reduction set here will not be altered.
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
                            if m.hasElement(n):
                                offset = n.getOffsetBySite(m)
                            else: # its in a Voice
                                for v in m.voices:
                                    if v.hasElement(n):
                                        offset = n.getOffsetBySite(v)
                            rn = ReductiveNote(l.text, n, i, offset)
                            if rn.isParsed():
                                #environLocal.printDebug(['parsing reductive note', rn])
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
        for unused_key, rn in self._reductiveNotes.items():
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
            # environLocal.printDebug(['self._reductiveGroups', self._reductiveGroups])

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
#             for m in gMeasures._elements:
#                 print gName, m
#                 m.clef = clef.TrebleClef()
            # TODO: insert into note or chord
            for unused_key, rn in self._reductiveNotes.items():
                if oneGroup or rn['group'] == gName:
                    #environLocal.printDebug(['_createReduction(): found reductive note, rn', rn, 'group', gName])
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
                            gMeasure.insert(rn.measureOffset, te)
                    else:
                        v = gMeasure.getElementById(rn['voice'])
                        if v is None: # just take the first
                            v = gMeasure.voices[0]
                        n, te = rn.getNoteAndTextExpression()
                        v.insertIntoNoteOrChord(rn.measureOffset, n)
                        if te is not None:
                            gMeasure.insert(rn.measureOffset, te)

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
class PartReductionException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class PartReduction(object):
    '''
    A part reduction reduces a Score into on or more parts. 
    Parts are combined based on a part group dictionary. 
    Each resulting part is then segmented by an object. 
    This object is assigned as floating-point value.

    This reduction is designed to work with the GraphHorizontalBarWeighted and related Plot 
    subclasses.

    If the `fillByMeasure` parameter is True, and if measures are available, 
    each part will segment by Measure divisions, and look for the target activity only 
    once per Measure. 
    
    If more than one target is found in the Measure, values will be averaged. 
    
    If `fillByMeasure` is False, the part will be segmented by each Note. 

    The `segmentByTarget` parameter is True, segments, which may be Notes or Measures, 
    will be divided if necessary to show changes that occur over the duration of the 
    segment by a target object. 

    If the `normalizeByPart` parameter is True, each part will be normalized within 
    the range only of that part. If False, all parts will be normalized by the max 
    of all parts. The default is True. 

    If the `normalize` parameter is False, no normalization will take place. The default is True. 

    '''
    def __init__(self, srcScore=None, *args, **keywords):
        if srcScore is None:
            return
        if 'Score' not in srcScore.classes:
            raise PartReductionException('provided Stream must be Score')
        self._score = srcScore
        # an ordered list of dictionaries for 
        # part id, part color, and a list of Part objs
        self._partBundles = []
        # a dictionary of part id to a list of events
        self._eventSpans = {}

        # define how parts are grouped
        # a list of dictionaries, with keys for name, color, and a match list
        self._partGroups = None
        if 'partGroups' in keywords:
            self._partGroups = keywords['partGroups']

        self._fillByMeasure = True
        if 'fillByMeasure' in keywords:
            self._fillByMeasure = keywords['fillByMeasure']

        # if we re-partition if spans change
        self._segmentByTarget = True
        if 'segmentByTarget' in keywords:
            self._segmentByTarget = keywords['segmentByTarget']

        self._normalizeByPart = False # norm by all parts is default
        if 'normalizeByPart' in keywords:
            self._normalizeByPart = keywords['normalizeByPart']

        self._normalizeToggle = True
        if 'normalize' in keywords:
            self._normalizeToggle = keywords['normalize']

        # check that there are measures
        for p in self._score.parts:
            if not p.hasMeasures():
                self._fillByMeasure = False         
                #environLocal.printDebug(['overrdding fillByMeasure as no measures are defined'])
                break

    def _createPartBundles(self):
        '''
        Fill the _partBundles list with dictionaries, 
        each dictionary defining a name (part id or supplied), a color, and list 
        of Parts that match.
        '''
        self._partBundles = []
        if self._partGroups is not None:
            for d in self._partGroups: # a list of dictionaries
                name, pColor, matches = d['name'], d['color'], d['match']
                sub = []
                for p in self._score.parts:
                    #environLocal.printDebug(['_createPartBundles: part.id', p.id])
                    # if matches is None, use group name
                    if matches is None:
                        matches = [name]
                    for m in matches: # strings or instruments
                        if common.isStr(m):
                            if str(p.id).lower().find(m.lower()) >= 0:
                                sub.append(p)
                                break
                        # TODO: match if m is Instrument class
                if sub == []:
                    continue
                data = {'pGroupId':name, 'color':pColor, 'parts':sub}
                self._partBundles.append(data)
        else: # manually creates    
            for p in self._score.parts:
                # store one or more Parts associated with an id
                data = {'pGroupId':p.id, 'color':'#666666', 'parts':[p]}
                self._partBundles.append(data)

        # create flat representation of all parts in a bundle
        for partBundle in self._partBundles:
            if len(partBundle['parts']) == 1:
                partBundle['parts.flat'] = partBundle['parts'][0].flat
            else:
                # align all parts and flatten
                # this takes a flat presentation of all parts
                s = stream.Stream()
                for p in partBundle['parts']:
                    s.insert(0, p)
                partBundle['parts.flat'] = s.flat


    def _createEventSpans(self):
        # for each part group id key, store a list of events
        self._eventSpans = {}

        for partBundle in self._partBundles:
            pGroupId = partBundle['pGroupId']
            pColor = partBundle['color']
            parts = partBundle['parts']
            #print pGroupId
            dataEvents = []
            # combine multiple streams into a single
            eStart = None
            eEnd = None
            eLast = None

            # segmenting by measure if that measure contains notes
            # note that measures are not elided of activity is contiguous
            if self._fillByMeasure:    
                partMeasures = []
                for p in parts:
                    partMeasures.append(p.getElementsByClass('Measure'))
                #environLocal.printDebug(['partMeasures', partMeasures])
                # assuming that all parts have same number of measures
                # iterate over each measures
                # iLast = len(partMeasures[0]) - 1
                for i in range(len(partMeasures[0])):
                    active = False
                    # check for activity in any part in the part group
                    for p in partMeasures: # iter of parts containing measures
                        #print p, i, p[i], len(p[i].flat.notes)
                        if len(p[i].flat.notes) > 0:
                            active = True
                            break
                    #environLocal.printDebug([i, 'active', active])
                    if not active:
                        continue    
                    # get offset, or start, of this measure
                    e = partMeasures[0][i]                            
                    eStart = e.getOffsetBySite(partMeasures[0])
                    # use duration, not barDuration.quarterLength
                    # as want filled duration?        
                    eEnd = (eStart + e.barDuration.quarterLength)
                    ds = {'eStart':eStart, 'span':eEnd-eStart, 
                          'weight':None, 'color':pColor}
                    dataEvents.append(ds)

#                     if eStart is None and active:
#                         eStart = partMeasures[0][i].getOffsetBySite(
#                                  partMeasures[0])
#                     elif (eStart is not None and not active) or i >= iLast:
#                         if eStart is None: # nothing to do; just the last
#                             continue
#                         # if this is the last measure and it is active
#                         if (i >= iLast and active):
#                             eLast = partMeasures[0][i]                            
#                         # use duration, not barDuration.quarterLength
#                         # as want filled duration?
#                         eEnd = (eLast.getOffsetBySite(
#                                 partMeasures[0]) + 
#                                 eLast.barDuration.quarterLength)
#                         ds = {'eStart':eStart, 'span':eEnd-eStart, 
#                               'weight':None, 'color':pColor}
#                         dataEvents.append(ds)
#                         eStart = None
#                    eLast = partMeasures[0][i]

            # fill by alternative approach, based on activity of notes  
            # creates region for each contiguous span of notes
            # this is useful as it will handle overlaps and similar arrangments
            # TODO: this needs further testing
            else:
                # this takes a flat presentation of all parts, and then
                # finds any gaps in consecutive notes
                eSrc = partBundle['parts.flat']
                # a li=st, not a stream
                # a None in the resulting list designates a rest
                noteSrc = eSrc.findConsecutiveNotes()
                for i, e in enumerate(noteSrc): 
                    #environLocal.printDebug(['i, e', i, e])
                    # if this event is a rest, e is None
                    if e is None:
                        if eStart is None: # the first event is a rest
                            continue
                        else:
                            eEnd = eLast.getOffsetBySite(eSrc) + eLast.quarterLength
                        # create a temporary weight
                        ds = {'eStart':eStart, 'span':eEnd-eStart, 
                              'weight':None, 'color':pColor}
                        dataEvents.append(ds)
                        eStart = None
                    elif i >= len(noteSrc) - 1: # this is the last
                        if eStart is None: # the last event was was a rest
                            # this the start is the start of this event
                            eStart = e.getOffsetBySite(eSrc)
                        eEnd = e.getOffsetBySite(eSrc) + e.quarterLength
                        # create a temporary weight
                        ds = {'eStart':eStart, 'span':eEnd-eStart, 
                              'weight':None, 'color':pColor}
                        dataEvents.append(ds)
                        eStart = None
                    else:
                        if eStart is None:
                            eStart = e.getOffsetBySite(eSrc)
                        eLast = e
            #environLocal.printDebug(['dataEvents', dataEvents])
            self._eventSpans[pGroupId] = dataEvents


    def _getValueForSpan(self, target='Dynamic', splitSpans=True, 
        targetToWeight=None):
        '''
        For each span, determine the measured parameter value. This is translated 
        as the height of the bar graph.

        If `splitSpans` is True, a span will be split of the target changes over the span. 
        Otherwise, Spans will be averaged. This is the `segmentByTarget` parameter. 

        The `targetToWeight` parameter is a function that takes a list or Stream of objects 
        (of the class specified by `target`) and returns a single floating-point value.
        ''' 
        # this temporary function only works with dynamics
        def _dynamicToWeight(targets):
            # permit a stream
            if hasattr(targets, 'isStream') and targets.isStream:
                pass
            elif not common.isIterable(targets):
                targets = [targets]
            summation = 0
            for e in targets: # a Stream
                summation += e.volumeScalar # for dynamics
            return summation / float(len(target))

        # supply function to convert one or more targets to number
        if targetToWeight is None:
            targetToWeight = _dynamicToWeight

        if not splitSpans: # this is segmentByTarget
            for partBundle in self._partBundles:
                flatRef = partBundle['parts.flat']
                for ds in self._eventSpans[partBundle['pGroupId']]:
                    # for each event span, find the targeted object
                    offsetStart = ds['eStart']
                    offsetEnd = offsetStart + ds['span']
                    match = flatRef.getElementsByOffset(offsetStart, offsetEnd,
                        includeEndBoundary=False, mustFinishInSpan=False, 
                        mustBeginInSpan=True).getElementsByClass(target)
                    if len(match) == 0:
                        w = None
                    else:
                        w = targetToWeight(match)
                    #environLocal.printDebug(['segment weight', w])
                    ds['weight'] = w
        else:
            for partBundle in self._partBundles:
                finalBundle = []
                flatRef = partBundle['parts.flat']
                # get each span
                for ds in self._eventSpans[partBundle['pGroupId']]:
                    offsetStart = ds['eStart']
                    offsetEnd = offsetStart + ds['span']
                    # get all targets within the contiguous region
                    # e.g., Dynamics objects
                    match = flatRef.getElementsByOffset(offsetStart, offsetEnd,
                        includeEndBoundary=True, mustFinishInSpan=False, 
                        mustBeginInSpan=True).getElementsByClass(target)
                    #environLocal.printDebug(['matched elements', target, match])
                    # extend duration of all found dynamics
                    match.extendDuration(target, inPlace=True)
                    #match.show('t')
                    dsFirst = copy.deepcopy(ds)
                    if len(match) == 0:
                        # weight is not known
                        finalBundle.append(dsFirst)
                        continue
                    # create new spans for each target in this segment
                    for i, t in enumerate(match):
                        targetStart = t.getOffsetBySite(flatRef)
                        # can use extended duration
                        targetSpan = t.duration.quarterLength
                        # if dur of target is greater tn this span
                        # end at this span
                        if targetStart + targetSpan > offsetEnd:
                            targetSpan = offsetEnd - targetStart
                        # if we have the last matched target, it will 
                        # have zero duration, as there is no following
                        # thus, span needs to be distance to end of regions
                        if targetSpan <= 0.001: 
                            targetSpan = offsetEnd - targetStart
                        #environLocal.printDebug([t, 'targetSpan', targetSpan, 
                        #  'offsetEnd', offsetEnd, "ds['span']", ds['span']])

                        if i==0 and ds['eStart'] == targetStart:
                            # the target start at the same position
                            # as the start of this existing span
                            #dsFirst['eStart'] = targetStart
                            dsFirst['span'] = targetSpan
                            dsFirst['weight'] = targetToWeight(t)
                            finalBundle.append(dsFirst)
                        elif t==0 and ds['eStart'] != targetStart: 
                            # add two, one for the empty region, one for target
                            # adjust span of first; weight is not knonw
                            # (hangs over from last)
                            dsFirst['span'] = targetStart - offsetStart                            
                            finalBundle.append(dsFirst)
                            dsNext = copy.deepcopy(ds)
                            dsNext['eStart'] = targetStart
                            dsNext['span'] = targetSpan
                            dsNext['weight'] = targetToWeight(t)
                            finalBundle.append(dsNext)
                        else: # for all other cases, create segment for each 
                            dsNext = copy.deepcopy(ds)
                            dsNext['eStart'] = targetStart
                            dsNext['span'] = targetSpan
                            dsNext['weight'] = targetToWeight(t)
                            finalBundle.append(dsNext)
                # after iterating all ds spans, reassign 
                self._eventSpans[partBundle['pGroupId']] = finalBundle

    def _extendSpans(self):
        '''
        Extend a the value of a target parameter to the next boundary. 
        An undefined boundary will wave as its weight None. 
        ''' 
#         environLocal.printDebug(['_extendSpans: pre'])    
#         for partBundle in self._partBundles:
#             for i, ds in enumerate(self._eventSpans[partBundle['pGroupId']]):
#                 print ds

        minValue = 0.01 # for error conditions
        for partBundle in self._partBundles:            
            lastWeight = None
            for i, ds in enumerate(self._eventSpans[partBundle['pGroupId']]):
                if i == 0: # cannot extend first
                    if ds['weight'] is None: # this is an error in the rep
                        ds['weight'] = minValue
                        #environLocal.printDebug(['cannnot extend a weight: no previous weight defined'])
                    else:
                        lastWeight = ds['weight']
                else: # not first
                    if ds['weight'] is not None:
                        lastWeight = ds['weight']
                    elif lastWeight is not None: # its None, use last
                        ds['weight'] = lastWeight
                    # do not have a list; mist set to min
                    elif ds['weight'] is None and lastWeight is None: 
                        ds['weight'] = minValue
                        #environLocal.printDebug(['cannnot extend a weight: no previous weight defined'])
#         environLocal.printDebug(['_extendSpans: post'])    
#         for partBundle in self._partBundles:
#             for i, ds in enumerate(self._eventSpans[partBundle['pGroupId']]):
#                 print ds

    def _normalize(self, byPart=False):
        '''Normalize, either within each Part, or for all parts
        ''' 
        partMaxRef = {}
        for partBundle in self._partBundles:
            partMax = 0
            for ds in self._eventSpans[partBundle['pGroupId']]:
                if ds['weight'] > partMax:
                    partMax = ds['weight']
            partMaxRef[partBundle['pGroupId']] = partMax

        maxOfMax = max([e for e in partMaxRef.values()])        

        for partBundle in self._partBundles:
            for ds in self._eventSpans[partBundle['pGroupId']]:
                # weight is now fraction of the max for that part
                if byPart:
                    bestMax = partMaxRef[partBundle['pGroupId']]
                else:
                    bestMax = maxOfMax
                if bestMax != 0:
                    ds['weight'] = (ds['weight'] / bestMax)
                else:
                    ds['weight'] = 1 # error?

    def process(self):
        '''Core processing routines.
        '''
        self._createPartBundles()
        self._createEventSpans()
        self._getValueForSpan(splitSpans=self._segmentByTarget)
        self._extendSpans()
        if self._normalizeToggle:
            self._normalize(byPart=self._normalizeByPart)



    def getGraphHorizontalBarWeightedData(self):
        '''
        Get all data organized into bar span specifications. 
        '''
#         data =  [
#         ('Violins',  [(3, 5, 1, '#fff000'), (1, 12, .2, '#3ff203',.1, 1)]  ), 
#         ('Celli',    [(2, 7, .2, '#0ff302'), (10, 3, .6, '#ff0000', 1)]  ), ]
        data = []
        # iterate over part bundles to get order
        for partBundle in self._partBundles:
            #print partBundle
            dataList = []
            for ds in self._eventSpans[partBundle['pGroupId']]:
                # data format here is set by the graphing routine
                dataList.append([ds['eStart'], ds['span'], ds['weight'], ds['color']])
            data.append((partBundle['pGroupId'], dataList))
        return data

#-------------------------------------------------------------------------------    
class Test(unittest.TestCase):

    def runTest(self):
        pass


    def testExtractionA(self):
        from music21 import analysis, corpus
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

        match = [(e, e.offset, e.duration.quarterLength) 
                  for e in post.parts[0].getElementsByClass('Measure')[0:3].flat.notesAndRests]
        self.assertEqual(str(match), 
                         '''[(<music21.note.Rest rest>, 0.0, 1.0), (<music21.note.Note F#>, 1.0, 1.0), (<music21.note.Rest rest>, 2.0, 1.0), (<music21.note.Note C#>, 3.0, 1.0), (<music21.note.Rest rest>, 5.0, 1.0), (<music21.note.Note G#>, 6.0, 1.0)]''')

        # test that lyric is found
        self.assertEqual(post.parts[0].flat.notes[0].lyric, 'fromBass')


    def testExtractionB(self):
        from music21 import analysis, corpus
        s = corpus.parse('bwv66.6')

        s.parts[0].flat.notes[4].addLyric('::/o:6/v:1/tb:s/g:Ursatz')
        s.parts[3].flat.notes[2].addLyric('::/o:5/v:2/tb:b')
        s.parts[2].flat.notes[3].addLyric('::/o:4/v:2/tb:t')
        s.parts[1].flat.notes[2].addLyric('::/o:4/v:2/tb:a')

        sr = analysis.reduction.ScoreReduction()
        extract = s.measures(0, 10)
        #extract.show()
        sr.score = extract
        #sr.score = s
        post = sr.reduce()
        #post.show()
        self.assertEqual(len(post.parts), 5)
        match = [n for n in post.parts[0].flat.notes]
        self.assertEqual(len(match), 3)

        
        #post.show()

    def testExtractionC(self):
        from music21 import analysis, corpus
        # http://solomonsmusic.net/schenker.htm
        # shows extracting an Ursatz line
        
        # BACH pre;ide !, WTC

        src = corpus.parse('bwv846')
        chords = src.flattenParts().makeChords(minimumWindowSize=4, 
                                    makeRests=False)
        for c in chords.flat.notes:
            c.quarterLength = 4
        for m in chords.getElementsByClass('Measure'):
            m.clef = m.bestClef()
        
        chords.measure(1).notes[0].addLyric('::/p:e/o:5/nf:no/ta:3/g:Ursatz')
        chords.measure(1).notes[0].addLyric('::/p:c/o:4/nf:no/tb:I')
        
        chords.measure(24).notes[0].addLyric('::/p:d/o:5/nf:no/ta:2')
        chords.measure(24).notes[0].addLyric('::/p:g/o:3/nf:no/tb:V')
        
        chords.measure(30).notes[0].addLyric('::/p:f/o:4/tb:7')
        
        chords.measure(34).notes[0].addLyric('::/p:c/o:5/nf:no/v:1/ta:1')
        chords.measure(34).notes[0].addLyric('::/p:g/o:4/nf:no/v:2')
        chords.measure(34).notes[0].addLyric('::/p:c/o:4/nf:no/v:1/tb:I')
        
        sr = analysis.reduction.ScoreReduction()
        sr.chordReduction = chords
        #sr.score = src
        unused_post = sr.reduce()
        #unused_post.show()        


    def testExtractionD(self):
        # this shows a score, extracting a single pitch
        from music21 import analysis, corpus

        src = corpus.parse('schoenberg/opus19', 6)
        for n in src.flat.notes:
            if 'Note' in n.classes:
                if n.pitch.name == 'F#':
                    n.addLyric('::/p:f#/o:4')
        #                 if n.pitch.name == 'C':
        #                     n.addLyric('::/p:c/o:4/g:C')
            elif 'Chord' in n.classes:
                if 'F#' in [p.name for p in n.pitches]:
                    n.addLyric('::/p:f#/o:4')
        #                 if 'C' in [p.name for p in n.pitches]:
        #                     n.addLyric('::/p:c/o:4/g:C')
                    
        sr = analysis.reduction.ScoreReduction()
        sr.score = src
        unused_post = sr.reduce()
        #post.show()        
    

    def testExtractionD2(self):
        # this shows a score, extracting a single pitch
        from music21 import analysis, corpus

        src = corpus.parse('schoenberg/opus19', 6)
        for n in src.flat.notes:
            if 'Note' in n.classes:
                if n.pitch.name == 'F#':
                    n.addLyric('::/p:f#/o:4/g:F#')
                if n.pitch.name == 'C':
                    n.addLyric('::/p:c/o:4/g:C')
            elif 'Chord' in n.classes:
                if 'F#' in [p.name for p in n.pitches]:
                    n.addLyric('::/p:f#/o:4/g:F#')
                if 'C' in [p.name for p in n.pitches]:
                    n.addLyric('::/p:c/o:4/g:C')
                    
        sr = analysis.reduction.ScoreReduction()
        sr.score = src
        unused_post = sr.reduce()
        #post.show()        



    def testExtractionE(self):
        from music21 import analysis, corpus

        src = corpus.parse('corelli/opus3no1/1grave')

        #chords = src.chordify()

        sr = analysis.reduction.ScoreReduction()
        #sr.chordReduction = chords
        sr.score = src
        unused_post = sr.reduce()
        #post.show()        
        


    def testPartReductionA(self):

        from music21 import analysis, corpus

        s = corpus.parse('bwv66.6')

        partGroups = [
            {'name':'High Voices', 'color':'#ff0088', 
                'match':['soprano', 'alto']}, 
            {'name':'Low Voices', 'color':'#8800ff', 
                'match':['tenor', 'bass']}
                    ]
        pr = analysis.reduction.PartReduction(s, partGroups=partGroups)
        pr.process()
        for sub in pr._partGroups:
            self.assertEqual(len(sub['match']), 2)


    def _matchWeightedData(self, match, target):
        '''Utility function to compare known data but not compare floating point weights. 
        '''
        for partId in range(len(target)):
            a = match[partId]
            b = target[partId]
            self.assertEqual(a[0], b[0])
            for i, dataMatch in enumerate(a[1]): # second item has data
                dataTarget = b[1][i]
                # start
                self.assertAlmostEqual(dataMatch[0], dataTarget[0])
                # span
                self.assertAlmostEqual(dataMatch[1], dataTarget[1])
                # weight
                self.assertAlmostEqual(dataMatch[2], dataTarget[2], 
                                msg="for partId %s, entry %d: should be %s <-> was %s" % (
                                                    partId, i, dataMatch[2], dataTarget[2]))

    def testPartReductionB(self, show=False):
        '''Artificially create test cases.
        '''
        from music21 import dynamics, graph, analysis
        durDynPairsA = [(1, 'mf'), (3, 'f'), (2, 'p'), (4, 'ff'), (2, 'mf')]
        durDynPairsB = [(1, 'mf'), (3, 'f'), (2, 'p'), (4, 'ff'), (2, 'mf')]

        s = stream.Score()
        pCount = 0
        for pairs in [durDynPairsA, durDynPairsB]:
            p = stream.Part()
            p.id = pCount
            pos = 0
            for ql, dyn in pairs:
                p.insert(pos, note.Note(quarterLength=ql))
                p.insert(pos, dynamics.Dynamic(dyn))
                pos += ql
            #p.makeMeasures(inPlace=True)
            s.insert(0, p)
            pCount += 1

        if show is True:
            s.show()

        pr = analysis.reduction.PartReduction(s, normalize=False)
        pr.process()
        match = pr.getGraphHorizontalBarWeightedData()
        target = [(0, [[0.0, 1.0, 0.07857142857142858, '#666666'], 
                       [1.0, 3.0, 0.09999999999999999, '#666666'], 
                       [4.0, 2.0, 0.05, '#666666'], 
                       [6.0, 4.0, 0.12142857142857143, '#666666'], 
                       [10.0, 2.0, 0.07857142857142858, '#666666']]), 
                  (1, [[0.0, 1.0, 0.07857142857142858, '#666666'], 
                       [1.0, 3.0, 0.09999999999999999, '#666666'], 
                       [4.0, 2.0, 0.05, '#666666'], 
                       [6.0, 4.0, 0.12142857142857143, '#666666'], 
                       [10.0, 2.0, 0.07857142857142858, '#666666']])]

        self._matchWeightedData(match, target)

        if show is True:
            p = graph.PlotDolan(s, title='Dynamics')
            p.process()


    def testPartReductionC(self):
        '''Artificially create test cases.
        '''
        from music21 import dynamics, analysis

        s = stream.Score()
        p1 = stream.Part()
        p1.id = 0
        p2 = stream.Part()
        p2.id = 1
        for ql in [1, 2, 1, 4]:
            p1.append(note.Note(quarterLength=ql))
            p2.append(note.Note(quarterLength=ql))
        for pos, dyn in [(0, 'p'), (2, 'fff'), (6, 'ppp')]:
            p1.insert(pos, dynamics.Dynamic(dyn))
        for pos, dyn in [(0, 'p'), (1, 'fff'), (2, 'ppp')]:
            p2.insert(pos, dynamics.Dynamic(dyn))
        s.insert(0, p1)
        s.insert(0, p2)
        #s.show()
        pr = analysis.reduction.PartReduction(s, normalize=False)
        pr.process()
        match = pr.getGraphHorizontalBarWeightedData()

        target = [(0, [[0.0, 2.0, 0.05, '#666666'], 
                       [2.0, 4.0, 0.1285714285714286, '#666666'], 
                       [6.0, 2.0, 0.0214285714286, '#666666']]), 
                  (1, [[0.0, 1.0, 0.05, '#666666'], 
                       [1.0, 1.0, 0.1285714285714286, '#666666'], 
                       [2.0, 6.0, 0.0214285714286, '#666666']])]

        self._matchWeightedData(match, target)


    def testPartReductionD(self):
        '''Artificially create test cases. Here, uses rests.
        '''
        from music21 import dynamics, analysis

        s = stream.Score()
        p1 = stream.Part()
        p1.id = 0
        p2 = stream.Part()
        p2.id = 1
        for ql in [None, 2, False, 2, False, 2]:
            if ql:
                p1.append(note.Note(quarterLength=ql))
                p2.append(note.Note(quarterLength=ql))
            else:
                p1.append(note.Rest(quarterLength=2))
                p2.append(note.Rest(quarterLength=2))
        for pos, dyn in [(0, 'p'), (2, 'fff'), (6, 'ppp')]:
            p1.insert(pos, dynamics.Dynamic(dyn))
        for pos, dyn in [(0, 'mf'), (2, 'f'), (6, 'mf')]:
            p2.insert(pos, dynamics.Dynamic(dyn))
        s.insert(0, p1)
        s.insert(0, p2)
        #s.show()

        pr = analysis.reduction.PartReduction(s)
        pr.process()
        match = pr.getGraphHorizontalBarWeightedData()
        #print match
        target = [(0, [[2.0, 2.0, 1.0, '#666666'], 
                       [6.0, 2.0, 0.166666666666666, '#666666'], 
                       [10.0, 2.0, 0.166666666666, '#666666']]), 
                  (1, [[2.0, 2.0, 0.7777777777777776, '#666666'], 
                       [6.0, 2.0, 0.6111111111111112, '#666666'], 
                       [10.0, 2.0, 0.6111111111111112, '#666666']])]
        self._matchWeightedData(match, target)


#         p = graph.PlotDolan(s, title='Dynamics')
#         p.process()


    def testPartReductionE(self):
        '''Artificially create test cases.
        '''
        from music21 import dynamics, analysis
        s = stream.Score()
        p1 = stream.Part()
        p1.id = 0
        p2 = stream.Part()
        p2.id = 1
        for ql in [2, 2, False, 2, False, 2]:
            if ql:
                p1.append(note.Note(quarterLength=ql))
                p2.append(note.Note(quarterLength=ql))
            else:
                p1.append(note.Rest(quarterLength=2))
                p2.append(note.Rest(quarterLength=2))
        for pos, dyn in [(0, 'p'), (2, 'fff'), (6, 'ppp')]:
            p1.insert(pos, dynamics.Dynamic(dyn))
        for pos, dyn in [(0, 'mf'), (2, 'f'), (6, 'mf')]:
            p2.insert(pos, dynamics.Dynamic(dyn))
        p1.makeMeasures(inPlace=True)
        p2.makeMeasures(inPlace=True)
        s.insert(0, p1)
        s.insert(0, p2)
        #s.show()

        pr = analysis.reduction.PartReduction(s, fillByMeasure=True,
                    segmentByTarget=False, normalize=False)
        pr.process()
        target = pr.getGraphHorizontalBarWeightedData()
        match = [(0, [[0.0, 4.0, 0.178571428571, '#666666'], 
                      [4.0, 4.0, 0.0214285714286, '#666666'], 
                      [8.0, 4.0, 0.0214285714286, '#666666']]), 
                 (1, [[0.0, 4.0, 0.178571428571, '#666666'], 
                      [4.0, 4.0, 0.07857142857142858, '#666666'], 
                      [8.0, 4.0, 0.07857142857142858, '#666666']])]

        self._matchWeightedData(match, target)

        pr = analysis.reduction.PartReduction(s, fillByMeasure=False,
                    segmentByTarget=True, normalize=False)
        pr.process()
        target = pr.getGraphHorizontalBarWeightedData()
        #print target
        match = [(0, [[0.0, 2.0, 0.05, '#666666'], 
                      [2.0, 2.0, 0.1285714285714286, '#666666'], 
                      [6.0, 2.0, 0.0214285714286, '#666666'], 
                      [10.0, 2.0, 0.0214285714286, '#666666']]), 
                 (1, [[0.0, 2.0, 0.07857142857142858, '#666666'], 
                      [2.0, 2.0, 0.1, '#666666'], 
                      [6.0, 2.0, 0.07857142857142858, '#666666'], 
                      [10.0, 2.0, 0.07857142857142858, '#666666']])]
        self._matchWeightedData(match, target)


        pr = analysis.reduction.PartReduction(s, fillByMeasure=False,
                    segmentByTarget=False)
        pr.process()
        target = pr.getGraphHorizontalBarWeightedData()
        #print target
        match = [(0, [[0.0, 4.0, 1.0, '#666666'], 
                      [6.0, 2.0, 0.12, '#666666'], 
                      [10.0, 2.0, 0.12, '#666666']]), 
                 (1, [[0.0, 4.0, 1.0, '#666666'], 
                      [6.0, 2.0, 0.44, '#666666'], 
                      [10.0, 2.0, 0.44, '#666666']])]
        self._matchWeightedData(match, target)


        pr = analysis.reduction.PartReduction(s, fillByMeasure=True,
                    segmentByTarget=True)
        pr.process()
        target = pr.getGraphHorizontalBarWeightedData()
        match = [(0, [[0.0, 2.0, 0.3888888888888, '#666666'], 
                      [2.0, 2.0, 1.0, '#666666'], 
                      [6.0, 2.0, 0.166666666667, '#666666'], 
                      [8.0, 4.0, 0.166666666667, '#666666']]), 
                 (1, [[0.0, 2.0, 0.6111111111111112, '#666666'], 
                      [2.0, 2.0, 0.7777777777777776, '#666666'], 
                      [6.0, 2.0, 0.611111111111111, '#666666'], 
                      [8.0, 4.0, 0.611111111111111, '#666666']])]
        self._matchWeightedData(match, target)


#         p = graph.PlotDolan(s, title='Dynamics', fillByMeasure=False,
#                             segmentByTarget=True, normalizeByPart=False)
#         p.process()

class TestExternal(unittest.TestCase):
    
    def testPartReductionB(self):
        t = Test()
        t.testPartReductionB(show=True)
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []



if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof



