'''
Created on 25.02.2014

@author: Michael
'''
from music21 import *

#myNote = note.Note("F5")
#myClef = clef.TabClef()

#mystream = stream.Stream()
#mystream.append(myClef)
#mystream.append(myNote)

#mystream.show()

mXMLtest = converter.parse("C:/Users/Michael/Dropbox/Music21/test.xml") 
mXMLtest.show()

if __name__ == '__main__':
    pass