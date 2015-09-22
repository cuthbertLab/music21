# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         xmlnode.py
# Purpose:      Base class for SAX-based xml objects
#
# Authors:      Christopher Ariza
#               
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''An object base-class for creating and editing specialized XML structures 
as object representations.  Used by the musicxml converter, obviously, but
also by environment.py.
'''
import copy
import xml.dom.minidom
from music21.ext import six


# cannot import environment because environment reads/writes XML
import unittest
import re
from music21 import common
from music21 import exceptions21

_MOD = 'xmlnode.py'

_DOC_IGNORE_MODULE_OR_PACKAGE = True

# these module-level dictionaries cache used xml name conversion
# store converted names for reuse
_cacheNameFromXml = {}
_cacheNameToXml = {}
RE_CAPS = re.compile('[A-Z]+')


#-------------------------------------------------------------------------------
# xml base class


def fixBytes(value):
    if six.PY3 and isinstance(value, bytes):
        return value.decode(errors='replace')
    else:
        return value


#-------------------------------------------------------------------------------
class XMLNodeException(exceptions21.Music21Exception):
    pass

class XMLNode(object):
    def __init__(self):
        '''
        >>> a = xmlnode.XMLNode()
        >>> a.set('charData', 'test')
        '''
        self._attr = {} # store attributes in dictionary
        self._tag = None # name of tag
        self.charData = None # obtained by assignment from a Tag

        self._doctypeName = None
        self._doctypePublic = None
        self._doctypeSystem = None

        # dictionary of local Python name and possible names assumed
        # from music xml. used in get and set methods
        # specialize in subclassess
        self._crossReference = {'charData': ['characterdata', 'content']}


    def _getAttributes(self):
        '''Return a list of attribute names / value pairs
        
        >>> a = xmlnode.XMLNode()
        >>> a._getAttributes()
        []
        '''
        return list(self._attr.items())


    def _getComponents(self):
        '''
        Get all sub-components, in order. 
        These may be XMLNode subclasses, or may be simple entities. 
 
        Simple entities do not have attributes and are only used 
        as containers for character data. These entities are generally 
        not modeled as objects.
               
        The xmlnode.XMLNode._getComponents() method just returns
        an empty list.  Subclasses override this method.
        '''
        return []


    def loadAttrs(self, attrs):
        '''
        Given a SAX attrs object, load all attributes that are 
        named within this object's _attr dictionary. 
        '''
        for key in self._attr:
            value = attrs.get(key, "") # from SAX attrs object
            if value.strip() != '': # only modify if not nothing
                self._attr[key] = value        

    def hasAttrs(self):
        '''
        Returns bool depending on whether there are any attributes
        
        >>> a = xmlnode.XMLNode()
        >>> a.hasAttrs()
        False
        >>> a = musicxml.mxObjects.Pitch()
        >>> a.hasAttrs()
        False
        >>> a = musicxml.mxObjects.Beam()
        >>> a.hasAttrs()
        True
        '''
        if len(self._attr) > 0:
            return True
        return False

    #---------------------------------------------------------------------------
    def _convertNameCrossReference(self, name):
        '''
        Define mappings from expected MusicXML names and specially named attributes in object.
        Return a list of zero or 1 name
        
        Specialize in subclasses as needed, calling this base class to get
        general defaults.

        All options need to be lower case.

        
        >>> a = xmlnode.XMLNode()
        >>> a._convertNameCrossReference('characterData')
        'charData'
        '''
        nl = name.lower()
        for attr, options in self._crossReference.items():
            if name in options or nl in options:
                return attr
        return '' # return an empty string if no match

    def _convertNameFromXml(self, nameSrc):
        '''
        Given an xml attribute/entity 
        name, try to convert it to a Python 
        attribute name. If the Python name 
        is given, without and - dividers, 
        the proper name should be returned

        
        >>> a = xmlnode.XMLNode()
        >>> a._convertNameFromXml('char-data')
        'charData'
        '''
        try:
            return _cacheNameFromXml[nameSrc]
        except KeyError:
            pass

        parts = nameSrc.split('-')
        nameDst = [parts[0]] # create a list for storage
        if len(parts) > 1:
            for stub in parts[1:]:
                nameDst.append(stub[0].upper() + stub[1:])
        #print _MOD, 'new name', ''.join(nameDst)
        _cacheNameFromXml[nameSrc] = ''.join(nameDst)
        return _cacheNameFromXml[nameSrc]

    def _convertNameToXml(self, nameSrc):
        '''
        Given an a Python attribute name, try 
        to convert it to a XML name.
        If already an XML name, leave alone.

        
        >>> a = xmlnode.XMLNode()
        >>> a._convertNameToXml('charData')
        'char-data'
        '''
        try:
            return _cacheNameToXml[nameSrc]
        except KeyError:
            pass

        # this method is slightly faster than below
        nameDst = nameSrc[:] # copy
        caps = RE_CAPS.findall(nameSrc) # get a list of caps chars
        caps = set(caps) # strip redundancies
        if len(caps) > 0:
            for char in caps:
                nameDst = nameDst.replace(char, '-%s' % char.lower())

#         nameDst = []
#         for char in nameSrc:
#             if char.isupper():
#                 nameDst.append('-%s' % char.lower())
#             else:
#                 nameDst.append(char)

        _cacheNameToXml[nameSrc] = nameDst
        return _cacheNameToXml[nameSrc]


    #---------------------------------------------------------------------------
        
    def _publicAttributes(self):
        '''
        Get all public names from this object.
        Used in merging. 

        
        >>> a = xmlnode.XMLNode()
        >>> len(a._publicAttributes())
        2
        >>> print(a._publicAttributes())
        ['charData', 'tag']
    
        '''
        names = dir(self)
        post = []
        for name in names:
            if name.startswith('_'): 
                continue
            # do not want methods
            if callable(getattr(self, name)): 
                continue
            post.append(name)
        return post
        

    #---------------------------------------------------------------------------

    def _mergeSpecial(self, new, other, favorSelf):
        '''Provide handling of merging when given an object of a different class.

        Objects can define special merge operations for dealing with
        Lower or upper level objects. 

        Define in subclass
        '''
        pass

    def merge(self, other, favorSelf=True, returnDeepcopy=True):
        '''Given another similar or commonly used XMLNode object, combine
        all attributes and return a new object.

        
        >>> a = xmlnode.XMLNode()
        >>> a.set('charData', 'green')

        >>> b = xmlnode.XMLNode()
        >>> c = b.merge(a)
        >>> c.get('charData')
        'green'
        '''
        if not isinstance(other, XMLNode):
            raise XMLNodeException('can only merge with other nodes')

        if returnDeepcopy:
            new = copy.deepcopy(self)
        else:
            new = self

        localAttr = self._publicAttributes()
        otherAttr = other._publicAttributes()

        #print _MOD, 'attempting to merge', localAttr

        # if attrs are the same, these are instances of same class
        if localAttr == otherAttr:
            for i in range(len(localAttr)):
                # get() may be expensive; do once
                attrLocal = self.get(localAttr[i])
                attrOther = other.get(otherAttr[i])
                # neither are defined; do not need to tests
#                 if (attrLocal is None and attrOther is None):
#                     pass
                # local is defined
                if attrLocal is not None and attrOther is None:
                    pass # already set as this is a copy of self
                # other is defined
                elif attrLocal is None and attrOther is not None:
                    new.set(otherAttr[i], attrOther)
                # other is defined as an empty list
                # note that this may contain component objects
                elif attrLocal == [] and attrOther != []:
                    new.set(otherAttr[i], attrOther)

#                 elif (attrLocal is None and attrOther is None):
#                     if favorSelf:
#                         pass # already set as this ia copy
#                         # new.set(localAttr[i], self.get(localAttr[i]))
#                     else:
#                         new.set(otherAttr[i], otherAttr.get(otherAttr[i]))
        else:
            raise XMLNodeException('cannot merge: %s, %s' % (self, other))
            #print _MOD, 

        # call local merge special
        # may upate new
        self._mergeSpecial(new, other, favorSelf)
        return new


    #---------------------------------------------------------------------------
    # getters and setters, properties
    # uniform get/set methods are used so as to not have to distinguish between
    # attributes and contained entities

    def _getTag(self):
        return self._tag

    def _setTag(self, tag):
        self._tag = tag

    # define property
    tag = property(_getTag, _setTag)
        

    def set(self, name, value):
        '''
        Set an attribute, using either the name of the attribute, 
        a name that can be converter, or a direct attribute on the object. 
        '''
        #if name in self._attr:
        try:    
            junk = self._attr[name] # will raise error
            self._attr[name] = value
            return
        except KeyError:
            pass

        nameDst = self._convertNameToXml(name)
        #if nameDst in self._attr:
        try:
            junk = self._attr[nameDst] # will raise error
            self._attr[nameDst] = value
            return
        except KeyError:
            pass

        match = False
        candidates = []
        candidates.append(self._convertNameFromXml(name))
        candidates.append(self._convertNameCrossReference(name))
        # only add if it exists already
        # print _MOD, candidates

        for candidate in candidates:
            if hasattr(self, candidate):
                setattr(self, candidate, value)
                match = True
                break
        if not match:
            raise XMLNodeException('this object (%r) does not have a "%s" (or %s) attribute' % (self, name, candidates))
        
    def get(self, name):
        '''
        Get a data attribute from this XMLNode. If available in the 
        attribute dictionary, return this first. 
        
        If available as an object attribute, return this second. 
        '''
        #if name in self._attr:
        try:
            return fixBytes(self._attr[name])
        except KeyError:
            pass

        # try direct access
        try:
            return fixBytes(getattr(self, name))
        except AttributeError:
            pass

        # try conversions
        nameDst = self._convertNameToXml(name)
        #if nameDst in self._attr:
        try:
            return fixBytes(self._attr[nameDst])
        except KeyError:
            pass

        # if a python name it will not be altered
        match = False
        candidates = []
        candidates.append(self._convertNameFromXml(name))
        candidates.append(self._convertNameCrossReference(name))
        candidate = None
        for candidate in candidates:
            if hasattr(self, candidate):
                match = True
                return fixBytes(getattr(self, candidate))
        if not match:
            raise XMLNodeException('this object (%r) does not have a "%s" (or %r) attribute' % (self, name, candidate))
        

    def setDefaults(self):
        '''provide defaults for all necessary attributes at this level
        '''
        pass




    #---------------------------------------------------------------------------
    def __repr__(self):
        '''Provide a linear string representation of the element. 
        This is not XML, but a simple format for viewing contents of elements.'''
        msg = []
        # NOTE: this fails in python3:
        msg.append(u'<%s ' % fixBytes(self._tag))
        sub = []
        for name, value in sorted(list(self._getAttributes()), key=lambda x: x[0]):
            if value == None: 
                continue
            sub.append(u'%s=%s' % (fixBytes(name), fixBytes(value)))
        if self.charData not in ['', None]:
            sub.append(u'charData=%s' % fixBytes(self.charData))
        
        for component in self._getComponents():
            if isinstance(component, tuple): # its a simple element
                name, value = component
                if value == None: 
                    continue
                # generally we do not need to see False boolean nodes
                if isinstance(value, bool) and value == False: 
                    continue 
                sub.append(u'%s=%s' % (fixBytes(name), fixBytes(value)))
            else: # its a node subclass
                if component == None: 
                    continue
                else: 
                    sub.append(fixBytes(component.__repr__())) # all __repr__ on sub objects
        #print _MOD, sub
        try:
            msg.append(u' '.join(sub))
        except UnicodeDecodeError:
            msg.append(u'unicode decode error!!')
            return "Unicode Decode Error"
        msg.append(u'>')

        if six.PY2:
            return u''.join(msg).encode('utf-8')
        else:
            return u''.join(msg)

    def getNewDoc(self):
        doc = xml.dom.minidom.Document()
        if self._doctypeName != None:
            doctype = doc.implementation.createDocumentType(self._doctypeName,
                self._doctypePublic, self._doctypeSystem)
            doc.appendChild(doctype)
        return doc

    def toxml(self, doc=None, parent=None, stringOut=False):
        '''Provides XML output as either a text string or as DOM node. 
        This method can be called recursively to build up nodes on a DOM tree. 
        This method will assume that if an self.charData attribute has been 
        defined this is a text element for this node. Attributes, sub 
        entities, and sub nodes are obtained via subclassed method calls.
        '''
        if doc == None:
            doc = self.getNewDoc()
        if parent == None:
            parent = doc

        node = doc.createElement(self._tag)  

        # if attributes are defined, add to tag
        for name, value in self._getAttributes():
            if value in [None, '']: 
                continue
            node.setAttribute(name, str(value))

        # if self.charData is defined, this is a text component of this tag
        if self.charData != None:
            cd = fixBytes(self.charData)
            try:
                node.appendChild(doc.createTextNode(str(cd)))
            except UnicodeEncodeError:                
                # try raw data
                node.appendChild(doc.createTextNode(cd))

        for component in self._getComponents():
            if component == None: 
                continue
            # its a simple element
            elif isinstance(component, tuple): 
                tag, content = component
                if content == None: 
                    continue

                # some elements are treated as boolean values; presence 
                # of element, w/o text, is true
                if isinstance(content, bool) and content == False: 
                    continue 
                content = fixBytes(content)
                tag = fixBytes(tag)
                
                sub = doc.createElement(tag)
                if isinstance(content, bool) and content == True:
                    pass # no text node needed
                else:
                    # was the topline; trying to use replace for errors
                    #entry = u"%s" % content
                    if isinstance(content, int) or isinstance(content, float):
                        contentStr = str(content)
                    else:
                        contentStr = content

                    if six.PY2:                       
                        try:
                            entry = unicode(contentStr, errors='replace') # @UndefinedVariable pylint: disable=undefined-variable 
                            
                        except TypeError:
                            entry = u"%s" % contentStr
                            #entry = str(content)
                        except NameError: # py3
                            entry = contentStr
                        except RuntimeError:  # IronPython
                            entry = u"%s" % contentStr                        
                    else:
                        entry = contentStr


                    try:
                        sub.appendChild(doc.createTextNode(entry))
                    except TypeError:
                        raise TypeError("More problems with %r, type: %s" % (entry, type(entry)))
                node.appendChild(sub)
            elif isinstance(component, XMLNode): # its a XMLNode subclass
                # parent is this node
                # if we have sub objects, we need to attach them to caller node
                component.toxml(doc, node, 0)
            elif isinstance(component, list):
                # TODO: this error is raised in a few cases that objects
                # are not properly organized in the resulting xml object; 
                # the problem is generally not here, but in the higher-level
                print(['cannot process component object', component, 'doc', doc, 'parent', parent])
            else:
                raise XMLNodeException(
                    'cannot process component object: %s' % component)

        # append completed node to parent (from arg) or document
        parent.appendChild(node)
        if stringOut:
            return parent.toprettyxml(indent=u"  ", encoding="utf-8")
            #return parent.toxml(encoding="utf-8")

        else:
            # do not need to do anything, as has been attached to parent
            return None 

    def xmlStr(self):
        '''Shortcut method to provide quick xml out.'''
        x = self.toxml(None, None, 1)
        if six.PY2:
            return x
        else:
            if isinstance(x, bytes):
                return x.decode(errors='replace')
            else:
                return x


class XMLNodeList(XMLNode):
    '''
To understand what a XMLNodeList is, we need to first see that Nodes are simply 
xml-like containers. Though many xml-like containers store just character 
data, like::

    <fifths>0</fifths>

Other xml-like containers are really more like lists, not storing character 
data but other xml-like containers in order, like::

    <attributes>
    <divisions>1</divisions>
    <key>
       <fifths>0</fifths>
       <mode>major</mode>
    </key>
    <time symbol="common">
       <beats>4</beats>
       <beat-type>4</beat-type>
    </time>
    <clef>
       <sign>G</sign>
       <line>2</line>
    </clef>
    </attributes>

In these cases, its much easier to have an xml-like container that is list like. 
That way they can be iterated over or appended to.  Thus, NodeLists, which are
nodes that give us list-like functionality for the cases where we need them.
'''

    def __init__(self):
        XMLNode.__init__(self)
        # basic storage location
        self.componentList = [] 
        # self._index = 0
        # additional attributes and nodess will be defined in subclass

    def _getComponents(self):
        return self.componentList

    def append(self, item):
        self.componentList.append(item)

    def __len__(self):
        return len(self.componentList)

    def __iter__(self):
        return common.Iterator(self.componentList)

        #return self

#     def next(self):
#         '''Method for treating this object as an iterator
#         Returns each node in sort order; could be in tree order. 
#         '''
#         if abs(self._index) >= self.__len__():
#             self._index = 0 # reset for next run
#             raise StopIteration
#         out = self.componentList[self._index] 
#         self._index += 1
#         return out
# 





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    '''Unit tests
    '''

    def setUp(self):
        pass

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types
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
                unused_a = copy.copy(obj)
                unused_b = copy.deepcopy(obj)



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [XMLNode, XMLNodeList]


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
#------------------------------------------------------------------------------
# eof

