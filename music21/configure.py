#-------------------------------------------------------------------------------
# Name:         configure.py
# Purpose:      Installation and Configuration Utilties
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


import os
import re
import time
import sys
import threading 
import unittest

try:
    import readline
except ImportError:
    pass


import music21


# for time-out gather of arguments: possibly look at:
# http://code.activestate.com/recipes/576780/
# http://www.garyrobinson.net/2009/10/non-blocking-raw_input-for-python.html


from music21 import environment
_MOD = "configure.py"
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
reMacFinaleA = re.compile('/Applications/Finale 20[0-1][0-9][a-z]*/Finale 20[0-1][0-9][a-z]*.app')
# maybe not in a directory
reMacFinaleB = re.compile('/Applications/Finale 20[0-1][0-9][a-z]*.app')



#-------------------------------------------------------------------------------
class Action(threading.Thread):
    '''
    A thread-based action for performing remote actions, like downloading or opening in a webbrowser. 
    '''
    def __init__ (self, prompt, timeOutTime):
        threading.Thread.__init__(self)
        self.status = None

    def run(self):
        pass


#-------------------------------------------------------------------------------
# error objects, not exceptions
class DialogError(object):
    def __init__(self, src=None):
        self.src = src
    def __repr__(self):
        return '<music21.configure.%s: %s>' % (self.__class__.__name__, self.src)


class KeyInterruptError(DialogError):
    def __init__(self, src=None):
        DialogError.__init__(self, src=src)

class IncompleteInput(DialogError):
    def __init__(self, src=None):
        DialogError.__init__(self, src=src)

class NoInput(DialogError):
    def __init__(self, src=None):
        DialogError.__init__(self, src=src)



#-------------------------------------------------------------------------------
class Dialog(object):
    '''
    Model a dialog as a question and response. Have different subclases for different types of questions. Store all in a Conversation, or multiple dialog passes.
    '''
    def __init__(self, default=None):
        # store the result obtained from the user
        self._result = None
        # store a previously entered value, permitting undoing an action
        self._resultPrior = None
        # set the default
        # parse the default to permit expressive flexibility
        defaultCooked = self._parseUserInput(default)
        # if not any class of error:
        if not isinstance(defaultCooked, DialogError):
            self._default = defaultCooked
        else:
            # default is None by default; this cannot be a default value then
            self._default = None

    def _writeToUser(self, msg):
        sys.stdout.write(msg)

    def _readFromUser(self):
        '''Collect from user; return None if an empty response.
        '''
        post = None
        try:
            post = raw_input()
        except KeyboardInterrupt:
            return KeyInterruptError()
        except:
            return DialogError()
        return NoInput()

    def _incompleteInput(self, default=None):
        '''What to do if input is incomplete
        '''
        # need to call a yes or no on using default
        return True

    def _rawQuery(self):
        '''Return a multiline presentation of the question.
        '''
        pass

    def _parseUserInput(self, raw):
        '''Translate string to desired output. Pass None through (as no input), convert '' to None, and pass all other outputs as IncompleteInput objects. 
        '''
        return raw

    def _evaluateUserInput(self, raw):
        '''Evaluate the user's string entry after persing; do not return None: either return a valid response, default if available, or IncompleteInput object. 
        '''
        pass
        # define in subclass

    def askUser(self, force=None):
        '''Ask the user, display the querry. The force argument can be provided to test. Sets self._result; does not return a value.
        '''
        # ten attempts; not using a while so will ultimately break
        for i in range(10):
            if force is None:
                self._writeToUser(self._rawQuery())
                rawInput = self._readFromUser()
            else:
                environLocal.printDebug(['writeToUser:', self._rawQuery()])
                rawInput = force
            environLocal.printDebug(['rawInput', rawInput])
            # check for errors and handle
            if isinstance(rawInput, KeyboardInterrupt):
                # might return sam class back to caller as self._result
                break #fall out
            if isinstance(rawInput, DialogError):
                # issue ask if want to continue?
                break

            cookedInput = self._evaluateUserInput(rawInput)
            environLocal.printDebug(['cookedInput', cookedInput])
            if isinstance(cookedInput, IncompleteInput):
                # incomprehensible: should try again
                post = self._incompleteInput()
                if post is True: # continue
                    continue
                else:
                    break
            # everything else is good:
            else:
                # should be in proper format after evaluation
                self._result = cookedInput
                break
        # self._result may still be None

    def _performAction(self):
        '''The query might require an action to be performed: this would happen here, after getting the result from the user. 
        '''
        # possibly return an error class or None
        pass

    def getResult(self):
        '''Return the result, or None if not set. This may also do a processing routine that is part of the desired result. 
        '''
        self._performAction()
        return self._result 


#-------------------------------------------------------------------------------
class YesOrNo(Dialog):
    '''Ask a yes or no question.

    >>> from music21 import *
    >>> d = configure.YesOrNo(default=True)
    >>> d.askUser('yes') # force arg for testing
    >>> d.getResult()
    True
    '''
    def __init__(self, default=None):
        Dialog.__init__(self, default=default) 
    
    def _rawQuery(self):
        '''Return a multiline presentation of the question.

        >>> from music21 import *
        >>> d = configure.YesOrNo(default=True)
        >>> d._rawQuery()
        'Enter [Y]es or No: '
        >>> d = configure.YesOrNo(default=False)
        >>> d._rawQuery()
        'Enter Yes or [N]o: '
        '''
        msg = 'Enter Yes or No: '
        if self._default is True:
            msg = 'Enter [Y]es or No: '
        elif self._default is False:
            msg = 'Enter Yes or [N]o: '
        return msg

    def _parseUserInput(self, raw):
        '''Translate string to desired output. Pass None and '' (as no input), as NoInput objects, and pass all other outputs as IncompleteInput objects. 

        >>> from music21 import *
        >>> d = configure.YesOrNo()
        >>> d._parseUserInput('y')
        True
        >>> d._parseUserInput('')
        <music21.configure.NoInput: None>
        >>> d._parseUserInput('asdf')
        <music21.configure.IncompleteInput: asdf>
        '''
        if raw is None:
            return NoInput()
        # string; 
        raw = str(raw)
        raw = raw.strip()
        raw = raw.lower()
        if raw is '':
            return NoInput()

        if raw in ['yes', 'y', '1', 'true']:
            return True
        elif raw in ['no', 'n', '0', 'false']:
            return False
        # if no match, or an empty string
        return IncompleteInput(raw)

    def _evaluateUserInput(self, raw):
        '''Evaluate the user's string entry after persing; do not return None: either return a valid response, default if available, or IncompleteInput object. 
    
        >>> from music21 import *
        >>> d = configure.YesOrNo()
        >>> d._evaluateUserInput('y')
        True
        >>> d._evaluateUserInput('False')
        False
        >>> d._evaluateUserInput('') # there is no default, 
        <music21.configure.NoInput: None>
        >>> d._evaluateUserInput('wer') # there is no default, 
        <music21.configure.IncompleteInput: wer>

        >>> d = configure.YesOrNo('yes')
        >>> d._evaluateUserInput('') # there is a default
        True
        >>> d._evaluateUserInput('wbf') # there is a default
        <music21.configure.IncompleteInput: wbf>

        >>> d = configure.YesOrNo('n')
        >>> d._evaluateUserInput('') # there is a default
        False
        >>> d._evaluateUserInput(None) # None is processed as NoInput
        False
        >>> d._evaluateUserInput('asdfer') # None is processed as NoInput
        <music21.configure.IncompleteInput: asdfer>
        '''
        rawParsed = self._parseUserInput(raw)
        # means no answer: return default
        if isinstance(rawParsed, NoInput): 
            if self._default is not None:
                return self._default
        # could be IncompleteInput, NoInput, or a proper, valid answer
        return rawParsed






#-------------------------------------------------------------------------------
# class Prompt(threading.Thread):
#     def __init__ (self, prompt, timeOutTime):
#         threading.Thread.__init__(self)
#         self.status = None
#         self.timeLeft = timeOutTime
#         self.prompt = prompt
# 
#     def removeTime(self, value):
#         self.timeLeft -= value
# 
#     def printPrompt(self):
#         sys.stdout.write('%s: ' % self.prompt)
# 
#     def run(self):
#         self.printPrompt() # print on first call
#         self.status = raw_input()
# 
# 
# def getResponseOrTimeout(prompt='provide a value', timeOutTime=16):
# 
#     current = Prompt(prompt=prompt, timeOutTime=timeOutTime)
#     current.start()
#     reportInterval = 4
#     updateInterval = 1
#     intervalCount = 0
# 
#     post = None
#     while True:
#     #for host in range(60,70):
#         if not current.isAlive() or current.status is not None:
#             break
#         if current.timeLeft <= 0:
#             break
#         time.sleep(updateInterval)
#         current.removeTime(updateInterval)
# 
#         if intervalCount % reportInterval == reportInterval - 1:
#             sys.stdout.write('\ntime out in %s seconds\n' % current.timeLeft)
#             current.printPrompt()
# 
#         intervalCount += 1
#     #for o in objList:
#         # can have timeout argument, otherwise blocks
#         #o.join() # wait until the thread terminates
# 
#     post = current.status
#     # this thread will remain active until the user provides values
# 
#     if post == None:
#         print('got no value')
#     else:
#         print ('got: %s' % post)


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass

    def testYesOrNo(self):
        d = YesOrNo(default=True)
        d.askUser()
        environLocal.printDebug(['getResult():', d.getResult()])

        d = YesOrNo(default=False)
        d.askUser()
        environLocal.printDebug(['getResult():', d.getResult()])



class Test(unittest.TestCase):
    
    def runTest(self):
        pass




if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        te = TestExternal()

        # arg[1] is test to launch
        if sys.argv[1] == 'te':
            # run test external
            getattr(te, sys.argv[2])()
        if hasattr(t, sys.argv[1]): 
            getattr(t, sys.argv[1])()

#------------------------------------------------------------------------------
# eof

