from dataclasses import dataclass
@dataclass
class InteractionState:
    person_id:int
    object_id:int
    state:str='NONE'
    duration:float=0.0
    first_seen:float=0.0
    last_seen:float=0.0
    score:float=0.0
    previous_distance:float=0.0
