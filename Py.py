import numpy as np
import pandas as pd
import yfinance as yf
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash import dash_table
import plotly.graph_objs as go

# Initialize the app
app = dash.Dash(__name__)
server = app.server

def download_data(tickers):
    # Define Tickers object
    tickers_obj = yf.Tickers(tickers)
    
    # Get historical data from 2000 to 2023
    hist_data = tickers_obj.history(start="2010-01-01", end="2023-12-31", group_by="ticker")
    
    # Initialize empty DataFrame to store data
    final_data = pd.DataFrame()

    # Iterate over each ticker
    for ticker in tickers:
        data = hist_data[ticker].copy()  # Get data for specific ticker
        data.index = data.index.tz_localize(None)  # Make the date timezone neutral

        # Keep only Close and Volume columns
        data = data[["Close", "Volume"]]

        # Add Ticker column
        data["Ticker"] = ticker
        
        # Append data to the final DataFrame
        final_data = final_data.append(data)

    # Reset index, rename columns, sort by 'Date' and reorder columns
    final_data = (final_data.reset_index()
                              .rename(columns={"index": "Date"})
                              .sort_values(by="Date")
                              .reindex(columns=["Date", "Ticker", "Close", "Volume"]))

    # Write the dataframe to a csv file
    final_data.to_csv('yahoo.csv', index=False)

    # Read the csv file into a pandas DataFrame
    yahoo = pd.read_csv(
        filepath_or_buffer='yahoo.csv',
        parse_dates=['Date']
    )

    return yahoo

tickers = ['NVDA','MSFT','META','PANW','TSLA','AAPL','PEP','JPM','AMZN','GOOG','MMM','DIS','CVS','PYPL','KO','BB','AMC','BTE','APE','IQ',
    "XLY",      # S&P 500 Consumer Discretionary
    "XLP",      # S&P 500 Consumer Staples
    "XLE",      # S&P 500 Energy
    "XLF",      # S&P 500 Financials
    "XLV",      # S&P 500 Health Care
    "XLI",      # S&P 500 Industrials
    "XLK",      # S&P 500 Information Technology
    "XLB",      # S&P 500 Materials
    "XLU",      # S&P 500 Utilities
]

yahoo = download_data(tickers)

# Calculate daily return
yahoo['Daily Return'] = yahoo.groupby('Ticker')['Close'].pct_change()

# Calculate cumulative return
yahoo['Cumulative Return'] = yahoo.groupby('Ticker')['Daily Return'].apply(lambda x: (1 + x).cumprod())

# Replace N/A
yahoo.replace([np.inf, -np.inf], np.nan, inplace=True)

# Establishing the min and max years
min_year = yahoo['Date'].dt.year.min()
max_year = yahoo['Date'].dt.year.max()

# Divide into two categories
data_categories = ['Stocks', 'S&P 500']

app.layout = html.Div([
    dcc.Dropdown(
        id="data_category",
        options=[{"label": x, "value": x} for x in data_categories],
        value=data_categories[0],
        clearable=False,
    ),
    dcc.Dropdown(
        id="ticker",
        options=[{"label": x, "value": x} for x in yahoo['Ticker'].unique()],
        value=yahoo['Ticker'].unique()[0],
        clearable=False,
    ),
    dcc.RangeSlider(
        id='year_slider',
        min=min_year,
        max=max_year,
        value=[min_year, max_year],
        marks={str(year): str(year) for year in range(min_year, max_year+1)},
        step=None
    ),
    dcc.Graph(id="time-series-chart"),
    dash_table.DataTable(id='table')
])

@app.callback(
    Output("ticker", "options"), 
    [Input("data_category", "value")])

def update_ticker_options(selected_category):
    if selected_category == 'Stocks':
        tickers = ['NVDA','MSFT','META','PANW','TSLA','AAPL','PEP','JPM','AMZN','GOOG','MMM','DIS','CVS','PYPL','KO','BB','AMC','BTE','APE','IQ']
    else:  # selected_category == 'S&P 500'
        tickers = ["XLY", "XLP", "XLE", "XLF", "XLV", "XLI", "XLK", "XLB", "XLU"]
    return [{"label": x, "value": x} for x in tickers]

@app.callback(
    Output("time-series-chart", "figure"), 
    [Input("ticker", "value"),
     Input("year_slider", "value")])

def update_graph(ticker_selected, year_range):
    df = yahoo[(yahoo['Ticker'] == ticker_selected) & (yahoo['Date'].dt.year >= year_range[0]) & (yahoo['Date'].dt.year <= year_range[1])]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name="Close"))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Daily Return'], name="Daily Return"))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Cumulative Return'], name="Cumulative Return"))
    
    # Create a secondary y-axis for volume with a bar trace
    fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name="Volume", yaxis="y2", marker=dict(color='purple', opacity=0.3)))
    
    fig.update_layout(
        yaxis_title="Value",
        xaxis_title="Date",
        title=ticker_selected,
        # Create secondary y-axis settings
        yaxis2=dict(
            title="Volume",
            titlefont=dict(
                color="red"
            ),
            tickfont=dict(
                color="red"
            ),
            overlaying="y",
            side="right",
            showgrid=False
        )
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

