import re
import socket
import os
import shutil
import time
import threading
import subprocess
import new
from cacheDecorators import *
from filesystem import *


class UniverseSet:
	'''
	super simple helper class for when you want a set that includes everything in the universe
	'''
	def add( self, item ): pass
	def remove( self, item ): pass
	def __contains__( self, item ):
		return True


def removeDupes( iterable ):
	'''
	will return an iterable of the same type supplied (must be mutable) with all duplicate entries
	removed, while preserving item order.  eg: removeDupes( [ 1, 5, 2, 2, 4, 5, 8 ] ) will return
	the list: [1, 5, 2, 4, 8]
	'''
	unique = set()
	newIterable = iterable.__class__()
	for item in iterable:
		if item not in unique: newIterable.append(item)
		unique.add(item)

	return newIterable


def iterBy( iterable, count ):
	'''
	returns an generator which will yield "chunks" of the iterable supplied of size "count".  eg:
	for chunk in iterBy( range( 7 ), 3 ): print chunk

	results in the following output:
	[0, 1, 2]
	[3, 4, 5]
	[6]
	'''
	cur = 0
	i = iter( iterable )
	while True:
		try:
			toYield = []
			for n in range( count ): toYield.append( i.next() )
			yield toYield
		except StopIteration:
			if toYield: yield toYield
			break


def unzip( iterable ):
	#assume the first item is representative of all items
	try:
		representativeItem = iterable[ 0 ]
	except IndexError: return

	sz = len( representativeItem )
	yieldLists = [ [] for n in range( sz ) ]
	for item in iterable:
		for idx, i in enumerate( item ):
			yieldLists[ idx ].append( i )

	return yieldLists


def encodeString( theString ):
	ESC_CHARS = ['\\', '\"', '\n', '\r', '\t']
	REPL_CHARS = [r'\\', r'\"', r'\n', r'\r', r'\t']
	for e, r in zip(ESC_CHARS, REPL_CHARS):
		theString = theString.replace(e, r)

	return theString


def getNearestExistingDir( path ):
	'''
    returns the nearest existing path
    '''
	if os.path.exists(path):
		return path

	existingPath = path
	while not os.path.exists(existingPath):
		existingPath = resolvePath(existingPath +"/../" )

	return existingPath


def addSubPathsToSearch():
	'''
    iterates through all sys.path paths and adds all subdirectories.  this doesn't
    happen automatically because it delays python startup time.

    if you're nesting	tools deeply in the tree, you can call this function to
    recursively add subdirs	to the search path, and then call your function
    '''
	import sys
	allSubDirs = []
	for p in sys.path:
		p = p.strip()
		if p == '': continue
		for dirpath,dirname,filenames in os.walk(p):
			allSubDirs.append(dirpath)

	sys.path.extend(allSubDirs)


def sendToMaya( cmd ):
	defaultMayaCommandPort = 12123

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(("127.0.0.1", defaultMayaCommandPort))
	sock.send(cmd)
	print sock.recv(1024*8)
	sock.close()


class ProcessQueue(threading.Thread):
	'''
    creates a queue object for executing multiple spawnProcess methods one after another, with an optional
    callback to be run once the queue is empty.  the queue is processed in ascending (FIFO) order
    '''
	def __init__( self, callback=None, *cbArgs, **cbKwargs ):
		threading.Thread.__init__(self)
		self.queue = []
		self.running = False
		self.callback = callback
		self.callbackArgs = cbArgs
		self.callbackKwargs = cbKwargs
	def __len__( self ):
		return len(self.queue)
	def __str__( self ):
		return '\n'.join(map(str, self.queue))
	__repr__ = __str__
	def append( self, cmdStr, cwd ):
		'''
        appends a new process to the queue - the cmdStr is the command as it would be typed in a console, and
        cwd is the current working directory - ie: the directory you would otherwise run the command from
        '''
		self.queue.append((cmdStr, cwd))
	def setCallback( self, callback, *cbArgs, **cbKwargs ):
		self.callback = callback
		self.callbackArgs = cbArgs
		self.callbackKwargs = cbKwargs
	def getCallback( self ):
		return (self.callback, self.callbackArgs, self.callbackKwargs)
	def run( self ):
		self.running = True
		self.count = len(self)

		while True:
			try:
				cmdStr, cwd = self.queue.pop(0)
				process = spawnProcess(cmdStr, cwd)
				process.wait()
				print 'done', cmdStr
			except IndexError: break

		try:
			self.callback(*self.callbackArgs, **self.callbackKwargs)
			print 'SUCCESS executing callback\n%s(*%s, *%s)' % (self.callback.__name__, str(self.callbackArgs), str(self.callbackKwargs))
		except TypeError: pass
	def progress( self ):
		'''
        returns the current progress of the thread - this is a tuple of remaining processes/total processes
        '''
		return len(self), self.count


def spawnProcess( cmd, workingDir=None, processEndCallback=None, **kw ):
	if workingDir is not None:
		Path.setcwd( workingDir )
	process = subprocess.Popen( str(cmd), **kw )

	return process


def exploreTo( aPath ):
	spawnProcess( 'explorer /n,/e,/select,"%s"' % aPath.resolve().asNative() )


def cmdTo( aPath ):
	spawnProcess( 'cmd /K cd "%s"' % aPath.resolve().asNative() )


def p4To( aPath ):
	spawnProcess( 'p4win -q -s "%s"' % aPath.resolve().asNative() )


class Singleton(object) :
	def __new__(cls, *p, **k):
		if not '_the_instance' in cls.__dict__:
			cls._the_instance = super(Singleton, cls).__new__(cls)
		return cls._the_instance


class Callback(object):
	'''
	stupid little callable object for when you need to "bake" temporary args into a
	callback - useful mainly when creating callbacks for dynamicly generated UI items
	'''
	def __init__( self, func, *args, **kwargs ):
		self.func = func
		self.args = args
		self.kwargs = kwargs
	def __call__( self, *args ):
		return self.func(*self.args, **self.kwargs)


import new
def reloadAll( module ):
	'''
    recursively reloads a module and all sub-modules.  it doesn't check for cyclical imports, but it
    does stop after 250 reloaded modules
    '''
	if not isinstance(module,new.module):
		print "reloadAll() argument must be a module"
		return

	reload(module)
	print 'reloading the module',module.__name__
	children = module.__dict__.values()
	n = 0
	while n<200:
		try:
			next = children.pop()
			if isinstance(next,new.module):
				children.extend( next.__dict__.values() )
				reload(next)
				print 'reloading the module',next.__name__
				n += 1
		except ImportError:
			pass
		except IndexError:
			break

	print 'finished'


#end