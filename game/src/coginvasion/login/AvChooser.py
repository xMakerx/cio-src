"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file AvChooser.py
@author Brian Lach
@date November 10, 2014

"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm.ClassicFSM import ClassicFSM
from direct.fsm.State import State
from direct.fsm.StateData import StateData
from src.coginvasion.globals import CIGlobals, ChatGlobals
from src.coginvasion.hood import ZoneUtil
from src.coginvasion.holiday.HolidayManager import HolidayType, HolidayGlobals
from src.coginvasion.gui.WhisperPopup import WhisperPopup
from .AvChoice import AvChoice
from .CharSelection import CharSelection

class AvChooser(StateData):
    notify = directNotify.newCategory("AvChooser")

    def __init__(self, parentFSM):
        StateData.__init__(self, "avChooseDone")
        self.avChooseFSM = ClassicFSM('avChoose', [State('getToonData', self.enterGetToonData, self.exitGetToonData),
                                State('avChoose', self.enterAvChoose, self.exitAvChoose),
                                State('waitForToonDelResponse', self.enterWaitForToonDelResponse,
                                    self.exitWaitForToonDelResponse),
                                State('off', self.enterOff, self.exitOff)], 'off', 'off')
        self.avChooseFSM.enterInitialState()
        self.parentFSM = parentFSM
        self.parentFSM.getStateNamed('avChoose').addChild(self.avChooseFSM)
        self.pickAToon = None
        self.newToonSlot = None
        self.setAvatarsNone()

    def enter(self, newToonSlot = None):
        StateData.enter(self)
        base.transitions.noTransitions()
        self.newToonSlot = newToonSlot
        self.avChooseFSM.request('getToonData')

    def exit(self):
        StateData.exit(self)
        self.setAvatarsNone()
        self.newToonSlot = None
        self.avChooseFSM.requestFinalState()

    def setAvatarsNone(self):
        self.avChoices = []

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterGetToonData(self):
        # Get the data for the avatars tied into this account.
        self.acceptOnce(base.cr.csm.getSetAvatarsEvent(), self.handleToonData)
        base.cr.csm.d_requestAvatars()

    def handleToonData(self, avatarList):
        for av in avatarList:
            avId = av[0]
            dna = av[1]
            name = av[2]
            slot = av[3]
            lastHood = av[4]
            choice = AvChoice(dna, name, slot, avId, ZoneUtil.getHoodId(lastHood))
            self.avChoices.append(choice)
        self.avChooseFSM.request('avChoose')

    def exitGetToonData(self):
        self.ignore(base.cr.csm.getSetAvatarsEvent())

    def enterAvChoose(self):
        if base.cr.holidayManager.getHoliday() == HolidayType.CHRISTMAS:
            base.playMusic(CIGlobals.getHolidayTheme())

            # Create message.
            whisper = WhisperPopup(HolidayGlobals.CHRISTMAS_TIME, CIGlobals.getToonFont(), ChatGlobals.WTSystem)
            whisper.manage(base.marginManager)

        self.pickAToon = CharSelection(self)
        self.pickAToon.load(self.newToonSlot)

    def enterWaitForToonDelResponse(self, avId):
        self.acceptOnce(base.cr.csm.getToonDeletedEvent(), self.handleDeleteToonResp)
        base.cr.csm.sendDeleteToon(avId)

    def exitWaitForToonDelResponse(self):
        self.ignore(base.cr.csm.getToonDeletedEvent())

    def hasToonInSlot(self, slot):
        if self.getAvChoiceBySlot(slot) != None:
            return True
        else:
            return False

    def getNameInSlot(self, slot):
        return self.getAvChoiceBySlot(slot).getName()

    def getNameFromAvId(self, avId):
        for avChoice in self.avChoices:
            if avChoice.getAvId() == avId:
                return avChoice.getName()

    def getAvChoiceBySlot(self, slot):
        for avChoice in self.avChoices:
            if avChoice.getSlot() == slot:
                return avChoice
        return None

    def getHeadInfo(self, slot):
        dna = self.getAvChoiceBySlot(slot).getDNA()
        self.pickAToon.dna.setDNAStrand(dna)
        return [self.pickAToon.dna.getGender(), self.pickAToon.dna.getAnimal(),
            self.pickAToon.dna.getHead(), self.pickAToon.dna.getHeadColor()]

    def handleDeleteToonResp(self):
        base.cr.loginFSM.request('avChoose')

    def exitAvChoose(self):
        self.pickAToon.unload()
        self.pickAToon = None
