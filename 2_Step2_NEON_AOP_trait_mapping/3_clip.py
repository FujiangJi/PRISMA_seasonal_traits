import os
import geopandas as gpd
from osgeo import gdal, ogr,gdalconst
from shapely.geometry import Point, Polygon,box


flights = ["NEON_2020_D10_CPER_20200913",
           "NEON_2020_D13_MOAB_20200705",
           "NEON_2021_D03_OSBS_20210924",
           "NEON_2021_D07_MLBS_20210617",
           "NEON_2021_D10_CPER_20210525",
           "NEON_2021_D10_CPER_20210608",
           "NEON_2021_D13_MOAB_20210429",
           "NEON_2021_D14_JORN_20210826",
           "NEON_2021_D14_JORN_20210909",
           "NEON_2021_D14_SRER_20210824",
           "NEON_2021_D14_SRER_20210907",
           "NEON_2021_D16_WREF_20210724",
           "NEON_2021_D19_BONA_20210713",
           "NEON_2021_D19_HEAL_20210719"]


for flightname in flights:
    print(flightname)
    data_folder = "/Volumes/UW_Madison/0_PhD_dissertation_data/1_NEON_AOP_trait_maps/2_mosaic_data/"
    out_folder = "/Volumes/UW_Madison/0_PhD_dissertation_data/1_NEON_AOP_trait_maps/3_clipped_data/"

    image_in_folder = f"{data_folder}{flightname}"
    image_out_folder = f"{out_folder}{flightname}"
    os.makedirs(image_out_folder, exist_ok=True)

    input_shapefile_path = f'{out_folder}/0_shapefiles/{flightname}_shapefile.shp'
    gdf = gpd.read_file(input_shapefile_path)

    upper_left_point = gdf.geometry.iloc[0].bounds
    bottom_right_point = gdf.geometry.iloc[1].bounds
    rectangle = Polygon([(upper_left_point[0], upper_left_point[3]),
                         (bottom_right_point[2], upper_left_point[3]),
                         (bottom_right_point[2], bottom_right_point[1]),
                         (upper_left_point[0], bottom_right_point[1])])

    gdf_rectangle = gpd.GeoDataFrame(geometry=[rectangle], crs=gdf.crs)

    file_names = [f"{flightname}_Carotenoids_area.tif", f"{flightname}_Chlorophylls_area.tif",
                  f"{flightname}_EWT.tif", f"{flightname}_imagery.tif",
                  f"{flightname}_LMA.tif", f"{flightname}_Nitrogen.tif"]

    
    bounds = gdf_rectangle.bounds
    min_x = bounds["minx"].values[0]
    min_y = bounds["miny"].values[0]
    max_x = bounds["maxx"].values[0]
    max_y = bounds["maxy"].values[0]
    ul_x, ul_y = (min_x, max_y)
    lr_x, lr_y = (max_x, min_y)
    # print(ul_x, lr_y, lr_x, ul_y)

    for file in file_names:
        input_tif = f"{image_in_folder}/{file}"
        output_tif = f"{image_out_folder}/{file[:-4]}_clipped.tif"

        gdal.Warp(output_tif, input_tif, format = 'GTiff', outputBounds=(ul_x, lr_y, lr_x, ul_y))
        output_tif = None