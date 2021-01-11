from direct.directnotify.DirectNotifyGlobal import directNotify

from .Attacks import ATTACK_NONE

from src.coginvasion.globals import CIGlobals

class BaseAttackShared:
    """
    Shared client/server functionality for an attack, useable by Avatars.

    This new attack system is designed to be character/interface-agnostic, meaning
    that attack code can be shared between Toons, Cogs, NPCs, etc, on the Client or Server.

    The design is tightly coupled with the new AI, which is also designed to be
    character/interface-agnostic.
    """

    notify = directNotify.newCategory("BaseAttackShared")

    HasClip = False
    HasSecondary = False
    ID = ATTACK_NONE
    Name = "Base Attack"

    Server = False
    
    StateOff = -1
    StateIdle = 0

    PlayRate = 1.0

    def __init__(self, sharedMetadata = None):
        self.maxClip = 10
        self.clip = 10
        self.maxAmmo = 10
        self.ammo = 10

        self.secondaryAmmo = 1
        self.secondaryMaxAmmo = 1

        self.level = 1

        self.action = self.StateOff
        self.lastAction = self.StateOff
        self.actionStartTime = 0
        self.nextAction = None

        self.equipped = False
        self.thinkTask = None

        self.avatar = None

        if sharedMetadata:
            for key, value in sharedMetadata.items():
                setattr(self, key, value)

    def setLevel(self, level):
        self.level = level
    
    def getLevel(self):
        return self.level
        
    def resetActions(self):
        self.action = self.StateOff
        self.lastAction = self.StateOff
        self.actionStartTime = 0
        self.nextAction = None

    def canUse(self):
        if self.HasClip:
            return self.hasClip() and self.hasAmmo()
        return self.hasAmmo() and self.action == self.StateIdle

    def getBaseDamage(self):
        return 10

    def getDamageMaxDistance(self):
        return 40.0

    def calcDamage(self, distance = 10.0):
        return CIGlobals.calcAttackDamage(distance, self.getBaseDamage(), self.getDamageMaxDistance())

    def getID(self):
        return self.ID

    def isServer(self):
        return self.Server

    def setAvatar(self, avatar):
        #assert isinstance(avatar, AvatarShared), "BaseAttackShared.setAvatar(): not a valid avatar"

        self.avatar = avatar

    def hasAvatar(self):
        return CIGlobals.isNodePathOk(self.avatar)

    def getAvatar(self):
        return self.avatar
        
    def getActionTime(self):
        return (globalClock.getFrameTime() - self.actionStartTime)
        
    def setNextAction(self, action):
        self.nextAction = action

    def getNextAction(self):
        return self.nextAction
        
    def setAction(self, action):
        self.actionStartTime = globalClock.getFrameTime()
        self.lastAction = self.action
        self.action = action
        if not self.isServer() and self.isFirstPerson():
            
            # hack
            if not self.getViewModel().isEmpty():
                if action == self.StateOff:
                    self.getViewModel().hide()
                else:
                    self.getViewModel().show()
                    
            self.onSetAction_firstPerson(action)
        else:
            self.onSetAction(action)
        
    def onSetAction(self, action):
        pass
        
    def onSetAction_firstPerson(self, action):
        pass

    def getAction(self):
        return self.action

    def getLastAction(self):
        return self.lastAction

    def __thinkTask(self, task):
        if not self.equipped:
            return task.done

        self.think()

        return task.cont

    def think(self):
        pass

    def equip(self):
        if self.equipped:
            return False

        self.equipped = True

        self.thinkTask = taskMgr.add(self.__thinkTask, "attackThink-" + str(id(self)))

        return True

    def unEquip(self):
        if not self.equipped:
            return False

        self.equipped = False
        
        self.resetActions()

        if self.thinkTask:
            self.thinkTask.remove()
            self.thinkTask = None

        return True

    def primaryFirePress(self, data = None):
        pass

    def primaryFireRelease(self, data = None):
        pass

    def secondaryFirePress(self, data = None):
        pass

    def secondaryFireRelease(self, data = None):
        pass

    def reloadPress(self, data = None):
        pass

    def reloadRelease(self, data = None):
        pass
        
    def setSecondaryAmmo(self, ammo2):
        self.secondaryAmmo = ammo2

    def getSecondaryAmmo(self):
        return self.secondaryAmmo
        
    def setSecondaryMaxAmmo(self, maxAmmo2):
        self.secondaryMaxAmmo = maxAmmo2

    def getSecondaryMaxAmmo(self):
        return self.getSecondaryMaxAmmo

    def usesSecondary(self):
        return self.HasSecondary

    def hasSecondaryAmmo(self):
        return self.secondaryAmmo > 0

    def needsReload(self):
        return self.clip == 0
        
    def setMaxClip(self, maxClip):
        self.maxClip = maxClip
        
    def setClip(self, clip):
        self.clip = clip

    def usesClip(self):
        return self.HasClip

    def hasClip(self):
        return self.clip > 0

    def isClipFull(self):
        return self.clip >= self.maxClip

    def isAmmoFull(self):
        return self.ammo >= self.maxAmmo

    def getClip(self):
        return self.clip

    def getMaxClip(self):
        return self.maxClip

    def setMaxAmmo(self, ammo):
        self.maxAmmo = ammo

    def getMaxAmmo(self):
        return self.maxAmmo

    def setAmmo(self, ammo):
        if (ammo > self.maxAmmo):
            ammo = self.maxAmmo
        self.ammo = ammo

    def getAmmo(self):
        return self.ammo

    def hasAmmo(self):
        return self.ammo > 0
        
    def getAmmoValues(self):
        return [self.ammo, self.maxAmmo,
                self.secondaryAmmo, self.secondaryMaxAmmo,
                self.clip, self.maxClip]

    def load(self):
        """
        Loads any models/sounds/data needed by this attack.
        """
        pass
        
    def doCleanup(self):
        """
        This is separated out so that unEquip() is always called before cleanup().
        """
        if self.equipped:
            self.unEquip()
        self.cleanup()

    def cleanup(self):
        del self.level
        del self.ammo
        del self.maxAmmo
        del self.avatar
        del self.secondaryAmmo
        del self.secondaryMaxAmmo
        del self.maxClip
        del self.clip
        del self.equipped
        del self.thinkTask
        del self.nextAction
        del self.action
        del self.actionStartTime
        del self.lastAction
