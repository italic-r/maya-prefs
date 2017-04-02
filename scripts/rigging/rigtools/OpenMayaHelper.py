# import the OpenMaya module
import maya.OpenMaya as OpenMaya

# function that returns a node object given a name
def nameToNode( name ):
 selectionList = OpenMaya.MSelectionList()
 selectionList.add( name )
 node = OpenMaya.MObject()
 selectionList.getDependNode( 0, node )
 return node

# function that returns a
def nameToDag( name ):
 selectionList = OpenMaya.MSelectionList()
 selectionList.add( name )
 dagPath = OpenMaya.MDagPath()
 selectionList.getDagPath(0, dagPath)
 return dagPath
 
# function that finds a plug given a node object and plug name
def nameToNodePlug( attrName, nodeObject ):
 depNodeFn = OpenMaya.MFnDependencyNode( nodeObject )
 attrObject = depNodeFn.attribute( attrName )
 plug = OpenMaya.MPlug( nodeObject, attrObject )
 return plug

# function that finds a paramater Nurbs curve for a given position
def getParametrCurve(cvName, pt):
    cpDag = nameToDag( cvName )
    wPoint = OpenMaya.MPoint(pt[0],pt[1],pt[2])
    # connect the MFnNurbsCurve
    # and ask the closest point
    nurbsCurveFn = OpenMaya.MFnNurbsCurve(cpDag)
    # get and set outPosition and min max Value
    outParam = OpenMaya.MScriptUtil()
    outParam.createFromDouble(0.0)
    outParamPtr = outParam.asDoublePtr()
    startTemp = OpenMaya.MScriptUtil()
    startTemp.createFromDouble(0.0)
    startPtr = startTemp.asDoublePtr()
    endTemp = OpenMaya.MScriptUtil()
    endTemp.createFromDouble(0.0)
    endPtr = endTemp.asDoublePtr() 
    
    nurbsCurveFn.getKnotDomain(startPtr, endPtr)
    outPosition = nurbsCurveFn.closestPoint(wPoint, True, outParamPtr ,0.001, OpenMaya.MSpace.kWorld)
    res = OpenMaya.MScriptUtil.getDouble(outParamPtr)/OpenMaya.MScriptUtil.getDouble(endPtr)
    
    return res
'''
# Find the persp camera node
print "Find the persp camera";
perspNode = nameToNode( "persp" )
print "APItype %d" % perspNode.apiType()
print "APItype string %s" % perspNode.apiTypeStr()
# Print the translateX value
translatePlug = nameToNodePlug( "translateX", perspNode )
print "Plug name: %s" % translatePlug.name()
print "Plug value %g" % translatePlug.asDouble()

perspDag = nameToDag( "persp" )
print "full path: %s" % perspDag.fullPathName()
print "APItype string: %s" % perspDag.node().apiTypeStr()
'''

