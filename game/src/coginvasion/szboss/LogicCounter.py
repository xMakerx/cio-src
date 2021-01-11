from .Entity import Entity

class LogicCounter(Entity):

    def __init__(self, air = None, dispatch = None):
        Entity.__init__(self)
        self.startVal = 0
        self.maxVal = 1
        self.minVal = 0
        self.val = 0
        
    def cleanup(self):
        self.startVal = None
        self.maxVal = None
        self.minVal = None
        self.val = None
        Entity.cleanup(self)
        
    def CountUp(self):
        if self.val == self.maxVal:
            return
            
        oldVal = self.val
        self.val += 1
        if oldVal == self.minVal:
            self.dispatchOutput("OnLoseMin")
        if self.val == self.maxVal:
            self.dispatchOutput("OnHitMax")
        
    def CountDown(self):
        
        if self.val == self.minVal:
            return
            
        oldVal = self.val
        self.val -= 1
        if oldVal == self.maxVal:
            self.dispatchOutput("OnLoseMax")
        if self.val == self.minVal:
            self.dispatchOutput("OnHitMin")
        
    def load(self):
        self.cEntity = self.bspLoader.getCEntity(self.entnum)
        Entity.load(self)
        self.startVal = self.getEntityValueInt("startVal")
        self.maxVal = self.getEntityValueInt("maxVal")
        self.minVal = self.getEntityValueInt("minVal")
        
        self.val = self.startVal
