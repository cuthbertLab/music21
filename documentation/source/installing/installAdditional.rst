.. _installAdditional:


Extending `music21` with Additional Software
=======================================================


Installing Additional Python Modules
-----------------------------------------------

`Music21` can do more things, such as plotting graphs, if you
install additional Python libraries.

The following topics cover additional software used by `music21`.
For each library, visit the websites listed below, download the
additional python libraries, and install them just as you did with
`music21` above.  If you don't feel like installing them now, no worries:
you can always install them later.

It's best not to install these until you have `music21` working without
the external modules.

Note: as of `music21` v.6, some of these additional modules are bundled with `music21`


Matplotlib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Graphing and visual displays in Music21 are provided by Matplotlib.
Matplotlib itself has additional dependencies (such as NumPy).

On Mac if you are using the version from python.org, run:

`pip3 install matplotlib`

and you should be set.  If you are using a version from anaconda
(conda, miniconda, etc.), you should run these lines::

    conda install matplotlib
    conda install python.app


numpy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Numeric extensions to Python.  Included with Matplotlib.

On Mac if you are using the version of python 3 from python.org, run::

    pip3 install numpy

and you should be set.



scipy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Scientific extensions to Python.  These are used to accelerate
audio searching and fast-Fourier transforms in `music21`.
If you will only be using symbolic music, it is not used, and
not essential in any case.

On Mac if you are using the version from python.org, run::

    pip3 install scipy

and you should be set.



pyaudio
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allows for recording within python.  We use it for the audioSearch module, and nowhere else.
Not essential. Requires `portaudio` and, on the Mac, the XCode command-line development tools.

On the Mac, run::

    xcode-select --install
    brew install portaudio
    pip3 install pyaudio


pygame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allows for realtime MIDI performance.  We use it in the midi.realtime module, and nowhere else.
It is therefore not essential.

On the Mac, run::

    pip3 install pygame



Installing Additional Software Components
-----------------------------------------------

Additional functionality of `music21` is available with the
installation of numerous helper applications. While not essential
for all applications, these tools will aid in working with `music21`.



MuseScore
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MuseScore offers a free, full-featured, cross-platform (Windows, Mac OS, Ubuntu,
Debian, and Fedora) application for viewing and editing music notation.
MuseScore can import and export MusicXML, and provides an excellent way to view,
edit, and export musical data for working in `music21`.
Downloading MuseScore (version 2 or higher)
is highly recommended for working with `music21`.

https://musescore.org/en



Lilypond
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lilypond is a free, open-source music display program that can produce
beautiful scores.  `Music21` can generate PDF or PNG (like JPG) files
automatically if Lilypond is installed on your system.  Download it at:

http://lilypond.org/


