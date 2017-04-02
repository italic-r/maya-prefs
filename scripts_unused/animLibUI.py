from animLib import *
import presetsUI
import xferAnimUI


__author__ = 'mel@macaronikazoo.com'
ui = None

def d_restoreLibrarySelection(f):
	'''
	restores the library selection - mainly used to retain selection when the library list is refreshed
	'''
	def func(*args, **kwargs):
		self = args[0]
		initialSelection = cmd.textScrollList(self.UI_libraries, q=True, si=True)
		try:
			ret = f(*args, **kwargs)
		except:
			raise
		finally:
			if initialSelection:
				for s in initialSelection:
					cmd.textScrollList(self.UI_libraries, e=True, si=s)

		return ret
	return func

class AnimLibUI(utils.Singleton):
	kOPT_SHOW_OPTIONS = 'animLibShowOptions'
	def __init__( self ):
		self.windowName = 'animLibWindow'

		self.clipUIs = []
		self.manager = ClipManager()

		if cmd.window(self.windowName, ex=True):
			cmd.deleteUI(self.windowName)
			cmd.windowPref(self.windowName, remove=True)

		self.windowName = cmd.window(self.windowName, wh=(800,400), mb=True)

		self.UI_form = cmd.formLayout()

		libraryWidth = 165
		self.UI_lbl_libraries = cmd.text(l='clip libraries')
		self.UI_libraries = cmd.textScrollList(width=libraryWidth, sc=self.onSelectLibrary, ann="this is the list of libraries found for the project you're currently vproject'd to.  to create a new library click on the 'new library' button below")
		self.UI_button_newLib = cmd.button(l='new library', w=libraryWidth, c=self.onNewLibrary, ann="to create a new library click here - libraries are ways of organising clips.  they can be organised in any way you see fit")
		cmd.popupMenu(p=self.UI_libraries, pmc=self.buildLibraryMenu)

		self.UI_lbl_filter = cmd.text(l='filter')
		self.UI_filter = cmd.textField(w=250, cc=self.setFilter, ann='enter a search term in here to display only clips that match')
		cmd.popupMenu(p=self.UI_filter, pmc=self.buildFilterMenu)

		self.UI_localeForm = cmd.formLayout()
		self.UI_lbl_local = cmd.text('local clips')
		ann = 'local clips are stored on your computer and only you can see them - to publish a clip so that everyone can use it, right click on the slider'
		self.UI_scroll_local = cmd.scrollLayout(childResizable=True, ann=ann)
		self.UI_column_local = cmd.columnLayout(adj=True, ann=ann)
		cmd.popupMenu(p=self.UI_scroll_local, pmc=self.buildEmptyMenu)

		cmd.setParent(self.UI_localeForm)
		self.UI_lbl_global = cmd.text('global clips')
		self.UI_sync = cmd.button(l='sync to global clips', w=150, c=self.onSync, ann="press this to sync to the latest clip libraries for your project")
		ann = 'these are the global clips - everyone can see global clips for a project.  global clips are managed by perforce, so when someone publishes a clip, you need to sync before it shows up here'
		self.UI_scroll_global = cmd.scrollLayout(childResizable=True, ann=ann)
		self.UI_column_global = cmd.columnLayout(adj=True, ann=ann)
		cmd.popupMenu(p=self.UI_scroll_global, pmc=self.buildEmptyMenu)

		self.localeUI = {LOCAL: self.UI_column_local, GLOBAL: self.UI_column_global}

		cmd.setParent(self.UI_localeForm)
		optionsCollapsed = cmd.optionVar(q=self.kOPT_SHOW_OPTIONS)
		self.UI_frame_options = cmd.frameLayout(l="options", la='bottom', cll=True, cl=optionsCollapsed, cc=lambda *x: cmd.optionVar(iv=(self.kOPT_SHOW_OPTIONS, 1)), ec=lambda *x: cmd.optionVar(rm=self.kOPT_SHOW_OPTIONS), bs='etchedOut')
		#self.UI_form_options = cmd.formLayout()
		colWidth = 175
		self.UI_row_options = cmd.rowLayout(nc=3, cw=((1, colWidth), (2, colWidth)))

		self.UI_opt_offset = cmd.checkBox(l='load clip at current time', v=True, ann="if turned on, all keys are imported starting at the current time.  if off, all keys are imported at the same times they were exported from")
		def onCC(*x):
			if x[0] == 'false': cmd.checkBox(self.UI_opt_additiveWorld, e=True, v=False)
		self.UI_opt_additive = cmd.checkBox(l='load clip additively', cc=onCC, ann="all values are added to current values upon load")
		def onCC(*x):
			if x[0] == 'true': cmd.checkBox(self.UI_opt_additive, e=True, v=True)
		self.UI_opt_additiveWorld = cmd.checkBox(l='load clip additively in world', cc=onCC, ann="attempts to figure out which objects are moving in world space and loads translation for those objects additively, and all other objects normally")

		cmd.setParent(self.UI_localeForm)
		self.UI_button_newPose = cmd.button(l='new pose clip', en=False, bgc=(0.6, 0.75, 0.6), c=self.onNewPose, ann="creates a new pose clip using the currently selected objects")
		self.UI_button_newAnim = cmd.button(l='new anim clip', en=False, c=self.onNewAnim)

		cmd.setParent(self.UI_form)
		self.helpLine = cmd.helpLine()

		cmd.formLayout(self.UI_form, e=True,
					   af=((self.UI_lbl_libraries, 'top', 3),
						   (self.UI_lbl_libraries, 'left', 5),
						   (self.UI_libraries, 'left', 2),
						   (self.UI_lbl_filter, 'top', 3),
						   (self.UI_filter, 'top', 0),
						   (self.UI_filter, 'right', 0),
						   (self.UI_localeForm, 'right', 0),
						   (self.UI_button_newLib, 'left', 2),
						   (self.helpLine, 'left', 0),
						   (self.helpLine, 'right', 0),
						   (self.helpLine, 'bottom', 0)),
					   ac=((self.UI_libraries, 'top', 3, self.UI_lbl_libraries),
						   (self.UI_libraries, 'bottom', 2, self.UI_button_newLib),
						   (self.UI_lbl_filter, 'right', 3, self.UI_filter),
						   (self.UI_localeForm, 'top', 0, self.UI_filter),
						   (self.UI_button_newLib, 'bottom', 0, self.helpLine),
						   (self.UI_localeForm, 'left', 5, self.UI_libraries),
						   (self.UI_localeForm, 'bottom', 0, self.helpLine)))
		cmd.formLayout(self.UI_localeForm, e=True,
					   af=((self.UI_lbl_local, 'top', 3),
						   (self.UI_lbl_local, 'left', 3),
						   (self.UI_scroll_local, 'left', 0),
						   (self.UI_lbl_global, 'top', 3),
						   (self.UI_sync, 'top', 0),
						   (self.UI_sync, 'right', 0),
						   (self.UI_scroll_global, 'right', 0),
						   (self.UI_frame_options, 'left', 0),
						   (self.UI_frame_options, 'right', 0),
						   (self.UI_button_newPose, 'left', 0),
						   (self.UI_button_newPose, 'bottom', 0),
						   (self.UI_button_newAnim, 'right', 0),
						   (self.UI_button_newAnim, 'bottom', 0)),
					   ac=((self.UI_scroll_local, 'top', 3, self.UI_lbl_local),
						   (self.UI_scroll_global, 'top', 3, self.UI_lbl_global),
						   (self.UI_sync, 'bottom', 0, self.UI_scroll_global),
						   (self.UI_scroll_local, 'bottom', 0, self.UI_frame_options),
						   (self.UI_scroll_global, 'bottom', 0, self.UI_frame_options),
						   (self.UI_frame_options, 'bottom', 0, self.UI_button_newPose)),
					   ap=((self.UI_lbl_global, 'left', 5, 50),
						   (self.UI_scroll_local, 'right', 1, 50),
						   (self.UI_scroll_global, 'left', 1, 50),
						   (self.UI_button_newPose, 'right', 1, 50),
						   (self.UI_button_newAnim, 'left', 1, 50)))

		cmd.showWindow(self.windowName)
		self.populateLibraries()

		reportUsageToAuthor()

	### POPUPS
	def buildFilterMenu( self, parent, *args ):
		cmd.setParent(parent, m=True)
		cmd.menu(parent, e=True, dai=True)

		pm = PresetManager(TOOL_NAME, 'filter')
		existingFilters = pm.listPresets(LOCAL)
		if existingFilters:
			for filter in existingFilters:
				cmd.menuItem(l=filter.name(), c=api.Callback(self.setFilter, filter.name()))
			cmd.menuItem(d=True)

		def onSave(*x):
			Preset(LOCAL, TOOL_NAME, self.getFilter(), 'filter').write('')
		cmd.menuItem(l='clear', en=bool(self.getFilter()), c=lambda *x: self.setFilter(''))
		cmd.menuItem(l='save preset', en=bool(self.getFilter()), c=onSave)
		cmd.menuItem(d=True)
		cmd.menuItem(l='manage presets', c=lambda *x: presetsUI.load(TOOL_NAME, ext='filter'))
	def buildEmptyMenu( self, parent, *args ):
		cmd.setParent(parent, m=True)
		cmd.menu(parent, e=True, dai=True)
		isGlobal = False

		if args[0] == self.UI_scroll_global:
			isGlobal = True

		selectedLib = self.getSelectedLibrary()
		selectedLibLoc = self.manager.getPathToLibrary(selectedLib, GLOBAL if isGlobal else LOCAL)
		if selectedLib is None:
			cmd.menuItem(l="please select a library")

		cmd.menuItem(l="create new pose clip", c=self.onNewPose)
		cmd.menuItem(l="create new anim clip", c=self.onNewAnim)

		cmd.menuItem(d=True)
		api.addExploreToMenuItems(selectedLibLoc)
		if isGlobal:
			cmd.menuItem(d=True)
			cmd.menuItem(l="sync to library", c=self.onSync)
		cmd.menuItem(d=True)
		cmd.menuItem(l="refresh", c=lambda *x: self.refreshClips())
	def buildLibraryMenu( self, parent, *args ):
		cmd.setParent(parent, m=True)
		cmd.menu(parent, e=True, dai=True)

		cmd.menuItem(l="create new library", c=self.onNewLibrary)

	### CALLBACKS
	def onSelectLibrary( self, *args ):
		self.setSelectedLibrary(self.getSelectedLibrary())
	def onNewLibrary( self, *args ):
		BUTTONS = OK, CANCEL = 'OK', 'Cancel'
		ans = cmd.promptDialog(t='enter library name', m='enter the library name:', b=BUTTONS, db=OK)
		if ans == CANCEL:
			return

		name = cmd.promptDialog(q=True, tx=True)
		self.manager.createLibrary(name)

		self.refreshLibraries()
		self.clearClips()
		self.setSelectedLibrary(name)
	def doNewClip( self, type ):
		BUTTONS = OK, CANCEL = 'OK', 'Cancel'
		typeLabel = ClipPreset.TYPE_LABELS[type]
		ans = cmd.promptDialog(t='enter %s name' % typeLabel, m='enter the %s name:' % typeLabel, b=BUTTONS, db=OK)
		if ans == CANCEL:
			return

		kwargs = {}
		if type == kANIM:
			kwargs = { 'startFrame': cmd.playbackOptions( q=True, min=True ),
			           'endFrame': cmd.playbackOptions( q=True, max=True ) }

		objs = cmd.ls(sl=True)
		name = cmd.promptDialog(q=True, tx=True)
		newClip = ClipPreset(LOCAL, self.getSelectedLibrary(), name, type)
		newClip.write( objs, **kwargs )
		self.clipUIs.append( ClipSliderUI(newClip, self.localeUI[LOCAL]) )

		print 'wrote new %s clip!' % typeLabel, newClip
	def onNewPose( self, *args ):
		self.doNewClip(kPOSE)
	def onNewAnim( self, *args ):
		self.doNewClip(kANIM)
	@api.d_showWaitCursor
	def onSync( self, *args ):
		p4 = P4File()
		for p in self.manager.getPresetDirs(GLOBAL):
			print 'SYNCING to:  ', p
			p4.sync(p)

		self.refreshLibraries()
		self.refreshClips()

	### UI SCRIPTED INTERACTION
	def setFilter( self, filterStr ):
		cmd.textField(self.UI_filter, e=True, tx=filterStr)
		for clipUI in self.clipUIs:
			if clipUI.name().find(filterStr) == -1:
				clipUI.hide()
			else:
				clipUI.show()
	def getFilter( self ):
		return cmd.textField(self.UI_filter, q=True, tx=True)
	def getSelectedLibrary( self ):
		try:
			return cmd.textScrollList(self.UI_libraries, q=True, si=True)[-1]
		except TypeError: return None
	def setSelectedLibrary( self, library ):
		if library is None:
			return

		cmd.textScrollList(self.UI_libraries, e=True, si=library)
		if library:
			cmd.button(self.UI_button_newPose, e=True, en=True)
			cmd.button(self.UI_button_newAnim, e=True, en=True)  #disabled until anim clip support is written
		else:
			cmd.button(self.UI_button_newPose, e=True, en=False)
			cmd.button(self.UI_button_newAnim, e=True, en=False)

		self.clearClips()
		self.populateClips()
	def getOpt( self, optName ):
		'''
		'''
		attr = getattr(self, 'UI_opt_%s' % optName)
		return cmd.checkBox(attr, q=True, v=True)
	def getOptions( self ):
		'''
		returns a dict containing all the options to pass to the clip.apply() method
		'''
		options = {}
		if self.getOpt('offset'):
			options[BaseClip.kOPT_OFFSET] = cmd.currentTime(q=True)

		options[BaseClip.kOPT_ADDITIVE] = self.getOpt('additive')
		options[BaseClip.kOPT_ADDITIVE_WORLD] = self.getOpt('additiveWorld')

		return options

	### UPDATING
	@d_restoreLibrarySelection
	def refreshLibraries( self ):
		self.clearLibraries()
		self.populateLibraries()
	def refreshClips( self ):
		self.clearClips()
		self.populateClips()
	def populateLibraries( self ):
		libraries = self.manager.getLibraryNames()
		for lib in libraries:
			cmd.textScrollList(self.UI_libraries, e=True, a=lib)

		self.setSelectedLibrary(libraries[0])

		return libraries
	def populateClips( self ):
		library = self.getSelectedLibrary()
		if library is None:
			return

		clips = self.manager.getLibraryClips(library)
		for clip in clips[LOCAL]:
			self.clipUIs.append( ClipSliderUI(clip, self.localeUI[LOCAL]) )

		for clip in clips[GLOBAL]:
			self.clipUIs.append( ClipSliderUI(clip, self.localeUI[GLOBAL]) )
	def clear( self ):
		self.clearLibraries()
		self.clearLocal()
		self.clearGlobal()
	def clearLibraries( self ):
		cmd.textScrollList(self.UI_libraries, e=True, ra=True)
	def clearClips( self ):
		for clipUI in self.clipUIs:
			try:
				cmd.deleteUI(clipUI.UI_form)
			except RuntimeError: pass

		self.clipUIs = []
	def reload( self ):
		'''
		clear the library and clip caches
		'''
		self.manager.reload()


class ClipSliderUI(object):
	SLIDER_VISIBLE = {kPOSE: True,
					  kANIM: False}

	def __init__( self, clipPreset, parentUI ):
		self.clipPreset = clipPreset
		self.name = self.clipPreset.niceName
		self.isActive = False
		self.preClip = {}
		self.objs = []
		self.mapping = {}
		self.type = self.clipPreset.getType()

		#cache the apply method locally - mainly for brevity in subsequent code...
		self.apply = clipPreset.apply

		#read the clip and cache some data...
		self.blended = None

		self.build( parentUI )
	def unpickle( self ):
		return self.clipPreset.unpickle()
	@property
	def clipObjs( self ):
		return self.unpickle()[ 'objects' ]
	@property
	def clipInstance( self ):
		return self.unpickle()[ 'clip' ]
	def build( self, parentUI ):
		'''
		build the top level form layout, and then call the populate method
		'''
		cmd.setParent(parentUI)
		self.UI_form = cmd.formLayout()
		self.populateUI()
	def populateUI( self ):
		'''
		populates the top level form with ui widgets
		'''
		cmd.setParent(self.UI_form)
		self.UI_icon = cmd.iconTextButton(l=self.name(), image=str(self.clipPreset.icon.resolve()), c=self.onApply, sourceType='python', ann="click the icon to apply the clip, or use the slider to partially apply it.  if you don't like the icon, right click and choose re-generate icon")

		typeLbl = ClipPreset.TYPE_LABELS[self.clipPreset.getType()]
		self.UI_lbl = cmd.text(l='%s clip:  %s' % (typeLbl, self.name()), font='boldLabelFont', ann="this is the clip's name.  right click and choose rename to change the clip's name")
		self.UI_slider = cmd.floatSlider(v=0, min=0, max=1, dc=self.onDrag, cc=self.onRelease, vis=self.SLIDER_VISIBLE[self.type], ann='use the slider to partially apply a clip, or click the icon to apply it completely')

		cmd.popupMenu(p=self.UI_form, pmc=self.buildMenu)

		cmd.formLayout(self.UI_form, e=True,
					   af=((self.UI_icon, 'left', 0),
						   (self.UI_lbl, 'top', 2),
						   (self.UI_lbl, 'right', 0),
						   (self.UI_slider, 'top', 20),
						   (self.UI_slider, 'right', 0)),
					   ac=((self.UI_lbl, 'left', 10, self.UI_icon),
						   (self.UI_slider, 'left', 0, self.UI_icon)))
	def onApply( self, slam=False ):
		opts = ui.getOptions()
		opts[ 'slam' ] = slam
		self.mapping = Mapping( cmd.ls(sl=True), self.clipObjs )
		self.apply(self.mapping, **opts)
	def unpopulateUI( self ):
		'''
		removes all widgets from teh top level form - usually used to rebuild the slider...
		'''
		if cmd.formLayout(self.UI_form, exists=True):
			children = cmd.formLayout(self.UI_form, q=True, ca=True)
			if children:
				for c in children: cmd.deleteUI(c)
	def hide( self ):
		cmd.formLayout(self.UI_form, e=True, vis=False)
	def show( self ):
		cmd.formLayout(self.UI_form, e=True, vis=True)
	def buildMenu( self, parent, *args ):
		cmd.setParent(parent, m=True)
		cmd.menu(parent, e=True, dai=True)

		cmd.menuItem(l=self.name(), boldFont=True)
		if self.clipPreset.locale == LOCAL:
			cmd.menuItem(l='publish to global -->', c=self.onPublish)

		def onIcon(*x):
			generateIcon(self.clipPreset)
			self.refreshIcon()
		cmd.menuItem(l='re-generate icon', c=onIcon)
		cmd.menuItem(d=True)
		cmd.menuItem(l='delete', c=lambda *x: self.delete())
		cmd.menuItem(l='rename', c=self.onRename)
		cmd.menuItem(d=True)

		cmd.menuItem(l='slam clip into scene', c=self.onSlam)
		cmd.menuItem(l='select items in clip', c=self.onSelect)
		cmd.menuItem(l='map names manually', c=self.onMapping)
		cmd.menuItem(d=True)
		api.addExploreToMenuItems(self.clipPreset)
		cmd.menuItem(d=True)
		api.addPerforceMenuItems(self.clipPreset, others=[self.clipPreset.icon], previous=False)
	def onPublish( self, *args ):
		movedPreset = self.clipPreset.move()
		self.clipPreset = movedPreset

		#delete the old UI and create the new UI
		cmd.deleteUI(self.UI_form)
		self.build(ui.localeUI[GLOBAL])

		#add to perforce
		p4 = P4File(self.clipPreset)
		p4.DEFAULT_CHANGE = 'animLib Auto Checkout'
		p4.add(self.clipPreset, type=P4File.BINARY)
		p4.add(self.clipPreset.icon)

		#ask the user whether they want to submit the clip - delayed submission is rarely useful/desired
		ans = cmd.confirmDialog(t='submit clip now?', m='do you want to submit the clip now', b=api.ui_QUESTION, db=api.YES)
		if ans == api.YES:
			p4.submit()
			api.melPrint('submitted!')
	def onSelect( self, arg ):
		objs = self.clipPreset.getClipObjects()
		existingObjs = []
		sceneTransforms = cmd.ls( typ='transform' )
		for o in objs:
			if not cmd.objExists( o ):
				newO = names.matchNames( [o], sceneTransforms, threshold=kDEFAULT_MAPPING_THRESHOLD )[ 0 ]
				if not cmd.objExists( newO ):
					print 'WARNING :: %s NOT FOUND IN SCENE!!!' % o
					continue

				existingObjs.append( newO )
				print 'WARNING :: re-mapping %s to %s' % (o, newO)
			else:
				existingObjs.append( o )

		cmd.select( existingObjs )
	def onSlam( self, arg ):
		self.onApply( True )
	def onMapping( self, *args ):
		mapping = Mapping( cmd.ls(sl=True), self.clipObjs )

		#gah...  convert the mapping to the type of mapping expected by the xfer anim editor - ie a single source maps to a list of targets instead of a single target...  need to turn the mapping into a class of some description methinks
		xferAnimMapping = {}
		for src, tgt in mapping.iteritems():
			xferAnimMapping[ src ] = [ tgt ]

		xferAnimUI.XferAnimEditor( mapping=xferAnimMapping, clipPreset=self.clipPreset )
	def onRename( self, *args ):
		ans, name = api.doPrompt(t='new name', m='enter new name', tx=self.name())
		if ans != api.OK:
			return

		self.clipPreset.rename(name)
		self.unpopulateUI()
		self.populateUI()
	def onDrag( self, value ):
		value = float(value)
		if not self.isActive:
			print 'starting press CB'
			self.onPress(value)
			return

		self.blended( value )
	def onPress( self, value ):
		self.isActive = True
		cmd.undoInfo( stateWithoutFlush=False )
		self.autoKeyBeginState = cmd.autoKeyframe( q=True, state=True )
		cmd.autoKeyframe( e=True, state=False )

		self.objs = objs = cmd.ls(sl=True)
		self.mapping = Mapping( objs, self.clipObjs )
		self.preClip = self.clipInstance.__class__( objs, *self.clipInstance.generatePreArgs() )
		self.blended = self.clipInstance.blender( self.preClip, self.clipInstance, self.mapping )

		print 'executing PRESS CB - undo is now OFF'
	def onRelease( self, value ):
		self.isActive = False
		cmd.undoInfo(stateWithoutFlush=True)
		cmd.autoKeyframe(e=True, state=self.autoKeyBeginState)

		value = float(value)
		self.blended( value )
		self.reset()

		print 'executing RELEASE CB - undo is now ON'
	def refreshIcon( self ):
		'''
		refreshes the icon UI element
		'''
		cmd.iconTextButton(self.UI_icon, e=True, image='')
		cmd.iconTextButton(self.UI_icon, e=True, image=str(self.clipPreset.icon.resolve()))
	def delete( self ):
		self.clipPreset.delete()
		cmd.deleteUI(self.UI_form)

		#if the clip is a global clip, ask the user if they want to submit the delete
		if self.clipPreset.locale == GLOBAL:
			ans = cmd.confirmDialog(t='submit the delete?', m='do you want to submit the delete?', b=api.ui_QUESTION, db=api.YES)
			if ans == api.YES:
				p4 = P4File(self.clipPreset)
				p4.DEFAULT_CHANGE = 'auto deleting file from %s' % TOOL_NAME
				p4.setChange( p4.DEFAULT_CHANGE )
				p4.setChange( p4.DEFAULT_CHANGE, self.clipPreset.icon )
				p4.submit()
	def reset( self ):
		cmd.floatSlider(self.UI_slider, e=True, v=0)


def load():
	#first make sure there is a default library...
	tmp = ClipManager().createLibrary('default')

	global ui
	ui = AnimLibUI()


#end