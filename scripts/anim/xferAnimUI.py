import maya.cmds as cmd
import baseMelUI
import mappingEditor
import api
import animLib


__author__ = 'mel@macaronikazoo.com'
ui = None
MelForm = baseMelUI.MelForm

class MelFrame(baseMelUI.BaseMelWidget):
	WIDGET_CMD = cmd.frameLayout


setParent = cmd.setParent
class XferAnimForm(MelForm):
	MODE_SCENE = 0
	MODE_FILE = 1
	def __init__( self, parent ):
		MelForm.__init__( self, parent )

		self.sortBySrcs = True  #otherwise it sorts by tgts when doing traces
		self._clipPreset = None
		self.UI_mapping = mappingEditor.MappingForm( self )
		self.UI_options = MelFrame( self, l="xfer options", labelVisible=1, collapsable=0, borderStyle='etchedIn' )

		cmd.columnLayout( adjustableColumn=True, rowSpacing=5 )
		cmd.rowLayout( numberOfColumns=2,
					   columnWidth2=(175, 165),
					   columnAttach=((1, "both", 5), (2, "both", 5)) )

		cmd.columnLayout( adjustableColumn=True )
		self.UI_radios = cmd.radioCollection()
		self.RAD_dupe = cmd.radioButton( l="duplicate nodes", align='left', sl=True, cc=self.on_update )
		self.RAD_copy = cmd.radioButton( l="copy/paste keys", align='left', cc=self.on_update )
		self.RAD_trace = cmd.radioButton( l="trace objects", align='left', cc=self.on_update )
		setParent('..')


		cmd.columnLayout( adjustableColumn=True )
		self.UI_check1 = cmd.checkBox( l="instance animation" )
		self.UI_check2 = cmd.checkBox( l="match rotate order", v=1 )
		self.UI_check3 = cmd.checkBox( l="", vis=0, v=0 )
		self.UI_check4 = cmd.checkBox( l="", vis=0, v=1 )
		setParent('..')
		setParent('..')


		cmd.rowColumnLayout( numberOfColumns=7,
							 columnWidth=((1, 75), (2, 95), (3, 35), (4, 45), (5, 35), (6, 45)),
							 columnAttach=((1, "both", 1),
										   (2, "both", 1),
										   (3, "both", 1),
										   (4, "both", 1),
										   (5, "both", 5),
										   (6, "both", 1),
										   (7, "both", 5)) )
		self.UI_keysOnly = cmd.checkBox( l="keys only", v=0, cc=self.on_update )
		self.UI_withinRange = cmd.checkBox( l="within range:", v=0, cc=self.on_update )
		cmd.text( l="start ->" )
		self.UI_start = cmd.textField( en=0, tx='!' )
		cmd.popupMenu( p=self.UI_start, b=3, pmc=self.buildTimeMenu )

		cmd.text( l="end ->" )
		self.UI_end = cmd.textField( en=0, tx='!' )
		cmd.popupMenu( p=self.UI_end, b=3, pmc=self.buildTimeMenu )

		cmd.setParent( self )
		UI_button = cmd.button( l='Xfer Animation', c=self.on_xfer )

		self( e=True,
			  af=((self.UI_mapping, 'top', 0),
				  (self.UI_mapping, 'left', 0),
				  (self.UI_mapping, 'right', 0),
				  (self.UI_options, 'left', 0),
				  (self.UI_options, 'right', 0),
				  (UI_button, 'left', 0),
				  (UI_button, 'right', 0),
				  (UI_button, 'bottom', 0)),
			  ac=((self.UI_mapping, 'bottom', 0, self.UI_options),
				  (self.UI_options, 'bottom', 0, UI_button)) )

		self.on_update()  #set initial state
	def isTraceMode( self, theMode ):
		m = cmd.radioCollection( self.UI_radios, q=True, sl=True )
		return theMode.endswith( '|'+ m )
	def setMapping( self, mapping ):
		self.UI_mapping.setMapping( mapping )
	def setClipPreset( self, clipPreset, mapping=None ):
		self._clipPreset = clipPreset

		#setup the file specific UI
		fileDict = clipPreset.unpickle()

		add = False
		delta = fileDict[ animLib.kEXPORT_DICT_CLIP_TYPE ] == animLib.kDELTA
		world = fileDict.get( animLib.kEXPORT_DICT_WORLDSPACE, False )
		nocreate = False

		#populate the source objects from the file
		self.UI_mapping.replaceSrcItems( fileDict[ animLib.kEXPORT_DICT_OBJECTS ] )

		self.UI_options( e=True, l="import options" )
		cmd.radioButton( self.RAD_dupe, e=True, en=True, sl=True, l="absolute times" )
		cmd.radioButton( self.RAD_copy, e=True, en=True, l="current time offset" )
		cmd.radioButton( self.RAD_trace, e=True, en=False, vis=False, l="current time offset" )

		cmd.checkBox( self.UI_check1, e=True, l="additive key values", vis=True, v=add )
		cmd.checkBox( self.UI_check2, e=True, l="match rotate order", vis=True, v=0 )
		cmd.checkBox( self.UI_check3, e=True, l="import as world space", vis=True, v=world )
		cmd.checkBox( self.UI_check4, e=True, l="don't create new keys", vis=True, v=nocreate )

		self.on_update()

	### MENU BUILDERS ###
	def buildTimeMenu( self, parent, uiItem ):
		cmd.menu( parent, e=True, dai=True )
		cmd.setParent( parent, m=True )

		cmd.menuItem( l="! - use current range", c=lambda a: cmd.textField( uiItem, e=True, tx='!' ) )
		cmd.menuItem( l=". - use current frame", c=lambda a: cmd.textField( uiItem, e=True, tx='.' ) )
		cmd.menuItem( l="$ - use scene range", c=lambda a: cmd.textField( uiItem, e=True, tx='$' ) )

	### EVENT HANDLERS ###
	def on_update( self, *a ):
			sel = cmd.ls( sl=True, dep=True )

			if not self._clipPreset is not None:
				if self.isTraceMode( self.RAD_dupe ):
					cmd.checkBox( self.UI_check1, e=True, en=True )
				else:
					cmd.checkBox( self.UI_check1, e=True, en=False, v=0 )

			if self.isTraceMode( self.RAD_trace ):
				cmd.checkBox( self.UI_keysOnly, e=True, en=True )
				cmd.checkBox( self.UI_check2, e=True, v=0 )
				cmd.checkBox( self.UI_check3, e=True, vis=1, v=1, l="process post-trace cmds" )
			else:
				cmd.checkBox( self.UI_keysOnly, e=True, en=False, v=0 )
				cmd.checkBox( self.UI_check3, e=True, vis=0, v=0 )

			if  cmd.checkBox( self.UI_keysOnly, q=True, v=True ):
				cmd.checkBox( self.UI_withinRange, e=True, en=1 )
			else:
				cmd.checkBox( self.UI_withinRange, e=True, en=0, v=0 )

			enableRange = self.isTraceMode( self.RAD_copy ) or self.isTraceMode( self.RAD_trace )
			keysOnly = cmd.checkBox( self.UI_keysOnly, q=True, v=True )
			withinRange = cmd.checkBox( self.UI_withinRange, q=True, v=True )
			if enableRange and not keysOnly or withinRange:
				cmd.textField( self.UI_start, e=True, en=True )
				cmd.textField( self.UI_end, e=True, en=True )
			else:
				cmd.textField( self.UI_start, e=True, en=False )
				cmd.textField( self.UI_end, e=True, en=False )
	def on_xfer( self, *a ):
		mapping = api.resolveMapping( self.UI_mapping.getMapping() )
		theSrcs = []
		theTgts = []

		#perform the hierarchy sort
		idx = 0 if self.sortBySrcs else 1
		toSort = [ (len(list(api.iterParents( srcAndTgt[ idx ] ))), srcAndTgt) for srcAndTgt in mapping.iteritems() if cmd.objExists( srcAndTgt[ idx ] ) ]
		toSort.sort()
		for idx, (src, tgt) in toSort:
				theSrcs.append( src )
				theTgts.append( tgt )

		offset = ''
		isDupe = self.isTraceMode( self.RAD_dupe )
		isCopy = self.isTraceMode( self.RAD_copy )
		isTraced = self.isTraceMode( self.RAD_trace )

		instance = cmd.checkBox( self.UI_check1, q=True, v=True )
		traceKeys = cmd.checkBox( self.UI_keysOnly, q=True, v=True )
		matchRo = cmd.checkBox( self.UI_check2, q=True, v=True )
		startTime = cmd.textField( self.UI_start, q=True, tx=True )
		endTime = cmd.textField( self.UI_end, q=True, tx=True )
		world = cmd.checkBox( self.UI_check3, q=True, v=True )  #this is also "process trace cmds"
		nocreate = cmd.checkBox( self.UI_check4, q=True, v=True )

		if startTime.isdigit():
			startTime = int( startTime )
		else:
			if startTime == '!': startTime = cmd.playbackOptions( q=True, min=True )
			elif startTime == '.': startTime = cmd.currentTime( q=True )
			elif startTime == '$': startTime = cmd.playbackOptions( q=True, animationStartTime=True )

		if endTime.isdigit():
			endTime = int( endTime )
		else:
			if endTime == '!': endTime = cmd.playbackOptions( q=True, max=True )
			elif endTime == '.': endTime = cmd.currentTime( q=True )
			elif endTime == '$': endTime = cmd.playbackOptions( q=True, animationEndTime=True )

		withinRange = cmd.checkBox( self.UI_withinRange, q=True, v=True )

		if withinRange:
			traceKeys = 2

		if isCopy:
			offset = "*"

		api.mel.zooXferAnimUtils()
		if self._clipPreset is not None:
			print self._clipPreset.asClip()
			#convert to mapping as expected by animLib...  this is messy!
			animLibMapping = {}
			for src, tgts in mapping.iteritems():
				animLibMapping[ src ] = tgts[ 0 ]

			self._clipPreset.asClip().apply( animLibMapping )
		elif isDupe:
			api.melecho.zooXferBatch( "-mode 0 -instance %d -matchRo %d" % (instance, matchRo), theSrcs, theTgts )
		elif isCopy:
			api.melecho.zooXferBatch( "-mode 1 -range %s %s -matchRo %d" % (startTime, endTime, matchRo), theSrcs, theTgts )
		elif isTraced:
			api.melecho.zooXferBatch( "-mode 2 -keys %d -postCmds %d -matchRo %d -sortByHeirarchy 0 -range %s %s" % (traceKeys, world, matchRo, startTime, endTime), theSrcs, theTgts )


class XferAnimEditor(baseMelUI.BaseMelWindow):
	WINDOW_NAME = 'xferAnim'
	WINDOW_TITLE = 'Xfer Anim'

	DEFAULT_SIZE = 350, 450
	DEFAULT_MENU = 'Tools'

	#FORCE_DEFAULT_SIZE = False

	def __new__( cls, mapping=None, clipPreset=None ):
		return baseMelUI.BaseMelWindow.__new__( cls )
	def __init__( self, mapping=None, clipPreset=None ):
		baseMelUI.BaseMelWindow.__init__( self )
		self.editor = XferAnimForm( self )
		if mapping is not None:
			self.editor.setMapping( mapping )

		if clipPreset is not None:
			self.editor.setClipPreset( clipPreset )

		def loadOffsetEditor( *a ):
			import applyToRig
			editor = applyToRig.CreateRigOffsetEditor()

		cmd.setParent( self.getMenu( 'Tools' ), m=True )
		cmd.menuItem( l="Open Offset Editor", c=loadOffsetEditor )

		self.show()


def load():
	global ui
	ui = XferAnimEditor()


#end
