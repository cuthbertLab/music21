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
        self._docstring = self.referent.__doc__ or ''

    ### READ-ONLY PUBLIC PROPERTIES ###

    @property
    def docstring(self):
        return self._docstring

    @property
    def referent(self):
        return self._referent


class FunctionDocumenter(ObjectDocumenter):
    '''
    A documenter for one function:
    '''

    ### INITIALIZER ###

    def __init__(self, referent):
        assert isinstance(referent, types.FunctionType)
        ObjectDocumenter.__init__(self, referent)


class MemberDocumenter(ObjectDocumenter):
    '''
    Abstract base class for documenting class members.
    '''
    pass


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
    A documenter for one class.
    '''

    ### INITIALIZER ###

    def __init__(self, referent):
        assert isinstance(referent, types.ClassType)
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
                documenter = MethodDocumenter(attr.object)
                localMembers = methods
                inheritedMembers = inheritedMethods
            elif attr.kind in ('property',) and attr.object.fset is not None:
                documenter = PropertyDocumenter(attr.object)
                localMembers = properties
                inheritedMembers = inheritedProperties
            elif attr.kind in ('property',) and attr.object.fset is None:
                documenter = AttributeDocumenter(attr.object)
                localMembers = attributes
                inheritedMembers = inheritedAttributes

            if defining_class is self.referent:
                localMembers.append(documenter)
            else:
                if defining_class not in inheritedMembers:
                    inheritedMembers[defining_class] = []
                inheritedMembers[defining_class].append(documenter)
            
            sortMethod = lambda x: x.referent.__name__
            methods.sort(sortMethod)
            attributes.sort(sortMethod)
            properties.sort(sortMethod)
            for documenters in inheritedMethods.itervalues():
                documenters.sort(sortMethod)
            for documenters in inheritedAttributes.itervalues():
                documenters.sort(sortMethod)
            for documenters in inheritedProperties.itervalues():
                documenters.sort(sortMethod) 

            self._methods = methods
            self._attributes = attributes
            self._properties = properties
            self._inheritedMethodsMapping = inheritedMethods
            self._inheritedAttributeMapping = inheritedAttributes
            self._inheritedPropertieMapping = inheritedProperties

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
    A documenter for one module.
    '''

    ### INITIALIZER ###
    
    def __init__(self, referent): 
        assert isinstance(referent, types.ModuleType)
        ObjectDocumenter.__init__(self, referent)
        namesMapping = self._examineModule()
        self._namesMapping = namesMapping
        self._order = getattr(self.referent, '_DOC_ORDER') or []

    ### PRIVATE METHODS

    def _examineModule(self):
        namesMapping = {}
        for name in dir(self.referent):
            named = self.referent.__dict__[name]
            if isinstance(named, types.ClassType):
                namesMapping[name] = ClassDocumenter(named)
            elif isinstance(named, types.FunctionType):
                namesMapping[name] = FunctionDocumenter(named)
        return namesMapping


class CorpusDocumenter(object):
    '''A documenter for music21's corpus.'''
