import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.express.colors import sample_colorscale
from datetime import datetime, timedelta
from PIL import Image
from discord import SyncWebhook, File
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.stattools import pacf, acf
from sklearn.metrics import mean_squared_error

def do_stuff_on_page_load():
    st.set_page_config(layout="wide")

def create_corr_plot(series, plot_pacf=False):
    corr_array = pacf(series.dropna(), alpha=0.05) if plot_pacf else acf(series.dropna(), alpha=0.05)
    lower_y = corr_array[1][:,0] - corr_array[0]
    upper_y = corr_array[1][:,1] - corr_array[0]

    fig = go.Figure()
    for i in range(len(corr_array[0])):
        fig.add_scatter(x=(i,i), y=(0,corr_array[0][i]), mode='lines',line_color='#3f3f3f')
    fig.add_scatter(x=np.arange(len(corr_array[0])), y=corr_array[0], mode='markers', marker_color='#1f77b4',
                marker_size=12)
    fig.add_scatter(x=np.arange(len(corr_array[0])), y=upper_y, mode='lines', line_color='rgba(255,255,255,0)')
    fig.add_scatter(x=np.arange(len(corr_array[0])), y=lower_y, mode='lines',fillcolor='rgba(32, 146, 230,0.3)',
            fill='tonexty', line_color='rgba(255,255,255,0)')
    fig.update_traces(showlegend=False)
    fig.update_xaxes(range=[-1,15])
    fig.update_yaxes(zerolinecolor='#000000')
    
    title='Partial Autocorrelation (PACF)' if plot_pacf else 'Autocorrelation (ACF)'
    fig.update_layout(title=title)
    return fig


do_stuff_on_page_load()

st.header('ARIMA Model Forecaster', anchor=None)
st.text('In this page you will be able to perform the entire ARIMA flow. Start by choosing the order of differencing that ensures stationarity.')

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

#Make Forecaster (simple ARIMA) and display
#Prepare Data for Model
df_nbr_sets_year = df_filtered[['year','set_num']].drop_duplicates().groupby('year').count().reset_index().rename(columns={'set_num':'nbr_sets'})
df_nbr_sets_year['date']= '31-12-'+df_nbr_sets_year.year.astype(int).astype(str)
df_nbr_sets_year['date'] = pd.to_datetime(df_nbr_sets_year['date'],dayfirst=True)
df_nbr_sets_year = df_nbr_sets_year.set_index('date')
df_nbr_sets_year = df_nbr_sets_year.asfreq(freq='Y')
df_nbr_sets_year['nbr_sets'] = df_nbr_sets_year.nbr_sets.fillna(0)
df_train = df_nbr_sets_year.iloc[:-5]
df_test = df_nbr_sets_year.iloc[-5:]

with st.container():
    order_differencing = st.slider('Order of Differencing:',min_value=0, max_value=2, value=1)
    if order_differencing == 0:
        df_train['nbr_sets_diff'] = df_train.nbr_sets
    else:
        df_train['nbr_sets_diff'] = df_train.nbr_sets.diff(order_differencing)
    #Use Augmented Dickey-Fuller test for stationarity check
    results_adfuller = adfuller(df_train.nbr_sets_diff.dropna())
    st.text(f'ADF Statistic: {results_adfuller[0]}')
    st.text(f'p-value: {results_adfuller[1]}')

    #Print the Differenced timeseries
    fig_diff = px.line(df_train, 
              x="year", 
              y="nbr_sets_diff", 
              title=f'Number of Sets After {order_differencing} Order Differencing',
              color_discrete_sequence=px.colors.qualitative.Plotly)
    fig_diff.update_layout(xaxis_title='Year', yaxis_title='Differenced Number of Parts per Set')
    st.plotly_chart(fig_diff,use_container_width =True)

    #Plot the ACF and PACF
    fig_acf = create_corr_plot(df_train['nbr_sets_diff'].dropna(),plot_pacf=False)
    fig_pacf = create_corr_plot(df_train['nbr_sets_diff'],plot_pacf=True)

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(fig_acf,use_container_width =True)
    with col2:
        st.plotly_chart(fig_pacf,use_container_width =True)

    #Accept user inputs for the ARIMA
    col1, col2 = st.columns(2)

    st.text('With the ACF and PACF you should have hints to the hyperparameters that could be used on the ARIMA.')

    with col1:
        param_p = st.number_input('Insert the value of hyperparameter p',min_value=0,max_value=10,value=0,step=1,format='%i')
    with col2:
        param_q = st.number_input('Insert the value of hyperparameter q',min_value=0,max_value=10,value=0,step=1,format='%i')
    
    #Initialize and fit your first guess for ARIMA hyperparameters
    arima = ARIMA(df_train.nbr_sets,order=(param_p,1,param_q))
    arima_model = arima.fit()

    fig_arima = go.Figure()
    fig_arima.add_trace(
        go.Scatter(
            x=df_nbr_sets_year.index, 
            y=df_nbr_sets_year.nbr_sets,
            mode='lines', 
            line={'color':px.colors.qualitative.Plotly[0]},
            name="Actual Values"
        ))
    fig_arima.add_trace(
        go.Scatter(
            x=df_nbr_sets_year.index, 
            y=arima_model.predict(start=0,end=67),
            mode='lines', 
            line={'dash': 'dash', 'color': px.colors.qualitative.Plotly[1]},
            name="ARIMA Predicted Values"
        ))

    fig_arima.update_layout(title= 'Number of New Sets per Year and ARIMA Predictions', xaxis_title='Year', yaxis_title='Number of New Sets')
    st.plotly_chart(fig_arima,use_container_width =True)
    fig_arima.write_image("arima_forecast.png")

    #Print Test Set RMSE
    preds_arima = arima_model.forecast(5)
    st.text(f"On the test set, for RMSE is {np.sqrt(mean_squared_error(df_test.nbr_sets,preds_arima)):.2f}")

if st.button('Send Forecasts to Discord'):
    webhook_url = st.text_input('Insert the Discord Webhook URL here!')
    webhook = SyncWebhook.from_url(webhook_url)
    webhook.send("The latest ARIMA forecast is in!")
    webhook.send(file=File('arima_forecast.png'))

    st.write('Forecasts sent!')
