
import cPickle

from maya import OpenMaya, OpenMayaUI, mel
from maya import cmds as cmd

from zooPy import presets
from zooPy.strUtils import Mapping
from zooPy.path import Path

import animClip

from melUtils import printInfoStr, printWarningStr, printErrorStr

TOOL_NAME = 'animLib'
VER = 4

#ICON_FMT_MAGIC_INT is the value for the defaultRenderGlobals.imageFormat node in maya
_BMP, _PNG, _XPM = ('bmp', 20), ('png', 32), ('xpm', 63)
ICON_FMT_STR, ICON_FMT_MAGIC_INT = _PNG

ICON_SIZE = 60  #icons are square


class AnimLibException(Exception): pass


def getMostLikelyModelView():
	'''
	returns the panel name for the most likely active panel - the currently active panel can be
	ambiguous if the user has been using the outliner, or graph editor or something after viewport
	usage...  this method simply looks at the currently active panel and if its not a modelPanel,
	then it returns the first visible model panel.  if no panels are found, returns None
	'''
	cur = cmd.getPanel(wf=True)
	curType = cmd.getPanel(to=cur)

	if curType == "modelPanel":
		return cur

	visPanels = cmd.getPanel(vis=True)
	for p in visPanels:
		if cmd.getPanel(to=p) == "modelPanel":
			return p

	return None


def generateIcon( preset ):
	'''
	given a preset object, this method will generate an icon using the currently active viewport.  the
	path to the icon is returned
	'''
	sel = cmd.ls(sl=True)
	cmd.select(cl=True)
	panel = getMostLikelyModelView()
	if panel is None:
		raise AnimLibException('cannot determine which panel to use for icon generation')

	#store some initial settings, change them to what is required, and then restored at the very end
	settings = "-df", "-cv", "-ca", "-nurbsCurves", "-nurbsSurfaces", "-lt", "-ha", "-dim", "-pv", "-ikh", "-j", "-dy"
	initialStates = []

	for setting in settings:
		initialStates.append( mel.eval("modelEditor -q %s %s;" % (setting, panel)) )
		mel.eval("modelEditor -e %s 0 %s;" % (setting, panel))

	#this is WAY more involved than doing a playblast, but it also results in prettier icons...  seems like a reasonably tradeoff to me!
	view = OpenMayaUI.M3dView()
	OpenMayaUI.M3dView.getM3dViewFromModelPanel( panel, view )
	xUtil, yUtil, wUtil, hUtil = OpenMaya.MScriptUtil(), OpenMaya.MScriptUtil(), OpenMaya.MScriptUtil(), OpenMaya.MScriptUtil()
	x, y, w, h = xUtil.asUintPtr(), yUtil.asUintPtr(), wUtil.asUintPtr(), hUtil.asUintPtr()
	view.viewport( x, y, w, h )
	x, y, w, h = xUtil.getUint( x ), xUtil.getUint( y ), xUtil.getUint( w ), xUtil.getUint( h )

	#we want a square image, so we need to figure out how best to fit the viewport
	isLandscape = w > h
	if isLandscape:
		x = (w - h) / 2
		w = h
	else:
		y = (h - w) / 2
		h = w

	view.pushViewport( x, y, w, h )
	image = OpenMaya.MImage()
	try:
		view.refresh( False, True, True )
		view.readColorBuffer( image, True )
	finally:
		view.popViewport()

	image.resize( ICON_SIZE, ICON_SIZE )
	image.writeToFile( preset.icon(), ICON_FMT_STR )

	if not preset.icon().exists():
		raise AnimLibException( "icon wasn't written out!" )

	#restore initial state
	try:
		cmd.select(sel)
	except: pass

	for setting, initialState in zip(settings, initialStates):
		mel.eval("modelEditor -e %s %s %s;" % (setting, initialState, panel))


class BaseClipPreset(presets.Preset):
	'''
	a clip preset is different from a normal preset because it is actually two separate files - a
	pickled animation data file, and an icon
	'''

	def __init__( self, locale, library, name ):
		tool = '%s/%s' % (TOOL_NAME, library)
		presets.Preset.__init__( self, locale, tool, name, self.EXT )

		self._icon = self.path().setExtension( ICON_FMT_STR )
		self._so = None
		self._clip = None
		self._nodes = None
	def icon( self ):
		return self._icon
	def load( self ):
		if self._so is None:
			with open( self.path() ) as f:
				self._so = cPickle.load( f )
				self._clip = self._so['clip']
				self._nodes = self._so['nodes']
	def clip( self ):
		self.load()
		return self._clip
	def nodes( self ):
		self.load()
		return self._nodes
	def niceName( self ):
		return self.path().name()
	def getLibrary( self ):
		return self[-2]
	def getTypeName( self ):
		return self.CLIP_CLS.EXT
	def getType( self ):
		return self.CLIP_CLS
	def move( self, library=None ):
		if library is None:
			library = self.getLibrary()

		newLoc = type( self )( self.otherLocale(), library, self.niceName() )

		#perform the move...
		self._path = self.path().move( newLoc )
		self._icon = self.icon().move( newLoc.icon() )
	def copy( self, library=None ):
		if library is None:
			library = self.library

		newLoc = type( self )( self.otherLocale(), library, self.niceName() )

		#perform the copy...
		self.path().copy( newLoc )
		self.icon().copy( newLoc.icon() )

		return newLoc
	def rename( self, newName ):
		'''
		newName should be the base name only - no extension
		'''
		newClipName = '%s.%s' % (newName, self.CLIP_CLS.EXT)
		newIconName = '%s.%s' % (newName, ICON_FMT_STR)
		self._path = self.path().rename( newClipName )
		self._icon = self.icon().rename( newIconName )
	def delete( self ):
		self.path().delete()
		self.icon().delete()
	def apply( self, nodes, attributes=None, **kwargs ):
		self.load()

		#do a version check - if older version clip is being used - perhaps we can write conversion functionality?
		try:
			if self._so.version != VER:
				printWarningStr( "the anim clip version being loaded is old.  YMMV!" )
		except KeyError:
			printErrorStr( "this is an old VER 1 pose clip - I don't know how to load them anymore..." )
			return

		#generate the name mapping
		slamApply = kwargs.pop( 'slam', False )
		if slamApply:
			mapping = mappingUtils.matchNames( cmd.ls( typ='transform' ), nodes )
		else:
			mapping = mappingUtils.matchNames( self._nodes, nodes )

		self._clip.applyToNodes( nodes )
	def write( self, nodes, **kwargs ):
		self._so = None
		so = dict( nodes=nodes )
		so['clip'] = self.CLIP_CLS.Generate( nodes, **kwargs )

		#write the preset file to disk
		with open( self.path(), 'w' ) as f:
			cPickle.dump( so, f )

		#generate the icon for the clip and add it to perforce if appropriate
		icon = generateIcon( self )

		printInfoStr( "Generated clip!" )


class AnimClipPreset(BaseClipPreset):
	EXT = 'anim'
	CLIP_CLS = animClip.AnimClip


class PoseClipPreset(BaseClipPreset):
	EXT = 'pose'
	CLIP_CLS = animClip.PoseClip


class LibraryManager():
	def __init__( self ):
		self._presetManager = presets.PresetManager( TOOL_NAME )
	def getLibraryNames( self ):
		'''
		returns the names of all libraries under the current mod
		'''
		libraries = set()

		for locale, paths in self.getLibraryPaths().iteritems():
			for p in paths:
				libName = p.name()
				libraries.add(libName)

		libraries = list(libraries)
		libraries.sort()

		return libraries
	def getLibraryPaths( self ):
		'''
		returns a dictionary of library paths keyed using locale.  ie:
		{LOCAL: [path1, path2, ...], GLOBAL: etc...}
		'''
		localeDict = {}
		for locale in presets.LOCAL, presets.GLOBAL:
			localeDict[locale] = libraries = []
			dirs = self._presetManager.getPresetDirs(locale)
			libraryNames = set()
			for d in dirs:
				dLibs = d.dirs()
				for dLib in dLibs:
					dLibName = dLib[-1]
					if dLibName not in libraryNames:
						libraries.append(dLib)
						libraryNames.add(dLibName)

		return localeDict
	def createLibrary( self, name ):
		newLibraryPath = presets.Preset( presets.LOCAL, TOOL_NAME, name, '' )
		newLibraryPath.path().create()
	def getLibraryClips( self, library ):
		clips = {presets.LOCAL: [], presets.GLOBAL: []}
		possibleTypes = AnimClipPreset, PoseClipPreset
		for locale, localeClips in clips.iteritems():
			for dir in self._presetManager.getPresetDirs(locale):
				dir += library
				if not dir.exists():
					continue

				for f in dir.files():
					for clipType in possibleTypes:
						if f.hasExtension( clipType.EXT ):
							localeClips.append( clipType( locale, library, f.name() ) )

		return clips
	def getPathToLibrary( self, library, locale=presets.LOCAL ):
		return self._presetManager.getPresetDirs(locale)[0] / library


#end
