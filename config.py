from typing import Dict, NamedTuple
from dataclasses import dataclass

@dataclass
class MapConfig:
    """地图生成配置"""
    generator_count: int = 1
    grid_width: int = 5
    grid_height: int = 5
    merge_chance: float = 0.7
    page_margin: int = 0
    object_margin: int = 3
    map_length: int = 768
    edge_width: int = 15

class RoomType:
    """房间类型常量"""
    START = 'start'
    BATTLE = 'battle'
    EVENT = 'event'
    REST = 'rest'
    ELITES = 'elites'
    BLESSING = 'blessing'
    BOSS = 'boss'
    SHOP = 'shop'
    PENDING = 'pending'

class RoomWeights(NamedTuple):
    """房间类型权重配置"""
    battle: int = 2
    event: int = 1
    elites: int = 1
    blessing: int = 1

# 默认配置
DEFAULT_CONFIG = MapConfig()
DEFAULT_WEIGHTS = RoomWeights()

# 颜色映射
COLOR_MAP: Dict[str, str] = {
    RoomType.START: '#007D3C',
    RoomType.BATTLE: '#BA5D03',
    RoomType.EVENT: '#21A1B3',
    RoomType.REST: '#CC2BB1',
    RoomType.ELITES: '#8E0668',
    RoomType.BLESSING: '#FCC737',
    RoomType.BOSS: '#730505',
    RoomType.SHOP: '#3E3CD8',
} 