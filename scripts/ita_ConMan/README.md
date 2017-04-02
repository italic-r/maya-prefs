# ConMan
##### A tool to create and manage constraints for rigging and animation.

To Install
--
Put ita_ConMan directory into your maya scripts directory. The default
locations are:

| System | Location |
| ------ | ------ |
| Windows | C:\Users\\_user_\My Documents\maya\\_version_\prefs\scripts |
| Linux | ~/maya/_version_/prefs/scripts |
| Mac | /Users/_user_/Library/Preferences/Autodesk/maya/version |

Loading and Unloading
--
```python
# Load
import ita_ConMan
ita_ConMan.show()
```

```python
# Unload
import ita_ConMan
ita_ConMan._CMan.close()
ita_ConMan.unregister_cb()
```

Create Constraint
--
Supported constraint types:
* Parent
* Point
* Orient
* Scale

Constraints are created with the options given in the UI.


Switch targets
--
* "OFF" turns off all weights and blend attributes.
* "ON" turns on all weights and blend attributes.
* "SWITCH" activates the blend attribute, a single target and deactivates the rest.
* Maintain Visual Transforms: Update constraint offsets to maintain the object's world-space transforms.
* Key: Animate the switch across two frames (current and immediately previous).

Constraint data is saved in the scene file under `maya.cmds.fileInfo("CMan_data", q=True)`

Remove Constraints and Data
--

Remove a constraint from the scene with the trash icon.

__WARNING: THIS IS NOT UNDO-ABLE!__ Purge: Remove ALL data from the tool.


# License

(c) Jeffrey "italic" Hoover
italic DOT rendezvous AT gmail DOT com

Licensed under the Apache 2.0 license.
This script can be used for commercial
and non-commercial projects free of charge.
For more information, visit:
https://www.apache.org/licenses/LICENSE-2.0

Attribution not necessary, but greatly appreciated.
Submit [bug reports](https://github.com/Italic-/ita_tools/issues) and [pull requests](https://github.com/Italic-/ita_tools/pulls):

Enjoy!
