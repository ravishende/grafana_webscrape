import pandas as pd
import warnings
import ast
from query_resources import query_and_insert_columns

'''
========================
        Phase 1
========================
'''


'''
------
step 1 - get successful bp3d runs
------
'''
# given a dataframe of runs with ens_status and run_status columns,
# return a new dataframe with only the successful runs 
def get_successful_runs(runs_df, reset_index=True):
    # get a df with only the successful runs
    successful_runs = df[(df["ens_status"]=="Done") & (df["run_status"]=="Done")]
    # if requested, reset the indices to 0 through end of new df after selection
    if reset_index:
        successful_runs = successful_runs.reset_index(drop=True)
    return successful_runs


'''
------
step 3 - add in ensemble_uuid
------
'''

# given a dataframe of successful runs (that have run_uuid, ensemble_uuid) and a dataframe of runs collected (with information on each run)
# return a dataframe of the two merged to include all information on the run and id columns
def add_id_cols(successful_runs_df, collected_runs_df):
    successful_runs_subset = successful_runs_df[['ensemble_uuid', 'run_uuid']]
    merged_df = pd.merge(collected_runs_df, successful_runs_subset, left_index=True, right_index=True)
    return merged_df


'''
------
step 4 - calculate area and runtime
------
'''

def _calculate_area(corners_list):
    # where p1 in the bottom left = (x1,y1) and p2 in the bottom left = (x2,y2)
    # corners_list is of the form [x1, y1,, x2, y2]
    corners_list = ast.literal_eval(corners_list) # converting string to list
    x1, y1, x2, y2 = float(corners_list[0]), float(corners_list[1]), float(corners_list[2]), float(corners_list[3])
    x_length = abs(x2-x1)
    y_length = abs(y2-y1)
    area = x_length * y_length
    return area

def _calculate_runtime(start, stop):
    # there are two slightly different ways that time strings are represented. Try the other if the first doesn't work.
    # get start and stop down to the second, no fractional seconds.
    start = start[0:start.find(".")]
    stop = stop[0:stop.find(".")]
    
    # get start and stop as datetimes
    parsing_successful = False
    format_strings = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]
    for format_str in format_strings:
        try:
            start_dt = datetime.strptime(start, format_string)
            stop_dt = datetime.strptime(stop, format_string)
            # if parsing is successful, break the loop
            parsing_successful = True
            break
        except ValueError:
            continue  # if parsing failed, try next format string
    if not parsing_successful:
        raise ValueError("Time format not recognized")

    # find the difference between stop and start for the runtime
    runtime_delta = stop_dt - start_dt
    return runtime_delta.total_seconds()


# given a dataframe with 'extent', 'start', and 'stop' columns, 
# return a df with added 'area' and 'runtime' columns
def add_area_and_runtime(df):
    df['area'] = df['extent'].apply(_calculate_area)
    df['runtime'] = df.apply(lambda row: _calculate_runtime(row['start'], row['stop']), axis=1)
    return df


'''
------
step 5 - drop unnecessary columns
------
'''

def drop_columns(df, columns_to_drop):
    df = df.drop(columns=columns_to_drop)
    return df


'''
------
step 6 - add duration_t1, duration_t2 columns
------
'''

# generate random values between run_start and some end time, put into duration1
def _insert_rand_refresh_col(df, refresh_title, method=0):
    duration_seconds = df['runtime']
    if method == 0:
        # generate random values between 45sec and 5min
        df[refresh_title] = duration_seconds.apply(lambda time: random.randint(45, 300) if time >= 300 else time)
    elif method == 1:
        # generate random values between 45sec and half of the duration
        df[refresh_title] = duration_seconds.apply(lambda time: random.randint(45, time // 2) if time // 2 >= 45 else time)
    elif method == 2:
        # generate random values between 45sec and the full duration
        df[refresh_title] = duration_seconds.apply(lambda time: random.randint(45, time))
    else:
        raise ValueError("method must be: 0, 1, or 2")
    return df


# given a dataframe and number of duration columns to insert, (also single_method, which is either False or some int between 0 and 2)
# return an updated dataframe with an added n duration columns of various insert methods
def insert_n_duration_columns(df, n, single_method=False):
    num_insert_methods = 3
    # warn the user if they are expecting more insert methods than are available in _insert_rand_refresh_col
    if n > num_insert_methods and not single_method:
        warnings.warn("There are more columns requested than insert methods defined. Repeating the last method after other methods are used.")
    for i in range(0, n):
        # get the insert method
        if single_method:
            insert_method = single_method
        else:
            insert_method = i
            if insert_method >= num_insert_methods:
                insert_method = num_insert_methods - 1
        # assemble the duration_title
        duration_title = "duration_t" + insert_method
        df = _insert_rand_refresh_col(df, duration_title, method=insert_method)



'''
========================
        Phase 2
========================
'''

# get the static and non_static metrics lists
def _get_metrics():
    # define the metrics to be queried
    # list of all metrics you can query (with query_and_insert_columns())
    all_metrics = [
        "cpu_usage",
        "mem_usage",
        "cpu_request",
        "mem_request",
        "transmitted_packets",
        "received_packets",
        "transmitted_bandwidth",
        "received_bandwidth"
        ]
    # metrics that don't change over a run
    static_metrics = ["cpu_request", "mem_request"]
    # metrics that do change over a run
    non_static_metrics = [metric for metric in all_metrics if metric not in STATIC_METRICS]

    return static_metrics, non_static_metrics


def _get_metric_column_names():
    # get column names
    col_names_static = static_metrics
    col_names_total = [name + "_total" for name in non_static_metrics]

    # get col_names_t1, col_names_t2, etc. in a list called col_names_by_time
    col_names_by_time = []
    for i in range(1, len(duration_col_namesn)+1):
        col_names_t_i = [name + "_t" + i for name in non_static_metrics]
        col_names_by_time.append(col_names_t_i)


# given: 
    # df - a dataframe 
    # num_inserted_duration_cols - the number previously passed in as n in insert_n_duration_columns
    # batch_size - number of rows to query at a time until the df is filled out
    # temporary_save_file - name of a csv file to save df to after each big insert in case the program is stopped
# query all important metrics, saving to the temporary_save_file after inserting columns of the same duration column.
    # Note: this function assumes the total duration column is "runtime" and duration columns 
    # are in the form "duration_t{N}" where {N} is an int from 1 to num_inserted_duration_cols inclusive
# return the updated dataframe with all columns queried
def query_metrics(df, num_inserted_duration_cols, batch_size, temporary_save_file):
    # get metrics lists
    static_metrics, non_static_metrics = _get_metrics()
    
    # get duration column names
    duration_col_names = ["duration_t" + num for num in range(1,num_inserted_duration_cols+1)]
    duration_col_total = "runtime"

    # get metric column names
    col_names_static, col_names_total, col_names_by_time = _get_metric_column_names()

    # collect all metric column names and initialize them in the dataframe if they aren't already
    all_col_names = col_names_static + col_names_total + [col_names_t_i for col_names_t_i in col_names_by_time]
    for column in all_column_names:
        if column not in df.columns:
            df[column] = None

    # query and insert static and total columns
    df = query_and_insert_columns(df, static_metrics, col_names_static, duration_col_total, batch_size)
    df.to_csv(temporary_save_file)
    df = query_and_insert_columns(df, non_static_metrics, col_names_total, duration_col_total, batch_size)
    df.to_csv(temporary_save_file)
    # query and insert duration_t_i columns
    for i, col_names_t_i in enumerate(col_names_by_time):
        df = query_and_insert_columns(df, non_static_metrics, col_names_t_i, duration_cols[i], batch_size)
        df.to_csv(temporary_save_file)

    return df
