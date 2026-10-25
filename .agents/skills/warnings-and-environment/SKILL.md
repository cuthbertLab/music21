---
name: warnings-and-environment
description: >-
  How music21 tells users about problems: `warnings.warn` with a module Warning
  class, `environLocal.warn`, and `environLocal.printDebug`. Read before adding
  a warning or debug message, and before writing a test or doctest that
  triggers one — tests must never print warnings to the console.
---

# Warnings and the Environment

## Three channels

| Call | Goes to | Can a caller catch or silence it? |
|---|---|---|
| `warnings.warn(MusicXMLWarning('...'), stacklevel=2)` | Python's warnings system | Yes: filters, `catch_warnings`, `assertWarns` |
| `environLocal.warn('...')` | `sys.stderr.write`, every time | No (only by redirecting stderr) |
| `environLocal.printDebug('...')` | stderr, only when debug is on | Toggle with `music21/test/toggleDebug.py` |

`environLocal = environment.Environment('moduleName')` at the top of the module.

## Where things stand

Not unified. In 2026 the code has about 73 `environLocal.warn`, 41
`warnings.warn` (some with a module class, some bare), 800 `printDebug`, and no
`logging`. We are moving slowly toward Python's warnings and logging systems.
It is low priority: convert a call when you are already changing it, never as
a sweep.

For new code, prefer `warnings.warn` for anything a caller might reasonably want to catch,
silence, or test. By default Python shows each distinct message once per call
site, so a message that names the object (`f'{p.nameWithOctave} is ...'`) shows
for each different object. Use `environLocal.warn` only when the user must hear
it every time.

Never `print()`.

## Warning classes

A module with its own warnings defines one class subclassing `UserWarning`
(`MusicXMLWarning` in `musicxml/xmlObjects.py`, `TranslateWarning` in
`midi/translate.py`). Warnings are not exceptions, so they do not subclass
`Music21Exception`.

Set `stacklevel` so the reported line is in the caller's code, not ours: 2 from
the method the user called, more if the warning comes from a helper.

## Tests

In a unittest, catch it and check it:

```python
with self.assertWarnsRegex(MusicXMLWarning, 'C-1'):
    mxPitch = MEX.pitchToXml(pitch.Pitch('C', octave=-1))
```

## Doctests

doctest captures only stdout, so any warning goes straight to the console
of whoever runs the tests. Every doctest that triggers a warning must catch it.

When the warning is the point of the example, record it and show it.
`simplefilter('always')` keeps Python from swallowing a repeat of a warning an
earlier test already raised:

```
>>> import warnings
>>> with warnings.catch_warnings(record=True) as w:
...     warnings.simplefilter('always')  #_DOCS_HIDE
...     musicxml.m21ToXml.moveOctaveIntoMusicxmlRange(12, 'C12')
9
>>> w[0].message
MusicXMLWarning('C12 is out of MusicXML range; writing octave 9')
```

When it is incidental, hide the silencing from the docs (see `writing-docs` for
`#_DOCS_HIDE`/`#_DOCS_SHOW`):

```
>>> import warnings  #_DOCS_HIDE
>>> with warnings.catch_warnings():  #_DOCS_HIDE
...     warnings.simplefilter('ignore')  #_DOCS_HIDE
...     out = midi.translate.timeSignatureToMidiEvents(ts)  #_DOCS_HIDE
>>> #_DOCS_SHOW out = midi.translate.timeSignatureToMidiEvents(ts)
```

`catch_warnings` cannot stop `environLocal.warn`. If a doctest has to trigger
one, wrap it in `contextlib.redirect_stderr(io.StringIO())`.
