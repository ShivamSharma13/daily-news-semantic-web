from allegro.connect import AllegroConnection
from allegro.dump import dump
from allegro.utils import normalize, get_uri, get_context_uri
from flask import Flask, jsonify, request, render_template, redirect
from web_scraper.crawler import crawl

app = Flask(__name__)
conn = None

@app.route('/', methods=['GET'])
def landing():
	print(conn)
	return render_template('index.html')

@app.route('/search/', methods=['GET'])
def search():
	query = request.args.get('q').strip().lower()
	normalized = normalize(query)

	persons = conn.getStatements(context=get_context_uri('P'), predicate=conn.createURI(get_uri('fullName', 'P')), object=conn.createLiteral(query, datatype=XMLSchema.STRING)).asList()
	organizations = conn.getStatements(context=get_context_uri('O'), predicate=conn.createURI(get_uri('title', 'O')), object=conn.createLiteral(query, datatype=XMLSchema.STRING)).asList()
	articles = set()
	for each in persons + organizations:
		article_uris = conn.getStatements(context=get_context_uri('A'), object=each.getSubject()).asList()
		for a in article_uris:
			articles.add(a.getSubject().uri)
	
	result = [{'url': '', 'heading': ''}]

	return jsonify(result), 200

@app.route('/update/', methods=['GET'])
def update():
	''' Add more articles '''
	urls = ['https://timesofindia.indiatimes.com', 'https://www.ndtv.com']
	articles = [article for article in crawl(urls, how_many=999) if article]
	try:
		dump(conn, articles)
	except Exception as e:
		print(e)
		return jsonify({'updated': False}), 500
#	return jsonify({'updated': True}), 200
	return redirect('http://localhost:8000/')

if __name__ == '__main__':
	username = input("Enter username: ")
	password = input("Enter password: ")
	connection = AllegroConnection(username, password, 'DailyNewsEngine')
	connection.establish_connection()

	conn = connection.connection
	app.run(host='localhost', port=8000)
