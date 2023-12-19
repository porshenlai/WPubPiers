from json import dumps as json_stringify
from piers.SQLite import JSONStorage as JStorage, FileStorage as AStorage
from piers import debug
from time import time
from datetime import datetime, timedelta
from re import compile as newRE
from os import path as Path, listdir, makedirs

class WebService :
	URLPrefix = "Test/"

	def __init__( self, root ) :
		self.DBR = Path.join( Path.abspath(root) if root else getcwd(), "db" )
		self.DBW = Path.join( Path.abspath(root) if root else getcwd(), "docs/db" )
		makedirs( self.DBR, exist_ok=True )
		makedirs( self.DBW, exist_ok=True )

	async def GET_listdb( self, rio ) :
		target = rio.path.group(2)
		return rio.JSON({ "R":"OK", "List":listdir(self.DBW) });

	async def GET_A( self, rio ) :
		target = rio.path.group(2)
		return rio.JSON({ "R":"OK", "Target":target });

	async def POST_A( self, rio ) :
		target = rio.path.group(2)
		ct, arg, hdrs = rio.Req
		return rio.JSON({ "R":"OK", "Target":target, "Arg":arg });
