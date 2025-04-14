import uuid
from typing import Tuple, Literal, Optional
from dataclasses import dataclass
from enum import Enum
import random

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
    
    def __post_init__(self) -> None:
        self.id = uuid.uuid4()
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def get_other(self, room: Room) -> Room:
        return self.w if room == self.v else self.v
    
    def get_either(self) -> Room:
        return self.v

    def contains(self, room: Room) -> bool:
        return room == self.v or room == self.w

    def get_room_coordinate(self, room: Room) -> Coordinate:
        return self.vCoordinate if room == self.v else self.wCoordinate


class Map:
    def __init__(self):
        self.id: uuid.UUID = uuid.uuid4()
        
        self.__rooms: list[Room] = []
        self.__edges: list[Edge] = []
        
        self.start_room: Optional[Room] = None
        self._neighbor_map: dict[Room, set[Edge]] = {}

    @property
    def V(self) -> int: 
        return len(self.__rooms)
    
    @property
    def E(self) -> int:
        return len(self.__edges)

    def __hash__(self) -> int:
        return hash(self.id)

    def get_index_room(self, index: int) -> Optional[Room]:
        if 0 <= index < len(self.__rooms):
            return self.__rooms[index]
        return None

    def get_room(self, coordinate: Coordinate) -> Optional[Room]:
        for room in self.__rooms:
            if room.coordinate.x <= coordinate.x < room.coordinate.x + room.width and \
               room.coordinate.y <= coordinate.y < room.coordinate.y + room.height:
                return room
        return None

    def get_random_room(self) -> Optional[Room]:
        if self.__rooms:
            return random.choice(self.__rooms)
        return None

    def get_neighbors(self, room: Room) -> set[Edge]:
        return self._neighbor_map.get(room, set())

    def add_room(self, room: Room) -> None:
        if room not in self.__rooms:
            self.__rooms.append(room)
            self._neighbor_map[room] = set()

    def delete_room(self, room: Room) -> None:
        if room in self.__rooms:
            self.__rooms.remove(room)
            self._neighbor_map.pop(room, None)
            # Remove edges connected to the room
            self.__edges = [edge for edge in self.__edges if not edge.contains(room)]
            # Update neighbor map
            for neighbors in self._neighbor_map.values():
                for edge in list(neighbors):
                    if edge.contains(room):
                        neighbors.remove(edge)

    def add_edge(self, edge: Edge) -> None:
        if edge not in self.__edges:
            self.__edges.append(edge)
            self._neighbor_map[edge.v].add(edge)
            self._neighbor_map[edge.w].add(edge)

    def delete_edge(self, edge: Edge) -> None:
        if edge in self.__edges:
            self.__edges.remove(edge)
            self._neighbor_map[edge.v].discard(edge)
            self._neighbor_map[edge.w].discard(edge)

    def get_edges(self) -> list[Edge]:
        return self.__edges
    
    def set_edges(self, edges: list[Edge]) -> None:
        self.__edges = edges
        self._neighbor_map.clear()
        for edge in edges:
            self._neighbor_map.setdefault(edge.v, set()).add(edge)
            self._neighbor_map.setdefault(edge.w, set()).add(edge)
    
    def get_rooms(self) -> list[Room]:
        return self.__rooms

@dataclass
class GeneratorConfig:
    room_count: int = 10
    mainroad_ratio: float = 0.5
    image_size: Tuple[int, int] = (800, 800)
    merge_ratio: float = 0.4
    further_merge_ratio: float = 0.7
    room_2x2_capacity: int = 1
    room_1x3_capacity: int = 1