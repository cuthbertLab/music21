# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         clercqTemperley.py
# Purpose:      Demonstration of using music21 to parse Clercq-Temperley's
#               popular music flavor of RomanText
#
# Authors:      Michael Scott Cuthbert
#               Beth Hadley
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Parses the de Clercq-Temperley popular music flavor of RomanText.
The Clercq-Temperley file format and additional rock corpus analysis
information may be located at http://theory.esm.rochester.edu/rock_corpus/

'''
import music21
import re
import copy
import weakref
class CTSongException(Exception):
    pass

testfile = '''
% Blitzkrieg Bop

BP: I | IV V | %THIS IS A COMMENT
In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4
Vr: $BP*3 I IV | I |
Br: IV | | I | IV I | IV | | ii | IV V |
Co: R |*4 I |*4
S: [A] $In $Vr $Vr $Br $Vr $Vr $Br $Vr $Vr $Co
'''

testfile2 = '''
% Rock Around the Clock
% just a general comment
In: I | | | | | | V | |
Vr: I | | | | IVd7 | | I | | V7 | | I | | %a comment on verse
Vrf: I | | | | IVd7 | | I | | V7 | | I | IV iv | V | . I |
S: [A] $In $Vr $Vr $Vr $Vr $Vr $Vr $Vrf    % 3rd and 6th verses are instrumental


'''
textString = '''%Simple Gifts \n % A wonderful shaker melody \n Vr: I | I | %incomplete verse \n S: [A] $Vr % Not quite finished!'''

class CTSong(object):
    '''
    This parser is an object-oriented approach; a CTSong object is created
    when the text file is read in. 
    
    Create a CTSong object as below:
    
    testfile2 = 
    % Rock Around the Clock
    % just a general comment
    In: I | | | | | | V | |
    Vr: I | | | | IVd7 | | I | | V7 | | I | | %a comment on verse
    Vrf: I | | | | IVd7 | | I | | V7 | | I | IV iv | V | . I |
    S: [A] $In $Vr $Vr $Vr $Vr $Vr $Vr $Vrf    % 3rd and 6th verses are instrumental
    
    >>> from music21.demos import clercqTemperley
    >>> s = clercqTemperley.CTSong(testfile2)

    When you call the .toScore() method on the newly created CTSong object,
    the code extracts meaningful properties (such as title, text, comments,
    year, rules, home time Signature, and home Key Signature) from the textfile
    and makes these accessible as below.
    
    >>> s.toScore().highestOffset
    374.0
    
    (this is a really bad way of showing that a score object is indeed returned)
    
    >>> s.title
    'Rock Around the Clock'
    
    >>> s.comments
    [['just a general comment'], ['Vr:', 'a comment on verse'], ['S:', '3rd and 6th verses are instrumental']]

    Year is not defined as part of the clercq-temperley format, but it will be helpful
    to have it as a property. So let's assing a year to this song:
    
    >>> s.year = 1952
    >>> s.year
    1952
    
    >>> s.homeTimeSig
    <music21.meter.TimeSignature 4/4>
    >>> s.homeKeySig
    <music21.key.Key of A major>

    Upon calling toScore(), CTRule objects are also created. CTRule objects are
    the individual rules that make up the song object. For example,
    
    >>> s.rules
    [<music21.CTRule.CTRule text = In: I | | | | | | V | | , <music21.CTRule.CTRule text = Vr: I | | | | IVd7 | | I | | V7 | | I | | %a comment on verse , <music21.CTRule.CTRule text = Vrf: I | | | | IVd7 | | I | | V7 | | I | IV iv | V | . I | ]
  
    The parser extracts meaningful properties to each rule, such as sectionName,
    home time signature of that rule, home key of that rule, and of course the individual
    stream of the song.

    The following examples display the instantiated properties of the first rule as created above.
    >>> rule = s.rules[0]
    >>> rule.text
    'In: I | | | | | | V | |'
    >>> rule.sectionName
    'Introduction'
    >>> rule.homeTimeSig
    <music21.meter.TimeSignature 4/4>
    >>> rule.homeKey
    <music21.key.Key of A major>
    >>> rule.streamFromCTSong().highestOffset
    28.0
    
    With this object-oriented approach to parsing the clercq-temperley text file format, 
    we now have the ability to analyze a large corpus (200 files) of popular music
    using the full suite of harmonic tools of music21. We can not only analyze each
    song as a whole, as presented in their paper, but we can also analyze each
    individual section (or rule) of a song. This may provide interesting insight
    into popular music beyond our current understanding.
    
    Examples used throughout this class utilize the following Clercq-Temperley text file:
    testfile = 
    % Blitzkrieg Bop
    
    BP: I | IV V | %THIS IS A COMMENT
    In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4
    Vr: $BP*3 I IV | I |
    Br: IV | | I | IV I | IV | | ii | IV V |
    Co: R |*4 I |*4
    S: [A] $In $Vr $Vr $Br $Vr $Vr $Br $Vr $Vr $Co
        
    '''
    def __init__(self, text = '', **keywords):
        self.text = text
        self._title = None
        self.year = None
        self._rules = [] #list of all component rules of the type CTRule
        self._homeTimeSig = None
        self._homeKeySig = None
        self._comments = []

        for kw in keywords:
            if kw == 'title':
                self._title = kw
            if kw == 'year':
                self.year = kw
    
    def __repr__(self):
        return '<music21.CTSong.%s text = %s title=%s year=%s' % (self.__class__.__name__, self.text, self.title, self.year)
    #---------------------------------------------------------------------------
    def _setTitle(self, value):
        self._title = str(value)
         
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
        Get or set the title of the CTSong. If not specified explicitly but CTtextfile present, searches first few lines of 
        text file for title (a string preceded by a '%') if found, sets title attribute to this string and returns this title)

        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTSong(testfile)
        >>> s.title
        'Blitzkrieg Bop'
        ''')

    def _setComments(self, value):
        self._comments = str(value)
        if self._comments != None and self._comments != '':
            self.text = self.text + ' %' + str(value)
         
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
        
    
    
    comments = property(_getComments, _setComments, doc= '''
        Get or set the comments list of a CTRule object...this also appends the comments to the CTRule.text
    
        comments are stored as a list of comments, each comment on a line as a list. If the
        comment is on a rule line, the list contains both the line's LHS (like In:) and the comment
        if the comment is on a line of its own, only the comment is appended as a list of length one.
        
        The title is not a comment. The title is stored under self.title
        textString = '%Simple Gifts \n % A wonderful shaker melody \n Vr: I | I | %incomplete verse \n S: [A] $Vr % Not quite finished!'

        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTSong(textString)
        >>> s.comments
        [['A wonderful shaker melody'], ['Vr:', 'incomplete verse'], ['S:', 'Not quite finished!']]

        ''')


    def _setRules(self, value):
        self._rules = value
    
    def _getRules(self):
        if self._rules == None or self._rules == []:
            lines = self.text.split('\n')
            for line in lines:
                if not line == '':
                    if line.split()[0].endswith(':') and '|' in line: #or 'S:' in line Let's not include 'Song' line for now...
                        self._rules.append(CTRule(line))
            return self._rules
        else:
            return self._rules


    rules = property(_getRules, _setRules, doc= '''
        Get or set the rules of a CTSong. the Rules is a list of objects of type CTRule. If only a textfile
        provided, this goes through text file and creates the rule object out of each line containing
        a LHS...NOT including the Song line
        
        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTSong(testfile)
        >>> len(s.rules)
        5
        >>> for rule in s.rules:
        ...   print rule.LHS
        BP
        In
        Vr
        Br
        Co
        
        ''')
    
    
    def _setHomeTimeSig(self, value):
        if hasattr(value, 'classes') and 'TimeSignature' in value.classes:
            self._homeTimeSig = value
            return
        try:
            self._homeTimeSig = music21.meter.TimeSignature(value)
            return
        except:
            raise CTSongException('not a valid time signature: %s' % value)

    def _getHomeTimeSig(self):
        #look at 'S' Rule and grab the home time Signature
        if self.text and 'S:' in self.text:
            lines = self.text.split('\n')
            for line in lines:
                if line.startswith('S:'):
                    for atom in line.split()[1:3]:
                        if '[' not in atom:
                            self._homeTimeSig = music21.meter.TimeSignature('4/4')
                            return self._homeTimeSig
                        elif '/' in atom:
                            self._homeTimeSig = music21.meter.TimeSignature(atom[1:-1])
                            return self._homeTimeSig
                        else:
                            pass
        return self._homeTimeSig
    
    homeTimeSig = property(_getHomeTimeSig, _setHomeTimeSig, doc = '''
        gets or sets the initial, or 'home' time signature in a song by looking at the 'S' substring
        and returning the provided time signature. If not present, returns the default time signat
        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTSong(testfile)
        >>> s.homeTimeSig
        <music21.meter.TimeSignature 4/4>
                 
        ''')
    

    def _setHomeKeySig(self, value):
        if hasattr(value, 'classes') and 'Key' in value.classes:
            self._homeKeySig = value
            return
        try:
            m21keyStr = music21.key.convertKeyStringToMusic21KeyString(value)
            self._homeKeySig = music21.key.Key(m21keyStr)
            return
        except:
            raise CTSongException('not a valid key signature: %s' % value)

    def _getHomeKeySig(self):
        #look at 'S' Rule and grab the home key Signature
        if self.text and 'S:' in self.text:
            lines = self.text.split('\n')
            for line in lines:
                if line.startswith('S:'):
                    for atom in line.split()[1:3]:
                        if '[' not in atom:
                            self.homeKeySig = music21.key.Key('C')
                            return self._homeKeySig
                        elif not '/' in atom:
                            m21keyStr = music21.key.convertKeyStringToMusic21KeyString(atom[1:-1])
                            self._homeKeySig = music21.key.Key(m21keyStr)
                            return self._homeKeySig
                        else:
                            pass
        return self._homeKeySig
    
    homeKeySig = property(_getHomeKeySig, _setHomeKeySig, doc = '''
        gets or sets initial, or 'home' key signature by looking at the musictext and locating
        the key signature in the first few characters in the song rule. A key signature in the song
        rule might look like this: S: [A] $In $Vr
        
        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTSong(testfile)
        >>> s.homeKeySig
        <music21.key.Key of A major>
        ''')
    
    #---------------------------------------------------------------------------------
    #HELPER METHODS FOR .toScore method
    '''
    Most of these methods have no tests....because I didn't know how to test them
    because many of them require many parameters and those parameters are generated
    real-time during parsing...
    
    The methods below are kind of a mess...advice on how to clean them up?
    '''
    def _stringhasDotsandBars(self, expressionString):
        split = expressionString.split()
        if split.count('|') > 1 and split.count('.') > 1 and expressionString.count('[') > 1:
            return True
        else:
            return False

    def _getDuration(self, containsIndex, entireString, timeSig): #change variable names!!!
        '''returns duration of any single object passed to it (whose index is specified by containsIndex)
        entireString is the entire split file
    
        '''
        starters = ['I', '#', 'B', 'V', 'R', '.']
        starters2 = ['I', '#', 'B', 'V', 'R', '.', '[']
        searchlocation = containsIndex - 1
        previouschar = entireString[searchlocation]
        measureContents = []
        atomBeingSearched = entireString[containsIndex]
        if atomBeingSearched[0].upper() in starters and not atomBeingSearched.endswith(':'):
            while previouschar[0].upper() in starters2 and not previouschar.endswith(':'):
                if previouschar.startswith('[') and "/" in previouschar:
                    timeSig = music21.meter.TimeSignature(previouschar[1:-1])
                elif previouschar.startswith('['): #could be a key
                    pass
                else:
                    measureContents.append(previouschar)
                searchlocation = searchlocation - 1
                previouschar = entireString[searchlocation]
            measureContents.reverse()
            searchlocation = containsIndex + 1
        
            nextChar = entireString[searchlocation]
            measureContents.append(entireString[containsIndex])
            while nextChar[0].upper() in starters2 and not nextChar.endswith(':'):
                if not '*' in nextChar and not nextChar.startswith('['):
                    measureContents.append(nextChar)
                searchlocation = searchlocation + 1
                nextChar = entireString[searchlocation]
        
        if len(measureContents) > 0:
            duration = timeSig.totalLength  / len(measureContents)
        else:
            duration = 0   
        return duration

    def _getStringWithBarsandDots(self, containsIndex, entireString):
        if entireString[containsIndex - 1].startswith('['):
            expressionString = entireString[containsIndex - 1] + ' '
            if entireString[containsIndex - 2].startswith('['):
                expressionString = expressionString + entireString[containsIndex - 2] + ' '
        else:
            expressionString = ''
        expressionString = expressionString + entireString[containsIndex] + ' '
        searchlocation = containsIndex + 1
        nextChar = entireString[searchlocation]
        while (nextChar == '|' or nextChar == '.' or (nextChar.startswith('[') and '/' in nextChar)) and len(entireString) > searchlocation + 1:
            expressionString = expressionString + nextChar + ' '
            searchlocation = searchlocation + 1
            nextChar = entireString[searchlocation]
        #print expressionString
        s = expressionString.split()
        if s.count('|') > 1 or s.count('.') > 0:
            if '/' in s[-1]:
                s.pop()      
            return ' '.join(s)
        else:
            return ""

    def _barIsDouble(self, indexofbar, expressionString):
    
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
            except:
                pass
        if count > 1:
            return True
        else:
            return False

    def _getStreamWithBarsandDots(self, indexofatom, expressionString, splitFile, atom, currentKey, timeSig):
        '''
        how do I write tests for this method??? This method is more of a run-time method...
        '''
        outputStream = music21.stream.Stream()
        index = -1
        starters = ['I', '#', 'B', 'V']
        dur = 0
        pleaseAppend = False
        for x in expressionString.split():
            index = index + 1
            if expressionString:
                if x.startswith('[') and "/" in x:
                    timeSig = music21.meter.TimeSignature(x[1:-1])
                    outputStream.append(timeSig)
                elif x.startswith('['):
                    m21keyStr = music21.key.convertKeyStringToMusic21KeyString(x[1:-1])
                    currentKey = music21.key.Key(m21keyStr)
                    outputStream.append(currentKey)
                elif x[0].upper() in starters:
                    rn = music21.roman.RomanNumeral(atom, currentKey)
                    rn.duration.quarterLength = self._getDuration(indexofatom, splitFile, timeSig)
                    
                    outputStream.append(rn)
                    if self._stringhasDotsandBars(expressionString):
                        for x in rn.pitches:
                            rn.setTie(music21.tie.Tie('start'), x) 
                elif x == '|':
                    if self._stringhasDotsandBars(expressionString) and expressionString.split()[index - 2] == '|' :
                        z = music21.roman.RomanNumeral(atom, currentKey)
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
            xy = music21.roman.RomanNumeral(atom, currentKey)
            xy.duration.quarterLength = dur
            outputStream.append(xy)
        outputStream = outputStream.makeMeasures(finalBarline = None)

        measureNumber = 1
        for x in expressionString.split():
         
            if expressionString:
                if x.startswith('[') and "/" in x:
                    
                    timeSig = music21.meter.TimeSignature(x[1:-1])
                    try:
                        currentTimeSig = outputStream.measure(measureNumber).flat.getElementsByClass(music21.meter.TimeSignature)[0]
                        if str(currentTimeSig) != str(timeSig):
                            
                            outputStream.remove(currentTimeSig)
                      
                            outputStream.measure(measureNumber).insert(0.0, timeSig)
                    except:
                        outputStream.measure(measureNumber).insert(0.0, timeSig)
                elif x == '|':
                    measureNumber = measureNumber + 1
                else:
                    pass
                    
        outputStream.makeTies()        
        return outputStream

#Vr1: I | [2/4] | [4/4] | [2/4] | [4/4] | | 

    def _removeDuplicateKeys(self, scoreObj):
        #remove duplicate key signatures in stream if present
        keyList = scoreObj.flat.getElementsByClass(music21.key.KeySignature)
        index = 0
        if len(keyList) > 1:
            for x in keyList[1:]:
                index = index + 1
                if str(x) == str(keyList[index-1]):
                    scoreObj.remove(x)
        return scoreObj
        
    def _removeDuplicateMeters(self, scoreObj):
        #remove duplicate time signatures in stream if present
        timeList = scoreObj.flat.getElementsByClass(music21.meter.TimeSignature)
        index = 0
        if len(timeList) > 1:
            for x in timeList[1:]:
                index = index + 1
                if str(x) == str(timeList[index-1]):
                    scoreObj.remove(x)
        return scoreObj
    
    
    def _removeDuplicateClefs(self, scoreObj):
        for x in scoreObj.flat.getElementsByClass(music21.clef.TrebleClef):
            scoreObj.remove(x)
        scoreObj.insert(0, music21.clef.TrebleClef())
        return scoreObj

    def _labelRomanNumerals(self, scoreObj):
        lastel = music21.roman.RomanNumeral(None, None)
        for el in scoreObj.flat.getElementsByClass(music21.roman.RomanNumeral):
            if el.tie == None:
                el.lyric = el.figure
            elif lastel.figure != el.figure and el.figure != None:
                el.lyric = el.figure
            elif el.tie != None and el.tie.type == 'start':
                el.lyric = el.figure
            else:
                pass
            lastel = el
        return scoreObj
            
    def toScore(self):
        '''creates Score object out of a from CTSong...also creates CTRule objects in the process,
        filling their .stream attributes in the process because there might be extra information in the
        Song string like key or time signature that changes the rule components
        and it makes more sense to only have to create each stream once
        
        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTSong(testfile)
        >>> scoreObj = s.toScore()
        >>> scoreObj.highestOffset   
        380.0
    
        '''
        scoreObj = music21.stream.Score() 
 
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
                homeTimeSig = music21.meter.TimeSignature(atomContents)
                self._homeTimeSig = homeTimeSig
                firsttimeSigFound = True
            elif x.startswith('[') and not '/' in x:
                m21keyStr = music21.key.convertKeyStringToMusic21KeyString(atomContents)
                homeKey = music21.key.Key(m21keyStr)
                self._homeKeySig = homeKey
                firstKeyFound = True
        if firsttimeSigFound == False:
            homeTimeSig = music21.meter.TimeSignature('4/4')
            #scoreObj.append( homeTimeSig) 
        if firstKeyFound == False:
            homeKey = music21.key.Key('C')
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
                    currentTimeSig = music21.meter.TimeSignature(temptime)
                    
            if indexofatom < jumpForwardIndexValue:
                if atom.startswith('[') and atom.endswith(']'):
                    atomContents = atom[1:-1]
                    if re.match('[a-zA-Z]', atomContents):
                        m21keyStr = music21.key.convertKeyStringToMusic21KeyString(atomContents)
                        currentKey = music21.key.Key(m21keyStr)
                    else: 
                        currentTimeSig = music21.meter.TimeSignature(atomContents)
                continue
    
            else:
                if atom.endswith(':'):
                    for label, subsectionToAppendName, offset in flags:
                        if '*' in label:
                            x = label[1: label.index('*')]
                        if x in allSubsections.keys():
                            referencedSubsection = label[1:]
                            match = re.search('^(.*)\*(\d+)', referencedSubsection)
                            if match:
                                numRepeat = int(match.group(2))
                                referencedSubsection = match.group(1)
                            else:
                                numRepeat = 1
                            tempStream = music21.stream.Stream()
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
                        currentSubsectionName = 'S' # replace with title of piece
                        currentSubsectionContents = scoreObj
                    else:
                        currentSubsectionContents = music21.stream.Stream()

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
                    match = re.search('^(.*)\*(\d+)', referencedSubsection)
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
                            currentSubsectionContents.append(copy.deepcopy(x))
        
                elif atom.startswith('[') and atom.endswith(']'):
                    atomContents = atom[1:-1]
                    if re.match('[a-zA-Z]', atomContents):
                        m21keyStr = music21.key.convertKeyStringToMusic21KeyString(atomContents)
                        currentKey = music21.key.Key(m21keyStr)
                        currentSubsectionContents.append(currentKey)
                    else:
                        currentTimeSig = music21.meter.TimeSignature(atomContents)
                        currentSubsectionContents.append(currentTimeSig)
                elif atom == 'R':
                    if currentTimeSig == None:
                        currentTimeSig = music21.meter.TimeSignature('4/4')
                    qlenrest = self._getDuration(indexofatom, splitFile, currentTimeSig)
                    currentSubsectionContents.append(music21.note.Rest(quarterLength=qlenrest) ) 
          
                elif atom[0].upper() in starters2 and not atom.endswith(':'):
                    if 'x' in atom:
                        atom = atom.replace('x', 'o')
                    if 'h' in atom:
                        atom = atom.replace('h', '/o')
                    if atom[0].islower() and 'a' in atom:
                        atom = atom.replace('a', '+')
        
                    expressionString = self._getStringWithBarsandDots(indexofatom, splitFile)
            
                    if len(expressionString) > 0:
                        streamToAppend = self._getStreamWithBarsandDots(indexofatom, expressionString, splitFile, atom, currentKey, currentTimeSig)
                        jumpForwardIndexValue = len(expressionString.split()) - expressionString.split().index(atom) + indexofatom
                        currentSubsectionContents.append(streamToAppend.flat.elements)
                        
                    else:
                        duration = self._getDuration(indexofatom, splitFile, currentTimeSig)
                        try:
                            rn = music21.roman.RomanNumeral(atom, currentKey)
                            rn.duration.quarterLength = duration
                            currentSubsectionContents.append(rn)
                        except Exception, e:
                            print "invalid atom: " + str(atom) + "exception: " + str(e)      
                else:
                        #should skip all bar lines and dots...
                        if atom != '|' and atom != '.':
                            raise CTSongException('invalid character found: %s' % atom)               

        for streamKey in allSubsections:
            for CTRuleObject in self.rules:
                if CTRuleObject.LHS == streamKey:
                    allSubsections[streamKey] = self._removeDuplicateClefs(allSubsections[streamKey])
                    allSubsections[streamKey] = self._removeDuplicateMeters(allSubsections[streamKey])                                          
                    allSubsections[streamKey] = self._removeDuplicateKeys(allSubsections[streamKey])
                    allSubsections[streamKey] = self._labelRomanNumerals(allSubsections[streamKey])
                    CTRuleObject._streamFromCTSong = allSubsections[streamKey]    
        
        scoreObj.subsections = allSubsections
        #needs to be done a second time...this time on whole Score Object
        scoreObj = self._labelRomanNumerals(scoreObj)
        scoreObj = self._removeDuplicateClefs(scoreObj)
        scoreObj = self._removeDuplicateKeys(scoreObj)
        scoreObj = self._removeDuplicateMeters(scoreObj)
        
        scoreObj.insert(music21.metadata.Metadata()) 
        scoreObj.metadata.title = self.title

        return scoreObj

        
class CTRule(object):
    
    def __init__(self, text = '', **keywords):
        self.text = text #FULL TEXT OF CTRULE (includes LHS, chords, and comments
        self._comments = []
        self._musicText = None #just the text above without the rule string or comments
        self._LHS = None #rule string
        self._sectionName = None #nice name of LHS
        self._homeTimeSig = None
        self._homeKey = None
        self._streamFromCTSong = None

    #possibly deal with keywords later....    
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
        Gets the full text of the CTRule, including the left hand side, music text, and comments
        
        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTRule('In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4 % This is a comment')
        >>> s.text
        'In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4 % This is a comment'
        >>> s.musicText
        '$BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4'
        ''')


    def _setComments(self, value):
        self._comments = str(value)
        if self._comments != None and self._comments != '':
            self.text = self.text + ' %' + str(value)
         
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
        

    comments = property(_getComments, _setComments, doc= '''
        Get or set the Comments of a CTRule object...this also appends the comments to the CTRule.text
        same return format as for CTSong object (as list of tuple-lists)

        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTRule('In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4 % This is a comment')
        >>> s.comments
        [['In:', 'This is a comment']]
        ''')

    def _setLHS(self, value):
        self._LHS = str(value)
         
    def _getLHS(self):
        if self._LHS == None or self._LHS == '':
            LHS = ''
            if self.text and ':' in self.text and '|' in self.text:
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
        Get or set the LHS (Left Hand Side) of the CTRule. If not specified explicitly but CTtext present, searches
        first characters up until ':' for rule and returns string)

        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTRule('In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4 % This is a comment')
        >>> s.LHS
        'In'
        ''')


    def _setSectionName(self, value):
        self._LHS = str(value)
         
    def _getSectionName(self):
        if self._sectionName == None or self._LHS == '':
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
            return self._sectionName
            
        else:
            return self._sectionName

    sectionName = property(_getSectionName, _setSectionName, doc= '''
        stores the expanded version of the Left hand side (LHS) such as Introduction, Verse, etc. if
        text present uses LHS to expand)
        
        Currently supported abbreviations:
        In: Introduction
        Br: Bridge
        Vr: Verse
        S: Song
        Fadeout: Fadeout

        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTRule('Vr2: $BP*3 I IV | I |')
        >>> s.sectionName
        'Verse2'
        ''')


    def _setHomeTimeSig(self, value):
        self._homeTimeSig = str(value)
         
    def _getHomeTimeSig(self):
        if self._homeTimeSig == None or self._homeTimeSig == '':
            if self._streamFromCTSong:
                return self._streamFromCTSong.flat.getElementsByClass(music21.meter.TimeSignature)[0]
            if self.text:
                for atom in self.musicText.split():
                    if '[' not in atom:
                        self._homeTimeSig = music21.meter.TimeSignature('4/4')
                        return self._homeTimeSig
                    else:
                        if '/' in atom:
                            self._homeTimeSig = music21.meter.TimeSignature(atom[1:-1])
                            return self._homeTimeSig
        else:
            return self._homeTimeSig

    homeTimeSig = property(_getHomeTimeSig, _setHomeTimeSig, doc= '''
        Get or set the beginning of the line's time signature. If not specified explicitly but CTtextfile present, 
        searches first characters of text file for a time signature (of the form [4/4] ) 
        if not found, returns default of 4/4

        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTRule('In: $BP*3 I IV | I | ')
        >>> s.homeTimeSig
        <music21.meter.TimeSignature 4/4>
        >>> s = clercqTemperley.CTRule('In: [C] [12/8] $BP*3 I IV | I | ')
        >>> s.homeTimeSig
        <music21.meter.TimeSignature 12/8>
        ''')

    def _setHomeKey(self, value):
        self._homeKey = str(value)
         
    def _getHomeKey(self):
        if self._homeKey == None or self._homeKey == '':
            if self._streamFromCTSong:
                return self._streamFromCTSong.flat.getElementsByClass(music21.key.KeySignature)[0]
            if self.text:
                for atom in self.musicText.split():
                    if '[' not in atom:
                        self._homeKey = music21.key.Key(music21.key.convertKeyStringToMusic21KeyString('C'))
                        return self._homeKey
                    else:
                        if not '/' in atom:
                            self._homeKey = music21.key.Key(music21.key.convertKeyStringToMusic21KeyString(atom[1:-1]))
                            return self._homeKey
        else:
            return self._homeKey

    homeKey = property(_getHomeKey, _setHomeKey, doc= '''
        Get or set the beginning of the line's key signature. If not specified explicitly but 
        CTtextfile present, searches first characters of text file for a key signature 
        (of the form [D#] or [Cb] or [a] uppercase for major, lowercase for minor) if not found, returns default of C Major

        >>> from music21.demos import clercqTemperley
        >>> s = clercqTemperley.CTRule('In: $BP*3 I IV | I | ')
        >>> s.homeKey
        <music21.key.Key of C major>
        >>> s = clercqTemperley.CTRule('In: [Db] [12/8] $BP*3 I IV | I | ')
        >>> s.homeKey
        <music21.key.Key of D- major>
        ''')


    def streamFromCTSong(self):
        if self._streamFromCTSong:
            return self._streamFromCTSong
        else:
            return None

#---------------------------------------------------------------------------

# define presented order in documentation

_DOC_ORDER = [CTSong, CTRule]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
