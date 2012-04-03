/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


window[(typeof (djConfig)!="undefined"&&djConfig.scopeMap&&djConfig.scopeMap[0][1])||"dojo"]._xdResourceLoaded(function(_1,_2,_3){return {depends:[["provide","dojo.AdapterRegistry"]],defineResource:function(_4,_5,_6){if(!_4._hasResource["dojo.AdapterRegistry"]){_4._hasResource["dojo.AdapterRegistry"]=true;_4.provide("dojo.AdapterRegistry");_4.AdapterRegistry=function(_7){this.pairs=[];this.returnWrappers=_7||false;};_4.extend(_4.AdapterRegistry,{register:function(_8,_9,_a,_b,_c){this.pairs[((_c)?"unshift":"push")]([_8,_9,_a,_b]);},match:function(){for(var i=0;i<this.pairs.length;i++){var _d=this.pairs[i];if(_d[1].apply(this,arguments)){if((_d[3])||(this.returnWrappers)){return _d[2];}else{return _d[2].apply(this,arguments);}}}throw new Error("No match found");},unregister:function(_e){for(var i=0;i<this.pairs.length;i++){var _f=this.pairs[i];if(_f[0]==_e){this.pairs.splice(i,1);return true;}}return false;}});}}};});