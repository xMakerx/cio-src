"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file AssetLoader.py
@author Maverick Liberty
@date January 11, 2021

@desc Improves upon the legacy CogInvasionLoader and implements async, caching, etc.

"""

from direct.showbase.Loader import Loader
from direct.notify.DirectNotifyGlobal import directNotify

class AssetLoader(Loader):
    notify = directNotify.newCategory('AssetLoader')

    def __init__(self, base):
        Loader.__init__(self, base)
        self.bspLoader = None if not base.want_bsp else LevelLoader(base, self)
