import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go


# Function to calculate the total asset over years with special years consideration
def calculate_total_assets(current_total_asset, initial_expense, inflation_rate, investment_growth_rate, years_to_live,
                           special_year_1, custom_growth_rate_1, custom_spending_1, custom_inflation_rate_1,
                           special_year_2, custom_growth_rate_2, custom_spending_2, custom_inflation_rate_2):
    total_assets = [current_total_asset]
    compound_inflation_rate = 1  # To calculate the compound inflation rate

    for year in range(1, years_to_live):
        if year == special_year_1:
            compound_inflation_rate *= (1 + custom_inflation_rate_1)
            expense = custom_spending_1
            current_growth_rate = custom_growth_rate_1
        elif year == special_year_2:
            compound_inflation_rate *= (1 + custom_inflation_rate_2)
            expense = custom_spending_2
            current_growth_rate = custom_growth_rate_2
        else:
            compound_inflation_rate *= (1 + inflation_rate)
            expense = initial_expense * compound_inflation_rate
            current_growth_rate = investment_growth_rate

        current_total_asset = current_total_asset * (1 + current_growth_rate) - expense

        if current_total_asset < 0:
            total_assets.extend([0] * (years_to_live - year))
            break

        total_assets.append(current_total_asset)

    return total_assets


# Function to calculate the natural spending for a given year based on compound inflation rate
def calculate_natural_spending(initial_expense, inflation_rate, year, special_year_1, custom_inflation_rate_1,
                               special_year_2, custom_inflation_rate_2):
    compound_inflation_rate = 1

    # Calculate compound inflation rate year-by-year
    for current_year in range(1, year + 1):
        if current_year == special_year_1:
            compound_inflation_rate *= (1 + custom_inflation_rate_1)
        elif current_year == special_year_2:
            compound_inflation_rate *= (1 + custom_inflation_rate_2)
        else:
            compound_inflation_rate *= (1 + inflation_rate)

    return initial_expense * compound_inflation_rate


# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the dashboard
app.layout = html.Div([
    html.H1("Retirement Asset Projection"),

    # Sliders for input parameters with dynamic values displayed
    html.Div([
        html.Label("Initial Total Assets: "),
        html.Span(id='total-asset-value', style={'fontWeight': 'bold'}),
    ]),
    dcc.Slider(id='total-asset-slider', min=1000000, max=10000000, step=50000, value=4000000,
               marks={i: f"${i // 1000}K" for i in range(1000000, 10000001, 1000000)}),

    html.Div([
        html.Label("Inflation Rate (%): "),
        html.Span(id='inflation-rate-value', style={'fontWeight': 'bold'}),
    ]),
    dcc.Slider(id='inflation-slider', min=0, max=0.1, step=0.001, value=0.05,
               marks={i: f"{i * 100:.0f}%" for i in np.arange(0, 0.11, 0.01)}),

    html.Div([
        html.Label("Investment Growth Rate (%): "),
        html.Span(id='growth-rate-value', style={'fontWeight': 'bold'}),
    ]),
    dcc.Slider(id='growth-slider', min=0, max=0.15, step=0.001, value=0.07,
               marks={i: f"{i * 100:.0f}%" for i in np.arange(0, 0.16, 0.01)}),

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

    # Special event 1 input
    html.H3("Special Event 1"),
    html.Label("Special Year 1 (e.g. 5): "),
    dcc.Input(id='special-year-input-1', type='number', placeholder='Year #', min=1, max=50, step=1),

    html.Div(id='special-year-settings-1', children=[
        html.Label("Custom Growth Rate 1 (%):"),
        dcc.Input(id='custom-growth-input-1', type='number', step=0.001, value=0.07),

        html.Label("Custom Inflation Rate 1 (%):"),
        dcc.Input(id='custom-inflation-input-1', type='number', step=0.001, value=0.05),

        html.Label("Custom Spending 1 ($):"),
        dcc.Input(id='custom-spending-input-1', type='text', value="100000")
    ]),

    # Special event 2 input
    html.H3("Special Event 2"),
    html.Label("Special Year 2 (e.g. 10): "),
    dcc.Input(id='special-year-input-2', type='number', placeholder='Year #', min=1, max=50, step=1),

    html.Div(id='special-year-settings-2', children=[
        html.Label("Custom Growth Rate 2 (%):"),
        dcc.Input(id='custom-growth-input-2', type='number', step=0.001, value=0.07),

        html.Label("Custom Inflation Rate 2 (%):"),
        dcc.Input(id='custom-inflation-input-2', type='number', step=0.001, value=0.05),

        html.Label("Custom Spending 2 ($):"),
        dcc.Input(id='custom-spending-input-2', type='text', value="100000")
    ]),

    # Graph to display the result
    dcc.Graph(id='asset-graph')
])


# Callback to update the displayed values next to each slider
@app.callback(
    Output('total-asset-value', 'children'),
    Input('total-asset-slider', 'value')
)
def update_total_asset_display(value):
    return f"${value:,.0f}"


@app.callback(
    Output('inflation-rate-value', 'children'),
    Input('inflation-slider', 'value')
)
def update_inflation_rate_display(value):
    return f"{value * 100:.2f}%"


@app.callback(
    Output('growth-rate-value', 'children'),
    Input('growth-slider', 'value')
)
def update_growth_rate_display(value):
    return f"{value * 100:.2f}%"


@app.callback(
    Output('expense-value', 'children'),
    Input('expense-slider', 'value')
)
def update_expense_display(value):
    return f"${value:,.0f}"


@app.callback(
    Output('years-to-live-value', 'children'),
    Input('years-slider', 'value')
)
def update_years_to_live_display(value):
    return f"{value}"


# Callback to auto-populate the special year 1 spending based on natural growth
@app.callback(
    Output('custom-spending-input-1', 'value'),
    Input('special-year-input-1', 'value'),
    State('expense-slider', 'value'),
    State('inflation-slider', 'value'),
    State('special-year-input-2', 'value'),
    State('custom-inflation-input-1', 'value'),
    State('custom-inflation-input-2', 'value')
)
def populate_special_year_spending_1(special_year_1, initial_expense, inflation_rate, special_year_2,
                                     custom_inflation_rate_1, custom_inflation_rate_2):
    if special_year_1 is None:
        return "100000"  # Default value if no special year is chosen

    # Calculate natural spending for the special year 1 using compound inflation rate
    natural_spending = calculate_natural_spending(initial_expense, inflation_rate, special_year_1,
                                                  special_year_1, custom_inflation_rate_1,
                                                  special_year_2, custom_inflation_rate_2)
    return f"{natural_spending:.0f}"  # Return the calculated spending as a string


# Callback to auto-populate the special year 2 spending based on natural growth
@app.callback(
    Output('custom-spending-input-2', 'value'),
    Input('special-year-input-2', 'value'),
    State('expense-slider', 'value'),
    State('inflation-slider', 'value'),
    State('special-year-input-1', 'value'),
    State('custom-inflation-input-1', 'value'),
    State('custom-inflation-input-2', 'value')
)
def populate_special_year_spending_2(special_year_2, initial_expense, inflation_rate, special_year_1,
                                     custom_inflation_rate_1, custom_inflation_rate_2):
    if special_year_2 is None:
        return "100000"  # Default value if no special year is chosen

    # Calculate natural spending for the special year 2 using compound inflation rate
    natural_spending = calculate_natural_spending(initial_expense, inflation_rate, special_year_2,
                                                  special_year_1, custom_inflation_rate_1,
                                                  special_year_2, custom_inflation_rate_2)
    return f"{natural_spending:.0f}"  # Return the calculated spending as a string


# Callback to update the graph when any slider or input changes
@app.callback(
    Output('asset-graph', 'figure'),
    Input('total-asset-slider', 'value'),
    Input('inflation-slider', 'value'),
    Input('growth-slider', 'value'),
    Input('expense-slider', 'value'),
    Input('years-slider', 'value'),
    Input('special-year-input-1', 'value'),
    Input('custom-growth-input-1', 'value'),
    Input('custom-spending-input-1', 'value'),
    Input('custom-inflation-input-1', 'value'),
    Input('special-year-input-2', 'value'),
    Input('custom-growth-input-2', 'value'),
    Input('custom-spending-input-2', 'value'),
    Input('custom-inflation-input-2', 'value')
)
def update_graph(current_total_asset, inflation_rate, investment_growth_rate, annual_expense, years_to_live,
                 special_year_1, custom_growth_rate_1, custom_spending_1, custom_inflation_rate_1,
                 special_year_2, custom_growth_rate_2, custom_spending_2, custom_inflation_rate_2):
    # If no special year is provided, don't apply special adjustments
    if special_year_1 is None:
        special_year_1 = -1  # Invalid year to ensure no special handling is applied
    if special_year_2 is None:
        special_year_2 = -1  # Invalid year to ensure no special handling is applied

    # Convert the custom spending inputs to floats
    try:
        custom_spending_1 = float(custom_spending_1.replace(",", ""))
    except ValueError:
        custom_spending_1 = 100000  # Default if invalid input

    try:
        custom_spending_2 = float(custom_spending_2.replace(",", ""))
    except ValueError:
        custom_spending_2 = 100000  # Default if invalid input

    # Calculate the total assets over the years based on current slider values and special year inputs
    years = np.arange(0, years_to_live)
    total_assets = calculate_total_assets(current_total_asset, annual_expense, inflation_rate, investment_growth_rate,
                                          years_to_live, special_year_1, custom_growth_rate_1, custom_spending_1,
                                          custom_inflation_rate_1, special_year_2, custom_growth_rate_2,
                                          custom_spending_2, custom_inflation_rate_2)

    # Remaining total asset at the last year
    remaining_total_asset = total_assets[-1]

    # Calculate the remaining total asset's actual value (buying power compared to the 1st year)
    remaining_buying_power = remaining_total_asset / ((1 + inflation_rate) ** (years_to_live - 1))

    # Create the Plotly figure
    fig = go.Figure(data=go.Scatter(x=years, y=total_assets, mode='lines', name='Total Assets'))

    # Add annotation for the remaining total asset and its actual value
    fig.add_annotation(
        x=years_to_live - 1,
        y=remaining_total_asset,
        text=f"Remaining: ${remaining_total_asset:,.0f}<br>Real Value: ${remaining_buying_power:,.0f}",
        showarrow=True,
        arrowhead=2,
        ax=-50,
        ay=-40
    )

    # Update layout with titles and axis labels
    fig.update_layout(title='Total Assets Over Time',
                      xaxis_title='Years',
                      yaxis_title='Total Assets',
                      yaxis_range=[0, max(total_assets) * 1.1])

    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
