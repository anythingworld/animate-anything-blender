from enum import Enum, auto

class DefaultBehaviourType(Enum):
    ''' Enum for default behaviour types '''
    Static = auto()
    WalkingAnimal = auto()
    FlyingVehicle = auto()
    FlyingAnimal = auto()
    SwimmingAnimal = auto()
    WheeledVehicle = auto()
    Shader = auto()

class AATypeHanlder:
    ''' Class for handling the type of the object '''
    
    @staticmethod
    def parse_behaviour_type(json_full) -> DefaultBehaviourType:
        ''' Parse the behaviour type from the json 
        :param json_full: The json data
        :type json_full: dict
        :return: The behaviour type
        :rtype: DefaultBehaviourType
        '''
        
        for json_item in json_full:
            behaviour_type = DefaultBehaviourType.Static
            if 'model' in json_item and 'rig' in json_item['model'] and 'animations' in json_item['model']['rig'] and json_item['model']['rig']['animations']:
                behaviour_type = DefaultBehaviourType.WalkingAnimal

            behaviour = json_item.get('behaviour', {})

            item_type = json_item.get('type', {})

            if behaviour == "fly":
                if "vehicle" in item_type:
                    behaviour_type = DefaultBehaviourType.FlyingVehicle
                else:
                    behaviour_type = DefaultBehaviourType.FlyingAnimal
            elif "swim" in behaviour:
                if "vehicle" in item_type:
                    # The original code had a commented line here. Add logic if needed.
                    pass
                else:
                    behaviour_type = DefaultBehaviourType.SwimmingAnimal
            elif behaviour == "drive":
                behaviour_type = DefaultBehaviourType.WheeledVehicle
            elif type == "uniform":
                if behaviour == "static":
                    behaviour_type = DefaultBehaviourType.Static
                else:
                    behaviour_type = DefaultBehaviourType.Shader

        return behaviour_type

