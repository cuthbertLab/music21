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
    pass

class KeyInterruptError(DialogError):
    pass

class IncompleteInput(DialogError):
    pass



class Dialog(object):
    '''
    Model a dialog as a question and response. Have different subclases for different types of questions. Store all in a Conversation, or multiple dialog passes.
    '''
    def __init__(self, default=None):
        # store the result obtained from the user
        self._result = None
        # store a previously entered value, permitting undoing an action
        self._resultPrior = None
        self._default = default

    def _writeToUser(self, msg):
        sys.stdout.write(msg)

    def _readFromUser(self):
        '''Collect from user; return 
        '''
        post = None
        try:
            post = raw_input()
        except KeyboardInterrupt:
            return KeyInterruptError()
        except:
            return DialogError()

    def _incompleteInput(self, default=None):
        '''What to do if input is incomplete
        '''
        # need to call a yes or no on using default
        return True

    def _rawQuery(self):
        '''Return a multiline presentation of the question.
        '''
        pass

    def _evaluateUserInput(self, raw):
        '''Evaluate the user's string entry; this may also try to perform a secondary arction
        '''
        raw = raw.strip()

    def askUser(self, force=None):
        '''Ask the user, display the querry.
        '''
        # ten attempts; not using a while so will ultimately break
        for i in range(10):
            if force is None:
                self._writeToUser(self._rawQuery())
                rawInput = self._readFromUser()
            else:
                environLocal.printDebug(['writeToUser:', self._rawQuery()])
                rawInput = force

            # check for errors and handle
            if isinstance(rawInput, KeyboardInterrupt):
                # might return sam class back to caller as self._result
                break #fall out
            if isinstance(rawInput, DialogError):
                # issue ask if want to continue?
                break

            cookedInput = self._evaluateUserInput(rawInput)
            if isinstance(cookedInput, IncompleteInput):
                # incomprehensible: should tyr again
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
        return None # do not return values?

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

    def _evaluateUserInput(self, raw):
        '''Evaluate the user's string entry
    
        >>> from music21 import *
        >>> d = configure.YesOrNo()
        >>> d._evaluateUserInput('y')
        True
        >>> d._evaluateUserInput('False')
        False
        '''
        if raw is None: # means no answer: return default
            return self._default 

        raw = raw.strip()
        if raw.lower() in [True, 'yes', 'y', 1, 'true']:
            return True
        elif raw.lower() in [False, 'no', 'n', 0, 'false']:
            return False
        elif raw == '': # no answer
            if self._default is not None:
                return self._default 
        # if nothing passes, return an incomplete input object
        return IncompleteInput()







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
        d = YesOrNo(default='yes')
        d.askUser()
        environLocal.printDebug(['getResult():', d.getResult()])

        d = YesOrNo(default='no')
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

