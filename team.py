
##### Team Analysis

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as path_effects
from matplotlib.colors import to_rgba
from matplotlib import rcParams
from scipy.ndimage import gaussian_filter

from mplsoccer import Pitch, VerticalPitch, Sbopen

import pandas as pd
import numpy as np


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

events, related, freeze, players = parser.event(match_id_selected)
events = events[events["team_name"] == selected_team]

######################### TABS ###########################################

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Passing Network", "All Passes", "Pass Flow",
                                  "Shots", "HeatMaps"])
                      
with tab1:
    st.title("Passing Network of " + selected_team, )
    
    ############ PASSING NETWORK

    events.loc[events.tactics_formation.notnull(), 'tactics_id'] = events.loc[
        events.tactics_formation.notnull(), 'id']
    events[['tactics_id', 'tactics_formation']] = events.groupby('team_name')[[
        'tactics_id', 'tactics_formation']].ffill()

    formation_dict = {1: 'GK', 2: 'RB', 3: 'RCB', 4: 'CB', 5: 'LCB', 6: 'LB', 7: 'RWB',
                      8: 'LWB', 9: 'RDM', 10: 'CDM', 11: 'LDM', 12: 'RM', 13: 'RCM',
                      14: 'CM', 15: 'LCM', 16: 'LM', 17: 'RW', 18: 'RAM', 19: 'CAM',
                      20: 'LAM', 21: 'LW', 22: 'RCF', 23: 'ST', 24: 'LCF', 25: 'SS'}
    players['position_abbreviation'] = players.position_id.map(formation_dict)

    sub = events.loc[events.type_name == 'Substitution',
                     ['tactics_id', 'player_id', 'substitution_replacement_id',
                      'substitution_replacement_name']]
    players_sub = players.merge(sub.rename({'tactics_id': 'id'}, axis='columns'),
                                on=['id', 'player_id'], how='inner', validate='1:1')
    players_sub = (players_sub[['id', 'substitution_replacement_id', 'position_abbreviation']]
                   .rename({'substitution_replacement_id': 'player_id'}, axis='columns'))
    players = pd.concat([players, players_sub])
    players.rename({'id': 'tactics_id'}, axis='columns', inplace=True)
    players = players[['tactics_id', 'player_id', 'position_abbreviation']]

    # add on the position the player was playing in the formation to the events dataframe
    events = events.merge(players, on=['tactics_id', 'player_id'], how='left', validate='m:1')
    # add on the position the receipient was playing in the formation to the events dataframe
    events = events.merge(players.rename({'player_id': 'pass_recipient_id'},
                                         axis='columns'), on=['tactics_id', 'pass_recipient_id'],
                          how='left', validate='m:1', suffixes=['', '_receipt'])

    formation_options = events['tactics_formation'].unique().tolist()
    formation_options = [int(round(x, 0)) for x in formation_options]

    FORMATION = st.selectbox("Select Formation", formation_options)

    TEAM = selected_team

    pass_cols = ['id', 'position_abbreviation', 'position_abbreviation_receipt']
    passes_formation = events.loc[(events.team_name == TEAM) & (events.type_name == 'Pass') &
                                  (events.tactics_formation == FORMATION) &
                                  (events.position_abbreviation_receipt.notnull()), pass_cols].copy()
    location_cols = ['position_abbreviation', 'x', 'y']
    location_formation = events.loc[(events.team_name == TEAM) &
                                    (events.type_name.isin(['Pass', 'Ball Receipt'])) &
                                    (events.tactics_formation == FORMATION), location_cols].copy()

    # average locations
    average_locs_and_count = (location_formation.groupby('position_abbreviation')
                              .agg({'x': ['mean'], 'y': ['mean', 'count']}))
    average_locs_and_count.columns = ['x', 'y', 'count']

    # calculate the number of passes between each position (using min/ max so we get passes both ways)
    passes_formation['pos_max'] = (passes_formation[['position_abbreviation',
                                                    'position_abbreviation_receipt']]
                                   .max(axis='columns'))
    passes_formation['pos_min'] = (passes_formation[['position_abbreviation',
                                                    'position_abbreviation_receipt']]
                                   .min(axis='columns'))
    passes_between = passes_formation.groupby(['pos_min', 'pos_max']).id.count().reset_index()
    passes_between.rename({'id': 'pass_count'}, axis='columns', inplace=True)

    # add on the location of each player so we have the start and end positions of the lines
    passes_between = passes_between.merge(average_locs_and_count, left_on='pos_min', right_index=True)
    passes_between = passes_between.merge(average_locs_and_count, left_on='pos_max', right_index=True,
                                          suffixes=['', '_end'])

    MAX_LINE_WIDTH = 18
    MAX_MARKER_SIZE = 3000
    passes_between['width'] = (passes_between.pass_count / passes_between.pass_count.max() *
                               MAX_LINE_WIDTH)
    average_locs_and_count['marker_size'] = (average_locs_and_count['count']
                                             / average_locs_and_count['count'].max() * MAX_MARKER_SIZE)

    MIN_TRANSPARENCY = 0.3
    color = np.array(to_rgba('white'))
    color = np.tile(color, (len(passes_between), 1))
    c_transparency = passes_between.pass_count / passes_between.pass_count.max()
    c_transparency = (c_transparency * (1 - MIN_TRANSPARENCY)) + MIN_TRANSPARENCY
    color[:, 3] = c_transparency

    # Create a new figure
    figure_one = plt.figure()

    pitch = Pitch(pitch_type='statsbomb', pitch_color='#22312b', line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
    fig.set_facecolor("#22312b")
    pass_lines = pitch.lines(passes_between.x, passes_between.y,
                             passes_between.x_end, passes_between.y_end, lw=passes_between.width,
                             color=color, zorder=1, ax=ax)
    pass_nodes = pitch.scatter(average_locs_and_count.x, average_locs_and_count.y,
                               s=average_locs_and_count.marker_size,
                               color='red', edgecolors='black', linewidth=1, alpha=1, ax=ax)
    for index, row in average_locs_and_count.iterrows():
        pitch.annotate(row.name, xy=(row.x, row.y), c='white', va='center',
                       ha='center', size=16, weight='bold', ax=ax)
        
    # Assign the figure to the variable
    figure_one = fig
    st.pyplot(figure_one)

with tab2:
    st.title("All passes by " + selected_team)
    
    rcParams['text.color'] = '#c7d5cc'  # set the default text color
    
    mask_team = (events.type_name == 'Pass') & (events.team_name == selected_team)
    
    df_pass = events.loc[mask_team, ['x', 'y', 'end_x', 'end_y', 'outcome_name']]
    mask_complete = df_pass.outcome_name.isnull()
    
    # Create a new figure
    figure_two = plt.figure()
    
   # Set up the pitch
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#22312b', line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
    fig.set_facecolor('#22312b')
    
    # Plot the completed passes
    pitch.arrows(df_pass[mask_complete].x, df_pass[mask_complete].y,
                 df_pass[mask_complete].end_x, df_pass[mask_complete].end_y, width=2,
                 headwidth=10, headlength=10, color='#ad993c', ax=ax, label='completed passes')
    
    # Plot the other passes
    pitch.arrows(df_pass[~mask_complete].x, df_pass[~mask_complete].y,
                 df_pass[~mask_complete].end_x, df_pass[~mask_complete].end_y, width=2,
                 headwidth=6, headlength=5, headaxislength=12,
                 color='#ba4f45', ax=ax, label='other passes')
    
    # Set up the legend
    ax.legend(facecolor='#22312b', handlelength=5, edgecolor='None', fontsize=20, loc='upper left')
    
    # Assign the figure to the variable
    figure_two = fig
    st.pyplot(figure_two)
    
with tab3:
    st.title("Pass flow by " + selected_team)
    mask_team = (events.type_name == 'Pass') & (events.team_name == selected_team)
    df_pass = events.loc[mask_team, ['x', 'y', 'end_x', 'end_y', 'outcome_name']]
    mask_complete = df_pass.outcome_name.isnull()
    
    pitch = Pitch(pitch_type='statsbomb',  line_zorder=2, line_color='#c7d5cc', pitch_color='#22312b')
    bins = (6, 4)
    
    # Create a new figure
    figure_three = plt.figure()
    
    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
    fig.set_facecolor('#22312b')
    # plot the heatmap - darker colors = more passes originating from that square
    bs_heatmap = pitch.bin_statistic(df_pass.x, df_pass.y, statistic='count', bins=bins)
    hm = pitch.heatmap(bs_heatmap, ax=ax, cmap='Greens')
    # plot the pass flow map with a single color and the
    # arrow length equal to the average distance in the cell
    fm = pitch.flow(df_pass.x, df_pass.y, df_pass.end_x, df_pass.end_y, color='black',
                arrow_type='average', bins=bins, ax=ax)
    
    # Assign the figure to the variable
    figure_three = fig
    st.pyplot(figure_three)
    
with tab4:
    st.title("All shots by " + selected_team)
    shots = events.loc[events['type_name'] == 'Shot'].set_index('id')
    
    # Create a new figure
    figure_four = plt.figure()
    
    pitch = VerticalPitch(line_color='black', half = True)
    fig, ax = pitch.grid(grid_height=0.9, title_height=0.06, axis=False,
                     endnote_height=0.04, title_space=0, endnote_space=0)
    #plotting all shots
    pitch.scatter(shots.x, shots.y, alpha = 1, s = 500, color = "red", ax=ax['pitch'], edgecolors="black")
    
    # Assign the figure to the variable
    figure_four = fig
    st.pyplot(figure_four)

with tab5:
    actions_options = events['type_name'].unique().tolist()
    actions_options = sorted(actions_options[2:-5])
    selected_action = st.selectbox("Select action for HeatMap", actions_options)
    
    
    st.title("Heatmap of " + selected_action + " actions")
    
    mask = (events.team_name == selected_team) & (events.type_name == selected_action)
    df_action = events.loc[mask, ['x', 'y']]
    
    #setup pitch
    
    # Create a new figure
    figure_five = plt.figure()
    
    pitch = Pitch(pitch_type='statsbomb', line_zorder=2,
                  pitch_color='#22312b', line_color='#efefef')
    # draw
    fig, ax = pitch.draw(figsize=(6.6, 4.125))
    fig.set_facecolor('#22312b')
    bin_statistic = pitch.bin_statistic(df_action.x, df_action.y, statistic='count', bins=(25, 25))
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='hot', edgecolors='#22312b')
    # Add the colorbar and format off-white
    cbar = fig.colorbar(pcm, ax=ax, shrink=0.6)
    cbar.outline.set_edgecolor('#efefef')
    cbar.ax.yaxis.set_tick_params(color='#efefef')
    ticks = plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#efefef')
    
    # Assign the figure to the variable
    figure_five = fig
    st.pyplot(figure_five)
              
