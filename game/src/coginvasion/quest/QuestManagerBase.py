"""

Copyright (c) Cog Invasion Online. All rights reserved.

@file QuestManagerBase.py
@author Brian Lach
@date July 30, 2015

"""

from direct.directnotify.DirectNotifyGlobal import directNotify

from src.coginvasion.npc import NPCGlobals
from src.coginvasion.quest.Quest import Quest
from src.coginvasion.quest import QuestData
from src.coginvasion.quest import Objectives
from src.coginvasion.quest import Quests

import random

class QuestManagerBase:
    notify = directNotify.newCategory('QuestManagerBase')

    def __init__(self, avatar):
        # The avatar this quest manager is for.
        self.avatar = avatar

        # A dictionary of questId -> quest instance
        self.quests = {}
        
        # The id of the quest we're tracking.
        self.trackingId = -1

    def cleanup(self):
        del self.quests

    def isOnLastObjectiveOfQuest(self, questId):
        """Returns whether or not the current objective of the quest specified is the last objective of the quest."""

        quest = self.quests.get(questId)
        return quest.currentObjectiveIndex >= quest.numObjectives - 1

    def getVisitQuest(self, npcId):
        """Returns the quest instance and the quest ID where we have an objective to visit the NPC specified."""
        
        for questId, quest in self.quests.items():
            accObjs = quest.accessibleObjectives

            isHQ = NPCGlobals.NPCToonDict[npcId][3] == NPCGlobals.NPC_HQ
            
            for objective in accObjs: 
                if objective.type == Objectives.VisitNPC and objective.npcId == npcId:
                    return [questId, quest, objective]
                elif objective.type == Objectives.VisitHQOfficer and isHQ:
                    return [questId, quest, objective]
                elif objective.isComplete():
                    if isHQ and objective.assigner == 0:
                        return [questId, quest, objective]
                    elif objective.assigner == npcId:
                        return [questId, quest, objective]

        # We have no quest with an objective to visit the NPC specified.
        return None
    
    def getInspectionQuest(self, siteId, zoneId):
        """ Returns the quest instance, quest id, and the objective where we have an objective to inspect the site specified. """
        
        for questId, quest in self.quests.items():
            accObjs = quest.accessibleObjectives
            
            for objective in accObjs:
                if objective.type == Objectives.InspectLocationObjective:
                    if objective.siteId == siteId and objective.area == zoneId:
                        return [quest, questId, objective]
                
        # We don't have a quest where we have to inspect the specified site.
        return None
    
    def wasLastObjectiveToVisit(self, npcId, checkCurrentCompleted = False):
        """
        If checkCurrentCompleted is True, the method will check if the last objective
        was to visit this npc, and the current objective is done.

        If checkCurrentCompleted is False, the method will only check if the last objective
        was to visit this npc.
        
        NOTE: This disregards visit objectives inside of ObjectiveCollections, the idea
        behind this method is to check if the last objective before the collection was to visit the assigner.
        """

        for quest in self.quests.values():
            questId = quest.id

            accessibleObjectives = quest.accessibleObjectives

            lastObjectiveIndex = quest.currentObjectiveIndex - 1
            if lastObjectiveIndex < 0:
                # Don't worry about this quest if it's only on the first objective.
                continue

            lastObjectiveData = Quests.Quests[questId][Quests.objectives][lastObjectiveIndex]
            lastObjectiveType = lastObjectiveData[Quests.objType]

            if lastObjectiveType == Objectives.VisitNPC:
                # Check if the npcId for the last objective matches the npcId provided.
                if lastObjectiveData[Quests.args][0] == npcId:
                    return (not checkCurrentCompleted) or (checkCurrentCompleted 
                        and accessibleObjectives.isComplete())

            elif lastObjectiveType == Objectives.VisitHQOfficer:
                # As long as the NPC is an HQ officer, we're good.
                if NPCGlobals.NPCToonDict[npcId][3] == NPCGlobals.NPC_HQ:
                    return (not checkCurrentCompleted) or (checkCurrentCompleted 
                        and accessibleObjectives.isComplete())

        # We had no matches.
        return False

    def hasAnObjectiveToVisit(self, npcId, zoneId):
        """ Checks if we have an objective to visit the specified NPC at the specified location. If so, return that objective. """

        for quest in self.quests.values():
            objectives = quest.accessibleObjectives
            complete = objectives.isComplete()

            isHQ = NPCGlobals.NPCToonDict[npcId][3] == NPCGlobals.NPC_HQ
            
            for objective in objectives:
                mustVisitOfficer = objective.assigner == 0
                if objective.type == Objectives.VisitNPC:
                    # Make sure the npcIds and zones match.
                    if objective.npcId == npcId and objective.npcZone == zoneId:
                        return objective
                elif objective.type == Objectives.VisitHQOfficer or (isHQ and complete and mustVisitOfficer):
                    # When the objective is to visit an HQ officer, we can visit any HQ officer.
                    # Just make sure that the NPC is an HQ Officer.
                    if isHQ:
                        return objective
                elif objectives.isComplete() and (objective.assigner == npcId):
                    return objective

        # I guess we have no objective to visit this npc.
        return None
    
    def getPickableQuestList(self, npc):
        """
        This method generates a list of quest IDs that can be chosen by the avatar.
        You have to pass in the DistributedHQNPCToonAI instance of the HQ officer that the avatar walked up to.
        """

        # Each NPC is random!
        generator = random.Random()
        generator.seed(npc.doId)

        # This is the final quest list that will eventually hold the quests the avatar can choose.
        # This variable will be returned at the end of the method.
        quests = []

        # Our possible quest list is every Quest, right now. We will go down the line and remove quests that shouldn't be available.
        possibleQuestIds = list(Quests.Quests.keys())

        for questId in possibleQuestIds:

            if Quests.Quests[questId][Quests.tier] != self.avatar.getTier():
                # This quest isn't in our tier. Remove it from the possible choices.
                possibleQuestIds.remove(questId)
                break

            for reqQuest in Quests.Quests[questId].get(Quests.requiredQuests, []):
                # Some quests need to have other quests completed before they are able to be chosen.
                if not reqQuest in self.avatar.getQuestHistory() and questId in possibleQuestIds:
                    # A required quest is not in our avatar's quest history. We can't choose it.
                    possibleQuestIds.remove(questId)

        for questId in self.avatar.getQuestHistory():
            if questId in possibleQuestIds:
                # We can't choose quests that we have already chosen or completed!
                possibleQuestIds.remove(questId)

        if len(possibleQuestIds) > 1:
            # We have more than one quest to choose from.
            for questId in possibleQuestIds:

                if Quests.Quests[questId].get(Quests.finalInTier, False) == True:
                    # We cannot choose the final quest for our tier if we still have other quests to complete.
                    possibleQuestIds.remove(questId)

        if len(possibleQuestIds) > 3:
            # We have 4 or more quests available. Choose a random 3 out of that list.
            quests += generator.sample(possibleQuestIds, 3)
        else:
            # We have less than 4 quests, use the stripped down quest list directly.
            quests = possibleQuestIds

        # And there's our quest list!
        return quests
    
    def makeQuestFromData(self, questDataStump):
        id_ = questDataStump[0]
        curObjIndex = questDataStump[1]
        trackObjIndex = questDataStump[2]
        objProgress = questDataStump[3]
        
        quest = Quest(id_, self)
        quest.setupCurrentObjectiveFromData(trackObjIndex, curObjIndex, objProgress)
        self.quests[id_] = quest

    def makeQuestsFromData(self, avatar = None):
        """Creates new quest instances based on the questData array from the avatar. 
        If not provided an avatar, it will default to the owner of this quest manager. """
        
        if avatar is None:
            avatar = self.avatar
            
            if self.avatar is None:
                raise AssertionError('An avatar must be provided to #makeQuestsFromData() if using an anonymous quest manager.')

        # Make sure to cleanup old quests before we override them.
        for quest in self.quests.values():
            quest.cleanup()

        self.quests = {}

        QuestData.extractDataAsIntegerLists(avatar.getQuests(), parseDataFunc = self.makeQuestFromData)
        
    def getNumQuests(self):
        return len(self.quests.values())

