import os
import pandas as pd
import numpy as np
import json
import pickle
from osgeo import gdal, osr
import warnings
import datetime
from multiprocessing import Pool
from joblib import Parallel, delayed
from functools import partial
from matplotlib.ticker import MultipleLocator
import psutil
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")

def read_tif(tif_file):
    dataset = gdal.Open(tif_file)
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    im_proj = (dataset.GetProjection())
    im_Geotrans = (dataset.GetGeoTransform())
    im_data = dataset.ReadAsArray(0, 0, cols, rows)
    if im_data.ndim == 3:
        im_data = np.moveaxis(dataset.ReadAsArray(0, 0, cols, rows), 0, -1)
    dataset = None
    return im_data, im_Geotrans, im_proj,rows, cols

def array_to_geotiff(array, output_path, geo_transform, projection, band_names=None):
    rows, cols, num_bands = array.shape
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(output_path, cols, rows, num_bands, gdal.GDT_Float32)
    
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)
    
    for band_num in range(num_bands):
        band = dataset.GetRasterBand(band_num + 1)
        band.WriteArray(array[:, :, band_num])
        band.FlushCache()
        
        if band_names:
            band.SetDescription(band_names[band_num])
    
    dataset = None
    band = None
    return

def get_corner(image_file):
    dataset = gdal.Open(image_file)
    geo_transform = dataset.GetGeoTransform()
    x_res = geo_transform[1]
    y_res = geo_transform[5] 
    x_min = geo_transform[0]
    y_max = geo_transform[3]
    x_max = x_min + x_res * dataset.RasterXSize
    y_min = y_max + y_res * dataset.RasterYSize
    
    x_size = dataset.RasterXSize
    y_size = dataset.RasterYSize
    im_proj = dataset.GetProjection()
    return im_proj, x_res, y_res, x_size, y_size, (x_min, y_min, x_max, y_max)
def get_pixel_pft(lulc_data, filter_pft):
    land_cover_type = {10: "Rainfed cropland",11: "Herbaceous cover cropland",12: "Tree or shrub cover (Orchard) cropland",
                       20: "Irrigated cropland",51: "Open evergreen broadleaved forest",52: "Closed evergreen broadleaved forest",
                       61: "Open deciduous broadleaved forest",62: "Closed deciduous broadleaved forest",71: "Open evergreen needle-leaved forest",
                       72: "Closed evergreen needle-leaved forest",81: "Open deciduous needle-leaved forest",82: "Closed deciduous needle-leaved forest",
                       91: "Open mixed leaf forest (broadleaved and needle-leaved)",92: "Closed mixed leaf forest (broadleaved and needle-leaved)", 
                       120: "Shrubland",121: "Evergreen shrubland",122: "Deciduous shrubland",130: "Grassland",140: "Lichens and mosses",
                       150: "Sparse vegetation",152: "Sparse shrubland",153: "Sparse herbaceous",181: "Swamp",182: "Marsh",183: "Flooded flat",
                       184: "Saline",185: "Mangrove",186: "Salt marsh",187: "Tidal flat",190: "Impervious surfaces",200: "Bare areas",
                       201: "Consolidated bare areas",202: "Unconsolidated bare areas",210: "Water body",220: "Permanent ice and snow",
                       0: "Filled value",250: "Filled value"}
    PFTs = {"Rainfed cropland":"CPR", "Herbaceous cover cropland":"CPR","Tree or shrub cover (Orchard) cropland":"CPR",
            "Irrigated cropland":"CPR", "Open evergreen broadleaved forest":"EBF", "Closed evergreen broadleaved forest":"EBF",
            "Open deciduous broadleaved forest":"DBF","Closed deciduous broadleaved forest":"DBF", "Open evergreen needle-leaved forest":"ENF",
            "Closed evergreen needle-leaved forest":"ENF","Open deciduous needle-leaved forest":"DNF","Closed deciduous needle-leaved forest":"DNF",
            "Open mixed leaf forest (broadleaved and needle-leaved)":"MF","Closed mixed leaf forest (broadleaved and needle-leaved)":"MF", 
            "Shrubland":"SHR", "Evergreen shrubland":"SHR","Deciduous shrubland":"SHR","Grassland":"GRA","Lichens and mosses":"nouse",
            "Sparse vegetation":"no_use", "Sparse shrubland":"no_use","Sparse herbaceous":"no_use","Swamp":"no_use","Marsh":"no_use", "Flooded flat":"no_use",
            "Saline":"no_use", "Mangrove":"no_use","Salt marsh":"no_use","Tidal flat":"no_use","Impervious surfaces":"no_use", "Bare areas":"no_use",
            "Consolidated bare areas":"no_use","Unconsolidated bare areas":"no_use","Water body":"no_use","Permanent ice and snow":"no_use",
            "Filled value":"no_use", "Filled value":"no_use"}
    lulc_flatten = lulc_data.flatten()
    pft = [PFTs[land_cover_type[x]] for x in lulc_flatten]
    mask = np.array([1 if item == filter_pft else np.nan for item in pft])
    mask = mask.reshape(lulc_data.shape[0],lulc_data.shape[1],1)
    return mask

def load_and_predict(im_array, model_folder, tr, iteration):
    with open(f"{model_folder}/{tr}_PLSR_model_interation{iteration+1}.pkl", 'rb') as model:
        pls = pickle.load(model)
    feature_names = pls.feature_names_in_
    im_array = pd.DataFrame(im_array, columns=feature_names)
    pred = pls.predict(im_array)
    return pd.DataFrame(pred, columns=[f'iteration_{iteration+1}'])

def apply_trait_models(image_array, PFT, model_path):
    ex_idx = [ 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111,112, 142, 143, 144, 145, 146, 147, 148, 
          149, 150, 151, 152, 153,154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 204, 205, 206,207, 208, 209, 
          210, 211, 212, 213, 214, 215, 216, 217, 218, 219,220, 221, 222, 223, 224, 225, 226, 227, 228, 229]
    filter_im = np.delete(im_data, ex_idx, axis = -1)
    filter_im = np.nan_to_num(filter_im, nan=0)
    im_array = filter_im.reshape(-1,filter_im.shape[2])
    
    model_folder = f"{model_path}{PFT}/saved_models"
    tr_name = ["Chla+b", "Ccar", "EWT", "Nitrogen"]
    var = True
    for tr in tr_name:
        trait_predictions = Parallel(n_jobs=20)(delayed(load_and_predict)(im_array, model_folder, tr, iteration) for iteration in range(100))
        trait_predictions = pd.concat(trait_predictions, axis=1)
        
        mean_pred = np.array(trait_predictions.mean(axis = 1)).reshape(filter_im.shape[0], filter_im.shape[1])
        std_pred  = np.array(trait_predictions.std(axis = 1)).reshape(filter_im.shape[0], filter_im.shape[1])
        final_pred = np.concatenate((mean_pred[:, :, np.newaxis], std_pred[:, :, np.newaxis]), axis=2)
        trait_predictions = None
        if var:
            results = final_pred
            var = False
        else:
            results = np.concatenate((results,final_pred),axis = 2)
    return results


image_path = "/mnt/cephfs/scratch/groups/chen_group/FujiangJi/BRDF_correction/6_BRDF_correction/"
lai_path = "/mnt/cephfs/scratch/groups/chen_group/FujiangJi/PRISMA_convolved_NIR_RED/8_estimated_LAI_VI_masked/NBAR_refl/"
lulc_path = "/mnt/cephfs/scratch/groups/chen_group/FujiangJi/PRISMA_convolved_NIR_RED/2_land_cover_NEON_sites/"
model_path = "/mnt/cephfs/scratch/groups/chen_group/FujiangJi/NEON_PLSR/6_PLSR_results/0_add_LAI/"
out_path = "/mnt/cephfs/scratch/groups/chen_group/FujiangJi/NEON_PLSR/7_PRISMA_estimated_traits/NBAR_refl_with_LAI/"

folders = ['D01_BART','D01_HARV','D02_SCBI','D03_OSBS','D07_MLBS','D07_ORNL','D08_TALL','D10_CPER','D13_MOAB','D14_JORN','D16_WREF']


for folder in folders:
    os.makedirs(f"{out_path}/{folder}", exist_ok=True)
    imagery_path = f"{image_path}{folder}"
    output_path = f"{out_path}{folder}"
    lulc_folder = f"{lulc_path}{folder}"
    lai_folder = f"{lai_path}{folder}"
    file_name = os.listdir(imagery_path)
    file_name = [x for x in file_name if "_FULL_NBAR.tif" in x and "._" not in x and ".aux.xml" not in x]
    for kk, file in enumerate(file_name):
        print(f"{datetime.datetime.now().replace(microsecond=0)}, {folder}, {kk+1}/{len(file_name)}: {file}")

        imagery_file = f"{imagery_path}/{file}"
        lai_file = f"{lai_folder}/{file.split('.')[0]}_LAI_VI_masked.tif"
        year = file.split("_")[3][0:4]
        if year == "2023":
            year ="2022"
        lulc_file = f"{lulc_folder}/{folder}_{year}_land_cover.tif"
        
        input_ds = gdal.Open(lulc_file)
        out_lulc = f"{output_path}/{file[:-4]}_lulc.tif"
        proj, x_res, y_res, x_size, y_size, bounds = get_corner(imagery_file)
        gdal.Warp(out_lulc, input_ds, xRes=x_res, yRes=abs(y_res),dstSRS=proj, outputBounds=bounds, 
                  width=x_size, height=y_size, resampleAlg=gdal.GRA_NearestNeighbour)
        input_ds = None
        out_lulc = None
        
        lulc_file = f"{output_path}/{file[:-4]}_lulc.tif"
        im_data, im_Geotrans, im_proj,im_rows, im_cols = read_tif(imagery_file)
        lulc_data,lulc_Geotrans, lulc_proj,lulc_rows, lulc_cols = read_tif(lulc_file)
        lai_data,lai_Geotrans, lai_proj, lai_rows, lai_cols = read_tif(lai_file)
        lai_data = lai_data[:,:,2]
        lai_data = np.nan_to_num(lai_data, nan=0)
        lai_data = lai_data[:, :, np.newaxis]
        im_data = np.concatenate([im_data, lai_data], axis = 2)
        
        masks = np.all(np.isnan(im_data), axis=2)
        masks = np.where(masks, np.nan, 1)
        masks = masks[:,:,np.newaxis]
        
        print("  all_data")
        tr_all_data = apply_trait_models(im_data,"all_data",model_path)
        tr_all_data = tr_all_data*masks
        
        band_names = ["Chla+b_mean", "Chla+b_std", "Ccar_mean", "Ccar_std", "EWT_mean",
                      "EWT_std",  "Nitrogen_mean","Nitrogen_std"]
        print("  start saving tif")
        out_tif = f"{output_path}/{file[:-4]}_all_data_models_traits.tif"
        array_to_geotiff(tr_all_data, out_tif, im_Geotrans, im_proj, band_names=band_names)
        tr_all_data = None

        PFTs = ["CPR","DBF","DNF","EBF","ENF","GRA","MF","SHR"]
        final_traits = 0
        for pft in PFTs:
            print("  ", pft)
            tr_estimated = apply_trait_models(im_data,pft,model_path)
            mask = get_pixel_pft(lulc_data, pft)
            traits = tr_estimated*mask
            traits = np.nan_to_num(traits, nan=0)
            final_traits = final_traits + traits
            traits = None
        
        final_traits = final_traits*masks
        out_tif = f"{output_path}/{file[:-4]}_PFT_specific_models_traits.tif"
        array_to_geotiff(final_traits, out_tif, im_Geotrans, im_proj, band_names=band_names)
        final_traits= None
     