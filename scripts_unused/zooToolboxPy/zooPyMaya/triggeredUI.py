
from triggered import *

import spaceSwitching


def removeDupes( iterable ):
	unique = set()
	newIterable = iterable.__class__()
	for item in iterable:
		if item not in unique:
			newIterable.append( item )

		unique.add( item )

	return newIterable


def buildMenuItems( parent, obj ):
	'''
	build the menuItems in the dagProcMenu - it is possible to set a "kill menu" attribute
	on an object now that will stop the dagMenu building after the objMenu items have been
	added
	'''

	defaultCmdName = "<empty cmd>"
	menusFromConnects = False
	killState = False

	objs = [ obj ] + (listRelatives( obj, pa=True, s=True ) or [])

	#the showMenusFromConnects attribute determines whether the object in question should show right click menus from any items connected to this one via triggered connects
	if objExists( '%s.showMenusFromConnects' % obj ):
		menusFromConnects = getAttr( '%s.showMenusFromConnects' % obj )

	if menusFromConnects:
		connects = Trigger( obj ).connects()
		for connectObj, connectIdx in connects:
			objs.append( connectObj )

	objs = removeDupes( objs )

	#now get a list of objs that have menus - if there are more than one, build section labels, otherwise skip labels
	objsWithMenus = []
	for obj in objs:
		obj = Trigger( obj )
		if obj.menus():
			objsWithMenus.append( obj )

	doLabels = len( objsWithMenus ) > 1

	setParent( parent, m=True )
	for obj in objsWithMenus:

		#if ANY of the objs have the kill state set, turn it on
		if getKillState( obj ):
			killState = True

		tgts, names = spaceSwitching.getSpaceTargetsNames( obj )
		names = [ 'parent to %s' % name for name in names ]
		if objExists( '%s.parent' % obj ):
			curIdx = getAttr( '%s.parent' % obj )
		else: curIdx = None

		if doLabels:
			menuItem( l='---%s Menus---' % str( obj ).split( '|' )[-1].split( ':' )[-1], en=False )

		for idx, cmdName, cmdStr in obj.menus( True ):

			#we need to construct the menu item using mel - because the tool was originally mel and all existing obj menu commands are written in mel
			#so you have to construct the menu item in mel otherwise its assumed the command is python...
			menuCmdToks = [ 'menuItem -l "%s"' % (cmdName or defaultCmdName) ]

			#so if the menu name starts with "parent to " then it assumed to be a menu item built by zooSpaceSwitching
			if cmdStr.startswith( "^parent to " ):
				if curIdx is not None:
					if idx == curIdx:
						menuCmdToks( '-cb 1' )

			if cmdStr:
				menuCmdToks.append( '-c "%s"' % encodeString(cmdStr) )

			mel.eval( ' '.join( menuCmdToks ) )

	#should we die after menu build?
	if not killState:
		menuItem( d=True )
		menuItem( d=True )

	return killState


#end
