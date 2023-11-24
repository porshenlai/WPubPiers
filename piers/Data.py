# python3 -m pip install PyCryptodome

from json import loads as __JSON2Obj__, dumps as __Obj2JSON__
from hashlib import sha256 as __sha256__
from secrets import token_bytes as createSecretBytes
from time import time
from os import path as Path
from re import compile as newRE
from datetime import datetime
from base64 import b64encode as __encb64__, b64decode as __decb64__, encodebytes as __encbytes__, decodebytes as __decbytes__

def sha256( s, b64=True ) :
	"""
	sha256( "Hello", b64=True )
	sha256( ["Hello",b"World"], b64=True )
	sha256( ["Hello",b"World"], b64=False )
	"""
	sha = __sha256__()
	for i in s if list == type(s) else [s] :
		sha.update( i.encode('utf8') if str == type(i) else i )
	s = sha.digest()
	return __encb64__(s).decode('ascii') if b64 else s

class LatestNCache :
	def __init__( self, size=16 ) :
		self.Size = size;
		self.DB = {}
	def _on_cache_miss_( self, key ) :
		return None
	def get( self, key ) :
		v = None
		try :
			v = self.DB[key]
			del self.DB[key]
		except KeyError :
			v = self._on_cache_miss_( key )
			while len(self.DB) >= self.Size :
				for k in self.DB.keys() :
					del self.DB[ k ]
					break
		finally :
			self.DB[key] = v
		return v

class JObj :
	"""
	## Source
	o = JObj( {OBJECT} )
	o = JObj.load( filepath, dv={} )
	## Editing Chain
	o.get(["A","B"],dv=100) => self ## {"A":{"B":456}} => 456, {"A":30} => 100
	o.put(["A","B"],999) => self ## {"A":{"B":456}} => {"A":{"B":999}}
	o.assign( {OBJECT} ) => self ## {"A":123,"B":{"C":456}}+{"B":{"D":789}}) => {"A":123,"B":{"D":789}}
	o.update( {OBJECT} ) => self ## {"A":123,"B":{"C":456}}+{"B":{"D":789}}) => {"A":123,"B":{"C":456,"D":789}}
	o.remove(["A","B"])
	## Sinker
	o.stringify( ) => "{...}"
	o.save( "FILENAME" )
	"""
	def __init__( self, data ) :
		if bytes == type(data) :
			data = data.decode('utf8')
		if str == type(data) :
			def ih(e) :
				try :
					if e["type"] == "B64" :
						return __decb64__(e["data"])
					if e["type"] == "Buffer" :
						return bytes(e["data"])
				except :
					pass
				return e
			data = __JSON2Obj__(data if str == type(data) else data.decode("utf8"),object_hook=ih)
		self.D = data

	def load( path, dv=None ) :
		try :
			with open( path, "r" ) as fi :
				return JObj( fi.read() )
		except Exception as x :
			if None != dv :
				return JObj( dv )
			raise x

	def put( self, path, value ) :
		o = self.D
		for i in path[:-1] :
			if i not in o:
				o[i] = {};
			o = o[i]
		o[path[-1]] = value
		return self

	def remove( self, path ) :
		h,o = [],self.D
		for i in path :
			if i in o :
				if dict == type(o[i]) or list == type(o[i]) :
					h.append((o,i))
					o = o[i]
					continue
				else :
					del o[i]
			break
		while h :
			o,i = h.pop()
			if o[i] :
				break
			else :
				del o[i]
		return self

	def assign( self, a ) :
		b = self.D
		for k in a :
			b[k] = a[k]
		return self

	def update( self, a ) :
		return JObj.__update__( self.D, a )

	def select( self, v ) :
		r = {}
		for n in self.D :
			r[n] = v[n] if n in v else self.D[n]
		return r

	def get( self, path, dv=None ) :
		o = self.D
		for i in path :
			if i not in o:
				return dv
			o = o[i]
		return o

	def stringify( self, codec=None ) :
		def oh(e) :
			if bytes == type(e) :
				return {"type":"B64","data":__encb64__(e).decode('ascii')}
			return {"type":str(type(e))}
		r = __Obj2JSON__( self.D, default=oh, ensure_ascii=False )
		return r.encode(codec) if codec else r

	def save( self, path ) :
		with open( path, "w" ) as fo :
			return fo.write( self.stringify() )

	def __update__( b, a ) :
		for i in a :
			if i in b :
				if dict == type(a[i]) :
					JObj.__update__(b[i],a[i])
				elif list == type(a[i]) :
					if a[i] and a[i][0] == None :
						b[i] += a[i][1:]
					else :
						b[i] = a[i]
				else :
					b[i] = a[i]
			else :
				b[i] = a[i];
		return b

class Bytes :
	def formatHexString( bs, lc=None ) :
		if bytes == type(bs) :
			if lc :
				s = []
				for i in range(0,len(bs),lc) :
					s.append(bs[i:i+lc])
			else :
				s = [bs]
		else :
			s = bs
		r = []
		RE_SEG = createRE(r"(..)")
		for bs in s :
			r.append(RE_SEG.sub(r"\1 ",bs.hex()).strip())
		return r

class Cache :
	"""
	c = Cache(8)
	c.put(1,"A")
	c.get(1) => "A" or None
	"""
	def __init__( self, size=8 ) :
		self.Q = []
		self.C = {}
		self.Z = size
	def get( self, key ) :
		r = None
		if key in self.C :
			r = self.C[key]
			self.Q.remove(key)
			self.Q.append(key)
		return r
	def put( self, key, data ) :
		if not self.get(key) :
			self.C[key] = data
			self.Q.append(key)
		while len(self.Q) > self.Z :
			del self.C[self.Q.pop(0)]

class KeyCode :
	"""
	kc = KeyCode("0123456789abcdefghijklmnopqrstuvwxyz") # base 36
	code = kc.create(100,width=0)
	value = kc.solve(code)
	"""
	BASE16 = "0123456789ABCDEF"
	BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"
	def __init__( self, ks=None ) :
		self.Ks = ks or KeyCode.BASE36
	def create( self, seed, width=0 ) :
		seed = int(seed) if seed else int(time()*1000000) 
		l,r,k = len(self.Ks), "", seed
		if width :
			for i in range(0,width) :
				r,k = self.Ks[k%l]+r, int(k/l)
		else :
			while k > 0 :
				r,k = self.Ks[k%l]+r, int(k/l)
		return r
	def solve( self, key ) :
		l,r = len(self.Ks), 0
		for c in key :
			r = r*l + self.Ks.find(c)
		return r

class TSKey :
	"""
	k = TSKey( secret=SECRET+PATH )
	key = k.create( 300 )
	k.verify( key ) => True or False
	"""
	def __init__( self, secret=None ) :
		if not secret :
			secret = createSecretBytes()
		self.SS = secret
	def create( self, tmax ) :
		ts = int(time())+tmax
		ts = ts.to_bytes(4,byteorder="big")
		return __encb64__(ts+sha256(ts+self.SS,b64=False)).decode('ascii')
	def verify( self, key ) :
		key = __decb64__(key.encode('ascii'))
		if key[0:4]+sha256(key[0:4]+self.SS,b64=False) == key :
			return int(time()) < int.from_bytes(key[0:4],byteorder="big")
		return False

class DTKey :
	"""
	k = DTKey( dt=int(time()*1000), uid=-1 )
	k.toString()
	k.toDate()
	"""
	UID = 166
	def __init__( this, dt=None, uid=-1 ) :
		dt = dt or int(time()*1000)
		if str == type(dt) :
			bc = KeyCode()
			this.D = bc.solve(dt[0:4])
			this.S = bc.solve(dt[4:8])
			this.U = bc.solve(dt[8:12])
			this.M = int(this.U/167)
			this.U = this.U%167
		else :
			this.M = dt%1000
			this.S = int(dt/1000)
			this.D = int(this.S/86400)
			this.S = this.S%86400
			if uid < 0 :
				uid = DTKey.UID = (1+DTKey.UID)%167;
			this.U = uid
	def toString( this ) :
		bc = KeyCode()
		return bc.create(this.D,width=4)+bc.create(this.S,width=4)+bc.create(this.M*167+this.U,width=4);
	def toDate( this ) :
		return datetime.utcfromtimestamp(86400*this.D+this.S+(float(this.M)/1000));

try :
	from Crypto.PublicKey import RSA as __RSA__
	from Crypto.Cipher import PKCS1_v1_5 as __RSACipher__
	class RSA :
		"""
		user = "porshenlai"
		rsa = RSA(user+".pem")
		print( { "U":user, "K":rsa.getPublicKey() } )
		cipher = rsa.encrypt({"A":123,"B":456})
		print( cipher )
		message = JObj( rsa.decrypt( cipher ) ).D
		print( message )
		"""
		def __init__( self, PEMPath=None, PEMString=None ) :
			key = None
			try :
				if PEMPath :
					try :
						with open( PEMPath, "rb" ) as fo :
							PEMString = fo.read( )
							PEMPath = None
					except :
						pass
				if PEMString :
					key = __RSA__.importKey( PEMString )
			except :
				pass

			self.Key = key or __RSA__.generate( 2048 );
			if PEMPath :
				with open( PEMPath, "wb" ) as fo :
					fo.write(self.Key.exportKey(format="PEM"))

		def getPublicKey( self, PEM=False ) :
			if PEM : return self.Key.publickey().exportKey(format="PEM").decode('utf8');
			pemMark = newRE("-----(.*)-----")
			pem = self.Key.publickey().exportKey(format="PEM")
			r = ""
			for l in pem.split("\n") :
				if not pemMark.match(l) :
					r += l
			return r

		def encrypt( self, message ) :

			if dict == type(message) :
				message = JObj(message).stringify()
			if str == type(message) :
				message = message.encode('utf8')
			return __encb64__( __RSACipher__.new(self.Key).encrypt(message) ).decode()

		def decrypt( self, cipher ) :
			if str == type(cipher) :
				cipher = cipher.encode('utf8')
			cipher = __decb64__( cipher )
			return __RSACipher__.new(self.Key).decrypt(cipher,None)

	from Crypto.Cipher import AES as __AES__
	class AES :
		"""
		c = AES( b"Secret", NoHashSecret=False )
		code = c.encrypt( "Message" )
		c.decrypt( code ) #=> "Message"
		c.save( "test.aes", "HELLO " )
		c.append( "test.aes", "WORLD" )
		print( c.load( "test.aes" ) )
		"""
		def __init__( self, secret_key, NoHashSecret=False ) :
			self.secret = secret_key if NoHashSecret else sha256( secret_key, b64=False )
		def __enc__( self, bs ) :
			bs = bs.encode('utf8') if str == type(bs) else bs
			while len(bs)%16 != 0:
				bs += bytes( (16-len(bs)%16)*chr(16-len(bs)%16), "ascii" )
			return __AES__.new( self.secret, __AES__.MODE_ECB ).encrypt( bs )
		def __dec__( self, code ) :
			text = __AES__.new( self.secret, __AES__.MODE_ECB ).decrypt(code)
			return text[:-text[-1]]

		def encrypt( self, bs ) :
			r = __encbytes__( self.__enc__(bs) )
			return r[0:-1] if r.endswith(b'\n') else r
		def decrypt( self, code ) :
			return self.__dec__(__decbytes__( code ))

		def save( self, path, bs, binary=True ) :
			with open(path,"wb") as w :
				w.write(self.__enc__(bs) if binary else self.encrypt(bs))
		def append( self, path, bs, binary=True ) :
			bs = bs.encode('utf8') if str == type(bs) else bs
			try :
				bs = self.load(path,binary=binary) + bs 
			except Exception as x :
				print(x)
			self.save(path,bs,binary=binary)
		def load( self, path, binary=True ) :
			with open(path,"rb") as r :
				return self.__dec__(r.read()) if binary else self.decrypt(r.read())
except Exception as x :
	print(x)
	print("Crypto module required.\nFor Posix System, please apt install python3-pycryptodome.\nFor MSWindows System, please python3 -m pip install pycrytodome.\n")
	from sys import exit
	exit(1)
