`music21` welcomes contributions such as bug reports, new features, fixes, and
documentation improvements. The
[project repository](http://www.github.com/cuthbertLab/music21) is hosted at GitHub.


## Resources ##

[Module Documentation and User's Guide](https://web.mit.edu/music21/doc/index.html)

[Developer Reference](https://web.mit.edu/music21/doc/developerReference/index.html)

[Mailing List](https://groups.google.com/forum/#!forum/music21list)

[Code of Conduct](README.md)


## Issue Tickets ##

Please use the provided templates for bug reports or feature proposals. For issues
parsing file formats, (i.e. missing/buggy features not translated to or from that
format), please add to (or start) a general ticket for all support requests for that format.
(Some formats are no longer being actively maintained, such as MEI, LilyPond, and MuseData,
but well-tested patches can be merged.)

Good bug reports clearly state the unexpected behavior and include a short set of
commands to reproduce the issue. If your example requires loading a file, a two-measure
file is appropriate; a symphony movement is not--that's a support request. GitHub
is not a support channel.

Speaking of support, helpful people hang out on the
[mailing list](https://groups.google.com/forum/#!forum/music21list)
or Stack Overflow.


## Submitting Pull Requests ##

Open an issue to propose a feature or report a bug before raising a pull request.
You can include a diff or link to your own repo if you've already started some of the work.
(Changes where the motivation is self-evident, like handling exceptions or increasing
test coverage, don't need issue tickets.)

If your PR fixes an existing issue, please use a GitHub keyword ("Fixes #NNNN")
in the body of the PR so that the issue will be closed on merge.

You can run locally the same tests that GitHub Actions will run. Install `pylint`
and `flake8` and run them against the files you edited, and give the test suite a go,
also. (Quick start: run `python3 -m music21.test.multiprocessTest`.)
If you miss something and GitHub Actions pesters you with red "X"s, just
expand the details to get the line-by-line violations, and push another commit.

Speaking of commits, use incremental commits with descriptive messages rather
than force-pushing, which prevents the reviewer from assessing what changed
between reviews. (Squashing commits will be handled by the merger.)


## Style Guide ##

`music21` began in Perl. Now it interfaces with the TypeScript package `music21j`.
For these reasons, as well as for backward compatibility, we adhere to `camelCase`
naming--rather than PEP8 `snake_case` naming--for public APIs such as method names,
arguments, and the like.

That said, snake_case is acceptable (even encouraged!) in new contributions
for internal variables that are not exposed publicly. Screen readers can
pronounce these names better.

Conventions:

  - `'strings MUST be single-quoted, but "double quotes" are allowed internally'`
  - variable names:
    - need to be unambiguous
    - must begin with lowercase
    - snake_case is encouraged for private variables
  - line lengths are capped at 100, but if approaching this limit, look for ways to avoid one-lining
  - line continuation characters (`\`) are not allowed; use open parentheses
  - prefer f-strings to `%` or `.format()`
  - annotating types is encouraged: e.g. `self.counter: int = 0` or `def makeNoises() -> List['noise.Noise']:`
  - prefer enums to string configurations
  - methods:
    - no more than three positional arguments (in addition to `self`)
    - keyword arguments should be keyword-only by using `*`
      to consume any other positional arguments: `def makeNoise(self, volume, *, color=noise.Pink):`
    - avoid generic `**kwargs`; make keywords explicit
  - use [Sphinx formatting](https://web.mit.edu/music21/doc/developerReference/documenting.html#documenting-modules-and-classes)
      to link to classes and methods in docstrings
  - use descriptive pull request titles (rather than GitHub's default "Update pitch.py")


## Testing ##

We write doctests and unit tests, and we strive for the total
test coverage of the project to increase with every pull request. See the
[developer docs](https://web.mit.edu/music21/doc/developerReference/index.html)
to dig in to specific topics like adjusting doctests to prevent
actions we don't want executed when running the general test suite (such as opening
browser windows or playing music).

Pull requests that increase or improve coverage of existing features are very welcome.
Coverage reports can be found at [Coveralls](https://coveralls.io/github/cuthbertLab/music21).

For changes to file parsing, please test both import and export (when supported for
that format), and please increment the most minor version number in `music21.__version__`
so that cached files will be invalidated. Your tests can use `converter.parse(fp, forceSource=True)`
so that tests have a chance to fail locally, but in most cases we will ask you to 
remove this keyword when polishing the patch.


## Finally ##

If you're looking for ways to get started, browse the issues board, the Coveralls module
coverage, or the TODO stubs in an area of the code that interests you.
Thanks for your interest in contributing to music21. We look forward to seeing your work!
