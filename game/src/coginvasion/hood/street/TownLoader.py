"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file TownLoader.py
@author Brian Lach
@date July 25, 2015

"""

from panda3d.core import ModelPool, TexturePool, NodePath, Vec4, DecalEffect, ModelNode

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm.StateData import StateData
from direct.fsm.State import State
from direct.fsm.ClassicFSM import ClassicFSM
from direct.interval.IntervalGlobal import Sequence, Func, LerpColorScaleInterval

from src.coginvasion.hood.QuietZoneState import QuietZoneState
from src.coginvasion.hood import LinkTunnel
from src.coginvasion.hood import ZoneUtil
from src.coginvasion.hood import ToonInterior
from src.coginvasion.cogoffice import CogOfficeInterior
from src.coginvasion.globals import CIGlobals
from src.coginvasion.phys import PhysicsUtils

class TownLoader(StateData):
    notify = directNotify.newCategory("TownLoader")

    def __init__(self, hood, parentFSMState, doneEvent):
        self.hood = hood
        self.parentFSMState = parentFSMState
        StateData.__init__(self, doneEvent)
        self.fsm = ClassicFSM('TownLoader', [State('start', self.enterStart, self.exitStart, ['quietZone', 'street', 'toonInterior']),
            State('street', self.enterStreet, self.exitStreet, ['quietZone']),
            State('toonInterior', self.enterToonInterior, self.exitToonInterior, ['quietZone']),
            State('suitInterior', self.enterSuitInterior, self.exitSuitInterior, ['quietZone']),
            State('quietZone', self.enterQuietZone, self.exitQuietZone, ['street', 'toonInterior', 'suitInterior']),
            State('final', self.enterFinal, self.exitFinal, ['start'])],
            'start', 'final')
        self.branchZone = None
        self.canonicalBranchZone = None
        self.placeDoneEvent = 'placeDone'
        self.streetSong = ''
        self.interiorSong = ''
        self.linkTunnels = []
        self.place = None
        return

    def findAndMakeLinkTunnels(self, requestStatus):
        for tunnel in self.geom.findAllMatches('**/*linktunnel*'):
            dnaRootStr = tunnel.getName()
            zone = LinkTunnel.getZoneFromDNARootStr(dnaRootStr)
            zone = LinkTunnel.maybeFixZone(zone)
            tunnelClass = LinkTunnel.getRecommendedTunnelClassFromZone(zone)
            link = tunnelClass(tunnel, dnaRootStr)
            self.linkTunnels.append(link)

    def load(self, zoneId):
        StateData.load(self)
        self.zoneId = zoneId
        self.branchZone = ZoneUtil.getBranchZone(zoneId)
        self.canonicalBranchZone = ZoneUtil.getCanonicalBranchZone(zoneId)

    def unload(self):
        self.parentFSMState.removeChild(self.fsm)
        del self.parentFSMState
        del self.fsm
        del self.streetClass
        base.disablePhysicsNodes(self.landmarkBlocks)
        self.landmarkBlocks.removeNode()
        del self.landmarkBlocks
        self.hood.dnaStore.resetSuitPoints()
        self.hood.dnaStore.resetBattleCells()
        del self.hood
        del self.nodeDict
        del self.zoneDict
        del self.fadeInDict
        del self.fadeOutDict
        del self.nodeList
        del self.zoneVisDict

        base.disablePhysicsNodes(self.geom)
        self.geom.removeNode()
        del self.geom
        del self.streetSong
        del self.interiorSong

        #CIGlobals.doSceneCleanup()

        StateData.unload(self)

    def enter(self, requestStatus):
        StateData.enter(self)
        self.findAndMakeLinkTunnels(requestStatus)
        self.fsm.enterInitialState()
        self.setState(requestStatus['where'], requestStatus)

    def exit(self):
        self.fsm.requestFinalState()
        self.ignoreAll()
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()
        StateData.exit(self)

    def setState(self, state, requestStatus):
        self.fsm.request(state, [requestStatus])

    def enterStart(self):
        pass

    def exitStart(self):
        pass

    def enterStreet(self, requestStatus):
        self.acceptOnce(self.placeDoneEvent, self.streetDone)
        self.place = self.streetClass(self, self.fsm, self.placeDoneEvent)
        self.place.load()

    def exitStreet(self):
        self.ignore(self.placeDoneEvent)
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)
        return

    def streetDone(self):
        self.requestStatus = self.place.doneStatus
        status = self.place.doneStatus
        if (status['loader'] == 'townLoader' and
        ZoneUtil.getBranchZone(status['zoneId']) == self.branchZone and
        status['shardId'] is None or
        status['how'] == 'doorOut' or status['where'] == 'suitInterior'):
            self.fsm.request('quietZone', [status])
        else:
            self.doneStatus = status
            messenger.send(self.doneEvent)

    def enterToonInterior(self, requestStatus):
        self.acceptOnce(self.placeDoneEvent, self.handleToonInteriorDone)
        self.place = ToonInterior.ToonInterior(self, self.fsm, self.placeDoneEvent)
        self.place.load()

    def exitToonInterior(self):
        self.ignore(self.placeDoneEvent)
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)
        return

    def enterSuitInterior(self, requestStatus):
        self.acceptOnce(self.placeDoneEvent, self.handleSuitInteriorDone)
        self.place = CogOfficeInterior.CogOfficeInterior(self, self.fsm, self.placeDoneEvent)
        self.place.load()

    def exitSuitInterior(self):
        self.ignore(self.placeDoneEvent)
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)

    def enterThePlace(self, requestStatus):
        base.cr.playGame.setPlace(self.place)
        if self.place is not None:
            self.place.enter(requestStatus)

    def handleToonInteriorDone(self):
        status = self.place.doneStatus
        if (status['loader'] == 'townLoader' and
        ZoneUtil.getBranchZone(status['zoneId']) == self.branchZone and
        status['shardId'] is None or
        status['how'] == 'doorOut'):
            self.fsm.request('quietZone', [status])
        else:
            self.doneStatus = status
            messenger.send(self.doneEvent)
        return

    def handleSuitInteriorDone(self):
        self.handleToonInteriorDone()

    def enterQuietZone(self, requestStatus):
        self.fsm.request(requestStatus['where'], [requestStatus], exitCurrent = 0)

        self.quietZoneDoneEvent = uniqueName('quietZoneDone')
        self.acceptOnce(self.quietZoneDoneEvent, self.handleQuietZoneDone)
        self.quietZoneStateData = QuietZoneState(self.quietZoneDoneEvent)
        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        self.ignore(self.quietZoneDoneEvent)
        del self.quietZoneDoneEvent
        self.quietZoneStateData.exit()
        self.quietZoneStateData.unload()
        self.quietZoneStateData = None
        return

    def handleQuietZoneDone(self):
        status = self.quietZoneStateData.getRequestStatus()
        self.exitQuietZone()
        self.enterThePlace(status)

    def enterFinal(self):
        pass

    def exitFinal(self):
        pass

    def createHood(self, dnaFile, loadStorage = 1, flattenNow = True):
        if loadStorage:
            loader.loadDNAFile(self.hood.dnaStore, 'phase_5/dna/storage_town.pdna')
            loader.loadDNAFile(self.hood.dnaStore, self.townStorageDNAFile)
        node = loader.loadDNAFile(self.hood.dnaStore, dnaFile)
        if node.getNumParents() == 1:
            self.geom = NodePath(node.getParent(0))
            self.geom.reparentTo(hidden)
        else:
            self.geom = hidden.attachNewNode(node)
        if flattenNow:
            self.doFlatten()
        self.geom.setName('town_top_level')

    def doFlatten(self):
        self.makeDictionaries(self.hood.dnaStore)
        self.reparentLandmarkBlockNodes()
        base.createPhysicsNodes(self.geom)
        self.renameFloorPolys(self.nodeList)
        self.geom.flattenLight()

        CIGlobals.preRenderScene(self.geom)

    def reparentLandmarkBlockNodes(self):
        bucket = self.landmarkBlocks = hidden.attachNewNode('landmarkBlocks')
        npc = self.geom.findAllMatches('**/sb*:*_landmark_*_DNARoot')
        for i in range(npc.getNumPaths()):
            nodePath = npc.getPath(i)
            nodePath.wrtReparentTo(bucket)

        npc = self.geom.findAllMatches('**/sb*:*animated_building*_DNARoot')
        for i in range(npc.getNumPaths()):
            nodePath = npc.getPath(i)
            nodePath.wrtReparentTo(bucket)

    def makeDictionaries(self, dnaStore):
        self.nodeDict = {}
        self.zoneDict = {}
        self.zoneVisDict = {}
        self.nodeList = []
        self.fadeInDict = {}
        self.fadeOutDict = {}
        a1 = Vec4(1, 1, 1, 1)
        a0 = Vec4(1, 1, 1, 0)
        numVisGroups = dnaStore.getNumDNAVisGroupsAI()
        for i in range(numVisGroups):
            groupFullName = dnaStore.getDNAVisGroupName(i)
            visGroup = dnaStore.getDNAVisGroupAI(i)
            groupName = base.cr.hoodMgr.extractGroupName(groupFullName)
            zoneId = int(groupName)
            zoneId = ZoneUtil.getTrueZoneId(zoneId, self.zoneId)
            groupNode = self.geom.find('**/' + groupFullName)
            if groupNode.isEmpty():
                continue
            else:
                if ':' in groupName:
                    groupName = '%s%s' % (zoneId, groupName[groupName.index(':'):])
                else:
                    groupName = '%s' % zoneId
                groupNode.setName(groupName)
                
            CIGlobals.replaceDecalEffectsWithDepthOffsetAttrib(groupNode)
            
            #group all the flat walls
            
            block2flatwall = {}
            flatwalls = groupNode.findAllMatches("**/tb*:*_DNARoot;+s")
            for flatwall in flatwalls:
                if "toon_landmark" in flatwall.getName():
                    print("Skipping", flatwall.getName())
                    continue
                if flatwall.hasTag("DNACode") and flatwall.hasMat():
                    continue
                block = int(flatwall.getName().split(":")[0][2:])
                if not block2flatwall.has_key(block):
                    block2flatwall[block] = groupNode.attachNewNode(ModelNode('toonBuildingsBlock' + str(block)))
                flatwall.wrtReparentTo(block2flatwall[block])
                
            for node in block2flatwall.values():
                for child in node.findAllMatches("**"):
                    child.clearEffect(DecalEffect.getClassType())
                    child.clearTag("DNACode")
                    child.clearTag("cam")
                CIGlobals.clearModelNodesBelow(node)
                node.flattenStrong()
            
            flattenGroup = groupNode.attachNewNode('optim')
            flattens = ['street*_DNARoot']
            removes = ['interactive_prop*_DNARoot']
            for remove in removes:
                for np in groupNode.findAllMatches("**/" + remove):
                    np.removeNode()
            for flatten in flattens:
                for np in groupNode.findAllMatches("**/" + flatten):
                    if np.hasTag("DNACode") and np.hasMat():
                        continue
                    for child in np.findAllMatches("**"):
                        child.clearEffect(DecalEffect.getClassType())
                        child.clearTag("DNACode")
                        child.clearTag("cam")
                    np.wrtReparentTo(flattenGroup)
            flattenGroup.clearModelNodes()
            flattenGroup.flattenStrong()
            
            CIGlobals.flattenModelNodes(groupNode)
            groupNode.flattenStrong()
            #groupNode.ls()
            
            self.nodeDict[zoneId] = []
            self.nodeList.append(groupNode)
            self.zoneDict[zoneId] = groupNode
            visibles = []
            for i in range(visGroup.getNumVisibles()):
                visibles.append(int(visGroup.get_visible(i)))
            visibles.append(ZoneUtil.getBranchZone(zoneId))
            self.zoneVisDict[zoneId] = visibles
            fadeDuration = 0.5
            self.fadeOutDict[groupNode] = Sequence(Func(groupNode.setTransparency, 1), LerpColorScaleInterval(groupNode, fadeDuration, a0, startColorScale=a1), Func(groupNode.clearColorScale), Func(groupNode.clearTransparency), Func(groupNode.stash), Func(base.disablePhysicsNodes, groupNode), name='fadeZone-' + str(zoneId), autoPause=1)
            self.fadeInDict[groupNode] = Sequence(Func(base.enablePhysicsNodes, groupNode), Func(groupNode.unstash), Func(groupNode.setTransparency, 1), LerpColorScaleInterval(groupNode, fadeDuration, a1, startColorScale=a0), Func(groupNode.clearColorScale), Func(groupNode.clearTransparency), name='fadeZone-' + str(zoneId), autoPause=1)

        for i in range(numVisGroups):
            groupFullName = dnaStore.getDNAVisGroupName(i)
            zoneId = int(base.cr.hoodMgr.extractGroupName(groupFullName))
            zoneId = ZoneUtil.getTrueZoneId(zoneId, self.zoneId)
            for j in range(dnaStore.getNumVisiblesInDNAVisGroup(i)):
                visName = dnaStore.getVisibleName(i, j)
                groupName = base.cr.hoodMgr.extractGroupName(visName)
                nextZoneId = int(groupName)
                nextZoneId = ZoneUtil.getTrueZoneId(nextZoneId, self.zoneId)
                visNode = self.zoneDict[nextZoneId]
                self.nodeDict[zoneId].append(visNode)

        self.hood.dnaStore.resetPlaceNodes()
        self.hood.dnaStore.resetDNAGroups()
        self.hood.dnaStore.resetDNAVisGroups()
        self.hood.dnaStore.resetDNAVisGroupsAI()

    def renameFloorPolys(self, nodeList):
        for i in nodeList:
            collNodePaths = i.findAllMatches('**/+BulletRigidBodyNode')
            numCollNodePaths = collNodePaths.getNumPaths()
            visGroupName = i.node().getName()
            for j in range(numCollNodePaths):
                collNodePath = collNodePaths.getPath(j)
                bitMask = collNodePath.node().getIntoCollideMask()
                if bitMask == CIGlobals.FloorGroup:
                    collNodePath.node().setName(visGroupName)
                    collNodePath.setCollideMask(CIGlobals.StreetVisGroup)
