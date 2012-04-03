/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


window[(typeof (djConfig)!="undefined"&&djConfig.scopeMap&&djConfig.scopeMap[0][1])||"dojo"]._xdResourceLoaded(function(_1,_2,_3){return {depends:[["provide","dijit._Contained"]],defineResource:function(_4,_5,_6){if(!_4._hasResource["dijit._Contained"]){_4._hasResource["dijit._Contained"]=true;_4.provide("dijit._Contained");_4.declare("dijit._Contained",null,{getParent:function(){var _7=_5.getEnclosingWidget(this.domNode.parentNode);return _7&&_7.isContainer?_7:null;},_getSibling:function(_8){var _9=this.domNode;do{_9=_9[_8+"Sibling"];}while(_9&&_9.nodeType!=1);return _9&&_5.byNode(_9);},getPreviousSibling:function(){return this._getSibling("previous");},getNextSibling:function(){return this._getSibling("next");},getIndexInParent:function(){var p=this.getParent();if(!p||!p.getIndexOfChild){return -1;}return p.getIndexOfChild(this);}});}}};});