from json import dumps as json_stringify
from piers.SQLite import JSONStorage as JStorage, FileStorage as AStorage
from time import time
from aiofile import async_open
from re import compile as newRE
from os import path as Path, listdir

class WebService :
	URLPrefix = "Adm/"
	ARGCutter = newRE("([^/]+)(/(.*))?")

	def __init__( self, root ) :
		self.DBR = Path.join( Path.abspath(root) if root else getcwd(), "docs" )

	async def POST_save( self, rio ) :
		try :
			if "N" not in rio.Session :
				return rio.JSON({ "E":"Violation" })
			ct, doc, hdrs = rio.Req 
			async with async_open( Path.join(self.DBR,rio.path.group(2)), "w" ) as fo :
				await fo.write( json_stringify(doc,ensure_ascii=False) );
			return rio.JSON({ "R":"OK" })
		except Exception as x :
			print(x)
			return rio.JSON({ "E":str(x) })
