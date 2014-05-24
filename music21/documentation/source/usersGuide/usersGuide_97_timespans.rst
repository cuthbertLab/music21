.. _usersGuide_97_timespans:
.. code:: python


.. code:: python

    from music21 import *

.. code:: python

    luca = corpus.parse('luca/gloria').measures(1,8)

.. code:: python

    tsCol = luca.asTimespans()

.. code:: python

    tsCol


.. parsed-literal::
   :class: ipython-result

    <TimespanCollection {55} (0.0 to 24.0) <music21.stream.Score 4371774736>>


.. code:: python

    for v in tsCol.iterateVerticalities():
        print v


.. parsed-literal::
   :class: ipython-result

    <Verticality 0.0 {F3 F4 C5}>
    <Verticality 3.0 {F3 F4 D5}>
    <Verticality 3.5 {F3 C4 C5}>
    <Verticality 4.5 {F3 C4 A4}>
    <Verticality 5.0 {F3 C4 F4}>
    <Verticality 5.5 {F3 A3 F4}>
    <Verticality 6.0 {F3 F4}>
    <Verticality 6.5 {F3 F4 A4}>
    <Verticality 7.5 {F3 F4 C5}>
    <Verticality 8.5 {F3 F4 C5}>
    <Verticality 9.0 {C4 E4 G4}>
    <Verticality 10.5 {D4 F4 A4}>
    <Verticality 12.0 {C4 E4 G4}>
    <Verticality 15.0 {G3 G4 D5}>
    <Verticality 16.5 {A3 E4 C5}>
    <Verticality 17.5 {A3 E4 B4}>
    <Verticality 18.0 {D4 F4 A4}>
    <Verticality 18.5 {D4 F4 G4}>
    <Verticality 19.0 {D4 F4}>
    <Verticality 19.5 {C4 E4 G4}>
    <Verticality 20.0 {C4 F4 G4}>
    <Verticality 20.5 {C4 D4 G4}>
    <Verticality 21.0 {C4 E4}>
    <Verticality 21.5 {A3 E4}>
    <Verticality 22.0 {A3 C4 F4}>
    <Verticality 22.5 {B-3 D4 F4}>
    <Verticality 23.0 {G3 B-3 D4}>
    <Verticality 23.5 {B-3 D4 F4}>

.. code:: python

    v4 = list(tsCol.iterateVerticalities())[4]

.. code:: python

    v4


.. parsed-literal::
   :class: ipython-result

    <Verticality 5.0 {F3 C4 F4}>


.. code:: python

    v4.pitchSet


.. parsed-literal::
   :class: ipython-result

    {<music21.pitch.Pitch F3>, <music21.pitch.Pitch C4>, <music21.pitch.Pitch F4>}


.. code:: python

    f = sorted(v4.pitchSet)[0]

.. code:: python

    f


.. parsed-literal::
   :class: ipython-result

    <music21.pitch.Pitch F3>


.. code:: python

    v4.startTimespans


.. parsed-literal::
   :class: ipython-result

    (<ElementTimespan (5.0 to 6.0) <music21.note.Note F>>,)


.. code:: python

    v4.stopTimespans


.. parsed-literal::
   :class: ipython-result

    (<ElementTimespan (4.5 to 5.0) <music21.note.Note A>>,)


.. code:: python

    v4.overlapTimespans


.. parsed-literal::
   :class: ipython-result

    (<ElementTimespan (3.0 to 6.0) <music21.note.Note F>>,
     <ElementTimespan (4.5 to 5.5) <music21.note.Note C>>)


.. code:: python

    v35 = tsCol.getVerticalityAt(3.5)

.. code:: python

    v35


.. parsed-literal::
   :class: ipython-result

    <Verticality 3.5 {F3 C4 C5}>


.. code:: python

    v35.startTimespans


.. parsed-literal::
   :class: ipython-result

    (<ElementTimespan (3.5 to 4.5) <music21.note.Note C>>,
     <ElementTimespan (3.5 to 4.5) <music21.note.Note C>>)


.. code:: python

    v35.stopTimespans


.. parsed-literal::
   :class: ipython-result

    (<ElementTimespan (3.0 to 3.5) <music21.note.Note D>>,
     <ElementTimespan (3.0 to 3.5) <music21.note.Note F>>)


.. code:: python

    v35.overlapTimespans


.. parsed-literal::
   :class: ipython-result

    (<ElementTimespan (3.0 to 6.0) <music21.note.Note F>>,)


.. code:: python

    elTsC = v35.startTimespans[0]

.. code:: python

    elTsC, elTsC.element


.. parsed-literal::
   :class: ipython-result

    (<ElementTimespan (3.5 to 4.5) <music21.note.Note C>>, <music21.note.Note C>)


.. code:: python

    prevElTs = tsCol.findPreviousElementTimespanInSamePart(elTsC)
    prevElTs


.. parsed-literal::
   :class: ipython-result

    <ElementTimespan (3.0 to 3.5) <music21.note.Note D>>


.. code:: python

    elTsC.part is prevElTs.part


.. parsed-literal::
   :class: ipython-result

    True


.. code:: python

    v35.previousVerticality


.. parsed-literal::
   :class: ipython-result

    <Verticality 3.0 {F3 F4 D5}>


.. code:: python

    tsCol.getVerticalityAt(elTsC.startOffset)


.. parsed-literal::
   :class: ipython-result

    <Verticality 3.5 {F3 C4 C5}>


.. code:: python

    _.previousVerticality


.. parsed-literal::
   :class: ipython-result

    <Verticality 3.0 {F3 F4 D5}>


Test previousVerticality with Rest

.. code:: python

    v22 = tsCol.getVerticalityAt(22.0)

.. code:: python

    v22


.. parsed-literal::
   :class: ipython-result

    <Verticality 22.0 {A3 C4 F4}>


.. code:: python

    v22.startTimespans


.. parsed-literal::
   :class: ipython-result

    (<ElementTimespan (22.0 to 23.0) <music21.note.Note F>>,
     <ElementTimespan (22.0 to 22.5) <music21.note.Note C>>)


.. code:: python

    elTSfollowingRest = v22.startTimespans[1]
    elTSfollowingRest


.. parsed-literal::
   :class: ipython-result

    <ElementTimespan (22.0 to 22.5) <music21.note.Note C>>


.. code:: python

    v22.stopTimespans


.. parsed-literal::
   :class: ipython-result

    (<ElementTimespan (21.0 to 22.0) <music21.note.Note E>>,)


.. code:: python

    elTSfollowingRest.part


.. parsed-literal::
   :class: ipython-result

    <music21.stream.Part Contratenor>


.. code:: python

    prevCT = tsCol.findPreviousElementTimespanInSamePart(elTSfollowingRest)
    prevCT


.. parsed-literal::
   :class: ipython-result

    <ElementTimespan (19.5 to 21.0) <music21.note.Note G>>


.. code:: python

    prevCT in v22.stopTimespans


.. parsed-literal::
   :class: ipython-result

    False


.. code:: python

    prevCT in v22.startTimespans


.. parsed-literal::
   :class: ipython-result

    False


.. code:: python

    prevCT in v22.overlapTimespans


.. parsed-literal::
   :class: ipython-result

    False


.. code:: python

    score = stream.timespans.makeExampleScore()

.. code:: python

    tsColSmall = stream.timespans.streamToTimespanCollection(score)

.. code:: python

    for v in tsColSmall.iterateVerticalities():
        print(v)
        print(v.getAllVoiceLeadingQuartets())
        


.. parsed-literal::
   :class: ipython-result

    <Verticality 0.0 {C3}>
    []
    <Verticality 1.0 {C3 D3}>
    [<music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note C> , v1n2=<music21.note.Note D>, v2n1=<music21.note.Note C>, v2n2=<music21.note.Note C>  ]
    <Verticality 2.0 {E3 G3}>
    [<music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note D> , v1n2=<music21.note.Note E>, v2n1=<music21.note.Note C>, v2n2=<music21.note.Note G>  ]
    <Verticality 3.0 {F3 G3}>
    [<music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note E> , v1n2=<music21.note.Note F>, v2n1=<music21.note.Note G>, v2n2=<music21.note.Note G>  ]
    <Verticality 4.0 {E3 G3}>
    [<music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note F> , v1n2=<music21.note.Note G>, v2n1=<music21.note.Note G>, v2n2=<music21.note.Note E>  ]
    <Verticality 5.0 {E3 A3}>
    [<music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note G> , v1n2=<music21.note.Note A>, v2n1=<music21.note.Note E>, v2n2=<music21.note.Note E>  ]
    <Verticality 6.0 {D3 B3}>
    [<music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note A> , v1n2=<music21.note.Note B>, v2n1=<music21.note.Note E>, v2n2=<music21.note.Note D>  ]
    <Verticality 7.0 {C3 D3}>
    [<music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note B> , v1n2=<music21.note.Note C>, v2n1=<music21.note.Note D>, v2n2=<music21.note.Note D>  ]

.. code:: python

    lucaAll = corpus.parse('luca/gloria')
    tsCol = lucaAll.asTimespans()

.. code:: python

    for v in tsCol.iterateVerticalities():
        vlqs = v.getAllVoiceLeadingQuartets()

.. code:: python

    bach = corpus.parse('bwv66.6')

.. code:: python

    import time
    t = time.time()
    dummy = theoryAnalysis.theoryAnalyzer.getVLQs(bach, 0, 1) # two parts only of bach
    print time.time() - t


.. parsed-literal::
   :class: ipython-result

    5.65062713623

.. code:: python

    t = time.time()
    tsCol = bach.asTimespans()
    for v in tsCol.iterateVerticalities():
        vlqs = v.getAllVoiceLeadingQuartets()
    print time.time() - t  # all parts == 6 pairs


.. parsed-literal::
   :class: ipython-result

    0.301722049713

.. code:: python

    

.. code:: python

    meterCol = lucaAll.parts[0].asTimespans(classList=(meter.TimeSignature))

.. code:: python

    meterCol


.. parsed-literal::
   :class: ipython-result

    <TimespanCollection {4} (0.0 to 275.0) <music21.stream.Part Cantus>>


.. code:: python

    print(meterCol)


.. parsed-literal::
   :class: ipython-result

    <TimespanCollection {4} (0.0 to 275.0) <music21.stream.Part Cantus>>
    	<ElementTimespan (0.0 to 0.0) <music21.meter.TimeSignature 6/8>>
    	<ElementTimespan (81.0 to 81.0) <music21.meter.TimeSignature 2/4>>
    	<ElementTimespan (185.0 to 185.0) <music21.meter.TimeSignature 6/8>>
    	<ElementTimespan (275.0 to 275.0) <music21.meter.TimeSignature 3/4>>

.. code:: python

    for i in range(0, 300):
        
