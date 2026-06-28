#!/usr/bin/env python
'''
Git *clean* filter: strip rendered image outputs from a Jupyter notebook.

Reads a notebook on stdin and writes it back to stdout with every ``image/*``
output payload removed (text/stream outputs are preserved). This keeps the huge
base64 PNGs that ``.show()`` produces out of git history while iterating on the
in-progress documentation notebooks.

It is wired up as the ``stripnbimage`` clean filter for
``documentation/source/testsAndInProgress/*-noimage.ipynb`` via the
``.gitattributes`` in that directory. The filter command itself is *not* shared
through the repo (git never lets ``.gitattributes`` define commands, for
security), so each clone/worktree must register it once -- see ``CONTRIBUTING.md``
(humans) and ``AGENTS.md`` (agents):

    git config filter.stripnbimage.clean \
        "python documentation/scripts/stripNotebookImages.py"

The transform is idempotent, so running it on an already-stripped notebook is a
no-op (no spurious diffs).
'''
import sys
import nbformat


def stripImages(nb):
    for cell in nb.cells:
        if cell.get('cell_type') != 'code':
            continue
        newOutputs = []
        for out in cell.get('outputs', []):
            data = out.get('data') or {}
            meta = out.get('metadata') or {}
            hadImage = (any(k.startswith('image/') for k in data)
                        or any(k.startswith('image/') for k in meta))
            # A rendered .show() output is a whole display_data whose only payload is an
            # image (its text/plain fallback is a useless "<IPython...Image object>"
            # placeholder and its metadata holds pixel dimensions). Drop it entirely.
            if hadImage and out.get('output_type') == 'display_data':
                continue
            # Otherwise strip image payloads defensively but keep real text/stream output.
            for key in [k for k in data if k.startswith('image/')]:
                del data[key]
            for key in [k for k in meta if k.startswith('image/')]:
                del meta[key]
            if not data and out.get('output_type') in ('display_data', 'execute_result'):
                continue
            newOutputs.append(out)
        cell['outputs'] = newOutputs
    return nb


def main():
    nb = nbformat.read(sys.stdin, as_version=4)
    nbformat.write(stripImages(nb), sys.stdout)


if __name__ == '__main__':
    main()
