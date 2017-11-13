import os, json, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from web_scraper.location.crawler import run_crawler

def initialize_turtle_file(turtle_file_location):
	context = '#<http://search.com/context#locationdata>\n'
	prefix_string = '@prefix country: <http://search.com/location/country/> . \n@prefix state: <http://search.com/location/state/> . \n@prefix city: <http://search.com/location/city/> . \n@prefix location: <http://search.com/location/ontology/> .\n@prefix dc: <http://purl.org/dc/elements/1.1/> .\n\n'
	with open(turtle_file_location, 'w') as file:
		file.write(context)
		file.write(prefix_string)
	return


def create_and_dump_triples(data, turtle_file_location, name = 'India', new_line = '\n'):
	country_id = name.lower().replace(" " , "_")
	predicate_title = 'dc:title'
	predicate_hasState = 'location:hasState'
	predicate_belongsTo = 'location:belongsTo'
	predicate_belongsToCountry = 'location:belongsToCountry'
	predicate_belongsToState = 'location:belongsToState'
	file = open(turtle_file_location , 'a+')
	file.write("country:" + str(country_id) + " " + str(predicate_title) + ' "' + str(name).lower() + '" .' + str(new_line))
	file.write('\n')
	for state in data:
		state_id = state['state_name'].lower().replace(" " , "_")
		file.write("state:" + str(state_id) + " " + str(predicate_title) + ' "' + str(state['state_name']).lower() + '" .' + str(new_line))
		file.write("state:" + str(state_id) + " " + str(predicate_belongsTo) + " country:" + str(country_id) + " ." + str(new_line))
		file.write("state:" + str(state_id) + " " + str(predicate_belongsToCountry) + " country:" + str(country_id) + " ." + str(new_line))
		file.write("country:" + str(country_id) + " " + str(predicate_hasState) + " state:" + str(state_id) + " ." + str(new_line))
		file.write('\n')
		for city in state['cities']:
			city_id = city.lower().replace(" " , "_")
			file.write("city:" + str(city_id) + " " + str(predicate_title) + ' "' + str(city).lower() + '" .' + str(new_line))
			file.write("city:" + str(city_id) + " " + str(predicate_belongsTo) + " state:" + str(state_id) + " ." + str(new_line))
			file.write("city:" + str(city_id) + " " + str(predicate_belongsToState) + " state:" + str(state_id) + " ." + str(new_line))
		file.write('\n\n')
	file.close()


if __name__ == '__main__':
	data = run_crawler()
	json_file_location = 'data/location.json'
	turtle_file_location = 'data/location_data.ttl'
	with open(json_file_location , 'w') as file:
		json.dump(data , file)
	#print("\n\nDumped data to a temporary File. Now reading...")
	initialize_turtle_file(turtle_file_location)
	print('\nReading and dumping location data...')
	create_and_dump_triples(data, turtle_file_location)
	print('Completed.')
	
