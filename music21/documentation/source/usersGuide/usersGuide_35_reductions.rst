.. code:: python

    # ignore this
    %load_ext music21.ipython21.ipExtension

.. code:: python

    from music21 import *
    
    s = corpus.parse('bwv66.6')

.. code:: python

    tree = analysis.offsetTree.OffsetTree.fromScore(s)
