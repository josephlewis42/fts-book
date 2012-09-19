Introduction
============

This digital book is being written as a project for an independent
study course that the author is taking at the University of Denver.

The book will cover the following topics and include one or more 
implementations. Each section of the book has two sub-sections, one
describing the theory behind the topic, and the other describing the
implementation that the book chooses to make and justifications for
that.

If you follow along, and write/compile the code given, at the end of 
the book, you should have a minimal Full Text Search engine that can
be paired with something like Tika to build a desktop search engine, 
a spider to index a site, or simply be embedded in an application that
you choose to use it with.

Most of the code will be written in Python due to portability, clarity,
ease of maintenance, and development speed.

Topics
======
1. Input
	The most important part of the system, a way to take input so
	the engine can do its thing.
	* Parser
	* Lexer
	* Normalizer
	* Stemmer

1. Storage techniques and design
	 These are the data structures needed for an inverted index, 
	serialization and deserialization
	* a full text index storage/retrieval engine

1. More to come as they are written...
