# -*- coding: utf-8 -*-
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

from qgis.PyQt.QtCore import QUrl, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QMenu, QToolButton
from qgis.core import QgsApplication
import processing
from .provider import DensityAnalysisProvider
from .settings import SettingsWidget
from .utils import h3InstallString

import os

class DensityAnalysis(object):
    heatmap_dialog = None
    style_Layers_dialog = None
    settingsDialog = None
    h3_installed = False

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.provider = DensityAnalysisProvider()

    def initGui(self):
        self.toolbar = self.iface.addToolBar('Density Analysis Toolbar')
        self.toolbar.setObjectName('DensityAnalysisToolbar')
        self.toolbar.setToolTip('Density Analysis Toolbar')

        # Create the Geohash menu items
        menu = QMenu()
        icon = QIcon(os.path.dirname(__file__) + '/icons/geohash.png')
        self.geohashAction = menu.addAction(icon, 'Styled geohash density map', self.geohashAlgorithm)

        icon = QIcon(os.path.dirname(__file__) + '/icons/ml_geohash.png')
        self.geohashMultiAction = menu.addAction(icon, 'Styled geohash multi-layer density map', self.geohashMultiAlgorithm)

        icon = QIcon(os.path.dirname(__file__) + '/icons/geohashdensity.svg')
        self.geohashDensityGridAction = menu.addAction(icon, 'Geohash density grid', self.geohashDensityGrid)

        icon = QIcon(os.path.dirname(__file__) + '/icons/geohashmultidensity.svg')
        self.geohashMultiDensityGridAction = menu.addAction(icon, 'Geohash multi-layer density grid', self.geohashMultiDensityGrid)

        # Add the geohash tools to the menu
        icon = QIcon(os.path.dirname(__file__) + '/icons/geohash.png')
        self.geohashActions = QAction(icon, 'Geohash density algorithms', self.iface.mainWindow())
        self.geohashActions.setMenu(menu)
        self.iface.addPluginToMenu('Density analysis', self.geohashActions)

        # Add the geohash algorithms to the toolbar
        self.geohashButton = QToolButton()
        self.geohashButton.setMenu(menu)
        self.geohashButton.setDefaultAction(self.geohashAction)
        self.geohashButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.geohashButton.triggered.connect(self.geohashTriggered)
        self.geohashToolbar = self.toolbar.addWidget(self.geohashButton)

        # Create the H3 menu items
        menu = QMenu()
        icon = QIcon(os.path.dirname(__file__) + '/icons/h3.png')
        self.h3Action = menu.addAction(icon, 'Styled H3 density map', self.h3Algorithm)

        icon = QIcon(os.path.dirname(__file__) + '/icons/ml_h3.png')
        self.h3MultiAction = menu.addAction(icon, 'Styled H3 multi-layer density map', self.h3MultiAlgorithm)

        icon = QIcon(os.path.dirname(__file__) + '/icons/h3density.svg')
        self.h3DensityGridAction = menu.addAction(icon, 'H3 density grid', self.h3DensityGrid)

        icon = QIcon(os.path.dirname(__file__) + '/icons/h3multidensity.svg')
        self.h3MultiDensityGridAction = menu.addAction(icon, 'H3 multi-layer density grid', self.h3MultiDensityGrid)
        
        icon = QIcon(os.path.dirname(__file__) + '/icons/h3grid.svg')
        self.h3GridAction = menu.addAction(icon, 'H3 grid', self.h3Grid)

        # Add the h3 tools to the menu
        icon = QIcon(os.path.dirname(__file__) + '/icons/h3.png')
        self.h3Actions = QAction(icon, 'H3 density algorithms', self.iface.mainWindow())
        self.h3Actions.setMenu(menu)
        self.iface.addPluginToMenu('Density analysis', self.h3Actions)

        # Add the h3 algorithms to the toolbar
        self.h3Button = QToolButton()
        self.h3Button.setMenu(menu)
        self.h3Button.setDefaultAction(self.h3Action)
        self.h3Button.setPopupMode(QToolButton.MenuButtonPopup)
        self.h3Button.triggered.connect(self.h3Triggered)
        self.h3Toolbar = self.toolbar.addWidget(self.h3Button)

        icon = QIcon(os.path.dirname(__file__) + '/icons/densitygrid.svg')
        self.densityGridAction = QAction(icon, "Styled density map", self.iface.mainWindow())
        self.densityGridAction.triggered.connect(self.densityGridAlgorithm)
        self.toolbar.addAction(self.densityGridAction)
        self.iface.addPluginToMenu("Density analysis", self.densityGridAction)

        icon = QIcon(os.path.dirname(__file__) + '/icons/densityexplorer.svg')
        self.heatmapAction = QAction(icon, "Density map analysis tool", self.iface.mainWindow())
        self.heatmapAction.triggered.connect(self.showHeatmapDialog)
        self.toolbar.addAction(self.heatmapAction)
        self.iface.addPluginToMenu("Density analysis", self.heatmapAction)

        icon = QIcon(os.path.dirname(__file__) + '/icons/kde.png')
        self.kdeAction = QAction(icon, "Styled heatmap (Kernel density estimation)", self.iface.mainWindow())
        self.kdeAction.triggered.connect(self.kdeAlgorithm)
        self.toolbar.addAction(self.kdeAction)

        self.iface.addPluginToMenu("Density analysis", self.kdeAction)
        icon = QIcon(os.path.dirname(__file__) + '/icons/styledrasterdensity.png')
        self.styledPolyDensityAction = QAction(icon, "Styled polygon density (raster)", self.iface.mainWindow())
        self.styledPolyDensityAction.triggered.connect(self.styledPolyDensityDialog)
        self.toolbar.addAction(self.styledPolyDensityAction)
        self.iface.addPluginToMenu("Density analysis", self.styledPolyDensityAction)

        icon = QIcon(os.path.dirname(__file__) + '/icons/polydensity.png')
        self.polyDensityAction = QAction(icon, "Polygon density (raster)", self.iface.mainWindow())
        self.polyDensityAction.triggered.connect(self.polyDensityDialog)
        self.iface.addPluginToMenu("Density analysis", self.polyDensityAction)

        icon = QIcon(os.path.dirname(__file__) + '/icons/vecpolydensity.png')
        self.styledPolyVecDensityAction = QAction(icon, "Styled polygon density (vector)", self.iface.mainWindow())
        self.styledPolyVecDensityAction.triggered.connect(self.styledPolyVecDensityDialog)
        self.iface.addPluginToMenu("Density analysis", self.styledPolyVecDensityAction)

        icon = QIcon(os.path.dirname(__file__) + '/icons/polydensity.png')
        self.polyVecDensityAction = QAction(icon, "Polygon density (vector)", self.iface.mainWindow())
        self.polyVecDensityAction.triggered.connect(self.polyVecDensityDialog)
        self.iface.addPluginToMenu("Density analysis", self.polyVecDensityAction)

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

        icon = QIcon(os.path.dirname(__file__) + '/icons/styleraster.png')
        self.rasterStyleAction = QAction(icon, "Apply pseudocolor raster style", self.iface.mainWindow())
        self.rasterStyleAction.triggered.connect(self.rasterStyleDialog)
        self.toolbar.addAction(self.rasterStyleAction)
        self.iface.addPluginToMenu("Density analysis", self.rasterStyleAction)

        # Settings
        icon = QIcon(':/images/themes/default/mActionOptions.svg')
        self.settingsAction = QAction(icon, 'Settings', self.iface.mainWindow())
        self.settingsAction.triggered.connect(self.settings)
        self.iface.addPluginToMenu('Density analysis', self.settingsAction)

        # Help
        icon = QIcon(os.path.dirname(__file__) + '/icons/help.svg')
        self.helpAction = QAction(icon, "Help", self.iface.mainWindow())
        self.helpAction.triggered.connect(self.help)
        self.iface.addPluginToMenu('Density analysis', self.helpAction)

        # Add the processing provider
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        self.iface.removePluginMenu('Density analysis', self.densityGridAction)
        self.iface.removePluginMenu('Density analysis', self.geohashActions)
        self.iface.removePluginMenu('Density analysis', self.h3Actions)
        self.iface.removePluginMenu('Density analysis', self.kdeAction)
        self.iface.removePluginMenu('Density analysis', self.graduatedStyleAction)
        self.iface.removePluginMenu('Density analysis', self.randomStyleAction)
        self.iface.removePluginMenu('Density analysis', self.styledPolyVecDensityAction)
        self.iface.removePluginMenu('Density analysis', self.polyVecDensityAction)
        self.iface.removePluginMenu('Density analysis', self.styledPolyDensityAction)
        self.iface.removePluginMenu('Density analysis', self.polyDensityAction)
        self.iface.removePluginMenu('Density analysis', self.heatmapAction)
        self.iface.removePluginMenu('Density analysis', self.style2layersAction)
        self.iface.removePluginMenu('Density analysis', self.rasterStyleAction)
        self.iface.removePluginMenu("Density analysis", self.settingsAction)
        self.iface.removePluginMenu("Density analysis", self.helpAction)
        if self.heatmap_dialog:
            self.iface.removeDockWidget(self.heatmap_dialog)
        # Remove Toolbar
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

    def geohashTriggered(self, action):
        self.geohashButton.setDefaultAction(action)

    def h3Triggered(self, action):
        self.h3Button.setDefaultAction(action)

    def geohashAlgorithm(self):
        processing.execAlgorithmDialog('densityanalysis:geohashdensitymap', {})

    def geohashMultiAlgorithm(self):
        processing.execAlgorithmDialog('densityanalysis:geohashmultidensitymap', {})

    def checkForH3(self):
        if self.h3_installed:
            return(True)
        try:
            import h3
            self.h3_installed = True
            return(True)
        except Exception:
            pass
        # H3 is not available
        QMessageBox.information(self.iface.mainWindow(), 'H3 Install Instructions', h3InstallString)
        return(False)

    def h3Algorithm(self):
        if self.checkForH3():
            processing.execAlgorithmDialog('densityanalysis:h3densitymap', {})

    def h3MultiAlgorithm(self):
        if self.checkForH3():
            processing.execAlgorithmDialog('densityanalysis:h3multidensitymap', {})
    
    def h3DensityGrid(self):
        if self.checkForH3():
            processing.execAlgorithmDialog('densityanalysis:h3density', {})
    
    def h3MultiDensityGrid(self):
        if self.checkForH3():
            processing.execAlgorithmDialog('densityanalysis:h3multidensity', {})
    
    def h3Grid(self):
        if self.checkForH3():
            processing.execAlgorithmDialog('densityanalysis:h3grid', {})

    def graduatedStyleAlgorithm(self):
        processing.execAlgorithmDialog('densityanalysis:graduatedstyle', {})

    def showRandomStyleDialog(self):
        processing.execAlgorithmDialog('densityanalysis:randomstyle', {})

    def polyDensityDialog(self):
        processing.execAlgorithmDialog('densityanalysis:polygondensity', {})

    def styledPolyVecDensityDialog(self):
        processing.execAlgorithmDialog('densityanalysis:styledpolygonvectordensity', {})

    def polyVecDensityDialog(self):
        processing.execAlgorithmDialog('densityanalysis:polygonvectordensity', {})

    def styledPolyDensityDialog(self):
        processing.execAlgorithmDialog('densityanalysis:styledpolygondensity', {})

    def rasterStyleDialog(self):
        processing.execAlgorithmDialog('densityanalysis:rasterstyle', {})

    def style2layers(self):
        if not self.style_Layers_dialog:
            from .style2layers import StyleToLayers
            self.style_Layers_dialog = StyleToLayers(self.iface, self.iface.mainWindow())
        self.style_Layers_dialog.show()
    
    def geohashDensityGrid(self):
        processing.execAlgorithmDialog('densityanalysis:geohashdensity', {})
    
    def geohashMultiDensityGrid(self):
        processing.execAlgorithmDialog('densityanalysis:geohashmultidensity', {})
    
    def kdeAlgorithm(self):
        processing.execAlgorithmDialog('densityanalysis:styledkde', {})

    def settings(self):
        if self.settingsDialog is None:
            self.settingsDialog = SettingsWidget(self.iface, self.iface.mainWindow())
        self.settingsDialog.show()

    def help(self):
        '''Display a help page'''
        import webbrowser
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)


