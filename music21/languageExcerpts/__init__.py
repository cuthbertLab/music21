import sys

if sys.version > '3':
    from . import instrumentLookup
    from . import naturalLanguageObjects
else:
    import instrumentLookup # @Reimport
    import naturalLanguageObjects # @Reimport
