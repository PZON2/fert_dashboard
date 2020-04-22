import pandas as pd
import plotly.express as px
import plotly as py
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly.graph_objects as go
from plotly.subplots import make_subplots

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']



df = pd.read_excel('Sample.xlsx')
gps = pd.read_excel('output.xlsx')

df1 = df[['Item ID', 'Brand', 'Country', 'Act net Sales at Act 2019 (EUR)', 'Act Net sales units 2019 (Eq. Units)', 'Act Total WCOGS 2019 (EUR)']]
df1.rename(columns={'Act net Sales at Act 2019 (EUR)':'Sales',
                   'Act Net sales units 2019 (Eq. Units)': 'Volume',
                   'Act Total WCOGS 2019 (EUR)': 'WCOGS'}, inplace=True)
df1['WCOGS'] = -df1['WCOGS']
df1['Country'] = df1['Country'].str[3:]
df1.loc[df1['Country'] =='Utd.Arab Emir.', 'Country']='UAE'
df1.loc[df1['Country'] =='Dominican Rep.', 'Country']='Dominican Republic'
df1.loc[df1['Country'] =='French Polynes.', 'Country']='French Polynesia'
df1.loc[df1['Country'] =='Serbia Kosavo', 'Country']='Serbia'
df1.loc[df1['Country'] =='Russian Fed.', 'Country']='Russia'

country_agg = df1.groupby('Country').agg('sum')
country_agg.reset_index(inplace=True)
df2 = pd.merge(df1, gps[['Country', 'lat', 'lon']], how='left', left_on='Country', right_on='Country')
brand_agg = df1.groupby('Brand').agg('sum')
brand_agg.reset_index(inplace=True)
brand_agg['NSP']=brand_agg['Sales']/brand_agg['Volume']
brand_agg['COGS']=brand_agg['WCOGS']/brand_agg['Volume']
brand_agg=brand_agg[['Brand', 'NSP', 'COGS']]
#country_brand_agg = df1.groupby(['Market', 'Brand']).agg('sum')
#country_brand_agg.reset_index(inplace=True)

#%%
brands = df2['Brand'].unique()
brands = np.append(brands, np.array(['All']))

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([
        html.Div(
            style={'width': '42%', 'backgroundColor': '#ffffff', 'display': 'inline-block',
                   'marginRight': '.8%', 'verticalAlign': 'top', 
                   'box-shadow':'0px 0px 10px #ededee', 'border': '1px solid #ededee','border-top': '#e36209 solid .2rem',},
            children=[
            
                html.Div([
                    html.Div(
                        style={'width': '48%', 'backgroundColor': '#ffffff', 'display': 'inline-block',
                        'marginRight': '.8%', 'verticalAlign': 'top', 
                        'box-shadow':'0px 0px 10px #ededee', 'border': '1px solid #ededee','border-top': '#e36209 solid .2rem',},
                        children=[
                            html.H5(
                                style={'textAlign': 'center', 'backgroundColor': '#ffffff', 'display': 'inline-block',
                                       'color': '#292929', 'padding': '1rem', 'marginBottom': '0','marginTop': '0'},
                                children='Select brands of choice'
                                ),
                            dcc.Dropdown(
                                id='brands',
                                options=[{'label': i, 'value': i} for i in brands],
                                value='All'),
                            ]),
                    
                    html.Div(
                        style={'width': '48%', 'backgroundColor': '#ffffff', 'display': 'inline-block',
                        'marginRight': '.8%', 'verticalAlign': 'top', 
                        'box-shadow':'0px 0px 10px #ededee', 'border': '1px solid #ededee','border-top': '#e36209 solid .2rem',},
                        children=[
                            html.H5(
                                style={'textAlign': 'center', 'backgroundColor': '#ffffff', 'display': 'inline-block',
                                       'color': '#292929', 'padding': '1rem', 'marginBottom': '0','marginTop': '0'},
                                children='Choose your gross margin benchmark (%)'
                                ),                            
                            dcc.Input(
                                id = 'gross_margin',
                                type = 'number',
                                min = 0,
                                max = 100,
                                value=80), 
                            ])
                    ]),
    
                html.H5(
                    style={'textAlign': 'center', 'backgroundColor': '#ffffff', 'display': 'inline-block',
                           'color': '#292929', 'padding': '1rem', 'marginBottom': '0','marginTop': '0'},
                    children='Countries with a GM > benchmark: Green    Countries with a GM < benchmark: Red'
                    ),
                dcc.Graph(
                    id = 'interactive-map')   
            
            ]),
    
        
        html.Div(
            style={'width': '55%', 'backgroundColor': '#ffffff', 'display': 'inline-block',
                   'marginRight': '.8%', 'verticalAlign': 'top', 
                   'box-shadow':'0px 0px 10px #ededee', 'border': '1px solid #ededee','border-top': '#e36209 solid .2rem',},
            children=[

                dcc.Graph(
                    id = 'country_deepdive')])
    ])

@app.callback(
    Output('interactive-map', 'figure'),
    [Input('brands', 'value'),
     Input('gross_margin', 'value')])
def update_graph(p, gross_margin_value):
    mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNqdnBvNDMyaTAxYzkzeW5ubWdpZ2VjbmMifQ.TXcBE-xg9BFdV2ocecc_7g"
    
    if p == 'All':
        dff = df2.groupby(['Country', 'lat', 'lon']).agg('sum')
    else:
        df3 = df2.loc[df2['Brand']== p]
        dff = df3.groupby(['Country', 'lat', 'lon']).agg('sum')
        
    dff.reset_index(inplace=True)
    dff['gm'] = (1- dff['WCOGS']/dff['Sales'])*100
    
    dff['round_sales'] = round(dff['Sales']/1000000, 2)
    dff['round_gm'] = round(dff['gm'], 0)

    dff['text'] = dff['Country'] + '<br>Sales: ' + dff['round_sales'].astype(str) + 'M€' \
        + '<br>Gross margin: ' + dff['round_gm'].astype(str) + '%'

    fig = go.Figure((go.Scattermapbox(
        lon = dff['lon'],
        lat = dff['lat'],
        mode='markers',
        text = dff['text'],
        hoverinfo='text',
        marker=go.scattermapbox.Marker(
            color=['#d7191c' if i <= gross_margin_value else '#1a9622' for i in dff['gm']],
            size=[i/100000  for i in dff['Sales']],
            sizemode='area')
        )))
    fig.update_layout(
        hovermode='closest',
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            style="light",
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=35,
                lon=0
            ),
            pitch=0,
            zoom=0.6,
        ))
    return fig

@app.callback(
    Output('country_deepdive', 'figure'),
    [Input('interactive-map', 'hoverData')])
def update_country_deepdive(hoverData):
    country_lon = hoverData['points'][0]['lon']
    df4 = df2.loc[df2['lon']== country_lon]
    df5=df4.groupby(['Country', 'Brand']).agg('sum')
    df5.reset_index(inplace=True)
    df5['NSP per eq. unit'] = df5['Sales']/df5['Volume']
    df5['WCOGS per eq. unit'] = df5['WCOGS']/df5['Volume']
    df5['gm']=(1-df5['WCOGS']/df5['Sales'])*100
    df5 = pd.merge(df5, brand_agg, how='left', left_on='Brand', right_on='Brand')
    
    fig1 = make_subplots(
        rows=1, cols=4,
        subplot_titles=("Sales(€)",
                        'Gross margin(%)',
                        "NSP(€/eq.unit)", 
                        "WCOGS(€/eq.unit)"),
        shared_xaxes=False,
        shared_yaxes=True)
    
    fig1.add_trace(go.Bar(
        x=df5['Sales'],
        y=df5['Brand'],
        orientation='h',
        marker_color='indianred'),
        1,1)
    
    fig1.add_trace(go.Bar(
        x=df5['gm'],
        y=df5['Brand'],
        orientation='h',
        marker_color='indianred'),
        1,2)

    fig1.add_trace(go.Bar(
        x=df5['NSP per eq. unit'],
        y=df5['Brand'],
        orientation='h',
        marker_color='indianred'),
        1,3)
    
    fig1.add_trace(go.Bar(
        x=df5['NSP'],
        y=df5['Brand'],
        orientation='h',
        marker_color='blue'),
        1,3)
    

    fig1.add_trace(go.Bar(
        x=df5['WCOGS per eq. unit'],
        y=df5['Brand'],
        orientation='h',
        marker_color='indianred'),
        1,4)
    
    fig1.add_trace(go.Bar(
        x=df5['COGS'],
        y=df5['Brand'],
        orientation='h',
        marker_color='blue'),
        1,4)
    
    
    fig1.update_layout(title_text='Country deep-dive:' + df5['Country'][0] + '<br>Blue: World Ave.    Red: Country', 
                       showlegend=False,
                       font=dict(
                            family="Courier New, monospace",
                            size=10,
                            color = '#292929'))

    return fig1
    
    
if __name__ == '__main__':
    app.run_server()
    
