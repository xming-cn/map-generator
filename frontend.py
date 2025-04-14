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
    st.session_state.merge_ratio = 0.2

if 'futher_merge_ratio' not in st.session_state:
    st.session_state.futher_merge_ratio = 0.7

if 'room_2x2_capacity' not in st.session_state:
    st.session_state.room_2x2_capacity = 1

if 'room_1x3_capacity' not in st.session_state:
    st.session_state.room_1x3_capacity = 1

if 'count_running' not in st.session_state:
    st.session_state.count_running = 0
if 'count_leaf_rooms' not in st.session_state:
    st.session_state.count_leaf_rooms = 0
if 'count_non_leaf_rooms' not in st.session_state:
    st.session_state.count_non_leaf_rooms = 0
if 'count_total_rooms' not in st.session_state:
    st.session_state.count_total_rooms = 0

def load_report(*reports: dict):
    for report in reports:
        st.session_state.count_leaf_rooms += report['leaf_rooms']
        st.session_state.count_non_leaf_rooms += report['non_leaf_rooms']
        st.session_state.count_total_rooms += report['total_rooms']
        st.session_state.count_running += 1

# 重新生成地图函数
def regenerate_map(force=False):
    if force:
        st.session_state.current_step = 0
        config = GeneratorConfig(
            room_count=st.session_state.room_count, 
            mainroad_ratio=st.session_state.mainroad_ratio,
            merge_ratio=st.session_state.merge_ratio,
            further_merge_ratio=st.session_state.futher_merge_ratio,
            image_size=IMAGE_SIZE,
            room_2x2_capacity=st.session_state.room_2x2_capacity,
            room_1x3_capacity=st.session_state.room_1x3_capacity
        )
        st.session_state.dungeon = MapGenerator(config)
        start_time = time.time()
        st.session_state.dungeon.generate()
        st.session_state.generation_time = time.time() - start_time
        st.session_state.render_time = st.session_state.dungeon.render_time
        load_report(st.session_state.dungeon.report)


if 'dungeon' not in st.session_state:
    regenerate_map(force=True)

# 布局
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    if st.button("上一步"):
        if st.session_state.current_step > 0:
            st.session_state.current_step -= 1
with col2:
    if st.button("下一步"):
        if st.session_state.current_step < len(st.session_state.dungeon.imgs) - 1:
            st.session_state.current_step += 1
with col3:
    if st.button("重新生成"):
        regenerate_map(force=True)
with col5:
    skip_animation = st.checkbox("跳过动画", key="skip_animation")
    if skip_animation:
        st.session_state.current_step = len(st.session_state.dungeon.imgs) - 1
with col6:
    auto_play = st.checkbox("自动播放", value=True, key="auto_play")

# 侧边栏
with st.sidebar:
    metric_bar = st.empty()
    
    room_count = st.slider("房间数量", min_value=1, max_value=50, value=20)
    if room_count != st.session_state.room_count:
        st.session_state.room_count = room_count
        regenerate_map(force=True)
        
    mainroad_ratio = st.slider("主路比例", min_value=5, max_value=100, value=35)
    if mainroad_ratio / 100 != st.session_state.mainroad_ratio:
        st.session_state.mainroad_ratio = mainroad_ratio / 100
        regenerate_map(force=True)
        
    merge_ratio = st.slider("合并比例", min_value=0, max_value=100, value=20)
    if merge_ratio / 100 != st.session_state.merge_ratio:
        st.session_state.merge_ratio = merge_ratio / 100
        regenerate_map(force=True)
        
    futher_merge_ratio = st.slider("进一步合并比例", min_value=0, max_value=100, value=70)
    if futher_merge_ratio / 100 != st.session_state.futher_merge_ratio:
        st.session_state.futher_merge_ratio = futher_merge_ratio / 100
        regenerate_map(force=True)
    
    capacity_col1, capacity_col2 = st.columns(2)
    with capacity_col1:
        room_1x3_capacity = st.number_input("1x3 房间上限", min_value=0, max_value=10, value=1)
        if room_1x3_capacity != st.session_state.room_1x3_capacity:
            st.session_state.room_1x3_capacity = room_1x3_capacity
            regenerate_map(force=True)
    
    with capacity_col2:
        room_2x2_capacity = st.number_input("2x2 房间上限", min_value=0, max_value=10, value=1)
        if room_2x2_capacity != st.session_state.room_2x2_capacity:
            st.session_state.room_2x2_capacity = room_2x2_capacity
            regenerate_map(force=True)
    
    if st.button('统计十次'):
        config = GeneratorConfig(
            room_count=st.session_state.room_count, 
            mainroad_ratio=st.session_state.mainroad_ratio,
            merge_ratio=st.session_state.merge_ratio,
            further_merge_ratio=st.session_state.futher_merge_ratio,
            image_size=IMAGE_SIZE,
            room_2x2_capacity=st.session_state.room_2x2_capacity,
            room_1x3_capacity=st.session_state.room_1x3_capacity
        )
        for _ in  range(10):
            st.session_state.dungeon = MapGenerator(config)
            st.session_state.dungeon.generate()
            report = st.session_state.dungeon.report
            load_report(report)
            

# 显示地图
image_spot = st.empty()
current_step = st.session_state.current_step
image_spot.image(st.session_state.dungeon.imgs[current_step])

progress_slot = st.empty()

# 自动播放逻辑
if auto_play:
    progress = progress_slot.progress(current_step / (len(st.session_state.dungeon.imgs) - 1))
    while current_step < len(st.session_state.dungeon.imgs) - 1:
        time.sleep(0.2)
        current_step += 1
        current_step = min(current_step, len(st.session_state.dungeon.imgs) - 1)
        image_spot.image(st.session_state.dungeon.imgs[current_step])
        progress.progress(current_step / (len(st.session_state.dungeon.imgs) - 1))
        st.session_state.current_step = current_step

progress_slot.text(f'generation time: {(st.session_state.generation_time - st.session_state.render_time) * 1000:.2f} ms')

col1, col2, col3 = metric_bar.columns(3)
col1.metric('Leaf', st.session_state.count_leaf_rooms, st.session_state.dungeon.report['leaf_rooms'])
col2.metric('Non-Leaf', st.session_state.count_non_leaf_rooms, st.session_state.dungeon.report['non_leaf_rooms'])
col3.metric('Total', st.session_state.count_total_rooms, st.session_state.dungeon.report['total_rooms'])
