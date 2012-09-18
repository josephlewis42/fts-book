Input
=====

Theory
------

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
	I like whales. Whales are great because...

 
**moby_dick.epub**
	Chief among these motives was the overwhelming idea of the great whale himself.

**Names.csv**
	Name,Age,Profession
	John Smith, 45, Whale Expert
	John Galt, ??, 2nd Asst. Bookkeeper

An index, in it's simplest form, would comprise of a series of documents, each 
named after the word they were indexing, containing a list of files that had
the given word.

whale.index
	whale_report.txt
	moby_dic.epub
	Names.csv
john.index
	Names.csv
great.index
	moby_dick.epub
	whale_report.epub
