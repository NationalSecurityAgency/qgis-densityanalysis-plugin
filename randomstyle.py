import os
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsCategorizedSymbolRenderer, QgsSymbol, QgsRendererCategory, QgsRandomColorRamp
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField)
import processing


class RandomStyleAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT', 'Input map layer', [QgsProcessing.TypeVectorAnyGeometry])
        )
        self.addParameter(
            QgsProcessingParameterField(
                'GROUP_FIELD',
                'Field used for styling',
                parentLayerParameterName='INPUT',
                type=QgsProcessingParameterField.Any,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                'NO_OUTLINE',
                'No feature outlines',
                True,
                optional=False)
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, 'INPUT', context)
        attr = self.parameterAsString(parameters, 'GROUP_FIELD', context)
        no_outline = self.parameterAsBool(parameters, 'NO_OUTLINE', context)
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

    def group(self):
        return 'Styles'

    def groupId(self):
        return 'styles'

    def name(self):
        return 'randomstyle'

    def displayName(self):
        return 'Apply random categorized style'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/random.png'))

    def createInstance(self):
        return RandomStyleAlgorithm()
