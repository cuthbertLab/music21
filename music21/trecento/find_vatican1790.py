'''Search for Vatican 1790 missing piece: find all ballatas in triple time'''

from music21 import lily
from music21.trecento import cadencebook

def find():
    ballatas = cadencebook.BallataSheet()
    allLily = lily.LilyString()
    for ballata in ballatas:
        if (ballata.timeSigBegin == "6/8" or ballata.timeSigBegin == "9/8"):
            incipit = ballata.incipit
            if incipit != None:
                iLily = incipit.lily
                allLily = allLily + iLily
    allLily.showPDF()

if __name__ == "__main__":
    find()