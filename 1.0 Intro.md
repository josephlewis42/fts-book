How to Build a Search Engine
============================


![The final product](https://raw.github.com/joehms22/fts-book/master/Illustrations/lovelace_search_final_product.png)

The final product.


Introduction
============

Over the past ten years the amount of digitized information available online has
grown at a breakneck speed. In order to properly sort through all of that 
information, people have come to use increasingly sophisticated search engines 
that have transitioned from being simple databases to something else entirely, 
full text indexes that use a reversed document structure for locating things. 

These indexes have allowed the fast and seemingly magical search ability we have
come to expect; no longer do users need to enter an exact term, precariously 
choosing ANDs and ORs from drop-downs to craft the perfect search. Instead, a 
simpler interface has overtaken the web, a single text-box and button.

This course was designed to demonstrate that it doesn't take years of study to 
be able to create a well-working full text index that can compete with much 
better funded competitors, such as the big search engine companies; rather it 
takes a little bit of insight in to how reversing the way we look at documents 
allows all of this to happen with a little code implementing conceptually 
simple algorithms. This book covers building and joining together the following
components:

* lexer
* parser
* indexer 
* database storage mechanism
* spell checker
* query interpreter
* ranker
* web server
* spider

The end result is a simple full text search engine that is efficient and compact; 
that has a surprising ability to do complex queries, easily lending itself to 
real-world applications.

Prerequisites
=============

This book is intended for intermediate level programmers, basic knowledge of 
lists, maps, and string manipulation is assumed. Some knowledge of Python would
be useful for reading the examples, however it is syntactically similar to 
Pseudocode, and thus not strictly necessary. Knowledge of file streams and
regular expressions will be very handy.

No knowledge in language-design, web servers, or databases is required.


How To Read This Book
=====================

While the source of this book is available for download, you are encouraged to
try and implement it in the programming language of your choice (and if you want
send the results back to me for inclusion in that language, if you desire, I'll
even include your source as another implementation; but if not, I'd love to have
it anyway.)


High Level Overview of Searching
================================

	 +------+        +------------+        +------+          +---------+
	 |Search+------->|Query Parser+------->|Ranker+--------->|Generator|
	 +------+        +------------+        +------+          +---------+

When you visit a search engine and look for something, your particular search
goes through the following mechanisms, briefly described below:

Query Parser
------------

The query parser looks at your input, and figures out what exactly you want to 
search for. Many times, like when you just put in words, this is a simple matter
of taking those words, splitting them apart, and looking up the matching 
documents.

The magic of this level comes in when you want to do more complex things, like
look for documents containing an exact phrase, two particular words, or that are
videos instead of text.

Ranker
------

The ranker takes the results of the Query Parser and decides how relevant they 
are to your search.

Generator
---------

The generator takes all of this information and creates results that a user 
could comprehend. Its role is that of sorting the ranked documents, choosing
the text the user will see along with those documents, deciding whether or not
the user made a spelling mistake in their query, and suggesting other, related
searches.

Once the generator is done, it returns the results to the user.


High Level Overview of Indexing
===============================

	+--------+    +---------+      +----------+      +-------------+     +-------+
	| Spider +--->|Extractor+----->|Normalizer+----->|Spell Checker+---->|Indexer|
	+--------+    +---------+      +----------+      +-------------+     +-------+

Indexing is the process by which documents are added to the database, the 
spider and extractor are projects not covered by this book, although the sources
are provided for them.

Spider
------

The spider is a program that looks for new documents to add to the search 
engine's index (it's database). It can look for files on a local machine, this
is how the search engines work when you look for a file on your computer; the 
web, like Google or Yahoo!; or even a restricted domain, like a single website
or intranet.

Spiders get their name because they "crawl" the web. They're also sometimes 
called bots.

Extractor
---------

The extractor takes the documents the spider finds and takes the pure text out
of them, as well as the metadata.

Normalizer
----------

The normalizer takes all of the data that the extractor has, and makes sure
that it is fit to put in the index. Common things it does are remove punctuation,
make all words lowercase (so when you search "George" it will also give you the
results for "george" and even "gEorge"), and stem words.

Stemming words is a way to find the roots of words and only store those,
therefore when you use "fishing", "fished" in a document, it would appear when
a user typed in "fish". This also cuts down on the number of things your index
has to store; however it is very difficult to do with irregular languages like
English because words like "went" wouldn't map to "go" without lots of rules
that would slow down the whole process.

This book provides a section and implementation of a stemmer, but the final 
search engine won't use it.

Spell Checker
-------------

The spell checker is a mechanism that finds likely misspellings and fixes them
in the text, allowing your users to better find documents with consistent
misspellings.

It is debatable whether or not spell checkers should even be run against
documents, as the quality of the documents with misspelled words may be low 
enough such that they are irrelevant to searches.

Indexer
-------

The indexer is the final step in document indexing. It takes the normalized
document and stores it on the drive in a way that is fast to look up. It 
encompasses a lexer that breaks the document down in to indiviaual words.
