.. _overviewFormats:


Overview: Importing File and Data Formats
===================================================

Music21 can import and export a variety of musical data formats. Many of these formats are distributed with music21 as part of the corpus module (see :ref:`moduleCorpus.base`). 

The converter module, as well as the module function :func:`music21.converter.parse` handle importing all supported formats. For complete documentation on file and data formats, see :ref:`moduleConverter`.



Parsing MusicXML Files
-----------------------

We can parse a MusicXML file by providing the :func:`music21.converter.parse` function with a local file path or an URL to a file path. The function will handle determining the file format. An appropriate :class:`~music21.stream.Stream`  or Stream subclass will be returned. For example, given a MusicXML file stored at the file path "/Volumes/xdisc/_scratch/bwv1007-01.xml", a Stream can be created from the file with the following:

>>> from music21 import converter
>>> sBach = converter.parse('/Volumes/xdisc/_scratch/bwv1007-01.xml')
>>> sBach.show()

After setting a new Clef on the first Measure, the Score can be viewed with the :meth:`~music21.base.Music21Object.show` method.

>>> sBach[0][1].clef = sBach[0][1].bestClef()
>>> sBach.show()

.. image:: images/overviewFormats-01.*
    :width: 600


Alternative, we can provide a URL to the :func:`music21.converter.parse` function that points to the desired file. Assuming proper system configuration (see :ref:`environment`), the file will be downloaded and parsed.

>>> url = 'http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/bach/cello&file=bwv1007-01.krn&f=xml'
>>> sAlt = converter.parse(url)


Note that presently music21 does not support compressed .mxl MusicXML files; this feature will be available soon.



Getting MusicXML Files
-----------------------

Numerous MusicXML files can be found at the following URLs.

http://www.wikifonia.org

http://kern.ccarh.org

http://www.gutenberg.org





Parsing Humdrum Files
-----------------------

Parsing Humdrum functions exactly as parsing other data formats. Simply call the :func:`music21.converter.parse` function on the desired file path or URL.

>>> sLassus = converter.parse('/Volumes/xdisc/_scratch/matona.krn')



Getting Humdrum Files
-----------------------

Over one hundred thousand Kern files can be found at the following URL.

http://kern.humdrum.net/






Parsing MIDI Files
-----------------------

Presently, MIDI input and output is not yet supported. We hope to have this feature available soon. 
