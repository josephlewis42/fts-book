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

*	POSTs must only contain more than one file, if more than one is
	found, the last definition is kept.
*	To submit a document with a different URI than the default (the
	uploaded file name) use a field with the name `uri`
*	All other form elements submitted will become metadata key->value
	pairs associated with the document.


Server Implementation
---------------------

This server will spawn a new thread for ever post, and will commit the
results upon shutdown.

	from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
	from SocketServer import ThreadingMixIn
	import threading
	import cgi
	import flat_file_database
	import document

	ffd = flat_file_database.FlatFile() # could also be the SQLite database.

	class Handler(BaseHTTPRequestHandler):
		'''A new Handler will be spawned for each connection.'''
	
		def do_GET(self):
			''' If the client does a GET request, i.e. the one you'd do by typing in
			http://localhost:33335/?q=hello%20world this function will be called.
			'''
		
			# Turn the query string (the part of the url after the ? mark, in to a
			# map.
			qs = {}
			if self.path.find('?') > -1:
				qs = self.path.split('?',1)[1]
				qs = cgi.parse_qs(qs, keep_blank_values=1)
		
			# Try forming a message based upon the query, in this simple example,
			# we'll just output an array for documents containing the given term.
			try:
				message = []
				for query in qs['q'][0].split():
					message.append( ffd.find_documents_for_term(query))
				message = str(message)
			except Exception:
				message = "no query string"
		
			# Send the client the 200, OK http response, as ?q should never 404.
			self.send_response(200)
			self.end_headers()
		
			# Send the client the message, terminated by a newline.
			self.wfile.write(message)
			self.wfile.write('\n')	
			return
		
		def do_POST(self):
			# Parse the form data posted
			form = cgi.FieldStorage(
				fp=self.rfile, 
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
						 'CONTENT_TYPE':self.headers['Content-Type'],})

			# Begin the response
			self.send_response(200)
			self.end_headers()
		
		
			document_text = None
			document_name = None
			metadata = {}

			# Echo back information about what was posted in the form
			for field in form.keys():
				field_item = form[field]
				if field_item.filename:
					# The field contains an uploaded file
					document_text = field_item.file;
					document_name = field_item.filename;
				else:
					# Regular form value
					metadata[field] = field_item.value;
		
			try:
				document_uri = metadata['uri']
			except KeyError:
				document_uri = document_name
		
			json = document.Document(document_text, document_uri, metadata).dump_json()
		
			if ffd.add_document(json):
				self.wfile.write("Document added success!\r\n")
			else:
				self.wfile.write("Document added failure.\r\n")
		
			self.wfile.write("JSON:\r\n%s" % json)
		
			return

	class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
		"""Handle requests in a separate thread."""

	if __name__ == '__main__':
		server = ThreadedHTTPServer(('localhost', 33335), Handler)
		print 'Starting server, use <Ctrl-C> to stop'
		try:
			server.serve_forever()
		except KeyboardInterrupt:
			ffd.shutdown()
