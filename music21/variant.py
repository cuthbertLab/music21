# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         variant.py
# Purpose:      Translate MusicXML and music21 objects
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest
import copy

import music21

from music21 import common
from music21 import stream
from music21 import environment
_MOD = "variant.py" # TODO: call variant
environLocal = environment.Environment(_MOD)

'''The :class:`~music21.variant.Variant` and its subclasses.
'''


# variant objs as groups
# ossia1 as a group
# variant group
# idea of m5, m7; each have two variants, each belonging to one group

# Stream.activateVariant() , take a group name as arg
# if None is given, take first
# overlapped content becomes
# inPlace: replaces original; original becomes a variant
# idea of performanceScale that realizes 



class Variant(music21.Music21Object):
    '''A Music21Object that stores elements like a Stream, but does not represent itself externally to a Stream; i.e., the contents of a Variant are not flattened.

    This is accomplished not by subclassing, but by object composition: similar to the Spanner, the Variant contains a Stream as a private attribute. Calls to this Stream, for the Variant, are automatically delegated by use of the __getattr__ method. Special casses are overridden or managed as necessary: e.g., the Duration of a Variant is generally always zero. 

    To use Variants from a Stream, see the :func:`~music21.stream.Stream.activateVariants` method. 

    >>> from music21 import *
    >>> v = variant.Variant()
    >>> v.repeatAppend(note.Note(), 8)
    >>> len(v.notes)
    8
    >>> v.highestTime
    0.0
    >>> v.duration # handled by Music21Object
    <music21.duration.Duration 0.0>
    >>> v.isStream
    False

    >>> s = stream.Stream()
    >>> s.append(v)
    >>> s.append(note.Note())
    >>> s.highestTime
    1.0
    >>> s.show('t')
    {0.0} <music21.variant.Variant object at ...>
    {0.0} <music21.note.Note C>
    >>> s.flat.show('t')
    {0.0} <music21.variant.Variant object at ...>
    {0.0} <music21.note.Note C>
    '''

    classSortOrder = 0  # variants should always come first?
    isVariant = True

    # this copies the init of Streams
    def __init__(self, givenElements=None, *args, **keywords):
        music21.Music21Object.__init__(self)
        self._cache = {}
        self.exposeTime = False
        self._stream = stream.VariantStorage(givenElements=givenElements, 
                                             *args, **keywords)

    def __deepcopy__(self, memo):
        new = self.__class__()
        old = self
        for name in self.__dict__.keys():
            if name.startswith('__'):
                continue
            if name == '_cache':
                continue
            part = getattr(self, name)
            # functionality duplicated from Music21Object
            if name == '_activeSite':
                setattr(new, name, self.activeSite)
            elif name == '_definedContexts':
                newValue = copy.deepcopy(part, memo)
                newValue.containedById = id(new)
                setattr(new, name, newValue)
            # do not deepcopy _components, as this will copy the 
            # contained objects
            # this means that the new object is not really free of the 
            # old elements it described
            elif name == '_stream':
                # this passes references; does not copy contained
                #for c in old._stream:
                #    new._stream.insert(c.getOffsetBySite(old._stream), c)
                # this copies the contained stream
                new._stream = copy.deepcopy(old._stream)
            else: 
                #environLocal.printDebug(['Spanner.__deepcopy__', name])
                newValue = copy.deepcopy(part, memo)
                setattr(new, name, newValue)
        # do after all other copying
        new._idLastDeepCopyOf = id(self)
        return new


    #---------------------------------------------------------------------------
    # as _stream is a private Stream, unwrap/wrap methods need to override
    # Music21Object to get at these objects 
    # this is the same as with Spanners

    def unwrapWeakref(self):
        '''Overridden method for unwrapping all Weakrefs.
        '''
        # call base method: this gets defined contexts and active site
        music21.Music21Object.unwrapWeakref(self)
        # for contained objects that have weak refs
        self._stream.unwrapWeakref()
        # this presently is not a weakref but in case of future changes


    def wrapWeakref(self):
        '''Overridden method for unwrapping all Weakrefs.
        '''
        # call base method: this gets defined contexts and active site
        music21.Music21Object.wrapWeakref(self)
        self._stream.wrapWeakref()


    def __getattr__(self, attr):
        '''This defers all calls not defined in this Class to calls on the privately contained Stream.
        '''
        #environLocal.pd(['relaying unmatched attribute request to private Stream'])

        # must mask pitches so as not to recurse
        # TODO: check tt recurse does not go into this
        if attr in ['flat', 'pitches']: 
            raise AttributeError
        try:
            return getattr(self._stream, attr)
        except:
            raise
        
    def __getitem__(self, key):
        return self._stream.__getitem__(key)
        

    def __len__(self):
        return len(self._stream)


    def getElementIds(self):
        if 'elementIds' not in self._cache or self._cache['elementIds'] is None:
            self._cache['elementIds'] = [id(c) for c in self._stream._elements]
        return self._cache['elementIds']


    def replaceElement(self, old, new):
        '''When copying a Variant, we need to update the Variant with new references for copied elements. Given the old component, this method will replace the old with the new.

        The `old` parameter can be either an object or object id. 

        This method is very similar to the replaceComponent method on Spanner. 

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> c1 = clef.AltoClef()
        >>> c2 = clef.BassClef()
        >>> sl = spanner.Spanner(n1, n2, c1)
        >>> sl.replaceComponent(c1, c2)
        >>> sl[-1] == c2
        True
        '''
        if old is None:
            return None # do nothing
        if common.isNum(old):
            # this must be id(obj), not obj.id
            e = self._stream.getElementByObjectId(old)
            if e is not None:
                self._stream.replace(e, new, allTargetSites=False)
        else:
            # do not do all Sites: only care about this one
            self._stream.replace(old, new, allTargetSites=False)


    #---------------------------------------------------------------------------
    # Stream  simulation/overrides

    def _getHighestTime(self):
        if self.exposeTime:
            return self._stream.highestTime
        else:
            return 0.0

    highestTime = property(_getHighestTime, doc='''
        This property masks calls to Stream.highestTime. Assuming `exposeTime` is False, this always returns zero, making the Variant always take zero time. 

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.highestTime
        0.0

        ''')

    def _getHighestOffset(self):
        if self.exposeTime:
            return self._stream.highestOffset
        else:
            return 0.0

    highestOffset = property(_getHighestOffset, doc='''
        This property masks calls to Stream.highestOffset. Assuming `exposeTime` is False, this always returns zero, making the Variant always take zero time. 

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.highestOffset
        0.0

        ''')

    def show(self, fmt=None, app=None):
        '''
        Call show() on the Stream contained by this Variant. 

        This method must be overridden, otherwise Music21Object.show() is called.

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.repeatAppend(note.Note(quarterLength=.25), 8)
        >>> v.show('t')
        {0.0} <music21.note.Note C>
        {0.25} <music21.note.Note C>
        {0.5} <music21.note.Note C>
        {0.75} <music21.note.Note C>
        {1.0} <music21.note.Note C>
        {1.25} <music21.note.Note C>
        {1.5} <music21.note.Note C>
        {1.75} <music21.note.Note C>
        '''
        self._stream.show(fmt=fmt, app=app)



    #---------------------------------------------------------------------------
    # particular to this class

    def _getContainedHighestTime(self):
        return self._stream.highestTime

    containedHighestTime = property(_getContainedHighestTime, doc='''
        This property calls the contained Stream.highestTime.

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.containedHighestTime
        4.0
        ''')

    def _getContainedHighestOffset(self):
        return self._stream.highestOffset

    containedHighestOffset = property(_getContainedHighestOffset, doc='''
        This property calls the contained Stream.highestOffset.

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.append(note.Note())
        >>> v.containedHighestOffset
        4.0

        ''')

    def _getContainedSite(self):
        return self._stream

    containedSite = property(_getContainedSite, doc='''
        Return a reference to the Stream contained in this Variant.
        ''')



#-------------------------------------------------------------------------------
class VariantBundle(object):
    '''A utility object for processing collections of Varaints. 

    This object serves a very similar purpose as the SpannerBundle; Variants and Spanners are similar in design and both require special handling in copying. 
    '''

    def __init__(self, *arguments, **keywords):
        self._storage = [] # a simple list, not a Stream
        for arg in arguments:
            if common.isListLike(arg):
                for e in arg:
                    self._storage.append(e)    
            # take a Stream and use its .variants property to get all Variants            
            elif arg.isStream:
                for e in arg.variants:
                    self._storage.append(e)
            # assume its a spanner
            elif 'Variant' in arg.classes:
                self._storage.append(arg)


    def __len__(self):
        return len(self._storage)

    def __repr__(self):
        return '<music21.variant.VariantBundle of size %s>' % self.__len__()

    def replaceElement(self, old, new):
        '''Given a variant component (an object), replace all old components with new components for all Variant objects contained in this bundle.

        The `old` parameter can be either an object or object id. 

        If no replacements are found, no errors are raised.
        '''
        # idTarget is the old id that we want to replace
        if common.isNum(old): # assume this is an id
            idTarget = old
        else:
            idTarget = id(old)

        # looking at each variant, if we w find that it includes an id to 
        # an object listed as old, replace it with the object listed as new
        for v in self._storage: # Variants in a list
            if idTarget in v.getElementIds():
                v.replaceElement(old, new)



#-------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasicA(self):
        from music21 import variant, stream, note

        o = variant.Variant()
        o.append(note.Note('G3', quarterLength=2.0))
        o.append(note.Note('f3', quarterLength=2.0))
        
        self.assertEqual(o.highestOffset, 0)
        self.assertEqual(o.highestTime, 0)

        o.exposeTime = True

        self.assertEqual(o.highestOffset, 2.0)
        self.assertEqual(o.highestTime, 4.0)


    def testBasicB(self):
        '''Testing relaying attributes requests to private Stream with __getattr__
        '''
        from music21 import variant, stream, note

        v = variant.Variant()
        v.append(note.Note('G3', quarterLength=2.0))
        v.append(note.Note('f3', quarterLength=2.0))
        # these are Stream attributes
        self.assertEqual(v.highestOffset, 0.0)
        self.assertEqual(v.highestTime, 0.0)

        self.assertEqual(len(v.notes), 2)
        self.assertEqual(v.hasElementOfClass('Note'), True)
        v.pop(1) # remove the last tiem

        self.assertEqual(v.highestOffset, 0.0)
        self.assertEqual(v.highestTime, 0.0)
        self.assertEqual(len(v.notes), 1)

        #v.show('t')

    def testVariantGroupA(self):
        '''Variant groups are used to distinguish
        '''
        from music21 import variant
        v1 = variant.Variant()
        v1.groups.append('alt-a')

        v1 = variant.Variant()
        v1.groups.append('alt-b')
        self.assertEqual('alt-b' in v1.groups, True)


    def testVariantClassA(self):
        from music21 import stream, variant, note

        m1 = stream.Measure()
        v1 = variant.Variant()
        v1.append(m1)

        self.assertEqual(v1.isClassOrSubclass(['Variant']), True)

        self.assertEqual(v1.hasElementOfClass('Variant'), False)
        self.assertEqual(v1.hasElementOfClass('Measure'), True)


    def testDeepCopyVariantA(self):
        from music21 import note, stream, variant
    
        s = stream.Stream()
        s.repeatAppend(note.Note('G4'), 8)
        vn1 = note.Note('F#4')
        vn2 = note.Note('A-4')
    
        v1 = variant.Variant([vn1, vn2])
        v1Copy = copy.deepcopy(v1)
        # copies stored objects; they point to the different Notes vn1/vn2
        self.assertEqual(v1Copy[0] is v1[0], False)
        self.assertEqual(v1Copy[1] is v1[1], False)
        self.assertEqual(v1[0] is vn1, True)
        self.assertEqual(v1Copy[0] is vn1, False)
    
        # normal in-place variant functionality
        s.insert(5, v1)
        self.assertEqual(str([p for p in s.pitches]), 
            '[G4, G4, G4, G4, G4, G4, G4, G4]')
        sv = s.activateVariants(inPlace=False)
        self.assertEqual(str([p for p in sv.pitches]), 
            '[G4, G4, G4, G4, G4, F#4, A-4, G4, G4]')
    
        # test functionality on a deepcopy    
        sCopy = copy.deepcopy(s)
        self.assertEqual(len(sCopy.variants), 1)
        self.assertEqual(str([p for p in sCopy.pitches]), 
            '[G4, G4, G4, G4, G4, G4, G4, G4]')
        sCopy.activateVariants(inPlace=True)
        self.assertEqual(str([p for p in sCopy.pitches]), 
            '[G4, G4, G4, G4, G4, F#4, A-4, G4, G4]')


    def testDeepCopyVariantB(self):
        from music21 import note, stream, variant
    
        s = stream.Stream()
        s.repeatAppend(note.Note('G4'), 8)
        vn1 = note.Note('F#4')
        vn2 = note.Note('A-4')
        v1 = variant.Variant([vn1, vn2])
        s.insert(5, v1)
    
        # as we deepcopy the elements in the variants, we have new Notes
        sCopy = copy.deepcopy(s)
        sCopy.activateVariants(inPlace=True)
        self.assertEqual(str([p for p in sCopy.pitches]), 
            '[G4, G4, G4, G4, G4, F#4, A-4, G4, G4]')
        # can transpose the note in place
        sCopy.notes[5].transpose(12, inPlace=True)
        self.assertEqual(str([p for p in sCopy.pitches]), 
            '[G4, G4, G4, G4, G4, F#5, A-4, G4, G4]')
    
        # however, if the the Variant deepcopy still references the original
        # notes it had, then when we try to activate the variant in the 
        # in original Stream, we would get unexpected results (the octave shift)
    
        s.activateVariants(inPlace=True)
        self.assertEqual(str([p for p in s.pitches]), 
            '[G4, G4, G4, G4, G4, F#4, A-4, G4, G4]')



    def testVariantBundleA(self):
        from music21 import note, stream, variant

        s = stream.Stream()
        s.repeatAppend(note.Note('G4'), 8)
        vn1 = note.Note('F#4')
        vn2 = note.Note('A-4')
        v1 = variant.Variant([vn1, vn2])
        s.insert(5, v1)

        vb = s.variantBundle
        self.assertEqual(str(vb), '<music21.variant.VariantBundle of size 1>')
        self.assertEqual(len(vb), 1) # has one variant

if __name__ == "__main__":
    music21.mainTest(Test)




