"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file CameraShyFirstPerson.py
@author Brian Lach
@date April 28, 2015

"""

from panda3d.core import BitMask32, CollisionNode, CollisionRay, CollisionHandlerEvent, VBase4, CollisionTraverser, CollisionHandlerQueue
from direct.fsm.ClassicFSM import ClassicFSM
from direct.fsm.State import State
from direct.gui.DirectGui import OnscreenText, DirectFrame, DirectWaitBar, OnscreenImage
from direct.showbase.InputStateGlobal import inputState
from direct.interval.IntervalGlobal import Sequence, Func, Wait
from direct.directnotify.DirectNotifyGlobal import directNotify

from .FirstPerson import FirstPerson
from src.coginvasion.globals import CIGlobals
from src.coginvasion.gui.Viewfinder import Viewfinder

class CameraShyFirstPerson(FirstPerson):
    notify = directNotify.newCategory("CameraShyFirstPerson")

    defaultColor = VBase4(1.0, 1.0, 1.0, 1.0)
    toonInFocusColor = VBase4(0.0, 0.7, 0.0, 1.0)
    toonOutOfFocusColor = VBase4(0.25, 1.0, 0.25, 1.0)
    redColor = VBase4(0.8, 0.0, 0.0, 1.0)
    batteryLevelTwoColor = VBase4(0.9, 0.36, 0.0, 1.0)
    batteryLevelThreeColor = VBase4(0.9, 0.9, 0.0, 1.0)
    batteryLevelFourColor = VBase4(1.0, 1.0, 0.0, 1.0)
    batteryLevelFiveColor = VBase4(0.0, 1.0, 0.0, 1.0)
    fullyChargedState = 5

    def __init__(self, mg):
        self.mg = mg
        self.batteryFrame = None
        self.batteryBg = None
        self.batteryBar = None
        self.rechargeSound = None
        self.fullyChargedSound = None

        self.hasToonInFocus = False
        self.toonToTakePicOf = None

        self.cameraRechargeState = None
        self.cameraRechargingLabel = None
        self.cameraFlashSeq = None

        self.viewfinder = None

        self.camFSM = ClassicFSM('CameraFSM',
              [State('off', self.enterOff, self.exitOff),
                State('ready', self.enterCameraReady, self.exitCameraReady),
                State('recharge', self.enterCameraRecharge, self.exitCameraRecharge)],
            'off', 'off')
        self.camFSM.enterInitialState()
        FirstPerson.__init__(self)

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterCameraReady(self):
        self.acceptOnce("mouse1", self.__mouse1Pressed)

    def stopCameraFlash(self):
        if self.cameraFlashSeq:
            self.cameraFlashSeq.finish()
            self.cameraFlashSeq = None

    def __mouse1Pressed(self):
        self.cameraFlashSeq = Sequence(Func(base.transitions.setFadeColor, 1, 1, 1),
			Func(base.transitions.fadeOut, 0.1),
			Wait(0.1),
			Func(base.transitions.fadeIn, 0.1),
			Wait(0.1),
			Func(base.transitions.setFadeColor, 0, 0, 0))
        self.cameraFlashSeq.start()
        self.mg.sendUpdate('remoteAvatarTakePicture', [base.localAvatar.doId])
        self.mg.myRemoteAvatar.takePicture()
        self.viewfinder['image'].setColorScale(self.defaultColor)
        picData = self.viewfinder.takePictureRaw()
        if self.hasToonInFocus and self.toonToTakePicOf:
            self.mg.sendUpdate('tookPictureOfToon', [self.toonToTakePicOf.doId])
        self.camFSM.request('recharge')

    def exitCameraReady(self):
        self.ignore("mouse1")

    def enterCameraRecharge(self):
        self.batteryBar.update(0)
        taskMgr.add(self.__rechargeNextState, "rechargeCamera")

    def __rechargeNextState(self, task):
        if self.cameraRechargeState is None:
            self.cameraRechargeState = -1
        self.cameraRechargeState += 1
        if self.cameraRechargeState > 0:
            base.playSfx(self.rechargeSound)
            
            if self.cameraRechargeState <= 1:
                self.batteryBar.setColorScale(self.redColor)
            elif self.cameraRechargeState == 2:
                self.batteryBar.setColorScale(self.batteryLevelTwoColor)
            elif self.cameraRechargeState == 3:
                self.batteryBar.setColorScale(self.batteryLevelThreeColor)
            elif self.cameraRechargeState == 4:
                self.batteryBar.setColorScale(self.batteryLevelFourColor)
            else:
                self.batteryBar.setColorScale(self.batteryLevelFiveColor)
            
        self.batteryBar.update(self.cameraRechargeState)
        if self.cameraRechargeState == self.fullyChargedState:
            base.playSfx(self.fullyChargedSound)
            self.camFSM.request('ready')
            return task.done
        task.delayTime = 1.0
        return task.again

    def exitCameraRecharge(self):
        taskMgr.remove("rechargeCamera")
        self.cameraRechargeState = None

    def __traverse(self, task):
        if not base.mouseWatcherNode.hasMouse():
            return task.cont

        toonInFoc = False
        avatar = None

        for av in self.mg.remoteAvatars:
            if av.avId != base.localAvatar.doId:
                if self.viewfinder.isInView(av):
                    self.notify.info("{0} is in our view finder".format(av.avId))
                    avatar = self.mg.cr.doId2do.get(av.avId)
                    break
        if avatar:
            remoteAvatar = self.mg.getRemoteAvatar(avatar.doId)
            if remoteAvatar:
                toonInFoc = True
                self.notify.info("We've got an avatar in focus ({0})".format(avatar.doId))
                self.__handleToonInFocus(avatar)

        if not toonInFoc:
            self.toonToTakePicOf = None
            self.hasToonInFocus = False
            self.notify.info("No avatar in focus")
            if self.viewfinder['image'].getColorScale() == self.toonInFocusColor:
                self.viewfinder['image'].setColorScale(self.toonOutOfFocusColor)
                                

        return task.cont

    def __handleToonInFocus(self, toon):
        if not self.hasToonInFocus or self.toonToTakePicOf is not None or self.toonToTakePicOf.doId != toon.doId:
            self.toonToTakePicOf = toon
            self.hasToonInFocus = True
            self.viewfinder['image'].setColorScale(self.toonInFocusColor)

    def start(self):
        self.fullyChargedSound = base.loadSfx('phase_4/audio/sfx/ring_get.ogg')
        self.rechargeSound = base.loadSfx('phase_4/audio/sfx/MG_sfx_travel_game_blue_arrow.ogg')
        self.batteryFrame = DirectFrame(parent = base.a2dBottomRight, pos = (-0.2, 0, 0.1), scale = (0.8, 0, 1))
        self.batteryBg = OnscreenImage(image = 'phase_4/maps/battery_charge_frame.png', parent = self.batteryFrame)
        self.batteryBg.setTransparency(1)
        self.batteryBg.setX(0.03)
        self.batteryBg.setScale(0.17, 0, 0.05)
        self.batteryBg.setColorScale(0, 0, 0, 1)
        self.batteryBar = DirectWaitBar(value = 0, range = 5, barColor = (1, 1, 1, 1), relief = None, scale = (0.12, 0.0, 0.3), parent = self.batteryFrame)

        self.viewfinder = Viewfinder(1.0)

        base.localAvatar.walkControls.setWalkSpeed(CIGlobals.ToonForwardSpeed, 0.0,
                                                   CIGlobals.ToonReverseSpeed, CIGlobals.ToonRotateSpeed)
        FirstPerson.start(self)

    def reallyStart(self):
        taskMgr.add(self.__traverse, "CSFP.__traverse")
        self.camFSM.request('recharge')
        #taskMgr.add(self.movementTask, "movementTask")
        base.localAvatar.startTrackAnimToSpeed()
        FirstPerson.reallyStart(self)

    def end(self):
        self.camFSM.request('off')
        taskMgr.remove("movementTask")
        taskMgr.remove("CSFP.__traverse")
        FirstPerson.end(self)

    def reallyEnd(self):
        self.batteryBar.destroy()
        self.batteryBar = None
        self.batteryBg.destroy()
        self.batteryBg = None
        self.batteryFrame.destroy()
        self.batteryFrame = None
        self.hasToonInFocus = None
        self.toonToTakePicOf = None
        self.fullyChargedSound = None
        self.rechargeSound = None
        self.viewfinder.cleanup()
        self.viewfinder = None
        self.stopCameraFlash()
        FirstPerson.reallyEnd(self)
        base.localAvatar.walkControls.setWalkSpeed(CIGlobals.ToonForwardSpeed, CIGlobals.ToonJumpForce,
            CIGlobals.ToonReverseSpeed, CIGlobals.ToonRotateSpeed)

    def cleanup(self):
        self.camFSM.requestFinalState()
        self.camFSM = None
        FirstPerson.cleanup(self)
