#!/bin/bash
#SBATCH --job-name=mosaic
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=64gb
#SBATCH --time=10:00:00
#SBATCH --output=mosaic_log/NEON_2020_D10_CPER_20200614_log.out

# Activate the conda environment
source /software/fji7/miniconda3/bin/activate /software/fji7/miniconda3/envs/Fujiang_envs

echo "Time begin: " $(date -u +%Y-%m-%d)','$(date +%H:%M:%S)

flightname=$1
data_folder="/mnt/cephfs/scratch/groups/chen_group/FujiangJi/NEON_AOP_trait_mapping/data/"
mkdir -p ${data_folder}mosaic_data/${flightname}/

tar -xvf ${data_folder}${flightname}.tar -C ${data_folder}
mv ${data_folder}${data_folder}${flightname} ${data_folder}

image_folder=${data_folder}${flightname}/
python $(pwd)/mosaic.py $flightname $image_folder $data_folder


rm -rf $image_folder
echo "Time end: " $(date -u +%Y-%m-%d)','$(date +%H:%M:%S)
exit