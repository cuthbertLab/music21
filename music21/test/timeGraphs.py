#!/usr/local/bin/python
#-------------------------------------------------------------------------------
# Name:          timeGraphs.py
# Purpose:       install
#
# Authors:       Michael Scott Cuthbert
#                Christopher Ariza
#
# Copyright:     (c) 2009-2010 The music21 Project
# License:       GPL
#-------------------------------------------------------------------------------


# script to create a graph to time how fast some things are happening...
# generates pretty graphs showing what the bottlenecks in the system are, for helping to
# improve them.  Requires pycallgraph (not included with music21).  


import pycallgraph
import time


from music21 import *
import music21.stream
import music21.humdrum
import music21.converter
import music21.corpus
import music21.lily
import music21.trecento.capua


from music21.humdrum import testFiles as humdrumTestFiles

from music21 import common

from music21 import environment
_MOD = "test.timeGraphs.py"
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
# define functions to Test


def timeHumdrum():
    masterStream = music21.humdrum.parseData(humdrumTestFiles.mazurka6).stream

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

def timeISMIR():
    s1 = corpus.parseWork('bach/bwv248')
    post = s1.musicxml



#-------------------------------------------------------------------------------
# handler
class CallGraph:

    def __init__(self):
        self.excludeList = ['pycallgraph.*','re.*','sre_*', 'copy*', '*xlrd*']
        #excludeList += ['*meter*', 'encodings*', '*isClass*', '*duration.Duration*']

        # might set test function from a string
        self.testFunction = timeISMIR

    def run(self):
        fp = environLocal.getTempFile('.png')
        gf = pycallgraph.GlobbingFilter(exclude=self.excludeList)

        # start timer
        t = common.Timer()
        t.start()

        pycallgraph.start_trace(filter_func = gf)
        self.testFunction() # run routine

        pycallgraph.stop_trace()
        pycallgraph.make_dot_graph(fp)

        print('elpased time: %s' % t)
        # open the completed file
        environLocal.launch('png', fp)


if __name__ == '__main__':

    cg = CallGraph()
    cg.run()



