# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         dynamics.py
# Purpose:      Module for dealing with dynamics changes.
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

'''
Classes and functions for creating and manipulating dynamic symbols. Rather than
subclasses, the :class:`~music21.dynamics.Dynamic` object is often specialized by parameters.
'''

import unittest

from music21 import base
from music21 import exceptions21
from music21 import common
from music21 import spanner
from music21 import style

from music21 import environment
_MOD = 'dynamics'
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

# could be really useful for automatic description of musical events
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


    >>> dynamics.dynamicStrFromDecimal(0.25)
    'pp'
    >>> dynamics.dynamicStrFromDecimal(1)
    'fff'
    '''
    if n is None or n <= 0:
        return 'n'
    elif n < 0.11:
        return 'pppp'
    elif n < 0.16:
        return 'ppp'
    elif n < 0.26:
        return 'pp'
    elif n < 0.36:
        return 'p'
    elif n < 0.5:
        return 'mp'
    elif n < 0.65:
        return 'mf'
    elif n < 0.8:
        return 'f'
    elif n < 0.9:
        return 'ff'
    else:
        return 'fff'


# defaults used for volume scalar
dynamicStrToScalar = {
    None: 0.5,  # default value
    'n': 0.0,
    'pppp': 0.1,
    'ppp': 0.15,
    'pp': 0.25,
    'p': 0.35,
    'mp': 0.45,
    'mf': 0.55,
    'f': 0.7,
    'fp': 0.75,
    'sf': 0.85,
    'ff': 0.85,
    'fff': 0.9,
    'ffff': 0.95,
}


# ------------------------------------------------------------------------------
class DynamicException(exceptions21.Music21Exception):
    pass


class WedgeException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------


class Dynamic(base.Music21Object):
    '''
    Object representation of Dynamics.

    >>> pp1 = dynamics.Dynamic('pp')
    >>> pp1.value
    'pp'
    >>> pp1.longName
    'pianissimo'
    >>> pp1.englishName
    'very soft'


    Dynamics can also be specified on a 0 to 1 scale with 1 being the
    loudest (see dynamicStrFromDecimal() above)

    >>> ppp = dynamics.Dynamic(0.15)  # on 0 to 1 scale
    >>> ppp.value
    'ppp'
    >>> print('%.2f' % ppp.volumeScalar)
    0.15


    Note that we got lucky last time because the dynamic 0.15 exactly corresponds
    to what we've considered the default for 'ppp'.  Here we assign 0.98 which
    is close to the 0.9 that is the default for 'fff' -- but the 0.98 will
    be retained in the .volumeScalar

    >>> loud = dynamics.Dynamic(0.98)  # on 0 to 1 scale
    >>> loud.value
    'fff'
    >>> print('%.2f' % loud.volumeScalar)
    0.98

    Transferring the .value ('fff') to a new Dynamic object will set the volumeScalar
    back to 0.9

    >>> loud2 = dynamics.Dynamic(loud.value)
    >>> loud2.value
    'fff'
    >>> print('%.2f' % loud2.volumeScalar)
    0.90


    Custom dynamics are possible:

    >>> myDyn = dynamics.Dynamic('rfzsfmp')
    >>> myDyn.value
    'rfzsfmp'
    >>> print(myDyn.volumeScalar)
    0.5
    >>> myDyn.volumeScalar = 0.87
    >>> myDyn.volumeScalar
    0.87




    Dynamics can be placed anywhere in a stream.


    >>> s = stream.Stream()
    >>> s.insert(0, note.Note('E-4', type='half'))
    >>> s.insert(2, note.Note('F#5', type='half'))
    >>> s.insert(0, dynamics.Dynamic('pp'))
    >>> s.insert(1, dynamics.Dynamic('mf'))
    >>> s.insert(3, dynamics.Dynamic('fff'))
    >>> #_DOCS_SHOW s.show()


    .. image:: images/dynamics_simple.*
        :width: 344


    '''
    classSortOrder = 10
    _styleClass = style.TextStyle

    _DOC_ORDER = ['longName', 'englishName']
    _DOC_ATTR = {
        'longName': r'''
            the name of this dynamic in Italian.


            >>> d = dynamics.Dynamic('pp')
            >>> d.longName
            'pianissimo'
            ''',
        'englishName': r'''
            the name of this dynamic in English.


            >>> d = dynamics.Dynamic('pp')
            >>> d.englishName
            'very soft'
            ''',
    }

    def __init__(self, value=None):
        super().__init__()

        # the scalar is used to calculate the final output of a note
        # under this dynamic. if this property is set, it will override
        # use of a default.
        self._volumeScalar = None
        self.longName = None
        self.englishName = None
        self._value = None

        if not isinstance(value, str):
            # assume it is a number, try to convert
            self._volumeScalar = value
            self.value = dynamicStrFromDecimal(value)
        else:
            self.value = value  # will use property

        # for position, as musicxml, all units are in tenths of interline space
        # position is needed as default positions are often incorrect
        self.style.absoluteX = -36
        self.style.absoluteY = -80  # below top line
        # this value provides good 16th note alignment
        self.positionPlacement = None

    def _reprInternal(self):
        return str(self.value)

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
                     doc='''
        Get or set the value of this dynamic, which sets the long and
        English names of this Dynamic. The value is a string specification.

        >>> p = dynamics.Dynamic('p')
        >>> p.value
        'p'
        >>> p.englishName
        'soft'
        >>> p.longName
        'piano'

        >>> p.value = 'f'
        >>> p.value
        'f'
        >>> p.englishName
        'loud'
        >>> p.longName
        'forte'
        ''')

    def _getVolumeScalar(self):
        if self._volumeScalar is not None:
            return self._volumeScalar
        # use default
        elif self._value in dynamicStrToScalar:
            return dynamicStrToScalar[self._value]
        else:
            thisDynamic = self._value
            # ignore leading s like in sf
            if 's' in thisDynamic:
                thisDynamic = thisDynamic[1:]
            # ignore closing z like in fz
            if thisDynamic[-1] == 'z':
                thisDynamic = thisDynamic[:-1]
            if thisDynamic in dynamicStrToScalar:
                return dynamicStrToScalar[thisDynamic]
            else:
                return dynamicStrToScalar[None]

    def _setVolumeScalar(self, value):
        # we can manually set this to be anything, overriding defaults
        if common.isNum(value) and 0 <= value <= 1:
            self._volumeScalar = value
        else:
            raise DynamicException(f'cannot set as volume scalar to: {value}')

    volumeScalar = property(_getVolumeScalar, _setVolumeScalar, doc=r'''
        Get or set the volume scalar for this dynamic. If not explicitly set, a
        default volume scalar will be provided. Any number between 0 and 1 can be
        used to set the volume scalar, overriding the expected behavior.

        As mezzo is at 0.5, the unit interval range is doubled for
        generating final output. The default output is 0.5.


        >>> d = dynamics.Dynamic('mf')
        >>> d.volumeScalar
        0.55...

        >>> d.volumeScalar = 0.1
        >>> d.volumeScalar
        0.1
        >>> d.value
        'mf'


        int(volumeScalar \* 127) gives the MusicXML <sound dynamics="x"/> tag

        >>> xmlOut = musicxml.m21ToXml.GeneralObjectExporter().parse(d).decode('utf-8')
        >>> print(xmlOut)
        <?xml...
        <direction>
            <direction-type>
              <dynamics default-x="-36" default-y="-80">
                <mf />
              </dynamics>
            </direction-type>
            <sound dynamics="12" />
        </direction>...
        ''')


# ------------------------------------------------------------------------------
class DynamicWedge(spanner.Spanner):
    '''Common base-class for Crescendo and Diminuendo.
    '''

    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)

        self.type = None  # crescendo or diminuendo
        self.placement = 'below'  # can above or below, after musicxml
        self.spread = 15  # this unit is in tenths
        self.niente = False


class Crescendo(DynamicWedge):
    '''A spanner crescendo wedge.

    >>> from music21 import dynamics
    >>> d = dynamics.Crescendo()
    >>> d.spread
    15
    >>> d.spread = 20
    >>> d.spread
    20
    >>> d.type
    'crescendo'
    '''

    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self.type = 'crescendo'


class Diminuendo(DynamicWedge):
    '''A spanner diminuendo wedge.

    >>> from music21 import dynamics
    >>> d = dynamics.Diminuendo()
    >>> d.spread = 20
    >>> d.spread
    20
    '''

    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self.type = 'diminuendo'

# ------------------------------------------------------------------------------


class TestExternal(unittest.TestCase):  # pragma: no cover

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
            o += 4  # increment
        a.show()


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import copy
        import sys
        import types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            # noinspection PyTypeChecker
            if callable(name) and not isinstance(name, types.FunctionType):
                try:  # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                unused_a = copy.copy(obj)
                unused_b = copy.deepcopy(obj)

    def testBasic(self):
        noDyn = Dynamic()
        assert noDyn.longName is None

        pp = Dynamic('pp')
        self.assertEqual(pp.value, 'pp')
        self.assertEqual(pp.longName, 'pianissimo')
        self.assertEqual(pp.englishName, 'very soft')

    def testCorpusDynamicsWedge(self):
        from music21 import corpus
        a = corpus.parse('opus41no1/movement2')  # has dynamics!
        b = a.parts[0].flat.getElementsByClass('Dynamic')
        self.assertEqual(len(b), 35)

        b = a.parts[0].flat.getElementsByClass('DynamicWedge')
        self.assertEqual(len(b), 2)

    def testMusicxmlOutput(self):
        # test direct rendering of musicxml
        from music21.musicxml import m21ToXml
        d = Dynamic('p')
        xmlOut = m21ToXml.GeneralObjectExporter().parse(d).decode('utf-8')
        match = '<p />'
        self.assertNotEqual(xmlOut.find(match), -1, xmlOut)

    def testDynamicsPositionA(self):
        from music21 import stream, note
        s = stream.Stream()
        selections = ['pp', 'f', 'mf', 'fff']
        # positions = [-20, 0, 20]
        for i in range(10):
            d = Dynamic(selections[i % len(selections)])
            s.append(d)
            s.append(note.Note('c1'))
        # s.show()

    def testDynamicsPositionB(self):
        import random
        from music21 import stream, note, layout
        s = stream.Stream()
        for i in range(6):
            m = stream.Measure(number=i + 1)
            m.append(layout.SystemLayout(isNew=True))
            m.append(note.Rest(type='whole'))
            s.append(m)
        for m in s.getElementsByClass('Measure'):
            offsets = [x * 0.25 for x in range(16)]
            random.shuffle(offsets)
            offsets = offsets[:4]
            for o in offsets:
                d = Dynamic('mf')
                d.style.absoluteY = 20
                m.insert(o, d)

        # s.show()


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Dynamic, dynamicStrFromDecimal]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

