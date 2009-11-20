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
import types

import music21

from music21 import clef
from music21 import chord
from music21 import common
from music21 import converter
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

from music21 import environment
_MOD = "doc.build.py"
environLocal = environment.Environment(_MOD)


OMIT_STR = 'OMIT_FROM_DOCS'
FORMATS = ['html', 'latex']


MODULES = [
#    chord, 
    common, 
     converter,
     duration, 
#     dynamics,
# #    environment, 
#     instrument,
#  #   interval, 
     note, 
    pitch, 
#     meter, 
#  #   musicxml, 
#   #  scale,
     stream, 
#     tempo,  
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


    def formatDocString(self, doc, indent=''):
        '''Given a docstring, clean it up for RST presentation.
        '''
        if doc == None:
            return ''
            #return '%sNo documentation.\n' % indent

        lines = doc.split('\n')
        sub = []
        for line in lines:
            line = line.strip()
            if OMIT_STR in line:
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


    #---------------------------------------------------------------------------
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
        '''For an object provided as an aargument, collect all relevant
        information in a dictionary. 
        '''
        info = {}
        info['reference'] = obj
        info['name'] = obj.__name__
        info['doc']  = self.formatDocString(obj.__doc__)
        info['methods'] = {}
        info['attributes'] = {}
        for partName in dir(obj):
            # partName is a string
            if partName.startswith('__'): 
                continue
            partObj = getattr(obj, partName)
            if (isinstance(partObj, types.StringTypes) or 
                isinstance(partObj, types.DictionaryType) or 
                isinstance(partObj, types.ListType) 
                ):
                pass
            elif (callable(partObj) or hasattr(partObj, '__doc__')):
                info['methods'][partName] = self.scanMethod(partObj)
            else:
                print 'noncallable', part

        self.classes[obj.__name__] = info

    #---------------------------------------------------------------------------
    def scanModule(self):
        '''For a given module, determine which objects need to be documented.
        '''
        for component in dir(self.mod):
            
            if component.startswith('__'): # ignore private variables
                continue
            if component == 'Test': # ignore test classes
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
            # some of these are functions that need to be documented as well
            else:
                environLocal.printDebug(['cannot process: %s' % obj])


    #---------------------------------------------------------------------------
    def getRestructured(self):
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
            titleStr = 'Class %s' % self.classes[className]['name']
            msg += self._heading(titleStr, '-')
            msg.append('%s\n' % self.classes[className]['doc'])
            #msg.append('*Attributes*\n\n')
            #msg.append('*Methods*\n\n')

            # create a dummy object and list its attributes
            obj = None
            try:
                obj = self.classes[className]['reference']()
            except TypeError:
                print _MOD, 'cannot create instance of %s' % className
            if obj != None:
                attrList = obj.__dict__.keys()
                attrList.sort()
                attrPublc = []
                attrPrivate = []
                for attr in attrList:
                    if attr.startswith('_'):
                        attrPrivate.append(attr)
                    else:
                        attrPublc.append(attr)
                if len(attrPublc) > 0:
                    msg += self._heading('Attributes', '~')
                    msg += self._list(attrPublc)
#                 if len(attrPrivate) > 0:
#                     msg += self._heading('Private Attributes', '~')
#                     msg += self._list(attrPrivate)

            methodNames = self.classes[className]['methods'].keys()
            methodNames.sort()
            methodPrivate = []
            methodPublic = []
            for methodName in methodNames:
                if methodName.startswith('_'):
                    methodPrivate.append(methodName)
                else:
                    methodPublic.append(methodName)
            for methodGroup, titleStr in [(methodPublic, 'Methods'), 
                                        (methodPrivate, 'Private Methods')]:
                if len(methodGroup) > 0:
                    msg += self._heading(titleStr, '~')
                    for methodName in methodGroup:
                        #msg += self._heading(methodName, '~')
                        msg.append('**%s()**\n\n' % methodName)
                        msg.append('%s\n' % self.classes[className]['methods'][methodName]['doc'])
#             if len(methodNames) == 0:
#                 msg.append('\nNo methods available.\n\n') # need space

            msg.append('\n'*1)
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

        self.titleMain = 'Music 21 Documentation'
        # include additional rst files that are not auto-generated
        self.chaptersMain = ['install', 'environment', 
                            'examples', 'glossary', 'faq']
        self.chaptersGenerated = [] # to be populated
        self.titleAppendix = 'Indices and Tables'
        self.chaptersAppendix = ['glossary']
    
        self.modulesToBuild = MODULES
        self.updateDirs()


    def updateDirs(self):
        self.dir = os.getcwd()
        if not self.dir.endswith('music21%sdoc' % os.sep):
            raise Exception('not in the music21%sdoc directory' % os.sep)
    
        self.dirBuild = os.path.join(self.dir, '_build')
        self.dirBuildHtml = os.path.join(self.dirBuild, 'html')
        self.dirBuildLatex = os.path.join(self.dirBuild, 'latex')
        self.dirBuildDoctrees = os.path.join(self.dirBuild, 'doctrees')

        for fp in [self.dirBuild, self.dirBuildHtml, self.dirBuildLatex,
                  self.dirBuildDoctrees]:
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
            msg.append("* :ref:'%s'\n" % name)
        msg.append('\n')

        fp = os.path.join(self.dir, 'contents.rst')
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
            f = open(os.path.join(self.dir, a.fileName), 'w')
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
    
        if common.getPlatform() in ['darwin', 'nix', 'win']:
            import sphinx
            sphinxList = ['sphinx', '-b', format, '-d', self.dirBuildDoctrees,
                         self.dir, dirOut] 
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
    if len(sys.argv) == 2 and sys.argv[1] in FORMATS:
        format = sys.argv[1]
    else:
        format = 'html'

    a = Documentation()
    a.main(format)
