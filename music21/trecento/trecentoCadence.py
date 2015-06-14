# -*- coding: utf-8 -*-

import unittest
import re
import copy

from music21 import tinyNotation
from music21 import note
from music21 import expressions

def _sendNoteInfo(music21noteObject):
    '''
    Debugging method to print information about a music21 note
    called by trecento.trecentoCadence, among other places
    '''
    retstr = ""
    a = music21noteObject
    if (isinstance(a, note.Note)):
        retstr += "Name: " + a.name + "\n"
        retstr += "Step: " + a.step + "\n"
        retstr += "Octave: " + str(a.octave) + "\n"
        if (a.accidental is not None):
            retstr += "Accidental: " + a.accidental.name + "\n"
    else:
        retstr += "Is a rest\n"
    if (a.tie is not None):
        retstr += "Tie: " + a.tie.type + "\n"
    retstr += "Duration Type: " + a.duration.type + "\n"
    retstr += "QuarterLength: " + str(a.duration.quarterLength) + "\n"
    if len(a.duration.tuplets) > 0:
        retstr += "Is a tuplet\n"
        if a.duration.tuplets[0].type == "start":
            retstr += "   in fact STARTS the tuplet group\n"
        elif a.duration.tuplets[0].type == "stop":
            retstr += "   in fact STOPS the tuplet group\n"
    if len(a.expressions) > 0:
        if (isinstance(a.expressions[0], expressions.Fermata)):
            retstr += "Has a fermata on it\n"
    return retstr




class CadenceNoteToken(tinyNotation.NoteToken):
    '''
    Subclass of TinyNotationNote where 2.. represents a dotted dotted half note (that is, a dotted
    half tied to a dotted quarter) instead of a double dotted note.  This makes entering Trecento
    music (which uses this note value often) much easier.  1.. and 4.. etc. are similarly transformed. 
    '''
    def dots(self, n, search, pm, t, parent):
        '''
        adds the appropriate number of dots to the right place.
        
        Subclassed in TrecentoNotation where two dots has a different meaning.
        '''
        dots = len(search.group(1))
        if dots == 1:
            n.duration.dots = 1
        elif dots == 2:
            n.duration.dotGroups = [1, 1]
        t = re.sub(pm, '', t)
        return t

class CadenceRestToken(tinyNotation.RestToken):
    '''
    Subclass of TinyNotationNote where 2.. represents a dotted dotted half note (that is, a dotted
    half tied to a dotted quarter) instead of a double dotted note.  This makes entering Trecento
    music (which uses this note value often) much easier.  1.. and 4.. etc. are similarly transformed. 
    '''
    def dots(self, n, search, pm, t, parent):
        '''
        adds the appropriate number of dots to the right place.
        
        Subclassed in TrecentoNotation where two dots has a different meaning.
        '''
        dots = len(search.group(1))
        if dots == 1:
            n.duration.dots = 1
        elif dots == 2:
            n.duration.dotGroups = [1, 1]
        t = re.sub(pm, '', t)
        return t



class CadenceConverter(tinyNotation.Converter):
    '''
    Subclass of Tiny Notation that calls TrecentoCadenceNote instead of TinyNotationNote    
    
    
    >>> dLucaGloriaIncipit = trecento.trecentoCadence.CadenceConverter("6/8 c'2. d'8 c'4 a8 f4 f8 a4 c'4 c'8").parse().stream
    >>> dLucaGloriaIncipit.rightBarline = 'final'
    >>> dLucaGloriaIncipit.elements
    (<music21.stream.Measure 1 offset=0.0>, <music21.stream.Measure 2 offset=3.0>, <music21.stream.Measure 3 offset=6.0>)
    '''
    tokenMap = [
                (r'(\d+\/\d+)', tinyNotation.TimeSignatureToken),
                (r'r(\S*)', CadenceRestToken),
                (r'(\S*)', CadenceNoteToken), # last
    ]

###### test routines

class Test(unittest.TestCase):

    def runTest(self):
        pass
    
    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys
        for part in sys.modules[self.__module__].__dict__:
            if part.startswith('_') or part.startswith('__'):
                continue
            elif part in ['Test', 'TestExternal']:
                continue
            elif callable(part):
                #environLocal.printDebug(['testing copying on', part])
                obj = getattr(self.__module__, part)()
                a = copy.copy(obj)
                b = copy.deepcopy(obj)
                self.assertNotEqual(a, obj)
                self.assertNotEqual(b, obj)


    def testDotGroups(self):
        cn = CadenceConverter('c#2..')
        cn.parse()
        
        a = cn.stream.flat.notes[0] # returns the stored music21 note.
        self.assertEqual(a.name, 'C#')
        self.assertEqual(a.duration.type, 'half')
        self.assertEqual(a.duration.dotGroups, (1,1))
        self.assertEqual(a.duration.quarterLength, 4.5)

    
class TestExternal(unittest.TestCase):
    '''
    These objects generate PNGs, etc.
    '''
    def runTest(self):
        pass
    
    def testTrecentoLine(self):
        '''
        should display a 6 beat long line with some triplets
        '''
        st = CadenceConverter('e2 f8 e f trip{g16 f e} d8 c B trip{d16 c B}').parse().stream
        #for thisNote in st:
        #    print _sendNoteInfo(thisNote)
        #    print "--------"
        self.assertAlmostEqual(st.duration.quarterLength, 6.0)
        st.show()
    
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

