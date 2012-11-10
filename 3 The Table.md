The Table
=========

Introduction
------------

Search engines are really fast at finding documents that have the terms you 
specify, they do this by storing those terms and the documents in something that
is referred to as an **inverted index**.

A normal document exists in a folder and has words (terms) inside of it, when
you want a particular document, you know how to get to it based upon its 
location and name:

	Location -> Document -> Term
	
But what happens when you don't know which document you want, but instead know
the content you want? This is where inverted indexes come in, rather than 
storing words in documents, they store documents in words, that is, you can 
look up a word, and find all documents that have that word.

	Term -> Document -> Location

Searching for something this way becomes monumentally faster than looking 
through every document in your collection (and they can get quite large, just
look at Google) for the word you want.


Methods to the Madness of Inversion
-----------------------------------

The biggest difference between search solutions is the way they structure their
inverted indexes.

Google use(s|d) a technology called **BigTable**, a single table that is spread 
across thousands of simple servers, lookups consist(ed) of putting in
a row and column, and getting the result stored in one of the nodes.

This method works well when the database needs to scale up to a high load and 
the interconnections between nodes is very fast (Google owns it's own fiber
between their data-centers, and there is compelling evidence they even custom
build [every part of their network](http://www.wired.com/wiredenterprise/2012/09/pluto-switch/).)

An [alternative method](http://dev.mysql.com/doc/refman/5.0/en/fulltext-search.html)
, used by MySQL tables is to simply produce a table of term document mappings, 
and document location mappings. This is a similar method to how 
[SQLite accomplishes the goal](http://www.sqlite.org/fts3.html). It is the 
method we'll use for this book because it doesn't litter your system with stuff,
and is fast enough for our purposes.

Yet another method, used by [Xapian](http://xapian.org/) and the 
[normal Lucene back-end](http://lucene.apache.org/core/old_versioned_docs/versions/3_0_3/fileformats.html), 
is to use a flat-file structure. In such structures, you'd have a folder, a file
for one or more terms, within that file would be the list of documents that
the term was found in.


Implementation Details
----------------------

Our index will be a simple database using SQLite as the database manager. 
There are a few advantages of using a SQLite database as the backend
over flat files:

*	The database can be opened instantly without being loaded in to
	memory.
*	The need to mark things as "dirty" is less, because deletes will
	cascade throughout the database.
*	Only one file is stored on disk, making it less likely that one of
	them will go missing and become corrupt.

However there are disatvantages as well.

*	SQLite has trouble with huge sets of data.
*	Due to the internal structures, the SQLite data files may be much larger than their flat-file counterparts.

![A UML diagram of the SQL database layout](https://raw.github.com/joehms22/fts-book/master/Illustrations/sqlite_database.png)

The database is comprised of three main tables `documents`, `terms` and
`metadata_dict`.

The `documents` table holds the uri of the indexed document, whether or not a 
newer version is available in `dirty` and the time the document was indexed 
in `time`.

The `metadata_dict` table just keeps a record of key->value relationships for 
metadata, and assigns each of these an index. This way, we don't duplicate
common metadata (like filetypes potentially millions of times).

The `terms` table simply matches a _term_ with a unique id, which can
then be looked up in the `term_document_map` table if you wanted to find
all documents with a given term.

Now we're left with only two helper tables. `metadata_document_map`
maps specific `metadata_dict`s with particular documents, so finding
documents with a particular map should be fast, due to indexing.

The other helper table is `term_doc_location` which matches the
location of a specific term in a certain document, thus if you looked up
all terms for one document, you could "reconstruct" that document.


Implementation Methods
----------------------

The following methods are used to create the main class that houses the 
database. All actual code has been cut out leaving just parameters and the word
"self", which is included in all class methods in Python. Extra notes are below
methods that aren't completely straightforward to implement describing their
implementation (a guide to you if you want to write the code yourself). 
Otherwise, all of the code is available in the "sqlite_database.py" file.


This is by far the largest piece of code in the whole software, but it is
justified, because everything else depends upon this bit.


	__init__(self)
	    Opens a connection to the database, or if it doesn't exist yet, 
	    creates the database.

This method is called when the class is constructed. It creates the tables using
`IF NOT EXISTS` SQL statements so they'll only be created if not already done.
If you decide to create a flat file database (where each term has its own file
with a list of words, it would be a good place to check if they all exist).
	
	add_document(self, doc)
	    Adds the given document to the database, deleting any documents
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



	contains_phrase(self, phrase, document_id)
	    True if the document contains the given phrase, False otherwise.
	    
	    Params:
	            phrase - (string[]) an array of words that constitute the phrase.
	            document_id - (integer) the id of the document to look for the 
	                                                            phrase in.

This is an interesting algorithm to implement. The implementation in this book 
takes the following process: Within the document, look for all locations of the 
first term in the phrase, these are potential places for the beginning of the
phrase, if there are none, return false. If there are some, save them, but only
those with indexes greater than or equal to 0 (eliminating spellchecked and
metadata words).

For each word after the initial, 1) look up locations for that word in the 
document. 2) For each of those locations, check to see if it one more than any
of the previous word's locations (meaning it comes right after). 3a) Save each of
these matching locations and go to the next word. 3b) If there are no matching,
it means the phrase isn't there, so return false rather than continue looking
up the rest of the words. 

If you get to the end of the words you're searching for, and you haven't 
returned false yet, you've found at least one match!

	count_documents(self)
	    Returns the total number of documents in the index.


	documents_with_phrase(self, phrase)
	    Returns a list of documents that contain the given phrase.
	    
	    Params:
	            phrase - (string[]) an array of words that constitute the phrase.

This method looks for all documents with the first term in the phrase, and calls
contains_phrase on them, returning the matches.
	
	find_documents_for_metadata(self, key, value)
	    Returns a list of document ids such that they have the given key
	    and value in metadata. If no such metadata exists, an empty list
	    will be returned.
	    
	    Params:
	            key             - (string) The key of the metadata to search for.
	            value   - (string) The value of the metadata to search for.


	find_documents_for_term(self, term)
	    Returns a list of all documents that have the given term in them.
	    
	    Params:
	            term - (string) the term to search for.


	find_metadata_for_document(self, docid)
	    Finds the key->values of the metadata for the given document.
	    
	    Params:
	            docid - (integer) The id of the document to fetch metadata for.
	    
	    Returns:
	            A key->value map for the metadata associated with the document.


	frequency(self, document_id, term)
	    Returns the frequency of a term in a particular document.
	    Returns 0 if the term is not present in the document, or the document
	    doesn't exist.
	    
	    Params:
	            document_id - (integer) The id of the document to look for the term
	                                            frequency in.
	            term - (string) The term to look for in the document.


	get_document_uri(self, docid)
	    Returns the uri for the document with the given id. If no document 
	    exists, returns a blank string.
	    
	    Params:
	            docid - (integer) The id of the document to fetch the URI for.


	get_term_locations(self, term, document_id)
	    Returns an array of the locations of the given term in the given
	    document.
	    
	    Params:
	            term            - a string that represents the term to be searched for.
	            document_id - the id of the document to search for


	id_to_term(self, term_id)
	    Returns the term text from the given term id or None if no term id 
	    is given.
	    
	    Example:
	            > id_to_term(85)
	            "wolf"
	    
	    Params:
	            term_id - (integer) The id of the term to return the value for.


	reconstruct_document(self, doc_id)
	    Takes the given document, and reports all the terms in it, in order,
	    back as a string. If no such document exists, return an empty string.
	    
	    Example:
	            If document 0 was originally indexed as "the quick red fox"
	            
	            > reconstruct_document(0)
	            "the quick red fox"
	            
	            > reconstruct_document(-999999) # doesn't exist
	            ""
	    
	    Params:
	            doc_id - The id of the document to look for the string in


	reconstruct_partial_document(self, doc_id, termstart, termend)
	    Takes the given document, and returns the terms from termstart to
	    termend that were found in that document. If there are no terms within
	    the given range, an empty string is returned.
	    
	    Example:
	            If document 0 was originally indexed as "the quick red fox"
	            
	            > reconstruct_partial_document(0, 1, 2)
	            "quick red"
	            
	            > reconstruct_partial_document(0, 50, 100)
	            ""
	    
	    Params:
	            doc_id          - The id of the document to look for the string in.
	            termstart       - The first word to include in the reconstruction.
	            termend         - The last word to include in the reconstruction.


	shutdown(self)
	    A method that is called before the whole software quits. The 
	    database is saved and closed during this call.


	total_frequency(self, term)
	    Returns the total number of times a particular term was found
	    in the index.
	    
	    Params:
	            term - (string) the term to fetch the frequency for.




Software Design
---------------

Fourtinately, Python has built-in support for SQLIte on all of it's
platforms that run the C built interpreter, so including it is a
non-issue, as any user that has a standard distribution installed will
be able to run the software.

Because I added primary key constraints and indexing to the example
database, speed should be fast, even if the whole thing isn't pulled in to
 memory by the SQLite runtime.

The database will also accept requests for documents using a simple query field:

	http://localhost:33335/search?q=<QUERYTEXT>
	
This is a similar query mechanism to Bing, Google, and Yahoo! the q followed by
a question mark is what allows Firefox to use all of them as search providers.

Being that writing an HTTP server is beyond the scope of these documents, I'll
include one that I wrote previously.


Advanced Topics
===============

As with all advanced topics sections, read on if you want more information on 
current systems.

Secondary Concerns
------------------

**Instant Indexing**

Let's assume you have an inverted index, and you wish to include all Twitter 
posts and have software looking for general shifts in words to obtain a picture
about how the world is feeling today. (Not so far fetched when you think of it
from a security perspective.)

The problem is that there are two parts to any inverted index, the part that
inputs the data, and the part that reads it:

* In order to be fast, the part that reads it stores it in memory.
* In order to be persistent, the part that writes to it stores it on disk.

You don't want to force a reload *every* time an inverted index is updated, as
that would defeat the whole purpose of having it stored in memory. This may work
if you update twice a day, but Twitter posts come with milliseconds between them
. If you wait to update the entire purpose of the Twitter generalizer is lost, 
as you want to know trending feelings, not yesterday's.

This requires another structure to sit atop the database. A mechanism that can
be written to so the most updated data can be available and is searched
alongside that which is already in the database.


**Work**

The database is the slow point of the whole operation, and thus it should avoid
doing as much work as possible. If you never want to re-construct documents, 
the indexes of the words should not be stored, if approximations are okay, you
should stem words.

One common feature of FTS engines is to stop indexing after a certain number of
bytes has been reached, this keeps large data sets, like CSVs that could range
in to the gigabytes from ruining the database.

**Spellcheck**

You may wish to use your database as the source for your spellcheck dictionary,
those words that appear most are (hopefully) spelled correctly, and can thus 
be given the weight when you are looking for words to replace with.

If you modify the spelling checker given earlier to incorporate the text of the
database, it will have the added benefit of accommodating any new language you 
run across, or even nonsensical documents.
