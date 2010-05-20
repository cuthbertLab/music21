.. _faq:

Frequently Asked Questions
==========================

General
-----------

How do I ask a question so that it becomes frequently asked?

    Don't you hate FAQs that are not based on anything anyone's ever asked?  To ask, post to http://groups.google.com/group/music21list.  But first read what we've already come up with below.


What is the native music21 data format?

    Quick answer: there is none.

    Longer answer: music21 is a toolkit for the manipulation and analysis of data that you already have or are generating on the fly. As such, its strength is its (and python's) ability to work with many common formats and easy extensibility to work with many more. You will find that for the most part you will not need to preserve your music21 data in an interchangeable format. And the number of things you can do with music21 makes it impossible for us to create formats for every possible use. We work with music21 all the time for our work and have never needed one.
    
    But if you must store your music21 data somehow, here are some suggestions:
    
    * For data that can quickly and exactly be recreated, use the script that generates as your data storage.  Then just rerun the script to get your data back.

    * For storing music notation, musicXML output will work well for many purposes. If you just want to store an audio file or graphic of your output, MIDI or Lilypond->PNG could work.

    * For data that cannot easily be recreated (because it's computationally expensive to create, or relies on user input, or is stochastically generated), Python's pickle or cPickle packages will allow you to store your data on disk.  These files cannot necessarily be read in by a later version of music21 (This is the reverse of the problem Finale has, where you can only read older versions of files), so it should not be used for long term storage and sharing.

    * For data that cannot easily be recreated but needs long-term storage and sharing, try saving the relevant parts of the data in an XML, json, or even CSV(!) format. See plistlib http://docs.python.org/dev/library/plistlib.html or http://code.activestate.com/recipes/440595. You cannot store every element of python's object structure, but you should easily be able to store the parts that are difficult to recreate.

    * If you're programming data structures too complex to be encapsulated in one of the solutions above, you should have enough experience to create a data storage format of your own. Please consider contributing your solution to improve the package.

Can I synthesize new sounds with music21?

    Yes, and no.  Music21 is primarily built for manipulating symbolic 
    musical data not sound waves.  There are lots of great programs for
    doing that.  But the symbolic data, however, be used as data within 
    a large variety of synthesis packages. So you could create new
    music21 objects that control the synthesis package of your choosing.    

I'll bite the bullet, but how do I install music21?

    Please see the complete install instructions: :ref:`install`.



3rd-Party Utilities
--------------------

What is MusicXML?
    MusicXML is a file format for exchanging musical scores among different 
    programs, such as, oh...music21 and Finale (or music21 and Sibelius).  
    It was created and owned by Recordare (Michael Good, CEO). More 
    information about the project can be found at:

    * http://www.recordare.com/

And this Humdrum about which you speak?
    It's another framework for studying music as symbolic data using 
    simple text files and UNIX scripting tools.  We're big fans of Humdrum 
    here at music21, but we thought that it was time to take a 
    different approach. 

    Information on Humdrum can be found here at the following links:

    * http://music-cog.ohio-state.edu/Humdrum
    * http://kern.humdrum.net

What's Lilypond?
    It's an open-source package for displaying music, sort of like 
    Finale and Sibelius, but with different goals and a different 
    approach (and it's free!).  If you have Lilypond installed, 
    music21 can output to lilypond by using "show('lily')" 
     
    More information on the Lilypond can be found here at the following links:

    * http://lilypond.org/web
    * http://lilypond.org/doc/v2.12/input/regression/musicxml/collated-files.html
