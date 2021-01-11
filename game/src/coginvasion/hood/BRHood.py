"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file BRHood.py
@author Brian Lach
@date July 01, 2015

"""

from .playground import BRSafeZoneLoader
from .street import BRTownLoader

from src.coginvasion.hood import ToonHood, ZoneUtil

class BRHood(ToonHood.ToonHood):

	def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
		ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
		self.id = ZoneUtil.TheBrrrgh
		self.safeZoneLoader = BRSafeZoneLoader.BRSafeZoneLoader
		self.townLoader = BRTownLoader.BRTownLoader
		self.abbr = "BR"
		self.storageDNAFile = "phase_8/dna/storage_BR.pdna"
		self.holidayDNAFile = None
		self.titleColor = (0.25, 0.25, 1.0, 1.0)
		self.loaderDoneEvent = 'BRHood-loaderDone'

	def load(self):
		ToonHood.ToonHood.load(self)
		self.parentFSM.getStateNamed('BRHood').addChild(self.fsm)

	def unload(self):
		self.parentFSM.getStateNamed('BRHood').removeChild(self.fsm)
		ToonHood.ToonHood.unload(self)
