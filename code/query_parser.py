#!/usr/bin/env
'''
A simple query langaguge for finding documents based upon search expressions.

The definition of the language is:

QUERY	= NOTBOOL (, NOTBOOL)*
NOTBOOL = (-) ANDBOOL
ANDBOOL = META+ANDBOOL | META
META	= WORD:WORD  | STRING
STRING  = "PHRASE" | WORD
PHRASE  = WORD(, WORD)*
WORD	= CHAR (, CHAR)*
CHAR 	= A-Za-z0-9

It may be useful to add in things like:
WORD<WORD | WORD>WORD
later on for meta expressions.


hello world+earth "this is a phrase" -site:google.com+test

'''

import re

SPECIAL_CHARS = [':','"','+','-']

def get_next_word(string):
	'''Returns a the next word, and the rest of the query after the word has
	been stripped.'''
	currword = ""
	
	# Strip off whitespace from head and tail.
	string = string.strip()
	
	for index, char in enumerate(string):
		for special in SPECIAL_CHARS:
			if char == special:
				if currword == "":
					return special, string[index + 1:]
				return currword, string[index:]
		
		# if whitespace, just return from here.
		if char.strip() == "":
			return currword, string[index:]
		
		currword += char
	return currword.lower(), ""

def tokenize(string):
	tokens = []
	curr = re.sub(r'[^\w\s:+"-]+', '', string.lower())
	
	while curr is not "":
		tok, rest = get_next_word(curr)
		curr = rest
		tokens.append(tok)
	
	return tokens

def word_only_tokenize(string):
	'''Tokenizes the string and returns only the words.'''
	return [tok for tok in tokenize(string) if tok not in SPECIAL_CHARS]


def get_results(querystr, database):
	'''Returns a list of documents that the query generates.
	'''
	return process_QUERY(tokenize(querystr), [], database)
	
def process_QUERY(query, curr_doc_list, database):
	while(query != []):
		query, curr_doc_list = process_NOTBOOL(query, curr_doc_list, database)
		
	return curr_doc_list

def process_NOTBOOL(query, curr_doc_list, database):
	try:
		if query[0] == '-' and query[1] not in SPECIAL_CHARS:
			query, notlist = process_ANDBOOL(query[1:], [], database)
			notlist = set(notlist)
			return query, [x for x in curr_doc_list if x not in notlist]
	except IndexError:
		pass
	
	return process_ANDBOOL(query, curr_doc_list, database)
	
	
def process_ANDBOOL(query, curr_doc_list, database):
	query, a = process_META(query, [], database)
	
	try:
		if query[0] == '+' and query[1] not in SPECIAL_CHARS:
			query, b = process_ANDBOOL(query[1:], [], database)
			
			return query, curr_doc_list + list(set(a).intersection(set(b)))
	except IndexError:
		pass
	
	return query, curr_doc_list + a
	

def process_META(query, curr_doc_list, database):
	try:
		if (query[0] not in SPECIAL_CHARS and 
			query[1] == ':' and 
			query[2] not in SPECIAL_CHARS):
				return query[3:], curr_doc_list + database.find_documents_for_metadata(query[0],query[2])
	except IndexError as ex:
		pass
		
	return process_STRING(query, curr_doc_list, database)


def process_STRING(query, curr_doc_list, database):
	# remove beginning "
	if query[0] == '"':
		query, curr_doc_list = process_PHRASE(query[1:], curr_doc_list, database)
		
		# remove ending " if it exists
		if query != [] and query[0] == '"':
			query = query[1:]
		return query, curr_doc_list
	
	return process_WORD(query, curr_doc_list, database)
	

def process_PHRASE(query, curr_doc_list, database):
	'''PHRASE  = WORD(, WORD)*'''
	last_index = 0
	
	for index, var in enumerate(query):
		if var == '"':
			last_index = index
			break
		elif var in SPECIAL_CHARS:
			last_index = index - 1
			break
		else:
			last_index = index
	else:
		last_index = len(query)
	
	return query[last_index:], database.documents_with_phrase(query[:last_index]) + curr_doc_list


def process_WORD(query, curr_doc_list, database):
	'''returns the new query and the remaining words.'''
	if len(query) == 0:
		return query, curr_doc_list
	
	if query[0] in SPECIAL_CHARS:
		return query[1:], curr_doc_list
	
	new_docs = database.find_documents_for_term(query[0])
	return query[1:], curr_doc_list + new_docs


class FakeDatabase:
	''' for testing purposes only.'''
	def find_documents_for_term(self, term):
		return [term]
	def find_documents_for_metadata(self, key, value):
		return [str(key) + ":" + str(value)]
	
	def documents_with_phrase(self, phrase):
		return phrase

if __name__ == "__main__":
	print(tokenize('"hello world"') == ['"','hello','world','"'])
	print((tokenize('"hello world:bob said+john -john') == 
				['"', 'hello', 'world', ':', 'bob', 'said', '+', 'john', '-', 'john']))
	print(word_only_tokenize('"hello world"') == ['hello','world'])
	print((word_only_tokenize('"hello world:bob said+john -john') == 
				['hello', 'world', 'bob', 'said', 'john','john']))			
				
	print(process_WORD(['testterm'], [], FakeDatabase()) == ([],['testterm']))
	print(process_WORD(['testterm'], ['a'], FakeDatabase()) == ([], ['a','testterm']))
	print(process_WORD(['testterm','b'], [], FakeDatabase()) == (['b'],['testterm']))
	print(process_WORD([':','b'], [1], FakeDatabase()) == (['b'],[1]))
	print(process_PHRASE(['w1','w2','w3','"'], [], FakeDatabase()) == (['"'],['w1','w2','w3']))
	print(process_PHRASE(['w1','w2','w3',':'], [], FakeDatabase()) == (['w3',':'],['w1','w2']))
	print(process_STRING(['"','hello','"'],[], FakeDatabase()) == ([],['hello']))
	print(process_STRING(['"','hello','world'],[], FakeDatabase()) == ([],['hello','world']))
	print(process_STRING(['"','hello',':'],[], FakeDatabase()) == (['hello', ':'], []))
	print(process_STRING(['"','h','w',':'],[], FakeDatabase()) == (['w',':'],['h']))
	print(process_STRING(['h','w',':'],[], FakeDatabase()) == (['w',':'],['h']))
	print(process_STRING(['w'],[], FakeDatabase()) == ([],['w']))
	print(process_META(['h',':','w'], [], FakeDatabase()) == ([],['h:w']))
	print(process_META(['h',':',':'], [], FakeDatabase()) == ([':',':'],['h']))
	print(process_META(['"','h','w',':'],[], FakeDatabase()) == (['w',':'],['h']))
	print(process_ANDBOOL(['a','+','b'],[], FakeDatabase()) == ([],[]))
	print(process_ANDBOOL(['a','+','a'],[], FakeDatabase()) == ([],['a']))
	print(process_ANDBOOL(['a','+','b','+'],[], FakeDatabase()) == (['+'],[]))
	print(process_ANDBOOL(['a','+','b','+','b'],[], FakeDatabase()) == ([],[]))
	print(process_ANDBOOL(['a','+','a','+','a'],[], FakeDatabase()) == ([],['a']))
	print(process_NOTBOOL(['-','a'],['a','b'], FakeDatabase()) == ([],['b']))
	print(process_NOTBOOL(['-','a'],['c','d'], FakeDatabase()) == ([],['c','d']))
	print(process_NOTBOOL(['-','c','-','d'],['c','d'], FakeDatabase()) == (['-','d'],['d']))
	print(process_QUERY(['a','b','c'], [], FakeDatabase()) == ['a','b','c'])
	print(get_results("a b c:d", FakeDatabase()) == ['a','b','c:d'])
	print(get_results("a b c:d d+d+d", FakeDatabase()) == ['a','b','c:d','d'])
	print(get_results("a b c:d d+d+d -d", FakeDatabase()) == ['a','b','c:d'])

