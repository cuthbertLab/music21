/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


window[(typeof (djConfig)!="undefined"&&djConfig.scopeMap&&djConfig.scopeMap[0][1])||"dojo"]._xdResourceLoaded(function(_1,_2,_3){return {depends:[["provide","dijit._base.window"]],defineResource:function(_4,_5,_6){if(!_4._hasResource["dijit._base.window"]){_4._hasResource["dijit._base.window"]=true;_4.provide("dijit._base.window");_5.getDocumentWindow=function(_7){if(_4.isIE&&window!==document.parentWindow&&!_7._parentWindow){_7.parentWindow.execScript("document._parentWindow = window;","Javascript");var _8=_7._parentWindow;_7._parentWindow=null;return _8;}return _7._parentWindow||_7.parentWindow||_7.defaultView;};}}};});