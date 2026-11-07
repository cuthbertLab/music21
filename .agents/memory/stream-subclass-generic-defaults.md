---
name: stream-subclass-generic-defaults
description: How we want Stream subclasses to inherit the M21ObjType generic once Python typing allows default type params
metadata:
  type: project
---

`Stream` is generic in its element type (`Stream[M21ObjType: base.Music21Object]`),
but its subclasses currently swallow the type parameter. The deleted
`inherit-generics` branch sketched the target shape: make every subclass carry the
generic through —

- `Voice`, `Measure`, `Part`, `System`, `Score`, `Opus`, `SpannerStorage`,
  `VariantStorage` all become `Stream[M21ObjType]` instead of plain `Stream`, and
  the `M21ObjType` / `StreamType` TypeVars in `common/types.py` become
  `covariant=True`.

**The blocker (why it's deferred):** for this to be usable, the subclasses need a
*default* type argument — `Measure` should mean `Stream[Music21Object]` unless a
caller specializes it, not force every annotation to write `Measure[Note]`. Plain
generics give no way to default the parameter; that needs PEP 696 generic
defaults. The branch commit literally says "defer until default generic types are
allowed." This is the typing feature that lands natively in a future Python; it is
also available earlier via `typing_extensions.TypeVar(default=...)`.

**How to apply:** when default generic type parameters are usable in our supported
Python range, revive the `inherit-generics` shape (subclasses parameterized as
`Stream[M21ObjType]`, covariant TypeVars, per-subclass default of
`Music21Object`). Before then, investigate whether adding `typing_extensions` as a
dependency is worth it to get `TypeVar(default=...)` early — that would let us do
this without waiting for the Python floor to rise (and we must NOT raise the
`requires-python` floor to get it). Track alongside the other deferred typing
work.
