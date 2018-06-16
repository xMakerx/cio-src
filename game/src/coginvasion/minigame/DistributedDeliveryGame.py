"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file DistributedDeliveryGame.py
@author Brian Lach
@date October 4, 2015

"""

from panda3d.core import CompassEffect, NodePath, CollisionSphere, CollisionNode, TextNode

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.interval.IntervalGlobal import SoundInterval
from direct.gui.DirectGui import OnscreenText, DirectLabel
from direct.fsm import State

from src.coginvasion.minigame.DistributedMinigame import DistributedMinigame
from src.coginvasion.hood import ZoneUtil
from src.coginvasion.globals import CIGlobals
import DeliveryGameGlobals as DGG
from DeliveryGamePie import DeliveryGamePie

import random

class DistributedDeliveryGame(DistributedMinigame):
    notify = directNotify.newCategory('DistributedDeliveryGame')

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.fsm.addState(State.State('announceGameOver', self.enterAnnounceGameOver, self.exitAnnounceGameOver, ['gameOver']))
        self.fsm.getStateNamed('play').addTransition('announceGameOver')
        self.world = None
        self.gagShop = None
        self.olc = None
        base.localAvatar.hasBarrel = False
        self.truckBarrelIsFrom = None
        self.soundPickUpBarrel = None
        self.soundDropOff = None
        self.barrelsByAvId = {}
        self.bsLabel = None
        self.brLabel = None
        self.bdLabel = None
        self.gagShopCollNP = None
        self.barrelsRemaining = 0
        self.barrelsStolen = 0
        self.barrelsDelivered = 0
        self.pies = []

    def allBarrelsGone(self):
        self.fsm.request('announceGameOver')

    def enterAnnounceGameOver(self):
        whistleSfx = base.loadSfx("phase_4/audio/sfx/AA_sound_whistle.ogg")
        whistleSfx.play()
        del whistleSfx
        self.gameOverLbl = DirectLabel(text = "GAME\nOVER!", relief = None, scale = 0.35, text_font = CIGlobals.getMickeyFont(), text_fg = (1, 0, 0, 1))

    def exitAnnounceGameOver(self):
        self.gameOverLbl.destroy()
        del self.gameOverLbl

    def setBarrelsRemaining(self, num):
        self.barrelsRemaining = num
        self.__updateLabels()

    def getBarrelsRemaining(self):
        return self.barrelsRemaining

    def setBarrelsStolen(self, num):
        self.barrelsStolen = num
        self.__updateLabels()

    def getBarrelsStolen(self):
        return self.barrelsStolen

    def setBarrelsDelivered(self, num):
        self.barrelsDelivered = num
        self.__updateLabels()

    def getBarrelsDelivered(self):
        return self.barrelsDelivered

    def giveBarrelToSuit(self, suitId):
        suit = self.cr.doId2do.get(suitId)
        if suit:
            barrel = loader.loadModel('phase_4/models/cogHQ/gagTank.bam')
            barrel.reparentTo(suit.find('**/joint_Rhold'))
            barrel.setP(180)
            #barrel.setZ(0.25)
            barrel.setScale(0.2)
            barrel.find('**/gagTankColl').removeNode()
            self.barrelsByAvId[suitId] = barrel

    def giveBarrelToPlayer(self, avId, truckId):
        if avId == self.localAvId:
            if not base.localAvatar.hasBarrel:
                base.localAvatar.hasBarrel = True
                base.playSfx(self.soundPickUpBarrel)
                self.truckBarrelIsFrom = truckId
            else:
                return
        av = self.cr.doId2do.get(avId)
        if av:
            av.setForcedTorsoAnim('catchneutral')
            barrel = loader.loadModel('phase_4/models/cogHQ/gagTank.bam')
            barrel.reparentTo(av.find('**/def_joint_right_hold'))
            barrel.setP(90)
            barrel.setZ(0.35)
            barrel.setScale(0.3)
            barrel.find('**/gagTankColl').removeNode()
            self.barrelsByAvId[avId] = barrel

    def dropOffBarrel(self, avId):
        if avId == self.localAvId:
            if base.localAvatar.hasBarrel:
                base.localAvatar.hasBarrel = False
                base.playSfx(self.soundDropOff)
            else:
                return
        av = self.cr.doId2do.get(avId)
        if av:
            av.clearForcedTorsoAnim()
            barrel = self.barrelsByAvId.get(avId)
            if barrel != None or not barrel.isEmpty():
                barrel.removeNode()
                del self.barrelsByAvId[avId]

    def load(self):
        spawn = random.choice(DGG.SpawnPoints)
        base.localAvatar.setPos(spawn)
        base.localAvatar.setHpr(0, 0, 0)
        self.soundPickUpBarrel = base.loadSfx('phase_6/audio/sfx/SZ_MM_gliss.ogg')
        self.soundDropOff = base.loadSfx('phase_4/audio/sfx/MG_sfx_travel_game_bell_for_trolley.ogg')
        self.soundBeep = base.loadSfx('phase_4/audio/sfx/MG_delivery_truck_beep.ogg')
        self.soundDoorOpen = base.loadSfx("phase_9/audio/sfx/CHQ_VP_door_open.ogg")
        self.setMinigameMusic('phase_4/audio/bgm/MG_Delivery.ogg')
        self.setDescription('A new supply of Gags were just shipped to Toontown! ' + \
            'Run over to a truck with Gag barrels to take a barrel out. Then, carry it over to the Gag Shop. ' + \
            'Try to unload and deliver as many barrels as you can to the Gag Shop. ' + \
            'Watch out for the Cogs - they might try to snatch a barrel!')
        self.setWinnerPrize(100)
        self.setLoserPrize(0)
        self.gagShop = loader.loadModel('phase_4/models/modules/gagShop_TT.bam')
        self.gagShop.reparentTo(base.render)
        self.gagShop.setY(-70)
        sphere = CollisionSphere(0, 0, 0, 3)
        sphere.setTangible(0)
        node = CollisionNode('MGDeliveryGagShop')
        node.addSolid(sphere)
        self.gagShopCollNP = self.gagShop.attachNewNode(node)
        self.world = loader.loadModel('phase_4/models/minigames/delivery_area.egg')
        self.world.setY(-5)
        self.world.reparentTo(base.render)
        self.world.find('**/ground').setBin('ground', 18)
        self.olc = ZoneUtil.getOutdoorLightingConfig(ZoneUtil.ToontownCentral)
        self.olc.setupAndApply()
        base.camera.setPos(20, 50, 30)
        base.camera.lookAt(20, 0, 7.5)
        DistributedMinigame.load(self)

    def enterStart(self):
        DistributedMinigame.enterStart(self)
        base.playSfx(self.soundBeep)

    def enterPlay(self):
        DistributedMinigame.enterPlay(self)
        base.localAvatar.attachCamera()
        base.localAvatar.startSmartCamera()
        base.localAvatar.enableAvatarControls()
        base.localAvatar.startTrackAnimToSpeed()
        base.localAvatar.setWalkSpeedNormalNoJump()
        self.brLabel = OnscreenText(text = "", parent = base.a2dTopRight,
                                    fg = (1, 1, 1, 1), shadow = (0, 0, 0, 1),
                                    pos = (-0.1, -0.1, 0), align = TextNode.ARight)
        self.bdLabel = OnscreenText(text = "", parent = base.a2dTopLeft,
                                    fg = (1, 1, 1, 1), shadow = (0, 0, 0, 1),
                                    pos = (0.1, -0.1, 0), align = TextNode.ALeft)
        self.bsLabel = OnscreenText(text = "", parent = base.a2dTopLeft,
                                    fg = (1, 1, 1, 1), shadow = (0, 0, 0, 1),
                                    pos = (0.1, -0.2, 0), align = TextNode.ALeft)
        self.accept('enterMGDeliveryGagShop', self.__maybeDropOffBarrel)
        self.accept('alt', self.__maybeThrowGag)

    def __maybeThrowGag(self):
        if base.localAvatar.hasBarrel:
            return

        self.b_throwPie()

    def b_throwPie(self):
        self.sendUpdate('throwPie', [base.localAvatar.doId])
        self.throwPie(base.localAvatar.doId)

    def throwPie(self, avId):
        toon = self.cr.doId2do.get(avId)
        if toon:
            pie = DeliveryGamePie(toon, self)
            self.pies.append(pie)

    def pieSplat(self, index):
        pie = self.pies[index]
        pie.splat()

    def __maybeDropOffBarrel(self, entry):
        if base.localAvatar.hasBarrel and self.truckBarrelIsFrom != None:
            self.sendUpdate('requestDropOffBarrel', [self.truckBarrelIsFrom])
            self.truckBarrelIsFrom = None

    def __updateLabels(self):
        if self.brLabel:
            self.brLabel.setText("Barrels Remaining: {0}".format(self.getBarrelsRemaining()))
        if self.bdLabel:
            self.bdLabel.setText("Barrels Delivered: {0}".format(self.getBarrelsDelivered()))
        if self.bsLabel:
            self.bsLabel.setText("Barrels Stolen: {0}".format(self.getBarrelsStolen()))

    def exitPlay(self):
        self.ignore('enterMGDeliveryGagShop')
        base.localAvatar.disableAvatarControls()
        base.localAvatar.stopSmartCamera()
        base.localAvatar.detachCamera()
        base.localAvatar.stopTrackAnimToSpeed()
        base.localAvatar.setWalkSpeedNormal()
        self.brLabel.destroy()
        self.brLabel = None
        self.bsLabel.destroy()
        self.bsLabel = None
        self.bdLabel.destroy()
        self.bdLabel = None
        DistributedMinigame.exitPlay(self)

    def announceGenerate(self):
        DistributedMinigame.announceGenerate(self)
        self.load()

    def disable(self):
        if self.world:
            self.world.removeNode()
            self.world = None
        if self.gagShop:
            self.gagShop.removeNode()
            self.gagShop = None
        if self.olc:
            self.olc.cleanup()
            self.olc = None
        if self.gagShopCollNP:
            self.gagShopCollNP.removeNode()
            self.gagShopCollNP = None
        self.soundPickUpBarrel = None
        self.soundDropOff = None
        self.truckBarrelIsFrom = None
        if hasattr(base.localAvatar, 'hasBarrel'):
            del base.localAvatar.hasBarrel
        self.barrelsByAvId = None
        DistributedMinigame.disable(self)
