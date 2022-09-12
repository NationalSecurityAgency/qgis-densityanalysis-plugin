import os
from qgis.PyQt import uic
from qgis.core import Qgis, QgsStyle, QgsUnitTypes
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.QtCore import QSettings

POLYGON_UNIT_LABELS = ["Kilometers", "Meters", "Miles", 'Yards', "Feet", "Nautical Miles", "Degrees", "Dimensions in pixels"]
UNIT_LABELS = ["Kilometers", "Meters", "Miles", 'Yards', "Feet", "Nautical Miles", "Degrees"]

def conversionToCrsUnits(selected_unit, crs_unit, value):
    if selected_unit == 0:  # Kilometers
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceKilometers, crs_unit)
    elif selected_unit == 1:  # Meters
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMeters, crs_unit)
    elif selected_unit == 2:  # Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMiles, crs_unit)
    elif selected_unit == 3:  # Yards
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceYards, crs_unit)
    elif selected_unit == 4:  # Feet
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceFeet, crs_unit)
    elif selected_unit == 5:  # Nautical Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceNauticalMiles, crs_unit)
    elif selected_unit == 6:  # Degrees
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceDegrees, crs_unit)
    return(measureFactor * value)

def conversionFromCrsUnits(selected_unit, crs_unit, value):
    if selected_unit == 0:  # Kilometers
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceKilometers)
    elif selected_unit == 1:  # Meters
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceMeters)
    elif selected_unit == 2:  # Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceMiles)
    elif selected_unit == 3:  # Yards
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceYards)
    elif selected_unit == 4:  # Feet
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceFeet)
    elif selected_unit == 5:  # Nautical Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceNauticalMiles)
    elif selected_unit == 6:  # Degrees
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceDegrees)
    return(measureFactor * value)

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/settings.ui'))

class Settings():
    def __init__(self):
        self.updateColorRamps()
        self.readSettings()

    def updateColorRamps(self):
        style = QgsStyle.defaultStyle()
        self.ramp_names = style.colorRampNames()

    def readSettings(self):
        qset = QSettings()
        self.color_ramp = qset.value('/DensityAnalysis/ColorRamp', 'Reds')
        if self.color_ramp not in self.ramp_names:
            self.color_ramp = 'Reds'
        try:
            self.num_ramp_classes = int(qset.value('/DensityAnalysis/NumRampClasses', 15))
        except Exception:
            self.num_ramp_classes = 15
        try:
            self.poly_measurement_unit = int(qset.value('/DensityAnalysis/PolyMeasuementUnit', 0))
        except Exception:
            self.poly_measurement_unit = 0
        try:
            self.measurement_unit = int(qset.value('/DensityAnalysis/MeasuementUnit', 0))
        except Exception:
            self.measurement_unit = 0
        try:
            self.default_dimension = float(qset.value('/DensityAnalysis/DefaultDimension', 1.0))
        except Exception:
            self.default_dimension = 1.0
        try:
            self.max_image_size = int(qset.value('/DensityAnalysis/MaxImageSize', 20000))
        except Exception:
            self.max_image_size = 20000

    def setDefaultColorRamp(self, color_ramp, num_ramp_classes):
        # print('color_ramp: {}'.format(color_ramp))
        # print('ramp_names: {}'.format(self.ramp_names))
        if color_ramp not in self.ramp_names:
            color_ramp = 'Reds'
        # print('color_ramp: {}'.format(color_ramp))
        self.color_ramp = color_ramp
        self.num_ramp_classes = num_ramp_classes
        qset = QSettings()
        qset.setValue('/DensityAnalysis/ColorRamp', color_ramp)
        qset.setValue('/DensityAnalysis/NumRampClasses', num_ramp_classes)
    
    def setDefaults(self, measurement_unit, poly_measurement_unit, default_dimension, max_image_size):
        self.measurement_unit = measurement_unit
        self.poly_measurement_unit = poly_measurement_unit
        self.default_dimension = default_dimension
        self.max_image_size = max_image_size
        qset = QSettings()
        qset.setValue('/DensityAnalysis/MeasuementUnit', measurement_unit)
        qset.setValue('/DensityAnalysis/PolyMeasuementUnit', poly_measurement_unit)
        qset.setValue('/DensityAnalysis/DefaultDimension', default_dimension)
        qset.setValue('/DensityAnalysis/MaxImageSize', max_image_size)
        
    
    def defaultColorRamp(self):
        # print('defaultColorRamp: {}'.format(self.color_ramp))
        return (self.color_ramp)
        
    def defaultColorRampIndex(self):
        try:
            index = self.ramp_names.index(self.color_ramp)
        except Exception:
            index = 0
        # print('index: {}'.format(index))
        return( index )

    def colorRamps(self):
        return (self.ramp_names)
        
settings = Settings()

class SettingsWidget(QDialog, FORM_CLASS):
    '''Settings Dialog box.'''
    def __init__(self, iface, parent):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.unitsComboBox.addItems(UNIT_LABELS)
        self.polyUnitsComboBox.addItems(POLYGON_UNIT_LABELS)

    def showEvent(self, e):
        settings.updateColorRamps()
        settings.readSettings()
        self.colorRampComboBox.clear()
        self.colorRampComboBox.addItems(settings.ramp_names)
        index = settings.defaultColorRampIndex()
        self.colorRampComboBox.setCurrentIndex(index)
        self.rampClassesSpinBox.setValue(settings.num_ramp_classes)
        self.unitsComboBox.setCurrentIndex(settings.measurement_unit)
        self.polyUnitsComboBox.setCurrentIndex(settings.poly_measurement_unit)
        self.defaultDimensionSpinBox.setValue(settings.default_dimension)
        self.maxImageSizeSpinBox.setValue(settings.max_image_size)

    def accept(self):
        selected_ramp = self.colorRampComboBox.currentText()
        settings.setDefaultColorRamp(selected_ramp, self.rampClassesSpinBox.value())
        settings.setDefaults(self.unitsComboBox.currentIndex(), self.polyUnitsComboBox.currentIndex(),
            self.defaultDimensionSpinBox.value(), self.maxImageSizeSpinBox.value())
        self.close()
