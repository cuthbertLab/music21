# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         configure.py
# Purpose:      Installation and Configuration Utilities
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2011-2019 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import os
import pathlib
import re
import time
import sys
import sysconfig
import textwrap
import unittest
import webbrowser

from importlib import reload

# assume that we will manually add this dir to sys.path top get access to
# all modules before installation
from music21 import common
from music21 import environment
from music21 import exceptions21

environLocal = environment.Environment('configure')

_DOC_IGNORE_MODULE_OR_PACKAGE = True
IGNORECASE = re.RegexFlag.IGNORECASE

# ------------------------------------------------------------------------------
# match finale name, which may be directory or something else
reFinaleApp = re.compile(r'Finale.*\.app', IGNORECASE)
reSibeliusApp = re.compile(r'Sibelius\.app', IGNORECASE)
reFinaleExe = re.compile(r'Finale.*\.exe', IGNORECASE)
reSibeliusExe = re.compile(r'Sibelius\.exe', IGNORECASE)
reFinaleReaderApp = re.compile(r'Finale Reader\.app', IGNORECASE)
reMuseScoreApp = re.compile(r'MuseScore.*\.app', IGNORECASE)
reMuseScoreExe = re.compile(r'Musescore.*\\bin\\MuseScore.*\.exe', IGNORECASE)

urlMusic21 = 'https://web.mit.edu/music21'
urlMuseScore = 'http://musescore.org'
urlGettingStarted = 'https://web.mit.edu/music21/doc/'
urlMusic21List = 'https://groups.google.com/g/music21list'

LINE_WIDTH = 78

# ------------------------------------------------------------------------------
# class Action(threading.Thread):
#     '''
#     A thread-based action for performing remote actions, like downloading
#     or opening in a webbrowser.
#     '''
#     def __init__ (self, prompt, timeOutTime):
#         super().__init__()
#         self.status = None
#
#     def run(self):
#         pass


# ------------------------------------------------------------------------------


def writeToUser(msg, wrapLines=True, linesPerPage=20):
    '''
    Display a message to the user, handling multiple lines as necessary and wrapping text
    '''
    # wrap everything to 60 lines
    if common.isListLike(msg):
        lines = msg
    else:
        # divide into lines if lines breaks are already in place
        lines = msg.split('\n')
    post = []
    if wrapLines:
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

    lineCount = 0
    for i, line in enumerate(post):
        if line == '':  # treat an empty line as a break
            line = '\n'
        # if first and there is more than one line
        elif i == 0 and len(post) > 1:
            # add a leading space
            line = f'\n{line} \n'
        # if only one line
        elif i == 0 and len(post) == 1:
            line = f'\n{line} '
        elif i < len(post) - 1:  # if not last
            line = f'{line} \n'
        else:  # if last, add trailing space, do not add trailing return
            line = f'{line} '
        if lineCount > 0 and lineCount % linesPerPage == 0:
            # ask user to continue
            d = AnyKey(promptHeader='Pausing for page.')
            d.askUser()
        sys.stdout.write(line)
        sys.stdout.flush()
        lineCount += 1


def getSitePackages():
    # Good enough for all but Red Hat (uses "platlib" but unsupported by us)
    return sysconfig.get_path('purelib')


def getUserData():
    '''
    Return a dictionary with user data
    '''
    post = {}
    try:
        import music21  # pylint: disable=redefined-outer-name
        post['music21.version'] = music21.VERSION_STR
    except ImportError:
        post['music21.version'] = 'None'

    if hasattr(os, 'uname'):
        uname = os.uname()
        post['os.uname'] = f'{uname[0]}, {uname[2]}, {uname[4]}'
    else:  # catch all
        post['os.uname'] = 'None'

    post['time.gmtime'] = time.strftime('%a, %d %b %Y %H:%M:%S', time.gmtime())
    post['time.timezone'] = time.timezone

    tzname = time.tzname
    if len(tzname) == 2 and tzname[1] not in [None, 'None', '']:
        post['time.tzname'] = tzname[1]
    else:
        post['time.tzname'] = tzname[0]
    return post


def _crawlPathUpward(start, target):
    '''
    Ascend up paths given a start; return when target file has been found.
    '''
    lastDir = start
    thisDir = lastDir
    match = None
    # first, ascend upward
    while True:
        environLocal.printDebug(f'at dir: {thisDir}')
        if match is not None:
            break
        for fn in sorted(os.listdir(thisDir)):
            if fn == target:
                match = os.path.join(thisDir, fn)
                break
        lastDir = thisDir
        thisDir, junk = os.path.split(thisDir)
        if thisDir == lastDir:  # at top level
            break
    return match



# ------------------------------------------------------------------------------
# error objects, not exceptions
class DialogError:
    '''
    DialogError is a normal object, not an Exception.
    '''
    def __init__(self, src=None):
        self.src = src

    def __repr__(self):
        return f'<music21.configure.{self.__class__.__name__}: {self.src}>'


class KeyInterruptError(DialogError):
    '''
    Subclass of DialogError that deals with Keyboard Interruptions.
    '''

    def __init__(self, src=None):
        super().__init__(src=src)


class IncompleteInput(DialogError):
    '''
    Subclass of DialogError that runs when the user has provided
    incomplete input that cannot be understood.
    '''

    def __init__(self, src=None):
        super().__init__(src=src)


class NoInput(DialogError):
    '''
    Subclass of DialogError for when the user has provided no input, and there is not a default.
    '''

    def __init__(self, src=None):
        super().__init__(src=src)


class BadConditions(DialogError):
    '''
    Subclass of DialogError for when the user's system does support the
    action of the dialog: something is missing or
    otherwise prohibits operation.
    '''

    def __init__(self, src=None):
        super().__init__(src=src)


# ------------------------------------------------------------------------------
class DialogException(exceptions21.Music21Exception, DialogError):
    pass

# ------------------------------------------------------------------------------


class Dialog:
    '''
    Model a dialog as a question and response. Have different subclasses for
    different types of questions. Store all in a Conversation, or multiple dialog passes.

    A `default`, if provided, is returned if the users provides no input and just enters return.

    The `tryAgain` option determines if, if a user provides incomplete or no response,
    and there is no default (for no response), whether the user is given another chance
    to provide valid input.

    The `promptHeader` is a string header that is placed in front of any common header
    for this dialog.
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
        # environLocal.printDebug(['Dialog: defaultCooked:', defaultCooked])

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

        # set platforms this dialog should run in
        self._platforms = ['win', 'darwin', 'nix']

    def _writeToUser(self, msg):
        '''
        Write output to user. Call module-level function
        '''
        writeToUser(msg)

    def _readFromUser(self):
        '''
        Collect from user; return None if an empty response.
        '''
        # noinspection PyBroadException
        try:
            post = input()
            return post
        except KeyboardInterrupt:
            # store as own class so as a subclass of dialog error
            return KeyInterruptError()
        except Exception:  # pylint: disable=broad-except
            return DialogError()

    def prependPromptHeader(self, msg):
        '''
        Add a message to the front of the stored prompt header.

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
            self._promptHeader = f'{msg} {self._promptHeader}'
        else:
            self._promptHeader = msg

    def appendPromptHeader(self, msg):
        '''

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
            self._promptHeader = f'{self._promptHeader} {msg}'
        else:
            self._promptHeader = msg

    def _askTryAgain(self, default=True, force=None):
        '''
        What to do if input is incomplete

        >>> prompt = configure.YesOrNo(default=True)
        >>> prompt._askTryAgain(force='yes')
        True
        >>> prompt._askTryAgain(force='n')
        False
        >>> prompt._askTryAgain(force='')  # gets default
        True
        >>> prompt._askTryAgain(force='blah')  # error gets False
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
        '''
        Prepare the header, given a string.

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
            if header.endswith('?') or header.endswith('.'):
                div = ''
            else:
                div = ':'

            if self._promptHeader.endswith('\n\n'):
                div += '\n\n'
            elif self._promptHeader.endswith('\n'):
                div += '\n'
            else:
                div += ' '
            msg = f'{header}{div}{msg}'
        return msg

    def _rawQueryPrepareFooter(self, msg=''):
        '''
        Prepare the end of the query message
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
            msg = f'{msg} (default is {default}){div} '
        return msg

    def _rawIntroduction(self):
        '''
        Return a multiline presentation of an introduction.
        '''
        return None

    def _rawQuery(self):
        '''
        Return a multiline presentation of the question.
        '''
        pass

    def _formatResultForUser(self, result):
        '''
        For various result options, we may need to at times convert the internal
        representation of the result into something else. For example, we might present
        the user with 'Yes' or 'No' but store the result as True or False.
        '''
        # override in subclass
        return result

    def _parseUserInput(self, raw):
        '''
        Translate string to desired output. Pass None through
        (as no input), convert '' to None, and pass all other
        outputs as IncompleteInput objects.
        '''
        return raw

    def _evaluateUserInput(self, raw):
        '''
        Evaluate the user's string entry after parsing; do not return None:
        either return a valid response, default if available, or IncompleteInput object.
        '''
        pass
        # define in subclass

    def _preAskUser(self, force=None):
        '''
        Call this method immediately before calling askUser.
        Can be used for configuration getting additional information.
        '''
        pass
        # define in subclass

    def askUser(self, force=None, *, skipIntro=False):
        '''
        Ask the user, display the query. The force argument can
        be provided to test. Sets self._result; does not return a value.
        '''
        # if an introduction is defined, try to use it
        intro = self._rawIntroduction()  # pylint: disable=assignment-from-none
        if intro is not None and not skipIntro:
            self._writeToUser(intro)

        # always call preAskUser: can customize in subclass. must return True
        # or False. if False, askUser cannot continue
        post = self._preAskUser(force=force)  # pylint: disable=assignment-from-no-return
        if post is False:
            self._result = BadConditions()
            return

        # ten attempts; not using a while so will ultimately break
        for i in range(self._maxAttempts):
            # in some cases, the query might not be able to be formed:
            # for example, in selecting values from a list, and not having
            # any values. thus, query may be an error
            query = self._rawQuery()  # pylint: disable=assignment-from-no-return
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
            # environLocal.printDebug(['received as rawInput', rawInput])
            # check for errors and handle
            if isinstance(rawInput, KeyInterruptError):
                # set as result KeyInterruptError
                self._result = rawInput
                break

            # need to not catch NoInput nor IncompleteInput classes, as they
            # will be handled in evaluation
            # pylint: disable=assignment-from-no-return
            cookedInput = self._evaluateUserInput(rawInput)
            # environLocal.printDebug(['post _evaluateUserInput() cookedInput', cookedInput])

            # if no default and no input, we get here (default supplied in
            # evaluate
            if isinstance(cookedInput, (NoInput, IncompleteInput)):
                # set result to these objects even if we try again
                self._result = cookedInput
                if self._tryAgain:
                    # only returns True or False
                    if self._askTryAgain():
                        pass
                    else:  # this will keep whatever the cooked was
                        break
                else:
                    break
            else:
                # should be in proper format after evaluation
                self._result = cookedInput
                break
        # self._result may still be None

    def getResult(self, simulate=True):
        '''
        Return the result, or None if not set. This may also do a
        processing routine that is part of the desired result.
        '''
        return self._result

    def _performAction(self, simulate=False):
        '''
        does nothing; redefine in subclass
        '''
        pass

    def performAction(self, simulate=False):
        '''
        After getting a result, the query might require an action
        to be performed. If result is None, this will use whatever
        value is found in _result.

        If simulate is True, no action will be taken.
        '''
        dummy = self.getResult()
        if isinstance(self._result, DialogError):
            environLocal.printDebug(
                f'performAction() called, but result is an error: {self._result}')
            self._writeToUser(['No action taken.', ' '])

        elif simulate:  # do not operate
            environLocal.printDebug(
                f'performAction() called, but in simulation mode: {self._result}')
        else:
            try:
                self._performAction(simulate=simulate)
            except DialogException:  # pylint: disable=catching-non-exception
                # in some cases, the action selected requires exciting the
                # configuration assistant
                # pylint: disable=raising-non-exception,raise-missing-from
                raise DialogException('perform action raised a dialog exception')


# ------------------------------------------------------------------------------
class AnyKey(Dialog):
    '''
    Press any key to continue
    '''

    def __init__(self, default=None, tryAgain=False, promptHeader=None):
        super().__init__(default=default, tryAgain=tryAgain, promptHeader=promptHeader)

    def _rawQuery(self):
        '''
        Return a multiline presentation of the question.
        '''
        msg = 'Press return to continue.'
        msg = self._rawQueryPrepareHeader(msg)
        # footer provides default; here, ignore
        # msg = self._rawQueryPrepareFooter(msg)
        return msg

    def _parseUserInput(self, raw):
        '''
        Always returns True
        '''
        return True


# ------------------------------------------------------------------------------
class YesOrNo(Dialog):
    '''
    Ask a yes or no question.

    >>> d = configure.YesOrNo(default=True)
    >>> d.askUser('yes')  # force arg for testing
    >>> d.getResult()
    True

    >>> d = configure.YesOrNo(tryAgain=False)
    >>> d.askUser('junk')  # force arg for testing
    >>> d.getResult()
     <music21.configure.IncompleteInput: junk>
    '''

    def __init__(self, default=None, tryAgain=True, promptHeader=None):
        super().__init__(default=default, tryAgain=tryAgain, promptHeader=promptHeader)

    def _formatResultForUser(self, result):
        '''
        For various result options, we may need to at times convert
        the internal representation of the result into something else.
        For example, we might present the user with 'Yes' or 'No' but
        store the result as True or False.
        '''
        if result is True:
            return 'Yes'
        elif result is False:
            return 'No'
        # while a result might be an error object, this method should probably
        # never be called with such objects.
        else:
            raise DialogException(f'attempting to format result for user: {result}')

    def _rawQuery(self):
        '''
        Return a multiline presentation of the question.

        >>> d = configure.YesOrNo(default=True)
        >>> d._rawQuery()
        'Enter Yes or No (default is Yes): '
        >>> d = configure.YesOrNo(default=False)
        >>> d._rawQuery()
        'Enter Yes or No (default is No): '

        >>> d = configure.YesOrNo(default=True, promptHeader='Would you like more time?')
        >>> d._rawQuery()
        'Would you like more time? Enter Yes or No (default is Yes): '
        '''
        msg = 'Enter Yes or No: '
        msg = self._rawQueryPrepareHeader(msg)
        msg = self._rawQueryPrepareFooter(msg)
        return msg

    def _parseUserInput(self, raw):
        '''
        Translate string to desired output. Pass None and '' (as no input), as
        NoInput objects, and pass all other outputs as IncompleteInput objects.

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
        if raw == '':
            return NoInput()

        if raw in ['yes', 'y', '1', 'true']:
            return True
        elif raw in ['no', 'n', '0', 'false']:
            return False
        # if no match, or an empty string
        return IncompleteInput(raw)

    def _evaluateUserInput(self, raw):
        '''
        Evaluate the user's string entry after parsing;
        do not return None: either return a valid response,
        default if available, IncompleteInput, NoInput objects.

        >>> d = configure.YesOrNo()
        >>> d._evaluateUserInput('y')
        True
        >>> d._evaluateUserInput('False')
        False
        >>> d._evaluateUserInput('')  # there is no default,
        <music21.configure.NoInput: None>
        >>> d._evaluateUserInput('wer')  # there is no default,
        <music21.configure.IncompleteInput: wer>

        >>> d = configure.YesOrNo('yes')
        >>> d._evaluateUserInput('')  # there is a default
        True
        >>> d._evaluateUserInput('wbf')  # there is a default
        <music21.configure.IncompleteInput: wbf>

        >>> d = configure.YesOrNo('n')
        >>> d._evaluateUserInput('')  # there is a default
        False
        >>> d._evaluateUserInput(None)  # None is processed as NoInput
        False
        >>> d._evaluateUserInput('blah')  # None is processed as NoInput
        <music21.configure.IncompleteInput: blah>
        '''
        rawParsed = self._parseUserInput(raw)
        # means no answer: return default
        if isinstance(rawParsed, NoInput):
            if self._default is not None:
                return self._default
        # could be IncompleteInput, NoInput, or a proper, valid answer
        return rawParsed


# ------------------------------------------------------------------------------
class AskOpenInBrowser(YesOrNo):
    '''
    Ask the user if the want to open a URL in a browser.


    >>> d = configure.AskOpenInBrowser('http://mit.edu/music21')
    '''

    def __init__(self, urlTarget, default=True, tryAgain=True,
                 promptHeader=None, prompt=None):
        super().__init__(default=default, tryAgain=tryAgain, promptHeader=promptHeader)

        self._urlTarget = urlTarget
        # try to directly set prompt header
        if prompt is not None:
            # override whatever is already in the prompt
            self._promptHeader = prompt
        else:  # else, append
            msg = f'Open the following URL ({self._urlTarget}) in a web browser?\n'
            self.appendPromptHeader(msg)

    def _performAction(self, simulate=False):
        '''
        The action here is to open the stored URL in a browser, if the user agrees.
        '''
        result = self.getResult()
        if result is True:
            webbrowser.open_new(self._urlTarget)
        elif result is False:
            pass
            # self._writeToUser(['No URL is opened.', ' '])

        # perform action


class AskSendInstallationReport(YesOrNo):
    '''
    Ask the user if they want to send a report
    regarding their system and usage.
    '''
    def __init__(self, default=True, tryAgain=True,
                 promptHeader=None, additionalEntries=None):
        super().__init__(default=default, tryAgain=tryAgain, promptHeader=promptHeader)

        if additionalEntries is None:
            additionalEntries = {}
        self._additionalEntries = additionalEntries

        msg = ('Would you like to send a pre-formatted email to music21 regarding your '
               'installation? Installation reports help us make music21 work better for you')
        self.appendPromptHeader(msg)

    def _getMailToStr(self):
        # noinspection PyListCreation
        body = []
        body.append('Please send the following email; your return email address '
                    'will never be used in any way.')
        body.append('')
        body.append('The following information on your installation '
                    'will be used only for research.')
        body.append('')

        userData = getUserData()
        # add any additional entries; this is used for adding the original egg info
        userData.update(self._additionalEntries)
        for key in sorted(userData):
            body.append(f'{key} // {userData[key]}')
        body.append('python version:')
        body.append(sys.version)

        body.append('')
        body.append('Below, please provide a few words about what sorts of tasks '
                    'or problems you plan to explore with music21. Any information on '
                    'your background is also appreciated (e.g., amateur musician, '
                    'computer programmer, professional music researcher). Thanks!')
        body.append('')

        platform = common.getPlatform()
        if platform == 'win':  # need to add proper return carriage for win
            body = '%0D%0A'.join(body)
        else:
            body = '\n'.join(body)

        msg = f'''mailto:music21stats@gmail.com?subject=music21 Installation Report&body={body}'''
        return msg  # pass this to webbrowser

    def _performAction(self, simulate=False):
        '''
        The action here is to open the stored URL in a browser, if the user agrees.
        '''
        result = self.getResult()
        if result is True:
            webbrowser.open(self._getMailToStr())


# ------------------------------------------------------------------------------
class SelectFromList(Dialog):
    '''
    General class to select values from a list.

    >>> d = configure.SelectFromList()  # empty selection list
    >>> d.askUser('no')  # results in bad condition
    >>> d.getResult()
    <music21.configure.BadConditions: None>

    >>> d = configure.SelectFromList()  # empty selection list
    >>> def validResults(force=None):
    ...     return range(5)
    >>> d._getValidResults = validResults  # provide alt function for testing
    >>> d.askUser(2)  # results in bad condition
    >>> d.getResult()
    2
    '''

    def __init__(self, default=None, tryAgain=True, promptHeader=None):
        super().__init__(default=default, tryAgain=tryAgain, promptHeader=promptHeader)

    def _getValidResults(self, force=None):
        '''
        Return a list of valid results that are possible and should be displayed to the user.
        '''
        # this might need to be cached
        # customize in subclass
        if force is not None:
            return force
        else:
            return []

    def _formatResultForUser(self, result):
        '''
        Reduce each complete file path to stub, or otherwise compact display
        '''
        return result

    def _askFillEmptyList(self, default=None, force=None):
        '''
        What to do if the selection list is empty. Only return True or False:
        if we should continue or not.

        >>> prompt = configure.SelectFromList(default=True)
        >>> prompt._askFillEmptyList(force='yes')
        True
        >>> prompt._askFillEmptyList(force='n')
        False
        >>> prompt._askFillEmptyList(force='')  # no default, returns False
        False
        >>> prompt._askFillEmptyList(force='blah')  # error gets false
        False
        '''
        # this does not do anything: customize in subclass
        d = YesOrNo(default=default,
                    tryAgain=False,
                    promptHeader='The selection list is empty. Try Again?')
        d.askUser(force=force)
        post = d.getResult()
        # if any errors are found, return False
        if isinstance(post, DialogError):
            return False
        else:  # must be True or False
            if post not in [True, False]:
                # this should never happen...
                raise DialogException(
                    '_askFillEmptyList(): sub-command returned non True/False value')
            return post

    def _preAskUser(self, force=None):
        '''
        Before we ask user, we need to run _askFillEmptyList list if the list is empty.

        >>> d = configure.SelectFromList()
        >>> d._preAskUser('no')  # force for testing
        False
        >>> d._preAskUser('yes')  # force for testing
        True
        >>> d._preAskUser('')  # no default, returns False
        False
        >>> d._preAskUser('x')  # bad input returns False
        False
        '''
        options = self._getValidResults()
        if not options:
            # must return True/False,
            post = self._askFillEmptyList(force=force)
            return post
        else:  # if we have options, return True
            return True

    def _rawQuery(self, force=None):
        '''
        Return a multiline presentation of the question.

        >>> d = configure.SelectFromList()
        >>> d._rawQuery(['a', 'b', 'c'])
        ['[1] a', '[2] b', '[3] c', ' ', 'Choose a number from the preceding options: ']

        >>> d = configure.SelectFromList(default=1)
        >>> d._default
        1
        >>> d._rawQuery(['a', 'b', 'c'])
        ['[1] a', '[2] b', '[3] c', ' ',
         'Choose a number from the preceding options (default is 1): ']
        '''
        head = []
        i = 1
        options = self._getValidResults(force=force)
        # if no options, cannot form query: return bad conditions
        if not options:
            return BadConditions('no options available')

        for entry in options:
            sub = self._formatResultForUser(entry)
            head.append(f'[{i}] {sub}')
            i += 1

        tail = 'Choose a number from the preceding options: '
        tail = self._rawQueryPrepareHeader(tail)
        tail = self._rawQueryPrepareFooter(tail)
        return head + [' ', tail]

    def _parseUserInput(self, raw):
        '''
        Convert all values to an integer, or return NoInput or IncompleteInput.
        Do not yet evaluate whether the number is valid in the context of the selection choices.

        >>> d = configure.SelectFromList()
        '''
        # environLocal.printDebug(['SelectFromList', '_parseUserInput', 'raw', raw])
        if raw is None:
            return NoInput()
        if raw == '':
            return NoInput()
        # accept yes as 1

        if raw in ['yes', 'y', '1', 'true']:
            post = 1
        else:  # try to convert string into a number
            try:
                post = int(raw)
            # catch all problems
            except (ValueError, TypeError, ZeroDivisionError):
                return IncompleteInput(raw)
        return post

    def _evaluateUserInput(self, raw):
        rawParsed = self._parseUserInput(raw)

        # means no answer: return default
        if isinstance(rawParsed, NoInput):
            if self._default is not None:
                return self._default

        # could be IncompleteInput, NoInput, or a proper, valid answer
        return rawParsed


class AskAutoDownload(SelectFromList):
    '''
    General class to select values from a list.
    '''

    def __init__(self, default=1, tryAgain=True, promptHeader=None):
        super().__init__(default=default, tryAgain=tryAgain, promptHeader=promptHeader)

    def _rawIntroduction(self):
        '''
        Return a multiline presentation of an introduction.
        '''
        return ['The BSD-licensed music21 software is distributed with a corpus of encoded '
                'compositions which are distributed with the permission of the encoders '
                '(and, where needed, the composers or arrangers) and where permitted under '
                'United States copyright law. Some encodings included in the corpus may not '
                'be used for commercial uses or have other restrictions: please see the '
                'licenses embedded in individual compositions or directories for more details.',
                ' ',
                'In addition to the corpus distributed with music21, other pieces are not '
                'included in this distribution, but are indexed as links to other web sites '
                'where they can be downloaded (the "virtual corpus"). If you would like, music21 '
                'can help your computer automatically resolve these links and bring them to your '
                'hard drive for analysis. '
                # 'See corpus/virtual.py for a list of sites that music21 '
                # 'might index.',
                ' ',
                'To the best of our knowledge, the music (if not the encodings) in the corpus are '
                'either out of copyright in the United States and/or are licensed for '
                'non-commercial use. These works, along with any works linked to in the virtual '
                'corpus, may or may not be free in your jurisdiction. If you believe this message '
                'to be in error regarding one or more works please contact '
                'Michael Cuthbert at cuthbert@mit.edu.',
                ' ',
                'Would you like to:'
                ]

    def _getValidResults(self, force=None):
        '''
        Just return number options
        '''
        if force is not None:
            return force
        else:
            return [
                'Acknowledge these terms and allow music21 to aid in finding pieces in the corpus',
                'Acknowledge these terms and block the virtual corpus',
                'Do not agree to these terms and will not use music21 (agreeing to the terms of '
                + 'the corpus is mandatory for using the system).'
            ]

    def _evaluateUserInput(self, raw):
        '''
        Evaluate the user's string entry after parsing; do not return None:
        either return a valid response, default if available, IncompleteInput, NoInput objects.
        '''
        rawParsed = self._parseUserInput(raw)
        # if NoInput: and a default, return default
        if isinstance(rawParsed, NoInput):
            if self._default is not None:
                # do not return the default, as this here is a number
                # and proper results are file paths. thus, set rawParsed
                # to default; will get converted later
                rawParsed = self._default

        # could be IncompleteInput, NoInput, or a proper, valid answer
        if isinstance(rawParsed, DialogError):  # keep as is
            return rawParsed

        if 1 <= rawParsed <= 3:
            return rawParsed
        else:
            return IncompleteInput(rawParsed)

    def _performAction(self, simulate=False):
        '''
        override base.
        '''
        result = self.getResult()
        if result in [1, 2, 3]:
            # noinspection PyTypeChecker
            reload(environment)
            # us = environment.UserSettings()
            if result == 1:
                # calling this function will check to see if a file is created
                environment.set('autoDownload', 'allow')
                # us['autoDownload'] = 'allow'  # automatically writes
            elif result == 2:
                # us['autoDownload'] = 'deny'  # automatically writes
                environment.set('autoDownload', 'deny')
            elif result == 3:
                raise DialogException('user selected an option that terminates configuration.')

        if result in [1, 2]:
            self._writeToUser([f"Auto Download set to: {environment.get('autoDownload')}", ' '])


class SelectFilePath(SelectFromList):
    '''
    General class to select values from a list.
    '''

    def __init__(self, default=None, tryAgain=True, promptHeader=None):
        super().__init__(default=default, tryAgain=tryAgain, promptHeader=promptHeader)

    def _getAppOSIndependent(self, comparisonFunction, path0: str, post: list[str],
                             *,
                             glob: str = '**/*'):
        '''
        Uses comparisonFunction to see if a file in path0 matches
        the RE embedded in comparisonFunction and if so manipulate the list
        in post

        comparisonFunction = function (lambda function on path returning True/False)
        path0 = os-specific string
        post = list of matching results to fill
        glob = string to glob for (default **/*, but **/*.exe on Windows and * on Mac).
        '''
        path0_as_path = pathlib.Path(path0)
        for path1 in path0_as_path.glob(glob):
            if comparisonFunction(str(path1)):
                post.append(str(path1))

    def _getDarwinApp(self, comparisonFunction) -> list[str]:
        '''
        Provide a comparison function that returns True or False based on the file name.
        This looks at everything in Applications, as well as every directory in Applications
        '''
        post: list[str] = []
        for path0 in ('/Applications', common.cleanpath('~/Applications', returnPathlib=False)):
            assert isinstance(path0, str)
            self._getAppOSIndependent(comparisonFunction, path0, post, glob='*')
        return post

    def _getWinApp(self, comparisonFunction) -> list[str]:
        '''
        Provide a comparison function that returns True or False based on the file name.
        '''
        # provide a similar method to _getDarwinApp
        post: list[str] = []
        environKeys = ('ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432')
        for possibleEnvironKey in environKeys:
            if possibleEnvironKey not in os.environ:
                continue  # Many do not define ProgramW6432
            environPath = os.environ[possibleEnvironKey]
            if environPath == '':
                continue
            self._getAppOSIndependent(comparisonFunction, environPath, post, glob='**/*.exe')

        return post

    def _evaluateUserInput(self, raw):
        '''
        Evaluate the user's string entry after parsing;
        do not return None: either return a valid response, default if available,
        IncompleteInput, NoInput objects.

        Here, we convert the user-selected number into a file path
        '''
        rawParsed = self._parseUserInput(raw)
        # if NoInput: and a default, return default
        if isinstance(rawParsed, NoInput):
            if self._default is not None:
                # do not return the default, as this here is a number
                # and proper results are file paths. thus, set rawParsed
                # to default; will get converted later
                rawParsed = self._default

        # could be IncompleteInput, NoInput, or a proper, valid answer
        if isinstance(rawParsed, DialogError):  # keep as is
            return rawParsed

        # else, translate a number into a file path; assume zero is 1
        options = self._getValidResults()
        if 1 <= rawParsed <= len(options):
            return options[rawParsed - 1]
        else:
            return IncompleteInput(rawParsed)


class SelectMusicXMLReader(SelectFilePath):
    '''
    Select a MusicXML Reader by presenting a user a list of options.
    '''

    def __init__(self, default=None, tryAgain=True, promptHeader=None):
        SelectFilePath.__init__(self,
                                default=default,
                                tryAgain=tryAgain,
                                promptHeader=promptHeader)

        # define platforms that this will run on
        self._platforms = ['darwin', 'win']

    def _rawIntroduction(self):
        '''
        Return a multiline presentation of an introduction.
        '''
        return [
            'Defining an XML Reader permits automatically opening '
            + 'music21-generated MusicXML in an editor for display and manipulation when calling '
            + 'the show() method. Setting this option is highly recommended. ',
            ' '
        ]

    def _getMusicXMLReaderDarwin(self):
        '''
        Get all possible MusicXML Reader paths on Darwin (i.e., macOS)
        '''
        def comparisonFinale(x):
            return reFinaleApp.search(x) is not None

        def comparisonMuseScore(x):
            return reMuseScoreApp.search(x) is not None

        def comparisonFinaleReader(x):
            return reFinaleReaderApp.search(x) is not None

        def comparisonSibelius(x):
            return reSibeliusApp.search(x) is not None

        # order here results in ranks
        results = self._getDarwinApp(comparisonMuseScore)
        results += self._getDarwinApp(comparisonFinale)
        results += self._getDarwinApp(comparisonFinaleReader)
        results += self._getDarwinApp(comparisonSibelius)

        # de-duplicate
        res = []
        for one_path in results:
            if one_path not in res:
                res.append(one_path)

        return res

    def _getMusicXMLReaderWin(self):
        '''
        Get all possible MusicXML Reader paths on Windows
        '''
        def comparisonFinale(x):
            return reFinaleExe.search(x) is not None

        def comparisonMuseScore(x):
            return reMuseScoreExe.search(x) is not None and 'crash-reporter' not in x

        def comparisonSibelius(x):
            return reSibeliusExe.search(x) is not None

        # order here results in ranks
        results = self._getWinApp(comparisonMuseScore)
        results += self._getWinApp(comparisonFinale)
        results += self._getWinApp(comparisonSibelius)

        # de-duplicate (Windows especially can put the same environment var twice)
        res = []
        for one_path in results:
            if one_path not in res:
                res.append(one_path)

        return res

    def _getMusicXMLReaderNix(self):
        '''
        Get all possible MusicXML Reader paths on Unix
        '''
        return []

    def _getValidResults(self, force=None):
        '''
        Return a list of valid results that are possible and
        should be displayed to the user.
        These will be processed by _formatResultForUser before usage.
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
        else:
            post = self._getMusicXMLReaderNix()
        return post

    def _askFillEmptyList(self, default=None, force=None):
        '''
        If we do not have any musicxml readers, ask user if they want to download.
        '''
        urlTarget = urlMuseScore

        # this does not do anything: customize in subclass
        d = AskOpenInBrowser(
            urlTarget=urlTarget,
            default=True,
            tryAgain=False,
            promptHeader='No available MusicXML readers are found on your system. '
            + 'We recommend downloading and installing a reader before continuing.\n\n')
        d.askUser(force=force)
        post = d.getResult()
        # can call regardless of result; will only function if result is True
        d.performAction()
        # if any errors are found, return False; this will end execution of
        # askUser and return a BadConditions error
        if isinstance(post, DialogError):
            return False
        else:  # must be True or False
            # if user selected to open web page, give them time to download
            # and install; so ask if ready to continue
            if post is True:
                for dummy in range(self._maxAttempts):
                    d = YesOrNo(default=True, tryAgain=False,
                                promptHeader='Are you ready to continue?')
                    d.askUser(force=force)
                    post = d.getResult()
                    if post is True:
                        break
                    elif isinstance(post, DialogError):
                        break

            return post

    def _performAction(self, simulate=False):
        '''
        The action here is to open the stored URL in a browser, if the user agrees.
        '''
        result = self.getResult()
        if result is not None and not isinstance(result, DialogError):
            # noinspection PyTypeChecker
            reload(environment)
            # us = environment.UserSettings()
            # us['musicxmlPath'] = result  # automatically writes
            environment.set('musicxmlPath', result)
            musicXmlNew = environment.get('musicxmlPath')
            self._writeToUser([f'MusicXML Reader set to: {musicXmlNew}', ' '])


# ------------------------------------------------------------------------------
class ConfigurationAssistant:
    '''
    Class for managing numerous configuration tasks.
    '''
    def __init__(self, simulate=False):
        self._simulate = simulate
        self._platform = common.getPlatform()

        # add dialogs to list
        self._dialogs = []
        self.getDialogs()

    def getDialogs(self):
        d = SelectMusicXMLReader(default=1)
        self._dialogs.append(d)

        d = AskAutoDownload(default=True)
        self._dialogs.append(d)

        d = AskSendInstallationReport(default=True)
        self._dialogs.append(d)

        d = AskOpenInBrowser(
            urlTarget=urlMusic21List,
            prompt='The music21 discussion group provides a forum for '
            + 'asking questions and getting help. Would you like to see the '
            + 'music21 discussion list or sign up for updates?')
        self._dialogs.append(d)

        # note: this is the on-line URL:
        # might be better to find local documentation
        d = AskOpenInBrowser(
            urlTarget=urlGettingStarted,
            prompt='Would you like to view the music21 documentation in a web browser?')
        self._dialogs.append(d)

        d = AnyKey(promptHeader='The music21 Configuration Assistant is complete.')
        self._dialogs.append(d)

    def _introduction(self):
        msg = []
        msg.append('Welcome to the music21 Configuration Assistant. You will be guided '
                   + 'through a number of questions to install and set up music21. '
                   + 'Simply pressing return at a prompt will select a default, if available.')
        msg.append('')  # will cause a line break
        msg.append('You may run this configuration again at a later time '
                   + 'by running music21/configure.py.')
        msg.append(' ')  # will cause a blank line

        writeToUser(msg)

    def _conclusion(self):
        pass

    def _hr(self):
        '''
        Draw a line
        '''
        msg = []
        msg.append('_' * LINE_WIDTH)
        msg.append(' ')  # add a space
        writeToUser(msg)

    def run(self, forceList=None):
        '''
        The forceList, if provided, is a list of string arguments
        passed in order to the included dialogs. Used for testing.
        '''
        if forceList is None:
            forceList = []
        self._hr()
        self._introduction()

        for i, d in enumerate(self._dialogs):
            # if this platform is not in those defined for the dialog, continue
            if self._platform not in d._platforms:
                continue

            self._hr()
            if len(forceList) > i:
                force = forceList[i]
            else:
                force = None

            d.askUser(force=force)
            unused_post = d.getResult()
            # post may be an error; no problem calling perform action in any case.
            try:
                d.performAction(simulate=self._simulate)
            except DialogException:
                # a user may have selected an option that requires breaking
                break

        # self._hr()
        self._conclusion()


# ------------------------------------------------------------------------------
# for time-out gather of arguments: possibly look at:
# https://code.activestate.com/recipes/576780/
# http://www.garyrobinson.net/2009/10/non-blocking-raw_input-for-python.html
# class Prompt(threading.Thread):
#     def __init__ (self, prompt, timeOutTime):
#         super().__init__()
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
#         self.printPrompt()  # print on first call
#         self.status = input()
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
#     # for host in range(60, 70):
#         if not current.isAlive() or current.status is not None:
#             break
#         if current.timeLeft <= 0:
#             break
#         time.sleep(updateInterval)
#         current.removeTime(updateInterval)
#
#         if intervalCount % reportInterval == reportInterval - 1:
#             sys.stdout.write('\n time out in %s seconds\n' % current.timeLeft)
#             current.printPrompt()
#
#         intervalCount += 1
#     # for o in objList:
#         # can have timeout argument, otherwise blocks
#         # o.join()  # wait until the thread terminates
#
#     post = current.status
#     # this thread will remain active until the user provides values
#
#     if post == None:
#         print('got no value')
#     else:
#         print('got: %s' % post)
# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER: list[type] = []


class TestUserInput(unittest.TestCase):  # pragma: no cover

    def testYesOrNo(self):
        print()
        print('starting: YesOrNo()')
        d = YesOrNo()
        d.askUser()
        print('getResult():', d.getResult())

        print()
        print('starting: YesOrNo(default=True)')
        d = YesOrNo(default=True)
        d.askUser()
        print('getResult():', d.getResult())

        print()
        print('starting: YesOrNo(default=False)')
        d = YesOrNo(default=False)
        d.askUser()
        print('getResult():', d.getResult())

    def testSelectMusicXMLReader(self):
        print()
        print('starting: SelectMusicXMLReader()')
        d = SelectMusicXMLReader()
        d.askUser()
        print('getResult():', d.getResult())

    def testSelectMusicXMLReaderDefault(self):
        print()
        print('starting: SelectMusicXMLReader(default=1)')
        d = SelectMusicXMLReader(default=1)
        d.askUser()
        print('getResult():', d.getResult())

    def testOpenInBrowser(self):
        print()
        d = AskOpenInBrowser('http://mit.edu/music21')
        d.askUser()
        print('getResult():', d.getResult())
        d.performAction()

    def testSelectMusicXMLReader2(self):
        print()
        print('starting: SelectMusicXMLReader()')
        d = SelectMusicXMLReader()
        d.askUser()
        print('getResult():', d.getResult())
        d.performAction()

        print()
        print('starting: SelectMusicXMLReader() w/o results')
        d = SelectMusicXMLReader()
        # force request to user by returning no valid results

        def getValidResults(force=None):
            return []

        d._getValidResults = getValidResults
        d.askUser()
        print('getResult():', d.getResult())
        d.performAction()

    def testConfigurationAssistant(self):
        print('Running ConfigurationAssistant all')
        configAsst = ConfigurationAssistant(simulate=True)
        configAsst.run()


class Test(unittest.TestCase):

    def testYesOrNo(self):
        from music21 import configure
        d = configure.YesOrNo(default=True, tryAgain=False,
                              promptHeader='Are you ready to continue?')
        d.askUser('n')
        self.assertEqual(str(d.getResult()), 'False')
        d.askUser('y')
        self.assertEqual(str(d.getResult()), 'True')
        d.askUser('')  # gets default
        self.assertEqual(str(d.getResult()), 'True')
        d.askUser('blah')  # gets default
        self.assertEqual(str(d.getResult()), '<music21.configure.IncompleteInput: blah>')

        d = configure.YesOrNo(default=None, tryAgain=False,
                              promptHeader='Are you ready to continue?')
        d.askUser('n')
        self.assertEqual(str(d.getResult()), 'False')
        d.askUser('y')
        self.assertEqual(str(d.getResult()), 'True')
        d.askUser('')  # gets default
        self.assertEqual(str(d.getResult()), '<music21.configure.NoInput: None>')
        d.askUser('blah')  # gets default
        self.assertEqual(str(d.getResult()), '<music21.configure.IncompleteInput: blah>')

    def testSelectFromList(self):
        from music21 import configure
        d = configure.SelectFromList(default=1)
        self.assertEqual(d._default, 1)

    def testSelectMusicXMLReaders(self):
        from music21 import configure
        d = configure.SelectMusicXMLReader()
        # force request to user by returning no valid results

        def getValidResults(force=None):
            return []

        d._getValidResults = getValidResults
        d.askUser(force='n', skipIntro=True)  # reject option to open in a browser
        post = d.getResult()
        # returns a bad condition b/c there are no options and user entered 'n'
        self.assertIsInstance(post, configure.BadConditions)

    def testRe(self):
        g = reFinaleApp.search('Finale 2011.app')
        self.assertEqual(g.group(0), 'Finale 2011.app')

        self.assertEqual(reFinaleApp.search('final blah 2011'), None)

        g = reFinaleApp.search('Finale.app')
        self.assertEqual(g.group(0), 'Finale.app')

        self.assertEqual(reFinaleApp.search('Final Cut 2017.app'), None)

    def testConfigurationAssistant(self):
        unused_ca = ConfigurationAssistant(simulate=True)

    def testGetUserData(self):
        unused_d = AskSendInstallationReport()
        # d.askUser()
        # d.getResult()
        # d.performAction()

    def testGetUserData2(self):
        unused_d = AskAutoDownload()
        # d.askUser()
        # d.getResult()
        # d.performAction()

    def testAnyKey(self):
        unused_d = AnyKey()
        # d.askUser()
        # d.getResult()
        # d.performAction()


def run():
    ca = ConfigurationAssistant()
    ca.run()


if __name__ == '__main__':
    if len(sys.argv) == 1:  # normal conditions
        # music21.mainTest(Test)
        run()

    else:
        # only if running tests
        testInstance = Test()
        te = TestUserInput()

        if len(sys.argv) < 2 or sys.argv[1] in ['all', 'test']:
            import music21
            music21.mainTest(Test)

        # arg[1] is the test to launch
        elif sys.argv[1] == 'te':
            # run test user input
            getattr(te, sys.argv[2])()
        # just run named Test
        elif hasattr(testInstance, sys.argv[1]):
            getattr(testInstance, sys.argv[1])()
