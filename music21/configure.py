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
class DialogException(Exception):
    pass

#-------------------------------------------------------------------------------
class Dialog(object):
    '''
    Model a dialog as a question and response. Have different subclases for different types of questions. Store all in a Conversation, or multiple dialog passes.

    A `default`, if provided, is returned if the users provides no input and just enters return. 

    The `tryAgain` option determines if, if a user provides incomplete or no response, and there is no default (for no response), whether the user is given another chance to provide valid input. 

    The `promptHeader` is a string header that is placed in front of any common header for this dialog.
    '''
    def __init__(self, default=None, tryAgain=True, promptHeader=None):
        # store the result obtained from the user
        self._result = None
        # store a previously entered value, permitting undoing an action
        self._resultPrior = None
        # set the default
        # parse the default to permit expressive flexibility
        defaultCooked = self._parseUserInput(default)
        # if not any class of error:
        #environLocal.printDebug(['Dialog: defaultCooked:', defaultCooked])

        if not isinstance(defaultCooked, DialogError):
            self._default = defaultCooked
        else:
            # default is None by default; this cannot be a default value then
            self._default = None
        # if we try again
        self._tryAgain = tryAgain
        self._promptHeader = promptHeader


    def _writeToUser(self, msg):
        sys.stdout.write(msg)

    def _readFromUser(self):
        '''Collect from user; return None if an empty response.
        '''
        try:
            post = raw_input()
            return post
        except KeyboardInterrupt:
            return KeyInterruptError()
        except:
            return DialogError()
        return NoInput()

    def _askTryAgain(self, default=True, force=None):
        '''What to do if input is incomplete

        >>> from music21 import *
        >>> d = configure.YesOrNo(default=True)
        >>> d._askTryAgain(force='yes')
        True
        >>> d._askTryAgain(force='n')
        False
        >>> d._askTryAgain(force='') # gets default
        True
        >>> d._askTryAgain(force='weree') # error gets false
        False
        '''
        # need to call a yes or no on using default
        d = YesOrNo(default=default, tryAgain=False, 
            promptHeader='Your input was not understood. Try Again?')
        d.askUser(force=force)
        post = d.getResult()
        # if any errors are found, return False
        if isinstance(post, DialogError):
            return False
        else:
            return post

    def _rawQueryPrepareHeader(self, msg=''):
        '''Prepare the header, given a string.

        >>> from music21 import configure
        >>> d = configure.Dialog()
        >>> d._rawQueryPrepareHeader('test')
        'test'
        >>> d = configure.Dialog(promptHeader='what are you doing?')
        >>> d._rawQueryPrepareHeader('test')
        'what are you doing? test'
        '''
        if self._promptHeader is not None:
            header = self._promptHeader.strip()
            if header.endswith('?'):
                div = ''
            else:
                div = ':'
            msg = '%s%s %s' % (header, div, msg)
        return msg

    def _rawQueryPrepareFooter(self, msg=''):
        '''Prepare the end of the query message
        '''
        if self._default is not None:
            msg = msg.strip()
            if msg.endswith(':'):
                div = ':'
                msg = msg[:-1]
                msg.strip()
            else:   
                div = ''
            default = self._formatResultForUser(self._default)
            # leave a space at end
            msg = '%s (default is %s)%s ' % (msg, default, div)
        return msg


    def _rawQuery(self):
        '''Return a multiline presentation of the question.
        '''
        pass

    def _formatResultForUser(self, result):
        '''For various result options, we may need to at times convert the internal representation of the result into something else. For example, we might present the user with 'Yes' or 'No' but store the result as True or False.
        '''
        # override in subclass
        return resut

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

            # need to not catch no NoInput nor IncompleteInput classes, as they 
            # will be handled in evaluation
            cookedInput = self._evaluateUserInput(rawInput)
            environLocal.printDebug(['cookedInput', cookedInput])

            # if no default and no input, we get here (default supplied in 
            # evaluate
            if (isinstance(cookedInput, NoInput) or 
                isinstance(cookedInput, IncompleteInput)):
                # set result to these objects whether or not try again
                self._result = cookedInput
                if self._tryAgain:
                    # only returns True or False
                    if self._askTryAgain():
                        pass
                    else: # this will keep whatever the cooked was
                        break 
                else:
                    break
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
        # result may be NoInput or IncompleteInput objects
        return self._result 


#-------------------------------------------------------------------------------
class YesOrNo(Dialog):
    '''Ask a yes or no question.

    >>> from music21 import *
    >>> d = configure.YesOrNo(default=True)
    >>> d.askUser('yes') # force arg for testing
    >>> d.getResult()
    True

    >>> d = configure.YesOrNo(tryAgain=False)
    >>> d.askUser('junk') # force arg for testing
    >>> d.getResult()
     <music21.configure.IncompleteInput: junk>
    '''
    def __init__(self, default=None, tryAgain=True, promptHeader=None):
        Dialog.__init__(self, default=default, tryAgain=tryAgain, promptHeader=promptHeader) 
    

    def _formatResultForUser(self, result):
        '''For various result options, we may need to at times convert the internal representation of the result into something else. For example, we might present the user with 'Yes' or 'No' but store the result as True or False.
        '''
        if result is True:
            return 'Yes'
        elif result is False:
            return 'No'
        # while a result might be an error object, this method should probably 
        # neve be called with such objects.
        else:
            raise DialogException('attempting to format result for user: %s' % result)

    def _rawQuery(self):
        '''Return a multiline presentation of the question.

        >>> from music21 import *
        >>> d = configure.YesOrNo(default=True)
        >>> d._rawQuery()
        'Enter Yes or No (default is Yes): '
        >>> d = configure.YesOrNo(default=False)
        >>> d._rawQuery()
        'Enter Yes or No (default is No): '

        >>> from music21 import *
        >>> d = configure.YesOrNo(default=True, promptHeader='Would you like more time?')
        >>> d._rawQuery()
        'Would you like more time? Enter Yes or No (default is Yes): '
        '''
        msg = 'Enter Yes or No: '
        msg = self._rawQueryPrepareHeader(msg)
        msg = self._rawQueryPrepareFooter(msg)
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
        '''Evaluate the user's string entry after persing; do not return None: either return a valid response, default if available, IncompleteInput, NoInput objects. 
    
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
class SelectFromList(Dialog):
    '''General class to select values from a list.

    >>> from music21 import *
    '''
    def __init__(self, default=None, tryAgain=True, promptHeader=None):
        Dialog.__init__(self, default=default, tryAgain=tryAgain, promptHeader=promptHeader) 
    

    def _getValidResults(self, force=None):
        '''Return a list of valid results that are possible and should be displayed to the user. These will be processed by _formatResultForUser before usage.
        '''
        # customize in subclass
        if force is not None:
            return force
        else:
            return []

    def _formatResultForUser(self, result):
        '''Reduce each complet file path to stub, or otherwise compact display
        '''
        return result


    def _rawQuery(self, force=None):
        '''Return a multiline presentation of the question.

        >>> from music21 import *
        >>> d = configure.SelectFromList()
        >>> d._rawQuery(['a', 'b', 'c'])
        '[1] a\\n[2] b\\n[3] c\\nSelect a number from the preceding options: '

        >>> d = configure.SelectFromList(default=1)
        >>> d._default
        1
        >>> d._rawQuery(['a', 'b', 'c'])
        '[1] a\\n[2] b\\n[3] c\\nSelect a number from the preceding options (default is 1): '

        '''
        msg = []
        i = 1
        for entry in self._getValidResults(force=force):
            sub = self._formatResultForUser(entry)
            msg.append('[%s] %s' % (i, sub))
            i += 1
        head = '\n'.join(msg)

        tail = 'Select a number from the preceding options: '
        tail = self._rawQueryPrepareHeader(tail)
        tail = self._rawQueryPrepareFooter(tail)
        return head + '\n' + tail

    def _parseUserInput(self, raw):
        '''Convert all values to an integer, or return NoInput or IncompleteInput. Do not yet evaluate whether the number is valid in the context of the selection choices. 

        >>> from music21 import *
        >>> d = configure.SelectFromList()
        '''
        #environLocal.printDebug(['SelectFromList', '_parseUserInput', 'raw', raw])
        if raw is None:
            return NoInput()
        if raw is '':
            return NoInput()
        # try to convert string into a number
        try:
            post = int(raw)
        # catch all problems
        except (ValueError, TypeError, ZeroDivisionError):
            return IncompleteInput(raw)
        return post

    
    def _evaluateUserInput(self, raw):
        '''Evaluate the user's string entry after persing; do not return None: either return a valid response, default if available, IncompleteInput, NoInput objects. 
    
        >>> from music21 import *
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
        print
        environLocal.printDebug(['starting: YesOrNo()'])
        d = YesOrNo()
        d.askUser()
        environLocal.printDebug(['getResult():', d.getResult()])

        print
        environLocal.printDebug(['starting: YesOrNo(default=True)'])
        d = YesOrNo(default=True)
        d.askUser()
        environLocal.printDebug(['getResult():', d.getResult()])

        print
        environLocal.printDebug(['starting: YesOrNo(default=False)'])
        d = YesOrNo(default=False)
        d.askUser()
        environLocal.printDebug(['getResult():', d.getResult()])



class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testSelectFromList(self):
        from music21 import configure
        d = configure.SelectFromList(default=1)
        self.assertEqual(d._default, 1)




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

