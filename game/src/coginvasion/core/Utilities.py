"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file Utilities.py
@author Maverick Liberty
@date January 12, 2021

@desc Moves useful methods, variables, etc here to be used by base.

"""

class maths:

    def angleVectors(self, angles, forward = False, right = False, up = False):
        """
        Get basis vectors for the angles.
        Each vector is optional.
        """

        if forward or right or up:
            sh = math.sin(deg2Rad(angles[0]))
            ch = math.cos(deg2Rad(angles[0]))
            sp = math.sin(deg2Rad(angles[1]))
            cp = math.cos(deg2Rad(angles[1]))
            sr = math.sin(deg2Rad(angles[2]))
            cr = math.cos(deg2Rad(angles[2]))

        result = []
        if forward:
            forward = Vec3(cp*ch,
                           cp*sh,
                           -sp)
            result.append(forward)
        if right:
            right = Vec3(-1*sr*sp*ch+-1*cr*-sh,
                         -1*sr*sp*sh+-1*cr*ch,
                         -1*sr*cp)
            result.append(right)
        if up:
            up = Vec3(cr*sp*ch+-sr*-sh,
                      cr*sp*sh+-sr*ch,
                      cr*cp)
            result.append(up)

        return result

    def vecToYaw(self, vec):
        return rad2Deg(math.atan2(vec[1], vec[0])) - 90

    def angleMod(self, a):
        return a % 360

    def angleDiff(self, destAngle, srcAngle):

        delta = destAngle - srcAngle

        if destAngle > srcAngle:
            if delta >= 180:
                delta -= 360
        else:
            if delta <= -180:
                delta += 360

        return delta

    def putVec3(self, dg, vec):
        from panda3d.direct import STFloat64
        dg.putArg(vec[0], STFloat64)
        dg.putArg(vec[1], STFloat64)
        dg.putArg(vec[2], STFloat64)

    def getVec3(self, dgi):
        from panda3d.direct import STFloat64
        x = dgi.getArg(STFloat64)
        y = dgi.getArg(STFloat64)
        z = dgi.getArg(STFloat64)
        return Vec3(x, y, z)

    def remapVal(self, val, A, B, C, D):
        if A == B:
            return D if val >= B else C
        
        return C + (D - C) * (val - A) / (B - A)
    
    def clamp(self, val, A, B):
        return max(A, min(B, val))

    def lerpWithRatio(self, v0, v1, ratio):
        dt = globalClock.getDt()
        amt = 1 - math.pow(1 - ratio, dt * 30.0)
        return lerp(v0, v1, amt)

    def lerp(self, v0, v1, amt):
        return v0 * amt + v1 * (1 - amt)

    # Helper method to check if two objects are facing each other like so: -> <-
    def areFacingEachOther(self, obj1, obj2):
        h1 = obj1.getH(render) % 360
        h2 = obj2.getH(render) % 360
        return not (-90.0 <= (h1 - h2) <= 90.0)

class strings:

    def toSingular(self, noun):
        """ Makes a plural noun singular. """
        pluralSuffixes = ['ies', 'es', 's']
    
        for suffix in pluralSuffixes:
            if noun.endswith(suffix):
                return noun[:-len(suffix)]

        return noun

    def toPlural(self, noun):
        """ Makes a noun string plural. Follows grammar rules with nouns ending in 'y' and 's'. Assumes noun is singular beforehand. """
        withoutLast = noun[:-1]
    
        if noun.endswith('y'):
            return '{0}ies'.format(withoutLast)
        elif noun.endswith('s'):
            return '{0}es'.format(withoutLast)
        else:
            return '{0}s'.format(noun)
    
    def toPastTense(self, noun):
        """ Makes a noun string past tense. """    
        withoutLast = noun[:-1]
        secondToLast = noun[-2:]
        lastChar = noun[-1:]

        if noun.endswith('y'):
            return '{0}ied'.format(withoutLast)
        elif not (noun.endswith('w') or noun.endswith('y')) and secondToLast in self.getVowels() and lastChar in self.getConsonants():
            # When a noun ends with a vowel then a consonant, we double the consonant and add -ed."
            return '{0}{1}ed'.format(noun, secondToLast)
        else:
            return '{0}ed'.format(noun)
    
    def getVowels(self):
        """ Returns a list of vowels """
        return ['a', 'e', 'i', 'o', 'u']

    def getConsonants(self):
        """ Returns a list of consonants """
        return ['b', 'c', 'd', 'f', 'g', 
                'h', 'j', 'k', 'l', 'm', 
                'n', 'p', 'q', 'r', 's', 
                't', 'v', 'w', 'x', 'y', 
        'z']

    def getAmountString(self, noun, amount):
        """ Returns a grammatically correct string stating the amount of something. E.g: An elephant horn, 5 packages, etc. """
    
        if amount > 1:
            return "{0} {1}".format(amount, self.toPlural(noun))
        else:
            firstChar = noun[1:]

            if firstChar in self.getVowels():
                # If the noun begins with a vowel, we use 'an'.
                return 'An {0}'.format(noun)
        
            return 'A {0}'.format(noun)
    
    def empty(string):
        """ Returns whether or not a string is empty. """
        return not (string and string.strip())

ANISOTROPIC_FILTERING_TASK_NAME = 'ApplyAnisotropicFiltering'

def __applyAF(task):
    degree = base.getSetting('af').getValue()

    for tex in render.findAllTextures():
        if tex.getAnisotropicDegree() != degree:
            tex.setAnisotropicDegree(degree)
    return task.done

def enableAntisotropicFiltering():
    if base.taskMgr.hasTaskNamed(ANISOTROPIC_FILTERING_TASK_NAME):
        return
    base.taskMgr.add(__applyAF, ANISOTROPIC_FILTERING_TASK_NAME)

def disableAntisotropicFiltering():
    if base.taskMgr.hasTaskNamed(ANISOTROPIC_FILTERING_TASK_NAME):
        base.taskMgr.removeTask(ANISOTROPIC_FILTERING_TASK_NAME)
