import bpy
import json
import re
import time
from os import system
from .addon_utils import AddonUtils
from .open_url import OpenURL
from .global_values import GlobalValues


class AW_PT_AAPanel(bpy.types.Panel):
    """
    This class represents the Animate Anything Panel in Blender.
    """
    bl_label = "Animate Anything Panel"
    bl_idname = "AW_PT_AAPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animate Anything"
    bl_context = "objectmode"
    
    loading_status = "Idle"
    old_loading_status = "Idle"
    code = ""
    icon = "ERROR"
    loading= False
    
    time_until_last_update = 0
    
    @staticmethod
    def message_handler(message):
        """
        Handles messages.
        :param message: The message to handle.
        :type message: str
        """
        # Regular expression pattern to match a JSON-like structure
        # This pattern assumes the JSON starts with either '{' or '[' and ends accordingly
        json_pattern = r'({.*?}|[.*?])'

        # Search for JSON-like string within the input
        match = re.search(json_pattern, message, re.DOTALL)
        #call report operator
        
        
        if match:
            # Extract the JSON string
            json_string = match.group()

            # Attempt to parse the JSON string
            try:
                # Convert the JSON string to a Python dictionary
                data = json.loads(json_string)

                # Check and process the JSON data
                if 'code' in data and 'message' in data:
                    print(f"Code: {data['code']}")
                    print(f"Message: {data['message']}")
                    AW_PT_AAPanel.code = f"{data['code']}"
                    AW_PT_AAPanel.loading_status = f"{data['message']}"
                    AW_PT_AAPanel.message_handler_popup(data['message'], data['code'],'INFO')
                else:
                    # The JSON data does not contain the expected fields
                    AW_PT_AAPanel.display_message(message)
                    AW_PT_AAPanel.message_handler_popup(message, "",'INFO')
            except (ValueError, json.JSONDecodeError):
               AW_PT_AAPanel.display_message(message)
               AW_PT_AAPanel.message_handler_popup(message, "",'INFO')
        else:
            # No JSON-like string was found
            AW_PT_AAPanel.display_message(message)
            AW_PT_AAPanel.message_handler_popup(message, "",'INFO')
        
        # if the time since the last update is greater than 1 second force the redraw
        current_time =  abs(AW_PT_AAPanel.time_until_last_update - time.monotonic())
        print(current_time)
        if current_time > 1:
        #redraw the window
            #bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            bpy.utils.unregister_class(AW_PT_AAPanel)
            bpy.utils.register_class(AW_PT_AAPanel)
       
            
    @staticmethod       
    def display_message(message):
        """
        Display the message in the Blender UI.
        :param context: The context in which the message is displayed.
        :type context: bpy.types.Context
        """
        AW_PT_AAPanel.code = "INFO"
        AW_PT_AAPanel.loading_status = message
        print(message)
        
    @staticmethod
    def message_handler_popup(message: str, title = "", icon = 'INFO', context=None):
        """
        Handles messages.
        :param message: The message to handle.
        :type message: str
        :param title: The title of the popup.
        :type title: str
        :param icon: The icon of the popup.
        :type icon: str
        :param context: The context in which the message is displayed.
        :type context: bpy.types.Context
        """
        #todo: add a popup
        #bpy.context.window_manager.popup_menu(AW_PT_AAPanel.draw_func, title="Info", icon='INFO')
        
        
    @staticmethod
    def register():
        """
        Register the panel and define the properties.
        """
        bpy.utils.register_class(OpenURL)
        bpy.types.Scene.temporary_api_key = bpy.props.StringProperty(name="Temporary API Key")
        bpy.types.Scene.symmetry = bpy.props.BoolProperty(name="My model is symmetric?", default=False, description="This switch grants the user the proper to use the model")
        bpy.types.Scene.author = bpy.props.BoolProperty(name="Did you create this model?", default=False, description="This switch grants the user the proper to use the model")
        bpy.types.Scene.author_name = bpy.props.StringProperty(name="", description="Enter the author of the model here", default= "")
        bpy.types.WindowManager.my_addon_typeofObject = bpy.props.StringProperty(
        name="Type",
        description="Enter the type of your object here",
        default="")
        bpy.types.Scene.my_addon_name = bpy.props.StringProperty(
        name="Name",
        description="Enter the name of your object here",
        default="")
        bpy.types.WindowManager.my_last_model = bpy.props.StringProperty(name="Last Model",description="Enter the last model here",default="")

        bpy.types.Scene.inproveAI = bpy.props.BoolProperty(name="Allow us to use this model", default=False, description="This switch grants the user the proper to use the model")
        bpy.types.Scene.earlyAccess = bpy.props.BoolProperty(name="I’ve checked and understood ", default=False, description="This switch grants the user the proper to use the model")

    @staticmethod
    def unregister():
        """
        Unregister the panel and delete the properties.
        """
        bpy.utils.unregister_class(OpenURL)
        del bpy.types.Scene.author
        del bpy.types.Scene.author_name
        del bpy.types.Scene.temporary_api_key
        del bpy.types.WindowManager.my_addon_typeofObject
        del bpy.types.WindowManager.my_last_model
        
        
    def wrap_text(self,text, width):
        # Split the text into words
        words = text.split(' ')
        # Initialize variables
        wrapped_lines = []
        current_line = ''

        # Iterate through the words
        for word in words:
            # If the current line is empty, add the word directly
            if not current_line:
                current_line = word
            # Otherwise, check if adding the next word with a space exceeds the width
            elif len(current_line) + len(word) + 1 <= width:
                # Add the word to the current line with a preceding space
                current_line += ' ' + word
            else:
                # Append the current line to the wrapped lines and start a new line with the current word
                wrapped_lines.append(current_line)
                current_line = word

        # Add the last line to the wrapped lines if it's not empty
        if current_line:
            wrapped_lines.append(current_line)

        return wrapped_lines
        
    def draw(self, context):
        """
        Draw the panel UI elements.
        """
        layout = self.layout
        wm = context.window_manager
        
        AW_PT_AAPanel.time_until_last_update = time.monotonic()
        
        # Get the preview collection (defined in register func)
        pcoll = AddonUtils.preview_collections["main"]
        my_icon = pcoll["my_icon"]
        box = layout.box()

        # Main Title
        box.label(text="ANIMATE ANYTHING", icon_value=my_icon.icon_id)
        # Subtitle
        box.label(text="        by Anything World")

        # Separator for visual spacing
        layout.separator()

        # Instructions
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text="Upload your own 3D model for AI-driven rigging and animation:")
        layout.separator()
       
        # Use split layout to create two columns
        split = layout.split(factor=0.5)  # Adjust the factor to change the width ratio of the columns

        col1 = split.column()
        # Model Sending Section
        col1.separator()
        col1.label(text="Model Info")
        col1.label(text="Choose a name for your model")
        box = col1.box()
        if bpy.context.active_object is not None:
            #box.label(text= bpy.context.active_object.name)
            box.prop(context.scene, "my_addon_name", text="")
        else:
            box.label(text="No model selected")
        # Object Type Selection
        col1.separator()
        col1.label(text="Model Type")
        col1.label(text="(e.g. woman, man, dog, cat, ant, tree)")
        col1.label(text="This will help us to classify your model in the next step")
        col1.prop(wm, "my_addon_typeofObject", text="")
        
        # Mesh
        col1.separator()
        col1.label(text="Mesh")
        col1.label(text="This will help us to select the mesh asset from your ")
        col1.label(text="project files. If you don’t have the model in Blender,")
        col1.label(text="import it there first. Ensure that textures are visible")
        col1.label(text=" within Blender, if your model has them.")
        
        col1.separator()
        col1.label(text="Model Selected: ")
        box = col1.box()
        if bpy.context.active_object is not None:
            box.label(text=bpy.context.active_object.name)
        else:
            box.label(text="No model selected")
            
        #symmetry 
        col1.separator()
        col1.label(text="Symmetry")
        col1.prop(context.scene, "symmetry")

        # Author
        col1.separator()
        col1.label(text="Model Author")
        col1.prop(context.scene, "author")
        col1.label(text="Please credit the author below. We cannot process")
        col1.label(text="your model without this information.")
        col1.prop(context.scene, "author_name")
        
        col2 = split.column(align=True)
        col2.separator()
        box2 = col2.box()
        box2.scale_y  = 0.7
        
        box2.label(text="Important:", icon='ERROR')
        box2.label(text="Your model must be correctly rotated to get")
        box2.label(text="proper results. The model should be")
        box2.label(text="facing -Y axis, with the vertical axis being +Z")
        box2.label(text="and side axis being X.")
        box2.operator("wm.open_url", text="Click here for more information").url = "https://anything-world.gitbook.io/anything-world/api/preparing-your-3d-model"
        
        col2.separator()
        box3 = col2.box()
        box3.prop(context.scene, "inproveAI")
        box3.scale_y  = 0.7
        box3.label(text="to improve our AI system.")
        box3.prop(context.scene, "earlyAccess")
        box3.label(text="the model processing constraints of ")
        box3.label(text="the current early access version.")
        box3.label(text="My model belongs to a category ")
        box3.label(text="which is already available.")
        box3.operator("wm.open_url", text="Click here for more information").url = "https://app.anything.world/animation-rigging/system-constraints"

        # Last Model Download Section
        col2.separator()
        col2.operator("wm.send_model_to_api", text="Upload", icon='EXPORT')
        col2.separator()
        
        # Loading Status Section
        col2.separator()
        box4 = col2.box()
        
        # Inside your if block where you check for message change
        if self.loading_status != self.old_loading_status:
            box4.label(text=self.code, icon='RADIOBUT_ON')
            self.old_loading_status = self.loading_status

            # Wrap the text based on the desired width
            wrapped_text = self.wrap_text(self.loading_status, 50)  # Assuming 50 is the max width

            # Display each line in the wrapped text
            for line in wrapped_text:
                box4.label(text=line)
            
                #box4.statusbar() TODO: add status bar
            
        col2.label(text="Download Model:")
        col2.prop(wm, "my_last_model", text="Model ID")
        if wm.my_last_model != "" and not self.loading:
            # get the scale of current selected object
            if bpy.context.active_object is not None:
                GlobalValues.sent_model_size = bpy.context.active_object.dimensions
            col2.operator("wm.getlastmodel", text="Download", icon='IMPORT')

    