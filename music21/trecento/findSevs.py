import music21
from music21 import *
from music21 import lily
from music21.trecento import cadencebook
#this is a terrible way of doing this...
from music21.trecento import find_vatican1790 
from music21.trecento.find_vatican1790 import *
from music21.lily import *

def find():
    ballatas = cadencebook.BallataSheet()
    alllily = ''
    for ballata in ballatas:
        #print ballata.fischerNum
#        try:
            if findinwork(ballata):
                alllily = alllily + ballata.getAllLily()
                print(ballata.title + ' has a seventh somewhere')
#        except:
#            pass
    lS = lily.LilyString("{" + alllily + "}")
    lS.showPDF()
    #makePDF(alllily)
    #print alllily

def findinwork(work):
    ballata = work
    streams = ballata.getAllStreams()
    containssev = False
    for astream in streams:
        intervals = astream.intervalOverRestsList
        genints = []
        for interval in intervals:
            if interval is not None:
                genints.append(interval.generic)
                if interval.generic == 7:
                    containssev = True
                    streamLily = astream.lily
                    lS = lily.Lilystring("{" + streamLily + "}")
                    lS.showPNG()
                    print(interval.note1.lilyName + ' -- ' + interval.note2.lilyName)
                    #interval.note1.editorial.color = "blue" #this doesn't actually work yet....
                    #interval.note2.editorial.color = "blue"
    return containssev

def findinwork2(work):
    snippets = work.snippetBlocks
    streamLily = ''
    for thisCadence in snippets:
        if thisCadence is not None:
            for astream in thisCadence.streams:
                intervals = astream.intervalOverRestsList
                genints = []
                for interval in intervals:
                    if interval is not None:
                        genints.append(interval.generic)
                        if interval.generic.undirected == 7:
                            streamLily += "\\score {" + \
                                "<< \\time " + str(thisCadence.timeSig) + \
                                "\n \\new Staff {" + astream.lily + "} >>" + \
                                thisCadence.header() + "\n}\n"
                            print("found sev")
    #lily.showPDF(streamLily)
    return streamLily

def findsixinwork(work):
    snippets = work.snippetBlocks
    streamLily = ''
    for thisCadence in snippets:
        if thisCadence is not None:
            for astream in thisCadence.streams:
                intervals = astream.intervalOverRestsList
                genints = []
                for interval in intervals:
                    if interval is not None:
                        genints.append(interval.generic)
                        if interval.generic.undirected == 6:
                            streamLily += "\\score {" + \
                                "<< \\time " + str(thisCadence.timeSig) + \
                                "\n \\new Staff {" + astream.lily + "} >>" + \
                                thisCadence.header() + "\n}\n"
                            print("found six")
    #lily.showPDF(streamLily)
    return streamLily    

def findintervalinwork(work, intervalnum):
    snippets = work.snippetBlocks
    streamLily = ''
    for thisCadence in snippets:
        if thisCadence is not None:
            for astream in thisCadence.streams:
                intervals = astream.intervalOverRestsList
                genints = []
                for interval in intervals:
                    if interval is not None:
                        genints.append(interval.generic)
                        if interval.generic.undirected == intervalnum:
                            streamLily += "\\score {" + \
                                "<< \\time " + str(thisCadence.timeSig) + \
                                "\n \\new Staff {" + astream.lily + "} >>" + \
                                thisCadence.header() + "\n}\n"
                            print("found " + str(intervalnum))
    #lily.showPDF(streamLily)
    return streamLily    

    

def test1(row):
    ballatas = cadencebook.BallataSheet()
    work = ballatas.makeWork(row)
    if findinwork(work):
        sevlily = work.getAllLily()
        lS = lily.LilyString(sevlily)
        lS.showPNG()
        print('done')
        
        
def findsevinrange(startrow, endrow):
    ballatas = cadencebook.BallataSheet()
    streamLily = ''
    for row in range(startrow, endrow):
        print(row)
        work = ballatas.makeWork(row)
        streamLily += findinwork2(work)
    if streamLily != '':
        lS = lily.LilyString(streamLily)
        lS.showPDF()
    print('done')

def test3(row):
    ballatas = cadencebook.BallataSheet()
    work = ballatas.makeWork(row)
    findinwork2(work)
    print('done')
    
def findsixinrange(startrow, endrow):
    ballatas = cadencebook.BallataSheet()
    streamLily = ''
    for row in range(startrow, endrow):
        print(row)
        work = ballatas.makeWork(row)
        streamLily += findsixinwork(work)
    if streamLily != '':
        lS = lily.LilyString(streamLily)
        lS.showPDF()
    print('done')
    
def findintervalinrange(startrow, endrow, intervalnum, makePDF=True):
    ballatas = cadencebook.BallataSheet()
    streamLily = ''
    for row in range(startrow, endrow):
        print(row)
        work = ballatas.makeWork(row)
        streamLily += findintervalinwork(work, intervalnum)
    if streamLily != '':
        if makePDF:
            lS = lily.LilyString(streamLily)
            lS.showPDF()
    print('done')

if __name__ == "__main__":
    find()