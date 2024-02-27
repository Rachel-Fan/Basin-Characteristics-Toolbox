#-------------------------------------------------------------------------------
# Name:        Extract_shp_from_SoilsMapUnits_Feature_Service.py
# Purpose:     Export LivingAtls - US SoilsMapUnits feature service dataset to local by tiles
# Author:      Rachel Fan
# Created:     2/2/2024


import arcpy
from arcpy.sa import *
import os
import time

# Check Spatial Analyst extention
arcpy.CheckOutExtension("Spatial")
#Define input and output parameters
arcpy.env.overwriteOutput = True

print("Tool starts")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)


# Define the paths to your input shapefile and the folder containing your clipping shapefiles
input_shapefile = "https://landscape11.arcgis.com/arcgis/rest/services/USA_Soils_Map_Units/featureserver/0"
clipping_folder = r"E:\NE\DEM_Extent_Tiles"
output_folder = r"E:\NE\Basin_Characteristics\Downloading_SoilMapUnits\64-79"

# Set the workspace to the clipping folder to list all shapefiles
arcpy.env.workspace = clipping_folder

# List all shapefiles in the clipping folder
clipping_shapefiles = arcpy.ListFeatureClasses()

# Loop through each clipping shapefile
for clipping_shapefile in clipping_shapefiles:
    clipping_path = os.path.join(clipping_folder, clipping_shapefile)
    

    
   
    # Define the output shapefile name based on the clipping shapefile name
    output_shapefile_name = f"clipped_{os.path.splitext(clipping_shapefile)[0]}.shp"
    output_shapefile_path = os.path.join(output_folder, output_shapefile_name)

    # Construct the path to the clipping shapefile
    current_time = time.strftime("%m-%d %X",time.localtime())
    
    print('*****************************')
    print(f"Start clipping {output_shapefile_name} at")
    print(current_time)

   
   
    # Perform the clipping operation
    arcpy.Clip_analysis(input_shapefile, clipping_path, output_shapefile_path)
   
    
    current_time = time.strftime("%m-%d %X",time.localtime())
    print(f"{output_shapefile_name} is clipped")
    print(current_time)
    print(f"Clipped output saved to: {output_shapefile_path}")
    print('*****************************')

print("Batch clipping process completed.")


print("Tool done at:")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)
