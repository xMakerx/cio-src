"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file Core.py
@author Maverick Liberty
@date January 11, 2021
@desc Derived from Brian's BSPBase in his singleplayer game.

"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.showbase.ShowBase import ShowBase

from . import Localizer
from .Utilities import maths, strings
from .AssetLoader import AssetLoader
from .PostProcessingEffects import PostProcessingEffects

from src.coginvasion.manager.UserInputStorage import UserInputStorage
from src.coginvasion.globals.CIGlobals import DefaultCameraNear, DefaultCameraFar
from src.coginvasion.settings.Setting import SHOWBASE_PREINIT, SHOWBASE_POSTINIT

from panda3d.core import CullBinManager, NodePath, OmniBoundingVolume, WindowProperties, LightRampAttrib, RescaleNormalAttrib
from panda3d.core import PandaSystem, loadPrcFile, loadPrcFileData, ConfigVariableString, ConfigVariableDouble

from panda3d.core import loadPrcFile, NodePath, PGTop, TextPropertiesManager, TextProperties, Vec3, MemoryUsage, MemoryUsagePointers, RescaleNormalAttrib
from panda3d.core import CollisionHandlerFloor, CollisionHandlerQueue, CollisionHandlerPusher, loadPrcFileData, TexturePool, ModelPool, RenderState, Vec4, Point3
from panda3d.core import CollisionTraverser, CullBinManager, LightRampAttrib, Camera, OmniBoundingVolume, Texture, GraphicsOutput, PStatCollector, PerspectiveLens, ModelNode, BitMask32, OrthographicLens
from panda3d.core import FrameBufferProperties, WindowProperties

from libpandabsp import BSPShaderGenerator, BSPRender

import builtins

SETTINGS_FILE_NAME          =        'settings.json'
PRC_FILE_DEV                =        'config_dev.prc'
PRC_FILE_CLIENT             =        'config_client.prc'
LEGACY_TOONTOWN_RATIO       =        (4. / 3.) # The legacy stretched Toontown Online aspect ratio

class Core(ShowBase):
    notify = directNotify.newCategory('Core')

    def __init__(self, want_bsp = 1, want_input = 1):
        self.notify.setInfo(True)
        if hasattr(self, '__created'):
            self.notify.error('Cannot instantiate two instances of Core!')
            sys.exit(0)
            return

        self.__created = 1
        self.setup = False
        self.bspLoader = None

        if want_bsp:
            from src.coginvasion.core.LevelLoader import LevelLoader
            self.bspLoader = LevelLoader()

        if want_input:
            self.input = UserInputStorage()
            self.inputStore = self.input
            builtins.uis = self.input
            builtins.inputStore = self.input

        self.want_bsp = want_bsp
        self.want_input = want_input

        # Let's add our helper utility pointers
        self.math = maths()
        self.strings = strings()
        self.language = Localizer

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
        self.camLens.setNearFar(DefaultCameraNear, DefaultCameraFar)
        #self.win.disableClears()

        render.hide()
        self.bspLoader.setWin(self.win)
        self.bspLoader.setCamera(self.camera)
        self.bspLoader.setRender(self.render)

        # Let's setup our graphics.
        from panda3d.core import RenderAttribRegistry, ShaderAttrib, \
            TransparencyAttrib

        attrRegistry = RenderAttribRegistry.getGlobalPtr()

        if want_bsp:
            from libpandabsp import BSPMaterialAttrib
            attrRegistry.setSlotSort(BSPMaterialAttrib.getClassSlot(), 0)

        attrRegistry.setSlotSort(ShaderAttrib.getClassSlot(), 1)
        attrRegistry.setSlotSort(TransparencyAttrib.getClassSlot(), 2)

        tickTaskName = 'Core._tick'
        self.taskMgr.add(self._tick, tickTaskName, 47)

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

        self.notify.info('Graphics Information:\n\tVendor: {0}\n\tRenderer: {1}\n\tVersion: {2}\n\tSupports Cube Maps: {3}\n\tSupports 3D Textures: {4}\n\tSupports Compute Shaders: {5}\n\tSupports Glsl: {6}'
                            .format(driverVendor, driverRenderer, driverVersion, supportsCubeMap, supports3dTextures, supportsBasicShaders, supportsGlsl))

        # Enable shader generation, if supported, on all main scenes.
        if supportsBasicShaders:
            for scene in [render, render2d, render2dp]:
                scene.setShaderAuto()
            self.notify.debug('Enabled automatic shaders on all scenes.')
        else:
            self.notify.error('Graphics driver is too out of date to run the game.')
            return

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
        #self.disableMouse()
        self.enableParticles()

        self.settingsMgr.doSunriseFor(sunrise = SHOWBASE_POSTINIT)

        # Let's initialize our shaders
        try:
            from panda3d.core import VirtualFileSystem, Filename
            vfs = VirtualFileSystem.getGlobalPtr()
            vfs.chdir(Filename('resources'))

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

        self.setup = True

    def makeCamera(self, win, sort = 0, scene = None,
                   displayRegion = (0, 1, 0, 1), stereo = None,
                   aspectRatio = None, clearDepth = 0, clearColor = None,
                   lens = None, camName = 'cam', mask = None,
                   useCamera = None):
        """
        Makes a new 3-d camera associated with the indicated window,
        and creates a display region in the indicated subrectangle.

        If stereo is True, then a stereo camera is created, with a
        pair of DisplayRegions.  If stereo is False, then a standard
        camera is created.  If stereo is None or omitted, a stereo
        camera is created if the window says it can render in stereo.

        If useCamera is not None, it is a NodePath to be used as the
        camera to apply to the window, rather than creating a new
        camera.
        """
        # self.camera is the parent node of all cameras: a node that
        # we can move around to move all cameras as a group.
        if self.camera == None:
            # We make it a ModelNode with the PTLocal flag, so that
            # a wayward flatten operations won't attempt to mangle the
            # camera.
            self.camera = self.render.attachNewNode(ModelNode('camera'))
            self.camera.node().setPreserveTransform(ModelNode.PTLocal)
            builtins.camera = self.camera

            self.mouse2cam.node().setNode(self.camera.node())

        if useCamera:
            # Use the existing camera node.
            cam = useCamera
            camNode = useCamera.node()
            assert(isinstance(camNode, Camera))
            lens = camNode.getLens()
            cam.reparentTo(self.camera)

        else:
            # Make a new Camera node.
            camNode = Camera(camName)
            if lens == None:
                lens = PerspectiveLens()

                if aspectRatio == None:
                    aspectRatio = self.getAspectRatio(win)
                lens.setAspectRatio(aspectRatio)

            cam = self.camera.attachNewNode(camNode)

        if lens != None:
            camNode.setLens(lens)

        if scene != None:
            camNode.setScene(scene)

        if mask != None:
            if (isinstance(mask, int)):
                mask = BitMask32(mask)
            camNode.setCameraMask(mask)

        if self.cam == None:
            self.cam = cam
            self.camNode = camNode
            self.camLens = lens

        self.camList.append(cam)

        # Now, make a DisplayRegion for the camera.
        if stereo is not None:
            if stereo:
                dr = win.makeStereoDisplayRegion(*displayRegion)
            else:
                dr = win.makeMonoDisplayRegion(*displayRegion)
        else:
            dr = win.makeDisplayRegion(*displayRegion)

        dr.setSort(sort)

        dr.disableClears()

        # By default, we do not clear 3-d display regions (the entire
        # window will be cleared, which is normally sufficient).  But
        # we will if clearDepth is specified.
        if clearDepth:
            dr.setClearDepthActive(1)

        if clearColor:
            dr.setClearColorActive(1)
            dr.setClearColor(clearColor)

        dr.setCamera(cam)

        return cam

    def makeCamera2d(self, win, sort = 10,
                     displayRegion = (0, 1, 0, 1), coords = (-1, 1, -1, 1),
                     lens = None, cameraName = None):
        """
        Makes a new camera2d associated with the indicated window, and
        assigns it to render the indicated subrectangle of render2d.
        """
        dr = win.makeMonoDisplayRegion(*displayRegion)
        dr.setSort(sort)
        dr.disableClears()

        # Make any texture reloads on the gui come up immediately.
        dr.setIncompleteRender(False)

        left, right, bottom, top = coords

        # Now make a new Camera node.
        if (cameraName):
            cam2dNode = Camera('cam2d_' + cameraName)
        else:
            cam2dNode = Camera('cam2d')

        if lens == None:
            lens = OrthographicLens()
            lens.setFilmSize(right - left, top - bottom)
            lens.setFilmOffset((right + left) * 0.5, (top + bottom) * 0.5)
            lens.setNearFar(-1000, 1000)
        cam2dNode.setLens(lens)

        # self.camera2d is the analog of self.camera, although it's
        # not as clear how useful it is.
        if self.camera2d == None:
            self.camera2d = self.render2d.attachNewNode('camera2d')

        camera2d = self.camera2d.attachNewNode(cam2dNode)
        dr.setCamera(camera2d)

        if self.cam2d == None:
            self.cam2d = camera2d

        return camera2d

    def __setattr__(self, name, value):
        # This has to be here or ShowBase will get messed up during initialization.
        if not hasattr(self, 'setup') or (hasattr(self, 'setup') and not self.setup): 
            super().__setattr__(name, value)
            return

        changed = False
        curVal = getattr(self, name, 'missingNo')

        if (curVal != 'missingNo' and not value == curVal):
            changed = True
        if name == 'hdrToggle':
            if changed or curVal == 'missingNo':
                # Their value changed!

                if value is True:
                    # Don't clamp lighting calculations with hdr.
                    render.setAttrib(LightRampAttrib.makeIdentity())
                else:
                    render.setAttrib(LightRampAttrib.makeDefault())

        super().__setattr__(name, value)

        if hasattr(builtins, 'messenger'):
            # Propagates an event for when a value changes
            messenger.send(self.getAttributeChangedEventName(name), [curVal, value])

    def adjustWindowAspectRatio(self, aspectRatio=None):
        maintainRatio = self.getSetting('maspr')
        if maintainRatio is not None:
            aspectRatio = LEGACY_TOONTOWN_RATIO if not maintainRatio.getValue() else aspectRatio

        ShowBase.adjustWindowAspectRatio(self, aspectRatio)
        #self.credits2d.setScale(1.0 / aspectRatio, 1.0, 1.0)

    def _initializeShaders(self):
        from src.coginvasion.globals.CIGlobals import ComputeCameraBitmask
        from panda3d.core import OmniBoundingVolume, NodePath
        if self.shaderGenerator is None:
            gsg = self.win.getGsg()
            self.shaderGenerator = BSPShaderGenerator(self.win, gsg, self.camera, self.render)

            self.win.getGsg().setShaderGenerator(self.shaderGenerator)

            for shader in self._getEnabledShaders():
                self.shaderGenerator.addShader(shader)

            self.shaderGenerator.setShaderQuality(self.getSetting("shaderquality").getValue())

            self.bloomToggle = False
            self.hdrToggle = False
            self.fxaaToggle = self.getSetting("aa").getValue() == "FXAA"
            self.aoToggle = False


            self.filters = PostProcessingEffects()
            self.filters.startup(self.win)
            self.filters.addCamera(self.cam)
            self.filters.setup()

            self.computeRoot = NodePath('computeRoot')
            self.computeCam = self.makeCamera(base.win)
            self.computeCam.node().setCameraMask(ComputeCameraBitmask)
            self.computeCam.node().setCullBounds(OmniBoundingVolume())
            self.computeCam.node().setFinal(True)
            self.computeCam.reparentTo(self.computeRoot)

            self.bspLoader.setShaderGenerator(self.shaderGenerator)
            self.bspLoader.setWantShadows(metadata.USE_REAL_SHADOWS)

    def _getEnabledShaders(self):
        from libpandabsp import VertexLitGenericSpec, LightmappedGenericSpec, UnlitGenericSpec, \
            UnlitNoMatSpec, CSMRenderSpec, SkyBoxSpec, DecalModulateSpec
        return [
            VertexLitGenericSpec(),
            UnlitGenericSpec(),
            LightmappedGenericSpec(),
            UnlitNoMatSpec(),
            CSMRenderSpec(),
            SkyBoxSpec(),
            DecalModulateSpec()
        ]

    def setupRender(self):
        if self.want_bsp:
            self.setupBSPRender()
            return

        # We don't want BSP
        super().setupRender()

    def setupBSPRender(self):
        """
        Creates the root of the 3D scene graph which supports BSP levels.
        """

        self.render = NodePath(BSPRender('render', self.bspLoader))
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
                if entity == 'filters':
                    member.windowEvent()

                member.update()

        return task.cont

    def renderFrames(self):
        for _ in range(2):
            self.graphicsEngine.renderFrame()

    def setMouseVisible(self, flag):
        props = WindowProperties()
        props.setCursorHidden(flag)
        self.win.requestProperties(props)

    def _initLoader(self):
        if self.loader is not None and not isinstance(self.loader, AssetLoader):
            self.loader.destroy()
        self.loader = AssetLoader(self)
        self.graphicsEngine.setDefaultLoader(self.loader.loader)
        builtins.loader = self.loader

        self.setupRender()

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

    def getGraphicsLibrary(self):
        lib = self.config.GetString('load-display')

        if lib == 'pandagl':
            return 'OpenGL'
        elif 'pandadx' in lib:
            return 'DirectX {0}'.format(str(lib.replace('pandadx', '')))
        
        return lib

    def getAudioLibrary(self):
        return self.config.GetString('audio-library-name').replace('p3', '').replace('_audio', '')

    def getAttributeChangedEventName(self, name):
        return 'Core-{0}-changed'.format(name)

if __name__ == "__main__":
    from src.coginvasion.base.Metadata import Metadata
    metadata = Metadata()
    builtins.metadata = metadata
    builtins.meta = metadata

    print('Starting Open Cog Invasion Online {0} with Panda3D version: {1}...'.format(metadata.getBuildInformation(), PandaSystem.getVersionString()))

    try:
        loadPrcFile('config/Confauto.prc')
        loadPrcFile('config/{0}'.format(PRC_FILE_DEV))

        # Let's mount our resources directly
        loadPrcFileData('', 'model-path resources')

        metadata.IS_PRODUCTION = 0
        print('Running development environment')

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

    base = Core()
    builtins.base = base

    if base.win is None:
        # Something went wrong!
        print('Failed to start the game! Did you install it correctly?')
        sys.exit()

    print('Rendering Engine: {0}, Sound Library: {1}'.format(base.getGraphicsLibrary(), base.getAudioLibrary()))
    base.onSuccessfulStart()

    base.run()
