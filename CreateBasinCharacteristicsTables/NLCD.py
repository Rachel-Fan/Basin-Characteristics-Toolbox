import arcpy
import os
import time

def batch_clip_raster(input_raster, input_polygon, output_folder, gdb_name):
    try:
        # Check out Spatial Analyst extension
        arcpy.CheckOutExtension("Spatial")

        # Set overwriteOutput to True
        arcpy.env.overwriteOutput = True

        # Create the output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Create the geodatabase folder
        gdb_folder = os.path.join(output_folder, gdb_name)
        if not os.path.exists(gdb_folder):
            os.makedirs(gdb_folder)

        # Create the file geodatabase
        gdb_path = os.path.join(gdb_folder, f"{gdb_name}.gdb")
        if not arcpy.Exists(gdb_path):
            arcpy.CreateFileGDB_management(gdb_folder, f"{gdb_name}.gdb")

        # Create a folder to store TIFF files
        tif_folder = os.path.join(gdb_folder, f"{gdb_name}_tif")
        if not os.path.exists(tif_folder):
            os.makedirs(tif_folder)

        arcpy.env.workspace = gdb_path

        # Iterate over input polygons
        with arcpy.da.SearchCursor(input_polygon, ["FID", "SHAPE@", "GID"]) as cursor:
            for row in cursor:
                feature_id = row[0]
                polygon_geometry = row[1]
                feature_name = row[2]

                # Set extent to the current polygon
                arcpy.env.extent = polygon_geometry.extent

                # Perform extract by mask
                mask = arcpy.sa.ExtractByMask(input_raster, polygon_geometry)

                # Save the output raster
                output_raster = os.path.join(tif_folder, f"{feature_name}_{gdb_name}.tif")
                mask.save(output_raster)

                # Reset extent
                arcpy.env.extent = None

        arcpy.AddMessage("Raster clipping completed successfully.")

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(str(e))

def convertTifToShp(tif_folder, shp_folder, output_folder, gdb_name):
    try:
        raster_files = [f for f in os.listdir(tif_folder) if f.endswith(".tif")]
        for raster_file in raster_files:
            tif_path = os.path.join(tif_folder, raster_file)
            shp_path = os.path.join(shp_folder, os.path.splitext(raster_file)[0] + ".shp")
            arcpy.conversion.RasterToPolygon(tif_path, shp_path, "SIMPLIFY")

        arcpy.AddMessage("Conversion from TIFF to shapefile completed successfully.")

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(str(e))

def addCatField(shp_folder, field_name):
    try:
        arcpy.env.workspace = shp_folder
        shapefiles = arcpy.ListFeatureClasses("*.shp")

        for shapefile in shapefiles:
            if field_name not in [field.name for field in arcpy.ListFields(shapefile)]:
                arcpy.AddField_management(shapefile, field_name, "DOUBLE")
            base_name = os.path.splitext(os.path.basename(shapefile))[0]

            arcpy.AddField_management(shapefile, "FirstDigit", "TEXT")
            with arcpy.da.UpdateCursor(shapefile, ["gridcode", "FirstDigit"]) as cursor:
                for row in cursor:
                    if row[0] is not None:
                        row[1] = str(row[0])[0]
                    cursor.updateRow(row)

            dissolved_shapefile = os.path.join(category_folder, f"{base_name}_category.shp")
            arcpy.management.Dissolve(shapefile, dissolved_shapefile, "FirstDigit")

            arcpy.AddField_management(dissolved_shapefile, "Category", "TEXT")
            with arcpy.da.UpdateCursor(dissolved_shapefile, ["FirstDigit", "Category"]) as cursor:
                for row in cursor:
                    first_digit = row[0]
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

            arcpy.CalculateGeometryAttributes_management(dissolved_shapefile, [["Area", "AREA"]], "", "ACRES")
            total_area = sum([row[0] for row in arcpy.da.SearchCursor(dissolved_shapefile, "AREA")])
            arcpy.AddField_management(dissolved_shapefile, "Percentage", "DOUBLE")
            with arcpy.da.UpdateCursor(dissolved_shapefile, ["AREA", "Percentage"]) as cursor:
                for row in cursor:
                    row[1] = (row[0] / total_area) * 100
                    cursor.updateRow(row)

        arcpy.AddMessage("Area calculation completed successfully.")

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(str(e))

def updateNLCDTable(category_folder, gdb_folder, gdb_name):
    try:
        arcpy.env.workspace = category_folder
        shapefiles = arcpy.ListFeatureClasses("*.shp")

        nlcd_gdb = os.path.join(gdb_folder, f"{gdb_name}.gdb")
        nlcd_table = os.path.join(nlcd_gdb, f"{gdb_name}")

        fields_to_add = [field.name for field in arcpy.ListFields(nlcd_table) if field.name != "GID"]
        with arcpy.da.InsertCursor(nlcd_table, ["GID"] + fields_to_add) as cursor:
            for shapefile in shapefiles:
                gid = os.path.splitext(os.path.basename(shapefile))[0].split('_')[0]
                percentages = {}
                with arcpy.da.SearchCursor(shapefile, ["Category", "Percentage"]) as s_cursor:
                    for row in s_cursor:
                        category, percentage = row
                        percentages[category] = percentage
                values = [gid] + [percentages.get(category, 0.0) for category in fields_to_add]
                cursor.insertRow(values)

        arcpy.AddMessage("NLCD summary table created successfully.")

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(str(e))

def main():
    try:
        print("Tool starts")
        current_time = time.strftime("%m-%d %X", time.localtime())
        print(current_time)

        # Input parameters
        input_raster = arcpy.GetParameterAsText(0)
        input_polygon = arcpy.GetParameterAsText(1)
        output_folder = arcpy.GetParameterAsText(2)
        gdb_name = "NLCD"

        # Call functions
        batch_clip_raster(input_raster, input_polygon, output_folder, gdb_name)

        gdb_folder = os.path.join(output_folder, gdb_name)
        tif_folder = os.path.join(gdb_folder, f"{gdb_name}_tif")
        shp_folder = os.path.join(gdb_folder, f"{gdb_name}_shp")
        adding_field = 'Area_Acre'

        if os.path.exists(tif_folder):
            convertTifToShp(tif_folder, shp_folder, output_folder, gdb_name)
            if os.path.exists(shp_folder):
                addCatField(shp_folder, adding_field)
                category_folder = os.path.join(shp_folder, f"{shp_folder}_category")
                if os.path.exists(category_folder):
                    updateNLCDTable(category_folder, gdb_folder, gdb_name)
                else:
                    arcpy.AddWarning("Category folder not found.")
            else:
                arcpy.AddWarning("Shapefile folder not found.")
        else:
            arcpy.AddWarning("TIFF folder not found.")

        print("Tool done at:")
        current_time = time.strftime("%m-%d %X", time.localtime())
        print(current_time)

    except Exception as e:
        print(str(e))

if __name__ == "__main__":
    main()
