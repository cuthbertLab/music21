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

**State as of 2026-10-22:** the Configuration Assistant sets `musescoreDirectPNGPath`
only when the user picks MuseScore as the MusicXML reader (new in v11, #1980; never in
10.x). Picking Dorico leaves the per-platform default in `environment.py`: MuseScore 4's
standard install location on Mac and Windows, but still `/usr/bin/mscore3` on Linux,
where MuseScore 4 has no standard location. Branch `musescore-png-detect` fixes this:
the assistant always sets the path when it finds MuseScore, and rendering looks for
MuseScore when the setting is missing. Update this note when it merges.

Myke renders with MuseScore 3 because it is much faster than 4 -- an advanced tip not
yet in the docs.

**How to apply:** install docs tell users to install MuseScore for notation in the
browser, then choose their favorite program in the assistant.
