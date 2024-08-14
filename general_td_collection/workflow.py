# autopep8: off
import pandas as pd
import shutil
from setup import prompt_new_run
from preprocessing import preprocess_df
from querying import Query_handler
from finalizing import Finalizer
# autopep8: on

# display settings
pd.set_option("display.max_columns", None)
terminal_width = shutil.get_terminal_size().columns
pd.set_option('display.width', terminal_width)


# given a dataframe with 'start' and 'stop', and potentially other columns,
# query it over those times with given/selected queries
read_file = "csvs/read.csv"

# get the df & make sure there's no unnamed column from if csv was saved with/without an index col
df = pd.read_csv(read_file)
unnamed_cols = df.columns.str.match('Unnamed')
df = df.loc[:, ~unnamed_cols]

if not 'start' in df.columns or not 'end' in df.columns:
    raise ValueError(
        "dataframe must have a 'start' column and an 'end' columnn")

# TURN THIS TO FALSE IF CONTINUING TO QUERY, OTHERWISE TURN TO TRUE
NEW_RUN = True
prompt_new_run(NEW_RUN)


pod_prefix = 'fc-worker-1-'
pod_regex_str = f'^{pod_prefix}.*'
query_handler = Query_handler(pod_regex=pod_regex_str)
# query_handler = Query_handler(namespace="rook")
finalizer = Finalizer()

df = df.iloc[len(df)-14:]
print("\n\n\nStarting df:\n", df, "\n\n\n\n")
df = preprocess_df(df)
df = query_handler.query_df(df,
                            rgw_queries=False,
                            gpu_queries=True,
                            gpu_compute_resource_queries=True,
                            cpu_compute_resource_queries=True)
df = finalizer.sum_df(
    df, graph_metrics=['min', 'max', 'mean', 'median', 'increase'])
print(f"Finalized dataframe:\n{df}")
