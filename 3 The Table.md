The Table
=========

Introduction
------------

Generally, search engines store their information in what is refered to as an 
**inverted index**, this means that the structure is the reverse of normal documents
that look like this:

	Location -> Document -> Term
	
Inverted indexes look roughly like this:

	Term -> Document -> Location

This allows rapid search because the searcher rarely looks for a single document
, that is what bookmarks and file systems are for, but rather for terms within a
number of documents and want to narrow those down to the one she needs--or in a
research context, the most relevant one.

The biggest difference between search solutions is the way they structure their
inverted indexes.

Google use(s|d) a technology called **BigTable**, a single table that could be 
spread across thousands of commodity machines, lookups consist(ed) of putting in
a row and column, and getting the result stored in one of the nodes.

This method works well when the database needs to scale up to a high load and 
the interconnections between nodes is very fast (Google owns it's own fiber
between their data-centers, and there is compelling evidence they even 
[build their own networking switches](http://www.wired.com/wiredenterprise/2012/09/pluto-switch/)
.)

An [alternative method](http://dev.mysql.com/doc/refman/5.0/en/fulltext-search.html)
, used by MySQL tables is to simply produce a table of term document mappings, 
and document location mappings. This is a similar method to how 
[SQLite accomplishes the goal](http://www.sqlite.org/fts3.html).

Yet another method, used by [Xapian](http://xapian.org/) and the 
[normal Lucene back-end](http://lucene.apache.org/core/old_versioned_docs/versions/3_0_3/fileformats.html), 
is to use a flat-file structure. How the files are structured are really up to
the back-end, although most Lucene versions have compatible outputs, so if you
use the C Lucene you won't have to re-index if you switch to Java.

The benefits of using a flat file versus a table come in the form of when 
re-indexing occurs. The flat file is easier to parse, edit, and load entirely
in to memory/swap out than an entire database.

When indexing huge numbers of documents, more common words will accumulate more
than uncommon ones, thus those files can be split, merged, and garbage can be
collected without locking the whole system if you go with a flat-file method.

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


**Metadata**

As a hypothetical example, let's say you've built an index full of historical
software, and included it all: OS2/Warp, BeOS, Palm, Apple][, and Tandy 102. (Of
course you've already obtained permission from each of the original authors 
before posting any of it...)

How would someone find only software for their Palm Pilot? If you're familiar
with Google, the command would be something like this:

	space trader platform:palm
	
Where platform would be one of a series of available platforms. This is metadata
and it comes in handy often, like when you want to search for pictures over a
certain size, or want to limit the shoes you're looking at to a size ten.

For this, we need another index in our database/flatfile format, one to look up
the metadata key, "platform" in our example, the type of platform and the
documents that have the platform in them:

	platform -> palm -> document

**Work**

The database is the slow point of the whole operation, and thus it should avoid
doing as much work as possible. If you never want to re-construct documents, 
the indexes of the words should not be stored, if approximations are okay, you
should stem words.
