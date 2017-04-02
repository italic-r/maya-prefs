import maya.cmds as cmd
import utils
import api
from baseMelUI import *
from filesystem import *


ui = None

class PresetForm(MelForm):
	ALLOW_MULTI_SELECTION = True

	def __new__( cls, parent, *a, **kw ):
		return BaseMelWidget.__new__( cls, parent )
	def __init__( self, parent, tool, locale=LOCAL, ext=DEFAULT_XTN ):
		self.tool = tool
		self.locale = locale
		self.ext = ext
		self.presetManager = PresetManager(tool, ext)

		self.populate()
	def populate( self ):
		children = self( q=True, ca=True )
		if children is not None:
			for c in children:
				cmd.deleteUI( c )

		other = self.other()
		otherLbl = "<-- %s" % other

		cmd.setParent( self )
		self.UI_lbl_title = cmd.text(l='Managing "%s" presets' % self.ext)
		self.UI_lbl_presets = cmd.text(l="%s presets" % self.locale)
		self.UI_button_swap = cmd.button(h=18, l="view %s presets" % other, c=self.swap)
		self.UI_tsl_presets = cmd.textScrollList(allowMultiSelection=self.ALLOW_MULTI_SELECTION, sc=self.updateButtonStatus)
		self.UI_button_1 = cmd.button(l="move to %s" % other, c=self.move)
		self.UI_button_2 = cmd.button(l="copy to %s" % other, c=self.copy)
		self.UI_button_3 = cmd.button(l="rename", c=self.rename)
		self.UI_button_4 = cmd.button(l="delete", c=self.delete)

		self.POP_filemenu = cmd.popupMenu(b=3, p=self.UI_tsl_presets, pmc=self.popup_filemenu)

		self( e=True,
			  af=((self.UI_lbl_title, "top", 5),
				  (self.UI_lbl_title, "left", 5),

				  (self.UI_lbl_presets, "left", 10),

				  (self.UI_button_swap, "right", 5),
				  (self.UI_tsl_presets, "left", 5),
				  (self.UI_tsl_presets, "right", 5),
				  (self.UI_button_1, "left", 5),
				  (self.UI_button_2, "right", 5),
				  (self.UI_button_3, "left", 5),
				  (self.UI_button_3, "bottom", 5),
				  (self.UI_button_4, "right", 5),
				  (self.UI_button_4, "bottom", 5)),
			  ac=((self.UI_lbl_presets, "top", 10, self.UI_lbl_title),
				  (self.UI_button_swap, "top", 7, self.UI_lbl_title),
				  (self.UI_button_1, "bottom", 0, self.UI_button_3),
				  (self.UI_button_swap, "left", 10, self.UI_lbl_presets),
				  (self.UI_tsl_presets, "top", 10, self.UI_lbl_presets),
				  (self.UI_tsl_presets, "bottom", 5, self.UI_button_1),
				  (self.UI_button_2, "bottom", 0, self.UI_button_4)),
			  ap=((self.UI_button_1, "right", 0, 50),
				  (self.UI_button_2, "left", 0, 50),
				  (self.UI_button_3, "right", 0, 50),
				  (self.UI_button_4, "left", 0, 50)) )

		self.updateList()
	def other( self ):
		'''
		returns the "other" locale
		'''
		return LOCAL if self.locale == GLOBAL else GLOBAL
	def updateList( self ):
		'''
		refreshes the preset list
		'''
		presets = self.presetManager.listPresets(self.locale)
		cmd.textScrollList(self.UI_tsl_presets, e=True, ra=True)
		self.presets = presets
		for p in presets:
			cmd.textScrollList(self.UI_tsl_presets, e=True, a=p[-1])

		self.updateButtonStatus()
	def updateButtonStatus( self, *args ):
		selected = self.selected()
		numSelected = len(selected)

		if numSelected == 0:
			cmd.button(self.UI_button_1, e=1, en=0)
			cmd.button(self.UI_button_2, e=1, en=0)
			cmd.button(self.UI_button_3, e=1, en=0)
			cmd.button(self.UI_button_4, e=1, en=0)
		elif numSelected == 1:
			cmd.button(self.UI_button_1, e=1, en=1)
			cmd.button(self.UI_button_2, e=1, en=1)
			cmd.button(self.UI_button_3, e=1, en=1)
			cmd.button(self.UI_button_4, e=1, en=1)
		else:
			cmd.button(self.UI_button_1, e=1, en=1)
			cmd.button(self.UI_button_2, e=1, en=1)
			cmd.button(self.UI_button_3, e=1, en=0)
			cmd.button(self.UI_button_4, e=1, en=1)
	def selected( self ):
		'''
		returns the selected presets as utils.Path instances - if nothing is selected, an empty
		list is returned
		'''
		try:
			selectedIdxs = [idx-1 for idx in cmd.textScrollList(self.UI_tsl_presets, q=True, sii=True)]
			selected = [self.presets[n] for n in selectedIdxs]
			return selected
		except TypeError: return []
	def getSelectedPresetNames( self ):
		selected = cmd.textScrollList( self.UI_tsl_presets, q=True, si=True)
	def getSelectedPresetName( self ):
		try: return self.getSelectedPresetNames()[ 0 ]
		except IndexError:
			return None
	def copy( self, *args ):
		files = []
		for s in self.selected():
			files.append( s.copy() )

		if self.locale == LOCAL:
			self.promptForSubmit(files)
	def delete( self, *args ):
		files = self.selected()
		for s in files:
			s.delete()

		self.updateList()
		if self.locale == GLOBAL:
			self.promptForSubmit(files)
	def move( self, *args ):
		files = []
		for s in self.selected():
			if self.locale == GLOBAL:
				files.append( Preset.FromFile(s) )
			else:
				files.append( s )
			s.move()

		self.updateList()
		self.promptForSubmit(files)
	def rename( self, *args ):
		'''
		performs the prompting and renaming of presets
		'''
		selected = self.selected()[0]
		ans, newName = api.doPrompt(m='new name', tx=selected.name())
		if ans != api.OK:
			return

		if not newName.endswith('.'+ self.ext):
			newName += '.'+ self.ext

		selected.rename(newName)
		self.updateList()
		if self.locale == GLOBAL:
			self.promptForSubmit([selected])
	def swap( self, *args ):
		'''
		performs the swapping from the local to global locale
		'''
		self.locale = self.other()
		self.populate()
	def promptForSubmit( self, files ):
		'''
		handles asking the user whether they want to submit changes - called after any file operation that happens
		in the global locale
		'''
		ans = api.doConfirm(t='submit files?', m='do you want to submit the files?', b=api.ui_QUESTION, db=api.YES)

		p4 = P4File()
		change = p4.getChangeNumFromDesc('presetManager auto submit')
		for f in files:
			p4.setChange(change, f)

		if ans == api.YES:
			print 'submitting change', change
			p4.submit(change)
	def syncall( self, *a ):
		'''
		syncs to ALL global presets for the current tool - NOTE: this syncs to all global preset dirs in
		the mod hierarchy...
		'''
		dirs = getPresetDirs(self.locale, self.tool)
		for dir in dirs:
			utils.P4Data(dir).sync()
			print 'syncing to %s...' % dir.resolve().asdir()
		self.updateList()
	def on_notepad( self, filepath ):
		utils.spawnProcess('notepad "%s"' % utils.Path(filepath).asNative())
	def popup_filemenu( self, parent, *args ):
		cmd.menu(parent, e=True, dai=True)
		cmd.setParent(parent, m=True)

		other = self.other()
		items = self.selected()
		numItems = len(items)
		if numItems:
			cmd.menuItem(l='copy to %s' % other, c=self.copy)
			cmd.menuItem(l='move to %s' % other, c=self.move)

			if len(items) == 1:
				filepath = items[0].resolve()
				cmd.menuItem(d=True)
				cmd.menuItem(l='open in notepad', c=lambda *x: self.on_notepad( filepath ))

				#if the files are global files, display the perforce menu
				if self.locale == GLOBAL:
					cmd.menuItem(d=True)
					api.addPerforceMenuItems(filepath)
				cmd.menuItem(d=True)
				api.addExploreToMenuItems(filepath)

			cmd.menuItem(d=True)
			cmd.menuItem(l='delete', c=self.delete)

		#if the file is a global file, display an option to sync to presets
		if self.locale == GLOBAL:
			if numItems: cmd.menuItem(d=True)
			cmd.menuItem(l='sync to presets', c=self.syncall)

		#if no files are selected, prompt the user to select files
		if numItems == 0: cmd.menuItem(en=False, l='select a preset file')


class PresetUI(BaseMelWindow):
	WINDOW_NAME = 'presetWindow'
	WINDOW_TITLE = 'Preset Manager'

	DEFAULT_SIZE = 275, 325
	DEFAULT_MENU = 'Perforce'

	FORCE_DEFAULT_SIZE = True

	def __new__( cls, *a, **kw ):
		return BaseMelWindow.__new__( cls )
	def __init__( self, tool, locale=LOCAL, ext=DEFAULT_XTN ):
		BaseMelWindow.__init__( self )

		self.editor = PresetForm( self, tool, locale, ext )

		cmd.setParent( self.getMenu( self.DEFAULT_MENU ), m=True )
		cmd.menuItem(l='Sync to Global Presets', c=lambda *a: self.editor.syncall())

		self.show()


def load( tool, locale=LOCAL, ext=DEFAULT_XTN ):
	'''
	this needs to be called to load the ui properly in maya
	'''
	global ui
	ui = PresetUI(tool, locale, ext)


#end
