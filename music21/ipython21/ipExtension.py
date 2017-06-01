# -*- coding: utf-8 -*-
# import music21.ipython21.objects

_DOC_IGNORE_MODULE_OR_PACKAGE = True

# See converter/subConverters/ConverterIPython for more info.

def load_ipython_extension(ip):
    '''
    Special method to automatically make PNG objects display inline.

    MAY 2017: everything happens in converter.subConverters
    '''
#     pngFormatter = ip.display_formatter.formatters['image/png']
#     pngFormatter.for_type(music21.ipython21.objects.IPythonPNGObject,
#                           music21.ipython21.objects.IPythonPNGObject.getData)
    try:
        from matplotlib import pyplot as plt
        plt.ion()
        # get retina figures in matplotlib
        ip.run_line_magic('config', "InlineBackend.figure_format = 'retina'")
    except ImportError:
        pass

