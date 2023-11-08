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
def classFactory(iface):
    if iface:
        from .densityanalysis import DensityAnalysis
        return DensityAnalysis(iface)
    else:
        # This is used when the plugin is loaded from the command line command qgis_process
        from .densityanalysisprocessing import DensityAnalysis
        return DensityAnalysis()
