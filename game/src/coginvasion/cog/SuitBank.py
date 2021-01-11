"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file Dept.py
@author Maverick Liberty
@date September 01, 2015

"""

from panda3d.core import VBase4, Vec3

from src.coginvasion.cog import SuitGlobals
from src.coginvasion.cog.SuitType import SuitType
from src.coginvasion.cog import Dept
from src.coginvasion.cog.Head import Head
from src.coginvasion.cog import Voice
from src.coginvasion.gags import GagGlobals
from src.coginvasion.cog.SuitAttackGlobals import *

class SuitPlan:

    def __init__(self, name, suitType, dept, head, scale, nametagZ, height, headColor = None,
                 headTex = None, headAnims = None, handColor = None, forcedVariant = None, forcedVoice = None,
                 levelRange = None, forcedLevel = None, attacks = [],#SuitAttacks.attack2attackClass.keys(),
                 headShadowName = "", headShadowScale = 0, headShadowPos = None, gagWeaknesses = {}, cls = SuitGlobals.COGCLASS_GRUNT):
        self.name = name
        self.height = height
        self.suitType = suitType
        self.dept = dept
        self.scale = scale
        self.nametagZ = nametagZ
        self.handColor = handColor
        self.forcedVariant = forcedVariant
        self.forcedVoice = forcedVoice
        self.attacks = attacks
        self.levelRange = levelRange
        self.forcedLevel = forcedLevel
        self.headShadowName = headShadowName
        self.headShadowScale = headShadowScale
        self.headShadowPos = headShadowPos
        self.behaviors = []
        self.cls = cls
        
        # Gag weaknesses are stored as a dictionary like so:
        # Gag Name : Percentage Bonus (0.0-1.0)
        # If % < 1, this is an immunity (does less damage),
        # If % > 1, this is a weakness ( does more damage ).
        self.gagWeaknesses = gagWeaknesses

        if 'phase' in head:
            self.head = Head(None, head, headColor = headColor, headTex = headTex, headAnims = headAnims)
        else:
            self.head = Head(self.suitType, head, headColor = headColor, headTex = headTex)

        if not self.handColor:
            self.handColor = self.dept.getHandColor()
        #if not len(self.behaviors) and metadata.PROCESS == 'server':
        #    from src.coginvasion.cog.SuitPanicBehaviorAI import SuitPanicBehaviorAI
        #    defaultBehaviors = [[SuitPanicBehaviorAI, 4]]
        #    self.behaviors = defaultBehaviors

    def getCogClassAttrs(self):
        return SuitGlobals.getClassAttrs(self.cls)

    def getCogClass(self):
        return self.cls

    def getCogClassName(self):
        return SuitGlobals.getClassName(self.cls)

    def getName(self):
        return self.name

    def getSuitType(self):
        return self.suitType

    def getDept(self):
        return self.dept

    def getHead(self):
        return self.head

    def getScale(self):
        return self.scale

    def getHeight(self):
        return self.height

    def getNametagZ(self):
        return self.nametagZ

    def getHandColor(self):
        return self.handColor

    def getForcedVariant(self):
        return self.forcedVariant

    def getForcedVoice(self):
        return self.forcedVoice

    def getAttacks(self):
        return self.attacks

    def getLevelRange(self):
        return self.levelRange

    def getForcedLevel(self):
        return self.forcedLevel

    def getHeadShadowName(self):
        return self.headShadowName

    def getHeadShadowScale(self):
        return self.headShadowScale

    def getHeadShadowPos(self):
        return self.headShadowPos

    def getBehaviors(self):
        return self.behaviors
    
    def getGagWeaknesses(self):
        return self.gagWeaknesses

TheBigCheese = SuitPlan(
    SuitGlobals.TheBigCheese,
    SuitType.A,
    Dept.BOSS,
    'bigcheese',
    height = 9.34,
    scale = 7.0,
    nametagZ = 9.8,
    handColor = VBase4(0.75, 0.95, 0.75, 1.0),
    levelRange = (8, 13),
    headShadowName = 'shadow8',
    headShadowScale = 0.9,
    headShadowPos = Vec3(-0.0225, 10, -0.025),
    attacks = [SA_teeoff, SA_glowerpower],
    cls = SuitGlobals.COGCLASS_SUPERVISOR
)
CorporateRaider = SuitPlan(
    SuitGlobals.CorporateRaider,
    SuitType.C,
    Dept.BOSS,
    'flunky',
    height = 8.23,
    scale = 6.75,
    nametagZ = 9.0,
    handColor = VBase4(0.85, 0.55, 0.55, 1.0),
    headTex = 'phase_3.5/maps/corporate-raider.mat',
    levelRange = (7, 11),
    headShadowName = 'shadow7',
    headShadowScale = 1.0,
    headShadowPos = Vec3(0, 10, -0.05),
    attacks = [SA_canned, SA_hardball, SA_powertie, SA_evileye],
    cls = SuitGlobals.COGCLASS_SEVEN
)
HeadHunter = SuitPlan(
    SuitGlobals.HeadHunter,
    SuitType.A,
    Dept.BOSS,
    'headhunter',
    height = 7.45,
    scale = 6.5,
    nametagZ = 7.9,
    levelRange = (6, 10),
    headShadowName = 'shadow6',
    headShadowScale = 1.05,
    headShadowPos = Vec3(0, 10, -0.0425),
    gagWeaknesses = {GagGlobals.GrandPiano : 1.2},
    attacks = [SA_fountainpen, SA_glowerpower, SA_halfwindsor], #headshrink, rolodex
    cls = SuitGlobals.COGCLASS_SIX
)
Downsizer = SuitPlan(
    SuitGlobals.Downsizer,
    SuitType.B,
    Dept.BOSS,
    'beancounter',
    height = 6.08,
    scale = 4.5,
    nametagZ = 6.3,
    levelRange = (5, 9),
    headShadowName = 'shadow5',
    headShadowScale = 1.0,
    headShadowPos = Vec3(-0.02, 10, -0.01),
    gagWeaknesses = {GagGlobals.TrapDoor : 1.2},
    attacks = [SA_canned, SA_sacked], #downsize, pinkslip
    cls = SuitGlobals.COGCLASS_FIVE
)
Micromanager = SuitPlan(
    SuitGlobals.Micromanager,
    SuitType.C,
    Dept.BOSS,
    'micromanager',
    height = 3.25,
    scale = 2.5,
    nametagZ = 3.5,
    levelRange = (4, 8),
    headShadowName = 'shadow4',
    headShadowScale = 1.0,
    headShadowPos = Vec3(0, 10, -0.02),
    gagWeaknesses = {GagGlobals.Anvil : 1.1},
    attacks = [SA_fingerwag, SA_fountainpen, SA_buzzword], #demotion, brainstorm
    cls = SuitGlobals.COGCLASS_FOUR
)
Yesman = SuitPlan(
    SuitGlobals.Yesman,
    SuitType.A,
    Dept.BOSS,
    'yesman',
    height = 5.28,
    scale = 4.125,
    nametagZ = 5.6,
    levelRange = (3, 7),
    headShadowName = 'shadow3',
    headShadowScale = 1.125,
    headShadowPos = Vec3(0, 10, -0.015),
    gagWeaknesses = {GagGlobals.FruitPieSlice : 1.2},
    attacks = [SA_teeoff, SA_razzledazzle, SA_rubberstamp], #synergy
    cls = SuitGlobals.COGCLASS_THREE
)
PencilPusher = SuitPlan(
    SuitGlobals.PencilPusher,
    SuitType.B,
    Dept.BOSS,
    'pencilpusher',
    height = 5.0,
    scale = 3.35,
    nametagZ = 5.2,
    levelRange = (2, 6),
    headShadowName = 'shadow2',
    headShadowScale = 0.9,
    headShadowPos = Vec3(0, 10, 0),
    gagWeaknesses = {GagGlobals.WaterGlass : 1.1},
    attacks = [SA_fountainpen, SA_fingerwag, SA_writeoff], #rubout, fillwithlead
    cls = SuitGlobals.COGCLASS_JUNIOR
)
Flunky = SuitPlan(
    SuitGlobals.Flunky,
    SuitType.C,
    Dept.BOSS,
    'flunky',
    height = 4.88,
    scale = 4.0,
    nametagZ = 5.2,
    levelRange = (1, 5),
    headShadowName = 'shadow1',
    headShadowScale = 1.225,
    headShadowPos = Vec3(0, 10, -0.03),
    attacks = [SA_clipontie], #poundkey, shred
    cls = SuitGlobals.COGCLASS_GRUNT
)
BigWig = SuitPlan(
    SuitGlobals.BigWig,
    SuitType.A,
    Dept.LAW,
    'bigwig',
    height = 8.69,
    scale = 7.0,
    nametagZ = 9.2,
    levelRange = (8, 13),
    headShadowName = 'shadow16',
    headShadowScale = 0.85,
    headShadowPos = Vec3(-0.005, 10, -0.035),
    gagWeaknesses = {GagGlobals.StormCloud : 1.3},
    attacks = [SA_fingerwag], #powertrip
    cls = SuitGlobals.COGCLASS_SUPERVISOR
)
LegalEagle = SuitPlan(
    SuitGlobals.LegalEagle,
    SuitType.A,
    Dept.LAW,
    'legaleagle',
    height = 8.27,
    scale = 7.125,
    nametagZ = 8.75,
    handColor = VBase4(0.25, 0.25, 0.5, 1.0),
    levelRange = (7, 11),
    headShadowName = 'shadow15',
    headShadowScale = 1.125,
    headShadowPos = Vec3(0.005, 10, -0.035),
    gagWeaknesses = {GagGlobals.StormCloud : 1.1},
    attacks = [SA_jargon, SA_evileye],  #legalese, peckingorder
    cls = SuitGlobals.COGCLASS_SEVEN
)
SpinDoctor = SuitPlan(
    SuitGlobals.SpinDoctor,
    SuitType.B,
    Dept.LAW,
    'telemarketer',
    height = 7.9,
    scale = 5.65,
    nametagZ = 8.3,
    headTex = 'phase_4/maps/spin-doctor.mat',
    handColor = VBase4(0.5, 0.8, 0.75, 1.0),
    levelRange = (6, 10),
    headShadowName = 'shadow14',
    headShadowScale = 0.95,
    headShadowPos = Vec3(0, 10, -0.01),
    gagWeaknesses = {GagGlobals.Anvil : 1.2},
    attacks = [SA_hangup, SA_writeoff], #paradigmshift, quake, spin
    cls = SuitGlobals.COGCLASS_SIX
)
BackStabber = SuitPlan(
    SuitGlobals.BackStabber,
    SuitType.A,
    Dept.LAW,
    'backstabber',
    height = 6.71,
    scale = 4.5,
    nametagZ = 7.0,
    levelRange = (5, 9),
    headShadowName = 'shadow13',
    headShadowScale = 0.9,
    headShadowPos = Vec3(0.005, 10, -0.01),
    gagWeaknesses = {GagGlobals.BigWeight : 1.1},
    attacks = [SA_restrainingorder, SA_fingerwag], #guilttrip
    cls = SuitGlobals.COGCLASS_FIVE
)
AmbulanceChaser = SuitPlan(
    SuitGlobals.AmbulanceChaser,
    SuitType.B,
    Dept.LAW,
    'ambulancechaser',
    height = 6.39,
    scale = 4.35,
    nametagZ = 7.0,
    levelRange = (4, 8),
    headShadowName = 'shadow12',
    headShadowScale = 1.0,
    headShadowPos = Vec3(0, 10, -0.01),
    gagWeaknesses = {GagGlobals.Aoogah : 1.15},
    attacks = [SA_redtape, SA_hangup], #rolodex, shake
    cls = SuitGlobals.COGCLASS_FOUR
)
DoubleTalker = SuitPlan(
    SuitGlobals.DoubleTalker,
    SuitType.A,
    Dept.LAW,
    'twoface',
    height = 5.63,
    headTex = 'phase_4/maps/double-talker.mat',
    scale = 4.25,
    nametagZ = 6.0,
    levelRange = (3, 7),
    headShadowName = 'shadow11',
    headShadowScale = 1.0,
    headShadowPos = Vec3(0.005, 10, -0.01),
    attacks = [SA_buzzword, SA_doubletalk, SA_jargon, SA_mumbojumbo, SA_rubberstamp], #bouncecheck
    cls = SuitGlobals.COGCLASS_THREE
)
Bloodsucker = SuitPlan(
    SuitGlobals.Bloodsucker,
    SuitType.B,
    Dept.LAW,
    'movershaker',
    height = 6.17,
    headTex = 'phase_3.5/maps/bloodsucker.mat',
    scale = 4.375,
    nametagZ = 6.5,
    handColor = VBase4(0.95, 0.95, 1.0, 1.0),
    levelRange = (2, 6),
    headShadowName = 'shadow10',
    headShadowScale = 1.0,
    headShadowPos = Vec3(0, 10, -0.01),
    gagWeaknesses = {GagGlobals.Cupcake : 1.5},
    attacks = [SA_evictionnotice, SA_redtape],#withdrawal, liquidate
    cls = SuitGlobals.COGCLASS_JUNIOR
)
BottomFeeder = SuitPlan(
    SuitGlobals.BottomFeeder,
    SuitType.C,
    Dept.LAW,
    'tightwad',
    height = 4.81,
    headTex = 'phase_3.5/maps/bottom-feeder.mat',
    scale = 4.0,
    nametagZ = 5.1,
    levelRange = (1, 5),
    headShadowName = 'shadow9',
    headShadowScale = 1.25,
    headShadowPos = Vec3(0, 10, -0.03),
    gagWeaknesses = {GagGlobals.BananaPeel : 1.3},
    attacks = [SA_pickpocket, SA_watercooler, SA_rubberstamp], #shred
    cls = SuitGlobals.COGCLASS_GRUNT
)
RobberBaron = SuitPlan(
    SuitGlobals.RobberBaron,
    SuitType.A,
    Dept.CASH,
    'yesman',
    height = 8.95,
    headTex = 'phase_3.5/maps/robberbaron.mat',
    scale = 7.0,
    nametagZ = 9.4,
    levelRange = (8, 13),
    headShadowName = 'shadow24',
    headShadowScale = 0.9,
    headShadowPos = Vec3(0, 10, -0.03),
    attacks = [SA_teeoff], #powertrip
    cls = SuitGlobals.COGCLASS_SUPERVISOR
)
LoanShark = SuitPlan(
    SuitGlobals.LoanShark,
    SuitType.B,
    Dept.CASH,
    'loanshark',
    height = 8.58,
    scale = 6.5,
    nametagZ = 8.9,
    handColor = VBase4(0.5, 0.85, 0.75, 1.0),
    levelRange = (7, 11),
    headShadowName = 'shadow23',
    headShadowScale = 0.95,
    headShadowPos = Vec3(0.02, 10, -0.0175),
    gagWeaknesses = {GagGlobals.Geyser : 1.05},
    attacks = [SA_bite, SA_chomp, SA_hardball, SA_writeoff],
    cls = SuitGlobals.COGCLASS_SEVEN
)
MoneyBags = SuitPlan(
    SuitGlobals.MoneyBags,
    SuitType.C,
    Dept.CASH,
    'moneybags',
    height = 6.97,
    scale = 5.3,
    nametagZ = 7.4,
    levelRange = (6, 10),
    headShadowName = 'shadow22',
    headShadowScale = 1.0,
    headShadowPos = Vec3(0, 10, -0.06),
    gagWeaknesses = {GagGlobals.Safe : 1.2},
    attacks = [SA_marketcrash, SA_powertie], #liquidate
    cls = SuitGlobals.COGCLASS_SIX
)
NumberCruncher = SuitPlan(
    SuitGlobals.NumberCruncher,
    SuitType.A,
    Dept.CASH,
    'numbercruncher',
    height = 7.22,
    scale = 5.25,
    nametagZ = 7.8,
    levelRange = (5, 9),
    headShadowName = 'shadow21',
    headShadowScale = 0.95,
    headShadowPos = Vec3(0.0175, 10, -0.015),
    attacks = [SA_hangup], #audit, calculate, crunch, tabulate
    cls = SuitGlobals.COGCLASS_FIVE
)
BeanCounter = SuitPlan(
    SuitGlobals.BeanCounter,
    SuitType.B,
    Dept.CASH,
    'beancounter',
    height = 5.95,
    scale = 4.4,
    nametagZ = 6.3,
    levelRange = (4, 8),
    headShadowName = 'shadow20',
    headShadowScale = 1.0,
    headShadowPos = Vec3(0, 10, 0),
    gagWeaknesses = {GagGlobals.Quicksand : 1.25},
    attacks = [SA_hangup, SA_writeoff], #calculate, tabulate, audit
    cls = SuitGlobals.COGCLASS_FOUR
)
Tightwad = SuitPlan(
    SuitGlobals.Tightwad,
    SuitType.C,
    Dept.CASH,
    'tightwad',
    height = 5.41,
    scale = 4.5,
    nametagZ = 5.8,
    levelRange = (3, 7),
    headShadowName = 'shadow19',
    headShadowScale = 1.1,
    headShadowPos = Vec3(0, 10, -0.04),
    gagWeaknesses = {GagGlobals.Sandbag : 1.3},
    attacks = [SA_glowerpower, SA_fingerwag, SA_fired], #bouncecheck, freezeassets
    cls = SuitGlobals.COGCLASS_THREE
)
PennyPincher = SuitPlan(
    SuitGlobals.PennyPincher,
    SuitType.A,
    Dept.CASH,
    'pennypincher',
    height = 5.26,
    scale = 3.55,
    nametagZ = 5.6,
    handColor = VBase4(1.0, 0.5, 0.6, 1.0),
    levelRange = (2, 6),
    headShadowName = 'shadow18',
    headShadowScale = 1.05,
    headShadowPos = Vec3(0, 10, 0),
    attacks = [SA_fingerwag], #freezeassets, bouncecheck
    cls = SuitGlobals.COGCLASS_JUNIOR
)
ShortChange = SuitPlan(
    SuitGlobals.ShortChange,
    SuitType.C,
    Dept.CASH,
    'coldcaller',
    height = 4.77,
    scale = 3.6,
    nametagZ = 4.9,
    levelRange = (1, 5),
    headShadowName = 'shadow17',
    headShadowScale = 1.2,
    headShadowPos = Vec3(0, 10, -0.01),
    gagWeaknesses = {GagGlobals.FlowerPot : 1.25},
    attacks = [SA_clipontie, SA_pickpocket, SA_watercooler], #bouncecheck
    cls = SuitGlobals.COGCLASS_GRUNT
)
MrHollywood = SuitPlan(
    SuitGlobals.MrHollywood,
    SuitType.A,
    Dept.SALES,
    'yesman',
    height = 8.95,
    scale = 7.0,
    nametagZ = 9.4,
    levelRange = (8, 13),
    headShadowName = 'shadow32',
    headShadowScale = 0.9,
    headShadowPos = Vec3(0.0025, 10, -0.03),
    gagWeaknesses = {GagGlobals.WeddingCake : 1.1},
    attacks = [SA_razzledazzle], #powertrip
    cls = SuitGlobals.COGCLASS_SUPERVISOR
)
TheMingler = SuitPlan(
    SuitGlobals.TheMingler,
    SuitType.A,
    Dept.SALES,
    'twoface',
    height = 7.61,
    scale = 5.75,
    nametagZ = 8.0,
    headTex = 'phase_3.5/maps/mingler.mat',
    levelRange = (7, 11),
    headShadowName = 'shadow31',
    headShadowScale = 1.0,
    headShadowPos = Vec3(0, 10, -0.02),
    gagWeaknesses = {GagGlobals.BirthdayCake : 1.15},
    attacks = [SA_teeoff, SA_schmooze, SA_buzzword], #paradigmshift, powertrip
    cls = SuitGlobals.COGCLASS_SEVEN
)
TwoFace = SuitPlan(
    SuitGlobals.TwoFace,
    SuitType.A,
    Dept.SALES,
    'twoface',
    height = 6.95,
    scale = 5.25,
    nametagZ = 7.3,
    levelRange = (6, 10),
    headShadowName = 'shadow30',
    headShadowScale = 0.95,
    headShadowPos = Vec3(0.005, 10, -0.01),
    attacks = [SA_hangup, SA_razzledazzle, SA_redtape, SA_evileye],
    cls = SuitGlobals.COGCLASS_SIX
)
MoverShaker = SuitPlan(
    SuitGlobals.MoverShaker,
    SuitType.B,
    Dept.SALES,
    'movershaker',
    height = 6.7,
    scale = 4.75,
    nametagZ = 7.1,
    levelRange = (5, 9),
    headShadowName = 'shadow29',
    headShadowScale = 0.93,
    headShadowPos = Vec3(0.005, 10, -0.01),
    gagWeaknesses = {GagGlobals.CreamPieSlice : 1.3},
    attacks = [SA_halfwindsor], #brainstorm, shake, quake, tremor
    cls = SuitGlobals.COGCLASS_FIVE
)
GladHander = SuitPlan(
    SuitGlobals.GladHander,
    SuitType.C,
    Dept.SALES,
    'gladhander',
    height = 6.4,
    scale = 4.75,
    nametagZ = 6.7,
    levelRange = (4, 8),
    headShadowName = 'shadow28',
    headShadowScale = 1.1,
    headShadowPos = Vec3(0, 10, -0.04),
    gagWeaknesses = {GagGlobals.WholeFruitPie : 1.6},
    attacks = [SA_fountainpen, SA_filibuster, SA_schmooze, SA_rubberstamp],
    cls = SuitGlobals.COGCLASS_FOUR
)
NameDropper = SuitPlan(
    SuitGlobals.NameDropper,
    SuitType.A,
    Dept.SALES,
    'numbercruncher',
    height = 5.98,
    scale = 4.35,
    nametagZ = 6.3,
    headTex = 'phase_3.5/maps/namedropper.mat',
    levelRange = (3, 7),
    headShadowName = 'shadow27',
    headShadowScale = 1.0,
    headShadowPos = Vec3(0, 10, 0),
    gagWeaknesses = {GagGlobals.Anvil : 1.3},
    attacks = [SA_razzledazzle, SA_pickpocket], #synergy, rolodex
    cls = SuitGlobals.COGCLASS_THREE
)
Telemarketer = SuitPlan(
    SuitGlobals.Telemarketer,
    SuitType.B,
    Dept.SALES,
    'telemarketer',
    height = 5.24,
    scale = 3.75,
    nametagZ = 5.6,
    levelRange = (2, 6),
    headShadowName = 'shadow26',
    headShadowScale = 1.0,
    headShadowPos = Vec3(0, 10, 0),
    gagWeaknesses = {GagGlobals.Whistle : 1.2},
    attacks = [SA_clipontie, SA_pickpocket, SA_doubletalk], #rolodex
    cls = SuitGlobals.COGCLASS_JUNIOR
)
ColdCaller = SuitPlan(
    SuitGlobals.ColdCaller,
    SuitType.C,
    Dept.SALES,
    'coldcaller',
    height = 4.63,
    scale = 3.5,
    nametagZ = 4.9,
    headColor = VBase4(0.25, 0.35, 1.0, 1.0),
    handColor = VBase4(0.55, 0.65, 1.0, 1.0),
    levelRange = (1, 5),
    headShadowName = 'shadow25',
    headShadowScale = 1.15,
    headShadowPos = Vec3(0, 10, -0.01),
    gagWeaknesses = {GagGlobals.SquirtFlower : 1.4},
    attacks = [SA_doubletalk, SA_hotair], #poundkey, freezeassets
    cls = SuitGlobals.COGCLASS_GRUNT
)
# Bosses:
VicePresident = SuitPlan(
    SuitGlobals.VicePresident,
    SuitType.A,
    Dept.SALES,
    'phase_9/models/char/sellbotBoss-head-zero.bam',
    headAnims = {'neutral': 'phase_9/models/char/bossCog-head-Ff_neutral.bam'},
    height = 13.0,
    scale = 10.0,
    nametagZ = 14.0,
    levelRange = (70, 70),
    forcedVoice = Voice.BOSS
)
LucyCrossbill = SuitPlan(
    SuitGlobals.LucyCrossbill,
    SuitType.A,
    Dept.LAW,
    'legaleagle',
    scale = 7.125,
    height = 8.0,
    nametagZ = 8.75,
    handColor = VBase4(0.25, 0.25, 0.5, 1.0),
    levelRange = (80, 80),
    forcedVoice = Voice.BOSS
)

SuitIds = {
    0 : Flunky,
    1 : PencilPusher,
    2 : Yesman,
    3 : Micromanager,
    4 : Downsizer,
    5 : HeadHunter,
    6 : CorporateRaider,
    7 : TheBigCheese,
    8 : BottomFeeder,
    9 : Bloodsucker,
    10 : DoubleTalker,
    11 : AmbulanceChaser,
    12 : BackStabber,
    13 : SpinDoctor,
    14 : LegalEagle,
    15 : BigWig,
    16 : ShortChange,
    17 : PennyPincher,
    18 : Tightwad,
    19 : BeanCounter,
    20 : NumberCruncher,
    21 : MoneyBags,
    22 : LoanShark,
    23 : RobberBaron,
    24 : ColdCaller,
    25 : Telemarketer,
    26 : NameDropper,
    27 : GladHander,
    28 : MoverShaker,
    29 : TwoFace,
    30 : TheMingler,
    31 : MrHollywood,
    32 : VicePresident,
    33 : LucyCrossbill
}

totalSuits = SuitIds.values()

def getSuitById(suitId):
    return SuitIds.get(suitId)

def getIdFromSuit(suit):
    for suitId, iSuit in SuitIds.items():
        if iSuit == suit:
            return suitId

def getSuitByName(suitName):
    for suit in SuitIds.values():
        if suit.getName() == suitName:
            return suit

def getSuits():
    return totalSuits

def chooseLevelAndGetAvailableSuits(levelRange, dept, boss = False):
    import random

    availableSuits = []
    minLevel = levelRange[0]
    maxLevel = levelRange[1]

    if boss:
        minLevel = maxLevel

    level = random.randint(minLevel, maxLevel)
    for suit in getSuits():
        if level >= suit.getLevelRange()[0] and level <= suit.getLevelRange()[1] and suit.getDept() == dept:
            availableSuits.append(suit)

    return [level, availableSuits]
    
def precacheSuits():
    from src.coginvasion.cog import Variant
    from src.coginvasion.cog.Suit import Suit
    from src.coginvasion.base.Precache import precacheActor
    suit = Suit()
    for suitPlan in totalSuits:
        print("Precaching", suitPlan.name)
        suit.suitPlan = suitPlan
        suit.suit = suitPlan.getSuitType()
        suit.head = suitPlan.getHead()
        suit.dept = suitPlan.getDept()
        suit.handColor = suitPlan.getHandColor()
        suit.variant = Variant.NORMAL
        suit.level = 0
        suit.generateCog(nameTag = False)
        precacheActor(suit)
        suit.generateCog(isLose = 1, nameTag = False)
        precacheActor(suit)
    suit.disable()
    suit.delete()
