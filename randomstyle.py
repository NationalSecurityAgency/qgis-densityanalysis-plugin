import os
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsCategorizedSymbolRenderer, QgsSymbol, QgsRendererCategory, QgsRandomColorRamp
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterMapLayer,
    QgsProcessingParameterField)
import processing


class RandomStyleAlgorithm(QgsProcessingAlgorithm):
    PrmMapLyaer = 'maplayer'
    PrmGroupField = 'groupfield'
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
        no_outline = self.parameterAsBool(parameters, self.PrmNoOutline, context)
        renderer = layer.renderer()
        geomtype = layer.geometryType()
        idx = layer.fields().indexOf(attr)
        values = layer.uniqueValues(idx)
        categories = []
        for value in values:
            symbol = QgsSymbol.defaultSymbol(geomtype)
            if no_outline:
                symbol.symbolLayer(0).setStrokeStyle(Qt.PenStyle(Qt.NoPen))
            category = QgsRendererCategory(value, symbol, str(value))
            categories.append(category)

        new_renderer = QgsCategorizedSymbolRenderer (attr, categories)
        ramp = QgsRandomColorRamp()
        new_renderer.updateColorRamp(ramp)
        layer.setRenderer(new_renderer)
        layer.triggerRepaint()
        return({})

    def name(self):
        return 'randomstyle'

    def displayName(self):
        return 'Apply a random categorized style'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/random.png'))

    def createInstance(self):
        return RandomStyleAlgorithm()
