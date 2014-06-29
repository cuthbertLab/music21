.. _usersGuide_96_ipython_comm:
.. code:: python


.. code:: python

    from music21 import *

.. code:: python

    from IPython.display import HTML, Javascript

.. code:: python

    m21url = "http://web.mit.edu/music21/music21j/src/music21.js"
    
    def Javas(msg, lib=None):
        pass
    
    Javas('console.log("m", music21);', lib=[m21url])
    HTML('''
    <script>
    require.config(
       { baseUrl: "http://web.mit.edu/music21/music21j/src/",
         paths: {'music21': 'http://web.mit.edu/music21/music21j/src/music21',}
        });
    console.log('hi');
      require(['music21'], function () {
          console.log('hey!');
          var n = new music21.note.Note("D#4");
          var s = new music21.stream.Stream();
          s.append(n);
      
          s.appendNewCanvas($('.output_subarea.output_html.rendered_html.output_pyout')[0]);
      });
    </script>
    ''')



.. code:: python

    nn = note.Note


.. code:: python

    vfp = vexflow.toMusic21j.VexflowPickler()
    vfp.mode = 'json'
    
    # Example from http://jakevdp.github.io/blog/2013/06/01/ipython-notebook-javascript-python-communication/ adapted for IPython 2.0
    # Add an input form similar to what we saw above
    input_form = """
    <div id="heya" style="background-color:gainsboro; border:solid black; width:600px; padding:20px;">
    Code: <input type="text" id="code_input" size="50" height="2" 
           value="corpus.parse('bwv66.6').measures(0,4)"><br>
    Result: <input type="text" id="result_output" size="50" value="??"><br>
    <button onclick="exec_code()">Execute</button>
    </div>
    """
     
    # here the javascript has a function to execute the code
    # within the input box, and a callback to handle the output.
    javascript = """
    <script type="text/Javascript">
    var heya = $('#heya');
    var newCanvas = $("<canvas/>");
    heya.append(newCanvas);
    
    function getData(msg) {
           var data = handle_output(msg);
           data = data.slice(1, -1);       
    var jpc = new music21.jsonPickle.Converter();
    var streamObj = jpc.run(data);
    streamObj.replaceLastCanvas("#heya");
           document.getElementById("result_output").value = streamObj._elements.length;
    
    }
    
    
       function handle_output(out){
           console.log(out);
           var res = null;
            // if output is a print statement
           if(out.msg_type == "stream"){
               res = out.content.data;
           }
           // if output is a python object
           else if(out.msg_type === "pyout"){
               res = out.content.data["text/plain"];
           }
           // if output is a python error
           else if(out.msg_type == "pyerr"){
               res = out.content.ename + ": " + out.content.evalue;
           }
           // if output is something we haven't thought of
           else{
               res = "[out type not implemented]";  
           }
           return res;
       }
       
       function exec_code(){
           var code_input = document.getElementById('code_input').value;
           var messagedCodeInput = 'vfp.fromObject(' + code_input + ')';
           
           var kernel = IPython.notebook.kernel;
           var callbacks = { 'iopub' : {'output' : getData}};
           document.getElementById("result_output").value = "";  // clear output box
           var msg_id = kernel.execute(messagedCodeInput, callbacks, {silent:false});
           console.log("button pressed");
           // IPython.notebook.clear_output();
       }
    </script>
    """
     
    HTML(input_form + javascript)



.. code:: python

    import random
    def vfshow(s):
        vfp = vexflow.toMusic21j.VexflowPickler()
        vfp.mode = 'jsonSplit'
        outputCode = vfp.fromObject(s)
        idName = 'canvasDiv' + str(random.randint(0, 10000))
        htmlBlock = '<div id="' + idName + '"><canvas/></div>'
        js = '''
        <script>
             require(['music21'], function() { 
               data = ''' + outputCode + ''';       
               var jpc = new music21.jsonPickle.Converter();
               streamObj = jpc.run(data);
               streamObj.replaceCanvas("#''' + idName + '''");
             });
        </script>
        '''
        return HTML(htmlBlock + js)

.. code:: python

    bach = corpus.parse('bwv66.6').measures(0, 4)
    vfshow(bach)



.. code:: python

    bach


.. parsed-literal::
   :class: ipython-result

    <music21.stream.Score 4412264400>


.. code:: python

    Javascript('''var n = new music21.note.Note("F#4");
          var s = new music21.stream.Stream();
          s.append(n);
          var newPlace = $('div.output_subarea.output_javascript.output_pyout');
          console.log(newPlace);
          s.appendNewCanvas(newPlace[newPlace.length-1]);''')


.. parsed-literal::
   :class: ipython-result

    <IPython.core.display.Javascript at 0x107704250>


.. code:: python

    

.. code:: python

    
