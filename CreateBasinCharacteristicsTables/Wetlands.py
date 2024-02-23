import arcpy
import os

class WetlandToolbox(object):
    def __init__(self):
        self.label = "Wetland Toolbox"
        self.description = "A toolbox for processing wetland data"
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Input parameters
        basin_param = arcpy.Parameter(
            displayName="Input Basin Shapefile",
            name="basin_shp",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input")

        wetland_param = arcpy.Parameter(
            displayName="Input Wetland Shapefile",
            name="wetland_shp",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input")

        output_folder_param = arcpy.Parameter(
            displayName="Output Folder",
            name="output_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [basin_param, wetland_param, output_folder_param]

    def execute(self, parameters, messages):
        # Get parameters
        basin_shp = parameters[0].valueAsText
        wetland_shp = parameters[1].valueAsText
        output_folder = parameters[2].valueAsText

        # Create subfolder 'Wetland'
        wetland_folder = os.path.join(output_folder, 'Wetland')
        if not os.path.exists(wetland_folder):
            os.makedirs(wetland_folder)

        # Create temp folder and gdb named 'wetland' under subfolder 'Wetland'
        temp_folder = os.path.join(wetland_folder, 'temp')
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        gdb_path = os.path.join(temp_folder, 'wetland.gdb')
        if not arcpy.Exists(gdb_path):
            arcpy.CreateFileGDB_management(temp_folder, 'wetland.gdb')

        # Create NationalWetlands table
        national_wetlands_table = os.path.join(gdb_path, 'NationalWetlands')
        if not arcpy.Exists(national_wetlands_table):
            arcpy.CreateTable_management(gdb_path, 'NationalWetlands')
            arcpy.AddField_management(national_wetlands_table, 'GID', 'LONG')
            arcpy.AddField_management(national_wetlands_table, 'Wetlands', 'DOUBLE')
            arcpy.AddField_management(national_wetlands_table, 'Lakes_and_Ponds', 'DOUBLE')

        # Process wetland data and populate NationalWetlands table
        with arcpy.da.SearchCursor(basin_shp, ['GID', 'SHAPE@AREA']) as cursor:
            for row in cursor:
                gid = row[0]
                basin_area = row[1]
                wetland_area = 0
                lake_pond_area = 0
                
                # Calculate wetland and lake/pond area within each basin
                with arcpy.da.SearchCursor(wetland_shp, ['WETLAND_TY', 'SHAPE@AREA'], f'GID={gid}') as wcursor:
                    for wrow in wcursor:
                        area = wrow[1]
                        if wrow[0] == 'wetland':
                            wetland_area += area
                        elif wrow[0] == 'lake and pond':
                            lake_pond_area += area
                
                # Calculate percentages
                wetlands_percentage = (wetland_area / basin_area) * 100
                lakes_ponds_percentage = (lake_pond_area / basin_area) * 100

                # Insert data into NationalWetlands table
                with arcpy.da.InsertCursor(national_wetlands_table, ['GID', 'Wetlands', 'Lakes_and_Ponds']) as icursor:
                    icursor.insertRow((gid, wetlands_percentage, lakes_ponds_percentage))

        arcpy.AddMessage("Process completed successfully.")

if __name__ == "__main__":
    # Execute the tool
    tool = WetlandToolbox()
    arcpy.AddMessage("Tool initialized successfully.")
    tool.execute(arcpy.GetParameterInfo())
