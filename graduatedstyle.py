import os
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsStyle, QgsSymbol, QgsGraduatedSymbolRenderer, QgsClassificationLogarithmic
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterMapLayer,
    QgsProcessingParameterField)
import processing


class GraduatedStyleAlgorithm(QgsProcessingAlgorithm):
    PrmMapLyaer = 'maplayer'
    PrmGroupField = 'groupfield'
    PrmRampNames = 'rampnames'
    PrmMode = 'mode'
    PrmClasses = 'classes'
    PrmNoOutline = 'NoOutline'
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMapLayer(
                self.PrmMapLyaer, 'Input map layer', defaultValue=None,
                types=[QgsProcessing.TypeVectorAnyGeometry ])
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PrmGroupField,
                'Field used for styling',
                parentLayerParameterName=self.PrmMapLyaer,
                type=QgsProcessingParameterField.Any,
                optional=False)
        )
        style = QgsStyle.defaultStyle()
        ramp_names = style.colorRampNames()
        ramp_name_param = QgsProcessingParameterString(self.PrmRampNames, 'Graduated color ramp name', defaultValue='Reds')
        ramp_name_param.setMetadata( {'widget_wrapper': {'value_hints': ramp_names } } )
        self.addParameter(ramp_name_param)
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmMode,
                'Mode',
                options=['Equal Count (Quantile)','Equal Interval','Logrithmic scale','Natural Breaks (Jenks)','Pretty Breaks','Standard Deviation'],
                defaultValue=0,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmClasses,
                'Number of classes',
                QgsProcessingParameterNumber.Integer,
                defaultValue=10,
                minValue=2,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmNoOutline,
                'No feature outlines',
                True,
                optional=False)
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.PrmMapLyaer, context)
        attr = self.parameterAsString(parameters, self.PrmGroupField, context)
        ramp_name = self.parameterAsString(parameters, self.PrmRampNames, context)
        mode = self.parameterAsInt(parameters, self.PrmMode, context)
        num_classes = self.parameterAsInt(parameters, self.PrmClasses, context)
        no_outline = self.parameterAsBool(parameters, self.PrmNoOutline, context)
        
        if mode == 0: # Quantile
            grad_mode = QgsGraduatedSymbolRenderer.Quantile
        elif mode == 1: # Equal Interval
            grad_mode = QgsGraduatedSymbolRenderer.EqualInterval
        elif mode == 2: # Logrithmic scale
            grad_mode = QgsGraduatedSymbolRenderer.Quantile
        elif mode == 3: # Natural Breaks (Jenks)
            grad_mode = QgsGraduatedSymbolRenderer.Jenks
        elif mode == 4: # Pretty Breaks
            grad_mode = QgsGraduatedSymbolRenderer.Pretty
        elif mode == 5: # Standard Deviation
            grad_mode = QgsGraduatedSymbolRenderer.StdDev

        geomtype = layer.geometryType()
        symbol = QgsSymbol.defaultSymbol(geomtype)
        if no_outline:
            symbol.symbolLayer(0).setStrokeStyle(Qt.PenStyle(Qt.NoPen))
        style = QgsStyle.defaultStyle()
        ramp = style.colorRamp(ramp_name)
        new_renderer = QgsGraduatedSymbolRenderer.createRenderer(
            layer, # The layer
            attr, # Attribute name
            num_classes, # Number of classes
            grad_mode, # Mode
            symbol, # QgsSymbol
            ramp # Our color ramp
        )
        if mode == 2:
            new_renderer.setClassificationMethod(QgsClassificationLogarithmic())
        layer.setRenderer(new_renderer)
        layer.triggerRepaint()
        return({})

    def name(self):
        return 'gratuatedstyle'

    def displayName(self):
        return 'Apply a graduated style'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/gradient.png'))

    def createInstance(self):
        return GraduatedStyleAlgorithm()
