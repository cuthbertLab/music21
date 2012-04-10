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
		returnList : new Array(),
		
		// Adds data to dataDict (replaces if key already exists)
		addData : function (name, fmt, data) {
			self.request.dataDict[name] = { "fmt" : fmt,
											"data" : data};
		},
		
		// Adds command to commandList
		addCommand : function (type, resultVar, caller, command, argList) {
			var cmdObj = new Object();
			cmdObj[type] = command;
			if (resultVar) {
				cmdObj.resultVariable = resultVar;
			}
			if (caller) {
				cmdObj.caller = caller;
			}
			if (argList) {
				cmdObj.argList = argList;
			}
			self.request.commandList.push(cmdObj);
		},
		
		// Adds variable name to returnList
		addReturnVar : function (varName, fmt) {
			self.request.returnList.push({name: varName, fmt: fmt});
		},
		
		
		// Clears the request object in preparation for a new request
		clear : function() {
			self.request.dataDict = new Object();
			self.request.commandList = new Array();
			self.request.returnList = new Array();
		},
		
		// Combines the datadict, commandlist, returnlist into a json string
		jsonText : function() {
			var obj = {
				dataDict : self.request.dataDict,
				commandList : self.request.commandList,
				returnList : self.request.returnList,
			};
			return JSON.stringify(obj);
		}
	};
	
	self.sendRequest = function () {
		var jsonStr = this.request.jsonText();
		this.ajaxObj.open('POST',this.opts.postUrl,true);
		this.ajaxObj.setRequestHeader("Content-type", "application/json");
		this.ajaxObj.send(jsonStr);	
		this.ajaxObj.onreadystatechange = function() {
			self.onServerReply();
		};
	};

	self.onServerReply = function () {
		if(self.ajaxObj.readyState == 4){
			var jsonStr = this.ajaxObj.responseText;
			self.result.responseObj = JSON.parse(jsonStr);
		}
		if(self.result.responseObj.status == "error") {
			self.onError();
			
		} else {
			self.onSuccess();
		}
		
	};
	
	// On reply functions, to be overridden in specific use cases
	self.onError = function () {
	};
	
	self.onSuccess = function () {
	};
	
	self.result = {
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
		postUrl : hostProtocol+"/music21interface"
	};
	
	self.util = {
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
			
			self.util.getNoteflightEmbed(scoreid).loadMusicXML(musicxml)
		},
		getMusicXMLFromNoteflightEmbed : function (scoreid) {
			return self.util.getNoteflightEmbed(scoreid).getMusicXML();
		}
	}
	
}