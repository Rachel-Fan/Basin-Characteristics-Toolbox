import arcpy
import os

# Set workspace environment
arcpy.env.workspace = r"path\to\your\workspace"
arcpy.env.overwriteOutput = True

# Define input and output folders
input_folder = r"path\to\your\Wetland\folder"
output_folder = r"path\to\your\output\folder"

# Create output folder if it does not exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Iterate through each shapefile in the input folder
for shpfile in arcpy.ListFiles("*.shp"):
    # Create full path to input shapefile
    input_shapefile = os.path.join(input_folder, shpfile)
    
    # Read field "WETLAND_TY" and perform operations based on its values
    with arcpy.da.UpdateCursor(input_shapefile, ["WETLAND_TY"]) as cursor:
        for row in cursor:
            if "Wetland" in row[0]:
                row[0] = "Wetland"
            elif "Lake" in row[0] or "Pond" in row[0]:
                row[0] = "Lake_and_Pond"
            else:
                cursor.deleteRow()
            cursor.updateRow(row)

    # Merge features
    merged_output = os.path.join(output_folder, os.path.splitext(shpfile)[0] + "_merged.shp")
    arcpy.Merge_management(input_shapefile, merged_output)

    # Add field "WetlandType" and populate values
    arcpy.AddField_management(merged_output, "WetlandType", "TEXT")
    with arcpy.da.UpdateCursor(merged_output, ["WETLAND_TY", "WetlandType"]) as cursor:
        for row in cursor:
            if "Wetland" in row[0]:
                row[1] = "Wetland"
            elif "Lake" in row[0] or "Pond" in row[0]:
                row[1] = "Lake_and_Pond"
            cursor.updateRow(row)
