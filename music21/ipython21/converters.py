# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         ipython21/converters.py
# Purpose:      music21 Jupyter Notebook external converters
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2013-23 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module contains music21 Jupyter Notebook external converters, which
used to be in the main music21.converter.subConverters module.
'''
from __future__ import annotations
from collections.abc import Sequence
import base64
import pathlib
import typing as t

from music21 import common
from music21.converter import museScore
from music21 import defaults
from music21 import environment
from music21 import stream

# from music21.ipython21.ipExtension import needsToLoadRequireJS

if t.TYPE_CHECKING:
    from music21 import base
    from music21.converter.subConverters import SubConverter, ConverterMidi

environLocal = environment.Environment('ipython21.converters')


def showImageThroughMuseScore(
    obj: base.Music21Object,
    subConverter: SubConverter,
    fmt: str = 'musicxml',
    subformats: Sequence[str] = ('png',),
    *,
    multipageWidget: bool = False,
    **keywords,
):
    # noinspection PyPackageRequirements
    from IPython.display import Image, display, HTML  # type: ignore

    if str(environLocal['musescoreDirectPNGPath']).startswith('/skip'):
        # During documentation testing of the Notebooks, we don't generate
        # images since they take too long, so we just display the
        # smallest transparent pixel instead.

        # noinspection SpellCheckingInspection
        pngData64 = (b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA'
                     + b'6fptVAAAACklEQVQYV2P4DwABAQEAWk1v8QAAAABJRU5ErkJggg==')
        pngData = base64.b64decode(pngData64)
        # noinspection PyTypeChecker
        display(Image(data=pngData, retina=True))
        return

    # hack to make musescore excerpts -- fix with a converter class in MusicXML
    # or make a new keyword to ignoreTitles, etc.
    savedDefaultTitle = defaults.title
    savedDefaultAuthor = defaults.author
    defaults.title = ''
    defaults.author = ''

    if isinstance(obj, stream.Opus):
        for s in obj.scores:
            showImageThroughMuseScore(
                s,
                subConverter=subConverter,
                fmt=fmt,
                subformats=subformats,
                multipageWidget=multipageWidget,
                **keywords,
            )
        return

    fp = subConverter.write(
        obj,
        fmt,
        subformats=subformats,
        trimEdges=not multipageWidget,
        **keywords,
    )

    if subformats[0] != 'png':
        return

    last_png = museScore.findLastPNGPath(fp)
    last_number, num_digits = museScore.findPNGRange(fp, last_png)
    pages = {}
    stem = str(fp)[:str(fp).rfind('-')]
    for pg in range(1, last_number + 1):
        page_str = stem + '-' + str(pg).zfill(num_digits) + '.png'
        page_fp = pathlib.Path(page_str)
        pages[pg] = page_fp

    if last_number == 1:
        # one page PNG -- display normally.
        display(Image(data=fp.read_bytes(), retina=True))
    elif not multipageWidget:
        for pg in range(1, last_number + 1):
            if pages[pg].exists():
                display(Image(data=pages[pg].read_bytes(), retina=True))
                if pg < last_number:
                    display(HTML('<p style="padding-top: 20px">&nbsp;</p>'))
    else:
        # multi-page png -- use our widget.
        # noinspection PyPackageRequirements
        from ipywidgets import interact  # type: ignore

        @interact(page=(1, last_number))
        def page_display(page=1):
            inner_page_fp = pages[page]
            if inner_page_fp.exists():
                display(Image(data=inner_page_fp.read_bytes(), retina=True))
            else:
                print(f'No file for page {page}.')

        return page_display

    defaults.title = savedDefaultTitle
    defaults.author = savedDefaultAuthor
    return None

def displayMusic21jMIDI(
    obj: base.Music21Object,
    subConverter: ConverterMidi,
    fmt: str = 'midi',
    subformats: Sequence[str] = (),
    **keywords,
):
    # noinspection PyPackageRequirements
    from IPython.display import display, HTML  # type: ignore

    fp = subConverter.write(
        obj,
        fmt,
        subformats=subformats,
        addStartDelay=True,
    )

    with open(fp, 'rb') as f:
        binaryMidiData = f.read()

    binaryBase64 = base64.b64encode(binaryMidiData)
    s = common.SingletonCounter()
    outputId = 'midiPlayerDiv' + str(s())

    load_require_script = '''
        <script
        src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.6/require.min.js"
        ></script>
    '''

    utf_binary = binaryBase64.decode('utf-8')
    # noinspection PyTypeChecker
    display(HTML('''
        <div id="''' + outputId + '''"></div>
        <link rel="stylesheet" href="https://cuthbertLab.github.io/music21j/css/m21.css">
        ''' + load_require_script + '''
        <script>
        function ''' + outputId + '''_play() {
            const rq = require.config({
                paths: {
                    'music21': 'https://cuthbertLab.github.io/music21j/releases/music21.debug',
                }
            });
            rq(['music21'], function(music21) {
                mp = new music21.miditools.MidiPlayer();
                mp.addPlayer("#''' + outputId + '''");
                mp.base64Load("data:audio/midi;base64,''' + utf_binary + '''");
            });
        }
        if (typeof require === 'undefined') {
            setTimeout(''' + outputId + '''_play, 2000);
        } else {
            ''' + outputId + '''_play();
        }
        </script>'''))


    # def vfshow(self, s):
    #     '''
    #     pickle this object and send it to Vexflow
    #
    #     Alpha -- does not work too well.
    #     '''
    #     import random
    #     from music21.vexflow import toMusic21j
    #     from IPython.display import HTML
    #     vfp = toMusic21j.VexflowPickler()
    #     vfp.mode = 'jsonSplit'
    #     outputCode = vfp.fromObject(s)
    #     idName = 'canvasDiv' + str(random.randint(0, 10000))
    #     htmlBlock = '<div id="' + idName + '"><canvas/></div>'
    #     js = '''
    #     <script>
    #          data = ''' + outputCode + ''';
    #          var jpc = new music21.jsonPickle.Converter();
    #          var streamObj = jpc.run(data);
    #          streamObj.replaceCanvas("#''' + idName + '''");
    #     </script>
    #     '''
    #     return HTML(htmlBlock + js)
