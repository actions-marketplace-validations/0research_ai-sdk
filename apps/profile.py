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


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
id = id_factory((__file__).rsplit("\\", 1)[1].split('.')[0])
print(id('here-----------'))
tab_labels = ['Step 1: Upload Data', 'Step 2: Set Data Profile', 'Step 3: Review Data']
tab_values = [id('upload_data'), id('set_data_profile'), id('review_data')]
datatype_list = ['object', 'Int64', 'float64', 'bool', 'datetime64', 'category']
option_filetype = [
    {'label': 'JSON', 'value': 'json'},
    {'label': 'CSV', 'value': 'csv'},
]
option_data_nature = [
    {'label': 'Numerical', 'value': 'numerical'},
    {'label': 'Categorical', 'value': 'categorical'},
    {'label': 'Hybrid', 'value': 'hybrid'},
    {'label': 'Time Series', 'value': 'time_series'},
    {'label': 'Geo Spatial', 'value': 'geo_spatial'},
]
option_delimiter = [
    {'label': 'Comma (,)', 'value': ','},
    {'label': 'Tab', 'value': r"\t"},
    {'label': 'Space', 'value': r"\s+"},
    {'label': 'Pipe (|)', 'value': '|'},
    {'label': 'Semi-Colon (;)', 'value': ';'},
    {'label': 'Colon (:)', 'value': ':'},
]


# Layout
layout = html.Div([
    dcc.Store(id=id('api_list'), storage_type='memory'),
    dcc.Store(id='dataset_metadata', storage_type='session'),
    dcc.Store(id='dataset_profile', storage_type='session'),
    dcc.Store(id=id('remove_list'), storage_type='session'),

    generate_tabs(id('tabs_content'), tab_labels, tab_values),
    dbc.Container([], fluid=True, id=id('content')),
    html.Div(id='test1'),
])


# Tab Content
@app.callback(Output(id("content"), "children"), [Input(id("tabs_content"), "value")])
def generate_tab_content(active_tab):
    content = None
    if active_tab == id('upload_data'):
        content = html.Div([
            dbc.Row([
                dbc.Col([
                    html.H5('Step 1.1: Dataset Settings'),
                    html.Div('Name', style={'width':'20%', 'display':'inline-block', 'vertical-align':'top'}),
                    html.Div(dbc.Input(id=id('input_name'), placeholder="Enter Name of Dataset", type="text"), style={'width':'80%', 'display':'inline-block', 'margin':'0px 0px 2px 0px'}),

                    html.Div('Type', style={'width':'20%', 'display':'inline-block', 'vertical-align':'top'}),
                    html.Div(generate_dropdown(id('dropdown_file_type'), option_data_nature), style={'width':'80%', 'display':'inline-block'}),

                    html.Div('Delimiter', style={'width':'20%', 'display':'inline-block', 'vertical-align':'top'}),
                    html.Div(generate_dropdown(id('dropdown_delimiter'), option_delimiter), style={'width':'80%', 'display':'inline-block'}),
        
                    dbc.Checklist(options=[
                        {"label": "Remove Spaces", "value": 'remove_space'},
                        {"label": "Remove Header", "value": 'remove_header'}
                    ], inline=False, switch=True, id=id('checklist_settings'), value=['remove_space'], labelStyle={'display':'block'}),
                ], width=6),
                
                dbc.Col([
                    html.H5('Step 1.2: Upload Data (Smaller than 1MB)'),
                    get_upload_component(id=id('upload')),
                    # generate_upload('upload_json', "Drag and Drop or Click Here to Select Files"),
                ], className='text-center', width=6),

            ], className='text-center', style={'margin': '3px'}),

            dbc.Row([
                dbc.Col(html.Hr(), width=12),
                dbc.Col(id=id('upload_api_list_options'), children=[], width=4),
                dbc.Col(id=id('upload_api_list'), children=[], width=7),
                dbc.Col([html.Button('Upload', id=id('button_upload'), className='btn btn-primary btn-block', style={'margin':'20px 0px 0px 0px', 'font-size': '13px', 'font-weight': 'bold'}),], width=12),
                dbc.Col(html.Hr(), width=12),
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Col(html.H5('Sample Data', style={'text-align':'center'})),
                    dbc.Col(html.Div(generate_datatable(id('input_datatable_sample'), height='300px')), width=12),
                    html.Br(),
                ], width=12),
                dbc.Col(id=id('upload_error'), width=12),
                dbc.Col([
                    html.Br(),
                    # html.Div(html.Button('Next Step', className='btn btn-primary', id=id('next_button_1')), className='text-center'),
                ]),
            ])
        ]),


    elif active_tab == id('set_data_profile'):
        content = html.Div([
            dbc.Row(dbc.Col(html.H5('Step 2: Set Data Profile'), width=12)),
            dbc.Row(dbc.Col(html.Div(id=id('data_profile'), style={'overflow-y': 'auto', 'overflow-x': 'hidden', 'height':'800px'}), width=12)),
            # html.Div(id=id('data_profile')),
            # html.Div(html.Button('Next Step', className='btn btn-primary', id=id('next_button_2')), className='text-center'),
        ], className='text-center', style={'margin': '3px'}),
        

    elif active_tab == id('review_data'):
        content = dbc.Row([
            dbc.Col(html.H5('Step 3: Preview Data'), width=12),
            dbc.Col(html.Div(generate_datatable(id('input_datatable'))), width=12),
            html.Br(),
            # dbc.Col(html.Div(html.Button('Upload Data', className='btn btn-primary', id=id('button_confirm')), className='text-center'), width=12),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '3px'}),

    return content


# Handles files being staged for uploading
@app.callback([Output(id('api_list'), 'data'),
                Output(id('upload_api_list'), 'children')],
                [Input(id('upload'), 'isCompleted'),
                Input({'type': id('upload_select_list'), 'index': ALL }, 'value')],
                [State(id('api_list'), 'data'),
                State(id('upload'), 'fileNames'),
                State(id('upload'), 'upload_id'),
                State(id('upload_api_list'), 'children')])
def process_upload(iscompleted, selection_list, api_list_store, filenames, upload_id, upload_api_list):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]

    # Initalize Variables
    num_uploads = len(upload_api_list)
    api_list = []
    if api_list_store is None: api_list_store = []
    out = []
    root_folder = Path(UPLOAD_FOLDER_ROOT) / upload_id
    time.sleep(0.5)
    # If Upload Triggered
    if triggered == id('upload'):
        if not iscompleted: return no_update

        api_list = [(root_folder / filename).as_posix() for filename in os.listdir(root_folder)]    # Filenames uploaded in server
        flat_api_list_store = [val for sublist in api_list_store for val in sublist]        # Filenames stored in local memory
        files_to_add = list(set(api_list) - set(flat_api_list_store))
        
        if len(files_to_add) > 0:
            api_list_store.append(files_to_add)
            options = [{'label': filename.rsplit('/', 1)[1], 'value': filename} for filename in files_to_add]
            new = dcc.Dropdown(options=options, value=files_to_add, multi=True, clearable=True, id={'type': id('upload_select_list'), 'index': num_uploads})
            out = upload_api_list + [new]
            return api_list_store, out
        else:
            return no_update
    # If remove from dropdown triggered
    else:
        for uploads, selection in zip(api_list_store, selection_list):
            files_to_remove = set(uploads) - set(selection)
            try:
                for filename in os.listdir(root_folder):
                    file = (root_folder/filename).as_posix()
                    if file in files_to_remove:
                        os.remove(file)
            except Exception as e:
                print(e)

        upload_api_list = list(filter(lambda x: len(x['props']['value']) != 0, upload_api_list))
        return selection_list, upload_api_list


# Upload Button
@app.callback([Output('dataset_metadata', 'data'),
                Output(id('upload_error'), 'children')], 
                [Input(id('button_upload'), 'n_clicks'),
                Input(id('dropdown_file_type'), 'value'),
                Input(id('dropdown_delimiter'), 'value'), 
                Input(id('checklist_settings'), 'value'),
                State(id('input_name'), 'value'),
                State(id('api_list'), 'data')])
def upload(n_clicks, type, delimiter, checklist_settings, input_name, api_list):
    if n_clicks is None: return no_update
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    metadata_name = 'dataset_' + input_name

    # If upload clicked
    if triggered == id('button_upload'):
        # Check invalid names
        if input_name == None or (' ' in input_name): 
            print('Invalid File Name')
            return no_update, html.Div('Invalid File Name', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-danger')
        # Check if name exist
        for c in client.collections.retrieve():
            if c['name'] == metadata_name:
                print('File Name Exist')
                return no_update, html.Div('File Name Exist', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-danger')
    
    # Upload Metadata
    metadata = {}
    metadata['name'] = input_name
    metadata['api'] = [metadata_name+'_api_'+str(num) for num in list(range(1, len(api_list)+1))]
    metadata['blob'] = []
    metadata['index'] = []
    metadata['datatype'] = {}
    metadata['expectation'] = []
    metadata['cytoscape_elements'] = []
    metadata['setting'] = {'type': type, 'delimiter': delimiter, 'checklist': checklist_settings}
    metadata2 = metadata.copy()
    for k, v in metadata2.items():
        metadata2[k] = str(metadata2[k])
    client.collections.create(generate_schema_auto(metadata_name))
    client.collections[metadata_name].documents.create(metadata2)

    # Upload File contents
    for i, file_list in enumerate(api_list):
        data = []
        if all(f.endswith('.json') for f in file_list): # JSON Uploaded
            for file in file_list:
                with open(file, 'r') as f:
                    json_file = json.load(f)
                json_file = flatten(json_file)
                data.append(json_file)
            df = json_normalize(data)

        elif all(f.endswith('.csv') for f in file_list):
            df = pd.read_csv(file_list[0]) # TODO for now Assume only 1 CSV uploaded

        df.fillna('None', inplace=True) # Replace null with 'None
        jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

        client.collections.create(generate_schema_auto(metadata['api'][i]))
        client.collections[metadata['api'][i]].documents.import_(jsonl, {'action': 'create'})
        
    return metadata, html.Div('Successfully Uploaded', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-success') 
        


# Update Sample Datatable 
# @app.callback([Output(id('input_datatable_sample'), "data"), 
#                 Output(id('input_datatable_sample'), 'columns'),
#                 Output(id('input_datatable_sample'), 'style_data_conditional')],
#                 [Input('dataset_metadata', "data")])
# def update_data_table(settings):
#     if settings is None or settings['name'] is None: return no_update

#     # Get Data & Columns
#     result = get_documents(settings['name'], 5)
#     df = json_normalize(result)
#     df.insert(0, column='index', value=range(1, len(df)+1))
#     columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]

#     # Style datatable and manipulate df upon settings change
#     style_data_conditional = []
#     if 'remove_space' in settings['checklist']:
#         df = whitespace_remover(df)
#     if 'remove_header' in settings['checklist']:
#         style_data_conditional.append({'if': {'row_index': 0}, 'backgroundColor': 'grey'})

#     # if len(str(filename)) > 80:
#     #     filename =str(filename)
#     #     filename = filename[:20] + " ... " + filename[-20:]
#     # options.append({'label': filename, 'value': })

#     return df.to_dict('records'), columns, style_data_conditional, no_update




def generate_expectations():
    datatype = None # TODO get selected dropdown datatype from arg
    expectation = html.Div()

    if datatype == datatype_list[0]:  # Object
        pass
    elif datatype == datatype_list[1]:  # Int64
        pass
    elif datatype == datatype_list[2]:  # float64
        pass
    elif datatype == datatype_list[3]:  # bool
        pass
    elif datatype == datatype_list[4]:  # datetime64
        pass
    elif datatype == datatype_list[5]:  # category
        pass

    return [ 
        html.Div([
            expectation,
            html.Div('Not Null Threshold', style={'width':'40%', 'display':'inline-block', 'vertical-align':'top'}),
            html.Div(generate_slider(id('slider_not_null_threshold'), min=0, max=100, step=1, value=1), style={'width':'50%','display':'inline-block'}),
            html.Div(style={'width':'40%', 'display':'inline-block', 'vertical-align':'top'}, id=id('val_not_null_threshold')),
        ]),
    ]
    

@app.callback(Output(id('data_profile'), 'children'), 
            [Input('dataset_metadata', 'data'),
            Input('url', 'pathname')])
def generate_profile(metadata, pathname):
    if metadata is None or metadata['name'] is None: return no_update
    
    result = get_documents('dataset_'+metadata['name'], 100)
    df = json_normalize(result)
    columns = list(df.columns)
    detected_datatype_list = list(map(str, df.convert_dtypes().dtypes))

    option_datatype = [
        {'label': 'object', 'value': 'object'},
        {'label': 'string', 'value': 'string'},
        {'label': 'Int64', 'value': 'Int64'},
        {'label': 'datetime64', 'value': 'datetime64'},
        {'label': 'boolean', 'value': 'boolean'},
        {'label': 'category', 'value': 'category'}
    ]

    return (html.Table(
        [html.Tr([
            html.Th('Column'),
            html.Th('Datatype'),
            html.Th('Invalid (%)'),
            html.Th('Result'),
            html.Th(''),
        ])] + 
        [html.Tr([
            html.Td(html.H6(col), id={'type':id('col_column'), 'index': i}),
            html.Td(generate_dropdown({'type':id('col_dropdown_datatype'), 'index': i}, option_datatype, value=dtype)),
            html.Td(html.H6('%', id={'type':id('col_invalid'), 'index': i})),
            html.Td(html.H6('-', id={'type':id('col_result'), 'index': i})),
            html.Td(html.Button('Remove', id={'type':id('col_button_remove'), 'index': i}, style={'background-color':'white'})),
            ], id={'type':id('row'), 'index': i}) for i, (col, dtype) in enumerate(zip(columns, detected_datatype_list))
        ] +
        [html.Tr([''])],
        style={'width':'100%', 'height':'800px'}, 
        id=id('table_data_profile')))


# Style deleted row
@app.callback(Output({'type':id('row'), 'index': MATCH}, 'style'), 
            [Input({'type':id('col_button_remove'), 'index': MATCH}, 'n_clicks'),
            State({'type':id('row'), 'index': MATCH}, 'style')])
def style_row(n_clicks, style):
    if n_clicks is None: return no_update

    if style is None: newStyle = {'background-color':'grey'}
    else: newStyle = None

    return newStyle




# Store profile
@app.callback(Output('dataset_profile', 'data'),
                Output(id('remove_list'), 'data'),
                [Input(id("tabs_content"), "value"),
                Input({'type':id('col_dropdown_datatype'), 'index': ALL}, 'value'),
                Input({'type':id('col_button_remove'), 'index': ALL}, 'n_clicks'),
                State({'type':id('col_column'), 'index': ALL}, 'children')])
def update_output(tab, datatype, remove_list_n_clicks, column):
    if tab != id('set_data_profile'): return no_update

    column = [c['props']['children'] for c in column]

    # Profile
    profile = {}
    profile['datatype'] = dict(zip(column, datatype))
    profile['index'] = '' # TODO Store index field 
    profile['expectation'] = {} # TODO Store expectations 

    # Remove Column List
    remove_list = []
    for n_clicks, c in zip(remove_list_n_clicks, column):
        if (n_clicks is not None) and n_clicks%2 == 1:
            remove_list.append(c)

    return profile, remove_list


# Update Datatable in "Review Data" Tab
@app.callback([Output(id('input_datatable'), "data"), 
                Output(id('input_datatable'), 'columns')], 
                [Input(id("tabs_content"), "value"),
                State('dataset_metadata', "data"),
                State('dataset_profile', "data"),
                State(id('remove_list'), "data")])
def update_data_table(tab, settings, profile, remove_list):
    if settings is None or settings['name'] is None: return no_update
    if tab != id('review_data'): return no_update
    
    result = get_documents(settings['name'], 250)
    df = json_normalize(result)
    df.insert(0, column='index', value=range(1, len(df)+1))

    # Remove Columns
    df.drop(remove_list, axis=1, inplace=True)

    # Settings
    print(settings)

    # Profile
    # print(profile['datatype'])

    columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]
    
    return df.to_dict('records'), columns


# Update typesense dataset with settings/profile/columns to remove
# @app.callback(Output(id('????????'), "??????"), 
#                 [Input(id("button_confirm"), "n_clicks"),
#                 State('dataset_metadata', "data"),
#                 State('dataset_profile', "data")])
# def upload_data(n_clicks, setting, profile):
#     if n_clicks is None: return no_update

#     print(setting)
#     print(profile)

    # Update typesense dataset

    # Update typesense dataset profile

#     return no_update
