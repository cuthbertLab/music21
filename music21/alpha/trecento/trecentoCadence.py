# -*- coding: utf-8 -*-

import unittest
import re
import copy

from music21 import tinyNotation

from music21 import environment
environLocal = environment.Environment()

class DotsMixin():
    def dots(self, n, search, pm, t, parent):
        '''
        adds the appropriate number of dots to the right place.
        '''
        dots = len(search.group(1))
        if dots == 1:
            n.duration.dots = 1
        elif dots == 2:
            n.duration.dotGroups = (1, 1)
        t = re.sub(pm, '', t)
        return t

class CadenceNoteToken(DotsMixin, tinyNotation.NoteToken):
    '''
    Subclass of NoteToken where 2.. represents a dotted dotted half note (that is, a dotted
    half tied to a dotted quarter) instead of a double dotted note.  This makes entering Trecento
    music (which uses this note value often) much easier.  1.. and 4.. etc. 
    are similarly transformed. 
    '''

class CadenceRestToken(DotsMixin, tinyNotation.RestToken):
    '''
    Subclass of RestToken where 2.. represents a dotted dotted half rest.
    
    See CadenceNoteToken for details 
    '''

class CadenceConverter(tinyNotation.Converter):
    '''
    Subclass of Tiny Notation that calls these tokens instead of the defaults    
    
    
    >>> dLucaGloriaIncipit = alpha.trecento.trecentoCadence.CadenceConverter(
    ...     "6/8 c'2. d'8 c'4 a8 f4 f8 a4 c'4 c'8").parse().stream
    >>> dLucaGloriaIncipit.rightBarline = 'final'
    >>> dLucaGloriaIncipit.elements
    (<music21.stream.Measure 1 offset=0.0>, 
     <music21.stream.Measure 2 offset=3.0>, 
     <music21.stream.Measure 3 offset=6.0>)
    '''
    def __init__(self, stringRep=""):
        super(CadenceConverter, self).__init__(stringRep)
        self.tokenMap = [
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
        self.assertAlmostEqual(st.duration.quarterLength, 6.0)
        st.show()
    
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

