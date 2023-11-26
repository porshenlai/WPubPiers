from json import dumps as json_stringify
from piers.SQLite import JSONStorage as JStorage, FileStorage as AStorage
from piers import debug
from time import time
from datetime import datetime, timedelta
from re import compile as newRE
from os import path as Path, listdir, makedirs

class WebService :
	URLPrefix = "DB/"
	ARGCutter = newRE("([^/]+)(/(.*))?")

	def __init__( self, root ) :
		self.DBR = Path.join( Path.abspath(root) if root else getcwd(), "db" )
		makedirs( self.DBR, exist_ok=True )
		self.S = {
#			"Applier":JStorage( Path.join( self.DBR, "Appliers" ), ["NO","Abbrev","ID","Nation","Agent"] ),
#			"Agent":JStorage( Path.join( self.DBR, "Agents" ), ["NO","Abbrev","ID","Nation"] ),
#			"Trademark":JStorage( Path.join( self.DBR, "Trademarks" ), ["NO","Name"] ),
#			"Case":JStorage( Path.join( self.DBR, "Cases" ), ["NO","FirstApplierNO","Year","YSN","CertNO","DTReg"] ),
#			"Task":JStorage( Path.join( self.DBR, "Tasks" ), ["NO","TaskID","LDx","ADx","GDx","UsrList"] ),
#			"Attach":AStorage( Path.join( self.DBR, "Attaches" ) ),
		}
		for k in self.S :
			self.S[k].start()

	def parse_args( self, url ) :
		m = self.ARGCutter.match( url )
		if m :
			return m.group(1), m.group(3)
		return url, None

	async def GET_list( self, rio ) :
		if "N" not in rio.Session :
			return rio.JSON({ "E":"Violation" })
		s, dbn = [], rio.path.group(2)
		if dbn in self.S :
			for i in self.S[dbn].find() :
				s.append(i);
		elif dbn == "Alerts" :
			dbn = "Task";
			dt7 = (datetime.now()+timedelta(days=7)).strftime("%Y-%m-%d")
			for i in self.S[dbn].find(
				where={ "LDx":dt7, "ADx":dt7, "GDx":dt7 },
				ops={"LDx":"<=","ADx":"<=","GDx":"<="},
				logicOP="OR"
			) :
				if i[6].find("."+rio.Session["N"]+".") >= 0 : s.append(i);
		return rio.JSON({ "C":self.S[dbn].SDB.Columns, "L":s });

	async def POST_list( self, rio ) :
		"""
		{
			"ops":{"NO":" LIKES "},
			"where":{"NO":"DT-"}
		}
		"""
		if "N" not in rio.Session :
			return rio.JSON({ "E":"Violation" })
		s, dbn = [], rio.path.group(2)
		ct, arg, hdrs = rio.Req
		xargs = {};
		if "ops" in arg : xargs["ops"] = arg["ops"];
		if "where" in arg : xargs["where"] = arg["where"];
		for i in self.S[dbn].find( **xargs ) :
			s.append(i);
		return rio.JSON({ "C":self.S[dbn].SDB.Columns, "L":s });


	async def GET_load( self, rio ) :
		try :
			if "N" not in rio.Session :
				return rio.JSON({ "E":"Violation" })
			dbn, key= self.parse_args( rio.path.group(2) )
			S = self.S[dbn];
			if not S :
				return res.JSON({ "E":"DB not found" })
			p,x = S.resolve( key )
			if Path.exists( p ) :
				return await rio.File( p, (x,None) )
			else :
				return rio.JSON({ "E":"Not found" })
		except Exception as x :
			debug( x )
			return rio.JSON({ "E":"Failed" })

	async def POST_save( self, rio ) :
		try :
			if "N" not in rio.Session :
				return rio.JSON({ "E":"Violation" })
			dbn, xargs = self.parse_args( rio.path.group(2) )
			S = self.S[dbn]
			if not S :
				return rio.JSON({ "E":"DB not found" })
			ct, doc, hdrs = rio.Req 
			if dbn == "Attach" :
				key = hex(int(time()*1000000))
				if str == type(doc) :
					doc = bytes(doc,encoding="utf-8");
				await S.save( (key,ct,xargs or "-"), doc or rio.read() )
				doc = key
			elif dbn == "Task" :
				Cs=doc["Controls"]
				LDx=ADx=GDx="9999-99-99"
				Users=""
				for li in Cs["Law"] :
					LC = Cs["Law"][li]
					if "CD" in LC and LC["CD"] : continue
					if LC["LD"] and LC["LD"] < LDx : LDx = LC["LD"]
					if LC["AD"] and LC["AD"] < ADx : ADx = LC["AD"]
				for li in Cs["General"] :
					NC = Cs["General"][li]
					if "CD" in NC and NC["CD"] : continue
					if NC["GD"] and NC["GD"] < GDx : GDx = NC["GD"]
				print("DEBUG",Cs,LDx,ADx,GDx,Users);
				doc["LDx"],doc["ADx"],doc["GDx"] = LDx,ADx,GDx
				doc["UsrList"] = "."+doc["Users"]["P"]+"."+doc["Users"]["C"]+"."+doc["Users"]["M"]+"."+doc["Users"]["F"]+"."+doc["Users"]["S"]+"."+doc["Users"]["A"]+"."
				await S.save( doc["NO"], doc )
			else:
				if "NO" not in doc :
					for k,v in S.SDB.do_select( cols=["__K__","Max(NO)"] ) :
						doc["NO"] = str(int("1"+v)+1)[1:]
						break
					doc = doc["NO"]
				await S.save( doc["NO"], doc )
			return rio.JSON({ "R":"OK", "D":doc })
		except Exception as x :
			debug(x)
			return rio.JSON({ "E":str(x) })

	async def GET_CaseANumber( self, rio ) :
		try :
			fan,year = rio.path.group(2).split("/")
			S = self.S["Case"]
			for k,v in S.SDB.do_select( cols=["__K__","Max(YSN)"], conds={"FirstApplierNO":fan,"Year":year} ) :
				if k and v :
					print(rio.path.group(2),k,v)
					v = str(int("1"+v)+1)[1:]
				else : return rio.JSON({ "R":"OK", "D":"001" });
			return rio.JSON({ "R":"OK", "D":v, "DEBUG":{"A":fan,"Y":year} });
		except Exception as x :
			return rio.JSON({ "E":str(x) });

	async def GET_test( self, rio ) :
		self.S["Applier"].remove( rio.path.group(2) )
		return rio.JSON({ "R":"OK" });

	async def POST_test( self, rio ) :
		try :
			ct, arg, hdrs = rio.Req
			print( arg )
			r = { "R":"OK", "A":arg }
		except Exception as x :
			r = { "E":str(x) }
		return res.JSON(r)
