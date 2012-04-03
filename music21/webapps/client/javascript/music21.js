
function createAJAXObject() {
	var request_type;
	var browser = navigator.appName;
	if(browser == "Microsoft Internet Explorer"){
		request_type = new ActiveXObject("Microsoft.XMLHTTP");
	}else{
		request_type = new XMLHttpRequest();
	}
	return request_type;
};

function createRequestObject() {
	var req_obj = Object();
	req_obj.dataDict = {};
	req_obj.commandList = [];
	req_obj.returnList = {};
};

// Get Movie - provides access to the flash Object - accounts for browser differences
function getMovie(movieName) {
    if (navigator.appName.indexOf("Microsoft") != -1) {
        return document.getElementById(movieName);
    }
    else {
        return document[movieName]
    }
}
function newData(name, fmt, data) {
	d = Object();
	d.fmt = fmt;
	d.data = data;
	return d;
}


function Music21interface() {
	var ajaxObj = createAJAXObject();
	this.requestObj = createRequestObject();
	var curUrl = window.location.href;
	var arr = curUrl.split("/");
	var hostProtocol = arr[0] + "//" + arr[2];
	
	this.queryMusic21 = function () {
		musicxml = getMovie('score1').getMusicXML();
			
		var obj = {
			"dataDict" : {
				"sc" : {
					"fmt" : "xml",
					"data" : musicxml
				}
			},
			"commandList" : [
				{"function" : "transpose",
				 "caller" : "sc",
				 "argList" : ["'p5'"],
				 "resultVariable" : "sc"}
			],
			"returnList" : [
				{"name" : "sc",
				"fmt" : "xml"}
			]
		};
		obj.commandList[obj.commandList.length] = 
				{"function" : "transpose",
				 "caller" : "sc",
				 "argList" : ["'p5'"],
				 "resultVariable" : "sc"};
		//obj.dataDict = {};
		//obj.dataDict.sc = newData("name","xml",musicxml);
		
		var jsontext = JSON.stringify(obj);
		document.getElementById('requestxmltextarea').value = jsontext;		
	
		// Set te random number to add to URL request
		nocache = Math.random();
		ajaxObj.open('POST', hostProtocol+'/music21interface',true);
		ajaxObj.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		ajaxObj.send(jsontext);
	
		ajaxObj.onreadystatechange = this.reply;
	};
	
    this.queryMusic21String = function (jsonStr) {
	
		// Set te random number to add to URL request
		nocache = Math.random();
		ajaxObj.open('POST', hostProtocol+'/music21interface',true);
		ajaxObj.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		ajaxObj.send(jsonStr);
	
		ajaxObj.onreadystatechange = this.reply;
	};
	
	this.reply = function () {
		if(ajaxObj.readyState == 4){
			json_response = ajaxObj.responseText;
			document.getElementById('realresponse').value = json_response;
			//return;
			
			json_response_obj = JSON.parse(json_response);		
			response_xml = json_response_obj['dataDict']['sc']['data'];
			document.getElementById('resultxmltextarea').value = response_xml;
			
			getMovie('score1').loadMusicXML(response_xml);		
		};
	}

};