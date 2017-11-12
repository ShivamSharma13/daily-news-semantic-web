'''Utility Functions'''

from urllib.parse import urljoin

from nltk import pos_tag, ne_chunk, word_tokenize
from nltk.tokenize import PunktSentenceTokenizer

import re

HOST = 'http://search.com/'


def traverse_ner(tree):
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


def named_entity_recognition(text, lower=True):
	tokenizer = PunktSentenceTokenizer()
	tokenized = tokenizer.tokenize(text)

	persons, locations, organizations = [set() for _ in range(3)]
	for sentence in tokenized:
		words = word_tokenize(sentence)
		tagged = pos_tag(words)
		ner = ne_chunk(tagged)
		entities = traverse_ner(ner)

		for entity in entities:
			ne = entity[0]
			ent = (entity[1].strip().lower() if lower else entity[1].strip())
			print(ne, ent)
			if ne == 'PERSON':
				persons.add(ent)
			elif ne == 'ORGANIZATION':
				organizations.add(ent)
			else: # GPE, LOCATION
				locations.add(ent)

	return (persons, locations, organizations)


def extract_main_location(articleBody):
	main_loc = re.search(r'^(?P<loc>([A-Z ]+/?)+) ?: ?.*', articleBody) # NEW DELHI/MUMBAI: 
	if main_loc and main_loc.groupdict():
		main_loc = [l.strip().lower() for l in main_loc.groupdict()['loc'].split('/')]
		articleBody = re.sub(r'^(?P<loc>([A-Z ]+/?)+) ?: ?', '', articleBody).strip()

	return (main_loc, articleBody)


def normalize(text):
	return re.sub(r'\s+', '_', text.strip().lower())


def get_uri(localname, type='A'):
	if type == 'A':
		namespace = "newsarticle/ontology/"
	elif type == 'L':
		namespace = "location/ontology"
	elif type == 'O':
		namespace = "organization/ontology/"
	elif type == 'P':
		namespace = "person/ontology/"
	return urljoin(HOST, namespace) + localname


def get_context_uri(type):
	if type == 'A':
		name = 'articledata'
	elif type == 'C':
		name = 'categorydata'
	elif type == 'P':
		name = 'persondata'
	elif type == 'O':
		name = 'organizationdata'
	elif type == 'L':
		name = 'locationdata'
	else:
		raise TypeError
	url = "context#" + name
	return '<' + urljoin(HOST, url) + '>'


def add_quad(conn, subject, predicate, obj, context):
	if not any(conn.getStatements(subject, predicate, obj, context).asList()):
		conn.add(subject, predicate, obj, context)
		return True
