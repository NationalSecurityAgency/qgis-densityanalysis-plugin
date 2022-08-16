import os
from qgis.PyQt import uic
from qgis.core import Qgis, QgsStyle
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.QtCore import QSettings

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

    def setDefaultColorRamp(self, color_ramp):
        # print('color_ramp: {}'.format(color_ramp))
        # print('ramp_names: {}'.format(self.ramp_names))
        if color_ramp not in self.ramp_names:
            color_ramp = 'Reds'
        # print('color_ramp: {}'.format(color_ramp))
        self.color_ramp = color_ramp
        qset = QSettings()
        qset.setValue('/DensityAnalysis/ColorRamp', color_ramp)
    
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

    def showEvent(self, e):
        settings.updateColorRamps()
        settings.readSettings()
        self.colorRampComboBox.clear()
        self.colorRampComboBox.addItems(settings.ramp_names)
        index = settings.defaultColorRampIndex()
        self.colorRampComboBox.setCurrentIndex(index)

    def accept(self):
       selected_ramp = self.colorRampComboBox.currentText()
       settings.setDefaultColorRamp(selected_ramp)
       self.close()
