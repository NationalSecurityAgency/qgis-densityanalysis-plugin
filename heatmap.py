import os

from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDockWidget, QAbstractItemView, QTableWidget, QTableWidgetItem
from qgis.core import Qgis, QgsMapLayerProxyModel, QgsFieldProxyModel, QgsWkbTypes, QgsFeatureRequest, QgsCoordinateTransform, QgsProject, QgsRectangle
from qgis.utils import isPluginLoaded, plugins
import traceback

MAX_LIST_SIZE = 5000

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/density.ui'))


class HeatmapAnalysis(QDockWidget, FORM_CLASS):
    selected_layer = None
    density_layer = None
    selected_score_field = None

    def __init__(self, iface, parent):
        super(HeatmapAnalysis, self).__init__(parent)
        self.setupUi(self)
        self.canvas = iface.mapCanvas()
        self.iface = iface
        self.clearButton.setIcon(QIcon(':/images/themes/default/mIconClearText.svg'))
        self.dataComboBox.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.dataComboBox.layerChanged.connect(self.layerChanged)
        self.densityHeatmapComboBox.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.densityHeatmapComboBox.layerChanged.connect(self.layerChanged)
        self.idComboBox.setFilters(QgsFieldProxyModel.Int | QgsFieldProxyModel.LongLong)
        self.idComboBox.fieldChanged.connect(self.fieldChanged)
        self.countComboBox.setFilters(QgsFieldProxyModel.Numeric)
        self.countComboBox.fieldChanged.connect(self.fieldChanged)
        self.resultsTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.resultsTable.setColumnCount(2)
        self.resultsTable.setSortingEnabled(False)
        self.resultsTable.setHorizontalHeaderLabels(['ID','Score'])
        self.resultsTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.resultsTable.itemSelectionChanged.connect(self.select_feature)

    def showEvent(self, e):
        self.layerChanged()

    def closeEvent(self, e):
        layer = self.dataComboBox.currentLayer()
        if layer:
            layer.setSubsetString('')

    def fieldChanged(self, fieldName):
        self.layerChanged()

    def layerChanged(self):
        if not self.isVisible():
            return
        reset_results = False
        layer = self.dataComboBox.currentLayer()
        if layer != self.selected_layer:
            reset_results = True
            self.selected_layer = layer
        density_layer = self.densityHeatmapComboBox.currentLayer()
        if density_layer != self.density_layer:
            if density_layer:
                density_layer.setSubsetString('')
            self.idComboBox.blockSignals(True)
            self.idComboBox.setLayer(density_layer)
            self.idComboBox.setField('id')
            self.idComboBox.blockSignals(False)
            self.countComboBox.blockSignals(True)
            self.countComboBox.setLayer(density_layer)
            self.countComboBox.setField('NUMPOINTS')
            self.countComboBox.blockSignals(False)
            reset_results = True
            self.density_layer = density_layer
        
        score_field = self.countComboBox.currentField()
        if score_field != self.selected_score_field:
            reset_results = True
            self.selected_score_field = score_field

        if reset_results:
            self.resultsTable.setRowCount(0)

    def select_feature(self):
        density_layer = self.densityHeatmapComboBox.currentLayer()
        selectedItems = self.resultsTable.selectedItems()
        auto_zoom = self.zoomComboBox.currentIndex()
        if len(selectedItems) == 0:
            if density_layer:
                density_layer.setSubsetString('')
            return
        id_field_name = self.idComboBox.currentField()
        ids = set()
        for item in selectedItems:
            selectedRow = item.row()
            ids.add(self.resultsTable.item(selectedRow, 0).text())
        ids_str = ",".join(ids)
        exp = '"{}" IN ({})'.format(id_field_name, ids_str)
        density_layer.setSubsetString(exp)
        
        if auto_zoom:
            density_crs = density_layer.crs()
            canvas_crs = self.canvas.mapSettings().destinationCrs()
            xform = QgsCoordinateTransform(density_crs, canvas_crs, QgsProject.instance())
            # center = xform.transform(density_layer.extent()).center()
            # rect = QgsRectangle(center.x(), center.y(), center.x(), center.y())
            rect = xform.transform(density_layer.extent())
            if auto_zoom == 1:
                center = rect.center()
                rect = QgsRectangle(center.x(), center.y(), center.x(), center.y())
            self.canvas.setExtent(rect)

    def on_applyButton_pressed(self):
        self.resultsTable.setRowCount(0)
        density_layer = self.densityHeatmapComboBox.currentLayer()
        score_field = self.countComboBox.currentField()
        id_field = self.idComboBox.currentField()
        if not id_field or not score_field:
            return

        request=QgsFeatureRequest().addOrderBy(score_field, ascending=False)
        iter = density_layer.getFeatures(request)
        for i, f in enumerate(iter):
            score = f[score_field]
            id = f[id_field]
            self.resultsTable.insertRow(i)
            item = QTableWidgetItem('{}'.format(id))
            self.resultsTable.setItem(i, 0, item)
            try:
                item = QTableWidgetItem('{}'.format(score))
            except:
                item = QTableWidgetItem('')
            self.resultsTable.setItem(i, 1, item)
            if i >= MAX_LIST_SIZE - 1:
                break

    def on_clearButton_pressed(self):
        """"
            This deselects all selected tracks. It doesn't remove them.
        """
        self.resultsTable.clearSelection()
