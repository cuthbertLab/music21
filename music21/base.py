# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         base.py
# Purpose:      Music21 base classes and important utilities
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2006-2015 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
`music21.base` is what you get in `music21` if you type ``import music21``. It
contains all the most low-level objects that also appear in the music21 module
(i.e., music21.base.Music21Object is the same as music21.Music21Object).

Music21 base classes for :class:`~music21.stream.Stream` objects and all
elements contained within them including Notes, etc.. Additional objects for
defining and manipulating elements are included.

The namespace of this file, as all base.py files, is loaded into the package
that contains this file via __init__.py. Everything in this file is thus
available after importing music21.

>>> import music21
>>> music21.Music21Object
<class 'music21.base.Music21Object'>

>>> music21.VERSION_STR
'2.1.2'

Alternatively, after doing a complete import, these classes are available
under the module "base":

>>> base.Music21Object
<class 'music21.base.Music21Object'>
'''
from __future__ import (print_function, division)

import collections
import copy
import sys
import types
import unittest

from music21.test.testRunner import mainTest
from music21.ext import six



#------------------------------------------------------------------------------
# version string and tuple must be the same

from music21._version import __version__, __version_info__
VERSION = __version_info__
VERSION_STR = __version__
#------------------------------------------------------------------------------
__all__ = ['Music21Exception', 
           'SitesException', 
           'Music21ObjectException',
           'ElementException', 
           
           'Groups',            
           'Music21Object',
           'ElementWrapper',
           
           'VERSION', 
           'VERSION_STR',            
           ]
## N.B. for eclipse "all" import working, we need to list this 
#       separately in "music21/__init__.py"
##      so make sure to update in both places

#-----all exceptions are in the exceptions21 package.
from music21 import exceptions21

Music21Exception = exceptions21.Music21Exception

from music21.sites import SitesException

from music21 import sites
from music21 import common
from music21 import defaults
from music21 import derivation
from music21 import duration
from music21 import environment

from music21.common import opFrac

_MOD = 'music21.base.py'
environLocal = environment.Environment(_MOD)


# check external dependencies and display
_missingImport = []
import imp
for modName in ('matplotlib', 'numpy', 'scipy'):    
    try:
        imp.find_module(modName)
    except ImportError:
        _missingImport.append(modName)

# used for better PNG processing in lily -- not very important
#try:
#    from PIL import Image
#except ImportError:
#    try:
#         import Image
#    except ImportError:
#        _missingImport.append('PIL')

# as this is only needed for one module, and error messages print
# to standard io, this has been removed
# try:
#     import pyaudio
# except (ImportError, SystemExit):
#     _missingImport.append('pyaudio')
    #sys.stderr.write('pyaudio is installed but PortAudio is not -- ' + 
    #                 're-download pyaudio at http://people.csail.mit.edu/hubert/pyaudio/')

if _missingImport:
    if environLocal['warnings'] in (1, '1', True):
        environLocal.warn(common.getMissingImportStr(_missingImport),
        header='music21:')

class Music21ObjectException(exceptions21.Music21Exception):
    pass

class ElementException(exceptions21.Music21Exception):
    pass

#------------------------------------------------------------------------------
# private metaclass...
_SortTuple = collections.namedtuple('SortTuple', ['atEnd','offset','priority',
                                                  'classSortOrder','isNotGrace','insertIndex'])

#------------------------------------------------------------------------------
# make subclass of set once that is defined properly


class Groups(list): # no need to inherit from slotted object
    '''
    Groups is a list (subclass) of strings used to identify 
    associations that an element might have.

    The Groups object enforces that all elements must be strings, and that
    the same element cannot be provided more than once.

    >>> g = Groups()
    >>> g.append("hello")
    >>> g[0]
    'hello'

    >>> g.append("hello") # not added as already present
    >>> len(g)
    1

    >>> g
    ['hello']

    >>> g.append(5)
    Traceback (most recent call last):
    GroupException: Only strings can be used as group names
    '''
    # could be made into a set instance, but actually
    # timing: a subclassed list and a set are almost the same speed 
    # and set does not allow calling by number
    
    # this speeds up creation slightly...
    __slots__ = ()
    
    def append(self, value):
        if isinstance(value, six.string_types):
            # do not permit the same entry more than once
            if not list.__contains__(self, value):
                list.append(self, value)
        else:
            raise exceptions21.GroupException("Only strings can be used as group names")

    def __setitem__(self, i, y):
        if isinstance(y, six.string_types):
            list.__setitem__(self, i, y)
        else:
            raise exceptions21.GroupException("Only strings can be used as group names")

    def __eq__(self, other):
        '''
        Test Group equality. In normal lists, order matters; here it does not.

        >>> a = base.Groups()
        >>> a.append('red')
        >>> a.append('green')
        >>> a
        ['red', 'green']

        >>> b = base.Groups()
        >>> b.append('green')
        >>> a == b
        False

        >>> b.append('reD') # case insensitive
        >>> a == b
        True
        
        >>> a == ['red', 'green'] # need both to be groups
        False
        
        >>> c = base.Groups()
        >>> c.append('black')
        >>> c.append('tuba')
        >>> a == c
        False
        '''
        if not isinstance(other, Groups):
            return False
        
        if len(self) != len(other):
            return False
        sls = sorted(self)
        slo = sorted(other)
        
        for x in range(len(sls)):
            if sls[x].lower() != slo[x].lower():
                return False
        return True

    def __ne__(self, other):
        '''
        In normal lists, order matters; here it does not.

        >>> a = Groups()
        >>> a.append('red')
        >>> a.append('green')
        >>> a
        ['red', 'green']

        >>> b = Groups()
        >>> b.append('green')
        >>> b.append('blue')
        >>> a != b
        True
        '''
        return not (self == other)



#------------------------------------------------------------------------------


class Music21Object(object):
    '''
    Base class for all music21 objects.

    All music21 objects have seven pieces of information:

    1.  id: identification string unique to the objects container (optional)
    2.  groups: a Groups object: which is a list of strings identifying
        internal subcollections (voices, parts, selections) to which this
        element belongs
    3.  duration: Duration object representing the length of the object
    4.  activeSite: a weakreference to the currently active Location
    5.  offset: a floating point value, generally in quarter lengths,
        specifying the position of the object in a site.
    6.  priority: int representing the position of an object among all
        objects at the same offset.
    7.  sites: a Sites object that stores all the Streams and Contexts that an
        object is in.

    Contexts, locations, and offsets are stored in a
    :class:`~music21.base.Sites` object.  Locations specify connections of this
    object to one location in a Stream subclass.  Contexts are weakrefs for
    current objects that are associated with this object (similar to locations
    but without an offset)

    Each of these may be passed in as a named keyword to any music21 object.

    Some of these may be intercepted by the subclassing object (e.g., duration
    within Note)
    '''

    classSortOrder = 20  # default classSortOrder
    # these values permit fast class comparisons for performance critical cases
    isStream = False
    isSpanner = False
    isVariant = False


    # this dictionary stores as a tuple of strings for each Class so that
    # it only needs to be made once (11 microseconds per call, can be
    # a big part of iteration; from cache just 1 microsecond)
    _classListCacheDict = {}
    _classSetCacheDict = {}
    # same with fully qualified names
    _classListFullyQualifiedCacheDict = {}


    # define order to present names in documentation; use strings
    _DOC_ORDER = [
        'classes',
        'classSet',
        'findAttributeInHierarchy',
        ]

    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
        'id': '''A unique identification string; not to be confused with the 
            default `.id()` method. However, if not set, will return the `id()` number''',
        'groups': '''An instance of a :class:`~music21.base.Group` object which describes 
            arbitrary `Groups` that this object belongs to.''',
        'isStream': '''Boolean value for quickly identifying 
            :class:`~music21.stream.Stream` objects (False by default).''',
        'isSpanner': '''Boolean value for quickly identifying
             :class:`~music21.spanner.Spanner` objects (False by default).''',
        'isVariant': '''Boolean value for quickly identifying 
            :class:`~music21.variant.Variant` objects (False by default).''',
        'classSortOrder' : '''Property which returns an number (int or otherwise)
            depending on the class of the Music21Object that
            represents a priority for an object based on its class alone --
            used as a tie for stream sorting in case two objects have the
            same offset and priority.  Lower numbers are sorted to the left
            of higher numbers.  For instance, Clef, KeySignature, TimeSignature
            all come (in that order) before Note.

            All undefined classes have classSortOrder of 20 -- same as note.Note


            >>> m21o = base.Music21Object()
            >>> m21o.classSortOrder
            20

            >>> tc = clef.TrebleClef()
            >>> tc.classSortOrder
            0

            >>> ks = key.KeySignature(3)
            >>> ks.classSortOrder
            2


            New classes can define their own default classSortOrder

            >>> class ExampleClass(base.Music21Object):
            ...     classSortOrder = 5
            ...
            >>> ec1 = ExampleClass()
            >>> ec1.classSortOrder
            5
            ''',
        'hideObjectOnPrint': '''if set to `True` will not print upon output 
            (only used in MusicXML output at this point and 
            Lilypond for notes, chords, and rests).''',
        'xPosition': '''if set, defines the display x-position from 
            the start of the container (in musicxml "tenths" by default)''',
        }

    def __init__(self, *arguments, **keywords):
        # None is stored as the internal location of an obj w/o any sites
        self._activeSite = None
        # offset when no activeSite is available
        self._naiveOffset = 0.0
        # offset when activeSite is already garbage collected/dead, as in short-lived sites
        # like .getElementsByClass
        self._activeSiteStoredOffset = None

        
        # store a derivation object to track derivations from other Streams
        # pass a reference to this object
        self._derivation = None
        
        # private duration storage; managed by property
        self._duration = None
        self._priority = 0 # default is zero

        self.hideObjectOnPrint = False
        self.xPosition = None

        if "id" in keywords:
            self.id = keywords["id"]
        else:
            self.id = id(self)

        # a duration object is not created until the .duration property is
        # accessed with _getDuration(); this is a performance optimization
        if "duration" in keywords:
            self.duration = keywords["duration"]
        if "groups" in keywords and keywords["groups"] is not None:
            self.groups = keywords["groups"]
        else:
            self.groups = Groups()
        if "sites" in keywords:
            self.sites = keywords["sites"]
        else:
            self.sites = sites.Sites()

        if "activeSite" in keywords:
            self.activeSite = keywords["activeSite"]


    def mergeAttributes(self, other):
        '''
        Merge all elementary, static attributes. Namely,
        `id` and `groups` attributes from another music21 object.
        Can be useful for copy-like operations.

        >>> m1 = base.Music21Object()
        >>> m2 = base.Music21Object()
        >>> m1.id = 'music21Object1'
        >>> m1.groups.append("group1")
        >>> m2.mergeAttributes(m1)
        >>> m2.id
        'music21Object1'
        >>> "group1" in m2.groups
        True
        '''
        if other.id != id(other):
            self.id = other.id
        self.groups = copy.deepcopy(other.groups)

    def _deepcopySubclassable(self, memo=None, ignoreAttributes=None, removeFromIgnore=None):
        '''
        Subclassable __deepcopy__ helper so that the same attributes do not need to be called
        for each Music21Object subclass.
        
        ignoreAttributes is a set of attributes not to copy via the default deepcopy style.
        More can be passed to it.
        
        removeFromIgnore can be a set of attributes to remove from ignoreAttributes of a
        superclass.
        
        TODO: move to class attributes to cache.
        '''
        defaultIgnoreSet = {'_derivation', '_activeSite', 'id', 'sites', '_duration'}
        if ignoreAttributes is None:
            ignoreAttributes = defaultIgnoreSet
        else:
            ignoreAttributes = ignoreAttributes | defaultIgnoreSet
        
        if removeFromIgnore is not None:
            ignoreAttributes = ignoreAttributes - removeFromIgnore
        
        # call class to get a new, empty instance
        new = self.__class__() # TODO: this creates an extra duration object for notes... ugghhh...
        #environLocal.printDebug(['Music21Object.__deepcopy__', self, id(self)])
        #for name in dir(self):
        if '_duration' in ignoreAttributes:
            ## this can be done much faster in most cases...
            d = self._duration
            if d is not None:
                clientStore = self._duration._client
                self._duration._client = None
                newValue = copy.deepcopy(self._duration, memo)
                self._duration._client = clientStore
                newValue.client = new
                setattr(new, '_duration', newValue)
                
        if '_derivation' in ignoreAttributes:
            # was: keep the old ancestor but need to update the client
            # 2.1 : NO, add a derivation of __deepcopy__ to the client
            newDerivation = derivation.Derivation(client=new)
            newDerivation.origin = self
            newDerivation.method = '__deepcopy__'
            setattr(new, '_derivation', newDerivation)

        if '_activeSite' in ignoreAttributes:
            # TODO: Fix this so as not to allow incorrect _activeSite (???)
            # keep a reference, not a deepcopy
            # do not use property: .activeSite; set to same weakref obj
# restore jan 18
#            setattr(new, '_activeSite', None) 
            setattr(new, '_activeSite', self._activeSite)

        if 'id' in ignoreAttributes:
            value = getattr(self, 'id')
            if value != id(self) or (common.isNum(value) and 
                                     value < defaults.minIdNumberToConsiderMemoryLocation): 
                newValue = value
                setattr(new, 'id', newValue)
        if 'sites' in ignoreAttributes:
            # we make a copy of the sites value even though it is obsolete because
            # the spanners will need to be preserved and then set to the new value
            # elsewhere.  The purgeOrphans call later will remove all but
            # spanners and variants.
            value = getattr(self, 'sites')
            # this calls __deepcopy__ in Sites
            newValue = copy.deepcopy(value, memo)
            setattr(new, 'sites', newValue)


        for name in self.__dict__:
            if name.startswith('__'):
                continue
            if name in ignoreAttributes:
                continue

            attrValue = getattr(self, name)
            # attributes that do not require special handling
            try:
                deeplyCopiedObject = copy.deepcopy(attrValue, memo)
                setattr(new, name, deeplyCopiedObject)
            except TypeError:
                if not isinstance(attrValue, Music21Object):
                    # shallow copy then...
                    try:
                        shallowlyCopiedObject = copy.copy(attrValue)
                        setattr(new, name, shallowlyCopiedObject)
                        environLocal.printDebug(
                            '__deepcopy__: Could not deepcopy ' + 
                            '{0} in {0}, not a music21Object'.format(name, self) +
                            'so making a shallow copy')
                    except TypeError:
                        # just link...
                        environLocal.printDebug('__deepcopy__: Could not copy (deep or shallow) ' +
                            '%s in %s, not a music21Object so just making a link' % (name, self))
                        setattr(new, name, attrValue)
                else: # raise error for our own problem.
                    raise Music21Exception('__deepcopy__: Cannot deepcopy Music21Object ' + 
                        '%s probably because it requires a default value in instantiation.' % name)
            
        return new

    def __deepcopy__(self, memo=None):
        '''
        Helper method to copy.py's deepcopy function.  Call it from there.

        memo=None is the default as specified in copy.py

        Problem: if an attribute is defined with an underscore (_priority) but
        is also made available through a property (e.g. priority)  using dir(self)
        results in the copy happening twice. Thus, __dict__.keys() is used.

        >>> from copy import deepcopy
        >>> n = note.Note('A')
        >>> n.offset = 1.0 #duration.Duration("quarter")
        >>> n.groups.append("flute")
        >>> n.groups
        ['flute']

        >>> idN = n.id
        >>> idN > 10000  # pointer
        True
        
        >>> b = deepcopy(n)
        >>> b.offset = 2.0 #duration.Duration("half")

        >>> n is b
        False
        >>> b.id != n.id
        True        
        >>> n.accidental = "-"
        >>> b.name
        'A'
        >>> n.offset
        1.0
        >>> b.offset
        2.0
        >>> n.groups[0] = "bassoon"
        >>> ("flute" in n.groups, "flute" in b.groups)
        (False, True)
        '''
        #environLocal.printDebug(['calling Music21Object.__deepcopy__', self])
        new = self._deepcopySubclassable(memo)
        # must do this after copying
        new.purgeOrphans()
        #environLocal.printDebug([self, 'end deepcopy', 'self._activeSite', self._activeSite])
        return new

    
    def __getstate__(self):
        state = self.__dict__.copy()
        state['_derivation'] = None
        state['_activeSite'] = None
        return state
 
    def __setstate__(self, state):
        # defining self.__dict__ upon initialization currently breaks everything
        self.__dict__ = state #pylint: disable=attribute-defined-outside-init

    def isClassOrSubclass(self, classFilterList):
        '''
        Given a class filter list (a list or tuple must be submitted),
        which may have strings or class objects, determine
        if this class is of the provided classes or a subclasses.
        
        NOTE: this is a performance critical operation
        for performance, only accept lists or tuples
        
        >>> n = note.Note()
        >>> n.isClassOrSubclass(('Note',))
        True
        >>> n.isClassOrSubclass(('GeneralNote',))
        True
        >>> n.isClassOrSubclass((note.Note,))
        True
        >>> n.isClassOrSubclass((note.Rest,))
        False
        >>> n.isClassOrSubclass((note.Note,note.Rest))
        True
        >>> n.isClassOrSubclass(('Rest','Note'))
        True
        '''
        return not self.classSet.isdisjoint(classFilterList)

    def _getClasses(self):
        try:
            return self._classListCacheDict[self.__class__]
        except KeyError:
            classList = tuple([x.__name__ for x in self.__class__.mro()])
            self._classListCacheDict[self.__class__] = classList
            return classList

    classes = property(_getClasses,
        doc='''Returns a tuple containing the names (strings, not objects) of classes that this
        object belongs to -- starting with the object's class name and going up the mro()
        for the object.  Very similar to Perl's @ISA array:


        >>> q = note.Note()
        >>> q.classes
        ('Note', 'NotRest', 'GeneralNote', 'Music21Object', 'object')

        Having quick access to these things as strings makes it easier to do comparisons:

        Example: find GClefs that are not Treble clefs (or treble 8vb, etc.):

        >>> s = stream.Stream()
        >>> s.insert(10, clef.GClef())
        >>> s.insert(20, clef.TrebleClef())
        >>> s.insert(30, clef.FrenchViolinClef())
        >>> s.insert(40, clef.Treble8vbClef())
        >>> s.insert(50, clef.BassClef())
        >>> s2 = stream.Stream()
        >>> for t in s:
        ...    if 'GClef' in t.classes and 'TrebleClef' not in t.classes:
        ...        s2.insert(t)
        >>> s2.show('text')
        {10.0} <music21.clef.GClef>
        {30.0} <music21.clef.FrenchViolinClef>
        
        `Changed 2015 Sep`: returns a tuple, not a list.        
        ''')

    def _getClassSet(self):
        try:
            return self._classSetCacheDict[self.__class__]
        except KeyError:
            classNameList = list(self.classes)
            classObjList = self.__class__.mro()
            classListFQ = [x.__module__ + '.' + x.__name__ for x in self.__class__.mro()]
            classList = classNameList + classObjList + classListFQ
            classSet = frozenset(classList)
            self._classSetCacheDict[self.__class__] = classSet
            return classSet

    classSet = property(_getClassSet, doc='''
        Returns a set (that is, unordered, but indexed) of all of the classes that
        this class belongs to, including
        string names, fullyQualified string names, and objects themselves.
        
        It's cached on a per class basis, so makes for a really fast way of checking to 
        see if something belongs
        to a particular class when you don't know if the user has given a string,
        a fully qualified string name, or an object.
        
        Did I mention it's fast?  It's a drop in substitute for the deprecated
        `.isClassOrSubClass`.  It's not as fast as x in n.classes or isinstance(n, x)
        if you know whether it's a string or class, but this is good and safe.
        
        >>> n = note.Note()
        >>> 'Note' in n.classSet
        True
        >>> 'music21.note.Note' in n.classSet
        True
        >>> note.Note in n.classSet
        True
        
        >>> 'Rest' in n.classSet
        False
        >>> note.Rest in n.classSet
        False
        
        >>> object in n.classSet
        True
        
        >>> sorted([s for s in n.classSet if isinstance(s, str)])
        ['GeneralNote', 'Music21Object', 'NotRest', 'Note', '....object', 
         'music21.base.Music21Object', 'music21.note.GeneralNote', 'music21.note.NotRest', 
         'music21.note.Note', 'object']
         
        >>> sorted([s for s in n.classSet if not isinstance(s, str)], key=lambda x: x.__name__)
        [<class 'music21.note.GeneralNote'>, 
         <class 'music21.base.Music21Object'>, 
         <class 'music21.note.NotRest'>, 
         <class 'music21.note.Note'>, 
         <... 'object'>]
        
    ''')

    #---------------------------
    # convienence.  used to be in note.Note, but belongs everywhere:
    def _getQuarterLengthFloat(self):
        return self.duration.quarterLengthFloat

    def _getQuarterLengthRational(self):
        return self.duration.quarterLength
    
    def _setQuarterLength(self, value):
        self.duration.quarterLength = value

    quarterLength = property(_getQuarterLengthRational, _setQuarterLength, doc='''
        Set or Return the Duration as represented in Quarter Length, possibly as a fraction

        note: the setter is identical to .quarterLengthFloat

        >>> n = note.Note()
        >>> n.quarterLength = 2.0
        >>> n.quarterLength
        2.0
        >>> n.quarterLength = 1.0/3
        >>> n.quarterLength
        Fraction(1, 3)
    ''')
    quarterLengthFloat = property(_getQuarterLengthFloat, _setQuarterLength,
        doc = '''Set or Return the Duration as represented in Quarter Length as a float

        >>> n = note.Note()
        >>> n.quarterLengthFloat = 2.0
        >>> n.quarterLengthFloat
        2.0
        >>> n.quarterLengthFloat = 1.0/3
        >>> n.quarterLengthFloat
        0.333...
        ''')


    def _getDerivation(self):
        '''
        Return the :class:`~music21.derivation.Derivation` object for this element.
        
        Or create one if none exists:
        
        >>> n = note.Note()
        >>> n.derivation
        <Derivation of <music21.note.Note C> from None via "None">
        >>> import copy
        >>> n2 = copy.deepcopy(n)
        >>> n2.pitch.step = 'D' # for seeing easier...
        >>> n2.derivation
        <Derivation of <music21.note.Note D> from <music21.note.Note C> via "__deepcopy__">
        >>> n2.derivation.origin is n
        True
        
        Note that (for now at least) derivation.origin is NOT a weakref:
        
        >>> del n
        >>> n2.derivation
        <Derivation of <music21.note.Note D> from <music21.note.Note C> via "__deepcopy__">
        >>> n2.derivation.origin
        <music21.note.Note C>
        '''
        if self._derivation is None:
            self._derivation = derivation.Derivation(client=self)
        return self._derivation

    def _setDerivation(self, newDerivation):
        self._derivation = newDerivation

    derivation = property(_getDerivation, _setDerivation)


    def getOffsetBySite(self, site, returnType='rational', stringReturns=False):
        '''
        If this class has been registered in a container such as a Stream,
        that container can be provided here, and the offset in that object
        can be returned.

        Note that this is different than the elementOffset() method on
        Stream in that this can never access the flat representation of a Stream.

        >>> n = note.Note('A-4')  # a Music21Objecct
        >>> n.offset = 30
        >>> n.getOffsetBySite(None)
        30.0

        >>> s1 = stream.Stream()
        >>> s1.id = 'containingStream'
        >>> s1.insert(20.0/3, n)
        >>> n.getOffsetBySite(s1)
        Fraction(20, 3)
        >>> n.getOffsetBySite(s1, returnType='float')
        6.6666...
        
        n.getOffsetBySite(None) should still return 30.0
        
        >>> n.getOffsetBySite(None)
        30.0

        If the Stream does not contain the element then a SitesException is raised:
        
        >>> s2 = stream.Stream()
        >>> s2.id = 'notContainingStream'
        >>> n.getOffsetBySite(s2)
        Traceback (most recent call last):
        SitesException: an entry for this object <music21.note.Note A-> is not 
              stored in stream <music21.stream.Stream notContainingStream>


        If the object is stored at the end of the Stream, then the highest time 
        is usually returned:
        
        >>> s3 = stream.Stream()
        >>> n3 = note.Note(type='whole')
        >>> s3.append(n3)
        >>> rb = bar.Barline()
        >>> s3.storeAtEnd(rb)  # s3.rightBarline = rb would do the same...
        >>> rb.getOffsetBySite(s3)
        4.0
        
        However, setting stringReturns to True will return 'highestTime'
        
        >>> s3._endElements
        [<music21.bar.Barline style=regular>]
        
        >>> rb.getOffsetBySite(s3, stringReturns=True)
        'highestTime'
        
        Normal numbers are still returned as a float or Fraction:
        
        >>> n3.getOffsetBySite(s3, stringReturns=True)
        0.0
        '''
        try:
            if site is not None:
                a = None
                tryOrigin = self
                originMemo = set()
                maxSearch = 100
                while a is None:
                    try:
                        a = site.elementOffset(tryOrigin, stringReturns=stringReturns)
                    except AttributeError:
                        raise SitesException(
                            "You were using %r as a site, when it is not a Stream..." % site)
                    except Music21Exception as e: # currently StreamException, but will change
                        if tryOrigin in site._endElements:
                            if stringReturns is True:
                                return 'highestTime'
                            else:
                                return site.highestTime
                        
                        tryOrigin = self.derivation.origin
                        if id(tryOrigin) in originMemo:
                            raise(e)
                        else:
                            originMemo.add(id(tryOrigin))
                        maxSearch -= 1
                        if tryOrigin is None or maxSearch < 0:
                            raise(e)
                if returnType == 'float':
                    a = float(a)
            else:
                a = self._naiveOffset
            return a
        except SitesException:
            raise SitesException(
                'an entry for this object %r is not stored in stream %r' % (self, site))

    def setOffsetBySite(self, site, value):
        '''
        Change the offset for a site.  These are equivalent:
        
            n1.setOffsetBySite(stream1, 20)
            
        and
        
            stream1.setElementOffset(n1, 20)
        
        >>> import music21
        >>> aSite = stream.Stream()
        >>> a = music21.Music21Object()
        >>> a.sites.add(aSite)
        >>> aSite.setElementOffset(a, 20)
        >>> a.setOffsetBySite(aSite, 30)
        >>> a.getOffsetBySite(aSite)
        30.0
        
        And if it isn't there? Nothing changes.
        
        >>> b = note.Note()
        >>> b.setOffsetBySite(aSite, 40)
        >>> b.offset
        0.0

        '''
        if site is not None:
            site.setElementOffset(self, value)
            if site is self.activeSite:
                self._activeSiteStoredOffset = value # update...     
        else:
            self._naiveOffset = value

    @common.deprecated("September 2015", "January 2016", "use self.sites.getAttrByName(attr)")
    def getContextAttr(self, attr):
        '''
        Given the name of an attribute, search the Sites object for
        contexts having this attribute and return
        the best match.

        DEPRECATED

        >>> import music21
        >>> class Mock(music21.Music21Object):
        ...     attr1 = 234
        >>> aObj = stream.Stream()
        >>> aObj.attr1 = 'test'
        >>> a = music21.Music21Object()
        >>> aObj.insert(0, a)
        >>> a.sites.getAttrByName('attr1')
        'test'

        >>> bObj = stream.Stream()
        >>> bObj.attr1 = 'came second'
        >>> bObj.insert(0, a)
        >>> a.sites.getAttrByName('attr1')
        'test'

        '''
        return self.sites.getAttrByName(attr)

    @common.deprecated("September 2015", "January 2016", "use self.sites.setAttrByName(attr, value)")
    def setContextAttr(self, attrName, value):
        '''
        Given the name of an attribute, search Contexts and return
        the best match.

        >>> import music21
        >>> class Mock(music21.Music21Object):
        ...     attr1 = 234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = music21.Music21Object()
        >>> a.sites.add(aObj)
        >>> a.sites.getAttrByName('attr1')
        'test'
        >>> a.sites.setAttrByName('attr1', 3000)
        >>> a.sites.getAttrByName('attr1')
        3000
        '''
        return self.sites.setAttrByName(attrName, value)

    def hasSite(self, other):
        '''
        Return True if other is a site in this Music21Object

        Matches on id(other)

        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> s.append(n)
        >>> n.hasSite(s)
        True
        >>> n.hasSite(stream.Stream())
        False
        '''
        return id(other) in self.sites.getSiteIds()


    def getSpannerSites(self, spannerClassList=None):
        '''
        Return a list of all :class:`~music21.spanner.Spanner` objects
        (or Spanner subclasses) that contain
        this element. This method provides a way for
        objects to be aware of what Spanners they
        reside in. Note that Spanners are not Streams
        but specialized Music21Objects that use a
        Stream subclass, SpannerStorage, internally to keep track
        of the elements that are spanned.

        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('D4')
        >>> sp1 = spanner.Slur(n1, n2)
        >>> n1.getSpannerSites() == [sp1]
        True

        Note that not all Spanners are in the spanner module. They
        tend to reside in modules closer to their musical function:

        >>> sp2 = dynamics.Crescendo(n2, n1)
        
        The order that Spanners are returned is usually the order they
        were created, but on fast computers there can be ties, so use
        a set comparison if you expect multiple:
        
        >>> set(n2.getSpannerSites()) == set([sp1, sp2])
        True

        Optionally a class name or list of class names can be
        specified and only Spanners of that class will be returned

        >>> sp3 = dynamics.Diminuendo(n1, n2)
        >>> n2.getSpannerSites('Diminuendo') == [sp3]
        True

        A larger class name can be used to get all subclasses:

        >>> set(n2.getSpannerSites('DynamicWedge')) == set([sp2, sp3])
        True
        >>> set(n2.getSpannerSites(['Slur','Diminuendo'])) == set([sp1, sp3])
        True


        >>> set(n2.getSpannerSites(['Slur','Diminuendo'])) == set([sp3, sp1])
        True


        Example: see which pairs of notes are in the same slur.

        >>> n3 = note.Note('E4')
        >>> sp4 = spanner.Slur(n1, n3)

        >>> for n in [n1, n2, n3]:
        ...    for nOther in [n1, n2, n3]:
        ...        if n is nOther:
        ...            continue
        ...        nSlurs = n.getSpannerSites('Slur')
        ...        nOtherSlurs = nOther.getSpannerSites('Slur')
        ...        for thisSlur in nSlurs:
        ...            if thisSlur in nOtherSlurs:
        ...               print("%s shares a slur with %s" % (n.name, nOther.name))
        C shares a slur with D
        C shares a slur with E
        D shares a slur with C
        E shares a slur with C
        
        :rtype: list(spanner.Spanner)
        '''
        found = self.sites.getSitesByClass('SpannerStorage')
        post = []
        if spannerClassList is not None:
            if not common.isIterable(spannerClassList):
                spannerClassList = [spannerClassList]

        for obj in found:
            if spannerClassList is None:
                post.append(obj.spannerParent)
            else:
                for spannerClass in spannerClassList:
                    if spannerClass in obj.spannerParent.classes:
                        post.append(obj.spannerParent)
                        break

        return post


    @common.deprecated('Summer 2015', 'Jan 2016', 'use self.sites.remove() instead and set activeSite manually.')
    def removeLocationBySite(self, site):
        '''
        DEPRECATED Jan 2016: use self.sites.remove() instead and set activeSite
        manually.

        Remove a location in the :class:`~music21.base.Sites` object.

        This is only for advanced location method and
        is not a complete or sufficient way to remove an object from a Stream.
        '''
        if not id(site) in self.sites.siteDict:
#             for s in self.sites.siteDict:
#                 # DEBUG!
#                 print s,
#                 ts = self.sites.siteDict[s]
#                 print ts.obj,
#                 print common.unwrapWeakref(ts.obj)

            raise Music21ObjectException(
                        'supplied site (%s) is not a site in this object: %s' % (site, self))
        #environLocal.printDebug(['removed location by site:', 'self', self, 'site', site])
        self.sites.remove(site)

        # if activeSite is set to that site, reassign to None
        if self._getActiveSite() == site:
            self._setActiveSite(None)

    def purgeOrphans(self, excludeStorageStreams=True):
        '''
        A Music21Object may, due to deep copying or other reasons,
        have contain a site (with an offset); yet, that site may
        no longer contain the Music21Object. These lingering sites
        are called orphans. This methods gets rid of them.

        The `excludeStorageStreams` are SpannerStorage and VariantStorage.
        '''
        #environLocal.printDebug(['purging orphans'])
        orphans = []
        # TODO: how can this be optimized to not use getSites, so as to
        # not unwrap weakrefs?
        for s in self.sites.getSites():
            # of the site does not actually have this Music21Object in
            # its elements list, it is an orphan and should be removed
            # note: this permits non-site context Streams to continue
            if s is None:
                continue
            if s.isStream and not s.hasElement(self):
                if excludeStorageStreams:
                    # only get those that are not Storage Streams
                    if ('SpannerStorage' not in s.classes
                        and 'VariantStorage' not in s.classes):
                        #environLocal.printDebug(['removing orphan:', s])
                        orphans.append(id(s))
                else: # get all
                    orphans.append(id(s))
        for i in orphans:
            self.sites.removeById(i)
            p = self._getActiveSite()  # this can be simplified.
            if p is not None and id(p) == i:
                self._setActiveSite(None)


    def purgeLocations(self, rescanIsDead=False):
        '''
        Remove references to all locations in objects that no longer exist.
        '''
        # NOTE: this method is overridden on Spanner and Variant, so not an easy fix...
        self.sites.purgeLocations(rescanIsDead=rescanIsDead)

    def getContextByClass(self, 
                          className,
                          callerFirst=None, 
                          getElementMethod='getElementAtOrBefore',
                          memo=None, 
                          serialReverseSearch=True,
                          sortByCreationTime=False):
        '''
        A very powerful method in music21 of fundamental importance: Returns
        the element matching the className that is closest to this element in
        its current hierarchy.  For instance, take this stream of changing time
        signatures:

        >>> s1 = converter.parse('tinynotation: 3/4 C4 D E 2/4 F G A B 1/4 c')
        >>> s2 = s1.makeMeasures()
        >>> s2.__class__ = stream.Part
        >>> s2.show('t')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
        {3.0} <music21.stream.Measure 2 offset=3.0>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note F>
            {1.0} <music21.note.Note G>
        {5.0} <music21.stream.Measure 3 offset=5.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
        {7.0} <music21.stream.Measure 4 offset=7.0>
            {0.0} <music21.meter.TimeSignature 1/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.bar.Barline style=final>

        Let's get the last two notes of the piece, the B and high c:

        >>> c = s2.measure(4).notes[0]
        >>> c
        <music21.note.Note C>

        >>> b = s2.measure(3).notes[-1]
        >>> b
        <music21.note.Note B>

        Now when we run `getContextByClass('TimeSignature')` on c, we get a
        time signature of 1/4.

        >>> c.getContextByClass('TimeSignature')
        <music21.meter.TimeSignature 1/4>

        Doing what we just did wouldn't be hard to do with other methods,
        though `getContextByClass` makes it easier.  But the time signature
        context for b would be much harder to get without this method, since in
        order to do it, it searches backwards within the measure, finds that
        there's nothing there.  It goes to the previous measure and searches
        that one backwards until it gets the proper TimeSignature of 2/4:

        >>> b.getContextByClass('TimeSignature')
        <music21.meter.TimeSignature 2/4>

        The method is smart enough to stop when it gets to the beginning of the
        part.  This is all you need to know for most uses.  The rest of the
        docs are for advanced uses:

        The methods searches both Sites as well as associated objects to find a
        matching class. Returns None if not match is found.

        A reference to the caller is required to find the offset of the object
        of the caller. This is needed for serialReverseSearch.

        The caller may be a Sites reference from a lower-level object.  If so,
        we can access the location of that lower-level object. However, if we
        need a flat representation, the caller needs to be the source Stream,
        not its Sites reference.

        The `callerFirst` is the first object from which this method was
        called. This is needed in order to determine the final offset from
        which to search.

        The `getElementMethod` is a string that selects which Stream method is
        used to get elements for searching. The strings 'getElementAtOrBefore'
        and 'getElementBeforeOffset' are currently accepted.

        OMIT_FROM_DOCS

        >>> s = corpus.parse('bwv66.6')
        >>> noteA = s[1][2][0]
        >>> noteA.getContextByClass('TimeSignature')
        <music21.meter.TimeSignature 4/4>
        '''
        def extractElementFromVerticality(verticality):
            if verticality is None:
                return None
            if len(verticality.startTimespans) > 0:
                return verticality.startTimespans[0].element
            elif len(verticality.overlapTimespans) > 0:
                return verticality.overlapTimespans[0].element

        def findElInTimespanTree(ts, offsetStart):
            if getElementMethod == 'getElementAtOrBefore':
                verticality = ts.getVerticalityAtOrBefore(offsetStart)
            elif getElementMethod == 'getElementBeforeOffset':
                verticality = ts.getVerticalityAt(offsetStart).previousVerticality
            if verticality is not None:
                element = extractElementFromVerticality(verticality)
                if element is not None and element.isClassOrSubclass(className):
                    # latter should not be necessary...
                    return element
            return None

        def findElInTimespanTreeNoRecurse(ts, offsetStart):
            # goes through each, but should be fast because
            # only contains containers and elements with the
            # proper classes...
            if getElementMethod == 'getElementAtOrBefore':
                offsetStart += 0.0001
            while offsetStart is not None: # redundant, but useful...
                offsetStart = ts.getOffsetBefore(offsetStart)
                if offsetStart is None:
                    return None
                startTimespans = ts.elementsStartingAt(offsetStart)
                for element in startTimespans:
                    if hasattr(element, 'source'):
                        continue
                    return element.element

        if not common.isListLike(className):
            className = (className,)

        for site, offsetStart, searchType in self.contextSites(
                                                sortByCreationTime=sortByCreationTime):
            if site.isClassOrSubclass(className):
                return site
            if searchType == 'elementsOnly' or searchType == 'elementsFirst':
                tsNotFlat = site.asTimespans(classList=className, recurse=False)
                el = findElInTimespanTreeNoRecurse(tsNotFlat, offsetStart)
                if el is not None:
                    return el
            if searchType != 'elementsOnly':
                tsFlat = site.asTimespans(classList=className, recurse=True)
                el = findElInTimespanTree(tsFlat, offsetStart)
                if el is not None:
                    return el


    #@common.deprecated("May 2014","soonest possible","not sure that it works at all...")
    def getAllContextsByClass(self, className, found=None, idFound=None,
                             memo=None):
        '''
        Search both Sites as well as associated
        objects to find all matching classes.
        Returns [] if not match is found.

        DEPRECATED possibly May 2014: Not sure if it works well...
        '''
        if memo is None:
            memo = {} # intialize
        if found is None:
            found = []
        if idFound is None:
            idFound = []

        #post = None
        # if this obj is a Stream
        if self.isStream:
        #if hasattr(self, "elements"):
            semiFlat = self.semiFlat
            # this memos updates to not exclude redundancies
            # TODO: check if getContextByClass can be improved
            # by adding these to memo
            memo[id(self)] = self
            memo[id(semiFlat)] = semiFlat

            for e in semiFlat.getElementsByClass([className]):
                # cannot be sure if this element is already found, as we may be
                # looking at a flattened version of container
                #if e not in found:
                if id(e) not in idFound:
                    found.append(e)
                    idFound.append(id(e))

        # next, search all defined contexts
        self.sites.getAllByClass(className, found=found,
                                         idFound=idFound, memo=memo)
        return found

    #--------------------------------------------------------------------------

    def _adjacentObject(self, 
                        site, 
                        classFilterList=None, 
                        forward=True,
                        beginNearest=True):
        '''
        Core method for finding adjacent objects given a single site.

        The `site` argument is a Stream that contains this
        element. The index of this element if sound in this site,
        and either the next or previous element, if found, is returned.

        If `forward` is True index values are
        incremented; if False, index values are decremented.

        If `beginNearest` is True, index values are searched based
        on those closest to the caller; if False, the search is
        done in reverse, from the most remote index toward the caller.
        This may be useful as an optimization when looking for elements 
        that are far from the caller.

        The `classFilterList` may specify one or more classes as targets.
        '''
        siteLength = len(site)
        # get another list to avoid function calls
        siteElements = site.elements
        # special optimization for class selection when a single str class
        # is given
        if (classFilterList is not None and len(classFilterList) == 1 and
            isinstance(classFilterList[0], str)):
            if not site.hasElementOfClass(classFilterList[0]):
                return None
        # go to right, start at nearest
        if forward and beginNearest:
            currentIndex = site.index(self) + 1 # start with next
            while (currentIndex < siteLength):
                nextObj = siteElements[currentIndex]
                if classFilterList is not None:
                    if nextObj.isClassOrSubclass(classFilterList):
                        return nextObj
                else:
                    return nextObj
                currentIndex += 1
        # go to right, start at rightmost
        elif forward and not beginNearest:
            try:
                lastIndex = site.index(self) + 1 # end with next
            except exceptions21.StreamException: 
                return None # see note below
            currentIndex = siteLength
            while (currentIndex >= lastIndex):
                nextObj = siteElements[currentIndex]
                if classFilterList is not None:
                    if nextObj.isClassOrSubclass(classFilterList):
                        return nextObj
                else:
                    return nextObj
                currentIndex -= 1
        # go to left, start at nearest
        elif not forward and beginNearest:
            try:
                currentIndex = site.index(self) - 1 # start with next
            except exceptions21.StreamException: 
                return None 
                # this may happen because a Stream may be in an object's .sites
                # after a deepcopy but which does not actually have the object in it.
                # TODO: Remove this check after sites is completely cleaned up so does not happen. 
            while (currentIndex >= 0):
                nextObj = siteElements[currentIndex]
                if classFilterList is not None:
                    if nextObj.isClassOrSubclass(classFilterList):
                        return nextObj
                else:
                    return nextObj
                currentIndex -= 1
        # go to left, start at leftmost
        elif not forward and not beginNearest:
            try:
                lastIndex = site.index(self) - 1 # start with next
            except exceptions21.StreamException:
                return None # see note above
            currentIndex = 0
            while (currentIndex <= lastIndex):
                nextObj = siteElements[currentIndex]
                if classFilterList is not None:
                    if nextObj.isClassOrSubclass(classFilterList):
                        return nextObj
                else:
                    return nextObj
                currentIndex += 1
        else:
            raise Music21ObjectException('bad organization of forward and beginNearest parameters')
        # if nothing found, return None
        return None

    def _adjacencySearch(self, 
                         classFilterList=None, 
                         forward=True,
                         beginNearest=True, 
                         flattenLocalSites=False):
        '''
        Get the next (if forward is True) or previous (if forward is False) element 
        of this element, according to various definitions of forward and backwards.

        It is pretty simple to define this for a simple object in one stream.  It's much
        harder if a lot of other streams/sites have interfered.

        If this element is in multiple Streams, the first next element found in any
        site will be returned. If not found no next element is found in any site, the flat
        representation of all sites of each immediate site are searched.

        If `beginNearest` is True, sites will be searched from the element nearest to the
        caller and then outward.
        '''
        if classFilterList is not None:
            if not common.isListLike(classFilterList):
                classFilterList = [classFilterList]
        selfSites = self.sites.getSites(excludeNone=True)
        match = None

        # store ids of of first sites; might need to take flattened version
        firstSites = []
        for s in selfSites:
            firstSites.append(id(s))
        # this might use get(sortByCreationTime)
        #environLocal.printDebug(['sites:', selfSites])
        #siteSites = []

        # first, look in sites that are do not req flat presentation
        # these do not need to be flattened b/c we know the self is in these
        # streams
        memo = {}
        while len(selfSites) > 0:
            #environLocal.printDebug(['looking at siteSites:', s])
            # check for duplicated sites; may be possible
            s = selfSites.pop(0) # take the first off of sites
            try:
                unused = memo[id(s)] 
                continue # if in dict, do not continue
            except KeyError: # if not in dict
                memo[id(s)] = None # add to dict, value does not matter

            if id(s) in firstSites:
                if flattenLocalSites is True:
                    if s.isFlat:
                        target = s
                    else:
                        target = s.semiFlat
                else: # do not flatten first sites
                    target = s
                    # add semi flat to sites, as we have not searched it yet
                    selfSites.append(s.semiFlat)
                firstSites.pop(firstSites.index(id(s))) # remove for efficiency
            # if flat, do not get semiFlat
            # note that semiFlat streams are marked as isFlat=True
            elif s.isFlat:
                target = s
            else: # normal site
                target = s.semiFlat
            # use semiflat of site
            match = self._adjacentObject(target,
                                         classFilterList=classFilterList, 
                                         forward=forward,
                                         beginNearest=beginNearest)
            if match is not None and match is not self:
                return match
            # append new sites to end of queue
            # these are the sites of s, not target
            selfSites += s.sites.getSites(excludeNone=True)
        # if cannot be found, return None
        return None

    def next(self, 
             classFilterList=None, 
             flattenLocalSites=False,
             beginNearest=True):
        '''
        Get the next element found in the activeSite (or other Sites)
        of this Music21Object.

        The `classFilterList` can be used to specify one or more classes to match.

        The `flattenLocalSites` parameter determines if the sites of this element 
        (e.g., a Measure's Part) are flattened on first search. 
        When True, elements contained in adjacent containers may be selected first.


        >>> s = corpus.parse('bwv66.6')
        >>> m3 = s.parts[0].measure(3) 
        >>> m3.next() is s.parts[0].measure(4)
        True
        
        Note that calling next() repeatedly gives...the same object.  You'll want to
        call next on that object...
        
        >>> m3.next() is s.parts[0].measure(4)
        True
        >>> m3.next() is s.parts[0].measure(4)
        True

        So do this instead:
        
        >>> o = m3
        >>> for i in range(4):
        ...     print(o)
        ...     o = o.next()
        <music21.stream.Measure 3 offset=9.0>
        <music21.stream.Measure 4 offset=13.0>
        <music21.stream.Measure 5 offset=17.0>
        <music21.stream.Measure 6 offset=21.0>        





        We can find the next element given a certain class with the `classFilterList`:
        
        >>> n = m3.next('Note')
        >>> n
        <music21.note.Note A>
        >>> n.measureNumber
        3
        >>> n is m3.notes[0]
        True


        ..note::
        
            There may be some unusual cases of using obj.next() in Python2 if obj
            uses itself as an Iterator, because Py2 assumes that each iterable has
            a .next() function.  In Python3 there will be no problem since the
            `next()` function is renamed to `__next__()`.



        OMIT_FROM_DOCS
        
        Add this back when it's explained what the difference from the previous is.
        
        >>> m3.next('Note', flattenLocalSites=True) == s.parts[0].measure(3).notes[0]
        True
        >>> n2 = m3.next('Note', flattenLocalSites=True)
        >>> n2
        <music21.note.Note A>
        >>> n2 is n
        True
        


        THIS IS OMITTED BECAUSE IT SOMETIMES GIVES SEMIFLATs etc.

        Notice though that when we get to the end of the set of measures, something
        interesting happens (maybe it shouldn't? don't count on this...): we descend
        into the last measure and give its elements instead.
        
        We'll leave o where it is (m7 now) to demonstrate what happens, and also
        print the its Part for more information...
        
        #>>> while o is not None:
        #...     print(o, o.getContextByClass('Part'))
        #...     o = o.next()
        <music21.stream.Measure 7 offset=25.0> <music21.stream.Part Soprano>
        <music21.stream.Measure 8 offset=29.0> <music21.stream.Part Soprano>
        <music21.stream.Measure 9 offset=33.0> <music21.stream.Part Soprano>
        <music21.note.Note F#> <music21.stream.Part Soprano>
        <music21.note.Note F#> <music21.stream.Part Soprano>
        <music21.note.Note E#> <music21.stream.Part Soprano>
        <music21.note.Note F#> <music21.stream.Part Soprano>
        <music21.bar.Barline style=final> <music21.stream.Part Soprano>
        <music21.bar.Barline style=final> <music21.stream.Part Alto>
        <music21.bar.Barline style=final> <music21.stream.Part Tenor>
        <music21.bar.Barline style=final> <music21.stream.Part Bass>       
        
        So we get through all the measures in Soprano, then with nothing else to do,
        it goes into the measure and gets all the notes in the measure and finally
        the final barline.  Then, having nothing else to do, it backtracks out of the
        Part to the Score object and finds the object that is at the same offset in
        the next object, which is the final barline of the Alto part, and so on.
        
        Not particularly useful here for `next()`, but it'll be very useful for `prev()`.
        
        '''
        return self._adjacencySearch(classFilterList=classFilterList,
                                     forward=True, 
                                     beginNearest=beginNearest, 
                                     flattenLocalSites=flattenLocalSites)

    def previous(self, 
                 classFilterList=None, 
                 flattenLocalSites=False,
                 beginNearest=True):
        '''
        Get the previous element found in the activeSite or other .sites of this
        Music21Object.

        The `classFilterList` can be used to specify one or more classes to match.

        The `flattenLocalSites` parameter determines if the sites of this element 
        (e.g., a Measure's Part) are flattened on first search. When True, elements 
        contained in adjacent containers may be selected first.

        >>> s = corpus.parse('bwv66.6')
        >>> m2 = s.parts[0].measure(2)
        >>> m3 = s.parts[0].measure(3)
        >>> m3.previous() is m2
        True
        >>> m3.previous('Note', flattenLocalSites=True) is m2.notes[-1]
        True
        
        
        TODO:  Try:  l = corpus.parse('luca/gloria'); 
        for el in l.recurse: print(el, el.previous('Note'))
        SLOWEST THING EVER! why????
        '''
        return self._adjacencySearch(classFilterList=classFilterList,
                                     forward=False, 
                                     beginNearest=beginNearest, 
                                     flattenLocalSites=flattenLocalSites)

    #--------------------------------------------------------------------------
    # properties

    def _getActiveSite(self):
        # can be None
        if sites.WEAKREF_ACTIVE:
            if self._activeSite is None: #leave None
                return self._activeSite
            else: # even if current activeSite is not a weakref, this will work
                #environLocal.printDebug(['_getActiveSite() called:', 
                #                          'self._activeSite', self._activeSite])
                return common.unwrapWeakref(self._activeSite)
        else:
            return self._activeSite

    def _setActiveSite(self, site):
        #environLocal.printDebug(['_setActiveSite() called:', 'self', self, 'site', site])

        # NOTE: this is a performance intensive call
        if site is not None:
            try:
                storedOffset = site.elementOffset(self)
            except SitesException:
                raise SitesException("v2.1. -- you may not assign an activesite for " + 
                                     "an object {} not in the Stream {}".format(self, site))

            self._activeSiteStoredOffset = storedOffset
            #siteId = id(site)
            #if not self.sites.hasSiteId(siteId): # This should raise a warning, should not happen
            #    #environLocal.warn("Adding a siteDict entry for a " +
            #    #                        "site that should already be there!")
            #    self.sites.add(site, idKey=siteId)
        else:
            self._activeSiteStoredOffset = None

        if sites.WEAKREF_ACTIVE:
            if site is None: # leave None alone
                self._activeSite = None
            else:
                self._activeSite = common.wrapWeakref(site)
        else:
            self._activeSite = site

    activeSite = property(_getActiveSite, _setActiveSite,
        doc='''
        A reference to the most-recent object used to
        contain this object. In most cases, this will be a
        Stream or Stream sub-class. In most cases, an object's
        activeSite attribute is automatically set when an the
        object is attached to a Stream.


        >>> n = note.Note("C#4")
        >>> p = stream.Part()
        >>> p.insert(20.0, n)
        >>> n.activeSite is p
        True
        >>> n.offset
        20.0

        >>> m = stream.Measure()
        >>> m.insert(10.0, n)
        >>> n.activeSite is m
        True
        >>> n.offset
        10.0
        >>> n.activeSite = p
        >>> n.offset
        20.0
        ''')

    def _getOffsetFloatOrRational(self, returnType):
        '''Get the offset for the activeSite.

        >>> n = note.Note()
        >>> m = stream.Measure()
        >>> m.id = 'm1'
        >>> m.insert(3.0, n)
        >>> n.activeSite is m
        True
        >>> n.offset
        3.0
        
        Still works...

        >>> n.offset
        3.0

        There is a branch that does slow searches.
        See test/testSerialization to have it active.
        '''
        #there is a problem if a new activeSite is being set and no offsets have
        # been provided for that activeSite; when self.offset is called,
        # the first case here would match
        #environLocal.printDebug(['Music21Object._getOffset', 'self.id', 
        #                           self.id, 'id(self)', id(self), self.__class__])
        activeSiteWeakRef = self._activeSite
        if activeSiteWeakRef is not None:
            activeSite = self.activeSite
            if activeSite is None:
                # it has died since last visit, as is the case with short-lived streams like 
                # .getElementsByClass, so we will return the most recent position
                return self._activeSiteStoredOffset
            
            try:
                o = activeSite.elementOffset(self)
            except SitesException:
                environLocal.printDebug(
                    'Not in Stream: changing activeSite to None and returning _naiveOffset')
                self.activeSite = None                
                o = self._naiveOffset
        else:
            o = self._naiveOffset
        
        if returnType != 'float':
            return o
        else:
            return float(o)

    def _setOffset(self, value):
        '''
        Set the offset for the activeSite.
        '''
        # assume that most times this is a number; in that case, the fastest
        # thing to do is simply try to set the offset w/ float(value)
        try:
            offset = opFrac(value)
        except TypeError:
            pass

        if hasattr(value, "quarterLength"):
            # probably a Duration object, but could be something else -- in any case, we'll take it.
            offset = value.quarterLength

        if self.activeSite is not None:
            self.activeSite.setElementOffset(self, offset)
        else:
            self._naiveOffset = offset

    def _getOffset(self):
        return self._getOffsetFloatOrRational('rational')

    offset = property(_getOffset, _setOffset,
        doc = '''
        The offset property sets or returns the position of this object
        as a float or fractions.Fraction value
        (generally in `quarterLengths`), depending on what is representable. 
        
        Offsets are measured from the start of the object's `activeSite`,
        that is, the most recently referenced `Stream` or `Stream` subclass such
        as `Part`, `Measure`, or `Voice`.  It is a simpler
        way of calling `o.getOffsetBySite(o.activeSite, returnType='rational')`.

        If we put a `Note` into a `Stream`, we will see the activeSite changes.

        >>> import fractions
        >>> n1 = note.Note("D#3")
        >>> n1.activeSite is None
        True

        >>> m1 = stream.Measure()
        >>> m1.number = 4
        >>> m1.insert(10.0, n1)
        >>> n1.offset
        10.0
        >>> n1.activeSite
        <music21.stream.Measure 4 offset=0.0>

        >>> n1.activeSite is m1
        True

        The most recently referenced `Stream` becomes an object's `activeSite` and
        thus the place where `.offset` looks to find its number.

        >>> m2 = stream.Measure()
        >>> m2.insert(3.0/5, n1)
        >>> m2.number = 5
        >>> n1.offset
        Fraction(3, 5)
        >>> n1.activeSite is m2
        True

        Notice though that `.offset` depends on the `.activeSite` which is the most
        recently accessed/referenced Stream.

        Here we will iterate over the `elements` in `m1` and we
        will see that the `.offset` of `n1` now is its offset in
        `m1` even though we haven't done anything directly to `n1`.
        Simply iterating over a site is enough to change the `.activeSite`
        of its elements:

        >>> for element in m1:
        ...     pass
        >>> n1.offset
        10.0


        The property can also set the offset for the object if no
        container has been set:


        >>> n1 = note.Note()
        >>> n1.id = 'hi'
        >>> n1.offset = 20/3.
        >>> n1.offset
        Fraction(20, 3)
        >>> float(n1.offset)
        6.666...


        >>> s1 = stream.Stream()
        >>> s1.append(n1)
        >>> n1.offset
        0.0
        >>> s2 = stream.Stream()
        >>> s2.insert(30.5, n1)
        >>> n1.offset
        30.5

        After calling `getElementById` on `s1`, the
        returned element's `offset` will be its offset in `s1`.

        >>> n2 = s1.getElementById('hi')
        >>> n2 is n1
        True
        >>> n2.offset
        0.0

        Iterating over the elements in a Stream will
        make its `offset` be the offset in iterated
        Stream.

        >>> for thisElement in s2:
        ...     thisElement.offset
        30.5

        When in doubt, use `.getOffsetBySite(streamObj)`
        which is safer.
        ''')
    
    def _getOffsetRational(self):
        return self._getOffsetFloatOrRational('rational')
    
    @common.deprecated("January 2015", "January 2016", "Use float(x.offset)")
    def _getOffsetFloat(self):
        return self._getOffsetFloatOrRational('float')

    offsetFloat = property(_getOffsetFloat, _setOffset, 
                           doc='''old style: always returns a float''')
    offsetRational = property(_getOffsetRational, _setOffset, doc='''synonym for .offset''')

    def sortTuple(self, useSite=False):
        '''
        Returns a collections.namedtuple called SortTuple(atEnd, offset, priority, classSortOrder,
        isNotGrace, insertIndex)
        which contains the six elements necessary to determine the sort order of any set of
        objects in a Stream.

        1) atEnd = {0, 1}; Elements specified to always stay at 
        the end of a stream (``stream.storeAtEnd``)
        sort after normal elements.

        2) offset = float; Offset (with respect to the active site) is the next and most
        important parameter in determining the order of elements in a stream (the note on beat 1
        has offset 0.0, while the note on beat 2 might have offset 1.0).

        3) priority = int; Priority is a
        user-specified property (default 0) that can set the order of 
        elements which have the same
        offset (for instance, two Parts both at offset 0.0).

        4) classSortOrder = int or float; ClassSortOrder
        is the third level of comparison that gives an ordering to elements with different classes,
        ensuring, for instance that Clefs (classSortOrder = 0) sort before Notes 
        (classSortOrder = 20).

        5) isNotGrace = {0, 1}; 0 = grace, 1 = normal. Grace notes sort before normal notes

        6) The last tie breaker is the creation time (insertIndex) of the site object
        represented by the activeSite.

        >>> n = note.Note()
        >>> n.offset = 4.0
        >>> n.priority = -3
        >>> n.sortTuple()
        SortTuple(atEnd=0, offset=4.0, priority=-3, classSortOrder=20, 
                    isNotGrace=1, insertIndex=0)
        >>> st = n.sortTuple()

        Check that all these values are the same as above...

        >>> st.offset == n.offset
        True
        >>> st.priority == n.priority
        True

        An object's classSortOrder comes from the Class object itself:

        >>> st.classSortOrder == note.Note.classSortOrder
        True

        Inserting the note into the Stream will set the insertIndex.  Most implementations of
        music21 will use a global counter rather than an actual timer.  Note that this is a
        last resort, but useful for things such as mutiple Parts inserted in order.  It changes
        with each run, so we can't display it here...

        >>> s = stream.Stream()
        >>> s.insert(n)
        >>> n.sortTuple()
        SortTuple(atEnd=0, offset=4.0, priority=-3, classSortOrder=20,
                     isNotGrace=1, insertIndex=...)
        >>> nInsertIndex = n.sortTuple().insertIndex

        If we create another nearly identical note, the insertIndex will be different:

        >>> n2 = note.Note()
        >>> n2.offset = 4.0
        >>> n2.priority = -3
        >>> s.insert(n2)
        >>> n2InsertIndex = n2.sortTuple().insertIndex
        >>> n2InsertIndex > nInsertIndex
        True
        
        >>> rb = bar.Barline()
        >>> s.storeAtEnd(rb)
        >>> rb.sortTuple()
        SortTuple(atEnd=1, offset=0.0, priority=0, classSortOrder=-5, 
                    isNotGrace=1, insertIndex=...)        
        '''
        if useSite is False: # False or a Site; since None is a valid site, default is False
            useSite = self.activeSite

        if useSite is None:                
            foundOffset = self.offset
        else:
            try:
                foundOffset = useSite.elementOffset(self, stringReturns=True)
            except SitesException:
                #environLocal.warn(r)  
                    # activeSite may have vanished! or does not have the element
                foundOffset = self._naiveOffset
                
        if foundOffset == 'highestTime':
            offset = 0.0
            atEnd = 1
        else:
            offset = foundOffset
            atEnd = 0

        if self.isGrace:
            isNotGrace = 0
        else:
            isNotGrace = 1

        if (useSite is not False and
                self.sites.hasSiteId(id(useSite))):
            insertIndex = self.sites.siteDict[id(useSite)].globalSiteIndex
        elif self.activeSite is not None:
            insertIndex = self.sites.siteDict[id(self.activeSite)].globalSiteIndex
        else:
            insertIndex = 0

        return _SortTuple(atEnd, offset, self.priority, 
                          self.classSortOrder, isNotGrace, insertIndex)

    def contextSites(self, callerFirst=None, memo=None, 
                     offsetAppend=0.0, sortByCreationTime=False, priorityTarget=None):
        '''
        A generator that returns a list of tuples of sites to search for a context...
        
        Each tuple contains a Stream object, the offset of this element in that Stream, and
        the method of searching that should be applied to search for a context.  
        These methods are:

            * 'flatten' -- flatten the stream and then look from this offset backwards.
            
            * 'elementsOnly' -- only search the stream's personal 
               elements from this offset backwards
            
            * 'elementsFirst' -- search this stream backwards, 
               and then flatten and search backwards
            
        >>> c = corpus.parse('bwv66.6')
        >>> c.id = 'bach'
        >>> n = c[2][4][2]
        >>> n
        <music21.note.Note G#>
        
        >>> for y in n.contextSites():
        ...      print(y)
        (<music21.stream.Measure 3 offset=9.0>, 0.5, 'elementsFirst')
        (<music21.stream.Part Alto>, 9.5, 'flatten')
        (<music21.stream.Score bach>, 9.5, 'elementsOnly')
        >>> m = c[2][4]
        >>> m
        <music21.stream.Measure 3 offset=9.0>
        >>> for y in m.contextSites():
        ...      print(y)
        (<music21.stream.Measure 3 offset=9.0>, 0.0, 'elementsFirst')
        (<music21.stream.Part Alto>, 9.0, 'flatten')
        (<music21.stream.Score bach>, 9.0, 'elementsOnly')

        >>> import copy
        >>> m2 = copy.deepcopy(m)
        >>> m2.number = 3333
        >>> for y in m2.contextSites():
        ...      print(y)
        (<music21.stream.Measure 3333 offset=0.0>, 0.0, 'elementsFirst')
        (<music21.stream.Part Alto>, 9.0, 'flatten')
        (<music21.stream.Score bach>, 9.0, 'elementsOnly')

        >>> tempPartStream = c.parts
        >>> tempPartStream.id = 'partStream' # for identificationBelow
        >>> m3 = tempPartStream[1].measure(3)
        >>> for y in m3.contextSites():
        ...      print(y)
        (<music21.stream.Measure 3 offset=9.0>, 0.0, 'elementsFirst')
        (<music21.stream.Part Alto>, 9.0, 'flatten')
        (<music21.stream.Score partStream>, 9.0, 'elementsOnly')
        (<music21.stream.Score bach>, 9.0, 'elementsOnly')



        Sorting order:

        >>> p1 = stream.Part()
        >>> p1.id = 'p1'
        >>> m1 = stream.Measure()
        >>> m1.number = 1
        >>> n = note.Note()
        >>> m1.append(n)
        >>> p1.append(m1)
        >>> for y in n.contextSites():
        ...     print(y[0])
        <music21.stream.Measure 1 offset=0.0>
        <music21.stream.Part p1>

        >>> p2 = stream.Part()
        >>> p2.id = 'p2'
        >>> m2 = stream.Measure()
        >>> m2.number = 2
        >>> m2.append(n)
        >>> p2.append(m2)


        The keys could have appeared in any order, but by default
        we set set priorityTarget to activeSite.  So this is the same as omitting.

        >>> for y in n.contextSites(priorityTarget=n.activeSite):
        ...     print(y[0])
        <music21.stream.Measure 2 offset=0.0>
        <music21.stream.Part p2>
        <music21.stream.Measure 1 offset=0.0>
        <music21.stream.Part p1>


        Or sort by creationTime...


        >>> for y in n.contextSites(sortByCreationTime = True):
        ...     print(y[0])
        <music21.stream.Measure 2 offset=0.0>
        <music21.stream.Part p2>
        <music21.stream.Measure 1 offset=0.0>
        <music21.stream.Part p1>

        oldest first...

        >>> for y in n.contextSites(sortByCreationTime='reverse'):
        ...     print(y[0])
        <music21.stream.Measure 1 offset=0.0>
        <music21.stream.Part p1>
        <music21.stream.Measure 2 offset=0.0>
        <music21.stream.Part p2>
        '''
        if memo is None:
            memo = []
        if callerFirst is None:
            callerFirst = self
            if self.isStream:
                recursionType = self.recursionType
                environLocal.printDebug("Caller first is {} with offsetAppend {}".format(
                                                                callerFirst, offsetAppend))
                yield(self, 0.0, recursionType)

        if priorityTarget is None and sortByCreationTime is False:
            priorityTarget = self.activeSite
        else:
            environLocal.printDebug('sortByCreationTime {}'.format(sortByCreationTime))
            

        allSites = self.sites.get(priorityTarget=priorityTarget,
                                      sortByCreationTime=sortByCreationTime,
                                      excludeNone=True)
        topLevel = self
        for siteObj in allSites:
            if 'SpannerStorage' in siteObj.classes:
                continue
            try:
                # do not change to siteObj.elementOffset(self)...
                offsetInStream = self.getOffsetBySite(siteObj) + offsetAppend
            except SitesException:
                continue # not a valid site any more.  Could be caught in derivationChain
            
            recursionType = siteObj.recursionType
            yield (siteObj, offsetInStream, recursionType)
            environLocal.printDebug("looking in contextSites for {} with offsetInStream {}".format(
                                                                siteObj, offsetInStream))
            for x in siteObj.contextSites(callerFirst=callerFirst,
                                              memo=memo,
                                              offsetAppend=offsetInStream,
                                              sortByCreationTime=sortByCreationTime,
                                              priorityTarget=None): 
                                # get activeSite unless sortByCreationTime
                topLevel = x[0] # only look at the derivation chain for the topmost level
                if x[0] not in memo:                    
                    environLocal.printDebug("Yielding {} from contextSites".format(x))
                    yield x
                    memo.append(x[0])

        for derivedObject in topLevel.derivation.chain():
            environLocal.printDebug("looking now in derivedObject, {} with offsetAppend {}".format(
                                                        derivedObject, offsetAppend))
            for z in derivedObject.contextSites(callerFirst=None,
                                          memo=memo,
                                          offsetAppend=0.0,
                                          sortByCreationTime=sortByCreationTime,
                                          priorityTarget=None): 
                                        # get activeSite unless sortByCreationTime
                if z[0] not in memo:
                    environLocal.printDebug("Yielding {} from derivedObject contextSites".format(z))
                    zz = (z[0], z[1] + offsetAppend, z[2])
                    yield zz
                    memo.append(z[0])

        environLocal.printDebug("--returning from derivedObject search")    
    #------------------------------------------------------------------
    def _getDuration(self):
        '''
        Gets the DurationObject of the object or None
        '''
        # lazy duration creation
        if self._duration is None:
            self._duration = duration.Duration(0)
        return self._duration

    def _setDuration(self, durationObj):
        '''
        Set the duration as a quarterNote length
        '''
        replacingDuration = False if self._duration is None else True
            
        try:
            ql = durationObj.quarterLength
            self._duration = durationObj
            durationObj.client = self
            if replacingDuration:
                self.durationChanged(ql)
                
        except AttributeError:
            # need to permit Duration object assignment here
            raise Exception('this must be a Duration object, not %s' % durationObj)

    duration = property(_getDuration, _setDuration,
        doc = '''
        Get and set the duration of this object as a Duration object.
        ''')

    def durationChanged(self, newQuarterLength):
        '''
        trigger called whenever the duration has changed.
        
        subclass this to do very interesting things.
        '''
        for s in self.sites.get():
            if hasattr(s, 'elementsChanged'):
                s.elementsChanged(updateIsFlat=False, keepIndex=True)

    def _getIsGrace(self):
        return self.duration.isGrace

    isGrace = property(_getIsGrace, doc='''
        Return True or False if this music21 object has a GraceDuration.

        >>> n = note.Note()
        >>> n.isGrace
        False
        >>> ng = n.getGrace()
        >>> ng.isGrace
        True
        ''')

    def _getPriority(self):
        return self._priority

    def _setPriority(self, value):
        '''
        value is an int.
        '''
        if not isinstance(value, int):
            raise ElementException('priority values must be integers.')
        if self._priority != value:
            self._priority = value
            # TODO: set priority in each site?
            #for s in self.sites.getSites(excludeNone=True):
            #    pass

    priority = property(_getPriority, _setPriority,
        doc = '''
        Get and set the priority integer value.

        Priority specifies the order of processing from left (lowest number)
        to right (highest number) of objects at the same offset.  For
        instance, if you want a key change and a clef change to happen at
        the same time but the key change to appear first, then set:
        keySigElement.priority = 1; clefElement.priority = 2 this might be
        a slightly counterintuitive numbering of priority, but it does
        mean, for instance, if you had two elements at the same offset,
        an allegro tempo change and an andante tempo change, then the
        tempo change with the higher priority number would apply to the
        following notes (by being processed second).

        Default priority is 0; thus negative priorities are encouraged
        to have Elements that appear before non-priority set elements.

        In case of tie, there are defined class sort orders defined in
        `music21.base.classSortOrder`.  For instance, a key signature
        change appears before a time signature change before a
        note at the same offset.  This produces the familiar order of
        materials at the start of a musical score.

        >>> import music21
        >>> a = music21.Music21Object()
        >>> a.priority = 3
        >>> a.priority = 'high'
        Traceback (most recent call last):
        ElementException: priority values must be integers.
        ''')


    #--------------------------------------------------------------------------
    # display and writing

    def write(self, fmt=None, fp=None, **keywords): #pragma: no cover
        '''
        Write out a file of music notation (or an image, etc.) in a given format.  If
        fp is specified as a file path then the file will be placed there.  If it is not
        given then a temporary file will be created.

        If fmt is not given then the default of your Environment's 'writeFormat' will
        be used.  For most people that is musicxml.

        Returns the full path to the file.
        '''
        if fmt is None: # get setting in environment
            fmt = environLocal['writeFormat']
        elif fmt.startswith('.'):
            fmt = fmt[1:]

        regularizedConverterFormat, unused_ext = common.findFormat(fmt)
        if regularizedConverterFormat is None:
            raise Music21ObjectException('cannot support showing in this format yet: %s' % fmt)

        formatSubs = fmt.split('.')
        fmt = formatSubs[0]
        subformats = formatSubs[1:]

        scClass = common.findSubConverterForFormat(regularizedConverterFormat)
        formatWriter = scClass()
        return formatWriter.write(self, regularizedConverterFormat, fp, subformats, **keywords)


    def _reprText(self, **keywords):
        '''
        Return a text representation possible with line
        breaks. This methods can be overridden by subclasses
        to provide alternative text representations.
        '''
        return self.__repr__()

    def _reprTextLine(self):
        '''
        Return a text representation without line breaks. This
        methods can be overridden by subclasses to provide
        alternative text representations.
        '''
        return self.__repr__()

    def show(self, fmt=None, app=None, **keywords): #pragma: no cover
        '''
        Displays an object in a format provided by the
        fmt argument or, if not provided, the format set in the user's Environment

        Valid formats include (but are not limited to)::
            musicxml
            text
            midi
            lily (or lilypond)
            lily.png
            lily.pdf
            lily.svg
            braille
            vexflow
            musicxml.png

        N.B. score.write('lily') returns a bare lilypond file,
        score.show('lily') runs it through lilypond and displays it as a png.
        '''
        # note that all formats here must be defined in
        # common.VALID_SHOW_FORMATS
        if fmt is None: # get setting in environment
            if common.runningUnderIPython():
                try:
                    # TODO: when everyone has updated, then remove these lines... 
                    #       do around January 2016
                    if 'vexflow' in environLocal['ipythonShowFormat']:
                        environLocal['ipythonShowFormat'] = 'ipython.musicxml.png'
                        environLocal.write()
                    # end delete
                    fmt = environLocal['ipythonShowFormat']
                except environment.EnvironmentException:
                    fmt = 'ipython.musicxml.png'
            else:
                fmt = environLocal['showFormat']
        elif fmt.startswith('.'):
            fmt = fmt[1:]
        regularizedConverterFormat, unused_ext = common.findFormat(fmt)
        if regularizedConverterFormat is None:
            raise Music21ObjectException('cannot support showing in this format yet: %s' % fmt)

        formatSubs = fmt.split('.')
        fmt = formatSubs[0]
        subformats = formatSubs[1:]

        scClass = common.findSubConverterForFormat(regularizedConverterFormat)
        formatWriter = scClass()
        return formatWriter.show(self, 
                                 regularizedConverterFormat, 
                                 app=app, 
                                 subformats=subformats, 
                                 **keywords)

    #--------------------------------------------------------------------------
    # duration manipulation, processing, and splitting

    def _getContainerHierarchy(self):
        post = []
        focus = self
        endMe = 200
        while endMe > 0:
            endMe = endMe - 1 # do not go forever
            # collect activeSite unless activeSite is None;
            # if so, try to get rootDerivation
            candidate = focus.activeSite
            #environLocal.printDebug(['_getContainerHierarchy(): activeSite found:', candidate])
            if candidate is None: # nothing more to derive
                # if this is a Stream, we might find a root derivation
                if hasattr(focus, 'derivation'):
                    #environLocal.printDebug(['_getContainerHierarchy(): 
                    # found rootDerivation:', focus.rootDerivation])
                    alt = focus.derivation.rootDerivation
                    if alt is None:
                        return post
                    else:
                        candidate = alt
                else:
                    return post
            post.append(candidate)
            focus = candidate
        return post

    containerHierarchy = property(_getContainerHierarchy,
        doc = '''
        Return a list of Stream subclasses that this Stream
        is contained within or derived from. This provides a way of seeing
        Streams contained within Streams.

        >>> s = corpus.parse('bach/bwv66.6')
        >>> [e for e in s[1][2][3].containerHierarchy]
        [<music21.stream.Measure 1 offset=1.0>, 
         <music21.stream.Part Soprano>, 
         <music21.stream.Score ...>]
        
        
        Note that derived objects also can follow the container hierarchy:
        
        >>> import copy
        >>> n2 = copy.deepcopy(s[1][2][3])
        >>> [e for e in s[1][2][3].containerHierarchy]
        [<music21.stream.Measure 1 offset=1.0>, 
         <music21.stream.Part Soprano>, 
         <music21.stream.Score ...>]
        ''')




    def splitAtQuarterLength(self, 
                             quarterLength, 
                             retainOrigin=True,
                             addTies=True, 
                             displayTiedAccidentals=False, 
                             delta=1e-06):
        '''
        Split an Element into two Elements at a provided
        `quarterLength` (offset) into the Element.


        >>> a = note.Note('C#5')
        >>> a.duration.type = 'whole'
        >>> a.articulations = [articulations.Staccato()]
        >>> a.lyric = 'hi'
        >>> a.expressions = [expressions.Mordent(), expressions.Trill(), expressions.Fermata()]
        >>> b, c = a.splitAtQuarterLength(3)
        >>> b.duration.type
        'half'
        >>> b.duration.dots
        1
        >>> b.duration.quarterLength
        3.0
        >>> b.articulations
        [<music21.articulations.Staccato>]
        >>> b.lyric
        'hi'
        >>> b.expressions
        [<music21.expressions.Mordent>, <music21.expressions.Trill>]
        >>> c.duration.type
        'quarter'
        >>> c.duration.dots
        0
        >>> c.duration.quarterLength
        1.0
        >>> c.articulations
        []
        >>> c.lyric
        >>> c.expressions
        [<music21.expressions.Trill>, <music21.expressions.Fermata>]

        Make sure that ties remain as they should be:

        >>> d = note.Note('D#4')
        >>> d.duration.quarterLength = 3.0
        >>> d.tie = tie.Tie('start')
        >>> e, f = d.splitAtQuarterLength(2.0)
        >>> e.tie, f.tie
        (<music21.tie.Tie start>, <music21.tie.Tie continue>)

        Should be the same for chords...

        >>> g = chord.Chord(['C4', 'E4', 'G4'])
        >>> g.duration.quarterLength = 3.0
        >>> g._notes[1].tie = tie.Tie('start')
        >>> h, i = g.splitAtQuarterLength(2.0)
        >>> for j in range(0,3):
        ...   h._notes[j].tie, i._notes[j].tie
        (<music21.tie.Tie start>, <music21.tie.Tie stop>)
        (<music21.tie.Tie start>, <music21.tie.Tie continue>)
        (<music21.tie.Tie start>, <music21.tie.Tie stop>)
        
        
        If quarterLength == self.quarterLength then the second element will be None.
        
        >>> n = note.Note()
        >>> n.quarterLength = 0.5
        >>> a, b = n.splitAtQuarterLength(0.5)
        >>> b is None
        True
        >>> a is n
        True
        
        (same with retainOrigin off)
        
        >>> n = note.Note()
        >>> n.quarterLength = 0.5
        >>> a, b = n.splitAtQuarterLength(0.5, retainOrigin=False)
        >>> a is n
        False
        
        
        If quarterLength > self.quarterLength then a DurationException will be raised:
        
        >>> n = note.Note()
        >>> n.quarterLength = 0.5
        >>> a, b = n.splitAtQuarterLength(0.7)
        Traceback (most recent call last):
        DurationException: cannot split a duration (0.5) at this quarterLength (0.7)
        '''
        # needed for temporal manipulations; not music21 objects
        from music21 import tie

        if self.duration is None:
            raise Exception('cannot split an element that has a Duration of None')

        if quarterLength - delta > self.duration.quarterLength:
            raise duration.DurationException(
            "cannot split a duration (%s) at this quarterLength (%s)" % (
            self.duration.quarterLength, quarterLength))

        if retainOrigin is True:
            e = self
        else:
            e = copy.deepcopy(self)
        eRemain = copy.deepcopy(self)

        # clear articulations from remaining parts
        if hasattr(eRemain, 'articulations'):
            eRemain.articulations = []
        if hasattr(eRemain, 'lyrics'):
            eRemain.lyrics = []

        if hasattr(e, 'expressions'):
            tempExpressions = e.expressions
            e.expressions = [] # pylint: disable=attribute-defined-outside-init
            eRemain.expressions = []
            for thisExpression in tempExpressions:
                if hasattr(thisExpression, 'tieAttach'):
                    if thisExpression.tieAttach == 'first':
                        e.expressions.append(thisExpression)
                    elif thisExpression.tieAttach == 'last':
                        eRemain.expressions.append(thisExpression)
                    else:  # default = 'all'
                        e.expressions.append(thisExpression)
                        eRemain.expressions.append(thisExpression)
                else: # default = 'all'
                    e.expressions.append(thisExpression)
                    eRemain.expressions.append(thisExpression)

        if quarterLength < delta:
            quarterLength = 0
        elif abs(quarterLength - self.duration.quarterLength) < delta:
            quarterLength = self.duration.quarterLength

        lenEnd = self.duration.quarterLength - quarterLength
        lenStart = self.duration.quarterLength - lenEnd

        d1 = duration.Duration()
        d1.quarterLength = lenStart

        d2 = duration.Duration()
        d2.quarterLength = lenEnd

        e.duration = d1
        eRemain.duration = d2

        # some higher-level classes need this functionality
        # set ties
        if addTies and ('Note' in e.classes or
            'Unpitched' in e.classes):

            forceEndTieType = 'stop'
            if e.tie is not None:
                # the last tie of what was formally a start should
                # continue
                if e.tie.type == 'start':
                    # keep start  if already set
                    forceEndTieType = 'continue'
                # a stop was ending a previous tie; we know that
                # the first is now a continue
                elif e.tie.type == 'stop':
                    forceEndTieType = 'stop'
                    e.tie.type = 'continue'
                elif e.tie.type == 'continue':
                    forceEndTieType = 'continue'
                    # keep continue if already set
            else:
                e.tie = tie.Tie('start')  # pylint: disable=attribute-defined-outside-init
                # # need a tie object

            eRemain.tie = tie.Tie(forceEndTieType)

        elif addTies and 'Chord' in e.classes:
            for i in range(len(e._notes)):
                component = e._notes[i]
                remainComponent = eRemain._notes[i]
                forceEndTieType = 'stop'
                if component.tie is not None:
                    # the last tie of what was formally a start should
                    # continue
                    if component.tie.type == 'start':
                        # keep start  if already set
                        forceEndTieType = 'continue'
                    # a stop was ending a previous tie; we know that
                    # the first is now a continue
                    elif component.tie.type == 'stop':
                        forceEndTieType = 'stop'
                        component.tie.type = 'continue'
                    elif component.tie.type == 'continue':
                        forceEndTieType = 'continue'
                        # keep continue if already set
                else:
                    component.tie = tie.Tie('start') # need a tie object
                remainComponent.tie = tie.Tie(forceEndTieType)

        # hide accidentals on tied notes where previous note
        # had an accidental that was shown
        # this is not general enough, for things like chords
        if hasattr(e, 'pitch'):
            if hasattr(e.pitch, 'accidental') and e.pitch.accidental is not None:
                if not displayTiedAccidentals: # if False
                    if (e.pitch.accidental.displayType not in
                        ['even-tied']):
                        eRemain.pitch.accidental.displayStatus = False
                else: # display tied accidentals
                    eRemain.pitch.accidental.displayType = 'even-tied'
                    eRemain.pitch.accidental.displayStatus = True

        if eRemain.duration.quarterLength > 0.0:
            return [e, eRemain]
        else:
            return [e, None]

    def splitByQuarterLengths(self, 
                              quarterLengthList, 
                              addTies=True,
                              displayTiedAccidentals=False):
        '''
        Given a list of quarter lengths, return a list of
        Music21Object objects, copied from this Music21Object,
        that are partitioned and tied with the specified quarter
        length list durations.


        >>> n = note.Note()
        >>> n.quarterLength = 3
        >>> post = n.splitByQuarterLengths([1,1,1])
        >>> [n.quarterLength for n in post]
        [1.0, 1.0, 1.0]
        '''
        # needed for temporal manipulations; not music21 objects
        from music21 import tie

        if self.duration is None:
            raise Music21ObjectException('cannot split an element that has a Duration of None')

        if opFrac(sum(quarterLengthList)) != self.duration.quarterLength:
            raise Music21ObjectException('cannot split by quarter length list that is not ' + 
                                         'equal to the duration of the source: %s, %s' % 
                                         (quarterLengthList, self.duration.quarterLength))
        # if nothing to do
        elif (len(quarterLengthList) == 1 and opFrac(quarterLengthList[0]) ==
            self.duration.quarterLength):
            # return a copy of self in a list
            return [copy.deepcopy(self)]
        elif len(quarterLengthList) <= 1:
            raise Music21ObjectException('cannot split by this quarter length list: %s.' % 
                                         (quarterLengthList,))

        post = []
        forceEndTieType = 'stop'
        for i in range(len(quarterLengthList)):
            ql = opFrac(quarterLengthList[i])
            e = copy.deepcopy(self)
            e.quarterLength = ql

            if i != 0:
                # clear articulations from remaining parts
                if hasattr(e, 'articulations'):
                    e.articulations = []


            if addTies:
                # if not last
                if i == 0:
                    # if the first elements has a Tie, then the status
                    # of that Tie needs to be continued here and, at the
                    # end of all durations in this block.
                    if e.tie is not None:
                        # the last tie of what was formally a start should
                        # continue
                        if e.tie.type == 'start':
                            # keep start  if already set
                            forceEndTieType = 'continue'
                        # a stop was ending a previous tie; we know that
                        # the first is now a continue
                        elif e.tie.type == 'stop':
                            forceEndTieType = 'stop'
                            e.tie.type = 'continue'
                        elif e.tie.type == 'continue':
                            forceEndTieType = 'continue'
                            # keep continue if already set
                    else:
                        e.tie = tie.Tie('start') # need a tie objects
                elif i < (len(quarterLengthList) - 1):
                    e.tie = tie.Tie('continue') # need a tie objects
                else: # if last
                    # last note just gets the tie of the original Note
                    e.tie = tie.Tie(forceEndTieType)

            # hide accidentals on tied notes where previous note
            # had an accidental that was shown
            if i != 0:
                # look at self for characteristics of origin
                if hasattr(self, 'pitch') and self.pitch.accidental is not None:
                    if not displayTiedAccidentals: # if False
                        # do not show accidentals unless display type in 'even-tied'
                        if (self.pitch.accidental.displayType not in
                            ['even-tied']):
                            e.pitch.accidental.displayStatus = False
                    else: # display tied accidentals
                        e.pitch.accidental.displayType = 'even-tied'
                        e.pitch.accidental.displayStatus = True

            post.append(e)

        return post

    def splitAtDurations(self):
        '''
        Takes a Music21Object (e.g., a note.Note) and returns a list of similar
        objects with only a single duration.DurationTuple in each.
        Ties are added if the object supports ties.

        Articulations only appear on the first note.  Same with lyrics.

        Fermatas should be on last note, but not done yet.

        >>> a = note.Note()
        >>> a.duration.clear() # remove defaults
        >>> a.duration.addDurationTuple(duration.durationTupleFromTypeDots('half', 0))
        >>> a.duration.quarterLength
        2.0
        >>> a.duration.addDurationTuple(duration.durationTupleFromTypeDots('whole', 0))
        >>> a.duration.quarterLength
        6.0
        >>> b = a.splitAtDurations()
        >>> b
        [<music21.note.Note C>, <music21.note.Note C>]
        >>> b[0].pitch == b[1].pitch
        True
        >>> b[0].duration
        <music21.duration.Duration 2.0>
        >>> b[0].duration.type
        'half'
        >>> b[1].duration.type
        'whole'
        >>> b[0].quarterLength, b[1].quarterLength
        (2.0, 4.0)

        >>> c = note.Note()
        >>> c.quarterLength = 2.5
        >>> d, e = c.splitAtDurations()
        >>> d.duration.type
        'half'
        >>> e.duration.type
        'eighth'
        >>> d.tie.type
        'start'
        >>> print(e.tie)
        <music21.tie.Tie stop>

        Assume c is tied to the next note.  Then the last split note should also be tied

        >>> c.tie = tie.Tie()
        >>> d, e = c.splitAtDurations()
        >>> e.tie.type
        'start'

        Rests have no ties:

        >>> f = note.Rest()
        >>> f.quarterLength = 2.5
        >>> g, h = f.splitAtDurations()
        >>> (g.duration.type, h.duration.type)
        ('half', 'eighth')
        >>> g.tie is None
        True
        '''
        # needed for temporal manipulations; not music21 objects
        from music21 import tie

        if self.duration is None:
            raise Exception('cannot split an element that has a Duration of None')

        returnNotes = []
        if hasattr(self, 'linkage'):
            linkageType = self.linkage
        else:
            linkageType = None

        for i in range(len(self.duration.components)):
            tempNote = copy.deepcopy(self)
            if i != 0:
                # clear articulations from remaining parts
                if hasattr(tempNote, 'articulations'):
                    tempNote.articulations = []
                if hasattr(tempNote, 'lyrics'):
                    tempNote.lyrics = []

            tempNote.duration.clear()
            tempNote.duration.addDurationTuple(self.duration.components[i])
            if i != (len(self.duration.components) - 1): # if not last note, use linkage
                if linkageType is None:
                    pass
                elif linkageType == 'tie':
                    tempNote.tie = tie.Tie()
            else:
                # last note just gets the tie of the original Note
                if hasattr(self, 'tie') and self.tie is None:
                    tempNote.tie = tie.Tie("stop")
                elif hasattr(self, 'tie') and self.tie is not None and self.tie.type == 'stop':
                    tempNote.tie = tie.Tie("stop")
                elif hasattr(self, 'tie'):
                    tempNote.tie = copy.deepcopy(self.tie)
            returnNotes.append(tempNote)
        return returnNotes

    #--------------------------------------------------------------------------
    # temporal and beat based positioning

    def _getMeasureNumber(self):
        '''
        If this object is contained in a Measure, return the measure number
        '''
        mNumber = None # default for not defined
        if self.activeSite is not None and self.activeSite.isMeasure:
            mNumber = self.activeSite.number
        else:
            # testing sortByCreationTime == true; this may be necessary
            # as we often want the most recent measure
            for cs in self.contextSites():
                m = cs[0]
                if 'Measure' in m.classes:
                    mNumber = m.number
        return mNumber

    measureNumber = property(_getMeasureNumber,
        doc = '''
        Return the measure number of a :class:`~music21.stream.Measure` that contains this
        object if the object is in a measure.

        Returns None if the object is not in a measure.  Also note that by 
        default Measure objects
        have measure number 0.

        If an object belongs to multiple measures (not in the same hierarchy...) 
        then it returns the
        measure number of the :meth:`~music21.base.Music21Object.activeSite` if that is a
        :class:`~music21.stream.Measure` object.  Otherwise it will use 
        :meth:`~music21.base.Music21Object.getContextByClass`
        to find the number of the measure it was most recently added to.


        >>> m = stream.Measure()
        >>> m.number = 12
        >>> n = note.Note()
        >>> m.append(n)
        >>> n.measureNumber
        12

        >>> n2 = note.Note()
        >>> n2.measureNumber is None
        True
        >>> m2 = stream.Measure()
        >>> m2.append(n2)
        >>> n2.measureNumber
        0

        This updates live if the measure number changes:

        >>> m2.number = 11
        >>> n2.measureNumber
        11


        The most recent measure added to is used unless activeSite is a measure:

        >>> m.append(n2)
        >>> n2.measureNumber
        12
        >>> n2.activeSite = m2
        >>> n2.measureNumber
        11
        
        Copies can retain measure numbers until set themselves:
        
        >>> import copy
        >>> nCopy = copy.deepcopy(n2)
        >>> nCopy.measureNumber
        12
        >>> m3 = stream.Measure()
        >>> m3.number = 4
        >>> m3.append(nCopy)
        >>> nCopy.measureNumber
        4
        ''')

    def _getMeasureOffset(self, includeMeasurePadding=True):
        '''
        Try to obtain the nearest Measure that contains this object,
        and return the offset of this object within that Measure.

        If a Measure is found, and that Measure has padding
        defined as `paddingLeft` (for pickup measures, etc.), padding will be added to the
        native offset gathered from the object.

        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> m = stream.Measure()
        >>> n._getMeasureOffset() # returns zero when not assigned
        0.0
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.repeatAppend(n, 4)
        >>> [n._getMeasureOffset() for n in m.notes]
        [0.0, 0.5, 1.0, 1.5]
        '''
        if self.activeSite is not None and self.activeSite.isMeasure:
            #environLocal.printDebug(['found activeSite as Measure, using for offset'])
            offsetLocal = self.getOffsetBySite(self.activeSite)
            if includeMeasurePadding:
                offsetLocal += self.activeSite.paddingLeft
        else:
            #environLocal.printDebug(['did not find activeSite as Measure, 
            #    doing context search', 'self.activeSite', self.activeSite])
            # testing sortByCreationTime == true; this may be necessary
            # as we often want the most recent measure
            m = self.getContextByClass('Measure', sortByCreationTime=True)
            if m is not None:
                #environLocal.printDebug(['using found Measure for offset access'])
                try:
                    if includeMeasurePadding:
                        offsetLocal = m.elementOffset(self) + m.paddingLeft
                    else:
                        offsetLocal = m.elementOffset(self)
                except SitesException:
                    try:
                        offsetLocal = self.offset
                    except AttributeError:
                        offsetLocal = 0.0

            else: # hope that we get the right one
                #environLocal.printDebug(
                #  ['_getMeasureOffset(): cannot find a Measure; using standard offset access'])
                offsetLocal = self.offset

        #environLocal.printDebug(
        #     ['_getMeasureOffset(): found local offset as:', offsetLocal, self])
        return offsetLocal

    def _getMeasureOffsetOrMeterModulusOffset(self, ts):
        '''
        Return the measure offset based on a Measure, if it exists,
        otherwise based on meter modulus of the TimeSignature.
        This assumes that a TimeSignature has already been found.

        >>> m = stream.Measure()
        >>> ts1 = meter.TimeSignature('3/4')
        >>> m.insert(0, ts1)
        >>> n1 = note.Note()
        >>> m.insert(2, n1)
        >>> n1._getMeasureOffsetOrMeterModulusOffset(ts1)
        2.0
        >>> n2 = note.Note()
        >>> m.insert(4, n2) # exceeding the range of the Measure gets a modulus
        >>> n1._getMeasureOffsetOrMeterModulusOffset(ts1)
        2.0

        Can be applied to Notes in a Stream with a TimeSignature.

        >>> ts2 = meter.TimeSignature('5/4')
        >>> s2 = stream.Stream()
        >>> s2.insert(0, ts2)
        >>> n3 = note.Note()
        >>> s2.insert(3, n3)
        >>> n3._getMeasureOffsetOrMeterModulusOffset(ts2)
        3.0
        >>> n4 = note.Note()
        >>> s2.insert(5, n4)
        >>> n4._getMeasureOffsetOrMeterModulusOffset(ts2)
        0.0
        '''
        #environLocal.printDebug(['_getMeasureOffsetOrMeterModulusOffset', 
        # self, ts, 'ts._getMeasureOffset()', ts._getMeasureOffset(), 
        # 'self._getMeasureOffset()', self._getMeasureOffset()])
        mOffset = self._getMeasureOffset()
        tsMeasureOffset = ts._getMeasureOffset(includeMeasurePadding=False)
        if (mOffset + tsMeasureOffset) < ts.barDuration.quarterLength:
            return mOffset
        else:
            # must get offset relative to not just start of Stream, but the last
            # time signature
            post = ((mOffset - tsMeasureOffset) % ts.barDuration.quarterLength)
            #environLocal.printDebug(['result', post])
            return post

    def _getBeat(self):
        '''
        Return a beat designation based on local
        Measure and TimeSignature

        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> m = stream.Measure()
        >>> m.isMeasure
        True
        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> m.repeatAppend(n, 2)
        >>> m[1].activeSite # here we get the activeSite, but not in m.notes
        <music21.stream.Measure 0 offset=0.0>

        >>> m.notes[0]._getBeat()
        1.0
        >>> m.notes[1]._getBeat()
        3.0
        
        >>> m = stream.Measure()        
        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> n = note.Note()
        >>> n.quarterLength = 1./3
        >>> m.repeatAppend(n, 12)
        >>> for i in range(5):
        ...    print(m.notes[i].beat)
        1.0
        4/3
        5/3
        2.0
        7/3
        '''
        ts = self.getContextByClass('TimeSignature')
        if ts is None:
            raise Music21ObjectException('this object does not have a TimeSignature in Sites')
        return ts.getBeatProportion(
            self._getMeasureOffsetOrMeterModulusOffset(ts))

    beat = property(_getBeat,
        doc = '''
        Return the beat of this object as found in the most
        recently positioned Measure. Beat values count from 1 and
        contain a floating-point designation between 0 and 1 to
        show proportional progress through the beat.


        >>> n = note.Note()
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [m.notes[i].beat for i in range(6)]
        [1.0, 1.5, 2.0, 2.5, 3.0, 3.5]

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [m.notes[i].beat for i in range(6)]
        [1.0, Fraction(4, 3), Fraction(5, 3), 2.0, Fraction(7, 3), Fraction(8, 3)]
        
        >>> s = stream.Stream()
        >>> s.insert(0, meter.TimeSignature('3/4'))
        >>> s.repeatAppend(note.Note(), 8)
        >>> [n.beat for n in s.notes]
        [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0]


        >>> s = stream.Stream()
        >>> ts = meter.TimeSignature('4/4')
        >>> s.insert(0, ts)
        >>> n = note.Note(type='eighth')
        >>> s.repeatAppend(n, 8)
        >>> s.makeMeasures(inPlace = True)
        >>> [n.beat for n in s.flat.notes]
        [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
        ''')

    def _getBeatStr(self):
        ts = self.getContextByClass('TimeSignature')
        #environLocal.printDebug(['_getBeatStr(): found ts:', ts])
        if ts is None:
            raise Music21ObjectException('this object does not have a TimeSignature in Sites')
        return ts.getBeatProportionStr(
            self._getMeasureOffsetOrMeterModulusOffset(ts))

    beatStr = property(_getBeatStr,
        doc = '''
        Return a string representation of the beat of
        this object as found in the most recently positioned
        Measure. Beat values count from 1 and contain a
        fractional designation to show progress through the beat.


        >>> n = note.Note()
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [m.notes[i].beatStr for i in range(6)]
        ['1', '1 1/2', '2', '2 1/2', '3', '3 1/2']
        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [m.notes[i].beatStr for i in range(6)]
        ['1', '1 1/3', '1 2/3', '2', '2 1/3', '2 2/3']

        >>> s = stream.Stream()
        >>> s.insert(0, meter.TimeSignature('3/4'))
        >>> s.repeatAppend(note.Note(), 8)
        >>> [n.beatStr for n in s.notes]
        ['1', '2', '3', '1', '2', '3', '1', '2']
        ''')

    def _getBeatDuration(self):
        '''
        Return a :class:`~music21.duration.Duration` of the beat
        active for this object as found in the most recently
        positioned Measure.


        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> m.repeatAppend(n, 2)
        >>> m.notes[0]._getBeatDuration()
        <music21.duration.Duration 1.0>
        >>> m.notes[1]._getBeatDuration()
        <music21.duration.Duration 1.0>
        '''
        ts = self.getContextByClass('TimeSignature')
        if ts is None:
            raise Music21ObjectException('this object does not have a TimeSignature in Sites')
        return ts.getBeatDuration(
            self._getMeasureOffsetOrMeterModulusOffset(ts))

    beatDuration = property(_getBeatDuration,
        doc = '''
        Return a :class:`~music21.duration.Duration` of the beat active 
        for this object as found in the most recently positioned Measure.

        If extending beyond the Measure, or in a Stream with a TimeSignature, 
        the meter modulus value will be returned.


        >>> n = note.Note()
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [m.notes[i].beatDuration.quarterLength for i in range(6)]
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [m.notes[i].beatDuration.quarterLength for i in range(6)]
        [1.5, 1.5, 1.5, 1.5, 1.5, 1.5]

        >>> s = stream.Stream()
        >>> s.insert(0, meter.TimeSignature('2/4+3/4'))
        >>> s.repeatAppend(note.Note(), 8)
        >>> [n.beatDuration.quarterLength for n in s.notes]
        [2.0, 2.0, 3.0, 3.0, 3.0, 2.0, 2.0, 3.0]
        ''')

    def _getBeatStrength(self):
        '''
        Return the metrical accent of this object
        in the most recently positioned Measure. Accent values
        are between zero and one, and are derived from the local
        TimeSignature's accent MeterSequence weights. If the offset
        of this object does not match a defined accent weight, a
        minimum accent weight will be returned.


        >>> n = note.Note()
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [m.notes[i].beatStrength for i in range(6)]
        [1.0, 0.25, 0.5, 0.25, 0.5, 0.25]

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [m.notes[i].beatStrength for i in range(6)]
        [1.0, 0.25, 0.25, 0.5, 0.25, 0.25]


        We can also get the beatStrength for elements not in
        a measure, if the enclosing stream has a :class:`~music21.meter.TimeSignature`.
        We just assume that the time signature carries through to
        hypothetical following measures:


        >>> n = note.Note('E--3', type='quarter')
        >>> s = stream.Stream()
        >>> s.insert(0.0, meter.TimeSignature('2/2'))
        >>> s.repeatAppend(n, 12)
        >>> [s.notes[i].beatStrength for i in range(12)]
        [1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25]


        Changing the meter changes the output, of course:

        >>> s.insert(4.0, meter.TimeSignature('3/4'))
        >>> [s.notes[i].beatStrength for i in range(12)]
        [1.0, 0.25, 0.5, 0.25, 1.0, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 0.5]


        Test not using measures

        >>> n = note.Note("E--3")
        >>> n.quarterLength = 2
        >>> s = stream.Stream()
        >>> s.isMeasure
        False
        >>> s.insert(0, meter.TimeSignature('2/2'))
        >>> s.repeatAppend(n, 16)
        >>> s.notes[0].beatStrength
        1.0
        >>> s.notes[1].beatStrength
        0.5
        >>> s.notes[4].beatStrength
        1.0
        >>> s.notes[5].beatStrength
        0.5
        '''
        #from music21.meter import MeterException
        ts = self.getContextByClass('TimeSignature')
        if ts is None:
            raise Music21ObjectException('this object does not have a TimeSignature in Sites')

#         environLocal.printDebug(['_getBeatStrength(): calling getAccentWeight()', 
#                'self._getMeasureOffset()', self._getMeasureOffset(), 'ts', ts, 
#                 'ts.getAccentWeight', accentWeight])
        #mOffset = self._getMeasureOffset()

        return ts.getAccentWeight(
            self._getMeasureOffsetOrMeterModulusOffset(ts),
                forcePositionMatch=True, permitMeterModulus=False)

    beatStrength = property(_getBeatStrength)

    def _setSeconds(self, value):
        ti = self.getContextByClass('TempoIndication')
        if ti is None:
            raise Music21ObjectException('this object does not have a TempoIndication in Sites')
        mm = ti.getSoundingMetronomeMark()
        self.duration = mm.secondsToDuration(value)
        for s in self.sites.getSites(excludeNone=True):
            if self in s._elements:
                s.elementsChanged() # highest time is changed.

    def _getSeconds(self):
        # do not search of duration is zero
        if self.duration is None or self.duration.quarterLength == 0.0:
            return 0.0

        ti = self.getContextByClass('TempoIndication')
        if ti is None:
            raise Music21ObjectException('this object does not have a TempoIndication in Sites')
        mm = ti.getSoundingMetronomeMark()
        # once we have mm, simply pass in this duration
        return mm.durationToSeconds(self.duration)

    seconds = property(_getSeconds, _setSeconds, doc='''
        Get or set the duration of this object in seconds, assuming
        that this object has a :class:`~music21.tempo.MetronomeMark` 
        or :class:`~music21.tempo.MetricModulation` in its past context.

        >>> s = stream.Stream()
        >>> s.repeatAppend(note.Note(), 12)
        >>> s.insert(0, tempo.MetronomeMark(number=120))
        >>> s.insert(6, tempo.MetronomeMark(number=240))
        >>> [n.seconds for n in s.notes]
        [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]
        ''')


#-------------------------------------------------------------------------------


class ElementWrapper(Music21Object):
    '''
    An ElementWrapper is a way of containing any object that is not a
    :class:`~music21.base.Music21Object`, so that that object can be positioned
    within a :class:`~music21.stream.Stream`.

    The object stored within ElementWrapper is available from the
    :attr:`~music21.base.ElementWrapper.obj` attribute.  All the attributes of
    the stored object (except .id and anything else that conflicts with a
    Music21Object attribute) are gettable and settable by querying the
    ElementWrapper.  This feature makes it possible easily to mix
    Music21Objects and non-Music21Objects with similarly named attributes in
    the same Stream.

    This example inserts 10 random wave files into a music21 Stream and then
    reports their filename and number of audio channels (in this example, it's
    always 2) if they fall on a strong beat in fast 6/8

    >>> import music21
    >>> #_DOCS_SHOW import wave
    >>> import random
    >>> class Wave_read(object): #_DOCS_HIDE
    ...    def getnchannels(self): return 2 #_DOCS_HIDE

    >>> s = stream.Stream()
    >>> s.id = 'mainStream'
    >>> s.append(meter.TimeSignature('fast 6/8'))
    >>> for i in range(10):
    ...    fileName = 'thisSound_' + str(random.randint(1,20)) + '.wav'
    ...    fileName = 'thisSound_' + str(1+((i * 100) % 19)) + '.wav' #_DOCS_HIDE 
    ...    soundFile = Wave_read() #_DOCS_HIDE # #make a more predictable "random" set.
    ...    #_DOCS_SHOW soundFile = wave.open(fileName)
    ...    soundFile.fileName = fileName
    ...    el = music21.ElementWrapper(soundFile)
    ...    s.insert(i, el)

    >>> for j in s.getElementsByClass('ElementWrapper'):
    ...    if j.beatStrength > 0.4:
    ...        (j.offset, j.beatStrength, j.getnchannels(), j.fileName)
    (0.0, 1.0, 2, 'thisSound_1.wav')
    (3.0, 1.0, 2, 'thisSound_16.wav')
    (6.0, 1.0, 2, 'thisSound_12.wav')
    (9.0, 1.0, 2, 'thisSound_8.wav')
    >>> for j in s.getElementsByClass('ElementWrapper'):
    ...    if j.beatStrength > 0.4:
    ...        (j.offset, j.beatStrength, j.getnchannels() + 1, j.fileName)
    (0.0, 1.0, 3, 'thisSound_1.wav')
    (3.0, 1.0, 3, 'thisSound_16.wav')
    (6.0, 1.0, 3, 'thisSound_12.wav')
    (9.0, 1.0, 3, 'thisSound_8.wav')

    Test representation of an ElementWrapper

    >>> for i, j in enumerate(s.getElementsByClass('ElementWrapper')):
    ...     if i == 2:
    ...         j.id = None
    ...     else:
    ...         j.id = str(i) + "_wrapper"
    ...     if i <=2:
    ...         print(j)
    <ElementWrapper id=0_wrapper offset=0.0 obj="<...Wave_read object...">
    <ElementWrapper id=1_wrapper offset=1.0 obj="<...Wave_read object...">
    <ElementWrapper offset=2.0 obj="<...Wave_read object...">
    '''
    _id = None
    obj = None
    
    _DOC_ORDER = ['obj']
    _DOC_ATTR = {
        'obj': 'The object this wrapper wraps. It should not be a Music21Object.',
        }

    def __init__(self, obj=None):
        Music21Object.__init__(self)
        self.obj = obj # object stored here
        # the unlinkedDuration is the duration that is inherited from
        # Music21Object
        #self._unlinkedDuration = None

    #--------------------------------------------------------------------------

    def __repr__(self):
        shortObj = (str(self.obj))[0:30]
        if len(str(self.obj)) > 30:
            shortObj += "..."

        if self.id is not None:
            return '<%s id=%s offset=%s obj="%s">' % \
                (self.__class__.__name__, self.id, self.offset, shortObj)
        else:
            return '<%s offset=%s obj="%s">' % \
                (self.__class__.__name__, self.offset, shortObj)

    def __eq__(self, other):
        '''Test ElementWrapper equality

        >>> import music21
        >>> n = note.Note("C#")
        >>> a = music21.ElementWrapper(n)
        >>> a.offset = 3.0
        >>> b = music21.ElementWrapper(n)
        >>> b.offset = 3.0
        >>> a == b
        True
        >>> a is not b
        True
        >>> c = music21.ElementWrapper(n)
        >>> c.offset = 2.0
        >>> c.offset
        2.0
        >>> a == c
        False
        '''
        if not hasattr(other, "obj") or \
           not hasattr(other, "offset") or \
           not hasattr(other, "priority") or \
           not hasattr(other, "groups") or \
           not hasattr(other, "activeSite") or \
           not hasattr(other, "duration"):
            return False


        if (self.obj == other.obj and \
            self.offset == other.offset and \
            self.priority == other.priority and \
            self.groups == other.groups and \
            self.duration == self.duration):
            return True
        else:
            return False

    def __ne__(self, other):
        '''
        '''
        return not self.__eq__(other)

    def __setattr__(self, name, value):
        #environLocal.printDebug(['calling __setattr__ of ElementWrapper', name, value])

        # if in the ElementWrapper already, set that first
        if name in self.__dict__:
            object.__setattr__(self, name, value)

        # if not, change the attribute in the stored object
        storedobj = object.__getattribute__(self, "obj")
        if name not in ['offset', '_offset', '_activeSite'] and \
            storedobj is not None and hasattr(storedobj, name):
            setattr(storedobj, name, value)
        # unless neither has the attribute, in which case add it to the ElementWrapper
        else:
            object.__setattr__(self, name, value)

    def __getattr__(self, name):
        '''This method is only called when __getattribute__() fails.
        Using this also avoids the potential recursion problems of subclassing
        __getattribute__()_

        see: http://stackoverflow.com/questions/371753/python-using-getattribute-method 
        for examples

        '''
        storedobj = Music21Object.__getattribute__(self, "obj")
        if storedobj is None:
            raise AttributeError("Could not get attribute '" + name + 
                                 "' in an object-less element")
        else:
            return object.__getattribute__(storedobj, name)

    def isTwin(self, other):
        '''
        A weaker form of equality.  a.isTwin(b) is true if
        a and b store either the same object OR objects that are equal.
        In other words, it is essentially the same object in a different context

        >>> import copy
        >>> import music21

        >>> aE = music21.ElementWrapper(obj = "hello")

        >>> bE = copy.copy(aE)
        >>> aE is bE
        False
        >>> aE == bE
        True
        >>> aE.isTwin(bE)
        True

        >>> bE.offset = 14.0
        >>> bE.priority = -4
        >>> aE == bE
        False
        >>> aE.isTwin(bE)
        True
        '''
        if not hasattr(other, "obj"):
            return False

        if (self.obj is other.obj or self.obj == other.obj):
            return True
        else:
            return False


#------------------------------------------------------------------------------


class TestMock(Music21Object):
    def __init__(self):
        Music21Object.__init__(self)


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        for part in sys.modules[self.__module__].__dict__:
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
                i = copy.copy(obj)
                j = copy.deepcopy(obj)

    def testObjectCreation(self):
        a = TestMock()
        a.groups.append("hello")
        a.id = "hi"
        a.offset = 2.0
        assert(a.offset == 2.0)

    def testElementEquality(self):
        from music21 import note
        n = note.Note("F-")
        a = ElementWrapper(n)
        a.offset = 3.0
        c = ElementWrapper(n)
        c.offset = 3.0
        assert (a == c)
        assert (a is not c)
        b = ElementWrapper(n)
        b.offset = 2.0
        assert (a != b)

    def testNoteCreation(self):
        from music21 import note
        n = note.Note('A')
        n.offset = 1.0 #duration.Duration("quarter")
        n.groups.append("flute")

        b = copy.deepcopy(n)
        b.offset = 2.0 # duration.Duration("half")

        self.assertFalse(n is b)
        n.accidental = "-"
        self.assertEqual(b.name, "A")
        self.assertEqual(n.offset, 1.0)
        self.assertEqual(b.offset, 2.0)
        n.groups[0] = "bassoon"
        self.assertFalse("flute" in n.groups)
        self.assertTrue("flute" in b.groups)

    def testOffsets(self):
        from music21 import note
        a = ElementWrapper(note.Note('A#'))
        a.offset = 23.0
        self.assertEqual(a.offset, 23.0)

    def testObjectsAndElements(self):
        from music21 import note, stream
        note1 = note.Note("B-")
        note1.duration.type = "whole"
        stream1 = stream.Stream()
        stream1.append(note1)
        unused_subStream = stream1.notes


    def testM21BaseDeepcopy(self):
        '''
        Test copying
        '''
        a = Music21Object()
        a.id = 'test'
        b = copy.deepcopy(a)
        self.assertNotEqual(a, b)
        self.assertEqual(b.id, 'test')

    def testM21BaseSites(self):
        '''
        Basic testing of M21 base object sites
        '''
        from music21 import stream, base # self import needed.
        a = base.Music21Object()
        b = stream.Stream()

        # storing a single offset does not add a Sites entry
        a.offset = 30
        # all offsets are store in locations
        self.assertEqual(len(a.sites), 1)
        self.assertEqual(a._naiveOffset, 30.0)
        self.assertEqual(a.offset, 30.0)

        # assigning a activeSite directly # v2.1. no longer allowed if not in site
        def assignActiveSite(a, b): 
            a.activeSite = b
        self.assertRaises(SitesException, assignActiveSite, a,b)
        # now we have two offsets in locations
        b.insert(a)
        self.assertEqual(len(a.sites), 2)
        self.assertEqual(a.activeSite, b)

        a.offset = 40
        # still have activeSite
        self.assertEqual(a.activeSite, b)
        # now the offst returns the value for the current activeSite
        #b.setElementOffset(a, 40.0)
        self.assertEqual(a.offset, 40.0)

        # assigning a activeSite to None
        a.activeSite = None
        # properly returns original offset
        self.assertEqual(a.offset, 30.0)
        # we still have two locations stored
        self.assertEqual(len(a.sites), 2)
        self.assertEqual(a.getOffsetBySite(b), 40.0)

    def testM21BaseLocationsCopy(self):
        '''
        Basic testing of M21 base object
        '''
        from music21 import stream, base
        a = stream.Stream()
        a.id = "a obj"
        b = base.Music21Object()
        b.id = "b obj"

        b.id = 'test'
        a.insert(0, b)
        c = copy.deepcopy(b)
        c.id = "c obj"

        # have two locations: None, and that set by assigning activeSite
        self.assertEqual(len(b.sites), 2)
        dummy = c.sites
        # c is in 1 site, None, because it is a copy of b
        self.assertEqual(len(c.sites), 1)


    def testM21BaseLocationsCopyB(self):
        # the active site of a deepcopy should not be the same?
        #self.assertEqual(post[-1].activeSite, a)
        from music21 import stream, base
        a = stream.Stream()
        b = base.Music21Object()
        b.id = 'test'
        a.insert(30, b)
        b.activeSite = a        
        
        d = stream.Stream()
        self.assertEqual(b.activeSite, a)
        self.assertEqual(len(b.sites), 2)
        c = copy.deepcopy(b)
        self.assertIs(c.activeSite, None)
        d.insert(20, c)
        self.assertEqual(len(c.sites), 2)

        # this works because the activeSite is being set on the object
        # the copied activeSite has been deepcopied, and cannot now be accessed
        # this fails! post[-1].getOffsetBySite(a)


    def testSitesSearch(self):
        from music21 import note, stream, clef

        n1 = note.Note('A')
        n2 = note.Note('B')
        c1 = clef.TrebleClef()
        c2 = clef.BassClef()

        s1 = stream.Stream()
        s1.insert(10, n1)
        s1.insert(100, n2)

        s2 = stream.Stream()
        s2.insert(0, c1)
        s2.insert(100, c2)
        s2.insert(10, s1) # placing s1 here should result in c2 being before n2

        self.assertEqual(s1.getOffsetBySite(s2), 10)
        # make sure in the context of s1 things are as we expect
        self.assertEqual(s2.flat.getElementAtOrBefore(0), c1)
        self.assertEqual(s2.flat.getElementAtOrBefore(100), c2)
        self.assertEqual(s2.flat.getElementAtOrBefore(20), n1)
        self.assertEqual(s2.flat.getElementAtOrBefore(110), n2)

        # note: we cannot do this
        #self.assertEqual(s2.flat.getOffsetBySite(n2), 110)
        # we can do this:
        self.assertEqual(n2.getOffsetBySite(s2.flat), 110)

        # this seems more idiomatic
        self.assertEqual(s2.flat.elementOffset(n2), 110)

        # both notes can find the treble clef in the activeSite stream
        post = n1.getContextByClass(clef.TrebleClef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)

        post = n2.getContextByClass(clef.TrebleClef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)

        # n1 cannot find a bass clef
        post = n1.getContextByClass(clef.BassClef)
        self.assertEqual(post, None)

        # n2 can find a bass clef, due to its shifted position in s2
        post = n2.getContextByClass(clef.BassClef)
        self.assertEqual(isinstance(post, clef.BassClef), True)

    def testSitesMeasures(self):
        '''Can a measure determine the last Clef used?
        '''
        from music21 import corpus, clef, stream
        a = corpus.parse('bach/bwv324.xml')
        measures = a.parts[0].getElementsByClass('Measure') # measures of first part

        # the activeSite of measures[1] is set to the new output stream
        self.assertEqual(measures[1].activeSite, measures)
        # the source Part should still be a context of this measure
        self.assertEqual(measures[1].hasSite(a.parts[0]), True)

        # from the first measure, we can get the clef by using
        # getElementsByClass
        post = measures[0].getElementsByClass(clef.Clef)
        self.assertEqual(isinstance(post[0], clef.TrebleClef), True)

        # make sure we can find offset in a flat representation        
        self.assertRaises(SitesException, a.parts[0].flat.elementOffset, a.parts[0][3])

        # for the second measure
        post = a.parts[0][3].getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)

        # for the second measure accessed from measures
        # we can get the clef, now that getContextByClass uses semiFlat
        post = measures[3].getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)

        # add the measure to a new stream
        newStream = stream.Stream()
        newStream.insert(0, measures[3])
        # all previous locations are still available as a context
        self.assertEqual(measures[3].hasSite(newStream), True)
        self.assertEqual(measures[3].hasSite(measures), True)
        self.assertEqual(measures[3].hasSite(a.parts[0]), True)
        # we can still access the clef through this measure on this
        # new stream
        post = newStream[0].getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)

    def testSitesClef(self):
        from music21 import note, stream, clef
        sOuter = stream.Stream()
        sOuter.id = 'sOuter'
        sInner = stream.Stream()
        sInner.id = 'sInner'

        n = note.Note()
        sInner.append(n)
        sOuter.append(sInner)

        unused_tss = sOuter.asTimespans(classList=(sInner.classes[0],), 
                                        recurse='semiFlat') 

        # append clef to outer stream
        sOuter.insert(0, clef.AltoClef())
        pre = sOuter.getElementAtOrBefore(0, [clef.Clef])
        self.assertEqual(isinstance(pre, clef.AltoClef), True)

        # we should be able to find a clef from the lower-level stream
        post = sInner.getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        post = sInner.getClefs(clef.Clef)
        self.assertEqual(isinstance(post[0], clef.AltoClef), True)

    def testBeatAccess(self):
        '''Test getting beat data from various Music21Objects.
        '''
        from music21 import corpus
        s = corpus.parse('bach/bwv66.6.xml')
        p1 = s.parts['Soprano']

        # this does not work; cannot get these values from Measures
        #self.assertEqual(p1.getElementsByClass('Measure')[3].beat, 3)

        # clef/ks can get its beat; these objects are in a pickup,
        # and this give their bar offset relative to the bar
        for classStr in ['Clef', 'KeySignature']:
            self.assertEqual(p1.flat.getElementsByClass(
                classStr)[0].beat, 4.0)
            self.assertEqual(p1.flat.getElementsByClass(
                classStr)[0].beatDuration.quarterLength, 1.0)
            self.assertEqual(
                p1.flat.getElementsByClass(classStr)[0].beatStrength, 0.25)

        # ts can get beatStrength, beatDuration
        self.assertEqual(p1.flat.getElementsByClass(
            'TimeSignature')[0].beatDuration.quarterLength, 1.0)
        self.assertEqual(p1.flat.getElementsByClass(
            'TimeSignature')[0].beatStrength, 0.25)

        # compare offsets found with items positioned in Measures
        # as the first bar is a pickup, the measure offset here is returned
        # with padding (resulting in 3)
        post = []
        for n in p1.flat.notesAndRests:
            post.append(n._getMeasureOffset())
        self.assertEqual(post, [3.0, 3.5, 0.0, 1.0, 2.0, 3.0, 0.0, 
                                1.0, 2.0, 3.0, 0.0, 0.5, 1.0, 2.0, 
                                3.0, 0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 
                                2.0, 3.0, 0.0, 1.0, 2.0, 3.0, 0.0, 
                                1.0, 2.0, 0.0, 2.0, 3.0, 0.0, 1.0, 1.5, 2.0])

        # compare derived beat string
        post = []
        for n in p1.flat.notesAndRests:
            post.append(n.beatStr)
        self.assertEqual(post, ['4', '4 1/2', '1', '2', '3', '4', '1', 
                                '2', '3', '4', '1', '1 1/2', '2', '3', 
                                '4', '1', '2', '3', '4', '1', '2', '3', 
                                '4', '1', '2', '3', '4', '1', '2', '3', 
                                '1', '3', '4', '1', '2', '2 1/2', '3'])

        # for stream and Stream subclass, overridden methods not yet
        # specialzied
        # _getMeasureOffset gets the offset within the activeSite
        # this shows that measure offsets are accommodating pickup
        post = []
        for m in p1.getElementsByClass('Measure'):
            post.append(m._getMeasureOffset())
        self.assertEqual(post, [0.0, 1.0, 5.0, 9.0, 13.0, 17.0, 21.0, 25.0, 29.0, 33.0] )

        # all other methods define None
        post = []
        for n in p1.getElementsByClass('Measure'):
            post.append(n.beat)
        self.assertEqual(post, [None, None, None, None, None, None, None, None, None, None] )

        post = []
        for n in p1.getElementsByClass('Measure'):
            post.append(n.beatStr)
        self.assertEqual(post, [None, None, None, None, None, None, None, None, None, None] )

        post = []
        for n in p1.getElementsByClass('Measure'):
            post.append(n.beatDuration)
        self.assertEqual(post, [None, None, None, None, None, None, None, None, None, None] )

    def testGetBeatStrengthA(self):
        from music21 import stream, note, meter

        n = note.Note('g')
        n.quarterLength = 1
        s = stream.Stream()
        s.insert(0, meter.TimeSignature('4/4'))
        s.repeatAppend(n, 8)
        #match = []
        self.assertEqual([e.beatStrength for e in s.notes], 
                         [1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25])

        n = note.Note('E--3', type='quarter')
        s = stream.Stream()
        s.insert(0.0, meter.TimeSignature('2/2'))
        s.repeatAppend(n, 12)
        match = [s.notes[i].beatStrength for i in range(12)]
        self.assertEqual([1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25], match)

    def testMeaureNumberAccess(self):
        '''Test getting measure numebr data from various Music21Objects.
        '''
        from music21 import corpus, stream, note

        s = corpus.parse('bach/bwv66.6.xml')
        p1 = s.parts['Soprano']
        for classStr in ['Clef', 'KeySignature', 'TimeSignature']:
            self.assertEqual(p1.flat.getElementsByClass(
                classStr)[0].measureNumber, 0)

        match = []
        for n in p1.flat.notesAndRests:
            match.append(n.measureNumber)
        self.assertEqual(match, [0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 
                                 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 
                                 8, 8, 8, 9, 9, 9, 9] )

        # create a note and put it in different measures
        m1 = stream.Measure()
        m1.number = 3
        m2 = stream.Measure()
        m2.number = 74
        n = note.Note()
        self.assertEqual(n.measureNumber, None) # not in a Meaure
        m1.append(n)
        self.assertEqual(n.measureNumber, 3)
        m2.append(n)
        self.assertEqual(n.measureNumber, 74)

    def testPickupMeauresBuilt(self):
        from music21 import stream, meter, note

        s = stream.Score()

        m1 = stream.Measure()
        m1.timeSignature = meter.TimeSignature('4/4')
        n1 = note.Note('d2')
        n1.quarterLength = 1.0
        m1.append(n1)
        # barDuration is baed only on TS
        self.assertEqual(m1.barDuration.quarterLength, 4.0)
        # duration shows the highest offset in the bar
        self.assertEqual(m1.duration.quarterLength, 1.0)
        # presently, the offset of the added note is zero
        self.assertEqual(n1.getOffsetBySite(m1), 0.0)
        # the _getMeasureOffset method is called by all methods that evaluate
        # beat position; this takes padding into account
        self.assertEqual(n1._getMeasureOffset(), 0.0)
        self.assertEqual(n1.beat, 1.0)

        # the Measure.padAsAnacrusis() method looks at the barDuration and,
        # if the Measure is incomplete, assumes its an anacrusis and adds
        # the appropriate padding
        m1.padAsAnacrusis()
        # app values are the same except _getMeasureOffset()
        self.assertEqual(m1.barDuration.quarterLength, 4.0)
        self.assertEqual(m1.duration.quarterLength, 1.0)
        self.assertEqual(n1.getOffsetBySite(m1), 0.0)
        # lowest offset inside of Measure still returns 0
        self.assertEqual(m1.lowestOffset, 0.0)
        # these values are now different
        self.assertEqual(n1._getMeasureOffset(), 3.0)
        self.assertEqual(n1.beat, 4.0)

        # appending this measure to the Score
        s.append(m1)
        # score duration is correct: 1
        self.assertEqual(s.duration.quarterLength, 1.0)
        # lowest offset is that of the first bar
        self.assertEqual(s.lowestOffset, 0.0)
        self.assertEqual(s.highestTime, 1.0)


        m2 = stream.Measure()
        n2 = note.Note('e2')
        n2.quarterLength = 4.0
        m2.append(n2)
        # based on contents
        self.assertEqual(m2.duration.quarterLength, 4.0)
        # we cannot get a bar duration b/c we have not associated a ts
        try:
            m2.barDuration.quarterLength
        except exceptions21.StreamException:
            pass

        # append to Score
        s.append(m2)
        # m2 can now find a time signature by looking to activeSite stream
        self.assertEqual(m2.duration.quarterLength, 4.0)
        # highest time of score takes into account new measure
        self.assertEqual(s.highestTime, 5.0)
        # offset are contiguous when accessed in a flat form
        self.assertEqual([n.offset for n in s.flat.notesAndRests], [0.0, 1.0])


        m3 = stream.Measure()
        n3 = note.Note('f#2')
        n3.quarterLength = 3.0
        m3.append(n3)

        # add to stream
        s.append(m3)
        # m3 can now find a time signature by looking to activeSite stream
        self.assertEqual(m2.duration.quarterLength, 4.0)
        # highest time of score takes into account new measure
        self.assertEqual(s.highestTime, 8.0)
        # offset are contiguous when accessed in a flat form
        self.assertEqual([n.offset for n in s.flat.notesAndRests], [0.0, 1.0, 5.0])

    def testPickupMeauresImported(self):
        from music21 import corpus
        s = corpus.parse('bach/bwv103.6')

        p = s.parts['soprano']
        m1 = p.getElementsByClass('Measure')[0]


        self.assertEqual([n.offset for n in m1.notesAndRests], [0.0, 0.5])
        self.assertEqual(m1.paddingLeft, 3.0)

        #offsets for flat representation have proper spacing
        self.assertEqual([n.offset for n in p.flat.notesAndRests], 
                         [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 
                          8.0, 9.0, 10.0, 11.0, 12.0, 12.5, 13.0, 15.0, 
                          16.0, 16.5, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 
                          23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 28.5, 29.0, 
                          31.0, 32.0, 33.0, 34.0, 34.5, 34.75, 35.0, 35.5, 
                          36.0, 37.0, 38.0, 39.0, 40.0, 41.0, 42.0, 43.0, 
                          44.0, 45.0, 47.0, 48.0, 48.5, 49.0, 50.0, 51.0, 
                          52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0, 
                          60.0, 60.5, 61.0, 63.0] )
        

    def testHighestTime(self):
        from music21 import stream, note, bar
        s = stream.Stream()
        n1 = note.Note()
        n1.quarterLength = 30
        n2 = note.Note()
        n2.quarterLength = 20

        b1 = bar.Barline()
        s.append(n1)
        self.assertEqual(s.highestTime, 30.0)
        s.setElementOffset(b1, 'highestTime')
        
        self.assertEqual(b1.getOffsetBySite(s), 30.0)

        s.append(n2)
        self.assertEqual(s.highestTime, 50.0)
        self.assertEqual(b1.getOffsetBySite(s), 50.0)

    def testGetAllContextsByClass(self):
        from music21 import note, stream, clef
        s1 = stream.Stream()
        s2 = stream.Stream()
        s3 = stream.Stream()

        n1 = note.Note()
        n2 = note.Note()
        n3 = note.Note()
        c1 = clef.Clef()
        c2 = clef.Clef()
        c3 = clef.Clef()

        s1.append(n1)
        s1.append(c1)
        s2.append(n2)
        s2.append(c2)
        s3.append(n3)
        s3.append(c3)

        # only get n1 here, as that is only level available
        self.assertEqual(s1.getAllContextsByClass('Note'), [n1])
        self.assertEqual(s2.getAllContextsByClass('Note'), [n2])
        self.assertEqual(s1.getAllContextsByClass('Clef'), [c1])
        self.assertEqual(s2.getAllContextsByClass('Clef'), [c2])

        # attach s2 to s1
        s2.append(s1)
        # stream 1 gets both notes
        self.assertEqual(s1.getAllContextsByClass('Note'), [n1, n2])
        # clef 1 gets both notes
        self.assertEqual(c1.getAllContextsByClass('Note'), [n1, n2])

        # stream 2 gets all notes, b/c we take a flat version
        self.assertEqual(s2.getAllContextsByClass('Note'), [n1, n2])
        # clef 2 gets both notes
        self.assertEqual(c2.getAllContextsByClass('Note'), [n1, n2])


        # attach s2 to s3
        s3.append(s2)
        # any stream can get all three notes
        self.assertEqual(s1.getAllContextsByClass('Note'), [n1, n2, n3])
        self.assertEqual(s2.getAllContextsByClass('Note'), [n1, n2, n3])
        self.assertEqual(s3.getAllContextsByClass('Note'), [n1, n2, n3])

    def testStoreLastDeepCopyOf(self):
        from music21 import note

        n1 = note.Note()
        n2 = copy.deepcopy(n1)
        self.assertEqual(id(n2.derivation.origin), id(n1))

    def testHasElement(self):
        from music21 import note, stream
        n1 = note.Note()
        s1 = stream.Stream()
        s1.append(n1)
        s2 = copy.deepcopy(s1)
        n2 = s2[0] # this is a new instance; not the same as n1
        self.assertEqual(s2.hasElement(n1), False)
        self.assertEqual(s2.hasElement(n2), True)

        self.assertEqual(n2.hasSite(s1), False)
        self.assertEqual(n2.hasSite(s2), True)

    def testGetContextByClassA(self):
        from music21 import stream, note, tempo

        p = stream.Part()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note(quarterLength=1), 4)
        m2 = copy.deepcopy(m1)
        mm1 = tempo.MetronomeMark(number=50, referent=.25)
        m1.insert(0, mm1)
        mm2 = tempo.MetronomeMark(number=150, referent=.5)
        m2.insert(0, mm2)
        p.append([m1, m2])

        # if done with default args, we get the same object, as we are using
        # getElementAtOrBefore
        self.assertEqual(str(mm2.getContextByClass('MetronomeMark')),
            '<music21.tempo.MetronomeMark Eighth=150>')
        # if we provide the getElementMethod parameter, we can use
        # getElementBeforeOffset
        self.assertEqual(str(mm2.getContextByClass('MetronomeMark',
            getElementMethod='getElementBeforeOffset')),
            '<music21.tempo.MetronomeMark lento 16th=50>')

    def testElementWrapperOffsetAccess(self):
        from music21 import stream, meter
        from music21 import base
        class Mock(object): 
            pass

        s = stream.Stream()
        s.append(meter.TimeSignature('fast 6/8'))
        storage = []
        for i in range(0,2):
            mock = Mock()
            el = base.ElementWrapper(mock)
            storage.append(el)
            s.insert(i, el)

        for ew in storage:
            self.assertEqual(s.hasElement(ew), True)

        match = [e.getOffsetBySite(s) for e in storage]
        self.assertEqual(match, [0.0, 1.0])

        self.assertEqual(s.elementOffset(storage[0]), 0.0)
        self.assertEqual(s.elementOffset(storage[1]), 1.0)

    def testGetActiveSiteTimeSignature(self):
        from music21 import base
        from music21 import stream, meter
        class Wave_read(object): 
            def getnchannels(self): 
                return 2

        s = stream.Stream()
        s.append(meter.TimeSignature('fast 6/8'))
        #s.show('t')
        storage = []
        for i in range(0,6):
            soundFile = Wave_read() #_DOCS_HIDE
            #el = music21.Music21Object() #
            el = base.ElementWrapper(soundFile)
            storage.append(el)
            #print el
            self.assertEqual(el.obj, soundFile)
            s.insert(i, el)

        for ew in storage:
            self.assertEqual(s.hasElement(ew), True)

        matchOffset = []
        matchBeatStrength = []
        matchAudioChannels = []

        for j in s.getElementsByClass('ElementWrapper'):
            matchOffset.append(j.offset)
            matchBeatStrength.append(j.beatStrength)
            matchAudioChannels.append(j.getnchannels())
        self.assertEqual(matchOffset, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertEqual(matchBeatStrength, [1.0, 0.25, 0.25, 1.0, 0.25, 0.25])
        self.assertEqual(matchAudioChannels, [2, 2, 2, 2, 2, 2])

    def testGetMeasureOffsetOrMeterModulusOffsetA(self):
        # test getting metric position in a Stream with a TS
        from music21 import stream, note, meter

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        s.insert(0, meter.TimeSignature('3/4'))

        match = [n.beat for n in s.notes]
        self.assertEqual(match, [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0])

        match = [n.beatStr for n in s.notes]
        self.assertEqual(match, ['1', '2', '3', '1', '2', '3', '1', '2', '3', '1', '2', '3'])

        match = [n.beatDuration.quarterLength for n in s.notes]
        self.assertEqual(match, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

        match = [n.beatStrength for n in s.notes]
        self.assertEqual(match, [1.0, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 0.5, 0.5])

    def testGetMeasureOffsetOrMeterModulusOffsetB(self):
        from music21 import stream, note, meter

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        s.insert(0.0, meter.TimeSignature('3/4'))
        s.insert(3.0, meter.TimeSignature('4/4'))
        s.insert(7.0, meter.TimeSignature('2/4'))

        match = [n.beat for n in s.notes]
        self.assertEqual(match, [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 1.0, 2.0, 1.0])

        match = [n.beatStr for n in s.notes]
        self.assertEqual(match, ['1', '2', '3', '1', '2', '3', '4', '1', '2', '1', '2', '1'])

        match = [n.beatStrength for n in s.notes]
        self.assertEqual(match, [1.0, 0.5, 0.5, 1.0, 0.25, 0.5, 0.25, 1.0, 0.5, 1.0, 0.5, 1.0])

    def testSecondsPropertyA(self):
        from music21 import stream, note, tempo
        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        s.insert(0, tempo.MetronomeMark(number=120))

        self.assertEqual([n.seconds for n in s.notes], 
                         [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])

        # changing tempo mid-stream
        s.insert(6, tempo.MetronomeMark(number=240))
        self.assertEqual([n.seconds for n in s.notes], 
                         [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25])

        # adding notes based on seconds
        s2 = stream.Stream()
        s2.insert(0, tempo.MetronomeMark(number=120))
        s2.append(note.Note())
        s2.notes[0].seconds = 2.0
        self.assertEqual(s2.notes[0].quarterLength, 4.0)
        self.assertEqual(s2.duration.quarterLength, 4.0)

        s2.append(note.Note('C4', type='half'))
        s2.notes[1].seconds = 0.5
        self.assertEqual(s2.notes[1].quarterLength, 1.0)
        self.assertEqual(s2.duration.quarterLength, 5.0)

        s2.append(tempo.MetronomeMark(number=30))
        s2.append(note.Note())
        s2.notes[2].seconds = 0.5
        self.assertEqual(s2.notes[2].quarterLength, 0.25)
        self.assertEqual(s2.duration.quarterLength, 5.25)


    def testGetContextByClassB(self):
        from music21 import stream, note, meter

        s = stream.Score()

        p1 = stream.Part()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note(), 3)
        m1.timeSignature = meter.TimeSignature('3/4')
        m2 = stream.Measure()
        m2.repeatAppend(note.Note(), 3)
        p1.append(m1)
        p1.append(m2)

        p2 = stream.Part()
        m3 = stream.Measure()
        m3.timeSignature = meter.TimeSignature('3/4')
        m3.repeatAppend(note.Note(), 3)
        m4 = stream.Measure()
        m4.repeatAppend(note.Note(), 3)
        p2.append(m3)
        p2.append(m4)

        s.insert(0, p1)
        s.insert(0, p2)

        p3 = stream.Part()
        m5 = stream.Measure()
        m5.timeSignature = meter.TimeSignature('3/4')
        m5.repeatAppend(note.Note(), 3)
        m6 = stream.Measure()
        m6.repeatAppend(note.Note(), 3)
        p3.append(m5)
        p3.append(m6)

        p4 = stream.Part()
        m7 = stream.Measure()
        m7.timeSignature = meter.TimeSignature('3/4')
        m7.repeatAppend(note.Note(), 3)
        m8 = stream.Measure()
        m8.repeatAppend(note.Note(), 3)
        p4.append(m7)
        p4.append(m8)

        s.insert(0, p3)
        s.insert(0, p4)

        #self.targetMeasures = m4
        #n1 = m2[-1] # last element is a note
        n2 = m4[-1] # last element is a note

        #environLocal.printDebug(['getContextByClass()'])
        #self.assertEqual(str(n1.getContextByClass('TimeSignature')), 
        #    '<music21.meter.TimeSignature 3/4>')
        environLocal.printDebug(['getContextByClass()'])
        self.assertEqual(str(n2.getContextByClass('TimeSignature')), 
                         '<music21.meter.TimeSignature 3/4>')

    def testNextA(self):
        from music21 import stream, scale, note
        s = stream.Stream()
        sc = scale.MajorScale()
        notes = []
        for i in sc.pitches:
            n = note.Note()
            s.append(n)
            notes.append(n) # keep for reference and testing

        self.assertEqual(notes[0], s[0])
        self.assertEqual(notes[1], s[0].next())
        self.assertEqual(notes[0], s[1].previous())

        self.assertEqual(id(notes[5]), id(s[4].next()))
        self.assertEqual(id(notes[3]), id(s[4].previous()))

        # if a note has more than one site, what happens
        self.assertEqual(notes[6], s.notes[5].next())
        self.assertEqual(notes[7], s.notes[6].next())

    def testNextB(self):
        from music21 import stream, note

        m1 = stream.Measure()
        m1.number = 1
        n1 = note.Note()
        m1.append(n1)

        m2 = stream.Measure()
        m2.number = 2
        n2 = note.Note()
        m2.append(n2)

        # n1 cannot be connected to n2 as no common site
        self.assertEqual(n1.next(), None)

        p1 = stream.Part()
        p1.append(m1)
        p1.append(m2)
        self.assertEqual(n1.next(), m2)
        self.assertEqual(n1.next('Note'), n2)

    def testNextC(self):
        from music21 import corpus
        s = corpus.parse('bwv66.6')

        # getting time signature and key sig
        p1 = s.parts[0]
        nLast = p1.flat.notes[-1]
        self.assertEqual(str(nLast.previous('TimeSignature')), 
                         '<music21.meter.TimeSignature 4/4>')
        self.assertEqual(str(nLast.previous('KeySignature')),
            '<music21.key.KeySignature of 3 sharps, mode minor>')

        # iterating at the Measure level, showing usage of flattenLocalSites
        measures = s.parts[0].getElementsByClass('Measure')
        self.assertEqual(measures[3].previous(), measures[2])
        self.assertEqual(measures[3].previous(flattenLocalSites=True), measures[2][-1])

        self.assertEqual(measures[3].next(), measures[4])
        self.assertEqual(measures[3].next('Note', flattenLocalSites=True), measures[3].notes[0])

        self.assertEqual(measures[3].previous().previous(), measures[1])
        self.assertEqual(measures[3].previous().previous().previous(), measures[0])
        self.assertEqual(
            str(measures[3].previous().previous().previous().previous()),
            'P1: Soprano: Instrument 1')

        self.assertEqual(str(measures[0].previous()), 'P1: Soprano: Instrument 1')

    def testActiveSiteCopyingA(self):
        from music21 import note, stream

        n1 = note.Note()
        s1 = stream.Stream()
        s1.append(n1)
        self.assertEqual(n1.activeSite, s1)

        n2 = copy.deepcopy(n1)
        self.assertIs(n2._activeSite, None)
        self.assertIs(n2.derivation.origin.activeSite, s1)

    def testSpannerSites(self):
        from music21 import note, spanner, dynamics
        
        n1 = note.Note('C4')
        n2 = note.Note('D4')
        sp1 = spanner.Slur(n1, n2)
        ss = n1.getSpannerSites()
        self.assertEqual(ss, [sp1])

        # test same for inherited classes and multiple sites, in order...
        sp2 = dynamics.Crescendo(n2, n1)
        # can return in arbitrary order esp. if speed is fast... 
        # TODO: use Ordered Dict.
        self.assertEqual(set(n2.getSpannerSites()), set([sp1, sp2]))

        #Optionally a class name or list of class names can be
        #specified and only Spanners of that class will be returned

        sp3 = dynamics.Diminuendo(n1, n2)
        self.assertEqual(n2.getSpannerSites('Diminuendo'), [sp3])

        # A larger class name can be used to get all subclasses:

        self.assertEqual(set(n2.getSpannerSites('DynamicWedge')), set([sp2, sp3]))
        self.assertEqual(set(n2.getSpannerSites(['Slur', 'Diminuendo'])), set([sp1, sp3]))

        #The order spanners are returned is generally the order that they were
        #added, but that is not guaranteed, so for safety sake, use set comparisons:

        self.assertEqual(set(n2.getSpannerSites(['Slur','Diminuendo'])), set([sp3, sp1]))


    def testContextSitesA(self):
        from music21 import corpus
        self.maxDiff = None
        c = corpus.parse('bwv66.6')
        c.id = 'bach'
        n = c[2][4][2]
        self.assertEqual(repr(n), '<music21.note.Note G#>')
        siteList = []
        for y in n.contextSites():
            siteList.append(repr(y))
        self.assertEqual(siteList, ["(<music21.stream.Measure 3 offset=9.0>, 0.5, 'elementsFirst')",
                                    "(<music21.stream.Part Alto>, 9.5, 'flatten')", 
                                    "(<music21.stream.Score bach>, 9.5, 'elementsOnly')"])

        m = c[2][4]
        self.assertEqual(repr(m), '<music21.stream.Measure 3 offset=9.0>')

        siteList = []      
        for y in m.contextSites():
            siteList.append(repr(y))
        self.assertEqual(siteList, ["(<music21.stream.Measure 3 offset=9.0>, 0.0, 'elementsFirst')",
                                    "(<music21.stream.Part Alto>, 9.0, 'flatten')", 
                                    "(<music21.stream.Score bach>, 9.0, 'elementsOnly')"])

        m2 = copy.deepcopy(m)
        m2.number = 3333
        siteList = []   
        #environLocal.warn("#########################")   
        for y in m2.contextSites():
            siteList.append(repr(y))
        self.assertEqual(siteList, 
                         ["(<music21.stream.Measure 3333 offset=0.0>, 0.0, 'elementsFirst')",
                          "(<music21.stream.Part Alto>, 9.0, 'flatten')", 
                          "(<music21.stream.Score bach>, 9.0, 'elementsOnly')"])
        siteList = []
        c.parts.id = 'partStream' # to make it easier to see below, will be cached...
        ptemp = c.parts[1]
        m3 = ptemp.measure(3)
        self.assertIs(m, m3)
        for y in m3.contextSites():
            siteList.append(repr(y))
        
        self.assertEqual(siteList, 
                         ["(<music21.stream.Measure 3 offset=9.0>, 0.0, 'elementsFirst')", 
                          "(<music21.stream.Part Alto>, 9.0, 'flatten')", 
                          "(<music21.stream.Score partStream>, 9.0, 'elementsOnly')",
                          "(<music21.stream.Score bach>, 9.0, 'elementsOnly')"])

    def testContextSitesB(self):        
        from music21 import stream, note
        p1 = stream.Part()
        p1.id = 'p1'
        m1 = stream.Measure()
        m1.number = 1
        n = note.Note()
        m1.append(n)
        p1.append(m1)
        siteList = []
        for y in n.contextSites():
            siteList.append(repr(y[0]))
        self.assertEqual(siteList, ["<music21.stream.Measure 1 offset=0.0>",
                                    "<music21.stream.Part p1>"])
        p2 = stream.Part()
        p2.id = 'p2'
        m2 = stream.Measure()
        m2.number = 2
        m2.append(n)
        p2.append(m2)

        siteList = []
        for y in n.contextSites(priorityTarget=n.activeSite):
            siteList.append(repr(y[0]))
        self.assertEqual(siteList, ["<music21.stream.Measure 2 offset=0.0>",
                                    "<music21.stream.Part p2>",
                                    "<music21.stream.Measure 1 offset=0.0>",
                                    "<music21.stream.Part p1>"])

        siteList = []
        for y in n.contextSites(sortByCreationTime = True):
            siteList.append(repr(y[0]))
        self.assertEqual(siteList, ["<music21.stream.Measure 2 offset=0.0>",
                                    "<music21.stream.Part p2>",
                                    "<music21.stream.Measure 1 offset=0.0>",
                                    "<music21.stream.Part p1>"])

        siteList = []
        for y in n.contextSites(sortByCreationTime = 'reverse'):
            siteList.append(repr(y[0]))
        self.assertEqual(siteList, ["<music21.stream.Measure 1 offset=0.0>",
                                    "<music21.stream.Part p1>",
                                    "<music21.stream.Measure 2 offset=0.0>",
                                    "<music21.stream.Part p2>"])
        
    def testPreviousAfterDeepcopy(self):
        from music21 import stream, note
        e1 = note.Note('C')
        e2 = note.Note('D')
        s = stream.Stream()
        s.insert(0, e1)
        s.insert(1, e2)
        self.assertIs(e2.previous(), e1)
        self.assertIs(s[1].previous(), e1)
        t = copy.deepcopy(s)
        self.assertIs(t[1].previous(), t[0])

        e1 = note.Note('C')
        e2 = note.Note('D')
        
        v = stream.Part()
        m1 = stream.Measure()
        m1.number = 1
        m1.insert(0, e1)
        v.insert(0, m1)
        m2 = stream.Measure()
        m2.insert(0, e2)
        m2.number = 2
        v.append(m2)
        self.assertIs(e2.previous('Note'), e1)
        self.assertIs(v[1][0], e2)
        self.assertIs(v[1][0].previous('Note'), e1)

        w = v.transpose('M3') # same as deepcopy,
        # but more instructive in debugging since pitches change...
        #w = copy.deepcopy(v)
        ecopy1 = w[0][0]
        ecopy2 = w[1][0]
        prev = ecopy2.previous('Note')
        self.assertIs(prev, ecopy1)
        
        

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Music21Object, ElementWrapper]




#------------------------------------------------------------------------------
if __name__ == "__main__":
#     from music21 import note, stream
#     s = stream.Stream(id="hello")
#     n = note.Note()
#     s.insert(0, n)
#     print(id(s))
#     copy.deepcopy(n)
    mainTest(Test) #, runTest='testPreviousAfterDeepcopy')


#------------------------------------------------------------------------------
# eof
