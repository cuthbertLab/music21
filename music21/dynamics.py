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
        self.posDefaultX = None
        self.posDefaultY = None
        self.posRelativeX = -36 # this value provides good 16th note alignment
        self.posRelativeY = None
        self.posPlacement = 'below' # attr in mxDirection, below or above


    def __repr__(self):
        return "<music21.dynamics.Dynamic %s >" % self.value


    def _getMX(self):
        return musicxmlTranslate.dyanmicToMx(self)
#         '''
#         returns a musicxml.Direction object
# 
#         >>> from music21 import *
#         >>> a = dynamics.Dynamic('ppp')
#         >>> a.posRelativeY = -10
#         >>> b = a.mx
#         >>> b[0][0][0].get('tag')
#         'ppp'
#         >>> b.get('placement')
#         'below'
#         '''
#         mxDynamicMark = musicxml.DynamicMark(self.value)
#         mxDynamics = musicxml.Dynamics()
#         for src, dst in [(self.posDefaultX, 'default-x'), 
#                          (self.posDefaultY, 'default-y'), 
#                          (self.posRelativeX, 'relative-x'),
#                          (self.posRelativeY, 'relative-y')]:
#             if src != None:
#                 mxDynamics.set(dst, src)
#         mxDynamics.append(mxDynamicMark) # store on component list
#         mxDirectionType = musicxmlMod.DirectionType()
#         mxDirectionType.append(mxDynamics)
#         mxDirection = musicxmlMod.Direction()
#         mxDirection.append(mxDirectionType)
#         mxDirection.set('placement', self.posPlacement)
#         return mxDirection

    def _setMX(self, mxDirection):
        musicxmlTranslate.mxToDynamic(mxDirection, self)

#         '''Given an mxDirection, load instance
# 
#         >>> from music21 import *
#         >>> mxDirection = musicxml.Direction()
#         >>> mxDirectionType = musicxml.DirectionType()
#         >>> mxDynamicMark = musicxml.DynamicMark('ff')
#         >>> mxDynamics = musicxml.Dynamics()
#         >>> mxDynamics.set('default-y', -20)
#         >>> mxDynamics.append(mxDynamicMark)
#         >>> mxDirectionType.append(mxDynamics)
#         >>> mxDirection.append(mxDirectionType)
#         >>> a = Dynamic()
#         >>> a.mx = mxDirection
#         >>> a.value
#         'ff'
#         >>> a.posDefaultY
#         -20
#         >>> a.posPlacement
#         'below'
#         '''
#         mxDynamics = None
#         for mxObj in mxDirection:
#             if isinstance(mxObj, musicxmlMod.DirectionType):
#                 for mxObjSub in mxObj:
#                     if isinstance(mxObjSub, musicxmlMod.Dynamics):
#                         mxDynamics = mxObjSub
#         if mxDynamics == None:
#             raise DynamicException('when importing a Dyanmics object from MusicXML, did not find a DyanmicMark')            
#         if len(mxDynamics) > 1:
#             raise DynamicException('when importing a Dyanmics object from MusicXML, found more than one DyanmicMark contained')
# 
#         # palcement is found in outermost object
#         if mxDirection.get('placement') != None:
#             self.posPlacement = mxDirection.get('placement') 
# 
#         # the tag is the dynmic mark value
#         mxDynamicMark = mxDynamics.componentList[0].get('tag')
#         self.value = mxDynamicMark
#         for dst, src in [('posDefaultX', 'default-x'), 
#                          ('posDefaultY', 'default-y'), 
#                          ('posRelativeX', 'relative-x'),
#                          ('posRelativeY', 'relative-y')]:
#             if mxDynamics.get(src) != None:
#                 setattr(self, dst, mxDynamics.get(src))

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
 

#         mxDirection = self._getMX()
# 
#         mxMeasure = musicxml.Measure()
#         mxMeasure.setDefaults()
#         mxMeasure.append(mxDirection)
# 
#         mxPart = musicxml.Part()
#         mxPart.setDefaults()
#         mxPart.append(mxMeasure)
#         mxScorePart = musicxml.ScorePart()
#         mxScorePart.setDefaults()
#         mxPartList = musicxml.PartList()
#         mxPartList.append(mxScorePart)
#         mxIdentification = musicxml.Identification()
#         mxIdentification.setDefaults() # will create a composer
#         mxScore = musicxml.Score()
#         mxScore.setDefaults()
#         mxScore.set('partList', mxPartList)
#         mxScore.set('identification', mxIdentification)
#         mxScore.append(mxPart)
# 
#         return mxScore.xmlStr()

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
        # relative-y and relative-x are also defined in xml
        self.posPlacement = 'below' # defined in mxDirection

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
        mxDirection.set('placement', self.posPlacement)
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
            self.posPlacement = mxDirection.get('placement') 

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
        a = corpus.parseWork('opus41no1/movement2') # has dynamics!
        b = a[0].flat.getElementsByClass(music21.dynamics.Dynamic)
        self.assertEquals(len(b), 35)

        b = a[0].flat.getElementsByClass(music21.dynamics.Wedge)
        self.assertEquals(len(b), 4)


    def testMusicxmlOutput(self):
        # test direct rendering of musicxml
        d = Dynamic('p')
        xmlout = d.musicxml
        match = '<p/>'
        self.assertEquals(xmlout.find(match), 888)


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Dynamic, Wedge]

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        # arg[1] is test to launch
        if hasattr(t, sys.argv[1]): getattr(t, sys.argv[1])()


#------------------------------------------------------------------------------
# eof

