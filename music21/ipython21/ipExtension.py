# -*- coding: utf-8 -*-
import music21.ipython21.objects

_DOC_IGNORE_MODULE_OR_PACKAGE = True

# See converter/subConverters/ConverterIPython for more info.

def load_ipython_extension(ip):
    pngFormatter = ip.display_formatter.formatters['image/png']
    pngFormatter.for_type(music21.ipython21.objects.IPythonPNGObject, music21.ipython21.objects.IPythonPNGObject.getData)  
#     from IPython.display import display, HTML # @UnresolvedImport
#     display(HTML('''
#      <script src='http://web.mit.edu/music21/music21j/ext/require/require.js'></script>
#      <script>
#     require.config(
#        { baseUrl: "http://web.mit.edu/music21/music21j/src/",
#          paths: {'music21': 'http://web.mit.edu/music21/music21j/src/music21',}
#         });
#     require(['music21'], function () {
#           var n = new music21.note.Note("D#4");
#           var s = new music21.stream.Stream();
#           s.append(n);
#           console.log('music21 loaded fine');
#     });
#     </script>
#     '''))
