# -*- coding: utf-8 -*-ch
'''
Created by: Dmitry Kryukov
website: www.linkedin.com/pub/dmitry-kryukov/86/5b7/7ba
email: dima.krukof@gmail.com
'''
import maya.cmds as cmds
import maya.mel as mel
#math
def linstep(fmin, fmax, x):
    """
    Returns a value from 0 to 1 that represents a parameters proportional distance between a minimum and maximum value.
    """
    if x < fmin:return 0
    if x > fmax:return 1
    if fmin == fmax:return 0
    return (x - fmin) / (fmax - fmin)

#attr
lock_attr = lambda node,b:[cmds.setAttr('%s.%s%s' %(node,a,aa),l=b) for a in 'trs' for aa in 'xyz']

connect_attr = lambda node_a,node_b:[cmds.connectAttr('%s.%s%s' %(node_a,a,aa),'%s.%s%s' %(node_b,a,aa)) for a in 'trs' for aa in 'xyz']

off_vis = lambda node:cmds.setAttr('%s.v' %node ,0,l=1)

#vector
length = lambda u :sum([a ** 2 for a in u]) ** 0.5
subtract = lambda u, v:[a - b for a, b in zip(u, v)]
#
def grouping(name):
	fastname = 'rigtools'
	def grp(cgrp,pgrp):
		if not cmds.objExists(cgrp):
			cmds.group(em=True,w=True,name=cgrp)
		if cmds.objExists(pgrp):
			prt = cmds.listRelatives(cgrp,p=True) or []
			if not pgrp in prt:
				cmds.parent(cgrp,pgrp)	
	
	basename = cmds.file(q=True,sn=True,shn=True)
	basename = basename.split('.')[0]
	
	base_gr = '%s_grp' %basename	
	rt_gr = '%s_grp' %fastname
	name_gr = '%s_grp#' %name
	c_gr = '%s_%s_grp#' %(name,'control')
	r_gr = '%s_%s_grp#' %(name,'rig')
	
	grp(rt_gr,base_gr)
	n_res = cmds.group(em=True,p=rt_gr,name=name_gr)
	c_res = cmds.group(em=True,p=n_res,name=c_gr)
	r_res = cmds.group(em=True,p=n_res,name=r_gr)
	cmds.setAttr('%s.v' %r_res ,0,l=1)
	return n_res,c_res,r_res 

#joints
def copy_joints(prefix,top):
    jts=cmds.ls(top,dag=1,type='joint')
    top2=cmds.duplicate(top,rc=1)[0]
    ef=cmds.ls(top2,dag=1,l=1,typ='ikEffector')
    if ef:cmds.delete(ef)
    jts2=cmds.ls(top2,dag=1,type='joint')
    res=[]
    for i,j in enumerate(jts):
        r=cmds.rename(jts2[i],'%s%s' %(prefix,j))
        res.append(r)
    return res

def chain(cu,num,name='joint'):
    """
    build a simple chain of joints equal to a defined length
    """
    cmds.select(cl=True)
    length=cmds.arclen(cu,ch=0)     
    jts=[];jts.append(cmds.joint(n='%s\#' %name,rad=1))    
    for j in range(num):
        rd = 1 - linstep(0., num+1, j+1)
        jtmp=cmds.joint(p=(length/num*(j+1),0, 0),rad=rd, n='%s\#' %name )
        jts.append(jtmp)        
    return jts

#curves
def get_curve():
    lls=cmds.listRelatives(s=1,f=1,type='nurbsCurve')
    res=cmds.listRelatives(lls,p=1,f=1)
    #test to see if user has selected curve components
    if not res:
        res=cmds.listRelatives(p=1,type='nurbsCurve')    
    res=list(set(res))
    return res


def chain_on_curve(name,num_j=12):
    curvs = get_curve()
    jt_grp = cmds.group(em=True,name='%s\#' %name)
    for cu in curvs:
        jts = chain(cu,num_j,'chain_joint')
        ikhnd=cmds.ikHandle(sj=jts[0], ee=jts[-1], c=cu, ccv=False, sol='ikSplineSolver',pcv=0)      
        cmds.parent(jts[0],jt_grp)
        cmds.delete(ikhnd)

# controls
def ctrl_cube(name='ctrl_cube',sz=1.,color=9):
    kv=range(16)
    pv=[[-0.5,0.5,0.5],[0.5,0.5,0.5],[0.5,0.5,-0.5],[-0.5,0.5,-0.5],
    [-0.5,0.5,0.5],[-0.5,-0.5,0.5],[-0.5,-0.5,-0.5],[0.5,-0.5,-0.5], 
    [0.5,-0.5,0.5],[-0.5,-0.5,0.5],[0.5,-0.5,0.5],[0.5,0.5,0.5], 
    [0.5,0.5,-0.5],[0.5,-0.5,-0.5],[-0.5,-0.5,-0.5],[-0.5,0.5,-0.5]]
    ctr=cmds.curve(d=1,p=pv,k=kv)
    ctr=cmds.rename(ctr,name)
    ctr_s=cmds.listRelatives(ctr,s=1)[0]
    cmds.setAttr("%s.overrideEnabled" %ctr_s,1)
    cmds.setAttr("%s.overrideColor" %ctr_s,color)
    cmds.setAttr('%s.v' %ctr,l=True,k=False)
    cmds.scale(sz,sz,sz,ctr)
    cmds.makeIdentity(ctr,apply=True,r=1,s=1)
    return ctr

def ctrl_sphere(name='ctrl_sphere',sz=1.,color=21):
	ctrl=cmds.createNode('transform', n='%s_#' %name)
	ctrl_sh=cmds.createNode('nurbsCurve', n='%sShape' %ctrl,p=ctrl)
	cmds.setAttr('%s.v' %ctrl_sh,k=False)
	cmds.setAttr('%s.ove' %ctrl_sh,1)
	cmds.setAttr('%s.ovc' %ctrl_sh,color)
	mel.eval('''setAttr ".cc" -type "nurbsCurve" 3 55 0 no 3
	60 
	0.05 0.05 0.05 0.06 0.08 0.10 0.11 0.13 0.15 0.16 0.18 0.19 0.21 0.23 0.24 0.26 0.27 0.29 0.31 0.32 0.34 0.35 0.37 0.39 0.40 0.42 0.44 0.45 0.47 0.48 
	0.50 0.52 0.53 0.55 0.56 0.58 0.60 0.61 0.63 0.65 0.66 0.68 0.69 0.71 0.73 0.74 0.76 0.77 0.79 0.81 0.82 0.84 0.85 0.87 0.89 0.90 0.92 0.94 0.94 0.94
	58
	0.00 -0.14 0.00 0.01 -0.12 0.06 -0.07 -0.12 0.06 -0.03 -0.14 -0.08 0.11 -0.11 -0.04 0.07 -0.11 0.12 -0.11 -0.10 0.09 -0.11 -0.12 -0.10 0.07 -0.11 -0.12 
	0.14 -0.09 0.03 0.04 -0.10 0.14 -0.12 -0.07 0.09 -0.14 -0.07 -0.04 -0.02 -0.10 -0.14 0.12 -0.07 -0.09 0.14 -0.06 0.06 0.03 -0.05 0.15 -0.11 -0.06 0.11 
	-0.15 -0.01 -0.02 -0.07 -0.07 -0.14 0.08 -0.05 -0.12 0.16 -0.04 -0.02 0.11 -0.02 0.12 -0.03 -0.03 0.16 -0.14 0.01 0.07 -0.15 -0.02 -0.07 -0.03 -0.02 -0.16 
	0.10 -0.01 -0.13 0.16 0.02 0.00 0.10 0.01 0.13 -0.04 0.03 0.15 -0.15 0.02 0.06 -0.14 0.02 -0.09 -0.02 0.02 -0.16 0.12 0.03 -0.11 0.16 0.04 0.03 0.07 0.06 
	0.14 -0.08 0.05 0.13 -0.16 0.05 0.01 -0.10 0.05 -0.13 0.05 0.05 -0.15 0.15 0.07 -0.04 0.11 0.08 0.10 -0.04 0.08 0.14 -0.14 0.08 0.03 -0.10 0.08 -0.11 0.06 
	0.08 -0.13 0.14 0.10 -0.01 0.04 0.11 0.12 -0.10 0.10 0.08 -0.11 0.10 -0.09 0.06 0.11 -0.11 0.11 0.12 0.04 -0.03 0.12 0.12 -0.10 0.13 -0.05 0.06 0.13 -0.11 
	0.08 0.13 0.01 0.00 0.15 0.00;''')
	cmds.scale(sz,sz,sz,ctrl)
	#cmds.rotate(90,0,0,ctrl)
	cmds.makeIdentity(ctrl,apply=True,r=1,s=1)
	return ctrl
#
def ctrl_sphere2(name='ctrl_sphere2',sz=1.,color=21):
	ctrl=cmds.createNode('transform', n='%s_#' %name)
	ctrl_sh=cmds.createNode('nurbsCurve', n='%sShape' %ctrl,p=ctrl)
	cmds.setAttr('%s.v' %ctrl_sh,k=False)
	cmds.setAttr('%s.ove' %ctrl_sh,1)
	cmds.setAttr('%s.ovc' %ctrl_sh,color)
	mel.eval('''setAttr ".cc" -type "nurbsCurve" 1 53 0 no 3
	54 
	0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22
	23 24 25 26 27 28 29 30 31 32 33 34
	35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53
	54
	0.00 0.81 0.00 -0.31 0.75 0.00 -0.57 0.57 0.00 -0.75 0.31 0.00 -0.81 0.00 0.00 -0.75 -0.31 0.00 -0.57 -0.57 0.00 -0.31 -0.75 0.00
	0.00 -0.81 0.00 0.31 -0.75 0.00 0.57 -0.57 0.00 0.75 -0.31 0.00 0.81 0.00 0.00 0.75 0.31 0.00 0.57 0.57 0.00 0.31 0.75 0.00
	0.00 0.81 0.00 0.00 0.75 0.31 0.00 0.57 0.57 0.00 0.31 0.75 0.00 0.00 0.81 0.00 -0.31 0.75 0.00 -0.57 0.57 0.00 -0.75 0.31
	0.00 -0.81 0.00 0.00 -0.75 -0.31 0.00 -0.57 -0.57 0.00 -0.31 -0.75 0.00 0.00 -0.81 0.00 0.31 -0.75 0.00 0.57 -0.57 0.00 0.75 -0.31
	0.00 0.81 0.00 -0.31 0.75 0.00 -0.57 0.57 0.00 -0.75 0.31 0.00 -0.81 0.00 0.00 -0.75 0.00 0.31 -0.57 0.00 0.57 -0.31 0.00 0.75 0.00
	0.00 0.81 0.31 0.00 0.75 0.57 0.00 0.57 0.75 0.00 0.31 0.81 0.00 0.00 0.75 0.00 -0.31 0.57 0.00 -0.57 0.31 0.00 -0.75 0.00
	0.00 -0.81 -0.31 0.00 -0.75 -0.57 0.00 -0.57 -0.75 0.00 -0.31 -0.81 0.00 0.00 -0.81 0.00 0.00;''')
	cmds.scale(sz,sz,sz,ctrl)
	cmds.makeIdentity(ctrl,apply=True,r=1,s=1)
	return ctrl

def onetenthNode(ctr,attr):		
		ucn = cmds.createNode('unitConversion',n='onetenthConversion')
		cmds.setAttr('%s.conversionFactor' %ucn, 0.1)
		cmds.connectAttr('%s.%s' %(ctr,attr), '%s.input' %ucn)
		return ucn

#follicle
def create_follicle(Nurbs, uPos=0.0, vPos=0.0,name='follice'):
    """
    Creates follicle (without hair system) on the surface in a certain position
    """
    Foll = cmds.createNode('follicle', name='%s#' %name)
    cmds.connectAttr('%s.local' %Nurbs, '%s.inputSurface' %Foll)
    cmds.connectAttr('%s.worldMatrix' %Nurbs, '%s.inputWorldMatrix' %Foll)
    FollTr = cmds.listRelatives(Foll,p=1)[0]

    cmds.connectAttr('%s.outTranslate' %Foll, '%s.translate' %FollTr)
    cmds.connectAttr('%s.outRotate' %Foll, '%s.rotate' %FollTr)
    cmds.setAttr('%s.translate' %FollTr,l=1)
    cmds.setAttr('%s.rotate' %FollTr,l=1)
    cmds.setAttr('%s.parameterU' %Foll,uPos)
    cmds.setAttr('%s.parameterV' %Foll,vPos)
    return Foll

#Put BlandShape or Cluster just before the skinCluster
def deformerBeforeSkin(top,bs):
	geoshape=cmds.ls(top,dag=1,g=1,ni=1)
	for g in geoshape:
		deform=cmds.listHistory(g,pdo=True,il=True)	
		sn=cmds.ls(deform,type='skinCluster')
		if sn:
			cmds.reorderDeformers(sn[0], bs, g)

def local_cluster_control2(cl):
		
	m_null=cmds.group(em=True,w=True,name='null_%s' %cl)
	m_ctr=ctrl_sphere2('second_ctrl#')
	
	tr=cmds.xform(cl,q=1,piv=1,ws=True)	[:3]
	cmds.xform(m_null,piv=(tr[0],tr[1],tr[2]))
	
	cmds.xform(m_ctr,ws=True,t=tr)
	cmds.makeIdentity(m_ctr,apply=1,t=1,r=1,s=1,n=0)
	connect_attr(m_ctr,m_null)
	cmds.parentConstraint(m_null, cl, mo=1)
	return m_ctr,m_null
