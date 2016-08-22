.. _advancedGraphing:



Advanced Graphing Topics
========================

The music21 tools for graphing and visualizing data are meant to be simple and intuitive to use. 
However, you may occasionally need some of the more advanced configuration topics described below.


Selecting the matplotlib Backend
------------------------------------------------

Most people will graph music21 data using matplotlib's default system for rendering and displaying
images (called the backend).  That default system is the TkAgg backend.  
But for embedding music21 in other graphical user interfaces you may want to choose another backend.
See the following discussion for more information.

  http://matplotlib.sourceforge.net/faq/installing_faq.html#what-is-a-backend
