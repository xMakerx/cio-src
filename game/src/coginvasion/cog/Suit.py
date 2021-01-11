"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file Suit.py
@author Maverick Liberty
@date July 31, 2015

"""

from panda3d.core import Vec4, VBase4, Texture, TextureStage, TexGenAttrib
from panda3d.bsp import TextureStages, BSPMaterialAttrib, BSPMaterial

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.interval.IntervalGlobal import Sequence, Parallel, ActorInterval, SoundInterval, Wait, Func
from direct.distributed import DelayDelete
from direct.actor.Actor import Actor
from direct.fsm.ClassicFSM import ClassicFSM
from direct.fsm.State import State
from direct.task.Task import Task

from src.coginvasion.avatar.Avatar import Avatar
from src.coginvasion.globals import CIGlobals, BSPUtility
from src.coginvasion.cog import SuitGlobals
from src.coginvasion.cog import Variant
from src.coginvasion.cog import Voice
from src.coginvasion.cog.SuitType import SuitType
from src.coginvasion.toon import ParticleLoader
from src.coginvasion.cog import GagEffects

from src.coginvasion.avatar.Activities import ACT_WAKE_ANGRY, ACT_SMALL_FLINCH, ACT_DIE, ACT_VICTORY_DANCE, ACT_COG_FLY_DOWN
from src.coginvasion.cog.activities.WakeAngry import WakeAngry
from src.coginvasion.cog.activities.Flinch import Flinch
from src.coginvasion.cog.activities.Die import Die
from src.coginvasion.cog.activities.VictoryDance import VictoryDance
from src.coginvasion.cog.activities.FlyDown import FlyDown

import random

class Suit(Avatar):
    notify = directNotify.newCategory('Suit')

    def __init__(self):
        Avatar.__init__(self)
        self.dept = None
        self.suit = None
        self.head = None
        self.headModel = None
        self.variant = None
        self.handColor = None
        self.voice = None
        self.chat = None
        self.chatDial = None
        self.shadow = None
        self.deathSound = None
        self.propeller = None
        self.smallExp = None
        self.largeExp = None
        self.explosion = None
        self.hasSpawned = False
        self.suitTrack = None
        self.timestampAnimTrack = None
        self.propellerSounds = {}
        self.healthBar = None
        self.healthBarGlow = None
        self.condition = 0
        self.avatarType = CIGlobals.Suit
        self.suitPlan = None
        self.footstepSound = None
        self.showNametagInMargins = False
        self.surfaceProp = "metal"

        self.activities = {ACT_WAKE_ANGRY   :   WakeAngry(self),
                           ACT_SMALL_FLINCH :   Flinch(self),
                           ACT_DIE          :   Die(self),
                           ACT_VICTORY_DANCE:   VictoryDance(self),
                           ACT_COG_FLY_DOWN :   FlyDown(self)}

        self.standWalkRunReverse = [('neutral', 'walk', 0.0, 5.0, 1.0, 1.0)]

        self.gruntSound = base.audio3d.loadSfx("phase_14/audio/sfx/cog_grunt.ogg")
        base.audio3d.attachSoundToObject(self.gruntSound, self)

        self.animFSM = ClassicFSM('Suit', [
            State('off', self.enterOff, self.exitOff),
            State('neutral', self.enterNeutral, self.exitNeutral),
            State('walk', self.enterWalk, self.exitWalk),
            State('die', self.enterDie, self.exitDie),
            State('win', self.enterWin, self.exitWin),
            State('flail', self.enterFlail, self.exitFlail),
            State('flyDown', self.enterFlyDown, self.exitFlyDown),
            State('flyAway', self.enterFlyAway, self.exitFlyAway),
            State('flyNeutral', self.enterFlyNeutral, self.exitFlyNeutral),
            State('trayWalk', self.enterTrayWalk, self.exitTrayWalk),
            State('trayNeutral', self.enterTrayNeutral, self.exitTrayNeutral),
            State('stunned', self.enterStunned, self.exitStunned),
            State('pie', self.enterPie, self.exitPie),
            State('drop', self.enterDrop, self.exitDrop),
            State('drop-react', self.enterDropReact, self.exitDropReact),
            State('soak', self.enterSoak, self.exitSoak),
            State('squirt-small', self.enterSquirtSmall, self.exitSquirtSmall)
        ], 'off', 'off')
        self.animFSM.enterInitialState()
        
    def getRightHandNode(self):
        return self.find("**/joint_Rhold")

    def getLeftHandNode(self):
        return self.find("**/joint_Lhold")

    def getHeadNode(self):
        return self.headModel

    def getUpperBodySubpart(self):
        return [None]

    def getLowerBodySubpart(self):
        return [None]

    def getMoveAction(self, forward, rotate, strafe):
        return 0

    def enterPie(self, ts = 0):
        self.play('pie')

    def exitPie(self):
        self.stop()

    def enterDrop(self, ts = 0):
        self.play("drop")

    def exitDrop(self):
        self.stop()

    def enterDropReact(self, ts = 0):
        self.play('drop-react')

    def exitDropReact(self):
        self.stop()

    def enterSoak(self, ts = 0):
        self.play('soak')

    def exitSoak(self):
        self.stop()

    def enterSquirtSmall(self, ts = 0):
        self.play('squirt-small')

    def exitSquirtSmall(self):
        self.stop()

    def enterStunned(self, animB4Stun, ts = 0):
        self.show()

        animB4Stun = SuitGlobals.getAnimById(animB4Stun).getName()

        self.stunnedSound = base.loadSfxOnNode("phase_4/audio/sfx/SZ_TC_bird1.ogg", self)
        self.stunnedSound.setLoop(True)
        self.stunnedSound.play()

        self.stunnedIval = Parallel(Sequence(ActorInterval(self, animB4Stun),
                                             Func(self.loop, 'stunned')),
                                    SuitGlobals.createStunInterval(self, 0, 100))
        self.stunnedIval.start()
        
    def clearStunnedIval(self):
        if hasattr(self, 'stunnedSound'):
            self.stunnedSound.stop()
            del self.stunnedSound
        if hasattr(self, 'stunnedIval'):
            self.stunnedIval.pause()
            del self.stunnedIval

    def exitStunned(self):
        self.clearStunnedIval()
        self.stop()
        
    def getLeftHand(self):
        return self.find("**/joint_Lhold")
        
    def getRightHand(self):
        return self.find("**/joint_Rhold")

    def getNametagJoints(self):
        return []

    # BEGIN STATES

    def enterOff(self, ts = 0):
        pass

    def exitOff(self):
        pass

    def exitGeneral(self):
        self.stop()

    def enterTrayWalk(self, ts = 0):
        self.show()
        self.loop('tray-walk')

    def exitTrayWalk(self):
        self.exitGeneral()

    def enterTrayNeutral(self, ts = 0):
        self.loop('tray-neutral')

    def exitTrayNeutral(self):
        self.stop()

    def enterNeutral(self, ts = 0):
        self.show()
        self.loop("neutral")

    def exitNeutral(self):
        self.exitTimestampAnimTrack()
        self.exitGeneral()

    def enterWalk(self, ts = 0):
        self.show()
        self.loop("walk")
        self.enableRay()
        self.disableShadowRay()
        self.startFootsteps()

    def exitWalk(self):
        self.stopFootsteps()
        self.exitTimestampAnimTrack()
        self.exitGeneral()
        self.enableShadowRay()

    def enterFlail(self, ts = 0):
        self.pingpong('flail', fromFrame = 30, toFrame = 35)

    def exitFlail(self):
        self.stop()

    def exitTimestampAnimTrack(self):
        if self.timestampAnimTrack:
            self.timestampAnimTrack.pause()
            self.timestampAnimTrack = None

    def enterFlyNeutral(self, ts = 0):
        self.disableRay()
        self.enableShadowRay()
        if not self.propeller:
            self.generatePropeller()
        sfx = self.propellerSounds['neutral']
        base.playSfx(sfx, node = self, looping = 1)
        self.propeller.loop('chan', fromFrame = 0, toFrame = 3)
        self.setPlayRate(0.8, 'land')
        self.pingpong('land', fromFrame = 0, toFrame = 10)

    def exitFlyNeutral(self):
        self.cleanupPropeller()

    def enterFlyDown(self, ts = 0):
        self.disableRay()
        self.enableShadowRay()
        if not self.propeller:
            self.generatePropeller()
        sfx = self.propellerSounds['in']
        base.playSfx(sfx, node = self)
        groundF = 28
        dur = self.getDuration('land')
        fr = self.getFrameRate('land')
        if fr:
            animTimeInAir = groundF / fr
        else:
            animTimeInAir = groundF
        impactLength = dur - animTimeInAir
        timeTillLanding = 6.5 - impactLength
        waitTime = timeTillLanding - animTimeInAir
        lastSpinFrame = 8
        propDur = self.propeller.getDuration('chan')
        fr = self.propeller.getFrameRate('chan')
        spinTime = lastSpinFrame / fr
        openTime = (lastSpinFrame + 1) / fr
        if hasattr(self, 'uniqueName'):
            name = self.uniqueName('enterFlyDown')
        else:
            name = 'enterFlyDown'
        animTrack = Sequence(Func(self.pose, 'land', 0), Wait(waitTime), ActorInterval(self, 'land', duration=dur))
        propTrack = Parallel(SoundInterval(sfx, duration=waitTime + dur, node=self), Sequence(ActorInterval(self.propeller, 'chan', constrainedLoop=1, duration=waitTime + spinTime, startTime=0.0, endTime=spinTime), ActorInterval(self.propeller, 'chan', duration=propDur - openTime, startTime=openTime)))
        self.suitTrack = Parallel(animTrack, propTrack, name=self.taskName('flyDown'))
        if not self.hasSpawned:
            self.show()
            fadeInTrack = Sequence(Func(self.setTransparency, 1), self.colorScaleInterval(1, colorScale=VBase4(1, 1, 1, 1), startColorScale=VBase4(1, 1, 1, 0)), Func(self.clearColorScale), Func(self.clearTransparency))
            self.hasSpawned = True
            self.suitTrack.append(fadeInTrack)
        self.suitTrack.setDoneEvent(self.suitTrack.getName())
        self.acceptOnce(self.suitTrack.getDoneEvent(), self.exitFlyDown)
        self.suitTrack.delayDelete = DelayDelete.DelayDelete(self, name)
        self.suitTrack.start(ts)

    def exitFlyDown(self):
        self.cleanupPropeller()
        self.enableRay()
        if self.suitTrack != None:
            self.ignore(self.suitTrack.getDoneEvent())
            self.suitTrack.finish()
            DelayDelete.cleanupDelayDeletes(self.suitTrack)
            self.suitTrack = None
        self.exitGeneral()

    def enterFlyAway(self, ts = 0, doFadeOut = 0):
        self.show()
        if not self.propeller:
            self.generatePropeller()
        sfx = self.propellerSounds['out']
        if hasattr(self, 'uniqueName'):
            name = self.uniqueName('enterFlyAway')
        else:
            name = 'enterFlyAway'
        dur = self.getDuration('land')
        actInt = ActorInterval(self, 'land', loop=0, startTime=dur, endTime=0.0)
        lastSpinFrame = 8
        propDur = self.propeller.getDuration('chan')
        fr = self.propeller.getFrameRate('chan')
        spinTime = lastSpinFrame / fr
        openTime = (lastSpinFrame + 1) / fr
        propTrack = Parallel(SoundInterval(sfx, node=self), Sequence(Func(self.propeller.show),
            ActorInterval(self.propeller, 'chan', endTime=openTime, startTime=propDur),
            ActorInterval(self.propeller, 'chan', constrainedLoop=1, duration=propDur - openTime,
            startTime=spinTime, endTime=0.0)))
        self.suitTrack = Parallel(actInt, propTrack, name=self.taskName('trackName'))
        if doFadeOut:
            fadeOut = Sequence(Wait(4.0), Func(self.setTransparency, 1), self.colorScaleInterval(1, colorScale=VBase4(1, 1, 1, 0), startColorScale=VBase4(1, 1, 1, 1)), Func(self.clearColorScale), Func(self.clearTransparency), Func(self.reparentTo, hidden))
            self.suitTrack.append(fadeOut)
        self.suitTrack.setDoneEvent(self.suitTrack.getName())
        self.acceptOnce(self.suitTrack.getDoneEvent(), self.exitFlyAway)
        self.suitTrack.delayDelete = DelayDelete.DelayDelete(self, name)
        self.suitTrack.start(ts)
        self.disableRay()
        self.enableShadowRay()

    def exitFlyAway(self):
        self.cleanupPropeller()
        if self.suitTrack:
            self.ignore(self.suitTrack.getDoneEvent())
            self.suitTrack.finish()
            DelayDelete.cleanupDelayDeletes(self.suitTrack)
            self.suitTrack = None
        self.exitGeneral()

    def enterDie(self, ts = 0):
        self.show()
        self.clearStunnedIval()
        self.generateCog(isLose = 1)
        self.nametag.clearChatText()
        self.deleteNameTag()
        self.deathSound = base.audio3d.loadSfx("phase_3.5/audio/sfx/Cog_Death_Full.ogg")
        base.audio3d.attachSoundToObject(self.deathSound, self)
        trackName = self.uniqueName('enterDie')

        smallGears = ParticleLoader.loadParticleEffect('phase_3.5/etc/gearExplosionSmall.ptf')
        smallGears.getParticlesNamed('particles-1').setPoolSize(30)
        smallGears.setShaderOff(1)

        singleGear = ParticleLoader.loadParticleEffect('phase_3.5/etc/gearExplosion.ptf')
        singleGear.getParticlesNamed('particles-1').setPoolSize(1)
        singleGear.setShaderOff(1)

        smallGearExplosion = ParticleLoader.loadParticleEffect('phase_3.5/etc/gearExplosion.ptf')
        smallGearExplosion.getParticlesNamed('particles-1').setPoolSize(10)
        smallGearExplosion.setShaderOff(1)

        bigGearExplosion = ParticleLoader.loadParticleEffect('phase_3.5/etc/gearExplosionBig.ptf')
        bigGearExplosion.getParticlesNamed('particles-1').setPoolSize(30)
        bigGearExplosion.setShaderOff(1)

        smallGears.setDepthWrite(False)
        smallGears.hide(CIGlobals.ShadowCameraBitmask)
        singleGear.setDepthWrite(False)
        singleGear.hide(CIGlobals.ShadowCameraBitmask)
        smallGearExplosion.setDepthWrite(False)
        smallGearExplosion.hide(CIGlobals.ShadowCameraBitmask)
        bigGearExplosion.setDepthWrite(False)
        bigGearExplosion.hide(CIGlobals.ShadowCameraBitmask)

        self.smallGears = smallGears
        self.smallGears.setPos(self.find('**/joint_head').getPos() + (0,0, 2))
        self.singleGear = singleGear
        self.smallGearExp = smallGearExplosion
        self.bigGearExp = bigGearExplosion

        gearTrack = Sequence(Wait(0.7), Func(self.doSingleGear), Wait(1.5), Func(self.doSmallGears), Wait(3.0), Func(self.doBigExp))
        self.suitTrack = Parallel(Sequence(Wait(0.8), SoundInterval(self.deathSound, duration = 4.28)),
                Sequence(Wait(0.7), Func(self.doSingleGear), Wait(4.5),
                Func(self.suitExplode), Wait(1.0), Func(self.disableBodyCollisions)), gearTrack,
                Sequence(ActorInterval(self, 'lose', duration = 6), Func(self.getGeomNode().hide)), name = trackName)
        self.suitTrack.setDoneEvent(self.suitTrack.getName())
        self.acceptOnce(self.suitTrack.getName(), self.exitDie)
        if self.isDistributed():
            self.suitTrack.delayDelete = DelayDelete.DelayDelete(self, trackName)
        self.suitTrack.start(ts)

    def doSingleGear(self):
        self.singleGear.start(self.getGeomNode())

    def doSmallGears(self):
        self.smallGears.start(self.getGeomNode())

    def doSmallExp(self):
        self.smallGearExp.start(self.getGeomNode())

    def doBigExp(self):
        self.bigGearExp.start(self.getGeomNode())

    def suitExplode(self):
        pos = self.getPart('body').find('**/joint_head').getPos(render) + (0, 0, 2)

        # Force the loser suit to use UnlitGeneric shader, workaround for the has_mat() assertion
        BSPUtility.applyUnlitOverride(self)

        CIGlobals.makeExplosion(pos, 0.5, soundVol = 0.32)

    def exitDie(self):
        if self.suitTrack != None:
            self.ignore(self.suitTrack.getName())
            self.suitTrack.finish()
            if self.isDistributed():
                DelayDelete.cleanupDelayDeletes(self.suitTrack)
            self.suitTrack = None
        if hasattr(self, 'singleGear'):
            self.singleGear.softStop()
            del self.singleGear
        if hasattr(self, 'smallGears'):
            self.smallGears.softStop()
            del self.smallGears
        if hasattr(self, 'smallGearExp'):
            self.smallGearExp.softStop()
            del self.smallGearExp
        if hasattr(self, 'bigGearExp'):
            self.bigGearExp.softStop()
            del self.bigGearExp
        if self.deathSound:
            self.deathSound.stop()
        self.deathSound = None

    def enterWin(self, ts = 0):
        self.play('win')

    def exitWin(self):
        self.exitGeneral()

    # END STATES

    def generateSuit(self, suitPlan, variant, voice = None, hideFirst = False):
        self.suitPlan = suitPlan
        self.suit = suitPlan.getSuitType()
        self.head = suitPlan.getHead()
        self.dept = suitPlan.getDept()
        self.handColor = suitPlan.getHandColor()
        self.variant = variant
        self.setVoice(voice)
        self.generateCog()

        mat = CIGlobals.getCharacterMaterial(shininess = 50.0, specular = (0.4, 0.4, 0.4, 1))
        self.setMaterial(mat)
        
        #ts = TextureStage('shiny')
        #ts.setMode(TextureStage.MAdd)
        #ts.setRgbScale(2)
        #tex = loader.loadCubeMap('phase_14/maps/cubemap/defaultcubemap_#.png')
        #tex = loader.loadTexture('phase_14/maps/envmap001a_cog.png')
        #self.setTexGen(ts, TexGenAttrib.MEyeSphereMap)
        #self.setTexture(ts, tex)
        
        self.initializeBodyCollisions()

        if hideFirst:
            self.hide()
        else:
            self.show()

    def __blinkRed(self, task):
        self.healthBar.setColor(SuitGlobals.healthColors[3], 1)
        self.healthBarGlow.setColor(SuitGlobals.healthGlowColors[3], 1)
        if self.condition == 5:
            self.healthBar.setScale(1.17)
        return task.done

    def __blinkGray(self, task):
        if not self.healthBar:
            return
        self.healthBar.setColor(SuitGlobals.healthColors[4], 1)
        self.healthBarGlow.setColor(SuitGlobals.healthGlowColors[4], 1)
        if self.condition == 5:
            self.healthBar.setScale(1.0)
        return task.done

    def generateHealthBar(self):
        self.removeHealthBar()
        button = loader.loadModel('phase_3.5/models/gui/matching_game_gui.bam').find('**/minnieCircle')
        button.setScale(3.0)
        button.setH(180)
        button.setColor(SuitGlobals.healthColors[0])
        chestNull = self.find('**/def_joint_attachMeter')
        if chestNull.isEmpty():
            chestNull = self.find('**/joint_attachMeter')
        button.reparentTo(chestNull)
        self.healthBar = button
        self.healthBarGlow = loader.loadModel('phase_3.5/models/props/glow.bam')
        self.healthBarGlow.reparentTo(self.healthBar)
        self.healthBarGlow.setScale(0.28)
        self.healthBarGlow.setPos(-0.005, 0.01, 0.015)
        self.healthBarGlow.setColor(SuitGlobals.healthGlowColors[0])
        button.flattenLight()
        button.setLightOff()
        self.condition = 0
        if hasattr(self, 'getHealth'):
            self.updateHealthBar(self.getHealth())

    def updateHealthBar(self, hp):
        if not self.healthBar:
            return
        if hp > self.health:
            self.health = hp
        health = 0.0
        try:
            health = float(hp) / float(self.maxHealth)
        except: pass
        if health > 0.95:
            condition = 0
        elif health > 0.7:
            condition = 1
        elif health > 0.3:
            condition = 2
        elif health > 0.05:
            condition = 3
        elif health > 0.0:
            condition = 4
        else:
            condition = 5
        if self.condition != condition:
            taskMgr.remove(self.taskName('blink-task'))
            if condition == 4:
                blinkTask = Task.loop(Task(self.__blinkRed), Task.pause(0.75), Task(self.__blinkGray), Task.pause(0.1))
                taskMgr.add(blinkTask, self.taskName('blink-task'))
            elif condition == 5:
                blinkTask = Task.loop(Task(self.__blinkRed), Task.pause(0.25), Task(self.__blinkGray), Task.pause(0.1))
                taskMgr.add(blinkTask, self.taskName('blink-task'))
            else:
                self.healthBar.setColor(SuitGlobals.healthColors[condition], 1)
                self.healthBarGlow.setColor(SuitGlobals.healthGlowColors[condition], 1)
            self.condition = condition

    def removeHealthBar(self):
        if self.healthBar:
            self.healthBar.removeNode()
            self.healthBar = None
        if self.condition == 4 or self.condition == 5:
            taskMgr.remove(self.taskName('blink-task'))
        self.healthCondition = 0
        return

    def initializeBodyCollisions(self):
        self.notify.info('Initializing Body Collisions!')
        self.setupPhysics(2, self.getHeight())
        self.enableRay()

    def hideSuit(self):
        self.hide()

    def showSuit(self):
        self.show()
        fadeIn = Sequence(Func(self.setTransparency, 1), self.colorScaleInterval(0.6, colorScale=Vec4(1,1,1,1), startColorScale=Vec4(1,1,1,0)), Func(self.clearColorScale), Func(self.clearTransparency), Func(self.reparentTo, render))
        fadeIn.start()

    def doStunEffect(self):
        self.clearStunnedIval()
        self.stunnedIval = SuitGlobals.createStunInterval(self, 0, 2)
        self.stunnedIval.start()

    def doGagEffect(self, flags):
        GagEffects.doGagEffect(self, flags)

    def generateCog(self, isLose = 0, nameTag = True):
        self.cleanup()
        if not isLose:
            if self.variant == Variant.SKELETON or self.variant == Variant.ZOMBIE:
                self.loadModel('phase_5/models/char/cog%s_robot-zero.bam' % (str(self.suit)), 'body')
            else:
                self.loadModel('phase_3.5/models/char/suit%s-mod.bam' % (str(self.suit)), 'body')
            animations = SuitGlobals.animations
            anims = {}
            for anim in animations:
                if not self.suit in anim.getSuitTypes():
                    continue
                path = 'phase_%s/models/char/suit%s-%s.bam' % (anim.getPhase(), self.suit, anim.getFile())
                anims[anim.getName()] = path
            self.loadAnims(anims, 'body')
            self.generateHealthBar()

            if self.suitPlan.suitType == SuitType.A:
                self.footstepSound = base.audio3d.loadSfx("phase_5/audio/sfx/ENC_cogafssm.ogg")
            elif self.suitPlan.suitType == SuitType.B:
                self.footstepSound = base.audio3d.loadSfx("phase_5/audio/sfx/ENC_cogbfssm.ogg")
            elif self.suitPlan.suitType == SuitType.C:
                self.footstepSound = base.audio3d.loadSfx("phase_5/audio/sfx/ENC_cogcfssm.ogg")
            if self.footstepSound:
                base.audio3d.attachSoundToObject(self.footstepSound, self)

        else:
            if self.variant == Variant.SKELETON or self.variant == Variant.ZOMBIE:
                self.loadModel('phase_5/models/char/cog%s_robot-lose-mod.bam' % (str(self.suit)), 'body')
            else:
                self.loadModel('phase_4/models/char/suit%s-lose-mod.bam' % (str(self.suit)), 'body')
            self.loadAnims({'lose' : 'phase_4/models/char/suit%s-lose.bam' % (str(self.suit))}, 'body')
        if self.variant != Variant.SKELETON:
            self.headModel = self.head.generate()
            self.headModel.reparentTo(self.find("**/joint_head"))
        if self.suitPlan.getName() == SuitGlobals.VicePresident:
            self.headModel.setScale(0.35)
            self.headModel.setHpr(270, 0, 270)
            self.headModel.setZ(-0.10)
            self.headModel.loop('neutral')
        self.setClothes()

        classScale = 1.0#self.suitPlan.getCogClassAttrs().scaleMod
        self.setAvatarScale((self.suitPlan.getScale() / SuitGlobals.scaleFactors[self.suit]) * classScale)
        #self.setHeight(self.suitPlan.getHeight())
        if nameTag:
            self.setupNameTag()

        Avatar.initShadow(self)

        # We've already done all manipulating to the cog, we can just flatten it.
        self.getPart('body').flattenStrong()
        self.postFlatten()
        self.headModel.flattenStrong()
        if isinstance(self.headModel, Actor):
            self.headModel.postFlatten()

    def cleanup(self):
        if self.footstepSound:
            self.footstepSound.stop()
        self.footstepSound = None
        self.cleanupPropeller()
        self.clearChatbox()
        if self.shadow:
            self.deleteShadow()
        if self.headModel:
            self.headModel.removeNode()
        self.headModel = None
        if self.getPart('body'):
            self.removePart('body')
        self.timestampAnimTrack = None

    def generatePropeller(self):
        self.cleanupPropeller()

        self.propeller = Actor('phase_4/models/props/propeller-mod.bam',
                               {'chan' : 'phase_4/models/props/propeller-chan.bam'})
        self.propeller.reparentTo(self.find("**/joint_head"))
        self.propellerSounds['in'] = base.audio3d.loadSfx(SuitGlobals.propellerInSfx)
        self.propellerSounds['out'] = base.audio3d.loadSfx(SuitGlobals.propellerOutSfx)
        self.propellerSounds['neutral'] = base.audio3d.loadSfx(SuitGlobals.propellerNeutSfx)
        for sound in self.propellerSounds.values():
            base.audio3d.attachSoundToObject(sound, self.propeller)

    def cleanupPropeller(self):
        for sound in self.propellerSounds.values():
            base.audio3d.detachSound(sound)
            sound.stop()
        self.propellerSounds = {}
        if self.propeller and not self.propeller.isEmpty():
            self.propeller.cleanup()
        self.propeller = None

    def setVoice(self, voice):
        if not voice:
            if self.variant == Variant.SKELETON or self.variant == Variant.ZOMBIE:
                self.voice = Voice.SKELETON
            else:
                self.voice = Voice.NORMAL
        else:
            self.voice = voice

    def setClothes(self):
        if self.variant == Variant.SKELETON:
            parts = self.findAllMatches('**/pPlane*')
            for partNum in range(0, parts.getNumPaths()):
                bb = parts.getPath(partNum)
                bb.setTwoSided(1)
            tie = 'phase_5/maps/cog_robot_tie_%s.mat' % self.dept.getTie()
            #tie.setMinfilter(Texture.FTLinearMipmapLinear)
            #tie.setMagfilter(Texture.FTLinear)
            self.find('**/tie').setBSPMaterial(tie, 1)
        else:
            prefix = 'phase_3.5/maps/' + self.dept.getClothingPrefix() + '_%s.mat'
            if self.variant == Variant.WAITER:
                prefix = 'phase_3.5/maps/waiter_m_%s.mat'
            elif self.variant == Variant.CORRODED:
                prefix = 'phase_3.5/maps/' + self.dept.getClothingPrefix() + '_rust_%s.mat'

            legTex = prefix % 'leg'
            armTex = prefix % 'sleeve'
            blazTex = prefix % 'blazer'
                
            texs = [legTex, armTex, blazTex]

            #for texture in texs:
            #    texture.setMinfilter(Texture.FTLinearMipmapLinear)
            #    texture.setMagfilter(Texture.FTLinear)

            self.find('**/legs').setBSPMaterial(legTex, 1)
            self.find('**/arms').setBSPMaterial(armTex, 1)
            self.find('**/torso').setBSPMaterial(blazTex, 1)
            
            self.find('**/hands').setBSPMaterial("phase_3.5/maps/tt_t_ene_sellbotRental_hand.mat", 1)
            
            if not self.variant == Variant.CORRODED:
                self.find('**/hands').setColor(self.handColor)
            else:
                self.find('**/hands').setColor(Variant.CORRODED_HAND_COLOR)

    def startFootsteps(self):
        classAttrs = self.suitPlan.getCogClassAttrs()

        if not self.footstepSound or not classAttrs.footsteps:
            return

        self.footstepSound.setPlayRate(classAttrs.walkMod)
        self.footstepSound.setLoop(True)
        self.footstepSound.play()

    def stopFootsteps(self):
        if not self.footstepSound:
            return

        self.footstepSound.stop()

    def setName(self, nameString, charName):
        Avatar.setName(self, nameString, charName = charName, createNow = 1)

    def setupNameTag(self, tempName = None):
        Avatar.setupNameTag(self, tempName = tempName)
        if self.nametag:
            if self.level > 0:
                self.nametag.setText(self.nametag.getText() + '\n%s\nLevel %s %s' % (self.dept.getName(), self.level, self.suitPlan.getCogClassName()))
            else:
                self.nametag.setText(self.nametag.getText() + '\n%s' % (self.dept.getName()))

    def chatStompComplete(self, chatString):
        if not CIGlobals.getSettingsMgr().getSetting("chs").getValue():
            return

        self.chat = chatString
        chatDial = None
        questionDial = self.voice.getSoundFile('question')
        question02Dial = None
        gruntDial = self.voice.getSoundFile('grunt')
        statementDial = self.voice.getSoundFile('statement')
        if self.voice == Voice.NORMAL:
            question02Dial = self.voice.getSoundFile('question_2')

        if '!' in self.chat:
            chatDial = base.audio3d.loadSfx(gruntDial)
        elif '?' in self.chat:
            questionDials = [questionDial]
            if self.voice == Voice.NORMAL:
                questionDials.append(question02Dial)
            chatDial = base.audio3d.loadSfx(random.choice(questionDials))
        else:
            chatDial = base.audio3d.loadSfx(statementDial)
        self.chatDial = chatDial

        # Make the voice higher/lower based on the class
        voiceMod = self.suitPlan.getCogClassAttrs().voiceMod
        self.chatDial.setPlayRate(voiceMod)

        if self.variant == Variant.SKELETON:
            base.audio3d.attachSoundToObject(self.chatDial, self)
        else:
            base.audio3d.attachSoundToObject(self.chatDial, self.headModel)
        base.playSfx(self.chatDial, node = self)

    def setChat(self, chat):
        self.clearChatbox()
        Avatar.setChat(self, chat)
        self.chat = chat

    def clearChatbox(self):
        self.clearChat()
        self.chat = None
        if self.chatDial:
            base.audio3d.detachSound(self.chatDial)
            self.chatDial.stop()
            self.chatDial = None

    def getDept(self):
        return self.dept

    def getVariant(self):
        return self.variant

    def disable(self):
        if self.suitTrack:
            self.suitTrack.finish()
            DelayDelete.cleanupDelayDeletes(self.suitTrack)
            self.suitTrack = None
        self.animFSM.requestFinalState()
        self.cleanup()
        Avatar.disable(self)

    def delete(self):
        Avatar.delete(self)
        self.cleanup()
