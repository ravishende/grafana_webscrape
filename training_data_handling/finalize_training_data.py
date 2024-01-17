import pandas as pd
import shutil

'''
file to get rid of all unnecessary columns for training a model
and dressing up anything else to help
'''

# settings
read_file = 'csv_files/all_metrics_ratios_added.csv'
write_file = 'csv_files/all_metrics_training_data.csv'

# display settings
pd.set_option("display.max_columns", None)
terminal_width = shutil.get_terminal_size().columns
pd.set_option('display.width', terminal_width)

# columns to drop
useless_columns = [
    'path',
    'start',
    'stop', 
    'timestep',  # no variations in values - all 600
    'ensemble_uuid', 
    # 'run_uuid', 
    'cpu_usage_t1',  # with the ratio columns added, these no longer become useful
    'mem_usage_t1',
    'cpu_usage_t2',
    'mem_usage_t2'
]

# read csv and drop unnecessary columns
whole_df = pd.read_csv(read_file, index_col=0)
training_data = whole_df.drop(columns=useless_columns)

# write updated df to csv file and print it
training_data.to_csv(write_file)
print("\n"*3)
print(training_data, "\n"*3)