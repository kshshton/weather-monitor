import re
import sqlite3

import pandas as pd

metadata = []
_pattern = r"\((?P<sensor>[^)]+).*?(?P<metric>\w+(\s\w+)?).*?(?P<value>\d+(\.\d+)?)\s+(?P<unit>[^\']+)"

conn = sqlite3.connect("metadata.db")
cursor = conn.cursor()

with open("sample.txt", "r") as file:
    log = file.read()
    lines = [line for line in log.split("\n") if "(" in line]

    for line in lines:
        if match := re.search(_pattern, line):
            metadata.append(match.groupdict())

df = pd.DataFrame(metadata)
df.drop_duplicates(subset=["sensor", "metric", "value", "unit"])
df.to_sql("metadata", conn, if_exists="append", index=False)

conn.close()
