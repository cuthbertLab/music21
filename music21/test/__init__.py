# -*- coding: utf-8 -*-

from music21.test.dedent import dedent

__all__ = [
    'dedent',
    'testDocumentation', 
    'testExternal', 
    'testPerformance', 
    'timeGraphs', 
    'testStream',
    'helpers',
    ]

import sys

if sys.version > '3':
    from music21.test import testStream
    from music21.test import testDocumentation
else:
    import testDocumentation # @Reimport
    import testStream # @Reimport

_DOC_IGNORE_MODULE_OR_PACKAGE = True

#------------------------------------------------------------------------------
# eof

