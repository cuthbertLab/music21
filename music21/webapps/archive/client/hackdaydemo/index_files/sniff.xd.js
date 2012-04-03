/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


window[(typeof (djConfig)!="undefined"&&djConfig.scopeMap&&djConfig.scopeMap[0][1])||"dojo"]._xdResourceLoaded(function(_1,_2,_3){return {depends:[["provide","dijit._base.sniff"]],defineResource:function(_4,_5,_6){if(!_4._hasResource["dijit._base.sniff"]){_4._hasResource["dijit._base.sniff"]=true;_4.provide("dijit._base.sniff");(function(){var d=_4,_7=d.doc.documentElement,ie=d.isIE,_8=d.isOpera,_9=Math.floor,ff=d.isFF,_a=d.boxModel.replace(/-/,""),_b={dj_ie:ie,dj_ie6:_9(ie)==6,dj_ie7:_9(ie)==7,dj_ie8:_9(ie)==8,dj_iequirks:ie&&d.isQuirks,dj_opera:_8,dj_khtml:d.isKhtml,dj_webkit:d.isWebKit,dj_safari:d.isSafari,dj_chrome:d.isChrome,dj_gecko:d.isMozilla,dj_ff3:_9(ff)==3};_b["dj_"+_a]=true;for(var p in _b){if(_b[p]){if(_7.className){_7.className+=" "+p;}else{_7.className=p;}}}_4._loaders.unshift(function(){if(!_4._isBodyLtr()){_7.className+=" dijitRtl";for(var p in _b){if(_b[p]){_7.className+=" "+p+"-rtl";}}}});})();}}};});