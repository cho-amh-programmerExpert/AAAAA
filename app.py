import streamlit as st
from streamlit_antd_components import divider as sac_divider
from streamlit_extras.let_it_rain import rain as rain_emoji
#from CustomModules.initializer import initial_run, set_page_info
import numpy as np
import random
import toml

#set_page_info("Pixel Territories", "🚩")

# Load configuration from a TOML file
#config = toml.load('../Configs/minigames/pixel_territories.toml')
config = toml.load("config.toml")

# Configuration variables
bonus_turn = config['bonus_turn']
max_water_province_percentage = config['max_water_province_percentage']
max_grid_size = config["max_grid_size"]
army_config = config['army']

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
    st.session_state['armies'] = {i: [] for i in range(1, num_players + 1)}

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
            if (st.session_state['map'][row, col] == 0 or st.session_state['map'][row, col] in opponent_players) and is_adjacent_to_player(row, col, current_player):
                if st.session_state['map'][row, col] == 0:  # Neutral province
                    st.session_state['map'][row, col] = current_player
                    st.session_state['player_territories'][current_player].append((row, col))
                    st.session_state['armies'][current_player].append(generate_unit())

                else:  # Enemy province
                    result = battle(current_player, st.session_state['map'][row, col])
                    if result == "win":
                        st.session_state['map'][row, col] = current_player
                        st.session_state['player_territories'][current_player].append((row, col))
                        for opponent in opponent_players:
                            if (row, col) in st.session_state['player_territories'][opponent]:
                                st.session_state['player_territories'][opponent].remove((row, col))
                            if (row, col) == st.session_state['capitals'][opponent]:
                                st.session_state['capitals'][opponent] = None
                                if all(capital is None for capital in st.session_state['capitals'].values() if capital != st.session_state['capitals'][current_player]):
                                    st.session_state['phase'] = f'player_{current_player}_wins'
                                    return
                    elif result == "lose":
                        switch_player()
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

    def generate_unit():
        unit_type = random.choices(list(army_config.keys()), weights=[unit['rarity'] for unit in army_config.values()], k=1)[0]
        return {k: army_config[unit_type][k] for k in ('attack', 'defense', 'rarity')}

    def battle(player1, player2):
        army1 = sum(unit['attack'] for unit in st.session_state['armies'][player1])
        army2 = sum(unit['defense'] for unit in st.session_state['armies'][player2])
        return "win" if army1 > army2 else "lose"

    sac_divider("Pixel Territories")
    if st.session_state['phase'] == 'name_selection':
        st.text_input("Enter your names:", key='names')
        if st.button("Start"):
            default_names = [n.strip() for n in st.session_state['names'].split(",")[:num_players]]
            st.session_state['phase'] = 'capital_selection'
            reset(x, y, num_players, default_names, water_province_percentage)

    elif st.session_state['phase'] == 'capital_selection':
        st.write(f"Player {st.session_state['current_player']} select your capital.")
        display_map()

    elif st.session_state['phase'] == 'gameplay':
        st.write(f"Player {st.session_state['current_player']}'s turn. Moves left: {st.session_state['moves_left']}")
        display_map()

    else:
        winner = st.session_state['phase'].split('_')[1]
        st.write(f"Congratulations! Player {winner} wins!")
        if st.button("Play Again"):
            st.session_state.clear()
            reset(x, y, num_players, default_names, water_province_percentage)

try:
    #initial_run()
    app()
except Exception as e:
    st.write(e)
