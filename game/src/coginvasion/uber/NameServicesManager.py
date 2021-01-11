"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file NameServicesManager.py
@author Maverick Liberty
@date February 21, 2016

"""

from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.directnotify.DirectNotifyGlobal import directNotify

class NameServicesManager(DistributedObjectGlobal):
    notify = directNotify.newCategory('NameServicesManager')

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self.requestedNames = []
        self.requestCompleteEventName = 'NameServicesManager-RequestComplete'
        return

    def d_requestName(self, name, avId):
        self.sendUpdate('requestName', [name, avId])

    def d_requestNameData(self):
        self.sendUpdate('requestNameData', [])

    def nameDataRequest(self, names, avatarIds, accIds, dates, statuses):
        for i in range(len(names)):
            request = {}
            request['name'] = str(names[i])
            request['avId'] = int(avatarIds[i])
            request['accId'] = int(accIds[i])
            request['date'] = str(dates[i])
            request['status'] = int(statuses[i])
            self.requestedNames.append(request)
        messenger.send(self.requestCompleteEventName)

    def getNameRequests(self):
        return self.requestedNames

    def getRequestCompleteName(self):
        return self.requestCompleteEventName
