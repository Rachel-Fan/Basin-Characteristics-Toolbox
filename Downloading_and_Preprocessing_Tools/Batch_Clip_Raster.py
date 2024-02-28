import arcpy
import os
import time



# Check Spatial Analyst extension
arcpy.CheckOutExtension("Spatial")
# Enable overwriting of output files
arcpy.env.overwriteOutput = True

def batch_clip_raster(input_folder, input_raster, output_folder):
    # Set workspace environment
    arcpy.env.workspace = input_folder
    arcpy.env.overwriteOutput = True

    # Check out Spatial Analyst extension
    arcpy.CheckOutExtension("Spatial")

    # Loop through each shapefile in the input folder
    for shapefile in arcpy.ListFeatureClasses("*.shp"):
        # Extract the filename without extension
        file_name = os.path.splitext(shapefile)[0]
        
        # Output raster name
        output_raster = os.path.join(output_folder, file_name + "_NLCD.tif")
        
        # Perform extract by mask
        arcpy.gp.ExtractByMask_sa(input_raster, shapefile, output_raster)

    # Release Spatial Analyst extension
    arcpy.CheckInExtension("Spatial")

print("Tool starts")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)


# Input folder containing HUC4 shapefiles
input_folder = arcpy.GetParameterAsText(0)

# Input NLCD raster
input_raster = arcpy.GetParameterAsText(1)

output_folder = r"C:\Users\Rachel\Documents\ArcGIS Pro 3.2\Projects\NE_Basin\Basin_Characteristics\NLCD_V2"


# Create output NLCD table with categories

batch_clip_raster(input_folder, input_raster, output_folder)
print("NLCD table populated at", time.ctime())  # Track progress
print('****************************************')

print("All Done", time.ctime())  # Track progress
