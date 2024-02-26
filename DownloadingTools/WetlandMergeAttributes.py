import arcpy
import os

# Set input and output paths
basin_shapefile = r"Z:\NE_Basin\Basin_Characteristics\PreProcessing_1027\basins_final_merge.shp"
wetland_shapefile = r"C:\Users\rfan\Documents\ArcGIS\Projects\NeDNR_Regression\Wetland_Local\Wetland_1027.shp"
output_folder = r"C:\Users\rfan\Documents\ArcGIS\Projects\NeDNR_Regression\Wetland_Tool"

# Create subfolder 'Wetland' if it doesn't exist
wetland_folder = os.path.join(output_folder, "Wetland")
if not os.path.exists(wetland_folder):
    os.makedirs(wetland_folder)

# Create temp folder and geodatabase
temp_folder = os.path.join(wetland_folder, "temp")
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

gdb_path = os.path.join(wetland_folder, "wetland.gdb")
if not arcpy.Exists(gdb_path):
    arcpy.CreateFileGDB_management(wetland_folder, "wetland.gdb")

# Create NationalWetlands table
national_wetlands_table = os.path.join(gdb_path, "NationalWetlands")
if not arcpy.Exists(national_wetlands_table):
    arcpy.CreateTable_management(gdb_path, "NationalWetlands")
    arcpy.AddField_management(national_wetlands_table, "GID", "LONG")
    arcpy.AddField_management(national_wetlands_table, "Wetlands_Percentage", "DOUBLE")
    arcpy.AddField_management(national_wetlands_table, "Lakes_and_Ponds_Percentage", "DOUBLE")

# Create a dictionary to store the total area of each basin
basin_area_dict = {}

# Read the "TDA_SqMi" field from basin_final_merge.shp to calculate total area for each basin
with arcpy.da.SearchCursor(basin_shapefile, ["GID", "TDA_SqMi"]) as cursor:
    for row in cursor:
        gid, area = row
        basin_area_dict[gid] = area

# Create insert cursor for NationalWetlands table
insert_fields = ["GID", "Wetlands_Percentage", "Lakes_and_Ponds_Percentage"]
insert_cursor = arcpy.da.InsertCursor(national_wetlands_table, insert_fields)

# Iterate over each basin
for gid, basin_area in basin_area_dict.items():
    wetlands_area = 0
    lakes_and_ponds_area = 0
    
    # Calculate total wetlands and lakes/ponds area for the current basin
    with arcpy.da.SearchCursor(wetland_shapefile, ["GID", "WETLAND_TY", "Area_SqMi"], f"GID = {gid}") as wetland_cursor:
        for wetland_row in wetland_cursor:
            if "Wetland" in wetland_row[1]:
                wetlands_area += wetland_row[2]
            elif "Pond" in wetland_row[1] or "Lake" in wetland_row[1]:
                lakes_and_ponds_area += wetland_row[2]

    # Calculate percentages
    wetlands_percentage = (wetlands_area / basin_area) * 100
    lakes_and_ponds_percentage = (lakes_and_ponds_area / basin_area) * 100
    
    # Insert values into NationalWetlands table
    insert_cursor.insertRow((gid, wetlands_percentage, lakes_and_ponds_percentage))

del insert_cursor

print("Process completed successfully.")
