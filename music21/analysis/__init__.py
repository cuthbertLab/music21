# -*- coding: utf-8 -*-
__all__ = [
    'correlate', 'discrete', 'elements', 'enharmonics',
    'floatingKey', 'metrical', 'neoRiemannian',
    'patel', 'pitchAnalysis',
    'reduceChords', 'reduceChordsOld', 'reduction', 'segmentByRests',
    'transposition', 'windowed',
    'AnalysisException',
]

# this is necessary to get these names available with a
# from music21 import * import statement
from music21.analysis import correlate
from music21.analysis import discrete
from music21.analysis import elements
from music21.analysis import enharmonics
from music21.analysis import floatingKey
from music21.analysis import metrical
from music21.analysis import neoRiemannian
from music21.analysis import patel
from music21.analysis import pitchAnalysis
from music21.analysis import reduceChords
from music21.analysis import reduceChordsOld
from music21.analysis import reduction
from music21.analysis import segmentByRests
from music21.analysis import transposition
from music21.analysis import windowed

from music21.exceptions21 import AnalysisException

