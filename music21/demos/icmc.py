def showDots():
    import music21
    from music21 import corpus, meter, note
    
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
            n.lyrics = []
            for i in range(ts.getBeatDepth(n.offset)):
                n.lyrics.append(note.Lyric('.', i+1))
    
    partBass.measures[0:7].show('musicxml') 

showDots()