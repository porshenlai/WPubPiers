// <script type="javascript" PiersEntrance="Main.init" PiersXMods="Forms,UI" src="piers/init.js"></script>
(function(){
	var R,OBJ,DOM,DATE,Piers,s,i;
	function log(){ console.log(arguments); }
	function nf(){ }

	if( !("Promise" in window) ){ // {{{
		window.Promise = function(rt){
			var self = this;
			this.R = [];
			this.E = [];
			this.or = function( r ){
				if( Array.isArray(self.E) )
					self.R.forEach(function(f){ f(r); });
				self.R = r;
				self.E = true;
			};
			this.oe = function( e ){
				if( Array.isArray(self.E) )
					self.E.forEach(function(f){ f(e); });
				self.R = e;
				self.E = false;
			};
			rt(this.or,this.oe);
		};
		window.Promise.all = function(psa){
			return new Promise(function( or, oe ){
				(function w( a ){
					var i;
					for(i=0;i<a.length;i++)
						if( a[i] instanceof Promise )
							return a[i].then(function(r){ a[i]=r; w(a); },oe);
					or(a);
				})(psa);
			});
		};
		window.Promise.prototype.then = function( or, oe ){
			if(Array.isArray(this.E)){
				this.R.push(or);
				this.E.push(oe);
			}else
				this.E ? or(this.R) : oe(this.R);
		};
	}	// }}}

	if( !( "find" in Array.prototype ) ) // {{{
		Array.prototype.find = function( cb, self ){
			var x;
			for( x=0; x<this.length; x++ )
				if( cb.call(self,this[x],x,this) )
					return this[x];
		};
	// }}}

	if( !( "assign" in Object ) ) // {{{
		Object.assign = function(){
			var b,i,j;
			b = arguments[0];
			for( i=1; i<arguments.length; i++ ){
				for( j in arguments[i] )
					b[j] = arguments[i][j];
			}
			return b;
		};
	// }}}

	if( !( "keys" in Object ) ) // {{{
		Object.keys = function(){
			var r=[];
			for(i in r)
				r.push(i);
			return r;
		};
	// }}}

	if( !FileReader.prototype.readAsBinaryString ) // {{{
    	FileReader.prototype.readAsBinaryString = function( fileData ){
			var pt=this,binary="",reader;
			reader = new FileReader();
			reader.onload = function( e ){
				var bytes,length,evt,i;
				bytes = new Uint8Array( reader.result );
				length = bytes.byteLength;
				for( i=0; i<length; i++ )
					binary += String.fromCharCode(bytes[i]);
				pt.content = pt.IEResult = binary;
				Piers.DOM.sendEvent(pt,"load");
    		};
			reader.readAsArrayBuffer(fileData);
		};
	// }}}

	R={	// {{{
		"toArray":function( a, packer ){
			if(!packer)
				packer = function(n,v){ return [n,v]; };
			var i,r=[];
			if( undefined === a.length )
				for( i in a ) r.push( packer(i,a[i]) );
			else
				for( i=0,r=[]; i<a.length; i++ ) r.push(a[i]);
			return r;
		},
		"uniq":function( a ){
			return a.filter(function(r,i){ return i===a.indexOf(r); });
		},
		"importJS":function( js, ASYNC=true ){
			return "string" === typeof(js) ? new Promise( function( or, oe ){
				var e = DOM.create({
					"T": "script",
					"E": {
						"load":function(){
							e.parentNode.removeChild(e);
							if(ASYNC) or(this);
						},
						"error":function(e){ e.parentNode.removeChild(e); oe(e); }
					},
					"A": {"src":js}
				});
				e.__onReady__ = or;
				document.head.appendChild( e );
			} ) : document.currentScript.__onReady__( js )
		},
		"loadFile":function( ct, mul ){
			return new Promise( function( or, oe ){
				var e = DOM.create({
					"T":"input", "V":{ "multiple":mul },
					"A":{ "type":"file", "accept":ct||"*/*" },
					"S":{ "position":"absolute", "top":"100%" },
					"E":{ "error":oe, "change":function(evt){
						or( R.toArray( this.files ) );
						if( this.parentNode ) this.parentNode.removeChild( this );
					} }
				});
				document.body.appendChild(e);
				e.click();
				setTimeout( function( ){
					if( e.parentNode ) e.parentNode.removeChild( e );
				}, 3000 );
			} );
		},
		"call":function( f, a ){
			switch( typeof( f ) ){
			case 'function': return f.apply( window, a );
			case 'string': return OBJ.apply( window, f, a );
			}
			if( Array.isArray( f ) )
				return f[1].apply( f[0], a );
		},
		"ensurePromise":function( p ){
			return p instanceof Promise ? p : new Promise( function(or,oe){ or(p); } );
		},
		"flushPromise":function( ps, or=nf, oe=nf ){ ps.then(or,oe); },
		"trace":function( e ){
			console.trace( );
			if( Piers.Env && Piers.Env.Mobile )
				return alert( "DEBUG"+e.m );
		},
		"throw":function( msg ){
			console.trace( )
			throw new Piers.Error(msg);
		},
		"log":log, "nf": nf
	};	// }}}

	OBJ={ // OBJECT ROUTINES {{{
		"assign": Object.assign,
		"keys": Object.keys,
		"find": function( o, vf ){ for( k in o ) if( vf(o[k],k) ) return k; },
		"createMethod":function( o, f ){
			return function(){ f.apply(o,arguments); };
		},
		"reduce":function( o, cb, i ){
			for( k in o )
				i = cb( i, o[k], k, o );
			return i;
		},
		"shadowCopy":function( o ){
			return this.assign( {}, o );
		},
		"deepCopy":function( o ){
			return JSON.parse( JSON.stringify(o) );
		},
		"isEmpty":function( o ){
			return Object.keys( o ).length > 0;
		},
		"inherit":function( base, init, protos={} ){
			init.prototype = Object.create( base.prototype, {
				constructor:{
					value:init,
					enumerable:false,
					writable:true,
					configurable:true
				}
			} );
			for( an in protos )
				init.prototype[an] = protos[an];
			return init;
		},
		"apply":function( o, p, a ){
			a = a || [];
			if( "string" === typeof(p) ) p = p.split(/\./);
			return p.reduce( function( r, i ){ return (o=r)[i]; }, o ).apply( o, a );
		},
		"get":function( o, p, dv ){
			if("string"===typeof(p)) p = p.split(/\./);
			try{ return p.reduce(function(r,i){ return r[i]; },o); }catch(e){ return dv; }
		},
		"put":function( o, p, v ){
			p = "string" === typeof(p) ? p.split(/\./) : this.assign( [], p );
			if(p){
				var n = p.pop();
				o = p.reduce( function( r, i ){
					if( !r[i] ) r[i]={}; return r[i];
				}, o );
				o[n] = v;
			}
		},
		"push":function( o, n, v ){
			if( Array.isArray(o[n]) )
				o[n].push( v );
			else o[n] = [v];
		},
		"join":function( o, n ){
			var i;
			function gt( o ){
				return "object" === typeof(o) ?
					Array.isArray(o) ? "a" : "o" : "v";
			}
			if(!n) return o;
			for( i in n ){
				if( i === undefined ) continue;
				switch( gt(o[i])+gt(n[i]) ){
				case "oo":
					if( o[i] && n[i] ) for( i in n ) {
						if( i === undefined ) continue;
						this.join( o[i], n[i] );
					}	break;
				case "aa":
					o[i] = o[i].concat( n[i] ); break;
				default:
					o[i] = n[i]; break;
				}
			}
			return o;
		},
		"mask":function( o, m ){
			r = {}
			if( m ) for( i in m ) switch( typeof(m[i]) ){
			case undefined :
				continue;
			case "object" :
				if( typeof( o[i] ) === "object" )
					r[i] = this.mask( o[i], m[i] );
				break;
			default:
				if( i in m ) r[i] = o[i];
				break;
			}
			return r;
		},
		"toQueryString":function( qo ){
			return R.toArray( qo ).reduce( function( r, i ){
				return r + (r?"&":"") + i[0] + ( i[1]===true ? "" : ("="+encodeURIComponent(i[1])) );
			},"");
		},
		"fromQueryString":function( qs ){
			return qs.replace( /^\?/, '' ).split( /&/ ).reduce( function( r, i ){
				if( i=/^([^=]+)(=(.*)){0,1}/.exec(i) )
					r[decodeURIComponent(i[1])] = i[2]
					? decodeURIComponent(i[3]) : true;
				return r;
			}, {} );
		},
		"filter":function( obj, key ){
			var k,i,r={},kf;
			kf = 'function' == typeof(key) ? key : function(v){ return v.indexOf(key)>=0; };
			for(k in obj){
				if( kf( obj[k], k ) ){
					r[k] = obj[k];
				}else if( "object" === typeof(obj[k]) ){
					i = OBJ.filter( obj[k], key );
					if(Object.keys(i).length>0) r[k] = i;
				}
			}
			return r;
		}
	}; // }}}

	var SELPAIR={ // {{{
		"SEP":"-",
		"decodeKV":function( kvs ){
			return kvs.split("\r");
		},
		"decodeKVR":function( r, kvs ){
			kvs = SELPAIR.decodeKV( kvs );
			r[kvs[1]||kvs[0]] = kvs[0];
			return r;
		},
		"__so":function(e,d,dv){
			if( Array.isArray(d) )
				d = d.reduce(SELPAIR.decodeKVR,{});
			while( e.firstChild ) e.removeChild( e.firstChild );
			for( k in d )
				e.appendChild( Piers.DOM.create(
					(function(l,v){
						return { "T":"option", "C":[l], "A":{"value":v} };
					})( k, (function(v){
						if( "object" === typeof(v) && undefined in v )
							return v[undefined];
						return v;
					})(d[k]) )
				) );
			if(dv) e.value = dv;
		}, // __opts
		"__sc":function( evt, dv=[] ){
			var pe = this.parentNode,rv;
			while( this.nextSibling ) pe.removeChild( this.nextSibling );
			if( this.__Doc__ && this.value in this.__Doc__ ){
				SELPAIR.__csp( pe, this.__Doc__[this.value], dv );
			}
			rv = []
			Piers.DOM.selectAll( pe, "select" ).forEach( function( e ){ rv.push(e.value); } );
			if(evt) evt.stopPropagation();
			pe.updateValue( rv.join(SELPAIR.SEP) );
		}, // __sc
		"__csp":function( e, d, dv=[] ){
			var doc = {}, dd=[], se = Piers.DOM.create({"T":"select"}), k, kv;
			if( !Array.isArray(d) ){
				for( k in d ){
					kv = SELPAIR.decodeKV( k );
					if( "object" === typeof(d[k]) ) doc[kv[0]] = d[k];
					dd.push(k);
				}
				if( Object.keys(doc) ) se.__Doc__ = doc;
				SELPAIR.__so(se,dd,dv.shift());
			}else this.__so(se, d, dv.shift());
			se.addEventListener( "change", SELPAIR.__sc );
			e.appendChild(se);
			SELPAIR.__sc.call(se,undefined,dv);
		}, // __csp
		"init":function( e, d, dv, sep ){
			if( "SELECT" === e.tagName || "DATALIST" === e.tagName )
				return SELPAIR.__so( e, d, dv );
			e.updateValue = function( val ){
				if( e.value !== val ){
					e.value = val;
					while( e.firstChild ) e.removeChild( e.firstChild );
					SELPAIR.__csp( e, d, val.split(SELPAIR.SEP) );
					Piers.DOM.sendEvent( e, "change", {"bubbles":true} );
				}
			};
			while( e.firstChild ) e.removeChild( e.firstChild );
			SELPAIR.__csp( e, d, dv );
		} // init
	}; // }}}

	DOM={ //	DOM : Data Object Model {{{
		"select":function( root, qs, mode=2 ){
			var i;
			switch(mode){
			case 2:
				return root.querySelector( qs );
			case 6:
				vf = 'function'===typeof(qs) ? qs : function(i){ return i.matches(qs); };
				for( i=root; i; i=i.nextSibling)
					if( i.nodeType===1 && vf(i) )
						return i;
			case 8:
				vf = 'function'===typeof(qs) ? qs : function(i){ return i.matches(qs); };
				for( i=root; i&&i.parentNode; i=i.parentNode )
					if( i.nodeType===1 && vf(i) )
						return i;
			}
		},
		"selectAll":function( root, qs, mode=2 ){
			var r=[],i,s,dir;
			switch(mode){
			case 2:
				s = root.querySelectorAll( qs );
				for( i=0; i<s.length; i++ ) r.push(s[i]);
				break;
			case 6:
				vf = 'function'===typeof(qs) ? qs : function(i){ return i.matches(qs); };
				for( i=root; i; i=i.nextSibling )
					if( i.nodeType===1 && vf(i) )
						r.push(i);
				break;
			case 8:
				vf = 'function'===typeof(qs) ? qs : function(i){ return i.matches(qs); };
				for( i=root; i&&i.parentNode; i=i.parentNode )
					if( i.nodeType===1 && vf(i) )
						r.push(i);
				break;
			}
			return r;
		},
		"find":function( e, cf, axis="parentNode", stop ){
			console.trace("Warning: replaced by DOM.select( e, qs, mode=8 )");
			if("X" in cf) stop = cf.X; 
			var v=cf;
			if("A" in cf){ cf=function(e){ try{ return e.hasAttribute(v.A); }catch(x){} }; }
			else if("V" in cf){ cf=function(e){ try{ return v.V in e; }catch(x){} }; }
			if(stop) while(e && e!=stop){ if( cf(e) ) return e; e = e[axis]; }
			else while(e){ if( cf(e) ) return e; e = e[axis]; }
		},
		"forEach":function(root,qs,cb){
			console.trace("Warning: replaced by DOM.selectAll( root, qs ).forEach( cb )");
			var i,s,r;
			if( !cb ){ cb = qs; qs = undefined; }
			if( !root ) root = document;
			if( !root.nodeType ){ qs = root; root = document }
			try{
				if( qs ){
					s = root.querySelectorAll(qs) || [];
					for(i=0;i<s.length;i++){ r = cb(s[i],i,s); if( r ) return r; }
				}else for( s=root.firstChild; s; s=s.nextSibling ){ r = cb(s,i,root); if( r !== undefined ) return r; }
			}catch(e){ }
			return this;
		},
		"reduce":function(root,qs,cb,rv){
			console.trace("Warning: replaced by DOM.selectAll( root, qs ).reduce( cb, rv )");
			var i,s,r;
			if( !cb ){ cb = qs; qs = undefined; }
			if( !root ) root = document;
			if( !root.nodeType ){ qs = root; root = document }
			try{
				if( qs ){
					s = root.querySelectorAll(qs) || [];
					for( i=0; i<s.length; i++ ) rv = cb( rv, s[i], i, s );
				}else for( s=root.firstChild; s; s=s.nextSibling ) rv = cb( rv, s, i, root );
				return rv;
			}catch(e){ }
			return this;
		},
		"getClasses":function( e ){
			return (e.getAttribute("class")||"").split(/\s+/).filter(function(n){ return n; });
		},
		"setClasses":function( e, cs ){
			if(cs) e.setAttribute("class",cs.toString().replace(/,/g,' '));
			else e.removeAttribute("class");
		},
		"addClass":function( e, c ){
			var cs = this.getClasses(e).filter(function(i){ return i!==c; });
			cs.push( c ); this.setClasses( e, cs );
		},
		"removeClass":function( e, c ){
			this.setClasses( e, this.getClasses(e).filter(function(i){ return i!==c; }) )
		},
		"updateClass":function( e, n, r ){
			var cs = this.getClasses( e );
			if(r) cs = cs.filter(function(n){ return !r.test(n); });
			if(n) cs.push(n); this.setClasses( e, cs );
			return this;
		},
		"updateText":function( e, t ){
			while(e.firstChild) e.removeChild(e.firstChild);
			e.appendChild(document.createTextNode(t));
			return this;
		},
		"createOption":function( l, v ){
			var o=DOM.create({ "T":"option","C":[l] });
			if(v) o.setAttribute("value",v);
			return o;
		},
		"createButton":function( l, onclick ){
			return DOM.create({ "T":"button", "E":{ "click":onclick }, "C":[l] });
		},
		"createPieChart":function( list, e ){
			var i,t,c,n,s = [];
			t = 0; for(i in list) t += list[i];
			c = 0; for(i in list){
				n = c+list[i];
				s.push(i+" "+Math.floor(c*360/t)+"deg "+Math.floor(n*360/t)+"deg");
				c = n;
			}
			if(!e) e = document.createElement("div");
			e.style.backgroundImage="conic-gradient("+s+")";
			return e;
		},
		"create":function( pf ){
			// pf={"T":"","Q":"qs","A":{"border":"1"},"S":{"width":"30%"},"E":{"click":cb,...},"C":["Text",{...}]}
			var self=this,e,i;
			if( "T" in pf ) e = document.createElement(pf.T);
			if( "Q" in pf ) e = "nodeType" in pf.Q ? pf.Q : document.querySelector(pf.Q);
			if( "A" in pf ) for( i in pf.A ) e.setAttribute(i,pf.A[i]);
			if( "S" in pf ) for( i in pf.S ) e.style[i] = pf.S[i];
			if( "E" in pf ) for( i in pf.E ) e.addEventListener(i,pf.E[i]);
			if( "V" in pf ) for( i in pf.V ) e[i] = pf.V[i];
			if( "C" in pf ) pf.C.forEach(function(i){
				e.appendChild( "string" == typeof(i) ? document.createTextNode(i) : self.create(i) );
			});
			return e;
		},
		"bind":function( en, eh, e=undefined ){
			try {
				e = e||document.currentScript.parentNode;
				e.addEventListener( en, function(evt){
					e.setAttribute("PsActive","en");
					return new Promise(function(or,oe){
						R.ensurePromise( eh.call(e,evt) ).then(function(r){
							e.removeAttribute("EHState","Active");
							or(r);
						},oe);
					});
				} );
			}catch(e){ console.log("EX:Piers.DOM.bind:"+e.toString()); }
		},
		"clear":function( e ){
			while( e.firstChild ) e.removeChild( e.firstChild );
		},
		"evalScript":function( se ){
			var p,x,s;
			p = se.parentNode;
			x = se.nextSibling;
			s = DOM.create({"T":"script","V":{"text":se.text}});
			p.removeChild(se);
			p.insertBefore(s,x);
		},
		"sendEvent":function( to, name, args ){
			var x = {};
			args = Object.assign({
				"block":function( cb ){ return ( x.Block=Piers.createPromise() ); },
				"flush":function( nodefault=false ){
					x.Event.stopPropagation();
					if( nodefault ) x.Event.preventDefault();
				}
			}, args||{} );
			x.Event = args ? new CustomEvent(name,args) : new Event(name);
			x.Event.complete = function( ){ return x.Block ? x.Block : new Promise(function(or,oe){ or(); }); };
			to.dispatchEvent( x.Event );
			return x.Event;
		},
		"isContained":function( p, c ){ for(;c&&p!==c;c=c.parentNode); return !!c; },
		"isSibling":function( a, b ){ return a.parentNode === b.parentNode; },
		"initSelect":SELPAIR.init
	}; //	}}}

	DATE={ // {{{
		"toString":function(y,m,d){
			if(!(y&&m&&d)){
				var t = new Date();
				if(d===undefined){
					if(m===undefined){
						d = y===undefined ? t.getDate() : y ;
						m = t.getMonth();
					}else{
						d = m;
						m = y;
					}
					y = t.getFullYear();
				}
			}
			return new Date(Date.UTC(y,m,d)).toISOString().replace(/T.*/,'');
		}
	}; // }}}

//	F : Future {{{
//	new F()
//	.setResult(value)
//	.setException(exception)
//	.get()
	function F(){ var T = this; this.P = new Promise(function(or,oe){ T.ORE=[or,oe]; }); }
	F.prototype.get=function(){ return this.P; };
	F.prototype.setResult=function(val){ if(this.ORE) this.ORE[0](val); this.ORE=undefined; }
	F.prototype.setException=function(val){ if(this.ORE) this.ORE[1](val); this.ORE=undefined; }
//	}}}

//	M : Message {{{
//	M.reg("NAME",function(arg,evt){...});
//	new M("NAME",{"arg":1}).send();
//	new M("NAME",{"arg":2}).origin(ORIGIN_WINDOW).to(TARGET_WINDOW).send();
	function M(n,a){
		this.N=n;
		this.A=a;
		this.W=parent;
		this.O="*";
	}
	M.prototype.to=function(w){ this.W=w||this.W;return this; };
	M.prototype.origin=function(o){ this.O=o||this.O;return this; };
	M.prototype.send=function(listener){
		var This=this,msg={"N":this.N,"A":this.A};
		if(listener===true) return this.W.postMessage(msg,this.O);
		if(!listener) listener=function(){};
		return new Promise(function(or,oe){
			Piers.M.reg(
				msg.R="Piers."+(new Date().getTime().toString(36))+"."+Math.random(),
				function(a){
					return a.progress?listener(a.progress):a.ready?or(a.ready):oe(a.error);
				},false
			);
			This.W.postMessage(msg,This.O);
		});
	};
	var __Handlers__={}
	M.reg=function(n,h,once){
		__Handlers__[n]=h; h.Once=once;
		return this;
	};
	window.addEventListener("message",(function(evt){
		var d=evt.data,h;
		if(!(h=__Handlers__[d.N])){
			if(parent){
				(new Piers.M(d.N,d.A)).send().then(function(doc){
					if(d.R)
						new Piers.M(d.R,{"ready":doc||{},"LastOne":true}).to(evt.source).send(true);
				},console.log);
			}
			return;
		}
		if(h.Once||d.LastOne) delete __Handlers__[d.N];
		h=h(d.A,evt,function(progress){
			new Piers.M(d.R,{"progress":progress}).to(evt.source).send(true);
		});
		if(h && h.then){
			h.then(function(doc){
				if(d.R)
					new Piers.M(d.R,{"ready":doc||{},"LastOne":true})
					.to(evt.source).send(true);
			},function(err){
				if(d.R)
					new Piers.M(d.R,{"error":err||"ERROR","LastOne":true})
					.to(evt.source).send(true);
			});
		}else if(d.R)
			new Piers.M(d.R,{"ready":h||{},"LastOne":true}).to(evt.source).send(true);
	}));
// M }}}

//	U : URL {{{
//	new URL( URL_STRING )
//	.addQS( NAME, VALUE ) :> THIS
//	.addHeader( NAME, VALUE ) :> THIS
//	.toString() :> URL_STRING
//	.on("progress",(p)=>...) :> THIS
//	.get(DEFAULT).then ...
//	.put(U.Data,DEFAULT).then ...
//	.post(U.Data,DEFAULT).then ...
//	.delete().then ...
	function U(s){
		var i;
		this.Headers={};
		if(/^[a-zA-Z]+:\/\//.test(s))
			Object.assign(this,U.parse(s));
		else{
			this.proto= location.protocol;
			this.hname= location.hostname;
			this.port = location.port;
			if(s[0]!=='/'){
				this.relative = s.replace(/\?.*$/,'');
				s = location.pathname.replace(/\/[^\/]*/,'')+"/"+s;
			}
			i=/^(\/[^\?]+)?(\?.*)?$/.exec(s);
			this.pathname = i[1];
			this.search = i[2]||"";
		}
		this.search = this.search.replace(/^\?/,'');
		this.QS = OBJ.fromQueryString(this.search);
	};
	U.prototype.toString=function(){
		var r = (this.search ? "?" : "")+this.search;
		r = this.relative ? this.relative+r:
			this.proto+"//"+this.hname+(this.port?(":"+this.port):"")+this.pathname+r;
		return r;
	};
	U.prototype.addQS=function(n,v){
		if(v===""||v) this.QS[n]=v; else delete this.QS[n];
		v = OBJ.toQueryString( this.QS );
		this.search = v ? ("?"+v) : "";
		return this;
	};
	U.prototype.addHeader=function(n,v){
		if(v===""||v) this.Headers[n]=v; else delete this.Headers[n];
		return this;
	};
	U.prototype._progress_ = nf;
	U.prototype.on = function(n,cb){ U["_"+n+"_"]=cb };
	U.prototype._cw = function(or,oe,dft){
		var self=this,i,r=new XMLHttpRequest();
		r.addEventListener(
			"progress",
			function(evt){
				self._progress_(evt.lengthComputable?(evt.loaded/evt.total):-1);
			}
		);
		r.addEventListener( "load", self.__AutoDecode__ ? function(){
			if( r.status !== 200 )
				dft===undefined ? oe("ERROR") : or(dft) ;
			else (new U.Data(r.response)).decode().then(or,oe);
		} : function(){
			r.status !== 200 ? dft ? or(dft) : oe("Not found")
			: or(new U.Data(r.response));
		} );
		r.addEventListener("abort",function(){ oe("aborted"); });
		r.addEventListener("error",function(e){ oe(e); });
		return r;
	};
	U.prototype.get = function(a,dft){
		var self = this;
		if(a) for(n in a) this.addQS(n,a[n])
		return new Promise(function(or,oe){
			var r=self._cw(or,oe,dft);
			r.open("GET",self.toString(),true);
			for(i in self.Headers)
				r.setRequestHeader(i,self.Headers[i]);
			r.responseType="blob";
			r.send();
		});
	};
	U.prototype.put = function(d,dft){
		var self=this;
		if(!(bb instanceof U.Data)) bb = new U.Data(bb);
		return new Promise(function(or,oe){
			var r=self._cw(or,oe,dft);
			r.open("PUT",self.toString(),true);
			for(i in self.Headers) r.setRequestHeader(i,self.Headers[i]);
			r.responseType="blob";
			r.setRequestHeader('Content-Type',bb.B.type);
			r.send(bb.B);
		});
	};
	U.prototype.post = function(bb,dft){
		var self = this;
		if(!(bb instanceof U.Data)) bb = new U.Data(bb);
		return new Promise(function(or,oe){
			var r=self._cw(or,oe,dft);
			r.open("POST",self.toString(),true);
			for(i in self.Headers)
				r.setRequestHeader(i,self.Headers[i]);
			r.responseType="blob";
			r.setRequestHeader('Content-Type',bb.B.type);
			r.send(bb.B);
		});
	};
	U.prototype.delete = function(){
		var self=this;
		return new Promise(function(or,oe){
			self._cw(or,oe).open("DELETE",self.toString(),true).send()
		});
	};
	U.create = function( url, auto=true ){
		var url = new U( url );
		url.__AutoDecode__ = auto;
		return url;
	};
	U.pathjoin = function( parts, sep="/" ){
		return parts.join(sep).replace( new RegExp(sep+'{1,}','g'), sep);
	};
	U.abs = function( url ){
		return url.indexOf("://") < 0
		? U.pathjoin([ (url[0]!=="/"?/([htps]+:\/\/[^\?]+\/).*/:/([htps]+:\/\/[^\/]+).*/).exec(U.abs(document.baseURI)||location.href)[1], url ]).replace(":/","://")
		: url ;
	};
	U.toRelative = function( url ){
		var bu = (url[0]!=="/"?/([htps]+:\/\/[^\?]+\/).*/:/([htps]+:\/\/[^\/]+).*/).exec(U.abs(document.baseURI)||location.href)[1];
		return url.replace(bu,'');
	};
	U.parse = function( u ){
		var i=/^([a-zA-Z]+:)\/\/([^\/:\?]+)?(:\d+)?(\/[^\?]+)?(\?.*)?$/.exec(u),r;
		if(!i) throw new Piers.Error("Bad Args","failed to parse URL input:"+u);
		return {
			"proto":i[1],
			"hname":i[2],
			"port":i[3] ? parseInt(i[3].substr(1)) : undefined,
			"pathname":i[4],
			"search":i[5]||""
		};
	};
// U }}}
	U.Data=function( b, t ){ // {{{
		t = t||"application/json";
		if( !(b instanceof Blob) ){
			if( "object" === typeof(b) ){ b = JSON.stringify(b); t = "application/json"; }
			b = new Blob([b],{"type":(t||"text/plain")+";charset=utf8"});
		}
		this.B = b;
	};
	U.Data.fromObject=function(o){
		return new Promise(function(or,oe){
			or(new Blob(o));
		});
	};
	U.Data.fromDataURL=function(s){
		return new Promise(function(or,oe){
			fetch(s).then(function(res){
				res.blob().then(function(blob){ or(new U.Data(blob)); },oe);
			},oe);
		});
	};
	U.Data.fromUpload=function(ct,mul){
		return new Promise(function(or,oe){
			R.loadFile(ct,mul).then(function(s){
				or(s.map(function(f){ return new U.Data(f); }));
			},oe);
		});
	};
	U.Data.prototype.decode=function(){
		var self=this;
		return new Promise(function(or,oe){
			var r = new FileReader(),type=self.getType();
			r.addEventListener("error",oe);
			switch( type ){
			case "application/json":
				r.addEventListener("load",function(e){
					or( JSON.parse(e.target.result) );
				});
				r.readAsText(self.B); break;
			case "image/jpeg": case "image/png": case "image/gif":
				self.getDataURL().then(or,oe); break;
			default:
				r.addEventListener("load",function(e){
					switch( type ){
					case "text/html": case "image/svg+xml":
						or( (new DOMParser()).parseFromString(e.target.result,type) ); break;
					default:
						or( e.target.result ); break;
					}
				});
				r.readAsText(self.B); break;
			}
		});
	};
	U.Data.prototype.getText=function(){
		return this.B.text();
	};
	U.Data.prototype.getType=function(){
		return this.B.type.replace(/;.*/,'');
	};
	U.Data.prototype.getDataURL=function(){
		var self = this;
		return new Promise(function(or,oe){
			try{
				var r = new FileReader();
				r.addEventListener("load",function(e){
					or( e.target.result );
				});
				r.addEventListener("error",oe);
				r.readAsDataURL(self.B);
			}catch(e){
				or( "data:"+self.B.type+";base64,"+btoa(self.B.data) );
			}
		});
	};
	U.Data.prototype.getURL=function(){
		var b=this.B;
		return new Promise(function(or,oe){ or(URL.createObjectURL(b)); });
	};
	U.Data.prototype.saveAs=function(n){
		var self=this, e;
		document.body.appendChild( e=DOM.create({
			"T":"A",
			"A":{"target":"_blank","download":n||"download"},
			"S":{"left":"-100%"}
		}) );
		return new Promise(function(or,oe){
			self.getDataURL().then(function(href){
				e.setAttribute("href",href);
				e.click();
				setTimeout(function(){ document.body.removeChild(e); },500);
				or("OK");
			},oe);
		});
	};
// }}}

	Piers=window.Piers={
		"__LIBS__":{},
		"require":function(u){
			var e,r;
			if( this.__LIBS__[u] ) return this.__LIBS__[u].get();
			else this.__LIBS__[u] = new this.F();
			this._.importJS(this.Env.PierPath+u+".js").then(nf,function(e){
				Piers.__LIBS__[u].setException(e);
			});
			return this.__LIBS__[u].get();
		},
		"Env":{
			"Args" : OBJ.fromQueryString( (window.location.search||'?').substr(1) ),
			"Mobile" : /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
			"OnTop" : window.self === window.top,
			"PierPath" : "",
			"PierArgs" : {}
		},

		"Error":OBJ.inherit( Error, function( name, msg ){
			Error.call(this,name);
			this.info = { "N":name, "D":msg };
		}, {
			"resolve": function( ){
				console.log( this.stack );
				return this.info;
			}
		} ),

		"createPromise":function( rv ){
			var r,x={};
			if( rv && rv.then )
				return new Promise(function(or,oe){ rv.then(or,oe); });
			r = new Promise(function(or,oe){ x.or=or; x.oe=oe; });
			r.setReady=function(r){ x.result={"R":r}; x.or(r); };
			r.setError=function(e){ x.result={"E":e}; x.oe(e); };
			r.flush=function(){ if(!x.result){ this.setReady(); x.result=undefined; } };
			if( rv ) r.setReady(r);
			return r;
		},

		"OBJ":OBJ,"DOM":DOM,"DATE":DATE,
		"F":F,	// Future
		"M":M,	// Message
		"U":U,	// URL
		"_":R,	// General Routines
		"nf":nf
	};

	if( (s=document.currentScript) && (i=/(.*)init.js/.exec(s.getAttribute("src")||""))
	){
		Piers.Env.PierPath = i[1];
		Piers.Env.PierArgs = R.toArray( s.attributes ).reduce( function(r,i){
			if(i.value) r[i.name] = i.value;
			return r;
		}, {} );
		Piers.Env.Entrance = s.getAttribute( "PierEntrance" ).split( "." );
		Piers.Env.XMods = s.getAttribute( "PierXMods" );
		Piers.Env.XMods = Piers.Env.XMods ? Piers.Env.XMods.split( "," ) : [];
		s.parentNode.appendChild( DOM.create({"T":"link","A":{"rel":"stylesheet","href":U.pathjoin([Piers.Env.PierPath,"style.css"])}}) );
	}

	window.addEventListener( "error", function(evt){
		R.trace({
			"c":"error",
			"m":"["+evt.filename+":"+evt.lineno+"."+evt.colno+"]\n"+evt.message
		});
	} );
	function doInit(){
		document.removeEventListener( "DOMContentLoaded", doInit );
		try {
			function start(){
				if( Piers.Env.Entrance )
					Piers.OBJ.apply( window, Piers.Env.Entrance );
			}
			if( Piers.Env.XMods )
				Promise.all( Piers.Env.XMods.map(function(v){
					return Piers.require(v);
				}) ).then( function(s){
					try{
						s.forEach(function(l,x){
							Piers[Piers.Env.XMods[x]] = l;
						});
						start();
					}catch(e){
						console.trace( e );
						alert( e instanceof Piers.Error ? JSON.stringify(e.resolve(),null,2) : e.toString() );
					}
				}, console.trace );
			else start();
		} catch(e) {
			console.trace( e );
			alert( e instanceof Piers.Error ? JSON.stringify(e.resolve(),null,2) : e.toString() );
		}
	}
	if( document.readyState==="complete" ||
		document.readyState==="loaded" ||
		document.readyState==="interactive" )
		doInit();
	else document.addEventListener( "DOMContentLoaded", doInit );
})();
