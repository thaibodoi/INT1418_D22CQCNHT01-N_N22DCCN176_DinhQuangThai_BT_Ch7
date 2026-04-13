from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional

@dataclass
class Object:
    id: str
    type: str
    name: str
    props: Dict[str, str]

@dataclass
class Activity:
    name: str
    props: Dict[str, str]

@dataclass
class Segment:
    video_id: str
    video_name: str
    start: int
    end: int
    objects: List[Object]
    activities: List[Activity]

@dataclass
class RSTreeNode:
    start: int
    end: int
    segments: List[Segment]
    object_types: Set[str] = field(default_factory=set)
    activity_names: Set[str] = field(default_factory=set)
    is_leaf: bool = False
    left: Optional['RSTreeNode'] = None
    right: Optional['RSTreeNode'] = None
