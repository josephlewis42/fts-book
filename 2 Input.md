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




Deficiencies
------------

There are still obvious deficiencies in this part of the software. 

How does it...
* get the documents?
* parse the documents?
* save the documents?

The first two are the jobs of other pieces of code we won't cover, like spiders,
that fetch web pages, or utilities like "file" that read metadata from a file, 
or text converters that extract text from it.
