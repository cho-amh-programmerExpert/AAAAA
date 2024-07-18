import streamlit as st
from streamlit_antd_components import divider as sac_divider
from streamlit_extras.let_it_rain import rain as rain_emoji
import numpy as np
import random
import toml

# set_page_info("Pixel Territories", "🚩")

# Load configuration from a TOML file
config = toml.load('config.toml')

# Configuration variables
bonus_turn = config['bonus_turn']
max_water_province_percentage = config['max_water_province_percentage']
max_grid_size = config["max_grid_size"]
units = config['units']

nation_colors = {
    1: "blue",
    2: "orange",
    3: "green",
    4: "grey"
}

x, y = 10, 10  # Default grid size
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
                if st.session_state['map'][row, col] in opponent_players:
                    opponent = st.session_state['map'][row, col]
                    result = fight(current_player, opponent)
                    if result:
                        st.session_state['player_territories'][current_player].append((row, col))
                        st.session_state['player_territories'][opponent].remove((row, col))
                        if (row, col) == st.session_state['capitals'][opponent]:
                            st.session_state['capitals'][opponent] = None
                            if all(capital is None for capital in st.session_state['capitals'].values() if capital != st.session_state['capitals'][current_player]):
                                st.session_state['phase'] = f'player_{current_player}_wins'
                                return
                else:
                    st.session_state['player_territories'][current_player].append((row, col))
                
                st.session_state['map'][row, col] = current_player

                if (row, col) == st.session_state['special_province']:
                    st.session_state['special_owner'] = current_player
                    update_moves_left()

                moves_left -= 1
                if moves_left == 0:
                    switch_player()
                    update_moves_left()
                else:
                    st.session_state['moves_left'] = moves_left

                # Add new unit to the player's army
                new_unit = get_random_unit()
                st.session_state['armies'][current_player].append(new_unit)
                st.session_state['armies'][current_player].sort(key=lambda x: x['rarity'])

    def get_random_unit():
        rarity_sum = sum(unit['rarity'] for unit in units)
        pick = random.uniform(0, rarity_sum)
        current = 0
        for unit in units:
            current += unit['rarity']
            if current > pick:
                return unit

    def fight(attacker, defender):
        attacker_army = st.session_state['armies'][attacker]
        defender_army = st.session_state['armies'][defender]
        attacker_strength = sum(unit['attack'] for unit in attacker_army)
        defender_strength = sum(unit['defense'] for unit in defender_army)

        # Determine the winner based on strength
        if attacker_strength > defender_strength:
            # Attacker wins, reduce the defender's army
            st.session_state['armies'][defender] = reduce_army_strength(defender_army, 'defense')
            return True
        else:
            # Defender wins, reduce the attacker's army
            st.session_state['armies'][attacker] = reduce_army_strength(attacker_army, 'attack')
            return False

    def reduce_army_strength(army, attribute):
        new_army = []
        for unit in army:
            unit[attribute] -= random.randint(2, 5)  # More significant reduction
            if unit[attribute] > 0:
                new_army.append(unit)
        return new_army

    def is_adjacent_to_player(row, col, player):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for r, c in st.session_state['player_territories'][player]:
            for dr, dc in directions:
                if (r + dr == row) and (c + dc == col):
                    return True
        return False

    def switch_player():
        st.session_state['current_player'] = (st.session_state['current_player'] % st.session_state['num_players']) + 1
        if st.session_state['current_player'] in st.session_state['removed_players']:
            switch_player()
        elif len(st.session_state['player_territories'][st.session_state['current_player']]) == 0:
            st.session_state['removed_players'].add(st.session_state['current_player'])
            switch_player()

    def update_moves_left():
        if st.session_state['special_owner'] == st.session_state['current_player']:
            st.session_state['moves_left'] = bonus_turn + 1
        else:
            st.session_state['moves_left'] = 1

    if st.session_state['phase'] == 'name_selection':
        st.title("Enter Player Names")
        for i in range(1, num_players + 1):
            st.text_input(f"Player {i} Name", key=f"player_{i}_name")

        if st.button("Start Game"):
            for i in range(1, num_players + 1):
                st.session_state['country_names'][i] = st.session_state.get(f'player_{i}_name', default_names[i - 1])
            st.session_state['phase'] = 'capital_selection'

    elif st.session_state['phase'] in ['capital_selection', 'gameplay']:
        st.title(f"Player {st.session_state['current_player']}'s Turn")

        display_map()

        if st.session_state['phase'] == 'gameplay':
            st.write(f"Moves left: {st.session_state['moves_left']}")

    elif st.session_state['phase'].startswith('player_'):
        winner = st.session_state['phase'].split('_')[1]
        st.title(f"Player {winner} Wins!")
        if st.button("Play Again"):
            reset(x, y, num_players, default_names)

try:
    app()
except Exception as e:
    st.write(e)
