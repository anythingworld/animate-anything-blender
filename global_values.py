import mathutils

# static class to store global values
class GlobalValues:
    """
    A class to store global values used in the application.

    Attributes:
        sendedModel_id (str): The ID of the sent model.
    """
    sendedModel_id = ""
    sent_model_size = mathutils.Vector((0,0,0))
