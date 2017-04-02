'''
'''


def d_initCache(f):
	def __init__(*args, **kwargs):
		self = args[0]
		self._CACHE_ = {}
		return f(*args, **kwargs)
	return __init__


def d_cacheValue(f):
	fname = f.func_name
	def cachedRetValFunc(*args, **kwargs):
		self = args[0]
		try:
			return self._CACHE_[fname]
		except KeyError:
			val = f(*args, **kwargs)
			self._CACHE_[fname] = val
			return val
		#it may be a parent class has caching turned on, but the child class does not...
		except AttributeError:
			return f(*args, **kwargs)
	cachedRetValFunc.func_name = fname
	return cachedRetValFunc


def d_cacheValueWithArgs(f):
	fname = f.func_name
	def cachedRetValFunc(*args, **kwargs):
		self = args[0]
		funcArgsTuple = (fname,)+tuple(args[1:])
		try:
			return self._CACHE_[funcArgsTuple]
		except KeyError:
			val = f(*args, **kwargs)
			self._CACHE_[funcArgsTuple] = val
			return val
		except TypeError:
			return f(*args, **kwargs)
		except AttributeError:
			return f(*args, **kwargs)
	cachedRetValFunc.func_name = fname
	return cachedRetValFunc


def d_resetCache(f):
	fname = f.func_name
	def resetCacheFunc(*args, **kwargs):
		self = args[0]
		retval = f(*args, **kwargs)
		try:
			self._CACHE_.clear()
			return retval
		except AttributeError:
			return retval
	resetCacheFunc.func_name = fname
	return resetCacheFunc


#end