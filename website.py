import streamlit as st
import time

from generator import MapGenerator, GeneratorConfig

IMAGE_SIZE = (1000, 1000)

# 初始化 session_state
if 'mainroad_ratio' not in st.session_state:
    st.session_state.mainroad_ratio = 0.35

if 'room_count' not in st.session_state:
    st.session_state.room_count = 20

if 'merge_ratio' not in st.session_state:
    st.session_state.merge_ratio = 20

if 'dungen' not in st.session_state:
    st.session_state.current_step = 0
    config = GeneratorConfig(
        room_count=st.session_state.room_count, 
        mainroad_ratio=st.session_state.mainroad_ratio,
        merge_ratio=st.session_state.merge_ratio,
        image_size=IMAGE_SIZE
    )
    st.session_state.dungen = MapGenerator(config)
    st.session_state.dungen.generate()

# 重新生成地图函数
def regenerate_map(force=False):
    if force:
        st.session_state.current_step = 0
        config = GeneratorConfig(
            room_count=st.session_state.room_count, 
            mainroad_ratio=st.session_state.mainroad_ratio,
            merge_ratio=st.session_state.merge_ratio,
            image_size=IMAGE_SIZE
        )
        st.session_state.dungen = MapGenerator(config)
        st.session_state.dungen.generate()

# 布局
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    if st.button("上一步"):
        if st.session_state.current_step > 0:
            st.session_state.current_step -= 1
with col2:
    if st.button("下一步"):
        if st.session_state.current_step < len(st.session_state.dungen.imgs) - 1:
            st.session_state.current_step += 1
with col3:
    if st.button("重新生成"):
        regenerate_map(force=True)
with col5:
    skip_animation = st.checkbox("跳过动画", key="skip_animation")
    if skip_animation:
        st.session_state.current_step = len(st.session_state.dungen.imgs) - 1
with col6:
    auto_play = st.checkbox("自动播放", value=True, key="auto_play")

# 侧边栏
with st.sidebar:
    room_count = st.slider("房间数量", min_value=1, max_value=50, value=20)
    if room_count != st.session_state.room_count:
        st.session_state.room_count = room_count
        regenerate_map(force=True)
        
    mainroad_ratio = st.slider("主路比例", min_value=5, max_value=100, value=35)
    if mainroad_ratio / 100 != st.session_state.mainroad_ratio:
        st.session_state.mainroad_ratio = mainroad_ratio / 100
        regenerate_map(force=True)
        
    merge_ratio = st.slider("合并比例", min_value=0, max_value=200, value=50)
    if merge_ratio / 100 != st.session_state.merge_ratio:
        st.session_state.merge_ratio = merge_ratio / 100
        regenerate_map(force=True)

# 显示地图
image_spot = st.empty()
current_step = st.session_state.current_step
image_spot.image(st.session_state.dungen.imgs[current_step])

# 自动播放逻辑
if auto_play:
    progress = st.progress(current_step / (len(st.session_state.dungen.imgs) - 1))
    while current_step < len(st.session_state.dungen.imgs) - 1:
        time.sleep(0.9)
        current_step += 3
        current_step = min(current_step, len(st.session_state.dungen.imgs) - 1)
        image_spot.image(st.session_state.dungen.imgs[current_step])
        progress.progress(current_step / (len(st.session_state.dungen.imgs) - 1))
        st.session_state.current_step = current_step

