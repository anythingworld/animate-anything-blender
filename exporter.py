import os
import bpy

from .global_values import GlobalValues

class Exporter:
    """
    The Exporter class is responsible for exporting selected objects and their children to a GLB file.

    Methods:
    - select_object_and_children(obj): Recursively select an object and all its children.
    - export_selected_object_and_children(path): Export the selected object along with all its children to a GLB file.
    """

    def select_object_and_children(self, obj):
        """
        Recursively select an object and all its children.

        :param obj: The object to start selection from.
        :type obj: bpy.types.Object
        """
        obj.select_set(True)  # Select the current object
        for child in obj.children:  # Iterate over all children of the object
            self.select_object_and_children(child)  # Recursively select children

    def export_selected_object_and_children(self, path):
        """
        Export the selected object along with all its children to a GLB file.

        :param path: The path to the directory where the model file will be saved.
        :type path: str
        :return: True if the export is successful, False otherwise.
        :rtype: bool
        """
        # Get the list of selected objects
        selected_objects = bpy.context.selected_objects

        # Ensure at least one object is selected
        if not selected_objects:
            print("At least one object must be selected")
            return False

        # Deselect all objects to start clean
        bpy.ops.object.select_all(action='DESELECT')

        # Select the initially selected objects and their children
        for obj in selected_objects:
            self.select_object_and_children(obj)

        # Construct the file path using the name of the first selected object
        first_selected_object = selected_objects[0]
        file_path = os.path.join(path, first_selected_object.name)
        
        GlobalValues.size = first_selected_object.dimensions
        #Get the size of the largest object
        for obj in selected_objects:
            if obj.dimensions.z > GlobalValues.size.z:
                GlobalValues.size = obj.dimensions

        
        print("Size of the object: " + str(GlobalValues.size))
        # Export the selected objects and their children
        try:
            bpy.ops.export_scene.gltf(filepath=file_path, use_selection=True)
            print("Exported to: " + file_path)
        except Exception as e:
            print(e)
            print("Error exporting to: " + file_path)
            return False

        return True

    def __init__(self):
        pass

    