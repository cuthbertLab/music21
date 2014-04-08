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
    from . import basic
    from . import examples
    from . import lookup
    from . import segment
    from . import test
    from . import text
    from . import translate
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