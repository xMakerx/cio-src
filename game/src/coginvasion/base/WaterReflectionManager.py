"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file WaterReflectionManager.py
@author Brian Lach
@date September 26, 2017
@author Brian Lach
@date July 04, 2018

"""

from panda3d.core import (BitMask32, Plane, NodePath, CullFaceAttrib, Texture,
                          TextureStage, Point3, PlaneNode, VBase4, Vec3, WindowProperties,
                          FrameBufferProperties, GraphicsPipe, GraphicsOutput, TransparencyAttrib,
                          Material, WeakNodePath, RigidBodyCombiner, AntialiasAttrib, CardMaker,
                          BoundingBox)

from direct.gui.DirectGui import OnscreenImage
from direct.filter.FilterManager import FilterManager

import math
import random

from src.coginvasion.globals import CIGlobals
from src.coginvasion.base.Lighting import LightingConfig, OutdoorLightingConfig

REFL_CAM_BITMASK = BitMask32.bit(10)

class WaterNode(NodePath):
    Nothing = 0
    Touching = 2
    Submerged = 4

    def __init__(self, size, pos, depth):
        NodePath.__init__(self, 'waterNode')
        self.setPos(pos)

        self.pos = pos
        self.depth = depth
        self.size = size
        self.height = pos[2]

        topCard = CardMaker('waterTop')
        topCard.setFrame(-size, size, -size, size)
        self.topNP = self.attachNewNode(topCard.generate())
        self.topNP.setP(-90)
        self.topNP.clearModelNodes()
        self.topNP.flattenStrong()

        botCard = CardMaker('waterBot')
        botCard.setFrame(-size, size, -size, size)
        self.botNP = self.attachNewNode(botCard.generate())
        self.botNP.setP(90)
        self.botNP.clearModelNodes()
        self.botNP.flattenStrong()

        # Create an AABB which defines the volume of this water.
        self.aabb = BoundingBox(Point3(-size, -size, -depth), Point3(size, size, 0))
        self.aabb.xform(self.getMat(render))

    def setup(self):
        self.reparentTo(render)
        self.hide(REFL_CAM_BITMASK)
        self.setLightOff(1)
        self.setMaterialOff(1)
        self.setTransparency(1)

    def disableEffects(self):
        self.topNP.clearShader()
        self.botNP.clearShader()

    def enableFakeEffect(self):
        self.disableEffects()

        staticTex = loader.loadTexture("phase_13/maps/water3.jpg")
        self.topNP.setTexture(staticTex, 1)
        self.botNP.setTexture(staticTex, 1)

    def disableFakeEffect(self):
        self.topNP.clearTexture()
        self.botNP.clearTexture()

    def enableEffects(self, reflScene, refrScene, underwaterRefrScene):
        self.disableFakeEffect()

        dudv = loader.loadTexture("phase_14/maps/water_surface_dudv_old.png")

        self.topNP.setShader(loader.loadShader("phase_14/models/shaders/water.sha"))
        self.topNP.setShaderInput("dudv", dudv)
        self.topNP.setShaderInput("dudv_tile", 0.02)
        self.topNP.setShaderInput("dudv_strength", 0.05)
        self.topNP.setShaderInput("move_factor", 0.0)
        self.topNP.setShaderInput("near", CIGlobals.DefaultCameraNear)
        self.topNP.setShaderInput("far", CIGlobals.DefaultCameraFar)
        self.topNP.setShaderInput("reflectivity", 1.0)
        self.topNP.setShaderInput("shine_damper", 1.5)
        self.topNP.setShaderInput("normal", loader.loadTexture("phase_14/maps/water_surface_normal.png"))

        currCfg = OutdoorLightingConfig.ActiveConfig
        if currCfg is not None and isinstance(currCfg, OutdoorLightingConfig):
            dir = CIGlobals.anglesToVector(currCfg.sunAngle)
            col = currCfg.sun
        else:
            dir = CIGlobals.anglesToVector(base.loader.envConfig.defaultSunAngle)
            col = base.loader.envConfig.defaultSunColor
        self.topNP.setShaderInput("lightdir", dir)
        self.topNP.setShaderInput("lightcol", col)

        self.botNP.setShader(loader.loadShader("phase_14/models/shaders/water_bottom.sha"))
        self.botNP.setShaderInput("dudv", dudv)
        self.botNP.setShaderInput("dudv_tile", 0.02)
        self.botNP.setShaderInput("dudv_strength", 0.05)
        self.botNP.setShaderInput("move_factor", 0.0)

        self.setTextureInputs(reflScene, refrScene, underwaterRefrScene)

    def setTextureInputs(self, reflScene, refrScene, underwaterRefrScene):
        self.topNP.setShaderInput("refl", reflScene.texture)
        self.topNP.setShaderInput("refr", refrScene.texture)
        self.topNP.setShaderInput("refr_depth", refrScene.depthTex)

        self.botNP.setShaderInput("refr", underwaterRefrScene.texture)

    def isInWater(self, bottom, top):
        return self.aabb.contains(bottom, top)

    def isTouchingWater(self, position):
        return self.aabb.contains(position) != BoundingBox.IFNoIntersection

    def removeNode(self):
        self.topNP.removeNode()
        del self.topNP
        self.botNP.removeNode()
        del self.botNP
        del self.aabb
        del self.height
        del self.pos
        del self.size
        del self.depth
        NodePath.removeNode(self)

class WaterScene:

    def __init__(self, name, reso, height, planeVec, reflection = False, needDepth = False):
        buffer = base.win.makeTextureBuffer(name, reso, reso)
        buffer.setSort(-1)
        buffer.setClearColorActive(True)
        buffer.setClearColor(base.win.getClearColor())

        self.buffer = buffer
        
        self.camera = base.makeCamera(buffer)
        self.camera.node().setLens(base.camLens)
        self.camera.node().setCameraMask(REFL_CAM_BITMASK)

        self.texture = buffer.getTexture()
        self.texture.setWrapU(Texture.WMClamp)
        self.texture.setWrapV(Texture.WMClamp)
        self.texture.setMinfilter(Texture.FTLinearMipmapLinear)

        if needDepth:
            depthTex = Texture(name + "_depth")
            depthTex.setWrapU(Texture.WMClamp)
            depthTex.setWrapV(Texture.WMClamp)
            depthTex.setMinfilter(Texture.FTLinearMipmapLinear)

            buffer.addRenderTexture(depthTex, GraphicsOutput.RTMBindOrCopy,
                                    GraphicsOutput.RTPDepth)

            self.depthTex = depthTex

        self.plane = Plane(planeVec, Point3(0, 0, height))
        self.planeNode = PlaneNode(name + "_plane", self.plane)
        self.planeNP = render.attachNewNode(self.planeNode)
        tmpnp = NodePath("StateInitializer")
        tmpnp.setClipPlane(self.planeNP)
        if reflection:
            tmpnp.setAttrib(CullFaceAttrib.makeReverse())
        else:
            tmpnp.setAttrib(CullFaceAttrib.makeDefault())
        # As an optimization, disable any kind of shaders (mainly the ShaderGenerator) on the
        # reflected/refracted scene.
        tmpnp.setShaderOff(10)
        tmpnp.setAntialias(0, 10)
        self.camera.node().setInitialState(tmpnp.getState())

        self.disable()

    def cleanup(self):
        self.disable()
        if hasattr(self, 'planeNP'):
            del self.plane
            del self.planeNode
            self.planeNP.removeNode()
            del self.planeNP

        self.camera.removeNode()
        del self.camera

        del self.texture
        if hasattr(self, 'depthTex'):
            del self.depthTex

        self.buffer.clearRenderTextures()
        del self.buffer

    def enable(self):
        self.camera.unstash()
        self.camera.reparentTo(render)

    def disable(self):
        self.camera.reparentTo(hidden)
        self.camera.stash()

class WaterReflectionManager:

    def __init__(self):
        self.enabled = True
        self.cameraSubmerged = False
        self.localAvTouching = WaterNode.Nothing
        self.underwater = False
        self.underwaterFog = [VBase4(0.0, 0.3, 0.7, 1.0), 0.02]
        self.waterNodes = []

        self.uwFilterMgr = FilterManager(base.win, base.cam)
        self.dudv = loader.loadTexture("phase_14/maps/water_surface_dudv_old.png")
        self.uwFilterQuad = None
        self.colortex = Texture("filter-base-color")
        self.colortex.setWrapU(Texture.WMClamp)
        self.colortex.setWrapV(Texture.WMClamp)

        self.underwaterSound = base.loadSfx("phase_14/audio/sfx/AV_ambient_water.ogg")
        self.underwaterSound.setLoop(True)

        self.wadeSounds = []
        wades = 4
        for i in xrange(wades):
            self.wadeSounds.append(base.loadSfx("phase_14/audio/sfx/wade{0}.ogg".format(i + 1)))
        
        sMgr = CIGlobals.getSettingsMgr()
        self.reso = sMgr.ReflectionQuality[sMgr.getSetting("refl")]

    def hasWaterEffects(self):
        return self.reso > 0

    def getHoodOLC(self):
        pg = base.cr.playGame
        if pg:
            hood = pg.hood
            if hood:
                if hasattr(hood, 'olc') and hood.olc:
                    return hood.olc
        return None

    def setupScene(self, height):
        if self.hasWaterEffects():
            self.reflScene = WaterScene("reflection", self.reso, height, Vec3(0, 0, 1), True)
            self.reflScene.enable()
            self.refrScene = WaterScene("refraction", self.reso, height, Vec3(0, 0, -1), needDepth = True)
            self.refrScene.enable()
            self.underwaterRefrScene = WaterScene("underwaterRefraction", self.reso, height, Vec3(0, 0, 1))
            self.underwaterRefrScene.disable()

        self.startUpdateTask()

    def isTouchingAnyWater(self, bottom, top):
        for waterNode in self.waterNodes:
            test = waterNode.isInWater(bottom, top)

            # TOUCHING, not submerged.
            if test & WaterNode.Touching and not test & WaterNode.Submerged:
                return [True, waterNode.height]

        return [False, 0.0]
    
    def addWaterNode(self, size, pos):
        if not self.enabled:
            return

        if len(self.waterNodes) == 0:
            # We will have to do 2 extra render passes to create the water.
            # One pass viewing only stuff that is above the water (reflection)
            # and another for viewing only what's underneath the water (refraction).
            # The shader will then take these 2 textures, do fancy effects,
            # and project a combined version of the 2 onto the water nodes.
            self.setupScene(pos[2])

        node = WaterNode(size, pos, 50)
        node.setup()

        if self.hasWaterEffects():
            node.enableEffects(self.reflScene, self.refrScene, self.underwaterRefrScene)
        else:
            node.enableFakeEffect()

        self.waterNodes.append(node)

    def clearWaterNodes(self):
        if len(self.waterNodes) == 0:
            return

        for waterNode in self.waterNodes:
            waterNode.removeNode()

        self.waterNodes = []
        self.cleanupScenes()

    def cleanupScenes(self):
        self.stopUpdateTask()
        
        if hasattr(self, 'reflScene') and self.reflScene:
            self.reflScene.cleanup()
            del self.reflScene
        if hasattr(self, 'refrScene') and self.refrScene:
            self.refrScene.cleanup()
            del self.refrScene
        if hasattr(self, 'underwaterRefrScene') and self.underwaterRefrScene:
            self.underwaterRefrScene.cleanup()
            del self.underwaterRefrScene

    def startUpdateTask(self):
        taskMgr.add(self.update, "waterRefl-update", sort = 45)

    def stopUpdateTask(self):
        taskMgr.remove("waterRefl-update")

    def cleanup(self):
        if not self.enabled:
            return

        self.clearWaterNodes()
        
    def handleResolutionUpdate(self, newResolution):
        # We need to cleanup the scenes and generate new ones.
        self.reso = newResolution
        
        self.cleanupScenes()
        
        if len(self.waterNodes) > 0:
            firstNode = self.waterNodes[0]
            self.setupScene(firstNode.height)
            
            for node in self.waterNodes:
                if self.hasWaterEffects():
                    # Let's update the textures on the shader inputs.
                    node.enableEffects(self.reflScene, self.refrScene, self.underwaterRefrScene)
                else:
                    node.enableFakeEffect()

    def update(self, task):
        if not self.enabled:
            return task.done

        if self.hasWaterEffects():
            self.reflScene.camera.setMat(base.cam.getMat(render) * self.reflScene.plane.getReflectionMat())
            self.refrScene.camera.setMat(base.cam.getMat(render))
            self.underwaterRefrScene.camera.setMat(base.cam.getMat(render))

            time = globalClock.getFrameTime()
            moveFactor = 0.02 * time

            if self.uwFilterQuad:
                self.uwFilterQuad.setShaderInput("move_factor", moveFactor * 0.8)

        foundCamSubmerged = False
        foundLocalAvTouching = WaterNode.Nothing
        waterLocalAvIsTouching = None
        for waterNode in self.waterNodes:

            # Let's see if our camera is submerged in this water node.
            if not foundCamSubmerged:
                if waterNode.isTouchingWater(camera.getPos(render)):
                    foundCamSubmerged = True

            # Now, let's see if local avatar is touching this water node.
            if not foundLocalAvTouching:
                test = waterNode.isInWater(base.localAvatar.getPos(render),
                                           base.localAvatar.getPos(render) + (0, 0, base.localAvatar.getHeight()))
                if test != WaterNode.Nothing:
                    foundLocalAvTouching = test
                    waterLocalAvIsTouching = waterNode

            if self.hasWaterEffects():
                waterNode.topNP.setShaderInput("move_factor", moveFactor)
                waterNode.botNP.setShaderInput("move_factor", moveFactor)

        if foundCamSubmerged != self.cameraSubmerged:
            if foundCamSubmerged:

                if self.hasWaterEffects():
                    self.reflScene.disable()
                    self.refrScene.disable()
                    self.underwaterRefrScene.enable()

                random.choice(self.wadeSounds).play()
                self.underwaterSound.play()
                olc = self.getHoodOLC()
                if olc:
                    olc.modifyFog(*self.underwaterFog)

                #self.uwFilterQuad = self.uwFilterMgr.renderSceneInto(colortex = self.colortex)
                #self.uwFilterQuad.setShader(loader.loadShader("phase_14/models/shaders/water_screen.sha"))
                #self.uwFilterQuad.setShaderInput("src", self.colortex)
                #self.uwFilterQuad.setShaderInput("dudv", loader.loadTexture("phase_14/maps/water_surface_dudv.png"))
                #self.uwFilterQuad.setShaderInput("dudv_tile", 1.3)
                #self.uwFilterQuad.setShaderInput("dudv_strength", 0.004)
                #self.uwFilterQuad.setShaderInput("move_factor", 0.0)
            else:
                #if self.uwFilterQuad:
                #    self.uwFilterQuad.removeNode()
                #    self.uwFilterQuad = None

                #self.uwFilterMgr.cleanup()

                if self.hasWaterEffects():
                    self.underwaterRefrScene.disable()
                    self.reflScene.enable()
                    self.refrScene.enable()

                random.choice(self.wadeSounds).play()
                self.underwaterSound.stop()
                olc = self.getHoodOLC()
                if olc:
                    olc.resetFog()

        if self.localAvTouching != foundLocalAvTouching:
            if foundLocalAvTouching & WaterNode.Submerged:
                base.localAvatar.isSwimming = True
                base.localAvatar.walkControls.setCurrentSurface('swim')
                base.localAvatar.walkControls.setControlScheme(base.localAvatar.walkControls.SSwim)
                if waterLocalAvIsTouching:
                    base.localAvatar.b_splash(base.localAvatar.getX(render),
                                              base.localAvatar.getY(render),
                                              waterLocalAvIsTouching.height)
            elif foundLocalAvTouching & WaterNode.Touching:
                base.localAvatar.isSwimming = False
                base.localAvatar.walkControls.setCurrentSurface('ttsloshnew')
                base.localAvatar.walkControls.setControlScheme(base.localAvatar.walkControls.SDefault)
            else:
                base.localAvatar.isSwimming = False
                base.localAvatar.walkControls.setCurrentSurface('hardsurface')
                base.localAvatar.walkControls.setControlScheme(base.localAvatar.walkControls.SDefault)

        self.cameraSubmerged = foundCamSubmerged
        self.localAvTouching = foundLocalAvTouching
        
        return task.cont
