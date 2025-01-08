import threading
import os
import shutil
# Third-party imports
import bpy

# Local application imports
from .exporter import Exporter
from .aw_api_tool import AWAPITool
from .api_key_manager import APIKeyManager
from .aa_panel import AW_PT_AAPanel
from .global_values import GlobalValues


class AAWindow(bpy.types.Operator):
    """
    This class represents a window for Animate Anything in Blender.
    """
    # The unique identifier for this action.
    bl_idname = "wm.send_model_to_api"
    bl_label = "Upload Model"
    bl_description = "Upload the selected model to Animate Anything"
    
    def execute(self, context):
        """
        Executes the main functionality of the addon.
        :param context: The context object containing information about the current Blender session.
        :type context: bpy.types.Context
        :return: A dictionary indicating the status of the execution.
        :rtype: dict
        """
        # Respect Blender's "Allow Online Access" 4.2:
        try:
            if not bpy.app.online_access:
                self.report({'ERROR'}, "Please enable online access in the preferences")
                AW_PT_AAPanel.message_handler("Please enable online access in the preferences, to do so go to Edit -> Preferences -> System -> Allow Online Access")
                return {'CANCELLED'}
        # Blender 4.00 and below
        except AttributeError:
            pass
        
        AW_PT_AAPanel.message_handler("Sending model...")
        active_obj = context.active_object
        wm = context.window_manager
        object_type = wm.my_addon_typeofObject
        api_key = APIKeyManager.get_api_key(self)
        author = context.scene.author
        improvements = context.scene.inproveAI
        early_access = context.scene.earlyAccess
        create_model = context.scene.author
        symmetry = context.scene.symmetry
        server_name = context.scene.my_addon_name
        
        # clean the temp folder
        temp_dir = bpy.app.tempdir
        # Iterate over each item in the temporary directory
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            try:
                # Check if the item is a file and delete it
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                # Check if the item is a directory and delete it along with its contents
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(e)
                
        if server_name == "":
            self.report({'ERROR'}, "Please enter the model name")
            AW_PT_AAPanel.message_handler("Please enter the model name")
            return {'CANCELLED'}
                    

        if active_obj is None:
            self.report({'ERROR'}, "Please select an object")
            AW_PT_AAPanel.message_handler("Please select an object")
            return {'CANCELLED'}

        # Store the size of the model
        GlobalValues.sent_model_size = active_obj.dimensions
        
        # if user not create model else use the user name
        if not create_model:
            if(context.scene.author_name == ""):
                self.report({'ERROR'}, "Please enter the author name")
                AW_PT_AAPanel.message_handler("Please enter the author name")
                return {'CANCELLED'}
        else:
            context.scene.author_name = os.getlogin()
            
        if not early_access:
            self.report({'ERROR'}, "Please check the early access box")
            AW_PT_AAPanel.message_handler("Please check the early access box")
            return {'CANCELLED'}
        
        # Check if the user has entered an API key
        api_key = APIKeyManager.get_api_key(bpy.types.RenderEngine)
      
        if api_key == "":
            self.report({'ERROR'}, "Missing API Key")
            AW_PT_AAPanel.message_handler("Missing API Key")
            return {'CANCELLED'}
        
        if not self.check_vertex_count():
            return {'CANCELLED'}
        
        print("Type of Object: " + object_type)
        if active_obj is not None:
            self.report({'INFO'}, "Selected Object: " + active_obj.name)

            self.report({'INFO'}, "convert to glb")
            model_path = bpy.app.tempdir
            
            exporter = Exporter()
            exporter.export_selected_object_and_children(model_path)
            # Start the asynchronous request
            threading.Thread(target=self.async_send_model, args=(
                api_key, model_path, active_obj.name ,server_name,symmetry,object_type,improvements,context.scene.author_name)).start()
        return {'FINISHED'}
    
    
    def check_vertex_count(self, threshold = 100000):
        """ 
        Check the vertex count of the selected object.
        :param threshold: The threshold for the vertex count.
        :type threshold: int
        """
        obj = bpy.context.object

        # Check if an object is selected
        if obj is None:
            self.report({'INFO'},"No object selected.")
            return False

        # Make sure the object is of mesh type
        if obj.type != 'MESH':
            self.report({'INFO'},f"The selected object '{obj.name}' is not a mesh.")
            AW_PT_AAPanel.message_handler(f"The selected object '{obj.name}' is not a mesh.")
            return False

        # Get the number of vertices
        vertex_count = len(obj.data.vertices)

        # Output result
        print(f"Object '{obj.name}' has {vertex_count} vertices.")
        
        if vertex_count > threshold:
            self.report({'INFO'},f"The object exceeds {threshold} vertices.")
            AW_PT_AAPanel.message_handler(f"The object exceeds {threshold} vertices.")
            return False
        
        return True
        
    
    def async_send_model(self, api_key, model_path, model_name ,server_name,symmetry, model_type,improvements,author):
        """
        Asynchronously sends a model to the API.
        :param api_key: The API key for authentication.
        :type api_key: str
        :param model_path: The path to the model file.
        :type model_path: str
        :param model_name: The name of the model.
        :type model_name: str
        :param model_type: The type of the model.
        :type model_type: str
        :param improvements: The improvements of the model.
        :type improvements: bool
        :param author: The author of the model.
        """
        print("Sending model...")
        response = AWAPITool.send_model_to_api(
            AWAPITool, api_key, model_path, model_name,server_name,symmetry, model_type,improvements,author)
        bpy.app.timers.register(
            lambda: AWAPITool.handle_sended_response(AWAPITool, response))
