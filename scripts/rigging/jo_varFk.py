######## Variable FK Autorigger ########
#	Version 1.00
# 	Version: 15.02.2014
# 	Author: Julian "fleity" Oberbeck
#	Download at and submit bugs to: http://www.creativecrash.com/maya/downloads/scripts-plugins/character/c/variable-fk-rigger
#  
#	Variable FK concept based on the video of Jeff Brodsky (https://vimeo.com/72424469).
#	thanks at adeptus from cgsociety.com/forum for a tip on how to orient joint chains
#
############## How To Use ##############
#
#	put varFk.py into scripts directory, varFk.jpg into documents\maya\<maya version>\prefs\icons
#
#	run from python command line / script editor:
#	import jo_varFk
#	reload(jo_varFk)
# 	jo_varFk.UI()
#
#	The script uses a curve to generate joints at curve's CVs/EPs, Lofts a surface from this curve on which the controls are positioned. 
#	The influence of each control is determined by it's distance to each joint on this surface.
#	Curve Tool buttons can be used like shelf buttons.
#
#	1. Insert the name of the input curve into the first input field (or press the button beside it to insert the currently selected object).
#	2. Enter a name for the rig in the second input field. Invalid characters will be removed, already existing object names will be incremented.
#	3. Choose number of controls to generate, minimum is 1, maximum is 999.
#	4. Press "Build" button.
#
#	Tip: You can select all skinning joints by selecting " bn_<rigname>* "
#
########################################

import pymel.core as pm

def UI():
	
	# kill window if it already exists
	if pm.window('varFkUI', exists = True):
		pm.deleteUI('varFkUI')
	
	# build window
	varFkWindow = pm.window('varFkUI', title = 'Variable Fk Rigger', widthHeight=(365.0, 340.0), sizeable=False, minimizeButton=True, maximizeButton=False)
	
	# create tabLayout
	tabs = pm.tabLayout(imw = 5, imh = 5)
	
	# create tabs
	form = pm.formLayout(numberOfDivisions=100, w = 365, h = 340, parent = tabs)
	pm.tabLayout(tabs, edit = True, tabLabel = (form, 'VarFk Rigger'))
	info = pm.formLayout(numberOfDivisions=100, w = 365, h = 340, parent = tabs)
	pm.tabLayout(tabs, edit = True, tabLabel = (info, 'Help'))
	
	# fill info tab
	pm.setParent ( info )
	
	# Creating Element scrollField_info
	infotext = 'Variable FK Autorigger \nVersion: 1.00 \nby Julian "fleity" Oberbeck. \n\nBasic variable FK concept by Jeff Brodsky (https://vimeo.com/72424469). \n\n\nVariable FK Rigs allow moving a FK-control along a joint chain, their influence being based on the distance to the joints. \n\n How to use: \n 1. Insert the name of the input curve. \n 2. Enter a name for the rig. \n 3. Choose number of controls. \n 4. Press "Build."'

	# Creating Element scrollField_infotext
	scrollField_infotext = pm.scrollField ( text = infotext, w = 340, h = 295, editable = False, wordWrap = True )
	pm.formLayout( info, edit=True, attachForm=[( scrollField_infotext, 'top', 10), ( scrollField_infotext, 'left', 10)] )

	# fill main utility tab
	pm.setParent( form )
	
	# Creating Element img_banner
	imagePath = pm.internalVar(upd = True) + '/icons/varFk.png'
	img_banner = pm.image( w = 365, h = 110, image = imagePath )
	pm.formLayout( form, edit=True, attachForm=[( img_banner, 'top', 0), ( img_banner, 'left', -5)] )
	# =========================================
	# Creating Element layout_curve_tools
	shelfLayout_curveTools = pm.shelfTabLayout( 'shelfCurves', w = 225, h = 50, tabsVisible = False )
	pm.setParent( shelfLayout_curveTools )
	pm.formLayout( form, edit=True, attachForm=[( shelfLayout_curveTools, 'top', 97), ( shelfLayout_curveTools, 'left', 70)] )
	rowLayout_curveTools = pm.rowLayout( 'rowLayout_curveTools', w = 200, h = 45, numberOfColumns = 4, cw4 = [40,40,40,40], ct4 = ['left', 'left', 'left', 'left'], co4 = [10,10,10,10] )
	pm.setParent( rowLayout_curveTools )
	# =========================================
	# Creating Elements curve tool buttons
	button_CVCurveTool = pm.iconTextButton( 'button_CVCurveTool', w = 40, h = 40, mw = 2, mh = 2, image = 'curveCV.png', command = pm.Callback(pm.runtime.CVCurveTool, ), doubleClickCommand = pm.Callback(pm.runtime.CVCurveToolOptions, ) )
	button_EPCurveTool = pm.iconTextButton( 'button_EPCurveTool', w = 40, h = 40, mw = 2, mh = 2, image = 'curveEP.png', command = pm.Callback(pm.runtime.EPCurveTool, ), doubleClickCommand = pm.Callback(pm.runtime.EPCurveToolOptions, ) )
	button_PencilCurveTool = pm.iconTextButton( 'button_PencilCurveTool', w = 40, h = 40, mw = 2, mh = 2, image = 'pencil.png', command = pm.Callback(pm.runtime.PencilCurveTool, ), doubleClickCommand = pm.Callback(pm.runtime.PencilCurveToolOptions, ) )
	button_BezierCurveTool = pm.iconTextButton( 'button_BezierCurveTool', w = 40, h = 40, mw = 2, mh = 2, image = 'curveBezier.png', command = pm.Callback(pm.runtime.CreateBezierCurveTool, ), doubleClickCommand = pm.Callback(pm.runtime.CreateBezierCurveToolOptions, ) )
	# =========================================
	pm.setParent( form )
	# =========================================
	# Creating Element button_insertSelectedCurve
	button_insertSelectedCurve = pm.button( label='>', w=35, h=25, command=pm.Callback(insertFirstSelected, ) )
	pm.formLayout( form, edit=True, attachForm=[( button_insertSelectedCurve, 'top', 155), ( button_insertSelectedCurve, 'left', 55)] )
	# =========================================	
	# Creating Element input_inputCurve
	input_inputCurve = pm.textField('input_inputCurve', text='Draw a curve, 1 Joint per CV.', w=250, h=25)
	pm.formLayout( form, edit=True, attachForm=[( input_inputCurve, 'top', 155), ( input_inputCurve, 'left', 100)] )
	# =========================================
	# Creating Element text_IdName
	text_IdName = pm.text( label='Prefix Name:', align='right', recomputeSize=True, w=80, h=25)
	pm.formLayout( form, edit=True, attachForm=[( text_IdName, 'top', 190), ( text_IdName, 'left', 10)] )
	# =========================================
	# Creating Element input_IdName
	input_IdName = pm.textField('input_IdName', text='varFk', w=250, h=25)
	pm.formLayout( form, edit=True, attachForm=[( input_IdName, 'top', 190), ( input_IdName, 'left', 100)] )	
	# =========================================	
	# Creating Element text_numOfCtrls
	text_numOfCtrls = pm.text( label='# of Controls:', align='right', recomputeSize=True, w=80, h=25)
	pm.formLayout( form, edit=True, attachForm=[( text_numOfCtrls, 'top', 225), ( text_numOfCtrls, 'left', 10)] )
	# =========================================
	# Creating Element slider_numOfCtrls
	slider_numOfCtrls = pm.intSliderGrp('slider_numOfCtrls', f=True, min=1, max=10, fieldMinValue=1,fieldMaxValue=999, value=3, ann='Number of Controls', w=255, h=25)
	pm.formLayout( form, edit=True, attachForm=[( slider_numOfCtrls, 'top', 225), ( slider_numOfCtrls, 'left', 100)] )
	# =========================================
	# Creating Element button_build
	button_build = pm.button( label='Build', w=340, h=40, command = pm.Callback(buildVarFkFromUI, ))
	pm.formLayout( form, edit=True, attachForm=[( button_build, 'top', 265), ( button_build, 'left', 10)] )
	# =========================================
	
	pm.setParent( '..' )	

	# show window
	varFkWindow.show()


# UI functions	
def insertFirstSelected( *args ):
	sel = pm.selected()
	if len(sel) > 0:
		pm.textField('input_inputCurve', edit = True, text = sel[0])
	else: 
		pm.textField('input_inputCurve', edit = True, text = 'Draw a curve, 1 Joint per CV.')
		pm.warning('Nothing is selected.')


def buildVarFkFromUI( *args ):
	
	# get inputs from UI
	inputCurve = pm.textField('input_inputCurve', query = True, text = True)
	IdName = pm.textField('input_IdName', query = True, text = True)
	numberOfCtrls = pm.intSliderGrp('slider_numOfCtrls', query = True, value = True)
	
	# check if input string is empty, default string or not existent
	if (inputCurve == '' or inputCurve == 'Draw a curve, 1 Joint per CV.'):
		pm.warning('You have to enter a curve. Select it and press the ">" button.')
		return
	
	# get input string's object
	pm.select(inputCurve)
	inputCurve = pm.selected()
	
	# check if input object exists
	if (pm.objExists(inputCurve[0]) != True):
		pm.warning(str(inputCurve) + ' does not exist. You have to enter a curve. Select it and press the ">" button.')
		return
	
	# continue if input is a transform with a nurbs curve shape, abort if not.
	if pm.nodeType(inputCurve[0]) == 'transform':
		if pm.nodeType(pm.listRelatives(inputCurve, shapes=True)[0]) == 'nurbsCurve':
			print('Curve is valid. Continuing...')
		else: 
			pm.warning('Selected Transform is invalid. Please select Curve.')
			return
	else: 
		pm.warning('Selected Object is invalid. Please select Curve (Transform).')
		return
	
	# workaround to get rid of unwanted characters by using maya's build in char check
	pm.select(clear = True)
	IdName = str( pm.group( name = IdName, empty = True ) )
	if (IdName[0] == "|"): IdName = IdName.rsplit("|")[1]
	pm.delete()
	
	# check if rig with that IdName already exists and increment
	while pm.objExists(IdName):
		pm.warning('An object with the name \"' + IdName + '"\ already exists.')
		# get index from string
		indexList = []
		for c in IdName[::-1]:
			if c.isdigit():
				indexList.append(c)
			else:
				break
		
		indexList.reverse()
		index = int("".join(indexList))
		
		# remove index from IdName
		IdName = IdName[0:-int(len(str(index)))]
		
		# add new index to IdName
		index += 1
		IdName = IdName + str(index)
		pm.warning('New name is \"' + IdName + '"\.')
		
	buildVarFk(IdName, inputCurve, numberOfCtrls)
	return


# Utility functions
def create_jointChain( IdName = 'joint', inputCurve = pm.selected(), orientation = 'xyz' ):
	
	# get number of CVs on InputCurve
	numberOfCvs = pm.getAttr( inputCurve[0] + '.cp',s=1 )
	
	# create joints on world space cv locations
	Jnts = []
	for i in range(0, numberOfCvs):
		pm.select( clear = True )
		currentCvPos = pm.pointPosition( inputCurve[0].cv[i], w=1 )
		Jnt = pm.joint( name = '_'.join( ['bn', IdName, str( i+1 )] ) )
		pm.xform( Jnt, t = currentCvPos )
		Jnts.append( Jnt )
		
	# create end joint
	pm.select( clear = True )
	endJntPos = 0.1 * ( pm.getAttr( Jnts[len(Jnts)-1].translate ) - pm.getAttr( Jnts[len(Jnts)-2].translate ) ) + pm.getAttr( Jnts[len(Jnts)-1].translate )
	endJnt = pm.joint( name = 'be_' + IdName, position = endJntPos, a = True )
	Jnts.append( endJnt )
	
	# set aim and orientation vectors, always yup
	aimDict = {}
	aimDict[orientation[0]] = 1
	aimDict[orientation[1]] = 0
	aimDict[orientation[2]] = 0
	aimVec = ( aimDict['x'], aimDict['y'], aimDict['z'] )

	orientDict = {}
	orientDict[orientation[0]] = 0
	orientDict[orientation[1]] = 0
	orientDict[orientation[2]] = 1
	orientVec = ( orientDict['x'], orientDict['y'], orientDict['z'] )
	
	# orient first joint
	JntAimConstrain = pm.aimConstraint( Jnts[1], Jnts[0], aimVector = aimVec, upVector = (0,1,0), worldUpType = "scene" )
	pm.delete( JntAimConstrain )
	Jnts[0].jointOrient.set( Jnts[0].rotate.get() )
	Jnts[0].rotate.set( 0,0,0 )
	
	# orient middle joints
	for i in range( 1, len( Jnts ) - 1 ):
		JntAimConstrain = pm.aimConstraint( Jnts[i+1], Jnts[i], aimVector = aimVec, upVector = orientVec, worldUpType = "objectrotation", worldUpVector = orientVec, worldUpObject = Jnts[i-1] )
		pm.delete( JntAimConstrain )
		Jnts[i].jointOrient.set( Jnts[i].rotate.get() )
		Jnts[i].rotate.set( 0,0,0 )
	
	# orient last joint
	Jnts[len( Jnts ) -1 ].jointOrient.set( Jnts[len( Jnts ) -2 ].jointOrient.get() )
	
	# parent joints
	for i in range( 1, len( Jnts ) ):
		pm.parent( Jnts[i], Jnts[i-1], absolute = True)

	pm.select( Jnts[0] )
	print('Successfully created and oriented joint-chain. Continuing...')
	return Jnts


def addPositionOnSurfaceAttr( objects, nurbsSurface ):
	# connect nurbsSurface to closestPointOnSurface node
	ObjPosOnSurface = pm.shadingNode( 'closestPointOnSurface', asUtility = True )
	nurbsSurface[0].getShape().worldSpace[0] >> ObjPosOnSurface.inputSurface

	# get parametric position of last joint to calculate relative position 
	ObjPosOnSurface.inPosition.set( pm.xform( objects[-1], q = True, t = True, ws = True ) )
	lastObjPos = ObjPosOnSurface.parameterU.get()

	# add custom attribute and set relative parametric position
	for each in objects:
		pm.addAttr( each, longName = 'jointPosition', attributeType = 'float', keyable = True )
		pm.setAttr( ObjPosOnSurface + '.inPosition', pm.xform( each, q = True, t = True, ws = True ) )
		relObjectPosition = ObjPosOnSurface.parameterU.get() / lastObjPos
		each.jointPosition.set(relObjectPosition, lock = True)

	pm.delete( ObjPosOnSurface )
	print('Added parametric position on surface attribute to all objects.')
	return

	
def create_guideSurface( IdName, listOfJnts ):
	loftCurves = []
	for i in range(2):
		# duplicate and select hierarchy of joints
		listOfOffsetJnts = pm.duplicate( listOfJnts, name = 'b_' + IdName +'_offset1', parentOnly = True )
		
		# offset each joint on it's own z-axis
		for jnt in listOfOffsetJnts:
			if i == 0: pm.move(jnt, (0,0,-0.5), relative = True, objectSpace = True, preserveChildPosition = True)
			if i == 1: pm.move(jnt, (0,0,0.5), relative = True, objectSpace = True, preserveChildPosition = True)
		
		# draw loftcurves
		loftCurvePoints = []
		for each in listOfOffsetJnts:
			jntPosition = pm.xform(each, q = True, t = True, ws = True)
			loftCurvePoints.append(jntPosition)
		
		loftCurves.append( pm.curve( name = IdName + '_loftCurve' + str(i), degree = 1, point = loftCurvePoints ) ) 
		pm.delete(listOfOffsetJnts)

	# loft guideSurface
	guideSurface = pm.loft( loftCurves[0], loftCurves[1], name = IdName + '_guide_surface', ar=True, rsn=True, d=3, ss=1, object=True, ch=False, polygon=0 )
	guideSurface = pm.rebuildSurface( guideSurface ,ch=1, rpo=1, rt=0, end=1, kr=1, kcp=0, kc=0, su=0, du=3, sv=1, dv=3, tol=0.01, fr=0, dir=2 )
		
	# cleanup
	pm.delete( loftCurves )
	guideSurface[0].inheritsTransform.set(False)
	guideSurface[0].overrideEnabled.set(True)
	guideSurface[0].overrideDisplayType.set(1)
	# guideSurface[0].visibility.set(False)
	
	print('Successfully lofted guide surface. Continuing...')
	return guideSurface


def create_VarFkCtrls( IdName, guideSurface, numberOfCtrls ):
	# create controls
	ctrlGrp = pm.group( name = IdName + '_ctrls', empty = True, world = True)
	ctrlGrp.inheritsTransform.set(0)
	
	listOfCtrls = []
	
	for currentCtrlIndex in range(numberOfCtrls):
		if numberOfCtrls > 1:
			FolliclePos = ( 1.0 / (numberOfCtrls-1) ) * currentCtrlIndex
		else: 
			FolliclePos = ( 1.0 / (numberOfCtrls) ) * currentCtrlIndex
		
		# create controlshape
		currentCtrl = pm.circle( name = ( 'ctrl_vFK' + str( currentCtrlIndex+1 )+ '_' + IdName ), c=(0,0,0), nr=(1,0,0), sw=360, r=1.5, d=3, ut=0, tol=0.01, s=8, ch=False)
		currentCtrl[0].overrideEnabled.set(True)
		currentCtrl[0].overrideColor.set(4)
		# lock'n hide translates + scaleX
		currentCtrl[0].translateX.set( lock = True, keyable = False, channelBox = False )
		currentCtrl[0].translateY.set( lock = True, keyable = False, channelBox = False )
		currentCtrl[0].translateZ.set( lock = True, keyable = False, channelBox = False )
		currentCtrl[0].scaleX.set( lock = True )
		# add strength, position, radius attributes
		pm.addAttr( longName='rotateStrength', attributeType='float', keyable=True, defaultValue=1 )
		pm.addAttr( longName='position', attributeType='float', keyable=True, min=0-FolliclePos, max=1-FolliclePos )
		pm.addAttr( longName='radius', attributeType='float', keyable=True, min=0.0001, defaultValue=0.3 )
		
		# position min/max relative to defaultposition so ctrl can be zeroed out. Is remapped later back to 0 to 1 when connected to Follicle
		currentFollicle = create_follicle( guideSurface[0], uPos=FolliclePos, vPos=0.5 )
		currentFollicle.simulationMethod.set(0)
		currentFollicle.collide.set(0)
		currentFollicle.flipDirection.set( True )
		currentFollicle = pm.listRelatives( currentFollicle, parent=True )
		
		# connect to strength multiplier
		rotateStrengthMultiplier = pm.shadingNode( 'multiplyDivide', asUtility = True, n = str( currentCtrl[0] ) + '_strength_mult' )
		currentCtrl[0].rotate >> rotateStrengthMultiplier.input1
		pm.connectAttr( currentCtrl[0] + '.rotateStrength', rotateStrengthMultiplier + '.input2X', f=1 )
		pm.connectAttr( currentCtrl[0] + '.rotateStrength', rotateStrengthMultiplier + '.input2Y', f=1 )
		pm.connectAttr( currentCtrl[0] + '.rotateStrength', rotateStrengthMultiplier + '.input2Z', f=1 )
		
		# compensate position zero value by current follicle position
		jntposZeroCompensate = pm.shadingNode( 'plusMinusAverage', asUtility = True, n=currentCtrl[0] + '_jntposZeroCompensate' )
		pm.setAttr( jntposZeroCompensate + '.input1D[0]', pm.getAttr( currentFollicle[0].getShape() + '.parameterU' ) )
		pm.connectAttr( currentCtrl[0] + '.position', jntposZeroCompensate + '.input1D[1]', f=1 )
		pm.connectAttr( jntposZeroCompensate + '.output1D', currentFollicle[0].getShape() + '.parameterU', f=1 )

		# grouping
		buf = createBufGrp( currentCtrl )[0]
		pm.parent( buf, ctrlGrp, relative = True )
		pm.parent( currentFollicle, ctrlGrp )
		
		# connect follicle position to control buffer
		currentFollicle[0].translate >> buf.translate

		listOfCtrls.append( currentCtrl[0] )
		pm.select( clear = 1 )
		print( 'Successfully created ' + currentCtrl[0] )
	return listOfCtrls


def createBufGrp( sel ):
	Bufs = []
	if sel:
		for node in sel:
			targetParent = pm.listRelatives( node, p = True )
			BufObj = pm.group( em = 1 )
			BufObj = pm.rename( BufObj, node + 'Buf')
			if targetParent != []:
				pm.parent( BufObj, targetParent )
			srcPos = pm.xform( node, q = True, t = True, ws = True )
			srcRot = pm.xform( node, q = True, ro = True, ws = True )
			pm.xform( BufObj, t = srcPos, ro = srcRot )
			pm.parent( node, BufObj )
			Bufs.append( BufObj )
		pm.select( Bufs )
		return Bufs
	else: pm.warning( 'Input is empty. Nothing to create Buffer-groups for.' )


# create hair follicle only code by Chris Lesage
# http://chrislesage.com/character-rigging/manually-create-maya-follicle-in-python/
def create_follicle(oNurbs, uPos=0.0, vPos=0.0):
	# manually place and connect a follicle onto a nurbs surface.
	if oNurbs.type() == 'transform':
		oNurbs = oNurbs.getShape()
	elif oNurbs.type() == 'nurbsSurface':
		pass
	else:
		'Warning: Input must be a nurbs surface.'
		return False
	
	# create a name with frame padding
	pName = '_'.join((oNurbs.name(),'follicle','# '.zfill(2)))
	
	oFoll = pm.createNode('follicle', name=pName)
	oNurbs.local.connect(oFoll.inputSurface)
	# if using a polygon mesh, use this line instead.
	# (The polygons will need to have UVs in order to work.)
	# oMesh.outMesh.connect(oFoll.inMesh)

	oNurbs.worldMatrix[0].connect(oFoll.inputWorldMatrix)
	oFoll.outRotate.connect(oFoll.getParent().rotate)
	oFoll.outTranslate.connect(oFoll.getParent().translate)
	oFoll.parameterU.set(uPos)
	oFoll.parameterV.set(vPos)
	oFoll.getParent().t.lock()
	oFoll.getParent().r.lock()

	return oFoll


def create_ctrlOutput( ctrl,jnt ):
	# create nodes and set initial values
	prefix = 'util_' + jnt + '__' + ctrl + '_'
	jntposMinusCtrlpos = pm.shadingNode('plusMinusAverage', asUtility = True, n=prefix + 'jntpos-Ctrlpos')
	jntposMinusCtrlpos.setAttr('operation', 2)
	absPower = pm.shadingNode('multiplyDivide', asUtility = True, n=prefix + 'absPower')
	absPower.setAttr('input2', 2,2,2, type='double3')
	absPower.setAttr('operation', 3)
	absSqrt = pm.shadingNode('multiplyDivide', asUtility = True, n=prefix + 'absSqrt')
	absSqrt.setAttr('input2', .5,.5,.5, type='double3')
	absSqrt.setAttr('operation', 3)
	remapDist = pm.shadingNode('remapValue', asUtility = True, n=prefix + 'remapDist')
	rotateMultiplier = pm.shadingNode('multiplyDivide', asUtility = True, n = prefix + 'infl_mult')
	
	# get existing offset nodes which were created in controller function
	jntposZeroCompensate = pm.listConnections( ctrl, exactType = True, type = 'plusMinusAverage' )[0]
	rotateStrengthMultiplier = pm.listConnections( ctrl, exactType = True, type = 'multiplyDivide' )[0]
	
	# jntpos - ctrlpos
	pm.connectAttr(jnt + '.jointPosition', jntposMinusCtrlpos + '.input1D[0]', f=1)
	pm.connectAttr(jntposZeroCompensate + '.output1D', jntposMinusCtrlpos + '.input1D[1]', f=1)
	
	# abs
	pm.connectAttr(jntposMinusCtrlpos + '.output1D', absPower + '.input1X', f=1)
	pm.connectAttr(absPower + '.outputX', absSqrt + '.input1X', f=1)
	
	# rotate remap: distance 0 to 1 | falloff distance to 0
	pm.connectAttr(absSqrt + '.outputX', remapDist + '.inputValue', f=1)
	pm.connectAttr(ctrl + '.radius', remapDist + '.value[1].value_Position', f=1)
	remapDist.setAttr('value[0].value_Position', 0)
	remapDist.setAttr('value[0].value_FloatValue', 1)
	remapDist.setAttr('value[1].value_FloatValue', 0)
	remapDist.setAttr('value[0].value_Interp', 2)
	
	# connect strength multiplier to rotate multiplier
	rotateStrengthMultiplier.output >> rotateMultiplier.input1
	pm.connectAttr(remapDist + '.outValue', rotateMultiplier + '.input2X', f=1)
	pm.connectAttr(remapDist + '.outValue', rotateMultiplier + '.input2Y', f=1)
	pm.connectAttr(remapDist + '.outValue', rotateMultiplier + '.input2Z', f=1)
	
	# print('Created ' + ctrl + '--' + jnt + ' output.')
	return rotateMultiplier


def buildVarFk( IdName, inputCurve, numberOfCtrls ):
	# main work calls
	# create joints on curve
	listOfJnts = create_jointChain( IdName, inputCurve )
	listOfJnts.pop() # pop endjoint
	pm.select( clear = True )
	
	# loft nurbs surface
	guideSurface = create_guideSurface( IdName, listOfJnts )
	
	# skinbind nurbs surface to jointchain
	pm.skinCluster( guideSurface, listOfJnts, tsb=True, skinMethod = 0, maximumInfluences = 1, dropoffRate = 10.0 )
	
	# add parametric attributes to joints
	addPositionOnSurfaceAttr( listOfJnts, guideSurface )
	
	# create controls
	listOfCtrls = create_VarFkCtrls( IdName, guideSurface, numberOfCtrls )
	
	# cleanup grouping
	# create main control
	mainCtrl = pm.curve( name=IdName, d = 1, p = [(-1,1,1),(1,1,1),(1,1,-1),(-1,1,-1),(-1,1,1),(-1,-1,1),(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1),(1,-1,1),(1,1,1),(1,1,-1),(1,-1,-1),(-1,-1,-1),(-1,1,-1)])
	mainCtrl.getShape().overrideEnabled.set(True)
	mainCtrl.getShape().overrideColor.set(17)

	# create joint group
	listJnt1 = [listOfJnts[0]] # because createBufGrp expects a list
	jntGrp = createBufGrp(listJnt1)[0]
	jntGrp.rename(IdName + '_joints')
	
	# snap main control pivot to joint group pivot and parent joint group
	jntGrpPos = pm.xform(jntGrp, q = True, t = True, ws = True)
	jntGrpRot = pm.xform(jntGrp, q = True, ro = True, ws = True)
	pm.xform(mainCtrl, t = jntGrpPos, ro = jntGrpRot)
	pm.parent(jntGrp, mainCtrl)
	
	# parent control group
	ctrlGrp = listOfCtrls[0].getParent(2)
	pm.parent(ctrlGrp, mainCtrl, r = True)
	pm.xform(ctrlGrp, piv = jntGrpPos)
	
	# scale constrain world locator to main-ctrl as a reference point for scaling, feed into follicle. only for cosmetic reasons
	offsetLoc = pm.spaceLocator( n = IdName + '_ctrl_offsetLoc')
	offsetLoc.inheritsTransform.set(0)
	offsetLoc.visibility.set(0)
	pm.parentConstraint( mainCtrl, offsetLoc, maintainOffset = False)
	pm.scaleConstraint( mainCtrl, offsetLoc, maintainOffset = False)
	for obj in ctrlGrp.getChildren(): 
		if pm.nodeType(obj.getChildren()[0]) != 'follicle':
			offsetLoc.rotate >> obj.rotate
			offsetLoc.scale >> obj.scale
	pm.parent(offsetLoc, ctrlGrp, r = True)
	
	inputCurve[0].visibility.set(False)
	pm.parent(inputCurve, mainCtrl)
	pm.parent(guideSurface, mainCtrl)
	print('Cleanup complete. Connecting Controls...')
	
	# generating ctrl output nodes and connecting to joints
	for jnt in listOfJnts:
		# reset list of outputs, important! otherwise every joints gets connected to all control-outputs for the previous joint(s) before too.
		rotateMultipliers = []
		
		# create a layered texture node and strength multiplier for every joint to multiply all scale values
		scaleMultiplier = pm.shadingNode( 'layeredTexture', asUtility = True, n = 'util_' + jnt + '_scaleInput' )
		
		i = 0
		for ctrl in listOfCtrls:
			
			rotateMultiplier = create_ctrlOutput(ctrl, jnt)
			rotateMultipliers.append( rotateMultiplier )

			# connect ctrl scale to scale multiplier
			pm.connectAttr( ctrl + '.scale', scaleMultiplier + '.inputs[' + str(i) + '].color' )
			pm.setAttr( scaleMultiplier + '.inputs[' + str(i) + '].blendMode', 6 )
			
			# get remapDistance outValue and connect to scale multiplier input[i] alpha
			remapDist = pm.listConnections( rotateMultiplier , type = 'remapValue' )[0]
			pm.connectAttr( remapDist + '.outValue', scaleMultiplier + '.inputs[' + str(i) + '].alpha' )
			
			i += 1
			
		# sum up rotate outputs of all controls and connect to joints
		# connect to sum +-avg node
		sum = pm.shadingNode( 'plusMinusAverage', asUtility = True, n = 'util_' + jnt + '_sum_rotate' )	
		for i in range( len(rotateMultipliers ) ):
			rotateMultipliers[i].output >> sum.input3D[i]
		pm.connectAttr( sum + '.output3D', jnt + '.rotate' )
		

		# set last input to base value of 1, OOP methods does not work on sub attributes of layeredTexture
		i += 1
		pm.setAttr( scaleMultiplier + '.inputs[' + str(i) + '].color', (1,1,1) )
		pm.setAttr( scaleMultiplier + '.inputs[' + str(i) + '].alpha', 1)
		pm.setAttr( scaleMultiplier + '.inputs[' + str(i) + '].blendMode', 0 )
		
		
		# connect scale multiplier to joint scale YZ
		scaleMultiplier.outColor >> jnt.scale		
		
		print('Successfully connected all control output to joint: ' + jnt + '.')

		
	# create buffer group for main control, buffer-function expects list
	pm.select(mainCtrl)
	createBufGrp(pm.selected())
	
	print('Successfully created variable FK rig.'),
	pm.select(clear=True)
	return
	
	
