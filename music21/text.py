#-------------------------------------------------------------------------------
# Name:         test.py
# Purpose:      music21 classes for text processing
#
# Authors:      Michael Scott Cuthbert
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
import doctest, unittest

import music21 ## needed to properly do isinstance checking



def assembleLyrics(streamIn):
    '''Concatenate text from a stream.
    '''
    word = []; words = []
    noteStream = streamIn.flat.notes
    for n in noteStream:
        for lyricObj in n.lyrics: # a list of lyric objs
            #print lyricObj, lyricObj.syllabic, lyricObj.text
            # need to match case of non-defined syllabic attribute
            if lyricObj.syllabic in ['begin', 'middle']:
                word.append(lyricObj.text)
            elif lyricObj.syllabic in ['end', 'single', None]:
                word.append(lyricObj.text)
                words.append(''.join(word))
                word = []
    return ' '.join(words)
        






#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        from music21 import converter, corpus

        a = converter.parse(corpus.getWork('haydn/opus74no2/movement4.xml'))
        post = assembleLyrics(a)
        self.assertEqual(post, '') # no lyrics!

        a = converter.parse(corpus.getWork('luca/gloria'))
        post = assembleLyrics(a)
        self.assertEqual(post.startswith('Et in terra pax hominibus bone voluntatis'), True) 



if __name__ == "__main__":
    music21.mainTest(Test)






