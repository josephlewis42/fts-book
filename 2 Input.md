Input
=====

Terminology
-----------
* document
	Any object that is being indexed, files, email-messages, videos, and social
	media posts are all documents.
	
* word
	Any one bit of information that is representable by characters, and is 
	separated by whitespace, literal words and groups of numbers are both 
	handled.

Tokenizing
----------

To even begin describing full-text-searches, indexing, parsing, lexing,
querying etc. We must first understand, fundamentally, what a full-text
search engine is, so the design makes sense.

In this context, we'll describe a full-text engine as a file, that looks
up documents based upon words, rather than the other way around; the 
thing that most documents do. This type of system is commonly called an
_inverted index_, due to this reversing of roles. In this way, an inverted
index may be modeled by a simple map or dictionary if documents are as
follows:

**whale_report.txt**

	I like whales. Whales are great because they are big.

 
**moby_dick.epub**

	Chief among these motives was the overwhelming idea of the great whale himself.

**Names.csv**

	Name,Age,Profession
	John Smith, 45, Whale Expert
	John Galt, ??, 2nd Asst. Bookkeeper

An index, in it's simplest form, would comprise of a series of documents, each 
named after the word they were indexing, containing a list of files that had
the given word.

**whale.index**

	moby_dick.epub
	Names.csv

**john.index**

	Names.csv

**great.index**

	moby_dick.epub
	whale_report.epub

...and so on.

Here is a simple python script which archives these ends:

	#!/usr/bin/env python
	import re

	def parse_document(doc):
		'''Parses a document in to a list of strings.'''
		doc = doc.lower
		doc = re.sub(r'[^\w\s]+', '', doc)
		return doc.split()

You may notice something interesting done here, rather than just splitting along 
whitespace, we included something called _normalization_, meaning the text
was normalized to a standard before being processed, all words were made lowercase
and anything not a character or whitespace was stripped.

Stemming
--------
"Wait!" you may exclaim, "Why does _whale.index_ not have the report on whales?" Well, the 
report only includes the word "whales", but never "whale". This can be
fixed through the process of "stemming". In stemming, we modify source words so they match the
original root of the word being searched, thus:

        whales -> whale
        whaling -> whale
        whaled -> whale
        man-whale -> man + whale

There are [several different algorithms](http://en.wikipedia.org/wiki/Stemming#Algorithms)
 for accomplishing this, the one we are going to implement is suffix 
stripping, as it is the simplest, it works by removing the common 
suffixes to words, like ing, ed, or ly. Of course, this will only work
for English, but stemming algorithms must be fine-tuned to a specific
language due to the inherent structural differences between them.
[Here is a page featuring stemmers](http://snowball.tartarus.org/) for other languages.

	#!/usr/bin/env python
	
	def stemmer(word):
		''' A simple stemmer for English. '''
		for suffix in ["ing","ly","ed"]:
			if word.endswith(suffix):
				return word[:- len(suffix)]
		return word

The advantages of using such a simple stemmer is chiefly speed and
maintainability. 
There is no need to look up a particular word, which would mean 
leaving a rather large table in-memory, and we can optimize the heck
out of these eight lines of code to ensure they are fast.

Of course, it isn't without its disadvantages, words like "whaling" won't come
out right, and strange words like "went" won't properly map to "go" where goed 
would be expected. It is times like this where [Esperanto](http://en.wikipedia.org/wiki/Esperanto) 
starts to look very pretty indeed.

One possible solution is to spell-check each of the generated words before
inserting it in to the index. This is highly important, as even words that
are used as input, cannot be guaranteed to be correct (after all, everything
was at one time input by a human). A simple (but slow) implementation of a
spellchecking algorithm can be found [here](http://norvig.com/spell-correct.html).

Spellchecking can also eliminate regional differences in spelling e.g. UK vs US
English, which would prevent all possible results of "colouring book" from
showing up if done improperly.

The disadvantage of using spellchecking is the likelihood of getting something 
wrong, for example, say you have a species named _Balloonus highus_ describing
a jellyfish that floated in air and wanted to add a journal article highlighting
this amazing species to your index, the spellchecker would likely change those
in to "balloon" and "high", and nobody would ever find your article. 

It is therefore important to take in to account the probability that the word
you have is correct. Alternatively, you could associate both correct and 
incorrect word with the document. This would make searches of Shakespearean
sonnets just as easy as more common text, but also raise the amount of data
you need to store about each document making larger and slower indexes; we'll 
discuss that more in the next chapter.

Another consideration that could be made is a context-sensitive spellcheck or
word replacement algorithm. If everything you want to search comes from a 
particular domain, such as [Twitter](http://twitter.com), where message length 
is at a premium, "words" like "4ever" would need to be accounted for.

Conversely, you also need to take account of what your users will be searching
for, English professors familiar with Shakespeare will undoubtedly feel 
obligated to use the middle English spellings, while students would not, this
will be discussed further in "Querying the index".

Wrapping it Up (In to Documents)
--------------------------------

All together we need a format to represent a document that can be portable and
communicated from one system to another:


	#!/usr/bin/env python

	'''
	Called like so:
	>>>	import document
	>>>	 d = document.Document(open('tests/incorrect_spelling'), 'file://tests/incorrect_spelling')
	'''

	import spell_checker
	import parser
	import json
	import collections

	class Document:
		# full text of the document
		full_text_words = None

		# full text of the document, run through the spelling correction
		# algorithm
		spelling_corrected = None

		# frequency of words found in the document
		word_frequency_map = None
	
	
		def get_word_locations(self):
			model = collections.defaultdict(lambda: [])
			for i in range(len(self.full_text_words)):
				model[self.full_text_words[i]].append(i)
			
			for word in self.spelling_corrected:
				model[word].append(-1)
		
			return model


		def __init__(self, fd, uri, metadatadict={}):
			''' Indexes/normalizes a document.'''

			self.metadata = metadatadict
			self.uri = uri
			self.full_text_words = parser.parse_document(fd.read())
			sc = spell_checker.Checker()

			self.word_frequency_map = sc.get_doc_dict(self.full_text_words)

			# Add in all of the words we don't know about
			self.spelling_corrected = []
			for word in self.full_text_words:
				new_word = sc.check_word(word, self.word_frequency_map)
			
				if new_word != word:
					self.spelling_corrected.append(new_word)

		def __str__(self):
			return " ".join(self.full_text_words)

		def dump_json(self):
			return json.dumps({"words_map" : self.get_word_locations(),
								"uri" : self.uri,
								"metadata" : self.metadata})


This "document" object takes in a file handle and parses the text that comes
out of it. That text, once processed can be encoded in JSON and sent to the 
database.

The JSON output will have a "words_map" which is a map of a string to an array
of locations the word was found in, the URI of the document, and a string->string
dictionary with all metadata (assumed to have been processed before creating
the document).

Deficiencies
------------

There are still obvious deficiencies in this part of the software. 

How does it...
* get the documents?
* parse the documents?
* save the documents?

The first two are the jobs of other pieces of code we won't cover, like spiders,
that fetch web pages, or utilities like "file" that read metadata from a file, 
or text converters that extract text from files like PDFs.
