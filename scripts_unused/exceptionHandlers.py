import os
import sys
import cgitb
import traceback
from filesystem import findMostRecentDefitionOf


def printMsg( *args ):
	for a in args: print a,


def SHOW_IN_UI():
	from wx import MessageBox, ICON_ERROR
	MessageBox( 'Sorry, it seems an un-expected problem occurred.\nYour error has been reported.  Good Luck!', 'An Unhandled Exception Occurred', ICON_ERROR )


DEFAULT_AUTHOR = 'mel@macaronikazoo.com'

def exceptionHandler( *args ):
	'''
	This is a generic exception handler that can replace the default python exception handler if
	needed (ie: sys.excepthook=exceptionHandler).  It will mail
	'''
	try:
		eType, e, tb = args
	except TypeError:
		eType, e, tb = sys.exc_info()

	printMsg( '### ERROR - Python Unhandled Exception' )
	printMsg( '### ', eType.__name__, e )

	#try to mail a callstack
	try:
		import smtplib
		message = 'Subject: [ERROR] assetEditor\n\n%s' % cgitb.text( args )

		author = findMostRecentDefitionOf( '__author__' ) or DEFAULT_AUTHOR
		svr = smtplib.SMTP( 'exchange2' )
		svr.sendmail(os.environ[ 'USERNAME' ], [author, os.environ[ 'USERNAME' ]], message)
	except Exception, x:
		printMsg( 'ERROR: failed to mail exception dump', x )

	#try to post an error dial
	try:
		SHOW_IN_UI()
	except: pass


def d_handleExceptions(f):
	'''
	if you can't/don't want to setup a generic exception handler, you can decorate a function with
	this to have exceptions handled
	exception hanlding decorator.  basically this decorator will catch any exceptions thrown by the
	decorated function, and spew a useful callstack to the event log - as well as throwing up a dial
	to alert of the issue...
	'''
	def newFunc( *a, **kw ):
		try: f( *a, **kw )
		except:
			exc_info = sys.exc_info()
			exceptionHandler( *exc_info )

	newFunc.__name__ = f.__name__
	newFunc.__doc__ = f.__doc__

	return newFunc


#end
