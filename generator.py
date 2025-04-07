from models import Map, Room, Edge, Coordinate, GeneratorConfig, RoomType
from renderer import Renderer
from dataclasses import dataclass
from typing import Tuple, List
    
import random
class MapGenerator:
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.imgs = []

    def generate(self) -> Map:
        map = Map([], [])
        start_room = self._create_start_room(map)
        mainroad_length, branch_length = self._calculate_road_lengths()
        
        available_main_road_connections = {(Coordinate(0, 0), start_room)}
        available_branch_locations = set()
        
        self._generate_main_road(map, mainroad_length, available_main_road_connections, available_branch_locations)
        self._set_special_rooms(map)
        self._generate_branches(map, branch_length, available_branch_locations)
        
        self._merge_rooms(map)

        return map

    def _create_start_room(self, map: Map) -> Room:
        start_location = Coordinate(0, 1)
        start_room = Room(start_location, 1, 1, RoomType.START)
        map.rooms.append(start_room)
        self.add_step(map)
        return start_room

    def _calculate_road_lengths(self) -> Tuple[int, int]:
        mainroad_length = int(self.config.room_count * self.config.mainroad_ratio)
        mainroad_length = max(1, mainroad_length)
        branch_length = self.config.room_count - mainroad_length
        return mainroad_length, branch_length

    def _generate_main_road(self, map: Map, mainroad_length: int, available_main_road_connections: set, available_branch_locations: set) -> None:
        for _ in range(mainroad_length):
            if not available_main_road_connections:
                break

            new_connection_location, room = random.choice(list(available_main_road_connections))
            available_main_road_connections.remove((new_connection_location, room))
            
            new_room = Room(new_connection_location, 1, 1, RoomType.PENDING)
            map.rooms.append(new_room)
            map.edges.append(Edge(room, room.coordinate, new_room, new_room.coordinate))
            
            available_next_coordinates = self._get_available_coordinates(map, new_connection_location, available_main_road_connections)
            if available_next_coordinates:
                chosen_coord = random.choice(available_next_coordinates)
                available_main_road_connections.add((chosen_coord, new_room))
                available_next_coordinates.remove(chosen_coord)
                available_branch_locations.update(available_next_coordinates)
            else:
                available_branch_locations.update(available_next_coordinates)
            self.add_step(map)

    def _set_special_rooms(self, map: Map) -> None:
        map.rooms[len(map.rooms) // 2].type = RoomType.REST
        self.add_step(map)
        map.rooms[-1].type = RoomType.BOSS
        self.add_step(map)

    def _generate_branches(self, map: Map, branch_length: int, available_branch_locations: set) -> None:
        branches_created = 0
        while branches_created < branch_length and available_branch_locations:
            branch_location = random.choice(list(available_branch_locations))
            available_branch_locations.remove(branch_location)
            
            connected_room = self._find_connected_room(map, branch_location)
            if connected_room.type in {RoomType.START, RoomType.BOSS}:
                continue
            
            if map.get_room(branch_location) is None:
                # 创建第一个支线房间
                new_branch_room = Room(branch_location, 1, 1, RoomType.PENDING)
                map.rooms.append(new_branch_room)
                map.edges.append(Edge(connected_room, connected_room.coordinate, new_branch_room, new_branch_room.coordinate))
                self.add_step(map)
                branches_created += 1
                
                # 动态更新支线房间的可用连接点
                new_branch_locations = self._get_available_coordinates(map, branch_location, available_branch_locations)
                available_branch_locations.update(new_branch_locations)
                
                # 创建第二个支线房间（确保支线长度至少为2）
                if branches_created < branch_length:
                    second_branch_location = self._get_second_branch_location(map, branch_location, available_branch_locations)
                    if second_branch_location:
                        second_branch_room = Room(second_branch_location, 1, 1, RoomType.PENDING)
                        map.rooms.append(second_branch_room)
                        map.edges.append(Edge(new_branch_room, new_branch_room.coordinate, second_branch_room, second_branch_room.coordinate))
                        branches_created += 1
                        self.add_step(map)
                        
                        # 动态更新第二个支线房间的可用连接点
                        new_branch_locations = self._get_available_coordinates(map, second_branch_location, available_branch_locations)
                        available_branch_locations.update(new_branch_locations)
                
                # 如果支线长度不足以继续生成更多房间，则停止
                if branches_created >= branch_length:
                    break
                
                # 更新当前房间的可用连接点
                available_next_coordinates = self._get_available_coordinates(map, branch_location, available_branch_locations)
                available_branch_locations.update(available_next_coordinates)

    def _get_available_coordinates(self, map: Map, location: Coordinate, existing_connections: set) -> List[Coordinate]:
        available_next_coordinates = [
            Coordinate(location.x + dx, location.y + dy)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            if map.get_room(Coordinate(location.x + dx, location.y + dy)) is None
            and not any(conn == Coordinate(location.x + dx, location.y + dy) for conn in existing_connections)
        ]
        return [
            coord for coord in available_next_coordinates
            if sum(
                1 for nx, ny in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                if map.get_room(Coordinate(coord.x + nx, coord.y + ny)) is not None
            ) <= 2
        ]

    def _find_connected_room(self, map: Map, location: Coordinate) -> Room:
        return next(
            room for room in map.rooms
            if any(
                room.coordinate == Coordinate(location.x + dx, location.y + dy)
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            )
        )

    def _get_second_branch_location(self, map: Map, branch_location: Coordinate, available_branch_locations: set) -> Coordinate | None:
        return next(
            (Coordinate(branch_location.x + dx, branch_location.y + dy)
             for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
             if map.get_room(Coordinate(branch_location.x + dx, branch_location.y + dy)) is None
             and Coordinate(branch_location.x + dx, branch_location.y + dy) not in available_branch_locations),
            None
        )

    def _merge_rooms(self, map: Map) -> None:
        # 将两个连续的房间合并成一个更大的房间
        merge_times = int(self.config.merge_ratio * self.config.room_count)
        for _ in range(merge_times):
            room1 = random.choice(map.rooms)
            neighbors = map.get_neighbors(room1)
            if not neighbors: continue
            
            room2 = random.choice(neighbors)
            
            if room1 == room2: continue
            if room1.type != RoomType.PENDING or room2.type != RoomType.PENDING: continue
            if room1.width != 1 or room1.height != 1 or room2.width != 1 or room2.height != 1: continue
            
            same_col = room1.coordinate.x == room2.coordinate.x
            same_row = room1.coordinate.y == room2.coordinate.y
            
            if same_col:
                new_width = max(room1.width, room2.width)
                new_height = room1.height + room2.height
                new_coordinate = Coordinate(room1.coordinate.x, min(room1.coordinate.y, room2.coordinate.y))
            elif same_row:
                new_width = room1.width + room2.width
                new_height = max(room1.height, room2.height)
                new_coordinate = Coordinate(min(room1.coordinate.x, room2.coordinate.x), room1.coordinate.y)
            
            new_room = Room(new_coordinate, new_width, new_height, RoomType.PENDING)
            map.rooms.append(new_room)
            
            for edge in map.edges:
                connect_room = None
                if edge.contains(room1) and edge.contains(room2):
                    map.edges.remove(edge)
                    continue
                elif edge.contains(room1):
                    connect_room = room1
                elif edge.contains(room2):
                    connect_room = room2

                if connect_room:
                    map.edges.append(Edge(
                        new_room, connect_room.coordinate, 
                        edge.get_other(connect_room), edge.get_room_coordinate(edge.get_other(connect_room))
                    ))
            
            if room1 in map.rooms: map.rooms.remove(room1)
            if room2 in map.rooms: map.rooms.remove(room2)
            
            self.add_step(map)
            

    def add_step(self, map: Map) -> None:
        img = Renderer(map, self.config).render()
        self.imgs.append(img)

if __name__ == '__main__':
    config = GeneratorConfig(room_count=20, image_size=(800, 800))
    generator = MapGenerator(config)
    dungeon_map = generator.generate()
    Renderer(dungeon_map, config).render().show()
