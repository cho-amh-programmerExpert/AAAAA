import streamlit as st
import numpy as np
import toml

# Load config
config = toml.load("config.toml")
units = config["units"]
max_forces_per_turn = config["max_forces_per_turn"]["max"]

# Initialize game state
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        "map": np.zeros((10, 10)),  # 10x10 map
        "player_capitals": [None, None],
        "current_player": 0,
        "forces": [{}, {}],  # Forces for each player
        "resources": [100, 100],  # Starting resources for each player
        "turn": 1,
    }

def recruit_units(player, unit_type, quantity):
    if unit_type in units and quantity <= max_forces_per_turn:
        cost = units[unit_type]["cost"] * quantity
        if st.session_state.game_state["resources"][player] >= cost:
            st.session_state.game_state["resources"][player] -= cost
            if unit_type in st.session_state.game_state["forces"][player]:
                st.session_state.game_state["forces"][player][unit_type] += quantity
            else:
                st.session_state.game_state["forces"][player][unit_type] = quantity

def place_capital(player, x, y):
    if st.session_state.game_state["player_capitals"][player] is None:
        st.session_state.game_state["player_capitals"][player] = (x, y)
        st.session_state.game_state["map"][x, y] = player + 1

def move_forces(player, from_x, from_y, to_x, to_y):
    if st.session_state.game_state["map"][from_x, from_y] == player + 1:
        st.session_state.game_state["map"][from_x, from_y] = 0
        st.session_state.game_state["map"][to_x, to_y] = player + 1

def attack(player, from_x, from_y, to_x, to_y):
    if st.session_state.game_state["map"][from_x, from_y] == player + 1:
        enemy_player = 1 - player
        if st.session_state.game_state["map"][to_x, to_y] == enemy_player + 1:
            # Simulate battle
            player_forces = st.session_state.game_state["forces"][player]
            enemy_forces = st.session_state.game_state["forces"][enemy_player]

            player_attack = sum(units[ut]["attack"] * qty for ut, qty in player_forces.items())
            enemy_defense = sum(units[ut]["defense"] * qty for ut, qty in enemy_forces.items())

            if player_attack > enemy_defense:
                st.session_state.game_state["map"][to_x, to_y] = player + 1
                st.session_state.game_state["forces"][enemy_player] = {}

# UI for the map
for i in range(10):
    cols = st.columns(10)
    for j in range(10):
        with cols[j]:
            if st.session_state.game_state["map"][i, j] == 0:
                st.button("", key=f"{i}-{j}", on_click=place_capital, args=(st.session_state.game_state["current_player"], i, j))
            elif st.session_state.game_state["map"][i, j] == 1:
                st.button("P1", key=f"{i}-{j}", on_click=move_forces, args=(0, i, j, i, j))  # Modify for actual move logic
            elif st.session_state.game_state["map"][i, j] == 2:
                st.button("P2", key=f"{i}-{j}", on_click=move_forces, args=(1, i, j, i, j))  # Modify for actual move logic

# UI for recruiting units
with st.popover("Recruit Units"):
    quantity = st.slider("Quantity", min_value=1, max_value=max_forces_per_turn)
    for unit_type in units.keys():
        st.button(unit_type, on_click=recruit_units, args=(st.session_state.game_state["current_player"], unit_type, quantity))

# Next Turn Button
if st.button("End Turn"):
    st.session_state.game_state["current_player"] = 1 - st.session_state.game_state["current_player"]
    st.session_state.game_state["turn"] += 1

# Display current player's turn
st.toast(f"Player {st.session_state.game_state['current_player'] + 1}'s turn")

# Display resources
st.write(f"Player 1 Resources: {st.session_state.game_state['resources'][0]}")
st.write(f"Player 2 Resources: {st.session_state.game_state['resources'][1]}")
