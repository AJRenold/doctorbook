#!/usr/bin/env python

from bs4 import BeautifulSoup, Tag
from urllib2 import urlopen
from nltk import metrics
import re
import json

class WikiUrlFetch():

    def __init__(self,term):
        self.cleaned_term = self.clean_term(term)
        self.results = self.get_wiki_url(self.cleaned_term)

    def clean_term(self,term):
        return re.sub(r"[^A-Za-z0-9 ]","",term.lower())
        
    def check_dbpedia(self, term):
        api = 'http://lookup.dbpedia.org/api/search.asmx/KeywordSearch?MaxHits=8&QueryString='
        #api = 'http://lookup.dbpedia.org/api/search.asmx/PrefixSearch?MaxHits=10&QueryString='
        response = urlopen(api+term)
        if not response:
            return ""
    
        soup = BeautifulSoup(response.read())
    
        results = []
        for result in soup.findAll('result'):
            for child in result.children:
                if isinstance(child,Tag):
                    if child.name == 'label':
                        current_label = child.string.lower()
                    if child.name == 'uri':
                        results.append({ 'term': current_label, 'url': child.string })
    
        return self.rank_dbpedia_results(results,term)
    
    def normalize(self,string):
        strings = string.split(" ")
        strings.sort()
        return " ".join(strings)

    def rank_dbpedia_results(self,results,term):
        """
        logic:
            if edit distance 0, exact match
            if edit distance 1-4, good-partial match
            if edit distance > 4, partial match (results unsorted)
        """

        matches = []
        for result in results:
            matches.append([metrics.edit_distance(self.normalize(result['term']), self.normalize(term)), result])

        matches.sort()
        #print matches
        if len(matches) == 0:
            return [ { 'match': 'none', 'term': term } ] 
        
        elif matches[0][0] == 0:
            new_results = [ matches[0][1] ]
            new_results[0]['match'] = 'exact'
            return new_results

        elif matches[0][0] <= 3:
            new_results = []
            for match in matches:
                if match[0] <= 3:
                    result = match[1]
                    result['match'] = 'good-partial'
                    new_results.append(result)
            return new_results
        
        else:
            new_results = []
            for result in results[0:3]:
                result['match'] = 'partial'
                new_results.append(result)
            return new_results
    
    def wiki_url(self,url):

        term = url[url.rfind('/'):]
    
        entity_page = 'http://dbpedia.org/data/{}.json'.format(term)
    
        wiki_type = 'http://xmlns.com/foaf/0.1/primaryTopic'
    
        response = urlopen(entity_page)
        if not response:
            return
    
        data = json.loads(response.read())
        for key,value in data.items():
            'http://xmlns.com/foaf/0.1/primaryTopic'
            if 'http://xmlns.com/foaf/0.1/primaryTopic' in value:
                return key

    def get_wiki_url(self, term):
    
        results = self.check_dbpedia(term)

        for result in results:
            if result['match'] != 'none':
                wiki = self.wiki_url(result['url'])
                result['wiki_url'] = wiki

        return results

if __name__ == '__main__':
    w = WikiUrlFetch('discipline')
    print w.results
    w = WikiUrlFetch('HTTP')
    print w.results
    w = WikiUrlFetch('Nunberg, Geoff')
    print w.results
    w = WikiUrlFetch('sdasdasd')
    print w.results

