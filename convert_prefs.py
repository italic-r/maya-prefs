#!/bin/python3
# encoding: utf-8
"""
Convert and copy Maya prefs between versions.

Use this script to convert existing 2016[.5] hotkeys, menus and shelves to
earlier versions of Maya. Cannot convert up to 2016[.5] at this time.
Requires Python 3.2+.
"""

"""
REGEX SYNTAX:
.               any character (except newline)
^               start of string
[^...]          exclusive match
$               end of string
*               >=0 of any character
+               >=1 of previous character
?               0|1 of previous character
*?, +?, ??      non-greedy *, +, ?
{m}             m copies of previous character
{m,n}           m-n range, copies of previous characters - requires comma, greedy (do not use whitespace)
{m,n}?          m-n range, copies of previous characters - requires comma, non-greedy (do not use whitespace)
\               escape
[]              character set
|               logical OR


\number         reference a numbered group ()
\A              match only at the start of the string
\b              empty string at beginning or end of word - backspace inside classes ([])
\B              empty string not at beginning or end of word
\d              any digit character
\D              any non-digit character
\s              any space character
\S              any non-space character
\w              any word character
\W              any non-word character
\Z              match at end of string
"""

import sys
import os
import shutil
import re
import glob

from pathlib import Path


def set_prefs_dir():
    repo = Path('.')
    prefs = 'prefs'

    verTupOld = (
        "2013-x64",
        "2014-x64",
        "2015-x64",
    )
    verTupNew = (
        "2016",
        "2016.5"
    )

    sourceVerInput = input(
        ">> 2013-x64\n"
        ">> 2014-x64\n"
        ">> 2015-x64\n"
        ">> 2016\n"
        ">> 2016.5\n"
        "Source: "
    )
    if sourceVerInput in verTupOld:
        destVerInput = input(
            ">> 2013-x64\n"
            ">> 2014-x64\n"
            ">> 2015-x64\n"
            "Destination: "
        )
    elif sourceVerInput in verTupNew:
        destVerInput = input(
            ">> 2013-x64\n"
            ">> 2014-x64\n"
            ">> 2015-x64\n"
            ">> 2016\n"
            ">> 2016.5\n"
            "Destination: "
        )
    else:
        sys.exit("Invalid input; exiting.")

    srcPath = repo / sourceVerInput / prefs
    destPath = repo / destVerInput / prefs

    return srcPath, destPath


def copy_prefs(source, dest):
    """
    Copy given sources to dest for conversion.

    TODO: Remove hard-coded hotkeys files for 2016+
    """
    # Source files
    if "2016" in str(source) or "2016.5" in str(source):
        userHotkeysSrc = source / 'hotkeys' / 'userHotkeys_JH_Anim.mel'
    else:
        userHotkeysSrc = source / 'userHotkeys.mel'
    namedCommandsSrc = source / 'userNamedCommands.mel'
    runtimeCommandSrc = source / 'userRunTimeCommands.mel'
    windowPrefsSrc = source / 'windowPrefs.mel'

    shelfdirSrc = source / 'shelves'
    markdirSrc = source / 'markingMenus'

    # Destination files
    if "2016" in str(dest) or "2016.5" in str(dest):
        userHotkeysDest = dest / 'hotkeys' / 'userHotkeys_JH_Anim.mel'
    else:
        userHotkeysDest = dest / 'userHotkeys.mel'
    namedCommandsDest = dest / 'userNamedCommands.mel'
    runtimeCommandDest = dest / 'userRunTimeCommands.mel'
    windowPrefsDest = dest / 'windowPrefs.mel'

    shelfdirDest = dest / 'shelves'
    markdirDest = dest / 'markingMenus'

    srcList = (userHotkeysSrc, namedCommandsSrc, runtimeCommandSrc, windowPrefsSrc)
    destList = (userHotkeysDest, namedCommandsDest, runtimeCommandDest, windowPrefsDest)

    srcDirList = (shelfdirSrc, markdirSrc)
    destDirList = (shelfdirDest, markdirDest)

    for src, dest in zip(srcList, destList):
        # print(src, dest)
        shutil.copy2(str(src), str(dest))

    for src, dest in zip(srcDirList, destDirList):
        shutil.rmtree(str(dest))
        shutil.copytree(str(src), str(dest))


def re_replace(source, dest):
    """Search/replace text within 'file' with 're' expression."""
    # Shelves
    shelfHighlightColor = r"^\s*-highlightColor.*$\n"
    shelfRotation = r"^\s*-rotation.*$\n"
    shelfFlipXY = r"^\s*-flip[XY].*$\n"
    shelfAlpha = r"^\s*-useAlpha.*$\n"
    shelfMenuItem = r"^\s*-menuItem.*$\n"
    shelfscaleIcon = r"^\s*-scaleIcon.*$\n"
    shelfPopup = r"^\s*-noDefaultPopup.*$\n"

    # Marking menu
    markLongDivider = r"^\s*-longDivider.*$\n"

    # Runtime command
    rtcCtx = r"^\s*-hotkeyCtx.*$\n"
    rtcHKEditor = r"^\s*-showInHotkeyEditor.*$\n"
    rtcHKPrefs = r"hotkeyEditorWindow"

    # Hotkey flags
    hkCtxC = r"^\s*-ctxClient.*$\n"
    hkDragPress = r"^\s*-dragPress.*$\n"
    hkKey = r"(\"\w\")(.*)( -sht)"
    hkSpecSht = r"(\"\S{2,6}\")(.*)( -sht)"
    hkSpec = r"(\"\S{2,6}\")(.*)"

    # Hotkey lines
    hkSet = r"^hotkeySet.*$\n"
    hkCtx = r"^hotkeyCtx.*$\n"

    ShelfList = (
        shelfHighlightColor,
        shelfRotation,
        shelfFlipXY,
        shelfAlpha,
        shelfMenuItem,
        shelfscaleIcon,
        shelfPopup
    )
    MarkingMenuList = (markLongDivider,)
    RuntimeCommandList = (rtcCtx, rtcHKEditor)
    HKeyFlagList = (hkCtxC, hkDragPress)
    HKeySpecList = (hkSpec, hkSpecSht)
    HKeyLineList = (hkSet, hkCtx)

    shelfGlob = dest.glob('shelves/*.mel')
    for shelfFile in shelfGlob:
        with shelfFile.open(mode='r', encoding='UTF-8') as f:
            reSearch = f.read()
            for regex in ShelfList:
                reSearch = re.sub(regex, r"", reSearch, flags=re.MULTILINE)
            f = shelfFile.open(mode='w', encoding='UTF-8')
            f.write(reSearch)

    markGlob = dest.glob('markingMenus/*.mel')
    for markFile in markGlob:
        with markFile.open(mode='r', encoding='UTF-8') as f:
            reSearch = f.read()
            for regex in MarkingMenuList:
                reSearch = re.sub(regex, r"", reSearch, flags=re.MULTILINE)
            f = markFile.open(mode='w', encoding='UTF-8')
            f.write(reSearch)

    rtcFile = dest / 'userRunTimeCommands.mel'
    with rtcFile.open(mode='r', encoding='UTF-8') as f:
        reSearch = f.read()
        reSearch = re.sub(
            rtcHKPrefs, r"HotkeyPreferencesWindow",
            reSearch, flags=re.MULTILINE
        )
        for regex in RuntimeCommandList:
            reSearch = re.sub(regex, r"", reSearch, flags=re.MULTILINE)
        f = rtcFile.open(mode='w', encoding='UTF-8')
        f.write(reSearch)

    hotkeyFile = dest / 'userHotkeys.mel'
    with hotkeyFile.open(mode='r', encoding='UTF-8') as f:
        reSearch = f.read()

        reSearch = re.sub(
            hkKey,
            lambda match: r"{}{}".format(
                match.group(1).upper(),
                match.group(2)
            ),
            reSearch, flags=re.MULTILINE
        )
        for regex in HKeySpecList:
            reSearch = re.sub(
                regex,
                lambda match: r"{}{}".format(
                    match.group(1).lower(),
                    match.group(2)
                ),
                reSearch, flags=re.MULTILINE
            )
        for regex in HKeyFlagList:
            reSearch = re.sub(regex, r"", reSearch, flags=re.MULTILINE)
        for regex in HKeyLineList:
            reSearch = re.sub(regex, r"", reSearch, flags=re.MULTILINE)

        f = hotkeyFile.open(mode='w', encoding='UTF-8')
        f.write(reSearch)


if __name__ == "__main__":
    source, dest = set_prefs_dir()
    print("\n", "Source: " + str(source), "\n", "Destination: " + str(dest), "\n")
    copy_prefs(source, dest)
    if "2016" in str(source) or "2016.5" in str(source):
        if "2013-x64" in str(dest) or "2014-x64" in str(dest) or "2015-x64" in str(dest):
            re_replace(source, dest)
