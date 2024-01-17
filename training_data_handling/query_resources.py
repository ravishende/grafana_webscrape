import pandas as pd
from datetime import datetime, timedelta
from termcolor import colored
import random
import shutil
# get set up to be able to import helper functions from parent directory (grafana_data_retrieval)
import sys
import os
sys.path.append("../grafana_data_retrieval")
current = os.path.dirname(os.path.realpath("query_resources.py"))
parent = os.path.dirname(current)
sys.path.append(parent)
from helpers.querying import query_data
from helpers.printing import print_heading, print_title
from helpers.time_functions import delta_to_time_str, datetime_ify, calculate_offset


# Settings - You can edit these, especially NUM_ROWS, which is how many rows to generate per run
# csv_file = 'csv_files/queried_all_metrics.csv'
csv_file = 'csv_files/nonzero_queried_all_metrics.csv'
NUM_ROWS = 100
NAMESPACE = 'wifire-quicfire'

# display settings
pd.set_option("display.max_columns", None)
terminal_width = shutil.get_terminal_size().columns
pd.set_option('display.width', terminal_width)


# For printing rows. Do not edit.
CURRENT_ROW = 1

'''
-----------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------
This file reads in a csv which contains all the training data from Devin's inputs as well as columns
for cpu_total, cpu_t1, cpu_t2, mem_total, mem_t1, and mem_t2 usage for the run. Running this appends NUM_ROWS values 
for those 6 columns to what has already been queried for, filling out more and 
more of the datapoints. This can be edited in the main program portion of the file to query for any cpu and memory
usage up until a certain duration. The only requirement is adding that new duration column.

All that needs to be done is select NUM_ROWS to be the value you would like and then run the file.
-----------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------
'''


'''
---------------------------------------
            Helper Functions
---------------------------------------
'''

# CPU Requests
# Memory Requests
# CPU/Memory Request percentages (t1, t2, total, so 6 total columns)
# • request% = 100*usage/request
# Transmitted Packets
# Received Packets
# Receive Bandwidth
# Transmit Bandwidth

# static
    # 'CPU Requests': 'cluster:namespace:pod_cpu:active:kube_pod_container_resource_requests',
    # 'Memory Requests': 'cluster:namespace:pod_memory:active:kube_pod_container_resource_requests',
# increase
    # 'Current Receive Bandwidth': 'container_network_receive_bytes_total',
    # 'Current Transmit Bandwidth': 'container_network_transmit_bytes_total',
    # 'Rate of Received Packets': 'container_network_receive_packets_total',
    # 'Rate of Transmitted Packets': 'container_network_transmit_packets_total',
# calculated
    # cpu/mem request percentages (t1, t2, total)


# cpu/mem Requests
# cpu/mem Request percentages (t1, t2, total)
# Transmitted packets
# Received packets
# receive/transmit bandwidth


def get_static_query_suffix(metric, start, duration_seconds):
     # static metrics only need to be requested for one datapoint at the beginning of the run (in this case 5 seconds in)
    offset = calculate_offset(start, 5)

    suffixes = {
        # set resource to cpu and multiply by duration seconds to get metric from measuring cpu cores to cpu seconds
        # ex: cpu_usage is measured in cpu seconds, so to make the cpu requests % (cpu_usage/cpu_requests) accurate, they both have to be in the same units.
        'cpu':'{resource="cpu", namespace="' + NAMESPACE + '"} offset ' + str(offset) + ') * ' + str(duration_seconds),
        # set resource to memory. It is already in the preferred unit of bytes
        'mem':'{resource="memory", namespace="' + NAMESPACE + '"} offset ' + str(offset) + ')'
    }

    resource = metric[:3]  # either cpu or mem
    suffix = suffixes[resource]  # get the appropriate suffix depending on the resource
    return suffix


# given a metric (one of the keys in query_bodies), start (datetime), and duration (float)
# return a query for the metric over the given duration of the run
def get_resource_query(metric, start, duration_seconds):
    # all resources and the heart of their queries
    query_bodies = {
        "cpu_usage":"increase(container_cpu_usage_seconds_total",  # increase metric
        "mem_usage":"max_over_time(container_memory_working_set_bytes",  # max over time metric
        "cpu_request":"cluster:namespace:pod_cpu:active:kube_pod_container_resource_requests",  # static metric
        "mem_request":"cluster:namespace:pod_memory:active:kube_pod_container_resource_requests",  # static metric
        "transmitted_packets":"increase(container_network_transmit_packets_total",  # increase metric
        "received_packets":"increase(container_network_receive_packets_total",  # increase metric
        "transmitted_bandwidth":"increase(container_network_transmit_bytes_total",  # increase metric
        "received_bandwidth":"increase(container_network_receive_bytes_total"  # increase metric
    }
    
    # check if user input metric is in known resources
    metrics = query_bodies.keys()
    if metric not in metrics:
        raise ValueError(f'query metric "{metric}" must be within one of the following metrics:\n{metric}')

    # get all the pieces necessary to assemble the query
    offset = calculate_offset(start, duration_seconds)    
    duration = delta_to_time_str(timedelta(seconds=duration_seconds))
    suffix = '{namespace="' + NAMESPACE + '"}[' + str(duration) + '] offset ' + str(offset) + '))'
    prefix = 'sum by (node, pod) ('

    # static metrics have a different suffix. Update suffix if metric is a static metric
    static_metrics = ["cpu_request", "mem_request"]
    if metric in static_metrics:
        suffix = get_static_query_suffix(metric, start, duration_seconds)

    # assemble the final query
    query = prefix + query_bodies[metric] + suffix
    return query

# Given a metric,, start of a run (time string), and duration_seconds (float or int)
# (Also takes in row_index and n_rows for printing purposes)
# return the queried data of that metric over the duration of the run
def query_resource(metric, start, duration_seconds, row_index, n_rows):
    # query for data
    start = datetime_ify(start)
    query = get_resource_query(metric, start, duration_seconds)
    resource_data = query_data(query)

    # print row information
    global CURRENT_ROW
    progress_message = f"Row complete: {CURRENT_ROW} / {n_rows}"
    print(colored(progress_message, "green"))
    print("Row index:", row_index)
    CURRENT_ROW += 1

    # return queried data
    return resource_data


'''
---------------------------------------
            User Functions
---------------------------------------
'''
# generate random values between run_start and some end time, put into duration1
def insert_rand_refresh_col(df, refresh_title):
    duration_seconds = df['runtime']
    # generate random values between 45sec and half of the duration
    # df[refresh_title] = duration_seconds.apply(lambda time: random.randint(45, time // 2) if time // 2 >= 45 else time)

    # generate random values between 45sec and 5min
    df[refresh_title] = duration_seconds.apply(lambda time: random.randint(45, 300) if time >= 300 else time)

    return df


# Given a dataframe, metric, name of the column to insert,
# name of the duration column to use for calculating, and the number of rows to query for:
# calculate performance data columns for those rows starting from the first None value. 
# The other rows' values for those columns will be unchanged.
# Returns the updated dataframe.
def insert_column(df, metric, insert_col, duration_col, n_rows):
    # handle if column doesn't exist
    if insert_col not in df.columns:
        df[insert_col] = None

    # Calculate start and end rows based on n_rows
    start_row = df[insert_col].isna().idxmax()
    end_row = start_row + n_rows - 1
    
    # make sure you don't try to query past the end of the dataframe
    last_index = len(df) - 1
    if(end_row > last_index):
        end_row = last_index
        n_rows = end_row - start_row + 1
        print(colored("\n\nEnd row is greater than last index. Only generating to last index.", "yellow"))

    # if no na values, there is nothing to generate.
    if start_row == 0 and df[insert_col][0]:
        print(colored("\n\nNo NA rows", "yellow"))
        return df
    
    # since we're starting a new column, reset the current printing row to 1
    # this CURRENT_ROW is used for printing in the query_resource function
    global CURRENT_ROW
    CURRENT_ROW = 1

    # Query metric and insert column into dataframe
    print_title(f"Inserting {insert_col}")
    df[insert_col] = df.apply(
        lambda row: query_resource(metric, row['start'], row[duration_col], row.name, n_rows) \
        if start_row <= row.name <= end_row else row[insert_col], axis=1)  
        # Note: row.name is just the index of the row
    
    return df


# given a dataframe and several columns to insert (all that have the same duration), 
# query the metrics and return the updated dataframe with the newly inserted columns
# Parameters:
#   - df:                   original pandas dataframe
#   - query_metrics_list:   list of all metrics to query for, in same order as col_names_list
#   - col_names_list:       list of all column names for each metric queried
#   - duration_col:         name of the duration column to get the durations from
#   - n_rows:               number of rows to query for
def insert_columns(df, query_metrics_list, col_names_list, duration_col, n_rows):
    # handle invalid user inputs
    if len(query_metrics_list) != len(col_names_list):
        raise ValueError("query_metrics_list and col_names_list must be the same length with a 1 to 1 matching of metric to name")
    if not isinstance(duration_col, str):
        raise ValueError("duration_col must be the name of the column for the durations to query over for each run")

    print_heading(f"Inserting Columns for Duration Column: {duration_col}")
    # loop over query_metrics_list and col_names_list, adding a 
    for metric, name in zip(query_metrics_list, col_names_list):
        df = insert_column(df, metric, name, duration_col, n_rows)

    return df

'''
---------------------------------------
            Main Program
---------------------------------------
'''

# get the csv file as a pandas dataframe
training_data = pd.read_csv(csv_file, index_col=0)

'''
# list of all metrics you can query (in insert_columns)
all_metrics = [
    "cpu_usage","mem_usage",
    "cpu_request","mem_request",
    "transmitted_packets","received_packets",
    "transmitted_bandwidth","received_bandwidth"
    ]
'''

# list of metrics to pass into insert_columns()
metrics_total = [
    "cpu_request",
    "mem_request",
    "transmitted_packets",
    "received_packets",
    "transmitted_bandwidth",
    "received_bandwidth"]
# list of metrics to pass into insert_columns that doesn't contain static columns (request metrics) which will be the same as the total columns
metrics_non_total = metrics_total[2:]
# names of columns to pass into insert_columns()
col_names_total = [name + "_total" for name in metrics_total]
col_names_t1 = [name + "_t1" for name in metrics_non_total]
col_names_t2 = [name + "_t2" for name in metrics_non_total]

# name of duration column to pass into insert_columns()
duration_col_total = "runtime"
duration_col_t1 = "duration_t1"
duration_col_t2 = "duration_t2"

# initialize columns if they aren't already
all_column_names = col_names_total + col_names_t1 + col_names_t2
for col_name in all_column_names:
    if col_name not in training_data.columns:
        training_data[col_name] = None

# query everything and insert the new columns into the dataframe, saving after each insertion
training_data = insert_columns(training_data, metrics_total, col_names_total, duration_col_total, NUM_ROWS)
training_data.to_csv(csv_file)  # in case program gets stopped before finishing, save partial progress
training_data = insert_columns(training_data, metrics_non_total, col_names_t1, duration_col_t1, NUM_ROWS)
training_data.to_csv(csv_file)  # in case program gets stopped before finishing, save partial progress
training_data = insert_columns(training_data, metrics_non_total, col_names_t2, duration_col_t2, NUM_ROWS)

# print and write the updated dataframe to a csv file
print("\n"*5, training_data)
training_data.to_csv(csv_file)




'''
========================================================
For using insert_column() to insert one metric at a time
========================================================
'''
# query total performance data
# cpu columns
# training_data = insert_column(training_data, "cpu", "cpu_total", 'runtime', n_rows)
# training_data = insert_column(training_data, "cpu", "cpu_t1", 'duration_t1', n_rows)
# training_data = insert_column(training_data, "cpu", "cpu_t2", 'duration_t2', n_rows)
# memory columns
# training_data = insert_column(training_data, "mem", "mem_total", 'runtime', n_rows)
# training_data = insert_column(training_data, "mem", "mem_t1", 'duration_t1', n_rows)
# training_data = insert_column(training_data, "mem", "mem_t2", 'duration_t2', n_rows)

# print and write updated df to a csv file
# print("\n"*5, training_data)
# training_data.to_csv(csv_file)


'''
======================================================
For inserting another duration and more metric columns

Note: make sure to edit insert_rand_refresh_col() to 
be within the time range you want it to be.
======================================================
'''
'''
# add new columns and insert duration col
# training_data['duration_t3'] = None
# training_data['cpu_t3'] = None
# training_data['mem_t3'] = None
# training_data = insert_rand_refresh_col(training_data, "duration_t3")

training_data = insert_column(training_data, "cpu", "cpu_t3", 'duration_t3', n_rows)
training_data = insert_column(training_data, "mem", "mem_t3", 'duration_t3', n_rows)
'''

