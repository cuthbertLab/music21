
var outFile;
var reqId;
var defaultOpenDir = QDir.homePath();

var form;

function init() {};

function run() {    
	curScore.save('/tmp/museScore_to_music21.xml','xml');
	var file = new QFile('/tmp/museScore_to_music21.xml');
	var line;
	if ( file.open(QIODevice.ReadOnly) ) {       
	  // file opened successfully
	  var t = new QTextStream( file ); // use a text stream
	  var content ="";
	  
	  do {
		line = t.readLine(); // line of text excluding '\n'
		// do something with the line
		content +=line; 
		content +='\n';    // add the missing '\n'
	  } while (line);        
	  // Close the file
	  file.close();
	}
    print('content');
		
	var url = "http://lars-johnsons-macbook-pro.local./music21interface/process";
    
    data = new QByteArray();
    data.append("xmltext=" + content+"&cmd=reduction&appname=musescore")

	outFile = new QTemporaryFile("/tmp/result_from_music21_XXXXXX.xml");
	outFile.open();
    
	var http = new QHttp();
	http.setHost("lars-johnsons-macbook-pro.local.", 80);
	http.requestFinished.connect(outFile,finished);
	reqId = http.post(url,data,outFile);

};
//---------------------------------------------------------
// display a message box with error message
//---------------------------------------------------------
function errorMessage(){
      mb = new QMessageBox();
      mb.setWindowTitle("Error: music21 connection error");
      mb.text = "Error with music21 export";
      mb.exec();
}

function finished(id ,error){
	print("finished");
	print(id);
	if (error){
		errorMessage();
		return;
	}
	if (id == reqId){
		outFile.flush();
		outFile.close();
		if(outFile.size() > 200){
			var score   = new Score();
			score.load(outFile.fileName());    
		} else {
			errorMessage();
		}  
	}
}


function close() {};

var mscorePlugin =
{
   majorVersion: 1,
   minorVersion: 1,
   menu: 'Plugins.Music21 (Old).Mensural Canon',
   init: init,
   run: run,
   onClose: close
};

mscorePlugin;
