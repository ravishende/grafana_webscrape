import requests
import json

ts = '[1h]'

QUERIES = {
	'CPU Utilisation (from requests)':'sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{cluster="", namespace="wifire-quicfire"}) / sum(kube_pod_container_resource_requests{job="kube-state-metrics", cluster="", namespace="wifire-quicfire", resource="cpu"})',
	'CPU Utilisation (from limits)':'sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{cluster="", namespace="wifire-quicfire"}) / sum(kube_pod_container_resource_limits{job="kube-state-metrics", cluster="", namespace="wifire-quicfire", resource="cpu"})',
	'Memory Utilisation (from requests)':'sum(container_memory_working_set_bytes{job="kubelet", metrics_path="/metrics/cadvisor", cluster="", namespace="wifire-quicfire",container!="", image!=""}) / sum(kube_pod_container_resource_requests{job="kube-state-metrics", cluster="", namespace="wifire-quicfire", resource="memory"})',
	'Memory Utilisation (from limits)':'sum(container_memory_working_set_bytes{job="kubelet", metrics_path="/metrics/cadvisor", cluster="", namespace="wifire-quicfire",container!="", image!=""}) / sum(kube_pod_container_resource_limits{job="kube-state-metrics", cluster="", namespace="wifire-quicfire", resource="memory"})'
}

# this part didn't work
QUERIES_WITH_TIME = {
	'A':'sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{cluster="", namespace="wifire-quicfire"})' +' / sum(kube_pod_container_resource_requests{job="kube-state-metrics", cluster="", namespace="wifire-quicfire", resource="cpu"}' + ')',
	'B':'sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{cluster="", namespace="wifire-quicfire"})'  +' / sum(kube_pod_container_resource_limits{job="kube-state-metrics", cluster="", namespace="wifire-quicfire", resource="cpu"}'  + ')',
	'C':'sum(container_memory_working_set_bytes{job="kubelet", metrics_path="/metrics/cadvisor", cluster="", namespace="wifire-quicfire",container!="", image!=""})'  + ' / sum(kube_pod_container_resource_requests{job="kube-state-metrics", cluster="", namespace="wifire-quicfire", resource="memory"}'+ ')',
	'D':'sum(container_memory_working_set_bytes{job="kubelet", metrics_path="/metrics/cadvisor", cluster="", namespace="wifire-quicfire",container!="", image!=""})' + ' / sum(kube_pod_container_resource_limits{job="kube-state-metrics", cluster="", namespace="wifire-quicfire", resource="memory"}' + ')' # always no data here
}

def find_query_values():
	query_values = {}

	for query_title, query in QUERIES.items():
		try:
			query_values[query_title] = query_api_site(query).json()['data']['result'][0]['value']
			# query_values[query_title] = query_api_site(query).json()
		except KeyError:
			query_values[query_title] = "no data/failed response"
		except IndexError:
			query_values[query_title] = "no data/failed response"

	return query_values


def print_query_values():
	query_values = find_query_values()
	for query_title, value in query_values.items():
		print(f'{query_title}: \n\t\t{value}\n')


def query_api_site(query=QUERIES['CPU Utilisation (from requests)']):
	base_url = 'https://thanos.nrp-nautilus.io/api/v1/'
	endpoint = f'query?query={query}'
	full_url = base_url + endpoint
	cpu_data = requests.get(full_url)
	return cpu_data

def write_json(data):
	with open("e.json","w") as file:
		json.dump(data.json(),file)

def read_json():
	with open("webscrape.json","r") as file:
		data = json.load(file)
	return data

