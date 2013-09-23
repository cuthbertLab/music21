def realizeOrnaments(s):        
    '''
    Realize all ornaments on a stream

    Creates a new stream that contains all realized ornaments in addition
    to other elements in the original stream.
    
    
    >>> s1 = stream.Stream()
    >>> m1 = stream.Measure()
    >>> m1.timeSignature = meter.TimeSignature("4/4")
    >>> n1 = note.WholeNote("C4")
    >>> n1.expressions.append(expressions.Mordent())
    >>> m1.append(n1)
    >>> m2 = stream.Measure()
    >>> n2 = note.WholeNote("D4")
    >>> m2.append(n2)
    >>> s1.append(m1)
    >>> s1.append(m2)
    >>> s1.recurse()
    [<music21.stream.Stream ...>, <music21.stream.Measure 0 offset=0.0>, <music21.meter.TimeSignature 4/4>, <music21.note.Note C>, <music21.stream.Measure 0 offset=4.0>, <music21.note.Note D>]
    >>> s2 = s1.realizeOrnaments()
    >>> s2.recurse()
    [<music21.stream.Stream ...>, <music21.stream.Measure 0 offset=0.0>, <music21.meter.TimeSignature 4/4>, <music21.note.Note C>, <music21.note.Note B>, <music21.note.Note C>, <music21.stream.Measure 0 offset=4.0>, <music21.note.Note D>] 
    '''
    newStream = s.__class__()
    newStream.offset = s.offset
    
    # IF this streamObj contains more streams (ie, a Part that contains multiple measures)
    recurse = s.recurse(streamsOnly = True)
    
    if len(recurse) > 1:
        i = 0
        for innerStream in recurse:
            if i > 0:
                newStream.append(innerStream.realizeOrnaments())
            i = i + 1
    else:
        for element in s:
            if hasattr(element, "expressions"):
                realized = False
                for exp in element.expressions:
                    if hasattr(exp, "realize"): 
                        newNotes = exp.realize(element)
                        realized = True
                        for n in newNotes: newStream.append(n)
                if not realized:
                    newStream.append(element)
            else:
                newStream.append(element)
    
    return newStream
