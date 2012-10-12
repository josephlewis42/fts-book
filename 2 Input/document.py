import spell_checker
import stemmer
import parser
import json

class Document:
	# full text of the document
	full_text_words = []
	
	# full text of the document, run through the spelling correction
	# algorithm
	spelling_corrected_full_text = []
	
	# frequency of words found in the document
	word_frequency_map={}
	
	def __init__(self, fd):
		''' Indexes/normalizes a document.'''
		
		self.full_text_words = parser.parse_document(fd.read())
		self.word_frequency_map = 
		
		for word in self.full_text_words:
			spelling_c
			
	def 
