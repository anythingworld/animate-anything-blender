from urllib.parse import urlparse
import json
import os
import requests
import bpy

from .aa_panel import AW_PT_AAPanel 

class ModelDownloader:
    """
    A class for downloading 3D models and textures from URLs.
    """
    def __init__(self, data):
        self.data = data
       

    def download_file(self, url, filename, folder):
        """
        Download a file from a URL to an absolute path.
        :param url: The URL to download from.
        :param filename: The filename to save the file as.
        """
        temp_dir = bpy.app.tempdir
        abs_path = os.path.join(temp_dir, folder, filename)
        response = requests.get(url, timeout=10)
        #create a folder if it does not exist
        if not os.path.exists(os.path.join(temp_dir, folder)):
            os.makedirs(os.path.join(temp_dir, folder))
        #check if a file exists and change the name
        if os.path.exists(abs_path):
            abs_path = os.path.join(temp_dir, "new_" + filename)
            
        with open(abs_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded {abs_path}")
        AW_PT_AAPanel.message_handler("Downloaded " + os.path.splitext(os.path.basename(abs_path))[0])

   
    def find_generic_files(self, json_data, extension):
        """
        Recursively search for file paths in JSON data.
        :param json_data: Parsed JSON data (can be a list, dict, or other).
        :return: A list of file paths found in the JSON data.
        """
        files = []
       
        
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                files.extend(self.find_generic_files(value, extension))
        elif isinstance(json_data, list):
            for item in json_data:
                files.extend(self.find_generic_files(item, extension))
        elif isinstance(json_data, str):
            if json_data.__contains__(extension):
                files.append(json_data)

        return files
    def find_generic_urls(self, url_list, extension):
        """
        Find URLs that end with a specific extension.
        :param url_list: A list of URLs.
        :return: A list of URLs that end with a specific extension.
        """
        urls = []

        for url in url_list:
            parsed_url = urlparse(url)
            if parsed_url.path.endswith(extension):
                urls.append(url)

        return urls
    
    def get_clean_filename_from_url(self, url):
        """
        Extract and clean the filename from a URL.
        :param url: A URL string.
        :return: A clean filename.
        """
        # Split the URL by '/' and get the last part, which should be the filename with parameters
        filename_with_params = url.split('/')[-1]

        # Split by '?' to remove URL parameters
        clean_filename = filename_with_params.split('?')[0]

        # Replace URL encoded spaces ('%20') with regular spaces as an example
        clean_filename = clean_filename.replace('%20', ' ')

        # Additional cleaning can be done here as needed

        return clean_filename

    def parse_and_download(self,callback=None):
        """
        Parse the data to extract model and texture URLs and download them to an absolute path.
        This method expects 'data' to be a list.
        """
        # Check if data is a string and convert it to a list if necessary
        if isinstance(self.data, str):
            self.data = json.loads(self.data)
            
        # Extract specific parts of the data
        for item in self.data:
            original_model = item.get('original_model', {})
            preprocessed_model = item.get('preprocessed_model', {})
            parts = item.get('model', {}).get('parts', {})
            rig = item.get('model', {}).get('rig', {})
            texture = item.get('textures', {})
            material = preprocessed_model.get('material', {})
            #get the model files 
            AW_PT_AAPanel.message_handler("Downloading model files")

            self.get_all_files(original_model, "original_model")

            self.get_all_files(preprocessed_model, "preprocessed_model")
            #put the texture files in the preprocessed_model folder
            self.get_all_files(texture, "preprocessed_model")


            self.get_all_files(parts, "parts")
            #put the texture files in the parts folder
            self.get_all_files(texture, "parts")
            #put the material files in the parts folder
            self.get_all_files(material, "parts")
            #get the animation files
            self.get_all_files(rig, "animations")
            
        
            
            
            
                
    def get_all_files(self, model_data, folder):
            # Extract GLB file paths
            glb_file_paths = self.find_generic_files(model_data, '.glb')
            glbUrl = self.find_generic_urls(glb_file_paths, '.glb')

            for url in glbUrl:
                name = self.get_clean_filename_from_url(url)
                print("gbl url -> " + name)
                self.download_file(url, name,folder)
                
            #Extract FBX file paths
            #fbx_file_paths = self.find_generic_files(model_data, '.fbx')
            #fbxUrl = self.find_generic_urls(fbx_file_paths, '.fbx')
            #for url in fbxUrl:
                #name = self.get_clean_filename_from_url(url)
                #print("fbx url -> " + name)
                #self.download_file(url, name,folder)
                
            #Extract OBJ file paths
            obj_file_paths = self.find_generic_files(model_data, '.obj')
            objUrl = self.find_generic_urls(obj_file_paths, '.obj')
            for url in objUrl:
                name = self.get_clean_filename_from_url(url)
                print("obj url -> " + name)
                self.download_file(url, name,folder)
                
            #Extract MTL file paths
            mtl_file_paths = self.find_generic_files(model_data, '.mtl')
            mtlUrl = self.find_generic_urls(mtl_file_paths, '.mtl')
            for url in mtlUrl:
                name = self.get_clean_filename_from_url(url)
                print("mtl url -> " + name)
                self.download_file(url, name,folder)
                
            # Extract png file paths
            png_file_paths = self.find_generic_files(model_data, '.png')
            pngUrl = self.find_generic_urls(png_file_paths, '.png')
            for url in pngUrl:
                name = self.get_clean_filename_from_url(url)
                print("png url -> " + name)
                self.download_file(url, name,folder)
                
            # Extract jpg file paths
            jpg_file_paths = self.find_generic_files(model_data, '.jpg')
            jpgUrl = self.find_generic_urls(jpg_file_paths, '.jpg')
            for url in jpgUrl:
                name = self.get_clean_filename_from_url(url)
                print("jpg url -> " + name)
                self.download_file(url, name,folder)
                
            # Extract jpeg file paths
            jpeg_file_paths = self.find_generic_files(model_data, '.jpeg')
            jpegUrl = self.find_generic_urls(jpeg_file_paths, '.jpeg')
            for url in jpegUrl:
                name = self.get_clean_filename_from_url(url)
                print("jpeg url -> " + name)
                self.download_file(url, name,folder)
                
    