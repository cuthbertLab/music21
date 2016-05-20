
from music21 import *

stream = converter.parseFile('minimal.mei', None, 'mei', True)

for i in stream.recurse().getInstruments():
    print(i)

stream.write('midi', 'written.midi')
stream.toSoundingPitch(inPlace=True)
stream.write('midi', 'sounding.midi')
print(pitch.Pitch('G10'))