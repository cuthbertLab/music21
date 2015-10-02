# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         chant.py
# Purpose:      Classes and Tools for converting Music21 Streams to Gregorio .gabc
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012, 15 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
``ALPHA MODULE``: Not directly supported by cuthbertLab.

Classes and Tools for converting Music21 Streams to Gregorio .gabc

Requires the amazing Gregoio library: http://gregorio-project.github.io , which itself
requires LaTeX. (MacTeX, etc.; I suggest Basic TeX instead of the full MacTeX for this,
since it's only 100MB instead of 2.5GB)
'''


from __future__ import unicode_literals

import re
import unittest
import os.path

from music21 import clef
from music21 import common
from music21 import exceptions21
from music21 import note
from music21 import stream

from music21.ext import six

from music21 import environment
_MOD = "chant.py"
environLocal = environment.Environment(_MOD)

 
def fromStream(inputStream):
    if inputStream.metadata is not None:
        incipit = inputStream.metadata.title
    else:
        incipit = "Benedicamus Domino"
    out = ''
    out += 'name: ' + incipit + ';\n'
    out += "%%\n"
    return out
 
class GregorianStream(stream.Stream):
    r'''
    
    >>> s = alpha.chant.GregorianStream()
    >>> s.append(clef.AltoClef())
    >>> n = alpha.chant.GregorianNote("C4")
    >>> l = note.Lyric("Po")
    >>> l.syllabic = "start"
    >>> n.lyrics.append(l)
    >>> n.oriscus = True
    >>> s.append(n)
    >>> s.toGABCText()
    '(c3) Po(ho)\n'
    
    '''
    def toGABCText(self):
        currentClef = None
        outLine = ""
        startedSyllable = False
        for e in self:
            if hasattr(e, 'isNote') and e.isNote is True:
                if self.lyrics and e.lyrics[0] != "":
                    if startedSyllable == True:
                        outLine += ")"
                        startedSyllable = False
                    if e.lyrics[0].syllabic in ['begin', 'single']:
                        outLine += " "
                    outLine += e.lyrics[0].text
                    outLine += "("
                    startedSyllable = True
 
                outLine += e.toGABC(useClef = currentClef)
            elif 'Clef' in e.classes:
                if startedSyllable == True:
                    outLine += ") "
                    startedSyllable = False
                currentClef = e
                outLine += self.clefToGABC(e) + ' '
        if startedSyllable == True:
            outLine += ")\n"
        return outLine
    def clefToGABC(self, clefIn):
        '''
        >>> s = alpha.chant.GregorianStream()
        >>> c = clef.AltoClef()
        >>> s.clefToGABC(c)
        '(c3)'  
        '''
        return "(" + clefIn.sign.lower() + str(clefIn.line) + ")"
 
 
class GregorianNote(note.Note):
    '''
    A GregorianNote is a subclass of :class:`~music21.note.Note` that
    contains extra attributes which represent the interpretation or
    graphical representation of the note.
    
    
    Most of the attributes default to False.  Exceptions are noted below.
    
    
    Example: a very special note.
    
    
    >>> n = alpha.chant.GregorianNote("C4")
    >>> n.liquescent = True 
    >>> n.quilisma = True
    >>> n.basicShape = 'virga'  # default: punctus
    >>> n.breakNeume = True # don't connect to the next note in a neume.
    >>> n.stropha = True
    >>> n.inclinatum = True
    >>> n.debilis = True  # small note
    >>> n.episema = True
    >>> n.punctumMora = True
    >>> n.fill = 'cavum' # 
    '''
    
    liquescent = False
    quilisma = False
    oriscus = False
    basicShape = 'punctus'
    breakNeume = False
    stropha = False
    inclinatum = False
    debilis = False
    nextNote = None
    episema = False
    punctumMora = False
    _fill = 'solid'
    fillDic = {'solid': '',
               'cavum': 'r',
               'linea': 'R',
               'linea-cavum': 'r0',
               'accentus': 'r1',
               'reversed-accentus': 'r2',
               'circulus': 'r3',
               'semi-circulus': 'r4',
               'reversed-semi-circulus': 'r5'}
    polyphonic = False
    choralSign = False
   
    def __init__(self, *arguments, **keywords):
        note.Note.__init__(self, *arguments, **keywords)
       
    def toGABC(self, useClef = None, nextNote = None):
        letter = self.toBasicGABC(useClef)
        if self.debilis == True:
            letter = "-" + letter
        if self.inclinatum == True:
            letter = letter.upper()
       
        if self.fill != 'solid':
            if self.fill in self.fillDic:
                letter += self.fillDic[self.fill]
            else:
                raise ChantException('cannot use filltype %s' % self.fill)
           
        if self.oriscus == True:
            letter += 'o'
        elif self.quilisma == True:
            letter += 'w'
        elif self.stropha == True:
            letter += 's'
        if self.liquescent != False:
            #if nextNote is not None:
            #   if nextNote.diatonicNoteNum > self.diatonicNoteNum:
            #        letter += '<'
            #    else:
            #        letter += '>'
            if self.liquescent == 'ascending':
                letter += '<'
            elif self.liquescent == 'descending':
                letter += '<'
            else:
                letter += '~'
        if self.punctumMora != False:
            if self.punctumMora == True or self.punctumMora == 1:
                letter += '.'
            elif self.punctumMora == 2:
                letter += '..'
            else:
                raise ChantException('unable to do punctumMora with more than two notes')
        if self.episema != False:
            if self.episema == 'vertical':
                letter += '\''
            elif self.episema == 'below':
                letter += '_0'
            else:
                letter += '_'
        if self.breakNeume != False:
            letter += "!"
               
        if self.choralSign != False:
            letter += "[cs:" + self.choralSign + "]"
               
        if self.polyphonic == True:
            letter = "{" + letter + "}"
        return letter
 
 
    def toBasicGABC(self, useClef = None):
        '''
        returns the character representing inNote in the given clef (default = AltoClef)
       
        see http://home.gna.org/gregorio/gabc/ for more details.  'd' = lowest line
       
        
        
        >>> n = alpha.chant.GregorianNote("C4")
        >>> c = clef.AltoClef()
        >>> n.toBasicGABC(c)
        'h'
       
        >>> c2 = clef.SopranoClef()
        >>> n.toBasicGABC(c2)
        'd'
       
        '''
        inNote = self
        usedDefaultClef = False
        if useClef is None:
            useClef = clef.AltoClef()
            usedDefaultClef = True
       
        asciiD = 100
        asciiA = 97
        asciiM = 109
       
        if not hasattr(useClef, 'lowestLine'):
            raise ChantException("useClef has to define the diatonicNoteNum representing the lowest line")
       
        stepsAboveLowestLine = inNote.diatonicNoteNum - useClef.lowestLine
        asciiNote = stepsAboveLowestLine + asciiD
       
        if asciiNote < asciiA:
            if usedDefaultClef is True:
                raise ChantException("note is too low for the default clef (AltoClef), choose a lower one")
            else:
                raise ChantException("note is too low for the clef (%s), choose a lower one" % str(useClef))
        elif asciiNote > asciiM:
            if usedDefaultClef is True:
                raise ChantException("note is too high for the default clef (AltoClef), choose a higher one")
            else:
                raise ChantException("note is too high for the clef (%s), choose a higher one" % str(useClef))
        else:
            return six.unichr(asciiNote) # unichr on python2; chr python3


    def _getFill(self):
        return self._fill
    
    def _setFill(self, value):
        if value not in self.fillDic:
            raise ChantException("Cannot set fill to value %s." % value)
        self._fill = value
    
    fill = property(_getFill, _setFill, doc='''Sets the
    fill for the note, for teaching purposes, representing
    polyphony, etc.  Acceptable values are:
    
        * solid (default)
        * cavum (void)
        * linea (lines around it; technically not a fill)
        * linea-cavum (both of the previous)
        * accentus
        * reversed-accentus
        * circulus
        * semi-circulus
        * reversed-semi-circulus
        
    See the docs for Gregorio for graphical representations of these figures.
    
    
    >>> n = alpha.chant.GregorianNote("D3")
    >>> n.fill
    'solid'
    >>> n.fill = 'cavum'
    >>> n.fill
    'cavum'
    
    ''')

class BaseScoreConverter(object):
    '''
    Converter for all Score objects.
    '''

    samplePiece = r'''
    style: modern;
    
    % Then, when gregorio encounters the following line (%%), it switches to the score, where you input the notes
    %%
    
    % The syntax in this part is called gabc. Please refer to http://home.gna.org/gregorio/gabc/#basis
    
    Pó(c3eh)pu(g)lus(h) Si(hi)on,(hgh.) *(;) ec(hihi)ce(e.) Dó(e.f!gwhhi)mi(h){n}us(h) vé(hi)ni(ig//ih)et(h.) (,) ad(iv./hig) sal(fe)ván(ghg)das(fg) gen(e_f_e_)tes(e.) :(:)
    
    et(e) au(eh)dí(hhi)tam(i) fá(kjki)ci(i)et(i) Dó(ij)mi(ihi)nus(iv./hiHF) (,) gló(h!i'j)ri(ji!kvJI)am(ij) vo(j.i!jwk)cis(ji) su(i_j_i_)æ,(i.) (;) in(e) læ(e)tí(e!f'h)ti(h)a(hi!jVji)
    
    cor(gh!ijI'H<)dis(ihhf!gwh) ve(e_f_e_)stri.(e) Ps.(::) Qui(ehg) re(hi)gis(i) I(i)sra(i)el,(hj) in(j)tén(ji)de(ij..) :*(:) qui(ig) de(hi)dú(i)cis(i)
    
    vel(i)ut(i!jwk) o(i')vem(h) Jo(hhh)seph.(fe..) (::) Gló(ehg)ri(hi)a(i) Pa(i)tri.(i) (:) E(i) u(i!jwk) o(i) u(h) a(hhh) e(fe..) (::)
    '''


    def __init__(self):
        self.environLocal = environLocal
        self.gregorioConverter = '/usr/local/bin/gregorio'
        self.gregorioOptions = ""
        self.gregorioCommand = None
        
        self.latexConverter = '/usr/texbin/lualatex'
        self.latexOptions = '--interaction=nonstopmode'
        
        self.score = ""
        self.incipit = ""
        self.mode = ""
        self.paperType = None
    
    def writeFile(self, text=None):
        '''
        
        >>> bsc = alpha.chant.BaseScoreConverter()
        >>> filePath = bsc.writeFile('hello')
        >>> assert(filePath.endswith('.gabc')) #_DOCS_HIDE
        >>> filePath = '/var/folders/k9/85ztxmy53xg1qxvr0brw1zyr0000gn/T/music21/tmpekHFCr.gabc' #_DOCS_HIDE
        >>> filePath 
        '/var/folders/k9/85ztxmy53xg1qxvr0brw1zyr0000gn/T/music21/tmpekHFCr.gabc'
        
        '''
        
        if text == None or text == "":
            raise ChantException('Cannot write file if there is no data')
        fp = self.environLocal.getTempFile('.gabc')
        f = open(fp, 'w')
        f.write(text)
        f.close()
        return fp
        
        
    def launchGregorio(self, fp = None):
        '''
        converts a .gabc file to LaTeX using the
        gregorio converter.  Returns the filename with .tex substituted for .gabc
        
        >>> bsc = alpha.chant.BaseScoreConverter()
        >>> #_DOCS_SHOW newFp = bsc.launchGregorio('~cuthbert/Library/Gregorio/examples/Populas.gabc')
        >>> #_DOCS_SHOW bsc.gregorioCommand
        >>> 'open -a"/usr/local/bin/gregorio"  ~cuthbert/Library/Gregorio/examples/Populas.gabc' #_DOCS_HIDE
        'open -a"/usr/local/bin/gregorio"  ~cuthbert/Library/Gregorio/examples/Populas.gabc'
        
        
        More often, you'll want to write a textfile from writeFile:
        
        '''
        platform = common.getPlatform()
        fpApp = self.gregorioConverter
        options = self.gregorioOptions

        if platform == 'win':  # note extra set of quotes!
            cmd = '""%s" %s "%s""' % (fpApp, options, fp)
        elif platform == 'darwin':
            cmd = '%s %s %s' % (fpApp, options, fp)
        elif platform == 'nix':
            cmd = '%s %s %s' % (fpApp, options, fp)        
        self.gregorioCommand = cmd
        os.system(cmd)
        newfp = re.sub(r'\.gabc', '.tex', fp)
        return newfp

    def launchLaTeX(self, fp = None):
        '''
        converts a .tex file to pdf using lulatex
        Returns the filename with .pdf substituted for .tex
        '''
        platform = common.getPlatform()
        fpApp = self.latexConverter
        options = self.latexOptions
        fpDir = os.path.dirname(fp)
        options += ' --output-dir="' + fpDir + '"'

        if platform == 'win':  # note extra set of quotes!
            cmd = '""%s" %s "%s""' % (fpApp, options, fp)
        elif platform == 'darwin':
            cmd = '%s %s %s' % (fpApp, options, fp)
        elif platform == 'nix':
            cmd = '%s %s %s' % (fpApp, options, fp)        
        self.gregorioCommand = cmd
        os.system(cmd)
        newfp = re.sub(r'\.tex', '.pdf', fp)
        return newfp


class DefaultTeXWrapper(object):
    
    def __init__(self):
        self.baseWrapper = '''% !TEX TS-program = lualatex
% !TEX encoding = UTF-8

% This is a simple template for a LuaLaTeX document using gregorio scores.

\\documentclass[11pt]{article} % use larger type; default would be 10pt

% usual packages loading:
\\usepackage{luatextra}
\\usepackage{graphicx} % support the \\includegraphics command and options
\\usepackage{geometry} % See geometry.pdf to learn the layout options. There are lots.
\\geometry{PAPERTYPEGOESHERE} % a4paper or letterpaper (US) or a5paper or other
\\usepackage{gregoriotex} % for gregorio score inclusion
\\usepackage{fullpage} % to reduce the margins

% choose the language of the document here
\\usepackage[latin]{babel}

% use the two following package for using normal TeX fonts
\\usepackage[T1]{fontenc}
\\usepackage[utf8]{luainputenc}

% If you use usual TeX fonts, here is a starting point:
\\usepackage{times}
% to change the font to something better, you can install the kpfonts package (if not already installed). To do so
% go open the "TeX Live Manager" in the Menu Start->All Programs->TeX Live 2010

% here we begin the document
\\begin{document}

% The title:
\\begin{center}\\begin{huge}\\textsc{INCIPITGOESHERE}\\end{huge}\\end{center}

% Here we set the space around the initial.
% Please report to http://home.gna.org/gregorio/gregoriotex/details for more details and options
\\setspaceafterinitial{2.2mm plus 0em minus 0em}
\\setspacebeforeinitial{2.2mm plus 0em minus 0em}

% Here we set the initial font. Change 43 if you want a bigger initial.
\\def\\greinitialformat#1{%
{\\fontsize{43}{43}\\selectfont #1}%
}

% We set red lines here, comment it if you want black ones.
\\redlines

% We set Mode above the initial.
\\gresetfirstlineaboveinitial{\\small \\textsc{\\textbf{MODEGOESHERE}}}{\\small \\textsc{\\textbf{MODEGOESHERE}}}

% We type a text in the top right corner of the score:
\\commentary{{\\small \\emph{Cf. Is. 30, 19 . 30 ; Ps. 79}}}

% and finally we include the score.
SCOREGOESHERE
'''        
        
    def substituteInfo(self, converter):
        r'''
        Puts the correct information into the TeXWrapper for the document
        
        
        >>> wrapper = alpha.chant.DefaultTeXWrapper()
        >>> class Converter():
        ...    score = r'\note{C}' + "\n" + r'\endgregorioscore %' + "\n" + r'\endinput %'
        ...    incipit = 'Gaudeamus Omnes'
        ...    mode = 'VII'
        ...    paperType = None
        >>> c = Converter()
        >>> print(wrapper.substituteInfo(c))
        % !TEX TS-program = lualatex
        % !TEX encoding = UTF-8
        ...
        \geometry{letterpaper} % a4paper or letterpaper (US) or a5paper or other 
        ...
        % The title:
        \begin{center}\begin{huge}\textsc{Gaudeamus Omnes}\end{huge}\end{center}
        ...
        % We set Mode above the initial.
        \gresetfirstlineaboveinitial{\small \textsc{\textbf{VII}}}{\small \textsc{\textbf{VII}}}
        ...
        % and finally we include the score.
        \note{C}
        \endgregorioscore %
        \end{document}
        \endinput %...
        '''
        score = converter.score
        incipit = converter.incipit
        mode = converter.mode
        paperType = converter.paperType
        if paperType is None:
            paperType = 'letterpaper'
        
        wrapper = self.baseWrapper
        wrapper = wrapper.replace(r'SCOREGOESHERE', score)
        wrapper = re.sub(r'INCIPITGOESHERE', incipit, wrapper)
        wrapper = re.sub(r'MODEGOESHERE', mode, wrapper)
        wrapper = re.sub(r'PAPERTYPEGOESHERE', paperType, wrapper)
        wrapper = re.sub(r'\\endinput %', r'\end{document}' + "\n" + r'\endinput %', wrapper)
        return wrapper
   
        
    
class ChantException(exceptions21.Music21Exception):
    pass
 
 

class Test(unittest.TestCase):
    pass

    def runTest(self):
        pass

class TestExternal(unittest.TestCase):
    pass

    def runTest(self):
        pass
    
    def testSimpleFile(self):
        s = GregorianStream()
        s.append(clef.AltoClef())
    
        n = GregorianNote("C4")
        l = note.Lyric("Po")
        l.syllabic = "start"
        n.lyrics.append(l)
        n.oriscus = True
        s.append(n)
        n2 = GregorianNote("D4")
        s.append(n2)
        n3 = GregorianNote("C4")
        n3.stropha = True
        s.append(n3)
        n4 = GregorianNote("B3")
        n4.stropha = True
        s.append(n4)

        gabcText = s.toGABCText()
        bsc = BaseScoreConverter()
        bsc.score = gabcText
        bsc.incipit = "Populus"
        bsc.mode = 'VII'
        fn = bsc.writeFile("style: modern;\n\n%%\n" + gabcText)
        texfn = bsc.launchGregorio(fn)
        texfh = open(texfn)
        texcontents = texfh.read()
        texfh.close()
        bsc.score = texcontents
        dtw = DefaultTeXWrapper()
        newgabcText = dtw.substituteInfo(bsc)
        texfh2 = open(texfn, 'w')
        texfh2.write(newgabcText)
        texfh2.close()
        pdffn = bsc.launchLaTeX(texfn)
        os.system('open %s' % pdffn)
        


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    import music21
    music21.mainTest(TestExternal)

#------------------------------------------------------------------------------
# eof
