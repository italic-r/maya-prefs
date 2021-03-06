'''
Group Selection Script

PYTHON*
----------------------------------------
'''

import maya.cmds as MC

GE_LIST = "graphEditorList"
GE_SELCON = "graphEditor1FromOutliner"


def getSelected():
    """
    Returns the selected nodes from the graph editors list.
    """
    return MC.selectionConnection(GE_SELCON, q=1, obj=1) or []


def getLoaded():
    """
    Returns a list of the nodes that are loaded into the graph editor
    """
    return MC.selectionConnection(GE_LIST, q=1, obj=1) or []


def highlightAttrs(attrs=[]):
    """
    Syncs all the selected attributes of the loaded nodes in the graph editor

    If the attr flag is passed, only that attribute would get synced,
    otherwise the selected attributes will be used
    """

    loaded = getLoaded()
    ## If there is nothing loaded in GE, dont do anything
    if not len(loaded):
        MC.warning("There is nothing loaded in graph editor")
        return

    ## Figure out the selected attrs if there isn't one passed in
    if not len(attrs):
        allselected = getSelected()
        if allselected == []:
            msg = ("There is no attribute selected in graph editor, nor " +
                   " one passed as an argument. Can't sync selection")
            MC.warning(msg)
            return

        attrs = []
        for alls in allselected:
            toks = alls.split(".")
            if len(toks) < 2:
                continue  # Skip highlighted nodes

            attrs.append(toks[1])

        attrs = list(set(attrs))

    ## If there are no attrs, then nothing to highlight
    if not len(attrs):
        MC.warning("There are no attrs to highlight")
        return

    ## Loop through loaded nodes, and highglight its attrs
    tohighlight = []
    for load in loaded:
        for attr in attrs:
            tohighlight.append(load + "." + attr)

    ## Load the new selection
    for x in tohighlight:
        MC.selectionConnection(GE_SELCON, select=x, e=1)

    print "Synced Highlighted Attributes"
