# script to create a graph to time how fast some things are happening...
# generates pretty graphs showing what the bottlenecks in the system are, for helping to
# improve them.  Requires pycallgraph (not included with music21).  


import pycallgraph
import time

import music21.stream
import music21.humdrum
from music21.humdrum import testFiles
htf = testFiles
import music21.converter
import music21.corpus
from music21.musicxml import testFiles
mxtf = testFiles
import music21.lily
import music21.trecento.capua

def timeHumdrum():
    masterStream = music21.humdrum.parseData(htf.mazurka6).stream

def timeMozart():
    a = music21.converter.parse(music21.corpus.getWork('k155')[0])
#    ls = music21.lily.LilyString("{" + a[0].lily + "}")
#    ls.showPNG()
#    a = music21.converter.parse(mxtf.ALL[1])

def timeCapua():
    c1 = music21.trecento.capua.Test()
    c1.testRunPiece()

def timeCapua2():
    music21.trecento.capua.ruleFrequency()

excludeList =  ['pycallgraph.*','re.*','sre_*', 'copy*', '*xlrd*',]
excludeList += ['*meter*', 'encodings*', '*isClass*', '*duration.Duration*']

gf = pycallgraph.GlobbingFilter(exclude=excludeList)

print(time.ctime())

pycallgraph.start_trace(filter_func = gf)

timeCapua2()

pycallgraph.make_dot_graph('d:\\desktop\\test1.png')

print(time.ctime())
