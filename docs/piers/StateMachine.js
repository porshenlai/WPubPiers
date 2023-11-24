(function(Return){

	function Tab( e, c ){
		var self = this;
		self.C = c;
		self.E = e;
		e.style.display="none";
		e.addEventListener("transitionend",function(){
			if(e.style.top==="-100%") e.style.display="none";
		});
	}
	Tab.prototype.prepare=function(){
		var self = this, src = self.E.getAttribute( "src" );
		return src ? new Promise(function(or,oe){
			function lp( dom ){
				dom = dom.querySelector( "body" ).cloneNode(true);
				while( dom.firstChild ) self.E.appendChild( dom.firstChild );
				Piers.DOM.selectAll( self.E, "script" ).forEach( function(e){
					Piers.DOM.evalScript(e);
				} );
				self.E.removeAttribute( "src" );
				self.src = src;
				or();
			}
			Piers.U.create( src ).get().then( lp, function(){
				lp( (new DOMParser()).parseFromString(
					"<!DocType:html><html><body>Not found</body></html>",
					"text/html"
				) );
			} );
		}) : new Promise(function(or,oe){ or(); },console.log);
	};
	Tab.prototype.release=function(){
		var self = this;
		if( self.src ){ // TODO
		}
	};
	Tab.prototype.hide=function(){
		this.E.style.top = "-100%";
	};
	Tab.prototype.show=function( doc ){
		var self=this,e,u;
		if( self.C.__Lock__ && (new Date())-self.C.__Lock__ < 3000 )
			return setTimeout( function(){ self.show( doc ); }, 500 );
		self.C.__Lock__ = new Date();
		for( e in self.C ) if( self.C[e].hide ) self.C[e].hide();
		Piers._.ensurePromise( self.prepare() ).then( function(){
			var fe;
			if( self.Form )
				self.Form.set( doc||{} );
			else
			if( fe=self.E.querySelector("[PsTabForm]") ){
				Piers.require( 'Forms' ).then( function( forms ){
					self.Form=forms.build( fe, fe.getAttribute("PsTabForm") );
					self.Form.set( doc );
				}, console.log );
			}
		}, console.log );
		self.E.style.display = "block";
		setTimeout( function(){
			self.E.style.top="0";
			delete self.C.__Lock__;
		}, 10 );
	};
	Tab.prototype.sendEvent=function( name, args ){
		var self=this, x={};
		args = Object.assign( {
			Tab:self,
			getDoc:function( dv ){ return self.Form ? self.Form.get() : dv; },
			setDoc:function( doc, or=console.log, oe=console.log ){ if(self.Form) self.Form.set( doc ).then( or, oe ); }
		}, args||{} );
		x.Event = Piers.DOM.sendEvent( self.E, name, {"detail":args||{}} );
		return x.Event;
	};

	function SM( div, init ){
		var self=this;
		this.D = { St:undefined };
		this.Tabs = Piers.OBJ.reduce( div.querySelectorAll('[PsTab]'), function( r, v ){
			if( v.getAttribute ) r[ v.getAttribute("PsTab") ] = new Tab( v, r );
			return r;
		}, {} );
		div.__StateMachine__ = this;

		async function uievt( type, evt ){
			var tab = self.Tabs[self.D.St], args;
			args = tab.E.parentNode.parentNode.__DialogCB__;
			args = args ? {"__DialogCB__":args} : {};
			await tab.sendEvent( "trigger", Object.assign( args, {
				"Type":type, "Event":evt,
				"getA":function( an, dv, lv=false ){
					// ,X:tab.E
					var r = Piers.DOM.select( evt.target, "["+an+"]", mode=8 );
					r = [ r, r ? r.getAttribute(an) : dv ];
					return lv ? r : r[1];
				},
				"getV":function( vn, dv, lv=false ){
					// ,X:tab.E
					var r = Piers.DOM.select( evt.target, function(i){ return vn in i; }, mode=8 );
					r = [ r, r ? r[vn] : dv ];
					return lv ? r : r[1];
				}
			} ) ).complete();
		}
		div.addEventListener( "click", async function(evt){ uievt( "click", evt ); } );
		div.addEventListener( "change", async function(evt){ uievt( "change", evt ); } );
		if( init ) init.call(this);
	}

	Object.assign( SM.prototype, {
		"goto":function(st, args){
			if( st in this.Tabs ){
				this.__NxS__ = st;
				this.__NxA__ = args;
				this.__sync__();
			}else console.log("No such state");
		},
		"cancel":function(nt){ if(nt) this.__NxS__ = nt; else delete this.__NxS__; },
		"isNext":function(sn){ return this.__NxS__ === sn; },
		"getTab":function(){ return this.Tabs[this.D.St]; },
		"getForm":function(){ return this.getTab().Form; },
		"save":function(){
			return JSON.stringify(this.D);
		},
		"load":function(json){
			this.D = JSON.parse(json)
			this.__sync__();
		},
		"editPage":function( ){
			var self = this, url, hnd;
			try {
				url = Piers.U.abs(self.Tabs[self.D.St].src);
				url = /[a-z]*:\/\/[^\/]+\/(.*)/.exec(url)[1]
				hnd = window.open( Piers.Env.PierPath+"editor.html?path=docs:"+url+(document.baseURI ? ("&base="+document.baseURI) : "") );
				hnd.addEventListener("load",function(evt){
					(new Piers.M("dataset",self.D)).to(hnd).send();
				});
			}catch(x){ console.log("Exception:",x); }
		},
		"__sync__":async function(){
			var self=this, tab, args;

			if( !(self.__NxS__ && self.__NxS__ in self.Tabs) ) return;
			if( self.D.St && self.D.St in self.Tabs ) // flush latest state
				await self.Tabs[self.D.St].sendEvent( "tab-flush", {"NxS":self.__NxS__,"cancel":function(){
					self.__NxS__ = undefined;
				}} ).complete();
			if(!self.__NxS__) return;

			// prepare new state
			self.D.St = self.__NxS__;
			tab = self.Tabs[self.D.St];
			await Piers.createPromise( tab.prepare() );
			self.__NxS__ = undefined;

			// init new state
			args = tab.E.parentNode.parentNode.__DialogCB__;
			args = args ? {"__DialogCB__":args} : {};
			Object.assign( args, self.__NxA__||{} )
			await tab.sendEvent( "tab-init", args ).complete();
			tab.show();
		}
	});
	SM.findInstance = function( e ){
		return ( Piers.DOM.select(
			e || document.currentScript,
			function(i){ return "__StateMachine__" in i; },
			mode=8 ) || {} ).__StateMachine__;
	};

	SM.Dialog = Piers.OBJ.inherit(
		SM, function( tab, init ){
			var C = (this.E = tab).parentNode;
			SM.call(this,tab,init);
			C.style.top = "-100%";
		}, {
			show:function( did, args={} ){
				var self = this, C = self.E.parentNode;
				return new Promise( function(or,oe){
					if( C.style.top === "0%" ) return or();
					(function(e,s){
						var i; for(i=0;i<s.length;i++) s[i].style.display = s[i] == e ? "block" : "none";
					})( self.E, C.querySelectorAll("[PsDialog]") );
					C.style.top = "0%";
					if(did){
						args["__DialogCB__"] = C.__DialogCB__ = function(result,err){
							if( result ) or(result); else console.log(err);
							C.style.top = "-100%";
							C.__DialogCB__ = undefined;
						};
						self.goto( did, args );
					}
				} );
			},
			hide:function( ){
				var C = this.E.parentNode;
				if( C.__DialogCB__ ) C.__DialogCB__( undefined, "Cancelled" );
				else C.style.top = "-100%";
			}
		}
	);
	Return.setResult(SM);
})(Piers.__LIBS__.StateMachine);
