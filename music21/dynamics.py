#-------------------------------------------------------------------------------
# Name:         stream.py
# Purpose:      base clases for dealing with groups of positioned objects
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Classes and functions for creating and manipulating dynamic symbols. Rather than subclasses, the :class:`~music21.dynamics.Dynamic` object is often specialized by parameters. 
'''

import unittest, doctest
import copy

import music21
from music21 import musicxml as musicxmlMod 
from music21.musicxml import translate as musicxmlTranslate
from music21 import common
from music21 import environment
_MOD = 'dynamics.py'
environLocal = environment.Environment(_MOD)



shortNames = ['pppppp','ppppp','pppp','ppp','pp','p','mp', 
                  'mf','f', 'fp', 'sf','ff','fff','ffff','fffff','ffffff']
longNames  = {'ppp': 'pianississimo',
              'pp': 'pianissimo',
              'p': 'piano',
              'mp': 'mezzopiano',
              'mf': 'mezzoforte',
              'f': 'forte',
              'fp': 'fortepiano',
              'sf': 'sforzando',
              'ff': 'fortissimo',
              'fff': 'fortississimo'}

## could be really useful for automatic description of musical events
englishNames  = {'ppp': 'extremely soft',
                 'pp': 'very soft',
                 'p': 'soft',
                 'mp': 'moderately soft',
                 'mf': 'moderately loud',
                 'f': 'loud',
                 'ff': 'very loud',
                 'fff': 'extremely loud'} 


def dynamicStrFromDecimal(n):
    '''
    Given a decimal from 0 to 1, return a string representing a dynamic
    with 0 being the softest (0.01 = 'ppp') and 1 being the loudest (0.9+ = 'fff')
    0 returns "n" (niente), while ppp and fff are the loudest dynamics used.
    
    >>> from music21 import *
    >>> dynamics.dynamicStrFromDecimal(0.25)
    'p'
    >>> dynamics.dynamicStrFromDecimal(1)
    'fff'
    '''
    if n == 0:
        return 'n'
    elif n > 0 and n < .1:
        return 'ppp'
    elif n >= .1 and n < .2:
        return 'pp'
    elif n >= .2 and n < .35:
        return 'p'
    elif n >= .35 and n < .5:
        return 'mp'
    elif n >= .5 and n < .65:
        return 'mf'
    elif n >= .65 and n < .8:
        return 'f'
    elif n >= .8 and n < .9:
        return 'ff'
    elif n >= .9:
        return 'fff'


class DynamicException(Exception):
    pass

class WedgeException(Exception):
    pass


class Dynamic(music21.Music21Object):
    '''Object representation of Dyanmics.
    
    >>> from music21 import *
    >>> pp1 = dynamics.Dynamic('pp')
    >>> pp1.value
    'pp'
    >>> pp1.longName
    'pianissimo'
    >>> pp1.englishName
    'very soft'
    
    Dynamics can also be specified on a 0 to 1 scale with 1 being the 
    loudest (see dynamicStrFromDecimal() above)
    
    >>> pp2 = dynamics.Dynamic(0.15) # on 0 to 1 scale
    >>> pp2.value
    'pp'
    '''
    
    classSortOrder = 10
    
    def __init__(self, value = None):
        music21.Music21Object.__init__(self)

        if not common.isStr(value):
            # assume it is a number, try to convert
            value = dynamicStrFromDecimal(value)

        self.value = value
        if self.value in longNames:
            self.longName = longNames[self.value]
        else:
            self.longName = None

        if self.value in englishNames:
            self.englishName = englishNames[self.value]
        else:
            self.englishName = None

        # for position, as musicxml, all units are in tenths of interline space
        # position is needed as default positions are often incorrect
        self._positionDefaultX = -36
        self._positionDefaultY = -80 # below top line
        # this value provides good 16th note alignment
        self._positionRelativeX = None
        self._positionRelativeY = None
        # this does not do anything if default y is defined
        self._positionPlacement = None

    def __repr__(self):
        return "<music21.dynamics.Dynamic %s >" % self.value


    def _getPositionVertical(self):
        return self._positionDefaultY
    
    def _setPositionVertical(self, value):
        if value is None:
            self._positionDefaultY = None
        else:
            try:
                value = float(value)
            except (ValueError):
                raise TextExpressionException('Not a supported size: %s' % value)
            self._positionDefaultY = value
    
    positionVertical = property(_getPositionVertical, _setPositionVertical, 
        doc = '''Get or set the the vertical position, where 0 is the top line of the staff and units are in 10ths of a staff space.

        >>> from music21 import *
        >>> te = expressions.TextExpression()
        >>> te.positionVertical = 10
        >>> te.positionVertical
        10.0
        ''')



    def _getMX(self):
        return musicxmlTranslate.dynamicToMx(self)

    def _setMX(self, mxDirection):
        musicxmlTranslate.mxToDynamic(mxDirection, self)

    mx = property(_getMX, _setMX)

    def _getMusicXML(self):
        '''Provide a complete MusicXML representation.
        '''
        from music21 import stream, note
        dCopy = copy.deepcopy(self)
        out = stream.Stream()
        out.append(dCopy)
        # call the musicxml property on Stream
        return out.musicxml
 
    musicxml = property(_getMusicXML)






class Wedge(music21.Music21Object):
    '''Object model of crescendeo/decrescendo wedges.
    '''
    
    def __init__(self, value = None):
        music21.Music21Object.__init__(self)
        # use inherited duration to show length n time
        # these correspond to start and stop
        self.type = None # crescendo, stop, or diminuendo
        self.spread = None

        # all musicxml-related positioning
        self._positionDefaultX = None
        self._positionDefaultY = None
        self._positionRelativeX = None
        self._positionRelativeY = None
        self._positionPlacement = 'below' # defined in mxDirection

    def _getMX(self):
        '''
        returns a musicxml.Direction object

        >>> from music21 import *
        >>> a = dynamics.Wedge()
        >>> a.type = 'crescendo'
        >>> mxDirection = a.mx
        >>> mxWedge = mxDirection.getWedge()
        >>> mxWedge.get('type')
        'crescendo'
        '''
        mxWedge = musicxmlMod.Wedge()
        mxWedge.set('type', self.type)
        mxWedge.set('spread', self.spread)

        mxDirectionType = musicxmlMod.DirectionType()
        mxDirectionType.append(mxWedge)
        mxDirection = musicxmlMod.Direction()
        mxDirection.append(mxDirectionType)
        mxDirection.set('placement', self._positionPlacement)
        return mxDirection


    def _setMX(self, mxDirection):
        '''
        given an mxDirection, load instance

        >>> from music21 import *
        >>> mxDirection = musicxml.Direction()
        >>> mxDirectionType = musicxml.DirectionType()
        >>> mxWedge = musicxml.Wedge()
        >>> mxWedge.set('type', 'crescendo')
        >>> mxDirectionType.append(mxWedge)
        >>> mxDirection.append(mxDirectionType)
        >>>
        >>> a = dynamics.Wedge()
        >>> a.mx = mxDirection
        >>> a.type
        'crescendo'
        '''
        if mxDirection.get('placement') != None:
            self._positionPlacement = mxDirection.get('placement') 

        mxWedge = mxDirection.getWedge()
        if mxWedge == None:
            raise WedgeException('no wedge found in MusicXML direction object')

        self.type = mxWedge.get('type')
        self.spread = mxWedge.get('spread')

    mx = property(_getMX, _setMX)




#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testSingle(self):
        a = Dynamic('ffff')
        a.show()

    def testBasic(self):
        '''present each dynamic in a single measure
        '''
        from music21 import stream
        a = stream.Stream()
        o = 0
        for dynStr in shortNames:
            b = Dynamic(dynStr)
            a.insert(o, b)
            o += 4 # increment
        a.show()



class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)


    def testBasic(self):
        nodyn = Dynamic()
        assert nodyn.longName is None
        
        pp = Dynamic('pp')
        self.assertEquals(pp.value, 'pp')
        self.assertEquals(pp.longName, 'pianissimo')
        self.assertEquals(pp.englishName, 'very soft')


    def testCorpusDyanmicsWedge(self):
        from music21 import corpus
        import music21
        a = corpus.parse('opus41no1/movement2') # has dynamics!
        b = a.parts[0].flat.getElementsByClass(music21.dynamics.Dynamic)
        self.assertEquals(len(b), 35)

        b = a.parts[0].flat.getElementsByClass(music21.dynamics.Wedge)
        self.assertEquals(len(b), 4)


    def testMusicxmlOutput(self):
        # test direct rendering of musicxml
        d = Dynamic('p')
        xmlout = d.musicxml
        match = '<p/>'
        self.assertEquals(xmlout.find(match), 885)


    def testDynamicsPositionA(self):
        from music21 import stream, note, dynamics
        s = stream.Stream()
        selections = ['pp', 'f', 'mf', 'fff']
        positions = [-20, 0, 20]
        for i in range(10):
            d = dynamics.Dynamic(selections[i%len(selections)])
            #d.positionVertical = positions[i%len(positions)]
            s.append(d)
            s.append(note.Note('c1'))
        #s.show()

    def testDynamicsPositionB(self):
        import random
        from music21 import stream, note, expressions, layout, dynamics
        s = stream.Stream()
        for i in range(6):
            m = stream.Measure(number=i+1)
            m.append(layout.SystemLayout(isNew=True))
            m.append(note.Rest(type='whole'))
            s.append(m)
        for m in s.getElementsByClass('Measure'):
            offsets = [x*.25 for x in range(16)]
            random.shuffle(offsets)
            offsets = offsets[:4]
            for o in offsets:
                d = dynamics.Dynamic('mf')
                d.positionVertical = 20
                m.insert(o, d)

        #s.show()



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Dynamic, Wedge]

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

