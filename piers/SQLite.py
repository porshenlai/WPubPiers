from os import path as Path, remove, listdir
from json import load as json_load, loads as json_parse, dumps as json_stringify
from sqlite3 import connect as connectdb, IntegrityError, ProgrammingError
from aiofile import async_open
from piers import debug

class SQTable:
	def __init__( self, dbpath, table, columns ) :
		self.DBPath = dbpath
		self.TableName = table
		self.Columns = columns
		self.Conn = None

	def __enter__( self ) :
		try:
			self.Conn = connectdb( self.DBPath )
			cur = self.Conn.cursor( )
			res = cur.execute( "PRAGMA table_info(%s)" % self.TableName )
			res = res.fetchall()
			if len(res) <= 0 :
				cur.execute( "CREATE TABLE %s (%s PRIMARY KEY,%s)" %
					( self.TableName, self.Columns[0], ",".join(self.Columns[1:]) ) )
				self.Conn.commit()
			else :
				self.Columns = [ v[1] for v in res ]
			cur.close()
			return self
		except Exception as x :
			debug(x)
	def __exit__( self, type, value, traceback ) :
		try :
			self.Conn.commit()
		except :
			pass
		self.Conn.close()

	def __ensure_string_dict__( self, d ) :
		for k in d :
			d[k] = str(d[k])
		return d

	def do_select( self, conds={}, ops={}, cols=[], logicOP="AND", cur=None ) :
		c = cur or self.Conn.cursor()
		qs = [ k+(ops[k] if k in ops else "=")+":"+k for k in conds ]
		print(
			"SELECT %s FROM %s%s" % (
				",".join( cols ) if cols else "*",
				self.TableName,
				" WHERE "+(" "+logicOP+" ").join(qs) if qs else ""
			)
		);
		for r in c.execute(
			"SELECT %s FROM %s%s" % (
				",".join( cols ) if cols else "*",
				self.TableName,
				" WHERE "+(" "+logicOP+" ").join(qs) if qs else ""
			), self.__ensure_string_dict__( conds )
		).fetchall() :
			yield r
		if not cur : c.close()

	def do_update( self, conds, vals, cur=None ) :
		c = cur or self.Conn.cursor()
		uv = {}
		uv.update( vals )
		uv.update( conds )
		r = c.execute(
			"UPDATE %s SET %s WHERE %s" % (
				self.TableName,
				",".join( [ k+"=:"+k for k in vals if k in self.Columns ] ),
				" AND ".join( [ k+"=:"+k for k in conds if k in self.Columns ] )
			), self.__ensure_string_dict__( uv )
		)
		if not cur : c.close()

	def do_insert( self, vals, cur=None ) :
		c = cur or self.Conn.cursor()
		for v in self.Columns :
			if v not in vals : vals[v] = ""
		c.execute(
			"INSERT INTO %s VALUES (%s)" % (
				self.TableName,
				",".join([ ":"+v for v in self.Columns ])
			), self.__ensure_string_dict__( vals )
		)
		if not cur : c.close()

	def do_delete( self, conds, cur=None ) :
		c = cur or self.Conn.cursor()
		c.execute(
			"DELETE FROM %s WHERE %s" % (
				self.TableName,
				" AND ".join( [ k+"=:"+k for k in conds ] )
			), self.__ensure_string_dict__( conds )
		) 
		if not cur : c.close()

	def open( self ) :
		self.__enter__()

	def close( self ) :
		self.__exit__( None, None, None )

	def put( self, where={}, value={} ) :
		try :
			cur = self.Conn.cursor()
			uv = {}
			uv.update(value)
			uv.update(where)
			self.do_insert( vals=uv, cur=cur )
		except IntegrityError :
			self.do_update( conds=where, vals=value, cur=cur )
		except Exception as x :
			debug(x)
		finally :
			cur.close()
			self.Conn.commit()

	def get( self, where={}, ops={}, targets=[], logicOP="AND") :
		for r in self.do_select( conds = where, ops = ops, logicOP=logicOP, cols = targets) :
			yield r

	def delete( self, ks ) :
		try :
			self.do_delete( [ k+"='"+ks[k]+"'" for k in ks ] )
		finally:
			self.Conn.commit()

class Storage :
	def __init__( self, rpath, cs ) :
		self.RPath = Path.realpath( rpath )
		self.SDB = SQTable( Path.join(self.RPath,"index.db"), "entries", ["__K__"]+cs )

	def __enter__( self ) :	
		self.SDB.open( )
		return self

	def __exit__( self, type, value, traceback ) :
		#	print("DEBUG:",type,value,traceback);
		self.SDB.close( )

	def start( self ) :
		self.__enter__( )

	def stop( self ) :
		self.__exit__( None, None, None )

	def open( self, key, mode, vs=None ) :
		r = open( Path.join( self.RPath, key ), mode )
		if vs : self.SDB.put( where={"__K__":key}, value=vs )
		return r;

	def find( self, where={}, ops={}, targets=[], logicOP="AND") :
		return self.SDB.get( where=where, ops=ops, logicOP=logicOP, targets=targets )

	def remove( self, key ) :
		self.SDB.delete( {"__K__":key} )
		remove( Path.join( self.RPath, key ) )

class FileStorage( Storage ) :
	def __init__( self, dbpath ) :
		super().__init__( dbpath, ["Ext","Memo"] );

	def start( self ) :
		self.__enter__( )

	async def save( self, key, bs ) :
		p,x,m = key;
		fp = Path.join( self.RPath, p )
		if str == type(bs) : bs = bytes(bs,encoding="utf8")
		async with async_open( fp, "wb" ) as fo :
			if bytes == type(bs) :
				await fo.write( bs )
			else :
				async for buf in bs :
					await fo.write( buf )
		self.SDB.put( where={"__K__":p}, value={"Ext":x,"Memo":m} )

	def resolve( self, key ) :
		p = Path.join(self.RPath,key)
		for (x,) in self.SDB.do_select( conds={"__K__":key}, cols=["Ext"] ) :
			return p,x
		return p,None

	async def load( self, key ) :
		async with async_open( Path.join( self.RPath, key ), "rb" ) as fo :
			return await fo.read()

class JSONStorage( Storage ) :
	def __init__( self, dbpath, columns ) :
		super().__init__( dbpath, columns );

	def start( self ) :
		auto_rebuild = not Path.exists( self.SDB.DBPath )
		self.__enter__( )
		if auto_rebuild :
			for f in listdir( self.RPath ) :
				if not f.endswith(".json") : continue
				with open( Path.join( self.RPath,f ), "r" ) as fo :
					doc = json_load(fo)
					if len([ k for k in doc if k in self.SDB.Columns[1:] ]) <= 0 :
						continue
					self.SDB.put( where={"__K__":f[:-5]}, value=doc )

	async def save( self, key, vs ) :
		async with async_open( Path.join( self.RPath, key+".json" ), "w" ) as fo :
			await fo.write( json_stringify( vs, ensure_ascii=False ) )
		self.SDB.put( where={"__K__":key}, value=vs )

	def resolve( self, key ) :
		return Path.join(self.RPath,key+".json"), "application/json; charset=utf-8"

	async def load( self, key ) :
		async with async_open( Path.join(self.RPath,key+".json"), "r" ) as fo :
			return json_parse( await fo.read() );

if __name__ == "__main__" :
	with Storage( "/tmp", ["Ds"] ) as db :
		with db.open( "Test1", "w", {"Ds":"123 456"} ) as fo :
			fo.write("Hello World")
		with db.open( "Test2", "w", {"Ds":"123 789"} ) as fo :
			fo.write("Hello Kitty")

		for k,d in db.find( ) :
			print("ALL:",k,d)
		for k,d in db.find( like={"Ds":"%123%"} ) :
			print("LIKE:",k,d)
		for k,d in db.find( where={"Ds":"123 789"} ) :
			with db.open( k, "r" ) as fo :
				print("WHERE:",k,d, fo.read())
		db.remove( "Test1" )
		db.remove( "Test2" )
