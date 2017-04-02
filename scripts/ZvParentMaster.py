'''
The MIT License (MIT)

Copyright (c) 2006-2013 Paolo Dominici

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

ZV Parent Master is an animation tool that helps you to animate objects in mutual contact or interaction with ease.

Usage:
import ZvParentMaster
ZvParentMaster.ZvParentMaster()
'''

__author__ = 'Paolo Dominici (paolodominici@gmail.com)'
__version__ = '1.3.1'
__date__ = '2013/09/30'
__copyright__ = 'Copyright (c) 2006-2013 Paolo Dominici'

from maya import cmds, mel
import os, sys, math

############################
## CUSTOMIZABLE CONSTANTS ##
############################

# On the first attachment ZVPM creates two groups above the control and one parent constraint node.
# You can customize their suffixes, just keep in mind your scene won't be compatible with other ZVPMs.
PARENT_HANDLE_SUFFIX = '_PH'
SNAP_GROUP_SUFFIX = '_SN'
PARENT_CONSTRAINT_SUFFIX = '_PC'

# If this constant is True ZVPM will not include the control suffix on ZVPM object names
# i.e. the snap group of leftfoot_CTRL will be named leftfoot_SN instead of leftfoot_CTRL_SN.
REMOVE_CONTROL_SUFFIX = False

# This constant is used only if REMOVE_CONTROL_SUFFIX = True.
CONTROL_SUFFIX = '_CTRL'

# The hierarchy of a referenced file is read-only so ZVPM cannot create its parent groups.
# However the root of a referenced file can be grouped, so you can use ZVPM on it.
# Set this constant to False in case you don't want a ref file root object to be used with ZVPM.
ALLOW_REFERENCE_ROOT = True


# Private constants
_isQt = not cmds.about(version=True).split()[0] in ['8.5', '2008', '2009', '2010']
_defaultSize = _isQt and (38, 208) or (52, 238)
_locSfx = '_TMPLOC'
_timeWinSfx = '_WIN'
_timeFormDiv = 10000
_timeFormSfx = '_TMFRM'
_labelSfx = ['_TMLB', '_ATLB']
_timelineHsvCols = [(55.0, 1.0, 1.0), (135.0, 1.0, 1.0), (190.0, 1.0, 1.0), (218.0, 0.85, 1.0), (276.0, 0.67, 1.0), (314.0, 0.65, 1.0), (0.0, 1.0, 1.0), (32.0, 0.8, 1.0), (32.0, 0.8, 0.75), (345.0, 1.0, 0.46)]

# You can place the zv folder either in icons or in the scripts folder
_pmpath = 'zv/parentmaster/'
try:
	_pmpath = os.path.join([s for s in sys.path if os.path.exists(os.path.join(s, _pmpath))][0], _pmpath)
except:
	pass

def _getObjName(obj):
	'''Restituisce il nome pulito senza percorso o namespace.'''
	
	idx = max(obj.rfind('|'), obj.rfind(':'))
	return obj[idx+1:]

def _getObjNameFromSnapGroup(snGrp):
	'''Restituisce il nome del controllo dallo snap group.'''
	
	if snGrp.endswith(SNAP_GROUP_SUFFIX):
		name = snGrp[:-len(SNAP_GROUP_SUFFIX)]
		if REMOVE_CONTROL_SUFFIX and cmds.ls(name + CONTROL_SUFFIX):
			name += CONTROL_SUFFIX
		return name
	return None

def _getParentHandle(obj):
	'''Restituisce il nome del parent handle.'''
	
	if REMOVE_CONTROL_SUFFIX and obj.endswith(CONTROL_SUFFIX):
		obj = obj[:-len(CONTROL_SUFFIX)]
	
	return obj + PARENT_HANDLE_SUFFIX

def _getSnapGroup(obj):
	'''Restituisce il nome dello snap group.'''
	
	if REMOVE_CONTROL_SUFFIX and obj.endswith(CONTROL_SUFFIX):
		obj = obj[:-len(CONTROL_SUFFIX)]
	
	return obj + SNAP_GROUP_SUFFIX

def _getParentConstraint(obj):
	'''Nome del parent constraint.'''
	
	if REMOVE_CONTROL_SUFFIX:
		return _getParentHandle(obj.replace(':', '_')) + PARENT_CONSTRAINT_SUFFIX
	else:
		return _getParentHandle(obj) + PARENT_CONSTRAINT_SUFFIX

def _getWorldLocation(obj):
	'''Restituisce due array: posizione e rotazione assoluta.'''
	
	return [cmds.xform(obj, q=True, rp=True, ws=True), cmds.xform(obj, q=True, ro=True, ws=True)]

def _setWorldLocation(obj, posRot):
	'''Setta posizione e rotazione secondo gli array specificati.'''
	
	pos = posRot[0]
	rot = posRot[1]
	objPiv = cmds.xform(obj, q=True, rp=True, ws=True)
	diff = (pos[0] - objPiv[0], pos[1] - objPiv[1], pos[2] - objPiv[2])
	cmds.xform(obj, t=diff, r=True, ws=True)
	cmds.xform(obj, ro=rot, a=True, ws=True)

def _getActiveAttachTarget(constrName):
	'''Restituisce il target attivo (quello con peso 1) per il constrain specificato.'''
	
	targets = cmds.parentConstraint(constrName, q=True, tl=True)
	activeTarget = None
	for i in range(len(targets)):
		if cmds.getAttr('%s.w%d' % (constrName, i)) == 1.0:
			activeTarget = targets[i]
			break
	return activeTarget

def _cleanCurves(animCurves):
	'''Pulisce le curve rimuovendo le chiavi superflue.'''
	
	tol = 0.0001
	for c in animCurves:
		keyCount = cmds.keyframe(c, query=True, keyframeCount=True)
		if keyCount == 0:
			continue
		# cancella le chiavi superflue intermedie
		if keyCount > 2:
			times = cmds.keyframe(c, query=True, index=(0, keyCount-1), timeChange=True)
			values = cmds.keyframe(c, query=True, index=(0, keyCount-1), valueChange=True)
			inTan = cmds.keyTangent(c, query=True, index=(0, keyCount-1), inAngle=True)
			outTan = cmds.keyTangent(c, query=True, index=(0, keyCount-1), outAngle=True)
			for i in range(1, keyCount-1):
				if math.fabs(values[i]-values[i-1]) < tol and math.fabs(values[i+1]-values[i]) < tol and math.fabs(inTan[i]-outTan[i-1]) < tol and math.fabs(inTan[i+1]-outTan[i]) < tol:
					cmds.cutKey(c, time=(times[i], times[i]))
		
		# ricalcola il numero di chiavi e pulisce le chiavi agli estremi
		keyCount = cmds.keyframe(c, query=True, keyframeCount=True)
		times = cmds.keyframe(c, query=True, index=(0, keyCount-1), timeChange=True)
		values = cmds.keyframe(c, query=True, index=(0, keyCount-1), valueChange=True)
		inTan = cmds.keyTangent(c, query=True, index=(0, keyCount-1), inAngle=True)
		outTan = cmds.keyTangent(c, query=True, index=(0, keyCount-1), outAngle=True)
		# piu' di due key rimanenti
		if keyCount > 2:
			if math.fabs(values[1]-values[0]) < tol and math.fabs(inTan[1]-outTan[0]) < tol:
				cmds.cutKey(c, time=(times[0], times[0]))
			if math.fabs(values[-1]-values[-2]) < tol and math.fabs(inTan[-1]-outTan[-2]) < tol:
				cmds.cutKey(c, time=(times[-1], times[-1]))
		# uno o due key rimanenti
		elif keyCount == 1 or (math.fabs(values[1]-values[0]) < tol and math.fabs(inTan[1]-outTan[0]) < tol):
			val = cmds.getAttr(c)		# debuggato
			cmds.cutKey(c)
			cmds.setAttr(c, val)

def _printParents(constrNames):
	'''Printa gli attuali parenti.'''
	
	sys.stdout.write('[%s]\n' % ', '.join([str(_getActiveAttachTarget(s)) for s in constrNames]))

def _setRootNamespace():
	if cmds.namespaceInfo(cur=True) != ':':
		cmds.namespace(set=':')

def _getCtrlsFromSelection(postfix):
	'''Validate selection, deve esistere un nodo con lo stesso nome + il postfix.'''
	
	# carica la selezione
	sel = cmds.ls(sl=True)
	# 8.5 issue
	if sel == None: sel = []
	ctrls = []
	# aggiungi i controlli con parent constraint alla lista
	for ctrl in sel:
		tmpCtrl = ctrl
		# se l'oggetto e' uno snapgroup restituisci il figlio
		ctrlFromSnGrp = _getObjNameFromSnapGroup(ctrl)
		if ctrlFromSnGrp:
			tmpCtrl = ctrlFromSnGrp
		
		if postfix == PARENT_HANDLE_SUFFIX:
			temp = _getParentHandle(tmpCtrl)
		elif postfix == SNAP_GROUP_SUFFIX:
			temp = _getSnapGroup(tmpCtrl)
		elif postfix == PARENT_CONSTRAINT_SUFFIX:
			temp = _getParentConstraint(tmpCtrl)
		else:
			temp = tmpCtrl
		
		temp = cmds.ls(temp)
		
		# se non presente nella lista aggiungilo
		if temp and not tmpCtrl in ctrls:
			ctrls.append(tmpCtrl)
	
	return (sel, ctrls)

def _getRigidBody(obj):
	'''Restituisce il nodo di rigidBody.'''
	
	try:
		return cmds.rigidBody(obj, q=True, n=True)
	except:
		return None

def _setRigidBodyState(rb, val):
	'''Se esiste ricava il nodo rigidBody e lo setta attivo o passivo.'''
	
	cmds.setAttr(rb + '.active', val)
	cmds.setKeyframe(rb + '.active')
	cmds.keyframe(rb + '.active', tds=True)

def _rbDetach(obj):
	'''Quando detacho diventa attivo.'''
	
	rb = _getRigidBody(obj)
	if rb:
		_setRigidBodyState(rb, 1)

def _rbAttach(obj):
	'''Quando attacho setto il rb passivo e setto le chiavi per la sua nuova posizione.'''
	
	rb = _getRigidBody(obj)
	if rb:
		wLoc = _getWorldLocation(obj)
		_setRigidBodyState(rb, 0)
		_setWorldLocation(obj, wLoc)
		_setWorldLocation(obj, wLoc)
		cmds.setKeyframe(obj, at=['translate', 'rotate'], ott='step')

		# cerca le curve d'animazione
		choices = cmds.listConnections(obj, s=True, d=False, t='choice')
		animCurves = cmds.listConnections(choices, s=True, d=False, t='animCurve')
		# setta le curve step
		cmds.keyTangent(animCurves, ott='step')

def _resetRigidBody(obj):
	'''Cancella le chiavi messe al rigid body.'''
	
	rb = _getRigidBody(obj)
	if rb:
		# cancella le chiavi attivo-passivo
		cmds.cutKey(rb, cl=True, at='act')
		cmds.setAttr(rb + '.act', 1)
		# cancella le chiavi di posizione per lo stato passivo
		try:
			choices = cmds.listConnections(obj, d=False, s=True, t='choice')
			animCurves = [cmds.listConnections(s + '.input[1]', d=False, s=True)[0] for s in choices]
			cmds.delete(animCurves)
		except:
			pass

def _createParentMaster(obj, translation=True, rotation=True):
	'''Crea i gruppi necessari per utilizzare il parent master.'''
	
	# creo il parent handle e lo snap group dell'oggetto (aventi stesso pivot)
	# un file referenziato genera eccezione
	if cmds.referenceQuery(obj, inr=True) and (not ALLOW_REFERENCE_ROOT or cmds.listRelatives(obj, p=True)):
		sys.stdout.write('Read-only hierarchy detected\n')
		msg = 'Are you working with referenced files?\n\nZVPM can\'t group "%s" because it\'s in a read-only hierarchy.\n\n\nDo the following:\n\n- Open the referenced file.\n- Select this object, right-click on "Attach objects" button and "Create parent groups".\n- Save the file.' % obj
		cmds.confirmDialog(title='Referenced file - ZV Parent Master', message=msg)
		return False
	
	piv = cmds.xform(obj, q=True, rp=True, ws=True)
	cmds.group(obj, n=_getSnapGroup(obj))
	cmds.xform(_getSnapGroup(obj), piv=piv, ws=True)
	ph = cmds.group(_getSnapGroup(obj), n=_getParentHandle(obj))
	cmds.xform(_getParentHandle(obj), piv=piv, ws=True)
	
	# locca gli attributi non diponibili e quelli non richiesti
	ts = set(['tx', 'ty', 'tz'])
	rs = set(['rx', 'ry', 'rz'])
	
	availAttrs = set(cmds.listAttr(obj, k=True, u=True, sn=True) or [])
	attrsToLock = (ts | rs) - availAttrs
	if not translation:
		attrsToLock |= ts
	if not rotation:
		attrsToLock |= rs
	
	for attr in attrsToLock:
		cmds.setAttr('%s.%s' % (ph, attr), lock=True)
	
	return True

def _fixThis(ctrl, timeRange):
	'''Fixa lo snap per questo controllo.'''
	
	constrName = _getParentConstraint(ctrl)
	# fixa il timerange corrente
	if timeRange:
		currentFrame = cmds.currentTime(q=True)
		allKeyTimes = list(set(cmds.keyframe(constrName, q=True, time=(cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True)), timeChange=True)))
		allKeyTimes.sort()
		for t in allKeyTimes:
			cmds.currentTime(t)
			_fixThis(ctrl, False)
		# ritorna al frame di prima
		cmds.currentTime(currentFrame)
	# fixa solo il frame corrente
	else:
		# se sono al primo frame o non ci sono keyframe in questo frame esci
		firstFrame = cmds.playbackOptions(q=True, ast=True)
		currentFrame = cmds.currentTime(q=True)
		if currentFrame == firstFrame or cmds.keyframe(constrName, q=True, time=(currentFrame, currentFrame), timeChange=True) == None:
			sys.stdout.write('Nothing to fix at frame %d\n' % currentFrame)
			return
		
		# target attivo
		activeTarget = _getActiveAttachTarget(constrName)
		
		# elimina le chiavi
		selectConstraintNodes(ctrl)
		cmds.cutKey(t=(currentFrame, currentFrame))
		
		# se rigid body rivaluta dal primo frame
		if _getRigidBody(ctrl):
			# dummy locator (faccio il bake su di lui e lo cancello)
			tempLoc = cmds.spaceLocator()[0]
			cmds.hide(tempLoc)
			# mi permette di riprodurre la simulazione dal primo frame fino a quello corrente
			cmds.bakeResults(tempLoc, at=['t'], sm=True, t=(firstFrame, currentFrame), dic=True, pok=True)
			cmds.delete(tempLoc)
		
		# rifai il parent (detach o attach)
		if not activeTarget:
			cmds.select(ctrl)
			detach()
		else:
			cmds.select([ctrl, activeTarget])
			attach()
		
		sys.stdout.write('Snap fixed at frame %d\n' % currentFrame)

def _bakeObj(obj):
	'''Bake animazione.'''
	
	constrName = _getParentConstraint(obj)
	constrExists = cmds.ls(constrName)
	
	# se il constraint non esiste o non contiene keyframe esci
	if not constrExists or cmds.keyframe(constrName, q=True, kc=True) == 0:
		sys.stdout.write('Nothing to bake\n')
		return
	
	# primo frame
	currentFrame = cmds.currentTime(q=True)
	firstFrame = cmds.playbackOptions(q=True, ast=True)
	cmds.currentTime(firstFrame)
	
	# salva come lastFrame l'ultimo frame d'animazione del constraint o dell'oggetto
	keyTimes = cmds.keyframe(obj, q=True, tc=True)
	if not keyTimes:
		keyTimes = cmds.keyframe(constrName, q=True, tc=True)
	else:
		keyTimes.extend(cmds.keyframe(constrName, q=True, tc=True))
	lastFrame = max(keyTimes)
	
	# se all'ultimo frame rimane attached oppure il corpo e' rigido allora usa animation end time
	if max(cmds.keyframe(constrName, q=True, ev=True, t=(lastFrame, lastFrame))) > 0.0 or _getRigidBody(obj):
		lastFrame = max(lastFrame, cmds.playbackOptions(q=True, aet=True))
	
	# crea il locator
	locatorName = obj + _locSfx
	_setRootNamespace()
	loc = cmds.spaceLocator(n=locatorName)[0]
	cmds.hide(loc)
	
	# trova il parent del gruppo PH
	parent = cmds.listRelatives(_getParentHandle(obj), p=True)
	if parent:
		cmds.parent([loc, parent[0]])
	
	# copia l'ordine degli assi
	cmds.setAttr(loc + '.rotateOrder', cmds.getAttr(obj + '.rotateOrder'))
	
	# copia matrice e pivot
	cmds.xform(loc, m=cmds.xform(obj, q=True, m=True, ws=True), ws=True)
	cmds.xform(loc, piv=cmds.xform(obj, q=True, rp=True, ws=True), ws=True)
	
	# costringi il locator
	constraint = cmds.parentConstraint(obj, loc, mo=True)[0]
	
	# fai il bake
	cmds.bakeResults(loc, at=['t', 'r'], sm=True, t=(firstFrame, lastFrame), dic=True, pok=True)
	
	# cancella il constraint
	cmds.delete(constraint)
	
	# ripristina il frame precedente
	cmds.currentTime(currentFrame)

def _applyBakedAnimation(obj):
	'''Connetti l'animazione del bake locator all'oggetto.'''
	
	# se il locator non e' stato creato (niente da bakare) esci
	locatorName = obj + _locSfx
	locList = cmds.ls(locatorName)
	if not locList:
		return
	loc = locList[0]
	
	# se esiste cancella il nodo rigidBody e il solver
	try:
		rb = _getRigidBody(obj)
		if rb:
			solver = cmds.listConnections(rb + '.generalForce', s=False)[0]
			cmds.delete(rb)
			# se il rigid solver non e' usato cancellalo
			if not cmds.listConnections(solver + '.generalForce', d=False):
				cmds.delete(solver)
	# se il nodo rigidBody e' referenziato allora disconnetti solamente i choice dagli attributi dell'oggetto
	except:
		for choice in cmds.listConnections(obj, d=False, s=True, t='choice'):
			cmds.disconnectAttr(choice + '.output', cmds.listConnections(choice + '.output', p=True)[0])
	
	# cancella eventuali chiavi nel nodo di trasformazione dell'oggetto
	cmds.cutKey(obj, at=['t', 'r'])
	
	# trova le curve d'animazione del locator
	animCurves = cmds.listConnections(loc, d=False, type='animCurve')
	
	# rinominale
	for animCurve in animCurves:
		cmds.rename(animCurve, obj + animCurve[len(locatorName):])
	
	# connetti le curve d'animazione all'oggetto
	attrs = cmds.listAttr([obj + '.t', obj + '.r'], u=True, s=True)
	if not attrs:
		return
	
	for attr in attrs:
		curveNameAttr = '%s_%s.output' % (obj, attr)
		cmds.connectAttr(curveNameAttr, '%s.%s' % (obj, attr))
	
	# pulisci le curve
	sys.stdout.write('Optimizing translation and rotation keys...\n')
	_cleanCurves(['%s.%s' % (obj, s) for s in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']])
	
	# cancella il locator
	cmds.delete(loc)

def _createParentConstraint(obj, target, constrName):
	'''Crea il parent constraint.'''
	
	ta = ('tx', 'ty', 'tz')
	ra = ('rx', 'ry', 'rz')
	
	# parent handle
	ph = _getParentHandle(obj)
	
	# valuta quali sono gli attributi che non vanno costretti
	availAttrs = cmds.listAttr(ph, k=True, u=True, sn=True) or []
	skipTranslate = [s[1] for s in ta if not s in availAttrs]
	skipRotate = [s[1] for s in ra if not s in availAttrs]
	
	# se tutte loccate lancia l'errore
	if len(skipTranslate) == 3 and len(skipRotate) == 3:
		raise Exception, 'The attributes of the selected object are locked'
	
	# crea il constraint
	_setRootNamespace()
	pc = cmds.parentConstraint(target, ph, mo=False, n=constrName, w=1, st=skipTranslate, sr=skipRotate)[0]
	
	# azzera la rest position
	cmds.setAttr('%s.restTranslate' % pc, 0.0, 0.0, 0.0)
	cmds.setAttr('%s.restRotate' % pc, 0.0, 0.0, 0.0)

def _addTarget(cns, target):
	'''Aggiungi un target al parent constraint.'''
	
	targetList = cmds.parentConstraint(cns, q=True, tl=True)
	count = len(targetList)
	cmds.addAttr(cns, sn='w%d' % count, ln='%sW%d' % (_getObjName(target), count), dv=1.0, min=0.0, at='double', k=True)
	cmds.setAttr('%s.w%d' % (cns, count), 0.0)
	
	cmds.connectAttr('%s.t' % target, '%s.tg[%d].tt' % (cns, count))
	cmds.connectAttr('%s.rp' % target, '%s.tg[%d].trp' % (cns, count))
	cmds.connectAttr('%s.rpt' % target, '%s.tg[%d].trt' % (cns, count))
	cmds.connectAttr('%s.r' % target, '%s.tg[%d].tr' % (cns, count))
	cmds.connectAttr('%s.ro' % target, '%s.tg[%d].tro' % (cns, count))
	cmds.connectAttr('%s.s' % target, '%s.tg[%d].ts' % (cns, count))
	cmds.connectAttr('%s.pm' % target, '%s.tg[%d].tpm' % (cns, count))
	
	# connetti il peso
	cmds.connectAttr('%s.w%d' % (cns, count), '%s.tg[%d].tw' % (cns, count))

def createParentGroups(translation=True, rotation=True):
	'''Funzione popup per la preparazione dei controlli nel file reference.'''
	
	# carica la selezione
	ctrls = cmds.ls(sl=True)
	
	# se non ci sono elementi selezionati esci
	if not ctrls:
		raise Exception, 'You must select one or more objects'
	
	counter = 0
	for ctrl in ctrls:
		# se l'oggetto non e' provvisto di parent handle e snap group creali
		temp = cmds.ls(_getParentHandle(ctrl))
		if not temp:
			# se l'oggetto e' referenziato interrompi il ciclo
			if not _createParentMaster(ctrl, translation, rotation):
				return
			counter += 1
	# alla fine riseleziona i controlli
	cmds.select(ctrls)
	
	# messaggio
	if counter == 1:
		singplur = ''
	else:
		singplur = 's'
	sys.stdout.write('Parent groups created for %d object%s\n' % (len(ctrls), singplur))

def attach():
	'''Parent constraint intelligente.'''
	
	# carica la selezione
	sel = cmds.ls(sl=True)
	if sel == None: sel = []
	sel = [s for s in sel if cmds.nodeType(s) == 'transform' or cmds.nodeType(s) == 'joint']		# nota: ls con filtro transforms non funziona bene (include i constraint)
	
	ctrls = []
	# elimina gli elementi che hanno un suffisso di ZVPM
	for s in sel:
		tmp = s
		objFromSnGrp = _getObjNameFromSnapGroup(s)
		if objFromSnGrp:
			tmp = objFromSnGrp
		if not tmp in ctrls:
			ctrls.append(tmp)
	
	# se sono selezionati meno di due elementi esci
	if len(ctrls) < 2:
		raise Exception, 'You must select one or more slave objects and a master object'
	
	target = ctrls.pop()
	
	currentFrame = cmds.currentTime(q=True)
	firstFrame = cmds.playbackOptions(q=True, ast=True)
	
	# si inizia!
	for ctrl in ctrls:
		# se l'oggetto non e' provvisto di parent handle e snap group creali
		temp = cmds.ls(_getParentHandle(ctrl))
		if not temp:
			# se l'oggetto e' referenziato interrompi il ciclo
			if not _createParentMaster(ctrl):
				return
		
		snapGroup = _getSnapGroup(ctrl)
		# memorizza la posizione dello snap group per poi fare lo snap sulla stessa
		ctrlWLoc = _getWorldLocation(snapGroup)
		# nome del constrain
		constrName = _getParentConstraint(ctrl)
		
		temp = cmds.ls(constrName)
		# se il parent constr esiste
		if temp:
			# se il target e' gia attivo esci
			if target == _getActiveAttachTarget(constrName):
				continue
			
			targetList = cmds.parentConstraint(constrName, q=True, tl=True)
			# azzera tutti i target
			for i in range(len(targetList)):
				cmds.setAttr('%s.w%d' % (constrName, i), 0.0)
				cmds.setKeyframe('%s.w%d' % (constrName, i), ott='step')
			
			# se il target non e' presente nel constrain allora aggiungilo
			if target not in targetList:
				_addTarget(constrName, target)
				# settalo a 0 nel primo fotogramma (dato che e' nuovo), non vale se sono nel primo frame
				if currentFrame > firstFrame:
					cmds.setKeyframe('%s.w%d' % (constrName, len(targetList)), ott='step', t=firstFrame, v=0.0)
			
			# settalo a 1 nel fotogramma corrente
			targetID = cmds.parentConstraint(constrName, q=True, tl=True).index(target)
			cmds.setAttr('%s.w%d' % (constrName, targetID), 1.0)
			cmds.setKeyframe('%s.w%d' % (constrName, targetID), ott='step')
			
			# snappa la posizione del controllo snap sulla posizione precedente e setta le chiavi del controllo snap
			_setWorldLocation(snapGroup, ctrlWLoc)
			cmds.setKeyframe(snapGroup, at=['translate', 'rotate'], ott='step')
		
		# se il constrain non esiste
		else:
			# crea il constrain e setta il keyframe
			_createParentConstraint(ctrl, target, constrName)
			cmds.setKeyframe(constrName, at='w0', ott='step')
			
			# snappa la posizione del controllo snap sulla posizione precedente e setta le chiavi del controllo snap
			_setWorldLocation(snapGroup, ctrlWLoc)
			cmds.setKeyframe(snapGroup, at=['translate', 'rotate'], ott='step')
			
			# settalo a 0 nel primo fotogramma (dato che e' nuovo), non vale se sono nel primo frame
			if currentFrame > firstFrame:
				cmds.setKeyframe(constrName, at='w0', ott='step', t=firstFrame, v=0.0)
				cmds.setKeyframe(snapGroup, at=['translate', 'rotate'], ott='step', t=firstFrame, v=0.0)
		
		# set keyframes to green
		cmds.keyframe([snapGroup, constrName], tds=True)
		# setta le curve step
		cmds.keyTangent([snapGroup, constrName], ott='step')
		
		# se e' un rigid body settalo passivo
		_rbAttach(ctrl)
		
		# aggiorna la timeline window
		pmScriptJobCmd(ctrl)
	
	# seleziona il target
	cmds.select(ctrls)
	# output
	sys.stdout.write(' '.join(ctrls) + ' attached to ' + target + '\n')

def detach():
	'''Detacha il parent constraint attivo.'''
	
	sel, ctrls = _getCtrlsFromSelection(PARENT_HANDLE_SUFFIX)
	
	# se non ho selezionato nessun controllo provvisto di ph esci
	if not ctrls:
		raise Exception, 'No valid objects selected'
	
	for ctrl in ctrls:
		snapGroup = _getSnapGroup(ctrl)
		# memorizza la posizione del controllo per poi fare lo snap sulla stessa
		ctrlWLoc = _getWorldLocation(snapGroup)
		# nome del constrain
		constrName = _getParentConstraint(ctrl)
		
		temp = cmds.ls(constrName)
		## se il parent constr esiste
		if temp:
			# se non ci sono target attivi esci
			if not _getActiveAttachTarget(constrName):
				continue
			
			targetList = cmds.parentConstraint(constrName, q=True, tl=True)
			# azzera tutti i target
			for i in range(len(targetList)):
				cmds.setAttr('%s.w%d' % (constrName, i), 0.0)
				cmds.setKeyframe('%s.w%d' % (constrName, i), ott='step')
			
			# snappa la posizione del controllo sulla posizione precedente e setta le chiavi del controllo
			_setWorldLocation(snapGroup, ctrlWLoc)
			cmds.setKeyframe(snapGroup, at=['translate', 'rotate'], ott='step')
			cmds.keyframe([snapGroup, constrName], tds=True)
			# setta le curve step
			cmds.keyTangent([snapGroup, constrName], ott='step')
			
			# se e' un rigid body settalo attivo da questo frame
			_rbDetach(ctrl)
			
			# aggiorna la timeline window
			pmScriptJobCmd(ctrl)
	
	# output
	sys.stdout.write(' '.join(ctrls) + ' detached\n')

def destroy():
	'''Cancella i parent constraint.'''
	
	sel, ctrls = _getCtrlsFromSelection(PARENT_HANDLE_SUFFIX)
	
	# se non ho selezionato nessun controllo provvisto di ph esci
	if not ctrls:
		raise Exception, 'No valid objects selected'
	
	# chiedi se fare bake o no
	result = cmds.confirmDialog(title='Destroy constraints', message='The constraints will be deleted.\nDo you want to revert to previous state or bake and keep animation?', button=['Revert', 'Bake', 'Cancel'], defaultButton='Revert', cancelButton='Cancel', dismissString='Cancel')
	if result == 'Cancel':
		return
	bake = result == 'Bake'
	
	for ctrl in ctrls:
		# nome del constrain
		constrName = _getParentConstraint(ctrl)
		
		temp = cmds.ls(_getSnapGroup(ctrl))
		## se il gruppo snap esiste
		if temp:
			temp = cmds.ls(constrName)
			## se il parent constr esiste (lo snap group puo' esistere anche senza parent constr... vedi la feature Create parent groups)
			if temp:
				# se necessario crea il locator e fai il bake
				if bake:
					_bakeObj(ctrl)
				targetList = cmds.parentConstraint(constrName, q=True, tl=True)
				# azzera tutti i target e cancella il constraint
				for i in range(len(targetList)):
					cmds.setAttr('%s.w%d' % (constrName, i), 0.0)
				cmds.delete(constrName)
				
			# cancella le chiavi del controllo snap
			cmds.cutKey(_getSnapGroup(ctrl), at=['translate', 'rotate'])
			# ripristino gli attributi del controllo snap a 0
			[cmds.setAttr('%s.%s' % (_getSnapGroup(ctrl), s), 0.0) for s in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']]
			
			# se possibile (cioe' se non referenziato) parento l'oggetto al genitore originario
			try:
				ctrlParent = cmds.pickWalk(_getParentHandle(ctrl), d='up')[0]
				if ctrlParent == _getParentHandle(ctrl):
					cmds.parent(ctrl, r=True, w=True)
				else:
					cmds.parent([ctrl, ctrlParent], r=True)
				# cancello il parent handle
				cmds.delete(_getParentHandle(ctrl))
			except:
				pass
			
			# resetta il rigid body
			_resetRigidBody(ctrl)
			if bake:
				_applyBakedAnimation(ctrl)
			
			# aggiorna la timeline window
			pmScriptJobCmd(ctrl)
	
	# seleziona i controlli
	cmds.select(ctrls)
	
	# output
	sys.stdout.write(' '.join(ctrls) + ' constraints destroyed\n')

def fixSnap(timeRange=False):
	'''Fixa lo snap.'''
	
	# carica la selezione
	sel, ctrls = _getCtrlsFromSelection(PARENT_CONSTRAINT_SUFFIX)
	
	# se non ho selezionato nessun controllo provvisto di ph esci
	if not ctrls:
		raise Exception, 'No valid objects selected'
	
	# esegui il fix per ogni oggetto
	for ctrl in ctrls:
		_fixThis(ctrl, timeRange)
	
	# ripristina la selezione
	cmds.select(sel)

def selectConstraintNodes(obj=None):
	'''Metodo per la selezione del controllo snap e del constraint.'''
	
	# se chiamo il metodo con l'argomento non leggere la selezione
	if obj:
		if type(obj) == type([]):
			sel = obj
		else:
			sel = [obj]
		ctrls = sel
	# leggi la selezione
	else:
		# carica la selezione
		sel, ctrls = _getCtrlsFromSelection(PARENT_HANDLE_SUFFIX)
		
		# se non ho selezionato nessun controllo provvisto di ph esci
		if not ctrls:
			raise Exception, 'No valid objects selected'
	
	# deseleziona tutto
	cmds.select(cl=True)
	for ctrl in ctrls:
		# nome del constrain
		constrName = _getParentConstraint(ctrl)
		
		temp = cmds.ls(constrName)
		# se il parent constr esiste
		if temp:
			cmds.select([_getSnapGroup(ctrl), constrName], add=True)
			# se inoltre esiste anche il nodo rigidbody
			rb = _getRigidBody(ctrl)
			if rb:
				try:
					# seleziona i nodi di animazione del rigidbody (compreso l'animazione active)
					choices = cmds.listConnections(ctrl, s=True, d=False, t='choice')
					animCurves = cmds.listConnections(choices, s=True, d=False, t='animCurve')
					animCurves.append(cmds.listConnections(rb + '.act', d=False)[0])
					cmds.select(animCurves, add=True)
				except:
					pass
	
	# se ho specificato l'argomento, non printare niente
	if obj:
		return
	
	# mostra a chi e' parentato
	sel = cmds.ls(sl=True)
	if not sel:
		sys.stdout.write(' '.join(ctrls) + ' not constrained\n')
	else:
		_printParents(cmds.ls(sel, type='parentConstraint'))

def navigate(direction):
	'''Go to next/prev constraint.'''
	
	sel, constrNames = _getCtrlsFromSelection(PARENT_CONSTRAINT_SUFFIX)
	if not constrNames: return
	
	constrNames = [_getParentConstraint(s) for s in constrNames]
	
	if direction > 0:
		currentFrame = cmds.currentTime(q=True)
		targetFrame = cmds.findKeyframe(constrNames, which='next', t=(currentFrame+0.01, currentFrame+0.01))
	else:
		targetFrame = cmds.findKeyframe(constrNames, which='previous')
	
	# spostati nella timeline
	cmds.currentTime(targetFrame)
	
	# visualizza gli oggetti a cui sono attaccati gli oggetti selezionati
	_printParents(constrNames)

def ZvParentMaster(posX=56, posY=180, width=_defaultSize[0], height=_defaultSize[1]):
	'''Main UI.'''
	
	winName = 'ZvParentMasterWin'
	if cmds.window(winName, exists=True):
		cmds.deleteUI(winName, window=True)
	
	cmds.window(winName, title='ZV', tlb=True)
	cmds.columnLayout(adj=True, rs=0, bgc=(0.3, 0.3, 0.3))
	
	#### PULSANTI ####
	cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=_pmpath + 'pm_attach.xpm', c='%s.attach()' % __name__, ann='Attach objects')
	cmds.popupMenu(mm=True)
	cmds.menuItem(l='Create parent groups - translation', c='%s.createParentGroups(True, False)' % __name__, rp='NE')
	cmds.menuItem(l='Create parent groups - available attrs', c='%s.createParentGroups()' % __name__, rp='E')
	cmds.menuItem(l='Create parent groups - rotation', c='%s.createParentGroups(False, True)' % __name__, rp='SE')
	cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=_pmpath + 'pm_detach.xpm', c='%s.detach()' % __name__, ann='Detach objects')
	cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=_pmpath + 'pm_destroy.xpm', c='%s.destroy()' % __name__, ann='Destroy constraints')
	cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=_pmpath + 'pm_fixsnap.xpm', c='%s.fixSnap()' % __name__, ann='Fix snap')
	cmds.popupMenu(mm=True)
	cmds.menuItem(l='Fix snaps in the active range', c='%s.fixSnap(True)' % __name__, rp='E')
	cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=_pmpath + 'pm_select.xpm', c='%s.selectConstraintNodes()' % __name__, ann='Select constraints and snap groups')
	cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=_pmpath + 'pm_timeline.xpm', c='%s.timeline()' % __name__, ann='Constraint timeline')
	cmds.popupMenu(mm=True)
	cmds.menuItem(l='<- Prev', c='%s.navigate(-1)' % __name__, rp='W')
	cmds.menuItem(l='Next ->', c='%s.navigate(1)' % __name__, rp='E')
	cmds.setParent('..')
	
	cmds.showWindow(winName)
	cmds.window(winName, edit=True, widthHeight=(width, height), topLeftCorner=(posY, posX))
	
	sys.stdout.write('ZV Parent Master %s          http://www.paolodominici.com          paolodominici@gmail.com\n' % __version__)


##
##################
##   TIMELINE   ##
##################
def timeline():
	'''Timeline UI.'''
	
	sel, objects = _getCtrlsFromSelection(PARENT_CONSTRAINT_SUFFIX)
	
	if not objects:
		raise Exception, 'No valid objects selected'
	
	posX = 150
	posY = 200
	width, height = _getTimelineWinSize()
	
	for obj in objects:
		winName = obj + _timeWinSfx
		if cmds.window(winName, exists=True):
			cmds.deleteUI(winName, window=True)
		
		cmds.window(winName, title=obj, tlb=True)
		
		mainForm = cmds.formLayout(nd=100, bgc=(0.3, 0.3, 0.3))
		
		# controlli del form
		frT = cmds.text(obj + _labelSfx[0], l='', al='center', w=50, bgc=(0.6, 0.6, 0.6))
		atT = cmds.text(obj + _labelSfx[1], l='', fn='boldLabelFont', bgc=(0.6, 0.6, 0.6))
		timeForm = cmds.formLayout(obj + _timeFormSfx, nd=_timeFormDiv, bgc=(0.3, 0.3, 0.3))
		
		# edita il form principale
		cmds.formLayout(mainForm, e=True, attachForm=[(timeForm, 'left', 0), (timeForm, 'top', 0), (timeForm, 'right', 0), (frT, 'left', 0), (frT, 'bottom', 0), (atT, 'right', 0), (atT, 'bottom', 0)], \
						attachControl=[(timeForm, 'bottom', 0, frT), (atT, 'left', 0, frT)])
		
		_refrTimeForm(obj)
		
		cmds.showWindow(winName)
		cmds.window(winName, edit=True, widthHeight=(width, height), topLeftCorner=(posY+height*objects.index(obj), posX))
		
		pmScriptJob(obj, winName)

def _refrTimeForm(obj):
	'''Aggiorna il form della timeline window.'''
	
	timeForm = obj + _timeFormSfx
	min = cmds.playbackOptions(q=True, min=True)
	max = cmds.playbackOptions(q=True, max=True)
	rng = max - min + 1.0
	currentFrame = cmds.currentTime(q=True)
	
	# rimuovi gli elementi del time form
	children = cmds.formLayout(timeForm, q=True, ca=True)
	if children:
		cmds.deleteUI(children)
	
	# rintraccia il nodo di parent
	pcNode = cmds.ls(_getParentConstraint(obj))
	if pcNode:
		pcNode = pcNode[0]
	else:
		# aggiorna le label
		cmds.text(obj + _labelSfx[0], e=True, l='%d' % currentFrame, w=50)
		cmds.text(obj + _labelSfx[1], e=True, l='')
		return
	
	# il main form e' il parent
	cmds.setParent(timeForm)
	
	# parametri per l'edit del form
	attachPositions = []
	attachForms = []
	
	# lista dei target
	targets = cmds.parentConstraint(pcNode, q=True, tl=True)
	for tid in range(len(targets)):
		times = cmds.keyframe('%s.w%d' % (pcNode, tid), q=True, tc=True)
		values = cmds.keyframe('%s.w%d' % (pcNode, tid), q=True, vc=True)
		
		# nessuna chiave, lista nulla e passa al successivo
		if not times:
			continue
		
		# indici dei tempi delle chiavi di attach/detach
		idxList = []
		check = True
		for v in range(len(values)):
			if values[v] == check:
				idxList.append(v)
				check = not check
		
		# deve funzionare anche se l'ultima chiave e' attached (quindi numero chiavi dispari)
		times.append(cmds.playbackOptions(q=True, aet=True)+1.0)
		
		# ogni elemento di attach times e' relativo ad un particolare target ed e' una lista di questo tipo [[3,10], [12, 20]]
		timeRanges = [times[idxList[i]:idxList[i]+2] for i in range(0, len(idxList), 2)]
		
		hsvCol = _getColor(tid)
		
		# aggiungi i nuovi controlli
		for timeRange in timeRanges:
			# normalizza il timeRange
			normRange = [_timeFormDiv*(_crop(tr, min, max+1) - min)/rng for tr in timeRange]
			
			# se l'elemento e' stato croppato dal timerange passa al successivo
			if normRange[0] == normRange[1]:
				continue
			
			control = cmds.canvas(hsvValue=hsvCol, w=1, h=1, ann='%s [%d, %d]' % (targets[tid], timeRange[0], timeRange[1]-1.0))
			for button in [1, 3]:
				cmds.popupMenu(mm=True, b=button)
				cmds.menuItem(l='[%s]' % targets[tid], c='cmds.select(\'%s\')' % targets[tid], rp='N')
				cmds.menuItem(l='Select child', c='cmds.select(\'%s\')' % obj, rp='S')
				cmds.menuItem(l='Fix snaps', c='cmds.select(\'%s\')\n%s.fixSnap(True)' % (obj, __name__), rp='E')
			
			attachForms.extend([(control, 'top', 0), (control, 'bottom', 0)])
			attachPositions.extend([(control, 'left', 0, normRange[0]), (control, 'right', 0, normRange[1])])
	
	# current frame
	if currentFrame >= min and currentFrame <= max:
		frameSize = _timeFormDiv/rng
		normCf = frameSize*(currentFrame - min)
		currentTarget = _getActiveAttachTarget(pcNode)
		if not currentTarget:
			hsvCol = (0.0, 0.0, 0.85)
		else:
			hsvCol = _getColor(targets.index(currentTarget), 0.15)
		cf = cmds.canvas(hsvValue=hsvCol, w=1, h=1)
		
		attachForms.extend([(cf, 'top', 0), (cf, 'bottom', 0)])
		attachPositions.extend([(cf, 'left', 0, normCf), (cf, 'right', 0, normCf+frameSize)])
	
	# setta i parametri del form
	cmds.formLayout(timeForm, e=True, attachForm=attachForms, attachPosition=attachPositions)
	
	# aggiorna le label
	cmds.text(obj + _labelSfx[0], e=True, l='%d' % currentFrame, w=50)
	cmds.text(obj + _labelSfx[1], e=True, l='[%s]' % _getActiveAttachTarget(pcNode))

def pmScriptJob(obj, parent):
	mel.eval('python("from maya import cmds")')
	jobNums = []
	jobNums.append(mel.eval("scriptJob -p \"%s\" -e \"timeChanged\" \"python(\\\"%s.pmScriptJobCmd(\\\'%s\\\')\\\")\"" % (parent, __name__, obj)))
	jobNums.append(mel.eval("scriptJob -p \"%s\" -e \"playbackRangeChanged\" \"python(\\\"%s.pmScriptJobCmd(\\\'%s\\\')\\\")\"" % (parent, __name__, obj)))
	jobNums.append(mel.eval("scriptJob -p \"%s\" -e \"playbackRangeSliderChanged\" \"python(\\\"%s.pmScriptJobCmd(\\\'%s\\\')\\\")\"" % (parent, __name__, obj)))
	return jobNums

def pmScriptJobCmd(obj):
	if cmds.window(obj + _timeWinSfx, exists=True):
		_refrTimeForm(obj)

def _crop(val, minVal, maxVal):
	if val < minVal:
		return minVal
	elif val > maxVal:
		return maxVal
	else:
		return val

def _getColor(idx, sat=None):
	'''Restituisce il colore (in hsv) della barra della timeline per un dato indice. Ogni parente ha un colore diverso.'''
	
	hsvCol = _timelineHsvCols[idx % len(_timelineHsvCols)]
	if not sat:
		return hsvCol
	else:
		return (hsvCol[0], sat*hsvCol[1], hsvCol[2])

def _getTimelineWinSize():
	'''Dimensione finestra timeline a seconda se sono su qt o no.'''
	
	mayaVersion = cmds.about(version=True).split()[0]
	if _isQt:
		return (cmds.layout('MainTimeSliderLayout|formLayout9|frameLayout2', q=True, w=True)-17, 38)
	else:
		return ((cmds.control('MayaWindow|mayaMainWindowForm', q=True, w=True)-311), 70)
