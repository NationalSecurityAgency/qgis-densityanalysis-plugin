# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QUrl, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsApplication
import processing
from .provider import DensityAnalysisProvider

try:
    import h3
    h3_installed = True
except Exception:
    from .utils import h3InstallString
    h3_installed = False

import os

class DensityAnalysis(object):
    heatmap_dialog = None
    style_Layers_dialog = None
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.provider = DensityAnalysisProvider()

    def initGui(self):
        self.toolbar = self.iface.addToolBar('Density Analysis Toolbar')
        self.toolbar.setObjectName('DensityAnalysisToolbar')
        self.toolbar.setToolTip('Density Analysis Toolbar')

        icon = QIcon(os.path.dirname(__file__) + '/icons/densitygrid.svg')
        self.densityGridAction = QAction(icon, "Styled density map", self.iface.mainWindow())
        self.densityGridAction.triggered.connect(self.densityGridAlgorithm)
        self.toolbar.addAction(self.densityGridAction)
        self.iface.addPluginToMenu("Density analysis", self.densityGridAction)

        icon = QIcon(os.path.dirname(__file__) + '/icons/geohash.png')
        self.geohashAction = QAction(icon, "Styled geohash density map", self.iface.mainWindow())
        self.geohashAction.triggered.connect(self.geohashAlgorithm)
        self.toolbar.addAction(self.geohashAction)
        self.iface.addPluginToMenu("Density analysis", self.geohashAction)

        icon = QIcon(os.path.dirname(__file__) + '/icons/h3.png')
        self.h3Action = QAction(icon, "Styled H3 density map", self.iface.mainWindow())
        self.h3Action.triggered.connect(self.h3Algorithm)
        self.toolbar.addAction(self.h3Action)
        self.iface.addPluginToMenu("Density analysis", self.h3Action)

        icon = QIcon(os.path.dirname(__file__) + '/icons/kde.png')
        self.kdeAction = QAction(icon, "Styled heatmap (Kernel density estimation)", self.iface.mainWindow())
        self.kdeAction.triggered.connect(self.kdeAlgorithm)
        self.toolbar.addAction(self.kdeAction)
        self.iface.addPluginToMenu("Density analysis", self.kdeAction)
        
        icon = QIcon(os.path.dirname(__file__) + '/icons/densityexplorer.svg')
        self.heatmapAction = QAction(icon, "Density map analysis tool", self.iface.mainWindow())
        self.heatmapAction.triggered.connect(self.showHeatmapDialog)
        self.toolbar.addAction(self.heatmapAction)
        self.iface.addPluginToMenu("Density analysis", self.heatmapAction)

        icon = QIcon(os.path.dirname(__file__) + '/icons/applystyles.svg')
        self.style2layersAction = QAction(icon, "Apply style to selected layers", self.iface.mainWindow())
        self.style2layersAction.triggered.connect(self.style2layers)
        self.toolbar.addAction(self.style2layersAction)
        self.iface.addPluginToMenu("Density analysis", self.style2layersAction)
        
        icon = QIcon(os.path.dirname(__file__) + '/icons/gradient.png')
        self.graduatedStyleAction = QAction(icon, "Apply graduated style", self.iface.mainWindow())
        self.graduatedStyleAction.triggered.connect(self.graduatedStyleAlgorithm)
        self.toolbar.addAction(self.graduatedStyleAction)
        self.iface.addPluginToMenu("Density analysis", self.graduatedStyleAction)
        
        icon = QIcon(os.path.dirname(__file__) + '/icons/random.png')
        self.randomStyleAction = QAction(icon, "Apply random categorized style", self.iface.mainWindow())
        self.randomStyleAction.triggered.connect(self.showRandomStyleDialog)
        self.toolbar.addAction(self.randomStyleAction)
        self.iface.addPluginToMenu("Density analysis", self.randomStyleAction)
        
        icon = QIcon(os.path.dirname(__file__) + '/icons/polydensity.png')
        self.polyDensityAction = QAction(icon, "Polygon raster density map", self.iface.mainWindow())
        self.polyDensityAction.triggered.connect(self.polyDensityDialog)
        self.toolbar.addAction(self.polyDensityAction)
        self.iface.addPluginToMenu("Density analysis", self.polyDensityAction)
        
        icon = QIcon(os.path.dirname(__file__) + '/icons/styleraster.png')
        self.rasterStyleAction = QAction(icon, "Apply pseudocolor raster style", self.iface.mainWindow())
        self.rasterStyleAction.triggered.connect(self.rasterStyleDialog)
        self.toolbar.addAction(self.rasterStyleAction)
        self.iface.addPluginToMenu("Density analysis", self.rasterStyleAction)
        
        icon = QIcon(os.path.dirname(__file__) + '/icons/h3grid.svg')
        self.h3GridAction = QAction(icon, "H3 grid", self.iface.mainWindow())
        self.h3GridAction.triggered.connect(self.h3Grid)
        self.iface.addPluginToMenu("Density analysis", self.h3GridAction)


        icon = QIcon(':/images/themes/default/processingAlgorithm.svg')
        self.geohashDensityGridAction = QAction(icon, "Geohash density grid", self.iface.mainWindow())
        self.geohashDensityGridAction.triggered.connect(self.geohashDensityGrid)
        self.iface.addPluginToMenu("Density analysis", self.geohashDensityGridAction)

        self.h3DensityGridAction = QAction(icon, "H3 density grid", self.iface.mainWindow())
        self.h3DensityGridAction.triggered.connect(self.h3DensityGrid)
        self.iface.addPluginToMenu("Density analysis", self.h3DensityGridAction)

        # Help
        icon = QIcon(os.path.dirname(__file__) + '/icons/help.svg')
        self.helpAction = QAction(icon, "Help", self.iface.mainWindow())
        self.helpAction.triggered.connect(self.help)
        self.iface.addPluginToMenu('Density analysis', self.helpAction)
        
        # Add the processing provider
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        self.iface.removePluginMenu('Density analysis', self.densityGridAction)
        self.iface.removePluginMenu('Density analysis', self.geohashAction)
        self.iface.removePluginMenu('Density analysis', self.h3Action)
        self.iface.removePluginMenu('Density analysis', self.kdeAction)
        self.iface.removePluginMenu('Density analysis', self.graduatedStyleAction)
        self.iface.removePluginMenu('Density analysis', self.randomStyleAction)
        self.iface.removePluginMenu('Density analysis', self.polyDensityAction)
        self.iface.removePluginMenu('Density analysis', self.heatmapAction)
        self.iface.removePluginMenu('Density analysis', self.style2layersAction)
        self.iface.removePluginMenu('Density analysis', self.rasterStyleAction)
        self.iface.removePluginMenu("Density analysis", self.h3GridAction)
        self.iface.removePluginMenu("Density analysis", self.geohashDensityGridAction)
        self.iface.removePluginMenu("Density analysis", self.h3DensityGridAction)
        self.iface.removePluginMenu("Density analysis", self.helpAction)
        if self.heatmap_dialog:
            self.iface.removeDockWidget(self.heatmap_dialog)
        # Remove Toolbar Icons
        self.iface.removeToolBarIcon(self.densityGridAction)
        self.iface.removeToolBarIcon(self.geohashAction)
        self.iface.removeToolBarIcon(self.h3Action)
        self.iface.removeToolBarIcon(self.kdeAction)
        self.iface.removeToolBarIcon(self.heatmapAction)
        self.iface.removeToolBarIcon(self.style2layersAction)
        self.iface.removeToolBarIcon(self.graduatedStyleAction)
        self.iface.removeToolBarIcon(self.randomStyleAction)
        self.iface.removeToolBarIcon(self.polyDensityAction)
        self.iface.removeToolBarIcon(self.rasterStyleAction)
        del self.toolbar
        """Remove the provider."""
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def showHeatmapDialog(self):
        """Display the kernal density analysis window."""
        if not self.heatmap_dialog:
            from .heatmap import HeatmapAnalysis
            self.heatmap_dialog = HeatmapAnalysis(self.iface, self.iface.mainWindow())
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.heatmap_dialog)
        self.heatmap_dialog.show()

    def densityGridAlgorithm(self):
        processing.execAlgorithmDialog('densityanalysis:densitymap', {})

    def geohashAlgorithm(self):
        processing.execAlgorithmDialog('densityanalysis:geohashdensitymap', {})

    def h3Algorithm(self):
        if h3_installed:
            processing.execAlgorithmDialog('densityanalysis:h3densitymap', {})
        else:
            QMessageBox.information(self.iface.mainWindow(), 'H3 Install Instructions', h3InstallString)

    def graduatedStyleAlgorithm(self):
        processing.execAlgorithmDialog('densityanalysis:gratuatedstyle', {})

    def showRandomStyleDialog(self):
        processing.execAlgorithmDialog('densityanalysis:randomstyle', {})

    def polyDensityDialog(self):
        processing.execAlgorithmDialog('densityanalysis:polygondensity', {})

    def rasterStyleDialog(self):
        processing.execAlgorithmDialog('densityanalysis:rasterstyle', {})

    def style2layers(self):
        if not self.style_Layers_dialog:
            from .style2layers import StyleToLayers
            self.style_Layers_dialog = StyleToLayers(self.iface, self.iface.mainWindow())
        self.style_Layers_dialog.show()
    
    def geohashDensityGrid(self):
        processing.execAlgorithmDialog('densityanalysis:geohashdensity', {})
    
    def h3DensityGrid(self):
        if h3_installed:
            processing.execAlgorithmDialog('densityanalysis:h3density', {})
        else:
            QMessageBox.information(self.iface.mainWindow(), 'H3 Install Instructions', h3InstallString)
    
    def h3Grid(self):
        if h3_installed:
            processing.execAlgorithmDialog('densityanalysis:h3grid', {})
        else:
            QMessageBox.information(self.iface.mainWindow(), 'H3 Install Instructions', h3InstallString)
    
    def kdeAlgorithm(self):
        processing.execAlgorithmDialog('densityanalysis:styledkde', {})

    def help(self):
        '''Display a help page'''
        import webbrowser
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)


