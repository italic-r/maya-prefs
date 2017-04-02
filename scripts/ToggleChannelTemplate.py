# Original mel procedure to (un)template a channel in the graph editor
"""
global proc
doTemplateChannel(string $selectionConnection, int $newState)
{
    string $command;
    int $result = 0;

    string $membersArray[] = `keyframe -query -sl -name`;

    if (size($membersArray) == 0)
    {
        string $selConn[] = expandSelectionConnectionAsArray($selectionConnection);
        for ($sel in $selConn) {
            string $isPC[] = `ls -type animCurve $sel`;
            if (size($isPC)) {
                $membersArray[size($membersArray)] = $sel;
            } else {
                string $pc[] = `listConnections -type animCurve $sel`;
                if (size($pc) == 1) {
                    $membersArray[size($membersArray)] = $pc[0];
                }
            }
        }
    }

    for ($m in $membersArray) {
        setAttr -l $newState ($m+".ktv");
    }

    if (size($membersArray) == 0)
    {
        error( (uiRes("m_loadAnimMenuLibrary.kNoChannelsSelected")));
    }
}
"""
