#!/usr/bin/env python3
'''
The main sidebar class, essentially just calls others to get the job done.
'''

import sidebar_items.by_metadata
import sidebar_items.by_format


ENABLED_SIDEBAR_ITEMS = [by_format, by_metadata]

def generate_sidebar(query, doc_id_rank_map, database):
	
	output = ""
	
	for item in ENABLED_SIDEBAR_ITEMS:
		links = item.get_links(query, doc_id_rank_map, database)
	
		if len(links) != 0:
			output += "<h2>%s</h2>" % (item.TITLE)
		
			for title, href in links.items():
				output += "<a href='%s'>%s</a><br>" % (href, title)
	

	return output
