from json import dumps as json_stringify, loads as json_parse
from os import path as Path, makedirs as mkdir, getcwd
from re import compile as newRE
from aiofile import async_open
from piers.Data import RSA, LatestNCache
from Crypto.Hash import SHA256
from base64 import b64encode
from piers.SQLite import SQTable

class UserKeyCache( LatestNCache ) :
	def __init__( self, size, db ) :
		super().__init__( size )
		self.SDB = db;
	def _on_cache_miss_( self, key ) :
		for a,ks in self.SDB.get( where={"A":key}, targets=["A","Ks"] ) :
			return json_parse(ks);
		return None;

class WebService :
	URLPrefix = "RSAHome/"
	Name = "Home"

	def __init__( self, root=None ) :
		self.Home = Path.join( Path.abspath(root) if root else getcwd(), "db" )
		self.RSA = RSA( PEMPath=Path.join( self.Home, "KeyPairs.pem" ) )
		self.DB = SQTable( Path.join(self.Home,"Users.db"), "users", ["A","S","SK","Ks"] )
		self.DB.open()
		#for row in self.DB.get() :
		#	print(row)
		self.KeyCache = UserKeyCache( 32, self.DB )

	def __release__( self ) :
		print("CLOSE DB")
		self.DB.close()

	async def installSession( self, rs ) :
		if "Piers-X-AUTH" in rs.Req[2] and "Piers-X-INFO" in rs.Req[2]:
			k = rs.Req[2]["Piers-X-INFO"]
			info = json_parse( k )
			h = SHA256.new()
			for (sk,ks) in self.DB.get(where={"A":info["N"]},targets=["SK","Ks"]) :
				h.update( bytes( k+sk, encoding="utf8" ) )
				if h.hexdigest() == rs.Req[2]["Piers-X-AUTH"] :
					info["Ks"] = ks
					rs.Session.update( info )
				else :
					return rs.JSON({"E":"BadSession"})

	async def GET_listMyKeys( self, rio ) :
		# for a,ks in self.DB.get( where={"A":rio.Session["N"]}, targets=["A","Ks"] ) :
		#	return rio.JSON({"R":"OK","D":{ "A":a, "Ks":ks }})
		ks = self.KeyCache.get( rio.Session["N"] )
		return rio.JSON( { "R":"OK", "D":{ "A":rio.Session["N"], "Ks":ks  } } if ks else { "E":"Failed" } )

	async def GET_listUsers( self, rio ) :
		rs = []
		for a in self.DB.get(targets=["A"]) :
			rs.append(a[0])
		return rio.JSON({"List":rs});

	async def GET_list( self, rio ) :
		if "adm" not in rio.Session["Ks"] :
			return rio.JSON({"E":"Violation"})

		rs = []
		for a,ks,fs in self.DB.get(targets=["A","Ks","Fs"]) :
			rs.append({"A":a,"Ks":json_parse(ks),"Fs":fs})
		return rio.JSON({"List":rs});

	async def GET_configure( self, rio ) :
		return rio.JSON( {
			"getKey": "getKey/",
			"auth": "auth/verify",
			"enroll": "auth/enroll",
			"verify": "listMyKeys/"
		} )

	async def GET_getKey( self, rio ) :
		return rio.Bytes(
			self.RSA.getPublicKey( PEM=True ),
			"application/x-pem-file"
		)

	async def POST_passwd( self, rio ) :
		ct,doc,hdrs = rio.Req
		if "adm" not in rio.Session["Ks"] and rio.Session["N"] != doc["A"]:
			return rio.JSON({ "E":"Violation" })

		self.DB.put(where={ "A":doc["A"] },value={ "S":doc["S"] });
		return rio.JSON({ "R":"OK" })

	async def POST_newKs( self, rio ) :
		if "adm" not in rio.Session["Ks"] :
			return rio.JSON({ "E":"Violation" })

		ct,doc,hdrs = rio.Req
		self.DB.put(where={ "A":doc["A"] },value={ "Ks":json_stringify(doc["Ks"],ensure_ascii=False) });
		return rio.JSON({ "R":"OK", "D":doc["Ks"] })

	async def POST_newFs( self, rio ) :
		if "adm" not in rio.Session["Ks"] :
			return rio.JSON({ "E":"Violation" })

		ct,doc,hdrs = rio.Req
		self.DB.put(where={ "A":doc["A"] },value={ "Fs":doc["Fs"] });
		return rio.JSON({ "R":"OK", "D":doc["Fs"] })

	async def POST_auth( self, rio ) :
		try :
			r = { "E":"Failed" }
			ct, args, hdrs = rio.Req 
			task = rio.path.group(2)
			userinfo = {}
			for a,s,sk,ks,fs in self.DB.get( where={"A":args["U"]} ) :
				userinfo = {"A":a,"S":s,"SK":sk,"Ks":ks,"Fs":fs}
			if not userinfo :
				return rio.JSON( { "E": "Not available" } )

			if "enroll" == task :
				self.DB.put(where={
					"A":args["U"]
				},value={
					"S":self.RSA.decrypt( args["S"] ).decode("utf8"),
					"SK":"", "Ks":[], "Fs":0
				});
				r = { "R":"OK", "D":{ "N":args["U"] } }
			elif "verify" == task :
				if userinfo["S"] == self.RSA.decrypt(args["S"]).decode("utf8") :
					sskey = self.RSA.decrypt(args["K"]).decode("utf8")
					self.DB.put(where={"A":userinfo["A"]},value={"SK":sskey});
					r = {
						"R":"OK",
						"D":{
							"N":userinfo["A"],
							"Ks":json_parse( userinfo["Ks"] ),
							"Fs":userinfo["Fs"]
					}	}
				else :
					r = { "E":"Authentication Failed" }
		except Exception as x :
			r = { "E": str(x) }
		return rio.JSON(r)
