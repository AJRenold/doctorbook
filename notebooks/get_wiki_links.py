#!/usr/bin/env python

from urllib2 import urlopen
import re
import json
from nltk import metrics
from bs4 import BeautifulSoup, Tag

class WikiUrlFetch():

    def __init__(self,term):
        self.cleaned_term = self.clean_term(term)
        self.results = self.get_wiki_url(self.cleaned_term)

    def clean_term(self,term):
        return re.sub(r"[^A-Za-z0-9 ]","",term.lower())
        
    def check_dbpedia(self, term):
        api = 'http://lookup.dbpedia.org/api/search.asmx/KeywordSearch?MaxHits=8&QueryString='
        #api = 'http://lookup.dbpedia.org/api/search.asmx/PrefixSearch?MaxHits=10&QueryString='
        
        try:
            response = urlopen(api+term)
        except:
            return ""
    
        soup = BeautifulSoup(response.read())
    
        results = []
        for result in soup.findAll('result'):
            for child in result.children:
                if isinstance(child,Tag):
                    if child.name == 'label':
                        current_label = child.string.lower()
                    if child.name == 'uri':
                        results.append({ 'term': current_label.encode('utf-8'), 'url': child.string.encode('utf-8') })
        #print results[0]
        
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
        print matches
        if len(matches) == 0:
            return [ { 'match': 'none', 'term': term.encode('utf-8') } ] 
        
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
            for result in results[0:2]:
                result['match'] = 'partial'
                new_results.append(result)
            return new_results
    
    def wiki_url(self,url):

        term = url[url.rfind('/'):]
    
        entity_page = 'http://dbpedia.org/data/{}.json'.format(term)
    
        wiki_type = 'http://xmlns.com/foaf/0.1/primaryTopic'
    
        try:
            response = urlopen(entity_page)
        except:
            return
    
        data = json.loads(response.read())
        for key,value in data.items():
            'http://xmlns.com/foaf/0.1/primaryTopic'
            if 'http://xmlns.com/foaf/0.1/primaryTopic' in value:
                print key
                return key.encode('utf-8')

    def get_wiki_url(self, term):
    
        results = self.check_dbpedia(term)

        for result in results:
            if result['match'] != 'none':
                wiki = self.wiki_url(result['url'])
                result['wiki_url'] = wiki

        return results
    
if __name__ == '__main__':
    w = WikiUrlFetch('Nunberg, Geoff')
    w = WikiUrlFetch('Penguins')
