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

def batch_clip(basin_shapefile, wetland_shapefile, output_folder):
    # Create temp folder
    temp_folder = os.path.join(output_folder, "WetlandByBasin")
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
        print('WetlandByBasin create at', temp_folder)
    
    # Clip wetland_shapefile by each record in basin_shapefile
    with arcpy.da.SearchCursor(basin_shapefile, ["GID"]) as cursor:
        for row in cursor:
            
            gid = row[0]
            print(f"Start clipping wetland for GID {gid}")
            output_shapefile = os.path.join(temp_folder, f"{gid}_wetland.shp")
            arcpy.Clip_analysis(wetland_shapefile, basin_shapefile, output_shapefile)
            print(f"Clipped wetland for GID {gid}")

            # Run Select By Attribute and dissolve based on conditions
            wetlands_output = os.path.join(temp_folder, f"{gid}_wetlands_dissolved.shp")
            arcpy.Select_analysis(output_shapefile, wetlands_output, "WETLAND_TY LIKE '%Wetland%'")
            arcpy.Dissolve_management(output_shapefile, wetlands_output)
            print(f"Wetland dissolved for GID {gid}")
            
            # Run Select By Attribute and dissolve based on conditions
            lakes_ponds_output = os.path.join(temp_folder, f"{gid}_lakes_ponds_dissolved.shp")
            arcpy.Select_analysis(output_shapefile, lakes_ponds_output, "WETLAND_TY LIKE '%Lake%' OR WETLAND_TY LIKE '%Pond%'")
            arcpy.Dissolve_management(output_shapefile, lakes_ponds_output)
            print(f"Lakes and ponds dissolved for GID {gid}")
            
        
    print("Process completed successfully.")


basin_shapefile = r"Z:\NE_Basin\Basin_Characteristics\PreProcessing_1027\basins_final_merge.shp"
wetland_shapefile = r"C:\Users\rfan\Documents\ArcGIS\Projects\NeDNR_Regression\Wetland_Local\Wetland_1027.shp"
output_folder = r"C:\Users\rfan\Documents\ArcGIS\Projects\NeDNR_Regression\Wetland_Tool"

print("Input read. Start processing.")    
    
# Usage
batch_clip(basin_shapefile, wetland_shapefile, output_folder)
