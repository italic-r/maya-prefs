'''
this module provides code to save and load skinWeight files.  the skinWeight files contain vert skinning data stored
both by position and by index, and as such can be used to restore weights using either method.  the actual maya UI
for this tool is found in zooSkinWeights
'''

from skinWeightsBase import *
from api import melPrint
import maya.cmds as cmd
import api


VertSkinWeight = MayaVertSkinWeight


def getAllParents( object ):
	allParents = []
	parent = [object]
	while parent is not None:
		allParents.append(parent[0])
		parent = cmd.listRelatives(parent,parent=True,pa=True)
	return allParents[1:]


def getDefaultPath():
	scenePath = cmd.file(q=True, sn=True)
	if not scenePath:
		return DEFAULT_PATH

	scenePath = Path( scenePath )
	scenePath = scenePath.setExtension( EXTENSION )

	return scenePath


kAPPEND = 0
kREPLACE = 1
@api.d_showWaitCursor
def saveWeights( geos, filepath=None, mode=kAPPEND ):
	reportUsageToAuthor()
	start = time.clock()
	miscData = api.writeExportDict(TOOL_NAME, TOOL_VERSION)

	#if filepath is None, then generate a default filepath based on the location of the file
	if filepath is None:
		filepath = getDefaultPath()
	else: filepath = Path(filepath)

	geoAndData = {}
	skinPercent = cmd.skinPercent
	xform = cmd.xform

	#define teh data we're gathering
	joints = {}
	jointHierarchies = {}
	weightData = []

	#does the weight file already exist?  if so, load it up and append data if append mode is true
	if filepath.exists and mode == kAPPEND:
		tmpA, joints, jointHierarchies, weightData = filepath.unpickle()

	#data gathering time!
	for geo in geos:
		geoNode = geo
		verts = cmd.ls(cmd.polyListComponentConversion(geo, toVertex=True), fl=True)
		skinClusters = cmd.ls(cmd.listHistory(geo), type='skinCluster')
		if len(skinClusters) > 1:
			api.melWarning("more than one skinCluster found on %s" % geo)
			continue

		try: skinCluster = skinClusters[0]
		except IndexError:
			msg = "cannot find a skinCluster for %s" % geo
			api.melWarning(msg)
			#raise SkinWeightException(msg)

		for idx, vert in enumerate(verts):
			jointList = skinPercent(skinCluster, vert, ib=1e-4, q=True, transform=None)
			weightList = skinPercent(skinCluster, vert, ib=1e-4, q=True, value=True)
			if jointList is None:
				raise SkinWeightException("I can't find any joints - sorry.  do you have any post skin cluster history???")

			#so this is kinda dumb - but using a dict here we can easily remap on restore if joint names
			#are different by storing the dict's value as the joint to use, and the key as the joint that
			#the vert was originally weighted to
			for j in jointList:
				joints[j] = j

			pos = xform(vert, q=True, ws=True, t=True)
			vertData = VertSkinWeight( pos )
			vertData.populate(geo, idx, jointList, weightList)
			weightData.append(vertData)

		#lastly, add an attribute to the object describing where the weight file exists
		dirOfCurFile = Path(cmd.file(q=True,sn=True)).up()
		if geoNode.find('.') != -1: geoNode = geo.split('.')[0]
		if not cmd.objExists('%s.weightSaveFile' % geoNode):
			cmd.addAttr(geoNode, ln='weightSaveFile', dt='string')

		relToCur = filepath.relativeTo(dirOfCurFile)
		if relToCur is None: relToCur = filepath
		cmd.setAttr('%s.weightSaveFile' % geoNode, relToCur.asfile(), type='string')

	#sort the weightData by ascending x values so we can search faster
	weightData = sortByIdx(weightData)

	#generate joint hierarchy data - so if joints are missing on load we can find the best match
	for j in joints.keys():
		jointHierarchies[j] = getAllParents(j)

	toWrite = miscData, joints, jointHierarchies, weightData

	filepath = Path(filepath)
	filepath.pickle(toWrite, False)
	melPrint('Weights Successfully %s to %s: time taken %.02f seconds' % ('Saved' if mode == kREPLACE else 'Appended', filepath.resolve(), time.clock()-start))

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


def findBestVector( theVector, vectors, tolerance=1e-6, doPreview=False ):
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

	if doPreview:
		cmd.select( best.getVertName() )
		print "skinning data"
		for x in zip( best.joints, best.weights ): print x
		raise Exception, 'preview mode'

	return best


def getDistanceWeightedVector( theVector, vectors, tolerance=1e-6, doPreview=False ):
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

	if doPreview:
		cmd.select( [ m.getVertName() for m in matching ] )
		print "skinning data"
		for x in zip( newVec.joints, newVec.weights ): print x
		raise Exception, "in preview mode"

	return newVec


@api.d_progress(t='initializing...', status='initializing...', isInterruptable=True)
def loadWeights( objects, filepath=None, usePosition=True, tolerance=TOL, axisMult=None, swapParity=True, averageVerts=True, doPreview=False, meshNameRemapDict=None, jointNameRemapDict=None ):
	'''
	loads weights back on to a model given a file.  NOTE: the tolerance is an axis tolerance
	NOT a distance tolerance.  ie each axis must fall within the value of the given vector to be
	considered a match - this makes matching a heap faster because vectors can be culled from
	the a sorted list.  possibly implementing some sort of oct-tree class might speed up the
	matching more, but...  the majority of weight loading time at this stage is spent by maya
	actually applying skin weights, not the positional searching
	'''
	reportUsageToAuthor()
	start = time.clock()


	#setup the mappings
	VertSkinWeight.MESH_NAME_REMAP_DICT = meshNameRemapDict
	VertSkinWeight.JOINT_NAME_REMAP_DICT = jointNameRemapDict


	#cache heavily access method objects as locals...
	skinPercent = cmd.skinPercent
	progressWindow = cmd.progressWindow
	xform = cmd.xform

	#now get a list of all weight files that are listed on the given objects - and
	#then load them one by one and apply them to the appropriate objects
	filesAndGeos = {}
	dirOfCurFile = Path(cmd.file(q=True,sn=True)).up()
	for obj in objects:
		items = []  #this holds the vert list passed in IF any
		if obj.find('.') != -1:
			items = [obj]
			obj = obj.split('.')[0]

		try:
			file = Path( dirOfCurFile + cmd.getAttr('%s.weightSaveFile' % obj) if filepath is None else filepath )
			if file.exists and not file.isfile():
				raise TypeError()
		except TypeError:
			#in this case, no weightSave file existed on the object, so try using the default file if it exists
			file = getDefaultPath() if filepath is None else filepath
			if not file.exists:
				api.melError('cant find a weightSaveFile for %s - skipping' % obj)
				continue

		filesAndGeos.setdefault(file, {})
		try: filesAndGeos[file][obj].extend( items )
		except KeyError: filesAndGeos[file][obj] = items

	print filesAndGeos

	unfoundVerts = []
	for filepath, objItemsDict in filesAndGeos.iteritems():
		numItems = len(objItemsDict)
		curItem = 1
		progressWindow(e=True, title='loading weights from file %d items' % numItems)

		miscData, joints, jointHierarchies, weightData = Path(filepath).unpickle()
		if miscData[ api.kEXPORT_DICT_TOOL_VER ] != TOOL_VERSION:
			api.melWarning( "WARNING: the file being loaded was stored from an older version (%d) of the tool - please re-generate the file.  Current version is %d." % (miscData[ api.kEXPORT_DICT_TOOL_VER ], TOOL_VERSION) )

		for geo, items in objItemsDict.iteritems():
			#the miscData contains a dictionary with a bunch of data stored from when the weights was saved - do some
			#sanity checking to make sure we're not loading weights from some completely different source
			curFile = cmd.file(q=True, sn=True)
			origFile = miscData['scene']
			if curFile != origFile:
				api.melWarning('the file these weights were saved in a different file from the current: "%s"' % origFile)
				#response = cmd.confirmDialog(t='files differ...', m='the file these weights were saved from was %s\nthis is different from your currently opened file.\n\nis that OK?' % origFile, b=('Proceed', 'Cancel'), db='Proceed')
				#if response == 'Cancel': return


			#axisMults can be used to alter the positions of verts saved in the weightData array - this is mainly useful for applying
			#weights to a mirrored version of a mesh - so weights can be stored on meshA, meshA duplicated to meshB, and then the
			#saved weights can be applied to meshB by specifying an axisMult=(-1,1,1) OR axisMult=(-1,)
			if axisMult is not None:
				for data in weightData:
					for n, mult in enumerate(axisMult): data[n] *= mult

				#we need to re-sort the weightData as the multiplication could have potentially reversed things...  i could probably
				#be a bit smarter about when to re-order, but its not a huge hit...  so, meh
				weightData = sortByIdx(weightData)

				#using axisMult for mirroring also often means you want to swap parity tokens on joint names - if so, do that now.
				#parity needs to be swapped in both joints and jointHierarchies
				if swapParity:
					for joint, target in joints.iteritems():
						joints[joint] = str( names.Name(target).swap_parity() )
					for joint, parents in jointHierarchies.iteritems():
						jointHierarchies[joint] = [str( names.Name(p).swap_parity() ) for p in parents]


			#if the geo is None, then check for data in the verts arg - the user may just want weights
			#loaded on a specific list of verts - we can get the geo name from those verts
			skinCluster = ''
			verts = cmd.ls(cmd.polyListComponentConversion(items if items else geo, toVertex=True), fl=True)


			#remap joint names in the saved file to joint names that are in the scene - they may be namespace differences...
			missingJoints = set()
			for j in joints.keys():
				if not cmd.objExists(j):
					#see if the joint with the same leaf name exists in the scene
					idxA = j.rfind(':')
					idxB = j.rfind('|')
					idx = max(idxA, idxB)
					if idx != -1:
						leafName = j[idx:]
						search = cmd.ls('%s*' % leafName, r=True, type='joint')
						if len(search):
							joints[j] = search[0]


			#now that we've remapped joint names, we go through the joints again and remap missing joints to their nearest parent
			#joint in the scene - NOTE: this needs to be done after the name remap so that parent joint names have also been remapped
			for j, jRemap in joints.iteritems():
				if not cmd.objExists(jRemap):
					dealtWith = False
					for n, jp in enumerate(jointHierarchies[j]):
						#if n > 2: break
						remappedJp = jp
						if jp in joints: remappedJp = joints[jp]
						if cmd.objExists(remappedJp):
							joints[j] = remappedJp
							dealtWith = True
							break

					if dealtWith: continue
					missingJoints.add(j)


			#now remove them from the list
			[joints.pop(j) for j in missingJoints]
			for key, value in joints.iteritems():
				if key != value:
					print '%s remapped to %s' % (key, value)

			#do we have a skinCluster on the geo already?  if not, build one
			skinCluster = cmd.ls(cmd.listHistory(geo), type='skinCluster')
			if not skinCluster:
				skinCluster = cmd.skinCluster(geo,joints.values())[0]
				verts = cmd.ls(cmd.polyListComponentConversion(geo, toVertex=True), fl=True)
			else: skinCluster = skinCluster[0]

			num = len(verts)
			cur = 0.0
			inc = 100.0/num

			findMethod = findBestVector
			if averageVerts:
				findMethod = getDistanceWeightedVector

			#if we're using position, the restore weights path is quite different
			if usePosition:
				progressWindow(edit=True, status='searching by position: %s (%d/%d)' % (geo, curItem, numItems))
				queue = api.CmdQueue()

				print "starting first iteration with", len( weightData ), "verts"

				iterationCount = 1
				while True:
					unfoundVerts = []
					foundVerts = []
					for vert in verts:
						progressWindow(edit=True, progress=cur)
						cur += inc

						pos = Vector( xform(vert, q=True, ws=True, t=True) )
						vertData = findMethod(pos, weightData, tolerance, doPreview)

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
								jointListSet = set(jointList)
								diff = missingJoints.difference(jointListSet)
								weightList = renormalizeWeights(jointList, weightList, diff)
								actualJointNames = [ joints[ j ] for j in jointList ]

								#if the weightList is empty after renormalizing, nothing to do - keep loopin
								if not weightList: raise NoVertFound

							#normalize the weightlist
							weightList = normalizeWeightList( weightList )

							#zip the joint names and their corresponding weight values together (as thats how maya
							#accepts the data) and fire off the skinPercent cmd
							jointsAndWeights = zip(actualJointNames, weightList)

							queue.append( 'skinPercent -tv %s %s %s' % (' -tv '.join( [ '%s %s' % t for t in jointsAndWeights ] ), skinCluster, vert) )
							foundVertData = VertSkinWeight( pos )
							foundVertData.populate( vertData.mesh, vertData.idx, actualJointNames, weightList )
							foundVerts.append( foundVertData )
						except NoVertFound:
							unfoundVerts.append( vert )
							#print '### no point found for %s' % vert

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
					print "starting iteration %d - using" % iterationCount, len( weightData ), "verts"
					#for www in weightData: print www

				#bail if we've been asked to cancel
				if progressWindow(q=True, isCancelled=True):
					progressWindow(ep=True)
					return

				progressWindow(e=True, status='maya is setting skin weights...')
				queue()

			#otherwise simply restore by id
			else:
				progressWindow(edit=True, status='searching by vert name: %s (%d/%d)' % (geo, curItem, numItems))
				queue = api.CmdQueue()

				#rearrange the weightData structure so its ordered by vertex name
				weightDataById = {}
				[ weightDataById.setdefault(i.getVertName(), (i.joints, i.weights)) for i in weightData ]

				for vert in verts:
					progressWindow(edit=True, progress=cur / num * 100.0)
					if progressWindow(q=True, isCancelled=True):
						progressWindow(ep=True)
						return

					cur += 1
					try:
						jointList, weightList = weightDataById[vert]
					except KeyError:
						#in this case, the vert doesn't exist in teh file...
						print '### no point found for %s' % vert
						continue
					else:
						jointsAndWeights = zip(jointList, weightList)
						skinPercent(skinCluster, vert, tv=jointsAndWeights)

			#remove unused influences from the skin cluster
			cmd.skinCluster(skinCluster, edit=True, removeUnusedInfluence=True)
			curItem += 1

	if unfoundVerts: cmd.select( unfoundVerts )
	end = time.clock()
	api.melPrint('time for weight load %.02f secs' % (end-start))


MAX_INFLUENCE_COUNT = 3
def normalizeWeightList( weightList ):
	sortedWeightList = sorted( weightList )[ -MAX_INFLUENCE_COUNT: ]
	smallestViable = sortedWeightList[ 0 ]

	weightSum = sum( sortedWeightList )
	try:
		return [ w / weightSum if w >= smallestViable else 0 for w in weightList ]
	except ZeroDivisionError:
		return []


def printDataFromFile( filepath=DEFAULT_PATH ):
	miscData,geoAndData = presets.PresetPath( filepath ).unpickle()
	for geo, data in geoAndData.iteritems():
		print geo,'------------'
		joints, weightData = data
		for joint in joints:
			print '\t', joint
		print


def printDataFromSelection( filepath=DEFAULT_PATH, tolerance=1e-4 ):
	miscData,geoAndData = presets.PresetPath(filepath).unpickle()
	selVerts = cmd.ls( cmd.polyListComponentConversion( cmd.ls( sl=True ), toVertex=True ), fl=True )
	selGeo = {}
	for v in selVerts:
		idx = v.rfind('.')
		geo = v[ :idx ]
		vec = Vector( cmd.xform( v, q=True, t=True, ws=True ) )
		try:
			selGeo[ geo ].append( ( vec, v ) )
		except KeyError:
			selGeo[ geo ] = [ ( vec, v ) ]

	#make sure the geo selected is actually in the file...
	names = selGeo.keys()
	for geo in names:
		try:
			geoAndData[ geo ]
		except KeyError:
			selGeo.pop( item )

	for geo,vecAndVert in selGeo.iteritems():
		joints, jointHierarchies, weightData = geoAndData[ geo ]
		weightData = sortByIdx( weightData )
		for vec, vertName in vecAndVert:
			try:
				vertData = findBestVector( vec, weightData, tolerance )
				jointList, weightList = vertData.joints, vertData.weights
				tmpStr = []
				for items in zip( jointList, weightList ):
					tmpStr.append( '(%s %0.3f)' % items )
				print '%s: %s' % ( vertName, '  '.join( tmpStr ) )
			except AttributeError:
				print '%s no match'


def mirrorWeightsOnSelected( tolerance=TOL ):
	selObjs = cmd.ls(sl=True, o=True)

	#so first we need to grab the geo to save weights for - we save geo for all objects which have
	#verts selected
	saveWeights( selObjs, Path('%TEMP%/tmp.weights'), mode=kREPLACE )
	loadWeights( cmd.ls(sl=True), Path( '%TEMP%/tmp.weights' ), True, 2, (-1,), True )


#end