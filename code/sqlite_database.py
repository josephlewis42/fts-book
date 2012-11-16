#!/usr/bin/env python
import os
import sqlite3
import time
import document
import sys

SQLITE_PATH = os.path.expanduser(os.path.join("~",".sqlite_fts.sqlite3"))

class SQLITEBackend:
	conn = None
	cursor = None

	def __init__(self):
		""" Opens a connection to the database, or if it doesn't exist yet, 
		creates the database.
		"""
		self.conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
		self.cursor = self.conn.cursor()
	
		# Create the documents table.
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS documents (
							id INTEGER PRIMARY KEY AUTOINCREMENT,
							uri TEXT,
							dirty BOOLEAN,
							time NUMERIC)
							""")
	
		self.cursor.execute("""CREATE INDEX IF NOT EXISTS document_uri_index ON documents (uri)""")
	
		# Create the metadata tables.
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS metadata_dict (id INTEGER PRIMARY KEY AUTOINCREMENT,
															metadata_key TEXT,
															metadata_value TEXT)""")
	
		self.cursor.execute("""CREATE UNIQUE INDEX IF NOT EXISTS metadata_dict_index ON metadata_dict (metadata_key, metadata_value)""")
	
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS metadata_document_map (metadata_id INTEGER REFERENCES metadata_dict(id) ON DELETE CASCADE, 
																				document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE)""")
	
		self.cursor.execute("""CREATE INDEX IF NOT EXISTS metadata_document_map_index ON metadata_document_map (metadata_id)""")
	
		# Create the term tables.
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS terms (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								term TEXT)""")
	
		self.cursor.execute("""CREATE INDEX IF NOT EXISTS term_index ON terms (term)""")
	
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS term_document_map (
								term INTEGER REFERENCES terms(id) ON DELETE CASCADE,
								document INTEGER REFERENCES documents(id) ON DELETE CASCADE,
								frequency INTEGER
								)""")
		
		self.cursor.execute("""CREATE UNIQUE INDEX IF NOT EXISTS term_document_map_index ON term_document_map (term, document)""")
			
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS term_doc_location 
								(term INTEGER REFERENCES terms(term) ON DELETE CASCADE,
								document INTEGER REFERENCES documents(id) ON DELETE CASCADE,
								location INTEGER
								)""")
		self.cursor.execute("""CREATE INDEX IF NOT EXISTS term_document_location_index ON term_doc_location (term, document)""")
	

	def get_document_uri(self, docid):
		'''Returns the uri for the document with the given id. If no document 
		exists, returns a blank string.
		
		Params:
			docid - (integer) The id of the document to fetch the URI for.
		'''
		
		ret = self.cursor.execute('SELECT uri FROM documents WHERE id=?', (docid,)).fetchone()
		return ret[0] if ret != None else ""
	
	
	def find_documents_for_term(self, term):
		''' Returns a list of all documents that have the given term in them.
		
		Params:
			term - (string) the term to search for.
		'''
		# first get the term key, if possible.
		ret = self._get_or_create_term_id(term, create=False)
	
		if ret == None:
			return []
	
		# now select all documents with term
		docs = self.cursor.execute('SELECT document FROM term_document_map WHERE term = ?',(ret,))
	
		return [row[0] for row in docs.fetchall()]
	
	
	def find_documents_for_metadata(self, key, value):
		''' Returns a list of document ids such that they have the given key
		and value in metadata. If no such metadata exists, an empty list
		will be returned.
		
		Params:
			key		- (string) The key of the metadata to search for.
			value	- (string) The value of the metadata to search for.
		'''
		mid = self._get_metadata_id(key, value)
	
		if mid == None:
			return []

	
		docids = []
		for docid in self.cursor.execute("SELECT document_id FROM metadata_document_map WHERE metadata_id = ?", (mid, )).fetchall():
			docids.append(docid[0])
		
		return docids
	
	
	def find_metadata_for_document(self, docid):
		''' Finds the key->values of the metadata for the given document.
		
		Params:
			docid - (integer) The id of the document to fetch metadata for.
		
		Returns:
			A key->value map for the metadata associated with the document.
		'''
		
		metadatas = {}
		for md_id in self.cursor.execute("SELECT metadata_id FROM metadata_document_map WHERE document_id = ?", (docid,)).fetchall():
			for key, value in self.cursor.execute("SELECT metadata_key, metadata_value FROM metadata_dict WHERE id = ?", (md_id[0],)).fetchall():
				metadatas[key] = value
		
		return metadatas


	def _get_or_create_term_id(self, term, create=True):
		ret = self.cursor.execute("SELECT id FROM terms WHERE term = ?", (term,)).fetchone()
	
		if ret != None:
			return ret[0]
		else:
			if create == True:
				return self.cursor.execute("INSERT INTO terms (term) VALUES (?)", (term,)).lastrowid
			return None

	def _get_metadata_id(self, key, value):
		# normalize key, value
		key, value = document.normalize(key), document.normalize(value)
		
		ret = self.cursor.execute("SELECT id FROM metadata_dict WHERE metadata_key = ? AND metadata_value = ?", (key, value)).fetchone()
	
		return ret[0] if ret != None else None

	def _get_or_create_metadata_id(self, key, value):
		# normalize key, value
		key, value = document.normalize(key), document.normalize(value)
		ret = self.cursor.execute("SELECT id FROM metadata_dict WHERE metadata_key = ? AND metadata_value = ?", (key, value)).fetchone()
	
		if ret != None:
			return ret[0]
		else:
			return self.cursor.execute("INSERT INTO metadata_dict (metadata_key, metadata_value) VALUES (?,?)", (key, value)).lastrowid
	
	
	def add_document(self, doc):
		''' Adds the given document to the database, deleting any documents
		that have the same URI first.
		
		Params:
			doc - An object that has the following attributes:
					uri       - (string) the uri of the "document"
					metadata  - (string->string map) A map of key->value pairs
								representing metadata for the object.
					words_map - (string->int[]) A map of the terms in the 
								document to the locations of those terms in the 
								full text.
				  
		Example:
			class SimpleDoc:
				uri = "http://simple.doc/path/to/doc.txt"
				metadata = {"type":"text","author":"john_john"...}
				words_map = {"hello":[0],"world":[1],"said":[2],"john":[3, 4]}
			
			This would represent the document: "Hello world, said John John." 
			after it had been normalized.
	
		Returns:
			True if document was successfully added, False otherwise.
	
		'''
		
		# needs 3 properties, without these we don't have a doc
		try:
			uri = doc.uri
			metadata = doc.metadata
			words_map = doc.words_map
			
			# First delete any old documents with the same URI
			self.cursor.execute("DELETE FROM documents WHERE uri = ?", (uri,))
		
			ret = self.cursor.execute("INSERT INTO documents (uri, dirty, time) VALUES (?,?,?)", (uri, False, time.time()))
			doc_id = ret.lastrowid
		
			term_doc_maps = []
			term_doc_locations = []
			for word, locations in list(words_map.items()):
				term_id = self._get_or_create_term_id(word)
				term_doc_maps.append((term_id, doc_id, len(locations)))

				for loc in locations:
					term_doc_locations.append((term_id, doc_id, loc))
			
			self.cursor.executemany("INSERT INTO term_document_map VALUES (?,?,?)", term_doc_maps)
			self.cursor.executemany("INSERT INTO term_doc_location VALUES (?,?,?)", term_doc_locations)
		
			for key, value in list(metadata.items()):
				parent = self._get_or_create_metadata_id(key, value)
				self.cursor.execute("INSERT INTO metadata_document_map VALUES (?,?)", (parent, doc_id))

		
			return True
		except KeyError:
			return False
	
	def reconstruct_document(self, doc_id):
		''' Takes the given document, and reports all the terms in it, in order,
		back as a string. If no such document exists, return an empty string.
		
		Example:
			If document 0 was originally indexed as "the quick red fox"
			
			> reconstruct_document(0)
			"the quick red fox"
			
			> reconstruct_document(-999999) # doesn't exist
			""
		
		Params:
			doc_id - The id of the document to look for the string in
		
		'''
		return self.reconstruct_partial_document(doc_id, 0, sys.maxsize)
	
		
	def reconstruct_partial_document(self, doc_id, termstart, termend):
		''' Takes the given document, and returns the terms from termstart to
		termend that were found in that document. If there are no terms within
		the given range, an empty string is returned.
		
		Example:
			If document 0 was originally indexed as "the quick red fox"
			
			> reconstruct_partial_document(0, 1, 2)
			"quick red"
			
			> reconstruct_partial_document(0, 50, 100)
			""
		
		Params:
			doc_id		- The id of the document to look for the string in.
			termstart	- The first word to include in the reconstruction.
			termend		- The last word to include in the reconstruction.
		
		'''
		document = {}
		for term, loc in self.cursor.execute("SELECT term,location FROM term_doc_location WHERE document=? AND location<=? AND location>=?", (doc_id,termend, termstart)).fetchall():
			document[loc] = self.id_to_term(term)
		
		output = ""
		for key in sorted(document.keys()):
			if key < 0:
				continue
			output += document[key]
			output += ' '
		return output
		
	def get_term_locations(self, term, document_id):
		''' Returns an array of the locations of the given term in the given
		document.
		
		Params:
			term		- a string that represents the term to be searched for.
			document_id - the id of the document to search for
		'''
		
		term_id = self._get_or_create_term_id(term, create=False)
		
		if not term_id:
			return []
			
		locs = []
		
		for loc in self.cursor.execute("SELECT location FROM term_doc_location WHERE term=? AND document=?", (term_id,document_id)).fetchall():
			locs.append(loc[0])
		return locs
		
	def documents_with_phrase(self, phrase):
		'''Returns a list of documents that contain the given phrase.
		
		Params:
			phrase - (string[]) an array of words that constitute the phrase.
		'''
		if phrase == []:
			return []
		
		return [ x for x in self.find_documents_for_term(phrase[0]) if self.contains_phrase(phrase, x)]

		
	def contains_phrase(self, phrase, document_id):
		''' True if the document contains the given phrase, False otherwise.
		
		Params:
			phrase - (string[]) an array of words that constitute the phrase.
			document_id - (integer) the id of the document to look for the 
									phrase in.
		'''
		if phrase == []:
			return True
		
		phrase_locations = []
		
		for index, word in enumerate(phrase):
			locs = self.get_term_locations(word, document_id)
			
			locs = [location for location in locs if location >= 0]
			
			if index == 0:
				if locs == None or len(locs) == 0:
					return False
				phrase_locations.append(locs)
				continue
			
			locs = [x for x in locs if x - 1 in phrase_locations[index - 1]]
			
			if locs == None or len(locs) == 0:
				return False
			else:
				phrase_locations.append(locs)

		
		return True
		
		
		
	
	def id_to_term(self, term_id):
		''' Returns the term text from the given term id or None if no term id 
		is given.
		
		Example:
			> id_to_term(85)
			"wolf"
		
		Params:
			term_id - (integer) The id of the term to return the value for.
		'''
		ret = self.cursor.execute("SELECT term FROM terms WHERE id=?", (term_id,)).fetchone()
		return ret[0] if ret else None

		
	
	
	def shutdown(self):
		''' A method that is called before the whole software quits. The 
		database is saved and closed during this call.
		'''
		self.conn.commit()
		self.conn.close()
		
	def frequency(self, document_id, term):
		''' Returns the frequency of a term in a particular document.
		Returns 0 if the term is not present in the document, or the document
		doesn't exist.
		
		Params:
			document_id - (integer) The id of the document to look for the term
							frequency in.
			term - (string) The term to look for in the document.
		'''
		# first get the term key, if possible.
		ret = self._get_or_create_term_id(term, create=False)

		if ret == None:
			return []
	
		# now select all documents with term
		docs = self.cursor.execute('SELECT frequency FROM term_document_map WHERE term = ? AND document = ?',(ret,document_id)).fetchone()
	
		if docs == None:
			return 0
		
		return docs[0]
	
	def total_frequency(self, term):
		''' Returns the total number of times a particular term was found
		in the index.
		
		Params:
			term - (string) the term to fetch the frequency for.
		'''
		
		term_id = self._get_or_create_term_id(term, create=False)
		
		if not term_id:
			return 0
		
		docs = self.cursor.execute('SELECT frequency FROM term_document_map WHERE term = ?',(term_id,)).fetchall()
		
		return sum([doc[0] for doc in docs])
	
	def count_documents(self):
		''' Returns the total number of documents in the index. '''
		return len(self.cursor.execute('SELECT id FROM documents').fetchall())
