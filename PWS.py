# PORSHENLAI MODIFIED AT 2023/11/27

from sys import path as libPath, stdin, exit
from os import listdir, makedirs, path as Path
from importlib import import_module
from re import compile as newRE
from json import loads as json_parse
from signal import signal, SIGINT

ROOT = Path.dirname(__file__)
if ROOT not in libPath : libPath.insert(0,ROOT)

from piers import Async
from piers.Async_HTTP import WebService, httpPOST, httpPUT

class PWS( WebService ) :
	def __init__( self, host, home, modules=[], cafiles=None ) :
		super().__init__( host, home, cafiles=cafiles )
		self.AuthMod = None
		for mn in modules :
			mod = self.reg_module(
				import_module("webservices."+mn),
				args = {"root":Path.realpath(ROOT)},
				prefix = "__api__"
			)
			if hasattr(mod,"installSession") : self.AuthMod = mod

	async def _authenticate_( self, rs ) :
		if self.AuthMod :
			return await self.AuthMod.installSession( rs )

async def main() :
	cfg = {
		"host":"0.0.0.0",
		"port":8780,
		"root":Path.join(ROOT,"docs"),
		"modules":["RSAHome","DB","Adm"],
		"index":"index.html",
		"pidfile":Path.join(ROOT,"etc/PWS.pid")
	}
	makedirs( Path.dirname(cfg["pidfile"]), exist_ok=True )
	print(cfg)

	if "pidfile" in cfg and cfg["pidfile"] :
		try :
			with open(cfg["pidfile"],"w") as fo :
				from os import getpid
				getpid = str(getpid())
				print("PID is %s" % getpid);
				fo.write( getpid )
		except Exception as x:
			print("Exception: ",x)
		
	ws = PWS(
		host = "%s:%d" % (cfg["host"],cfg["port"]),
		home = Path.join(cfg["root"],cfg["index"]),
		modules = cfg["modules"],
		cafiles = (cfg["cert"],cfg["key"]) if "cert" in cfg and cfg["cert"] and "key" in cfg and cfg["key"] else None

	)
	signal(SIGINT,lambda sig,frame : Async.addTask(ws.stop()))
	print("Web Server is ",ws);
	try :
		async for s,c,d in ws.play() :
			print(c,d)
	except Exception as x :
		print(x)

	if "pidfile" in cfg and cfg["pidfile"] :
		from os import remove
		remove(cfg["pidfile"])

Async.addTask(main())
Async.play()
