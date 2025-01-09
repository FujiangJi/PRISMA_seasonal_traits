import os
import pandas as pd
import numpy as np
from osgeo import gdal, osr
import warnings
warnings.filterwarnings("ignore")


def read_tif(tif_file):
    dataset = gdal.Open(tif_file)
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    im_proj = (dataset.GetProjection())
    im_Geotrans = (dataset.GetGeoTransform())
    im_data = np.moveaxis(dataset.ReadAsArray(0, 0, cols, rows), 0, -1)
    return im_data, im_Geotrans, im_proj,rows, cols

data_path = "/Volumes/data/PRISMA_L2D/PRISMA_L2D_tif/"
out_path = "/Volumes/data/PRISMA_imagery_array/"
folders = os.listdir(data_path)
for folder in folders:
    os.makedirs(f"{out_path}{folder}", exist_ok=True)

in_folder_path = [f"{data_path}{x}" for x in folders]
out_folder_path = [f"{out_path}{x}" for x in folders]

for i in range(len(in_folder_path)):
    print(i+1, in_folder_path[i])
    print("***********************************************************************")
    file_name = os.listdir(in_folder_path[i])
    file_name = [x for x in file_name if ("_FULL.tif" in x)&("._" not in x)]
    for file in file_name:
        print("   ", file)
        im_data, im_Geotrans, im_proj, rows, cols = read_tif(f"{in_folder_path[i]}/{file}")
        basename = file.split(".")[0]
        df= pd.read_csv(f"{in_folder_path[i]}/{basename}.wvl",delimiter=" ")
        df['wl'] = round(df['wl'],2)
        df['wl'] = df['wl'].astype(str)
        wl = list(df['wl'])
        dataset = pd.DataFrame(im_data.reshape(-1,im_data.shape[2]),columns = wl)
        dataset.to_csv(f"{out_folder_path[i]}/{basename}.csv", index = False)
        dataset = None
        im_data = None