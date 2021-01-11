"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file DistributedBRPond.py
@author Maverick Liberty
@date March 1, 2018
@desc Distributed version of the BRWater.py system that Brian Lach made a couple years ago.

"""

from direct.distributed.DistributedObject import DistributedObject
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.ClockDelta import globalClockDelta
from direct.interval.IntervalGlobal import Sequence, Func, Parallel, Wait
from direct.gui.DirectGui import DirectFrame, DirectWaitBar, OnscreenText

from src.coginvasion.toon import ToonEffects

from panda3d.core import WindowProperties
from random import choice
import itertools

class DistributedBRPond(DistributedObject):
    notify = directNotify.newCategory('DistributedBRPond')
    LowerPowerBarTaskName = 'BRWater-lowerPowerBar'
    WatchMouseMovementTaskName = 'BRWater-watchMouseMovement'
    WaterWatchTaskName = 'BRWater-waterWatch'
    InWaterZ = 0.93
    PowerLoss = 1
    
    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.freezeUpSfx = base.audio3d.loadSfx('phase_8/audio/sfx/freeze_up.ogg')
        self.freezeUpSfx.setVolume(12)

        self.frozenSfxArray = [
            base.audio3d.loadSfx('phase_8/audio/sfx/frozen_1.ogg'),
            base.audio3d.loadSfx('phase_8/audio/sfx/frozen_2.ogg'),
            base.audio3d.loadSfx('phase_8/audio/sfx/frozen_3.ogg')
        ]
        self.coolSfxArray = [
            base.audio3d.loadSfx('phase_8/audio/sfx/cool_down_1.ogg'),
            base.audio3d.loadSfx('phase_8/audio/sfx/cool_down_2.ogg')
        ]
        
        # Fancy code that will iterate through both lists and set their volume to 12.
        for sfx in itertools.chain(self.frozenSfxArray, self.coolSfxArray):
            sfx.setVolume(12)
        
        # A dictionary of avIds that point to a list of useful data.
        # Example: 0 : [iceCubeNode, interval]
        self.avId2Data = {}
        
        # Variables that store values for local stuff such as the GUI and the lastMouseX.
        self.frame = None
        self.powerBar = None
        self.label = None
        self.lastMouseX = 0
        
    def attachSoundToAvatar(self, avatar, sound):
        """ This is expecting a valid avatar object, either fetched from base.cr.doId2do#get() or passed directly """
        base.audio3d.attachSoundToObject(sound, avatar)
        base.playSfx(sound, node=avatar)
            
    def __resetAvatarIvalAndUnloadIceCube(self, avatar):
        """ This is expecting a valid avatar object, either fetched from base.cr.doId2do#get() or passed directly 
            This deletes the ice cube node, pauses the current interval, and deletes the data. """
        iceCube, ival = self.__fetchAvatarIntervalAndIceCube(avatar)
        
        if iceCube:
            iceCube.removeNode()
            iceCube = None
        
        if ival:
            ival.pause()
            ival = None
            
        if avatar.doId in self.avId2Data.keys():
            del self.avId2Data[avatar.doId]
            
    def __setAvatarIntervalAndIceCube(self, avatar, iceCube, ival, ts):
        """ This is expecting a valid avatar object, either fetched from base.cr.doId2do#get() or passed directly 
            NOTE: This starts the interval if one is passed! """
        if ival: ival.start(ts)
        self.avId2Data.update({avatar.doId : [iceCube, ival]})
        
    def __fetchAvatarIntervalAndIceCube(self, avatar):
        """ This is expecting a valid avatar object, either fetched from base.cr.doId2do#get() or passed directly 
            This returns the ice cube node and the current interval """
        
        # Let's default both of the data to None.
        data = [None, None]
        if avatar.doId in list(self.avId2Data.keys()):
            data = self.avId2Data.get(avatar.doId)
        return data[0], data[1]
    
    def processStateRequest(self, avId, stateId, lastStateId, timestamp):
        """ This is the processing part of the state system that mimics the FSM system """
        avatar = base.cr.doId2do.get(avId, None)
        elapsedTime = globalClockDelta.localElapsedTime(timestamp)
        
        if not avatar:
            self.notify.warning('SUSPICIOUS! Attempted to change the state of a non-existent avatar!')
            return
        
        # Let's exit out of the previous state.
        if lastStateId == 0:
            self.exitFreezeUp(avatar)
        elif lastStateId == 1:
            self.exitFrozen(avatar)
        
        if stateId == 0:
            self.enterFreezeUp(avatar, elapsedTime)
        elif stateId == 1:
            self.enterFrozen(avatar, elapsedTime)
        elif stateId == 2:
            self.enterCooldown(avatar, elapsedTime)
        elif stateId == 3:
            self.enterCooldown(avatar, elapsedTime, fromFrozen = 1)
        elif stateId == 4:
            self.handleCooldownFinish(avatar)
        elif stateId == 5:
            # The AI is just clearing the state of the specified avatar.
            self.__resetAvatarIvalAndUnloadIceCube(avatar)
        else:
            self.notify.warning('Attempted to set state with unknown state id: {0}.'.format(stateId))
            
    def d_requestState(self, stateId):
        """ This is the requesting part of the state system that mimics the FSM system """
        self.sendUpdate('requestState', [stateId])
    
    def enterFreezeUp(self, avatar, ts):
        """ This is expecting a valid avatar object, either fetched from base.cr.doId2do#get() or passed directly """
        
        def shouldFreeze():
            if avatar == base.localAvatar:
                self.d_requestState(1)
        
        length = 1.0
        ival = Sequence(
            Func(self.attachSoundToAvatar, avatar, self.freezeUpSfx),
            ToonEffects.getToonFreezeInterval(avatar, duration = length),
            Func(shouldFreeze),
            name = 'FreezeUp'
        )

        if avatar == base.localAvatar:
            self.__startWaterWatch(0)
        self.__setAvatarIntervalAndIceCube(avatar, None, ival, ts)
        
    def exitFreezeUp(self, avatar):
        """ This is expecting a valid avatar object, either fetched from base.cr.doId2do#get() or passed directly """
        self.__resetAvatarIvalAndUnloadIceCube(avatar)
        if avatar == base.localAvatar: self.__stopWaterWatch()
    
    def enterFrozen(self, avatar, ts):
        """ This is expecting a valid avatar object, either fetched from base.cr.doId2do#get() or passed directly """
        iceCube = ToonEffects.generateIceCube(avatar)
        
        if avatar == base.localAvatar:
            base.cr.playGame.getPlace().fsm.request('stop', [0])
            base.localAvatar.stop()
            
            # We need to hide the mouse cursor.
            props = WindowProperties()
            props.setCursorHidden(True)
            base.win.requestProperties(props)
            
            # Let's setup our GUI elements.
            self.frame = DirectFrame(pos = (0.0, 0.0, 0.7))
            self.powerBar = DirectWaitBar(frameColor = (1.0, 1.0, 1.0, 1.0), range = 100, value = 0, 
                scale = (0.4, 0.5, 0.25), parent = self.frame, barColor = (0.55, 0.7, 1.0, 1.0))
            self.label = OnscreenText(text = 'SHAKE MOUSE', shadow = (0.0, 0.0, 0.0, 1.0),
                fg = (0.55, 0.7, 1.0, 1.0), pos = (0.0, -0.1, 0.0), parent = self.frame)
            
            # Let's add our tasks
            taskMgr.add(self.__lowerPowerBar, self.LowerPowerBarTaskName)
            taskMgr.add(self.__watchMouseMovement, self.WatchMouseMovementTaskName)
            
            mw = base.mouseWatcherNode
            if mw.hasMouse():
                self.lastMouseX = mw.getMouseX()
        else:
            avatar.stop()

        ival = Sequence(
            Func(self.attachSoundToAvatar, avatar, choice(self.frozenSfxArray)),
            ToonEffects.getIceCubeFormInterval(iceCube)
        )

        self.__setAvatarIntervalAndIceCube(avatar, iceCube, ival, ts)
        
    def exitFrozen(self, avatar):
        """ This is expecting a valid avatar object, either fetched from base.cr.doId2do#get() or passed directly """
        self.__resetAvatarIvalAndUnloadIceCube(avatar)
        if avatar == base.localAvatar:
            # Let's make our cursor visible again.
            props = WindowProperties()
            props.setCursorHidden(False)
            base.win.requestProperties(props)
            
            # Let's remove our tasks
            taskMgr.remove(self.LowerPowerBarTaskName)
            taskMgr.remove(self.WatchMouseMovementTaskName)
            
            # Let's destroy all of our UI elements.
            if self.frame:
                self.label.destroy()
                self.label = None
                self.powerBar.destroy()
                self.powerBar = None
                self.frame.destroy()
                self.frame = None
            self.lastMouseX = 0
            
            base.cr.playGame.getPlace().fsm.request('walk')
            base.localAvatar.b_setAnimState('neutral')
        else:
            avatar.loop('neutral')
        
    def enterCooldown(self, avatar, ts, fromFrozen = 0):
        """ This is expecting a valid avatar object, either fetched from base.cr.doId2do#get() or passed directly """
        ival = Parallel()
        iceCube = None
        
        def handleComplete():
            if avatar == base.localAvatar:
                self.d_requestState(4)
        
        if fromFrozen:
            iceCube = ToonEffects.generateIceCube(avatar)
            iceCube.setColorScale(ToonEffects.ICE_CUBE_SOLID_COLOR)
            ival.append(ToonEffects.getIceCubeThawInterval(iceCube))
        
        # Let's do the color scale interval on the avatar.
        ival.append(Sequence(
            Func(self.attachSoundToAvatar, avatar, choice(self.coolSfxArray)),
            ToonEffects.getToonThawInterval(avatar, duration = 1.0),
            Wait(4.0),
            Func(handleComplete)
        ))
        
        self.__setAvatarIntervalAndIceCube(avatar, iceCube, ival, ts)
        
    def handleCooldownFinish(self, avatar):
        """ This is expecting a valid avatar object, either fetched from base.cr.doId2do#get() or passed directly """
        self.__resetAvatarIvalAndUnloadIceCube(avatar)
        
        if avatar == base.localAvatar:
            self.__startWaterWatch()

    def __lowerPowerBar(self, task):
        if self.powerBar['value'] <= 0:
            self.powerBar.update(0)
        self.powerBar.update(int(self.powerBar['value'] - (self.PowerLoss * globalClock.getDt())))
        return task.cont
    
    def __watchMouseMovement(self, task):
        if self.powerBar['value'] >= self.powerBar['range']:
            self.d_requestState(3)
            return task.done

        mw = base.mouseWatcherNode
        if mw.hasMouse():
            if not self.lastMouseX or self.lastMouseX != mw.getMouseX():
                value = abs(self.lastMouseX - mw.getMouseX()) / 0.001
                self.lastMouseX = mw.getMouseX()
                self.powerBar.update(self.powerBar['value'] + abs(value))
        return task.cont
    
    def __startWaterWatch(self, enter = 1):
        taskMgr.add(self.__waterWatch, self.WaterWatchTaskName, 
            extraArgs = [enter], appendTask = True)
        
    def __stopWaterWatch(self):
        taskMgr.remove(self.WaterWatchTaskName)
    
    def __waterWatch(self, enter, task):
        """ This task is ran locally to control when to switch to certain states """
        z = base.localAvatar.getZ(render)
        if enter and z <= self.InWaterZ:
            self.d_requestState(0)
            return task.done
        elif not enter and z > self.InWaterZ:
            _, ival = self.__fetchAvatarIntervalAndIceCube(base.localAvatar)
            if ival and ival.getName() == 'FreezeUp':
                self.d_requestState(2)
                return task.done
        return task.cont
    
    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        self.__startWaterWatch()
        self.sendUpdate('requestAvatarStates', [])
    
    def disable(self):
        taskMgr.remove(self.LowerPowerBarTaskName)
        taskMgr.remove(self.WatchMouseMovementTaskName)
        self.__stopWaterWatch()
        DistributedObject.disable(self)
    
    def delete(self):
        DistributedObject.delete(self)
        self.LowerPowerBarTaskName = None
        self.WatchMouseMovementTaskName = None
        self.WaterWatchTaskName = None
        self.InWaterZ = None
        self.freezeUpSfx = None
        self.frozenSfxArray = None
        self.coolSfxArray = None
        self.avId2Data = None
        
        if self.frame:
            self.label.destroy()
            self.label = None
            self.powerBar.destroy()
            self.powerBar = None
            self.frame.destroy()
            self.frame = None
        del self.LowerPowerBarTaskName
        del self.WatchMouseMovementTaskName
        del self.WaterWatchTaskName
        del self.InWaterZ
        del self.freezeUpSfx
        del self.frozenSfxArray
        del self.coolSfxArray
        del self.avId2Data
        del self.label
        del self.powerBar
        del self.frame
