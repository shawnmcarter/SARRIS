import csv
from datetime import datetime, timedelta
import os
import pandas as pd
import requests
import subprocess
import sarris_2025 as sarris

# Folder Locations
ref_images = '/Projects/remote_sensing/reference_images'
sarris_images = '/Projects/remote_sensing/sarris_images'
s3_script = '/Projects/remote_sensing/SARRIS_Code/GET_S1_S3.sh'
gpt = '/Projects/Software/esa-snap/bin/gpt'
repo = '/Projects/remote_sensing/SARRIS_Code'


# Time Constraints
end_date = datetime.now()
start_date = end_date - timedelta(days=1)
start_date = start_date.strftime('%Y-%m-%d')
end_date = end_date.strftime('%Y-%m-%d')


with open('/Projects/remote_sensing/reference_images/center_coords.csv', 'r') as csvFile:  #CSV with Orbit Number, center Lat/Lon, and Node Direction
    reader = csv.reader(csvFile)
    data = list(reader)


urls = []
orbits = []
frame = []
for i, image in enumerate(data):
    if i > 0:
        orbit_number = image[0]
        url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?'
        search = (f"$filter=contains(Name,'S1A_IW_GRD') and ContentDate/Start gt {start_date}T00:00:00.000Z and "\
              f"ContentDate/Start lt {end_date}T23:59:59.999Z and "\
              f"Attributes/OData.CSC.IntegerAttribute/any(att:att/Name eq 'relativeOrbitNumber' and "\
              f"att/OData.CSC.IntegerAttribute/Value eq {orbit_number}) and "\
              f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and "\
              f"att/OData.CSC.StringAttribute/Value eq 'IW_GRDH_1S') and "\
              f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'orbitDirection' and "\
              f"att/OData.CSC.StringAttribute/Value eq '{image[4]}') and "\
              f"OData.CSC.Intersects(area=geography%27SRID=4326;POINT({image[3]}%20{image[2]})%27)&$orderby=ContentDate/Start")
    
        json = requests.get(f"{url}{search}").json()
        try:
            df = pd.DataFrame.from_dict(json['value'])
            if not df.empty:
                urls.append(df['S3Path'][0])
                orbits.append(image[0])
                frame.append(image[1])
            else:
                print(f'Orbit Number: {orbit_number} Unavailable.')
        except KeyError:
            pass

log = []
with open('/Projects/remote_sensing/SARRIS_Code/orbit_processing_log.csv', 'r') as csvFile: #CSV File with previously processed images to prevent reprocessing swaths that have been completed
    reader = csv.DictReader(csvFile)
    for row in reader:
        log.append(row)

processed_images = []
for i in log:
    process_date = datetime.strptime(i['date'], '%Y-%m-%d')
    current_date = datetime.now()
    if abs(current_date - process_date).days < 6: # The minimal repeat image time in the SARRIS Domain
        processed_images.append(i['orbit']) # Completed images in the processing log


aggregated_orbits = set(orbits)
for individual_orbit in aggregated_orbits:
    s3_url = []
    frames = []
    if individual_orbit in processed_images:                                   
        print(f'Orbit: {individual_orbit} Image Processed, Skipping')
    else:
        save_dir = f'/Projects/remote_sensing/sarris_images/Orbit_{individual_orbit}'
        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)
        for i, orbit in enumerate(orbits):
            if orbit == individual_orbit:
                s3_url.append(urls[i])
                frames.append(frame[i])
        for individual_frame in s3_url:
            subprocess.call([s3_script, individual_frame, individual_orbit])
        
        if individual_orbit in ['62']:
            process_xml = f'{repo}/SNAP_SAR_Preprocess_10m.xml'
        else:
            process_xml = f'{repo}/SNAP_SAR_Preprocess.xml'
            
        safe_folders = [i for i in os.listdir(save_dir) if i.endswith('.SAFE')]
        for i, image in enumerate(safe_folders):
            raw_s1 = os.path.join(save_dir, image)
            subprocess.call([gpt, 
                            process_xml, 
                            f'-Pfile={raw_s1}', 
                            f'-Poutput={raw_s1[:-5]}_RTC.dim'])
        sarris.main(individual_orbit)
