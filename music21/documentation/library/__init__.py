# -*- coding: utf-8 -*-

import sys

if sys.version > '3':
    from music21.documentation.library.documenters import *
    from music21.documentation.library.iterators import *
    from music21.documentation.library.writers import *
else:
    from documenters import *
    from iterators import *
    from writers import *
