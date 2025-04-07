from PIL import Image
from map_generator import MapGenerator
from config import MapConfig, DEFAULT_CONFIG

def generate_maps(config: MapConfig = DEFAULT_CONFIG) -> None:
    """生成并显示多个随机地图
    
    Args:
        config: 地图生成配置，默认使用DEFAULT_CONFIG
    """
    imgs = []
    
    # 生成多个地图
    for _ in range(config.generator_count):
        generator = MapGenerator(config)
        generator.generate()
        img = generator.render()
        imgs.append(img)
    
    # 计算布局
    margin = 20  # 图片之间的边距
    max_cols = min(config.generator_count, 3)  # 每行最多显示3张图片
    rows = (config.generator_count + max_cols - 1) // max_cols  # 向上取整计算行数
    
    # 创建组合图像
    combined_width = max_cols * (config.map_length + margin) + margin
    combined_height = rows * (config.map_length + margin) + margin
    combined_img = Image.new('RGB', 
                           (combined_width, combined_height), 
                           (255, 255, 255))
    
    # 拼接所有地图
    for i in range(config.generator_count):
        row = i // max_cols
        col = i % max_cols
        x = margin + col * (config.map_length + margin)
        y = margin + row * (config.map_length + margin)
        combined_img.paste(imgs[i], (x, y))
    
    # 显示结果
    combined_img.show()

if __name__ == '__main__':
    custom_config = MapConfig(
        generator_count=9,
        grid_width=5,
        grid_height=5,
        page_margin=10,
        object_margin=5,
        map_length=512,
        edge_width=20
    )
    generate_maps(custom_config) 