import maya.cmds as cmds
import maya.mel as mel


def hideVPelement(typ):
    """
    //Hide viewport element (nurbs, polys, joints, etc)

    string $activePanel = `getPanel -wf`;
    if (`modelEditor -q -locators $activePanel` == 1) {
     modelEditor -e -locators 0 $activePanel;
    } else {
     modelEditor -e -locators 1 $activePanel;
    }
    """

    activePanel = cmds.getPanel(wf=True)
    if typ == "locators":
        if cmds.modelEditor(activePanel, q=True, locators=True):
            cmds.modelEditor(activePanel, e=True, locators=False)
        else:
            cmds.modelEditor(activePanel, e=True, locators=True)
    elif typ == "joints":
        if cmds.modelEditor(activePanel, q=True, joints=True):
            cmds.modelEditor(activePanel, e=True, joints=False)
        else:
            cmds.modelEditor(activePanel, e=True, joints=True)
    elif typ == "nurbsCurves":
        if cmds.modelEditor(activePanel, q=True, nurbsCurves=True):
            cmds.modelEditor(activePanel, e=True, nurbsCurves=False)
        else:
            cmds.modelEditor(activePanel, e=True, nurbsCurves=True)
    elif typ == "polymeshes":
        if cmds.modelEditor(activePanel, q=True, polymeshes=True):
            cmds.modelEditor(activePanel, e=True, polymeshes=False)
        else:
            cmds.modelEditor(activePanel, e=True, polymeshes=True)
    elif typ == "strokes":
        if cmds.modelEditor(activePanel, q=True, strokes=True):
            cmds.modelEditor(activePanel, e=True, strokes=False)
        else:
            cmds.modelEditor(activePanel, e=True, strokes=True)


def frameRange():
    """
    //Frame time range in graph/dopesheet

    string $panType = `getPanel -withFocus`;
    {
    if ($panType == "dopeSheetPanel1") {
        animView -startTime (`playbackOptions -query -minTime` - 8) -endTime (`playbackOptions -query -maxTime` + 8) dopeSheetPanel1DopeSheetEd;
        }
    else animView -startTime (`playbackOptions -query -minTime` - 8) -endTime (`playbackOptions -query -maxTime` + 8) graphEditor1GraphEd;
    }
    """

    panType = cmds.getPanel(wf=True)
    animStart = int(cmds.playbackOptions(q=True, min=True))
    animEnd = int(cmds.playbackOptions(q=True, max=True))
    if panType == "dopeSheetPanel1":
        cmds.animView('dopeSheetPanel1DopeSheetEd', st=animStart - 5, et=animEnd + 5)
    elif panType == "graphEditor1":
        cmds.animView('graphEditor1GraphEd', st=animStart - 5, et=animEnd + 5)


def centerView():
    """
    //Center time cursor in graph/dopesheet

    string $panType = `getPanel -withFocus`;
    {
    if ($panType == "dopeSheetPanel1") {
        dopeSheetEditor -edit -lookAt currentTime dopeSheetPanel1DopeSheetEd;
        }
    else animCurveEditor -edit -lookAt currentTime graphEditor1GraphEd;
    }
    """

    panType = cmds.getPanel(wf=True)
    print(panType)
    if panType == "dopeSheetPanel1":
        cmds.dopeSheetEditor('dopeSheetPanel1DopeSheetEd', e=True, la='currentTime')
    elif panType == "graphEditor1":
        cmds.animCurveEditor('graphEditor1GraphEd', e=True, la='currentTime')


def breakTan(arg=None):
    """
    //Break and unlock tangents

    undoInfo -stateWithoutFlush off;
    MoveTool;
    keyTangent -lock off;
    keyTangent -weightLock off;
    undoInfo -stateWithoutFlush on;


    //Unify and lock tangents

    undoInfo -stateWithoutFlush off;
    keyTangent -lock on;
    keyTangent -weightLock on;

    global string $gSelect;   // Sacred Select Tool
    setToolTo $gSelect;

    undoInfo -stateWithoutFlush on;
    """

    if arg == "Press":
        cmds.undoInfo(swf=False)
        mel.eval('MoveTool;')
        cmds.keyTangent(e=True, l=False)
        cmds.keyTangent(e=True, wl=False)
        cmds.undoInfo(swf=True)
    elif arg == "Release":
        cmds.undoInfo(swf=False)
        cmds.keyTangent(e=True, l=True)
        cmds.keyTangent(e=True, wl=True)
        mel.eval('global string $gSelect; setToolTo $gSelect')
        cmds.undoInfo(swf=True)


def TanLock(arg=None):
    """
    //Lock tangents

    string $panType = `getPanel -withFocus`;
    {
    if ($panType == "graphEditor1") {
        undoInfo -stateWithoutFlush off;
        keyTangent -weightLock off;
        undoInfo -stateWithoutFlush on;
        }
    else dR_DoCmd("pointSnapPress");
    }


    //Unlock tangents

    string $panType = `getPanel -withFocus`;
    {
    if ($panType == "graphEditor1") {
        undoInfo -stateWithoutFlush off;
        keyTangent -weightLock on;
        undoInfo -stateWithoutFlush on;
        }
    else dR_DoCmd("pointSnapRelease");
    }
    """

    panType = cmds.getPanel(wf=True)
    if arg == "Press":
        if panType == "graphEditor1":
            cmds.undoInfo(swf=False)
            mel.eval('MoveTool;')
            cmds.keyTangent(e=True, wl=False)
            cmds.undoInfo(swf=True)
        else:
            cmds.snapMode(point=True)
    elif arg == "Release":
        if panType == "graphEditor1":
            cmds.undoInfo(swf=False)
            mel.eval('global string $gSelect; setToolTo $gSelect')
            cmds.keyTangent(e=True, wl=True)
            cmds.undoInfo(swf=True)
        else:
            cmds.snapMode(point=False)


def skCluster():
    """Turns off custom normals on skin clusters (old problem in old Mayas)"""
    sceneGeo = cmds.ls(g=True)
    if len(sceneGeo) != 0:
        charSC = [skin for skin in cmds.listConnections(sceneGeo, type='skinCluster')]

        for sc in charSC:
            cmds.setAttr((sc + '.deformUserNormals'), False)


def cacheVP():
    """
    //Cache viewport geometry for playback

    undoInfo -stateWithoutFlush off;

    string $activePanel = `getPanel -wf`;
    modelEditor -e -grid false $activePanel;
    modelEditor -e -allObjects 0 $activePanel;
    modelEditor -e -polymeshes 1 $activePanel;

    int $rangeStartFrame = `playbackOptions -q -min`;

    currentTime -e $rangeStartFrame;
    playbackOptions -playbackSpeed 0 -loop "once" -by 1;
    playButtonForward;
    playbackOptions -playbackSpeed 1 -loop "continuous";

    undoInfo -stateWithoutFlush on;
    """

    cmds.undoInfo(swf=False)
    panType = cmds.getPanel(wf=True)
    cmds.modelEditor(panType, e=True, gr=False)
    cmds.modelEditor(panType, e=True, alo=False)
    cmds.modelEditor(panType, e=True, pm=True)

    rangeStartFrame = cmds.playbackOptions(q=True, min=True)

    cmds.currentTime = int(rangeStartFrame)
    cmds.playbackOptions(ps=0, l="once", by=1)
    cmds.play(f=True, ps=True)
    cmds.playbackOptions(ps=1, l="continuous")
    cmds.undoInfo(swf=True)


def resetVP():
    """
    Reset viewport elements to sane state

    string $activePanel = `getPanel -wf`;
    modelEditor -e -grid false $activePanel;
    modelEditor -e -allObjects 0 $activePanel;

    modelEditor -e -polymeshes 1 $activePanel;
    modelEditor -e -nurbsCurves 1 $activePanel;
    modelEditor -e -locators 1 $activePanel;
    modelEditor -e -cameras 1 $activePanel;
    modelEditor -e -motionTrails 1 $activePanel;
    modelEditor -e -twoSidedLighting true $activePanel;
    """

    panType = cmds.getPanel(wf=True)
    cmds.modelEditor(panType, e=True, gr=False)
    cmds.modelEditor(panType, e=True, alo=False)

    cmds.modelEditor(panType, e=True, pm=True)
    cmds.modelEditor(panType, e=True, nc=True)
    cmds.modelEditor(panType, e=True, lc=True)
    cmds.modelEditor(panType, e=True, ca=True)
    cmds.modelEditor(panType, e=True, mt=True)
    cmds.modelEditor(panType, e=True, tsl=True)


def useOSD():
    """
    Use OSD non-adaptive, 1 subdivision, enable OCL, low OCL tesselation.
    """

    for msh in cmds.ls(type='mesh'):
        cmds.setAttr(msh + ".useGlobalSmoothDrawType", False)
        cmds.setAttr(msh + ".smoothDrawType", 2)
        cmds.setAttr(msh + ".smoothLevel", 1)
        cmds.setAttr(msh + ".enableOpenCL", True)
        cmds.setAttr(msh + ".smoothTessLevel", 2)


def pin_control():
    # Rigging Dojo: 2016 v.2
    aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider')
    selection = cmds.ls(sl=True)
    selectionActvive = cmds.timeControl(aPlayBackSliderPython, query=True, rangeVisible=True)
    selectedRange = cmds.timeControl(aPlayBackSliderPython, query=True, rangeArray=True)
    frameRange = range(*map(int, selectedRange))
    zeroStartKey = cmds.setKeyframe(selection, time=(selectedRange[0] - 1), id=True)  # zero the frames to base layer adjust as needed
    startTime = cmds.currentTime(selectedRange[0])  # makesure pose is from the start of the selection
    keyRange = cmds.setKeyframe(selection, time=frameRange)  # Set all the keys at the same time
    zeroEndKey = cmds.setKeyframe(selection, time=(selectedRange[1] + 1), id=True)  # zero the frames to base layer adjust as needed
