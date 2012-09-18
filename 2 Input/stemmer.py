#!/usr/bin/env python

def stemmer(word):
	''' A simple stemmer for English. '''
	for suffix in ["ing","ly","ed"]:
		if word.endswith(suffix):
			return word[:- len(suffix)]
	return word
