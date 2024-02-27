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


# Set workspace environments
arcpy.env.workspace = r"D:\NE\Wetland\Preprocessing"
arcpy.env.overwriteOutput = True

# Input folders
tiles_folder = r"D:\NE\Wetland\HUC4"
wetlands_folder = r"D:\NE\Wetland\Download_shapefile_wetlands"

# Output folder
output_folder = r"D:\NE\Wetland\Preprocessing"
clipped_folder = os.path.join(output_folder, "clipped")
merged_folder = os.path.join(output_folder, "merged")

# Create output subfolders if they don't exist
if not os.path.exists(clipped_folder):
    os.makedirs(clipped_folder)
if not os.path.exists(merged_folder):
    os.makedirs(merged_folder)

# Loop through each tile shapefile
for tile_file in os.listdir(tiles_folder):
    if tile_file.endswith('.shp'):
        tile_name = os.path.splitext(tile_file)[0]
        tile_path = os.path.join(tiles_folder, tile_file)
        tile_extent = arcpy.Describe(tile_path).extent
        print('tile_name is', tile_name)

        # Loop through each wetland shapefile
        for wetland_file in os.listdir(wetlands_folder):
            if wetland_file.endswith('.shp'):
                wetland_name = os.path.splitext(wetland_file)[0]
                wetland_path = os.path.join(wetlands_folder, wetland_file)

                # Check for intersection
                wetland_extent = arcpy.Describe(wetland_path).extent
                if tile_extent.overlaps(wetland_extent):
                    # Clip wetland by tile
                    clipped_output = os.path.join(clipped_folder, f"{tile_name}_{wetland_name}.shp")
                    arcpy.Clip_analysis(wetland_path, tile_path, clipped_output)
                    print(wetland_name, ' is clipped')

        # Merge clipped features by tile
        clipped_files = [os.path.join(clipped_folder, f) for f in os.listdir(clipped_folder) if f.endswith('.shp') and f.startswith(tile_name)]
        if clipped_files:
            arcpy.Merge_management(clipped_files, os.path.join(merged_folder, f"{tile_name}_merged.shp"))
        print(f"{tile_name}_merged.shp", ' is merged at')
        current_time = time.strftime("%m-%d %X",time.localtime())
        print(current_time)


print("Tool done at:")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)