`Music21` welcomes contributions such as bug reports, new features, fixes, and
documentation improvements. The
[project repository](https://github.com/cuthbertLab/music21) is hosted at GitHub.

Information that was formerly here is now in 
[Developer Reference](https://www.music21.org/music21docs/developerReference/index.html)

Pull requests or issues created primarily with AI or in other ways not directly authored by the
contributor must be declared with (AI) or (AI Generated) in their issue/PR titles.
If not accepted, they will generally be closed without comment unless the contributor has
a demonstrated track record of being able to fix the code in question.  Reviewers that
do not disclose AI usage will be politely reminded the first time and may be blocked
for subsequent lack of disclosure. (New in 2025: this
is a pre-emptive time savings from experiences on other Open Source projects.)

In 2026 we welcome AI-Assisted contributions, but users must take responsibility for them and
they must match the code-style of the rest of the music21 project. "Slop that works somehow" will
not be accepted.

## Image-free documentation notebooks ##

In-progress documentation notebooks under `documentation/source/testsAndInProgress/`
whose names end in `-noimage.ipynb` (e.g. `findingParallels-noimage.ipynb`) keep their
rendered `.show()` image output **out of git** so pull-request diffs stay small while a
notebook is being iterated on. A git *clean* filter strips the base64 image payloads when
the file is staged; your local working copy keeps its images, and text outputs are
preserved in git.

Git does not (for security) let a repository ship the filter command itself, so each clone
must register it **once**:

```bash
git config filter.stripnbimage.clean \
  "python documentation/scripts/stripNotebookImages.py"
```

Use any Python that has `nbformat` installed — your music21 dev environment, or
`uv run python …` instead of `python …`. Without this step the `-noimage` notebooks are
simply committed unchanged (images and all), so please run it before contributing to them.

## Resources ##

[Module Documentation and User's Guide](https://www.music21.org/music21docs/)

[Mailing List](https://groups.google.com/forum/#!forum/music21list)

[Code of Conduct](README.md)
