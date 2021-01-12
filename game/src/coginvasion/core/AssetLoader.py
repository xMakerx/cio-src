"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file AssetLoader.py
@author Maverick Liberty
@date January 11, 2021

@desc Improves upon the legacy CogInvasionLoader and implements async, caching, etc.

"""

from direct.showbase.Loader import Loader
from direct.directnotify.DirectNotifyGlobal import directNotify

from panda3d.core import PStatCollector

LoadSfxCollector = PStatCollector('App:Show Code:Load SFX')

class AssetLoader(Loader):
    notify = directNotify.newCategory('AssetLoader')

    def __init__(self, base):
        Loader.__init__(self, base)

    def loadSfx(self, *args, **kw):
        LoadSfxCollector.start()
        Loader.loadSfx(args, kw)
        LoadSfxCollector.stop()
