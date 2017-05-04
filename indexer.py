#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Feb 25 09:27:41 2017

@author: evita
"""
import pickle
import os
from string import punctuation as punct
from string import maketrans
from nltk.corpus import stopwords
from urlparse import urlparse
try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup
import re
from nltk.stem.porter import PorterStemmer
from collections import defaultdict
import glob
import math

global skipped_files_counter

trans_table = maketrans(punct, ' '*len(punct))

def tokenize(text):
     tokens = []
     text=text.translate(trans_table) #source: http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python      
     for w in text.split():
         w=w.lower()
         w=''.join(s for s in w if ord(s)>31 and ord(s)<126) #remove non-ascii chars source: http://stackoverflow.com/questions/20183669/remove-formatting-from-strings   
         tokens.append(w)          
     tokens=filter(None,tokens)
     filtered_words = [word for word in tokens if word not in stopwords.words('english')] 
     return filtered_words
 
def listdir_nohidden(path):
    #source: http://stackoverflow.com/questions/7099290/how-to-ignore-hidden-files-using-os-listdir/14063074
    #skip hidden files
   return glob.glob(os.path.join(path, '*'))
    
def list_files(dir):                                                                                                  
    r = []
    folder_names_dict = dict()                                                                                                            
    subdirs = [x[0] for x in os.walk(dir)]                                                                            
    for subdir in subdirs:      
        files = listdir_nohidden(subdir)                                                                          
        if (len(files) > 0):
            folder_names_dict[subdir]= files                                                                                    
            for file in files: 
                    if not os.path.isdir(file):                                                                                       
                        r.append(file)                                                                         
    return r
    
def word_positions(filtered_words): #source: http://aakashjapi.com/fuckin-search-engines-how-do-they-work/
    '''
    returns: positions of each word in the document: {word: [pos1, pos2, etc.]} 
    '''
    position_dict = dict()
    positions = []
    for pos,word in enumerate(filtered_words):
        if word in position_dict.keys():
            curr_positions = []
            curr_positions = position_dict[word]
            curr_positions.append(pos)
            position_dict[word]=curr_positions
        else:
            positions = []
            positions.append(pos)
            position_dict[word] = positions
    return position_dict  

def parse_html_and_tokenize(filename,urls,urlname):
    stemmed_words = []
    urls_anchor = dict()
    global skipped_files_counter
    if is_valid(urlname):
        soup = BeautifulSoup(open(filename), 'html.parser')
        content_text = (soup.text).encode('utf-8').strip()
        for link in soup.findAll('a', href=True):
            url = link['href']
            if is_valid(url) and url in urls:
                anchor_text = link.get_text()
                if anchor_text and anchor_text!= "(?)":
                    anchor_text = " ".join(anchor_text.split())
                    urls_anchor[url]= anchor_text
        filtered_words = tokenize(content_text)
        porter = PorterStemmer()
        try:
            stemmed_words = [porter.stem(word) for word in filtered_words]
        except:
            stemmed_words = filtered_words
        if urls_anchor:
            with open("all_urls_anchor.txt","a+") as writer:
                for key,value in urls_anchor.items():
                    writer.write('{},{}\n'.format(key, value))
        return stemmed_words
    else:
        print filename, ": skipped"
        skipped_files_counter +=1
        return stemmed_words
    
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

def create_postings_per_file(filenames,urls,filename_to_url_dict):
    doc_set= set()
    counter=0
    block=0
    for f in sorted(filenames):
        file_name = f.split("/")
        length = len(file_name)
        doc_id = file_name[length -2] + "_" + file_name[length-1]
        url_name = filename_to_url_dict[doc_id]
        counter += 1 #counts the number of files in each folder
        file_tokens = []
        title_tokens = []
        file_tokens = parse_html_and_tokenize(f,urls,url_name)
        non_sorted_tokens_positions = dict()
        if len(file_tokens) or len(title_tokens) > 0:  
            counter += 1
            non_sorted_tokens_positions = word_positions(file_tokens)
            file_name = f.split("/")
            length = len(file_name)
            doc_id = file_name[length -2] + "_" + file_name[length-1]
            doc_set.add(doc_id)  
            if counter > 500:
                counter = 0
                block += 1 #change folder
            dir_to_write = "postings_per_file/" + str(block) + "/"
            if not os.path.exists(dir_to_write):
                os.makedirs(dir_to_write)
            with open(dir_to_write + doc_id + ".pkl",'wb') as output: 
                pickle.dump(non_sorted_tokens_positions,output)
        print "skipped files: ", skipped_files_counter
        print "total documents indexed: ", len(doc_set)

def create_block_index(directory):
    filenames2 = []
    block_index = dict()
    filenames2 = list_files(directory)
    counter = 0
    directory_name_split = directory.split("/")
    total_length = len(directory_name_split)
    directory_name = directory_name_split[total_length-1]
    print directory_name
    for f in sorted(filenames2):
        postings_dict_file = open(f,'rb')
        try:
            postings_dict = pickle.load(postings_dict_file)
            file_name = f.split("/")
            length = len(file_name)
            doc_id_splitted = file_name[length-1].split(".")
            doc_id = doc_id_splitted[0]
            #print "doc_id: ",doc_id
            postings_dict_file.close()
            for t in postings_dict.keys(): #merge into a main index
                if t in block_index.keys():
    #append the doc id and the positions of that term to the main index
                    postings_list = block_index[t]
                    postings_list.append({doc_id: postings_dict[t]})
                    block_index[t]= postings_list
                else:
                    postings_list = []
                    postings_list.append({doc_id: postings_dict[t]})
                        #create a listing of the term in the main index
                    block_index[t]=postings_list
        except:
            print f,": error"
            continue
    output = open("new_block_indexes/block_index_"+directory_name+".pkl",'wb')
    pickle.dump(block_index,output)
    output.close()
        
def merge_blocks_to_main_index():
    '''
    Merges intermediate indexes to a main index
    '''
    blocks = list_files('new_block_indexes')
    main_index= defaultdict(list)
    counter = 0
    block_dict=list()
    for b in sorted(blocks):
        print "block: ",counter
        block_dict_file = open(b,'rb')
        block_index = pickle.load(block_dict_file)
        block_dict.append(block_index)
    for dictionar in block_dict:
        print "block: ",counter
        for term in dictionar:
            try:
                main_index[term].extend(dictionar[term])
            except KeyError:
                main_index[term]=dictionar[term]
        counter += 1
    output = open("final_merged_main_index.pkl",'wb')
    pickle.dump(main_index,output)
    output.close()
    
def TF_IDF(main_ind, N):
    '''
    returns the final dictionary with tf_idf values of each document and its terms
    '''
    tf = dict() #term frequency in each document
    df = dict()
    idf = dict() #inverted document frequency of each term
    doc_terms_tfidf = dict()
    for t in main_ind.keys(): #for each term t in the inverted index
        tf_idf_dict = dict() #a new dictionary for tf_idf value
        postings = main_ind[t]
        if len(postings)>1:
            df[t] = len(postings)
            for p in postings:
                for d in p.keys():
                    doc = d
                    freq = len(p[d])
                #print "doc:", doc, "tf:", freq
                tf[doc] = freq
                idf[t] = math.log10(N/df[t])
                tf_idf_dict = {t: tf[doc] * idf[t]}
                if doc in doc_terms_tfidf.keys():
                    tf_idf_list = doc_terms_tfidf[doc]
                    tf_idf_list.append(tf_idf_dict)
                    doc_terms_tfidf[doc] = tf_idf_list
                else:
                    tf_idf = list()
                    tf_idf.append(tf_idf_dict)
                    doc_terms_tfidf[doc]=tf_idf
        else:
            df[t]=1
            dictionar = postings[0]
            for d in dictionar.keys():
                doc=d
                freq=len(dictionar[d])
                #print "doc:", doc, "tf:", freq
                tf[doc]=freq
                idf[t]=math.log10(N/df[t])
                tf_idf_dict= {t: tf[doc]*idf[t]}
                if doc in doc_terms_tfidf.keys():
                    tf_idf_list = doc_terms_tfidf[doc]
                    tf_idf_list.append(tf_idf_dict)
                    doc_terms_tfidf[doc] = tf_idf_list
                else:
                    tf_idf=list()
                    tf_idf.append(tf_idf_dict)
                    doc_terms_tfidf[doc]=tf_idf
    output = open("final_tfidf_index.pkl",'wb')
    pickle.dump(doc_terms_tfidf,output)
    output.close()
    return doc_terms_tfidf   

