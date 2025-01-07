"""
MIT License
Copyright (c) 2024 Anything World
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
# Standard library imports
import threading
import urllib.request
import os

# Third-party imports
import bpy
from bpy.types import Operator, AddonPreferences


# Local application imports
from .aa_core import AAWindow
from .aa_panel import AW_PT_AAPanel
from .exporter import Exporter
from .global_values import GlobalValues
from .aw_api_tool import AWAPITool
from .model_return import ModelReturn
from .api_key_manager import APIKeyManager
from .addon_utils import AddonUtils
from pathlib import Path

# Information required to register the addon in Blender.
bl_info = {
    "name": "Animate Anything Window",
    "author": "Anything World",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "description": "Opens a Animate Anything in Blender",
    "category": "AI Tool",
}

class KeyPreferences(bpy.types.AddonPreferences):
    """
    This class represents the preferences for the add-on.
    """
    bl_idname = __name__

    api_key: bpy.props.StringProperty(
        name="API Key",
        description="Enter your API key here",
        default="",
        subtype='PASSWORD',  # Use 'TEXT' to don't hide the key
        update=lambda self, context: self.save_api_key()  # Add update callback

    )
    def save_api_key(self):
        """
        Saves the API key to a file.
        """
        if len(self.api_key) < 5:
            AW_PT_AAPanel.message_handler("API Key is too short")
            return
        APIKeyManager.api_key = self.api_key
        if  APIKeyManager.validate_api_key(APIKeyManager) != {'FINISHED'}:
                AW_PT_AAPanel.message_handler("Invalid API Key!")
                return
    
        try:
            temp_dir = Path(os.path.dirname(bpy.app.tempdir))
            dir_up = os.fspath(Path(temp_dir.parent).resolve())
            folder = os.path.join(dir_up, "api_key.txt")
            file_path = os.path.join(folder)
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.api_key)
                AW_PT_AAPanel.message_handler("Created API Key file and saved")
            else:
                # clean file and write new key
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.api_key)
                AW_PT_AAPanel.message_handler("Saved API Key")
        except Exception as e:
            AW_PT_AAPanel.message_handler("Error saving API Key: " + str(e))

    def draw(self, context):
        """
        Draw method for the addon's UI panel.
        :param context: The current context.
        """
        layout = self.layout
        layout.prop(self, "api_key")

def register():
    """
    Register the necessary classes and properties for the addon.
    """
    bpy.utils.register_class(AAWindow)
    AddonUtils.load_image_as_icon()
    bpy.utils.register_class(AW_PT_AAPanel)
    bpy.utils.register_class(APIKeyManager)
    bpy.utils.register_class(KeyPreferences)
    bpy.utils.register_class(ModelReturn)
    
    prefs = bpy.context.preferences.addons[__package__].preferences
    APIKeyManager.set_api_key(APIKeyManager, prefs.api_key)
    
def unregister():
    """
    Unregisters the addon by removing the necessary classes and properties.
    """
    bpy.utils.unregister_class(AAWindow)
    bpy.utils.unregister_class(AW_PT_AAPanel)
    bpy.utils.unregister_class(APIKeyManager)
    bpy.utils.unregister_class(KeyPreferences)
    bpy.utils.unregister_class(ModelReturn)

if __name__ == "__main__":
    register()
