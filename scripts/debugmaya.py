#
#  Copyright 2012 Autodesk, Inc.  All rights reserved.
#
#  Use of this software is subject to the terms of the Autodesk license
#  agreement provided at the time of installation or download, or which
#  otherwise accompanies this software in either electronic or hard copy form.
#

__copyright__ = "Copyright (c) 2012 Autodesk, Inc."
__version__ = "1.4"
__date__ = "Date: 2012/04/30"
__author__ = "Cyrille Fauvel <cyrille.fauvel@autodesk.com>"
__credits__ = ["Cyrille Fauvel"]
__status__ = "Production"


import sys
import imp
import __builtin__
sys.path.append("/home/italic/playground/eclipse/.p2/pool/plugins/org.python.pydev_5.1.2.201606231256/pysrc")
import pydevd
import zipimport


def startDebug():
    global gMayaImportController
    pydevd.settrace()
    gMayaImportController = MayaImportController()


def debugModule(m1):
    f, filename, description = imp.find_module(m1)
    package = imp.load_module(m1, f, filename, description)


def mayaPythonZip(m1):
    importer = zipimport.zipimporter('python26.zip')
    for m1 in ['zipimport_get_code', 'zipimport_get_source']:
        source = importer.get_source(m1)
    return source


def getCurrentExecuterControl():
    # Returns the current executer control.
    sCommandExecuterTabs = maya.mel.eval('$t = $gCommandExecuterTabs')
    # get tab array
    aCommandExecuterTabs = maya.cmds.tabLayout(sCommandExecuterTabs, query=True, childArray=True)
    # get selected tab index
    selTabIdx = maya.cmds.tabLayout(sCommandExecuterTabs, query=True, selectTabIndex=True) - 1
    # get the tab at the index
    curFormLayout = aCommandExecuterTabs[selTabIdx]
    # get the formLayout children in this tab (according to how we built it)
    tabChldrn = maya.cmds.formLayout(curFormLayout, query=True, childArray=True)
    # get the formLayout's first child which should be the cmdScrollFieldExecuter
    curExecuter = tabChldrn[0]
    return curExecuter


def getCurrentExecuterCode():
    curExecuter = getCurrentExecuterControl()
    # int $len =`cmdScrollFieldExecuter -q -textLength $curExecuter`;
    # string $text1 =`cmdScrollFieldExecuter -q -selectedText $curExecuter`;
    # string $text2 =`cmdScrollFieldExecuter -q -text $curExecuter`;
    text = maya.cmds.cmdScrollFieldExecuter(curExecuter, query=True, text=True)
    return text


class MayaImportController(object):
    singleton = None

    def __new__(cls, *args, **kwargs):
        if not cls.singleton:
            cls.singleton = super(MayaImportController, cls).__new__(cls, *args, **kwargs)
            # Creates an instance and installs as the global importer
            cls.singleton.previousModules = sys.modules.copy()
            cls.singleton .__import__ = __builtin__.__import__
            __builtin__.__import__ = cls.singleton ._import_
            cls.singleton.newModules = {}
        return cls.singleton

    def __init__(self):
        pass

    def _import_(self, name, globals=None, locals=None, fromlist=[], level=-1):
        if self.newModules.has_key(name):
            if not self.previousModules.has_key(name):
                # Force reload when name next imported
                del(sys.modules[name])
        result = apply(self.__import__, (name, globals, locals, fromlist))
        self.newModules[name] = 1
        return result

    def uninstall(self):
        for name in self.newModules.keys():
            if not self.previousModules.has_key(name):
                # Force reload when name next imported
                del(sys.modules[name])
        __builtin__.__import__ = self.__import__
