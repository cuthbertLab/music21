
from music21 import *

stream = converter.parseFile('A_mov6.mei', None, 'mei', True)

for i in stream.recurse().getInstruments():
    print(i)

stream.write('midi', 'written.midi')
stream.toSoundingPitch(inPlace=True)
stream.write('midi', 'sounding.midi')