#     import abzTweenMachine
#     abzTweenMachine.abzTweenMachineWindow()
#     reload(abzTweenMachine)


#--------------start
import maya.cmds as maya
import maya.mel as mel
import math
import sys
maya.displayRGBColor('timeSliderBreakdown', 0, 0.70, 0.70)

#--------------procedura create window --------------------------------------------------------------------------------------------------------------------------
def abzTweenMachineWindow():

	global aTMactionTime
	global aTMtweenMachineCollect
	global aTMlastSelected
	global aTMmaxValArray
	
	aTMsettingStatus = 0
	aTMtweenStatus = 1
	aTMgroupsStatus = 0
	aTMghostsStatus = 0
	aTMkeyToolsStatus = 0
	aTMstatus = "OK!!!"
	aTMbgcOK = [0.332,0.885,0.683]
	aTMactionTime = -0.356
	aTMtweenMachineCollect = 1
	aTMlastSelected = []
	aTMmaxValArray = []
	mVersion = mel.eval( "getApplicationVersionAsFloat" )
	if int(mVersion) <= 2010:
		stepButtonDistance = [60,162,27,200]
	else:
		stepButtonDistance = [47,173,27,200]

	if maya.window('abzTweenMachineWindow',ex=1):
		maya.deleteUI('abzTweenMachineWindow',wnd=1)
	window = maya.window('abzTweenMachineWindow',t="Advanced Tween Machine LITE",s=1,mb=1)
	maya.menu( l='Settings',to=0,ni=0,pmc=__name__+".doChangeaTMWindowGrp(\"aTMsettingsLayout\")")
	maya.menu( l='Tween Machine',ni=0,to=0,pmc=__name__+".doChangeaTMWindowGrp(\"aTMtweenMachineLayout\")")
	maya.menu( l='Groups',to=0,en=0,pmc=__name__+".doChangeaTMWindowGrp(\"aTMgroupsLayout\")")
	maya.menu( l='Ghosts',to=0,en=1,pmc=__name__+".doChangeaTMWindowGrp(\"aTMghostsLayout\")")
#	maya.menu( l='Key tools',to=0,en=1,pmc=__name__+".doChangeaTMWindowGrp(\"aTMkeyToolsLayout\")")
	maya.menu( l='Fix',to=0,pmc=__name__+".doFixTMscript()")
	maya.menu( l='About',to=0,hm=1,pmc=__name__+".doShowAbout()")
	maya.columnLayout('aTMframeLayoutParent',rs=0,adj=1)
	maya.rowLayout("aTMstatusRowlayout",nc=2, cw2=(60,351),cl2=["right","left"],bgc=aTMbgcOK)
	maya.text('aTMstatusInfo',l="Status :",al="right",bgc=aTMbgcOK)
	maya.text('aTMSTATUS',l=aTMstatus,al="left",bgc=aTMbgcOK)
	maya.setParent( '..' )
	maya.frameLayout('aTMsettingsLayout',l="Settings",bs="etchedOut",w=411,cll=1,cl=-aTMsettingStatus+1,vis=aTMsettingStatus,p='aTMframeLayoutParent')
	maya.columnLayout(rs=3,adj=0)
	maya.rowLayout(nc=2, cw2=(60,351))
	maya.text( l='' )
	maya.radioButtonGrp('aTMworkModeRadiobutton',cl2=["left","left"],l='Working mode',la2=['fast (in buffer)','slow (on curves)'],cw3=[100,90,100],nrb=2,en=1,sl=1,cl3=["left","left","left"])
	maya.setParent( '..' )
	maya.rowLayout(nc=2, cw2=(60,351))
	maya.text( l='' )
	maya.radioButtonGrp('aTMmayaLinkRadiobutton',cl2=["left","left"],l='Link with maya',la2=['yes','no'],cw3=[100,90,90],nrb=2,en=1,sl=2,cl3=["left","left","left"],on1=__name__+".doSetLinkWithMaya(1)",on2=__name__+".doSetLinkWithMaya(0)" )
	maya.setParent( '..' )
	maya.rowLayout(nc=2, cw2=(60,351))
	maya.text( l='' )
	maya.radioButtonGrp('aTMtweenBetweenRadiobutton',cl2=["left","left"],l='Tween between',la2=['poses','keys'],cw3=[100,90,90],nrb=2,en=1,sl=1,cl3=["left","left","left"],cc=__name__+".doSetaTMactionTime()" )
	maya.setParent( '..' )
	maya.rowLayout(nc=2, cw2=(60,351))
	maya.text( l='' )
	maya.radioButtonGrp('aTMkeyTangentRadiobutton',cl3=["left","left","left"],l='Key tangent',la3=['auto', 'step', 'linear'],cw4=[100,90,90,80],nrb=3,en=1,sl=1,cl4=["left","left","left","left"],cc=__name__+".doSetaTMactionTime()" )
	maya.setParent( '..' )
	maya.rowLayout(nc=2, cw2=(60,351))
	maya.text( l='' )
	maya.radioButtonGrp('aTMkeyTypeRadiobutton',cl2=["left","left"],l='Key type',la2=['pose', 'breakdown'],cw3=[100,90,90],nrb=2,en=1,sl=1,cl3=["left","left","left"] )
	maya.setParent( '..' )
	maya.rowLayout(nc=3, cw3=(60,280,71),en=1)
	maya.text( l='' )
	maya.checkBoxGrp('aTMpredictArcCheckBox',cl2=["left","left"],ncb=2, l='Predict', la2=[ 'arc', 'overlap'],va2 = [0,0],en=1,cw3=[100,90,90],cl3=["left","left","left"])
	maya.floatFieldGrp('aTMpredictVarCheckBox',nf=1,el='lag',v1=0.2,pre=2,cw2=[30,41],cl2=["left","left"] )
	maya.setParent( '..' )
	maya.frameLayout('aTMtweenMachineLayout',l="Tween Machine",bs="etchedOut",w=411,cll=0,cl=-aTMtweenStatus+1,vis=aTMtweenStatus,p='aTMframeLayoutParent')
	maya.columnLayout(rs=3,adj=0)
	maya.rowLayout( nc=4, cw4=(60,175,176,27),cl4=["center","right","left","center"])
	maya.text( l='' )
	maya.text( l='\\',w=175)
	maya.text( l='/' )
	maya.text( l='' )
	maya.setParent( '..' )
	maya.floatSliderGrp('aTMmainFloatSliderGrp',el='',f=1,min=-50.0,max=150.0,fmn=-50.0,fmx=150.0,v=50,cw3=[60,351,1],cc=__name__+".doSetTweenKey(\"sliderEnd\",0)",dc=__name__+".doSetTweenKey(\"sliderDrag\",0)")	
	maya.floatSliderGrp('aTMmainFloatSliderGrp',e=1,adj=2,cw=[2,351])
	maya.rowLayout( nc=4, cw4=stepButtonDistance,cl4=["left","right","center","left"])
	maya.text( l='' )
	maya.rowLayout( nc=6, cw6=(27,27,27,27,27,27),cl6=["center","center","center","center","center","center"])
	maya.button(l='-50',w=27,c=__name__+".doSetTweenKey(\"button\",-50)")
	maya.button(l='-33',w=27,c=__name__+".doSetTweenKey(\"button\",-33)")
	maya.button(l='-16',w=27,c=__name__+".doSetTweenKey(\"button\",-16)")
	maya.button(l='0',w=27,c=__name__+".doSetTweenKey(\"button\",0)")
	maya.button(l='16',w=27,c=__name__+".doSetTweenKey(\"button\",16)")
	maya.button(l='33',w=27,c=__name__+".doSetTweenKey(\"button\",33)")
	maya.setParent( '..' )
	maya.button(l='50',w=27,c=__name__+".doSetTweenKey(\"button\",50)")
	maya.rowLayout( nc=6, cw6=(27,27,27,27,27,27),cl6=["center","center","center","center","center","center"])
	maya.button(l='67',w=27,c=__name__+".doSetTweenKey(\"button\",67)")
	maya.button(l='84',w=27,c=__name__+".doSetTweenKey(\"button\",84)")
	maya.button(l='100',w=27,c=__name__+".doSetTweenKey(\"button\",100)")
	maya.button(l='116',w=27,c=__name__+".doSetTweenKey(\"button\",116)")
	maya.button(l='133',w=27,c=__name__+".doSetTweenKey(\"button\",133)")
	maya.button(l='150',w=27,c=__name__+".doSetTweenKey(\"button\",150)")
	maya.setParent( '..' )
	maya.setParent( '..' )
	maya.rowLayout( nc=5, cw5=(60,88,87,88,88),cl5=["right","right","right","left","left"])
	maya.text( l='' )
	maya.button('aTMmoveAnim<',l='anim <<<',w=88,c=__name__+".doMoveFrames(\"-1\",\"1\")")	
	maya.button('aTMmovePose<',l='pose <',w=87,c=__name__+".doMoveFrames(\"-1\",\"0\")")
	maya.button('aTMmovePose>',l='> pose',w=88,c=__name__+".doMoveFrames(\"1\",\"0\")")
	maya.button('aTMmovePAnim>',l='>>> anim',w=88,c=__name__+".doMoveFrames(\"1\",\"1\")")
	maya.setParent( '..' )
	maya.rowLayout( nc=5, cw5=(60,88,87,88,88),cl5=["right","right","right","left","left"])
	maya.text( l='' )
	maya.button('aTMkeyPrevPose',l='Key PREV pose',w=88,c=__name__+".doSetTweenKey(\"setPoseKey\",\"prev\")")
	maya.button('aTMkeyLinePose',l='Key linear pose',w=87,c=__name__+".doSetTweenKey(\"setPoseKey\",\"line\")")
	maya.button('aTMkeyFlowPose',l='Key flow pose',w=88,c=__name__+".doSetTweenKey(\"setPoseKey\",\"flow\")")
	maya.button('aTMkeyNextPose',l='Key NEXT pose',w=88,c=__name__+".doSetTweenKey(\"setPoseKey\",\"next\")")
	maya.setParent( '..' )
	maya.rowLayout( nc=3, cw3=(60,176,175),cl3=["right","center","center"])
	maya.text( l='' )
	maya.button('aTMsetKeysAsBreakdown',l='Set keys as breakdown',w=176,c=__name__+".doSetKeyMode(1)")
	maya.button('aTMsetKeysAsPose',l='Set keys as pose',w=175,c=__name__+".doSetKeyMode(0)")
	maya.setParent( '..' )
	maya.frameLayout('aTMGroupsLayout',l="Groups",bs="etchedOut",w=411,cll=1,cl=-aTMgroupsStatus+1,vis=aTMgroupsStatus,p='aTMframeLayoutParent')
	maya.columnLayout(rs=3,adj=0)
	maya.rowLayout()
	maya.checkBoxGrp('aTMdoTweenOn',cl2=["left","left"],ncb=2, l="Tween on", la2=['Selected', 'List'],va2 = [1,0],en=1,cw3=[67,70,70],cl3=["left","left","left"],cc=__name__+".doSetaTMactionTime()")
	maya.setParent( '..' )
	maya.rowLayout()
	maya.radioButtonGrp('aTMorganizeByRadiobutton',cl2=["left","left"],l='Organize by',la2=['Object', 'Channels'],cw3=[67,70,70],nrb=2,en=0,sl=1,cl3=["left","left","left"] )
	maya.setParent( '..' )
	maya.textFieldButtonGrp('aTMinputSetName',text='Type set name...',buttonLabel='Create set',cw2=[158,70] ,co2=[0,50])
	maya.rowLayout( nc=3, cw3=(150,8,50))
	maya.textScrollList('aTMtweenList',h=230,nr=16,ams=1,w=150,a=['one','two','three','four','five','six','seven','eight','nine','ten'],en=0,shi=4,sc="print \"costam\"")
	maya.text( l='' )
	maya.columnLayout()
	maya.button('aTMdeleteSet',l='Delete set',w=73,en=0,c=__name__+".doSetTweenKey(\"button\",180)")
	maya.text( l='' )
	maya.text( l='' )
	maya.button('aTMgoIn>',l='In > ]',w=73,en=0,c=__name__+".doSetTweenKey(\"button\",180)")
	maya.button('aTMgoOut>',l='[ > Out',w=73,en=0,c=__name__+".doSetTweenKey(\"button\",180)")
	maya.text( l='' )
	maya.button('aTMloadFile',l='Load file',w=73,en=0,c=__name__+".doSetTweenKey(\"button\",180)")
	maya.button('aTMloadRigg',l='Load rig',w=73,en=0,c=__name__+".doSetTweenKey(\"button\",180)")
	maya.text( l='' )
	maya.button('aTMsaveFile',l='Save file',w=73,en=0,c=__name__+".doSetTweenKey(\"button\",180)")
	maya.setParent( '..' )
	maya.frameLayout('aTMghostsLayout',l="Ghosts",bs="etchedOut",w=411,cll=1,cl=-aTMghostsStatus+1,vis=aTMghostsStatus,p='aTMframeLayoutParent')
	maya.columnLayout(rs=3,adj=0)
	maya.rowLayout(nc=2, cw2=(60,351))
	maya.intFieldGrp('aTMGhostsInt',nf=2,l='before',el='after',v1=-2,v2=2)
	maya.setParent( '..' )
	maya.rowLayout( nc=3, cw3=(60,160,191),cl3=["right","center","center"],vis=1)
	maya.text( l='' )
	maya.attrColorSliderGrp('aTMbeforeColorSlider',l="",sb=0,cw4=[80,75,1,1])
	maya.attrColorSliderGrp('aTMafterColorSlider',l="",sb=0,cw4=[1,75,1,1])
	maya.setParent( '..' )
	maya.rowLayout( nc=4, cw4=(60,117,117,117),cl4=["right","center","center","center"])
	maya.text( l='' )
	maya.button('aTMGhostsCreate',l='Create ghosts',w=117,c=__name__+".doGhosts(2)")
	maya.button('aTMGhostsDelete',l='Delete ghost',w=117,c=__name__+".doGhosts(1)")
	maya.button('aTMGhostsDeleteAll',l='Delete all ghosts',w=117,c=__name__+".doGhosts(0)")
	maya.setParent( '..' )
	maya.frameLayout('aTMkeyToolsLayout',l="Key tools",bs="etchedOut",w=411,cll=1,cl=-aTMkeyToolsStatus+1,vis=aTMkeyToolsStatus,p='aTMframeLayoutParent')
	maya.columnLayout(rs=3,adj=0)
	maya.rowLayout( nc=3, cw3=(60,176,175),cl3=["right","center","center"],vis=1)
	maya.text( l='' )
	maya.button('aTMsnapKeysToCurrentFrame',l='Snap keys to current frame',w=176,c=__name__+".doSetTweenKey(\"button\",150)")
	maya.button('aTMsnapAllKaysToFrames',l='Snap ALL kays to frames',w=175,c=__name__+".doSetTweenKey(\"button\",150)")
	maya.setParent( '..' )
	maya.rowLayout( nc=3, cw3=(60,176,175),cl3=["right","center","center"],vis=1)
	maya.text( l='' )
	maya.button('aTMconvKeysToStep',l='Convert keys to STEP',w=176,c=__name__+".doSetKeys(\"STEP\")")
	maya.button('aTMconvKaysToSplined',l='Convert keys to splined',w=175,c=__name__+".doSetKeys(\"SPLINE\")")
	maya.setParent( '..' )
	maya.setParent( '..' )
	maya.setParent( '..' )
	maya.text('aTMcopyrgts', l='Advanced Tween Machine by Blaze \"asblaze\" Andrzejewski' ,fn="smallPlainLabelFont")	
	maya.showWindow("abzTweenMachineWindow")
	maya.window('abzTweenMachineWindow',e=1,w=438,h=255)

#--------------procedura doChangeaTMWindowGrp --------------------------------------------------------------------------------------------------------------------------
def doChangeaTMWindowGrp(aTMwindowGrp):
	aTMwindowHeight = maya.window('abzTweenMachineWindow',q=1,h=1)
	if maya.frameLayout(aTMwindowGrp,q=1,vis=1) ==0:
		maya.frameLayout(aTMwindowGrp,e=1,cl=0,vis=1)
		maya.frameLayout(aTMwindowGrp,e=1,cll=0)
		if aTMwindowGrp=="aTMsettingsLayout":
			maya.window('abzTweenMachineWindow',e=1,h=aTMwindowHeight+125)
		if aTMwindowGrp=="aTMtweenMachineLayout":
			maya.window('abzTweenMachineWindow',e=1,h=aTMwindowHeight+190)
		if aTMwindowGrp=="aTMghostsLayout":
			maya.window('abzTweenMachineWindow',e=1,h=aTMwindowHeight+100)
	else:
		maya.frameLayout(aTMwindowGrp,e=1,cll=1)
		maya.frameLayout(aTMwindowGrp,e=1,cl=1,vis=0)
		if aTMwindowGrp=="aTMsettingsLayout":
			maya.window('abzTweenMachineWindow',e=1,h=aTMwindowHeight-125)
		if aTMwindowGrp=="aTMtweenMachineLayout":
			maya.window('abzTweenMachineWindow',e=1,h=aTMwindowHeight-190)
		if aTMwindowGrp=="aTMghostsLayout":
			maya.window('abzTweenMachineWindow',e=1,h=aTMwindowHeight-100)

#--------------procedura doShowAbout --------------------------------------------------------------------------------------------------------------------------
def doShowAbout():
	aTMabout = "Advanced Tween Machine v 0.9.1 LITE \nBased on other similar scripts, but more developed.\n\nContact:\nBlaze \"asblaze\" Andrzejewski\nasblaze3d@gmail.com\n"
	maya.confirmDialog( t='About',ma="center",m=aTMabout,b=['Close'],db='Close')

#--------------procedura doSetaTMactionTime --------------------------------------------------------------------------------------------------------------------------
def doSetaTMactionTime():
	global aTMactionTime
	aTMactionTime = -0.356

#--------------procedura doSetLinkWithMaya --------------------------------------------------------------------------------------------------------------------------
def doSetLinkWithMaya(state):
	if maya.objExists("aTMmayaLinkExpression") :
		maya.delete("aTMmayaLinkExpression")
	if state == 1:
		aTMlinkExpressionTXT ="int $frame = frame;\npython( \"abzTweenMachine.doUpdateWindowSlider(int(\"+$frame+\"))\");"
		aTMlinkExpression = maya.expression(s=aTMlinkExpressionTXT,n="aTMmayaLinkExpression")

#--------------procedura doMoveFrames --------------------------------------------------------------------------------------------------------------------------
def doMoveFrames(direction,whole):
	aTMbgcOK = [0.332,0.885,0.683]
	checkSelectionErrors()
	aTMactionTime = maya.currentTime(q=1)
	if whole == "1":
		aTMendTime = (maya.playbackOptions(q=1,max=1))+20000
	else :
		aTMendTime = aTMactionTime
	maya.keyframe(e=1,iub=1,t=(aTMactionTime,aTMendTime),r=1,o="over",tc=direction)
	maya.currentTime(aTMactionTime+int(direction))
	maya.text('aTMSTATUS',e=1,l="OK!!!",bgc=aTMbgcOK)  #maya
	maya.text('aTMstatusInfo',e=1,bgc=aTMbgcOK)
	maya.rowLayout("aTMstatusRowlayout",e=1,bgc=aTMbgcOK) #maya

#--------------procedura checkSelectionErrors --------------------------------------------------------------------------------------------------------------------------
def checkSelectionErrors():
	if maya.checkBoxGrp('aTMdoTweenOn',q=1,v1=1)==1 or maya.checkBoxGrp('aTMdoTweenOn',q=1,v2=1)==1: #maya
		aTMcurrSelected = maya.ls(sl=1,tr=1) #maya
	else:
		doPrintERROR("Error!!! Check \"Tween on\" option")
		sys.exit()	
	if not aTMcurrSelected:
		doPrintERROR("Error!!! Select something")
		sys.exit()	

#--------------procedura doSetKeyMode --------------------------------------------------------------------------------------------------------------------------
def doSetKeyMode(aTMbdMode):
	aTMactionTime = maya.currentTime(q=1)
	aTMbgcOK = [0.332,0.885,0.683]
	checkSelectionErrors()
	aTMkeyExists = maya.keyframe(q=1,t=(aTMactionTime,aTMactionTime),vc=1)
	if not aTMkeyExists:
		doPrintERROR("Error!!! No keys in this frame")
		sys.exit()
	maya.keyframe(e=1,t=(aTMactionTime,aTMactionTime),bd=aTMbdMode)
	maya.text('aTMSTATUS',e=1,l="OK!!!",bgc=aTMbgcOK)  #maya
	maya.text('aTMstatusInfo',e=1,bgc=aTMbgcOK)
	maya.rowLayout("aTMstatusRowlayout",e=1,bgc=aTMbgcOK) #maya

#--------------procedura doGhosts --------------------------------------------------------------------------------------------------------------------------
def doGhosts(doSomething):
	aTMbgcOK = [0.332,0.885,0.683]
	checkSelectionErrors()
	if doSomething>0:
		aTMshapesArray = []
		aTMghostsArray = []
		aTMlambertArray = []
		aTMcurrentTime = maya.currentTime(q=1)
		aTMcurrSelected = maya.ls(sl=1)
		if doSomething==1:
			maya.select(hi=1)
			aTMhierSelected = maya.ls(sl=1)
			for obj in aTMhierSelected:
				if maya.nodeType(obj)=="mesh":
					aTMghostNode = (maya.listConnections(obj+".worldMesh[0]"))
					if aTMghostNode:
						aTMtoDelete = maya.listConnections(aTMghostNode,d=1,s=0)
						maya.delete(aTMtoDelete[0])
		if doSomething==2:
			if maya.objExists("aTMghostColorHolder") :
				if not maya.attributeQuery('beforeColor',node="aTMghostColorHolder", ex=1 ) or not maya.attributeQuery('afterColor',node="aTMghostColorHolder", ex=1 ):
					maya.lockNode("aTMghostColorHolder",l=0)
					maya.delete("aTMghostColorHolder")
			if not maya.objExists("aTMghostColorHolder") :
				aTMghostColorHolder = maya.createNode("unknown",n="aTMghostColorHolder")
				maya.addAttr(ln="beforeColor",sn="bc",at="double3")
				maya.addAttr(ln="afterColor",sn="ac",at="double3")
				maya.addAttr(ln="beforeColorR",sn="bcr",at="double",p="beforeColor")
				maya.addAttr(ln="beforeColorG",sn="bcg",at="double",p="beforeColor")
				maya.addAttr(ln="beforeColorB",sn="bcb",at="double",p="beforeColor")
				maya.addAttr(ln="afterColorR",sn="acr",at="double",p="afterColor")
				maya.addAttr(ln="afterColorG",sn="acg",at="double",p="afterColor")
				maya.addAttr(ln="afterColorB",sn="acb",at="double",p="afterColor")
				maya.setAttr(aTMghostColorHolder+".beforeColor",0.317,0.471,0.669,typ="double3")
				maya.setAttr(aTMghostColorHolder+".afterColor",0,0.669,0.326,typ="double3")
				maya.lockNode(aTMghostColorHolder,l=1,ic=1)
				maya.attrColorSliderGrp('aTMbeforeColorSlider',e=1,at="aTMghostColorHolder.beforeColor")
				maya.attrColorSliderGrp('aTMafterColorSlider',e=1,at="aTMghostColorHolder.afterColor")
				maya.select(aTMcurrSelected)
			maya.select(hi=1)
			aTMhierSelected = maya.ls(sl=1)
			for obj in aTMhierSelected:
				if maya.nodeType(obj)=="mesh":
					aTMshapesArray.append(obj)
			aTMhierSelected = maya.ls()
			for obj in aTMhierSelected:
				if maya.nodeType(obj)=="snapshot":
					aTMconnected = maya.listConnections(obj,d=0,s=1)
					maya.select(aTMconnected,hi=1)
					aTMhierSelected = maya.ls(sl=1)
					maya.delete(maya.listConnections(obj,d=1,s=0))
					for mesh in aTMhierSelected:
						if maya.nodeType(mesh)=="mesh" and mesh not in aTMshapesArray:
							aTMshapesArray.append(mesh)
			if maya.objExists("aTMghostContainer") :
				maya.delete("aTMghostContainer")
			aTMworkMode = maya.radioButtonGrp('aTMworkModeRadiobutton',q=1,sl=1)
			print aTMworkMode
			if aTMworkMode==1: aTMghostUpdate = "animCurve"
			elif aTMworkMode==2: aTMghostUpdate = "always"
			aTMbeforeAfterVar = [maya.intFieldGrp('aTMGhostsInt',q=1,v1=1),maya.intFieldGrp('aTMGhostsInt',q=1,v2=1)]
			if aTMbeforeAfterVar[0] >-1 or aTMbeforeAfterVar[1]<1:
				doPrintERROR("Error!!! Ghosts out of range")
				sys.exit()
			maya.text('aTMSTATUS',e=1,l="OK!!!",bgc=aTMbgcOK)
			maya.text('aTMstatusInfo',e=1,bgc=aTMbgcOK)
			maya.rowLayout("aTMstatusRowlayout",e=1,bgc=aTMbgcOK)
			if aTMbeforeAfterVar[0] <-5 or aTMbeforeAfterVar[1]>5:
				doPrintWARNING("Worning!!! Ghosts above 5 may not be visible")			
			aTMbeforeTransparency = 1.0/(2**((-aTMbeforeAfterVar[0])))
			aTMafterTransparency = 0.5
			aTMghostContainer = maya.container(n="aTMghostContainer")
			for i in range(1,-aTMbeforeAfterVar[0]+1):
				if maya.objExists("aTMbefore"+str(i)+"_lb") : maya.delete("aTMbefore"+str(i)+"_lb"),maya.delete("aTMbefore"+str(i)+"_lbSG")
				aTMlambert = maya.shadingNode("lambert",au=1,n="aTMbefore"+str(i)+"_lb")
				maya.setAttr(aTMlambert+".transparency",-aTMbeforeTransparency+1,-aTMbeforeTransparency+1,-aTMbeforeTransparency+1,typ="double3")
				maya.sets(r=1,nss=1,em=1,n=aTMlambert+"SG")
				maya.connectAttr(aTMlambert+".outColor",aTMlambert+"SG.surfaceShader",f=1)
				aTMlambertArray.append(aTMlambert)
				aTMbeforeTransparency = aTMbeforeTransparency*2
				maya.container(aTMghostContainer,edit=1,an=aTMlambert,inc=1,ihb=1)
				maya.container(aTMghostContainer,edit=1,an=aTMlambert+"SG",inc=1,ihb=1)
				maya.connectAttr("aTMghostColorHolder.beforeColor",aTMlambert+".color",f=1)
			aTMlambertArray.append("lambert1")
			for i in range(1,aTMbeforeAfterVar[1]+1):
				if maya.objExists("aTMafter"+str(i)+"_lb") : maya.delete("aTMafter"+str(i)+"_lb"),maya.delete("aTMafter"+str(i)+"_lbSG")
				aTMlambert = maya.shadingNode("lambert",au=1,n="aTMafter"+str(i)+"_lb")
				maya.setAttr(aTMlambert+".transparency",aTMafterTransparency,aTMafterTransparency,aTMafterTransparency,typ="double3")
				maya.sets(r=1,nss=1,em=1,n=aTMlambert+"SG")
				maya.connectAttr(aTMlambert+".outColor",aTMlambert+"SG.surfaceShader",f=1)
				aTMlambertArray.append(aTMlambert)
				aTMafterTransparency = aTMafterTransparency+1.0/(2**(i+1))
				maya.container(aTMghostContainer,edit=1,an=aTMlambert,inc=1,ihb=1)
				maya.container(aTMghostContainer,edit=1,an=aTMlambert+"SG",inc=1,ihb=1)
				maya.connectAttr("aTMghostColorHolder.afterColor",aTMlambert+".color",f=1)
			for shape in aTMshapesArray:
				aTMghostsArrayTmp = []
				aTMghostNode = maya.snapshot(shape,n=shape+"GhostNode",ch=1,st=0,et=-aTMbeforeAfterVar[0]+aTMbeforeAfterVar[1],i=1,u=aTMghostUpdate )
				maya.select(aTMghostNode[0],hi=1)
				aTMghostShapeList = maya.ls(sl=1)
				for obj in aTMghostShapeList:
					if maya.nodeType(obj)=="mesh":
						aTMghostsArrayTmp.append(obj)
				aTMghostsArray.append(aTMghostsArrayTmp)
				aTMbeforeAdl = maya.createNode('addDoubleLinear',n=aTMghostNode[1]+"Before_adl")
				aTMafterAdl = maya.createNode('addDoubleLinear',n=aTMghostNode[1]+"After_adl")
				maya.setAttr(aTMbeforeAdl+".i2",aTMbeforeAfterVar[0])
				maya.setAttr(aTMafterAdl+".i2",aTMbeforeAfterVar[1])
				maya.connectAttr("time1.outTime",aTMbeforeAdl+".i1",f=1)
				maya.connectAttr("time1.outTime",aTMafterAdl+".i1",f=1)
				maya.connectAttr(aTMbeforeAdl+".o",aTMghostNode[1]+".startTime",f=1)
				maya.connectAttr(aTMafterAdl+".o",aTMghostNode[1]+".endTime",f=1)
				maya.container(aTMghostContainer,edit=1,an=aTMghostNode)
				maya.container(aTMghostContainer,edit=1,an=aTMbeforeAdl,inc=1,ihb=1)
				maya.container(aTMghostContainer,edit=1,an=aTMafterAdl,inc=1,ihb=1)
			for i in range(0,len(aTMghostsArray)):
				for a in range(0,len(aTMghostsArray[i])):
					maya.setAttr(aTMghostsArray[i][a]+".overrideEnabled",1)
					maya.setAttr(aTMghostsArray[i][a]+".overrideDisplayType",2)
					maya.setAttr(aTMghostsArray[i][a]+".backfaceCulling",3)
					if a==-aTMbeforeAfterVar[0]:
						maya.setAttr(aTMghostsArray[i][a]+".v",0)
					else:
						maya.disconnectAttr(aTMghostsArray[i][a]+".instObjGroups[0]","initialShadingGroup.dagSetMembers",na=1)
						maya.connectAttr(aTMghostsArray[i][a]+".instObjGroups[0]",aTMlambertArray[a]+"SG.dagSetMembers["+str(i)+"]",f=1)
		maya.select(aTMcurrSelected)

	if doSomething==0:
		if maya.objExists("aTMghostColorHolder") :
			maya.lockNode("aTMghostColorHolder",l=0)
		try:
			maya.delete('aTMghostContainer')
			maya.delete("aTMghostColorHolder")
		except :
			pass
	
#--------------procedura doPrintERROR --------------------------------------------------------------------------------------------------------------------------
def doPrintERROR(aTMerrorMSG):
	aTMbgcError = [0.968,0.182,0]
	maya.text('aTMSTATUS',e=1,l=aTMerrorMSG,bgc=aTMbgcError)
	maya.text('aTMstatusInfo',e=1,bgc=aTMbgcError)
	maya.rowLayout("aTMstatusRowlayout",e=1,bgc=aTMbgcError)

#--------------procedura doPrintWARNING --------------------------------------------------------------------------------------------------------------------------
def doPrintWARNING(aTMwarningMSG):
	aTMbgcWarning = [0.767,0.124,0.872]
	maya.text('aTMSTATUS',e=1,l=aTMwarningMSG,bgc=aTMbgcWarning)
	maya.text('aTMstatusInfo',e=1,bgc=aTMbgcWarning)
	maya.rowLayout("aTMstatusRowlayout",e=1,bgc=aTMbgcWarning)
	
#--------------procedura collectSettingsState --------------------------------------------------------------------------------------------------------------------------
def collectSettingsState():
	global aTMworkMode
	global aTMmayaLink
	global aTMtweenBetweenValue
	global aTMkeyTangentValue	
	global aTMkeyTypeValue
	global aTMpredictArcValue
	global aTMpredictVar
	aTMworkMode = maya.radioButtonGrp('aTMworkModeRadiobutton',q=1,sl=1) #maya
	aTMmayaLink = maya.radioButtonGrp('aTMmayaLinkRadiobutton',q=1,sl=1) #maya
	aTMtweenBetweenValue = maya.radioButtonGrp('aTMtweenBetweenRadiobutton',q=1,sl=1) #maya
	aTMkeyTangentValue = maya.radioButtonGrp('aTMkeyTangentRadiobutton',q=1,sl=1) #maya
	aTMkeyTypeValue = maya.radioButtonGrp('aTMkeyTypeRadiobutton',q=1,sl=1) #maya
	aTMpredictArcValue = [maya.checkBoxGrp('aTMpredictArcCheckBox',q=1,v1=1),maya.checkBoxGrp('aTMpredictArcCheckBox',q=1,v2=1)] #maya
	aTMpredictVar = maya.floatFieldGrp('aTMpredictVarCheckBox',q=1,v1=1) #maya

#--------------procedura Glowna --------------------------------------------------------------------------------------------------------------------------	
def doSetTweenKey(inputType,value):

	global aTMstatus
	global aTMactionTime
	global aTMtweenMachineCollect
	global aTMlastSelected
	global aTManimCurvesArray
	global aTManimChannelsArray
	global aTMerror
	global aTMwarning
	global aTMbgColor
	global aTMworkMode
	global aTMtweenBetweenValue
	global aTMtangentOutValueArray
	global aTMtangentInValueArray
	global aTMkeyTypeValue
	global aTMpredictArcValue
	global aTMpredictVar
	global aTMkeyTangentValue
	global aTMprevKeysArray
	global aTMnextKeysArray
	global aTMprevPoseArray
	global aTMnextPoseArray
	global aTMminPrevKeysArcArray
	global aTMmaxPrevKeysArcArray
	global aTMminNextKeysArcArray
	global aTMmaxNextKeysArcArray
	global aTMminPrevPoseArcArray
	global aTMmaxPrevPoseArcArray
	global aTMminNextPoseArcArray
	global aTMmaxNextPoseArcArray
	global aTMlastKeysTimeArray
	global aTMcomingKeysTimeArray
	global aTMlastPoseTimeArray
	global aTMcomingPoseTimeArray
	global aTMprevKeysArcArray
	global aTMnextKeysArcArray
	global aTMprevPoseArcArray
	global aTMnextPoseArcArray
	
	aTMbgcOK = [0.332,0.885,0.683]
	aTMcurrentTime = maya.currentTime(q=1) #maya
	
#--------------sprawdzanie postawowych bledow
	if maya.checkBoxGrp('aTMdoTweenOn',q=1,v1=1)==1 or maya.checkBoxGrp('aTMdoTweenOn',q=1,v2=1)==1: #maya
		aTMcurrSelected = maya.ls(sl=1,tr=1) #maya
	else:
		doPrintERROR("Error!!! Check \"Tween on\" option")
		sys.exit()	
	if not aTMcurrSelected:
		doPrintERROR("Error!!! Select something")
		sys.exit()		
	if inputType == "button":
		maya.floatSliderGrp('aTMmainFloatSliderGrp',e=1,v=value) #maya
	if aTMactionTime!=aTMcurrentTime or aTMlastSelected!=aTMcurrSelected:

#--------------jednorazowy pobor danych z krzywych (wyrzucenie breakdownow z listy i zbudowanie infa o zakresie animacji oraz pozycji kluczy)
		aTMerror = 0
		aTManimCurvesArray = []
		aTManimChannelsArray = []
		aTManimValueArray = []
		aTManimTimeArray = []
		aTManimTimeGloalArray = []
		aTManimTimeList = []
		aTManimKeyPoseArray = []
		aTManimTangOutArray = []
		aTMtangentOutValueArray = []
		aTMtangentInValueArray = []
		aTMprevKeysLinearDataArray = []
		aTMnextKeysLinearDataArray = []
		aTMprevPoseLinearDataArray = []
		aTMnextPoseLinearDataArray = []
		aTMprevKeysArray = []
		aTMnextKeysArray = []
		aTMprevPoseArray = []
		aTMnextPoseArray = []
		aTMlastKeysTimeArray = []
		aTMcomingKeysTimeArray = []
		aTMlastPoseTimeArray = []
		aTMcomingPoseTimeArray = []
		aTMminPrevKeysArcArray = []
		aTMmaxPrevKeysArcArray = []
		aTMminNextKeysArcArray = []
		aTMmaxNextKeysArcArray = []
		aTMminPrevPoseArcArray = []
		aTMmaxPrevPoseArcArray = []
		aTMminNextPoseArcArray = []
		aTMmaxNextPoseArcArray = []
		aTMprevKeysArcArray = []
		aTMnextKeysArcArray = []
		aTMprevPoseArcArray = []
		aTMnextPoseArcArray = []
		aTMstatus = "OK!!!"	
		aTMwarning = 0
		aTMbgColor = aTMbgcOK
		aTMtweenBetweenValue = maya.radioButtonGrp('aTMtweenBetweenRadiobutton',q=1,sl=1) #maya
		aTMkeyTangentValue = maya.radioButtonGrp('aTMkeyTangentRadiobutton',q=1,sl=1) #maya
		aTMselectedChannels = maya.channelBox("mainChannelBox",q=1,sma=1)#maya	<-
		for aTMtransform in aTMcurrSelected:
			aTManimCurves = maya.findKeyframe(aTMtransform,curve=True) #maya
			if aTManimCurves:
				for aTManimCurve in aTManimCurves:
					aTManimChannelTMP = maya.connectionInfo(aTManimCurve+".o",dfs=1) #maya	<-
					aTManimChannelSN = maya.attributeName(aTManimChannelTMP,s=1) #maya	<-
					if aTMselectedChannels and aTManimChannelSN not in aTMselectedChannels: #maya	<-
							continue #maya	<-
					else: #maya	<-
						aTManimCurvesArray.append(aTManimCurve)
						aTManimChannelsArray.append(aTManimChannelTMP) #maya
						aTManimValueTMP = maya.keyframe(aTManimCurve,q=1,vc=1) #maya
						aTManimTimeTMP = maya.keyframe(aTManimCurve,q=1,tc=1) #maya
						aTManimBreakTMP = maya.keyframe(aTManimCurve,q=1,bd=1) #maya
						aTManimTangOutTMP = maya.keyTangent(aTManimCurve,q=1,ott=1) #maya
						if aTManimBreakTMP and aTMtweenBetweenValue ==2:
							for aTMbreakdown in aTManimBreakTMP:
								aTMindex = aTManimTimeTMP.index(aTMbreakdown)
								aTManimTimeTMP.remove(aTMbreakdown)
								aTManimValueTMP.pop(aTMindex)
								aTManimTangOutTMP.pop(aTMindex)
						aTManimTimeList = aTManimTimeList + aTManimTimeTMP
						aTManimTimeArray.append(aTManimTimeTMP)
						aTManimKeyPoseArray.append([1] * len(aTManimTimeTMP))
						aTManimValueArray.append(aTManimValueTMP)
						aTManimTangOutArray.append(aTManimTangOutTMP)
		aTManimTimeGlobalArray = sorted(set(aTManimTimeList))		
		aTMactionTime = aTMcurrentTime
		aTMlastSelected = aTMcurrSelected
		if not aTManimCurvesArray:
			doPrintERROR("Error!!! No animated object")
			sys.exit()	
		if aTMcurrentTime < aTManimTimeGlobalArray[0] or aTMcurrentTime >aTManimTimeGlobalArray[len(aTManimTimeGlobalArray)-1]:
			doPrintERROR("Error!!! Timeline behind anmation range")
			sys.exit()	
		if aTMcurrentTime == aTManimTimeGlobalArray[0] or aTMcurrentTime ==aTManimTimeGlobalArray[len(aTManimTimeGlobalArray)-1]:
			doPrintERROR("Error!!! You can't add breakdown at first or last animation frame")
			sys.exit()	

#-------------- uzupelnianie danych z krzywych o klucze widma 1- fizyczny klucz, 2- pierwszy i ostatni klucz (widmo), 0 - klucz widmo
		for i in range(0,len(aTManimCurvesArray)):
			if len(aTManimTimeGlobalArray) != len(aTManimTimeArray[i]):
				aTMmissedFramesArray = list(sorted(set(aTManimTimeGlobalArray).difference(set(aTManimTimeArray[i]))))
				for aTMframe in aTMmissedFramesArray:
					aTMindex = aTManimTimeGlobalArray.index(aTMframe)
					aTMposeVarTMP = 0
					if 	aTMframe<aTManimTimeArray[i][0]:
						aTMprevFrameTMP = aTMframe
						aTMprevVarTMP = aTManimValueArray[i][aTMindex]
						aTMposeVarTMP = 2
					else:
						aTMprevFrameTMP = aTManimTimeArray[i][aTMindex-1]
						aTMprevVarTMP = aTManimValueArray[i][aTMindex-1]
					if 	aTMindex==len(aTManimTimeArray[i]):
						aTMnextFrameTMP = aTMframe
						aTMnextVarTMP = aTManimValueArray[i][aTMindex-1]
					else:
						aTMnextFrameTMP = aTManimTimeArray[i][aTMindex]
						aTMnextVarTMP = aTManimValueArray[i][aTMindex]
					if aTMindex==len(aTManimTimeGlobalArray)-1: aTMposeVarTMP = 2
					aTManimValueArray[i].insert(aTMindex,((aTMnextVarTMP-aTMprevVarTMP)/(aTMnextFrameTMP-aTMprevFrameTMP) * (aTMframe-aTMprevFrameTMP) + aTMprevVarTMP))
					aTManimTimeArray[i].insert(aTMindex,aTMframe)
					aTManimKeyPoseArray[i].insert(aTMindex,aTMposeVarTMP)
					if aTMindex-1<0: aTMprevTangOutTMP="linear"
					else: aTMprevTangOutTMP=aTManimTangOutArray[i][aTMindex-1]
					aTManimTangOutArray[i].insert(aTMindex,str(aTMprevTangOutTMP))
			if aTMactionTime in aTManimTimeGlobalArray:
				aTMindexTMP = aTManimTimeGlobalArray.index(aTMactionTime)
				aTManimValueArray[i].pop(aTMindexTMP)
				aTManimTimeArray[i].pop(aTMindexTMP)
				aTManimKeyPoseArray[i].pop(aTMindexTMP)
				if i == len(aTManimCurvesArray)-1:
					aTManimTimeGlobalArray.pop(aTMindexTMP)
					
					
					
					
					
#					doPrintWARNING("Warning!!! You are changing key pose")
#					aTMwarning = 1
					
#-------------- zrobmy cos - dane do mnozenia Linear
		aTMwarningTMP = []
		for i in range(0,len(aTManimCurvesArray)):
			for a in range(0,len(aTManimTimeGlobalArray)):
				if aTManimTimeGlobalArray[a] <= aTMactionTime <= aTManimTimeGlobalArray[a+1]:
					aTMprevPoseLinearVal = (aTManimValueArray[i][a])
					aTMprevPoseLinearTime = (aTManimTimeArray[i][a])
					if a-1<0:
						aTMprev2PoseLinearVal =aTManimValueArray[i][a]
						aTMprev2PoseLinearTime =aTManimTimeArray[i][a]
					else:
						aTMprev2PoseLinearVal =aTManimValueArray[i][a-1]
						aTMprev2PoseLinearTime =aTManimTimeArray[i][a-1]
					aTMnextPoseLinearVal =(aTManimValueArray[i][a+1])
					aTMnextPoseLinearTime =(aTManimTimeArray[i][a+1])
					if a+2>=len(aTManimTimeGlobalArray):
						aTMnext2PoseLinearVal =aTManimValueArray[i][a+1]
						aTMnext2PoseLinearTime =aTManimTimeArray[i][a+1]
					else:
						aTMnext2PoseLinearVal =aTManimValueArray[i][a+2]
						aTMnext2PoseLinearTime =aTManimTimeArray[i][a+2]
					b=a
					if aTManimKeyPoseArray[i][a]==0:	
						aTMwarningTMP.append(1)
						while aTManimKeyPoseArray[i][b]==0:	b=b-1
						aTMprevKeysLinearVal =(aTManimValueArray[i][b])
						aTMprevKeysLinearTime =(aTManimTimeArray[i][b])
					else:
						aTMprevKeysLinearVal =(aTManimValueArray[i][a])
						aTMprevKeysLinearTime =(aTManimTimeArray[i][b])
					c=b-1
					if c<0:
						aTMprev2KeysLinearVal = (aTManimValueArray[i][b])
						aTMprev2KeysLinearTime = (aTManimTimeArray[i][b])
					elif aTManimKeyPoseArray[i][c]==0:
						while aTManimKeyPoseArray[i][c]==0:	c=c-1
						aTMprev2KeysLinearVal = (aTManimValueArray[i][c])
						aTMprev2KeysLinearTime = (aTManimTimeArray[i][c])
					else:
						aTMprev2KeysLinearVal = (aTManimValueArray[i][b-1])
						aTMprev2KeysLinearTime = (aTManimTimeArray[i][b-1])
					b=a+1
					if aTManimKeyPoseArray[i][a+1]==0:
						aTMwarningTMP.append(2)
						while aTManimKeyPoseArray[i][b]==0:	b=b+1
						aTMnextKeysLinearVal =(aTManimValueArray[i][b])
						aTMnextKeysLinearTime =(aTManimTimeArray[i][b])
					else:
						aTMnextKeysLinearVal =(aTManimValueArray[i][a+1])
						aTMnextKeysLinearTime =(aTManimTimeArray[i][a+1])
					c=b+1
					if c>=len(aTManimTimeGlobalArray):
						aTMnext2KeysLinearVal = (aTManimValueArray[i][b])
						aTMnext2KeysLinearTime = (aTManimTimeArray[i][b])
					elif aTManimKeyPoseArray[i][c]==0:
						while aTManimKeyPoseArray[i][c]==0:	c=c+1
						aTMnext2KeysLinearVal = (aTManimValueArray[i][c])
						aTMnext2KeysLinearTime = (aTManimTimeArray[i][c])
					else:
						aTMnext2KeysLinearVal = (aTManimValueArray[i][b+1])
						aTMnext2KeysLinearTime = (aTManimTimeArray[i][b+1])
					aTMminPrevKeysValue = aTMprevKeysLinearVal
					if aTMprevKeysLinearTime==aTMprev2KeysLinearTime: aTMmaxPrevKeysValue = aTMnextKeysLinearVal
					else: aTMmaxPrevKeysValue = aTMprevKeysLinearVal+((aTMprev2KeysLinearVal-aTMprevKeysLinearVal) / (aTMprev2KeysLinearTime-aTMprevKeysLinearTime)) * (aTMnextKeysLinearTime-aTMprevKeysLinearTime)
					if aTMnextKeysLinearTime==aTMnext2KeysLinearTime: aTMminNextKeysValue = aTMprevKeysLinearVal
					else: aTMminNextKeysValue = aTMnextKeysLinearVal-((aTMnext2KeysLinearVal-aTMnextKeysLinearVal) / (aTMnext2KeysLinearTime-aTMnextKeysLinearTime)) * (aTMnextKeysLinearTime-aTMprevKeysLinearTime)
					aTMmaxNextKeysValue = aTMnextKeysLinearVal
					aTMminPrevPoseValue = aTMprevPoseLinearVal
					if aTMprevPoseLinearTime==aTMprev2PoseLinearTime: aTMmaxPrevPoseValue = aTMnextPoseLinearVal
					else: aTMmaxPrevPoseValue = aTMprevPoseLinearVal+((aTMprev2PoseLinearVal-aTMprevPoseLinearVal) / (aTMprev2PoseLinearTime-aTMprevPoseLinearTime)) * (aTMnextPoseLinearTime-aTMprevPoseLinearTime)
					if aTMnextPoseLinearTime==aTMnext2PoseLinearTime: aTMminNextPoseValue = aTMprevPoseLinearVal
					else: aTMminNextPoseValue = aTMnextPoseLinearVal-((aTMnext2PoseLinearVal-aTMnextPoseLinearVal) / (aTMnext2PoseLinearTime-aTMnextPoseLinearTime)) * (aTMnextPoseLinearTime-aTMprevPoseLinearTime)
					aTMmaxNextPoseValue = aTMnextPoseLinearVal
					aTMprevKeysArray.append(aTMprevKeysLinearVal)
					aTMnextKeysArray.append(aTMnextKeysLinearVal)
					aTMprevPoseArray.append(aTMprevPoseLinearVal)
					aTMnextPoseArray.append(aTMnextPoseLinearVal)
					aTMminPrevKeysArcArray.append(aTMminPrevKeysValue)
					aTMmaxPrevKeysArcArray.append(aTMmaxPrevKeysValue)
					aTMminNextKeysArcArray.append(aTMminNextKeysValue)
					aTMmaxNextKeysArcArray.append(aTMmaxNextKeysValue)
					aTMminPrevPoseArcArray.append(aTMminPrevPoseValue)
					aTMmaxPrevPoseArcArray.append(aTMmaxPrevPoseValue)
					aTMminNextPoseArcArray.append(aTMminNextPoseValue)
					aTMmaxNextPoseArcArray.append(aTMmaxNextPoseValue)				

					
					aTMprevKeysArcArray.append(aTMprev2KeysLinearVal)
					aTMnextKeysArcArray.append(aTMnext2KeysLinearVal)
					aTMprevPoseArcArray.append(aTMprev2PoseLinearVal)
					aTMnextPoseArcArray.append(aTMnext2PoseLinearVal)
					
		
					aTMlastKeysTimeArray.append(aTMprevKeysLinearTime)
					aTMcomingKeysTimeArray.append(aTMnextKeysLinearTime)
					aTMlastPoseTimeArray.append(aTMprevPoseLinearTime)
					aTMcomingPoseTimeArray.append(aTMnextPoseLinearTime)
					if aTMkeyTangentValue ==1:
						aTMtangentInValueArray.append("spline")
						aTMtangentOutValueArray.append("spline")
					if aTMkeyTangentValue ==2:
						aTMtangentInValueArray.append("linear")
						aTMtangentOutValueArray.append("step")
					if aTMkeyTangentValue ==3:
						aTMtangentInValueArray.append("linear")
						aTMtangentOutValueArray.append("linear")
		if aTMwarningTMP:
			if len(aTMwarningTMP)==1 and aTMwarningTMP[0] == 1: doPrintWARNING("Warning!!! Previous pose is not fully keyed - can be distorted")
			elif len(aTMwarningTMP)==1 and aTMwarningTMP[0] == 2: doPrintWARNING("Warning!!! Next pose is not fully keyed - can be distorted")
			else: doPrintWARNING("Warning!!! Both poses are not fully keyed - can be distorted")
			aTMwarning = 1

#-------------------------------------------------------------- WYKONANIE
	if aTMerror == 0:
		if aTMtweenMachineCollect ==1:
			aTMworkMode = maya.radioButtonGrp('aTMworkModeRadiobutton',q=1,sl=1) #maya
			aTMtweenBetweenValue = maya.radioButtonGrp('aTMtweenBetweenRadiobutton',q=1,sl=1) #maya
			aTMpredictArcValue = [maya.checkBoxGrp('aTMpredictArcCheckBox',q=1,v1=1),maya.checkBoxGrp('aTMpredictArcCheckBox',q=1,v2=1)] #maya
			aTMkeyTypeValue = maya.radioButtonGrp('aTMkeyTypeRadiobutton',q=1,sl=1) #maya
			aTMpredictVar = maya.floatFieldGrp('aTMpredictVarCheckBox',q=1,v1=1) #maya
			if aTMworkMode ==1:
				maya.select(aTManimCurvesArray,tgl=1) #maya
				for i in range(0,len(aTManimCurvesArray)):
					maya.disconnectAttr(aTManimCurvesArray[i]+".o",aTManimChannelsArray[i][0]) #maya
		aTMnewKeyValueArray = []
		sliderValue = (maya.floatSliderGrp('aTMmainFloatSliderGrp',q=1,v=1)/100) #maya
		rad_to_deg = math.degrees
		atan = math.atan
		cos = math.cos
		sin = math.sin
		PI = math.pi
		aTMparametr=aTMpredictVar+1
		aTMamplituda= 1/(sin((aTMparametr/2-1/3)*PI))
		aTMtranslateSTR = "translate"
		aTMrotateSTR = "rotate"
		for i in range(0,len(aTManimChannelsArray)):
			if aTMpredictArcValue[0]==1 and aTManimChannelsArray[i][0].find(aTMtranslateSTR,len(aTManimChannelsArray[i][0])-12)>0:
				if aTMtweenBetweenValue ==1:
					aTMphantomAnimCurve1 =aTMminPrevPoseArcArray[i]+((aTMmaxPrevPoseArcArray[i]-aTMminPrevPoseArcArray[i])*sliderValue)
					aTMphantomAnimCurve2 =aTMminNextPoseArcArray[i]+((aTMmaxNextPoseArcArray[i]-aTMminNextPoseArcArray[i])*sliderValue)
					if sliderValue<0: aTMnewKeyValue =aTMprevPoseArcArray[i]+((aTMprevPoseArray[i]-aTMprevPoseArcArray[i])*(sliderValue+1))
					elif sliderValue>1: aTMnewKeyValue =aTMnextPoseArray[i]+((aTMnextPoseArcArray[i]-aTMnextPoseArray[i])*(sliderValue-1))
					else: aTMnewKeyValue =((aTMphantomAnimCurve1+aTMphantomAnimCurve2)/2)+(-cos(sliderValue*PI))*((aTMphantomAnimCurve2-aTMphantomAnimCurve1)/2)
				if aTMtweenBetweenValue ==2:
					aTMphantomAnimCurve1 =aTMminPrevKeysArcArray[i]+((aTMmaxPrevKeysArcArray[i]-aTMminPrevKeysArcArray[i])*sliderValue)
					aTMphantomAnimCurve2 =aTMminNextKeysArcArray[i]+((aTMmaxNextKeysArcArray[i]-aTMminNextKeysArcArray[i])*sliderValue)
					if sliderValue<0: aTMnewKeyValue =aTMprevKeysArcArray[i]+((aTMprevKeysArray[i]-aTMprevKeysArcArray[i])*(sliderValue+1))
					elif sliderValue>1:aTMnewKeyValue =aTMnextKeysArray[i]+((aTMnextKeysArcArray[i]-aTMnextKeysArray[i])*(sliderValue-1))
					else: aTMnewKeyValue =((aTMphantomAnimCurve1+aTMphantomAnimCurve2)/2)+(-cos(sliderValue*PI))*((aTMphantomAnimCurve2-aTMphantomAnimCurve1)/2)						
			elif aTMpredictArcValue[1]==1 and aTManimChannelsArray[i][0].find(aTMrotateSTR,len(aTManimChannelsArray[i][0])-9):					
				if aTMtweenBetweenValue ==1:
					aTMphantomAnimCurve1 =aTMminPrevPoseArcArray[i]+((aTMmaxPrevPoseArcArray[i]-aTMminPrevPoseArcArray[i])*sliderValue)
					aTMphantomAnimCurve2 =aTMminNextPoseArcArray[i]+((aTMmaxNextPoseArcArray[i]-aTMminNextPoseArcArray[i])*sliderValue)
					aTMnewKeyValue =(((aTMphantomAnimCurve1+aTMphantomAnimCurve2)/2)+sin(sliderValue*PI-(aTMparametr/2-1/3)*PI)*((aTMphantomAnimCurve2-aTMphantomAnimCurve1)/2))*aTMamplituda
				if aTMtweenBetweenValue ==2:
					aTMphantomAnimCurve1 =aTMminPrevKeysArcArray[i]+((aTMmaxPrevKeysArcArray[i]-aTMminPrevKeysArcArray[i])*sliderValue)
					aTMphantomAnimCurve2 =aTMminNextKeysArcArray[i]+((aTMmaxNextKeysArcArray[i]-aTMminNextKeysArcArray[i])*sliderValue)
					aTMnewKeyValue =(((aTMphantomAnimCurve1+aTMphantomAnimCurve2)/2)+sin(sliderValue*PI-(aTMparametr/2-1/3)*PI)*((aTMphantomAnimCurve2-aTMphantomAnimCurve1)/2))*aTMamplituda
			else:
				if aTMtweenBetweenValue ==2:	aTMnewKeyValue=(aTMnextKeysArray[i] - aTMprevKeysArray[i])*sliderValue+aTMprevKeysArray[i]
				if aTMtweenBetweenValue ==1:	aTMnewKeyValue=(aTMnextPoseArray[i] - aTMprevPoseArray[i])*sliderValue+aTMprevPoseArray[i]				
			if aTMworkMode ==1 and inputType != "setPoseKey":
				maya.setAttr(aTManimChannelsArray[i][0],aTMnewKeyValue,c=1)
				aTMnewKeyValueArray.append(aTMnewKeyValue)
			elif aTMworkMode ==2 and inputType != "setPoseKey":
				maya.setKeyframe(aTManimCurvesArray[i],v=aTMnewKeyValue-1,bd=aTMkeyTypeValue-1)
				maya.keyframe(aTManimCurvesArray[i],e=1,t=(aTMactionTime,aTMactionTime),vc=1,iub=1,r=1,o="over")
				maya.keyTangent(aTManimCurvesArray[i],e=1,t=(aTMactionTime,aTMactionTime),itt=aTMtangentInValueArray[i],ott=aTMtangentOutValueArray[i])
				if aTMkeyTangentValue ==1:
					if aTMprevKeysArcArray[i]<=aTMprevKeysArray[i]>=aTMnewKeyValue or aTMprevKeysArcArray[i]>=aTMprevKeysArray[i]<=aTMnewKeyValue: aTMprevOutTangent = 0
					else: aTMprevOutTangent = (rad_to_deg(atan((aTMnewKeyValue-aTMprevKeysArray[i])/(aTMactionTime-aTMlastKeysTimeArray[i]))))
					if  aTMprevKeysArray[i]<=aTMnewKeyValue>=aTMnextKeysArray[i] or aTMprevKeysArray[i]>=aTMnewKeyValue<=aTMnextKeysArray[i]: aTMthisTangent = 0
					else: aTMthisTangent = ((rad_to_deg(atan((aTMnewKeyValue-aTMprevKeysArray[i])/(aTMactionTime-aTMlastKeysTimeArray[i]))))+(rad_to_deg(atan((aTMnextKeysArray[i]-aTMnewKeyValue)/(aTMcomingKeysTimeArray[i]-aTMactionTime)))))/2
					if aTMnewKeyValue<=aTMnextKeysArray[i]>=aTMnextKeysArcArray[i] or aTMnewKeyValue>=aTMnextKeysArray[i]<=aTMnextKeysArcArray[i]: aTMnextInTangent = 0
					else: aTMnextInTangent = (rad_to_deg(atan((aTMnextKeysArray[i]-aTMnewKeyValue)/(aTMcomingKeysTimeArray[i]-aTMactionTime))))
					maya.keyTangent(aTManimCurvesArray[i],e=1,t=(aTMlastKeysTimeArray[i],aTMlastKeysTimeArray[i]),ia=aTMprevOutTangent,oa=aTMprevOutTangent)
					maya.keyTangent(aTManimCurvesArray[i],e=1,t=(aTMactionTime,aTMactionTime),ia=aTMthisTangent,oa=aTMthisTangent)
					maya.keyTangent(aTManimCurvesArray[i],e=1,t=(aTMcomingKeysTimeArray[i],aTMcomingKeysTimeArray[i]),ia=aTMnextInTangent,oa=aTMnextInTangent)
				if aTMkeyTangentValue ==2:
					maya.keyTangent(aTManimCurvesArray[i],e=1,t=(aTMlastKeysTimeArray[i],aTMlastKeysTimeArray[i]),ott=aTMtangentOutValueArray[i])
		if inputType == "sliderEnd" or inputType =="button" or inputType == "setPoseKey":
			aTMtweenMachineCollect = 1
			if aTMworkMode ==1:
				maya.select(aTManimCurvesArray,tgl=1)
				maya.undoInfo(swf=1) 
				for i in range(0,len(aTManimCurvesArray)):
					if inputType != "setPoseKey":
						maya.setKeyframe(aTManimCurvesArray[i],v=aTMnewKeyValueArray[i],bd=aTMkeyTypeValue-1)
						maya.keyTangent(aTManimCurvesArray[i],e=1,t=(aTMactionTime,aTMactionTime),itt=aTMtangentInValueArray[i],ott=aTMtangentOutValueArray[i])
						if aTMkeyTangentValue ==1:
							if aTMprevKeysArcArray[i]<=aTMprevKeysArray[i]>=aTMnewKeyValueArray[i] or aTMprevKeysArcArray[i]>=aTMprevKeysArray[i]<=aTMnewKeyValueArray[i]: aTMprevOutTangent = 0
							else: aTMprevOutTangent = (rad_to_deg(atan((aTMnewKeyValueArray[i]-aTMprevKeysArray[i])/(aTMactionTime-aTMlastKeysTimeArray[i]))))
							if  aTMprevKeysArray[i]<=aTMnewKeyValueArray[i]>=aTMnextKeysArray[i] or aTMprevKeysArray[i]>=aTMnewKeyValueArray[i]<=aTMnextKeysArray[i]: aTMthisTangent = 0
							else: aTMthisTangent = ((rad_to_deg(atan((aTMnewKeyValueArray[i]-aTMprevKeysArray[i])/(aTMactionTime-aTMlastKeysTimeArray[i]))))+(rad_to_deg(atan((aTMnextKeysArray[i]-aTMnewKeyValueArray[i])/(aTMcomingKeysTimeArray[i]-aTMactionTime)))))/2
							if aTMnewKeyValueArray[i]<=aTMnextKeysArray[i]>=aTMnextKeysArcArray[i] or aTMnewKeyValueArray[i]>=aTMnextKeysArray[i]<=aTMnextKeysArcArray[i]: aTMnextInTangent = 0
							else: aTMnextInTangent = (rad_to_deg(atan((aTMnextKeysArray[i]-aTMnewKeyValueArray[i])/(aTMcomingKeysTimeArray[i]-aTMactionTime))))
							maya.keyTangent(aTManimCurvesArray[i],e=1,t=(aTMlastKeysTimeArray[i],aTMlastKeysTimeArray[i]),ia=aTMprevOutTangent,oa=aTMprevOutTangent)
							maya.keyTangent(aTManimCurvesArray[i],e=1,t=(aTMactionTime,aTMactionTime),ia=aTMthisTangent,oa=aTMthisTangent)
							maya.keyTangent(aTManimCurvesArray[i],e=1,t=(aTMcomingKeysTimeArray[i],aTMcomingKeysTimeArray[i]),ia=aTMnextInTangent,oa=aTMnextInTangent)
						if aTMkeyTangentValue ==2:
							maya.keyTangent(aTManimCurvesArray[i],e=1,t=(aTMlastKeysTimeArray[i],aTMlastKeysTimeArray[i]),ott=aTMtangentOutValueArray[i])
				maya.undoInfo(swf=0)
				for i in range(0,len(aTManimCurvesArray)):
					maya.connectAttr(aTManimCurvesArray[i]+".o",aTManimChannelsArray[i][0],f=1) #maya
#					maya.keyframe(aTManimCurvesArray[i],e=1,t=(aTMactionTime,aTMactionTime),vc=1,iub=1,r=1,o="over")
			maya.undoInfo(swf=1) #maya					
			if inputType == "setPoseKey":
				for i in range(0,len(aTManimCurvesArray)):
					if value == "prev":
						aTMkeyPoseTime = aTMlastPoseTimeArray[i]
						aTMkeyPoseVal = aTMprevPoseArray[i]
					if value == "line":
						aTMkeyPoseTime = aTMactionTime
						aTMkeyPoseVal = ((aTMnextKeysArray[i]-aTMprevKeysArray[i])/(aTMcomingKeysTimeArray[i]-aTMlastKeysTimeArray[i])*(aTMactionTime-aTMlastKeysTimeArray[i]))+aTMprevKeysArray[i]
					if value == "flow":
						aTMkeyPoseTime = aTMactionTime
						aTMkeyPoseValTMP = maya.keyframe(aTManimCurvesArray[i],q=1,t=(aTMkeyPoseTime,aTMkeyPoseTime),ev=1)
						aTMkeyPoseVal = aTMkeyPoseValTMP[0]
					if value == "next":
						aTMkeyPoseTime = aTMcomingPoseTimeArray[i]
						aTMkeyPoseVal = aTMnextPoseArray[i]
					maya.setKeyframe(aTManimCurvesArray[i],t=(aTMkeyPoseTime,aTMkeyPoseTime),v=aTMkeyPoseVal,bd=aTMkeyTypeValue-1)
					maya.keyTangent(aTManimCurvesArray[i],e=1,t=(aTMkeyPoseTime,aTMkeyPoseTime),itt="spline",ott="spline")
					aTMwarning = 0	
				doSetaTMactionTime()			
		else:
			aTMtweenMachineCollect = 0
			maya.undoInfo(swf=0) #maya
		if aTMwarning == 0:
			maya.text('aTMSTATUS',e=1,l="OK!!!",bgc=aTMbgcOK)  #maya
			maya.text('aTMstatusInfo',e=1,bgc=aTMbgcOK)
			maya.rowLayout("aTMstatusRowlayout",e=1,bgc=aTMbgcOK) #maya

#--------------procedura doUpdateWindowSlider --------------------------------------------------------------------------------------------------------------------------
def doUpdateWindowSlider(aTMcurrentTime):
	aTMkeyExists = maya.keyframe(q=1,t=(aTMcurrentTime,aTMcurrentTime),vc=1)
	if not aTMkeyExists:
		global aTMlastSelected
		global aTManimCurvesArray
		global aTManimChannelsArray
		global aTMtweenBetweenValue
		global aTMmaxValArray
		global aTMminValArray
		global aTMpercentArray
		aTManimTimeList = []
		aTManimTimeArray = []
		aTManimKeyPoseArray = []
		aTManimValueArray = []
		aTMpercentArray = []
		aTMcurrSelected = maya.ls(sl=1,tr=1)
		if aTMlastSelected!=aTMcurrSelected and aTMcurrSelected:
			aTMmaxValArray = []
			aTMminValArray = []
			aTManimCurvesArray = []
			aTManimChannelsArray = []
			collectSettingsState()
			for aTMtransform in aTMcurrSelected:
				aTManimCurves = maya.findKeyframe(aTMtransform,curve=True)
				for aTManimCurve in aTManimCurves:
					aTManimCurvesArray.append(aTManimCurve)
					aTManimChannelsArray.append(maya.connectionInfo(aTManimCurve+".o",dfs=1)) #maya
					aTManimValueTMP = maya.keyframe(aTManimCurve,q=1,vc=1) #maya
					aTManimTimeTMP = maya.keyframe(aTManimCurve,q=1,tc=1) #maya
					aTManimBreakTMP = maya.keyframe(aTManimCurve,q=1,bd=1) #maya
					if aTManimBreakTMP and aTMtweenBetweenValue ==2:
						for aTMbreakdown in aTManimBreakTMP:
							aTMindex = aTManimTimeTMP.index(aTMbreakdown)
							aTManimTimeTMP.remove(aTMbreakdown)
							aTManimValueTMP.pop(aTMindex)
					aTManimTimeList = aTManimTimeList + aTManimTimeTMP
					aTManimTimeArray.append(aTManimTimeTMP)
					aTManimKeyPoseArray.append([1] * len(aTManimTimeTMP))
					aTManimValueArray.append(aTManimValueTMP)
			aTManimTimeGlobalArray = sorted(set(aTManimTimeList))		
			aTMactionTime = aTMcurrentTime
			aTMlastSelected = aTMcurrSelected
		
			for i in range(0,len(aTManimCurvesArray)):
				if len(aTManimTimeGlobalArray) != len(aTManimTimeArray[i]):
					aTMmissedFramesArray = list(sorted(set(aTManimTimeGlobalArray).difference(set(aTManimTimeArray[i]))))
					for aTMframe in aTMmissedFramesArray:
						aTMindex = aTManimTimeGlobalArray.index(aTMframe)
						aTMposeVarTMP = 0
						if 	aTMframe<aTManimTimeArray[i][0]:
							aTMprevFrameTMP = aTMframe
							aTMprevVarTMP = aTManimValueArray[i][aTMindex]
							aTMposeVarTMP = 2
						else:
							aTMprevFrameTMP = aTManimTimeArray[i][aTMindex-1]
							aTMprevVarTMP = aTManimValueArray[i][aTMindex-1]
						if 	aTMindex==len(aTManimTimeArray[i]):
							aTMnextFrameTMP = aTMframe
							aTMnextVarTMP = aTManimValueArray[i][aTMindex-1]
						else:
							aTMnextFrameTMP = aTManimTimeArray[i][aTMindex]
							aTMnextVarTMP = aTManimValueArray[i][aTMindex]
						if aTMindex==len(aTManimTimeGlobalArray)-1: aTMposeVarTMP = 2
						aTManimValueArray[i].insert(aTMindex,((aTMnextVarTMP-aTMprevVarTMP)/(aTMnextFrameTMP-aTMprevFrameTMP) * (aTMframe-aTMprevFrameTMP) + aTMprevVarTMP))
						aTManimTimeArray[i].insert(aTMindex,aTMframe)
						aTManimKeyPoseArray[i].insert(aTMindex,aTMposeVarTMP)
#matematyka srednia
				for a in range(0,len(aTManimTimeGlobalArray)):
					if aTManimTimeGlobalArray[a] <= aTMactionTime <= aTManimTimeGlobalArray[a+1]:
						aTMmaxValArray.append(aTManimValueArray[i][a+1]-aTManimValueArray[i][a])
						aTMminValArray.append(aTManimValueArray[i][a])
		for i in range(0,len(aTManimCurvesArray)):
			aTMkeyPoseValTMP = maya.keyframe(aTManimCurvesArray[i],q=1,t=(aTMcurrentTime,aTMcurrentTime),ev=1)
			if aTMkeyPoseValTMP[0]!=aTMminValArray[i] and aTMcurrSelected:
				aTMpercentArray.append(abs((aTMkeyPoseValTMP[0]-aTMminValArray[i])*100/aTMmaxValArray[i]))
		try:
			maya.floatSliderGrp('aTMmainFloatSliderGrp',e=1,v=(sum(aTMpercentArray)/len(aTMpercentArray)))
		except:
			pass
	else:
		maya.floatSliderGrp('aTMmainFloatSliderGrp',e=1,v=0)
		aTMlastSelected = []
