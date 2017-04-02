import maya.cmds as cmd
import utils
import weakref


class BaseMelWidget(str):
	'''
	This is a wrapper class for a mel widget to make it behave a little more like an object.  It
	inherits from str because thats essentially what a mel widget is - a name coupled with a mel
	command.  To interact with the widget the mel command is called with the UI name as the first arg.

	As a shortcut objects of this type are callable - the args taken depend on the specific command,
	and can be found in the mel docs.

	example:
	class AButtonClass(BaseMelWidget):
		WIDGET_CMD = cmd.button

	aButton = AButtonClass( parentName, label='hello' )
	aButton( edit=True, label='new label!' )
	'''

	#this should be set to the mel widget command used by this widget wrapped - ie cmd.button, or cmd.formLayout
	WIDGET_CMD = None

	#track instances so we can send them update messages -
	_INSTANCE_LIST = []

	def __new__( cls, parent, *a, **kw ):
		cmd.setParent( parent )

		new = str.__new__( cls, cls.WIDGET_CMD( *a, **kw ) )
		cls._INSTANCE_LIST.append( new )

		return new
	def __init__( self, parent, *a, **kw ):
		#make sure kw args passed to init are executed as edit commands (which should have been passed
		#to the cmd on creation, but we can't do that because we're inheriting from str, and we don't
		#want to force all subclasses to implement a __new__ method...
		self( edit=True, **kw )

		self.parent = parent
	def __call__( self, *a, **kw ):
		return self.WIDGET_CMD( self, *a, **kw )
	@classmethod
	def FromStr( cls, theStr ):
		'''
		given a ui name, this will cast the string as a widget instance
		'''
		return str.__new__( cls, theStr )
	@classmethod
	def IterInstances( cls ):
		existingInstList = []
		for inst in cls._INSTANCE_LIST:
			if cls.WIDGET_CMD( inst, q=True, exists=True ):
				existingInstList.append( inst )
				yield inst

		cls._INSTANCE_LIST = existingInstList


class MelForm(BaseMelWidget): WIDGET_CMD = cmd.formLayout
class MelColumn(BaseMelWidget): WIDGET_CMD = cmd.columnLayout


class BaseMelWindow(str):
	'''
	This is a wrapper class for a mel window to make it behave a little more like an object.  It
	inherits from str because thats essentially what a mel widget is.

	Objects of this class are callable.  Calling an object is basically the same as passing the given
	args to the cmd.window maya command:

	aWindow = BaseMelWindow()
	aWindow( q=True, exists=True )

	is the same as doing:
	aWindow = cmd.window()
	cmd.window( aWindow, q=True, exists=True )
	'''
	WINDOW_NAME = 'unnamed_window'
	WINDOW_TITLE = 'Unnamed Tool'

	DEFAULT_SIZE = None
	DEFAULT_MENU = 'File'

	FORCE_DEFAULT_SIZE = False

	def __new__( cls, **kw ):
		kw.setdefault( 'title', cls.WINDOW_TITLE )
		kw.setdefault( 'widthHeight', cls.DEFAULT_SIZE )
		kw.setdefault( 'menuBar', True )

		if cmd.window( cls.WINDOW_NAME, ex=True ):
			cmd.deleteUI( cls.WINDOW_NAME )

		new = str.__new__( cls, cmd.window( cls.WINDOW_NAME, **kw ) )
		cmd.menu( l=cls.DEFAULT_MENU )

		return new
	def __call__( self, *a, **kw ):
		return cmd.window( self, *a, **kw )
	def setTitle( self, newTitle ):
		cmd.window( self.WINDOW_NAME, e=True, title=newTitle )
	def getMenu( self, menuName, createIfNotFound=True ):
		'''
		returns the UI name for the menu with the given name
		'''
		menus = self( q=True, menuArray=True )
		if menus is None:
			return

		for m in menus:
			if cmd.menu( m, q=True, label=True ) == menuName:
				return m

		if createIfNotFound:
			return cmd.menu( l=menuName )
	def show( self, state=True ):
		if state:
			cmd.showWindow( self )
		else:
			self( e=True, visible=False )

		if self.FORCE_DEFAULT_SIZE:
			self( e=True, widthHeight=self.DEFAULT_SIZE )


#end