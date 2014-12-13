.. _usersGuide_96b_ipython_comm_noM21:
.. code:: python

    from IPython.display import HTML, Javascript

.. code:: python

    input_form = """
    <div id="heya" style="background-color:gainsboro; border:solid black; width:600px; padding:20px;">
    Code: <input type="text" id="code_input" size="50" height="2" 
           value="round(23.522, 2)"><br>
    Result: <input type="text" id="result_output" size="50" value="??"><br>
    <button onclick="exec_code()">Execute</button>
    </div>
    """
     
    # here the javascript has a function to execute the code
    # within the input box, and a callback to handle the output.
    javascript = """
    <script type="text/javascript">
       function getData(msg) {
           var data = handle_output(msg);
           console.log(data);
           document.getElementById("result_output").value = data;
       }
    
    
       function handle_output(out){
           console.log(out);
           var res = null;
            // if output is a print statement
           if(out.msg_type == "stream"){ // nothing to do with music21 stream
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
           var kernel = IPython.notebook.kernel;
           var callbacks = { 'iopub' : {'output' : getData}};
           document.getElementById("result_output").value = "";  // clear output box
           var msg_id = kernel.execute(code_input, callbacks, {silent:false});
           console.log("button pressed");
           // IPython.notebook.clear_output();
       }
    </script>
    """
     
    HTML(input_form + javascript)



.. code:: python

    HTML(input_form)



.. code:: python

    round(23.122, 2)


.. parsed-literal::
   :class: ipython-result

    23.12

