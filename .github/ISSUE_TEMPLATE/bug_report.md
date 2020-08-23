---
name: Bug report
about: Report an issue with music21
title: ''
labels: ''
assignees: ''

---
<!-- Version of music21:  print(music21.__version__) -->
**music21 version**

`9.8.7`   <!-- replace with actual version -->


**Problem summary**
<!-- Briefly: what undesired thing happens when what action is taken? -->


**Steps to reproduce**

```
Paste minimal code example here. Most issues can be reproduced with just a few elements.
Attach external files only after attempting to reproduce using a simple stream.

myStream1 = converter.parse('tinynotation: 4/4 c4 e4 g2')
myStream2 = stream.Stream()
myStream2.insert(note.Rest(0.5))
```

**Expected vs. actual behavior**
<!-- Consider annotating the output produced by a function -->

**More information**
<!-- If relevant: OS, suggested fix, attempted workarounds -->

<!-- Note: only Mac and Windows are directly supported by music21 staff.  
     Bug reports that are specific to other OSes w/o a PR will be closed.
 -->
