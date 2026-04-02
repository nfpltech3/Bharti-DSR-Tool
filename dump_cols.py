import pandas as pd
import json
df = pd.read_excel(r"c:\projects\DOCS\dsr_consolidation\Bharti DSR Report (7).xlsx")
with open("cols.json", "w") as f:
    json.dump(df.columns.tolist(), f, indent=4)
