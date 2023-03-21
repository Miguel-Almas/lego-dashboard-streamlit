import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.express.colors import sample_colorscale
from datetime import datetime, timedelta

df = pd.read_csv('df_combined_lego.csv')

#Set Header
#image = Image.open('lego-bricks.jpeg')

#st.image(image, caption='Lego Bricks')
st.header('Lego Sets Explorer', anchor=None)

#Set Sidebar Elements
with st.sidebar:
    st.header('Filters', anchor=None)
    values = st.slider(
        'Select the Start and End Years',
        1950, 2017, (1950, 2017))
    st.write('Date Range: '+str(values[0])+'-01-01 to '+str(values[1])+'-01-01')

@st.cache_data  # 👈 caching decorator
def load_data(url):
    df = pd.read_pickle(url)  # 👈 Download the data
    return df

for i in range(4):
    if i == 0:
        df = load_data(f'df_combined_lego_part{i+1}.pkl')
    else:
        df = pd.concat((df,load_data(f'df_combined_lego_part{i+1}.pkl')))
st.session_state['df'] = df

df_filtered = df[(df.year >= values[0]) & (df.year <= values[1])]

#Cards with Number of New Master Themes, Themes, Sets and Parts
col1, col2, col3, col4 = st.columns(4)

with st.spinner('Loading...'):
    #New Master Themes (considering first year of appearance)
    metric_new_master_themes = df.groupby('parent_theme_name').year.min().reset_index()
    metric_new_master_themes = metric_new_master_themes[(metric_new_master_themes.year >= values[0]) & (metric_new_master_themes.year <= values[1])]
    col1.metric("New Master Themes", int(metric_new_master_themes.parent_theme_name.nunique()))

with st.spinner('Loading...'):
    #New Themes (considering first year of appearance)
    metric_new_themes = df.groupby('theme_name').year.min().reset_index()
    metric_new_themes = metric_new_themes[(metric_new_themes.year >= values[0]) & (metric_new_themes.year <= values[1])]
    col2.metric("New Themes", int(metric_new_themes.theme_name.nunique()))

with st.spinner('Loading...'):
    #New Sets (considering first year of appearance)
    metric_new_sets = df.groupby('set_name').year.min().reset_index()
    metric_new_sets = metric_new_sets[(metric_new_sets.year >= values[0]) & (metric_new_sets.year <= values[1])]
    col3.metric("New Sets", int(metric_new_sets.set_name.nunique()))

with st.spinner('Loading...'):
    #New Sets (considering first year of appearance)
    metric_new_sets_parts = df.groupby(['set_name','num_parts']).year.min().reset_index()
    metric_new_sets_parts = metric_new_sets_parts[(metric_new_sets_parts.year >= values[0]) & (metric_new_sets_parts.year <= values[1])]
    col4.metric("Parts of New Sets", int(metric_new_sets_parts[['set_name','num_parts']].drop_duplicates().num_parts.sum()))

#Get Top N Themes
filt_n_themes = st.slider('Consider the Top N Master Themes:',min_value=1, max_value=20, value=10)

with st.expander(f"New Sets of the Top {filt_n_themes} Master Themes",expanded=True):
    with st.spinner('Loading...'):
        #Prepare sample of colors
        #x = np.linspace(0, 1, filt_n_themes)
        #colors_scaled = sample_colorscale('Portland', list(x))
        colors_scaled = ["#1F78C8","#ff0000","#33a02c","#6A33C2","#ff7f00","#565656",
            "#FFD700","#a6cee3","#FB6496","#b2df8a","#CAB2D6","#FDBF6F",
            "#999999","#EEE685","#C8308C","#FF83FA","#C814FA","#0000FF",
            "#36648B","#00E2E5","#00FF00","#778B00","#BEBE00","#8B3B00",
            "#A52A3C"]

        #Show the Number of New Sets associated with the Top N Master Themes
        df_themes_to_parts = df_filtered.groupby(['parent_theme_name','theme_name','set_name']).num_parts.sum().reset_index()
        sets_per_parent_theme = df_themes_to_parts.groupby(['parent_theme_name']).set_name.nunique().sort_values(ascending=False).reset_index()[:filt_n_themes]
        nbr_sets_remained = df_themes_to_parts.groupby(['parent_theme_name']).set_name.nunique().sort_values(ascending=False).reset_index()[filt_n_themes:].set_name.sum()
        dict_colors = dict(zip(sets_per_parent_theme.parent_theme_name.sort_values().tolist(),colors_scaled))
        sets_per_parent_theme['colors'] = sets_per_parent_theme.parent_theme_name.map(dict_colors)
        sets_per_parent_theme = pd.concat((sets_per_parent_theme,pd.DataFrame({'parent_theme_name':'Remainder',
                'set_name':nbr_sets_remained,
                'colors':'#808080'},
                index=[filt_n_themes])))

        #Make sure the colors are well assigned to a specific category so they match across graphs
        fig_parent_theme = px.bar(sets_per_parent_theme,
            y='parent_theme_name',
            x='set_name',
            color='parent_theme_name',
            title=f'Number of Distinct Lego Sets per Master Theme (Top {filt_n_themes})',
            color_discrete_sequence=sets_per_parent_theme.colors)
        fig_parent_theme.update_layout(yaxis_title='', 
                        xaxis_title='Number Distinct Sets')
        fig_parent_theme.update_yaxes(automargin=True)
        st.plotly_chart(fig_parent_theme,use_container_width =True)

with st.expander(f"New Sets of the Top {filt_n_themes} Master Themes over the Years",expanded=True):
    with st.spinner('Loading...'):
        #Show the Number of New Sets associated with the Top N Master Themes
        sets_master_themes_per_first_year = df_filtered[['year','parent_theme_name','set_name']].groupby(['parent_theme_name','set_name']).year.min().reset_index()
        sets_per_year_master_theme = sets_master_themes_per_first_year.groupby(['year','parent_theme_name']).set_name.nunique().reset_index()
        sets_per_year_master_theme_top = sets_per_year_master_theme[sets_per_year_master_theme['parent_theme_name'].isin(sets_per_parent_theme.parent_theme_name.tolist())].copy().sort_values('parent_theme_name')
        sets_per_year_master_theme_top['colors'] = sets_per_year_master_theme_top.parent_theme_name.map(dict_colors)
        #Get the remainders
        sets_per_year_master_theme_remainder = sets_per_year_master_theme[~sets_per_year_master_theme['parent_theme_name'].isin(sets_per_parent_theme.parent_theme_name.tolist())].copy()
        sets_per_year_master_theme_remainder = sets_per_year_master_theme_remainder.groupby('year').set_name.sum().reset_index()
        sets_per_year_master_theme_remainder['parent_theme_name'] = 'Remainder'
        sets_per_year_master_theme_remainder['colors'] = '#808080'
        #Merge both
        sets_per_year_master_theme = pd.concat((sets_per_year_master_theme_top,sets_per_year_master_theme_remainder))
        fig_sets_per_master = px.bar(sets_per_year_master_theme, 
                    x="year", 
                    y="set_name", 
                    color='parent_theme_name',
                    title=f'Number of New Sets per Year for Top {filt_n_themes} Master Themes',
                    color_discrete_sequence=colors_scaled[:filt_n_themes]+['#808080'])
        fig_sets_per_master.update_layout(xaxis_title='Year', 
                        yaxis_title='Number of New Sets')
        st.plotly_chart(fig_sets_per_master,use_container_width =True)

#Get Largest Lego Set per Year
with st.expander("Largest Lego Set per Year",expanded=True):
    with st.spinner('Loading...'):
        df_sets_to_theme = df_filtered[['year','parent_theme_name','theme_name','set_name','num_parts']].drop_duplicates()
        df_sets_to_theme['theme_set'] = df_sets_to_theme['theme_name'] + ' - ' + df_sets_to_theme['set_name'] #
        df_sets_to_theme = df_sets_to_theme.groupby(['year','parent_theme_name','theme_set']).num_parts.sum().reset_index().\
            sort_values('num_parts',ascending=False)
        df_sets_to_theme['rank'] = df_sets_to_theme.groupby('year').num_parts.rank(ascending=False)
        #Get the largest set of every year
        largest_set_year = df_sets_to_theme.query('rank == 1').sort_values('year',ascending=False)

        fig_largest_set_year = px.bar(largest_set_year,
            x='year',
            y='num_parts',
            color='parent_theme_name',
            title='Largest Set of Every Year', 
            color_discrete_sequence=colors_scaled,
            hover_name = 'theme_set')
        fig_largest_set_year.update_layout(xaxis_title='Year', yaxis_title='Number of New Parts per Set')

        fig_largest_set_year.add_trace(
            go.Scatter(
                x=largest_set_year.year,
                y=largest_set_year.num_parts,
                mode='lines', 
                line={'dash': 'dash', 'color': 'black'},
                showlegend=False
            ))
        st.plotly_chart(fig_largest_set_year,use_container_width =True)

#Free table explorer
with st.expander("Free Table Explorer:",expanded=True):
    with st.spinner('Loading...'):
        df_table = df_filtered[['year','parent_theme_name','theme_name','set_name','num_parts']].drop_duplicates()
        st.dataframe(data=df_table, use_container_width=True)
