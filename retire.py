import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import multiprocessing as mp
import time
from numba import njit

# Updated sampling distributions based on historical data
INFLATION_MEAN = 0.025
INFLATION_STD = 0.02
SP500_MEAN = 0.105
SP500_STD = 0.20


def single_simulation_batch(batch):
    results = []
    avg_growths = []
    avg_inflations = []
    for initial_asset, annual_expense, years_to_live in batch:
        growths = []
        inflations = []
        asset = initial_asset
        history = np.zeros(years_to_live)
        for year in range(years_to_live):
            g = np.random.normal(SP500_MEAN, SP500_STD)
            i = np.random.normal(INFLATION_MEAN, INFLATION_STD)
            growths.append(g)
            inflations.append(i)
            expense = annual_expense * ((1 + i) ** year)
            asset = asset * (1 + g) - expense
            if asset < 0:
                history[year:] = 0
                break
            history[year] = asset
        results.append(history)
        avg_growths.append(np.mean(growths))
        avg_inflations.append(np.mean(inflations))
    return results, avg_growths, avg_inflations

def simulate_asset_projection(initial_asset, annual_expense, years_to_live, n_simulations=100000, batch_size=100):
    batches = [
        [(initial_asset, annual_expense, years_to_live)] * batch_size
        for _ in range(n_simulations // batch_size)
    ]
    with mp.Pool(processes=mp.cpu_count()) as pool:
        all_results = pool.map(single_simulation_batch, batches)

    results = [sim for batch in all_results for sim in batch[0]]
    all_growths = [g for batch in all_results for g in batch[1]]
    all_inflations = [i for batch in all_results for i in batch[2]]

    results = np.array(results)
    median = np.median(results, axis=0)
    lower = np.percentile(results, 10, axis=0)
    upper = np.percentile(results, 90, axis=0)
    avg_growth = np.mean(all_growths)
    avg_inflation = np.mean(all_inflations)
    return lower, median, upper, avg_growth, avg_inflation

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Retirement Asset Projection with Monte Carlo Simulation"),

    html.Div([
        html.Label("Initial Total Assets: "),
        html.Span(id='total-asset-value', style={'fontWeight': 'bold'}),
    ]),
    dcc.Slider(id='total-asset-slider', min=1000000, max=10000000, step=50000, value=5000000,
               marks={i: f"${i // 1000}K" for i in range(1000000, 10000001, 1000000)}),

    html.Div([
        html.Label("Annual Expense (1st Year): "),
        html.Span(id='expense-value', style={'fontWeight': 'bold'}),
    ]),
    dcc.Slider(id='expense-slider', min=50000, max=500000, step=5000, value=100000,
               marks={i: f"${i // 1000}K" for i in range(50000, 500001, 50000)}),

    html.Div([
        html.Label("Years to Live: "),
        html.Span(id='years-to-live-value', style={'fontWeight': 'bold'}),
    ]),
    dcc.Slider(id='years-slider', min=10, max=50, step=1, value=35,
               marks={i: f"{i}" for i in range(10, 51, 5)}),

    dcc.Loading(
        id="loading-graph",
        type="circle",
        children=[
            dcc.Graph(id='asset-graph'),
            html.Div(id='summary-output', style={
                'marginTop': '20px',
                'fontSize': '16px',
                'display': 'flex',
                'justifyContent': 'center'
            })
        ]
    )
])

@app.callback(Output('total-asset-value', 'children'), Input('total-asset-slider', 'value'))
def update_total_asset_display(value):
    return f"${value:,.0f}"

@app.callback(Output('expense-value', 'children'), Input('expense-slider', 'value'))
def update_expense_display(value):
    return f"${value:,.0f}"

@app.callback(Output('years-to-live-value', 'children'), Input('years-slider', 'value'))
def update_years_to_live_display(value):
    return f"{value}"

@app.callback(
    Output('asset-graph', 'figure'),
    Output('summary-output', 'children'),
    Input('total-asset-slider', 'value'),
    Input('expense-slider', 'value'),
    Input('years-slider', 'value')
)
def update_graph(initial_asset, annual_expense, years_to_live):
    start_time = time.time()
    lower, median, upper, avg_growth, avg_inflation = simulate_asset_projection(
        initial_asset, annual_expense, years_to_live
    )
    duration = time.time() - start_time
    years = np.arange(0, years_to_live)
    real_factor = (1 + INFLATION_MEAN) ** (years_to_live - 1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=median, mode='lines', name='Median'))
    fig.add_trace(go.Scatter(x=years, y=upper, mode='lines', name='90th Percentile', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=years, y=lower, mode='lines', name='10th Percentile', fill='tonexty', line=dict(width=0), showlegend=True))

    fig.update_layout(title='Monte Carlo Simulation: Portfolio Balance Over Time',
                      xaxis_title='Years',
                      yaxis_title='Total Assets ($)',
                      hovermode='x')

    table = html.Div([
        html.Table([
            html.Caption("Simulation Summary", className="text-center fw-bold mb-2", style={'fontSize': '20px'}),
            html.Thead(html.Tr([
                html.Th("Metric", className="text-center align-middle"),
                html.Th("Nominal Amount", className="text-center align-middle"),
                html.Th("Real Amount", className="text-center align-middle")
            ])),
            html.Tbody([
                html.Tr([html.Td("10th Percentile Final Asset"), html.Td(f"${lower[-1]:,.0f}"),
                         html.Td(f"${lower[-1] / real_factor:,.0f}")]),
                html.Tr([html.Td("Median Final Asset"), html.Td(f"${median[-1]:,.0f}"),
                         html.Td(f"${median[-1] / real_factor:,.0f}")]),
                html.Tr([html.Td("90th Percentile Final Asset"), html.Td(f"${upper[-1]:,.0f}"),
                         html.Td(f"${upper[-1] / real_factor:,.0f}")]),
                html.Tr([html.Td("Input: Avg Inflation Rate"), html.Td(f"{INFLATION_MEAN * 100:.2f}%"), html.Td("—")]),
                html.Tr([html.Td("Input: Avg Growth Rate"), html.Td(f"{SP500_MEAN * 100:.2f}%"), html.Td("—")]),
                html.Tr(
                    [html.Td("Simulated Avg Inflation Rate"), html.Td(f"{avg_inflation * 100:.2f}%"), html.Td("—")]),
                html.Tr([html.Td("Simulated Avg Growth Rate"), html.Td(f"{avg_growth * 100:.2f}%"), html.Td("—")]),
                html.Tr([html.Td("Simulation Time"), html.Td(f"{duration:.2f} seconds", colSpan=2)])
            ])
        ], className="table table-bordered table-hover table-striped table-sm text-center align-middle", style={
            'width': '90%',
            'margin': 'auto',
            'fontSize': '15px',
            'borderCollapse': 'collapse',
            'borderSpacing': '0'
        })
    ])

    return fig, table

if __name__ == '__main__':
    app.run_server(debug=True)
