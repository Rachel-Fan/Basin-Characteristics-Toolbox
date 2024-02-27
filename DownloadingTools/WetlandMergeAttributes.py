import arcpy
import os
import time

def merge_shapfiles_by_prefix(before_merge_folder, output_folder):
    shapefile_dict = {}
    
    # Create the 'merged' folder if it doesn't exist
    merged_folder = os.path.join(output_folder, "merged")
    if not os.path.exists(merged_folder):
        os.makedirs(merged_folder)
    
    for filename in os.listdir(before_merge_folder):
        if filename.endswith(".shp"):
            # Extract the prefix (first four digits) from the filename
            prefix = filename[:4]
            # Check if trhe prefix already exists in the dictionary
            if prefix in shapefile_dict:
                # Append
                shapefile_dict[prefix].append(os.path.join(before_merge_folder, filename))
                
            else:
                shapefile_dict[prefix] = [os.path.join(before_merge_folder,filename)]
                
    for prefix, shapefiles in shapefile_dict.items():
        output_merged_shapefile = os.path.join(merged_folder, f"{prefix}_merged.shp")
        arcpy.Merge_management(shapefiles,output_merged_shapefile)
        
        print("shapefiles with {prefix} are merged")
        
    print("Shapefiles merged")
    

print("Tool starts")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)


# Check Spatial Analyst extension
arcpy.CheckOutExtension("Spatial")
# Enable overwriting of output files
arcpy.env.overwriteOutput = True

# Set input and output folders
before_merge_folder = r"C:\Users\rfan\Documents\ArcGIS\Projects\NeDNR_Regression\Wetland_Local\ToolTest"
output_folder = r"C:\Users\rfan\Documents\ArcGIS\Projects\NeDNR_Regression\Wetland_Local\Processed"

# Set the coordinate system
output_coordinate_system = arcpy.SpatialReference(26852)  # WKID 26852 for NAD83 StatePlane Nebraska FIPS 2600

# Create the 'reproject' folder if it doesn't exist
reproject_folder = os.path.join(output_folder, "reproject")
if not os.path.exists(reproject_folder):
    os.makedirs(reproject_folder)

# Iterate through each shapefile in the input folder
for filename in os.listdir(merged_folder):
    if filename.endswith(".shp"):
        # Define the full paths
        input_shapefile = os.path.join(merged_folder, filename)
        output_shapefile = os.path.join(reproject_folder, filename)
        print('Input shapefile is selected', input_shapefile)

        # Step 1: Run Delete Identical
        arcpy.DeleteIdentical_management(input_shapefile, ["SHAPE_Area"])
        print('Delete Identical done')

        # Step 2: Reproject the shapefile
        arcpy.management.Project(input_shapefile, output_shapefile, output_coordinate_system)
        print('Reproject done')

        # Step 3: Remove records based on WETLAND_TY field
        with arcpy.da.UpdateCursor(output_shapefile, ["WETLAND_TY"]) as cursor:
            for row in cursor:
                if not any(word in row[0] for word in ["Wetland", "Lake", "Pond"]):
                    cursor.deleteRow()
        print('Records cleaned')

        # Step 4: Add a new field "Type" and populate it based on WETLAND_TY
        arcpy.AddField_management(output_shapefile, "Type", "TEXT")
        with arcpy.da.UpdateCursor(output_shapefile, ["WETLAND_TY", "Type"]) as cursor:
            for row in cursor:
                if "Wetland" in row[0]:
                    row[1] = "Wetland"
                elif "Lake" in row[0] or "Pond" in row[0]:
                    row[1] = "LakePond"
                cursor.updateRow(row)
        print('New field TYPE is created and populated')
        
        # Step 5: Remove Attribute and ACRES fields
        fields_to_delete = ["Attribute", "ACRES"]
        arcpy.DeleteField_management(output_shapefile, fields_to_delete)
        print('Extra fields removed')

        print(f"Processed: {filename}")
        print('*********************')

print("All shapefiles processed.")

print("Tool done at:")
current_time = time.strftime("%m-%d %X",time.localtime())
print(current_time)
