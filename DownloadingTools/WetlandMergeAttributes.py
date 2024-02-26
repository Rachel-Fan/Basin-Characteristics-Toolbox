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

# Set input and output folders
input_folder = r"path\to\input\folder"
output_folder = r"path\to\output\folder"

# Set the coordinate system
output_coordinate_system = arcpy.SpatialReference(26852)  # WKID 26852 for NAD83 StatePlane Nebraska FIPS 2600

# Create the 'reproject' folder if it doesn't exist
reproject_folder = os.path.join(output_folder, "reproject")
if not os.path.exists(reproject_folder):
    os.makedirs(reproject_folder)

# Iterate through each shapefile in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(".shp"):
        # Define the full paths
        input_shapefile = os.path.join(input_folder, filename)
        output_shapefile = os.path.join(reproject_folder, filename)

        # Step 1: Run Delete Identical
        arcpy.DeleteIdentical_management(input_shapefile, ["Acres"])

        # Step 2: Reproject the shapefile
        arcpy.management.Project(input_shapefile, output_shapefile, output_coordinate_system)

        # Step 3: Remove records based on WETLAND_TY field
        with arcpy.da.UpdateCursor(output_shapefile, ["WETLAND_TY"]) as cursor:
            for row in cursor:
                if not any(word in row[0] for word in ["Wetland", "Lake", "Pond"]):
                    cursor.deleteRow()

        # Step 4: Add a new field "Type" and populate it based on WETLAND_TY
        arcpy.AddField_management(output_shapefile, "Type", "TEXT")
        with arcpy.da.UpdateCursor(output_shapefile, ["WETLAND_TY", "Type"]) as cursor:
            for row in cursor:
                if "Wetland" in row[0]:
                    row[1] = "Wetland"
                elif "Lake" in row[0] or "Pond" in row[0]:
                    row[1] = "LakePond"
                cursor.updateRow(row)

        # Step 5: Remove Attribute and ACRES fields
        fields_to_delete = ["Attribute", "ACRES"]
        arcpy.DeleteField_management(output_shapefile, fields_to_delete)

        print(f"Processed: {filename}")

print("All shapefiles processed.")
