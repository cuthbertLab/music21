# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         convertIPythonNotebooksToReST.py
# Purpose:      music21 documentation IPython notebook to ReST converter
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
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

    @abc.abstractmethod
    def __repr__(self):
        raise NotImplemented

    ### READ-ONLY PRIVATE PROPERTIES ###

    @property
    def _packagesystemPath(self):
        return '.'.join((
            self.__class__.__module__,
            self.__class__.__name__,
            ))

    ### READ-ONLY PUBLIC PROPERTIES ###

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


class FunctionDocumenter(ObjectDocumenter):
    '''
    A documenter for one function:

    ::

        >>> function = common.almostEquals
        >>> documenter = documentation.documenters.FunctionDocumenter(function)
        >>> documenter
        <music21.documentation.documenters.FunctionDocumenter: music21.common.almostEquals>

    ::

        >>> documenter.rstCrossReferenceString
        ':func:`~music21.common.almostEquals`'

    ::

        >>> for line in documenter.rstAutodocDirectiveFormat:
        ...     line
        ...
        '.. autofunction:: music21.common.almostEquals'

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

    ### READ-ONLY PUBLIC PROPERTIES ###

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

    ### READ-ONLY PUBLIC PROPERTIES ###

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
        >>> documenter = documentation.documenters.MethodDocumenter(
        ...     method, 'transpose', key.KeySignature)
        >>> documenter
        <music21.documentation.documenters.MethodDocumenter: music21.key.KeySignature.transpose>

    ::

        >>> documenter.rstCrossReferenceString
        ':meth:`~music21.key.KeySignature.transpose`'

    ::

        >>> for line in documenter.rstAutodocDirectiveFormat:
        ...     line
        ...
        '.. automethod:: music21.key.KeySignature.transpose'
        
    '''

    ### READ-ONLY PUBLIC PROPERTIES ###

    @property
    def rstAutodocDirectiveFormat(self):
        result = []
        result.append('.. automethod:: {0}'.format(
            self.referentPackagesystemPath,
            ))
        return result

    @property
    def sphinxCrossReferenceRole(self):
        return 'meth'


class AttributeDocumenter(MemberDocumenter):
    '''
    A documenter for class attributes, both read/write and read-only:

    ::

        >>> attribute = key.KeySignature.mode
        >>> documenter = documentation.documenters.AttributeDocumenter(
        ...     attribute, 'mode', key.KeySignature)
        >>> documenter
        <music21.documentation.documenters.AttributeDocumenter: music21.key.KeySignature.mode>

    ::

        >>> documenter.rstCrossReferenceString
        ':attr:`~music21.key.KeySignature.mode`'

    ::

        >>> for line in documenter.rstAutodocDirectiveFormat:
        ...     line
        ...
        '.. autoattribute:: music21.key.KeySignature.mode'

    '''

    ### READ-ONLY PUBLIC PROPERTIES ###

    @property
    def rstAutodocDirectiveFormat(self):
        result = []
        result.append('.. autoattribute:: {0}'.format(
            self.referentPackagesystemPath,
            ))
        return result

    @property
    def sphinxCrossReferenceRole(self):
        return 'attr'


class ClassDocumenter(ObjectDocumenter):
    '''
    A documenter for one class:

    ::

        >>> klass = stream.Stream
        >>> documenter = documentation.documenters.ClassDocumenter(klass)
        >>> documenter
        <music21.documentation.documenters.ClassDocumenter: music21.stream.Stream>

    ::

        >>> documenter.rstCrossReferenceString
        ':class:`~music21.stream.Stream`'

    ::

        >>> for line in documenter.rstAutodocDirectiveFormat:
        ...     line
        ...
        '.. autoclass:: music21.stream.Stream'

    '''

    ### INITIALIZER ###

    def __init__(self, referent):
        assert isinstance(referent, type)
        ObjectDocumenter.__init__(self, referent) 

        self._docAttr = getattr(self.referent, '_DOC_ATTR', {})
        self._docOrder = getattr(self.referent, '_DOC_ORDER', [])

        methods = []
        inheritedMethods = {}

        # Read/Write
        properties = []
        inheritedProperties = {}

        # Read-only
        attributes = []
        inheritedAttributes = {}

        attrs = inspect.classify_class_attrs(self.referent)
        for attr in attrs:
            # Ignore definitions derived directly from object
            if attr.defining_class is object:
                continue
            # Ignore private members ('_') and special members ('__')
            elif attr.name.startswith('_'):
                continue
            
            defining_class = attr.defining_class
            if attr.kind in ('class method', 'method'):
                documenterClass = MethodDocumenter
                localMembers = methods
                inheritedMembers = inheritedMethods
            elif attr.kind in ('property',) and attr.object.fset is not None:
                documenterClass = AttributeDocumenter
                localMembers = properties
                inheritedMembers = inheritedProperties
            elif attr.kind in ('property',) and attr.object.fset is None:
                documenterClass = AttributeDocumenter
                localMembers = attributes
                inheritedMembers = inheritedAttributes
            else:
                continue

            documenter = documenterClass(
                    attr.object,
                    attr.name,
                    attr.defining_class,
                    )
            if defining_class is self.referent:
                localMembers.append(documenter)
            else:
                if defining_class not in inheritedMembers:
                    inheritedMembers[defining_class] = []
                inheritedMembers[defining_class].append(documenter)
            
            keyLambda = lambda x: x.memberName

            methods.sort(key=keyLambda)
            attributes.sort(key=keyLambda)
            properties.sort(key=keyLambda)
            for documenters in inheritedMethods.itervalues():
                documenters.sort(key=keyLambda)
            for documenters in inheritedAttributes.itervalues():
                documenters.sort(key=keyLambda)
            for documenters in inheritedProperties.itervalues():
                documenters.sort(key=keyLambda) 

            self._methods = methods
            self._attributes = attributes
            self._properties = properties
            self._inheritedMethodsMapping = inheritedMethods
            self._inheritedAttributeMapping = inheritedAttributes
            self._inheritedPropertieMapping = inheritedProperties

    ### SPECIAL METHODS ###

    def __repr__(self):
        referentPath = '.'.join((
            self.referent.__module__,
            self.referent.__name__,
            ))
        return '<{0}: {1}>'.format(
            self._packagesystemPath,
            referentPath,
            )

    ### READ-ONLY PUBLIC PROPERTIES ###

    @property
    def attributes(self):
        return self._attributes

    @property
    def docAttr(self):
        return self._docAttr

    @property
    def docOrder(self):
        return self._docOrder

    @property
    def inheritedAttributeMapping(self):
        return self._inheritedAttributeMapping

    @property
    def inheritedMethodsMapping(self):
        return self._inheritedMethodsMapping

    @property
    def inheritedPropertieMapping(self):
        return self._inheritedPropertieMapping

    @property
    def methods(self):
        return self._methods

    @property
    def properties(self):
        return self._properties

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
        return result

    @property
    def sphinxCrossReferenceRole(self):
        return 'class'


class ModuleDocumenter(ObjectDocumenter):
    '''
    A documenter for one module:

    ::

        >>> module = key
        >>> documenter = documentation.documenters.ModuleDocumenter(module)
        >>> documenter
        <music21.documentation.documenters.ModuleDocumenter: music21.key>

    ::

        >>> for reference, referent in sorted(documenter.namesMapping.iteritems()):
        ...     print reference, referent
        ...
        Key <music21.documentation.documenters.ClassDocumenter: music21.key.Key>
        KeySignature <music21.documentation.documenters.ClassDocumenter: music21.key.KeySignature>
        Test <music21.documentation.documenters.ClassDocumenter: music21.key.Test>
        convertKeyStringToMusic21KeyString <music21.documentation.documenters.FunctionDocumenter: music21.key.convertKeyStringToMusic21KeyString>
        pitchToSharps <music21.documentation.documenters.FunctionDocumenter: music21.key.pitchToSharps>
        sharpsToPitch <music21.documentation.documenters.FunctionDocumenter: music21.key.sharpsToPitch>

    ::

        >>> documenter.rstCrossReferenceString
        ':mod:`~music21.key`'

    ::

        >>> for line in documenter.rstAutodocDirectiveFormat:
        ...     line
        ...
        '.. automodule:: music21.key'

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
            if isinstance(named, type):
                if set(inspect.getmro(named)).intersection(
                    self._ignored_classes):
                    continue
                namesMapping[name] = ClassDocumenter(named)
            elif isinstance(named, types.FunctionType):
                namesMapping[name] = FunctionDocumenter(named)
        return namesMapping

    ### READ-ONLY PUBLIC PROPERTIES ###

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
        return result

    @property
    def sphinxCrossReferenceRole(self):
        return 'mod'
    

class CorpusDocumenter(object):
    '''A documenter for music21's corpus.'''


if __name__ == '__main__':
    import music21
    music21.mainTest()
