import os
import bpy
import functools
from .aa_type_handler import DefaultBehaviourType
from .aa_panel import AW_PT_AAPanel
from .global_values import GlobalValues
from mathutils import Vector
class BlenderModelImporter:
    """
    A class for importing 3D models into Blender and applying textures.
    """
    model_imported = False
    first_rig = None
    offset_increment = 5
    offset_x = 0.0
    offset_y = 0.0
    current_index = 0 
    first_scale = -1
    def __init__(self):
        self.model_imported = False
        self.offset_x = 0.0
        self.offset_y = 0.0
        pass
        
    def get_or_create_collection(self, collection_name):
        """
        Get an existing collection by name or create a new one if it doesn't exist.
        """
        if collection_name in bpy.data.collections:  # Check if the collection already exists
            return bpy.data.collections[collection_name]
        else:
            new_collection = bpy.data.collections.new(name=collection_name)
            bpy.context.scene.collection.children.link(new_collection)
            return new_collection
        
    def import_models(self, folder, def_type:DefaultBehaviourType):
        """
        Import all 3D models in the specified folder and apply textures.
        """
        collection = self.get_or_create_collection("Collection")
        folder = os.path.join(bpy.app.tempdir, folder)
        #import all the textures in the folder
        texture_files = [f for f in os.listdir(
            folder) if f.endswith('.png') or f.endswith('.jpg')or f.endswith('.jpeg')]
        for texture_file in texture_files:
            texture_filepath = os.path.join(folder, texture_file)
            bpy.ops.image.open(filepath=texture_filepath)
            
        # Get all model files in the folder
        model_files = [f for f in os.listdir(
           folder) if f.endswith('.glb') or f.endswith('.obj')]
        if def_type == DefaultBehaviourType.WalkingAnimal or def_type == DefaultBehaviourType.FlyingAnimal:
           self.import_animated_model(folder,model_files)
            
        elif def_type == DefaultBehaviourType.WheeledVehicle or def_type == DefaultBehaviourType.FlyingVehicle:
            #create a colelction for the models
            models_collection = self.get_or_create_collection("Vehicle")
            # Import each model
            body = None
            for model_file in model_files:
                #check if the model is named body and import it
                if "body" in model_file:
                    model_filepath = os.path.join(folder, model_file)
                    body = self.import_model(model_filepath)
                    # Move the imported model to the models collection
                    if body is not None:
                        models_collection.objects.link(body)
                        bpy.context.active_object.select_set(False)
                        try :
                            collection.objects.unlink(body)
                        except:
                            pass              
            for model_file in model_files:
                #put every other model in the collection as child of the body
                if "body" not in model_file:
                    model_filepath = os.path.join(folder, model_file)
                    model = self.import_model(model_filepath)
                    # Move the imported model to the models collection
                    if model is not None:
                        models_collection.objects.link(model)
                        bpy.context.active_object.select_set(False)
                        try :
                            collection.objects.unlink(model)
                        except:
                            pass
                        #model.parent = body
                        #model.matrix_parent_inverse = body.matrix_world.inverted()
                        bpy.ops.object.select_all(action='DESELECT') # deselect all object
                        model.select_set(True)
                        body.select_set(True)     # select the object for the 'parenting'
                        bpy.context.view_layer.objects.active = body    # the active object will be the parent of all selected object
                        bpy.ops.object.parent_set()
            #reselect the body
            body.select_set(True)
            bpy.context.view_layer.objects.active = body
            #scale the model to ajust to the blender metric scale
            scale_factor = self.calculate_dimension_difference(body)*3.5
            body.scale *= scale_factor
            
            
                        
                        
        elif def_type == DefaultBehaviourType.Static:
            #create a colelction for the models
            models_collection = self.get_or_create_collection("Imported Models")
            for model_file in model_files:
                model_filepath = os.path.join(folder, model_file)
                model = self.import_model(model_filepath)
                # Move the imported model to the models collection
                if model is not None:
                    models_collection.objects.link(model)
                    bpy.context.active_object.select_set(False)
                    try :
                        collection.objects.unlink(model)
                    except:
                        pass
                    
            #scale the model to ajust to the blender metric scale
            for model in models_collection.objects:
                scale_factor = self.calculate_dimension_difference(body)
                model.scale *= scale_factor
                
    def import_model(self, model_filepath, max_dimension=10):
        """
        Import a 3D model into Blender, and check model size and name.
        
        :param model_filepath: File path to the 3D model.
        :param max_dimension: Maximum allowed dimension for the model.
        """
        old_objs = set(bpy.data.objects)
        AW_PT_AAPanel.message_handler("Importing model " + os.path.splitext(os.path.basename(model_filepath))[0])
        # Import the model based on its file extension
        if model_filepath.endswith('.glb'):
            bpy.ops.import_scene.gltf(filepath=model_filepath,bone_heuristic='TEMPERANCE')
        elif model_filepath.endswith('.obj'):
            bpy.ops.wm.obj_import(filepath=model_filepath)
        elif model_filepath.endswith('.fbx'):
            bpy.ops.import_scene.fbx(filepath=model_filepath)
        else:
            raise ValueError("Unsupported model format: {}".format(model_filepath))
        # Get the base name of the file without the extension
        base_name = os.path.splitext(os.path.basename(model_filepath))[0]
        imported_object = (set(bpy.data.objects) - old_objs).pop()
        
        # Check if the imported object's name contains the base name of the file
        if base_name not in imported_object.name:
            #print(f"Warning: The imported object's name '{imported_object.name}' does not contain the expected base name '{base_name}'.")
            imported_object.name = base_name
        # Check the dimensions of the imported object
        dimensions = imported_object.dimensions
        if any(dim > max_dimension for dim in dimensions):
            print(f"Warning: The imported model is too big. Dimensions: {dimensions}, Max allowed: {max_dimension}")
        
        return imported_object
    # Function to move an object and its children to a specified collection
    def move_to_collection(self, obj, collection):
        # Move the object to the target collection
        if obj.name not in collection.objects:
            # Link object to the target collection
            collection.objects.link(obj)
        
        # Unlink the object from its current collections
        for col in obj.users_collection:
            if col != collection:
                col.objects.unlink(obj)
        # Recursively move the children
        for child in obj.children:
            self.move_to_collection(child, collection)
            
    def import_animated_model(self,folder,model_files):
        """
        Import a 3D model into Blender and apply animations.
        
        :param model_filepath: File path to the 3D model.
        """
        #create a colelction for the models
        models_collection = self.get_or_create_collection("Animated Models")
            
        # Import each model              
        bpy.app.timers.register(functools.partial(self.import_next_model, model_files, folder, models_collection))
                 
    def import_next_model(self,model_files,folder,models_collection):
        if self.current_index >= len(model_files):
            return None  # Stop the timer when all models are processed
        model_file = model_files[self.current_index]
        if "_" in model_file:  # Process only if the model file is designated as an animation
            model_filepath = os.path.join(folder, model_file)
            self.import_model(model_filepath)
            model = bpy.context.active_object
            #check if model has an animation
            if model.animation_data is None:
                #delete the model if it does not have an animation
                bpy.ops.object.delete()
                self.current_index += 1  # Prepare for the next model
                return 1  # Call this function again after 1 seconds
                
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
            empty = bpy.context.active_object
            empty.name = os.path.splitext(model_file)[0]
            model.select_set(True)
            bpy.context.view_layer.objects.active = empty
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            self.move_to_collection(empty, models_collection)
            empty.location.x = self.offset_x
            empty.location.y = self.offset_y
            # Move the empty to the right of the model by half of the model's x dimension         
            self.offset_x += (model.dimensions.x * 0.5)
            print("stored dimensions: " + str(GlobalValues.sent_model_size))
            
            if self.first_scale < 0:
                print("in a first model calculate the scale factor")
                # If have no scale stored use the default cube size
                if(GlobalValues.sent_model_size.length < 0.1):
                    print("No stored dimensions")
                    GlobalValues.sent_model_size = Vector((2, 2, 2))
                target_dim=GlobalValues.sent_model_size
                current_dim = model.dimensions
                
                #keep the dimension aways positive and in the outside a vector to avoid inverted dimensions
                current_dim_x = abs(current_dim.x)
                current_dim_y = abs(current_dim.y)
                current_dim_z = abs(current_dim.z)
                print("Target dimensions: " + str(target_dim))
                print("Current dimensions: " + str(current_dim))
                print("Current dimensionsnorm: " + str(current_dim_x) + " " + str(current_dim_y) + " " + str(current_dim_z))
                
                #get the largest dimension of target
                if target_dim.z > target_dim.x and target_dim.z > target_dim.y:
                    target_dim_out = target_dim.z
                elif target_dim.x > target_dim.y:
                    target_dim_out = target_dim.x
                else:
                    target_dim_out = target_dim.y
                #get the largest dimension of the model
                if current_dim_z > current_dim_x and current_dim_z > current_dim_y:
                    current_dim_out = current_dim_z
                elif current_dim_x > current_dim_y:
                    current_dim_out = current_dim_x
                else:
                    current_dim_out = current_dim_y
                    
                # Dynamically calculate scale factors with an adjustable scaling multiplier.
                scale_factors = target_dim_out / current_dim_out
                print("Scale factor: " + str(scale_factors))
                # Apply these scale factors to the object's scale
                empty.scale.x *= scale_factors
                empty.scale.y *= scale_factors
                empty.scale.z *= scale_factors
                
                self.first_scale = scale_factors
            else:
                print("using stored scale factor"+str(self.first_scale))
                # Apply the first scale to the object's scale
                empty.scale.x *= self.first_scale
                empty.scale.y *= self.first_scale
                empty.scale.z *= self.first_scale
                
            #if location y is bigger than 200 move to the next row
            if self.offset_x > 100:
                self.offset_x = 0
                self.offset_y += model.dimensions.y + self.offset_increment
                empty.location.y = self.offset_y
        self.current_index += 1  # Prepare for the next model
        return 0.2  # Call this function again after 0.2 seconds
    
    def calculate_dimension_difference(self,model):
        """Calculate the scale factor needed to adjust the model to the blender metric scale
            :param model: The model to scale.
            :type model: bpy.types.Object
            :return: The scale factor needed to adjust the model to the blender metric scale.
        """
        if GlobalValues.firstScale < 0:
            # If have no scale stored, use the model dimensions
            if(GlobalValues.sent_model_size.length < 0.1):
                GlobalValues.sent_model_size = model.dimensions * 0.1
            target_dim=GlobalValues.sent_model_size
            current_dim = model.dimensions
            print("Target dimensions: " + str(target_dim))
            print("Current dimensions: " + str(current_dim))
            # Calculate scale factors needed for each dimension
            scale_factors = [target_dim / current_dim if current_dim != 0 else 0
                                for target_dim, current_dim in zip(target_dim, current_dim)]
            GlobalValues.firstScale = scale_factors[2]
            print("Scale factor: " + str(scale_factors[2]))
            return scale_factors[2]
        else:
            return GlobalValues.firstScale
