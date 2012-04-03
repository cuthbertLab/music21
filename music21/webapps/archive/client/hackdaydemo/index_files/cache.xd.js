/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


window[(typeof (djConfig)!="undefined"&&djConfig.scopeMap&&djConfig.scopeMap[0][1])||"dojo"]._xdResourceLoaded(function(_1,_2,_3){return {depends:[["provide","dojo.cache"]],defineResource:function(_4,_5,_6){if(!_4._hasResource["dojo.cache"]){_4._hasResource["dojo.cache"]=true;_4.provide("dojo.cache");(function(){var _7={};_4.cache=function(_8,_9,_a){if(typeof _8=="string"){var _b=_4.moduleUrl(_8,_9);}else{_b=_8;_a=_9;}var _c=_b.toString();var _d=_a;if(_a!==undefined&&!_4.isString(_a)){_d=("value" in _a?_a.value:undefined);}var _e=_a&&_a.sanitize?true:false;if(_d||_d===null){if(_d==null){delete _7[_c];}else{_d=_7[_c]=_e?_4.cache._sanitize(_d):_d;}}else{if(!(_c in _7)){_d=_4._getText(_c);_7[_c]=_e?_4.cache._sanitize(_d):_d;}_d=_7[_c];}return _d;};_4.cache._sanitize=function(_f){if(_f){_f=_f.replace(/^\s*<\?xml(\s)+version=[\'\"](\d)*.(\d)*[\'\"](\s)*\?>/im,"");var _10=_f.match(/<body[^>]*>\s*([\s\S]+)\s*<\/body>/im);if(_10){_f=_10[1];}}else{_f="";}return _f;};})();}}};});