import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.express.colors import sample_colorscale
from datetime import datetime, timedelta
from PIL import Image

def do_stuff_on_page_load():
    st.set_page_config(layout="wide")

do_stuff_on_page_load()

st.header('Theme Explorer', anchor=None)

#Set Sidebar Elements
with st.sidebar:
    st.header('Filters', anchor=None)
    values = st.slider(
        'Select the Start and End Years',
        1950, 2017, (1950, 2017))
    st.write('Date Range: '+str(values[0])+'-01-01 to '+str(values[1])+'-01-01')

#Import Data
df = st.session_state['df']
df_filtered = df[(df.year >= values[0]) & (df.year <= values[1])]
df_sets_to_theme = df_filtered[['year','parent_theme_name','theme_name','set_name','num_parts']].drop_duplicates()

#Explore the Themes to Sets relationship
with st.expander("Theme Explorer:",expanded=True):
    with st.spinner('Loading...'):
        df_themes_to_parts = df_filtered.groupby(['parent_theme_name','theme_name','set_name']).num_parts.sum().reset_index()
        list_parent_themes = df_themes_to_parts.groupby(['parent_theme_name']).set_name.nunique().sort_values(ascending=False).reset_index().parent_theme_name.tolist()

        chosen_theme = st.selectbox(
            'What theme do you want to explore?',
            list_parent_themes)

        df_sunburst = df_filtered[['parent_theme_name','theme_name','set_name']].drop_duplicates()
        df_sunburst['nbr'] = 1
        df_sunburst = df_sunburst.dropna()[df_sunburst.dropna()['parent_theme_name'].isin([chosen_theme])].reset_index()
        #df_sunburst = df_sunburst[df_sunburst.theme_name != df_sunburst.parent_theme_name]
        df_sunburst = df_sunburst[['theme_name','parent_theme_name','set_name','nbr']]

        fig_sunburst = px.sunburst(df_sunburst, 
                        path=['parent_theme_name','theme_name','set_name'], 
                        values='nbr',
                        height=1200,
                        color_discrete_sequence=px.colors.qualitative.Plotly)

        st.plotly_chart(fig_sunburst,use_container_width =True)

#Table Explorer
with st.expander("Theme Explorer:",expanded=True):
    with st.spinner('Loading...'):
        df_table_sets = df_filtered[['parent_theme_name','theme_name',
                                     'year','set_num',
                                     'set_name','num_parts',
                                     'part_num','part_name',
                                     'part_category_name','quantity',
                                     'color_name','is_trans']].drop_duplicates()
        st.dataframe(data=df_table_sets, use_container_width=True)
