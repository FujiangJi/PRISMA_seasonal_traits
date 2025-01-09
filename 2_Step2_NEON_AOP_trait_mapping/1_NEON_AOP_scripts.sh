#!/bin/bash
#SBATCH --job-name=JORN0909
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=32
#SBATCH --cpus-per-task=1
#SBATCH --mem=64gb
#SBATCH --time=48:00:00
#SBATCH --output=log_files/NEON_2021_D14_JORN_20210909_log.out

echo "Time begin: " $(date -u +%Y-%m-%d)','$(date +%H:%M:%S)
# Step 1: Set Environment.
echo "Step 1: Set Environment"
#####################################
ENVNAME=py365ht120
ENVDIR=$ENVNAME
export PATH=$(pwd)/pyenvs/$ENVDIR:$(pwd)/pyenvs/$ENVDIR/lib:$(pwd)/pyenvs/$ENVDIR/share:$PATH
. $(pwd)/pyenvs/$ENVDIR/bin/activate

# Step 2: Initial Processing Steps.
echo "Step 2: Initial Processing Steps"
#####################################
flightname=$1
data_folder="/mnt/cephfs/scratch/groups/chen_group/FujiangJi/NEON_AOP_trait_mapping/data/"
mkdir -p ${data_folder}${flightname}
image_folder=${data_folder}${flightname}

site=$(echo $flightname | cut -d'_' -f 4)
flightdate=$(echo $flightname | cut -d'_' -f 5)
year=$(echo $flightdate | cut -c1-4)
month=$(echo $flightdate | cut -c5-6)
date="${year}-${month}"

echo '    - Flight name: '$flightname
echo '    - Site: '$site
echo '    - Flight date: '$flightdate

mkdir -p ${image_folder}/coeffs/
mkdir -p ${image_folder}/imagery/
mkdir -p ${image_folder}/${flightname}_all
mkdir -p ${image_folder}/${flightname}_brdf
flightnamefolder=${flightname}_all
brdffolder=${flightname}_brdf

mkdir -p ${image_folder}/jsons/
mkdir -p ${image_folder}/traits/
mkdir -p ${image_folder}/trait_models/
cp $(pwd)/trait_models/trait_models.tar.gz "${image_folder}"
tar -xzf ${image_folder}/trait_models.tar.gz -C ${image_folder}/trait_models/ #Full Traits

shopt -s extglob
tr="Carotenoids_area_HT112.json|Chlorophylls_area_HT112.json|EWT_HT112.json|LMA_HT112.json|Nitrogen_HT112.json"
rm -rf ${image_folder}/trait_models/!($tr)
rm -rf ${image_folder}/trait_models.tar.gz

# Step 3: Data pull.
echo "Step 3: Data pull"
#####################################
python $(pwd)/data_pull.py $site $date $flightdate $image_folder $flightnamefolder

# Step 4: Topographic correction.
echo "Step 4: Topographic correction"
#####################################
python $(pwd)/image_correct_json_generate120_1.py $flightname $flightnamefolder $image_folder
python $(pwd)/image_correct120.py ${image_folder}/ic_config_$flightname.json
cp ${image_folder}/ic_config_$flightname.json ${image_folder}/ic1_config_$flightname.json
rm -rf ${image_folder}/ic_config_$flightname.json

mv ${image_folder}/${flightnamefolder}/* ${image_folder}/${brdffolder}/

# Step 5: BRDF correction.
echo "Step 5: BRDF correction"
#####################################
python $(pwd)/image_correct_json_generate120_2.py $flightname $brdffolder $image_folder
python $(pwd)/image_correct120.py ${image_folder}/ic_config_$flightname.json
cp ${image_folder}/ic_config_$flightname.json ${image_folder}/ic2_config_$flightname.json
rm -rf ${image_folder}/ic_config_$flightname.json
mv ${image_folder}/$brdffolder/* ${image_folder}/$flightnamefolder

# Step 6: Topo_BRDF_export corrected images.
echo "Step 6: Topo_BRDF_export corrected images"
#####################################
python $(pwd)/image_correct_json_generate120_3.py $flightname $flightnamefolder $image_folder
python $(pwd)/image_correct120.py ${image_folder}/ic_config_${flightname}_new.json 
cp ${image_folder}/ic_config_${flightname}_new.json ${image_folder}/ic3_config_$flightname.json
rm -rf ${image_folder}/ic_config_${flightname}_new.json

# Step 7: Trait prediction.
echo "Step 7: Trait prediction"
####################################
python $(pwd)/trait_estimate_json_generate.py $flightname $flightnamefolder $image_folder
python $(pwd)/trait_estimate.py ${image_folder}/trait_config_$flightname.json

# Step 8: Remove Files.
echo "Step 8: Remove Files"
####################################
mv ${image_folder}/coeffs/*.json ${image_folder}/jsons/
mv ${image_folder}/ic1_config_$flightname.json ${image_folder}/jsons/
mv ${image_folder}/ic2_config_$flightname.json ${image_folder}/jsons/
mv ${image_folder}/ic3_config_$flightname.json ${image_folder}/jsons/
mv ${image_folder}/trait_config_$flightname.json ${image_folder}/jsons/


rm -rf ${image_folder}/$brdffolder
rm -rf ${image_folder}/coeffs/
rm -rf ${image_folder}/trait_models/

tar -cvf ${data_folder}/${flightname}.tar ${image_folder}/
rm -rf ${image_folder}/

echo "Time end: " $(date -u +%Y-%m-%d)','$(date +%H:%M:%S)

exit