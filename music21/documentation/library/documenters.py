# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         convertIPythonNotebooksToReST.py
# Purpose:      music21 documentation IPython notebook to ReST converter
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

import abc
import inspect
import types


class ObjectDocumenter(object):
    '''
    Abstract base class for object documenting classes.
    '''

    ### CLASS VARIABLES ###

    __metaclass__ = abc.ABCMeta

    ### INITIALIZER ###

    def __init__(self, referent):
        self._referent = referent

    ### SPECIAL METHODS ###

    def __call__(self):
        raise NotImplemented

    @abc.abstractmethod
    def __repr__(self):
        raise NotImplemented

    ### PRIVATE PROPERTIES ###

    @property
    def _packagesystemPath(self):
        return '.'.join((
            self.__class__.__module__,
            self.__class__.__name__,
            ))

    ### PUBLIC PROPERTIES ###

    @property
    def referent(self):
        return self._referent

    @abc.abstractproperty
    def referentPackagesystemPath(self):
        raise NotImplemented

    @abc.abstractproperty
    def rstAutodocDirectiveFormat(self):
        raise NotImplemented

    @property
    def rstCrossReferenceString(self):
        return ':{0}:`~{1}`'.format(
            self.sphinxCrossReferenceRole,
            self.referentPackagesystemPath,
            )

    @abc.abstractproperty
    def sphinxCrossReferenceRole(self):
        raise NotImplemented

    ### PUBLIC METHODS ###

    def makeHeading(self, text, heading_level):
        assert isinstance(text, (str, unicode)) and len(text)
        assert heading_level in (1, 2)
        heading_characters = ['=', '-']
        result = [text]
        result.append(heading_characters[heading_level - 1] * len(text))
        result.append('')
        return result


class FunctionDocumenter(ObjectDocumenter):
    '''
    A documenter for one function:

    ::

        >>> function = common.almostEquals
        >>> documenter = documentation.FunctionDocumenter(function)
        >>> documenter
        <music21.documentation.library.documenters.FunctionDocumenter: music21.common.almostEquals>

    ::

        >>> documenter.rstCrossReferenceString
        ':func:`~music21.common.almostEquals`'

    ::

        >>> for line in documenter.rstAutodocDirectiveFormat:
        ...     line
        ...
        '.. autofunction:: music21.common.almostEquals'
        ''

    '''

    ### INITIALIZER ###

    def __init__(self, referent):
        assert isinstance(referent, types.FunctionType)
        ObjectDocumenter.__init__(self, referent)

    ### SPECIAL METHODS ###

    def __repr__(self):
        return '<{0}: {1}>'.format(
            self._packagesystemPath,
            self.referentPackagesystemPath,
            )

    ### PUBLIC PROPERTIES ###

    @property
    def referentPackagesystemPath(self):
        return '.'.join((
            self.referent.__module__,
            self.referent.__name__,
            ))

    @property
    def rstAutodocDirectiveFormat(self):
        result = []
        result.append('.. autofunction:: {0}'.format(
            self.referentPackagesystemPath,
            ))
        result.append('')
        return result

    @property
    def sphinxCrossReferenceRole(self):
        return 'func'


class MemberDocumenter(ObjectDocumenter):
    '''
    Abstract base class for documenting class members.
    '''

    ### INITIALIZER ###

    def __init__(self, referent, memberName, definingClass):
        assert isinstance(definingClass, type)
        ObjectDocumenter.__init__(self, referent)
        self._memberName = memberName
        self._definingClass = definingClass

    ### SPECIAL METHODS ###

    def __call__(self):
        result = []
        result.extend(self.rstAutodocDirectiveFormat)
        return result

    def __repr__(self):
        referentPath = '.'.join((
            self.definingClass.__module__,
            self.definingClass.__name__,
            self.memberName,
            ))
        return '<{0}: {1}>'.format(
            self._packagesystemPath,
            referentPath,
            )

    ### PUBLIC PROPERTIES ###

    @property
    def definingClass(self):
        return self._definingClass

    @property
    def memberName(self):
        return self._memberName

    @property
    def referentPackagesystemPath(self):
        return '.'.join((
            self.definingClass.__module__,
            self.definingClass.__name__,
            self.memberName,
            ))


class MethodDocumenter(MemberDocumenter):
    '''
    A documenter for class methods:

    ::

        >>> method = key.KeySignature.transpose
        >>> documenter = documentation.MethodDocumenter(
        ...     method, 'transpose', key.KeySignature)
        >>> documenter
        <music21.documentation.library.documenters.MethodDocumenter: music21.key.KeySignature.transpose>

    ::

        >>> documenter.rstCrossReferenceString
        ':meth:`~music21.key.KeySignature.transpose`'

    ::

        >>> for line in documenter.rstAutodocDirectiveFormat:
        ...     line
        ...
        '.. automethod:: music21.key.KeySignature.transpose'
        ''
        
    '''

    ### PUBLIC PROPERTIES ###

    @property
    def rstAutodocDirectiveFormat(self):
        result = []
        result.append('.. automethod:: {0}'.format(
            self.referentPackagesystemPath,
            ))
        result.append('')
        return result

    @property
    def sphinxCrossReferenceRole(self):
        return 'meth'


class AttributeDocumenter(MemberDocumenter):
    '''
    A documenter for class attributes, both read/write and read-only:

    ::

        >>> attribute = key.KeySignature.mode
        >>> documenter = documentation.AttributeDocumenter(
        ...     attribute, 'mode', key.KeySignature)
        >>> documenter
        <music21.documentation.library.documenters.AttributeDocumenter: music21.key.KeySignature.mode>

    ::

        >>> documenter.rstCrossReferenceString
        ':attr:`~music21.key.KeySignature.mode`'

    ::

        >>> for line in documenter.rstAutodocDirectiveFormat:
        ...     line
        ...
        '.. autoattribute:: music21.key.KeySignature.mode'
        ''

    '''

    ### PUBLIC PROPERTIES ###

    @property
    def rstAutodocDirectiveFormat(self):
        result = []
        result.append('.. autoattribute:: {0}'.format(
            self.referentPackagesystemPath,
            ))
        result.append('')
        return result

    @property
    def sphinxCrossReferenceRole(self):
        return 'attr'


class ClassDocumenter(ObjectDocumenter):
    '''
    A documenter for one class:

    ::

        >>> klass = documentation.ClassDocumenter
        >>> documenter = documentation.ClassDocumenter(klass)
        >>> documenter
        <music21.documentation.library.documenters.ClassDocumenter: music21.documentation.library.documenters.ClassDocumenter>

    ::

        >>> documenter.rstCrossReferenceString
        ':class:`~music21.documentation.library.documenters.ClassDocumenter`'


    ::

        >>> for line in documenter.rstAutodocDirectiveFormat:
        ...     line
        ...
        '.. autoclass:: music21.documentation.library.documenters.ClassDocumenter'
        ''

    Generate the ReST lines by calling the documenter:

    ::

        >>> restructedText = documenter()

    '''

    ### CLASS VARIABLES ###

    _identityMap = {}

    ### INITIALIZER ###

    def __init__(self, referent):
        assert isinstance(referent, type)
        ObjectDocumenter.__init__(self, referent) 

        self._baseClasses = tuple(
            cls for cls in inspect.getmro(self.referent)[1:] \
            if cls.__module__.startswith('music21'))
        self._baseClassDocumenters = tuple(
            type(self).fromIdentityMap(cls) for cls in self.baseClasses)

        self._docAttr = getattr(self.referent, '_DOC_ATTR', {})
        self._docOrder = getattr(self.referent, '_DOC_ORDER', [])

        inheritedDocAttr = {}
        for baseClass in self.baseClasses:
            baseClassDocAttr = getattr(baseClass, '_DOC_ATTR', None)
            if baseClassDocAttr is not None:
                baseClassDocumenter = type(self).fromIdentityMap(baseClass)
                inheritedDocAttr[baseClassDocumenter] = baseClassDocAttr
        self._inheritedDocAttrMapping = inheritedDocAttr

        methods = []
        inheritedMethods = {}

        # Read/Write
        readwriteProperties = []
        inheritedReadwriteProperties = {}

        # Read-only
        readonlyProperties = []
        inheritedReadonlyProperties = {}

        attrs = inspect.classify_class_attrs(self.referent)
        for attr in attrs:

            # Ignore definitions derived directly from object
            if attr.defining_class is object:
                continue
            # Ignore private members ('_') and special members ('__')
            elif attr.name.startswith('_'):
                continue
            
            definingClass = attr.defining_class
            if attr.kind in ('class method', 'method', 'static method'):
                documenterClass = MethodDocumenter
                localMembers = methods
                inheritedMembers = inheritedMethods
            elif attr.kind in ('property',) and attr.object.fset is not None:
                documenterClass = AttributeDocumenter
                localMembers = readwriteProperties
                inheritedMembers = inheritedReadwriteProperties
            elif attr.kind in ('property',) and attr.object.fset is None:
                documenterClass = AttributeDocumenter
                localMembers = readonlyProperties
                inheritedMembers = inheritedReadonlyProperties
            else:
                continue

            documenter = documenterClass(
                    attr.object,
                    attr.name,
                    definingClass,
                    )
            if definingClass is self.referent:
                localMembers.append(documenter)
            else:
                definingClassDocumenter = type(self).fromIdentityMap(definingClass)
                if definingClassDocumenter not in inheritedMembers:
                    inheritedMembers[definingClassDocumenter] = []
                inheritedMembers[definingClassDocumenter].append(documenter)
            
        keyLambda = lambda x: x.memberName
        methods.sort(key=keyLambda)
        readonlyProperties.sort(key=keyLambda)
        readwriteProperties.sort(key=keyLambda)
        for documenters in inheritedMethods.itervalues():
            documenters.sort(key=keyLambda)
        for documenters in inheritedReadonlyProperties.itervalues():
            documenters.sort(key=keyLambda)
        for documenters in inheritedReadwriteProperties.itervalues():
            documenters.sort(key=keyLambda) 

        self._methods = methods
        self._readonlyProperties = readonlyProperties
        self._readwriteProperties = readwriteProperties
        self._inheritedDocAttrMapping = inheritedDocAttr
        self._inheritedMethodsMapping = inheritedMethods
        self._inheritedReadonlyPropertiesMapping = inheritedReadonlyProperties
        self._inheritedReadwritePropertiesMapping = inheritedReadwriteProperties

        if self.referent not in self._identityMap:
            self._identityMap[self.referent] = self 
 
    ### SPECIAL METHODS ###

    def __call__(self):
        result = []
        result.extend(self.makeHeading(self.referent.__name__, 2))
        result.extend(self.rstAutodocDirectiveFormat)
        result.extend(self.rstBasesFormat)
        result.extend(self.rstReadonlyPropertiesFormat)
        result.extend(self.rstInheritedReadonlyPropertiesFormat)
        result.extend(self.rstReadwritePropertiesFormat)
        result.extend(self.rstInheritedReadwritePropertiesFormat)
        result.extend(self.rstMethodsFormat)
        result.extend(self.rstInheritedMethodsFormat)
        return result

    def __hash__(self):
        return hash((type(self), self.referent))

    def __repr__(self):
        referentPath = '.'.join((
            self.referent.__module__,
            self.referent.__name__,
            ))
        return '<{0}: {1}>'.format(
            self._packagesystemPath,
            referentPath,
            )

    ### PRIVATE METHODS ###

    def _formatInheritedMembersMapping(self, mapping, banner):
        result = []
        if not mapping:
            return result
        for classDocumenter in self.baseClassDocumenters:
            if classDocumenter not in mapping:
                continue
            result.append(banner.format(classDocumenter.rstCrossReferenceString))
            result.append('')
            memberDocumenters = mapping[classDocumenter]
            for memberDocumenter in memberDocumenters: 
                result.append('- {0}'.format(
                    memberDocumenter.rstCrossReferenceString))
            result.append('')    
        return result

    ### PUBLIC METHODS ###

    @classmethod
    def fromIdentityMap(cls, referent):
        if referent in cls._identityMap:
            return cls._identityMap[referent]
        return cls(referent)

    ### PUBLIC PROPERTIES ###

    @property
    def baseClasses(self):
        return self._baseClasses

    @property
    def baseClassDocumenters(self):
        return self._baseClassDocumenters

    @property
    def docAttr(self):
        '''
        The music21 _DOC_ATTR definition for a documented class:

        ::

            >>> klass = stream.Stream
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for key in sorted(documenter.docAttr.iterkeys()):
            ...     key
            ...
            'autoSort'
            'definesExplicitPageBreaks'
            'definesExplicitSystemBreaks'
            'flattenedRepresentationOf'
            'isFlat'
            'isSorted'

        '''
        return self._docAttr

    @property
    def docOrder(self):
        '''
        The music21 _DOC_ORDER definition for a documented class:

        ::

            >>> klass = stream.Stream
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for name in documenter.docOrder:
            ...     name
            ...
            'append'
            'insert'
            'insertAndShift'
            'notes'
            'pitches'
            'transpose'
            'augmentOrDiminish'
            'scaleOffsets'
            'scaleDurations'

        '''
        return self._docOrder

    @property
    def inheritedDocAttrMapping(self):
        '''
        A mapping of parent class documenters and doc-attr attribute dicts
        for a documented class:

        ::

            >>> klass = stream.Measure 
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> mapping = documenter.inheritedDocAttrMapping
            >>> sortBy = lambda x: x.referentPackagesystemPath
            >>> for classDocumenter in sorted(mapping, key=sortBy):
            ...     classDocumenter
            ...
            <music21.documentation.library.documenters.ClassDocumenter: music21.base.Music21Object>
            <music21.documentation.library.documenters.ClassDocumenter: music21.stream.Stream>

        '''
        return self._inheritedDocAttrMapping

    @property
    def inheritedReadonlyPropertiesMapping(self):
        '''
        A mapping of parent class documenters and inherited read-only
        properties for a documented class:

        ::

            >>> klass = stream.Measure
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> mapping = documenter.inheritedReadonlyPropertiesMapping
            >>> sortBy = lambda x: x.referentPackagesystemPath
            >>> for classDocumenter in sorted(mapping, key=sortBy):
            ...     print '{0}:'.format(classDocumenter.referentPackagesystemPath)
            ...     for attributeDocumenter in mapping[classDocumenter][:10]:
            ...         print '- {0}'.format(attributeDocumenter.referentPackagesystemPath)
            ...
            music21.base.Music21Object:
            - music21.base.Music21Object.classes
            - music21.base.Music21Object.derivationHierarchy
            - music21.base.Music21Object.fullyQualifiedClasses
            - music21.base.Music21Object.isGrace
            - music21.base.Music21Object.measureNumber
            music21.stream.Stream:
            - music21.stream.Stream.beat
            - music21.stream.Stream.beatDuration
            - music21.stream.Stream.beatStr
            - music21.stream.Stream.beatStrength
            - music21.stream.Stream.derivationChain
            - music21.stream.Stream.flat
            - music21.stream.Stream.highestOffset
            - music21.stream.Stream.highestTime
            - music21.stream.Stream.isGapless
            - music21.stream.Stream.lowestOffset

        '''

        return self._inheritedReadonlyPropertiesMapping

    @property
    def inheritedMethodsMapping(self):
        '''
        A mapping of parent class documenters and inherited attributes for a
        documented class:

        ::

            >>> klass = stream.Measure
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> mapping = documenter.inheritedMethodsMapping
            >>> sortBy = lambda x: x.referentPackagesystemPath
            >>> for classDocumenter in sorted(mapping, key=sortBy):
            ...     print '{0}:'.format(classDocumenter.referentPackagesystemPath)
            ...     for attributeDocumenter in mapping[classDocumenter][:10]:
            ...         print '- {0}'.format(attributeDocumenter.referentPackagesystemPath)
            ...
            music21.base.Music21Object:
            - music21.base.Music21Object.addContext
            - music21.base.Music21Object.addLocation
            - music21.base.Music21Object.findAttributeInHierarchy
            - music21.base.Music21Object.getAllContextsByClass
            - music21.base.Music21Object.getContextAttr
            - music21.base.Music21Object.getContextByClass
            - music21.base.Music21Object.getOffsetBySite
            - music21.base.Music21Object.getSiteIds
            - music21.base.Music21Object.getSites
            - music21.base.Music21Object.getSpannerSites
            music21.stream.Stream:
            - music21.stream.Stream.activateVariants
            - music21.stream.Stream.addGroupForElements
            - music21.stream.Stream.allPlayingWhileSounding
            - music21.stream.Stream.analyze
            - music21.stream.Stream.append
            - music21.stream.Stream.attachIntervalsBetweenStreams
            - music21.stream.Stream.attachMelodicIntervals
            - music21.stream.Stream.attributeCount
            - music21.stream.Stream.augmentOrDiminish
            - music21.stream.Stream.beatAndMeasureFromOffset

        '''
        return self._inheritedMethodsMapping

    @property
    def inheritedReadwritePropertiesMapping(self):
        '''
        A mapping of parent class documenters and inherited read/write
        properties for a documented class:

        ::

            >>> klass = stream.Measure
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> mapping = documenter.inheritedReadwritePropertiesMapping
            >>> sortBy = lambda x: x.referentPackagesystemPath
            >>> for classDocumenter in sorted(mapping, key=sortBy):
            ...     print '{0}:'.format(classDocumenter.referentPackagesystemPath)
            ...     for attributeDocumenter in mapping[classDocumenter][:10]:
            ...         print '- {0}'.format(attributeDocumenter.referentPackagesystemPath)
            ...
            music21.base.Music21Object:
            - music21.base.Music21Object.activeSite
            - music21.base.Music21Object.offset
            - music21.base.Music21Object.priority
            music21.stream.Stream:
            - music21.stream.Stream.atSoundingPitch
            - music21.stream.Stream.derivationMethod
            - music21.stream.Stream.derivesFrom
            - music21.stream.Stream.duration
            - music21.stream.Stream.elements
            - music21.stream.Stream.finalBarline
            - music21.stream.Stream.metadata
            - music21.stream.Stream.seconds

        '''
        return self._inheritedReadwritePropertiesMapping

    @property
    def methods(self):
        '''
        The method documenters for a documented class:

        ::

            >>> klass = stream.Stream
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for method in documenter.methods[:10]:
            ...     method
            ... 
            <music21.documentation.library.documenters.MethodDocumenter: music21.stream.Stream.activateVariants>
            <music21.documentation.library.documenters.MethodDocumenter: music21.stream.Stream.addGroupForElements>
            <music21.documentation.library.documenters.MethodDocumenter: music21.stream.Stream.allPlayingWhileSounding>
            <music21.documentation.library.documenters.MethodDocumenter: music21.stream.Stream.analyze>
            <music21.documentation.library.documenters.MethodDocumenter: music21.stream.Stream.append>
            <music21.documentation.library.documenters.MethodDocumenter: music21.stream.Stream.attachIntervalsBetweenStreams>
            <music21.documentation.library.documenters.MethodDocumenter: music21.stream.Stream.attachMelodicIntervals>
            <music21.documentation.library.documenters.MethodDocumenter: music21.stream.Stream.attributeCount>
            <music21.documentation.library.documenters.MethodDocumenter: music21.stream.Stream.augmentOrDiminish>
            <music21.documentation.library.documenters.MethodDocumenter: music21.stream.Stream.beatAndMeasureFromOffset>

        ''' 
        return self._methods

    @property
    def readonlyProperties(self):
        '''
        The read-only property documenters for a documented class:

        ::

            >>> klass = stream.Stream
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for attr in documenter.readonlyProperties:
            ...     attr
            ...
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.beat>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.beatDuration>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.beatStr>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.beatStrength>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.derivationChain>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.flat>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.highestOffset>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.highestTime>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.isGapless>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.lowestOffset>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.notes>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.notesAndRests>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.offsetMap>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.pitches>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.rootDerivation>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.secondsMap>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.semiFlat>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.sorted>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.spannerBundle>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.spanners>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.variants>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.voices>

        '''
        return self._readonlyProperties

    @property
    def readwriteProperties(self):
        '''
        The read/write property documenters for a documented class:

        ::

            >>> klass = stream.Stream
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for prop in documenter.readwriteProperties:
            ...     prop
            ...
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.atSoundingPitch>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.derivationMethod>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.derivesFrom>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.duration>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.elements>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.finalBarline>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.metadata>
            <music21.documentation.library.documenters.AttributeDocumenter: music21.stream.Stream.seconds>

        '''
        return self._readwriteProperties

    @property
    def referentPackagesystemPath(self):
        return '.'.join((
            self.referent.__module__,
            self.referent.__name__,
            ))

    @property
    def rstAutodocDirectiveFormat(self):
        result = []
        result.append('.. autoclass:: {0}'.format(
            self.referentPackagesystemPath,
            ))
        result.append('')
        return result

    @property
    def rstBasesFormat(self):
        '''
        The ReST format for the bases from which the documented class
        inherits:

        ::

            >>> klass = documentation.ClassDocumenter
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for line in documenter.rstBasesFormat:
            ...     line
            ...
            'Inherits from:'
            ''
            '- :class:`~music21.documentation.library.documenters.ObjectDocumenter`'
            ''

        '''
        result = []
        if self.baseClasses:
            result.append('Inherits from:')
            result.append('')
            for class_documenter in self.baseClassDocumenters:
                result.append('- {0}'.format(
                    class_documenter.rstCrossReferenceString))
            result.append('')
        return result

    @property
    def rstInheritedDocAttrFormat(self):
        pass

    @property
    def rstInheritedMethodsFormat(self):
        '''
        The ReST format for inherited methods:

        ::

            >>> klass = documentation.MethodDocumenter
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for line in documenter.rstInheritedMethodsFormat:
            ...     line
            ...
            'Methods inherited from :class:`~music21.documentation.library.documenters.ObjectDocumenter`:'
            ''
            '- :meth:`~music21.documentation.library.documenters.ObjectDocumenter.makeHeading`'
            ''

        '''
        mapping = self.inheritedMethodsMapping
        banner = 'Methods inherited from {0}:'
        return self._formatInheritedMembersMapping(mapping, banner)


    @property
    def rstInheritedReadonlyPropertiesFormat(self):
        '''
        The ReST format for inherited methods:

        ::

            >>> klass = documentation.MethodDocumenter
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for line in documenter.rstInheritedReadonlyPropertiesFormat:
            ...     line
            ...
            'Read-only properties inherited from :class:`~music21.documentation.library.documenters.MemberDocumenter`:'
            ''
            '- :attr:`~music21.documentation.library.documenters.MemberDocumenter.definingClass`'
            '- :attr:`~music21.documentation.library.documenters.MemberDocumenter.memberName`'
            '- :attr:`~music21.documentation.library.documenters.MemberDocumenter.referentPackagesystemPath`'
            ''
            'Read-only properties inherited from :class:`~music21.documentation.library.documenters.ObjectDocumenter`:'
            ''
            '- :attr:`~music21.documentation.library.documenters.ObjectDocumenter.referent`'
            '- :attr:`~music21.documentation.library.documenters.ObjectDocumenter.rstCrossReferenceString`'
            ''

        '''
        mapping = self.inheritedReadonlyPropertiesMapping
        banner = 'Read-only properties inherited from {0}:'
        return self._formatInheritedMembersMapping(mapping, banner)

    @property
    def rstInheritedReadwritePropertiesFormat(self):
        '''
        The ReST format for inherited methods:

        ::

            >>> klass = documentation.MethodDocumenter
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for line in documenter.rstInheritedReadwritePropertiesFormat:
            ...     line
            ...

        '''
        mapping = self.inheritedReadwritePropertiesMapping
        banner = 'Read/write properties inherited from {0}:'
        return self._formatInheritedMembersMapping(mapping, banner)

    @property
    def rstMethodsFormat(self):
        '''
        The ReST format for the documented class's methods:

        ::

            >>> klass = documentation.ClassDocumenter
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for line in documenter.rstMethodsFormat:
            ...     line
            ...
            ':class:`~music21.documentation.library.documenters.ClassDocumenter` *methods*'
            ''
            '.. automethod:: music21.documentation.library.documenters.ClassDocumenter.fromIdentityMap'
            ''

        '''
        result = []
        if self.methods:
            result.append('{0} *methods*'.format(
                self.rstCrossReferenceString))
            result.append('')
            for documenter in self.methods: 
                result.extend(documenter())
            if result[-1] != '':
                result.append('')
        return result

    @property
    def rstReadonlyPropertiesFormat(self):
        '''
        The ReST format for the documented class's read-only properties:

        ::

            >>> klass = documentation.ClassDocumenter
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for line in documenter.rstReadonlyPropertiesFormat:
            ...     line
            ...
            ':class:`~music21.documentation.library.documenters.ClassDocumenter` *read-only properties*'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.baseClassDocumenters'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.baseClasses'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.docAttr'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.docOrder'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.inheritedDocAttrMapping'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.inheritedMethodsMapping'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.inheritedReadonlyPropertiesMapping'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.inheritedReadwritePropertiesMapping'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.methods'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.readonlyProperties'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.readwriteProperties'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.referentPackagesystemPath'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.rstAutodocDirectiveFormat'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.rstBasesFormat'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.rstInheritedDocAttrFormat'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.rstInheritedMethodsFormat'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.rstInheritedReadonlyPropertiesFormat'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.rstInheritedReadwritePropertiesFormat'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.rstMethodsFormat'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.rstReadonlyPropertiesFormat'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.rstReadwritePropertiesFormat'
            ''
            '.. autoattribute:: music21.documentation.library.documenters.ClassDocumenter.sphinxCrossReferenceRole'
            ''

        '''
        result = []
        if self.readonlyProperties:
            result.append('{0} *read-only properties*'.format(
                self.rstCrossReferenceString))
            result.append('')
            for documenter in self.readonlyProperties:
                result.extend(documenter())
            if result[-1] != '':
                result.append('')
        return result

    @property
    def rstReadwritePropertiesFormat(self):
        '''
        The ReST format for the documented class's read-only properties:

        ::

            >>> klass = documentation.ClassDocumenter
            >>> documenter = documentation.ClassDocumenter(klass)
            >>> for line in documenter.rstReadwritePropertiesFormat:
            ...     line
            ...

        '''
        result = []
        if self.readwriteProperties:
            result.append('{0} *read/write properties*'.format(
                self.rstCrossReferenceString))
            result.append('')
            for documenter in self.readwriteProperties:
                result.extend(documenter())
            if result[-1] != '':
                result.append('')
        return result

    @property
    def sphinxCrossReferenceRole(self):
        return 'class'


class ModuleDocumenter(ObjectDocumenter):
    '''
    A documenter for one module:

    ::

        >>> module = key
        >>> documenter = documentation.ModuleDocumenter(module)
        >>> documenter
        <music21.documentation.library.documenters.ModuleDocumenter: music21.key>

    ::

        >>> for reference, referent in sorted(documenter.namesMapping.iteritems()):
        ...     print reference, referent
        ...
        Key <music21.documentation.library.documenters.ClassDocumenter: music21.key.Key>
        KeySignature <music21.documentation.library.documenters.ClassDocumenter: music21.key.KeySignature>
        Test <music21.documentation.library.documenters.ClassDocumenter: music21.key.Test>
        convertKeyStringToMusic21KeyString <music21.documentation.library.documenters.FunctionDocumenter: music21.key.convertKeyStringToMusic21KeyString>
        pitchToSharps <music21.documentation.library.documenters.FunctionDocumenter: music21.key.pitchToSharps>
        sharpsToPitch <music21.documentation.library.documenters.FunctionDocumenter: music21.key.sharpsToPitch>

    ::

        >>> documenter.rstCrossReferenceString
        ':mod:`~music21.key`'

    ::

        >>> for line in documenter.rstAutodocDirectiveFormat:
        ...     line
        ...
        '.. automodule:: music21.key'
        ''

    '''

    ### CLASS VARIABLES ###

    _ignored_classes = frozenset((
        BaseException,
        ))

    ### INITIALIZER ###
    
    def __init__(self, referent): 
        assert isinstance(referent, types.ModuleType)
        ObjectDocumenter.__init__(self, referent)
        namesMapping = self._examineModule()
        self._namesMapping = namesMapping
        self._memberOrder = tuple(getattr(self.referent, '_DOC_ORDER')) or ()

    ### SPECIAL METHODS ###

    def __repr__(self):
        return '<{0}: {1}>'.format(
            self._packagesystemPath,
            self.referentPackagesystemPath,
            )

    ### PRIVATE METHODS ###

    def _examineModule(self):
        namesMapping = {}
        for name in dir(self.referent):
            named = getattr(self.referent, name)
            if isinstance(named, (type, types.ClassType)):
                if set(inspect.getmro(named)).intersection(
                    self._ignored_classes):
                    continue
                if named.__module__ != self.referent.__name__:
                    continue
                namesMapping[name] = ClassDocumenter(named)
            elif isinstance(named, types.FunctionType):
                if named.__module__ != self.referent.__name__:
                    continue
                namesMapping[name] = FunctionDocumenter(named)
        return namesMapping

    ### PUBLIC PROPERTIES ###

    @property
    def namesMapping(self):
        return self._namesMapping

    @property
    def memberOrder(self):
        return self._memberOrder

    @property
    def referentPackagesystemPath(self):
        if isinstance(self.referent.__name__, tuple):
            return self.referent.__name__[0],
        return self.referent.__name__

    @property
    def rstAutodocDirectiveFormat(self):
        result = []
        result.append('.. automodule:: {0}'.format(
            self.referentPackagesystemPath,
            ))
        result.append('')
        return result

    @property
    def sphinxCrossReferenceRole(self):
        return 'mod'
    

class CorpusDocumenter(object):
    '''A documenter for music21's corpus.'''


if __name__ == '__main__':
    import music21
    music21.mainTest()
