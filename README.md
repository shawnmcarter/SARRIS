# Synthetic Aperture Radar River Ice Surveillance (SARRIS)

This repository contains the documentation and code for SARRIS, a simple python enabled method of mapping out river ice using Copernicus Sentinel-1 Synthetic Aperture Radar (SAR) imagery.  The process is predicated on maintaining a library
of synthetic reference images constructed from ice free images as close to freeze-up as possible.  Synthetic reference images are constructed by stacking the ice free imagery and taking a pixelwise mean value for each image.  The wintertime 
image is then compared against the synthetic reference images and classified by the absolute delta between radar backscatter over water images.  The images are then masked to only normal water extents and then visualized.

## Dependencies
