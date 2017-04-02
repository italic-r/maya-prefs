# ----------------------------------------------------------------------------------------------
#
# ActorTools.py
# v2.0 (150518)
#
# create a game engine compatible rig based on the given animation rig
# including basic tools for exporting/importing animation
#
# Ingo Clemens
# www.braverabbit.com
#
# Copyright brave rabbit, Ingo Clemens 2011-2015
# All rights reserved.
#
# ----------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# ----------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------
#
#	USE AND MODIFY AT YOUR OWN RISK!!
#
# ----------------------------------------------------------------------------------------------


import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya

from functools import partial
import math
import os
import shutil
import re

class ActorTools():
	
	def __init__(self):
		self.version = '2.0 (150518)'
		self.creator = 'Ingo Clemens'
		self.copyright = 'brave rabbit 2011-2015'
		
		self.win = 'actorToolsWindow'
		self.aboutWin = 'actorToolsAboutWindow'
		self.nodesWin = 'actorNodesWindow'
		self.rootJointWin = 'actorDefineRootJointWindow'
		self.meshTSL = ''
		self.skinTSL = ''
		self.bsTSL = ''
		self.rigButton = ''
		self.nameField = ''
		self.charOption = ''
		self.masterButton = ''
		self.saveButton = ''
		self.loadButton = ''
		self.bakeButton = ''
		self.frameRange = ''
		self.animFileField = ''
		self.exportMenuItem = ''
		self.fbxVersionOption = ''
		self.fbxOptionsLayout = ''
		self.reviewCheck = ''
		self.rootCheck = ''
		self.loadRigButton = ''
		self.saveRigButton = ''
		self.loadActorButton = ''
		self.saveActorButton = ''
		self.newSceneButton = ''
		
		self.mainProgress = ''
		
		self.name = ''
		self.char = ''
		self.actor = 'actor_grp'
		self.root = ''
		self.skinNodes = {}
		self.skinMeshes = []
		self.skinCluster = []
		self.bsNodes = []
		self.meshHasBs = {}
		self.joints = {}
		self.actorMeshes = {}
		self.reParent = []
		self.useDescription = False
		
		self.actorPath = ''
		
		self.loadPlugins()
		self.buildUI()
	
	def round(self, a, digits):
		'''
		round the given list of floats to 5 decimals
		'''
		result = []
		mult = math.pow(10.0, digits)
		for i in a:
			result.append(math.floor(i * mult) / mult)
		return result
	
	def loadPlugins(self):
		'''
		make sure the fbx and atom plug-in is loaded
		'''
		if not cmds.pluginInfo('fbxmaya', q = True, l = True):
			try:
				cmds.loadPlugin('fbxmaya')
			except:
				OpenMaya.MGlobal_displayError('Error while trying to load the FBX plug-in')
		
		if not cmds.pluginInfo('atomImportExport', q = True, l = True):
			try:
				cmds.loadPlugin('atomImportExport')
			except:
				OpenMaya.MGlobal_displayError('Error while trying to load the ATOM plug-in')
	
	# --------------------------------------------------------------------------------------------------
	# folder creation
	# --------------------------------------------------------------------------------------------------

	def createDir(self, path):
		'''
		create a folder at the given path if it doesn't exist
		'''
		if not os.path.exists(path):
			try:
				os.makedirs(path)
				print '// Created folder %s' % path
			except:
				print '// Unable to write to current directory'
				return False
		return True
	
	def createActorDir(self):
		'''
		create the folder structure for the rig and the actor
		'''
		actorsPath = self.getActorRootPath()
		self.name = cmds.textFieldGrp(self.nameField, q = True, tx = True)
		if self.createDir(actorsPath):
			if self.createDir(actorsPath + '/' + self.name):
				self.actorPath = actorsPath + '/' + self.name
				if self.createDir(self.actorPath + '/rig'):
					self.createDir(self.actorPath + '/rig/versions')
				if self.createDir(self.actorPath + '/actor'):
					self.createDir(self.actorPath + '/actor/versions')
				self.createDir(self.actorPath + '/animations')
				self.createDir(self.actorPath + '/export')
				self.createDir(self.actorPath + '/data')
	
	# --------------------------------------------------------------------------------------------------
	# write/read descriptions
	# --------------------------------------------------------------------------------------------------
	
	def writeDescription(self, path, data):
		'''
		write a text file with the given data to the given path
		'''
		try:
			file = open(path, 'wb')
		except:
			OpenMaya.MGlobal_displayError('A file error has occured for file \'%s\'' % path)
			return
		file.write(str(data) + '\n')
		file.close()
	
	def readDescription(self, path):
		'''
		read a text file at the given path and return a list of lines
		'''
		try:
			file = open(path, 'rb')
		except:
			OpenMaya.MGlobal_displayError('A file error has occured for file \'%s\'' % path)
			return
		data = file.read()
		lines = data.split('\n')
		file.close()
		return lines
	
	# --------------------------------------------------------------------------------------------------
	# getting path/file information
	# --------------------------------------------------------------------------------------------------
	
	def getActorRootPath(self):
		'''
		return the base path of the rig/actor folder structure
		'''
		rootPath = cmds.workspace(q = True, rd = True)
		return rootPath + 'scenes/actors'
		
	def getActors(self):
		'''
		return a list of actors based on existing folders
		'''
		actorsPath = self.getActorRootPath()
		chars = []
		if os.path.exists(actorsPath):
			items = os.listdir(actorsPath)
			for i in items:
				# only respect folder names
				if os.path.isdir(actorsPath + '/' + i):
					chars.append(i)
		return chars
	
	def getFileVersion(self, path, fileName, ext):
		'''
		return the full path from the given path elements
		including a version identifier which is increased by one
		if a previous version exists
		'''
		version = 1
		exists = True
		while exists:
			if os.path.isfile('%s/%s_v%i.%s' % (path, fileName, version, ext)):
				version += 1
			else:
				exists = False
		return '%s/%s_v%i.%s' % (path, fileName, version, ext)
	
	# --------------------------------------------------------------------------------------------------
	# ui
	# --------------------------------------------------------------------------------------------------
	
	def buildUI(self):
		'''
		create the tool window
		'''
		if cmds.window(self.win, exists = True):
			cmds.deleteUI(self.win)
		
		if cmds.windowPref(self.win, ex = True):
			cmds.windowPref(self.win, e = True, w = 280, h = 150)
		
		# get the user preferences
		advCheck = False
		revCheck = False
		makeRootCheck = False
		if cmds.optionVar(ex = 'actorToolsAdvancedExportCheck'):
			advCheck = cmds.optionVar(q = 'actorToolsAdvancedExportCheck')
		if cmds.optionVar(ex = 'actorToolsReviewAfterExportCheck'):
			revCheck = cmds.optionVar(q = 'actorToolsReviewAfterExportCheck')
		if cmds.optionVar(ex = 'actorToolsCreateRootNodeCheck'):
			makeRootCheck = cmds.optionVar(q = 'actorToolsCreateRootNodeCheck')
		
		cmds.window(self.win, t = 'Actor Tools', w = 280, h = 150, mb = True)
		cmds.menu(l = 'Options')
		self.exportMenuItem = cmds.menuItem(l = 'Advanced Export', cb = advCheck, c = partial(self.toggleAdvancedExport))
		cmds.menu(l = 'Help')
		cmds.menuItem(l = 'About', c = partial(self.openAbout))
		
		cmds.columnLayout(adj = True)
		
		libraryFrame = cmds.frameLayout(l = 'Library', cll = 0, mw = 10, mh = 10)
		self.charOption = cmds.optionMenu(cc = partial(self.loadCharacter))
		cmds.setParent('..')
		
		tabs = cmds.tabLayout(bs = 'none')
		
		createFrame = cmds.frameLayout(l = 'Create', lv = False, mw = 10, mh = 10)
		cmds.text(l = 'Enter the character name and select the\ntop character group node to create the setup.', w = 230)
		self.nameField = cmds.textFieldGrp(l = 'Character Name', cw2 = (100, 160), co2 = (0, 5), ct2 = ('both', 'both'))
		self.rootCheck = cmds.checkBoxGrp(l = 'Create Root Joint', v1 = makeRootCheck, cw2 = (106, 30), co2 = (5, 0), ct2 = ('right', 'both'))
		cmds.separator(h = 50, style = 'none')
		self.rigButton = cmds.button(l = 'Create Actor', w = 50, c = partial(self.getRigNodes))
		cmds.setParent('..')
		
		editFrame = cmds.frameLayout(l = 'Edit', lv = False, mw = 10, mh = 10)
		self.loadRigButton = cmds.button(l = 'Load Character Rig', w = 50, en = False, c = partial(self.loadRig, 'rig'))
		self.saveRigButton = cmds.button(l = 'Save Character Rig', w = 50, en = False, c = partial(self.saveRig, 'rig'))
		self.loadActorButton = cmds.button(l = 'Load Actor Rig', w = 50, en = False, c = partial(self.loadRig, 'actor'))
		self.saveActorButton = cmds.button(l = 'Save Actor Rig', w = 50, en = False, c = partial(self.saveRig, 'actor'))
		cmds.separator(h = 10, style = 'none')
		self.newSceneButton = cmds.button(l = 'Create New Animation Scene', w = 50, en = False, c = partial(self.newScene))
		cmds.setParent('..')
		
		animationFrame = cmds.frameLayout(l = 'Animation', lv = False, mw = 10, mh = 10)
		cmds.text(l = 'Select the character group node in the scene\nto save the animation. The node name must\nmatch the name of the library character.', w = 230)
		self.animFileField = cmds.textFieldButtonGrp(l = 'Animation File', bl = '...', cw3 = (100, 160, 30), co3 = (0, 5, 0), ct3 = ('both', 'both', 'both'), bc = partial(self.openFileList, 'animation'))
		cmds.separator(h = 58, style = 'none')
		self.saveButton = cmds.button(l = 'Save Animation', w = 50, en = False, c = partial(self.exportAnimation))
		cmds.setParent('..')
		
		rangeStart = cmds.playbackOptions(q = True, min = True)
		rangeEnd = cmds.playbackOptions(q = True, max = True)
		
		exportFrame = cmds.frameLayout(l = 'Export', lv = False, mw = 10, mh = 10)
		self.masterButton = cmds.button(l = 'Load Export Master Scene', w = 50, en = False, c = partial(self.loadMasterScene))
		self.loadButton = cmds.button(l = 'Load Animation', w = 50, en = False, c = partial(self.loadAnimation))
		self.frameRange = cmds.floatFieldGrp(l = 'Frame Range', nf = 2, pre = 2, v1 = rangeStart, v2 = rangeEnd, cw3 = (100, 60, 60), co3 = (0, 5, 5), ct3 = ('both', 'both', 'both'))
		self.exportFileField = cmds.textFieldButtonGrp(l = 'Export File', bl = '...', cw3 = (100, 160, 30), co3 = (0, 5, 0), ct3 = ('both', 'both', 'both'), bc = partial(self.openFileList, 'export'))
		self.reviewCheck = cmds.checkBoxGrp(l = 'Review', v1 = revCheck, cw2 = (106, 30), co2 = (5, 0), ct2 = ('right', 'both'))
		self.bakeButton = cmds.button(l = 'Bake And Export Actor', w = 50, en = False, c = partial(self.exportActor))
		cmds.setParent('..')
		
		self.fbxOptionsLayout = cmds.frameLayout(l = 'FBX Options', lv = False, mw = 10, mh = 10)
		value = mel.eval('FBXExportSmoothingGroups -q')
		cmds.checkBoxGrp(l = 'Smoothing Groups', v1 = value, cw2 = (168, 30), co2 = (5, 0), ct2 = ('right', 'both'), cc = partial(self.setFBXPreference, 'FBXExportSmoothingGroups'))
		value = mel.eval('FBXExportSmoothMesh -q')
		cmds.checkBoxGrp(l = 'Smooth Mesh', v1 = value, cw2 = (168, 30), co2 = (5, 0), ct2 = ('right', 'both'), cc = partial(self.setFBXPreference, 'FBXExportSmoothMesh'))
		value = mel.eval('FBXExportHardEdges -q')
		cmds.checkBoxGrp(l = 'Split-Vertex Normals', v1 = value, cw2 = (168, 30), co2 = (5, 0), ct2 = ('right', 'both'), cc = partial(self.setFBXPreference, 'FBXExportHardEdges'))
		value = mel.eval('FBXExportTriangulate -q')
		cmds.checkBoxGrp(l = 'Triangulate', v1 = value, cw2 = (168, 30), co2 = (5, 0), ct2 = ('right', 'both'), cc = partial(self.setFBXPreference, 'FBXExportTriangulate'))
		value = mel.eval('FBXExportTangents -q')
		cmds.checkBoxGrp(l = 'Tangents & Bi-Normals', v1 = value, cw2 = (168, 30), co2 = (5, 0), ct2 = ('right', 'both'), cc = partial(self.setFBXPreference, 'FBXExportTangents'))
		
		self.fbxVersionOption = cmds.optionMenuGrp(l = 'FBX Version', cw2 = (168, 80), co2 = (5, 0), ct2 = ('right', 'both'), cc = partial(self.setFBXVersion))
		cmds.menuItem(l = '2016')
		cmds.menuItem(l = '2014')
		cmds.menuItem(l = '2013')
		cmds.menuItem(l = '2012')
		cmds.menuItem(l = '2011')
		cmds.menuItem(l = '2010')
		cmds.menuItem(l = '2009')
		cmds.optionMenuGrp(self.fbxVersionOption, e = True, v = self.getFBXVersion())
		cmds.setParent('..')
		
		cmds.tabLayout(tabs, e = True, sti = 4, tl = ((createFrame, 'Create'), (editFrame, 'Edit'), (animationFrame, 'Animation'), (exportFrame, 'Export'), (self.fbxOptionsLayout, 'Options')))

		cmds.showWindow(self.win)
		# refresh the character list
		self.listCharacters()
	
	def openAbout(self, *args):
		'''
		open the about window
		'''
		if cmds.window(self.aboutWin, exists = True):
			cmds.deleteUI(self.aboutWin)

		cmds.window(self.aboutWin, t = 'About Actor Tools', w = 200, h = 130)
		if cmds.windowPref(self.aboutWin, ex = True):
			cmds.windowPref(self.aboutWin, e = True, wh = (200, 130))
	
		cmds.columnLayout(adj = True)
		cmds.separator(style = 'none', h = 15)
		cmds.text(l = 'Actor Tools', fn = 'boldLabelFont')
		cmds.separator(style = 'none', h = 15)
		cmds.text(l = self.version)
		cmds.separator(style = 'none', h = 15)
		cmds.text(l = 'Creator: %s' % self.creator)
		cmds.separator(style = 'none', h = 5)
		cmds.text(l = u"\u00A9" + ' %s' % self.copyright)
		cmds.setParent('..')
	
		cmds.showWindow(self.aboutWin)
	
	# --------------------------------------------------------------------------------------------------
	# ui actions
	# --------------------------------------------------------------------------------------------------
	
	def listCharacters(self):
		'''
		refresh the option menu to
		show all available characters
		'''
		items = cmds.optionMenu(self.charOption, q = True, ill = True)
		if items != None:
			cmds.deleteUI(items)
		
		chars = self.getActors()
		if len(chars):
			cmds.menuItem('Select Character', p = self.charOption)
			for c in chars:
				cmds.menuItem(c, p = self.charOption)
		else:
			cmds.menuItem('No Characters', p = self.charOption)
	
	def loadCharacter(self, *args):
		'''
		load the name of the selected character root node
		which is stored in the description file
		activate the buttons if a valid character is loaded
		'''
		enable = False
		if cmds.optionMenu(self.charOption, q = True, sl = True) != 1:
			self.name = cmds.optionMenu(self.charOption, q = True, v = True)
			actorsPath = self.getActorRootPath()
			self.actorPath = actorsPath + '/' + self.name
			lines = self.readDescription('%s/data/%s.txt' % (self.actorPath, self.name))
			self.char = lines[0]
			print '// Loaded character \'%s\' with root node \'%s\' from \'%s\'' % (self.name, self.char, self.actorPath)
			enable = True
		
		# set the buttons enabled state
		cmds.button(self.masterButton, e = True, en = enable)
		cmds.button(self.saveButton, e = True, en = enable)
		cmds.button(self.loadButton, e = True, en = enable)
		cmds.button(self.bakeButton, e = True, en = enable)
		cmds.button(self.loadRigButton, e = True, en = enable)
		cmds.button(self.saveRigButton, e = True, en = enable)
		cmds.button(self.loadActorButton, e = True, en = enable)
		cmds.button(self.saveActorButton, e = True, en = enable)
		cmds.button(self.newSceneButton, e = True, en = enable)
		
		# clear the character node name if no character is selected
		if not enable:
			self.char = ''
	
	def toggleAdvancedExport(self, *args):
		'''
		toggle the fbx export process between simple and manual
		manual is the default export selected dialog
		'''
		state = cmds.menuItem(self.exportMenuItem, q = True, cb = True)
		cmds.frameLayout(self.fbxOptionsLayout, e = True, en = not state)
		cmds.textFieldButtonGrp(self.exportFileField, e = True, en = not state)
	
	def loadRig(self, type, *args):
		'''
		load the original rig scene for editing
		'''
		path = self.getMasterScenePath('/%s' % type, self.name)
		if path != '':
			cmds.file(path, f = True, op = 'v=0', o = True)
			self.applyCameraPosition()
	
	def saveRig(self, type, *args):
		'''
		save the edited rig file and create a new version
		'''
		cmds.file(save = True)
		# export the rig version by copying the rig file
		fileNameRig = cmds.file(q = True, sn = True)
		ext = fileNameRig.split('.')[-1]
		fileVersion = self.getFileVersion(self.actorPath + '/%s/versions' % type, self.name, ext)
		shutil.copy(str(fileNameRig), str(fileVersion))
		print '// Saved %s version to %s' % (type, fileVersion)
	
	def newScene(self, *args):
		'''
		create a new scene and reference the rig
		'''
		path = self.getMasterScenePath('/rig', self.name)
		if path != '':
			cmds.file(f = True, new = True)
			# reference the rig
			cmds.file(path, r = True, op = 'v=0', iv = True, gl = True, mnc = False, ns = 'rig')
			self.applyCameraPosition()
	
	def applyCameraPosition(self):
		'''
		read the camera transform from the file
		and apply it to the current scene
		'''
		lines = self.readDescription('%s/data/%s.txt' % (self.actorPath, self.name))
		cmds.xform('persp', m = eval(lines[1]))
		self.setCameraCenterOfInterest()
	
	def setCameraCenterOfInterest(self):
		'''
		place the center of interest depending on the camera position
		'''
		pos = cmds.getAttr('persp.translate')[0]
		world = OpenMaya.MVector(0, 0, 0)
		camPos = OpenMaya.MVector(pos[0], pos[1], pos[2])
		coi = (world - camPos).length()
		cmds.setAttr('persp.centerOfInterest', coi)
		
	def openFileList(self, type, *args):
		'''
		open a file dialog for letting the user choose a file
		for saving the animation or exporting the actor
		'''
		if type == 'animation':
			filter = 'ATOM (*.atom)'
			path = '%s/animations' % self.actorPath
			caption = 'Animation'
			field = self.animFileField
		else:
			filter = 'FBX export (*.fbx)'
			path = '%s/export' % self.actorPath
			caption = 'Export'
			field = self.exportFileField
		
		fileName = cmds.fileDialog2(dir = path, fm = 0, ff = filter, okc = 'OK', cap = 'Select %s File' % caption)
		if not fileName:
			return
		
		cmds.textFieldButtonGrp(field, e = True, tx = os.path.basename(fileName[0]).split('.')[0])
	
	# --------------------------------------------------------------------------------------------------
	# fbx settings
	# --------------------------------------------------------------------------------------------------
	
	def getFBXVersion(self):
		'''
		get the fbx version from the preferences and set the option menu
		'''
		value = mel.eval('FBXExportFileVersion -q')
		value = value[3:7]
		return value
	
	def setFBXVersion(self, *args):
		'''
		set the fbx version based on the option menu setting
		'''
		value = cmds.optionMenuGrp(self.fbxVersionOption, q = True, v = True)
		value = 'FBX%s00' % value
		mel.eval('FBXExportFileVersion -v ' + value)
	
	def setFBXPreference(self, var, *args):
		'''
		toggle the given fbx preference setting
		'''
		value = mel.eval(var + ' -q')
		mel.eval(var + ' -v ' + str(1 - value))
	
	# --------------------------------------------------------------------------------------------------
	# actor building
	# --------------------------------------------------------------------------------------------------
	
	def getRigNodes(self, *args):
		'''
		First step for building the actor
		
		perform some basic selection checks
		write the character root node name to the description file
		try to find the skin meshes and skin clusters
		and display them in a window
		'''
		# check for the group selection
		if not self.getSelection():
			OpenMaya.MGlobal_displayError('Select the character group')
			return
		
		if cmds.textFieldGrp(self.nameField, q = True, tx = True) == '':
			OpenMaya.MGlobal_displayError('No character name entered')
			return
		
		if cmds.checkBoxGrp(self.rootCheck, q = True, v1 = True):
			if not self.findRootJoint():
				self.showDefineRootJointUI()
				return
		
		result = cmds.confirmDialog(	t = 'Actor Tools', 
										m = 'Save the scene before creating the actor?', 
										b = ['Save', 'Cancel'], 
										db = 'Cancel', 
										cb = 'Cancel', 
										ds = 'Cancel')
		if result == 'Save':
			cmds.file(save = True)
		
		self.createActorDir()
		pos = cmds.xform('persp', q = True, m = True)
		self.writeDescription('%s/data/%s.txt' % (self.actorPath, self.name), self.char + '\n' + str(pos))
		
		self.skinNodes = {}
		
		# get the skin meshes and skin clusters
		if not self.getSkinMesh():
			OpenMaya.MGlobal_displayError('The character contains no meshes with a skin cluster')
			return
		# display the found rig nodes
		self.showRigNodesUI()
	
	def findRootJoint(self):
		'''
		returns true if the rig contains a joint named "Root"
		'''
		cmds.select(self.char, hi = True)
		joints = cmds.ls(sl = True, type = 'joint')
		exists = False
		for j in joints:
			if j == 'Root':
				exists = True
		cmds.select(self.char, r = True)
		return exists
	
	def showDefineRootJointUI(self):
		'''
		show the window to let the user define the root joint placement
		'''
		if cmds.window(self.rootJointWin, exists = True):
			cmds.deleteUI(self.rootJointWin)
		if cmds.windowPref(self.rootJointWin, ex = True):
			cmds.windowPref(self.rootJointWin, e = True, w = 160, h = 160)
		cmds.window(self.rootJointWin, t = 'Define Character Root', w = 160, h = 160, s = False)
		
		cmds.columnLayout()
		cmds.frameLayout(lv = False, cll = 0, mw = 10, mh = 10)
		cmds.text(l = 'The rig must contain a joint\nwith the name "Root" at\nthe top of the joint hierarchy.\n')
		cmds.text(l = 'Select the root joint of the character\'s\njoint hierarchy and press Continue to\ncreate the joint automatically.\n')
		
		cmds.button(l = 'Continue', c = partial(self.createRigRootJoint))
		cmds.setParent('..')
		cmds.setParent('..')
		
		cmds.showWindow(self.rootJointWin)
	
	def createRigRootJoint(self, *args):
		'''
		create the root joint for the rig
		based on the user selection
		'''
		sel = cmds.ls(sl = True, type = 'joint')
		if sel == None or not len(sel):
			OpenMaya.MGlobal_displayError('No joint selected')
			return
		
		parent = cmds.listRelatives(sel[0], p = True)
		if parent == None or not len(parent):
			OpenMaya.MGlobal_displayError('The selected joint is at scene level. This is not recommended for a character rig and not supported.')
			return
		
		# check for siblings
		cancel = False
		children = cmds.listRelatives(parent[0], c = True, type = 'joint')
		if len(children) > 1:
			result = cmds.confirmDialog(	t = 'Actor Tools', 
											m = 'There are other joints at the same\nhierarchy level as the selected root.\nShould these be parented to the\nnew Root joint as well?', 
											b = ['Parent', 'Skip', 'Cancel'], 
											db = 'Parent', 
											cb = 'Cancel', 
											ds = 'Cancel')
			if result == 'Parent':
				pass
			elif result == 'Skip':
				children = []
			elif result == 'Cancel':
				cancel = True
		
		if not cancel:
			cmds.select(cl = True)
			jnt = cmds.joint(n = 'Root')
			jnt = cmds.parent(jnt, parent[0])
			cmds.parent(sel[0], jnt)
			if len(children) > 1:
				children.remove(sel[0])
				cmds.parent(children, jnt)
			cmds.select(self.char, r = True)
		
		cmds.deleteUI(self.rootJointWin)
		
		if cancel:
			cmds.select(self.char, r = True)
			return
		
		self.getRigNodes()
	
	def getSelection(self):
		'''
		get the current selection
		and store the name as the character root node
		'''
		sel = cmds.ls(sl = True)
		if sel == None or not len(sel):
			return False
		self.char = sel[0]
		return True
	
	def getSkinMesh(self):
		'''
		search for any meshes in the selected hierarchy
		which also have a skin cluster attached
		'''
		hier = cmds.listRelatives(self.char, ad = True, f = True)
		if hier == None or not len(hier):
			return False
		
		skinExists = False
		for h in hier:
			if cmds.nodeType(h) == 'transform':
				shape = cmds.listRelatives(h, s = True, f = True)
				if shape != None and len(shape):
					for s in shape:
						if cmds.nodeType(s) == 'mesh':
							self.skinNodes[h.split('|')[-1]] = self.findSkinCluster(s)
							if len(self.skinNodes[h.split('|')[-1]]['skinCluster']):
								skinExists = True
							break
		if len(self.skinNodes.keys()) and skinExists:
			return True
		else:
			return False
	
	def findSkinCluster(self, shape):
		'''
		return the skin cluster and blend shape nodes for the given mesh
		'''
		skinNodes = []
		bsNodes = []
		hist = cmds.listHistory(shape, gl = True, pdo = True, lf = True, f = False, il = 2)
		if hist != None and len(hist):
			for h in hist:
				if cmds.nodeType(h) == 'skinCluster':
					skinNodes.append(h)
				if cmds.nodeType(h) == 'blendShape':
					bsNodes.append(h)
		return {'skinCluster': skinNodes, 'blendShape': bsNodes}
	
	def showRigNodesUI(self):
		'''
		create the window for showing the character meshes
		and skin clusters
		'''
		if cmds.window(self.nodesWin, exists = True):
			cmds.deleteUI(self.nodesWin)
		if cmds.windowPref(self.nodesWin, ex = True):
			cmds.windowPref(self.nodesWin, e = True, w = 230, h = 200)
		cmds.window(self.nodesWin, t = 'Skin Nodes', w = 230, h = 200)
		
		form = cmds.formLayout()
		title = cmds.text(l = 'Selected meshes and skin clusters\nwill be used for the actor.')
		meshLabel = cmds.text(l = 'Skin Mesh', al = 'left')
		self.meshTSL = cmds.textScrollList(ams = True, h = 50, sc = partial(self.updateScrollList, 'mesh'))
		skinLabel = cmds.text(l = 'Skin Cluster', al = 'left')
		self.skinTSL = cmds.textScrollList(ams = True, h = 50, sc = partial(self.updateScrollList, 'skin'))
		bsLabel = cmds.text(l = 'Blend Shapes', al = 'left')
		self.bsTSL = cmds.textScrollList(ams = True, h = 50, sc = partial(self.updateScrollList, 'blendShape'))
		button = cmds.button(l = 'Continue', c = partial(self.createActor))
		
		cmds.formLayout(form, 	e = True, 
								af = ((title, 'top', 5), 
									(title, 'left', 5), 
									(title, 'right', 5), 
									(meshLabel, 'left', 5), 
									(self.meshTSL, 'left', 5), 
									(self.meshTSL, 'right', 5), 
									(skinLabel, 'left', 5), 
									(self.skinTSL, 'left', 5), 
									(self.skinTSL, 'right', 5), 
									(bsLabel, 'left', 5), 
									(self.bsTSL, 'left', 5), 
									(self.bsTSL, 'right', 5), 
									(button, 'left', 5), 
									(button, 'right', 5), 
									(button, 'bottom', 5)), 
								ac = ((meshLabel, 'top', 15, title), 
									(self.meshTSL, 'top', 5, meshLabel), 
									(skinLabel, 'top', 10, self.meshTSL), 
									(self.skinTSL, 'top', 5, skinLabel), 
									
									(bsLabel, 'top', 10, self.skinTSL), 
									(self.bsTSL, 'top', 5, bsLabel), 
									
									(self.bsTSL, 'bottom', 5, button)), 
								ap = ((self.meshTSL, 'bottom', 5, 33), 
									(self.skinTSL, 'bottom', 5, 66)))
		
		cmds.showWindow(self.nodesWin)
		
		# add the found meshes to the list and select them all
		for i in self.skinNodes.keys():
			cmds.textScrollList(self.meshTSL, e = True, a = i, si = i)
			# add the found skin clusters to the list and select them all
			for k in self.skinNodes[i]['skinCluster']:
				cmds.textScrollList(self.skinTSL, e = True, a = k, si = k)
			# add the found blend shape nodes to the list and select them all
			for k in self.skinNodes[i]['blendShape']:
				cmds.textScrollList(self.bsTSL, e = True, a = k, si = k)
	
	def updateScrollList(self, list, *args):
		'''
		select list items based on the user selection
		'''
		if list == 'mesh':
			cmds.textScrollList(self.skinTSL, e = True, da = True)
			cmds.textScrollList(self.bsTSL, e = True, da = True)
			meshes = cmds.textScrollList(self.meshTSL, q = True, si = True)
			if meshes != None:
				for m in meshes:
					for skin in self.skinNodes[m]['skinCluster']:
						cmds.textScrollList(self.skinTSL, e = True, si = skin)
					for bs in self.skinNodes[m]['blendShape']:
						cmds.textScrollList(self.bsTSL, e = True, si = bs)
		elif list == 'skin':
			cmds.textScrollList(self.meshTSL, e = True, da = True)
			cmds.textScrollList(self.bsTSL, e = True, da = True)
			skins = cmds.textScrollList(self.skinTSL, q = True, si = True)
			if skins != None:
				for s in skins:
					for m in self.skinNodes.keys():
						if s in self.skinNodes[m]['skinCluster']:
							cmds.textScrollList(self.meshTSL, e = True, si = m)
							for bs in self.skinNodes[m]['blendShape']:
								cmds.textScrollList(self.bsTSL, e = True, si = bs)
		elif list == 'blendShape':
			pass
	
	def createActor(self, *args):
		'''
		Second step for building the actor
		
		collect all the joints from the selected skin clusters
		and store them in a dictionary
		'''
		# initialize the progress bar
		self.mainProgress = mel.eval('$temp = $gMainProgressBar')
		cmds.progressBar(self.mainProgress, e = True, bp = True, ii = False, max = 6)
		
		self.skinCluster = []
		self.bsNodes = []
		
		# update the mesh and cluster information from the lists
		self.skinMeshes = cmds.textScrollList(self.meshTSL, q = True, si = True)
		self.skinCluster = cmds.textScrollList(self.skinTSL, q = True, si = True)
		for m in self.skinMeshes:
			temp = []
			exists = True
			bs = cmds.textScrollList(self.bsTSL, q = True, si = True)
			if bs != None:
				for b in bs:
					if b in self.skinNodes[m]['blendShape']:
						temp.append(b)
			else:
				exists = False
			self.bsNodes.append(temp[:])
			self.meshHasBs[m] = exists
		
		#print self.skinMeshes, self.skinCluster, self.bsNodes
		
		# get the full path of the meshes because of duplication later
		temp = []
		for i in self.skinMeshes:
			temp.append(str(cmds.ls(i, l = True)[0]))
		self.skinMeshes = temp[:]
		
		cmds.deleteUI(self.nodesWin)
		
		allJoints = []
		# get the influences for each skin cluster and store them in a dictionary
		for c in self.skinCluster:
			jntList = cmds.skinCluster(c, q = True, inf = True)
			if jntList == None or not len(jntList):
				OpenMaya.MGlobal_displayError('%s has no influences. Aborting.' % c)
				cmds.progressBar(self.mainProgress, e = True, ep = True)
				return
			self.joints[c] = jntList
			allJoints.extend(jntList)
		
		# also store all joints names after removing any duplicates
		allJoints = list(set(allJoints))
		self.joints['all'] = allJoints
		
		# create the actor joints based on the found influences
		self.createJoints()
		
	def createJoints(self):
		'''
		Third step for building the actor
		
		build the actual actor joints from the previous collected lists
		and rebuild the hierarchy
		'''
		cmds.progressBar(self.mainProgress, e = True, st = 'Creating Joints ...')
		
		# add the actor message attribute
		if not cmds.objExists(self.actor):
			self.actor = cmds.createNode('transform', n = self.actor)
			cmds.addAttr(self.actor, ln = 'actor', at = 'message')
		cmds.select(cl = True)
		
		# create duplicates of the rig joints
		count = 0
		for j in self.joints['all']:
			if not cmds.objExists('skin_' + j):
				jnt = cmds.joint(n = 'skin_' + j)
				cmds.delete(cmds.pointConstraint(j, jnt))
				cmds.delete(cmds.orientConstraint(j, jnt))
				
				# use the rotation values as orientation values
				jntRot = cmds.getAttr(jnt + '.rotate')[0]
				cmds.setAttr(jnt + '.jointOrient', jntRot[0], jntRot[1], jntRot[2])
				cmds.setAttr(jnt + '.rotate', 0, 0, 0)
				
				cmds.select(cl = True)
				count += 1
		
		cmds.progressBar(self.mainProgress, e = True, s = 1, st = 'Building Hierarchy ...')
		
		# reassemble the hierarchy
		for j in self.joints['all']:
			parent = cmds.listRelatives(j, p = True)
			if parent == None:
				cmds.parent('skin_' + j, self.actor)
			elif cmds.nodeType(parent[0]) == 'joint' and cmds.objExists('skin_' + parent[0]):
				cmds.parent('skin_' + j, 'skin_' + parent[0])
			else:
				cmds.parent('skin_' + j, self.actor)
		
		print ('// %i actor joints created' % count)
		
		# try to re-assembly the resulting hierarchies if any
		for i in range(4, 1, -1):
			rootJnts = cmds.listRelatives(self.actor, c = True)
			if len(rootJnts) > 1:
				print '// trying assembly with precision factor %i' % i
				self.iterateRebuildHierarchy(rootJnts, i)
			else:
				break
		
		cmds.select(self.char, r = True)
		
		# check if the result is a single hierarchy
		self.checkActorHierarchy()
		
	def iterateRebuildHierarchy(self, rootJnts, precision):
		'''
		if there is more than one resulting hierarchy in the actor group
		try to find a joint in the rig hierarchy with the same position
		and use it's parent for the floating hierarchy
		'''
		cmds.select(self.char, hi = True)
		allNodes = cmds.ls(sl = True, tr = True)
		for j in rootJnts:
			jPos = self.round(cmds.xform(j, q = True, ws = True, t = True), precision)
			for node in allNodes:
				pos = self.round(cmds.xform(node, q = True, ws = True, t = True), precision)
				if jPos[0] == pos[0] and jPos[1] == pos[1] and jPos[2] == pos[2] and node != j and cmds.nodeType(node) == 'joint':
					parent = cmds.listRelatives(node, p = True)
					if parent != None and len(parent):
						if cmds.nodeType(parent[0]) == 'joint' and parent[0] in self.joints['all'] and j != 'skin_' + parent[0]:
							print '// parenting %s to %s' % (j, 'skin_' + parent[0])
							cmds.parent(j, 'skin_' + parent[0])
		cmds.select(cl = True)
	
	def checkActorHierarchy(self, *args):
		'''
		Fourth step for building the actor
		
		check if the joint result is a single hierarchy
		if the previous step was not successful user interaction is requested
		if successful finish the rig process:
		- build the optional root joint
		- copy the skin weights
		- export the rigs and reference them
		- connect the rigs in the master scene
		'''
		# check if the result is a single hierarchy
		children = cmds.listRelatives(self.actor, c = True)
		if len(children) > 1:
			# check for an existing hierarchy file
			if os.path.exists('%s/data/hierarchyEdit.txt' % self.actorPath):
				self.useDescription = False
				result = cmds.confirmDialog(	t = 'Actor Tools', 
												m = 'An existing description was found to rebuild a single hierarchy.\nDo you want to apply this description?', 
												b = ['Yes', 'No'], 
												db = 'Yes', 
												cb = 'No', 
												ds = 'No')
				if result == 'Yes':
					self.useDescription = True
					lines = self.readDescription('%s/data/hierarchyEdit.txt' % self.actorPath)
					for line in lines:
						mel.eval(line)
					self.checkActorHierarchy()
					return
			
			self.reParent = children[:]
			cmds.button(self.rigButton, e = True, l = 'Finish Actor Rig', c = partial(self.checkActorHierarchy))
			cmds.confirmDialog(	t = 'Actor Tools', 
								m = 'Actor Tools was unable to rebuild a single hierarchy.\nRebuild the character\'s hierarchy in the actor_grp and press\nFinish Actor Rig to complete the process.', 
								b = ['OK'], 
								db = 'OK', 
								cb = 'OK', 
								ds = 'OK')
			return False
		else:
			if len(self.reParent):
				if not self.useDescription:
					self.saveCustomParenting()
				del self.reParent[:]
			
			cmds.button(self.rigButton, e = True, l = 'Create Actor', c = partial(self.getRigNodes))
			self.root = children[0]
			if cmds.checkBoxGrp(self.rootCheck, q = True, v1 = True):
				self.createActorRootJoint()
			
			cmds.progressBar(self.mainProgress, e = True, s = 1, st = 'Perform Skinning ...')
			self.createSkin()
			
			cmds.progressBar(self.mainProgress, e = True, s = 1, st = 'Creating Blend Shapes ...')
			self.createBlendShapes()
			
			cmds.progressBar(self.mainProgress, e = True, s = 1, st = 'Exporting Rigs ...')
			self.exportRigs()
			
			cmds.progressBar(self.mainProgress, e = True, s = 1, st = 'Connecting Rigs ...')
			self.connectRigs()
			
			cmds.progressBar(self.mainProgress, e = True, ep = True)
			
			cmds.file(save = True)
			cmds.button(self.masterButton, e = True, en = True)
			self.listCharacters()
			
			cmds.optionVar(iv = ('actorToolsCreateRootNodeCheck', cmds.checkBoxGrp(self.rootCheck, q = True, v1 = True)))
	
	def saveCustomParenting(self):
		'''
		compare the resulting joint hierarchy with the one before
		the manual assembly and store the parenting to a file
		which can be used to automate the process in future builds of the actor
		'''
		children = cmds.listRelatives(self.actor, c = True)
		cmd = ''
		for i in self.reParent:
			if not i in children:
				parent = cmds.listRelatives(i, p = True)
				if parent != None and len(parent):
					cmd += 'parent %s %s;\n' % (i, parent[0])
		if cmd != '':
			self.writeDescription('%s/data/hierarchyEdit.txt' % self.actorPath, cmd)
	
	def createActorRootJoint(self):
		'''
		create an optional root joint at the world origin
		in case the targeted engine requires it
		'''
		cmds.select(cl = True)
		jnt = cmds.joint(n = 'Root')
		jnt = cmds.parent(jnt, self.actor)
		cmds.parent(self.root, jnt)
		self.root = jnt
		cmds.select(cl = True)
	
	def createSkin(self):
		'''
		create the skinning for the actor
		by duplicating the meshes, applying a basic skin cluster
		and copying the skin weights
		'''
		# create the geometry group
		grp = cmds.createNode('transform')
		cmds.parent(grp, self.actor)
		grp = cmds.rename(grp, 'geo_grp')
		
		# duplicate all chosen skin meshes
		self.actorMeshes = {}
		for i in self.skinMeshes:
			mesh = cmds.duplicate(i, rr = True, rc = True)
			# delete any transform children
			children = cmds.listRelatives(mesh[0], c = True, typ = 'transform')
			if children != None and len(children):
				cmds.delete(children)
			# remove unnecessary intermediate shapes
			allShapes = cmds.listRelatives(mesh[0], s = True)
			shape = cmds.listRelatives(mesh[0], s = True, ni = True)
			for s in allShapes:
				if not s in shape:
					cmds.delete(s)
			
			cmds.parent(mesh[0], grp)
			self.actorMeshes[i] = cmds.rename(mesh[0], i.split('|')[-1])
			
			# duplicate the mesh for the blend shape setup
			# if the mesh has a blend shape node
			if self.meshHasBs[i.split('|')[-1]]:
				self.createBlendShapeBase(self.actorMeshes[i])
		
		# move the geo group above the joints
		cmds.reorder(grp, r = -1)
		
		# create the skin clusters and copy the weights
		for j, i in enumerate(self.skinCluster):
			# select all related joints
			joints = []
			for jnt in self.joints[self.skinCluster[j]]:
				joints.append('skin_' + jnt)
			cmds.select(joints, r = True)
			cmds.select(self.actorMeshes[self.skinMeshes[j]], add = True)
			
			norm = cmds.getAttr(i + '.normalizeWeights')
			maxInf = cmds.getAttr(i + '.maxInfluences')
			dropoff = cmds.getAttr(i + '.dropoff')[0][0]
			
			flags = '-nw %s -mi %s -dr %s' % (norm, maxInf, dropoff)
		
			# check for the version
			# up to Maya 2012 the bind method flag is not available
			version = mel.eval('getApplicationVersionAsFloat()')
			bindMethod = '-bm 0 '
			if version < 2013:
				bindMethod = '-ih '
		
			# create the new skinCluster
			newSkinCluster = mel.eval('newSkinCluster \"-tsb ' + bindMethod + flags + '-omi true -rui false\"')[0]
			cmds.rename(newSkinCluster, i + '_actor')
			
			# copy the weights from the rig mesh
			cmds.select([self.skinMeshes[j], self.actorMeshes[self.skinMeshes[j]]], r = True)
			cmds.copySkinWeights(nm = True, sa = 'closestPoint', ia = 'closestJoint')
	
	def createBlendShapeBase(self, mesh):
		'''
		duplicate the skin mesh for the blend shape setup
		and group it
		'''
		name = mesh.split('|')[-1]
		grp = cmds.createNode('transform', n = name + '_bs_grp')
		base = cmds.duplicate(mesh, rr = True, rc = True)
		cmds.parent(base, grp)
		cmds.rename(base, name + '_bsBase')	
	
	def createBlendShapes(self):
		'''
		extract the blend shape targets and
		re-create them on a new blend shape node for the actor
		'''
		bsData = self.getBlendShapeData()
		#print bsData
		
		# clear the original blend shape nodes list to contain
		# only the nodes which are used and contain targets
		# this is necessary for connecting the blend shape nodes
		# for the master setup
		self.bsNodes = []
		
		cmd = ''
		setupList = bsData.keys()
		for setup in setupList:
			bsNodes = bsData[setup].keys()
			for bs in bsNodes:
				if len(bsData[setup][bs]):
					self.bsNodes.append(bs)
					bsNode = bs + '_actor'
					skin = self.actorMeshes[setup]
					cmd += 'deformer -type blendShape -foc -n %s %s;\n' % (bsNode, skin)
					targetList = bsData[setup][bs]
					for t in targetList:
						counter = 0
						values = t['values']
						meshName = setup.split('|')[-1]
						for v in values:
							target = self.extractTarget(bs, t['target'], t['index'], v, meshName)
							if target == None:
								cmds.progressBar(self.mainProgress, e = True, ep = True)
								return
							if v == 6000:
								cmd += 'blendShape -e -t %s %s %s %s %s;\n' % (skin, str(t['index']), target, str((v - 5000) / 1000.0), bsNode)
							else:
								target = cmds.rename(target, t['target'] + '_inbetween' + str(counter))
								cmd += 'blendShape -e -ib -t %s %s %s %s %s;\n' % (skin, str(t['index']), target, str((v - 5000) / 1000.0), bsNode)
								counter += 1
			
			# delete the duplicated original mesh
			if self.meshHasBs[setup.split('|')[-1]]:
				cmds.delete(setup.split('|')[-1] + '_bsBase')
		
		try:
			mel.eval(cmd)
		except:
			cmds.progressBar(self.mainProgress, e = True, ep = True)
			return
		
		# delete the groups with the blend shape targets
		for i in self.skinMeshes:
			if self.meshHasBs[i.split('|')[-1]]:
				cmds.delete(self.actorMeshes[i].split('|')[-1] + '_bs_grp')
		
	def getBlendShapeData(self):
		'''
		return the blend shape data as a dictionary
		{'geo1': {u'bsNode2': [{'index': 0, 'values': [6000], 'target': 'armLift'}]}, 'geo2': {u'bsNode2': []}}
		'''
		expr = re.compile('\d+')
		
		bsData = {}
		for i, meshBs in enumerate(self.bsNodes):
			bsDict = {}
			for bsNode in meshBs:
				nodeData = []
				if len(bsNode):
					# list all targets in order with their alias names if existing
					aliasList = cmds.aliasAttr(bsNode, q = True)
					if aliasList != None:
						for a in range(0, len(aliasList), 2):
							target = aliasList[a]
							index = int(expr.findall(aliasList[a + 1])[0])
					
							valueList = cmds.listAttr('%s.it[0].itg[%i].iti' % (bsNode, index), a = True, m = True)
							valueArray = []
							if valueList != None:
								for v in valueList:
									valueArray.append(int(expr.findall(v)[-1]))
						
								targetDict = {}
								targetDict['index'] = index
								targetDict['target'] = str(target)
						
								# sort the inbetweens and put the base at index 0
								values = list(set(valueArray))
								values.sort()
								values.pop(len(values) - 1)
								values.insert(0, 6000)
								targetDict['values'] = values
						
								nodeData.append(targetDict)
				bsDict[bsNode] = nodeData
			bsData[self.skinMeshes[i]] = bsDict
		
		return bsData
	
	def extractTarget(self, bsNode, target, index, value, original):
		'''
		extract the given blendshape target by index and value (for inbetweens)
		and build a new mesh from it
		'''
		inbetweenName = ''
		if value != 6000:
			inbetweenName = '_inbetween'
		
		rebuild = []
		
		# check if a mesh is still connected to the target channel
		# need to disconnect to get the point data from the channel
		connect = cmds.listConnections(bsNode + '.it[0].itg[' + str(index) + '].iti[' + str(value) + '].igt', p = True)
		if connect != None:
			cmds.disconnectAttr(connect[0], bsNode + '.it[0].itg[' + str(index) + '].iti[' + str(value) + '].igt')
			print '// %s has been disconnected from %s to be able to read the target channel.' % (connect[0], bsNode)
			rebuild.append(connect[0])
			rebuild.append(bsNode + '.it[0].itg[' + str(index) + '].iti[' + str(value) + '].igt')
	
		# get the components and the point array
		points = cmds.getAttr(bsNode + '.it[0].itg[' + str(index) + '].iti[' + str(value) + '].ict')
		pos = cmds.getAttr(bsNode + '.it[0].itg[' + str(index) + '].iti[' + str(value) + '].ipt')
	
		# get the name of the target to be extracted
		name = target + inbetweenName
	
		# duplicate the original mesh
		target = cmds.duplicate(original + '_bsBase', rc = True)
		target = cmds.rename(target[0], name)
		cmds.setAttr(target + '.v', 0)
	
		# create a duplicate for the temporary blendshape target
		# this is needed to be able to write the point data
		temp = cmds.duplicate(target, rc = True)
	
		tempBS = cmds.blendShape(temp, target)
		cmds.blendShape(tempBS, e = True, w = [(0, 1)])
		cmds.delete(temp[0])
	
		# flatten the component list
		# cover the case where the target channel contains no actual point data
		if points != None and len(points):
			compList = self.flattenComponentList(points, 'string')
		else:
			OpenMaya.MGlobal_displayError('Unable to read the blend shape channel data')
			cmds.delete(target)
			return
	
		# transfer the blendshape target values to the temporary blendshape target
		cmds.setAttr(tempBS[0] + '.it[0].itg[0].iti[6000].ict', len(compList), *compList, type = 'componentList')
		cmds.setAttr(tempBS[0] + '.it[0].itg[0].iti[6000].ipt', len(pos), *pos, type = 'pointArray')
	
		# cleanup
		cmds.select(target, r = True)
		cmds.delete(ch = True)
		cmds.sets(target, e = True, fe = 'initialShadingGroup')
		cmds.select(cl = True)
		
		if len(rebuild):
			for r in range(0, len(rebuild), 2):
				cmds.connectAttr(rebuild[r], rebuild[r + 1], f = True)
				print '// %s has been re-connected to %s.' % (rebuild[r], bsNode)
		
		return target
	
	def flattenComponentList(self, compList, mode = 'string'):
		'''
		take a mixed component list from a blendshape channel [u'vtx[5]', u'vtx[7:25]']
		and return it as a flattened list ['vtx[5]', 'vtx[7]', 'vtx[8]', ...
		'''
		ids = []
		flatList = []
		expr = re.compile('\d+')
		for c in compList:
			ids = expr.findall(c)
	
			if len(ids) == 1:
				if mode == 'string':
					flatList.append('vtx[%i]' % int(ids[0]))
				else:
					flatList.append(int(ids[0]))
			else:
				idRange = range(int(ids[0]), int(ids[1]) + 1)
				for i in idRange:
					if mode == 'string':
						flatList.append('vtx[%i]' % i)
					else:
						flatList.append(i)
		return flatList
	
	def exportRigs(self):
		'''
		export the rigs and create version files
		create a master scene and reference the rigs
		'''
		# get the camera position
		# to rebuild the same camera position in the master scene
		pos = cmds.xform('persp', q = True, m = True)
		
		# get the current file type
		ext = cmds.file(q = True, sn = True).split('.')[-1]
		fileType = 'mayaAscii'
		if ext == 'mb':
			fileType = 'mayaBinary'
		else:
			ext = 'ma'
		
		# export the rig
		fileNameRig = '%s/rig/%s.%s' % (self.actorPath, self.name, ext)
		cmds.select(self.char, r = True)
		cmds.file(fileNameRig, f = True, op = 'v=0', typ = fileType, es = True)
		print '// Saved rig to %s' % fileNameRig
		
		# export the rig version by copying the rig file
		fileVersion = self.getFileVersion(self.actorPath + '/rig/versions', self.name, ext)
		shutil.copy(str(fileNameRig), str(fileVersion))
		print '// Saved rig version to %s' % fileVersion
		
		# export the actor
		fileNameActor = '%s/actor/%s.%s' % (self.actorPath, self.name, ext)
		cmds.select(self.actor, r = True)
		cmds.file(fileNameActor, f = True, op = 'v=0', typ = fileType, es = True)
		print '// Saved actor to %s' % fileNameActor
		# open the actor file to rename the group node to match the character group node
		cmds.file(fileNameActor, f = True, op = 'v=0', typ = fileType, o = True)
		cmds.rename(self.actor, self.char)
		cmds.file(save = True)
		
		# export the actor version by copying the rig file
		fileVersion = self.getFileVersion(self.actorPath + '/actor/versions', self.name, ext)
		shutil.copy(str(fileNameActor), str(fileVersion))
		print '// Saved actor version to %s' % fileVersion
		
		# create the master scene
		cmds.file(f = True, new = True)
		cmds.xform('persp', m = pos)
		self.setCameraCenterOfInterest()
		
		# reference the rigs
		cmds.file(fileNameRig, r = True, typ = fileType, op = 'v=0', iv = True, gl = True, mnc = False, ns = 'rig')
		cmds.file(fileNameActor, r = True, typ = fileType, op = 'v=0', iv = True, gl = True, mnc = False, ns = 'actor')
		# rename and save
		cmds.file(rn = '%s/%s_exportMaster' % (self.actorPath, self.name))
		cmds.file(save = True, typ = fileType)
	
	# --------------------------------------------------------------------------------------------------
	# master scene
	# --------------------------------------------------------------------------------------------------
	
	def connectRigs(self):
		'''
		parent constraint the actor joints to the rig joints
		'''
		for i in self.skinCluster:
			for jnt in self.joints[i]:
				cmds.parentConstraint('rig:' + jnt, 'actor:skin_' + jnt, mo = True)
			print '// Connected %i joints' % len(self.joints[i])
		
		for bsNode in self.bsNodes:
			attrList = cmds.listAttr('rig:%s.w' % bsNode, m = True)
			for a in attrList:
				cmds.connectAttr('rig:%s.%s' % (bsNode, a), 'actor:%s_actor.%s' % (bsNode, a), f = True)
			print '// Connected %i blend shape attributes' % len(attrList)
		
		if cmds.checkBoxGrp(self.rootCheck, q = True, v1 = True):
			cmds.parentConstraint('rig:Root', 'actor:Root', mo = True)
	
	def loadMasterScene(self, *args):
		'''
		load the master scene based on the currently selected character
		'''
		path = self.getMasterScenePath('', '%s_exportMaster' % self.name)
		if path != '':
			cmds.file(path, f = True, op = 'v=0', o = True)
	
	def getMasterScenePath(self, subPath, fileName):
		'''
		return the file name at the given path including the extension
		'''
		path = ''
		if os.path.exists(self.actorPath + subPath):
			items = os.listdir(self.actorPath + subPath)
			for i in items:
				if fileName in i:
					path = '%s/%s' % (self.actorPath + subPath, i)
					break
		return path
	
	def removeNameSpace(self, array):
		'''
		remove the namespace from all items in the given array
		'''
		return [a.split(':')[-1] for a in array]
	
	# --------------------------------------------------------------------------------------------------
	# export/import animation
	# --------------------------------------------------------------------------------------------------
	
	def exportAnimation(self, *args):
		'''
		export the animation for the currently selected group node
		
		- check for all transform nodes which have time based animation curves
		- select all animated nodes
		- export the animation for the current selection via ATOM
		- store the selection in a description file in the same folder where the animation file is stored
		'''
		if self.char == '':
			OpenMaya.MGlobal_displayError('No character selected')
			return
		
		sel = cmds.ls(sl = True, tr = True)
		if sel == None or not len(sel):
			OpenMaya.MGlobal_displayError('Select the character group node')
			return
		
		if sel[0].split(':')[-1] != self.char:
			OpenMaya.MGlobal_displayError('The selected character group node does not match the current character')
			return
		
		animFile = cmds.textFieldButtonGrp(self.animFileField, q = True, tx = True)
		if sel == None or not len(sel):
			OpenMaya.MGlobal_displayError('No file name set')
			return
		
		cmds.select(sel[0], r = True, hi = True)
		hier = cmds.ls(sl = True, tr = True)
		cmds.select(cl = True)
		
		controls = []
		curves = ['animCurveTA', 'animCurveTT', 'animCurveTL', 'animCurveTU']
		for h in hier:
			conn = cmds.listConnections(h, s = True, d = False, p = True)
			if conn != None and len(conn):
				for c in conn:
					if cmds.nodeType(c.split('.')[0]) in curves:
						controls.append(h)
		
		# remove any double items in the controls list
		controls = list(set(controls))
		if not len(controls):
			OpenMaya.MGlobal_displayError('Character is not animated')
			return
		
		# select the controls because export is based on selection
		cmds.select(controls, r = True)
		
		# use ATOM export
		fileName = '%s/animations/%s.atom' % (self.actorPath, animFile)
		cmds.file(fileName, f = True, op = 'precision=8;statics=1;baked=1;sdk=0;constraint=0;animLayers=1;selected=selectedOnly;whichRange=1;range=1:10;hierarchy=none;controlPoints=0;useChannelBox=1;options=keys;copyKeyCmd=-animation objects -option keys -hierarchy none -controlPoints 0', typ = 'atomExport' , es = True)
		
		# save the control names to the description file which is needed for importing the animation
		controls = self.removeNameSpace(controls)
		self.writeDescription('%s/animations/%s.txt' % (self.actorPath, animFile), ' '.join(controls))
		
	def loadAnimation(self, *args):
		'''
		let the user choose an ATOM file
		also read the related description file
		for selecting the nodes for the import
		'''
		if self.char == '':
			OpenMaya.MGlobal_displayError('No character selected')
			return
		
		if not cmds.objExists('rig:' + self.char):
			OpenMaya.MGlobal_displayError('Wrong character loaded')
			return
		
		filter = 'atomImport (*.atom)'
		path = '%s/animations' % self.actorPath
		fileName = cmds.fileDialog2(dir = path, fm = 4, ff = filter, okc = 'Import', cap = 'Select Animation File')
		if not fileName:
			return
		
		# read the description file and select the nodes
		descFile = fileName[0].split('.')[0] + '.txt'
		lines = self.readDescription(descFile)
		controls = lines[0].split(' ')
		controls = ['rig:' + c for c in controls]
		cmds.select(cl = True)
		for c in controls:
			if not cmds.objExists(c):
				OpenMaya.MGlobal_displayError('Skipped node %s because it doesn\'t exist. Aborting.' % c)
				return
		cmds.select(controls, r = True)
		
		# import the animation
		cmds.file(fileName[0], i = True, ra = True, typ = 'atomImport', op = ';;targetTime=3;option=insert;match=hierarchy;;selected=selectedOnly;search=;replace=;prefix=;suffix=;mapFile=;')
		# display the time range based on the atom file
		frameList = self.getAtomTimeRange(fileName[0])
		cmds.floatFieldGrp(self.frameRange, e = True, v1 = float(frameList[0]), v2 = float(frameList[1]))
		
		# display the file name for the export
		cmds.textFieldButtonGrp(self.exportFileField, e = True, tx = ('%s_%s' % (self.name, os.path.basename(fileName[0]).split('.')[0])))

	def getAtomTimeRange(self, file):
		'''
		return the start and end frames from the given ATOM file
		'''
		lines = self.readDescription(file)
		start = lines[6].replace(';', '').split(' ')[-1]
		end = lines[7].replace(';', '').split(' ')[-1]
		return [start, end]
	
	# --------------------------------------------------------------------------------------------------
	# actor export
	# --------------------------------------------------------------------------------------------------
	
	def getReferencedBlendShapeAttributes(self, group):
		'''
		returns a list with all blend shape nodes and attributes
		from all referenced blend shape nodes
		'''
		refNode = cmds.referenceQuery('actor:%s' % self.char, rfn = True)
		nodes = cmds.referenceQuery(refNode, n = True)
		attrList = []
		bsNodes = []
		for n in nodes:
			if cmds.nodeType(n) == 'blendShape':
				attrList.extend(cmds.listAttr(n + '.w', m = True))
				bsNodes.append(n)
		attrList = list(set(attrList))
		return [bsNodes, attrList]
	
	def exportActor(self, *args):
		'''
		bake the animation and export the actor rig
		'''
		if self.char == '':
			OpenMaya.MGlobal_displayError('No character selected')
			return
		
		actor = 'actor:' + self.char
		
		if not cmds.objExists(actor):
			OpenMaya.MGlobal_displayError('Wrong character loaded')
			return
		
		if not cmds.attributeQuery('actor', node = actor, ex = True):
			OpenMaya.MGlobal_displayError('The actor group is not valid')
			return
		
		joints = cmds.listRelatives(actor, c = True, type = 'joint')
		if joints == None or not len(joints):
			OpenMaya.MGlobal_displayError('The actor group does not contain any joints')
			return
		
		if not cmds.menuItem(self.exportMenuItem, q = True, cb = True):
			if cmds.textFieldButtonGrp(self.exportFileField, q = True, tx = True) == '':
				OpenMaya.MGlobal_displayError('No export file name set')
				return
		
		'''
		confirm = cmds.confirmDialog(	t = 'Publish Actor', 
										m = 'Save the scene before publishing?\n\nAny unsaved changes will get lost after publishing.', 
										b = ('Save', 'Continue', 'Cancel'), 
										db = 'Save', 
										cb = 'Cancel', 
										ds = 'Cancel', 
										icn = 'warning')
		if confirm == 'Save':
			cmds.file(save = True)
		elif confirm == 'Cancel':
			return
		'''
		
		bsChannels = self.getReferencedBlendShapeAttributes(actor)
		attrList = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
		attrList.extend(bsChannels[1])
		
		bakeNodes = [actor]
		bakeNodes.extend(bsChannels[0])
		
		# get the frame range and bake the selected actor
		startFrame = cmds.floatFieldGrp(self.frameRange, q = True, v1 = True)
		endFrame = cmds.floatFieldGrp(self.frameRange, q = True, v2 = True)
		cmds.select(actor, r = True)
		cmds.bakeResults(bakeNodes,	simulation = True, 
									t = (startFrame, endFrame), 
									hi = 'below', 
									sampleBy = 1, 
									disableImplicitControl = True, 
									preserveOutsideKeys = True, 
									sparseAnimCurveBake = False, 
									at = attrList)
		
		# delete the constraints
		cmds.delete(cmds.listRelatives(actor, ad = True, type = 'parentConstraint'))
		
		# make sure skins and blend shapes are exported
		mel.eval('FBXExportSkins -v 1')
		mel.eval('FBXExportShapes -v 1')
		
		cmds.select(actor, r = True)
		
		# check if the advanced export is selected
		# use the default Maya export command to let the user choose the export path and format
		if cmds.menuItem(self.exportMenuItem, q = True, cb = True):
			# store the currently selected export format
			format = cmds.optionVar(q = 'defaultFileExportActiveType')
			cmds.optionVar(sv = ('defaultFileExportActiveType', 'FBX export'))
			mel.eval('ExportSelection')
			# set the export format back
			cmds.optionVar(sv = ('defaultFileExportActiveType', format))
		else:
			fileName = cmds.textFieldButtonGrp(self.exportFileField, q = True, tx = True)
			fileName = '%s/export/%s.fbx' % (self.actorPath, fileName)
			mel.eval('FBXExport -f "%s" -s' % fileName)
			print '// Exported actor to %s' % fileName
			
		if cmds.checkBoxGrp(self.reviewCheck, q = True, v1 = True):
			pos = cmds.xform('persp', q = True, m = True)
			cmds.file(f = True, new = True)
			cmds.xform('persp', m = pos)
			cmds.file(fileName, i = True, typ = 'FBX', iv = True, op = 'fbx', pr = True, mnc = False)
		
		# set the preferences
		cmds.optionVar(iv = ('actorToolsAdvancedExportCheck', cmds.menuItem(self.exportMenuItem, q = True, cb = True)))
		cmds.optionVar(iv = ('actorToolsReviewAfterExportCheck', cmds.checkBoxGrp(self.reviewCheck, q = True, v1 = True)))
