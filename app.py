import streamlit as st
import numpy as np
import toml

# Load configuration
config = toml.load("config.toml")
units = config["units"]
map_width = config["game"]["map_width"]
map_height = config["game"]["map_height"]
max_recruits_per_turn = config["game"]["max_recruits_per_turn"]

# Initialize session state
if "map" not in st.session_state:
    st.session_state.map = np.zeros((map_height, map_width), dtype=int)
    st.session_state.capitals = [None, None]
    st.session_state.turn = 0
    st.session_state.resources = [100, 100]
    st.session_state.units = [{}, {}]
    st.session_state.armies = [[], []]
    st.session_state.selected_army = None

def end_turn():
    st.session_state.turn = 1 - st.session_state.turn
    st.session_state.selected_army = None

def recruit_units(unit_type, quantity):
    turn = st.session_state.turn
    if st.session_state.resources[turn] >= units[unit_type]["cost"] * quantity:
        st.session_state.resources[turn] -= units[unit_type]["cost"] * quantity
        if unit_type in st.session_state.units[turn]:
            st.session_state.units[turn][unit_type] += quantity
        else:
            st.session_state.units[turn][unit_type] = quantity

def handle_click(row, col):
    turn = st.session_state.turn
    if st.session_state.capitals[turn] is None:
        st.session_state.capitals[turn] = (row, col)
        st.session_state.map[row, col] = turn + 1
    elif st.session_state.selected_army is None and st.session_state.map[row, col] == turn + 1:
        st.session_state.selected_army = (row, col)
    elif st.session_state.selected_army is not None:
        selected_row, selected_col = st.session_state.selected_army
        if is_adjacent(selected_row, selected_col, row, col):
            if st.session_state.map[row, col] == 0:
                # Move to unoccupied territory
                st.session_state.map[row, col] = turn + 1
                st.session_state.selected_army = (row, col)
            elif st.session_state.map[row, col] != turn + 1:
                # Attack enemy territory
                attack(row, col)
                st.session_state.selected_army = (row, col)

def is_adjacent(row1, col1, row2, col2):
    return abs(row1 - row2) + abs(col1 - col2) == 1

def attack(target_row, target_col):
    turn = 1 if st.session_state.turn%2 != 0 else 2
    enemy = 1 - turn
    attacking_units = st.session_state.units[turn]
    defending_units = st.session_state.units[enemy]
    
    attack_strength = sum(units[unit]["attack"] * count for unit, count in attacking_units.items())
    defense_strength = sum(units[unit]["defense"] * count for unit, count in defending_units.items())
    
    if attack_strength > defense_strength:
        st.session_state.map[target_row, target_col] = turn + 1
        st.session_state.units[enemy] = {}
        # Reduce the attacking units proportionally to their contribution to the attack strength
        for unit, count in attacking_units.items():
            loss_ratio = defense_strength / attack_strength
            st.session_state.units[turn][unit] = max(0, count - int(count * loss_ratio))
    else:
        # Reduce the defending units proportionally to their contribution to the defense strength
        for unit, count in defending_units.items():
            loss_ratio = attack_strength / defense_strength
            st.session_state.units[enemy][unit] = max(0, count - int(count * loss_ratio))
        st.session_state.units[turn] = {}

# Display map
st.write(f"Player {st.session_state.turn + 1}'s turn")
for row in range(map_height):
    cols = st.columns(map_width)
    for col in range(map_width):
        if st.session_state.map[row, col] == 0:
            button_label = f"🟤"
        else:
            button_label = f"P{st.session_state.map[row, col]}"
        cols[col].button(button_label, key=f"{row}-{col}", on_click=handle_click, args=(row, col))

# Recruitment UI
with st.sidebar:
    st.header("Recruit Units")
    for unit_type in units.keys():
        quantity = st.slider(f"Number of {unit_type}", 0, max_recruits_per_turn, key=f"recruit_{unit_type}")
        if st.button(f"Recruit {unit_type}", key=f"button_{unit_type}"):
            recruit_units(unit_type, quantity)

# End turn button
st.button("Next Turn", on_click=end_turn)

# Display resources and units
st.write(f"Resources for Player 1: {st.session_state.resources[0]}")
st.write(f"Resources for Player 2: {st.session_state.resources[1]}")
st.write(f"Player 1's units: {st.session_state.units[0]}")
st.write(f"Player 2's units: {st.session_state.units[1]}")
