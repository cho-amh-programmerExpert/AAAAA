import streamlit as st
import toml
import numpy as np

# Load the TOML file
config = toml.load("config.toml")

# Define the game state
units = config['units']
players = config['players']
provinces = config['provinces']
recruit_costs = config['recruit_costs']

# Initialize session state
if 'turn' not in st.session_state:
    st.session_state.turn = 1
    st.session_state.current_player = "Player1"
    st.session_state.units = units
    st.session_state.players = players
    st.session_state.provinces = provinces
    st.session_state.map_size = 2  # 2x2 map for simplicity
    st.session_state.selected_province = None

def switch_turn():
    if st.session_state.current_player == "Player1":
        st.session_state.current_player = "Player2"
    else:
        st.session_state.current_player = "Player1"
    st.session_state.turn += 1

def recruit(unit_type):
    player = st.session_state.current_player
    cost = recruit_costs[unit_type]
    if st.session_state.players[player]['resources'] >= cost:
        st.session_state.players[player]['resources'] -= cost
        st.session_state.players[player]['units'].append(unit_type)
        # Add unit to selected province
        province_id = st.session_state.selected_province
        st.session_state.provinces[province_id]['units'].append(unit_type)

def attack():
    province_id = st.session_state.selected_province
    province = st.session_state.provinces[province_id]
    attacker_units = province['units']
    
    adjacent_province_ids = get_adjacent_provinces(province_id)
    for adj_id in adjacent_province_ids:
        adj_province = st.session_state.provinces[adj_id]
        if adj_province['owner'] != st.session_state.current_player:
            defender_units = adj_province['units']
            if defender_units:
                attacker = st.session_state.units[attacker_units[0]]
                defender = st.session_state.units[defender_units[0]]
                damage = max(0, attacker['attack'] - defender['defense'])
                defender['health'] -= damage
                if defender['health'] <= 0:
                    adj_province['units'].remove(defender_units[0])
                if not adj_province['units']:
                    adj_province['owner'] = st.session_state.current_player
                break

def get_adjacent_provinces(province_id):
    row, col = divmod(int(province_id), st.session_state.map_size)
    adjacent = []
    for r, c in [(row-1, col), (row+1, col), (row, col-1), (row, col+1)]:
        if 0 <= r < st.session_state.map_size and 0 <= c < st.session_state.map_size:
            adjacent.append(str(r * st.session_state.map_size + c))
    return adjacent

# Display game state
st.title("Turn-Based Strategy Game")
st.write(f"Turn: {st.session_state.turn}")
st.write(f"Current Player: {st.session_state.current_player}")

st.header("Provinces")
map_matrix = np.zeros((st.session_state.map_size, st.session_state.map_size), dtype=int)

for i in range(st.session_state.map_size ** 2):
    row, col = divmod(i, st.session_state.map_size)
    province = st.session_state.provinces[str(i)]
    if province['owner'] == st.session_state.current_player:
        map_matrix[row, col] = 1

for row in range(map_matrix.shape[0]):
    cols = st.columns(map_matrix.shape[1])
    for col in range(map_matrix.shape[1]):
        province_id = row * st.session_state.map_size + col
        province = st.session_state.provinces[str(province_id)]
        if cols[col].button(f"{province['owner']}\nProv {province_id}"):
            st.session_state.selected_province = str(province_id)
            st.experimental_rerun()

st.header("Actions")

if st.session_state.selected_province:
    st.write(f"Selected Province: {st.session_state.selected_province}")

action = st.radio("Select Action", ["Recruit", "Attack", "End Turn"], index=2)

if action == "Recruit":
    unit_type = st.selectbox("Unit Type", list(units.keys()))
    if st.button("Recruit"):
        recruit(unit_type)
        st.experimental_rerun()

elif action == "Attack":
    if st.button("Execute Attack"):
        attack()
        st.experimental_rerun()

if action == "End Turn":
    if st.button("End Turn"):
        switch_turn()
        st.experimental_rerun()

st.header("Player Info")
player = st.session_state.players[st.session_state.current_player]
st.write(f"Resources: {player['resources']}")
st.write("Units:")
for unit_name in player['units']:
    unit = st.session_state.units[unit_name]
    st.write(f"{unit_name} - Attack: {unit['attack']}, Defense: {unit['defense']}, Health: {unit['health']}")
