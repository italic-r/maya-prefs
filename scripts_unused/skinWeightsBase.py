'''
this module provides code to save and load skinWeight files.  the skinWeight files contain vert skinning data stored
both by position and by index, and as such can be used to restore weights using either method.  the actual maya UI
for this tool is found in zooSkinWeights
'''

from vectors import *
from filesystem import Path, resolvePath, reportUsageToAuthor, writeExportDict
from vs import dmxedit
from vsUtils import DmxFile, iterParents, getJointList
import time, datetime, names, filesystem
from modelpipeline import apps


TOOL_NAME = 'weightSaver'
TOOL_VERSION = 2
DEFAULT_PATH = Path('%TEMP%/temp_skin.weights')
TOL = 1e-6
EXTENSION = 'weights'


class SkinWeightException(Exception): pass
class NoVertFound(Exception): pass


class VertSkinWeight(Vector):
	'''
	extends Vector to store a vert's joint list, weightlist and id
	'''

	#can be used to store a dictionary so mesh names can be substituted at restore time when restoring by id
	MESH_NAME_REMAP_DICT = None

	#can be used to store a dictionary so joint names can be substituted at restore time
	JOINT_NAME_REMAP_DICT = None

	def populate( self, meshName, vertIdx, jointList, weightList ):
		self.idx = vertIdx
		self.weights = weightList

		self.__mesh = meshName
		self.__joints = jointList
	@property
	def mesh( self ):
		'''
		If a MESH_NAME_REMAP Mapping object is present, the mesh name is re-mapped accordingly,
		otherwise the stored mesh name is returned.
		'''
		if self.MESH_NAME_REMAP_DICT is None:
			return self.__mesh

		return self.MESH_NAME_REMAP_DICT.get( self.__mesh, self.__mesh )
	@property
	def joints( self ):
		'''
		Returns the list of joints the vert is skinned to.  If a JOINT_NAME_REMAP Mapping object is
		present, names are re-mapped accordingly.
		'''
		jointRemap = self.JOINT_NAME_REMAP_DICT
		if jointRemap is None:
			return self.__joints

		joints = [ jointRemap.get( j, j ) for j in self.__joints ]

		if len( joints ) != set( joints ):
			joints, self.weights = regatherWeights( joints, self.weights )

		return joints
	def getVertName( self ):
		return '%s.%d' % (self.mesh, self.idx)


class MayaVertSkinWeight(VertSkinWeight):
	'''
	NOTE: this class needs to be defined in this file otherwise weight files saved from maya will be
	unavailable to external tools like modelpipeline because the maya scripts are invisible outside
	of maya.  When unpickling objects - python needs to know what module to find the object's class
	in, so if that module is unavailable, a pickleException is raised when loading the file.
	'''
	def getVertName( self ):
		return '%s.vtx[%d]' % (self.mesh, self.idx)


class WeightSaveData(tuple):
	def __init__( self, data ):
		self.miscData, self.joints, self.jointHierarchies, self.weightData = data
	def getUsedJoints( self ):
		allJoints = set()
		for jData in self.weightData:
			allJoints |= set( jData.joints )

		return allJoints
	def getUsedMeshes( self ):
		allMeshes = set()
		for d in self.weightData:
			allMeshes.add( d.mesh )

		return allMeshes


def getDefaultPath( filepath, dmeMesh=None ):
	if filepath is None:
		if dmeMesh is None:
			raise SkinWeightException

		fileId = dmeMesh.GetFileId()
		fileRoot = vs.dm.GetElement( vs.dm.GetFileRoot( fileId ) )
		fileName = Path( vs.dm.GetFileName( fileId ) )
		srcFile = Path( fileRoot.makefile.sources[ 0 ].name )

		filepath = fileName.up() / srcFile
		#filepath = vs.dm.GetFileName( dmeMesh.GetFileId() )

	filepath = Path( filepath )
	if not filepath.exists:
		raise SkinWeightException

	filepath = filepath.setExtension( EXTENSION )

	return filepath


def findMatchingVectors( theVector, vectors, tolerance=1e-6 ):
	'''
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

	#now the matching vectors is a list of vectors that fall within the bounding box with length of 2*tolerance.
	#we want to reduce this to a list of vectors that fall within the bounding sphere with radius tolerance
	inSphere = []
	for m in matching:
		if (theVector - m).mag <= tolerance:
			inSphere.append( m )

	return inSphere


def findBestVector( theVector, vectors, tolerance=1e-6 ):
	'''
	given a list of vectors, this method will return the one with the best match based
	on the distance between any two vectors
	'''
	matching = findMatchingVectors(theVector, vectors, tolerance)

	#now iterate over the matching vectors and return the best match
	try:
		best = matching.pop()
	except IndexError: return None

	diff = (best - theVector).mag
	for match in matching:
		curDiff = (match - theVector).mag
		if curDiff < diff:
			best = match
			diff = curDiff

	return best


def getDistanceWeightedVector( theVector, vectors, tolerance=1e-6 ):
	matching = findMatchingVectors( theVector, vectors, tolerance )
	try:
		newVec = VertSkinWeight( matching[ 0 ] )
	except IndexError: return

	joints = []
	weights = []
	for v in matching:
		dist = ( v - theVector ).get_magnitude()
		distanceBiasedWeight = (tolerance - dist) / tolerance
		distanceBiasedWeight **= 3  #3 seems to produce magically good results...  tahts all there is to it
		joints += v.joints
		weights += [ w * distanceBiasedWeight for w in v.weights ]

	joints, weights = regatherWeights( joints, weights )
	newVec = VertSkinWeight( matching[ 0 ] )
	newVec.populate( None, -1, joints, weights )

	return newVec


def getWeightsFromDmx( dmxFilepath=None ):
	'''
	loads a dmx and gathers weight data from the meshes present.  the data returned can be fed to the
	applyWeights function to effectively transfer skinning data between meshes of differing topology
	'''
	geoAndData = {}

	#define the data we're gathering
	joints = {}
	jointHierarchies = {}
	weightData = []
	weightDataAppend = weightData.append


	#load the dmx file
	dmxFilepath = DmxFile( dmxFilepath )
	root = dmxFilepath.read()
	model = root.model


	#data gathering time!
	for mesh in dmxedit.MeshIt( model ):
		meshName = mesh.name
		state = mesh.currentState
		try:
			jointWeights = state.jointWeights
			jointIndices = state.jointIndices
		except AttributeError: continue

		jointList = getJointList( mesh )
		jointCount = state.jointCount
		for idx, pos in enumerate( state.positions ):
			baseIdx = idx * jointCount

			#generate the weight list first because if the weight is zero, the jointIndex can potentially be bogus
			weightList = [ jointWeights[ baseIdx + n ] for n in range( jointCount ) ]
			jointIdxList = [ jointIndices[ baseIdx + n ] for n in range( jointCount ) ]

			jointNameList = []
			append = jointNameList.append
			for n, jIdx in enumerate( jointIdxList ):
				try: append( jointList[ jIdx ].name )
				except IndexError:
					assert weightList[ n ] < 1e-6, "weighting refers to a non-existant joint"
					append( jointList[ 0 ].name )


			#so this is kinda dumb - but using a dict here we can easily remap on restore if joint names
			#are different by storing the dict's value as the joint to use, and the key as the joint that
			#the vert was originally weighted to
			for j in jointNameList:
				joints[ j ] = j

			pos = pos.x, pos.y, pos.z
			vertData = VertSkinWeight( pos )
			vertData.populate( meshName, idx, jointNameList, weightList)
			weightDataAppend( vertData )


	#sort the weightData by ascending x values so we can search faster
	weightData = sortByIdx( weightData )


	#generate joint hierarchy data - so if joints are missing on load we can find the best match
	for elt in jointList:
		jointHierarchies[ elt.name ] = [ p for p in iterParents( elt, True ) ]


	#generate the misc data for the weights
	miscData = writeExportDict( TOOL_NAME, TOOL_VERSION, kEXPORT_DICT_SOURCE=dmxFilepath )


	return WeightSaveData( (miscData, joints, jointHierarchies, weightData) )


def applyWeights( dmeMesh, weightData, usePosition=True, tolerance=TOL, axisMult=None, swapParity=True, averageVerts=True, meshNameRemapDict=None, jointNameRemapDict=None ):
	'''
	loads weights back on to a model given a file.  NOTE: the tolerance is an axis tolerance
	NOT a distance tolerance.  ie each axis must fall within the value of the given vector to be
	considered a match - this makes matching a heap faster because vectors can be culled from
	the a sorted list.  possibly implementing some sort of oct-tree class might speed up the
	matching more, but...  the majority of weight loading time at this stage is spent by maya
	actually applying skin weights, not the positional searching
	'''
	assert isinstance( dmeMesh, vs.movieobjects.CDmeMesh )
	reportUsageToAuthor()
	start = time.clock()

	unfoundVerts = []
	miscData, joints, jointHierarchies, weightData = weightData

	if miscData[ filesystem.kEXPORT_DICT_TOOL_VER ] != TOOL_VERSION:
		print( "WARNING: the file being loaded was stored from an older version (%d) of the tool - please re-generate the file.  Current version is %d." % (miscData[ filesystem.kEXPORT_DICT_TOOL_VER ], TOOL_VERSION) )

	#setup the mappings
	VertSkinWeight.MESH_NAME_REMAP_DICT = meshNameRemapDict
	VertSkinWeight.JOINT_NAME_REMAP_DICT = jointNameRemapDict


	#axisMults can be used to alter the positions of verts saved in the weightData array - this is mainly useful for applying
	#weights to a mirrored version of a mesh - so weights can be stored on meshA, meshA duplicated to meshB, and then the
	#saved weights can be applied to meshB by specifying an axisMult=(-1,1,1) OR axisMult=(-1,)
	if axisMult is not None:
		for data in weightData:
			for n, mult in enumerate( axisMult ): data[ n ] *= mult

		#we need to re-sort the weightData as the multiplication could have potentially reversed things...  i could probably
		#be a bit smarter about when to re-order, but its not a huge hit...  so, meh
		weightData = sortByIdx( weightData )

		#using axisMult for mirroring also often means you want to swap parity tokens on joint names - if so, do that now.
		#parity needs to be swapped in both joints and jointHierarchies
		if swapParity:
			for joint, target in joints.iteritems():
				joints[ joint ] = str( names.Name( target ).swap_parity() )
			for joint, parents in jointHierarchies.iteritems():
				jointHierarchies[ joint ] = [ str( names.Name( p ).swap_parity() ) for p in parents ]


	num = dmeMesh.numVerts()
	verts = xrange( num )

	findMethod = findBestVector
	if averageVerts:
		findMethod = getDistanceWeightedVector


	#if we're using position, the restore weights path is quite different
	setVertWeight = dmeMesh.setVertWeight
	if usePosition:
		vertPositions = dmeMesh.currentState.positions
		print "starting first iteration with", len( weightData ), "verts"

		iterationCount = 1
		while True:
			unfoundVerts = []
			unfoundVertsAppend = unfoundVerts.append
			foundVerts = []
			foundVertsAppend = foundVerts.append
			for vert in verts:
				pos = vertPositions[ vert ]
				pos = Vector( (pos.x, pos.y, pos.z) )
				vertData = findMethod(pos, weightData, tolerance)

				try:
					#unpack data to locals
					try:
						jointList, weightList = vertData.joints, vertData.weights
					except AttributeError: raise NoVertFound

					try:
						#re-map joints to their actual values
						actualJointNames = [ joints[ j ] for j in jointList ]

						#check sizes - if joints have been remapped, there may be two entries for a joint
						#in the re-mapped jointList - in this case, we need to re-gather weights
						actualJointsAsSet = set( actualJointNames )
						if len( actualJointsAsSet ) != len( actualJointNames ):
							#so if the set sizes are different, then at least one of the joints is listed twice,
							#so we need to gather up its weights into a single value
							new = {}
							[ new.setdefault(j, 0) for j in actualJointNames ]  #init the dict with 0 values
							for j, w in zip(actualJointNames, weightList):
								new[ j ] += w

							#if the weightList is empty after renormalizing, nothing to do - keep loopin
							actualJointNames, weightList = new.keys(), new.values()
							if not weightList: raise NoVertFound
					except KeyError:
						#if there was a key error, then one of the joints was removed from the joints dict
						#as it wasn't found in the scene - so get the missing joints, remove them from the
						#list and renormalize the remaining weights
						jointListSet = set( jointList )
						diff = missingJoints.difference(jointListSet)
						weightList = renormalizeWeights( jointList, weightList, diff )
						actualJointNames = [ joints[ j ] for j in jointList ]

						#if the weightList is empty after renormalizing, nothing to do - keep loopin
						if not weightList: raise NoVertFound

					setVertWeight( vert, actualJointNames, weightList )

					foundVertData = VertSkinWeight( pos )
					foundVertData.populate( vertData.mesh, vertData.idx, actualJointNames, weightList )
					foundVertsAppend( foundVertData )
				except NoVertFound:
					unfoundVertsAppend( vert )

			#so with the unfound verts - sort them, call them "verts" and iterate over them with the newly grown weight data
			#the idea here is that when a vert is found its added to the weight data (in memory not on disk).  by performing
			#another iteration for the previously un-found verts, we should be able to get a better approximation
			verts = unfoundVerts
			if unfoundVerts:
				if foundVerts:
					weightData = sortByIdx( foundVerts )
				else:
					print "### still unfound verts, but no new matches were made in previous iteration - giving up.  %d iterations performed" % iterationCount
					break
			else:
				print "### all verts matched!  %d iterations performed" % iterationCount
				break

			iterationCount += 1
			print "iteration %d - using %d verts (increasing the search radius will reduce iterations)" % (iterationCount, len( weightData ))

	#otherwise simply restore by id
	else:
		#rearrange the weightData structure so its ordered by id
		meshName = dmeMesh.name
		weightDataById = {}
		[ weightDataById.setdefault(i.getVertName(), (i.joints, i.weights)) for i in weightData ]
		for vert in verts:
			try:
				jointList, weightList = weightDataById[ '%s.%d' % (meshName, vert) ]
				setVertWeight( vert, jointList, weightList )
			except KeyError:
				#in this case, the vert doesn't exist in teh file...
				print '### no point found for %s' % vert
				continue

	end = time.clock()
	print 'time for weight load %.02f secs' % (end - start)


def loadWeights( dmeMesh, filepath=None, *a, **kw ):
	'''
	loads weights back on to a model given a file.  NOTE: the tolerance is an axis tolerance
	NOT a distance tolerance.  ie each axis must fall within the value of the given vector to be
	considered a match - this makes matching a heap faster because vectors can be culled from
	the a sorted list.  possibly implementing some sort of oct-tree class might speed up the
	matching more, but...  the majority of weight loading time at this stage is spent by maya
	actually applying skin weights, not the positional searching
	'''
	if filepath is None:
		filepath = getDefaultPath( filepath, dmeMesh )

	applyWeights( dmeMesh, filepath.unpickle(), *a, **kw )


def getUsedJoints( filepath ):
	return WeightSaveData( filepath.unpickle() ).getUsedJoints()


def getWeightFileSource( filepath ):
	miscData, joints, jointHierarchies, weightData = filepath.unpickle()
	try:
		return Path( miscData[ apps.kEXPORT_DICT_SOURCE ] )
	except KeyError:
		return None


def normalizeWeightList( weightList ):
	sortedWeightList = sorted( weightList )
	smallestViable = sortedWeightList[ 0 ]

	weightSum = sum( sortedWeightList )
	try:
		return [ w / weightSum if w >= smallestViable else 0 for w in weightList ]
	except ZeroDivisionError:
		return []


def renormalizeWeights( jointList, weightList, missingJoints ):
	''' '''
	for item in missingJoints:
		try:
			idx = jointList.index( item )
			jointList.pop( idx )
			weightList.pop( idx )
		#its possible that the jointList doesn't actually contain the missing joint - so we need
		#to catch this possibility...
		except ValueError: continue

	weightSum = sum( weightList )
	try:
		return [ w / weightSum for w in weightList ]
	except ZeroDivisionError:
		return []


def regatherWeights( actualJointNames, weightList ):
	'''
	re-gathers weights.  when joints are re-mapped (when the original joint can't be found) there is
	the potential for joints to be present multiple times in the jointList - in this case, weights
	need to be summed for the duplicate joints otherwise maya doesn't weight the vert properly (dupes
	just get ignored)
	'''
	new = {}
	[ new.setdefault(j, 0) for j in actualJointNames ]
	for j, w in zip( actualJointNames, weightList ):
		new[ j ] += w

	return new.keys(), new.values()


#end
