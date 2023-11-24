from piers import Platform
from piers.Data import JObj,KeyCode



if Platform == "AWS.Lambda" :
	from piers.Storage_AWS import Base
else :
	from piers.Storage_POSIX import Base

class UAIndex( Base ):
	"""
	idx = UAIndex( prefix, maxu=64 )
	r = idx.get( "A" )
	idx.put( {"A":{"B":123}} )
	idx.put( patch={"A":{"B":123}} )
	"""
	def __init__( self, Root, basename=".index", maxu=64 ) :
		super().__init__( Root )
		self.MU = maxu
		self.Prefix = basename
		self.AD = None
		self.UD = {}

	async def prepare( self ) :
		try :
			self.UD = JObj( (await self.read( self.Prefix+".u" ))[0] ).D 
		except :
			pass

	async def getArchives( self ) :
		if None == self.AD :
			try :
				self.AD = JObj( (await self.read( self.Prefix ))[0] ).D
			except :
				self.AD = {}
		return self.AD

	async def sync( self ) :
		if self.UD :
			ad = await self.getArchives()
			ad.update(self.UD)
			self.UD = {}
			await self.write( self.Prefix, JObj(ad).stringify('utf8') )
			self.remove( self.Prefix+".u" )

	async def get( self, key=None, dv=None ) :
		if key in self.UD :
			return self.UD[key]
		ad = await self.getArchives()
		if None == key :
			ad.update(self.UD)
			return ad
		return ad[key] if key in ad else dv

	async def put( self, key, data=None, patch=None ) :
		if None == data :
			data = JObj(await self.get(key)).update(patch).D
		self.UD[key] = data
		if len(self.UD) > self.MU :
			await self.sync()
		else :
			await self.write( self.Prefix+".u", JObj(self.UD).stringify('utf8') ) 
		return self

class JSet :
	"""
	s = Set(key="K",atts={"A":1,"B":2}) 
	s.put({"A":2,"B":3,"C":3})
	d = s.get(2)
	"""
	def __init__( self, root, index=".index", attrs={} ) :
		self.Index = UAIndex( root, basename=index )
		self.Attrs = JObj(attrs)

	async def open( self ) :
		await self.Index.prepare()

	async def close( self ) :
		await self.Index.sync()

	async def get( self, key=None, dv=None ) :
		try :
			if None == key :
				return await self.Index.get()
			else :
				return JObj( (await self.Index.read( str(key) ))[0] ).D
		except Exception as x :
			if None == dv :
				raise x
			else :
				return dv

	async def put( self, key, data ) :
		data = JObj(data)
		await self.Index.write( str(key), data.stringify('utf8') )
		await self.Index.put( key, self.Attrs.select(data.D or {}) )

class EffectiveList :
	"""
	tvs = TimeoutList( timeout=30 )
	tvs.put( "user", "123" ) #=> "user"
	tvs.get( "user" ) #=> "123" or None
	"""
	def __init__( self, timeout=300 ) :
		self.KG = KeyCode("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
		self.TO = timeout
		self.DB = {}
	def put( self, value, key=None ) :
		tk = self.KG.create(time()+self.TO)
		key = key or tk
		self.DB[key] = (value,tk)
		return key
	def get( self, key ) :
		self.__recycle__()
		if key in self.DB :
			value=self.DB[key]
			del self.DB[key]
			return value[0]
		else :
			return None
	def __recycle__( self ) :
		now = self.KG.create(time())
		ks = []
		for k in self.DB :
			if self.DB[k][1] < now :
				ks.append(k)
		for k in ks :
			del self.DB[k]
