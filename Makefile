PLUGINNAME = densityanalysis
PLUGINS = "$(HOME)"/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)
PY_FILES = __init__.py densityanalysis.py densityanalysisprocessing.py densitygrid.py geohash.py geohashdensity.py geohashdensitymap.py geohashmultidensity.py geohashmultidensitymap.py graduatedstyle.py h3density.py h3densitymap.py h3grid.py h3multidensity.py h3multidensitymap.py heatmap.py polygondensity.py polyvectordensity.py provider.py randomstyle.py rasterstyle.py settings.py style2layers.py styledkde.py styledpolygondensity.py styledpolyvectordensity.py utils.py
EXTRAS = metadata.txt icon.png LICENSE

deploy:
	mkdir -p $(PLUGINS)
	cp -vf $(PY_FILES) $(PLUGINS)
	cp -vf $(EXTRAS) $(PLUGINS)
	cp -vfr icons $(PLUGINS)
	cp -vfr ui $(PLUGINS)
	cp -vfr help $(PLUGINS)
	cp -vf helphead.html index.html
	python -m markdown -x extra readme.md >> index.html
	echo '</body>' >> index.html
	cp -vf index.html $(PLUGINS)/index.html
