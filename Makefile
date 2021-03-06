PLUGINNAME = densityanalysis
PLUGINS = "$(HOME)"/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)
PY_FILES = __init__.py densityanalysis.py densitygrid.py geohash.py geohashdensity.py geohashdensitymap.py graduatedstyle.py h3density.py h3densitymap.py heatmap.py polygondensity.py provider.py randomstyle.py rasterstyle.py style2layers.py utils.py
EXTRAS = metadata.txt icon.png

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
