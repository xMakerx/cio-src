"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file DDTownLoader.py
@author Brian Lach
@date July 26, 2015

"""

from src.coginvasion.hood.street import TownLoader, DDStreet
from src.coginvasion.globals import CIGlobals

class DDTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = DDStreet.DDStreet
        self.streetSong = 'DD_SZ'
        self.interiorSong = 'DD_SZ_activity'
        self.townStorageDNAFile = 'phase_6/dna/storage_DD_town.pdna'

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        zone4File = str(self.branchZone)
        dnaFile = 'phase_6/dna/donalds_dock_' + zone4File + '.pdna'
        self.createHood(dnaFile)

    def enter(self, requestStatus):
        TownLoader.TownLoader.enter(self, requestStatus)
        #self.hood.setWhiteFog()

    def exit(self):
        #self.hood.setNoFog()
        TownLoader.TownLoader.exit(self)
