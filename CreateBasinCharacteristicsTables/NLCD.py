#-------------------------------------------------------------------------------
# Name:        NLCD_Area_Percentage_by_SHP.py
# Purpose:     Create a dbf to read area percentage of each NLCD category for all records in a shapefile
# Author:      Rachel Fan
# Created:     2/2/2024
#-------------------------------------------------------------------------------
import arcpy
from arcpy.sa import *

import os
from os import path
import time

print("Tool starts")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)

# Check Spatial Analyst extention
arcpy.CheckOutExtension("Spatial")
#Define input and output parameters
arcpy.env.overwriteOutput = True
def batch_clip_raster(input_raster,input_polygon, output_folder, gdb_name):
    #input_raster = r"U:\1937\193709666\03_data\gis_cad\gis\Basin_Characteristics_Testing\PRISM_NE_01.tif"
    #input_polygon = r"U:\1937\193709666\03_data\gis_cad\gis\Basin_Characteristics\SourceData\NeDNR_HUC8_Watersheds_SP_Buffer.shp"
    #output_folder = r"C:\Users\rfan\Documents\Test"
    #gdb_name = 'PRISM_annual'
    #gdb_path = arcpy.os.path.join(output_folder,gdb_name)
    #Define input and output parameters
    arcpy.env.overwriteOutput = True
    
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
    
    # Create a directory with the same name as gdb_name under output_folder
    tif_folder = os.path.join(gdb_folder, f"{gdb_name}_tif")
    # Check if the folder exists; if not, create it
    if not os.path.exists(tif_folder):
        os.makedirs(tif_folder)
        
    print('gdb_path:', gdb_path)
     
    arcpy.env.workspace = gdb_path
    #spatial_ref = arcpy.Describe(input_polygon).spatialReference
    #arcpy.env.outputCoordinateSystem = spatial_ref
    arcpy.env.overwriteOutput = True 
    print('')  
     
    print('dictionary read')
    
    #field_to_add_1 = "Mean_Value"
    
    arcpy.management.CreateTable(gdb_path , f"{gdb_name}")
    #arcpy.management.AddField(f"{gdb_name}", "GID", "integer")
    #arcpy.management.AddField(f"{gdb_name}", field_to_add_1, "float")
        # List of fields to add
    fields_to_add = ["Water", "Developed", "Barren", "Forest", "Shrubland", "Herbaceous", "Planted/Cultivated", "Wetlands"]
    # Create a new table in the geodatabase
    table_path = arcpy.management.CreateTable(gdb_path, gdb_name)
    # Add a field for "GID"
    arcpy.management.AddField(table_path, "GID", "TEXT")
    # Add the fields specified in the "fields_to_add" array
    for field_name in fields_to_add:
        arcpy.management.AddField(table_path, field_name, "FLOAT")
     
    with arcpy.da.SearchCursor(input_polygon, ["FID", "SHAPE@", "GID"]) as cursor:
        for row in cursor:
            feature_id = row[0]
            polygon_geometry = row[1]
            feature_name = row[2]
            print(feature_name)
            
            arcpy.env.extent = polygon_geometry.extent
            mask = ExtractByMask(input_raster, polygon_geometry)
            
            output_raster = arcpy.os.path.join(tif_folder, f"{feature_name}_{gdb_name}.tif")
            #arcpy.management.CopyRaster(mask, f"{feature_name}_{gdb_name}")
            mask.save(output_raster)
            print("***************output raster created *******************")
            print(output_raster)
            print("*********************************************************")
            
            arcpy.env.extent = None
            
    print("all done")
    return
def convertTifToShp(tif_folder, shp_folder, output_folder, gdb_name):
    
    
    # List all raster files in the tif_folder
    raster_files = [f for f in os.listdir(tif_folder) if f.endswith(".tif")]
    # Loop through each raster and convert to shapefile
    for raster_file in raster_files:
        # Construct the full paths
        tif_path = os.path.join(tif_folder, raster_file)
        shp_path = os.path.join(shp_folder, os.path.splitext(raster_file)[0] + ".shp")
        # Use RasterToPolygon tool to convert raster to shapefile
        arcpy.conversion.RasterToPolygon(tif_path, shp_path, "SIMPLIFY")
        
    return
def addCatField(shp_folder, field_name):
    # Set the workspace to the folder containing the shapefiles
    arcpy.env.workspace = shp_folder
    # List all shapefiles in the workspace
    shapefiles = arcpy.ListFeatureClasses("*.shp")
    # Loop through each shapefile
    for shapefile in shapefiles:
        # Check if the field already exists
        if field_name not in [field.name for field in arcpy.ListFields(shapefile)]:
            arcpy.AddField_management(shapefile, field_name, "DOUBLE")
        # Get the base name of the input shapefile without extension
        base_name = os.path.splitext(os.path.basename(shapefile))[0]    
            
        # Create a new field called "FirstDigit" to store the first digit of "gridcode"
        arcpy.AddField_management(shapefile, "FirstDigit", "TEXT")
        # Calculate the first digit of "gridcode" into the "FirstDigit" field
        with arcpy.da.UpdateCursor(shapefile, ["gridcode", "FirstDigit"]) as cursor:
            for row in cursor:
                if row[0] is not None:
                    row[1] = str(row[0])[0]  # Get the first digit as a string
                cursor.updateRow(row)
        # Dissolve the shapefile based on the "FirstDigit" field
        dissolved_shapefile = os.path.join(category_folder, f"{base_name}_category.shp")
        arcpy.management.Dissolve(shapefile, dissolved_shapefile, "FirstDigit")
        # Add a "Category" field and calculate it based on the "FirstDigit" field
        arcpy.AddField_management(dissolved_shapefile, "Category", "TEXT")
        with arcpy.da.UpdateCursor(dissolved_shapefile, ["FirstDigit", "Category"]) as cursor:
            for row in cursor:
                first_digit = row[0]
                if first_digit == "1":
                    row[1] = "Water"
                elif first_digit == "2":
                    row[1] = "Developed"
                elif first_digit == "3":
                    row[1] = "Barren"
                elif first_digit == "4":
                    row[1] = "Forest"
                elif first_digit == "5":
                    row[1] = "Shrubland"
                elif first_digit == "7":
                    row[1] = "Herbaceous"
                elif first_digit == "8":
                    row[1] = "Planted_Cultivated"
                elif first_digit == "9":
                    row[1] = "Wetlands"
                cursor.updateRow(row)
        
        # Calculate the geometry of the dissolved shapefile
        arcpy.CalculateGeometryAttributes_management(dissolved_shapefile, [["Area", "AREA"]], "", "ACRES")       
        # Calculate the total area of the dissolved shapefile
        total_area = sum([row[0] for row in arcpy.da.SearchCursor(dissolved_shapefile, "AREA")])
        # Add another field "Percentage" and calculate percentage for each record
        arcpy.AddField_management(dissolved_shapefile, "Percentage", "DOUBLE")
        with arcpy.da.UpdateCursor(dissolved_shapefile, ["AREA", "Percentage"]) as cursor:
            for row in cursor:
                row[1] = (row[0] / total_area) * 100
                cursor.updateRow(row)
    # Inform the user that the process is complete
    arcpy.AddMessage("Area calculation completed successfully.") 
    
    return
    
def updateNLCDTable(category_folder, gdb_folder, gdb_name):
    arcpy.env.workspace = category_folder
    shapefiles = arcpy.ListFeatureClasses("*.shp")
    
    nlcd_gdb = os.path.join(gdb_folder, f"{gdb_name}.gdb")
    nlcd_table = os.path.join(nlcd_gdb, f"{gdb_name}")
    
    # Get the list of fields in the NLCD table
    fields_to_add = [field.name for field in arcpy.ListFields(nlcd_table) if field.name != "GID"]
    with arcpy.da.InsertCursor(nlcd_table, ["GID"] + fields_to_add) as cursor:
        for shapefile in shapefiles:
            # Extract the first 8 digits of the shapefile name
            gid = os.path.splitext(os.path.basename(shapefile))[0][:8]
            # Create a dictionary to store the Percentage values for each category
            percentages = {}
            # Use a cursor to read Percentage values and populate the dictionary
            with arcpy.da.SearchCursor(shapefile, ["Category", "Percentage"]) as s_cursor:
                for row in s_cursor:
                    category, percentage = row
                    percentages[category] = percentage
            # Create a list of values to insert into the NLCD table
            values = [gid] + [percentages.get(category, 0.0) for category in fields_to_add]
            # Insert the values as a new record in the NLCD table
            cursor.insertRow(values)
            
if __name__ == "__main__":
    input_raster = arcpy.GetParameterAsText(0)
    input_polygon = arcpy.GetParameterAsText(1)
    output_folder = arcpy.GetParameterAsText(2)
    #gdb_name = arcpy.GetParameterAsText(3)
    gdb_name = "NLCD"
    
    batch_clip_raster(input_raster,input_polygon, output_folder, gdb_name)
    # Create a directory with the same name as gdb_name under output_folder
    
    print("Batch clipping raster done at:")
    current_time = time.strftime("%m-%d %X",time.localtime())
    print(current_time)
    
    gdb_folder = os.path.join(output_folder, gdb_name)
    
    # Check if the folder exists; if not, create it
    if not os.path.exists(gdb_folder):
        os.makedirs(gdb_folder)
    
    tif_folder = os.path.join(gdb_folder, f"{gdb_name}_tif")
    # Check if the folder exists; if not, break the tool with a warning message
    if os.path.exists(tif_folder):
        # Create a directory with the same name as gdb_name under output_folder
        shp_folder = os.path.join(gdb_folder, f"{gdb_name}_shp")
        # Check if the folder exists; if not, create it
        if not os.path.exists(shp_folder):
            os.makedirs(shp_folder)
        
        convertTifToShp(tif_folder, shp_folder, output_folder, gdb_name)
        print("Tif to shapefile conversion done at:")
        current_time = time.strftime("%m-%d %X",time.localtime())
        print(current_time)
    else:
        arcpy.AddWarning("Cannot find extracted basin rasters. Please extract the basins first.")
        
    
    # Create a directory with the same name as gdb_name under output_folder
    shp_folder = os.path.join(gdb_folder, f"{gdb_name}_shp")
    
    adding_field = 'Area_Acre' # input the text of the adding field
    
    # Create a new folder for the dissolved shapefiles
    category_folder = os.path.join(shp_folder, f"{shp_folder}_category")
    
    if not os.path.exists(category_folder):
        os.makedirs(category_folder)
    if os.path.exists(shp_folder):
        # Create a directory with the same name as gdb_name under output_folder       
        addCatField(shp_folder, adding_field)
    else:
        arcpy.AddWarning("Cannot find extracted basin rasters. Please extract the basins first.")       
    
    # Check if the category_folder exists
    if os.path.exists(category_folder):
        # Call the function to update the NLCD table
        updateNLCDTable(category_folder, gdb_folder, gdb_name)
        print("NLCD summary table created at:")
        current_time = time.strftime("%m-%d %X",time.localtime())
        print(current_time)
    else:
        arcpy.AddWarning("Category folder not found.")
   
print('Main function done')

print("Tool done at:")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)