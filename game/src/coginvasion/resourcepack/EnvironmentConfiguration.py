"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file EnvironmentConfiguration.py
@author Maverick Liberty
@date 27-09-17

"""

from direct.directnotify.DirectNotifyGlobal import directNotify

from panda3d.core import Vec3

from yaml import load

from src.coginvasion.globals.CIGlobals import colorFromRGBScalar255
from src.coginvasion.hood.ZoneUtil import HoodAbbr2Hood

boolean = 'boolean'
color = 'color'
position = 'position'
numberValue = 'number'
stringValue = 'string'
stringList = 'stringList'
anyValue = 'any'

class Modifier:
    notify = directNotify.newCategory('YAMLConfigurationModifier')
    
    def __init__(self, modType = color):
        self.modType = modType
    
    # Called when a key is suspected to be this modifier.
    # This method will double-check that and verify that it has everything it needs.
    def digest(self, data):
        if self.modType is color:
            if not isinstance(data, list):
                self.notify.warning('Expected 3 or 4 [0-255] rgb values for color (position 4 should be scalar).')
                self.notify.warning('Instead, %d values were found.' % len(data))
                return None
            else:
                for n in data:
                    if not isinstance(n, int):
                        self.notify.warning('Received a non-int value for color.')
                        return None
            
            if len(data) < 3:
                # if the user supplied less than 3 values for a color,
                # fill in the missing values with the last supplied value.
                for _ in range(3 - len(data)):
                    data.append(data[len(data) - 1])
            if len(data) < 4:
                # user didn't supply a scalar.
                # automatically use 255 (which would be no scaling).
                data.append(255)
            return colorFromRGBScalar255(data)
        elif self.modType is stringList:
            if not isinstance(data, list):
                self.notify.warning('Expected a list of strings.')
                return None
            return data
        elif self.modType is position:
            if not isinstance(data, list) or len(data) != 3:
                self.notify.warning('Expected 3 integer values for position.')
                self.notify.warning('Instead, %d values were found.' % len(data))
                return None
            elif isinstance(data, list) and len(data) == 3:
                for n in data:
                    if not isinstance(n, int):
                        self.notify.warning('Positional values must be integers.')
                        return None
            return Vec3(data[0], data[1], data[2])
        elif self.modType is numberValue:
            try:
                return float(data)
            except ValueError:
                self.notify.warning('Expected a single number value for fog density')
                return None
        elif self.modType is boolean:
            if not type(data) == type(True):
                self.notify.warning('Expected a boolean value for want-reflections.')
                return None
            return data
        elif self.modType is stringValue:
            if not isinstance(data, basestring):
                self.notify.warning('Expected a string value.')
                return None
            return data
        elif self.modType is anyValue:
            return data

class HoodData(object):
    
    def __init__(self, envConfig):
        self.envConfig = envConfig
        self.outdoorAmbientColor = None
        self.indoorAmbientColor = None
        self.fogColor = None
        self.fogDensity = None
        self.sunColor = None
        self.sunAngle = None
        self.interiorLightColor = None
        self.skyType = None
        self.modifiers = {
            'outdoor-ambient-color' : [Modifier(color), 'outdoorAmbientColor'],
            'indoor-ambient-color' : [Modifier(color), 'indoorAmbientColor'],
            'fog-color' : [Modifier(color), 'fogColor'],
            'fog-density' : [Modifier(numberValue), 'fogDensity'],
            'sun-color' : [Modifier(color), 'sunColor'],
            'sun-angle' : [Modifier(position), 'sunAngle'],
            'interior-light-color' : [Modifier(color), 'interiorLightColor'],
            'sky-type' : [Modifier(numberValue), 'skyType']
        }
        
    def setDefaults(self):
        # Let's set non-set attributes to the defaults inside of EnvironmentConfiguration.
        for valueSet in self.modifiers.values():
            attrName = valueSet[1]
            if not getattr(self, valueSet[1]):
                setattr(self, valueSet[1], getattr(self.envConfig, 'default' + attrName[0].upper() + attrName[1:]))
        
    def digest(self, hoodSection):
        for key in hoodSection:
            if not isinstance(key, dict):
                if key in list(self.modifiers.keys()):
                    entry = self.modifiers.get(key)
                    modifier = entry[0]
                    setattr(self, entry[1], modifier.digest(hoodSection[key]))
                    
        self.setDefaults()
                
    def __str__(self):
        return 'Outside Ambient Color: %s, Indoor Ambient Color: %s, \
        Fog Color: %s, Fog Density: %d, Sun Color: %s, Sun Angle: %s,\
        Interior Light Color: %s, Sky Type: %d' % (self.outdoorAmbientColor, 
            self.indoorAmbientColor, self.fogColor, self.fogDensity, self.sunColor,
            self.sunAngle, self.interiorLightColor, self.skyType)

class EnvironmentConfiguration:
    notify = directNotify.newCategory('EnvironmentConfiguration')

    # Requires the path to the config file
    # and, if only a section of the config file contains
    # the information for the environment, specify the
    # name of that section.
    def __init__(self, configStream = None, configPath = None, section = None):
        self.configStream = configStream
        self.configPath = configPath
        self.section = section
        self.wantReflections = True
        self.defaultOutdoorAmbientColor = None
        self.defaultIndoorAmbientColor = None
        self.defaultSunColor = None
        self.defaultSunAngle = None
        self.defaultFogColor = None
        self.defaultFogDensity = None
        self.defaultInteriorLightColor = None
        self.defaultSkyType = None
        self.defaultShaderModifiers = {
           'default-sky-type' : [Modifier(numberValue), 'defaultSkyType'],
           'default-outdoor-ambient-color' : [Modifier(color), 'defaultOutdoorAmbientColor'],
           'default-indoor-ambient-color' : [Modifier(color), 'defaultIndoorAmbientColor'],
           'default-sun-color' : [Modifier(color), 'defaultSunColor'],
           'default-sun-angle' : [Modifier(position), 'defaultSunAngle'],
           'default-fog-color' : [Modifier(color), 'defaultFogColor'],
           'default-fog-density' : [Modifier(numberValue), 'defaultFogDensity'],
           'default-interior-light-color' : [Modifier(color), 'defaultInteriorLightColor'],
        }
        
        self.hoodData = {}
        
        for hood in list(HoodAbbr2Hood.keys()):
            self.hoodData[hood] = HoodData(self)
            
    def processData(self, data):
        # This is the section where our environment data can be found.
        environ = data if not self.section else data[self.section]

        if 'want-reflections' in list(environ.keys()):
            modifier = Modifier(boolean)
            self.wantReflections = modifier.digest(environ['want-reflections'])
        
        if 'shaders' in environ:
            shaders = environ['shaders']
            # A list of keys that point to hood data that should be loaded.
            hoodDataToLoad = list(self.hoodData.keys())
            fileHoodDataToLoad = []
            for key in shaders:
                hoodData = self.getHoodSection(key)
                if not isinstance(shaders[key], dict) and key in list(self.defaultShaderModifiers.keys()):
                    entry = self.defaultShaderModifiers.get(key)
                    modifier = entry[0]
                    setattr(self, entry[1], modifier.digest(shaders[key]))
                elif hoodData:
                    # We're going to load up hood data after we set our defaults.
                    if key.upper() in hoodDataToLoad:
                        hoodDataToLoad.remove(key.upper())
                        fileHoodDataToLoad.append(key)
                    continue
                else:
                    self.notify.warning('Unexpected key %s was found.' % key)
            
            fileDataLoaded = 0
            for i in range(0, len(list(self.hoodData.keys()))):
                if len(hoodDataToLoad) > 0 and i < len(hoodDataToLoad):
                    hoodData = self.getHoodSection(hoodDataToLoad[i])
                    hoodData.setDefaults()
                elif len(fileHoodDataToLoad) > 0:
                    hoodData = self.getHoodSection(fileHoodDataToLoad[fileDataLoaded])
                    hoodData.digest(shaders[key])
                    fileDataLoaded += 1
                
            for key in shaders:
                hoodData = self.getHoodSection(key)
                if isinstance(shaders[key], dict) and hoodData:
                    hoodData.digest(shaders[key])
        
    def digest(self):
        if self.configPath:
            with open(self.configPath, 'r') as stream:
                self.processData(load(stream))
        elif self.configStream:
            self.processData(load(self.configStream))
                    
    def getHoodSection(self, key):
        index = -1 if not key in list(HoodAbbr2Hood.values()) else list(HoodAbbr2Hood.values()).index(key)
        if key.upper() in list(HoodAbbr2Hood.keys()):
            return self.hoodData.get(list(HoodAbbr2Hood.keys())[list(HoodAbbr2Hood.keys()).index(key.upper())])
        elif index > -1:
            return self.hoodData.get(list(HoodAbbr2Hood.keys())[index])
        return None
        