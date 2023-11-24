"""
asynchronous I/O related function or base classes.

EXAMPLE:

async def sig_handler() :
	async for sig in Async.Signal( captures={SIGINT} ).play() :
		print(sig)

Async.addTask(sig_handler)
Async.play()
"""
import piers,asyncio

def getLoop() :
	"""
	# running loop or current event loop or new event loop
	> Async.getLoop() => asyncio.loop
	"""
	try :
		loop = asyncio.get_running_loop()
	except RuntimeError :
		try :
			loop = asyncio.get_event_loop()
		except RuntimeError :
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
	return loop

def addTask( co=None ) :
	"""
	# RUN ASYNC FUNCTION
	> Async.addTask( async_function() ) => awaitable
	# RUN MULTIPLE ASYNC FUNCTIONS AT THE SAME TIME
	> Async.addTask( [ async_function_1(), async_function_2() ] ) => awaitable
	# CREATE A FUTURE OBJECT TO RECEIVE DATA FROM THE FUTURE
	> Async.addTask( ) => future
	"""
	if not co :
		f = getLoop().create_future()
	elif isinstance( co, list ) :
		f = asyncio.ensure_future(asyncio.gather( *co ))
	else :
		f = asyncio.ensure_future(co)
	return f

__RUNNING_LOOP__ = None

def play() :
	"""
	# WAIT ALL TASKS IN QUEUE UNTIL ALL FINISHED.
	> piers.play()
	"""
	global __RUNNING_LOOP__
	async def playing() :
		while True :
			ts = asyncio.all_tasks()
			ts.remove(asyncio.current_task())
			if not ts : 
				break;
			for t in ts :
				try :
					await asyncio.sleep(1)
				except asyncio.CancelledError :
					piers.debug[1]("[I] piers.play: cancelled")
				except KeyboardInterrupt :
					piers.debug[1]("[I] piers.play: keyboard interrupted")
				except Exception as e :
					piers.trace(e,"piers.play:")
				break
			await asyncio.sleep(0)
	if not __RUNNING_LOOP__ :
		__RUNNING_LOOP__ = getLoop()
	if not __RUNNING_LOOP__.is_running() :
		__RUNNING_LOOP__.run_until_complete(playing())

def cancelTasks() :
	"""
	# CANCEL ALL TASKS IN QUEUE
	> piers.cancelTasks()
	"""
	async def fQ() :
		c = None
		## asyncio.Task.all_tasks()
		for t in asyncio.all_tasks() :
			## asyncio.Task.current_task()
			if t == asyncio.current_task() :
				continue
			if c ==  t :
				await asyncio.sleep(1)
			else :
				c = t
				t.cancel()
	asyncio.ensure_future(fQ())

async def tryWait( rv ) :
	return (await rv) if asyncio.iscoroutine( rv ) else rv

async def sleep( dur ) :
	"""
	# HALT FOR 1.234 SECONDS
	> await piers.sleep(1.234)
	"""
	await asyncio.sleep(dur)

class Reply() :
	"""
	Implementation to wait reply asynchronously

	<<< EXAMPLE >>>
	reply = Reply( timeout=5 )
	await reply.get()

	## Another Loop
	reply.set( 100 )
	"""
	def __init__( self, timeout=None ) :
		self.F = asyncio.get_event_loop().create_future()
		self.TT = addTask( self.__tof__(timeout) ) if timeout else None
	async def __tof__( self, to ) :
		await asyncio.sleep(to)
		self.TT = None
		if not self.F.done() :
			self.F.set_exception(piers.XI("TIMEOUT"))
	async def get( self, timeout_value=piers.XI("TIMEOUT")) :
		try :
			timeout_value = await self.F
		except Exception :
			if isinstance(timeout_value,Exception) :
				raise timeout_value
		return timeout_value
	def set( self, value ) :
		if not self.F.done() :
			self.F.set_result(value)
		if self.TT :
			self.TT.cancel()
			self.TT = None

	def renew( oR, timeout=5 ) :
		"""
		Renew reply object
		"""
		if oR and not oR.F.done() :
			oR.F.set_exception(piers.XI("TIMEOUT"))
		return Reply(timeout=timeout)

class Queue() :
	"""
	Basic Queue Implementation for Asynchronous I/O

	<<< EXAMPLE >>>
	q = Queue( queuelen=1024 )
	async for d in q.play( timeout=3 ) :
		...
	## another loop
	if q.isActive() :
		q.push(d)
		await q.close()
	"""
	def __init__( self, queuelen=1024 ) :
		self.Q = []
		self.QL = queuelen
		self.W = None
	def isActive( self ) :
		return self.QL > 0
	def push( self, pl=None ) :
		if pl :
			self.Q.append(pl)
		if len(self.Q) > self.QL :
			piers.debug[0](f"Drop {self.Q.pop(0)} / {self.QL}")
		if self.W :
			self.W.set(True)
			self.W = None
	async def play( self, timeout=None ) :
		while self.QL :
			while self.Q :
				d = self.Q.pop(0)
				yield d
			if self.W :
					self.W.set(False)
			self.W = w = Reply(timeout=timeout)

			if self.QL :
				await w.get()
	async def close( self ) :
		self.QL = 0
		if self.W :
			self.W.set(False)
			self.W = None

class QDrive() :
	"""
	class XXX( QDrive ) :
		def __init__( self, retry=None, name="Name" ) :
			super().__init__( retry=None, name="Name" )
			...
		async def __start__( self ) :
			... self.Queue.push(s,c,d) ...
		async def __stop__( self ) :
			...
	x = XXX({...})
	async for s,c,d in x.play()
		if (c,d) == ("I","Ready") : ...
		if (c,d) == ("I","Closed") : ...
		if c == "D" : ...
	await x.put(...)
	await x.stop()
	"""
	def __init__( self, retry=None, name="NoName" ) :
		self.Name = name
		self.Retry = retry
		self.Queue = Queue()
	async def __start__( self ) :
		raise piers.XE("Please implement __start__ to start device")
	async def __stop__( self ) :
		raise piers.XE("Please implement __stop__ to stop device")
	async def play( self, timeout=None ) :
		state = 1
		while self.Queue.isActive() :
			if 0 == state : # playing
				async for scd in self.Queue.play(timeout=timeout) :
					yield scd
				yield self,"I","Closed"
				state = 3
			if 3 == state : # restarting
				if None == self.Retry : state = 2
			else :
				await sleep(self.Retry or 0)
			if state&1 : # init | restarting
				try :
					await self.__start__()
					state = 0
					yield self,"I","Ready"
				except Exception as e :
					piers.trace(e)
					state = 3
					yield self,"I","Failed to start / "+str(e)
			if 2 == state : # terminated
				await self.Queue.close()
	async def put( self, va ) :
		raise NotImplementedError
	async def stop( self ) :
		self.Retry = None
		try :
			await self.__stop__()
			await self.Queue.close()
		except Exception as x :
			pass

class SignalHub( Queue ) :
	"""
	Signal handler implementation

	<<< EXAMPLE >>>
	sh = Signal()
	sh.savePID("/tmp/test.pid");
	async def handler( ... )
		async for s in sh.play() :
			print( s )
		await sh.close();
	"""
	from signal import signal as _register_, SIGINT

	def __init__( self, captures=None ) :
		super().__init__()
		def __on_signal__( signal, stacks ) :
			self.push( signal )
		for sig in captures or {SignalHub.SIGINT} :
			SignalHub._register_(sig,__on_signal__)
	def savePID( self, fpath=None ) :
		from os import getpid
		pid = getpid()
		if fpath :
			with open(fpath,"w") as fo :
				fo.write( str(pid) )
		return pid

class Filter :
	def __init__( self, wrap ) :
		self.U, wrap.U = wrap.U, self
	async def __dec__( self ) :
		return await self.U.__dec__( )
	async def __enc__( self, data ) :
		return await self.U.__enc__( data )

class StringFilter( Filter ) :
	async def __dec__(self) :
		return (await super().__dec__()).decode("utf8")
	async def __enc__(self,data) :
		return await super().__enc__(data.encode("utf8"))

class Device( Filter ) :
	def __init__( self ) :
		self.U = self;
		super().__init__( self )
		self.Queue = None
		self.__QBuf__ = ""
	async def __dec__( self ) :
		r, self.__QBuf__ = self.__QBuf__, ""
		return r
	async def __enc__( self, data ) : #*
		return await print( data )
	async def __start__( self ) : #*
		pass
	async def play( self ) :
		if not self.Queue : self.Queue = Queue()
		await self.__start__()
		async for s,c,d in self.Queue.play() :
			if "D" == c :
				self.__QBuf__ = d;
				d = await self.U.__dec__()
			if d : yield s,c,d
	async def put( self, data ) :
		return await self.U.__enc__( data )
