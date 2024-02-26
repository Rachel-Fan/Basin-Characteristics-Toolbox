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


def batch_clip(basin_shapefile, input_clip_polygon, output_directory):
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
            arcpy.analysis.Clip(basin_shapefile, clip_polygon_layer, output_shapefile)
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



basin_shapefile = r"Z:\NE_Basin\Basin_Characteristics\PreProcessing_1027\basins_final_merge.shp"
wetland_shapefile = r"C:\Users\rfan\Documents\ArcGIS\Projects\NeDNR_Regression\Wetland_Local\Wetland_1027.shp"
output_folder = r"C:\Users\rfan\Documents\ArcGIS\Projects\NeDNR_Regression\Wetland_Tool"

print("Input read. Start processing.")    
    
# Create output subfolder if it doesn't exist
clip_subfolder = os.path.join(output_folder, "dissolve")
if not os.path.exists(clip_subfolder):
    os.makedirs(clip_subfolder)
batch_clip(basin_shapefile, wetland_shapefile, clip_subfolder)

# Create output subfolder if it doesn't exist
dissolve_subfolder = os.path.join(output_folder, "dissolve")
if not os.path.exists(dissolve_subfolder):
    os.makedirs(dissolve_subfolder)
batch_dissolve(clip_subfolder,dissolve_subfolder)