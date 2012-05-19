// Utility Functions
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


// Main Music21 Interface Object
function Music21interface() {
	var self = this;
	
	var curUrl = window.location.href;
	var arr = curUrl.split("/");
	var hostProtocol = arr[0] + "//" + arr[2];
	
	self.ajaxObj = createAJAXObject()
	
	// Allows user to build the request before sending
	self.request = {
		dataDict : new Object(),
		commandList : [],
		returnDict : new Object(),
		// Adds data to dataDict (replaces if key already exists)
		addData : function (name, fmt, data) {
			var dataObj = new Object();
			dataObj.data = data;
			if(fmt) {
				dataObj.fmt = fmt;
			}
			self.request.dataDict[name] = dataObj;
		},
		
		// Adds command to commandList
		addCommand : function (type, resultVar, caller, command, argList) {
			var cmdObj = new Object();
			cmdObj[type] = command;
			if (resultVar) {
				cmdObj.resultVar = resultVar;
			}
			if (caller) {
				cmdObj.caller = caller;
			}
			if (argList) {
				cmdObj.argList = argList;
			}
			self.request.commandList.push(cmdObj);
		},
		
		// Adds variable name to returnDict
		addReturnVar : function (varName, fmt) {
			self.request.returnDict[varName] = fmt;
		},
		
		
		// Clears the request object in preparation for a new request
		clear : function() {
			self.request.dataDict = new Object();
			self.request.commandList = new Array();
			self.request.returnDict = new Object();
		},
		
		// Combines the datadict, commandlist, returnDict into a json string
		jsonText : function() {
			var obj = {
				dataDict : self.request.dataDict,
				commandList : self.request.commandList,
				returnDict : self.request.returnDict
			};
			return JSON.stringify(obj);
		},
		prettyJsonText : function() {
			var obj = {
				dataDict : self.request.dataDict,
				commandList : self.request.commandList,
				returnDict : self.request.returnDict
			};
			return JSON.stringify(obj,undefined,2);
		}
	};
	
	self.sendRequest = function () {
		var jsonStr = self.request.jsonText();
		self.sendRawRequest(jsonStr)
	};
	
	self.sendRawRequest = function (jsonStr) {
		this.ajaxObj.open('POST',self.opts.postUrl,true);
		this.ajaxObj.setRequestHeader("Content-type", "application/json");
		this.ajaxObj.send(jsonStr);	
		this.ajaxObj.onreadystatechange = function() {
			self.onServerReply();
		};
	};

	self.onServerReply = function () {
		if(self.ajaxObj.readyState == 4){
			var jsonStr = this.ajaxObj.responseText;
			self.result.rawResponse = jsonStr;
			self.result.responseObj = JSON.parse(jsonStr);
		
			if(self.result.responseObj.status == "error") {
				self.onError();
				
			} else {
				self.onSuccess();
			}
		}
		
	};
	
	// On reply functions, to be overridden in specific use cases
	self.onError = function () {
	};
	
	self.onSuccess = function () {
	};
	
	self.result = {
		rawResponse : "",
		responseObj : {},
		getData : function (varName) {
			if (self.result.responseObj.dataDict) {
				if (varName in self.result.responseObj.dataDict) {
					return self.result.responseObj.dataDict[varName].data;
				} else {
					//alert(varName + " not found in result object");
					return null;
				}
			} else {
				return null;
			}
		},
		errorString : function() {
			var str = "";
			for (i = 0; i < self.result.responseObj.errorList.length; i++) {
				str += self.result.responseObj.errorList[i] + "<br />";
			}
			return str;
		}
	};
	
	self.opts = {
		curUrl : window.location.href,
		postUrl : hostProtocol+"/music21/webinterface"
	};
	
	self.noteflight = {
		createNoteflightEmbed : function (divid, scoreid, noteflightid, width, height, scale) {
			if(!scale) {
				scale = 1.0;
			}
			var embedURL = "http://music21.sites.noteflight.com/scores/embed";
			document.getElementById(divid).innerHTML = "<object id='"+scoreid+"' width='"+width+"' height='"+height+"'> \
				<param name='movie' value='"+embedURL+"'></param> \
				<param name='FlashVars' value='id="+noteflightid+"&scale="+scale+"&role=template&displayMode=paginated'></param> \
				<param name='allowScriptAccess' value='always'/> \
				<embed name='"+scoreid+"' src='"+embedURL+"' type='application/x-shockwave-flash' \
					FlashVars='id="+noteflightid+"&scale="+scale+"&role=template&displayMode=paginated' \
					width='"+width+"' height='"+height+"' \
					allowScriptAccess='always'> \
				</embed> \
				</object>";
			
		},
		
		getNoteflightEmbed :  function(scoreid) {
			if (navigator.appName.indexOf("Microsoft") != -1) {
				return document.getElementById(scoreid);
			}
			else {
				return document[scoreid]
			}
		},
		sendMusicXMLToNoteflightEmbed : function (scoreid, musicxml) {
			
			self.noteflight.getNoteflightEmbed(scoreid).loadMusicXML(musicxml)
		},
		getMusicXMLFromNoteflightEmbed : function (scoreid) {
			return self.noteflight.getNoteflightEmbed(scoreid).getMusicXML();
		}
	}
	
}