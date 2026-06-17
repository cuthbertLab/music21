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
from music21.common.misc import runningInJupyterOrColab, runningInMarimo
from music21.converter import museScore
from music21 import defaults
from music21 import environment
from music21 import stream

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
        return None

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
        return None

    fp = subConverter.write(
        obj,
        fmt,
        subformats=subformats,
        trimEdges=not multipageWidget,
        **keywords,
    )

    if subformats[0] != 'png':
        return None

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
        from ipywidgets import interact  # type: ignore  # pylint: disable=import-error

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
) -> t.Any:
    fp = subConverter.write(
        obj,
        fmt,
        subformats=subformats,
        addStartDelay=True,
        **keywords,
    )

    with open(fp, 'rb') as f:
        binaryMidiData: bytes = f.read()

    htmlOutput = htmlOutputForMidi(binaryMidiData)

    if runningInJupyterOrColab():
        displayMusic21jMIDIJupyter(htmlOutput)
    elif runningInMarimo():
        return displayMusic21jMIDIMarimo(htmlOutput)
    else:
        raise ValueError('Cannot run displayMusic21jMIDI if not running in a supported Notebook')

def displayMusic21jMIDIJupyter(htmlOutput: str) -> None:
    from IPython.display import display, HTML
    display(HTML(htmlOutput))

def displayMusic21jMIDIMarimo(htmlOutput: str) -> t.Any:
    # noinspection PyPackageRequirements
    from marimo import iframe  # type: ignore  # pylint: disable=import-error
    return iframe(htmlOutput, width='100%', height='80px')

def htmlOutputForMidi(binaryMidiData: bytes) -> str:
    binaryBase64 = base64.b64encode(binaryMidiData)
    s = common.SingletonCounter()
    outputId = 'midiPlayerDiv' + str(s())
    utf_binary: str = binaryBase64.decode('utf-8')
    # noinspection PyTypeChecker
    return '''
        <div id="''' + outputId + '''">
            <p class="m21-trust-warning">
                This MIDI player only runs in <em>trusted</em> notebooks.
                In JupyterLab: File &rarr; Trust Notebook, then re-run this cell.
            </p>
        </div>
        <script>
        (function() {
            const outputId = "''' + outputId + '''";
            const b64 = "''' + utf_binary + '''";
            const jsUrl = "https://cdn.jsdelivr.net/npm/music21j@0.23.1/releases/music21.debug.min.js";
            const cssUrl = "https://cdn.jsdelivr.net/npm/music21j@0.23.1/releases/music21j.min.css";

            const root = document.getElementById(outputId);
            const warning = root && root.querySelector(".m21-trust-warning");
            if (warning) warning.remove();

            function play(music21) {
                music21.common.urls.soundfontUrl = "https://cdn.jsdelivr.net/gh/cuthbertLab/midi-js-soundfonts@2026.05.15/FluidR3_GM/";
                music21.common.urls.midiPlayer = "https://cdn.jsdelivr.net/gh/cuthbertLab/music21j@v0.23.1/webResources/midiPlayer";
                const mp = new music21.miditools.MidiPlayer();
                mp.addPlayer("#" + outputId);
                mp.base64Load("data:audio/midi;base64," + b64);
            }

            window.m21conf = window.m21conf || { loadSoundfont: false };
            if (!document.querySelector("link[data-music21j]")) {
                const link = document.createElement("link");
                link.rel = "stylesheet";
                link.href = cssUrl;
                link.dataset.music21j = "1";
                document.head.appendChild(link);
            }

            // RequireJS / AMD route (Sphinx/nbsphinx HTML, classic Jupyter):
            // the music21j UMD bundle registers as an AMD module when define.amd
            // is present and never sets window.music21, so the script-tag/global
            // path below would fire play() with music21 undefined.
            if (typeof window.require === "function"
                    && typeof window.require.config === "function") {
                window.require.config({
                    paths: { music21: jsUrl.replace(/\\.js$/, "") }
                });
                window.require(["music21"], play);
                return;
            }

            if (window.music21) {
                play(window.music21);
                return;
            }
            let script = document.querySelector("script[data-music21j]");
            if (!script) {
                script = document.createElement("script");
                script.src = jsUrl;
                script.dataset.music21j = "1";
                document.head.appendChild(script);
            }
            script.addEventListener("load", function() { play(window.music21); });
        })();
        </script>'''
