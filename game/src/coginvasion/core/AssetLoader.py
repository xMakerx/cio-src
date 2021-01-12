"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file AssetLoader.py
@author Maverick Liberty
@date January 11, 2021

@desc Improves upon the legacy CogInvasionLoader and implements async, caching, etc.

"""

from direct.showbase import Loader
from direct.directnotify.DirectNotifyGlobal import directNotify

from panda3d.core import PStatCollector

LoadSfxCollector = PStatCollector('App:Show Code:Load SFX')

class AssetLoader(Loader.Loader):
    notify = directNotify.newCategory('AssetLoader')

    def __init__(self, base):
        Loader.Loader.__init__(self, base)

    def loadSfx(self, *args, **kw):
        LoadSfxCollector.start()
        Loader.Loader.loadSfx(args, kw)
        LoadSfxCollector.stop()

    def loadDNAFile(self, dnaStore, filename):
        return loadDNAFile(dnaStore, filename)

    def loadModel(self, *args, **kw):
        ret = Loader.Loader.loadModel(self, *args, **kw)
        #CIGlobals.fixGrayscaleTextures(ret)

        self.tick()
        return ret

    def loadFont(self, *args, **kw):
        ret = Loader.Loader.loadFont(self, *args, **kw)
        self.tick()
        return ret

    def loadTexture(self, texturePath, alphaPath = None, okMissing = False):
        ret = Loader.Loader.loadTexture(self, texturePath, alphaPath, okMissing=okMissing)
        self.tick()
        if alphaPath:
            self.tick()
        return ret

    def loadSfx(self, soundPath):
        ret = Loader.Loader.loadSfx(self, soundPath)
        self.tick()
        return ret

    def tick(self): pass

    def loadMusic(self, soundPath):
        ret = Loader.Loader.loadMusic(self, soundPath)
        self.tick()
        return ret

    def loadParticleEffect(self, ptfPath):
        return ParticleLoader.loadParticleEffect(ptfPath)

    def destroy(self):
        Loader.Loader.destroy(self)
        try:
            self.progressScreen.destroy()
            del self.progressScreen
        except:
            pass