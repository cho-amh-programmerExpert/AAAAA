import streamlit as st
from streamlit_antd_components import divider as sac_divider
from streamlit_extras.let_it_rain import rain as rain_emoji
#from CustomModules.initializer import initial_run, set_page_info
import numpy as np
import random
import toml

#set_page_info("Pixel Territories", "🚩")

# Load configuration from a TOML file
config = toml.load('./config.toml')

# Configuration variables
bonus_turn = config['bonus_turn']
max_water_province_percentage = config['max_water_province_percentage']
max_grid_size = config["max_grid_size"]

nation_colors = {
    1: "blue",
    2: "orange",
    3: "green",
    4: "grey"
}

x, y = 2, 2
num_players = 2
default_names = ["D1", "D2"]
water_province_percentage = 20

def reset(x: int = 10, y: int = 10, num_players: int = 2, default_names=None, water_per: int=10):
    if default_names is None:
        default_names = [f"D{i}" for i in range(1, num_players + 1)]
    
    st.session_state['map'] = np.zeros((y, x), dtype=int)
    st.session_state['player_territories'] = {i: [] for i in range(1, num_players + 1)}
    st.session_state['capitals'] = {i: None for i in range(1, num_players + 1)}
    st.session_state['current_player'] = 1
    st.session_state['phase'] = 'name_selection'
    st.session_state['country_names'] = {i: default_names[i - 1] for i in range(1, num_players + 1)}
    st.session_state['special_province'] = (random.randint(0, y - 1), random.randint(0, x - 1))
    st.session_state['special_owner'] = None
    st.session_state['moves_left'] = 1
    st.session_state['num_players'] = num_players
    st.session_state['removed_players'] = set()
    st.session_state['army_strength'] = {i: 100 for i in range(1, num_players + 1)}  # Initialize army strength for each player

    # Add water provinces based on the configured percentage
    num_water_provinces = int((x * y) * water_per / 100)
    for _ in range(num_water_provinces):
        while True:
            wx, wy = random.randint(0, y - 1), random.randint(0, x - 1)
            if (wx, wy) != st.session_state['special_province'] and st.session_state['map'][wy, wx] == 0:
                st.session_state['map'][wy, wx] = -1  # Mark as water province
                break

def app():
    global default_names, x, y, num_players

    if 'map' not in st.session_state:
        reset(x, y, num_players, default_names)

    def display_map():
        map = st.session_state['map']
        territories = st.session_state['player_territories']
        special_province = st.session_state['special_province']
        
        for i, row in enumerate(map):
            cols = st.columns(len(row))
            for j, cell in enumerate(row):
                label = "🟫"  # Land with soil
                if (i, j) == special_province:
                    label = "⭐"
                elif cell == -1:
                    label = "🌊"  # Water province

                if cell in st.session_state['country_names']:
                    curr_l = st.session_state['country_names'][cell]
                    label = f":{nation_colors[cell]}[{curr_l}]"
                    if (i, j) == special_province:
                        label = f":{nation_colors[cell]}[▪︎☆▪︎]"

                capitals = list(st.session_state['capitals'].values())

                if (i, j) in capitals:
                    if cell in st.session_state['country_names']:
                        label = f":{nation_colors[cell]}[◆]🔰:{nation_colors[cell]}[◆]"

                with cols[j]:
                    st.button(f"**{label}**", key=f"{i}-{j}", on_click=handle_click, args=(i, j))

    def handle_click(row, col):
        current_player = st.session_state['current_player']
        opponent_players = [i for i in range(1, st.session_state['num_players'] + 1) if i != current_player]
        moves_left = st.session_state['moves_left']
        
        if st.session_state['phase'] == 'capital_selection':
            if st.session_state['capitals'][current_player] is None and st.session_state['map'][row, col] == 0:
                st.session_state['map'][row, col] = current_player
                st.session_state['capitals'][current_player] = (row, col)
                st.session_state['player_territories'][current_player].append((row, col))
                switch_player()
                if all(st.session_state['capitals'].values()):
                    st.session_state['current_player'] = 1
                    st.session_state['phase'] = 'gameplay'
                    update_moves_left()

        elif st.session_state['phase'] == 'gameplay':
            if len(st.session_state['player_territories'][current_player]) == 0:
                switch_player()
                return

            opponent_players = [i for i in opponent_players if i not in st.session_state['removed_players']]
            if is_adjacent_to_player(row, col, current_player):
                target_cell = st.session_state['map'][row, col]
                if target_cell == 0 or target_cell in opponent_players:
                    if target_cell in opponent_players:
                        # Battle occurs
                        defender = target_cell
                        damage = random.randint(5, 15)
                        st.session_state['army_strength'][current_player] -= damage  # Decrease attacker strength
                        st.session_state['army_strength'][defender] -= damage  # Decrease defender strength
                        if st.session_state['army_strength'][defender] <= 0:
                            st.session_state['removed_players'].add(defender)
                            st.session_state['capitals'][defender] = None
                        if st.session_state['army_strength'][current_player] <= 0:
                            st.session_state['removed_players'].add(current_player)
                            switch_player()
                            return
                    
                    st.session_state['map'][row, col] = current_player
                    st.session_state['player_territories'][current_player].append((row, col))
                    if target_cell in opponent_players:
                        st.session_state['player_territories'][target_cell].remove((row, col))
                    
                    if (row, col) == st.session_state['capitals'][target_cell]:
                        st.session_state['capitals'][target_cell] = None
                        if all(capital is None for capital in st.session_state['capitals'].values() if capital != st.session_state['capitals'][current_player]):
                            st.session_state['phase'] = f'player_{current_player}_wins'
                            return

                    if (row, col) == st.session_state['special_province']:
                        st.session_state['special_owner'] = current_player
                        update_moves_left()

                    moves_left -= 1
                    if moves_left == 0:
                        switch_player()
                        update_moves_left()
                    else:
                        st.session_state['moves_left'] = moves_left

    def is_adjacent_to_player(row, col, player):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for r, c in st.session_state['player_territories'][player]:
            for dr, dc in directions:
                if (r + dr == row) and (c + dc == col):
                    return True
        return False

    def switch_player():
        st.session_state['current_player'] = (st.session_state['current_player'] % st.session_state['num_players']) + 1

    def update_moves_left():
        if st.session_state['special_owner'] == st.session_state['current_player']:
            st.session_state['moves_left'] = bonus_turn
        else:
            st.session_state['moves_left'] = 1

    @st.experimental_dialog("🏴 Match Settings 🏴")
    def input_country_names():
        global default_names, num_players, x, y
        sac_divider("Country Names", "flag", "start", 'horizontal', False, True)
        
        num_players = st.number_input("**Number of Players:**", min_value=2, max_value=4, value=2)
        default_names = [st.text_input(f"**Country #{i}, Enter a name:**", placeholder=f"D{i}") for i in range(1, num_players + 1)]

        sac_divider("Map Customization", "map-fill", "start", 'horizontal', False, True)
        sidebar_cols = st.columns((3, 1, 3), vertical_alignment='center')
        x = sidebar_cols[0].number_input("X:", min_value=2, max_value=max_grid_size, value=5, key="mapsize-x")
        sidebar_cols[1].write("-X-")
        y = sidebar_cols[2].number_input("Y:", min_value=2, max_value=max_grid_size, value=5, key="mapsize-y")

        water_percentage = st.slider("Water Province Percentage", 0, 100, water_province_percentage)
        reset(x, y, num_players, default_names, water_percentage)
        st.experimental_rerun()

    if st.session_state['phase'] == 'name_selection':
        input_country_names()
    
    st.write(f"**Map Size:** {x} x {y}")
    display_map()
    
    st.info(icon=":material/cycle:", body=f"**:rainbow[Current Player]:red[:] Player#{st.session_state['current_player']} :red[(]{st.session_state['country_names'][st.session_state['current_player']]}:red[)]**")
    st.toast(icon=":material/cycle:", body=f"**:rainbow[Current Player]:red[:] Player#{st.session_state['current_player']} :red[(]{st.session_state['country_names'][st.session_state['current_player']]}:red[)]**")
    st.info(icon=f":material/counter_{st.session_state['moves_left']}:", body=f"**:orange[Moves Left]:red[:] {st.session_state['moves_left']}**")
    st.info(icon=":material/shield:", body=f"**:orange[Army Strength]:red[:] {st.session_state['army_strength'][st.session_state['current_player']]}**")

if __name__ == "__main__":
    app()
