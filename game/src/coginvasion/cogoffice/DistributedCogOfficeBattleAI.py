"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file DistributedCogOfficeBattleAI.py
@author Brian Lach
@date December 15, 2015

"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.ClockDelta import globalClockDelta
from direct.fsm import ClassicFSM, State

from src.coginvasion.battle.DistributedBattleZoneAI import DistributedBattleZoneAI

from src.coginvasion.cog import SuitBank, Variant
from src.coginvasion.cog.SuitType import SuitType
from src.coginvasion.cog import CogBattleGlobals, SuitGlobals
from src.coginvasion.gags.GagType import GagType
from src.coginvasion.battle import BattleGlobals
from src.coginvasion.hood import ZoneUtil
from src.coginvasion.toon.ToonGlobals import GAG_START_EVENT

from .DistributedCogOfficeElevatorAI import DistributedCogOfficeElevatorAI
from .DistributedCogOfficeSuitAI import DistributedCogOfficeSuitAI
from .CogOfficeConstants import *
from .ElevatorConstants import *
import .SuitBuildingGlobals

import random

RIDE_ELEVATOR_TIME = 7.5
FACE_OFF_TIME = 8.5
VICTORY_TIME = 5.0

class DistributedCogOfficeBattleAI(DistributedBattleZoneAI):
    notify = directNotify.newCategory('DistributedCogOfficeBattleAI')
    UNIQUE_FLOORS = []

    battleType = BattleGlobals.BTOffice

    def __init__(self, air, numFloors, dept, hood, bldg, exteriorZoneId):
        DistributedBattleZoneAI.__init__(self, air)
        self.STOP_TRACKING_WHEN_DEAD = 0
        self.fsm = ClassicFSM.ClassicFSM('DistributedCogOfficeBattleAI', [State.State('off', self.enterOff, self.exitOff),
         State.State('floorIntermission', self.enterFloorIntermission, self.exitFloorIntermission),
         State.State('bldgComplete', self.enterBldgComplete, self.exitBldgComplete),
         State.State('battle', self.enterBattle, self.exitBattle),
         State.State('rideElevator', self.enterRideElevator, self.exitRideElevator),
         State.State('faceOff', self.enterFaceOff, self.exitFaceOff),
         State.State('victory', self.enterVictory, self.exitVictory)], 'off', 'off')
        self.fsm.enterInitialState()
        self.hood = hood
        self.bldg = bldg
        self.bldgDoId = self.bldg.doId
        self.exteriorZoneId = exteriorZoneId
        self.toonId2suitsTargeting = {}
        self.guardSuits = []
        self.roomsVisited = []
        self.numFloors = numFloors
        self.currentFloor = 0
        self.tauntSuitId = 0
        self.currentRoom = ""
        self.readyAvatars = []
        self.elevators = [None, None]
        self.entranceElevator = None
        self.exitElevator = None
        self.infoEntity = None
        self.dept = dept
        if dept == 'c':
            self.deptClass = Dept.BOSS
        elif dept == 'l':
            self.deptClass = Dept.LAW
        elif dept == 's':
            self.deptClass = Dept.SALES
        elif dept == 'm':
            self.deptClass = Dept.CASH
            
    def getInfoEntity(self):
        return self.infoEntity

    def setTauntSuitId(self, id):
        self.tauntSuitId = id

    def getTauntSuitId(self):
        return self.tauntSuitId

    def b_setTauntSuitId(self, id):
        self.sendUpdate('setTauntSuitId', [id])
        self.setTauntSuitId(id)

    def getExteriorZoneId(self):
        return self.exteriorZoneId

    def getBldgDoId(self):
        return self.bldgDoId

    # Sent by the client when they enter a certain floor section
    def enterSection(self, sectionIndex):
        # Get the guard suits associated with this section
        for guard in self.getGuardsBySection(sectionIndex):
            # Make sure this guard isn't already activated
            if not guard.isActivated():
                # Activate this guard!
                guard.activate()

    def handleAvatarLeave(self, avatar, reason):
        DistributedBattleZoneAI.handleAvatarLeave(self, avatar, reason)

        if hasattr(self, 'watchingAvatarIds') and len(self.watchingAvatarIds) == 0:
            self.resetEverything()
            self.bldg.elevator.b_setState('opening')

    def getDept(self):
        return self.dept

    def getNumFloors(self):
        return self.numFloors

    def enterOff(self):
        pass

    def exitOff(self):
        self.acceptEvents()
    
    def rewardSequenceComplete(self, timestamp):
        DistributedBattleZoneAI.rewardSequenceComplete(self, timestamp)
        self.stopTrackingAll()
        base.taskMgr.doMethodLater(0.1, self.victoryTask, self.uniqueName('victoryTask'), 
                                   extraArgs = [self.avReadyToContinue], appendTask = True)

    def enterVictory(self):
        DistributedBattleZoneAI.battleComplete(self)
        
        for avId in self.watchingAvatarIds:
            avatar = self.air.doId2do.get(avId)
            if avatar:
                # Let this avatar's quest manager know that they have defeated a cog building.
                avatar.questManager.cogBuildingDefeated(self.hood, self.deptClass, self.numFloors)

    def victoryTask(self, victorIds, task):
        while len(victorIds) < 4:
            victorIds.append(None)
        self.bldg.fsm.request('waitForVictors', [victorIds])
        return task.done

    def exitVictory(self):
        base.taskMgr.remove(self.uniqueName('victoryTask'))

    def enterFaceOff(self):
        base.taskMgr.doMethodLater(FACE_OFF_TIME, self.faceOffTask, self.uniqueName('faceOffTask'))

    def faceOffTask(self, task):
        self.b_setState('battle')

        # Activate all of the guards in section 0 (the first section).
        for guard in self.getGuardsBySection(0):
            guard.activate()

        return task.done

    def exitFaceOff(self):
        base.taskMgr.remove(self.uniqueName('faceOffTask'))

    def enterRideElevator(self):
        base.taskMgr.doMethodLater(RIDE_ELEVATOR_TIME, self.rideElevatorTask, self.uniqueName('rideElevatorTask'))

    def rideElevatorTask(self, task):
        suit = self.air.doId2do.get(self.tauntSuitId)
        taunts = SuitGlobals.FaceoffTaunts[suit.suitPlan.getName()]
        tauntIndex = taunts.index(random.choice(taunts))

        self.sendUpdate('doFaceoff', [tauntIndex, globalClockDelta.getRealNetworkTime()])

        self.setState('faceOff')

        return task.done

    def exitRideElevator(self):
        base.taskMgr.remove(self.uniqueName('rideElevatorTask'))

    def enterBattle(self):
        if self.elevators[0]:
            self.elevators[0].b_setState('closing')
        if self.elevators[1]:
            self.elevators[1].b_setState('closed')
            
        self.infoEntity.dispatch_OnFloorBegin()

    def exitBattle(self):
        pass

    def enterBldgComplete(self):
        self.enterFloorIntermission()

    def exitBldgComplete(self):
        pass

    def enterFloorIntermission(self):
        self.infoEntity.dispatch_OnFloorEnd()

        if self.elevators[1]:
            self.elevators[1].b_setState('opening')
        if self.elevators[0]:
            self.elevators[0].b_setState('closed')
        self.readyAvatars = []
        
    def pickAndStartFloor(self, floorIdx):
        """Picks and starts the next floor,
        or the floor index specified."""
            
        floors = numFloors2roomsVisited[self.numFloors]
        newFloor = floors[floorIdx]
        if newFloor == RANDOM_FLOOR:
            # Let's choose a random middle floor to go to!
            self.notify.debug("Choosing random floor")
            choices = []
            for floor in middleFloors:
                if not floor in self.roomsVisited:
                    self.notify.debug("Added floor to choices: " + floor)
                    choices.append(floor)
                else:
                    self.notify.debug("Room {0} already visited.".format(floor))
            if len(choices) == 0:
                self.notify.debug("No choices, choosing randomly from middleFloors.")
                # We haven't finished making all of the floors yet, go to one we have already been to.
                newFloor = random.choice(middleFloors)
            else:
                newFloor = random.choice(choices)
        self.notify.debug('Chose floor: ' + newFloor)
        self.startFloor(floorIdx, newFloor)

    def readyForNextFloor(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId in self.readyAvatars:
            self.readyAvatars.append(avId)
        if len(self.readyAvatars) == len(self.watchingAvatarIds):
            self.pickAndStartFloor(self.currentFloor + 1)

    def exitFloorIntermission(self):
        pass

    def setState(self, state):
        self.fsm.request(state)

    def d_setState(self, state):
        timestamp = globalClockDelta.getRealNetworkTime()
        self.sendUpdate('setState', [state, timestamp])

    def b_setState(self, state):
        self.d_setState(state)
        self.setState(state)

    def setAvatars(self, avIds):
        DistributedBattleZoneAI.d_setAvatars(self, avIds)
        DistributedBattleZoneAI.setAvatars(self, avIds)
        self.toonId2suitsTargeting = {avId: [] for avId in self.watchingAvatarIds}

    def b_setCurrentFloor(self, floor):
        self.sendUpdate('setCurrentFloor', [floor])
        self.currentFloor = floor

    def getCurrentFloor(self):
        return self.currentFloor

    def generate(self):
        DistributedBattleZoneAI.generate(self)

        import AIEntities
        from src.coginvasion.szboss import (InfoTimer, DistributedFuncDoorAI, DistributedTriggerAI)
        from src.coginvasion.battle import (DistributedHPBarrelAI, DistributedGagBarrelAI)
        self.bspLoader.linkServerEntityToClass("cogoffice_suitspawn",       AIEntities.SuitSpawn)
        self.bspLoader.linkServerEntityToClass("cogoffice_hangoutpoint",    AIEntities.SuitHangout)
        self.bspLoader.linkServerEntityToClass("cogoffice_elevator",        DistributedCogOfficeElevatorAI)
        self.bspLoader.linkServerEntityToClass("info_timer",                InfoTimer.InfoTimer)
        self.bspLoader.linkServerEntityToClass("func_door",                 DistributedFuncDoorAI.DistributedFuncDoorAI)
        self.bspLoader.linkServerEntityToClass("info_cogoffice_floor",      AIEntities.InfoCogOfficeFloor)
        self.bspLoader.linkServerEntityToClass("item_gagbarrel",            DistributedGagBarrelAI.DistributedGagBarrelAI)
        self.bspLoader.linkServerEntityToClass("item_laffbarrel",           DistributedHPBarrelAI.DistributedHPBarrelAI)

    def cleanupGuardSuits(self):
        for suit in self.guardSuits:
            suit.requestDelete()
        self.guardSuits = []

    def cleanupElevators(self):
        self.elevators = [None, None]

    def resetEverything(self):
        DistributedBattleZoneAI.resetStats(self)
        self.currentFloor = 0
        self.toonId2suitsTargeting = {}
        self.spotTaken2suitId = {}
        self.cleanupGuardSuits()
        self.resetPhysics()
        self.ignoreEvents()
        self.unloadBSPLevel()
        self.readyAvatars = []
        for elevator in self.elevators:
            if elevator:
                elevator.b_setState('closed')
        self.b_setState('off')

    def delete(self):
        self.fsm.requestFinalState()
        self.fsm = None
        self.infoEntity = None
        self.currentFloor = None
        self.toonId2suitsTargeting = None
        self.spotTaken2suitId = None
        self.cleanupGuardSuits()
        self.guardSuits = None
        self.readyAvatars = None
        self.cleanupElevators()
        self.elevators = None
        self.entanceElevator = None
        self.exitElevator = None
        self.hood = None
        self.numFloors = None
        self.dept = None
        self.deptClass = None
        self.bldg = None
        self.bldgDoId = None
        self.exteriorZoneId = None
        self.availableBattlePoints = None
        DistributedBattleZoneAI.delete(self)

    def suitHPAtZero(self, doId):
        foundIt = False
        section = 0
        for suit in self.guardSuits:
            if suit.doId == doId:
                section = suit.floorSection
                foundIt = True
                break
                
        numInSection = len(self.getGuardsBySection(section, excludeIfZeroHP = 1))
        if numInSection == 0:
            self.infoEntity.dispatch_OnCogGroupDead(section)

    def deadSuit(self, doId):
        foundIt = False
        section = 0
        for suit in self.guardSuits:
            if suit.doId == doId:
                section = suit.floorSection
                self.guardSuits.remove(suit)
                foundIt = True
                break

        if len(self.guardSuits) == 0:
            if self.currentFloor < self.numFloors - 1:
                self.b_setState('floorIntermission')
            else:
                self.b_setState('victory')

    def getHoodIndex(self):
        return CogBattleGlobals.hi2hi[self.hood]

    def makeSuit(self, spawnData, hangoutData, isChair, boss = False):
        bldgInfo = SuitBuildingGlobals.buildingInfo[self.hood]
        if self.currentFloor < self.numFloors - 1:
            levelRange = bldgInfo[SuitBuildingGlobals.LEVEL_RANGE]
        else:
            levelRange = bldgInfo[SuitBuildingGlobals.BOSS_LEVEL_RANGE]
        battlePoint = None
        level, availableSuits = SuitBank.chooseLevelAndGetAvailableSuits(levelRange, self.deptClass, boss)

        plan = random.choice(availableSuits)
        suit = DistributedCogOfficeSuitAI(self.air, self, spawnData, hangoutData, isChair, self.hood)
        suit.setBattleZone(self) 
        variant = Variant.NORMAL
        hood = self.hood
        if self.hood == ZoneUtil.ToontownCentral:
            hood = ZoneUtil.BattleTTC
        if CogBattleGlobals.hi2hi[hood] == CogBattleGlobals.WaiterHoodIndex:
            variant = Variant.WAITER
        suit.setLevel(level)
        suit.setSuit(plan, variant)
        suit.generateWithRequired(self.zoneId)
        suit.d_setHood(suit.hood)
        suit.battleZone = self
        
        suit.b_setPlace(self.zoneId)
        suit.b_setName(plan.getName())
        return suit

    def getGuardsBySection(self, sectionIndex, excludeIfZeroHP = 0):
        guards = []
        for guard in self.guardSuits:
            if guard.floorSection == sectionIndex:
                if not excludeIfZeroHP or (excludeIfZeroHP and not guard.isDead()):
                    guards.append(guard)
        return guards

    def startFloor(self, floorNum, room):
        # Clean up barrels and drops from the last floor.
        self.unloadBSPLevel()

        self.b_setCurrentFloor(floorNum)
        self.currentRoom = room
        if room not in self.roomsVisited:
            self.roomsVisited.append(room)

        # We need to wait for a response from all players telling us that they finished loading the floor.
        # Once they all finish loading the floor, we ride the elevator.
        self.readyAvatars = []
        # Load the BSP level for this floor.
        self.b_setMap(room)
        
        # Get the info entity
        infos = self.bspLoader.findAllEntities("info_cogoffice_floor")
        assert len(infos) > 0, "No info entity found in map!"
        assert len(infos) < 2, "More than one info entity found in map!"
        self.infoEntity = infos[0]

        # Make the Cogs for this floor.
        wantBoss = (self.currentFloor == (self.numFloors - 1))
        sectionRange = SuitBuildingGlobals.buildingInfo[self.hood][SuitBuildingGlobals.GUARDS_PER_SECTION]
        guardSection2NumInSection = {}
        maxInThisSection = 0

        forceBoss = 0x1
        spawnImmediately = 0x2
        dontIgnore = 0x4
        noHangout = 0x8

        guard = None
        
        # look through all the spawn points
        spawns = self.bspLoader.findAllEntities("cogoffice_suitspawn")
        hangouts = self.bspLoader.findAllEntities("cogoffice_hangoutpoint")
        for spawn in spawns:
            
            spawnflags = spawn.getEntityValueInt("spawnflags")
            if not (spawnflags & spawnImmediately):
                # Doesn't want us to spawn a cog here upon level load.
                continue

            section = spawn.getEntityValueInt("section")
            pos = spawn.cEntity.getOrigin()
            hpr = spawn.cEntity.getAngles()
            
            isBoss = False
            if wantBoss or (spawnflags & forceBoss):
                isBoss = True
                wantBoss = False
        
            if not guardSection2NumInSection.has_key(section):
                guardSection2NumInSection[section] = 0
                if section == 0:
                    # Always make section 0 have 4 guards.
                    maxInThisSection = 4
                else:
                    maxInThisSection = random.randint(sectionRange[0], sectionRange[1])

            if guardSection2NumInSection[section] < maxInThisSection:

                hangoutData = [False, None, None]
                if section == 0 and not (spawnflags & noHangout):
                    if len(hangouts):
                        hangout = random.choice(hangouts)
                        hangoutData = [True, hangout.cEntity.getOrigin(), hangout.cEntity.getAngles()]
                        hangouts.remove(hangout)

                suit = self.makeSuit([section, (pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])], hangoutData, 0, isBoss)
                self.guardSuits.append(suit)
                guardSection2NumInSection[section] += 1
                
        # Pick the suit that gives the taunt
        guards = list(self.getGuardsBySection(0))
        guards.sort(key = lambda guard: guard.getLevel(), reverse = True)
        guard = guards[0]

        self.b_setTauntSuitId(guard.doId)

        self.elevators = [None, None]
        elevs = self.bspLoader.findAllEntities("cogoffice_elevator")
        for elev in elevs:
            self.elevators[elev.getEntityValueInt("index")] = elev

    # Sent by the player telling us that they have finished loading/setting up the floor.
    def loadedMap(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId in self.readyAvatars:
            self.readyAvatars.append(avId)
        if len(self.readyAvatars) == len(self.watchingAvatarIds):
            # Let's ride!
            if self.elevators[0]:
                self.elevators[0].sendUpdate('putToonsInElevator')
            self.b_setState('rideElevator')

    def handleAvatarsReady(self):
        # We're ready to go!
        self.pickAndStartFloor(0)
