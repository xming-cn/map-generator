import random
from typing import Optional, List, Set, Dict, Tuple, cast
from PIL import Image
from models import Room, Edge
from renderer import MapRenderer
from config import RoomType, MapConfig, DEFAULT_CONFIG


# 颜色映射
COLOR_MAP = {
    RoomType.START: '#007D3C',
    RoomType.BATTLE: '#BA5D03',
    RoomType.EVENT: '#21A1B3',
    RoomType.REST: '#CC2BB1',
    RoomType.ELITES: '#8E0668',
    RoomType.BLESSING: '#FCC737',
    RoomType.BOSS: '#730505',
    RoomType.SHOP: '#3E3CD8',
}

class Map:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.rooms: List[Room] = []
        self.edges: List[Edge] = []

    def add_room(self, room: Room) -> None:
        self.rooms.append(room)
    
    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)
    
    def get_room(self, pos: Tuple[int, int]) -> Optional[Room]:
        for room in self.rooms:
            if pos[0] >= room.topLeft[0] and pos[0] < room.topLeft[0] + room.size[0] and \
               pos[1] >= room.topLeft[1] and pos[1] < room.topLeft[1] + room.size[1]:
                return room
        return None

class MapGenerator:
    """地图生成器类，负责生成随机地图"""
    
    def __init__(self, config: MapConfig = DEFAULT_CONFIG) -> None:
        self.config = config
        self.width = config.grid_width
        self.height = config.grid_height
        self.unavailable_pos: Set[Tuple[int, int]] = set()
        self.available_pos: Set[Tuple[int, int]] = set()
        self.pending_pos: Set[Tuple[int, int]] = set()
        self.pending_room: List[Room] = []
        self.room_types: Dict[Tuple[int, int], str] = {}
        self.edges: List[Edge] = []
        self.distance_to_start: Dict[Room, int] = {}
        self.distance_to_start_path: Dict[Room, List[Room]] = {}
        
        # 初始化所有位置为不可用
        for x in range(1, self.width + 1):
            for y in range(1, self.height + 1):
                self.unavailable_pos.add((x, y))

    def set_available_pos(self, pos: Tuple[int, int]) -> None:
        """将位置标记为可用"""
        if pos in self.unavailable_pos:
            self.available_pos.add(pos)
            self.unavailable_pos.remove(pos)
    
    def set_pending_pos(self, pos: Tuple[int, int]) -> None:
        """将位置标记为待处理，并更新其相邻位置为可用"""
        self.pending_pos.add(pos)
        self.available_pos.discard(pos)
        self.unavailable_pos.discard(pos)
        
        # 更新相邻位置为可用
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            self.set_available_pos((pos[0] + dx, pos[1] + dy))

    def get_neighboring_pending_pos(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """获取给定位置的所有待处理相邻位置"""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (pos[0] + dx, pos[1] + dy)
            if neighbor in self.pending_pos:
                neighbors.append(neighbor)
        return neighbors

    def is_room_connected(self, roomA: Room, roomB: Room) -> bool:
        """检查两个房间是否通过边连接"""
        if not self.check_adjacent(roomA, roomB):
            return False
            
        for edge in self.edges:
            edge_start = edge.start
            edge_end = (
                edge_start[0] + (1 if edge.direction == 'Horizontal' else 0),
                edge_start[1] + (1 if edge.direction == 'Vertical' else 0)
            )
            if (self.get_room(edge_start) == roomA and self.get_room(edge_end) == roomB) or \
               (self.get_room(edge_start) == roomB and self.get_room(edge_end) == roomA):
                return True
        return False

    def get_room(self, pos: Tuple[int, int]) -> Optional[Room]:
        """获取给定位置的房间"""
        for room in self.pending_room:
            if (pos[0] >= room.topLeft[0] and 
                pos[0] < room.topLeft[0] + room.size[0] and 
                pos[1] >= room.topLeft[1] and 
                pos[1] < room.topLeft[1] + room.size[1]):
                return room
        return None

    def get_neighboring_pending_room(self, room: Room) -> List[Room]:
        """获取给定房间的所有相邻房间"""
        neighbors: Set[Room] = set()
        for x in range(room.topLeft[0], room.topLeft[0] + room.size[0]):
            for y in range(room.topLeft[1], room.topLeft[1] + room.size[1]):
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = self.get_room((x + dx, y + dy))
                    if (neighbor and 
                        neighbor != room and 
                        neighbor not in neighbors and
                        self.is_room_connected(room, neighbor)):
                        neighbors.add(neighbor)
        return list(neighbors)
    
    def is_room_leaf(self, room: Room) -> bool:
        """检查房间是否为叶子节点（只有一个相邻房间）"""
        return len(self.get_neighboring_pending_room(room)) == 1
    
    def check_adjacent(self, a: Room, b: Room) -> bool:
        """检查两个房间是否相邻"""
        a_left, a_top = a.topLeft
        a_right = a_left + a.size[0]
        a_bottom = a_top + a.size[1]

        b_left, b_top = b.topLeft
        b_right = b_left + b.size[0]
        b_bottom = b_top + b.size[1]

        # 水平相邻
        horizontal = (a_right == b_left or b_right == a_left) and \
                    (a_top < b_bottom and a_bottom > b_top)
        
        # 垂直相邻
        vertical = (a_bottom == b_top or b_bottom == a_top) and \
                  (a_left < b_right and a_right > b_left)
        
        return horizontal or vertical

    def generate_base_map(self) -> Tuple[Tuple[int, int], Set[Tuple[int, int]]]:
        """生成基础地图结构，返回起点位置和已连接位置集合"""
        # 随机选择起点位置
        start_pos = (random.choice([1, self.width]), random.randint(1, self.height)) if random.random() < 0.5 \
            else (random.randint(1, self.width), random.choice([1, self.height]))
        self.room_types[start_pos] = RoomType.START
        self.set_pending_pos(start_pos)
        
        # 用于追踪已连接的位置
        connected_positions = {start_pos}
        start_room_connected = False
        
        while self.available_pos:
            # 优先选择与已连接位置相邻的可用位置
            available_connected = [
                pos for pos in self.available_pos 
                if any((pos[0] + dx, pos[1] + dy) in connected_positions 
                      for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)])
            ]
            
            pos = random.choice(available_connected) if available_connected \
                else random.choice(list(self.available_pos))
            
            self.set_pending_pos(pos)
            self.room_types[pos] = RoomType.PENDING
            
            # 获取已连接的邻居位置
            connected_neighbors = [n for n in self.get_neighboring_pending_pos(pos) 
                                if n in connected_positions]
            
            if connected_neighbors:
                # 处理与起始房间的连接
                is_start_involved = pos == start_pos or any(n == start_pos for n in connected_neighbors)
                if is_start_involved:
                    if start_room_connected:
                        connected_neighbors = [n for n in connected_neighbors if n != start_pos]
                    else:
                        connected_neighbors = [start_pos]
                        start_room_connected = True
                
                if not connected_neighbors: continue
                
                # 创建边连接
                neighbor = random.choice(connected_neighbors)
                if pos[0] == neighbor[0]:
                    edge_start = neighbor if neighbor[1] < pos[1] else pos
                    self.edges.append(Edge(edge_start, 'Vertical'))
                else:
                    edge_start = neighbor if neighbor[0] < pos[0] else pos
                    self.edges.append(Edge(edge_start, 'Horizontal'))
                
                connected_positions.add(pos)
        
        return start_pos, connected_positions

    def merge_rooms(self) -> None:
        """合并相邻的房间"""
        # 创建初始房间
        for room_pos in self.pending_pos:
            self.pending_room.append(Room(room_pos, (1, 1), self.room_types[room_pos]))
        
        # 尝试合并房间
        for _ in range(self.width * self.height // 2):
            room = random.choice(self.pending_room)
            neighbors = self.get_neighboring_pending_room(room)
            if not neighbors: continue
            
            neighbor = random.choice(neighbors)
            if room.color != neighbor.color or room.size != (1, 1) or neighbor.size != (1, 1):
                continue
            
            # 确定合并方向和新房间属性
            same_row = room.topLeft[1] == neighbor.topLeft[1]
            same_col = room.topLeft[0] == neighbor.topLeft[0]
            
            new_top_left = (
                min(room.topLeft[0], neighbor.topLeft[0]), room.topLeft[1]
            ) if same_row else (
                room.topLeft[0], min(room.topLeft[1], neighbor.topLeft[1])
            )
            
            new_size = (
                room.size[0] + neighbor.size[0], room.size[1]
            ) if same_row else (
                room.size[0], room.size[1] + neighbor.size[1]
            )
            
            new_room = Room(new_top_left, new_size, room.color)
            
            # 应用合并
            self.pending_room.remove(room)
            self.pending_room.remove(neighbor)
            self.pending_room.append(new_room)
            
            # 检查是否形成叶子节点
            if self.is_room_leaf(new_room):
                self.pending_room.append(room)
                self.pending_room.append(neighbor)
                self.pending_room.remove(new_room)
                continue
            
            # 尝试进一步合并
            if random.random() < self.config.merge_chance:
                self._try_further_merge(new_room, same_row, same_col)

    def _try_further_merge(self, room: Room, same_row: bool, same_col: bool) -> None:
        """尝试进一步合并房间"""
        merger_neighbors = self.get_neighboring_pending_room(room)
        if random.random() < 0.5:
            self._try_merge_1x3(room, merger_neighbors, same_row, same_col)
        else:
            self._try_merge_2x2(room, same_row, same_col)

    def _try_merge_1x3(self, room: Room, neighbors: List[Room], same_row: bool, same_col: bool) -> None:
        """尝试合并成1x3或3x1的房间"""
        for neighbor in neighbors:
            if (neighbor.size != (1, 1) or 
                neighbor.color != room.color or 
                (same_row and neighbor.topLeft[1] != room.topLeft[1]) or 
                (same_col and neighbor.topLeft[0] != room.topLeft[0])):
                continue
            
            merger_top_left = (
                min(room.topLeft[0], neighbor.topLeft[0]), room.topLeft[1]
            ) if same_row else (
                room.topLeft[0], min(room.topLeft[1], neighbor.topLeft[1])
            )
            
            merger_size = (
                room.size[0] + neighbor.size[0], room.size[1]
            ) if same_row else (
                room.size[0], room.size[1] + neighbor.size[1]
            )
            
            merger_room = Room(merger_top_left, merger_size, room.color)
            
            self.pending_room.remove(neighbor)
            self.pending_room.remove(room)
            self.pending_room.append(merger_room)
            
            if self.is_room_leaf(merger_room):
                self.pending_room.append(neighbor)
                self.pending_room.append(room)
                self.pending_room.remove(merger_room)
            break

    def _try_merge_2x2(self, room: Room, same_row: bool, same_col: bool) -> None:
        """尝试合并成2x2的房间"""
        if same_row:
            neighbors_to_merge = (
                (self.get_room((room.topLeft[0], room.topLeft[1] - 1)), 
                 self.get_room((room.topLeft[0] + 1, room.topLeft[1] - 1))),
                (self.get_room((room.topLeft[0], room.topLeft[1] + 1)), 
                 self.get_room((room.topLeft[0] + 1, room.topLeft[1] + 1))),
            )
        elif same_col:
            neighbors_to_merge = (
                (self.get_room((room.topLeft[0] + 1, room.topLeft[1])), 
                 self.get_room((room.topLeft[0] + 1, room.topLeft[1] + 1))),
                (self.get_room((room.topLeft[0] - 1, room.topLeft[1])), 
                 self.get_room((room.topLeft[0] - 1, room.topLeft[1] + 1))),
            )
        else:
            return
        
        merger_neighbors = self.get_neighboring_pending_room(room)
        for neighbor1, neighbor2 in neighbors_to_merge:
            if not self._can_merge_2x2(room, neighbor1, neighbor2, merger_neighbors):
                continue
                
            # 类型检查已经在_can_merge_2x2中完成，这里可以安全地使用cast
            neighbor1 = cast(Room, neighbor1)
            neighbor2 = cast(Room, neighbor2)
            
            merger_top_left = (
                min(neighbor1.topLeft[0], neighbor2.topLeft[0], room.topLeft[0]),
                min(neighbor1.topLeft[1], neighbor2.topLeft[1], room.topLeft[1])
            )
            merger_room = Room(merger_top_left, (2, 2), room.color)
            
            self.pending_room.remove(neighbor1)
            self.pending_room.remove(neighbor2)
            self.pending_room.remove(room)
            self.pending_room.append(merger_room)
            
            if self.is_room_leaf(merger_room):
                self.pending_room.append(neighbor1)
                self.pending_room.append(neighbor2)
                self.pending_room.append(room)
                self.pending_room.remove(merger_room)
            break

    def _can_merge_2x2(self, room: Room, neighbor1: Optional[Room], 
                       neighbor2: Optional[Room], merger_neighbors: List[Room]) -> bool:
        """检查是否可以合并成2x2的房间"""
        if not (neighbor1 and neighbor2):
            return False
            
        if not (neighbor1 in merger_neighbors or neighbor2 in merger_neighbors):
            return False
            
        if not (neighbor1 in merger_neighbors and neighbor2 in self.get_neighboring_pending_room(neighbor1) or
                neighbor2 in merger_neighbors and neighbor1 in self.get_neighboring_pending_room(neighbor2)):
            return False
            
        if not (neighbor1.color == neighbor2.color == room.color):
            return False
            
        if not (neighbor1.size == neighbor2.size == (1, 1)):
            return False
            
        return True

    def assign_room_types(self) -> None:
        """为房间分配类型"""
        # 标记叶子节点
        for room in self.pending_room:
            if self.is_room_leaf(room):
                room.description += 'leaf\n'
        
        # 计算到起点的距离
        start_room = self.get_room(next(pos for pos, type in self.room_types.items() 
                                      if type == RoomType.START))
        if not start_room:
            raise ValueError("Start room not found")
            
        self.bfs(start_room)
        
        # 添加距离信息
        for room, distance in self.distance_to_start.items():
            room.description += f'{distance}\n'
        
        # 获取最远距离
        longest_distance = max(self.distance_to_start.values())
        
        # 分离叶子和非叶子房间
        pending_leaf_rooms = []
        pending_non_leaf_rooms = []
        for room in self.pending_room:
            if room.color != RoomType.PENDING:
                continue
            if self.is_room_leaf(room):
                pending_leaf_rooms.append(room)
            else:
                pending_non_leaf_rooms.append(room)
        
        random.shuffle(pending_leaf_rooms)
        random.shuffle(pending_non_leaf_rooms)
        
        # 分配商店
        if pending_leaf_rooms:
            shop_room = pending_leaf_rooms.pop(0)
            shop_room.color = RoomType.SHOP
        
        # 分配Boss和其他叶子房间类型
        boss_room = None
        for room in pending_leaf_rooms:
            if room in self.distance_to_start and not boss_room and \
               self.distance_to_start[room] == longest_distance:
                room.color = RoomType.BOSS
                boss_room = room
            else:
                room.color = random.choice([RoomType.EVENT, RoomType.BLESSING])
        
        # 分配休息房间
        if boss_room:
            self._assign_rest_room(boss_room)
        
        # 分配其他房间类型
        non_leaf_choices = [RoomType.BATTLE, RoomType.BATTLE, RoomType.ELITES]
        for room in pending_non_leaf_rooms:
            if room.color == RoomType.REST:
                continue
            
            if room in self.distance_to_start and self.distance_to_start[room] < 3:
                room.color = RoomType.BATTLE
            else:
                room.color = random.choice(non_leaf_choices)
                if room.color == RoomType.ELITES:
                    non_leaf_choices.append(RoomType.BATTLE)
        
        # 标记主路径
        if boss_room:
            for room in self.distance_to_start_path[boss_room]:
                room.description += 'main_path\n'

    def _assign_rest_room(self, boss_room: Room) -> None:
        """在主路径上分配休息房间"""
        main_path = self.distance_to_start_path.get(boss_room, [])
        if not main_path:
            return
            
        rest_index = len(main_path) // 2
        left = right = rest_index
        
        # 寻找合适的休息房间位置
        while left >= 0 or right < len(main_path):
            if left >= 0 and main_path[left].size == (1, 1):
                rest_index = left
                break
            if right < len(main_path) and main_path[right].size == (1, 1):
                rest_index = right
                break
            left -= 1
            right += 1
        
        if 0 <= rest_index < len(main_path):
            main_path[rest_index].color = RoomType.REST

    def bfs(self, start: Room) -> None:
        """广度优先搜索计算房间间的距离"""
        queue = [start]
        visited = {start}
        self.distance_to_start[start] = 0
        
        while queue:
            current = queue.pop(0)
            for neighbor in self.get_neighboring_pending_room(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    self.distance_to_start[neighbor] = self.distance_to_start[current] + 1
                    self.distance_to_start_path[neighbor] = self.distance_to_start_path.get(current, []) + [current]
                    if neighbor not in self.pending_room:
                        self.pending_room.append(neighbor)

    def generate(self) -> None:
        """生成完整的地图"""
        start_pos, _ = self.generate_base_map()
        self.merge_rooms()
        self.assign_room_types()

    def render(self) -> Image.Image:
        """渲染地图"""
        renderer = MapRenderer(self.width, self.height)
        for room in self.pending_room:
            renderer.add_room(room)
        for edge in self.edges:
            renderer.add_edge(edge)
        return renderer.render()

def show_grave() -> None:
    renderer = MapRenderer(4, 3)

    renderer.add_room(Room((1, 3), (1, 1), RoomType.START))
    renderer.add_room(Room((1, 2), (1, 1), RoomType.BATTLE))
    renderer.add_room(Room((1, 1), (1, 1), RoomType.EVENT))
    renderer.add_room(Room((2, 1), (1, 1), RoomType.REST))
    renderer.add_room(Room((2, 2), (2, 1), RoomType.ELITES))
    renderer.add_room(Room((2, 3), (1, 1), RoomType.BLESSING))
    renderer.add_room(Room((3, 3), (1, 1), RoomType.BATTLE))
    renderer.add_room(Room((3, 1), (2, 1), RoomType.BOSS))
    renderer.add_room(Room((4, 2), (1, 1), RoomType.EVENT))

    renderer.add_edge(Edge((1, 2), 'Vertical'))
    renderer.add_edge(Edge((1, 1), 'Vertical'))
    renderer.add_edge(Edge((1, 1), 'Horizontal'))
    renderer.add_edge(Edge((2, 1), 'Vertical'))
    renderer.add_edge(Edge((2, 2), 'Vertical'))
    renderer.add_edge(Edge((3, 2), 'Vertical'))
    renderer.add_edge(Edge((3, 2), 'Horizontal'))
    renderer.add_edge(Edge((4, 1), 'Vertical'))

    renderer.render().show()
