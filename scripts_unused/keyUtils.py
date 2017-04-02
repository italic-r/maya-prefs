import vectors, cPickle, names, math, time, datetime, mayaVectors, api
import exportManagerCore
import maya.cmds as cmd
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim
import bisect, os


g_defaultKeyUtilsPickle = 'd:/temp.pickle'
g_validWorldAttrs = ('translateX','translateY','translateZ','rotateX','rotateY','rotateZ')
mel = api.mel


PRIMARY_NAMES =          ['NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
PRIMARY_ROTATIONS =      [-45,  -90, -135, 180, 135,  90,   45]
PRIMARY_SPEEDS =         [1.0,  1.0, 1.0,  1.0, 1.0,  1.0,  1.0]
PRIMARY_START_FRAMES =   [60,   120, 180,  240, 300,  360,  420]


#SECONDARY_ROTATIONS =    [-45,  -90,  -135, -180, 135, 90,  45]
#SECONDARY_SPEEDS =       [0.85, 0.68, 0.85, 0.6, 0.85, 0.68, 0.85]
#SECONDARY_STARTS =       [ 60,  120,  180,  240, 300,  360,  420 ]
#SECONDARY_NAMES =        [ 'NE', 'E', 'SE', 'S', 'SW',  'W', 'NW']


class MatrixAtTime(mayaVectors.MayaMatrix):
	#simply stores time along with a matrix...
	def __init__( self, values=(), size=4, time=None ):
		if isinstance(values,MatrixAtTime):
			time = values.time
			values = values.as_list()

		mayaVectors.MayaMatrix.__init__(self,values,4)
		self.time = time


#this decorator turns off all the "slow things" when doing time change operations...
def noUpdate(f):
	def actualFunc(*args):
		start = time.clock()
		initialAutoKeyState = cmd.autoKeyframe(q=True,state=True)
		cmd.autoKeyframe(state=False)
		api.mel.zooAllViews(0)

		retVal = f(*args)

		api.mel.zooAllViews(1)
		cmd.autoKeyframe(state=initialAutoKeyState)
		print 'time taken',time.clock()-start,'secs'
		return retVal
	return actualFunc


class Key(object):
	'''this is simply a convenient abstraction of a key object in maya - which doesn't
	really exist...  working with key data is a pain in the ass.  you can specify either
	a key time or a key index when creating an instance.  if both are specifed, index is
	used.  if time is specified, and there is no key at that time, a phantom key is
	created using the curve value at that point - the index is set to -1 in this case,
	and tangent data is guessed'''
	def __init__( self, obj=None, attr=None, time=None, value=None, idx=None, populateTangents=True ):
		#if the attrpath doesn't exist, then just create an empty key instance
		self.idx = idx
		self.obj, self.attr, self.time, self.value = obj, attr, time, value
		self.iw, self.ow, self.ia, self.oa = 1.0, 1.0, 0, 0
		self.itt, self.ott, self.lock = 'linear', 'linear', True

		if obj is None or attr is None: return

		#make sure the attr name is the long version of the name, its too annoying to have to deal with shortnames AND long names...
		#self.attr = cmd.attributeQuery(self.attr,longName=True,node=self.obj)
		#self.attrShort = cmd.attributeQuery(self.attr,shortName=True,node=self.obj)

		#populating tangents is slow - so only do it when required
		if populateTangents: self.populateTangents()
	def copy( self ):
		new = self.__class__()
		new.idx = self.idx
		new.obj, new.attr, new.time, new.value = self.obj, self.attr, self.time, self.value
		new.iw, new.ow, new.ia, new.oa = self.iw, self.ow, self.ia, self.oa
		new.itt, new.ott, new.lock = self.itt, self.ott, self.lock

		return new
	def get_attrpath( self ):
		return '%s.%s'%(self.obj,self.attr)
	attrpath = property(get_attrpath)
	def populateTangents( self ):
		#is there a key at the time?
		attrpath = self.attrpath
		if cmd.keyframe(attrpath,time=(keyTime,),query=True,keyframeCount=True):
			self.value = cmd.keyframe(attrpath,time=(keyTime,),query=True,valueChange=True)[0]
			self.iw,self.ow,self.ia,self.oa = cmd.keyTangent(attrpath,time=(keyTime,),query=True,inWeight=True,outWeight=True,inAngle=True,outAngle=True)
			self.itt,self.ott = cmd.keyTangent(attrpath,time=(keyTime,),query=True,inTangentType=True,outTangentType=True)
			self.lock = cmd.keyTangent(attrpath,time=(keyTime,),query=True,lock=True)[0]

			#this is purely 'clean up after maya' code.  for whatever reason maya will return a tangent type of "fixed" even though its a completely invalid tangent type...  not sure what its supposed to map to, so I'm just assuming spline
			if self.itt == 'fixed': self.itt = 'spline'
			if self.ott == 'fixed': self.ott = 'spline'
		else:
			self.idx = self.get_index()
			self.value = cmd.keyframe(attrpath,time=(self.time,),query=True,eval=True,valueChange=True)
			index = self.idx
			previousOutTT = None
			previousOutTW = None
			nextInTT = None
			nextInTW = None
			if index > 1:
				previousOutTT = cmd.keyTangent(attrpath,index=(index-1,),query=True,outTangentType=True)
				previousOutTW = cmd.keyTangent(attrpath,index=(index-1,),query=True,outWeight=True)
			else:
				previousOutTT = cmd.keyTangent(attrpath,index=(index,),query=True,outTangentType=True)
				previousOutTW = cmd.keyTangent(attrpath,index=(index,),query=True,outWeight=True)

			if index < cmd.keyframe(self.attr,query=True,keyframeCount=True):
				nextInTT = cmd.keyTangent(attrpath,index=(index+1,),query=True,inTangentType=True)
				nextInTW = cmd.keyTangent(attrpath,index=(index+1,),query=True,inWeight=True)
			else:
				nextInTT = cmd.keyTangent(attrpath,index=(index,),query=True,inTangentType=True)
				nextInTW = cmd.keyTangent(attrpath,index=(index,),query=True,inWeight=True)

			#now average the tangents
				self.iw = self.ow = (previousOutTW + nextInTW )/2
	def __str__( self ):
		return '%.2f'% (self.time,)
	def __repr__( self ):
		return self.__str__()
	def __cmp__( self, other, tolerance=1e-4 ):
		if isinstance(other,Key): other = other.time
		if abs(self.time-other) <= tolerance : return 0
		if self.time - other < 0: return -1
		return 1
	def offset( self, amount ):
		#time offsets the channel by a given time delta
		self.time += amount
	def get_index( self ):
		'''returns the key object's index'''
		return cmd.keyframe(self.attr,time=(":%f"+self.time,),query=True,keyframeCount=True)-1


class Channel(object):
	'''a channel is simply a list of key objects with some convenience methods attached'''
	def __init__( self, obj=None, attr=None, start=None, end=None, populateTangents=True ):
		self.obj = obj
		self.attr = attr
		self.weighted = True
		self.keys = []

		#unless an attrpath has been specified, we're done...
		if obj is None or attr is None: return
		attrpath = '.'.join((obj,attr))

		if start is None:
			#get the timecount of the first key
			start = cmd.keyframe(attrpath,index=(0,),query=True)[0]
		if end is None:
			#get the timecount of the first key
			lastKeyIdx = cmd.keyframe(attrpath,keyframeCount=True,query=True)-1
			end = cmd.keyframe(attrpath,index=(lastKeyIdx,),query=True)[0]

		self.attr = str( cmd.attributeQuery(self.attr,longName=True,node=self.obj) )
		self.attrShort = str( cmd.attributeQuery(self.attr,shortName=True,node=self.obj) )
		self.weighted = cmd.keyTangent(attrpath,query=True,weightedTangents=True)

		if self.weighted == 1: self.weighted = True
		else: self.weighted = False

		if cmd.objExists(attrpath):
			times = cmd.keyframe(attrpath,time=(start,end),query=True)
			values = cmd.keyframe(attrpath,time=(start,end),query=True,vc=True)

			#if there are no keys - bail
			if times is None: return
			self.keys = [Key(obj,attr,time=k,value=v,populateTangents=False) for k,v in zip(times,values)]
			if populateTangents:
				#querying heaps of tangent data at once is much more efficient than throwing a query for
				#each key created - so although uglier, its quite significantly faster...
				iws = cmd.keyTangent(attrpath,time=(start,end),query=True,iw=True)
				ows = cmd.keyTangent(attrpath,time=(start,end),query=True,ow=True)
				ias = cmd.keyTangent(attrpath,time=(start,end),query=True,ia=True)
				oas = cmd.keyTangent(attrpath,time=(start,end),query=True,oa=True)
				itts = cmd.keyTangent(attrpath,time=(start,end),query=True,itt=True)
				otts = cmd.keyTangent(attrpath,time=(start,end),query=True,ott=True)
				locks = cmd.keyTangent(attrpath,time=(start,end),query=True,lock=True)

				#remove all instances of 'fixed' tangent types.  maya will return a type of fixed, but it throws an exception if
				#you try to set a tangent type of fixed...  nice...
				try:
					while True: itts.remove('fixed')
				except ValueError: pass
				try:
					while True: otts.remove('fixed')
				except ValueError: pass

				#
				for key,iw,ow,ia,oa,itt,ott,lock in zip(self.keys,iws,ows,ias,oas,itts,otts,locks):
					key.iw,key.ow,key.ia,key.oa,key.itt,key.ott,key.lock = iw,ow,ia,oa,itt,ott,lock

			self.keys.sort()
	@classmethod
	def FromChannel( cls, channel, keys=None ):
		new = cls()
		new.obj = channel.obj
		new.attr = channel.attr
		new.attrShort = channel.attrShort
		new.weighted = channel.weighted
		if keys is None: new.keys = [key.copy() for key in channel.keys]
		else: new.keys = [key.copy() for key in keys]

		return new
	def copy( self ):
		return Channel.FromChannel(self)
	def get_attrpath( self ):
		return '%s.%s'%(self.obj,self.attr)
	attrpath = property(get_attrpath)
	def get_start( self ):
		keyTimes = [key.time for key in self.keys]
		if len(keyTimes): return min(keyTimes)
	start = property(get_start)
	def get_end( self ):
		keyTimes = [key.time for key in self.keys]
		if len(keyTimes): return max(keyTimes)
	end = property(get_end)
	def get_values( self ):
		values = []
		for key in self.keys:
			values.append(key.value)
		return values
	values = property(get_values)
	def __str__( self ):
		return '%s %s'%(self.attrpath, str(self.keys))
	def __repr__( self ):
		return self.__str__()
	def __nonzero__( self ):
		return bool(self.keys)
	def __add__( self, other ):
		assert isinstance(other,Channel)
		newChannel = self.copy()

		#so when adding channels, if there are two keys on the same frame, their values get added together
		#TODO: if not, then find surrounding keys (if any) and do a value lerp to add to the key value
		for key in other.keys:
			keyAtTime = self[key.time]
			if keyAtTime:
				keyAtTime.keys[0].value += key.value
			else:
				newChannel.keys.append(key)

		newChannel.keys.sort()

		return newChannel
	def __getitem__( self, timeValue ):
		'''so this returns a slice based on a time value NOT and index.  NOTE: the slice step is ignored - it
		doesn't really make any sense'''
		if isinstance(timeValue,slice):
			start_idx = bisect.bisect_left(self.keys,timeValue.start)
			end_idx = bisect.bisect(self.keys,timeValue.stop)
			keys = self.keys[start_idx:end_idx]
			newChannel = Channel.FromChannel(self,keys)

			return newChannel

		try:
			idx = bisect.bisect_left(self.keys,timeValue)
			key = self.keys[idx]
			if abs(timeValue-key.time)<=1e-4: return Channel.FromChannel(self,[key])
		except IndexError:
			return Channel.FromChannel(self,[])
	def __len__( self ):
		return len(self.keys)
	def offset( self, amount ):
		#time offsets the channel by a given time delta
		[key.offset(amount) for key in self.keys]
	def transform( self, transformFunction ):
		#transforms all key values by the given transform function.  the first arg passed to the transform function is the key
		#the return value should also be a key object
		self.keys = [transformFunction(key) for key in self.keys]
	def applyToObj( self, obj, applyAsWorld=False, clearFirst=False ):
		'''applies the current channel to a given attrpath'''
		tgtAttrpath = '.'.join((obj,self.attr))
		if not cmd.objExists(tgtAttrpath): return
		if clearFirst:
			if self.start is not None:
				cmd.cutKey(tgtAttrpath,t=(self.start,self.end),cl=True)

		if applyAsWorld and self.hasWorld:
			#apply as world - NOT DONE YET
			for key in self.keys:
				cmd.setKeyframe(tgtAttrpath,time=(key.time,),value=key.value,inTangentType=key.itt,outTangentType=key.ott)
				cmd.keyTangent(tgtAttrpath,time=(key.time,),edit=True,inWeight=key.iw,outWeight=key.ow,inAngle=self.ia,outAngle=self.oa)
		else:
			#set this initial dummy keyframe so we can set the curve's (whcih may not exist) weightedness
			if len( self.keys ):
				cmd.setKeyframe(tgtAttrpath,time=(self.keys[0].time,))
				cmd.keyTangent(tgtAttrpath,edit=True,weightedTangents=self.weighted)

			#if self.weighted: print "hi i'm weighting ur tangents..."
			for key in self.keys:
				cmd.setKeyframe(tgtAttrpath,time=(key.time,),value=key.value,inTangentType=key.itt,outTangentType=key.ott)
				#cmd.keyTangent(tgtAttrpath,time=(key.time,),edit=True,lock=key.lock,inWeight=key.iw,outWeight=key.ow,inAngle=key.ia,outAngle=key.oa)
	def getTurningPoints( self ):
		'''returns a list of keys that are turning points'''
		if len(self.keys) < 3:
			return []

		turningPoints = []
		keyIter = iter(self.keys)
		prevKey = keyIter.next()
		curKey = keyIter.next()
		nextKey = keyIter.next()
		while True:
			try:
				prevValue = prevKey.value - curKey.value
				nextValue = nextKey.value - curKey.value
				if ( prevValue<0 and nextValue<0 ) or ( prevValue>0 and nextValue>0 ):
					#in this case nextKey is a turning point
					turningPoints.append(curKey)

				prevKey = curKey
				curKey = nextKey
				nextKey = keyIter.next()
			except StopIteration:
				break

		return turningPoints
	def keyReduce( self ):
		#get the nodeType of the animCurve driving this channel
		animCurve = cmd.listConnections('%s.%s'%(self.obj,self.attr),type='animCurve',destination=False)[0]
		nodeType = cmd.nodeType(animCurve)

		#create an array to hold the "reduced" set of keys to create - start/end and turning points are mandatory
		newKeys = [self.keys[0]] + self.getTurningPoints() + [self.keys[-1]]

		#create the new animCurve - we do this because asking maya to query the interpolation between keys is way easier than doing it via script
		reduce = cmd.createNode(nodeType)
		for key in newKeys: cmd.setKeyframe(reduce,time=(key.time,),value=key.value,inTangentType='linear',outTangentType='linear')

		#
		return reduce


class Clip(object):
	'''creates a convenient abstraction of a collection of animation data on multiple
	channels.  supports adding, removing etc...  if start and end aren't specified, it
	uses the entire range.  if channels isn't specified, assumes all keyable channels'''
	def __init__( self, obj=None, start=None, end=None, channels=None, populateTangents=True ):
		#create object attrs
		self.obj = obj
		self.channels = {}
		self.world = []

		if obj is None:
			return

		#if channels is the default value, assume all keyable channels on the node
		if channels == None:
			attributes = cmd.listAttr(obj,keyable=True,multi=True,scalar=True)
			channels = [str(a) for a in attributes if cmd.keyframe(obj+'.'+a,query=True,keyframeCount=True)]

		for channel in channels:
			newChannel = Channel(obj,channel,start,end,populateTangents)
			self.channels[channel] = newChannel
	@classmethod
	def FromClip( cls, clip, channels=None, world=None ):
		new = cls()
		new.obj = clip.obj
		if channels is None:
			for name,channel in clip.channels.iteritems():
				new.channels[name] = channel.copy()
		else:
			for name,channel in channels.iteritems():
				new.channels[name] = chan.copy()

		if world is None: new.world = [mat.copy() for mat in clip.world]
		else: new.world = [mat.copy() for mat in world]

		return new
	def copy( self ):
		return Clip.FromClip(self)
	def __str__( self ):
		asStr = '\n'.join( map(str,self.channels.values()) )
		return asStr
	def __getattr__( self, attr ):
		return self.channels[attr]
	def __contains__( self, item ):
		return item in self.channels
	def get_start( self ):
		starts = []
		for channel in self.channels:
			starts.append(channel.start)
		return min(starts)
	start = property(get_start)
	def get_end( self ):
		ends = []
		for channel in self.channels:
			ends.append(channel.end)
		return max(ends)
	end = property(get_end)
	def _hasWorld( self ):
		return not( not self.world )
	hasWorld = property(_hasWorld)
	def __add__( self, other ):
		assert isinstance(other,Clip)
		newClip = self.copy()

		for name,channel in newClip.channels.iteritems():
			if name in other.channels:
				newClip.channels[name] = newClip[name]+other[name]

		#deal with world matricies - so if two matricies exist on the same frame, then we need to merge them
		if other.world:
			newWorld = []
			for matB in other.world:
				matA = None
				for m in newClip.world:
					if m.time == matB.time: matA = m

				if matA is not None:
					#in this case, we need to merge the two matricies together...
					posA = matA.pos
					posB = matB.pos
					newPos = (posA+posB)/2

					quatA = vectors.Quaternion(matA)
					quatB = vectors.Quaternion(matB)
					newQuat = (quatA/2)*(quatB/2)
					mergedMat = MatrixAtTime(newQuat,time=matB.time)
					mergedMat.pos = newPos
					newWorld.append( mergedMat )
				else:
					newWorld.append(matB)
			newClip.world = newWorld

		return newClip
	def __getitem__( self, item ):
		#so this returns a slice based on a time value NOT and index.  NOTE: the slice step is ignored - it
		#doesn't really make any sense
		if isinstance(item,basestring):
			return self.channels[item]

		newChannels = {}
		for name,channel in self.channels.iteritems():
			newChannels[name] = channel[item]
		worldTimes = [mat.time for mat in self.world]
		if isinstance(item,slice):
			start_idx = bisect.bisect_left(worldTimes,item.start)
			end_idx = bisect.bisect(worldTimes,item.stop)
			newWorld = worldTimes[start_idx:end_idx]
			newClip = Clip.FromClip(self,newChannels,newWorld)

			return newClip

		newWorld = []
		if self.hasWorld:
			idx = bisect.bisect_left(worldTimes,item)
			newWorld.append(self.world[idx])
			abs(item-newWorld[0])<=1e-4
		return Clip.FromClip(self,newChannels,newWorld)
	def __len__( self ):
		return len(self.keys)
	def offset( self, amount ):
		#time offsets the channel by a given time delta
		[channel.offset(amount) for channel in self.channels.values()]
		for mat in self.world:
			mat.time += amount
	def transform( self, transformFunction ):
		#transforms all key values by the given transform function.  the first arg passed to the transform function is the key
		[channel.transform(transformFunction) for channel in self.channels.values()]
	def get_channels( self, channelListToGet ):
		resultingChannels = []
		for name in channelListToGet:
			resultingChannels.append(getattr(self,name))

		return resultingChannels
	def listKeysInOrder( self, channels=None ):
		'''returns a list of the clip's keys in ascending temporal order'''
		if not channels: channels = self.channels

		#do a DSU sort...
		keys = [(key.time,key) for key in self.keys]
		keys.sort()
		keys = [x[1] for x in keys]

		return keys
	keys = property(listKeysInOrder)
	def as_frames( self, channels=None ):
		'''bundles the keys in this channel into groups of unique times - we call these frames.  ie: each frame has one or more keys at that time and ONLY that time
		return value is a list of lists (a list of frames).  each frame contains all the keys at that time'''
		keys = self.listKeysInOrder(channels)
		prevTime = keys[0].time
		frames = [(prevTime,[keys[0]])]
		curList = frames[0][1]
		for key in keys:
			if prevTime != key.time:
				prevTime = key.time
				nextFrame = (prevTime,[])
				frames.append(nextFrame)
				curList = nextFrame[1]
			curList.append(key)

		return frames
	frames = property(as_frames)
	def as_keys( self ):
		keys = []
		for channel in self.channels.values():
			keys += channel.keys
		return keys
	keys = property(as_keys)
	def get_times( self, channelStrs=None ):
		#returns a set of time values for all keys in this clip - optionally only on a given list of channels
		if channelStrs is None:
			channelStrs = self.channels.keys() #NOTE: channels is a dict

		times = set()
		for channelStr in channelStrs:
			if channelStr not in self:
				continue
			for key in self[channelStr].keys:
				times.add( key.time )

		return times
	def applyToObj( self, obj=None, applyAsWorld=False, clearFirst=False ):
		'''applies the current clip to an object - if the animation is being applied as world space, first check to make
		sure the world space animation for the clip exists.  then separate the transform channels out of the channels list
		and apply them as world space data.  then we need to apply the rest of the channels as per normal'''
		if obj is None:
			obj = self.obj

		if applyAsWorld and self.hasWorld:
			for matrix in self.world:
				cmd.currentTime(matrix.time)
				tfn = OpenMaya.MFnTransform( api.getMDagPath(obj) )
				tfn.set( OpenMaya.MTransformationMatrix( key[0] ) )

			'''nonTransformChannels = []
			for channel in self.channels:
				if channel.attr not in g_validWorldAttrs: nonTransformChannels.append(channel)

			frames = self.as_frames(transformChannels)
			for channel in self.world:
				tgtAttrpath = obj +'.'+ channel.attr
				channel.applyToObj(obj,applyAsWorld)

			#run a euler filter over the resulting rotation animation - converting to world space
			#rotations often causes all sorts of nasty euler flips
			maya.mel.eval('filterCurve %s.rx %s.ry %s.rz;'%(obj,obj,obj))

			for channel in transformChannels:
				channel.applyToObj(obj)'''
		else:
			for channel in self.channels.values():
				channel.applyToObj(obj,clearFirst=clearFirst)
	def populateWorld( self, time=None ):
		if time is None:
			time = cmd.currentTime(q=True)

		mat = MatrixAtTime.FromObject(self.obj,True)
		mat.time = time

		self.world.append(mat)
	@noUpdate
	def getWorld( self ):
		'''saves world space matricies for each animation frame in the clip - ie for each transform key a world space matrix
		is saved in the self.world list'''
		orgTime = cmd.currentTime(q=True)
		for time,keys in self.frames:
			cmd.currentTime(time)
			self.populateWorld(time)

		cmd.currentTime(orgTime) #restore time


class Animation(object):
	def __init__( self, objs=None, start=None, end=None, channels=None ):
		self.clips = {}

		#we need to store objs in a list so we can preserve ordering - when re-applying an animation clip back to a collection of objects, we don't want to have to worry about a mapping - hence ordering is important
		self.objs = objs

		if objs is not None:
			for obj in objs:
				self.clips[obj] = Clip(obj,start,end,channels)
	@classmethod
	def FromAnimation( cls, animation, clips=None ):
		new = cls()
		if clips is None:
			for name,clip in animation.clips.iteritems():
				new.clips[name] = clip.copy()
		else:
			for name,clip in clips.iteritems():
				new.clips[name] = clip.copy()

		return new
	def copy( self ):
		return Animation.FromAnimation(self)
	def __str__( self ):
		asStr = '\n'.join( map(str,self.clips.values()) )
		return asStr
	def __getattr__( self, attr ):
		return self.clips[attr]
	def __getitem__( self, item ):
		if isinstance(item,basestring):
			return self.clips[item]

		newClips = {}
		for name,clip in self.clips.iteritems():
			newClips[name] = clip[item]
		return Animation.FromAnimation(self,newClips)
	def __add__( self, other ):
		assert isinstance(other,Animation)
		newAnim = self.copy()

		for obj,clip in self.clips.iteritems():
			if obj in other.clips:
				newAnim.clips[obj] = newAnim[obj] + other[obj]

		return newAnim
	def __contains__( self, item ):
		return item in self.clips
	def get_start( self ):
		starts = []
		for clip in self.clips:
			starts.append(clip.start)
		return min(starts)
	start = property(get_start)
	def get_end( self ):
		ends = []
		for clip in self.clips:
			ends.append(channel.end)
		return max(ends)
	end = property(get_end)
	def _hasWorld( self ):
		return not( not self.world )
	hasWorld = property(_hasWorld)
	def offset( self, amount ):
		[clip.offset(amount) for clip in self.clips.values()]
	def transform( self, transformFunction ):
		#transforms all key values by the given transform function.  the first arg passed to the transform function is the key
		[clip.transform(transformFunction) for clip in self.clips]
	def get_times( self, channels=None ):
		transformTimes = set()
		for clip in self.clips.values():
			times = clip.get_times(channels)
			transformTimes = transformTimes.union( times )

		transformTimes = list(transformTimes)
		transformTimes.sort()

		return transformTimes
	@noUpdate
	def getWorld( self, objs=None, channels=None ):
		clips = self.clips.values() if objs is None else [self.clips[obj] for obj in objs]
		transformTimes = set()
		clipTimeSets = []
		for clip in clips:
			times = set( clip.get_times(channels) )
			transformTimes = transformTimes.union( times )
			clipTimeSets.append( times )

		transformTimes = list(transformTimes)
		transformTimes.sort()

		orgTime = cmd.currentTime(q=True)
		for time in transformTimes:
			cmd.currentTime(time)
			for clip,clipTimeSet in zip(clips,clipTimeSets):
				if time not in clipTimeSet:
					continue

				clip.populateWorld(time)

		cmd.currentTime(orgTime) #restore time
	def applyToObjs( self, objs=None, applyAsWorld=False, clearFirst=False ):
		if objs is None:
			for obj,clip in self.clips.iteritems():
				clip.applyToObj(obj,applyAsWorld,clearFirst)
		else:
			for n,obj in enumerate(objs):
				self.clips[ self.objs[n] ].applyToObj(obj,applyAsWorld,clearFirst)


def write( object, filepath ):
	sourceSceneData = {}
	sourceSceneData['file'] = cmd.file(q=True,sn=True)
	sourceSceneData['mayaVersion'] = cmd.about(version=True)
	sourceSceneData['datetime'] = datetime.datetime.today()
	sourceSceneData['env'] = os.environ

	fileobj = file(filepath,'wb')
	cPickle.dump( (sourceSceneData, object), fileobj, True )
	fileobj.close()


def load( filepath ):
	fileobj = file(filepath,'rb')
	new = cPickle.load(fileobj)
	fileobj.close()

	return new


def createCompassRun():
	namespace = ''
	worldSpaceObjs = ['leg_L','leg_R','root','arm_L','arm_R']


def propagateChanges():
	pass


def generatePrimary( baseStart, baseEnd ):
	generate( baseStart, baseEnd, PRIMARY_ROTATIONS, PRIMARY_SPEEDS, PRIMARY_START_FRAMES, PRIMARY_NAMES )


def generate( baseStart, baseEnd,\
			  rotations =               PRIMARY_ROTATIONS,\
			  strideLengthMultipliers = PRIMARY_SPEEDS,\
			  starts =                  PRIMARY_START_FRAMES,\
			  directions =              PRIMARY_NAMES ):

	#determine which ctrl set to use
	ctrlSet = names.matchNames(['body_ctrls'],cmd.ls(type='objectSet'),threshold=1)
	if not ctrlSet:
		raise Exception('control set not found')
	ctrlSet = ctrlSet[0]

	ctrls = cmd.sets(ctrlSet,q=True)
	length = baseEnd-baseStart
	num = len(rotations)


	#does the base locomote have an asset?
	vx = exportManagerCore.ExportManager()
	baseAsset = vx.exists(start=baseStart,end=baseEnd)
	infoNode = ''
	exportSet = ''
	if len(baseAsset):
		baseAsset = baseAsset[0]
		exportSet = baseAsset.obj
	else:
		#if it doesn't exist, try and create one
		infoNodes = cmd.ls(type='vstInfo')
		candidates = []
		for node in infoNodes:
			if not cmd.referenceQuery(node,inr=True): continue
			if not cmd.listRelatives(node): continue
			candidates.append(node)
		infoNode = candidates[0]
		exportSet = exportManagerCore.ExportManager.CreateExportSet( [infoNode] )

		#now build the actual asset
		asset = vx.createAsset(exportSet)
		asset.setAttr('start', baseStart)
		asset.setAttr('end', baseEnd)
		asset.setAttr('name', 'N')
		asset.setAttr('type', exportManagerCore.ExportComponent.kANIM)


	#grab the list of ctrls we need to actually transform
	toFind = [ 'upperBodyControl', 'legControl_L', 'legControl_R' ]#, 'armControl_L', 'armControl_R' ]
	xformCtrls = [ name for name in names.matchNames( toFind, ctrls, parity=True, threshold=0.8 ) if name != '' ]

	animation = Animation( ctrls, baseStart, baseEnd )
	animation.getWorld(xformCtrls,['translateX','translateZ'])

	#save the animation out - useful for doing deltas later on
	#write(animation,g_defaultKeyUtilsPickle)

	#build the rotation axis
	axis = vectors.Vector([0, 1, 0])

	for n in xrange(num):
		offset = starts[n]-baseStart

		tmpAnim = animation.copy()
		tmpAnim.offset( offset )

		#convert angles to radians, and do other static calcs
		angle = rotations[n]
		angle = math.radians(angle)
		quat = vectors.Quaternion.AxisAngle( axis, angle )

		for ctrl in xformCtrls:
			clip = tmpAnim[ctrl]

			#do the actual rotation around Y
			mats = clip.world
			translateX = clip.translateX.keys = []
			translateZ = clip.translateZ.keys = []
			for mat in mats:
				pos = mat.get_position()
				pos = pos.rotate(quat)
				mat[3][:3] = pos

				translateX.append( Key( time=mat.time, value=pos.x ) )
				translateZ.append( Key( time=mat.time, value=pos.z ) )

			#now do stride length multiplication
			strideMult = strideLengthMultipliers[n]
			if strideMult is not None:
				def makeShorter( key ):
					key.value *= strideMult
					return key

				clip.translateX.transform(makeShorter)
				clip.translateZ.transform(makeShorter)

		tmpAnim.applyToObjs(clearFirst=True)

		#finally create an asset for the new anim
		existing = vx.exists( start=starts[n], end=starts[n]+length, name=directions[n] )
		if not len(existing):
			asset = vx.createAsset( exportSet )
			asset.setAttr('start', starts[n])
			asset.setAttr('end', starts[n]+length)
			asset.setAttr('name', directions[n])
			asset.setAttr('type', exportManagerCore.ExportComponent.kANIM)


def motionList( obj, start, end ):
	#creates a list of positions at each frames over a given time range
	motion = []
	for n in xrange(start,end+1): #add one because this is an inclusive range
		curX = cmd.keyframe(obj +'.tx',t=(n,),q=True,ev=True)[0]
		curY = cmd.keyframe(obj +'.ty',t=(n,),q=True,ev=True)[0]
		curZ = cmd.keyframe(obj +'.tz',t=(n,),q=True,ev=True)[0]
		motion.append( (curX,curY,curZ) )
	return motion


def merge( directionAstart, directionAend, directionBstart, newStart ):
	'''merges two different locomotes together - for example N and E to give a NE locomote'''
	#determine which ctrl set to use
	length = directionAend-directionAstart
	ctrlSet = names.matchNames(['body_ctrls'],cmd.ls(type='objectSet'))
	if not ctrlSet:
		raise Exception('control set not found')
	ctrlSet = ctrlSet[0]

	ctrls = cmd.sets(ctrlSet,q=True)


	#deal with the assets for the new animation
	vx = exportManagerCore.ExportManager()
	assetA = vx.exists(start=directionAstart,end=directionAend)[0]
	assetB = vx.exists(start=directionBstart,end=directionBstart+length)[0]
	exportSet = assetA.obj

	assetC = vx.exists(start=newStart,end=newStart+length)
	if not assetC:
		assetC = vx.createAsset(exportSet)
		assetC.setAttr('start', newStart)
		assetC.setAttr('end', newStart+length)
		assetC.setAttr('name', assetA.name + assetB.name)
		assetC.setAttr('type', exportManagerCore.ExportComponent.kANIM)


	#now start building the animations
	animationA = Animation(ctrls,directionAstart,directionAend)
	animationB = Animation(ctrls,directionBstart,directionBstart+length)
	animationB.offset(-directionBstart+directionAstart)
	animationC = animationA+animationB
	animationC.offset(newStart)

	#grab the list of ctrls we need to actually transform
	toFind = ['upperBodyControl','legControl_L','legControl_R']
	xformCtrls = [name for name in names.matchNames(toFind,ctrls,parity=True,threshold=0.8) if name != '']

	for ctrl in xformCtrls:
		motionA = motionList(ctrl,directionAstart,directionAend)
		motionB = motionList(ctrl,directionBstart,directionBstart+length)

		#make the time zero based
		times = [int(time)-newStart for time in animationC[ctrl].get_times(channels=['translateX','translateZ'])]
		times.sort()
		print times,len(motionA),len(motionB)
		for time in times:
			print motionA[time],motionB[time]
			newPos = vectors.Vector(motionA[time]) + vectors.Vector(motionB[time])
			newPos *= 0.70710678118654757 #= math.cos(45degrees)
			tx = animationC[ctrl].translateX[time]
			tz = animationC[ctrl].translateZ[time]
			if tx: tx.keys[0] = newPos.x
			if tz: tz.keys[0] = newPos.z

	animationC.applyToObjs()


#end