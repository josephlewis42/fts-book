Ranking
=======

	  +-----------------+
	  |Client           |
	  +--^--------+-----+
		 |        |
		 |  +-----v-----+
		 |  |Webserver  +---------------------+
		 |  +-----------+                     |
		 |              |                     |
		 |       +------v--------+     +------v---------+
		 |       |Query Parser   |     |Document Parser |
		 |       |               |     |(spellcheck too)|
		 |       +-------+-------+     +-------+--------+
		 |               |                     |
		 |       +-------v-------+             |
		 |       |Database       <-------------+
		 |       +-------+-------+
		 |               |
		 |               |
		 |       +-------v-------+
		 |       |Ranking        |
		 +-------+(Building Now!)|
				 +---------------+

Introduction
------------
In this section, we'll build the mechanism for **ranking** i.e. deciding which
results are more important, and should be shown first. Just because a document
has a word, doesn't mean it is what the user was looking for, imagine if your
search engine looked over a website that had a file containing a list of all the
words known in the English language, while this may be interesting it would 
probably not be what the person searching would want to show up first in *every*
search result.

One of the most famous ranking algorithms is [PageRank](http://infolab.stanford.edu/pub/papers/google.pdf), 
developed at Stanford by [Larry Page](http://en.wikipedia.org/wiki/Larry_Page), 
one of the co-founders of [Google](https://www.google.com). PageRank works by 
counting the references from one page to another, say site A links to site B, 
and site C links to site B and A, then A has one link, B two, and C zero. Under
this scheme site B would appear first in relevant searches because it has more 
links and thus appears to be a more useful resource. One downfall of this 
algorithm is that it can be tricked by sites that just serve up pages filled 
with useless links; prompting Google to create new algorithms like 
[Penguin](http://en.wikipedia.org/wiki/Google_Penguin) and
[Panda](http://en.wikipedia.org/wiki/Google_Panda).


Our Ranking Algorithm
---------------------

Ranking based upon links from one place to another is fantastic, if you can 
salvage the links, however this isn't always possible, especially in places like
the Desktop, where documents don't actually have links. In this case we'll do 
ranking by the use of specialized keywords; i.e. the documents with more 
specialized terms and a greater number of these terms will recieve a greater
weight.

For instance, if you entered the query "to be or not to be Shakespeare" the word
Shakespeare would take precidence, as thousands of other documents undoubtedly
have some combination of "to", "be", "or", and "not". The equation for doing
this is quite simple:

	TermDocumentWeight = Td * (1 / Ta)
	
	Td - Number of times the term is in the document
	Ta - Number of times the term is in the whole database

Then to get the score of an entire document, you'd sum all of the 
TermDocumentWeights for all of the searched terms.

In our application, we'll call `rank_documents` with the query the user entered, 
the list of applicable documents we got from the query parser, and a copy of our
database, so the ranker can look up frequencies.

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


Summary Generation
------------------

This ranking is not only good for ranking documents, but also generating the
small blurbs of text generally found below a result. By stepping through the 
whole document, word by word, with the length of the blurb you want you can 
add together the weight of the given substring in the document, choosing the
highest value as the one to show:

Here is an example of

	Query: The Red Fox
	Length: 3

	Document:	The Quick Red Fox Jumped Over The Lazy Black Dog
	Weight:		.5  1     1   1   1      1    .5  1    1     1
		1.5		The Quick Red
		2		    Quick Red Fox
		2		          Red Fox Jumped
		1		              Fox Jumped Over
		.5		                  Jumped Over The
		.5		                         Over The Lazy
		.5		                              The Lazy Black
		0		                                  Lazy Black Dog

In this example, the first substring searched would seem like a prime candidate
for showing, because it has two of the three words, but we note that the word 
"the" has a lower weight than the winning substring (either the second or third).

But to be even more efficient, we don't have to search the whole document each 
time, but rather simply the words the user searched for in the query. Once you 
know the positions of those, and their weight, you can step through calculating
the subset of the document with the highest weight and then look for all the 
rest of the words inside that subset to return to the user.

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

Marking Terms
-------------

Generally, search engines will mark the terms that the user has searched in
these short summaries so they are easier to spot for the user who is scanning 
for the best result, this can be achieved using the following chunk of code:

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
		

Full Code for `ranker.py`
-------------------------
	
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

