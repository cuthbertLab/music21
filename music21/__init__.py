# -*- coding: utf-8 -*-
'''
The music21 Framework is Copyright © 2006-2021 Michael Scott Cuthbert
and the music21 Project

(Michael Scott Cuthbert, principal investigator; cuthbert@mit.edu)

Some Rights Reserved
Released under the BSD (3-clause) license.  For historical reasons, music21
can also be used under an LGPL license.

See license.txt file for the full license which represents your legal
obligations in using, modifying, or distributing music21.

Roughly speaking, this means that anyone can use this software for
free, they can distribute it to anyone, so long as this acknowledgment
of copyright and ownership remain publicly accessible.  You may also
modify this software or use it in your own programs so long as you do
so long as you make your product available
under the same license.  You may also link to this code as a library
from your sold, proprietary commercial product so long as this code
remains open and accessible, this license is made accessible,
and the developers are credited.

The development of music21 was supported by grants
from the Seaver Institute and the NEH/Digging into Data Challenge,
with the support of the MIT
Music and Theater Arts section and the School of Humanities, Arts,
and Social Sciences.  Portions of music21 were originally part of
the PMusic (Perl) library, developed by Cuthbert prior to arriving at MIT.

music21 outputs a subset of XML data defined by the MusicXML 4.0
standard, Copyright © 2004-2021 the Contributors to the MusicXML Specification.

The corpus files have copyrights retained by their
owners who have allowed them to be included with music21.
'''
import sys

minPythonVersion = (3, 7)
minPythonVersionStr = '.'.join([str(x) for x in minPythonVersion])
if sys.version_info < minPythonVersion:
    # DO NOT CHANGE THIS TO AN f-String -- it needs to run on old python.
    raise ImportError('''
    Music21 v.7.0+ is a Python {}+ only library.
    Use music21 v1 to run on Python 2.1-2.6.
    Use music21 v4 to run on Python 2.7.
    Use music21 v5.1 to run on Python 3.4.
    Use music21 v5.7 to run on Python 3.5.
    Use music21 v6.7 to run on Python 3.6.

    If you have the wrong version there are several options for getting
    the right one.

    - 1. (Best) Upgrade to Python 3, latest (currently 3.10).

         The great features there will more
         than make up for the headache of downloading
         a new version from https://www.python.org/

         You may already have Python 3 on your system.
         Try running "python3" instead of "python"

    - 2. Upgrade pip and setuptools to the latest version
         and then "upgrade" music21 to pre-version 5.

         $ pip install --upgrade pip setuptools
         $ pip install 'music21<5.0'
    '''.format(minPythonVersionStr))
del sys
del minPythonVersion
del minPythonVersionStr

# this defines what  is loaded when importing __all__
# put these in alphabetical order FIRST dirs then modules
# but: base must come first; in some cases other modules depend on
# definitions in base


__all__ = [
    'prebase',  # before all
    'base',  # top...
    'sites',  # important

    # sub folders
    'abcFormat',
    'alpha',
    'analysis',
    'audioSearch',
    'braille',
    'capella',
    'chord',
    'common',
    'converter',
    'corpus',
    'features',
    'figuredBass',
    'graph',
    'humdrum',
    'ipython21',
    'languageExcerpts',
    'lily',
    'mei',
    'metadata',
    'meter',
    'midi',
    'musedata',
    'musicxml',
    'noteworthy',
    'omr',
    'romanText',
    'scale',
    'search',
    'stream',
    'test',
    'tree',
    'vexflow',

    # individual modules
    # KEEP ALPHABETICAL unless necessary for load reasons, if so
    # put a note.  Keep one letter per line.

    'articulations',
    'bar',
    # base listed above
    'beam',
    'clef',
    'configure',
    'defaults',
    'derivation',
    'duration',
    'dynamics',
    'editorial',
    'environment',
    'exceptions21',
    'expressions',
    'freezeThaw',
    'harmony',
    'instrument',
    'interval',
    'key',
    'layout',
    'note',
    'percussion',
    'pitch',
    # prebase listed above
    'repeat',
    'roman',
    'serial',
    'sieve',
    # sites listed above
    'sorting',
    'spanner',
    'style',
    'tablature',
    'tempo',
    'text',
    'tie',
    'tinyNotation',
    'variant',
    'voiceLeading',
    'volpiano',
    'volume',
]

# ------------------------------------------------------------------------------
# for sub packages, need to manually add the modules in these subpackages


# ------------------------------------------------------------------------------
# base Music21Object -- all objects should inherit from this!
from music21 import base  # noqa: E402
from music21 import prebase  # noqa: E402
from music21 import sites  # noqa: E402

# should this simply be from music21.base import * since __all__ is well defined?
from music21.base import Music21Exception  # noqa: E402
from music21.base import SitesException  # noqa: E402
from music21.base import Music21ObjectException  # noqa: E402
from music21.base import ElementException  # noqa: E402

from music21.base import Groups  # noqa: E402
from music21.base import Music21Object  # noqa: E402
from music21.base import ElementWrapper  # noqa: E402

from music21.base import VERSION  # noqa: E402
from music21.base import VERSION_STR  # noqa: E402

__version__ = VERSION_STR

# legacy reason why it's here...
from music21.test.testRunner import mainTest  # noqa: E402

# -----------------------------------------------------------------------------
# now import all modules so they are accessible from "import music21"
from music21 import abcFormat  # noqa: E402
from music21 import alpha  # noqa: E402
from music21 import analysis  # noqa: E402
from music21 import audioSearch  # noqa: E402
from music21 import braille  # noqa: E402
from music21 import capella  # noqa: E402
from music21 import chord  # noqa: E402
from music21 import common  # noqa: E402
from music21 import converter  # noqa: E402
from music21 import corpus  # noqa: E402
from music21 import features  # noqa: E402
from music21 import figuredBass  # noqa: E402
from music21 import graph  # noqa: E402
from music21 import humdrum  # noqa: E402
from music21 import ipython21  # noqa: E402
from music21 import languageExcerpts  # noqa: E402
from music21 import lily  # noqa: E402
from music21 import mei  # noqa: E402
from music21 import metadata  # noqa: E402
from music21 import meter  # noqa: E402
from music21 import midi  # noqa: E402
from music21 import musedata  # noqa: E402
from music21 import musicxml  # noqa: E402
from music21 import noteworthy  # noqa: E402
from music21 import omr  # noqa: E402
from music21 import romanText  # noqa: E402
from music21 import scale  # noqa: E402
from music21 import search  # noqa: E402
from music21 import stream  # noqa: E402
from music21 import test  # noqa: E402
from music21 import tree  # noqa: E402
from music21 import vexflow  # noqa: E402

# individual modules
from music21 import articulations  # noqa: E402
from music21 import bar  # noqa: E402
# base already imported
from music21 import beam  # noqa: E402
from music21 import clef  # noqa: E402
from music21 import configure  # noqa: E402
from music21 import defaults  # noqa: E402
from music21 import derivation  # noqa: E402
from music21 import duration  # noqa: E402
from music21 import dynamics  # noqa: E402
from music21 import editorial  # noqa: E402
from music21 import environment  # noqa: E402
from music21 import exceptions21  # noqa: E402
from music21 import expressions  # noqa: E402
from music21 import freezeThaw  # noqa: E402
from music21 import harmony  # noqa: E402
from music21 import instrument  # noqa: E402
from music21 import interval  # noqa: E402
from music21 import key  # noqa: E402
from music21 import layout  # noqa: E402
from music21 import note  # noqa: E402
from music21 import percussion  # noqa: E402
from music21 import pitch  # noqa: E402
# prebase already imported
from music21 import repeat  # noqa: E402
from music21 import roman  # noqa: E402
from music21 import serial  # noqa: E402
from music21 import sieve  # noqa: E402
# sites already imported
from music21 import sorting  # noqa: E402
from music21 import spanner  # noqa: E402
from music21 import style  # noqa: E402
from music21 import tablature  # noqa: E402
from music21 import tempo  # noqa: E402
from music21 import text  # noqa: E402
from music21 import tie  # noqa: E402
from music21 import tinyNotation  # noqa: E402
from music21 import variant  # noqa: E402
from music21 import voiceLeading  # noqa: E402
from music21 import volpiano  # noqa: E402
from music21 import volume  # noqa: E402

