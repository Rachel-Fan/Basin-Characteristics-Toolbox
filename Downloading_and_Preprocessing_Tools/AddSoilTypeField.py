import arcpy
import os
import time



# Function to clean and format SoilType values
def format_soil_type(hydgrpdcd):
    if not hydgrpdcd or hydgrpdcd.strip() == "":
        return "OtherSoilTypes"
    elif "/" in hydgrpdcd:
        return hydgrpdcd.replace("/", "_")
    else:
        return hydgrpdcd

# Input folder containing shapefiles
input_folder = arcpy.GetParameterAsText(0)

current_time = time.strftime("%m-%d %X",time.localtime())
print("Tool starts at", current_time)

# Add field "SoilType" to each shapefile
arcpy.AddMessage("Processing shapefiles...")
for root, dirs, files in os.walk(input_folder):
    for file in files:
        if file.endswith(".shp"):
            shapefile = os.path.join(root, file)
            arcpy.AddMessage("Processing: " + shapefile)
            arcpy.AddField_management(shapefile, "SoilType", "TEXT", field_length=50)
            
            # Update SoilType field based on hydgrpdcd field
            with arcpy.da.UpdateCursor(shapefile, ["hydgrpdcd", "SoilType"]) as cursor:
                for row in cursor:
                    row[1] = format_soil_type(row[0])
                    cursor.updateRow(row)

arcpy.AddMessage("Script execution completed.")

current_time = time.strftime("%m-%d %X",time.localtime())
print("Tool done at", current_time)