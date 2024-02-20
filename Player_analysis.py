#### STREAMLIT APP FOR FREE STATSBOMB DATA

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


from mplsoccer import Pitch, VerticalPitch, Sbopen
import pandas as pd


from PIL import Image

#image = Image.open('C:/Users/kenny/Dropbox/Soccermatics/Project_code/Griezmann_project/statsbomb_image.png') 

#st.sidebar.image(image, use_column_width=True)

st.sidebar.title("Free Statsbomb data analysis")

# Open parser
parser = Sbopen(dataframe=True)

# List of competitions available
df = parser.competition()
df["competition_gender"] = df["competition_gender"].str.capitalize()

# lets get all options for dropdowns - select gender, competition and season
gender_options = df['competition_gender'].unique().tolist()

# select gender
selected_gender = st.sidebar.selectbox("Select Gender", gender_options)

# select competition
filtered_df = df[df['competition_gender'] == selected_gender]
competition_options = filtered_df['competition_name'].unique().tolist()
selected_competition = st.sidebar.selectbox("Select Competition", competition_options)

# select season
filtered_df2 = df[df['competition_name'] == selected_competition]
season_options = filtered_df2['season_name'].unique().tolist()
selected_season = st.sidebar.selectbox("Select Season", season_options)

# select team
filtered_df3 = filtered_df2[filtered_df2['season_name'] == selected_season]

# look up the season and competition IDs
selected_row = df[(df['competition_name'] == selected_competition) & (df['season_name'] == selected_season) & (df['competition_gender'] == selected_gender)]
season_id = selected_row['season_id'].values[0]
competition_id = selected_row['competition_id'].values[0]

# Get all matches from selected event PARSER MATCH
data_selected = parser.match(competition_id, season_id)

# concatenate columns
unique_home_entries = data_selected['home_team_name'].unique().tolist()
unique_away_entries = data_selected['away_team_name'].unique().tolist()
all_teams = unique_home_entries + unique_away_entries
all_teams_options = sorted(set(all_teams))

selected_team = st.sidebar.selectbox("Select Team", all_teams_options)

filtered_df_4 = data_selected[data_selected["home_team_name"].isin([selected_team]) | data_selected["away_team_name"].isin([selected_team])]

match_descriptions = [row['home_team_name'] + " v " + row['away_team_name'] + " : " + row['competition_stage_name'] for index, row in filtered_df_4.iterrows()]


match_selected = st.sidebar.selectbox('Select Match', match_descriptions)

home_team = match_selected.split(' v ')[0]
away_team = match_selected.split(' v ')[1].split(' : ')[0]
competition_round = match_selected.split(' : ')[1]

# Create a new column with boolean values
filtered_df_4['match_bool'] = (filtered_df_4['home_team_name'].str.contains(home_team)) & (filtered_df_4['away_team_name'].str.contains(away_team)) & (filtered_df_4['competition_stage_name'].str.contains(competition_round))
# Get the match_id for the corresponding row
match_id_selected = filtered_df_4.loc[filtered_df_4['match_bool'] == True, 'match_id'].values[0]
#comp_id_selected = data_selected.loc[data_selected['match_bool'] == True, 'competition_id'].values[0]

df_events = parser.event(match_id_selected)[0] 
df_events = df_events[df_events["team_name"] == selected_team]

# Get unique names in the player_name column
unique_names = sorted(df_events['player_name'].dropna().unique())

# Create a dropdown in Streamlit
player_selected = st. sidebar.selectbox("Select a player", unique_names)

######################### TABS #########################################

tab1, tab2 = st.tabs(["Actions", "Passes"])
                      
with tab1:
    st.title("All actions by " + player_selected, )
    
    df_actions = df_events.loc[df_events.player_name == player_selected , ['x', 'y']]

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
    
    st.pyplot(figure_one)

with tab2:
    st.title("All passes by " + player_selected)
    
    passes = df_events.loc[(df_events["player_name"] == player_selected) & (df_events["type_name"] == "Pass")]
    passes = passes[['x', 'y', 'end_x', 'end_y']]

    # Create a new figure
    figure_two = plt.figure()

    pitch = Pitch(pitch_type='statsbomb',  line_color='#c7d5cc')
    fig.set_facecolor('#22312b')
    fig, ax = pitch.grid(grid_height=0.9, title_height=0.06, axis=False,
                         endnote_height=0.04, title_space=0, endnote_space=0)
    pitch.arrows(passes.x, passes.y, passes.end_x, passes.end_y,
                color = "red", ax=ax['pitch'])
    pitch.scatter(passes.x, passes.y, alpha = 0.4, s = 500, color = "blue", ax=ax['pitch'])

    # Assign the figure to the variable
    figure_two = fig
    
    st.pyplot(figure_two)      
