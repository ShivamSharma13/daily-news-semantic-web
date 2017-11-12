import re
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urlparse, urljoin

class Parser(object):
	
	def __init__(self, content, strainer=None, *args, **kwargs):
		if strainer:
			self.soup = BeautifulSoup(content, 'html.parser', parse_only=strainer)
		else:
			self.soup = BeautifulSoup(content, 'html.parser')

	def parse(self):
		raise NotImplementedError


# ====+====+====+====+====+====+====+====+ #

def site_links_validator(link, additional_validation_func=None):
	''' Validates links to filter the ones:
		- that are of the same domain
		- have correct path
	'''
	
	# Additional Validation Function passes the tag as param
	
	def inner(tag):
		try:
			href = tag['href']
		except KeyError:
			return False
		parsed_url = urlparse(href)
		valid_netloc = (not parsed_url.netloc) or (parsed_url.netloc.split('.')[-2] == urlparse(link).netloc.split('.')[-2])
		valid_path = bool(re.match(r'^/.+$', parsed_url.path))
		verdict = valid_netloc and valid_path

		if additional_validation_func is not None:
			verdict = verdict and additional_validation_func(tag) # and parsed_url.path.endswith('.cms')
			
		return verdict
	return inner

# ====+====+====+====+====+====+====+====+ #

class LinkParser(Parser):
	''' Links parser. Uses SoupStrainer to strain the anchor tags '''

	def __init__(self, content, url, *args, **kwargs):
		strainer = SoupStrainer('a') # Straining anchor tags
		super().__init__(content, strainer=strainer, *args, **kwargs)
		self.url = url

	def clean_anchors(self, anchor_tags):
		''' Cleans anchor tags for 'href' attribute '''
		news_article_links = set()
		for a in anchor_tags:
			parsed_url = urlparse(a['href'])
			if not parsed_url.netloc:
				news_article_links.add(urljoin(self.url, parsed_url.path))
			else:
				news_article_links.add(a['href'])
		return news_article_links

	def parse(self):
		anchors = self.soup.find_all(site_links_validator(self.url))
		return self.clean_anchors(anchors)

# ====+====+====+====+====+====+====+====+ #

class TOIParser(LinkParser):
	''' (Homepage) Links Scraper with personalized validations for Times of India. '''

	def __init__(self, content, url, *args, **kwargs):
		super().__init__(content, url, *args, **kwargs)

	@staticmethod
	def _toi_links_checker(tag):
		''' Checks whether the href ends in .cms for TOI article links '''
		# Additional validation
		parsed_url = urlparse(tag['href'])
		return parsed_url.path.endswith('.cms')

	def parse(self):
		anchors = self.soup.find_all(site_links_validator(self.url, TOIParser._toi_links_checker))
		return self.clean_anchors(anchors)

# ====+====+====+====+====+====+====+====+ #

class NewsArticleParser(Parser):
	''' Parses for NewsArticle Entity, and its attributes.
		Ref: https://schema.org/NewsArticle
	'''

	def __init__(self, content, *args, **kwargs):
		super().__init__(content, *args, **kwargs)

	@staticmethod
	def _tag_has_attribute(attr_name):
		''' If bs4.Tag object has attribute passed '''
		def inner(tag):
			return tag.has_attr(attr_name)
		return inner
	
	@staticmethod
	def _news_article_checker(tag):
		''' Returns True if the tag defines the scope of NewsArticle, else False '''
	
		# Assuming microdata format as:
		# <div itemscope itemtype="https://schema.org/NewsArticle">
	
		# Helper functions for bs4.Tag
		has_itemscope = NewsArticleParser._tag_has_attribute('itemscope')
		has_itemtype = NewsArticleParser._tag_has_attribute('itemtype')
	
		return (has_itemscope(tag) and has_itemtype(tag) and 'NewsArticle' in tag['itemtype'])

	@staticmethod
	def _parse_itemscope(scope_tag):
		has_itemscope = NewsArticleParser._tag_has_attribute('itemscope')
		has_itemprop = NewsArticleParser._tag_has_attribute('itemprop')
		itemscopes = scope_tag.find_all(has_itemscope)

		properties = {}

		if any(itemscopes):
			for each in itemscopes:
				result = NewsArticleParser._parse_itemscope(each)
				if result[0]: # Property
					properties[result[0]] = result[1]

		properties['type'] = urlparse(scope_tag['itemtype']).path.replace('/','')

		for prop_tag in scope_tag.find_all(has_itemprop):
			if not prop_tag or not prop_tag.attrs:
				continue

			itemprop = prop_tag['itemprop']

			if prop_tag.name in ['a', 'link']:
				properties[itemprop] = prop_tag['href']

			elif prop_tag.name == 'meta':
				try:
					properties[itemprop] = prop_tag['content']
				except KeyError:
					continue

			elif itemprop == 'articleBody':
				properties[itemprop] = prop_tag.text.strip()
		
			# Need to remove the already parsed itemprops, otherwise
			# they would again pop-up in the find_all of an ancestor
			# , since the call is recursive.
			if not has_itemscope(prop_tag):
				prop_tag.decompose()

		return (scope_tag.attrs.get('itemprop'), properties) # (property, dict)
	
	def parse(self):
		soup = self.soup

		articles = soup.find_all(NewsArticleParser._news_article_checker)
		has_itemscope = NewsArticleParser._tag_has_attribute('itemscope')
		parsed_articles = []

		for article in articles:
			# Each article is an itemscope with itemtype NewsArticle
			parsed_articles.append(NewsArticleParser._parse_itemscope(article)[1])

		return parsed_articles
