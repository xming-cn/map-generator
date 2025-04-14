import uuid
from typing import Tuple, Literal, Optional
from dataclasses import dataclass
from enum import Enum

@dataclass
class Coordinate:
    x: int
    y: int
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))

class RoomType(Enum):
    START = 'start'
    BOSS = 'boss'
    BATTLE = 'battle'
    ELITES = 'elite'
    BLESSING = 'blessing'
    SHOP = 'shop'
    EVENT = 'event'
    REST = 'rest'
    PENDING = 'pending'
    
    def get_color(self) -> str:
        return {
            RoomType.START: '#00B25A',
            RoomType.BOSS: '#A10A0A',
            RoomType.BATTLE: '#E07A26',
            RoomType.ELITES: '#B10A8A',
            RoomType.BLESSING: '#FFD966',
            RoomType.SHOP: '#5A5AF0',
            RoomType.EVENT: '#3CC8D6',
            RoomType.REST: '#E057C4',
            RoomType.PENDING: '#A0A0A0',
        }[self]

@dataclass
class Room:
    """表示地图中的一个房间"""
    coordinate: Coordinate
    width: int
    height: int
    type: RoomType
    description: str = ''
    id: uuid.UUID = uuid.uuid4()
    
    def __hash__(self) -> int:
        return hash(self.id)

@dataclass
class Edge:
    """表示房间之间的连接"""
    v: Room
    vCoordinate: Coordinate
    
    w: Room
    wCoordinate: Coordinate
    
    def get_other(self, room: Room) -> Room:
        return self.w if room == self.v else self.v
    
    def get_either(self) -> Room:
        return self.v

    def contains(self, room: Room) -> bool:
        return room == self.v or room == self.w

    def get_room_coordinate(self, room: Room) -> Coordinate:
        return self.vCoordinate if room == self.v else self.wCoordinate
    
@dataclass
class Map:
    rooms: list[Room]
    edges: list[Edge]
    id: uuid.UUID = uuid.uuid4()
    start_room: Optional[Room] = None
    
    def __hash__(self) -> int:
        return hash(self.id)

    def get_room(self, coordinate: Coordinate) -> Optional[Room]:
        for room in self.rooms:
            if room.coordinate.x <= coordinate.x < room.coordinate.x + room.width and \
               room.coordinate.y <= coordinate.y < room.coordinate.y + room.height:
                return room
        return None

    def get_neighbors(self, room: Room) -> set[Room]:
        neighbors = set()
        for edge in self.edges:
            if edge.contains(room):
                neighbor = edge.get_other(room)
                neighbors.add(neighbor)
        return neighbors

@dataclass
class GeneratorConfig:
    room_count: int = 10
    mainroad_ratio: float = 0.5
    image_size: Tuple[int, int] = (800, 800)
    merge_ratio: float = 0.4
    further_merge_ratio: float = 0.7
    room_2x2_capacity: int = 1
    room_1x3_capacity: int = 1