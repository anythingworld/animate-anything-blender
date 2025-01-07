import json
import os
import threading
import time
import bpy
import requests

from .blender_model_importer import BlenderModelImporter
from .global_values import GlobalValues
from .model_downloader import ModelDownloader
from .aa_panel import AW_PT_AAPanel
from .api_key_manager import APIKeyManager
from .aa_type_handler import AATypeHanlder
from .aa_type_handler import DefaultBehaviourType

class AWAPITool:
    """
    This class is used to send and receive models from the server.
    It is used by the main thread and by the timer thread.
    """
    RECEIVE_URL = "https://api.anything.world/user-processed-model"
    SEND_URL = "https://api.anything.world/animate"
  

    def get_extension(self,filename: str) -> str:
        """
        Get the file extension from a given filename.
        :param filename: File name as a str
        :return: The file extension as a str
        """
        return filename.split(".")[-1].lower()

    def get_mimetype_by_extension(self, file_path: str) -> str:
        """
        Get mimetype by file extension.
        :param file_path: str, path to file
        :return: str, mimetype of file
        """
        extensions = {
            "mtl": "text/plain",
            "obj": "text/plain",
            "jpeg": "image/jpeg",
            "jpg": "image/jpg",
            "glb": "model/gltf-binary",
            "png": "image/png",
            "gif": "image/gif",
            "tga": "image/x-tga",
            "tif": "image/tiff",
            "tiff": "image/tiff",
            "bmp": "image/bmp",
            "gltf": "model/gltf+json",
            "fbx": "application/octet-stream",
            "bin": "application/octet-stream",
            "zip": "application/zip"
        }
        try:
            return extensions.get(self.get_extension(file_path))
        except IndexError:
            raise Exception(f"Could not get extension for file {file_path}")

    def get_mimetype(self, file_path: str, backend: str = "magic") -> str:
        """
        Get the mimetype of a file.
        :param file_path: str, path to file
        :return: str, mimetype of file
        """
        if backend == "magic":
            import magic
            mime = magic.Magic(mime=True)
            return mime.from_buffer(open(file_path, "rb").read(4096))
        return self.get_mimetype_by_extension(file_path)

    def read_files(self, files_dir: str) -> list:
        """
        Read files from a directory (or single file), returning a tuple with
        filename, full path to file and its mimetype (inferred by its
        extension-only for now).
        :param files_dir: str, path to asset directory (or single asset file)
        :return: list, files as tuples (file name, local path, mime type)
        """
        files_to_get = []
        if os.path.isdir(files_dir):
            files_to_get = os.listdir(files_dir)
        else:
            files_to_get = [files_dir]
        files = []
        for filename in files_to_get:
            if filename == files_dir:
                file_path = filename
            else:
                file_path = os.path.join(files_dir, filename)
            # Note: change here to use magic instead of extension if
            # possible to import magic module
            mimetype = self.get_mimetype(file_path, backend="extension")
            files.append((os.path.basename(file_path), file_path, mimetype))
        return files

    
    def create_form_data(self, files: list, key_value_data: dict) -> (bytes, str):
        """
        Manually create the multipart/form-data body for HTTP requests, encoding
        files and key-value pairs.
        :param files: list of tuples, each containing (filename, filepath, mimetype)
        :param key_value_data: dict, representing key-value pairs
        :return: tuple containing the form-data as bytes and the content type header
        """
        boundary = 'Boundary1234567890'
        lines = []

        for filename, filepath, mimetype in files:
            lines.append(f'--{boundary}'.encode('utf-8'))
            lines.append(f'Content-Disposition: form-data; name="files"; filename="{filename}"'.encode('utf-8'))
            lines.append(f'Content-Type: {mimetype}'.encode('utf-8'))
            lines.append(b'')  # Empty line must be in bytes
            with open(filepath, 'rb') as f:
                lines.append(f.read())  # File content is already in bytes

        for key, value in key_value_data.items():
            lines.append(f'--{boundary}'.encode('utf-8'))
            lines.append(f'Content-Disposition: form-data; name="{key}"'.encode('utf-8'))
            lines.append(b'')  # Empty line must be in bytes
            lines.append(str(value).encode('utf-8'))  # Ensure the value is in bytes

        # Final boundary
        lines.append(f'--{boundary}--'.encode('utf-8'))
        lines.append(b'')  # Empty line must be in bytes

        # Join all parts using b'\r\n' as the separator
        body = b'\r\n'.join(lines)

        content_type = f'multipart/form-data; boundary={boundary}'

        return body, content_type


    def send_model_to_api(self, api_key, model_path, model_name,server_name,symmetry, model_type,improvements,author, url = SEND_URL):
        """
        Send a model to the API.
        :param api_key: str, API key
        :param model_path: str, path to the model file
        :param model_name: str, name of the model
        :param model_type: str, type of the model
        :param url: str, API URL
        :return: Response from the API
        """
        print("Sending name..."+ model_name)

        # Ensure the file exists
        if not os.path.isfile(model_path+model_name+".glb"):
            return "Model file not found"

        data = {
            'key': api_key,
            'model_name': server_name,
            'model_type': model_type,
            'symmetry': symmetry,
            'can_use_for_internal_improvements': improvements, 
            'author': author, 
            'platform': 'blender', 
        }
        
        # Read the files from the directory
        files = AWAPITool().read_files(model_path+model_name+".glb")

        form_data, content_type = AWAPITool().create_form_data(files, data)
        try:
            
            response = requests.post(url, data=form_data, headers={'Content-Type': content_type}, timeout=10)
        except requests.RequestException as e:
            return f"Request failed: {e}"
        return response

    def getModelProcessed(self, api_key, model_id, url = RECEIVE_URL):
        """
        Get a processed model from the API.
        :param api_key: str, API key
        :param model_id: str, ID of the model
        :param url: str, API URL
        :return: Response from the API
        """
        data = {
            'key': api_key,
            'id': model_id,
        }
        response = requests.get(url, params=data, timeout=20)
        return response

    def handle_sended_response(self, response):
        """
        Handle the response after sending a model to the API.
        :param response: Response from the API
        """
        # if response is a string, it means there was an error
        if isinstance(response, str):
            # get the message from the response 
            
            AW_PT_AAPanel.message_handler("Oops! We need to select a model: " + response + "   Maybe you need to select one parent object instead of multiple objects. 🤔")

            return None

        if response.status_code == 200:
            AW_PT_AAPanel.message_handler("Woohoo! Your model was sent off successfully and is now being processed. 🚀")
            # get model id
            response_data = json.loads(response.text)
            model_id = response_data.get("model_id", None)
            GlobalValues.sendedModel_id = model_id
            wm = bpy.context.window_manager
            wm.my_last_model= model_id
            
            #delay to check if the model was processed 
            bpy.app.timers.register(
            lambda: AWAPITool.check_model_was_processed(self), first_interval=10.0)
            AW_PT_AAPanel.message_handler("Hang tight! We're now checking if your model has been processed. You'll be notified shortly. 🕒")

            AW_PT_AAPanel.loading = True

        else:
            show_response_error = False
            # Provide a more descriptive error message based on the response status code
            if response.status_code == 400:
                error_message = "There seems to be something off with the request format. Could you double-check it? 🤔"
            elif response.status_code == 403:
                error_message = "Hmm, looks like there's an issue Model Type. Let's make sure everything's in order! 🔑"
            elif response.status_code == 404:
                error_message = "We couldn't find what you were looking for. Might want to check that again! 🔍"
            elif response.status_code == 500:
                error_message = "Ah, seems like we've hit a snag on our side. Rest assured, we're looking into it! 🛠️"
            elif response.status_code == 429:
                error_message = "You have consumed your monthly model processing credits, so the model cannot be processed. To keep processing models, please consider acquiring new credits in https://app.anything.world/profile"
            else:
                error_message = "Something unexpected happened. Our team has been notified, and we're on it! 🚀"
                show_response_error = True
                
            if(show_response_error):
                AW_PT_AAPanel.message_handler("Uh-oh! " + error_message + "  " + response.text)
            else:
                AW_PT_AAPanel.message_handler("Uh-oh! " + error_message)

            
        return None  # Unregister the timer
    
    def check_model_was_processed(self):
        """
        Check if the model was processed by the API each 02 seconds.
        :param context: Blender context
        """

        api_key = APIKeyManager.get_api_key(bpy.types.RenderEngine)
        print("Checking if model was processed")
        if api_key and GlobalValues.sendedModel_id != "":
            AWAPITool.start_check_model_processed(self, api_key, GlobalValues.sendedModel_id)
        return None
    
    def start_check_model_processed(self, api_key, model_id):
        """
        Start a separate thread to check if the model has been processed.
        """
        threading.Thread(target=self.loop_check_model_was_processed, args=(self, api_key, model_id)).start()

    
    def loop_check_model_was_processed(self, api_key, model_id):
        """
        Check if the model was processed by the API, with retries and exponential backoff.
        """
        url = self.RECEIVE_URL
        max_retries = 100  # Maximum number of retries
        retry_delay = 5  # Delay between retries in seconds
        AW_PT_AAPanel.message_handler("Checking if model was processed.")
        AW_PT_AAPanel.loading = True
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params={'key': api_key, 'id': model_id}, timeout=10)
                if response.status_code == 200:
                    AW_PT_AAPanel.loading = False
                    AW_PT_AAPanel.message_handler("Great news! Your model is ready and has been processed successfully. 🎉")
                    threading.Thread(target=self.async_get_model, args=(
                        self,APIKeyManager.api_key, GlobalValues.sendedModel_id)).start()
                    break
                elif response.status_code == 403 and "ongoing" in response.text:
                    AW_PT_AAPanel.message_handler(f"Your model is still cooking! 🕒 Attempt {attempt + 1} of {max_retries}. We'll keep trying!")

                elif response.status_code == 400:
                    AW_PT_AAPanel.loading = False
                    AW_PT_AAPanel.message_handler("Oops! It looks like there was a little hiccup with the format of your request. 🤔 Please check and try again.")
                    break  # Stop retrying on incorrect format
                elif response.status_code == 404:
                    AW_PT_AAPanel.loading = False
                    AW_PT_AAPanel.message_handler("Hmm, we couldn't find your model. Could it be a mix-up in the ID? 🧐")

                    break  # Stop retrying on model not found
                elif response.status_code == 403:
                    AW_PT_AAPanel.loading = False
                    AW_PT_AAPanel.message_handler("Oops! It looks like there was a little hiccup, if the problem persists, please contact us. 🤔")
                    break  # Stop retrying on forbidden
                elif response.status_code == 429:
                    AW_PT_AAPanel.loading = False
                    AW_PT_AAPanel.message_handler("Too many requests: User has no more credits.  Please, visit the user's profile page to see current credits count and how to acquire more")
                    break  # Stop retrying on too many requests
                elif response.status_code == 500:
                    AW_PT_AAPanel.loading = False
                    AW_PT_AAPanel.message_handler("Yikes! Something went wonky on our end. 🛠️ We're on it, but feel free to reach out if you need immediate assistance.")
                    break
                else:
                    AW_PT_AAPanel.loading = False

                    AW_PT_AAPanel.message_handler("We ran into an unexpected issue. Please Contact out Team. Your patience is much appreciated! 🙏")
                    break  # Stop retrying on unexpected response
                print(response.text)
            except requests.RequestException:
                AW_PT_AAPanel.loading = False
                AW_PT_AAPanel.message_handler("We ran into an unexpected issue. Please Contact out Team. Your patience is much appreciated! 🙏")
                
            # if the attempt is not the last one, wait before trying again   
            time.sleep(retry_delay)

        # This is outside the for loop, so it runs after all attempts
        if attempt>=max_retries-1:
            AW_PT_AAPanel.message_handler("Your model is still cooking! 🕒 Please take a few minutes and click download.")

        AW_PT_AAPanel.loading = False
        return None  # Unregister the timer


    def async_get_model(self, api_key, model_id):
        """
        Asynchronously gets the model using the provided API key and model ID.
        :param api_key: The API key used to authenticate the request.
        :param model_id: The ID of the model to retrieve.
        """
        AW_PT_AAPanel.message_handler("Getting model...")
        response = AWAPITool.getModelProcessed(AWAPITool, api_key, model_id)
        bpy.app.timers.register(
            lambda: AWAPITool.handle_received_response(AWAPITool, response))     
        

    def handle_received_response(self, response):
        """
        Handle the response after receiving a model from the API.
        :param response: Response from the API
        """
        # if response is a string, it means there was an error
        if isinstance(response, str):
            AW_PT_AAPanel.message_handler("Failed to receive model: " + response)
            return None

        if response.status_code == 200:

            AW_PT_AAPanel.message_handler("Model received successfully: ")
            
            typeofthis = AATypeHanlder.parse_behaviour_type(response.json())
            
            print("Type of this model: " + str(typeofthis))
            
            downloader = ModelDownloader(response.json())
            importer = BlenderModelImporter()
            
            if typeofthis == DefaultBehaviourType.WalkingAnimal or typeofthis == DefaultBehaviourType.FlyingAnimal or typeofthis == DefaultBehaviourType.SwimmingAnimal:
                # Create an instance of the ModelDownloader and use it
                #in animated models we need to download in thread due to quantity of files
                threading.Thread(target=self.animated_routine, args=(self,importer,downloader,typeofthis)).start()
            
            elif typeofthis == DefaultBehaviourType.Static:
                # Create an instance of the ModelDownloader and use it
                AW_PT_AAPanel.message_handler("Downloading Static model...")
                downloader.parse_and_download()
                AW_PT_AAPanel.message_handler("Importing Static model...")
                importer = BlenderModelImporter()
                importer.import_models("preprocessed_model",typeofthis)
                AW_PT_AAPanel.message_handler("Static model imported successfully")
                
            elif typeofthis == DefaultBehaviourType.WheeledVehicle:
                # Create an instance of the ModelDownloader and use it
                AW_PT_AAPanel.message_handler("Downloading WheeledVehicle...")
                downloader.parse_and_download()
                AW_PT_AAPanel.message_handler("Importing WheeledVehicle...")
                importer.import_models("parts",typeofthis)
                AW_PT_AAPanel.message_handler("WheeledVehicle imported successfully")
            
            else:
                #dont know what to, better download all
                AW_PT_AAPanel.message_handler("Downloading model...")
                downloader.parse_and_download()
                AW_PT_AAPanel.message_handler("Importing model...")
                importer.import_models("preprocessed_model",typeofthis)
                importer.import_models("parts",typeofthis)
                importer.import_models("animations",typeofthis)
                importer.import_models("shader",typeofthis)
                importer.import_models("rig",typeofthis)
                AW_PT_AAPanel.message_handler("Model imported successfully")
            

        else:
            AW_PT_AAPanel.message_handler("Failed to receive model: " + response.text)
            
        return None  # Unregister the timer
    
    def animated_routine(self,importer,downloader,typeofthis):
        """
        Routine to animate the model.
        :param context: The context in which the operator is executed.
        :return: A dictionary indicating the status of the execution.
        """
        AW_PT_AAPanel.message_handler("Downloading Animal...")
        downloader.parse_and_download()
        AW_PT_AAPanel.message_handler("Importing Animal...")
        importer.import_models("animations",typeofthis)
        AW_PT_AAPanel.message_handler("Animation imported successfully")
        return {'FINISHED'}