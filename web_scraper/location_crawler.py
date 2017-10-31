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
	def _gather_schema_data(r):
		soup = BeautifulSoup(r.content , 'html.parser')
		data = {}
		cities = []
		state_container = soup.find('tr' , {'itemtype' : 'http://schema.org/State'})
		cities_containers = soup.find_all('tr' , {'itemtype' : 'http://schema.org/City'})
		if state_container is not None:
			state_name = state_container.find('span' , {'itemprop' : 'name'}).string
		for city_container in cities_containers:
			city_name = city_container.find('span' , {'itemprop' : 'name'}).string
			cities.append(city_name)
		print(cities)

	def get_root_anchors(self):
		return self.root_anchors

	def parse_all(self):
		print("Now parsing...")
		for country in self.root_anchors:
			state_anchors = LocationCollector._gather_state_anchors(country)
			#Multi-Threading can be implemented here.
			print("Extracted %d states." %len(state_anchors))
			for idx, state in enumerate(state_anchors):
				print("[Hit] %d of %d sates" %(idx+1 , len(state_anchors)))
				r = LocationCollector.hit(urljoin(source , (state.get('href'))))
				if r == None:
					print("Error! Missed %s." %state.__str__())
					continue
				schema_data_instance = LocationCollector._gather_schema_data(r)
				if idx == 4:
					break
			print("Completed location extraction for root_anchor.")


if __name__ == '__main__':
	root_anchors = ['India' , ]
	source = 'https://www.citypopulation.de'
	urls = [urljoin(source , (country + ".html")) for country in root_anchors]
	collector = LocationCollector(urls)
	collector.parse_all()