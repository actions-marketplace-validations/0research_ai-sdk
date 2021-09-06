import json
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
from app import app
import dash_bootstrap_components as dbc
import dash_table
from dash import no_update, callback_context
import json
from flatten_json import flatten, unflatten, unflatten_list
from jsonmerge import Merger
from pprint import pprint
from genson import SchemaBuilder
from jsondiff import diff
import json
import os
from jsondiff import diff



def generate_tab(label, value):
    return dcc.Tab(
                label=label,
                value=value,
                className='custom-tab',
                selected_className='custom-tab--selected'
            )

def generate_tabs(tabs_id, tab_labels, tab_values):
    return dcc.Tabs(
        id=tabs_id,
        parent_className='custom-tabs',
        className='custom-tabs-container',
        children=[
            generate_tab(label, value) for label, value in zip(tab_labels, tab_values)
        ],
    )

def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

def get_data(path):
    data = {}
    for file in os.listdir(path):
        full_filename = "%s/%s" % (path, file)
        with open(full_filename,'r') as f:
            data[file] = json.load(f)
    
    return data

def generate_upload(component_id, display_text=None):
    if display_text is not None:
        display_text = html.A(display_text)
    else:
        display_text = html.A('Drag and Drop or Click Here to Select Files')

    return dcc.Upload(
        id=component_id,
        children=html.Div([
            display_text
        ]),
        style={
            'width': '90%',
            'height': '120px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px',
        },
        multiple=True
    )

def generate_json_tree(component_id, data):
    return html.Div(children=[
        # html.Button('Submit', id='button'),
        # html.Div(dcc.Input(id='input-box', type='text')),
        json_dash.jsondash(
            id=component_id,
            json=data,
            height=800,
            width=600,
            selected_node='',
        ),
    ])

def filter_dict(json_dict, args):
    dict1 = json_dict[:]
    for i in range(len(args)):
        dict1 = dict1[args[i]]

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),
        html.P("Inset X axis data"),
        dcc.Dropdown(id='xaxis-data', options=[{'label': x, 'value': x} for x in df.columns], persistence=True),
        html.P("Inset Y axis data"),
        dcc.Dropdown(id='yaxis-data', options=[{'label': x, 'value': x} for x in df.columns], persistence=True),
        html.Button(id="submit-button", children="Create Graph"),
        html.Hr(),

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            page_size=15
        ),
        dcc.Store(id='stored-data', data=df.to_dict('records')),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

def flatten_json(data):
    if type(data) == list:
        for i in range(len(data)):
            data[i] = flatten(data[i])
    elif type(data) == dict:
        data = flatten(data)
    return data

def generate_selection(index):
    index = str(index)
    id_select_button = 'select_list_merge_'+index
    id_selected_list = 'selected_list_merge_'+index
    id_button_clear = {'type': 'select_button_merge_'+index, 'index': -1}

    return [
        html.Div(id=id_selected_list, style={'border-style': 'outset', 'margin': '5px'}),
        html.Button('Clear Selection', id=id_button_clear, style={'width':'90%'}),
        html.Br(),
        html.Br(),
        dbc.ButtonGroup(id=id_select_button)]

def get_selected_merge_strategy(selected_tab):
    merge_strategy = None
    if selected_tab == 'tab-1': merge_strategy = 'overwrite'
    elif selected_tab == 'tab-2': merge_strategy = 'objectMerge'
    elif selected_tab == 'tab-3': merge_strategy = 'version'
    return merge_strategy

def json_merge(base, new, merge_strategy):
    schema = {'mergeStrategy': merge_strategy}
    merger = Merger(schema)
    base = merger.merge(base, new)
    return base

