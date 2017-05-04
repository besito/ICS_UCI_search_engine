#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 16 14:10:38 2017

@author: evita
"""

import requests
from bs4 import BeautifulSoup
from urlparse import urlparse, parse_qs
import re

def is_valid(url):
    '''
    Returns true is url is within ics.uci.edu and does not have any of the below extensions (valid page)
    '''
    # some regex: source: https://support.archive-it.org/hc/en-us/articles/208332963-Modify-your-crawl-scope-with-a-Regular-Expression
    # remove php, jsp, asp, txt, c , py, java, h , cpp, cc
    # and other kind of files
    parsed = urlparse(url)
    if parsed.scheme not in set(["http", "https"]):
        return False
    try:
        return ".ics.uci.edu" in parsed.hostname \
            and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4"\
            + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
            + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
            + "|thmx|mso|arff|rtf|jar|csv"\
            + "|php|jsp|asp|txt|c|py|java|h|cpp|cc"\
            + "|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()) \
            and not re.match("^.*calendar.*$", url.lower())\
            and not re.match("^.*php.*$", url.lower())\
            and not re.match("^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$", url.lower())\
            and not re.match("^.*(/misc|/sites|/all|/themes|/modules|/profiles|/css|/field|/node|/theme){3}.*$", url.lower())\
            and (bool(urlparse(url).netloc) == True)
    except TypeError:
        print ("TypeError for ", parsed)    

def fetch_urls(query):
    query = query.replace (" ", "+") #replaces whitespace with a plus sign for Google compatibility purposes
    r = requests.get('https://www.google.com/search?q=site:ics.uci.edu+{}&start=0&num=65&gbv=1&sei=YwHNVpHLOYiWmQHk3K24Cw'.format(query))
    soup = BeautifulSoup(r.text, "html.parser") # parse text with html parser
    links = []
    urls_in_collection=set(load_urlnames())
    for item in soup.find_all('h3', attrs={'class' : 'r'}):
        page=item.a['href'][7:]
        url_split=page.split("&")
        url=url_split[0].rstrip('/')
        url = url.replace("https://","http://")
        if is_valid(url) and (url in urls_in_collection): #check if valid url
             links.append(url) # [7:] strips the "/url?q=" prefix
        else:
            print "this url is invalid and will be skipped: ",url
    print "total results:",len(links)
    print
    print "Google's valid results:"
    print links [:5]
    print
    return links[:5] 

def load_urlnames():
    urls = set()
    splitted = []
    with open('/Users/evita/Documents/ICS_Search_Engine/bookkeeping.tsv') as read:
        for line in read:
            splitted=line.split('\t')
            urls.add("http://"+splitted[1].rstrip())
    return urls
    
def main():
   query = raw_input("Search for: ")
   fetch_urls(query)

if __name__ == "__main__":
    main()

