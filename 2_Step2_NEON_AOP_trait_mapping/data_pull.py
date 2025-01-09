import requests
import os
import sys

site = sys.argv[1]
date = sys.argv[2]
flightdate = sys.argv[3]
reflectance_id = 'DP1.30006.001'
home = sys.argv[4]
fdf = sys.argv[5]

product_request = requests.get('https://data.neonscience.org/api/v0/data/%s/%s/%s' % (reflectance_id,site,date)).json()
files= product_request['data']['files']

for file in files:
    if file['name'].endswith('h5') and flightdate in file['name']:
        print(file['name'])
		
        # Download image to disk
        url = file['url']
        local_filename = '%s/%s/%s' % (home,fdf,file['name'])
        with requests.get(url, stream=True) as r:
            print("Downloading %s" % file['name'])
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=int(1E8)):
                    f.write(chunk)