from dataclasses import dataclass, field
from collections import deque
from typing import Deque, List, Optional, Tuple

@dataclass
class TrackState:
    track_id:int
    class_name:str
    confidence:float
    bbox:Tuple[int,int,int,int]
    center:Tuple[float,float]
    previous_center:Tuple[float,float]
    velocity:float=0.0
    direction:str='NONE'
    motion_state:str='STATIONARY'
    age:int=1
    last_seen:float=0.0
    movement_distance:float=0.0
    history:Deque[Tuple[float,float]]=field(default_factory=lambda:deque(maxlen=30))
    interaction_person:Optional[int]=None
    interaction_state:str='NONE'
    pose:Optional[dict]=None
    foundation_pose:Optional[object]=None
    activity:str='IDLE'
