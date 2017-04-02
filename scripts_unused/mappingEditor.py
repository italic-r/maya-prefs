from filesystem import *
from baseMelUI import *
import utils
import names
import api
import presetsUI


TOOL_NAME = 'zoo'
TOOL_VER = 1
EXT = 'mapping'
ui = None


class MappingForm(BaseMelWidget):
	'''
	Acts as a generic UI for editing "mappings".  A mapping is basically just a dictionaries in maya,
	but they're used for things like animation transfer and weight transfer between one or more
	differing name sets.

	Mappings can be stored out to presets.
	'''

	WIDGET_CMD = cmd.formLayout

	#args for controlling the name mapping algorithm - see the names.matchNames method for documentation on what these variables actually control
	STRIP_NAMESPACES = True
	PARITY_MATCH = True
	UNIQUE_MATCHING = False
	MATCH_OPPOSITE_PARITY = False
	THRESHOLD = names.DEFAULT_THRESHOLD

	#if this is set to True, then sources can be mapped to multiple targets
	ALLOW_MULTIPLE_TGTS = True

	def __new__( cls, parent, *a, **kw ):
		return BaseMelWidget.__new__( cls, parent )
	def __init__( self, parent, srcItems=None, tgtItems=None ):
		self._srcToTgtDict = {}
		self._previousMappingFile = None

		self.UI_srcButton = cmd.button( l='Source Items (click for menu)' )
		self.UI_tgtButton = cmd.button( l='Target Items (click for menu)' )

		cmd.popupMenu( p=self.UI_srcButton, pmc=self.build_srcMenu )
		cmd.popupMenu( p=self.UI_tgtButton, pmc=self.build_tgtMenu )

		cmd.popupMenu( p=self.UI_srcButton, b=1, pmc=self.build_srcMenu )
		cmd.popupMenu( p=self.UI_tgtButton, b=1, pmc=self.build_tgtMenu )

		cmd.setParent( self )
		self.UI_tsl_src = cmd.textScrollList( sc=self.on_selectItemSrc, allowMultiSelection=False, deleteKeyCommand=self.on_delete, doubleClickCommand=self.on_selectSrc )
		self.UI_tsl_tgt = cmd.textScrollList( sc=self.on_selectItemTgt, allowMultiSelection=self.ALLOW_MULTIPLE_TGTS, deleteKeyCommand=self.on_delete, doubleClickCommand=self.on_selectTgt )

		cmd.popupMenu( p=self.UI_tsl_src, pmc=self.build_srcMenu )
		cmd.popupMenu( p=self.UI_tsl_tgt, pmc=self.build_tgtMenu )

		cmd.formLayout( self, e=True,
						af=((self.UI_srcButton, "top", 0),
							(self.UI_srcButton, "left", 0),
							(self.UI_tgtButton, "top", 0),
							(self.UI_tgtButton, "right", 0),
							(self.UI_tsl_src, "left", 2),
							(self.UI_tsl_src, "bottom", 2),
							(self.UI_tsl_tgt, "top", 3),
							(self.UI_tsl_tgt, "right", 2),
							(self.UI_tsl_tgt, "bottom", 2)),
						ap=((self.UI_tsl_src, "right", 1, 50),
							(self.UI_srcButton, "right", 1, 50),
							(self.UI_tsl_tgt, "left", 1, 50),
							(self.UI_tgtButton, "left", 1, 50)),
						ac=((self.UI_tsl_src, "top", 3, self.UI_srcButton),
							(self.UI_tsl_tgt, "top", 3, self.UI_tgtButton)) )

		if srcItems is not None:
			self.addSrcItems( srcItems )

		if tgtItems is not None:
			self.addTgtItems( tgtItems )
	@property
	def srcs( self ):
		srcs = cmd.textScrollList( self.UI_tsl_src, q=True, ai=True )
		if srcs is None:
			return []

		return srcs
	@property
	def tgts( self ):
		tgts = cmd.textScrollList( self.UI_tsl_tgt, q=True, ai=True )
		if tgts is None:
			return []

		return tgts
	def getUnmappedSrcs( self ):
		return list( set( self.srcs ).difference( self.getMapping().srcs ) )
	def getUnmappedTgts( self ):
		return list( set( self.tgts ).difference( self.getMapping().tgts ) )
	def getMapping( self ):
		mapping = names.Mapping.FromDict( self._srcToTgtDict )
		return mapping
	def setMapping( self, mapping ):
		if isinstance( mapping, dict ):
			self._srcToTgtDict = mapping
		elif isinstance( mapping, names.Mapping ):
			self._srcToTgtDict = mapping.asDict()
		else:
			raise TypeError, "unsupported mapping type %s" % type( mapping )

		self.refresh()
	def getSelectedSrc( self ):
		'''
		returns the name of the src item selected.  None if nothing is selected
		'''
		try:
			return cmd.textScrollList( self.UI_tsl_src, q=True, selectItem=True )[ 0 ]
		except TypeError: return None
	def getSelectedTgts( self ):
		return cmd.textScrollList( self.UI_tsl_tgt, q=True, selectItem=True )
	def mapSrcItem( self, src ):
		self._srcToTgtDict[ src ] = names.matchNames( [ src ], self.tgts, self.STRIP_NAMESPACES, self.PARITY_MATCH, self.UNIQUE_MATCHING, self.MATCH_OPPOSITE_PARITY, self.THRESHOLD )
	def mapAllSrcItems( self ):
		for src in self.srcs:
			self.mapSrcItem( src )
	def addSrcItems( self, items ):
		if items:
			cmd.textScrollList( self.UI_tsl_src, e=True, append=list( sorted( items ) ) )
			for i in items:
				self.mapSrcItem( i )
	def replaceSrcItems( self, items ):
		cmd.textScrollList( self.UI_tsl_src, e=True, ra=True )
		self.addSrcItems( items )
	def addTgtItems( self, items ):
		performMapping = cmd.textScrollList( self.UI_tsl_tgt, q=True, allItems=True ) is None
		if items:
			cmd.textScrollList( self.UI_tsl_tgt, e=True, append=items )
			if performMapping:
				self.mapAllSrcItems()
	def refresh( self ):
		#remove all items
		cmd.textScrollList( self.UI_tsl_src, e=True, ra=True )
		cmd.textScrollList( self.UI_tsl_tgt, e=True, ra=True )

		#add the data to the UI
		theSrcs = []
		theTgts = []
		for src in sorted( self._srcToTgtDict.keys() ):
			theSrcs.append( src )
			theTgts += self._srcToTgtDict[ src ]

		theSrcs = utils.removeDupes( theSrcs )
		theTgts = utils.removeDupes( theTgts )

		cmd.textScrollList( self.UI_tsl_src, e=True, append=theSrcs )
		cmd.textScrollList( self.UI_tsl_tgt, e=True, append=theTgts )
	def saveMappingToFile( self, filepath ):
		filepath = Path( filepath ).setExtension( EXT )
		filedata = api.writeExportDict( TOOL_NAME, TOOL_VER ), self.getMapping()
		filepath.pickle( filedata )
	def saveMappingPreset( self, presetName ):
		filepath = Preset( LOCAL, TOOL_NAME, presetName, EXT )
		self.saveMappingToFile( filepath )
	def loadMappingFile( self, filepath ):
		d, mapping = Path( filepath ).unpickle()

		mapping = names.Mapping.FromDict( mapping )
		if self.ALLOW_MULTIPLE_TGTS:
			self._srcToTgtDict = mapping.asDict()
		else:
			self._srcToTgtDict = mapping.asFlatDict()

		self.refresh()
	def loadMappingPreset( self, presetName ):
		filepath = findPreset( presetName, TOOL_NAME, EXT )
		self.loadMappingFile( filepath )

	### MENU BUILDERS ###
	def build_srcMenu( self, *a ):
		cmd.setParent( a[ 0 ], menu=True )
		cmd.menu( a[ 0 ], e=True, dai=True )

		cmd.menuItem( l='Add Selected Objects', c=self.on_addSrc )
		cmd.menuItem( l='Replace With Selected Objects', c=self.on_replaceSrc )
		cmd.menuItem( d=True)
		cmd.menuItem( l='Edit Name', c=self.on_editSrcItem )
		cmd.menuItem( l='Edit All Names', c=self.on_editSrcItems )
		cmd.menuItem( d=True)
		cmd.menuItem( l='Select All Objects', c=self.on_selectAllSrc )
		cmd.menuItem( d=True )
		cmd.menuItem( l='Save Mapping...', c=self.on_saveMapping )
		cmd.menuItem( l='Load Mapping...', sm=True )
		pm = PresetManager( TOOL_NAME, EXT )
		presets = pm.listAllPresets( True )

		for loc in LOCAL, GLOBAL:
			for f in presets[ loc ]:
				f = Path( f )
				cmd.menuItem( l=f.name(), c=utils.Callback( self.loadMappingFile, f ) )

		cmd.menuItem( d=True )
		cmd.menuItem( l='Manage Mappings...', c=lambda *x: presetsUI.load( TOOL_NAME, LOCAL, EXT ) )

		cmd.setParent( '..', menu=True )
		cmd.menuItem( d=True )
		cmd.menuItem( l='Swap Mapping', c=self.on_swap )
	def build_tgtMenu( self, *a ):
		cmd.setParent( a[ 0 ], menu=True )
		cmd.menu( a[ 0 ], e=True, dai=True )

		cmd.menuItem( l='Add Selected Objects', c=self.on_addTgt )
		cmd.menuItem( l='Replace With Selected Objects', c=self.on_replaceTgt )
		cmd.menuItem( d=True)
		cmd.menuItem( l='Select All Objects', c=self.on_selectAllTgt )
		cmd.menuItem( l='Select Highlighted Objects', c=self.on_selectTgt )
		cmd.menuItem( d=True)
		cmd.menuItem( l='Swap Mapping', c=self.on_swap )

	### EVENT CALLBACKS ###
	def on_selectAllSrc( self, *a ):
		cmd.select( cl=True )
		for s in cmd.textScrollList( self.UI_tsl_src, q=True, ai=True ):
			if cmd.objExists( s ):
				cmd.select( s, add=True )
	def on_selectAllTgt( self, *a ):
		cmd.select( cl=True )
		for t in cmd.textScrollList( self.UI_tsl_tgt, q=True, ai=True ):
			if cmd.objExists( t ):
				cmd.select( t, add=True )
	def on_editSrcItem( self, *a ):
		src = self.getSelectedSrc()
		if not src:
			return

		selectedItemIdx = cmd.textScrollList( self.UI_tsl_src, q=True, selectIndexedItem=True )[ 0 ]

		bOK, bCANCEL = 'OK', 'Cancel'
		ret = cmd.promptDialog( t="Enter New Name", m="Enter a new item name", tx=src, b=(bOK, bCANCEL), db=bOK )
		if ret == bOK:
			newName = cmd.promptDialog( q=True, tx=True )
			value = self._srcToTgtDict.pop( src )
			self._srcToTgtDict[ newName ] = value

			cmd.textScrollList( self.UI_tsl_src, e=True, removeIndexedItem=selectedItemIdx )
			cmd.textScrollList( self.UI_tsl_src, e=True, appendPosition=(selectedItemIdx, newName) )
	def on_editSrcItems( self, *a ):
		bOK, bCANCEL = 'OK', 'Cancel'
		ret = cmd.promptDialog( t="Enter New Names", m="Enter a new item name template (%s to insert old name)", tx='%s', b=(bOK, bCANCEL), db=bOK )
		if ret == bOK:
			newNameTemplate = cmd.promptDialog( q=True, tx=True )
			oldNames = self._srcToTgtDict.keys()
			for oldName in oldNames:
				newName = newNameTemplate % oldName
				value = self._srcToTgtDict.pop( oldName )
				self._srcToTgtDict[ newName ] = value

		self.refresh()
	def on_selectItemSrc( self, *a ):
		cmd.textScrollList( self.UI_tsl_tgt, e=True, deselectAll=True )
		src = self.getSelectedSrc()
		if src:
			try: tgts = self._srcToTgtDict[ src ]
			except KeyError:
				return

			for t in tgts:
				if t: cmd.textScrollList( self.UI_tsl_tgt, e=True, si=t )
	def on_addSrc( self, *a ):
		self.addSrcItems( cmd.ls( sl=True ) )
	def on_replaceSrc( self, *a ):
		self._srcToTgtDict = {}
		cmd.textScrollList( self.UI_tsl_src, e=True, ra=True )
		self.on_addSrc()
	def on_selectSrc( self, *a ):
		src = self.getSelectedSrc()
		if src:
			#if the object doesnt' exist in teh scene - try to find it
			if not cmd.objExists( src ):
				src = names.matchNames( [ src ], cmd.ls( typ='transform' ) )[ 0 ]

			if cmd.objExists( src ):
				cmd.select( src )
	def on_selectItemTgt( self, *a ):
		src = self.getSelectedSrc()
		if src:
			tgts = cmd.textScrollList( self.UI_tsl_tgt, q=True, si=True )
			self._srcToTgtDict[ src ] = tgts
		else:
			cmd.textScrollList( self.UI_tsl_tgt, e=True, deselectAll=True )
	def on_delete( self, *a ):
		src = self.getSelectedSrc()
		if src:
			del( self._srcToTgtDict[ src ] )
			self.on_selectItemSrc()
	def on_addTgt( self, *a ):
		self.addTgtItems( cmd.ls( sl=True ) )
	def on_replaceTgt( self, *a ):
		self._srcToTgtDict = {}
		cmd.textScrollList( self.UI_tsl_tgt, e=True, ra=True )
		self.on_addTgt()
		self.mapAllSrcItems()
	def on_selectTgt( self, *a ):
		tgts = self.getSelectedTgts()
		if tgts:
			toSearch = cmd.ls( typ='transform' )
			existingTgts = []
			for t in tgts:
				if not cmd.objExists( t ):
					t = names.matchNames( [ t ], toSearch )[ 0 ]

				if cmd.objExists( t ):
					existingTgts.append( t )

			if existingTgts:
				cmd.select( existingTgts )
	def on_swap( self, *a ):
		curMapping = names.Mapping.FromDict( self._srcToTgtDict )
		curMapping.swap()

		if self.ALLOW_MULTIPLE_TGTS:
			self._srcToTgtDict = curMapping.asDict()
		else:
			self._srcToTgtDict = curMapping.asFlatDict()

		self.refresh()
	def on_saveMapping( self, *a ):
		ret = cmd.promptDialog( m='Enter a name for the mapping', t='Enter Name', b=('Ok', 'Cancel'), db='Ok' )
		if ret == 'Ok':
			self.saveMappingPreset( cmd.promptDialog( q=True, tx=True ) )
	def on_loadMapping( self, *a ):
		previous = getPresetDirs( LOCAL, TOOL_NAME )[ 0 ]
		if self._previousMappingFile is not None:
			previous = self._previousDir

		filename = cmd.fileDialog( directoryMask=( "%s/*.%s" % (previous, EXT) ) )
		filepath = Path( filename )

		self._previousMappingFile = filepath.up()
		self.loadMappingFile( filepath )


class MappingEditor(BaseMelWindow):
	'''
	'''
	WINDOW_NAME = 'mappingEditorUI'
	WINDOW_TITLE = 'Mapping Editor'

	DEFAULT_SIZE = 400, 600

	def __new__( cls, *a, **kw ):
		return BaseMelWindow.__new__( cls )
	def __init__( self, srcItems=None, tgtItems=None ):
		BaseMelWindow.__init__( self )
		self.editor = MappingForm( self, srcItems, tgtItems )
		self.show()
	def getMapping( self ):
		return self.editor.getMapping()


def load():
	global ui
	ui = MappingEditor()


#end