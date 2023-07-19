from utils import *

column_names=["CPU Usage","CPU Requests",'CPU Requests %', 'CPU Limits']

class MemQuota():
	def __init__(self):
		self.result = {
			"CPU Usage":None, 
			"CPU Requests":None, 
			'CPU Requests %':None, 
			'CPU Limits':None
		}

	def get_values(self, pod):
		self.result["CPU Usage"] = self._get_cpu_usage(pod)
		self.result["CPU Requests"] = self._get_cpu_requests(pod)
		self.result["CPU Requests %"] = self._get_cpu_requests_percent(pod)
		self.result["CPU Limits"] = self._get_cpu_limits(pod)
		return self.result

	def _get_cpu_usage(self,pod):
		cpu_usage = query_api_site('sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{cluster="", namespace="wifire-quicfire", pod="'+pod+'"})')
		cpu_usage = cpu_usage.json()['data']['result']
		
		# if error retrieving from api, ping again recursively
		if (len(cpu_usage) == 0):
			return self._get_cpu_usage(pod)

		return float(cpu_usage[0]['value'][1])

	def _get_cpu_requests(self,pod):
		pass

	def _get_cpu_requests_percent(self,pod):
		pass

	def _get_cpu_limits(self,pod):
		pass


