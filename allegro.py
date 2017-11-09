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

from urllib.parse import urljoin

from web_scraper.crawler import crawl
from pprint import pprint

from nltk import pos_tag, ne_chunk, word_tokenize
from nltk.tokenize import PunktSentenceTokenizer

import re, nltk, uuid
from .connect import AllegroConnection

HOST = 'http://search.com/' # 'http://example.org/'


def traverse(tree):
	prev_child = None
	entities = []

	def extract_word(leaves):
		return " ".join([w[0] for w in leaves])

	for child in tree:
		if hasattr(child, 'label'):
			label = child.label()
			word = extract_word(child.leaves())
			if prev_child:
				if hasattr(prev_child, 'label'):
					label = prev_child.label()
					word = extract_word(prev_child) + " " + word
				elif prev_child[1] == 'NNP':
					word = prev_child[0] + " " + word
			entities.append((label, word))
		prev_child = child
	return entities


def normalize(text):
	return re.sub(r'\s+', '_', text.strip().lower())


def get_full_uri(localname, type=':'):
	if type == 'A':
		namespace = 'article/'
	elif type == 'C':
		namespace = 'category/'
	elif type == 'P':
		namespace = 'person/'
	elif type == 'O':
		namespace = 'organization/'
	elif type == 'L':
		namespace = 'location/'
	else: # (type == ':')
		namespace = "newsarticle/ontology/"
		return urljoin(HOST,namespace, localname)
	return urljoin(HOST, namespace, normalize(localname))



def run():

	urls = ['https://timesofindia.indiatimes.com', 'https://www.ndtv.com']

	news_articles = [article for article in crawl(urls, how_many=10) if article]

	connection = AllegroConnection('super', 'password', 'DailyNewsEngine')
	connection.establish_connection()
	conn = connection.connection

	for article in articles:
		article = article[0]
		# pprint(article)
		main_loc = re.search(r'^(?P<loc>([A-Z ]+/?)+): ?.*', article['articleBody']) # NEW DELHI/MUMBAI: 
		if main_loc and main_loc.groupdict():
			main_loc = [l.strip().lower() for l in main_loc.groupdict()['loc'].split('/')]
			article['articleBody'] = re.sub(r'^(?P<loc>([A-Z ]+/?)+): ?', '', article['articleBody']).strip()
		
		tokenizer = PunktSentenceTokenizer()
		tokenized = tokenizer.tokenize(article['articleBody'])

		# Named Entity Recognition
		persons, locations, organizations = [list() for _ in range(3)]
		for sentence in tokenized:
			words = word_tokenize(sentence)
			tagged = pos_tag(words)
			ner = ne_chunk(tagged)
			entities = traverse(ner)
			for entity in entities:
				ne = entity[0]
				if ne == 'PERSON':
					persons.append(conn.createURI(entity[1], 'P'))
				elif ne == 'ORGANIZATION':
					organizations.append(conn.createURI(entity[1], 'O'))
				else: # GPE, LOCATION
					locations.append(conn.createURI(entity[1], 'L'))

#		if main_loc

		author = {}
		if 'name' in article['author']:
			author['name'] = conn.createLiteral(article['author']['name'], datatype=XMLSchema.STRING)
			author['uri'] = conn.createURI(get_full_uri(author_name, 'P'))
		
		dates = {}
		dates['modified'] = conn.createLiteral(article['dateModified'], datatype=XMLSchema.DATETIME)
		dates['published'] = conn.createLiteral(article['datePublished'], datatype=XMLSchema.DATETIME)

		news_article = {}
		news_article['uri'] = conn.createURI(get_full_uri(str(uuid.uuid4()), 'A'))
		news_article['url'] = conn.createLiteral(article['mainEntityOfPage'] or article['url'], datatype=XMLSchema.STRING)
		news_article['description'] = conn.createLiteral(article['description'], datatype=XMLSchema.STRING)
		news_article['headline'] = conn.createLiteral(article['headline'], datatype=XMLSchema.STRING)

		publisher = {}
		if 'publisher' in article and 'name' in article['publisher']:
			publisher['name'] = article['publisher']['name']
			publisher['uri'] = conn.createURI(get_full_uri(publisher['name'], 'O'))
			publisher['url'] = article['publisher']['url']

		article_section = {}
		article_section['type'] = conn.createLiteral(article['articleSection'], datatype=XMLSchema.STRING)
#		article_section['uri'] = conn.createURI(get_full_uri(article['articleSection'], 'G'))
		news_genre_uri = conn.createURI(get_full_uri('newsGenre'))

# Create Statements / Add Triples
		published_on = conn.createURI(get_full_uri('publishedOn'))
		conn.addStatement(conn.createStatement(news_article['uri'], published_on, dates['published']))
#		conn.addStatement(conn.createStatement(news_article['uri'], modified_on, dates['modified']))

		description = conn.createURI(get_full_uri('description'))
		conn.addStatement(conn.createStatement(news_article['uri'], description, news_article['description']))


		headline = conn.createURI(get_full_uri('headline'))
		conn.addStatement(conn.createStatement(news_article['uri'], headline, news_article['headline']))

		news_genre = conn.createURI(get_full_uri('newsGenre'))
		news_category = conn.createURI(get_full_uri(uuid.uuid4(), 'C'))
		conn.addStatement(conn.createStatement(new_category, news_genre, article_section['type']))

		conn.addStatement(conn.createStatement(news_article['uri'], get_full_uri('category'), news_category))
