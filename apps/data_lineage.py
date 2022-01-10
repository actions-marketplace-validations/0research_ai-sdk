from typing_extensions import ParamSpecArgs
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
from app import app
import dash_bootstrap_components as dbc
from dash import dash_table
from dash import no_update, callback_context
import json
from flatten_json import flatten, unflatten, unflatten_list
import jsonmerge
from pprint import pprint
from genson import SchemaBuilder
from jsondiff import diff
import json
from jsondiff import diff, symbols
from apps.util import *
import base64
import pandas as pd
from pandas import json_normalize
from itertools import zip_longest
from datetime import datetime
import dash_cytoscape as cyto
from apps.typesense_client import *
import ast
from apps.constants import *
import copy
from pathlib import Path

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('data_lineage')
du.configure_upload(app, UPLOAD_FOLDER_ROOT)
    

# Creating styles
stylesheet = [
    # All Nodes
    {
        'selector': 'node',
        'style': {
            'content': 'data(name)'
        }
    },
    # Edge
    {
        'selector': 'edge',
        'style': {
            'curve-style': 'bezier',
            'target-arrow-color': 'black',
            'target-arrow-shape': 'triangle',
            'line-color': 'black'
        }
    },
    # Dataset Nodes
    {
        'selector': '.raw_fileupload',
        'style': {

        }
    },
    {
        'selector': '.raw_restapi',
        'style': {

        }
    },
    # Action
    {
        'selector': '.action',
        'style': {
            # 'background-color': 'yellow',
            # 'width': 25,
            # 'height': 25,
            # 'background-image': "/assets/static/api.png"
            'background-color': '#FFFF00',
            'shape': 'rectangle',
            'content': 'data(action)'
        }
    },
    

]


options_merge = [{'label': o, 'value': o} for o in MERGE_TYPES]

layout = html.Div([
    html.Div([
        dcc.Store(id=id('do_cytoscape_reload'), storage_type='session', data=False),
        dcc.Store(id=id('dataset_data'), storage_type='memory'),

        # Left Panel
        dbc.Row([
            dbc.Col([
                html.H5('Data Lineage (Data Flow Experiments)', style={'text-align':'center', 'display':'inline-block', 'margin':'0px 0px 0px 40px'}),
                html.Div([
                    html.Button('Load', id=id('button_load'), className='btn btn-secondary btn-lg', style={'margin-right':'1px'}),
                    # html.Button('Hide/Show', id=id('button_hide_show'), className='btn btn-warning btn-lg', style={'margin-right':'1px'}), 
                    dbc.DropdownMenu(label="Action", children=[], id=id('dropdown_action'), size='lg', color='warning', style={'display':'inline-block'}),
                ], style={'float':'right', 'display':'inline-block'}),

                cyto.Cytoscape(id=id('cytoscape'),
                                minZoom=0.2,
                                maxZoom=2,
                                elements=[], 
                                selectedNodeData=[],
                                layout={'name': 'breadthfirst',
                                        'fit': True,
                                        'directed': True,
                                        'padding': 10,
                                        },
                                style={'height': '800px','width': '100%'},
                                stylesheet=stylesheet)
            ], width=6),

            # Right Panel
            dbc.Col([
                html.Div([
                    html.Div(dbc.Tabs([], id=id("tabs_node")), style={'float':'left', 'text-align':'left', 'display':'inline-block'}),
                    html.Div([
                        dbc.Button(html.I(n_clicks=0, className='fas fa-check'), id=id('button_perform_action'), disabled=True, className='btn btn-warning', style={'margin-left':'1px'}),
                        dbc.Button(html.I(n_clicks=0, className='fas fa-chart-area'), id=id('button_chart'), disabled=True, className='btn btn-success', style={'margin-left':'1px'}),
                        dbc.Button(html.I(n_clicks=0, className='fas fa-times'), id=id('button_remove'), disabled=True, className='btn btn-danger', style={'margin-left':'1px'}),
                        dbc.Tooltip('Perform Action', target=id('button_perform_action')),
                        dbc.Tooltip('Chart', target=id('button_chart')),
                        dbc.Tooltip('Remove Action or Raw Dataset', target=id('button_remove')),
                    ], style={'float':'right', 'text-align':'right', 'display':'inline-block'}),
                ], style={'display':'inline-block', 'width':'100%'}),
                  
                dbc.Card([
                    # Headers
                    dbc.CardHeader([html.P(id=id('right_header_1'), style={'text-align':'center', 'font-size':'13px', 'font-weight':'bold', 'float':'left', 'width':'100%'})]),

                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                dcc.RangeSlider(
                                    id=id('range'),
                                    value=[],
                                    tooltip={"placement": "bottom", "always_visible": True},
                                ),
                            ]),
                            dbc.Col([
                                dbc.Select(options=options_merge, value=options_merge[0]['value'], id=id('merge_type'), style={'text-align':'center'}),
                                dbc.Select(options=[], value=None, id=id('merge_idRef'), style={'text-align':'center', 'display':'none'}),
                            ], id=id('merge_type_container'), style={'display':'none'}, width=4),
                            dbc.Col([
                                dbc.Button(html.I(n_clicks=0, className='fa fa-table'), color='info', outline=True, id=id('button_tabular'), n_clicks=0),
                                dbc.Tooltip('View in Tabular Format', target=id('button_tabular')),
                            ], width=1),
                            dbc.Col([dbc.Input(id=id('search_json'), placeholder='Search', style={'text-align':'center'})], width=12),
                        ]),
                    ], id=id('right_header_2'), style={'display':'none', 'font-size':'13px'}),


                    # Right Body (Data, Metadata)
                    dbc.CardBody(html.Div([], id=id('right_content'), style={'min-height': '650px'})),

                    # Right Body 2 (Config)
                    dbc.CardBody([
                        dbc.InputGroup([
                            dbc.InputGroupText('Description', style={'width':'30%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'12px'}),
                            dbc.Textarea(id=id('description'), placeholder='Enter Dataset Description', style={'height':'50px', 'text-align':'center'}, persistence=True, persistence_type='session'),
                        ]),
                        dbc.InputGroup([
                            dbc.InputGroupText('Documentation', style={'width':'30%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'12px'}),
                            dbc.Input(id=id('documentation'), placeholder='Enter Documentation URL (Optional) ', style={'height':'40px', 'min-width':'120px', 'text-align':'center'}, persistence=True, persistence_type='session'),
                        ]),
                        html.Hr(),
                        dbc.InputGroup([
                            dbc.InputGroupText('Data Source Type', style={'width':'30%', 'font-weight':'bold', 'font-size': '13px', 'padding-left':'12px'}),
                            dbc.Select(id('select_dataset_type'), options=[
                                {"label": "Manually Upload Files", "value": "raw_fileupload"},
                                {"label": "Rest API", "value": "raw_restapi"},
                                {"label": "Search Data Catalog", "value": "type3", 'disabled':True},
                                {"label": "GraphQL", "value": "type4", 'disabled':True},
                            ], value='raw_fileupload', style={'text-align':'center', 'font-size':'15px'}),
                        ], style={'margin-bottom':'10px'}),
                        html.Div(generate_manuafilelupload_details(id), style={'display':'none'}, id=id('config_options_fileupload')),
                        html.Div(generate_restapi_details(id), style={'display':'none'}, id=id('config_options_restapi')),
                    ], id=id('right_content_2'), style={'min-height': '800px', 'display': 'none'}),
                    
                    # Right Footer
                    dbc.CardFooter([
                        dbc.Button(children='Save', id=id('button_save'), color='warning', style={'width':'100%', 'font-size':'22px'}),
                    ])

                ], className='bg-dark', inverse=True),

            ], width=6),
        ]),

        # Modal (View Tabular Form Data)
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle('', id=id('modal_title'))),
            dbc.ModalBody('', id=id('modal_body')),
            dbc.ModalFooter('', id=id('modal_footer')),
        ], id=id('modal'), size='xl'),

    ], style={'width':'100%'}),
])


# Load Dataset Config 
@app.callback(
    Output(id('description'), 'value'),
    Output(id('documentation'), 'value'),
    Output(id('select_dataset_type'), 'value'),
    Output(id('dropdown_method'), 'value'),
    Output(id('url'), 'value'),
    Output(id('select_dataset_type'), 'disabled'),
    Input(id('cytoscape'), 'tapNodeData')
)
def populate_dataset_config(tapNodeData):
    if tapNodeData is None: return no_update
    description, documentation, method, url, disabled = '', '', 'get', '', False
    
    if tapNodeData['id'] in get_all_collections():
        dataset = get_document('dataset', tapNodeData['id'])
        description = dataset['description']
        documentation = dataset['documentation']
        if dataset['type'] == 'raw':
            dataset_type = 'raw_fileupload'
        elif dataset['type'] == 'raw_restapi':
            method = dataset['details']['method']
            url = dataset['details']['url']
            dataset_type = dataset['type']
        elif dataset['type'] == 'processed':
            dataset_type = ''
            disabled = True
        else:
            dataset_type = dataset['type']
    else:
        dataset_type = 'raw_fileupload'
    return description, documentation, dataset_type, method, url, disabled

# Load Dataset Config Options
@app.callback(
    Output(id('config_options_fileupload'), 'style'),
    Output(id('config_options_restapi'), 'style'),
    # Output(id('config_options_restapi'), 'children'),
    Input(id('select_dataset_type'), 'value'),
    State(id('config_options_restapi'), 'children'),
)
def load_dataset_options(dataset_type, options_restapi):
    style1, style2 = {'display':' none'}, {'display':' none'}
    if dataset_type == 'raw_fileupload':  style1 = {'display':' block'}
    elif dataset_type == 'raw_restapi': style2 = {'display':' block'}

    return style1, style2


# Tab Content, Add New Datasets
@app.callback(
    Output(id('tabs_node'), 'children'),
    Output(id('tabs_node'), 'active_tab'),
    Output(id('do_cytoscape_reload'), 'data'),
    Input(id('cytoscape'), 'selectedNodeData'),
    Input(id('button_save'), 'n_clicks'),
    # New Dataset Inputs
    State(id('select_dataset_type'), 'value'),
    State({'type':id('node_name'), 'index': ALL}, 'value'),
    State(id('description'), 'value'),
    State(id('documentation'), 'value'),
    State(id('browse_drag_drop'), 'isCompleted'),
    State(id('browse_drag_drop'), 'upload_id'),
    State(id('browse_drag_drop'), 'fileNames'),
    State(id('dropdown_method'), 'value'),
    State(id('url'), 'value'),
    State({'type': id('header_key'), 'index': ALL}, 'value'),
    State({'type': id('header_value'), 'index': ALL}, 'value'),
    State({'type': id('header_value_position'), 'index': ALL}, 'value'),
    State({'type': id('param_key'), 'index': ALL}, 'value'),
    State({'type': id('param_value'), 'index': ALL}, 'value'),
    State({'type': id('param_value_position'), 'index': ALL}, 'value'),
    State({'type': id('body_key'), 'index': ALL}, 'value'),
    State({'type': id('body_value'), 'index': ALL}, 'value'),
    State({'type': id('body_value_position'), 'index': ALL}, 'value'),
    State(id('tabs_node'), 'active_tab'),
    State(id('right_content_2'), 'style'),
)
def generate_tabs(selectedNodeData, n_clicks_button_save_config,
                    dataset_type, node_name, description, documentation,
                    isCompleted, upload_id, fileNames,                                               # Tabular / JSON 
                    method, url, header_key_list, header_value_list, header_value_position_list, param_key_list, param_value_list, param_value_position_list, body_key_list, body_value_list, body_value_position_list,     # REST API
                    active_tab, right_content_2_style):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    triggered = json.loads(triggered) if triggered.startswith('{') and triggered.endswith('}') else triggered
    tab1_disabled, tab2_disabled, tab3_disabled = True, True, True
    num_selected = len(selectedNodeData)
    do_cytoscape_reload = False

    # Click Cytoscape Nodes
    if triggered == '' or triggered == id('cytoscape'):
        # If none selected
        if num_selected == 0:
            active_tab = None

        # One Node Selected
        elif num_selected == 1:
            store_session('dataset_id', selectedNodeData[0]['id'])
            if selectedNodeData[0]['type'] == 'action':
                tab2_disabled = False
                tab3_disabled = False
                active_tab = "tab2"
            else:
                tab1_disabled = False
                tab2_disabled = False
                tab3_disabled = False
                active_tab = 'tab1' if active_tab is None else active_tab

        # Multiple Nodes Selected
        elif num_selected > 1:
            if all(node['type'] != 'action' for node in selectedNodeData):
                tab1_disabled = False
                tab2_disabled = False
                active_tab = 'tab1' if active_tab is None else active_tab
    

    # Save Button Clicked
    elif triggered == id('button_save') and right_content_2_style['display'] != 'none' and n_clicks_button_save_config is not None and num_selected == 1:
        tab1_disabled = False
        tab2_disabled = False
        tab3_disabled = False
        active_tab = 'tab1'
        dataset_id = selectedNodeData[0]['id']
        project_id = get_session('project_id')
        source_id = None
        dataset_name = node_name[0]

        # Upload Files
        if dataset_type == 'raw_fileupload':
            if fileNames is not None and isCompleted is True:
                df, details = process_fileupload(upload_id, fileNames[0])
                save_dataset_config(dataset_id, df, dataset_name, description, documentation, dataset_type, details)
            else:
                save_dataset_config(dataset_id, None, dataset_name, description, documentation, dataset_type, None)
        
        # RestAPI
        elif dataset_type == 'raw_restapi':
            df, details = process_restapi(method, url, header_key_list, header_value_list, param_key_list, param_value_list, body_key_list, body_value_list)
            save_dataset_config(dataset_id, df, dataset_name, description, documentation, dataset_type, details)

            # Add Edges if dataset is dependent on other datasets
            if any(header_value_position_list) != None or any(param_value_position_list) or any(body_value_position_list):
                for header in header_value_position_list:
                    if header is not None and header != '': 
                        source_id = header[0]['id']
                        add_edge(project_id, source_id, dataset_id)

                for param in param_value_position_list:
                    if param is not None and param != '': 
                        source_id = param[0]['id']
                        add_edge(project_id, source_id, dataset_id)
                for body in body_value_position_list:
                    if body is not None and body != '': 
                        source_id = body[0]['id']
                        add_edge(project_id, source_id, dataset_id)

        # Save processed datasets
        else:
            save_dataset_config(dataset_id, None, dataset_name, description, documentation, dataset_type, None)

        do_cytoscape_reload = True

    tab_list = [
        dbc.Tab(label="Data", tab_id="tab1", disabled=tab1_disabled),
        dbc.Tab(label="Metadata", tab_id="tab2", disabled=tab2_disabled),
        dbc.Tab(label="Config", tab_id="tab3", disabled=tab3_disabled),
        # dbc.Tab(label="Experiments", tab_id="tab4", disabled=True),
    ]
    return tab_list, active_tab, do_cytoscape_reload



def merge_dataset_data(node_list, merge_type='objectMerge', idRef=None):
    data = get_dataset_data(node_list[0]['id']).to_dict('records')

    try:
        if merge_type in ['objectMerge', 'overwrite']:
            for node in node_list[1:]:
                new_data = get_dataset_data(node['id']).to_dict('records')
                data = [json_merge(row, row_new, merge_type) for row, row_new in zip(data, new_data)]

        elif merge_type == 'arrayMergeByIndex':
            schema = {"mergeStrategy": merge_type}
            print('idRef:', idRef)
            for node in node_list[1:]:
                new_data = get_dataset_data(node['id']).to_dict('records')
                data = jsonmerge.merge(data, new_data, schema)

        elif merge_type == 'arrayMergeById':
            schema = {"mergeStrategy": merge_type, "mergeOptions": {"idRef": idRef}}
            for node in node_list[1:]:
                new_data = get_dataset_data(node['id']).to_dict('records')
                data = jsonmerge.merge(data, new_data, schema)

        else:
            data = "TBD"

    except Exception as e:
        print(e, idRef)
        data = 'Merge Error'
    
    return data

def merge_dataset(dataset_list, merge_type='objectMerge'):
    dataset = get_document('dataset', dataset_list[0]['id'])
    dataset['changes'] = None
    for node in dataset_list[1:]:
        node['changes'] = None
        dataset = json_merge(dataset, get_document('dataset', node['id']), merge_type)
    return dataset



# Generate Node Data
@app.callback(
    Output(id('right_header_1'), 'children'),
    Output(id('dataset_data'), 'data'),
    Output(id('right_content'), 'style'),
    Output(id('right_header_2'), 'style'),
    Output(id('right_content_2'), 'style'),
    Output(id('merge_type_container'), 'style'),
    Output(id('range'), 'min'),
    Output(id('range'), 'max'),
    Output(id('range'), 'value'),
    Input(id('tabs_node'), 'active_tab'),
    Input(id('range'), 'value'),
    Input(id('merge_type'), 'value'),
    Input(id('merge_idRef'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('right_content'), 'style'),
    State(id('right_content_2'), 'style'),
)
def select_node(active_tab, range_value, merge_type, merge_idRef, selectedNodeData, out1_display, out2_display):
    name, out, out2 = [], [], ''
    range_min, range_max = None, None
    num_selected = len(selectedNodeData)
    out1_display['display'] = 'block'
    out2_display['display'] = 'none'
    right_header_2_style, right_content_2_style = {'display': 'none'}, {'display': 'none'}
    merge_type_container_style = {'display': 'none'}
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    
    # Node Names
    if num_selected == 0:
        name = []
    elif num_selected == 1:
        name = [dbc.Input(value=selectedNodeData[0]['name'], id={'type':id('node_name'), 'index': selectedNodeData[-1]['id']}, disabled=True, style={'font-size':'14px', 'text-align':'center'})]
        
    elif num_selected > 1:
        for node in selectedNodeData:
            name = name + [dbc.Input(value=str(len(name)+1)+') '+node['name'], disabled=True, style={'margin':'5px', 'text-align':'center'})]
        name = [dbc.InputGroup(name)]
    else:
        name = []

    # New/Add Dataset when No Active Tab
    if active_tab is None and num_selected == 0:
        out = dbc.Row([
            dbc.Col([
                html.H1("Select a Node", className="border border-info", style={'text-align':'center'}),
            ], width={'size':10, 'offset':1}),
        ])
    
    # Node Data
    elif active_tab == 'tab1' and all(node['type'] != 'action' for node in selectedNodeData):
        if num_selected == 1:
            data = get_dataset_data(selectedNodeData[-1]['id'])
            data = data.to_dict('records')
            
        elif num_selected > 1:
            merge_type_container_style['display'] = 'block'
            data  = merge_dataset_data(selectedNodeData, merge_type, idRef=merge_idRef)
            
        range_min = 1
        range_max = len(data)
        if triggered != id('range'):
            range_value = [range_min, range_max]
        data = data[range_value[0]-1:range_value[1]]
        out = data
        right_header_2_style['display'] = 'block'
        

    elif active_tab == 'tab2':
        if num_selected == 1:
            if selectedNodeData[0]['type'] == 'action': 
                action = get_document('action', selectedNodeData[0]['id'])
                out = [display_action(action)]
            else:
                dataset = get_document('dataset', selectedNodeData[0]['id'])
                out = [display_metadata(dataset, id, disabled=False)]

        elif num_selected > 1:
            if all(node['type'] == 'action' for node in selectedNodeData): 
                out = []

            elif all(node['type'] != 'action' for node in selectedNodeData): 
                dataset = merge_dataset(selectedNodeData)
                out = [display_metadata(dataset, id, disabled=True)]
    
    elif active_tab == 'tab3':
        out1_display['display'] = 'none'
        out2_display['display'] = 'block'
        right_content_2_style['display'] = 'block'

    else:
        out = []

    return (name, out, out1_display, right_header_2_style,
            right_content_2_style, merge_type_container_style, range_min, range_max, range_value)






# Merge Type Triggers
@app.callback(
    Output(id('merge_idRef'), 'style'),
    Output(id('merge_idRef'), 'options'),
    Output(id('merge_idRef'), 'value'),
    Input(id('merge_type'), 'value'),
    State(id('dataset_data'), 'data'),
)
def merge_type_triggers(merge_type, dataset_data):
    if merge_type is None: return no_update
    style = {'display':'none', 'text-align':'center'}
    options, value = no_update, no_update
    if merge_type == 'arrayMergeById':
        style['display'] = 'block'
        df = json_normalize(dataset_data)
        options = [{'label': c, 'value': c} for c in df.columns]
        value = df.columns[0]
    return style, options, value


# Tabular/Json Format
@app.callback(
    Output(id('right_content'), 'children'),
    Input(id('dataset_data'), 'data'),
    Input(id('button_tabular'), 'n_clicks'),
    State(id('tabs_node'), 'active_tab'),
)
def button_tabular(data, n_clicks, active_tab):
    if active_tab is None:
        out = data
    elif active_tab == 'tab1':
        if n_clicks % 2 == 0: out = display_dataset_data(data, format='json')
        else: out = display_dataset_data(data, format='tabular')
    elif active_tab == 'tab2':
        out = data
    else:
        out = []
    
    return out

# Enable Editing Data Source name when in Config Tab
@app.callback(
    Output({'type': id('node_name'), 'index': ALL}, 'disabled'),
    Input(id('right_content_2'), 'style'),
)
def callback(style):
    if style['display'] != 'none': return [False]
    else: return [True]


# Remove Feature
@app.callback(
    Output({'type': id('col_button_remove_feature'), 'index': MATCH}, 'outline'),
    Input({'type': id('col_button_remove_feature'), 'index': MATCH}, 'n_clicks'),
    prevent_initial_call=True,
)
def button_remove_feature(n_clicks):
    print(callback_context.triggered)
    if n_clicks is None: return no_update
    if n_clicks % 2 == 0: return True
    else: return False


# Load Cytoscape, Button Reset, Merge
@app.callback(
    Output(id('cytoscape'), 'elements'),
    Output(id('cytoscape'), 'layout'),
    Input(id('button_load'), 'n_clicks'),
    Input(id('button_save'), 'n_clicks'),
    Input('url', 'pathname'),
    Input({'type': id('button_remove'), 'index': ALL}, 'n_clicks'),
    Input(id('do_cytoscape_reload'), 'data'),
    Input(id('merge_type'), 'value'),
    Input(id('merge_idRef'), 'value'),
    Input({'type': id('button_add_data_source'), 'index': ALL}, 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('tabs_node'), 'active_tab'),
    State({'type':id('col_feature_hidden'), 'index': ALL}, 'value'),
    State({'type':id('col_feature'), 'index': ALL}, 'value'),
    State({'type':id('col_datatype'), 'index': ALL}, 'value'),
    State({'type':id('col_button_remove_feature'), 'index': ALL}, 'n_clicks'),
    State(id('right_content'), 'style'),
)
def cytoscape_triggers(n_clicks_load, n_clicks_merge, pathname, n_clicks_remove_list, do_cytoscape_reload, merge_type, merge_idRef,
                        n_clicks_add_data_source_list,
                        selectedNodeData, active_tab, feature_list, new_feature_list, datatype_list, button_remove_feature_list,
                        right_content_style):
    num_selected = len(selectedNodeData)
    project_id = get_session('project_id')
    merge_idRef = None if merge_idRef is None else merge_idRef

    if num_selected <= 0:
        triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
        # New Data Source
        if triggered == '{"index":0,"type":"data_lineage-button_add_data_source"}' and n_clicks_add_data_source_list[0] != None:
            dataset_id = new_data_source()
            add_dataset(project_id, dataset_id)
    else:
        triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
        dataset_id = selectedNodeData[0]['id']

        # On Page Load and Reset Button pressed
        if triggered == '' or triggered == id('button_load'):
            pass
        
        elif triggered == id('do_cytoscape_reload'):
            if do_cytoscape_reload == False: return no_update
        
        elif triggered == id('button_save') and right_content_style['display'] != 'none':
            if n_clicks_merge is None: return no_update
            dataset = get_document('dataset', dataset_id)

            if num_selected == 1:
                # Truncate Dataset TODO
                if active_tab == 'tab1' and num_selected == 1:
                    pass

                # Modify Metadata Action
                elif active_tab == 'tab2':
                    new_dataset = dataset.copy()
                    new_dataset['features'] = dict(zip(new_feature_list, datatype_list))
                    remove_list = [feature for feature, n_clicks in zip(new_feature_list, button_remove_feature_list) if (n_clicks % 2 != 0)]
                    for feature in remove_list:
                        new_dataset['features'].pop(feature, None)
                    changed_feature_dict = {f1:f2 for f1, f2 in zip(feature_list, new_feature_list) if f1 != f2}
                    action(project_id, dataset_id, 'metadata', 'description', new_dataset, changed_feature_dict)

            # Merge Datasets Action
            if num_selected > 1:
                dataset_data = merge_dataset_data(selectedNodeData, merge_type, idRef=merge_idRef)
                dataset = merge_dataset(selectedNodeData, 'objectMerge')
                source_id_list = [node['id'] for node in selectedNodeData]
                changes = {'merge_type': merge_type}
                merge(project_id, source_id_list, '', dataset_data, dataset, changes)

        # Button Remove Node
        elif triggered == '{"index":0,"type":"data_lineage-button_remove"}' and n_clicks_remove_list[0] != None:
            node_id_list = [node['id'] for node in selectedNodeData]
            remove(project_id, node_id_list)
                

    elements = generate_cytoscape_elements(project_id)
    layout={'name': 'breadthfirst',
        'fit': True,
        'roots': [e['data']['id'] for e in elements if e['classes'].startswith('raw')]
    }
    return elements, layout


# Disable/Enable Right Panel Buttons
# @app.callback(
#     Output(id('button_save'), 'disabled'),
#     Output(id('button_chart'), 'disabled'),
#     Output(id('button_remove'), 'disabled'),
#     Input(id('tabs_node'), 'active_tab'),
#     Input('url', 'pathname'),
#     State(id('cytoscape'), 'selectedNodeData'),
# )
# def button_disable_enable(active_tab, pathname, selectedNodeData):
#     button1, button2, button3, button4 = True, True, True, True    
#     num_selected = len(selectedNodeData)

#     if num_selected == 1:
#         if active_tab == 'tab1':
#             button1, button2, button3, button4 = True, False, False, False
#         elif active_tab == 'tab2':
#             button1, button2, button3, button4 = True, False, False, False
    
#     elif num_selected > 1:
#         pass

#     return button1, button2, button3, button4 


# Toggle button Tabular
@app.callback(
    Output(id('button_tabular'), 'outline'),
    Input(id('button_tabular'), 'n_clicks'),
)
def toggle_button_tabular(n_clicks):
    if n_clicks is None: return no_update
    if n_clicks % 2 == 0: return True
    else: return False


# Button Chart
@app.callback(Output('url', 'pathname'),
                Input(id('button_chart'), 'n_clicks'),
                State(id('cytoscape'), 'selectedNodeData'))
def button_chart(n_clicks, selectedNodeData):
    if n_clicks is None: return no_update
    if selectedNodeData is None: return no_update
    if len(selectedNodeData) != 1: return no_update
    if selectedNodeData[0]['type'] == 'action': return no_update

    return '/apps/plot_graph'



# Add/Remove Headers, Params, Body
@app.callback(
    Output(id('header_div'), 'children'),
    Output(id('param_div'), 'children'),
    Output(id('body_div'), 'children'),
    Input(id('cytoscape'), 'tapNodeData'),
    Input(id('button_add_header'), 'n_clicks'),
    Input(id('button_remove_header'), 'n_clicks'),
    Input(id('button_add_param'), 'n_clicks'),
    Input(id('button_remove_param'), 'n_clicks'),
    Input(id('button_add_body'), 'n_clicks'),
    Input(id('button_remove_body'), 'n_clicks'),
    State(id('header_div'), 'children'),
    State(id('param_div'), 'children'),
    State(id('body_div'), 'children'),
)
def load_restapi_options(tapNodeData, _, _2, _3, _4, _5, _6, header_div, param_div, body_div):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    if triggered == '' or triggered == None: return no_update
    
    if triggered == id('cytoscape') and tapNodeData['type'] != 'action':
        header_div, param_div, body_div = [], [], []
        dataset = get_document('dataset', tapNodeData['id'])
        if dataset['type'] == 'raw_restapi':
            for k, v in dataset['details']['header'].items():
                header_div += generate_restapi_options(id, 'header', len(header_div), k, v)
            for k, v in dataset['details']['param'].items():
                param_div += generate_restapi_options(id, 'param', len(param_div), k, v)
            for k, v in dataset['details']['body'].items():
                body_div += generate_restapi_options(id, 'body', len(body_div), k, v)
    
    # Add
    if 'add' in triggered:
        if triggered == id('button_add_header'): header_div += generate_restapi_options(id, 'header', len(header_div))
        elif triggered == id('button_add_param'): param_div += generate_restapi_options(id, 'param', len(param_div))
        elif triggered == id('button_add_body'): body_div += generate_restapi_options(id, 'body', len(body_div))

    # Remove
    if 'remove' in triggered:
        if triggered == id('button_remove_header'): header_div = header_div[:-1]
        elif triggered == id('button_remove_param'): param_div = param_div[:-1]
        elif triggered == id('button_remove_body'): body_div = body_div[:-1]

    # Remove n_clicks
    try:
        for i in range(len(header_div)):
            header_div[i]['props']['children'][0]['props']['children'][2]['props']['n_clicks'] = None
        for i in range(len(param_div)):
            param_div[i]['props']['children'][0]['props']['children'][2]['props']['n_clicks'] = None
        for i in range(len(body_div)):
            body_div[i]['props']['children'][0]['props']['children'][2]['props']['n_clicks'] = None

    except Exception as e:
        print('Exception: ', e)

    return header_div, param_div, body_div



for option_type in ['header', 'param', 'body']:
    # Open Modal
    @app.callback(
        Output({'type':id('{}_modal'.format(option_type)), 'index': MATCH}, 'is_open'),
        Input({'type':id('button_{}_value'.format(option_type)), 'index': MATCH}, 'n_clicks')
    )
    def button_open_modal(n_clicks):
        if n_clicks is None or n_clicks == 0: return no_update
        return True

    # Populate Existing Data Source dropdown
    @app.callback(
        Output({'type': id('{}_datasource_list'.format(option_type)), 'index': MATCH}, 'options'),
        Output({'type': id('{}_datasource_list'.format(option_type)), 'index': MATCH}, 'value'),
        Input({'type': id('button_{}_value'.format(option_type)), 'index': MATCH}, 'n_clicks'),
        State(id('cytoscape'), 'selectedNodeData'),
    )
    def populate_datasource_dropdown(n_clicks, selectedNodeData):
        project = get_document('project', get_session('project_id'))
        project_name_list = [{'label': get_document('dataset', dataset_id)['name'], 'value': dataset_id} for dataset_id in project['dataset_list'] if get_document('dataset', dataset_id)['type'].startswith('raw')]
        return project_name_list, ''

    # Populate Datatable
    @app.callback(
        Output({'type': id('{}_value_datatable'.format(option_type)), 'index': MATCH}, 'data'),
        Output({'type': id('{}_value_datatable'.format(option_type)), 'index': MATCH}, 'columns'),
        Input({'type': id('{}_datasource_list').format(option_type), 'index': MATCH}, 'value'),
    )
    def populate_datatable(dataset_id):
        if dataset_id == '' or dataset_id is None: return no_update
        df = get_dataset_data(dataset_id)
        columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]
        return df.to_dict('records'), columns

    # Get Selected Inputs from datatable into input
    @app.callback(
        Output({'type':id('{}_value'.format(option_type)), 'index': MATCH}, 'value'),
        Output({'type':id('{}_value'.format(option_type)), 'index': MATCH}, 'valid'),
        Output({'type':id('{}_value_position'.format(option_type)), 'index': MATCH}, 'value'),
        Input({'type':id('{}_value_datatable'.format(option_type)), 'index': MATCH}, 'selected_cells'),
        Input({'type':id('{}_value'.format(option_type)), 'index': MATCH}, 'value'),
        State({'type':id('{}_value_datatable'.format(option_type)), 'index': MATCH}, 'data'),
        State({'type': id('{}_datasource_list'.format(option_type)), 'index': MATCH}, 'value'),
    )
    def select_input(selected_cells, value, data, dataset_id):
        if callback_context.triggered[0]['prop_id'] == '.': return no_update
        if selected_cells is None: return no_update
        if len(selected_cells) <= 0: return no_update
        triggered = json.loads(callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0])
        out, valid, cell_position_list = no_update, None, no_update

        if 'datatable' in triggered['type']:
            out = ''
            if selected_cells is not None:
                df = json_normalize(data)
                for cell in selected_cells:
                    out = out + str(df.loc[cell['row'], cell['column_id']]) + ','
                out = out[:-1]
                valid = True
                cell_position_list = [{'row': cell['row'], 'col': cell['column_id'], 'id': dataset_id} for cell in selected_cells]
            else:
                valid = None

        elif 'value' in triggered['type']:
            cell_position_list = ''
                
        return out, valid, cell_position_list



# Generate options in dropdown and button 
@app.callback(
    Output(id('dropdown_action'), 'children'),
    Input(id('cytoscape'), 'selectedNodeData'),
    # Input(id('dropdown_action'), 'children')
)
def generate_dropdown_actions(selected_nodes):
    if selected_nodes is None: return no_update
    
    single = [ nav for nav in SIDEBAR_2_LIST  if nav['multiple']==False ]
    multiple = [ nav for nav in SIDEBAR_2_LIST  if nav['multiple']==True ]
    
    # Generate Options
    options = []
    if len(selected_nodes) == 0:
        options = [dbc.DropdownMenuItem('Add Data Source', href='#', id={'type': id('button_add_data_source'), 'index': 0}, style={'background-color':'#90ee90', 'padding':'10px'})]
    if len(selected_nodes) == 1:
        options = [dbc.DropdownMenuItem(nav['label'], href=nav['value'], style={'background-color':'yellow', 'padding':'10px'}) for nav in single]
        options.append(dbc.DropdownMenuItem(divider=True))
        options.append(dbc.DropdownMenuItem('Remove', href='#', id={'type': id('button_remove'), 'index': 0}, style={'background-color':'#FF7F7F', 'padding':'10px', 'text-align':'center'}))
    elif len(selected_nodes) > 1 and all(node['type'] != 'action' for node in selected_nodes):
        options = [dbc.DropdownMenuItem(nav['label'], href=nav['value']) for nav in multiple]

    return options

