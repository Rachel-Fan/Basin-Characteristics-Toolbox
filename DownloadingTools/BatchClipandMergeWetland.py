import arcpy
import os

# Set workspace environments
arcpy.env.workspace = "path/to/workspace"
arcpy.env.overwriteOutput = True

# Input folders
tiles_folder = "path/to/tiles_folder"
wetlands_folder = "path/to/wetlands_folder"

# Output folder
output_folder = "path/to/output_folder"
clipped_folder = os.path.join(output_folder, "clipped")
merged_folder = os.path.join(output_folder, "merged")

# Create output subfolders if they don't exist
if not os.path.exists(clipped_folder):
    os.makedirs(clipped_folder)
if not os.path.exists(merged_folder):
    os.makedirs(merged_folder)

# Loop through each tile shapefile
for tile_file in arcpy.ListFiles(tiles_folder):
    if tile_file.endswith('.shp'):
        tile_name = os.path.splitext(tile_file)[0]
        tile_path = os.path.join(tiles_folder, tile_file)

        # Loop through each wetland shapefile
        for wetland_file in arcpy.ListFiles(wetlands_folder):
            if wetland_file.endswith('.shp'):
                wetland_name = os.path.splitext(wetland_file)[0]
                wetland_path = os.path.join(wetlands_folder, wetland_file)

                # Clip wetland by tile
                clipped_output = os.path.join(clipped_folder, f"{tile_name}_{wetland_name}.shp")
                arcpy.Clip_analysis(wetland_path, tile_path, clipped_output)

        # Merge clipped features by tile
        clipped_files = [os.path.join(clipped_folder, f) for f in os.listdir(clipped_folder) if f.startswith(tile_name)]
        arcpy.Merge_management(clipped_files, os.path.join(merged_folder, f"{tile_name}_merged.shp"))
