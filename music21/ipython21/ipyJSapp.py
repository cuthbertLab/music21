############
#
# IPythonNotebook like connections between Javascript and Python, but 


# start with
# ~/anaconda/bin/python ipythonNotebookStart 

#    -- needs ipython v.2  
import os
import threading
import webbrowser
from IPython.html import notebookapp # @UnresolvedImport


def runApp(htmlFile = 'm21pj.html'):
    '''
    run the Javascript to Python processor
    '''
    thisDirectory = os.path.abspath(os.path.dirname(__file__))
    nbDirectory = os.path.join(thisDirectory, 'notebookBlank')
    print(nbDirectory)
    staticDirectory = os.path.join(thisDirectory, 'static')
    
    relativeStaticFile = 'static/' + htmlFile
    print(relativeStaticFile)
    print(staticDirectory)
    
    npa = notebookapp.NotebookApp()
    npa.extra_static_paths = [staticDirectory]
    #print(npa.connection_url)
    OPEN_IN_NEW_TAB = 2
    
    
    # start the web browser after a delay so that the webserver can already have started...
    delayInSeconds = 2
    startWebbrowserDelayed = lambda: webbrowser.open(
                                    npa.connection_url + relativeStaticFile, new=OPEN_IN_NEW_TAB )
    threading.Timer(delayInSeconds, startWebbrowserDelayed).start()
    
    # now start the main app
    npa.launch_instance(open_browser=False, notebook_dir=nbDirectory, extra_static_paths = [staticDirectory])


if __name__ == '__main__':
    runApp('m21pj.html')