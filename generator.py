from models import Map, Room, Edge, Coordinate, GeneratorConfig, RoomType
from renderer import Renderer
from dataclasses import dataclass
from typing import Tuple, List, Optional
    
import random
class MapGenerator:
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.imgs = []
        self.count_1x3_room = 0
        self.count_2x2_room = 0

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
        
        self.report = self._generator_report(map)

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
            if not success: i += 0.01
            else: i += success

    def _merge_rooms_one(self, map: Map) -> int:
        room1 = random.choice(map.rooms)
        neighbors = map.get_neighbors(room1)
        if len(neighbors) <= 1: return 0
        
        room2 = random.choice(list(neighbors))
        
        if room1 == room2: return 0
        if room1.type != RoomType.PENDING or room2.type != RoomType.PENDING: return 0
        if room1.width != 1 or room1.height != 1 or room2.width != 1 or room2.height != 1: return 0
        
        if len(map.get_neighbors(room2)) <= 1: return 0
        
        same_col = room1.coordinate.x == room2.coordinate.x
        same_row = room1.coordinate.y == room2.coordinate.y
        
        new_room = self._merge_room(map, room1, room2)
        self.add_step(map)
        
        if random.random() < self.config.further_merge_ratio:
            furthur_merge_policy = 'RANDOM'
            if self.count_1x3_room >= self.config.room_1x3_capacity and self.count_2x2_room >= self.config.room_2x2_capacity:
                return 1
            if self.count_1x3_room >= self.config.room_1x3_capacity:
                furthur_merge_policy = '2x2'
            elif self.count_2x2_room >= self.config.room_2x2_capacity:
                furthur_merge_policy = '1x3'
            else:
                furthur_merge_policy = random.choice(['1x3', '2x2'])
            
            if furthur_merge_policy == '1x3':
                furthur_mergeabla = map.get_neighbors(new_room)
                furthur_mergeabla = filter(lambda x: x.type == RoomType.PENDING and x.width == 1 and x.height == 1, furthur_mergeabla)
                if same_col: furthur_mergeabla = filter(lambda x: x.coordinate.x == new_room.coordinate.x, furthur_mergeabla)
                else:        furthur_mergeabla = filter(lambda x: x.coordinate.y == new_room.coordinate.y, furthur_mergeabla)
                furthur_mergeabla = filter(lambda x: len(map.get_neighbors(x)) > 1, furthur_mergeabla)
                furthur_mergeabla = list(furthur_mergeabla)
                if not furthur_mergeabla: return 2
                furthur_merge = random.choice(furthur_mergeabla)
                furthur_new_room = self._merge_room(map, new_room, furthur_merge)
                self.count_1x3_room += 1
                self.add_step(map)
            
            # merge 2x2 room
            elif furthur_merge_policy == '2x2':
                if same_row:
                    furthur_mergeabla_side_a = (
                        map.get_room(Coordinate(new_room.coordinate.x, new_room.coordinate.y - 1)),
                        map.get_room(Coordinate(new_room.coordinate.x + 1, new_room.coordinate.y - 1))
                    )
                    furthur_mergeabla_side_b = (
                        map.get_room(Coordinate(new_room.coordinate.x, new_room.coordinate.y + 1)),
                        map.get_room(Coordinate(new_room.coordinate.x + 1, new_room.coordinate.y + 1))
                    )
                else:
                    furthur_mergeabla_side_a = (
                        map.get_room(Coordinate(new_room.coordinate.x - 1, new_room.coordinate.y)),
                        map.get_room(Coordinate(new_room.coordinate.x - 1, new_room.coordinate.y + 1))
                    )
                    furthur_mergeabla_side_b = (
                        map.get_room(Coordinate(new_room.coordinate.x + 1, new_room.coordinate.y)),
                        map.get_room(Coordinate(new_room.coordinate.x + 1, new_room.coordinate.y + 1))
                    )
                
                def is_valid_to_merge(room) -> bool:
                    return room is not None and room.type == RoomType.PENDING and room.width == 1 and room.height == 1
                def is_connected(map, new_room, room1, room2) -> bool:
                    new_room_neighbors = map.get_neighbors(new_room)
                    room1_neighbors = map.get_neighbors(room1)
                    return (room2 in new_room_neighbors and room1 in new_room_neighbors) or \
                        (room1 in new_room_neighbors and room2 in room1_neighbors)
                def is_all_valid_to_merge(map, new_room, rooms) -> bool:
                    print('rooms', type(rooms), rooms)
                    room1 = rooms[0]
                    room2 = rooms[1]
                    return is_valid_to_merge(room1) and is_valid_to_merge(room2) and is_connected(map, new_room, room1, room2)
                
                furthur_mergeabla = None
                if is_all_valid_to_merge(map, new_room, furthur_mergeabla_side_a) and is_all_valid_to_merge(map, new_room, furthur_mergeabla_side_b):
                    furthur_mergeabla = random.choice((furthur_mergeabla_side_a, furthur_mergeabla_side_b))
                elif is_all_valid_to_merge(map, new_room, furthur_mergeabla_side_a) :
                    furthur_mergeabla = furthur_mergeabla_side_a
                elif is_all_valid_to_merge(map, new_room, furthur_mergeabla_side_b):
                    furthur_mergeabla = furthur_mergeabla_side_b
                else:
                    return 1

                furthur_merge_room_a = self._merge_room(map, furthur_mergeabla[0], furthur_mergeabla[1])
                self.add_step(map)
                
                furthur_merge_room = self._merge_room(map, new_room, furthur_merge_room_a)
                self.add_step(map)
                
                self.count_2x2_room += 1
                return 3
        
        return 1
    
    def _merge_room(self, map: Map, room1: Room, room2: Room) -> Room:
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
        else:
            print('try to merge non-adjacent rooms')
            print('room1', room1)
            print('room2', room2)
            return room1
        
        new_room = Room(new_coordinate, new_width, new_height, RoomType.PENDING)
        map.rooms.append(new_room)
        
        map.rooms.remove(room1)
        map.rooms.remove(room2)
        
        new_edges = []
        for edge in map.edges:
            connect_room = None
            if edge.contains(room1) and edge.contains(room2):
                continue
            elif edge.contains(room1):
                connect_room = room1
            elif edge.contains(room2):
                connect_room = room2
            else:
                new_edges.append(edge)
                continue
            
            other = edge.get_other(connect_room)
            new_edges.append(Edge(
                new_room, self._adjust_coordinate_for_edge(new_room, edge.get_room_coordinate(connect_room)), 
                other, edge.get_room_coordinate(other)
            ))
        map.edges = new_edges
        return new_room
    
    def _adjust_coordinate_for_edge(self, room: Room, original_coord: Coordinate) -> Coordinate:
        # Adjust the coordinate for the edge to match the new room's dimensions
        if room.coordinate.x <= original_coord.x < room.coordinate.x + room.width and \
            room.coordinate.y <= original_coord.y < room.coordinate.y + room.height:
            return original_coord
        return room.coordinate

    def bfs(self, map: Map, start: Room):
        queue = [start]
        visited = {start}
        self.distance_from_start = {start: 0}
        
        while queue:
            current_room = queue.pop(0)
            neighbors = map.get_neighbors(current_room)
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    self.distance_from_start[neighbor] = self.distance_from_start[current_room] + 1
                    neighbor.description += str(self.distance_from_start[neighbor]) + '\n'
    

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
            elif room.width == 2 and room.height == 2:
                room.type = RoomType.ELITES
            else:
                room.type = random.choice(non_leaf_room_choice)
                non_leaf_room_choice.append(RoomType.BATTLE if room.type == RoomType.ELITES else RoomType.ELITES)

            self.add_step(map)
    
    def add_step(self, map: Map) -> None:
        img = Renderer(map, self.config).render()
        self.imgs.append(img)

    def _generator_report(self, map: Map) -> dict:
        leaf_rooms = [room for room in map.rooms if len(map.get_neighbors(room)) == 1]
        non_leaf_rooms = [room for room in map.rooms if room not in leaf_rooms]
        
        return {
            'leaf_rooms': len(leaf_rooms),
            'non_leaf_rooms': len(non_leaf_rooms),
            'total_rooms': len(map.rooms),
        }

if __name__ == '__main__':
    config = GeneratorConfig(room_count=20, image_size=(800, 800))
    generator = MapGenerator(config)
    dungeon_map = generator.generate()
    Renderer(dungeon_map, config).render().show()

