#########################################################################################################################
# Arc Tracker For Maya 2012 - Not supported
# Spencer Jones, www.spence-animator.co.uk. All Rights Reserved
#
# TO INSTALL:
# Place the arctrackerfree.py or arctrackerpro.py script in the scripts directory & run the relative python commands below:
# import arctrackerpro2012; reload(arctrackerpro2012)
#
# TIP: Adjust the variables under '# CUSTOMISE DEFAULT SETTINGS #' to create custom default settings for Arc Tracker Pro (File may be read only)

# HOTKEY COMMANDS:
# FOR CREATING TRAILS (ON SELECED) USE THE FOLLOWING COMMAND: from arctrackerpro import arctrackerpro2012; arctrackerpro2012().HOTKEYCOMMANDCREATETRAILS()
# FOR REMOVING TRAILS (ALL TRAILS) USE THE FOLLOWING COMMAND: from arctrackerpro import arctrackerpro2012; arctrackerpro2012().HOTKEYCOMMANDREMOVETRAILS() 

#########################################################################################################################

import maya.cmds as mc
import maya.mel as mm
import random as rand
import maya.OpenMaya as OpenMaya
import sys
import os
import colorsys
from functools import partial

class arctrackerpro2012(object):

	def __init__(self):
	
		# CUSTOMISE DEFAULT SETTINGS ##############################################################################
		
		# TRAILS
		
		#	RANDOM COLOURS
		self.settingRandomColour = True
		self.settingRandomTrailColourHueRange = [0.0, 1.0] #0.0-1.0
		self.settingRandomTrailColourSaturationRange = [0.5, 0.5] #0.0-1.0
		self.settingRandomTrailColourValueRange = [0.8, 0.8] #0.0-1.0
		
		#	SET FRAMES & KEYFRAMES COLOUR RELATIVE TO TRAILS RANDOM COLOUR
		self.settingRandomTrailMatchFramesHueToTrailHue = True
		self.settingRandomTrailColourTrailValRange = [0.4, 0.6] #0.0-1.0
		self.settingRandomTrailColourFrameValRange = [0.7, 0.7] #0.0-1.0
		self.settingRandomTrailColourKeyframeValRange = [0.8, 0.8] #0.0-1.0
		self.settingRandomTrailColourTrailSatRange = [0.4, 0.6] #0.0-1.0
		self.settingRandomTrailColourFrameSatRange = [0.3, 0.3] #0.0-1.0
		self.settingRandomTrailColourKeyframeSatRange = [0.2, 0.2] #0.0-1.0
		
		#	HARD CODED COLOURS (IF RANDOM COLOURS = FALSE)
		self.settingTrailColour = [0.80000001192092896, 0.40000000596046448, 0.69599992036819458]
		self.settingKeyframesColour = [0.40000000596046448, 0.47210749983787537, 0.80000001192092896]
		self.settingFramesColour = [0.57930880784988403, 0.80000001192092896, 0.40000000596046448]
		
		#	MATCH COLOURS TO (SHAPE OR TRANSFORM DRAWING OVERRIDES)
		self.settingAlwaysMatchColoursTo = 'None' #None, Transform, Shape
		self.adjustTrailSaturationValue = True
		self.adjustFrameSaturationValue = True
		self.adjustKeyframeSaturationValue = True
		self.settingMatchHueToShapeNodeHue_TrailSaturation = 0.5 #0.0-1.0
		self.settingMatchHueToShapeNodeHue_FrameSaturation = 0.2 #0.0-1.0
		self.settingMatchHueToShapeNodeHue_KeyframeValue = 0.9 #0.0-1.0
		self.settingMatchHueToShapeNodeHue_TrailValue = 0.7 #0.0-1.0
		self.settingMatchHueToShapeNodeHue_FrameValue = 0.8 #0.0-1.0
		self.settingMatchHueToShapeNodeHue_KeyframeSaturation = 0.1 #0.0-1.0
		
		#
		self.editabletrails = True
		self.autoupdatetype = 'always' #demand(most efficient), animCurve(efficient), always(least efficient) 
		self.settingActiveKeyframeColour = [1,1,0.25] # DEFAULT MAYA:[1,1,0]
		self.settingExtraKeyframeColour = [0.451,0.451,0.451] # DEFAULT MAYA:[0.451,0.451,0.451]
		self.settingBeadColour = [.8,0.4,0.779] # DEFAULT MAYA:[1,0,1]
		self.settingKeyframes = True
		self.settingFrames = False
		self.settingKeyframeNumbers = False
		self.settingFrameNumbers = False
		self.settingLocked = False
		self.settingXrayDraw = True
		self.settingPinned = True
		self.settingPreFrame = 0
		self.settingPostFrame = 0
		self.settingKeyframeSize = 1.0
		self.settingFrameSize = 1.0
		self.settingThickness = 1.0
		self.settingIncrement = 1.0
		self.settingExtraKeyframes = True
		self.settingInBead = False
		self.settingOutBead = False
		self.settingInTangent = False
		self.settingOutTangent = False
		self.settingModifyKeys = False
		self.selectObjectsUsingListBox = False
		
		# OLD SCHOOL TRAILS
		self.enableOldSchoolTrails = False
		self.oldSchoolTrail = True
		self.oldSchoolFrames = True
		self.oldSchoolKeyframes = True
		self.oldSchoolLocked = False
		self.oldSchoolThorough = True
		self.oldSchoolFrameSize = 0.05
		self.oldSchoolKeyframeSize = 0.05
		self.oldSchoolTrailColour = 16 # 1-20
		self.oldSchoolFrameColour = 19 # 1-20
		self.oldSchoolKeyframeColour = 17 # 1-20
		self.oldSchoolRelativeTo = False
		
		# WINDOW
		self.windowHeight = 214
		self.windowWidth = 264
		self.windowMaxHeight = 800
		self.allowCollapsingWhenDocked = False
		
		#OLD MAYA VERSION (IF USING MAYA 2012, 1=True, 0=False)
		self.oldversion = 1
		
		# END CUSTOMISE DEFAULT SETTINGS ##############################################################################
		self.freeorpro = 'Pro'
		self.name = 'ArcTracker'+self.freeorpro
		self.version = '2012(Not supported)'
		self.mayaVersion = mc.about(version=True)
		self.supportedMayaVersion = '2012'
		self.title = 'ATP'+self.version
		self.credit = 'Arc Tracker Pro | Spencer Jones | www.spence-animator.co.uk'
		self.check = self.credit
		self.window = self.name+'Window'
		self.dockname = self.name+'Dock'
		self.trackname = self.name+'Trail'
		self.filename = self.name+self.version+'Record'
		self.filepath = mc.internalVar(userScriptDir=True)
		self.fullfilepath = self.filepath+self.filename+'.txt'
		self.scrollBarThickness = 10
		self.textScrollLayoutLineHeight = 14
		self.textScrollLayoutLineHeightMin = 50
		self.textScrollLayoutLineHeightMax = 250
		separatorheight = 10
		separatorstyle = 'in'
		buttonwidth = 250
		buttonheight01 = 25
		buttonheight02 = 20
		fieldwidth = 75
		rowspacing = 0
		rowmargin = 2
		rowwidth = buttonwidth -(rowmargin*4)
		columnwidth01 = (rowwidth/100.0)*25.0
		columnwidth02 = (rowwidth/100.0)*25.0
		columnwidth03 = (rowwidth/100.0)*45.0
		columnwidth04 = 0
		columnwidth05 = (rowwidth/100.0)*25.0
		columnwidth06 = (rowwidth/100.0)*70.0
		columnwidth07 = (rowwidth/100.0)*45.0
		collapseboolean = 1
		
		#CHECK MAYA VERSION !! CHECK HAS ISSUES WITH MAYA 2014 ON LINUX - AUTODESK ISSUE
		#if self.mayaVersion < self.supportedMayaVersion: self.ATERROR('MAYA VERSION NOT SUPPORTED') 

		#CHECK IF DOCKED WINDOW EXISTS
		if mc.dockControl(self.dockname, q=True, ex=True) == 1: mc.deleteUI(self.dockname)

		#CHECK IF WINDOW EXISTS, CREATE WINDOW
		if (mc.window(self.window, q=True, exists=True)) != True:
			
			self.window = mc.window(self.window, title=self.title, ret=True, rtf=1, s=1 )
			
			#LIST
			mc.scrollLayout(self.name+'ScrollLayout',  horizontalScrollBarThickness=self.scrollBarThickness, verticalScrollBarThickness=self.scrollBarThickness)
			mc.columnLayout(self.name+'mainColumnLayout', co=('both', rowmargin), rs=rowspacing, adj=1 )
			mc.rowColumnLayout(nc=3, w=buttonwidth)
			mc.button( l='Add Objects', c=self.ADDTOLIST, h=buttonheight01, w=buttonwidth-50)
			mc.button( l='- #', c=self.REMOVEFROMLIST, h=buttonheight01, w=24)
			mc.button( l='-', c=self.REMOVEALLFROMLIST, h=buttonheight01, w=24)
			mc.setParent( '..' )
			textlist = mc.textScrollList(self.name+'TextScrollList', h=self.textScrollLayoutLineHeightMin, bgc=[0.365, 0.365, 0.365], w=buttonwidth, ams=1, sc=self.UPDATEUI)
			mc.rowColumnLayout(nc=3, w=buttonwidth)
			mc.button( l='Create Trail', c=self.CREATETRAIL, h=buttonheight01, w=buttonwidth-50)
			mc.button( l='- #', c=self.REMOVETRAIL, h=buttonheight01, w=24)
			mc.button( l='-', c=self.REMOVETRAILS, h=buttonheight01, w=24)
			mc.setParent( '..' )
			
			#PAN ZOOM ACTIVE CAMERA
			mc.frameLayout(self.name+'FrameLayout01', cl=collapseboolean, cll=1, fn='plainLabelFont', mh=5, l='Pan Zoom Active Camera', bs='etchedOut', w=buttonwidth, cc=self.WRITEFILE, ec=self.WRITEFILE)
			mc.columnLayout( co=('both', rowmargin), rs=rowspacing )
			roxColumnNumber = 7
			mc.rowColumnLayout(nc=roxColumnNumber, w=rowwidth)
			mc.button( l='-', c=self.CAMZOOMOUT, h=buttonheight02, w=rowwidth/roxColumnNumber)
			mc.button( l='<', c=self.CAMLEFT, h=buttonheight02, w=rowwidth/roxColumnNumber)
			mc.button( l='v', c=self.CAMDOWN, h=buttonheight02, w=rowwidth/roxColumnNumber)
			mc.button( l='^', c=self.CAMUP, h=buttonheight02, w=rowwidth/roxColumnNumber)
			mc.button( l='>', c=self.CAMRIGHT, h=buttonheight02, w=rowwidth/roxColumnNumber)
			mc.button( l='+', c=self.CAMZOOMIN, h=buttonheight02, w=rowwidth/roxColumnNumber)
			mc.button( l='R', c=self.CAMRESET, h=buttonheight02, w=rowwidth/roxColumnNumber)
			mc.setParent( '..' )
			mc.floatSliderGrp( self.name+'ZoomSlider01', l='Z', en=1, f=1, min=0.001, max=1, fmn=0.001, fmx=1, v=1, s=1, pre=3, cw=((1, 10),(2,0),(3,rowwidth-15)), cc=self.CAMZOOM)
			mc.floatSliderGrp( self.name+'ZoomSlider02', l='V', en=1, f=1, min=-1, max=1, fmn=-1, fmx=1, v=0, s=1, pre=3, cw=((1, 10),(2,0),(3,rowwidth-15)), cc=self.CAMZOOM)
			mc.floatSliderGrp( self.name+'ZoomSlider03', l='H', en=1, f=1, min=-1, max=1, fmn=-1, fmx=1, v=0, s=1, pre=3, cw=((1, 10),(2,0),(3,rowwidth-15)), cc=self.CAMZOOM)
			mc.setParent( '..' ) # END COLUMN LAYOUT
			mc.setParent( '..' ) # END SCROLL LAYOUT
			
			#TRAIL TIME
			mc.frameLayout(self.name+'FrameLayout02', cl=collapseboolean, cll=1, fn='plainLabelFont', mh=5, l='Trail Time Range', bs='etchedOut', w=buttonwidth, cc=self.WRITEFILE, ec=self.WRITEFILE)
			mc.columnLayout( co=('both', rowmargin), rs=rowspacing )
			mc.checkBox(self.name+'TimeCheckbox01', l='Override Range Slider', al='left', v=0, en=1, w=buttonwidth, cc=self.TIMESWITCH)
			roxColumnNumber = 5
			mc.rowColumnLayout(nc=roxColumnNumber, w=rowwidth)
			mc.floatField(self.name+'TimeFloatField01', v=0, en=0, pre=0, w=(rowwidth/2)-37, cc=self.UPDATETRAIL )
			mc.button(self.name+'TimeButton01',  l='<', c=self.INPUTSTART, h=buttonheight02, w=24)
			mc.floatField(self.name+'TimeFloatField02', v=200, en=0, pre=0, w=(rowwidth/2)-37, cc=self.UPDATETRAIL )
			mc.button(self.name+'TimeButton02', l='<', c=self.INPUTEND, h=buttonheight02, w=24)
			mc.button(self.name+'TimeButton03', l='R', c=self.INPUTRANGE, h=buttonheight02, w=24)
			mc.setParent( '..' )
			mc.setParent( '..' ) # END COLUMN LAYOUT
			mc.setParent( '..' ) # END SCROLL LAYOUT
			
			#TRAIL DISPLAY
			mc.frameLayout(self.name+'FrameLayout03', cl=collapseboolean, cll=1, fn='plainLabelFont', mh=5, l='Trail Display', bs='etchedOut', w=buttonwidth, cc=self.WRITEFILE, ec=self.WRITEFILE)
			mc.columnLayout( co=('both', rowmargin), rs=rowspacing )
			
			if self.settingRandomColour == True:
				if self.settingRandomTrailMatchFramesHueToTrailHue == True:
					hueMatch = rand.uniform(self.settingRandomTrailColourHueRange[0], self.settingRandomTrailColourHueRange[1])
					
					satMatch = rand.uniform(self.settingRandomTrailColourTrailSatRange[0], self.settingRandomTrailColourTrailSatRange[1])
					valMatch = rand.uniform(self.settingRandomTrailColourTrailValRange[0], self.settingRandomTrailColourTrailValRange[1])
					attrailrgb = self.GENCOLOUR (1, hueMatch, satMatch, valMatch)
					
					satMatch = rand.uniform(self.settingRandomTrailColourKeyframeSatRange[0], self.settingRandomTrailColourKeyframeSatRange[1])
					valMatch = rand.uniform(self.settingRandomTrailColourKeyframeValRange[0], self.settingRandomTrailColourKeyframeValRange[1])
					atkeyframergb = self.GENCOLOUR (1, hueMatch, satMatch, valMatch)
					
					satMatch = rand.uniform(self.settingRandomTrailColourFrameSatRange[0], self.settingRandomTrailColourFrameSatRange[1])
					valMatch = rand.uniform(self.settingRandomTrailColourFrameValRange[0], self.settingRandomTrailColourFrameValRange[1])
					atframergb = self.GENCOLOUR (1, hueMatch, satMatch, valMatch)
					
				else:
					attrailrgb = self.GENCOLOUR()
					atkeyframergb = self.GENCOLOUR()
					atframergb = self.GENCOLOUR()					
			else:
				attrailrgb = self.settingTrailColour
				atkeyframergb = self.settingKeyframesColour
				atframergb = self.settingFramesColour
			
			mc.colorSliderGrp(self.name+'DisplayColbox01', cal=[1,'left'], l=' Trail', rgb=attrailrgb, cw=((1, columnwidth05),(2,columnwidth06-30),(3,columnwidth04)), cc=partial(self.UPDATETRAILPART, 'trailColor'))
			mc.floatSliderGrp( self.name+'DisplaySlider02', cal=[1,'left'], l='', en=1, f=1, min=0.001, max=5, fmn=0.001, fmx=5, v=self.settingThickness, s=0.001, pre=3, cw=((1, columnwidth04),(2,columnwidth05),(3,columnwidth06)), cc=partial(self.UPDATETRAILPART, 'trailThickness'))
			
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			roxColumnNumber = 3
			mc.rowColumnLayout(nc=roxColumnNumber, w=buttonwidth)
			mc.colorSliderGrp(self.name+'DisplayColbox02', cal=[1,'left'], l=' Keyframes', rgb=atkeyframergb, cw=((1, columnwidth05),(2,columnwidth06-30),(3,columnwidth04)), cc=partial(self.UPDATETRAILPART, 'keyframeColor'))
			mc.checkBox(self.name+'DisplayCheckbox02', l='', v=self.settingKeyframes, en=1, w=15, cc=partial(self.UPDATETRAILPART, 'keyframeSize'))
			mc.checkBox(self.name+'DisplayCheckbox03', l='', v=self.settingKeyframeNumbers, en=1, w=15, cc=partial(self.UPDATETRAILPART, 'showFrames'))
			mc.setParent( '..' )
			mc.floatSliderGrp( self.name+'DisplaySlider01', cal=[1,'left'], l='', en=1, f=1, min=0.001, max=5, fmn=0.001, fmx=1000, v=self.settingKeyframeSize, s=0.001, pre=3, cw=((1, columnwidth04),(2,columnwidth05),(3,columnwidth06)), cc=partial(self.UPDATETRAILPART, 'keyframeSize'))
			
			'''
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			roxColumnNumber = 3
			mc.rowColumnLayout(nc=roxColumnNumber, w=buttonwidth)
			mc.colorSliderGrp(self.name+'DisplayColbox03', cal=[1,'left'], l=' Frames', rgb=atframergb, cw=((1, columnwidth05),(2,columnwidth06-30),(3,columnwidth04)), cc=partial(self.UPDATETRAILPART, 'frameMarkerColor'))
			mc.checkBox(self.name+'DisplayCheckbox04', l='', al='left', v=self.settingFrames, en=1, w=15, cc=partial(self.UPDATETRAILPART, 'showFrames'))
			mc.checkBox(self.name+'DisplayCheckbox05', l='', al='left', v=self.settingFrameNumbers, w=15, cc=partial(self.UPDATETRAILPART, 'showFrameMarkerFrames'))
			mc.setParent( '..' )
			mc.floatSliderGrp( self.name+'DisplaySlider05', cal=[1,'left'], l='', en=1, f=1, min=0.001, max=5, fmn=0.001, fmx=1000, v=self.settingFrameSize, s=0.001, pre=3, cw=((1, columnwidth04),(2,columnwidth05),(3,columnwidth06)), cc=partial(self.UPDATETRAILPART, 'frameMarkerSize'))
			'''
			
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			mc.floatSliderGrp( self.name+'DisplaySlider03', cal=[1,'left'], l=' Pre Frame', en=1, f=1, min=0, max=10, fmn=0, fmx=100, v=self.settingPreFrame, s=1, pre=0, cw=((1, columnwidth01),(2,columnwidth02),(3,columnwidth03)), cc=partial(self.UPDATETRAILPART, 'preFrame'))
			mc.floatSliderGrp( self.name+'DisplaySlider04', cal=[1,'left'], l=' Post Frame', en=1, f=1, min=0, max=10, fmn=0, fmx=100, v=self.settingPostFrame, s=1, pre=0, cw=((1, columnwidth01),(2,columnwidth02),(3,columnwidth03)), cc=partial(self.UPDATETRAILPART, 'postFrame'))
			mc.floatSliderGrp( self.name+'OptionsSlider01', cal=[1,'left'], l=' Increment', en=1, f=1, min=0.25, max=1, fmn=0.25, fmx=100, v=self.settingIncrement, s=0.01, pre=3, cw=((1, columnwidth01),(2,columnwidth02),(3,columnwidth03)), cc=partial(self.UPDATETRAILPART, 'increment'))
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			roxColumnNumber = 2
			mc.rowColumnLayout(nc=roxColumnNumber, w=buttonwidth)
			mc.checkBox(self.name+'OptionsCheckbox01', l='Locked', al='left', v=self.settingLocked, w=rowwidth/roxColumnNumber, cc=partial(self.UPDATETRAILPART, 'locked'))
			mc.checkBox(self.name+'OptionsCheckbox03', l='Pinned', al='left', v=self.settingPinned, w=rowwidth/roxColumnNumber, cc=partial(self.UPDATETRAILPART, 'pinned'))
			mc.checkBox(self.name+'OptionsCheckbox02', l='Xray Draw', al='left', v=self.settingXrayDraw, w=rowwidth/roxColumnNumber, cc=partial(self.UPDATETRAILPART, 'xrayDraw'))
			mc.checkBox(self.name+'MoreOptionsCheckbox07', l='Modify Keys', al='left', v=self.settingModifyKeys, en=1, w=rowwidth/roxColumnNumber, cc=partial(self.UPDATETRAILPART, 'modifyKeys'), onc=self.MODIFYKEYSON)
			mc.checkBox(self.name+'MoreOptionsCheckbox05', l='In Tangent', al='left', v=self.settingInTangent, en=1, w=rowwidth/roxColumnNumber, cc=partial(self.UPDATETRAILPART, 'showInTangent'), onc=self.INOUTTANON)
			mc.checkBox(self.name+'MoreOptionsCheckbox06', l='Out Tangent', al='left', v=self.settingOutTangent, en=1, w=rowwidth/roxColumnNumber, cc=partial(self.UPDATETRAILPART, 'showOutTangent'), onc=self.INOUTTANON)
			mc.checkBox(self.name+'MoreOptionsCheckbox04', l='In Bead', al='left', v=self.settingOutBead, en=1, w=rowwidth/roxColumnNumber, cc=partial(self.UPDATETRAILPART, 'showInBead'), onc=self.INBEADON)
			mc.checkBox(self.name+'MoreOptionsCheckbox03', l='Out Bead', al='left', v=self.settingInBead, en=1, w=rowwidth/roxColumnNumber, cc=partial(self.UPDATETRAILPART, 'showOutBead'), onc=self.OUTBEADON)
			mc.setParent( '..' )
			
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			mc.colorSliderGrp(self.name+'MoreOptionsColbox01', cal=[1,'left'], l=' Active', rgb=self.settingActiveKeyframeColour, cw=((1, columnwidth05),(2,columnwidth06-30),(3,columnwidth04)), cc=partial(self.UPDATETRAILPART, 'activeKeyframeColor'))
			mc.colorSliderGrp(self.name+'MoreOptionsColbox03', cal=[1,'left'], l=' Bead', rgb=self.settingBeadColour, cw=((1, columnwidth05),(2,columnwidth06-30),(3,columnwidth04)), cc=partial(self.UPDATETRAILPART, 'beadColor'))
			roxColumnNumber = 3
			mc.rowColumnLayout(nc=roxColumnNumber, w=buttonwidth)
			#mc.colorSliderGrp(self.name+'MoreOptionsColbox02', cal=[1,'left'], l=' Extra', rgb=self.settingExtraKeyframeColour, cw=((1, columnwidth05),(2,columnwidth06-30),(3,columnwidth04)), cc=partial(self.UPDATETRAILPART, 'extraKeyframeColor'))
			#mc.checkBox(self.name+'MoreOptionsCheckbox02', l='', v=0, w=15, cc=partial(self.UPDATETRAILPART, 'showExtraKeys'))
			mc.setParent( '..' )
			
			mc.setParent( '..' ) # END COLUMN LAYOUT
			mc.setParent( '..' ) # END SCROLL LAYOUT
			
			#OLD SCHOOL OPTIONS
			mc.frameLayout(self.name+'FrameLayout05', cl=collapseboolean, cll=1, fn='plainLabelFont', mh=5, l='Old School Trails', bs='etchedOut', w=buttonwidth, cc=self.WRITEFILE, ec=self.WRITEFILE)
			mc.columnLayout( co=('both', rowmargin), rs=rowspacing )
			mc.checkBox(self.name+'OldSchoolCheckbox01', l='Old School Trails', al='left', v=self.enableOldSchoolTrails, en=1, w=buttonwidth, cc=self.WRITEFILE, onc=self.OLDSCHOOLTOGGLE, ofc=self.OLDSCHOOLTOGGLE)
			#mc.checkBox(self.name+'OldSchoolCheckboxUpdate', l='Auto Update', al='left', v=1, en=1, w=buttonwidth)
			mc.checkBox(self.name+'OldSchoolCheckbox03', l='Thorough Old School Trails', al='left', v=self.oldSchoolThorough, en=1, w=buttonwidth)
			mc.checkBox(self.name+'OldSchoolCheckbox02', l='Locked', al='left', v=self.oldSchoolLocked, en=1, w=buttonwidth)
			mc.checkBox(self.name+'OldSchoolCheckbox04', l='Trails', al='left', v=self.oldSchoolTrail, en=1, w=buttonwidth)
			mc.colorIndexSliderGrp( self.name+'OldSchoolSlider01', l='', en=1, v=self.oldSchoolTrailColour, min=1, max=20, cw=((1, columnwidth04),(2,columnwidth05),(3,columnwidth06)))
			mc.checkBox(self.name+'OldSchoolCheckbox05', l='Frames', al='left', v=self.oldSchoolFrames, en=1, w=buttonwidth)
			mc.colorIndexSliderGrp( self.name+'OldSchoolSlider02', l='', en=1, v=self.oldSchoolFrameColour, min=1, max=20, cw=((1, columnwidth04),(2,columnwidth05),(3,columnwidth06)))
			mc.floatSliderGrp( self.name+'OldSchoolDisplaySlider01', cal=[1,'left'], l='', en=1, f=1, min=0.01, max=1, fmn=0.001, fmx=1000, v=self.oldSchoolFrameSize, s=0.001, pre=3, cw=((1, columnwidth04),(2,columnwidth05),(3,columnwidth06)), cc=partial(self.UPDATETRAILPART, 10))
			mc.checkBox(self.name+'OldSchoolCheckbox06', l='Keyframes', al='left', v=self.oldSchoolKeyframes, en=1, w=buttonwidth)
			mc.colorIndexSliderGrp( self.name+'OldSchoolSlider03', l='', en=1, v=self.oldSchoolKeyframeColour, min=1, max=20, cw=((1, columnwidth04),(2,columnwidth05),(3,columnwidth06)))
			mc.floatSliderGrp( self.name+'OldSchoolDisplaySlider02', cal=[1,'left'], l='', en=1, f=1, min=0.01, max=1, fmn=0.001, fmx=1000, v=self.oldSchoolKeyframeSize, s=0.001, pre=3, cw=((1, columnwidth04),(2,columnwidth05),(3,columnwidth06)), cc=partial(self.UPDATETRAILPART, 10))
			mc.optionMenu(self.name+'OldSchoolOptionMenu01', l='', en=True, w=rowwidth)
			axisorder = ['Curves', 'Spheres']; axisorder.sort()
			for x in axisorder: mc.menuItem( l=x)
			
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			roxColumnNumber = 3
			mc.rowColumnLayout(nc=roxColumnNumber, w=rowwidth)
			mc.checkBox(self.name+'OldSchoolCheckbox07', l='Relative To', v=self.oldSchoolRelativeTo, en=1, w=(rowwidth/2)-12, cc=self.WRITEFILE)
			mc.button(self.name+'OldSchoolButton01', l='>', h=buttonheight02, w=24, en=1, c=self.INPUTRELATIVETO)
			mc.textField(self.name+'OldSchoolTextField01', tx='Moving Camera', en=1, w=(rowwidth/2)-12, cc=self.WRITEFILE)
			mc.setParent( '..' )
			
			mc.setParent( '..' ) # END COLUMN LAYOUT
			mc.setParent( '..' ) # END SCROLL LAYOUT
			
			#OPTIONS
			mc.frameLayout(self.name+'FrameLayout04', cl=collapseboolean, cll=1, fn='plainLabelFont', mh=5, l='Options', bs='etchedOut', w=buttonwidth, cc=self.WRITEFILE, ec=self.WRITEFILE)
			mc.columnLayout( co=('both', rowmargin), rs=rowspacing )
			
			mc.checkBox(self.name+'OptionsCheckbox06', l='Editable Trails (Faster Disabled)', al='left', v=self.editabletrails, w=buttonwidth, cc=self.WRITEFILE)
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			
			roxColumnNumber = 2
			mc.rowColumnLayout(nc=roxColumnNumber, w=rowwidth)
			mc.text(label=' Match Trail Colours To', al='left', w=(rowwidth/roxColumnNumber))
			mc.radioCollection('OptionsRadio01')
			mc.radioButton('None', label='None', w=(rowwidth/roxColumnNumber), onc=self.UPDATEUI )
			mc.radioButton('Transform', label='Transform Overrides', w=(rowwidth/roxColumnNumber), onc=self.UPDATEUI )
			mc.radioButton('Shape', label='Shape Overrides', w=(rowwidth/roxColumnNumber), onc=self.UPDATEUI )
			mc.setParent( '..' )
			mc.radioCollection('OptionsRadio01', e=1, sl=self.settingAlwaysMatchColoursTo)
			
			'''
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			mc.button(self.name+'OptionsButton01', l='Open Seetings File', h=buttonheight02, w=rowwidth, en=1, c=self.OPENFILE)
			mc.button(self.name+'OptionsButton02', l='Remove Seetings File', h=buttonheight02, w=rowwidth, en=1, c=self.REMOVEFILE)
			'''
			
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			mc.checkBox(self.name+'OptionsCheckbox04', l='Select Objects Using Arc Tracker', al='left', v=self.selectObjectsUsingListBox, w=buttonwidth, cc=self.WRITEFILE)
			
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			mc.checkBox(self.name+'OptionsCheckbox05', l='Allow Collapsing When Docked', al='left', v=self.allowCollapsingWhenDocked, w=buttonwidth, cc=self.WRITEFILE)
			mc.button(self.name+'DockButton', l='Dock', c=self.DOCK, h=buttonheight01, w=rowwidth)
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			mc.button( l='Toggle Curves', c=self.TOGGLECURVES, h=buttonheight01, w=rowwidth)
			mc.separator( style=separatorstyle, height=separatorheight, width=buttonwidth )
			mc.button( l='Remove All', c=self.REMOVEALL, h=buttonheight01, w=rowwidth)
			
			mc.setParent( '..' ) # END COLUMN LAYOUT
			mc.setParent( '..' ) # END SCROLL LAYOUT

			mc.showWindow( self.window ) # END WINDOW
			
			self.INPUTRANGE()
			self.READFILE()
			self.OLDSCHOOLTOGGLE()
			#self.RESIZEWINDOW()
			self.ATINFO(self.credit)
			
		else:
			mc.showWindow( self.window ) # SHOW WINDOW
			self.ATWARN('WINDOW ALREADY EXISTS')

	def GENCOLOUR (self, m=0, h=1.0, s=0.0, v=[0.0, 1.0], arg=None):
		if m == 0:
			rgb = colorsys.hsv_to_rgb(rand.uniform(self.settingRandomTrailColourHueRange[0], self.settingRandomTrailColourHueRange[1]), rand.uniform(self.settingRandomTrailColourSaturationRange[0], self.settingRandomTrailColourSaturationRange[1]), rand.uniform(self.settingRandomTrailColourSaturationRange[0], self.settingRandomTrailColourSaturationRange[1]))
		else:
			rgb = colorsys.hsv_to_rgb(h, s, v)
		return rgb
	
	def RESIZEWINDOW (self, arg=None):
		resizeHeight = self.windowHeight
		max = self.windowMaxHeight
		if mc.window(self.window, q=1, exists=1) == 1:
			if mc.frameLayout(self.name+'FrameLayout01', q=True, cl=True) == 0:
				resizeHeight = (resizeHeight + mc.frameLayout(self.name+'FrameLayout01', q=True, h=True))-20
			if mc.frameLayout(self.name+'FrameLayout02', q=True, cl=True) == 0:
				resizeHeight = (resizeHeight + mc.frameLayout(self.name+'FrameLayout02', q=True, h=True))-20
			if mc.frameLayout(self.name+'FrameLayout03', q=True, cl=True) == 0:
				resizeHeight = (resizeHeight + mc.frameLayout(self.name+'FrameLayout03', q=True, h=True))-20
			if mc.frameLayout(self.name+'FrameLayout04', q=True, cl=True) == 0:
				resizeHeight = (resizeHeight + mc.frameLayout(self.name+'FrameLayout04', q=True, h=True))-20
			if mc.frameLayout(self.name+'FrameLayout05', q=True, cl=True) == 0:
				resizeHeight = (resizeHeight + mc.frameLayout(self.name+'FrameLayout05', q=True, h=True))-20
			resizeHeight = (resizeHeight + mc.textScrollList(self.name+'TextScrollList', q=True, h=True))-50
			if mc.dockControl(self.dockname, q=1, exists=1) != 1 and resizeHeight > max:
				resizeHeight = max
				mc.window(self.window, e=1, w=self.windowWidth+(self.scrollBarThickness+4), h=resizeHeight)
			elif mc.dockControl(self.dockname, q=1, exists=1) == 1:
				if mc.checkBox(self.name+'OptionsCheckbox05', q=1, v=1) != 1:
					mc.frameLayout(self.name+'FrameLayout01', e=True, cl=0)
					mc.frameLayout(self.name+'FrameLayout02', e=True, cl=0)
					mc.frameLayout(self.name+'FrameLayout03', e=True, cl=0)
					mc.frameLayout(self.name+'FrameLayout04', e=True, cl=0)
					mc.frameLayout(self.name+'FrameLayout05', e=True, cl=0)
					mc.scrollLayout(self.name+'ScrollLayout',  e=1, w=self.windowWidth+(self.scrollBarThickness+6))
			else:
				mc.window(self.window, e=1, w=self.windowWidth, h=resizeHeight)
			if  self.check.count('pen') != 2 : mc.deleteUI(self.window)
			
	def RESIZELIST (self, arg=None):
		amount = mc.textScrollList(self.name+'TextScrollList', q=True, ni=True )
		amount = amount * self.textScrollLayoutLineHeight
		if amount < self.textScrollLayoutLineHeightMin: amount = self.textScrollLayoutLineHeightMin
		if amount > self.textScrollLayoutLineHeightMax: amount = self.textScrollLayoutLineHeightMax
		mc.textScrollList(self.name+'TextScrollList', e=True, h=amount)
		if mc.frameLayout(self.name+'FrameLayout01', q=True, cl=True) == 1:
			mc.frameLayout(self.name+'FrameLayout01', e=True, cl=False)
			mc.frameLayout(self.name+'FrameLayout01', e=True, cl=True)
		else:
			mc.frameLayout(self.name+'FrameLayout01', e=True, cl=True)
			mc.frameLayout(self.name+'FrameLayout01', e=True, cl=False)
		self.RESIZEWINDOW()
	
	def CREATETRAIL (self, arg=None):
	
		currentSelection = mc.ls(sl=True, r=True, l=True)
		
		if mc.checkBox(self.name+'OldSchoolCheckbox01', q=True, v=True) == 1: self.THOROUGHTRAIL()
		else:
			self.REMOVETRAIL()
			#CHECK LIST ISNT EMPTY
			if mc.textScrollList(self.name+'TextScrollList', q=True, nsi=True) != 0:
				listedobjects = mc.textScrollList(self.name+'TextScrollList', q=True, si=True)
				#CHECK SELECTED OBJECT EXISTS BEFORE ADDED TO LIST AKA DAVE VASQUE CHECK
				for i in [i for i in listedobjects if mc.objExists(i) == 1]:
					shortname = mc.ls(i, r=True, sn=True)[0]
					longname = mc.ls(i, r=True, l=True)[0]
					newname = shortname.replace('|', '_')
					motiontrail = mc.snapshot(longname, n=newname+self.trackname, motionTrail=1, increment=1, startTime=mc.playbackOptions(q=True, min=True), endTime=mc.playbackOptions(q=True, max=True), ch=mc.checkBox(self.name+'OptionsCheckbox06', q=1, v=1), u=self.autoupdatetype)
					mc.group(motiontrail[0], n=newname+self.trackname+'Group')
					mc.select(cl=1)
					#UNLIMITED KEYFRAME, FRAMEMARKER SIZE - AKA MATT BUGEJA FIX
					attributes = ['atKeyframeSize', 'atFrameMarkerSize', 'atTrailThickness']
					for a in attributes: mc.addAttr(newname+self.trackname+'Handle', ln=a, at='float', dv=1, k=1)
					mc.connectAttr(newname+self.trackname+'Handle'+'.'+attributes[0], newname+self.trackname+'Handle'+'.keyframeSize')
					#mc.connectAttr(newname+self.trackname+'Handle'+'.'+attributes[1], newname+self.trackname+'Handle'+'.frameMarkerSize')
					mc.connectAttr(newname+self.trackname+'Handle'+'.'+attributes[2], newname+self.trackname+'Handle'+'.trailThickness')
					
					self.UPDATETRAIL()
			else: self.ATERROR('NO OBJECTS IN ARCTRACKER LIST BOX')
		
		if len(currentSelection) > 0: mc.select(currentSelection, r=1)
		
	def UPDATETRAIL (self, arg=None):
	
		#if mc.checkBox(self.name+'OldSchoolCheckbox01', q=1, v=1) == 1: self.CREATETRAIL()
		self.UPDATETRAILPART('all')
	
	def UPDATETRAILPART (self, valid, arg=None):
	
		if mc.checkBox(self.name+'OldSchoolCheckbox01', q=1, v=1) == 0:
		
			#CHECK LIST ISNT EMPTY
			if mc.textScrollList(self.name+'TextScrollList', q=True, nsi=True) != 0:
				listedobjects = mc.textScrollList(self.name+'TextScrollList', q=True, si=True)
				for i in [i for i in listedobjects if mc.objExists(i) == 1]:
					shortname = mc.ls(i, r=True, sn=True)[0]
					longname = mc.ls(i, r=True, l=True)[0]
					newname = shortname.replace('|', '_')
					listedobject = newname
					
					if mc.objExists(listedobject+self.trackname+'Handle') ==1:
						
						if mc.radioCollection('OptionsRadio01', q=1, sl=1) != 'None': 
							if mc.radioCollection('OptionsRadio01', q=1, sl=1) == 'Shape': index = mc.getAttr(mc.listRelatives(i, shapes=1)[0]+'.overrideColor')
							else: index = mc.getAttr(i+'.overrideColor')
							
							colourArray = [[0.471, 0.471, 0.471], [0, 0, 0], [0.251, 0.251, 0.251], [0.502, 0.502, 0.502], [0.608, 0, 0.157], [0, 0.16, 0.376], [0, 0, 1], [0, 0.275, 0.098], [0.14902, 0, 0.262745], [0.784314, 0, 0.784314], [0.541176, 0.282353, 0.2], [0.247059, 0.137255, 0.121569], [0.6, 0.14902, 0], [1, 0, 0], [0, 1, 0], [0, 0.254902, 0.6], [1, 1, 1], [1, 1, 0], [0.392157, 0.862745, 1], [0.262745, 1, 0.639216], [1, 0.690196, 0.690196], [0.894118, 0.67451, 0.47451], [1, 1, 0.388235], [0, 0.6, 0.329412], [0.631373, 0.411765, 0.188235], [0.623529, 0.631373, 0.188235], [0.407843, 0.631373, 0.188235], [0.188235, 0.631373, 0.364706], [0.188235, 0.631373, 0.631373], [0.188235, 0.403922, 0.631373], [0.435294, 0.188235, 0.631373]]
							origcolour = colourArray[index]
							
							colour = origcolour
							if self.adjustTrailSaturationValue == True:
								colour = colorsys.rgb_to_hsv(colour[0], colour[1], colour[2])
								colour = [colour[0], colour[1], colour[2]]
								colour = colorsys.hsv_to_rgb(colour[0], colour[1], colour[2])
							mc.colorSliderGrp(self.name+'DisplayColbox01', e=True, rgb=colour)
							
							colour = origcolour
							if self.adjustFrameSaturationValue == True:
								colour = colorsys.rgb_to_hsv(colour[0], colour[1], colour[2])
								colour = [colour[0], self.settingMatchHueToShapeNodeHue_KeyframeSaturation, self.settingMatchHueToShapeNodeHue_KeyframeValue]
								colour = colorsys.hsv_to_rgb(colour[0], colour[1], colour[2])
							mc.colorSliderGrp(self.name+'DisplayColbox02', e=True, rgb=colour)
							
							'''
							colour = origcolour
							if self.adjustKeyframeSaturationValue == True:
								colour = colorsys.rgb_to_hsv(colour[0], colour[1], colour[2])
								colour = [colour[0], self.settingMatchHueToShapeNodeHue_FrameSaturation, self.settingMatchHueToShapeNodeHue_FrameValue]
								colour = colorsys.hsv_to_rgb(colour[0], colour[1], colour[2])
							mc.colorSliderGrp(self.name+'DisplayColbox03', e=True, rgb=colour)
							'''
							
						if valid == 'all' or valid == 'trailColor':
							rgb = mc.colorSliderGrp(self.name+'DisplayColbox01', q=True, rgb=True)
							mc.setAttr(listedobject+self.trackname+'Handle'+'.trailColor', rgb[0], rgb[1], rgb[2], type='double3')
						if valid == 'all' or valid == 'keyframeColor':
							rgb = mc.colorSliderGrp(self.name+'DisplayColbox02', q=True, rgb=True)
							mc.setAttr(listedobject+self.trackname+'Handle'+'.keyframeColor', rgb[0], rgb[1], rgb[2], type='double3')
						'''
						if valid == 'all' or valid == 'frameMarkerColor':
							rgb = mc.colorSliderGrp(self.name+'DisplayColbox03', q=True, rgb=True)
							mc.setAttr(listedobject+self.trackname+'Handle'+'.frameMarkerColor', rgb[0], rgb[1], rgb[2], type='double3')
						'''
						if valid == 'all' or valid == 'activeKeyframeColor':
							rgb = mc.colorSliderGrp(self.name+'MoreOptionsColbox01', q=True, rgb=True)		
							mc.setAttr(listedobject+self.trackname+'Handle'+'.activeKeyframeColor', rgb[0], rgb[1], rgb[2], type='double3')
						'''
						if valid == 'all' or valid == 'extraKeyframeColor':
							rgb = mc.colorSliderGrp(self.name+'MoreOptionsColbox02', q=True, rgb=True)				
							mc.setAttr(listedobject+self.trackname+'Handle'+'.extraKeyframeColor', rgb[0], rgb[1], rgb[2], type='double3')
						'''
						if valid == 'all' or valid == 'beadColor':
							rgb = mc.colorSliderGrp(self.name+'MoreOptionsColbox03', q=True, rgb=True)
							mc.setAttr(listedobject+self.trackname+'Handle'+'.beadColor', rgb[0], rgb[1], rgb[2], type='double3')
						
						if valid == 'all' or valid == 'keyframeSize':
							if mc.checkBox(self.name+'DisplayCheckbox02', q=True, v=True) == 1: mc.setAttr(listedobject+self.trackname+'Handle'+'.atKeyframeSize', mc.floatSliderGrp( self.name+'DisplaySlider01', q=True, v=True))
							else: mc.setAttr(listedobject+self.trackname+'Handle'+'.atKeyframeSize', 0.1)
							
						if valid == 'all' or valid == 'showFrames': mc.setAttr(listedobject+self.trackname+'Handle'+'.showFrames', mc.checkBox(self.name+'DisplayCheckbox03', q=True, v=True))
						#if valid == 'all' or valid == 'showFrames': mc.setAttr(listedobject+self.trackname+'Handle'+'.showFrames', mc.checkBox(self.name+'DisplayCheckbox04', q=True, v=True))
						#if valid == 'all' or valid == 'showFrameMarkerFrames': mc.setAttr(listedobject+self.trackname+'Handle'+'.showFrameMarkerFrames', mc.checkBox(self.name+'DisplayCheckbox05', q=True, v=True))
						#if valid == 'all' or valid == 'frameMarkerSize': mc.setAttr(listedobject+self.trackname+'Handle'+'.atFrameMarkerSize', mc.floatSliderGrp( self.name+'DisplaySlider05', q=True, v=True))
						if valid == 'all' or valid == 'trailThickness': mc.setAttr(listedobject+self.trackname+'Handle'+'.atTrailThickness', mc.floatSliderGrp( self.name+'DisplaySlider02', q=True, v=True))
						if valid == 'all' or valid == 'pinned': mc.setAttr(listedobject+self.trackname+'Handle'+'.pinned', mc.checkBox(self.name+'OptionsCheckbox03', q=True, v=True))
						if valid == 'all' or valid == 'xrayDraw': mc.setAttr(listedobject+self.trackname+'Handle'+'.xrayDraw', mc.checkBox(self.name+'OptionsCheckbox02', q=True, v=True))
						if valid == 'all' or valid == 'preFrame': mc.setAttr(listedobject+self.trackname+'Handle'+'.preFrame', mc.floatSliderGrp( self.name+'DisplaySlider03', q=True, v=True))
						if valid == 'all' or valid == 'postFrame': mc.setAttr(listedobject+self.trackname+'Handle'+'.postFrame', mc.floatSliderGrp( self.name+'DisplaySlider04', q=True, v=True))
						#if valid == 'all' or valid == 'showExtraKeys': mc.setAttr(listedobject+self.trackname+'Handle'+'.showExtraKeys', mc.checkBox(self.name+'MoreOptionsCheckbox02', q=True, v=True))
						if valid == 'all' or valid == 'showOutBead': mc.setAttr(listedobject+self.trackname+'Handle'+'.showOutBead', mc.checkBox(self.name+'MoreOptionsCheckbox03', q=True, v=True))
						if valid == 'all' or valid == 'showInBead': mc.setAttr(listedobject+self.trackname+'Handle'+'.showInBead', mc.checkBox(self.name+'MoreOptionsCheckbox04', q=True, v=True))
						if valid == 'all' or valid == 'showInTangent': mc.setAttr(listedobject+self.trackname+'Handle'+'.showInTangent', mc.checkBox(self.name+'MoreOptionsCheckbox05', q=True, v=True))
						if valid == 'all' or valid == 'showOutTangent': mc.setAttr(listedobject+self.trackname+'Handle'+'.showOutTangent', mc.checkBox(self.name+'MoreOptionsCheckbox06', q=True, v=True))
						if valid == 'all' or valid == 'modifyKeys': mc.setAttr(listedobject+self.trackname+'Handle'+'.modifyKeys', mc.checkBox(self.name+'MoreOptionsCheckbox07', q=True, v=True))
						
						#IF AUTO UPDATE TRAILS ON
						if mc.checkBox(self.name+'OptionsCheckbox06', q=1, v=1) == 1:
							if valid == 'all' or valid == 'increment': mc.setAttr(listedobject+self.trackname+'.increment', mc.floatSliderGrp(self.name+'OptionsSlider01', q=True, v=True))
							if valid == 'all' or valid == 'time':
								if mc.checkBox(self.name+'TimeCheckbox01', q=True, v=True) == 0:
									mc.setAttr(listedobject+self.trackname+'.startTime', mc.playbackOptions(q=True, min=True))
									mc.setAttr(listedobject+self.trackname+'.endTime', mc.playbackOptions(q=True, max=True))
								else:
									if mc.floatField(self.name+'TimeFloatField01', q=True, v=True) < mc.floatField(self.name+'TimeFloatField02', q=True, v=True):
										mc.setAttr(listedobject+self.trackname+'.startTime', mc.floatField(self.name+'TimeFloatField01', q=True, v=True))
										mc.setAttr(listedobject+self.trackname+'.endTime', mc.floatField(self.name+'TimeFloatField02', q=True, v=True))
									else:
										self.ATERROR('START FRAME IS HIGHER THAN OR EQUAL TO END FRAME')
						
						if valid == 'all' or valid == 'locked':
							if mc.checkBox(self.name+'OptionsCheckbox01', q=True, v=True) == 1:
								mc.setAttr(listedobject+self.trackname+'Handle'+'.overrideEnabled', 1)
								mc.setAttr(listedobject+self.trackname+'Handle'+'.overrideDisplayType', 2)
							else:
								mc.setAttr(listedobject+self.trackname+'Handle'+'.overrideEnabled', 0)
								mc.setAttr(listedobject+self.trackname+'Handle'+'.overrideDisplayType', 0)
			
			else: self.ATWARN('NO TRAIL EXISTS OR NO OBJECTS IN ARCTRACKER LIST BOX')

		
	def SELECTOBJECTS (self, arg=None):
		if mc.checkBox(self.name+'OptionsCheckbox04', q=True, v=True)==True:
			if mc.textScrollList(self.name+'TextScrollList', q=True, nsi=True) != 0:
				listedobjects = mc.textScrollList(self.name+'TextScrollList', q=True, si=True)
				newobjects = [i for i in listedobjects if mc.objExists(i) == 1]
				if len(newobjects) != 0: mc.select(newobjects, r=True)
	
	def UPDATEUI (self, arg=None):
	
		#CHECK LIST ISNT EMPTY
		if mc.textScrollList(self.name+'TextScrollList', q=True, nsi=True) != 0:
			listedobjects = mc.textScrollList(self.name+'TextScrollList', q=True, si=True)
			for i in [i for i in listedobjects if mc.objExists(i) == 1]:
				shortname = mc.ls(i, r=True, sn=True)[0]
				longname = mc.ls(i, r=True, l=True)[0]
				newname = shortname.replace('|', '_')
				listedobject = newname
				
				if mc.objExists(listedobject+self.trackname+'Handle') ==1:
					rgb = mc.getAttr(listedobject+self.trackname+'Handle'+'.trailColor')
					mc.colorSliderGrp(self.name+'DisplayColbox01', e=True, rgb=rgb[0])
					rgb = mc.getAttr(listedobject+self.trackname+'Handle'+'.keyframeColor')
					mc.colorSliderGrp(self.name+'DisplayColbox02', e=True, rgb=rgb[0])
					#rgb = mc.getAttr(listedobject+self.trackname+'Handle'+'.frameMarkerColor')
					#mc.colorSliderGrp(self.name+'DisplayColbox03', e=True, rgb=rgb[0])
					rgb = mc.getAttr(listedobject+self.trackname+'Handle'+'.activeKeyframeColor')
					mc.colorSliderGrp(self.name+'MoreOptionsColbox01', e=True, rgb=rgb[0])
					#rgb = mc.getAttr(listedobject+self.trackname+'Handle'+'.extraKeyframeColor')
					#mc.colorSliderGrp(self.name+'MoreOptionsColbox02', e=True, rgb=rgb[0])
					rgb = mc.getAttr(listedobject+self.trackname+'Handle'+'.beadColor')
					mc.colorSliderGrp(self.name+'MoreOptionsColbox03', e=True, rgb=rgb[0])
					mc.checkBox(self.name+'DisplayCheckbox03', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.showFrames'))
					#mc.checkBox(self.name+'DisplayCheckbox04', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.showFrames'))
					#mc.checkBox(self.name+'DisplayCheckbox05', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.showFrameMarkerFrames'))
					mc.floatSliderGrp(self.name+'OptionsSlider01', e=True, v=mc.getAttr(listedobject+self.trackname+'.increment'))
					mc.floatSliderGrp( self.name+'DisplaySlider01', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.atKeyframeSize'))
					#mc.floatSliderGrp( self.name+'DisplaySlider05', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.atFrameMarkerSize'))
					mc.floatSliderGrp( self.name+'DisplaySlider02', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.atTrailThickness'))
					mc.checkBox(self.name+'OptionsCheckbox02', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.xrayDraw')) 
					mc.checkBox(self.name+'OptionsCheckbox03', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.pinned'))
					mc.floatSliderGrp( self.name+'DisplaySlider03', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.preFrame'))
					mc.floatSliderGrp( self.name+'DisplaySlider04', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.postFrame'))
					mc.floatField(self.name+'TimeFloatField01', e=True, v=mc.getAttr(listedobject+self.trackname+'.startTime'))
					mc.floatField(self.name+'TimeFloatField02', e=True, v=mc.getAttr(listedobject+self.trackname+'.endTime'))
					#mc.checkBox(self.name+'MoreOptionsCheckbox02', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.showExtraKeys'))
					mc.checkBox(self.name+'MoreOptionsCheckbox03', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.showOutBead'))
					mc.checkBox(self.name+'MoreOptionsCheckbox04', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.showInBead'))
					mc.checkBox(self.name+'MoreOptionsCheckbox05', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.showInTangent'))
					mc.checkBox(self.name+'MoreOptionsCheckbox06', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.showOutTangent'))
					mc.checkBox(self.name+'MoreOptionsCheckbox07', e=True, v=mc.getAttr(listedobject+self.trackname+'Handle'+'.modifyKeys'))
					if mc.getAttr(listedobject+self.trackname+'Handle'+'.overrideDisplayType')==2: mc.checkBox(self.name+'OptionsCheckbox01', e=True, v=1)
					else: mc.checkBox(self.name+'OptionsCheckbox01', e=True, v=0)
	
			self.SELECTOBJECTS()
			self.RESIZELIST()
			self.WRITEFILE()
	
	def TIMESWITCH (self, arg=None):
		value = mc.checkBox(self.name+'TimeCheckbox01', q=True, v=True)
		mc.floatField(self.name+'TimeFloatField01', e=True, en=value)
		mc.floatField(self.name+'TimeFloatField02', e=True, en=value)
		self.UPDATETRAIL()
		
	def INPUTSTART (self, arg=None):
		end = mc.floatField(self.name+'TimeFloatField02', q=True, v=True)
		if mc.currentTime(q=True) < end:
			mc.floatField(self.name+'TimeFloatField01', e=True, v=mc.currentTime(q=True))
		else: self.ATERROR('START FRAME IS HIGHER THAN OR EQUAL TO END FRAME')
		self.UPDATETRAIL()
		
	def INPUTEND (self, arg=None):
		start = mc.floatField(self.name+'TimeFloatField01', q=True, v=True)
		if mc.currentTime(q=True) > start:
			mc.floatField(self.name+'TimeFloatField02', e=True, v=mc.currentTime(q=True))
		else: self.ATERROR('END FRAME IS LOWER THAN OR EQUAL TO START FRAME')
		self.UPDATETRAIL()
		
	def INPUTRANGE (self, arg=None):
		mc.floatField(self.name+'TimeFloatField01', e=True, v=mc.playbackOptions(q=True, min=True))
		mc.floatField(self.name+'TimeFloatField02', e=True, v=mc.playbackOptions(q=True, max=True))
		if mc.textScrollList(self.name+'TextScrollList', q=True, nsi=True) != 0: self.UPDATETRAIL()	
		
	def INPUTRELATIVETO (self, arg=None):
		mc.textField(self.name+'OldSchoolTextField01', e=1, tx=mc.ls(sl=1, r=1, sn=1)[0])
		self.WRITEFILE()
		
	def REMOVEALL (self, arg=None):
		list = mc.ls('*'+self.trackname+'*', r=True, l=True)
		if len(list) > 0: mc.delete(list)
		if (mc.window(self.window, q=1, exists=1)): mc.deleteUI(self.window)
		if mc.dockControl(self.dockname, q=1, ex=1) == 1: mc.deleteUI(self.dockname)
	
	def REMOVETRAIL (self, arg=None):
		if mc.textScrollList(self.name+'TextScrollList', q=True, nsi=True) != 0:
			listedobjects = mc.textScrollList(self.name+'TextScrollList', q=True, si=True)
			newobjects = [i for i in listedobjects if mc.objExists(i) == 1]
			for i in newobjects:
				shortname = mc.ls(i, r=True, sn=True)[0]
				longname = mc.ls(i, r=True, l=True)[0]
				newname = shortname.replace('|', '_')
				if mc.objExists(newname+self.trackname+'*') ==1: mc.delete(newname+self.trackname+'*')
		
	def REMOVETRAILS (self, arg=None):	
		list = mc.ls('*'+self.trackname+'*', r=True, l=True)
		if len(list) > 0: mc.delete(list)
	
	def TOGGLECURVES (self, arg=None):
		view = mc.getPanel(wf=True)
		if view in mc.getPanel(typ='modelPanel'):
			if mc.modelEditor(view, q=True, nurbsCurves=True): mc.modelEditor(view, e=True, nurbsCurves=0)
			else: mc.modelEditor(view, e=True, nurbsCurves=1)
		
	def ADDTOLIST (self, arg=None):
		textlist = self.name+'TextScrollList'
		listedObj = mc.textScrollList(self.name+'TextScrollList', q=True, ai=True )
		if listedObj == None: listedObj = []
		selection = mc.ls(sl=True, r=True, sn=True)
		if len(selection) < 1: self.ATERROR('NOTHING SELECTED')
		for obj in selection:
			if obj in listedObj: self.ATWARN(obj+' ALREADY IN LIST')
			else:
				mc.textScrollList(self.name+'TextScrollList', e=True, append=[obj])
		if mc.textScrollList(self.name+'TextScrollList', q=True, ni=True) != 0:
			mc.textScrollList(self.name+'TextScrollList', e=True, da=1)
			mc.textScrollList(self.name+'TextScrollList', e=True, si=selection)	
		
		self.WRITEFILE()
		self.RESIZELIST()

	def REMOVEFROMLIST (self, arg=None):	
		textlist = self.name+'TextScrollList'
		listedObj = mc.textScrollList(self.name+'TextScrollList', q=True, ai=True )
		mc.textScrollList(textlist, e=True, ri=mc.textScrollList(textlist, q=True, si=True))
		if mc.textScrollList(self.name+'TextScrollList', q=True, ni=True) != 0:
			mc.textScrollList(self.name+'TextScrollList', e=True, sii=1)
		else: mc.textScrollList(self.name+'TextScrollList', e=True, da=1)
		self.WRITEFILE()
		self.RESIZELIST()
		
	def REMOVEALLFROMLIST (self, arg=None):	
		textlist = self.name+'TextScrollList'
		for all in mc.textScrollList(textlist, q=True, ai=True ): mc.textScrollList(textlist, e=True, ri=all)
		if mc.textScrollList(self.name+'TextScrollList', q=True, ni=True) != 0:
			mc.textScrollList(self.name+'TextScrollList', e=True, sii=1)
		else: mc.textScrollList(self.name+'TextScrollList', e=True, da=1)
		self.WRITEFILE()
		self.RESIZELIST()

	def ADDCAMERA (self, arg=None):
		obj = mc.ls(r=True, sl=True)
		mc.textField(self.name+'OptionsTextField01', e=True, tx=obj[0])
		
	def CAMZOOM (self, arg=None):
		activecamera = mc.lookThru( q=True )
		activecamerashape = mc.listRelatives(activecamera, s=True)[0]
		mc.setAttr( activecamerashape+'.panZoomEnabled', 1 )
		mc.setAttr( activecamerashape+'.zoom', mc.floatSliderGrp(self.name+'ZoomSlider01', q=True, v=True)) 
		mc.setAttr( activecamerashape+'.verticalPan', mc.floatSliderGrp(self.name+'ZoomSlider02', q=True, v=True)) 
		mc.setAttr( activecamerashape+'.horizontalPan', mc.floatSliderGrp(self.name+'ZoomSlider03', q=True, v=True)) 
		
	def CAMLEFT (self, arg=None):
		value = mc.floatSliderGrp(self.name+'ZoomSlider03', q=True, v=True) - 0.01
		mc.floatSliderGrp(self.name+'ZoomSlider03', e=True, v=value)
		self.CAMZOOM()
	
	def CAMRIGHT (self, arg=None):
		value = mc.floatSliderGrp(self.name+'ZoomSlider03', q=True, v=True) + 0.01
		mc.floatSliderGrp(self.name+'ZoomSlider03', e=True, v=value)
		self.CAMZOOM()
		
	def CAMUP (self, arg=None):
		value = mc.floatSliderGrp(self.name+'ZoomSlider02', q=True, v=True) + 0.01
		mc.floatSliderGrp(self.name+'ZoomSlider02', e=True, v=value)
		self.CAMZOOM()
		
	def CAMDOWN (self, arg=None):
		value = mc.floatSliderGrp(self.name+'ZoomSlider02', q=True, v=True) - 0.01
		mc.floatSliderGrp(self.name+'ZoomSlider02', e=True, v=value)
		self.CAMZOOM()
		
	def CAMZOOMOUT (self, arg=None):
		value = mc.floatSliderGrp(self.name+'ZoomSlider01', q=True, v=True) + 0.01
		if value > 1.0: value = 1.0
		mc.floatSliderGrp(self.name+'ZoomSlider01', e=True, v=value)
		self.CAMZOOM()
		
	def CAMZOOMIN (self, arg=None):
		value = mc.floatSliderGrp(self.name+'ZoomSlider01', q=True, v=True) - 0.01
		if value < 0.001: value = 0.001
		mc.floatSliderGrp(self.name+'ZoomSlider01', e=True, v=value)
		self.CAMZOOM()
	
	def CAMRESET (self, arg=None):
		activecamera = mc.lookThru( q=True )
		activecamerashape = mc.listRelatives(activecamera, s=True)[0]
		mc.floatSliderGrp(self.name+'ZoomSlider01', e=True, v=1)
		mc.floatSliderGrp(self.name+'ZoomSlider02', e=True, v=0)
		mc.floatSliderGrp(self.name+'ZoomSlider03', e=True, v=0)
		mc.setAttr( activecamerashape+'.verticalPan', 0)
		mc.setAttr( activecamerashape+'.horizontalPan', 0)
		mc.setAttr( activecamerashape+'.zoom', 1)
		
	def DOCK (self, arg=None):
		mc.window(self.window, e=1, s=1 )
		dockctrl = mc.dockControl(self.dockname, area='left', l=self.title, allowedArea=('left','right'), w=self.windowWidth, con=self.window)
		mc.button(self.name+'DockButton', e=True, l='Float', c=self.UNDOCK)
		self.RESIZEWINDOW()
		self.WRITEFILEDOCKSTATE()
	
	def UNDOCK (self, arg=None):
		dockableUI = self.dockname
		if mc.dockControl(dockableUI, ex=True): mc.deleteUI(dockableUI)
		self.WRITEFILEDOCKSTATE()
		import arctrackerpro; reload(arctrackerpro)
		
	def INCREASELIST (self, arg=None):
		value = mc.textScrollList(self.name+'TextScrollList', q=True, h=True) +50
		mc.textScrollList(self.name+'TextScrollList', e=True, h=value)
		self.RESIZEWINDOW()
	
	def DECREASELIST (self, arg=None):
		value = mc.textScrollList(self.name+'TextScrollList', q=True, h=True) -50
		if value < 50: value = 50
		mc.textScrollList(self.name+'TextScrollList', e=True, h=value)
		self.RESIZEWINDOW()
	
	def MODIFYKEYSON (self, arg=None):	
		mc.checkBox(self.name+'MoreOptionsCheckbox05', e=1, v=0)
		mc.checkBox(self.name+'MoreOptionsCheckbox06', e=1, v=0)
		mc.checkBox(self.name+'MoreOptionsCheckbox03', e=1, v=0)
		mc.checkBox(self.name+'MoreOptionsCheckbox04', e=1, v=0)
		
	def OUTBEADON (self, arg=None):
		mc.checkBox(self.name+'MoreOptionsCheckbox05', e=1, v=0)
		mc.checkBox(self.name+'MoreOptionsCheckbox06', e=1, v=0)
		mc.checkBox(self.name+'MoreOptionsCheckbox04', e=1, v=0)
		mc.checkBox(self.name+'MoreOptionsCheckbox07', e=1, v=0)
		
	def INBEADON (self, arg=None):
		mc.checkBox(self.name+'MoreOptionsCheckbox05', e=1, v=0)
		mc.checkBox(self.name+'MoreOptionsCheckbox06', e=1, v=0)
		mc.checkBox(self.name+'MoreOptionsCheckbox03', e=1, v=0)
		mc.checkBox(self.name+'MoreOptionsCheckbox07', e=1, v=0)
		
	def INOUTTANON (self, arg=None):
		mc.checkBox(self.name+'MoreOptionsCheckbox03', e=1, v=0)
		mc.checkBox(self.name+'MoreOptionsCheckbox04', e=1, v=0)
		mc.checkBox(self.name+'MoreOptionsCheckbox07', e=1, v=0)
	
	def ATINFO (self, msg='Info', arg=None):
		fullmsg = 'ARC TRACKER : '+ msg
		OpenMaya.MGlobal.displayInfo(fullmsg)

	def ATERROR (self, msg='Error', arg=None):
		fullmsg = 'ARC TRACKER : '+ msg
		OpenMaya.MGlobal.displayError(fullmsg)
		sys.exit()
		
	def ATWARN (self, msg='Warn', arg=None):
		fullmsg = 'ARC TRACKER : ' + msg
		OpenMaya.MGlobal.displayWarning(fullmsg)
		
	def WRITEFILEDOCKSTATE(self, arg=None):	
		settings = []
		filename = self.filename
		filepath = self.filepath
		fullfilepath = self.fullfilepath
		if mc.file(fullfilepath, q=True, ex=True) == 1:
			with open(fullfilepath, 'r') as file:data = file.readlines()
			if mc.dockControl(self.dockname, q=1, ex=1) == 1: data[2] = 'Docked\n'
			else: data[2] = 'Floating\n'
			with open(fullfilepath, 'w') as file:file.writelines( data )
		else:
			self.WRITEFILE()
		
	def WRITEFILE(self, arg=None):	
		settings = []
		filename = self.filename
		filepath = self.filepath
		fullfilepath = self.fullfilepath
		selectedobjects = ''
		f = open(fullfilepath, 'w')
		#TITLE
		f.write(self.title+'\n')
		#1 TRAIL TYPE
		if mc.checkBox(self.name+'OldSchoolCheckbox01', q=1, v=1) == 1: f.write('OldSchoolTrails\n')
		else: f.write('EditableMotionTrails\n')
		#2 DOCKED
		if mc.dockControl(self.dockname, q=1, ex=1) == 1: f.write('Docked\n')
		else: f.write('Floating\n')
		#3 ALLOW COLLAPSE
		if mc.checkBox(self.name+'OptionsCheckbox05', q=1, v=1) == 1: f.write('AllowCollapse\n')
		else: f.write('DisallowCollapse\n')
		#4 RELATIVE TO
		if mc.checkBox(self.name+'OldSchoolCheckbox07', q=1, v=1) == 1: f.write('EnableRelativeTo\n')
		else: f.write('DisableRelativeTo\n')
		#5 RELATIVE TO OBJECT
		f.write(mc.textField(self.name+'OldSchoolTextField01', q=1, tx=1)+'\n')
		#6 MATCH COLOURS TO
		f.write(mc.radioCollection('OptionsRadio01', q=1, sl=1)+'\n')
		#7 SELECT OBJECTS
		if mc.checkBox(self.name+'OptionsCheckbox04', q=1, v=1) == 1: f.write('EnableSelectObjests\n')
		else: f.write('DisableSelectObjects\n')
		#8 SELECTED OBJECTS
		if mc.textScrollList(self.name+'TextScrollList', q=True, nsi=True) != 0:
			selectedobjects = ','.join(mc.textScrollList(self.name+'TextScrollList', q=True, si=True))
			f.write(selectedobjects+'\n')
		else: f.write('\n')
		#9 EDITABLE TRAILS
		if mc.checkBox(self.name+'OptionsCheckbox06', q=1, v=1) == 1: f.write('Editabletrails\n')
		else: f.write('DisableEditabletrails\n')
		#10 MENUS
		ms1 = str(mc.frameLayout(self.name+'FrameLayout01', q=1, cl=1))
		ms2 = str(mc.frameLayout(self.name+'FrameLayout02', q=1, cl=1))
		ms3 = str(mc.frameLayout(self.name+'FrameLayout03', q=1, cl=1))
		ms4 = str(mc.frameLayout(self.name+'FrameLayout04', q=1, cl=1))
		ms5 = str(mc.frameLayout(self.name+'FrameLayout05', q=1, cl=1))
		f.write(ms1+','+ms2+','+ms3+','+ms4+','+ms5+','+'\n')
		#11+ OBJECTS
		if mc.textScrollList(self.name+'TextScrollList', q=True, ni=True) != 0:
			data = mc.textScrollList(self.name+'TextScrollList', q=True, ai=True)
			for i in data: f.write(i+'\n')
		f.close()
		#print 'write file ' + fullfilepath
		
		self.RESIZEWINDOW()
		
	def READFILE(self, arg=None):
		filename = self.name+self.version+'Record'
		filepath = mc.internalVar(userScriptDir=True)
		fullfilepath = filepath+filename+'.txt'
		if mc.file(fullfilepath, q=True, ex=True) == 1: 
			data = open(fullfilepath, 'r').read()
			if data != '':
				listdata = [line.strip() for line in open(fullfilepath, 'r')]
				#1 TRAIL TYPE
				if listdata[1] == 'OldSchoolTrails': mc.checkBox(self.name+'OldSchoolCheckbox01', e=1, v=1)
				else: mc.checkBox(self.name+'OldSchoolCheckbox01', e=1, v=0)
				#2 DOCKED
				if listdata[2] == 'Docked': self.DOCK()
				#3 ALLOW COLLAPSE
				if listdata[3] == 'AllowCollapse': mc.checkBox(self.name+'OptionsCheckbox05', e=1, v=1)
				else: mc.checkBox(self.name+'OptionsCheckbox05', e=1, v=0)
				#4 RELATIVE TO
				if listdata[4] == 'EnableRelativeTo': mc.checkBox(self.name+'OldSchoolCheckbox07', e=1, v=1)
				else: mc.checkBox(self.name+'OldSchoolCheckbox07', e=1, v=0)
				#5 RELATIVE TO OBJECT
				mc.textField(self.name+'OldSchoolTextField01', e=1, tx=listdata[5])
				#6 MATCH COLOURS TO
				mc.radioCollection('OptionsRadio01', e=1, sl=listdata[6])
				#7 SELECT OBJECTS
				if listdata[7] == 'EnableSelectObjests': mc.checkBox(self.name+'OptionsCheckbox04', e=1, v=1)
				else: mc.checkBox(self.name+'OptionsCheckbox04', e=1, v=0)
				
				#9 EDITABLE TRAILS
				if listdata[9] == 'Editabletrails': mc.checkBox(self.name+'OptionsCheckbox06', e=1, v=1)
				else: mc.checkBox(self.name+'OptionsCheckbox06', e=1, v=0)
				
				#10 EDITABLE TRAILS
				menustatus = [self.STR2BOOL(i) for i in listdata[10].split(',')[:5]]
				mc.frameLayout(self.name+'FrameLayout01', e=1, cl=menustatus[0])
				mc.frameLayout(self.name+'FrameLayout02', e=1, cl=menustatus[1])
				mc.frameLayout(self.name+'FrameLayout03', e=1, cl=menustatus[2])
				mc.frameLayout(self.name+'FrameLayout04', e=1, cl=menustatus[3])
				mc.frameLayout(self.name+'FrameLayout05', e=1, cl=menustatus[4])
				self.RESIZEWINDOW()
				
				#9+
				for item in listdata[11:]:
					if item != '': mc.textScrollList(self.name+'TextScrollList', e=True, append=item)
				#8 SELECTED OBJECTS
				if mc.textScrollList(self.name+'TextScrollList', q=True, ni=True) != 0:
					words = listdata[8].split(',')
					[mc.textScrollList('ArcTrackerProTextScrollList', e=True, si=i) for i in words if mc.objExists(i) == 1]
				
				self.UPDATEUI()
	
	def STR2BOOL(self, string, arg=None):
		if string == 'True': return 1
		else: return 0
	
	def OPENFILE(self, arg=None):
		filename = self.name+self.version+'Record'
		filepath = mc.internalVar(userScriptDir=True)
		fullfilepath = filepath+filename+'.txt'
		
		
	def REMOVEFILE(self, arg=None):
		filename = self.name+self.version+'Record'
		filepath = mc.internalVar(userScriptDir=True)
		fullfilepath = filepath+filename+'.txt'
		
	def CREATEKNOT(self, cvNum, degree, arg=None):
		if cvNum <= degree:return None
		tailsSize = degree
		knotsNum = cvNum + degree - 1
		knotsArray = [0]*knotsNum
		for i in range(0, len(knotsArray)-degree+1):
			knotsArray[i + degree-1] = i
			tailValue = knotsArray[-tailsSize-1] + 1
		for i in range(1,tailsSize):
			knotsArray[-i] = tailValue
		return knotsArray
	
	def CREATECURVESPHERE(self, name='curveSphere1', arg=None):	
		a = mc.circle( n=name, nr=( 1, 0, 0), sw=360, r=.5, d=3, ut=0, tol=0.01, s=8, ch=1 )
		ashape = mc.listRelatives(c=True)
		b = mc.circle( nr=( 0, 1, 0), sw=360, r=.5, d=3, ut=0, tol=0.01, s=8, ch=1 )
		bshape = mc.listRelatives(c=True)
		c = mc.circle( nr=( 0, 0, 1), sw=360, r=.5, d=3, ut=0, tol=0.01, s=8, ch=1 )
		cshape = mc.listRelatives(c=True)
		mc.parent(bshape[0], cshape[0], a[0], r=True, s=True)
		mc.delete(b[0], c[0])
		mc.select(cl=True)
		return a[0], ashape[0]
		
	def OLDSCHOOLTOGGLE(self, arg=None):
	
		switch = mc.checkBox(self.name+'OldSchoolCheckbox01', q=1, v=1)
		#mc.checkBox(self.name+'OldSchoolCheckboxUpdate', e=1, en=switch)
		mc.checkBox(self.name+'OldSchoolCheckbox02', e=1, en=switch)
		mc.checkBox(self.name+'OldSchoolCheckbox03', e=1, en=switch)
		mc.floatSliderGrp( self.name+'OldSchoolDisplaySlider01', e=1, en=switch)
		mc.floatSliderGrp( self.name+'OldSchoolDisplaySlider02', e=1, en=switch)
		mc.checkBox(self.name+'OldSchoolCheckbox04', e=1, en=switch)
		mc.optionMenu(self.name+'OldSchoolOptionMenu01', e=1, en=switch)
		mc.colorIndexSliderGrp( self.name+'OldSchoolSlider01', e=1, en=switch)
		mc.checkBox(self.name+'OldSchoolCheckbox05', l='Frames', e=1, en=switch)
		mc.colorIndexSliderGrp( self.name+'OldSchoolSlider02', e=1, en=switch)
		mc.checkBox(self.name+'OldSchoolCheckbox06', e=1, en=switch)
		mc.colorIndexSliderGrp(self.name+'OldSchoolSlider03', e=1, en=switch)
		mc.checkBox(self.name+'OldSchoolCheckbox07', e=1, en=switch)
		mc.button(self.name+'OldSchoolButton01', e=1, en=switch)
		mc.textField(self.name+'OldSchoolTextField01', e=1, en=switch)

	def THOROUGHTRAIL(self, arg=None):
	
		currentSelection = mc.ls(sl=True, r=True, l=True)
		
		#VAR
		mydegree = 1
		framesize = mc.floatSliderGrp( self.name+'OldSchoolDisplaySlider01', q=1, v=1)
		keyframesize = mc.floatSliderGrp( self.name+'OldSchoolDisplaySlider02', q=1, v=1)
		
		#TIME RANGE
		if mc.checkBox(self.name+'TimeCheckbox01', q=True, v=True) == 0:
			start= mc.playbackOptions(q=True, min=True)
			end= mc.playbackOptions(q=True, max=True)
		else:
			if mc.floatField(self.name+'TimeFloatField01', q=True, v=True) < mc.floatField(self.name+'TimeFloatField02', q=True, v=True):
				start= mc.floatField(self.name+'TimeFloatField01', q=True, v=True)
				end= mc.floatField(self.name+'TimeFloatField02', q=True, v=True)
			else:
				self.ATERROR('START FRAME IS HIGHER THAN OR EQUAL TO END FRAME')
				
		self.REMOVETRAIL()
		
		#CHECK LIST ISNT EMPTY
		if mc.textScrollList(self.name+'TextScrollList', q=True, nsi=True) != 0:
			listedobjects = mc.textScrollList(self.name+'TextScrollList', q=True, si=True)
			newobjects = [i for i in listedobjects if mc.objExists(i) == 1]
			for i in newobjects:
				shortname = mc.ls(i, r=True, sn=True)[0]
				longname = mc.ls(i, r=True, l=True)[0]
				newname = shortname.replace('|', '_')
		
				#HELPER
				helper = mc.spaceLocator(n=newname+self.trackname+'Helper')
				con = mc.pointConstraint(longname, helper[0], w=1, mo=0, n=newname+self.trackname+'pointConstraint')
				bakeObjects = [helper[0]]
				
				if mc.checkBox(self.name+'OldSchoolCheckbox07', q=1, v=1) == 1:
					if mc.textField(self.name+'OldSchoolTextField01', q=1, tx=1) == '' or mc.objExists(mc.textField(self.name+'OldSchoolTextField01', q=1, tx=1)) != 1: self.ATERROR('RELATIVE TO OBJECT DOES NOT EXIST 2')
					relativeToObject = mc.ls(mc.textField(self.name+'OldSchoolTextField01', q=1, tx=1), r=1, l=1)[0]
					if mc.objExists(relativeToObject) != 1: self.ATERROR('RELATIVE TO OBJECT DOES NOT EXIST')
					camerahelper = mc.spaceLocator(n=newname+self.trackname+'CameraHelper')
					cameracon = mc.pointConstraint(relativeToObject, camerahelper[0], w=1, mo=0, n=newname+self.trackname+'CamerapointConstraint')
					bakeObjects.append(camerahelper[0])
				
				if mc.checkBox(self.name+'OldSchoolCheckbox03', q=1, v=1) == 1:
					mc.bakeResults(bakeObjects, at=['tx','ty','tz'], sm=1, sampleBy=1, time=(start,end), preserveOutsideKeys=1, sparseAnimCurveBake=0)
				else: mc.bakeResults(bakeObjects, at=['tx','ty','tz'], sm=0, sampleBy=1, time=(start,end), preserveOutsideKeys=1, sparseAnimCurveBake=0)
				
				if mc.keyframe( shortname, q=True, kc=True ) < 0: objecttimes = list(set(mc.keyframe( shortname, q=True, tc=True )))
				else: objecttimes = []
				helpertimes = list(set(mc.keyframe( helper[0], q=True, tc=True ))) 
				keys = [mc.keyframe( helper[0], q=True, time=(ti,ti), at=('tx','ty','tz'), vc=True ) + [ti] for ti in helpertimes if ti in objecttimes]
				frames = [mc.keyframe( helper[0], q=True, time=(ti,ti), at=('tx','ty','tz'), vc=True ) + [ti] for ti in helpertimes if not ti in objecttimes]
				trails = [mc.keyframe( helper[0], q=True, time=(ti,ti), at=('tx','ty','tz'), vc=True )  for ti in helpertimes]
				
				if mc.checkBox(self.name+'OldSchoolCheckbox07', q=1, v=1) == 1:
					cameraframes = [mc.keyframe( camerahelper[0], q=True, time=(ti,ti), at=('tx','ty','tz'), vc=True ) for ti in helpertimes]
					newframes = []
					for i in range(len(frames)): newframes.append([frames[i][0]+cameraframes[i][0],frames[i][1]+cameraframes[i][1], frames[i][2]+cameraframes[i][2],frames[i][2]+cameraframes[i][2],frames[i][3]])
					newkeys = []
					for i in range(len(keys)): newframes.append([keys[i][0]+cameraframes[i][0],keys[i][1]+cameraframes[i][1], keys[i][2]+cameraframes[i][2],keys[i][2]+cameraframes[i][2],keys[i][3]])

				#FRAMES
				if mc.checkBox(self.name+'OldSchoolCheckbox05', q=1, v=1) == 1:
					for i in frames:
						number = '_%04d_' % (int(i[3]))
						nname = newname+self.trackname+number+'Frame'
						if mc.optionMenu(self.name+'OldSchoolOptionMenu01', q=1, v=1) == 'Curves': knot = self.CREATECURVESPHERE(nname)
						else: knot = mc.sphere(n=nname)
						mc.move( i[0], i[1], i[2], knot, a=True, ws=True )
						mc.scale( framesize, framesize, framesize, knot, a=True)
						mc.setAttr(knot[0]+'.overrideEnabled', 1)
						mc.setAttr(knot[0]+'.overrideColor', mc.colorIndexSliderGrp( self.name+'OldSchoolSlider02', q=1, v=1)-1)
				
				#KEYFRAMES
				if mc.checkBox(self.name+'OldSchoolCheckbox06', q=1, v=1) == 1:
					for i in keys:
						number = '_%04d_' % (int(i[3]))
						nname = newname+self.trackname+number+'Keyframe'
						if mc.optionMenu(self.name+'OldSchoolOptionMenu01', q=1, v=1) == 'Curves': knot = self.CREATECURVESPHERE(nname)
						else: knot = mc.sphere(n=nname)
						mc.move( i[0], i[1], i[2], knot, a=True, ws=True )
						mc.scale( keyframesize, keyframesize, keyframesize, knot, a=True)
						mc.setAttr(knot[0]+'.overrideEnabled', 1)
						mc.setAttr(knot[0]+'.overrideColor', mc.colorIndexSliderGrp( self.name+'OldSchoolSlider03', q=1, v=1)-1)
						
				#RELATIVE TO
				if mc.checkBox(self.name+'OldSchoolCheckbox07', q=1, v=1) == 1:
					now = mc.currentTime(q=1)
					for t in helpertimes:
						mc.currentTime(int(t))
						strt = '%04d' % (int(t))
						mc.parent(newname+self.trackname+'*_'+strt+'_*rame', relativeToObject)
					mc.delete(camerahelper[0], cameracon[0])
					mc.currentTime(now)
					
				#TRAILS
				if mc.checkBox(self.name+'OldSchoolCheckbox04', q=1, v=1) == 1:
					if mc.checkBox(self.name+'OldSchoolCheckbox07', q=1, v=1) == 1:
						trails = [mc.xform(i, q=1, ws=1, t=1) for i in mc.ls(newname+self.trackname+'*rame', r=1, l=1) if 'Shape' not in i]
					curveknots = self.CREATEKNOT(len(trails), mydegree)
					curve = mc.curve(n=newname+self.trackname+'Trail', d=mydegree, p=trails, k=curveknots)
					mc.setAttr(curve+'.overrideEnabled', 1)
					mc.setAttr(curve+'.overrideColor', mc.colorIndexSliderGrp( self.name+'OldSchoolSlider01', q=1, v=1)-1)

				#LOCK
				for trailpart in mc.ls(newname+self.trackname+'*rame*', newname+self.trackname+'Trail*', r=1, l=1):
					if mc.checkBox(self.name+'OldSchoolCheckbox02', q=1, v=1) == 1: mc.setAttr(trailpart+'.overrideDisplayType', 1)
					mc.setAttr(trailpart+'.overrideShading', 0)
					mc.setAttr(trailpart+'.overrideTexturing', 0)
					mc.setAttr(trailpart+'.overridePlayback', 0)
				
				#GROUP
				group = mc.group(mc.ls(newname+self.trackname+'*',l=True), n=newname+self.trackname+'Group')
				if mc.checkBox(self.name+'OldSchoolCheckbox07', q=1, v=1) == 1: mc.parent(group, relativeToObject)
				mc.delete(helper[0], con[0])
				if len(currentSelection) > 0: mc.select(currentSelection, r=1)
				
				#UPDATE
				#attr = 'translateY'
				#atJobNum1 = mc.scriptJob( ac= [(shortname+'.'+attr), self.THOROUGHTRAIL ], ro=1, protected=True)
				#KillAtJobNum1 = mc.scriptJob( nd= [(shortname+'.'+attr), 'mc.scriptJob( k='+str(atJobNum1)+', force=True)'], ro=1, protected=True)
	
	def HOTKEYCOMMANDCREATETRAILS(self, arg=None):
		mc.checkBox(self.name+'OptionsCheckbox04', e=1, v=0)
		#self.REMOVETRAILS()
		self.ADDTOLIST()
		self.CREATETRAIL()
		#mc.currentTime(mc.currentTime(q=1))
		if mc.window(self.window, q=1, exists=1): mc.deleteUI(self.window)
		if mc.dockControl(self.dockname, q=1, ex=1) == 1: mc.deleteUI(self.dockname)
		
	def HOTKEYCOMMANDREMOVETRAILS(self, arg=None):
		self.REMOVEALL()
	
myWin = arctrackerpro2012()