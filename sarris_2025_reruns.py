#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 11:16:15 2024

@author: shawn.carter
"""

import csv
import glob
import os
import numpy as np
import rasterio as rio
from rasterio.merge import merge 
import subprocess

#orbit= 165
def main(orbit):
    repo = '/Projects/remote_sensing/SARRIS_Code'
    ref_dir = '/Projects/remote_sensing/reference_images'
    gpt = '/Projects/Software/esa-snap/bin/gpt'
    process_xml = f'{repo}/SNAP_SAR_Preprocess.xml'
    stack_xml = f'{repo}/SNAP_SAR_MATH.xml'
    img_list = f'{ref_dir}/center_coords.csv'
    
    def align_extent_raster(raster_reference, raster_to_be_aligned, output):
        with rio.open(raster_reference) as src1:
            profile1 = src1.profile
            bounds1 = src1.bounds 
        
        with rio.open(raster_to_be_aligned) as src2:
            transform2 = src2.transform 
        
        window = rio.windows.from_bounds(*bounds1, transform=transform2)
        
        with rio.open(raster_to_be_aligned) as src2:
            smaller_array = src2.read(window=window, boundless=True)
        smaller_array = np.where(smaller_array == 0, np.nan, smaller_array)    
        with rio.open(output, 'w', **profile1) as dst:
            dst.write(smaller_array)
    
    # Classify Ice
    file_dir = '/Projects/remote_sensing/sarris_images'
    ref_dir = '/Projects/remote_sensing/reference_images'
    current_folder = os.path.join(file_dir, f'Orbit_{orbit}')
    s1_images = sorted(list([i for i in os.listdir(current_folder) if i.endswith('.data')]))
    ref_images_fldrs = sorted(list([i for i in os.listdir(ref_dir) if f'Orbit_{str(orbit)}_' in i and i.endswith('_new')]))
    
    
    
    for i, fldr in enumerate(s1_images):
        print(f'Working {fldr}')
        
        ref_img_url = os.path.join(ref_dir, ref_images_fldrs[i], f'{ref_images_fldrs[i][:-4]}.data')
        with rio.open(os.path.join(ref_img_url, 'VV_Mean.img')) as vv_mean_img:
            vv_mean = vv_mean_img.read(1)
            bounds = vv_mean_img.bounds
            
            if bounds.top > 52:
                fdd = '/Projects/Net_Degree_Days/Alaska/tif_folder/YTD_zero_final_warped.tif'
            else: fdd = '/Projects/Net_Degree_Days/tif_folder/YTD_zero_final_warped.tif'
                
        with rio.open(os.path.join(ref_img_url, 'VH_Mean.img')) as vh_mean_img:
            vh_mean = vh_mean_img.read(1)
        with rio.open(os.path.join(ref_img_url, 'VV_Stdev.img')) as vv_stdev_img:
            vv_stdev = vv_stdev_img.read(1)
        with rio.open(os.path.join(ref_img_url, 'VH_Stdev.img')) as vh_stdev_img:
            vh_stdev = vh_stdev_img.read(1)
        
        # Colocate Images to Reference Images
        
        print('Aligning current image to reference images.')
        raster_ref = os.path.join(ref_img_url, 'VV_Mean.img')
        align_extent_raster(raster_ref, 
                            os.path.join(current_folder, fldr, 'Gamma0_VV_db.img'), 
                            os.path.join(current_folder, fldr, 'Gamma0_VV_db_col.tif'))
        
        with rio.open(os.path.join(current_folder, fldr, 'Gamma0_VV_db_col.tif')) as vv_img:
            vv = vv_img.read(1)
            raster_profile = vv_img.profile
            
        align_extent_raster(raster_ref, 
                            os.path.join(current_folder, fldr, 'Gamma0_VH_db.img'), 
                            os.path.join(current_folder, fldr, 'Gamma0_VH_db_col.tif'))
        with rio.open(os.path.join(current_folder, fldr, 'Gamma0_VH_db_col.tif')) as vh_img:
            vh = vh_img.read(1)
            
        align_extent_raster(raster_ref, 
                            os.path.join(ref_img_url, 'Water_Mask.tif'), 
                            os.path.join(current_folder, fldr, 'Water_Mask.tif'))
        
        with rio.open(os.path.join(current_folder, fldr, 'Water_Mask.tif')) as wm_img:
            wm = wm_img.read(1)
            wm = np.where(vv != 0, wm, np.nan)
            
        align_extent_raster(raster_ref,
                            fdd,
                            os.path.join(current_folder, f'TDD_{i}.tif'))
        
        with rio.open(os.path.join(current_folder, f'TDD_{i}.tif')) as tdd_img:
            tdd = tdd_img.read(1)
            tdd = np.where(vv != 0, tdd, np.nan)
            
        # Calculate Delta
        vv_linear = 10**(vv/10)
        vv_mean_linear = 10**(vv_mean/10)  
        stdev_linear = 10**((vv_mean + vv_stdev)/10)
        
        
        copol_delta = abs(vv_mean) - abs(vv)
        
        river_ice = np.where(copol_delta < -2, 2, 
                             np.where(np.logical_and(copol_delta > -2, copol_delta < 1.5), 1, 
                             np.where(np.logical_and(copol_delta > 1.5, copol_delta < 4), 2, 
                             np.where(np.logical_and(copol_delta > 4, copol_delta < 9), 3,
                             np.where(copol_delta > 9, 4, np.nan)))))
        # Freeze Lakes
        river_ice = np.where(np.logical_and.reduce([tdd > 50, wm == 2, vv < -15, river_ice == 1]),2, river_ice)
        #river_ice = np.where(np.logical_and.reduce([tdd > 50, tdd < 150, wm == 2, vv > -15, river_ice == 2]), 1, river_ice)
        river_ice = np.where(np.logical_and.reduce([tdd > 50, wm == 2, vv > -9]), 3, river_ice)
        #river_ice = np.where(np.logical_and.reduce([tdd < 50, river_ice > 1]), 1, river_ice)
        
        # Mask out the land
        river_ice = np.where(np.logical_or(wm==1,wm==2), river_ice, np.nan)
        
        # Wind?
        #river_ice = np.where(np.logical_and.reduce([river_ice > 1, wm==1, vv < -19]), 1, river_ice)
        
        # Avoid borders in the Ref Image
        river_ice = np.where(np.isnan(vv), np.nan, river_ice)
        
        # Convert NaN to -9999
        nan_mask = np.isnan(river_ice)
        river_ice = np.where(nan_mask, -9999, river_ice)
        raster_profile.update(nodata=-9999)
        
        # Write the File
       
        raster_profile.update(compress='lzw')
        raster_profile.update(driver='GTiff')
        
        raster_profile.update(dtype='int16')
        with rio.open(os.path.join(current_folder, f'river_ice_classified_{i}.tif'), 'w', **raster_profile) as dst:
            dst.write(river_ice,1)
        
        vv_ratio = np.where(vv != 0, vv/vh, -9999)
        vv_mean = np.where(wm > 0, vv_mean, -9999)
        vv = np.where(wm>0, vv, -9999)
        vh = np.where(wm>0, vh, -9999)
        vv_ratio = np.where(wm>0, vv_ratio, -9999)
        
        raster_profile.update(count=3)
        raster_profile.update(dtype='float32')
        with rio.open(os.path.join(current_folder, f'RGB_{i}.tif'), 'w', **raster_profile) as dst:
            dst.write(vv, 1)
            dst.write(vh, 2)
            dst.write(vv_ratio, 3)
        
        
        
    raster_files = glob.glob(os.path.join(current_folder, 'river_ice_classified_*.tif'))
    
    # Merge all the rasters
    raster_to_mosaic = []
    for p in raster_files:
        src = rio.open(p)
        raster_to_mosaic.append(src)
    
    # Merge rasters
    mosaic, out_trans = merge(raster_to_mosaic)
    
    # Update metadata for the output mosaic
    out_meta = src.meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans
    })
    
    date = fldr[17:25]
    # Write the mosaic to a new file
    print('Saving the SARRIS Product.')
    with rio.open(os.path.join(current_folder, f'NWC_SARRIS_{date}_{orbit}.tif'), 'w', **out_meta) as dest:
        dest.write(mosaic)



    ref_images = []
    with open('/Projects/remote_sensing/reference_images/center_coords.csv', 'r') as csvFile:
        for row in csvFile:
            if row.split(',')[0] != 'Orbit':
                if int(row.split(',')[0]) == int(orbit):
                    ref_images.append(row)
    num_ref_images = len(ref_images)

    if len(s1_images) == num_ref_images:
        date_with_hyphens = f'{date[0:4]}-{date[4:6]}-{date[6:8]}'
        subprocess.call([f'{repo}/polygonize_sarris.sh', orbit, f'NWC_SARRIS_{date}_{orbit}.tif', f'NWC_SARRIS_{date}_{orbit}.shp'])
        with open('/Projects/remote_sensing/SARRIS_Code/orbit_processing_log.csv', 'a') as csvFile:
            new_row = [orbit, date_with_hyphens]
            writer = csv.writer(csvFile, delimiter = ',')
            writer.writerow(new_row)
        
