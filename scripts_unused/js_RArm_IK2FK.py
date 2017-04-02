##########################
#Jason Sutter
#All Rights Reserved 2012
#hello@jasonanimation.net 
#
#Signature: js_RArm_ik2FK()
#
#Left Arm ik controls--> fk controls snap
##########################
import maya.cmds as cmds

def js_RArm_ik2FK():
    # Get the XYZ Translation values from the left arm pole vector "dummy" node
    # We don’t care about the rotation from the “dummy” node#
    RelbAimDummyTX = cmds.getAttr("LOC_R_PoleVectorDummy.tx")
    RelbAimDummyTY = cmds.getAttr("LOC_R_PoleVectorDummy.ty")
    RelbAimDummyTZ = cmds.getAttr("LOC_R_PoleVectorDummy.tz")
    
    # Get the XYZ Translation values from the left Arm ik Control "dummy"
    RwristDummyX = cmds.getAttr("LOC_R_WristDummy.tx")
    RwristDummyY = cmds.getAttr("LOC_R_WristDummy.ty")
    RwristDummyZ = cmds.getAttr("LOC_R_WristDummy.tz")
    
    # Get the XYZ Rotation values from the left Arm ik Control "dummy"
    RwristDummyRX = cmds.getAttr("LOC_R_WristDummy.rx")
    RwristDummyRY = cmds.getAttr("LOC_R_WristDummy.ry")
    RwristDummyRZ = cmds.getAttr("LOC_R_WristDummy.rz")
    
    #Move the Left arm Pole Vector control to the "dummy" position
    cmds.setAttr("CNTRL_R_ElbowPV.tx",RelbAimDummyTX)
    cmds.setAttr("CNTRL_R_ElbowPV.ty",RelbAimDummyTY)
    cmds.setAttr("CNTRL_R_ElbowPV.tz ",RelbAimDummyTZ)
    
    # Move and rotate the left arm ik control to the "dummy" position
    cmds.setAttr("CNTRL_R_IK_Wrist.tx ",RwristDummyX)
    cmds.setAttr("CNTRL_R_IK_Wrist.ty" ,RwristDummyY)
    cmds.setAttr("CNTRL_R_IK_Wrist.tz", RwristDummyZ)
    
    cmds.setAttr("CNTRL_R_IK_Wrist.rx ",RwristDummyRX)
    cmds.setAttr("CNTRL_R_IK_Wrist.ry", RwristDummyRY)
    cmds.setAttr("CNTRL_R_IK_Wrist.rz ",RwristDummyRZ)
    
# Run Script
ik2FK = js_RArm_ik2FK()

#end of js_RArm_ik2FK()
