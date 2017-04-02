import maya.OpenMaya as om

def getGlobalTransform(node, tfmPlug="worldMatrix"):
	fn = om.MFnTransform(node)
	plug = fn.findPlug(tfmPlug)

	if plug.isArray():
		plug = plug.elementByLogicalIndex(0)

	mat = plug.asMObject()
	fnMat = om.MFnMatrixData(mat)

	return fnMat.transformation()


def matchTransform(nodes, source, translate=True, rotate=True, scale=True, space=om.MSpace.kWorld, matchPivot=False):
	nodeList = []
	if isinstance(nodes, list):
		nodeList = nodes
	elif isinstance(nodes, om.MSelectionList):
		for i in xrange(nodes.length()):
			dagNode = om.MDagPath()
			nodes.getDagPath(i, dagNode)
			nodeList.append(dagNode)
	elif isinstance(nodes, om.MObject):
		nodeList.append(om.MDagPath.getAPathTo(nodes))
	elif isinstance(nodes, om.MDagPath):
		nodeList.append(nodes)
	elif isinstance(nodes, om.MDagPathArray):
		for i in xrange(nodes.length()):
			nodeList.append(nodes[i])
	else:
		raise RuntimeError("incorrect type: nodes")
		
	# get the proper matrix of source
	if space == om.MSpace.kWorld:
		srcTfm = getGlobalTransform(source, "worldMatrix")
	else:
		srcTfm = getGlobalTransform(source, "matrix")

	# source pos
	pos = srcTfm.getTranslation(space)

	# source pivot
	srcPivot = srcTfm.scalePivot(space)

	# stupid MScriptUtil stuff
	util = om.MScriptUtil()
	util.createFromDouble(0.0, 0.0, 0.0)
	scl = util.asDoublePtr()

	fn = om.MFnTransform()
	for node in nodeList:
		if space == om.MSpace.kObject:
			tfm = srcTfm
		else:
			# multiply the global scale and rotation by the nodes parent inverse world matrix to get local rot & scl
			invParent = getGlobalTransform(node, "parentInverseMatrix")
			tfm = om.MTransformationMatrix(srcTfm.asMatrix() * invParent.asMatrix())

		# rotation
		rot = tfm.rotation()

		# scale
		tfm.getScale(scl, space)

		# Set Transforms----------------------------
		fn.setObject(node)
		
		# set Scaling
		if scale:
			fn.setScale(scl)
		# set Rotation
		if rotate:
			fn.setRotation(rot)
		# set Translation
		if translate:
			if matchPivot:
				nodePivot = fn.scalePivot(space)
				pos += srcPivot - nodePivot
			fn.setTranslation(pos, space)
