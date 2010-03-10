#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         node.py
# Purpose:      XML base class for SAX-based xml objects
#
# Authors:      Christopher Ariza
#               
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import copy
import xml.sax
from xml.sax import saxutils
import xml.dom.minidom


import doctest, unittest
from music21 import common

_MOD = 'node.py'


#-------------------------------------------------------------------------------
# xml base class

# ugly printyprint hack thanks to 
# http://ronrothman.com/public/leftbraned/xml-dom-minidom-toprettyxml-and-silly-whitespace
# this should be fixed by python 2.7


def fixed_writexml(self, writer, indent="", addindent="", newl=""):
    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        xml.dom.minidom._write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        if len(self.childNodes) == 1 \
          and self.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
            writer.write(">")
            self.childNodes[0].writexml(writer, "", "", "")
            writer.write("</%s>%s" % (self.tagName, newl))
            return
        writer.write(">%s"%(newl))
        for node in self.childNodes:
            node.writexml(writer,indent+addindent,addindent,newl)
        writer.write("%s</%s>%s" % (indent,self.tagName,newl))
    else:
        writer.write("/>%s"%(newl))



#-------------------------------------------------------------------------------
class NodeException(Exception):
    pass

class Node(object):
    def __init__(self):
        '''
        >>> a = Node()
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
        >>> a = Node()
        >>> a._getAttributes()
        []
        '''
        return self._attr.items()


    def _getComponents(self):
        '''Get all sub-components, in order. This may be Node subclasses, or may be simple entities. Simple entities do not have attributes and are only used as containers for character data. These entities are generally not modelled as objects '''
        return []


    def loadAttrs(self, attrs):
        '''Given a SAX attrs object, load all atributes that are named within this object's _attr dictionary. 
        '''
        for key in self._attr.keys():
            value = attrs.get(key, "") # from SAX attrs object
            if value.strip() != '': # only modify if not nothing
                self._attr[key] = value        


    #---------------------------------------------------------------------------
    def _convertNameCrossReference(self, name):
        '''Define mappings from expected MusicXML names and specially named attributes in object.
        Return a list of zero or 1 name
        
        Speialize in sublcasses as needed, calling this base class to get
        general defaults

        All options need to be lower case.

        >>> a = Node()
        >>> a._convertNameCrossReference('characterData')
        'charData'
        '''
        for attr, options in self._crossReference.items():
            if name in options or name.lower() in options:
                return attr
        return '' # return an empty string if no match

    def _convertNameFromXml(self, nameSrc):
        '''Given an xml attribute/entity name, try to convert it to a Python attribute name. If the python name is given, without and - dividers, the the proper name should be returned

        >>> a = Node()
        >>> a._convertNameFromXml('char-data')
        'charData'
        '''
        parts = nameSrc.split('-')
        nameDst = [parts[0]] # create a list for storage
        if len(parts) > 1:
            for stub in parts[1:]:
                nameDst.append(stub[0].upper() + stub[1:])
        #print _MOD, 'new name', ''.join(nameDst)
        return ''.join(nameDst)

    def _convertNameToXml(self, nameSrc):
        '''Given an a Python attribute name, try to convert it to a XML name.
        If already an XML name, leave alone.

        >>> a = Node()
        >>> a._convertNameToXml('charData')
        'char-data'
        '''
        nameDst = []
        for char in nameSrc:
            if char.isupper():
                nameDst.append('-%s' % char.lower())
            else:
                nameDst.append(char)
        return ''.join(nameDst)


    #---------------------------------------------------------------------------
        
    def _publicAttributes(self):
        '''Get all public names from this object.
        Used in merging. 

        >>> a = Node()
        >>> len(a._publicAttributes())
        2
        >>> print(a._publicAttributes())
        ['charData', 'tag']
    
        '''
        names = dir(self)
        post = []
        for name in names:
            if name.startswith('_'): continue
            # do not want methods
            if callable(getattr(self, name)): continue
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

    def merge(self, other, favorSelf=True):
        '''Given another similar or commonly used Node object, combine
        all attributes and return a new object.

        >>> a = Node()
        >>> a.set('charData', 'green')
        >>> b = Node()
        >>> c = b.merge(a)
        >>> c.get('charData')
        'green'
        '''
        if not isinstance(other, Node):
            raise NodeException('can only merge with other nodes')

        new = copy.deepcopy(self)

        localAttr = self._publicAttributes()
        otherAttr = other._publicAttributes()

        # print _MOD, 'attempting to merge', localAttr

        # if attrs are the same, these are instances of same class
        if localAttr == otherAttr:
            for i in range(len(localAttr)):
                # neither are defined 
                if (self.get(localAttr[i]) == None and 
                    other.get(otherAttr[i]) == None):
                    pass
                # local is defined
                elif (self.get(localAttr[i]) != None and 
                    other.get(otherAttr[i]) == None):
                    pass # already set as this ia copy
                    # new.set(localAttr[i], self.get(localAttr[i]))
                # other is defined
                elif (self.get(localAttr[i]) == None and 
                    other.get(otherAttr[i]) != None):
                    new.set(otherAttr[i], other.get(otherAttr[i]))
                # both are defined
                elif (self.get(localAttr[i]) == None and 
                    other.get(otherAttr[i]) == None):
                    if favorSelf:
                        pass # already set as this ia copy
                        # new.set(localAttr[i], self.get(localAttr[i]))
                    else:
                        new.set(otherAttr[i], otherAttr.get(otherAttr[i]))
        else:
            raise NodeException('cannot merge: %s, %s' % (self, other))
            #print _MOD, 

        # call local merge special
        # may upate new
        self._mergeSpecial(new, other, favorSelf)
        return new


    #---------------------------------------------------------------------------
    # getters and setters, properties

    def _getTag(self):
        return self._tag

    def _setTag(self, tag):
        self._tag = tag

    # define property
    tag = property(_getTag, _setTag)
        

    def set(self, name, value):
        if name in self._attr.keys():
            self._attr[name] = value
        elif self._convertNameToXml(name) in self._attr.keys():
            self._attr[self._convertNameToXml(name)] = value
        else: # if a python name it will not be altered
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
            if not match:
                raise NodeException('this object does not have a %s (or %s) attribute' % (name, candidates))
        
    def get(self, name):
        if name in self._attr.keys():
            return self._attr[name]
        elif self._convertNameToXml(name) in self._attr.keys():
            return self._attr[self._convertNameToXml(name)]
        else: # if a python name it will not be altered
            match = False
            candidates = []
            candidates.append(self._convertNameFromXml(name))
            candidates.append(self._convertNameCrossReference(name))
            for candidate in candidates:
                if hasattr(self, candidate):
                    match = True
                    return getattr(self, candidate)
            if not match:
                raise NodeException('this object does not have a %s (or %s) attribute' % (name, candidate))
        

    def setDefaults(self):
        '''provide defaults for all necessary attributes at this level
        '''
        pass




    #---------------------------------------------------------------------------
    def __repr__(self):
        '''Provide a linear string representation of the element. This is not XML, but a simple format for viewing contents of elements.'''
        msg = []
        # NOTE: this fails in python3:
        msg.append(u'<%s ' % self._tag)
        sub = []
        for name, value in self._getAttributes():
            if value == None: continue
            sub.append(u'%s=%s' % (name, value))
        if self.charData not in ['', None]:
            sub.append(u'charData=%s' % self.charData)
        
        for component in self._getComponents():
            if type(component) == tuple: # its a simple element
                name, value = component
                if value == None: continue
                # generally we do not need to see False boolean nodes
                if type(value) == bool and value == False: continue 
                sub.append(u'%s=%s' % (name, value))
            else: # its a node subclass
                if component == None: continue
                sub.append(component.__repr__()) # all __repr__ on sub objects
        #print _MOD, sub
        try:
            msg.append(u' '.join(sub))
        except UnicodeDecodeError:
            msg.append(u'unicode decode error!!')
        msg.append(u'>')

        return u''.join(msg).encode('utf-8')

    def getNewDoc(self):
        doc = xml.dom.minidom.Document()
        if self._doctypeName != None:
            doctype = doc.implementation.createDocumentType(self._doctypeName,
                self._doctypePublic, self._doctypeSystem)
            doc.appendChild(doctype)
        return doc

    def toxml(self, doc=None, parent=None, stringOut=0):
        '''Provides XML output as either a text string or as DOM node. This method can be called recursively to build up nodes on a DOM tree. This method will assume that if an self.charData attribute has been defined this is a text element for this node. Attributes, sub entities, and sub nodes are obtained via subclassed method calls.
        '''
        if doc == None:
            doc = self.getNewDoc()
        if parent == None:
            parent = doc

        node = doc.createElement(self._tag)  

        # if attributes are defined, add to tag
        for name, value in self._getAttributes():
            if value in [None, '']: continue
            node.setAttribute(name, str(value))

        # if self.charData is defined, this is a text component of this tag
        if self.charData != None:
            node.appendChild(doc.createTextNode(str(self.charData)))

        for component in self._getComponents():
            if component == None: continue
            elif type(component) == tuple: # its a simple element
                tag, content = component
                if content == None: continue
                # some elements are treated as boolean values; presence 
                # of element, w/o text, is true
                if type(content) == bool and content == False: 
                    continue 
                sub = doc.createElement(tag)
                if type(content) == bool and content == True:
                    pass # no text node needed
                else:
                    sub.appendChild(doc.createTextNode(u"%s" % content))
                node.appendChild(sub)
            elif isinstance(component, Node): # its a Node subclass
                # parent is this node
                # if we have sub objects, we need to attach them to caller node
                component.toxml(doc, node, 0)
            else:
                raise NodeException(
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
        return self.toxml(None, None, 1)



class NodeList(Node):
    '''Nodes that is designed to function as a list. In general,
     this is an node this only used to contain other nodes. 
     List operations permit easy access and manipuatlooi'''

    def __init__(self):
        Node.__init__(self)
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
        '''Test copyinng all objects defined in this module
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



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Node, NodeList]


if __name__ == "__main__":
    s1 = doctest.DocTestSuite(__name__)
    s2 = unittest.defaultTestLoader.loadTestsFromTestCase(Test)
    s1.addTests(s2)
    runner = unittest.TextTestRunner()
    runner.run(s1)  