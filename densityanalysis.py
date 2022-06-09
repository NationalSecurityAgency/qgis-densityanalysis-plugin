# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QUrl, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsApplication
import processing
from .provider import DensityAnalysisProvider
from .utils import H3_INSTALLED

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
        self.densityGridAction = QAction(icon, "Create a density map grid", self.iface.mainWindow())
        self.densityGridAction.triggered.connect(self.densityGridAlgorithm)
        self.toolbar.addAction(self.densityGridAction)
        self.iface.addPluginToMenu("Density analysis", self.densityGridAction)

        icon = QIcon(os.path.dirname(__file__) + '/icons/geohash.png')
        self.geohashAction = QAction(icon, "Create geohash density map", self.iface.mainWindow())
        self.geohashAction.triggered.connect(self.geohashAlgorithm)
        self.toolbar.addAction(self.geohashAction)
        self.iface.addPluginToMenu("Density analysis", self.geohashAction)

        icon = QIcon(os.path.dirname(__file__) + '/icons/h3.png')
        self.h3Action = QAction(icon, "Create H3 density map", self.iface.mainWindow())
        self.h3Action.triggered.connect(self.h3Algorithm)
        self.toolbar.addAction(self.h3Action)
        self.iface.addPluginToMenu("Density analysis", self.h3Action)
        
        icon = QIcon(os.path.dirname(__file__) + '/icons/densityexplorer.svg')
        self.heatmapAction = QAction(icon, "Heatmap density analysis", self.iface.mainWindow())
        self.heatmapAction.triggered.connect(self.showHeatmapDialog)
        self.toolbar.addAction(self.heatmapAction)
        self.iface.addPluginToMenu("Density analysis", self.heatmapAction)

        icon = QIcon(os.path.dirname(__file__) + '/icons/applystyles.svg')
        self.style2layersAction = QAction(icon, "Apply style to selected layers", self.iface.mainWindow())
        self.style2layersAction.triggered.connect(self.style2layers)
        self.toolbar.addAction(self.style2layersAction)
        self.iface.addPluginToMenu("Density analysis", self.style2layersAction)
        
        icon = QIcon(os.path.dirname(__file__) + '/icons/gradient.png')
        self.graduatedStyleAction = QAction(icon, "Apply a graduated style", self.iface.mainWindow())
        self.graduatedStyleAction.triggered.connect(self.graduatedStyleAlgorithm)
        self.toolbar.addAction(self.graduatedStyleAction)
        self.iface.addPluginToMenu("Density analysis", self.graduatedStyleAction)
        
        icon = QIcon(os.path.dirname(__file__) + '/icons/random.png')
        self.randomStyleAction = QAction(icon, "Apply random categorized style", self.iface.mainWindow())
        self.randomStyleAction.triggered.connect(self.showRandomStyleDialog)
        self.toolbar.addAction(self.randomStyleAction)
        self.iface.addPluginToMenu("Density analysis", self.randomStyleAction)
        # self.toolbar.addAction(self.heatmapAction)
        
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
        self.iface.removePluginMenu('Density analysis', self.graduatedStyleAction)
        self.iface.removePluginMenu('Density analysis', self.randomStyleAction)
        self.iface.removePluginMenu('Density analysis', self.heatmapAction)
        self.iface.removePluginMenu('Density analysis', self.style2layersAction)
        self.iface.removePluginMenu("Density analysis", self.helpAction)
        if self.heatmap_dialog:
            self.iface.removeDockWidget(self.heatmap_dialog)
        # Remove Toolbar Icons
        self.iface.removeToolBarIcon(self.densityGridAction)
        self.iface.removeToolBarIcon(self.geohashAction)
        self.iface.removeToolBarIcon(self.h3Action)
        self.iface.removeToolBarIcon(self.heatmapAction)
        self.iface.removeToolBarIcon(self.style2layersAction)
        self.iface.removeToolBarIcon(self.graduatedStyleAction)
        self.iface.removeToolBarIcon(self.randomStyleAction)
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
        processing.execAlgorithmDialog('densityanalysis:kerneldensity', {})

    def geohashAlgorithm(self):
        processing.execAlgorithmDialog('densityanalysis:geohashdensity', {})

    def h3Algorithm(self):
        if H3_INSTALLED:
            processing.execAlgorithmDialog('densityanalysis:h3density', {})
            return
        helpString = '''
            <p>
              To create H3 density maps you will need to install the H3 Python Library (<a href="https://h3geo.org/">https://h3geo.org/</a>).<br><br>
              The H3 package can be installed by running the OSGeo4W shell as system administrator and running 'pip install h3' or whatever method you use to install python packages.
            </p>
            <p>
              Please refer to the H3 installation documentation: <a href="https://h3geo.org/docs/installation">https://h3geo.org/docs/installation</a>
            </p>
            <p>
              Once H3 is installed, please restart QGIS.
            </p>
            '''
        QMessageBox.information(self.iface.mainWindow(), 'H3 Install Instructions', helpString)

    def graduatedStyleAlgorithm(self):
        processing.execAlgorithmDialog('densityanalysis:gratuatedstyle', {})

    def showRandomStyleDialog(self):
        processing.execAlgorithmDialog('densityanalysis:randomstyle', {})

    def style2layers(self):
        if not self.style_Layers_dialog:
            from .style2layers import StyleToLayers
            self.style_Layers_dialog = StyleToLayers(self.iface, self.iface.mainWindow())
        self.style_Layers_dialog.show()

    def help(self):
        '''Display a help page'''
        import webbrowser
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)


