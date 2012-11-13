#!/usr/bin/env python

'''
Called like so:
>>>	import document
>>>	 d = document.Document(open('tests/incorrect_spelling'), 'file://tests/incorrect_spelling')
'''

import spell_checker
import collections
import re

# If the document is *huge* don't index it all, just the first part.
BYTES_TO_READ=100000
sc = spell_checker.Checker()



def parse_document(doc):
	'''Parses a document in to a list of strings.'''
	doc = doc.lower()
	doc = re.sub(r'[^\w\s]+', '', doc)
	return doc.split()


def normalize(string):
	'''Normalizes a string, while replacing all whitespace with underscores.'''
	return "_".join(parse_document(string))



class Document:
	'''
	A class representing a document, has 3 properties:
	
	Properties:
		uri - the uri of the document that was indexed
		metadata - a key->value map for the metadata associated with the doc
		words_map - a map of the words in this document to their occurances
				Example Input:
					"I like kats. Cats are cool because they are fluffy"
				Example words_map:
					{'i':[0],'like':[1],'kats':[2],'cats':[-1,3],...}
	
	'''
	def __init__(self, fd, uri, metadatadict={}):
		''' Indexes/normalizes a document.'''

		self.metadata = metadatadict
		self.uri = uri
		self.words_map = collections.defaultdict(lambda: [])
		
		read = fd.read(BYTES_TO_READ).decode("utf-8")
		
		# Normalize the words.
		full_text_terms = parse_document(read)
		
		# Count the # of times each term appears in the document.
		term_frequency_map = sc.get_doc_dict(full_text_terms)
		
		for location, term in enumerate(full_text_terms):
			# Add the term location to the map of term to locations
			self.words_map[term].append(location)
			
			# Check the spelling of this term, if new add it with
			# a location of -1
			new_term = sc.check_word(term, term_frequency_map)
			if new_term != term:
				self.words_map[new_term].append(-1)
		
		# append all metadata as index of -2
		for term in parse_document(" ".join(self.metadata.values())):
			self.words_map[term].append(-2)
			

