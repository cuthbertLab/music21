/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


window[(typeof (djConfig)!="undefined"&&djConfig.scopeMap&&djConfig.scopeMap[0][1])||"dojo"]._xdResourceLoaded(function(_1,_2,_3){return {depends:[["provide","dojo.string"]],defineResource:function(_4,_5,_6){if(!_4._hasResource["dojo.string"]){_4._hasResource["dojo.string"]=true;_4.provide("dojo.string");_4.string.rep=function(_7,_8){if(_8<=0||!_7){return "";}var _9=[];for(;;){if(_8&1){_9.push(_7);}if(!(_8>>=1)){break;}_7+=_7;}return _9.join("");};_4.string.pad=function(_a,_b,ch,_c){if(!ch){ch="0";}var _d=String(_a),_e=_4.string.rep(ch,Math.ceil((_b-_d.length)/ch.length));return _c?_d+_e:_e+_d;};_4.string.substitute=function(_f,map,_10,_11){_11=_11||_4.global;_10=_10?_4.hitch(_11,_10):function(v){return v;};return _f.replace(/\$\{([^\s\:\}]+)(?:\:([^\s\:\}]+))?\}/g,function(_12,key,_13){var _14=_4.getObject(key,false,map);if(_13){_14=_4.getObject(_13,false,_11).call(_11,_14,key);}return _10(_14,key).toString();});};_4.string.trim=String.prototype.trim?_4.trim:function(str){str=str.replace(/^\s+/,"");for(var i=str.length-1;i>=0;i--){if(/\S/.test(str.charAt(i))){str=str.substring(0,i+1);break;}}return str;};}}};});