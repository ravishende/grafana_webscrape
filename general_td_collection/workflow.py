"""This file collects performance data of runs in a dataframe

Given a dataframe with 'start' and 'end' columns (and potentially others too),
Query it over those times with selected queries and metrics from grafana dashboards
You can specify a filter for the queries as well as which dashboards you would life for querying.
The filter can be a node, pod, namespace, or regex for any of those.
Additionally, for graph queries, you can specify which metrics you would like saved 
(e.g. max, increase, etc.).

Since querying over large datasets can take a long time, this workflow automatically saves progress
of what has been queried. This is where NEW_RUN comes in. If this is the first time entering a 
dataset to be queried, set NEW_RUN to True. If you are running this file to continue querying, set
NEW_RUN to False.

Usage:
1. Put a csv containing 'start' and 'end' columns in the 'csvs' folder. 
    - Specify the READ_FILE variable to contain the path to that csv.
2. Specify the filter when instantiating the QueryHandler class
    - Ex: query_handler = QueryHandler(pod_regex="...", namespace="wifire-quicfire")
    - If you later need to redefine filters in the same program, use the update_filter_str() method
3. Call the query_df method, specifying which query dashboards to include
    - Ex: queried_df = query_handler.query_df(df, rgw_queries=True, gpu_queries=True)
4. In the Finalizer's sum_df method, specify the graph_metrics to collect for graph queries
    - Ex: finalizer.sum_df(queried_df, graph_metrics=['max', 'mean', 'increase'])
5. Save the final dataframe of queried information
    - df.to_csv(WRITE_FILE)
"""
# autopep8: off
import shutil
import pandas as pd
from setup import prompt_new_run
from querying import QueryHandler
from finalizing import Finalizer
# autopep8: on

# display settings
pd.set_option("display.max_columns", None)
terminal_width = shutil.get_terminal_size().columns
pd.set_option('display.width', terminal_width)


# SETTINGS
READ_FILE = "csvs/read.csv"
WRITE_FILE = "csvs/write.csv"
# Set to False if continuing to query, otherwise, set to True
NEW_RUN = True

# ==========================
#       MAIN PROGRAM
# ==========================

# get the df & make sure there's no unnamed column from if csv was saved with/without an index col
df = pd.read_csv(READ_FILE)
unnamed_cols = df.columns.str.match('Unnamed')
df = df.loc[:, ~unnamed_cols]

prompt_new_run(NEW_RUN)

# way to filter - can be pod, node, namespace, or regex of any of the three
POD_SUBSTRING = 'fc-worker-1-'
pod_regex_str = f'.*{POD_SUBSTRING}.*'
# NODE_NAME = "node-1-1.sdsc.optiputer.net"

# initialize classes with desired filter and data settings
query_handler = QueryHandler(pod_regex=pod_regex_str)
# query_handler = QueryHandler(node=NODE_NAME)
# query_handler = QueryHandler(namespace="rook")  # has data for rgw queries
finalizer = Finalizer()

# for testing on just a few datapoints - if you want the whole dataset, set test_subset to False
test_subset = False
if test_subset:
    df = df.iloc[len(df)-5:]
    print("\n\n\nStarting df:\n", df, "\n\n\n\n")

# Main workflow
df = query_handler.query_df(
    df,  # pandas dataframe containing 'start' and 'end' columns
    rgw_queries=False,  # rgw queue, cache, and gets/puts metrics
    gpu_queries=False,  # total gpu usage and requested gpus
    gpu_compute_resource_queries=False,  # gpu utilization and physical metrics
    cpu_compute_resource_queries=True  # cpu, memory, and network metrics
)
df = finalizer.sum_df(
    df, graph_metrics=['min', 'max', 'mean', 'median', 'increase'])
    # graph_metrics describe the data for graph-based queries. Choose the metrics you want
    # all metrics are [["min", "max", "mean", "median", "std", "var", "sum", "increase", "q1", "q3", "iqr"]]

df.to_csv(WRITE_FILE)
print(f"Finalized dataframe:\n{df}")
