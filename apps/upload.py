from dash import dcc, html, dash_table, no_update, callback_context
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
from app import app
import dash_bootstrap_components as dbc
import json
import io
import sys
from flatten_json import flatten, unflatten, unflatten_list
from jsonmerge import Merger
from pprint import pprint
from genson import SchemaBuilder
import json
from jsondiff import diff, symbols
from apps.util import *
import base64
import pandas as pd
from itertools import zip_longest
from datetime import datetime
from pandas import json_normalize
from pathlib import Path
from apps.typesense_client import *
import time

from pathlib import Path
import uuid
import dash_uploader as du



def get_upload_component(id):
    return du.Upload(
        id=id,
        max_file_size=1,  # 1 Mb
        filetypes=['csv', 'json', 'jsonl'],
        upload_id=uuid.uuid1(),  # Unique session id
        max_files=100,
        default_style={'height':'150px'},
    )


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
UPLOAD_FOLDER_ROOT = r"C:\tmp\Uploads"
du.configure_upload(app, UPLOAD_FOLDER_ROOT)
id = id_factory((__file__).rsplit("\\", 1)[1].split('.')[0]) # Prepend filename to id
tab_labels = ['Step 1: Create or Load Dataset', 'Step 2: Upload API']
tab_values = [id('create_load_dataset'), id('upload_api')]
datatype_list = ['object', 'Int64', 'float64', 'bool', 'datetime64', 'category']

dataset_type = [
    {'label': 'Numerical', 'value': 'numerical'},
    {'label': 'Categorical', 'value': 'categorical'},
    {'label': 'Hybrid', 'value': 'hybrid'},
    {'label': 'Time Series', 'value': 'time_series'},
    {'label': 'Geo Spatial', 'value': 'geo_spatial'},
]
option_delimiter = [
    {'label': 'Comma (,)', 'value': ','},
    {'label': 'Tab', 'value': "\\t"},
    {'label': 'Space', 'value': "\\s+"},
    {'label': 'Pipe (|)', 'value': '|'},
    {'label': 'Semi-Colon (;)', 'value': ';'},
    {'label': 'Colon (:)', 'value': ':'},
]


# Layout
layout = html.Div([
    dcc.Store(id='current_dataset', storage_type='session'),
    dcc.Store(id='current_node', storage_type='session'),
    # dcc.Store(id=id('api_list'), storage_type='memory'),    
    # dcc.Store(id='dataset_profile', storage_type='session'),
    # dcc.Store(id=id('remove_list'), storage_type='session'),

    generate_tabs(id('tabs_content'), tab_labels, tab_values),
    dbc.Container([], fluid=True, id=id('content')),
    html.Div(id='test1'),
])


dropdown_menu_items = [
    dbc.DropdownMenuItem("Deep thought", id="dropdown-menu-item-1"),
    dbc.DropdownMenuItem("Hal", id="dropdown-menu-item-2"),
    dbc.DropdownMenuItem(divider=True),
    dbc.DropdownMenuItem("Clear", id="dropdown-menu-item-clear"),
]

# Tab Content
@app.callback(Output(id("content"), "children"), [Input('url', 'pathname'), Input(id("tabs_content"), "value")])
def generate_tab_content(pathname, active_tab):
    content = None
    if active_tab == id('create_load_dataset'):
        content = html.Div([
            dbc.Row(dbc.Col(html.H2('Step 1: Create or Load Existing Dataset')), style={'text-align':'center'}),
            dbc.Row([
                dbc.Col([
                    dbc.Input(id=id('input_dataset_name'), placeholder="Enter Dataset Name", size="lg", style={'text-align':'center'}),
                    html.Div(generate_dropdown(id('dropdown_dataset_type'), dataset_type, placeholder='Select Type of Dataset'), style={'width':'100%', 'display':'inline-block'}),
                    dbc.Button("Create Dataset", id=id('button_create_load_dataset'), size="lg"),
                ], width={"size": 6, "offset": 3})
            ], align="center", style={'height':'700px', 'text-align':'center'})
        ])

    if active_tab == id('upload_api'):
        content = html.Div([
            # Settings & Drag and Drop
            dbc.Row([
                dbc.Col([
                    html.H5('Step 1.1: API Description'),
                    dbc.InputGroup([
                        dbc.InputGroupText("Node ID", style={'width':'120px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'30px'}), 
                        dbc.Input(id=id('node_id'), disabled=True, style={'font-size': '12px', 'text-align':'center'})
                    ], className="mb-3 lg"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Description", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                        dbc.Textarea(id=id('node_description'), placeholder='Enter API Description (Optional)', style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                    ], className="mb-3 lg"),
                ], width={'size':8, 'offset':2}, className='rounded bg-info text-dark'),
                dbc.Col(html.Hr(style={'border': '1px dotted black', 'margin': '30px 0px 30px 0px'}), width=12),
            ], className='text-center', style={'margin': '1px'}),
            
            dbc.Row([
                dbc.Col([
                    html.H5('Step 1.2: Select Files'),
                    html.Div(get_upload_component(id=id('browse_drag_drop'))),
                ], width={'size':4, 'offset':0}),
                dbc.Col([
                    html.H5('Step 1.3: Review Selected Files'),
                    dcc.Dropdown(options=[], value=[], id=id('files_selected'), multi=True, clearable=True, placeholder=None, style={'height':'150px', 'overflow-y':'auto'})
                ], width={'size':4, 'offset':0}),
                dbc.Col([
                    html.H5('Step 1.4: Set Settings'),
                    dbc.InputGroup([
                        dbc.InputGroupText("Delimiter", style={'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                        dbc.Select(options=option_delimiter, id=id('dropdown_delimiter'), value=option_delimiter[0], style={'font-size': '12px'}),
                    ]),
                    dbc.Checklist(options=[
                        {"label": "Remove Spaces", "value": 'remove_space'},
                        {"label": "Remove Header", "value": 'remove_header'}
                    ], inline=False, switch=True, id=id('checklist_settings'), value=['remove_space'], labelStyle={'display':'block'}),
                ], width={'size':4, 'offset':0}),
                dbc.Col(html.Hr(style={'border': '1px dotted black', 'margin': '30px 0px 30px 0px'}), width=12),
            ], style={'text-align':'center'}),
            
            # Datatable
            dbc.Row([
                dbc.Col([
                    dbc.Col(html.H5('API Data', style={'text-align':'center'})),
                    dbc.Col(html.Div(generate_datatable(id('datatable'), height='500px')), width=12),
                    html.Br(),
                ], width=12),
            ], className='bg-white text-dark'),

            # Upload Button & Error Messages
            dbc.Row([
                dbc.Col(html.Button('Upload', id=id('button_upload'), className='btn btn-primary btn-block', style={'margin':'20px 0px 0px 0px', 'font-size': '13px', 'font-weight': 'bold'}), width={'size':10, 'offset':1}),
                dbc.Col(id=id('upload_error'), width=12),
            ]),
        ]),
    return content


# Generate New Node ID or Load Node ID
# @app.callback(Output(id('node_id'), "value"),
#                 [Input('current_dataset', "data"),
#                 Input('current_node', 'data'),])
# def generate_load_node_id(metadata, selected_node):
#     # If New Dataset, Generate random Node number
#     if (metadata['node']) == 0:
#         return 123
#     else:
#         return selected_node


# Check if Dataset Exist. Modify Button to "Create Dataset" or "Load Dataset"
@app.callback([Output(id('button_create_load_dataset'), "children"), 
                Output(id('button_create_load_dataset'), "color"),
                Output(id('dropdown_dataset_type'), "disabled")],
                [Input(id('input_dataset_name'), "value")])
def check_if_dataset_name_exist(value):
    if value is None: return no_update

    list_of_collections = [c['name'] for c in client.collections.retrieve()]
    dataset_name = "dataset_" + value
    isDisabled = False

    if dataset_name in list_of_collections: 
        button_name = "Load Dataset"
        color = "success"
        isDisabled = True
    else: 
        button_name = "Create Dataset"
        color = "primary"

    return button_name, color, isDisabled



@app.callback([Output(id('tabs_content'), "value"), 
                Output('current_dataset', "data"),
                Output(id('input_dataset_name'), "invalid"),
                Output(id('dropdown_dataset_type'), "style")],
                [Input(id('button_create_load_dataset'), "n_clicks"),
                State(id('input_dataset_name'), "value"),
                State(id('dropdown_dataset_type'), 'value')])
def on_create_load_dataset(n_clicks, name, dataset_type):
    if n_clicks is None: return no_update

    active_tab = no_update
    metadata = no_update
    invalid = False
    borderStyle = {}

    if (name is None) or (not name.isalnum()):
        print('Invalid File Name')
        invalid = True
    if dataset_type is None:
        print('Invalid Dataset Type')
        borderStyle = {'border': '1px solid red'}

    if (name is not None) and (name.isalnum()) and (dataset_type is not None):
        list_of_collections = [c['name'] for c in client.collections.retrieve()]
        name = "dataset_" + name
        active_tab = id('upload_api')
        metadata = {
            'name': name,               # Str
            'type': dataset_type,       # Str
            'node': [],                 # List of Str (Node Names)
        }
        # Upload Metadata
        if name not in list_of_collections: 
            client.collections.create(generate_schema_auto(name))

    print('Metadata: ' + str(metadata))

    return active_tab, metadata, invalid, borderStyle
    

# Browse Drag&Drop Files, Display File Selection, Settings, Update Datatable 
@app.callback([Output(id('files_selected'), 'value'),
                Output(id('files_selected'), 'options'),
                Output(id('dropdown_delimiter'), 'disabled'),
                Output(id('datatable'), "data"), 
                Output(id('datatable'), 'columns'),
                Output(id('datatable'), 'style_data_conditional'),],
                [Input(id('browse_drag_drop'), 'isCompleted'),
                Input(id('files_selected'), 'value'),
                Input(id('dropdown_delimiter'), 'value'),
                Input(id('checklist_settings'), 'value'),
                State(id('browse_drag_drop'), 'upload_id'),
                State(id('datatable'), 'data')])
def browse_drag_drop_files(isCompleted, files_selected, dropdown_delimiter, checklist_settings, upload_id, datatable_data):
    time.sleep(0.5)
    if not isCompleted: return no_update
    # Initialize Default Outputs
    files_selected_options = []
    dropdown_delimiter_disabled = True
    # datatable_data = {}
    datatable_columns = []
    style_data_conditional = []
    
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    root_folder = Path(UPLOAD_FOLDER_ROOT) / upload_id
    file_name_list = os.listdir(root_folder)
    file_name_list_full = [(root_folder / filename).as_posix() for filename in os.listdir(root_folder)]

    # Drag & Drop or Delete Files or Change Delimiter
    if triggered == id('browse_drag_drop') or triggered == id('files_selected') or triggered == id('dropdown_delimiter'):

        if triggered == id('browse_drag_drop'):
            files_selected_options = [{'label': filename, 'value': filename_full} for filename, filename_full in zip(file_name_list, file_name_list_full)]
            file_extensions = [name.rsplit('.', 1)[1] for name in file_name_list]
            if 'csv' in file_extensions: 
                dropdown_delimiter_disabled = False

        elif triggered == id('files_selected'):
            files_to_remove = set(file_name_list_full) - set(files_selected)
            try:
                for file in files_to_remove:
                    os.remove(file)
            except Exception as e:
                print(e)
            file_name_list = os.listdir(root_folder)
            file_name_list_full = [(root_folder / filename).as_posix() for filename in os.listdir(root_folder)]
            files_selected_options = [{'label': filename, 'value': filename_full} for filename, filename_full in zip(file_name_list, file_name_list_full)]

        data = []
        for file in file_name_list_full:
            if file.endswith('.json'):
                with open(file, 'r') as f:
                    json_file = json.load(f)
                json_file = flatten(json_file)
                data.append(json_file)
                df = json_normalize(data)
                
            elif file.endswith('.csv'):
                df = pd.read_csv(file_name_list_full[0], sep=dropdown_delimiter['value']) # Assume only 1 CSV uploaded, TODO combine if CSV and JSON uploaded together?

        datatable_data = df.to_dict('records')
        datatable_columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]

    # Select Checklist
    if triggered == id('checklist_settings'):
        df = json_normalize(datatable_data)
        if 'remove_space' in checklist_settings:
            df = whitespace_remover(df)
        if 'remove_header' in checklist_settings:
            style_data_conditional = [{'if': {'row_index': 0}, 'backgroundColor': 'grey'}]
    
    return file_name_list_full, files_selected_options, dropdown_delimiter_disabled, datatable_data, datatable_columns, style_data_conditional


# Upload Button
@app.callback([Output(id('current_dataset'), 'data'),
                Output(id('current_node'), 'data')],
                [Input(id('button_upload'), 'n_clicks'),
                State(id('current_dataset'), 'data'),
                State(id('node_id'), 'value'),
                State(id('node_description'), 'value'),
                State(id('dropdown_delimiter'), 'value'),
                State(id('checklist_settings'), 'value'),
                State(id('datatable'), 'data')])
def upload(n_clicks, current_dataset, node_id, node_description, dropdown_delimiter, checklist_settings, datatable_data):
    if n_clicks is None: return no_update

    pprint(datatable_data)

    if 'remove_space' in checklist_settings:
        pass
    if 'remove_header' in checklist_settings:
        pass

    df = json_normalize(datatable_data)
    # df.fillna('None', inplace=True) # Replace null with 'None
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl
    client.collections[current_dataset].documents.import_(jsonl, {'action': 'create'})

    return no_update


# # Upload Button
# @app.callback([Output('dataset_metadata', 'data'),
#                 Output(id('upload_error'), 'children')], 
#                 [Input(id('button_upload'), 'n_clicks'),
#                 Input(id('dropdown_dataset_type'), 'value'),
#                 Input(id('dropdown_delimiter'), 'value'), 
#                 Input(id('checklist_settings'), 'value'),
#                 State(id('input_name'), 'value'),
#                 State(id('api_list'), 'data')])
# def upload(n_clicks, type, delimiter, checklist_settings, input_name, api_list):
#     if n_clicks is None: return no_update
#     triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
#     dataset_name = 'dataset_' + input_name

#     # If upload clicked
#     if triggered == id('button_upload'):
#         # Check invalid names
#         # if (name is None) or (not name.isalnum()):
#         #     print('Invalid File Name')
#         #     return no_update, html.Div('Invalid File Name', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-danger')
#         # Check if name exist
#         if dataset_name in [c['name'] for c in client.collections.retrieve()]:
#             print('File Name Exist')
#             return no_update, html.Div('File Name Exist', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-danger')
    
#     # # Upload Metadata
#     # metadata = {}
#     # metadata['name'] = input_name
#     # metadata['api'] = [dataset_name+'_api_'+str(num) for num in list(range(1, len(api_list)+1))]
#     # metadata['blob'] = []
#     # metadata['index'] = []
#     # metadata['datatype'] = {}
#     # metadata['expectation'] = []
#     # metadata['cytoscape_elements'] = []
#     # metadata['setting'] = {'type': type, 'delimiter': delimiter, 'checklist': checklist_settings}
#     # metadata2 = metadata.copy()
#     # for k, v in metadata2.items():
#     #     metadata2[k] = str(metadata2[k])
#     # client.collections.create(generate_schema_auto(dataset_name))
#     # client.collections[dataset_name].documents.create(metadata2)

#     # Upload File contents
#     for i, file_list in enumerate(api_list):
#         data = []
#         if all(f.endswith('.json') for f in file_list): # JSON Uploaded
#             for file in file_list:
#                 with open(file, 'r') as f:
#                     json_file = json.load(f)
#                 json_file = flatten(json_file)
#                 data.append(json_file)
#             df = json_normalize(data)

#         elif all(f.endswith('.csv') for f in file_list):
#             df = pd.read_csv(file_list[0]) # TODO for now Assume only 1 CSV uploaded

#         df.fillna('None', inplace=True) # Replace null with 'None
#         jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

#         client.collections.create(generate_schema_auto(metadata['api'][i]))
#         client.collections[metadata['api'][i]].documents.import_(jsonl, {'action': 'create'})
        
#     return metadata, html.Div('Successfully Uploaded', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-success') 
        




