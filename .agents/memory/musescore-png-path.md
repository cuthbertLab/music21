---
name: musescore-png-path
description: MuseScore is needed even by Dorico/Sibelius users -- musescoreDirectPNGPath renders notation in notebooks and .png/.pdf; musicxmlPath stays the user's own app
metadata:
  type: project
---

Two separate settings:

- `musicxmlPath`: the app `.show()` opens outside a notebook. Docs encourage users to
  pick their regular notation program (Dorico, Sibelius, MuseScore, Finale).
- `musescoreDirectPNGPath`: the MuseScore program music21 runs in the background
  (`converter/museScore.py: runThroughMuseScore`) to turn MusicXML into images. Used by
  `.show()` in Jupyter (default format `ipython.musicxml.png`) and by
  `write('musicxml.png')` / `write('musicxml.pdf')`. A value starting with `/skip` turns
  rendering off (documentation tests show a 1-pixel image instead).

**Why MuseScore is special:** it is the only notation program music21 can run from the
command line to render images, so anyone who wants notation in a notebook needs it
installed, even if they never open it.

**How the path gets set (v11, #1980 and #2099; none of this is in 10.x):**

- `converter.museScore.findMuseScore()` finds MuseScore 3 or newer in the usual places:
  Applications on Mac, Program Files on Windows, the PATH on Linux.
- The Configuration Assistant sets `musescoreDirectPNGPath` to the chosen reader if it is
  MuseScore (the program inside a Mac `.app`), otherwise to any MuseScore it finds,
  unless the current setting already exists.
- When rendering, `getOrFindMuseScoreDirectPNGPath()` looks for MuseScore if the setting
  is missing or points nowhere, saves what it finds, or raises with the musescore.org link.
- Defaults in `environment.py`: MuseScore 4's install location on Mac and Windows;
  `/usr/bin/mscore3` on Linux, where MuseScore 4 has no standard location.

Myke renders with MuseScore 3 because it is much faster than 4 -- an advanced tip not
yet in the docs.

**How to apply:** install docs tell users to install MuseScore for notation in the
browser, then choose their favorite program in the assistant.
