# -*- coding: utf-8 -*-
import music21.ipython21.objects

_DOC_IGNORE_MODULE_OR_PACKAGE = True

# See converter/subConverters/ConverterIPython for more info.

def load_ipython_extension(ip):
    '''
    Special method to automatically make PNG objects display inline.
    '''
    pngFormatter = ip.display_formatter.formatters['image/png']
    pngFormatter.for_type(music21.ipython21.objects.IPythonPNGObject, 
                          music21.ipython21.objects.IPythonPNGObject.getData)
    # also get matplotlib going inline for free...
    ip.run_line_magic('matplotlib', 'inline')


    