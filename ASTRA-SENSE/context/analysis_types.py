from dataclasses import dataclass, field
from typing import Any
@dataclass
class FrameAnalysisResult:
    camera_id:str; camera_name:str; timestamp:float; frame:Any
    persons:list=field(default_factory=list); objects:list=field(default_factory=list); interactions:list=field(default_factory=list); activities:list=field(default_factory=list); contexts:list=field(default_factory=list); events:list=field(default_factory=list); fps:float=0.0; system_status:dict=field(default_factory=dict)
