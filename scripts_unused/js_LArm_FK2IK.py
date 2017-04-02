##########################
#Jason Sutter
#All Rights Reserved 2012
#hello@jasonanimation.net 
#
#Signature: js_LArm_fk2IK()
#
# ----- Left Arm fk controls--> ik controls snap ------ 
##########################
import maya.cmds as cmds

def js_LArm_fk2IK(():
    # Get the XYZ Rotation values of the ik shoulder bone
    L_ArmRX = cmds.getAttr("JNT_IK_L_Arm.rx")
    L_ArmRY = cmds.getAttr("JNT_IK_L_Arm.ry")
    L_ArmRZ = cmds.getAttr("JNT_IK_L_Arm.rz")
    
    
    #Get the Y Rotation values of the ik elbow bone
    L_LowerArmRX = cmds.getAttr("JNT_IK_L_LowerArm.rx")
    L_LowerArmRY = cmds.getAttr("JNT_IK_L_LowerArm.ry")
    L_LowerArmRZ = cmds.getAttr("JNT_IK_L_LowerArm.rz")
    
    # Get the XYZ Rotation values of the ik wrist bone
    L_WristRX = cmds.getAttr("JNT_IK_L_Wrist.rx")
    L_WristRY = cmds.getAttr("JNT_IK_L_Wrist.ry")
    L_WristRZ = cmds.getAttr("JNT_IK_L_Wrist.rz")
    
    
    
    # Match the XYZ Rotation values for the fk shoulder bone
    cmds.setAttr("JNT_FK_L_Arm.rx", L_ArmRX)
    cmds.setAttr("JNT_FK_L_Arm.ry", L_ArmRY)
    cmds.setAttr("JNT_FK_L_Arm.rz", L_ArmRZ)
    
    # Match the Y Rotation value for the fk elbow bone
    cmds.setAttr ("JNT_FK_L_LowerArm.rx", L_LowerArmRX )
    cmds.setAttr ("JNT_FK_L_LowerArm.ry", L_LowerArmRY )
    cmds.setAttr ("JNT_FK_L_LowerArm.rz", L_LowerArmRZ )
    
    # Match the XYZ Rotation values for the fk wrist bone
    cmds.setAttr ("JNT_FK_L_Wrist.rx",L_WristRX)
    cmds.setAttr ("JNT_FK_L_Wrist.ry",L_WristRY)
    cmds.setAttr ("JNT_FK_L_Wrist.rz",L_WristRZ)

    

# Run Script
fk2IK = js_LArm_fk2IK()

#end of js_LArm_fk2IK()