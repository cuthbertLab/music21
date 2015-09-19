# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/m21ToString.py
# Purpose:      Translate Music21Objects to full MusicXML Strings
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Medium-level conversion routines to take music21
Streams and other objects and get a full MusicXML String
from them.  In general do not use this module.  Instead call:


>>> s = converter.parse('tinyNotation: 3/4 C4 D E r2.').makeMeasures()
>>> #_DOCS_SHOW s.show('musicxml')

But you might need this routine if you want to check that
the musicxml string returned has certain features:

>>> musicxmlStr = musicxml.m21ToString.fromMusic21Object(s)
>>> '<rest' in musicxmlStr
True

This module is an intermediate level of complexity for working
with musicxml between the standard music21 objects and musicxml.toMxObjects
'''
#------------------------------------------------
# general conversion

import copy
import unittest

from music21 import exceptions21
from music21 import note
from music21 import stream
from music21.musicxml import toMxObjects

def fromMusic21Object(m21Object):
    '''
    Translate an arbitrary music21 object to a musicxml
    string and return it
    
    This function is called by music21.base.write()
    and is the most important function here.
    '''
    classes = m21Object.classes
    
    if 'Measure' in classes: # must go before Stream
        return fromMeasure(m21Object)
    elif 'Stream' in classes:
        return fromStream(m21Object)
    elif 'GeneralNote' in classes:
        return fromGeneralNote(m21Object)
    elif 'Pitch' in classes:
        return fromPitch(m21Object)
    elif 'Duration' in classes:
        return fromDuration(m21Object)
    elif 'Dynamic' in classes:
        return fromDynamic(m21Object)
    elif 'DiatonicScale' in classes:
        return fromDiatonicScale(m21Object)
    elif 'Scale' in classes:
        return fromScale(m21Object)
    elif 'TimeSignature' in classes:
        return fromTimeSignature(m21Object)
    else:
        raise M21ToStringException("Cannot translate the object %s to a complete musicXML document; put it in a Stream first!" % m21Object)

def fromStream(streamObject):
    '''
    return a complete musicxml string
    from a music21 Stream object
    '''
    # always make a deepcopy before processing musicxml
    # this should only be done once
    post = copy.deepcopy(streamObject)
    post.makeImmutable()
    mxScore = toMxObjects.streamToMx(post)
    del post
    return mxScore.xmlStr()

def fromMeasure(m):
    '''Translate a music21 Measure into a 
    complete MusicXML string representation.

    Note: this method is called for complete MusicXML 
    representation of a Measure, not for partial 
    solutions in Part or Stream production.

    
    >>> m = stream.Measure()
    >>> m.repeatAppend(note.Note('g3'), 4)
    >>> post = musicxml.m21ToString.fromMeasure(m)
    >>> len(post) > 1000
    True
    '''
    # search for time signatures, either defined locally or in context
    #environLocal.printDebug(['fromMeasure', m]) 
    # we already have a deep copy passed in, which happens in 
    # fromMeasure(stream.Measure)
    m.makeNotation(inPlace=True)

    out = stream.Part()
    out.append(m)
    # call the musicxml property on Stream
    return fromMusic21Object(out)


def fromDuration(d):
    '''
    Translate a music21 :class:`~music21.duration.Duration` into 
    a complete MusicXML representation.
    
    Rarely rarely used.  Only if you call .show() on a duration object
    
    
    >>> d = duration.Duration(4.0)
    >>> dxml = musicxml.m21ToString.fromDuration(d)
    >>> print(dxml)
    <?xml version="1.0" ...?>
    <!DOCTYPE score-partwise
      PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
      'http://www.musicxml.org/dtds/partwise.dtd'>
    <score-partwise>
      <movement-title>Music21 Fragment</movement-title>
      <identification>
        <creator type="composer">Music21</creator>
      </identification>
      <defaults>
        <scaling>
          <millimeters>7</millimeters>
          <tenths>40</tenths>
        </scaling>
      </defaults>
      <part-list>
      ...
      </part-list>
      <part id="...">
        <measure number="1">
          <attributes>
            <divisions>10080</divisions>
            <time>
              <beats>4</beats>
              <beat-type>4</beat-type>
            </time>
            <clef>
              <sign>G</sign>
              <line>2</line>
            </clef>
          </attributes>
          <note>
            <pitch>
              <step>C</step>
              <octave>4</octave>
            </pitch>
            <duration>40320</duration>
            <type>whole</type>
            <notations/>
          </note>
          <barline location="right">
            <bar-style>light-heavy</bar-style>
          </barline>
        </measure>
      </part>
    </score-partwise>

    Or, more simply
    
    >>> #_DOCS_SHOW d.show('musicxml')
    '''
    # make a copy, as we this process will change tuple types
    # not needed, since fromGeneralNote does it too.  but so
    # rarely used, it doesn't matter, and the extra safety is nice.
    dCopy = copy.deepcopy(d)
    n = note.Note()
    n.duration = dCopy
    # call the musicxml property on Stream
    return fromGeneralNote(n)

def fromDynamic(dynamicObject):
    '''
    Provide a complete MusicXML string from a single dynamic by
    putting it into a Stream first.
    '''
    dCopy = copy.deepcopy(dynamicObject)
    out = stream.Stream()
    out.append(dCopy)
    # call the musicxml property on Stream
    return fromStream(out)
 
def fromScale(scaleObject):
    '''
    Generate the pitches from this scale
    and put it into a stream.Measure, then call 
    fromMeasure on it
    '''
    m = stream.Measure()
    for i in range(1, scaleObject._abstract.getDegreeMaxUnique()+1):
        p = scaleObject.pitchFromDegree(i)
        n = note.Note()
        n.pitch = p
        if i == 1:
            n.addLyric(scaleObject.name)

        if p.name == scaleObject.getTonic().name:
            n.quarterLength = 4 # set longer
        else:
            n.quarterLength = 1
        m.append(n)
    m.timeSignature = m.bestTimeSignature()
    return fromMeasure(m)

def fromDiatonicScale(diatonicScaleObject):
    '''
    Return a complete musicxml of the DiatonicScale

    Overrides the general scale behavior to highlight
    the tonic and dominant.
    '''
    m = stream.Measure()
    for i in range(1, diatonicScaleObject._abstract.getDegreeMaxUnique()+1):
        p = diatonicScaleObject.pitchFromDegree(i)
        n = note.Note()
        n.pitch = p
        if i == 1:
            n.addLyric(diatonicScaleObject.name)

        if p.name == diatonicScaleObject.getTonic().name:
            n.quarterLength = 4 # set longer
        elif p.name == diatonicScaleObject.getDominant().name:
            n.quarterLength = 2 # set longer
        else:
            n.quarterLength = 1
        m.append(n)
    m.timeSignature = m.bestTimeSignature()
    return fromMeasure(m)


def fromTimeSignature(ts):
    '''
    return a single TimeSignature as a musicxml document
    '''
    
    # return a complete musicxml representation
    tsCopy = copy.deepcopy(ts)
#         m = stream.Measure()
#         m.timeSignature = tsCopy
#         m.append(note.Rest())
    out = stream.Stream()
    out.append(tsCopy)
    return fromMusic21Object(out)

def fromGeneralNote(n):
    '''
    Translate a music21 :class:`~music21.note.Note` into a 
    complete MusicXML representation.

    
    >>> n = note.Note('c3')
    >>> n.quarterLength = 3
    >>> post = musicxml.m21ToString.fromGeneralNote(n)
    >>> #print post
    
    '''
    # make a copy, as this process will change tuple types
    # this method is called infrequently, and only for display of a single 
    # note
    nCopy = copy.deepcopy(n)
    
    # modifies in place
    stream.makeNotation.makeTupletBrackets([nCopy.duration], inPlace=True) 
    out = stream.Stream()
    out.append(nCopy)

    # call the musicxml property on Stream
    return fromMusic21Object(out)

def fromPitch(p):
    n = note.Note()
    n.pitch = copy.deepcopy(p)
    out = stream.Stream()
    out.append(n)
    # call the musicxml property on Stream
    return fromStream(out)


class M21ToStringException(exceptions21.Music21Exception):
    pass

#--------------------------------------------------
# Test Classes

class Test(unittest.TestCase):
    pass

    def testVoices(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.voiceDouble)
        unused_raw = fromMusic21Object(s)
        # TODO- Test voices out...

    def testTextExpressionsB(self):
        from music21 import expressions

        textSrc = ['loud', 'soft', 'with\nspirit', 'with\nless\nintensity']
        sizeSrc = [8, 10, 12, 18, 24]
        positionVerticalSrc = [20, -80, 20]
        enclosureSrc = [None, None, None, 'rectangle', 'oval']
        styleSrc = ['italic', 'bold', None, 'bolditalic']

        p = stream.Part()
        for i in range(20):
            te = expressions.TextExpression(textSrc[i % len(textSrc)])
            te.size = sizeSrc[i % len(sizeSrc)]
            te.justify = 'left'
            te.positionVertical = positionVerticalSrc[
                                    i % len(positionVerticalSrc)]
            te.enclosure = enclosureSrc[i % len(enclosureSrc)]
            te.style = styleSrc[i % len(styleSrc)]

            p.append(te)
            p.append(note.Note(type='quarter'))
            for i in range(4):
                p.append(note.Rest(type='16th'))

        s = stream.Score()
        s.insert(0, p)
        #s.show()

        musicxml = fromMusic21Object(s)
        #print musicxml
        match = """<direction>
        <direction-type>
          <words default-y="20.0" enclosure="rectangle" font-size="18.0" justify="left">with
spirit</words>
        </direction-type>
        <offset>0</offset>
      </direction>"""
        self.assertEqual(match in musicxml, True)



    def testImportRepeatExpressionsA(self):
        # test importing from musicxml
        from music21.musicxml import testPrimitive
        from music21 import converter

        # has one segno
        s = converter.parse(testPrimitive.repeatExpressionsA)
        # test roundtrip output
        raw = fromMusic21Object(s)

        self.assertEqual(raw.find('<segno') > 0, True)
        self.assertEqual(raw.find('Fine') > 0, True)
        self.assertEqual(raw.find('D.S. al Fine') > 0, True)

        # has two codas
        s = converter.parse(testPrimitive.repeatExpressionsB)
        # has one d.c.al coda
        raw = fromMusic21Object(s)

        self.assertEqual(raw.find('<coda') > 0, True)
        self.assertEqual(raw.find('D.C. al Coda') > 0, True)

    def testImportRepeatBracketA(self):
        from music21 import corpus
        # has repeats in it; start with single emasure
        s = corpus.parse('opus74no1', 3)
        raw = fromMusic21Object(s.parts[1])

        # TODO: order of attributes is not assured; allow for either order.
        self.assertEqual(raw.find("""<ending number="1" type="start"/>""") > 1, True)
        self.assertEqual(raw.find("""<ending number="1" type="stop"/>""") > 1, True)

        self.assertEqual(raw.find("""<ending number="2" type="start"/>""") > 1, True)
        self.assertEqual(raw.find("""<ending number="2" type="stop"/>""") > 1, True)

    def testImportMetronomeMarksA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter
        # has metronome marks defined, not with sound tag
        s = converter.parse(testPrimitive.metronomeMarks31c)
        raw = fromMusic21Object(s)

        raw = raw.replace(' ', '').replace('\n', '')
        match = '<beat-unit>long</beat-unit><per-minute>100.0</per-minute>'
        self.assertEqual(raw.find(match) > 0, True)

        match = '<beat-unit>quarter</beat-unit><beat-unit-dot/><per-minute>100.0</per-minute>'
        self.assertEqual(raw.find(match) > 0, True)

        match = '<beat-unit>long</beat-unit><beat-unit>32nd</beat-unit><beat-unit-dot/>'
        self.assertEqual(raw.find(match) > 0, True)

        match = '<beat-unit>quarter</beat-unit><beat-unit-dot/><beat-unit>half</beat-unit><beat-unit-dot/>'
        self.assertEqual(raw.find(match) > 0, True)

        # this is <metronome parenthesis="yes"> with spaces removed...
        match = '<metronomeparentheses="yes">'
        self.assertEqual(raw.find(match) > 0, True)

    def testExportMetronomeMarksA(self):
        from music21 import tempo
        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # default quarter assumed
        p.insert(0, tempo.MetronomeMark(number=121.6))

        raw = fromMusic21Object(p)
        match1 = '<beat-unit>quarter</beat-unit>'
        match2 = '<per-minute>121.6</per-minute>'
        self.assertEqual(raw.find(match1) > 0, True)
        self.assertEqual(raw.find(match2) > 0, True)

    def testExportMetronomeMarksB(self):
        from music21 import tempo
        from music21 import duration
        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # default quarter assumed
        p.insert(0, tempo.MetronomeMark(number=222.2,
                referent=duration.Duration(quarterLength=.75)))
        #p.show()
        raw = fromMusic21Object(p)
        match1 = '<beat-unit>eighth</beat-unit>'
        match2 = '<beat-unit-dot/>'
        match3 = '<per-minute>222.2</per-minute>'
        self.assertEqual(raw.find(match1) > 0, True)
        self.assertEqual(raw.find(match2) > 0, True)
        self.assertEqual(raw.find(match3) > 0, True)

    def testExportMetronomeMarksC(self):
        from music21 import tempo
        from music21 import duration
        # set metronome positions at different offsets in a measure or part
        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # default quarter assumed
        p.insert(0, tempo.MetronomeMark(number=222.2,
                referent=duration.Duration(quarterLength=.75)))
        p.insert(3, tempo.MetronomeMark(number=106, parentheses=True))
        p.insert(7, tempo.MetronomeMark(number=93,
                referent=duration.Duration(quarterLength=.25)))
        #p.show()

        raw = fromMusic21Object(p)
        match1 = '<beat-unit>eighth</beat-unit>'
        match2 = '<beat-unit-dot/>'
        match3 = '<per-minute>222.2</per-minute>'
        match4 = '<metronome parentheses="yes">'
        match5 = '<metronome parentheses="no">'
        self.assertEqual(raw.find(match1) > 0, True)
        self.assertEqual(raw.find(match2) > 0, True)
        self.assertEqual(raw.find(match3) > 0, True)
        self.assertEqual(raw.count(match4) == 1, True)
        self.assertEqual(raw.count(match5) == 2, True)


    def testExportMetronomeMarksD(self):
        from music21 import tempo
        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # default quarter assumed
        p.insert(0, tempo.MetronomeMark('super fast', number=222.2))

        # TODO: order of attributes is not assured; allow for any order.
        match1 = '<words default-y="45.0" font-weight="bold" justify="left">super fast</words>'
        match2 = '<per-minute>222.2</per-minute>'
        raw = fromMusic21Object(p)
        self.assertEqual(raw.find(match1) > 0, True)
        self.assertEqual(raw.find(match2) > 0, True)

        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # text does not show when implicit
        p.insert(0, tempo.MetronomeMark(number=132))
        # TODO: order of attributes is not assured; allow for any order.
        match1 = '<words default-y="45.0" font-weight="bold" justify="left">fast</words>'
        match2 = '<per-minute>132</per-minute>'
        raw = fromMusic21Object(p)
        self.assertEqual(raw.find(match1) > 0, False)
        self.assertEqual(raw.find(match2) > 0, True)

        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        mm = tempo.MetronomeMark('very slowly')
        self.assertEqual(mm.number, None)
        p.insert(0, mm)
        # text but no number
        # TODO: order of attributes is not assured; allow for any order.
        match1 = '<words default-y="45.0" font-weight="bold" justify="left">very slowly</words>'
        match2 = '<per-minute>'
        
        raw = fromMusic21Object(p)
        self.assertEqual(raw.find(match1) > 0, True)
        self.assertEqual(raw.find(match2) > 0, False)


    def testExportMetronomeMarksE(self):
        '''
        Test writing of sound tags
        '''
        from music21 import meter
        from music21 import tempo
        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # default quarter assumed
        p.insert(0, tempo.MetronomeMark('super slow', number=30.2))

        raw = fromMusic21Object(p)

        match1 = '<sound tempo="30.2"/>'
        self.assertEqual(raw.find(match1) > 0, True)
        #p.show()


        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 14)
        # default quarter assumed
        p.insert(meter.TimeSignature('2/4'))
        p.insert(0, tempo.MetronomeMark(number=30))
        p.insert(2, tempo.MetronomeMark(number=60))
        p.insert(4, tempo.MetronomeMark(number=120))
        p.insert(6, tempo.MetronomeMark(number=240))
        p.insert(8, tempo.MetronomeMark(number=240, referent=.75))
        p.insert(10, tempo.MetronomeMark(number=240, referent=.5))
        p.insert(12, tempo.MetronomeMark(number=240, referent=.25))
        #p.show()

        raw = fromMusic21Object(p)
        match1 = '<sound tempo="30.0"/>'
        self.assertEqual(raw.find(match1) > 0, True)
        match2 = '<sound tempo="60.0"/>'
        self.assertEqual(raw.find(match2) > 0, True)
        match3 = '<sound tempo="120.0"/>'
        self.assertEqual(raw.find(match3) > 0, True)
        match4 = '<sound tempo="240.0"/>'
        self.assertEqual(raw.find(match4) > 0, True)
        # from the dotted value
        match5 = '<sound tempo="180.0"/>'
        self.assertEqual(raw.find(match5) > 0, True)


    def testMetricModulationA(self):
        from music21 import tempo
        s = stream.Stream()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note(quarterLength=1), 4)
        mm1 = tempo.MetronomeMark(number=60.0)
        m1.insert(0, mm1)

        m2 = stream.Measure()
        m2.repeatAppend(note.Note(quarterLength=1), 4)
        # tempo.MetronomeMark(number=120.0)
        mmod1 = tempo.MetricModulation()
        # assign with an equivalent statement of the eight
        mmod1.oldMetronome = mm1.getEquivalentByReferent(.5)
        # set the other side of eq based on the desired  referent
        mmod1.setOtherByReferent(referent='quarter')
        m2.insert(0, mmod1)

        m3 = stream.Measure()
        m3.repeatAppend(note.Note(quarterLength=1), 4)
        mmod2 = tempo.MetricModulation()
        mmod2.oldMetronome = mmod1.newMetronome.getEquivalentByReferent(1.5)
        # set the other side of eq based on the desired  referent
        mmod2.setOtherByReferent(referent=1)
        m3.insert(0, mmod2)

        s.append([m1, m2, m3])
        raw = fromMusic21Object(s)

        match = '<sound tempo="60.0"/>'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<per-minute>60.0</per-minute>'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<sound tempo="120.0"/>'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<sound tempo="80.0"/>'
        self.assertEqual(raw.find(match) > 0, True)

        #s.show('t')
        #s.show()

    def testNoteheadConversion(self):
        # test to ensure notehead functionality
        n = note.Note('c3')
        n.notehead = 'diamond'

        out = fromMusic21Object(n)
        match1 = '<notehead>diamond</notehead>'
        self.assertEqual(out.find(match1) > 0, True, out)

    def testNoteheadSmorgasbord(self):
        # tests the of many different types of noteheads
        from music21 import expressions

        n = note.Note('c3')
        n.notehead = 'diamond'
        
        p = stream.Part()
        tn = expressions.TextExpression('diamond')
        m = note.Note('c3')
        m.notehead = 'cross'
        tm = expressions.TextExpression('cross')
        l = note.Note('c3')
        l.notehead = 'triangle'
        tl = expressions.TextExpression('triangle')
        k = note.Note('c3')
        k.notehead = 'circle-x'
        tk = expressions.TextExpression('circle-x')
        j = note.Note('c3')
        j.notehead = 'x'
        tj = expressions.TextExpression('x')
        i = note.Note('c3')
        i.notehead = 'slash'
        ti = expressions.TextExpression('slash')
        h = note.Note('c3')
        h.notehead = 'square'
        th = expressions.TextExpression('square')
        g = note.Note('c3')
        g.notehead = 'arrow down'
        tg = expressions.TextExpression('arrow down')
        f = note.Note('c3')
        f.notehead = 'inverted triangle'
        tf = expressions.TextExpression('inverted triangle')
        f.addLyric('inverted triangle')
        e = note.Note('c3')
        e.notehead = 'back slashed'
        te = expressions.TextExpression('back slashed')
        d = note.Note('c3')
        d.notehead = 'fa'
        td = expressions.TextExpression('fa')
        c = note.Note('c3')
        c.notehead = 'normal'
        tc = expressions.TextExpression('normal')

        noteList = [tc, c, tn, n, th, h, tl, l, tf, f, tg, g, te, e, ti, i, tj, j, tm, m, tk, k, td, d]
        for thisNote in noteList:
            p.append(thisNote)

        #p.show()
        raw = fromMusic21Object(p)

        self.assertEqual(raw.find('<notehead>diamond</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>square</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>triangle</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>inverted triangle</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>arrow down</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>back slashed</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>slash</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>x</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>cross</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>circle-x</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>fa</notehead>') > 0, True)



    def testMusicXMLNoteheadtoMusic21Notehead(self):
        # test to ensure noteheads can be imported from MusicXML
        from music21 import converter

        n = note.Note('c3')
        n.notehead = 'cross'
        noteMusicXML = fromMusic21Object(n)
        m = converter.parse(noteMusicXML)
        self.assertEqual(m.flat.notes[0].notehead, 'cross')

        #m.show()

    def testNoteheadWithTies(self):
        #what happens when you have notes with two different noteheads tied together?
        from music21 import tie
        from music21 import converter

        n1 = note.Note('c3')
        n1.notehead = 'diamond'
        n1.tie = tie.Tie('start')
        n2 = note.Note('c3')
        n2.notehead = 'cross'
        n2.tie = tie.Tie('stop')
        p = stream.Part()
        p.append(n1)
        p.append(n2)

        xml = fromMusic21Object(p)
        m = converter.parse(xml)
        self.assertEqual(m.flat.notes[0].notehead, 'diamond')
        self.assertEqual(m.flat.notes[1].notehead, 'cross')

        #m.show()

    def testStemDirection(self):
        #testing the ability to changing stem directions

        n1 = note.Note('c3')
        n1.notehead = 'diamond'
        n1._setStemDirection('double')
        p = stream.Part()
        p.append(n1)
        xml = fromMusic21Object(p)
        match1 = '<stem>double</stem>'
        self.assertEqual(xml.find(match1) > 0, True)

    def testStemDirImport(self):

        from music21 import converter

        n1 = note.Note('c3')
        n1.notehead = 'diamond'
        n1._setStemDirection('double')
        p = stream.Part()
        p.append(n1)

        xml = fromMusic21Object(p)
        m = converter.parse(xml)
        self.assertEqual(m.flat.notes[0].stemDirection, 'double')


    def testStaffGroupsB(self):
        from music21 import layout
        
        p1 = stream.Part()
        p1.repeatAppend(note.Note(), 8)
        p2 = stream.Part()
        p3 = stream.Part()
        p4 = stream.Part()
        p5 = stream.Part()
        p6 = stream.Part()
        p7 = stream.Part()
        p8 = stream.Part()

        sg1 = layout.StaffGroup([p1, p2], symbol='brace', name='marimba')
        sg2 = layout.StaffGroup([p3, p4], symbol='bracket', name='xlophone')
        sg3 = layout.StaffGroup([p5, p6], symbol='line', barTogether=False)
        sg4 = layout.StaffGroup([p5, p6, p7], symbol='line', barTogether=False)

        s = stream.Score()
        s.insert([0, p1, 0, p2, 0, p3, 0, p4, 0, p5, 0, p6, 0, p7, 0, p8, 0, sg1, 0, sg2, 0, sg3, 0, sg4])
        #s.show()

        raw = fromMusic21Object(s)

        match = '<group-symbol>brace</group-symbol>'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<group-symbol>bracket</group-symbol>'
        self.assertEqual(raw.find(match) > 0, True)
        # TODO: order of attributes is not assured; allow for any order.
        match = '<part-group number="1" type="start">'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<part-group number="1" type="stop"/>'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<part-group number="2" type="start">'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<part-group number="2" type="stop"/>'
        self.assertEqual(raw.find(match) > 0, True)

    
    def testInstrumentTranspositionA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.transposingInstruments72a)
        raw = fromMusic21Object(s)

        self.assertEqual(raw.find('<diatonic>-5</diatonic>') > 0, True)
        self.assertEqual(raw.find('<chromatic>-9</chromatic>') > 0, True)
        self.assertEqual(raw.find('<diatonic>-1</diatonic>') > 0, True)
        self.assertEqual(raw.find('<chromatic>-2</chromatic>') > 0, True)

    def testInstrumentTranspositionC(self):
        # generate all transpositions on output
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.transposing01)
        raw = fromMusic21Object(s)

        self.assertEqual(raw.count('<transpose>'), 6)

    def testHarmonyB(self):
        from music21 import harmony
        from music21 import key
        s = stream.Stream()
        s.append(key.KeySignature(-2))

        h1 = harmony.ChordSymbol()
        h1.root('c')
        h1.chordKind = 'minor-seventh'
        h1.chordKindStr = 'm7'
        h1.duration.quarterLength = 4
        s.append(h1)

        h2 = harmony.ChordSymbol()
        h2.root('f')
        h2.chordKind = 'dominant'
        h2.chordKindStr = '7'
        h2.duration.quarterLength = 4
        s.append(h2)

        h3 = harmony.ChordSymbol()
        h3.root('B-')
        h3.chordKind = 'major-seventh'
        h3.chordKindStr = 'Maj7'
        h3.duration.quarterLength = 4
        s.append(h3)

        h4 = harmony.ChordSymbol()
        h4.root('e-')
        h4.chordKind = 'major-seventh'
        h4.chordKindStr = 'Maj7'
        h4.duration.quarterLength = 4
        s.append(h4)

        h5 = harmony.ChordSymbol()
        h5.root('a')
        h5.chordKind = 'half-diminished'
        h5.chordKindStr = 'm7b5'
        h5.duration.quarterLength = 4
        s.append(h5)

        h6 = harmony.ChordSymbol()
        h6.root('d')
        h6.chordKind = 'dominant'
        h6.chordKindStr = '7'
        h6.duration.quarterLength = 4
        s.append(h6)

        h7 = harmony.ChordSymbol()
        h7.root('g')
        h7.chordKind = 'minor-sixth'
        h7.chordKindStr = 'm6'
        h7.duration.quarterLength = 4
        s.append(h7)

        #s.show()
        raw = fromMusic21Object(s)
        self.assertEqual(raw.find('<kind text="m7">minor-seventh</kind>') > 0, True)
        self.assertEqual(raw.find('<kind text="7">dominant</kind>') > 0, True)
        self.assertEqual(raw.find('<kind text="Maj7">major-seventh</kind>') > 0, True)
        self.assertEqual(raw.find('<kind text="Maj7">major-seventh</kind>') > 0, True)
        self.assertEqual(raw.find('<kind text="m7b5">half-diminished</kind>') > 0, True)

        self.assertEqual(raw.find('<root-step>C</root-step>') > 0, True)
        self.assertEqual(raw.find('<root-alter>-1</root-alter>') > 0, True)


    def testHarmonyC(self):
        from music21 import harmony

        h = harmony.ChordSymbol()
        h.root('E-')
        h.bass('B-')
        h.inversion(2, transposeOnSet = False)
        #h.romanNumeral = 'I64'
        h.chordKind = 'major'
        h.chordKindStr = 'M'

        hd = harmony.ChordStepModification()
        hd.modType = 'alter'
        hd.interval = -1
        hd.degree = 3
        h.addChordStepModification(hd)

        s = stream.Stream()
        s.append(h)
        #s.show()
        raw = fromMusic21Object(s)
        self.assertEqual(raw.find('<root-alter>-1</root-alter>') > 0, True)
        self.assertEqual(raw.find('<degree-value>3</degree-value>') > 0, True)
        self.assertEqual(raw.find('<degree-type>alter</degree-type>') > 0, True)

    def testChordNoteheadFillA(self):
        from music21 import chord
        c = chord.Chord(['c4', 'g4'])
        c[0].noteheadFill = False

        raw = fromMusic21Object(c)
        self.assertEqual(raw.count('<notehead filled="no">normal</notehead>'), 1)
        
        c[1].noteheadFill = False
        raw = fromMusic21Object(c)
        self.assertEqual(raw.count('<notehead filled="no">normal</notehead>'), 2)

    def testSummedNumerators(self):
        from music21 import meter
        # this forces a call to summed numerator translation
        ts1 = meter.TimeSignature('5/8') # assumes two partitions
        ts1.displaySequence.partition(['3/16', '1/8', '5/16'])

        ts2 = meter.TimeSignature('5/8') # assumes two partitions
        ts2.displaySequence.partition(['2/8', '3/8'])
        ts2.summedNumerator = True

        s = stream.Stream()
        for ts in [ts1, ts2]:
            m = stream.Measure()
            m.timeSignature = ts
            n = note.Note('b')
            n.quarterLength = 0.5
            m.repeatAppend(n, 5)
            s.append(m)
        unused_raw = fromMusic21Object(s)
        # TODO: Test Raw for something!!!!

    def testOrnamentA(self):
        from music21 import expressions
        from music21 import chord
        s = stream.Stream()
        s.repeatAppend(note.Note(), 4)
        s.repeatAppend(chord.Chord(['c4', 'g5']), 4)

        #s.insert(4, expressions.Trill())
        s.notes[3].expressions.append(expressions.Trill())
        s.notes[2].expressions.append(expressions.Mordent())
        s.notes[1].expressions.append(expressions.InvertedMordent())

        s.notes[6].expressions.append(expressions.Trill())
        s.notes[7].expressions.append(expressions.Mordent())
        s.notes[5].expressions.append(expressions.InvertedMordent())

        raw = fromMusic21Object(s)
        #s.show()

        self.assertEqual(raw.count('<trill-mark'), 2)
        self.assertEqual(raw.count('<ornaments>'), 6)
        self.assertEqual(raw.count('<inverted-mordent/>'), 2)
        self.assertEqual(raw.count('<mordent/>'), 2)


    def testNoteColorA(self):
        from music21 import chord
        n1 = note.Note()
        n2 = note.Note()
        n2.color = '#ff1111'
        n3 = note.Note()
        n3.color = '#1111ff'
        r1 = note.Rest()
        r1.color = '#11ff11'

        c1 = chord.Chord(['c2', 'd3', 'e4'])
        c1.color = '#ff0000'
        s = stream.Stream()
        s.append([n1, n2, n3, r1, c1])
        #s.show()

        raw = fromMusic21Object(s)
        # three color indications
        self.assertEqual(raw.count("color="), 8) #exports to notehead AND note, so increased from 6 to 8
        # color set at note level only for rest, so only 1
        self.assertEqual(raw.count('note color="#11ff11"'), 1)

    def testNoteColorB(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.colors01)
        #s.show()
        raw = fromMusic21Object(s)
        expectedColors = 8
        self.assertEqual(raw.count("color="), expectedColors, 'did not find the correct number of color statements: %d != %d \n %s' % (raw.count("color="), expectedColors, raw)) #exports to notehead AND note, so increased from 6 to 8
        # color set at note level only for rest, so only 1
        self.assertEqual(raw.count('note color="#11ff11"'), 1, 'did not find the correct number of color statements: %s' % raw)

    def testTextBoxB(self):
        from music21 import text
        y = 1000
        s = stream.Stream()

        tb3 = text.TextBox('c', 200, y)
        tb3.size = 40
        tb3.alignVertical = 'bottom'
        s.append(tb3)

        tb2 = text.TextBox('B', 300, y)
        tb2.size = 60
        tb2.alignVertical = 'bottom'
        s.append(tb2)

        tb2 = text.TextBox('!*&', 500, y)
        tb2.size = 100
        tb2.alignVertical = 'bottom'
        s.append(tb2)

        tb1 = text.TextBox('slowly', 700, y)
        tb1.alignVertical = 'bottom'
        tb1.size = 20
        tb1.style = 'italic'
        s.append(tb1)


        tb1 = text.TextBox('A', 850, y)
        tb1.alignVertical = 'bottom'
        tb1.size = 80
        tb1.weight = 'bold'
        tb1.style = 'italic'
        s.append(tb1)

        raw = fromMusic21Object(s)
        self.assertEqual(raw.count('</credit>'), 5)
        self.assertEqual(raw.count('font-size'), 5)


    def testSlursA(self):
        from music21 import corpus
        # this is a good test as this encoding uses staffs, not parts
        # to encode both parts; this requires special spanner handling
        s = corpus.parse('k545')
        # test roundtrip output
        raw = fromMusic21Object(s)
        # 2 pairs of start/stop
        self.assertEqual(raw.count('<slur'), 4) 
        #s.show()


    def testWedgeA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a)
        self.assertEqual(len(s.flat.getElementsByClass('Crescendo')), 1)

        # test roundtrip output
        raw = fromMusic21Object(s)
        self.assertEqual(raw.count('type="crescendo"'), 1)
        self.assertEqual(raw.count('type="diminuendo"'), 1)
        #s.show()

    def testWedgeB(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # this produces a single component cresc
        s = converter.parse(testPrimitive.directions31a)

        # test roundtrip output
        raw = fromMusic21Object(s)
        self.assertEqual(raw.count('type="crescendo"'), 2)


    def testBracketA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.directions31a)
        raw = fromMusic21Object(s)
        self.assertEqual(raw.count('<bracket'), 4)

    def testBracketB(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a)
        raw = fromMusic21Object(s) # test roundtrip output
        self.assertEqual(raw.count('<bracket'), 12)


    def testTrillExtensionA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.notations32a)
        raw = fromMusic21Object(s) # test roundtrip output
        self.assertEqual(raw.count('<wavy-line'), 4)

    def testGlissandoA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.spanners33a)
        raw = fromMusic21Object(s) # test roundtrip
        self.assertEqual(raw.count('<glissando'), 2)


    def testDashes(self):
        # dashes are imported as Lines (as are brackets)
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a)
        raw = fromMusic21Object(s)
        self.assertEqual(raw.count('<bracket'), 12)


    def testGraceA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.graceNotes24a)
        # test roundtrip output
        raw = fromMusic21Object(s)
        self.assertEqual(raw.count('<grace'), 15)


    def testGraceB(self):
        ng1 = note.Note('c4', quarterLength=.5).getGrace()
        ng1.duration.stealTimeFollowing = .5
        ng1.duration.slash = False
        n1 = note.Note('g4', quarterLength=2)

        ng2 = note.Note('c4', quarterLength=.5).getGrace()
        ng2.duration.stealTimePrevious = .25
        n2 = note.Note('d4', quarterLength=2)

        s = stream.Stream()
        s.append([ng1, n1, ng2, n2])
        #s.show()

        # test roundtrip output
        raw = fromMusic21Object(s)
        self.assertEqual(raw.count('slash="no"'), 1)
        self.assertEqual(raw.count('slash="yes"'), 1)

class TestExternal(unittest.TestCase):
    pass

    def runTest(self):
        pass
    
    def testShowAllTypes(self):
        '''
        show all known types to display
        
        tests fromMusic21Object()
        '''
        from music21 import scale
        from music21 import chord
        from music21 import duration
        from music21 import dynamics
        from music21 import meter
        from music21 import pitch
        
        m = stream.Measure()
        n = note.Note("D#6")
        m.repeatAppend(n, 6)
        m.show()

        s = stream.Stream()
        s.repeatAppend(n, 6)
        s.show()
        
        s = stream.Score()
        s.repeatAppend(n, 6)
        s.show()
        
        s = stream.Score()
        p = stream.Part()
        p.repeatAppend(n, 6)
        p2 = stream.Part()
        p2.repeatAppend(n, 6)
        s.insert(0, p)
        s.insert(0, p2)
        s.show()
        #emptyStream
        s = stream.Stream()
        s.show()
        p2.show()

        n.show()
        
        c = chord.Chord(['C3','D4','E5'])
        c.show()
        
        r = note.Rest()
        r.show()
        
        p = pitch.Pitch()
        p.show()
        
        d = duration.Duration(2.0)
        d.show()
        
        #empty duration! shows blank 4/4 measure, maybe with default rest.
        d = duration.Duration()
        d.show()

        mf = dynamics.Dynamic('mf')
        mf.show()
        
        cm = scale.MajorScale('C')
        cm.show()
        
        o = scale.OctatonicScale("C#4")
        o.show()
        
        ts = meter.TimeSignature('3/4')
        ts.show()


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof
