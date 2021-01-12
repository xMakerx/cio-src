"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file BSPBase.py
@author Maverick Liberty
@date January 11, 2021
@desc Derived from Brian's BSPBase in his singleplayer game.

"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.showbase.ShowBase import ShowBase

from .CogInvasionLoader import CogInvasionLoader
from .CIPostProcess import CIPostProcess

from src.coginvasion.settings.Setting import SHOWBASE_PREINIT, SHOWBASE_POSTINIT

from panda3d.core import CullBinManager, NodePath, OmniBoundingVolume, WindowProperties, LightRampAttrib
from panda3d.core import PandaSystem, loadPrcFile, loadPrcFileData, ConfigVariableString, ConfigVariableDouble
from libpandabsp import BSPShaderGenerator, VertexLitGenericSpec, LightmappedGenericSpec, UnlitGenericSpec, UnlitNoMatSpec, CSMRenderSpec, SkyBoxSpec, DecalModulateSpec

import builtins

SETTINGS_FILE_NAME          =        'settings.json'
PRC_FILE_DEV                =        'config_client.prc'
PRC_FILE_CLIENT             =        'config_client.prc'
LEGACY_TOONTOWN_RATIO       =        (4. / 3.) # The legacy stretched Toontown Online aspect ratio

class BSPBase(ShowBase):
    notify = directNotify.newCategory("BSPBase")

    def __init__(self, want_bsp = 1, want_input = 1):
        if hasattr(self, '__created'):
            self.notify.error('Cannot instantiate two instances of {0}!'.format(self.__name__))
            sys.exit(0)
            return

        self.__created = 1
        self.want_bsp = want_bsp
        self.want_input = want_input

        # Let's setup our BSPLoader
        self.bspLoader = Py_CL_BSPLoader()
        self.bspLoader.setGlobalPtr(self.bspLoader)

        # Let's setup our settings
        from src.coginvasion.settings.SettingsManager import SettingsManager
        self.settingsMgr = SettingsManager()

        try:
            self.notify.info('Loading {0}.'.format(SETTINGS_FILE_NAME))
            self.settingsMgr.loadFile(SETTINGS_FILE_NAME)
        except BaseException as e:
            self.notify.error('An error occurred while loading settings.')
            raise e

        self.settingsMgr.doSunriseFor(sunrise = SHOWBASE_PREINIT)

        builtins.getSetting = self.getSetting

        ShowBase.__init__(self)

        self._initLoader()
        self.makeAllPipes()

        self.cam.node().getDisplayRegion(0).setClearDepthActive(1)

        # Let's setup our graphics.
        from panda3d.core import RenderAttribRegistry, ShaderAttrib, \
            TransparencyAttrib
        from libpandabsp import BSPMaterialAttrib

        attrRegistry = RenderAttribRegistry.getGlobalPtr()
        if want_bsp: attrRegistry.setSlotSort(BSPMaterialAttrib.getClassSlot(), 0)
        attrRegistry.setSlotSort(ShaderAttrib.getClassSlot(), 1)
        attrRegistry.setSlotSort(TransparencyAttrib.getClassSlot(), 2)

        tickTaskName = '{0}._tick'.format(self.__name__)
        self.taskMgr.add(self._tick, tickTaskName, 100)

        # Let's setup our SettingsManager
        self.settingsMgr = SettingsManager()
        builtins.getSetting = self.getSetting

        self.shaderGenerator = None

        gsg = self.win.getGsg()

        # Let's print out our Graphics information.
        driverVendor = gsg.getDriverVendor()
        driverRenderer = gsg.getDriverRenderer()
        driverVersion = gsg.getDriverVersion()

        supportsCubeMap = gsg.getSupportsCubeMap()
        supports3dTextures = gsg.getSupports3dTexture()
        supportsBasicShaders = gsg.getSupportsBasicShaders()
        supportsGlsl = gsg.getSupportsGlsl()

        self.notify.info('Graphics Information:\n\tVendor: {0}\n\tRenderer: {1}\n\tVersion: {2}\n\tSupports Cube Maps: {3}\n\tSupports 3D Textures: {4}\n\tSupports Compute Shaders: {5}\n\tSupports Glsl{6}'
                            .format(driverVendor, driverRenderer, driverVersion, supportsCubeMap, supports3dTextures, supportsBasicShaders, supportsGlsl))

        # Enable shader generation, if supported, on all main scenes.
        if supportsBasicShaders:
            for scene in range([render, render2d, render2dp]):
                scene.setShaderAuto()
            self.notify.debug('Enabled automatic shaders on all scenes.')
        else:
            self.notify.error('Graphics driver is too out of date to run the game.')
            return
            
        def __fixPlatformIssues():
            if driverVendor == "Intel":
                metadata.NO_FOG = 1
                self.notify.info("Applied Intel-specific graphical fix.")

            self.win.disableClears()

        if True: __fixPlatformIssues()

        # Let's setup our camera bitmasks
        from src.coginvasion.globals.CIGlobals import MainCameraBitmask, ShadowCameraBitmask, DefaultBackgroundColor
        self.camNode.setCameraMask(MainCameraBitmask)
        render.show(ShadowCameraBitmask)

        from direct.distributed.ClockDelta import globalClockDelta
        builtins.globalClockDelta = globalClockDelta

        # Let's setup our bins
        cbm = CullBinManager.getGlobalPtr()
        cbm.addBin('ground', CullBinManager.BTUnsorted, 18)

        # The portal/teleport hole uses the shadow bin by default, but we still want to see it with real shadows.
        cbm.addBin('portal', CullBinManager.BTBackToFront, 19)
        if metadata.USE_REAL_SHADOWS:
            cbm.addBin('shadow', CullBinManager.BTFixed, -100)
        else:
            cbm.addBin('shadow', CullBinManager.BTBackToFront, 19)
        cbm.addBin('gui-popup', CullBinManager.BTUnsorted, 60)
        cbm.addBin('gsg-popup', CullBinManager.BTFixed, 70)

        self.setBackgroundColor(DefaultBackgroundColor)
        self.disableMouse()
        self.enableParticles()

        self.settingsMgr.doSunriseFor(sunrise = SHOWBASE_POSTINIT)

        # Let's initialize our shaders
        try:
            self._initializeShaders()
        except Exception as e:
            self.notify.error('Failed to initialize shaders. Exception: {0}'.format(str(e)))
            raise e

    def onSuccessfulStart(self):
        ConfigVariableDouble('decompressor-step-time').setValue(0.01)
        ConfigVariableDouble('extractor-step-time').setValue(0.01)

        from src.coginvasion.globals.CIGlobals import getToonFont
        toonFont = getToonFont

        from direct.gui import DirectGuiGlobals as DGG
        DGG.setDefaultFontFunc(toonFont)
        DGG.setDefaultFont(toonFont())

        rlvrSfx = loader.loadSfx('phase_3/audio/sfx/GUI_rollover.ogg')
        clickSfx = loader.loadSfx('phase_3/audio/sfx/GUI_create_toon_fwd.ogg')
        DGG.setDefaultRolloverSound(rlvrSfx)
        DGG.setDefaultClickSound(clickSfx)
        DGG.setDefaultDialogGeom(loader.loadModel('phase_3/models/gui/dialog_box_gui.bam'))

        from src.coginvasion.nametag import NametagGlobals
        from src.coginvasion.margins.MarginManager import MarginManager
        from src.coginvasion.globals import ChatGlobals

        ChatGlobals.loadWhiteListData()
        NametagGlobals.setMe(base.cam)
        NametagGlobals.setCardModel('phase_3/models/props/panel.bam')
        NametagGlobals.setArrowModel('phase_3/models/props/arrow.bam')
        NametagGlobals.setChatBalloon3dModel('phase_3/models/props/chatbox.bam')
        NametagGlobals.setChatBalloon2dModel('phase_3/models/props/chatbox_noarrow.bam')
        NametagGlobals.setThoughtBalloonModel('phase_3/models/props/chatbox_thought_cutout.bam')
        chatButtonGui = loader.loadModel('phase_3/models/gui/chat_button_gui.bam')
        NametagGlobals.setPageButton(chatButtonGui.find('**/Horiz_Arrow_UP'), chatButtonGui.find('**/Horiz_Arrow_DN'),
                                     chatButtonGui.find('**/Horiz_Arrow_Rllvr'), chatButtonGui.find('**/Horiz_Arrow_UP'))
        NametagGlobals.setQuitButton(chatButtonGui.find('**/CloseBtn_UP'), chatButtonGui.find('**/CloseBtn_DN'),
                                     chatButtonGui.find('**/CloseBtn_Rllvr'), chatButtonGui.find('**/CloseBtn_UP'))
        NametagGlobals.setRolloverSound(rlvrSfx)
        NametagGlobals.setClickSound(clickSfx)

    def __setattr__(self, name, value):
        if name == 'hdrToggle':
            curVal = super(BSPBase, self).__getattribute__(name, None)

            if not curVal == value:
                # Their value changed!

                if value is True:
                    # Don't clamp lighting calculations with hdr.
                    render.setAttrib(LightRampAttrib.makeIdentity())
                else:
                    render.setAttrib(LightRampAttrib.makeDefault())

        super(BSPBase, self).__setattr__(name, value)

    def _initializeShaders(self):
        if not hasattr(self, 'shaderGenerator') or (hasattr(self, 'shaderGenerator') and self.shaderGenerator is None):
            gsg = self.win.getGsg()
            self.shaderGenerator = BSPShaderGenerator(self.win, gsg, self.camera, self.render)
            gsg.setShaderGenerator(self.shaderGenerator)

            for shader in self._getEnabledShaders():
                self.shaderGenerator.addShader(shader)

            self.shaderGenerator.setShaderQuality(self.getSetting("shaderquality").getValue())

            self.filters = CIPostProcess()
            self.filters.startup(self.win)
            self.filters.addCamera(self.cam)
            self.filters.setup()

            self.bloomToggle = False
            self.hdrToggle = False
            self.fxaaToggle = self.getSetting("aa").getValue() == "FXAA"
            self.aoToggle = False

    def _getEnabledShaders(self):
        return [
            VertexLitGenericSpec(),
            UnlitGenericSpec(),
            LightmappedGenericSpec(),
            UnlitNoMatSpec(),
            CSMRenderSpec(),
            SkyBoxSpec(),
            DEcalModulateSpec()
        ]

    def setupRender(self):
        if self.want_bsp:
            self.setupBSPRender()
            return

        # We don't want BSP
        super(BSPBase, self).setupRender()

    def setupBSPRender(self):
        """
        Creates the root of the 3D scene graph which supports BSP levels.
        """

        if BSPLoader.getGlobalPtr() is None:
            # We need to setup the BSPLoader.
            pass

        self.render = NodePath(BSPRender('render', BSPLoader.getGlobalPtr()))
        self.render.setAttrib(RescaleNormalAttrib.makeDefault())
        self.render.setTwoSided(0)

        self.backfaceCullingEnabled = 1
        self.textureEnabled = 1
        self.wireframeEnabled = 0

    def _tick(self, task):
        # Let's "tick" things that need to tick
        entitiesToTick = ['shaderGenerator', 'filters', 'audio3d']

        for entity in entitiesToTick:
            member = getattr(self, entity, None)
            if hasattr(self, entity) and member is not None:
                member.update()

                if entity == 'filters':
                    member.windowEvent()

        return task.cont

    def renderFrames(self):
        for _ in range(2):
            self.graphicsEngine.renderFrame()

    def setMouseVisible(self, flag):
        props = WindowProperties()
        props.setCursorHidden(flag)
        self.win.requestProperties(props)

    def _initLoader(self):
        if not isinstance(self.loader, CogInvasionLoader):
            self.loader.destroy()
        self.loader = CogInvasionLoader(self)
        self.graphicsEngine.setDefaultLoader(self.loader.loader)
        builtins.loader = self.loader

    """
    Quickly fetch a setting.
    Pass the name of the setting.
    """

    def getSetting(self, settingName):
        if hasattr(self, 'settingsMgr'):
            if settingName in list(self.settingsMgr.registry.keys()):
                return self.settingsMgr.getSetting(settingName)
            else:
                self.notify.error("SettingsManager does not have a Setting called \"{0}\"".format(settingName))
        
        self.notify.error("SettingsManager isn't defined!")
        return None

    def getGraphicsLibrary():
        lib = self.config.GetString('load-display')

        if lib == 'pandagl':
            return 'OpenGL'
        elif 'pandadx' in lib:
            return 'DirectX {0}'.format(str(lib.replace('pandadx', '')))
        
        return lib

    def getAudioLibrary():
        return self.config.GetString('audio-library-name').replace('p3', '').replace('_audio', '')


if __name__ == "__main__":
    from src.coginvasion.base.Metadata import Metadata
    metadata = Metadata()
    builtins.metadata = metadata
    builtins.meta = metadata

    print('Starting Open Cog Invasion Online {0} with Panda3D version: {1}...'.format(metadata.getBuildInformation(), PandaSystem.getVersionString()))

    try:
        loadPrcFile('config/{0}'.format(PRC_FILE_DEV))
        loadPrcFile('config/Confauto.prc')

        # Let's mount our resources directly
        loadPrcFileData('', 'model-path ./resources')

        metadata.IS_PRODUCTION = 0
        print('Running development environment')

        # We could enable some fun stuff or something
    except:
        import aes
        import config
        # Config
        prc = config.CONFIG
        iv, key, prc = prc[:16], prc[16:32], prc[32:]
        prc = aes.decrypt(prc, key, iv)
        for line in prc.split('\n'):
            line = line.strip()
            if line:
                loadPrcFileData('coginvasion config', line)
        print('Running Production')

    metadata.MULTITHREADED_PIPELINE = int(ConfigVariableString('threading-model', '').getValue() == 'Cull/Draw')

    base = BSPBase()
    builtins.base = BSPBase()

    if base.win is None:
        # Something went wrong!
        print('Failed to start the game! Did you install it correctly?')
        sys.exit()

    # Enable admin commands
    import src.coginvasion.distributed.AdminCommands

    print('Rendering Engine: {0}, Sound Library: {1}'.format(base.getGraphicsLibrary(), base.getAudioLibrary()))
    base.onSuccessfulStart()

