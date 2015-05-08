# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         clercqTemperley.py
# Purpose:      Demonstration of using music21 to parse Clercq-Temperley's
#               popular music flavor of RomanText
#
# Authors:      Beth Hadley
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Parses the de Clercq-Temperley popular music flavor of RomanText.
The Clercq-Temperley file format and additional rock corpus analysis
information may be located at http://theory.esm.rochester.edu/rock_corpus/

'''
import re
import copy
import unittest
from music21 import exceptions21


#clercqTemperley test files used as tests throughout this module
BlitzkriegBopCT = '''
% Blitzkrieg Bop

BP: I | IV V | %THIS IS A COMMENT
In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4
Vr: $BP*3 I IV | I |
Br: IV | | I | IV I | IV | | ii | IV V |
Co: R |*4 I |*4
S: [A] $In $Vr $Vr $Br $Vr $Vr $Br $Vr $Vr $Co
'''

RockClockCT = '''
% Rock Around the Clock
% just a general comment
In: I | | | | | | V | |
Vr: I | | | | IVd7 | | I | | V7 | | I | | %a comment on verse
Vrf: I | | | | IVd7 | | I | | V7 | | I | IV iv | V | . I |
S: [A] $In $Vr $Vr $Vr $Vr $Vr $Vr $Vrf    % 3rd and 6th verses are instrumental
'''
textString = '''
% Simple Gifts 
% A wonderful shaker melody 
Vr: I | I | %incomplete verse 
S: [A] $Vr % Not quite finished!'''

exampleClercqTemperley =  '''
% Brown-Eyed Girl

VP: I | IV | I | V |
In: $VP*2
Vr: $VP*4 IV | V | I | vi | IV | V | I | V |       % Second part of verse could be called chorus
Ch: V | | $VP*2 I |*4 
Ch2: V | | $VP*3     % Fadeout
S: [G] $In $Vr $Vr $Ch $VP $Vr $Ch2
'''
RingFireCT = '''
% Ring Of Fire

In: [3/4] I . IV | [4/4] I | [3/4] . . V7 | [4/4] I |
Vr: I . . IV | [3/4] I . IV | [4/4] I | . . . V | [3/4] I . V | [4/4] I | I . . IV | [3/4] I . IV | [4/4] I | [3/4] . . V | [4/4] I |
Vr2: I . . IV | [3/4] I . IV | [4/4] I | . . . V | [3/4] I . V | [4/4] I | I . IV I | . . . IV | I | . . . V | I | % Or (alternate barring) | [3/4] I . IV | [2/4] I | [3/4] . . IV | [4/4] I | . . . V | I |
Ch: V | IV I | V | IV I | [2/4] | [4/4] . . . V | I . . V | I |       % Or the 2/4 measure could be one measure later
Fadeout: I . . V | I . . V | I . . V |
Co: [2/4] I | [4/4] . . . V | I . . V | $Fadeout
S: [G] $In $Vr $Ch $In*2 $Ch $Vr2 $Ch $Ch $Co
'''
def _convertTextFileToCTString(fileName):
    '''
    Called when a CTSong is created by passing a filename; opens the file
    and removes all blank lines, and adds in new line characters
    returns pieceString that CTSong can parse.
    '''
    fileOpened = open(fileName, 'r')
            
    pieceString = ""
    for l in fileOpened:
        line = str(l).strip()
        if len(line) > 0:
            pieceString = pieceString + line.strip() + ' ' + '\n'
    
    return pieceString

class CTSongException(exceptions21.Music21Exception):
    pass

class CTSong(object):
    r"""
    This parser is an object-oriented approach to parsing clercqTemperley text files into music.
    
    Create a CTSong object one of two ways:
    1) by passing in the string, with newline characters (\\n) at the end of each line
    2) by passing in the text file as a string, and have python open the file and read the text
    #_DOCS_HIDE Please note: the backslashes included in the file below are for sphinx documentation
    #_DOCS_HIDE purposes only. They are not permitted in the clercq-temperley file format   

    ::

        >>> exampleClercqTemperley = '''
        ... % Brown-Eyed Girl
        ... VP: I \| IV \| I \| V \|
        ... In: $VP\*2
        ... Vr: $VP\*4 IV \| V \| I \| vi \| IV \| V \| I \| V \|       % Second part of verse could be called chorus
        ... Ch: V \| \| $VP\*2 I \|\*4 
        ... Ch2: V \| \| $VP\*3     % Fadeout
        ... S: [G] $In $Vr $Vr $Ch $VP $Vr $Ch2
        ... '''
        
    ::

        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.exampleClercqTemperley) #_DOCS_HIDE
        >>> #_DOCS_SHOW s = romanText.clercqTemperley.CTSong('C:/Brown-Eyed_Girl.txt')
    
    When you call the .toScore() method on the newly created CTSong object,
    the code extracts meaningful properties (such as title, text, comments,
    year, rules, home time Signature, and home Key Signature) from the textfile
    and makes these accessible as below.
    
    The toScore() method has two optional labeling parameters, labelRomanNumerals and 
    labelSubsectionsOnScore. Both are set to True by default. Thus, the created score
    will have labels (on the chord's lyric) for each roman numeral as well as for each 
    section in the song (LHS). In case of a recursive definition (a rule contains a reference
    to another rule), both labels are printed, with the deepest reference on the smallest lyric line.

    ::
    
        >>> #_DOCS_SHOW s.toScore().show()
        
    .. image:: images/ClercqTemperleyExbrown-eyed_girl.png
       :width: 500
    
    ::

        >>> s.title
        'Brown-Eyed Girl'

    ::

        >>> s.homeTimeSig
        <music21.meter.TimeSignature 4/4>

    ::

        >>> s.homeKeySig
        <music21.key.Key of G major>

    ::

        >>> s.comments
        [['Vr:', 'Second part of verse could be called chorus'], ['Ch2:', 'Fadeout']]
        
    Year is not defined as part of the clercq-temperley format, but it will be helpful
    to have it as a property. So let's assign a year to this song:
    
    ::

        >>> s.year = 1967
        >>> s.year
        1967
    
    Upon calling toScore(), CTRule objects are also created. CTRule objects are
    the individual rules that make up the song object. For example,
    
    ::

        >>> s.rules
        [<music21.CTRule.CTRule text = VP: I | IV | I | V | , <music21.CTRule.CTRule text = In: $VP*2 , <music21.CTRule.CTRule text = Vr: $VP*4 IV | V | I | vi | IV | V | I | V |       % Second part of verse could be called chorus , <music21.CTRule.CTRule text = Ch: V | | $VP*2 I |*4  , <music21.CTRule.CTRule text = Ch2: V | | $VP*3     % Fadeout ]

    The parser extracts meaningful properties to each rule, such as sectionName,
    home time signature of that rule, home key of that rule, and of course the individual
    stream from the song corresponding to the rule.

    The following examples display the instantiated properties of the second rule (list indexes
    start at one) as created above.

    ::

        >>> rule = s.rules[1]
        >>> rule.text
        'In: $VP*2'

    ::

        >>> rule.sectionName
        'Introduction'

    ::

        >>> rule.homeTimeSig
        <music21.meter.TimeSignature 4/4>



    Note that the rule.homeKeySig will be different after calling song.toStream() which will
    apply the key signature of G major everywhere:
    
    ::

        >>> rule.homeKeySig
        <music21.key.Key of C major>

    ::

        >>> #_DOCS_HIDE assert(rule.streamFromCTSong().highestOffset == 28.0)
        >>> #_DOCS_SHOW rule.streamFromCTSong().show()
    
    .. image:: images/ClercqTemperleyIntroduction.png
       :width: 500
    
    With this object-oriented approach to parsing the clercq-temperley text file format, 
    we now have the ability to analyze a large corpus (200 files) of popular music
    using the full suite of harmonic tools of music21. We can not only analyze each
    song as a whole, as presented in Clercq and Temperley's research, but we can also analyze each
    individual section (or rule) of a song. This may provide interesting insight
    into popular music beyond our current understanding.
    
    Examples used throughout this class utilize the following Clercq-Temperley text file
    
    #_DOCS_HIDE Please note: the backslashes included in the file below are for sphinx documentation
    #_DOCS_HIDE purposes only. They are not permitted in the clercq-temperley file format   

    ::
 
        >>> BlitzkriegBopCT = '''
        ... % Blitzkrieg Bop
        ... BP: I \| IV V \| %THIS IS A COMMENT
        ... In: $BP\*3 I IV \| I \| $BP\*3 I IV \| I \| R \|\*4 I \|\*4
        ... Vr: $BP\*3 I IV \| I \|
        ... Br: IV \| \| I \| IV I \| IV \| \| ii \| IV V \|
        ... Co: R \|\*4 I \|\*4
        ... S: [A] $In $Vr $Vr $Br $Vr $Vr $Br $Vr $Vr $Co
        ... '''
    
    OMIT_FROM_DOCS
    
    Another example using a different Clercq-Temperley file
    
    ::

        RockClockCT = 
        % Rock Around the Clock
        % just a general comment
        In: I | | | | | | V | |
        Vr: I | | | | IVd7 | | I | | V7 | | I | | %a comment on verse
        Vrf: I | | | | IVd7 | | I | | V7 | | I | IV iv | V | . I |
        S: [A] $In $Vr $Vr $Vr $Vr $Vr $Vr $Vrf    % 3rd and 6th verses are instrumental

    ::

        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.RockClockCT)
        >>> s.toScore().highestOffset
        374.0 

    ::

        >>> s.title
        'Rock Around the Clock'

    ::

        >>> s.homeTimeSig
        <music21.meter.TimeSignature 4/4>

    ::

        >>> s.homeKeySig
        <music21.key.Key of A major>

    ::

        >>> s.comments
        [['just a general comment'], ['Vr:', 'a comment on verse'], ['S:', '3rd and 6th verses are instrumental']]

    ::

        >>> s.year = 1952
        >>> s.year
        1952

    ::

        >>> s.rules
        [<music21.CTRule.CTRule text = In: I | | | | | | V | | , <music21.CTRule.CTRule text = Vr: I | | | | IVd7 | | I | | V7 | | I | | %a comment on verse , <music21.CTRule.CTRule text = Vrf: I | | | | IVd7 | | I | | V7 | | I | IV iv | V | . I | ]

    ::

        >>> rule = s.rules[0]
        >>> rule.text
        'In: I | | | | | | V | |'

    ::

        >>> rule.sectionName
        'Introduction'

    ::

        >>> rule.homeTimeSig
        <music21.meter.TimeSignature 4/4>

    ::

        >>> rule.homeKeySig
        <music21.key.Key of A major>

    ::

        >>> rule.streamFromCTSong().highestOffset
        28.0
    
    one more example...the bane of this parser's existence...

    ::
        
        % Ring Of Fire
        
        In: [3/4] I . IV | [4/4] I | [3/4] . . V7 | [4/4] I |
        Vr: I . . IV | [3/4] I . IV | [4/4] I | . . . V | [3/4] I . V | [4/4] I | I . . IV | [3/4] I . IV | [4/4] I | [3/4] . . V | [4/4] I |
        Vr2: I . . IV | [3/4] I . IV | [4/4] I | . . . V | [3/4] I . V | [4/4] I | I . IV I | . . . IV | I | . . . V | I |
                                                % Or (alternate barring) | [3/4] I . IV | [2/4] I | [3/4] . . IV | [4/4] I | . . . V | I |
        Ch: V | IV I | V | IV I | [2/4] | [4/4] . . . V | I . . V | I |       % Or the 2/4 measure could be one measure later
        Fadeout: I . . V | I . . V | I . . V |
        Co: [2/4] I | [4/4] . . . V | I . . V | $Fadeout
        S: [G] $In $Vr $Ch $In*2 $Ch $Vr2 $Ch $Ch $Co


    """
    _DOC_ORDER = ['text', 'toScore', 'title', 'homeTimeSig', 'homeKeySig', 'comments', 'appendComment', 'rules']
    _DOC_ATTR = {'year': 'the year of the CTSong; not formally defined by the Clercq-Temperley format'}
                 
    
    def __init__(self, textFile, **keywords):
        self.text = textFile
        self._title = None
        self.year = None
        self._rules = [] #list of all component rules of the type CTRule
        self._homeTimeSig = None
        self._homeKeySigSig = None
        self._comments = []
        #self._text = "" # CUTHBERT cannot initialize this here
        

        for kw in keywords:
            if kw == 'title':
                self._title = kw
            if kw == 'year':
                self.year = kw
    
    def __repr__(self):
        return '<music21.CTSong.%s text = %s title=%s year=%s' % (self.__class__.__name__, self.text, self.title, self.year)

    #---------------------------------------------------------------------------
    
    def _setText(self, value):
        if '|' in value and 'S:' in value:
            self._text = value
        else:
            try:
                self._text = _convertTextFileToCTString(value)
            except:  
                raise CTSongException('Invalid File Format; must be string or text file: %s' % value)
                
    def _getText(self):
        return self._text
    
    text = property (_getText, _setText, doc = '''
Get the text of the CTSong.

This is the full text of the Clercq-Temperley file. This
attribute is typically instantiated when the CTSong object is created, either by passing 
in the full string, with newline characters (\n) at the end of each line or by passing 
in the text file as a string, and have python do the parsing.
''')
   
    
    def _setTitle(self, value):
        if isinstance(value, str):
            self._title = str(value)
        else:
            raise CTSongException('not a valid title; must be string: %s' % value)
    def _getTitle(self):
        if self._title == None or self._title == '':
            if self.text:
                lines = self.text.split('\n')
                for x in lines:
                    line = str(x).strip()
                    if "%" in line:
                        pieceTitle = line
                        pieceTitle = pieceTitle.replace('%', '').strip()
                        self._title = pieceTitle
                        return self._title
                    elif len(line) > 0 and '|' in line:
                        self._title = ''
                        return self._title
        else:
            return self._title

    title = property(_getTitle, _setTitle, doc= '''
        Get or set the title of the CTSong. If not specified explicitly but the clercq-Temperley text exists, 
        this attribute searches first few lines of text file for title (a string preceded by a '%') 
        if found, sets title attribute to this string and returns this title)
        
        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.textString)
        >>> s.title
        'Simple Gifts'
        ''')

    def _setComments(self, value):
        if isinstance(value, list):
            self._comments = value
        else:
            raise CTSongException('not a valid comment list: %s' % value)
        
    def _getComments(self):
        comments = []
        if self._comments == None or self._comments == []:
            lines = self.text.split('\n')
            for line in lines:
                if line == '' or line == None:
                    lines.remove(line)
            for line in lines[1:]:
                if "%" in line:
                    if line.split()[0].endswith(':'):
                        comments.append([ line.split()[0] , (line[line.index('%')+1:].strip()) ] )
                    else:
                        comments.append([ line[line.index('%')+1:].strip() ])
            self._comments = comments
            return self._comments
        else:
            return self._comments
    
    def appendComment(self, value):
        r"""
        append a comment to self.text at the end of the text file. Only strings or lists of strings are
        acceptible to append to the text file. this list of comments (self.comments) is also appended
        #_DOCS_HIDE Please note: the backslashes included in the file below are for sphinx documentation
        #_DOCS_HIDE purposes only. They are not permitted in the clercq-temperley file format   
            
            | textString = '''
            | %Simple Gifts
            | % A wonderful shaker melody
            | Vr: I \| I \| %incomplete verse
            | S: [A] $Vr % Not quite finished!'''

        
        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.textString)
        >>> s.comments
        [['A wonderful shaker melody'], ['Vr:', 'incomplete verse'], ['S:', 'Not quite finished!']]
        >>> s.appendComment('please append this comment to list')
        >>> s.comments
        [['A wonderful shaker melody'], ['Vr:', 'incomplete verse'], ['S:', 'Not quite finished!'], 'please append this comment to list']
        """
        try:
            self._comments.append(value)
            if isinstance(value, str) and value != '':
                self.text = self.text + ' %' + str(value)
            elif isinstance(value, list):
                for x in value:
                    self.text = self.text + ' % ' + str(x)
        except:
            raise CTSongException('not a valid comment to append (must be a string or list): %s' % value)
        
    comments = property(_getComments, _setComments, doc= r"""
        Get or set the comments list of a CTRule object. setting comments does not alter self.text
    
        comments are stored as a list of comments, each comment on a line as a list. If the
        comment is on a rule line, the list contains both the line's LHS (like In:) and the comment
        if the comment is on a line of its own, only the comment is appended as a list of length one.
        
        The title is not a comment. The title is stored under self.title
        #_DOCS_HIDE Please note: the backslashes included in the file below are for sphinx documentation
        #_DOCS_HIDE purposes only. They are not permitted in the clercq-temperley file format   

            | textString = '''
            | %Simple Gifts
            | % A wonderful shaker melody
            | Vr: I \| I \| %incomplete verse
            | S: [A] $Vr % Not quite finished!'''
        
        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.textString)
        >>> s.comments
        [['A wonderful shaker melody'], ['Vr:', 'incomplete verse'], ['S:', 'Not quite finished!']]
        
        >>> s.comments = ['a new list of comments']
        >>> s.comments
        ['a new list of comments']
        >>> s.appendComment('please append this comment to list')
        >>> s.comments
        ['a new list of comments', 'please append this comment to list']

        """)


    def _setRules(self, value):
        self._rules = value
    
    def _getRules(self):
        if self._rules == None or self._rules == []:
            lines = self.text.split('\n')
            for line in lines:
                if not line == '':
                    if line.split()[0].endswith(':') and 'S:' not in line: #or 'S:' in line Let's not include 'Song' line for now...
                        self._rules.append(CTRule(line))
            return self._rules
        else:
            return self._rules


    rules = property(_getRules, _setRules, doc= '''
        Get the rules of a CTSong. the Rules is a list of objects of type CTRule. If only a textfile
        provided, this goes through text file and creates the rule object out of each line containing
        a LHS...NOT including the Song line
        
        
        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.BlitzkriegBopCT)
        >>> len(s.rules)
        5
        >>> for rule in s.rules:
        ...   print(rule.LHS)
        BP
        In
        Vr
        Br
        Co
        ''')
    
    
    def _setHomeTimeSig(self, value):
        from music21 import meter
        if hasattr(value, 'classes') and 'TimeSignature' in value.classes:
            self._homeTimeSig = value
            return
        try:
            self._homeTimeSig = meter.TimeSignature(value)
            return
        except:
            raise CTSongException('not a valid time signature: %s' % value)

    def _getHomeTimeSig(self):
        from music21 import meter
        #look at 'S' Rule and grab the home time Signature
        if self.text and 'S:' in self.text:
            lines = self.text.split('\n')
            for line in lines:
                if line.startswith('S:'):
                    for atom in line.split()[1:3]:
                        if '[' not in atom:
                            self._homeTimeSig = meter.TimeSignature('4/4')
                            return self._homeTimeSig
                        elif '/' in atom:
                            self._homeTimeSig = meter.TimeSignature(atom[1:-1])
                            return self._homeTimeSig
                        else:
                            pass
        return self._homeTimeSig
    
    homeTimeSig = property(_getHomeTimeSig, _setHomeTimeSig, doc = '''
        gets the initial, or 'home', time signature in a song by looking at the 'S' substring
        and returning the provided time signature. If not present, returns a default music21
        time signature of 4/4
        
        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.textString)
        >>> s.homeTimeSig
        <music21.meter.TimeSignature 4/4>
                 
        ''')
    

    def _setHomeKeySig(self, value):
        from music21 import key
        if hasattr(value, 'classes') and 'Key' in value.classes:
            self._homeKeySigSig = value
            return
        try:
            m21keyStr = key.convertKeyStringToMusic21KeyString(value)
            self._homeKeySigSig = key.Key(m21keyStr)
            return
        except:
            raise CTSongException('not a valid key signature: %s' % value)

    def _getHomeKeySig(self):
        from music21 import key
        #look at 'S' Rule and grab the home key Signature
        if self.text and 'S:' in self.text:
            lines = self.text.split('\n')
            for line in lines:
                if line.startswith('S:'):
                    for atom in line.split()[1:3]:
                        if '[' not in atom:
                            self.homeKeySig = key.Key('C')
                            return self._homeKeySigSig
                        elif not '/' in atom:
                            m21keyStr = key.convertKeyStringToMusic21KeyString(atom[1:-1])
                            self._homeKeySigSig = key.Key(m21keyStr)
                            return self._homeKeySigSig
                        else:
                            pass
        return self._homeKeySigSig
    
    homeKeySig = property(_getHomeKeySig, _setHomeKeySig, doc = '''
        gets the initial, or 'home', key signature by looking at the musictext and locating
        the key signature in the first few characters in the song rule. A key signature in the song
        rule might look like this: S: [A] $In $Vr
        
        
        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.textString)
        >>> s.homeKeySig
        <music21.key.Key of A major>
        ''')
    
    #---------------------------------------------------------------------------------
    #HELPER METHODS FOR .toScore method
    
    def _stringhasDotsandBars(self, expressionString):
        '''
        returns true if expressionString contains both bars (|), dots (.), and the
        '[' which signifies either a change in time or key signature. Method is
        necessary because if both bars and dots are present, parser must be careful
        about time signatures nested within, and also tied chords (implied by the dot)
        vs. repeated by untied chords (implied by the bar)
        '''
        
        split = expressionString.split()
        if split.count('|') > 1 and split.count('.') > 1 and expressionString.count('[') > 1:
            return True
        else:
            return False

    def _getDuration(self, containsIndex, entireSplitString, timeSig):
        '''
        returns duration (in quarterLength) of any single character passed to it 
        (whose index in entireSplitString is specified by containsIndex) 
        entireSplitString is the entire textfile split by spaces. timeSig is the time
        signature the character being analyzed is in
    
        '''
        from music21 import meter
        
        starters = ['I', '#', 'B', 'V', 'R', '.']
        starters2 = ['I', '#', 'B', 'V', 'R', '.', '[']
        searchlocation = containsIndex - 1
        previouschar = entireSplitString[searchlocation]
        measureContents = []
        atomBeingSearched = entireSplitString[containsIndex]
        if atomBeingSearched[0].upper() in starters and not atomBeingSearched.endswith(':'):
            while previouschar[0].upper() in starters2 and not previouschar.endswith(':'):
                if previouschar.startswith('[') and "/" in previouschar:
                    timeSig = meter.TimeSignature(previouschar[1:-1])
                elif previouschar.startswith('['): #could be a key
                    pass
                else:
                    measureContents.append(previouschar)
                searchlocation = searchlocation - 1
                previouschar = entireSplitString[searchlocation]
            measureContents.reverse()
            searchlocation = containsIndex + 1
        
            nextChar = entireSplitString[searchlocation]
            measureContents.append(entireSplitString[containsIndex])
            while nextChar[0].upper() in starters2 and not nextChar.endswith(':'):
                if not '*' in nextChar and not nextChar.startswith('['):
                    measureContents.append(nextChar)
                searchlocation = searchlocation + 1
                nextChar = entireSplitString[searchlocation]
        
        if len(measureContents) > 0:
            duration = timeSig.totalLength  / len(measureContents)
        else:
            duration = 0   
        return duration

    def _getStringWithBarsandDots(self, containsIndex, entireSplitString):
        '''
        given an index which corresponds to a charcter in the entireSplitString, method
        returns the surrounding bars and dots (if they exist) that correspond to
        that character.
        '''
        if entireSplitString[containsIndex - 1].startswith('['):
            expressionString = entireSplitString[containsIndex - 1] + ' '
            if entireSplitString[containsIndex - 2].startswith('['):
                expressionString = expressionString + entireSplitString[containsIndex - 2] + ' '
        else:
            expressionString = ''
        expressionString = expressionString + entireSplitString[containsIndex] + ' '
        searchlocation = containsIndex + 1
        nextChar = entireSplitString[searchlocation]
        while (nextChar == '|' or nextChar == '.' or (nextChar.startswith('[') and '/' in nextChar)) and len(entireSplitString) > searchlocation + 1:
            expressionString = expressionString + nextChar + ' '
            searchlocation = searchlocation + 1
            nextChar = entireSplitString[searchlocation]
        #print expressionString
        s = expressionString.split()
        if s.count('|') > 1 or s.count('.') > 0:
            if '/' in s[-1]:
                s.pop()      
            return ' '.join(s)
        else:
            return ""

    def _barIsDouble(self, indexofbar, expressionString):
        '''
        returns true if the expressionString contains double bars (a repeated roman numeral)
        '''
        expressionString = expressionString.split()
        count = 0
        index = indexofbar
        atom = expressionString[index]
        while (atom == '|' or atom.startswith('[')) and len(expressionString) > index:
            if atom == '|':
                count = count + 1
            index = index + 1
            try:
                atom = expressionString[index]
            except IndexError:
                pass
        if count > 1:
            return True
        else:
            return False

    def _getStreamWithBarsandDots(self, indexofatom, expressionString, splitFile, atom, currentKey, timeSig):
        '''
        a very ugly method, and all the methods it calls are also very ugly. A messy solution to 
        dealing roman numerals with bars and dots after it, but this method is necessary to deal
        with possible changes in key or time signature found embedded within the string.
        
        If there's a parsing error related to missing key signatures or time signatures, 
        it's probably here or in the methods this method depends on.
        '''
        from music21 import stream
        from music21 import meter
        from music21 import key
        from music21 import roman
        from music21 import tie
        
        outputStream = stream.Stream()
        index = -1
        starters = ['I', '#', 'B', 'V']
        dur = 0
        pleaseAppend = False
        for x in expressionString.split():
            index = index + 1
            if expressionString:
                if x.startswith('[') and "/" in x:
                    timeSig = meter.TimeSignature(x[1:-1])
                    outputStream.append(timeSig)
                elif x.startswith('['):
                    m21keyStr = key.convertKeyStringToMusic21KeyString(x[1:-1])
                    currentKey = key.Key(m21keyStr)
                    outputStream.append(currentKey)
                elif x[0].upper() in starters:
                    rn = roman.RomanNumeral(atom, currentKey)
                    rn.duration.quarterLength = self._getDuration(indexofatom, splitFile, timeSig)
                    outputStream.append(rn)
                    if self._stringhasDotsandBars(expressionString):
                        for x in rn.pitches:
                            rn.setTie(tie.Tie('start'), x) 
                elif x == '|':
                    if self._stringhasDotsandBars(expressionString) and expressionString.split()[index - 2] == '|' :
                        z = roman.RomanNumeral(atom, currentKey)
                        z.duration.quarterLength = timeSig.totalLength
                        outputStream.append(z)
                    elif self._barIsDouble(index, expressionString) and not self._stringhasDotsandBars(expressionString):
                        rn.duration.quarterLength = rn.duration.quarterLength + timeSig.totalLength
                elif x == '.':
                    if not self._stringhasDotsandBars(expressionString):
                        rn.duration.quarterLength = rn.duration.quarterLength + self._getDuration((indexofatom + index), splitFile, timeSig)
                    else:
                        pleaseAppend = True
                        dur = dur +  self._getDuration((indexofatom + index), splitFile, timeSig)
                        
                else:
                    pass
                
        if pleaseAppend:
            xy = roman.RomanNumeral(atom, currentKey)
            xy.duration.quarterLength = dur
            outputStream.append(xy)
        outputStream = outputStream.makeMeasures(finalBarline = None)
        
        measureNumber = 1
        for x in expressionString.split():
         
            if expressionString:
                if x.startswith('[') and "/" in x:
                    
                    timeSig = meter.TimeSignature(x[1:-1])
                    try:
                        currentTimeSig = outputStream.measure(measureNumber).flat.getElementsByClass(meter.TimeSignature)[0]
                        if str(currentTimeSig) != str(timeSig):
                            
                            outputStream.remove(currentTimeSig)
                      
                            outputStream.measure(measureNumber).insert(0.0, timeSig)
                    except IndexError:
                        try:
                            outputStream.measure(measureNumber).insert(0.0, timeSig)
                        except exceptions21.StreamException:
                            # ...handles the case that not enough measures were created
                            #by just the duration of the long note (in case of changes
                            #in time signatures, such as:
                            #I | [2/4] | [4/4] . . .
                            #where the I is really IV I in the previous measure
                            
                            newM = stream.Measure()
                            newM.timeSignature = timeSig
                            outputStream.append(newM)
                            outputStream = outputStream.makeMeasures(finalBarline = None)

                elif x == '|':
                    measureNumber = measureNumber + 1
                else:
                    pass
                    
        outputStream.makeTies()       
        return outputStream


    def _removeDuplicateKeys(self, scoreObj):
        '''
        a handy method that searches through a stream and removes any duplicated
        keys it finds..cleans up the stream a bit!
        Method called at the end of toScore()
        '''
        keyList = scoreObj.flat.getElementsByClass("KeySignature")
        index = 0
        if len(keyList) > 1:
            for x in keyList[1:]:
                index = index + 1
                if str(x) == str(keyList[index-1]):
                    scoreObj.remove(x)
        return scoreObj
        
    def _removeDuplicateMeters(self, scoreObj):
        '''
        a handy method that searches through a stream and removes any duplicated
        time signatures it finds..cleans up the stream a bit!
        method called at the end of toScore()
        '''
        timeList = scoreObj.flat.getElementsByClass("TimeSignature")
        index = 0
        if len(timeList) > 1:
            for x in timeList[1:]:
                index = index + 1
                if str(x) == str(timeList[index-1]):
                    scoreObj.remove(x)
        return scoreObj
    
    
    def _removeDuplicateClefs(self, scoreObj):
        '''
        a handy method that searches through a stream and removes any duplicated
        clefs it finds..cleans up the stream a bit!
        method called at the end of toScore()
        '''
        for x in scoreObj.flat.getElementsByClass("TrebleClef"):
            scoreObj.remove(x)
        from music21 import clef
        scoreObj.insert(0, clef.TrebleClef())
        return scoreObj

    def labelRomanNumerals(self, scoreObj):
        '''
        provided a scoreObject, labels the roman numerals on each chord.
        The CTSong.toScore() method calls this function by default unless
        labelRomanNumerals=False is passed as a parameter. Method labeling 
        doesn't relabel tied roman numeral chords.
        '''
        from music21 import roman
        lastel = roman.RomanNumeral(None, None)
        for el in scoreObj.flat.getElementsByClass("RomanNumeral"):
            if el.tie == None:
                el.insertLyric(el.figure)
            elif lastel.figure != el.figure and el.figure != None:
                el.insertLyric(el.figure)
            elif el.tie != None and el.tie.type == 'start':
                el.insertLyric(el.figure)
            else:
                pass
            lastel = el
        return scoreObj
            
    def toScore(self ,labelRomanNumerals=True, labelSubsectionsOnScore = True):
        '''
        creates Score object out of a from CTSong...also creates CTRule objects in the process,
        filling their .streamFromCTSong attribute with the corresponding smaller inner stream. 
        Individual attributes of a rule are defined by the entire CTSong, such as 
        meter and time signature, so creation of CTRule objects typically occurs
        only from this method and directly from the clercqTemperly text.
        
        
        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.BlitzkriegBopCT)
        >>> scoreObj = s.toScore()
        >>> scoreObj.highestOffset   
        380.0
    
        '''
        from music21 import stream
        from music21 import meter
        from music21 import key
        from music21 import roman
        from music21 import note
        from music21 import metadata
        
        scoreObj = stream.Stream() 
 
        allSubsections = {}
        currentSubsectionName = None
        currentSubsectionContents = None

        starters2 = ['I', '#', 'B', 'I', '#' , 'V']
        indexofatom = -1
        duration = 0
        firsttimeSigFound = False
        firstKeyFound = False
        jumpForwardIndexValue = -10 #arbitrary negative number
        homeKey = None
        currentKey = None
        homeTimeSig = None
        currentTimeSig = None
        flags = []
        putLyricOnNextItemInStream = False
        #omit the comments (denotated by '%' from the RTSong text)
        lines = self.text.split('\n')
        pieceString = ''
        for l in lines:
            line = str(l).strip()
            if "%" in line:
                temp = line[0: line.index('%')]
                if len(temp.strip()) > 0:
                    pieceString = pieceString + temp.strip() + ' ' + '\n'
            elif len(line) > 0:
                pieceString = pieceString + line.strip() + ' ' + '\n'
        splitFile = pieceString.split()
      
        #look at S string, and grab time sigs or key sigs
        #this information actually alters the rule objects,
        #which is why a CTSong is not necessarily the sum of its CTRules!
        for x in splitFile[splitFile.index('S:') : splitFile.index('S:') + 3]:
            atomContents = x[1:-1]
            if x.startswith('[') and '/' in x:
                homeTimeSig = meter.TimeSignature(atomContents)
                self._homeTimeSig = homeTimeSig
                firsttimeSigFound = True
            elif x.startswith('[') and not '/' in x:
                m21keyStr = key.convertKeyStringToMusic21KeyString(atomContents)
                homeKey = key.Key(m21keyStr)
                self._homeKeySigSig = homeKey
                firstKeyFound = True
        if firsttimeSigFound == False:
            homeTimeSig = meter.TimeSignature('4/4')
             
        if firstKeyFound == False:
            homeKey = key.Key('C')
            #if no key set, make homeKey C Major
            
        #now just check to make sure time sig doesn't change in main strain....should
        #I do the same for Key????
        timeSigList = []
        for x in splitFile[splitFile.index('S:') :]:
            if '[' in x and '/' in x:
                timeSigList.append([splitFile[splitFile.index(x) + 1], x[1:-1]])
        
        for atom in splitFile:
            indexofatom = indexofatom + 1
            for element, temptime in timeSigList:
                if atom.replace(':','') == element.replace('$',''):
                    currentTimeSig = meter.TimeSignature(temptime)
                    
            if indexofatom < jumpForwardIndexValue:
                if atom.startswith('[') and atom.endswith(']'):
                    atomContents = atom[1:-1]
                    if re.match('[a-zA-Z]', atomContents):
                        m21keyStr = key.convertKeyStringToMusic21KeyString(atomContents)
                        currentKey = key.Key(m21keyStr)
                    else: 
                        currentTimeSig = meter.TimeSignature(atomContents)
                continue
    
            else:
                if atom.endswith(':'):
                    for label, subsectionToAppendName, offset in flags:
                        if '*' in label:
                            x = label[1: label.index('*')]
                        if x in allSubsections:
                            referencedSubsection = label[1:]
                            match = re.search(r'^(.*)\*(\d+)', referencedSubsection)
                            if match:
                                numRepeat = int(match.group(2))
                                referencedSubsection = match.group(1)
                            else:
                                numRepeat = 1
                            tempStream = stream.Stream()
                            for i in range(numRepeat):
                                for refEl in allSubsections[referencedSubsection]:
                                    tempStream.append(copy.deepcopy(refEl))
                            offsety = offset
                            for y in tempStream:
                                allSubsections[subsectionToAppendName].insertAndShift(offsety+1, y)
                                offsety = offsety + 1
                            flags.remove([label, subsectionToAppendName, offset])
                    if currentSubsectionName is not None:
                        allSubsections[currentSubsectionName] = currentSubsectionContents
                    currentSubsectionName = atom[0:-1]
                    if currentSubsectionName.upper() == 'S':
                        # special, score object
                        currentSubsectionName = 'S'
                        currentSubsectionContents = scoreObj
                    else:
                        currentSubsectionContents = stream.Stream()
                        if labelSubsectionsOnScore:
                            putLyricOnNextItemInStream = True
                            
                        keySigAtom = splitFile[indexofatom + 1]
                        if not keySigAtom.startswith('[') and not keySigAtom.endswith(']') or '/' in keySigAtom: 
                            currentSubsectionContents.append(homeKey)  
                        
                        for x in splitFile[indexofatom + 1: indexofatom + 2]:
                            if not x.startswith('[') and not x.endswith(']') and not '/' in x:                        
                                currentSubsectionContents.append(homeTimeSig)                        
                        currentKey = homeKey             
                        currentTimeSig = homeTimeSig 
    
                elif atom.startswith('$'):
                    referencedSubsection = atom[1:]
                    match = re.search(r'^(.*)\*(\d+)', referencedSubsection)
                    if match:
                        numRepeat = int(match.group(2))
                        referencedSubsection = match.group(1)
                    else:
                        numRepeat = 1
                    
                    if referencedSubsection not in allSubsections:
                        flags.append([atom, currentSubsectionName, currentSubsectionContents.highestOffset])
                    else:
                        for i in range(numRepeat):
                            for refEl in allSubsections[referencedSubsection]:
                                currentSubsectionContents.append(copy.deepcopy(refEl))
                elif atom.startswith('|*'):
                    repetitions = int(atom[2:])
                    myScoreTemp = currentSubsectionContents.makeMeasures()
                    mList = myScoreTemp.getElementsByClass('Measure')
                    for i in range(repetitions - 1):
                        for x in mList[len(mList) - 1].notesAndRests:
                            if x.isClassOrSubclass([roman.RomanNumeral]):
                                try:
                                    del x.lyrics
                                except AttributeError:
                                    pass
                            currentSubsectionContents.append(copy.deepcopy(x))
        
                elif atom.startswith('[') and atom.endswith(']'):
                    atomContents = atom[1:-1]
                    if re.match('[a-zA-Z]', atomContents):
                        m21keyStr = key.convertKeyStringToMusic21KeyString(atomContents)
                        currentKey = key.Key(m21keyStr)
                        currentSubsectionContents.append(currentKey)
                    else:
                        currentTimeSig = meter.TimeSignature(atomContents)
                        currentSubsectionContents.append(currentTimeSig)
                elif atom == 'R':
                    if currentTimeSig == None:
                        currentTimeSig = meter.TimeSignature('4/4')
                    qlenrest = self._getDuration(indexofatom, splitFile, currentTimeSig)
                    r1 = note.Rest(quarterLength=qlenrest)
                    currentSubsectionContents.append(r1) 
                elif atom[0].upper() in starters2 and not atom.endswith(':'):
                    originalAtom = atom
                    if 'x' in atom:
                        atom = atom.replace('x', 'o')
                    if 'h' in atom:
                        atom = atom.replace('h', '/o')
                    if atom[0].islower() and 'a' in atom:
                        atom = atom.replace('a', '+')
        
                    expressionString = self._getStringWithBarsandDots(indexofatom, splitFile)
        
                    if len(expressionString) > 0:
                        streamToAppend = self._getStreamWithBarsandDots(indexofatom, expressionString, splitFile, atom, currentKey, currentTimeSig)
                        jumpForwardIndexValue = len(expressionString.split()) - expressionString.split().index(originalAtom) + indexofatom
                        currentSubsectionContents.append(streamToAppend.flat.elements) 
                    else:
                        duration = self._getDuration(indexofatom, splitFile, currentTimeSig)
                        try:
                            rn = roman.RomanNumeral(atom, currentKey)
                            rn.duration.quarterLength = duration
                            currentSubsectionContents.append(rn)
                        except:
                            raise CTSongException('invalid character found: %s' % atom)     
                else:
                    #should skip all bar lines and dots...
                    if atom != '|' and atom != '.':
                        raise CTSongException('invalid character found: %s' % atom)               
               
                
            listofRomans = currentSubsectionContents.flat.getElementsByClass(roman.RomanNumeral)
            if putLyricOnNextItemInStream and len(listofRomans) >= 1:
                listofRomans[0].addLyric(currentSubsectionName)
                putLyricOnNextItemInStream = False      
                    
        for streamKey in allSubsections:
            for CTRuleObject in self.rules:
                if CTRuleObject.LHS == streamKey:
                    allSubsections[streamKey] = self._removeDuplicateClefs(allSubsections[streamKey])
                    allSubsections[streamKey] = self._removeDuplicateMeters(allSubsections[streamKey])                                          
                    allSubsections[streamKey] = self._removeDuplicateKeys(allSubsections[streamKey])
                    if labelRomanNumerals:
                        allSubsections[streamKey] = self.labelRomanNumerals(allSubsections[streamKey])
                    CTRuleObject._streamFromCTSong = allSubsections[streamKey]    
        
        #scoreObj.subsections = allSubsections #not really sure what this line does...
      
        #needs to be done a second time...this time on whole Score Object
        if labelRomanNumerals:
            scoreObj = self.labelRomanNumerals(scoreObj)
        scoreObj = self._removeDuplicateClefs(scoreObj)
        scoreObj = self._removeDuplicateKeys(scoreObj)
        scoreObj = self._removeDuplicateMeters(scoreObj)
        
        scoreObj.insert(metadata.Metadata()) 
        scoreObj.metadata.title = self.title

        return scoreObj

class CTRuleException(exceptions21.Music21Exception):
    pass
        
class CTRule(object):
    '''
    CTRule objects correspond to the individual lines defined in a 
    :class:`~music21.romanText.clercqTemperley.CTSong` object. They are typically
    created by the parser after a CTSong object has been created and the .toScore() method
    has been called on that object. The usefullness of each CTRule object is that each 
    has a :meth:`~music21.romanText.clercqTemperley.CTRUle.streamFromCTSong` attribute, 
    which is the stream from the entire score that the rule corresponds to.
    '''
    _DOC_ORDER = ['LHS', 'sectionName','musicText', 'homeTimeSig', 'homeKeySig', 'comments', 'appendComment']
    _DOC_ATTR = {'text': 'the full text of the CTRule, including the LHS, chords, and comments'}
     
    def __init__(self, text = '', **keywords):
        self.text = text #FULL TEXT OF CTRULE (includes LHS, chords, and comments
        self._comments = []
        self._musicText = None #just the text above without the rule string or comments
        self._LHS = None #rule string
        self._sectionName = None #nice name of LHS
        self._homeTimeSig = None
        self._homeKeySig = None
        self._streamFromCTSong = None
  
    def __repr__(self):
        return '<music21.CTRule.%s text = %s ' % (self.__class__.__name__, self.text)
    #---------------------------------------------------------------------------
    def _setMusicText(self, value):
        self._musicText = str(value)
         
    def _getMusicText(self):
        if self._musicText == None or self._musicText == '':
            text = ''
            stillOnLHS = True
            if self.text:
                for char in self.text:
                    if char != ':' and stillOnLHS:
                        continue
                    else:
                        if char == '%':
                            self._musicText = text.strip()
                            return self._musicText
                        elif char == ':':
                            stillOnLHS = False
                        else:
                            text = text + char 
                
                self._musicText = text.strip()
                return self._musicText
        else:
            return self._musicText

    musicText = property(_getMusicText, _setMusicText, doc= '''
        Gets just the music text of the CTRule, excluding the left hand side and comments
        
        
        >>> s = romanText.clercqTemperley.CTRule('In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4 % This is a comment')
        >>> s.text
        'In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4 % This is a comment'
        >>> s.musicText
        '$BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4'
        ''')

    def _setComments(self, value):
        if isinstance(value, list):
            self._comments = value
        else:
            raise CTRuleException('not a valid comment list: %s' % value) 
                
    def _getComments(self):
        comments = []
        if self._comments == None or self._comments == []:
            if "%" in self.text:
                if self.text.split()[0].endswith(':'):
                    comments.append([ self.text.split()[0] , (self.text[self.text.index('%')+1:].strip()) ] )
                else:
                    comments.append([ self.text[self.text.index('%')+1:].strip() ])
            self._comments = comments
            return self._comments
        else:
            return self._comments
        
    def appendComment(self, value):
        '''
        append a comment to self.text at the end of the text file. Only strings or lists of strings are
        acceptible to append to the text file. Identical to 
        :meth:`~music21.romanText.clercqTemperley.CTSong.appendComment`
        '''
        try:
            self._comments.append(value)
            if isinstance(value, str) and value != '':
                self.text = self.text + ' %' + str(value)
            elif isinstance(value, list):
                for x in value:
                    self.text = self.text + ' % ' + str(x)
        except:
            raise CTRuleException('not a valid comment to append (must be a string or list): %s' % value)
                

    comments = property(_getComments, _setComments, doc= '''
        Get or set the comments of a CTRule object. Functionality is identical to CTRule comments

        
        >>> s = romanText.clercqTemperley.CTRule('In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4 % This is a comment')
        >>> s.comments
        [['In:', 'This is a comment']]
        ''')

    def _setLHS(self, value):
        self._LHS = str(value)
         
    def _getLHS(self):
        if self._LHS == None or self._LHS == '':
            LHS = ''
            if self.text and self.text.split()[0].endswith(':'):
                for char in self.text:
                    if char == ':':
                        self._LHS = LHS.strip()
                        return self._LHS
                    LHS = LHS + char
            else:
                return self._LHS
        else:
            return self._LHS

    LHS = property(_getLHS, _setLHS, doc= '''
        Get the LHS (Left Hand Side) of the CTRule. If not specified explicitly but CTtext present, searches
        first characters up until ':' for rule and returns string)

        
        >>> s = romanText.clercqTemperley.CTRule('In: $BP*3 I IV | R |*4 I |*4 % This is a comment')
        >>> s.LHS
        'In'
        ''')


    def _setSectionName(self, value):
        self._LHS = str(value)
         
    def _getSectionName(self):
        if self._sectionName == None or self._sectionName == '' and self.LHS != '':
            if 'In' in self.LHS:
                self._sectionName = 'Introduction' + self.LHS[2:]
            elif 'Br' in self.LHS:
                self._sectionName = 'Bridge' + self.LHS[2:]
            elif 'Vr' in self.LHS:
                self._sectionName = 'Verse' + self.LHS[2:]
            elif 'S' in self.LHS:
                self._sectionName = 'Song' + self.LHS[1:]
            elif 'Fadeout' == self.LHS:
                self._sectionName = 'Fadeout'
            else:
                self._sectionName = self.LHS
            return self._sectionName
        else:
            return self._sectionName

    sectionName = property(_getSectionName, _setSectionName, doc= '''
        stores the expanded version of the Left hand side (LHS) such as Introduction, Verse, etc. if
        text present uses LHS to expand)
        
        Currently supported abbreviations: In: Introduction, Br: Bridge, Vr: Verse, S: Song, Fadeout: Fadeout

        
        >>> s = romanText.clercqTemperley.CTRule('Vr2: $BP*3 I IV | I |')
        >>> s.sectionName
        'Verse2'
        ''')


    def _setHomeTimeSig(self, value):
        self._homeTimeSig = str(value)
         
    def _getHomeTimeSig(self):
        from music21 import meter
        if self._homeTimeSig == None or self._homeTimeSig == '':
            if self._streamFromCTSong:
                return self._streamFromCTSong.flat.getElementsByClass(meter.TimeSignature)[0]
            if self.text:
                for atom in self.musicText.split():
                    if '[' not in atom:
                        self._homeTimeSig = meter.TimeSignature('4/4')
                        return self._homeTimeSig
                    else:
                        if '/' in atom:
                            self._homeTimeSig = meter.TimeSignature(atom[1:-1])
                            return self._homeTimeSig
        else:
            return self._homeTimeSig

    homeTimeSig = property(_getHomeTimeSig, _setHomeTimeSig, doc= '''
        Get the beginning of the line's time signature. If not specified explicitly but CTtextfile present, 
        searches first characters of text file for a time signature (of the form [4/4] ) 
        if not found, returns default of 4/4

        
        >>> s = romanText.clercqTemperley.CTRule('In: $BP*3 I IV | I | ')
        >>> s.homeTimeSig
        <music21.meter.TimeSignature 4/4>
        >>> s = romanText.clercqTemperley.CTRule('In: [C] [12/8] $BP*3 I IV | I | ')
        >>> s.homeTimeSig
        <music21.meter.TimeSignature 12/8>
        ''')

    def _setHomeKeySig(self, value):
        self._homeKeySig = str(value)
         
    def _getHomeKeySig(self):
        from music21 import key
        
        if self._homeKeySig == None or self._homeKeySig == '':
            if self._streamFromCTSong:
                return self._streamFromCTSong.flat.getElementsByClass(key.KeySignature)[0]
            if self.text:
                for atom in self.musicText.split():
                    if '[' not in atom:
                        self._homeKeySig = key.Key(key.convertKeyStringToMusic21KeyString('C'))
                        return self._homeKeySig
                    else:
                        if not '/' in atom:
                            self._homeKeySig = key.Key(key.convertKeyStringToMusic21KeyString(atom[1:-1]))
                            return self._homeKeySig
        else:
            return self._homeKeySig

    homeKeySig = property(_getHomeKeySig, _setHomeKeySig, doc= '''
        Get or set the beginning of the line's key signature. If not specified explicitly but 
        CTtextfile present, searches first characters of text file for a key signature 
        (of the form [D#] or [Cb] or [a] uppercase for major, lowercase for minor) if not found, returns default of C Major

        
        >>> s = romanText.clercqTemperley.CTRule('In: $BP*3 I IV | I | ')
        >>> s.homeKeySig
        <music21.key.Key of C major>
        >>> s = romanText.clercqTemperley.CTRule('In: [Db] [12/8] $BP*3 I IV | I | ')
        >>> s.homeKeySig
        <music21.key.Key of D- major>
        ''')


    def streamFromCTSong(self):
        '''
        returns the stream associated with this CTRule only if present; would be generated
        by the :meth:`~music21.romanText.clercqTemperley.CTSong.toScore` method on a 
        :class:`~music21.romanText.clercqTemperley.CTSong` object
        '''
        from music21 import metadata
        
        if self._streamFromCTSong:
            try:
                self._streamFromCTSong.metadata.title
            except AttributeError: 
                self._streamFromCTSong.insert(metadata.Metadata()) 
                self._streamFromCTSong.metadata.title = self.sectionName
            return self._streamFromCTSong
        else:
            return None


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass
    
class TestExternal(unittest.TestCase):
    def runTest(self):
        pass
    
    def testB(self):
        from music21.romanText import clercqTemperley
        BlitzkriegBopCT = '''
% Blitzkrieg Bop

BP: I | IV V | %THIS IS A COMMENT
In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4
Vr: $BP*3 I IV | I |
Br: IV | | I | IV I | IV | | ii | IV V |
Co: R |*4 I |*4
S: [A] $In $Vr $Vr $Br $Vr $Vr $Br $Vr $Vr $Co
'''

        s = clercqTemperley.CTSong(BlitzkriegBopCT)
        scoreObj = s.toScore()
        scoreObj.show()
    def xtestA(self):
        '''
        from music21.romanText import clercqTemperley
        
        dt = 'C:/clercqTemperley/dt'
        tdc = 'C:/clercqTemperley/tdc'
 
        for x in os.listdir(tdc):
            print(x)
            f = open(os.path.join(tdc, x), 'r')
            txt = f.read()

            s = clercqTemperley.CTSong(txt)
            for chord in s.toScore().flat.getElementsByClass('Chord'):
                try:
                    x = chord.pitches
                except:
                    print(x, chord)
        
        
        for num in range(1, 200):
            try:
                fileName = 'C:\\dt\\%s.txt' % num
                s = clercqTemperley.CTSong(fileName)
                print(s.toScore().highestOffset, 'Success', num)
            except:
                print("ERROR", num)
        '''
        pass
        #s = clercqTemperley.CTSong(exampleClercqTemperley)
        
        #sc = s.toScore()
        #print sc.highestOffset
        #sc.show()
#---------------------------------------------------------------------------

# define presented class order in documentation

_DOC_ORDER = [CTSong, CTRule]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
    # from music21.romanText import clercqTemperley
    # test = clercqTemperley.TestExternal()
    # test.testB()
#------------------------------------------------------------------------------
# eof
