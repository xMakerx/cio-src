"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file MLHood.py
@author Brian Lach
@date July 24, 2015

"""

from panda3d.core import VBase4, Vec3

from direct.directnotify.DirectNotifyGlobal import directNotify

from .ToonHood import ToonHood
from .playground.MLSafeZoneLoader import MLSafeZoneLoader
from .street.MLTownLoader import MLTownLoader
from src.coginvasion.holiday.HolidayManager import HolidayType
from src.coginvasion.hood import ZoneUtil

class MLHood(ToonHood):
    notify = directNotify.newCategory("MLHood")

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = ZoneUtil.MinniesMelodyland
        self.safeZoneLoader = MLSafeZoneLoader
        self.townLoader = MLTownLoader
        self.abbr = "MM"
        self.storageDNAFile = "phase_6/dna/storage_MM.pdna"
        self.holidayDNAFile = None
        if base.cr.holidayManager.getHoliday() == HolidayType.CHRISTMAS:
            self.holidayDNAFile = "phase_6/dna/winter_storage_MM.pdna"
        self.titleColor = (0.945, 0.54, 1.0, 1.0)
        self.loaderDoneEvent = 'MLHood-loaderDone'

    def load(self):
        ToonHood.load(self)
        self.parentFSM.getStateNamed('MLHood').addChild(self.fsm)

    def unload(self):
        self.parentFSM.getStateNamed('MLHood').removeChild(self.fsm)
        ToonHood.unload(self)
