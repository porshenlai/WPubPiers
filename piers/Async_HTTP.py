from aiohttp import web,web_request,ClientSession
from aiofile import async_open
from asyncio import CancelledError
from json import dumps as json_stringify
from mimetypes import guess_type
from os import path as Path
from re import compile as createRE, fullmatch as matchRE

from piers import XI
from piers.Data import JObj
from piers.Async import Queue, tryWait

import ssl

async def httpGET( url ) :
	async with ClientSession() as session:
		async with session.get(url) as resp:
			if resp.status == 200 :
				return await resp.text()
			else :
				return (resp.status,"Failed")

async def httpPOST( url, obj ) :
	async with ClientSession() as session:
		async with session.post(url,json=obj) as resp:
			if resp.status == 200 :
				return await resp.json()
			else :
				return (resp.status,"Failed")

async def httpPUT( url, data ) :
	async with ClientSession() as session:
		async with session.put(url,data=data) as resp:
			if resp.status == 200 :
				return await resp.json()
			else :
				return (resp.status,"Failed")

class RIO:

	RE_FilterDirDot = createRE('/\.+')
	RE_MimeTypeJSON = createRE("^(application)/(json)(;.*)?")
	RE_MimeTypeText = createRE("^(text)/(.*)(;.*)?")
	RE_MimeTypeImage = createRE("^(image)/(.*)(;.*)?")
	RE_MimeTypeBytes = createRE("^(application)/(octet-stream)(;.*)?")

	def __init__( self, req, srv ) :
		self.request = req
		self.server = srv
		self.headers = self.server.CORS.copy()
		self.path = RIO.RE_FilterDirDot.sub( '/', req.path )
		self.path = "/" + ( self.path[1:] if self.path.startswith('/') else self.path )
		self.Req = (None,None,None) ## content-type, body, header
		self.Session = {}
		self.server._log_( "%s %s %s" % (req.remote,req.method,self.path), 7 )

	async def __prepare__( self ) :
		req,opt = self.request, self.server.O
		if hasattr(req,"content_length") and req.content_length :
			if req.content_length > opt["MAXREQSIZE"] :
				raise XI("OUT_OF_RESOURCE","Request body too large.")

		ct = req.content_type if hasattr(req,"content_type") else "application/octet-stream"
		if RIO.RE_MimeTypeJSON.match(ct) :
			self.Req = ("JSON",await req.json(),req.headers)
		elif RIO.RE_MimeTypeText.match(ct) :
			self.Req = ("Text",await req.text(),req.headers)
		else :
			self.Req = (ct,None,req.headers)

	async def read( self ) :
		yield await self.request.read()

	async def save( self, path ) :
		if not self.ReqBody :
			async with async_open( path, "wb" ) as fo :
				async for buf in self.read() :
					await fo.write( buf )
		elif "Text" == self.ReqType :
			async with async_open( path, "w" ) as fo :
				await fo.write( self.ReqBody )
		elif "JSON" == self.ReqType :
			async with async_open( path, "w" ) as fo :
				await fo.write( json_stringify( self.ReqBody, ensure_ascii=False ) )

	def addHeader( self, name, value ) :
		self.headers[name] = value

	def JSON( self, data ) :
		return self.Bytes( JObj( data ).stringify().encode('utf8'), "application/json" )

	def Bytes( self, data, ctype ) :
		return web.Response( body = data, headers = self.headers, content_type = "application/json" )

	def Redirect( self, url ) :
		return web.HTTPFound(url)

	async def File( self, path, mtype=None ) :
		ctype, ec = mtype or guess_type( path )
		if ec : ctype += "; charset="+ec
		self.headers["Content-Type"] = ctype
		try :
			rs = web.StreamResponse( status=200, reason="OK", headers=self.headers )
			if web_request.BaseRequest == type( self.request ) :
				await rs.prepare( self.request )
			async with async_open( path, "rb" ) as fd :
				while self.server.Q.isActive( ) :
					buf = await fd.read( self.server.O["BUFSIZE"] )
					if not buf : break
					await rs.write( buf )
			return rs
		except Exception as x :
			return web.HTTPNotFound(text="File Error")

	async def URL( self, url ) :
		path = self.server._resolve_( url )
		if path and Path.exists( path ) :
			return await self.File( path )
		return web.HTTPNotFound(text="File Error")

class Server( ) :
	"""
	s = Server(
		host = "0.0.0.0:80",
		home = "./index.html",
		options = { "BUFSIZE":1048576, "MAXREQ":32, "MAXREQSIZE":8388608 },
		cors = { "Access-Control-Allow-Origin":"*", "Access-Control-Allow-Headers":"*" },
		cafiles = None
	)
	async for s,c,d in s.play() :
		print(s,c,d)
	"""
	# {{{

	def __init__( self, addr="0.0.0.0:9980", home="./index.html", options=None, cors=None, cafiles=None ) :
		addr = matchRE( r"(.*):(\d+)", addr )
		if not addr : raise Exception("Bad Argument: addr(%s)" % addr)
		self.Host, self.Port = addr.group(1), int(addr.group(2))

		home = matchRE( r"(.*)[\\/]([^\\/]+)", home )
		if not home : raise Exception("Bad Argument: home(%s)" % home)
		self.Root, self.Index = Path.realpath(home.group(1)), home.group(2)
		
		self.O = {
			"BUFSIZE":1048576,
			"MAXREQ":32,
			"MAXREQSIZE":8388608
		}
		if options : self.O.update( options )
		self.CORS = { "Access-Control-Allow-Origin":"*", "Access-Control-Allow-Headers":"*" }
		if cors : self.CORS.update( cors )

		self.P = None # TCPSite
		self.Q = None # Queue
		self.LogLevel = 0
		self.ReqCounts = 0
		self.SSLCtx = None
		if cafiles :
			self.SSLCtx = ssl.create_default_context( ssl.Purpose.CLIENT_AUTH )
			self.SSLCtx.load_cert_chain( *cafiles ) # crt,key

	def _log_( self, message, level=0 ) :
		if level > self.LogLevel : self.Q.push( (self,"I","[%d]:%s" % (level,message)) )

	def _resolve_( self, url ) :
		url = Path.join( self.Root, url )
		if Path.isdir( url ) :
			url = Path.join( url, self.Index )
		return url

	async def _authenticate_( self, rs ) :
		pass

	async def _handle_OPTIONS_( self, rs ) :
		return rs.JSON( {"R":"OK"} )

	async def _handle_POST_( self, rs ) :
		return rs.JSON( {"E":"NOT_SUPPORT"} )

	async def _handle_GET_( self, rs ) :
		return await rs.URL( rs.path[1:] )

	async def _handle_PUT_( self, rs ) :
		return rs.JSON( { "E":"NOT_SUPPORT" } )

	async def __handle__( self, request ) :
		try :
			if self.ReqCounts >= self.O["MAXREQ"] :
				return web.HTTPTooManyRequests()
			self.ReqCounts += 1
			request._client_max_size = self.O["BUFSIZE"]
			r = RIO( request, self )
			await r.__prepare__()
			## authenticate
			rs = await self._authenticate_( r )
			if rs != None:
				return rs
			## dispatch
			return await getattr( self, "_handle_"+request.method+"_" )( r )
		except web.HTTPException as x :
			return x
		except AttributeError as x :
			self._log_( str(x), level=7 )
			return web.HTTPBadRequest(reason="Unhandled Method: "+request.method)
		except CancelledError :
			await self.stop()
			return web.HTTPBadRequest(reason="Cancelled")
		except XI as x :
			self._log_( str(x), level=7 )
			return web.HTTPBadRequest(reason=str(x))
		except Exception as x :
			self._log_( str(x), level=7 )
			return web.HTTPBadRequest(reason=str(x))
		finally:
			self.ReqCounts -= 1
		return web.HTTPBadRequest(reason="Unhandle Exception")

	async def __aenter__( self ) :
		try :
			self.Q = Queue()
			self.Q.push( (self,"I","Init Host: %s, Port: %d" % (self.Host,self.Port)) )
			self.Q.push( (self,"I","Init Docs: %s/%s" % (self.Root,self.Index)) )

			runner = web.ServerRunner( web.Server( self.__handle__ ) )
			await runner.setup()

			host = self.Host
			if host.startswith("[") and host.endswith("]") :
				host = host[1:len(host)-1]
			self.P = web.TCPSite( runner, host, self.Port, ssl_context=self.SSLCtx ) if self.SSLCtx else web.TCPSite( runner, host, self.Port )
			await self.P.start()
			self.Q.push( (self,"I","Ready") )
		except Exception as e :
			print("Exception",e);
			await self.__aexit__( None, None, None )

	async def __aexit__( self, type, value, traceback ) :
		if self.P:
			await self.P.stop()
			self.P = None
		if self.Q:
			self.Q.push( (self,"I","Closed") )
			await self.Q.close()
			self.Q = None

	async def play( self, timeout=None ) :
		async with self :
			async for scd in self.Q.play( timeout=timeout ) :
				yield scd

	async def stop( self ) :
		if self.Q:
			self.Q.push( (self,"I","Closed") )
			await self.Q.close()
			self.Q = None
	## }}}

class WebService( Server ) :
	"""
	s = WebService (
		host = "0.0.0.0:80",
		home = "./index.html",
		options = { "BUFSIZE":1048576, "MAXREQ":32, "MAXREQSIZE":8388608 },
		cors = { "Access-Control-Allow-Origin":"*", "Access-Control-Allow-Headers":"*" },
		cafiles = None
	)
	s.reg("DC/path/.*",self.FUNCTION)
	"""
	## {{{
	def __init__( self, addr="0.0.0.0:9980", home="./index.html", options=None, cors=None, cafiles=None ) :
		super().__init__( addr, home, options=options, cors=cors, cafiles=cafiles )
		self.APIs = {"GET":set(),"POST":set(),"PUT":set()}
		self.URLPrefixes = {};
		self.Modules = {};

	async def __aexit__( self, type, value, traceback ) :
		await super().__aexit__( type, value, traceback )
		for m in self.Modules :
			self.Modules[m].__release__()

	def reg( self, prefix, handler, method="POST" ) :
		print("Register",prefix)
		r = (prefix,handler)
		if str == type(prefix) :
			key = method+":"+prefix
			if key in self.URLPrefixes :
				self.APIs[method].remove( self.URLPrefixes[key] )
			r = self.URLPrefixes[key] = (createRE(prefix),handler);
		self.APIs[method].add( r )

	def reg_module( self, mod, args={}, prefix="" ) :
		class MH :
			def __init__( self, inst ) :
				self.WS = inst
			async def GET( self, rio ) :
				return await getattr(self.WS, "GET_"+rio.path.group(1))( rio );
			async def POST( self, rio ) :
				return await getattr(self.WS, "POST_"+rio.path.group(1))( rio );
			async def PUT( self, rio ) :
				return await getattr(self.WS, "PUT_"+rio.path.group(1))( rio );
		s,m = mod.WebService(**args), {}
		if hasattr(mod.WebService,"Name") and hasattr(s,"__release__") :
			self.Modules[mod.WebService.Name] = s
		for fn in dir( s ) :
			if fn.startswith("GET_") : m["GET"] = True
			elif fn.startswith("POST_") : m["POST"] = True
			elif fn.startswith("PUT_") : m["PUT"] = True
		if prefix and not prefix.endswith("/") : prefix += "/"
		prefix += mod.WebService.URLPrefix
		if prefix.endswith("/") : prefix = prefix[:-1]
		mh = MH( s )
		for k in m :
			self.reg( prefix+"/([^/]*)/?(.*)", getattr(mh,k), method=k )
		return s;

	def __find_api__( self, apis, rio ) :
		for (t,h) in apis :
			m = t.match( rio.path[1:] )
			if m :
				rio.path = m
				return h
	async def _handle_POST_( self, rio ) :
		h = self.__find_api__( self.APIs["POST"], rio )
		return await (tryWait( h( rio ) ) if h else super()._handle_POST_( rio ))

	async def _handle_GET_( self, rio ) :
		h = self.__find_api__( self.APIs["GET"], rio )
		return await (tryWait( h( rio ) ) if h else super()._handle_GET_( rio ))

	## }}}

if __name__ == "__main__" :
	from sys import stdin
	from json import loads
	from signal import signal, SIGINT
	from piers.Async import addTask, play as playAsync

	ws = WebService( "0.0.0.0:9980", "./index.html", {
		"BUFSIZE":1048576, "MAXREQ":32, "MAXREQSIZE":8388608
	} )

	def test( rio ) :
		return rio.JSON( {"A":123} )
	ws.reg( "test/(.*)", test, "GET" )

	signal(SIGINT,lambda sig,frame : addTask(ws.stop()))

	async def play_ws() :
		async for s,c,d in ws.play() :
			print(c,d)

	addTask( play_ws() )
	playAsync()
