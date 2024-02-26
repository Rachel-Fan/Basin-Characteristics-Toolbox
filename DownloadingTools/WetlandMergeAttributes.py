import arcpy
import os

def batch_clip(basin_shapefile, wetland_shapefile, output_folder):
    # Create temp folder
    temp_folder = os.path.join(output_folder, "WetlandByBasin")
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    
    # Clip wetland_shapefile by each record in basin_shapefile
    with arcpy.da.SearchCursor(basin_shapefile, ["GID"]) as cursor:
        for row in cursor:
            gid = row[0]
            output_shapefile = os.path.join(temp_folder, f"{gid}_wetland.shp")
            arcpy.Clip_analysis(wetland_shapefile, basin_shapefile, output_shapefile)
            print(f"Clipped wetland for GID {gid}")

    # Run Select By Attribute and dissolve based on conditions
    wetlands_output = os.path.join(temp_folder, "Wetland", "wetlands_dissolved.shp")
    lakes_ponds_output = os.path.join(temp_folder, "Wetland", "lakes_ponds_dissolved.shp")

    # Select and dissolve wetlands
    arcpy.Select_analysis(wetland_shapefile, wetlands_output, "WETLAND_TY LIKE '%Wetland%'")
    arcpy.Dissolve_management(wetlands_output, wetlands_output)

    # Select and dissolve lakes/ponds
    arcpy.Select_analysis(wetland_shapefile, lakes_ponds_output, "WETLAND_TY LIKE '%Lake%' OR WETLAND_TY LIKE '%Pond%'")
    arcpy.Dissolve_management(lakes_ponds_output, lakes_ponds_output)

    print("Process completed successfully.")

# Usage
batch_clip(basin_shapefile, wetland_shapefile, output_folder)
