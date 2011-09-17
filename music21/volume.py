# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         volume.py
# Purpose:      Objects for representing volume, amplitude, and related 
#               parameters
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''This module defines the object model of Volume, covering all representation of amplitude, volume, velocity, and related parameters.  
'''
 
import unittest

import music21
from music21 import common



#-------------------------------------------------------------------------------
class VolumeException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Volume(object):
    '''The Volume object lives on NotRest objects and subclasses. It is not a Music21Object subclass. 

    >>> from music21 import *
    >>> v = volume.Volume()     
    '''
    def __init__(self, parent=None, velocity=None):

        # store a reference to the parent, as we use this to do context 
        # will use property; if None will leave as None
        self._parent = None
        self.parent = parent    
        self._velocity = None
        if velocity is not None:
            self.velocity = velocity

    def __deepcopy__(self, memo=None):
        '''Need to manage copying of weak ref; when copying, do not copy weak ref, but keep as a reference to the same object. 
        '''
        new = self.__class__()
        new.mergeAttributes(self) # will get all numerical values
        # keep same weak ref object
        new._parent = self._parent
        return new


    def __repr__(self):
        return "<music21.voliume.Volume realized=%s>" % round(self.realized, 2)

    #---------------------------------------------------------------------------
    # properties
        
    def _getParent(self):
        if self._parent is None:
            return None
        post = common.unwrapWeakref(self._parent)
        if post is None:
            # set attribute for speed
            self._parent = None
        return post

    def _setParent(self, parent):
        if parent is not None:
            if hasattr(parent, 'classes') and 'NotRest' in parent.classes:
                self._parent = common.wrapWeakref(parent)
        else:
            self._parent = None

    parent = property(_getParent, _setParent, doc = '''
        Get or set the parent, which must be a note.NotRest subclass. The parent is wrapped in a weak reference.
        ''')

    def _getVelocity(self):
        return self._velocity
        
    def _setVelocity(self, value):
        if not common.isNum(value):
            raise VolumeException('value provided for velocity must be a number, not %s' % value)
        if value < 0:
            self._velocity = 0
        elif value > 127:
            self._velocity = 127
        else:
            self._velocity = value

    velocity = property(_getVelocity, _setVelocity, doc = '''
        Get or set the velocity value, a numerical value between 0 and 127 and available setting amplitude on each Note or Pitch in chord. 

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.volume.velocity = 20
        >>> n.volume.parent == n
        True
        >>> n.volume.velocity 
        20
        ''')


    def _getVelocityScalar(self):
        # multiplying by 1/127. for performance
        return self._velocity * 0.007874015748031496
        
    def _setVelocityScalar(self, value):
        if not common.isNum(value):
            raise VolumeException('value provided for velocityScalar must be a number, not %s' % value)
        if value < 0:
            scalar = 0
        elif value > 1:
            scalar = 1
        else:
            scalar = value
        self._velocity = int(round(scalar * 127))

    velocityScalar = property(_getVelocityScalar, _setVelocityScalar, doc = '''
        Get or set the velocityScalar value, a numerical value between 0 and 1 and available setting amplitude on each Note or Pitch in chord. This value is mapped to the range 0 to 127 on output.

        Note that this value is derived from the set velocity value. Floating point error seen here will not be fond in the velocity value. 

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.volume.velocityScalar = .5
        >>> n.volume.velocity
        64
        >>> n.volume.velocity = 127
        >>> n.volume.velocityScalar
        1.0
        ''')

    #---------------------------------------------------------------------------
    # high-level methods

    def getContextByClass(self, className, sortByCreationTime=False,         
            getElementMethod='getElementAtOrBefore'):
        '''Simulate get context by class method as found on parent NotRest object.
        '''
        p = self.parent # unwrap weak ref
        if p is None:
            raise VolumeException('cannot call getContextByClass because parent is None.')
        # call on parent object
        return p.getContextByClass(className, serialReverseSearch=True,
            callerFirst=None, sortByCreationTime=sortByCreationTime, prioritizeActiveSite=True, getElementMethod=getElementMethod, 
            memo=None)

    def getDynamicContext(self):
        '''Return the dynamic context of this Volume, based on the position of the NotRest parent of this object.
        '''
        # TODO: find wedges and crescendi too
        return self.getContextByClass('Dynamic')


    def mergeAttributes(self, other):
        '''Given another Volume object, gather all attributes except parent. Values are always copied, not passed by reference. 

        >>> from music21 import *
        >>> n1 = note.Note()
        >>> v1 = volume.Volume()
        >>> v1.velocity = 111
        >>> v1.parent = n1

        >>> v2 = volume.Volume()
        >>> v2.mergeAttributes(v1)
        >>> v2.parent == None
        True
        >>> v2.velocity
        111
        '''
        if other is not None:      
            self._velocity = other._velocity

        

    def getRealized(self, dynamicContext=True, useVelocity=True, 
        useArticulations=True, baseLevel=1.0):
        '''Get a realized unit-interval scalar for this Volume. This scalar is to be applied to the final amplitude scalar, whatever that may be.
 
        This can optionally take into account `dynamicContext`, `useVelocity`, and `useArticulation`.
        '''
        val = baseLevel
        if dynamicContext:
            pass
        if useVelocity:
            if self._velocity is not None:
                val = val * self.velocityScalar
        if useArticulations:
            pass
        # might to rebalance range after scalings       
        return val

    realized = property(getRealized, doc='''
        Return the realized unit-interval scalar for this Volume

        >>> from music21 import *
        >>> 
        ''')

        
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        from music21 import volume, note

        n1 = note.Note()
        v = volume.Volume(parent=n1)
        self.assertEqual(v.parent, n1)
        del n1
        # weak ref does not exist
        self.assertEqual(v.parent, None)


    def testGetContextSearchA(self):
        from music21 import stream, note, volume, dynamics
        
        s = stream.Stream()
        d1 = dynamics.Dynamic('mf')
        s.insert(0, d1)
        d2 = dynamics.Dynamic('f')
        s.insert(2, d2)

        n1 = note.Note('g')
        v1 = volume.Volume(parent=n1)
        s.insert(4, n1)

        # can get dyanmics from volume object
        self.assertEqual(v1.getContextByClass('Dynamic'), d2)
        self.assertEqual(v1.getDynamicContext(), d2)


    def testGetContextSearchB(self):
        from music21 import stream, note, volume, dynamics
        
        s = stream.Stream()
        d1 = dynamics.Dynamic('mf')
        s.insert(0, d1)
        d2 = dynamics.Dynamic('f')
        s.insert(2, d2)

        n1 = note.Note('g')
        s.insert(4, n1)

        # can get dyanmics from volume object
        self.assertEqual(n1.volume.getDynamicContext(), d2)


    def testDeepCopyA(self):
        import copy
        from music21 import volume, note    
        n1 = note.Note()

        v1 = volume.Volume()
        v1.velocity = 111
        v1.parent = n1
        
        v1Copy = copy.deepcopy(v1)
        self.assertEqual(v1.velocity, 111)
        self.assertEqual(v1Copy.velocity, 111)

        self.assertEqual(v1.parent, n1)
        self.assertEqual(v1Copy.parent, n1)
        


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof




