#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         correlate.py
# Purpose:      Stream analyzer designed to correlate and graph two properties
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''Various tools and utilities to find correlations between disparate objects in a Stream.

See the chapter :ref:`overviewFormats` for more information and examples of converting formats into and out of music21.
'''


import unittest, doctest, random
import sys

import music21
from music21 import common
from music21 import converter
from music21 import stream
from music21 import note
from music21 import dynamics
from music21 import pitch
from music21 import duration

from music21 import environment
_MOD = 'correlate.py'
environLocal = environment.Environment(_MOD)




#-------------------------------------------------------------------------------
class CorrelateException(Exception):
    pass




#-------------------------------------------------------------------------------
class ActivityMatch(object):
    '''Given a Stream, find if one object is active while another is also active.

    Plotting routines to graph the output of dedicated methods in this class are available. 

    :class:`~music21.graph.PlotScatterPitchSpaceDynamicSymbol` and :class:`~music21.graph.PlotScatterWeightedPitchSpaceDynamicSymbol` employs the :meth:`~music21.analysis.correlate.ActivityMatch.pitchToDynamic` method. Sample output is as follows:

    .. image:: images/PlotScatterWeightedPitchSpaceDynamicSymbol.*
        :width: 600
    
    '''

    def __init__(self, streamObj):
        if not isinstance(streamObj, music21.stream.Stream):
            raise CorrelateException, 'non-stream provided as argument'
        self.streamObj = streamObj
        self.data = None


    def _findActive(self, objNameSrc=None, objNameDst=None):
        '''Do the analysis, finding correlations of src with dst
        returns an ordered list of dictionaries, in the form
        {'src': obj, 'dst': [objs]}

        '''        
        if objNameSrc == None:
            objNameSrc = note.Note
        if objNameDst == None:
            objNameDst = dynamics.Dynamic

        post = []
        streamFlat = self.streamObj.flat

        streamFlat = streamFlat.extendDuration(objNameDst)

        # get each src object; create a dictionary for each
        for element in streamFlat.getElementsByClass(objNameSrc):
            post.append({'src':element, 'dst':[]})

        # get each dst object, and find its start and end time
        # then, go through each source object, and see if this
        # dst object is within the source objects boundaries
        # if so, append it to the source object's dictionary
        for element in streamFlat.getElementsByClass(objNameDst):
            #print _MOD, 'dst', element
            dstStart = element.offset
            dstEnd = dstStart + element.duration.quarterLength

            for entry in post:
                # here, we are only looking if start times match
                if (entry['src'].offset >= dstStart and 
                    entry['src'].offset <= dstEnd):
                    # this is match; add a reference to the element
                    entry['dst'].append(element)            
                
        self.data = post
        return self.data


    def pitchToDynamic(self, dataPoints=True):
        '''Create an analysis of pitch to dynamic symbol.

        If `dataPoints` is True, all data matches between source and destination are returned. If false, 3 point weighted coordinates are created for each unique match. 

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv8.6.xml')
        >>> am = analysis.correlate.ActivityMatch(s[0].flat.sorted)
        >>> am.pitchToDynamic()
        Traceback (most recent call last):
        CorrelateException: cannot create correlation an object that is not found in the Stream: <class 'music21.dynamics.Dynamic'>

        >>> s = corpus.parseWork('schumann/opus41no1', 2)
        >>> am = analysis.correlate.ActivityMatch(s[0].flat.sorted)
        >>> data = am.pitchToDynamic()
        >>> len(data)
        401
        '''
        objNameSrc = note.Note
        objNameDst = dynamics.Dynamic

        for objName in [objNameSrc, objNameDst]:
            dstCheck = self.streamObj.flat.getElementsByClass(objName)
            if len(dstCheck) == 0:
                raise CorrelateException('cannot create correlation an object that is not found in the Stream: %s' % objName)

        self._findActive(objNameSrc, objNameDst)

        fx = lambda e: e.ps
        # get index value used for dynamics
        fy = lambda e: dynamics.shortNames.index(e.value)

        pairs = []
        for entry in self.data:
            entrySrc = entry['src']
            # there may be multiple dst:
            for entryDst in entry['dst']:
                pairs.append([fx(entrySrc), fy(entryDst)])

        # if requesting data points, just return all points
        if dataPoints:
            return pairs

        # find unique coords and count instances
        dict = {}
        for coord in pairs: 
            coord = tuple(coord)
            if coord not in dict.keys():
                dict[coord] = 0
            dict[coord] += 1
        pairs = []
        for key in dict.keys():
            pairs.append((key[0], key[1], dict[key]))
        return pairs







#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
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



    def testActivityMatchPitchToDynamic(self):
        from music21 import corpus

        #a = corpus.parseWork('bach/bwv8.6.xml')
        #a = corpus.parseWork('beethoven/opus18no1', 2)
        a = corpus.parseWork('schumann/opus41no1', 2)

        # just get the soprano part
        b = ActivityMatch(a[0].flat.sorted)
        dataPairs = b.pitchToDynamic()
        self.assertEqual(len(dataPairs), 401)


#-------------------------------------------------------------------------------
if __name__ == "__main__":

    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof

