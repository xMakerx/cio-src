"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file DistributedBuilding.py
@author Brian Lach
@date December 13, 2015

"""

from panda3d.core import TextNode, Vec3, VBase4, Point3, DecalEffect, ShaderInput

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObject import DistributedObject
from direct.distributed.ClockDelta import globalClockDelta
from direct.distributed import DelayDelete
from direct.interval.IntervalGlobal import Sequence, Wait, Func, Parallel, LerpPosInterval
from direct.interval.IntervalGlobal import LerpScaleInterval, LerpFunctionInterval, LerpHprInterval
from direct.fsm import ClassicFSM, State
from direct.gui.DirectGui import DirectLabel

from src.coginvasion.globals import CIGlobals
from src.coginvasion.cog import Dept
from src.coginvasion.hood import ZoneUtil
from src.coginvasion.base.Precache import Precacheable, precacheModel
from src.coginvasion.battle import BattleGlobals

from src.coginvasion.cogoffice.ElevatorConstants import *
from src.coginvasion.cogoffice.ElevatorUtils import *
from src.coginvasion.cogoffice.SuitBuildingGlobals import *

class DistributedBuilding(DistributedObject, Precacheable):
    notify = directNotify.newCategory('DistributedBuilding')

    SUIT_INIT_HEIGHT = 125
    TAKEOVER_SFX_PREFIX = 'phase_5/audio/sfx/'
    
    # for precaching
    ELEVATOR_MDL = 'phase_4/models/modules/elevator.bam'
    ICONS_MDL = 'phase_3/models/gui/cog_icons.bam'
    SIGN_MDL = 'phase_5/models/modules/suit_sign.bam'

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.suitDoorOrigin = None
        self.elevatorModel = None
        self.fsm = ClassicFSM.ClassicFSM('DistributedBuilding', [State.State('off', self.enterOff, self.exitOff),
         State.State('waitForVictors', self.enterWaitForVictors, self.exitWaitForVictors),
         State.State('becomingToon', self.enterBecomingToon, self.exitBecomingToon),
         State.State('toon', self.enterToon, self.exitToon),
         State.State('becomingSuit', self.enterBecomingSuit, self.exitBecomingSuit),
         State.State('suit', self.enterSuit, self.exitSuit)], 'off', 'off')
        self.fsm.enterInitialState()
        self.elevatorNodePath = None
        self.transitionTrack = None
        self.victorList = [0, 0, 0, 0]
        self.waitingMessage = None
        self.cogDropSound = None
        self.cogLandSound = None
        self.cogSettleSound = None
        self.cogWeakenSound = None
        self.toonGrowSound = None
        self.toonSettleSound = None
        self.leftDoor = None
        
        self.setLights = False
        
    @classmethod
    def doPrecache(cls):
        precacheModel(cls.ELEVATOR_MDL)
        precacheModel(cls.ICONS_MDL)
        precacheModel(cls.SIGN_MDL)

    def getDeptClassFromAbbr(self, abbr):
        if abbr == 's':
            return Dept.SALES
        elif abbr == 'l':
            return Dept.LAW
        elif abbr == 'c':
            return Dept.BOSS
        elif abbr == 'm':
            return Dept.CASH

    def generate(self):
        DistributedObject.generate(self)
        self.mode = 'toon'
        self.townTopLevel = self.cr.playGame.hood.loader.geom

    def disable(self):
        self.fsm.requestFinalState()
        del self.townTopLevel
        self.stopTransition()
        DistributedObject.disable(self)

    def delete(self):
        self.victorList = None
        if self.elevatorNodePath:
            base.disablePhysicsNodes(self.elevatorNodePath)
            self.elevatorNodePath.removeNode()
            del self.elevatorNodePath
            del self.elevatorModel
            if hasattr(self, 'cab'):
                del self.cab
            del self.leftDoor
            del self.rightDoor
        self.leftDoor = None
        del self.suitDoorOrigin
        self.cleanupSuitBuilding()
        self.unloadSfx()
        del self.fsm
        DistributedObject.delete(self)

    def setBlock(self, block, interiorZoneId):
        self.block = block
        self.interiorZoneId = interiorZoneId

    def setSuitData(self, suitDept, difficulty, numFloors):
        self.suitDept = suitDept
        self.difficulty = difficulty
        self.numFloors = numFloors

    def setState(self, state, timestamp):
        self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def getSuitElevatorNodePath(self):
        if self.mode != 'suit':
            self.setToSuit()
        return self.elevatorNodePath

    def getSuitDoorOrigin(self):
        if self.mode != 'suit':
            self.setToSuit()
        return self.suitDoorOrigin

    def setVictorList(self, victorList):
        self.victorList = victorList

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterWaitForVictors(self, ts):
        if self.mode != 'suit':
            self.setToSuit()
        victorCount = self.victorList.count(base.localAvatar.doId)
        if victorCount == 1:
            self.acceptOnce('insideVictorElevator', self.handleInsideVictorElevator)
            camera.reparentTo(render)
            camera.setPosHpr(self.elevatorNodePath, 0, -32.5, 9.4, 0, 348, 0)
            base.camLens.setMinFov(CIGlobals.DefaultCameraFov / (4./3.))
            anyOthers = 0
            for v in self.victorList:
                if v != 0 and v != base.localAvatar.doId:
                    anyOthers = 1

            if anyOthers:
                self.waitingMessage = DirectLabel(text = "Waiting for other players...", text_fg = VBase4(1, 1, 1, 1),
                                                  text_align = TextNode.ACenter, relief = None, pos = (0, 0, 0.35),
                                                  scale = 0.1, text_shadow = (0, 0, 0, 1))
        elif victorCount == 0:
            pass
        else:
            self.error('localToon is on the victorList %d times' % victorCount)
        closeDoors(self.leftDoor, self.rightDoor)
        for light in self.floorIndicator:
            if light != None:
                light.setColor(LIGHT_OFF_COLOR)

    def handleInsideVictorElevator(self):
        self.sendUpdate('setVictorReady', [])

    def exitWaitForVictors(self):
        self.ignore('insideVictorElevator')
        if self.waitingMessage != None:
            self.waitingMessage.destroy()
            self.waitingMessage = None

    def enterBecomingToon(self, ts):
        self.animToToon(ts)

    def exitBecomingToon(self):
        pass

    def enterToon(self, ts):
        self.setToToon()

    def exitToon(self):
        pass

    def enterBecomingSuit(self, ts):
        self.animToSuit(ts)

    def exitBecomingSuit(self):
        pass

    def enterSuit(self, ts):
        self.setToSuit()

    def exitSuit(self):
        pass

    def getNodePaths(self):
        nodePath = []
        npc = self.townTopLevel.findAllMatches('**/?b' + str(self.block) + ':*_DNARoot;+s')
        npc.addPathsFrom(self.townTopLevel.findAllMatches("**/toonBuildingsBlock" + str(self.block) + ";+s"))
        for i in range(npc.getNumPaths()):
            nodePath.append(npc.getPath(i))
        return nodePath

    def getElevatorModel(self):
        return self.elevatorModel

    def loadElevator(self, newNP):
        self.floorIndicator = [None, None, None, None, None]
        self.elevatorNodePath = hidden.attachNewNode('elevatorNodePath')
        self.elevatorModel = loader.loadModel(self.ELEVATOR_MDL)
        npc = self.elevatorModel.findAllMatches('**/floor_light_?;+s')
        for i in range(npc.getNumPaths()):
            np = npc.getPath(i)
            floor = int(np.getName()[-1:]) - 1
            self.floorIndicator[floor] = np
            if floor < self.numFloors:
                np.setColor(LIGHT_OFF_COLOR)
            else:
                np.hide()

        self.elevatorModel.reparentTo(self.elevatorNodePath)
        self.cab = self.elevatorModel.find('**/elevator')
        cogIcons = loader.loadModel(self.ICONS_MDL)
        dept = self.getDeptClassFromAbbr(self.suitDept)
        if dept == Dept.BOSS:
            corpIcon = cogIcons.find('**/CorpIcon').copyTo(self.cab)
        elif dept == Dept.SALES:
            corpIcon = cogIcons.find('**/SalesIcon').copyTo(self.cab)
        elif dept == Dept.LAW:
            corpIcon = cogIcons.find('**/LegalIcon').copyTo(self.cab)
        elif dept == Dept.CASH:
            corpIcon = cogIcons.find('**/MoneyIcon').copyTo(self.cab)
        corpIcon.setPos(0, 6.79, 6.8)
        corpIcon.setScale(3)
        corpIcon.setColor(dept.getMedallionColor())
        cogIcons.removeNode()
        self.leftDoor = self.elevatorModel.find('**/left-door')
        if self.leftDoor.isEmpty():
            self.leftDoor = self.elevatorModel.find('**/left_door')
        self.rightDoor = self.elevatorModel.find('**/right-door')
        if self.rightDoor.isEmpty():
            self.rightDoor = self.elevatorModel.find('**/right_door')
        self.suitDoorOrigin = newNP.find('**/*_door_origin')
        self.elevatorNodePath.reparentTo(self.suitDoorOrigin)
        base.createPhysicsNodes(self.elevatorNodePath)
        base.enablePhysicsNodes(self.elevatorNodePath)
        #self.elevatorNodePath.flattenStrong()
        self.normalizeElevator()

    def loadAnimToSuitSfx(self):
        if self.cogDropSound is None:
            self.cogDropSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'cogbldg_drop.ogg')
            self.cogLandSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'cogbldg_land.ogg')
            self.cogSettleSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'cogbldg_settle.ogg')
            self.openSfx = base.loadSfx('phase_5/audio/sfx/elevator_door_open.ogg')

    def loadAnimToToonSfx(self):
        if self.cogWeakenSound is None:
            self.cogWeakenSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'cogbldg_weaken.ogg')
            self.toonGrowSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'toonbldg_grow.ogg')
            self.toonSettleSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'toonbldg_settle.ogg')
            self.openSfx = base.loadSfx('phase_5/audio/sfx/elevator_door_open.ogg')

    def unloadSfx(self):
        if self.cogDropSound != None:
            self.cogDropSound = None
            self.cogLandSound = None
            self.cogSettleSound = None
            self.openSfx = None
        if self.cogWeakenSound != None:
            self.cogWeakenSound = None
            self.toonGrowSound = None
            self.toonSettleSound = None
            self.openSfx = None

    def _deleteTransitionTrack(self):
        if self.transitionTrack:
            DelayDelete.cleanupDelayDeletes(self.transitionTrack)
            self.transitionTrack = None

    def animToSuit(self, timeStamp):
        self.stopTransition()
        if self.mode != 'toon':
            self.setToToon()
        self.loadAnimToSuitSfx()
        sideBldgNodes = self.getNodePaths()
        nodePath = hidden.find(self.getSbSearchString())
        newNP = self.setupSuitBuilding(nodePath)
        if not self.leftDoor:
            return
        closeDoors(self.leftDoor, self.rightDoor)
        newNP.stash()
        sideBldgNodes.append(newNP)
        soundPlayed = 0
        tracks = Parallel(name = self.taskName('toSuitTrack'))
        for i in sideBldgNodes:
            name = i.getName()
            timeForDrop = TO_SUIT_BLDG_TIME * 0.85
            if name[0] == 's':
                showTrack = Sequence(name = self.taskName('ToSuitFlatsTrack') + '-' + str(sideBldgNodes.index(i)))
                initPos = Point3(0, 0, self.SUIT_INIT_HEIGHT) + i.getPos()
                showTrack.append(Func(i.setPos, initPos))
                showTrack.append(Func(i.unstash))
                showTrack.append(Func(base.enablePhysicsNodes, i))
                if i == sideBldgNodes[len(sideBldgNodes) - 1]:
                    showTrack.append(Func(self.normalizeElevator))
                if not soundPlayed:
                    showTrack.append(Func(base.playSfx, self.cogDropSound, 0, 1, None, 0.0))
                showTrack.append(LerpPosInterval(i, timeForDrop, i.getPos(), name = self.taskName('ToSuitAnim') + '-' + str(sideBldgNodes.index(i))))
                if not soundPlayed:
                    showTrack.append(Func(base.playSfx, self.cogLandSound, 0, 1, None, 0.0))
                showTrack.append(self.createBounceTrack(i, 2, 0.65, TO_SUIT_BLDG_TIME - timeForDrop, slowInitBounce = 1.0))
                if not soundPlayed:
                    showTrack.append(Func(base.playSfx, self.cogSettleSound, 0, 1, None, 0.0))
                tracks.append(showTrack)
                if not soundPlayed:
                    soundPlayed = 1
            elif name[0] == 't':
                hideTrack = Sequence(name = self.taskName('ToSuitToonFlatsTrack'))
                timeTillSquish = (self.SUIT_INIT_HEIGHT - 20.0) / self.SUIT_INIT_HEIGHT
                timeTillSquish *= timeForDrop
                hideTrack.append(LerpFunctionInterval(self.adjustColorScale, fromData = 1, toData = 0.25, duration = timeTillSquish, extraArgs = [i]))
                hideTrack.append(LerpScaleInterval(i, timeForDrop - timeTillSquish, Vec3(1, 1, 0.01)))
                hideTrack.append(Func(base.disablePhysicsNodes, i))
                hideTrack.append(Func(i.stash))
                hideTrack.append(Func(i.setScale, Vec3(1)))
                hideTrack.append(Func(i.clearColorScale))
                tracks.append(hideTrack)

        self.stopTransition()
        self._deleteTransitionTrack()
        self.transitionTrack = tracks
        self.transitionTrack.start(timeStamp)

    def setupSuitBuilding(self, nodePath):
        if nodePath.isEmpty():
            return
        dnaStore = self.cr.playGame.dnaStore
        level = int(self.difficulty / 2) + 1
        suitNP = dnaStore.findNode('suit_landmark_' + self.getDeptClassFromAbbr(self.suitDept).getClothingPrefix() + str(level))
        zoneId = dnaStore.getZoneFromBlockNumber(self.block)
        zoneId = ZoneUtil.getTrueZoneId(zoneId, self.interiorZoneId)
        newParentNP = base.cr.playGame.hood.loader.zoneDict[zoneId]
        suitBuildingNP = suitNP.copyTo(newParentNP)
        base.createPhysicsNodes(suitBuildingNP)
        buildingTitle = dnaStore.getTitleFromBlockNumber(self.block)
        if not buildingTitle:
            buildingTitle = "Cogs, Inc."
        else:
            buildingTitle += ", Inc."
        buildingTitle += "\n%s" % self.getDeptClassFromAbbr(self.suitDept).getName()
        textNode = TextNode('sign')
        textNode.setTextColor(1.0, 1.0, 1.0, 1.0)
        textNode.setFont(CIGlobals.getSuitFont())
        textNode.setAlign(TextNode.ACenter)
        textNode.setWordwrap(17.0)
        textNode.setText(buildingTitle)
        textHeight = textNode.getHeight()
        zScale = (textHeight + 2) / 3.0
        signOrigin = suitBuildingNP.find('**/sign_origin;+s')
        backgroundNP = loader.loadModel(self.SIGN_MDL)
        backgroundNP.reparentTo(signOrigin)
        backgroundNP.setPosHprScale(0.0, 0.0, textHeight * 0.8 / zScale, 0.0, 0.0, 0.0, 8.0, 8.0, 8.0 * zScale)
        #backgroundNP.node().setEffect(DecalEffect.make())
        signTextNodePath = backgroundNP.attachNewNode(textNode.generate())
        signTextNodePath.setPosHprScale(0.0, -0.02, -0.21 + textHeight * 0.1 / zScale, 0.0, 0.0, 0.0,  0.1, 0.1, 0.1 / zScale)
        signTextNodePath.setColor(1.0, 1.0, 1.0, 1.0)
        frontNP = suitBuildingNP.find('**/*_front/+GeomNode;+s')
        backgroundNP.wrtReparentTo(frontNP)
        frontNP.node().setEffect(DecalEffect.make())
        suitBuildingNP.setName('sb' + str(self.block) + ':_landmark__DNARoot')
        suitBuildingNP.setPosHprScale(nodePath, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        
        suitBuildingNP.flattenStrong()

        self.loadElevator(suitBuildingNP)
        
        #CIGlobals.replaceDecalEffectsWithDepthOffsetAttrib(suitBuildingNP)
        
        #CIGlobals.flattenModelNodes(suitBuildingNP)
        
        base.enablePhysicsNodes(suitBuildingNP)
        
        #suitBuildingNP.ls()
        
        return suitBuildingNP

    def cleanupSuitBuilding(self):
        if hasattr(self, 'floorIndicator'):
            del self.floorIndicator

    def adjustColorScale(self, scale, node):
        node.setColorScale(scale, scale, scale, 1)

    def animToToon(self, timeStamp):
        self.stopTransition()
        if self.mode != 'suit':
            self.setToSuit()
        self.loadAnimToToonSfx()
        suitSoundPlayed = 0
        toonSoundPlayed = 0
        bldgNodes = self.getNodePaths()
        tracks = Parallel()
        for i in bldgNodes:
            name = i.getName()
            if name[0] == 's':
                hideTrack = Sequence(name = self.taskName('ToToonSuitFlatsTrack'))
                landmark = name.find('_landmark_') != -1
                if not suitSoundPlayed:
                    hideTrack.append(Func(base.playSfx, self.cogWeakenSound, 0, 1, None, 0.0))
                hideTrack.append(self.createBounceTrack(i, 3, 1.2, TO_TOON_BLDG_TIME * 0.05, slowInitBounce = 0.0))
                hideTrack.append(self.createBounceTrack(i, 5, 0.8, TO_TOON_BLDG_TIME * 0.1, slowInitBounce = 0.0))
                hideTrack.append(self.createBounceTrack(i, 7, 1.2, TO_TOON_BLDG_TIME * 0.17, slowInitBounce = 0.0))
                hideTrack.append(self.createBounceTrack(i, 9, 1.2, TO_TOON_BLDG_TIME * 0.18, slowInitBounce = 0.0))
                realScale = i.getScale()
                hideTrack.append(LerpScaleInterval(i, TO_TOON_BLDG_TIME * 0.1, Vec3(realScale[0], realScale[1], 0.01)))
                hideTrack.append(Func(base.disablePhysicsNodes, i))
                if landmark:
                    hideTrack.append(Func(i.removeNode))
                else:
                    hideTrack.append(Func(i.stash))
                    hideTrack.append(Func(i.setScale, Vec3(1)))
                if not suitSoundPlayed:
                    suitSoundPlayed = 1
                tracks.append(hideTrack)
            elif name[0] == 't':
                hideTrack = Sequence(name = self.taskName('ToToonFlatsTrack'))
                hideTrack.append(Wait(TO_TOON_BLDG_TIME * 0.5))
                if not toonSoundPlayed:
                    hideTrack.append(Func(base.playSfx, self.toonGrowSound, 0, 1, None, 0.0))
                hideTrack.append(Func(i.unstash))
                hideTrack.append(Func(base.enablePhysicsNodes, i))
                hideTrack.append(Func(i.setScale, Vec3(1, 1, 0.01)))
                if not toonSoundPlayed:
                    hideTrack.append(Func(base.playSfx, self.toonSettleSound, 0, 1, None, 0.0))
                hideTrack.append(self.createBounceTrack(i, 11, 1.2, TO_TOON_BLDG_TIME * 0.5, slowInitBounce=4.0))
                tracks.append(hideTrack)
                if not toonSoundPlayed:
                    toonSoundPlayed = 1

        self.stopTransition()
        bldgMTrack = tracks
        localToonIsVictor = self.localToonIsVictor()
        if localToonIsVictor:
            base.localAvatar.loop('neutral')
            camTrack = self.walkOutCameraTrack()
        victoryRunTrack, delayDeletes = self.getVictoryRunTrack()
        trackName = self.taskName('toToonTrack')
        self._deleteTransitionTrack()
        if localToonIsVictor:
            freedomTrack1 = Func(self.cr.playGame.getPlace().fsm.request, 'walk')
            freedomTrack2 = Func(base.localAvatar.d_setParent, CIGlobals.SPRender)
            freedomTrack3 = Func(messenger.send, BattleGlobals.BATTLE_COMPLETE_EVENT)
            self.transitionTrack = Parallel(camTrack, Sequence(victoryRunTrack, bldgMTrack, freedomTrack1, freedomTrack2, freedomTrack3), name = trackName)
        else:
            self.transitionTrack = Sequence(victoryRunTrack, bldgMTrack, name = trackName)
        self.transitionTrack.delayDeletes = delayDeletes
        if localToonIsVictor:
            self.transitionTrack.start(0)
        else:
            self.transitionTrack.start(timeStamp)

    def walkOutCameraTrack(self):
        track = Sequence(Func(camera.reparentTo, render), Func(camera.setPosHpr, self.elevatorNodePath, 0, -32.5, 9.4, 0, 348, 0),
                         Func(base.camLens.setMinFov, CIGlobals.DefaultCameraFov / (4./3.)), Wait(VICTORY_RUN_TIME),
                         Func(camera.setPosHpr, self.elevatorNodePath, 0, -32.5, 17, 0, 347, 0),
                         Func(base.camLens.setMinFov, 75.0 / (4./3)), Wait(TO_TOON_BLDG_TIME),
                         Func(base.camLens.setMinFov, CIGlobals.DefaultCameraFov / (4./3.)))
        return track

    def plantVictorsOutsideBldg(self):
        retVal = 0
        for victor in self.victorList:
            if victor != 0 and victor in self.cr.doId2do:
                toon = self.cr.doId2do[victor]
                toon.setPosHpr(self.elevatorModel, 0, -10, 0, 0, 0, 0)
                toon.startSmooth()
                if victor == base.localAvatar.doId:
                    retVal = 1
                    self.cr.playGame.getPlace().fsm.request('walk')

        return retVal

    def getVictoryRunTrack(self):
        origPosTrack = Sequence()
        delayDeletes = []
        i = 0
        for victor in self.victorList:
            if victor != 0 and victor in self.cr.doId2do:
                toon = self.cr.doId2do[victor]
                delayDeletes.append(DelayDelete.DelayDelete(toon, 'getVictoryRunTrack'))
                toon.stopSmooth()
                toon.setParent(CIGlobals.SPHidden)
                origPosTrack.append(Func(toon.setPosHpr, self.elevatorNodePath,
                                    apply(Point3, ElevatorPoints[i]), Point3(180, 0, 0)))
                origPosTrack.append(Func(toon.setParent, CIGlobals.SPRender))
            i += 1

        openDoors = getOpenInterval(self, self.leftDoor, self.rightDoor, self.openSfx, None)
        toonDoorPosHpr = self.cr.playGame.dnaStore.getDoorPosHprFromBlockNumber(self.block)
        useFarExitPoints = toonDoorPosHpr.getPos(render).getZ() > 1.0
        runOutAll = Parallel()
        i = 0
        for victor in self.victorList:
            if victor != 0 and victor in self.cr.doId2do:
                toon = self.cr.doId2do[victor]
                p0 = Point3(0, 0, 0)
                p1 = Point3(ElevatorPoints[i][0], ElevatorPoints[i][1] - 5.0, ElevatorPoints[i][2])
                if useFarExitPoints:
                    p2 = Point3(ElevatorOutPointsFar[i][0], ElevatorOutPointsFar[i][1], ElevatorOutPointsFar[i][2])
                else:
                    p2 = Point3(ElevatorOutPoints[i][0], ElevatorOutPoints[i][1], ElevatorOutPoints[i][2])
                runOutSingle = Sequence(Func(toon.animFSM.request, 'run'),
                    LerpPosInterval(toon, TOON_VICTORY_EXIT_TIME * 0.25, p1, other = self.elevatorNodePath),
                    Func(toon.headsUp, self.elevatorNodePath, p2),
                    LerpPosInterval(toon, TOON_VICTORY_EXIT_TIME * 0.5, p2, other = self.elevatorNodePath),
                    LerpHprInterval(toon, TOON_VICTORY_EXIT_TIME * 0.25, Point3(0, 0, 0), other = self.elevatorNodePath),
                    Func(toon.animFSM.request, 'neutral'),
                    Func(toon.startSmooth))
                runOutAll.append(runOutSingle)
            i += 1

        victoryRunTrack = Sequence(origPosTrack, openDoors, runOutAll)
        return (victoryRunTrack, delayDeletes)

    def localToonIsVictor(self):
        retVal = 0
        for victor in self.victorList:
            if victor == base.localAvatar.doId:
                retVal = 1

        return retVal

    def createBounceTrack(self, nodeObj, numBounces, startScale, totalTime, slowInitBounce = 0.0):
        if not nodeObj or numBounces < 1 or startScale == 0.0 or totalTime == 0:
            self.notify.warning('createBounceTrack called with invalid parameter(s)')
            return
        result = Sequence()
        numBounces += 1
        if slowInitBounce:
            bounceTime = totalTime / (numBounces + slowInitBounce - 1.0)
        else:
            bounceTime = totalTime / float(numBounces)
        if slowInitBounce:
            currTime = bounceTime * float(slowInitBounce)
        else:
            currTime = bounceTime
        realScale = nodeObj.getScale()
        currScaleDiff = startScale - realScale[2]
        for currBounceScale in range(numBounces):
            if currBounceScale == numBounces - 1:
                currScale = realScale[2]
            elif currBounceScale % 2:
                currScale = realScale[2] - currScaleDiff
            else:
                currScale = realScale[2] + currScaleDiff
            result.append(LerpScaleInterval(nodeObj, currTime, Vec3(realScale[0], realScale[1], currScale),
                          blendType = 'easeInOut'))
            currScaleDiff *= 0.5
            currTime = bounceTime

        return result

    def stopTransition(self):
        if self.transitionTrack:
            self.transitionTrack.finish()
            self._deleteTransitionTrack()

    def setToSuit(self):
        self.stopTransition()
        if self.mode == 'suit':
            return
        self.mode = 'suit'
        nodes = self.getNodePaths()
        for i in nodes:
            name = i.getName()
            if name[0] == 's':
                if name.find('_landmark_') != -1:
                    base.disablePhysicsNodes(i)
                    i.removeNode()
                else:
                    base.enablePhysicsNodes(i)
                    i.unstash()
            elif name[0] == 't':
                for spl in i.findAllMatches("**/+Spotlight"):
                    render.clearLight(spl)
                base.disablePhysicsNodes(i)
                i.stash()
            elif name[0] == 'c':
                base.disablePhysicsNodes(i)
                if name.find('_landmark_') != -1:
                    i.removeNode()
                else:
                    i.stash()
        
        if self.setLights and hasattr(self.cr.playGame.hood.loader, 'lampLights'):
            blockLamps = self.cr.playGame.hood.loader.lampLights.get(int(self.block), [])
            for lamp in blockLamps:
                render.clearLight(lamp)
            self.setLights = False

        npc = hidden.findAllMatches(self.getSbSearchString())
        for i in range(npc.getNumPaths()):
            nodePath = npc.getPath(i)
            self.adjustSbNodepathScale(nodePath)
            self.setupSuitBuilding(nodePath)

    def setToToon(self):
        self.stopTransition()
        
        if not self.setLights and hasattr(self.cr.playGame.hood.loader, 'lampLights'):
            blockLamps = self.cr.playGame.hood.loader.lampLights.get(self.block, [])
            for lamp in blockLamps:
                render.setLight(lamp)
            self.setLights = True
        
        if self.mode == 'toon':
            return
        self.mode = 'toon'
        self.suitDoorOrigin = None
        nodes = self.getNodePaths()
        for i in nodes:
            i.clearColorScale()
            name = i.getName()
            if name[0] in ['s', 'c']:
                base.disablePhysicsNodes(i)
                if name.find('_landmark_') != -1:
                    for spl in i.findAllMatches("**/+Spotlight"):
                        render.clearLight(spl)
                    i.removeNode()
                else:
                    i.stash()
            elif name[0] == 't':
                for spl in i.findAllMatches("**/+Spotlight"):
                    render.setLight(spl)
                base.enablePhysicsNodes(i)
                i.unstash()

    def normalizeElevator(self):
        self.elevatorNodePath.setScale(render, Vec3(1, 1, 1))
        self.elevatorNodePath.setPosHpr(0, 0, 0, 0, 0, 0)

    def getSbSearchString(self):
        result = 'landmarkBlocks/sb' + str(self.block) + ':*_landmark_*_DNARoot'
        return result

    def adjustSbNodepathScale(self, nodePath):
        pass

    def getVisZoneId(self):
        exteriorZoneId = self.cr.playGame.dnaStore.getZoneFromBlockNumber(self.block)
        visZoneId = ZoneUtil.getTrueZoneId(exteriorZoneId, self.zoneId)
        return visZoneId
