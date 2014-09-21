'''
Downloads the zip file with the csv tables for BRFSS dataset provided by the VizRisk organizers:

http://www.hhsvizrisk.org/alldatasets-1/

@copyright: Fathom Information Design 2014
'''

import os, sys, zipfile, requests

def download_file(url, local_folder):
    local_filename = local_folder + '/' + url.split('/')[-1]
    print 'Attempting to open ' + url
    r = None
    for i in range(0, 5):
        try:
            r = requests.get(url)
            break; 
        except:
            r = None
            if i < 5 - 1: print "  Warning: Could not open " + url + ", will try again"
    if r == None:
        sys.stderr.write("Error: Failed opening " + url + " after 5 attempts\n")
        sys.exit(1)
    print 'Downloading ' + url + '...'
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    print 'Done.'      
    return 
    
def extract_zip(zip_file):
    print 'Unzipping ' + zip_file + '...'
    extract_folder = os.path.splitext(zip_file)[0]
    with zipfile.ZipFile(zip_file, 'r') as z:
        z.extractall(extract_folder)   
    print 'Done.'
    
base_url = 'https://github.com/mirador/brfss/releases/download/latest'
data_files = ['vizrisk.zip']

source_folder = 'source'
if not os.path.exists(source_folder):
    os.makedirs(source_folder)

for file in data_files:
    url = base_url + '/' + file
    download_file(url, source_folder)
    extract_zip(source_folder + '/' + file)
