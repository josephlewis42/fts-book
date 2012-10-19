Query Parsing
=============

![Hi Randall!](https://raw.github.com/joehms22/fts-book/master/Illustrations/exploits_of_a_mom.png)

[Credit: xkcd](http://xkcd.com/327/)

Introduction
------------
In this section, I'll describe one way to implement the Query Parser,
but first, an aside on common query conventions:

Search has come a long way from pages like these:

![A very bad search interface from Web Of Science](https://raw.github.com/joehms22/fts-book/master/Illustrations/web_of_science.png)

This is much due to a change in the way queries are performed on the
backend. Rather than constructing SQL queries for search *databases*
based upon the given terms as is probably happening here, modern search
*engines* have a different approach that allows special characters to
instruct the search engine what you want.

Note that traditional database lookups wouldn't mean much for the
inverted index backends we've built because there are no fields to do
queries on.

When we perform queries on a full text index system, not only does the
old query mechanism become cumbersome, but it gets to be replaced by
something more natural...simply asking for what you want.

Traditional FTS systems suport the following types of queries:

	+	An and, both preceeding and following words must be in the given
		document.

	-	The following word/phrase cannot be in the document

	"	The phrase within the quotes must be in the document exactly

	key:val	The document must have the metadata given associated with it

In combination these queries allow us to create complex searches that
are really quite natural, say you remembered some words:

	To be or not to be

and that they were in some old English guy's piece of literature:

	English, literature, not a song

The query you'd search would be something like this:

	"To be or not to be" English+literature -song

Of course this would work as well:

	to be or not to be english literature

The formal definition for this search _language_ that we'll implement is
this:

	QUERY	= NOTBOOL (,NOTBOOL)*
	NOTBOOL = (-) ANDBOOL
	ANDBOOL = META+ANDBOOL | META
	META	= WORD:WORD  | STRING
	STRING  = "PHRASE" | WORD
	PHRASE  = WORD(, WORD)*
	WORD	= CHAR (, CHAR)*
	CHAR 	= A-Za-z0-9

