'''
Smear Limb Script
By Daniel V. Rico
'''

import maya.cmds as cmds


class Smear_Limb:

    def __init__(self):
        self.showUI()

    def showUI(self):
        '''
        Create GUI so that the user can generate the components of a smear limb
        '''
        if cmds.window('Smearing Poly', exists=True):
            cmds.deleteUI('Smearing Poly', window=True)
        window = cmds.window('Smearing Poly', iconName='SmrLimb', widthHeight=(300, 500))
        layoutSetup = cmds.rowColumnLayout(numberOfColumns=2, columnAttach=(
            1, 'right', 0), columnWidth=[(1, 50), (2, 300)])
        cmds.separator(style='single', h=40)

        cmds.text(label='Please select the original geometry')
        cmds.separator(style='single', h=40)

        cmds.button('setGeo', label='Set Geo Base',
                    command=self.setGeometry, w=100, h=40)
        allFather = cmds.textField("allFather", ed=False, visible=False)
        oldMan = cmds.textField("oldGeo", ed=False)
        cmds.separator(style='single', h=40)

        cmds.text(label='Please select the origin pivot of the limb you wish to smear')
        cmds.separator(style='single', h=40)

        cmds.button('setBase', label='Set Pivot Base',
                    command=self.setOrigin, w=100, h=40)
        cmds.separator(style='single', h=20)
        theSea = cmds.textField("theSea", ed=False)
        cmds.separator(style='single', h=20)

        cmds.text(label='Please set the name for the smear geo')
        cmds.separator(style='single', h=20)

        self.chainName = cmds.textField()
        cmds.separator(style='single', h=20)

        cmds.text(label='Please select the geometry faces you wish to clone')
        cmds.separator(style='single', h=40)

        cmds.button('setClone', label='Set Clone Geo',
                    command=self.setClone, w=100, h=40)
        cmds.separator(style='single', h=20)

        cmds.text(label="Please select the control's new parent group")
        cmds.separator(style='single', h=20)

        cmds.button('setOrder', label='Set Control Home',
                    command=self.setOrder, w=100, h=40)
        theEnd = cmds.textField("theEnd", ed=False, visible=False)
        cmds.showWindow(window)

    def setGeometry(self, *arg):
        '''
        Set the original geometry as the point of origin for the new control
        '''
        # select the original geo, then run this
        Old = cmds.ls(selection=True)
        cmds.textField("allFather", edit=True, text=Old[0])
        allFather = cmds.textField("allFather", query=True, text=True)
        print allFather

        cmds.duplicate(returnRootsOnly=True, inputConnections=True)
        Original = cmds.ls(selection=True)
        print Original

        cmds.textField("oldGeo", edit=True, text=Original[0])
        print "selection confirmed"

        cmds.setAttr(allFather + '.overrideEnabled', 1)
        cmds.setAttr(allFather + '.overrideDisplayType', 1)
        cmds.select(clear=True)

    def setOrigin(self, *arg):
        '''
        Sets the selection as the point of orientation
        and position for the new control
        '''
        # Select the base control you want the arm to move from, then run this
        Pivot = cmds.ls(selection=True)
        print Pivot
        cmds.textField("theSea", edit=True, text=Pivot[0])
        print "selection confirmed"
        cmds.select(clear=True)

    def setClone(self, *arg):
        '''
        Creating the smear and its associated control
        '''
        self.chainText = cmds.textField(self.chainName, query=True, text=True)

        # select the arm geo you want to act as the smear, then run this
        if cmds.objExists(self.chainText + "_smearGeo"):
            raise KeyError('Please change the name in the text field')
        else:
            print "Making geo clones."

        oldMan = cmds.textField("oldGeo", query=True, text=True)
        theSea = cmds.textField("theSea", query=True, text=True)
        Origin = cmds.ls(selection=True)
        cmds.select(Origin)
        cmds.polyChipOff(constructionHistory=1, keepFacesTogether=True,
                         duplicate=True, off=0)

        if cmds.objExists('originalGeo'):
            cmds.select('originalGeo')
            cmds.rename('originalGeo_Grp')
        else:
            cmds.select(oldMan)

        cmds.polySeparate()
        SuperSmear = cmds.ls(selection=True)
        cmds.select(SuperSmear[0])
        print SuperSmear[0]

        g1 = cmds.rename("originalGeo")
        cmds.select(SuperSmear[1])
        print SuperSmear[1]

        g2 = cmds.rename(self.chainText + "_smearGeo")
        del SuperSmear[:]
        SuperSmear = [g1, g2]

        cmds.setAttr('originalGeoShape.doubleSided', 0)
        cmds.setAttr(self.chainText + '_smearGeoShape.doubleSided', 0)

        # meant to group the new arm geo twice
        Grp = cmds.group(empty=True, name=self.chainText + "_Clone_Arm_Grp")
        cmds.parent(Grp, oldMan)
        Offset = cmds.group(empty=True, name=self.chainText + "_Clone_Arm_Offset")
        cmds.parent(Offset, Grp)
        cmds.parent(SuperSmear[1], Offset)
        cmds.select(clear=True)

        # Organize the new Transformation Null
        cmds.select('transform1')
        theProphet = cmds.rename(self.chainText + '_transform')
        if cmds.objExists('Smear_DO_NOT_TOUCH'):
            print "No need for another 'DNT', as one already exists"
        else:
            cmds.group(empty=True, name='Smear_DO_NOT_TOUCH')
            cmds.parent('Smear_DO_NOT_TOUCH', oldMan)
        Agro = ('Smear_DO_NOT_TOUCH')
        cmds.parent(theProphet, Agro)
        cmds.select(clear=True)

        # Create the adjustment Locator
        if cmds.objExists(self.chainText + "_smearLoc"):
            print "Locator exists, proceeding"
        else:
            cmds.spaceLocator(name=self.chainText + "_smearLoc")

        Loc = (self.chainText + "_smearLoc")
        cmds.parent(Loc, Grp)
        cmds.parentConstraint(oldMan, Loc, name=self.chainText + "_warpPC")
        cmds.parentConstraint(theSea, Grp, name=self.chainText + "_warpGrpPC")
        cmds.select(clear=True)

        # Connects Locator's translate and rotate attributes to clone arm attributes
        cmds.connectAttr(self.chainText + '_smearLoc.translate',
                         self.chainText + '_smearGeo.translate')
        cmds.connectAttr(self.chainText + '_smearLoc.rotate',
                         self.chainText + '_smearGeo.rotate')

        # Create control for the new arm
        cmds.curve(degree=1,
                   point=[(0, 0, 3), (2, 0, 2), (3, 0, 0), (2, 0, -2),
                          (0, 0, -3), (-2, 0, -2), (-3, 0, 0), (-2, 0, 2),
                          (0, 0, 3), (0, -2, 2), (0, -3, 0), (0, -2, -2),
                          (0, 0, -3), (0, 2, -2), (0, 3, 0), (0, 2, 2),
                          (0, 0, 3), (0, 0, 0), (-3, 0, 0), (3, 0, 0),
                          (0, 0, 0), (0, -3, 0), (0, 3, 0), (0, 0, 0),
                          (0, 0, -3), (0, 0, 0), (3, 0, 0), (2, 2, 0),
                          (0, 3, 0), (-2, 2, 0), (-3, 0, 0), (-2, -2, 0),
                          (0, -3, 0), (2, -2, 0), (3, 0, 0)],
                   knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                         15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
                         28, 29, 30, 31, 32, 33, 34])
        warpControl = cmds.rename(self.chainText + '_Warp_Ctrl')
        WarpControlGroup = cmds.group(warpControl, name=self.chainText + '_Warp_Ctrl_Grp')
        cmds.parent(WarpControlGroup, theSea, relative=True)
        cmds.parent(WarpControlGroup, world=True)
        cmds.select(clear=True)

        if cmds.objExists('Warp_Controls_Group'):
            print "The host thrives"
        elif cmds.objExists('Warp_Ctrls_Group'):
            print "The host thrives"
        else:
            cmds.group(empty=True, name='Warp_Ctrls_Group')

        cmds.parent(WarpControlGroup, 'Warp_Ctrls_Group')
        cmds.parentConstraint(warpControl, Offset)
        cmds.scaleConstraint(warpControl, Offset)
        cmds.setAttr(Offset + '.t', lock=True)
        cmds.setAttr(Offset + '.r', lock=True)
        cmds.setAttr(Offset + '.s', lock=True)
        cmds.setAttr(Offset + '.v', lock=True)
        cmds.setAttr(Grp + '.t', lock=True)
        cmds.setAttr(Grp + '.r', lock=True)
        cmds.setAttr(Grp + '.s', lock=True)
        cmds.setAttr(Grp + '.v', lock=True)
        cmds.setAttr(Loc + '.t', lock=True)
        cmds.setAttr(Loc + '.r', lock=True)
        cmds.setAttr(Loc + '.s', lock=True)
        cmds.setAttr(Loc + '.v', 0, lock=True)
        cmds.setAttr(Agro + '.t', lock=True)
        cmds.setAttr(Agro + '.r', lock=True)
        cmds.setAttr(Agro + '.s', lock=True)
        cmds.setAttr(Agro + '.v', lock=True)
        cmds.setAttr(theProphet + '.t', lock=True)
        cmds.setAttr(theProphet + '.r', lock=True)
        cmds.setAttr(theProphet + '.s', lock=True)
        cmds.setAttr(theProphet + '.v', lock=True)
        cmds.select(clear=True)

        # Connect the smear control to the rig
        cmds.parentConstraint(theSea, WarpControlGroup, maintainOffset=True)
        cmds.setAttr(self.chainText + '_Warp_Ctrl.v', lock=True, keyable=False, channelBox=False)
        cmds.setAttr(self.chainText + '_Warp_Ctrl_Grp.t', lock=True)
        cmds.setAttr(self.chainText + '_Warp_Ctrl_Grp.r', lock=True)
        cmds.setAttr(self.chainText + '_Warp_Ctrl_Grp.s', lock=True)
        cmds.setAttr(self.chainText + '_Warp_Ctrl_Grp.v', lock=True)
        cmds.setAttr(self.chainText + '_Warp_CtrlShape.overrideDisplayType', 1)
        print "Please select the group you wish to place the smear pivot control to"

    def setOrder(self, *arg):
        '''
        Sends the control home
        '''
        # Move the smear control into the proper rig sub group
        theEnd = cmds.textField("theEnd", query=True, text=True)
        allFather = cmds.textField("allFather", query=True, text=True)
        oldMan = cmds.textField("oldGeo", query=True, text=True)
        newHome = cmds.ls(selection=True)
        cmds.select(newHome)

        if cmds.objExists('Warp_Controls_Group'):
            print "We're cool, dude."
            # cmds.select('Warp_Controls_Group')
            # Horn=cmds.ls(selection=True, long=True)
            # cmds.textField("theEnd", edit=True, text=Horn[0])
        else:
            cmds.parent('Warp_Ctrls_Group', newHome)
            cmds.select('Warp_Ctrls_Group')
            cmds.rename('Warp_Controls_Group')
            cmds.setAttr('Warp_Controls_Group.v', lock=True)
            cmds.setAttr('Warp_Controls_Group.t', lock=True)
            cmds.setAttr('Warp_Controls_Group.r', lock=True)
            cmds.setAttr('Warp_Controls_Group.s', lock=True)
        cmds.delete("originalGeo")
        cmds.select(oldMan)
        cmds.rename(self.chainText + '_Smear_Geo_Grp')

        if cmds.objExists(self.chainText + "_Smear_Geo_Grp|originalGeo_Grp"):
            cmds.delete(self.chainText + "_Smear_Geo_Grp|originalGeo_Grp")
        else:
            print "No worries, human"

        cmds.setAttr(allFather + '.overrideEnabled', 0)
        cmds.setAttr(allFather + '.overrideDisplayType', 0)
        cmds.select(clear=True)

        print "Your transaction has been complete."
        print "If you would like to begin a new transaction, please return to the start, and begin again"


smrLmb = Smear_Limb()
