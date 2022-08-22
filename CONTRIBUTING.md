`Music21` welcomes contributions such as bug reports, new features, fixes, and
documentation improvements. The
[project repository](http://www.github.com/cuthbertLab/music21) is hosted at GitHub.

In the first few years of `music21`, major new areas of investigation (medieval
rhythm encoding, contour analysis, etc.) were routinely added to the system. Now
features that are unlikely to be of general use are encouraged to live in their
own projects that import and extend `music21`.


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
You can include a diff or link to your own repo if you've 
already started some of the work.
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

`Music21` began in Perl. Now it interfaces with the TypeScript package `music21j`.
Both of those languages use `camelCase` extensively. For these reasons, 
as well as for backward compatibility, we adhere to `camelCase`
naming--rather than Python PEP8 `snake_case` naming--for public APIs such as method names,
arguments, and the like.

That said, snake_case is acceptable (even encouraged!) in new contributions
for internal variables that are not exposed publicly. Screen readers can
pronounce these names better and make them more accessible.  
However, all exposed methods and functions and their exposed arguments must
be in camelCase.

Conventions:

  - **strings MUST be 'single-quoted', but "double quotes" are allowed internally**
    - this rule applies to triple quotes and doc strings also, contrary to PEP 257.
    - when there is a hyphen or single quote in the string, double quotes should be used, 
      not escaping/backslashing.
    - For long streams of TinyNotation or Lilypond code, which both use single quotes to indicate octave,
       triple single quotes around the string are better than double quotes.  Internal whitespace
       rarely matters in those formats.
    - Documentation should follow quoting in American English grammar when not 
       discussing code.  So for instance, a quotation in documentation is in double quotes.
  - variable names:
    - need to be unambiguous, even if rather long.
    - must begin with lowercase
    - snake_case is allowed/encouraged for private variables
    - camelCase is required for public.
  - line lengths are capped at 100, but if approaching this limit, look for ways to avoid one-lining.
    - if it's easy to split your line into two which are both under 80 characters, do so.
  - line continuation characters (`\`) are not allowed; use open parentheses.
  - prefer f-strings to `.format()`.  The `%` interpolation is no longer allowed.
  - annotating types is required in new code, and encouraged to be added to older code.
    - e.g. `self.counter: int = 0` or `def makeNoises() -> t.List['noise.Noise']:`
    - The typing library should always be imported as `t`.
    - Until `music21` no longer supports Python 3.8, use `t.List[]` rather than `list[]`.
    - Until `music21` no longer supports Python 3.9, use `t.Optional[x]` rather than `x|None`.
  - prefer enums to string configurations
    - in music21.common.enums, there is a StrEnum class for nearly-backwards compatible
      replacement of a former string argument with an enum.
    - new Enums do not need to inherit from StrEnum or IntEnum.
    - Enum members should be in ALL_CAPS with underscores, unless there is a good reason (such
      as case differentiation) to use CamelCase.  I personally hate this convention--it looks
      like shouting--and will revisit it if `music21` is ever ported to a language where
      this is not the convention.  Do not leave out underscores in the member names; it makes
      it hard for people whose native language is not English to parse and impossible for
      screen readers.
  - methods:
    - no more than three positional arguments (in addition to `self`)
    - keyword arguments should be keyword-only by using `*`
      to consume any other positional arguments: `def makeNoise(self, volume, *, color=noise.PINK):`
    - avoid generic `**keywords`; make keywords explicit. 
      (This rule does not necessarily apply for subclass inheritance where you want to allow the superclass
      to add more features later.  But see the Liskov principle next.)
      See also https://github.com/cuthbertLab/music21/issues/1389
    - prefer methods that by default do not alter the object passed in and instead return a new one.
      It is permitted and encouraged to have an `inPlace: bool = False` argument that allows for
      manipulation of the original object.  When `inPlace` is True, nothing should be returned
      (not true for `music21j` since passing through objects is so expected in JavaScript thanks
      to JQuery and other libraries).
  - New classes should strongly endeavor to follow Liskov Substitution Principle.
    - Exceptions may be granted if the class structures follow names that are in common musical use
      but whose real world objects do not follow this principle.  For instance, a `Manx` is a subclass
      of `Cat` without `self.tail`.  Sometimes, however, rewriting the superclass might be possible
      (perhaps `self.tail: Optional[Tail]`).
    - `Music21` was originally designed without this principle in mind, so you will find
      parts of the system that do not follow LSP and for backwards compatibility never will.
      I (Myke) have personally apologized to Barbara Liskov for my past ignorance. 
  - use [Sphinx formatting](https://web.mit.edu/music21/doc/developerReference/documenting.html#documenting-modules-and-classes)
      to link to classes and methods in docstrings
  - use descriptive pull request titles (rather than GitHub's default "Update pitch.py")
    - do not have the PR title too long that it cannot be seen in one line.  Simplify and
      rewrite and go into more detail in the description.  I depend on skimming PR titles
      to prepare reports of changes.
    - don't turn a PR into a general discussion of something not included in the PR.
      Make an issue and link to the PR from there.
  - Write the word `music21` in lowercase in the middle of a sentence and as `Music21` at
    the beginning of a sentence.  Avoid beginning a sentence with a module name, but if
    it has to be done, write it in lowercase, obviously.  In contexts where possible,
    `music21` should be stylized in monospaced (with slab serifs, like old typewriters).

## Testing ##

We write doctests and unit tests, and we strive for the total
test coverage of the project to increase with every pull request. See the
[developer docs](https://web.mit.edu/music21/doc/developerReference/index.html)
to dig in to specific topics like adjusting doctests to prevent
actions we don't want executed when running the general test suite (such as opening
browser windows or playing music).

Pull requests that increase or improve coverage of existing features are very welcome.
Coverage reports can be found at [Coveralls](https://coveralls.io/github/cuthbertLab/music21).
Pull requests that lower overall coverage are likely to be rejected (exception: replace
30 covered lines with 5 covered lines that do the same job more efficiently, and you've
lowered the overall coverage, but that's okay).

For changes to file parsing, please test both import and export (when supported for
that format), and please increment the most minor version number in `music21.__version__`
so that cached files will be invalidated. Your tests can use `converter.parse(fp, forceSource=True)`
so that tests have a chance to fail locally, but in most cases we will ask you to 
remove this keyword when polishing the patch.


## Finally ##

If you're looking for ways to get started, browse the issues board, the Coveralls module
coverage, or the TODO stubs in an area of the code that interests you.
Thanks for your interest in contributing to `music21`. We look forward to seeing your work!
