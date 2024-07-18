import streamlit as st
from streamlit_antd_components import divider as sac_divider
from streamlit_extras.let_it_rain import rain as rain_emoji
#from CustomModules.initializer import initial_run, set_page_info
import numpy as np
import random
import toml

#set_page_info("Pixel Territories", "🚩")

# Load configuration from a TOML file
config = toml.load('config.toml')

# Configuration variables
bonus_turn = config['bonus_turn']
max_water_province_percentage = config['max_water_province_percentage']
max_grid_size = config["max_grid_size"]
army_config = config['army']
avr_rarity = np.mean([x["rarity"] for x in army_config])
st.write(avr_config)

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

    # Initialize army for each player
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
            if len(st.session_state['armies'][current_player]) == 0:
                switch_player()
                return

            opponent_players = [i for i in opponent_players if i not in st.session_state['removed_players']]
            if (st.session_state['map'][row, col] == 0 or st.session_state['map'][row, col] in opponent_players) and is_adjacent_to_player(row, col, current_player):
                if st.session_state['map'][row, col] in opponent_players:
                    # Engage in battle
                    opponent = st.session_state['map'][row, col]
                    if not battle(current_player, opponent):
                        return

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

                if (row, col) == st.session_state['special_province']:
                    st.session_state['special_owner'] = current_player
                    update_moves_left()
                else:
                    gain_army(current_player)

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

    def gain_army(player):
        units = list(army_config.keys())
        probabilities = [100 - army_config[unit]['rarity'] for unit in units]
        total_probability = sum(probabilities)
        normalized_probabilities = [p / total_probability for p in probabilities]
        gained_unit = random.choices(units, weights=normalized_probabilities, k=1)[0]
        st.session_state['armies'][player].append(army_config[gained_unit])
        st.toast(icon=":crossed_swords:", body=f"**:green[Player {player}] gained a {gained_unit} unit!**")

    def battle(attacker, defender):
        attacker_army = st.session_state['armies'][attacker]
        defender_army = st.session_state['armies'][defender]

        if not attacker_army:
            return False

        attack_strength = sum(unit['attack'] for unit in attacker_army)
        defense_strength = sum(unit['defense'] for unit in defender_army)

        if attack_strength >= defense_strength:
            st.session_state['armies'][attacker] = []
            st.session_state['armies'][defender] = []
            return True
        else:
            st.session_state['armies'][attacker] = []
            return False

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
        water_per_inp = st.slider("**Water Province Percentage:**", min_value=0, max_value=max_water_province_percentage, value=int(str(float(max_water_province_percentage/2)).split(".")[0]), step=1)

        if st.button("🚩 Start Game 🚩", use_container_width=True):
            invalid_names = ["🟫", "🔰", "⭐️"]
            if any(name.replace(" ", "") in invalid_names for name in default_names):
                st.warning(icon=":material/error:", body="Don't use :red[']```🟢```:red['] or :red[']```🔰```:red['] in your country names!")
            else:
                if any(name == "" for name in default_names):
                    st.toast(icon="🔻", body="Please enter names for all countries!")
                else:
                    reset(x, y, num_players, default_names, water_per_inp)
                    st.session_state['phase'] = 'capital_selection'
                    st.rerun()

    # Check if country names are set
    if st.session_state['phase'] == 'name_selection':
        input_country_names()

    st.header("🚩 Pixel Territories 🚩", divider="violet")

    if st.session_state['phase'] == 'capital_selection':
        st.toast(icon=":material/things_to_do:", body=f"**:orange[Player {st.session_state['current_player']}] :red[(]```{st.session_state['country_names'][st.session_state['current_player']]}```:red[)], select your capital:red[.]**")

    elif st.session_state['phase'] == 'gameplay':
        st.info(icon=":material/cycle:", body=f"**:rainbow[Current Player]:red[:] Player#{st.session_state['current_player']} :red[(]{st.session_state['country_names'][st.session_state['current_player']]}:red[)]**")
        st.toast(icon=":material/cycle:", body=f"**:rainbow[Current Player]:red[:] Player#{st.session_state['current_player']} :red[(]{st.session_state['country_names'][st.session_state['current_player']]}:red[)]**")
        st.info(icon=f":material/counter_{st.session_state['moves_left']}:", body=f"**:orange[Moves Left]:red[:] {st.session_state['moves_left']}**")
    elif 'wins' in st.session_state['phase']:
        winner = st.session_state['phase'].split('_')[1]

        st.toast(icon=":material/celebration:", body=f"**:rainbow-background[:blue[Player {winner}] :red[(]```{st.session_state['country_names'][int(winner)]}```:red[)] wins!]**")
        st.success(icon=":material/celebration:", body=f"**:rainbow-background[:blue[Player {winner}] :red[(]```{st.session_state['country_names'][int(winner)]}```:red[)] wins!]**")
        rain_emoji("🍾", 45, 5, '3s')

    with st.sidebar:
        if st.button("**:orange[Another Match!]**", use_container_width=True):
            reset(x, y, num_players, default_names)
            input_country_names()

    with st.sidebar.expander("**Help:**", expanded=True):
        for player, name in st.session_state['country_names'].items():
            color = nation_colors[player]
            st.write(f"**Color :{color}[{color.title()}] → Player #{player} :red[(]```{name}```:red[)]**")

        st.divider()

        st.write("```🔰``` → Capital")
        st.write(f"```⭐``` → Special Province (capture to gain ```{bonus_turn}``` moves per turn)")

        st.divider()

        st.write("🎯 **Objective/Winner** 🎯 → Whoever Captures All Of The Capitals.")

        st.divider()

        st.write("**:blue[Basic Rules]:red[:]**")
        st.write("- You will still get a turn while you have at least ```1``` province (Even with the capital fallen).")
        st.write("- The fallen Player(s) will get a turn. But as the roles suggest, that turn will be skipped by simply picking a random pixel.")

    st.divider()

    # Display the map
    display_map()
    st.write(st.session_state.armies)

try:
    #initial_run(lambda: app())
    app()
except:
    pass
