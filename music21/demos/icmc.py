def showDots():
    import music21
    from music21 import corpus, meter
    
    score = corpus.parseWork('bach/bwv281.xml') 
    partBass = score[3]
    ts = partBass.flat.getElementsByClass(
         meter.TimeSignature)[0]
    
    ts.beat.partition(1)
    for h in range(len(ts.beat)):
        ts.beat[h] = ts.beat[h].subdivide(2)
        for i in range(len(ts.beat[h])):
            ts.beat[h][i] = \
                ts.beat[h][i].subdivide(2)
            for j in range(len(ts.beat[h][i])):
                ts.beat[h][i][j] = \
                    ts.beat[h][i][j].subdivide(2)
    
    for m in partBass.measures:
        for n in m.notes:
            for i in range(ts.getBeatDepth(n.offset)):
                n.addLyric('.')
    
    partBass.measures[0:7].show() 

def findRaisedSevenths():
    import music21
    from music21 import corpus, meter, stream, note
    from music21.note import Lyric

    score = corpus.parseWork('bach/bwv366.xml')  
    ts = score.flat.getElementsByClass(
        meter.TimeSignature)[0]
    ts.beat.partition(3)

    found = stream.Stream()
    count = 0
    for part in score:
        found.insert(count, 
            part.flat.getElementsByClass(
            music21.clef.Clef)[0])
        for i in range(len(part.measures)):
            m = part.measures[i]
            for n in m.notes:
                if n.name == 'C#': 
                    n.addLyric('%s, m. %s' % (          
        part.getInstrument().partName[0], 
        m.measureNumber))
                    n.addLyric('beat %s' %
        ts.getBeat(n.offset))
                    found.insert(count, n)
                    count += 4

    found.show('musicxml')

if __name__ == "__main__":
    showDots()
    findRaisedSevenths()