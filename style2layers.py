"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
import re

from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtWidgets import QDialog, QApplication
from qgis.PyQt.uic import loadUiType
from qgis.core import Qgis, QgsMapLayerType

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/styleToLayer.ui'))


class StyleToLayers(QDialog, FORM_CLASS):

    def __init__(self, iface, parent):
        super(StyleToLayers, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.fileWidget.setFilter("*.qml")

    def accept(self):
        path = self.fileWidget.filePath().strip()
        reclassify = self.autoReclassifyCheckBox.isChecked()
        if not path:
            doc = QDomDocument()
            text = QApplication.clipboard().text()
            if not doc.setContent(text):
                self.iface.messageBar().pushMessage("","Invalid clipboard style content", level=Qgis.Warning, duration=4)
                return
        total_layers = 0
        success = 0
        for layer in self.iface.layerTreeView().selectedLayersRecursive():
            total_layers += 1
            if path:
                (msg, status) = layer.loadNamedStyle(path)
            else:
                try:
                    (status, msg) = layer.importNamedStyle(doc)
                except Exception:
                    status = False

            if status:
                layer_type = layer.type()
                if reclassify and layer_type == QgsMapLayerType.VectorLayer and layer.renderer().type() == 'graduatedSymbol':
                    renderer = layer.renderer()
                    nclass = len(renderer.ranges())
                    renderer.updateClasses(layer, nclass)
                layer.triggerRepaint()
                success += 1

        self.iface.messageBar().pushMessage("","Style applied to {} out of {} layers".format(success, total_layers), level=Qgis.Info, duration=4)

        self.close()