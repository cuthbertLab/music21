# -*- coding: utf-8 -*-

from music21.test.dedent import dedent

__all__ = [
    'dedent',
    'test', 
    'testDocumentation', 
    'testExternal', 
    'testPerformance', 
    'timeGraphs', 
    'testStream',
    ]

import sys

if sys.version > '3':
    from . import testStream
else:
    import testStream # @Reimport

_DOC_IGNORE_MODULE_OR_PACKAGE = True

#------------------------------------------------------------------------------
# eof

