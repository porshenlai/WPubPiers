(function(Return){

	function HomeBase( pfn, eh ){ // {{{
		var self = this;
		self.Keys = { };
		self.Authorized = false;
		self.__onEvent__ = eh;

		// load keys from localStorage
		self.PfName = pfn;
		if( !("localStorage" in window) )
			throw new Piers.Error("Not Support","localStorage not enabled or supported!");
		try {
			if( self.PfName )
				self.Keys = JSON.parse(localStorage.getItem( self.PfName ) || "{}");
			if( self.Keys.Profile ){
				profile = self.Keys.Profile;
				delete self.Keys.Profile;
				self.enter( profile );
			}else self.__onEvent__( 'changed' );
		} catch(e) {
			console.log(e);
			localStorage.removeItem( self.PfName );
		}
	}
	Object.assign( HomeBase.prototype, {
		"get":function( df=undefined ){
			try {
				return this.Keys.Profile;
			} catch( x ){ return df; }
		},
		"enter":function( profile ){
			var self = this, r;
			if( !self.__R__ )
				self.__R__ = Piers.createPromise();
			if( profile ){
				if( !self.Keys.Profile || self.Keys.Profile.N!==profile.N ){
					self.Keys.Profile = profile;
					//console.log("PROFILE updated",JSON.stringify(self.Keys.Profile));
					if( self.PfName )
						localStorage.setItem( self.PfName, JSON.stringify(self.Keys) );
					self.Authorized = true;
					self.__R__.setReady( profile );
					if( self.__onEvent__ ) self.__onEvent__( "changed" );
				}
			}else{
				if( !("Profile" in self.Keys) )
					self.__onEvent__( "login_required" );
				return self.__R__;
			}
		},
		"leave":function(){
			var self = this;
			self.Authorized = false;
			if( self.PfName ) localStorage.removeItem( self.PfName );
			self.Keys = {};
			delete self.__R__;
			self.__onEvent__( "changed" );
		},
		"authenticate":function( user, pass, enroll=false ){
			var self = this;
			return new Promise( function( or, oe ){
				if( !user ) return oe( "User is requied" );
				var pf={ "R":"OK", "D":{"N":user} };
				or( pf );
				self.enter( pf.D );
			} );
		},
		"request":function( url, payload ){
			var self = this, bs = payload || "";
			return Piers.U.create( url )[payload ? "post" : "get"]( bs );
		}
	} ); // }}}

	var Session={
		"createKeyPair":function(){
			var jse = new Session.RSA( { "default_key_size":1024} );
			return { "public":jse.getPublicKey(), "private":jse.getPrivateKey() };
		},
		"PrivateKey":function( key ){
			this.jse = new Session.RSA( );
			this.jse.setPrivateKey( key );
		},
		"PublicKey":function( key ){
			this.jse = new Session.RSA( );
			this.jse.setPublicKey( key );
		},
		// auth = new RSAHome( profile_name, event_handler() )
		// auth.enter().then( authenticated_works() )
		// ??? ... auth.authenticate( user, pass )
		"Home": HomeBase,

		"RSAHome":Piers.OBJ.inherit( HomeBase, function( pfn, eh ){ // {{{
			this.PFX = {
				"Base":"/__api__/RSAHome/",
				"getKey": "getKey/",
				"auth": "auth/verify",
				"enroll": "auth/enroll",
				"verify": "listMyKeys/"
			};
			HomeBase.call( this, pfn, eh );
		}, {
			"authenticate":function( user, pass, enroll=false ){
				var self = this;
				return new Promise( function( or, _oe_ ){
					function oe( x ){
						x = { "E":x.toString() };
						_oe_( x );
						if(self.__R__.onError) self.__R__.onError( x );
					}
					(new Piers.U( self.PFX.Base+self.PFX.getKey )).get()
					.then(function( r ){ r.getText().then( function( r ){
						var sessionKey = new Uint8Array(16)
						crypto.getRandomValues(sessionKey)
						self.Keys.Session = btoa( sessionKey );
						pubKey = new Piers.Session.PublicKey(r)
						Piers.U.create(
							self.PFX.Base+( enroll ? self.PFX.enroll : self.PFX.auth )
						).post( {
							"U": user,
							"K": pubKey.encrypt( self.Keys.Session ),
							"S": pubKey.encrypt( pass ),
							"F": enroll ? "Enroll" : "Auth"
						} ).then( function( r ){
							or( r );
							self.enter( r.D );
						}, function( e ){
							delete self.Keys.Session;
							oe( e );
						} );
					}, oe ); }, oe );
				} );
			},
			"request":function( url, payload ){
				var self = this, bs = payload || "";
				url = Piers.U.create( url );
				//if( "object" == typeof( bs ) )
				//	bs = JSON.stringify( bs );
				function act(){
					if( self.Keys.Profile ){
						xa = JSON.stringify( {
							"N": self.Keys.Profile.N,
							"T": new Date().getTime().toString(36)
						} );
						url.addHeader( "Piers-X-INFO", xa )
						url.addHeader( "Piers-X-AUTH", Session.SHA( xa + self.Keys.Session ) )
					}
					return url[payload ? "post" : "get"]( bs );
				}
				if( self.Keys.Profile ) return act();
				return new Promise( function(or,oe){
					setTimeout(function(){
						if( self.Keys.Profile ) or( act() );
						else oe( "Not login");
					},500);
				} );
			},
			"sign":function( bs ){
				if(!this.PrivateKey)
					this.PrivateKey = new Session.PrivateKey(this.Keys.private);
				return this.PrivateKey.sign( bs );
			}
		} ), // }}}

		"MSHome":Piers.OBJ.inherit( HomeBase, function( pfn, eh ){ // {{{
			this.PFX = "qdata.aspx?task=";
			HomeBase.call( this, pfn, eh );
		}, {
			"authenticate":function( user, pass, enroll=false ){
				var self = this;
				return new Promise( function( or, oe ){
					self.request( enroll ? "enroll" : "authenticate", { "U":user, "S":pass } )
					.then( or, oe );
				} );
			},
			"request":function( url, payload ){
				//console.log("request()",url,payload);
				var self = this, bs = payload || "";
				return Piers.U.create( self.PFX+url )[payload ? "post" : "get"]( bs );
/*
				return new Promise(function(or,oe){
					Piers.U.create( self.PFX+url )[payload ? "post" : "get"]( bs ).then(function(r){
						console.log("REQUEST",url,r);
						or(r);
					},oe);
				});
*/
			}
		} )	
	}; // }}}

	Object.assign( Session.PrivateKey.prototype, { // {{{
		"sign":function( value ){
			return this.jse.sign( value, Session.SHA, "sha256" );
		},
		"decrypt":function( value ){
			return this.jse.decrypt( value );
		}
	} ); // }}}

	Object.assign( Session.PublicKey.prototype, { // {{{ 
		"verify":function( value ){
			return this.jse.verify( value, Session.SHA );
		},
		"encrypt":function( value ){
			return this.jse.encrypt( value );
		}
	} );	// }}}

	function flush(){
		Session.SHA = sha256;
		delete window.sha256;
		delete window.sha224;
		Session.RSA = JSEncrypt;
		delete window.JSEncrypt;
		return Return.setResult( Session );
	}
	if( "JSEncrypt" in window && "sha256" in window ) flush()
	ps=[Piers._.importJS( Piers.Env.PierPath+"3rdparty/sha256.min.js" ),
		Piers._.importJS( Piers.Env.PierPath+"3rdparty/jsencrypt.min.js" )];
	ps[0].then(function(){
		ps[1].then( flush, function(e){ Return.setException(e) } );
	},function(e){ Return.setException( e ); });
})(Piers.__LIBS__.Session);
