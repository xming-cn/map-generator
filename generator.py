from models import Map, Room, Edge, Coordinate, GeneratorConfig, RoomType
from renderer import Renderer
from dataclasses import dataclass
from typing import Tuple, List, Optional
    
import random
class MapGenerator:
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.imgs = []

    def generate(self) -> Map:
        map = Map([], [])
        start_room = self._create_start_room(map)
        map.start_room = start_room
        mainroad_length, branch_length = self._calculate_road_lengths()
        
        available_main_road_connections = {(Coordinate(0, 0), start_room)}
        available_branch_locations = set()
        
        self._generate_main_road(map, mainroad_length, available_main_road_connections, available_branch_locations)
        self._set_special_rooms(map)
        self._generate_branches(map, branch_length, available_branch_locations)
        
        self._merge_rooms(map)
        
        self.bfs(map, map.start_room)
        self._coloring_room(map)

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

    def _get_second_branch_location(self, map: Map, branch_location: Coordinate, available_branch_locations: set) -> Optional[Coordinate]:
        return next(
            (Coordinate(branch_location.x + dx, branch_location.y + dy)
             for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
             if map.get_room(Coordinate(branch_location.x + dx, branch_location.y + dy)) is None
             and Coordinate(branch_location.x + dx, branch_location.y + dy) not in available_branch_locations),
            None
        )

    def _merge_rooms(self, map: Map) -> None:
        # 将两个连续的房间合并成一个更大的房间
        i = 0
        merge_times = self.config.merge_ratio * self.config.room_count
        while i < merge_times:
            success = self._merge_rooms_one(map)
            if success: i += 1
            else: i += 0.2

    def _merge_rooms_one(self, map: Map) -> bool:
        room1 = random.choice(map.rooms)
        neighbors = map.get_neighbors(room1)
        if len(neighbors) <= 1: return False
        
        room2 = random.choice(neighbors)
        
        if room1 == room2: return False
        if room1.type != RoomType.PENDING or room2.type != RoomType.PENDING: return False
        if room1.width != 1 or room1.height != 1 or room2.width != 1 or room2.height != 1: return False
        if len(map.get_neighbors(room2)) <= 1: return False
        
        same_col = room1.coordinate.x == room2.coordinate.x
        same_row = room1.coordinate.y == room2.coordinate.y
        
        if same_col:
            new_width = max(room1.width, room2.width)
            new_height = room1.height + room2.height
            new_coordinate = Coordinate(min(room1.coordinate.x, room2.coordinate.x), min(room1.coordinate.y, room2.coordinate.y))
        elif same_row:
            new_width = room1.width + room2.width
            new_height = max(room1.height, room2.height)
            new_coordinate = Coordinate(min(room1.coordinate.x, room2.coordinate.x), min(room1.coordinate.y, room2.coordinate.y))
        
        new_room = Room(new_coordinate, new_width, new_height, RoomType.PENDING)
        map.rooms.append(new_room)
        
        new_edges = []
        for edge in map.edges:
            connect_room = None
            if edge.contains(room1) and edge.contains(room2):
                continue
            elif edge.contains(room1):
                connect_room = room1
            elif edge.contains(room2):
                connect_room = room2

            if connect_room:
                new_edges.append(Edge(
                    new_room, connect_room.coordinate, 
                    edge.get_other(connect_room), edge.get_room_coordinate(edge.get_other(connect_room))
                ))
            else:
                new_edges.append(edge)
        map.edges = new_edges
        
        map.rooms.remove(room1)
        map.rooms.remove(room2)
        
        self.add_step(map)
        return True

    def bfs(self, map: Map, start: Room):
        queue = [start]
        visited = {start}
        distance = {start: 0}
        
        while queue:
            current_room = queue.pop(0)
            neighbors = map.get_neighbors(current_room)
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    distance[neighbor] = distance[current_room] + 1
                    neighbor.description += str(distance[neighbor]) + '\n'
        
        self.distance_from_start = distance

    def _coloring_room(self, map: Map) -> None:
        if map.start_room is None: return
        self.add_step(map)
        
        pending_room = [room for room in map.rooms if room.type == RoomType.PENDING]
        pending_leaf_rooms = [room for room in pending_room if len(map.get_neighbors(room)) == 1]
        pending_non_leaf_rooms = [room for room in pending_room if room not in pending_leaf_rooms]
        
        for room in pending_leaf_rooms:
            room.description += 'leaf\n'
        
        if pending_leaf_rooms:
            shop_room = random.choice(pending_leaf_rooms)
            shop_room.type = RoomType.SHOP
            pending_leaf_rooms.remove(shop_room)
            self.add_step(map)
        
        leaf_room_choice = [RoomType.EVENT, RoomType.BLESSING]
        non_leaf_room_choice = [RoomType.BATTLE, RoomType.ELITES]
        
        for room in pending_leaf_rooms:
            if room.type != RoomType.PENDING: continue
            room.type = random.choice(leaf_room_choice)
            leaf_room_choice.append(RoomType.EVENT if room.type == RoomType.BLESSING else RoomType.BLESSING)
            self.add_step(map)
        
        for room in pending_non_leaf_rooms:
            if room.type != RoomType.PENDING: continue
            if room.width == 1 and room.height == 1 or self.distance_from_start[room] < 2:
                room.type = RoomType.BATTLE
            else:
                room.type = random.choice(non_leaf_room_choice)
                non_leaf_room_choice.append(RoomType.BATTLE if room.type == RoomType.ELITES else RoomType.ELITES)

            self.add_step(map)
    
    def add_step(self, map: Map) -> None:
        img = Renderer(map, self.config).render()
        self.imgs.append(img)

if __name__ == '__main__':
    config = GeneratorConfig(room_count=20, image_size=(800, 800))
    generator = MapGenerator(config)
    dungeon_map = generator.generate()
    Renderer(dungeon_map, config).render().show()
