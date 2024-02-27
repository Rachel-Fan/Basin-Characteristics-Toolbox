import os
import arcpy
import time

print("Tool starts")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)


# Check Spatial Analyst extension
arcpy.CheckOutExtension("Spatial")
# Enable overwriting of output files
arcpy.env.overwriteOutput = True

def batch_clip_raster(input_raster, input_shp, tif_folder):

        # Set environment settings
        arcpy.env.workspace = tif_folder

        # Check out the Spatial Analyst extension
        arcpy.CheckOutExtension("Spatial")

        # Define input NLCD raster and basin shapefile
        nlcd_raster = input_raster
        basin_shapefile = input_shp


        

        # Get list of unique GIDs from the basin shapefile
        gids = set()
        with arcpy.da.SearchCursor(basin_shapefile, "GID") as cursor:
            for row in cursor:
                gids.add(row[0])

        # Iterate over each unique GID and clip NLCD raster
        for gid in gids:
            # Define output raster name
            output_raster = os.path.join(tif_folder, f"NLCD_{gid}.tif")
            
            # Define expression for selection
            expression = f"\"GID\" = '{gid}'"
            
            # Create feature layer for the selected GID
            arcpy.MakeFeatureLayer_management(basin_shapefile, "temp_layer", expression)
            
            # Clip NLCD raster based on GID
            arcpy.sa.ExtractByMask(nlcd_raster, "temp_layer").save(output_raster)
            
            print(f"{gid} NLCD is clipped", time.ctime())  # Track progress
            
            # Clean up temporary feature layer
            arcpy.Delete_management("temp_layer")

def tiff_to_shapefile(input_folder, output_folder):
    # Set workspace
    arcpy.env.workspace = input_folder

    # Get list of TIFF files in input folder
    tiff_files = arcpy.ListRasters("*", "TIF")

    # Create output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate over each TIFF file and convert to shapefile
    for tiff_file in tiff_files:
        # Define output shapefile name
        output_shapefile = os.path.join(output_folder, os.path.splitext(tiff_file)[0] + ".shp")
        

        # Convert TIFF to shapefile
        arcpy.RasterToPolygon_conversion(tiff_file, output_shapefile, "NO_SIMPLIFY", "Value")
        arcpy.AddMessage(f"Converted {tiff_file} to {output_shapefile}")
        print(f"{tiff_file} is converted", time.ctime())  # Track progress


def dissolve_and_categorize_shapefiles(input_folder, output_folder):
    # Set workspace
    arcpy.env.workspace = input_folder
    grid_code_field = 'gridcode'

    # Get list of shapefiles in input folder
    shapefiles = arcpy.ListFeatureClasses("*.shp")
    print('shapefiles to be processed are:', shapefiles)


    # Iterate over each shapefile
    for shapefile in shapefiles:
        # Define output dissolved shapefile name
        dissolved_shapefile = os.path.join(output_folder, os.path.splitext(shapefile)[0] + "_category.shp")

        # Dissolve based on grid code field
        arcpy.Dissolve_management(shapefile, dissolved_shapefile, grid_code_field)

        # Add "NLCD_Type" field
        arcpy.AddField_management(dissolved_shapefile, "NLCD_Type", "TEXT")

        # Update "NLCD_Type" field based on "FirstDigit" field
        with arcpy.da.UpdateCursor(dissolved_shapefile, [grid_code_field, "NLCD_Type"]) as cursor:
            for row in cursor:
                first_letter = str(row[0])  # Convert grid code to string
                first_digit = first_letter[0]  # Extract first digit
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

        # Add "Area_SqMi" field
        arcpy.AddField_management(dissolved_shapefile, "Area_SqMi", "DOUBLE")

        # Calculate area in square miles
        arcpy.CalculateField_management(dissolved_shapefile, "Area_SqMi", "!shape.area@SQUAREMILES!", "PYTHON")


        arcpy.AddMessage(f"Processed {shapefile}")



def create_and_populate_NLCD_table(NLCD_Category_folder, output_folder):
    
    arcpy.env.workspace = NLCD_Category_folder
    
    # Create file geodatabase
    gdb_path = os.path.join(output_folder, "NLCD.gdb")
    arcpy.CreateFileGDB_management(output_folder, "NLCD.gdb")


    # Create table in the geodatabase
    table_path = os.path.join(gdb_path, "NLCD")
    arcpy.CreateTable_management(gdb_path, "NLCD")
    arcpy.AddField_management(table_path, "GID", "TEXT")
    fields_to_add = ["Water", "Developed", "Barren", "Forest", "Shrubland", "Herbaceous", "Planted_Cultivated", "Wetlands"]
    for field in fields_to_add:
            arcpy.AddField_management(table_path, field, "FLOAT")  # Change field type to FLOAT for percentage values
    
    shapefiles = arcpy.ListFeatureClasses("*.shp")
    
    nlcd_table = os.path.join(gdb_path, "NLCD")
    
    with arcpy.da.InsertCursor(nlcd_table, ["GID"] + fields_to_add) as cursor:
        for shapefile in shapefiles:
            # Extract GID from shapefile name
            GID = shapefile.split("_")[1]  # Extract GID from shapefile name

            # Calculate area in square miles for each category
            area_values = {}
            with arcpy.da.SearchCursor(shapefile, ["NLCD_Type", "SHAPE@AREA"]) as s_cursor:
                for row in s_cursor:
                    nlcd_type, shape_area = row
                    if nlcd_type not in area_values:
                        area_values[nlcd_type] = 0.0
                    area_values[nlcd_type] += shape_area

            # Calculate total area
            total_area = sum(area_values.values())

            # Calculate percentage for each category and insert into the NLCD table
            percentages = {category: (area / total_area * 100) if total_area != 0 else 0.0 for category, area in
                            area_values.items()}
            values = [GID] + [percentages.get(category, 0.0) for category in fields_to_add]
            cursor.insertRow(values)



input_raster = r"C:\Users\Rachel\Documents\ArcGIS Pro 3.2\Projects\NE_Basin\Basin_Characteristics\SourceData\NLCD_DEM_Extent.tif"
input_shp = r"C:\Users\Rachel\Documents\ArcGIS Pro 3.2\Projects\NE_Basin\Basin_Characteristics\1012\basins_final_merge.shp"
output_folder = r"C:\Users\Rachel\Documents\ArcGIS Pro 3.2\Projects\NE_Basin\Basin_Characteristics\NLCD_V2"

# Create tif output folder if it does not exist
tif_folder = os.path.join(output_folder, "NLCD_TIF")
if not os.path.exists(tif_folder):
    os.makedirs(tif_folder)
batch_clip_raster(input_raster, input_shp, tif_folder)
print("Batch Clip raster Done at", time.ctime())  # Track progress
print('****************************************')

# Create shp output folder if it does not exist
shp_folder = os.path.join(output_folder, "NLCD_shp")
if not os.path.exists(shp_folder):
    os.makedirs(shp_folder)
tiff_to_shapefile(tif_folder, shp_folder)
print("Batch Clip raster Done at", time.ctime())  # Track progress
print('****************************************')

# Create shp output folder if it does not exist
shp_folder = os.path.join(output_folder, "NLCD_shp")
if not os.path.exists(shp_folder):
    os.makedirs(shp_folder)
tiff_to_shapefile(tif_folder, shp_folder)
print("Tiff to shapefiles Done at", time.ctime())  # Track progress
print('****************************************')

# Create category output folder if it does not exist
cat_folder = os.path.join(output_folder, "NLCD_category")
if not os.path.exists(cat_folder):
    os.makedirs(cat_folder)
dissolve_and_categorize_shapefiles(shp_folder, cat_folder, )
print("add category field and merged shapefiles Done at", time.ctime())  # Track progress
print('****************************************')


# Create output NLCD table with categories

create_and_populate_NLCD_table(cat_folder, output_folder)
print("NLCD table populated at", time.ctime())  # Track progress
print('****************************************')

print("All Done", time.ctime())  # Track progress
