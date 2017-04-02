###############################################################################
# Name: 
#   display_override.py
#
# Description: 
#   Quickly override the display color of one or more selected objects 
#   through a simple GUI.
#
# Author: 
#   Chris Zurbrigg (http://zurbrigg.com)
#
# Copyright (C) 2012 Chris Zurbrigg. All rights reserved.
###############################################################################

import maya.cmds as cmds
import maya.OpenMaya as om

class DisplayColorOverride:
    
    MAX_OVERRIDE_COLORS = 32
    
    @staticmethod
    def override_color(color_index):
        if (color_index >= DisplayColorOverride.MAX_OVERRIDE_COLORS):
            om.MGlobal.displayError("Color index out-of-range (must be less than 32)")
            return False
        
        selection = cmds.ls(selection=True)
        if not selection:
            om.MGlobal.displayError("No objects selected")
            return False

        for obj in selection:
            shapeNodes = cmds.listRelatives(obj, shapes=True)
            
            for shape in shapeNodes:
                try:
                    cmds.setAttr("{0}.overrideEnabled".format(shape), True)
                    cmds.setAttr("{0}.overrideColor".format(shape), color_index)
                except:
                    om.MGlobal.displayWarning("Failed to override color: {0}".format(shape))
        
        return True
        
    @staticmethod
    def use_defaults():
        shapes = DisplayColorOverride.shape_nodes()
        if shapes == None:
            om.MGlobal.displayError("No objects selected")
            return False
            
        for shape in shapes:
            try:
                cmds.setAttr("{0}.overrideEnabled".format(shape), False)
            except:
                om.MGlobal.displayWarning("Failed to restore defaults: {0}".format(shape))
            
        return True
        
    @staticmethod
    def shape_nodes():
        selection = cmds.ls(selection=True)
        if not selection:
            return None
          
        shapes = []   
        for obj in selection:
            shapes.extend(cmds.listRelatives(obj, shapes=True))
                          
        return shapes
            
        
            

class DisplayColorOverrideUi:
    
    WINDOW_NAME = "czDisplayColorOverrideUi"

    FORM_OFFSET = 2

    color_palette = None
    
    @staticmethod
    def display():
        DisplayColorOverrideUi.delete()
        
        main_window = cmds.window(DisplayColorOverrideUi.WINDOW_NAME, title="Display Color Override", rtf=True, sizeable=False)        
        main_layout = cmds.formLayout(parent=main_window)

        columns = DisplayColorOverride.MAX_OVERRIDE_COLORS / 2
        rows = 2
        cell_width = 17
        cell_height = 17
        DisplayColorOverrideUi.color_palette = cmds.palettePort(dimensions=(columns, rows), 
                                                                transparent=0,
                                                                width=(columns*cell_width),
                                                                height=(rows*cell_width),
                                                                topDown=True,
                                                                colorEditable=False);
        
        for index in range(1, DisplayColorOverride.MAX_OVERRIDE_COLORS):
            color_component = cmds.colorIndex(index, q=True)
            cmds.palettePort(DisplayColorOverrideUi.color_palette,
                             edit=True,
                             rgbValue=(index, color_component[0], color_component[1], color_component[2]))
            
        cmds.palettePort(DisplayColorOverrideUi.color_palette,
                       edit=True,
                       rgbValue=(0, 0.6, 0.6, 0.6))
        
        
        
        # Create the Override and Default buttons
        override_button = cmds.button(label="Override",
                                      command="DisplayColorOverrideUi.override()",
                                      parent=main_layout)
                                    
        default_button = cmds.button(label="Default",
                                     command="DisplayColorOverrideUi.default()",
                                     parent=main_layout)
        

                
        # Layout the Color Palette
        cmds.formLayout(main_layout, edit=True, 
                        attachForm=(DisplayColorOverrideUi.color_palette, "top", DisplayColorOverrideUi.FORM_OFFSET));
        cmds.formLayout(main_layout, edit=True, 
                        attachForm=(DisplayColorOverrideUi.color_palette, "left", DisplayColorOverrideUi.FORM_OFFSET));
        cmds.formLayout(main_layout, edit=True, 
                        attachForm=(DisplayColorOverrideUi.color_palette, "right", DisplayColorOverrideUi.FORM_OFFSET));        
        
        # Layout the Override and Default buttons
        cmds.formLayout(main_layout, edit=True, 
                        attachControl=(override_button, "top", DisplayColorOverrideUi.FORM_OFFSET, DisplayColorOverrideUi.color_palette))        
        cmds.formLayout(main_layout, edit=True, 
                        attachForm=(override_button, "left", DisplayColorOverrideUi.FORM_OFFSET))
        cmds.formLayout(main_layout, edit=True, 
                        attachPosition=(override_button, "right", 0, 50))
        
        cmds.formLayout(main_layout, edit=True, 
                        attachOppositeControl=(default_button, "top", 0, override_button))
        cmds.formLayout(main_layout, edit=True, 
                        attachControl=(default_button, "left", 0, override_button))
        cmds.formLayout(main_layout, edit=True, 
                        attachForm=(default_button, "right", DisplayColorOverrideUi.FORM_OFFSET))
        
        cmds.showWindow(main_window)
    
    
    @staticmethod
    def delete():
        if cmds.window(DisplayColorOverrideUi.WINDOW_NAME, exists=True):
            cmds.deleteUI(DisplayColorOverrideUi.WINDOW_NAME, window=True)
            
    
    @staticmethod
    def override():
        color_index = cmds.palettePort(DisplayColorOverrideUi.color_palette, q=True, setCurCell=True)
        DisplayColorOverride.override_color(color_index)
        
    @staticmethod
    def default():
        DisplayColorOverride.use_defaults()



if __name__ == "__main__":
    
    DisplayColorOverrideUi.display()
    
  