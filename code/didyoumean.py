#!/usr/bin/env python

import spell_checker
import query_parser

sc = spell_checker.Checker()

def did_you_mean(query_string):
	''' Implements a "did you mean _____" function, if the user
	seems to have misspelled a word.
	'''
	
	original = query_string
	
	for word in query_parser.word_only_tokenize(query_string):
		new_word = sc.check_word(word)
		query_string = query_string.replace(word, new_word)
		
	return query_string if query_string != original else None
