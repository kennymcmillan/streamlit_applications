#### STREAMLIT APP FOR GRIEZMANN PROJECT

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from mplsoccer import Pitch, VerticalPitch, Sbopen
import pandas as pd


from PIL import Image

image = Image.open('C:/Users/kenny/Dropbox/Soccermatics/Project_code/Griezmann_project/WC2022logo.jpg') 

# Open parser
parser = Sbopen(dataframe=True)

# List of competitions available
competition = parser.competition()

# Get all matches from FIFA World Cup 2022
df_2022 = parser.match(43, 106)

match_descriptions = [row['home_team_name'] + " v " + row['away_team_name'] + " : " + row['competition_stage_name'] for index, row in df_2022.iterrows()]

#df_2022_matchid_list = df_2022['match_id'].unique().tolist()

#data_WC2022 = [parser.event(match) for match in df_2022_matchid_list]
#events_WC2022 = pd.concat(list(zip(*data_WC2022))[0], ignore_index=True)
# positions_WC2022 = pd.concat(list(zip(*data_WC2022))[3], ignore_index=True)

# all_home_teams = events_WC2022['home_team_name']
# all_away_teams = events_WC2022['away_team_name']
# #remove duplicates and sort alphabetically
# unique_teams = sorted(list(set(all_teams)))

# print(unique_teams)

# Create a sidebar
st.sidebar.image(image, use_column_width=True)
time.sleep(0.2)
st.sidebar.title("World Cup 2022 Analysis")


match_selected = st.sidebar.selectbox('Select Match', match_descriptions)

home_team = match_selected.split(' v ')[0]
away_team = match_selected.split(' v ')[1].split(' : ')[0]
competition_round = match_selected.split(' : ')[1]

# Create a new column with boolean values
df_2022['match_bool'] = (df_2022['home_team_name'].str.contains(home_team)) & (df_2022['away_team_name'].str.contains(away_team)) & (df_2022['competition_stage_name'].str.contains(competition_round))
# Get the match_id for the corresponding row
match_id_selected = df_2022.loc[df_2022['match_bool'] == True, 'match_id'].values[0]
comp_id_selected = df_2022.loc[df_2022['match_bool'] == True, 'competition_id'].values[0]

st.sidebar.write("Match ID is " + str(match_id_selected))

parser = Sbopen()
df = parser.event(match_id_selected)[0] 

# Get unique names in the player_name column
unique_names = df['player_name'].dropna().unique()

# Create a dropdown in Streamlit
player_selected = st. sidebar.selectbox("Select a player", unique_names)

df_actions = df.loc[df.player_name == player_selected , ['x', 'y']]

# Create a new figure
figure_one = plt.figure()
flamingo_cmap = LinearSegmentedColormap.from_list("Flamingo - 10 colors",
                                                  ['#e3aca7', '#c03a1d'], N=10)

# Make a hexbin plot
pitch = VerticalPitch(line_color='#000009', line_zorder=2, pitch_color='white')
fig, ax = pitch.draw(figsize=(4.4, 6.4))
hexmap = pitch.hexbin(df_actions.x, df_actions.y, ax=ax, edgecolors='#f4f4f4',
                      gridsize=(8, 8), cmap=flamingo_cmap)

# Assign the figure to the variable
figure_one = fig

# Add the graph to Streamlit
#st.pyplot(figure_one)

wc2022_passes = df.loc[(df["player_name"] == player_selected) & (df["type_name"] == "Pass")]
wc2022_passes = wc2022_passes[['x', 'y', 'end_x', 'end_y']]

# Create a new figure
figure_two = plt.figure()

pitch = Pitch(pitch_type='statsbomb',  line_color='#c7d5cc')
fig.set_facecolor('#22312b')
fig, ax = pitch.grid(grid_height=0.9, title_height=0.06, axis=False,
                     endnote_height=0.04, title_space=0, endnote_space=0)
pitch.arrows(wc2022_passes.x, wc2022_passes.y, wc2022_passes.end_x, wc2022_passes.end_y,
            color = "red", ax=ax['pitch'])
pitch.scatter(wc2022_passes.x, wc2022_passes.y, alpha = 0.4, s = 500, color = "blue", ax=ax['pitch'])

# Assign the figure to the variable
figure_two = fig

tab1, tab2 = st.tabs(["Actions", "Passes"])
                      
with tab1:
    st.title("All actions by " + player_selected, )
    st.pyplot(figure_one)

with tab2:
    st.title("All passes by " + player_selected)
    st.pyplot(figure_two)         

          
