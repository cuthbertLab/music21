# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         volume.py
# Purpose:      Objects for representing volume, amplitude, and related
#               parameters
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2011-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
This module defines the object model of Volume, covering all representation of
amplitude, volume, velocity, and related parameters.
'''

import unittest

from music21 import exceptions21
from music21 import common
from music21.common import SlottedObject

from music21 import environment
_MOD = "volume.py"
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------


class VolumeException(exceptions21.Music21Exception):
    pass


#-------------------------------------------------------------------------------


class Volume(SlottedObject):
    '''
    The Volume object lives on NotRest objects and subclasses. It is not a
    Music21Object subclass.

    >>> v = volume.Volume(velocity=90)
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_client',
        '_velocity',
        '_cachedRealized',
        'velocityIsRelative',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        client=None,
        velocity=None,
        velocityScalar=None,
        velocityIsRelative=True,
        ):
        # store a reference to the client, as we use this to do context
        # will use property; if None will leave as None
        self._client = None
        self.client = client
        self._velocity = None
        if velocity is not None:
            self.velocity = velocity
        elif velocityScalar is not None:
            self.velocityScalar = velocityScalar
        self._cachedRealized = None
        self.velocityIsRelative = velocityIsRelative

    ### SPECIAL METHODS ###

    def __deepcopy__(self, memo=None):
        '''
        Need to manage copying of weak ref; when copying, do not copy weak ref,
        but keep as a reference to the same object.
        '''
        new = self.__class__()
        new.mergeAttributes(self) # will get all numerical values
        # keep same weak ref object
        new._client = self._client
        return new

    def __repr__(self):
        return "<music21.volume.Volume realized=%s>" % round(self.realized, 2)

    def __getstate__(self):
        self._client = common.unwrapWeakref(self._client)
        return SlottedObject.__getstate__(self)

    def __setstate__(self, state):
        SlottedObject.__setstate__(self, state)
        self._client = common.wrapWeakref(self._client)

    ### PUBLIC METHODS ###


    def getDynamicContext(self):
        '''Return the dynamic context of this Volume, based on the position of the NotRest client of this object.
        '''
        # TODO: find wedges and crescendi too
        return self.client.getContextByClass('Dynamic')

    def mergeAttributes(self, other):
        '''Given another Volume object, gather all attributes except client. Values are always copied, not passed by reference.


        >>> n1 = note.Note()
        >>> v1 = volume.Volume()
        >>> v1.velocity = 111
        >>> v1.client = n1

        >>> v2 = volume.Volume()
        >>> v2.mergeAttributes(v1)
        >>> v2.client == None
        True
        >>> v2.velocity
        111
        '''
        if other is not None:
            self._velocity = other._velocity
            self.velocityIsRelative = other.velocityIsRelative

    def getRealizedStr(self, useDynamicContext=True, useVelocity=True,
        useArticulations=True, baseLevel=0.5, clip=True):
        '''Return the realized as rounded and formatted string value. Useful for testing.


        >>> v = volume.Volume(velocity=64)
        >>> v.getRealizedStr()
        '0.5'
        '''
        val = self.getRealized(useDynamicContext=useDynamicContext,
                    useVelocity=useVelocity, useArticulations=useArticulations,
                    baseLevel=baseLevel, clip=clip)
        return str(round(val, 2))

    def getRealized(
        self,
        useDynamicContext=True,
        useVelocity=True,
        useArticulations=True,
        baseLevel=0.5,
        clip=True,
        ):
        '''
        Get a realized unit-interval scalar for this Volume. This scalar is to
        be applied to the dynamic range of whatever output is available,
        whatever that may be.

        The `baseLevel` value is a middle value between 0 and 1 that all
        scalars modify. This also becomes the default value for unspecified
        dynamics. When scalars (between 0 and 1) are used, their values are
        doubled, such that mid-values (around .5, which become 1) make no
        change.

        This can optionally take into account `dynamicContext`, `useVelocity`,
        and `useArticulation`.

        If `useDynamicContext` is True, a context search for a dynamic will be
        done, else dynamics are ignored. Alternatively, the useDynamicContext
        may supply a Dynamic object that will be used instead of a context
        search.

        If `useArticulations` is True and client is not None, any articulations
        found on that client will be used to adjust the volume. Alternatively,
        the `useArticulations` parameter may supply a list of articulations
        that will be used instead of that available on a client.

        The `velocityIsRelative` tag determines if the velocity value includes
        contextual values, such as dynamics and and accents, or not.

        >>> s = stream.Stream()
        >>> s.repeatAppend(note.Note('d3', quarterLength=.5), 8)
        >>> s.insert([0, dynamics.Dynamic('p'), 1, dynamics.Dynamic('mp'), 2, dynamics.Dynamic('mf'), 3, dynamics.Dynamic('f')])

        >>> s.notes[0].volume.getRealized()
        0.496...

        >>> s.notes[1].volume.getRealized()
        0.496...

        >>> s.notes[2].volume.getRealized()
        0.63779...

        >>> s.notes[7].volume.getRealized()
        0.99212...

        velocity, if set, will be scaled by dynamics
        
        >>> s.notes[7].volume.velocity = 20
        >>> s.notes[7].volume.getRealized()
        0.22047...

        unless we set the velocity to not be relative...
        
        >>> s.notes[7].volume.velocityIsRelative = False
        >>> s.notes[7].volume.getRealized()
        0.1574803...

        '''
        #velocityIsRelative might be best set at import. e.g., from MIDI,
        # velocityIsRelative is False, but in other applications, it may not
        # be
        val = baseLevel
        dm = None  # no dynamic mark
        # velocity is checked first; the range between 0 and 1 is doubled,
        # to 0 to 2. a velocityScalar of .7 thus scales the base value of
        # .5 by 1.4 to become .7
        if useVelocity:
            if self._velocity is not None:
                if not self.velocityIsRelative:
                    # if velocity is not relateive
                    # it should fully determines output independent of anything
                    # else
                    val = self.velocityScalar
                else:
                    val = val * (self.velocityScalar * 2.0)
            # this value provides a good default velocity, as .5 is low
            # this not a scalar application but a shift.
            else: # target :0.70866
                val += 0.20866
        # only change the val from here if velocity is relative
        if self.velocityIsRelative:
            if useDynamicContext is not False:
                if hasattr(useDynamicContext,
                    'classes') and 'Dynamic' in useDynamicContext.classes:
                    dm = useDynamicContext # it is a dynamic
                elif self.client is not None:
                    dm = self.getDynamicContext() # dm may be None
                else:
                    environLocal.printDebug(['getRealized():',
                    'useDynamicContext is True but no dynamic supplied or found in context'])
                if dm is not None:
                    # double scalare (so range is between 0 and 1) and scale
                    # t he current val (around the base)
                    val = val * (dm.volumeScalar * 2.0)
            # userArticulations can be a list of 1 or more articulation objects
            # as well as True/False
            if useArticulations is not False:
                am = None
                if common.isIterable(useArticulations):
                    am = useArticulations
                elif (hasattr(useArticulations, 'classes') and 
                        'Articulation' in useArticulations.classes):
                    am = [useArticulations] # place in a list
                elif self.client is not None:
                    am = self.client.articulations
                if am is not None:
                    for a in am:
                        # add in volume shift for all articulations
                        val += a.volumeShift
        if clip: # limit between 0 and 1
            if val > 1:
                val = 1.0
            elif val < 0:
                val = 0.0
        # might to rebalance range after scalings
        # always update cached result each time this is called
        self._cachedRealized = val
        return val

    ### PUBLIC PROPERTIES ###

    @property
    def cachedRealized(self):
        '''
        Return the cached realized value of this volume. This will be the last
        realized value or, if that value has not been set, a newly realized
        value. If the caller knows that the realized values have all been
        recently set, using this property will add significant performance
        boost.

        >>> v = volume.Volume(velocity=128)
        >>> v.cachedRealized
        1.0
        '''
        if self._cachedRealized is None:
            self._cachedRealized = self.getRealized()
        return self._cachedRealized

    @property
    def cachedRealizedStr(self):
        '''
        Convenience property for testing.

        >>> v = volume.Volume(velocity=128)
        >>> v.cachedRealizedStr
        '1.0'
        '''
        return str(round(self.cachedRealized, 2))

    @property
    def client(self):
        '''
        Get or set the client, which must be a note.NotRest subclass. The
        client is wrapped in a weak reference.
        '''
        if self._client is None:
            return None
        post = common.unwrapWeakref(self._client)
        if post is None:
            # set attribute for speed
            self._client = None
        return post

    @client.setter
    def client(self, client):
        if client is not None:
            if hasattr(client, 'classes') and 'NotRest' in client.classes:
                self._client = common.wrapWeakref(client)
        else:
            self._client = None

    @property
    def realized(self):
        return self.getRealized()

    @property
    def velocity(self):
        '''
        Get or set the velocity value, a numerical value between 0 and 127 and
        available setting amplitude on each Note or Pitch in chord.

        >>> n = note.Note()
        >>> n.volume.velocity = 20
        >>> n.volume.client == n
        True

        >>> n.volume.velocity
        20
        '''
        return self._velocity

    @velocity.setter
    def velocity(self, value):
        if not common.isNum(value):
            raise VolumeException('value provided for velocity must be a number, not %s' % value)
        if value < 0:
            self._velocity = 0
        elif value > 127:
            self._velocity = 127
        else:
            self._velocity = value

    @property
    def velocityScalar(self):
        '''
        Get or set the velocityScalar value, a numerical value between 0
        and 1 and available setting amplitude on each Note or Pitch in
        chord. This value is mapped to the range 0 to 127 on output.

        Note that this value is derived from the set velocity value.
        Floating point error seen here will not be found in the velocity
        value.

        When setting this value, an integer-based velocity value will be
        derived and stored.

        >>> n = note.Note()
        >>> n.volume.velocityScalar = .5
        >>> n.volume.velocity
        64

        >>> n.volume.velocity = 127
        >>> n.volume.velocityScalar
        1.0
        '''
        # multiplying by 1/127. for performance
        return self._velocity * 0.007874015748031496

    @velocityScalar.setter
    def velocityScalar(self, value):
        if not common.isNum(value):
            raise VolumeException('value provided for velocityScalar must be a number, not %s' % value)
        if value < 0:
            scalar = 0
        elif value > 1:
            scalar = 1
        else:
            scalar = value
        self._velocity = int(round(scalar * 127))


#-------------------------------------------------------------------------------
# utility stream processing methods


def realizeVolume(srcStream, setAbsoluteVelocity=False,
            useDynamicContext=True, useVelocity=True, useArticulations=True):
    '''Given a Stream with one level of dynamics (e.g., a Part, or two Staffs that share Dynamics), destructively modify it to set all realized volume levels. These values will be stored in the Volume object as `cachedRealized` values.

    This is a top-down routine, as opposed to bottom-up values available with context searches on Volume. This thus offers a performance benefit.

    This is always done in place; for the option of non-in place processing, see Stream.realizeVolume().

    If setAbsoluteVelocity is True, the realized values will overwrite all existing velocity values, and the Volume objects velocityIsRelative parameters will be set to False.


    '''
    # get dynamic map
    flatSrc = srcStream.flat # assuming sorted

    # check for any dynamics
    dynamicsAvailable = False
    if flatSrc.iter.getElementsByClass('Dynamic'):
        dynamicsAvailable = True
    else: # no dynamics available
        if useDynamicContext is True: # only if True, and non avail, override
            useDynamicContext = False

    if dynamicsAvailable:
        # extend durations of all dynamics
        # doing this in place as this is a destructive operation
        boundaries = flatSrc.extendDurationAndGetBoundaries('Dynamic', inPlace=True)
        bKeys = list(boundaries.keys())
        bKeys.sort() # sort

    # assuming stream is sorted
    # storing last releven index lets us always start form the last-used
    # key, avoiding searching through entire list every time
    lastRelevantKeyIndex = 0
    for e in flatSrc: # iterate over all elements
        if hasattr(e, 'volume') and 'NotRest' in e.classes:
            # try to find a dynamic
            eStart = e.getOffsetBySite(flatSrc)

            # get the most recent dynamic
            if dynamicsAvailable and useDynamicContext is True:
                dm = False # set to not search dynamic context
                for k in range(lastRelevantKeyIndex, len(bKeys)):
                    start, end = bKeys[k]
                    if eStart >= start and eStart < end:
                        # store so as to start in the same position
                        # for next element
                        lastRelevantKeyIndex = k
                        dm = boundaries[bKeys[k]]
                        break
            else: # permit supplying a single dynamic context for all materia
                dm = useDynamicContext
            # this returns a value, but all we need to do is to set the
            # cached values stored internally
            val = e.volume.getRealized(useDynamicContext=dm, useVelocity=True,
                  useArticulations=True)
            if setAbsoluteVelocity:
                e.volume.velocityIsRelative = False
                # set to velocity scalar
                e.volume.velocityScalar = val



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        from music21 import volume, note

        n1 = note.Note()
        v = volume.Volume(client=n1)
        self.assertEqual(v.client, n1)
        del n1
        # weak ref does not exist
        self.assertEqual(v.client, None)


    def testGetContextSearchA(self):
        from music21 import stream, note, volume, dynamics

        s = stream.Stream()
        d1 = dynamics.Dynamic('mf')
        s.insert(0, d1)
        d2 = dynamics.Dynamic('f')
        s.insert(2, d2)

        n1 = note.Note('g')
        v1 = volume.Volume(client=n1)
        s.insert(4, n1)

        # can get dynamics from volume object
        self.assertEqual(v1.client.getContextByClass('Dynamic'), d2)
        self.assertEqual(v1.getDynamicContext(), d2)


    def testGetContextSearchB(self):
        from music21 import stream, note, dynamics

        s = stream.Stream()
        d1 = dynamics.Dynamic('mf')
        s.insert(0, d1)
        d2 = dynamics.Dynamic('f')
        s.insert(2, d2)

        n1 = note.Note('g')
        s.insert(4, n1)

        # can get dynamics from volume object
        self.assertEqual(n1.volume.getDynamicContext(), d2)


    def testDeepCopyA(self):
        import copy
        from music21 import volume, note
        n1 = note.Note()

        v1 = volume.Volume()
        v1.velocity = 111
        v1.client = n1

        v1Copy = copy.deepcopy(v1)
        self.assertEqual(v1.velocity, 111)
        self.assertEqual(v1Copy.velocity, 111)

        self.assertEqual(v1.client, n1)
        self.assertEqual(v1Copy.client, n1)


    def testGetRealizedA(self):
        from music21 import volume, dynamics

        v1 = volume.Volume(velocity=64)
        self.assertEqual(v1.getRealizedStr(), '0.5')

        d1 = dynamics.Dynamic('p')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.35')

        d1 = dynamics.Dynamic('ppp')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.15')


        d1 = dynamics.Dynamic('fff')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.91')


        # if vel is at max, can scale down with a dynamic
        v1 = volume.Volume(velocity=127)
        d1 = dynamics.Dynamic('fff')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '1.0')

        d1 = dynamics.Dynamic('ppp')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.3')
        d1 = dynamics.Dynamic('mp')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.9')
        d1 = dynamics.Dynamic('p')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.7')


    def testGetRealizedB(self):


        from music21 import articulations

        v1 = Volume(velocity=64)
        self.assertEqual(v1.getRealizedStr(), '0.5')

        a1 = articulations.StrongAccent()
        self.assertEqual(v1.getRealizedStr(useArticulations=a1), '0.65')

        a1 = articulations.Accent()
        self.assertEqual(v1.getRealizedStr(useArticulations=a1), '0.6')

#         d1 = dynamics.Dynamic('ppp')
#         self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.1')





    def testRealizeVolumeA(self):
        from music21 import stream, dynamics, note, volume

        s = stream.Stream()
        s.repeatAppend(note.Note('g3'), 16)

        # before insertion of dynamics
        match = [n.volume.cachedRealizedStr for n in s.notes]
        self.assertEqual(match, ['0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71'])

        for i, d in enumerate(['pp', 'p', 'mp', 'f', 'mf', 'ff', 'ppp', 'mf']):
            s.insert(i*2, dynamics.Dynamic(d))

        # cached will be out of date in regard to new dynamics
        match = [n.volume.cachedRealizedStr for n in s.notes]
        self.assertEqual(match, ['0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71'])

        # calling realize will set all to new cached values
        volume.realizeVolume(s)
        match = [n.volume.cachedRealizedStr for n in s.notes]
        self.assertEqual(match, ['0.35', '0.35', '0.5', '0.5', '0.64', '0.64', '0.99', '0.99', '0.78', '0.78', '1.0', '1.0', '0.21', '0.21', '0.78', '0.78'])

        # we can get the same results without using realizeVolume, though
        # this uses slower context searches
        s = stream.Stream()
        s.repeatAppend(note.Note('g3'), 16)

        for i, d in enumerate(['pp', 'p', 'mp', 'f', 'mf', 'ff', 'ppp', 'mf']):
            s.insert(i*2, dynamics.Dynamic(d))
        match = [n.volume.cachedRealizedStr for n in s.notes]
        self.assertEqual(match, ['0.35', '0.35', '0.5', '0.5', '0.64', '0.64', '0.99', '0.99', '0.78', '0.78', '1.0', '1.0', '0.21', '0.21', '0.78', '0.78'])

        # loooking at raw velocity values
        match = [n.volume.velocity for n in s.notes]
        self.assertEqual(match, [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None])

        # can set velocity with realized values
        volume.realizeVolume(s, setAbsoluteVelocity=True)
        match = [n.volume.velocity for n in s.notes]
        self.assertEqual(match, [45, 45, 63, 63, 81, 81, 126, 126, 99, 99, 127, 127, 27, 27, 99, 99])

        #s.show('midi')

    def testRealizeVolumeB(self):
        from music21 import corpus, dynamics
        s = corpus.parse('bwv66.6')

        durUnit = s.highestTime  // 8 # let floor
        dyns = ['pp', 'p', 'mp', 'f', 'mf', 'ff', 'f', 'mf']

        for i, p in enumerate(s.parts):
            for j, d in enumerate(dyns):
                oTarget = j*durUnit
                # placing dynamics in Measure requires extra handling
                m = p.getElementsByOffset(oTarget,
                    mustBeginInSpan=False).getElementsByClass('Measure')[0]
                oInsert = oTarget - m.getOffsetBySite(p)
                m.insert(oInsert, dynamics.Dynamic(d))
            # shift 2 places each time
            dyns = dyns[2:] + dyns[:2]

        #s.show()
        #s.show('midi')

        #### TODO: BUG -- one note too loud...
        match = [n.volume.cachedRealizedStr for n in s.parts[0].flat.notes]
        self.assertEqual(match, ['0.35', '0.35', '0.35', '0.35', '0.35', '0.5', '0.5', '0.5', '0.5', '0.64', '0.64', '0.64', '0.64', '0.64', '0.99', '0.99', '0.99', '0.99', '0.78', '0.78', '0.78', '0.78', '1.0', '1.0', '1.0', '1.0', '0.99', '0.99', '0.99', '0.99', '0.78', '0.78', '0.78', '0.78', '0.78', '0.78', '0.78'])

        match = [n.volume.cachedRealizedStr for n in s.parts[1].flat.notes]

        self.assertEqual(match, ['0.64', '0.64', '0.64', '0.64', '0.99', '0.99', '0.99', '0.99', '0.99', '0.78', '0.78', '0.78', '0.78', '0.78', '1.0', '1.0', '1.0', '1.0', '0.99', '0.99', '0.99', '0.99', '0.99', '0.78', '0.78', '0.78', '0.78', '0.35', '0.35', '0.35', '0.35', '0.35', '0.35', '0.5', '0.5', '0.5', '0.5', '0.5', '0.5', '0.5', '0.5', '0.5'])

        match = [n.volume.cachedRealizedStr for n in s.parts[3].flat.notes]

        self.assertEqual(match, ['0.99', '0.99', '0.99', '0.99', '0.99', '0.78', '0.78', '0.78', '0.78', '0.78', '0.35', '0.35', '0.35', '0.35', '0.35', '0.5', '0.5', '0.5', '0.5', '0.5', '0.5', '0.5', '0.64', '0.64', '0.64', '0.64', '0.99', '0.99', '0.99', '0.99', '0.78', '0.78', '0.78', '0.78', '0.78', '1.0', '1.0', '1.0', '1.0', '1.0', '1.0'])


    def testRealizeVolumeC(self):
        from music21 import stream, note, articulations

        s = stream.Stream()
        s.repeatAppend(note.Note('g3'), 16)

        for i in range(0, 16, 3):
            s.notes[i].articulations.append(articulations.Accent())
        for i in range(0, 16, 4):
            s.notes[i].articulations.append(articulations.StrongAccent())

        match = [n.volume.cachedRealizedStr for n in s.notes]
        self.assertEqual(match, ['0.96', '0.71', '0.71', '0.81', '0.86', '0.71', '0.81', '0.71', '0.86', '0.81', '0.71', '0.71', '0.96', '0.71', '0.71', '0.81'])
        #s.show()
        #s.show('midi')



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof




