
from music21.note import Note

def getEnharmonic(note1):
    '''Returns a new note that is the(/an) enharmonic equivalent of note1.

    N.B.: n1.name == getEnharmonic(getEnharmonic(n1)).name is not necessarily true.
    For instance: getEnharmonic(E##) => F#; getEnharmonic(F#) => G-
              or: getEnharmonic(A--) => G; getEnharmonic(G) => F##
    However, for all cases not involving double sharps or flats (and even many that do)
    getEnharmonic(getEnharmonic(n)) = n

    Enharmonics of the following are defined:
           C <-> B#, D <-> C##, E <-> F-; F <-> E#, G <-> F##, A <-> B--, B <-> C-

    However, areEnharmonics(A##, B) certainly returns true.

    Perhaps a getFirstNEnharmonics(n) needs to be defined which returns a list of the
    first n Enharmonics according to a particular algorithm, moving into triple sharps, etc.
    if need be.  Or getAllCommonEnharmonics(note) which returns all possible enharmonics that
    do not involve triple or more accidentals.

    '''
    pass

def flipEnharmonic(note1):
    '''like getEnharmonic, but alters the note that comes in'''
    pass

def getHigherEnharmonic(note1):
    '''returns the enharmonic note that is a dim-second above the current note'''
    pass

def getLowerEnharmonic(note1):
    '''returns the enharmonic note that is a dim-second below the current note'''
    pass

def areEnharmonics(note1, note2):
    pass

def getQuarterToneEnharmonic(note1):
    '''like getEnharmonic but handles quarterTones as well'''
    pass

def flipQuarterToneEnharmonic(note1):
    pass

def areQuarterToneEnharmonics(note1, note2):
    pass
