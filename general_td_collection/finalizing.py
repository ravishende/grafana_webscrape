from multiprocessing.sharedctypes import Value
import pandas as pd


class Finalizer():
    def __init__(self, graph_metrics_dict=None, graph_columns=None):
        if graph_columns is None:
            graph_columns = self.get_graph_columns()

        self._check_graph_metrics_dict(graph_metrics_dict)
        self._check_graph_columns(graph_columns)
        self._graph_metric_cols_dict = {}
        self.graph_metrics_dict = graph_metrics_dict
        self.gaph_columns = graph_columns
        self.all_graph_metrics = ['min', 'max', 'avg',
                                  'std', 'var', 'med', 'q1', 'q3', 'iqr']

    def get_graph_columns(self):
        # TODO: save graph_columns in Query_handler, then read it in here
        graph_columns = []
        return graph_columns

    def _check_graph_columns(self, graph_columns):
        if isinstance(graph_columns, str):
            # if there's just one passed in column, put it in a list still
            graph_columns = [graph_columns]
        if not isinstance(graph_columns, list):
            raise ValueError(
                f"graph_columns must be a str or list but was {type(graph_columns)}.")

    def _check_graph_metrics_dict(self, graph_metrics_dict):
        if graph_metrics_dict is not None:
            if not isinstance(graph_metrics_dict, dict):
                raise ValueError(
                    "graph_query_metrics must be a dictionary of str:bool, where the possible keys are: ")
            for key in graph_metrics_dict.keys():
                if key not in self.all_graph_metrics:
                    raise ValueError(
                        f"key {key} not in acceptable metrics: {self.all_graph_metrics}.")

    def _title_to_col_name(self, title):
        title = title.lower()
        title = title.replace(" ", "_")
        return title

    def _get_col_name_for_graph(self, graph_title, metric):
        if metric not in self.graph_metrics_dict.keys():
            raise ValueError(
                f"metric {metric} not in acceptable metrics: {self.graph_metrics_dict.keys()}")
        cleaned_title = self._title_to_col_name(graph_title)
        col_name = f"{metric}_{cleaned_title}"
        return col_name

    # takes in a pandas series and metric
    # returns the metric taken of the series
    def _calculate_metric_row(self, graph_col_series, metric):
        ['min', 'max', 'avg', 'std', 'var', 'med', 'q1', 'q3', 'iqr']
        match metric:
            case "min":
                return graph_col_series.min()
            case "max":
                return graph_col_series.max()
            case "avg":
                return graph_col_series.avg()
            case "std":
                return graph_col_series.std()
            case "var":
                return graph_col_series.var()
            case "med":
                return graph_col_series.quantile(q=0.5)
            case "q1":
                return graph_col_series.quantile(q=0.25)
            case "q3":
                return graph_col_series.quantile(q=0.75)
            case "iqr":
                return graph_col_series.quantile(q=0.75) - graph_col_series.quantile(q=0.25)
            case _:
                raise ValueError(
                    f"metric {metric} not in known metrics: {self.all_graph_metrics}")

    def _calculate_metric_col(self, df):
        # TODO: apply self._calculate_metric_row - look at how it is done in llm_data_collection
        return

    def _insert_graph_metric_columns(self, df, graph_metrics_dict=None, graph_columns=None):
        # handle user input
        if not isinstance(df, pd.DataFrame):
            raise ValueError(
                f"df must be a pandas dataframe but was {type(df)}")
        if graph_metrics_dict is None:
            graph_metrics_dict = self.graph_metrics_dict
        else:
            self._check_graph_metrics_dict(graph_metrics_dict)
        if graph_columns is None:
            graph_columns = self.graph_columns
        else:
            self._check_graph_columns(graph_columns)

        graph_metric_cols_dict = {title: [] for title in graph_columns}
        for graph_title in graph_columns:
            for metric, status in graph_metrics_dict.items():
                if status == False:
                    continue
                col_name = self._get_col_name_for_graph(graph_title, metric)
                graph_metric_cols_dict[graph_title].append(col_name)
                df[col_name] = self._calculate_metric_col(
                    df[graph_title], metric)

        self._graph_metric_cols_dict = graph_metric_cols_dict
        return df

    def _sum_result_list(self, result_list):
        total = 0
        for metric_value_dict in result_list:
            for time_value_pair in metric_value_dict['values']:
                total += time_value_pair[1]
        return total

    def sum_df(self, df, graph_metrics_dict=None, graph_columns=None):
        for column in df.columns:
            if column not in self.graph_columns:
                df[column] = df[column].apply(self._sum_result_list)

        # TODO: handle graph columns
        df = self._insert_graph_metric_columns(
            graph_metrics_dict, graph_columns)
        df = self.fil_graph_metric_columns(graph_columns)
        return df
