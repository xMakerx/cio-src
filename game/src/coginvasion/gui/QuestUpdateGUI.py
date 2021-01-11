from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import Sequence, Func, Wait
from direct.interval.IntervalGlobal import LerpColorScaleInterval, LerpScaleInterval, LerpPosInterval, Parallel

from src.coginvasion.globals import CIGlobals
from src.coginvasion.npc import NPCGlobals
from src.coginvasion.battle.BattleGlobals import BATTLE_COMPLETE_EVENT
from src.coginvasion.quest.QuestGlobals import RETURN, QUEST_DATA_UPDATE_EVENT, getLocationText
from src.coginvasion.quest.Quest import Quest
from src.coginvasion.quest import QuestData

from collections import OrderedDict
import itertools

class QuestUpdateGUI(DirectFrame):
    
    MAX_LINES = 4
    LINE_Y_OFFSET = 0.095
    LINE_MINIMUM_POS = (0.0, -(LINE_Y_OFFSET * MAX_LINES) * 1.66666667)
    LINE_MAXIMUM_POS = (0.0, (LINE_Y_OFFSET * (MAX_LINES + 2)))
    
    SHOW_DURATION = 3.0
    FADE_DURATION = 2.0
    
    SHADOW_MODIFIER = 0.45
    YELLOW_COLOR = (243.0 / 255.0, 236.0 / 255.0, 32.0 / 255.0, 1.0)
    ORANGE_COLOR = (241.0 / 255.0, 127.0 / 255.0, 43.0 / 255.0, 1.0)
    GREEN_COLOR = (51.0 / 255.0, 204 / 255.0, 51.0 / 255.0, 1.0)
    
    NEW_OBJECTIVE = 'New Objective'
    OBJECTIVE_UPDATE = 'Objective Update'
    OBJECTIVE_COMPLETE = 'Objective Complete'
    NEW_QUEST = 'New Quest'
    QUEST_COMPLETE = 'Quest Complete'
    
    def __init__(self):
        DirectFrame.__init__(self, parent = aspect2d, pos = (0.0, 0.0, 0.0))
        
        # Dictionary containing OnscreenText and an ival as a value
        self.lines = []
        self.ivalDict = {}
        self.alertSfx = base.loadSfx('phase_5.5/audio/sfx/mailbox_alert.ogg')
        
        # Text as keys and colors as values
        self.queuedLines = OrderedDict()
        
        self.initialiseoptions(QuestUpdateGUI)
        self.accept(QUEST_DATA_UPDATE_EVENT, self.__handleNewQuestData, [])
        self.accept(BATTLE_COMPLETE_EVENT, self.__handleBattleCompletion, [])
        self.accept(CIGlobals.ENTER_WALK_EVENT, self.__handleEnterWalk, [])
        
    def __addQueuedLines(self):
        for text, color in self.queuedLines.items():
            self.addLine(text, color)
        self.queuedLines.clear()
        
    def __handleBattleCompletion(self):
        self.__addQueuedLines()
        
    def __handleEnterWalk(self):
        self.__addQueuedLines()
        
    def __handleNewQuestData(self, oldDataStr, newDataStr):
        _, oldData = QuestData.extractDataAsIntegerLists(oldDataStr, None)
        _, newData = QuestData.extractDataAsIntegerLists(newDataStr, None)
        
        newQuests = {}
        oldQuests = {}
        
        for newQuestData in newData:
            questId = newQuestData[0]
            quest = Quest(questId, None)
            quest.setupCurrentObjectiveFromData(newQuestData[2], newQuestData[1], newQuestData[3])
            newQuests.update({questId : quest})
            
        for oldQuestData in oldData:
            questId = oldQuestData[0]
            quest = Quest(questId, None)
            quest.setupCurrentObjectiveFromData(oldQuestData[2], oldQuestData[1], oldQuestData[3])
            oldQuests.update({questId : quest})
            
        def acknowledgeLastObjectivesComplete(quest):
            # Let's acknowledge that we finished our last objectives.
            for objective in quest.accessibleObjectives:
                objText = objective.getUpdateBrief()
                if objective.HasProgress:
                    # This is a bit hacky, but it just allows
                    # #getProgressUpdateBrief() to show the correct stuff.
                    objective.progress = objective.goal
                    objText = objective.getProgressUpdateBrief()
                self.addLine('{0}: {1}'.format(self.OBJECTIVE_COMPLETE, objText), self.GREEN_COLOR)
        
        if len(oldDataStr) > 0:
            
            # Let's display the text for completed quests.
            if len(oldData) > len(newData):
                for questId, quest in oldQuests.items():
                    if not questId in newQuests.keys():
                        # Let's acknowledge that we finished our last objective.
                        if len(quest.accessibleObjectives) == 1:
                            objective = quest.accessibleObjectives[0]
                        else:
                            objective = quest.accessibleObjectives[len(quest.accessibleObjectives)-1]
                        
                        npcId = objective.assigner if not hasattr(objective, 'npcId') else objective.npcId
                        
                        if npcId == 0:
                            objInfo = '{0} to a {1}'.format(RETURN, NPCGlobals.lHQOfficerM)
                        else:
                            locationText = getLocationText(None, objective, verbose=False)
                            objInfo = '{0} to {1} at {2}'.format(RETURN, NPCGlobals.NPCToonNames[npcId], locationText)
                        self.addLine('{0}: {1}'.format(self.OBJECTIVE_COMPLETE, objInfo), self.GREEN_COLOR)
                        
                        # This quest isn't in our new dictionary. It must've been completed!
                        quest = oldQuests.get(questId)
                        self.addLine('{0}: \"{1}\"'.format(self.QUEST_COMPLETE, quest.name), self.GREEN_COLOR)
            
            for questId, newQuest in newQuests.items():
                oldQuest = oldQuests.get(questId, None)
                
                if oldQuest:
                    # Let's handle when the quest is complete.
                    if newQuest.isComplete() and not oldQuest.isComplete():
                        objective = newQuest.accessibleObjectives[0]
                        npcId = objective.assigner if not hasattr(objective, 'npcId') else objective.npcId
                        
                        acknowledgeLastObjectivesComplete(oldQuest)
                        
                        if npcId == 0:
                            objInfo = '{0} to a {1}'.format(RETURN, NPCGlobals.lHQOfficerM)
                        else:
                            locationText = getLocationText(None, objective, verbose=False)
                            objInfo = '{0} to {1} at {2}'.format(RETURN, NPCGlobals.NPCToonNames[npcId], locationText)

                        self.addLine('{0}: {1}'.format(self.NEW_OBJECTIVE, objInfo), self.ORANGE_COLOR)
                    
                    # Let's handle when the current objective changes.
                    elif newQuest.currentObjectiveIndex > oldQuest.currentObjectiveIndex:
                        objInfo = newQuest.accessibleObjectives[0].getUpdateBrief()
                        color = self.ORANGE_COLOR
                        prefix = self.NEW_OBJECTIVE
                    
                        # Let's acknowledge that we finished our last objectives.
                        acknowledgeLastObjectivesComplete(oldQuest)
                        
                        if newQuest.isComplete() and not oldQuest.isComplete():
                            color = self.GREEN_COLOR
                            prefix = self.QUEST_COMPLETE
                        
                        self.addLine('{0}: {1}'.format(prefix, objInfo), color)

                    elif newQuest.currentObjectiveIndex == oldQuest.currentObjectiveIndex:
                        for objIndex, newObjective in enumerate(newQuest.accessibleObjectives):
                            oldObjective = oldQuest.accessibleObjectives[objIndex]
                            
                            if newObjective.progress > oldObjective.progress:
                                objInfo = newObjective.getProgressUpdateBrief()
                                prefix = self.OBJECTIVE_UPDATE
                                color = self.YELLOW_COLOR
                                
                                if newObjective.isComplete():
                                    color = self.GREEN_COLOR
                                    prefix = self.OBJECTIVE_COMPLETE
                                
                                self.addLine('{0}: {1}'.format(prefix, objInfo), color)
                else:
                    newObjective = newQuest.accessibleObjectives[0]
                    objInfo = newObjective.getUpdateBrief()
                    
                    self.addLine('{0}: \"{1}\"'.format(self.NEW_QUEST, newQuest.name), self.YELLOW_COLOR)
                    self.addLine('{0}: {1}'.format(self.NEW_OBJECTIVE, objInfo), self.YELLOW_COLOR)
        
        # Let's cleanup our garbage now.
        for quest in itertools.chain(oldQuests.values(), newQuests.values()):
            quest.cleanup()
        newQuests.clear()
        oldQuests.clear()
        
    def addLine(self, text, color):
        # Whilst in a battle, we don't want to display update text.
        if base.localAvatarReachable():
            place = base.cr.playGame.getPlace()
            
            if base.localAvatar.getBattleZone() or (place and place.fsm.getCurrentState().getName() != 'walk'):
                self.queuedLines[text] = color
                return
        
        if len(self.lines) == self.MAX_LINES:
            oldestLine = self.lines[len(self.lines)-1]
            ival = self.ivalDict.get(oldestLine, None)
            ival.finish()
        
        newLine = OnscreenText(parent = self, 
            text = text, 
            fg = color, 
            shadow = (color[0] * self.SHADOW_MODIFIER, color[1] * self.SHADOW_MODIFIER, color[2] * self.SHADOW_MODIFIER, 1.0),
            mayChange = 1,
        font = CIGlobals.getMinnieFont())
        
        newLine.setPos(*self.LINE_MINIMUM_POS)
        
        initScale = (1.0, 1.0, 1.0)
        growScale = (1.15, 1.15, 1.15)
    
        """
        LerpScaleInterval(newLine, 0.5, 
            scale = initScale,
            blendType = 'easeIn',
            bakeInStart = 0),
        """
        
        lineIval = Sequence(
            Func(self.alertSfx.play),
            LerpScaleInterval(newLine, 0.5, 
                scale = initScale,
                startScale = (0.01, 0.01, 0.01),
                blendType = 'easeOut',
                bakeInStart = 0),
            Wait(0.5),
            Wait(self.SHOW_DURATION),
            Parallel(
                LerpPosInterval(newLine, self.FADE_DURATION, 
                    pos = (0.0, 0.0, (self.LINE_Y_OFFSET * (self.MAX_LINES + 1.8))), 
                    blendType = 'easeIn',
                    bakeInStart = 0,
                    other = self),
                LerpColorScaleInterval(newLine, self.FADE_DURATION - 0.5, (1.0, 1.0, 1.0, 0.01), blendType = 'easeIn')
            ),
            Func(self.deleteLine, newLine)
        )
        
        self.lines.insert(0, newLine)
        self.ivalDict.update({newLine : lineIval})

        for i in range(1, len(self.lines)):
            line = self.lines[i]
            
            if not line.isEmpty():
                # Let's reposition this element.
                line.setPos(line.getX(), self.LINE_MINIMUM_POS[1] + (self.LINE_Y_OFFSET * i))
        
        lineIval.start()
        
    def deleteLine(self, line):
        if line in self.lines:
            index = self.lines.index(line)
            lineIval = self.ivalDict.get(line, None)
            
            if lineIval:
                lineIval.pause()
                lineIval = None
            line.destroy()
            self.lines.pop(index)
            self.ivalDict.pop(line)
            
    def clear(self):
        for line in self.lines:
            self.deleteLine(line)
        self.queuedLines.clear()
            
    def cleanup(self):
        self.ignoreAll()
        self.clear()
        self.lines = None
        self.ivalDict = None
        self.alertSfx = None
        self.queuedLines = None
        DirectFrame.destroy(self)
