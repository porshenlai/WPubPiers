(function(Return){
	function Generic( e, t, d, tagname="an" )
	{
		this.E = e;	// DOM element to apply actions
		this.D = d; // dataRef(d)=TYPE(t)
		this.T = t.shift();
		try{ this.O = t.shift(); }catch(x){ this.O = ""; }
	}
	Generic.prototype.get=function()
	{
		var e = this.E;
		switch(this.T){
		case "Text":
			return (this.E.firstChild||{}).nodeValue||"";
		case "Src":
			this.O = "src";
		case "Class":
		case "Attribute":
			return this.E.getAttribute(this.O||"class")||"";
		case "Val": case "Choose":
		case "Value":
			return this.E[this.O||"value"]||"";
		case "Style":
			return this.E.style[this.O||"display"]||"";
		case "Radio":
			return Piers.DOM.selectAll( this.E, '[type="radio"]' ).forEach( function( oe ){
				if( oe.checked )
					return oe.getAttribute("value");
			} );
		case "Checkbox":
			return Piers.DOM.selectAll( this.E, '[type="checkbox"]' ).reduce( function( rv, oe ){
				if( oe.checked )
					rv.push( oe.getAttribute("value") );
				return rv;
			}, [] );
		}
	};
	Generic.prototype.clear=function(){
		switch( this.T ){
			case "Value": case "value":
				this.E[this.O||"value"] = ""; break;
			case "Text": case "text":
				Piers.DOM.updateText( this.E, "" ); break;
			case "Attribute":
				this.E.removeAttribute( this.O ); break;
			case "Style":
				delete this.E.style[this.O||"display"]; break;
		}
	};
	Generic.prototype.set=function(d)
	{
		var self=this;
		return new Promise(function(or,oe){
			switch(self.T){
			case "T": 
			case "Text": case "text":
				Piers.DOM.updateText( self.E, d === undefined ? "" : d );
				break;

			case "class": case "src": case "activeMode":
				self.O=(function(t){
					switch(t){
					case "class": return "class";
					case "src": return "src";
					case "activeMode": return "activeMode"; }
				})(self.T);
			case "Attribute": case "attribute":
				d === undefined ?
					self.E.removeAttribute( self.O||"class" ) :
					self.E.setAttribute( self.O||"class", d ) ;
				break;

			case "D": case "display":
				d !== undefined ?
					Piers.DOM.updateClass(e,undefined,/PsHide/) :
					Piers.DOM.updateClass(e,"PsHide",/PsHide/) ;
				break;
			case "V": case "Val":
			case "Value": case "value":
				if( self.E.updateValue ){
					self.E.updateValue( d );
				}else
					d === undefined ?
						delete self.E[ self.O||"value" ] :
						self.E[ self.O||"value" ] = d;
				break;

			case "BG": case "image":
				self.O="backgroundImage";
				if(d) d="url("+d+")";
			case "Style": case "style":
				d === undefined ?
					delete self.E.style[ self.O||"display" ] :
					self.E.style[ self.O||"display" ] = d;
				break;

			case "Choose":
				if( d !== undefined ){
					var i;
					for( i=e.firstChild; i; i=i.nextSibling ){
						if( i.nodeType !== 1 ) continue;
						i.click();
						if( self.E.value === d ) break;
						Piers.DOM.removeClass( i, "PsS" );
					}
					self.E.value = d;
				}
				break;
			case "Radio": case "radio":
				Piers.DOM.selectAll( self.E, '[type="radio"]' ).forEach( function( oe ){
					oe.checked = oe.getAttribute("value") === d;
				} );
				break;
			case "Checkbox": case "checkbox":
				(function(d){
					Piers.DOM.selectAll( self.E, '[type="radio"]' ).forEach( function( oe ){
						oe.checked = oe.getAttribute("value") in d;
					} );
				})( d.reduce( function(r,v){
					r[v]=true;
					return r;
				}, {} ));
				break;
			}
			or();
		});
	};

	function List( e, tagname="an" )
	{
		this.E = e;
		this.FormTag = tagname;
		this.LT = this.E.cloneNode(true);
		this.F = [];
		this.ConvertFrom = undefined;
	}
	List.prototype.set = function( ds )
	{
		var self=this;
		ds = ds || self.E.__Doc__ || [];
		if( !Array.isArray(ds) ){
			ds = self.D = Piers.OBJ.reduce( ds, function(r,v,k){ v.__Key__ = k; r.push(v); return r; }, [] );
			self.ConvertFrom = "Obj";
		}
		self.E.__Doc__ = ds;
		self.RedrawTS = ds.RedrawTS = new Date();
		self.clear();
		return new Promise(function(or,oe){
			Promise.all( ds.reduce( function( r, d, ix ){
				if(!d) return r;
				var fie = document.createTextNode( "" ),
					form = new Form( self.LT.cloneNode(true), self.FormTag ),
					ne,ie,dt;
				self.E.appendChild( fie );
				r.push( new Promise( function( or, oe ){
					form.set( d ).then( function( ){
						self.E.__Doc__ = ds;
						ne = form.E;
						while( ie = ne.firstChild ){
							if( ie.nodeType === 1 ){
								ie.__Doc__ = d; ie.__Idx__ = ix;
								Piers.DOM.updateClass( ie,ix%2==0 ? "PsEvenRow" : "PsOddRow" );
							}
							self.E.insertBefore( ie, fie.parentNode==self.E ? fie : undefined);
						}
						or();
					}, oe );
				} ) );
				return r;
			}, [] ) ).then(or,oe);
		});
	};
	List.prototype.get = function( )
	{
		var self=this, i,rv,
			es = this.E.childNodes;
		for( i=0, rv=[]; i<es.length; i++ )
			if(es[i].nodeType==1)
				rv.push( (new Form( es[i], self.FormTag )).get( es[i].__Doc__ ) );
		this.E.__Doc__ = rv;
		return this.ConvertFrom ? rv.reduce( function(r,v,i){
			if( "__Key__" in v )
				r[v.__Key__] = Piers.OBJ.filter( v, function(v,k){ return k!=="__Key__"; } );
			return r;
		}, {} ) : rv;
	};
	List.prototype.clear = function( )
	{
		while( this.E.firstChild )
			this.E.removeChild(this.E.firstChild);
		delete this.E.__ObjConverted__;
		delete this.E.__Doc__;
	};
	List.prototype.act = function(op, args)
	{
		switch(op){
		case "SortA":
			return this.set(this.E.__Doc__.sort(function(a,b){
				return a[args] > b[args] ? 1 : a[args] < b[args] ? -1 : 0 ; }));
		case "SortD":
			return this.set(this.E.__Doc__.sort(function(a,b){
				return a[args] > b[args] ? -1 : a[args] < b[args] ? 1 : 0 ; }));
		case "Filter":
			this.E.__Doc__.myFilter = args ? function(d){
				return d && args.reduce(function(r,a,i){
					return r && a.reduce(function(r,o,i){
						return r || (function(o,d){
							var k;
							if( o[1] ) return (d[o[1]]||"").toString().indexOf(o[0]) >= 0;
							for( k in d ) if( (d[k]||"").toString().indexOf(o[0]) >=0 ) return true;
							return false;
						})(o,d);
					},false);
				},true) ? d : undefined;
			} : undefined;
			return this.set();
		}
	};
	List.prototype.removeItem = function( e )
	{
		i = Piers.DOM.select( e, function(i){ return "__Idx__" in i; }, mode=8 );
		i = (i||{}).__Idx__;
		if( undefined !== i ){
			this.get();
			this.E.__Doc__.splice(i,1);
			this.set().then(console.log,console.log);
		}
	};
	List.prototype.insertItem = function( d, loc=undefined )
	{
		this.get();
		if( undefined !== loc ) this.E.__Doc__.splice(loc,0,d); else this.E.__Doc__.push(d);
		this.set().then(console.log,console.log);
	};

	function OptForm( e, tagname="an" )
	{
		this.E = e;
		this.FormTag = tagname;
		this.L = {};
	}
	OptForm.prototype.set = function( d )
	{
		var i,es=this.E.querySelectorAll("[OptForm]"), dn, wa=[];
		for(i=0;i<es.length;i++){
			dn = es[i].getAttribute("OptForm");
			if( dn in d ){
				Piers.DOM.updateClass(es[i],undefined,/PsHide/);
				if( !(dn in this.L) ) this.L[dn] = new Form( es[i], this.FormTag );
				wa.push( this.L[dn].set( d[dn] ) );
			}else Piers.DOM.updateClass(es[i],"PsHide",/PsHide/);
		}
		this.E.__Doc__ = d;
		return Promise.all(wa);
	};
	OptForm.prototype.get = function( d )
	{
		var i,es=this.E.querySelectorAll("[OptForm]"), dn, rd={};
		if(!d) d=this.E.__Doc__||{};
		for(i=0;i<es.length;i++){
			dn = es[i].getAttribute("OptForm");
			cs = es[i].getAttribute("class");
			if( (!cs) || cs.indexOf("PsHide") < 0 ){
				if( !(dn in this.L) ) this.L[dn] = new Form( es[i], this.FormTag );
				rd[dn] = this.L[dn].get( d[dn] );
			}
		}
		this.E.__Doc__ = rd;
		return rd;
	};
	OptForm.prototype.clear = function( )
	{
		(new Form( this.E, this.FormTag )).clear();
		delete this.E.__Doc__;
	};

	function Form( e, tagname="an" )
	{
		var self=this;
		self.L=[];
		(function dec(E){
			var e,a;
			for(e=E.firstChild;e;e=e.nextSibling) if(e.nodeType===1){
				a=e.getAttribute(tagname);
				if(a){
					a.split(/;/).forEach(function( a ){
						if(!a) return;
						a = a.split(":");

						var dataRef = a.shift().split(/\./), type = a, handle;
						switch( type[0] ){
						case "Form":
							self.L.push( {"D":dataRef,"H":new Form( e, tagname )} ); break;
						case "List":
							self.L.push( {"D":dataRef,"H":new List( e, tagname )} ); break;
						case "OptForm":
							self.L.push( {"D":dataRef,"H":new OptForm( e, tagname )} ); break;
						default:
							self.L.push( {"D":dataRef,"H":new Generic( e, type, dataRef, tagname )} );
							dec(e); break;
						}
					});
				}else dec(e);
			}
		})( self.E=e );
	};
	Form.prototype.set = function( d )
	{
		var self=this, lk;
		return new Promise( function(or,oe){
			var q=[]; // waiting queue
			self.L.forEach(function( lk ){
				if( "set" in lk.H && "function"===typeof(lk.H.set) ){
					q.push( lk.H.set( Piers.OBJ.get(d,lk.D) ) );
				}else console.log("EXCEPTION -9",lk);
			});
			Promise.all(q).then(function(){
				or( self.E.__Doc__ = d );
			},oe);
		} );
	};
	Form.prototype.get = function( d )
	{
		var self=this, lk;
		if(!d) d=self.E.__Doc__||{};
		self.L.forEach(function( lk ){
			if( "get" in lk.H && "function"===typeof(lk.H.get) ){
				var x = (function(v){
					return v!==undefined ? v : Piers.OBJ.get(d,lk.D);
				})( lk.H.get() );
				if( lk.D ){
					if( x !== undefined ) Piers.OBJ.put( d, lk.D, x );
				}else d=x;
			}
		});
		self.E.__Doc__ = d;
		return d;
	};
	Form.prototype.clear = function( l )
	{
		var self=this, k, lk;
		if( !l ){ l = self.L||{}; }
		self.L.forEach(function( lk ){
			if( "clear" in lk.H && "function"===typeof(lk.H.clear) ) lk.H.clear();
		});
		delete self.E.__Doc__;
		return self;
	};
	Form.prototype.readonly = function( )
	{
		var i,es;
		es = this.E.querySelectorAll("input");
		for(i=0;i<es.length;i++) es[i].setAttribute("readonly",true);
		es = this.E.querySelectorAll("select");
		for(i=0;i<es.length;i++) es[i].setAttribute("disabled",true);
		es = this.E.querySelectorAll("button");
		for(i=0;i<es.length;i++) es[i].style.display = "none";
	};
	Form.prototype.findDoc = function( e )
	{
		return e ? Piers.DOM.find(e,function( i ){ return i.__Doc__; }).__Doc__ : this.E.__Doc__;
	};

	function __entry__( tagname="an" ){
		var fms=this;
		Piers.DOM.selectAll( document.body, "[PsForm]" ).forEach( function(pb){
			var a = pb.getAttribute("PsForm");
			if(a){
				fms[a] = new Form( pb, tagname );
				pb.removeAttribute("PsForm");
			}
		} );
	}
	__entry__.build = function( e, tagname="an" ){ return new Form( e, tagname ); };

	Return.setResult( __entry__ );
})(Piers.__LIBS__.Forms);
