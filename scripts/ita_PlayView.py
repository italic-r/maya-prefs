"""
PlayView: Save a viewport for single-view playback mode.

This script will benefit you if your playback mode is set to "active"
instead of "all." Otherwise it will play forward as normal. Use the given
button grid to select a viewport to play through. Set it as default to save
it for future playback. Set this script to a hotkey for easy reuse.

Help: Open a help window with this information in it.
Cancel: Close PlayView without setting defaults or playback.
Make Default: Save selected viewport to prevent future prompts.
Select a viewport with the provided buttons. One window will pop up for each
window with a viewport in it.

import ita_PlayView
#reload(ita_PlayView)  # To reset default
#ita_PlayView.destroy_window()  # To destroy all PlayView windows
ita_PlayView.init()

(c) Jeffrey "italic" Hoover
italic DOT rendezvous AT gmail DOT com
30 October 2016

Licensed under the Apache 2.0 license.
This script can be used for non-commercial
and commercial projects free of charge.
For more information, visit:
https://www.apache.org/licenses/LICENSE-2.0
"""

import logging
import maya.cmds as cmds
import maya.mel as mel
from functools import partial

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

windowID = 'PlayView'
helpID = 'PlayViewHelp'
custom_viewport = ""  # Saves panel name for future playback


def play_button(*args):
    """Play functionality."""
    return mel.eval(
        "undoInfo -stateWithoutFlush off;"
        "playButtonForward;"
        "undoInfo -stateWithoutFlush on;"
    )


def play_view(view):
    """Play with specified viewport."""
    cmds.setFocus(view)
    destroy_window()
    play_button()


def play_view_caller(make_default, view, *args):
    """
    Caller to make use of Default checkbox.
    Ultimately call play_view() to play with specific view.
    """
    if cmds.checkBox(make_default, q=True, v=True) is True:
        global custom_viewport
        custom_viewport = view
        log.info("Default viewport for playback is now {}.".format(custom_viewport))
    play_view(view)


def gui(ctrl, pWindowTitle, winID, TLC, *args):
    """Draw window."""

    lconfig = get_layout_config(ctrl)
    lconfigarray = get_layout_child_array(ctrl)

    log.debug("Layout: {}".format(ctrl))
    log.debug("Layout config: {}".format(lconfig))
    log.debug("Children: {}".format(lconfigarray))

    win_draw = cmds.window(
        winID,
        title=pWindowTitle,
        titleBar=False,
        sizeable=False,
        resizeToFitChildren=True,
        tlc=TLC,
        wh=(255, 200)
    )
    rowcol = cmds.rowColumnLayout(
        numberOfColumns=1,
        columnWidth=[(1, 250)],
        columnOffset=[(1, 'both', 5)]
    )
    cmds.separator(h=5, style='none')
    cmds.text(label='Select a viewport to play from.')
    cmds.separator(h=5, style='none')
    cmds.rowLayout(
        parent=rowcol,
        numberOfColumns=3,
        columnAttach=[
            (1, 'both', 0),
            (2, 'both', 5),
            (3, 'both', 0)
        ],
        columnWidth=[
            (1, 75),  # Total == 250 - margins
            (2, 90),
            (3, 75)
        ]
    )
    cmds.button(label='Help', command=help_call)
    makeDefault = cmds.checkBox(label='Make Default')
    cmds.button(label='Cancel', command=destroy_window)

    button_grid(rowcol, lconfigarray, makeDefault, lconfig)

    cmds.showWindow()
    cmds.window(win_draw, e=True, tlc=TLC, wh=(255, 200))


def button_grid(parent, child_array, make_default, layout_config=None, *args):
    """UI grid based on layout from get_layout_config()."""

    RC = cmds.columnLayout(p=parent)
    cmds.rowLayout(parent=RC, nc=1)
    cmds.separator(h=5, style='none')

    if layout_config == "single":
        # 1*1, center button
        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=135, label="", command=partial(play_view_caller, make_default, child_array[0]))

    elif layout_config == "quad":
        # 2*2
        cmds.rowLayout(parent=RC, nc=2)
        cmds.button(w=(240 / 2), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[0]))
        cmds.button(w=(240 / 2), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[1]))

        cmds.rowLayout(parent=RC, nc=2)
        cmds.button(w=(240 / 2), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[3]))
        cmds.button(w=(240 / 2), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[2]))

    elif layout_config == "horizontal2":
        # 1*2
        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[0]))

        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[1]))

    elif layout_config == "vertical2":
        # 2*1
        cmds.rowLayout(parent=RC, nc=2)
        cmds.button(w=(240 / 2), h=135, label="", command=partial(play_view_caller, make_default, child_array[0]))
        cmds.button(w=(240 / 2), h=135, label="", command=partial(play_view_caller, make_default, child_array[1]))

    elif layout_config == "horizontal3":
        # 1*3
        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 3), label="", command=partial(play_view_caller, make_default, child_array[0]))

        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 3), label="", command=partial(play_view_caller, make_default, child_array[1]))

        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 3), label="", command=partial(play_view_caller, make_default, child_array[2]))

    elif layout_config == "vertical3":
        # 3*1
        cmds.rowLayout(parent=RC, nc=3)
        cmds.button(w=(240 / 3), h=135, label="", command=partial(play_view_caller, make_default, child_array[0]))
        cmds.button(w=(240 / 3), h=135, label="", command=partial(play_view_caller, make_default, child_array[1]))
        cmds.button(w=(240 / 3), h=135, label="", command=partial(play_view_caller, make_default, child_array[2]))

    elif layout_config == "top3":
        # 2*1
        cmds.rowLayout(parent=RC, nc=2)
        cmds.button(w=(240 / 2), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[0]))
        cmds.button(w=(240 / 2), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[1]))

        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 2), label="", command=child_array[2])

    elif layout_config == "left3":
        # 2*2
        row1 = cmds.rowLayout(p=RC, nc=2)

        col1 = cmds.columnLayout(p=row1)
        cmds.button(w=(240 / 2), h=(130 / 2), p=col1, label="", command=partial(play_view_caller, make_default, child_array[0]))
        cmds.separator(h=5, style='none')
        cmds.button(w=(240 / 2), h=(130 / 2), p=col1, label="", command=partial(play_view_caller, make_default, child_array[2]))

        col2 = cmds.columnLayout(p=row1)
        cmds.button(w=(240 / 2), h=135, p=col2, label="", command=partial(play_view_caller, make_default, child_array[1]))

    elif layout_config == "bottom3":
        # 2*1
        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[0]))

        cmds.rowLayout(parent=RC, nc=2)
        cmds.button(w=(240 / 2), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[2]))
        cmds.button(w=(240 / 2), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[1]))

    elif layout_config == "right3":
        # 2*2
        row1 = cmds.rowLayout(p=RC, nc=2)

        col1 = cmds.columnLayout(p=row1)
        cmds.button(w=(240 / 2), h=135, p=col1, label="", command=partial(play_view_caller, make_default, child_array[0]))

        col2 = cmds.columnLayout(p=row1)
        cmds.button(w=(240 / 2), h=(130 / 2), p=col2, label="", command=partial(play_view_caller, make_default, child_array[1]))
        cmds.separator(h=5, style='none')
        cmds.button(w=(240 / 2), h=(130 / 2), p=col2, label="", command=partial(play_view_caller, make_default, child_array[2]))

    elif layout_config == "horizontal4":
        # 1*4
        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 4), label="", command=partial(play_view_caller, make_default, child_array[0]))

        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 4), label="", command=partial(play_view_caller, make_default, child_array[1]))

        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 4), label="", command=partial(play_view_caller, make_default, child_array[2]))

        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 4), label="", command=partial(play_view_caller, make_default, child_array[3]))

    elif layout_config == "vertical4":
        # 4*1
        cmds.rowLayout(parent=RC, nc=4)
        cmds.button(w=(240 / 4), h=135, label="", command=partial(play_view_caller, make_default, child_array[0]))
        cmds.button(w=(240 / 4), h=135, label="", command=partial(play_view_caller, make_default, child_array[1]))
        cmds.button(w=(240 / 4), h=135, label="", command=partial(play_view_caller, make_default, child_array[2]))
        cmds.button(w=(240 / 4), h=135, label="", command=partial(play_view_caller, make_default, child_array[3]))

    elif layout_config == "top4":
        # 3*2
        cmds.rowLayout(parent=RC, nc=3)
        cmds.button(w=(240 / 3), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[0]))
        cmds.button(w=(240 / 3), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[1]))
        cmds.button(w=(240 / 3), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[2]))

        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[3]))

    elif layout_config == "left4":
        # 2*3
        row1 = cmds.rowLayout(p=RC, nc=2)

        col1 = cmds.columnLayout(p=row1)
        cmds.button(w=(240 / 2), h=(135 / 3) - 3, p=col1, label="", command=partial(play_view_caller, make_default, child_array[0]))
        cmds.separator(h=4, style='none')
        cmds.button(w=(240 / 2), h=(135 / 3) - 3, p=col1, label="", command=partial(play_view_caller, make_default, child_array[3]))
        cmds.separator(h=4, style='none')
        cmds.button(w=(240 / 2), h=(135 / 3) - 3, p=col1, label="", command=partial(play_view_caller, make_default, child_array[2]))

        col2 = cmds.columnLayout(p=row1)
        cmds.button(w=(240 / 2), h=135, p=col2, label="", command=partial(play_view_caller, make_default, child_array[1]))

    elif layout_config == "bottom4":
        # 3*2
        cmds.rowLayout(parent=RC, nc=1)
        cmds.button(w=240, h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[0]))

        cmds.rowLayout(parent=RC, nc=3)
        cmds.button(w=(240 / 3), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[3]))
        cmds.button(w=(240 / 3), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[2]))
        cmds.button(w=(240 / 3), h=(135 / 2), label="", command=partial(play_view_caller, make_default, child_array[1]))

    elif layout_config == "right4":
        # 2*3
        row1 = cmds.rowLayout(p=RC, nc=2)

        col1 = cmds.columnLayout(p=row1)
        cmds.button(w=(240 / 2), h=135, p=col1, label="", command=partial(play_view_caller, make_default, child_array[0]))

        col2 = cmds.columnLayout(p=row1)
        cmds.button(w=(240 / 2), h=(135 / 3) - 3, p=col2, label="", command=partial(play_view_caller, make_default, child_array[1]))
        cmds.separator(h=4, style='none')
        cmds.button(w=(240 / 2), h=(135 / 3) - 3, p=col2, label="", command=partial(play_view_caller, make_default, child_array[2]))
        cmds.separator(h=4, style='none')
        cmds.button(w=(240 / 2), h=(135 / 3) - 3, p=col2, label="", command=partial(play_view_caller, make_default, child_array[3]))

    cmds.rowLayout(parent=RC, nc=1)
    cmds.separator(h=5, style='none')

    return RC


def help_call(*args):
    """Open a text window with help information."""
    helpText = (
        "PlayView: Always play a specific viewport.\n"
        "\n"
        "Cancel: Close PlayView without setting defaults or playback.\n"
        "Make Default: Save selected viewport to prevent future prompts.\n"
        "Select a viewport with the provided buttons. One PlayView \n"
        "window will pop up for each window with a viewport in it.\n"
        "\n"
        "(c) Jeffrey 'italic' Hoover\n"
        "italic DOT rendezvous AT gmail DOT com\n"
        "\n"
        "Licensed under the Apache 2.0 license.\n"
        "This script can be used for non-commercial\n"
        "and commercial projects free of charge.\n"
        "For more information, visit:\n"
        "https://www.apache.org/licenses/LICENSE-2.0\n"
    )

    if cmds.window(helpID, exists=True):
        cmds.deleteUI(helpID)

    cmds.window(
        helpID,
        title='PlayViewHelp',
        widthHeight=[300, 200],
        sizeable=True,
        resizeToFitChildren=True
    )
    cmds.columnLayout(width=300)
    cmds.scrollField(
        wordWrap=True,
        text=helpText,
        editable=False,
        width=300,
        height=200,
        font='smallPlainLabelFont'
    )

    cmds.showWindow()


def draw_PlayView(pWindowTitle, *args):
    ctrl_set = set()
    wInd = 0
    WH = (-75, -125)  # Window dimensions are 250*150, negated for addition

    for panel in cmds.getPanel(vis=True):
        try:
            ctrl = cmds.modelPanel(panel, q=True, control=True)
            ctrl_set.add(get_layout_control(ctrl))

            log.debug("Panel: {}".format(ctrl))
            log.debug("Control: {}".format(ctrl_set))
        except:
            pass

    for parent in ctrl_set:
        for w in get_windows():
            if parent.startswith(w):
                WC = get_window_center(w)
                TLC = [sum(x) for x in zip(WC, WH)]

                log.debug("Window center: {}".format(WC))
                log.debug("Top-left corner: {}".format(TLC))

                gui(parent, pWindowTitle, "{}{}".format(windowID, wInd), TLC)

                log.debug("Window: {}{}".format(windowID, wInd))
                log.debug("Control: {}".format(parent))

                wInd += 1


def get_windows(*args):
    """Get all available windows."""
    return cmds.lsUI(windows=True)


def get_window_center(window, *args):
    """Get window's center position."""
    WH = [l // 2 for l in cmds.window(window, q=True, wh=True)]
    WH.reverse()
    TLC = cmds.window(window, q=True, tlc=True)
    return [sum(x) for x in zip(TLC, WH)]


def get_layout_control(ctrl, *args):
    """Get layout's control."""
    return "|".join(ctrl.split("|")[:-1])


def get_layout_config(ctrl, *args):
    """Get layout's configuration."""
    return cmds.paneLayout(ctrl, q=True, configuration=True)


def get_layout_child_array(ctrl, *args):
    """Get layout's child array."""
    return cmds.paneLayout(ctrl, q=True, childArray=True)


def destroy_window(*args):
    """If PlayView windows exist, destroy them."""
    for w in get_windows():
        if w.startswith(windowID):
            cmds.deleteUI(w)
    if cmds.window(helpID, exists=True):
        cmds.deleteUI(helpID)


def prefs_play_all(*args):
    """Check user prefs for viewport playback type."""
    return cmds.playbackOptions(q=True, v=True) == "active"


def init(*args):
    """Funtion to call to start the script."""
    destroy_window()
    if cmds.play(q=True, state=True) is True:
        play_button()
    else:
        if not prefs_play_all():
            play_button()
            log.info("Playback prefs set to update all viewports.")
        else:
            if custom_viewport == "":
                draw_PlayView('PlayView')
            else:
                play_view(custom_viewport)
