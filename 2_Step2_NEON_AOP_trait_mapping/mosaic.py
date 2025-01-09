import os
import sys
from osgeo import gdal


flightname = sys.argv[1]
image_folder = sys.argv[2]
output_folder = sys.argv[3]

imagery_path = f'{image_folder}imagery/'
imagery_list = os.listdir(imagery_path)
imagery_list = [x for x in imagery_list if "." not in x]

trait_path = f'{image_folder}traits/'
trait_list = os.listdir(trait_path)
trait_list = [x for x in trait_list if "." not in x]
cab_list = [x for x in trait_list if "Chlorophylls_area" in x]
car_list = [x for x in trait_list if "Carotenoids_area" in x]
ewt_list = [x for x in trait_list if "EWT" in x]
lma_list = [x for x in trait_list if "LMA" in x]
nitrogen_list = [x for x in trait_list if "Nitrogen" in x]

data_list = [imagery_list, cab_list, car_list, ewt_list, lma_list, nitrogen_list]
names = ['imagery','Chlorophylls_area','Carotenoids_area','EWT','LMA','Nitrogen']

k = 0
for data in data_list:
    data = [imagery_path+x for x in data] if k ==0 else [trait_path+x for x in data]
    output_path = f'{output_folder}mosaic_data/{flightname}/{flightname}_{names[k]}.tif'
    options = gdal.WarpOptions(format='GTiff')  # Change format as required
    mosaic = gdal.Warp(output_path, data, options=options)
    mosaic = None 
    print("Mosaic created successfully at:", output_path)
    k = k+1
