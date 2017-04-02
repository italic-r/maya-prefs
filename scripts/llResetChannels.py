"""
Original MEL script by Lluis Llobera: lluisllobera@hotmail.com
Python version by Jeffrey "italic" Hoover: italic.rendezvous@gmail.com

import llResetChannels
llResetChannels.llResetChannels()
"""

import maya.cmds as cmds


def llResetChannels():
    selected = False
    selchan = cmds.channelBox(
        'mainChannelBox', q=True,
        sma=True, soa=True, ssa=True
    )
    if selchan is not None and len(selchan) > 0:
        selected = True

    for obj in cmds.ls(sl=True):
        if not selected:
            selchan = cmds.listAttr(obj, k=True)
        for chan in selchan:
            channame = "{}.{}".format(obj, chan)
            if cmds.objExists(channame) \
                    and cmds.getAttr(channame, k=True) \
                    and not cmds.getAttr(channame, l=True):
                default = cmds.attributeQuery(chan, n=obj, ld=True)
                cmds.setAttr(channame, default[0])
