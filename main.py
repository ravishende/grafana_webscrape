#!/usr/bin/python3
# -*- coding: utf-8 -*-
from header import Header
from tables import Tables
from graphs import Graphs
from utils import print_heading, print_title, print_sub_title
from termcolor import colored
import pandas as pd

# set pandas display dataframe options to display all columns
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)
# pd.set_option('display.max_rows', None)

# create variables for classes
header_class = Header()
tables_class = Tables()
graphs_class = Graphs()


# returns three dicts: one containing all header data,
# one with all tables, and one with all graph data
def get_all_data(only_include_worker_pods=False):
    print("    Retrieving Header Data")
    header_dict = header_class.get_header_dict(
        only_include_worker_pods=only_include_worker_pods
    )

    print("    Retrieving Tables Data")
    tables_dict = tables_class.get_tables_dict(
        only_include_worker_pods=only_include_worker_pods
    )

    print("    Retrieving Graphs Data")
    graphs_dict = graphs_class.get_graphs_dict(
        only_include_worker_pods=only_include_worker_pods,
        display_time_as_timestamp=True,
        show_runtimes=False
    )

    return_dict = {
        'header': header_dict,
        'tables': tables_dict,
        'graphs': graphs_dict
    }

    return return_dict


# Helper Function: for a given dictionary in the form {titles:dataframes}
# print the title and dataframe of each item in the dict
def print_dict(dictionary):
    for title, dataframe in dictionary.items():
        print_title(title)
        if len(dataframe.index) > 0:
            print(dataframe)
        else:
            print(colored("No Data", "red"))
        print("\n\n")


# prints data for headers, tables, and graphs.
def print_all_data(data_dict=None):
    if data_dict is None:
        data_dict = get_all_data()

    print_heading('Header')
    print_dict(data_dict['header'])

    print_heading('Tables')
    print_dict(data_dict['tables'])

    print_heading('Graphs')
    print_dict(data_dict['graphs'])

def check_graphs_losses(graphs_dict, print_info=True, requery=None):
    # get losses
    graphs_losses_dict = graphs_class.check_for_losses(graphs_dict, print_info=print_info)

    # prompt the user so requery can be set to True or False
    if requery is None:
        #Prompt if the user would like to requery the graphs
        user_response = input("Would you like to requery the graphs for zoomed in views of the pod drops and recoveries?\n(y/n)\n")
        if user_response in ['y', 'yes', 'Y', 'Yes']:
            requery = True
        else:
            requery = False
    
    if requery == False:
        return {"losses":graphs_losses_dict, "requeried":None}
    
    # requery is True
    requeried_graphs_dict = graphs_class.requery_losses(graphs_dict, graphs_losses_dict)
    print_heading('Requeried Graphs')
    #loop through requeried_graphs_dict and print all requeried graphs
    for graph_title, loss_dict in requeried_graphs_dict.items():
        # print graph title
        print_title(graph_title)

        for category, graphs_list in loss_dict.items():
            # Print Dropped or Recovered
            print_sub_title(category)
            # Print graphs
            for graph in graphs_list:
                print(graph, "\n\n")
        
    return {"losses":graphs_losses_dict, "requeried":requeried_graphs_dict}
    
    

# run all code
result_dict = get_all_data(only_include_worker_pods=False)
print_all_data(result_dict)
graphs_dict = result_dict['graphs']
losses_and_requeried_graphs = check_graphs_losses(graphs_dict, print_info=True, requery=False)



