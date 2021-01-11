"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file DistributedDeliveryTruck.py
@author Brian Lach
@date October 4, 2015

"""

from panda3d.core import CollisionSphere, CollisionNode

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedNode import DistributedNode
from direct.showutil.Rope import Rope

from src.coginvasion.globals import CIGlobals

class DistributedDeliveryTruck(DistributedNode):
    notify = directNotify.newCategory('DistributedDeliveryTruck')

    
    

    def __init__(self, cr):
        DistributedNode.__init__(self, cr)
        self.kart = None
        self.rope = None
        self.pod = None
        self.barrels = []
        self.numBarrels = 0
        self.triggerNP = None
        self.mg = None

    def setNumBarrels(self, num):
        self.numBarrels = num
        self.__generateBarrels()

    def getNumBarrels(self):
        return self.numBarrels

    def __removeAllBarrels(self):
        for barrel in self.barrels:
            barrel.removeNode()
        self.barrels = []

    def __generateBarrels(self):
        self.__removeAllBarrels()
        for i in range(self.numBarrels):
            point = self.barrelpoints[i]
            barrel = loader.loadModel('phase_4/models/cogHQ/gagTank.bam')
            barrel.setScale(self.barrelscale)
            barrel.setPos(point)
            barrel.setH(180)
            barrel.reparentTo(self)
            self.barrels.append(barrel)

    def __handleTruckTrigger(self, entry):
        if not base.localAvatar.hasBarrel:
            self.sendUpdate('requestBarrel')

    def announceGenerate(self):
        DistributedNode.announceGenerate(self)
        self.kart = loader.loadModel('phase_6/models/karting/Kart3_Final.bam')
        self.kart.find('**/decals').removeNode()
        self.kart.reparentTo(self)
        self.pod = loader.loadModel('phase_4/models/minigames/pods_truck.egg')
        self.pod.reparentTo(self)
        self.pod.setScale(0.2)
        self.pod.setY(8.5)
        self.pod.setH(180)
        self.pod.find('**/metal_ramp').setBin('ground', 18)
        self.pod.find('**/metal_ramp_coll').setCollideMask(CIGlobals.FloorBitmask)
        self.rope = Rope()
        self.rope.ropeNode.setUseVertexColor(1)
        self.rope.setup(3, ({'node': self.kart, 'point': (0, 1.5, 0.7), 'color': (0, 0, 0, 1), 'thickness': 1000},
         {'node': self.kart, 'point': (0, 1.5, 0.7), 'color': (0, 0, 0, 1), 'thickness': 1000},
         {'node': self.pod, 'point': (0, 31, 5), 'color': (0, 0, 0, 1), 'thickness': 1000}), [])
        self.rope.setH(180)
        self.rope.reparentTo(self)
        sphere = CollisionSphere(0, 0, 0, 2)
        sphere.setTangible(0)
        node = CollisionNode(self.uniqueName('truck_trigger'))
        node.addSolid(sphere)
        node.setCollideMask(CIGlobals.WallBitmask)
        self.triggerNP = self.attachNewNode(node)
        self.triggerNP.setPos(0, 8.0, 2.0)
        self.setScale(2.0)

        self.accept('enter' + self.triggerNP.node().getName(), self.__handleTruckTrigger)

    def disable(self):
        self.ignore('enter' + self.triggerNP.node().getName())
        self.__removeAllBarrels()
        self.barrels = None
        self.numBarrels = None
        if self.rope:
            self.rope.removeNode()
            self.rope = None
        if self.pod:
            self.pod.removeNode()
            self.pod = None
        if self.kart:
            self.kart.removeNode()
            self.kart = None
        self.mg = None
        DistributedNode.disable(self)
