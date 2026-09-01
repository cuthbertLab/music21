.. _migratingToV11:

Migrating to music21 v11
========================

The changes in v11 that can break old code, each with what to type instead.


Octaves are always integers
---------------------------

**In one line:** ``Pitch.octave`` is always an ``int``.  A pitch made without
an octave reports ``4``, not ``None``, and a new flag, ``octaveIsImplicit``,
remembers that you never gave one.

Before v11, ``pitch.Pitch('F#').octave`` was ``None``: a lovely idea (an
F-sharp in *any* octave) that crashed the moment someone wrote
``p.octave + 1``.  The pitch knew all along which octave it would use for
MIDI or a staff.  It kept that in ``implicitOctave``, a property that nobody
remembered.  Now ``octave`` does that job itself:

>>> from music21 import *
>>> anyFSharp = pitch.Pitch('F#')
>>> anyFSharp.octave
4
>>> anyFSharp.octaveIsImplicit
True

Nothing else about an octave-less pitch changes.  It still prints without a
number, transposes without one, and is not equal to an explicit F#4:

>>> anyFSharp
<music21.pitch.Pitch F#>
>>> anyFSharp.transpose('P8')
<music21.pitch.Pitch F#>
>>> anyFSharp == pitch.Pitch('F#4')
False

Give it an octave and the flag flips:

>>> anyFSharp.octave = 5
>>> anyFSharp.octaveIsImplicit
False
>>> anyFSharp
<music21.pitch.Pitch F#5>

Notes follow along: ``note.Note('B-').octave`` is ``4``, and the flag lives
on the note's pitch, ``n.pitch.octaveIsImplicit``.


What to change
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Before v11
     - v11
   * - ``if p.octave is None:``
     - ``if p.octaveIsImplicit:``
   * - ``p.octave = None``
     - ``p.octaveIsImplicit = True``  (the old spelling still works)
   * - ``p.implicitOctave``
     - ``p.octave``
   * - ``if p.octave is None: p.octave = p.implicitOctave``
     - ``p.octaveIsImplicit = False``
   * - ``octave: int | None``
     - ``octave: int``

``implicitOctave`` stays as a synonym for ``octave`` so nothing breaks
today.  It will be deprecated no earlier than v12 and removed later, so swap
it out when convenient.


What no longer crashes
~~~~~~~~~~~~~~~~~~~~~~

Arithmetic and formatting on any pitch, octave given or not:

>>> chordRoot = pitch.Pitch('E-')
>>> chordRoot.octave + 1
5
>>> f'{chordRoot.name}{chordRoot.octave}'
'E-4'

The few methods that need a pitch's *own* octave, such as
:meth:`~music21.pitch.Pitch.transposeAboveTarget`, still raise for an
implicit one.  Set ``.octave`` first.

The default of 4 comes from ``defaults.pitchOctave``.  Nobody has changed it
in the history of music21, but you could.
