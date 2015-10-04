# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         romanText/translate.py
# Purpose:      Translation routines for roman numeral analysis text files
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Translation routines for roman numeral analysis text files, as defined 
and demonstrated by Dmitri Tymoczko.  Also used for the ClerqTemperley
format which is similar but a little different.

This module is really only needed for people extending the parser,
for others it's simple to get Harmony, RomanNumeral, Key (or KeySignature) 
and other objects out of an rntxt file by running this:


>>> monteverdi = corpus.parse('monteverdi/madrigal.3.1.rntxt')
>>> monteverdi.show('text')
{0.0} <music21.metadata.Metadata object at 0x...>
{0.0} <music21.stream.Part ...>
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.key.KeySignature of 1 flat>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.roman.RomanNumeral vi in F major>
        {3.0} <music21.roman.RomanNumeral V[no3] in F major>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.roman.RomanNumeral I in F major>
        {3.0} <music21.roman.RomanNumeral IV in F major>
    ...

Then the stream can be analyzed with something like this, storing
the data to make a histogram of scale degree usage within a key:

>>> degreeDictionary = {}
>>> for el in monteverdi.recurse():
...    if 'RomanNumeral' in el.classes:
...         print("%s %s" % (el.figure, el.key))
...         for p in el.pitches:
...              degree, accidental = el.key.getScaleDegreeAndAccidentalFromPitch(p)
...              if accidental is None:
...                   degreeString = str(degree)
...              else:
...                   degreeString = str(degree) + str(accidental.modifier)
...              if degreeString not in degreeDictionary:
...                   degreeDictionary[degreeString] = 1
...              else:
...                   degreeDictionary[degreeString] += 1
...              degTuple = (str(p), degreeString)
...              print ("%r" % (degTuple,) )
    vi F major
    ('D5', '6')
    ('F5', '1')
    ('A5', '3')
    V[no3] F major
    ('C5', '5')
    ('G5', '2')
    I F major
    ('F4', '1')
    ('A4', '3')
    ('C5', '5')
    ...
    V6 g minor
    ('F#5', '7#')
    ('A5', '2')
    ('D6', '5')
    i g minor
    ('G4', '1')
    ('B-4', '3')
    ('D5', '5')
    ...

Now if we'd like we can get a Histogram of the data.
It's a little complex, but worth seeing in full:

>>> import operator
>>> histo = graph.GraphHistogram()
>>> i = 0
>>> data = []
>>> xlabels = []
>>> values = []
>>> for deg,value in sorted(list(degreeDictionary.items()), key=operator.itemgetter(1), reverse=True):
...    data.append((i, degreeDictionary[deg]), )
...    xlabels.append((i+.5, deg), )
...    values.append(degreeDictionary[deg])
...    i += 1 
>>> histo.setData(data)


These commands give nice labels for the data; optional:

>>> histo.setIntegerTicksFromData(values, 'y')
>>> histo.setTicks('x', xlabels)
>>> histo.setAxisLabel('x', 'ScaleDegree')

Now generate the histogram:

>>> #_DOCS_HIDE histo.process()

.. image:: images/romanTranslatePitchDistribution.*
    :width: 600
    
    
OMIT_FROM_DOCS
>>> x = converter.parse('romantext: m1 a: VI')
>>> [str(p) for p in x.flat.getElementsByClass('RomanNumeral')[0].pitches]
['F5', 'A5', 'C6']

>>> x = converter.parse('romantext: m1 a: vi')
>>> [str(p) for p in x.flat.getElementsByClass('RomanNumeral')[0].pitches]
['F#5', 'A5', 'C#6']

>>> [str(p) for p in converter.parse('romantext: m1 a: vio').flat.getElementsByClass('RomanNumeral')[0].pitches]
['F#5', 'A5', 'C6']
'''
import unittest
import copy

from music21 import base
from music21 import exceptions21
from music21 import common
from music21 import bar

from music21.romanText import rtObjects


from music21 import environment
_MOD = 'romanText.translate.py'
environLocal = environment.Environment(_MOD)

USE_RN_CACHE = False 
## Not currently using rnCache because of problems with PivotChords,
## See mail from Dmitri, 30 September 2014

#-------------------------------------------------------------------------------

class RomanTextTranslateException(exceptions21.Music21Exception):
    pass

class RomanTextUnprocessedToken(base.ElementWrapper):
    pass

def _copySingleMeasure(t, p, kCurrent):
    '''Given a RomanText token, a Part used as the current container, 
    and the current Key, return a Measure copied from the past of the Part. 
    
    This is used in cases of definitions such as:
    m23=m21
    '''
    # copy from a past location; need to change key
    #environLocal.printDebug(['calling _copySingleMeasure()'])
    targetNumber, unused_targetRepeat = t.getCopyTarget()
    if len(targetNumber) > 1: # this is an encoding error
        raise RomanTextTranslateException('a single measure cannot define a copy operation for multiple measures')
    # TODO: ignoring repeat letters
    target = targetNumber[0]
    for mPast in p.getElementsByClass('Measure'):
        if mPast.number == target:
            try:
                m = copy.deepcopy(mPast)
            except TypeError:
                raise RomanTextTranslateException('Failed to copy measure %d: did you perhaps parse an RTOpus object with romanTextToStreamScore instead of romanTextToStreamOpus?' % (mPast.number))
            m.number = t.number[0]
            # update all keys
            for rnPast in m.getElementsByClass('RomanNumeral'):
                if kCurrent is None: # should not happen
                    raise RomanTextTranslateException('attempting to copy a measure but no past key definitions are found')
                if rnPast.followsKeyChange is True:
                    kCurrent = rnPast.key
                elif rnPast.pivotChord is not None:
                    kCurrent = rnPast.pivotChord.key
                else:
                    rnPast.key = kCurrent
                if rnPast.secondaryRomanNumeral is not None:
                    from music21 import roman
                    newRN = roman.RomanNumeral(rnPast.figure, kCurrent)
                    newRN.duration = copy.deepcopy(rnPast.duration)
                    newRN.lyrics = copy.deepcopy(rnPast.lyrics)
                    m.replace(rnPast, newRN)

            break
    return m, kCurrent


def _copyMultipleMeasures(t, p, kCurrent):
    '''
    Given a RomanText token for a RTMeasure, a 
    Part used as the current container, and the current Key, 
    return a Measure range copied from the past of the Part.
    
    This is used for cases such as:
    m23-25 = m20-22
    
    
    
    '''
    # the key provided needs to be the current key
    #environLocal.printDebug(['calling _copyMultipleMeasures()'])

    targetNumbers, unused_targetRepeat = t.getCopyTarget()
    if len(targetNumbers) == 1: # this is an encoding error
        raise RomanTextTranslateException('a multiple measure range cannot copy a single measure')
    # TODO: ignoring repeat letters
    targetStart = targetNumbers[0]
    targetEnd = targetNumbers[1]
    
    if t.number[1] - t.number[0] != targetEnd - targetStart:
        raise RomanTextTranslateException('both the source and destination sections need to have the same number of measures')
    elif t.number[0] < targetEnd:
        raise RomanTextTranslateException('the source section cannot overlap with the destination section')

    measures = []
    for mPast in p.getElementsByClass('Measure'):
        if mPast.number in range(targetStart, targetEnd +1):
            try:
                m = copy.deepcopy(mPast)
            except TypeError:
                raise RomanTextTranslateException('Failed to copy measure %d to measure range %d-%d: did you perhaps parse an RTOpus object with romanTextToStreamScore instead of romanTextToStreamOpus?' % (mPast.number, targetStart, targetEnd))
            
            m.number = t.number[0] + mPast.number - targetStart
            measures.append(m)
            # update all keys
            allRNs = m.getElementsByClass('RomanNumeral').elements
            for rnPast in allRNs:
                if kCurrent is None: # should not happen
                    raise RomanTextTranslateException('attempting to copy a measure but no past key definitions are found')
                if rnPast.followsKeyChange is True:
                    kCurrent = rnPast.key
                elif rnPast.pivotChord is not None:
                    kCurrent = rnPast.pivotChord.key
                else:
                    rnPast.key = kCurrent                
                if rnPast.secondaryRomanNumeral is not None:
                    from music21 import roman
                    newRN = roman.RomanNumeral(rnPast.figure, kCurrent)
                    newRN.duration = copy.deepcopy(rnPast.duration)
                    newRN.lyrics = copy.deepcopy(rnPast.lyrics)
                    m.replace(rnPast, newRN)
                    
        if mPast.number == targetEnd:
            break
    return measures, kCurrent


def _getKeyAndPrefix(rtKeyOrString):
    '''Given an RTKey specification, return the Key and a string prefix based
    on the tonic:

    >>> romanText.translate._getKeyAndPrefix('c')
    (<music21.key.Key of c minor>, 'c: ')
    >>> romanText.translate._getKeyAndPrefix('F#')
    (<music21.key.Key of F# major>, 'F#: ')
    >>> romanText.translate._getKeyAndPrefix('Eb')
    (<music21.key.Key of E- major>, 'E-: ')
    >>> romanText.translate._getKeyAndPrefix('Bb')
    (<music21.key.Key of B- major>, 'B-: ')
    >>> romanText.translate._getKeyAndPrefix('bb')
    (<music21.key.Key of b- minor>, 'b-: ')
    >>> romanText.translate._getKeyAndPrefix('b#')
    (<music21.key.Key of b# minor>, 'b#: ')
    '''
    from music21 import key
    if common.isStr(rtKeyOrString):
        rtKeyOrString = key.convertKeyStringToMusic21KeyString(rtKeyOrString)
        k = key.Key(rtKeyOrString)
    else:
        k = rtKeyOrString.getKey()
    tonicName = k.tonic.name
    if k.mode == 'minor':
        tonicName = tonicName.lower()
    prefix = tonicName + ": "
    return k, prefix


def romanTextToStreamScore(rtHandler, inputM21=None):
    '''The main processing module for single-movement RomanText works.

    Given a romanText handler or string, return or fill a Score Stream.
    '''
    # accept a string directly; mostly for testing
    if common.isStr(rtHandler):
        rtf = rtObjects.RTFile()
        rtHandler = rtf.readstr(rtHandler) # return handler, processes tokens

    # this could be just a Stream, but b/c we are creating metadata, perhaps better to match presentation of other scores. 

    from music21 import metadata
    from music21 import stream
    from music21 import note
    from music21 import meter
    from music21 import key
    from music21 import roman
    from music21 import tie

    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21

    # metadata can be first
    md = metadata.Metadata()
    s.insert(0, md)

    p = stream.Part()
    # ts indication are found in header, and also found elsewhere
    tsCurrent = meter.TimeSignature('4/4') # create default 4/4
    tsAtTimeOfLastChord = tsCurrent
    tsSet = False # store if set to a measure
    lastMeasureToken = None
    lastMeasureNumber = 0
    previousRn = None
    keySigCurrent = None
    keySigSet = True  # set a keySignature
    foundAKeySignatureSoFar = False
    kCurrent, unused_prefixLyric = _getKeyAndPrefix('C') # default if none defined
    prefixLyric = ''

    repeatEndings = {}
    rnKeyCache = {}

    for t in rtHandler.tokens:
        try:

            # environLocal.printDebug(['token', t])
            if t.isTitle():
                md.title = t.data            

            elif t.isWork():
                md.alternativeTitle = t.data

            elif t.isPiece():
                md.alternativeTitle = t.data

            elif t.isComposer():
                md.composer = t.data

            elif t.isMovement():
                md.movementNumber = t.data
    
            elif t.isTimeSignature():
                tsCurrent = meter.TimeSignature(t.data)
                tsSet = False
                # environLocal.printDebug(['tsCurrent:', tsCurrent])

            elif t.isKeySignature():
                if t.data == "":
                    keySigCurrent = key.KeySignature(0)
                elif t.data == "Bb":
                    keySigCurrent = key.KeySignature(-1)
                else:
                    pass 
                    # better to print a message
                    # environLocal.printDebug(['still need to write a generic RomanText KeySignature routine.  this is just temporary'])
                    # raise RomanTextTranslateException("still need to write a generic RomanText KeySignature routine.  this is just temporary")
                keySigSet = False
                # environLocal.printDebug(['keySigCurrent:', keySigCurrent])
                foundAKeySignatureSoFar = True

            elif t.isMeasure():
                # environLocal.printDebug(['handling measure token:', t])
                #if t.number[0] % 10 == 0:
                #    print "at number " + str(t.number[0])
                if t.variantNumber is not None:
                    # environLocal.printDebug(['skipping variant: %s' % t])
                    continue
                if t.variantLetter is not None:
                    # environLocal.printDebug(['skipping variant: %s' % t])
                    continue
    
                # if this measure number is more than 1 greater than the last
                # defined measure number, and the previous chord is not None, 
                # then fill with copies of the last-defined measure
                if ((t.number[0] > lastMeasureNumber + 1) and 
                    (previousRn is not None)):
                    for i in range(lastMeasureNumber + 1, t.number[0]):
                        mFill = stream.Measure()
                        mFill.number = i
                        newRn = copy.deepcopy(previousRn)
                        newRn.lyric = ""
                        # set to entire bar duration and tie 
                        newRn.duration = copy.deepcopy(tsAtTimeOfLastChord.barDuration)
                        if previousRn.tie is None:
                            previousRn.tie = tie.Tie('start')
                        else:
                            previousRn.tie.type = 'continue'
                        # set to stop for now; may extend on next iteration
                        newRn.tie = tie.Tie('stop')
                        previousRn = newRn
                        mFill.append(newRn)
                        appendMeasureToRepeatEndingsDict(lastMeasureToken, mFill, repeatEndings, i)
                        p._appendCore(mFill)
                    lastMeasureNumber = t.number[0] - 1
                    lastMeasureToken = t

                # create a new measure or copy a past measure
                if len(t.number) == 1 and t.isCopyDefinition: # if not a range
                    p.elementsChanged()
                    m, kCurrent = _copySingleMeasure(t, p, kCurrent)
                    p._appendCore(m)
                    lastMeasureNumber = m.number
                    lastMeasureToken = t
                    romans = m.iter.getElementsByClass(roman.RomanNumeral)
                    if romans:
                        previousRn = romans[-1] 

                elif len(t.number) > 1:
                    p.elementsChanged()
                    measures, kCurrent = _copyMultipleMeasures(t, p, kCurrent)
                    p.append(measures) # appendCore does not work with list
                    lastMeasureNumber = measures[-1].number
                    lastMeasureToken = t
                    romans = measures[-1].iter.getElementsByClass(roman.RomanNumeral)
                    if romans:
                        previousRn = romans[-1]

                else:       
                    m = stream.Measure()
                    m.number = t.number[0]
                    appendMeasureToRepeatEndingsDict(t, m, repeatEndings)                            
                    lastMeasureNumber = t.number[0]
                    lastMeasureToken = t
                    
                    if not tsSet:
                        m.timeSignature = tsCurrent
                        tsSet = True # only set when changed
                    if not keySigSet and keySigCurrent is not None:
                        m.insert(0, keySigCurrent)
                        keySigSet = True # only set when changed
        
                    o = 0.0 # start offsets at zero
                    previousChordInMeasure = None
                    pivotChordPossible = False
                    numberOfAtoms = len(t.atoms)
                    setKeyChangeToken = False # first RomanNumeral object after a key change should have this set to True
                    
                    for i, a in enumerate(t.atoms):
                        if isinstance(a, rtObjects.RTKey) or \
                           ((foundAKeySignatureSoFar == False) and \
                            (isinstance(a, rtObjects.RTAnalyticKey))): 
                            # found a change of Key+KeySignature or
                            # just found a change of analysis but no keysignature so far
                    
                            # environLocal.printDebug(['handling key token:', a])
                            try: # this sets the key and the keysignature
                                kCurrent, pl = _getKeyAndPrefix(a)
                                prefixLyric += pl
                            except:
                                raise RomanTextTranslateException('cannot get key from %s in line %s' % (a.src, t.src))
                            # insert at beginning of measure if at beginning -- for things like pickups.
                            if m.number < 2:
                                m._insertCore(0, kCurrent)
                            else:
                                m._insertCore(o, kCurrent)
                            foundAKeySignatureSoFar = True
                            setKeyChangeToken = True
    
                        elif isinstance(a, rtObjects.RTKeySignature):
                            try: # this sets the keysignature but not the prefix text
                                thisSig = a.getKeySignature()
                            except:
                                raise RomanTextTranslateException('cannot get key from %s in line %s' % (a.src, t.src))
                            #insert at beginning of measure if at beginning -- for things like pickups.
                            if m.number < 2:
                                m._insertCore(0, thisSig)
                            else:
                                m._insertCore(o, thisSig)
                            foundAKeySignatureSoFar = True
    
                        elif isinstance(a, rtObjects.RTAnalyticKey):
                            # just a change in analyzed key, not a change in anything else
                            #try: # this sets the key, not the keysignature
                            kCurrent, pl = _getKeyAndPrefix(a)
                            prefixLyric += pl
                            setKeyChangeToken = True

                            #except:
                            #    raise RomanTextTranslateException('cannot get key from %s in line %s' % (a.src, t.src))
    
                        elif isinstance(a, rtObjects.RTBeat):
                            # set new offset based on beat
                            try:
                                o = a.getOffset(tsCurrent)
                            except ValueError:
                                raise RomanTextTranslateException("cannot properly get an offset from beat data %s under timeSignature %s in line %s" % (a.src, tsCurrent, t.src))
                            if (previousChordInMeasure is None and 
                                previousRn is not None and o > 0):
                                # setting a new beat before giving any chords
                                firstChord = copy.deepcopy(previousRn)
                                firstChord.quarterLength = o
                                firstChord.lyric = ""
                                if previousRn.tie == None:
                                    previousRn.tie = tie.Tie('start')
                                else:
                                    previousRn.tie.type = 'continue'    
                                firstChord.tie = tie.Tie('stop')
                                previousRn = firstChord
                                previousChordInMeasure = firstChord
                                m._insertCore(0, firstChord)
                            pivotChordPossible = False

                        elif isinstance(a, rtObjects.RTNoChord):
                            # use source to evaluation roman 
                            tsAtTimeOfLastChord = tsCurrent
                            rn = note.Rest()
                            if pivotChordPossible == False:
                                # probably best to find duration
                                if previousChordInMeasure is None:
                                    pass # use default duration
                                else: # update duration of previous chord in Measure
                                    oPrevious = previousChordInMeasure.getOffsetBySite(m)
                                    newQL = o - oPrevious
                                    if newQL <= 0:
                                        raise RomanTextTranslateException('too many notes in this measure: %s' % t.src)
                                    previousChordInMeasure.quarterLength = newQL                                                          
                                prefixLyric = ""
                                m._insertCore(o, rn)
                                previousChordInMeasure = rn
                                previousRn = rn
                                pivotChordPossible = False

                        elif isinstance(a, rtObjects.RTChord):
                            # use source to evaluation roman 
                            tsAtTimeOfLastChord = tsCurrent
                            try:
                                asrc = a.src
    #                            if kCurrent.mode == 'minor':
    #                                if asrc.lower().startswith('vi'): #vi or vii w/ or w/o o
    #                                    if asrc.upper() == a.src: # VI or VII to bVI or bVII
    #                                        asrc = 'b' + asrc
                                cacheTuple = (asrc, kCurrent.tonicPitchNameWithCase)
                                if USE_RN_CACHE and cacheTuple in rnKeyCache:                                    
                                    #print "Got a match: " + str(cacheTuple)
                                    # Problems with Caches not picking up pivot chords... Not faster, see below.
                                    rn = copy.deepcopy(rnKeyCache[cacheTuple])
                                else:
                                    #print "No match for: " + str(cacheTuple)
                                    rn = roman.RomanNumeral(asrc, copy.deepcopy(kCurrent))
                                    rnKeyCache[cacheTuple] = rn
                                # surprisingly, not faster... and more dangerous
                                #rn = roman.RomanNumeral(asrc, kCurrent)
                                ## SLOWEST!!!
                                #rn = roman.RomanNumeral(asrc, kCurrent.tonicPitchNameWithCase)                                
                                
                                #>>> from timeit import timeit as t
                                #>>> t('roman.RomanNumeral("IV", "c#")', 'from music21 import roman', number=1000)
                                #45.75
                                #>>> t('roman.RomanNumeral("IV", k)', 'from music21 import roman, key; k = key.Key("c#")', number=1000)
                                #16.09
                                #>>> t('roman.RomanNumeral("IV", copy.deepcopy(k))', 'from music21 import roman, key; import copy; k = key.Key("c#")', number=1000)
                                #22.49
                                ## key cache, does not help much...
                                #>>> t('copy.deepcopy(r)', 'from music21 import roman; import copy; r = roman.RomanNumeral("IV", "c#")', number=1000)
                                #19.01
                                                              
                                if setKeyChangeToken is True:
                                    rn.followsKeyChange = True
                                    setKeyChangeToken = False
                                else:
                                    rn.followsKeyChange = False
                            except (roman.RomanNumeralException, 
                                common.Music21CommonException): 
                                #environLocal.printDebug('cannot create RN from: %s' % a.src)
                                rn = note.Note() # create placeholder 

                            if pivotChordPossible == False:
                                # probably best to find duration
                                if previousChordInMeasure is None:
                                    pass # use default duration
                                else: # update duration of previous chord in Measure
                                    oPrevious = previousChordInMeasure.getOffsetBySite(m)
                                    newQL = o - oPrevious
                                    if newQL <= 0:
                                        raise RomanTextTranslateException('too many notes in this measure: %s' % t.src)
                                    previousChordInMeasure.quarterLength = newQL                          
                                
                                rn.addLyric(prefixLyric + a.src)
                                prefixLyric = ""
                                m._insertCore(o, rn)
                                previousChordInMeasure = rn
                                previousRn = rn
                                pivotChordPossible = True
                            else:
                                previousChordInMeasure.lyric += "//" + prefixLyric + a.src
                                previousChordInMeasure.pivotChord = rn
                                prefixLyric = ""
                                pivotChordPossible = False

                        elif isinstance(a, rtObjects.RTRepeat):
                            if o == 0:
                                if isinstance(a, rtObjects.RTRepeatStart):
                                    m.leftBarline = bar.Repeat(direction='start')
                                else:
                                    rtt = RomanTextUnprocessedToken(a)
                                    m._insertCore(o, rtt)
                            elif tsCurrent is not None and (tsCurrent.barDuration.quarterLength == o or i == numberOfAtoms - 1):
                                if isinstance(a, rtObjects.RTRepeatStop):
                                    m.rightBarline = bar.Repeat(direction='end')
                                else:
                                    rtt = RomanTextUnprocessedToken(a)
                                    m._insertCore(o, rtt)
                            else: # mid measure repeat signs
                                rtt = RomanTextUnprocessedToken(a)
                                m._insertCore(o, rtt)

                        else:
                            rtt = RomanTextUnprocessedToken(a)
                            m._insertCore(o, rtt)
                            #environLocal.warn("Got an unknown token: %r" % a)
                    
                    # may need to adjust duration of last chord added
                    if tsCurrent is not None:
                        previousRn.quarterLength = tsCurrent.barDuration.quarterLength - o
                    m.elementsChanged()
                    p._appendCore(m)

        except Exception:
            import traceback
            tracebackMessage = traceback.format_exc()
            raise RomanTextTranslateException("At line %d for token %r, an exception was raised: \n%s" % (t.lineNumber, t, tracebackMessage))

    p.elementsChanged()
    fixPickupMeasure(p)
    p.makeBeams(inPlace=True)
    p.makeAccidentals(inPlace=True)
    _addRepeatsFromRepeatEndings(p, repeatEndings) # 1st and second endings...
    s.insert(0, p)

    return s


letterToNumDict = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}


def appendMeasureToRepeatEndingsDict(t, m, repeatEndings, measureNumber = None):
    '''Takes an RTMeasure object (t), (which might represent one or more
    measures; but currently only one) and a music21 stream.Measure object and
    store it as a tuple in the repeatEndings dictionary to mark where the
    translator should later mark for adding endings.
    
    If the optional measureNumber is specified, we use that rather than the
    token number to add to the dict.
    
    This does not yet work for skipped measures.
    
    >>> rtm = romanText.rtObjects.RTMeasure('m15a V6 b1.5 V6/5 b2 I b3 viio6')
    >>> rtm.repeatLetter
    ['a']
    >>> rtm2 = romanText.rtObjects.RTMeasure('m15b V6 b1.5 V6/5 b2 I')
    >>> rtm2.repeatLetter
    ['b']
    >>> repeatEndings = {}
    >>> m1 = stream.Measure()
    >>> m2 = stream.Measure()
    >>> romanText.translate.appendMeasureToRepeatEndingsDict(rtm, m1, repeatEndings)
    >>> repeatEndings
    {1: [(15, <music21.stream.Measure 0a offset=0.0>)]}
    >>> romanText.translate.appendMeasureToRepeatEndingsDict(rtm2, m2, repeatEndings)
    >>> repeatEndings[1], repeatEndings[2]
    ([(15, <music21.stream.Measure 0a offset=0.0>)], [(15, <music21.stream.Measure 0b offset=0.0>)])
    >>> repeatEndings[2][0][1] is m2
    True
    '''
    if len(t.repeatLetter) == 0:
        return
    
    m.numberSuffix = t.repeatLetter[0]
    
    for rl in t.repeatLetter:
        if rl is None or rl == "":
            continue
        if rl not in letterToNumDict:
            raise RomanTextTranslateException("Improper repeat letter: %s" % rl)
        repeatNumber = letterToNumDict[rl]
        if repeatNumber not in repeatEndings:
            repeatEndings[repeatNumber] = []
        if measureNumber is None:
            measureTuple = (t.number[0], m)
        else:
            measureTuple = (measureNumber, m)
        repeatEndings[repeatNumber].append(measureTuple)


def _consolidateRepeatEndings(repeatEndings):
    '''
    take repeatEndings, which is a dict of integers (repeat ending numbers) each
    holding a list of tuples of measure numbers and measure objects that get this ending, 
    and return a list where contiguous endings should appear.  Each element of the list is a 
    two-element tuple, where the first element is a list of measure objects that should have
    a bracket and the second element is the repeat number.
    
    Assumes that the list of measure numbers in each repeatEndings array is sorted.

    For the sake of demo and testing, we will use strings instead of measure objects.

    
    >>> repeatEndings = {1: [(5, 'm5a'), (6, 'm6a'), (17, 'm17'), (18, 'm18'), (19, 'm19'), (23, 'm23a')], 
    ...                  2: [(5, 'm5b'), (6, 'm6b'), (20, 'm20'), (21, 'm21'), (23, 'm23b')], 
    ...                  3: [(23, 'm23c')]}
    >>> print(romanText.translate._consolidateRepeatEndings(repeatEndings))
    [(['m5a', 'm6a'], 1), (['m17', 'm18', 'm19'], 1), (['m23a'], 1), (['m5b', 'm6b'], 2), (['m20', 'm21'], 2), (['m23b'], 2), (['m23c'], 3)]
    '''
    returnList = []
    
    for endingNumber in repeatEndings:
        startMeasureNumber = None
        lastMeasureNumber = None
        measureList = []
        for measureNumberUnderEnding, measureObject in repeatEndings[endingNumber]:
            if startMeasureNumber is None:
                startMeasureNumber = measureNumberUnderEnding
                lastMeasureNumber = measureNumberUnderEnding
                measureList.append(measureObject)
            elif measureNumberUnderEnding > lastMeasureNumber + 1:
                myTuple = (measureList, endingNumber)
                returnList.append(myTuple)
                startMeasureNumber = measureNumberUnderEnding
                lastMeasureNumber = measureNumberUnderEnding
                measureList = [measureObject]
            else:
                measureList.append(measureObject)
                lastMeasureNumber = measureNumberUnderEnding
        if startMeasureNumber is not None:
            myTuple = (measureList, endingNumber)
            returnList.append(myTuple)

    return returnList


def _addRepeatsFromRepeatEndings(s, repeatEndings):
    '''
    given a Stream and the repeatEndings dict, add repeats to the stream...    
    '''
    from music21 import spanner
    consolidatedRepeats = _consolidateRepeatEndings(repeatEndings)
    for repeatEndingTuple in consolidatedRepeats:
        measureList, endingNumber = repeatEndingTuple[0], repeatEndingTuple[1]
        rb = spanner.RepeatBracket(measureList, number=endingNumber)
        rbOffset = measureList[0].getOffsetBySite(s)
        #Adding repeat bracket to stream at beginning of repeated section.  
        #Maybe better at end?
        s.insert(rbOffset, rb)
        if endingNumber == 1: # should be "if not max(endingNumbers), but we can't tell that for each repeat...
            if measureList[-1].rightBarline is None:
                measureList[-1].rightBarline = bar.Repeat(direction='end')


def fixPickupMeasure(partObject):
    '''Fix a pickup measure if any.

    We determine a pickup measure by being measure 0 and not having an RN
    object at the beginning.

    Demonstration: an otherwise incorrect part
    
    >>> p = stream.Part()
    >>> m0 = stream.Measure()
    >>> m0.number = 0
    >>> k0 = key.Key('G')
    >>> m0.insert(0, k0)
    >>> m0.insert(0, meter.TimeSignature('4/4'))
    >>> m0.insert(2, roman.RomanNumeral('V', k0))
    >>> m1 = stream.Measure()
    >>> m1.number = 1
    >>> m2 = stream.Measure()
    >>> m2.number = 2
    >>> p.insert(0, m0)
    >>> p.insert(4, m1)
    >>> p.insert(8, m2)
    
    After running fixPickupMeasure()
    
    >>> romanText.translate.fixPickupMeasure(p)
    >>> p.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.key.Key of G major>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.roman.RomanNumeral V in G major>
    {2.0} <music21.stream.Measure 1 offset=2.0>
    <BLANKLINE>
    {6.0} <music21.stream.Measure 2 offset=6.0>
    <BLANKLINE>
    >>> m0.paddingLeft
    2.0
    '''
    m0 = partObject.measure(0)
    if m0 is None:
        return
    rnObjects = m0.getElementsByClass('RomanNumeral')
    if len(rnObjects) == 0:
        return
    if rnObjects[0].offset == 0:
        return
    newPadding = rnObjects[0].offset
    for el in m0:
        if el.offset < newPadding: # should be zero for Clefs, etc.
            pass
        else:
            el.offset = el.offset - newPadding
    m0.paddingLeft = newPadding
    for el in partObject: # adjust all other measures backwards
        if el.offset > 0:
            el.offset -= newPadding

def romanTextToStreamOpus(rtHandler, inputM21=None):
    '''The main processing routine for RomanText objects that may or may not
    be multi movement.
    
    Takes in a romanText.rtObjects.RTFile() object, or a string as rtHandler.
    
    Runs `romanTextToStreamScore()` as its main work.
    
    If inputM21 is None then it will create a Score or Opus object.
    
    Return either a Score object, or, if a multi-movement work is defined, an
    Opus object.
    '''
    from music21 import stream
    if common.isStr(rtHandler):
        rtf = rtObjects.RTFile()
        rtHandler = rtf.readstr(rtHandler) # return handler, processes tokens

    if rtHandler.definesMovements(): # create an opus
        if inputM21 == None:
            s = stream.Opus()
        else:
            s = inputM21
        # copy the common header to each of the sub-handlers
        handlerBundles = rtHandler.splitByMovement(duplicateHeader=True)
        # see if we have header information
        for h in handlerBundles:
            #print h, len(h)
            # append to opus
            s.append(romanTextToStreamScore(h))
        return s # an opus
    else: # create a Score
        return romanTextToStreamScore(rtHandler, inputM21=inputM21)


#-------------------------------------------------------------------------------

class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
 
    def testExternalA(self):
        from music21.romanText import testFiles

        for tf in testFiles.ALL:
            rtf = rtObjects.RTFile()
            rth = rtf.readstr(tf) # return handler, processes tokens
            s = romanTextToStreamScore(rth)
            s.show()


class TestSlow(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testBasicA(self):
        from music21.romanText import testFiles

        for tf in testFiles.ALL:
            rtf = rtObjects.RTFile()
            rth = rtf.readstr(tf) # return handler, processes tokens
            unused_s = romanTextToStreamOpus(rth) # will run romanTextToStreamScore on all but k273
            #s.show()
        
        s = romanTextToStreamScore(testFiles.swv23)
        self.assertEqual(s.metadata.composer, 'Heinrich Schutz')
        # this is defined as a Piece tag, but shows up here as a title, after
        # being set as an alternate title
        self.assertEqual(s.metadata.title, 'Warum toben die Heiden, Psalmen Davids no. 2, SWV 23')
        
        s = romanTextToStreamScore(testFiles.riemenschneider001)
        self.assertEqual(s.metadata.composer, 'J. S. Bach')
        self.assertEqual(s.metadata.title, 'Aus meines Herzens Grunde')

        s = romanTextToStreamScore(testFiles.monteverdi_3_13)
        self.assertEqual(s.metadata.composer, 'Claudio Monteverdi')

    def testMeasureCopyingA(self):
        from music21.romanText import testFiles

        s = romanTextToStreamScore(testFiles.swv23)
        mStream = s.parts[0].getElementsByClass('Measure')
        # the first four measures should all have the same content
        rn1 = mStream[1].getElementsByClass('RomanNumeral')[0]
        self.assertEqual([str(x) for x in rn1.pitches], ["D5", "F#5", "A5"])
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[1].getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn2.figure), 'i')

        # make sure that m2, m3, m4 have the same values
        rn1 = mStream[2].getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[2].getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn2.figure), 'i')

        rn1 = mStream[3].getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[3].getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn2.figure), 'i')

        # test multiple measure copying
        s = romanTextToStreamScore(testFiles.monteverdi_3_13)
        mStream = s.parts[0].getElementsByClass('Measure')
        for m in mStream:
            if m.number == 41: #m49-51 = m41-43
                m1a = m
            elif m.number == 42: #m49-51 = m41-43
                m2a = m
            elif m.number == 43: #m49-51 = m41-43
                m3a = m
            elif m.number == 49: #m49-51 = m41-43
                m1b = m
            elif m.number == 50: #m49-51 = m41-43
                m2b = m
            elif m.number == 51: #m49-51 = m41-43
                m3b = m

        rn = m1a.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'IV')        
        rn = m1a.getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn.figure), 'I')        

        rn = m1b.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'IV')        
        rn = m1b.getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn.figure), 'I')        

        rn = m2a.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'I')        
        rn = m2a.getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn.figure), 'ii')        

        rn = m2b.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'I')        
        rn = m2b.getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn.figure), 'ii')        

        rn = m3a.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'V/ii')        
        rn = m3b.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'V/ii')        

    def testMeasureCopyingB(self):
        from music21 import converter
        from music21.romanText import testFiles
        s = converter.parse(testFiles.monteverdi_3_13)
        m25 = s.measure(25)
        rn = m25.flat.getElementsByClass('RomanNumeral')
        self.assertEqual(rn[1].figure, 'III')
        self.assertEqual(str(rn[1].key), 'd minor')

        # TODO: this is getting the F#m even though the key and figure are 
        # correct
        #self.assertEqual(str(rn[1].pitches), '[F4, A4, C5]')

        #s.show()
        
    def testOpus(self):
        from music21.romanText import testFiles

        o = romanTextToStreamOpus(testFiles.mozartK279)
        self.assertEqual(o.scores[0].metadata.movementNumber, '1')
        self.assertEqual(o.scores[0].metadata.composer, 'Mozart')
        self.assertEqual(o.scores[1].metadata.movementNumber, '2')
        self.assertEqual(o.scores[1].metadata.composer, 'Mozart')
        self.assertEqual(o.scores[2].metadata.movementNumber, '3')
        self.assertEqual(o.scores[2].metadata.composer, 'Mozart')

        # test using converter.
        from music21 import converter
        s = converter.parse(testFiles.mozartK279)
        self.assertEqual('Opus' in s.classes, True)
        self.assertEqual(len(s.scores), 3)

        # make sure a normal file is still a Score
        s = converter.parse(testFiles.riemenschneider001)
        self.assertEqual('Score' in s.classes, True)
        

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testPivotInCopyMultiple(self):
        from music21 import converter
        testCase = '''
m1 G: I
m2 I
m3 V D: I
m4 V
m5 G: I
m6-7 = m3-4
m8 I
'''
        s = converter.parse(testCase, format='romanText')
        m = s.measure(7).flat
        self.assertEqual(m.getElementsByClass('RomanNumeral')[0].key.name, 'D major')
        m = s.measure(8).flat
        self.assertEqual(m.getElementsByClass('RomanNumeral')[0].key.name, 'D major')

    def testPivotInCopyMultiple2(self):
        '''
        test whether a chord in a pivot situation outside of copying affects copying
        '''
        
        from music21 import converter
        testCase = '''
m1 G: I
m2 V D: I
m3 G: IV
m4 V
m5 I
m6-7 = m4-5
m8 I
'''
        s = converter.parse(testCase, format='romanText')
        m = s.measure(5).flat
        self.assertEqual(m.getElementsByClass('RomanNumeral')[0].key.name, 'G major')


    def testPivotInCopySingle(self):
        from music21 import converter
        testCase = '''
m1 G: I
m2 I
m3 V D: I
m4 G: I
m5 = m3
m6 I
'''
        s = converter.parse(testCase, format='romanText')
        m = s.measure(6).flat
        self.assertEqual(m.getElementsByClass('RomanNumeral')[0].key.name, 'D major')

        
    def testSecondaryInCopyMultiple(self):
        '''
        test secondary dominants after copy
        '''
        
        testSecondaryInCopy = '''
Time Signature: 4/4
m1 g: i
m2 i6
m3 V7/v
m4 d: i
m5-6 = m2-3
m7 = m3
'''

        s = romanTextToStreamScore(testSecondaryInCopy)
        m = s.measure(6).flat
        self.assertEqual(m.getElementsByClass('RomanNumeral')[0].pitchedCommonName, 'E5-dominant seventh chord')
        m = s.measure(7).flat
        self.assertEqual(m.getElementsByClass('RomanNumeral')[0].pitchedCommonName, 'E5-dominant seventh chord')
        #s.show()

    def testBasicB(self):
        from music21.romanText import testFiles

        unused_s = romanTextToStreamScore(testFiles.riemenschneider001)
        #unused_s.show()

    def testRomanTextString(self):
        from music21 import converter
        s = converter.parse('m1 KS1 I \n m2 V6/5 \n m3 I b3 V7 \n m4 KS-3 vi \n m5 a: i b3 V4/2 \n m6 I', format='romantext')

        rnStream = s.flat.getElementsByClass('RomanNumeral')
        self.assertEqual(rnStream[0].figure, 'I')
        self.assertEqual(rnStream[1].figure, 'V6/5')        
        self.assertEqual(rnStream[2].figure, 'I')
        self.assertEqual(rnStream[3].figure, 'V7')
        self.assertEqual(rnStream[4].figure, 'vi')
        self.assertEqual(rnStream[5].figure, 'i')
        self.assertEqual(rnStream[6].figure, 'V4/2')
        self.assertEqual(rnStream[7].figure, 'I')


        rnStreamKey = s.flat.getElementsByClass('KeySignature')
        self.assertEqual(rnStreamKey[0].sharps, 1)
        self.assertEqual(rnStreamKey[1].sharps, -3)

        #s.show()


    def testMeasureCopyingB(self):
        from music21 import converter
        from music21 import pitch

        src = """m1 G: IV || b3 d: III b4 ii
m2 v b2 III6 b3 iv6 b4 ii/o6/5
m3 i6/4 b3 V
m4-5 = m2-3
m6-7 = m4-5
"""
        s = converter.parse(src, format='romantext')
        rnStream = s.flat.getElementsByClass('RomanNumeral')

        for elementNumber in [0, 6, 12]:
            self.assertEqual(rnStream[elementNumber + 4].figure, 'III6')
            self.assertEqual(str([str(p) for p in rnStream[elementNumber + 4].pitches]), "['A4', 'C5', 'F5']")

            x = rnStream[elementNumber + 4].pitches[2].accidental
            if x == None: 
                x = pitch.Accidental('natural')
            self.assertEqual(x.alter, 0)

            self.assertEqual(rnStream[elementNumber + 5].figure, 'iv6')
            self.assertEqual(str([str(p) for p in rnStream[elementNumber + 5].pitches]), "['B-4', 'D5', 'G5']")

            self.assertEqual(rnStream[elementNumber + 5].pitches[0].accidental.displayStatus, True)

    def testNoChord(self):
        from music21 import converter

        src = """m1 G: IV || b3 d: III b4 NC
m2 b2 III6 b3 iv6 b4 ii/o6/5
m3 NC b3 G: V
"""
        s = converter.parse(src, format='romantext')
        p = s.parts[0]
        m1 = p.getElementsByClass('Measure')[0]
        r1 = m1[-1]
        self.assertIn('Rest', r1.classes)
        self.assertEqual(r1.quarterLength, 1.0)
        m2 = p.getElementsByClass('Measure')[1]
        r2 = m2[0]
        self.assertIn('Rest', r2.classes)
        self.assertEqual(r1.quarterLength, 1.0)
        rn1 = m2[1]
        self.assertIn('RomanNumeral', rn1.classes)
        #s.show()
        
    def testPivotChord(self):
        from music21 import converter

        src = """m1 G: I b3 v d: i b4 V"""
        s = converter.parse(src, format='romantext')
        p = s.parts[0]
        m1 = p.getElementsByClass('Measure')[0]
        allRNs = m1.getElementsByClass('RomanNumeral')
        notPChord = allRNs[0]
        pChord = allRNs[1]
        self.assertEqual(pChord.key.tonic.step, 'G')
        self.assertEqual(pChord.figure, 'v')
        pivot = pChord.pivotChord
        self.assertEqual(pivot.key.tonic.step, 'D')
        self.assertEqual(pivot.figure, 'i')
        
        self.assertIsNone(notPChord.pivotChord)
        #s.show('text')
        
    def testTimeSigChanges(self):
        from music21 import converter
        src = """Time Signature: 4/4
        m1 C: I
        Time Signature: 2/4
        m10 V
        Time Signature: 4/4
        m12 I
        m14-25 = m1-12
        """
        s = converter.parse(src, format='romantext')
        p = s.parts[0]
        m3 = p.getElementsByClass('Measure')[2]
        self.assertEqual(m3.getOffsetBySite(p), 8.0)
        m10 = p.getElementsByClass('Measure')[9]
        self.assertEqual(m10.getOffsetBySite(p), 36.0)
        m11 = p.getElementsByClass('Measure')[10]
        self.assertEqual(m11.getOffsetBySite(p), 38.0)
        m12 = p.getElementsByClass('Measure')[11]
        self.assertEqual(m12.getOffsetBySite(p), 40.0)
        m13 = p.getElementsByClass('Measure')[12]
        self.assertEqual(m13.getOffsetBySite(p), 44.0)
        
        m16 = p.getElementsByClass('Measure')[15]
        self.assertEqual(m16.getOffsetBySite(p), 56.0)
        m23 = p.getElementsByClass('Measure')[22]
        self.assertEqual(m23.getOffsetBySite(p), 84.0)
        m24 = p.getElementsByClass('Measure')[23]
        self.assertEqual(m24.getOffsetBySite(p), 86.0)
        m25 = p.getElementsByClass('Measure')[24]
        self.assertEqual(m25.getOffsetBySite(p), 88.0)

        
    def testEndings(self):
        # has first and second endings...
        
        from music21.romanText import testFiles
        from music21 import converter
        unused_s = converter.parse(testFiles.mozartK283_2_opening, format='romanText')
        #s.show('text')

    def testTuplets(self):
        from music21 import converter
        c = converter.parse("m1 C: I b2.66 V", format='romantext')
        n1 = c.flat.notes[0]
        n2 = c.flat.notes[1]
        self.assertEqual(n1.duration.quarterLength, common.opFrac(5./3) )
        self.assertEqual(n2.offset, common.opFrac(5./3) )        
        self.assertEqual(n2.duration.quarterLength, common.opFrac(7./3) )

        c = converter.parse("TimeSignature: 6/8\nm1 C: I b2.66 V", format='romantext')
        n1 = c.flat.notes[0]
        n2 = c.flat.notes[1]
        self.assertEqual(n1.duration.quarterLength, common.opFrac(5./2) )
        self.assertEqual(n2.offset, common.opFrac(5./2) )        
        self.assertEqual(n2.duration.quarterLength, common.opFrac(1./2) )

        c = converter.parse("m1 C: I b2.66.5 V", format='romantext')
        n1 = c.flat.notes[0]
        n2 = c.flat.notes[1]
        self.assertEqual(n1.duration.quarterLength, common.opFrac(11./6) )
        self.assertEqual(n2.offset, common.opFrac(11./6) )        
        self.assertEqual(n2.duration.quarterLength, common.opFrac(13./6) )


#-------------------------------------------------------------------------------

# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    import music21
    #from music21 import converter
    #r = converter.parse('/Users/cuthbert/desktop/dmitri_rn2.rntxt', format='romantext')
    #r.show('text')
    #import time
    #t = time.time()
    #import sys
    #sys.argv.append('PivotInCopyMultiple2')
    #music21.mainTest(Test, runTest='testTuplets')
    music21.mainTest(Test, TestSlow)
    #print(time.time() - t)


#------------------------------------------------------------------------------
# eof

