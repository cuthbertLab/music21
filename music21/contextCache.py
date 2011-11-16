
from music21 import common

import music21
import unittest


class ContextCacheException(Exception):
    pass


#-------------------------------------------------------------------------------
class ContextCache(object):
    def __init__(self):
        self._cache = {}

    def _getKey(self, className, callerFirst, getElementMethod):
        if not isinstance(className, str):
            raise ContextCacheException('cannot cache a class name given as a string')
        return (className, id(callerFirst), getElementMethod)
        #return (className, getElementMethod)


    def add(self, className, callerFirst, getElementMethod, match):
        # store a context request
        key = self._getKey(className, callerFirst, getElementMethod)
        
        cf = common.wrapWeakref(callerFirst)
        m = common.wrapWeakref(match)

        self._cache[key] = {'match':m, 'callerFirst':cf}


    def get(self, className, callerFirst, getElementMethod):
        '''
        >>> from music21 import *
        >>> cc = contextCache.ContextCache()
        >>> n1 = note.Note()
        >>> ts1 = meter.TimeSignature()
        >>> cc.add('TimeSignature', n1, 'getElementAtOrBefore', ts1)
        >>> cc.get('TimeSignature', n1, 'getElementAtOrBefore') == ts1
        True
        >>> del ts1 # if we delete the found obj we get None 
        >>> cc.get('TimeSignature', n1, 'getElementAtOrBefore') == None
        True
        '''

        key = self._getKey(className, callerFirst, getElementMethod)
        try:
            data = self._cache[key]
        except KeyError:
            return None
        # both caller and the match must still exist
        cf = common.unwrapWeakref(data['callerFirst'])
        if cf is None:
            return None
        m = common.unwrapWeakref(data['match'])
        if m is None:   
            return None
        return m




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass




#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []

if __name__ == '__main__':
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof



