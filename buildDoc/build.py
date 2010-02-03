#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         build.py
# Purpose:      music21 documentation builder
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest
import os, sys, webbrowser
import types, inspect

import music21

from music21 import base
from music21 import clef
from music21 import chord
from music21 import common
from music21 import converter
from music21 import corpus
from music21 import duration
from music21 import dynamics
from music21 import environment
from music21 import instrument
from music21 import interval
from music21 import note
from music21 import pitch
from music21 import meter
from music21 import musicxml
from music21 import scale
from music21 import stream
from music21 import tempo

from music21.trecento import cadencebook as trecentoCadencebook

#from music21 import environment #redundant
_MOD = "doc.build.py"
environLocal = environment.Environment(_MOD)


OMIT_STR = 'OMIT_FROM_DOCS'
FORMATS = ['html', 'latex', 'pdf']


MODULES = [
    base,
    common, 
    converter,
    corpus, 
    chord, 
    duration, 
    dynamics,
    environment, 
    instrument,
    interval, 
    meter, 
    note, 
    pitch, 
    stream,     


#   musicxml, 
#   #  scale,
#     tempo,  

# trecento
#    trecentoCadencebook
]


#-------------------------------------------------------------------------------
# experimenting with auto documentation of modules
# incomplete

class RestrtucturedWriter(object):

    def __init__(self):
        self.INDENT = ' ' * 4

    def _heading(self, line, headingChar='='):
        '''Format an RST heading.
        '''
        msg = []
        msg.append(line)
        msg.append('\n')
        msg.append(headingChar*len(line))
        msg.append('\n'*2)
        return msg

    def _para(self, doc):
        '''Format an RST paragraph.
        '''
        if doc == None:
            return []
        doc = doc.strip()
        msg = []
        msg.append('\n'*2)
        msg.append(doc)
        msg.append('\n'*2)
        return msg

    def _list(self, elementList, indent=''):
        '''Format an RST list.
        '''
        msg = []
        for item in elementList:
            item = item.strip()
            msg.append('%s+ ' % indent)
            msg.append(item)
            msg.append('\n'*1)
        msg.append('\n'*1)
        return msg

    def formatParent(self, mroEntry):
        '''Return a class name as a parent, showing module when necessary

        >>> from music21 import note
        >>> rw = RestrtucturedWriter()
        >>> post = rw.formatParent(inspect.getmro(note.Note)[1])
        >>> 'note.NotRest' in post      
        True
        >>> post = rw.formatParent(inspect.getmro(note.Note)[4])
        >>> 'object' in post      
        True
        '''
        modName = mroEntry.__module__
        modName = modName.replace('music21.', '') # remove leading music21
        className = mroEntry.__name__
        if modName == '__builtin__':
            return className
        else:
            return '%s.%s' % (modName, className)

    def formatClassInheritance(self, mro):
        '''Given a lost of classes from inspect.getmro, return a formatted
        String

        >>> from music21 import note
        >>> rw = RestrtucturedWriter()
        >>> post = rw.formatClassInheritance(inspect.getmro(note.Note))
        >>> 'note.GeneralNote' in post
        True
        >>> 'base.Music21Object' in post
        True
        >>> 'object' in post
        True
        '''
        msg = []
        msg.append('Inherits from:')
        sub = []
        for i in range(len(mro)):
            if i == 0: continue # first is always the class itself
            sub.append(self.formatParent(mro[i]))        
        msg.append(', '.join(sub))
        return ' '.join(msg)


    def formatDocString(self, doc, indent=''):
        '''Given a docstring, clean it up for RST presentation.

        Note: can use inspect.getdoc() or inspect.cleandoc(); though
        we need customized approach demonstrated here.
        '''
        if doc == None:
            return ''
            #return '%sNo documentation.\n' % indent

        lines = doc.split('\n')
        sub = []
        for line in lines:
            line = line.strip()
            if OMIT_STR in line: # permit blocking doctest examples
                break # do not gather any more lines
            sub.append(line)

        # find double breaks in text
        post = []
        for i in range(len(sub)):
            line = sub[i]
            if line == '' and i != 0 and sub[i-1] == '':
                post.append(None) # will be replaced with line breaks
            elif line == '':
                pass
            else: 
                post.append(line)

        msg = [indent] # can add indent here
        inExamples = False
        for line in post:
            if line == None: # insert breaks from two spaces
                msg.append('\n\n' + indent) # can add indent here
            elif line.startswith('>>>'): # python examples
                if inExamples == False:
                    space = '\n\n'
                    inExamples = True
                else:
                    space = '\n'
                msg.append(space + indent + line)
            else: # continueing an existing line
                if inExamples == False:
                    msg.append(line + ' ')
                else: # assume we are in examples; 
                # need to get lines python lines tt do not start with delim
                    msg.append('\n' + indent + line + ' ')
        msg.append('\n')

        return ''.join(msg)


#-------------------------------------------------------------------------------
class ModuleDoc(RestrtucturedWriter):
    def __init__(self, mod):
        RestrtucturedWriter.__init__(self)

        self.mod = mod
        self.modName = mod.__name__
        self.modDoc = mod.__doc__
        self.classes = {}
        self.functions = {}
        self.imports = []
        self.globals = []

        # file name for this module; leave off music21 part
        fn = mod.__name__.split('.')
        self.fileName = 'module' + fn[1][0].upper() + fn[1][1:] + '.rst'
        # refernces used in rst table of contestns
        self.fileRef = 'module' + fn[1][0].upper() + fn[1][1:]


    def findDerivationClass(self, mro, partName):
        '''Given an mro (method resolution order) and a part of an object, find from where the part is derived.
        '''
        lastIndex = None
        for i in range(len(mro)):
            classPart = mro[i]
            classDir = dir(classPart)
            if partName in classDir:
                lastIndex = i
            else:
                break # none further should match
        if lastIndex == None:
            raise Exception('cannot find %s in %s' % (partName, mro))
        return lastIndex, partName

    #---------------------------------------------------------------------------
    # for methods and functions can use
    # inspect.getargspec(func)
    # to get argument information
    # can use this to format: inspect.formatargspec(inspect.getargspec(a.show))

#             args, varargs, varkw, defaults = inspect.getargspec(object)
#             argspec = inspect.formatargspec(
#                 args, varargs, varkw, defaults, formatvalue=self.formatvalue)

# might be abel to use
# inspect.classify_class_attrs

    def scanMethod(self, obj):
        methodInfo = {}
        #methodInfo['name'] = str(obj)
        methodInfo['doc'] = self.formatDocString(obj.__doc__, self.INDENT)
        return methodInfo

    def scanFunction(self, obj):
        info = {}
        info['reference'] = obj
        info['name'] = obj.__name__
        info['doc']  = self.formatDocString(obj.__doc__)

        # skip private functions
        if not obj.__name__.startswith('_'): 
            self.functions[obj.__name__] = info

    def scanClass(self, obj):
        '''For an object provided as an argument, collect all relevant
        information in a dictionary. 
        '''
        info = {}
        info['reference'] = obj
        info['name'] = obj.__name__
        info['doc']  = self.formatDocString(obj.__doc__)
        info['properties'] = {}
        info['methods'] = {}
        info['derivations'] = [] # a list of mroIndex, objName
        info['attributes'] = {}
        # get a list of parent objects, starting from this one
        # provide obj, not obj.__class__
        info['mro'] = inspect.getmro(obj)
        #environLocal.printDebug(['mro: %s, %s' % (obj, info['mro'])])

        for partName in dir(obj):
            # add to a list the index, name of derived obj
            # derivation from mro
            info['derivations'].append(self.findDerivationClass(info['mro'],
                                                                partName))

            # partName is a string
            if partName.startswith('__'): 
                continue
            partObj = getattr(obj, partName)
            if (isinstance(partObj, types.StringTypes) or 
                isinstance(partObj, types.DictionaryType) or 
                isinstance(partObj, types.ListType) 
                ):
                pass
            elif isinstance(partObj, property):
                # can use method processing on properties
                info['properties'][partName] = self.scanMethod(partObj)

            elif (callable(partObj) or hasattr(partObj, '__doc__')):
                info['methods'][partName] = self.scanMethod(partObj)
            else:
                print 'noncallable', part


        # will sort by index, which is proximity to this class
        info['derivations'].sort() 
        info['derivations'].reverse() # start with most remote first
        # environLocal.printDebug(info['derivations'])

        self.classes[obj.__name__] = info

    #---------------------------------------------------------------------------
    # note: can use inspect to get properties:
    # inspect.isdatadescriptor()

    def scanModule(self):
        '''For a given module, determine which objects need to be documented.
        '''
        for component in dir(self.mod):
            
            if component.startswith('__'): # ignore private variables
                continue
            elif 'Test' in component: # ignore test classes
                continue
            elif 'Exception' in component: # ignore test classes
                continue

            objName = '%s.%s' % (self.modName, component)
            obj = eval(objName)
            objType = type(obj)
            # print objName, objType
            if isinstance(obj, types.ModuleType):
                importName = objName.replace(self.modName+'.', '')
                self.imports.append(importName)

            elif (isinstance(obj, types.StringTypes) or 
                isinstance(obj, types.DictionaryType) or 
                isinstance(obj, types.ListType) 
                ):
                self.globals.append(objName)
            # assume that these are classes
            elif isinstance(obj, types.TypeType):
                self.scanClass(obj)
            elif isinstance(obj, types.FunctionType):
                self.scanFunction(obj)
            elif isinstance(obj, environment.Environment):
                continue # skip environment object
            else:
                environLocal.printDebug(['cannot process: %s' % repr(obj)])


    #---------------------------------------------------------------------------
    def getRestructuredClass(self, className):
        msg = []
        titleStr = 'Class %s' % self.classes[className]['name']
        msg += self._heading(titleStr, '-')

        msg.append('%s\n\n' % self.formatClassInheritance(
            self.classes[className]['mro']))

        msg.append('%s\n' % self.classes[className]['doc'])
        #msg.append('*Attributes*\n\n')
        #msg.append('*Methods*\n\n')

        obj = None
        try: # create a dummy object and list its attributes
            obj = self.classes[className]['reference']()
        except TypeError:
            pass
            #print _MOD, 'cannot create instance of %s' % className

        if obj != None:
            attrList = obj.__dict__.keys()
            attrList.sort()
            attrPublic = []
            attrPrivate = []
            for attr in attrList:
                if not attr.startswith('_'):
                    attrPublic.append(attr)
            if len(attrPublic) > 0:
                msg += self._heading('Attributes', '~')

                # not working:
#                 for i, nameFound in self.classes[className]['derivations']:
#                     if nameFound not in attrPublic:
#                         continue
#                     #msg += self._list(attrPublic)
                for nameFound in attrPublic:
                    msg.append('**%s**\n\n' % nameFound)

        for groupName, groupKey, postfix in [
                                    ('Methods', 'methods', '()'), 
                                    ('Properties', 'properties', '')]:
            methodNames = self.classes[className][groupKey].keys()
            methodPublic = []
            for methodName in methodNames:
                if not methodName.startswith('_'):
                    methodPublic.append(methodName)
            if len(methodPublic) == 0: 
                continue    

            msg += self._heading(groupName, '~')
    
            iLast = None
            for i, nameFound in self.classes[className]['derivations']:
                if nameFound not in methodPublic:
                    continue
                if i == len(self.classes[className]['mro']) - 1:
                    continue # skip names dervied from object
    
                parentSrc = self.formatParent(
                            self.classes[className]['mro'][i])
    
                if i != iLast:
                    msg += '\n'
                    iLast = i
                    if i != 0:
                        titleStr = 'Inherited from %s' % parentSrc
                    else:
                        titleStr = 'Locally Defined' 
                    msg.append('%s\n\n' % titleStr)

                msg.append('**%s%s**\n\n' % (nameFound, postfix))    
                if i == 0: # only provide full doc
                    msg.append('%s\n' % 
                        self.classes[className][groupKey][nameFound]['doc'])

        msg.append('\n'*1)
        return msg


    def getRestructured(self):
        '''Produce RST documentation for a complete module.
        '''
        msg = []
        msg += self._heading(self.modName , '=')
        msg += self._para(self.modDoc)

        # can optionally list imports
        #msg += self._heading('Imports' , '-')
        #msg += self._list(self.imports)


        funcNames = self.functions.keys()
        funcNames.sort()
        for funcName in funcNames:
            titleStr = 'Function %s()' % self.functions[funcName]['name']
            msg += self._heading(titleStr, '-')
            msg.append('%s\n' % self.functions[funcName]['doc'])

        classNames = self.classes.keys()
        classNames.sort()
        for className in classNames:
            msg += self.getRestructuredClass(className)
        return ''.join(msg)


# def buildModuleReference():
#     for module in [note]:
#         a = ModuleDoc(module)
#         a.scanModule()
#         a.getRestructured()





#-------------------------------------------------------------------------------
class Documentation(RestrtucturedWriter):

    def __init__(self):
        RestrtucturedWriter.__init__(self)

        self.titleMain = 'Music21 Documentation'
        # include additional rst files that are not auto-generated
        self.chaptersMain = ['what',
                             'quickStart',
                             'overviewNotes', 
                             'overviewStreams', 
                             'overviewFormats', 
                             'examples', 
                             'about', 

                             'install', 
                             'environment', 
                             'graphing', 
                             'glossary', 
                             'faq']
        self.chaptersGenerated = [] # to be populated
        self.titleAppendix = 'Indices and Tables'
        self.chaptersAppendix = ['glossary']
    
        self.modulesToBuild = MODULES
        self.updateDirs()


    def updateDirs(self):
        self.dir = os.getcwd()
        if not self.dir.endswith('music21%sbuildDoc' % os.sep):
            raise Exception('not in the music21%sdoc directory' % os.sep)
    
        parentDir = os.path.dirname(self.dir)
        self.dirBuild = os.path.join(parentDir, 'music21', 'doc')
        self.dirRst = os.path.join(self.dir, 'rst')
        self.dirBuildHtml = os.path.join(self.dirBuild, 'html')
        #self.dirBuildLatex = os.path.join(self.dirBuild, 'latex')
        #self.dirBuildPdf = os.path.join(self.dirBuild, 'pdf')
        self.dirBuildDoctrees = os.path.join(self.dir, 'doctrees')

        for fp in [self.dirBuild, self.dirBuildHtml, 
                  #self.dirBuildLatex,
                  self.dirBuildDoctrees]:
                  #self.dirBuildPdf]:
            if os.path.exists(fp):
                # delete old paths?
                pass
            else:
                os.mkdir(fp)

    def writeContents(self):
        '''This writes the main table of contents file, contents.rst. 
        '''
        msg = []
        msg.append('.. _contents\n\n')
        msg += self._heading(self.titleMain, '=')
        msg.append('.. toctree::\n')
        msg.append('   :maxdepth: 2\n\n')

        for name in self.chaptersMain + self.chaptersGenerated:
            msg.append('   %s\n' % name)        
        msg.append('\n')

        msg += self._heading(self.titleAppendix, '=')
        for name in self.chaptersAppendix:
            msg.append("* :ref:`%s`\n" % name)
        msg.append('\n')

        fp = os.path.join(self.dirRst, 'contents.rst')
        f = open(fp, 'w')
        f.write(''.join(msg))
        f.close()

#         ex = '''.. _contents:
# 
# music21 Documentation
# ==============================
# 
# .. toctree::
#    :maxdepth: 2
# 
#    objects
#    examples
#    glossary
#    faq
# 
#    moduleNote_
# 
# Indices and Tables
# ==================
# 
# * :ref:`glossary`
# 
#         '''



    def writeModuleReference(self):
        '''Write a .rst file for each module defined in modulesToBuild.
        Add the file reference to the list of chaptersGenerated.
        '''
        for module in self.modulesToBuild:
            a = ModuleDoc(module)
            a.scanModule()
            f = open(os.path.join(self.dirRst, a.fileName), 'w')
            f.write(a.getRestructured())
            f.close()
            self.chaptersGenerated.append(a.fileRef)

    def main(self, format):
        '''Create the documentation. 
        '''
        if format not in FORMATS:
            raise Exception, 'bad format'

        self.writeModuleReference()    
        self.writeContents()    

        if format == 'html':
            dirOut = self.dirBuildHtml
            pathLaunch = os.path.join(self.dirBuildHtml, 'contents.html')
        elif format == 'latex':
            dirOut = self.dirBuildLatex
            #pathLaunch = os.path.join(dirBuildHtml, 'contents.html')
        elif format == 'pdf':
            dirOut = self.dirBuildPdf
        else:
            raise Exception('undefined format %s' % format)

        if common.getPlatform() in ['darwin', 'nix', 'win']:
            # -b selects the builder
            import sphinx
            sphinxList = ['sphinx', '-E', '-b', format, '-d', self.dirBuildDoctrees,
                         self.dirRst, dirOut] 
            sphinx.main(sphinxList)


    # alternative command line approach
    #         cmd = 'sphinx-build -b %s -d %s %s %s' % (format, dirBuildDoctrees,
    #                 dir, dirOut)
    #         print _MOD, cmd  # print is function in python 3.0
    #         os.system(cmd)
    
    
        if format == 'html':
            webbrowser.open(pathLaunch)





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def setUp(self):
        pass

    def testToRoman(self):
        self.assertEqual(True, True)



#-------------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'test':
        music21.mainTest(Test)
        buildDoc = False
    elif len(sys.argv) == 2 and sys.argv[1] in FORMATS:
        format = [sys.argv[1]]
        buildDoc = True
    else:
        format = ['html']#, 'pdf']
        buildDoc = True

    if buildDoc:
        for fmt in format:
            a = Documentation()
            a.main(fmt)
