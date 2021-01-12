"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file LevelLoader.py
@author Maverick Liberty
@date January 11, 2021

@desc Wraps around BSPLoader

"""

from direct.directnotify.DirectNotifyGlobal import directNotify

from libpandabsp import Py_CL_BSPLoader, BSPLoader, BSPMaterialAttrib, BSPMaterial

MATERIALS_FILE          =          'phase_14/etc/materials.txt'
UNLIT_MATERIAL          =          'phase_14/materials/unlit.mat'
UNLIT_NOMATERIAL        =          'phase_14/materials/unlit_nomat.mat' 
GAMMA_LEVEL             =          2.2

class LevelLoader(Py_CL_BSPLoader):
    notify = directNotify.newCategory('LevelLoader')

    def __init__(self):
        Py_CL_BSPLoader.__init__(self)
        BSPLoader.setGlobalPtr(self)

        self.level = None
        self.brushCollisionMaterialData = {}

        self.setGamma(GAMMA_LEVEL)
        self.setMaterialsFile(MATERIALS_FILE)
        self.setVisible(True)

    def loadLevel(self, levelFile):
        self.cleanupLevel()

        try:
            self.read(levelFile)
            self.level = self.getResult()
            self.doOptimizations()
            self.notify.debug('Successfully loaded Level {0}!'.format(levelFile))
        except Exception as e:
            self.notify.error('Failed to load Level {0}. Exception: {1}'.format(levelFile, str(e)))

        if self.level is not None:
            for prop in self.level.findAllMatches('**/+BSPProp'):
                # TODO: ENABLE PHYSICS
                pass

            # Let's determine what sky to use.
            skyType = 1

            try:
                skyType = base.cr.playGame.hood.olc.skyType # I really hate this way of doing things
            except:
                try:
                    skyType = int(self.level.getCEntity(0).getEntityValue("skytype"))
                except: pass

            gsg = base.win.getGsg()
            if skyType != OutdoorLightingConfig.STNone and gsg.getSupportsCubeMap():
                cubemap = loader.loadCubemap(OutdoorLightingConfig.SkyData[skyType][2])
                base.shaderGenerator.setIdentityCubemap(cubemap)
                self.notify.debug('Initialized level cubemap.')
            elif not gsg.getSupportsCubeMap():
                self.notify.debug('Refused to load cubemap because of graphics card incompatibility.')
                # TODO: Maybe load geometric sky?

            # Let's cache our scene.

    def getLightEnvironmentData(self):
        # [has data, angles, color]
        data = [0, Vec3(0), Vec4(0)]

        if self.hasActiveLevel():
            for i in range(self.getNumEntities()):
                className = self.getEntityValue(i, 'classname')

                if className == 'light_environment':
                    angles = self.getEntityValueVector(i, 'angles')
                    lightColor = self.getEntityValueColor(i, '_light')

                    data[0] = 1
                    data[1] = self.convertHammerAngles(angles)
                    data[2] = lightColor
                    break

        return data

    def convertHammerAngles(self, angles):
        """
        (pitch, yaw + 90, roll) -> (yaw, pitch, roll)
        """

        temp = angles[0]
        angles[0] = angles[1] - 90
        angles[1] = temp
        return angles

    def cleanupLevel(self):
        if self.level:
            # TODO: Cleanup physics meshes.
            self.level.removeNode()
            self.level = None
        super(LevelLoader, self).cleanup()
        self.brushCollisionMaterialData = {}

    def getMaterialFile(self, filepath):
        """ Fetches a material file using a string filepath """
        return BSPMaterial.getFromFile(str(filepath))

    def getUnlitMaterial(self):
        if isinstance(UNLIT_MATERIAL, str):
            # We haven't loaded the material file yet, do that.
            UNLIT_MATERIAL = self.getMaterialFile(UNLIT_MATERIAL)
        return UNLIT_MATERIAL

    def getUnlitNoMaterial(self):
        if isinstance(UNLIT_NOMATERIAL, str):
            # We haven't loaded the material file yet, do that.
            UNLIT_NOMATERIAL = self.getMaterialFile(UNLIT_NOMATERIAL)
        return UNLIT_NOMATERIAL

    def applyOverrideShader(self, nodepath, overrideShader):
        """ Tries to apply the specified override shader to the specified geometry. """

        gsg = base.win.getGsg()
        shaderName = 'missingNo'
        nodeName = 'missingNo' if nodepath is None or (not nodepath is None and nodepath.isEmpty()) else nodepath.getName()

        try:
            shaderName = str(overrideShader)
        except: pass

        if not gsg.getSupportsBasicShaders():
            self.notify.warning('System graphics card does not support basic shaders. Cannot apply Shader {0} to NodePath {1}.'.format(shaderName, nodeName))
            return
        
        nodepath.setAttrib(BSPMaterialAttrib.makeOverrideShader(overrideShader))

    def applyUnlitMaterial(self, nodepath):
        self.applyOverrideShader(nodepath, self.getUnlitMaterial())

    def applyUnlit(self, nodepath):
        self.applyOverrideShader(nodepath, self.getUnlitNoMaterial())

    def setVisible(self, flag):
        if isinstance(flag, int):
            flag = bool(flag)

        self.setWantVisibility(flag)

    def cleanup(self):
        Py_CL_BSPLoader.cleanup(self)
        self.cleanupLevel()





