#-------------------------------------------------------------------------------
# Name:        EcoRegion_Area_Percentage_by_SHP.py
# Purpose:     Create a DBF to read area percentage of each ecoregion L4 category
#              for all records in a basins shapefile.
# Author:      Rachel Fan
# Created:     2/12/2024
#-------------------------------------------------------------------------------

import arcpy
import os
import time

print("Tool starts")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)


# Check Spatial Analyst extension
arcpy.CheckOutExtension("Spatial")
# Enable overwriting of output files
arcpy.env.overwriteOutput = True

def batch_clip(input_ecoregion, input_clip_polygon, output_directory):
    """
    Clips an input ecoregion shapefile using each polygon in an input clip polygon shapefile.
    Creates a clipped shapefile for each polygon based on its GID.
    """
    # Set the workspace to the directory of the input ecoregion shapefile
    arcpy.env.workspace = os.path.dirname(input_ecoregion)
    
    # Ensure the output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    # Create a feature layer from the clip polygon shapefile
    clip_polygon_layer = "clip_polygon_layer"
    arcpy.MakeFeatureLayer_management(input_clip_polygon, clip_polygon_layer)
    
    # Iterate over each polygon in the clip layer using its GID to define output filenames
    with arcpy.da.SearchCursor(clip_polygon_layer, ["GID"]) as cursor:
        for row in cursor:
            gage_id = row[0]
            query = f"GID = '{gage_id}'"
            arcpy.SelectLayerByAttribute_management(clip_polygon_layer, "NEW_SELECTION", query)
            
            output_shapefile = os.path.join(output_directory, f"{gage_id}_Ecoregion.shp")
            arcpy.analysis.Clip(input_ecoregion, clip_polygon_layer, output_shapefile)
            print(f"Clipped and saved: {output_shapefile}")
    
    arcpy.SelectLayerByAttribute_management(clip_polygon_layer, "CLEAR_SELECTION")
    print("Batch clipping completed.")

def calculate_area_percentage(input_directory):
    """
    Adds 'Area' and 'Percentage' fields to shapefiles in a directory, calculates the area for each feature,
    and calculates each feature's percentage of the total area.
    """
    arcpy.env.workspace = input_directory
    shapefiles = arcpy.ListFeatureClasses("*.shp")
    
    for shapefile in shapefiles:
        arcpy.AddField_management(shapefile, "Area", "DOUBLE")
        arcpy.CalculateField_management(shapefile, "Area", "!shape.area@ACRES!", "PYTHON3")
        arcpy.AddField_management(shapefile, "Percentage", "DOUBLE")
        
        total_area = sum(row[0] for row in arcpy.da.SearchCursor(shapefile, ["Area"]))
        
        with arcpy.da.UpdateCursor(shapefile, ["Area", "Percentage"]) as cursor:
            for row in cursor:
                row[1] = (row[0] / total_area) * 100
                cursor.updateRow(row)
        print(f"Processed {shapefile}")    

def sanitize_field_name(name):
    """Sanitizes the field name to conform to ArcGIS naming conventions."""
    # Replace spaces with underscores and remove any other non-alphanumeric characters
    clean_name = ''.join(char if char.isalnum() else '_' for char in name)
    # Ensure the field name does not start with a digit
    if clean_name[0].isdigit():
        clean_name = "f" + clean_name
    return clean_name

def create_gdb_and_table(input_shapefiles_folder, output_folder):
    """
    Creates a Geodatabase and a table within it to organize area percentage data from shapefiles.
    """
    gdb_path = arcpy.CreateFileGDB_management(output_folder, "EcoregionData.gdb")[0]
    table_path = arcpy.CreateTable_management(gdb_path, "Ecoregion")[0]
    arcpy.AddField_management(table_path, "GID", "TEXT")
    
    arcpy.env.workspace = input_shapefiles_folder
    shapefiles = arcpy.ListFeatureClasses("*.shp")
    fields_added = {}
    
    for shapefile in shapefiles:
        gid = os.path.basename(shapefile)[:8]
        with arcpy.da.InsertCursor(table_path, ["GID"]) as cursor:
            cursor.insertRow([gid])
        
        with arcpy.da.SearchCursor(shapefile, ["US_L4NAME", "Percentage"]) as cursor:
            for row in cursor:
                us_l4name, percentage = row
                sanitized_name = sanitize_field_name(us_l4name)
                if sanitized_name not in fields_added:
                    arcpy.AddField_management(table_path, sanitized_name, "DOUBLE")
                    fields_added[sanitized_name] = True
                
                with arcpy.da.UpdateCursor(table_path, ["GID", sanitized_name]) as updateCursor:
                    for updateRow in updateCursor:
                        if updateRow[0] == gid:
                            updateRow[1] = percentage
                            updateCursor.updateRow(updateRow)
                            break
    print(f"Table 'Ecoregion' successfully created and populated in 'EcoregionData.gdb'.")

if __name__ == "__main__":
    # Set your input and output paths here
    
    '''
    input_raster = arcpy.GetParameterAsText(0)
    input_polygon = arcpy.GetParameterAsText(1)
    output_folder = arcpy.GetParameterAsText(2)
    #gdb_name = arcpy.GetParameterAsText(3)
    gdb_name = "NLCD"
    
    
    input_ecoregion = r"U:\1937\193709666\03_data\gis_cad\gis\Basin_Characteristics\SourceData\EcoRegion\ecoregion_DEM_extent.shp"
    input_clip_polygon = r"U:\1937\193709666\03_data\gis_cad\gis\Basin_Characteristics_Testing\Testing_Dataset\PreProcessing_1021\basins_final_merge.shp"
    output_folder = r"U:\1937\193709666\03_data\gis_cad\gis\Basin_Characteristics_Testing\Testing_Dataset\ecoregion_test"
    '''
    
    input_ecoregion = r"E:\NE\Basin_Characteristics\EcoRegion\ecoregion_DEM_extent.shp"
    input_clip_polygon = r"E:\NE\Basin_Characteristics\PreProcessing_1021\basins_final_merge.shp"
    output_folder = r"E:\NE\Basin_Characteristics\Testing_Dataset"
    
    
    
    print('Parameters are read. Start processing...')
    
    # Prepare directories for shapefile output and GDB creation
    gdb_folder = os.path.join(output_folder, "EcoregionData")
    if not os.path.exists(gdb_folder):
        os.makedirs(gdb_folder)
    
    shp_folder = os.path.join(gdb_folder, "Ecoregion_by_Basins")
    if not os.path.exists(shp_folder):
        os.makedirs(shp_folder)
    
    # Perform batch clipping, area percentage calculation, and table creation
    batch_clip(input_ecoregion, input_clip_polygon, shp_folder)
    print('Ecoregion has been batch clipped at')
    current_time = time.strftime("%m-%d %X",time.localtime())
    print(current_time)
    
    calculate_area_percentage(shp_folder)
    print('Area and percentage calculations are complete at')
    current_time = time.strftime("%m-%d %X",time.localtime())
    print(current_time)
    
    create_gdb_and_table(shp_folder, gdb_folder)
    print('Main function completed at')
    current_time = time.strftime("%m-%d %X",time.localtime())
    print(current_time)
    
    print("Tool done at:")
    current_time = time.strftime("%m-%d %X",time.localtime())
    print(current_time)

