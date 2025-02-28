# Synthetic Aperture Radar River Ice Surveillance (SARRIS)

This repository contains the documentation and code for SARRIS, a simple python enabled method of mapping out river ice using Copernicus Sentinel-1 Synthetic Aperture Radar (SAR) imagery.  The process is predicated on maintaining a library
of synthetic reference images constructed from ice free images as close to freeze-up as possible.  Synthetic reference images are constructed by stacking the ice free imagery and taking a pixelwise mean value for each image.  The wintertime 
image is then compared against the synthetic reference images and classified by the absolute delta between radar backscatter over water images.  The images are then masked to only normal water extents and then visualized.

## Dependencies
Python Dependencies:
- csv
- glob
- numpy
- rasterio
- subprocess

System Dependencies:
- Copernicus SeNtinel APplications (SNAP) gpt command line application

Reference Image Library
- Reference image of images constructed during ice free conditions
- - Gamma0_VV Mean Image
- - Gamma0_VH Mean Image
- - Water Mask Image
- Water Mask representing where SARRIS classifications will be limited to
- CSV with the following column names: Orbit, Frame, Lat, Lon, Node
- CSV to log completed orbit swath acquisitions
