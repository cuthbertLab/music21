# -*- coding: utf-8 -*-

__all__ = ['checker',
           'examples',
           'notation',
           'possibility',
           'realizer',
           'realizerScale',
           'resolution',
           'rules',
           'segment']

import sys
from music21.ext import six

if six.PY3:
    from . import checker
    from . import examples
    from . import notation
    from . import possibility
    from . import realizer
    from . import realizerScale
    from . import resolution
    from . import rules
    from . import segment
else:           
    import checker   # @Reimport
    import examples # @Reimport
    import notation # @Reimport
    import possibility # @Reimport
    import realizer # @Reimport
    import realizerScale # @Reimport
    import resolution # @Reimport
    import rules # @Reimport
    import segment # @Reimport

#------------------------------------------------------------------------------
# eof