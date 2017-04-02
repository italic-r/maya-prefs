##########################
#Jason Sutter
#All Rights Reserved 2012
#hello@jasonanimation.net 
#
#Signature: js_RArm_fk2IK()
#
# ----- Left Arm fk controls--> ik controls snap ------ 
##########################
import maya.cmds as cmds

def js_RArm_fk2IK():
    # Get the XYZ Rotation values of the ik shoulder bone
    R_ArmRX = cmds.getAttr("JNT_IK_R_Arm.rx")
    R_ArmRY = cmds.getAttr("JNT_IK_R_Arm.ry")
    R_ArmRZ = cmds.getAttr("JNT_IK_R_Arm.rz")
    
    
    #Get the Y Rotation values of the ik elbow bone
    R_LowerArmRX = cmds.getAttr("JNT_IK_R_LowerArm.rx")
    R_LowerArmRY = cmds.getAttr("JNT_IK_R_LowerArm.ry")
    R_LowerArmRZ = cmds.getAttr("JNT_IK_R_LowerArm.rz")
    
    # Get the XYZ Rotation values of the ik wrist bone
    R_WristRX = cmds.getAttr("JNT_IK_R_Wrist.rx")
    R_WristRY = cmds.getAttr("JNT_IK_R_Wrist.ry")
    R_WristRZ = cmds.getAttr("JNT_IK_R_Wrist.rz")
    
    
    
    # Match the XYZ Rotation values for the fk shoulder bone
    cmds.setAttr("JNT_FK_R_Arm.rx", R_ArmRX)
    cmds.setAttr("JNT_FK_R_Arm.ry", R_ArmRY)
    cmds.setAttr("JNT_FK_R_Arm.rz", R_ArmRZ)
    
    # Match the Y Rotation value for the fk elbow bone
    cmds.setAttr ("JNT_FK_R_LowerArm.rx", R_LowerArmRX )
    cmds.setAttr ("JNT_FK_R_LowerArm.ry", R_LowerArmRY )
    cmds.setAttr ("JNT_FK_R_LowerArm.rz", R_LowerArmRZ )
    
    # Match the XYZ Rotation values for the fk wrist bone
    cmds.setAttr ("JNT_FK_R_Wrist.rx",R_WristRX)
    cmds.setAttr ("JNT_FK_R_Wrist.ry",R_WristRY)
    cmds.setAttr ("JNT_FK_R_Wrist.rz",R_WristRZ)

    

# Run Script
fk2IK = js_RArm_fk2IK()

#end of js_RArm_fk2IK()