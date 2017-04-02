import cPickle, threading, time
import os, sys, re, shutil, stat, inspect


class GoodException(Exception):
	'''
	good exceptions are just a general purpose way of breaking out of loops and whatnot.  basically anytime an exception is
	needed to control code flow and not indicate an actual problem using a GoodException makes it a little more obvious what
	the code is doing in the absence of comments
	'''
	pass

BreakException = GoodException


MAIL_SERVER = 'exchange'
DEFAULT_AUTHOR = 'default_username@your_domain.com'

def removeDupes( iterable ):
	'''
	'''
	unique = set()
	newIterable = iterable.__class__()
	for item in iterable:
		if item not in unique: newIterable.append(item)
		unique.add(item)

	return newIterable


def findMostRecentDefitionOf( variableName ):
	'''
	'''
	try:
		fr = inspect.currentframe()
		frameInfos = inspect.getouterframes( fr, 0 )

		#in this case, walk up the caller tree and find the first occurance of the variable named <variableName>
		for frameInfo in frameInfos:
			frame = frameInfo[0]

			if var is None:
				try:
					var = frame.f_locals[ variableName ]
					return var
				except KeyError: pass

				try:
					var = frame.f_globals[ variableName ]
					return var
				except KeyError: pass

	#NOTE: this method should never ever throw an exception...
	except: pass


def reportUsageToAuthor( author=None, payloadCB=None ):
	'''
	when called, this method will fire of a useage report email to whoever has marked themselves as the __author__ of the tool
	the call was made from.  if no author is found then an email is sent to the DEFAULT_AUTHOR
	'''
	additionalMsg = ''
	try:
		additionalMsg = payloadCB()
	except: pass

	try:
		fr = inspect.currentframe()
		frameInfos = inspect.getouterframes( fr, 0 )

		dataToSend = []
		if author is None:
			#set the default - in case we can't find an __author__ variable up the tree...
			author = DEFAULT_AUTHOR

		#in this case, walk up the caller tree and find the top most __author__ variable definition
		for frameInfo in frameInfos:
			frame = frameInfo[0]
			dataToSend.append( '%s:  %s' % (Path( frameInfo[1] ), frameInfo[3]) )

			if author is None:
				try:
					author = frame.f_globals['__author__']
				except KeyError: pass

				try:
					author = frame.f_locals['__author__']
				except KeyError: pass

		import smtplib
		envDump = '\ncontent: %s\nproject: %s\n' % (content(), project())
		subject = '[using] %s' % str( Path( frameInfos[1][1] ).name() )
		msg = u'Subject: %s\n\n%s\n\n%s\n\n%s' % (subject, '\n'.join( map(str, dataToSend) ), envDump, additionalMsg)

		svr = smtplib.SMTP( MAIL_SERVER )
		svr.sendmail(os.environ['USERNAME'], author, msg)
	#NOTE: this method should never ever throw an exception...  its purely a useage tracking tool and if it fails, it should fail invisibly...
	except: pass


#try to import the windows api - this may fail if we're not running on windows
try:
	import win32con, win32api
except ImportError: pass


########### PATH MANIPULATION ###########
#set the pickle protocol to use
PICKLE_PROTOCOL = 2

#set some variables for separators
NICE_SEPARATOR = '/'
NASTY_SEPARATOR = '\\'
NATIVE_SEPARATOR = (NICE_SEPARATOR, NASTY_SEPARATOR)[ os.name == 'nt' ]
PATH_SEPARATOR = '/' #(NICE_SEPARATOR, NASTY_SEPARATOR)[ os.name == 'nt' ]
OTHER_SEPARATOR = '\\' #(NASTY_SEPARATOR, NICE_SEPARATOR)[ os.name == 'nt' ]
UNC_PREFIX = PATH_SEPARATOR * 2


def cleanPath( pathString ):
	'''
	will clean out all nasty crap that gets into pathnames from various sources.
	maya will often put double, sometimes triple slashes, different slash types etc
	'''
	path = str( pathString ).strip().replace( OTHER_SEPARATOR, PATH_SEPARATOR )
	isUNC = path.startswith( UNC_PREFIX )
	while path.find( UNC_PREFIX ) != -1:
		path = path.replace( UNC_PREFIX, PATH_SEPARATOR)

	if isUNC:
		path = PATH_SEPARATOR + path

	return path


ENV_REGEX = re.compile( "\%[^%]+\%" )
def resolve( path, envDict=None, raiseOnMissing=False ):
	'''
	recursively expands all environment variables and '..' tokens in a pathname
	'''
	if envDict is None:
		envDict = os.environ

	#first resolve any env variables
	global ENV_REGEX
	matches = re.findall( ENV_REGEX, path )
	missingVars = set()
	while matches:
		for match in matches:
			try:
				path = str( path ).replace( match, envDict[ match[ 1:-1 ] ] )
			except KeyError:
				if raiseOnMissing: raise
				missingVars.add( match )
		matches = set( re.findall( ENV_REGEX, path ) )

		#remove any variables that have been found to be missing...
		[ matches.remove( missing ) for missing in missingVars ]

	#now resolve any subpath navigation
	path = str( path ).replace( OTHER_SEPARATOR, PATH_SEPARATOR )
	isUNC = path.startswith( UNC_PREFIX )
	if isUNC:
		path = path[ 2: ]

	pathToks = path.split( PATH_SEPARATOR )
	pathsToUse = []
	for n, tok in enumerate( pathToks ):
		if tok == "..":
			try: pathsToUse.pop()
			except IndexError:
				if raiseOnMissing: raise
				pathsToUse = pathToks[ n: ]
				break
		else:
			pathsToUse.append( tok )

	#finally convert it back into a path
	path = PATH_SEPARATOR.join( pathsToUse )
	if isUNC:
		return UNC_PREFIX + path

	return path

resolvePath = resolve


sz_BYTES = 0
sz_KILOBYTES = 1
sz_MEGABYTES = 2
sz_GIGABYTES = 3

class Path(str):
	__CASE_MATTERS = os.name != 'nt'
	def __new__( cls, path='', caseMatters=None, envDict=None ):
		if path is None:
			path = ''

		resolvedPath = resolve( cleanPath( path ), envDict )
		new = str.__new__( cls, resolvedPath )
		new.isUNC = resolvedPath.startswith( UNC_PREFIX )
		new.hasTrailing = resolvedPath.endswith( PATH_SEPARATOR )

		return new
	def __init__( self, path='', caseMatters=None, envDict=None ):
		'''
		if case doesn't matter for the path instance you're creating, setting caseMatters
		to False will do things like caseless equality testing, caseless hash generation
		'''

		self._passed = path

		#case sensitivity, if not specified, defaults to system behaviour
		if caseMatters is not None:
			self.__CASE_MATTERS = caseMatters
	@classmethod
	def Temp( cls ):
		'''
		returns a temporary filepath - the file should be unique (i think) but certainly the file is guaranteed
		to not exist
		'''
		import datetime, random
		def generateRandomPathName():
			now = datetime.datetime.now()
			rnd = '%06d' % (abs(random.gauss(0.5, 0.5)*10**6))
			return '%TEMP%'+ PATH_SEPARATOR +'TMP_FILE_%s%s%s%s%s%s%s%s' % (now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond, rnd)

		randomPathName = cls(generateRandomPathName())
		while randomPathName.exists:
			randomPathName = cls(generateRandomPathName())

		return randomPathName
	def __nonzero__( self ):
		if self.strip() == '':
			return False

		if self.strip() == PATH_SEPARATOR:
			return False

		return True
	def __add__( self, other ):
		return self.__class__( '%s%s%s' % (self, PATH_SEPARATOR, other), self.__CASE_MATTERS )
	#the / or + operator both concatenate path tokens
	__div__ = __add__
	def __radd__( self, other ):
		return self.__class__( other, self.__CASE_MATTERS ) + self
	__rdiv__ = __radd__
	def __getitem__( self, item ):
		toks = self.split()
		return toks[ item ]
	def __getslice__( self, a, b ):
		toks = self.split()
		newPath = PATH_SEPARATOR.join( toks[ a:b ] ) + ('', PATH_SEPARATOR)[ self.hasTrailing ]

		return self.__class__( newPath, self.__CASE_MATTERS )
	def __len__( self ):
		if not self:
			return 0

		return len( self.split() )
	def __contains__( self, item ):
		if not self.__CASE_MATTERS:
			return item.lower() in [ s.lower() for s in self.split() ]

		return item in self.split()
	def __hash__( self ):
		'''
		the hash for two paths that are identical should match - the most reliable way to do this
		is to use a tuple from self.split to generate the hash from
		'''
		if not self.__CASE_MATTERS:
			return hash( tuple( [ s.lower() for s in self.split() ] ) )

		return hash( tuple( self.split() ) )
	def _toksToPath( self, toks ):
		'''
		given a bunch of path tokens, deals with prepending and appending path
		separators for unc paths and paths with trailing separators
		'''
		if self.isUNC:
			toks = ['', ''] + toks

		if self.hasTrailing:
			toks.append( '' )

		return self.__class__( PATH_SEPARATOR.join( toks ), self.__CASE_MATTERS )
	def resolve( self, envDict=None, raiseOnMissing=False ):
		if envDict is None:
			return self
		else:
			return Path( self.unresolved(), self.__CASE_MATTERS, envDict )
	def unresolved( self ):
		return self._passed
	def isEqual( self, other ):
		'''
		compares two paths after all variables have been resolved, and case sensitivity has been
		taken into account - the idea being that two paths are only equal if they refer to the
		same filesystem object.  NOTE: this doesn't take into account any sort of linking on *nix
		systems...
		'''
		other = Path( other, self.__CASE_MATTERS )

		if self.__CASE_MATTERS:
			return str( self ) == str( other )
		else:
			return str.lower( self ) == str.lower( other )
	__eq__ = isEqual
	def __ne__( self, other ):
		return not self.isEqual( other )
	def doesCaseMatter( self ):
		return self.__CASE_MATTERS
	@classmethod
	def getcwd( cls ):
		'''
		returns the current working directory as a path object
		'''
		return cls( os.getcwd() )
	@classmethod
	def setcwd( cls, path ):
		'''
		simply sets the current working directory - NOTE: this is a class method so it can be called
		without first constructing a path object
		'''
		newPath = cls( path )
		try:
			os.chdir( newPath )
		except WindowsError: return None

		return newPath
	putcwd = setcwd
	def getStat( self ):
		try:
			return os.stat( self )
		except:
			#return a null stat_result object
			return os.stat_result( [ 0 for n in range( os.stat_result.n_sequence_fields ) ] )
	stat = property( getStat )
	def isAbs( self ):
		try:
			return os.path.isabs( str( self ) )
		except: return False
	def abs( self ):
		'''
		returns the absolute path as is reported by os.path.abspath
		'''
		return self.__class__( os.path.abspath( str( self ) ) )
	def split( self ):
		'''
		splits a path into directory/file tokens
		'''
		isUNC = self.isUNC
		newPath = str.replace( self, UNC_PREFIX, '' )
		if newPath.startswith( PATH_SEPARATOR ):
			newPath = newPath[1:]

		hasTrailing = newPath.endswith( PATH_SEPARATOR )
		if hasTrailing:
			newPath = newPath[ :-1 ]

		toks = newPath.split( PATH_SEPARATOR )

		return toks
	def asDir( self ):
		'''
		makes sure there is a trailing / on the end of a path
		'''
		if self.hasTrailing:
			return self

		return self.__class__( '%s%s' % (self, PATH_SEPARATOR), self.__CASE_MATTERS )
	asdir = asDir
	def asFile( self ):
		'''
		makes sure there is no trailing path separators
		'''
		if not self.hasTrailing:
			return self

		return self.__class__( str( self )[ :-1 ], self.__CASE_MATTERS )
	asfile = asFile
	def isDir( self ):
		'''
		bool indicating whether the path object points to an existing directory or not.  NOTE: a
		path object can still represent a file that refers to a file not yet in existence and this
		method will return False
		'''
		return os.path.isdir( self )
	isdir = isDir
	def isFile( self ):
		'''
		see isdir notes
		'''
		return os.path.isfile( self )
	isfile = isFile
	def getReadable( self ):
		'''
		returns whether the current instance's file is readable or not.  if the file
		doesn't exist False is returned
		'''
		try:
			s = os.stat( self )
			return s.st_mode & stat.S_IREAD
		except:
			#i think this only happens if the file doesn't exist
			return False
	def setWritable( self, state=True ):
		'''
		sets the writeable flag (ie: !readonly)
		'''
		try:
			setTo = stat.S_IREAD
			if state:
				setTo = stat.S_IWRITE

			os.chmod(self, setTo)
		except: pass
	def getWritable( self ):
		'''
		returns whether the current instance's file is writeable or not.  if the file
		doesn't exist True is returned
		'''
		try:
			s = os.stat( self )
			return s.st_mode & stat.S_IWRITE
		except:
			#i think this only happens if the file doesn't exist - so return true
			return True
	def getExtension( self ):
		'''
		returns the extension of the path object - an extension is defined as the string after a
		period (.) character in the final path token
		'''
		endTok = self[ -1 ]
		idx = endTok.rfind( '.' )
		if idx == -1:
			return ''

		return endTok[ idx+1: ] #add one to skip the period
	def setExtension( self, xtn=None, renameOnDisk=False ):
		'''
		sets the extension the path object.  deals with making sure there is only
		one period etc...

		if the renameOnDisk arg is true, the file on disk (if there is one) is
		renamed with the new extension
		'''
		if xtn is None:
			xtn = ''

		#make sure there is are no start periods
		while xtn.startswith( '.' ):
			xtn = xtn[ 1: ]

		toks = self.split()
		endTok = toks[ -1 ]
		idx = endTok.rfind( '.' )
		name = endTok
		if idx >= 0:
			name = endTok[ :idx ]

		if xtn: newEndTok = '%s.%s' % (name, xtn)
		else: newEndTok = name

		if renameOnDisk:
			self.rename( newEndTok, True )
		else:
			toks[ -1 ] = newEndTok

		return self._toksToPath( toks )
	extension = property(getExtension, setExtension)
	def isExtension( self, extension ):
		'''
		returns whether the extension is of a certain value or not
		'''
		ext = self.getExtension()
		if not self.__CASE_MATTERS:
			ext = ext.lower()
			extension = extension.lower()

		return ext == extension
	hasExtension = isExtension
	def name( self, stripExtension=True, stripAllExtensions=False ):
		'''
		returns the filename by itself - by default it also strips the extension, as the actual filename can
		be easily obtained using self[-1], while extension stripping is either a multi line operation or a
		lengthy expression
		'''
		name = self[ -1 ]
		if stripExtension:
			pIdx = -1
			if stripAllExtensions:
				pIdx = name.find('.')
			else:
				pIdx = name.rfind('.')

			if pIdx != -1:
				return name[ :pIdx ]

		return name
	def up( self, levels=1 ):
		'''
		returns a new path object with <levels> path tokens removed from the tail.
		ie: Path("a/b/c/d").up(2) returns Path("a/b")
		'''
		if not levels:
			return self

		toks = self.split()
		levels = max( min( levels, len(toks)-1 ), 1 )
		toksToJoin = toks[ :-levels ]
		if self.hasTrailing:
			toksToJoin.append( '' )

		return self._toksToPath( toksToJoin )
	def replace( self, search, replace='', caseMatters=None ):
		'''
		a simple search replace method - works on path tokens.  if caseMatters is None, then the system
		default case sensitivity is used
		'''
		idx = self.find( search, caseMatters )
		toks = self.split()
		toks[ idx ] = replace

		return self._toksToPath( toks )
	def find( self, search, caseMatters=None ):
		'''
		returns the index of the given path token
		'''
		if caseMatters is None:
			#in this case assume system case sensitivity - ie sensitive only on *nix platforms
			caseMatters = self.__CASE_MATTERS

		if not caseMatters:
			toks = [ s.lower() for s in self.split() ]
			search = search.lower()
		else:
			toks = self.split()

		idx = toks.index( search )

		return idx
	index = find
	def doesExist( self ):
		'''
		returns whether the file exists on disk or not
		'''
		try:
			return os.path.exists( self )
		except IndexError: return False
	exists = property( doesExist )
	def matchCase( self ):
		'''
		If running under an env where file case doesn't matter, this method will return a Path instance
		whose case matches the file on disk.  It assumes the file exists
		'''
		if self.doesCaseMatter(): return self

		for f in self.up().files():
			if f == self:
				return f
	def getSize( self, units=sz_MEGABYTES ):
		'''
		returns the size of the file in mega-bytes
		'''
		div = float( 1024 ** units )
		return os.path.getsize( self ) / div
	def create( self ):
		'''
		if the directory doesn't exist - create it
		'''
		if not self.exists:
			os.makedirs( str( self ) )
	def delete( self, doP4=True ):
		'''
		WindowsError is raised if the file cannot be deleted.  if the file is managed by perforce, then a p4 delete is performed
		'''
		if doP4 and P4File.USE_P4:
			try:
				asP4 = self.asP4()
				if asP4.managed():
					if asP4.action is None:
						asP4.delete()
						return
					else:
						asP4.revert()
						asP4.delete()

						#only return if the file doesn't exist anymore - it may have been open for add in
						#which case we still need to do a normal delete...
						if not self.exists: return
			except Exception, e: pass

		if self.isfile():
			try:
				os.remove( self )
			except WindowsError, e:
				win32api.SetFileAttributes( self, win32con.FILE_ATTRIBUTE_NORMAL )
				os.remove( self )
		elif self.isdir():
			for f in self.files( recursive=True ):
				f.delete()

			win32api.SetFileAttributes( self, win32con.FILE_ATTRIBUTE_NORMAL )
			shutil.rmtree( self.asDir(), True )
	remove = delete
	def rename( self, newName, nameIsLeaf=False, doP4=True ):
		'''
		it is assumed newPath is a fullpath to the new dir OR file.  if nameIsLeaf is True then
		newName is taken to be a filename, not a filepath.  the instance is modified in place.
		if the file is in perforce, then a p4 rename (integrate/delete) is performed
		'''
		reAdd, change = False, None
		asP4 = None

		newPath = Path( newName ).resolve()
		if nameIsLeaf:
			newPath = Path( self ).up() / newName

		if self.isfile():
			tgtExists = newPath.exists
			if doP4 and P4File.USE_P4:
				try:
					asP4 = P4File( self )

					#if its open for add, revert - we're going to rename the file...
					if asP4.action == 'add':
						asP4.revert()
						change = asP4.getChange()
						reAdd = True

					#so if we're managed by p4 - try a p4 rename, and return on success.  if it
					#fails however, then just do a normal rename...
					if asP4.managed():
						asP4.rename( newPath )
						self.setPath( str(newPath) )
						return

					#if the target exists and is managed by p4, make sure its open for edit
					if tgtExists and asP4.managed( newPath ):
						asP4.edit( newPath )
				except Exception: pass

			#now perform the rename
			os.rename( self, newPath )

			if reAdd:
				asP4.add( newPath )
				asP4.setChange( change, newPath )
		elif self.isdir():
			raise NotImplementedError('dir renaming not implemented yet...')

		return newPath
	move = rename
	def copy( self, target, nameIsLeaf=False, doP4=True ):
		'''
		same as rename - except for copying.  returns the new target name
		'''
		if self.isfile():
			target = Path( target )
			if nameIsLeaf:
				asPath = self.up() / target
				target = asPath

			if doP4 and P4File.USE_P4:
				try:
					asP4 = P4File(self)
					tgtAsP4 = P4File(target)
					if asP4.managed() and tgtAsP4.isUnderClient():
						'''
						so if we're managed by p4 - try a p4 rename, and return on success.  if it
						fails however, then just do a normal rename...
						'''
						asP4.copy( target )
						return target
				except: pass

			try:
				shutil.copy2( self, target )
			#this happens when src and dest are the same...  its pretty harmless, so we do nothing...
			except shutil.Error:
				pass

			return target
		elif self.isdir():
			raise NotImplementedError('dir copying not implemented yet...')
			#shutil.copytree( str(self.resolve()), str(target) )
	def read( self, strip=True ):
		'''
		returns a list of lines contained in the file. NOTE: newlines are stripped from the end but whitespace
		at the head of each line is preserved unless strip=False
		'''
		if self.exists and self.isfile():
			fileId = file( self )
			if strip:
				lines = [line.rstrip() for line in fileId.readlines()]
			else:
				lines = fileId.read()
			fileId.close()

			return lines
	def write( self, contentsStr, doP4=True ):
		'''
		writes a given string to the file defined by self.  if doP4 is true, the file will be either
		checked out of p4 before writing or add to perforce after writing if its not managed already
		'''
		#make sure the directory to we're writing the file to exists
		self.up().create()

		existedBeforeWrite = self.exists
		isUnderClient = False
		if doP4 and P4File.USE_P4:
			asP4 = self.asP4()
			isUnderClient = asP4.isUnderClient()
			if existedBeforeWrite and isUnderClient:
				asP4.edit()

		fileId = file( self, 'w' )
		fileId.write( str(contentsStr) )
		fileId.close()

		if doP4 and not existedBeforeWrite and isUnderClient:
			asP4.add()
	def pickle( self, toPickle, doP4=True ):
		'''
		similar to the write method but pickles the file
		'''
		Path( self ).up().create()

		existedBeforeWrite = self.exists
		if existedBeforeWrite and doP4 and P4File.USE_P4:
			self.edit()

		#make sure the file is writeable - it may have been made unwriteable by copying from a non writeable source (ie from p4)
		if not self.getWritable():
			self.setWritable()

		fileId = file( self, 'wb' )
		cPickle.dump( toPickle, fileId, PICKLE_PROTOCOL )
		fileId.close()

		if not existedBeforeWrite and doP4 and P4File.USE_P4:
			#need to explicitly add pickled files as binary type files, otherwise p4 mangles them
			self.asP4().add(type=P4File.BINARY)
	def unpickle( self ):
		'''
		unpickles the file
		'''
		fileId = file( self, 'rb' )
		data = cPickle.load(fileId)
		fileId.close()

		return data
	def asRelative( self ):
		'''
		returns the path relative to either VCONTENT or VGAME.  if the path isn't under either of these directories
		None is returned
		'''
		c = content()
		g = game()
		if self.isUnder( c ):
			return self - c
		elif self.isUnder( g ):
			return self - g

		return None
	def relativeTo( self, other ):
		'''
		returns self as a path relative to another
		'''
		path = self
		other = Path( other )

		#if the first path token is different, early out - one is not a subset of the other in any fashion
		lenPath, lenOther = len( path ), len( other )
		if other[0].lower() != path[0].lower():
			return None
		elif lenPath < lenOther:
			return None

		newPathToks = []
		pathsToDiscard = lenOther
		for pathN, otherN in zip(path, other):
			if pathN.lower() == otherN.lower():
				continue
			else:
				newPathToks.append( '..' )
				pathsToDiscard -= 1

		newPathToks.extend( path[ pathsToDiscard: ] )
		path = Path( PATH_SEPARATOR.join(newPathToks), self.__CASE_MATTERS )

		return path
	__sub__ = relativeTo
	def __rsub__( self, other ):
		return self.__class__( other, self.__CASE_MATTERS ).relativeTo( self )
	def inject( self, other, envDict=None ):
		'''
		injects an env variable into the path - if the env variable doesn't
		resolve to tokens that exist in the path, a path string with the same
		value as self is returned...

		NOTE: a string is returned, not a Path instance - as Path instances are
		always resolved

		NOTE: this method is alias'd by __lshift__ and so can be accessed using the << operator:
		d:/main/content/mod/models/someModel.ma << '%VCONTENT%' results in %VCONTENT%/mod/models/someModel.ma
		'''
		#if not isinstance(other, Path): other = Path(other)
		toks = toksLower = tuple(self.split())
		otherToks = Path( other ).split()
		newToks = []
		n = 0
		if not self.__CASE_MATTERS:
			toksLower = [ t.lower() for t in toks ]
			otherToks = [ t.lower() for t in otherToks ]

		while n < len( toks ):
			tok, tokLower = toks[ n ], toksLower[ n ]
			if tokLower == otherToks[ 0 ]:
				allMatch = True
				for tok, otherTok in zip( toksLower[ n + 1: ], otherToks[ 1: ] ):
					if tok != otherTok:
						allMatch = False
						break

				if allMatch:
					newToks.append( other )
					n += len( otherToks ) - 1
				else:
					newToks.append( toks[ n ] )
			else:
				newToks.append( tok )
			n += 1

		return PATH_SEPARATOR.join( newToks )
	__lshift__ = inject
	def findNearest( self ):
		'''
		returns the longest path that exists on disk
		'''
		path = self
		while not path.exists and len( path ) > 1:
			path = path.up()

		if not path.exists:
			return None
		return path
	getClosestExisting = findNearest
	nearest = findNearest
	def asNative( self ):
		'''
		returns a string with system native path separators
		'''
		return str( self ).replace( PATH_SEPARATOR, NATIVE_SEPARATOR )
	def startswith( self, other ):
		'''
		returns whether the current instance begins with a given path fragment.  ie:
		Path('d:/temp/someDir/').startswith('d:/temp') returns True
		'''
		otherToks = Path( other, self.__CASE_MATTERS ).split()
		selfToks = self.split()
		if not self.__CASE_MATTERS:
			otherToks = [ t.lower() for t in otherToks ]
			selfToks = [ t.lower() for t in selfToks ]

		if len( otherToks ) > len( selfToks ):
			return False

		for tokOther, tokSelf in zip(otherToks, selfToks):
			if tokOther != tokSelf: return False

		return True
	isUnder = startswith
	def endswith( self, other ):
		'''
		determines whether self ends with the given path - it can be a string
		'''
		#copies of these objects NEED to be made, as the results from them are often cached - hence modification to them
		#would screw up the cache, causing really hard to track down bugs...  not sure what the best answer to this is,
		#but this is clearly not it...  the caching decorator could always return copies of mutable objects, but that
		#sounds wasteful...  for now, this is a workaround
		otherToks = Path( other ).split()[:]
		selfToks = self.split()[:]
		otherToks.reverse()
		selfToks.reverse()
		if not self.__CASE_MATTERS:
			otherToks = [ t.lower() for t in otherToks ]
			selfToks = [ t.lower() for t in selfToks ]

		for tokOther, tokSelf in zip(otherToks, selfToks):
			if tokOther != tokSelf:
				return False

		return True
	def _list_filesystem_items( self, itemtest, namesOnly=False, recursive=False ):
		'''
		does all the listing work - itemtest can generally only be one of os.path.isfile or
		os.path.isdir.  if anything else is passed in, the arg given is the full path as a
		string to the filesystem item
		'''
		if not self.exists:
			return []

		start = len(self)
		items = []
		if recursive:
			walker = os.walk( self )
			for path, subs, files in walker:
				items.append( Path(path, self.__CASE_MATTERS) )
				fileItems = [path + Path(item, self.__CASE_MATTERS) for item in files]
				items.extend( fileItems )

			#first item is always ./
			try: items.pop(0)
			except IndexError: pass
		else: items = [ self / item for item in os.listdir( self ) ]

		if namesOnly: return [ item[ start: ] for item in items if itemtest( item ) ]
		return [ item for item in items if itemtest( item ) ]
	def dirs( self, namesOnly=False, recursive=False ):
		'''
		lists all sub-directories.  If namesOnly is True, then only directory names (relative to
		teh current dir) are returned
		'''
		return self._list_filesystem_items( os.path.isdir, namesOnly, recursive )
	def files( self, namesOnly=False, recursive=False ):
		'''
		lists all files in the directory.  If namesOnly is True, then only directory names (relative
		to teh current dir) are returned
		'''
		return self._list_filesystem_items( os.path.isfile, namesOnly, recursive )
	###--- Perforce integration stuff ---###
	def asP4( self ):
		'''
		returns self as a P4File instance - the instance is cached so repeated calls to this
		method will result in the same P4File instance being returned.

		NOTE: the caching is done within the method, it doesn't rely on the cache decorators
		used elsewhere in this class, so it won't get blown away on cache flush
		'''
		try:
			return self.p4
		except AttributeError:
			self.p4 = P4File(self)
			return self.p4
	def edit( self ):
		'''
		if the file exists and is in perforce, this will open it for edit - if the file isn't in perforce
		AND exists then this will open the file for add, otherwise it does nothing
		'''
		if self.exists:
			return self.asP4().editoradd()

		return False
	editoradd = edit
	def add( self, type=None ):
		return self.asP4().add()
	def revert( self ):
		return self.asP4().revert()
	def asDepot( self ):
		'''
		returns this instance as a perforce depot path
		'''
		return self.asP4().where()


def findInPyPath( filename ):
	'''
	given a filename or path fragment, will return the full path to the first matching file found in
	the sys.path variable
	'''
	for p in map( Path, sys.path ):
		loc = p / filename
		if loc.exists:
			return loc

	return None


#make sure there is a HOME var...
try:
	os.environ['HOME']
except KeyError:
	os.environ['HOME'] = os.environ['USERPROFILE']


########### PERFORCE INTEGRATION ###########


class FinishedP4Operation(Exception): pass
class TimedOutP4Operation(Exception): pass


class P4Exception(Exception): pass


class P4Output(dict):
	EXIT_PREFIX = 'exit:'
	ERROR_PREFIX = 'error:'

	#
	START_DIGITS = re.compile( '(^[0-9]+)(.*)' )
	END_DIGITS = re.compile( '(.*)([0-9]+$)' )

	def __init__( self, outStr, keysColonDelimited=False ):
		EXIT_PREFIX = P4Output.EXIT_PREFIX
		ERROR_PREFIX = P4Output.ERROR_PREFIX
		self.errors = []

		if isinstance( outStr, basestring ):
			lines = outStr.split( '\n' )
		elif isinstance( outStr, (list, tuple) ):
			lines = outStr
		else:
			print outStr
			raise P4Exception( "unsupported type (%s) given to %s" % (type( outStr ), self.__class__.__name__) )

		delimiter = (' ', ':')[ keysColonDelimited ]
		for line in lines:
			line = line.strip()

			if not line:
				continue

			if line.startswith( EXIT_PREFIX ):
				break

			if line.startswith( ERROR_PREFIX ):
				self.errors.append( line )
				continue

			idx = line.find( ':' )
			if idx == -1:
				continue

			line = line[ idx + 1: ].strip()
			idx = line.find( delimiter )
			if idx == -1:
				prefix = line
				data = True
			else:
				prefix = line[ :idx ].strip()
				data = line[ idx + 1: ].strip()
				if data.isdigit():
					data = int( data )

			if keysColonDelimited:
				prefix = ''.join( [ (s, s.capitalize())[ n ] for n, s in enumerate( prefix.lower().split() ) ] )
			else:
				prefix = prefix[ 0 ].lower() + prefix[ 1: ]

			self[ prefix ] = data

		#finally, if there are prefixes which have a numeral at the end, strip it and pack the data into a list
		multiKeys = {}
		for k in self.keys():
			m = self.END_DIGITS.search( k )
			if m is None:
				continue

			prefix, idx = m.groups()
			idx = int( idx )

			data = self.pop( k )
			try:
				multiKeys[ prefix ].append( (idx, data) )
			except KeyError:
				multiKeys[ prefix ] = [ (idx, data) ]

		for prefix, dataList in multiKeys.iteritems():
			try:
				self.pop( prefix )
			except KeyError: pass

			dataList.sort()
			self[ prefix ] = [ d[ 1 ] for d in dataList ]
	def __getattr__( self, attr ):
		return self[ attr ]
	def asStr( self ):
		return '\n'.join( '%s:  %s' % items for items in self.iteritems() )


def _p4run( *args ):
	if not P4File.USE_P4:
		return False

	cmdStr = 'p4 '+ ' '.join( map( str, args ) )
	try:
		p4Proc = subprocess.Popen( cmdStr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
	except OSError:
		P4File.USE_P4 = False
		return False

	startTime = time.clock()
	stdoutAccum = []
	stderrAccum = []
	hasTimedOut = False
	while True:
		ret = p4Proc.poll()
		newStdout = p4Proc.stdout.readlines()
		newStderr = p4Proc.stderr.readlines()

		stdoutAccum += newStdout
		stderrAccum += newStderr

		#if the proc has terminated, deal with returning appropriate data
		if ret is not None:
			if hasTimedOut:
				if callable( P4_RETURNED_CALLBACK ):
					try: P4_RETURNED_CALLBACK( *args )
					except: pass

			return stdoutAccum + stderrAccum

		#if there has been new output, the proc is still alive so reset counters
		if newStderr or newStdout:
			startTime = time.clock()

		#make sure we haven't timed out
		curTime = time.clock()
		if curTime - startTime > P4File.TIMEOUT_PERIOD:
			hasTimedOut = True
			if callable( P4_LENGTHY_CALLBACK ):
				try:
					P4_LENGTHY_CALLBACK( p4Proc, *args )
				except BreakException:
					return False
				except:
					return False


def p4run( *args, **kwargs ):
	ret = _p4run( *args )
	if ret is False:
		return False

	return P4Output( ret, **kwargs )


P4INFO = None
def p4Info():
	global P4INFO

	if P4INFO:
		return P4INFO

	P4INFO = p4run( '-s info', keysColonDelimited=True )

	return P4INFO


def populateChange( change ):
		changeNum = change[ 'change' ]
		if isinstance( changeNum, int ) and changeNum:
			fullChange = P4Change.FetchByNumber( changeNum )
			for key, value in fullChange.iteritems():
				change[ key ] = value


class P4Change(dict):
	def __init__( self ):
		self[ 'change' ] = None
		self[ 'description' ] = ''
		self[ 'files' ] = []
		self[ 'actions' ] = []
		self[ 'revisions' ] = []
	def __setattr__( self, attr, value ):
		if isinstance( value, basestring ):
			if value.isdigit():
				value = int( value )

		self[ attr ] = value
	def __getattr__( self, attr ):
		'''
		if the value of an attribute is the populateChanges function (in the root namespace), then
		the full changelist data is queried.  This is useful for commands like the p4 changes command
		(wrapped by the FetchChanges class method) which lists partial changelist data.  The method
		returns P4Change objects with partial data, and when more detailed data is required, a full
		query can be made.  This ensures minimal server interaction.
		'''
		value = self[ attr ]
		if value is populateChange:
			populateChange( self )
			value = self[ attr ]

		return value
	def __str__( self ):
		return str( self.change )
	def __int__( self ):
		return self[ 'change' ]
	__hash__ = __int__
	def __lt__( self, other ):
		return self.change < other.change
	def __le__( self, other ):
		return self.change <= other.change
	def __eq__( self, other ):
		return self.change == other.change
	def __ne__( self, other ):
		return self.change != other.change
	def __gt__( self, other ):
		return self.change > other.change
	def __ge__( self, other ):
		return self.change >= other.change
	def __len__( self ):
		return len( self.files )
	def __eq__( self, other ):
		if isinstance( other, int ):
			return self.change == other
		elif isinstance( other, basestring ):
			if other == 'default':
				return self.change == 0

		return self.change == other.change
	def __iter__( self ):
		return zip( self.files, self.revisions, self.actions )
	@classmethod
	def Create( cls, description, files=None ):

		#clean the description line
		description = '\n\t'.join( [ line.strip() for line in description.split( '\n' ) ] )
		info = p4Info()
		contents = '''Change:\tnew\n\nClient:\t%s\n\nUser:\t%s\n\nStatus:\tnew\n\nDescription:\n\t%s\n''' % (info.clientName, info.userName, description)

		p4Proc = subprocess.Popen( 'p4 -s change -i', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
		stdout, stderr = p4Proc.communicate( contents )

		output = P4Output( stdout + stderr, False )
		changeNum = int( P4Output.START_DIGITS.match( output.change ).groups()[ 0 ] )

		new = cls()
		new.description = description
		new.change = changeNum

		if files is not None:
			p4run( 'reopen -c', changeNum, *files )

		return new
	@classmethod
	def FetchByNumber( cls, number ):
		lines = _p4run( '-s', 'describe', number )
		if not lines:
			return None

		change = cls()
		change.change = number

		change.description = ''
		lineIter = iter( lines[ 2: ] )
		try:
			prefix = 'text:'
			PREFIX_LEN = len( prefix )

			line = lineIter.next()
			while line.startswith( prefix ):
				line = line[ PREFIX_LEN: ].lstrip()

				if line.startswith( 'Affected files ...' ):
					break

				change.description += line
				line = lineIter.next()

			prefix = 'info1:'
			PREFIX_LEN = len( prefix )
			while not line.startswith( prefix ):
				line = lineIter.next()

			while line.startswith( prefix ):
				line = line[ PREFIX_LEN: ].lstrip()
				idx = line.rfind( '#' )
				depotFile = Path( line[ :idx ] )

				revAndAct = line[ idx + 1: ].split()
				rev = int( revAndAct[ 0 ] )
				act = revAndAct[ 1 ]

				change.files.append( depotFile )
				change.actions.append( act )
				change.revisions.append( rev )

				line = lineIter.next()
		except StopIteration:
			pass

		return change
	@classmethod
	def FetchByDescription( cls, description, createIfNotFound=False ):
		'''
		fetches a changelist based on a given description from the list of pending changelists
		'''
		cleanDesc = ''.join( [ s.strip() for s in description.lower().strip().split( '\n' ) ] )
		for change in cls.IterPending():
			thisDesc = ''.join( [ s.strip() for s in change.description.lower().strip().split( '\n' ) ] )
			if thisDesc == cleanDesc:
				return change

		if createIfNotFound:
			return cls.Create( description )
	@classmethod
	def FetchChanges( cls, *args ):
		'''
		effectively runs the command:
		p4 changes -l *args

		a list of P4Change objects is returned
		'''
		lines = _p4run( 'changes -l %s' % ' '.join( args ) )
		changes = []
		if lines:
			lineIter = iter( lines )
			curChange = None
			try:
				while True:
					line = lineIter.next()
					if line.startswith( 'Change' ):
						curChange = cls()
						changes.append( curChange )
						toks = line.split()
						curChange.change = int( toks[ 1 ] )
						curChange.user = toks[ -1 ]
						curChange.date = datetime.date( *list( map( int, toks[ 3 ].split( '/' ) ) ) )
						curChange.description = ''

						#setup triggers for other data in the changelist that doesn't get returned by the changes command - see the __getattr__ doc for more info
						curChange.files = populateChange
						curChange.actions = populateChange
						curChange.revisions = populateChange
					elif curChange is not None:
						curChange.description += line
			except StopIteration:
				return changes
	@classmethod
	def IterPending( cls ):
		'''
		iterates over pending changelists
		'''
		info = p4Info()
		for line in _p4run( 'changes -u %s -s pending -c %s' % (info.userName, info.clientName) ):
			toks = line.split()
			changeNum = int( toks[ 1 ] )

			yield cls.FetchByNumber( changeNum )


#the number of the default changelist
P4Change.CHANGE_NUM_DEFAULT = P4Change()
P4Change.CHANGE_NUM_DEFAULT.change = 0

#the object to represent invalid changelist numbers
P4Change.CHANGE_NUM_INVALID = P4Change()

#all opened perforce files get added to a changelist with this description by default
DEFAULT_CHANGE = 'default auto-checkout'

#gets called when a perforce command takes too long (defined by P4File.TIMEOUT_PERIOD)
P4_LENGTHY_CALLBACK = None

#gets called when a lengthy perforce command finally returns
P4_RETURNED_CALLBACK = None

class P4File(Path):
	'''
	provides a more convenient way of interfacing with perforce.  NOTE: where appropriate all actions
	are added to the changelist with the description DEFAULT_CHANGE
	'''
	USE_P4 = True

	#the default change description for instances
	DEFAULT_CHANGE = DEFAULT_CHANGE

	BINARY = 'binary'
	XBINARY = 'xbinary'

	TIMEOUT_PERIOD = 5

	def run( self, *args, **kwargs ):
		return p4run( *args, **kwargs )
	def getFile( self, f=None ):
		if f is None:
			return self

		return Path( f )
	def getFileStr( self, f=None, allowMultiple=False, verifyExistence=True ):
		if f is None:
			return '"%s"' % self

		if isinstance( f, (list, tuple) ):
			if verifyExistence: return '"%s"' % '" "'.join( [ anF for anF in f if Path( anF ).exists ] )
			else: return '"%s"' % '" "'.join( f )

		return '"%s"' % Path( f )
	def getStatus( self, f=None ):
		'''
		returns the status dictionary for the instance.  if the file isn't managed by perforce,
		None is returned
		'''
		if not self.USE_P4:
			return None

		f = self.getFile( f )
		try:
			return self.run( '-s fstat', f )
		except Exception: return None
	def isManaged( self, f=None ):
		'''
		returns True if the file is managed by perforce, otherwise False
		'''
		if not self.USE_P4:
			return False

		f = self.getFile( f )
		stat = self.getStatus( f )
		if stat:
			#if the file IS managed - only return true if the head action isn't delete - which effectively means the file
			#ISN'T managed...
			try:
				return stat[ 'headAction' ] != 'delete'
			except KeyError:
				#this can happen if the file is a new file and is opened for add
				return True
		return False
	managed = isManaged
	def isUnderClient( self, f=None ):
		'''
		returns whether the file is in the client's root
		'''
		if not self.USE_P4:
			return False

		f = self.getFile( f )
		results = self.getStatus()
		if not results:
			phrases = [ "not in client view", "not under client's root" ]
			for e in results.errors:
				for ph in phrases:
					if ph in e: return False

		return True
	def getAction( self, f=None ):
		'''
		returns the head "action" of the file - if the file isn't in perforce None is returned...
		'''
		if not self.USE_P4:
			return None

		f = self.getFile( f )
		data = self.getStatus( f )

		try:
			return data.get( 'action', None )
		except AttributeError: return None
	action = property( getAction )
	def getHaveHead( self, f=None ):
		if not self.USE_P4:
			return False

		f = self.getFile( f )
		data = self.getStatus( f )

		try:
			return data[ 'haveRev' ], data[ 'headRev' ]
		except (AttributeError, TypeError, KeyError):
			return None, None
	def isEdit( self, f=None ):
		if not self.USE_P4:
			return False

		editActions = [ 'add', 'edit' ]
		action = self.getAction( f )

		#if the action is none, the file may not be managed - check
		if action is None:
			if not self.getStatus( f ):
				return None

		return action in editActions
	def isLatest( self, f=None ):
		'''
		returns True if the user has the latest version of the file, otherwise False
		'''

		#if no p4 integration, always say everything is the latest to prevent complaints from tools
		if not self.USE_P4:
			return True

		status = self.getStatus( f )
		if not status:
			return None

		#if there is any action on the file then always return True
		if 'action' in status:
			return True

		#otherwise check revision numbers
		try:
			headRev, haveRev = status[ 'headRev' ], status[ 'haveRev' ]

			return headRev == haveRev
		except KeyError:
			return False
	def add( self, f=None, type=None ):
		if not self.USE_P4:
			return False

		args = [ '-s add', '-c', self.getOrCreateChange() ]

		#if the type has been specified, add it to the add args
		if type is not None:
			args += [ '-t', type ]

		args.append( self.getFile( f ) )

		lines = _p4run( *args )
		for line in lines:
			if line.startswith( 'error' ):
				return False

			if "can't add existing file" in line:
				return False

		return True
	def edit( self, f=None ):
		if not self.USE_P4:
			return False

		lines = _p4run( '-s edit', '-c', self.getOrCreateChange(), self.getFile( f ) )
		for line in lines:
			if line.startswith( 'error' ):
				return False

			if "can't edit exclusive" in line:
				return False

		return True
	def editoradd( self, f=None ):
		if self.edit( f ):
			return True

		if self.add( f ):
			return True

		return False
	def revert( self, f=None ):
		if not self.USE_P4:
			return False

		return self.run( 'revert', self.getFile( f ) )
	def sync( self, f=None, force=False, rev=None, change=None ):
		'''
		rev can be a negative number - if it is, it works as previous revisions - so rev=-1 syncs to
		the version prior to the headRev.  you can also specify the change number using the change arg.
		if both a rev and a change are specified, the rev is used
		'''
		if not self.USE_P4:
			return False

		f = self.getFile( f )

		#if file is a directory, then we want to sync to the dir
		if os.path.isdir( f ):
			f = ('%s/...' % f).replace('//','/')

		if rev is not None:
			if rev == 0: f += '#none'
			elif rev < 0:
				status = self.getStatus()
				headRev = status[ 'headRev' ]
				rev += int( headRev )
				if rev <= 0: rev = 'none'
				f += '#%s' % rev
			else: f += '#%s' % rev
		elif change is not None:
			f += '@%s' % change

		if force: return self.run( '-s sync', '-f', f )
		else: return self.run( '-s sync', f )
	def delete( self, f=None ):
		if not self.USE_P4:
			return False

		f = self.getFile( f )
		action = self.getAction( f )
		if action is None and self.managed( f ):
			return self.run( '-s delete', '-c', self.getOrCreateChange(), f )
	def rename( self, newName, f=None ):
		if not self.USE_P4:
			return False

		f = self.getFile( f )

		try:
			action = self.getAction( f )
			if action is None and self.managed( f ):
				self.run( 'integrate', '-c', self.getOrCreateChange(), f, str( newName ) )
				return self.run( 'delete', '-c', self.getOrCreateChange(), f )
		except Exception: pass
		return False
	def copy( self, newName, f=None ):
		if not self.USE_P4:
			return False

		f = self.getFile( f )
		newName = self.getFile( newName )
		action = self.getAction( f )

		if self.managed( f ):
			return self.run( 'integrate', '-c', self.getOrCreateChange(), f, newName )

		return False
	def submit( self, change=None ):
		if not self.USE_P4:
			return

		if change is None:
			change = self.getChange()

		self.run( 'submit', '-c', change )
	def getChange( self, f=None ):
		if not self.USE_P4:
			return P4Change.CHANGE_NUM_INVALID

		f = self.getFile( f )
		stat = self.getStatus( f )
		try:
			return stat.get( 'change', P4Change.CHANGE_NUM_DEFAULT )
		except (AttributeError, ValueError): return P4Change.CHANGE_NUM_DEFAULT
	def setChange( self, newChange=None, f=None ):
		'''
		sets the changelist the file belongs to. the changelist can be specified as either a changelist
		number, a P4Change object, or a description. if a description is given, the existing pending
		changelists are searched for a matching description.  use 0 for the default changelist.  if
		None is passed, then the changelist as described by self.DEFAULT_CHANGE is used
		'''
		if not self.USE_P4:
			return

		if isinstance( newChange, (int, long) ):
			change = newChange
		elif isinstance( newChange, P4Change ):
			change = newChange.change
		else:
			change = P4Change.FetchByDescription( newChange, True ).change

		f = self.getFile( f )
		self.run( 'reopen', '-c', change, f )
	def getOtherOpen( self, f=None ):
		f = self.getFile( f )
		statusDict = self.getStatus( f )
		try:
			return statusDict[ 'otherOpen' ]
		except (KeyError, TypeError):
			return []
	def getOrCreateChange( self, f=None ):
		'''
		if the file isn't already in a changelist, this will create one.  returns the change number
		'''
		if not self.USE_P4:
			return P4Change.CHANGE_NUM_INVALID

		f = self.getFile( f )
		ch = self.getChange( f )
		if ch == P4Change.CHANGE_NUM_DEFAULT:
			return P4Change.FetchByDescription( self.DEFAULT_CHANGE, True ).change

		return ch
	def getChangeNumFromDesc( self, description=None, createIfNotFound=True ):
		if description is None:
			description = self.DEFAULT_CHANGE

		return P4Change.FetchByDescription( description, createIfNotFound )
	def allPaths( self, f=None ):
		'''
		returns all perforce paths for the file (depot path, workspace path and disk path)
		'''
		if not self.USE_P4:
			return None

		f = self.getFile( f )

		dataLine = _p4run( 'where', f )[ 0 ].strip()
		dataLineToSearch = dataLine
		fName = f[ -1 ]
		fNameLen = len( fName )

		if not self.doesCaseMatter():
			dataLineToSearch = dataLine.lower()
			fName = fName.lower()

		#I'm not entirely sure this is bullet-proof...  but basically the return string for this command
		#is a simple space separated string, with three values.  i guess I could try to match //HOSTNAME
		#and the client's depot root to find the start of files, but for now its simply looking for the
		#file name substring three times
		depotNameIdx = dataLineToSearch.find( fName ) + fNameLen
		depotName = P4File( dataLine[ :depotNameIdx ], self.doesCaseMatter() )

		workspaceNameIdx = dataLineToSearch.find( fName, depotNameIdx ) + fNameLen
		workspaceName = P4File( dataLine[ depotNameIdx + 1:workspaceNameIdx ], self.doesCaseMatter() )

		diskNameIdx = dataLineToSearch.find( fName, workspaceNameIdx ) + fNameLen
		diskName = P4File( dataLine[ workspaceNameIdx + 1:diskNameIdx ], self.doesCaseMatter() )

		return depotName, workspaceName, diskName
	def toDepotPath( self, f=None ):
		'''
		returns the depot path to the file
		'''
		if not self.USE_P4:
			return None

		return self.allPaths( f )[ 0 ]
	def toDiskPath( self, f=None ):
		'''
		returns the disk path to a depot file
		'''
		if not self.USE_P4:
			return None

		return self.allPaths( f )[ 2 ]


P4Data = P4File  #used to be called P4Data - this is just for any legacy references...


def isPerforceEnabled():
	return P4File.USE_P4


def enablePerforce( state=True ):
	'''
	sets the enabled state of perforce
	'''
	P4File.USE_P4 = bool( state )


def disablePerforce():
	'''
	alias for enablePerforce( False )
	'''
	enablePerforce( False )


def d_preserveDefaultChange(f):
	'''
	decorator to preserve the default changelist
	'''
	def newF( *a, **kw ):
		global DEFAULT_CHANGE
		preChange = DEFAULT_CHANGE
		try: f( *a, **kw )
		except:
			DEFAULT_CHANGE = preChange
			raise

		DEFAULT_CHANGE = preChange

	newF.__doc__ = f.__doc__
	newF.__name__ = f.__name__

	return newF


def syncFiles( files, force=False, rev=None, change=None ):
	'''
	syncs a given list of files to either the headRev (default) or a given changelist,
	or a given revision number
	'''
	p4 = P4File()
	if rev is not None:
		ret = []
		for f in files:
			if force:
				r = p4.sync( '-f', f, rev )
			else:
				r = p4.sync( f, rev )

			ret.append( r )

		return ret
	elif change is not None:
		args = files
		if force:
			args = [ '-f' ] + args

		return p4.run( 'sync', '-c', change, *args )
	else:
		args = files
		if force:
			args = [ '-f' ] + args

		return p4.run( 'sync', *args )


def findStaleFiles( fileList ):
	'''
	given a list of files (can be string paths or Path instances) returns a list of "stale" files.  stale files are simply
	files that aren't at head revision
	'''
	p4 = P4File()
	stale = []
	for f in fileList:
		latest = p4.isLatest( f )
		if latest is None:
			continue

		if not latest:
			stale.append( f )

	return stale


def gatherFilesIntoChange( files, change=None ):
	'''
	gathers the list of files into a single changelist - if no change is specified, then the
	default change is used
	'''
	p4 = P4File()
	filesGathered = []
	for f in files:
		if not isinstance( f, Path ): f = Path( f )

		try:
			stat = p4.getStatus( f )
		except IndexError: continue

		if stat is None:
			try:
				if not f.exists:
					continue
			except TypeError: continue

			#in this case, the file isn't managed by perforce - so add it
			print 'adding file:', f
			p4.add( f )
			p4.setChange(change, f)
			filesGathered.append( f )
			continue

		#otherwise, see what the action is on the file - if there is no action then the user hasn't
		#done anything to the file, so move on...
		try:
			action = stat[ 'action' ]
			p4.setChange( change, f )
			filesGathered.append( f )
		except KeyError: continue

	return filesGathered


def cleanEmptyChanges():
	p4 = P4File()
	for change in P4Change.IterPending():
		deleteIt = False
		try:
			deleteIt = not change.files
		except KeyError: deleteIt = True

		if deleteIt:
			p4run( 'change -d', str( change ) )


def removeLineComments( lines ):
	'''
	removes all line comments from a list of lines
	'''
	newLines = []
	for line in lines:
		commentStart = line.find('//')
		if commentStart != -1:
			line = line[:commentStart]
			if not line: continue
		newLines.append(line)

	return newLines


def removeBlockComments( lines ):
	'''
	removes all block comments from a list of lines
	'''
	newLines = []
	end = len(lines)
	n = 0
	while n<end:
		blockCommentStart = lines[n].find('/*')
		newLines.append(lines[n])
		contFlag = 0
		if blockCommentStart != -1:
			newLines[-1] = lines[n][:blockCommentStart]
			while n<end:
				blockCommentEnd = lines[n].find('*/')
				if blockCommentEnd != -1:
					newLines[-1] += lines[n][blockCommentEnd+2:]
					n+=1
					contFlag = 1
					break
				n+=1
		if contFlag: continue
		n+=1
	return newLines


class Chunk( object ):
	'''
	a chunk creates a reasonably convenient way to hold and access key value pairs, as well as a way to access
	a chunk's parent.  the value attribute can contain either a string or a list containing other Chunk instances
	'''
	QUOTE_COMPOUND_KEYS = False
	def __init__( self, key, value=None, parent=None, append=False ):
		self.key = key
		self.value = value
		self.parent = parent
		if append:
			parent.append(self)
	def __getitem__( self, item ):
		return self.value[item]
	def __getattr__( self, attr ):
		if self.hasLen:
			for val in self.value:
				if val.key == attr:
					return val

		raise AttributeError( "has no attribute called %s"%attr )
	def __len__( self ):
		if self.hasLen: return len(self.value)
		return None
	def _hasLen( self ):
		return isinstance( self.value, list )
	hasLen = property(_hasLen)
	def __iter__( self ):
		if self.hasLen:
			return iter(self.value)
		raise TypeError("non-compound value is not iterable")
	def __repr__( self, depth=0 ):
		strLines = []

		compoundLine = '%s%s\n'
		if self.QUOTE_COMPOUND_KEYS:
			compoundLine = '%s"%s"\n'

		if isinstance(self.value,list):
			strLines.append( compoundLine % ('\t'*depth, self.key))
			strLines.append( '\t'*depth +'{\n' )
			for val in self.value: strLines.append( val.__repr__(depth+1) )
			strLines.append( '\t'*depth +'}\n' )
		else:
			strLines.append( '%s"%s" "%s"\n'%('\t'*depth, self.key, self.value) )

		return ''.join( strLines )
	__str__ = __repr__
	def __hash__( self ):
		return id( self )
	def iterChildren( self ):
		'''
		'''
		if self.hasLen:
			for chunk in self:
				if chunk.hasLen:
					for subChunk in chunk.iterChildren():
						yield subChunk
				else:
					yield chunk
	def asDict( self, parentDict ):
		if isinstance(self.value, list):
			parentDict[self.key] = subDict = {}
			for c in self.value:
				c.asDict(subDict)
		else:
			parentDict[self.key] = self.value
	def append( self, new ):
		if not isinstance( self.value, list ):
			self.value = []

		self.value.append(new)

		#set the parent of the new Chunk to this instance
		new.parent = self
	def findKey( self, key ):
		'''
		recursively searches this chunk and its children and returns a list of chunks with the given key
		'''
		matches = []
		if self.key == key:
			matches.append(self)
		if self.hasLen:
			for val in self.value:
				matches.extend(val.findKey(key))

		return matches
	def findValue( self, value ):
		'''
		recursively searches this chunk and its children and returns a list of chunks with the given value
		'''
		matches = []
		if self.hasLen:
			for val in self.value:
				matches.extend(val.findValue(value))
		elif self.value == value:
			matches.append(self)

		return matches
	def findKeyValue( self, key, value ):
		'''
		recursively searches this chunk and its children and returns a list of chunks with the given key AND value
		'''
		matches = []
		if self.hasLen:
			for val in self.value:
				matches.extend(val.findKeyValue(key,value))
		elif self.key == key and self.value == value:
			matches.append(self)

		return matches
	def testOnValues( self, valueTest ):
		matches = []
		if self.hasLen:
			for val in self.value:
				matches.extend( val.testOnValues(valueTest) )
		elif valueTest(self.value):
			matches.append(self)

		return matches
	def listAttr( self ):
		#lists all the "attributes" - an attribute is just as a named key.  NOTE: only Chunk's with length have attributes
		attrs = []
		for attr in self:
			attrs.append(attr.key)

		return attrs
	def hasAttr( self, attr ):
		attrs = self.listAttr()
		return attr in attrs
	def getFileObject( self ):
		'''
		walks up the chunk hierarchy to find the file to which this chunk instance belongs
		'''
		parent = self.parent
		lastParent = parent
		safety = 1000
		while parent is not None and safety:
			lastParent = parent
			parent = parent.parent
			safety -= 1

		return lastParent


def parseLine( line ):
	'''
	this line parser works well for all internal key value files I've thrown at it
	'''
	c = line.count('"')
	if c == 4:
		toks = line[1:-1].split('"')
		return toks[0],toks[-1]
	if c == 2:
		#so this could mean we have a
		#A) "key" value   OR
		#B) key "value"   OR
		#C) "key"
		if line.strip().startswith('"'):
			toks = [tok.strip() for tok in line[1:].split('"')]
			tokCount = len(toks)
			if tokCount == 2:
				return toks[0],toks[-1].strip()
			elif tokCount == 1:
				return toks[0],[]
		else:
			toks = [tok.strip() for tok in line.rstrip()[:-1].split('"')]
			#toks = line.split()
			#idx = line.find('"')
			#value = line[idx:].strip()[1:-1]
			tokCount = len(toks)
			if tokCount == 2:
				return toks[0],toks[-1].strip()
			elif tokCount == 1:
				return toks[0],[]
			elif tokCount > 2:
				key = toks[0]
				for v in toks[1:]:
					if v.strip() != '':
						return key, v
	if c == 0:
		toks = line.split()
		tokCount = len(toks)
		if tokCount == 2: return toks[0],toks[1]
		if tokCount == 1: return toks[0],[]


class KeyValueFile( object ):
	'''
	self.data contains a list which holds all the top level Chunk objects
	'''
	def __init__( self, filepath=None, lineParser=parseLine, chunkClass=Chunk, readCallback=None, supportsComments=True ):
		'''
		lineParser needs to return key,value
		'''
		self.filepath = filepath
		self.data = self.value = []
		self.key = None
		self.parent = None
		self.lineParser = lineParser
		self.chunkClass = chunkClass
		self.callback = readCallback
		self.supportsComments = supportsComments

		def nullCallback(*args): pass
		self.nullCallback = nullCallback

		#if no callback is defined, create a dummy one
		if self.callback is None:
			self.callback = nullCallback

		#if no line parser was given, then use a default one
		if self.lineParser is None:
			def simpleLineParse( line ):
				toks = line.split()
				if len(toks) == 1: return toks[0],[]
				else: return toks[0],toks[1]
			self.lineParser = simpleLineParse

		#if a filepath exists, then read it
		if self.filepath.exists:
			self.read()
	def getFilepath( self ):
		return self._filepath
	def setFilepath( self, newFilepath ):
		'''
		this wrapper is here so to ensure the _filepath attribute is a Path instance
		'''
		self._filepath = Path(newFilepath)
	filepath = property(getFilepath, setFilepath)
	def read( self, filepath=None ):
		'''
		reads the actual file, and passes the data read over to the parseLines method
		'''
		if filepath == None: filepath = self.filepath
		else: filepath = Path(filepath)

		self.parseLines( filepath.read() )
	def parseLines( self, lines ):
		'''
		this method does the actual parsing/data creation.  deals with comments, passing off data to the lineParser,
		firing off the read callback, all that juicy stuff...
		'''
		lines = [l.strip() for l in lines]

		#remove comments
		if self.supportsComments:
			lines = removeLineComments(lines)
			lines = removeBlockComments(lines)

		numLines = len(lines)

		#hold a list representation of the current spot in the hierarchy
		parentList = [self]
		parentListEnd = self
		callback = self.callback
		lineParser = self.lineParser
		n = 0
		for line in lines:
			#run the callback - if there are any problems, replace the callback with the nullCallback
			try: callback(n,numLines)
			except: callback = self.nullCallback

			if line == '': pass
			elif line == '{':
				curParent = parentList[-1][-1]
				parentList.append(curParent)
				parentListEnd = curParent
			elif line == '}':
				parentList.pop()
				parentListEnd = parentList[-1]
			else:
				key, value = lineParser(line)
				parentListEnd.append( self.chunkClass(key, value, parentListEnd) )
			n += 1
	def __getitem__( self, *args ):
		'''
		provides an index based way of accessing file data - self[0,1,2] accesses the third child of
		the second child of the first root element in self
		'''
		args = args[0]
		if not isinstance(args,tuple):
			data = self.data[args]
		else:
			data = self.data[args[0]]
			if len(args) > 1:
				for arg in args[1:]:
					data = data[arg]

		return data
	def __len__( self ):
		'''
		lists the number of root elements in the file
		'''
		return len(self.data)
	def __repr__( self ):
		'''
		this string representation of the file is almost identical to the formatting of a vmf file written
		directly out of hammer
		'''
		strList = []
		for chunk in self.data:
			strList.append( str(chunk) )

		return ''.join(strList)
	__str__ = __repr__
	serialize = __repr__
	def unserialize( self, theString ):
		'''
		'''
		theStringLines = theString.split( '\n' )
		self.parseLines( theStringLines )
	@property
	def hasLen( self ):
		try:
			self.data[ 0 ]
			return True
		except IndexError:
			return False
	def asDict( self ):
		'''
		returns a dictionary representing the key value file - this isn't always possible as it is valid for
		a keyValueFile to have mutiple keys with the same key name within the same level - which obviously
		isn't possible with a dictionary - so beware!
		'''
		asDict = {}
		for chunk in self.data:
			chunk.asDict( asDict )

		return asDict
	def append( self, chunk ):
		'''
		appends data to the root level of this file - provided to make the vmf file object appear
		more like a chunk object
		'''
		self.data.append( chunk )
	def findKey( self, key ):
		'''
		returns a list of all chunks that contain the exact key given
		'''
		matches = []
		for item in self.data:
			matches.extend( item.findKey(key) )

		return matches
	def findValue( self, value ):
		'''
		returns a list of all chunks that contain the exact value given
		'''
		matches = []
		for item in self.data:
			matches.extend( item.findValue(value) )

		return matches
	def findKeyValue( self, key, value ):
		'''
		returns a list of all chunks that have the exact key and value given
		'''
		matches = []
		for item in self.data:
			matches.extend( item.findKeyValue(key,value) )

		return matches
	def testOnValues( self, valueTest ):
		'''
		returns a list of chunks that return true to the method given - the method should take as its
		first argument the value of the chunk it is testing against.  can be useful for finding values
		containing substrings, or all compound chunks etc...
		'''
		matches = []
		for item in self.data:
			matches.extend( item.testOnValues(valueTest) )

		return matches
	def write( self, filepath=None, doP4=True ):
		'''
		writes the instance back to disk - optionally to a different location from that which it was
		loaded.  NOTE: deals with perforce should the file be managed by p4
		'''
		if filepath is None:
			filepath = self.filepath
		else:
			filepath = Path(filepath)

		filepath.write(str(self), doP4=doP4)


########### PRESET DATA INTERFACES ###########
LOCALES = LOCAL, GLOBAL = 'local', 'global'
DEFAULT_XTN = 'preset'

#define where the base directories are for presets
kLOCAL_BASE_DIR = Path('%HOME%/presets/')
kGLOBAL_BASE_DIR = Path('%SHARED_NETWORK_LOCATION%/presets')

class PresetException(Exception):
	def __init__( self, *args ):
		Exception.__init__(self, *args)


def getPresetDirs( locale, tool ):
	'''
	returns the base directory for a given tool's preset files
	'''
	global kLOCAL_BASE_DIR, kGLOBAL_BASE_DIR

	if locale == LOCAL:
		localDir = kLOCAL_BASE_DIR / ('.%s/' % tool)
		localDir.create()

		return [localDir]

	dirs = []
	globalDir = kGLOBAL_BASE_DIR / ('.%s/' % tool)
	globalDir.create()

	return [ globalDir ]


def presetPath( locale, tool, presetName, ext=DEFAULT_XTN ):
	preset = getPresetDirs(locale, tool)[0] + scrubName(presetName, exceptions='./')
	preset = preset.setExtension( ext )

	return preset


def readPreset( locale, tool, presetName, ext=DEFAULT_XTN ):
	'''
	reads in a preset file if it exists, returning its contents
	'''
	file = getPresetPath(presetName, tool, ext, locale)
	if file is not None:
		return file.read()
	return []


def savePreset( locale, tool, presetName, ext=DEFAULT_XTN, contentsStr='' ):
	'''
	given a contents string, this convenience method will store it to a preset file
	'''
	preset = Preset(locale, tool, presetName, ext)
	preset.write(contentsStr, locale==GLOBAL)

	return preset


def unpicklePreset( locale, tool, presetName, ext=DEFAULT_XTN ):
	'''
	same as readPreset except for pickled presets
	'''
	dirs = getPresetDirs(locale, tool)
	for dir in dirs:
		cur = dir/presetName
		cur.extension = ext
		if cur.exists: return cur.unpickle()
	raise IOError("file doesn't exist!")


def picklePreset( locale, tool, presetName, ext=DEFAULT_XTN, contentsObj=None ):
	preset = presetPath(locale, tool, presetName, ext)
	preset.pickle(contentsObj, locale==GLOBAL)


def listPresets( locale, tool, ext=DEFAULT_XTN ):
	'''
	lists the presets in a given local for a given tool
	'''
	files = []
	for dir in getPresetDirs(locale, tool):
		if dir.exists:
			files.extend( map(str, [f for f in dir.files() if f.getExtension() == ext] ) )

	#remove duplicates
	files = [Preset.FromFile(f) for f in set(files)]

	return files


def listAllPresets( tool, ext=DEFAULT_XTN, localTakesPrecedence=False ):
	'''
	lists all presets for a given tool and returns a dict with local and global keys.  the dict
	values are lists of Path instances to the preset files, and are unique - so a preset in the
	global list will not appear in the local list by default.  if localTakesPrecedence is True,
	then this behaviour is reversed, and locals will trump global presets of the same name
	'''
	primaryLocale = GLOBAL
	secondaryLocale = LOCAL
	primary = listPresets(primaryLocale, tool, ext)
	secondary = listPresets(secondaryLocale, tool, ext)

	if localTakesPrecedence:
		primary, secondary = secondary, primary
		primaryLocale, secondaryLocale = secondaryLocale, primaryLocale

	#so teh localTakesPrecedence determines which locale "wins" when there are leaf name clashes
	#ie if there is a preset in both locales called "yesplease.preset", if localTakesPrecedence is
	#False, then the global one gets included, otherwise the local one is listed
	alreadyAdded = set()
	locales = {LOCAL:[], GLOBAL:[]}
	for p in primary:
		locales[primaryLocale].append(p)
		alreadyAdded.add(p[-1])

	for p in secondary:
		if p[-1] not in alreadyAdded:
			locales[secondaryLocale].append(p)

	return locales


def getPresetPath( presetName, tool, ext=DEFAULT_XTN, locale=GLOBAL ):
	'''
	given a preset name, this method will return a path to that preset if it exists.  it respects the project's
	mod hierarchy, so it may return a path to a file not under the current mod's actual preset directory...
	'''
	searchPreset = '%s.%s' % (presetName, ext)
	dirs = getPresetDirs(locale, tool)
	for dir in dirs:
		presetPath = dir / searchPreset
		if presetPath.exists:
			return presetPath.resolve()


def findPreset( presetName, tool, ext=DEFAULT_XTN, startLocale=LOCAL ):
	'''
	looks through all locales and all search mods for a given preset name.  the startLocale simply dictates which
	locale is searched first - so if a preset exists under both locales, then then one found in the startLocale
	will get returned
	'''
	other = list( LOCALES ).remove( startLocale )
	for loc in [ startLocale, other ]:
		p = getPresetPath( presetName, tool, ext, loc )
		if p is not None: return p


def dataFromPresetPath( path ):
	'''
	returns a tuple containing the locale, tool, name, extension for a given Path instance.  a PresetException
	is raised if the path given isn't an actual preset path
	'''
	locale, tool, name, ext = None, None, None, None
	pathCopy = Path( path )
	if pathCopy.isUnder( kGLOBAL_BASE_DIR ):
		locale = GLOBAL
		pathCopy -= kGLOBAL_BASE_DIR
	elif pathCopy.isUnder( kLOCAL_BASE_DIR ):
		locale = LOCAL
		pathCopy -= kLOCAL_BASE_DIR
	else:
		raise PresetException("%s isn't under the local or the global preset dir" % file)

	tool = pathCopy[ -2 ][ 1: ]
	ext = pathCopy.getExtension()
	name = pathCopy.name()

	return locale, tool, name, ext


def scrubName( theStr, replaceChar='_', exceptions=None ):
	invalidChars = """`~!@#$%^&*()-+=[]\\{}|;':"/?><., """
	if exceptions:
		for char in exceptions:
			invalidChars = invalidChars.replace(char, '')

	for char in invalidChars:
		theStr = theStr.replace(char, '_')

	return theStr


#these are a bunch of variables used for keys in the export dict.  they're provided mainly for
#the sake of auto-completion...
kEXPORT_DICT_USER = 'user'
kEXPORT_DICT_MACHINE = 'machine'
kEXPORT_DICT_DATE = 'date'
kEXPORT_DICT_TIME = 'time'
kEXPORT_DICT_TOOL = 'tool_name'
kEXPORT_DICT_TOOL_VER = 'tool_version'
kEXPORT_DICT_SOURCE = 'scene'  #the source of the file - if any
def writeExportDict( toolName=None, toolVersion=None, **kwargs ):
	'''
	returns a dictionary containing a bunch of common info to write when generating presets
	or other such export type data
	'''
	d = {}
	d[ kEXPORT_DICT_USER ] = os.environ[ 'USERNAME' ]
	d[ kEXPORT_DICT_MACHINE ] = os.environ[ 'COMPUTERNAME' ]
	now = datetime.datetime.now()
	d[ kEXPORT_DICT_DATE ], d[ kEXPORT_DICT_TIME ] = now.date(), now.time()
	d[ kEXPORT_DICT_TOOL ] = toolName
	d[ kEXPORT_DICT_TOOL_VER ] = toolVersion


class PresetManager(object):
	def __init__( self, tool, ext=DEFAULT_XTN ):
		self.tool = tool
		self.extension = ext
	def getPresetDirs( self, locale=GLOBAL ):
		'''
		returns the base directory for a given tool's preset files
		'''
		return getPresetDirs(locale, self.tool)
	def presetPath( self, name, locale=GLOBAL ):
		return Preset(locale, self.tool, name, self.extension)
	def findPreset( self, name, startLocale=LOCAL ):
		return Preset( *dataFromPresetPath( findPreset(name, self.tool, self.extension, startLocale) ) )
	def listPresets( self, locale=GLOBAL ):
		return listPresets(locale, self.tool, self.extension)
	def listAllPresets( self, localTakesPrecedence=False ):
		return listAllPresets(self.tool, self.extension, localTakesPrecedence)


class Preset(Path):
	'''
	provides a convenient way to write/read and otherwise handle preset files
	'''
	def __new__( cls, locale, tool, name, ext=DEFAULT_XTN ):
		'''
		locale should be one of either GLOBAL or LOCAL object references.  tool is the toolname
		used to refer to all presets of that kind, while ext is the file extension used to
		differentiate between multiple preset types a tool may have
		'''
		name = scrubName(name, exceptions='./')
		path = getPresetPath(name, tool, ext, locale)
		if path is None:
			path = presetPath(locale, tool, name, ext)

		return Path.__new__( cls, path )
	def __init__( self, locale, tool, name, ext=DEFAULT_XTN ):
		self.locale = locale
		self.tool = tool
	@staticmethod
	def FromFile( filepath ):
		return Preset(*dataFromPresetPath(filepath))
	FromPreset = FromFile
	def up( self, levels=1 ):
		return Path( self ).up( levels )
	def other( self ):
		'''
		returns the "other" locale - ie if teh current instance points to a GLOBAL preset, other()
		returns LOCAL
		'''
		if self.locale == GLOBAL:
			return LOCAL
		else: return GLOBAL
	def copy( self ):
		'''
		copies the current instance from its current locale to the "other" locale. handles all
		perforce operations when copying a file from one locale to the other.  NOTE: the current
		instance is not affected by a copy operation - a new Preset instance is returned
		'''
		other = self.other()
		otherLoc = getPresetDirs(other, self.tool)[0]

		dest = otherLoc / self[-1]
		destP4 = None
		addToP4 = False

		#in this case, we want to make sure the file is open for edit, or added to p4...
		if other == GLOBAL:
			destP4 = P4File(dest)
			if destP4.managed():
				destP4.edit()
				print 'opening %s for edit' % dest
			else:
				addToP4 = True

		Path.copy(self, dest)
		if addToP4:
			#now if we're adding to p4 - we need to know if the preset is a pickled preset - if it is, we need
			#to make sure we add it as a binary file, otherwise p4 assumes text, which screws up the file
			try:
				self.unpickle()
				destP4.add(type=P4File.BINARY)
			except Exception, e:
				#so it seems its not a binary file, so just do a normal add
				print 'exception when trying to unpickle - assuming a text preset', e
				destP4.add()
			print 'opening %s for add' % dest

		return Preset(self.other(), self.tool, self.name(), self.extension)
	def move( self ):
		'''
		moves the preset from the current locale to the "other" locale.  all instance variables are
		updated to point to the new location for the preset
		'''
		newLocation = self.copy()

		#delete the file from disk - and handle p4 reversion if appropriate
		self.delete()

		#now point instance variables to the new locale
		self.locale = self.other()

		return self.FromFile( newLocation )
	def rename( self, newName ):
		'''
		newName needs only be the new name for the preset - extension is optional.  All perforce
		transactions are taken care of.  all instance attributes are modified in place

		ie: a = Preset(GLOBAL, 'someTool', 'presetName')
		a.rename('the_new_name)
		'''
		if not newName.endswith(self.extension):
			newName = '%s.%s' % (newName, self.extension)

		return Path.rename(self, newName, True)
	def getName( self ):
		return Path(self).setExtension()[-1]


#end