"""

Copyright (c) Cog Invasion Online. All rights reserved.

@file DistributedHQNPCToonAI.py
@author Brian Lach
@date August 2, 2015

"""

from direct.directnotify.DirectNotifyGlobal import directNotify

import DistributedNPCToonAI
from src.coginvasion.globals import CIGlobals
from src.coginvasion.quests.QuestGlobals import NPCDialogue

import random

class DistributedHQNPCToonAI(DistributedNPCToonAI.DistributedNPCToonAI):
    notify = directNotify.newCategory("DistributedHQNPCToonAI")

    def doQuestStuffWithThisAvatar(self):
        DistributedNPCToonAI.DistributedNPCToonAI.doQuestStuffWithThisAvatar(self)
        av = self.air.doId2do.get(self.currentAvatar)
        if av:
            if self.currentAvatarQuestOfMe == None:
                self.d_setChat(NPCDialogue.PickQuest)
                questList = av.questManager.getPickableQuestList(self)
                self.sendUpdateToAvatarId(self.currentAvatar, 'makePickableQuests', [questList])

    def ranOutOfTime(self):
        avId = self.air.getAvatarIdFromSender()
        if avId == self.currentAvatar:
            self.d_setChat(NPCDialogue.PickQuestTimeOut)
            self.requestExit(avId)

    def pickedQuest(self, questId):
        av = self.air.doId2do.get(self.currentAvatar)
        if av:
            av.questManager.addNewQuest(questId)

    def hasValidReasonToEnter(self, avId):
        av = self.air.doId2do.get(avId)
        if av:
            chat = None
            if len(av.questManager.quests.keys()) >= 4 and not av.questManager.hasAnObjectiveToVisit(self.npcId, self.zoneId):
                array = list(CIGlobals.NPCEnter_Pointless_Dialogue)
                array.remove(array[28])
                chat = random.choice(array)
            elif (len(av.questManager.getPickableQuestList(self)) == 0 and
            not av.questManager.hasAnObjectiveToVisit(self.npcId, self.zoneId)):
                chat = CIGlobals.NPCEnter_HQ_FinishCurrentQuest
            if chat:
                if '%s' in chat:
                    chat = chat % av.getName()
                self.d_setChat(chat)
                return False
            return True
