#-------------------------------------------------------------------------------
# Name:        PRISM_Mean_RasterValue_by_SHP.py
# Purpose:     Create a dbf to read mean value of each PRISM raster 
# Author:      Rachel Fan
# Created:     2/2/2024

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

def zonal_statistics_summary(basin_shapefile, zone_field, output_folder, raster):
    try:
        output_table_name = os.path.splitext(os.path.basename(raster))[0]
        
        table_name = output_table_name[0:8]            
        output_table_path = os.path.join(output_folder, table_name + ".dbf")

        arcpy.gp.ZonalStatisticsAsTable_sa(basin_shapefile, zone_field, raster, output_table_path, "DATA", statistics_type)

        return output_table_path

    except Exception as e:
        arcpy.AddError(str(e))
        arcpy.AddMessage(arcpy.GetMessages())
        return None

if __name__ == "__main__":

    
    input_folder = arcpy.GetParameterAsText(0)
    output_folder = arcpy.GetParameterAsText(1)
    basin_shapefile = arcpy.GetParameterAsText(2)
    zone_field = arcpy.GetParameterAsText(3)
    #statistics_type=arcpy.GetParameterAsText(4)
    statistics_type= "MEAN"
    
    '''
    
    input_folder=r"U:\1937\193709666\03_data\gis_cad\gis\Basin_Characteristics\SourceData\PRISM_ppt_30yr_normal_800mM4"
    output_folder=r"U:\1937\193709666\03_data\gis_cad\gis\Basin_Characteristics_Testing\Testing_Dataset\ToolT-est"
    basin_shapefile=r"U:\1937\193709666\03_data\gis_cad\gis\Basin_Characteristics_Testing\Testing_Dataset\basins_list.shp"
    zone_field="Basin_ID"
    statistics_type= "MEAN"
    '''
    
    print("Parameters read. Functions start!")

    gdb_name = "PRISM"
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
    
    temp_folder = os.path.join(gdb_folder, "prism_temp_tables")
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)


    print("Temp folder created")
    print(temp_folder)

    # Initialize the intermediate tables list at the beginning of the script
    intermediate_tables = []

    # Process each raster and create intermediate tables
  
    for raster in rasters:
        intermediate_table = zonal_statistics_summary(basin_shapefile, zone_field, temp_folder, raster)
        print('looping intermedite table')
        print(intermediate_table)
        intermediate_tables.append(intermediate_table)

    
    #arcpy.Merge_management([os.path.join(temp_folder, table_name + ".dbf") for table_name in set([os.path.splitext(os.path.basename(raster))[0] for raster in rasters])], final_output_table)
    
    print('intermediate tables are... ')
    print(intermediate_tables)       
    

    
    # Create a dictionary to store the values for each intermediate table
    values_dict = {}
    
    # Loop through intermediate tables to populate the dictionary
    for intermediate_table in intermediate_tables:
        table_name = os.path.splitext(os.path.basename(intermediate_table))[0]
        with arcpy.da.SearchCursor(intermediate_table, ["GID", "MEAN"]) as cursor:
            for row in cursor:
                gid, mean_value = row[0], row[1]
                if gid not in values_dict:
                    values_dict[gid] = {}
                values_dict[gid][table_name] = mean_value
    
    print('values_dict is... ')
    print(values_dict)    
    
    
    # Create a list of unique Basins_IDs from values_dict
    unique_basin_ids = list(values_dict.keys())
    print("unique_basin_ids are")
    print(unique_basin_ids)

    # Create the table
    final_output_table = os.path.join(gdb_path, "PRISM")
    
    arcpy.CreateTable_management(gdb_path, "PRISM")
    arcpy.AddField_management(final_output_table, "GID", "TEXT")
    
    #Populate the new table with the unique_basin_ids values
    with arcpy.da.InsertCursor(final_output_table,["GID"]) as cursor:
        for gid in unique_basin_ids:
            cursor.insertRow([gid])

    
    # Add PRISM fields
    
    # Define the field names and data types based on values_dict
    field_names = list(values_dict[unique_basin_ids[0]].keys())
    field_types = ["DOUBLE"] * len(field_names)
    print('field_names are')
    print(field_names)
    
    # Add fields to the table
    for field_name, field_type in zip(field_names, field_types):
        arcpy.AddField_management(final_output_table,field_name,field_type)
        print(field_name)
        print("field added")
  
    print('final_output_table is... ')
    print(final_output_table)


    # Create an update cursor to modify the table
    with arcpy.da.UpdateCursor(final_output_table, ["GID"] + field_names) as cursor:
        field_names = cursor.fields  # Get the field names
        print(field_names)
        for row in cursor:
            gid = row[0]
            print("Start looping writing PRISM")
            print('basin_id is')
            print(gid)

            if gid in values_dict:
                for table_name, mean_value in values_dict[gid].items():
                    # Handle special characters in field names
                    print('table name is')
                    print(table_name)
                    field_name = table_name 
                    if field_name in field_names:
                        field_index = field_names.index(field_name)
                        row[field_index] = mean_value
                        print('field_name is in the loop is')
                        print(field_name)
                    else:
                        print(f"Field {field_name} not found in the table.")
                cursor.updateRow(row)
    
    
# Check in Spatial Analyst extension
arcpy.CheckInExtension("Spatial")