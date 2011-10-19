'''
Parses the de Clercq-Temperley popular music flavor of RomanText
'''

testfile1 = '''
A: I | | ii | vi |
B: I | ii . IV V7/vi | vi | I |

In: I V6 vi I64 | ii65 V43/ii ii vi6 bVIId7 . VId7 . | V |
Vr: $A $B
Br: ii | I | ii | vi | ii | vi | V/V | V7 |

S: [Bb] $In $Vr*3 $Br $Vr I |
'''

import copy
import re

import music21


def convertCTRTstr(fileString):
    '''
    converts a string containing the de Clercq Temperley popular music flavor of RomanText
    to a :class:~`music21.stream.Score` object.  Subsections of the piece are stored in
    a property called `subsections` containing a dictionary of subsections whose
    keys are the subsection name ('Vr' for verse, for instance) and whose value is 
    a :class:~`music21.stream.Stream` object
    
    Beth -- test code here...
    '''

    allSubsections = {}
    currentSubsectionName = None
    currentSubsectionContents = None
    scoreObj = music21.stream.Score()
    currentKey = None
    
    for atom in fileString.split():
        if atom.endswith(':'):
            if currentSubsectionName is not None:
                allSubsections[currentSubsectionName] = currentSubsectionContents
            currentSubsectionName = atom[0:-1]
            if currentSubsectionName.upper() == 'S':
                # special, score object
                currentSubectionName = 'S' # replace with title of piece
                currentSubsectionContents = scoreObj
            else:
                currentSubsectionContents = music21.stream.Stream()
        elif atom.startswith('$'):
            referencedSubsection = atom[1:]
            match = re.search('^(.*)\*(\d+)', referencedSubsection)
            if match:
                numRepeat = int(match.group(2))
                referencedSubsection = match.group(1)
            else:
                numRepeat = 1
            
            if referencedSubsection not in allSubsections:
                raise ClercqTemperleyException('Could not find referenced subsection %s in score (referenced before defined?)' % referencedSubsection)
            else:
                for i in range(numRepeat):
                    for refEl in allSubsections[referencedSubsection]:
                        currentSubsectionContents.append(copy.deepcopy(refEl))
        elif atom.startswith('[') and atom.endswith(']'):
            atomContents = atom[1:-1]
            if re.match('[a-zA-Z]', atomContents):
                m21keyStr = music21.key.convertKeyStringToMusic21KeyString(atomContents)
                currentKey = music21.key.Key(m21keyStr)
                currentSubsectionContents.append(currentKey) 
            else:
                pass # BETH: Meter (and rhythm throughout...)
        elif atom != '|' and atom != ".":
            try:
                if currentKey is None:
                    rn = music21.roman.RomanNumeral(atom)
                else:
                    rn = music21.roman.RomanNumeral(atom, currentKey)
                currentSubsectionContents.append(rn)
            except Exception, e:
                print "invalid atom: " + str(atom) + "exception: " + str(e)

    # reparse currentKey for all romanNumerals because key could be defined in S while RN objects were created in subsection
    currentKey = None
    for el in scoreObj:
        if 'Key' in el.classes:
            currentKey = el
        elif 'RomanNumeral' in el.classes:
            el.setKeyOrScale(currentKey)
            el.lyric = el.figure
    
    scoreObj.subsections = allSubsections
    return scoreObj

class ClercqTemperleyException(music21.Music21Exception):
    pass

if __name__ == '__main__':
    myScore = convertCTRTstr(testfile1)
    myScore.show()



    