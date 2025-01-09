import os
import sys
import numpy as np
from osgeo import gdal, ogr
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


def read_tif(tif_file):
    dataset = gdal.Open(tif_file)
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    im_proj = (dataset.GetProjection())
    im_Geotrans = (dataset.GetGeoTransform())
    im_data = np.moveaxis(dataset.ReadAsArray(0, 0, cols, rows), 0, -1)
    return im_data, im_Geotrans, im_proj,rows, cols

def array_to_geotiff(array, output_path, geo_transform, projection):
    rows, cols, num_bands = array.shape
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(output_path, cols, rows, num_bands, gdal.GDT_Float32)
    
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)
    
    for band_num in range(num_bands):
        dataset.GetRasterBand(band_num + 1).WriteArray(array[:, :, band_num])
        dataset.FlushCache()
    
    dataset = None
    return


NDVI_threshold = {"CPER":0.2, "MOAB":0.3, "OSBS":0.35, "MLBS": 0.4, "JORN": 0.2, "SRER": 0.3, "WREF":0.4, "BONA":0.45, "HEAL":0.45}

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
flights = ["NEON_2021_D14_SRER_20210824"]


for flightname in flights:
    print(flightname)
    sites = flightname.split("_")[3]
    ndvi_threshold = NDVI_threshold[sites]
    #####
    data_folder = "/Volumes/UW_Madison/0_PhD_dissertation_data/1_NEON_AOP_trait_maps/3_clipped_data/"
    out_folder = "/Volumes/UW_Madison/0_PhD_dissertation_data/1_NEON_AOP_trait_maps/4_upscaled_data/"
     
    image_in_folder = f"{data_folder}{flightname}"
    image_out_folder = f"{out_folder}{flightname}"
    os.makedirs(image_out_folder, exist_ok=True)

    imagery = f"{flightname}_imagery_clipped.tif"
    # leaf_traits = [f"{flightname}_Carotenoids_area_clipped.tif", f"{flightname}_Chlorophylls_area_clipped.tif",
    #                f"{flightname}_EWT_clipped.tif",f"{flightname}_LMA_clipped.tif", 
    #                f"{flightname}_Nitrogen_clipped.tif"]

    leaf_traits = [f"{flightname}_EWT_clipped.tif"]
    
    # input_im = gdal.Open(f"{image_in_folder}/{imagery}")
    # output_path = f"{image_out_folder}/{imagery[:-4]}_aggregated.tif"
    # gdal.Warp(output_path, input_im, format='GTiff', xRes=30, yRes=30, resampleAlg=gdal.GRA_Bilinear)
    # input_im = None
    
    ##### Build mask
    im_array, im_Geotrans, im_proj, rows, cols =  read_tif(f"{image_in_folder}/{imagery}")
    nir_band = im_array[:,:,3]
    red_band = im_array[:,:,0]
    ndvi = (nir_band - red_band)/(nir_band + red_band)
    condition1 = ndvi > ndvi_threshold
    condition2 = nir_band>0.1*10000
    mask1 = np.where(condition1, 1, np.nan)
    mask2 = np.where(condition2, 1, np.nan)
    mask = mask1 * mask2
    mask = np.expand_dims(mask, axis=-1)
    
    #im_array = None
    
    #### upscaling
    for tr_file in leaf_traits:
        trait_array, trait_Geotrans, trait_proj, rows, cols =  read_tif(f"{image_in_folder}/{tr_file}")
        masked_trait_map = mask * trait_array
        
        #trait_array = None
        aggregated_traits = np.zeros(shape = ((rows//30)+1, (cols//30)+1, masked_trait_map.shape[2]))
        veg_fraction = np.zeros(shape = ((rows//30)+1, (cols//30)+1, mask.shape[2]))
#         print("vegetation_fraction_shape:", veg_fraction.shape)
#         print("aggregated_traits_shape", aggregated_traits.shape)
        for ii in range(0, rows, 30):
            for jj in range(0, cols, 30):
                data_array = masked_trait_map[ii: min(rows, (ii + 30)), jj: min(cols, (jj + 30)),:]
                mean_values = np.nanmean(data_array, axis = (0,1))
                aggregated_traits[int(ii/30), int(jj/30), :] = mean_values

                data_array2 = mask[ii: min(rows, (ii + 30)), jj: min(cols, (jj + 30)),:]
                one_counts = np.count_nonzero(data_array2 == 1)
                fraction = one_counts/900
                veg_fraction[int(ii/30), int(jj/30),:] = fraction
                       
        output_path = f"{image_out_folder}/{tr_file[:-4]}_aggregated.tif"
        mask_path = f"{image_out_folder}/{flightname}_vegetation_fraction.tif"

        geo_transform = (trait_Geotrans[0], 30.0, trait_Geotrans[2],
                         trait_Geotrans[3],trait_Geotrans[4],-30.0)

        array_to_geotiff(aggregated_traits, output_path, geo_transform, trait_proj)
        # array_to_geotiff(veg_fraction, mask_path, geo_transform, trait_proj)