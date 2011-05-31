from music21.pitch import Pitch

class HashablePitch(Pitch):
    def __hash__(self):
        return hash(self.fullName)
    