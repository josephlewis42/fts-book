#!/usr/bin/env python3
'''
Allows the user to filter by a specific format, quickly.
'''



TITLE = "Format"


FORMATS = ["-media:image","-media:audio","-media:video","-media:text"]

def get_links(query, doc_id_rank_map, database):
	''' Returns a title -> href map for applicable search filters/helpers.
	'''
	
	# Remove all existing formats.
	for fmt in FORMATS:
		query = query.replace(fmt, "")
	
	
	formats = {"All":"",
				"Text"  :"-media:image -media:audio -media:video -media:application",
				"Images":"-media:text -media:audio -media:video -media:application",
				"Audio" :"-media:text -media:video -media:image -media:application",
				"Video" :"-media:text -media:image -media:audio -media:application"}
	
	link_map = {}
	
	for text, addition in formats.items():
		link_map[text] = "?q=%s %s" % (query, addition)


	return link_map
