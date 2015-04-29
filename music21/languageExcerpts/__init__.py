# -*- coding: utf-8 -*-
import sys

if sys.version > '3':
    from music21.languageExcerpts import instrumentLookup
    from music21.languageExcerpts import naturalLanguageObjects
else:
    import instrumentLookup # @Reimport
    import naturalLanguageObjects # @Reimport
