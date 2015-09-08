
from music21.duration import DurationException, typeToDuration, typeFromNumDict, convertTypeToQuarterLength, ordinalTypeFromNum, quarterLengthToClosestType, dottedMatch, nextLargerType, quarterLengthToTuplet
from music21 import common
from music21.common import opFrac

def quarterLengthToDurations(qLen):
    '''
    Returns a List of new DurationTuples given a quarter length.

    For many simple quarterLengths, the list will have only a
    single element.  However, for more complex durations, the list
    could contain several durations (presumably to be tied to each other).

    (All quarterLengths can, technically, be notated as a single unit
    given a complex enough tuplet, but we don't like doing that).

    This is mainly a utility function. Much faster for many purposes
    is something like::

       d = duration.Duration()
       d.quarterLength = 251.231312

    and then let Duration automatically create Duration Components as necessary.

    These examples use unitSpec() to get a concise summary of the contents

    '''
    post = []
    qLen = opFrac(qLen)

    if qLen < 0:
        raise DurationException("qLen cannot be less than Zero.  Read Lewin, GMIT for more details...")

    elif qLen == 0:
        post.append(ZeroDuration()) # this is a DurationUnit subclass
        return post

    # try match to type, get next lowest
    typeFound, match = quarterLengthToClosestType(qLen)
    if match:
        post.append(DurationUnit(typeFound))
    else:
        if typeFound is None :
            raise DurationException('cannot find duration types near quarter length %s' % qLen)

    # try dots
    # using typeFound here is the largest type that is not greater than qLen
    if not match:
        dots, durType = dottedMatch(qLen)
        if durType is not False:
            dNew = DurationUnit(durType)
            dNew.dots = dots
            post.append(dNew)
            match = True

    typeNext = nextLargerType(typeFound)
    # try tuplets
    # using typeNext is the next type that is larger than then the qLen
    if not match:
        # just get the first candidate
        tupleCandidates = quarterLengthToTuplet(qLen, 1)
        if len(tupleCandidates) > 0:
            # assume that the first, using the smallest type, is best
            dNew = DurationUnit(typeNext)
            dNew.tuplets = (tupleCandidates[0],)
            post.append(dNew)
            match = True

    # if we do not have a match, remove the largest type not greater
    # and recursively apply
    if not match:
        post.append(DurationUnit(typeFound))
        qLenRemainder = qLen - typeToDuration[typeFound]
        if qLenRemainder < 0:
            raise DurationException('cannot reduce quarter length (%s)' % qLenRemainder)
        # trying a fixed minimum limit
        # this it do deal with common errors in processing
        if qLenRemainder > .004: # 1e-4 grain almostEquals -- TODO: FIX
            try:
                if len(post) > 6: # we probably have a problem
                    raise DurationException('duration exceeds 6 components, with %s qLen left' % (qLenRemainder))
                else:
                    post += quarterLengthToDurations(qLenRemainder)
            except RuntimeError: # if recursion exceeded
                msg = 'failed to find duration for qLen %s, qLenRemainder %s, post %s' % (qLen, qLenRemainder, post)
                raise DurationException(msg)
    return post



class DurationUnit(object):
    '''
    A DurationUnit is a duration notation that (generally) can be notated with
    a single notation unit, such as one note head, without a tie.

    DurationUnits are not usually instantiated by users of music21, but are
    used within Duration objects to model the containment of numerous summed
    components.

    Like Durations, DurationUnits have the option of unlinking the
    quarterLength and its representation on the page. For instance, in 12/16,
    Brahms sometimes used a dotted half note to indicate the length of 11/16th
    of a note. (see Don Byrd's Extreme Notation webpage for more information).
    Since this duration can be expressed by a single graphical unit in Brahms's
    shorthand, it can be modeled by a single DurationUnit of unliked
    graphical/temporal representation.

    Additional types are needed beyond those in Duration::

        * 'zero' type for zero-length durations
        * 'unexpressible' type for anything that cannot
          be expressed as a single notation unit, and thus
          needs a full Duration object (such as 2.5 quarterLengths.)

    '''

    ### CLASS VARIABLES ###



    ### INITIALIZER ###

    def __init__(self, prototype='quarter'):
        self.linked = True  # default is True
        self._type = ""
        # dots can be a float for expressing Crumb dots (1/2 dots)
        # dots is a tuple for rarely used: dotted-dotted notes;
        #  e.g. dotted-dotted half in 9/8 expressed as 1,1
        self._dotGroups = ()
        self._tuplets = ()  # an empty tuple
        if common.isNum(prototype):
            self._qtrLength = opFrac(prototype)
            self._typeNeedsUpdating = True
            self._quarterLengthNeedsUpdating = False
        else:
            if prototype not in typeToDuration:
                raise DurationException('type (%s) is not valid' % type)
            self.type = prototype
            self._qtrLength = 0.0
            self._typeNeedsUpdating = False
            self._quarterLengthNeedsUpdating = True

    ### SPECIAL METHODS ###

    def __eq__(self, other):
        '''
        Test equality. Based on type, dots, tuplets, and quarterLength

        >>> aDur = duration.DurationUnit('quarter')
        >>> bDur = duration.DurationUnit('16th')
        >>> cDur = duration.DurationUnit('16th')
        >>> aDur == bDur
        False

        >>> cDur == bDur
        True
        '''
        if other is None or not isinstance(other, DurationUnit):
            return False
        if self.type == other.type:
            if self.dots == other.dots:
                if self.tuplets == other.tuplets:
                    if self.quarterLength == other.quarterLength:
                        return True
        return False

    def __ne__(self, other):
        '''
        Test not equality.

        >>> aDur = duration.DurationUnit('quarter')
        >>> bDur = duration.DurationUnit('16th')
        >>> cDur = duration.DurationUnit('16th')
        >>> aDur != bDur
        True

        >>> cDur != bDur
        False
        '''
        return not self.__eq__(other)

    def __repr__(self):
        '''
        Return a string representation.

        >>> aDur = duration.DurationUnit('quarter')
        >>> repr(aDur)
        '<music21.duration.DurationUnit 1.0>'

        '''
        qlr = self.quarterLength
        
        return '<music21.duration.DurationUnit %s>' % qlr

    ### PUBLIC METHODS ###

    def appendTuplet(self, newTuplet):
        newTuplet.frozen = True
        self._tuplets = self._tuplets + (newTuplet,)
        self._quarterLengthNeedsUpdating = True

    def augmentOrDiminish(self, amountToScale, inPlace=True):
        '''
        Given a number greater than zero, multiplies the current quarterLength
        of the duration by the number and resets the components for the
        duration (by default).  Or if inPlace is set to False, returns a new
        duration that has the new length.


        Note that the default for inPlace is the opposite of what it is for
        augmentOrDiminish on a Stream.  This is done purposely to reflect the
        most common usage.

        >>> bDur = duration.DurationUnit('16th')
        >>> bDur
        <music21.duration.DurationUnit 0.25>

        >>> bDur.augmentOrDiminish(2)
        >>> bDur.quarterLength
        0.5
        >>> bDur.type
        'eighth'
        >>> bDur
        <music21.duration.DurationUnit 0.5>

        >>> bDur.augmentOrDiminish(4)
        >>> bDur.type
        'half'
        >>> bDur
        <music21.duration.DurationUnit 2.0>

        >>> bDur.augmentOrDiminish(.125)
        >>> bDur.type
        '16th'
        >>> bDur
        <music21.duration.DurationUnit 0.25>

        >>> cDur = bDur.augmentOrDiminish(16, inPlace=False)
        >>> cDur, bDur
        (<music21.duration.DurationUnit 4.0>, <music21.duration.DurationUnit 0.25>)
        '''
        if not amountToScale > 0:
            raise DurationException('amountToScale must be greater than zero')

        if inPlace:
            post = self
        else:
            post = DurationUnit()
        # note: this is not yet necessary, as changes are configured
        # by quarterLength, and this process generates new tuplets
        # if alternative scaling methods are used for performance, this
        # method can be used.
#         for tup in post._tuplets:
#             tup.augmentOrDiminish(amountToScale, inPlace=True)
        # possible look for convenient optimizations for easy scaling
        # not sure if linked should be altered?
        post.quarterLength = self.quarterLength * amountToScale
        if not inPlace:
            return post
        else:
            return None

    def setTypeFromNum(self, typeNum):
        #numberFound = None
        if str(typeNum) in typeFromNumDict:
            self.type = typeFromNumDict[str(typeNum)]
        else:
            raise DurationException("cannot find number %s" % typeNum)

    def updateQuarterLength(self):
        '''
        Updates the quarterLength if linked is True. Called by
        self._getQuarterLength if _quarterLengthNeedsUpdating is set to True.

        To set quarterLength, use self.quarterLength.

        >>> bDur = duration.DurationUnit('16th')
        >>> bDur.quarterLength
        0.25

        >>> bDur.linked = False
        >>> bDur.quarterLength = 234
        >>> bDur.quarterLength
        234.0

        >>> bDur.type
        '16th'

        >>> bDur.linked = True # if linking is restored, type is used to get qLen
        >>> bDur.updateQuarterLength()
        >>> bDur.quarterLength
        0.25
        '''
        if self.linked is True:
            self._qtrLength = convertTypeToQuarterLength(
                self.type,
                self.dots,
                self.tuplets,
                self.dotGroups,
                ) # add self.dotGroups
        self._quarterLengthNeedsUpdating = False

    def updateType(self):
        if self.linked is True:
            # cant update both at same time
            self._quarterLengthNeedsUpdating = False
            tempDurations = quarterLengthToDurations(self.quarterLength)
            if len(tempDurations) > 1:
                self.type = 'unexpressible'
                self.dots = 0
                self.tuplets = ()
            else:
                self.type = tempDurations[0].type
                self.dots = tempDurations[0].dots
                self.tuplets = tempDurations[0].tuplets
        self._typeNeedsUpdating = False

    ### PUBLIC PROPERTIES ###

    @property
    def dotGroups(self):
        '''
        _dots is a list (so we can do weird things like dot groups)
        _getDotGroups lets you do the entire list (as a tuple)

        >>> d1 = duration.DurationUnit('half')
        >>> d1.dotGroups = [1, 1]  # dotted dotted half
        >>> d1.dots
        1

        >>> d1.dotGroups
        (1, 1)

        >>> d1.quarterLength
        4.5
        '''
        if self._typeNeedsUpdating:
            self.updateType()
        return tuple(self._dots)

    @dotGroups.setter
    def dotGroups(self, listValue):
        '''
        Sets the number of dots in a dot group
        '''
        self._quarterLengthNeedsUpdating = True
        if common.isListLike(listValue):
            if not isinstance(listValue, list):
                self._dots = list(listValue)
            else:
                self._dots = listValue
        else:
            raise DurationException("number of dots must be a number")

    @property
    def dots(self):
        '''
        _dots is a list (so we can do weird things like dot groups)
        Normally we only want the first element.
        So that's what dots returns...

        >>> a = duration.DurationUnit()
        >>> a.dots # dots is zero before assignment
        0

        >>> a.type = 'quarter'
        >>> a.dots = 1
        >>> a.quarterLength
        1.5

        >>> a.dots = 2
        >>> a.quarterLength
        1.75
        '''
        if self._typeNeedsUpdating:
            self.updateType()
        return self._dots[0]

    @dots.setter
    def dots(self, value):
        if value != self._dots[0]:
            self._quarterLengthNeedsUpdating = True
        if common.isNum(value):
            self._dots = (value,)
        else:
            raise DurationException("number of dots must be a number")

    @property
    def fullName(self):
        '''
        Return the most complete representation of this Duration, providing
        dots, type, tuplet, and quarter length representation.

        >>> d = duration.DurationUnit()
        >>> d.quarterLength = 1.5
        >>> d.fullName
        'Dotted Quarter'

        >>> d = duration.DurationUnit()
        >>> d.quarterLength = 1.75
        >>> d.fullName
        'Double Dotted Quarter'

        >>> d = duration.DurationUnit()
        >>> d.type = 'half'
        >>> d.fullName
        'Half'

        >>> d = duration.DurationUnit()
        >>> d.type = 'longa'
        >>> d.fullName
        'Imperfect Longa'

        >>> d.dots = 1
        >>> d.fullName
        'Perfect Longa'
        '''
        dots = self.dots
        if dots == 1:
            dotStr = 'Dotted'
        elif dots == 2:
            dotStr = 'Double Dotted'
        elif dots == 3:
            dotStr = 'Triple Dotted'
        elif dots == 4:
            dotStr = 'Quadruple Dotted'
        elif dots > 4:
            dotStr = ('%d-Times Dotted' % dots)
        else:
            dotStr = None

        tuplets = self.tuplets
        #environLocal.printDebug(['tuplets', tuplets])
        tupletStr = None
        if len(tuplets) > 0:
            tupletStr = []
            for tup in tuplets:
                tupletStr.append(tup.fullName)
            tupletStr = ' '.join(tupletStr)
            #environLocal.printDebug(['tupletStr', tupletStr, tuplets])

        msg = []
        # type added here
        typeStr = self.type
        if dots >= 2 or (typeStr != 'longa' and typeStr != 'maxima'):
            if dotStr is not None:
                msg.append('%s ' % dotStr)
        else:
            if dots == 0:
                msg.append('Imperfect ')
            elif dots == 1:
                msg.append('Perfect ')

        if typeStr[0] in ('1', '2', '3', '5', '6'):
            pass # do nothing with capitalization
        else:
            typeStr = typeStr.title()

        if typeStr.lower() == 'complex':
            pass
        else:
            msg.append('%s ' % typeStr)

        if tupletStr is not None:
            msg.append('%s ' % tupletStr)
        # only add QL display if there are no dots or tuplets
        if tupletStr is not None or dots >= 3 or typeStr.lower() == 'complex':
            qlStr = common.mixedNumeral(self.quarterLength)
            msg.append('(%s QL)' % (qlStr))

        return ''.join(msg).strip() # avoid extra space

    @property
    def ordinal(self):
        '''
        Converts type to an ordinal number where maxima = 1 and 1024th = 14;
        whole = 4 and quarter = 6.  Based on duration.ordinalTypeFromNum

        >>> a = duration.DurationUnit('whole')
        >>> a.ordinal
        4

        >>> b = duration.DurationUnit('maxima')
        >>> b.ordinal
        1

        >>> c = duration.DurationUnit('1024th')
        >>> c.ordinal
        14
        '''
        if self._typeNeedsUpdating:
            self.updateType()
        ordinalFound = None
        for i in range(len(ordinalTypeFromNum)):
            if self.type == ordinalTypeFromNum[i]:
                ordinalFound = i
                break
        if ordinalFound is None:
            raise DurationException(
                "Could not determine durationNumber from %s" % ordinalFound)
        else:
            return ordinalFound

    def _getQuarterLengthFloat(self):
        '''
        Property for getting or setting the quarterLength of a
        DurationUnit.

        >>> a = duration.DurationUnit()
        >>> a.quarterLength = 3
        >>> a.quarterLength
        3.0

        >>> a.type
        'half'

        >>> a.dots
        1

        >>> a.quarterLength = .5
        >>> a.type
        'eighth'

        >>> a.quarterLength = .75
        >>> a.type
        'eighth'

        >>> a.dots
        1

        >>> b = duration.DurationUnit()
        >>> b.quarterLength = 16
        >>> b.type
        'longa'
        '''
        if self._quarterLengthNeedsUpdating:
            self.updateQuarterLength()
        return float(self._qtrLength)
    
    def _getQuarterLengthRational(self):
        '''
        Property for getting or setting the quarterLength of a
        DurationUnit.

        This will return a float if it's binary representable, or a fraction if not...

        >>> a = duration.DurationUnit()
        >>> a.quarterLength = 3
        >>> a.quarterLength
        3.0
        >>> a.quarterLength = .75
        >>> a.quarterLength
        0.75
        >>> a.quarterLength = 2.0/3
        >>> a.type
        'quarter'
        >>> a.tuplets
        (<music21.duration.Tuplet 3/2/quarter>,)
        >>> a.quarterLength
        Fraction(2, 3)            
        '''
        if self._quarterLengthNeedsUpdating:
            self.updateQuarterLength()
        return self._qtrLength
        

    def _setQuarterLength(self, value):
        '''Set the quarter note length to the specified value.

        (We no longer unlink if quarterLength is greater than a longa)

        >>> a = duration.DurationUnit()
        >>> a.quarterLength = 3
        >>> a.type
        'half'
        >>> a.dots
        1

        >>> a.quarterLength = .5
        >>> a.type
        'eighth'

        >>> a.quarterLength = .75
        >>> a.type
        'eighth'
        >>> a.dots
        1

        >>> b = duration.DurationUnit()
        >>> b.quarterLength = 16
        >>> b.type
        'longa'

        >>> c = duration.DurationUnit()
        >>> c.quarterLength = 129
        >>> c.type
        Traceback (most recent call last):
        DurationException: cannot get the next larger of duplex-maxima        
        '''
        if not common.isNum(value):
            raise DurationException(
            "not a valid quarter length (%s)" % value)
            
        if self.linked:
            self._typeNeedsUpdating = True
        
        value = opFrac(value)
        self._qtrLength = value

    quarterLength      = property(_getQuarterLengthRational, _setQuarterLength)
    quarterLengthFloat = property(_getQuarterLengthFloat, _setQuarterLength)

    @property
    def tuplets(self):
        '''Return a tuple of Tuplet objects '''
        if self._typeNeedsUpdating:
            self.updateType()
        return self._tuplets

    @tuplets.setter
    def tuplets(self, value):
        '''Takes in a tuple of Tuplet objects
        '''
        if not isinstance(value, tuple):
            raise DurationException(
            "value submitted (%s) is not a tuple of tuplets" % value)
        if self._tuplets != value:
            self._quarterLengthNeedsUpdating = True
        # note that in some cases this methods seems to be called more
        # often than necessary
        #environLocal.printDebug(['assigning tuplets in DurationUnit',
        #                         value, id(value)])
        for thisTuplet in value:
            thisTuplet.frozen = True
        self._tuplets = value

    @property
    def type(self):
        '''
        Property for getting or setting the type of a DurationUnit.

        >>> a = duration.DurationUnit()
        >>> a.quarterLength = 3
        >>> a.type
        'half'

        >>> a.dots
        1

        >>> a.type = 'quarter'
        >>> a.quarterLength
        1.5

        >>> a.type = '16th'
        >>> a.quarterLength
        0.375
        '''
        if self._typeNeedsUpdating:
            self.updateType()
        return self._type

    @type.setter
    def type(self, value):
        if value not in typeToDuration:
            raise DurationException("no such type exists: %s" % value)
        if value != self._type:  # only update if different
            # link status will be checked in quarterLengthNeeds updating
            self._quarterLengthNeedsUpdating = True
        self._type = value


#-------------------------------------------------------------------------------

