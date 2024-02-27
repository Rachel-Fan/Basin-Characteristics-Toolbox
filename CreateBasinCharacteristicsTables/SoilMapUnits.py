import arcpy
import os
import time
from collections import defaultdict

# Enable overwriting of output
arcpy.env.overwriteOutput = True

def SoilTypeKsat(soil_map_units_shp,basins_list_shp, output_folder):

    # Create output geodatabase and temp folder
    gdb_name = "Soil.gdb"
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
    with arcpy.da.SearchCursor(intersect_output, ["GID", "SoilType", "ksat", "Area"]) as cursor:
        for row in cursor:
            gid, soil_type, ksat, area = row

            data[gid]['ksat'].append(ksat * area)
            data[gid][soil_type].append(area)

    print("Data gathered for calculations:", time.ctime())  # Track progress

    # Calculate statistics
    results = {}
    for gid, values in data.items():
        total_area = sum([sum(values[soil_type]) for soil_type in values if soil_type != 'ksat'])
        soil_type_percentages = {soil_type: (sum(values[soil_type]) / total_area * 100) for soil_type in values if soil_type != 'ksat'}
        ksat_weighted_sum = sum(values['ksat']) / total_area
        results[gid] = {'soil_type_percentages': soil_type_percentages, 'ksat_weighted_sum': ksat_weighted_sum}

    print("Statistics calculated:", time.ctime())  # Track progress
    print("Results are", results)

    # Before adding fields, create a list of field names to be added to the table
    unique_soil_types = set(soil_type for gid in results for soil_type in results[gid]['soil_type_percentages'])

    # Update field names list to include the desired field names
    field_names = ["GID"]  # Start with GID and OtherSoilType
    print("unique_soil_types are", unique_soil_types)
    '''
    for soil_type in unique_soil_types:
        if soil_type != ' ':
            field_name = f"{soil_type}"
            field_names.append(field_name)  # Remove SoilType_ prefix for other types
    field_names.append("ksat_weighted")  # Add ksat_weighted field
    '''
    
    # Adding soil types fields
    Soil_Type_fields = ['SoilType_A', 'SoilType_B', 'SoilType_C', 'SoilType_D', 'SoilType_A_D', 'SoilType_B_D', 'SoilType_C_D', 'OtherSoilTypes']

    for field_name in Soil_Type_fields:  # Skip 'GID' as it's already added
        arcpy.AddField_management(table_path, field_name, "DOUBLE")

    # Add ksat_weighted field
    arcpy.AddField_management(table_path, "ksat_weighted", "DOUBLE")
    
    print("Fields added to table:", time.ctime())  # Track progress

    # Populate the table
    with arcpy.da.InsertCursor(table_path, field_names) as cursor:
        for gid, stats in results.items():
            row = [gid]
            for soil_type in unique_soil_types:
                row.append(stats['soil_type_percentages'].get(soil_type, 0))
            row.append(stats['ksat_weighted_sum'])  # Add ksat_weighted sum for each GID
            cursor.insertRow(row)

    print("Table populated with data:", time.ctime())  # Track progress
    
    # Update rows where soil type fields are not in the unique soil types
    with arcpy.da.UpdateCursor(table_path, Soil_Type_fields) as cursor:
        for row in cursor:
            for i in range(len(row)):
                if Soil_Type_fields[i] not in unique_soil_types:
                    row[i] = 0  # Fill with 0 if soil type field not in unique soil types
            cursor.updateRow(row)

    print("Filled missing soil type fields with 0:", time.ctime())  # Track progress


# Inputs

soil_map_units_shp = arcpy.GetParameterAsText(0)  # 'SoilMapUnits.shp'
basins_list_shp = arcpy.GetParameterAsText(1)    # 'basins_list.shp'
output_folder = arcpy.GetParameterAsText(2)      # Output folder for gdb and temp files

'''
soil_map_units_shp = r'U:\1937\193709666\03_data\gis_cad\gis\Basin_Characteristics\SourceData\SoilsMapUnits\Soils_1025.shp'  # 'SoilMapUnits.shp'
basins_list_shp = r'U:\1937\193709666\03_data\gis_cad\gis\Basin_Characteristics_Testing\Testing_Dataset\PreProcessing_1025\basins_final_merge.shp'    # 'basins_list.shp'
output_folder = r'U:\1937\193709666\03_data\gis_cad\gis\Basin_Characteristics_Testing\Testing_Dataset\Soil'
'''

print("Start:", time.ctime())  # Track progress

# Create soil folder

soil_folder = os.path.join(output_folder, "Soil")

if not os.path.exists(soil_folder):
    os.makedirs(soil_folder)
        
SoilTypeKsat(soil_map_units_shp,basins_list_shp, soil_folder)
arcpy.AddMessage("Processing completed successfully.")