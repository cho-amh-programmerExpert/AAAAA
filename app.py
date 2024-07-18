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
    st.session_state.armies = [None, None]

def end_turn():
    st.session_state.turn = 1 - st.session_state.turn

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
    elif st.session_state.armies[turn] is None:
        st.session_state.armies[turn] = (row, col)
    else:
        # Add logic for attacking/moving here
        pass

# Display map
st.write(f"Player {st.session_state.turn + 1}'s turn")
for row in range(map_height):
    cols = st.columns(map_width)
    for col in range(map_width):
        if st.session_state.map[row, col] == 0:
            button_label = f"{row},{col}"
        else:
            button_label = f"P{st.session_state.map[row, col]}"
        cols[col].button(button_label, key=f"{row}-{col}", on_click=handle_click, args=(row, col))

# Recruitment UI
with st.popover("Recruit Units"):
    for unit_type in units.keys():
        quantity = st.slider(f"Number of {unit_type}", 0, max_recruits_per_turn)
        if st.button(f"Recruit {unit_type}"):
            recruit_units(unit_type, quantity)

# End turn button
st.button("Next Turn", on_click=end_turn)

# Display resources and units
st.write(f"Resources for Player 1: {st.session_state.resources[0]}")
st.write(f"Resources for Player 2: {st.session_state.resources[1]}")
st.write(f"Player 1's units: {st.session_state.units[0]}")
st.write(f"Player 2's units: {st.session_state.units[1]}")
