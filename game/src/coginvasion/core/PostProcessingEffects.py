"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file PostProcessingEffects.py
@author Maverick Liberty
@date January 12, 2021

@desc Derived from CIPostProcess.

"""

from panda3d.core import Shader, PTA_LVecBase3f, Vec3
from libpandabsp import PostProcess, PostProcessPass, PostProcessEffect, bits_PASSTEXTURE_COLOR, HDREffect, BloomEffect, FXAA_Effect

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.showbase.DirectObject import DirectObject

class PostProcessingEffects(DirectObject, PostProcess):
    notify = directNotify.newCategory('PostProcessingEffects')

    def __init__(self):
        DirectObject.__init__(self)
        self.notify.setDebug(True)
        self.notify.debug('Initializing post processing effects...')
        PostProcess.__init__(self)

        self.hdr = None
        self.bloom = None
        self.fxaa = None
        self.ssao = None

        self.flashEnabled = True
        self.flashColor = PTA_LVecBase3f.emptyArray(1)
        self.setFlashColor(Vec3(0))

        self.notify.debug('Done initializing post processing effects!')

    def enableFlash(self, color = Vec3(0)):
        self.flashEnabled = True
        self.setFlashColor(color)
        
    def setFlashColor(self, color):
        self.flashColor.setElement(0, color)
        
    def disableFlash(self):
        self.flashEnabled = False
        self.setFlashColor(Vec3(0))
        
    def cleanup(self):
        if self.hdr:
            self.hdr.shutdown()
            self.removeEffect(self.hdr)
        self.hdr = None
        
        if self.bloom:
            self.bloom.shutdown()
            self.removeEffect(self.bloom)
        self.bloom = None

        if self.fxaa:
            self.fxaa.shutdown()
            self.removeEffect(self.fxaa)
        self.fxaa = None

        if self.ssao:
            self.ssao.shutdown()
            self.removeEffect(self.ssao)
        self.ssao = None

        self.ignoreAll()
        
    def setup(self):
        self.cleanup()
        
        textures = {"sceneColorSampler": self.getSceneColorTexture()}
        
        if base.hdrToggle:
            self.hdr = HDREffect(self)
            self.hdr.getHdrPass().setExposureOutput(base.shaderGenerator.getExposureAdjustment())
            self.addEffect(self.hdr)
            #textures["hdrDebug"] = self.hdr.getFinalTexture()
        
        if base.bloomToggle:
            self.bloom = BloomEffect(self)
            self.addEffect(self.bloom)
            textures["bloomSampler"] = self.bloom.getFinalTexture()
            
        if base.fxaaToggle:
            self.fxaa = FXAA_Effect(self)
            self.addEffect(self.fxaa)
            # Replace scene color with FXAA'ed version
            textures["sceneColorSampler"] = self.fxaa.getFinalTexture()
        
        finalQuad = self.getScenePass().getQuad()
        
        vtext = "#version 330\n"
        vtext += "uniform mat4 p3d_ModelViewProjectionMatrix;\n"
        vtext += "in vec4 p3d_Vertex;\n"
        vtext += "in vec4 texcoord;\n"
        vtext += "out vec2 l_texcoord;\n"
        vtext += "void main()\n"
        vtext += "{\n"
        vtext += "  gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;\n"
        vtext += "  l_texcoord = texcoord.xy;\n"
        vtext += "}\n"

        ptext = "#version 330\n"
        ptext += "out vec4 outputColor;\n"
        ptext += "in vec2 l_texcoord;\n"

        for sampler in textures.keys():
            ptext += "uniform sampler2D " + sampler + ";\n"
            
        if self.flashEnabled:
            ptext += "uniform vec3 flashColor[1];\n"

        ptext += "void main()\n"
        ptext += "{\n"
        ptext += "  outputColor = texture(sceneColorSampler, l_texcoord);\n"
        if base.bloomToggle:
            ptext += "  outputColor.rgb += texture(bloomSampler, l_texcoord).rgb;\n"
        if self.flashEnabled:
            ptext += "  outputColor.rgb += pow(flashColor[0], vec3(2.2));\n"
        ptext += "}\n"

        shader = Shader.make(Shader.SL_GLSL, vtext, ptext)
        if not shader:
            return
            
        finalQuad.setShader(shader)
        
        for sampler, texture in textures.items():
            finalQuad.setShaderInput(sampler, texture)
            
        if self.flashEnabled:
            finalQuad.setShaderInput("flashColor", self.flashColor)


