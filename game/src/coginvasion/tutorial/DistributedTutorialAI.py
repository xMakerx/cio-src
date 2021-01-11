# Filename: DistributedTutorialAI.py
# Created by:  blach (16Oct15)

from direct.directnotify.DirectNotifyGlobal import directNotify

from src.coginvasion.globals import CIGlobals
from src.coginvasion.battle.DistributedBattleZoneAI import DistributedBattleZoneAI
from src.coginvasion.battle import BattleGlobals
from src.coginvasion.cog import SuitBank, Variant
from . import DistributedTutorialSuitAI

class DistributedTutorialAI(DistributedBattleZoneAI):
    notify = directNotify.newCategory('DistributedTutorialAI')
    notify.setInfo(True)

    battleType = BattleGlobals.BTTutorial

    def __init__(self, air, avatarId):
        DistributedBattleZoneAI.__init__(self, air)
        self.avatarId = avatarId
        self.av = self.air.doId2do.get(self.avatarId)
        self.tutSuit = None
        self.suitsKilled = 0

    def makeSuit(self, index):
        plan = SuitBank.Flunky
        level = 1
        variant = Variant.NORMAL
        suit = DistributedTutorialSuitAI.DistributedTutorialSuitAI(self.air, index, self, self.avatarId)
        suit.generateWithRequired(self.zoneId)
        suit.b_setLevel(level)
        suit.b_setSuit(plan, variant)
        suit.b_setPlace(self.zoneId)
        suit.b_setName(plan.getName())
        suit.b_setParent(CIGlobals.SPHidden)
        suit.battleZone = self
        self.tutSuit = suit

    def finishedTutorial(self):
        self.notify.info('Deleting tutorial: avatar finished')
        self.av.b_setTutorialCompleted(1)
        self.requestDelete()

    def __monitorAvatar(self, task):
        if not self.avatarId in self.air.doId2do.keys():
            self.notify.info('Deleting tutorial: avatar logged out')
            self.requestDelete()
            return task.done
        return task.cont

    def announceGenerate(self):
        DistributedBattleZoneAI.announceGenerate(self)
        # Let's go ahead and add the avatar doing the tutorial to the battleZone's list and data dict.
        self.addAvatar(self.avatarId);
        base.taskMgr.add(self.__monitorAvatar, self.uniqueName('monitorAvatar'))

    def delete(self):
        base.taskMgr.remove(self.uniqueName('monitorAvatar'))
        self.avatarId = None
        self.av = None
        if self.tutSuit:
            self.tutSuit.disable()
            self.tutSuit.requestDelete()
            self.tutSuit = None
        DistributedBattleZoneAI.delete(self)
