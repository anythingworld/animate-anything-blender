import bpy
import webbrowser

class OpenURL(bpy.types.Operator):
    """Open Documentation"""
    bl_idname = "wm.open_url"
    bl_label = "Open URL"

    url: bpy.props.StringProperty()

    def execute(self, context):
        webbrowser.open(self.url)
        return {'FINISHED'}
