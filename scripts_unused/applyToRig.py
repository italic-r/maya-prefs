from modelpipeline import apps
from baseMelUI import *
import exportManagerCore
import mappingEditor
import fileListForm
import assetLister
import filesystem
import api
import names
import webbrowser
import bugReporterUI
import presetsUI
from filesystem import Preset, LOCAL, GLOBAL, findPreset


__author__ = 'hamish@valvesoftware.com'
ui = None
Path = filesystem.Path
P4File = filesystem.P4File

TOOL_NAME = 'applyToRig'
EXTENSION = 'postTraceScheme'

IMPORT_DATA_NS = 'tmp:'
POST_TRACE_ATTR_NAME = 'xferPostTraceCmd'

api.mel.source( 'zooAlign' )


def savePostTraceScheme( presetName ):
	'''
	stores all post trace commands found in the current scene out to disk
	'''

	#grab a list of transforms with post trace commands on them
	postTraceNodes = cmd.ls( "*.%s" % POST_TRACE_ATTR_NAME, r=True )

	postTraceDict = {}
	for n in postTraceNodes:
		noNS = n.split( ':' )[ -1 ]  #strip the namespace
		noNS = noNS.split( '.' )[ 0 ]  #strip the attribute
		postTraceDict[ noNS ] = cmd.getAttr( n )

	xportDict = api.writeExportDict( TOOL_NAME, 0 )

	p = Preset( GLOBAL, TOOL_NAME, presetName, EXTENSION )
	p.pickle( (xportDict, postTraceDict) )


def clearPostTraceScheme():
	postTraceNodes = cmd.ls( "*.%s" % POST_TRACE_ATTR_NAME, r=True )
	for n in postTraceNodes:
		#ideally delete the attribute
		try:
			cmd.deleteAttr( n )

		#this can happen if the node is referenced - so just set it to an empty string...
		except RuntimeError:
			cmd.setAttr( n, '', typ='string' )


def loadPostTraceSchemeFilepath( presetFile ):
	'''
	re-applies a stored post trace command scheme back to the controls found in the current scene
	'''

	#first we need to purge all existing post trace commands
	clearPostTraceScheme()

	presetFile = Path( presetFile )
	if not presetFile.isfile():
		raise IOError, "no such preset"

	xportDict, postTraceDict = presetFile.unpickle()

	allTransforms = cmd.ls( typ='transform' )
	for n, postTraceCmd in postTraceDict.iteritems():
		n = n.split( '.' )[ 0 ]  #strip off the attribute
		nInScene = names.matchNames( [ n ], allTransforms )[ 0 ]
		if cmd.objExists( nInScene ):
			api.mel.zooSetPostTraceCmd( nInScene, postTraceCmd )


def loadPostTraceScheme( presetName ):
	'''
	added so the load save commands are symmetrical - its sometimes more convenient to load from just
	a preset name instead of a full filepath...  esp when debugging
	'''
	p = findPreset( presetName, TOOL_NAME, EXTENSION, LOCAL )
	return loadPostTraceSchemeFilepath( p )


def commonApply( rig, rigNS, filename, nodes, mapping, postTraceSchemeFilepath=None, sortBySrcs=True ):

	#apply the post trace scheme if applicable
	if postTraceSchemeFilepath is not None:
		loadPostTraceSchemeFilepath( postTraceSchemeFilepath )


	possibleSrcs = cmd.ls( '%s*' % IMPORT_DATA_NS, typ='transform' )
	possibleTgts = cmd.ls( '%s*' % rigNS, typ='transform' )


	#build the ctrl-bone mapping - and ensure proper namespaces are present...  the mapping contains no namespaces
	srcs, tgts = [], []
	idx = 0 if sortBySrcs else 1
	toSort = []
	for src, tgt in mapping.iteritems():
		src = names.matchNames( [ src ], possibleSrcs )[ 0 ]
		tgt = names.matchNames( [ tgt ], possibleTgts )[ 0 ]
		srcOrTgt = src, tgt

		if cmd.objExists( srcOrTgt[ idx ] ):
			numParents = len( list( api.iterParents( srcOrTgt[ idx ] ) ) )
			toSort.append( (numParents, src, tgt) )

	toSort.sort()
	for idx, src, tgt in toSort:
		srcs.append( src )
		tgts.append( tgt )


	print "rig namespace is:", rigNS
	print 'srcs are', srcs
	print 'tgts are', tgts


	#sort the items by hierarchy based on the src items - xferAnim does have the option of doing this, but it sorts using the tgt list, and its done in mel, so...  I don't trust it
	srcsParentCount = [ (len( [p for p in api.iterParents( s )] ), s, t) for s, t in zip( srcs, tgts ) if cmd.objExists( s ) ]
	srcsParentCount.sort()
	srcs = [ s[ 1 ] for s in srcsParentCount ]
	tgts = [ s[ 2 ] for s in srcsParentCount ]


	#now turn any ik off - we'll restore it afterwards, but if ik is on, then fk controls don't get traced properly...  coz maya is ghey!
	initIkBlendValues = {}
	for t in tgts:
		attrPath = "%s.ikBlend" % t
		if cmd.objExists( attrPath ):
			initIkBlendValues[ attrPath ] = cmd.getAttr( attrPath )
			cmd.setAttr( attrPath, 0 )


	#perform the trace
	api.melecho.zooXferTrace( srcs, tgts, True, True, False, True, False, -1000, 1000 )


	#restore ik settings
	for attrPath, value in initIkBlendValues.iteritems():
		cmd.setAttr( attrPath, value )


	#rename the file
	mayaFilepath = apps.getAssetRoot( rig, apps.MAYA ) / 'maya/animation' / filename.name()
	mayaFilepath.up().create()
	cmd.file( rename=mayaFilepath )
	mayaFilepath = Path( cmd.file( q=True, sn=True ) )


	#try to determine the info node to export
	exportNode = None
	for n in cmd.ls( typ='vstInfo' ):
		if n.startswith( rigNS ):
			exportNode = n
			break


	#setup the export manager data if we can...
	if exportNode is not None:
		xm = exportManagerCore.ExportManager()
		comp = xm.createExportComponent( [ exportNode ] )
		comp.setAttr( 'name', mayaFilepath.name() )
		comp.setAttr( 'type', exportManagerCore.ExportComponent.kANIM )


	#save changes...
	cmd.file( save=True, f=True )

	return mayaFilepath


def applySmd( rig, smd, mapping, postTraceSchemeFilepath=None ):

	#source xferAnim
	api.mel.zooXferAnimUtils()


	#create a new file
	cmd.file( f=True, new=True )


	#import the smd
	nodes = api.importSmdAnimationAndSkeleton( smd, namespace=IMPORT_DATA_NS[ :-1 ] )
	nodes = nodes + cmd.listRelatives( nodes, ad=True, pa=True )


	#bring in the rig
	rigNS = rig.name().replace( '_rig', '' ) +':'
	cmd.file( rig.unresolved(), reference=True, prompt=False, namespace=rigNS[ :-1 ] )

	return commonApply( rig, rigNS, smd, nodes, mapping, postTraceSchemeFilepath )


def applyMaya( rig, mayaFile, mapping, postTraceSchemeFilepath=None ):

	#source xferAnim
	api.mel.zooXferAnimUtils()


	#create a new file
	cmd.file( f=True, new=True )


	#bring in the rig and maya file (reference it in)
	rigNS = rig.name().replace( '_rig', '' ) +':'
	nodes = cmd.file( rig.unresolved(), reference=True, returnNewNodes=True, prompt=False, loadReferenceDepth='topOnly', namespace=rigNS[ :-1 ] )
	actualRigNS = ''
	n = 0
	while actualRigNS == '':
		actualRigNS = api.Name( nodes[ n ] ).getNamespace()
		n += 1

	nodes = cmd.file( mayaFile, reference=True, returnNewNodes=True, namespace=IMPORT_DATA_NS[ :-1 ] )


	return commonApply( rig, actualRigNS, mayaFile, nodes, mapping, postTraceSchemeFilepath )


#extensions that want to be exposed to the file chooser should be registered in this dictionary with
#the appropriate function to handle doing the import when passed appropriate data.  see the ApplyToRigForm.go
#method for a function definition
REGISTERED_EXTENSIONS = { 'smd': applySmd,
						  'ma': applyMaya,
						  'mb': applyMaya,
						  'dmx': applyMaya }


def getMain( namespace='' ):
	matches = [ i for i in cmd.ls( 'main', r=True ) if i.startswith( namespace ) ]

	return matches[ 0 ]


def bakeRotateDelta( src, tgt, ctrl, presetStr ):
	'''
	Bakes a post trace command into the ctrl object such that when ctrl is aligned to src (with post
	trace cmds enabled) src and tgt are perfectly aligned.

	This is useful because rig controls are rarely aligned to the actual joints they drive, but it
	can be useful when you have motion from a tool such as SFM, or generated from motion capture that
	needs to be applied back to a rig.
	'''
	api.mel.zooAlign( "-load 1" )
	api.mel.zooAlign( "-src %s -tgt %s" % (src, ctrl) )

	offset = api.getRotateDelta__( src, tgt, ctrl )
	print offset

	api.mel.zooSetPostTraceCmd( ctrl, presetStr % offset )
	api.mel.zooAlign( "-src %s -tgt %s -postCmds 1" % (src, ctrl) )


def bakeManualRotateDelta( src, tgt, ctrl, presetStr ):
	'''
	When you need to apply motion from a skeleton that is completely different from a skeleton driven
	by the rig you're working with (transferring motion from old assets to newer assets for example)
	you can manually align the control to the joint and then use this function to generate offset
	rotations and bake a post trace cmd.
	'''
	preMat = api.getObjectMatrix( ctrl )

	api.mel.zooAlign( "-load 1" )
	api.mel.zooAlign( "-src %s -tgt %s" % (src, ctrl) )

	postMat = api.getObjectMatrix( ctrl )

	#generate the offset matrix as
	mat_o = preMat * postMat.inverse()

	#now figure out the euler rotations for the offset
	tMat = api.OpenMaya.MTransformationMatrix( mat_o )
	asEuler = tMat.rotation().asEulerRotation()
	asEuler = map(api.OpenMaya.MAngle, (asEuler.x, asEuler.y, asEuler.z))
	asEuler = tuple( a.asDegrees() for a in asEuler )

	cmd.rotate( asEuler[ 0 ], asEuler[ 1 ], asEuler[ 2 ], ctrl, relative=True, os=True )
	print asEuler

	api.mel.zooSetPostTraceCmd( ctrl, presetStr % asEuler )
	api.mel.zooAlign( "-src %s -tgt %s -postCmds 1" % (src, ctrl) )


class CreateRigOffsetForm(MelColumn):
	#this dict contains UI labels and a presets for offset commands...  when adding new ones make sure it contains exactly three format strings...
	CMD_PRESETS = { 'a) default': ('rotate -r -os %0.3f %0.3f %0.3f #; setKeyframe -at r -at t #;', bakeRotateDelta),
					'b) ik foot with toe': ('rotate -r -os %0.3f %0.3f %0.3f #; setKeyframe -at r -at t #; traceToe # %%opt0%% x z;', bakeRotateDelta),
					'c) copy local rotation': ('float $f[] = `getAttr %%opt0%%.r`; setAttr #.rx $f[0]; setAttr #.ry $f[1]; setAttr #.rz $f[2]; setKeyframe -at r #;', None),
					'd) manual local rotation': ('rotate -r -os %0.3f %0.3f %0.3f #; setKeyframe -at r -at t #;', bakeManualRotateDelta)}

	def __init__( self, parent ):
		MelColumn.__init__( self, parent, rowSpacing=15, adjustableColumn=True )

		cmd.text( l='first load the rig you want to author offsets for', align='left' )

		cmd.button( l="Set Reference Skeleton - if you don't have one already", c=self.setRefSkeleton )
		cmd.button( l="Import Reference Skeleton", c=self.importRefSkeleton )

		buttonLbl = 'Bake Offset'
		cmd.text( l='1) select the target skeleton joint\n2) select the rigged skeleton joint\n3) select the control\n4) hit "%s"' % buttonLbl, align='left' )

		self.UI_presetType = cmd.optionMenu( l='Offset Command Preset' )
		for lbl in sorted( self.CMD_PRESETS.keys() ):
			cmd.menuItem( l=lbl )

		cmd.button( l=buttonLbl, c=self.performOffset )
	def setRefSkeleton( self, *a ):
		smdRef = cmd.fileDialog( directoryMask=Path( '%VCONTENT%/%VMOD%/models/*.smd' ), mode=0, title="Browse to the Smd Reference File" )
		smdRef = Path( smdRef )

		if not smdRef.exists:
			api.melPrint( 'no file specified...' )
			return

		main = getMain()
		if not cmd.objExists( '%s.smdModelSourceLocation' % main ):
			cmd.addAttr( main, longName='smdModelSourceLocation', dt='string' )

		cmd.setAttr( '%s.smdModelSourceLocation' % main, smdRef << '%VCONTENT%', typ='string' )
	def importRefSkeleton( self, *a ):
		main = getMain()
		assert cmd.objExists( main ), "Cannot find the main control.  Please load the rig file."

		if cmd.objExists( '%s.smdModelSourceLocation' % main ):
			smdRef = Path( cmd.getAttr( '%s.smdModelSourceLocation' % main ) )
		else:
			try:
				smdRef = cmd.fileDialog( directoryMask=Path( '%VCONTENT%/%VMOD%/models/*.smd' ), mode=0, title="Browse to the Smd Reference File" )
				smdRef = Path( smdRef )
				if not smdRef.exists:
					raise Exception

				if not cmd.objExists( '%s.smdModelSourceLocation' % main ):
					cmd.addAttr( main, longName='smdModelSourceLocation', dt='string' )

				cmd.setAttr( '%s.smdModelSourceLocation' % main, smdRef << '%VCONTENT%', typ='string' )
			except Exception:
				api.melPrint( "no smd source file located - may not have been defined?" )
				return

		if not smdRef.exists:
			P4File( smdRef ).toDepotPath().sync( force=True )

		if not smdRef.exists:
			api.melPrint( "can't find reference file - tried syncing but it still doesn't exist..." )
			return

		api.importFile( smdRef )
	def performOffset( self, *a ):
		sel = cmd.ls( sl=True )
		assert len( sel ) == 3, "Please select the 3 objects described in the instructions"

		presetStr, presetDataFunc = self.CMD_PRESETS[ cmd.optionMenu( self.UI_presetType, q=True, v=True ) ]

		src, tgt, ctrl = sel
		if callable( presetDataFunc ):
			presetDataFunc( src, tgt, ctrl, presetStr )


class CreateRigOffsetEditor(BaseMelWindow):
	WINDOW_NAME = 'rigOffsetEditor'
	WINDOW_TITLE = 'Create Rig Offset Editor'

	DEFAULT_SIZE = 300, 305

	FORCE_DEFAULT_SIZE = True

	def __init__( self ):
		BaseMelWindow.__init__( self )

		CreateRigOffsetForm( self )

		self.show()


class TheFileList(fileListForm.FileListForm):
	EXTENSION_SETS = {}
	for ext, m in REGISTERED_EXTENSIONS.iteritems():
		try: EXTENSION_SETS[ m ].append( ext )
		except KeyError: EXTENSION_SETS[ m ] = [ ext ]

	EXTENSION_SETS = EXTENSION_SETS.values()
	EXTENSIONS = EXTENSION_SETS[ 0 ]

	#IGNORE_SUBSTRINGS = [ '_reference' ]

	def on_open( self, theFile ):
		api.openFile( theFile )
		cmd.vstSmdIO( i=True, importSkeleton=True, filename=theFile )
	def on_import( self, theFile ):
		cmd.vstSmdIO( i=True, importSkeleton=True, filename=theFile )
	def on_reference( self, theFile ):
		api.referenceFile( theFile, 'ref' )


class PostTraceSchemeChooser(presetsUI.PresetForm):
	ALLOW_MULTI_SELECTION = False

	def __init__( self, parent ):
		presetsUI.PresetForm.__init__( self, parent, TOOL_NAME, GLOBAL, EXTENSION )
	def getSelectedFilepath( self ):
		try:
			return self.selected()[ 0 ]
		except IndexError: return None
	def popup_filemenu( self, parent, *a ):
		#call base class menu build cmd
		presetsUI.PresetForm.popup_filemenu( self, parent, *a )

		items = self.selected()
		en = bool( items )

		#now add options for loading and saving of post trace schemes
		cmd.menuItem( d=True )
		cmd.menuItem( l="Save Current Post Trace Scheme", c=self.on_saveTracePreset )
		cmd.menuItem( d=True )
		cmd.menuItem( en=en, l="Apply Post Trace Scheme Now", c=self.on_applyPreset )
		cmd.menuItem( l="Clear Current Scheme", c=self.on_clearPreset )
		cmd.menuItem( d=True )
		cmd.menuItem( en=en, l="Print Contents", c=self.on_printContents )
	def on_saveTracePreset( self, *a ):
		bOK, bCANCEL = 'OK', 'Cancel'
		ret = cmd.promptDialog( t='Enter Preset Name', m='Enter a name for the post trace command preset', b=(bOK, bCANCEL), db=bOK )
		if ret == bOK:
			presetName = cmd.promptDialog( q=True, tx=True )
			savePostTraceScheme( presetName )
			self.updateList()
	def on_applyPreset( self, *a ):
		try:
			pFilepath = self.selected()[ 0 ]
		except IndexError: return

		loadPostTraceSchemeFilepath( pFilepath )
	def on_clearPreset( self, *a ):
		clearPostTraceScheme()
	def on_printContents( self, *a ):
		for s in self.selected():
			print '-------------------', s, '-------------------'
			d, data = s.unpickle()
			for name, info in d.iteritems():
				print '#', name.rjust( 15 ), '--->', info
			print '#------- trace command info -------#'
			for name, info in data.iteritems():
				print name.rjust( 30 ), '--->', info


class SummaryForm(BaseMelWidget):
	WIDGET_CMD = cmd.scrollLayout

	def __init__( self, parent ):
		BaseMelWidget.__init__( self, parent, childResizable=True, horizontalScrollBarThickness=0 )

		cmd.setParent( self )
		cmd.columnLayout( rowSpacing=15, adjustableColumn=True )

		self.UI_button = cmd.button()
		self.texts = []

		self.texts.append( cmd.text( l='', align='left' ) )
		self.texts.append( cmd.text( l='', align='left' ) )
		self.texts.append( cmd.text( l='', align='left' ) )
		self.texts.append( cmd.text( l='', align='left' ) )
	def update( self, data ):
		try: theRig = data[ Step_ChooseRig_Form ][ 0 ]
		except TypeError:
			theRig = None

		if theRig is None:
			theRig = '<NO RIG SELECTED!>'

		scheme = data[ Step_PostTrace_Form ]
		if scheme is None:
			scheme = '<NO POST TRACE SCHEME WILL BE APPLIED>'

		cmd.text( self.texts[ 0 ], e=True, l='applying animation from the following files:\n%s\n' % '\n'.join( data[ Step_ChooseFiles_Form ] ) )
		cmd.text( self.texts[ 1 ], e=True, l='to the following rig:     %s\n' % theRig  )
		cmd.text( self.texts[ 2 ], e=True, l='using the mapping:\n%s\n' % '\n'.join( [ '%s -> %s' % s_and_t for s_and_t in data[ Step_DefineMapping_Form ].iteritems() ] ) )
		cmd.text( self.texts[ 3 ], e=True, l='applying the post trace scheme preset:     %s\n' % scheme )


class BaseStep(MelForm):
	def __init__( self, parent, stepString, helpLink, mainWidget ):
		MelForm.__init__( self, parent )

		self._helpLink = helpLink

		UI_tx = self.UI_tx = cmd.text( l=stepString )
		UI_help = cmd.button( l='HELP!', c=self.on_help )
		UI_widget = self.UI_widget = mainWidget( self )

		self( e=True,
			  af=((UI_tx, 'top', 10),
				  (UI_tx, 'left', 10),
				  (UI_help, 'top', 10),
				  (UI_help, 'right', 10),
				  (UI_widget, 'left', 0),
				  (UI_widget, 'right', 0),
				  (UI_widget, 'bottom', 0)),
			  ac=((UI_widget, 'top', 10, UI_tx),
				  (UI_help, 'bottom', 10, UI_widget)) )

		if not helpLink:
			cmd.control( UI_help, e=True, vis=False )
	def isCompleted( self ):
		'''
		Should return whether the current tab's step has been "completed".  If not the tool will let
		the user know they haven't completed the current step.
		'''
		return True
	def finished( self ):
		'''
		This is called when the user hits "next", and can be used to "do something" if needed.
		'''
		pass
	def getData( self ):
		return None
	def on_select( self, *a ):
		pass
	def on_help( self, *a ):
		webbrowser.open( self._helpLink )


class Step_ChooseRig_Form(BaseStep):
	def __init__( self, parent ):
		BaseStep.__init__( self, parent,
						   "Find the asset in the list, and choose which rig you want to apply the animation to.",
						   '',
						   assetLister.AssetListerForm )

		self.UI_widget.setFileFilter( 'rig' )
	def isCompleted( self ):
		selFile = self.UI_widget.getSelectedFile()
		return selFile is not None
	def getData( self ):
		return self.UI_widget.getSelectedFile()


class Step_ChooseFiles_Form(BaseStep):
	def __init__( self, parent ):
		BaseStep.__init__( self, parent,
						   "Choose the directory the files live in, and select the files you want to transfer animation from.",
						   '',
						   TheFileList )
	def isCompleted( self ):
		return len( self.getData() )
	def getData( self ):
		return self.UI_widget.getSelectedFiles()


class Step_DefineMapping_Form(BaseStep):
	def __init__( self, parent ):
		BaseStep.__init__( self, parent,
							"Define the way the skeleton maps to the rig being traced.  So in the left column should be joint names\nfrom the skeleton with animation on it, while the right column should contain names of the rig controls",
							'https://intranet.valvesoftware.com/wiki/index.php/Apply_to_Rig#Workflow',
							mappingEditor.MappingForm )
	def isCompleted( self ):
		return len( self.UI_widget.srcs ) + len( self.UI_widget.tgts )
	def getData( self ):
		return self.UI_widget.getMapping()


class Step_PostTrace_Form(BaseStep):
	def __init__( self, parent ):
		BaseStep.__init__( self, parent,
						   "Select the post trace command scheme to apply to the rig before the trace is performed.  If you don't\nwant a post trace command scheme to be applied at all (or have no idea what this means - see the wiki\nlink in the help menu) you may skip this step",
						   'https://intranet.valvesoftware.com/wiki/index.php/Apply_to_Rig#Authoring_Skeleton-.3ERig_Offsets',
						   PostTraceSchemeChooser )
	def isCompleted( self ):
		#it is entirely valid to have no scheme chosen
		return True
	def getData( self ):
		return self.UI_widget.getSelectedFilepath()


class Final_Step_Form(BaseStep):
	def __init__( self, parent, editor ):
		self.editor = editor
		BaseStep.__init__( self, parent,
						   "Make sure all the details are correct and when you're ready, hit Go!",
						   None,
						   SummaryForm )

		self.button = self.UI_widget.UI_button
		cmd.button( self.button, e=True, l='GO!', c=self.on_go )
	def on_select( self, *a ):
		data = self.editor.getData()
		self.UI_widget.update( data )
	def on_go( self, *a ):
		self.editor.go()


class ApplyToRigForm(MelForm):
	def __init__( self, parent ):
		MelForm.__init__( self, parent )

		UI_tabs = self.UI_tabs = cmd.tabLayout( childResizable=True, selectCommand=self.on_selectTab )
		self._tabs = []

		self.appendTab( Step_ChooseRig_Form( UI_tabs ), "Choose the Rig" )
		self.appendTab( Step_ChooseFiles_Form( UI_tabs ), "Choose Files" )
		self.appendTab( Step_DefineMapping_Form( UI_tabs ), "Define Name Mapping" )
		self.appendTab( Step_PostTrace_Form( UI_tabs ), "Choose a Trace Cmd Scheme" )
		self.appendTab( Final_Step_Form( UI_tabs, self ), "Review And GO!" )

		cmd.setParent( self )
		UI_lowerButtons = cmd.formLayout()
		UI_prev = cmd.button( l='<- Prev', w=100, c=self.on_prev )
		UI_next = cmd.button( l='Next ->', w=100, c=self.on_next )

		cmd.formLayout( UI_lowerButtons, e=True,
						af=((UI_prev, 'top', 5),
							(UI_prev, 'left', 5),
							(UI_prev, 'bottom', 5),
							(UI_next, 'top', 5),
							(UI_next, 'right', 5),
							(UI_next, 'bottom', 5)) )

		self( e=True,
			  af=((UI_tabs, 'top', 0),
				  (UI_tabs, 'left', 0),
				  (UI_tabs, 'right', 0),
				  (UI_lowerButtons, 'left', 0),
				  (UI_lowerButtons, 'right', 0),
				  (UI_lowerButtons, 'bottom', 0)),
			  ac=((UI_tabs, 'bottom', 0, UI_lowerButtons)) )
	def appendTab( self, tabWidget, title ):
		self._tabs.append( tabWidget )

		cmd.tabLayout( self.UI_tabs, e=True, tabLabel=((tabWidget, title),) )
	def getCurrentTab( self ):
		curTabIdx = cmd.tabLayout( self.UI_tabs, q=True, selectTabIndex=True )
		return self._tabs[ curTabIdx-1 ]
	def checkIfCurrentTabCompleted( self ):
		tabUI = self.getCurrentTab()
		return tabUI.isCompleted()
	def getData( self ):
		data = {}
		for t in self._tabs[ :-1 ]:  #don't care about the last tab - its a summary tab and has no data
			data[ t.__class__ ] = t.getData()

		return data
	@filesystem.d_preserveDefaultChange
	def go( self ):
		#first make sure all tabs have been completed - if not, throw the user back to the appropriate tab to complete
		for idx, t in enumerate( self._tabs ):
			if not t.isCompleted():
				cmd.tabLayout( self.UI_tabs, e=True, sti=idx + 1 )  #tab indices in maya's tabLayout are 1-based
				return

		data = self.getData()
		rig = data[ Step_ChooseRig_Form ][ 1 ]
		files = data[ Step_ChooseFiles_Form ]
		mapping = data[ Step_DefineMapping_Form ]
		postTraceSchemeFile = data[ Step_PostTrace_Form ]

		#change the default changelist to something sensible
		filesystem.DEFAULT_CHANGE = 'default change for applyToRig on %s' % rig

		for f in files:
			apply = REGISTERED_EXTENSIONS[ f.getExtension().lower() ]
			apply( rig, f, mapping, postTraceSchemeFile )

	### EVENT CALLBACKS ###
	def on_next( self, *a ):
		if self.checkIfCurrentTabCompleted():
			curTabIdx = cmd.tabLayout( self.UI_tabs, q=True, selectTabIndex=True )
			nextTabIdx = curTabIdx + 1
			try:
				cmd.tabLayout( self.UI_tabs, e=True, selectTabIndex=nextTabIdx )
			except RuntimeError: return

			self.on_selectTab()
		else:
			cmd.confirmDialog( title="Please Complete", message="Please complete the task for the current tab" )
	def on_prev( self, *a ):
		curTabIdx = cmd.tabLayout( self.UI_tabs, q=True, selectTabIndex=True )
		prevTabIdx = curTabIdx - 1

		try:
			cmd.tabLayout( self.UI_tabs, e=True, selectTabIndex=prevTabIdx )
		except RuntimeError: return

		self.on_selectTab()
	def on_selectTab( self, *a ):
		tabUI = self.getCurrentTab()
		tabUI.on_select()


class ApplyToRigEditor(BaseMelWindow):
	WINDOW_NAME = 'applyToRigEditor'
	WINDOW_TITLE = 'Apply to Rig Editor'

	DEFAULT_SIZE = 600, 500

	FORCE_DEFAULT_SIZE = True

	def __init__( self ):
		BaseMelWindow.__init__( self )

		ApplyToRigForm( self )

		cmd.setParent( self.getMenu( 'File' ), menu=True )
		cmd.menuItem( l="Open Offset Editor", c=lambda *a: CreateRigOffsetEditor() )

		cmd.setParent( self.getMenu( 'Help' ), menu=True )
		cmd.menuItem( l="Help...", c=lambda *a: webbrowser.open( 'https://intranet.valvesoftware.com/wiki/index.php/Apply_to_Rig' ) )
		cmd.menuItem( d=True )
		bugReporterUI.addBugReporterMenuItems( TOOL_NAME )

		filesystem.reportUsageToAuthor()
		self.show()


def load():
	global ui
	ui = ApplyToRigEditor()


#end