#!/usr/bin/env python

#imports
import pandas as pd
from bs4 import BeautifulSoup, NavigableString, Tag
import nltk
import re
from itertools import islice
from collections import Counter
import os

# Our tools
from get_wiki_links import WikiUrlFetch
from get_wiki_links import WikiUrlFetch2

from get_wiki_text import Wiki2Plain

class ParseTextForWiki():

    def __init__(self,text):
        self.text = text
        self.term_list = self.create_term_list(self.text)
        self.term_df = self.create_df_from_terms(self.term_list)
        self.wiki_df = self.create_wiki_df(self.term_df)
        self.wiki_df = self.append_term_location_in_text(self.wiki_df, self.text)

        #self.test = self.get_first_term_test()

    def create_term_list(self,text):

        clean_text = re.sub(r"[\n\.,\(\)\?\!\-']",' ',text)
        tagged_text = nltk.pos_tag(clean_text.split(' '))

        pos = ['NN','NNS','NNP','NNPS']

        terms = []
        chain = []
        for term in tagged_text:

            if term[1] in pos:
                chain.append(term)
                terms.append(term[0].lower().encode('UTF-8'))
                terms.append(" ".join([ item[0].lower().encode('UTF-8') for item in chain ]))
            else:
                if len(chain) > 0:
                    terms.append(" ".join([ item[0].lower().encode('UTF-8') for item in chain ]))
                    chain = []

        terms = [ re.sub(r' +',' ',term) for term in terms ]
        terms = [ re.sub(r'^ | $','',term) for term in terms ]

        return terms

    def create_df_from_terms(self,terms):

        term_count = Counter(terms)
        count_threshold = 1
        seen = {}

        list_for_df = []
        for term,count in term_count.iteritems():
            if count >= count_threshold:
                if term != "" and term != " " and term not in seen:
                    list_for_df.append({ 'term': term, 'count': count, 'tag': 'raw'})
                    seen[term] = True

        #print list_for_df
        return pd.DataFrame(list_for_df)
        return pd.DataFrame(list_for_df)

    def create_wiki_df(self,term_df):

        list_for_wiki_df = []

        search_wiki = WikiUrlFetch()

        for row in islice(term_df.iterrows(),None): # iterations limited 100 because WikiUrlFetch is very slow for many terms
                                        # likely this is because of DBPedia API limitations
            wikis = search_wiki.fetch_wiki(row[1]['term'])
    
            for wiki in wikis:
                if wiki['match'] == 'exact' or wiki['match'] == 'good-partial':
                    list_for_wiki_df.append( { 'term': row[1]['term'], 'matched_term': wiki['term'], \
                    'count': row[1]['count'], 'match': wiki['match'], 'url': wiki['wiki_url'] } )
            
        wiki_df = pd.DataFrame(list_for_wiki_df)
            
        def get_wiki_textimage(url):
            wiki = Wiki2Plain(url)
            return wiki.text, wiki.image()

        if len(wiki_df) > 0:
            wiki_df['wiki_text'],wiki_df['wiki_image'] = zip(*wiki_df['url'].apply(get_wiki_textimage))

        return wiki_df


    def append_term_location_in_text(self, wiki_df, text):
        
        def append_text_locations(term):
            term_len = len(term)
            term_loc = text.lower().find(term)
            text_loc = [ term_loc, term_loc+term_len ]
            text_before = text[term_loc-50:term_loc]
            text_after = text[term_loc+term_len:term_loc+term_len+50]
            return text_loc, text_before, text_after

        if len(wiki_df) > 0:
            wiki_df['offset'],wiki_df['text_before'],wiki_df['text_after'] = zip(*wiki_df['term'].apply(append_text_locations))
        return wiki_df

    def get_first_term_test(self):

        wiki_df = self.wiki_df
        for row in wiki_df.iterrows():
            print row[1]['term'], row[1]['url']

    def get_wiki_df(self):
        return self.wiki_df
