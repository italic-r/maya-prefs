'''
super simple vector class and vector functionality.  i wrote this simply because i couldn't find
anything that was easily accessible and quick to write.  this may just go away if something more
comprehensive/mature is found
'''

import math, random

zeroThreshold = 1e-8

class MatrixException(Exception):
	pass


class Angle(object):
	def __init__( self, angle, radian=False ):
		'''set the radian to true on init if the angle is in radians - otherwise degrees are assumed'''
		if radian:
			self.radians = angle
			self.degrees = math.degrees(angle)
		else:
			self.degrees = angle
			self.radians = math.radians(angle)


class Vector(list):
	'''
	provides a bunch of common vector functionality.  Vectors can be instantiated with either an iterable, or
	with individual components, but using an iterable is faster.

	ie: Vector([1, 2, 3]) is faster than Vector(1, 2, 3).

	using an iterable is roughly twice as fast...
	'''
	INDEX_NAMES = 'xyzw'
	def __init__(self, *a):
		try:
			list.__init__(self, *a)
		except TypeError:
			super(Vector, self).__init__(a)
	def __repr__( self ):
		return '<%s>' % ', '.join( map(str, self ) )
	__str__ = __repr__
	def getNamedIndex( self, name ):
		idx = self.INDEX_NAMES.index( name )
		return self[ idx ]
	def setNamedIndex( self, name, value ):
		idx = self.INDEX_NAMES.index( name )
		self[ idx ] = value
	def __add__( self, other ):
		return self.__class__( map(lambda *x: sum(x), self, other) )
	def __sub__( self, other ):
		return self.__add__( -other )
	def __mul__( self, factor ):
		if isinstance(factor, Matrix):
			size = len( self )
			new = self.__class__( [0] * size )

			for i in xrange(size):
				element = 0
				col = factor.getCol(i)
				for j in xrange( size ):
					element += self[j] * col[j]

				new[i] = element

			return new

		#test whether the object is iterable or not
		isIterable = False
		try:
			iter(factor)
			isIterable = True
		except TypeError: pass

		if isIterable:
			return self.dot( factor )

		return self.__class__( [x * factor for x in self] )
	def __div__( self, denominator ):
		return self.__class__( [x / denominator for x in self] )
	def __neg__( self ):
		return self.__class__( [-x for x in self] )
	__invert__ = __neg__
	def __eq__( self, other, tolerance=1e-5 ):
		'''
		overrides equality test - can specify a tolerance if called directly.
		NOTE: other can be any iterable
		'''
		for thisItem, otherItem in zip(self, other):
			if abs( thisItem - otherItem ) > tolerance:
				return False

		return True
	within = __eq__
	def __ne__( self, other, tolerance=1e-5 ):
		return not self.__eq__(other, tolerance)
	def __mod__( self, other ):
		return self.__class__( [x % other for x in self] )
	def __int__( self ):
		return int( self.get_magnitude() )
	def __hash__( self ):
		return tuple( self ).__hash__()
	@classmethod
	def Zero( cls, size=4 ):
		return cls( *([0] * size) )
	@classmethod
	def Random( cls, size=4, range=(0,1) ):
		rands = [random.uniform( *range ) for n in xrange( size )]
		return cls( *rands )
	@classmethod
	def Axis( cls, axisName, size=3 ):
		'''
		returns a vector from an axis name - the axis name can be anything from the Vector.INDEX_NAMES
		list.  you can also use a - sign in front of the axis name
		'''
		axisName = axisName.lower()
		isNegative = axisName.startswith('-')

		if isNegative:
			axisName = axisName[1:]

		new = cls.Zero( size )
		idx = cls.INDEX_NAMES.index( axisName )
		val = 1
		if isNegative:
			val = -1

		new[ idx ] = val

		return new
	def dot( self, other, preNormalize=False ):
		a, b = self, other
		if preNormalize:
			a = self.normalize()
			b = other.normalize()

		dot = sum( [s[0] * s[1] for s in zip(a, b)] )

		return dot
	def __rxor__( self, other ):
		'''
		used for cross product - called using a**b
		NOTE: the cross product is only defined for a 3 vector
		'''
		x = self[1] * other[2] - self[2] * other[1]
		y = self[2] * other[0] - self[0] * other[2]
		z = self[0] * other[1] - self[1] * other[0]

		return self.__class__( [x, y, z] )
	cross = __rxor__
	def get_magnitude( self ):
		return math.sqrt( sum( [x**2 for x in self] ) )
	__float__ = get_magnitude
	__abs__ = get_magnitude
	def set_magnitude( self, factor ):
		'''
		changes the magnitude of this instance
		'''
		factor /= self.get_magnitude()
		for n, val in enumerate(self):
			self[n] *= factor
	mag = length = magnitude = property(get_magnitude, set_magnitude)
	def normalize( self ):
		'''
		returns a normalized vector
		'''
		mag = self.get_magnitude()
		return self.__class__( [v / mag for v in self] )
	def change_space( self, basisX, basisY, basisZ=None ):
		'''
		will re-parameterize this vector to a different space
		NOTE: the basisZ is optional - if not given, then it will be computed from X and Y
		NOTE: changing space isn't supported for 4-vectors
		'''
		if basisZ is None:
			basisZ = basisX ^ basisY
			basisZ.normalize()

		newX = self.dot( basisX )
		newY = self.dot( basisY )
		newZ = self.dot( basisZ )

		self[0], self[1], self[2] = newX, newY, newZ
	def rotate( self, quat ):
		'''
		Return the rotated vector v.

        The quaternion must be a unit quaternion.
        This operation is equivalent to turning v into a quat, computing
        self*v*self.conjugate() and turning the result back into a vec3.
        '''
		ww = quat.w * quat.w
		xx = quat.x * quat.x
		yy = quat.y * quat.y
		zz = quat.z * quat.z
		wx = quat.w * quat.x
		wy = quat.w * quat.y
		wz = quat.w * quat.z
		xy = quat.x * quat.y
		xz = quat.x * quat.z
		yz = quat.y * quat.z

		newX = ww * self.x + xx * self.x - yy * self.x - zz * self.x + 2*((xy-wz) * self.y + (xz+wy) * self.z)
		newY = ww * self.y - xx * self.y + yy * self.y - zz * self.y + 2*((xy+wz) * self.x + (yz-wx) * self.z)
		newZ = ww * self.z - xx * self.z - yy * self.z + zz * self.z + 2*((xz-wy) * self.x + (yz+wx) * self.y)

		return self.__class__( [newX, newY, newZ] )
	def complex( self ):
		return self.__class__( [ complex(v) for v in tuple(self) ] )
	def conjugate( self ):
		return self.__class__( [ v.conjugate() for v in tuple(self.complex()) ] )

	#this is kinda dumb - it'd be nice if this could be auto-derived from the value of INDEX_NAMES but I couldn't get it working so...  meh
	x = property( lambda self: self.getNamedIndex( 'x' ), lambda self, value: self.setNamedIndex( 'x', value ) )
	y = property( lambda self: self.getNamedIndex( 'y' ), lambda self, value: self.setNamedIndex( 'y', value ) )
	z = property( lambda self: self.getNamedIndex( 'z' ), lambda self, value: self.setNamedIndex( 'z', value ) )
	w = property( lambda self: self.getNamedIndex( 'w' ), lambda self, value: self.setNamedIndex( 'w', value ) )


def findMatchingVectors( theVector, vectors, tolerance=1e-6 ):
	'''
	finds vectors that fall within an axis tolerance of theVector - ie the axis values
	of vectors[n] fall within the tolerance boundaries of axis values of theVector.  so
	in other words - this returns all vectors that fall within the bounding box defined
	by the theVector and +/-tolerance

	NOTE: this method assumes that vectors are sorted by x - you can use sortByIdx(vectors)
	to do this...
	'''
	numVectors = len(vectors)

	#do some binary culling before beginning the search - the 200 number is arbitrary,
	#but values less than that don't lead to significant performance improvements
	idx = 0
	theVectorIdx = theVector[idx]
	while numVectors > 200:
		half = numVectors / 2
		halfPoint = vectors[half][idx]

		if (halfPoint + tolerance) < theVectorIdx: vectors = vectors[half:]
		elif (halfPoint - tolerance) > theVectorIdx: vectors = vectors[:half]
		else: break

		numVectors = len(vectors)

	matchingX = []
	for i in vectors:
		diff = i[0] - theVector[0]
		if abs(diff) <= tolerance:
			matchingX.append(i)

	matchingY = []
	for i in matchingX:
		diff = i[1] - theVector[1]
		if abs(diff) <= tolerance:
			matchingY.append(i)

	matching = []
	for i in matchingY:
		diff = i[2] - theVector[2]
		if abs(diff) <= tolerance:
			matching.append(i)

	return matching


def findBestVector( theVector, vectors, tolerance=1e-6 ):
	'''
	given a list of vectors, this method will return the one with the best match based
	on the distance between any two vectors
	'''
	matching = findMatchingVectors(theVector, vectors, tolerance)
	numMatches = len(matching)
	if numMatches == 0:
		return None
	elif numMatches == 1:
		return matching[0]

	#now iterate over the matching vectors and return the best match
	best = matching.pop()
	diff = (best - theVector).mag
	for match in matching:
		curDiff = (match - theVector).mag
		if curDiff < diff:
			best = match
			diff = curDiff

	return best


def sortByIdx( vectorList, idx=0 ):
	'''
	sort the weightData by ascending x values so we can perform binary culling on the
	list when searching
	'''
	sortedByIdx = sorted( [(i[idx], i) for i in vectorList] )
	return [i[1] for i in sortedByIdx]


class Quaternion(Vector):
	def __init__( self, x=0, y=0, z=0, w=1 ):
		'''initialises a vector from either x,y,z,w args or a Matrix instance'''
		if isinstance(x, Matrix):
			#the matrix is assumed to be a valid rotation matrix
			matrix = x
			d1, d2, d3 = matrix.getDiag()
			t = d1 + d2 + d3 + 1.0
			if t > zeroThreshold:
				s = 0.5 / math.sqrt( t )
				w = 0.25 / s
				x = ( matrix[2][1] - matrix[1][2] )*s
				y = ( matrix[0][2] - matrix[2][0] )*s
				z = ( matrix[1][0] - matrix[0][1] )*s
			else:
				if d1 >= d2 and d1 >= d3:
					s = math.sqrt( 1.0 + d1 - d2 - d3 ) * 2.0
					x = 0.5 / s
					y = ( matrix[0][1] + matrix[1][0] )/s
					z = ( matrix[0][2] + matrix[2][0] )/s
					w = ( matrix[1][2] + matrix[2][1] )/s
				elif d2 >= d1 and d2 >= d3:
					s = math.sqrt( 1.0 + d2 - d1 - d3 ) * 2.0
					x = ( matrix[0][1] + matrix[1][0] )/s
					y = 0.5 / s
					z = ( matrix[1][2] + matrix[2][1] )/s
					w = ( matrix[0][2] + matrix[2][0] )/s
				else:
					s = math.sqrt( 1.0 + d3 - d1 - d2 ) * 2.0
					x = ( matrix[0][2] + matrix[2][0] )/s
					y = ( matrix[1][2] + matrix[2][1] )/s
					z = 0.5 / s
					w = ( matrix[0][1] + matrix[1][0] )/s

		Vector.__init__(self, [x, y, z, w])
	def __mul__( self, other ):
		if isinstance( other, Quaternion ):
			x1, y1, z1, w1 = self
			x2, y2, z2, w2 = other

			newW = w1*w2 - x1*x2 - y1*y2 - z1*z2
			newX = w1*x2 + x1*w2 + y1*z2 - z1*y2
			newY = w1*y2 - x1*z2 + y1*w2 + z1*x2
			newZ = w1*z2 + x1*y2 - y1*x2 + z1*w2

			return self.__class__(newX, newY, newZ, newW)
		elif isinstance( other, (float, int, long) ):
			return self.__class__(self.x*other, self.y*other, self.z*other, self.w*other)
	__rmul__ = __mul__
	def __div__( self, other ):
		assert isinstance( other, (float, int, long) )
		return self.__class__(self.x / other, self.y / other, self.z / other, self.w / other)
	def copy( self ):
		return self.__class__(self)
	@classmethod
	def FromEulerXYZ( cls, x, y, z, fromdeg=False ): return cls(Matrix.FromEulerXYZ(x,y,z,fromdeg))
	@classmethod
	def FromEulerYZX( cls, x, y, z, fromdeg=False ): return cls(Matrix.FromEulerYZX(x,y,z,fromdeg))
	@classmethod
	def FromEulerZXY( cls, x, y, z, fromdeg=False ): return cls(Matrix.FromEulerZXY(x,y,z,fromdeg))
	@classmethod
	def FromEulerXZY( cls, x, y, z, fromdeg=False ): return cls(Matrix.FromEulerXZY(x,y,z,fromdeg))
	@classmethod
	def FromEulerYXZ( cls, x, y, z, fromdeg=False ): return cls(Matrix.FromEulerYXZ(x,y,z,fromdeg))
	@classmethod
	def FromEulerZYX( cls, x, y, z, fromdeg=False ): return cls(Matrix.FromEulerZYX(x,y,z,fromdeg))
	@classmethod
	def AxisAngle( cls, axis, angle, normalize=False ):
		'''angle is assumed to be in radians'''
		if normalize:
			axis.normalize()

		angle /= 2.0
		newW = math.cos( angle )
		x, y, z = axis
		s = math.sin( angle ) / math.sqrt( x**2 + y**2 + z**2 )

		newX = x * s
		newY = y * s
		newZ = z * s
		new = cls(newX, newY, newZ, newW)
		new.normalize()

		return new
	def toAngleAxis( self ):
		'''Return angle (in radians) and rotation axis.
		'''

		nself = self.normalize()

		# Clamp nself.w (since the quat has to be normalized it should
		# be between -1 and 1 anyway, but it might be slightly off due
		# to numerical inaccuracies)
		w = max( min(nself.w, 1.0), -1.0 )

		w = math.acos( w )
		s = math.sin( w )
		if s < 1e-12:
			return (0.0, Vector(0, 0, 0))

		return ( 2.0 * w, Vector(nself.x / s, nself.y / s, nself.z / s) )
	def as_tuple( self ):
		return tuple( self )
	def log( self ):
		global zeroThreshold

		b = math.sqrt(self.x**2 + self.y**2 + self.z**2)
		res = self.__class__()
		if abs( b ) <= zeroThreshold:
			if self.w <= zeroThreshold:
				raise ValueError, "math domain error"

			res.w = math.log( self.w )
		else:
			t = math.atan2(b, self.w)
			f = t / b
			res.x = f * self.x
			res.y = f * self.y
			res.z = f * self.z
			ct = math.cos( t )
			if abs( ct ) <= zeroThreshold:
				raise ValueError, "math domain error"

			r = self.w / ct
			if r <= zeroThreshold:
				raise ValueError, "math domain error"

			res.w = math.log( r )

		return res


class Matrix(object):
	'''deals with square matricies'''
	def __init__( self, values=(), size=4 ):
		'''initialises a matrix from either an iterable container of values or a quaternion.  in the
		case of a quaternion the matrix is 3x3'''
		if isinstance(values,Matrix):
			values = values.as_list()
		elif isinstance( values, Quaternion ):
			#NOTE: quaternions result in a 4x4 matrix
			size = 4
			x, y, z, w = values
			xx = 2.0 * x * x
			yy = 2.0 * y * y
			zz = 2.0 * z * z
			xy = 2.0 * x * y
			zw = 2.0 * z * w
			xz = 2.0 * x * z
			yw = 2.0 * y * w
			yz = 2.0 * y * z
			xw = 2.0 * x * w
			row0 = 1.0-yy-zz, xy-zw, xz+yw, 0
			row1 = xy+zw, 1.0-xx-zz, yz-xw, 0
			row2 = xz-yw, yz+xw, 1.0-xx-yy, 0

			values = row0 + row1 + row2 + (0, 0, 0, 1)
		if len(values) > size*size:
			raise MatrixException('too many args: the size of the matrix is %d and %d values were given'%(size,len(values)))
		self.size = size
		self.rows = []

		for n in xrange(size):
			row = [ 0 ] * size
			row[ n ] = 1
			self.rows.append( row )

		for n in xrange( len(values) ):
			self.rows[ n / size ][ n % size ] = values[ n ]
	def __repr__( self ):
		fmt = '%9.4f'
		asStr = []
		for row in self.rows:
			rowStr = []
			for r in row:
				rowStr.append( fmt % r )

			asStr.append( '[%s]' % ','.join( rowStr ) )

		return '\n'.join( asStr )
	def __str__( self ):
		return self.__repr__()
	def __add__( self, other ):
		new = self.__class__.Zero(self.size)
		for i in xrange(self.size):
			for j in xrange(self.size):
				new[i][j] = self[i][j] + other[i][j]

		return new
	def __sub__( self, other ):
		new = self.__class__.Zero(self.size)
		new = self + (other*-1)

		return new
	def __mul__( self, other ):
		new = None
		if isinstance( other, (float, int) ):
			new = self.__class__.Zero(self.size)
			for i in xrange(self.size):
				for j in xrange(self.size):
					new[i][j] = self[i][j] * other
		elif isinstance( other, Vector ):
			new = Vector()
			for i in xrange(self.size):
				#vector indicies
				for j in xrange(4):
					#matrix indicies
					new[i] += other[j] * self[i][j]
		else:
			#otherwise assume is a Matrix instance
			new = self.__class__.Zero(self.size)

			cur = self
			if self.size != other.size:
				#if sizes are differnet - shoehorn the smaller matrix into a bigger matrix
				if self.size < other.size: cur = self.__class__(self,other.size)
				else: other = self.__class__(other,self.size)
			for i in xrange(self.size):
				for j in xrange(self.size):
					new[i][j] = Vector( *cur.getRow(i) ) * Vector( *other.getCol(j) )

		return new
	def __div__( self, other ):
		return self.__mul__(1.0/other)
	def __getitem__( self, item ):
		'''matrix is indexed as: self[row][column]'''
		return self.rows[item]
	def __setitem__( self, item, newRow ):
		if len(newRow) != self.size: raise MatrixException( 'row length not of correct size' )
		self.rows[item] = newRow
	def __eq__( self, other ):
		return self.isEqual(other)
	def __ne__( self, other ):
		return not self.isEqual(other)
	def isEqual( self, other, tolerance=1e-5 ):
		if self.size != other.size:
			return False
		for i in xrange(self.size):
			for j in xrange(self.size):
				if abs( self[i][j] - other[i][j] ) > tolerance:
					return False

		return True
	def copy( self ):
		return self.__class__(self,self.size)
	#some alternative ways to build matrix instances
	@classmethod
	def Zero( cls, size=4 ):
		new = cls([0]*size*size,size)
		return new
	@classmethod
	def Identity( cls, size=4 ):
		rows = [0]*size*size
		for n in xrange(size):
			rows[n+(n*size)] = 1

		return cls(rows,size)
	@classmethod
	def Random( cls, size=4, range=(0,1) ):
		rows = []
		import random
		for n in xrange(size*size):
			rows.append(random.uniform(*range))

		return cls(rows,size)
	@classmethod
	def RotateFromTo( cls, fromVec, toVec, normalize=False ):
		'''Returns a rotation matrix that rotates one vector into another

		The generated rotation matrix will rotate the vector from into
		the vector to. from and to must be unit vectors'''
		e = fromVec*toVec
		f = e.mag

		if f > 1.0-zeroThreshold:
			#from and to vector almost parallel
			fx = abs(fromVec.x)
			fy = abs(fromVec.y)
			fz = abs(fromVec.z)

			if fx < fy:
				if fx < fz: x = Vector(1.0, 0.0, 0.0)
				else: x = Vector(0.0, 0.0, 1.0)
			else:
				if fy < fz: x = Vector(0.0, 1.0, 0.0)
				else: x = Vector(0.0, 0.0, 1.0)

			u = x-fromVec
			v = x-toVec

			c1 = 2.0/(u*u)
			c2 = 2.0/(v*v)
			c3 = c1*c2*u*v

			res = cls(size=3)
			for i in xrange(3):
				for j in xrange(3):
					res[i][j] =  - c1*u[i]*u[j] - c2*v[i]*v[j] + c3*v[i]*u[j]
				res[i][i] += 1.0

			return res
		else:
			#the most common case unless from == to, or from == -to
			v = fromVec^toVec
			h = 1.0/(1.0 + e)
			hvx = h*v.x
			hvz = h*v.z
			hvxy = hvx*v.y
			hvxz = hvx*v.z
			hvyz = hvz*v.y

			row0 = e + hvx*v.x, hvxy - v.z, hvxz + v.y
			row1 = hvxy + v.z, e + h*v.y*v.y,hvyz - v.x
			row2 = hvxz - v.y, hvyz + v.x, e + hvz*v.z

			return cls( row0+row1+row2 )
	@classmethod
	def FromEulerXYZ( cls, x, y, z, fromdeg=False ):
		if fromdeg: x,y,z = map(math.radians,(x,y,z))
		A = math.cos(x)
		B = math.sin(x)
		C = math.cos(y)
		D = math.sin(y)
		E = math.cos(z)
		F = math.sin(z)
		AE = A*E
		AF = A*F
		BE = B*E
		BF = B*F

		row0 = ( C*E, -C*F, D )
		row1 = ( AF+BE*D, AE-BF*D, -B*C )
		row2 = ( BF-AE*D, BE+AF*D, A*C )

		return cls( row0+row1+row2, 3 )
	@classmethod
	def FromEulerYZX( cls, x, y, z, fromdeg=False ):
		if fromdeg: x,y,z = map(math.radians,(x,y,z))
		A = math.cos(x)
		B = math.sin(x)
		C = math.cos(y)
		D = math.sin(y)
		E = math.cos(z)
		F = math.sin(z)
		AC = A*C
		AD = A*D
		BC = B*C
		BD = B*D

		row0 = ( C*E, BD-AC*F, BC*F+AD )
		row1 = ( F, A*E, -B*E )
		row2 = ( -D*E, AD*F+BC, AC-BD*F )

		return cls( row0+row1+row2, 3 )
	@classmethod
	def FromEulerZXY( cls, x, y, z, fromdeg=False ):
		if fromdeg: x,y,z = map(math.radians,(x,y,z))
		A = math.cos(x)
		B = math.sin(x)
		C = math.cos(y)
		D = math.sin(y)
		E = math.cos(z)
		F = math.sin(z)
		CE = C*E
		CF = C*F
		DE = D*E
		DF = D*F

		row0 = ( CE-DF*B, -A*F, DE+CF*B )
		row1 = ( CF+DE*B, A*E, DF-CE*B )
		row2 = ( -A*D, B, A*C )

		return cls( row0+row1+row2, 3 )
	@classmethod
	def FromEulerXZY( cls, x, y, z, fromdeg=False ):
		if fromdeg: x,y,z = map(math.radians,(x,y,z))
		A = math.cos(x)
		B = math.sin(x)
		C = math.cos(y)
		D = math.sin(y)
		E = math.cos(z)
		F = math.sin(z)
		AC = A*C
		AD = A*D
		BC = B*C
		BD = B*D

		row0 = ( C*E, -F, D*E )
		row1 = ( AC*F+BD, A*E, AD*F-BC )
		row2 = ( BC*F-AD, B*E, BD*F+AC )

		return cls( row0+row1+row2, 3 )
	@classmethod
	def FromEulerYXZ( cls, x, y, z, fromdeg=False ):
		if fromdeg: x,y,z = map(math.radians,(x,y,z))
		A = math.cos(x)
		B = math.sin(x)
		C = math.cos(y)
		D = math.sin(y)
		E = math.cos(z)
		F = math.sin(z)
		CE = C*E
		CF = C*F
		DE = D*E
		DF = D*F

		row0 = ( CE+DF*B, DE*B-CF, A*D )
		row1 = ( A*F, A*E, -B )
		row2 = ( CF*B-DE, DF+CE*B, A*C )

		return cls( row0+row1+row2, 3 )
	@classmethod
	def FromEulerZYX( cls, x, y, z, fromdeg=False ):
		if fromdeg: x,y,z = map(math.radians,(x,y,z))
		A = math.cos(x)
		B = math.sin(x)
		C = math.cos(y)
		D = math.sin(y)
		E = math.cos(z)
		F = math.sin(z)
		AE = A*E
		AF = A*F
		BE = B*E
		BF = B*F

		row0 = ( C*E, BE*D-AF, AE*D+BF )
		row1 = ( C*F, BF*D+AE, AF*D-BE )
		row2 = ( -D, B*C, A*C )

		return cls( row0+row1+row2, 3 )
	def getRow( self, row ):
		return self.rows[row]
	def setRow( self, row, newRow ):
		if len(newRow) > self.size: newRow = newRow[:self.size]
		if len(newRow) < self.size:
			newRow.extend( [0] * (self.size-len(newRow)) )

		self.rows = newRow

		return newRow
	def getCol( self, col ):
		column = [0]*self.size
		for n in xrange(self.size):
			column[n] = self.rows[n][col]

		return column
	def setCol( self, col, newCol ):
		newColActual = []
		for n in xrange(min(self.size,len(newCol))):
			self.rows[n] = newCol[n]
			newColActual.append(newCol[n])

		return newColActual
	def getDiag( self ):
		diag = []
		for i in xrange(self.size):
			diag.append( self[i][i] )
		return diag
	def setDiag( self, diag ):
		for i in xrange(self.size):
			self[i][i] = diag[i]
		return diag
	def swapRow( self, nRowA, nRowB ):
		rowA = self.getRow(nRowA)
		rowB = self.getRow(nRowB)
		tmp = rowA
		self.setRow(nRowA,rowB)
		self.setRow(nRowB,tmp)
	def swapCol( self, nColA, nColB ):
		colA = self.getCol(nColA)
		colB = self.getCol(nColB)
		tmp = colA
		self.setCol(nColA,colB)
		self.setCol(nColB,tmp)
	def transpose( self ):
		new = self.__class__.Zero(self.size)
		for i in xrange(self.size):
			for j in xrange(self.size):
				new[i][j] = self[j][i]

		return new
	def transpose3by3( self ):
		new = self.copy()
		for i in xrange(3):
			for j in xrange(3):
				new[i][j] = self[j][i]

		return new
	def det( self ):
		'''calculates the determinant for an arbitrarily sized square matrix'''
		d = 0
		if self.size <= 0: return 1
		for i in xrange(self.size):
			sign = (1,-1)[ i % 2 ]
			cofactor = self.cofactor(i,0)
			d += sign * self[i][0] * cofactor.det()

		return d
	determinant = det
	def cofactor( self, aI, aJ ):
		cf = self.__class__(size=self.size-1)
		cfi = 0
		for i in xrange(self.size):
			if i == aI: continue
			cfj = 0
			for j in xrange(self.size):
				if j == aJ: continue
				cf[cfi][cfj] = self[i][j]
				cfj += 1
			cfi += 1

		return cf
	minor = cofactor
	def isSingular( self ):
		det = self.det()
		if abs(det) < 1e-6: return True,0
		return False,det
	def isRotation( self ):
		'''rotation matricies have a determinant of 1'''
		return ( abs(self.det()) - 1 < 1e-6 )
	def inverse( self ):
		'''Each element of the inverse is the determinant of its minor
		divided by the determinant of the whole'''
		isSingular,det = self.isSingular()
		if isSingular: return self.copy()

		new = self.__class__.Zero(self.size)
		for i in xrange(self.size):
			for j in xrange(self.size):
				sign = (1,-1)[ (i+j) % 2 ]
				new[i][j] = sign * self.cofactor(i,j).det()

		new /= det

		return new.transpose()
	def adjoint( self ):
		new = self.__class__.Zero(self.size)
		for i in xrange(self.size):
			for j in xrange(self.size):
				new[i][j] = (1,-1)[(i+j)%2] * self.cofactor(i,j).det()

		return new.transpose()
	def ortho( self ):
		'''return a matrix with orthogonal base vectors'''
		x = Vector(self[0][:3])
		y = Vector(self[1][:3])
		z = Vector(self[2][:3])

		xl = x.mag
		xl *= xl
		y = y - ((x*y)/xl)*x
		z = z - ((x*z)/xl)*x

		yl = y.mag
		yl *= yl
		z = z - ((y*z)/yl)*y

		row0 = ( x.x, y.x, z.x )
		row1 = ( x.y, y.y, z.y )
		row2 = ( x.z, y.z, z.z )

		return self.__class__(row0+row1+row2,size=3)
	def decompose( self ):
		'''decomposes the matrix into a rotation and scaling part.
	    returns a tuple (rotation, scaling). the scaling part is given
	    as a 3-tuple and the rotation a Matrix(size=3)'''
		dummy = self.ortho()

		x = dummy[0]
		y = dummy[1]
		z = dummy[2]
		xl = x.mag
		yl = y.mag
		zl = z.mag
		scale = xl,yl,zl

		x/=xl
		y/=yl
		z/=zl
		dummy.setCol(0,x)
		dummy.setCol(1,y)
		dummy.setCol(2,z)
		if dummy.det() < 0:
			dummy.setCol(0,-x)
			scale.x = -scale.x

		return (dummy, scale)
	def get_position( self ):
		return Vector( *self[3][:3] )
	def set_position( self, pos ):
		pos = Vector( pos )
		self[3][:3] = pos
	pos = property(get_position,set_position)

	def ToEulerXYZ2( self, asdeg=False ):
		#get basis vectors
		fwd = Vector( [1, 0, 0] ) * self
		left = Vector( [0, 1, 0] ) * self
		up = Vector( [0, 0, 1] ) * self

		xyDist = math.sqrt( fwd[0]**2 + fwd[1]**2 )
		angles = [0, 0, 0]

		if xyDist > 0.001:
			angles[0] = math.atan2( left[2], up[2] )
			angles[1] = math.atan2( -fwd[2], xyDist )
			angles[2] = math.atan2( fwd[1], fwd[0] )
		else:
			angles[0] = 0
			angles[1] = math.atan2( fwd[2], xyDist )
			angles[2] = math.atan2( left[0], left[1] )

		if asdeg: return map(math.degrees, angles)
		return angles
	#the following methods return euler angles of a rotation matrix
	def ToEulerXYZ( self, asdeg=False ):
		r1 = self[0]
		r2 = self[1]
		r3 = self[2]

		D = r1[2]
		y = math.asin(D)
		C = math.cos(y)

		if C > zeroThreshold:
			try: x = math.acos(r3[2]/C)
			except ValueError: x = 180

			try: z = math.acos(r1[0]/C)
			except ValueError: z = 180
		else:
			z = 0.0
			x = math.acos(r2[1])

		angles = [-x, -y, -z]
		if asdeg: return map(math.degrees, angles)
		return angles
	def ToEulerYZX( self, asdeg=False ):
		r1 = self[0]
		r2 = self[1]
		r3 = self[2]

		F = r2[0]
		z = math.asin(F)
		E = math.cos(z)

		if E > zeroThreshold:
			x = math.acos(r2[1]/E)
			y = math.acos(r1[0]/E)
		else:
			y = 0.0
			x = math.asin(r3[1])

		angles = [-x, -y, -z]
		if asdeg: return map(math.degrees, angles)
		return angles
	def ToEulerZXY( self, asdeg=False ):
		r1 = self[0]
		r2 = self[1]
		r3 = self[2]

		B = r3[1]
		x = math.asin(B)
		A = math.cos(x)

		if A > zeroThreshold:
			y = math.acos(r3[2]/A)
			z = math.acos(r2[1]/A)
		else:
			z = 0.0
			y = math.acos(r1[0])

		angles = [-x, -y, -z]
		if asdeg: return map(math.degrees, angles)
		return angles
	def ToEulerXZY( self, asdeg=False ):
		r1 = self[0]
		r2 = self[1]
		r3 = self[2]

		F = -r1[1]
		z = math.asin(F)
		E = math.cos(z)

		if E > zeroThreshold:
			x = math.acos(r2[1]/E)
			y = math.acos(r1[0]/E)
		else:
			y = 0.0
			x = math.acos(r3[2])

		angles = [-x, -y, -z]
		if asdeg: return map(math.degrees, angles)
		return angles
	def ToEulerYXZ( self, asdeg=False ):
		r1 = self[0]
		r2 = self[1]
		r3 = self[2]

		B = -r2[2]
		x = math.asin(B)
		A = math.cos(x)

		if A > zeroThreshold:
			y = math.acos(r3[2]/A)
			z = math.acos(r2[1]/A)
		else:
			z = 0.0
			y = math.acos(r1[0])

		angles = [-x, -y, -z]
		if asdeg: return map(math.degrees, angles)
		return angles
	def ToEulerZYX( self, asdeg=False ):
		r1 = self[0]
		r2 = self[1]
		r3 = self[2]

		D = -r3[0]
		y = math.asin(D)
		C = math.cos(y)

		if C > zeroThreshold:
			x = math.acos(r3[2]/C)
			z = math.acos(r1[0]/C)
		else:
			z = 0.0
			x = math.acos(-r2[1])

		angles = [-x, -y, -z]
		if asdeg: return map(math.degrees, angles)
		return angles
	#some conversion routines
	def as_list( self ):
		list = []
		for i in xrange(self.size):
			list.extend(self[i])

		return list
	def as_tuple( self ):
		return tuple( self.as_list() )

def euler_from_matrix(matrix, axes='rxyz'):
	"""Return Euler angles from rotation matrix for specified axis sequence.

    axes : One of 24 axis sequences as string or encoded tuple

    Note that many Euler angle triplets can describe one matrix.

    >>> R0 = euler_matrix(1, 2, 3, 'syxz')
    >>> al, be, ga = euler_from_matrix(R0, 'syxz')
    >>> R1 = euler_matrix(al, be, ga, 'syxz')
    >>> numpy.allclose(R0, R1)
    True

    """
	try:
		firstaxis, parity, repetition, frame = _AXES2TUPLE[axes.lower()]
	except (AttributeError, KeyError):
		_TUPLE2AXES[axes]
		firstaxis, parity, repetition, frame = axes

	i = firstaxis
	j = _NEXT_AXIS[i+parity]
	k = _NEXT_AXIS[i-parity+1]

	M = matrix
	if repetition:
		sy = math.sqrt( M[i][j] * M[i][j] + M[i][k] * M[i][k] )
		if sy > zeroThreshold:
			ax = math.atan2( M[i][j],  M[i][k] )
			ay = math.atan2( sy,       M[i][i] )
			az = math.atan2( M[j][i], -M[k][i] )
		else:
			ax = math.atan2(-M[j][k],  M[j][j] )
			ay = math.atan2( sy,       M[i][i] )
			az = 0.0
	else:
		cy = math.sqrt( M[i][i] * M[i][i] + M[j][i] * M[j][i] )
		if cy > zeroThreshold:
			ax = math.atan2( M[k][j],  M[k][k] )
			ay = math.atan2(-M[k][i],  cy)
			az = math.atan2( M[j][i],  M[i][i] )
		else:
			ax = math.atan2(-M[j][k],  M[j][j] )
			ay = math.atan2(-M[k][i],  cy )
			az = 0.0

	if not parity:
		ax, ay, az = -ax, -ay, -az
	if frame:
		ax, az = az, ax

	if True: return map(math.degrees, [ax, ay, az])
	return ax, ay, az


_NEXT_AXIS = [1, 2, 0, 1] # axis sequences for Euler angles

_AXES2TUPLE = { # axes string -> (inner axis, parity, repetition, frame)
    "sxyz": (0, 0, 0, 0), "sxyx": (0, 0, 1, 0), "sxzy": (0, 1, 0, 0),
    "sxzx": (0, 1, 1, 0), "syzx": (1, 0, 0, 0), "syzy": (1, 0, 1, 0),
    "syxz": (1, 1, 0, 0), "syxy": (1, 1, 1, 0), "szxy": (2, 0, 0, 0),
    "szxz": (2, 0, 1, 0), "szyx": (2, 1, 0, 0), "szyz": (2, 1, 1, 0),
    "rzyx": (0, 0, 0, 1), "rxyx": (0, 0, 1, 1), "ryzx": (0, 1, 0, 1),
    "rxzx": (0, 1, 1, 1), "rxzy": (1, 0, 0, 1), "ryzy": (1, 0, 1, 1),
    "rzxy": (1, 1, 0, 1), "ryxy": (1, 1, 1, 1), "ryxz": (2, 0, 0, 1),
    "rzxz": (2, 0, 1, 1), "rxyz": (2, 1, 0, 1), "rzyz": (2, 1, 1, 1)}

_TUPLE2AXES = dict((v, k) for k, v in _AXES2TUPLE.items())


#end