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
import textwrap


try:
    import readline
except ImportError:
    pass

# may need to not import any music21 here
from music21 import common
from music21 import environment
_MOD = "configure.py"
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
# match finale name, which may be directory or something else
reFinaleApp = re.compile('Finale 20[0-1][0-9][a-z]*.app')
reFinaleExe = re.compile('Finale 20[0-1][0-9][a-z]*.exe')
reFinaleReaderApp = re.compile('Finale Reader.app')
reMuseScoreApp = re.compile('MuseScore.app')


urlMusic21 = 'http://mit.edu/music21'
urlFinaleReader = 'http://www.finalemusic.com/Reader'
urlMuseScore = 'http://musescore.org'
urlGettingStarted = 'http://mit.edu/music21/doc/html/quickStart.html'

LINE_WIDTH = 80

#-------------------------------------------------------------------------------
# class Action(threading.Thread):
#     '''
#     A thread-based action for performing remote actions, like downloading or opening in a webbrowser. 
#     '''
#     def __init__ (self, prompt, timeOutTime):
#         threading.Thread.__init__(self)
#         self.status = None
# 
#     def run(self):
#         pass


#-------------------------------------------------------------------------------


def writeToUser(msg, wrap=True):
    '''Display a message to the user
    '''
    # wrap everything to 60 lines
    if common.isListLike(msg):
        lines = msg
    else:
        # divide into lines if lines breaks are already in place
        lines = msg.split('\n')
    #print lines
    post = []
    if wrap:
        for sub in lines:
            if sub == '':
                post.append('')
            elif sub == ' ':
                post.append(' ')
            else:
                # concatenate lines 
                post += textwrap.wrap(sub, LINE_WIDTH)
    else:
        post = lines
    #print post
    for i, l in enumerate(post):
        if l == '': # treat an empty line as a break
            l = '\n'
        # if first and there is more than one line
        elif i == 0 and len(post) > 1:
            # add a leading space
            l = '\n%s \n' % l # 
        # if only one line
        elif i == 0 and len(post) == 1:
            l = '\n%s ' % l # 
        elif i < len(post) - 1: # if not last
            l = '%s \n' % l 
        else: # if last, add trailing space, do not add trailing return
            l = '%s ' % l 
        sys.stdout.write(l)
        sys.stdout.flush()


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
    '''The user has provided incomplete input that cannot be understood. 
    '''
    def __init__(self, src=None):
        DialogError.__init__(self, src=src)

class NoInput(DialogError):
    '''The user has provided no input, and there is not a default.
    '''
    def __init__(self, src=None):
        DialogError.__init__(self, src=src)

class BadConditions(DialogError):
    '''The users system does support the action of the dialog: something is missing or otherwise prohibits operation. 
    '''
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

        # how many times to ask the user again and again for the same thing
        self._maxAttempts = 8


    def _writeToUser(self, msg):
        '''Write output to user. Call module-level function
        '''
        writeToUser(msg)

    def _readFromUser(self):
        '''Collect from user; return None if an empty response.
        '''
        try:
            post = raw_input()
            return post
        except KeyboardInterrupt:
            # store as own class so as a subclass of dialog error
            return KeyInterruptError()
        except:
            return DialogError()
        return NoInput()


    def prependPromptHeader(self, msg):
        '''
        >>> from music21 import *
        >>> d = configure.Dialog()
        >>> d.prependPromptHeader('test')
        >>> d._promptHeader
        'test'

        >>> d = configure.Dialog(promptHeader='this is it')
        >>> d.prependPromptHeader('test')
        >>> d._promptHeader
        'test this is it'
        '''
        msg = msg.strip()
        if self._promptHeader is not None:
            self._promptHeader = '%s %s' % (msg, self._promptHeader)
        else:
            self._promptHeader = msg

    def appendPromptHeader(self, msg):
        '''
        >>> from music21 import *
        >>> d = configure.Dialog()
        >>> d.appendPromptHeader('test')
        >>> d._promptHeader
        'test'

        >>> d = configure.Dialog(promptHeader='this is it')
        >>> d.appendPromptHeader('test')
        >>> d._promptHeader
        'this is it test'
        '''
        msg = msg.strip()
        if self._promptHeader is not None:
            self._promptHeader = '%s %s' % (self._promptHeader, msg)
        else:
            self._promptHeader = msg


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


    def _rawIntroduction(self):
        '''Return a multiline presentation of an introduction.
        '''
        return None

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

    def _preAskUser(self, force=None):
        '''Call this method immediately before calling askUser. Can be used for configuration getting additional information. 
        '''
        pass
        # define in subclass

    def askUser(self, force=None):
        '''Ask the user, display the querry. The force argument can be provided to test. Sets self._result; does not return a value.
        '''
        # if an introduction is defined, try to use it
        intro = self._rawIntroduction()
        if intro is not None:
            self._writeToUser(intro)

        # always call preAskUser: can customize in subclass. must return True
        # or False. if False, askUser cannot continue
        post = self._preAskUser(force=force)
        if post is False:
            self._result = BadConditions()
            return

        # ten attempts; not using a while so will ultimately break
        for i in range(self._maxAttempts):
            # in some cases, the query might not be able to be formed: 
            # for example, in selecting values from a list, and not having
            # any values. thus, query may be an error
            query = self._rawQuery()
            if isinstance(query, DialogError):
                # set result as error
                self._result = query
                break

            if force is None:
                self._writeToUser(query)
                rawInput = self._readFromUser()
            else:
                environLocal.printDebug(['writeToUser:', query])
                rawInput = force

            # rawInput here could be an error or a value
            #environLocal.printDebug(['received as rawInput', rawInput])
            # check for errors and handle
            if isinstance(rawInput, KeyInterruptError):
                # set as result KeyInterruptError
                self._result = rawInput
                break

            # need to not catch no NoInput nor IncompleteInput classes, as they 
            # will be handled in evaluation
            cookedInput = self._evaluateUserInput(rawInput)
            #environLocal.printDebug(['post _evaluateUserInput() cookedInput', cookedInput])

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

    def getResult(self, simulate=True):
        '''Return the result, or None if not set. This may also do a processing routine that is part of the desired result. 
        '''
        return self._result 

    def performAction(self, result=None):
        '''After getting a result, the query might require an action to be performed. If result is None, this will use whatever value is found in _result. 
        '''
        result = self.getResult()
        if isinstance(self._result, DialogError):
            #environLocal.printDebug('performAction() called, but result is an error: %s' % self._result)
            pass # nothing to do
        # perform action


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
class OpenInBrowser(YesOrNo):
    '''Ask the user if the want to open a URL in a browser.

    >>> from music21 import *
    >>> d = configure.OpenInBrowser('http://mit.edu/music21')
    '''
    def __init__(self, urlTarget, default=True, tryAgain=True,
        promptHeader=None):
        YesOrNo.__init__(self, default=default, tryAgain=tryAgain, promptHeader=promptHeader) 
    
        self._urlTarget = urlTarget
        # need to update prompt header
        msg = 'Open the following URL (%s) in a web browser?' % self._urlTarget
        self.appendPromptHeader(msg)

    def performAction(self, result=None):
        '''The action here is to open the stored URL in a browser, if the user agrees. 
        '''
        result = self.getResult()
        if isinstance(self._result, DialogError) or result is None:
            environLocal.printDebug('performAction() called, but result is an error: %s' % self._result)
            pass # nothing to do

        if result is True: # if True            
            import webbrowser
            webbrowser.open_new(self._urlTarget)
        # perform action




#-------------------------------------------------------------------------------
class SelectFromList(Dialog):
    '''General class to select values from a list.

    >>> from music21 import *
    >>> d = configure.SelectFromList() # empty selection list
    >>> d.askUser('no') # results in bad condition
    >>> d.getResult()
    <music21.configure.BadConditions: None>

    >>> d = configure.SelectFromList() # empty selection list
    >>> def validResults(force=None): return range(5)
    >>> d._getValidResults = validResults # provide alt function for testing
    >>> d.askUser(2) # results in bad condition
    >>> d.getResult()
    2
    '''
    def __init__(self, default=None, tryAgain=True, promptHeader=None):
        Dialog.__init__(self, default=default, tryAgain=tryAgain, promptHeader=promptHeader) 

    def _getValidResults(self, force=None):
        '''Return a list of valid results that are possible and should be displayed to the user. These will be processed by _formatResultForUser before usage.
        '''
        # this might need to be cached
        # customize in subclass
        if force is not None:
            return force
        else:
            return []

    def _formatResultForUser(self, result):
        '''Reduce each complete file path to stub, or otherwise compact display
        '''
        return result


    def _askFillEmptyList(self, default=None, force=None):
        '''What to do if the selection list is empty. Only return True or False: if we should continue or not.

        >>> from music21 import *
        >>> d = configure.SelectFromList(default=True)
        >>> d._askFillEmptyList(force='yes')
        True
        >>> d._askFillEmptyList(force='n')
        False
        >>> d._askFillEmptyList(force='') # no default, returns False
        False
        >>> d._askFillEmptyList(force='weree') # error gets false
        False
        '''
        # this does not do anything: customize in subclass
        d = YesOrNo(default=default, tryAgain=False, 
            promptHeader='The selection list is empty. Try Again?')
        d.askUser(force=force)
        post = d.getResult()
        # if any errors are found, return False
        if isinstance(post, DialogError):
            return False
        else: # must be True or False
            if post not in [True, False]:
                raise DialogError('_askFillEmptyList(): sub-command returned non True/False value')
            return post

    def _preAskUser(self, force=None):
        '''Before we ask user, we need to to run _askFillEmptyList list if the list is empty.

        >>> from music21 import *
        >>> d = configure.SelectFromList()
        >>> d._preAskUser('no') # force for testing
        False
        >>> d._preAskUser('yes') # force for testing
        True
        >>> d._preAskUser('') # no default, returns False
        False
        >>> d._preAskUser('x') # bad input returns false
        False
        '''
        options = self._getValidResults()
        if len(options) == 0:
            # must return True/False, 
            post = self._askFillEmptyList(force=force)
            return post 
        else: # if we have options, return True
            return True

    def _rawQuery(self, force=None):
        '''Return a multiline presentation of the question.

        >>> from music21 import *
        >>> d = configure.SelectFromList()
        >>> d._rawQuery(['a', 'b', 'c'])
        ['[1] a', '[2] b', '[3] c', ' ', 'Select a number from the preceding options: ']

        >>> d = configure.SelectFromList(default=1)
        >>> d._default
        1
        >>> d._rawQuery(['a', 'b', 'c'])
        ['[1] a', '[2] b', '[3] c', ' ', 'Select a number from the preceding options (default is 1): ']
        '''
        head = []
        i = 1
        options = self._getValidResults(force=force)
        # if no options, cannot form query: return bad conditions
        if len(options) == 0:
            return BadConditions('no options available')

        for entry in options:
            sub = self._formatResultForUser(entry)
            head.append('[%s] %s' % (i, sub))
            i += 1

        tail = 'Select a number from the preceding options: '
        tail = self._rawQueryPrepareHeader(tail)
        tail = self._rawQueryPrepareFooter(tail)
        return head + [' ', tail]

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




class SelectFilePath(SelectFromList):
    '''General class to select values from a list.

    >>> from music21 import *
    '''
    def __init__(self, default=None, tryAgain=True, promptHeader=None):
        SelectFromList.__init__(self, default=default, tryAgain=tryAgain, promptHeader=promptHeader) 

    def _getDarwinApp(self, comparisonFunction):
        '''Provide a comparison function that returns True or False based on the file name. This looks at everything in Applications, as well as every directory in Applications
        '''
        post = []
        path0 = '/Applications'
        for sub1 in os.listdir(path0):
            path1 = os.path.join(path0, sub1)
            if os.path.isdir(path1):
                # on macos, .apps are (always?) directories; thus, look
                # at these names directly
                if comparisonFunction(sub1):
                    post.append(path1)
                    continue
                #environLocal.printDebug(['_getDarwinApp: dir', path1])
                for sub2 in os.listdir(path1):
                    path2 = os.path.join(path1, sub2)
                    if comparisonFunction(sub2):
                        post.append(path2)
            else:        
                if comparisonFunction(sub1):
                    post.append(path1)
        return post


    def _getWinApp(self, comparisonFunction):
        '''Provide a comparison function that returns True or False based on the file name. 
        '''
        # provide a similar method to _getDarwinApp
        return []


    def _evaluateUserInput(self, raw):
        '''Evaluate the user's string entry after persing; do not return None: either return a valid response, default if available, IncompleteInput, NoInput objects. 
    
        Here, we convert the user-selected number into a file path
        >>> from music21 import *
        '''
        rawParsed = self._parseUserInput(raw)
        # of NoInput: and a default, return default
        if isinstance(rawParsed, NoInput): 
            if self._default is not None:
                # do not return the default, as this here is a number
                # and proper results are file paths. thus, set rawParsed
                # to default; will get converted later
                rawParsed = self._default

        # could be IncompleteInput, NoInput, or a proper, valid answer
        if isinstance(rawParsed, DialogError): # keep as is
            return rawParsed

        # else, translate a number into a file path; assume zero is 1
        options = self._getValidResults()
        if rawParsed >= 1 and rawParsed <= len(options):
            return options[rawParsed-1]
        else:
            return IncompleteInput(rawParsed)



class SelectMusicXMLReader(SelectFilePath):
    '''Select a MusicXML Reader by presenting a user a list of options. 

    >>> from music21 import *
    '''
    def __init__(self, default=None, tryAgain=True, promptHeader=None):
        SelectFilePath.__init__(self, default=default, tryAgain=tryAgain, promptHeader=promptHeader) 

    def _rawIntroduction(self):
        '''Return a multiline presentation of an introduction.
        '''
        return ['Defining an XML Reader permits automatically opening music21-generated MusicXML in an editor for display and manipulation when calling the show() method. Setting this option is highly recommended.', ' ']

    def _getMusicXMLReaderDarwin(self):
        '''Get all possible finale paths on Darwin
        '''
        # order here results in ranks
        def comparisonFinale(name):
            m = reFinaleApp.match(name)
            if m is not None: return True
            else: return False
        results = self._getDarwinApp(comparisonFinale)

        def comparisonMuseScore(name):
            m = reMuseScoreApp.match(name)
            if m is not None: return True
            else: return False
        results += self._getDarwinApp(comparisonMuseScore)

        def comparisonFinaleReader(name):
            m = reFinaleReaderApp.match(name)
            if m is not None: return True
            else: return False
        results += self._getDarwinApp(comparisonFinaleReader)

        return results
        
        # only go two levels deep in /Applications: all things there, 
        # and all things in directories stored there.


    def _getMusicXMLReaderWin(self):
        '''Get all possible finale paths on Darwin
        '''
        return []

    def _getMusicXMLReaderNix(self):
        '''Get all possible finale paths on Darwin
        '''
        return []

    def _getValidResults(self, force=None):
        '''Return a list of valid results that are possible and should be displayed to the user. These will be processed by _formatResultForUser before usage.
        '''
        # customize in subclass
        if force is not None:
            return force

        platform = common.getPlatform()
        if platform == 'win':
            post = self._getMusicXMLReaderWin()
        elif platform == 'darwin':
            post = self._getMusicXMLReaderDarwin()
        elif platform == 'nix':
            post = self._getMusicXMLReaderNix()
        return post


    def _askFillEmptyList(self, default=None, force=None):
        '''If we do not have an musicxml readers, ask user if they want to download. 

        >>> from music21 import *
        '''
        platform = common.getPlatform()
        if platform == 'win':
            urlTarget = urlFinaleReader
        elif platform == 'darwin':
            urlTarget = urlFinaleReader
        elif platform == 'nix':
            urlTarget = urlMuseScore
        
        # this does not do anything: customize in subclass
        d = OpenInBrowser(urlTarget=urlTarget, default=True, tryAgain=False, 
            promptHeader='No available MusicXML readers are found on your system. It is reccomended to download and install a reader.')
        d.askUser(force=force)
        post = d.getResult()
        # can call regardless of result; will only function if result is True
        d.performAction() 
        # if any errors are found, return False; this will end execution of 
        # askUser and return a BadConditions error
        if isinstance(post, DialogError):
            return False
        else: # must be True or False
            # if user selected to open webpage, give them time to download
            # and install; so ask if ready to continue
            if post is True: 
                for x in range(self._maxAttempts):
                    d = YesOrNo(default=True, tryAgain=False, 
                        promptHeader='Are you ready to continue?')
                    d.askUser(force=force)
                    post = d.getResult()
                    if post is True:
                        break
            return post



#-------------------------------------------------------------------------------
class ConfigurationAssistant(object):
    def __init__(self):
        
        self._dialogs = []

        d = SelectMusicXMLReader(default=1)
        self._dialogs.append(d)


        # note: this is the on-line URL: 
        # might be better to find local documentaiton
        d = OpenInBrowser(urlTarget=urlGettingStarted, promptHeader='Would you like to view the music21 Quick Start?')
        self._dialogs.append(d)


    def _introduction(self):
        msg = []
        msg.append('''Welcome the music21 Configuration Assistant. You will be guided through a number of questions to install and setup music21. Simply pressing return at a prompt will select a default, if available.''')
        msg.append('') # will cause a line break
        msg.append('''You may run this configuration again at a later time by running configure.py.''')
        msg.append(' ') # will cause a blank line

        writeToUser(msg)

    def _conclusion(self):
        msg = []
        msg.append('''This concludes the music21 Configuration Assistant.''')
        msg.append('')
        writeToUser(msg)


    def _hr(self):
        '''Draw a line
        '''
        msg = []
        msg.append('_' * LINE_WIDTH)
        msg.append(' ') # add a space
        writeToUser(msg)

    def run(self):
        self._hr()
        self._introduction()
        for d in self._dialogs:
            self._hr()
            d.askUser()
            post = d.getResult()
            # post may be an error; no problem calling perform action anyways
            d.performAction()

        self._hr()
        self._conclusion()







#-------------------------------------------------------------------------------
# for time-out gather of arguments: possibly look at:
# http://code.activestate.com/recipes/576780/
# http://www.garyrobinson.net/2009/10/non-blocking-raw_input-for-python.html

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


    def testSelectMusicXMLReader(self):

        print 
        environLocal.printDebug(['starting: SelectMusicXMLReader()'])
        d = SelectMusicXMLReader()
        d.askUser()
        environLocal.printDebug(['getResult():', d.getResult()])


        print 
        environLocal.printDebug(['starting: SelectMusicXMLReader(default=1)'])
        d = SelectMusicXMLReader(default=1)
        d.askUser()
        environLocal.printDebug(['getResult():', d.getResult()])



    def testOpenInBrowser(self):
        print 
        environLocal.printDebug(['starting: SelectMusicXMLReader()'])
        d = OpenInBrowser('http://mit.edu/music21')
        d.askUser()
        environLocal.printDebug(['getResult():', d.getResult()])
        d.performAction()


    def testSelectMusicXMLReader(self):
        print 
        environLocal.printDebug(['starting: SelectMusicXMLReader()'])
        d = SelectMusicXMLReader()
        d.askUser()
        environLocal.printDebug(['getResult():', d.getResult()])
        d.performAction()


        print 
        environLocal.printDebug(['starting: SelectMusicXMLReader()'])
        d = SelectMusicXMLReader()
        # force request to user by returning no valid results
        def getValidResults(force=None): return []
        d._getValidResults = getValidResults
        d.askUser()
        environLocal.printDebug(['getResult():', d.getResult()])
        d.performAction()



    def testConfigurationAssistant(self):

        ca = ConfigurationAssistant()
        ca.run()

        

class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testYesOrNo(self):
        from music21 import configure
        d = configure.YesOrNo(default=True, tryAgain=False, 
                        promptHeader='Are you ready to continue?')
        d.askUser('n')
        self.assertEqual(str(d.getResult()), 'False')
        d.askUser('y')
        self.assertEqual(str(d.getResult()), 'True')
        d.askUser('') # gets default
        self.assertEqual(str(d.getResult()), 'True')
        d.askUser('werwer') # gets default
        self.assertEqual(str(d.getResult()), '<music21.configure.IncompleteInput: werwer>')


        d = configure.YesOrNo(default=None, tryAgain=False, 
                        promptHeader='Are you ready to continue?')
        d.askUser('n')
        self.assertEqual(str(d.getResult()), 'False')
        d.askUser('y')
        self.assertEqual(str(d.getResult()), 'True')
        d.askUser('') # gets default
        self.assertEqual(str(d.getResult()), '<music21.configure.NoInput: None>')
        d.askUser('werwer') # gets default
        self.assertEqual(str(d.getResult()), '<music21.configure.IncompleteInput: werwer>')



    def testSelectFromList(self):
        from music21 import configure
        d = configure.SelectFromList(default=1)
        self.assertEqual(d._default, 1)


    def testSelectMusicXMLReaders(self):
        from music21 import configure
        d = configure.SelectMusicXMLReader()
        # force request to user by returning no valid results
        def getValidResults(force=None): return []
        d._getValidResults = getValidResults
        d.askUser('n') # reject option to open in a browser
        post = d.getResult()
        # returns a bad condition b/c there are no options and user entered 'n'
        self.assertEqual(isinstance(post, music21.configure.BadConditions), True)

    def testRe(self):
        
        g = reFinaleApp.match('Finale 2011.app')
        self.assertEqual(g.group(0), 'Finale 2011.app')

        self.assertEqual(reFinaleApp.match('final adsf 2011'), None)

        g = reFinaleApp.match('Finale 2009.app')
        self.assertEqual(g.group(0), 'Finale 2009.app')

        self.assertEqual(reFinaleApp.match('Finale 1992.app'), None)




if __name__ == "__main__":
    import sys


    # only if running tests
    if len(sys.argv) == 1: # normal conditions
        #music21.mainTest(Test)
        ca = ConfigurationAssistant()
        ca.run()

    elif len(sys.argv) > 1:
        t = Test()
        te = TestExternal()

        if sys.argv[1] in ['all', 'test']:
            import music21
            music21.mainTest(Test)
        
        # arg[1] is test to launch
        elif sys.argv[1] == 'te':
            # run test external
            getattr(te, sys.argv[2])()
        # just run named Test
        elif hasattr(t, sys.argv[1]): 
            getattr(t, sys.argv[1])()

#------------------------------------------------------------------------------
# eof

