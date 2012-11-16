#!/usr/bin/env python
import query_parser


def _inverse_term_frequency(term, database):
	''' Returns the 1/frequency of the word in the database, if the term exists,
	else returns 0.
	'''
	try:
		return 1.0 / database.total_frequency(term)
	except ZeroDivisionError:
		return 0


def rank_documents(querystring, document_list, database):
	''' Iterates over a set of documents, and ranks them from most relevant to 
	least based upon the query that the user performed.
	'''
	docmap = {}
	for doc in list(set(document_list)):
		docmap[doc] = 0

	for word in query_parser.word_only_tokenize(querystring):
		wordweight = _inverse_term_frequency(word, database)
	
		if wordweight == 0:
			continue
	
		for doc in docmap.keys():
			docmap[doc] += wordweight * database.frequency(doc, word)
		
	return docmap


def generate_summary(querystring, document_id, database, summary_length=20):
	''' Generates a "summary" based upon the document and query string. 

	The summary results are weighted, so they will contain the most relevant results instead of 
	the greatest number of results.

	'''
	location_worth = {} # A map between the location, and how much the term in it is worth.

	for term in query_parser.word_only_tokenize(querystring):
		term_weight = _inverse_term_frequency(term, database)
	
		for location in database.get_term_locations(term, document_id):
			location_worth[location] = term_weight

	locations = set(location_worth.keys())
	
	# This could happen if the user just enters metadata or such, just give the
	# initial part of the document.
	if len(locations) == 0:
		locations = set([0])
		location_worth = {0:1}

	# Search over the range, looking for the subset of terms that has the greatest
	# value of its enclosed terms.
	best_starting_pos = min(locations)
	best_range_score = 0

	for i in range(min(locations), (max(locations) - summary_length) + 1):
		range_score = 0
	
		for j in range(summary_length):
			if i + j in locations:
				range_score += location_worth[i + j]
	
		if range_score > best_range_score:
			best_range_score = range_score
			best_starting_pos = i
		
	return database.reconstruct_partial_document(document_id, best_starting_pos, best_starting_pos + summary_length)


def bold_summary(querystring, summary, prefix_str="<b>", suffix_str="</b>"):
	''' Bolds the portions of the querystring that are found in the summary
	by breaking down the querystring and summary to individual words, applying 
	the prefix_str before, and the suffix_str after.

	'''

	queryterms = query_parser.word_only_tokenize(querystring)
	summary    = query_parser.word_only_tokenize(summary)

	for i in range(len(summary)):
		if summary[i] in queryterms:
			summary[i] = "%s%s%s" % (prefix_str, summary[i], suffix_str)

	return " ".join(summary)

