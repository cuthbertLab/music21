# -----------------------------------------------------------------------------
# Name:         extensions.py
# Purpose:      Sphinx extension for hiding and showing lines in docs
#
# Authors:      Joséphine Wolf Oberholtzer
#
# Copyright:    Copyright © 2013-22 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
from __future__ import annotations

import enum
import importlib

from sphinx import addnodes
from sphinx.transforms.post_transforms import SphinxPostTransform

# loaded by source/conf.py

_DOC_IGNORE_MODULE_OR_PACKAGE = True


def fixLines(lines):
    newLines = []
    omitting = False
    for i, line in enumerate(lines):
        if ' #_DOCS_SHOW ' in line and omitting is not True:
            newLines.append(line.replace(' #_DOCS_SHOW ', ' '))
        elif '# _DOCS_SHOW' in line and omitting is not True:
            newLines.append(line.replace('# _DOCS_SHOW', ' '))
        elif '#_DOCS_HIDE' in line or '# _DOCS_HIDE' in line:
            continue
        elif 'OMIT_FROM_DOCS' in line:
            omitting = True
            continue
        elif 'RESUME_DOCS' in line:
            omitting = False
            continue
        elif '#_RAISES_ERROR' in line:
            newLines.append(line.replace(' #_RAISES_ERROR', ' '))
        elif omitting is True:
            continue
        else:
            newLines.append(line)
    lines[:] = newLines

def isEnumClass(what, obj) -> bool:
    '''
    True if autodoc is documenting an enum class:

    >>> from music21 import interval
    >>> isEnumClass('class', interval.Direction)
    True
    >>> isEnumClass('class', interval.Interval)
    False
    '''
    return what == 'class' and isinstance(obj, type) and issubclass(obj, enum.Enum)


def enumMemberLines(enumClass: type[enum.Enum]) -> list[str]:
    '''
    rst lines listing an enum's members and their values:

    >>> from music21 import interval
    >>> enumMemberLines(interval.Direction)
    ['', '.. rubric:: Members', '', '- ``DESCENDING`` = ``-1``',
     '- ``OBLIQUE`` = ``0``', '- ``ASCENDING`` = ``1``']
    '''
    return ['', '.. rubric:: Members', ''] + [
        f'- ``{member.name}`` = ``{member.value!r}``' for member in enumClass
    ]


def processDocstring(app, what, name, obj, options, lines):
    '''
    Process the ``lines`` of each docstring, in place.
    Enum classes also get a list of their members.
    '''
    #    print('WHAT ', what)
    #    print('NAME ', name)
    #    print('OBJ  ', obj)
    #    print('OPTS ', options)
    #    print('LINES', lines)
    fixLines(lines)
    if isEnumClass(what, obj):
        lines.extend(enumMemberLines(obj))


def processSignature(app, what, name, obj, options, signature, return_annotation):
    '''
    Show no signature for enum classes, rather than Python's `(*values)`.
    '''
    if isEnumClass(what, obj):
        return '', None
    return None


def processSource(app, name, lines):
    linesSep = lines[0].split('\n')
    fixLines(linesSep)
    lines[0] = '\n'.join(linesSep)


class LinkImportedNames(SphinxPostTransform):
    '''
    Point a bare name in a signature at the class the module imports under that name.
    In music21.scale, `Direction` is music21.scale.intervalNetwork.Direction, not
    music21.interval.Direction, which Sphinx alone cannot tell apart.

    AI-assisted (Claude).
    '''
    default_priority = 5  # before Sphinx resolves references at 10

    def run(self, **kwargs):
        pyObjects = self.env.get_domain('py').objects
        for node in self.document.findall(addnodes.pending_xref):
            target = node.get('reftarget', '')
            modName = node.get('py:module')
            if node.get('refdomain') != 'py' or not modName or '.' in target:
                continue
            try:
                obj = getattr(importlib.import_module(modName), target)
            except (ImportError, AttributeError):
                continue
            fullName = f'{getattr(obj, "__module__", "")}.{getattr(obj, "__qualname__", "")}'
            if fullName in pyObjects:
                node['reftarget'] = fullName


def setup(app):
    app.connect('autodoc-process-docstring', processDocstring)
    app.connect('autodoc-process-signature', processSignature)
    app.connect('source-read', processSource)
    app.add_post_transform(LinkImportedNames)
    extension_metadata = {'version': '1.0',
                          'parallel_read_safe': True,
                          'parallel_write_safe': True,
                          }
    return extension_metadata
