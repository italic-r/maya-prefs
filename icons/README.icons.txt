The files in this directory are maya icon files in .xpm format.

Place them in the icon directory of the VERSION of Maya that you are running...
(ie. C:\Documents and Settings\MyLogin\My Documents\maya\6.0\prefs\icons\ )

The script "ManControls.mel" makes specific reference to this path, so if you
put the icons in another directory, you'll have to change the $iconPath in that
script to match. We've created a separate path for the icons so you can keep
them in a safe place, or alter the image without changing everyone elses
icons. In the event that the installed version of Maya gets trashed, your icons
will be safe.
