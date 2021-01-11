"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file ClientServicesManager.py
@author Brian Lach
@date December 3, 2014

"""

from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from src.coginvasion.gui.WhisperPopup import WhisperPopup
from src.coginvasion.globals import CIGlobals, ChatGlobals

class ClientServicesManager(DistributedObjectGlobal):

	def __init__(self, cr):
		DistributedObjectGlobal.__init__(self, cr)
		return

	def d_requestLogin(self, token, username):
		self.sendUpdate('requestLogin', [token, username])

	def getLoginAcceptedEvent(self):
		return "LOGIN_ACCEPTED"

	def loginAccepted(self):
		messenger.send(self.getLoginAcceptedEvent())

	def d_requestAvatars(self):
		self.sendUpdate("requestAvatars", [])

	def getSetAvatarsEvent(self):
		return "GOT_AVATARS"

	def setAvatars(self, avatarList):
		messenger.send(self.getSetAvatarsEvent(), [avatarList])

	def sendSubmitNewToon(self, dnaStrand, slot, name, skipTutorial):
		self.sendUpdate('requestNewAvatar', [dnaStrand, slot, name, skipTutorial])

	def getToonCreatedEvent(self):
		return "NEW_TOON_CREATED"

	def toonCreated(self, avId):
		messenger.send(self.getToonCreatedEvent(), [avId])

	def sendDeleteToon(self, avId):
		self.sendUpdate("requestDeleteAvatar", [avId])

	def getToonDeletedEvent(self):
		return "TOON_DELETED"

	def toonDeleted(self):
		messenger.send(self.getToonDeletedEvent())

	def sendSetAvatar(self, avId):
		self.sendUpdate('requestSetAvatar', [avId])

	def getSetAvatarEvent(self):
		return "SET_AVATAR"

	def setAvatarResponse(self):
		messenger.send(self.getSetAvatarEvent())
		
	def networkMessage(self, message):
		print('I got a network message!')
		whisper = WhisperPopup('ADMIN: ' + message, CIGlobals.getToonFont(), ChatGlobals.WTSystem)
		whisper.manage(base.marginManager)
