#!/usr/bin/env python
import re

def parse_document(doc):
	'''Parses a document in to a list of strings.'''
	doc = doc.lower
	doc = re.sub(r'[^\w\s]+', '', doc)
	return doc.split()
