import streamlit
import map_generator
from config import MapConfig

col1, col2 = streamlit.columns(2)

width_slider = col1.slider("Width", 2, 13, 5)
length_slider = col2.slider("Length", 2, 13, 5)
merge_chance_slider = col1.slider("Merge Chance", 0.0, 1.0, 0.7)
refresh_button = streamlit.button("Refresh")

config = MapConfig(
    grid_width=width_slider,
    grid_height=length_slider,
    merge_chance=merge_chance_slider
)

generator = map_generator.MapGenerator(config)

generator.generate()
img = generator.render()

img