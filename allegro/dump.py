from franz.openrdf.sail.allegrographserver import AllegroGraphServer
from franz.openrdf.repository.repository import Repository
from franz.miniclient import repository
from franz.openrdf.query.query import QueryLanguage
from franz.openrdf.model import URI
from franz.openrdf.vocabulary.rdf import RDF
from franz.openrdf.vocabulary.rdfs import RDFS
from franz.openrdf.vocabulary.owl import OWL
from franz.openrdf.vocabulary.xmlschema import XMLSchema
from franz.openrdf.query.dataset import Dataset
from franz.openrdf.rio.rdfformat import RDFFormat
from franz.openrdf.rio.rdfwriter import  NTriplesWriter
from franz.openrdf.rio.rdfxmlwriter import RDFXMLWriter

from pprint import pprint

import os, sys, uuid

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from allegro.connect import AllegroConnection
from allegro.utils import *
from web_scraper.crawler import crawl

def dump(conn, articles):
	for article in articles:
		article = article[0]
		# pprint(article)

		if not 'articleBody' in article:
			# Not a useful article then
			continue

		news_article = {}
		news_article['uri'] = conn.createURI(get_uri(str(uuid.uuid4())))
		news_article['url'] = conn.createLiteral(article.get('mainEntityOfPage') or article.get('url', ''), datatype=XMLSchema.STRING)
		news_article['description'] = conn.createLiteral(article.get('description', ''), datatype=XMLSchema.STRING)
		news_article['headline'] = conn.createLiteral(article.get('headline', ''), datatype=XMLSchema.STRING)

		# Checking if an article already exists (assuming heading to be unique)
		if any(conn.getStatements(predicate=conn.createURI(get_uri('url')), object=news_article['url'], contexts=[get_context_uri('A')]).asList()):
			print('## Duplicate Entry for', article.get('headline'))
			continue

		# Extracting main location from start of the article
		main_loc, article['articleBody'] = extract_main_location(article['articleBody'])

		# Named Entity Recognition
		persons, locations, organizations = named_entity_recognition(article['articleBody'])

		# # # # # # # # # # 
		# Dumping Locations #
		def add_location(loc, news_prop_uri):
			loc_uri = None
			existing_statements = conn.getStatements(contexts=[get_context_uri('L')], object=conn.createURI(namespace='http://purl.org/dc/elements/1.1/', localname='title')).asList()
			if any(existing_statements):
				loc_uri = existing_statements[0].getSubject(); # Retrieving existing State/City/County URI
			else:
				loc_uri = conn.createURI(namespace='http://purl.org/dc/terms/', localname=normalize(loc))
			subject, predicate, obj, context = news_article['uri'], news_prop_uri, loc_uri, get_context_uri('A')
			add_quad(conn, subject, predicate, obj, context)

		if main_loc:
			locations = locations - set(main_loc) # because locations should contain only the secondary locs
			# Add main location(s)
			primary_location_uri = conn.createURI(get_uri('primaryLocations'))
			for loc in main_loc:
				add_location(loc, primary_location_uri)


		# Add secondary locations
		secondary_location_uri = conn.createURI(get_uri('secondaryLocations'))
		for loc in locations:
			add_location(loc, secondary_location_uri)

		# # # # # # # # # #
		# Add organizations
		mentioned_org_uri = conn.createURI(get_uri('mentionedOrganizations'))
		for org in organizations:
			org_uri = conn.createURI(get_uri(normalize(org), 'O'))

			add_quad(conn, org_uri, conn.createURI(get_uri('title', 'O')), conn.createLiteral(org, datatype=XMLSchema.STRING), get_context_uri('O'))

			subject, predicate, obj, context = news_article['uri'], mentioned_org_uri, org_uri, get_context_uri('A')
			add_quad(conn, subject, predicate, obj, context)

		# # # # # # # # # #
		# Add persons
		secondary_per_uri = conn.createURI(get_uri('secondaryPersons'))
		for person in persons:
			person_uri = conn.createURI(get_uri(normalize(person), 'P'))
			add_quad(conn, person_uri, conn.createURI(get_uri('fullName', 'P')), conn.createLiteral(person, datatype=XMLSchema.STRING), get_context_uri('P'))

			subject, predicate, obj, context = news_article['uri'], secondary_per_uri, person_uri, get_context_uri('A')
			add_quad(conn, subject, predicate, obj, context)

		author = {}
		if article.get('author') and article['author'].get('name'):
			author_name = article['author']['name']
			author['name'] = conn.createLiteral(author_name, datatype=XMLSchema.STRING)
			author['uri'] = conn.createURI(get_uri(normalize(author_name)))
		
		dates = {}
		try:
			if article.get('dateModified'):
				dates['modified'] = conn.createLiteral(article['dateModified'], datatype=XMLSchema.DATETIME)
			if article.get('datePublished'):
				dates['published'] = conn.createLiteral(article['datePublished'], datatype=XMLSchema.DATETIME)
		except:
			pass  # Leave the date. Error occurred while parsing the datetime string.

		publisher = {}
		if 'publisher' in article and article['publisher'].get('name'):
			publisher['name'] = article['publisher']['name'].lower()
			publisher['uri'] = conn.createURI(normalize(get_uri(publisher['name'])))
			if article['publisher'].get('url'):
				publisher['url'] = article['publisher']['url']

		article_section = {}
		if article.get('articleSection'):
			article_section['type'] = conn.createLiteral(article['articleSection'].lower(), datatype=XMLSchema.STRING)

# Create Statements / Add Triples
		if dates.get('published'):
			published_on = conn.createURI(get_uri('publishedOn'))
			conn.add(news_article['uri'], published_on, dates['published'], get_context_uri('A'))
#		if dates.get('modified'):
#			conn.add(news_article['uri'], modified_on, dates['modified'], get_context_uri('A'))

		if news_article.get('description'):
			description = conn.createURI(get_uri('description'))
			conn.add(news_article['uri'], description, news_article['description'], get_context_uri('A'))

		if news_article.get('headline'):
			headline = conn.createURI(get_uri('headline'))
			conn.add(news_article['uri'], headline, news_article['headline'], get_context_uri('A'))

		if news_article.get('url'):
			url = conn.createURI(get_uri('url'))
			conn.add(news_article['uri'], url, news_article['url'], get_context_uri('A'))

		if article_section.get('type'):
			news_genre = conn.createURI(get_uri('newsGenre'))
			news_category = None
			existing_triples = conn.getStatements(predicate=news_genre, object=article_section['type'], contexts=[get_context_uri('C')]).asList()
			if any(existing_triples):
				news_category = existing_triples[0].getSubject()
			else:
				news_category = conn.createURI(get_uri(str(uuid.uuid4())))
				conn.add(news_category, news_genre, article_section['type'], get_context_uri('C'))
			conn.add(news_article['uri'], conn.createURI(get_uri('category')), news_category, get_context_uri('A'))


if __name__ == '__main__':

	urls = ['https://timesofindia.indiatimes.com', 'https://www.ndtv.com']

	articles = [article for article in crawl(urls, how_many=100) if article]

	connection = AllegroConnection('super', 'allegro', 'DailyNewsEngine')
	connection.establish_connection()
	conn = connection.connection

	dump(conn, articles)
