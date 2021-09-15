import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
from app import app
import collections
import json
from pprint import pprint
from jsondiff import diff
from dash import no_update
from apps.util import *

id = id_factory('impute_time_series_missing_data')

# Layout
layout = html.Div([
    dcc.Store(id='input_data_store', storage_type='session'),
    dcc.Store(id=id('slider_merge_store'), storage_type='session'),
    dcc.Store(id='selection_list_store', storage_type='session'), # TODO remove
    dcc.Store(id=id('selection_list_store'), storage_type='session'),
    dcc.Store(id=id('merge_strategy_store'), storage_type='session'),
    dcc.Store(id=id('json_store_1'), storage_type='session'),
    dcc.Store(id=id('json_store_2'), storage_type='session'),

    dbc.Container([
        # Page Title
        dbc.Row(dbc.Col(html.H2('Impute Time Series Missing Data')), style={'textAlign':'center'}),

        # Datatable & Selected Rows/Json List
        dbc.Row([
            dbc.Col(html.H5('Step 1: Select Column to Impute Data'), width=12),
            dbc.Col(html.Div(generate_datatable('input_datatable')), width=12),
            dbc.Col(html.Div(generate_slider('slider_merge'), style={'display':'hidden'}), width=12),
            dbc.Col(html.H5('Column Selected: None', id=id('selection_list')), width=12),
            
        
        dbc.Row([
            dbc.Col(html.H5('Action: '), width=3),
            dbc.Col(dcc.Dropdown(
                id='demo-dropdown',
                options=[
                    {'label': 'Remove NaN', 'value': 'removeNaN'},
                    {'label': 'SimpleImputer', 'value': 'NYC'},
                    {'label': 'Moving Average', 'value': 'MTL'},
                    {'label': 'Exponential Moving Average', 'value': 'SF'}
                ],
                value='NYC'
            ), width=9),
            dbc.Col(html.Button('Confirm', className='btn-secondary', id='button_confirm'), width=6),
            dbc.Col(html.Button('Undo', className='btn-secondary', id='button_undo'), width=6),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
        ], className='text-center', style={'margin': '5px'}),

        dbc.Row([
            
        ], className='text-center', style={'margin': '5px'}),
        
    ], style={'width':'100%', 'maxWidth':'100%'}),
    
])


@app.callback(Output(id('selection_list_store'), 'data'), Input('input_datatable', 'selected_columns'))
def save_selected_column(selected_columns):
    return selected_columns

@app.callback(Output(id('selection_list'), 'children'), Input(id('selection_list_store'), 'data'))
def generate_selected_column(selected_columns):
    return 'Column Selected: ' , str(selected_columns[0])