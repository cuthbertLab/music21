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


class FunctionDocumenter(ObjectDocumenter):
    '''
    A documenter for one function:

    ::

        >>> function = common.almostEquals
        >>> documenter = documentation.documenters.FunctionDocumenter(function)
        >>> documenter
        <music21.documentation.documenters.FunctionDocumenter: music21.common.almostEquals>

    '''

    ### INITIALIZER ###

    def __init__(self, referent):
        assert isinstance(referent, types.FunctionType)
        ObjectDocumenter.__init__(self, referent)

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


class MemberDocumenter(ObjectDocumenter):
    '''
    Abstract base class for documenting class members.
    '''

    ### INITIALIZER ###

    def __init__(self, referent, name, definingClass):
        assert isinstance(definingClass, type)
        ObjectDocumenter.__init__(self, referent)
        self._name = name
        self._definingClass = definingClass

    ### SPECIAL METHODS ###

    def __repr__(self):
        definingClassPath = '.'.join((
            self.definingClass.__module__,
            self.definingClass.__name__,
            ))
        referentPath = ':'.join((
            definingClassPath,
            self.name,
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
    def name(self):
        return self._name


class MethodDocumenter(MemberDocumenter):
    '''
    A documenter for class methods.
    '''
    pass


class PropertyDocumenter(MemberDocumenter):
    '''
    A documenter for (read/write) class properties.
    '''
    pass


class AttributeDocumenter(MemberDocumenter):
    '''
    A documenter for (read-only) class attributes.
    '''
    pass


class ClassDocumenter(ObjectDocumenter):
    '''
    A documenter for one class:

    ::

        >>> klass = stream.Stream
        >>> documenter = documentation.documenters.ClassDocumenter(klass)
        >>> documenter
        <music21.documentation.documenters.ClassDocumenter: music21.stream.Stream>

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
                documenterClass = PropertyDocumenter
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
            
            keyLambda = lambda x: x.name

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
        KeyException <music21.documentation.documenters.ClassDocumenter: music21.key.KeyException>
        KeySignature <music21.documentation.documenters.ClassDocumenter: music21.key.KeySignature>
        KeySignatureException <music21.documentation.documenters.ClassDocumenter: music21.key.KeySignatureException>
        Test <music21.documentation.documenters.ClassDocumenter: music21.key.Test>
        convertKeyStringToMusic21KeyString <music21.documentation.documenters.FunctionDocumenter: music21.key.convertKeyStringToMusic21KeyString>
        pitchToSharps <music21.documentation.documenters.FunctionDocumenter: music21.key.pitchToSharps>
        sharpsToPitch <music21.documentation.documenters.FunctionDocumenter: music21.key.sharpsToPitch>

    '''

    ### INITIALIZER ###
    
    def __init__(self, referent): 
        assert isinstance(referent, types.ModuleType)
        ObjectDocumenter.__init__(self, referent)
        namesMapping = self._examineModule()
        self._namesMapping = namesMapping
        self._order = getattr(self.referent, '_DOC_ORDER') or []

    ### SPECIAL METHODS ###

    def __repr__(self):
        return '<{0}: {1}>'.format(
            self._packagesystemPath,
            self.referent.__name__,
            )

    ### PRIVATE METHODS ###

    def _examineModule(self):
        namesMapping = {}
        for name in dir(self.referent):
            named = getattr(self.referent, name)
            if isinstance(named, type):
                namesMapping[name] = ClassDocumenter(named)
            elif isinstance(named, types.FunctionType):
                namesMapping[name] = FunctionDocumenter(named)
        return namesMapping

    ### READ-ONLY PUBLIC PROPERTIES ###

    @property
    def namesMapping(self):
        return self._namesMapping


class CorpusDocumenter(object):
    '''A documenter for music21's corpus.'''


if __name__ == '__main__':
    import music21
    music21.mainTest()
