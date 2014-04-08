__all__ = ['cadencebook', 'capua', 'findTrecentoFragments', 'notation','tonality']

# this is necessary to get these names available with a 
# from music21 import * import statement
import sys

if sys.version > '3':
    pass
    # xlrd errors! 
#     from . import cadencebook
#     from . import capua
#     from . import findTrecentoFragments
#     from . import notation
#     from . import tonality
else:
    import cadencebook # @Reimport
    import capua # @Reimport
    import findTrecentoFragments # @Reimport
    import notation # @Reimport
    import tonality # @Reimport

#from music21.trecento import *

#------------------------------------------------------------------------------
# eof

