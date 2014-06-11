.. _usersGuide_54_extendingConverter:
User's Guide: Chapter 54: Extending Converter with New Formats
==============================================================

.. code:: python


For this example, rather than importing \* from music21, we'll just
import the modules we need. If you're developing a new SubConverter
class just for yourself you can import everything, but if you're
thinking that you'd like to contribute your module back to music21
someday, it is important not to import \* since that will create
circular imports

.. code:: python

    from music21 import converter, note, stream, meter

We'll create a dummy file format, '.sb' or the 'singlebeat' format which
consists solely of a string of letters A-G in groups of any length
separated by spaces. A-G represents the pitch name (no accidentals),
while all notes written conjunctly in a group are interpreted as evenly
fitting within a quarter note.

.. code:: python

    class SingleBeat(converter.subConverters.SubConverter):
        registerFormats = ('singlebeat',)  # note the comma after the string
        registerInputExtensions = ('sb',)  # these are single element tuples.
        
        # we will just define parseData for now and let the SubConverter base class
        # deal with loading data from files of type .sb and URLs ending in .sb for us.
        
        def parseData(self, strData, number=None):  # movement number is ignored...
            '''  'AB C' -> A-8th, B-8th, C-qtr '''
            strDataList = strData.split()
            s = stream.Part()
            m = meter.TimeSignature('4/4')
            s.insert(0, m)
            for beat in strDataList:
                ql = 1.0/len(beat)
                for n in beat:
                    nObj = note.Note(n)
                    nObj.duration.quarterLength = ql
                    s.append(nObj)
            self.stream = s.makeMeasures()

Next we tell the converter module that our subconverter exists and can
handle 'singlebeat'/'singleBeat'/'.sb' files.

.. code:: python

    converter.registerSubconverter(SingleBeat)

Now the format is ready to be used through converter.parse() on string
data:

.. code:: python

    s = converter.parse('CDC DE F GAGB GE C DEFED C', format='singleBeat')
    s.show('text')


.. parsed-literal::
   :class: ipython-result

    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
        {0.3333} <music21.note.Note D>
        {0.6667} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {1.5} <music21.note.Note E>
        {2.0} <music21.note.Note F>
        {3.0} <music21.note.Note G>
        {3.25} <music21.note.Note A>
        {3.5} <music21.note.Note G>
        {3.75} <music21.note.Note B>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.note.Note G>
        {0.5} <music21.note.Note E>
        {1.0} <music21.note.Note C>
        {2.0} <music21.note.Note D>
        {2.2} <music21.note.Note E>
        {2.4} <music21.note.Note F>
        {2.6} <music21.note.Note E>
        {2.8} <music21.note.Note D>
        {3.0} <music21.note.Note C>
        {4.0} <music21.bar.Barline style=final>

Or, singleBeat is now a custom header for parse:

.. code:: python

    s = converter.parse('singleBeat: CDC DE F GAGB GE C DEFED C')
    s[-1][0]


.. parsed-literal::
   :class: ipython-result

    <music21.note.Note G>


Or we can write out a file and read it in:

.. code:: python

    from music21 import environment
    e = environment.Environment()
    fp = e.getTempFile('.sb')
    with open(fp, 'w') as f:
        f.write('CDC DE F GAGB GE C DEFED C')
        
    print fp


.. parsed-literal::
   :class: ipython-result

    /var/folders/x5/rymq2tx16lqbpytwb1n_cc4c0000gn/T/music21/tmpUB90FJ.sb

.. code:: python

    s2 = converter.parse(fp)
    s2.show('text')


.. parsed-literal::
   :class: ipython-result

    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
        {0.3333} <music21.note.Note D>
        {0.6667} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {1.5} <music21.note.Note E>
        {2.0} <music21.note.Note F>
        {3.0} <music21.note.Note G>
        {3.25} <music21.note.Note A>
        {3.5} <music21.note.Note G>
        {3.75} <music21.note.Note B>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.note.Note G>
        {0.5} <music21.note.Note E>
        {1.0} <music21.note.Note C>
        {2.0} <music21.note.Note D>
        {2.2} <music21.note.Note E>
        {2.4} <music21.note.Note F>
        {2.6} <music21.note.Note E>
        {2.8} <music21.note.Note D>
        {3.0} <music21.note.Note C>
        {4.0} <music21.bar.Barline style=final>

If you want to be extra-safe, pass the format in with the parse

.. code:: python

    s3 = converter.parse(fp, format='singleBeat')
    s3


.. parsed-literal::
   :class: ipython-result

    <music21.stream.Part 4412381520>


SingleBeat will now appear in all places where fileformats are listed:

.. code:: python

    from music21 import common
    common.findFormat('singleBeat')


.. parsed-literal::
   :class: ipython-result

    ('singlebeat', '.sb')

