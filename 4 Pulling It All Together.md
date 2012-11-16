Pulling It All Together
=======================

Introduction
------------
In this section, we'll take all of the software made so far, and combine
it together to make a webserver that can get a query, and return a list
of documents that contain the words in that query, as well as input
new documents.

The overall process looks something like this:

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
		 |       |(not built yet)|     |(spellcheck too)|
		 |       +-------+-------+     +-------+--------+
		 |               |                     |
		 |       +-------v-------+             |
		 |       |Database       <-------------+
		 |       +-------+-------+
		 |               |
		 |               |
		 |       +-------v-------+
		 |       |Ranking        |
		 +-------+(not built yet)|
				 +---------------+

The client will send a request to the webserver, either a `GET` or
`POST`. If the client does a `GET`, i.e. a standard web request, they
should also pass along a query like `?q=hello world`, this will then
be passed on to the *query parser* which will look up the terms in the
database, and pass the results to a ranking algorithm, which will decide
that documents are most relevant to the user's request.

If the client does a `POST` request, we'll assume that they are
submitting a new document to be indexed. It is their responsability to
make sure the document arrives in a plain text format before it is
parsed.

As example documents, I have fetched the first one-hundred documents
that were archived as part of [Project Gutenberg](http://www.gutenberg.org/).
I have removed the open source headers from each of these as is possible
under the license provided, otherwise each document would have a large
amount of the same text.


POSTing Guidelines
------------------

For the server to work, the following posting guidelines must be adhered
to.

*	POSTs must only contain one file, if more than one is
	found, the last definition is kept.
*	To submit a document with a different URI than the default (the
	uploaded file name) use a field with the name `uri`
*	All other form elements submitted will become metadata key->value
	pairs associated with the document.

Implementation
--------------

We won't go through the *whole* server implementation here, just the part that
parses the documents you upload (a full review will be later). The source is 
available in `lovelace.py`

The `do_POST` method first finds all of the data that was sent to it and saves
it in a form:

	def do_POST(self):
		# Parse the form data posted
		form = cgi.FieldStorage(
			fp=self.rfile, 
			headers=self.headers,
			environ={'REQUEST_METHOD':'POST',
					 'CONTENT_TYPE':self.headers['Content-Type'],})
	
		document_text = None
		document_name = None
		metadata = {}

Next, it loops through all of the form items, and sets up a map for field names 
and items.

		field_items = {}
		for field in form.keys():
			if isinstance(form[field],  cgi.FieldStorage):
				field_items[field] = form[field]
			else:
				field_items[field] = form[field][0]

After finding all form items, try to set them up as either metadata, or the 
uploaded document itself.
		
		for field, field_item in field_items.items():
			try:
				if field_item.filename:
					# The field contains an uploaded file
					document_text = field_item.file
					document_name = field_item.filename
				else:
					# Regular form value
					metadata[field] = field_item.value
			except AttributeError:
				metadata[field] = field_item.value

Next, we try to set the URI: if one was uploaded with the key 'URI' use that, 
otherwise use the file name that came with the document.
	
		try:
			document_uri = metadata['uri']
		except KeyError:
			document_uri = document_name

Next, we'll create a document and add it to the database, then send back whether
it worked or not.
	
		doc = document.Document(document_text, document_uri, metadata)
		self.show_page("Success!" if ffd.add_document(doc) else "Failure")
