import sqlite3
from datetime import datetime

import pandas as pd
from flask import Flask, abort, jsonify, request
from ref.metrics import METRICS

app = Flask(__name__)
conn = sqlite3.connect("data/metadata.db", check_same_thread=False)


@app.route("/data", methods=["GET"])
def get_metric():
    metric_name = request.args["metric_name"]
    from_date = request.args["from_date"]

    try:
        parsed_date = datetime.strptime(from_date, "%Y_%m_%d").date()
    except ValueError:
        abort(400, description="Invalid date format. Use YYYY_MM_DD.")

    if metric_name not in METRICS.keys():
        abort(404, description="Metric not found.")

    metric_code = METRICS[metric_name]
    query = "SELECT sensor, unit, value FROM metadata WHERE metric = ?"
    metric_data = pd.read_sql_query(query, con=conn, params=(metric_code,))

    response = {
        "metric_name": metric_name,
        "metric_code": metric_code,
        # "from_date": parsed_date.isoformat(), TODO: add timestamp
        "data": metric_data.to_dict(orient="records")
    }

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)
