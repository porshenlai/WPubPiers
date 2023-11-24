def debug( exception ) :
	print( exception )

class XI(Exception) :
	""" 
	try :
		raise XI("EXCEPTION_CODE","Detailed exception information")
	except XI as x :
		...
	"""

	def __init__( self, code, msg="") :
		super().__init__( code, msg )

class XE(Exception) :
	"""
	# ==<< EXCEPTION CODE >>================================================ 
	#  "NOT_FOUND"
	#  "BAD_ARGUMENTS"
	#  "VIOLATION"
	#  "NOT_READY"
	#  "NOT_SUPPORT"
	#  "FAILED"
	# ======================================================================
	try :
		raise XE("EXCEPTION_CODE","Detailed exception information")
	except XE as x :
		...
	"""

	def __init__( self, code, msg="" ) :
		super().__init__( code, msg );

