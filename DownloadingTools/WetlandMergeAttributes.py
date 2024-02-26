import arcpy
import os

# Set input and output paths
basin_shapefile = "path/to/basin_final_merge.shp"
wetland_shapefile = "path/to/WETLAND.shp"
output_folder = "path/to/output_folder"

# Create subfolder 'Wetland' if it doesn't exist
wetland_folder = os.path.join(output_folder, "Wetland")
if not os.path.exists(wetland_folder):
    os.makedirs(wetland_folder)

# Create temp folder and geodatabase
temp_folder = os.path.join(wetland_folder, "temp")
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

gdb_path = os.path.join(temp_folder, "wetland.gdb")
if not arcpy.Exists(gdb_path):
    arcpy.CreateFileGDB_management(temp_folder, "wetland.gdb")

# Create NationalWetlands table
national_wetlands_table = os.path.join(gdb_path, "NationalWetlands")
if not arcpy.Exists(national_wetlands_table):
    arcpy.CreateTable_management(gdb_path, "NationalWetlands")
    arcpy.AddField_management(national_wetlands_table, "GID", "LONG")
    arcpy.AddField_management(national_wetlands_table, "Wetlands_Percentage", "DOUBLE")
    arcpy.AddField_management(national_wetlands_table, "Lakes_and_Ponds_Percentage", "DOUBLE")

# Calculate area of basin_final_merge.shp
basin_area = 0
with arcpy.da.SearchCursor(basin_shapefile, ["SHAPE@AREA"]) as cursor:
    for row in cursor:
        basin_area += row[0]

# Calculate area of Wetlands and Lakes_and_Ponds for each basin
with arcpy.da.UpdateCursor(national_wetlands_table, ["GID", "Wetlands_Percentage", "Lakes_and_Ponds_Percentage"]) as cursor:
    for row in cursor:
        gid = row[0]
        wetlands_area = 0
        lakes_and_ponds_area = 0
        with arcpy.da.SearchCursor(wetland_shapefile, ["WETLAND_TY", "ACRES"], f"GID = {gid}") as wetland_cursor:
            for wetland_row in wetland_cursor:
                if "Wetland" in wetland_row[0]:
                    wetlands_area += wetland_row[1]
                elif "Pond" in wetland_row[0] or "Lake" in wetland_row[0]:
                    lakes_and_ponds_area += wetland_row[1]

        row[1] = (wetlands_area / basin_area) * 100
        row[2] = (lakes_and_ponds_area / basin_area) * 100
        cursor.updateRow(row)

print("Process completed successfully.")
