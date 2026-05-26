# Releasing music21

These are the steps for making a new music21 release. 

## Setup

Run `uv sync`. This installs all the devtools the steps below need.

Install separately:

- `pandoc` — brew install pandoc
- `markdown` — `uv pip install markdown` (or `pip install markdown`).

## Steps

1. Update the `VERSION` in `music21/_version.py` and the single test case in
   `base.py`.

2. Run `corpus.corpora.CoreCorpus().cacheMetadata()`.
   For a major change that affects parsing, run
   `corpus.corpora.CoreCorpus().rebuildMetadataCache()` instead
   (~2 min on an M4). Either of these *may* change a lot of tests in `corpus`,
   `metadata`, etc., so do not skip the next step.

3. Run `uv run documentation/testDocumentation.py`, then fix errors.
   - You cannot check whether fixed tests work while it is still running.
   - This takes a while, runs single-core, and then almost always needs code
     patches, so allocate time (~2 min on an M4). Start working on the
     announcement while it runs.
   - You cannot run steps 2 and 3 in parallel, since metadata changes often
     cause documentation changes.

4. `uv run music21/test/warningMultiprocessTest.py` for the lowest and highest
   supported Python versions — fix all warnings.

5. Run `from music21.test import treeYield`, then:
   - `treeYield.find_all_non_hashable_m21objects()` and check that the returned
     set is empty. (It prints a bunch of module names, but only the final
     `set()` being empty matters.)
   - Then the same for `treeYield.find_all_non_default_instantiation_m21objects()`.
     If that one isn't empty it is not a bug, but it's nice to keep it so that
     `Music21Object`s don't need args.

6. Commit and wait for results on GitHub Actions.
   (Normally not necessary — it's slower and mostly duplicates
   `multiprocessTest` — but should be done before making a release.)

7. `uv run documentation/make.py clean` (skip on minor version changes).
   You may need to create a `documentation/build` directory first.

8. `uv run documentation/make.py linkcheck`.
   Some persistent errors that actually work are listed in `conf.py` under
   `linkcheck_ignore`.

9. `uv run documentation/make.py` -- build the documentation HTML files and supports.

10. `uv run documentation/upload.py` — zips `documentation/build/html` and
    uploads it to `music21.org/music21docs/`. Requires MSAC's private key.

11. Zip up `documentation/build/html` and get ready to upload/delete it (your
    desktop or wherever is fine). Rename to `music21-X.Y.Z-docs.zip`
    (skip for Alpha/Beta).

12. From the music21 main folder (not a subfolder) run `uv run hatch build`.
    This builds `dist/music21-X.Y.Z.tar.gz` and
    `dist/music21-X.Y.Z-py3-none-any.whl`.

13. Run `uv run scripts/buildNoCorpus.py`: it builds the no-corpus version of
    music21 (needs Python 3.12 or higher).
    **Do not run this on a PC**, or the Mac `.tar.gz` might end up with incorrect
    permissions. (TODO: To lift this restriction, rewrite removeCorpus() to run tar-to-tar with
    `tarfile`, copying each TarInfo so Unix modes survive)

14. PR and commit to GitHub at this point w/ a commit comment of the new
    version, then don't change anything until the next step is done. Merge to
    main/master. (`.gitignore` avoids uploading the large files created in `dist/`.)

15. Switch back to the master/main branch (or whatever main version you are
    releasing).

16. Tag the commit: `git tag -a vX.Y.Z -m "music21 vX.Y.Z"`.
    Don't forget the `v` in the release tag. Sanity-check that the correct commit
    was tagged: `git log`.

17. Push that tag: `git push origin vX.Y.Z`.

18. Create a new release on GitHub (using the tag just created) and upload the
    non-wheel files created here and the docs.
    Drag in this order: `.tar.gz` (wait to finish), `-docs.zip` (wait),
    `no-corpus.tar.gz`. Finish this before doing the next step, even though it
    looks like it could be done in parallel.

19. Upload the tar.gz file to PyPI: `uv run twine upload music21-X.Y.Z.tar.gz`.

20. Do the same for the `.whl` file (but not for the no-corpus file).

   - You will need a `~/.pypirc` file:

     ```ini
     [distutils]
     index-servers =
         pypi

     [pypi]
     username:__token__
     password:pypi-API_TOKEN
     ```

     The "password" is the API token you just created — if you lose this file you
     also lose the API token and have to create it again. This is all very poorly
     documented. It is not the "Unique identifier" you see in the "API Tokens"
     tab on the "Your Account" page — super confusing.

21. Delete the two `.tar.gz` files and the `.whl` file in `dist/` (and the docs).

22. For starting a new major release, create a GitHub branch to preserve the old
    one for patches, etc., especially during beta releases.

23. Immediately increment the number in `_version.py` and run tests on it to
    prepare for the next release.

24. Announce on the blog and to the list.

---

*History: these steps and `scripts/buildNoCorpus.py` were a single `dist/dist.py`
until May 2026, split out so they would stop living in the disposable `dist/`
directory.*
