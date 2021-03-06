#!/usr/bin/env python

#imports
import pandas as pd
from bs4 import BeautifulSoup, NavigableString, Tag
import nltk
import re
from itertools import islice
from collections import Counter
import os
import sys
 
# Our tools
from get_wiki_links import WikiUrlFetch
from get_wiki_links import WikiUrlFetchNonDBPedia

from get_wiki_text import Wiki2Plain

try:
    ## flickr api tools
    from flickr_api.auth import AuthHandler
    from flickr_api import FlickrError
    import flickr_api

    ## news api tools
    from tidings import Guardian, NewYorkTimes

except:
    pass

class ParseTextForWiki():

    def __init__(self,text,flickr=False,news=False):

        self.flickr = flickr
        self.news = news
        if self.flickr or self.news:
            self.secrets, self.news_keys = self.load_api_keys()

        self.text = text
        self.term_list = self.create_term_list(self.text)
        self.term_df = self.create_df_from_terms(self.term_list)
        self.wiki_df = self.create_wiki_df(self.term_df, self.flickr, self.news)
        self.wiki_df = self.append_term_location_in_text(self.wiki_df, self.text)



    def load_api_keys(self):
        if os.path.exists('settings.py'):
            from settings import FLICKR_KEY, FLICKR_SECRET, guardian_key, nyt_key
            secrets = {'api_key': FLICKR_KEY, 'api_secret': FLICKR_SECRET}
            news_keys = {'guardian_key': guardian_key, 'nyt_key': nyt_key }
            return secrets, news_keys
        else:
            print("settings.py not found, add to directory or run without flickr and news")
            sys.exit()

    def create_term_list(self,text):

        clean_text = re.sub(r"[\n\.,\(\)\?\!\-':]",'',text)
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

    def create_wiki_df(self,term_df,flickr,news):

        list_for_wiki_df = []

        #search_wiki = WikiUrlFetch()
        search_wiki = WikiUrlFetchNonDBPedia()
        print 'start search'

        for row in islice(term_df.iterrows(),None):
            wikis = search_wiki.fetch_wiki(row[1]['term'])

            for wiki in wikis:
                if wiki['match'] == 'exact' or wiki['match'] == 'good-partial':
                    list_for_wiki_df.append( { 'term': row[1]['term'], 'matched_term': wiki['term'], \
                    'count': row[1]['count'], 'match': wiki['match'], 'url': wiki['wiki_url'] } )

        print 'end search'
        wiki_df = pd.DataFrame(list_for_wiki_df)

        ## currently Wiki2Plain .image() is running slow, not fetching images
        def get_wiki_textimage(url):
            wiki = Wiki2Plain(url)
            return wiki.text, "none" #wiki.image()

        def get_flickr_url(term):
            flickr_api.set_keys(**self.secrets)
            photos = flickr_api.Photo.search(tags=term, sort='date-posted-desc')

            if len(photos) == 0 or type(photos) == dict:
                print "len 0 or dict"
                print photos
                return []
            flickr_urls = []
            for photo in photos[:3]:
                try:
                    flickr_urls.append("http://farm{farm}.staticflickr.com/{server}/{id}_{secret}_m.jpg".format(**photo.getInfo()))
                except FlickrError:
                    pass

            return flickr_urls

        def get_news_url(term):
            g = Guardian(self.news_keys['guardian_key'])
            g_links = g.query(term, from_date='2013-01-01', to_date='2013-4-30')
            return g_links

            #nyt = NewYorkTimes(self.news_keys['nyt_key'])
            #nyt_links = nyt.query(term, from_date='2013-01-01', to_date='2013-4-30')
            #for nyt_url in nyt_links:
            #    print nyt_url

        print 'get text and image, flickr, news'
        if len(wiki_df) > 0:
            wiki_df['wiki_text'],wiki_df['wiki_image'] = zip(*wiki_df['url'].apply(get_wiki_textimage))
            if self.flickr:
                wiki_df['flickr_urls'] = wiki_df['term'].apply(get_flickr_url)
            if self.news:
                wiki_df['news_urls'] = wiki_df['term'].apply(get_news_url)

        print 'done'

        return wiki_df

    def append_term_location_in_text(self, wiki_df, text):
        
        def append_text_locations(term):
            term_len = len(term)
            term_loc = text.encode("UTF-8").lower().find(term)
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

if __name__ == '__main__':
    w = ParseTextForWiki('a')
