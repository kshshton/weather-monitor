from collections import defaultdict
from datetime import datetime
from urllib.parse import parse_qs

import plotly.graph_objs as go
from dash import Dash, Input, Output, dcc, html
from ref.metrics import METRICS
from sqlalchemy import create_engine, text

app = Dash(__name__)
server = app.server
engine = create_engine("sqlite:///data/metadata.db")

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="plot-container")
])
datetime.now().strftime("%Y-%m-%d")

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),

    html.Div(
        children=[
            html.Span(style={"marginRight": "15px", "fontWeight": "bold"}),
            *[
                html.A(
                    metric_name.replace("_", " "),
                    href=f"/query?metric={metric_name}&from_date={datetime.now().strftime("%Y-%m-%d")}",
                    style={
                        "marginRight": "10px",
                        "padding": "8px 12px",
                        "textDecoration": "none",
                        "color": "white",
                        "backgroundColor": "#007BFF",
                        "borderRadius": "5px"
                    }
                )
                for metric_name in METRICS.keys()
            ]
        ],
        style={
            "padding": "15px 20px",
            "backgroundColor": "#e9ecef",
            "borderBottom": "1px solid #ddd"
        }
    ),

    html.Div(id="plot-container", style={
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "center",
        "height": "calc(100vh - 160px)",
        "padding": "30px",
        "maxWidth": "1000px",
        "margin": "0 auto",
    }),
], style={"fontFamily": "'Inter', sans-serif", "backgroundColor": "#fff", "color": "#222"})


@app.callback(
    Output("plot-container", "children"),
    Input("url", "pathname"),
    Input("url", "search")
)
def render_plot(pathname, query_string):
    if pathname != "/query":
        return html.H3("Navigate to /query with the required parameters.")

    if not query_string:
        return html.H3("No query provided.")

    params = parse_qs(query_string.lstrip("?"))
    metric = params.get("metric", [None])[0]
    from_date_str = params.get("from_date", [None])[0]

    if not metric or not from_date_str:
        return html.H3("Missing 'metric' or 'from_date' parameters.")

    if metric not in METRICS.keys():
        return html.H3("Metric not found.")

    try:
        parsed_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
    except ValueError:
        return html.H3("Invalid date format. Use YYYY-MM-DD.")

    metric_code = METRICS[metric]

    query = text("""
        SELECT timestamp, value, unit, sensor
        FROM metadata
        WHERE metric = :metric
            AND timestamp >= :from_date
        ORDER BY timestamp
    """)

    with engine.connect() as conn:
        rows = conn.execute(
            query, {"metric": metric_code, "from_date": parsed_date}).fetchall()

    if not rows:
        return html.H3("No data found for this query.")

    sensor_data = defaultdict(lambda: {"x": [], "y": []})

    for row in rows:
        timestamp, value, unit, sensor = row
        sensor_data[sensor]["x"].append(timestamp)
        sensor_data[sensor]["y"].append(value)

    units = set([row[2] for row in rows])
    if len(units) == 1:
        unit = units.pop()
    else:
        unit = None
        return html.Div(f"Warning: Multiple units found: {', '.join(units)}", style={"color": "orange"})

    fig = go.Figure()
    for sensor, data in sensor_data.items():
        fig.add_trace(go.Scatter(
            x=data["x"], y=data["y"], mode="lines+markers", name=f"Sensor {sensor}"))

    fig.update_layout(
        title=f"{metric.capitalize()} Since {parsed_date}",
        xaxis_title="Timestamp",
        yaxis_title=f"Value ({unit})" if unit else "Value",
        legend_title="Sensor",
    )

    return dcc.Graph(figure=fig)


if __name__ == "__main__":
    app.run(debug=True)
