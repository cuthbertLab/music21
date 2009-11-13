from music21.noteStream import Stream
from music21.twoStreams import TwoStreamComparer
from music21.note import Note

(n11,n12,n13,n14) = (Note(), Note(), Note(), Note())
(n21,n22,n23,n24) = (Note(), Note(), Note(), Note())
n11.step = "C"
n12.step = "D"
n13.step = "E"
n14.step = "F"
n21.step = "G"
n22.step = "A"
n23.step = "B"
n24.step = "C"
n24.octave = 5

n11.duration.type = "half"
n12.duration.type = "whole"
n13.duration.type = "eighth"
n14.duration.type = "half"

n21.duration.type = "half"
n22.duration.type = "eighth"
n23.duration.type = "whole"
n24.duration.type = "eighth"

stream1 = Stream([n11,n12,n13,n14])
stream2 = Stream([n21,n22,n23,n24])
twoStream1 = TwoStreamComparer(stream1, stream2)
attackedTogether = twoStream1.attackedTogether()
assert len(attackedTogether) == 3  # nx1, nx2, nx4
assert attackedTogether[1][1] == n22

playingWhenSounded = twoStream1.playingWhenSounded(n23)
assert playingWhenSounded == n12

allPlayingWhileSounded = twoStream1.allPlayingWhileSounded(n14)
assert allPlayingWhileSounded == [n24]

exclusivePlayingWhileSounded = \
     twoStream1.exclusivePlayingWhileSounded(n12)
assert exclusivePlayingWhileSounded == [n22]

trimPlayingWhileSounded = \
     twoStream1.trimPlayingWhileSounded(n12)
assert trimPlayingWhileSounded[0] == n22
assert trimPlayingWhileSounded[1].duration.quarterLength == 3.5

#ballataObj = BallataSheet()
#randomPiece = ballataObj.makeWork(random.randint(231, 312) # landini a-l
#trecentoStreams =  randomPiece.incipitStreams()

### test your objects on these two streams


