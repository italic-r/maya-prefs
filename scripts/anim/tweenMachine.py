"""
tweenMachine.py

author:         Justin S Barrett

description:    Tool for creating breakdown or "tween" keyframes between the
                previous and next keys, using a slider to adjust the bias/weight
                that the surrounding keys have over the new key.

usage:          import tweenMachine
                tweenMachine.start()
                
revisions:
    - 04.12.2013 - 3.0.0 - jbarrett
        - Initial publish after conversion to Python
    - 05.22.2015 - 3.0.0b1 - jbarrett
        - First public beta release (limited feature set)
    - 07.11.2015 - 3.0.0b1a - jbarrett
        - Fixed: Overshoot mode reset properly from settings when restarting TM
        - Fixed: When grabbing the global key tangent, make sure it's a string
        - Fixed: If there are no curves to tween, force an empty list
        - Changed: Disabled toolbar opt for Maya 2013 until a fix can be found
    - 06.07.2016 - 3.0.0b1b - jbarrett
        - Work around issue with keyTangent command in Maya 2016 Extension 2 
        
to-do:
    
"""

#-------------------------------------------------------------------------
#----------------------------------------------------------- Imports -----

# Built-in
import os
import urllib2
import xml.etree.cElementTree as etree

# Third-party
import maya.cmds as mc
import maya.mel as mel

# Custom

#-------------------------------------------------------------------------
#----------------------------------------------------------- Globals -----

__version__ = "3.0.0 b1b"
MAYA_VERSION = mc.about(version=True)

#-------------------------------------------------------------------------
#--------------------------------------------------------- Functions -----

def clear_menu(menu):
    """
    Clear the specified menu of its current contents
    """
    try:
        [mc.deleteUI(i) for i in mc.menu(menu, q=True, ia=True)]
    except:
        pass

def defer_delete(item):
    """
    Defer the deletion of a UI item to prevent Maya from crashing when that UI
    item is still active as it's deleted
    """
    mc.evalDeferred("mc.deleteUI('" + item + "')")
        
def find_ui(uitype):
    found = mc.lsUI(type=uitype)
    if found is None:
        return ""
    for item in found:
        try:
            doctag = eval("mc." + uitype + "(item, q=True, docTag=True)")
        except RuntimeError:
            doctag = ""
        if doctag == "tweenMachine":
            return item
    return ""

def start():
    """
    Convenience function to open the main tweenMachine instance
    """
    TMWindowUI()
    
def inactive():
    """
    Display a warning when a feature is not active
    """
    mc.warning("This tweenMachine feature is not currently active.")

def tween(bias, nodes=None):
    """
    Create the in-between key(s) on the specified nodes
    """
    if isinstance(nodes, list) and not nodes:
        nodes = None
    # Find the current frame, where the new key will be added
    currenttime = mc.timeControl("timeControl1", q=True, ra=True)[0]
    # Figure out which nodes to pull from
    if nodes is not None:
        pullfrom = nodes
    else:
        pullfrom = mc.ls(sl=True)
        if not pullfrom:
            return
    # If attributes are selected, use them to build curve node list
    attributes = mc.channelBox("mainChannelBox", q=True, sma=True)
    if attributes:
        curves = []
        for attr in attributes:
            for node in pullfrom:
                fullnode = "%s.%s" % (node, attr)
                if not mc.objExists(fullnode):
                    continue
                tmp = mc.keyframe(fullnode, q=True, name=True)
                if not tmp:
                    continue
                curves += tmp
    # Otherwise get curves for all nodes
    else:
        curves = mc.keyframe(pullfrom, q=True, name=True)
    mc.waitCursor(state=True)
    # Wrap the main operation in a try/except to prevent the waitcursor from
    # sticking if something should fail
    try:
    	# If we have no curves, force a list
    	if curves is None:
    		curves = []
        # Process all curves
        for curve in curves:
            # Find time for next and previous keys...
            time_prev = mc.findKeyframe(curve, which="previous")
            time_next = mc.findKeyframe(curve, which="next")
            # Find previous and next tangent types
            try:
                in_tan_prev = mc.keyTangent(curve, time=(time_prev,), q=True,
                                            itt=True)[0]
                out_tan_prev = mc.keyTangent(curve, time=(time_prev,), q=True,
                                             ott=True)[0]
                in_tan_next = mc.keyTangent(curve, time=(time_next,), q=True,
                                            itt=True)[0]
                out_tan_next = mc.keyTangent(curve, time=(time_next,), q=True,
                                             ott=True)[0]
            # Workaround for keyTangent error in Maya 2016 Extension 2
            except RuntimeError:
                in_tan_prev = mel.eval("keyTangent -time %s -q -itt %s" % (time_prev, curve))[0]
                out_tan_prev = mel.eval("keyTangent -time %s -q -ott %s" % (time_prev, curve))[0]
                in_tan_next = mel.eval("keyTangent -time %s -q -itt %s" % (time_next, curve))[0]
                out_tan_next = mel.eval("keyTangent -time %s -q -ott %s" % (time_next, curve))[0]
            # Set new in and out tangent types
            in_tan_new = out_tan_prev
            out_tan_new = in_tan_next
            # However, if any of the types (previous or next) is "fixed",
            # use the global (default) tangent instead
            if "fixed" in [in_tan_prev, out_tan_prev, in_tan_next, out_tan_next]:
                in_tan_new = mc.keyTangent(q=True, g=True, itt=True)[0]
                out_tan_new = mc.keyTangent(q=True, g=True, ott=True)[0]
            elif out_tan_next == "step":
                out_tan_new = out_tan_next
            # Find previous and next key values
            value_prev = mc.keyframe(curve, time=(time_prev,), q=True,
                                     valueChange=True)[0]
            value_next = mc.keyframe(curve, time=(time_next,), q=True,
                                     valueChange=True)[0]
            value_new = value_prev + ((value_next - value_prev) * bias)
            # Set new keyframe and tangents
            mc.setKeyframe(curve, t=(currenttime,), v=value_new,
                           ott=out_tan_new)
            if in_tan_new != "step":
                mc.keyTangent(curve, t=(currenttime,), itt=in_tan_new)
            # If we're using the special tick, set that appropriately
            if SETTINGS["use_special_tick"]:
                mc.keyframe(curve, tds=True, t=(currenttime,))
    except:
        raise
    finally:
        mc.waitCursor(state=False)
        mc.currentTime(currenttime)
        mel.eval("global string $gMainWindow;")
        windowname = mel.eval("$temp = $gMainWindow")
        mc.setFocus(windowname)

#-------------------------------------------------------------------------
#----------------------------------------------------------- Classes -----

class TMData(object):
    """
    Core code for data organization (groups and sets)
    """
    
    def __init__(self):
        # Try to read preferences from option variables; otherwise use defaults
        self.element = None
        self.name = "selected"
        self.groups = []
        # Try to read the existing XML data
        oldnodes = mc.ls("tmXML*")
        newnodes = mc.ls("tweenMachineData")
#        if True:
#            return
        if oldnodes:
            # If we have more than one, use the first one, but warn the user
            self.node = oldnodes[0]
            if len(oldnodes) > 1:
                mc.warning("Multiple tweenMachine data nodes found.  Using"
                           + self.node)
            # If the data is in the old format (tmXML has children), convert it
            if mc.listRelatives(self.node, children=True):
                print "# tweenMachine: Old data found.  Converting."
                self.root = etree.XML("<tweenMachineData />")
                self.tree = etree.ElementTree(self.root)
                # Create base elements
                buttons_element = etree.SubElement(self.root, "buttons")
                buttons_element.set("height", str(SETTINGS["button_height"]))
                groups_element = etree.SubElement(self.root, "groups")
                # Convert option data
                slider_vis_node = mc.ls("tmSliderVis*")[0]
                slider_vis_value = int(mc.getAttr(slider_vis_node + ".data"))
                button_vis_node = mc.ls("tmSliderVis*")[0]
                button_vis_value = int(mc.getAttr(button_vis_node + ".data"))
                if slider_vis_value and button_vis_value:
                    show_mode = "both"
                else:
                    if slider_vis_value:
                        show_mode = "slider"
                    else:
                        show_mode = "button"
                SETTINGS["show_mode"] = show_mode
                # Convert button data
                buttons_node = mc.ls("tmButtons*")[0]
                for node in mc.listRelatives(buttons_node, children=True):
                    suffix = node[-1]
                    bcolor = str(mc.getAttr("tmButtonRGB%s.data" % suffix))
                    bvalue = str(mc.getAttr("tmButtonValue%s.data" % suffix))
                    button_element = etree.SubElement(buttons_element, "button")
                    button_element.set("rgb", bcolor)
                    button_element.set("value", bvalue)
                # Convert groups and sets
                group_node = mc.ls("tmGroups*")[0]
                for node in mc.ls(group_node + "|tmGroup*"):
                    # Get the group name and order
                    gname = str(mc.getAttr(node + ".id"))
                    gorder = str(mc.getAttr(node + ".order"))
                    group_element = etree.SubElement(groups_element, "group")
                    group_element.set("name", gname)
                    group_element.set("index", gorder)
                    # Get the sets in this group
                    for setnode in mc.listRelatives(node, children=True):
                        setname = str(mc.getAttr(setnode + ".id"))
                        setorder = str(mc.getAttr(setnode + ".order"))
                        # Create a set node and add the set objects to it
                        set_element = etree.SubElement(group_element, "set")
                        set_element.set("name", setname)
                        set_element.set("index", setorder)
                        setobjs = []
                        for objnode in mc.listRelatives(setnode, children=True):
                            setobjs.append(str(mc.getAttr(objnode + ".data")))
                        set_element.text = " ".join(setobjs)
            # Otherwise get the data from the node
            else:
                self.root = etree.XML(mc.getAttr(node + ".data"))
                self.tree = etree.ElementTree(self.root)
        # Otherwise start from scratch
        else:
            self.root = etree.XML("""<tweenMachineData>
    <buttons height="%s">
         <button rgb="0.6 0.6 0.6" value="-75" />
         <button rgb="0.6 0.6 0.6" value="-60" />
         <button rgb="0.6 0.6 0.6" value="-33" />
         <button rgb="0.6 0.6 0.6" value="0" />
         <button rgb="0.6 0.6 0.6" value="33" />
         <button rgb="0.6 0.6 0.6" value="60" />
         <button rgb="0.6 0.6 0.6" value="75" />
    </buttons>
    <groups />
</tweenMachineData>
""" % SETTINGS["button_height"])
            self.tree = etree.ElementTree(self.root)
        # Next: replace existing data with new XML data
        if newnodes:
            newnode = newnodes[0]
        else:
            # Capture former selection
            selection = mc.ls(sl=True)
            # Make the new data node
            newnode = mc.createNode("transform", name="tweenMachineData")
            mc.addAttr(newnode, longName="data", dataType="string")
            # Reset former selection
            if selection:
                mc.select(selection)
            else:
                mc.select(clear=True)
        mc.setAttr(newnode + ".data", etree.tostring(self.root), type="string")
        # Erase old data nodes (FUTURE: ask user to confirm)
        if False:
            for node in oldnodes:
                mc.delete(node)
            
            
'''
            
        global string $tmGroups[], $tmSets[], $tmButtonRGB[];
        global int $tmNumButtons, $tmShowButtons, $tmShowSliders;
        global float $tmButtonVal[];

        $tmSets[0] = "tmMainSelectedSet";

        // read groups

#        for ($grp in $groups) {

#            string $grpId = `getAttr ($grp + ".id")`;
#            int $grpOrd = `getAttr ($grp + ".order")`;
#            $tmGroups[$grpOrd] = $grpId;
#            tmBuildGroup ($grpId,$grpOrd);

            // get sets in the group and put them in order

            string $sets[];
            $sets = getByType ($grp, "tmSet");

            string $tmpSet[];
            clear $tmpSet;

            for ($set in $sets) {

                int $setOrd = `getAttr ($set + ".order")`;
                $tmpSet[$setOrd] = $set;

            }
        
            // build sets into groups
            for ($i=0; $i<size($tmpSet); $i++) {
            
                $setName = `getAttr ($tmpSet[$i] + ".id")`;
                string $longSetName = "tm" + $grpId + $setName + "Set";

                // read objects in the set
                string $objects[];
                $objects = getByType ($tmpSet[$i], "tmObject");

                string $obj[];
                clear $obj;
                int $makeSet = 1;
                for ($o in $objects) {
                    string $objTmp = `getAttr ($o + ".data")`;
                    if (`objExists $objTmp`) 
                        $obj[size($obj)] = $objTmp;
                    else if ($objTmp == "tmCustomCharacterSet")
                        $makeSet = 0;
                    else print ("# tweenMachine: Omitting \"" + $objTmp + "\" from set \"" + $setName + "\". Object does not exist in scene.\n");
                
                }

                // if set does not exist, build it
            
                if (!`objExists $longSetName` && $makeSet) sets -n $longSetName $obj;

                // add set to group

                tmBuildSet ($grpId, $setName);

            }

        }

        if (size($tmGroups)) menuItem -e -en 1 tmAddSetMI;
        
    def load_data(self):
        """
        Try to load data from XML (if it exists)
        """
        try:
            pass
        except:
            self.element = etree.
        
'''


class TMGroup(object):
    """
    Container object for a collection of TMSet classes
    """
    
    def __init__(self, element=None, element_parent=None):
        self._element_parent = element_parent
        self.sets = []
        self._element = element
        if self._element is not None:
            # Build list of sets from XML data
            pass
        else:
            self._element = etree.SubElement(self._element_parent, "group", name="")
        
    def add_set(self, name):
        """
        Add the named set
        """
        
    # Properties

    def _get_nodes(self):
        """
        Return all nodes in all contained sets
        """
        allnodes = []
        for set_ in self.sets:
            allnodes += set_.nodes
        return list(set(allnodes))
        
    nodes = property(_get_nodes)

        

class TMSet(object):
    """
    Data class that operates on a predefined list of nodes (or no nodes, in the
    case of the default selected set)
    """
    
    def __init__(self, nodes=None, element=None, groupelement=None):
        self._groupelement = groupelement
        # If we have an element, assume that it contains the list of nodes
        if element is not None:
            self._nodes = element.get("nodes").split()
            self.name = element.get("name")
        else:
            # If we have no element, and no nodes, this is the selected set.
            # Otherwise assume that the list of nodes was passed in, and make a
            # new XML element
            self._nodes = nodes
            if nodes is not None:
                self._element = etree.SubElement(groupelement, "set", name="",
                                                 nodes=" ".join(self._nodes))
        
    # Properties
    
    def _get_nodes(self):
        """
        Returns the list of nodes for this set
        """
        return self._nodes
        
    def _set_nodes(self, nodes=None):
        """
        Sets the list of nodes
        """
        # If no nodes were passed (or None was passed), default to the current selection
        if nodes is None:
            self._nodes = mc.ls(sl=True)
        else:
            self._nodes = nodes
        
    nodes = property(_get_nodes, _set_nodes)
        
        
    
class TMWindowUI(object):
    """
    Main tool window
    """
    
    def __init__(self):
        # Import maya.cmds at root namespace for deferred commands
        mc.evalDeferred("import maya.cmds as mc")
        # Check for updates
        if SETTINGS["update_check"]:
            self.update_check()
        # First get an instance of the main data class
        self.data = TMData()
        # Set core variables
        self.docked = SETTINGS["docked"]
        self.show_mode = SETTINGS["show_mode"]
        self.use_overshoot = SETTINGS["use_overshoot"]
        self.use_special_tick = SETTINGS["use_special_tick"]
        self.window = None
        self.set_ui_mode()
        self._build_all_groups()

        # Kick off scriptJobs
        ##scriptJob -p tweenMachineWin -e "SceneOpened" "deleteUI tweenMachineWin; tweenMachine;";
        #scriptJob -p tweenMachineWin -e "NewSceneOpened" "deleteUI tweenMachineWin;";
        #scriptJob -uid tweenMachineWin "tmRestoreTimeControl";

    def _make_window(self):
        """
        Make the core window that will contain all the UI elements
        """
        # Make the main window
        windowname = "tweenMachineWindow"
        if SETTINGS["ui_mode"] != "window":
            windowname = None
        if SETTINGS["ui_mode"] == "window" and mc.window("tweenMachineWindow",
                                                         q=True, ex=True):
            mc.deleteUI("tweenMachineWindow")
        self.window = mc.window(windowname, width=300, height=50,
                 minimizeButton=True, maximizeButton=False, menuBar=True,
                 menuBarVisible=SETTINGS["show_menu_bar"],
                 resizeToFitChildren=True, sizeable=True,
                 title="tweenMachine v%s" % __version__,
                 docTag="tweenMachine", iconName="tweenMachine")
        # Build the base UI elements
        self.main_form = mc.formLayout(parent=self.window)
        self.selected_row = TMSetUI(self.main_form, "Selected")
        mc.formLayout(self.main_form, e=True,
                      attachForm=[(self.selected_row.form, "top", 0),
                                  (self.selected_row.form, "left", 0),
                                  (self.selected_row.form, "right", 0)])
        
    def _make_menus(self):
        """
        Make the menus
        """
        # Force the show_menu_bar to a certain setting in certain modes
        if SETTINGS["ui_mode"] in ["toolbar", "dock"]:
            SETTINGS["show_menu_bar"] = False
        # Make the base menus
        if SETTINGS["show_menu_bar"]:
            menus = mc.window(self.window, q=True, menuArray=True)
            if menus is not None:
                for menu in menus:
#                    if mc.menu(menu, q=True, label=True) == "File":
#                        self._file_menu = menu
#                    if mc.menu(menu, q=True, label=True) == "Tools":
#                        self._tool_menu = menu
                    if mc.menu(menu, q=True, label=True) == "Options":
                        self._opt_menu = menu
            else:
#                self._file_menu = mc.menu(label="File",
#                                          postMenuCommand=self._make_file_menu)
#                self._tool_menu = mc.menu(label="Tools",
#                                          postMenuCommand=self._make_tool_menu)
                self._opt_menu = mc.menu(label="Options",
                                          postMenuCommand=self._make_opt_menu)
            mc.evalDeferred("mc.window('%s', e=True, menuBarVisible=True)"
                            % self.window)
        else:
            if not hasattr(self, "popup_menu"):
                self.popup_menu = mc.popupMenu(parent=self.main_form)
#            self._file_menu = mc.menuItem(p=self.popup_menu, label="File",
#                                  postMenuCommand=self._make_file_menu,
#                                  subMenu=True)
#            self._tool_menu = mc.menuItem(p=self.popup_menu, label="Tools",
#                                  postMenuCommand=self._make_tool_menu,
#                                  subMenu=True)
            self._opt_menu = mc.menuItem(p=self.popup_menu, label="Options",
                                 postMenuCommand=self._make_opt_menu,
                                 subMenu=True)
        
    def _make_file_menu(self, *args):
        """
        Make the file menu
        """
        clear_menu(self._file_menu)
        mc.menuItem(p=self._file_menu, label="Coming soon...", enable=False)
        if True:
            return
        mc.menuItem(p=self._file_menu, label="New...", command=self.new)
        mc.menuItem(p=self._file_menu, divider=True)
        mc.menuItem(p=self._file_menu, label="Open...", command=self.load)
        mc.menuItem(p=self._file_menu, label="Save...", command=self.save, 
                    enable=len(self.data.groups)>0)
        
    def _make_tool_menu(self, *args):
        """
        Make the tool menu
        """
        clear_menu(self._tool_menu)
        mc.menuItem(p=self._tool_menu, label="Coming soon...", enable=False)
        if True:
            return
        mc.menuItem(p=self._tool_menu, label="Add Group...",
                    command=self._add_group_prompt)
        mc.menuItem(p=self._tool_menu, label="Add Set...",
                    command=self._add_set_pre,
                    enable=len(self.data.groups)>0)
        mc.menuItem(p=self._tool_menu, divider=True)
        mc.menuItem(p=self._tool_menu, label="Manage Sets and Groups...",
                    command=self._open_data_manager)
        mc.menuItem(p=self._tool_menu, label="Manage Buttons...",
                    command=self._open_button_manager)
        mc.menuItem(p=self._tool_menu, divider=True)
        charset_menu = mc.menuItem(p=self._tool_menu, label="Character Sets...",
                                   subMenu=True)
        mc.menuItem(p=charset_menu, label="Add Character Group",
                    command=self._add_character_group)
        mc.menuItem(p=charset_menu, label="Import Character Sets",
                    command=self._import_character_sets)
        
    def _make_opt_menu(self, *args):
        """
        Make the options menu
        """
        clear_menu(self._opt_menu)
        show_menu = mc.menuItem(p=self._opt_menu, label="Show...", subMenu=True)
        # Menu bar  and label visibility toggles
        if SETTINGS["ui_mode"] in ["window", "dock"]:
            mc.menuItem(p=show_menu, label="Menu Bar",
                        cb=SETTINGS["show_menu_bar"],
                        command=self._toggle_menu_visibility)
        mc.menuItem(p=show_menu, label="Label", cb=SETTINGS["show_label"],
                    command=self._toggle_label_visibility)
        mc.menuItem(p=show_menu, divider=True)
        # Slider and button visibility options
        show_collection = mc.radioMenuItemCollection(parent=show_menu)
        mc.menuItem(p=show_menu, label="Slider and Buttons",
                    rb=self.show_mode == "both",
                    command=lambda x, m="both":self._set_show_mode(m))
        mc.menuItem(p=show_menu, label="Slider Only",
                    rb=self.show_mode == "slider",
                    command=lambda x, m="slider":self._set_show_mode(m))
        mc.menuItem(p=show_menu, label="Buttons Only",
                    rb=self.show_mode == "buttons",
                    command=lambda x, m="buttons":self._set_show_mode(m))
        # UI mode options
        if "2013" not in MAYA_VERSION:
            mc.menuItem(p=self._opt_menu, divider=True)
            mode_menu = mc.menuItem(p=self._opt_menu, label="Mode...",
                                    subMenu=True)
            mode_collection = mc.radioMenuItemCollection(parent=mode_menu)
            mc.menuItem(p=mode_menu, label="Window",
                        rb=SETTINGS["ui_mode"] == "window",
                        command=lambda x, m="window":self.set_ui_mode(m))
            mc.menuItem(p=mode_menu, label="Toolbar",
                        rb=SETTINGS["ui_mode"] == "toolbar",
                        command=lambda x, m="toolbar":self.set_ui_mode(m))
#       mc.menuItem(p=mode_menu, label="HUD",
#                    rb=SETTINGS["ui_mode"] == "hud",
#                    command=lambda x, m="hud":self.set_ui_mode(m))
        mc.menuItem(p=self._opt_menu, divider=True)
        mc.menuItem(p=self._opt_menu, label="Overshoot", cb=self.use_overshoot,
                    command=self._toggle_overshoot)
        mc.menuItem(p=self._opt_menu, label="Special Tick Color",
                    cb=self.use_special_tick,
                    command=self._toggle_special_tick)
        
    def _add_group_prompt(self, *args):
        """
        Open a dialog that allows the user to add a new group
        """
        result = mc.promptDialog(title="Add Group", message="Enter group name",
                                 button=["OK", "Cancel"], defaultButton="OK",
                                 cancelButton="Cancel", dismissString="Cancel")
        if result == "OK":
            self._add_group(mc.promptDialog(q=True, text=True))
        
    def _add_group(self, name):
        """
        Create a group with the specified name
        """
        inactive()
        
    def _add_set_pre(self, *args):
        """
        Open a dialog that allows the user to add a new set
        """
        inactive()
        
    def _add_set_post(self):
        """
        Callback from the dialog made by _add_set_pre
        """
        inactive()
        
    def _open_data_manager(self, *args):
        """
        Open the group/set data manager dialog
        """
        inactive()
        
    def _open_button_manager(self, *args):
        """
        Open the group/set data manager dialog
        """
        inactive()

    def _set_show_mode(self, mode):
        """
        Set the show mode
        """
        self.show_mode = mode
        SETTINGS["show_mode"] = mode
        self.selected_row.set_show_mode(mode)
        
    def _toggle_overshoot(self, *args):
        """
        Toggle the overshoot setting
        """
        self.use_overshoot = not self.use_overshoot
        SETTINGS["use_overshoot"] = self.use_overshoot
        self.selected_row.toggle_overshoot()
        
    def _toggle_special_tick(self, *args):
        """
        Toggle the use of the special tick color
        """
        self.use_special_tick = not self.use_special_tick
        SETTINGS["use_special_tick"] = self.use_special_tick
        
    def _toggle_label_visibility(self, *args):
        """
        Toggle visibility of the slider label(s)
        """
        show = not SETTINGS["show_label"]
        SETTINGS["show_label"] = show
        self.selected_row.set_label_visibility(show)
        
    def _toggle_menu_visibility(self, *args):
        """
        Toggle visibility of the window menu
        """
        show = not SETTINGS["show_menu_bar"]
        SETTINGS["show_menu_bar"] = show
        mc.window(self.window, e=True, menuBarVisible=show)
        self._make_menus()
        mc.refresh(force=True)
        if show:
            if self.popup_menu is not None:
                mc.popupMenu(self.popup_menu, e=True, dai=True)
        
    def _build_all_groups(self):
        """
        Build the group interface(s) based on the data in the scene
        """

    def _cleanup(self):
        """
        Clean up stuff when the tool is closed
        """
        # Restore the time control to the animation list
        mc.timeControl("timeControl1", e=True, mlc="animationList")
        
#    def window_name(self):
#        return find_ui("window")
        
    # ----- Character Sets ---------------------------------------------------#
    
    def _add_character_group(self, *args):
        """
        Add a group that will work with character set data
        """
        inactive()
        
    def _import_character_sets(self, *args):
        """
        Import character set data from scene
        """
        inactive()
        
    # ----- UI Management ----------------------------------------------------#
    
    def set_ui_mode(self, mode=None):
        """
        Set the UI's current state (window, dock, toolbar, HUD)
        """
        oldmode = SETTINGS["ui_mode"]
        # If user is in Maya 2013, force window mode until a fix can be found
        # for toolbar mode
        if "2013" in MAYA_VERSION:
            mode = None
            oldmode = "window"
        # Update the UI appropriately if we're changing modes
        if mode != oldmode:
            if mode is None:
                mode = oldmode
            SETTINGS["ui_mode"] = mode
            # Delete the popup menu variable so that a new one can be made
            if hasattr(self, "popup_menu"):
                del(self.popup_menu)
            # Show the proper UI
            window = self.window
            if self.window is None:
                window = find_ui("window")
            toolbar = find_ui("toolBar")
            dock = find_ui("dockControl")
            self._make_window()
            deleteold = None
            hasmenu = True
            if mode == "window":
                if oldmode == "toolbar" and toolbar:
                    deleteold = toolbar
                    SETTINGS["show_menu_bar"] = True
                if oldmode == "dock" and dock:
                    deleteold = dock
                mc.showWindow(self.window)
            elif mode == "toolbar":
                if toolbar:
                    deleteold = toolbar
                if oldmode == "window" and window:
                    deleteold = window
                if oldmode == "dock" and dock:
                    deleteold = dock
                if not mc.toolBar("tweenMachineToolbar", q=True, exists=True):
                    mc.toolBar("tweenMachineToolbar", height=20,
                               docTag="tweenMachine", content=self.window,
                               area="left", label="tweenMachine")
                    mc.windowPref(restoreMainWindowState="startupMainWindowState")
                else:
                    mc.windowPref(saveMainWindowState="startupMainWindowState")
            elif mode == "dock":
                pass
            elif mode == "hud":
                hasmenu = False
            if hasmenu:
                self._make_menus()
            # If we're deleting an old item, set a deferred command to do so
            if deleteold is not None:
                defer_delete(deleteold)
            
    # ----- File Management --------------------------------------------------#
    
    def new(self, *args):
        """
        Flush all data and start over
        """
        inactive()
        
    def load(self, *args):
        """
        Load groups and sets from a tweenMachine data file
        """
        inactive()
        
    def save(self, *args):
        """
        Save groups and sets to a tweenMachine data file
        """
        inactive()
        
    def update_check(self):
        """
        Check for updates (or cancel update when cancel flag is set)
        """
        url = "http://www.justinsbarrett.com/tmupdate.php?tmquery=version"
        link = urllib2.urlopen(url)
        if link.getcode() == 200:
            data = link.read()
            if data.strip() != __version__:
                mc.warning("A new version is available")
            else:
                print "Versions match"
        link.close()
            

        
class TMSetUI(object):
    """
    Base UI class for a single set, which includes a slider, a set of buttons,
    a numeric field, a check box, and a label
    """
    
    def __init__(self, parent, name, **kwds):
        self.data = TMSet()
        self.name = name
        self.form = mc.formLayout(parent=parent)
        self.showcheck = lambda:self.data.nodes is not None
        self.checkbox = mc.checkBox(parent=self.form, label="",
                                    manage=self.showcheck())
        self.label = mc.text(parent=self.form, label=self.name, width=90,
                             manage=SETTINGS["show_label"])
        mode = SETTINGS["show_mode"]
        self.slider = mc.floatSlider(parent=self.form, min=-100,
                                        max=100, value=0, 
                                        manage=mode in ["both", "slider"],
                                        changeCommand=self.tween_slider,
                                        dragCommand=self.update_field)
        self.field = mc.floatField(parent=self.form, min=-100, max=100, value=0,
                                   width=50, pre=1, step=1,
                                   changeCommand=self.tween_field,
                                   enterCommand=self.tween_field,
                                   dragCommand=self.tween_field)
        # Attach the checkbox
        mc.formLayout(self.form, e=True, 
                      attachForm=[(self.checkbox, "left", 5),
                                  (self.checkbox, "top", 0)])
        # Attach the label
        mc.formLayout(self.form, e=True,
                      attachControl=[(self.label, "left", 5, self.checkbox)])
        mc.formLayout(self.form, e=True,
                      attachForm=[(self.label, "top", 3)])
        labelOffset = 90 * int(SETTINGS["show_label"])
        # Attach the field
        mc.formLayout(self.form, e=True,
                      attachForm=[(self.field, "left", labelOffset),
                                  (self.field, "top", 0)])
        # Attach the slider
        mc.formLayout(self.form, e=True,
                      attachForm=[(self.slider, "left", labelOffset + 55),
                                  (self.slider, "right", 5),
                                  (self.slider, "top", 3)])
        # Build and attach the button row
        self.buttonrow = TMButtonRowUI(self, self.form, **kwds)
        mc.formLayout(self.buttonrow.form, e=True,
                      manage=mode in ["both", "buttons"])
        mc.formLayout(self.form, e=True,
                      attachForm=[(self.buttonrow.form, "left", labelOffset + 55),
                                  (self.buttonrow.form, "top", 5 + (20 * int(mode!="buttons"))),
                                  (self.buttonrow.form, "right", 5)])
        # If overshoot mode is active, then force-toggle the overshoot
        if SETTINGS["use_overshoot"]:
            self.toggle_overshoot()
        
    def tween(self, value):
        """
        Callback when the slider is triggered
        """
        tween((value + 100) / 200.0, self.data.nodes)
        
    def tween_field(self, value):
        """
        Callback when the field value is changed
        """
        mc.floatSlider(self.slider, e=True, value=value)
        self.tween(value)
        
    def tween_slider(self, value):
        """
        Callback when the slider value is changed
        """
        self.update_field(value)
        self.tween(value)
        
    def tween_button(self, value):
        """
        Callback when a button is clicked
        """
        self.update_field(value)
        self.tween_field(value)
        
    def update_field(self, value):
        """
        Update the field without tweening
        """
        mc.floatField(self.field, e=True, value=value)
        
    def set_show_mode(self, mode):
        """
        Set the show mode for this row
        """
        mc.floatSlider(self.slider, e=True, manage=mode in ["both", "slider"])
        mc.formLayout(self.buttonrow.form, e=True,
                      manage=mode in ["both", "buttons"])
        mc.formLayout(self.form, e=True,
                      attachForm=[(self.buttonrow.form, "top",
                                   5 + (20 * int(mode!="buttons")))])
    
    def set_label_visibility(self, mode):
        """
        Set the visibility of the set's label
        """
        mc.text(self.label, e=True, manage=mode)
        # Adjust spacing of other UI elements
        labelOffset = 90 * int(mode)
        mc.formLayout(self.form, e=True,
                      attachForm=[(self.field, "left", labelOffset)])
        mc.formLayout(self.form, e=True,
                      attachForm=[(self.slider, "left", labelOffset + 55)])
        mc.formLayout(self.form, e=True,
                      attachForm=[(self.buttonrow.form, "left", labelOffset + 55)])
        
    def toggle_overshoot(self):
        """
        Toggle the overshoot setting
        """
        if mc.floatSlider(self.slider, q=True, min=True) == -100:
            mc.floatSlider(self.slider, e=True, min=-150, max=150)
            mc.floatField(self.field, e=True, min=-150, max=150)
        else:
            value = mc.floatSlider(self.slider, q=True, value=True)
            if value > 100:
                mc.floatSlider(self.slider, e=True, value=100)
                mc.floatField(self.field, e=True, value=100)
            if value < -100:
                mc.floatSlider(self.slider, e=True, value=-100)
                mc.floatField(self.field, e=True, value=-100)
            mc.floatSlider(self.slider, e=True, min=-100, max=100)
            mc.floatField(self.field, e=True, min=-100, max=100)



class TMButtonRowUI(object):
    """
    UI for the row of buttons within a single TM set
    """
    
    def __init__(self, setUI, parentform, **kwds):
        self.set = setUI
        self.edit = kwds.get("edit", False)
        if "button_data" in kwds:
            data = kwds["button_data"]
        else:
            # Use the default data
            data = SETTINGS["default_button_data"]
        self.data = TMButtonRowData(data)
        self.form = mc.formLayout(parent=parentform, height=10,
                                  nd=(10 * len(self.data)))
        self.buttons = ()
        self.refresh()
            
    def refresh(self):
        """
        Refresh the items in the row
        """
        [mc.deleteUI(button) for button in self.buttons]
        buttons = []
        index = 0
        for index, element in enumerate(self.data):
            buttons.append(mc.iconTextButton(parent=self.form,
                           height=SETTINGS["button_height"],
                           backgroundColor=element.color,
                           #label=str((index*buttonwidth)/100.0),
                           style="textOnly",
                           command=lambda v=element.value:self.tween(v)))
            left = (index * 10) + 1
            right = ((index + 1) * 10) - 1
            mc.formLayout(self.form, e=True,
                          attachPosition=[(buttons[-1], "left", 0, left),
                                          (buttons[-1], "right", 0, right),
                                          (buttons[-1], "top", 0, 0)])
        self.buttons = tuple(buttons)
    
    def tween(self, value):
        """
        Call the tween method of the set
        """
        if not self.edit:
            self.set.tween_button(value)



class TMButtonRowData(object):
    """
    Data for a row of buttons
    """
    
    def __init__(self, data):
        self.buttons = tuple([TMButtonData(element) for element in data])

    def __len__(self):
        return len(self.buttons)

    def __iter__(self):
        """
        Part of the iteration protocol
        """
        self.iter_index = -1
        return self
        
    def next(self):
        """
        Part of the iteration protocol
        """
        self.iter_index += 1
        try:
            return self.buttons[self.iter_index]
        except:
            raise StopIteration
        
        


class TMButtonData(object):
    """
    Data for a single button in a row
    """
    
    def __init__(self, data):
        self.value, self.color = data
        
    def change_value(self, value):
        """
        Change the value of this button
        """
        self.value = value
    
    def change_color(self, color):
        """
        Change the color of this button
        """
        self.color = color
        
    def __repr__(self):
        """
        Return a tuple that represents the data
        """
        return (self.value, self.color)




class TMSettings(dict):
    """
    Convenience class to get/set global settings via an option variable
    """
    
    def __init__(self, *args, **kwds):
        dict.__init__(self, *args, **kwds)
        # Search for existing option variable.  If it doesn't exist, make it
        # using the default options
        self.name = "tweenMachineSettings"
        if mc.optionVar(exists=self.name):
            data = eval(mc.optionVar(q=self.name))
            for key in data:
                self[key] = data[key]
        # Add new items if they don't exist
        if "use_special_tick" not in self:
            self["special_tick"] = False
        if "slider_width" not in self:
            self["slider_width"] = 200
        if "docked" not in self:
            self["docked"] = False
        if "show_mode" not in self:
            self["show_mode"] = "both"
        if "use_overshoot" not in self:
            self["use_overshoot"] = False
        if "use_special_tick" not in self:
            self["use_special_tick"] = False
        if "default_button_data" not in self:
            self["default_button_data"] = ((-75, (0.6, 0.6, 0.6)),
                                           (-60, (0.6, 0.6, 0.6)),
                                           (-33, (0.6, 0.6, 0.6)),
                                           (0, (0.6, 0.6, 0.6)),
                                           (33, (0.6, 0.6, 0.6)),
                                           (60, (0.6, 0.6, 0.6)),
                                           (75, (0.6, 0.6, 0.6)))
        if "button_height" not in self:
            self["button_height"] = 8
        if "show_label" not in self:
            self["show_label"] = True
        if "show_menu_bar" not in self:
            self["show_menu_bar"] = True
        if "update_check" not in self:
            self["update_check"] = False
        if "ui_mode" not in self:
            self["ui_mode"] = "window"
        
    def __setitem__(self, key, value):
        """
        Set the named item, and save the data back to the optionVar
        """
        dict.__setitem__(self, key, value)
        mc.optionVar(stringValue=(self.name, str(self)))
        
        

#-------------------------------------------------------------------------
#----------------------------------------------------------- Default -----

SETTINGS = TMSettings()

if __name__ == "__main__":
    # Create a instance of the settings class, then kick off the main window
    TMWindowUI()





"""

global proc tweenMachine() {

	// Global Variables
	global string $tmGroups[], $tmSets[], $tmButtonRGB[], $tmSelConArray;
	global int $tmNumButtons, $tmSliderWidth, $tmShowButtons, $tmShowSliders, $tmButtonRowPad, $mayaVers, $tmSpecTick;
	global float $tmButtonVal[];

	clear $tmGroups;
	clear $tmSets;

	$tmSliderWidth = 200;
	$mayaVers = (int) startString(`about -v`,1);
	$tmSpecTick = 0;
	
	// Source needed libraries
	source xml_lib.mel;

	// OS check -- this will probably go away once the UI is built using forms
	if (`about -mac`) {
		$tmButtonRowPad = 10;
	} else {
		$tmButtonRowPad = 1;
	}

	if (`window -q -ex tweenMachineWin`) deleteUI tweenMachineWin ;

	// Make Window
	window -w 300 -h 5 -mnb 1 -mxb 0 -menuBar 1 -mbv 1 -rtf 1 -s 1 -t "tweenMachine - 2.03" -in "tweenMachine" tweenMachineWin;

	menu -l "File" tmFile;
		menuItem -l "New..." -en 1 -c "tmNew";
		menuItem -d true;
		menuItem -l "Open..." -en 1 -c "tmLoadFromFile";
		menuItem -l "Save..." -en 1 -c "fileBrowser \"tmSaveToFile\" \"Save\" \"\" 1";

	menu -l "Tools" tmTools;
		menuItem -l "Add Set..." -en 0 -c "tmAddSetUI" tmAddSetMI;
		menuItem -l "Add Group..." -c "tmAddGroupUI";
		menuItem -d true;
		menuItem -l "Manage Sets..." -en 1 -c "tmSGMBuildUI(0)";
		menuItem -l "Manage Groups..." -en 1 -c "tmSGMBuildUI(1)";
		//menuItem -d true;
		//menuItem -l "Manage Buttons..." -en 0;
		menuItem -d true;
		menuItem -l "Character Sets..." -sm 1;
			menuItem -l "Add Character Group" -c "tmAddCharacterGroup";
			menuItem -l "Import Character Sets" -c "tmImportCharSets";

	menu -l "Options" -to 1 tmOptions;
		menuItem -l "Sliders" -cb 1 -c "tmShowChange" tmSliderTog;
		menuItem -l "Buttons" -cb 1 -c "tmShowChange" tmButtonTog;
		menuItem -d true;
		menuItem -l "Overshoot" -cb 0 -c "tmToggleOvershoot" tmOvershootTog;
		if ($mayaVers > 6 || $mayaVers == 2) {
			menuItem -d true;
			menuItem -l "Special Tick Color" -cb 0 -c "$tmSpecTick = 1-$tmSpecTick";
		}


	columnLayout -adj 1 -cat "both" 0 tmMainGroupCL;

	tmBuildAllGroups;

	showWindow tweenMachineWin ;

	
	//scriptJob -p tweenMachineWin -e "SceneOpened" "deleteUI tweenMachineWin; tweenMachine;";
	scriptJob -p tweenMachineWin -e "NewSceneOpened" "deleteUI tweenMachineWin;";
	scriptJob -uid tweenMachineWin "tmRestoreTimeControl";
	
}

// --------------------------------------------------------------------------

global proc tmNew () {

	global string $tmGroups[];

	string $c = "Yes";
	if (size($tmGroups) > 0) $c = `confirmDialog -t "Start over?" -m "Erase all tweenMachine data?" -b "Yes" -b "No" -db "Yes" -cb "No" -ds "No"`;

	if ($c != "No") {
		delete tmXML1;
		tweenMachine;
	}
}

// --------------------------------------------------------------------------

global proc tmBuildAllGroups () {

	// start with the default data
	tmDefaultData;

	// build the "Selected" set no matter what
	tmBuildSet ("Main", "Selected");
	timeControl -e -mlc animationList timeControl1;

	separator -style "none" -h 5;

	// create master selectionConnection object
	if (!`selectionConnection -ex tmMasterSC`) selectionConnection -lst tmMasterSC;
	
	// If data exists in scene, pull the options and interface data from it
	// if not, build XML data using default values

	int $XMLexists = `objExists tmXML1`;
	if ($XMLexists) {
		tmReadXML;
	} else {
		tmDefaultXML;
	}

	setParent tweenMachineWin;
}

// --------------------------------------------------------------------------

global proc tmDefaultData () {

	global int $tmNumButtons, $tmShowButtons, $tmShowSliders;
	global float $tmButtonVal[];
	global string $tmGroups[], $tmSets[], $tmButtonRGB[];

	clear $tmGroups;
	clear $tmSets;

	$tmNumButtons = 7;
	$tmShowButtons = 1;
	$tmShowSliders = 1;

	clear $tmButtonVal;

	$tmButtonVal[0] = -75;
	$tmButtonVal[1] = -60;
	$tmButtonVal[2] = -33;
	$tmButtonVal[3] = 0;
	$tmButtonVal[4] = 33;
	$tmButtonVal[5] = 60;
	$tmButtonVal[6] = 75;

	int $i;
	for ($i=0; $i<$tmNumButtons; $i++) $tmButtonRGB[$i] = "0.6 0.6 0.6";

}

// --------------------------------------------------------------------------

global proc tmDefaultXML () {

	global int $tmNumButtons, $tmShowButtons, $tmShowSliders;
	global float $tmButtonVal[];
	global string $tmGroups[], $tmSets[], $tmButtonRGB[];

	// build XML-based data structure

	makeNode ("tmXML",1);
		makeNode ("tmOptions",0);
			makeNode ("tmSliderVis",0);
				addContent ("1");
			closeTag;
			makeNode ("tmButtonVis",0);
				addContent ("1");
			closeTag;
			makeNode ("tmButtons id=\"7\"",0);
				for ($i=0; $i<$tmNumButtons; $i++) {
					makeNode ("tmButton",0);
						makeNode ("tmButtonRGB",0);
							addContent ($tmButtonRGB[$i]);
						closeTag;
						makeNode ("tmButtonValue",0);
							addContent ($tmButtonVal[$i]);
						closeTag;
					closeTag;
				}
			closeTag;
		closeTag;
		makeNode ("tmGroups",0);
		closeTag;
	closeTag;

	select -cl;
}

// ************************************************************************
// ************************************************************************
//                         Ticks and Toggles
// ************************************************************************
// ************************************************************************

global proc tmShowChange () {

	global string $tmSets[];

	int $sliderState = `menuItem -q -cb tmSliderTog`;
	int $buttonState = `menuItem -q -cb tmButtonTog`;
	int $sliderEnable = `menuItem -q -en tmSliderTog`;
	int $buttonEnable = `menuItem -q -en tmButtonTog`;

	if (!$sliderState && $buttonState) {
		menuItem -e -en 0 tmButtonTog;
		for ($set in $tmSets) {
			string $fullName = $set + "Bias";
			floatSliderGrp -e -m 0 $fullName;
			rowLayout -e -rat 1 "top" 5 -rat 2 "top" 10 ($set + "OuterRow");
		}
	}

	if ($sliderState && !$buttonEnable) {
		menuItem -e -en 1 tmButtonTog;
		for ($set in $tmSets) {
			string $fullName = $set + "Bias";
			floatSliderGrp -e -m 1 $fullName;
			rowLayout -e -rat 1 "bottom" 10 -rat 2 "top" 0 ($set + "OuterRow");
		}
	}

	if ($sliderState && !$buttonState) {
		menuItem -e -en 0 tmSliderTog;
		for ($set in $tmSets) {
			string $fullName = $set + "Buttons";
			rowLayout -e -m 0 $fullName;
			rowLayout -e -rat 1 "top" 3 ($set + "OuterRow");
		}
	}

	if (!$sliderEnable && $buttonState) {
		menuItem -e -en 1 tmSliderTog;
		for ($set in $tmSets) {
			string $fullName = $set + "Buttons";
			rowLayout -e -m 1 $fullName;
			rowLayout -e -rat 1 "bottom" 10 ($set + "OuterRow");
		}
	}

}

// --------------------------------------------------------------------------

global proc tmToggleOvershoot () {

	global string $tmSets[];
	float $oldMin, $newMin, $newMax;

	float $oldMin = `floatSliderGrp -q -min tmMainSelectedSetBias`;

	if ($oldMin == -100) {
		$newMin = -150;
		$newMax = 150;
	} else {
		$newMin = -100;
		$newMax = 100;
	}
		
	for ($set in $tmSets) {
		string $fullName = $set + "Bias";
		float $oldVal = `floatSliderGrp -q -v $fullName`;
		float $newVal = `clamp $newMin $newMax $oldVal`;
		floatSliderGrp -e -min $newMin -max $newMax -v $newVal $fullName;
	}

}

// --------------------------------------------------------------------------

global proc tmTickToggle (string $objName, string $objParent) {

	global string $tmSets[], $tmGroups[];
	
	if ($objName == "tmMainSelectedSet") {

		// swap selectionConnection
		int $selChk = `checkBox -q -v tmMainSelectedSetTicks`;
		if (!$selChk) {
			timeControl -e -mlc tmMasterSC timeControl1;
		} else {
			timeControl -e -mlc animationList timeControl1;
		}

		// toggle "enable" setting for all
		int $en = 1-(`checkBox -q -v tmMainSelectedSetTicks`);

		for ($grp in $tmGroups) {
			string $grpTk = $grp + "Ticks";
			checkBox -e -en $en $grpTk;

			for ($set in tmSetsInGroup($grp,1)) {
				int $v = `checkBox -q -v $grpTk`;
				string $setTk = $set + "Ticks";
				if ($v && $en) checkBox -e -en 1 $setTk;
				if (!$v && $en) checkBox -e -en 0 $setTk;
				if ($v && !$en) checkBox -e -en 0 $setTk;
			}
		}
	} else {
		string $objTk = $objName + "Ticks";
		if (startsWith($objName,"tm")) {
			// object is a set
			string $objSC = $objName + "SC";
			string $parSC = "tm" + $objParent + "GroupSC";

			int $tkStat = `checkBox -q -v $objTk`;
			if ($tkStat) {
				selectionConnection -e -add $objSC $parSC;
			} else {
				selectionConnection -e -rm $objSC $parSC;
			}
		} else {
			// object is a group
			string $objSC = "tm" + $objName + "GroupSC";
			string $parSC = "tmMasterSC";

			int $tkStat = `checkBox -q -v $objTk`;
			if ($tkStat) {
				selectionConnection -e -add $objSC $parSC;
			} else {
				selectionConnection -e -rm $objSC $parSC;
			}

			for ($set in tmSetsInGroup($objName,1)) {
				string $setTk = $set + "Ticks";
				int $s = 1-(`checkBox -q -en $setTk`);
				checkBox -e -en $s $setTk;
			}

		}
	}
}


// ************************************************************************
// ************************************************************************
//                         Manage sets and groups
// ************************************************************************
// ************************************************************************

global proc tmSGMBuildUI (int $mode) {

	// $mode: 0 = manage sets, 1 = manage groups

	global string $sgmArray[], $tmGroups[];
	string $winTitle;

	if (!$mode) $winTitle = "Manage Sets";	else $winTitle = "Manage Groups";

	if (`window -ex tmSGMWin`) deleteUI tmSGMWin;

	window -t $winTitle -w 250 -h 250 -rtf 1 tmSGMWin;

	formLayout -w 250 -nd 100 tmSGMFormLayout;
	
		textScrollList -ams 0 -sc ("tmSGMSelect(" + $mode + ")") -dkc ("tmSGMDelete(" + $mode + ",1)") -da tmSGMList;
		if (!$mode) textScrollList -e -dcc "tmSGMMembers" tmSGMList;
	
		optionMenu -l "Manage:" -cc "tmSGMMode" tmSGMMode;
			menuItem -l "Sets";
			menuItem -l "Groups";
			optionMenu -e -sl ($mode+1) tmSGMMode;
		setParent tmSGMFormLayout;
	
		optionMenu -l "in group: " -cc "tmSGMRebuildList" -m (1-$mode) tmSGMGroups;
			for ($grp in $tmGroups) menuItem -l $grp;
		setParent tmSGMFormLayout;
	
		button -l "Move Up" -al "center" -w 80 -vis 0 -h 1 sgmUp;
		button -l "Move Down" -al "center" -w 80 -vis 0 -h 1 sgmDown;

		//button -l "Move Up" -al "center" -w 80 -en 0 -c ("tmReorderSGMList(-1," + $mode + ")") sgmUp;
		//button -l "Move Down" -al "center" -w 80 -en 0 -c ("tmReorderSGMList(1," + $mode + ")") sgmDown;

		button -l "Rename" -al "center" -w 80 -en 0 -c ("tmSGMRename(" + $mode + ")") sgmRen;
		button -l "Delete" -al "center" -w 80 -en 0 -c ("tmSGMDelete(" + $mode + ",1)") sgmDel;
		button -l "Properties..." -al "center" -w 80 -en 0 -m 0 -c "tmSGMProperties" sgmProp;
		//button -l "Properties..." -al "center" -w 80 -en 0 -m (1-$mode) -c "tmSGMProperties" sgmProp;
	
	formLayout -e

		-af tmSGMMode "top" 5
		-af tmSGMMode "left" 5

		-ac tmSGMGroups "left" 10 tmSGMMode
		-af tmSGMGroups "top" 5
	
		-af sgmUp "right" 5
		-ac sgmUp "top" 5 tmSGMMode
	
		-af sgmDown "right" 5 
		-ac sgmDown "top" 2 sgmUp

		-af sgmRen "right" 5 
		-ac sgmRen "top" 2 sgmDown

		-af sgmDel "right" 5 
		-ac sgmDel "top" 2 sgmRen
	
		-af sgmProp "right" 5 
		-ac sgmProp "top" 2 sgmDel 
	
		-ac tmSGMList "top" 5 tmSGMMode
		-ac tmSGMList "right" 5 sgmUp
		-af tmSGMList "bottom" 5
		-af tmSGMList "left" 5
	
		tmSGMFormLayout;
		
	showWindow tmSGMWin;
	
	tmSGMRebuildList;

}

// ------------------------------------------------------------------------

global proc tmSGMMode () {
	int $i = (`optionMenu -q -sl tmSGMMode`)-1;
	tmSGMBuildUI($i);
}

// ------------------------------------------------------------------------

global proc tmSGMSelect (int $mode) {
	button -e -en 1 sgmRen;
	button -e -en 1 sgmDel;
	//if (!$mode) button -e -en 1 sgmProp;
	int $item[];
	$item = `textScrollList -q -sii tmSGMList`;
	int $numItems = `textScrollList -q -ni tmSGMList`;
	//if ($item[0] > 1) button -e -en 1 sgmUp; else button -e -en 0 sgmUp;
	//if ($item[0] < $numItems) button -e -en 1 sgmDown; else button -e -en 0 sgmDown;
}

// ------------------------------------------------------------------------

global proc tmReorderSGMList (int $dir, int $mode) {
	global string $sgmArray[];

	int $item[], $index;
	$item = `textScrollList -q -sii tmSGMList`;
	$index = $item[0]-1;
	$sgmArray = stringArrayMoveItem($sgmArray,$index,$dir);

	textScrollList -e -ra tmSGMList;

	for ($i in $sgmArray) {
		textScrollList -e -append $i tmSGMList;
	}
	textScrollList -e -sii ($item[0]+$dir) tmSGMList;
	tmSGMSelect($mode);
	button -e -en 1 sgmApp;

}

// ------------------------------------------------------------------------

global proc tmSGMRebuildList() {

	global string $tmGroups[], $sgmArray[];

	int $mode = (`optionMenu -q -sl tmSGMMode`)-1;
	
	clear $sgmArray;
	if (!$mode) {
		string $group = `optionMenu -q -v tmSGMGroups`;
		$sgmArray = tmSetsInGroup($group,0);
	} else {
		$sgmArray = $tmGroups;	
	}

	textScrollList -e -ra tmSGMList;

	for ($item in $sgmArray) textScrollList -e -append $item tmSGMList;

	textScrollList -e -da tmSGMList;
	button -e -en 0 sgmRen;
	button -e -en 0 sgmDel;
	button -e -en 0 sgmDown;
	button -e -en 0 sgmUp;
	
}

// ------------------------------------------------------------------------

global proc tmSGMRename(int $mode) {

	global string $tmGroups[];
	string $modeName[], $item[], $group;
	$modeName[0] = " set";
	$modeName[1] = " group";

	$item = `textScrollList -q -si tmSGMList`;
	string $oldName = $item[0];

	if ($mode == 1 && $oldName == "CharacterSet") {
		confirmDialog -t "Rename not allowed" -m "You are not allowed to rename this item.";
		return;
	}
	
 	string $result = `promptDialog -t ("Rename" + $modeName[$mode]) -message "Enter new name:" -b "OK" -b "Cancel"
 		-defaultButton "OK" -cancelButton "Cancel"
 		-dismissString "Cancel"`;

 	if ($result == "OK") {
		string $newName = `promptDialog -q -text`;
		if (`isValidObjectName($newName)`) {
			if (!$mode) {
				$group = `optionMenu -q -v tmSGMGroups`;
				string $oldNameLong = "tm" + $group + $oldName + "Set";
				string $newNameLong = "tm" + $group + $newName + "Set";

				if (`objExists $newNameLong`) {
					confirmDialog -t "Set exists" -m "A set by that name already exists.  Please choose a new name.";
					return;
				}

				tmSGMRenameSet ($group, $oldNameLong, $newNameLong);

				text -e -l ($newName) ($newNameLong + "Label");

				// change id in XML data node
				string $grpObj = tmFindInXML("tmGroup","tmGroups1",".id",$group);
				string $setObj = tmFindInXML("tmSet",$grpObj,".id",$oldName);
				setAttr -type "string" ($setObj + ".id") $newName;

				tmSGMRebuildList;
			} else {
				for ($grp in $tmGroups) {
					if ($grp == $newName) {
						confirmDialog -t "Group exists" -m "A group by that name already exists.  Please choose a new name.";
						return;
					}
				}
				
				$group = $oldName;
				string $oldPrefix = "tm" + $group;
				string $newPrefix = "tm" + $newName;

				// rename and relabel group frameLayout
				renameUI ($oldPrefix + "Group") ($newPrefix + "Group");
				frameLayout -e -l $newName ($newPrefix + "Group");

				// rename columnLayout
				renameUI ($oldPrefix + "GroupCL") ($newPrefix + "GroupCL");

				// rename tick check box, and change command
				string $checkCommand = "tmTickToggle(\"" + $newName + "\", \"Main\")";
				renameUI ($oldName + "Ticks") ($newName + "Ticks");
				checkBox -e -cc $checkCommand ($newName + "Ticks");

				// rename group SC
				renameUI ($oldPrefix + "GroupSC") ($newPrefix + "GroupSC");
				
				// rename sets in group
				string $set;
				for ($set in tmSetsInGroup($group,0)) {
					string $oldName = $oldPrefix + $set + "Set";
					string $newName = $newPrefix + $set + "Set";
					tmSGMRenameSet ($group, $oldName, $newName);
				}

				// rename item in $tmGroups array
				int $g;
				for ($g=0; $g<=size($tmGroups); $g++) if ($tmGroups[$g] == $group) $tmGroups[$g] = $newName;
				
				// change ID in XML data node
				string $grpObj = tmFindInXML("tmGroup","tmGroups1",".id",$group);
				setAttr -type "string" ($grpObj + ".id") $newName;
				
				tmSGMRebuildList;

			}
	 	} else {
			confirmDialog -t "Invalid name" -m "The name entered is not valid.\nSet and group names must be valid Maya object names.";
		}
	}
}

// ------------------------------------------------------------------------

global proc tmSGMRenameSet(string $group, string $oldName, string $newName) {

	global string $tmSets[];
	global int $tmNumButtons;
	global float $tmButtonVal[];

	rename $oldName $newName;
	renameUI ($oldName + "SC") ($newName + "SC");
	renameUI ($oldName + "Spacer") ($newName + "Spacer");
	renameUI ($oldName + "OuterRow") ($newName + "OuterRow");

	renameUI ($oldName + "Bias") ($newName + "Bias");
	floatSliderGrp -e -cc ("tmSliderStart(\"" + $newName + "\");") ($newName + "Bias");
	
	string $checkCommand = "tmTickToggle(\"" + $newName + "\", \"" + $group + "\")";
	renameUI ($oldName + "Ticks") ($newName + "Ticks");
	checkBox -e -cc $checkCommand ($newName + "Ticks");
	
	renameUI ($oldName + "Buttons") ($newName + "Buttons");
	int $i;
 	for ($i=0; $i<$tmNumButtons; $i++) {
		string $buttonName = $newName + "Button" + $i;
		renameUI ($oldName + "Button" + $i) $buttonName;
		canvas -e -pc ("tmButtonStart(" + $tmButtonVal[$i] + ", \"" + $newName + "\")")  $buttonName ;
	}
		
	renameUI ($oldName + "Label") ($newName + "Label");

	// rename item in $tmSets array
	int $s;
	for ($s=0; $s<=size($tmSets); $s++) if ($tmSets[$s] == $oldName) $tmSets[$s]= $newName;

}

// ------------------------------------------------------------------------

global proc tmSGMDelete(int $mode, int $confirm) {

	global string $tmSets[], $tmGroups[], $sgmArray[];

	string $modeName[];
	$modeName[0] = " set?";
	$modeName[1] = " group?";

	string $i[], $item;
	int $iP[], $itemPos;
	$i = `textScrollList -q -si tmSGMList`;
	$iP = `textScrollList -q -sii tmSGMList`;
	$item = $i[0];
	$itemPos = $iP[0]-1;

	// display confirmation if $confirm is 1
	string $c;
	if ($confirm) {
		string $confirmMsg = "Are you sure you want to delete the \"" + $item + "\"" + $modeName[$mode];
		$c = `confirmDialog -t ("Delete" + $modeName[$mode]) -m $confirmMsg -b "Yes" -b "No" -db "Yes" -cb "No" -ds "No"`;
	} else $c = "Yes";

	if ($c == "Yes") {
		if (!$mode) {
			// query group from UI
			string $group = `optionMenu -q -v tmSGMGroups`;
			
			// build name of full set
			$setName = "tm" + $group + $item + "Set";

			// remove set from $tmSets array
			$tmSets = stringArrayRemove ({$setName},$tmSets);

			// remove setSC from groupSC, and delete setSC
			string $setSC = $setName + "SC";
			string $grpSC = "tm" + $group + "GroupSC";
			selectionConnection -e -rm $setSC $grpSC;

			// remove set from group in main window
			deleteUI ($setName + "Spacer");
			deleteUI ($setName + "OuterRow");

			// remove set from XML
			for ($set in tmSetsInGroup($group,2)) {
				int $setOrder = `getAttr ($set + ".order")`;
				if ($setOrder == $itemPos) delete $set;
				if ($setOrder > $itemPos) setAttr -type "string" ($set + ".order") ($setOrder -1);
			}

			// remove set
			delete $setName;

			tmSGMRebuildList;

		} else {
			// remove group from $tmGroups array
			$tmGroups = stringArrayRemove ({$item},$tmGroups);

			// remove groupSC from masterSC
			selectionConnection -e -rm ("tm" + $item + "GroupSC") tmMasterSC;

			// remove all sets in group from $tmSets array
			string $set;
			for ($set in tmSetsInGroup($item,1)) {
				$tmSets = stringArrayRemove ({$set},$tmSets);
			}

			if (!size($tmGroups)) menuItem -e -en 0 tmAddSetMI;
			
			// remove group from UI
			deleteUI ("tm" + $item + "Group");

			// remove group from XML
			for ($grp in getByType("tmGroups1","tmGroup")) {
				int $grpOrder = `getAttr ($grp + ".order")`;
				if ($grpOrder == $itemPos) delete $grp;
				if ($grpOrder > $itemPos) setAttr -type "string" ($grp + ".order") ($grpOrder-1);
			}

			tmSGMRebuildList;
		}
		
	}
}

// ************************************************************************
// ************************************************************************
//                         Build sets and groups
// ************************************************************************
// ************************************************************************

global proc tmBuildGroup (string $groupName, int $order) {

	global string $tmGroups[];

	print ("Building group: " + $groupName + "...");

	$tmGroups[$order] = $groupName;
	string $grpPrefix = "tm" + $groupName;
	string $checkCommand = "tmTickToggle(\"" + $groupName + "\", \"Main\")";

	setParent tmMainGroupCL;

	int $s = 1-(`checkBox -q -v tmMainSelectedSetTicks`);
	frameLayout -l $groupName -cl 1 -cll 1 ($grpPrefix + "Group");
		columnLayout ($grpPrefix + "GroupCL");
		checkBox -l "Toggle All" -v 1 -en $s -cc $checkCommand ($groupName + "Ticks");
	
	setParent tweenMachineWin;

	// make selectionConnection for group and add to master
	string $grpSC = $grpPrefix + "GroupSC";
	selectionConnection -p ($grpPrefix + "GroupCL") -lst $grpSC;
	selectionConnection -e -add $grpSC tmMasterSC;

	print ("done.\n");

}

// ------------------------------------------------------------------------

global proc tmBuildSet (string $groupName, string $setName) {

	global string $tmSets[];
	global int $tmSliderWidth, $tmShowSliders;

	$setLabel = $setName;
	
	$setName = "tm" + $groupName + $setName + "Set";
	$tmSets[size($tmSets)] = $setName;

	// if first set (Selected), check and disable
	// if second set or later, check only; enable based on current Selected set check status
	int $tickCheck, $tickEnable;
	if (size($tmSets)==1) {
		$tickCheck = 1;
		$tickEnable = 0;
	} else {
		$tickCheck = 1;
		$tickEnable = 1-(`checkBox -q -v tmMainSelectedSetTicks`);
		checkBox -e -en 1 tmMainSelectedSetTicks;
	}

	string $groupCLName = "tm" + $groupName + "GroupCL"; // this will need to change to the name of the group form
	setParent ($groupCLName);

	separator -style "none" -h 7 ($setName + "Spacer");  // this will go away once the form system is used

	string $checkCommand = "tmTickToggle(\"" + $setName + "\", \"" + $groupName + "\")";
	rowLayout -nc 2 -adj 2 -w 300 -h 30 -rat 1 "bottom" 10 -cat 1 "both" 5 -cal 1 "right" ($setName + "OuterRow");
		columnLayout -adj 1;
			rowLayout -nc 2 -adj 2 -cw2 20 70 -rat 1 "bottom" 5 -rat 2 "bottom" 5;
				checkBox -l "" -v $tickCheck -en $tickEnable -cc $checkCommand -rs 1 ($setName + "Ticks");
				text -l $setLabel -al "right" ($setName + "Label");
			setParent ..;
		setParent ..;
		columnLayout;
			floatSliderGrp -field 1 -min -100.0 -max 100.0 -v 0 -adj 2 -m $tmShowSliders -cw2 40 $tmSliderWidth -cc ("tmSliderStart(\"" + $setName + "\");") ($setName + "Bias");

			tmBuildButtonRow ($setName);

	setParent $groupCLName;

	// make selectionConnection for set and add to parent group's selectionConnection
	if ($setName != "tmMainSelectedSet" && $setName != "tmCharacterSetCurrentSet") {
		string $setSC = $setName + "SC";
		string $grpSC = "tm" + $groupName + "GroupSC";
		selectionConnection -p ($setName + "OuterRow") -obj $setName $setSC;
		selectionConnection -e -add $setSC $grpSC;
	}


}

// ------------------------------------------------------------------------

global proc tmBuildButtonRow (string $setName) {

	global int $tmNumButtons, $tmSliderWidth, $tmShowButtons, $tmButtonRowPad;
	global float $tmButtonVal[];
	global string $tmButtonRGB[];

	int $totalSpace = ($tmNumButtons) * 5;
	int $buttonWidth = floor((($tmSliderWidth)-$totalSpace)/$tmNumButtons);
	int $leftover = ($tmSliderWidth) - ($totalSpace + ($tmNumButtons * $buttonWidth)) + $tmButtonRowPad;
		
	string $rowLayoutName = $setName + "Buttons";
	if (`rowLayout -exists $rowLayoutName`) deleteUI $rowLayoutName;
	
	string $rowBuilder = "rowLayout -nc " + ($tmNumButtons + 1) + " -w 300 -h 15 -m " + $tmShowButtons + " -cw 1 " + ($leftover + 40);
		
	int $i;
	for ($i=1; $i<=$tmNumButtons; $i++)
		$rowBuilder += " -cw " + ($i + 1) + " " + ($buttonWidth + 5);
	$rowBuilder += " " + $rowLayoutName + ";";
		
	eval $rowBuilder;
		
	text -l "" -h 12;

 	for ($i=0; $i<$tmNumButtons; $i++) {

		string $buttonName = $setName + "Button" + $i;
		string $canvasBuilder = "canvas -rgb " + $tmButtonRGB[$i] + " -width " + $buttonWidth;
		$canvasBuilder += " -h 10 -ann " + $tmButtonVal[$i] + " -pc \"tmButtonStart(" + $tmButtonVal[$i] + ",\\\"" + $setName + "\\\")\" " + $buttonName + ";";
		eval $canvasBuilder;
			
	}
}

// ************************************************************************
// ************************************************************************
//                         Add Sets and Groups
// ************************************************************************
// ************************************************************************

global proc tmAddGroupUI () {

	window -t "Add Group" -w 100 -h 5 -rtf 1 -s 0 -mnb 0 -mxb 0 tmGroupUIWin;

	string $command = "tmAddGroup(`textField -q -tx tmGroupUIText`)";
	formLayout -nd 10 tmAddGrpFL;
		text -l "Enter name of new group:" tmAddGrpLabel;
		textField -w 100 -ec $command tmGroupUIText;
		button -l "OK" -al "center" -c $command tmAddGrpOK;

	formLayout -e
		-af tmAddGrpLabel "top" 5
		-af tmAddGrpLabel "left" 5
		-af tmAddGrpLabel "right" 5
		
		-ac tmGroupUIText "top" 5 tmAddGrpLabel
		-af tmGroupUIText "left" 5
		-af tmGroupUIText "right" 5
		
		-ac tmAddGrpOK "top" 5 tmGroupUIText
		-ap tmAddGrpOK "left" 0 2
		-ap tmAddGrpOK "right" 0 8
		
		tmAddGrpFL;
	
	showWindow tmGroupUIWin;

}

// ------------------------------------------------------------------------

global proc tmAddGroup (string $newGroup) {

	global string $tmGroups[], $currParent;

	if (`isValidObjectName($newGroup)`) {
		if (`frameLayout -ex ("tm" + $newGroup + "Group")`) {
			confirmDialog -t "Group exists" -m "A group by that name already exists.  Please choose a new name.";
		} else {
	
			$currParent = "tmGroups1";
			int $order = size($tmGroups);
			string $nodeString = "tmGroup id=\"" + $newGroup + "\" order=\"" + $order + "\"";
			makeNode ($nodeString,0);
	
			select -cl;

			tmBuildGroup ($newGroup, $order);

			if (!`menuItem -q -en tmAddSetMI`) menuItem -e -en 1 tmAddSetMI;
			
			if (`window -ex tmGroupUIWin`) textField -e -tx "" tmGroupUIText;

		}
	} else {
		confirmDialog -t "Invalid name" -m "The name entered is not valid.\nGroup names must be valid Maya object names.";
	}

}

// ------------------------------------------------------------------------

global proc tmAddSetUI () {

	global string $tmGroups[];

	window -t "Add Set" -w 50 -h 10 -rtf 1 -s 0 -mnb 0 -mxb 0 tmSetUIWin;

	string $command = "tmAddSet(`ls -sl`,`textField -q -tx tmSetUIText`,`optionMenu -q -v tmSelectGroup`)";
	formLayout -w 50 -nd 10 tmSetUIFL;

		text -l "Enter name of new set:" tmSetUILabel1;
		textField -ec $command tmSetUIText;

		text -l "Add new set to group:" tmSetUILabel2;
		optionMenu tmSelectGroup;
			for ($grp in $tmGroups) menuItem -l $grp;
		setParent tmSetUIFL;
		button -l "OK" -al "center" -c $command tmSetUIOK;
	
	formLayout -e
	
		-af tmSetUILabel1 "top" 5
		-af tmSetUILabel1 "left" 5
		-af tmSetUILabel1 "right" 5
		
		-ac tmSetUIText "top" 5 tmSetUILabel1
		-af tmSetUIText "left" 5
		-af tmSetUIText "right" 5
		
		-ac tmSetUILabel2 "top" 5 tmSetUIText
		-af tmSetUILabel2 "left" 5 
		-af tmSetUILabel2 "right" 5
		
		-ac tmSelectGroup "top" 5 tmSetUILabel2
		-af tmSelectGroup "left" 5
		-af tmSelectGroup "right" 5
		
		-ac tmSetUIOK "top" 7 tmSelectGroup
		-ap tmSetUIOK "left" 0 2
		-ap tmSetUIOK "right" 0 8
		-af tmSetUIOK "bottom" 5
		
		tmSetUIFL;
	
	showWindow tmSetUIWin;

}

// ------------------------------------------------------------------------

global proc tmAddSet (string $nodes[], string $newSet, string $groupName) {

	global string $tmGroups[], $tmSets[], $currParent;

	if (!size($nodes)) {
		confirmDialog -t "Nothing Selected" -m "You must select one or more objects to make a new set.";
		return;
	}

	if (`isValidObjectName($newSet)`) {

		string $set;
		for ($set in tmSetsInGroup($groupName,0)) {
			if ($newSet == $set) {
				confirmDialog -t "Set exists in selected group" -m "A set by that name already exists in the selected group.\nPlease choose a new set name, or pick a different group.";
				return;
			}
		}

		string $longSetName = "tm" + $groupName + $newSet + "Set";
		
		// create new set
		sets -n $longSetName $nodes;
		select -r $nodes;

		string $groups[];
		$groups = getByType("tmGroups1","tmGroup");

		for ($grp in $groups) {
			if(`getAttr($grp+".id")` == $groupName) {
				$currParent = $grp;
			}
		}

		string $sets[];
		$sets = getByType($currParent,"tmSet");
		int $order = size($sets);

		string $nodeString = "tmSet id=\"" + $newSet + "\" order=\"" + $order + "\"";
		makeNode ($nodeString,0);

		for ($n in $nodes) {
			makeNode ("tmObject",0);
			addContent ($n);
			closeTag;
		}

		select -r $nodes;

		tmBuildSet ($groupName, $newSet);
			
		if (`window -ex tmSetUIWin`) textField -e -tx "" tmSetUIText;
		string $parentLayout = "tm" + $groupName + "Group";
		frameLayout -e -cl 0 $parentLayout;
	} else {
		confirmDialog -t "Invalid name" -m "The name entered is not valid.\nSet names must be valid Maya object names.";
	}

}
// ************************************************************************
// ************************************************************************
//                          Character set utilities
// ************************************************************************
// ************************************************************************

global proc tmAddCharacterGroup () {

	global string $tmGroups[], $currParent;
	
	// check to see if custom set already exists
	if (`frameLayout -ex "tmCharacterSetGroup"`) {
		confirmDialog -t "Group exists" -m "A group and set that control the current character set already exist.";
		return;
	}
	
	// add group
	$currParent = "tmGroups1";
	int $order = size($tmGroups);
	string $nodeString = "tmGroup id=\"CharacterSet\" order=\"" + $order + "\"";
	makeNode ($nodeString,0);
	
	tmBuildGroup ("CharacterSet", $order);

	if (!`menuItem -q -en tmAddSetMI`) menuItem -e -en 1 tmAddSetMI;
	
	// add set named "Current"

	makeNode ("tmSet id=\"Current\" order=\"0\"",0);

	makeNode ("tmObject",0);
	addContent ("tmCustomCharacterSet");
	closeTag;

	tmBuildSet ("CharacterSet", "Current");

}

proc tmGetSubChars (string $curChar, string $group) {
	int $i;
	string $ind, $subChars[], $obj, $charSet;
	
	$charSet = $curChar;
	// if name has namespace, replace colon with underscore
	if (`match ".*:.*" $curChar` != "") $curChar = `substitute ":" $curChar "_"`;

	print ("Adding set for sub-character: " + $charSet + "\n");
	tmAddSet ({$charSet}, $curChar, $group);
	select -cl;
	
	$subChars = `character -q $charSet`;

	for ($obj in $subChars) if (`nodeType $obj` == "character") tmGetSubChars ($obj, $group);
}

global proc tmImportCharSets () {

	string $chars[], $subChars[], $obj, $charSet;
	$chars = `currentCharacters`;

	for ($char in $chars) {
		$charSet = $char;
		// if name has namespace, replace colon with underscore
		if (`match ".*:.*" $char` != "") $char = `substitute ":" $char "_"`;
		
		if (`frameLayout -ex ("tm" + $char + "Group")`) 
			print ("Skipping character: " + $char + " .  Group already exists.\n");
		else {
			print ("Adding group and set for parent character: " + $charSet + "\n");

			tmAddGroup ($char);
			tmAddSet ({$charSet}, $char, $char);
			select -cl;
			
			$subChars = `character -q $charSet`;
	
			for ($obj in $subChars) if (`nodeType $obj` == "character") tmGetSubChars ($obj, $char);

		}
	}
}

// ************************************************************************
// ************************************************************************
//                        Read from XML data in scene
// ************************************************************************
// ************************************************************************

global proc tmReadXML () {

	global string $tmGroups[], $tmSets[], $tmButtonRGB[];
	global int $tmNumButtons, $tmShowButtons, $tmShowSliders;
	global float $tmButtonVal[];

	clear $tmGroups;
	clear $tmSets;
	clear $tmButtonVal;
	clear $tmButtonRGB;

	$tmSets[0] = "tmMainSelectedSet";

	// read button/slider visibility settings
	$tmShowSliders = getData("tmSliderVis1");
	$tmShowButtons = getData("tmButtonVis1");
	menuItem -e -cb $tmShowSliders tmSliderTog;
	menuItem -e -cb $tmShowButtons tmButtonTog;

	// read button values and RGB settings
	$tmNumButtons = (int) `getAttr ("tmButtons1.id")`;
	
	int $i;
	for ($i=0; $i<$tmNumButtons; $i++) {
		string $buttonVal = "tmButtonValue" + ($i+1);
		$tmButtonVal[$i] = `getData ($buttonVal)`;
		string $buttonRGB = "tmButtonRGB" + ($i+1);
		$tmButtonRGB[$i] = `getData ($buttonRGB)`;
	}

	// read groups

	string $groups[];
	$groups = getByType ("tmGroups1","tmGroup");

	for ($grp in $groups) {

		string $grpId = `getAttr ($grp + ".id")`;
		int $grpOrd = `getAttr ($grp + ".order")`;
		$tmGroups[$grpOrd] = $grpId;
		tmBuildGroup ($grpId,$grpOrd);

		// get sets in the group and put them in order

		string $sets[];
		$sets = getByType ($grp, "tmSet");

		string $tmpSet[];
		clear $tmpSet;

		for ($set in $sets) {

			int $setOrd = `getAttr ($set + ".order")`;
			$tmpSet[$setOrd] = $set;

		}
		
		// build sets into groups
		for ($i=0; $i<size($tmpSet); $i++) {
			
			$setName = `getAttr ($tmpSet[$i] + ".id")`;
			string $longSetName = "tm" + $grpId + $setName + "Set";

			// read objects in the set
			string $objects[];
			$objects = getByType ($tmpSet[$i], "tmObject");

			string $obj[];
			clear $obj;
			int $makeSet = 1;
			for ($o in $objects) {
				string $objTmp = `getAttr ($o + ".data")`;
				if (`objExists $objTmp`) 
					$obj[size($obj)] = $objTmp;
				else if ($objTmp == "tmCustomCharacterSet")
					$makeSet = 0;
				else print ("Omitting \"" + $objTmp + "\" from set \"" + $setName + "\". Object does not exist in scene.\n");
				
			}

			// if set does not exist, build it
			
			if (!`objExists $longSetName` && $makeSet) sets -n $longSetName $obj;

			// add set to group

			tmBuildSet ($grpId, $setName);

		}

	}

	if (size($tmGroups)) menuItem -e -en 1 tmAddSetMI;
}

// ************************************************************************
// ************************************************************************
//                         Save and Load XML Data
// ************************************************************************
// ************************************************************************

global proc int tmSaveToFile (string $file, string $fileType) {

	global int $tmNumButtons, $tmShowButtons, $tmShowSliders;
	global string $tmButtonRGB[];
	global float $tmButtonVal[];

	$fileType = ".xml";

	int $chkAgain = 1;

	if (`filetest -w $file` && endsWith($file,$fileType)) $chkAgain = 0;

	// tack on .XML suffix if not already there
	if (!endsWith($file,$fileType)) $file = $file + $fileType;

	// if current file exists, display overwrite confirmation
	string $c;
	if (`filetest -w $file` && $chkAgain) {
		$c = `confirmDialog -t "Overwrite?" -m "File exists.  Overwrite with current data?" -b "Yes" -b "No" -db "Yes" -cb "No" -ds "No"`;
	}

	if ($c != "No") {

		$fileId=`fopen $file "w"`;
	
		fprint $fileId "<?xml version=\"1.0\"?>\n";
		fprint $fileId "<tmData>\n";
	
		// export data for options
		fprint $fileId "   <tmOptions>\n";

		// need to add script to export Options data
		fprint $fileId ("      <tmSliderVis>" + $tmShowSliders + "</tmSliderVis>\n");
		fprint $fileId ("      <tmButtonVis>" + $tmShowButtons + "</tmButtonVis>\n");
		fprint $fileId ("      <tmButtons id=\"" + $tmNumButtons + "\">\n");

		int $i = 0;
		for ($i=0; $i<$tmNumButtons; $i++) {
			fprint $fileId "         <tmButton>\n";
			fprint $fileId ("            <tmButtonRGB>" + $tmButtonRGB[$i] + "</tmButtonRGB>\n");
			fprint $fileId ("            <tmButtonValue>" + $tmButtonVal[$i] + "</tmButtonValue>\n");
			fprint $fileId "         </tmButton>\n";
		}

		fprint $fileId ("      </tmButtons>\n");
		fprint $fileId "   </tmOptions>\n";

		// export data for groups and sets
		fprint $fileId "   <tmGroups>\n";

		string $groups[];
		$groups = getByType ("tmGroups1","tmGroup");

		for ($grp in $groups) {
	
			string $grpId = `getAttr ($grp + ".id")`;
			string $grpOrd = `getAttr ($grp + ".order")`;
			fprint $fileId ("      <tmGroup id=\"" + $grpId + "\" order=\"" + $grpOrd + "\">\n");
	
			string $sets[];
			$sets = getByType ($grp,"tmSet");
	
			for ($set in $sets) {
				string $setId = `getAttr ($set + ".id")`;
				string $order = `getAttr ($set + ".order")`;
				fprint $fileId ("         <tmSet id=\"" + $setId + "\"");
				fprint $fileId (" order=\"" + $order + "\"");
				fprint $fileId (">\n");
	
				string $tmObjects[];
				$tmObjects = getByType ($set,"tmObject");
		
				for ($obj in $tmObjects) {
					string $objName = getData($obj);
					fprint $fileId ("            <tmObject>" + $objName + "</tmObject>\n");
				}
				fprint $fileId ("         </tmSet>\n");
			}
			fprint $fileId "      </tmGroup>\n";
		}

		fprint $fileId "   </tmGroups>\n";
		fprint $fileId "</tmData>\n";
		fclose $fileId;

		// return true to close browser dialog
		return 1;

	} else {
		fileBrowser tmSaveToFile "Save" "" 1;
		return 0;
	}

}

// --------------------------------------------------------------------------

global proc tmLoadFromFile () {

	global string $tmSets[];

	string $c;
	// if a set exists, confirm that user wants to load new data
	if (size($tmSets) > 1) $c = `confirmDialog -t "Replace data?" -m "Replace current data with data from file?" -b "Yes" -b "No" -db "Yes" -cb "No" -ds "No"`;

	if ($c != "No") {

		// show file browser dialog (fileDialog) for user to choose file
		string $file = `fileDialog -dm "*.xml"`;
		if ($file != "") {

			// delete existing XML data
			delete tmXML1;

			// load XML data from file
			loadXML ($file);

			// check that data is valid tweenMachine data
			string $s[] = `ls -sl`;
			string $test[];
			$test = getByType ("XML1","tmOptions");
			if (size($test)==0) {
				confirmDialog -t "Invalid file" -m "Selected file does not contain valid tweenMachine data.";
			} else {
				rename XML1 tmXML1;
				select -cl;
				tweenMachine;
			}
		}
	}

}

// ************************************************************************
// ************************************************************************
//                      Starters and main TM procedure
// ************************************************************************
// ************************************************************************

global proc tmSliderStart (string $name) {

	string $nodes[], $biasCtl;

	$biasCtl = $name + "Bias";
	$bias = (`floatSliderGrp -q -v $biasCtl` + 100) / 200;

	if (startsWith($name,"tmCharacterSet")) 
		$nodes = `currentCharacters`;
	else 	if ($biasCtl == "tmMainSelectedSetBias") 
			$nodes = `ls -sl`;
		else
			$nodes = `sets -q $name`;


	tween_Machine ($bias,$nodes);

}

// --------------------------------------------------------------------------

global proc tmButtonStart (float $bias, string $name) {

	string $nodes[];

	$biasCtl = $name + "Bias";
	floatSliderGrp -e -v $bias $biasCtl;
	$bias = ($bias + 100) / 200;

	if (startsWith ($name, "tmCharacterSet")) 
		$nodes = `currentCharacters`;
	else 	if ($biasCtl == "tmMainSelectedSetBias") 
			$nodes = `ls -sl`;
		else
			$nodes = `sets -q $name`;

	tween_Machine ($bias,$nodes);

}

// --------------------------------------------------------------------------

global proc tween_Machine(float $bias, string $nodes[]) {
	
	global int $tmSpecTick;
	string $nodes[], $curves[], $newCurves[], $attrs[], $crv, $attr, $biasCtl; 

	clear $curves;
	clear $newCurves;

	string $pf = `getPanel -wf`;

	float $timeRng[] = `timeControl -q -ra timeControl1`;  // get selected range on timeline (as an array)
	int $timeC = $timeRng[0]; // current keyframe, where new key will be added

	$curves = `keyframe -q -name $nodes` ; // get names of all keyframed curves on all selected objects
	$attrs = `channelBox -q -sma "mainChannelBox"`; // get names of selected attributes in channel box

	if (size($attrs) > 0) {
	
	// convert short entries in attribute list to long names
	int $i;
	for ($i=0; $i<size($attrs); $i++) {
		switch ($attrs[$i]) {
			case "tx": $attrs[$i] = "translateX"; break;
			case "ty": $attrs[$i] = "translateY"; break;
			case "tz": $attrs[$i] = "translateZ"; break;
			case "rx": $attrs[$i] = "rotateX"; break;
			case "ry": $attrs[$i] = "rotateY"; break;
			case "rz": $attrs[$i] = "rotateZ"; break;
			case "sx": $attrs[$i] = "scaleX"; break;
			case "sy": $attrs[$i] = "scaleY"; break;
			case "sz": $attrs[$i] = "scaleZ"; break;
			case "v": $attrs[$i] = "visibility"; break;
		}
	}

	// compare selected attributes to curves and build new curves array

	for ($crv in $curves) {
		for ($attr in $attrs) {
			if (endsWith($crv, $attr)) $newCurves[size($newCurves)] = $crv;
		}
	}
	clear $curves;
	$curves = $newCurves;
	}

	waitCursor -state on ;
	
		// For each curve...
	for ($crv in $curves)  {

		// Find time for next and previous keys...
		int $timeP = `findKeyframe -which previous $crv`;
		int $timeN = `findKeyframe -which next $crv`;

		// Find previous and next tangent types
		string $tanInPs[] = `keyTangent -time $timeP -q -itt $crv`;
		string $tanOutPs[] = `keyTangent -time $timeP -q -ott $crv`;
		string $tanInNs[] = `keyTangent -time $timeN -q -itt $crv`;
		string $tanOutNs[] = `keyTangent -time $timeN -q -ott $crv`;

		// Set new in and out tangent types based on previous and next tangent types
		string $tanInC = $tanOutPs[0];
		string $tanOutC = $tanInNs[0];

		// However...if any of the types (previous or next) is "fixed", then use the global (default) tangent instead

		if (($tanInPs[0] == "fixed") || ($tanOutPs[0] == "fixed") || ($tanInNs[0] == "fixed") || ($tanOutNs[0] == "fixed"))
		{
		string $tanInGs[] = `keyTangent -q -g -itt`;
		string $tanOutGs[] = `keyTangent -q -g -ott`;
		$tanInC = $tanInGs[0];
		$tanOutC = $tanOutGs[0];
		}
		else
		{		
		if ($tanOutNs[0] == "step")
			$tanOutC = $tanOutNs[0];
		}

		// Find previous and next key values
		float $valPs[] = `keyframe -time $timeP -q -valueChange $crv` ;
		float $valNs[] = `keyframe -time $timeN -q -valueChange $crv` ;

		float $valP = $valPs[0] ;
		float $valN = $valNs[0] ;

		// Find difference in value between previous and next keys

		float $diff = $valN - $valP ;

		// Find percentage of difference to use based on Pose Bias value

		float $diffToUse = $diff * $bias;

		// Find current key value by adding amount used to previous key

		float $valC = $valP + $diffToUse;

		// Set new keyframe

		setKeyframe -t $timeC -v $valC -ott $tanOutC $crv;
		if ($tmSpecTick) keyframe -tds on -t $timeC $crv;
		
		if ($tanInC != "step")
		keyTangent -t $timeC -itt $tanInC $crv;

		}
	
	currentTime -e $timeC;

	setFocus $pf;

	waitCursor -state off ;
	
}

// ************************************************************************
// ************************************************************************
//                         Misc. helper procedures
// ************************************************************************
// ************************************************************************

global proc string[] tmSetsInGroup (string $group, int $type) {
	// $type: 0 for short set names, 1 for full set names, 2 for XML object names

	global string $tmSets[];
	string $setsInGroup[];

	if ($type < 2) {
		for ($set in $tmSets) {
			string $setSW = "tm" + $group;
			if (startsWith ($set, $setSW)) {
				if ($type == 0) {
					$set = `substitute $setSW $set ""`;
					$set = `substitute "Set" $set ""`;
				}
				$setsInGroup[size($setsInGroup)] = $set;
			}
		}
	} else {
		for ($grp in getByType("tmGroups1","tmGroup")) {
			if (`getAttr ($grp + ".id")` == $group) $setsInGroup = getByType($grp,"tmSet");
		}
	}

	return $setsInGroup;
}

// --------------------------------------------------------------------------

global proc string tmFindInXML (string $type, string $parent, string $att, string $val) {

	// find set or group in XML data with parent $parent where attribute $att = value $val
	// $type = 0 (set) or 1 (group)

	string $foundObj;

	string $obj;
	for($obj in getByType($parent,$type)) {
		string $v = `getAttr ($obj + $att)`;
		if ($v == $val) $foundObj = $obj;
	}

	return $foundObj;
}

// --------------------------------------------------------------------------

global proc tmRestoreTimeControl () {
	timeControl -e -mlc animationList timeControl1;
}
"""

# Old XML file format reference
"""
<?xml version="1.0"?>
<tmData>
   <tmOptions>
      <tmSliderVis>1</tmSliderVis>
      <tmButtonVis>1</tmButtonVis>
      <tmButtons id="7">
         <tmButton>
            <tmButtonRGB>0.6 0.6 0.6</tmButtonRGB>
            <tmButtonValue>-75</tmButtonValue>
         </tmButton>
         <tmButton>
            <tmButtonRGB>0.6 0.6 0.6</tmButtonRGB>
            <tmButtonValue>-60</tmButtonValue>
         </tmButton>
         <tmButton>
            <tmButtonRGB>0.6 0.6 0.6</tmButtonRGB>
            <tmButtonValue>-33</tmButtonValue>
         </tmButton>
         <tmButton>
            <tmButtonRGB>0.6 0.6 0.6</tmButtonRGB>
            <tmButtonValue>0</tmButtonValue>
         </tmButton>
         <tmButton>
            <tmButtonRGB>0.6 0.6 0.6</tmButtonRGB>
            <tmButtonValue>33</tmButtonValue>
         </tmButton>
         <tmButton>
            <tmButtonRGB>0.6 0.6 0.6</tmButtonRGB>
            <tmButtonValue>60</tmButtonValue>
         </tmButton>
         <tmButton>
            <tmButtonRGB>0.6 0.6 0.6</tmButtonRGB>
            <tmButtonValue>75</tmButtonValue>
         </tmButton>
      </tmButtons>
   </tmOptions>
   <tmGroups>
   </tmGroups>
</tmData>

"""

