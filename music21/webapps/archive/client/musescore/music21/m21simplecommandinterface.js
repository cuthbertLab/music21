var responseFile;

var reqId;
var defaultOpenDir = QDir.homePath();

var ui;

// Loads External JSON2 file for json parsing
function init() {
    Qt.include("json2.js");
};

// Called when plugin is started - loads and displays ui interface
function run() {
    var loader = new QUiLoader(null);
    var file   = new QFile(pluginPath + "/m21simplecommandinterface.ui");
    file.open(QIODevice.OpenMode(QIODevice.ReadOnly, QIODevice.Text));
    ui = loader.load(file, null);
    ui.buttonBox.accepted.connect(submitDialog);
    ui.show();
}

// Called when OK is clicked from Dialog
function submitDialog() {
    // Get information from form
    var cmd = ui.command.plainText;
    
    // Save and read score XML    
	curScore.save('/tmp/museScore_to_music21.xml','xml');
    xmlcontent = readFile('/tmp/museScore_to_music21.xml');
    
    // Make JSON String of information
	var obj = { 
		 "type"   :   "simpleCommand", 
		 "xml"    :   xmlcontent, 
		 "cmd"    :   cmd, 
	};
	var jsontext = JSON.stringify(obj);
        

    // HTTP Post involves sending a data file to a url.
    // The response is written to the reponseFile
    data = new QByteArray();
    data.append(jsontext);
    
	responseFile = new QTemporaryFile("/tmp/response_from_music21_XXXXXX.xml");
	responseFile.open();

    var url = "http://lars-johnsons-macbook-pro.local./music21interface";

	var http = new QHttp();
	http.setHost("lars-johnsons-macbook-pro.local.", 80);
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
        writeFile('/tmp/xml_to_museScore.xml',json_response_obj['xml']);
        var score = new Score();
        score.load('/tmp/xml_to_museScore.xml');
        if(json_reponse_obj['message']) {
           displayMessage(json_response_obj['message']);
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
   menu: 'Plugins.Music21.M21 Simple Command Interface',
   init: init,
   run: run,
   onClose: close
};

mscorePlugin;
