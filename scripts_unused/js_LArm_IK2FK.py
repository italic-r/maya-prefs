##########################
#Jason Sutter
#All Rights Reserved 2012
#hello@jasonanimation.net 
#
#Signature: js_LArm_ik2FK()
#
#Left Arm ik controls--> fk controls snap
##########################
import maya.cmds as cmds

def js_LArm_ik2FK():
    #Start of ik to fk matching 
    # Get the XYZ Translation values from the left arm pole vector "dummy" node
    # We don’t care about the rotation from the “dummy” node#
    LelbAimDummyTX = cmds.getAttr("LOC_L_PoleVectorDummy.tx")
    LelbAimDummyTY = cmds.getAttr("LOC_L_PoleVectorDummy.ty")
    LelbAimDummyTZ = cmds.getAttr("LOC_L_PoleVectorDummy.tz")
    
    # Get the XYZ Translation values from the left Arm ik Control "dummy"
    LwristDummyX = cmds.getAttr("LOC_L_WristDummy.tx")
    LwristDummyY = cmds.getAttr("LOC_L_WristDummy.ty")
    LwristDummyZ = cmds.getAttr("LOC_L_WristDummy.tz")
    
    # Get the XYZ Rotation values from the left Arm ik Control "dummy"
    LwristDummyRX = cmds.getAttr("LOC_L_WristDummy.rx")
    LwristDummyRY = cmds.getAttr("LOC_L_WristDummy.ry")
    LwristDummyRZ = cmds.getAttr("LOC_L_WristDummy.rz")
    
    #Move the Left arm Pole Vector control to the "dummy" position
    cmds.setAttr("CNTRL_L_ElbowPV.tx",LelbAimDummyTX)
    cmds.setAttr("CNTRL_L_ElbowPV.ty",LelbAimDummyTY)
    cmds.setAttr("CNTRL_L_ElbowPV.tz ",LelbAimDummyTZ)
    
    # Move and rotate the left arm ik control to the "dummy" position
    cmds.setAttr("CNTRL_L_IK_Wrist.tx ",LwristDummyX)
    cmds.setAttr("CNTRL_L_IK_Wrist.ty" ,LwristDummyY)
    cmds.setAttr("CNTRL_L_IK_Wrist.tz", LwristDummyZ)
    
    cmds.setAttr("CNTRL_L_IK_Wrist.rx ",LwristDummyRX)
    cmds.setAttr("CNTRL_L_IK_Wrist.ry", LwristDummyRY)
    cmds.setAttr("CNTRL_L_IK_Wrist.rz ",LwristDummyRZ)
    
# Run Script
ik2FK = js_LArm_ik2FK()

#end of js_LArm_ik2FK()
