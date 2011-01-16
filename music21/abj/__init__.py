'''
converter routines from Music21 to Abjad (see translate.py) -- 
called 'abj' to avoid namespace conflicts with the 'abjad'
package
'''

abjad = None

import music21

try:
    import abjad
    from translate import *
except ImportError:
    pass

