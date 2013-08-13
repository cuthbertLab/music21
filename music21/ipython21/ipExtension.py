import music21.ipython21.objects
import os

_DOC_IGNORE_MODULE_OR_PACKAGE = True

def returnDataFromIPython21Object(obj):
    fp = obj.fp
    data = open(fp).read()
    os.remove(fp)
    return data

def load_ipython_extension(ip):
    pngFormatter = ip.display_formatter.formatters['image/png']
    pngFormatter.for_type(music21.ipython21.objects.IPythonPNGObject, returnDataFromIPython21Object)
