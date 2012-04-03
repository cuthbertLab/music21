/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


window[(typeof (djConfig)!="undefined"&&djConfig.scopeMap&&djConfig.scopeMap[0][1])||"dojo"]._xdResourceLoaded(function(_1,_2,_3){return {depends:[["provide","dijit._DialogMixin"]],defineResource:function(_4,_5,_6){if(!_4._hasResource["dijit._DialogMixin"]){_4._hasResource["dijit._DialogMixin"]=true;_4.provide("dijit._DialogMixin");_4.declare("dijit._DialogMixin",null,{attributeMap:_5._Widget.prototype.attributeMap,execute:function(_7){},onCancel:function(){},onExecute:function(){},_onSubmit:function(){this.onExecute();this.execute(this.attr("value"));},_getFocusItems:function(_8){var _9=_5._getTabNavigable(_4.byId(_8));this._firstFocusItem=_9.lowest||_9.first||_8;this._lastFocusItem=_9.last||_9.highest||this._firstFocusItem;if(_4.isMoz&&this._firstFocusItem.tagName.toLowerCase()=="input"&&_4.getNodeProp(this._firstFocusItem,"type").toLowerCase()=="file"){_4.attr(_8,"tabIndex","0");this._firstFocusItem=_8;}}});}}};});