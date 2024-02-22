import arcpy
import os
import time
from collections import defaultdict

# Enable overwriting of output
arcpy.env.overwriteOutput = True

# Inputs
soil_map_units_shp = arcpy.GetParameterAsText(0)  # 'SoilMapUnits.shp'
basins_list_shp = arcpy.GetParameterAsText(1)    # 'basins_list.shp'
output_folder = arcpy.GetParameterAsText(2)      # Output folder for gdb and temp files

print("Start:", time.ctime())  # Track progress

# Create output geodatabase and temp folder
gdb_name = "OutputGDB.gdb"
gdb_path = os.path.join(output_folder, gdb_name)
temp_folder = os.path.join(output_folder, "soil_temp")

if not arcpy.Exists(gdb_path):
    arcpy.CreateFileGDB_management(output_folder, gdb_name)
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

print("GDB and temp folder created:", time.ctime())  # Track progress

# Prepare the output table
table_name = "SoilMapUnits"
table_path = os.path.join(gdb_path, table_name)
if arcpy.Exists(table_path):
    arcpy.Delete_management(table_path)
arcpy.CreateTable_management(gdb_path, table_name)
arcpy.AddField_management(table_path, "GID", "TEXT")

print("Output table prepared:", time.ctime())  # Track progress

# Intersect soil map units with basins
intersect_output = os.path.join(temp_folder, "intersected.shp")
arcpy.Intersect_analysis([soil_map_units_shp, basins_list_shp], intersect_output, "ALL", "", "INPUT")

print("Intersection completed:", time.ctime())  # Track progress

# Calculate area of each intersected feature
arcpy.AddField_management(intersect_output, "Area", "DOUBLE")
arcpy.CalculateField_management(intersect_output, "Area", "!shape.area@squaremeters!", "PYTHON3")

print("Area calculated:", time.ctime())  # Track progress

# Gather data for calculations
data = defaultdict(lambda: defaultdict(list))
with arcpy.da.SearchCursor(intersect_output, ["GID", "hydgrpdcd", "ksat", "Area"]) as cursor:
    for row in cursor:
        gid, hydgrpdcd, ksat, area = row
        if hydgrpdcd is None:
            hydgrpdcd = 'OtherSoilType'
        data[gid]['ksat'].append(ksat * area)
        data[gid][hydgrpdcd].append(area)

print("Data gathered for calculations:", time.ctime())  # Track progress

# Calculate statistics
results = {}
for gid, values in data.items():
    total_area = sum([sum(values[hydgrpdcd]) for hydgrpdcd in values if hydgrpdcd != 'ksat'])
    hydgrpdcd_percentages = {hydgrpdcd: (sum(values[hydgrpdcd]) / total_area * 100) for hydgrpdcd in values if hydgrpdcd != 'ksat'}
    ksat_weighted_sum = sum(values['ksat']) / total_area
    results[gid] = {'hydgrpdcd_percentages': hydgrpdcd_percentages, 'ksat_weighted_sum': ksat_weighted_sum}

print("Statistics calculated:", time.ctime())  # Track progress

# Add necessary fields to the table for each hydgrpdcd found in the dataset
unique_hydgrpdcds = set(hydgrpdcd for gid in results for hydgrpdcd in results[gid]['hydgrpdcd_percentages'])
for hydgrpdcd in unique_hydgrpdcds:
    if hydgrpdcd == 'OtherSoilType':
        arcpy.AddField_management(table_path, hydgrpdcd, "DOUBLE")
    else:
        arcpy.AddField_management(table_path, f"{hydgrpdcd}_perc", "DOUBLE")
arcpy.AddField_management(table_path, "ksat_weighted", "DOUBLE")

print("Fields added to table:", time.ctime())  # Track progress

# Populate the table
with arcpy.da.InsertCursor(table_path, ["GID"] + [f"{hydgrpdcd}_perc" if hydgrpdcd != 'OtherSoilType' else hydgrpdcd for hydgrpdcd in unique_hydgrpdcds] + ["ksat_weighted"]) as cursor:
    for gid, stats in results.items():
        row = [gid] + [stats['hydgrpdcd_percentages'].get(hydgrpdcd, 0) for hydgrpdcd in unique_hydgrpdcds] + [stats['ksat_weighted_sum']]
        cursor.insertRow(row)

print("Table populated with data:", time.ctime())  # Track progress

arcpy.AddMessage("Processing completed successfully.")
