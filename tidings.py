import requests
from datetime import date
import json

class Guardian(object):
	def __init__(self, api_key):
		self.api_key = api_key

	def _request(self, query, from_date, to_date, page=1):
		if not query or not query.strip():
			return None

		endpoint = 'http://content.guardianapis.com/search'
		payload = {
			'q': query, 
			'api-key': self.api_key, 
			'format': 'json',
			'page-size': 50,
			'page': page,
			'from-date': from_date,
			'to-date': to_date
		}
		api_response = requests.get(endpoint, params=payload)
		api_response.raise_for_status()
		return api_response.text

	def _process_result(self, json):
		webUrl = []
#		for val in json['response']['results']:
#			webUrl.append(val['webUrl'])	
		return [el['webUrl'] for el in json['response']['results']]	

	def query(self, query, from_date=date.today().strftime('%Y-01-01'), to_date=date.today().strftime('%Y-%m-%d')):
		out_list = [] 
		raw_response = self._request(query, from_date, to_date)
		json_response = json.loads(raw_response)
		out_list += self._process_result(json_response)#raw_response
		current_page = 1
		while current_page < json_response['response']['pages']:
			current_page += 1
			raw_response = self._request(query, from_date, to_date, current_page)
			json_response = json.loads(raw_response)
			out_list += self._process_result(json_response)
		return out_list

class NewYorkTimes(object):
	def __init__(self, api_key):
		self.api_key = api_key

	def _request(self, query, from_date, to_date, offset=0):
		if not query or not query.strip():
			return None

		endpoint = 'http://api.nytimes.com/svc/search/v1/article'
		payload = {
			'query': query,
			'api-key': self.api_key,
			'begin_date': from_date,
			'end_date': to_date,
			'offset': offset
		}
		api_response = requests.get(endpoint, params=payload)
		api_response.raise_for_status()
		return api_response.text

	def _process_result(self, json):
		return [el['url'] for el in json['results']]

	def query(self, query, from_date=date.today().strftime('%Y0101'), to_date=date.today().strftime('%Y%m%d')):
		out_list = []
		raw_response = self._request(query, from_date.replace('-', ''), to_date.replace('-', ''))
		json_response = json.loads(raw_response)
		out_list += self._process_result(json_response)
		current_offset = 0
		while current_offset < (json_response['total']/10):
			current_offset += 1
			raw_response = self._request(query, from_date.replace('-', ''), to_date.replace('-', ''), current_offset)
			json_response = json.loads(raw_response)
			out_list += self._process_result(json_response)
		return out_list