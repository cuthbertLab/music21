#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common/formats.py
# Purpose:      Utilities for formats
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Utilities for working with file formats.

almost everything here is deprecated.
'''
__all__ = ['subConverterList', 'findSubConverterForFormat', 'findFormat',
           'findInputExtension', 'findFormatFile', 'findFormatExtFile',
           'findFormatExtURL',
           'VALID_SHOW_FORMATS', 'VALID_WRITE_FORMATS', 'VALID_AUTO_DOWNLOAD']

# used for checking preferences, and for setting environment variables
VALID_SHOW_FORMATS = ['musicxml', 'lilypond', 'text', 'textline', 'midi', 'png', 'pdf', 'svg', 'lily.pdf', 'lily.png', 'lily.svg', 'braille', 'vexflow', 'vexflow.html', 'vexflow.js', 'ipython', 'ipython.png', 'musicxml.png']
VALID_WRITE_FORMATS = ['musicxml', 'lilypond', 'text', 'textline', 'midi', 'png', 'pdf', 'svg', 'lily.pdf', 'lily.png', 'lily.svg', 'braille', 'vexflow', 'vexflow.html', 'vexflow.js', 'ipython', 'ipython.png', 'musicxml.png']
VALID_AUTO_DOWNLOAD = ['ask', 'deny', 'allow']

from music21.common.decorators import deprecated 

#-------------------------------------------------------------------------------
@deprecated('May 2015', '[soonest possible]', 'Moved to converter')
def subConverterList():
    '''
    returns a list of subconverter classes available to music21
    in converter/subConverters, including the stub SubConverter class
    
    DEPRECATED May 2015: moved to converter. #TODO: Remove
    '''
    from music21 import converter
    return converter.Converter().subconvertersList()

def findSubConverterForFormat(fmt):
    '''
    return a converter.subConverter.SubConverter subclass
    for a given format -- this is a music21 format name,
    not a file extension. Or returns None
    
    >>> common.findSubConverterForFormat('musicxml')
    <class 'music21.converter.subConverters.ConverterMusicXMLET'>
    
    >>> common.findSubConverterForFormat('text')
    <class 'music21.converter.subConverters.ConverterText'>

    Some subconverters have format aliases

    >>> common.findSubConverterForFormat('t')
    <class 'music21.converter.subConverters.ConverterText'>
    
    '''
    fmt = fmt.lower().strip()
    from music21 import converter
    scl = converter.Converter().subconvertersList()
    for sc in scl:
        formats = sc.registerFormats
        if fmt in formats:
            return sc


#@deprecated('May 2014', '[soonest possible]', 'Moved to converter')
def findFormat(fmt):
    '''
    Given a format defined either by a format name, abbreviation, or
    an extension, return the regularized format name as well as 
    the output exensions.
    
    DEPRECATED May 2014 -- moving to converter

    
    All but the first element of the tuple are deprecated for use, since
    the extension can vary by subconverter (e.g., lily.png)

    Note that .mxl and .mx are only considered MusicXML input formats.

    >>> common.findFormat('mx')
    ('musicxml', '.xml')
    >>> common.findFormat('.mxl')
    ('musicxml', '.xml')
    >>> common.findFormat('musicxml')
    ('musicxml', '.xml')
    >>> common.findFormat('lily')
    ('lilypond', '.ly')
    >>> common.findFormat('lily.png')
    ('lilypond', '.ly')
    >>> common.findFormat('humdrum')
    ('humdrum', '.krn')
    >>> common.findFormat('txt')
    ('text', '.txt')
    >>> common.findFormat('textline')
    ('textline', '.txt')
    >>> common.findFormat('midi')
    ('midi', '.mid')
    >>> common.findFormat('abc')
    ('abc', '.abc')
    >>> common.findFormat('scl')
    ('scala', '.scl')
    >>> common.findFormat('braille')
    ('braille', '.txt')
    >>> common.findFormat('vexflow')
    ('vexflow', '.html')
    >>> common.findFormat('capx')
    ('capella', '.capx')

    >>> common.findFormat('mx')
    ('musicxml', '.xml')

    
    #>>> common.findFormat('png')
    #('musicxml.png', '.png')
    
    #>>> common.findFormat('ipython')
    #('ipython', '.png')
    #     >>> common.findFormat('ipython.png')
    #     ('ipython', '.png')
    #     >>> common.findFormat('musicxml.png')
    #     ('musicxml.png', '.png')


    Works the same whether you have a leading dot or not:


    >>> common.findFormat('md')
    ('musedata', '.md')
    >>> common.findFormat('.md')
    ('musedata', '.md')


    If you give something we can't deal with, returns a Tuple of None, None:

    >>> common.findFormat('wpd')
    (None, None)

    '''
    from music21 import converter
    c = converter.Converter()
    fileformat = c.regularizeFormat(fmt)
    if fileformat is None:
        return (None, None)
    scf = c.getSubConverterFormats()
    sc = scf[fileformat]

        
    if sc.registerOutputExtensions:
        firstOutput = '.' + sc.registerOutputExtensions[0]
    elif sc.registerInputExtensions:
        firstOutput = '.' + sc.registerInputExtensions[0]
    else:
        firstOutput = None
            
    return fileformat, firstOutput
    
#     for key in sorted(list(fileExtensions)):
#         if fmt.startswith('.'):
#             fmt = fmt[1:] # strip .
#         if fmt == key or fmt in fileExtensions[key]['input']:
#             # add leading dot to extension on output
#             return key, '.' + fileExtensions[key]['output']
#     return None, None # if no match found

#@deprecated('May 2014', '[soonest possible]', 'Moved to converter')

def findInputExtension(fmt):
    '''
    Will be fully deprecated when there's an exact equivalent in converter...
    
    
    Given an input format or music21 format, find and return all possible 
    input extensions.

    >>> a = common.findInputExtension('musicxml')
    >>> a
    ('.xml', '.mxl', '.mx', '.musicxml')
    >>> a = common.findInputExtension('humdrum')
    >>> a
    ('.krn',)
    >>> common.findInputExtension('musedata')
    ('.md', '.musedata', '.zip')
    
    mx is not a music21 format but it is a file format
    
    >>> common.findInputExtension('mx')
    ('.xml', '.mxl', '.mx', '.musicxml')
    
    Leading dots don't matter...
    
    >>> common.findInputExtension('.mx')
    ('.xml', '.mxl', '.mx', '.musicxml')


    blah is neither
    
    >>> common.findInputExtension('blah') is None
    True
    '''
    from music21 import converter
    fmt = fmt.lower().strip()    
    if fmt.startswith('.'):
        fmt = fmt[1:] # strip .

    sc = findSubConverterForFormat(fmt)
    if sc is None:
        # file extension
        post = []
        for sc in converter.Converter().subconvertersList():
            if fmt not in sc.registerInputExtensions:
                continue
            for ext in sc.registerInputExtensions:
                if not ext.startswith('.'):
                    ext = '.' + ext
                post.append(ext)
            if post:
                return tuple(post)
        return None
    else:
        # music21 format
        post = []
        for ext in sc.registerInputExtensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            post.append(ext)
        return tuple(post)

#@deprecated('May 2014', '[soonest possible]', 'Moved to converter')
def findFormatFile(fp):
    '''
    Given a file path (relative or absolute) return the format
    
    DEPRECATED May 2014 -- moving to converter


    >>> common.findFormatFile('test.xml')
    'musicxml'
    >>> common.findFormatFile('long/file/path/test-2009.03.02.xml')
    'musicxml'
    >>> common.findFormatFile('long/file/path.intermediate.png/test-2009.03.xml')
    'musicxml'

    On a windows networked filesystem
    >>> common.findFormatFile('\\\\long\\file\\path\\test.krn')
    'humdrum'
    '''
    fmt, unused_ext = findFormat(fp.split('.')[-1])
    return fmt # may be None if no match

#@deprecated('May 2014', '[soonest possible]', 'Moved to converter')
def findFormatExtFile(fp):
    '''Given a file path (relative or absolute) find format and extension used (not the output extension)

    DEPRECATED May 2014 -- moving to converter

    >>> common.findFormatExtFile('test.mx')
    ('musicxml', '.mx')
    >>> common.findFormatExtFile('long/file/path/test-2009.03.02.xml')
    ('musicxml', '.xml')
    >>> common.findFormatExtFile('long/file/path.intermediate.png/test-2009.03.xml')
    ('musicxml', '.xml')

    >>> common.findFormatExtFile('test')
    (None, None)

    Windows drive
    >>> common.findFormatExtFile('d:/long/file/path/test.xml')
    ('musicxml', '.xml')

    On a windows networked filesystem
    >>> common.findFormatExtFile('\\\\long\\file\\path\\test.krn')
    ('humdrum', '.krn')
    '''
    fileFormat, unused_extOut = findFormat(fp.split('.')[-1])
    if fileFormat == None:
        return None, None
    else:
        return fileFormat, '.'+fp.split('.')[-1] # may be None if no match

#@deprecated('May 2014', '[soonest possible]', 'Moved to converter')
def findFormatExtURL(url):
    '''Given a URL, attempt to find the extension. This may scrub arguments in a URL, or simply look at the last characters.

    DEPRECATED May 2014 -- moving to converter


    >>> urlA = 'http://somesite.com/?l=cc/schubert/piano/d0576&file=d0576-06.krn&f=xml'
    >>> urlB = 'http://somesite.com/cgi-bin/ksdata?l=cc/schubert/piano/d0576&file=d0576-06.krn&f=kern'
    >>> urlC = 'http://somesite.com/cgi-bin/ksdata?l=cc/bach/cello&file=bwv1007-01.krn&f=xml'
    >>> urlF = 'http://junk'

    >>> common.findFormatExtURL(urlA)
    ('musicxml', '.xml')
    >>> common.findFormatExtURL(urlB)
    ('humdrum', '.krn')
    >>> common.findFormatExtURL(urlC)
    ('musicxml', '.xml')
    >>> common.findFormatExtURL(urlF)
    (None, None)
    '''
    from music21 import converter
    ext = None
    # first, look for cgi arguments
    if '=xml' in url:
        ext = '.xml'
    elif '=kern' in url:
        ext = '.krn'
    # specific tag used on musedata.org
    elif 'format=stage2' in url or 'format=stage1' in url:
        ext = '.md'
    else: # check for file that ends in all known input extensions
        for sc in converter.Converter().subconvertersList():
            inputTypes = sc.registerInputExtensions            
            for extSample in inputTypes:
                if url.endswith('.' + extSample):
                    ext = '.' + extSample
                    break
    # presently, not keeping the extension returned from this function
    # reason: mxl is converted to xml; need to handle mxl files first
    if ext != None:
        fileFormat, unused_junk = findFormat(ext)
        return fileFormat, ext
    else:
        return None, None
    

if __name__ == "__main__":
    import music21
    music21.mainTest()

#------------------------------------------------------------------------------
# eof

