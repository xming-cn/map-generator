from typing import List, Optional, Tuple, Any
from PIL import Image, ImageDraw
from models import Room, Edge
from config import COLOR_MAP, MapConfig, DEFAULT_CONFIG

class MapRenderer:
    """负责将地图渲染成图像"""
    
    def __init__(self, width: int, height: int, config: MapConfig = DEFAULT_CONFIG) -> None:
        self.width = width
        self.height = height
        self.config = config
        self.rooms: List[Room] = []
        self.edges: List[Edge] = []

    def add_room(self, room: Room) -> None:
        """添加房间到渲染列表"""
        self.rooms.append(room)
    
    def add_edge(self, edge: Edge) -> None:
        """添加边到渲染列表"""
        self.edges.append(edge)
    
    def get_grid_cell_size(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """计算网格单元格大小"""
        cell_width = (self.config.map_length - self.config.page_margin * 2) // self.width
        cell_height = (self.config.map_length - self.config.page_margin * 2) // self.height
        return cell_width, cell_height
    
    def get_grid_cell_topLeft(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """计算网格单元格左上角坐标"""
        cell_width, cell_height = self.get_grid_cell_size(pos)
        return (self.config.page_margin + (pos[0]-1) * cell_width, 
                self.config.page_margin + (pos[1]-1) * cell_height)
    
    def get_room(self, pos: Tuple[int, int]) -> Optional[Room]:
        """获取指定位置的房间"""
        for room in self.rooms:
            if pos[0] >= room.topLeft[0] and pos[0] < room.topLeft[0] + room.size[0] and \
               pos[1] >= room.topLeft[1] and pos[1] < room.topLeft[1] + room.size[1]:
                return room
        return None
    
    def draw_edges(self, draw: Any) -> None:
        """绘制边缘连接"""
        for edge in self.edges:
            cell_width, cell_height = self.get_grid_cell_size(edge.start)
            left, top = self.get_grid_cell_topLeft(edge.start)
            start_left = left + cell_width // 2
            start_top = top + cell_height // 2
            
            if edge.direction == 'Horizontal':
                end_left = start_left + cell_width
                end_top = start_top
            else:  # Vertical
                end_left = start_left
                end_top = start_top + cell_height
                
            draw.line([start_left, start_top, end_left, end_top], 
                     fill='#00008B', width=self.config.edge_width)
    
    def draw_rooms(self, draw: Any) -> None:
        """绘制房间"""
        default_color = 0xAEA8A5
        for room in self.rooms:
            color = COLOR_MAP.get(room.color)
            if not color: 
                color = f'#{default_color:06x}'
                default_color -= 0x040404
            
            cell_width, cell_height = self.get_grid_cell_size(room.topLeft)
            left, top = self.get_grid_cell_topLeft(room.topLeft)
            right = left + cell_width * room.size[0]
            bottom = top + cell_height * room.size[1]
            
            # 应用边距
            margin = self.config.object_margin
            left, top = left + margin, top + margin
            right, bottom = right - margin, bottom - margin
            
            draw.rectangle([left, top, right, bottom], fill=color)
            draw.text((left + margin, top + margin), 
                     f'{room.color}\n{room.description}', fill=(0, 0, 0))
    
    def draw_empty_cells(self, draw: Any) -> None:
        """绘制空单元格"""
        for x in range(1, self.width + 1):
            for y in range(1, self.height + 1):
                if not self.get_room((x, y)):
                    cell_width, cell_height = self.get_grid_cell_size((x, y))
                    left, top = self.get_grid_cell_topLeft((x, y))
                    right = left + cell_width
                    bottom = top + cell_height
                    
                    # 应用边距
                    margin = self.config.object_margin
                    left, top = left + margin, top + margin
                    right, bottom = right - margin, bottom - margin
                    
                    draw.rectangle([left, top, right, bottom], fill=(240, 240, 240))
                    draw.text((left + margin, top + margin), 
                            'empty', fill=(0, 0, 0))
    
    def render(self) -> Image.Image:
        """渲染完整地图"""
        img = Image.new('RGB', 
                       (self.config.map_length, self.config.map_length), 
                       (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        self.draw_edges(draw)
        self.draw_rooms(draw)
        self.draw_empty_cells(draw)
        
        return img 