# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         tempo.py
# Purpose:      Classes and tools relating to tempo
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-11 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''This module defines objects for describing tempo and changes in tempo.
'''

from __future__ import unicode_literals

import unittest, doctest, copy

import music21
import music21.note
from music21 import common
from music21 import duration
from music21 import expressions

from music21 import environment
_MOD = "tempo.py"
environLocal = environment.Environment(_MOD)


# all lowercase, even german
defaultTempoValues = {
     'molto adagio': 40,
     'adagio': 52,
     'slow': 52,
     'langsam': 52,
     'andante': 72,
     'moderato': 90,
     'moderate': 90,
     'allegretto': 108,
     'allegro': 132,
     'fast': 132,
     'schnell': 132,
     'molto allegro': 144,
     u'très vite': 144,
     'presto': 168,
     'prestissimo': 200
     }



def convertTempoAtBeat(numberSrc, quarterLengthBeatSrc, 
                       quarterLengthBeatDst=1.0):
    '''Convert between equivalent tempi, where the speed stays the same but the beat referent and number chnage.

    >>> from music21 import *
    >>> tempo.convertTempoAtBeat(60, 1, 2) # 60 bpm at quarter, going to half
    30.0
    >>> tempo.convertTempoAtBeat(60, 1, .25) # 60 bpm at quarter, going to 16th
    240.0
    >>> tempo.convertTempoAtBeat(60, 1.5, 1) # 60 at dotted quarter, get quarter
    90.0
    >>> tempo.convertTempoAtBeat(60, 1.5, 2) # 60 at dotted quarter, get half
    45.0
    >>> tempo.convertTempoAtBeat(60, 1.5, 1/3.) # 60 at dotted quarter, get trip
    270.0

    '''
    # find duration in seconds of of quarter length
    srcDurPerBeat = 60.0 / numberSrc
    # convert to dur for one quarter length
    dur = srcDurPerBeat * (1.0 / quarterLengthBeatSrc)
    # multiply dur by dst quarter
    dstDurPerBeat = dur * float(quarterLengthBeatDst)
    #environLocal.printDebug(['dur', dur, 'dstDurPerBeat', dstDurPerBeat])
    # find tempo
    return 60.0 / dstDurPerBeat




#-------------------------------------------------------------------------------
class TempoException(Exception):
    pass


#-------------------------------------------------------------------------------
class TempoIndication(music21.Music21Object):
    '''A generic base class for all tempo indications to inherit. Can be used to filter out all types of tempo indications. 
    '''
    classSortOrder = 1

    def __init__(self):
        music21.Music21Object.__init__(self)


#-------------------------------------------------------------------------------
class TempoText(TempoIndication):
    '''
    >>> import music21
    >>> tm = music21.tempo.TempoText("adagio")
    >>> tm.text
    'adagio'
    

    Common marks such as "adagio," "moderato," "molto allegro," etc.
    get sensible default values.  If not found, uses a default of 90:

    '''
    def __init__(self, text=None):
        TempoIndication.__init__(self)

        # store text in a TextExpression instance        
        self._textExpression = None # a stored object
        self._textJustification = 'left'

        if text is not None:
            try: # use property
                self.text = str(text) 
            except UnicodeEncodeError: # if it is already unicode
                self.text = text
    
    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.text)

    def _getText(self):
        '''Get the text used for this expression.
        '''
        return self._textExpression.content

    def _setText(self, value):
        '''Set the text of this repeat expression. This is also the primary way that the stored TextExpression object is created.
        '''
        if self._textExpression is None:
            self._textExpression = expressions.TextExpression(value)
            self.applyTextFormatting()
        else:
            self._textExpression.content = value

    text = property(_getText, _setText, doc = '''
        Get or set the text as a string.

        >>> import music21
        >>> tm = music21.tempo.TempoText("adagio")
        >>> tm.text
        'adagio'
        >>> tm.getTextExpression()
        <music21.expressions.TextExpression "adagio">
        ''')

    def getMetronomeMark(self):
        '''Return a MetronomeMark object that is configured from this objects Text.

        >>> from music21 import *
        >>> tt = tempo.TempoText("slow")
        >>> mm = tt.getMetronomeMark()
        >>> mm.number
        52
        '''
        return MetronomeMark(text=self.text)

    def getTextExpression(self, numberImplicit=False):
        '''Return a TextExpression object for this text.
        '''
        if self._textExpression is None:
            return None
        else:
            self.applyTextFormatting(numberImplicit=numberImplicit)
            return copy.deepcopy(self._textExpression)

    def setTextExpression(self, vale):
        '''Given a TextExpression, set it in this object.
        '''
        self._textExpression = value
        self.applyTextFormatting()
        
    def applyTextFormatting(self, te=None, numberImplicit=False):
        '''Apply the default text formatting to the text expression version of of this repeat
        '''
        if te is None: # use the stored version if possible
            te = self._textExpression
        te.justify = self._textJustification
        te.style = 'bold'
        if numberImplicit:
            te.positionVertical = 20 # if not showing number
        else:
            te.positionVertical = 45 # 4.5 staff lines above
        return te

    def isValidText(self, value):
        '''Return True or False if the supplied text could be used for this TempoText.  
        '''
        def stripText(s):
            # remove all spaces, punctuation, and make lower
            s = s.strip()
            s = s.replace(' ', '')
            s = s.replace('.', '')
            s = s.lower()
            return s
        # TODO: compare to known tempo marks
#         for candidate in self._textAlternatives:
#             candidate = stripText(candidate)
#             value = stripText(value)
#             if value == candidate:
#                 return True
        return False



#-------------------------------------------------------------------------------
class MetronomeMark(TempoIndication):
    '''
    A way of specifying a particular tempo with a text string, a referent (a duration) and a number.

    The `referent` attribute is a Duration object. As this object is a Music21Object, it also has a .duration property object.
    
    >>> from music21 import *
    >>> a = tempo.MetronomeMark("slow", 40, note.HalfNote())
    >>> a.number
    40
    >>> a.referent
    <music21.duration.Duration 2.0>
    >>> a.referent.type
    'half'
    >>> a.text
    'slow'

    >>> mm = tempo.MetronomeMark('adagio')
    >>> mm.number
    52
    >>> mm.numberImplicit
    True

    >>> tm2 = music21.tempo.MetronomeMark(u"très vite")
    >>> tm2.text.endswith('vite')
    True
    >>> tm2.number
    144

    >>> tm2 = music21.tempo.MetronomeMark(number=200)
    >>> tm2.text
    'prestissimo'
    >>> tm2.referent
    <music21.duration.Duration 1.0>
    '''
# 
#     >>> tm3 = music21.tempo.TempoText("extremely, wicked fast!")
#     >>> tm3.number
#     90

    def __init__(self, text=None, number=None, referent=None, 
        parentheses=False):
        TempoIndication.__init__(self)

        self._number = number # may be None
        self.numberImplicit = None
        if self._number is not None:
            self.numberImplicit = False

        self._tempoText = None # set with property text
        self.textImplicit = None
        if text is not None: # use property to create object if necessary
            self.text = text

        self.parentheses = parentheses 


        self._referent = None # set with property
        if referent is None: 
            # if referent is None, set a default quarter note duration
            referent = duration.Duration(type='quarter')
        self.referent = referent # use property

        # assume ql value or a type string
#         elif common.isNum(referent) or common.isStr(referent): 
#             self.referent = duration.Duration(referent)
#         elif 'Duration' not in referent.classes:
#             # try get duration object, like from Note
#             self.referent = referent.duration
#         elif 'Duration' in referent.classes:
#             self.referent = referent # should be a music21.duration.Duration object or a Music21Object with a duration or None
#         else:
#             raise TempoException('unhandled condition')

        # set implicit values if necessary
        self._updateNumberFromText()
        self._updateTextFromNumber()

        # need to store a sounding value for the case where where
        # a sounding different is different than the number given in the MM
        self._numberSounding = None

    def __repr__(self):
        if self.text is None:
            return "<music21.tempo.MetronomeMark %s=%s>" % (self.referent.fullName, str(self.number))
        else:
            return "<music21.tempo.MetronomeMark %s %s=%s>" % (self.text, self.referent.fullName, str(self.number))

    def _updateTextFromNumber(self):
        '''Update text if number is given and text is not defined
        '''
        if self._tempoText is None and self._number is not None:
            self._setText(self._getDefaultText(self._number), 
                            updateNumberFromText=False)
            if self.text is not None:
                self.textImplicit = True

    def _updateNumberFromText(self):
        '''Update number if text is given and number is not defined 
        '''
        if self._number is None and self._tempoText is not None:
            self._number = self._getDefaultNumber(self._tempoText)
            if self._number is not None: # only if set
                self.numberImplicit = True

    #--------------------------------------------------------------------------
    def _getReferent(self):
        return self._referent
    
    def _setReferent(self, value):
        if value is None: # this may be better not here
            # if referent is None, set a default quarter note duration
            self._referent = duration.Duration(type='quarter')
        # assume ql value or a type string
        elif common.isNum(value) or common.isStr(value): 
            self._referent = duration.Duration(value)
        elif 'Duration' not in value.classes:
            # try get duration object, like from Note
            self._referent = value.duration
        elif 'Duration' in value.classes:
            self._referent = value # should be a music21.duration.Duration object or a Music21Object with a duration or None
        else:
            raise TempoException('Cannot get a Duration from the supplied object: %s', value)

    referent = property(_getReferent, _setReferent, doc=
        '''Get or set the referent, or the Duration object that is the reference for the tempo value in BPM.
        ''')        


    # properties and conversions
    def _getText(self):
        if self._tempoText is None:
            return None
        return self._tempoText.text

    def _setText(self, value, updateNumberFromText=True):
        if value is None:
            self._tempoText = None
        elif isinstance(value, TempoText):
            self._tempoText = value
            self.textImplicit = False # must set here
        else:
            self._tempoText = TempoText(value)
            self.textImplicit = False # must set here

        if updateNumberFromText:
            self._updateNumberFromText()

    text = property(_getText, _setText, doc = 
        '''Get or set a text string for this MetronomeMark. Internally implemented as a :class:`~music21.tempo.TempoText` object, which stores the text in a :class:`~music21.expression.TextExpression` object. 

        >>> from music21 import *
        >>> mm = tempo.MetronomeMark(number=120)
        >>> mm.text == None 
        True
        >>> mm.text = 'medium fast'
        >>> mm.text
        'medium fast'
        ''')


    def _getNumber(self):
        return self._number # may be None
    
    def _setNumber(self, value, updateTextFromNumber=True):
        if not common.isNum(value):
            raise TempoException('cannot set number to a string')
        self._number = value
        self.numberImplicit = False
        if updateTextFromNumber:
            self._updateTextFromNumber()

    number = property(_getNumber, _setNumber, doc =
        '''Get and set the number, or the numerical value of the Metronome. 

        >>> from music21 import *
        >>> mm = tempo.MetronomeMark('slow')
        >>> mm.number
        52
        >>> mm.numberImplicit
        True
        >>> mm.number = 52.5
        >>> mm.number       
        52.5
        >>> mm.numberImplicit
        False
        ''')


    def _getNumberSounding(self):
        return self._numberSounding # may be None
    
    def _setNumberSounding(self, value):
        if not common.isNum(value):
            raise TempoException('cannot set numberSounding to a string')
        self._numberSounding = value

    numberSounding = property(_getNumberSounding, _setNumberSounding, doc =
        '''Get and set the numberSounding, or the numerical value of the Metronome that is used for playback independent of display. If numberSounding is None number is assumed to be numberSounding. 

        >>> from music21 import *
        >>> mm = tempo.MetronomeMark('slow')
        >>> mm.number
        52
        >>> mm.numberImplicit
        True
        >>> mm.numberSounding == None
        True
        >>> mm.numberSounding = 120
        >>> mm.numberSounding
        120
        ''')


    #--------------------------------------------------------------------------
    def getQuarterBPM(self, useNumberSounding=True):
        '''Get a BPM value where the beat is a quarter; must convert from the defined beat to a quarter beat. Will return None if no beat number is defined.

        This mostly used for generating MusicXML <sound> tags when necessary.

        >>> from music21 import *
        >>> mm = MetronomeMark(number=60, referent='half')
        >>> mm.getQuarterBPM()
        120.0
        >>> mm.referent = 'quarter'
        >>> mm.getQuarterBPM()
        60.0
        '''
        if useNumberSounding and self.numberSounding is not None:
            return convertTempoAtBeat(self.numberSounding, 
                self.referent.quarterLength, 1.0)
        if self.number is not None:
            # target quarter length is always 1.0
            return convertTempoAtBeat(self.number, 
                self.referent.quarterLength, 1.0)
        return None


    def setQuarterBPM(self, value, setNumber=True):
        '''Given a value in BPM, use it to set the value of this MetroneMark. BPM values are assumed to be refer only to quarter notes; different beat values, if definded here, will be scaled

        >>> from music21 import *
        >>> mm = MetronomeMark(number=60, referent='half')
        >>> mm.setQuarterBPM(240) # set to 240 for a quarter
        >>> mm.number  # a half is half as fast
        120.0
        '''
        # assuming a quarter value coming in, what is with our current beat
        value = convertTempoAtBeat(value, 1.0, self.referent.quarterLength)
        if not setNumber:
            # convert this to a quarter bpm
            self._numberSounding = value
        else: # go through property so as to set implicit status
            self.number = value


    def _getDefaultNumber(self, tempoText):
        '''Given a tempo text expression or an TempoText, get the default number.

        >>> from music21 import *
        >>> mm = MetronomeMark()
        >>> mm._getDefaultNumber('schnell')
        132
        >>> mm._getDefaultNumber('adagio')
        52
        '''
        if isinstance(tempoText, TempoText):
            tempoStr = tempoText.text
        else:
            tempoStr = tempoText
        post = None # returned if no match
        if tempoStr.lower() in defaultTempoValues.keys():
            post = defaultTempoValues[tempoStr.lower()]
        # an exact match
        elif tempoStr in defaultTempoValues.keys():
            post = defaultTempoValues[tempoStr]
        return post

    def _getDefaultText(self, number, spread=2):
        '''Given a tempo number try to get a text expression; presently only looks for approximate matches

        The `spread` value is a +/- shift around the default tempo indications defined in defaultTempoValues

        >>> from music21 import *
        >>> mm = MetronomeMark()
        >>> mm._getDefaultText(90)
        u'moderate'
        >>> mm._getDefaultText(201)
        u'prestissimo'
        '''
        if common.isNum(number):
            tempoNumber = number
        else: # try to convert
            tempoNumber = float(number)
        post = None # returned if no match
        # get a items and sort
        matches = []
        for tempoStr, tempoValue in defaultTempoValues.items():
            matches.append([tempoValue, tempoStr])
        matches.sort()
        #environLocal.printDebug(['matches', matches])
        post = None
        for tempoValue, tempoStr in matches:
            if (tempoNumber >= (tempoValue-spread) and tempoNumber <= 
                (tempoValue+spread)): # found a match
                post = tempoStr
                break 
        return post


    def getTextExpression(self, returnImplicit=False):
        '''If there is a TextExpression available that is not implicit, return it; otherwise, return None.

        >>> from music21 import *
        >>> mm = MetronomeMark('presto')
        >>> mm.number
        168
        >>> mm.numberImplicit
        True
        >>> mm.getTextExpression()
        <music21.expressions.TextExpression "presto">
        >>> mm.textImplicit
        False

        >>> mm = MetronomeMark(number=90)
        >>> mm.numberImplicit
        False
        >>> mm.textImplicit     
        True
        >>> mm.getTextExpression() == None
        True
        >>> mm.getTextExpression(returnImplicit=True)
        <music21.expressions.TextExpression "moderate">
        '''
        if self._tempoText is None:
            return None
        # if explicit, always return; if implicit, return if returnImplicit true
        if not self.textImplicit or (self.textImplicit and returnImplicit): 
            # adjust position if number is implicit; pass number implicit
            return self._tempoText.getTextExpression(
                numberImplicit=self.numberImplicit)







#-------------------------------------------------------------------------------
class MetricModulation(TempoIndication):
    '''A class for representing the relationship between two MetronomeMarks. Generally this relationship is one of equality.

    The `classicalStyle` attribute determines of the first MetronomeMark describes the new tempo, not the old (the reverse of expected usage).

    The `maintainBeat` attribute determines if, after an equality statement, the beat is maintained. 
    '''
    def __init__(self, value = None):
        TempoIndication.__init__(self)

        self.classicalStyle = False 
        self.maintainBeat = False
        self.transitionSymbol = '=' # accept different symbols
        # some old formats use arrows
        self.arrowDirection = None # can be left or right as well

        # showing parens or not
        self.parentheses = False 

        # store two MetronomeMark objects
        self._leftMetronome = None
        self._rightMetronome = None







#-------------------------------------------------------------------------------
def interpolateElements(element1, element2, sourceStream, 
    destinationStream, autoAdd = True):
    '''
    Assume that element1 and element2 are two elements in sourceStream 
    and destinationStream with other elements (say eA, eB, eC) between 
    them.  For instance, element1 could be the downbeat at offset 10
    in sourceStream (a Stream representing a score) and offset 20.5 
    in destinationStream (which might be a Stream representing the 
    timing of notes in particular recording at approximately but not 
    exactly qtr = 30). Element2 could be the following downbeat in 4/4, 
    at offset 14 in source but offset 25.0 in the recording:
    
    >>> from music21 import *
    >>> sourceStream = stream.Stream()
    >>> destinationStream = stream.Stream()
    >>> element1 = note.QuarterNote("C4")
    >>> element2 = note.QuarterNote("G4")
    >>> sourceStream.insert(10, element1)
    >>> destinationStream.insert(20.5, element1)
    >>> sourceStream.insert(14, element2)
    >>> destinationStream.insert(25.0, element2)
    
    
    Suppose eA, eB, and eC are three quarter notes that lie
    between element1 and element2 in sourceStream
    and destinationStream, as in:
    
    
    >>> eA = note.QuarterNote("D4")
    >>> eB = note.QuarterNote("E4")
    >>> eC = note.QuarterNote("F4")
    >>> sourceStream.insert(11, eA)
    >>> sourceStream.insert(12, eB)
    >>> sourceStream.insert(13, eC)
    >>> destinationStream.append([eA, eB, eC])  # not needed if autoAdd were true
    
    
    
    then running this function will cause eA, eB, and eC
    to have offsets 21.625, 22.75, and 23.875 respectively
    in destinationStream:
    
    
    
    >>> tempo.interpolateElements(element1, element2, sourceStream, destinationStream, autoAdd = False)
    >>> for el in [eA, eB, eC]:
    ...    print el.getOffsetBySite(destinationStream)
    21.625
    22.75
    23.875
    
    
    if the elements between element1 and element2 do not yet
    appear in destinationStream, they are automatically added
    unless autoAdd is False.
        
    
    (with the default autoAdd, elements are automatically added to new streams):
    
    
    >>> destStream2 = stream.Stream()
    >>> destStream2.insert(10.1, element1)
    >>> destStream2.insert(50.5, element2)
    >>> tempo.interpolateElements(element1, element2, sourceStream, destStream2)
    >>> for el in [eA, eB, eC]:
    ...    print el.getOffsetBySite(destStream2)
    20.2
    30.3
    40.4


    (unless autoAdd is set to false, in which case a Tempo Exception arises...)


    >>> destStream3 = stream.Stream()
    >>> destStream3.insert(100, element1)
    >>> destStream3.insert(500, element2)
    >>> tempo.interpolateElements(element1, element2, sourceStream, destStream3, autoAdd = False)
    Traceback (most recent call last):
    ...
    TempoException: Could not find element <music21.note.Note D> with id ...

    '''
    try:
        startOffsetSrc = element1.getOffsetBySite(sourceStream)
    except StreamException:
        raise TempoException("could not find element1 in sourceStream")
    try:
        startOffsetDest = element1.getOffsetBySite(destinationStream)
    except StreamException:
        raise TempoException("could not find element1 in destinationStream")
    
    try:
        endOffsetSrc = element2.getOffsetBySite(sourceStream)
    except StreamException:
        raise TempoException("could not find element2 in sourceStream")
    try:
        endOffsetDest = element2.getOffsetBySite(destinationStream)
    except StreamException:
        raise TempoException("could not find element2 in destinationStream")
    
    scaleAmount = ((endOffsetDest - startOffsetDest + 0.0)/(endOffsetSrc - startOffsetSrc + 0.0))
    
    interpolatedElements = sourceStream.getElementsByOffset(offsetStart = startOffsetSrc, offsetEnd = endOffsetSrc)
    
    for el in interpolatedElements:
        elOffsetSrc = el.getOffsetBySite(sourceStream)
        try:
            el.getOffsetBySite(destinationStream)
        except music21.DefinedContextsException:
            if autoAdd is True:
                destinationOffset = (scaleAmount * (elOffsetSrc - startOffsetSrc)) + startOffsetDest
                destinationStream.insert(destinationOffset, el)
            else:
                raise TempoException("Could not find element %s with id %d in destinationStream and autoAdd is false" % (repr(el), el.id))
        else:
            destinationOffset = (scaleAmount * (elOffsetSrc - startOffsetSrc)) + startOffsetDest
            el.setOffsetBySite(destinationStream, destinationOffset)
                
    




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                a = copy.copy(obj)
                b = copy.deepcopy(obj)


    def testSetup(self):
        MM1 = MetronomeMark(number=60, referent=music21.note.QuarterNote())
        self.assertEqual(MM1.number, 60)

        TM1 = TempoText("Lebhaft")
        self.assertEqual(TM1.text, "Lebhaft")
        

    def testUnicode(self):

        from music21 import tempo
        # test with no arguments
        tm = music21.tempo.TempoText()

        #environLocal.printDebug(['testing tempo instantion', tm])

        tm = music21.tempo.TempoText("adagio")
        mm = music21.tempo.MetronomeMark("adagio")
        self.assertEqual(mm.number, 52)
        self.assertEqual(mm.numberImplicit, True)

        self.assertEqual(mm.number, 52)
        tm2 = music21.tempo.TempoText(u"très vite")

        self.assertEqual(tm2.text, u'très vite')
        mm = tm2.getMetronomeMark()
        self.assertEqual(mm.number, 144)

        
    def testMetronomeMarkA(self):
        from music21 import tempo, duration
        mm = tempo.MetronomeMark()
        mm.number = 52 # should implicitly set text
        self.assertEqual(mm.text, 'adagio')
        self.assertEqual(mm.textImplicit, True)
        mm.text = 'slowish'
        self.assertEqual(mm.text, 'slowish')
        self.assertEqual(mm.textImplicit, False)
        # default
        self.assertEqual(mm.referent.quarterLength, 1.0)

        # setting the text first        
        mm = tempo.MetronomeMark()
        mm.text = 'presto'
        mm.referent = duration.Duration(3.0)
        self.assertEqual(mm.text, 'presto')
        self.assertEqual(mm.number, 168)
        self.assertEqual(mm.numberImplicit, True)
        mm.number = 200
        self.assertEqual(mm.number, 200)
        self.assertEqual(mm.numberImplicit, False)        
        # still have default
        self.assertEqual(mm.referent.quarterLength, 3.0)
        self.assertEqual(repr(mm), '<music21.tempo.MetronomeMark presto Dotted Half=200>')


    def testMetronomeMarkB(self):
        from music21 import tempo
        mm = tempo.MetronomeMark()
        # with no args these are set to None
        self.assertEqual(mm.numberImplicit, None)
        self.assertEqual(mm.textImplicit, None)


        mm = tempo.MetronomeMark(number=100)
        self.assertEqual(mm.number, 100)
        self.assertEqual(mm.numberImplicit, False)
        self.assertEqual(mm.text, None)
        # not set
        self.assertEqual(mm.textImplicit, None)

        mm = tempo.MetronomeMark(number=101, text='rapido')
        self.assertEqual(mm.number, 101)
        self.assertEqual(mm.numberImplicit, False)
        self.assertEqual(mm.text, 'rapido')
        self.assertEqual(mm.textImplicit, False)



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [MetronomeMark, TempoText, MetricModulation, interpolateElements]


if __name__ == "__main__":

    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof


