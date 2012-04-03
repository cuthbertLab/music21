var responseFile;

var reqId;
var defaultOpenDir = QDir.homePath();

var exerciseChooserUI;
var additionalQuestionsUI;
var checkerResultsUI;
var submitUI;

var exerciseID;

var SERVER_URL = "http://ciconia.mit.edu/music21/music21interface";
var SERVER_HOST = "ciconia.mit.edu";

var LOCAL_SERVER_URL = "http://larsj.local/music21interface";
var LOCAL_SERVER_HOST = "larsj.local";


// Loads External JSON2 file for json parsing
function init() {
    Qt.include("json2.js");
};

// Called when plugin is started - loads and displays exercise chooser
function run() {
    var loader = new QUiLoader(null);
    var file   = new QFile(pluginPath + "/exercisechooser.ui");
    file.open(QIODevice.OpenMode(QIODevice.ReadOnly, QIODevice.Text));
    exerciseChooserUI = loader.load(file, null);
    exerciseChooserUI.treeWidget.setColumnHidden(1,true);
    exerciseChooserUI.instructionText.text = "Select the exercise you wish to check:"
    pm = new QPixmap(pluginPath + "/data/header.png");
    exerciseChooserUI.header.setPixmap(pm);
    exerciseChooserUI.buttonBox.accepted.connect(submitExerciseChooser);
    exerciseChooserUI.show();
}

// Called when OK is clicked from additional Questions
function submitExerciseChooser() {
    // Get information from form
    exerciseID = exerciseChooserUI.treeWidget.currentItem().text(1);
    //displayMessage(exerciseID);
    
    curScore.save('/tmp/museScore_to_music21.xml','xml');
    xmlcontent = readFile('/tmp/museScore_to_music21.xml');
        
    // Make JSON String of information
	var obj = { 
		 "type"     :   "wwnorton", 
		 "command"  :   "checkExercise",
		 "xml"    :   xmlcontent, 
		 "exerciseID"    :   exerciseID, 
	};
    var jsontext = JSON.stringify(obj);
        

    // HTTP Post involves sending a data file to a url.
    // The response is written to the reponseFile
    data = new QByteArray();
    data.append(jsontext);
	responseFile = new QTemporaryFile("/tmp/response_from_music21_XXXXXX.xml");
	responseFile.open();

    var url = LOCAL_SERVER_URL;

	var http = new QHttp();
	http.setHost(LOCAL_SERVER_HOST, 80);
	http.requestFinished.connect(responseFile,checkExerciseRequestFinished);
	reqId = http.post(url,data,responseFile);
}

function loadExerciseRequestFinished(id ,error) {
    if (error){
		errorMessage();
		return;
	}
	if (id == reqId){
		responseFile.flush();
		responseFile.close();
        responseText = readFile(responseFile.fileName());
		json_response_obj = JSON.parse(responseText);
        
        var loader = new QUiLoader(null);
        var file   = new QFile(pluginPath + "/instructionsAndCheck.ui");
        file.open(QIODevice.OpenMode(QIODevice.ReadOnly, QIODevice.Text));
        instAndCheckUI = loader.load(file, null);
        
        if (json_response_obj['additionalQuestion'] != "") {
            instructions = json_response_obj['additionalQuestionInstructions']
            label = json_response_obj['additionalQuestion']
            showAdditionalQuestion(instructions,label)
        } else {
            submitStudentAssignment()
        }
        
    }
}


/*function showAdditionalQuestion(instructions, label) {
    var loader = new QUiLoader(null);
    var file   = new QFile(pluginPath + "/additionalQuestions.ui");
    file.open(QIODevice.OpenMode(QIODevice.ReadOnly, QIODevice.Text));
    additionalQuestionsUI = loader.load(file, null);
    additionalQuestionsUI.textFieldInstructions.text = instructions
    additionalQuestionsUI.textFieldLabel.text = label
    additionalQuestionsUI.buttonBox.accepted.connect(submitAdditionalQuestions);
    pm = new QPixmap(pluginPath + "/data/header.png");
    additionalQuestionsUI.header.setPixmap(pm);
    additionalQuestionsUI.show();
}*/

/*function run() {
    var loader = new QUiLoader(null);
    var file   = new QFile(pluginPath + "/submitExercise.ui");
    file.open(QIODevice.OpenMode(QIODevice.ReadOnly, QIODevice.Text));
    submitUI = loader.load(file, null);
    submitUI.buttonBox.accepted.connect(submitExercise);
    pm = new QPixmap(pluginPath + "/data/header.png");
    submitUI.header.setPixmap(pm);
    submitUI.show();
}*/

// Called when OK is clicked from additional Questions
function submitExercise() {
    // Get information from form
    // Save and read score XML  
    // Get information from form
    var studentName = submitUI.studentName.text;
    var studentEmail = submitUI.studentEmail.text;

	curScore.save('/tmp/museScore_to_music21.xml','xml');
    xmlcontent = readFile('/tmp/museScore_to_music21.xml');
        
    // Make JSON String of information
	var obj = { 
		 "type"     :   "wwnorton", 
		 "command"  :   "checkExercise",
		 "xml"    :   xmlcontent, 
		 "exerciseID"    :   "11_3_A_2", 
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
	http.requestFinished.connect(responseFile,submitExerciseRequestFinished);
	reqId = http.post(url,data,responseFile);
}

// Called once the server is done processing the load exercise request
function checkExerciseRequestFinished(id ,error) {
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
        showResults(json_response_obj['message']);
    }
}

function showResults(resultsString) {
    var loader = new QUiLoader(null);
    var file   = new QFile(pluginPath + "/checkerResults.ui");
    file.open(QIODevice.OpenMode(QIODevice.ReadOnly, QIODevice.Text));
    checkerResultsUI = loader.load(file, null);
    checkerResultsUI.results.text = resultsString
    //height = checkerResultsUI.results.height + 150
    //displayMessage(height)
    checkerResultsUI.buttonBox.accepted.connect(finished);
    pm = new QPixmap(pluginPath + "/data/header.png");
    checkerResultsUI.header.setPixmap(pm);
    pm2 = new QPixmap(pluginPath + "/data/results.png");
    checkerResultsUI.resultsHeader.setPixmap(pm2);
    checkerResultsUI.results.adjustSize()
    checkerResultsUI.adjustSize()
    checkerResultsUI.show();
}

function finished() {
    checkerResultsUI.hide();
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
   menu: 'Plugins.Music21.Check exercise',
   init: init,
   run: run,
   onClose: close
};

mscorePlugin;
