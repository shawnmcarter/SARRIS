#!/bin/bash
orbit=$1
raster=$2
shp=$3

gdal_polygonize.py /Projects/remote_sensing/sarris_images/Orbit_${orbit}/${raster} -b 1 -f "ESRI Shapefile" /Projects/remote_sensing/sarris_images/${shp} ${shp%.*} Ice_Class

gdal_footprint -convex_hull /Projects/remote_sensing/sarris_images/Orbit_${orbit}/${raster} /Projects/remote_sensing/sarris_images/${shp%.*}_extent.shp
