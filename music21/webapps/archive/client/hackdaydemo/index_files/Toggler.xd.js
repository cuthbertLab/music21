/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


window[(typeof (djConfig)!="undefined"&&djConfig.scopeMap&&djConfig.scopeMap[0][1])||"dojo"]._xdResourceLoaded(function(_1,_2,_3){return {depends:[["provide","dojo.fx.Toggler"]],defineResource:function(_4,_5,_6){if(!_4._hasResource["dojo.fx.Toggler"]){_4._hasResource["dojo.fx.Toggler"]=true;_4.provide("dojo.fx.Toggler");_4.declare("dojo.fx.Toggler",null,{node:null,showFunc:_4.fadeIn,hideFunc:_4.fadeOut,showDuration:200,hideDuration:200,constructor:function(_7){var _8=this;_4.mixin(_8,_7);_8.node=_7.node;_8._showArgs=_4.mixin({},_7);_8._showArgs.node=_8.node;_8._showArgs.duration=_8.showDuration;_8.showAnim=_8.showFunc(_8._showArgs);_8._hideArgs=_4.mixin({},_7);_8._hideArgs.node=_8.node;_8._hideArgs.duration=_8.hideDuration;_8.hideAnim=_8.hideFunc(_8._hideArgs);_4.connect(_8.showAnim,"beforeBegin",_4.hitch(_8.hideAnim,"stop",true));_4.connect(_8.hideAnim,"beforeBegin",_4.hitch(_8.showAnim,"stop",true));},show:function(_9){return this.showAnim.play(_9||0);},hide:function(_a){return this.hideAnim.play(_a||0);}});}}};});