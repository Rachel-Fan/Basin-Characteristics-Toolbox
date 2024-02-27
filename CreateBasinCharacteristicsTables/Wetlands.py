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


def batch_clip(input_wetland, input_clip_polygon, output_directory):
    """
    Clips an input ecoregion shapefile using each polygon in an input clip polygon shapefile.
    Creates a clipped shapefile for each polygon based on its GID.
    """
    # Set the workspace to the directory of the input ecoregion shapefile
    arcpy.env.workspace = os.path.dirname(basin_shapefile)
    
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
            
            output_shapefile = os.path.join(clip_subfolder, f"{gage_id}_Wetland.shp")
            arcpy.analysis.Clip(input_wetland, clip_polygon_layer, output_shapefile)
            print(f"Clipped and saved: {output_shapefile}")
    
    arcpy.SelectLayerByAttribute_management(clip_polygon_layer, "CLEAR_SELECTION")
    print("Batch clipping completed.")
    
def batch_dissolve(input_folder, output_folder):
    """
    Dissolves the 'TYPE' field of shapefiles in the input folder and saves the results in the output folder.
    """
    try:
                
        # Get list of shapefiles in input folder
        shapefiles = [f for f in os.listdir(input_folder) if f.endswith(".shp")]
        
        # Iterate over each shapefile in the input folder
        for shapefile in shapefiles:
            # Construct input and output paths
            input_shapefile = os.path.join(input_folder, shapefile)
            output_shapefile = os.path.join(output_folder, f"{os.path.splitext(shapefile)[0]}_dissolved.shp")
            
            # Perform dissolve
            arcpy.management.Dissolve(input_shapefile, output_shapefile, "TYPE")
            print(f"Dissolved and saved: {output_shapefile}")
    
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(str(e))

def add_area_field(input_folder):
    # List all shapefiles in the input folder
    shapefiles = [f for f in os.listdir(input_folder) if f.endswith('.shp')]

    # Loop through each shapefile
    for shapefile in shapefiles:
        # Create a full path to the shapefile
        shapefile_path = os.path.join(input_folder, shapefile)

        # Add 'Area_SqMi' field
        arcpy.AddField_management(shapefile_path, 'Area_SqMi', 'DOUBLE')

        # Calculate area in square miles
        arcpy.CalculateGeometryAttributes_management(shapefile_path, [['Area_SqMi', 'AREA']], area_unit='SQUARE_MILES_INT', coordinate_system='26852')
        print(f"Area calculated for {shapefile}")

    print("Process completed successfully.")
    
def create_national_wetland_table(basin_shapefile, output_gdb, dissolve_folder):
    
    # Create NationalWetland table
    national_wetland_table = os.path.join(output_gdb, "NationalWetland")
    if not arcpy.Exists(national_wetland_table):
        arcpy.CreateTable_management(output_gdb, "NationalWetland")
        arcpy.AddField_management(national_wetland_table, "GID", "TEXT")
        arcpy.AddField_management(national_wetland_table, "Wetland_Pctg", "DOUBLE")
        arcpy.AddField_management(national_wetland_table, "LakePond_Pctg", "DOUBLE")

    # Get a list of shapefiles in the dissolve folder
    dissolve_shapefiles = [f for f in os.listdir(dissolve_folder) if f.endswith(".shp")]

    # Initialize dictionary to store area totals for each GID
    gid_totals = {}

    # Loop through each shapefile
    for dissolve_shapefile in dissolve_shapefiles:
        # Extract GID from the shapefile name
        gid = dissolve_shapefile.split('_')[0]

        # Initialize variables to store area totals for each type
        wetland_area_total = 0
        lakepond_area_total = 0

        # Use SearchCursor to calculate total area for each type
        with arcpy.da.SearchCursor(os.path.join(dissolve_folder, dissolve_shapefile), ["TYPE", "Area_SqMi"]) as cursor:
            for row in cursor:
                if row[0] == "Wetland":
                    wetland_area_total += row[1]
                elif row[0] == "LakePond":
                    lakepond_area_total += row[1]

        # Update dictionary with totals for this GID
        gid_totals[gid] = {
            "wetland": wetland_area_total,
            "lakepond": lakepond_area_total
        }

    # Calculate total area from basin_shapefile
    total_area = 0
    with arcpy.da.SearchCursor(basin_shapefile, ["TDA_SqMi"]) as cursor:
        for row in cursor:
            total_area += row[0]

    # Insert data into NationalWetland table
    with arcpy.da.InsertCursor(national_wetland_table, ["GID", "Wetland_Pctg", "LakePond_Pctg"]) as cursor:
        for gid, areas in gid_totals.items():
            print('area of ', {gid}, 'is', areas["wetland"] )
            print('total area is ', total_area)
            wetland_percentage = (areas["wetland"] / total_area) * 100
            lakepond_percentage = (areas["lakepond"] / total_area) * 100
            cursor.insertRow((gid, wetland_percentage, lakepond_percentage))

    print("Process completed successfully.")

basin_shapefile = r"C:\Users\rfan\Documents\ArcGIS\Projects\NeDNR_Regression\Input_Basins\1012\basins_final_merge.shp"
wetland_shapefile = r"C:\Users\rfan\Documents\ArcGIS\Projects\NeDNR_Regression\Wetland_Local\Processed\reproject\1012_merged.shp"
output_folder = r"C:\Users\rfan\Documents\ArcGIS\Projects\NeDNR_Regression\Wetland_Tool\1012"

print("Input read. Start processing.") 

# Get the base filename
base_filename = os.path.basename(wetland_shapefile)

# Split the filename by underscore
prefix = base_filename.split('_')[0]
print('prefix is ', prefix)


   
# Create output subfolder if it doesn't exist
wetland_subfolder = os.path.join(output_folder, f"Wetland_{prefix}")
if not os.path.exists(wetland_subfolder):
    os.makedirs(wetland_subfolder)

# Create output subfolder if it doesn't exist
clip_subfolder = os.path.join(wetland_subfolder, f"clip_{prefix}")
if not os.path.exists(clip_subfolder):
    os.makedirs(clip_subfolder)
batch_clip(wetland_shapefile, basin_shapefile, clip_subfolder)
print("batch_clip Done at")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)

# Create output subfolder if it doesn't exist
dissolve_subfolder = os.path.join(wetland_subfolder, f"dissolve_{prefix}")
if not os.path.exists(dissolve_subfolder):
    os.makedirs(dissolve_subfolder)
batch_dissolve(clip_subfolder,dissolve_subfolder)
print("batch_dissolve Done at")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)

add_area_field(dissolve_subfolder)

# Create the file geodatabase
gdb_path = os.path.join(wetland_subfolder, f"NationalWetland_{prefix}.gdb")
if not arcpy.Exists(gdb_path):
    arcpy.CreateFileGDB_management(wetland_subfolder, f"NationalWetland_{prefix}.gdb")
create_national_wetland_table(basin_shapefile, gdb_path,dissolve_subfolder)
print("create_national_wetland_table Done at")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)

print("Tool Done at")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)
