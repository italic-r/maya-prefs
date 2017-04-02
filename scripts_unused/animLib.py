from filesystem import *
import maya.cmds as cmd
import utils
import names
import api


__author__ = 'mel@macaronikazoo.com'
TOOL_NAME = 'animLib'
kEXT = 'clip'
VER = 3  #version


### clip types
kPOSE = 0
kANIM = 1
kDELTA = 2

kDEFAULT_MAPPING_THRESHOLD = 1

mel = api.mel
Mapping = names.Mapping


class AnimLibException(Exception):
	def __init__( self, *args ):
		Exception.__init__(self, *args)


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
	settings = ["-df", "-cv", "-ca", "-nurbsCurves", "-nurbsSurfaces", "-lt", "-ha", "-dim", "-pv", "-ikh", "-j", "-dy"]
	imgFormat = cmd.getAttr("defaultRenderGlobals.imageFormat")
	states = []

	cmd.setAttr("defaultRenderGlobals.imageFormat", 20)
	for setting in settings:
		states.append( mel.eval("modelEditor -q %s %s;" % (setting, panel)) )

	for setting in settings:
		mel.eval("modelEditor -e %s 0 %s;" % (setting, panel))

	time = cmd.currentTime(q=True)

	#make sure the icon is open for edit if its a global clip
	if preset.locale == GLOBAL and preset.icon.exists:
		preset.edit()

	icon = cmd.playblast(st=time, et=time, w=60, h=60, fo=True, fmt="image", v=0, p=100, orn=0, cf=str(preset.icon.resolve()))
	icon = Path(icon)

	if icon.exists:
		icon = icon.setExtension('bmp', True)

	cmd.setAttr("defaultRenderGlobals.imageFormat", imgFormat)

	#restore viewport settings
	try: cmd.select(sel)
	except TypeError: pass

	for setting, initialState in zip(settings, states):
		mel.eval("modelEditor -e %s %s %s;" % (setting, initialState, panel))

	return icon


class BaseBlender(object):
	'''
	a blender object is simply a callable object that when called with a percentage arg (0-1) will
	apply said percentage of the given clips to the given mapping
	'''
	def __init__( self, clipA, clipB, mapping=None ):
		self.clipA = clipA
		self.clipB = clipB
		self.__mapping = mapping
	def setMapping( self, mapping ):
		self.__mapping = mapping
	def getMapping( self ):
		return self.__mapping
	def __call__( self, pct, mapping=None ):
		if mapping is not None:
			self.setMapping( mapping )
		assert self.getMapping() is not None


class PoseBlender(BaseBlender):
	def __call__( self, pct, mapping=None ):
		BaseBlender.__call__(self, pct, mapping)
		cmdQueue = api.CmdQueue()

		if mapping is None:
			mapping = self.getMapping()

		for clipAObj, attrDictA in self.clipA.iteritems():
			clipBObjs = mapping[ clipAObj ]
			for a, valueA in attrDictA.iteritems():
				attrpath = '%s.%s' % (clipAObj, a)
				if not cmd.getAttr( attrpath, settable=True ):
					continue

				for clipBObj in clipBObjs:
					try:
						attrDictB = self.clipB[ clipBObj ]
					except KeyError: continue

					try:
						valueB = attrDictB[ a ]
						blendedValue = (valueA * (1-pct)) + (valueB * pct)
						cmdQueue.append( 'setAttr %s %s' % (attrpath, blendedValue) )
					except KeyError:
						cmdQueue.append( 'setAttr %s %s' % (attrpath, valueA) )
					except: pass

		cmdQueue()


class AnimBlender(BaseBlender):
	def __init__( self, clipA, clipB, mapping=None ):
		BaseBlender.__init__(self, clipA, clipB, mapping)

		#so now we need to generate a dict to represent the curves for both of the clips
		animCurveDictA = self.animCurveDictA = {}
		animCurveDictB = self.animCurveDictB = {}

		#the curvePairs attribute contains a dict - indexed by attrpath - containing a tuple of (curveA, curveB)
		self.curvePairs = {}

		for clip, curveDict in zip([self.clipA, self.clipB], [animCurveDictA, animCurveDictB]):
			for o, attrDict in clip.iteritems():
				curveDict[o] = {}
				for a, keyData in attrDict.iteritems():
					curve = curveDict[o][a] = animCurve.AnimCurve()

					#unpack the key data
					weightedTangents, keyList = keyData

					#generate the curves
					for time, value, itt, ott, ix, iy, ox, oy, isLocked, isWeighted in keyList:
						curve.m_bWeighted = weightedTangents
						curve.AddKey( time, value, ix, iy, ox, oy )

					attrPath = '%s.%s' % (o, a)
					try: self.curvePairs[attrPath].append( curve )
					except KeyError: self.curvePairs[attrPath] = [ curve ]

		#now iterate over each curve pair and make sure they both have keys on the same frames...
		for attrPath, curves in self.curvePairs.iteritems():
			try:
				curveA, curveB = curves
			except ValueError: continue

			curveTimes = set( curveA.m_keys.keys() + curveB.m_keys.keys() )
			for t in curveTimes:
				curveA.InsertKey( t )
				curveB.InsertKey( t )
			print 'keys on', attrPath, 'at times', curveTimes
	def __call__( self, pct, mapping=None ):
		BaseBlender.__call__(self, pct, mapping)
		cmdQueue = api.CmdQueue()

		if pct == 0:
			self.clipA.apply( self.getMapping() )
		elif pct == 1:
			self.clipB.apply( self.getMapping() )
		else:
			for attrPath, curves in self.curvePairs.iteritems():
				try:
					curveA, curveB = curves
				except ValueError: continue

				#because we know both curves have the same timings (ie if curveA has a key at time x, curveB is guaranteed to also have a key
				#at time x) then we just need to iterate over the keys of one curve, and blend them with the values of the other
				for time, keyA in curveA.m_keys.iteritems():
					keyB = curveB.m_keys[ time ]
					blendedValue = (keyA.m_flValue * (1-pct)) + (keyB.m_flValue * pct)
					blendedIX = (keyA.m_flInTanX * (1-pct)) + (keyB.m_flInTanX * pct)
					blendedIY = (keyA.m_flInTanY * (1-pct)) + (keyB.m_flInTanY * pct)
					blendedOX = (keyA.m_flOutTanX * (1-pct)) + (keyB.m_flOutTanX * pct)
					blendedOY = (keyA.m_flOutTanY * (1-pct)) + (keyB.m_flOutTanY * pct)
					cmdQueue.append( 'setKeyframe -t %s -v %s %s' % (time, blendedValue, attrPath) )
					cmdQueue.append( 'keyTangent -e -t %s -ix %s -iy %s -ox %s -oy %s %s' % (time, blendedIX, blendedIY, blendedOX, blendedOY, attrPath) )


class BaseClip(dict):
	'''
	baseclass for clips
	'''
	blender = None
	OPTIONS =\
			kOPT_ADDITIVE, kOPT_ADDITIVE_WORLD, kOPT_OFFSET, kOPT_CLEAR, kMULT =\
			'additive', 'additiveWorld', 'offset', 'clear', 'mult'

	kOPT_DEFAULTS = {kOPT_ADDITIVE: False,
					 kOPT_ADDITIVE_WORLD: False,
					 kOPT_OFFSET: 0,
					 kOPT_CLEAR: True,
					 kMULT: 1}
	def __init__( self, objects=None ):
		if objects is not None:
			self.generate( objects )
	def generate( self, objects ):
		pass
	def apply( self, mapping, **kwargs ):
		'''
		valid kwargs are
		additive			[False]           applys the animation additively
		'''
		pass
	def getObjects( self ):
		return self.keys()
	def generatePreArgs( self ):
		return tuple()


class PoseClip(BaseClip):
	blender = PoseBlender
	@classmethod
	def FromObjects( cls, objects ):
		new = cls()
		cls.generate(new, objects)
		return new
	def __add__( self, other ):
		'''
		for adding multiple pose clips together - returns a new PoseClip instance
		'''
		pass
	def __mult__( self, other ):
		'''
		for multiplying a clip by a scalar value
		'''
		assert isinstance(other, (int, long, float))
		new = PoseClip
		for obj, attrDict in self.iteritems():
			for attr, value in attrDict.iteritems():
				attrDict[attr] = value * other
	def generate( self, objects ):
		'''
		generates a pose dictionary - its basically just dict with node names for keys.  key values
		are dictionaries with attribute name keys and attribute value keys
		'''
		self.clear()
		for obj in objects:
			attrs = cmd.listAttr( obj, keyable=True, visible=True, scalar=True )
			if attrs is None:
				continue

			self[ obj ] = objDict = {}
			for attr in attrs:
				objDict[ attr ] = cmd.getAttr('%s.%s' % (obj, attr))
	def apply( self, mapping, **kwargs ):
		'''
		construct a mel string to pass to eval - so it can be contained in a single undo...
		'''
		cmdQueue = api.CmdQueue()

		#gather options...
		additive = kwargs.get( self.kOPT_ADDITIVE,
							   self.kOPT_DEFAULTS[ self.kOPT_ADDITIVE ] )

		for clipObj, tgtObj in mapping.iteritems():
			try:
				attrDict = self[ clipObj ]
			except KeyError: continue

			for attr, value in attrDict.iteritems():
				attrpath = '%s.%s' % (tgtObj, attr)
				try:
					if not cmd.getAttr( attrpath, settable=True ): continue
				except TypeError: continue

				if additive: value += cmd.getAttr( attrpath )
				cmdQueue.append( 'setAttr -clamp %s %s;' % (attrpath, value) )

		cmdQueue()


class AnimClip(BaseClip):
	blender = AnimBlender
	def __init__( self, objects=None ):
		self.offset = 0
		BaseClip.__init__(self, objects)
	def __add__( self, other ):
		pass
	def __mult__( self, other ):
		assert isinstance(other, (int, long, float))
		for obj, attrDict in self.iteritems():
			for attr, value in attrDict.iteritems():
				value *= other
	def generate( self, objects, startFrame=None, endFrame=None ):
		'''
		generates an anim dictionary - its basically just dict with node names for keys.  key values
		are lists of tuples with the form: (keyTime, attrDict) where attrDict is a dictionary with
		attribute name keys and attribute value keys
		'''
		defaultWeightedTangentOpt = bool(cmd.keyTangent(q=True, g=True, wt=True))
		self.clear()

		if startFrame is None:
			startFrame = cmd.playbackOptions( q=True, min=True )
		if endFrame is None:
			endFrame = cmd.playbackOptions( q=True, max=True )

		startFrame, endFrame = list( sorted( [startFrame, endFrame] ) )
		self.offset = startFrame

		#list all keys on the objects - so we can determine the start frame, and range.  all times are stored relative to this time
		allKeys = cmd.keyframe( objects, q=True ) or []
		allKeys.sort()
		allKeys = [ k for k in allKeys if startFrame <= k <= endFrame ]

		self.offset = offset = allKeys[ 0 ]
		self.__range = allKeys[ -1 ] - offset

		for obj in objects:
			attrs = cmd.listAttr( obj, keyable=True, visible=True, scalar=True )
			if attrs is None:
				continue

			objDict = {}
			self[ obj ] = objDict
			for attr in attrs:
				timeTuple = startFrame, endFrame

				#so the attr value dict contains a big fat list containing tuples of the form:
				#(time, value, itt, ott, ita, ota, iw, ow, isLockedTangents, isWeightLock)
				attrpath = '%s.%s' % (obj, attr)
				times = cmd.keyframe( attrpath, q=True, t=timeTuple )
				weightedTangents = defaultWeightedTangentOpt

				#if there is an animCurve this will return its "weighted tangent" state - otherwise it will return None and a TypeError will be raised
				try: weightedTangents = bool(cmd.keyTangent(attrpath, q=True, weightedTangents=True)[0])
				except TypeError: pass

				if times is None:
					#in this case the attr has no animation, so simply record the pose for this attr
					objDict[attr] = (False, [(None, cmd.getAttr(attrpath), None, None, None, None, None, None, None, None)])
					continue
				else:
					times = [ t-offset for t in times ]

				values = cmd.keyframe(attrpath, q=True, t=timeTuple, vc=True)
				itts = cmd.keyTangent(attrpath, q=True, t=timeTuple, itt=True)
				otts = cmd.keyTangent(attrpath, q=True, t=timeTuple, ott=True)
				ixs = cmd.keyTangent(attrpath, q=True, t=timeTuple, ix=True)
				iys = cmd.keyTangent(attrpath, q=True, t=timeTuple, iy=True)
				oxs = cmd.keyTangent(attrpath, q=True, t=timeTuple, ox=True)
				oys = cmd.keyTangent(attrpath, q=True, t=timeTuple, oy=True)
				isLocked = cmd.keyTangent(attrpath, q=True, t=timeTuple, weightLock=True)
				isWeighted = cmd.keyTangent(attrpath, q=True, t=timeTuple, weightLock=True)

				objDict[ attr ] = weightedTangents, zip(times, values, itts, otts, ixs, iys, oxs, oys, isLocked, isWeighted)
	def apply( self, mapping, **kwargs ):
		'''
		valid kwargs are:
		mult                [1.0]   apply a mutiplier when applying curve values
		additive			[False]
		clear				[True]
		'''
		beginningWeightedTanState = cmd.keyTangent(q=True, g=True, wt=True)

		### gather options...
		additive = kwargs.get(self.kOPT_ADDITIVE,
							  self.kOPT_DEFAULTS[self.kOPT_ADDITIVE])
		worldAdditive = kwargs.get(self.kOPT_ADDITIVE_WORLD,
							  self.kOPT_DEFAULTS[self.kOPT_ADDITIVE_WORLD])
		clear = kwargs.get(self.kOPT_CLEAR,
						   self.kOPT_DEFAULTS[self.kOPT_CLEAR])
		mult = kwargs.get(self.kMULT,
						  self.kOPT_DEFAULTS[self.kMULT])
		timeOffset = kwargs.get(self.kOPT_OFFSET, self.offset)

		#if worldAdditive is turned on, then additive is implied
		if worldAdditive:
			additive = worldAdditive

		#determine the time range to clear
		clearStart = timeOffset
		clearEnd = clearStart + self.range

		for obj, tgtObj in mapping.iteritems():
			if not tgtObj:
				continue

			try:
				attrDict = self[ obj ]
			except KeyError: continue

			for attr, (weightedTangents, keyList) in attrDict.iteritems():
				attrpath = '%s.%s' % (tgtObj, attr)
				try:
					if not cmd.getAttr(attrpath, settable=True):
						continue
				except TypeError: continue
				except RuntimeError:
					print obj, tgtObj, attrpath
					raise

				#do the clear...  maya doesn't complain if we try to do a cutKey on an attrpath with no
				#animation - and this is good to do before we determine whether the attrpath has a curve or not...
				if clear:
					cmd.cutKey( attrpath, t=(clearStart, clearEnd), cl=True )

				#is there an anim curve on the target attrpath already?
				curveExists = cmd.keyframe(attrpath, index=(0,), q=True) is not None

				preValue = 0
				if additive:
					if worldAdditive:
						isWorld = True

						#if the control has space switching setup, see if its value is set to "world" - if its not, we're don't treat the control's animation as additive
						try: isWorld = cmd.getAttr('%s.parent' % obj, asString=True) == 'world'
						except TypeError: pass

						#only treat translation as additive
						if isWorld and attr.startswith('translate'):
							preValue = cmd.getAttr(attrpath)
					else:
						preValue = cmd.getAttr(attrpath)

				for time, value, itt, ott, ix, iy, ox, oy, isLocked, isWeighted in keyList:
					value *= mult
					value += preValue
					if time is None:
						#in this case the attr value was just a pose...
						cmd.setAttr( attrpath, value )
					else:
						time += timeOffset
						cmd.setKeyframe( attrpath, t=(time,), v=value )
						if weightedTangents:
							#this needs to be done as two separate commands - because setting the tangent types in the same cmd as setting tangent weights can result
							#in the tangent types being ignored (for the case of stepped mainly, but subtle weirdness with flat happens too)
							cmd.keyTangent( attrpath, t=(time,), ix=ix, iy=iy, ox=ox, oy=oy, l=isLocked, wl=isWeighted )
							cmd.keyTangent( attrpath, t=(time,), itt=itt, ott=ott )
						else:
							cmd.keyTangent( attrpath, t=(time,), ix=ix, iy=iy, ox=ox, oy=oy )

		#cmd.keyTangent( e=True, g=True, wt=beginningWeightedTanState )
	def getKeyTimes( self ):
		'''
		returns an ordered list of key times
		'''
		keyTimesSet = set()
		for obj, attrDict in self.iteritems():
			for attr, (weightedTangents, keyList) in attrDict.iteritems():
				if keyList[0][0] is None:
					continue

				for tup in keyList:
					keyTimesSet.add( tup[0] )

		keyTimes = list( keyTimesSet )
		keyTimes.sort()

		return keyTimes
	def getRange( self ):
		'''
		returns a tuple of (start, end)
		'''
		times = self.getKeyTimes()
		try:
			start, end = times[0], times[-1]
			self.offset = start
		except IndexError:
			start, end = 0, 0
			self.__range = 0

		return start, end
	def getRangeValue( self ):
		try:
			return self.__range
		except AttributeError:
			self.getRange()
			return self.__range
	range = property(getRangeValue)
	def generatePreArgs( self ):
		return tuple()


kEXPORT_DICT_THE_CLIP = 'clip'
kEXPORT_DICT_CLIP_TYPE = 'clip_type'
kEXPORT_DICT_OBJECTS = 'objects'
kEXPORT_DICT_WORLDSPACE = 'worldspace'
class ClipPreset(Preset):
	'''
	a clip preset is different from a normal preset because it is actually two separate files - a
	pickled animation data file, and an icon
	'''
	TYPE_CLASSES = {kPOSE: PoseClip,
					kANIM: AnimClip,
					kDELTA: None}
	TYPE_LABELS = {kPOSE: 'pose',
				   kANIM: 'anim',
				   kDELTA: 'delta'}

	### auto generate a label types
	LABEL_TYPES = {}
	for t, l in TYPE_LABELS.iteritems():
		LABEL_TYPES[l] = t

	def __new__( cls, locale, library, name, type=kPOSE ):
		tool = '%s/%s' % (TOOL_NAME, library)
		typeLbl = cls.TYPE_LABELS[type]
		ext = '%s.%s' % (typeLbl, kEXT)

		self = Preset.__new__( cls, locale, tool, name, ext )
		self.icon = Preset( locale, tool, name, '%s.bmp' % typeLbl )

		return self
	def asClip( self ):
		presetDict = self.unpickle()
		return presetDict[ kEXPORT_DICT_THE_CLIP ]
	def niceName( self ):
		return self.name().split('.')[0]
	def getLibrary( self ):
		return self[-2]
	def setLibrary( self, library ):
		self[-2] = library
	def getTypeName( self ):
		return self.name().split('.')[ -1 ]
	def getType( self ):
		typeLbl = self.getTypeName()
		return self.LABEL_TYPES[typeLbl]
	def move( self, library=None ):
		if library is None:
			library = self.getLibrary()

		newLoc = ClipPreset(self.other(), library, self.niceName(), self.getType())

		#perform the move...
		Path.move(self, newLoc)
		Path.move(self.icon, newLoc.icon)

		return newLoc
	def copy( self, library=None ):
		if library is None:
			library = self.library

		newLoc = ClipPreset(self.other(), library, self.niceName(), self.getType())

		#perform the copy...
		Path.copy(self, newLoc)
		Path.copy(self.icon, newLoc.icon)

		return newLoc
	def rename( self, newName ):
		'''
		newName should be the base name - sans any clip type id or extension...
		'''
		newName = '%s.%s' % (scrubName(newName), self.getTypeName())
		Preset.rename(self, newName)
		self.icon.rename(newName)
	def delete( self ):
		Path.delete(self)
		self.icon.delete()
	@api.d_noAutoKey
	def apply( self, objects, **kwargs ):
		presetDict = self.unpickle()
		srcObjs = presetDict[ kEXPORT_DICT_OBJECTS ]
		clip = presetDict[ kEXPORT_DICT_THE_CLIP ]

		#do a version check - if older version clip is being used - perhaps we can write conversion functionality?
		try:
			ver = presetDict[ kEXPORT_DICT_TOOL_VER ]
			if ver != VER:
				api.melWarning("the anim clip version don't match!")
		except KeyError:
			api.melWarning("this is an old VER 1 pose clip - I don't know how to load them anymore...")
			return

		#generate the name mapping
		slamApply = kwargs.get( 'slam', False )
		if slamApply:
			objects = cmd.ls( typ='transform' )
			tgts = names.matchNames( srcObjs, objects, threshold=kDEFAULT_MAPPING_THRESHOLD )
			mapping = Mapping( srcObjs, tgts )
		else:
			tgts = names.matchNames( srcObjs, objects, threshold=kDEFAULT_MAPPING_THRESHOLD )
			mapping = Mapping( srcObjs, tgts )

		#run the clip's apply method
		clip.apply( mapping, **kwargs )
	def getClipObjects( self ):
		'''
		returns a list of all the object names contained in the clip
		'''
		presetDict = self.unpickle()
		srcObjs = presetDict[ kEXPORT_DICT_OBJECTS ]

		return srcObjs
	def write( self, objects, **kwargs ):
		type = self.getType()
		clipDict = api.writeExportDict( TOOL_NAME, VER )
		clipDict[ kEXPORT_DICT_CLIP_TYPE ] = type
		clipDict[ kEXPORT_DICT_OBJECTS ] = objects
		clipDict[ kEXPORT_DICT_WORLDSPACE ] = False

		theClip = self.TYPE_CLASSES[ type ]()
		theClip.generate( objects, **kwargs )
		clipDict[ kEXPORT_DICT_THE_CLIP ] = theClip

		#write the preset file to disk
		self.pickle( clipDict )

		#generate the icon for the clip and add it to perforce if appropriate
		icon = generateIcon( self )
		icon.asP4().add()


class ClipManager(PresetManager):
	'''
	an abstraction for listing libraries and library clips for clip presets - there are two
	main differences between clip presets and other presets - clips have a library which is
	a subdir of the main preset dir, and there are also multiple types of clips both with
	the same extension.
	'''
	def __init__( self ):
		PresetManager.__init__(self, TOOL_NAME, kEXT)
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

		for locale in LOCAL, GLOBAL:
			localeDict[locale] = libraries = []
			dirs = self.getPresetDirs(locale)
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
		newLibraryPath = Preset(LOCAL, TOOL_NAME, name, '')
		newLibraryPath.create()
	def getLibraryClips( self, library ):
		global kEXT

		clips = {LOCAL: [], GLOBAL: []}
		for locale in LOCAL, GLOBAL:
			localeClips = clips[locale]
			for dir in getPresetDirs(locale, TOOL_NAME):
				dir += library
				if not dir.exists:
					continue

				for f in dir.files():
					if f.hasExtension( kEXT ):
						f = f.setExtension()
						name, type = f[ -1 ].split('.')
						f = f[ :-1 ]
						type = ClipPreset.LABEL_TYPES[ type ]
						localeClips.append( ClipPreset(locale, library, name, type) )

		return clips
	def getPathToLibrary( self, library, locale=LOCAL ):
		return getPresetDirs(locale, TOOL_NAME)[0] / library
	def reload( self ):
		pass


#end
