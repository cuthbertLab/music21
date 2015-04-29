# -*- coding: utf-8 -*-

__all__ = ['basic',
           'examples',
           'lookup',
           'segment',
           'test',
           'text',
           'translate']
import sys

if sys.version > '3':
    from music21.braille import basic
    from music21.braille import examples
    from music21.braille import lookup
    from music21.braille import segment
    from music21.braille import test
    from music21.braille import text
    from music21.braille import translate
else:          
    import basic # @Reimport
    import examples # @Reimport
    import lookup # @Reimport
    import segment # @Reimport
    import test # @Reimport
    import text # @Reimport
    import translate # @Reimport

#------------------------------------------------------------------------------
# eof
