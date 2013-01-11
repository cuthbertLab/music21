__all__ = ['transcriber', 'base', 'recording', 'scoreFollower']

from music21.audioSearch import base # for some reason, imports music21.base!!!
from music21.audioSearch import recording
from music21.audioSearch import transcriber
from music21.audioSearch.base import *

__doc__ = base.__doc__ #@ReservedAssignment @UndefinedVariable