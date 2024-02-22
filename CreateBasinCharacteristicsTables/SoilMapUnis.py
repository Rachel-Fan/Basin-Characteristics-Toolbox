import arcpy
import os
from collections import defaultdict

# Inputs
soil_map_units_shp = arcpy.GetParameterAsText(0)  # 'SoilMapUnits.shp'
basins_list_shp = arcpy.GetParameterAsText(1)    # 'basins_list.shp'
output_folder = arcpy.GetParameterAsText(2)      # Output folder for gdb and temp files

# Setup
gdb_name = "OutputGDB.gdb"
gdb_path = os.path.join(output_folder, gdb_name)
temp_folder = os.path.join(output_folder, "soil_temp")

# Create output GDB and temp folder
if not arcpy.Exists(gdb_path):
    arcpy.CreateFileGDB_management(output_folder, gdb_name)
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

# Create output table
table_name = "SoilMapUnits"
table_path = os.path.join(gdb_path, table_name)
if not arcpy.Exists(table_path):
    arcpy.CreateTable_management(gdb_path, table_name)
    arcpy.AddField_management(table_path, "GID", "TEXT")
    # Dynamic addition of fields for hydrogrp percentages based on unique hydrogrp values
    hydrogrp_values = [row[0] for row in arcpy.da.SearchCursor(soil_map_units_shp, "hydrogrp")]
    unique_hydrogrp = set(hydrogrp_values)
    for hydrogrp in unique_hydrogrp:
        arcpy.AddField_management(table_path, f"perc_{hydrogrp}", "DOUBLE")
    arcpy.AddField_management(table_path, "ksat_weighted_sum", "DOUBLE")

# Intersect soil map units with basins
intersect_output = os.path.join(temp_folder, "intersected.shp")
arcpy.Intersect_analysis([soil_map_units_shp, basins_list_shp], intersect_output, "ALL", "", "INPUT")

# Initialize data structures for calculations
gid_stats = defaultdict(lambda: defaultdict(float))
gid_area = defaultdict(float)

# Calculate stats for each GID
with arcpy.da.SearchCursor(intersect_output, ["GID", "hydrogrp", "ksat", "SHAPE@AREA"]) as cursor:
    for row in cursor:
        gid, hydrogrp, ksat, area = row
        gid_stats[gid][hydrogrp] += area  # Sum area by hydrogrp
        gid_stats[gid]['ksat_sum'] += ksat * area  # Sum ksat * area for weighted average
        gid_area[gid] += area  # Total area per GID

# Calculate percentages and weighted ksat
for gid in gid_stats:
    for hydrogrp in unique_hydrogrp:
        if gid_stats[gid][hydrogrp] > 0:  # Check if hydrogrp exists in this GID
            gid_stats[gid][f"perc_{hydrogrp}"] = (gid_stats[gid][hydrogrp] / gid_area[gid]) * 100
    gid_stats[gid]['ksat_weighted_avg'] = gid_stats[gid]['ksat_sum'] / gid_area[gid]

# Insert calculated stats into the SoilMapUnits table
with arcpy.da.InsertCursor(table_path, ["GID"] + [f"perc_{hydrogrp}" for hydrogrp in unique_hydrogrp] + ["ksat_weighted_sum"]) as insert_cursor:
    for gid, stats in gid_stats.items():
        row = [gid] + [stats.get(f"perc_{hydrogrp}", 0) for hydrogrp in unique_hydrogrp] + [stats.get('ksat_weighted_avg', 0)]
        insert_cursor.insertRow(row)

arcpy.AddMessage("Processing completed successfully.")
