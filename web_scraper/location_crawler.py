import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class LocationCollector(object):
	def __init__(self, urls, *args, **kwargs):
		self.urls = urls
		self.root_anchors = []
		self.schema_data = {}
		for url in self.urls:
			self.root_anchors.append(LocationCollector.hit(url))
		print("Successfully gathered %d root anchors." %len(self.root_anchors))

	@staticmethod
	def hit(url):
		try:
			r = requests.get(url)
			r.raise_for_status()
			return r
		except:
			print("Missed URL: %s" %url)
			return None

	@staticmethod
	def _gather_state_anchors(country):	
		soup = BeautifulSoup(country.content ,'html.parser')
		columns = soup.find_all('div' , {'class' : 'mcol'})
		#fetching Major and Midsize Agglomerations and Cities
		agglo_column_div = columns[0]
		state_anchors = agglo_column_div.find_all('a')
		return state_anchors

	@staticmethod
	def _sort_through_values(unsorted_ranks):
		'''
			Give a dictionary and the function returns a list of dictionary values arranged by [keys]. 
			Highest first.
		'''
		populations = []
		for key, value in unsorted_ranks.items():
			populations.append(key)
		populations.sort()
		populations.reverse()
		return [unsorted_ranks[key] for key in populations]

	@staticmethod
	def _standardize_number_of_cities(cities):
		'''
		Limiting the number of cities. Min and Max are set. 
		Some large states have too many cities and the upper limit in those cases shoots up.
		'''
		minimum_cities = 1
		maximum_cities = 8
		length = len(cities)
		if length < 10:
			return cities[:minimum_cities]
		else:
			standardized_length = int(length * 0.1)
			if standardized_length > 8:
				standardized_length = maximum_cities
			return cities[:standardized_length]

	@staticmethod
	def _gather_schema_data(r):
		soup = BeautifulSoup(r.content , 'html.parser')
		data = {}
		unsorted_ranks = {}
		cities = []
		state_name = ""
		state_container = soup.find('tr' , {'itemtype' : 'http://schema.org/State'})
		#Sometimes there is an Administrative state instead of a simple state. Like: Delhi, Andamans etc.
		if state_container is None:
			state_container = soup.find('tr' , {'itemtype' : 'http://schema.org/AdministrativeArea'})
		state_name = state_container.find('span' , {'itemprop' : 'name'}).string
		cities_containers = soup.find_all('tr' , {'itemtype' : 'http://schema.org/City'})		
		for city_container in cities_containers:
			city_name = city_container.find('span' , {'itemprop' : 'name'}).string
			#parameter is taken as population of the latest census. [Inside td tag with class attribute : "prio1"]
			city_parameter = city_container.find('td' , {'class' : 'prio1'}).string
			if city_name is not None and city_parameter is not None:
				try:
					city_population = int(city_parameter.replace(',' , ''))
					unsorted_ranks[city_population] = city_name
				except ValueError:
					pass
		cities = LocationCollector._sort_through_values(unsorted_ranks)
		data[state_name] = LocationCollector._standardize_number_of_cities(cities)
		print(data)
		return data

	def get_root_anchors(self):
		return self.root_anchors

	def parse_all(self):
		print("Now parsing...")
		for country in self.root_anchors:
			state_anchors = LocationCollector._gather_state_anchors(country)
			#Multi-Threading can be implemented here.
			print("Extracted %d states. \n" %len(state_anchors))
			for idx, state in enumerate(state_anchors):
				print("[Hit] %d of %d sates" %(idx+1 , len(state_anchors)))
				r = LocationCollector.hit(urljoin(source , (state.get('href'))))
				if r == None:
					print("========>  Error! Missed %s. <========" %state.__str__())
					continue
				schema_data_instance = LocationCollector._gather_schema_data(r)
			print("\n\nCompleted location extraction for root_anchor. Bye!!")


if __name__ == '__main__':
	root_anchors = ['India' , ]
	source = 'https://www.citypopulation.de'
	urls = [urljoin(source , (country + ".html")) for country in root_anchors]
	collector = LocationCollector(urls)
	collector.parse_all()