# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         dynamics.py
# Purpose:      Module for dealing with dynamics changes.
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Classes and functions for creating and manipulating dynamic symbols. Rather than 
subclasses, the :class:`~music21.dynamics.Dynamic` object is often specialized by parameters. 
'''

import unittest, doctest
import copy

import music21
from music21 import musicxml as musicxmlMod 
from music21.musicxml import translate as musicxmlTranslate
from music21 import common
from music21 import spanner

from music21 import environment
_MOD = 'dynamics.py'
environLocal = environment.Environment(_MOD)



shortNames = ['pppppp', 'ppppp', 'pppp', 'ppp', 'pp', 'p', 'mp',
                  'mf', 'f', 'fp', 'sf', 'ff', 'fff', 'ffff', 'fffff', 'ffffff']
longNames = {'ppp': 'pianississimo',
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
englishNames = {'ppp': 'extremely soft',
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
    'pp'
    >>> dynamics.dynamicStrFromDecimal(1)
    'fff'
    '''
    if n <= 0:
        return 'n'
    elif n < .11:
        return 'pppp'
    elif n < .16:
        return 'ppp'
    elif n < .26:
        return 'pp'
    elif n < .36:
        return 'p'
    elif n < .5:
        return 'mp'
    elif n < .65:
        return 'mf'
    elif n < .8:
        return 'f'
    elif n < .9:
        return 'ff'
    else:
        return 'fff'

# defaults used for volume scalar
dyanmicStrToScalar = {
             None: .5, # default value
              'n': 0,
              'pppp': 0.1,
              'ppp': .15,
              'pp': .25,
              'p': .35,
              'mp': .45,
              'mf': .55,
              'f': .7,
              'fp': .75,
              'sf': .85,
              'ff': .85,
              'fff': .9,
              'ffff': .95,
        }


#-------------------------------------------------------------------------------
class DynamicException(Exception):
    pass

class WedgeException(Exception):
    pass

#-------------------------------------------------------------------------------
class Dynamic(music21.Music21Object):
    '''
    Object representation of Dynamics.
    
    
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
    'ppp'
    >>> pp2.volumeScalar
    0.15
    
    Dynamics can be placed anywhere in a stream.
    
    
    >>> s = stream.Stream()
    >>> s.insert(0, note.HalfNote('E-4'))
    >>> s.insert(2, note.HalfNote('F#5'))
    >>> s.insert(0, dynamics.Dynamic('pp'))
    >>> s.insert(1, dynamics.Dynamic('mf'))
    >>> s.insert(3, dynamics.Dynamic('fff'))
    >>> #_DOCS_SHOW s.show()
    
    
    .. image:: images/dynamics_simple.*
        :width: 344

    
    '''
    classSortOrder = 10
    
    def __init__(self, value=None):
        music21.Music21Object.__init__(self)

        if not common.isStr(value):
            # assume it is a number, try to convert
            self.value = dynamicStrFromDecimal(value)
        else:
            self.value = value # will use property

        # the scalar is used to calculate the final output of a note
        # under this dynamic. if this property is set, it will override 
        # use of a default. 
        self._volumeScalar = None

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


    def _getValue(self):
        return self._value

    def _setValue(self, value):
        self._value = value
        if self._value in longNames:
            self.longName = longNames[self._value]
        else:
            self.longName = None

        if self._value in englishNames:
            self.englishName = englishNames[self._value]
        else:
            self.englishName = None

    value = property(_getValue, _setValue,
        doc='''Get or set the value of this dynamic, which sets the long and english names of this Dynamic. The value is a string specification. 
        ''')


    def _getVolumeScalar(self):
        if self._volumeScalar is not None:
            return self._volumeScalar
        # use default
        if self._value in dyanmicStrToScalar.keys():
            return dyanmicStrToScalar[self._value]
        return 

    def _setVolumeScalar(self, value):
        # we can manually set this to be anything, overriding defaults
        if common.isNum(value) and 0 >= value <= 1:
            self._volumeScalar = value
        else:
            raise DynamicException('cannot set as volume scalar to: %s', value)

    volumeScalar = property(_getVolumeScalar, _setVolumeScalar, doc=r'''
        Get or set the volume scalar for this dynamic. If not explicitly set, a default volume scalar will be provided. Any number between 0 and 1 can be used to set the volume scalar, overriding the expected behavior. 

        As mezzo is at .5, the unit interval range is doubled for generating final output. The default output is .5.

        >>> from music21 import *
        >>> d = dynamics.Dynamic('mf')
        >>> d.volumeScalar
        0.55...

        int(volumeScalar \* 127) gives the MusicXML <sound dynamics="x"/> tag 

        >>> print d.musicxml
        <?xml...
        <direction>
            <direction-type>
              <dynamics default-x="-36" default-y="-80">
                <mf/>
              </dynamics>
            </direction-type>
            <offset>0</offset>
            <sound dynamics="69"/>
        </direction>...
        ''')


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
        doc='''Get or set the the vertical position, where 0 is the top line of the staff and units are in 10ths of a staff space.

        >>> from music21 import *
        >>> te = expressions.TextExpression()
        >>> te.positionVertical = 10
        >>> te.positionVertical
        10.0
        ''')

    def _getMX(self):
        return musicxmlTranslate.dynamicToMx(self)

    def _setMX(self, mxDirection):
        # if applied in this fashion, only one dynamic can be set
        dynamicList = musicxmlTranslate.mxToDynamicList(mxDirection)
        target = dynamicList[0] # just get first in this case
        # manually transfer attrs to self
        for attr in ['value', '_positionPlacement', '_positionDefaultX', '_positionDefaultY', '_positionRelativeX', '_positionRelativeY']:
            setattr(self, attr, (getattr(target, attr)))


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



#-------------------------------------------------------------------------------
class DynamicWedge(spanner.Spanner):
    '''Common base-class for Crescendo and Diminuendo. 
    '''
    def __init__(self, *arguments, **keywords):
        spanner.Spanner.__init__(self, *arguments, **keywords)

        self.type = None # crescendo or diminuendo
        self.placement = 'below' # can above or below, after musicxml
        self.spread = 15 # this unit is probably in tenth

    def __repr__(self):
        msg = spanner.Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.DynamicWedge ')
        return msg

class Crescendo(DynamicWedge):
    '''A spanner crescendo wedge.

    >>> from music21 import dynamics
    >>> d = dynamics.Crescendo()
    >>> d.getStartParameters()
    {'spread': 0, 'type': 'crescendo'}
    >>> d.getEndParameters()
    {'spread': 15, 'type': 'stop'}
    '''
    def __init__(self, *arguments, **keywords):
        DynamicWedge.__init__(self, *arguments, **keywords)
        self.type = 'crescendo'

    def __repr__(self):
        msg = spanner.Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.Crescendo ')
        return msg

    def getStartParameters(self):
        '''Return the parameters for the start of this spanner
        ''' 
        post = {}
        post['type'] = self.type # cresc 
        post['spread'] = 0 # start at zero
        return post

    def getEndParameters(self):
        '''Return the parameters for the start of this spanner
        ''' 
        post = {}
        post['type'] = 'stop'  # end is always stop
        post['spread'] = self.spread # end with spread
        return post

class Diminuendo(DynamicWedge):
    '''A spanner diminuendo wedge.

    >>> from music21 import dynamics
    >>> d = dynamics.Diminuendo()
    >>> d.getStartParameters()
    {'spread': 15, 'type': 'diminuendo'}
    >>> d.getEndParameters()
    {'spread': 0, 'type': 'stop'}
    '''
    def __init__(self, *arguments, **keywords):
        DynamicWedge.__init__(self, *arguments, **keywords)
        self.type = 'diminuendo'

    def __repr__(self):
        msg = spanner.Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.Diminuendo ')
        return msg

    def getStartParameters(self):
        '''Return the parameters for the start of this spanner
        ''' 
        post = {}
        post['type'] = self.type # dim
        post['spread'] = self.spread # start with spread
        return post

    def getEndParameters(self):
        '''Return the parameters for the start of this spanner
        ''' 
        post = {}
        post['type'] = 'stop'  # end is always stop
        post['spread'] = 0
        return post




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


#-------------------------------------------------------------------------------
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

        b = a.parts[0].flat.getElementsByClass(music21.dynamics.DynamicWedge)
        self.assertEquals(len(b), 2)


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
            d = dynamics.Dynamic(selections[i % len(selections)])
            #d.positionVertical = positions[i%len(positions)]
            s.append(d)
            s.append(note.Note('c1'))
        #s.show()

    def testDynamicsPositionB(self):
        import random
        from music21 import stream, note, expressions, layout, dynamics
        s = stream.Stream()
        for i in range(6):
            m = stream.Measure(number=i + 1)
            m.append(layout.SystemLayout(isNew=True))
            m.append(note.Rest(type='whole'))
            s.append(m)
        for m in s.getElementsByClass('Measure'):
            offsets = [x * .25 for x in range(16)]
            random.shuffle(offsets)
            offsets = offsets[:4]
            for o in offsets:
                d = dynamics.Dynamic('mf')
                d.positionVertical = 20
                m.insert(o, d)

        #s.show()




#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Dynamic, dynamicStrFromDecimal]

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

