from dash import Dash, html, dcc, callback, Output, Input, State, register_page
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import pandas as pd
import plotly.express as px
from datetime import datetime

register_page(__name__)

df = pd.read_csv("assets/reports.csv")
fig_reports_by_platform = px.histogram(df, x = 'platform')
fig_report_types = px.histogram(df, x = 'report_type', facet_col = 'platform')
fig_decisions = px.histogram(df, x = 'platform_decision', facet_col = 'platform')

grid = dag.AgGrid(
            id = "reports-table",
            rowData = df.to_dict("records"),
            columnDefs = [{"field": i} for i in df.columns],
            columnSize = "sizeToFit",
            defaultColDef = {"filter": True},
            dashGridOptions = {"pagination": True, "paginationPageSize":7},
        )

tabs_container = dbc.Container([
    dbc.Tabs([
        dbc.Tab([
            grid
            ],
            label = 'Report Table'),
        dbc.Tab([
            dcc.Graph(id ='id_graph_all_reports', figure = fig_reports_by_platform),
            ],
            label = 'Reports by Platform'
            ),
        dbc.Tab([
            dcc.Graph(id = 'id_graph_reports_types', figure = fig_report_types),
            ],
            label = 'Reports Types by Platform'
            ),
        dbc.Tab([
            dcc.Graph(id = 'id_graph_decisions', figure = fig_decisions)
            ],
            label = 'Decisions by Platform'
            )
        ],
        id = 'all_tabs')
    ])

layout = dbc.Container([
        dbc.Row([html.H1("Data Insights", style = {"text-align":"center"})]),
        dbc.Row(tabs_container)
    ],
    fluid = True
)
