"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file DistributedDLTreasure.py
@author Brian Lach
@date July 29, 2015

"""

from . import DistributedTreasure

class DistributedDLTreasure(DistributedTreasure.DistributedTreasure):

    def __init__(self, cr):
        DistributedTreasure.DistributedTreasure.__init__(self, cr)
        self.modelPath = 'phase_8/models/props/zzz_treasure.bam'
        self.grabSoundPath = 'phase_4/audio/sfx/SZ_DD_treasure.ogg'
