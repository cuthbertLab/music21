# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         correlate.py
# Purpose:      Stream analyzer designed to correlate and graph two properties
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2009-2010 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Various tools and utilities to find correlations between disparate objects in a Stream.
'''
from __future__ import annotations

from collections import OrderedDict
import unittest

from music21 import exceptions21

from music21 import note
from music21 import chord
from music21 import dynamics
from music21 import environment

environLocal = environment.Environment('analysis.correlate')


# ------------------------------------------------------------------------------
class CorrelateException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------
class ActivityMatch:
    '''
    Given a Stream, find if one object is active while another is also active.

    Plotting routines to graph the output of dedicated methods in this class are available.

    :class:`~music21.graph.plot.ScatterPitchSpaceDynamicSymbol` and
    :class:`~music21.graph.plot.ScatterWeightedPitchSpaceDynamicSymbol`
    employs the :meth:`~music21.analysis.correlate.ActivityMatch.pitchToDynamic` method.

    Sample output is as follows:

    .. image:: images/ScatterWeightedPitchSpaceDynamicSymbol.*
        :width: 600

    '''
    def __init__(self, streamObj):
        if not hasattr(streamObj, 'classes') or 'Stream' not in streamObj.classes:
            raise CorrelateException('non-stream provided as argument')
        self.streamObj = streamObj
        self.data = None


    def _findActive(self, objNameSrc=None, objNameDst=None):
        '''
        Do the analysis, finding correlations of src with dst
        returns an ordered list of dictionaries, in the form
        {'src': obj, 'dst': [objs]}

        '''
        if objNameSrc is None:
            objNameSrc = (note.Note, chord.Chord)
        if objNameDst is None:
            objNameDst = dynamics.Dynamic

        post = []
        streamFlat = self.streamObj.flatten()

        streamFlat = streamFlat.extendDuration(objNameDst)

        # get each src object; create a dictionary for each
        for element in streamFlat.getElementsByClass(objNameSrc):
            post.append({
                'src': element,
                'dst': [],
            })

        # get each dst object, and find its start and end time
        # then, go through each source object, and see if this
        # dst object is within the source objects boundaries
        # if so, append it to the source object's dictionary
        for element in streamFlat.getElementsByClass(objNameDst):
            dstStart = element.offset
            dstEnd = dstStart + element.duration.quarterLength

            for entry in post:
                # here, we are only looking if start times match
                if dstStart <= entry['src'].offset <= dstEnd:
                    # this is match; add a reference to the element
                    entry['dst'].append(element)

        self.data = post
        # environLocal.printDebug(['_findActive', self.data])
        return self.data


    def pitchToDynamic(self, dataPoints=True):
        '''
        Create an analysis of pitch to dynamic symbol.

        If `dataPoints` is True, all data matches between source and destination are returned.
        If False, 3 point weighted coordinates are created for each unique match.

        No dynamics here.

        >>> s = corpus.parse('bach/bwv8.6.xml')
        >>> am = analysis.correlate.ActivityMatch(s.parts.first().flatten())
        >>> am.pitchToDynamic()
        Traceback (most recent call last):
        music21.analysis.correlate.CorrelateException: cannot create correlation:
            an object that is not found in the Stream: <class 'music21.dynamics.Dynamic'>

        Many dynamics

        >>> s = corpus.parse('schoenberg/opus19/movement2')
        >>> am = analysis.correlate.ActivityMatch(s.parts.first().flatten())
        >>> data = am.pitchToDynamic()
        >>> len(data)
        39
        >>> data[0]
        (83.0, 7)
        '''
        objNameSrc = (note.Note, chord.Chord)
        # objNameSrc = note.Note
        objNameDst = dynamics.Dynamic

        for objName in [objNameSrc, objNameDst]:
            dstCheck = self.streamObj.recurse().getElementsByClass(objName)
            if not dstCheck:
                raise CorrelateException('cannot create correlation: an object '
                                         + f'that is not found in the Stream: {objName}')

        self._findActive(objNameSrc, objNameDst)

        fx = lambda e: e.pitch.ps
        # get index value used for dynamics
        fy = lambda e: dynamics.shortNames.index(e.value)

        # TODO: needs to handle chords as entrySrc
        pairs = []
        for entry in self.data:
            entrySrc = entry['src']
            # there may be multiple dst:

            if entrySrc.isChord:
                sub = list(entrySrc)
            else:
                sub = [entrySrc]

            for entrySrc in sub:
                for entryDst in entry['dst']:
                    x = fx(entrySrc)
                    y = fy(entryDst)
                    if x is None or y is None:
                        pass
                    else:
                        pairs.append((x, y))

        # if requesting data points, just return all points
        if dataPoints:
            return pairs

        # find unique coords and count instances
        dictionary = OrderedDict()
        for coord in pairs:
            if coord not in dictionary:
                dictionary[coord] = 0
            dictionary[coord] += 1
        pairs = []
        for key in dictionary:
            pairs.append((key[0], key[1], dictionary[key]))
        return pairs







# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())

    def testActivityMatchPitchToDynamic(self):
        from music21 import corpus

        a = corpus.parse('schoenberg/opus19', 2)

        b = ActivityMatch(a.flatten())
        dataPairs = b.pitchToDynamic()
        # print(dataPairs)
        # previous pair count was 401
        self.assertEqual(len(dataPairs), 111)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)

