import threading
import bpy
import os
import shutil
# Local application imports
from .global_values import GlobalValues
from .aw_api_tool import AWAPITool
from .api_key_manager import APIKeyManager

class ModelReturn(bpy.types.Operator):
    """
    Operator to get the last model using an API key and model ID.
    """

    bl_idname = "wm.getlastmodel"
    bl_label = "Get Last Model"

    def async_get_model(self, api_key, model_id):
        """
        Asynchronously gets the model using the provided API key and model ID.
        :param api_key: The API key used to authenticate the request.
        :param model_id: The ID of the model to retrieve.
        """
        response = AWAPITool.getModelProcessed(AWAPITool, api_key, model_id)
        bpy.app.timers.register(
            lambda: AWAPITool.handle_received_response(AWAPITool, response))
        #threading.Thread(target=AWAPITool.handle_received_response, args=(AWAPITool, response)).start()

    def execute(self, context):
        """
        Executes the operator to get the last model.
        :param context: The context in which the operator is executed.
        :return: A dictionary indicating the status of the execution.
        """
        
        #clean the temp folder
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
                    
        wm = context.window_manager
        api_key = APIKeyManager.get_api_key(bpy.types.RenderEngine)
        if APIKeyManager.api_key == "":
            self.report({'ERROR'}, "Missing API Key")
            return {'CANCELLED'}
        if wm.my_last_model != "":
            print("Getting last model from window" + wm.my_last_model)
            GlobalValues.sendedModel_id = wm.my_last_model

        if GlobalValues.sendedModel_id == "":
            self.report({'ERROR'}, "Missing Model ID")
            return {'CANCELLED'}

        print("Getting last model" + GlobalValues.sendedModel_id)
        threading.Thread(target=self.async_get_model, args=(
           api_key, GlobalValues.sendedModel_id)).start()
        return {'FINISHED'}
