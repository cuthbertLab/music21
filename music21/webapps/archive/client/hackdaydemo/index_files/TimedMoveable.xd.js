/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


window[(typeof (djConfig)!="undefined"&&djConfig.scopeMap&&djConfig.scopeMap[0][1])||"dojo"]._xdResourceLoaded(function(_1,_2,_3){return {depends:[["provide","dojo.dnd.TimedMoveable"],["require","dojo.dnd.Moveable"]],defineResource:function(_4,_5,_6){if(!_4._hasResource["dojo.dnd.TimedMoveable"]){_4._hasResource["dojo.dnd.TimedMoveable"]=true;_4.provide("dojo.dnd.TimedMoveable");_4.require("dojo.dnd.Moveable");(function(){var _7=_4.dnd.Moveable.prototype.onMove;_4.declare("dojo.dnd.TimedMoveable",_4.dnd.Moveable,{timeout:40,constructor:function(_8,_9){if(!_9){_9={};}if(_9.timeout&&typeof _9.timeout=="number"&&_9.timeout>=0){this.timeout=_9.timeout;}},markupFactory:function(_a,_b){return new _4.dnd.TimedMoveable(_b,_a);},onMoveStop:function(_c){if(_c._timer){clearTimeout(_c._timer);_7.call(this,_c,_c._leftTop);}_4.dnd.Moveable.prototype.onMoveStop.apply(this,arguments);},onMove:function(_d,_e){_d._leftTop=_e;if(!_d._timer){var _f=this;_d._timer=setTimeout(function(){_d._timer=null;_7.call(_f,_d,_d._leftTop);},this.timeout);}}});})();}}};});