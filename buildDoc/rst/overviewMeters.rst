.. _overviewMeters:


Overview: Meters, Time Signatures, and Processing Beams, Accents, and Beats
===========================================================================

Meters and Time Signatures are represented in music21 as nested hierarchical structures. In many cases, the default configuration of a music21 :class:`~music21.meter.TimeSignature` object will do what you want. However, by configuring the fundamental component objects, the :class:`~music21.meter.MeterTerminal` and :class:`~music21.meter.MeterSequence`, a wide range of options are available.

The :class:`~music21.meter.TimeSignature` object additionally features numerous high-level methods to provide access to and configuration of beaming, accent, and beat information

This overview will illustrate key features of music21's meter objects. For complete documentation of these objects, see :ref:`moduleMeter`. 

For a more formal discussion of these designs, see the paper "Modeling Beats, Accents, Beams, and Time Signatures Hierarchically with music21 Meter Objects" (Ariza and Cuthbert 2010), at the following URL: http://mit.edu/music21/papers/2010MeterObjects.pdf




Creating and Editing MeterTerminals
-------------------------------------

Pass



Creating and Editing MeterSequences
-------------------------------------

Pass

.. image:: images/overviewMeters-02.*
    :width: 300







Creating and Editing Time Signatures 
---------------------------------------

The music21 :class:`~music21.meter.TimeSignature` object contains four parallel MeterSequence objects, each assigned to the attributes :attr:`~music21.meter.TimeSignature.display`, :attr:`~music21.meter.TimeSignature.beat`, :attr:`~music21.meter.TimeSignature.beam`, :attr:`~music21.meter.TimeSignature.accent`. The following displays a graphical realization of these four MeterSequence objects. 


.. image:: images/overviewMeters-01.*
    :width: 400





Configuring Time Signature Display
-------------------------------------

The following example demonstrates setting an independent display MeterSequence for a TimeSignature::


    ts1 = meter.TimeSignature('5/8') # assumes two partitions
    ts1.display.partition(['3/16','1/8','5/16'])
    
    ts2 = meter.TimeSignature('5/8') # assumes two partitions
    ts2.display.partition(['2/8', '3/8'])
    ts2.summedNumerator = True
        
    s = stream.Stream()
    for ts in [ts1, ts2]:
        m = stream.Measure()
        m.timeSignature = ts
        n = note.Note('b')
        n.quarterLength = 0.5
        m.repeatAppend(n, 5)
        s.append(m)
    s.show('musicxml')


.. image:: images/overviewMeters-08.*
    :width: 400




Configuring Time Signature Beaming
-------------------------------------

The following example beams a bar of 3/4 in four different ways. The diversity, and complexity, of beaming is offered here to illustrate the flexibility of this model::


    ts1 = meter.TimeSignature('3/4') 
    ts1.beam.partition(1)
    ts1.beam[0] = ts1.beam[0].subdivide(['3/8', '5/32', '4/32', '3/32'])
    
    ts2 = meter.TimeSignature('3/4') 
    ts2.beam.partition(3)
    
    ts3 = meter.TimeSignature('3/4') 
    ts3.beam.partition(3)
    for i in range(len(ts3.beam)):
        ts3.beam[i] = ts3.beam[i].subdivide(2)
    
    ts4 = meter.TimeSignature('3/4') 
    ts4.beam.partition(['3/8', '3/8'])
    for i in range(len(ts4.beam)):
        ts4.beam[i] = ts4.beam[i].subdivide(['6/32', '6/32'])
        for j in range(len(ts4.beam[i])):
            ts4.beam[i][j] = ts4.beam[i][j].subdivide(2)
    
    s = stream.Stream()
    for ts in [ts1, ts2, ts3, ts4]:
        m = stream.Measure()
        m.timeSignature = ts
        n = note.Note('b')
        n.quarterLength = 0.125
        m.repeatAppend(n, 24)
        s.append(m.makeBeams())
    s.show()


.. image:: images/overviewMeters-04.*
    :width: 400


The following is a fractional grid representation of the four beam partitions created. 

.. image:: images/overviewMeters-03.*
    :width: 300





Annotating Found Notes with Beat Count
-----------------------------------------

The following collects all C#s into a new Stream, and displays the resulting notes with annotations for part, measure, and beat::


    import music21
    from music21 import corpus, meter, stream
    
    score = corpus.parseWork('bach/bwv366.xml') 
    ts = score.flat.getElementsByClass(
        meter.TimeSignature)[0]
    ts.beat.partition(3)
    
    found = stream.Stream()
    offsetQL = 0
    for part in score:
        found.insert(offsetQL, 
            part.flat.getElementsByClass(
            music21.clef.Clef)[0])
        for i in range(len(part.measures)):
            m = part.measures[i]
            for n in m.notes:
                if n.name == 'C#': 
                    n.addLyric('%s, m. %s' %
                        (part.id[0], 
                        m.measureNumber))
                    n.addLyric('beat %s' % 
                        ts.getBeat(n.offset))
                    found.insert(offsetQL, n)
                    offsetQL += 4
    
    found.show('musicxml')

.. image:: images/overviewMeters-06.*
    :width: 400



Using Beat Depth to Provide Metrical Analysis
----------------------------------------------

The following example uses the number of hierarchical levels starting at or before a note provide a metrical weighting::


    import music21
    from music21 import corpus, meter
    
    score = corpus.parseWork('bach/bwv281.xml') 
    partBass = score.getElementById('Bass')
    ts = partBass.flat.getElementsByClass(
         meter.TimeSignature)[0]
    
    ts.beat.partition(1)
    for h in range(len(ts.beat)):
        ts.beat[h] = ts.beat[h].subdivide(2)
        for i in range(len(ts.beat[h])):
            ts.beat[h][i] = \
                ts.beat[h][i].subdivide(2)
            for j in range(len(ts.beat[h][i])):
                ts.beat[h][i][j] = \
                    ts.beat[h][i][j].subdivide(2)
    
    for m in partBass.measures:
        for n in m.notes:
            for i in range(ts.getBeatDepth(n.offset)):
                n.addLyric('*')
    
    partBass.measures[0:7].show('musicxml') 


.. image:: images/overviewMeters-07.*
    :width: 400







Applying Articulations Based on Accent
-----------------------------------------

The following example extract the Bass line of a Bach chorale in 3/4 and, after repartitioning the beat and accent attributes, applies accents to reflect a meter of 6/8::


    from music21 import corpus, meter, articulations
    
    score = corpus.parseWork('bach/bwv366.xml')
    partBass = score.getElementById('Bass')
    
    ts = partBass.flat.getElementsByClass(meter.TimeSignature)[0]
    ts.beat.partition(['3/8', '3/8'])
    ts.accent.partition(['3/8', '3/8'])
    ts.setAccentWeight([1, .5])
    
    for m in partBass.measures:
        lastBeat = None
        for n in m.notes:
            beat, progress = ts.getBeatProgress(n.offset)
            if beat != lastBeat and progress == 0:
                if n.tie != None and n.tie.type == 'stop':
                    continue
                if ts.getAccentWeight(n.offset) == 1:
                    mark = articulations.StrongAccent()
                elif ts.getAccentWeight(n.offset) == .5:
                    mark = articulations.Accent()
                n.articulations.append(mark)
                lastBeat = beat
            m = m.sorted
    
    partBass.measures[0:8].show('musicxml')


.. image:: images/overviewMeters-05.*
    :width: 400
