#!/usr/bin/env python

from urllib2 import urlopen
import urllib2
import re
import json
from nltk import metrics
from bs4 import BeautifulSoup, Tag

class WikiUrlFetch():

    def __init__(self):
        self.cleaned_term = None

    def fetch_wiki(self,term):
        self.cleaned_term = self.clean_term(term)
        self.results = self.get_wiki_url(self.cleaned_term)
        return self.results

    def clean_term(self,term):
        return re.sub(r"[^A-Za-z0-9 ]","",term.lower())
        
    def check_dbpedia(self, term):
        api = 'http://lookup.dbpedia.org/api/search.asmx/KeywordSearch?MaxHits=5&QueryString='
        #api = 'http://lookup.dbpedia.org/api/search.asmx/PrefixSearch?MaxHits=10&QueryString='
       
        #print term

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
            return [ { 'match': 'none', 'term': term.encode('utf-8') } ] 
        
        elif matches[0][0] == 0:
            new_results = [ matches[0][1] ]
            new_results[0]['match'] = 'exact'
            return new_results

        elif matches[0][0] <= 8:
            new_results = []
            for match in matches:
                if match[0] <= 3:
                    result = match[1]
                    result['match'] = 'good-partial'
                    new_results.append(result)

                """ # needs refinement to provide good matches
                elif match[0] <= 5:
                    words = self.normalize(result['term']).split(' ')
                    if self.normalize(term) in words:
                        result = match[1]
                        result['match'] = 'good-partial'
                        new_results.append(result)
                """
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
                #print key
                return key.encode('utf-8')

    def get_wiki_url(self, term):
    
        results = self.check_dbpedia(term)

        for result in results:
            if result['match'] != 'none':
                wiki = self.wiki_url(result['url'])
                result['wiki_url'] = wiki

        return results

class WikiUrlFetchNonDBPedia():

    def __init__(self):
        self.wiki_api =  'http://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srsearch='
        self.cleaned_term = None

    def fetch_wiki(self,term):
        self.cleaned_term = self.clean_term(term)
        self.results = self.get_wiki_url(self.cleaned_term)
        return self.results

    def check_wikipedia_api(self,term):

        url = self.wiki_api+re.sub(' ','_',term)
        request = urllib2.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0')

        try:
            response = urlopen(request)
        except urllib2.HTTPError, e:
            print e.code
            return
        except urllib2.URLError, e:
            print e.reason
            return

        results = []
        data = json.loads(response.read())
        for key,value in data.items():
            if 'search' in value:
                if type(value['search']) == list:
                    results = self.parse_wikipedia_results(value['search'])

        if len(results) > 0:
            return self.rank_dbpedia_results(results,term)
        else:
            return [ { 'match': 'none', 'term': term.encode('utf-8') } ]

    def parse_wikipedia_results(self,results):
        base_wikipedia_url = 'http://en.wikipedia.org/wiki/'
        wiki_urls = []
        for result in results:
            if 'title' in result:
                wiki_urls.append( \
                { 'url': (base_wikipedia_url + re.sub(' ','_',result['title'])).encode('UTF-8') , \
                'term': result['title'].encode('UTF-8') } )

        return wiki_urls

    def clean_term(self,term):
        return re.sub(r"[^A-Za-z0-9 ]","",term.lower())

    def normalize(self,string):
        strings = string.lower().split(" ")
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
        print term,matches
        print
        if len(matches) == 0:
            return [ { 'match': 'none', 'term': term.encode('utf-8') } ] 

        elif matches[0][0] == 0:
            new_results = [ matches[0][1] ]
            new_results[0]['match'] = 'exact'
            return new_results

        elif matches[0][0] <= 5:
            new_results = []
            for match in matches:
                if match[0] <= 3:
                    result = match[1]
                    result['match'] = 'good-partial'
                    new_results.append(result)

                # needs refinement to provide good matches
                elif match[0] <= 5:
                    words = self.normalize(result['term']).split(' ')
                    if self.normalize(term) in words:
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

    def get_wiki_url(self, term):

        results = self.check_wikipedia_api(term)

        for result in results:
            if result['match'] != 'none' and result['match'] != 'partial':
                result['wiki_url'] = result['url']
                

        #print results
        return results


if __name__ == '__main__':
    w = WikiUrlFetch('Nunberg, Geoff')
    w = WikiUrlFetch('Penguins')
