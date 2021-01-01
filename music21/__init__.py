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

music21 outputs a subset of XML data defined by the  MusicXML 3.1
standard, Copyright © Recordare LLC;  License available at
http://www.recordare.com/dtds/license.html, transferred to MakeMusic
now transferred to W3C

The corpus files have copyrights retained by their
owners who have allowed them to be included with music21.
'''
import sys

minPythonVersion = (3, 6)
minPythonVersionStr = '.'.join([str(x) for x in minPythonVersion])
if sys.version_info < minPythonVersion:
    raise ImportError('''
    Music21 v.6.0+ is a Python {}+ only library.
    Use music21 v.1 to run on Python 2.1-2.6.
    Use music21 v.4 to run on Python 2.7.
    Use music21 v.5.1 to run on Python 3.4.
    Use music21 v.5.7 to run on Python 3.5.

    If you got this library by installing there are several options.

    - 1. (Best) Upgrade to Python 3, latest (currently 3.9).

         The great features there will more
         than make up for the headache of downloading
         a new version from https://www.python.org/

         You may already have Python 3 on your system.
         Try running "python3" instead of "python"

    - 2. Upgrade pip and setuptools to the latest version
         and then "upgrade" music21 to version 4.

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
    'humdrum',
    'ipython21',
    'languageExcerpts',
    'lily',
    'mei',
    'metadata',
    'midi',
    'musedata',
    'musicxml',
    'noteworthy',
    'omr',
    'romanText',
    'scale',
    'search',
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
    'graph',
    'harmony',
    'instrument',
    'interval',
    'key',
    'layout',
    'meter',
    'note',
    'pitch',
    # prebase listed above
    'repeat',
    'roman',
    'serial',
    'sieve',
    'sorting',
    'spanner',
    'stream',
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
# this brings all of our own __all__ names into the music21 package namespace
# pylint: disable=wildcard-import
from music21 import *  # @UnresolvedImport  # noqa: E402,F403

