.. _overviewStreams:


Overview: Streams, Scores, Parts, and Measures
==============================================

The :class:`~music21.stream.Stream` object and its many subclasses offer the fundamental container of music21 objects. As a container like a Python list (or an array in some languages), a Stream can be used to hold objects. These objects can be ordered in more than one way, or treated as an unordered collection. Objects stored in a Stream can be spaced in time; each stored object can have an offset from the beginning of the Stream. Streams, further, can store and offset other Streams, permitting a wide variety of nested, ordered, and timed structures.

Commonly used subclasses of Streams include the :class:`~music21.stream.Score`, :class:`~music21.stream.Part`, and :class:`~music21.stream.Measure`. As should be clear, any time we want to collect and contain a group of music21 objects, we do so in a Stream. Streams can, of course, be used for less conventional organizational structures. We frequently will build and pass around temporary Streams, as doing so gives us access to wide variety of tools for extracting, processing, and manipulating objects on the Stream. 

A critical feature of music21's design is that one music21 object can be simultaneously stored (or, more accurately, referenced) in more than one Stream. For examples, we might have numerous :class:`~music21.stream.Measure` Streams contained in a :class:`~music21.stream.Part` Stream. If we extract a region of this Part (using the :meth:`~music21.stream.Stream.getMeasureRange` method), we get a new Stream containing the specified Measures. We have not actually created new Measures or their components; the output Stream simply has references to the same objects. Changes made to Measures in this output Stream will be simultaneously made to Measures in the source Part. 

For complete documentation on Streams, see :ref:`moduleStream`.



Appending and Inserting Objects into Streams
---------------------------------------------

Streams provide a way to structure and position music21 objects both hierarchically and temporally.




Getting and Accessing Objects froms Streams
---------------------------------------------




Viewing and Visualizing Streams
---------------------------------------------


(See :ref:`quickStart` for basic configuraton information; see :ref:`environment` for complete information on configuring your :class:`~music21.environment.Environment`.). 





Accessing Hierarchically Nested and Flat Streams
-------------------------------------------------

Streams provide a way to structure and position music21 objects both hierarchically and temporally.







