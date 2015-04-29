var responseFile;

var reqId;
var defaultOpenDir = QDir.homePath();

var ui;

var SERVER_URL = "http://ciconia.mit.edu/music21/music21interface";
var SERVER_HOST = "ciconia.mit.edu";

var LOCAL_SERVER_URL = "http://larsj.local/music21interfaceArchive";
var LOCAL_SERVER_HOST = "larsj.local";

// Loads External JSON2 file for json parsing
function init() {
    Qt.include("json2.js");
};

// Called when plugin is started - loads and displays ui interface
function run() {
    var loader = new QUiLoader(null);
    var file   = new QFile(pluginPath + "/m21codeinterfaceresults.ui");
    file.open(QIODevice.OpenMode(QIODevice.ReadOnly, QIODevice.Text));
    ui = loader.load(file, null);
    ui.code.plainText = "";
    ui.output.plainText = "(output will appear here)";
    ui.executeButton.clicked.connect(submitDialog);
    ui.show();
}

function submitDialog() {
    // Get information from form
    var code = ui.code.plainText;
    ui.output.plainText = "Processing";
    ui.executeButton.text = "Processing";
    ui.executeButton.enabled = false;
    

    if (ui.exportCurrent.checked == true) {
        // Save and read score XML    
        curScore.save('/tmp/museScore_to_music21.xml','xml');
        xmlcontent = readFile('/tmp/museScore_to_music21.xml');
    
        // Make JSON String of information
        var obj = { 
             "type"   :   "code", 
             "xml"    :   xmlcontent, 
             "code"    :   code, 
        };
    }
    else {
        // Make JSON String of information
        var obj = { 
             "type"   :   "code", 
             "code"    :   code, 
        };
    
    }
	var jsontext = JSON.stringify(obj);
        

    // HTTP Post involves sending a data file to a url.
    // The response is written to the reponseFile
    data = new QByteArray();
    data.append(jsontext);
    
	responseFile = new QTemporaryFile("/tmp/response_from_music21_XXXXXX.xml");
	responseFile.open();
    
    // Determine where to send request
    if (ui.executeOnCiconia.checked == true) {
        url = SERVER_URL;
        host = SERVER_HOST;
    } else {
        url = LOCAL_SERVER_URL;
        host = LOCAL_SERVER_HOST;
    }
    
	var http = new QHttp();
	http.setHost(host, 80);
	http.requestFinished.connect(responseFile,response_function);
	reqId = http.post(url,data,responseFile);

};


// Called on response from Music21. Writes the file to 
function response_function(id ,error){
	if (error){
		errorMessage();
		return;
	}
	if (id == reqId){
		responseFile.flush();
		responseFile.close();
        responseText = readFile(responseFile.fileName());
		json_response_obj = JSON.parse(responseText);
        ui.executeButton.enabled = true;
        ui.executeButton.text = "Execute";
        if(json_response_obj['status'] == 'error') {
            displayMessage('Note: An error occurred in processing your code')
            ui.code.plainText = json_response_obj['origObj']['code'];
            ui.output.plainText = json_response_obj['error'];
            ui.executeButton.clicked.connect(submitResultsDialog);
            ui.show();
        } else{
            if (ui.showSc.checked == true) {
                writeFile('/tmp/xml_to_museScore.xml',json_response_obj['xml']);
                var score = new Score();
                score.load('/tmp/xml_to_museScore.xml');
            }
            ui.code.plainText = json_response_obj['code'];
            ui.output.plainText = json_response_obj['stdOut'];
            ui.executeButton.clicked.connect(submitDialog);
            ui.show();
        }

    }
}


// -- HELPER FUNCTIONS --

// Displays dialog box with text message
function displayMessage(msg){
      mb = new QMessageBox();
      mb.setWindowTitle("Music21 message:");
      mb.text = msg;
      mb.exec();
}

// Returns string of contents of filepath
function readFile(filepath) {
    var file = new QFile(filepath);
	var line;
	if ( file.open(QIODevice.ReadOnly) ) {       
	  // file opened successfully
	  var t = new QTextStream( file ); // use a text stream
	  var result ="";
	  
	  do {
		line = t.readLine(); // line of text excluding '\n'
		// do something with the line
		result +=line; 
		result +='\n';    // add the missing '\n'
	  } while (line);        
	  // Close the file
	  file.close();
	}
    return result;
}

// Writes contents to filePath
function writeFile(filepath, contents) {
    var file = new QFile(filepath);
	if(file.exists())
		file.remove();
	if ( file.open(QIODevice.ReadWrite) ) {       
        // file opened successfully
        var textStream = new QTextStream(file);
        textStream.writeString(contents); // set string
        file.close();
	}
}

// Needed as part of the MuseScore Plugin Specificatino
function close() {};

// -- Sets up MuseScore Access, names of functions
var mscorePlugin =
{
   majorVersion: 1,
   minorVersion: 1,
   menu: 'Plugins.Music21.M21 Code Interface',
   init: init,
   run: run,
   onClose: close
};

mscorePlugin;
