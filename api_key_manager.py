import urllib.request
import bpy
import os

from pathlib import Path

# Local application imports
from .global_values import GlobalValues
from .aa_panel import AW_PT_AAPanel

class APIKeyManager(bpy.types.Operator):
    """
    This class represents an API key manager for updating, setting, and retrieving API keys.
    """
    bl_idname = "wm.update_api_key"
    bl_label = "Update API Key"
    api_key = ""
    VALIDATION_URL = "https://api.anything.world"

    def execute(self, context):
        """
        Executes the operator to update the API key, call server validation, and return the result.
        """
        key = APIKeyManager.read_key_from_file(self)
        if key:
            APIKeyManager.api_key = key
        
        AW_PT_AAPanel.message_handler( "API Key updated")
        self.validate_api_key()
        return {'FINISHED'}

    def set_api_key(self, api_key):
        """
        Sets the API key.
        :param api_key: The API key to set.
        """
        APIKeyManager.api_key = api_key

    def get_api_key(self):
        """
        Retrieves the API key.
        :returns str -- The API key if it is valid, or 'CANCELLED' if it is invalid.
        """
        if APIKeyManager.api_key == "":
            key = APIKeyManager.read_key_from_file(self)
            if key:
                APIKeyManager.api_key = key
                if APIKeyManager.validate_api_key(self):
                    return APIKeyManager.api_key
                else:
                    return {'CANCELLED'}
        else:
            return APIKeyManager.api_key

    def validate_api_key(self):
        """
        Calls the server to validate the API key.
        :returns dict: The result of the server validation.
        """
        if (APIKeyManager.api_key == ""):
            AW_PT_AAPanel.message_handler( "Missing API Key")
            return {'CANCELLED'}
        try:
            validation_url = APIKeyManager.VALIDATION_URL + "/has-valid-key?" + f"key={urllib.parse.quote(APIKeyManager.api_key)}"
            with urllib.request.urlopen(validation_url) as response:
                if response.getcode() == 200:
                    #AW_PT_AAPanel.message_handler( "Valid API Key")
                    return {'FINISHED'}
                AW_PT_AAPanel.message_handler( "Invalid API Key")
                return {'CANCELLED'}
        except urllib.error.HTTPError as e:
            if e.code == 403:
                AW_PT_AAPanel.message_handler( "Invalid or Missing API Key")
            elif e.code == 429:
                AW_PT_AAPanel.message_handler( "You have consumed your monthly model processing credits, so the model cannot be processed. To keep processing models, please consider acquiring new credits in https://app.anything.world/profile")
            elif e.code == 500:
                AW_PT_AAPanel.message_handler( "Server Error")
            else:
                AW_PT_AAPanel.message_handler( "HTTP Error: " + str(e))
            return {'CANCELLED'}
        except urllib.error.URLError as e:
            AW_PT_AAPanel.message_handler( "Request Failed: " + str(e))
            return {'CANCELLED'}
    
    def read_key_from_file(self):
        """
        Reads the API key from a file.
        :return str: The API key read from the file, or an empty string if the file is not found or an error occurs.
        """
        temp_dir = Path(os.path.dirname(bpy.app.tempdir))
        dir_up = os.fspath(Path(temp_dir.parent).resolve())
        
        folder = os.path.join(dir_up, "api_key.txt")
        try:
            with open(folder, "r", encoding="utf-8") as file:
                # Removes any leading/trailing whitespace
                key = file.read().strip() 
            return key
        except FileNotFoundError:
            AW_PT_AAPanel.message_handler("Key file not found.")
            return ""
        except Exception as e:
            AW_PT_AAPanel.message_handler(f"An error occurred: {e}")
            return ""