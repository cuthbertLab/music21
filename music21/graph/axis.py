# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         graph/axis.py
# Purpose:      Classes for extracting one dimensional data for graphs
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#               Evan Lynch
#
# Copyright:    Copyright © 2009-2012, 2017 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Definitions for extracting data from a Stream to place on one axis of a
:class:`~music21.graph.plot.PlotStream` or similar object.
'''
import collections
import math
import unittest
import re

from music21.graph.utilities import accidentalLabelToUnicode, GraphException

from music21 import common
from music21 import duration
from music21 import dynamics
from music21 import pitch
from music21 import prebase
from music21 import stream

from music21.analysis import elements as elementAnalysis
from music21.analysis import pitchAnalysis


class Axis(prebase.ProtoM21Object):
    '''
    An Axis is an easier way of specifying what to plot on any given axis.

    Client should be a .plot.PlotStream or None.  Eventually a Stream may be allowed,
    but not yet.
    '''
    _DOC_ATTR = {
        'axisName': 'the name of the axis.  One of "x" or "y" or for 3D Plots, "z"',
        'minValue': '''
            None or number representing the axis minimum.  Default None.
            ''',
        'maxValue': '''
            None or number representing the axis maximum.  Default None.
            ''',
        'axisDataMap': '''
            a dict of {'x': 0, 'y': 1, 'z': 2} mapping where an axis's data can
            be found in self.client.data after extract data is run:

            >>> b = corpus.parse('bwv66.6')
            >>> plot = graph.plot.ScatterPitchClassOffset(b)
            >>> pcAxis = plot.axisY
            >>> pcAxis.axisName
            'y'
            >>> pcAxisDataIndex = pcAxis.axisDataMap[pcAxis.axisName]
            >>> pcAxisDataIndex
            1
            >>> plot.extractData()
            >>> pcValues = [dataTuple[pcAxisDataIndex] for dataTuple in plot.data]
            >>> pcValues[0:2]
            [1, 11]
            ''',
        'quantities': '''
            a tuple of strings representing the quantities the axis can plot.
            The first element of the tuple is the authoritative name.

            >>> ax = graph.axis.DynamicsAxis()
            >>> ax.quantities
            ('dynamic', 'dynamics', 'volume')
            ''',
    }

    labelDefault = 'an axis'
    axisDataMap = {'x': 0, 'y': 1, 'z': 2}
    quantities = ('generic', 'one', 'nothing', 'blank')

    def __init__(self, client=None, axisName='x'):
        if isinstance(client, str):
            raise GraphException('Client must be a PlotStream, Stream, or None')
        self._client = None
        self._label = None

        self.client = client
        self.axisName = axisName

        self.minValue = None
        self.maxValue = None

    def _reprInternal(self):
        '''
        The representation of the Axis shows the client and the axisName
        in addition to the class name.

        >>> s = stream.Stream()
        >>> plot = graph.plot.ScatterPitchClassQuarterLength(s)
        >>> plot.axisX
        <music21.graph.axis.QuarterLengthAxis: x axis for ScatterPitchClassQuarterLength>

        >>> plot.axisY
        <music21.graph.axis.PitchClassAxis: y axis for ScatterPitchClassQuarterLength>

        >>> axIsolated = graph.axis.DynamicsAxis(axisName='z')
        >>> axIsolated
        <music21.graph.axis.DynamicsAxis: z axis for (no client)>

        >>> s = stream.Part()
        >>> axStream = graph.axis.DynamicsAxis(s, axisName='y')
        >>> axStream
        <music21.graph.axis.DynamicsAxis: y axis for Part>

        '''
        c = self.client
        if c is not None:
            clientName = c.__class__.__name__
        else:
            clientName = '(no client)'

        return f': {self.axisName} axis for {clientName}'

    @property
    def label(self):
        '''
        Returns self.label or class.labelDefault if not set:

        >>> ax = graph.axis.Axis(axisName='y')
        >>> ax.label
        'an axis'
        >>> ax.label = 'velocity'
        >>> ax.label
        'velocity'
        '''
        if self._label is not None:
            return self._label
        else:
            return self.labelDefault

    @label.setter
    def label(self, value):
        self._label = value

    @property
    def client(self):
        '''
        The client stores a reference to the Plot that
        makes reference to this axis.

        (Like all music21 clients, It is normally stored internally as a weakref,
        so no need for garbage collecting)
        '''
        return common.unwrapWeakref(self._client)

    @client.setter
    def client(self, referent):
        self._client = common.wrapWeakref(referent)

    @property
    def stream(self):
        '''
        Returns a reference to the client's .streamObj  (or None if client is None)

        If the client is itself a stream, return it.

        Read-only
        '''
        c = self.client
        if c is None:
            return None
        elif isinstance(c, stream.Stream):
            return c
        else:
            return c.streamObj

    def extractOneElement(self, n, formatDict):
        '''
        Override in subclasses...
        '''
        return 1

    def setBoundariesFromData(self, values):
        '''
        If self.minValue is not set,
        then set self.minValue to be the minimum of these values.

        Same with maxValue

        >>> ax = graph.axis.Axis()
        >>> print(ax.minValue)
        None

        >>> values = [10, 0, 3, 5]
        >>> ax.setBoundariesFromData(values)
        >>> ax.minValue
        0
        >>> ax.maxValue
        10

        If a boundary is given or .setXXXFromData is False then no changes are made

        >>> ax = graph.axis.Axis()
        >>> ax.minValue = -1
        >>> ax.setBoundariesFromData(values)
        >>> ax.minValue
        -1
        >>> ax.maxValue
        10
        '''
        if self.minValue is None and values:
            self.minValue = min(values)
        if self.maxValue is None and values:
            self.maxValue = max(values)

    def ticks(self):
        '''
        Get a set of ticks for this data.  Used by several numeric axes
        to make a reasonable number of ticks.

        >>> cax = graph.axis.Axis()
        >>> cax.minValue = 1
        >>> cax.maxValue = 9
        >>> cax.ticks()
        [(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'),
         (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')]

        For larger data, the ticks are farther apart.

        >>> cax.minValue = 7
        >>> cax.maxValue = 80
        >>> cax.ticks()
        [(0, '0'), (10, '10'), (20, '20'), (30, '30'), (40, '40'),
         (50, '50'), (60, '60'), (70, '70'), (80, '80'), (90, '90')]

        >>> cax.minValue = 712
        >>> cax.maxValue = 2213
        >>> cax.ticks()
        [(600, '600'), (700, '700'), (800, '800'), (900, '900'), (1000, '1000'),
         ...
         (2100, '2100'), (2200, '2200'), (2300, '2300')]
        '''
        minV = self.minValue
        maxV = self.maxValue

        if minV is None:
            minV = 0
        if maxV is None:
            maxV = 10

        difference = maxV - minV
        if difference == 0:
            log10distance = 0
        else:
            log10distance = int(math.log10(maxV - minV))

        closest10 = 10 ** log10distance  # closest power of 10 that is smaller than the difference
        if closest10 > 1 and (difference / closest10) <= 2:  # min three steps
            closest10 = int(closest10 / 10)

        startValue = (int(minV / closest10) - 1) * closest10
        if startValue < 0 and minV >= 0:
            startValue = 0

        stopValue = (int(maxV / closest10) + 2) * closest10
        steps = range(startValue, stopValue, closest10)

        ticks = []
        for tickNum in steps:
            ticks.append((tickNum, str(tickNum)))
        return ticks

    def postProcessData(self, dataList=None):
        '''
        Routine to be called after data has been extracted to
        do any cleanup, etc.  Defaults to doing nothing, but
        see CountingAxis for an example of how this works.
        '''
        pass

# -----------------------------------------------------------------------------


class PitchAxis(Axis):
    '''
    Axis subclass for dealing with Pitches
    '''
    _DOC_ATTR = {
        'showEnharmonic': '''
            bool on whether to show both common enharmonics in labels, default True
            ''',
        'blankLabelUnused': '''
            bool on whether to hide labels for unused pitches, default True.
            ''',
        'hideUnused': '''
            bool on whether not to even show a tick when a pitch doesn't exist.
            default True.
            ''',
        'showOctaves': '''
            bool or 'few' about whether to show octave numbers.  If 'few' then
            only the first pitch in each octave is shown.  Default 'few'
            ''',
    }
    labelDefault = 'Pitch'
    quantities = ('pitchGeneric', )

    def __init__(self, client=None, axisName='x'):
        super().__init__(client, axisName)
        self.showOctaves = 'few'
        self.showEnharmonic = True
        self.blankLabelUnused = True
        self.hideUnused = True

    @staticmethod
    def makePitchLabelsUnicode(ticks):
        '''
        Given a list of ticks, replace all labels with alternative/unicode symbols where necessary.

        >>> ticks = [(60, 'C4'), (61, 'C#4'), (62, 'D4'), (63, 'E-4')]
        >>> t2 = graph.axis.PitchAxis.makePitchLabelsUnicode(ticks)
        >>> len(t2)
        4
        >>> [num for num, label in t2]
        [60, 61, 62, 63]
        >>> t2[0]
        (60, 'C4')
        >>> for num, label in t2:
        ...     label
        'C4'
        'C♯4'
        'D4'
        'E♭4'
        '''
        # environLocal.printDebug(['calling filterPitchLabel', ticks])
        # this uses tex mathtext, which happens to define sharp and flat
        # http://matplotlib.org/users/mathtext.html
        post = []
        for value, label in ticks:
            label = accidentalLabelToUnicode(label)
            post.append((value, label))
        return post

    def _pitchTickHelper(self, attributeCounter, attributeCompare):
        '''
        Helper method that can apply all the showEnharmonic, etc. values consistently

        see the `ticks` methods below.

        Returns a list of two-element tuples
        '''
        s = self.stream
        if s is None:
            # better hope that hideUnused is False, or just will get an empty list
            nameCount = {}
        else:
            nameCount = pitchAnalysis.pitchAttributeCount(s, attributeCounter)

        ticks = []

        helperDict = {}
        octavesSeen = set()

        def weightedSortHelper(x):
            '''
            ensure that higher weighed weights come first, but
            then alphabetical by name, except that G comes before
            A... since we are only comparing enharmonics...
            '''
            weight, name = x
            if name.startswith('A'):
                name = 'H' + name[1:]
            return (-1 * weight, name)

        def unweightedSortHelper(x):
            weight, name = x
            if name.startswith('A'):
                name = 'H' + name[1:]
            return (weight, name)

        for i in range(int(self.minValue), int(self.maxValue) + 1):
            p = pitch.Pitch()
            setattr(p, attributeCompare, i)
            weights = []  # a list of pairs of count/label
            for key in nameCount:
                if key not in helperDict:
                    # store a dict of say, C4: 60, etc. so we don't need to make so many
                    # pitch.Pitch objects
                    helperDict[key] = getattr(pitch.Pitch(key), attributeCompare)

                if helperDict[key] == i:
                    weights.append((nameCount[key], key))

            if self.showEnharmonic:
                weights.sort(key=unweightedSortHelper)
            else:
                weights.sort(key=weightedSortHelper)

            label = None
            if not weights:  # get a default
                if self.hideUnused:
                    continue  # don't append any ticks...
                if not self.blankLabelUnused:
                    label = getattr(p, attributeCounter)
                else:  # use an empty label to maintain spacing
                    label = ''
            elif not self.showEnharmonic:
                # get just the first weighted
                label = weights[0][1]  # second value is label
            else:
                sub = []
                for unused_weight, name in weights:
                    sub.append(accidentalLabelToUnicode(name))
                label = '/'.join(sub)

            if self.showOctaves is False:
                label = re.sub(r'\d', '', label)
            elif self.showOctaves == 'few':
                matchOctave = re.search(r'\d', label)
                if matchOctave:
                    octaveMatch = matchOctave.group(0)
                    if octaveMatch in octavesSeen:
                        label = re.sub(r'\d', '', label)
                    else:
                        octavesSeen.add(octaveMatch)

            ticks.append((i, label))
        ticks = self.makePitchLabelsUnicode(ticks)
        return ticks


class PitchClassAxis(PitchAxis):
    '''
    Axis subclass for dealing with PitchClasses

    By default, axis is not set from data, but set to 0, 11
    '''
    labelDefault = 'Pitch Class'
    quantities = ('pitchClass', 'pitchclass', 'pc')

    def __init__(self, client=None, axisName='x'):
        self.showOctaves = False
        super().__init__(client, axisName)
        self.minValue = 0
        self.maxValue = 11

    def extractOneElement(self, n, formatDict):
        if hasattr(n, 'pitch'):
            return n.pitch.pitchClass

    def ticks(self):
        '''
        Get ticks and labels for pitch classes.

        If `showEnharmonic` is `True` (default) then
        when choosing whether to display as sharp or flat use
        the most commonly used enharmonic.

        >>> s = corpus.parse('bach/bwv324.xml')
        >>> s.analyze('key')
        <music21.key.Key of G major>

        >>> plotS = graph.plot.PlotStream(s)
        >>> ax = graph.axis.PitchClassAxis(plotS)
        >>> ax.hideUnused = True

        Ticks returns a list of two-element tuples:

        >>> ax.ticks()
        [(0, 'C'), (2, 'D'), ..., (11, 'B')]

        >>> for position, noteName in ax.ticks():
        ...            print(str(position) + ' ' + noteName)
        0 C
        2 D
        3 D♯
        4 E
        6 F♯
        7 G
        9 A
        11 B


        >>> s = corpus.parse('bach/bwv281.xml')
        >>> plotS = graph.plot.PlotStream(s)
        >>> ax = graph.axis.PitchClassAxis(plotS)
        >>> ax.hideUnused = True
        >>> ax.showEnharmonic = True

        >>> for position, noteName in ax.ticks():
        ...            print(str(position) + ' ' + noteName)
        0 C
        2 D
        3 E♭
        4 E
        5 F
        7 G
        9 A
        10 B♭
        11 B

        >>> ax.blankLabelUnused = True
        >>> ax.hideUnused = False
        >>> for position, noteName in ax.ticks():
        ...            print(str(position) + ' ' + noteName)
        0 C
        1
        2 D
        3 E♭
        4 E
        5 F
        6
        7 G
        8
        9 A
        10 B♭
        11 B

        .showEnharmonic will change here...

        >>> s.append(note.Note('A#4'))
        >>> s.append(note.Note('G#4'))
        >>> s.append(note.Note('A-4'))
        >>> s.append(note.Note('A-4'))
        >>> for position, noteName in ax.ticks():
        ...            print(str(position) + ' ' + noteName)
        0 C
        1
        2 D
        3 E♭
        4 E
        5 F
        6
        7 G
        8 G♯/A♭
        9 A
        10 A♯/B♭
        11 B

        Make sure that Ab shows since there are two of them and only one G#

        >>> ax.showEnharmonic = False
        >>> for position, noteName in ax.ticks():
        ...            print(str(position) + ' ' + noteName)
        0 C
        1
        2 D
        3 E♭
        4 E
        5 F
        6
        7 G
        8 A♭
        9 A
        10 B♭
        11 B


        OMIT_FROM_DOCS

        TODO: this ultimately needs to look at key signature/key to determine
        defaults for undefined notes where blankLabelUnused is False...
        '''
        # keys are integers
        # name strings are keys, and enharmonic are thus different
        return self._pitchTickHelper('name', 'pitchClass')


class PitchSpaceAxis(PitchAxis):
    '''
    Axis subclass for dealing with PitchSpace (MIDI numbers...)
    '''
    labelDefault = 'Pitch'
    quantities = ('pitchSpace', 'pitch', 'pitchspace', 'ps')

    def extractOneElement(self, n, formatDict):
        if hasattr(n, 'pitch'):
            return n.pitch.ps

    def ticks(self, dataMin=36, dataMax=100):
        '''
        >>> ax = graph.axis.PitchSpaceAxis()
        >>> ax.hideUnused = False
        >>> ax.blankLabelUnused = False
        >>> ax.minValue = 20
        >>> ax.maxValue = 24
        >>> for ps, label in ax.ticks():
        ...     print(str(ps) + ' ' + label)
        20 G♯0
        21 A
        22 B♭
        23 B
        24 C1

        >>> ax.showOctaves = False
        >>> for ps, label in ax.ticks():
        ...     print(str(ps) + ' ' + label)
        20 G♯
        21 A
        22 B♭
        23 B
        24 C

        >>> ax.showOctaves = True
        >>> for ps, label in ax.ticks():
        ...     print(str(ps) + ' ' + label)
        20 G♯0
        21 A0
        22 B♭0
        23 B0
        24 C1

        >>> ax.minValue = 60
        >>> ax.maxValue = 72
        >>> [x for x, y in ax.ticks()]
        [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]

        >>> bach = corpus.parse('bwv66.6')
        >>> plotS = graph.plot.PlotStream(bach.parts[-1])
        >>> ax = graph.axis.PitchSpaceAxis(plotS)
        >>> ax.hideUnused = False
        >>> ax.minValue = 36
        >>> ax.maxValue = 100
        >>> ticks = ax.ticks()
        >>> ticks[0]  # blank because no note 36 in data
        (36, '')
        >>> ticks[21]
        (57, 'A')
        '''
        return self._pitchTickHelper('nameWithOctave', 'ps')


class PitchSpaceOctaveAxis(PitchSpaceAxis):
    '''
    An axis similar to pitch classes, but just shows the octaves
    '''
    labelDefault = 'Octave'
    quantities = ('octave', 'octaves')

    def __init__(self, client=None, axisName='x'):
        super().__init__(client, axisName)
        self.startNameWithOctave = 'C2'

    def ticks(self):
        '''
        This class does not currently take into account whether the octaves themselves
        are found in the Stream.

        >>> ax = graph.axis.PitchSpaceOctaveAxis()
        >>> ax.minValue = 36
        >>> ax.maxValue = 100
        >>> ax.ticks()
        [(36, 'C2'), (48, 'C3'), (60, 'C4'), (72, 'C5'), (84, 'C6'), (96, 'C7')]

        >>> ax.startNameWithOctave = 'A2'
        >>> ax.ticks()
        [(45, 'A2'), (57, 'A3'), (69, 'A4'), (81, 'A5'), (93, 'A6')]
        '''
        ticks = []
        currentPitch = pitch.Pitch(self.startNameWithOctave)
        while currentPitch.ps <= self.maxValue:
            if currentPitch.ps >= self.minValue:
                ticks.append((int(currentPitch.ps), currentPitch.nameWithOctave))
            currentPitch.octave += 1
        ticks = self.makePitchLabelsUnicode(ticks)
        return ticks

# class PitchDiatonicAxis(PitchAxis):
#     '''
#     Axis subclass for dealing with Diatonic Values (.diatonicNoteNum)
#     '''
#     labelDefault = 'Step'
#     quantities = ('diatonic', 'diatonicNoteNum')
#
#     def extractOneElement(self, n, formatDict):
#         if hasattr(n, 'pitch'):
#             return n.pitch.diatonicNoteNum
#
#     def ticks(self, dataMin=15, dataMax=43):
#         '''
#         >>> ax = graph.axis.PitchDiatonicAxis()
#         >>> ax.hideUnused = False
#         >>> ax.blankLabelUnused = False
#         >>> ax.minValue = 20
#         >>> ax.maxValue = 30
#         >>> for ps, label in ax.ticks():
#         ...     print(str(ps) + ' ' + label)
#         20 G♯0
#         21 A
#         22 B♭
#         23 B
#         24 C1
#
#         >>> ax.showOctaves = False
#         >>> for ps, label in ax.ticks():
#         ...     print(str(ps) + ' ' + label)
#         20 G♯
#         21 A
#         22 B♭
#         23 B
#         24 C
#
#         >>> ax.showOctaves = True
#         >>> for ps, label in ax.ticks():
#         ...     print(str(ps) + ' ' + label)
#         20 G♯0
#         21 A0
#         22 B♭0
#         23 B0
#         24 C1
#
#         >>> bach = corpus.parse('bwv66.6')
#         >>> plotS = graph.plot.PlotStream(bach.parts[-1])
#         >>> ax = graph.axis.PitchSpaceAxis(plotS)
#         >>> ax.hideUnused = False
#         >>> ax.minValue = 36
#         >>> ax.maxValue = 100
#         >>> ticks = ax.ticks()
#         >>> ticks[0]  # blank because no note 36 in data
#         (36, '')
#         >>> ticks[21]
#         (57, 'A')
#         '''
#         return self._pitchTickHelper('nameWithOctave', 'diatonicNoteNum')

# -----------------------------------------------------------------------------


class PositionAxis(Axis):
    '''
    Axis subclass for dealing with Positions
    '''
    _DOC_ATTR = {
        'graceNoteQL': '''
            length to substitute a grace note or other Zero-length element for.
            Default is the length of a 64th note (1/16 of a QL)
        ''',
    }

    labelDefault = 'Position'
    quantities = ('position', 'positions')

    def __init__(self, client=None, axisName='x'):
        super().__init__(client, axisName)
        self.graceNoteQL = 2**-4


class OffsetAxis(PositionAxis):
    '''
    Axis subclass for dealing with Offsets
    '''
    _DOC_ATTR = {
        'useMeasures': '''
            bool or None for whether offsets (False) or measure numbers (True) should be used
            in the case of an offset access.  Default, None, meaning to check whether
            the stream has measures first.
            ''',
        'offsetStepSize': '''
            If measures are not used then this number is used to create the number
            of steps between an axis tick.  Currently the default is 10, but it
            might become a function of the length of the stream eventually.
            ''',
        'minMaxMeasureOnly': '''
            If True then only the first and last values will be used to
            create ticks for measures.  Default False.
            ''',

    }
    labelDefault = 'Offset'
    quantities = ('offset', 'measure', 'offsets', 'measures', 'time')

    def __init__(self, client=None, axisName='x'):
        super().__init__(client, axisName)
        self.useMeasures = None
        # self.displayMeasureNumberZero = False  # not used...
        self.offsetStepSize = 10
        self.minMaxMeasureOnly = False

    def extractOneElement(self, n, formatDict):
        return n.getOffsetInHierarchy(self.stream)

    @property
    def label(self):
        '''
        Return an axis label for measure or offset, depending on if measures are available.

        >>> a = graph.axis.OffsetAxis()
        >>> a.label
        'Offset'
        >>> a.useMeasures = True
        >>> a.label
        'Measure Number'
        '''
        if self._label is not None:
            return self._label

        useMeasures = self.useMeasures
        if useMeasures is None:
            useMeasures = self.setUseMeasuresFromOffsetMap()

        if useMeasures:
            return 'Measure Number'
        else:
            return 'Offset'

    @label.setter
    def label(self, value):
        self._label = value

    def setBoundariesFromData(self, values=None):
        try:
            self.minValue = self.stream.lowestOffset
            self.maxValue = self.stream.highestTime
        except AttributeError:  # stream is not defined
            self.minValue = 0
            if values:
                self.maxValue = max(values)
            else:
                self.maxValue = 10

    def ticks(self):
        '''
        Get offset or measure ticks

        >>> s = corpus.parse('bach/bwv281.xml')
        >>> plotS = graph.plot.PlotStream(s)
        >>> ax = graph.axis.OffsetAxis(plotS)
        >>> ax.setBoundariesFromData()
        >>> ax.ticks()  # on whole score, showing anacrusis spacing
        [(0.0, '0'), (1.0, '1'), (5.0, '2'), (9.0, '3'), (13.0, '4'), (17.0, '5'),
         (21.0, '6'), (25.0, '7'), (29.0, '8')]

        >>> a = graph.plot.PlotStream(s.parts[0].flat)  # on a Part
        >>> plotS = graph.plot.PlotStream(s)
        >>> ax = graph.axis.OffsetAxis(plotS)
        >>> ax.setBoundariesFromData()
        >>> ax.ticks()  # on whole score, showing anacrusis spacing
        [(0.0, '0'), (1.0, '1'), (5.0, '2'), (9.0, '3'), (13.0, '4'), (17.0, '5'),
         (21.0, '6'), (25.0, '7'), (29.0, '8')]

        >>> ax.minMaxMeasureOnly = True
        >>> ax.ticks()  # on whole score, showing anacrusis spacing
        [(0.0, '0'), (29.0, '8')]


        >>> ax.minMaxMeasureOnly = False
        >>> ax.minValue = 8
        >>> ax.maxValue = 12
        >>> ax.ticks()
        [(9.0, '3')]

        >>> n = note.Note('a')  # on a raw collection of notes with no measures
        >>> s = stream.Stream()
        >>> s.repeatAppend(n, 20)
        >>> plotS = graph.plot.PlotStream(s)
        >>> ax = graph.axis.OffsetAxis(plotS)
        >>> ax.setBoundariesFromData()
        >>> ax.ticks()
        [(0, '0'), (10, '10'), (20, '20')]
        >>> ax.offsetStepSize = 5
        >>> ax.ticks()
        [(0, '0'), (5, '5'), (10, '10'), (15, '15'), (20, '20')]
        '''
        offsetMap = self.getOffsetMap()
        self.setUseMeasuresFromOffsetMap(offsetMap)

        if self.useMeasures:
            return self._measureTicks(self.minValue, self.maxValue, offsetMap)
        else:  # generate numeric ticks
            # environLocal.printDebug(['using offsets for offset ticks'])
            # get integers for range calculation
            ticks = []  # a list of graphed value, string label pairs
            oMin = int(math.floor(self.minValue))
            oMax = int(math.ceil(self.maxValue))
            for i in range(oMin, oMax + 1, self.offsetStepSize):
                ticks.append((i, '%s' % i))
                # environLocal.printDebug(['ticksOffset():', 'final ticks', ticks])
            return ticks

    def _measureTicks(self, dataMin, dataMax, offsetMap):
        '''
        helper method for ticks() just to pull out code.
        '''
        ticks = []
        # environLocal.printDebug(['using measures for offset ticks'])
        # store indices in offsetMap
        mNoToUse = []
        sortedKeys = list(offsetMap.keys())
        for key in sortedKeys:
            if dataMin <= key <= dataMax:
                # if key == 0.0 and not displayMeasureNumberZero:
                #     continue  # skip
                # if key == sorted(offsetMap.keys())[-1]:
                #    continue  # skip last
                # assume we can get the first Measure in the lost if
                # measurers; this may not always be True
                mNoToUse.append(key)
        # environLocal.printDebug(['ticksOffset():', 'mNotToUse', mNoToUse])

        # just get the min and the max
        if self.minMaxMeasureOnly:
            for i in (0, -1):
                offset = mNoToUse[i]
                mNumber = offsetMap[offset][0].number
                ticks.append((offset, '%s' % mNumber))
        else:  # get all of them
            if len(mNoToUse) > 20:
                # get about 10 ticks
                mNoStepSize = int(len(mNoToUse) / 10)
            else:
                mNoStepSize = 1
            # for i in range(0, len(mNoToUse), mNoStepSize):
            i = 0  # always start with first
            while i < len(mNoToUse):
                offset = mNoToUse[i]
                # this should be a measure object
                foundMeasure = offsetMap[offset][0]
                mNumber = foundMeasure.number
                ticks.append((offset, '%s' % mNumber))
                i += mNoStepSize
        return ticks

    def getOffsetMap(self):
        '''
        Find the first partlike object and get the measureOffsetMap from it, or an
        empty-dict if not.

        >>> b = corpus.parse('bwv66.6')
        >>> p = graph.plot.PlotStream(b)
        >>> ax = graph.axis.OffsetAxis(p, 'x')
        >>> om = ax.getOffsetMap()
        >>> om
        OrderedDict([(0.0, [<music21.stream.Measure 0 offset=0.0>]),
                     (1.0, [<music21.stream.Measure 1 offset=1.0>]),
                     (5.0, [<music21.stream.Measure 2 offset=5.0>]),
                     ...])

        Same if called on a single part:

        >>> p = graph.plot.PlotStream(b.parts[0])
        >>> ax = graph.axis.OffsetAxis(p, 'x')
        >>> om2 = ax.getOffsetMap()
        >>> om2
        OrderedDict([(0.0, [<music21.stream.Measure 0 offset=0.0>]),
                     (1.0, [<music21.stream.Measure 1 offset=1.0>]),
                     (5.0, [<music21.stream.Measure 2 offset=5.0>]),
                     ...])

        But empty if called on a single Measure ...

        >>> p = graph.plot.PlotStream(b.parts[0].getElementsByClass('Measure')[2])
        >>> ax = graph.axis.OffsetAxis(p, 'x')
        >>> om3 = ax.getOffsetMap()
        >>> om3
        {}

        '''
        s = self.stream
        if s is None:
            return {}

        if s.hasPartLikeStreams():
            # if we have part-like sub streams; we can assume that all parts
            # have parallel measures start times here for simplicity
            # take the top part
            offsetMap = s.getElementsByClass(
                'Stream')[0].measureOffsetMap([stream.Measure])
        elif s.hasMeasures():
            offsetMap = s.measureOffsetMap([stream.Measure])
        else:
            offsetMap = {}

        return offsetMap

    def setUseMeasuresFromOffsetMap(self, offsetMap=None):
        '''
        Given an offsetMap and `.useMeasures=None` return
        True or False based on whether the offsetMap or self.getOffsetMap() is
        non-empty.

        >>> b = corpus.parse('bwv66.6')
        >>> p = graph.plot.PlotStream(b)
        >>> ax = graph.axis.OffsetAxis(p, 'x')
        >>> print(ax.useMeasures)
        None
        >>> ax.setUseMeasuresFromOffsetMap()
        True

        Sets `.useMeasures` as a side effect:

        >>> ax.useMeasures
        True

        same as:

        >>> ax = graph.axis.OffsetAxis(p, 'x')
        >>> om = ax.getOffsetMap()
        >>> ax.setUseMeasuresFromOffsetMap(om)
        True

        If `.useMeasures` is set explicitly, then
        we return that

        >>> ax.useMeasures = False
        >>> ax.setUseMeasuresFromOffsetMap()
        False

        Returns False if the offsetMap is empty

        >>> p = graph.plot.PlotStream(b.parts[0].getElementsByClass('Measure')[2])
        >>> axMeasure = graph.axis.OffsetAxis(p, 'x')
        >>> axMeasure.setUseMeasuresFromOffsetMap()
        False
        >>> axMeasure.useMeasures
        False
        '''
        if self.useMeasures is not None:
            return self.useMeasures
        if offsetMap is None:
            offsetMap = self.getOffsetMap()
        self.useMeasures = bool(offsetMap)
        return self.useMeasures


class QuarterLengthAxis(PositionAxis):
    '''
    Axis subclass for dealing with QuarterLengths
    '''
    _DOC_ATTR = {
        'useLogScale': '''
            bool or int for whether to scale numbers logarithmically.  Adds (log2) to the
            axis label if used.  If True (default) then log2 is assumed.  If an int, then
            log the int (say, 10) is used. instead.
        ''',
        'useDurationNames': '''
            If used then duration names replace numbers for ticks.
            If set, probably will want to change tickFontSize in the graph object
        ''',
    }

    labelDefault = 'Quarter Length'
    quantities = ('quarterLength', 'ql', 'quarterlengths', 'durations', 'duration')

    def __init__(self, client=None, axisName='x'):
        super().__init__(client, axisName)
        self.useLogScale = True
        self.useDurationNames = False

    def extractOneElement(self, n, formatDict):
        return self.dataFromQL(n.duration.quarterLength)

    def dataFromQL(self, ql):
        if self.useLogScale:
            x = self.remapQuarterLength(ql)
        elif ql > 0:
            x = float(ql)
        else:
            x = self.graceNoteQL
        return x

    def ticks(self):
        '''
        Get ticks for quarterLength.

        If `remap` is `True` (the default), the `remapQuarterLength()`
        method will be used to scale displayed quarter lengths
        by log base 2.

        Note that mix and max do nothing, but must be included
        in order to set the tick style.


        >>> s = stream.Stream()
        >>> for t in ['32nd', '16th', 'eighth', 'quarter', 'half']:
        ...     n = note.Note()
        ...     n.duration.type = t
        ...     s.append(n)

        >>> plotS = graph.plot.PlotStream(s)
        >>> ax = graph.axis.QuarterLengthAxis(plotS)
        >>> ax.ticks()
        [(-3.0, '0.12'), (-2.0, '0.25'), (-1.0, '0.5'), (0.0, '1.0'), (1.0, '2.0')]

        >>> ax.useLogScale = False
        >>> ax.ticks()
        [(0.125, '0.12'), (0.25, '0.25'), (0.5, '0.5'), (1.0, '1.0'), (2.0, '2.0')]
        >>> ax.useDurationNames = True
        >>> ax.ticks()
        [(0.125, '32nd'), (0.25, '16th'), (0.5, 'Eighth'), (1.0, 'Quarter'), (2.0, 'Half')]

        >>> nGrace = note.Note()
        >>> nGrace.getGrace(inPlace=True)
        >>> s.append(nGrace)
        >>> plotS = graph.plot.PlotStream(s)
        >>> ax = graph.axis.QuarterLengthAxis(plotS)
        >>> ax.ticks()[0]
        (-4.0, '0.0')

        >>> ax.useLogScale = False
        >>> ax.ticks()[0]
        (0.0625, '0.0')
        '''
        s = self.stream
        if not s:
            return []
        elif self.client.recurse:
            sSrc = s.recurse()
        else:
            sSrc = s.iter

        sSrc = sSrc.getElementsByClass(self.client.classFilterList)
        # get all quarter lengths
        mapping = elementAnalysis.attributeCount(sSrc, 'quarterLength')

        ticks = []
        for ql in sorted(mapping):
            x = self.dataFromQL(ql)
            if self.useDurationNames:
                label = duration.Duration(ql).fullName
            else:
                label = str(round(ql, 2))
            ticks.append((x, label))
        return ticks

    def labelLogTag(self):
        '''
        Returns a TeX formatted tag to the axis label depending on whether
        the scale is logarithmic or not.  Checks `.useLogScale`

        >>> a = graph.axis.QuarterLengthAxis()
        >>> a.useLogScale
        True
        >>> a.labelLogTag()
        ' ($log_2$)'

        >>> a.useLogScale = False
        >>> a.labelLogTag()
        ''

        >>> a.useLogScale = 10
        >>> a.labelLogTag()
        ' ($log_10$)'
        '''
        if self.useLogScale is False:
            return ''
        elif self.useLogScale is True:
            return ' ($log_2$)'
        else:
            return ' ($log_{:d}$)'.format(self.useLogScale)

    @property
    def label(self):
        return super().label + self.labelLogTag()

    @label.setter
    def label(self, value):
        super().label = value

    def remapQuarterLength(self, x):
        '''
        Remap a quarter length as its log2.  Essentially it's
        just math.log2(x), but x=0 is replaced with self.graceNoteQL.
        '''
        if x == 0:  # grace note
            x = self.graceNoteQL

        try:
            return math.log2(float(x))
        except ValueError:  # pragma: no cover
            raise GraphException('cannot take log of x value: %s' % x)


class OffsetEndAxis(OffsetAxis):
    '''
    An Axis that gives beginning and ending values for each element
    '''
    _DOC_ATTR = {
        'noteSpacing': '''
            amount in QL to leave blank between untied notes.
            (default = graceNoteQL)
            '''
    }
    quantities = ('offsetEnd', 'timespans', 'timespan')

    def __init__(self, client=None, axisName='x'):
        super().__init__(client, axisName)
        self.noteSpacing = self.graceNoteQL

    def extractOneElement(self, n, formatDict):
        off = float(n.getOffsetInHierarchy(self.stream))
        useQL = float(n.duration.quarterLength)
        if useQL < self.graceNoteQL:
            useQL = self.graceNoteQL
        elif useQL > self.graceNoteQL * 2:
            if hasattr(n, 'tie') and n.tie is not None and n.tie.type in ('start', 'continue'):
                pass
            else:
                useQL -= self.graceNoteQL

        return (off, useQL)

# -----------------------------------------------------------------------------


class DynamicsAxis(Axis):
    '''
    Axis subclass for dealing with Dynamics
    '''
    labelDefault = 'Dynamic'
    quantities = ('dynamic', 'dynamics', 'volume')

    def setBoundariesFromData(self, values=None):
        if values is None:
            self.minValue = 0
            self.maxValue = len(dynamics.shortNames) - 1
        else:
            super().setBoundariesFromData(values)
            self.minValue = int(self.minValue)
            self.maxValue = int(self.maxValue)

    def ticks(self):
        '''
        Utility method to get ticks in dynamic values:

        >>> ax = graph.axis.DynamicsAxis()
        >>> ax.ticks()
        [(0, '$pppppp$'), (1, '$ppppp$'), (2, '$pppp$'), (3, '$ppp$'), (4, '$pp$'),
         (5, '$p$'), (6, '$mp$'), (7, '$mf$'), (8, '$f$'), (9, '$fp$'), (10, '$sf$'),
         (11, '$ff$'), (12, '$fff$'), (13, '$ffff$'), (14, '$fffff$'), (15, '$ffffff$')]

        A minimum and maximum dynamic index can be specified as minValue and maxValue

        >>> ax.minValue = 3
        >>> ax.maxValue = 6
        >>> ax.ticks()
        [(3, '$ppp$'), (4, '$pp$'), (5, '$p$'), (6, '$mp$')]

        '''
        ticks = []
        if self.minValue is None:
            self.setBoundariesFromData()
        for i in range(self.minValue, self.maxValue + 1):
            # place string in tex format for italic display
            ticks.append((i, r'$%s$' % dynamics.shortNames[i]))
        return ticks

# -----------------------------------------------------------------------------


class CountingAxis(Axis):
    '''
    Axis subclass for counting data in another Axis.

    Used for histograms, weighted scatter, etc.

    >>> bach = corpus.parse('bwv66.6')
    >>> plotS = graph.plot.PlotStream(bach)
    >>> plotS.axisX = graph.axis.PitchSpaceAxis(plotS, 'x')
    >>> plotS.axisY = graph.axis.CountingAxis(plotS)
    >>> plotS.doneAction = None
    >>> plotS.run()
    >>> plotS.data
    [(42.0, 1, {}), (45.0, 1, {}), (46.0, 1, {}), (47.0, 5, {}), (49.0, 6, {}), ...]
    '''
    _DOC_ATTR = {
        'countAxes': '''
            a string or tuple of strings representing an axis or axes to use in counting
            ''',
    }

    labelDefault = 'Count'
    quantities = ('count', 'quantity', 'frequency', 'counting')

    def __init__(self, client=None, axisName='y'):
        super().__init__(client, axisName)
        self.countAxes = 'x'

    def postProcessData(self):
        '''
        Replace client.data with a list that only includes each key once.
        '''
        client = self.client
        if client is None:
            return []

        from operator import itemgetter
        countAxes = self.countAxes
        if not common.isIterable(countAxes):
            countAxes = (countAxes,)

        axesIndices = tuple([self.axisDataMap[axisName] for axisName in countAxes])
        thisIndex = self.axisDataMap[self.axisName]
        selector = itemgetter(*axesIndices)
        relevantData = [selector(innerTuple) for innerTuple in client.data]

        # all the format dicts will soon be smooshed, so get all the data from it:
        tupleFormatDict = {}
        for dataPoint in client.data:
            dataIndex = selector(dataPoint)
            formatDict = dataPoint[-1]
            if not isinstance(formatDict, dict):
                continue
            if dataIndex in tupleFormatDict:  # already saw one:
                tupleFormatDict[dataIndex].update(formatDict)
            else:
                tupleFormatDict[dataIndex] = formatDict

        counter = collections.Counter(relevantData)

        newClientData = []
        for counterKey in counter:
            innerList = [None] * (len(axesIndices) + 1)
            if len(axesIndices) > 1:
                for dependentIndex in axesIndices:
                    innerList[dependentIndex] = counterKey[dependentIndex]
            else:  # single axesIndices means the counterKey will not be a tuple:
                innerList[axesIndices[0]] = counterKey
            innerList[thisIndex] = counter[counterKey]
            formatDict = tupleFormatDict.get(counterKey, {})
            newClientData.append(tuple(innerList) + (formatDict,))

        client.data = sorted(newClientData)
        return client.data


# -----------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testCountingAxisFormat(self):
        def countingAxisFormatter(n, formatDict):
            if n.pitch.accidental is not None:
                formatDict['color'] = 'red'
            return n.pitch.diatonicNoteNum

        from music21.graph.plot import Histogram
        from music21 import converter
        s = converter.parse('tinynotation: 4/4 C4 D E F C D# E F#')
        hist = Histogram(s)
        hist.doneAction = None
        hist.axisX = Axis(hist, 'x')
        hist.axisX.extractOneElement = countingAxisFormatter
        hist.run()
        self.assertEqual(hist.data,
                         [(1, 2, {}), (2, 2, {'color': 'red'}),
                          (3, 2, {}), (4, 2, {'color': 'red'})])


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
