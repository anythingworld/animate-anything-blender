import bpy
import bpy.utils.previews
import os


class AddonUtils:
    # We can store multiple preview collections here,
    preview_collections = {}  # Declare the preview_collections variable

    @staticmethod
    def load_image_as_icon():
        pcoll = bpy.utils.previews.new()

        # path to the folder where the icon is
        # the path is calculated relative to this py file inside the addon folder
        my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")

        # load a preview thumbnail of a file and store in the previews collection
        pcoll.load("my_icon", os.path.join(my_icons_dir, "whiteGlobeico.png"), 'IMAGE')

        AddonUtils.preview_collections["main"] = pcoll  # Assign value to the class variable
        
   
        

