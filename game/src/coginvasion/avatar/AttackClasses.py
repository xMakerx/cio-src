from Attacks import *

# I don't like this, but it works
if metadata.PROCESS != 'server':
    from src.coginvasion.gagsnew.WholeCreamPie import WholeCreamPie
    from src.coginvasion.cog.attacks.ClipOnTie import ClipOnTie
    from src.coginvasion.gagsnew.HL2Shotgun import HL2Shotgun
    from src.coginvasion.gagsnew.HL2Pistol import HL2Pistol
    from src.coginvasion.gagsnew.TNT import TNT
else:
    from src.coginvasion.gagsnew.WholeCreamPie import WholeCreamPieAI as WholeCreamPie
    from src.coginvasion.cog.attacks.ClipOnTie import ClipOnTieAI as ClipOnTie
    from src.coginvasion.gagsnew.HL2Shotgun import HL2ShotgunAI as HL2Shotgun
    from src.coginvasion.gagsnew.HL2Pistol import HL2PistolAI as HL2Pistol
    from src.coginvasion.gagsnew.TNT import TNT_AI as TNT

from src.coginvasion.base.Precache import Precacheable

class AttackManager(Precacheable):

    AttackClasses = {
        ATTACK_GAG_WHOLECREAMPIE    :   WholeCreamPie,
        ATTACK_CLIPONTIE            :   ClipOnTie,
        ATTACK_HL2SHOTGUN           :   HL2Shotgun,
        ATTACK_HL2PISTOL            :   HL2Pistol,
        ATTACK_GAG_TNT              :   TNT
    }

    def getAttackClassByID(self, aID):
        return self.AttackClasses.get(aID)

    def getAttackName(self, aID):
        aCls = self.getAttackClassByID(aID)
        if aCls:
            return aCls.Name
        return "Not found"

    @classmethod
    def doPrecache(cls):
        for aCls in cls.AttackClasses.values():
            aCls.precache()