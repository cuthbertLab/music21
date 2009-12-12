#-------------------------------------------------------------------------------
# Name:         stream.py
# Purpose:      base clases for dealing with groups of positioned objects
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


import unittest, doctest

import music21
from music21 import musicxml
musicxmlMod = musicxml # alias as to avoid name conflicts

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


class Dynamic(music21.Music21Object):
    '''
    class to deal with dynamics
    '''
    
    def __init__(self, value = None):
        music21.Music21Object.__init__(self)

        self.value = value
        if self.value in longNames:
            self.longName = longNames[self.value]
        else:
            self.longName = None
        if self.value in englishNames:
            self.englishName = englishNames[self.value]
        else:
            self.englishName = None

    def __repr__(self):
        return "<music21.dynamics.Dynamic %s >" % self.value



    def _getMX(self):
        '''
        returns a musicxml.DynamicMark object
        '''
        mxDynamicMark = musicxml.DynamicMark(self.value)
        return mxDynamicMark

    def _setMX(self, mxDynamicMark):
        '''
        given an mxDynamicMark, load instance

        >>> mxDynamicMark = musicxml.DynamicMark('ff')
        >>> a = Dynamic()
        >>> a.mx = mxDynamicMark
        >>> a.value
        'ff'
        '''
        self.value = mxDynamicMark.get('tag')

    mx = property(_getMX, _setMX)




    def _getMusicXML(self):
        '''Provide a complete MusicXM: representation. Presently, this is based on 
        '''
        mxDynamicMark = self._getMX()

        mxDynamics = musicxml.Dynamics()
        mxDynamics.append(mxDynamicMark)

        mxDirectionType = musicxml.DirectionType()
        mxDirectionType.append(mxDynamics)

        mxDirection = musicxml.Direction()
        mxDirection.append(mxDirectionType)

        mxMeasure = musicxml.Measure()
        mxMeasure.setDefaults()
        mxMeasure.append(mxDirection)

        mxPart = musicxml.Part()
        mxPart.setDefaults()
        mxPart.append(mxMeasure)
        mxScorePart = musicxml.ScorePart()
        mxScorePart.setDefaults()
        mxPartList = musicxml.PartList()
        mxPartList.append(mxScorePart)
        mxIdentification = musicxml.Identification()
        mxIdentification.setDefaults() # will create a composer
        mxScore = musicxml.Score()
        mxScore.setDefaults()
        mxScore.set('partList', mxPartList)
        mxScore.set('identification', mxIdentification)
        mxScore.append(mxPart)

        return mxScore.xmlStr()

    def _setMusicXML(self, mxNote):
        '''
        '''
        pass

    musicxml = property(_getMusicXML, _setMusicXML)









class Wedge(music21.Music21Object):
    '''
    class to deal with dynamics
    '''
    
    def __init__(self, value = None):
        music21.Music21Object.__init__(self)
        # use ineherited duration to show length n time
        self.type = None # crescendo, stop, or diminuendo
        self.spread = None
        # relative-y and relative-x are also defined in xml

    def _getMX(self):
        '''
        returns a musicxml.DynamicMark object
        >>> a = Wedge()
        >>> a.type = 'crescendo'
        >>> mxWedge = a.mx
        >>> mxWedge.get('type')
        'crescendo'
        '''
        mxWedge = musicxml.Wedge()
        mxWedge.set('type', self.type)
        mxWedge.set('spread', self.spread)
        return mxWedge


    def _setMX(self, mxWedge):
        '''
        given an mxDynamicMark, load instance

        >>> mxWedge = musicxml.Wedge()
        >>> mxWedge.set('type', 'crescendo')
        >>> a = Wedge()
        >>> a.mx = mxWedge
        >>> a.type
        'crescendo'
        '''
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

if __name__ == "__main__":
    music21.mainTest(Test)