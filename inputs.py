#!/usr/bin/python3
# -*- coding: utf-8 -*-
from datetime import datetime


# namespace
NAMESPACE = 'wifire-quicfire'  # main namespace to be using
# NAMESPACE = 'alto'  # used for testing when no data in wifire-quicfire

# duration for data types: tables, graphs
DEFAULT_DURATION = '10m'

# graphs
DEFAULT_GRAPH_STEP = '1m'
DEFAULT_GRAPH_TIME_OFFSET = '1h'
DEFAULT_FINAL_GRAPH_TIME = datetime.now() # must be a datetime object
# requerying
REQUERY_GRAPH_STEP_DIVISOR = 10  # a value of 10 means there will be 10x the number of datapoints for a given timeframe
