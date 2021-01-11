from panda3d.core import (Point3, Vec3, Quat, GeomPoints, GeomVertexWriter, GeomVertexFormat,
                          GeomVertexData, GeomEnums, InternalName, TextureStage, TexGenAttrib,
                          Geom, GeomNode, BoundingSphere, CallbackNode, CallbackObject, TextureAttrib,
                          ColorBlendAttrib, ColorWriteAttrib, Vec4, TransparencyAttrib, ColorWriteAttrib)
from panda3d.bsp import GlowNode

from src.coginvasion.globals import CIGlobals
from .Entity import Entity

class PointSpotlight(Entity):

    def __init__(self):
        Entity.__init__(self)
        self.spotlightWidth = 1.0
        self.spotlightLength = 1.0
        self.spotlightDir = Vec3(0)
        self.negSpotlightDir = Vec3(0)

        self.spotlight = None
        self.halo = None
        self.callback = None
        self.rgbColor = Vec3(0)
        
    def setBeamHaloFactor(self, blend):
        if blend <= 0.001:
            self.spotlight.hide()
            self.halo.show()
        elif blend >= 0.999:
            self.spotlight.show()
            self.halo.hide()
        else:
            self.spotlight.show()
            self.halo.show()
        
        self.spotlight.setColorScale(self.rgbColor * (1.0 - blend), 1)
        self.halo.setColorScale(self.rgbColor, 1)

    def load(self):
        Entity.load(self)

        self.setPos(self.cEntity.getOrigin())
        self.setHpr(self.cEntity.getAngles())
        
        self.setDepthWrite(False, 1)
        col = self.getEntityValueColor("_light")
        self.rgbColor = col
        self.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OOne, ColorBlendAttrib.OOne), 1)
        
        self.hide(CIGlobals.ShadowCameraBitmask)

        self.spotlightLength = self.getEntityValueFloat("SpotlightLength") / 16.0
        self.spotlightWidth = self.getEntityValueFloat("SpotlightWidth") / 16.0
        
        beamAndHalo = loader.loadModel("phase_14/models/misc/light_beam_and_halo.bam")
     
        # Blend between halo and beam
        spotlightroot = self.attachNewNode('spotlightRoot')
        spotlightroot.setP(90)
        self.spotlight = beamAndHalo.find("**/beam")
        self.spotlight.setBillboardAxis()
        self.spotlight.reparentTo(spotlightroot)
        
        self.halo = CIGlobals.makeLightGlow(self.spotlightWidth)
        self.halo.reparentTo(self)
        
        beamAndHalo.removeNode()

        entPos = self.getPos()
        
        spotDir = self.getQuat().getForward()
        # User specified a max length, but clip that length so the spot effect doesn't appear to go through a floor or wall
        traceEnd = entPos + (spotDir * self.spotlightLength)
        endPos = self.bspLoader.clipLine(entPos, traceEnd)
        realLength = (endPos - entPos).length()
        self.spotlight.setSz(realLength)
        self.spotlight.setSx(self.spotlightWidth)
        
        self.spotlightDir = spotDir
        self.negSpotlightDir = -self.spotlightDir
        
        # Full beam, no halo
        self.setBeamHaloFactor(1.0)
        
        self.reparentTo(render)
        
        # Only update the spotlight if the object passes the Cull test.
        self.node().setFinal(True)
        clbk = CallbackNode('point_spotlight_callback')
        clbk.setCullCallback(CallbackObject.make(self.__spotlightThink))
        clbk.setBounds(BoundingSphere((0, 0, 0), 0))
        self.callback = self.attachNewNode(clbk)
        self.callback.hide(CIGlobals.ReflectionCameraBitmask)
        self.callback.hide(CIGlobals.ShadowCameraBitmask)

    def __spotlightThink(self, data):
        camToLight = self.getPos() - base.camera.getPos(render)
        camToLight.normalize()

        factor = abs(camToLight.dot(self.negSpotlightDir))
        
        self.setBeamHaloFactor(factor)
        
    def unload(self):
        self.callback.removeNode()
        self.callback = None
        self.spotlight.removeNode()
        self.spotlight = None
        self.halo.removeNode()
        self.halo = None
        self.spotlightWidth = None
        self.spotlightLength = None
        self.spotlightDir = None
        self.negSpotlightDir = None
        Entity.unload(self)
