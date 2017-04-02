"""
MIXAMO Maya Auto Control Rig      
www.mixamo.com/c/maya-auto-control-rig   
Copyright Mixamo www.mixamo.com 2012 Created by Dan Babcock

This script automatically creates a no-bake-necessary control rig for editing MIXAMO motions.

Notes:
    Autodesk Maya 2009 or higher is required.

To Use:
    Run the script.

Noted Features:
    FK/IK legs and arms that follow animation data with no baking
    Keyable AnimDataMult attributes that exaggerate or ignore animation data
    The ability to bake animation to controls at any point in time
    The ability to clear controls at any point in time, preserving animation
    IK legs and arms can follow body motion
    Hands and Feet custom attributes
    Export baked FK skeleton
"""
Mixamo_AutoControlRig_Version = "Beta 1_02c"

"""
Changelog:


Changes in Beta 1_03:
    Temporary: Added Bounding Box Override to assist with characters that have unusual proportions/capes/tails/etc  


Changes in Beta 1_02:
    Now works on skeletons with world-oriented joints! 
             (must still be Mixamo-style, however, and is still not compatible with some rigs with different joint styles(adam, etc))
        Added several special considerations for unknowns
        -added rotation order check to proportion check
        -deletes any locators in the scene while keeping the NULLs
        -removes any transform limits on joints
        -controls and Nulls now use joints' rotation orders
        -added several aliases for joint names
    All finger joints are now optional
    Mesh now gets locked on rig creation
    Improved Hula/Non-Hula contingencies:
        -Added check for hula joint animation coming in to a rig with no hula joint
        -Animation now copies correctly from root joint to root joint with hula option
    Fixed renaming of Orig Animation Mesh
    Removed Export Joints from the Bind Joint Layer
    Imported rigs will now export meshes correctly
    Added special case for deletion of export skeleton/mesh for Maya 2010
    

Changes in Beta 1_01:
    Improved compatibility with user-created motions
        -Imported animations with no keys on some joints will no longer cause "copy animation to rig" to fail
        (for example, MVN motions come in with no finger data)
    Added the ability to export a baked FK skeleton (optionally with mesh) for game developers
    Added Proportion Check to make sure animations are being applied to correct skeleton
    Pelvis Control is now optional (default off) with a warning that it changes the hierarchy
        -"Rig Character" now works with a skeleton with a "Root" joint already present 
        (in this case, Pelvis control is created regardless of the checkbox)
    Script now automatically loads the fbx plugin on execution if it is not loaded
        (Users will still have to load it manually if they import the downloaded character before running the script)
    Names for original animation now have "Original_Animation_" prefix
    Names for mesh now have "Mesh_" prefix
    Functions no longer fail when deformers are added on mesh
    Meshes bound to hierarchy but not Hips joint now properly get integrated into Original_Anim_GRP
    Script now handles problems with mesh hierarchy and namespaces better
"""

    
import maya.cmds as mayac
import maya.mel as mel
import maya.OpenMaya as OpenMaya
import math
import sys
import re
import cPickle
mel.eval("source channelBoxCommand.mel;")
mel.eval("cycleCheck -e off")

FBXpluginLoaded = mayac.pluginInfo("fbxmaya", query = True, loaded = True)
if not FBXpluginLoaded:
    mayac.loadPlugin( "fbxmaya")

ERRORCHECK = 0
JOINT_NAMESPACE = 0
proportionCheckTolerance = .01
DJB_Character_ProportionOverrideCube = ""




#assorted functions
def goToWebpage(page):
    if page == "mixamo":
        mayac.showHelp( 'http://www.mixamo.com', absolute = True)
    elif page == "autoRigger":
        mayac.showHelp( 'http://www.mixamo.com/c/auto-rigger', absolute = True)
    elif page == "motions":
        mayac.showHelp( 'http://www.mixamo.com/motions', absolute = True)
    elif page == "autoControlRig":
        mayac.showHelp( 'http://www.mixamo.com/c/auto-control-rig-for-maya', absolute = True)
    else:
        OpenMaya.MGlobal.displayError("Webpage Call Invalid")



def DJB_LockNHide(node, tx = True, ty = True, tz = True, rx = True, ry = True, rz = True, s = True, v = True):
    if tx:
        mayac.setAttr("%s.tx" % (node), lock = True, keyable = False, channelBox  = False)
    if ty:
        mayac.setAttr("%s.ty" % (node), lock = True, keyable = False, channelBox  = False)
    if tz:
        mayac.setAttr("%s.tz" % (node), lock = True, keyable = False, channelBox  = False)
    if rx:
        mayac.setAttr("%s.rx" % (node), lock = True, keyable = False, channelBox  = False)
    if ry:
        mayac.setAttr("%s.ry" % (node), lock = True, keyable = False, channelBox  = False)
    if rz:
        mayac.setAttr("%s.rz" % (node), lock = True, keyable = False, channelBox  = False)
    if s:
        mayac.setAttr("%s.sx" % (node), lock = True, keyable = False, channelBox  = False)
        mayac.setAttr("%s.sy" % (node), lock = True, keyable = False, channelBox  = False)
        mayac.setAttr("%s.sz" % (node), lock = True, keyable = False, channelBox  = False)
    if v:
        mayac.setAttr("%s.v" % (node), lock = True, keyable = False, channelBox  = False)
        
        
def DJB_Unlock(node, tx = True, ty = True, tz = True, rx = True, ry = True, rz = True, s = True, v = True):
    if tx:
        mayac.setAttr("%s.tx" % (node), lock = False, keyable = True)
    if ty:
        mayac.setAttr("%s.ty" % (node), lock = False, keyable = True)
    if tz:
        mayac.setAttr("%s.tz" % (node), lock = False, keyable = True)
    if rx:
        mayac.setAttr("%s.rx" % (node), lock = False, keyable = True)
    if ry:
        mayac.setAttr("%s.ry" % (node), lock = False, keyable = True)
    if rz:
        mayac.setAttr("%s.rz" % (node), lock = False, keyable = True)
    if s:
        mayac.setAttr("%s.sx" % (node), lock = False, keyable = True)
        mayac.setAttr("%s.sy" % (node), lock = False, keyable = True)
        mayac.setAttr("%s.sz" % (node), lock = False, keyable = True)
    if v:
        mayac.setAttr("%s.v" % (node), lock = False, keyable = True)
 
 
def DJB_Unlock_Connect_Lock(att1, att2):
    mayac.setAttr(att2, lock = False, keyable = True)
    mayac.connectAttr(att1, att2)
    mayac.setAttr(att2, lock = True, keyable = False) 
    

def DJB_parentShape(master, slaveGRP):
    mayac.parent(slaveGRP, master)
    mayac.makeIdentity(slaveGRP, apply = True, t=1, r=1, s=1, n=0) 
    shapes = mayac.listRelatives(slaveGRP, shapes = True)
    for shape in shapes:
        mayac.parent(shape, master, relative = True, shape = True)
    mayac.delete(slaveGRP)

def DJB_createGroup(transform = None, suffix = None, fullName = None, pivotFrom = "self"):
    Grp = 0
    if suffix:
        Grp = mayac.group(empty = True, name = (transform + suffix))
    elif fullName:
        Grp = mayac.group(empty = True, name = fullName)
    else:
        Grp = mayac.group(empty = True, name = (transform + "GRP"))
    if pivotFrom == "self":
        mayac.delete(mayac.parentConstraint(transform, Grp))
    else:
        mayac.delete(mayac.parentConstraint(pivotFrom, Grp))
    if transform:
        mayac.parent(transform, Grp)
    return Grp

def DJB_movePivotToObject(moveMe, toHere, posOnly = False):
    POS = mayac.xform(toHere, query=True, absolute=True, worldSpace=True ,rp=True)
    mayac.move(POS[0], POS[1], POS[2], (moveMe + ".rotatePivot"), (moveMe + ".scalePivot"), absolute=True, worldSpace=True)
    if not posOnly:
        mayac.parent(moveMe, toHere)
        DJB_cleanGEO(moveMe)
        mayac.parent(moveMe, world=True)
         

def DJB_findBeforeSeparator(object, separatedWith):
    latestSeparator = object.rfind(separatedWith)
    return object[0:latestSeparator+1]
    
def DJB_findAfterSeperator(object, separatedWith):
    latestSeparator = object.rfind(separatedWith)
    return object[latestSeparator+1:len(object)]
    
    
def DJB_addNameSpace(namespace, string):
    if string == None:
        return None
    else:
        return namespace + string
    
def DJB_cleanGEO(mesh):
    mayac.setAttr("%s.tx" % (mesh), lock = False, keyable = True)
    mayac.setAttr("%s.ty" % (mesh), lock = False, keyable = True)
    mayac.setAttr("%s.tz" % (mesh), lock = False, keyable = True)
    mayac.setAttr("%s.rx" % (mesh), lock = False, keyable = True)
    mayac.setAttr("%s.ry" % (mesh), lock = False, keyable = True)
    mayac.setAttr("%s.rz" % (mesh), lock = False, keyable = True)
    mayac.setAttr("%s.sx" % (mesh), lock = False, keyable = True)
    mayac.setAttr("%s.sy" % (mesh), lock = False, keyable = True)
    mayac.setAttr("%s.sz" % (mesh), lock = False, keyable = True)
    mayac.setAttr("%s.visibility" % (mesh), lock = False, keyable = True)
    mayac.makeIdentity(mesh, apply = True, t=1, r=1, s=1, n=0)
    mayac.delete(mesh, constructionHistory = True)
    return mesh    


def DJB_ZeroOut(transform):
    if transform:
        if not mayac.getAttr("%s.tx" % (transform),lock=True):
            mel.eval('CBdeleteConnection "%s.tx";'%(transform))
            mayac.setAttr("%s.tx" % (transform), 0)
        if not mayac.getAttr("%s.ty" % (transform),lock=True):
            mel.eval('CBdeleteConnection "%s.ty";'%(transform))
            mayac.setAttr("%s.ty" % (transform), 0)
        if not mayac.getAttr("%s.tz" % (transform),lock=True):
            mel.eval('CBdeleteConnection "%s.tz";'%(transform))
            mayac.setAttr("%s.tz" % (transform), 0)
        if not mayac.getAttr("%s.rx" % (transform),lock=True):
            mel.eval('CBdeleteConnection "%s.rx";'%(transform))
            mayac.setAttr("%s.rx" % (transform), 0)
        if not mayac.getAttr("%s.ry" % (transform),lock=True):
            mel.eval('CBdeleteConnection "%s.ry";'%(transform))
            mayac.setAttr("%s.ry" % (transform), 0)
        if not mayac.getAttr("%s.rz" % (transform),lock=True):
            mel.eval('CBdeleteConnection "%s.rz";'%(transform))
            mayac.setAttr("%s.rz" % (transform), 0)


def DJB_ZeroOutAtt(att, value = 0):
    if mayac.objExists("%s" % (att)):
        mel.eval('CBdeleteConnection %s;'%(att))
        mayac.setAttr("%s" % (att), value)


def DJB_ChangeDisplayColor(object, color = None):
    colorNum = 0
    if color == "red1":
        colorNum = 12
    elif color == "red2":
        colorNum = 10
    elif color == "red3":
        colorNum = 24
    elif color == "blue1":
        colorNum = 15
    elif color == "blue2":
        colorNum = 29
    elif color == "blue3":
        colorNum = 28
    elif color == "yellow":
        colorNum = 17
    elif color == "white":
        colorNum = 16
    else:    #default is black
        colorNum = 1
    if object:
        mayac.setAttr('%s.overrideEnabled' % (object), 1)
        mayac.setAttr('%s.overrideColor' % (object), colorNum)


def DJB_CheckAngle(object1, object2, object3, axis = "z", multiplier = 1): #axis can be "x", "y", or "z"
    obj1POS = mayac.xform(object1, query = True, worldSpace = True, absolute = True, translation = True)
    obj3POS = mayac.xform(object3, query = True, worldSpace = True, absolute = True, translation = True)
    rotOrig = mayac.getAttr("%s.rotate%s" % (object2, axis.upper()))
    distOrig = math.sqrt((obj3POS[0]-obj1POS[0])*(obj3POS[0]-obj1POS[0]) + (obj3POS[1]-obj1POS[1])*(obj3POS[1]-obj1POS[1]) + (obj3POS[2]-obj1POS[2])*(obj3POS[2]-obj1POS[2]))
    mayac.setAttr("%s.rotate%s" % (object2, axis.upper()), rotOrig + .5*multiplier)
    obj1POS = mayac.xform(object1, query = True, worldSpace = True, absolute = True, translation = True)
    obj3POS = mayac.xform(object3, query = True, worldSpace = True, absolute = True, translation = True)
    distBack = math.sqrt((obj3POS[0]-obj1POS[0])*(obj3POS[0]-obj1POS[0]) + (obj3POS[1]-obj1POS[1])*(obj3POS[1]-obj1POS[1]) + (obj3POS[2]-obj1POS[2])*(obj3POS[2]-obj1POS[2]))
    mayac.setAttr("%s.rotate%s" % (object2, axis.upper()), rotOrig)
    if distOrig < distBack:
        return True
    else:
        return False


def pyToAttr(objAttr, data):
    obj, attr = objAttr.split('.')
    if not mayac.objExists(objAttr):
        mayac.addAttr(obj, longName=attr, dataType='string')
    if mayac.getAttr(objAttr, type=True) != 'string':
        raise Exception("Object '%s' already has an attribute called '%s', but it isn't type 'string'"%(obj,attr))

    stringData = cPickle.dumps(data)
    mayac.setAttr(objAttr, stringData, type='string')


def attrToPy(objAttr):
    stringAttrData = str(mayac.getAttr(objAttr))
    loadedData = cPickle.loads(stringAttrData)
    return loadedData


class DJB_CharacterNode():
    def __init__(self, joint_name_, infoNode_ = None, optional_ = 0, hasIK_ = 0, parent = None, nameSpace_ = "", actAsRoot_ = 0, alias_ = None):
        self.characterNameSpace = nameSpace_
        self.infoNode = None
        if infoNode_:
            self.infoNode = self.characterNameSpace + infoNode_
        self.nodeName = joint_name_
        self.children = []
        self.AnimData_Joint = None
        self.Bind_Joint = None
        self.Export_Joint = None
        self.origPosX = None
        self.origPosY = None
        self.origPosZ = None
        self.origRotX = None
        self.origRotY = None
        self.origRotZ = None
        self.FK_Joint =  None
        self.IK_Joint = None
        self.IK_Dummy_Joint = None
        self.templateGeo = None
        self.FK_CTRL = None
        self.FK_CTRL_COLOR = None
        self.FK_CTRL_inRig_CONST_GRP = None
        self.FK_CTRL_animData_CONST_GRP = None
        self.FK_CTRL_animData_MultNode = None
        self.FK_CTRL_animData_MultNode_Trans = None
        self.FK_CTRL_POS_GRP = None
        self.IK_CTRL = None
        self.IK_CTRL_COLOR = None
        self.IK_CTRL_inRig_CONST_GRP = None
        self.IK_CTRL_animData_CONST_GRP = None
        self.IK_CTRL_animData_MultNode = None
        self.IK_CTRL_POS_GRP = None
        self.IK_CTRL_ReorientGRP = None
        
        self.IK_CTRL_parent_animData_CONST_GRP = None
        self.IK_CTRL_parent_animData_MultNode = None
        self.IK_CTRL_parent_POS_GRP = None
        
        self.IK_CTRL_grandparent_inRig_CONST_GRP = None
        self.IK_CTRL_grandparent_animData_CONST_GRP = None
        self.IK_CTRL_grandparent_animData_MultNode = None
        self.IK_CTRL_grandparent_POS_GRP = None
        
        self.Inherit_Rotation_GRP = None
        self.Inherit_Rotation_Constraint = None
        self.Inherit_Rotation_Reverse = None
        self.Constraint = None
        self.FK_Constraint = None
        self.IK_Constraint = None
        self.IK_Handle = None
        self.IK_EndEffector = None
        self.PV_Constraint = None
        self.Guide_Curve = None
        self.Guide_Curve_Cluster1 = None
        self.Guide_Curve_Cluster2 = None
        self.Options_CTRL = None
        self.Options_CTRL_COLOR = None
        
        self.IK_CTRL_parent_Global_POS_GRP = None
        self.IK_CTRL_grandparent_Global_POS_GRP = None
        self.grandparent_Global_Constraint = None
        self.grandparent_Global_Constraint_Reverse = None
        self.parent_Global_Constraint = None
        self.parent_Global_Constraint_Reverse = None
        
        self.follow_extremity_Constraint = None
        self.follow_extremity_Constraint_Reverse = None
        
        self.locator = None
        self.locatorConstraint = None
        self.locator1 = None
        self.locatorConstraint1 = None
        self.locator2 = None
        self.locatorConstraint2 = None
        self.locator3 = None
        self.locatorConstraint3 = None
        self.footRotateLOC = None
        self.Follow_Foot_GRP = None
        self.Follow_Knee_GRP = None
        self.Follow_Knee_Constraint = None
        self.Follow_Foot_Constraint = None
        self.IK_BakingLOC = None
        self.actAsRoot = actAsRoot_
        self.rotOrder = None
        self.alias = alias_
        
        
        
        
        if not self.infoNode:
            if not self.Bind_Joint:
                self.Bind_Joint = self.validateExistance(str(JOINT_NAMESPACE) + joint_name_)
            if not self.Bind_Joint and self.alias:
                for alias in self.alias:
                    self.Bind_Joint = self.validateExistance(str(JOINT_NAMESPACE) + alias)
                    if self.Bind_Joint:
                        break
            if not self.Bind_Joint and not optional_:
                OpenMaya.MGlobal.displayError("ERROR: %s cannot be found and is necessary for the autorigger to complete process" % (str(JOINT_NAMESPACE) + joint_name_))
                sys.exit()
            
            if self.Bind_Joint:
                self.Bind_Joint = mayac.rename(self.Bind_Joint, 'Bind_' + joint_name_)
                mel.eval('CBdeleteConnection "%s.tx";'%(self.Bind_Joint))
                mel.eval('CBdeleteConnection "%s.ty";'%(self.Bind_Joint))
                mel.eval('CBdeleteConnection "%s.tz";'%(self.Bind_Joint))
                mel.eval('CBdeleteConnection "%s.rx";'%(self.Bind_Joint))
                mel.eval('CBdeleteConnection "%s.ry";'%(self.Bind_Joint))
                mel.eval('CBdeleteConnection "%s.rz";'%(self.Bind_Joint))
                self.rotOrder = mayac.getAttr("%s.rotateOrder" %(self.Bind_Joint))
            if not self.Bind_Joint:
                return None
            self.parent = parent
            if self.parent:
                self.parent.children.append(self)
       
        #recreate from an infoNode
        else:              
            self.parent = parent
            if self.parent:
                self.parent.children.append(self)
            try:
                self.Bind_Joint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Bind_Joint" % (self.infoNode)))
            except:
                version = mel.eval("float $ver = `getApplicationVersionAsFloat`;")
                if version == 2010.0:
                    OpenMaya.MGlobal.displayError("The Auto-Control Setup requires namespaces in Maya 2010.")
                return None
            self.AnimData_Joint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.AnimData_Joint" % (self.infoNode)))
            self.rotOrder = attrToPy("%s.rotOrder" % (self.infoNode))
            self.origPosX = attrToPy("%s.origPosX" % (self.infoNode))
            self.origPosY = attrToPy("%s.origPosY" % (self.infoNode))
            self.origPosZ = attrToPy("%s.origPosZ" % (self.infoNode))
            self.origRotX = attrToPy("%s.origRotX" % (self.infoNode))
            self.origRotY = attrToPy("%s.origRotY" % (self.infoNode))
            self.origRotZ = attrToPy("%s.origRotZ" % (self.infoNode))
            self.FK_Joint =  DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.FK_Joint" % (self.infoNode)))
            self.IK_Joint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_Joint" % (self.infoNode)))
            self.IK_Dummy_Joint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_Dummy_Joint" % (self.infoNode)))
            self.Export_Joint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Export_Joint" % (self.infoNode)))
            self.templateGeo = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.templateGeo" % (self.infoNode)))
            self.FK_CTRL = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.FK_CTRL" % (self.infoNode)))
            self.FK_CTRL_COLOR = attrToPy("%s.FK_CTRL_COLOR" % (self.infoNode))
            self.FK_CTRL_inRig_CONST_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.FK_CTRL_inRig_CONST_GRP" % (self.infoNode)))
            self.FK_CTRL_animData_CONST_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.FK_CTRL_animData_CONST_GRP" % (self.infoNode)))
            self.FK_CTRL_animData_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.FK_CTRL_animData_MultNode" % (self.infoNode)))
            self.FK_CTRL_animData_MultNode_Trans = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.FK_CTRL_animData_MultNode_Trans" % (self.infoNode)))
            self.FK_CTRL_POS_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.FK_CTRL_POS_GRP" % (self.infoNode)))
            self.IK_CTRL = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL" % (self.infoNode)))
            self.IK_CTRL_COLOR = attrToPy("%s.IK_CTRL_COLOR" % (self.infoNode))
            self.IK_CTRL_inRig_CONST_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_inRig_CONST_GRP" % (self.infoNode)))
            self.IK_CTRL_animData_CONST_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_animData_CONST_GRP" % (self.infoNode)))
            self.IK_CTRL_animData_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_animData_MultNode" % (self.infoNode)))
            self.IK_CTRL_POS_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_POS_GRP" % (self.infoNode)))
            self.IK_CTRL_ReorientGRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_ReorientGRP" % (self.infoNode)))
            
            self.IK_CTRL_parent_animData_CONST_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_parent_animData_CONST_GRP" % (self.infoNode)))
            self.IK_CTRL_parent_animData_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_parent_animData_MultNode" % (self.infoNode)))
            self.IK_CTRL_parent_POS_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_parent_POS_GRP" % (self.infoNode)))
            
            self.IK_CTRL_grandparent_inRig_CONST_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_parent_POS_GRP" % (self.infoNode)))
            self.IK_CTRL_grandparent_animData_CONST_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_grandparent_animData_CONST_GRP" % (self.infoNode)))
            self.IK_CTRL_grandparent_animData_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_grandparent_animData_MultNode" % (self.infoNode)))
            self.IK_CTRL_grandparent_POS_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_grandparent_POS_GRP" % (self.infoNode)))
            
            self.Inherit_Rotation_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Inherit_Rotation_GRP" % (self.infoNode)))
            self.Inherit_Rotation_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Inherit_Rotation_Constraint" % (self.infoNode)))
            self.Inherit_Rotation_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Inherit_Rotation_Reverse" % (self.infoNode)))
            self.Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Constraint" % (self.infoNode)))
            self.FK_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.FK_Constraint" % (self.infoNode)))
            self.IK_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_Constraint" % (self.infoNode)))
            self.IK_Handle = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_Handle" % (self.infoNode)))
            self.IK_EndEffector = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_EndEffector" % (self.infoNode)))
            self.PV_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.PV_Constraint" % (self.infoNode)))
            self.Guide_Curve = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Guide_Curve" % (self.infoNode)))
            self.Guide_Curve_Cluster1 = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Guide_Curve_Cluster1" % (self.infoNode)))
            self.Guide_Curve_Cluster2 = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Guide_Curve_Cluster2" % (self.infoNode)))
            self.Options_CTRL = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Options_CTRL" % (self.infoNode)))
            self.Options_CTRL_COLOR = attrToPy("%s.Options_CTRL_COLOR" % (self.infoNode))
            
            self.IK_CTRL_parent_Global_POS_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_parent_Global_POS_GRP" % (self.infoNode)))
            self.IK_CTRL_grandparent_Global_POS_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_CTRL_grandparent_Global_POS_GRP" % (self.infoNode)))
            self.grandparent_Global_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.grandparent_Global_Constraint" % (self.infoNode)))
            self.grandparent_Global_Constraint_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.grandparent_Global_Constraint_Reverse" % (self.infoNode)))
            self.parent_Global_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.parent_Global_Constraint" % (self.infoNode)))
            self.parent_Global_Constraint_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.parent_Global_Constraint_Reverse" % (self.infoNode)))
            
            self.follow_extremity_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.follow_extremity_Constraint" % (self.infoNode)))
            self.follow_extremity_Constraint_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.follow_extremity_Constraint_Reverse" % (self.infoNode)))
            
            self.locator = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.locator" % (self.infoNode)))
            self.locatorConstraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.locator" % (self.infoNode)))
            self.locator1 = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.locator1" % (self.infoNode)))
            self.locatorConstraint1 = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.locatorConstraint1" % (self.infoNode)))
            self.footRotateLOC = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.footRotateLOC" % (self.infoNode)))
            self.Follow_Foot_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Follow_Foot_GRP" % (self.infoNode)))
            self.Follow_Knee_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Follow_Knee_GRP" % (self.infoNode)))
            self.Follow_Knee_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Follow_Knee_Constraint" % (self.infoNode)))
            self.Follow_Foot_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Follow_Knee_Constraint" % (self.infoNode)))
            self.IK_BakingLOC = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_BakingLOC" % (self.infoNode)))

        
        
    def writeInfoNode(self):
        self.infoNode = mayac.createNode("transform", name = "MIXAMO_CHARACTER_%s_infoNode" % (self.nodeName))
        
        pyToAttr("%s.Bind_Joint" % (self.infoNode), self.Bind_Joint)
        pyToAttr("%s.AnimData_Joint" % (self.infoNode), self.AnimData_Joint)
        pyToAttr("%s.rotOrder" % (self.infoNode), self.rotOrder)
        pyToAttr("%s.origPosX" % (self.infoNode), self.origPosX)
        pyToAttr("%s.origPosY" % (self.infoNode), self.origPosY)
        pyToAttr("%s.origPosZ" % (self.infoNode), self.origPosZ)
        pyToAttr("%s.origRotX" % (self.infoNode), self.origRotX)
        pyToAttr("%s.origRotY" % (self.infoNode), self.origRotY)
        pyToAttr("%s.origRotZ" % (self.infoNode), self.origRotZ)
        pyToAttr("%s.FK_Joint" % (self.infoNode), self.FK_Joint)
        pyToAttr("%s.IK_Joint" % (self.infoNode), self.IK_Joint)
        pyToAttr("%s.IK_Dummy_Joint" % (self.infoNode), self.IK_Dummy_Joint)
        pyToAttr("%s.Export_Joint" % (self.infoNode), self.Export_Joint)
        pyToAttr("%s.templateGeo" % (self.infoNode), self.templateGeo)
        pyToAttr("%s.FK_CTRL" % (self.infoNode), self.FK_CTRL)
        pyToAttr("%s.FK_CTRL_COLOR" % (self.infoNode), self.FK_CTRL_COLOR)
        pyToAttr("%s.FK_CTRL_inRig_CONST_GRP" % (self.infoNode), self.FK_CTRL_inRig_CONST_GRP)
        pyToAttr("%s.FK_CTRL_animData_CONST_GRP" % (self.infoNode), self.FK_CTRL_animData_CONST_GRP)
        pyToAttr("%s.FK_CTRL_animData_MultNode" % (self.infoNode), self.FK_CTRL_animData_MultNode)
        pyToAttr("%s.FK_CTRL_animData_MultNode_Trans" % (self.infoNode), self.FK_CTRL_animData_MultNode_Trans)
        pyToAttr("%s.FK_CTRL_POS_GRP" % (self.infoNode), self.FK_CTRL_POS_GRP)
        pyToAttr("%s.IK_CTRL" % (self.infoNode), self.IK_CTRL)
        pyToAttr("%s.IK_CTRL_COLOR" % (self.infoNode), self.IK_CTRL_COLOR)
        pyToAttr("%s.IK_CTRL_inRig_CONST_GRP" % (self.infoNode), self.IK_CTRL_inRig_CONST_GRP)
        pyToAttr("%s.IK_CTRL_animData_CONST_GRP" % (self.infoNode), self.IK_CTRL_animData_CONST_GRP)
        pyToAttr("%s.IK_CTRL_animData_MultNode" % (self.infoNode), self.IK_CTRL_animData_MultNode)
        pyToAttr("%s.IK_CTRL_POS_GRP" % (self.infoNode), self.IK_CTRL_POS_GRP)
        pyToAttr("%s.IK_CTRL_ReorientGRP" % (self.infoNode), self.IK_CTRL_ReorientGRP)
        pyToAttr("%s.IK_CTRL_parent_animData_CONST_GRP" % (self.infoNode), self.IK_CTRL_parent_animData_CONST_GRP)
        pyToAttr("%s.IK_CTRL_parent_animData_MultNode" % (self.infoNode), self.IK_CTRL_parent_animData_MultNode)
        pyToAttr("%s.IK_CTRL_parent_POS_GRP" % (self.infoNode), self.IK_CTRL_parent_POS_GRP)
        pyToAttr("%s.IK_CTRL_grandparent_inRig_CONST_GRP" % (self.infoNode), self.IK_CTRL_grandparent_inRig_CONST_GRP)
        pyToAttr("%s.IK_CTRL_grandparent_animData_CONST_GRP" % (self.infoNode), self.IK_CTRL_grandparent_animData_CONST_GRP)
        pyToAttr("%s.IK_CTRL_grandparent_animData_MultNode" % (self.infoNode), self.IK_CTRL_grandparent_animData_MultNode)
        pyToAttr("%s.IK_CTRL_grandparent_POS_GRP" % (self.infoNode), self.IK_CTRL_grandparent_POS_GRP)
        pyToAttr("%s.Inherit_Rotation_GRP" % (self.infoNode), self.Inherit_Rotation_GRP)
        pyToAttr("%s.Inherit_Rotation_Constraint" % (self.infoNode), self.Inherit_Rotation_Constraint)
        pyToAttr("%s.Inherit_Rotation_Reverse" % (self.infoNode), self.Inherit_Rotation_Reverse)
        pyToAttr("%s.Constraint" % (self.infoNode), self.Constraint)
        pyToAttr("%s.FK_Constraint" % (self.infoNode), self.FK_Constraint)
        pyToAttr("%s.IK_Constraint" % (self.infoNode), self.IK_Constraint)
        pyToAttr("%s.IK_Handle" % (self.infoNode), self.IK_Handle)
        pyToAttr("%s.IK_EndEffector" % (self.infoNode), self.IK_EndEffector)
        pyToAttr("%s.PV_Constraint" % (self.infoNode), self.PV_Constraint)
        pyToAttr("%s.Guide_Curve" % (self.infoNode), self.Guide_Curve)
        pyToAttr("%s.Guide_Curve_Cluster1" % (self.infoNode), self.Guide_Curve_Cluster1)
        pyToAttr("%s.Guide_Curve_Cluster2" % (self.infoNode), self.Guide_Curve_Cluster2)
        pyToAttr("%s.Options_CTRL" % (self.infoNode), self.Options_CTRL)
        pyToAttr("%s.Options_CTRL_COLOR" % (self.infoNode), self.Options_CTRL_COLOR)
        pyToAttr("%s.IK_CTRL_parent_Global_POS_GRP" % (self.infoNode), self.IK_CTRL_parent_Global_POS_GRP)
        pyToAttr("%s.IK_CTRL_grandparent_Global_POS_GRP" % (self.infoNode), self.IK_CTRL_grandparent_Global_POS_GRP)
        pyToAttr("%s.grandparent_Global_Constraint" % (self.infoNode), self.grandparent_Global_Constraint)
        pyToAttr("%s.grandparent_Global_Constraint_Reverse" % (self.infoNode), self.grandparent_Global_Constraint_Reverse)
        pyToAttr("%s.parent_Global_Constraint" % (self.infoNode), self.parent_Global_Constraint)
        pyToAttr("%s.parent_Global_Constraint_Reverse" % (self.infoNode), self.parent_Global_Constraint_Reverse)
        pyToAttr("%s.follow_extremity_Constraint" % (self.infoNode), self.follow_extremity_Constraint)
        pyToAttr("%s.follow_extremity_Constraint_Reverse" % (self.infoNode), self.follow_extremity_Constraint_Reverse)
        pyToAttr("%s.locator" % (self.infoNode), self.locator)
        pyToAttr("%s.locatorConstraint" % (self.infoNode), self.locatorConstraint)
        pyToAttr("%s.locator1" % (self.infoNode), self.locator1)
        pyToAttr("%s.locatorConstraint1" % (self.infoNode), self.locatorConstraint1)
        pyToAttr("%s.footRotateLOC" % (self.infoNode), self.footRotateLOC)
        pyToAttr("%s.Follow_Foot_GRP" % (self.infoNode), self.Follow_Foot_GRP)
        pyToAttr("%s.Follow_Knee_GRP" % (self.infoNode), self.Follow_Knee_GRP)
        pyToAttr("%s.Follow_Knee_Constraint" % (self.infoNode), self.Follow_Knee_Constraint)
        pyToAttr("%s.Follow_Foot_Constraint" % (self.infoNode), self.Follow_Foot_Constraint)
        pyToAttr("%s.IK_BakingLOC" % (self.infoNode), self.IK_BakingLOC)
        
        return self.infoNode
            
     
     
    def fixAllLayerOverrides(self, layer):
        if self.FK_CTRL:
            self.fixLayerOverrides(self.FK_CTRL, self.FK_CTRL_COLOR, layer)
        if self.IK_CTRL:
            self.fixLayerOverrides(self.IK_CTRL, self.IK_CTRL_COLOR, layer)
        if self.Options_CTRL:
            self.fixLayerOverrides(self.Options_CTRL, self.Options_CTRL_COLOR, layer)

        
           
    def fixLayerOverrides(self, control, color, layer, referenceAlways = False):
        if mayac.listConnections( "%s.drawOverride" % (control)):
            mayac.disconnectAttr("%s.drawInfo" % (layer), "%s.drawOverride" % (control))
        mayac.connectAttr("%s.levelOfDetail" % (layer), "%s.overrideLevelOfDetail" % (control), force = True)
        mayac.connectAttr("%s.shading" % (layer), "%s.overrideShading" % (control), force = True)
        mayac.connectAttr("%s.texturing" % (layer), "%s.overrideTexturing" % (control), force = True)
        mayac.connectAttr("%s.playback" % (layer), "%s.overridePlayback" % (control), force = True)
        mayac.connectAttr("%s.visibility" % (layer), "%s.overrideVisibility" % (control), force = True)
        DJB_ChangeDisplayColor(control, color = color)
        if referenceAlways:
            mayac.setAttr("%s.overrideDisplayType" % (control), 2)
        else:
            mayac.connectAttr("%s.displayType" % (layer), "%s.overrideDisplayType" % (control), force = True)
        shapes = mayac.listRelatives(control, children = True, shapes = True)
        if shapes:
            for shape in shapes:
                self.fixLayerOverrides(shape, color, layer, referenceAlways)
    
        
    def validateExistance(self, object):
        if mayac.objExists(object):
            return object
        else:
            return None

    def duplicateJoint(self, type, parent_ = "UseSelf", jointNamespace = None):
        if self.Bind_Joint:
            if type == "AnimData":
                temp = mayac.duplicate(self.Bind_Joint, parentOnly = True, name = "AnimData_" + self.nodeName)
                self.AnimData_Joint = temp[0]
            elif type == "FK":
                temp = mayac.duplicate(self.Bind_Joint, parentOnly = True, name = "FK_" + self.nodeName)
                self.FK_Joint = temp[0]
            elif type == "IK":
                temp = mayac.duplicate(self.Bind_Joint, parentOnly = True, name = "IK_" + self.nodeName)
                self.IK_Joint = temp[0]
            elif type == "IK_Dummy":
                temp = mayac.duplicate(self.Bind_Joint, parentOnly = True, name = "IK_Dummy_" + self.nodeName)
                self.IK_Dummy_Joint = temp[0]
            elif type == "ExportSkeleton":
                if jointNamespace:
                    temp = mayac.duplicate(self.Bind_Joint, parentOnly = True, name = jointNamespace + self.nodeName)
                    self.Export_Joint = temp[0]
                    mayac.parent(self.Export_Joint, world = True)
                else:
                    temp = mayac.duplicate(self.Bind_Joint, parentOnly = True, name = self.nodeName)
                    self.Export_Joint = temp[0]
                    mayac.parent(self.Export_Joint, world = True)
            if parent_ == "UseSelf" and self.parent:
                if type == "AnimData":
                    mayac.parent(self.AnimData_Joint, self.parent.AnimData_Joint)
                if type == "FK":
                    mayac.parent(self.FK_Joint, self.parent.FK_Joint)
                if type == "IK":
                    mayac.parent(self.IK_Joint, self.parent.IK_Joint)
                if type == "IK_Dummy":
                    mayac.parent(self.IK_Dummy_Joint, self.parent.IK_Dummy_Joint)
                if type == "ExportSkeleton":
                    mayac.parent(self.Export_Joint, self.parent.Export_Joint)
                    
                    
    def createGuideCurve(self, group_, optionsCTRL = None):
        pos1 = mayac.xform(self.IK_CTRL, query = True, absolute = True, worldSpace = True, translation = True)
        pos2 = mayac.xform(self.IK_Joint, query = True, absolute = True, worldSpace = True, translation = True)
        self.Guide_Curve = mayac.curve(degree = 1, name = "%s_GuideCurve" % (self.IK_CTRL),
                                      point = [(pos1[0], pos1[1], pos1[2]), (pos2[0], pos2[1], pos2[2])],
                                      knot = [0,1])
        mayac.xform(self.Guide_Curve, centerPivots = True)
        mayac.select("%s.cv[0]" % (self.Guide_Curve), replace = True) ;
        temp = mayac.cluster(name = "%s_Cluster1" % (self.Guide_Curve))
        self.Guide_Curve_Cluster1 = temp[1]
        mayac.select("%s.cv[1]" % (self.Guide_Curve), replace = True) ;
        temp = mayac.cluster(name = "%s_Cluster2" % (self.Guide_Curve))
        self.Guide_Curve_Cluster2 = temp[1]
        mayac.parent(self.Guide_Curve_Cluster1, self.IK_CTRL)
        mayac.parent(self.Guide_Curve_Cluster2, self.IK_Joint)
        mayac.parent(self.Guide_Curve, group_)
        mayac.setAttr("%s.visibility" % (self.Guide_Curve_Cluster1),0)
        mayac.setAttr("%s.visibility" % (self.Guide_Curve_Cluster2),0)
        mayac.setAttr("%s.overrideEnabled" % (self.Guide_Curve), 1)
        mayac.setAttr("%s.overrideDisplayType" % (self.Guide_Curve), 1)
        multDiv = mayac.createNode( 'multiplyDivide', n=self.Guide_Curve + "_Visibility_MultNode")
        mayac.addAttr(self.IK_CTRL, longName='GuideCurve', defaultValue=1.0, min = 0.0, max = 1.0, keyable = True)
        mayac.connectAttr("%s.GuideCurve" %(self.IK_CTRL), "%s.input2X" %(multDiv), force = True)
        if optionsCTRL:
            mayac.connectAttr("%s.FK_IK" %(optionsCTRL), "%s.input1X" %(multDiv), force = True)
        mayac.connectAttr("%s.outputX" %(multDiv), "%s.visibility" %(self.Guide_Curve), force = True)
        DJB_LockNHide(self.Guide_Curve)
        DJB_LockNHide(self.Guide_Curve_Cluster1)
        DJB_LockNHide(self.Guide_Curve_Cluster2)



    def createControl(self, type, rigType = "AutoRig", style = "circle", partialConstraint = 0, scale = (0.1,0.1,0.1), rotate = (0,0,0), offset = (0,0,0), estimateSize = True, color_ = None):
        control = 0 
        if style == "circle":
            if estimateSize:
                control = mayac.circle(constructionHistory = 0)
                control = control[0]
                mayac.rotate(0, 90, 90)
                if "Root" not in self.nodeName and "Spine" not in self.nodeName and "Hips" not in self.nodeName and rigType == "World":
                    mayac.rotate(rotate[0], rotate[1], rotate[2], control, absolute = True) #override for world-oriented rigs
                mayac.scale(scale[0],scale[1],scale[2])
                mayac.move(offset[0], offset[1], offset[2], "%s.cv[0:7]" % (control), relative = True)
                mayac.makeIdentity(control, apply = True, t=1, r=1, s=1, n=0)
            else:
                print "exactSizeNotFunctionalYet"

        elif style == "box":
            if estimateSize:
                control = mayac.curve(degree = 1,
                                      point = [(0.5, 0.5, 0.5),
                                          (0.5, 0.5, -0.5),
                                          (-0.5, 0.5, -0.5),
                                          (-0.5, -0.5, -0.5),
                                          (0.5, -0.5, -0.5),
                                          (0.5, 0.5, -0.5),
                                          (-0.5, 0.5, -0.5),
                                          (-0.5, 0.5, 0.5),
                                          (0.5, 0.5, 0.5),
                                          (0.5, -0.5, 0.5),
                                          (0.5, -0.5, -0.5),
                                          (-0.5, -0.5, -0.5),
                                          (-0.5, -0.5, 0.5),
                                          (0.5, -0.5, 0.5),
                                          (-0.5, -0.5, 0.5),
                                          (-0.5, 0.5, 0.5)],
                                      knot = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])                                                                            
                mayac.move(0, -.2, 0, "%s.cv[0]" % (control), "%s.cv[7:8]" % (control), "%s.cv[15]" % (control), relative = True)
                mayac.scale(1.3, 1.3, 1.3, "%s.cv[3:4]" % (control), "%s.cv[9:12]" % (control), "%s.cv[13:14]" % (control))       
                mayac.scale(scale[0], scale[1], scale[2], control)
                mayac.rotate(rotate[0], rotate[1], rotate[2], control, relative = True)
                mayac.move(offset[0], offset[1], offset[2],  "%s.cv[0:15]" % (control), relative = True)
                mayac.makeIdentity(control, apply = True, t=1, r=1, s=1, n=0)
            else:
                print "exactSizeNotFunctionalYet"
                
                
        elif style == "footBox":
            if estimateSize:
                control = mayac.curve(degree = 1,
                                      point = [(0.5, 0.5, 0.5),
                                          (0.5, 0.5, -0.5),
                                          (-0.5, 0.5, -0.5),
                                          (-0.5, -0.5, -0.5),
                                          (0.5, -0.5, -0.5),
                                          (0.5, 0.5, -0.5),
                                          (-0.5, 0.5, -0.5),
                                          (-0.5, 0.5, 0.5),
                                          (0.5, 0.5, 0.5),
                                          (0.5, -0.5, 0.5),
                                          (0.5, -0.5, -0.5),
                                          (-0.5, -0.5, -0.5),
                                          (-0.5, -0.5, 0.5),
                                          (0.5, -0.5, 0.5),
                                          (-0.5, -0.5, 0.5),
                                          (-0.5, 0.5, 0.5)],
                                      knot = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])                                                                            
                mayac.move(0, -.4, .1, "%s.cv[1:2]" % (control), "%s.cv[5:6]" % (control), relative = True)
                mayac.move(0, .1, 0, "%s.cv[3:4]" % (control), "%s.cv[10:11]" % (control), relative = True)
                mayac.move(0, .3, 0, "%s.cv[0]" % (control), "%s.cv[7:8]" % (control), "%s.cv[15]" % (control), relative = True)
                mayac.scale(1.0, .75, 1.0, "%s.cv[1:6]" % (control), "%s.cv[10:11]" % (control))      
                mayac.scale(scale[0], scale[1], scale[2], control)
                mayac.rotate(rotate[0], rotate[1], rotate[2], control, relative = True)
                mayac.move(offset[0], offset[1], offset[2],  "%s.cv[0:15]" % (control), relative = True)
                mayac.makeIdentity(control, apply = True, t=1, r=1, s=1, n=0)
            else:
                print "exactSizeNotFunctionalYet"
                

                
        elif style == "circleWrapped":
            if estimateSize:
                control = mayac.circle(constructionHistory = 0)
                control = control[0]
                mayac.move(0, 0, 1.0, "%s.cv[3]" % (control), "%s.cv[7]" % (control), relative = True)
                mayac.move(0, 0, -1.0, "%s.cv[1]" % (control), "%s.cv[5]" % (control), relative = True)
                mayac.scale(scale[0],scale[1],scale[2])
                mayac.rotate(rotate[0], rotate[1], rotate[2], control, relative = True) #override for world-oriented rigs
                mayac.move(offset[0], offset[1], offset[2], "%s.cv[0:7]" % (control), relative = True)
                mayac.makeIdentity(control, apply = True, t=1, r=1, s=1, n=0)
            else:
                print "exactSizeNotFunctionalYet"
            
            
        elif style == "pin":
            if estimateSize:
                control = mayac.circle(constructionHistory = 0)
                control = control[0]
                mayac.scale(1.0, 0.0, 0.0, "%s.cv[1:5]" % (control))
                mayac.move(-2.891806, 0, 0, "%s.cv[3]" % (control), relative = True)
                mayac.move(4.0, 0, 0, "%s.cv[0:7]" % (control), relative = True)
                mayac.rotate(180, 0, 180, control)
                mayac.scale(scale[0], scale[1], scale[2], control)
                mayac.rotate(rotate[0], rotate[1], rotate[2], control, relative = True) #override for world-oriented rigs
                mayac.move(offset[0], offset[1], offset[2], "%s.cv[0:7]" % (control), relative = True)
                mayac.makeIdentity(control, apply = True, t=1, r=1, s=1, n=0)
            else:
                print "exactSizeNotFunctionalYet"
                
        elif style == "pin1" or style == "pin2":
            if estimateSize:
                control = mayac.circle(constructionHistory = 0)
                control = control[0]
                mayac.scale(1.0, 0.0, 0.0, "%s.cv[1:5]" % (control))
                mayac.move(-2.891806, 0, 0, "%s.cv[3]" % (control), relative = True)
                mayac.move(4.0, 0, 0, "%s.cv[0:7]" % (control), relative = True)
                mayac.scale(scale[0], scale[1], scale[2], control)
                mayac.rotate(rotate[0], rotate[1], rotate[2], control, relative = True) #override for world-oriented rigs
                mayac.move(offset[0], offset[1], offset[2], "%s.cv[0:7]" % (control), relative = True)
                mayac.makeIdentity(control, apply = True, t=1, r=1, s=1, n=0)
            else:
                print "exactSizeNotFunctionalYet"       
        

        elif style == "options":
            if estimateSize:
                control = mayac.curve(degree = 1,
                                      point = [(-1.03923, 0.0, 0.6),
                                          (1.03923, 0.0, 0.6),
                                          (0.0, 0.0, -1.2),
                                          (-1.03923, 0.0, 0.6)],
                                      knot = [0,1,2,3])    
                mayac.scale(scale[0], scale[1], scale[2], control)
                mayac.rotate(rotate[0], rotate[1], rotate[2], control, relative = True)
                mayac.rotate(rotate[0], rotate[1], rotate[2], control, relative = True) #override for world-oriented rigs
                mayac.move(offset[0], offset[1], offset[2],  "%s.cv[0:15]" % (control), relative = True)
                mayac.makeIdentity(control, apply = True, t=1, r=1, s=1, n=0)
            else:
                print "exactSizeNotFunctionalYet"
            
            
        elif style == "hula":
            if estimateSize:
                control = mayac.circle(constructionHistory = 0)
                control = control[0]
                mayac.move(0, 0, -0.5, "%s.cv[0]" % (control), "%s.cv[2]" % (control), "%s.cv[4]" % (control), "%s.cv[6]" % (control), relative = True)
                mayac.move(0, 0, 0.3, "%s.cv[1]" % (control), "%s.cv[3]" % (control), "%s.cv[5]" % (control), "%s.cv[7]" % (control), relative = True)
                mayac.rotate(0, 90, 90, control)
                mayac.scale(scale[0], scale[1], scale[2], control)
                mayac.move(offset[0], offset[1], offset[2], "%s.cv[0:7]" % (control), relative = True)
                mayac.makeIdentity(control, apply = True, t=1, r=1, s=1, n=0)
            else:
                print "exactSizeNotFunctionalYet"
                
                
        elif style == "PoleVector":
            if estimateSize:
                control = mayac.curve(degree = 1,
                                      point = [(0.0, 2.0, 0.0),
                                          (1.0, 0.0, -1.0),
                                          (-1.0, 0.0, -1.0),
                                          (0.0, 2.0, 0.0),
                                          (-1.0, 0.0, 1.0),
                                          (1.0, 0.0, 1.0),
                                          (0.0, 2.0, 0.0),
                                          (1.0, 0.0, -1.0),
                                          (1.0, 0.0, 1.0),
                                          (-1.0, 0.0, 1.0),
                                          (-1.0, 0.0, -1.0)],
                                      knot = [0,1,2,3,4,5,6,7,8,9,10])
                mayac.rotate(90, 0, 0, control)
                mayac.rotate(rotate[0], rotate[1], rotate[2], control, relative = True)                                                                                          
                mayac.scale(scale[0], scale[1], scale[2], control)
                mayac.move(offset[0], offset[1], offset[2],  "%s.cv[0:9]" % (control), relative = True)
                mayac.makeIdentity(control, apply = True, t=1, r=1, s=1, n=0)
            else:
                print "exactSizeNotFunctionalYet"


        #set color
        DJB_ChangeDisplayColor(control, color = color_)
        #place control
        if not partialConstraint:
            mayac.delete(mayac.parentConstraint(self.Bind_Joint, control))
        elif partialConstraint == 2:
            mayac.delete(mayac.parentConstraint(self.Bind_Joint, control, sr=["x"]))
        elif partialConstraint == 1:
            mayac.delete(mayac.pointConstraint(self.Bind_Joint, control))
            mayac.makeIdentity(control, apply = True, t=1, r=1, s=1, n=0)
            mayac.xform(control, cp = True)
            mayac.scale(1,-1,1, control)
            mayac.makeIdentity(control, apply = True, t=1, r=1, s=1, n=0)
            cvPos = mayac.xform("%s.cv[0]" % (control), query = True, worldSpace = True, translation = True)
            pivPosY = mayac.getAttr("%s.rotatePivotY" % (control))
            mayac.setAttr("%s.translateY" % (control), cvPos[1] - pivPosY)
            DJB_movePivotToObject(control, self.Bind_Joint, posOnly = True)
            mayac.delete(mayac.aimConstraint(self.children[0].Bind_Joint, control, skip = ["x", "z"], weight = 1, aimVector = (0,0,1), worldUpType = "vector", upVector = (0,1,0)))

        if style == "pin1":
            mayac.delete(mayac.orientConstraint(self.Bind_Joint, control, offset = (0,-90,90)))
        if type == "FK":
            self.FK_CTRL = mayac.rename(control, DJB_findAfterSeperator(self.nodeName, ":") + "_FK_CTRL")
            self.FK_CTRL_COLOR = color_ 
        elif type == "IK":
            self.IK_CTRL = mayac.rename(control, DJB_findAfterSeperator(self.nodeName, ":") + "_IK_CTRL")
            self.IK_CTRL_COLOR = color_
        elif type == "options":
            self.Options_CTRL = mayac.rename(control, DJB_findAfterSeperator(self.nodeName, ":") + "_Options")
            self.Options_CTRL_COLOR = color_
        elif type == "normal":
            if "Hips" in self.nodeName:
                if self.actAsRoot:
                    self.FK_CTRL = mayac.rename(control, "Root_CTRL")
                else:
                    self.FK_CTRL = mayac.rename(control, "Pelvis_CTRL")
            else:
                self.FK_CTRL = mayac.rename(control, DJB_findAfterSeperator(self.nodeName, ":") + "_CTRL")
            self.FK_CTRL_COLOR = color_
     
     
     
        
    def zeroToOrig(self, transform):
        if transform:
            if not mayac.getAttr("%s.tx" % (transform),lock=True):
                mel.eval('CBdeleteConnection "%s.tx";'%(transform))
                mayac.setAttr("%s.tx" % (transform), self.origPosX)
            if not mayac.getAttr("%s.ty" % (transform),lock=True):
                mel.eval('CBdeleteConnection "%s.ty";'%(transform))
                mayac.setAttr("%s.ty" % (transform), self.origPosY)
            if not mayac.getAttr("%s.tz" % (transform),lock=True):
                mel.eval('CBdeleteConnection "%s.tz";'%(transform))
                mayac.setAttr("%s.tz" % (transform), self.origPosZ)
            if not mayac.getAttr("%s.rx" % (transform),lock=True):
                mel.eval('CBdeleteConnection "%s.rx";'%(transform))
                mayac.setAttr("%s.rx" % (transform), self.origRotX)
            if not mayac.getAttr("%s.ry" % (transform),lock=True):
                mel.eval('CBdeleteConnection "%s.ry";'%(transform))
                mayac.setAttr("%s.ry" % (transform), self.origRotY)
            if not mayac.getAttr("%s.rz" % (transform),lock=True):
                mel.eval('CBdeleteConnection "%s.rz";'%(transform))
                mayac.setAttr("%s.rz" % (transform), self.origRotZ)




    def finalizeCTRLs(self, parent = "UseSelf"):   
        #record original positions, rotations
        self.origPosX = mayac.getAttr("%s.translateX" % (self.Bind_Joint))
        self.origPosY = mayac.getAttr("%s.translateY" % (self.Bind_Joint))
        self.origPosZ = mayac.getAttr("%s.translateZ" % (self.Bind_Joint))
        self.origRotX = mayac.getAttr("%s.rotateX" % (self.Bind_Joint))
        self.origRotY = mayac.getAttr("%s.rotateY" % (self.Bind_Joint))
        self.origRotZ = mayac.getAttr("%s.rotateZ" % (self.Bind_Joint))
        #hook up control
        if self.FK_CTRL:
            #place control
            temp = mayac.duplicate(self.Bind_Joint, parentOnly = True, name = "UnRotate" + self.nodeName)
            mayac.parent(self.FK_CTRL, temp[0])
            mayac.rotate(0,0,0, temp[0])
            mayac.parent(self.FK_CTRL, world = True)
            DJB_movePivotToObject(self.FK_CTRL, temp[0])
            mayac.delete(temp[0])
            #add attributes  
            mayac.addAttr(self.FK_CTRL, longName='AnimDataMult', defaultValue=1.0, keyable = True)
            self.FK_CTRL_inRig_CONST_GRP = DJB_createGroup(transform = self.FK_CTRL, fullName = self.FK_CTRL + "_In_Rig_CONST_GRP")
            self.FK_CTRL_animData_CONST_GRP = DJB_createGroup(transform = self.FK_CTRL_inRig_CONST_GRP, fullName = self.FK_CTRL + "_AnimData_CONST_GRP")
            self.FK_CTRL_animData_MultNode = mayac.createNode( 'multiplyDivide', n=self.FK_CTRL + "_AnimData_MultNode")
            self.FK_CTRL_POS_GRP = DJB_createGroup(transform = self.FK_CTRL_animData_CONST_GRP, fullName = self.FK_CTRL + "_POS_GRP")
            
            #set rotation orders
            mayac.setAttr("%s.rotateOrder" % (self.FK_CTRL), self.rotOrder)
            mayac.setAttr("%s.rotateOrder" % (self.FK_CTRL_inRig_CONST_GRP), self.rotOrder)
            mayac.setAttr("%s.rotateOrder" % (self.FK_CTRL_animData_CONST_GRP), self.rotOrder)
            mayac.setAttr("%s.rotateOrder" % (self.FK_CTRL_POS_GRP), self.rotOrder)
            
            #place in hierarchy
            if parent == "UseSelf" and self.parent:
                mayac.parent(self.FK_CTRL_POS_GRP, self.parent.FK_CTRL)
            elif parent != "UseSelf":
                mayac.parent(self.FK_CTRL_POS_GRP, parent)
                
            if "Head" in self.nodeName:
                mayac.addAttr(self.FK_CTRL, longName='InheritRotation', defaultValue=1.0, min = 0, max = 1.0, keyable = True)
                self.Inherit_Rotation_GRP = DJB_createGroup(transform = None, fullName = self.FK_CTRL + "_Inherit_Rotation_GRP", pivotFrom = self.FK_CTRL)
                mayac.parent(self.Inherit_Rotation_GRP, self.FK_CTRL_animData_CONST_GRP)
                mayac.setAttr("%s.inheritsTransform" % (self.Inherit_Rotation_GRP), 0)
                temp = mayac.orientConstraint(self.FK_CTRL_animData_CONST_GRP, self.FK_CTRL_inRig_CONST_GRP, maintainOffset = True)
                self.Inherit_Rotation_Constraint = temp[0]
                mayac.orientConstraint(self.Inherit_Rotation_GRP, self.FK_CTRL_inRig_CONST_GRP, maintainOffset = True)
                self.Inherit_Rotation_Constraint_Reverse = mayac.createNode( 'reverse', n="Head_Inherit_Rotation_Constraint_Reverse")
                mayac.connectAttr("%s.InheritRotation" %(self.FK_CTRL), "%s.inputX" %(self.Inherit_Rotation_Constraint_Reverse))
                mayac.connectAttr("%s.InheritRotation" %(self.FK_CTRL), "%s.%sW0" %(self.Inherit_Rotation_Constraint, self.FK_CTRL_animData_CONST_GRP))
                mayac.connectAttr("%s.outputX" %(self.Inherit_Rotation_Constraint_Reverse), "%s.%sW1" %(self.Inherit_Rotation_Constraint, self.Inherit_Rotation_GRP))
                mayac.setAttr("%s.interpType" %(self.Inherit_Rotation_Constraint), 2)
                
        
        
        
            #hook up CTRLs
            mayac.connectAttr("%s.rotateX" %(self.AnimData_Joint), "%s.input1X" %(self.FK_CTRL_animData_MultNode), force = True)
            mayac.connectAttr("%s.AnimDataMult" %(self.FK_CTRL), "%s.input2X" %(self.FK_CTRL_animData_MultNode), force = True)
            mayac.connectAttr("%s.rotateY" %(self.AnimData_Joint), "%s.input1Y" %(self.FK_CTRL_animData_MultNode), force = True)
            mayac.connectAttr("%s.AnimDataMult" %(self.FK_CTRL), "%s.input2Y" %(self.FK_CTRL_animData_MultNode), force = True)
            mayac.connectAttr("%s.rotateZ" %(self.AnimData_Joint), "%s.input1Z" %(self.FK_CTRL_animData_MultNode), force = True)
            mayac.connectAttr("%s.AnimDataMult" %(self.FK_CTRL), "%s.input2Z" %(self.FK_CTRL_animData_MultNode), force = True)
            
            mayac.connectAttr("%s.outputX" %(self.FK_CTRL_animData_MultNode), "%s.rotateX" %(self.FK_CTRL_animData_CONST_GRP), force = True)
            mayac.connectAttr("%s.outputY" %(self.FK_CTRL_animData_MultNode), "%s.rotateY" %(self.FK_CTRL_animData_CONST_GRP), force = True)
            mayac.connectAttr("%s.outputZ" %(self.FK_CTRL_animData_MultNode), "%s.rotateZ" %(self.FK_CTRL_animData_CONST_GRP), force = True)
            if not self.FK_Joint:
                if self.actAsRoot:
                    mayac.addAttr(self.FK_CTRL, longName='AnimDataMultTrans', defaultValue=1.0, keyable = True)
                    self.FK_CTRL_animData_MultNode_Trans = mayac.createNode( 'multiplyDivide', n=self.FK_CTRL + "_AnimData_MultNode_Trans")
                    temp = mayac.parentConstraint(self.FK_CTRL, self.Bind_Joint, mo = True, name = "%s_Constraint" %(self.nodeName))
                    self.Constraint = temp[0]
                    
                    mayac.connectAttr("%s.translateX" %(self.AnimData_Joint), "%s.input1X" %(self.FK_CTRL_animData_MultNode_Trans), force = True)
                    mayac.connectAttr("%s.AnimDataMultTrans" %(self.FK_CTRL), "%s.input2X" %(self.FK_CTRL_animData_MultNode_Trans), force = True)
                    mayac.connectAttr("%s.translateY" %(self.AnimData_Joint), "%s.input1Y" %(self.FK_CTRL_animData_MultNode_Trans), force = True)
                    mayac.connectAttr("%s.AnimDataMultTrans" %(self.FK_CTRL), "%s.input2Y" %(self.FK_CTRL_animData_MultNode_Trans), force = True)
                    mayac.connectAttr("%s.translateZ" %(self.AnimData_Joint), "%s.input1Z" %(self.FK_CTRL_animData_MultNode_Trans), force = True)
                    mayac.connectAttr("%s.AnimDataMultTrans" %(self.FK_CTRL), "%s.input2Z" %(self.FK_CTRL_animData_MultNode_Trans), force = True)
                    
                    mayac.connectAttr("%s.outputX" %(self.FK_CTRL_animData_MultNode_Trans), "%s.translateX" %(self.FK_CTRL_POS_GRP), force = True)
                    mayac.connectAttr("%s.outputY" %(self.FK_CTRL_animData_MultNode_Trans), "%s.translateY" %(self.FK_CTRL_POS_GRP), force = True)
                    mayac.connectAttr("%s.outputZ" %(self.FK_CTRL_animData_MultNode_Trans), "%s.translateZ" %(self.FK_CTRL_POS_GRP), force = True)
                    mayac.connectAttr("%s.outputX" %(self.FK_CTRL_animData_MultNode_Trans), "%s.translateX" %(self.IK_Dummy_Joint), force = True)
                    mayac.connectAttr("%s.outputY" %(self.FK_CTRL_animData_MultNode_Trans), "%s.translateY" %(self.IK_Dummy_Joint), force = True)
                    mayac.connectAttr("%s.outputZ" %(self.FK_CTRL_animData_MultNode_Trans), "%s.translateZ" %(self.IK_Dummy_Joint), force = True)
                else:
                    temp = mayac.orientConstraint(self.FK_CTRL, self.Bind_Joint, mo = True, name = "%s_Constraint" %(self.nodeName))
                    self.Constraint = temp[0]
                    mayac.setAttr("%s.offsetX" % (self.Constraint), 0)
                    mayac.setAttr("%s.offsetY" % (self.Constraint), 0)
                    mayac.setAttr("%s.offsetZ" % (self.Constraint), 0)
            else:
                temp= mayac.orientConstraint(self.FK_CTRL, self.FK_Joint, mo = True, name = "%s_FK_Constraint" %(self.nodeName))
                self.FK_Constraint = temp[0]
                temp = mayac.orientConstraint(self.FK_Joint, self.Bind_Joint, mo = True, name = "%s_FKIK_Constraint" %(self.nodeName))
                self.Constraint = temp[0]
                mayac.setAttr("%s.offsetX" % (self.Constraint), 0)
                mayac.setAttr("%s.offsetY" % (self.Constraint), 0)
                mayac.setAttr("%s.offsetZ" % (self.Constraint), 0)
        
        if self.IK_Dummy_Joint:
            mayac.connectAttr("%s.rotateX" %(self.AnimData_Joint), "%s.rotateX" %(self.IK_Dummy_Joint), force = True)
            mayac.connectAttr("%s.rotateY" %(self.AnimData_Joint), "%s.rotateY" %(self.IK_Dummy_Joint), force = True)
            mayac.connectAttr("%s.rotateZ" %(self.AnimData_Joint), "%s.rotateZ" %(self.IK_Dummy_Joint), force = True)

        if self.IK_CTRL:
            #place control
            if "Foot" in self.nodeName:
                self.footRotateLOC = mayac.spaceLocator(n = self.IK_CTRL + "_footRotateLOC")
                self.footRotateLOC = self.footRotateLOC[0]
                DJB_movePivotToObject(self.footRotateLOC, self.IK_Joint)
                mayac.delete(mayac.orientConstraint(self.IK_CTRL, self.footRotateLOC))
                mayac.setAttr("%s.rotateOrder" % (self.footRotateLOC), self.rotOrder)

                
                
            temp = mayac.duplicate(self.Bind_Joint, parentOnly = True, name = "UnRotate" + self.nodeName)
            mayac.parent(self.IK_CTRL, temp[0])
            mayac.rotate(0,0,0, temp[0])
            mayac.parent(self.IK_CTRL, world = True)
            DJB_movePivotToObject(self.IK_CTRL, temp[0])
            mayac.delete(temp[0])
            #add attributes  
            mayac.addAttr(self.IK_CTRL, longName='AnimDataMult', defaultValue=1.0, keyable = True)
            mayac.addAttr(self.IK_CTRL, longName='FollowBody', defaultValue=1.0, minValue = 0, maxValue = 1.0, keyable = True)
            if "Foot" in self.nodeName:
                self.IK_CTRL_ReorientGRP = DJB_createGroup(transform = self.IK_CTRL, fullName = self.IK_CTRL + "_Reorient_GRP")
                self.IK_CTRL_inRig_CONST_GRP = DJB_createGroup(transform = self.IK_CTRL_ReorientGRP, fullName = self.IK_CTRL + "_In_Rig_CONST_GRP")
                DJB_movePivotToObject(self.IK_CTRL, self.footRotateLOC)
                DJB_movePivotToObject(self.IK_CTRL_ReorientGRP, self.footRotateLOC)
                mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_ReorientGRP), self.rotOrder)
                mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_inRig_CONST_GRP), self.rotOrder)
                #mayac.delete(self.footRotateLOC)
                mayac.parent(self.IK_CTRL_ReorientGRP, self.IK_CTRL_inRig_CONST_GRP)
                mayac.parent(self.IK_CTRL, self.IK_CTRL_ReorientGRP)
            else:
                self.IK_CTRL_inRig_CONST_GRP = DJB_createGroup(transform = self.IK_CTRL, fullName = self.IK_CTRL + "_In_Rig_CONST_GRP")
            self.IK_CTRL_animData_CONST_GRP = DJB_createGroup(transform = self.IK_CTRL_inRig_CONST_GRP, fullName = self.IK_CTRL + "_AnimData_CONST_GRP")
            self.IK_CTRL_animData_MultNode = mayac.createNode( 'multiplyDivide', n=self.IK_CTRL + "_AnimData_MultNode")
            self.IK_CTRL_POS_GRP = DJB_createGroup(transform = self.IK_CTRL_animData_CONST_GRP, fullName = self.IK_CTRL + "_POS_GRP")
            
            #set rotation orders
            mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL), self.rotOrder)
            mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_inRig_CONST_GRP), self.rotOrder)
            mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_animData_CONST_GRP), self.rotOrder)
            mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_POS_GRP), self.rotOrder)
            
            #place in hierarchy
            #hook up CTRLs
            mayac.connectAttr("%s.rotateX" %(self.AnimData_Joint), "%s.input1X" %(self.IK_CTRL_animData_MultNode), force = True)
            mayac.connectAttr("%s.AnimDataMult" %(self.IK_CTRL), "%s.input2X" %(self.IK_CTRL_animData_MultNode), force = True)
            mayac.connectAttr("%s.rotateY" %(self.AnimData_Joint), "%s.input1Y" %(self.IK_CTRL_animData_MultNode), force = True)
            mayac.connectAttr("%s.AnimDataMult" %(self.IK_CTRL), "%s.input2Y" %(self.IK_CTRL_animData_MultNode), force = True)
            mayac.connectAttr("%s.rotateZ" %(self.AnimData_Joint), "%s.input1Z" %(self.IK_CTRL_animData_MultNode), force = True)
            mayac.connectAttr("%s.AnimDataMult" %(self.IK_CTRL), "%s.input2Z" %(self.IK_CTRL_animData_MultNode), force = True)
            
            mayac.connectAttr("%s.outputX" %(self.IK_CTRL_animData_MultNode), "%s.rotateX" %(self.IK_CTRL_animData_CONST_GRP), force = True)
            mayac.connectAttr("%s.outputY" %(self.IK_CTRL_animData_MultNode), "%s.rotateY" %(self.IK_CTRL_animData_CONST_GRP), force = True)
            mayac.connectAttr("%s.outputZ" %(self.IK_CTRL_animData_MultNode), "%s.rotateZ" %(self.IK_CTRL_animData_CONST_GRP), force = True)
            
            if "Hand" in self.nodeName or "ForeArm" in self.nodeName or "Foot" in self.nodeName or "Leg" in self.nodeName:
                self.IK_CTRL_parent_animData_CONST_GRP = DJB_createGroup(transform = self.IK_CTRL_POS_GRP, fullName = self.IK_CTRL + "_parent_AnimData_CONST_GRP")
                
                #place parent GRP
                temp = mayac.duplicate(self.parent.Bind_Joint, parentOnly = True, name = "UnRotate" + self.nodeName)
                mayac.parent(self.IK_CTRL_parent_animData_CONST_GRP, temp[0])
                mayac.rotate(0,0,0, temp[0])
                mayac.parent(self.IK_CTRL_POS_GRP, world = True)
                mayac.parent(self.IK_CTRL_parent_animData_CONST_GRP, world = True)
                DJB_movePivotToObject(self.IK_CTRL_parent_animData_CONST_GRP, temp[0])
                mayac.delete(temp[0])
                mayac.parent(self.IK_CTRL_POS_GRP, self.IK_CTRL_parent_animData_CONST_GRP)
                
                self.IK_CTRL_parent_animData_MultNode = mayac.createNode( 'multiplyDivide', n=self.IK_CTRL + "_parent_AnimData_MultNode")
                self.IK_CTRL_parent_Global_POS_GRP = DJB_createGroup(transform = self.IK_CTRL_parent_animData_CONST_GRP, fullName = self.IK_CTRL + "_parent_Global_POS_GRP")
                self.IK_CTRL_parent_POS_GRP = DJB_createGroup(transform = self.IK_CTRL_parent_Global_POS_GRP, fullName = self.IK_CTRL + "_parent_POS_GRP")

                #set rotation orders
                mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_parent_animData_CONST_GRP), self.parent.rotOrder)
                mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_parent_Global_POS_GRP), self.parent.rotOrder)
                mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_parent_POS_GRP), self.parent.rotOrder)

                mayac.connectAttr("%s.rotateX" %(self.parent.AnimData_Joint), "%s.input1X" %(self.IK_CTRL_parent_animData_MultNode), force = True)
                mayac.connectAttr("%s.AnimDataMult" %(self.IK_CTRL), "%s.input2X" %(self.IK_CTRL_parent_animData_MultNode), force = True)
                mayac.connectAttr("%s.rotateY" %(self.parent.AnimData_Joint), "%s.input1Y" %(self.IK_CTRL_parent_animData_MultNode), force = True)
                mayac.connectAttr("%s.AnimDataMult" %(self.IK_CTRL), "%s.input2Y" %(self.IK_CTRL_parent_animData_MultNode), force = True)
                mayac.connectAttr("%s.rotateZ" %(self.parent.AnimData_Joint), "%s.input1Z" %(self.IK_CTRL_parent_animData_MultNode), force = True)
                mayac.connectAttr("%s.AnimDataMult" %(self.IK_CTRL), "%s.input2Z" %(self.IK_CTRL_parent_animData_MultNode), force = True)
                
                mayac.connectAttr("%s.outputX" %(self.IK_CTRL_parent_animData_MultNode), "%s.rotateX" %(self.IK_CTRL_parent_animData_CONST_GRP), force = True)
                mayac.connectAttr("%s.outputY" %(self.IK_CTRL_parent_animData_MultNode), "%s.rotateY" %(self.IK_CTRL_parent_animData_CONST_GRP), force = True)
                mayac.connectAttr("%s.outputZ" %(self.IK_CTRL_parent_animData_MultNode), "%s.rotateZ" %(self.IK_CTRL_parent_animData_CONST_GRP), force = True)
                
                mayac.addAttr(self.IK_CTRL, longName='ParentToGlobal', defaultValue=0.0, minValue = 0, maxValue = 1.0, keyable = True)

                if "ForeArm" in self.nodeName:
                    mayac.addAttr(self.IK_CTRL, longName='FollowHand', defaultValue=0.0, minValue = 0, maxValue = 1.0, keyable = True)
                    #if "Left" in self.nodeName:
                        #mayac.aimConstraint(self.IK_Joint, self.IK_CTRL, upVector = (0,1,0), aimVector = (-1,0,0))
                    #elif "Right" in self.nodeName:
                        #mayac.aimConstraint(self.IK_Joint, self.IK_CTRL, upVector = (0,1,0), aimVector = (1,0,0))
                        
                    #IK elbow bakingLOCs
                    temp = mayac.spaceLocator(name = "%s_IK_BakingLOC" % (self.nodeName))
                    self.IK_BakingLOC = temp[0]
                    mayac.parent(self.IK_BakingLOC, self.Bind_Joint)
                    DJB_ZeroOut(self.IK_BakingLOC)
                    mayac.setAttr("%s.rotateOrder" % (self.IK_BakingLOC), self.rotOrder)
                    
                    
                
                        
                if "Leg" in self.nodeName:
                    mayac.addAttr(self.IK_CTRL, longName='FollowFoot', defaultValue=0.0, minValue = 0, maxValue = 1.0, keyable = True)
                    #mayac.aimConstraint(self.IK_Joint, self.IK_CTRL, upVector = (0,1,0), aimVector = (0,0,-1))
                    
                    #groups for follow foot Attr
                    self.Follow_Knee_GRP = DJB_createGroup(transform = None, fullName = self.IK_CTRL + "_Follow_Knee_GRP", pivotFrom = self.FK_CTRL)
                    self.Follow_Foot_GRP = DJB_createGroup(transform = self.Follow_Knee_GRP, fullName = self.IK_CTRL + "_Follow_Foot_GRP", pivotFrom = self.FK_CTRL)
                    #set rotation orders
                    mayac.setAttr("%s.rotateOrder" % (self.Follow_Knee_GRP), self.rotOrder)
                    mayac.setAttr("%s.rotateOrder" % (self.Follow_Foot_GRP), self.rotOrder)

                    mayac.parent(self.Follow_Foot_GRP, self.IK_CTRL_animData_CONST_GRP)
                    selfPOS = mayac.xform(self.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
                    parentPOS = mayac.xform(self.parent.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
                    tempDistance = math.sqrt((selfPOS[0]-parentPOS[0])*(selfPOS[0]-parentPOS[0]) + (selfPOS[1]-parentPOS[1])*(selfPOS[1]-parentPOS[1]) + (selfPOS[2]-parentPOS[2])*(selfPOS[2]-parentPOS[2]))
                    mayac.setAttr("%s.translateZ" % (self.Follow_Knee_GRP), tempDistance / 2)
                    temp = mayac.pointConstraint(self.IK_Joint, self.Follow_Knee_GRP, sk = ("x", "y"), mo = True)
                    self.Follow_Knee_Constraint = temp[0]
                    
                    #IK knee bakingLOCs
                    temp = mayac.spaceLocator(name = "%s_IK_BakingLOC" % (self.nodeName))
                    self.IK_BakingLOC = temp[0]
                    mayac.parent(self.IK_BakingLOC, self.Bind_Joint)
                    DJB_ZeroOut(self.IK_BakingLOC)
                    mayac.setAttr("%s.rotateOrder" % (self.IK_BakingLOC), self.rotOrder)

                    if "Left" in self.nodeName:
                        mayac.setAttr("%s.translateZ" % (self.IK_BakingLOC), tempDistance / 2)
                        #mayac.setAttr("%s.translateX" % (self.IK_BakingLOC), -2.017)
                    elif "Right" in self.nodeName:
                        mayac.setAttr("%s.translateZ" % (self.IK_BakingLOC), tempDistance / 2)
                    

                if "Hand" in self.nodeName or "Foot" in self.nodeName:
                    self.IK_CTRL_grandparent_inRig_CONST_GRP = DJB_createGroup(transform = self.IK_CTRL_parent_POS_GRP, fullName = self.IK_CTRL + "_grandparent_inRig_CONST_GRP", pivotFrom = self.parent.parent.Bind_Joint)
                    
                    
                    #place parent GRP
                    temp = mayac.duplicate(self.parent.parent.Bind_Joint, parentOnly = True, name = "UnRotate" + self.nodeName)
                    mayac.parent(self.IK_CTRL_grandparent_inRig_CONST_GRP, temp[0])
                    mayac.rotate(0,0,0, temp[0])
                    mayac.parent(self.IK_CTRL_parent_POS_GRP, world = True)
                    mayac.parent(self.IK_CTRL_grandparent_inRig_CONST_GRP, world = True)
                    DJB_movePivotToObject(self.IK_CTRL_grandparent_inRig_CONST_GRP, temp[0])
                    mayac.delete(temp[0])
                    mayac.parent(self.IK_CTRL_parent_POS_GRP, self.IK_CTRL_grandparent_inRig_CONST_GRP)
                
                    self.IK_CTRL_grandparent_animData_CONST_GRP = DJB_createGroup(transform = self.IK_CTRL_grandparent_inRig_CONST_GRP, fullName = self.IK_CTRL + "_grandparent_AnimData_CONST_GRP")
                    self.IK_CTRL_grandparent_animData_MultNode = mayac.createNode( 'multiplyDivide', n=self.IK_CTRL + "_grandparent_AnimData_MultNode")
                    self.IK_CTRL_grandparent_Global_POS_GRP = DJB_createGroup(transform = self.IK_CTRL_grandparent_animData_CONST_GRP, fullName = self.IK_CTRL + "_grandparent_Global_POS_GRP")
                    self.IK_CTRL_grandparent_POS_GRP = DJB_createGroup(transform = self.IK_CTRL_grandparent_Global_POS_GRP, fullName = self.IK_CTRL + "_grandparent_POS_GRP")
                    
                    #set rotation orders
                    mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_grandparent_inRig_CONST_GRP), self.parent.parent.rotOrder)
                    mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_grandparent_animData_CONST_GRP), self.parent.parent.rotOrder)
                    mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_grandparent_Global_POS_GRP), self.parent.parent.rotOrder)
                    mayac.setAttr("%s.rotateOrder" % (self.IK_CTRL_grandparent_POS_GRP), self.parent.parent.rotOrder)
                    
                    mayac.connectAttr("%s.rotateX" %(self.parent.parent.AnimData_Joint), "%s.input1X" %(self.IK_CTRL_grandparent_animData_MultNode), force = True)
                    mayac.connectAttr("%s.AnimDataMult" %(self.IK_CTRL), "%s.input2X" %(self.IK_CTRL_grandparent_animData_MultNode), force = True)
                    mayac.connectAttr("%s.rotateY" %(self.parent.parent.AnimData_Joint), "%s.input1Y" %(self.IK_CTRL_grandparent_animData_MultNode), force = True)
                    mayac.connectAttr("%s.AnimDataMult" %(self.IK_CTRL), "%s.input2Y" %(self.IK_CTRL_grandparent_animData_MultNode), force = True)
                    mayac.connectAttr("%s.rotateZ" %(self.parent.parent.AnimData_Joint), "%s.input1Z" %(self.IK_CTRL_grandparent_animData_MultNode), force = True)
                    mayac.connectAttr("%s.AnimDataMult" %(self.IK_CTRL), "%s.input2Z" %(self.IK_CTRL_grandparent_animData_MultNode), force = True)
                    
                    mayac.connectAttr("%s.outputX" %(self.IK_CTRL_grandparent_animData_MultNode), "%s.rotateX" %(self.IK_CTRL_grandparent_animData_CONST_GRP), force = True)
                    mayac.connectAttr("%s.outputY" %(self.IK_CTRL_grandparent_animData_MultNode), "%s.rotateY" %(self.IK_CTRL_grandparent_animData_CONST_GRP), force = True)
                    mayac.connectAttr("%s.outputZ" %(self.IK_CTRL_grandparent_animData_MultNode), "%s.rotateZ" %(self.IK_CTRL_grandparent_animData_CONST_GRP), force = True)
                    
                    temp = mayac.ikHandle( n="%s_IK_Handle" % (self.nodeName), sj= self.parent.parent.IK_Joint, ee= self.IK_Joint, solver = "ikRPsolver", weight = 1)
                    self.IK_Handle = temp[0]
                    mayac.setAttr("%s.visibility" % (self.IK_Handle), 0)
                    self.IK_EndEffector = temp[1]
                    temp = mayac.poleVectorConstraint( self.parent.IK_CTRL, self.IK_Handle )
                    self.PV_Constraint = temp[0]
                    if "Foot" in self.nodeName:
                        temp = mayac.orientConstraint(self.IK_CTRL_inRig_CONST_GRP, self.IK_Joint)
                        self.IK_Constraint = temp[0]
                    else:
                        temp = mayac.orientConstraint(self.IK_CTRL, self.IK_Joint)
                        self.IK_Constraint = temp[0]
                                     
                    
                    if "Hand" in self.nodeName:
                        mayac.parent(self.IK_Handle, self.IK_CTRL)
                        DJB_LockNHide(self.IK_Handle)
                        DJB_LockNHide(self.IK_EndEffector)
                    if "Foot" in self.nodeName:
                        mayac.addAttr(self.IK_CTRL, longName='FootControls', defaultValue=0.0, hidden = False, keyable = True)
                        mayac.setAttr("%s.FootControls" % (self.IK_CTRL), lock = True)
                        mayac.addAttr(self.IK_CTRL, longName='FootRoll', defaultValue=0.0, hidden = False, keyable = True)
                        mayac.addAttr(self.IK_CTRL, longName='ToeTap', defaultValue=0.0, hidden = False, keyable = True)
                        mayac.addAttr(self.IK_CTRL, longName='ToeSideToSide', defaultValue=0.0, hidden = False, keyable = True)
                        mayac.addAttr(self.IK_CTRL, longName='ToeRotate', defaultValue=0.0, hidden = False, keyable = True)
                        mayac.addAttr(self.IK_CTRL, longName='ToeRoll', defaultValue=0.0, hidden = False, keyable = True)
                        mayac.addAttr(self.IK_CTRL, longName='HipPivot', defaultValue=0.0, hidden = False, keyable = True)
                        mayac.addAttr(self.IK_CTRL, longName='BallPivot', defaultValue=0.0, hidden = False, keyable = True)
                        mayac.addAttr(self.IK_CTRL, longName='ToePivot', defaultValue=0.0, hidden = False, keyable = True)
                        mayac.addAttr(self.IK_CTRL, longName='HipSideToSide', defaultValue=0.0, hidden = False, keyable = True)
                        mayac.addAttr(self.IK_CTRL, longName='HipBackToFront', defaultValue=0.0, hidden = False, keyable = True)
                        
                        #Foot IK Baking LOCs
                        temp = mayac.spaceLocator(n = "%s_IK_BakingLOC" % (self.nodeName))
                        self.IK_BakingLOC = temp[0]
                        mayac.setAttr("%s.visibility"%(self.IK_BakingLOC), 0)
                        mayac.parent(self.IK_BakingLOC, self.Bind_Joint)
                        mayac.delete(mayac.parentConstraint(self.IK_CTRL, self.IK_BakingLOC))
                        

            mayac.orientConstraint(self.IK_Joint, self.Bind_Joint, mo = True)
        if not self.IK_CTRL and self.IK_Joint:
            mayac.orientConstraint(self.IK_Joint, self.Bind_Joint, mo = True)
            
        if self.Options_CTRL:
            #place control
            DJB_movePivotToObject(self.Options_CTRL, self.Bind_Joint)
            mayac.parentConstraint(self.Bind_Joint, self.Options_CTRL, mo = True, name = "%s_Constraint" %(self.Options_CTRL))
            #add attributes  
            mayac.addAttr(self.Options_CTRL, longName='FK_IK', defaultValue=0.0, min = 0.0, max = 1.0, keyable = True)
            mayac.setAttr("%s.rotateOrder" % (self.Options_CTRL), self.rotOrder)
            if "Hand" in self.nodeName:
                mayac.addAttr(self.Options_CTRL, longName='FingerControls', defaultValue=0.0, hidden = False, keyable = True)
                mayac.setAttr("%s.FingerControls" % (self.Options_CTRL), lock = True)
                mayac.addAttr(self.Options_CTRL, longName='ThumbCurl', defaultValue=0.0, min = -10.0, max = 10.0, hidden = False, keyable = True)
                mayac.addAttr(self.Options_CTRL, longName='IndexCurl', defaultValue=0.0, min = -10.0, max = 10.0, hidden = False, keyable = True)
                mayac.addAttr(self.Options_CTRL, longName='MiddleCurl', defaultValue=0.0, min = -10.0, max = 10.0, hidden = False, keyable = True)
                mayac.addAttr(self.Options_CTRL, longName='RingCurl', defaultValue=0.0, min = -10.0, max = 10.0, hidden = False, keyable = True)
                mayac.addAttr(self.Options_CTRL, longName='PinkyCurl', defaultValue=0.0, min = -10.0, max = 10.0, hidden = False, keyable = True)
                mayac.addAttr(self.Options_CTRL, longName='Sway', defaultValue=0.0, min = -10.0, max = 10.0, hidden = False, keyable = True)
                mayac.addAttr(self.Options_CTRL, longName='Spread', defaultValue=0.0, min = -10.0, max = 10.0, hidden = False, keyable = True)
                
            
            
            
    def lockUpCTRLs(self):    
        #lock and hide attributes
        if self.FK_CTRL:
            if self.nodeName == "Root":
                DJB_LockNHide(self.FK_CTRL, tx = False, ty = False, tz = False, rx = False, ry = False, rz = False)
            elif self.nodeName == "Hips" and self.actAsRoot:
                DJB_LockNHide(self.FK_CTRL, tx = False, ty = False, tz = False, rx = False, ry = False, rz = False)
            else:
                DJB_LockNHide(self.FK_CTRL, rx = False, ry = False, rz = False)
            DJB_LockNHide(self.FK_CTRL_inRig_CONST_GRP)
            DJB_LockNHide(self.FK_CTRL_animData_CONST_GRP)
            DJB_LockNHide(self.FK_CTRL_POS_GRP)
            
        if self.IK_CTRL:
            #lock and hide channels
            DJB_LockNHide(self.IK_CTRL, tx = False, ty = False, tz = False, rx = False, ry = False, rz = False)
            DJB_LockNHide(self.IK_CTRL_inRig_CONST_GRP)
            DJB_LockNHide(self.IK_CTRL_animData_CONST_GRP)
            DJB_LockNHide(self.IK_CTRL_POS_GRP)
            if self.IK_CTRL_grandparent_inRig_CONST_GRP:
                DJB_LockNHide(self.IK_CTRL_grandparent_inRig_CONST_GRP)
            if self.IK_CTRL_parent_POS_GRP:
                DJB_LockNHide(self.IK_CTRL_parent_POS_GRP)
                DJB_LockNHide(self.IK_CTRL_parent_Global_POS_GRP)
                DJB_LockNHide(self.IK_CTRL_parent_animData_CONST_GRP)
                if self.IK_CTRL_grandparent_POS_GRP:
                    DJB_LockNHide(self.IK_CTRL_grandparent_POS_GRP)
                    DJB_LockNHide(self.IK_CTRL_grandparent_Global_POS_GRP)
                    DJB_LockNHide(self.IK_CTRL_grandparent_animData_CONST_GRP)
            if self.IK_CTRL_ReorientGRP:
                DJB_LockNHide(self.IK_CTRL_ReorientGRP)
            if self.IK_Handle:
                DJB_LockNHide(self.IK_Handle)
            if "ForeArm" in self.nodeName or "LeftLeg" in self.nodeName or "RightLeg" in self.nodeName:
                DJB_LockNHide(self.IK_CTRL, tx = False, ty = False, tz = False, rx = True, ry = True, rz = True)
                mayac.setAttr("%s.visibility" % (self.IK_BakingLOC), 0)
            
        if self.Options_CTRL:
            DJB_LockNHide(self.Options_CTRL)
            
        


class DJB_Character():
    def __init__(self, infoNode_ = None, hulaOption_ = 0):
        self.characterNameSpace = None
        self.joints = None
        self.original_Mesh_Names = None
        self.mesh = None
        self.jointNamespace = None
        self.BoundingBox = None
        self.Root = None
        self.Hips = None
        self.Spine = None
        self.Spine1 = None
        self.Spine2 = None
        self.Spine3 = None
        self.Neck = None
        self.Neck1 = None
        self.Head = None
        self.HeadTop_End = None
        self.LeftShoulder = None
        self.LeftArm = None
        self.LeftForeArm = None
        self.LeftHand = None
        self.LeftHandThumb1 = None
        self.LeftHandThumb2 = None
        self.LeftHandThumb3 = None
        self.LeftHandThumb4 = None
        self.LeftHandIndex1 = None
        self.LeftHandIndex2 = None
        self.LeftHandIndex3 = None
        self.LeftHandIndex4 = None
        self.LeftHandMiddle1 = None
        self.LeftHandMiddle2 = None
        self.LeftHandMiddle3 = None
        self.LeftHandMiddle4 = None
        self.LeftHandRing1 = None
        self.LeftHandRing2 = None
        self.LeftHandRing3 = None
        self.LeftHandRing4 = None
        self.LeftHandPinky1 = None
        self.LeftHandPinky2 = None
        self.LeftHandPinky3 = None
        self.LeftHandPinky4 = None
        self.RightShoulder = None
        self.RightArm = None
        self.RightForeArm = None
        self.RightHand = None
        self.RightHandThumb1 = None
        self.RightHandThumb2 = None
        self.RightHandThumb3 = None
        self.RightHandThumb4 = None
        self.RightHandIndex1 = None
        self.RightHandIndex2 = None
        self.RightHandIndex3 = None
        self.RightHandIndex4 = None
        self.RightHandMiddle1 = None
        self.RightHandMiddle2 = None
        self.RightHandMiddle3 = None
        self.RightHandMiddle4 = None
        self.RightHandRing1 = None
        self.RightHandRing2 = None
        self.RightHandRing3 = None
        self.RightHandRing4 = None
        self.RightHandPinky1 = None
        self.RightHandPinky2 = None
        self.RightHandPinky3 = None
        self.RightHandPinky4 = None
        self.LeftUpLeg = None
        self.LeftLeg = None
        self.LeftFoot = None
        self.LeftToeBase = None
        self.LeftToe_End = None
        self.RightUpLeg = None
        self.RightLeg = None
        self.RightFoot = None
        self.RightToeBase = None
        self.RightToe_End = None
        self.bodyParts = None
        self.proportions = {}
        self.defaultControlScale = 0
        self.Character_GRP = None
        self.global_CTRL = None
        self.CTRL_GRP = None
        self.Joint_GRP = None
        self.AnimData_Joint_GRP = None
        self.Bind_Joint_GRP = None
        self.Mesh_GRP = None
        self.Misc_GRP = None
        self.LeftArm_Switch_Reverse = None
        self.RightArm_Switch_Reverse = None
        self.LeftLeg_Switch_Reverse = None
        self.RightLeg_Switch_Reverse = None
        self.Bind_Joint_SelectSet = None
        self.AnimData_Joint_SelectSet = None
        self.Controls_SelectSet = None
        self.Geo_SelectSet = None
        self.Left_Toe_IK_AnimData_GRP = None
        self.Left_Toe_IK_CTRL = None
        self.Left_ToeBase_IK_AnimData_GRP = None
        self.Left_IK_ToeBase_animData_MultNode = None
        self.Left_ToeBase_IK_CTRL = None
        self.Left_Ankle_IK_AnimData_GRP = None
        self.Left_Ankle_IK_CTRL = None
        self.Left_ToeBase_IkHandle = None
        self.Left_ToeEnd_IkHandle = None
        self.Right_Toe_IK_AnimData_GRP = None
        self.Right_Toe_IK_CTRL = None
        self.Right_ToeBase_IK_AnimData_GRP = None
        self.Right_IK_ToeBase_animData_MultNode = None
        self.Right_ToeBase_IK_CTRL = None
        self.Right_Ankle_IK_AnimData_GRP = None
        self.Right_Ankle_IK_CTRL = None
        self.Right_ToeBase_IkHandle = None
        self.Right_ToeEnd_IkHandle = None
        self.LeftHand_CTRLs_GRP = None
        self.RightHand_CTRLs_GRP = None
        self.LeftFoot_FootRoll_MultNode = None
        self.LeftFoot_ToeRoll_MultNode = None
        self.RightFoot_FootRoll_MultNode = None
        self.RightFoot_ToeRoll_MultNode = None
        self.RightFoot_HipPivot_MultNode = None
        self.RightFoot_BallPivot_MultNode = None
        self.RightFoot_ToePivot_MultNode = None
        self.RightFoot_HipSideToSide_MultNode = None
        self.RightFoot_ToeRotate_MultNode = None
        self.IK_Dummy_Joint_GRP = None
        self.LeftHand_grandparent_Constraint = None
        self.LeftHand_grandparent_Constraint_Reverse = None
        self.RightHand_grandparent_Constraint = None
        self.RightHand_grandparent_Constraint_Reverse = None
        self.LeftForeArm_grandparent_Constraint = None
        self.LeftForeArm_grandparent_Constraint_Reverse = None
        self.RightForeArm_grandparent_Constraint = None
        self.RightForeArm_grandparent_Constraint_Reverse = None
        self.origAnim = None
        self.origAnimation_Layer = None
        self.Mesh_Layer = None
        self.Bind_Joint_Layer = None
        self.infoNode = infoNode_
        self.rigType = None
        
        self.hulaOption = hulaOption_
        self.exportList = None
        
        if not self.infoNode:
            mayac.currentTime(1)
            self.joints = mayac.ls(type = "joint")
            locators = mayac.ls(et = "locator")
            if locators:
                mayac.delete(locators)
            global JOINT_NAMESPACE
            self.mesh = []
            temp = mayac.ls(geometry = True)
            self.original_Mesh_Names = []
            shapes = []
            for geo in temp:
                if "ShapeOrig" not in geo and "Bounding_Box_Override_Cube" not in geo:
                    shapes.append(geo)
                    transform = mayac.listRelatives(geo, parent = True)[0]
                    self.original_Mesh_Names.append(transform)
            for geo in shapes:
                parent = mayac.listRelatives(geo, parent = True)[0]
                DJB_Unlock(parent)
                parent = mayac.rename(parent, "Mesh_%s" % (DJB_findAfterSeperator(parent, ":")))
                self.mesh.append(mayac.listRelatives(parent, children = True, type = "shape")[0])
                
            self.jointNamespace = JOINT_NAMESPACE = DJB_findBeforeSeparator(self.joints[1], ':') #changed from 0 for one special case - zombie lores
            
            #override box gets proportions if it exists
            global DJB_Character_ProportionOverrideCube
            if DJB_Character_ProportionOverrideCube:
                if mayac.objExists(DJB_Character_ProportionOverrideCube):
                    self.BoundingBox = mayac.exactWorldBoundingBox(DJB_Character_ProportionOverrideCube)
                    mayac.delete(DJB_Character_ProportionOverrideCube)
                else:
                    DJB_Character_ProportionOverrideCube = ""
                    self.BoundingBox = mayac.exactWorldBoundingBox(self.mesh)
            else:
                self.BoundingBox = mayac.exactWorldBoundingBox(self.mesh)
            
            if self.hulaOption:              
                self.Root = DJB_CharacterNode("Root", actAsRoot_ = 1, optional_ = 1)
                if not self.Root.Bind_Joint:
                    mayac.duplicate(self.jointNamespace + "Hips", parentOnly = True, name = self.jointNamespace + "Root")
                    self.Root = DJB_CharacterNode("Root", actAsRoot_ = 1)
                self.Hips = DJB_CharacterNode("Hips", parent = self.Root)
                self.Spine = DJB_CharacterNode("Spine", parent = self.Root)
                mayac.parent(self.Hips.Bind_Joint, self.Spine.Bind_Joint, self.Root.Bind_Joint)
            else:
                self.Root = DJB_CharacterNode("Root", optional_ = 1)
                if self.Root.Bind_Joint:
                    self.Hips = DJB_CharacterNode("Hips")
                    self.hulaOption = True
                else:
                    self.Hips = DJB_CharacterNode("Hips", actAsRoot_ = 1)
                self.Spine = DJB_CharacterNode("Spine", parent = self.Hips)
                
            self.Spine1 = DJB_CharacterNode("Spine1", parent = self.Spine)
            self.Spine2 = DJB_CharacterNode("Spine2", parent = self.Spine1)
            self.Spine3 = DJB_CharacterNode("Spine3", parent = self.Spine2, optional_ = 1)
            if self.Spine3.Bind_Joint:
                self.Neck = DJB_CharacterNode("Neck", parent = self.Spine3)
            else:
                self.Neck = DJB_CharacterNode("Neck", parent = self.Spine2)
            self.Neck1 = DJB_CharacterNode("Neck1", parent = self.Neck, optional_ = 1)
            if self.Neck1.Bind_Joint:
                self.Head = DJB_CharacterNode("Head", parent = self.Neck1)
            else:
                self.Head = DJB_CharacterNode("Head", parent = self.Neck)
            self.HeadTop_End = DJB_CharacterNode("HeadTop_End", parent = self.Head, alias_ = ["Head_End", "Head_END"])
            if self.Spine3.Bind_Joint:
                self.LeftShoulder = DJB_CharacterNode("LeftShoulder", parent = self.Spine3)
            else:
                self.LeftShoulder = DJB_CharacterNode("LeftShoulder", parent = self.Spine2)
            self.LeftArm = DJB_CharacterNode("LeftArm", parent = self.LeftShoulder)
            self.LeftForeArm = DJB_CharacterNode("LeftForeArm", parent = self.LeftArm)
            self.LeftHand = DJB_CharacterNode("LeftHand", parent = self.LeftForeArm)
            self.LeftHandThumb1 = DJB_CharacterNode("LeftHandThumb1", optional_ = 1, parent = self.LeftHand)
            self.LeftHandThumb2 = DJB_CharacterNode("LeftHandThumb2", optional_ = 1, parent = self.LeftHandThumb1)
            self.LeftHandThumb3 = DJB_CharacterNode("LeftHandThumb3", optional_ = 1, parent = self.LeftHandThumb2)
            self.LeftHandThumb4 = DJB_CharacterNode("LeftHandThumb4", optional_ = 1, parent = self.LeftHandThumb3)
            self.LeftHandIndex1 = DJB_CharacterNode("LeftHandIndex1", optional_ = 1,parent = self.LeftHand)
            self.LeftHandIndex2 = DJB_CharacterNode("LeftHandIndex2", optional_ = 1, parent = self.LeftHandIndex1)
            self.LeftHandIndex3 = DJB_CharacterNode("LeftHandIndex3", optional_ = 1, parent = self.LeftHandIndex2)
            self.LeftHandIndex4 = DJB_CharacterNode("LeftHandIndex4", optional_ = 1, parent = self.LeftHandIndex3)
            self.LeftHandMiddle1 = DJB_CharacterNode("LeftHandMiddle1", optional_ = 1, parent = self.LeftHand)
            self.LeftHandMiddle2 = DJB_CharacterNode("LeftHandMiddle2", optional_ = 1, parent = self.LeftHandMiddle1)
            self.LeftHandMiddle3 = DJB_CharacterNode("LeftHandMiddle3", optional_ = 1, parent = self.LeftHandMiddle2)
            self.LeftHandMiddle4 = DJB_CharacterNode("LeftHandMiddle4", optional_ = 1, parent = self.LeftHandMiddle3)
            self.LeftHandRing1 = DJB_CharacterNode("LeftHandRing1", optional_ = 1, parent = self.LeftHand)
            self.LeftHandRing2 = DJB_CharacterNode("LeftHandRing2", optional_ = 1, parent = self.LeftHandRing1)
            self.LeftHandRing3 = DJB_CharacterNode("LeftHandRing3", optional_ = 1, parent = self.LeftHandRing2)
            self.LeftHandRing4 = DJB_CharacterNode("LeftHandRing4", optional_ = 1, parent = self.LeftHandRing3)
            self.LeftHandPinky1 = DJB_CharacterNode("LeftHandPinky1", optional_ = 1, parent = self.LeftHand)
            self.LeftHandPinky2 = DJB_CharacterNode("LeftHandPinky2", optional_ = 1, parent = self.LeftHandPinky1)
            self.LeftHandPinky3 = DJB_CharacterNode("LeftHandPinky3", optional_ = 1, parent = self.LeftHandPinky2)
            self.LeftHandPinky4 = DJB_CharacterNode("LeftHandPinky4", optional_ = 1, parent = self.LeftHandPinky3)
            if self.Spine3.Bind_Joint:
                self.RightShoulder = DJB_CharacterNode("RightShoulder", parent = self.Spine3)
            else:
                self.RightShoulder = DJB_CharacterNode("RightShoulder", parent = self.Spine2)
            self.RightArm = DJB_CharacterNode("RightArm", parent = self.RightShoulder)
            self.RightForeArm = DJB_CharacterNode("RightForeArm", parent = self.RightArm)
            self.RightHand = DJB_CharacterNode("RightHand", parent = self.RightForeArm)
            self.RightHandThumb1 = DJB_CharacterNode("RightHandThumb1", optional_ = 1, parent = self.RightHand)
            self.RightHandThumb2 = DJB_CharacterNode("RightHandThumb2", optional_ = 1, parent = self.RightHandThumb1)
            self.RightHandThumb3 = DJB_CharacterNode("RightHandThumb3", optional_ = 1, parent = self.RightHandThumb2)
            self.RightHandThumb4 = DJB_CharacterNode("RightHandThumb4", optional_ = 1, parent = self.RightHandThumb3)
            self.RightHandIndex1 = DJB_CharacterNode("RightHandIndex1", optional_ = 1, parent = self.RightHand)
            self.RightHandIndex2 = DJB_CharacterNode("RightHandIndex2", optional_ = 1, parent = self.RightHandIndex1)
            self.RightHandIndex3 = DJB_CharacterNode("RightHandIndex3", optional_ = 1, parent = self.RightHandIndex2)
            self.RightHandIndex4 = DJB_CharacterNode("RightHandIndex4", optional_ = 1, parent = self.RightHandIndex3)
            self.RightHandMiddle1 = DJB_CharacterNode("RightHandMiddle1", optional_ = 1, parent = self.RightHand)
            self.RightHandMiddle2 = DJB_CharacterNode("RightHandMiddle2", optional_ = 1, parent = self.RightHandMiddle1)
            self.RightHandMiddle3 = DJB_CharacterNode("RightHandMiddle3", optional_ = 1, parent = self.RightHandMiddle2)
            self.RightHandMiddle4 = DJB_CharacterNode("RightHandMiddle4", optional_ = 1, parent = self.RightHandMiddle3)
            self.RightHandRing1 = DJB_CharacterNode("RightHandRing1", optional_ = 1, parent = self.RightHand)
            self.RightHandRing2 = DJB_CharacterNode("RightHandRing2", optional_ = 1, parent = self.RightHandRing1)
            self.RightHandRing3 = DJB_CharacterNode("RightHandRing3", optional_ = 1, parent = self.RightHandRing2)
            self.RightHandRing4 = DJB_CharacterNode("RightHandRing4", optional_ = 1, parent = self.RightHandRing3)
            self.RightHandPinky1 = DJB_CharacterNode("RightHandPinky1", optional_ = 1, parent = self.RightHand)
            self.RightHandPinky2 = DJB_CharacterNode("RightHandPinky2", optional_ = 1, parent = self.RightHandPinky1)
            self.RightHandPinky3 = DJB_CharacterNode("RightHandPinky3", optional_ = 1, parent = self.RightHandPinky2)
            self.RightHandPinky4 = DJB_CharacterNode("RightHandPinky4", optional_ = 1, parent = self.RightHandPinky3)
            self.LeftUpLeg = DJB_CharacterNode("LeftUpLeg", parent = self.Hips)
            self.LeftLeg = DJB_CharacterNode("LeftLeg", parent = self.LeftUpLeg)
            self.LeftFoot = DJB_CharacterNode("LeftFoot", parent = self.LeftLeg)
            self.LeftToeBase = DJB_CharacterNode("LeftToeBase", parent = self.LeftFoot)
            self.LeftToe_End = DJB_CharacterNode("LeftToe_End", parent = self.LeftToeBase, alias_ = ["toe_L", "LeftFootToeBase_End"])
            self.RightUpLeg = DJB_CharacterNode("RightUpLeg", parent = self.Hips)
            self.RightLeg = DJB_CharacterNode("RightLeg", parent = self.RightUpLeg)
            self.RightFoot = DJB_CharacterNode("RightFoot", parent = self.RightLeg)
            self.RightToeBase = DJB_CharacterNode("RightToeBase", parent = self.RightFoot)
            self.RightToe_End = DJB_CharacterNode("RightToe_End", parent = self.RightToeBase, alias_ = ["toe_R", "RightFootToeBase_End"])
            
            #educated guess with 2 samples for rig type
            if mayac.getAttr("%s.jointOrient" % self.LeftUpLeg.Bind_Joint)[0] == (0,0,0) and mayac.getAttr("%s.jointOrient" % self.RightArm.Bind_Joint)[0] == (0,0,0):
                self.rigType = "World"
            else:
                self.rigType = "AutoRig"
            
            
            
        #there is an infoNode for this Character
        else:
            self.characterNameSpace = DJB_findBeforeSeparator(self.infoNode, ':')
            self.jointNamespace = attrToPy("%s.jointNamespace" % (self.infoNode))
            
            self.mesh = attrToPy("%s.mesh" % (self.infoNode))
            self.original_Mesh_Names = attrToPy("%s.original_Mesh_Names" % (self.infoNode))
            self.BoundingBox = attrToPy("%s.BoundingBox" % (self.infoNode))
            self.rigType = attrToPy("%s.rigType" % (self.infoNode))
            #####################
            self.hulaOption = attrToPy("%s.hulaOption" % (self.infoNode))
            
            self.Root = DJB_CharacterNode("Root", infoNode_ = attrToPy("%s.Root" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            if self.hulaOption:
                if not self.Root.Bind_Joint:
                    return None
                self.Hips = DJB_CharacterNode("Hips", parent = self.Root, infoNode_ = attrToPy("%s.Hips" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
                self.Spine = DJB_CharacterNode("Spine", parent = self.Root, infoNode_ = attrToPy("%s.Spine" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            else:
                self.Hips = DJB_CharacterNode("Hips", infoNode_ = attrToPy("%s.Hips" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
                self.Spine = DJB_CharacterNode("Spine", parent = self.Hips, infoNode_ = attrToPy("%s.Spine" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.Spine1 = DJB_CharacterNode("Spine1", parent = self.Spine, infoNode_ = attrToPy("%s.Spine1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.Spine2 = DJB_CharacterNode("Spine2", parent = self.Spine1, infoNode_ = attrToPy("%s.Spine2" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.Spine3 = DJB_CharacterNode("Spine3", parent = self.Spine2, optional_ = 1, infoNode_ = attrToPy("%s.Spine3" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            if self.Spine3.Bind_Joint:
                self.Neck = DJB_CharacterNode("Neck", parent = self.Spine3, infoNode_ = attrToPy("%s.Neck" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            else:
                self.Neck = DJB_CharacterNode("Neck", parent = self.Spine2, infoNode_ = attrToPy("%s.Neck" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.Neck1 = DJB_CharacterNode("Neck1", parent = self.Neck, optional_ = 1, infoNode_ = attrToPy("%s.Neck1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            if self.Neck1.Bind_Joint:
                self.Head = DJB_CharacterNode("Head", parent = self.Neck1, infoNode_ = attrToPy("%s.Head" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            else:
                self.Head = DJB_CharacterNode("Head", parent = self.Neck, infoNode_ = attrToPy("%s.Head" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.HeadTop_End = DJB_CharacterNode("HeadTop_End", parent = self.Head, infoNode_ = attrToPy("%s.HeadTop_End" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            if self.Spine3.Bind_Joint:
                self.LeftShoulder = DJB_CharacterNode("LeftShoulder", parent = self.Spine3, infoNode_ = attrToPy("%s.LeftShoulder" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            else:
                self.LeftShoulder = DJB_CharacterNode("LeftShoulder", parent = self.Spine2, infoNode_ = attrToPy("%s.LeftShoulder" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftArm = DJB_CharacterNode("LeftArm", parent = self.LeftShoulder, infoNode_ = attrToPy("%s.LeftArm" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftForeArm = DJB_CharacterNode("LeftForeArm", parent = self.LeftArm, infoNode_ = attrToPy("%s.LeftForeArm" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHand = DJB_CharacterNode("LeftHand", parent = self.LeftForeArm, infoNode_ = attrToPy("%s.LeftHand" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandThumb1 = DJB_CharacterNode("LeftHandThumb1", optional_ = 1, parent = self.LeftHand, infoNode_ = attrToPy("%s.LeftHandThumb1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandThumb2 = DJB_CharacterNode("LeftHandThumb2", optional_ = 1, parent = self.LeftHandThumb1, infoNode_ = attrToPy("%s.LeftHandThumb2" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandThumb3 = DJB_CharacterNode("LeftHandThumb3", optional_ = 1, parent = self.LeftHandThumb2, infoNode_ = attrToPy("%s.LeftHandThumb3" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandThumb4 = DJB_CharacterNode("LeftHandThumb4", optional_ = 1, parent = self.LeftHandThumb3, infoNode_ = attrToPy("%s.LeftHandThumb4" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandIndex1 = DJB_CharacterNode("LeftHandIndex1", optional_ = 1, parent = self.LeftHand, infoNode_ = attrToPy("%s.LeftHandIndex1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandIndex2 = DJB_CharacterNode("LeftHandIndex2", optional_ = 1, parent = self.LeftHandIndex1, infoNode_ = attrToPy("%s.LeftHandIndex2" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandIndex3 = DJB_CharacterNode("LeftHandIndex3", optional_ = 1, parent = self.LeftHandIndex2, infoNode_ = attrToPy("%s.LeftHandIndex3" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandIndex4 = DJB_CharacterNode("LeftHandIndex4", optional_ = 1, parent = self.LeftHandIndex3, infoNode_ = attrToPy("%s.LeftHandIndex4" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandMiddle1 = DJB_CharacterNode("LeftHandMiddle1", optional_ = 1, parent = self.LeftHand, infoNode_ = attrToPy("%s.LeftHandMiddle1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandMiddle2 = DJB_CharacterNode("LeftHandMiddle2", optional_ = 1, parent = self.LeftHandMiddle1, infoNode_ = attrToPy("%s.LeftHandMiddle2" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandMiddle3 = DJB_CharacterNode("LeftHandMiddle3", optional_ = 1, parent = self.LeftHandMiddle2, infoNode_ = attrToPy("%s.LeftHandMiddle3" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandMiddle4 = DJB_CharacterNode("LeftHandMiddle4", optional_ = 1, parent = self.LeftHandMiddle3, infoNode_ = attrToPy("%s.LeftHandMiddle4" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandRing1 = DJB_CharacterNode("LeftHandRing1", optional_ = 1, parent = self.LeftHand, infoNode_ = attrToPy("%s.LeftHandRing1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandRing2 = DJB_CharacterNode("LeftHandRing2", optional_ = 1, parent = self.LeftHandRing1, infoNode_ = attrToPy("%s.LeftHandRing2" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandRing3 = DJB_CharacterNode("LeftHandRing3", optional_ = 1, parent = self.LeftHandRing2, infoNode_ = attrToPy("%s.LeftHandRing3" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandRing4 = DJB_CharacterNode("LeftHandRing4", optional_ = 1, parent = self.LeftHandRing3, infoNode_ = attrToPy("%s.LeftHandRing4" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandPinky1 = DJB_CharacterNode("LeftHandPinky1", optional_ = 1, parent = self.LeftHand, infoNode_ = attrToPy("%s.LeftHandPinky1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandPinky2 = DJB_CharacterNode("LeftHandPinky2", optional_ = 1, parent = self.LeftHandPinky1, infoNode_ = attrToPy("%s.LeftHandPinky2" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandPinky3 = DJB_CharacterNode("LeftHandPinky3", optional_ = 1, parent = self.LeftHandPinky2, infoNode_ = attrToPy("%s.LeftHandPinky3" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftHandPinky4 = DJB_CharacterNode("LeftHandPinky4", optional_ = 1, parent = self.LeftHandPinky3, infoNode_ = attrToPy("%s.LeftHandPinky4" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            if self.Spine3.Bind_Joint:
                self.RightShoulder = DJB_CharacterNode("RightShoulder", parent = self.Spine3, infoNode_ = attrToPy("%s.RightShoulder" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            else:
                self.RightShoulder = DJB_CharacterNode("RightShoulder", parent = self.Spine2, infoNode_ = attrToPy("%s.RightShoulder" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightArm = DJB_CharacterNode("RightArm", parent = self.RightShoulder, infoNode_ = attrToPy("%s.RightArm" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightForeArm = DJB_CharacterNode("RightForeArm", parent = self.RightArm, infoNode_ = attrToPy("%s.RightForeArm" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHand = DJB_CharacterNode("RightHand", parent = self.RightForeArm, infoNode_ = attrToPy("%s.RightHand" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandThumb1 = DJB_CharacterNode("RightHandThumb1", optional_ = 1, parent = self.RightHand, infoNode_ = attrToPy("%s.RightHandThumb1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandThumb2 = DJB_CharacterNode("RightHandThumb2", optional_ = 1, parent = self.RightHandThumb1, infoNode_ = attrToPy("%s.RightHandThumb2" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandThumb3 = DJB_CharacterNode("RightHandThumb3", optional_ = 1, parent = self.RightHandThumb2, infoNode_ = attrToPy("%s.RightHandThumb3" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandThumb4 = DJB_CharacterNode("RightHandThumb4", optional_ = 1, parent = self.RightHandThumb3, infoNode_ = attrToPy("%s.RightHandThumb4" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandIndex1 = DJB_CharacterNode("RightHandIndex1", optional_ = 1, parent = self.RightHand, infoNode_ = attrToPy("%s.RightHandIndex1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandIndex2 = DJB_CharacterNode("RightHandIndex2", optional_ = 1, parent = self.RightHandIndex1, infoNode_ = attrToPy("%s.RightHandIndex2" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandIndex3 = DJB_CharacterNode("RightHandIndex3", optional_ = 1, parent = self.RightHandIndex2, infoNode_ = attrToPy("%s.RightHandIndex3" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandIndex4 = DJB_CharacterNode("RightHandIndex4", optional_ = 1, parent = self.RightHandIndex3, infoNode_ = attrToPy("%s.RightHandIndex4" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandMiddle1 = DJB_CharacterNode("RightHandMiddle1", optional_ = 1, parent = self.RightHand, infoNode_ = attrToPy("%s.RightHandMiddle1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandMiddle2 = DJB_CharacterNode("RightHandMiddle2", optional_ = 1, parent = self.RightHandMiddle1, infoNode_ = attrToPy("%s.RightHandMiddle2" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandMiddle3 = DJB_CharacterNode("RightHandMiddle3", optional_ = 1, parent = self.RightHandMiddle2, infoNode_ = attrToPy("%s.RightHandMiddle3" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandMiddle4 = DJB_CharacterNode("RightHandMiddle4", optional_ = 1, parent = self.RightHandMiddle3, infoNode_ = attrToPy("%s.RightHandMiddle4" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandRing1 = DJB_CharacterNode("RightHandRing1", optional_ = 1, parent = self.RightHand, infoNode_ = attrToPy("%s.RightHandRing1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandRing2 = DJB_CharacterNode("RightHandRing2", optional_ = 1, parent = self.RightHandRing1, infoNode_ = attrToPy("%s.RightHandRing2" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandRing3 = DJB_CharacterNode("RightHandRing3", optional_ = 1, parent = self.RightHandRing2, infoNode_ = attrToPy("%s.RightHandRing3" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandRing4 = DJB_CharacterNode("RightHandRing4", optional_ = 1, parent = self.RightHandRing3, infoNode_ = attrToPy("%s.RightHandRing4" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandPinky1 = DJB_CharacterNode("RightHandPinky1", optional_ = 1, parent = self.RightHand, infoNode_ = attrToPy("%s.RightHandPinky1" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandPinky2 = DJB_CharacterNode("RightHandPinky2", optional_ = 1, parent = self.RightHandPinky1, infoNode_ = attrToPy("%s.RightHandPinky2" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandPinky3 = DJB_CharacterNode("RightHandPinky3", optional_ = 1, parent = self.RightHandPinky2, infoNode_ = attrToPy("%s.RightHandPinky3" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightHandPinky4 = DJB_CharacterNode("RightHandPinky4", optional_ = 1, parent = self.RightHandPinky3, infoNode_ = attrToPy("%s.RightHandPinky4" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftUpLeg = DJB_CharacterNode("LeftUpLeg", parent = self.Hips, infoNode_ = attrToPy("%s.LeftUpLeg" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftLeg = DJB_CharacterNode("LeftLeg", parent = self.LeftUpLeg, infoNode_ = attrToPy("%s.LeftLeg" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftFoot = DJB_CharacterNode("LeftFoot", parent = self.LeftLeg, infoNode_ = attrToPy("%s.LeftFoot" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftToeBase = DJB_CharacterNode("LeftToeBase", parent = self.LeftFoot, infoNode_ = attrToPy("%s.LeftToeBase" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.LeftToe_End = DJB_CharacterNode("LeftToe_End", parent = self.LeftToeBase, infoNode_ = attrToPy("%s.LeftToe_End" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightUpLeg = DJB_CharacterNode("RightUpLeg", parent = self.Hips, infoNode_ = attrToPy("%s.RightUpLeg" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightLeg = DJB_CharacterNode("RightLeg", parent = self.RightUpLeg, infoNode_ = attrToPy("%s.RightLeg" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightFoot = DJB_CharacterNode("RightFoot", parent = self.RightLeg, infoNode_ = attrToPy("%s.RightFoot" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightToeBase = DJB_CharacterNode("RightToeBase", parent = self.RightFoot, infoNode_ = attrToPy("%s.RightToeBase" % (self.infoNode)), nameSpace_ = self.characterNameSpace)
            self.RightToe_End = DJB_CharacterNode("RightToe_End", parent = self.RightToeBase, infoNode_ = attrToPy("%s.RightToe_End" % (self.infoNode)), nameSpace_ = self.characterNameSpace)

            ##############################################
            self.proportions = attrToPy("%s.proportions" % (self.infoNode))
            self.defaultControlScale = attrToPy("%s.defaultControlScale" % (self.infoNode))
            self.Character_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Character_GRP" % (self.infoNode)))
            self.global_CTRL = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.global_CTRL" % (self.infoNode)))
            self.CTRL_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.CTRL_GRP" % (self.infoNode)))
            self.Joint_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Joint_GRP" % (self.infoNode)))
            self.AnimData_Joint_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.AnimData_Joint_GRP" % (self.infoNode)))
            self.Bind_Joint_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Bind_Joint_GRP" % (self.infoNode)))
            self.Mesh_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Mesh_GRP" % (self.infoNode)))
            self.Misc_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Misc_GRP" % (self.infoNode)))
            self.LeftArm_Switch_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Misc_GRP" % (self.infoNode)))
            self.RightArm_Switch_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightArm_Switch_Reverse" % (self.infoNode)))
            self.LeftLeg_Switch_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.LeftLeg_Switch_Reverse" % (self.infoNode)))
            self.RightLeg_Switch_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightLeg_Switch_Reverse" % (self.infoNode)))
            self.Bind_Joint_SelectSet = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Bind_Joint_SelectSet" % (self.infoNode)))
            self.AnimData_Joint_SelectSet = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.AnimData_Joint_SelectSet" % (self.infoNode)))
            self.Controls_SelectSet = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Controls_SelectSet" % (self.infoNode)))
            self.Geo_SelectSet = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Geo_SelectSet" % (self.infoNode)))
            self.Left_Toe_IK_AnimData_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Left_Toe_IK_AnimData_GRP" % (self.infoNode)))
            self.Left_Toe_IK_CTRL = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Left_Toe_IK_CTRL" % (self.infoNode)))
            self.Left_ToeBase_IK_AnimData_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Left_ToeBase_IK_AnimData_GRP" % (self.infoNode)))
            self.Left_IK_ToeBase_animData_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Left_IK_ToeBase_animData_MultNode" % (self.infoNode)))
            self.Left_ToeBase_IK_CTRL = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Left_ToeBase_IK_CTRL" % (self.infoNode)))
            self.Left_Ankle_IK_AnimData_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Left_Ankle_IK_AnimData_GRP" % (self.infoNode)))
            self.Left_Ankle_IK_CTRL = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Left_Ankle_IK_CTRL" % (self.infoNode)))
            self.Left_ToeBase_IkHandle = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Left_ToeBase_IkHandle" % (self.infoNode)))
            self.Left_ToeEnd_IkHandle = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Left_ToeEnd_IkHandle" % (self.infoNode)))
            self.Right_Toe_IK_AnimData_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Right_Toe_IK_AnimData_GRP" % (self.infoNode)))
            self.Right_Toe_IK_CTRL = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Right_Toe_IK_CTRL" % (self.infoNode)))
            self.Right_ToeBase_IK_AnimData_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Right_ToeBase_IK_AnimData_GRP" % (self.infoNode)))
            self.Right_IK_ToeBase_animData_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Right_IK_ToeBase_animData_MultNode" % (self.infoNode)))
            self.Right_ToeBase_IK_CTRL = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Right_ToeBase_IK_CTRL" % (self.infoNode)))
            self.Right_Ankle_IK_AnimData_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Right_Ankle_IK_AnimData_GRP" % (self.infoNode)))
            self.Right_Ankle_IK_CTRL = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Right_Ankle_IK_AnimData_GRP" % (self.infoNode)))
            self.Right_ToeBase_IkHandle = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Right_ToeBase_IkHandle" % (self.infoNode)))
            self.Right_ToeEnd_IkHandle = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Right_ToeEnd_IkHandle" % (self.infoNode)))
            self.LeftHand_CTRLs_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.LeftHand_CTRLs_GRP" % (self.infoNode)))
            self.RightHand_CTRLs_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightHand_CTRLs_GRP" % (self.infoNode)))
            self.LeftFoot_FootRoll_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.LeftFoot_FootRoll_MultNode" % (self.infoNode)))
            self.LeftFoot_ToeRoll_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.LeftFoot_ToeRoll_MultNode" % (self.infoNode)))
            self.RightFoot_FootRoll_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightFoot_FootRoll_MultNode" % (self.infoNode)))
            self.RightFoot_ToeRoll_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightFoot_ToeRoll_MultNode" % (self.infoNode)))
            self.RightFoot_HipPivot_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightFoot_HipPivot_MultNode" % (self.infoNode)))
            self.RightFoot_BallPivot_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightFoot_BallPivot_MultNode" % (self.infoNode)))
            self.RightFoot_ToePivot_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightFoot_ToePivot_MultNode" % (self.infoNode)))
            self.RightFoot_HipSideToSide_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightFoot_HipSideToSide_MultNode" % (self.infoNode)))
            self.RightFoot_ToeRotate_MultNode = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightFoot_ToeRotate_MultNode" % (self.infoNode)))
            self.IK_Dummy_Joint_GRP = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.IK_Dummy_Joint_GRP" % (self.infoNode)))
            self.LeftHand_grandparent_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.LeftHand_grandparent_Constraint" % (self.infoNode)))
            self.LeftHand_grandparent_Constraint_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.LeftHand_grandparent_Constraint_Reverse" % (self.infoNode)))
            self.RightHand_grandparent_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightHand_grandparent_Constraint" % (self.infoNode)))
            self.RightHand_grandparent_Constraint_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightHand_grandparent_Constraint_Reverse" % (self.infoNode)))
            self.LeftForeArm_grandparent_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.LeftForeArm_grandparent_Constraint" % (self.infoNode)))
            self.LeftForeArm_grandparent_Constraint_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.LeftForeArm_grandparent_Constraint_Reverse" % (self.infoNode)))
            self.RightForeArm_grandparent_Constraint = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightForeArm_grandparent_Constraint" % (self.infoNode)))
            self.RightForeArm_grandparent_Constraint_Reverse = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.RightForeArm_grandparent_Constraint_Reverse" % (self.infoNode)))
            self.exportList = attrToPy("%s.exportList" % (self.infoNode))
            
            if attrToPy("%s.origAnim" % (self.infoNode)):
                if mayac.objExists(DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.origAnim" % (self.infoNode)))):
                    self.origAnim = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.origAnim" % (self.infoNode)))
                    self.origAnimation_Layer = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.origAnimation_Layer" % (self.infoNode)))
                else:
                    self.origAnim = attrToPy("%s.origAnim" % (self.infoNode))
                    self.origAnimation_Layer = attrToPy("%s.origAnimation_Layer" % (self.infoNode))
            self.Mesh_Layer = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Mesh_Layer" % (self.infoNode)))
            self.Bind_Joint_Layer = DJB_addNameSpace(self.characterNameSpace, attrToPy("%s.Bind_Joint_Layer" % (self.infoNode)))
            
            
            
            
            
            
        
        
           
        self.bodyParts = []
        for bodyPart in (self.Root, self.Hips, self.Spine, self.Spine1, self.Spine2, self.Spine3, self.Neck, self.Neck1, self.Head, self.HeadTop_End, self.LeftShoulder, 
                              self.LeftArm, self.LeftForeArm, self.LeftHand, self.LeftHandThumb1, self.LeftHandThumb2, self.LeftHandThumb3, 
                              self.LeftHandThumb4, self.LeftHandIndex1, self.LeftHandIndex2, self.LeftHandIndex3, self.LeftHandIndex4,
                              self.LeftHandMiddle1, self.LeftHandMiddle2, self.LeftHandMiddle3, self.LeftHandMiddle4, self.LeftHandRing1,
                              self.LeftHandRing2, self.LeftHandRing3, self.LeftHandRing4, self.LeftHandPinky1, self.LeftHandPinky2, 
                              self.LeftHandPinky3, self.LeftHandPinky4, self.RightShoulder, self.RightArm, self.RightForeArm, 
                              self.RightHand, self.RightHandThumb1, self.RightHandThumb2, self.RightHandThumb3, 
                              self.RightHandThumb4, self.RightHandIndex1, self.RightHandIndex2, self.RightHandIndex3, self.RightHandIndex4,
                              self.RightHandMiddle1, self.RightHandMiddle2, self.RightHandMiddle3, self.RightHandMiddle4, self.RightHandRing1,
                              self.RightHandRing2, self.RightHandRing3, self.RightHandRing4, self.RightHandPinky1, self.RightHandPinky2, 
                              self.RightHandPinky3, self.RightHandPinky4, self.LeftUpLeg, self.LeftLeg, self.LeftFoot, self.LeftToeBase,
                              self.LeftToe_End, self.RightUpLeg, self.RightLeg, self.RightFoot, self.RightToeBase, self.RightToe_End):
            if bodyPart.Bind_Joint:
                self.bodyParts.append(bodyPart)
        
        
        
        mayac.select(clear = True)
        

    
    def fixArmsAndLegs(self):
        LAnklePosStart = mayac.xform(self.LeftFoot.Bind_Joint, query = True, worldSpace = True, absolute = True, translation = True)
        RAnklePosStart = mayac.xform(self.RightFoot.Bind_Joint, query = True, worldSpace = True, absolute = True, translation = True)
        
        if self.rigType == "World":
            value = -1
            while not DJB_CheckAngle(self.LeftUpLeg.Bind_Joint, self.LeftLeg.Bind_Joint, self.LeftFoot.Bind_Joint, axis = "x", multiplier = -1):
                mayac.rotate(value, 0, 0, self.LeftUpLeg.Bind_Joint, relative = True)
                mayac.rotate(value*-1, 0, 0, self.LeftLeg.Bind_Joint, relative = True)
                mayac.refresh()
            mayac.rotate(-45, 0, 0, self.LeftUpLeg.Bind_Joint, relative = True)
            mayac.rotate(90, 0, 0, self.LeftLeg.Bind_Joint, relative = True)
            mayac.joint(self.LeftUpLeg.Bind_Joint, edit = True, setPreferredAngles=True, children=True)
            mayac.rotate(45, 0, 0, self.LeftUpLeg.Bind_Joint, relative = True)
            mayac.rotate(-90, 0, 0, self.LeftLeg.Bind_Joint, relative = True)
              
            value = -1
            while not DJB_CheckAngle(self.RightUpLeg.Bind_Joint, self.RightLeg.Bind_Joint, self.RightFoot.Bind_Joint, axis = "x", multiplier = -1):
                mayac.rotate(value, 0, 0, self.RightUpLeg.Bind_Joint, relative = True)
                mayac.rotate(value*-1, 0, 0, self.RightLeg.Bind_Joint, relative = True)
                mayac.refresh()
            mayac.rotate(-45, 0, 0, self.RightUpLeg.Bind_Joint, relative = True)
            mayac.rotate(90, 0, 0, self.RightLeg.Bind_Joint, relative = True)
            mayac.joint( self.RightUpLeg.Bind_Joint, edit = True, setPreferredAngles=True, children=True)
            mayac.rotate(45, 0, 0, self.RightUpLeg.Bind_Joint, relative = True)
            mayac.rotate(-90, 0, 0, self.RightLeg.Bind_Joint, relative = True)
            
            value = -1
            while not DJB_CheckAngle(self.LeftArm.Bind_Joint, self.LeftForeArm.Bind_Joint, self.LeftHand.Bind_Joint, axis = "y", multiplier = 1):
                mayac.rotate(0, value, 0, self.LeftForeArm.Bind_Joint, relative = True)
                mayac.refresh()
            tempRotData = mayac.getAttr("%s.rotate" %(self.LeftArm.Bind_Joint))
            mayac.rotate(0, 0, 0, self.LeftArm.Bind_Joint, absolute = True)
            mayac.rotate(0, -90, 0, self.LeftForeArm.Bind_Joint, relative = True)
            mayac.joint( self.LeftArm.Bind_Joint, edit = True, setPreferredAngles=True, children=True)
            mayac.setAttr("%s.rotate" %(self.LeftArm.Bind_Joint), tempRotData[0][0], tempRotData[0][1], tempRotData[0][2], type = "double3")
            mayac.rotate(0, 90, 0, self.LeftForeArm.Bind_Joint, relative = True)
                
            value = 1
            while not DJB_CheckAngle(self.RightArm.Bind_Joint, self.RightForeArm.Bind_Joint, self.RightHand.Bind_Joint, axis = "y", multiplier = -1):
                mayac.rotate(0, value, 0, self.RightForeArm.Bind_Joint, relative = True)
                mayac.refresh()
            tempRotData = mayac.getAttr("%s.rotate" %(self.RightArm.Bind_Joint))
            mayac.rotate(0, 0, 0, self.RightArm.Bind_Joint, absolute = True)
            mayac.rotate(0, 90, 0, self.RightForeArm.Bind_Joint, relative = True)
            mayac.joint( self.RightArm.Bind_Joint, edit = True, setPreferredAngles=True, children=True)
            mayac.setAttr("%s.rotate" %(self.RightArm.Bind_Joint), tempRotData[0][0], tempRotData[0][1], tempRotData[0][2], type = "double3")
            mayac.rotate(0, -90, 0, self.RightForeArm.Bind_Joint, relative = True)
        
        elif self.rigType =="AutoRig":
            value = 1
            while not DJB_CheckAngle(self.LeftUpLeg.Bind_Joint, self.LeftLeg.Bind_Joint, self.LeftFoot.Bind_Joint, axis = "x", multiplier = 1):
                mayac.rotate(value, 0, 0, self.LeftUpLeg.Bind_Joint, relative = True)
                mayac.rotate(value*-1, 0, 0, self.LeftLeg.Bind_Joint, relative = True)
                mayac.refresh()
            mayac.rotate(45, 0, 0, self.LeftUpLeg.Bind_Joint, relative = True)
            mayac.rotate(-90, 0, 0, self.LeftLeg.Bind_Joint, relative = True)
            mayac.joint(self.LeftUpLeg.Bind_Joint, edit = True, setPreferredAngles=True, children=True)
            mayac.rotate(-45, 0, 0, self.LeftUpLeg.Bind_Joint, relative = True)
            mayac.rotate(90, 0, 0, self.LeftLeg.Bind_Joint, relative = True)
              
            value = 1
            while not DJB_CheckAngle(self.RightUpLeg.Bind_Joint, self.RightLeg.Bind_Joint, self.RightFoot.Bind_Joint, axis = "x", multiplier = 1):
                mayac.rotate(value, 0, 0, self.RightUpLeg.Bind_Joint, relative = True)
                mayac.rotate(value*-1, 0, 0, self.RightLeg.Bind_Joint, relative = True)
                mayac.refresh()
            mayac.rotate(45, 0, 0, self.RightUpLeg.Bind_Joint, relative = True)
            mayac.rotate(-90, 0, 0, self.RightLeg.Bind_Joint, relative = True)
            mayac.joint( self.RightUpLeg.Bind_Joint, edit = True, setPreferredAngles=True, children=True)
            mayac.rotate(-45, 0, 0, self.RightUpLeg.Bind_Joint, relative = True)
            mayac.rotate(90, 0, 0, self.RightLeg.Bind_Joint, relative = True)
            
            value = 1
            while not DJB_CheckAngle(self.LeftArm.Bind_Joint, self.LeftForeArm.Bind_Joint, self.LeftHand.Bind_Joint, axis = "z", multiplier = -1):
                mayac.rotate(0, 0, value, self.LeftForeArm.Bind_Joint, relative = True)
                mayac.refresh()
            tempRotData = mayac.getAttr("%s.rotate" %(self.LeftArm.Bind_Joint))
            mayac.rotate(0, 0, 0, self.LeftArm.Bind_Joint, absolute = True)
            mayac.rotate(0, 0, 90, self.LeftForeArm.Bind_Joint, relative = True)
            mayac.joint( self.LeftArm.Bind_Joint, edit = True, setPreferredAngles=True, children=True)
            mayac.setAttr("%s.rotate" %(self.LeftArm.Bind_Joint), tempRotData[0][0], tempRotData[0][1], tempRotData[0][2], type = "double3")
            mayac.rotate(0, 0, -90, self.LeftForeArm.Bind_Joint, relative = True)
                
            value = -1
            while not DJB_CheckAngle(self.RightArm.Bind_Joint, self.RightForeArm.Bind_Joint, self.RightHand.Bind_Joint, axis = "z", multiplier = 1):
                mayac.rotate(0, 0, value, self.RightForeArm.Bind_Joint, relative = True)
                mayac.refresh()
            tempRotData = mayac.getAttr("%s.rotate" %(self.RightArm.Bind_Joint))
            mayac.rotate(0, 0, 0, self.RightArm.Bind_Joint, absolute = True)
            mayac.rotate(0, 0, -90, self.RightForeArm.Bind_Joint, relative = True)
            mayac.joint( self.RightArm.Bind_Joint, edit = True, setPreferredAngles=True, children=True)
            mayac.setAttr("%s.rotate" %(self.RightArm.Bind_Joint), tempRotData[0][0], tempRotData[0][1], tempRotData[0][2], type = "double3")
            mayac.rotate(0, 0, 90, self.RightForeArm.Bind_Joint, relative = True)
        
        LAnklePosEnd = mayac.xform(self.LeftFoot.Bind_Joint, query = True, worldSpace = True, absolute = True, translation = True)
        RAnklePosEnd = mayac.xform(self.RightFoot.Bind_Joint, query = True, worldSpace = True, absolute = True, translation = True)
        AvgDiff = (LAnklePosStart[1]-LAnklePosEnd[1] + RAnklePosStart[1] - RAnklePosEnd[1]) / 2
        
        if self.hulaOption:
            mayac.move(0,AvgDiff,0, self.Root.Bind_Joint, relative = True)
        else:
            mayac.move(0,AvgDiff,0, self.Hips.Bind_Joint, relative = True)
        
        
        
    def makeAnimDataJoints(self):
        for bodyPart in self.bodyParts:
            bodyPart.duplicateJoint("AnimData")
        mayac.select(clear = True)
        
        #IK dummy joints
        if self.Root.Bind_Joint:
            self.Root.duplicateJoint("IK_Dummy")
        self.Hips.duplicateJoint("IK_Dummy")
        self.Spine.duplicateJoint("IK_Dummy")
        self.Spine1.duplicateJoint("IK_Dummy")
        self.Spine2.duplicateJoint("IK_Dummy")
        if self.Spine3.Bind_Joint:
            self.Spine3.duplicateJoint("IK_Dummy")
        self.LeftShoulder.duplicateJoint("IK_Dummy")
        self.RightShoulder.duplicateJoint("IK_Dummy")
            
    def makeControls(self, estimateSize = True):
    
        if len(self.mesh):
            bbox = self.BoundingBox
            
            self.proportions["highPoint"] = bbox[4]
            self.proportions["lowPoint"] = bbox[1]
            self.proportions["height"] = bbox[4]-bbox[1]
            self.proportions["front"] = bbox[5]
            self.proportions["back"] = bbox[2]
            self.proportions["depth"] = bbox[5]-bbox[2]
            self.proportions["depthMidpoint"] = ((bbox[5]-bbox[2])/2) + bbox[2]
            self.proportions["left"] = bbox[0]
            self.proportions["right"] = bbox[3]
            self.proportions["width"] = bbox[3]-bbox[0]
            self.proportions["widthMidpoint"] = ((bbox[3]-bbox[0])/2) + bbox[0]
            
        #global   
        temp = mayac.circle(
                        radius = (self.proportions["width"]+self.proportions["depth"])*.35,
                        constructionHistory = False,
                        name = "global_CTRL")
        self.global_CTRL = temp[0]
        mayac.move(self.proportions["widthMidpoint"], self.proportions["lowPoint"], self.proportions["depthMidpoint"], absolute = True, worldSpace = True)
        mayac.rotate(90,0,0, self.global_CTRL)
        DJB_cleanGEO(self.global_CTRL)
        DJB_ChangeDisplayColor(self.global_CTRL)
        
        
        
        if self.rigType == "AutoRig":  
            #root
            if self.Root.Bind_Joint:
                self.Root.createControl(type = "normal", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.8, self.proportions["depth"]*0.8, self.proportions["depth"]*0.8), 
                                    offset = (0,0,0), 
                                    estimateSize = estimateSize)
            
                #hips
                self.Hips.createControl(type = "normal", 
                                        style = "hula", 
                                        scale = (self.proportions["depth"]*0.75, self.proportions["depth"]*0.75, self.proportions["depth"]*0.75),
                                        offset = (0,-.01*self.proportions["height"],0), 
                                        estimateSize = estimateSize,
                                        color_ = "yellow")
            else:
                #hips
                self.Hips.createControl(type = "normal", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.8, self.proportions["depth"]*0.8, self.proportions["depth"]*0.8), 
                                    offset = (0,0,0), 
                                    estimateSize = estimateSize)
            #spine
            self.Spine.createControl(type = "normal", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.7, self.proportions["depth"]*0.7, self.proportions["depth"]*0.7),
                                    offset = (0,0,self.proportions["depth"]*0.1), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
            
            #spine1
            self.Spine1.createControl(type = "normal", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.6, self.proportions["depth"]*0.6, self.proportions["depth"]*0.6),
                                    offset = (0,0,self.proportions["depth"]*0.15), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
            #spine2
            if self.Spine3.Bind_Joint:
                self.Spine2.createControl(type = "normal", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.6, self.proportions["depth"]*0.6, self.proportions["depth"]*0.6),
                                    offset = (0,0,self.proportions["depth"]*0.15), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
                self.Spine3.createControl(type = "normal", 
                                    style = "box", 
                                    scale = (self.proportions["depth"]*0.7, self.proportions["depth"]*0.7, (self.proportions["depth"])*0.8), 
                                    offset = (0,self.proportions["depth"]*.2,self.proportions["depth"]*0.1), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
            else:
                self.Spine2.createControl(type = "normal", 
                                    style = "box", 
                                    scale = (self.proportions["depth"]*0.7, self.proportions["depth"]*0.7, (self.proportions["depth"])*0.8), 
                                    offset = (0,self.proportions["depth"]*.2,self.proportions["depth"]*0.1), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
                                    
            #neck
            self.Neck.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*-0.18, self.proportions["depth"]*0.18, self.proportions["depth"]*0.18),
                                    offset = (self.proportions["height"]*0.033, 0, self.proportions["height"]*-0.04),  
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
            if self.Neck1.Bind_Joint:
                self.Neck1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*-0.18, self.proportions["depth"]*0.18, self.proportions["depth"]*0.18),
                                    offset = (self.proportions["height"]*0.033, 0, self.proportions["height"]*-0.04),  
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
                                    
            #head
            self.Head.createControl(type = "normal", 
                                    style = "box", 
                                    scale = (self.proportions["depth"]*0.4, self.proportions["height"]*0.13, (self.proportions["depth"])*0.5), 
                                    offset = (0,self.proportions["height"]*.08,self.proportions["depth"]*0.1), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
                              
            #LeftShoulder
            self.LeftShoulder.createControl(type = "normal", 
                                    style = "circleWrapped", 
                                    scale = (self.proportions["depth"]*0.4, self.proportions["depth"]*0.15, self.proportions["depth"]*0.15), 
                                    offset = (0,self.proportions["depth"]*0.3,self.proportions["height"]*-0.04),  
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
                                    
            #RightShoulder
            self.RightShoulder.createControl(type = "normal", 
                                    style = "circleWrapped", 
                                    scale = (self.proportions["depth"]*0.4, self.proportions["depth"]*0.15, self.proportions["depth"]*0.15), 
                                    offset = (0,self.proportions["depth"]*0.3,self.proportions["height"]*-0.04),  
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            #LeftArm
            self.LeftArm.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.25, self.proportions["depth"]*0.25, self.proportions["depth"]*0.25),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
            
            #RightArm
            self.RightArm.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.25, self.proportions["depth"]*0.25, self.proportions["depth"]*0.25),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            #LeftForeArm
            self.LeftForeArm.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.25, self.proportions["depth"]*0.25, self.proportions["depth"]*0.25),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
            
            self.LeftForeArm.createControl(type = "IK", 
                                    style = "PoleVector", 
                                    scale = (self.proportions["depth"]*0.1, self.proportions["depth"]*0.2, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0),
                                    rotate = (0, 90, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            
            #RightForeArm
            self.RightForeArm.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.25, self.proportions["depth"]*0.25, self.proportions["depth"]*0.25),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            self.RightForeArm.createControl(type = "IK", 
                                    style = "PoleVector", 
                                    scale = (self.proportions["depth"]*0.1, self.proportions["depth"]*0.2, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0),  
                                    rotate = (0, -90, 0),
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            
            #LeftHand
            self.LeftHand.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.2, self.proportions["depth"]*0.2, self.proportions["depth"]*0.2),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
            
            self.LeftHand.createControl(type = "IK", 
                                    style = "box", 
                                    scale = (self.proportions["depth"]*0.2, self.proportions["depth"]*0.3, self.proportions["depth"]*0.2),
                                    offset = (0, self.proportions["depth"]*0.3, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            
            #RightHand
            self.RightHand.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.2, self.proportions["depth"]*0.2, self.proportions["depth"]*0.2),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            self.RightHand.createControl(type = "IK", 
                                    style = "box", 
                                    scale = (self.proportions["depth"]*0.2, self.proportions["depth"]*0.3, self.proportions["depth"]*0.2),
                                    offset = (0, self.proportions["depth"]*0.3, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                                    
                                    
            #LeftUpLeg
            self.LeftUpLeg.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*0.1, self.proportions["depth"]*0.1, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
                                    
            #LeftLeg
            self.LeftLeg.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*0.09, self.proportions["depth"]*0.09, self.proportions["depth"]*0.09),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
                                    
            self.LeftLeg.createControl(type = "IK", 
                                    style = "PoleVector", 
                                    scale = (self.proportions["depth"]*0.1, self.proportions["depth"]*0.2, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            
            #LeftFoot
            self.LeftFoot.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*0.08, self.proportions["depth"]*0.08, self.proportions["depth"]*0.08),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
            
            self.LeftFoot.createControl(type = "IK", 
                                    style = "footBox", 
                                    scale = (self.proportions["depth"]*0.4, self.proportions["depth"]*0.7, self.proportions["depth"]*-0.4),
                                    offset = (0, self.proportions["depth"]*0.1, self.proportions["depth"]*0.1),
                                    rotate = (90, 0, 0),  
                                    partialConstraint = 1,
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            mayac.move(self.proportions["lowPoint"], "%s.scalePivot" % (self.LeftFoot.IK_CTRL),  "%s.rotatePivot" % (self.LeftFoot.IK_CTRL),  y = True)
    
            #LeftToeBase
            self.LeftToeBase.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*0.07, self.proportions["depth"]*0.07, self.proportions["depth"]*0.07),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
                                    
                                    
            #RightUpLeg
            self.RightUpLeg.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*-0.1, self.proportions["depth"]*0.1, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red1")
                                    
            #RightLeg
            self.RightLeg.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*-0.09, self.proportions["depth"]*0.09, self.proportions["depth"]*0.09),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            self.RightLeg.createControl(type = "IK", 
                                    style = "PoleVector", 
                                    scale = (self.proportions["depth"]*0.1, self.proportions["depth"]*0.2, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                                    
            #RightFoot
            self.RightFoot.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*-0.08, self.proportions["depth"]*0.08, self.proportions["depth"]*0.08),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            self.RightFoot.createControl(type = "IK", 
                                    style = "footBox", 
                                    scale = (self.proportions["depth"]*0.4, self.proportions["depth"]*0.7, self.proportions["depth"]*-0.4),
                                    offset = (0, self.proportions["depth"]*0.1, self.proportions["depth"]*0.1),
                                    rotate = (90, 0, 0),
                                    partialConstraint = 1,  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            mayac.move(self.proportions["lowPoint"], "%s.scalePivot" % (self.RightFoot.IK_CTRL),  "%s.rotatePivot" % (self.RightFoot.IK_CTRL),  y = True)
    
            #RightToeBase
            self.RightToeBase.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*-0.07, self.proportions["depth"]*0.07, self.proportions["depth"]*0.07),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            #fingers
            if self.LeftHandThumb1.Bind_Joint:
                self.LeftHandThumb1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandThumb2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandThumb3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            if self.LeftHandIndex1.Bind_Joint:
                self.LeftHandIndex1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandIndex2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandIndex3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            if self.LeftHandMiddle1.Bind_Joint:
                self.LeftHandMiddle1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandMiddle2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandMiddle3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            if self.LeftHandRing1.Bind_Joint:
                self.LeftHandRing1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandRing2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandRing3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            if self.LeftHandPinky1.Bind_Joint:
                self.LeftHandPinky1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandPinky2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandPinky3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                
            if self.RightHandThumb1.Bind_Joint:
                self.RightHandThumb1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandThumb2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandThumb3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            if self.RightHandIndex1.Bind_Joint:
                self.RightHandIndex1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandIndex2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandIndex3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            if self.RightHandMiddle1.Bind_Joint:
                self.RightHandMiddle1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandMiddle2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandMiddle3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            if self.RightHandRing1.Bind_Joint:
                self.RightHandRing1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandRing2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandRing3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            if self.RightHandPinky1.Bind_Joint:
                self.RightHandPinky1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandPinky2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandPinky3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                
            #Options
            self.LeftFoot.createControl(type = "options", 
                                    style = "options", 
                                    scale = (self.proportions["depth"]*0.12, self.proportions["depth"]*0.12, self.proportions["depth"]*-0.12),
                                    offset = (0, 0, self.proportions["depth"]*-0.4),  
                                    estimateSize = estimateSize,
                                    partialConstraint = 2,
                                    color_ = "black")
            
            self.RightFoot.createControl(type = "options", 
                                    style = "options", 
                                    scale = (self.proportions["depth"]*0.12, self.proportions["depth"]*0.12, self.proportions["depth"]*-0.12),
                                    offset = (0, 0, self.proportions["depth"]*-0.4),  
                                    estimateSize = estimateSize,
                                    partialConstraint = 2,
                                    color_ = "black")
            
            self.LeftHand.createControl(type = "options", 
                                    style = "options", 
                                    scale = (self.proportions["depth"]*0.12, self.proportions["depth"]*0.12, self.proportions["depth"]*-0.12),
                                    offset = (0, self.proportions["depth"]*0.3, self.proportions["depth"]*-0.3),  
                                    estimateSize = estimateSize,
                                    color_ = "black")
            
            self.RightHand.createControl(type = "options", 
                                    style = "options", 
                                    scale = (self.proportions["depth"]*0.12, self.proportions["depth"]*0.12, self.proportions["depth"]*-0.12),
                                    offset = (0, self.proportions["depth"]*0.3, self.proportions["depth"]*-0.3),  
                                    estimateSize = estimateSize,
                                    color_ = "black")
        
        
        elif self.rigType == "World":     
            #root
            if self.Root.Bind_Joint:
                self.Root.createControl(type = "normal", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.8, self.proportions["depth"]*0.8, self.proportions["depth"]*0.8), 
                                    offset = (0,0,0), 
                                    estimateSize = estimateSize)
            
                #hips
                self.Hips.createControl(type = "normal", 
                                        style = "hula", 
                                        scale = (self.proportions["depth"]*0.75, self.proportions["depth"]*0.75, self.proportions["depth"]*0.75),
                                        offset = (0,-.01*self.proportions["height"],0), 
                                        estimateSize = estimateSize,
                                        color_ = "yellow")
            else:
                #hips
                self.Hips.createControl(type = "normal", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.8, self.proportions["depth"]*0.8, self.proportions["depth"]*0.8), 
                                    offset = (0,0,0), 
                                    estimateSize = estimateSize)
            #spine
            self.Spine.createControl(type = "normal", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.7, self.proportions["depth"]*0.7, self.proportions["depth"]*0.7),
                                    offset = (0,0,0), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
            
            #spine1
            self.Spine1.createControl(type = "normal", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.6, self.proportions["depth"]*0.6, self.proportions["depth"]*0.6),
                                    offset = (0,0,0), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
            #spine2
            if self.Spine3.Bind_Joint:
                self.Spine2.createControl(type = "normal", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.6, self.proportions["depth"]*0.6, self.proportions["depth"]*0.6),
                                    offset = (0,0,0), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
                self.Spine3.createControl(type = "normal", 
                                    style = "box", 
                                    scale = (self.proportions["depth"]*0.7, self.proportions["depth"]*0.7, (self.proportions["depth"])*0.8), 
                                    offset = (0,self.proportions["depth"]*.2,0), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
            else:
                self.Spine2.createControl(type = "normal", 
                                    style = "box", 
                                    scale = (self.proportions["depth"]*0.7, self.proportions["depth"]*0.7, (self.proportions["depth"])*0.8), 
                                    offset = (0,self.proportions["depth"]*.2,0), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
                                    
            #neck
            self.Neck.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*-0.18, self.proportions["depth"]*0.18, self.proportions["depth"]*0.18),
                                    offset = (self.proportions["height"]*0.033, 0, self.proportions["height"]*-0.04),  
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
            if self.Neck1.Bind_Joint:
                self.Neck1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*-0.18, self.proportions["depth"]*0.18, self.proportions["depth"]*0.18),
                                    offset = (self.proportions["height"]*0.033, 0, self.proportions["height"]*-0.04),  
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
                                    
            #head
            self.Head.createControl(type = "normal", 
                                    style = "box", 
                                    scale = (self.proportions["depth"]*0.4, self.proportions["height"]*0.13, (self.proportions["depth"])*0.5), 
                                    offset = (0,self.proportions["height"]*.06,self.proportions["depth"]*0.1), 
                                    estimateSize = estimateSize,
                                    color_ = "yellow")
                               
            #LeftShoulder
            self.LeftShoulder.createControl(type = "normal", 
                                    style = "circleWrapped", 
                                    scale = (self.proportions["depth"]*0.4, self.proportions["depth"]*0.15, self.proportions["depth"]*0.15), 
                                    offset = (self.proportions["height"]*0.04, self.proportions["depth"]*0.3, 0), 
                                    rotate = (0, -90, 90), 
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
                                    
            #RightShoulder
            self.RightShoulder.createControl(type = "normal", 
                                    style = "circleWrapped", 
                                    scale = (self.proportions["depth"]*0.4, self.proportions["depth"]*0.15, self.proportions["depth"]*0.15), 
                                    offset = (self.proportions["height"]*-0.04, self.proportions["depth"]*0.3, 0), 
                                    rotate = (0, -90, 90),  
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            #LeftArm
            self.LeftArm.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.25, self.proportions["depth"]*0.25, self.proportions["depth"]*0.25),
                                    offset = (0, 0, 0),
                                    rotate = (0, 90, 0), 
                                    rigType = "World",
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
            
            #RightArm
            self.RightArm.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.25, self.proportions["depth"]*0.25, self.proportions["depth"]*0.25),
                                    offset = (0, 0, 0),
                                    rotate = (0, 90, 0), 
                                    rigType = "World",
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            #LeftForeArm
            self.LeftForeArm.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.25, self.proportions["depth"]*0.25, self.proportions["depth"]*0.25),
                                    offset = (0, 0, 0),
                                    rotate = (0, 90, 0),  
                                    rigType = "World",
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
            
            self.LeftForeArm.createControl(type = "IK", 
                                    style = "PoleVector", 
                                    scale = (self.proportions["depth"]*0.1, self.proportions["depth"]*0.2, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0),
                                    rotate = (0, 180, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            
            #RightForeArm
            self.RightForeArm.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.25, self.proportions["depth"]*0.25, self.proportions["depth"]*0.25),
                                    offset = (0, 0, 0),
                                    rotate = (0, 90, 0), 
                                    rigType = "World", 
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            self.RightForeArm.createControl(type = "IK", 
                                    style = "PoleVector", 
                                    scale = (self.proportions["depth"]*0.1, self.proportions["depth"]*0.2, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 180, 0),
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            
            #LeftHand
            self.LeftHand.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.2, self.proportions["depth"]*0.2, self.proportions["depth"]*0.2),
                                    offset = (0, 0, 0), 
                                    rotate = (0, 90, 0), 
                                    rigType = "World",
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
            
            self.LeftHand.createControl(type = "IK", 
                                    style = "box", 
                                    scale = (self.proportions["depth"]*0.2, self.proportions["depth"]*0.3, self.proportions["depth"]*0.2),
                                    offset = (self.proportions["depth"]*0.3, 0, 0),  
                                    rotate = (0, -90, -90),
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            
            #RightHand
            self.RightHand.createControl(type = "FK", 
                                    style = "circle", 
                                    scale = (self.proportions["depth"]*0.2, self.proportions["depth"]*0.2, self.proportions["depth"]*0.2),
                                    offset = (0, 0, 0),
                                    rotate = (0, 90, 0),
                                    rigType = "World",
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            self.RightHand.createControl(type = "IK", 
                                    style = "box", 
                                    scale = (self.proportions["depth"]*0.2, self.proportions["depth"]*0.3, self.proportions["depth"]*0.2),
                                    offset = (self.proportions["depth"]*-0.3, 0, 0), 
                                    rotate = (0, 90, 90), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                                    
                                    
            #LeftUpLeg
            self.LeftUpLeg.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*0.1, self.proportions["depth"]*0.1, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0),
                                    rotate = (0, 180, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
                                    
            #LeftLeg
            self.LeftLeg.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*0.09, self.proportions["depth"]*0.09, self.proportions["depth"]*0.09),
                                    offset = (0, 0, 0),
                                    rotate = (0, 180, 0),
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
                                    
            self.LeftLeg.createControl(type = "IK", 
                                    style = "PoleVector", 
                                    scale = (self.proportions["depth"]*0.1, self.proportions["depth"]*0.2, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            
            #LeftFoot
            self.LeftFoot.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*0.08, self.proportions["depth"]*0.08, self.proportions["depth"]*0.08),
                                    offset = (0, 0, 0),
                                    rotate = (0, 180, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
            
            self.LeftFoot.createControl(type = "IK", 
                                    style = "footBox", 
                                    scale = (self.proportions["depth"]*0.4, self.proportions["depth"]*0.7, self.proportions["depth"]*-0.4),
                                    offset = (0, self.proportions["depth"]*0.1, self.proportions["depth"]*0.1),
                                    rotate = (90, 0, 0),  
                                    partialConstraint = 1,
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            mayac.move(self.proportions["lowPoint"], "%s.scalePivot" % (self.LeftFoot.IK_CTRL),  "%s.rotatePivot" % (self.LeftFoot.IK_CTRL),  y = True)
    
            #LeftToeBase
            self.LeftToeBase.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*0.07, self.proportions["depth"]*0.07, self.proportions["depth"]*0.07),
                                    offset = (0, 0, 0),
                                    rotate = (0, 180, 0),   
                                    estimateSize = estimateSize,
                                    color_ = "blue1")
                                    
                                    
            #RightUpLeg
            self.RightUpLeg.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*-0.1, self.proportions["depth"]*0.1, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0),
                                    rotate = (0, 180, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red1")
                                    
            #RightLeg
            self.RightLeg.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*-0.09, self.proportions["depth"]*0.09, self.proportions["depth"]*0.09),
                                    offset = (0, 0, 0),
                                    rotate = (0, 180, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            self.RightLeg.createControl(type = "IK", 
                                    style = "PoleVector", 
                                    scale = (self.proportions["depth"]*0.1, self.proportions["depth"]*0.2, self.proportions["depth"]*0.1),
                                    offset = (0, 0, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                                    
            #RightFoot
            self.RightFoot.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*-0.08, self.proportions["depth"]*0.08, self.proportions["depth"]*0.08),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 180, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            self.RightFoot.createControl(type = "IK", 
                                    style = "footBox", 
                                    scale = (self.proportions["depth"]*0.4, self.proportions["depth"]*0.7, self.proportions["depth"]*-0.4),
                                    offset = (0, self.proportions["depth"]*0.1, self.proportions["depth"]*0.1),
                                    rotate = (90, 0, 0),
                                    partialConstraint = 1,  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            mayac.move(self.proportions["lowPoint"], "%s.scalePivot" % (self.RightFoot.IK_CTRL),  "%s.rotatePivot" % (self.RightFoot.IK_CTRL),  y = True)
    
            #RightToeBase
            self.RightToeBase.createControl(type = "FK", 
                                    style = "pin", 
                                    scale = (self.proportions["depth"]*-0.07, self.proportions["depth"]*0.07, self.proportions["depth"]*0.07),
                                    offset = (0, 0, 0),
                                    rotate = (0, 180, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red1")
            
            #fingers
            if self.LeftHandThumb1.Bind_Joint:
                self.LeftHandThumb1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandThumb2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),
                                    rotate = (0, 90, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandThumb3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),
                                    rotate = (0, 90, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            if self.LeftHandIndex1.Bind_Joint:
                self.LeftHandIndex1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0), 
                                    rotate = (0, 90, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandIndex2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandIndex3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            if self.LeftHandMiddle1.Bind_Joint:
                self.LeftHandMiddle1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandMiddle2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandMiddle3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0), 
                                    rotate = (0, 90, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            if self.LeftHandRing1.Bind_Joint:
                self.LeftHandRing1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandRing2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandRing3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
            if self.LeftHandPinky1.Bind_Joint:
                self.LeftHandPinky1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0), 
                                    rotate = (0, 90, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandPinky2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0), 
                                    rotate = (0, 90, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                self.LeftHandPinky3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "blue2")
                
            if self.RightHandThumb1.Bind_Joint:
                self.RightHandThumb1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0), 
                                    rotate = (0, 90, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandThumb2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandThumb3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            if self.RightHandIndex1.Bind_Joint:
                self.RightHandIndex1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0), 
                                    rotate = (0, 90, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandIndex2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandIndex3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0), 
                                    rotate = (0, 90, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            if self.RightHandMiddle1.Bind_Joint:
                self.RightHandMiddle1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandMiddle2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0), 
                                    rotate = (0, 90, 0),  
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandMiddle3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            if self.RightHandRing1.Bind_Joint:
                self.RightHandRing1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandRing2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandRing3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
            if self.RightHandPinky1.Bind_Joint:
                self.RightHandPinky1.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.02, self.proportions["depth"]*0.02, self.proportions["depth"]*0.02),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandPinky2.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.016, self.proportions["depth"]*0.016, self.proportions["depth"]*0.016),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
                self.RightHandPinky3.createControl(type = "normal", 
                                    style = "pin1", 
                                    scale = (self.proportions["depth"]*0.012, self.proportions["depth"]*0.012, self.proportions["depth"]*0.012),
                                    offset = (0, 0, 0),  
                                    rotate = (0, 90, 0), 
                                    estimateSize = estimateSize,
                                    color_ = "red2")
        
            #Options
            self.LeftFoot.createControl(type = "options", 
                                    style = "options", 
                                    scale = (self.proportions["depth"]*0.12, self.proportions["depth"]*0.12, self.proportions["depth"]*-0.12),
                                    offset = (0, 0, self.proportions["depth"]*-0.4),  
                                    estimateSize = estimateSize,
                                    partialConstraint = 2,
                                    color_ = "black")
            
            self.RightFoot.createControl(type = "options", 
                                    style = "options", 
                                    scale = (self.proportions["depth"]*0.12, self.proportions["depth"]*0.12, self.proportions["depth"]*-0.12),
                                    offset = (0, 0, self.proportions["depth"]*-0.4),  
                                    estimateSize = estimateSize,
                                    partialConstraint = 2,
                                    color_ = "black")
            
            self.LeftHand.createControl(type = "options", 
                                    style = "options", 
                                    scale = (self.proportions["depth"]*0.12, self.proportions["depth"]*0.12, self.proportions["depth"]*-0.12),
                                    offset = (self.proportions["depth"]*0.3, self.proportions["depth"]*0.3, 0),  
                                    rotate = (-90, 0, -90),  
                                    estimateSize = estimateSize,
                                    color_ = "black")
            
            self.RightHand.createControl(type = "options", 
                                    style = "options", 
                                    scale = (self.proportions["depth"]*0.12, self.proportions["depth"]*0.12, self.proportions["depth"]*-0.12),
                                    offset = (self.proportions["depth"]*-0.3, self.proportions["depth"]*0.3, 0),  
                                    rotate = (-90, 0, -90), 
                                    estimateSize = estimateSize,
                                    color_ = "black")
                                
                
                
    def hookUpControls(self):
        #Groupings
        self.Character_GRP = mayac.group(em = True, name = "Character")
        DJB_movePivotToObject(self.Character_GRP, self.global_CTRL)
        self.CTRL_GRP = mayac.group(em = True, name = "CTRL_GRP")
        DJB_movePivotToObject(self.CTRL_GRP, self.global_CTRL)
        mayac.parent(self.global_CTRL, self.CTRL_GRP)
        mayac.parent(self.CTRL_GRP, self.Character_GRP)
        self.Joint_GRP = mayac.group(em = True, name = "Joint_GRP")
        DJB_movePivotToObject(self.Joint_GRP, self.global_CTRL)
        mayac.parent(self.Joint_GRP, self.Character_GRP)
        self.AnimData_Joint_GRP = mayac.group(em = True, name = "AnimData_Joint_GRP")
        DJB_movePivotToObject(self.AnimData_Joint_GRP, self.global_CTRL)
        mayac.parent(self.AnimData_Joint_GRP, self.Joint_GRP)
        if self.hulaOption:
            mayac.parent(self.Root.AnimData_Joint, self.AnimData_Joint_GRP)
        else:
            mayac.parent(self.Hips.AnimData_Joint, self.AnimData_Joint_GRP)
        self.Bind_Joint_GRP = mayac.group(em = True, name = "Bind_Joint_GRP")
        DJB_movePivotToObject(self.Bind_Joint_GRP, self.global_CTRL)
        mayac.parent(self.Bind_Joint_GRP, self.Joint_GRP)
        if self.hulaOption:
            mayac.parent(self.Root.Bind_Joint, self.Bind_Joint_GRP)
        else:
            mayac.parent(self.Hips.Bind_Joint, self.Bind_Joint_GRP)
        self.Mesh_GRP = mayac.group(em = True, name = "Mesh_GRP")
        DJB_movePivotToObject(self.Mesh_GRP, self.global_CTRL)
        tempTransList =[]
        for geo in self.mesh:
            transform = mayac.listRelatives(geo, parent = True)
            if mayac.objectType(transform) == "transform" and transform not in tempTransList:
                mayac.parent(transform, self.Mesh_GRP)
                DJB_LockNHide(transform[0])
                tempTransList.append(transform)
        mayac.parent(self.Mesh_GRP, self.Character_GRP)

        #get rid of any limitations
        for bodyPart in self.bodyParts:
            if bodyPart.Bind_Joint:
                mayac.transformLimits(bodyPart.Bind_Joint, rm = True)
        
        #create FK and IK Joints
        self.LeftArm.duplicateJoint("FK", parent_ = "Bind_Joint")
        self.LeftForeArm.duplicateJoint("FK")
        self.LeftHand.duplicateJoint("FK")
        self.RightArm.duplicateJoint("FK", parent_ = "Bind_Joint")
        self.RightForeArm.duplicateJoint("FK")
        self.RightHand.duplicateJoint("FK")
        self.LeftUpLeg.duplicateJoint("FK", parent_ = "Bind_Joint")
        self.LeftLeg.duplicateJoint("FK")
        self.LeftFoot.duplicateJoint("FK")
        self.LeftToeBase.duplicateJoint("FK")
        self.LeftToe_End.duplicateJoint("FK")
        self.RightUpLeg.duplicateJoint("FK", parent_ = "Bind_Joint")
        self.RightLeg.duplicateJoint("FK")
        self.RightFoot.duplicateJoint("FK")
        self.RightToeBase.duplicateJoint("FK")
        self.RightToe_End.duplicateJoint("FK")
        
        self.LeftArm.duplicateJoint("IK", parent_ = "Bind_Joint")
        self.LeftForeArm.duplicateJoint("IK")
        self.LeftHand.duplicateJoint("IK")
        self.RightArm.duplicateJoint("IK", parent_ = "Bind_Joint")
        self.RightForeArm.duplicateJoint("IK")
        self.RightHand.duplicateJoint("IK")
        self.LeftUpLeg.duplicateJoint("IK", parent_ = "Bind_Joint")
        self.LeftLeg.duplicateJoint("IK")
        self.LeftFoot.duplicateJoint("IK")
        self.LeftToeBase.duplicateJoint("IK")
        self.LeftToe_End.duplicateJoint("IK")
        self.RightUpLeg.duplicateJoint("IK", parent_ = "Bind_Joint")
        self.RightLeg.duplicateJoint("IK")
        self.RightFoot.duplicateJoint("IK")
        self.RightToeBase.duplicateJoint("IK")
        self.RightToe_End.duplicateJoint("IK")
        
        #finalize CTRLs
        for bodyPart in self.bodyParts:
            bodyPart.finalizeCTRLs()
            
        #Left Arm IK BakingLOC Positions
        selfPOS = mayac.xform(self.LeftForeArm.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
        parentPOS = mayac.xform(self.LeftForeArm.parent.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
        tempDistance = math.sqrt((selfPOS[0]-parentPOS[0])*(selfPOS[0]-parentPOS[0]) + (selfPOS[1]-parentPOS[1])*(selfPOS[1]-parentPOS[1]) + (selfPOS[2]-parentPOS[2])*(selfPOS[2]-parentPOS[2]))
        if self.rigType == "AutoRig":
            mayac.setAttr("%s.translateX" % (self.LeftForeArm.IK_BakingLOC), tempDistance / 2)
        elif self.rigType == "World":  
            mayac.setAttr("%s.translateZ" % (self.LeftForeArm.IK_BakingLOC), tempDistance / -2)
            
        #Right Arm IK BakingLOC Positions
        selfPOS = mayac.xform(self.RightForeArm.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
        parentPOS = mayac.xform(self.RightForeArm.parent.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
        tempDistance = math.sqrt((selfPOS[0]-parentPOS[0])*(selfPOS[0]-parentPOS[0]) + (selfPOS[1]-parentPOS[1])*(selfPOS[1]-parentPOS[1]) + (selfPOS[2]-parentPOS[2])*(selfPOS[2]-parentPOS[2]))
        if self.rigType == "AutoRig":
            mayac.setAttr("%s.translateX" % (self.RightForeArm.IK_BakingLOC), tempDistance / -2)
        elif self.rigType == "World":  
            mayac.setAttr("%s.translateZ" % (self.RightForeArm.IK_BakingLOC), tempDistance / -2)
            
        #more groupings
        self.LeftHand_CTRLs_GRP = mayac.group(em = True, name = "LeftHand_CTRLs_GRP")
        self.RightHand_CTRLs_GRP = mayac.group(em = True, name = "RightHand_CTRLs_GRP")
        DJB_movePivotToObject(self.LeftHand_CTRLs_GRP, self.LeftHand.Bind_Joint)
        DJB_movePivotToObject(self.RightHand_CTRLs_GRP, self.RightHand.Bind_Joint)
        #set rotation orders
        mayac.setAttr("%s.rotateOrder" % (self.LeftHand_CTRLs_GRP), self.LeftHand.rotOrder)
        mayac.setAttr("%s.rotateOrder" % (self.RightHand_CTRLs_GRP), self.RightHand.rotOrder)

        mayac.parent(self.LeftHand_CTRLs_GRP, self.RightHand_CTRLs_GRP, self.global_CTRL)
        if self.LeftHandIndex1.Bind_Joint:
            mayac.parent(self.LeftHandIndex1.FK_CTRL_POS_GRP, self.LeftHand_CTRLs_GRP)
        if self.LeftHandThumb1.Bind_Joint:
            mayac.parent(self.LeftHandThumb1.FK_CTRL_POS_GRP, self.LeftHand_CTRLs_GRP)
        if self.LeftHandMiddle1.Bind_Joint:
            mayac.parent(self.LeftHandMiddle1.FK_CTRL_POS_GRP, self.LeftHand_CTRLs_GRP)
        if self.LeftHandRing1.Bind_Joint:
            mayac.parent(self.LeftHandRing1.FK_CTRL_POS_GRP, self.LeftHand_CTRLs_GRP)
        if self.LeftHandPinky1.Bind_Joint:
            mayac.parent(self.LeftHandPinky1.FK_CTRL_POS_GRP, self.LeftHand_CTRLs_GRP)
        if self.RightHandIndex1.Bind_Joint:
            mayac.parent(self.RightHandIndex1.FK_CTRL_POS_GRP, self.RightHand_CTRLs_GRP)    
        if self.RightHandThumb1.Bind_Joint:
            mayac.parent(self.RightHandThumb1.FK_CTRL_POS_GRP, self.RightHand_CTRLs_GRP)
        if self.RightHandMiddle1.Bind_Joint:
            mayac.parent(self.RightHandMiddle1.FK_CTRL_POS_GRP, self.RightHand_CTRLs_GRP)
        if self.RightHandRing1.Bind_Joint:
            mayac.parent(self.RightHandRing1.FK_CTRL_POS_GRP, self.RightHand_CTRLs_GRP)
        if self.RightHandPinky1.Bind_Joint:
            mayac.parent(self.RightHandPinky1.FK_CTRL_POS_GRP, self.RightHand_CTRLs_GRP)

        mayac.parentConstraint(self.LeftHand.Bind_Joint, self.LeftHand_CTRLs_GRP, name = "%s_Constraint" %(self.LeftHand_CTRLs_GRP))
        mayac.parentConstraint(self.RightHand.Bind_Joint, self.RightHand_CTRLs_GRP, name = "%s_Constraint" %(self.RightHand_CTRLs_GRP))
        DJB_LockNHide(self.LeftHand_CTRLs_GRP)
        DJB_LockNHide(self.RightHand_CTRLs_GRP)
        
        mayac.parent(self.LeftFoot.Options_CTRL, self.RightFoot.Options_CTRL, self.LeftHand.Options_CTRL, self.RightHand.Options_CTRL, self.global_CTRL)
        if self.hulaOption:
            mayac.parent(self.Root.FK_CTRL_POS_GRP, self.global_CTRL)
        else:
            mayac.parent(self.Hips.FK_CTRL_POS_GRP, self.global_CTRL)
        mayac.parent(self.LeftForeArm.IK_CTRL_parent_POS_GRP, self.global_CTRL)
        mayac.parent(self.LeftHand.IK_CTRL_grandparent_POS_GRP, self.global_CTRL)
        mayac.parent(self.RightForeArm.IK_CTRL_parent_POS_GRP, self.global_CTRL)
        mayac.parent(self.RightHand.IK_CTRL_grandparent_POS_GRP, self.global_CTRL)
        mayac.parent(self.LeftLeg.IK_CTRL_parent_POS_GRP, self.global_CTRL)
        mayac.parent(self.LeftFoot.IK_CTRL_grandparent_POS_GRP, self.global_CTRL)
        mayac.parent(self.RightLeg.IK_CTRL_parent_POS_GRP, self.global_CTRL)
        mayac.parent(self.RightFoot.IK_CTRL_grandparent_POS_GRP, self.global_CTRL)
        
        self.IK_Dummy_Joint_GRP = mayac.group(em = True, name = "IK_Dummy_Joint_GRP")
        if self.hulaOption:
            mayac.parent(self.Root.IK_Dummy_Joint, self.IK_Dummy_Joint_GRP)
        else:
            mayac.parent(self.Hips.IK_Dummy_Joint, self.IK_Dummy_Joint_GRP)
        mayac.parent(self.IK_Dummy_Joint_GRP, self.global_CTRL)
        
        #IKFK follow body
        #arms
        temp = mayac.parentConstraint(self.LeftShoulder.IK_Dummy_Joint, self.LeftHand.IK_CTRL_grandparent_POS_GRP, maintainOffset = True)
        self.LeftHand_grandparent_Constraint = temp[0]
        mayac.parentConstraint(self.LeftShoulder.Bind_Joint, self.LeftHand.IK_CTRL_grandparent_POS_GRP, maintainOffset = True)
        self.LeftHand_grandparent_Constraint_Reverse = mayac.createNode( 'reverse', n="LeftHand_grandparent_Constraint_Reverse")
        mayac.connectAttr("%s.FollowBody" %(self.LeftHand.IK_CTRL), "%s.inputX" %(self.LeftHand_grandparent_Constraint_Reverse))
        mayac.connectAttr("%s.FollowBody" %(self.LeftHand.IK_CTRL), "%s.%sW1" %(self.LeftHand_grandparent_Constraint, self.LeftShoulder.Bind_Joint))
        mayac.connectAttr("%s.outputX" %(self.LeftHand_grandparent_Constraint_Reverse), "%s.%sW0" %(self.LeftHand_grandparent_Constraint, self.LeftShoulder.IK_Dummy_Joint))
        mayac.setAttr("%s.interpType" %(self.LeftHand_grandparent_Constraint), 2)
        
        temp = mayac.parentConstraint(self.RightShoulder.IK_Dummy_Joint, self.RightHand.IK_CTRL_grandparent_POS_GRP, maintainOffset = True)
        self.RightHand_grandparent_Constraint = temp[0]
        mayac.parentConstraint(self.RightShoulder.Bind_Joint, self.RightHand.IK_CTRL_grandparent_POS_GRP, maintainOffset = True)
        self.RightHand_grandparent_Constraint_Reverse = mayac.createNode( 'reverse', n="RightHand_grandparent_Constraint_Reverse")
        mayac.connectAttr("%s.FollowBody" %(self.RightHand.IK_CTRL), "%s.inputX" %(self.RightHand_grandparent_Constraint_Reverse))
        mayac.connectAttr("%s.FollowBody" %(self.RightHand.IK_CTRL), "%s.%sW1" %(self.RightHand_grandparent_Constraint, self.RightShoulder.Bind_Joint))
        mayac.connectAttr("%s.outputX" %(self.RightHand_grandparent_Constraint_Reverse), "%s.%sW0" %(self.RightHand_grandparent_Constraint, self.RightShoulder.IK_Dummy_Joint))
        mayac.setAttr("%s.interpType" %(self.RightHand_grandparent_Constraint), 2)
        
        temp = mayac.parentConstraint(self.LeftShoulder.IK_Dummy_Joint, self.LeftForeArm.IK_CTRL_parent_POS_GRP, maintainOffset = True)
        self.LeftForeArm_parent_Constraint = temp[0]
        mayac.parentConstraint(self.LeftShoulder.Bind_Joint, self.LeftForeArm.IK_CTRL_parent_POS_GRP, maintainOffset = True)
        self.LeftForeArm_parent_Constraint_Reverse = mayac.createNode( 'reverse', n="LeftForeArm_parent_Constraint_Reverse")
        mayac.connectAttr("%s.FollowBody" %(self.LeftForeArm.IK_CTRL), "%s.inputX" %(self.LeftForeArm_parent_Constraint_Reverse))
        mayac.connectAttr("%s.FollowBody" %(self.LeftForeArm.IK_CTRL), "%s.%sW1" %(self.LeftForeArm_parent_Constraint, self.LeftShoulder.Bind_Joint))
        mayac.connectAttr("%s.outputX" %(self.LeftForeArm_parent_Constraint_Reverse), "%s.%sW0" %(self.LeftForeArm_parent_Constraint, self.LeftShoulder.IK_Dummy_Joint))
        mayac.setAttr("%s.interpType" %(self.LeftForeArm_parent_Constraint), 2)
        
        temp = mayac.parentConstraint(self.RightShoulder.IK_Dummy_Joint, self.RightForeArm.IK_CTRL_parent_POS_GRP, maintainOffset = True)
        self.RightForeArm_parent_Constraint = temp[0]
        mayac.parentConstraint(self.RightShoulder.Bind_Joint, self.RightForeArm.IK_CTRL_parent_POS_GRP, maintainOffset = True)
        self.RightForeArm_parent_Constraint_Reverse = mayac.createNode( 'reverse', n="RightForeArm_parent_Constraint_Reverse")
        mayac.connectAttr("%s.FollowBody" %(self.RightForeArm.IK_CTRL), "%s.inputX" %(self.RightForeArm_parent_Constraint_Reverse))
        mayac.connectAttr("%s.FollowBody" %(self.RightForeArm.IK_CTRL), "%s.%sW1" %(self.RightForeArm_parent_Constraint, self.RightShoulder.Bind_Joint))
        mayac.connectAttr("%s.outputX" %(self.RightForeArm_parent_Constraint_Reverse), "%s.%sW0" %(self.RightForeArm_parent_Constraint, self.RightShoulder.IK_Dummy_Joint))
        mayac.setAttr("%s.interpType" %(self.RightForeArm_parent_Constraint), 2)
        
        #legs
        temp = mayac.parentConstraint(self.Hips.IK_Dummy_Joint, self.LeftFoot.IK_CTRL_grandparent_POS_GRP, maintainOffset = True)
        self.LeftFoot_grandparent_Constraint = temp[0]
        mayac.parentConstraint(self.Hips.Bind_Joint, self.LeftFoot.IK_CTRL_grandparent_POS_GRP, maintainOffset = True)
        self.LeftFoot_grandparent_Constraint_Reverse = mayac.createNode( 'reverse', n="LeftFoot_grandparent_Constraint_Reverse")
        mayac.connectAttr("%s.FollowBody" %(self.LeftFoot.IK_CTRL), "%s.inputX" %(self.LeftFoot_grandparent_Constraint_Reverse))
        mayac.connectAttr("%s.FollowBody" %(self.LeftFoot.IK_CTRL), "%s.%sW1" %(self.LeftFoot_grandparent_Constraint, self.Hips.Bind_Joint))
        mayac.connectAttr("%s.outputX" %(self.LeftFoot_grandparent_Constraint_Reverse), "%s.%sW0" %(self.LeftFoot_grandparent_Constraint, self.Hips.IK_Dummy_Joint))
        mayac.setAttr("%s.interpType" %(self.LeftFoot_grandparent_Constraint), 2)
        
        temp = mayac.parentConstraint(self.Hips.IK_Dummy_Joint, self.RightFoot.IK_CTRL_grandparent_POS_GRP, maintainOffset = True)
        self.RightFoot_grandparent_Constraint = temp[0]
        mayac.parentConstraint(self.Hips.Bind_Joint, self.RightFoot.IK_CTRL_grandparent_POS_GRP, maintainOffset = True)
        self.RightFoot_grandparent_Constraint_Reverse = mayac.createNode( 'reverse', n="RightFoot_grandparent_Constraint_Reverse")
        mayac.connectAttr("%s.FollowBody" %(self.RightFoot.IK_CTRL), "%s.inputX" %(self.RightFoot_grandparent_Constraint_Reverse))
        mayac.connectAttr("%s.FollowBody" %(self.RightFoot.IK_CTRL), "%s.%sW1" %(self.RightFoot_grandparent_Constraint, self.Hips.Bind_Joint))
        mayac.connectAttr("%s.outputX" %(self.RightFoot_grandparent_Constraint_Reverse), "%s.%sW0" %(self.RightFoot_grandparent_Constraint, self.Hips.IK_Dummy_Joint))
        mayac.setAttr("%s.interpType" %(self.RightFoot_grandparent_Constraint), 2)
        
        temp = mayac.parentConstraint(self.Hips.IK_Dummy_Joint, self.LeftLeg.IK_CTRL_parent_POS_GRP, maintainOffset = True)
        self.LeftLeg_parent_Constraint = temp[0]
        mayac.parentConstraint(self.Hips.Bind_Joint, self.LeftLeg.IK_CTRL_parent_POS_GRP, maintainOffset = True)
        self.LeftLeg_parent_Constraint_Reverse = mayac.createNode( 'reverse', n="LeftLeg_parent_Constraint_Reverse")
        mayac.connectAttr("%s.FollowBody" %(self.LeftLeg.IK_CTRL), "%s.inputX" %(self.LeftLeg_parent_Constraint_Reverse))
        mayac.connectAttr("%s.FollowBody" %(self.LeftLeg.IK_CTRL), "%s.%sW1" %(self.LeftLeg_parent_Constraint, self.Hips.Bind_Joint))
        mayac.connectAttr("%s.outputX" %(self.LeftLeg_parent_Constraint_Reverse), "%s.%sW0" %(self.LeftLeg_parent_Constraint, self.Hips.IK_Dummy_Joint))
        mayac.setAttr("%s.interpType" %(self.LeftLeg_parent_Constraint), 2)
        
        temp = mayac.parentConstraint(self.Hips.IK_Dummy_Joint, self.RightLeg.IK_CTRL_parent_POS_GRP, maintainOffset = True)
        self.RightLeg_parent_Constraint = temp[0]
        mayac.parentConstraint(self.Hips.Bind_Joint, self.RightLeg.IK_CTRL_parent_POS_GRP, maintainOffset = True)
        self.RightLeg_parent_Constraint_Reverse = mayac.createNode( 'reverse', n="RightLeg_parent_Constraint_Reverse")
        mayac.connectAttr("%s.FollowBody" %(self.RightLeg.IK_CTRL), "%s.inputX" %(self.RightLeg_parent_Constraint_Reverse))
        mayac.connectAttr("%s.FollowBody" %(self.RightLeg.IK_CTRL), "%s.%sW1" %(self.RightLeg_parent_Constraint, self.Hips.Bind_Joint))
        mayac.connectAttr("%s.outputX" %(self.RightLeg_parent_Constraint_Reverse), "%s.%sW0" %(self.RightLeg_parent_Constraint, self.Hips.IK_Dummy_Joint))
        mayac.setAttr("%s.interpType" %(self.RightLeg_parent_Constraint), 2)
        
        
        
        #IK Legs and Arms to Global
        temp = mayac.parentConstraint(self.LeftFoot.IK_CTRL_grandparent_POS_GRP, self.LeftFoot.IK_CTRL_grandparent_Global_POS_GRP, maintainOffset = True)
        self.LeftFoot.grandparent_Global_Constraint = temp[0]
        mayac.parentConstraint(self.global_CTRL, self.LeftFoot.IK_CTRL_grandparent_Global_POS_GRP, maintainOffset = True)
        self.LeftFoot.grandparent_Global_Constraint_Reverse = mayac.createNode( 'reverse', n="LeftFoot_grandparent_Global_Constraint_Reverse")
        mayac.connectAttr("%s.ParentToGlobal" %(self.LeftFoot.IK_CTRL), "%s.inputX" %(self.LeftFoot.grandparent_Global_Constraint_Reverse))
        mayac.connectAttr("%s.ParentToGlobal" %(self.LeftFoot.IK_CTRL), "%s.%sW1" %(self.LeftFoot.grandparent_Global_Constraint, self.global_CTRL))
        mayac.connectAttr("%s.outputX" %(self.LeftFoot.grandparent_Global_Constraint_Reverse), "%s.%sW0" %(self.LeftFoot.grandparent_Global_Constraint, self.LeftFoot.IK_CTRL_grandparent_POS_GRP))
        mayac.setAttr("%s.interpType" %(self.LeftFoot.grandparent_Global_Constraint), 0)
        
        temp = mayac.parentConstraint(self.RightFoot.IK_CTRL_grandparent_POS_GRP, self.RightFoot.IK_CTRL_grandparent_Global_POS_GRP, maintainOffset = True)
        self.RightFoot.grandparent_Global_Constraint = temp[0]
        mayac.parentConstraint(self.global_CTRL, self.RightFoot.IK_CTRL_grandparent_Global_POS_GRP, maintainOffset = True)
        self.RightFoot.grandparent_Global_Constraint_Reverse = mayac.createNode( 'reverse', n="RightFoot_grandparent_Global_Constraint_Reverse")
        mayac.connectAttr("%s.ParentToGlobal" %(self.RightFoot.IK_CTRL), "%s.inputX" %(self.RightFoot.grandparent_Global_Constraint_Reverse))
        mayac.connectAttr("%s.ParentToGlobal" %(self.RightFoot.IK_CTRL), "%s.%sW1" %(self.RightFoot.grandparent_Global_Constraint, self.global_CTRL))
        mayac.connectAttr("%s.outputX" %(self.RightFoot.grandparent_Global_Constraint_Reverse), "%s.%sW0" %(self.RightFoot.grandparent_Global_Constraint, self.RightFoot.IK_CTRL_grandparent_POS_GRP))
        mayac.setAttr("%s.interpType" %(self.RightFoot.grandparent_Global_Constraint), 2)
        
        temp = mayac.parentConstraint(self.LeftHand.IK_CTRL_grandparent_POS_GRP, self.LeftHand.IK_CTRL_grandparent_Global_POS_GRP, maintainOffset = True)
        self.LeftHand.grandparent_Global_Constraint = temp[0]
        mayac.parentConstraint(self.global_CTRL, self.LeftHand.IK_CTRL_grandparent_Global_POS_GRP, maintainOffset = True)
        self.LeftHand.grandparent_Global_Constraint_Reverse = mayac.createNode( 'reverse', n="LeftHand_grandparent_Global_Constraint_Reverse")
        mayac.connectAttr("%s.ParentToGlobal" %(self.LeftHand.IK_CTRL), "%s.inputX" %(self.LeftHand.grandparent_Global_Constraint_Reverse))
        mayac.connectAttr("%s.ParentToGlobal" %(self.LeftHand.IK_CTRL), "%s.%sW1" %(self.LeftHand.grandparent_Global_Constraint, self.global_CTRL))
        mayac.connectAttr("%s.outputX" %(self.LeftHand.grandparent_Global_Constraint_Reverse), "%s.%sW0" %(self.LeftHand.grandparent_Global_Constraint, self.LeftHand.IK_CTRL_grandparent_POS_GRP))
        mayac.setAttr("%s.interpType" %(self.LeftHand.grandparent_Global_Constraint), 2)
        
        temp = mayac.parentConstraint(self.RightHand.IK_CTRL_grandparent_POS_GRP, self.RightHand.IK_CTRL_grandparent_Global_POS_GRP, maintainOffset = True)
        self.RightHand.grandparent_Global_Constraint = temp[0]
        mayac.parentConstraint(self.global_CTRL, self.RightHand.IK_CTRL_grandparent_Global_POS_GRP, maintainOffset = True)
        self.RightHand.grandparent_Global_Constraint_Reverse = mayac.createNode( 'reverse', n="RightHand_grandparent_Global_Constraint_Reverse")
        mayac.connectAttr("%s.ParentToGlobal" %(self.RightHand.IK_CTRL), "%s.inputX" %(self.RightHand.grandparent_Global_Constraint_Reverse))
        mayac.connectAttr("%s.ParentToGlobal" %(self.RightHand.IK_CTRL), "%s.%sW1" %(self.RightHand.grandparent_Global_Constraint, self.global_CTRL))
        mayac.connectAttr("%s.outputX" %(self.RightHand.grandparent_Global_Constraint_Reverse), "%s.%sW0" %(self.RightHand.grandparent_Global_Constraint, self.RightHand.IK_CTRL_grandparent_POS_GRP))
        mayac.setAttr("%s.interpType" %(self.RightHand.grandparent_Global_Constraint), 2)
        

        ''' self.IK_CTRL_inRig_CONST_GRP = None
        self.follow_extremity_Constraint = None
        self.follow_extremity_Constraint_Reverse = None'''
        
        #IK Elbows and Knees to Global
        temp = mayac.parentConstraint(self.LeftLeg.IK_CTRL_parent_POS_GRP, self.LeftLeg.IK_CTRL_parent_Global_POS_GRP, maintainOffset = True)
        self.LeftLeg.parent_Global_Constraint = temp[0]
        mayac.parentConstraint(self.global_CTRL, self.LeftLeg.IK_CTRL_parent_Global_POS_GRP, maintainOffset = True)
        self.LeftLeg.parent_Global_Constraint_Reverse = mayac.createNode( 'reverse', n="LeftLeg_parent_Global_Constraint_Reverse")
        mayac.connectAttr("%s.ParentToGlobal" %(self.LeftLeg.IK_CTRL), "%s.inputX" %(self.LeftLeg.parent_Global_Constraint_Reverse))
        mayac.connectAttr("%s.ParentToGlobal" %(self.LeftLeg.IK_CTRL), "%s.%sW1" %(self.LeftLeg.parent_Global_Constraint, self.global_CTRL))
        mayac.connectAttr("%s.outputX" %(self.LeftLeg.parent_Global_Constraint_Reverse), "%s.%sW0" %(self.LeftLeg.parent_Global_Constraint, self.LeftLeg.IK_CTRL_parent_POS_GRP))
        mayac.setAttr("%s.interpType" %(self.LeftLeg.parent_Global_Constraint), 2)
        
        temp = mayac.parentConstraint(self.RightLeg.IK_CTRL_parent_POS_GRP, self.RightLeg.IK_CTRL_parent_Global_POS_GRP, maintainOffset = True)
        self.RightLeg.parent_Global_Constraint = temp[0]
        mayac.parentConstraint(self.global_CTRL, self.RightLeg.IK_CTRL_parent_Global_POS_GRP, maintainOffset = True)
        self.RightLeg.parent_Global_Constraint_Reverse = mayac.createNode( 'reverse', n="RightLeg_parent_Global_Constraint_Reverse")
        mayac.connectAttr("%s.ParentToGlobal" %(self.RightLeg.IK_CTRL), "%s.inputX" %(self.RightLeg.parent_Global_Constraint_Reverse))
        mayac.connectAttr("%s.ParentToGlobal" %(self.RightLeg.IK_CTRL), "%s.%sW1" %(self.RightLeg.parent_Global_Constraint, self.global_CTRL))
        mayac.connectAttr("%s.outputX" %(self.RightLeg.parent_Global_Constraint_Reverse), "%s.%sW0" %(self.RightLeg.parent_Global_Constraint, self.RightLeg.IK_CTRL_parent_POS_GRP))
        mayac.setAttr("%s.interpType" %(self.RightLeg.parent_Global_Constraint), 2)
        
        temp = mayac.parentConstraint(self.LeftForeArm.IK_CTRL_parent_POS_GRP, self.LeftForeArm.IK_CTRL_parent_Global_POS_GRP, maintainOffset = True)
        self.LeftForeArm.parent_Global_Constraint = temp[0]
        mayac.parentConstraint(self.global_CTRL, self.LeftForeArm.IK_CTRL_parent_Global_POS_GRP, maintainOffset = True)
        self.LeftForeArm.parent_Global_Constraint_Reverse = mayac.createNode( 'reverse', n="LeftForeArm_parent_Global_Constraint_Reverse")
        mayac.connectAttr("%s.ParentToGlobal" %(self.LeftForeArm.IK_CTRL), "%s.inputX" %(self.LeftForeArm.parent_Global_Constraint_Reverse))
        mayac.connectAttr("%s.ParentToGlobal" %(self.LeftForeArm.IK_CTRL), "%s.%sW1" %(self.LeftForeArm.parent_Global_Constraint, self.global_CTRL))
        mayac.connectAttr("%s.outputX" %(self.LeftForeArm.parent_Global_Constraint_Reverse), "%s.%sW0" %(self.LeftForeArm.parent_Global_Constraint, self.LeftForeArm.IK_CTRL_parent_POS_GRP))
        mayac.setAttr("%s.interpType" %(self.LeftForeArm.parent_Global_Constraint), 2)
        
        temp = mayac.parentConstraint(self.RightForeArm.IK_CTRL_parent_POS_GRP, self.RightForeArm.IK_CTRL_parent_Global_POS_GRP, maintainOffset = True)
        self.RightForeArm.parent_Global_Constraint = temp[0]
        mayac.parentConstraint(self.global_CTRL, self.RightForeArm.IK_CTRL_parent_Global_POS_GRP, maintainOffset = True)
        self.RightForeArm.parent_Global_Constraint_Reverse = mayac.createNode( 'reverse', n="RightForeArm_parent_Global_Constraint_Reverse")
        mayac.connectAttr("%s.ParentToGlobal" %(self.RightForeArm.IK_CTRL), "%s.inputX" %(self.RightForeArm.parent_Global_Constraint_Reverse))
        mayac.connectAttr("%s.ParentToGlobal" %(self.RightForeArm.IK_CTRL), "%s.%sW1" %(self.RightForeArm.parent_Global_Constraint, self.global_CTRL))
        mayac.connectAttr("%s.outputX" %(self.RightForeArm.parent_Global_Constraint_Reverse), "%s.%sW0" %(self.RightForeArm.parent_Global_Constraint, self.RightForeArm.IK_CTRL_parent_POS_GRP))
        mayac.setAttr("%s.interpType" %(self.RightForeArm.parent_Global_Constraint), 2)
        
        
        
        #IK Elbows and Knees to Hands and feet     
        temp = mayac.parentConstraint(self.LeftFoot.IK_CTRL, self.LeftLeg.Follow_Foot_GRP, maintainOffset = True)
        self.LeftLeg.Follow_Foot_Constraint = temp[0]
        temp = mayac.parentConstraint(self.LeftLeg.IK_CTRL_animData_CONST_GRP, self.LeftLeg.IK_CTRL_inRig_CONST_GRP, maintainOffset = False)
        self.LeftLeg.follow_extremity_Constraint = temp[0]
        mayac.parentConstraint(self.LeftLeg.Follow_Knee_GRP, self.LeftLeg.IK_CTRL_inRig_CONST_GRP, maintainOffset = False)
        self.LeftLeg.follow_extremity_Constraint_Reverse = mayac.createNode( 'reverse', n="LeftLeg_follow_extremity_Constraint_Reverse")
        mayac.connectAttr("%s.FollowFoot" %(self.LeftLeg.IK_CTRL), "%s.inputX" %(self.LeftLeg.follow_extremity_Constraint_Reverse))
        mayac.connectAttr("%s.FollowFoot" %(self.LeftLeg.IK_CTRL), "%s.%sW1" %(self.LeftLeg.follow_extremity_Constraint, self.LeftLeg.Follow_Knee_GRP))
        mayac.connectAttr("%s.outputX" %(self.LeftLeg.follow_extremity_Constraint_Reverse), "%s.%sW0" %(self.LeftLeg.follow_extremity_Constraint, self.LeftLeg.IK_CTRL_animData_CONST_GRP))
        mayac.setAttr("%s.interpType" %(self.LeftLeg.follow_extremity_Constraint), 2)
        
        temp = mayac.parentConstraint(self.RightFoot.IK_CTRL, self.RightLeg.Follow_Foot_GRP, maintainOffset = True)
        self.RightLeg.Follow_Foot_Constraint = temp[0]
        temp = mayac.parentConstraint(self.RightLeg.IK_CTRL_animData_CONST_GRP, self.RightLeg.IK_CTRL_inRig_CONST_GRP, maintainOffset = False)
        self.RightLeg.follow_extremity_Constraint = temp[0]
        mayac.parentConstraint(self.RightLeg.Follow_Knee_GRP, self.RightLeg.IK_CTRL_inRig_CONST_GRP, maintainOffset = False)
        self.RightLeg.follow_extremity_Constraint_Reverse = mayac.createNode( 'reverse', n="RightLeg_follow_extremity_Constraint_Reverse")
        mayac.connectAttr("%s.FollowFoot" %(self.RightLeg.IK_CTRL), "%s.inputX" %(self.RightLeg.follow_extremity_Constraint_Reverse))
        mayac.connectAttr("%s.FollowFoot" %(self.RightLeg.IK_CTRL), "%s.%sW1" %(self.RightLeg.follow_extremity_Constraint, self.RightLeg.Follow_Knee_GRP))
        mayac.connectAttr("%s.outputX" %(self.RightLeg.follow_extremity_Constraint_Reverse), "%s.%sW0" %(self.RightLeg.follow_extremity_Constraint, self.RightLeg.IK_CTRL_animData_CONST_GRP))
        mayac.setAttr("%s.interpType" %(self.RightLeg.follow_extremity_Constraint), 2)
        
        temp = mayac.parentConstraint(self.LeftForeArm.IK_CTRL_animData_CONST_GRP, self.LeftForeArm.IK_CTRL_inRig_CONST_GRP, maintainOffset = True)
        self.LeftForeArm.follow_extremity_Constraint = temp[0]
        mayac.parentConstraint(self.LeftHand.IK_CTRL, self.LeftForeArm.IK_CTRL_inRig_CONST_GRP, maintainOffset = True)
        self.LeftForeArm.follow_extremity_Constraint_Reverse = mayac.createNode( 'reverse', n="LeftForeArm_follow_extremity_Constraint_Reverse")
        mayac.connectAttr("%s.FollowHand" %(self.LeftForeArm.IK_CTRL), "%s.inputX" %(self.LeftForeArm.follow_extremity_Constraint_Reverse))
        mayac.connectAttr("%s.FollowHand" %(self.LeftForeArm.IK_CTRL), "%s.%sW1" %(self.LeftForeArm.follow_extremity_Constraint, self.LeftHand.IK_CTRL))
        mayac.connectAttr("%s.outputX" %(self.LeftForeArm.follow_extremity_Constraint_Reverse), "%s.%sW0" %(self.LeftForeArm.follow_extremity_Constraint, self.LeftForeArm.IK_CTRL_animData_CONST_GRP))
        mayac.setAttr("%s.interpType" %(self.LeftForeArm.follow_extremity_Constraint), 2)
        
        temp = mayac.parentConstraint(self.RightForeArm.IK_CTRL_animData_CONST_GRP, self.RightForeArm.IK_CTRL_inRig_CONST_GRP, maintainOffset = True)
        self.RightForeArm.follow_extremity_Constraint = temp[0]
        mayac.parentConstraint(self.RightHand.IK_CTRL, self.RightForeArm.IK_CTRL_inRig_CONST_GRP, maintainOffset = True)
        self.RightForeArm.follow_extremity_Constraint_Reverse = mayac.createNode( 'reverse', n="RightForeArm_follow_extremity_Constraint_Reverse")
        mayac.connectAttr("%s.FollowHand" %(self.RightForeArm.IK_CTRL), "%s.inputX" %(self.RightForeArm.follow_extremity_Constraint_Reverse))
        mayac.connectAttr("%s.FollowHand" %(self.RightForeArm.IK_CTRL), "%s.%sW1" %(self.RightForeArm.follow_extremity_Constraint, self.RightHand.IK_CTRL))
        mayac.connectAttr("%s.outputX" %(self.RightForeArm.follow_extremity_Constraint_Reverse), "%s.%sW0" %(self.RightForeArm.follow_extremity_Constraint, self.RightForeArm.IK_CTRL_animData_CONST_GRP))
        mayac.setAttr("%s.interpType" %(self.RightForeArm.follow_extremity_Constraint), 2)
        

        
        #IK feet
        self.Left_Ankle_IK_CTRL = DJB_createGroup(transform = None, suffix = None, fullName ="Left_Ankle_IK_CTRL", pivotFrom = self.LeftToeBase.Bind_Joint)
        self.Left_ToeBase_IK_CTRL = DJB_createGroup(transform = None, suffix = None, fullName ="Left_ToeBase_IK_CTRL", pivotFrom = self.LeftToeBase.Bind_Joint)
        self.Left_ToeBase_IK_AnimData_GRP = DJB_createGroup(transform = self.Left_ToeBase_IK_CTRL, suffix = None, fullName ="Left_ToeBase_IK_AnimData_GRP")
        self.Left_Ankle_IK_AnimData_GRP = DJB_createGroup(transform = self.Left_Ankle_IK_CTRL, suffix = None, fullName ="Left_Ankle_IK_AnimData_GRP")
        self.Left_Toe_IK_CTRL = DJB_createGroup(transform = None, suffix = None, fullName ="Left_Toe_End_IK_CTRL", pivotFrom = self.LeftToe_End.Bind_Joint)
        self.Left_Toe_IK_AnimData_GRP = DJB_createGroup(transform = self.Left_Toe_IK_CTRL, suffix = None, fullName ="Left_Toe_IK_AnimData_GRP")   
        #set rotation orders
        mayac.setAttr("%s.rotateOrder" % (self.Left_Ankle_IK_CTRL), self.LeftFoot.rotOrder)
        mayac.setAttr("%s.rotateOrder" % (self.Left_ToeBase_IK_CTRL), self.LeftToeBase.rotOrder)
        mayac.setAttr("%s.rotateOrder" % (self.Left_ToeBase_IK_AnimData_GRP), self.LeftToeBase.rotOrder)
        mayac.setAttr("%s.rotateOrder" % (self.Left_Ankle_IK_AnimData_GRP), self.LeftFoot.rotOrder)
        mayac.setAttr("%s.rotateOrder" % (self.Left_Toe_IK_CTRL), self.LeftToeBase.rotOrder)
        mayac.setAttr("%s.rotateOrder" % (self.Left_Toe_IK_AnimData_GRP), self.LeftToeBase.rotOrder)
        
        
        #handle     
        temp = mayac.ikHandle( n="Left_ToeBase_IkHandle", sj= self.LeftFoot.IK_Joint, ee= self.LeftToeBase.IK_Joint, solver = "ikSCsolver", weight = 1)
        self.Left_ToeBase_IkHandle = temp[0]
        mayac.setAttr("%s.visibility" % (self.Left_ToeBase_IkHandle), 0)

        mayac.parent(self.Left_Toe_IK_AnimData_GRP, self.LeftFoot.IK_CTRL)
        mayac.parent(self.Left_ToeBase_IK_AnimData_GRP, self.Left_Toe_IK_CTRL)
        mayac.parent(self.Left_Ankle_IK_AnimData_GRP, self.Left_Toe_IK_CTRL)
        mayac.parent(self.LeftFoot.IK_Handle, self.Left_Ankle_IK_CTRL)
        mayac.parent(self.Left_ToeBase_IkHandle, self.Left_Ankle_IK_CTRL)
        mayac.orientConstraint(self.Left_Toe_IK_CTRL, self.LeftToe_End.IK_Joint)
        mayac.orientConstraint(self.Left_ToeBase_IK_CTRL, self.LeftToeBase.IK_Joint)
        mayac.delete(self.LeftFoot.IK_Constraint)
        self.LeftFoot.IK_Constraint = None
        mayac.orientConstraint(self.Left_Ankle_IK_CTRL, self.LeftFoot.IK_Joint)
        
        self.Left_IK_ToeBase_animData_MultNode = mayac.createNode( 'multiplyDivide', n="Left_IK_ToeBase_animData_MultNode")
        mayac.connectAttr("%s.rotateX" %(self.LeftToeBase.AnimData_Joint), "%s.input1X" %(self.Left_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.AnimDataMult" %(self.LeftFoot.IK_CTRL), "%s.input2X" %(self.Left_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.rotateY" %(self.LeftToeBase.AnimData_Joint), "%s.input1Y" %(self.Left_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.AnimDataMult" %(self.LeftFoot.IK_CTRL), "%s.input2Y" %(self.Left_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.rotateZ" %(self.LeftToeBase.AnimData_Joint), "%s.input1Z" %(self.Left_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.AnimDataMult" %(self.LeftFoot.IK_CTRL), "%s.input2Z" %(self.Left_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.outputX" %(self.Left_IK_ToeBase_animData_MultNode), "%s.rotateX" %(self.Left_ToeBase_IK_AnimData_GRP), force = True)
        mayac.connectAttr("%s.outputY" %(self.Left_IK_ToeBase_animData_MultNode), "%s.rotateY" %(self.Left_ToeBase_IK_AnimData_GRP), force = True)
        mayac.connectAttr("%s.outputZ" %(self.Left_IK_ToeBase_animData_MultNode), "%s.rotateZ" %(self.Left_ToeBase_IK_AnimData_GRP), force = True)
    
        self.Right_Ankle_IK_CTRL = DJB_createGroup(transform = None, suffix = None, fullName ="Right_Ankle_IK_CTRL", pivotFrom = self.RightToeBase.Bind_Joint)
        self.Right_ToeBase_IK_CTRL = DJB_createGroup(transform = None, suffix = None, fullName ="Right_ToeBase_IK_CTRL", pivotFrom = self.RightToeBase.Bind_Joint)
        self.Right_ToeBase_IK_AnimData_GRP = DJB_createGroup(transform = self.Right_ToeBase_IK_CTRL, suffix = None, fullName ="Right_ToeBase_IK_AnimData_GRP")
        self.Right_Ankle_IK_AnimData_GRP = DJB_createGroup(transform = self.Right_Ankle_IK_CTRL, suffix = None, fullName ="Right_Ankle_IK_AnimData_GRP")
        self.Right_Toe_IK_CTRL = DJB_createGroup(transform = None, suffix = None, fullName ="Right_Toe_End_IK_CTRL", pivotFrom = self.RightToe_End.Bind_Joint)
        self.Right_Toe_IK_AnimData_GRP = DJB_createGroup(transform = self.Right_Toe_IK_CTRL, suffix = None, fullName ="Right_Toe_IK_AnimData_GRP")            
        #set rotation orders
        mayac.setAttr("%s.rotateOrder" % (self.Right_Ankle_IK_CTRL), self.LeftFoot.rotOrder)
        mayac.setAttr("%s.rotateOrder" % (self.Right_ToeBase_IK_CTRL), self.LeftToeBase.rotOrder)
        mayac.setAttr("%s.rotateOrder" % (self.Right_ToeBase_IK_AnimData_GRP), self.LeftToeBase.rotOrder)
        mayac.setAttr("%s.rotateOrder" % (self.Right_Ankle_IK_AnimData_GRP), self.LeftFoot.rotOrder)
        mayac.setAttr("%s.rotateOrder" % (self.Right_Toe_IK_CTRL), self.LeftToeBase.rotOrder)
        mayac.setAttr("%s.rotateOrder" % (self.Right_Toe_IK_AnimData_GRP), self.LeftToeBase.rotOrder)
        #IK Handle
        temp = mayac.ikHandle( n="Right_ToeBase_IkHandle", sj= self.RightFoot.IK_Joint, ee= self.RightToeBase.IK_Joint, solver = "ikSCsolver", weight = 1)
        self.Right_ToeBase_IkHandle = temp[0]
        mayac.setAttr("%s.visibility" % (self.Right_ToeBase_IkHandle), 0)

        
        mayac.parent(self.Right_Toe_IK_AnimData_GRP, self.RightFoot.IK_CTRL)
        mayac.parent(self.Right_ToeBase_IK_AnimData_GRP, self.Right_Toe_IK_CTRL)
        mayac.parent(self.Right_Ankle_IK_AnimData_GRP, self.Right_Toe_IK_CTRL)
        mayac.parent(self.RightFoot.IK_Handle, self.Right_Ankle_IK_CTRL)
        mayac.parent(self.Right_ToeBase_IkHandle, self.Right_Ankle_IK_CTRL)
        mayac.orientConstraint(self.Right_Toe_IK_CTRL, self.RightToe_End.IK_Joint)
        mayac.orientConstraint(self.Right_ToeBase_IK_CTRL, self.RightToeBase.IK_Joint)
        mayac.delete(self.RightFoot.IK_Constraint)
        self.RightFoot.IK_Constraint = None
        mayac.orientConstraint(self.Right_Ankle_IK_CTRL, self.RightFoot.IK_Joint)
        
        self.Right_IK_ToeBase_animData_MultNode = mayac.createNode( 'multiplyDivide', n="Right_IK_ToeBase_animData_MultNode")
        mayac.connectAttr("%s.rotateX" %(self.RightToeBase.AnimData_Joint), "%s.input1X" %(self.Right_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.AnimDataMult" %(self.RightFoot.IK_CTRL), "%s.input2X" %(self.Right_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.rotateY" %(self.RightToeBase.AnimData_Joint), "%s.input1Y" %(self.Right_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.AnimDataMult" %(self.RightFoot.IK_CTRL), "%s.input2Y" %(self.Right_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.rotateZ" %(self.RightToeBase.AnimData_Joint), "%s.input1Z" %(self.Right_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.AnimDataMult" %(self.RightFoot.IK_CTRL), "%s.input2Z" %(self.Right_IK_ToeBase_animData_MultNode), force = True)
        mayac.connectAttr("%s.outputX" %(self.Right_IK_ToeBase_animData_MultNode), "%s.rotateX" %(self.Right_ToeBase_IK_AnimData_GRP), force = True)
        mayac.connectAttr("%s.outputY" %(self.Right_IK_ToeBase_animData_MultNode), "%s.rotateY" %(self.Right_ToeBase_IK_AnimData_GRP), force = True)
        mayac.connectAttr("%s.outputZ" %(self.Right_IK_ToeBase_animData_MultNode), "%s.rotateZ" %(self.Right_ToeBase_IK_AnimData_GRP), force = True)

        #Zero offsets on Foot Constraints
        mayac.setAttr("%s.offsetX" % (self.LeftFoot.Constraint), 0)
        mayac.setAttr("%s.offsetY" % (self.LeftFoot.Constraint), 0)
        mayac.setAttr("%s.offsetZ" % (self.LeftFoot.Constraint), 0)
        mayac.setAttr("%s.offsetX" % (self.RightFoot.Constraint), 0)
        mayac.setAttr("%s.offsetY" % (self.RightFoot.Constraint), 0)
        mayac.setAttr("%s.offsetZ" % (self.RightFoot.Constraint), 0)

        #attr connections to foot controls
        if self.rigType == "AutoRig":
            self.LeftFoot_FootRoll_MultNode = mayac.createNode( 'multiplyDivide', n="LeftFoot_FootRoll_MultNode")
            mayac.setAttr("%s.input2X" %(self.LeftFoot_FootRoll_MultNode), -1)
            mayac.connectAttr("%s.FootRoll" %(self.LeftFoot.IK_CTRL), "%s.input1X" %(self.LeftFoot_FootRoll_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.LeftFoot_FootRoll_MultNode), "%s.rotateX" %(self.Left_Ankle_IK_CTRL), force = True)
    
            mayac.connectAttr("%s.ToeTap" %(self.LeftFoot.IK_CTRL), "%s.rotateX" %(self.Left_ToeBase_IK_CTRL), force = True)
            Left_ToeBase_ZAdd = mayac.shadingNode('plusMinusAverage', asUtility=True, n = "Left_ToeBase_ZAdd")
            mayac.connectAttr("%s.ToeSideToSide" %(self.LeftFoot.IK_CTRL), "%s.input1D[0]" %(Left_ToeBase_ZAdd), force = True)
            mayac.connectAttr("%s.output1D" %(Left_ToeBase_ZAdd), "%s.rotateZ" %(self.Left_ToeBase_IK_CTRL), force = True)
            mayac.connectAttr("%s.ToeRotate" %(self.LeftFoot.IK_CTRL), "%s.rotateY" %(self.Left_ToeBase_IK_CTRL), force = True)
            
            self.LeftFoot_ToeRoll_MultNode = mayac.createNode( 'multiplyDivide', n="LeftFoot_ToeRoll_MultNode")
            mayac.setAttr("%s.input2X" %(self.LeftFoot_ToeRoll_MultNode), -1)
            mayac.connectAttr("%s.ToeRoll" %(self.LeftFoot.IK_CTRL), "%s.input1X" %(self.LeftFoot_ToeRoll_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.LeftFoot_ToeRoll_MultNode), "%s.rotateX" %(self.Left_Toe_IK_CTRL), force = True)
            
            mayac.connectAttr("%s.HipPivot" %(self.LeftFoot.IK_CTRL), "%s.rotateY" %(self.LeftFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)
    
            mayac.connectAttr("%s.BallPivot" %(self.LeftFoot.IK_CTRL), "%s.input1D[1]" %(Left_ToeBase_ZAdd), force = True)
            mayac.connectAttr("%s.BallPivot" %(self.LeftFoot.IK_CTRL), "%s.rotateZ" %(self.Left_Ankle_IK_CTRL), force = True)
            
            mayac.connectAttr("%s.ToePivot" %(self.LeftFoot.IK_CTRL), "%s.rotateZ" %(self.Left_Toe_IK_CTRL), force = True)
            
            mayac.connectAttr("%s.HipSideToSide" %(self.LeftFoot.IK_CTRL), "%s.rotateZ" %(self.LeftFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)
    
            mayac.connectAttr("%s.HipBackToFront" %(self.LeftFoot.IK_CTRL), "%s.rotateX" %(self.LeftFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)
        
        
            self.RightFoot_FootRoll_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_FootRoll_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_FootRoll_MultNode), -1)
            mayac.connectAttr("%s.FootRoll" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_FootRoll_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_FootRoll_MultNode), "%s.rotateX" %(self.Right_Ankle_IK_CTRL), force = True)
    
            mayac.connectAttr("%s.ToeTap" %(self.RightFoot.IK_CTRL), "%s.rotateX" %(self.Right_ToeBase_IK_CTRL), force = True)
            Right_ToeBase_ZAdd = mayac.shadingNode('plusMinusAverage', asUtility=True, n = "Right_ToeBase_ZAdd")
            mayac.connectAttr("%s.ToeSideToSide" %(self.RightFoot.IK_CTRL), "%s.input1D[0]" %(Right_ToeBase_ZAdd), force = True)
            mayac.connectAttr("%s.output1D" %(Right_ToeBase_ZAdd), "%s.rotateZ" %(self.Right_ToeBase_IK_CTRL), force = True)
            mayac.connectAttr("%s.ToeRotate" %(self.RightFoot.IK_CTRL), "%s.rotateY" %(self.Right_ToeBase_IK_CTRL), force = True)
    
            self.RightFoot_ToeRoll_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_ToeRoll_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_ToeRoll_MultNode), -1)
            mayac.connectAttr("%s.ToeRoll" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_ToeRoll_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_ToeRoll_MultNode), "%s.rotateX" %(self.Right_Toe_IK_CTRL), force = True)
            
            self.RightFoot_HipPivot_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_HipPivot_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_HipPivot_MultNode), -1)
            mayac.connectAttr("%s.HipPivot" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_HipPivot_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_HipPivot_MultNode), "%s.rotateY" %(self.RightFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)
            
            self.RightFoot_BallPivot_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_BallPivot_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_BallPivot_MultNode), -1)
            mayac.connectAttr("%s.BallPivot" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_BallPivot_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_BallPivot_MultNode), "%s.input1D[1]" %(Right_ToeBase_ZAdd), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_BallPivot_MultNode), "%s.rotateZ" %(self.Right_Ankle_IK_CTRL), force = True)
            
            self.RightFoot_ToePivot_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_ToePivot_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_ToePivot_MultNode), -1)
            mayac.connectAttr("%s.ToePivot" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_ToePivot_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_ToePivot_MultNode), "%s.rotateZ" %(self.Right_Toe_IK_CTRL), force = True)
            
            self.RightFoot_HipSideToSide_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_HipSideToSide_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_HipSideToSide_MultNode), -1)
            mayac.connectAttr("%s.HipSideToSide" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_HipSideToSide_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_HipSideToSide_MultNode), "%s.rotateZ" %(self.RightFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)
            
            mayac.connectAttr("%s.HipBackToFront" %(self.RightFoot.IK_CTRL), "%s.rotateX" %(self.RightFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)
        
        
        
        
        elif self.rigType == "World":
            self.LeftFoot_FootRoll_MultNode = mayac.createNode( 'multiplyDivide', n="LeftFoot_FootRoll_MultNode")
            mayac.setAttr("%s.input2X" %(self.LeftFoot_FootRoll_MultNode), 1)
            mayac.connectAttr("%s.FootRoll" %(self.LeftFoot.IK_CTRL), "%s.input1X" %(self.LeftFoot_FootRoll_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.LeftFoot_FootRoll_MultNode), "%s.rotateX" %(self.Left_Ankle_IK_CTRL), force = True)
    
            LeftFoot_ToeTap_MultNode = mayac.createNode( 'multiplyDivide', n="LeftFoot_ToeTap_MultNode")
            mayac.setAttr("%s.input2X" %(LeftFoot_ToeTap_MultNode), -1)
            mayac.connectAttr("%s.ToeTap" %(self.LeftFoot.IK_CTRL), "%s.input1X" %(LeftFoot_ToeTap_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(LeftFoot_ToeTap_MultNode), "%s.rotateX" %(self.Left_ToeBase_IK_CTRL), force = True)
            
            Left_ToeBase_ZAdd = mayac.shadingNode('plusMinusAverage', asUtility=True, n = "Left_ToeBase_ZAdd")
            mayac.connectAttr("%s.ToeSideToSide" %(self.LeftFoot.IK_CTRL), "%s.input1D[0]" %(Left_ToeBase_ZAdd), force = True)
            mayac.connectAttr("%s.output1D" %(Left_ToeBase_ZAdd), "%s.rotateY" %(self.Left_ToeBase_IK_CTRL), force = True)
            mayac.connectAttr("%s.ToeRotate" %(self.LeftFoot.IK_CTRL), "%s.rotateZ" %(self.Left_ToeBase_IK_CTRL), force = True)
            
            self.LeftFoot_ToeRoll_MultNode = mayac.createNode( 'multiplyDivide', n="LeftFoot_ToeRoll_MultNode")
            mayac.setAttr("%s.input2X" %(self.LeftFoot_ToeRoll_MultNode), 1)
            mayac.connectAttr("%s.ToeRoll" %(self.LeftFoot.IK_CTRL), "%s.input1X" %(self.LeftFoot_ToeRoll_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.LeftFoot_ToeRoll_MultNode), "%s.rotateX" %(self.Left_Toe_IK_CTRL), force = True)
            
            mayac.connectAttr("%s.HipPivot" %(self.LeftFoot.IK_CTRL), "%s.rotateY" %(self.LeftFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)
    
            mayac.connectAttr("%s.BallPivot" %(self.LeftFoot.IK_CTRL), "%s.input1D[1]" %(Left_ToeBase_ZAdd), force = True)
            mayac.connectAttr("%s.BallPivot" %(self.LeftFoot.IK_CTRL), "%s.rotateY" %(self.Left_Ankle_IK_CTRL), force = True)
            
            mayac.connectAttr("%s.ToePivot" %(self.LeftFoot.IK_CTRL), "%s.rotateY" %(self.Left_Toe_IK_CTRL), force = True)
            
            mayac.connectAttr("%s.HipSideToSide" %(self.LeftFoot.IK_CTRL), "%s.rotateZ" %(self.LeftFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)
    
            mayac.connectAttr("%s.HipBackToFront" %(self.LeftFoot.IK_CTRL), "%s.rotateX" %(self.LeftFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)
            
            
            self.RightFoot_FootRoll_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_FootRoll_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_FootRoll_MultNode), 1)
            mayac.connectAttr("%s.FootRoll" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_FootRoll_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_FootRoll_MultNode), "%s.rotateX" %(self.Right_Ankle_IK_CTRL), force = True)
    
            RightFoot_ToeTap_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_ToeTap_MultNode")
            mayac.setAttr("%s.input2X" %(RightFoot_ToeTap_MultNode), -1)
            mayac.connectAttr("%s.ToeTap" %(self.RightFoot.IK_CTRL), "%s.input1X" %(RightFoot_ToeTap_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(RightFoot_ToeTap_MultNode), "%s.rotateX" %(self.Right_ToeBase_IK_CTRL), force = True)
            
            Right_ToeBase_ZAdd = mayac.shadingNode('plusMinusAverage', asUtility=True, n = "Right_ToeBase_ZAdd")
            mayac.connectAttr("%s.ToeSideToSide" %(self.RightFoot.IK_CTRL), "%s.input1D[0]" %(Right_ToeBase_ZAdd), force = True)
            mayac.connectAttr("%s.output1D" %(Right_ToeBase_ZAdd), "%s.rotateY" %(self.Right_ToeBase_IK_CTRL), force = True)
            mayac.connectAttr("%s.ToeRotate" %(self.RightFoot.IK_CTRL), "%s.rotateZ" %(self.Right_ToeBase_IK_CTRL), force = True)
    
            self.RightFoot_ToeRoll_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_ToeRoll_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_ToeRoll_MultNode), 1)
            mayac.connectAttr("%s.ToeRoll" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_ToeRoll_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_ToeRoll_MultNode), "%s.rotateX" %(self.Right_Toe_IK_CTRL), force = True)
            
            self.RightFoot_HipPivot_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_HipPivot_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_HipPivot_MultNode), -1)
            mayac.connectAttr("%s.HipPivot" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_HipPivot_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_HipPivot_MultNode), "%s.rotateY" %(self.RightFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)
            
            self.RightFoot_BallPivot_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_BallPivot_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_BallPivot_MultNode), -1)
            mayac.connectAttr("%s.BallPivot" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_BallPivot_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_BallPivot_MultNode), "%s.input1D[1]" %(Right_ToeBase_ZAdd), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_BallPivot_MultNode), "%s.rotateY" %(self.Right_Ankle_IK_CTRL), force = True)
            
            self.RightFoot_ToePivot_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_ToePivot_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_ToePivot_MultNode), -1)
            mayac.connectAttr("%s.ToePivot" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_ToePivot_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_ToePivot_MultNode), "%s.rotateY" %(self.Right_Toe_IK_CTRL), force = True)
            
            self.RightFoot_HipSideToSide_MultNode = mayac.createNode( 'multiplyDivide', n="RightFoot_HipSideToSide_MultNode")
            mayac.setAttr("%s.input2X" %(self.RightFoot_HipSideToSide_MultNode), -1)
            mayac.connectAttr("%s.HipSideToSide" %(self.RightFoot.IK_CTRL), "%s.input1X" %(self.RightFoot_HipSideToSide_MultNode), force = True)
            mayac.connectAttr("%s.outputX" %(self.RightFoot_HipSideToSide_MultNode), "%s.rotateZ" %(self.RightFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)
            
            mayac.connectAttr("%s.HipBackToFront" %(self.RightFoot.IK_CTRL), "%s.rotateX" %(self.RightFoot.IK_CTRL_grandparent_inRig_CONST_GRP), force = True)


        
        
        #finger SDKs
        if self.rigType == "AutoRig":
            if self.LeftHandIndex1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -30.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 12.0)
            else:
                mayac.deleteAttr("%s.IndexCurl"  % (self.LeftHand.Options_CTRL))
            if self.LeftHandMiddle1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -10.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 3.0)
            else:
                mayac.deleteAttr("%s.MiddleCurl"  % (self.LeftHand.Options_CTRL))    
            if self.LeftHandRing1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 15.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -5.0)
            else:
                mayac.deleteAttr("%s.RingCurl"  % (self.LeftHand.Options_CTRL))      
            if self.LeftHandPinky1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.LeftHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 30.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -13.0)
            else:
                mayac.deleteAttr("%s.PinkyCurl"  % (self.LeftHand.Options_CTRL))    
            if self.LeftHandThumb1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 25.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -25.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 60.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -60.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -15.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 15.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 30.0)
            else:
                mayac.deleteAttr("%s.ThumbCurl"  % (self.LeftHand.Options_CTRL))
            if not self.LeftHandPinky1.Bind_Joint and not self.LeftHandRing1.Bind_Joint and not self.LeftHandMiddle1.Bind_Joint and not self.LeftHandIndex1.Bind_Joint:
                mayac.deleteAttr("%s.Sway"  % (self.LeftHand.Options_CTRL))
                if not self.LeftHandThumb1.Bind_Joint:
                    mayac.deleteAttr("%s.Spread"  % (self.LeftHand.Options_CTRL))
                    
                    
            if self.RightHandIndex1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 30.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -12.0)
            else:
                mayac.deleteAttr("%s.IndexCurl"  % (self.RightHand.Options_CTRL))
            if self.RightHandMiddle1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 10.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -3.0)
            else:
                mayac.deleteAttr("%s.MiddleCurl"  % (self.RightHand.Options_CTRL))    
            if self.RightHandRing1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -15.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 5.0)
            else:
                mayac.deleteAttr("%s.RingCurl"  % (self.RightHand.Options_CTRL))      
            if self.RightHandPinky1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateX" % (self.RightHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -30.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 13.0)
            else:
                mayac.deleteAttr("%s.PinkyCurl"  % (self.RightHand.Options_CTRL))    
            if self.RightHandThumb1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -25.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 25.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -60.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 60.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 15.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -15.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -30.0)
            else:
                mayac.deleteAttr("%s.ThumbCurl"  % (self.RightHand.Options_CTRL))
            if not self.RightHandPinky1.Bind_Joint and not self.RightHandRing1.Bind_Joint and not self.RightHandMiddle1.Bind_Joint and not self.RightHandIndex1.Bind_Joint:
                mayac.deleteAttr("%s.Sway"  % (self.RightHand.Options_CTRL))
                if not self.RightHandThumb1.Bind_Joint:
                    mayac.deleteAttr("%s.Spread"  % (self.RightHand.Options_CTRL))

        elif self.rigType == "World":
            if self.LeftHandIndex1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -30.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 12.0)
            else:
                mayac.deleteAttr("%s.IndexCurl"  % (self.LeftHand.Options_CTRL))
            if self.LeftHandMiddle1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -10.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 3.0)
            else:
                mayac.deleteAttr("%s.MiddleCurl"  % (self.LeftHand.Options_CTRL))    
            if self.LeftHandRing1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 15.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -5.0)
            else:
                mayac.deleteAttr("%s.RingCurl"  % (self.LeftHand.Options_CTRL))      
            if self.LeftHandPinky1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.LeftHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 30.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -13.0)
            else:
                mayac.deleteAttr("%s.PinkyCurl"  % (self.LeftHand.Options_CTRL))    
            if self.LeftHandThumb1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 25.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -25.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 60.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -60.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = 10.0, value = -15.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 15.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.LeftHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.LeftHand.Options_CTRL), driverValue = -10.0, value = 30.0)
            else:
                mayac.deleteAttr("%s.ThumbCurl"  % (self.LeftHand.Options_CTRL))
            if not self.LeftHandPinky1.Bind_Joint and not self.LeftHandRing1.Bind_Joint and not self.LeftHandMiddle1.Bind_Joint and not self.LeftHandIndex1.Bind_Joint:
                mayac.deleteAttr("%s.Sway"  % (self.LeftHand.Options_CTRL))
                if not self.LeftHandThumb1.Bind_Joint:
                    mayac.deleteAttr("%s.Spread"  % (self.LeftHand.Options_CTRL))
                    
                    
            if self.RightHandIndex1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandIndex3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.IndexCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 30.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandIndex1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -12.0)
            else:
                mayac.deleteAttr("%s.IndexCurl"  % (self.RightHand.Options_CTRL))
            if self.RightHandMiddle1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandMiddle3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.MiddleCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 10.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandMiddle1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -3.0)
            else:
                mayac.deleteAttr("%s.MiddleCurl"  % (self.RightHand.Options_CTRL))    
            if self.RightHandRing1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandRing3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.RingCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -15.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandRing1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 5.0)
            else:
                mayac.deleteAttr("%s.RingCurl"  % (self.RightHand.Options_CTRL))      
            if self.RightHandPinky1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateZ" % (self.RightHandPinky3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.PinkyCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Sway"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 45.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -30.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandPinky1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 13.0)
            else:
                mayac.deleteAttr("%s.PinkyCurl"  % (self.RightHand.Options_CTRL))    
            if self.RightHandThumb1.Bind_Joint:
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -25.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 25.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -60.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 60.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = -90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb3.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.ThumbCurl"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = 90.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 0.0, value = 0.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = 10.0, value = 15.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb1.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -15.0)
                mayac.setDrivenKeyframe( "%s.rotateY" % (self.RightHandThumb2.FK_CTRL_inRig_CONST_GRP), currentDriver="%s.Spread"  % (self.RightHand.Options_CTRL), driverValue = -10.0, value = -30.0)
            else:
                mayac.deleteAttr("%s.ThumbCurl"  % (self.RightHand.Options_CTRL))
            if not self.RightHandPinky1.Bind_Joint and not self.RightHandRing1.Bind_Joint and not self.RightHandMiddle1.Bind_Joint and not self.RightHandIndex1.Bind_Joint:
                mayac.deleteAttr("%s.Sway"  % (self.RightHand.Options_CTRL))
                if not self.RightHandThumb1.Bind_Joint:
                    mayac.deleteAttr("%s.Spread"  % (self.RightHand.Options_CTRL))
            
            

        
        #global scale
        mayac.scaleConstraint(self.global_CTRL, self.Joint_GRP, name = "Global_Scale_Constraint")
        
        #IKFK switches
        self.LeftArm_Switch_Reverse = mayac.createNode( 'reverse', n="LeftArm_Switch_Reverse")
        self.RightArm_Switch_Reverse = mayac.createNode( 'reverse', n="RightArm_Switch_Reverse")
        self.LeftLeg_Switch_Reverse = mayac.createNode( 'reverse', n="LeftLeg_Switch_Reverse")
        self.RightLeg_Switch_Reverse = mayac.createNode( 'reverse', n="RightLeg_Switch_Reverse")
        mayac.connectAttr("%s.FK_IK" %(self.LeftHand.Options_CTRL), "%s.inputX" %(self.LeftArm_Switch_Reverse))
        mayac.connectAttr("%s.FK_IK" %(self.RightHand.Options_CTRL), "%s.inputX" %(self.RightArm_Switch_Reverse))
        mayac.connectAttr("%s.FK_IK" %(self.LeftFoot.Options_CTRL), "%s.inputX" %(self.LeftLeg_Switch_Reverse))
        mayac.connectAttr("%s.FK_IK" %(self.RightFoot.Options_CTRL), "%s.inputX" %(self.RightLeg_Switch_Reverse))
        
        mayac.setAttr("%s.interpType" %(self.LeftArm.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.LeftForeArm.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.LeftHand.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.RightArm.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.RightForeArm.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.RightHand.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.LeftUpLeg.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.LeftLeg.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.LeftFoot.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.LeftToeBase.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.RightUpLeg.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.RightLeg.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.RightFoot.Constraint), 2)
        mayac.setAttr("%s.interpType" %(self.RightToeBase.Constraint), 2)
        
        mayac.connectAttr("%s.FK_IK" %(self.LeftHand.Options_CTRL), "%s.%sW1" %(self.LeftArm.Constraint, self.LeftArm.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.LeftArm_Switch_Reverse), "%s.%sW0" %(self.LeftArm.Constraint, self.LeftArm.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.LeftHand.Options_CTRL), "%s.%sW1" %(self.LeftForeArm.Constraint, self.LeftForeArm.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.LeftArm_Switch_Reverse), "%s.%sW0" %(self.LeftForeArm.Constraint, self.LeftForeArm.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.LeftHand.Options_CTRL), "%s.%sW1" %(self.LeftHand.Constraint, self.LeftHand.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.LeftArm_Switch_Reverse), "%s.%sW0" %(self.LeftHand.Constraint, self.LeftHand.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.RightHand.Options_CTRL), "%s.%sW1" %(self.RightArm.Constraint, self.RightArm.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.RightArm_Switch_Reverse), "%s.%sW0" %(self.RightArm.Constraint, self.RightArm.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.RightHand.Options_CTRL), "%s.%sW1" %(self.RightForeArm.Constraint, self.RightForeArm.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.RightArm_Switch_Reverse), "%s.%sW0" %(self.RightForeArm.Constraint, self.RightForeArm.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.RightHand.Options_CTRL), "%s.%sW1" %(self.RightHand.Constraint, self.RightHand.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.RightArm_Switch_Reverse), "%s.%sW0" %(self.RightHand.Constraint, self.RightHand.FK_Joint))
        
        mayac.connectAttr("%s.FK_IK" %(self.LeftFoot.Options_CTRL), "%s.%sW1" %(self.LeftUpLeg.Constraint, self.LeftUpLeg.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.LeftLeg_Switch_Reverse), "%s.%sW0" %(self.LeftUpLeg.Constraint, self.LeftUpLeg.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.LeftFoot.Options_CTRL), "%s.%sW1" %(self.LeftLeg.Constraint, self.LeftLeg.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.LeftLeg_Switch_Reverse), "%s.%sW0" %(self.LeftLeg.Constraint, self.LeftLeg.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.LeftFoot.Options_CTRL), "%s.%sW1" %(self.LeftFoot.Constraint, self.LeftFoot.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.LeftLeg_Switch_Reverse), "%s.%sW0" %(self.LeftFoot.Constraint, self.LeftFoot.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.LeftFoot.Options_CTRL), "%s.%sW1" %(self.LeftToeBase.Constraint, self.LeftToeBase.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.LeftLeg_Switch_Reverse), "%s.%sW0" %(self.LeftToeBase.Constraint, self.LeftToeBase.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.RightFoot.Options_CTRL), "%s.%sW1" %(self.RightUpLeg.Constraint, self.RightUpLeg.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.RightLeg_Switch_Reverse), "%s.%sW0" %(self.RightUpLeg.Constraint, self.RightUpLeg.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.RightFoot.Options_CTRL), "%s.%sW1" %(self.RightLeg.Constraint, self.RightLeg.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.RightLeg_Switch_Reverse), "%s.%sW0" %(self.RightLeg.Constraint, self.RightLeg.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.RightFoot.Options_CTRL), "%s.%sW1" %(self.RightFoot.Constraint, self.RightFoot.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.RightLeg_Switch_Reverse), "%s.%sW0" %(self.RightFoot.Constraint, self.RightFoot.FK_Joint))
        mayac.connectAttr("%s.FK_IK" %(self.RightFoot.Options_CTRL), "%s.%sW1" %(self.RightToeBase.Constraint, self.RightToeBase.IK_Joint))
        mayac.connectAttr("%s.outputX" %(self.RightLeg_Switch_Reverse), "%s.%sW0" %(self.RightToeBase.Constraint, self.RightToeBase.FK_Joint))
        
        #FKIK Visibilities
        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.LeftHand.Options_CTRL), "%s.visibility" %(self.LeftArm.IK_Joint))
        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.LeftHand.Options_CTRL), "%s.visibility" %(self.LeftForeArm.IK_CTRL_POS_GRP))
        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.LeftHand.Options_CTRL), "%s.visibility" %(self.LeftHand.IK_CTRL_POS_GRP))
        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.RightHand.Options_CTRL), "%s.visibility" %(self.RightArm.IK_Joint))
        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.RightHand.Options_CTRL), "%s.visibility" %(self.RightForeArm.IK_CTRL_POS_GRP))
        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.RightHand.Options_CTRL), "%s.visibility" %(self.RightHand.IK_CTRL_POS_GRP))

        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.LeftFoot.Options_CTRL), "%s.visibility" %(self.LeftUpLeg.IK_Joint))
        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.LeftFoot.Options_CTRL), "%s.visibility" %(self.LeftLeg.IK_CTRL_POS_GRP))
        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.LeftFoot.Options_CTRL), "%s.visibility" %(self.LeftFoot.IK_CTRL_POS_GRP))
        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.RightFoot.Options_CTRL), "%s.visibility" %(self.RightUpLeg.IK_Joint))
        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.RightFoot.Options_CTRL), "%s.visibility" %(self.RightLeg.IK_CTRL_POS_GRP))
        DJB_Unlock_Connect_Lock("%s.FK_IK" %(self.RightFoot.Options_CTRL), "%s.visibility" %(self.RightFoot.IK_CTRL_POS_GRP))
     
        DJB_Unlock_Connect_Lock("%s.outputX" %(self.LeftArm_Switch_Reverse), "%s.visibility" %(self.LeftArm.FK_Joint))
        DJB_Unlock_Connect_Lock("%s.outputX" %(self.LeftArm_Switch_Reverse), "%s.visibility" %(self.LeftArm.FK_CTRL_POS_GRP))
        DJB_Unlock_Connect_Lock("%s.outputX" %(self.RightArm_Switch_Reverse), "%s.visibility" %(self.RightArm.FK_Joint))
        DJB_Unlock_Connect_Lock("%s.outputX" %(self.RightArm_Switch_Reverse), "%s.visibility" %(self.RightArm.FK_CTRL_POS_GRP))
        
        DJB_Unlock_Connect_Lock("%s.outputX" %(self.LeftLeg_Switch_Reverse), "%s.visibility" %(self.LeftUpLeg.FK_Joint))
        DJB_Unlock_Connect_Lock("%s.outputX" %(self.LeftLeg_Switch_Reverse), "%s.visibility" %(self.LeftUpLeg.FK_CTRL_POS_GRP))
        DJB_Unlock_Connect_Lock("%s.outputX" %(self.RightLeg_Switch_Reverse), "%s.visibility" %(self.RightUpLeg.FK_Joint))
        DJB_Unlock_Connect_Lock("%s.outputX" %(self.RightLeg_Switch_Reverse), "%s.visibility" %(self.RightUpLeg.FK_CTRL_POS_GRP))
        
        mayac.select(clear = True)
        self.Misc_GRP = mayac.group(em = True, name = "Misc_GRP", world = True)
        DJB_movePivotToObject(self.Misc_GRP, self.global_CTRL)
        mayac.parent(self.Misc_GRP, self.Character_GRP)
        self.LeftForeArm.createGuideCurve(self.Misc_GRP, optionsCTRL = self.LeftHand.Options_CTRL)
        self.RightForeArm.createGuideCurve(self.Misc_GRP, optionsCTRL = self.RightHand.Options_CTRL)
        self.LeftLeg.createGuideCurve(self.Misc_GRP, optionsCTRL = self.LeftFoot.Options_CTRL)
        self.RightLeg.createGuideCurve(self.Misc_GRP, optionsCTRL = self.RightFoot.Options_CTRL)

        #Layers
        mayac.select(clear = True)
        self.Mesh_Layer = mayac.createDisplayLayer(name = "MeshLayer", number = 1)
        mayac.editDisplayLayerMembers(self.Mesh_Layer, self.Mesh_GRP)
        self.Bind_Joint_Layer = mayac.createDisplayLayer(name = "BindJointLayer", number = 2)
        mayac.editDisplayLayerMembers(self.Bind_Joint_Layer, self.Bind_Joint_GRP)
        #self.AnimData_Joint_Layer = mayac.createDisplayLayer(name = "AnimDataJointLayer", number = 3)
        #mayac.editDisplayLayerMembers(self.AnimData_Joint_Layer, self.AnimData_Joint_GRP)
        mayac.setAttr("%s.visibility" % (self.AnimData_Joint_GRP), 0)
        self.Control_Layer = mayac.createDisplayLayer(name = "ControlLayer", number = 4)
        mayac.editDisplayLayerMembers(self.Control_Layer, self.CTRL_GRP)
        mayac.editDisplayLayerMembers(self.Control_Layer, self.Misc_GRP)
        mayac.setAttr("%s.visibility" %(self.Mesh_Layer), 1)
        mayac.setAttr("%s.displayType" %(self.Mesh_Layer), 2)
        mayac.setAttr("%s.visibility" %(self.Bind_Joint_Layer), 1)
        mayac.setAttr("%s.displayType" %(self.Bind_Joint_Layer), 2)
        #mayac.setAttr("%s.visibility" %(self.AnimData_Joint_Layer), 0)
        #mayac.setAttr("%s.displayType" %(self.AnimData_Joint_Layer), 2)
        
        for bodyPart in self.bodyParts:
            bodyPart.fixAllLayerOverrides(self.Control_Layer)
        self.Hips.fixLayerOverrides(self.global_CTRL, "black", self.Control_Layer)
        self.Hips.fixLayerOverrides(self.LeftForeArm.Guide_Curve, "black", self.Control_Layer, referenceAlways = True)
        self.Hips.fixLayerOverrides(self.RightForeArm.Guide_Curve, "black", self.Control_Layer, referenceAlways = True)
        self.Hips.fixLayerOverrides(self.LeftLeg.Guide_Curve, "black", self.Control_Layer, referenceAlways = True)
        self.Hips.fixLayerOverrides(self.RightLeg.Guide_Curve, "black", self.Control_Layer, referenceAlways = True)
         
         
        #quick select sets
        mayac.select(clear = True)
        for bodyPart in self.bodyParts:
            if bodyPart.Bind_Joint:
                mayac.select(bodyPart.Bind_Joint, add = True)
        self.Bind_Joint_SelectSet = mayac.sets(text = "gCharacterSet", name = "Bind_Joint_SelectSet")
        #mayac.select(clear = True)
        #for bodyPart in self.bodyParts:
            #if bodyPart.AnimData_Joint:
                #mayac.select(bodyPart.AnimData_Joint, add = True)
        #self.AnimData_Joint_SelectSet = mayac.sets(text = "gCharacterSet", name = "AnimData_Joint_SelectSet")
        mayac.select(clear = True)
        for bodyPart in self.bodyParts:
            if bodyPart.FK_CTRL:
                mayac.select(bodyPart.FK_CTRL, add = True)
            if bodyPart.IK_CTRL:
                mayac.select(bodyPart.IK_CTRL, add = True)
            if bodyPart.Options_CTRL:
                mayac.select(bodyPart.Options_CTRL, add = True)
        mayac.select(self.global_CTRL, add = True)
        self.Controls_SelectSet = mayac.sets(text = "gCharacterSet", name = "Controls_SelectSet")
        mayac.select(clear = True)
        for geo in self.mesh:
            mayac.select(geo, add = True)
        self.Geo_SelectSet = mayac.sets(text = "gCharacterSet", name = "Geo_SelectSet")
        mayac.select(clear = True)
        
        #Cleanup
        mayac.delete(self.LeftFoot.footRotateLOC)
        mayac.delete(self.RightFoot.footRotateLOC)
        DJB_LockNHide(self.Character_GRP)
        DJB_LockNHide(self.CTRL_GRP)
        DJB_LockNHide(self.Joint_GRP)
        DJB_LockNHide(self.Bind_Joint_GRP)
        DJB_LockNHide(self.AnimData_Joint_GRP)
        DJB_LockNHide(self.Mesh_GRP)
        DJB_LockNHide(self.Misc_GRP)
        mayac.setAttr("%s.visibility" % (self.IK_Dummy_Joint_GRP), 0)
        DJB_LockNHide(self.IK_Dummy_Joint_GRP)
        
        DJB_LockNHide(self.Left_ToeBase_IkHandle)
        DJB_LockNHide(self.Right_ToeBase_IkHandle)
        DJB_LockNHide(self.Left_Ankle_IK_CTRL)
        DJB_LockNHide(self.Left_ToeBase_IK_CTRL)
        DJB_LockNHide(self.Left_ToeBase_IK_AnimData_GRP)
        DJB_LockNHide(self.Left_Ankle_IK_AnimData_GRP)
        DJB_LockNHide(self.Left_Toe_IK_CTRL)
        DJB_LockNHide(self.Left_Toe_IK_AnimData_GRP)
        DJB_LockNHide(self.Right_Ankle_IK_CTRL)
        DJB_LockNHide(self.Right_ToeBase_IK_CTRL)
        DJB_LockNHide(self.Right_ToeBase_IK_AnimData_GRP)
        DJB_LockNHide(self.Right_Ankle_IK_AnimData_GRP)
        DJB_LockNHide(self.Right_Toe_IK_CTRL)
        DJB_LockNHide(self.Right_Toe_IK_AnimData_GRP)

        
        
        
        #lock CTRLS
        for bodyPart in self.bodyParts:
            bodyPart.lockUpCTRLs()
        
        #defaultValues
        mayac.setAttr("%s.FK_IK" % (self.LeftFoot.Options_CTRL), 1)
        mayac.setAttr("%s.FK_IK" % (self.RightFoot.Options_CTRL), 1)
        mayac.setAttr("%s.FK_IK" % (self.LeftHand.Options_CTRL), 0)
        mayac.setAttr("%s.FK_IK" % (self.RightHand.Options_CTRL), 0)
        
        mayac.setAttr("%s.FollowBody" % (self.LeftHand.IK_CTRL), 0)
        mayac.setAttr("%s.FollowBody" % (self.RightHand.IK_CTRL), 0)
        mayac.setAttr("%s.FollowBody" % (self.LeftForeArm.IK_CTRL), 0)
        mayac.setAttr("%s.FollowBody" % (self.RightForeArm.IK_CTRL), 0)
        mayac.setAttr("%s.FollowBody" % (self.LeftFoot.IK_CTRL), 0)
        mayac.setAttr("%s.FollowBody" % (self.RightFoot.IK_CTRL), 0)
        mayac.setAttr("%s.FollowBody" % (self.LeftLeg.IK_CTRL), 0)
        mayac.setAttr("%s.FollowBody" % (self.RightLeg.IK_CTRL), 0)
        
        selfPOS = mayac.xform(self.LeftLeg.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
        parentPOS = mayac.xform(self.LeftLeg.parent.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
        tempDistance = math.sqrt((selfPOS[0]-parentPOS[0])*(selfPOS[0]-parentPOS[0]) + (selfPOS[1]-parentPOS[1])*(selfPOS[1]-parentPOS[1]) + (selfPOS[2]-parentPOS[2])*(selfPOS[2]-parentPOS[2]))
        mayac.setAttr("%s.translateZ" % (self.LeftLeg.IK_CTRL), tempDistance / 2)
        mayac.setAttr("%s.translateZ" % (self.RightLeg.IK_CTRL), tempDistance / 2)
        if self.rigType == "AutoRig":
            mayac.setAttr("%s.translateX" % (self.LeftForeArm.IK_CTRL), tempDistance / 2)
            mayac.setAttr("%s.translateX" % (self.RightForeArm.IK_CTRL), tempDistance / -2)
        elif self.rigType == "World":
            mayac.setAttr("%s.translateZ" % (self.LeftForeArm.IK_CTRL), tempDistance / -2)
            mayac.setAttr("%s.translateZ" % (self.RightForeArm.IK_CTRL), tempDistance / -2)
        DJB_LockNHide(self.global_CTRL, tx = False, ty = False, tz = False, rx = False, ry = False, rz = False, s = False, v = True)
        
        OpenMaya.MGlobal.displayInfo("Rig Complete")

        
    def checkSkeletonProportions(self, incomingDataRootJoint):
        global proportionCheckTolerance
        success = True
        New_joint_Namespace = DJB_findBeforeSeparator(incomingDataRootJoint, ':')
        if not self.hulaOption and "Root" in incomingDataRootJoint:
            success = False
        for bodyPart in self.bodyParts:
            if bodyPart.children and bodyPart.nodeName != "Root" and bodyPart.Bind_Joint:
                selfPOS = mayac.xform(bodyPart.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
                if not mayac.objExists("%s%s" % (New_joint_Namespace, bodyPart.nodeName)):
                    success = False
                    break
                else:
                    DataSelfPOS = mayac.xform("%s%s" % (New_joint_Namespace, bodyPart.nodeName), query = True, absolute = True, worldSpace = True, translation = True)
                    for child in bodyPart.children:
                        if child.Bind_Joint and "End" not in child.nodeName:
                            childPOS = mayac.xform(child.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
                            if not mayac.objExists("%s%s" % (New_joint_Namespace, child.nodeName)):
                                success = False
                                break
                            else:
                                DataChildPOS = mayac.xform("%s%s" % (New_joint_Namespace, child.nodeName), query = True, absolute = True, worldSpace = True, translation = True)
                                correctDistance = math.sqrt((selfPOS[0]-childPOS[0])*(selfPOS[0]-childPOS[0]) + (selfPOS[1]-childPOS[1])*(selfPOS[1]-childPOS[1]) + (selfPOS[2]-childPOS[2])*(selfPOS[2]-childPOS[2])) / mayac.getAttr("%s.scaleX" % (self.global_CTRL))
                                distanceInQuestion = math.sqrt((DataSelfPOS[0]-DataChildPOS[0])*(DataSelfPOS[0]-DataChildPOS[0]) + (DataSelfPOS[1]-DataChildPOS[1])*(DataSelfPOS[1]-DataChildPOS[1]) + (DataSelfPOS[2]-DataChildPOS[2])*(DataSelfPOS[2]-DataChildPOS[2]))
                                if not math.fabs(distanceInQuestion/correctDistance) > 1 - proportionCheckTolerance or not math.fabs(distanceInQuestion/correctDistance) < 1 + proportionCheckTolerance:
                                    success = False
                                    break
                            if bodyPart.rotOrder != mayac.getAttr("%s.rotateOrder" % (New_joint_Namespace + bodyPart.nodeName)):
                                success = False
                                break
        return success
        
        
           
    def transferMotionToAnimDataJoints(self, incomingDataRootJoint, newStartTime = 0, mixMethod = "insert"): #mixMethod - insert or merge
        mayac.currentTime(1)
        New_joint_Namespace = DJB_findBeforeSeparator(incomingDataRootJoint, ':')
        keyList = mayac.keyframe("%s.translateX"%(incomingDataRootJoint),query = True, timeChange = True)
        lastFrame = keyList[len(keyList)-1]
        curJoint = 0.0
        gMainProgressBar = mel.eval('$tmp = $gMainProgressBar');
        mayac.progressBar( gMainProgressBar,
                       edit=True,
                       beginProgress=True,
                       isInterruptable=True,
                       status='Copying Keyframes for joint %d/%d ...' % (curJoint, len(self.bodyParts)-1),
                       maxValue=lastFrame )
        for bodyPart in self.bodyParts:
            if mayac.progressBar(gMainProgressBar, query=True, isCancelled=True ) :
                break
            if bodyPart.nodeName == "Root" and self.hulaOption:
                if mayac.objExists("%sRoot" % (New_joint_Namespace)):
                    mayac.copyKey("%sRoot" % (New_joint_Namespace), time = (0,lastFrame), hierarchy = "none", controlPoints = 0, shape = 1)
                    mayac.pasteKey(bodyPart.AnimData_Joint, option = mixMethod, connect = 1, timeOffset = newStartTime, valueOffset = 0)
                else:
                    mayac.copyKey("%sHips" % (New_joint_Namespace), time = (0,lastFrame), hierarchy = "none", controlPoints = 0, shape = 1)
                    mayac.pasteKey(bodyPart.AnimData_Joint, option = mixMethod, connect = 1, timeOffset = newStartTime, valueOffset = 0)
            elif bodyPart.nodeName == "Hips" and self.hulaOption and mayac.objExists("%sRoot" % (New_joint_Namespace)):
                mayac.copyKey("%sHips" % (New_joint_Namespace), time = (0,lastFrame), hierarchy = "none", controlPoints = 0, shape = 1)
                mayac.pasteKey(bodyPart.AnimData_Joint, option = mixMethod, connect = 1, timeOffset = newStartTime, valueOffset = 0)
            elif bodyPart.nodeName == "Hips" and not self.hulaOption:
                mayac.copyKey("%sHips" % (New_joint_Namespace), time = (0,lastFrame), hierarchy = "none", controlPoints = 0, shape = 1)
                mayac.pasteKey(bodyPart.AnimData_Joint, option = mixMethod, connect = 1, timeOffset = newStartTime, valueOffset = 0)
            elif bodyPart.nodeName not in ["Hips", "HeadTop_End", "LeftHandThumb4", "LeftHandIndex4", "LeftHandMiddle4", "LeftHandRing4", "LeftHandPinky4", "LeftToe_End", "RightHandThumb4", "RightHandIndex4", "RightHandMiddle4", "RightHandRing4", "RightHandPinky4", "RightToe_End"]:
                newAnimDataJoint = "%s%s" % (New_joint_Namespace, bodyPart.nodeName)
                if mayac.objExists(newAnimDataJoint):
                    numCurves = mayac.copyKey(newAnimDataJoint, time = (0,lastFrame), hierarchy = "none", controlPoints = 0, shape = 1)
                    if numCurves:
                        mayac.pasteKey(bodyPart.AnimData_Joint, option = mixMethod, connect = 1, timeOffset = newStartTime, valueOffset = 0)
            mayac.progressBar(gMainProgressBar, edit=True, step=1)    
            curJoint += 1
        mayac.progressBar(gMainProgressBar, edit=True, endProgress=True)
        sClusters = []
        sClusters = mayac.listConnections(incomingDataRootJoint, destination = True, type = "skinCluster")
        for joint in mayac.listRelatives(incomingDataRootJoint, allDescendents = True, type = 'joint'):
            checkClusterList = mayac.listConnections(joint, destination = True, type = "skinCluster")
            if checkClusterList:
                for checkCluster in checkClusterList:
                    if checkCluster not in sClusters:
                        sClusters.append(checkCluster)
        self.origAnim = mayac.group(incomingDataRootJoint, name = "Original_Animation_GRP")
        if sClusters:
            for sCluster in sClusters:
                shapes =  mayac.listConnections(sCluster, destination = True, type = "mesh")
                if shapes:
                    for shape in shapes:
                        parent = mayac.listRelatives(shape, parent = True)
                        if parent and self.origAnim not in parent:
                            DJB_Unlock(shape)
                            while "Original_Animation_" not in shape:
                                shape = mayac.rename(shape, "Original_Animation_%s" % (shape))
                            shape = mayac.parent(shape, self.origAnim)[0]
                        if not parent:
                            DJB_Unlock(shape)
                            while "Original_Animation_" not in shape:
                                shape = mayac.rename(shape, "Original_Animation_%s" % (shape))
                            shape = mayac.parent(shape, self.origAnim)[0]
                                
                            
        #rename orig anim joints
        for bodyPart in self.bodyParts:
            if mayac.objExists("%s%s" % (New_joint_Namespace, bodyPart.nodeName)):
                mayac.rename("%s%s" % (New_joint_Namespace, bodyPart.nodeName), "Original_Animation_%s" % (bodyPart.nodeName))
                    
        mayac.parent(self.origAnim, self.Character_GRP)
        self.origAnimation_Layer = mayac.createDisplayLayer(name = "OrigAnimationLayer", number = 1)
        mayac.editDisplayLayerMembers(self.origAnimation_Layer, self.origAnim)
        mayac.setAttr("%s.visibility" %(self.origAnimation_Layer), 0)
        mayac.setAttr("%s.displayType" %(self.origAnimation_Layer), 2)
        #update infoNode
        pyToAttr("%s.origAnim" % (self.infoNode), self.origAnim)
        pyToAttr("%s.origAnimation_Layer" % (self.infoNode), self.origAnimation_Layer)
        
        
        ##adjust timeline to fit animation
        #find first and last frames
        howManyKeys = []
        last = 0
        highestTime = -999999999
        lowestTime = 99999999
        objectsOfInterest = []
        for bodyPart in self.bodyParts:
            if "4" not in bodyPart.nodeName and "End" not in bodyPart.nodeName:
                if bodyPart.FK_CTRL:
                    objectsOfInterest.append(bodyPart.FK_CTRL)
                if bodyPart.IK_CTRL:
                    objectsOfInterest.append(bodyPart.IK_CTRL)
                if bodyPart.Options_CTRL:
                    objectsOfInterest.append(bodyPart.Options_CTRL)
                if bodyPart.AnimData_Joint:
                    objectsOfInterest.append(bodyPart.AnimData_Joint)
        objectsOfInterest.append(self.global_CTRL)
        for obj in objectsOfInterest:
            myKeys = mayac.keyframe(obj, query = True, name = True)
            if myKeys:
                howManyKeys = mayac.keyframe(myKeys[0], query = True, timeChange = True)
                last = len(howManyKeys)-1
                if howManyKeys[last] > highestTime:
                    highestTime = howManyKeys[last]
                if howManyKeys[0] < lowestTime:
                    lowestTime = howManyKeys[0]
        
        startTime = lowestTime
        endTime = highestTime
        mayac.playbackOptions(minTime = startTime, maxTime = highestTime)
        
        OpenMaya.MGlobal.displayInfo("Animation Data Attached")
        
        
    def deleteOriginalAnimation(self):
        mayac.delete(self.origAnim, self.origAnimation_Layer)
        self.origAnim = None
        self.origAnimation_Layer = None
        pyToAttr("%s.origAnim" % (self.infoNode), self.origAnim)
        pyToAttr("%s.origAnimation_Layer" % (self.infoNode), self.origAnimation_Layer)
        
        OpenMaya.MGlobal.displayInfo("Original Animation Deleted")
        
    
    
    def bakeAnimationToControls(self, bodyPart_ = "all"):
        #find first and last frames
        howManyKeys = []
        last = 0
        highestTime = -999999999
        lowestTime = 99999999
        objectsOfInterest = []
        for bodyPart in self.bodyParts:
            if "4" not in bodyPart.nodeName and "End" not in bodyPart.nodeName:
                if bodyPart.FK_CTRL:
                    objectsOfInterest.append(bodyPart.FK_CTRL)
                if bodyPart.IK_CTRL:
                    objectsOfInterest.append(bodyPart.IK_CTRL)
                if bodyPart.Options_CTRL:
                    objectsOfInterest.append(bodyPart.Options_CTRL)
                if bodyPart.AnimData_Joint:
                    objectsOfInterest.append(bodyPart.AnimData_Joint)
        objectsOfInterest.append(self.global_CTRL)
        for obj in objectsOfInterest:
            myKeys = mayac.keyframe(obj, query = True, name = True)
            if myKeys:
                howManyKeys = mayac.keyframe(myKeys[0], query = True, timeChange = True)
                last = len(howManyKeys)-1
                if howManyKeys[last] > highestTime:
                    highestTime = howManyKeys[last]
                if howManyKeys[0] < lowestTime:
                    lowestTime = howManyKeys[0]
        
        startTime = lowestTime
        endTime = highestTime
        
        if startTime == 99999999 and endTime == -999999999:
            OpenMaya.MGlobal.displayError("No Keyframes found on Character to bake!")
            return None
        
        #create locators
        locators = []
        for bodyPart in self.bodyParts:
            if "LeftLeg" in bodyPart.nodeName or "RightLeg" in bodyPart.nodeName or "ForeArm" in bodyPart.nodeName:
                temp = mayac.spaceLocator(n = "%s_locator1" % (bodyPart.nodeName))
                bodyPart.locator1 = temp[0]
                mayac.setAttr("%s.rotateOrder" % (bodyPart.locator1), bodyPart.rotOrder)
                mayac.setAttr("%s.visibility"%(bodyPart.locator1), 0)
                mayac.parent(bodyPart.locator1, self.global_CTRL)
                locators.append(bodyPart.locator1)
                temp = mayac.pointConstraint(bodyPart.IK_BakingLOC, bodyPart.locator1)
                bodyPart.locatorConstraint1 = temp[0]
            if "Foot" not in bodyPart.nodeName:
                temp = mayac.spaceLocator(n = "%s_locator" % (bodyPart.nodeName))
                bodyPart.locator = temp[0]
                mayac.setAttr("%s.rotateOrder" % (bodyPart.locator), bodyPart.rotOrder)
                mayac.setAttr("%s.visibility"%(bodyPart.locator), 0)
                mayac.parent(bodyPart.locator, self.global_CTRL)
                locators.append(bodyPart.locator)
                temp = mayac.parentConstraint(bodyPart.Bind_Joint, bodyPart.locator)
                bodyPart.locatorConstraint = temp[0]
            else:
                temp = mayac.spaceLocator(n = "%s_locator1" % (bodyPart.nodeName))
                bodyPart.locator1 = temp[0]
                mayac.setAttr("%s.rotateOrder" % (bodyPart.locator1), bodyPart.rotOrder)
                mayac.setAttr("%s.visibility"%(bodyPart.locator1), 0)
                mayac.parent(bodyPart.locator1, self.global_CTRL)
                mayac.delete(mayac.parentConstraint(bodyPart.Bind_Joint, bodyPart.locator1))
                temp = mayac.spaceLocator(n = "%s_locator" % (bodyPart.nodeName))
                bodyPart.locator = temp[0]
                mayac.setAttr("%s.rotateOrder" % (bodyPart.locator), bodyPart.rotOrder)
                mayac.setAttr("%s.visibility"%(bodyPart.locator), 0)
                mayac.parent(bodyPart.locator, self.global_CTRL)
                mayac.delete(mayac.parentConstraint(bodyPart.IK_BakingLOC, bodyPart.locator))
                temp = mayac.parentConstraint(bodyPart.locator1, bodyPart.locator, maintainOffset = True)
                bodyPart.locatorConstraint1 = temp[0]
                
                locators.append(bodyPart.locator)
                locators.append(bodyPart.locator1)
                temp = mayac.parentConstraint(bodyPart.Bind_Joint, bodyPart.locator1)
                bodyPart.locatorConstraint = temp[0]
                
        #bake onto locators
        mayac.select(clear = True)
        mayac.bakeResults(locators, simulation = True, time = (startTime, endTime))
        for bodyPart in self.bodyParts:
            mayac.delete(bodyPart.locatorConstraint)
            bodyPart.locatorConstraint = None
            if bodyPart.locatorConstraint1:
                mayac.delete(bodyPart.locatorConstraint1)
                bodyPart.locatorConstraint1 = None
        
        #zero out controls, animJoints
        for bodyPart in self.bodyParts:
            if bodyPart.AnimData_Joint:
                bodyPart.zeroToOrig(bodyPart.AnimData_Joint)
            if bodyPart.FK_CTRL:
                DJB_ZeroOut(bodyPart.FK_CTRL)
                DJB_ZeroOutAtt(bodyPart.FK_CTRL + ".AnimDataMult", value = 1)
                if "Root" in bodyPart.nodeName and self.hulaOption:
                    DJB_ZeroOutAtt(bodyPart.FK_CTRL + ".AnimDataMultTrans", value = 1)
                elif "Hips" in bodyPart.nodeName and not self.hulaOption:
                    DJB_ZeroOutAtt(bodyPart.FK_CTRL + ".AnimDataMultTrans", value = 1)
                if "Head" in bodyPart.nodeName:
                    DJB_ZeroOutAtt(bodyPart.FK_CTRL + ".InheritRotation", value = 1)
            if bodyPart.IK_CTRL:
                DJB_ZeroOut(bodyPart.IK_CTRL)
                DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".AnimDataMult", value = 1)
                DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ParentToGlobal")
                DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".FollowBody")
                if "Leg" in bodyPart.nodeName:
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".FollowFoot")
                if "ForeArm" in bodyPart.nodeName:
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".FollowHand")
                if "Foot" in bodyPart.nodeName:
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".FootRoll")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ToeTap")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ToeSideToSide")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ToeRotate")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ToeRoll")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".HipPivot")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".BallPivot")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ToePivot")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".HipSideToSide")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".HipBackToFront")
            if bodyPart.Options_CTRL:
                if "Hand" in bodyPart.nodeName:
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".FollowHand")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".ThumbCurl")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".IndexCurl")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".MiddleCurl")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".RingCurl")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".PinkyCurl")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".Sway")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".Spread")
                   
            
    
        #constraints
        bakeConstraintList = []
        bakeCTRLList = []
        EulerList = []
        for bodyPart in self.bodyParts:
            if bodyPart.FK_CTRL:
                if "Root" in bodyPart.nodeName:
                    temp = mayac.parentConstraint(bodyPart.locator, bodyPart.FK_CTRL)
                    bakeConstraintList.append(temp[0])
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".translateX")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".translateY")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".translateZ")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateX")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateY")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateZ")
                    
                elif "Hips" in bodyPart.nodeName and not self.hulaOption:
                    temp = mayac.parentConstraint(bodyPart.locator, bodyPart.FK_CTRL)
                    bakeConstraintList.append(temp[0])
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".translateX")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".translateY")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".translateZ")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateX")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateY")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateZ")
                   
                elif "Foot" in bodyPart.nodeName:
                    temp = mayac.orientConstraint(bodyPart.locator1, bodyPart.FK_CTRL)
                    bakeConstraintList.append(temp[0])
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateX")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateY")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateZ")
                    
                else:
                    temp = mayac.orientConstraint(bodyPart.locator, bodyPart.FK_CTRL)
                    bakeConstraintList.append(temp[0])
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateX")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateY")
                    bakeCTRLList.append(bodyPart.FK_CTRL + ".rotateZ")

            if bodyPart.IK_CTRL:
                
                if "ForeArm" in bodyPart.nodeName or "Leg" in bodyPart.nodeName:
                    temp = mayac.pointConstraint(bodyPart.locator1, bodyPart.IK_CTRL)
                    bakeConstraintList.append(temp[0])
                    bakeCTRLList.append(bodyPart.IK_CTRL + ".translateX")
                    bakeCTRLList.append(bodyPart.IK_CTRL + ".translateY")
                    bakeCTRLList.append(bodyPart.IK_CTRL + ".translateZ")
                else:
                    temp = mayac.parentConstraint(bodyPart.locator, bodyPart.IK_CTRL)
                    bakeConstraintList.append(temp[0])
                    bakeCTRLList.append(bodyPart.IK_CTRL + ".translateX")
                    bakeCTRLList.append(bodyPart.IK_CTRL + ".translateY")
                    bakeCTRLList.append(bodyPart.IK_CTRL + ".translateZ")
                    bakeCTRLList.append(bodyPart.IK_CTRL + ".rotateX")
                    bakeCTRLList.append(bodyPart.IK_CTRL + ".rotateY")
                    bakeCTRLList.append(bodyPart.IK_CTRL + ".rotateZ")

                
        #bake onto controls
        mayac.bakeResults(bakeCTRLList, simulation = True, time = (startTime, endTime))
        mayac.delete(bakeConstraintList)

        
        #Euler filter
        for bodyPart in self.bodyParts:
            if bodyPart.FK_CTRL:
                mayac.filterCurve( '%s_rotateX'%(bodyPart.FK_CTRL), '%s_rotateY'%(bodyPart.FK_CTRL), '%s_rotateZ'%(bodyPart.FK_CTRL))
            if bodyPart.nodeName  == "LeftHand" or bodyPart.nodeName  == "RightHand" or bodyPart.nodeName  == "LeftFoot" or bodyPart.nodeName  == "RightFoot":
                mayac.filterCurve( '%s_rotateX'%(bodyPart.IK_CTRL), '%s_rotateY'%(bodyPart.IK_CTRL), '%s_rotateZ'%(bodyPart.IK_CTRL))
            
        
        #delete garbage
        for bodyPart in self.bodyParts:
            mayac.delete(bodyPart.locator)
            bodyPart.locator = None
            if bodyPart.locator1:
                mayac.delete(bodyPart.locator1)
                bodyPart.locator1 = None
                
        #make sure animLayer1 is active
        baseLayer = mayac.animLayer(query = True, root = True)
        if baseLayer:
            layers = mayac.ls(type = 'animLayer')
            for layer in layers:
                mel.eval('animLayerEditorOnSelect "%s" 0;'%(layer))
            mel.eval('animLayerEditorOnSelect "%s" 1;'%(baseLayer))
             
        #IK Toe Tap
        if self.rigType == "AutoRig":
            mayac.copyKey(self.LeftToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateX")
            mayac.pasteKey(self.LeftFoot.IK_CTRL, connect = 1, attribute = "ToeTap")
            mayac.copyKey(self.LeftToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateY")
            mayac.pasteKey(self.LeftFoot.IK_CTRL, connect = 1, attribute = "ToeRotate")
            mayac.copyKey(self.LeftToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateZ")
            mayac.pasteKey(self.LeftFoot.IK_CTRL, connect = 1, attribute = "ToeSideToSide")
            mayac.copyKey(self.RightToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateX")
            mayac.pasteKey(self.RightFoot.IK_CTRL, connect = 1, attribute = "ToeTap")
            mayac.copyKey(self.RightToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateY")
            mayac.pasteKey(self.RightFoot.IK_CTRL, connect = 1, attribute = "ToeRotate")
            mayac.copyKey(self.RightToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateZ")
            mayac.pasteKey(self.RightFoot.IK_CTRL, connect = 1, attribute = "ToeSideToSide")
        elif self.rigType == "World":
            mayac.copyKey(self.LeftToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateX")
            mayac.pasteKey(self.LeftFoot.IK_CTRL, connect = 1, attribute = "ToeTap")
            mayac.scaleKey(self.LeftFoot.IK_CTRL, at='ToeTap', time=(startTime, endTime), valueScale = -1, valuePivot=0 )
            
            mayac.copyKey(self.LeftToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateY")
            mayac.pasteKey(self.LeftFoot.IK_CTRL, connect = 1, attribute = "ToeSideToSide")
            mayac.copyKey(self.LeftToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateZ")
            mayac.pasteKey(self.LeftFoot.IK_CTRL, connect = 1, attribute = "ToeRotate")
            mayac.copyKey(self.RightToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateX")
            mayac.pasteKey(self.RightFoot.IK_CTRL, connect = 1, attribute = "ToeTap")
            mayac.scaleKey(self.RightFoot.IK_CTRL, at='ToeTap', time=(startTime, endTime), valueScale = -1, valuePivot=0 )
            
            mayac.copyKey(self.RightToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateY")
            mayac.pasteKey(self.RightFoot.IK_CTRL, connect = 1, attribute = "ToeSideToSide")
            mayac.copyKey(self.RightToeBase.FK_CTRL, time = (startTime, endTime), hierarchy = "none", controlPoints = 0, shape = 1, attribute = "rotateZ")
            mayac.pasteKey(self.RightFoot.IK_CTRL, connect = 1, attribute = "ToeRotate")
            
        OpenMaya.MGlobal.displayInfo("Bake Successful")


    def clearAnimationControls(self, bodyPart_ = "all"):
        #find first and last frames
        #find first and last frames
        howManyKeys = []
        last = 0
        highestTime = -999999999
        lowestTime = 99999999
        objectsOfInterest = []
        for bodyPart in self.bodyParts:
            if "4" not in bodyPart.nodeName and "End" not in bodyPart.nodeName:
                if bodyPart.FK_CTRL:
                    objectsOfInterest.append(bodyPart.FK_CTRL)
                if bodyPart.IK_CTRL:
                    objectsOfInterest.append(bodyPart.IK_CTRL)
                if bodyPart.Options_CTRL:
                    objectsOfInterest.append(bodyPart.Options_CTRL)
                if bodyPart.AnimData_Joint:
                    objectsOfInterest.append(bodyPart.AnimData_Joint)
        objectsOfInterest.append(self.global_CTRL)
        for object in objectsOfInterest:
            myKeys = mayac.keyframe(object, query = True, name = True)
            if myKeys:
                howManyKeys = mayac.keyframe(myKeys[0], query = True, timeChange = True)
                last = len(howManyKeys)-1
                if howManyKeys[last] > highestTime:
                    highestTime = howManyKeys[last]
                if howManyKeys[0] < lowestTime:
                    lowestTime = howManyKeys[0]
        
        startTime = lowestTime
        endTime = highestTime
        
        if startTime == 99999999 and endTime == -999999999:
            OpenMaya.MGlobal.displayError("No Keyframes found on Character to clear!")
            return None
            
            
            
            
        #create locators
        locators = []
        temp = mayac.duplicate(self.global_CTRL, parentOnly = True)
        fakeGlobal = temp[0]
        mayac.setAttr("%s.translateX"%(fakeGlobal), 0)
        mayac.setAttr("%s.translateY"%(fakeGlobal), 0)
        mayac.setAttr("%s.translateZ"%(fakeGlobal), 0)
        mayac.setAttr("%s.rotateX"%(fakeGlobal), 0)
        mayac.setAttr("%s.rotateY"%(fakeGlobal), 0)
        mayac.setAttr("%s.rotateZ"%(fakeGlobal), 0)
        mayac.connectAttr("%s.scaleX"%(self.global_CTRL), "%s.scaleX"%(fakeGlobal))
        mayac.connectAttr("%s.scaleY"%(self.global_CTRL), "%s.scaleY"%(fakeGlobal))
        mayac.connectAttr("%s.scaleZ"%(self.global_CTRL), "%s.scaleZ"%(fakeGlobal))
        mayac.setAttr("%s.visibility"%(fakeGlobal), lock = False, keyable = True)
        mayac.setAttr("%s.visibility"%(fakeGlobal), 0)
        for bodyPart in self.bodyParts:
            temp = mayac.spaceLocator(n = "%s_locator" % (bodyPart.nodeName))
            bodyPart.locator = temp[0]
            locators.append(bodyPart.locator)
            mayac.setAttr("%s.visibility"%(bodyPart.locator), 0)
            mayac.parent(bodyPart.locator, self.global_CTRL)
            temp = mayac.parentConstraint(bodyPart.Bind_Joint, bodyPart.locator)
            bodyPart.locatorConstraint = temp[0]
            if "LeftLeg" in bodyPart.nodeName or "RightLeg" in bodyPart.nodeName or "ForeArm" in bodyPart.nodeName:
                temp = mayac.spaceLocator(n = "%s_locator2" % (bodyPart.nodeName))
                bodyPart.locator2 = temp[0]
                locators.append(bodyPart.locator2)
                mayac.setAttr("%s.visibility"%(bodyPart.locator2), 0)
                mayac.parent(bodyPart.locator2, self.global_CTRL)
                temp = mayac.parentConstraint(bodyPart.IK_BakingLOC, bodyPart.locator2)
                bodyPart.locatorConstraint2 = temp[0]
                temp = mayac.spaceLocator(n = "%s_locator3" % (bodyPart.nodeName))
                bodyPart.locator3 = temp[0]
                mayac.parent(bodyPart.locator3, fakeGlobal)
                mayac.setAttr("%s.visibility"%(bodyPart.locator3), 0)
                locators.append(bodyPart.locator3)
                mayac.connectAttr("%s.translateX" % (bodyPart.locator2), "%s.translateX" % (bodyPart.locator3))
                mayac.connectAttr("%s.translateY" % (bodyPart.locator2), "%s.translateY" % (bodyPart.locator3))
                mayac.connectAttr("%s.translateZ" % (bodyPart.locator2), "%s.translateZ" % (bodyPart.locator3))
                mayac.connectAttr("%s.rotateX" % (bodyPart.locator2), "%s.rotateX" % (bodyPart.locator3))
                mayac.connectAttr("%s.rotateY" % (bodyPart.locator2), "%s.rotateY" % (bodyPart.locator3))
                mayac.connectAttr("%s.rotateZ" % (bodyPart.locator2), "%s.rotateZ" % (bodyPart.locator3))
           
            temp = mayac.spaceLocator(n = "%s_locator1" % (bodyPart.nodeName))
            bodyPart.locator1 = temp[0]
            mayac.setAttr("%s.visibility"%(bodyPart.locator1), 0)
            locators.append(bodyPart.locator1)
            mayac.parent(bodyPart.locator1, fakeGlobal)
            mayac.connectAttr("%s.translateX" % (bodyPart.locator), "%s.translateX" % (bodyPart.locator1))
            mayac.connectAttr("%s.translateY" % (bodyPart.locator), "%s.translateY" % (bodyPart.locator1))
            mayac.connectAttr("%s.translateZ" % (bodyPart.locator), "%s.translateZ" % (bodyPart.locator1))
            mayac.connectAttr("%s.rotateX" % (bodyPart.locator), "%s.rotateX" % (bodyPart.locator1))
            mayac.connectAttr("%s.rotateY" % (bodyPart.locator), "%s.rotateY" % (bodyPart.locator1))
            mayac.connectAttr("%s.rotateZ" % (bodyPart.locator), "%s.rotateZ" % (bodyPart.locator1))
        mayac.select(clear = True)
            
                
        
        #bake onto locators
        mayac.bakeResults(locators, simulation = True, time = (startTime, endTime))
        for bodyPart in self.bodyParts:
            mayac.delete(bodyPart.locatorConstraint)
            bodyPart.locatorConstraint = None
            if bodyPart.locatorConstraint1:
                mayac.delete(bodyPart.locatorConstraint1)
                bodyPart.locatorConstraint1 = None
            if bodyPart.locatorConstraint2:
                mayac.delete(bodyPart.locatorConstraint2)
                bodyPart.locatorConstraint2 = None
            if bodyPart.locatorConstraint3:
                mayac.delete(bodyPart.locatorConstraint3)
                bodyPart.locatorConstraint3 = None
                
        
        bakeConstraintList = []
        bakeJointList = []
        #zero out controls, animJoints
        for bodyPart in self.bodyParts:
            if bodyPart.AnimData_Joint:
                bodyPart.zeroToOrig(bodyPart.AnimData_Joint)
            if bodyPart.FK_CTRL:
                DJB_ZeroOut(bodyPart.FK_CTRL)
                DJB_ZeroOutAtt(bodyPart.FK_CTRL + ".AnimDataMult", value = 1)
                if "Root" in bodyPart.nodeName:
                    DJB_ZeroOutAtt(bodyPart.FK_CTRL + ".AnimDataMultTrans", value = 1)
                elif "Hips" in bodyPart.nodeName and not self.hulaOption:
                    DJB_ZeroOutAtt(bodyPart.FK_CTRL + ".AnimDataMultTrans", value = 1)
                if "Head" in bodyPart.nodeName:
                    DJB_ZeroOutAtt(bodyPart.FK_CTRL + ".InheritRotation", value = 1)
            if bodyPart.IK_CTRL:
                DJB_ZeroOut(bodyPart.IK_CTRL)
                DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".AnimDataMult", value = 1)
                DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ParentToGlobal")
                DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".FollowBody")
                if "LeftLeg" in bodyPart.nodeName or "RightLeg" in bodyPart.nodeName or "ForeArm" in bodyPart.nodeName:
                    temp = mayac.pointConstraint(bodyPart.IK_CTRL, bodyPart.locator1)
                    bodyPart.locatorConstraint1 = temp[0]
                if "Leg" in bodyPart.nodeName:
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".FollowFoot")
                if "ForeArm" in bodyPart.nodeName:
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".FollowHand")
                if "Foot" in bodyPart.nodeName:
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".FootRoll")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ToeTap")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ToeSideToSide")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ToeRotate")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ToeRoll")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".HipPivot")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".BallPivot")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".ToePivot")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".HipSideToSide")
                    DJB_ZeroOutAtt(bodyPart.IK_CTRL + ".HipBackToFront")
            if bodyPart.Options_CTRL:
                if "Hand" in bodyPart.nodeName:
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".FollowHand")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".ThumbCurl")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".IndexCurl")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".MiddleCurl")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".RingCurl")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".PinkyCurl")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".Sway")
                    DJB_ZeroOutAtt(bodyPart.Options_CTRL + ".Spread")
                    
            
        
        #constraints
        for bodyPart in self.bodyParts:
            if "Root" in bodyPart.nodeName and self.hulaOption:
                temp = mayac.parentConstraint(bodyPart.locator1, bodyPart.AnimData_Joint)
                bakeConstraintList.append(temp[0])
                bakeJointList.append(bodyPart.AnimData_Joint + ".translateX")
                bakeJointList.append(bodyPart.AnimData_Joint + ".translateY")
                bakeJointList.append(bodyPart.AnimData_Joint + ".translateZ")
                bakeJointList.append(bodyPart.AnimData_Joint + ".rotateX")
                bakeJointList.append(bodyPart.AnimData_Joint + ".rotateY")
                bakeJointList.append(bodyPart.AnimData_Joint + ".rotateZ")   
            elif "Hips" in  bodyPart.nodeName and not self.hulaOption:
                temp = mayac.parentConstraint(bodyPart.locator1, bodyPart.AnimData_Joint)
                bakeConstraintList.append(temp[0])
                bakeJointList.append(bodyPart.AnimData_Joint + ".translateX")
                bakeJointList.append(bodyPart.AnimData_Joint + ".translateY")
                bakeJointList.append(bodyPart.AnimData_Joint + ".translateZ")
                bakeJointList.append(bodyPart.AnimData_Joint + ".rotateX")
                bakeJointList.append(bodyPart.AnimData_Joint + ".rotateY")
                bakeJointList.append(bodyPart.AnimData_Joint + ".rotateZ")            
            else:
                temp = mayac.orientConstraint(bodyPart.locator1, bodyPart.AnimData_Joint)
                bakeConstraintList.append(temp[0])
                bakeJointList.append(bodyPart.AnimData_Joint + ".rotateX")
                bakeJointList.append(bodyPart.AnimData_Joint + ".rotateY")
                bakeJointList.append(bodyPart.AnimData_Joint + ".rotateZ")

                
        #bake onto joints
        mayac.bakeResults(bakeJointList, simulation = True, time = (startTime, endTime))
        mayac.delete(bakeConstraintList)
        
                
        #Euler filter
        for bodyPart in self.bodyParts:
            if bodyPart.AnimData_Joint:
                mayac.filterCurve( '%s_rotateX'%(bodyPart.AnimData_Joint), '%s_rotateY'%(bodyPart.AnimData_Joint), '%s_rotateZ'%(bodyPart.AnimData_Joint))

        
        #delete garbage
        for bodyPart in self.bodyParts:
            mayac.delete(bodyPart.locator)
            bodyPart.locator = None
            if bodyPart.locator1:
                mayac.delete(bodyPart.locator1)
                bodyPart.locator1 = None
            if bodyPart.locator2:
                mayac.delete(bodyPart.locator2)
                bodyPart.locator2 = None
            if bodyPart.locator3:
                mayac.delete(bodyPart.locator3)
                bodyPart.locator3 = None
        #mayac.delete(fakeGlobal)
            
        #move PVs out a bit
        DJB_ZeroOut(self.LeftForeArm.IK_BakingLOC)
        DJB_ZeroOut(self.RightForeArm.IK_BakingLOC)
        DJB_ZeroOut(self.LeftLeg.IK_BakingLOC)
        DJB_ZeroOut(self.RightLeg.IK_BakingLOC)
        DJB_ZeroOut(self.LeftForeArm.IK_CTRL)
        DJB_ZeroOut(self.RightForeArm.IK_CTRL)
        DJB_ZeroOut(self.LeftLeg.IK_CTRL)
        DJB_ZeroOut(self.RightLeg.IK_CTRL)

        selfPOS = mayac.xform(self.LeftLeg.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
        parentPOS = mayac.xform(self.LeftLeg.parent.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
        tempDistance = math.sqrt((selfPOS[0]-parentPOS[0])*(selfPOS[0]-parentPOS[0]) + (selfPOS[1]-parentPOS[1])*(selfPOS[1]-parentPOS[1]) + (selfPOS[2]-parentPOS[2])*(selfPOS[2]-parentPOS[2]))
        mayac.setAttr("%s.translateZ" % (self.LeftLeg.IK_CTRL), tempDistance / 2)
        mayac.setAttr("%s.translateZ" % (self.RightLeg.IK_CTRL), tempDistance / 2)
        mayac.setAttr("%s.translateZ" % (self.LeftLeg.IK_BakingLOC), tempDistance / 2)
        mayac.setAttr("%s.translateZ" % (self.RightLeg.IK_BakingLOC), tempDistance / 2)
        selfPOS = mayac.xform(self.LeftForeArm.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
        parentPOS = mayac.xform(self.LeftForeArm.parent.Bind_Joint, query = True, absolute = True, worldSpace = True, translation = True)
        tempDistance = math.sqrt((selfPOS[0]-parentPOS[0])*(selfPOS[0]-parentPOS[0]) + (selfPOS[1]-parentPOS[1])*(selfPOS[1]-parentPOS[1]) + (selfPOS[2]-parentPOS[2])*(selfPOS[2]-parentPOS[2]))
        if self.rigType == "AutoRig":
            mayac.setAttr("%s.translateX" % (self.LeftForeArm.IK_CTRL), tempDistance / 2)
            mayac.setAttr("%s.translateX" % (self.RightForeArm.IK_CTRL), tempDistance / -2)
            mayac.setAttr("%s.translateX" % (self.LeftForeArm.IK_BakingLOC), tempDistance / 2)
            mayac.setAttr("%s.translateX" % (self.RightForeArm.IK_BakingLOC), tempDistance / -2)
        elif self.rigType == "World":
            mayac.setAttr("%s.translateZ" % (self.LeftForeArm.IK_CTRL), tempDistance / -2)
            mayac.setAttr("%s.translateZ" % (self.RightForeArm.IK_CTRL), tempDistance / -2)
            mayac.setAttr("%s.translateZ" % (self.LeftForeArm.IK_BakingLOC), tempDistance / -2)
            mayac.setAttr("%s.translateZ" % (self.RightForeArm.IK_BakingLOC), tempDistance / -2)
        
        OpenMaya.MGlobal.displayInfo("Un-Bake Successful")
        


    def createExportSkeleton(self, keepMesh_ = False):
        #copy joints and mesh
        if self.exportList:
            for obj in self.exportList:
                if mayac.objExists(obj):
                    mayac.delete(obj)
        self.exportList = []
        for bodyPart in self.bodyParts:
            bodyPart.duplicateJoint("ExportSkeleton", jointNamespace = self.jointNamespace)
            bodyPart.Export_Joint = mayac.rename(bodyPart.Export_Joint, self.jointNamespace + bodyPart.nodeName)
            self.exportList.append(bodyPart.Export_Joint)
            mayac.disconnectAttr("%s.drawInfo" % (self.Bind_Joint_Layer), "%s.drawOverride" % (bodyPart.Export_Joint))
        pyToAttr("%s.exportList" % (self.infoNode), self.exportList)
        
        
        #create Constraints
        constraintList = []
        for bodyPart in self.bodyParts:
            if bodyPart.Bind_Joint:
                constraintList.append(mayac.parentConstraint(bodyPart.Bind_Joint, bodyPart.Export_Joint))
        
        
        #find first and last frames
        howManyKeys = []
        last = 0
        highestTime = -999999999
        lowestTime = 99999999
        objectsOfInterest = []
        for bodyPart in self.bodyParts:
            if "4" not in bodyPart.nodeName and "End" not in bodyPart.nodeName:
                if bodyPart.FK_CTRL:
                    objectsOfInterest.append(bodyPart.FK_CTRL)
                if bodyPart.IK_CTRL:
                    objectsOfInterest.append(bodyPart.IK_CTRL)
                if bodyPart.Options_CTRL:
                    objectsOfInterest.append(bodyPart.Options_CTRL)
                if bodyPart.AnimData_Joint:
                    objectsOfInterest.append(bodyPart.AnimData_Joint)
        objectsOfInterest.append(self.global_CTRL)
        for obj in objectsOfInterest:
            myKeys = mayac.keyframe(obj, query = True, name = True)
            if myKeys:
                howManyKeys = mayac.keyframe(myKeys[0], query = True, timeChange = True)
                last = len(howManyKeys)-1
                if howManyKeys[last] > highestTime:
                    highestTime = howManyKeys[last]
                if howManyKeys[0] < lowestTime:
                    lowestTime = howManyKeys[0]
        
        startTime = lowestTime
        endTime = highestTime
        
        anythingToBake = True
        
        if startTime == 99999999 and endTime == -999999999:
            anythingToBake = False
        
        #bake animation to joints
        mayac.select(clear = True)
        if anythingToBake:
            mayac.bakeResults(self.exportList, simulation = True, time = (startTime, endTime))
        for constraint in constraintList:
            mayac.delete(constraint)
        
        if anythingToBake:
            for bodyPart in self.bodyParts:
                if bodyPart.Export_Joint:
                    mayac.filterCurve( '%s_rotateX'%(bodyPart.Export_Joint), '%s_rotateY'%(bodyPart.Export_Joint), '%s_rotateZ'%(bodyPart.Export_Joint))
            
        
        #add mesh
        if keepMesh_:
            for i in range(len(self.mesh)):
                oldSkin = mayac.listConnections(self.characterNameSpace + self.mesh[i], destination = True, type = "skinCluster")
                if oldSkin:
                    oldSkin = oldSkin[0]
                else:  #special case if there are deformers on top of rig and skinCluster is no longer directly connected
                    connections = mayac.listConnections((self.characterNameSpace + self.mesh[i]), destination = True)
                    for connection in connections:
                        if "skinCluster" in connection:
                            oldSkin = connection[:-3]
                        
                duplicatedMesh = mayac.duplicate(self.characterNameSpace + self.mesh[i])[0]
                shapeNode = mayac.listRelatives(duplicatedMesh, children = True, type = "shape")[0]
                oldTransform = mayac.listRelatives(self.characterNameSpace + self.mesh[i], parent = True)[0]
                DJB_Unlock(duplicatedMesh)
                DJB_Unlock(oldTransform)
                isItLocked = mayac.getAttr("%s.visibility" % (oldTransform))
                mayac.setAttr("%s.visibility" % (oldTransform), 1)
                mayac.setAttr("%s.visibility" % (self.characterNameSpace + self.mesh[i]), 1)
                mayac.setAttr("%s.visibility" % (duplicatedMesh), 1)
                mayac.setAttr("%s.visibility" % (shapeNode), 1)
                mayac.parent(duplicatedMesh, world = True)
                duplicatedMesh = mayac.rename(duplicatedMesh, self.original_Mesh_Names[i])
                self.exportList.append(duplicatedMesh)
                mayac.disconnectAttr("%s.drawInfo" % (self.Mesh_Layer), "%s.drawOverride" % (duplicatedMesh))
                shapeNode = mayac.listRelatives(duplicatedMesh, children = True, type = "shape")[0]
                mayac.disconnectAttr("%s.drawInfo" % (self.Mesh_Layer), "%s.drawOverride" % (shapeNode))
                newSkin = None
                if self.hulaOption:
                    newSkin = mayac.skinCluster( self.Root.Export_Joint, duplicatedMesh)[0]
                else:
                    newSkin = mayac.skinCluster( self.Hips.Export_Joint, duplicatedMesh)[0]
                mayac.copySkinWeights( ss= oldSkin, ds= newSkin, noMirror=True )
                mayac.setAttr("%s.visibility" % (oldTransform), isItLocked)
                mayac.setAttr("%s.visibility" % (self.characterNameSpace + self.mesh[i]), isItLocked)
                mayac.setAttr("%s.visibility" % (duplicatedMesh), isItLocked)
                mayac.setAttr("%s.visibility" % (shapeNode), isItLocked)
        pyToAttr("%s.exportList" % (self.infoNode), self.exportList)
        
        
    def exportSkeleton(self):
        mayac.select(self.exportList, replace = True)
        mayac.ExportSelection()
    
    
    def deleteExportSkeleton(self):
        mayac.select(self.exportList, replace = True)
        mayac.delete()
        self.exportList = None
        pyToAttr("%s.exportList" % (self.infoNode), self.exportList)



    def writeInfoNode(self):
        self.infoNode = mayac.createNode("transform", name = "MIXAMO_CHARACTER_infoNode")
        
        pyToAttr("%s.mesh" % (self.infoNode), self.mesh)
        pyToAttr("%s.original_Mesh_Names" % (self.infoNode), self.original_Mesh_Names)
        pyToAttr("%s.jointNamespace" % (self.infoNode), self.jointNamespace)
        pyToAttr("%s.rigType" % (self.infoNode), self.rigType)
        pyToAttr("%s.BoundingBox" % (self.infoNode), self.BoundingBox)
        pyToAttr("%s.Root" % (self.infoNode), self.Root.writeInfoNode())
        pyToAttr("%s.Hips" % (self.infoNode), self.Hips.writeInfoNode())
        pyToAttr("%s.Spine" % (self.infoNode), self.Spine.writeInfoNode())
        pyToAttr("%s.Spine1" % (self.infoNode), self.Spine1.writeInfoNode())
        pyToAttr("%s.Spine2" % (self.infoNode), self.Spine2.writeInfoNode())
        pyToAttr("%s.Spine3" % (self.infoNode), self.Spine3.writeInfoNode())
        pyToAttr("%s.Neck" % (self.infoNode), self.Neck.writeInfoNode())
        pyToAttr("%s.Neck1" % (self.infoNode), self.Neck1.writeInfoNode())
        pyToAttr("%s.Head" % (self.infoNode), self.Head.writeInfoNode())
        pyToAttr("%s.HeadTop_End" % (self.infoNode), self.HeadTop_End.writeInfoNode())
        pyToAttr("%s.LeftShoulder" % (self.infoNode), self.LeftShoulder.writeInfoNode())
        pyToAttr("%s.LeftArm" % (self.infoNode), self.LeftArm.writeInfoNode())
        pyToAttr("%s.LeftForeArm" % (self.infoNode), self.LeftForeArm.writeInfoNode())
        pyToAttr("%s.LeftHand" % (self.infoNode), self.LeftHand.writeInfoNode())
        pyToAttr("%s.LeftHandThumb1" % (self.infoNode), self.LeftHandThumb1.writeInfoNode())
        pyToAttr("%s.LeftHandThumb2" % (self.infoNode), self.LeftHandThumb2.writeInfoNode())
        pyToAttr("%s.LeftHandThumb3" % (self.infoNode), self.LeftHandThumb3.writeInfoNode())
        pyToAttr("%s.LeftHandThumb4" % (self.infoNode), self.LeftHandThumb4.writeInfoNode())
        pyToAttr("%s.LeftHandIndex1" % (self.infoNode), self.LeftHandIndex1.writeInfoNode())
        pyToAttr("%s.LeftHandIndex2" % (self.infoNode), self.LeftHandIndex2.writeInfoNode())
        pyToAttr("%s.LeftHandIndex3" % (self.infoNode), self.LeftHandIndex3.writeInfoNode())
        pyToAttr("%s.LeftHandIndex4" % (self.infoNode), self.LeftHandIndex4.writeInfoNode())
        pyToAttr("%s.LeftHandMiddle1" % (self.infoNode), self.LeftHandMiddle1.writeInfoNode())
        pyToAttr("%s.LeftHandMiddle2" % (self.infoNode), self.LeftHandMiddle2.writeInfoNode())
        pyToAttr("%s.LeftHandMiddle3" % (self.infoNode), self.LeftHandMiddle3.writeInfoNode())
        pyToAttr("%s.LeftHandMiddle4" % (self.infoNode), self.LeftHandMiddle4.writeInfoNode())
        pyToAttr("%s.LeftHandRing1" % (self.infoNode), self.LeftHandRing1.writeInfoNode())
        pyToAttr("%s.LeftHandRing2" % (self.infoNode), self.LeftHandRing2.writeInfoNode())
        pyToAttr("%s.LeftHandRing3" % (self.infoNode), self.LeftHandRing3.writeInfoNode())
        pyToAttr("%s.LeftHandRing4" % (self.infoNode), self.LeftHandRing4.writeInfoNode())
        pyToAttr("%s.LeftHandPinky1" % (self.infoNode), self.LeftHandPinky1.writeInfoNode())
        pyToAttr("%s.LeftHandPinky2" % (self.infoNode), self.LeftHandPinky2.writeInfoNode())
        pyToAttr("%s.LeftHandPinky3" % (self.infoNode), self.LeftHandPinky3.writeInfoNode())
        pyToAttr("%s.LeftHandPinky4" % (self.infoNode), self.LeftHandPinky4.writeInfoNode())
        pyToAttr("%s.RightShoulder" % (self.infoNode), self.RightShoulder.writeInfoNode())
        pyToAttr("%s.RightArm" % (self.infoNode), self.RightArm.writeInfoNode())
        pyToAttr("%s.RightForeArm" % (self.infoNode), self.RightForeArm.writeInfoNode())
        pyToAttr("%s.RightHand" % (self.infoNode), self.RightHand.writeInfoNode())
        pyToAttr("%s.RightHandThumb1" % (self.infoNode), self.RightHandThumb1.writeInfoNode())
        pyToAttr("%s.RightHandThumb2" % (self.infoNode), self.RightHandThumb2.writeInfoNode())
        pyToAttr("%s.RightHandThumb3" % (self.infoNode), self.RightHandThumb3.writeInfoNode())
        pyToAttr("%s.RightHandThumb4" % (self.infoNode), self.RightHandThumb4.writeInfoNode())
        pyToAttr("%s.RightHandIndex1" % (self.infoNode), self.RightHandIndex1.writeInfoNode())
        pyToAttr("%s.RightHandIndex2" % (self.infoNode), self.RightHandIndex2.writeInfoNode())
        pyToAttr("%s.RightHandIndex3" % (self.infoNode), self.RightHandIndex3.writeInfoNode())
        pyToAttr("%s.RightHandIndex4" % (self.infoNode), self.RightHandIndex4.writeInfoNode())
        pyToAttr("%s.RightHandMiddle1" % (self.infoNode), self.RightHandMiddle1.writeInfoNode())
        pyToAttr("%s.RightHandMiddle2" % (self.infoNode), self.RightHandMiddle2.writeInfoNode())
        pyToAttr("%s.RightHandMiddle3" % (self.infoNode), self.RightHandMiddle3.writeInfoNode())
        pyToAttr("%s.RightHandMiddle4" % (self.infoNode), self.RightHandMiddle4.writeInfoNode())
        pyToAttr("%s.RightHandRing1" % (self.infoNode), self.RightHandRing1.writeInfoNode())
        pyToAttr("%s.RightHandRing2" % (self.infoNode), self.RightHandRing2.writeInfoNode())
        pyToAttr("%s.RightHandRing3" % (self.infoNode), self.RightHandRing3.writeInfoNode())
        pyToAttr("%s.RightHandRing4" % (self.infoNode), self.RightHandRing4.writeInfoNode())
        pyToAttr("%s.RightHandPinky1" % (self.infoNode), self.RightHandPinky1.writeInfoNode())
        pyToAttr("%s.RightHandPinky2" % (self.infoNode), self.RightHandPinky2.writeInfoNode())
        pyToAttr("%s.RightHandPinky3" % (self.infoNode), self.RightHandPinky3.writeInfoNode())
        pyToAttr("%s.RightHandPinky4" % (self.infoNode), self.RightHandPinky4.writeInfoNode())
        pyToAttr("%s.LeftUpLeg" % (self.infoNode), self.LeftUpLeg.writeInfoNode())
        pyToAttr("%s.LeftLeg" % (self.infoNode), self.LeftLeg.writeInfoNode())
        pyToAttr("%s.LeftFoot" % (self.infoNode), self.LeftFoot.writeInfoNode())
        pyToAttr("%s.LeftToeBase" % (self.infoNode), self.LeftToeBase.writeInfoNode())
        pyToAttr("%s.LeftToe_End" % (self.infoNode), self.LeftToe_End.writeInfoNode())
        pyToAttr("%s.RightUpLeg" % (self.infoNode), self.RightUpLeg.writeInfoNode())
        pyToAttr("%s.RightLeg" % (self.infoNode), self.RightLeg.writeInfoNode())
        pyToAttr("%s.RightFoot" % (self.infoNode), self.RightFoot.writeInfoNode())
        pyToAttr("%s.RightToeBase" % (self.infoNode), self.RightToeBase.writeInfoNode())
        pyToAttr("%s.RightToe_End" % (self.infoNode), self.RightToe_End.writeInfoNode())
        
        mayac.parent(self.infoNode, self.Misc_GRP)
        DJB_LockNHide(self.infoNode)
        for bodyPart in (self.Root, self.Hips, self.Spine, self.Spine1, self.Spine2, self.Spine3, self.Neck, self.Neck1, self.Head, self.HeadTop_End, self.LeftShoulder, 
                              self.LeftArm, self.LeftForeArm, self.LeftHand, self.LeftHandThumb1, self.LeftHandThumb2, self.LeftHandThumb3, 
                              self.LeftHandThumb4, self.LeftHandIndex1, self.LeftHandIndex2, self.LeftHandIndex3, self.LeftHandIndex4,
                              self.LeftHandMiddle1, self.LeftHandMiddle2, self.LeftHandMiddle3, self.LeftHandMiddle4, self.LeftHandRing1,
                              self.LeftHandRing2, self.LeftHandRing3, self.LeftHandRing4, self.LeftHandPinky1, self.LeftHandPinky2, 
                              self.LeftHandPinky3, self.LeftHandPinky4, self.RightShoulder, self.RightArm, self.RightForeArm, 
                              self.RightHand, self.RightHandThumb1, self.RightHandThumb2, self.RightHandThumb3, 
                              self.RightHandThumb4, self.RightHandIndex1, self.RightHandIndex2, self.RightHandIndex3, self.RightHandIndex4,
                              self.RightHandMiddle1, self.RightHandMiddle2, self.RightHandMiddle3, self.RightHandMiddle4, self.RightHandRing1,
                              self.RightHandRing2, self.RightHandRing3, self.RightHandRing4, self.RightHandPinky1, self.RightHandPinky2, 
                              self.RightHandPinky3, self.RightHandPinky4, self.LeftUpLeg, self.LeftLeg, self.LeftFoot, self.LeftToeBase,
                              self.LeftToe_End, self.RightUpLeg, self.RightLeg, self.RightFoot, self.RightToeBase, self.RightToe_End):
            mayac.parent(bodyPart.infoNode, self.Misc_GRP)
            DJB_LockNHide(bodyPart.infoNode)

        pyToAttr("%s.proportions" % (self.infoNode), self.proportions)
        pyToAttr("%s.defaultControlScale" % (self.infoNode), self.defaultControlScale)
        pyToAttr("%s.Character_GRP" % (self.infoNode), self.Character_GRP)
        pyToAttr("%s.global_CTRL" % (self.infoNode), self.global_CTRL)
        pyToAttr("%s.CTRL_GRP" % (self.infoNode), self.CTRL_GRP)
        pyToAttr("%s.Joint_GRP" % (self.infoNode), self.Joint_GRP)
        pyToAttr("%s.AnimData_Joint_GRP" % (self.infoNode), self.AnimData_Joint_GRP)
        pyToAttr("%s.Bind_Joint_GRP" % (self.infoNode), self.Bind_Joint_GRP)
        pyToAttr("%s.Mesh_GRP" % (self.infoNode), self.Mesh_GRP)
        pyToAttr("%s.Misc_GRP" % (self.infoNode), self.Misc_GRP)
        pyToAttr("%s.LeftArm_Switch_Reverse" % (self.infoNode), self.LeftArm_Switch_Reverse)
        pyToAttr("%s.RightArm_Switch_Reverse" % (self.infoNode), self.RightArm_Switch_Reverse)
        pyToAttr("%s.LeftLeg_Switch_Reverse" % (self.infoNode), self.LeftLeg_Switch_Reverse)
        pyToAttr("%s.RightLeg_Switch_Reverse" % (self.infoNode), self.RightLeg_Switch_Reverse)
        pyToAttr("%s.Bind_Joint_SelectSet" % (self.infoNode), self.Bind_Joint_SelectSet)
        pyToAttr("%s.AnimData_Joint_SelectSet" % (self.infoNode), self.AnimData_Joint_SelectSet)
        pyToAttr("%s.Controls_SelectSet" % (self.infoNode), self.Controls_SelectSet)
        pyToAttr("%s.Geo_SelectSet" % (self.infoNode), self.Geo_SelectSet)
        pyToAttr("%s.Left_Toe_IK_AnimData_GRP" % (self.infoNode), self.Left_Toe_IK_AnimData_GRP)
        pyToAttr("%s.Left_Toe_IK_CTRL" % (self.infoNode), self.Left_Toe_IK_CTRL)
        pyToAttr("%s.Left_ToeBase_IK_AnimData_GRP" % (self.infoNode), self.Left_ToeBase_IK_AnimData_GRP)
        pyToAttr("%s.Left_IK_ToeBase_animData_MultNode" % (self.infoNode), self.Left_IK_ToeBase_animData_MultNode)
        pyToAttr("%s.Left_ToeBase_IK_CTRL" % (self.infoNode), self.Left_ToeBase_IK_CTRL)
        pyToAttr("%s.Left_Ankle_IK_AnimData_GRP" % (self.infoNode), self.Left_Ankle_IK_AnimData_GRP)
        pyToAttr("%s.Left_Ankle_IK_CTRL" % (self.infoNode), self.Left_Ankle_IK_CTRL)
        pyToAttr("%s.Left_ToeBase_IkHandle" % (self.infoNode), self.Left_ToeBase_IkHandle)
        pyToAttr("%s.Left_ToeEnd_IkHandle" % (self.infoNode), self.Left_ToeEnd_IkHandle)
        pyToAttr("%s.Right_Toe_IK_AnimData_GRP" % (self.infoNode), self.Right_Toe_IK_AnimData_GRP)
        pyToAttr("%s.Right_Toe_IK_CTRL" % (self.infoNode), self.Right_Toe_IK_CTRL)
        pyToAttr("%s.Right_ToeBase_IK_AnimData_GRP" % (self.infoNode), self.Right_ToeBase_IK_AnimData_GRP)
        pyToAttr("%s.Right_IK_ToeBase_animData_MultNode" % (self.infoNode), self.Right_IK_ToeBase_animData_MultNode)
        pyToAttr("%s.Right_ToeBase_IK_CTRL" % (self.infoNode), self.Right_ToeBase_IK_CTRL)
        pyToAttr("%s.Right_Ankle_IK_AnimData_GRP" % (self.infoNode), self.Right_Ankle_IK_AnimData_GRP)
        pyToAttr("%s.Right_Ankle_IK_CTRL" % (self.infoNode), self.Right_Ankle_IK_CTRL)
        pyToAttr("%s.Right_ToeBase_IkHandle" % (self.infoNode), self.Right_ToeBase_IkHandle)
        pyToAttr("%s.Right_ToeEnd_IkHandle" % (self.infoNode), self.Right_ToeEnd_IkHandle)
        pyToAttr("%s.LeftHand_CTRLs_GRP" % (self.infoNode), self.LeftHand_CTRLs_GRP)
        pyToAttr("%s.RightHand_CTRLs_GRP" % (self.infoNode), self.RightHand_CTRLs_GRP)
        pyToAttr("%s.LeftFoot_FootRoll_MultNode" % (self.infoNode), self.LeftFoot_FootRoll_MultNode)
        pyToAttr("%s.LeftFoot_ToeRoll_MultNode" % (self.infoNode), self.LeftFoot_ToeRoll_MultNode)
        pyToAttr("%s.RightFoot_FootRoll_MultNode" % (self.infoNode), self.RightFoot_FootRoll_MultNode)
        pyToAttr("%s.RightFoot_ToeRoll_MultNode" % (self.infoNode), self.RightFoot_ToeRoll_MultNode)
        pyToAttr("%s.RightFoot_HipPivot_MultNode" % (self.infoNode), self.RightFoot_HipPivot_MultNode)
        pyToAttr("%s.RightFoot_BallPivot_MultNode" % (self.infoNode), self.RightFoot_BallPivot_MultNode)
        pyToAttr("%s.RightFoot_ToePivot_MultNode" % (self.infoNode), self.RightFoot_ToePivot_MultNode)
        pyToAttr("%s.RightFoot_HipSideToSide_MultNode" % (self.infoNode), self.RightFoot_HipSideToSide_MultNode)
        pyToAttr("%s.RightFoot_ToeRotate_MultNode" % (self.infoNode), self.RightFoot_ToeRotate_MultNode)
        pyToAttr("%s.IK_Dummy_Joint_GRP" % (self.infoNode), self.IK_Dummy_Joint_GRP)
        pyToAttr("%s.LeftHand_grandparent_Constraint" % (self.infoNode), self.LeftHand_grandparent_Constraint)
        pyToAttr("%s.LeftHand_grandparent_Constraint_Reverse" % (self.infoNode), self.LeftHand_grandparent_Constraint_Reverse)
        pyToAttr("%s.RightHand_grandparent_Constraint" % (self.infoNode), self.RightHand_grandparent_Constraint)
        pyToAttr("%s.RightHand_grandparent_Constraint_Reverse" % (self.infoNode), self.RightHand_grandparent_Constraint_Reverse)
        pyToAttr("%s.LeftForeArm_grandparent_Constraint" % (self.infoNode), self.LeftForeArm_grandparent_Constraint)
        pyToAttr("%s.LeftForeArm_grandparent_Constraint_Reverse" % (self.infoNode), self.LeftForeArm_grandparent_Constraint_Reverse)
        pyToAttr("%s.RightForeArm_grandparent_Constraint" % (self.infoNode), self.RightForeArm_grandparent_Constraint)
        pyToAttr("%s.RightForeArm_grandparent_Constraint_Reverse" % (self.infoNode), self.RightForeArm_grandparent_Constraint_Reverse)
        pyToAttr("%s.origAnim" % (self.infoNode), self.origAnim)
        pyToAttr("%s.origAnimation_Layer" % (self.infoNode), self.origAnimation_Layer)
        pyToAttr("%s.Mesh_Layer" % (self.infoNode), self.Mesh_Layer)
        pyToAttr("%s.Bind_Joint_Layer" % (self.infoNode), self.Bind_Joint_Layer)
        pyToAttr("%s.hulaOption" % (self.infoNode), self.hulaOption)
        pyToAttr("%s.exportList" % (self.infoNode), self.exportList)
        

        
 
 
def DJB_populatePythonSpaceWithCharacter():
    global DJB_CharacterInstance
    mayac.select(all = True, hi = True)
    unknownNodes = mayac.ls(selection = True, type = "transform")
    infoNodes = []
    for check in unknownNodes:
        if "MIXAMO_CHARACTER_infoNode" in check:
            infoNodes.append(check)
    for infoNode in infoNodes:
        DJB_CharacterInstance = DJB_Character(infoNode_ = infoNode)
    mayac.select(clear = True)

            
            
            

            
class MIXAMO_AutoControlRig_UI:
    def __init__(self):
        global Mixamo_AutoControlRig_Version
        self.name = "MIXAMO_AutoControlRig_UI"
        self.title = "MIXAMO Auto-Control-Rig v. %s" % (Mixamo_AutoControlRig_Version)

        # Begin creating the UI
        if (mayac.window(self.name, q=1, exists=1)): mayac.deleteUI(self.name)
        self.window = mayac.window(self.name, title=self.title)

        self.layout = mayac.columnLayout(adjustableColumn = True)
        mayac.text( label='', align='left' )
        
        autoSkinnerText = mayac.text( label='  If the character has unusual proportions or large appendages, the button below will create a cube that you may scale to', align='center' )
        autoSkinnerText = mayac.text( label='compensate for the unusual proportions.', align='center' )
        self.fakeBB_button = mayac.button(label='Create override Bounding Box', w=100, c=self.createOverrideBB_function)
        mayac.text( label='', align='left' )
        
        autoSkinnerText = mayac.text( label='  Step 1: Import your downloaded MIXAMO character and then press the button below.', align='left' )
        mayac.popupMenu(parent=autoSkinnerText, ctl=False, button=1) 
        mayac.menuItem(l='Go to Mixamo Auto-Rigger webpage', command = lambda *args: goToWebpage("autoRigger"))
        self.hulaOptionCheckBox = mayac.checkBox(label = 'Add Pelvis ("hula") Control     WARNING!!!!: This changes the hierarchy.  Skeleton will no longer match original fbx.', align='left' )
               
        self.setupControls_button = mayac.button(label='Rig Character', w=100, c=self.setupControls_function)
        mayac.text( label='', align='left' )
        animationText = mayac.text( label='  Step 2: Import your downloaded MIXAMO animation.', align='left' )
        mayac.popupMenu(parent=animationText, ctl=False, button=1) 
        mayac.menuItem(l='Go to Mixamo Motions webpage', command = lambda *args: goToWebpage("motions")) 
        self.browseMotions_button = mayac.button(label='Import Animation', w=100, c=self.browseMotions_function)
        mayac.text( label='', align='left' )
        mayac.text( label='  Step 3: Select the "Hips" joint of the imported motion and then press the button below.', align='left' )
        self.connectAnimationToRig_button = mayac.button(label='Copy Animation to Rig', w=100, c=self.connectAnimationToRig_function)
        mayac.text( label='', align='left' )
        mayac.text( label='', align='left' )
        mayac.text( label='Here you can bake the animation to the controls and/or revert to clean controls at any time.', align='center' )
        controlRigText = mayac.text( label="For more details see the documentation or www.mixamo.com/c/auto-control-rig-for-maya", align='center' )
        mayac.popupMenu(parent=controlRigText, ctl=False, button=1) 
        mayac.menuItem(l='Go to Auto-Control-Rig webpage', command = lambda *args: goToWebpage("autoControlRig")) 
        mayac.text( label='', align='left' )
        self.bakeAnimation_button = mayac.button(label='Bake Animation to Controls', w=100, c=self.bakeAnimation_function)
        mayac.text( label='', align='left' )
        self.bakeAnimation_button = mayac.button(label='Clear Animation Controls', w=100, c=self.clearAnimation_function)
        mayac.text( label='', align='left' )
        mayac.text( label='', align='left' )
        self.deleteOrigAnimation_button = mayac.button(label='Delete Original Animation', w=100, c=self.deleteOrigAnimation_function)
        mayac.text( label='', align='left' )
        mayac.text( label='  Note: The original animation resides in the scene on its own layer until deleted.', align='left' )
        mayac.text( label='', align='left' )
        
        self.exportWithMeshOptionCheckBox = mayac.checkBox(label = 'Export Mesh with Skeleton', align='left' )
        self.exportBakedSkeleton_button = mayac.button(label='Export Baked Skeleton', w=100, c=self.exportBakedSkeleton_function)
        
        mayac.text( label='', align='left' )
        mayac.text( label='', align='left' )
        happyAnimatingText = mayac.text( label='  Happy Animating! www.mixamo.com', align='left' )
        mayac.popupMenu(parent=happyAnimatingText, ctl=False, button=1) 
        mayac.menuItem(l='Go to Mixamo.com', command = lambda *args: goToWebpage("mixamo")) 


        mayac.window(self.window, e=1, w=650, h=615, sizeable = 0) #580,560
        mayac.showWindow(self.window)
            

    def createOverrideBB_function(self, arg = None):
        global DJB_CharacterInstance
        DJB_CharacterInstance = None
        DJB_populatePythonSpaceWithCharacter()
        if not DJB_CharacterInstance:
            global DJB_Character_ProportionOverrideCube
            if mayac.objExists(DJB_Character_ProportionOverrideCube):
                mayac.delete(DJB_Character_ProportionOverrideCube)
                DJB_Character_ProportionOverrideCube = ""
            DJB_Character_ProportionOverrideCube = mayac.polyCube(n = "Bounding_Box_Override_Cube", ch = False)[0]
            
            #get default proportions
            mesh = []
            temp = mayac.ls(geometry = True)
            shapes = []
            for geo in temp:
                if "ShapeOrig" not in geo:
                    shapes.append(geo)
                    transform = mayac.listRelatives(geo, parent = True)[0]
            for geo in shapes:
                parent = mayac.listRelatives(geo, parent = True)[0]
                mesh.append(mayac.listRelatives(parent, children = True, type = "shape")[0])
            #place and lock up cube
            BoundingBox = mayac.exactWorldBoundingBox(mesh)
            mayac.move(BoundingBox[0], BoundingBox[1], BoundingBox[5], "%s.vtx[0]" % (DJB_Character_ProportionOverrideCube), absolute = True)
            mayac.move(BoundingBox[3], BoundingBox[1], BoundingBox[5], "%s.vtx[1]" % (DJB_Character_ProportionOverrideCube), absolute = True)
            mayac.move(BoundingBox[0], BoundingBox[4], BoundingBox[5], "%s.vtx[2]" % (DJB_Character_ProportionOverrideCube), absolute = True)
            mayac.move(BoundingBox[3], BoundingBox[4], BoundingBox[5], "%s.vtx[3]" % (DJB_Character_ProportionOverrideCube), absolute = True)
            mayac.move(BoundingBox[0], BoundingBox[4], BoundingBox[2], "%s.vtx[4]" % (DJB_Character_ProportionOverrideCube), absolute = True)
            mayac.move(BoundingBox[3], BoundingBox[4], BoundingBox[2], "%s.vtx[5]" % (DJB_Character_ProportionOverrideCube), absolute = True)
            mayac.move(BoundingBox[0], BoundingBox[1], BoundingBox[2], "%s.vtx[6]" % (DJB_Character_ProportionOverrideCube), absolute = True)
            mayac.move(BoundingBox[3], BoundingBox[1], BoundingBox[2], "%s.vtx[7]" % (DJB_Character_ProportionOverrideCube), absolute = True)
            pivotPointX = ((BoundingBox[3] - BoundingBox[0]) / 2) + BoundingBox[0]
            pivotPointY = BoundingBox[1]
            pivotPointZ = ((BoundingBox[5] - BoundingBox[2]) / 2) + BoundingBox[2]
            mayac.move(pivotPointX, pivotPointY, pivotPointZ, "%s.scalePivot" % (DJB_Character_ProportionOverrideCube), "%s.rotatePivot" % (DJB_Character_ProportionOverrideCube), absolute = True)
            mayac.setAttr("%s.tx" % (DJB_Character_ProportionOverrideCube),lock = True)
            mayac.setAttr("%s.ty" % (DJB_Character_ProportionOverrideCube),lock = True)
            mayac.setAttr("%s.tz" % (DJB_Character_ProportionOverrideCube),lock = True)
            mayac.setAttr("%s.rx" % (DJB_Character_ProportionOverrideCube),lock = True)
            mayac.setAttr("%s.ry" % (DJB_Character_ProportionOverrideCube),lock = True)
            mayac.setAttr("%s.rz" % (DJB_Character_ProportionOverrideCube),lock = True)
            
        else:
            OpenMaya.MGlobal.displayError("You must create and scale the override cube before rigging the character.")
        mayac.select(clear = True)
        
            
    def setupControls_function(self, arg = None):
        global DJB_CharacterInstance
        DJB_CharacterInstance = None
        DJB_populatePythonSpaceWithCharacter()
        if not DJB_CharacterInstance:
            joints = mayac.ls(type = "joint")
            if not joints:
                OpenMaya.MGlobal.displayError("There must be a Mixamo Autorigged character in the scene.")
            else:
                hulaValue = mayac.checkBox(self.hulaOptionCheckBox, query = True, value = True)
                DJB_CharacterInstance = DJB_Character(hulaOption_ = hulaValue)
                DJB_CharacterInstance.fixArmsAndLegs()
                DJB_CharacterInstance.makeAnimDataJoints()
                DJB_CharacterInstance.makeControls()
                DJB_CharacterInstance.hookUpControls()
                DJB_CharacterInstance.writeInfoNode()
        else:
            OpenMaya.MGlobal.displayError("There is already a rig in the scene")
        mayac.select(clear = True)
        
        
    def browseMotions_function(self, arg = None):
        mayac.Import()
    
    def connectAnimationToRig_function(self, arg = None):
        global DJB_CharacterInstance
        selection = mayac.ls(selection = True)
        DJB_CharacterInstance = None
        DJB_populatePythonSpaceWithCharacter()
        if not DJB_CharacterInstance:
            OpenMaya.MGlobal.displayError("You must rig a character first")
        elif len(selection) == 0 or mayac.nodeType(selection[0]) != "joint":
            OpenMaya.MGlobal.displayError("You must select the 'Hips' Joint of the imported animation")
        elif DJB_CharacterInstance.Hips.Bind_Joint:
            isCorrectRig = DJB_CharacterInstance.checkSkeletonProportions(selection[0])
            if isCorrectRig:
                DJB_CharacterInstance.transferMotionToAnimDataJoints(selection[0], newStartTime = 0, mixMethod = "insert")
            else:
                OpenMaya.MGlobal.displayError("Imported Skeleton does not match character!")
            
    def deleteOrigAnimation_function(self, arg = None):
        global DJB_CharacterInstance
        DJB_CharacterInstance = None
        DJB_populatePythonSpaceWithCharacter()
        if not DJB_CharacterInstance:
            OpenMaya.MGlobal.displayError("No Character Found!")
        else:
            if DJB_CharacterInstance.origAnim:
                DJB_CharacterInstance.deleteOriginalAnimation()
            else:
                OpenMaya.MGlobal.displayError("No Original Animation Found!")
            
    def bakeAnimation_function(self, arg = None):
        global DJB_CharacterInstance
        DJB_CharacterInstance = None
        DJB_populatePythonSpaceWithCharacter()
        if DJB_CharacterInstance:
            DJB_CharacterInstance.bakeAnimationToControls()
        else:
            OpenMaya.MGlobal.displayError("No Character Found!")
        
    def clearAnimation_function(self, arg = None):
        global DJB_CharacterInstance
        DJB_CharacterInstance = None
        DJB_populatePythonSpaceWithCharacter()
        if DJB_CharacterInstance:
            DJB_CharacterInstance.clearAnimationControls()
        else:
            OpenMaya.MGlobal.displayError("No Character Found!")
            
    def exportBakedSkeleton_function(self, arg = None):
        global DJB_CharacterInstance
        DJB_CharacterInstance = None
        DJB_populatePythonSpaceWithCharacter()
        if DJB_CharacterInstance:
            keepMesh = mayac.checkBox(self.exportWithMeshOptionCheckBox, query = True, value = True)
            DJB_CharacterInstance.createExportSkeleton(keepMesh_ = keepMesh)
            DJB_CharacterInstance.exportSkeleton()
            version = mel.eval("float $ver = `getApplicationVersionAsFloat`;")
            if version != 2010.0:
                DJB_CharacterInstance.deleteExportSkeleton()
            if version == 2010.0:
                OpenMaya.MGlobal.displayInfo("You may delete the newly created geometry and joints after exporting is complete")
        else:
            OpenMaya.MGlobal.displayError("No Character Found!")





DJB_MIX_ACS_UI = MIXAMO_AutoControlRig_UI()