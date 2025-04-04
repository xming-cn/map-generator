import uuid
from typing import Tuple, Literal
from dataclasses import dataclass

@dataclass
class Room:
    """表示地图中的一个房间"""
    topLeft: Tuple[int, int]
    size: Tuple[int, int]
    color: str
    description: str = ''
    id: uuid.UUID = uuid.uuid4()
    
    def __hash__(self) -> int:
        return hash(self.id)

@dataclass
class Edge:
    """表示房间之间的连接"""
    start: Tuple[int, int]
    direction: Literal['Horizontal', 'Vertical'] 