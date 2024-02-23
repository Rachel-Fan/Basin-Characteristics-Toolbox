#-------------------------------------------------------------------------------
# Name:        NOAA_Atlas14_Center_RasterValue_by_SHP.py
# Purpose:     Create a dbf to read mean value of each NOAA Atlas14 raster 
# Author:      Rachel Fan
# Created:     2/6/2024

#-------------------------------------------------------------------------------
import arcpy
from arcpy.sa import *
import csv
import sys
import os
from os import path

# Check Spatial Analyst extention
arcpy.CheckOutExtension("Spatial")
#Define input and output parameters
arcpy.env.overwriteOutput = True

def create_basin_centroid(basin_shapefile, output_folder, output_point_shapefile):
        
    # Create a duplicate of the basin shapefile under the temporary folder
    arcpy.Copy_management(basin_shapefile, basin_shapefile_copy)
    print('basin_shapefile_copy is at ')
    print(basin_shapefile_copy)
    
    # Add centroid_x and centroid_y fields to the copy of the basin shapefile
    arcpy.AddField_management(basin_shapefile_copy, "centroid_x", "DOUBLE")
    arcpy.AddField_management(basin_shapefile_copy, "centroid_y", "DOUBLE")
    
    # Calculate geometry to populate centroid_x and centroid_y fields
    arcpy.CalculateGeometryAttributes_management(basin_shapefile_copy, [["centroid_x", "CENTROID_X"], ["centroid_y", "CENTROID_Y"]])
    print("calculate geometry done")
    
    
    # Run XY Table to Point to create a point shapefile from centroid coordinates
    arcpy.management.XYTableToPoint(basin_shapefile_copy, output_point_shapefile, "centroid_x", "centroid_y", None, coordinate_system='PROJCS["NAD_1983_StatePlane_Nebraska_FIPS_2600_Feet",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",1640416.666666667],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-100.0],PARAMETER["Standard_Parallel_1",40.0],PARAMETER["Standard_Parallel_2",43.0],PARAMETER["Latitude_Of_Origin",39.83333333333334],UNIT["Foot_US",0.3048006096012192]];-119097700 -96454900 37300567.3219182;-100000 10000;-100000 10000;3.28083333333333E-03;0.001;0.001;IsHighPrecision')
    
    print("Centroid points shapefile created successfully at:", output_point_shapefile)


if __name__ == "__main__":
    
    
    input_folder = arcpy.GetParameterAsText(0)
    output_folder = arcpy.GetParameterAsText(1)
    basin_shapefile = arcpy.GetParameterAsText(2)
    
    
    print("Parameters read. Functions start!")
    
    gdb_name = "Atlas14"
    gdb_folder = os.path.join(output_folder, gdb_name)
    
    # Check if the folder exists; if not, create it
    if not os.path.exists(gdb_folder):
        os.makedirs(gdb_folder)
        
    # Create the file geodatabase
    gdb_path = os.path.join(gdb_folder, gdb_name + ".gdb")
    # Check if the geodatabase exists; if not, create it
    if not arcpy.Exists(gdb_path):
        arcpy.CreateFileGDB_management(gdb_folder, gdb_name)
        print('GDB created')
        
    all_files= os.listdir(input_folder)
    rasters = [os.path.join(input_folder, file) for file in all_files if file.lower().endswith(".tif")]
    print("Number of rasters are ")
    print(len(rasters))
    print(rasters)
    
    # Create a temporary folder if it doesn't exist
    temp_folder = os.path.join(gdb_folder, "temp")
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    
    # Create a duplicate of the basin shapefile under the temporary folder
    basin_shapefile_copy = os.path.join(temp_folder, os.path.basename(basin_shapefile))
    
    # Define output point shapefile path
    output_point_shapefile = os.path.join(temp_folder, "basin_centroid_points.shp")
    
    print("Temp folder created")
    print(temp_folder)

    create_basin_centroid(basin_shapefile, gdb_folder, output_point_shapefile)
    print("output_point_shapefile created at")
    print(output_point_shapefile)

    # Run Extract Multi Values to Points tool
    arcpy.sa.ExtractMultiValuesToPoints(output_point_shapefile, rasters, "NONE")
    
    print(f"Values extracted from rasters to points shapefile: {output_point_shapefile}")


    final_output_table = os.path.join(gdb_path, "NOAA_Atlas14_Precipitation_Frequency")

    # Create the final output table and add fields
    arcpy.CreateTable_management(gdb_path, "NOAA_Atlas14_Precipitation_Frequency")
    arcpy.AddField_management(final_output_table, "GID", "TEXT")
    arcpy.AddField_management(final_output_table, "PrecFr10yr", "DOUBLE")
    arcpy.AddField_management(final_output_table, "PrecFr2yr", "DOUBLE")

    # Retrieve unique GIDs from output_point_shapefile
    gids = set()
    with arcpy.da.SearchCursor(output_point_shapefile, "GID") as cursor:
        for row in cursor:
            gids.add(row[0])
    print("gids are")
    print(gids)

    # Insert records into final_output_table
with arcpy.da.InsertCursor(final_output_table, ["GID", "PrecFr10yr", "PrecFr2yr"]) as cursor:
    for gid in sorted(gids):
        # Get PrecFr10yr and PrecFr2yr values for the current GID
        prec_fr_10yr = None
        prec_fr_2yr = None
        with arcpy.da.SearchCursor(output_point_shapefile, ["GID", "Atlas14_10", "Atlas14_2y"], where_clause=f"GID = '{gid}'") as search_cursor:
            for row in search_cursor:
                gid, prec_fr_10yr, prec_fr_2yr = row
                # Divide the values by 1000
                prec_fr_10yr /= 1000
                prec_fr_2yr /= 1000
                break  # Assuming there's only one record per GID
        
        # Insert values into the final_output_table
        cursor.insertRow((gid, prec_fr_10yr, prec_fr_2yr))

    print("Final output table created successfully at:", final_output_table)


    
# Check in Spatial Analyst extension
arcpy.CheckInExtension("Spatial")