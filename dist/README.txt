This directory holds throwaway build output (.tar.gz, .whl) and is in
.gitignore. It is safe to `trash dist` -- nothing here is source.

The old dist/dist.py was split and moved out so it would stop living in a
directory people routinely delete:

  - The release runbook (how to cut and upload a release) is now:
        RELEASING.md   (repository root)

  - The no-corpus distribution builder (removeCorpus) is now:
        scripts/buildNoCorpus.py
        run with:  uv run scripts/buildNoCorpus.py

Moved 2026-05-25.
