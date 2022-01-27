import dash
import dash_bootstrap_components as dbc
from dash_extensions.enrich import DashProxy, MultiplexerTransform
import sentry_sdk

# Sentry
sentry_sdk.init(
    "https://c44f48907043459dab2a41fecc0216cb@o1119809.ingest.sentry.io/6154603",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)

# External Scripts
external_scripts = [
    # {'src': 'https://cdn.jsdelivr.net/npm/typesense@latest/dist/typesense.min.js', 'type':'module', 'data-main': 'main'},
    # {'src': '/assets/require.js', 'data-main': 'main', 'type':'module'},
    {'src': '/assets/typesense.js', 'data-main': 'main', 'type':'module'},
    # {'src': '/assets/typesense.min.js', 'data-main': 'main'},
    {'src': 'http://requirejs.org/docs/release/2.1.5/comments/require.js', 'type':'module', 'data-main': 'main'}
]

# Stylesheet
FA = {
    "href": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css",
    "rel": "stylesheet",
    "integrity": "sha512-iBBXm8fW90+nuLcSKlbmrPcLa0OT92xO1BIsZ+ywDWZCvqsWgccV3gFoRBv0z+8dLJgyAHIhR35VZc2oM/gI1w==",
    "crossorigin": "anonymous",
    "referrerpolicy": "no-referrer",
}
external_stylesheets = [dbc.themes.BOOTSTRAP, FA, 'https://codepen.io/chriddyp/pen/bWLwgP.css']

# App
app = DashProxy(__name__,
                suppress_callback_exceptions=True,
                external_scripts=external_scripts,
                transforms=[MultiplexerTransform()],
                external_stylesheets=external_stylesheets,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}],
                title='AI-SDK'
                )

app.layout = dbc.Container(
    dbc.Alert("Wrangle Data!", color="success"),
    className="p-5",
)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        {%scripts%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            
            {%renderer%}
            
        </footer>
    </body>
</html>
'''

server = app.server



