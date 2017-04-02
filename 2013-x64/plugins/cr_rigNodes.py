'''
--------------------------------------------------------------------------
cr_rigNodes.py- MAYA PYTHON Plug-in
--------------------------------------------------------------------------
Copyright (c) 2013 Wasim Khan creaturerigs.com 

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


Add this file to your plug-in path and load it in Maya from the Plug-in Manager 
(Window -> Settings/Preferences -> Plug-in Manager).

AUTHORS:
    Wasim Khan - wasim.cg@gmail.com , wasim@creaturerigs.com .

VERSIONS:
    0.1 - Jun 09, 2011  - Initial Revision.
    1.0 - Oct 14, 2011  - mid offset functionality added.
                        - mid lock blend functionality.
    1.1 - May 22, 2012  - soft stretch functionality added.
                        - translate /scale switch mode added. 
    1.2 - Oct 10, 2013  - parent matrix input for distance calculation also helps in non-uniform scale.
    1.3 - Oct 20, 2013  - cr_rubberBand locator added.
                        - "translate/scale" text display option added.
'''
##------------------------------------------------------------------------
# global import
##------------------------------------------------------------------------
import sys,math
import maya.OpenMaya as om
import maya.OpenMayaUI as omUI
import maya.OpenMayaMPx as omMPx
import maya.OpenMayaRender as omRender
from pymel import core
from cr_rigNodesLib import *
##------------------------------------------------------------------------
# initializePlugin
##------------------------------------------------------------------------
def initializePlugin(obj):
    if not initializeCRPlugin(obj):
        raise RuntimeError('Failed to load plug-in')

def uninitializePlugin(obj):
    uninitializeCRPlugin(obj)