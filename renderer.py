from models import Map, Room, Edge, Coordinate, RoomType, GeneratorConfig
from typing import Tuple
from PIL import Image, ImageDraw
from models import GeneratorConfig

ROOM_LENGTH = 100
class Renderer:
    def __init__(self, map: Map, GeneratorConfig: GeneratorConfig) -> None:
        self.map = map
        self.config = GeneratorConfig
        self.calculate_center_offset()

    def calculate_center_offset(self) -> None:
        # Calculate the bounding box of all rooms
        min_x = min(room.coordinate.x for room in self.map.rooms)
        max_x = max(room.coordinate.x for room in self.map.rooms)
        min_y = min(room.coordinate.y for room in self.map.rooms)
        max_y = max(room.coordinate.y for room in self.map.rooms)

        # Calculate the center of the bounding box
        map_center_x = (min_x + max_x) // 2
        map_center_y = (min_y + max_y) // 2

        # Calculate the offset to center the map in the image
        self.offset_x = -map_center_x * ROOM_LENGTH + self.config.image_size[0] // 2
        self.offset_y = -map_center_y * ROOM_LENGTH + self.config.image_size[1] // 2

    def render(self) -> Image.Image:
        img = Image.new('RGB', (self.config.image_size[0], self.config.image_size[1]), 'white')
        draw = ImageDraw.Draw(img)
        
        for edge in self.map.edges:
            self.draw_edge(draw, edge)
        
        for room in self.map.rooms:
            self.draw_room(draw, room)
        
        return img

    def coordinate_to_pixel(self, coord: Coordinate) -> Tuple[int, int]:
        x = coord.x * ROOM_LENGTH + self.offset_x
        y = coord.y * ROOM_LENGTH + self.offset_y
        return x, y

    def draw_room(self, draw: ImageDraw.ImageDraw, room: Room) -> None:
        room_center = self.coordinate_to_pixel(room.coordinate)
        room_topleft = (room_center[0] - ROOM_LENGTH // 2 + 8, room_center[1] - ROOM_LENGTH // 2 + 8)
        room_bottomright = (
            room_topleft[0] + room.width * ROOM_LENGTH - 16,
            room_topleft[1] + room.height * ROOM_LENGTH - 16
        )
        description_top_left = (room_topleft[0] + 5, room_topleft[1] + 5)
        draw.rectangle([room_topleft, room_bottomright], outline="black", fill=room.type.get_color())
        draw.text(description_top_left, room.type.name + '\n' + room.description, fill="black")

    def draw_edge(self, draw: ImageDraw.ImageDraw, edge: Edge) -> None:
        v_center = self.coordinate_to_pixel(edge.vCoordinate)
        w_center = self.coordinate_to_pixel(edge.wCoordinate)
        draw.line([v_center, w_center], fill="black", width=5)

if __name__ == "__main__":
    # 示例用法
    room1 = Room(Coordinate(0, 0), 1, 1, RoomType.START, "Start Room")
    room2 = Room(Coordinate(1, 0), 1, 1, RoomType.BATTLE, "Battle Room")
    edge = Edge(room1, room1.coordinate, room2, room2.coordinate)
    
    dungeon_map = Map([room1, room2], [edge])
    config = GeneratorConfig(image_size=(800, 600))
    
    renderer = Renderer(dungeon_map, config)
    img = renderer.render()
    img.show()  # 显示生成的图像
