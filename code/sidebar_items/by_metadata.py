#!/usr/bin/env python3
'''
When given a list of documents, finds common metadata that is common amongst
them, and gives links back.

'''



TITLE = "Filter By"

def get_links(query, doc_id_rank_map, database):
	''' Returns a title -> href map for applicable search filters/helpers.
	'''
	
	metadata_map = {}
	metadata_map_counter = {}
	numdocs = 0
	# find all metadata for all documents
	for doc_id, rank in doc_id_rank_map.items():
		numdocs += 1
		for key, value in database.find_metadata_for_document(doc_id).items():
			metadata_map[key] = value
			try:
				metadata_map_counter[key + ':' + value] += 1
			except KeyError:
				metadata_map_counter[key + ':' + value] = 1
	
	link_map = {}
	
	document_count = database.count_documents()
	p_a = (numdocs * 1.0) / document_count
	
	for key, value in metadata_map.items():
		p_k = len(database.find_documents_for_metadata(key, value)) * 1.0 / document_count
		p_ka = metadata_map_counter[key + ':' + value] / numdocs
		
		p_ak = (p_ka * p_a) / p_k
		
		if p_ak < 1 and p_ak > 0.1:
			link_map["%s:%s" % (key, value)] = "?q=%s %s:%s" % (query, key, value)


	return link_map
