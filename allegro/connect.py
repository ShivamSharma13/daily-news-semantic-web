from franz.openrdf.sail.allegrographserver import AllegroGraphServer
from franz.openrdf.repository import Repository
from franz.openrdf.exceptions import ServerException
from franz.miniclient.request import RequestError
import os

class AllegroConnection(object):
	def __init__(self, username, password, repository, *args, **kwargs):
		self.username = username
		self.password = password
		self.repository = repository

	def establish_connection(self):
		try:
			server = AllegroGraphServer(host = '192.168.1.27' , port = 10035 , user = self.username , password = self.password)
			catalog = server.openCatalog(None)
		except RequestError:
			print("Please run the script again.")
			exit()
		repository = None
		try:
			repository = catalog.getRepository(self.repository , Repository.OPEN)
		except ServerException:
			print("No repository found. Creating repository...")
			#creating repository if Allegro doesn't have it.
			repository_name = input("Enter the name of Repository. (Enter 'y' for DailyNewsEngine)")
			if repository_name == 'y':
				repository_name = 'DailyNewsEngine'
			self.repository = repository_name
			catalog.createRepository(repository_name)
			repository = catalog.getRepository(self.repository , Repository.OPEN)
		if repository != None:
			repository = repository.initialize()	
			connection = repository.getConnection()
		self.connection = connection
		return {'server' : server , 'catalog' : catalog , 'repository' : repository , 'connection' : connection}

	def test(self):
		connection = self.connection
		statements = connection.getStatements(output_format = 'JSON')
		num = len(statements.asList())
		print("%d statements in your repository." %num)


	def setup(self):
		ontologies_path = 'ontologies'
		print('Adding Ontologies...')
		AllegroConnection._add_files(ontologies_path , self.connection)
		print('Ontologies added successfully.')
		data_path = 'data'
		print('Adding data files...')
		AllegroConnection._add_files(data_path , self.connection)
		print('Data files added successfully.')

	def _add_files(_path, connection):
		files_present = connection.getContextIDs()
		path = ''
		try:
			path = os.path.join(os.getcwd() , _path)
			filenames = os.listdir(path)
		except FileNotFoundError:
			print("Incorrect path...")
			exit()
		for idx , filename in enumerate(filenames):
			file_path = os.path.join(path , filename)
			filename, file_extension = os.path.splitext(file_path)
			if file_extension != '.ttl':
				continue
			with open(file_path) as file:
				#fetching the context from the first comment of the ontology file.
				context = file.readline()
			
			#exiting if context is not present.
			if context[0] != '#':
				print('[ERROR] ==> Context comment is missing. Please add a context comment and try again.')
				exit()
			
			#using context[1:] below because of the '#' symbol in the begining of the 1st line used for comment. 
			context_uri = connection.createURI(context[1:].replace('\n' , ''))
			if context_uri in files_present:
				print('Ignoring file %d of %d. Already present. Try changing the first comment of the file.' %(idx + 1, len(filenames)))
				continue
			
			print('Dumping file %d of %d' %(idx + 1, len(filenames)))				
			connection.addFile(filePath = file_path , context = context_uri)
		return		


if __name__ == '__main__':
	username = input("Enter username: ")
	password = input("Enter password: ")
	repository = 'DailyNewsEngine'
	allegro = AllegroConnection(username , password , repository)
	allegro.establish_connection()
	allegro.test()
	allegro.setup()
