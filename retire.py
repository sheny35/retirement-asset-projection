
import os
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import time
from numba import njit

INFLATION_STD = 0.02
SP500_STD = 0.20
SIMULATION_ROUNDS = 100000

@njit
def single_simulation_batch_numba(initial_asset, annual_expense, years_to_live, batch_size,
                                   inflation_mean, growth_mean, annual_income, income_start_year):
    results = np.zeros((batch_size, years_to_live))
    avg_growths = np.zeros(batch_size)
    avg_inflations = np.zeros(batch_size)

    for b in range(batch_size):
        asset = initial_asset
        history = np.zeros(years_to_live)
        growth_sum = 0.0
        inflation_sum = 0.0

        for year in range(years_to_live):
            g = np.random.normal(growth_mean, SP500_STD)
            i = np.random.normal(inflation_mean, INFLATION_STD)
            growth_sum += g
            inflation_sum += i

            # Add income if applicable
            income = 0.0
            if year >= income_start_year:
                income = annual_income * ((1 + i) ** year)

            expense = annual_expense * ((1 + i) ** year)
            asset = asset * (1 + g) + income - expense
            if asset < 0:
                history[year:] = 0
                break
            history[year] = asset

        results[b, :] = history
        avg_growths[b] = growth_sum / years_to_live
        avg_inflations[b] = inflation_sum / years_to_live

    return results, avg_growths, avg_inflations

def simulate_asset_projection(initial_asset, annual_expense, years_to_live,
                              n_simulations=SIMULATION_ROUNDS, batch_size=1000,
                              inflation_mean=0.025, growth_mean=0.105, annual_income=0, income_start_year=0):
    num_batches = n_simulations // batch_size
    all_results = []
    all_growths = []
    all_inflations = []

    for _ in range(num_batches):
        results, growths, inflations = single_simulation_batch_numba(
            initial_asset, annual_expense, years_to_live, batch_size,
            inflation_mean, growth_mean, annual_income, income_start_year
        )
        all_results.append(results)
        all_growths.append(growths)
        all_inflations.append(inflations)

    results = np.vstack(all_results)
    all_growths = np.concatenate(all_growths)
    all_inflations = np.concatenate(all_inflations)

    final_assets = results[:, -1]

    # Calculate ruin risk (probability of running out of money)
    ruin_count = np.sum(final_assets <= 0)
    ruin_probability = (ruin_count / n_simulations) * 100

    p10, p50, p90 = np.percentile(final_assets, [10, 50, 90])
    p45, p55 = np.percentile(final_assets, [45, 55])

    idx_10th = (final_assets <= p10)
    idx_median = (final_assets > p45) & (final_assets <= p55)
    idx_90th = (final_assets >= p90)

    group_stats = {
        '10th': {
            'final': np.percentile(final_assets[idx_10th], 10),
            'inflation_avg': np.mean(all_inflations[idx_10th]),
            'inflation_median': np.median(all_inflations[idx_10th]),
            'growth_avg': np.mean(all_growths[idx_10th]),
            'growth_median': np.median(all_growths[idx_10th]),
        },
        '50th': {
            'final': np.percentile(final_assets[idx_median], 50),
            'inflation_avg': np.mean(all_inflations[idx_median]),
            'inflation_median': np.median(all_inflations[idx_median]),
            'growth_avg': np.mean(all_growths[idx_median]),
            'growth_median': np.median(all_growths[idx_median]),
        },
        '90th': {
            'final': np.percentile(final_assets[idx_90th], 90),
            'inflation_avg': np.mean(all_inflations[idx_90th]),
            'inflation_median': np.median(all_inflations[idx_90th]),
            'growth_avg': np.mean(all_growths[idx_90th]),
            'growth_median': np.median(all_growths[idx_90th]),
        },
    }

    lower = np.percentile(results, 10, axis=0)
    median = np.percentile(results, 50, axis=0)
    upper = np.percentile(results, 90, axis=0)
    return lower, median, upper, group_stats, ruin_probability

external_stylesheets = ['https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div([
        html.H1("Retirement Asset Projection", className="text-center my-4"),

        # Key Results Section (will be populated by callback)
        dcc.Loading(
            id="loading-key-results",
            type="circle",
            children=[html.Div(id='key-results', className='mb-4')]
        ),

        # Chart Section
        dcc.Loading(
            id="loading-graph",
            type="circle",
            children=[dcc.Graph(id='asset-graph')]
        ),

        # Input Controls Section
        html.Div([
            html.H4("Adjust Your Scenario", className="text-center mt-4 mb-3"),

            html.Label("Initial Total Assets: "), html.Span(id='total-asset-value', className="fw-bold"),
            dcc.Slider(id='total-asset-slider', min=1000000, max=10000000, step=50000, value=5000000,
                       marks={i: f"${i // 1000}K" for i in range(1000000, 10000001, 1000000)}),

            html.Label("Annual Expense (1st Year): "), html.Span(id='expense-value', className="fw-bold"),
            dcc.Slider(id='expense-slider', min=50000, max=500000, step=5000, value=100000,
                       marks={i: f"${i // 1000}K" for i in range(50000, 500001, 50000)}),

            html.Label("Years to Live: "), html.Span(id='years-to-live-value', className="fw-bold"),
            dcc.Slider(id='years-slider', min=10, max=50, step=1, value=35,
                       marks={i: f"{i}" for i in range(10, 51, 5)}),

            html.Label("Annual Income (Social Security, Pension, etc.): "), html.Span(id='income-value', className="fw-bold"),
            dcc.Slider(id='income-slider', min=0, max=100000, step=5000, value=0,
                       marks={i: f"${i // 1000}K" for i in range(0, 100001, 20000)}),

            html.Label("Income Start Year: "), html.Span(id='income-start-value', className="fw-bold"),
            dcc.Slider(id='income-start-slider', min=0, max=20, step=1, value=0,
                       marks={i: f"{i}" for i in range(0, 21, 5)}),

            html.Label("Inflation Mean (%): "), html.Span(id='inflation-mean-value', className="fw-bold"),
            dcc.Slider(id='inflation-mean-slider', min=0.0, max=0.1, step=0.001, value=0.025,
                       marks={i/100: f"{i}%" for i in range(0, 11, 1)}),

            html.Label("Growth Mean (%): "), html.Span(id='growth-mean-value', className="fw-bold"),
            dcc.Slider(id='growth-mean-slider', min=0.0, max=0.2, step=0.001, value=0.105,
                       marks={i/100: f"{i}%" for i in range(0, 21, 2)}),
        ], className="mb-4"),

        # Detailed Summary Section
        html.Div(id='summary-output', className='mt-4')
    ], className="container")
])

@app.callback(Output('total-asset-value', 'children'), Input('total-asset-slider', 'value'))
def update_total_asset_display(value): return f"${value:,.0f}"

@app.callback(Output('expense-value', 'children'), Input('expense-slider', 'value'))
def update_expense_display(value): return f"${value:,.0f}"

@app.callback(Output('years-to-live-value', 'children'), Input('years-slider', 'value'))
def update_years_to_live_display(value): return f"{value}"

@app.callback(Output('inflation-mean-value', 'children'), Input('inflation-mean-slider', 'value'))
def update_inflation_display(value): return f"{value*100:.2f}%"

@app.callback(Output('growth-mean-value', 'children'), Input('growth-mean-slider', 'value'))
def update_growth_display(value): return f"{value*100:.2f}%"

@app.callback(Output('income-value', 'children'), Input('income-slider', 'value'))
def update_income_display(value): return f"${value:,.0f}"

@app.callback(Output('income-start-value', 'children'), Input('income-start-slider', 'value'))
def update_income_start_display(value): return f"{value} years"

@app.callback(
    Output('asset-graph', 'figure'),
    Output('summary-output', 'children'),
    Output('key-results', 'children'),
    Input('total-asset-slider', 'value'),
    Input('expense-slider', 'value'),
    Input('years-slider', 'value'),
    Input('inflation-mean-slider', 'value'),
    Input('growth-mean-slider', 'value'),
    Input('income-slider', 'value'),
    Input('income-start-slider', 'value')
)
def update_graph(initial_asset, annual_expense, years_to_live, inflation_mean, growth_mean, annual_income, income_start_year):
    start_time = time.time()
    lower, median, upper, group_stats, ruin_probability = simulate_asset_projection(
        initial_asset, annual_expense, years_to_live,
        inflation_mean=inflation_mean, growth_mean=growth_mean,
        annual_income=annual_income, income_start_year=income_start_year
    )
    duration = time.time() - start_time
    years = np.arange(0, years_to_live)
    real_factor = (1 + inflation_mean) ** (years_to_live - 1)

    # Determine success color
    if ruin_probability < 10:
        success_color = "success"
        success_message = "Excellent! Your retirement plan looks very secure."
    elif ruin_probability < 30:
        success_color = "warning"
        success_message = "Acceptable risk level, but consider adjustments for better security."
    else:
        success_color = "danger"
        success_message = "High risk! Consider reducing expenses or increasing assets."

    # Key Results Cards
    key_results = html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.H5("Success Rate", className="card-title"),
                    html.H2(f"{100 - ruin_probability:.1f}%", className=f"text-{success_color}"),
                    html.P(f"Risk of running out: {ruin_probability:.1f}%", className="card-text"),
                    html.P(success_message, className="card-text small")
                ], className="card-body text-center")
            ], className="card border-primary mb-3", style={"display": "inline-block", "width": "32%", "margin": "0.5%"}),

            html.Div([
                html.Div([
                    html.H5("Median Final Balance", className="card-title"),
                    html.H2(f"${median[-1]:,.0f}", className="text-primary"),
                    html.P(f"Today's Dollars: ${median[-1] / real_factor:,.0f}", className="card-text"),
                    html.P("50% chance of having more than this", className="card-text small")
                ], className="card-body text-center")
            ], className="card border-primary mb-3", style={"display": "inline-block", "width": "32%", "margin": "0.5%"}),

            html.Div([
                html.Div([
                    html.H5("Worst Case (10th %ile)", className="card-title"),
                    html.H2(f"${lower[-1]:,.0f}", className="text-info"),
                    html.P(f"Today's Dollars: ${lower[-1] / real_factor:,.0f}", className="card-text"),
                    html.P("90% chance of doing better", className="card-text small")
                ], className="card-body text-center")
            ], className="card border-primary mb-3", style={"display": "inline-block", "width": "32%", "margin": "0.5%"}),
        ], className="text-center")
    ])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=median, mode='lines', name='Median'))
    fig.add_trace(go.Scatter(x=years, y=upper, mode='lines', name='90th Percentile', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=years, y=lower, mode='lines', name='10th Percentile', fill='tonexty', line=dict(width=0), showlegend=True))
    fig.update_layout(title='Monte Carlo Simulation: Portfolio Balance Over Time',
                      xaxis_title='Years', yaxis_title='Total Assets ($)', hovermode='x')

    def asset_row(label, final_asset, inflation_avg, inflation_median, growth_avg, growth_median):
        return html.Tr([
            html.Td(label),
            html.Td(f"${final_asset:,.0f}"),
            html.Td(f"${final_asset / real_factor:,.0f}"),
            html.Td(f"{inflation_avg * 100:.2f}%"),
            html.Td(f"{inflation_median * 100:.2f}%"),
            html.Td(f"{growth_avg * 100:.2f}%"),
            html.Td(f"{growth_median * 100:.2f}%")
        ])

    asset_table = html.Div([
        html.H5("Detailed Outcome Analysis", className="text-center fw-bold mb-3"),
        html.Table([
            html.Thead(html.Tr([
                html.Th("Scenario"),
                html.Th("Future Dollars"),
                html.Th("Today's Dollars"),
                html.Th("Avg Inflation"),
                html.Th("Median Inflation"),
                html.Th("Avg Growth"),
                html.Th("Median Growth")
            ])),
            html.Tbody([
                asset_row("10th Percentile Final Asset", lower[-1],
                          group_stats['10th']['inflation_avg'], group_stats['10th']['inflation_median'],
                          group_stats['10th']['growth_avg'], group_stats['10th']['growth_median']),
                asset_row("Median Final Asset", median[-1],
                          group_stats['50th']['inflation_avg'], group_stats['50th']['inflation_median'],
                          group_stats['50th']['growth_avg'], group_stats['50th']['growth_median']),
                asset_row("90th Percentile Final Asset", upper[-1],
                          group_stats['90th']['inflation_avg'], group_stats['90th']['inflation_median'],
                          group_stats['90th']['growth_avg'], group_stats['90th']['growth_median']),
            ])
        ], className="table table-bordered table-hover table-sm text-center")
    ], className="mb-4")

    tech_table = html.Details([
        html.Summary("Advanced Details (click to expand)", className="text-center fw-bold mb-3", style={"cursor": "pointer"}),
        html.Table([
            html.Thead(html.Tr([html.Th("Metric"), html.Th("Value")])),
            html.Tbody([
                html.Tr([html.Td("Simulation Time"), html.Td(f"{duration:.2f} seconds")]),
                html.Tr([html.Td("Simulation Rounds"), html.Td(f"{SIMULATION_ROUNDS:,} simulations")])
            ])
        ], className="table table-bordered table-hover table-sm text-center")
    ], className="mb-4")

    return fig, html.Div([asset_table, tech_table]), key_results

if __name__ == '__main__':
    debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '8050'))
    app.run(host=host, port=port, debug=debug_mode)
