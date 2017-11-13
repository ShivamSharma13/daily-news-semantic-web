import requests
from .parser import *

# TODO: Multi-threaded crawling
# Add more sites

class Crawler(object):
	''' To fetch web pages for a list of urls '''

	def __init__(self, urls, *args, **kwargs):
		self.urls = urls

	@staticmethod
	def fetch(url):
		try:
			r = requests.get(url, timeout=5)
			r.raise_for_status()
			return r
		except:
			return None

	def run(self):
		responses = []
		for url in self.urls:
			responses.append(Crawler.fetch(url))
		self.responses = responses

	def get_responses(self):
		return self.responses


def fetch_news_articles(news_article_links, how_many=10):
	news_article_links = news_article_links[:how_many]
	crawler = Crawler(news_article_links)
	crawler.run()
	responses = crawler.get_responses()
	news_articles = []

	for i,url in enumerate(news_article_links):
		if responses[i] is None:
			continue
		try:
			parser = NewsArticleParser(responses[i].text)
			news_articles.append(parser.parse())
		except:
			continue
	
	return news_articles

def crawl(urls, how_many=10):
	crawler = Crawler(urls)
	crawler.run()
	responses = crawler.get_responses()

	news_article_links = list()

	for i,url in enumerate(urls):
		if responses[i] is None:
			continue
		try:
			if 'timesofindia' in url:
				parser = TOIParser(responses[i].text, url)
				news_article_links.extend(list(parser.parse()))
			else:
				parser = LinkParser(responses[i].text, url)
				news_article_links.extend(list(parser.parse()))
		except:
			continue
	
	return fetch_news_articles(news_article_links, how_many)



if __name__ == '__main__':
	
	from pprint import pprint
	
	urls = ['https://timesofindia.indiatimes.com', 'https://www.ndtv.com']

	news_articles = crawl(urls)

	print('News Articles Fetched: ', len(news_articles))
	pprint(news_articles)
