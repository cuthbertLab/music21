
def assembleLyrics(streamIn):
    word = []; words = []
    noteStream = streamIn.flat.getNotes()
    for n in noteStream:
        for lyricObj in n.lyrics: # a list of lyric objs
            if lyricObj.syllabic in ['begin', 'middle']:
                word.append(lyricObj.text)
            elif lyricObj.syllabic in ['end', 'single']:
                word.append(lyricObj.text)
                words.append(''.join(word))
                word = []
    return ' '.join(words)
        