from generator import MapGenerator, GeneratorConfig

config = GeneratorConfig(room_count=15)
generator = MapGenerator(config)
map = generator.generate()
